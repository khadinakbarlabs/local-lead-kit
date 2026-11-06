"""Small fixed-origin Apify client. No paid request is automatically retried."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

from . import __version__
from .core import ACTORS
from .pricing import PricingError, current_ppe_pricing, finite_amount

def metadata_digest(metadata):
    """Bind reviewed metadata to the same canonical JSON digest as saved plans."""
    return hashlib.sha256(json.dumps(metadata,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class ApiError(RuntimeError):pass

class ApifyAccessDenied(ApiError):pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def validate_input(value,schema,path='input'):
    expected=schema.get('type')
    types={'object':dict,'array':list,'string':str,'boolean':bool,'integer':int,'number':(int,float)}
    if expected in types and (not isinstance(value,types[expected]) or expected in ['integer','number'] and isinstance(value,bool)):
        raise ValueError(f'{path} does not match the current Actor schema.')
    if 'enum' in schema and value not in schema['enum']:raise ValueError(f'{path} has an unsupported value.')
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if 'minimum' in schema and value<schema['minimum'] or 'maximum' in schema and value>schema['maximum']:raise ValueError(f'{path} is outside the current bounds.')
    if isinstance(value,dict):
        properties=schema.get('properties',{})
        if any(k not in value for k in schema.get('required',[])):raise ValueError(f'{path} is missing a current required field.')
        for key,item in value.items():
            if key not in properties:raise ValueError(f'{path}.{key} is not a current Actor field.')
            validate_input(item,properties[key],path+'.'+key)
    if isinstance(value,list):
        if 'minItems' in schema and len(value)<schema['minItems'] or 'maxItems' in schema and len(value)>schema['maxItems']:raise ValueError(f'{path} has an unsupported item count.')
        for i,item in enumerate(value):
            if isinstance(schema.get('items'),dict):validate_input(item,schema['items'],path+f'[{i}]')

class ApifyClient:
    sources = ACTORS
    def __init__(self,token=None,transport=None,*,public_metadata_only=False):
        self.public_metadata_only=public_metadata_only
        self.token='' if public_metadata_only else token or os.environ.get('APIFY_TOKEN','')
        if not self.token and not public_metadata_only:raise ApiError('Connect your Apify account through secure APIFY_TOKEN configuration first.')
        self.transport=transport
        cafile=os.getenv('SSL_CERT_FILE')
        if not cafile and Path('/etc/ssl/cert.pem').exists():cafile='/etc/ssl/cert.pem'
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=cafile)))

    def request(self,path,payload=None,missing_ok=False):
        if not isinstance(path,str) or not path or path.startswith('/') or '..' in path or '://' in path:
            raise ValueError('Unsupported API path.')
        if self.public_metadata_only and (payload is not None or not re.fullmatch(r'(?:acts|actor-builds)/[A-Za-z0-9]{8,32}',path)):
            raise ApiError('Public metadata mode only permits read-only Actor and build metadata.')
        headers={'Content-Type':'application/json','User-Agent':'looksy/'+__version__}
        if self.token:headers['Authorization']='Bearer '+self.token
        request=urllib.request.Request('https://api.apify.com/v2/'+path,
            data=None if payload is None else json.dumps(payload,allow_nan=False).encode(),headers=headers)
        try:
            if self.transport:return self.transport(request)
            with self.opener.open(request,timeout=40) as response:
                body=response.read(32*1024*1024+1)
                if len(body)>32*1024*1024:raise ApiError('The response exceeded the safe read limit.')
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code==404 and missing_ok:return None
            if exc.code in [401,403]:raise ApifyAccessDenied('Apify access was denied. Reconnect or review this account’s access.') from None
            raise ApiError(f'Apify returned HTTP {exc.code}. Review the existing stage before retrying.') from None
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            raise ApiError('The Apify connection did not return a confirmed response.') from exc
        except (json.JSONDecodeError,UnicodeError):
            raise ApiError('Apify returned an unreadable response.') from None

    @staticmethod
    def identity(value):
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9]{8,32}',value):raise ValueError('Use a valid Apify resource ID.')
        return value

    def data(self,path):
        response=self.request(path)
        if not isinstance(response,dict) or not isinstance(response.get('data'),dict):raise ApiError('Apify returned an unexpected resource response.')
        return response['data']

    def metadata(self,stage):
        if stage not in self.sources:raise ValueError('Choose an Actor from the configured sources.')
        spec=self.sources[stage]
        actor_id=self.identity(spec.get('id'))
        if not isinstance(spec.get('slug'),str) or not re.fullmatch(r'khadinakbar/[a-zA-Z0-9_-]+',spec['slug']):
            raise ApiError('Only verified khadinakbar Actors are supported.')
        actor=self.data('acts/'+actor_id)
        if (actor.get('id')!=actor_id or actor.get('isPublic') is not True or actor.get('isDeprecated') is not False or
                actor.get('username')!='khadinakbar' or f"{actor.get('username')}/{actor.get('name')}"!=spec['slug']):
            raise ApiError('The configured Actor is unavailable for public use or has been deprecated.')
        # Actor API permission level is authoritative. Never infer limited access
        # from public visibility, a catalog entry, or a successful build.
        if actor.get('actorPermissionLevel')!='LIMITED_PERMISSIONS':
            raise ApiError('Limited permissions could not be verified. Full or unknown permission Actors cannot run through Looksy; inspect the Actor in Apify.')
        defaults=actor.get('defaultRunOptions')
        tagged=actor.get('taggedBuilds')
        if not isinstance(defaults,dict) or not isinstance(tagged,dict):
            raise ApiError('The default published build could not be verified; inspect the Actor in Apify.')
        if defaults.get('forcePermissionLevel') not in (None,'LIMITED_PERMISSIONS'):
            raise ApiError('The Actor default permission override is full or unknown; inspect it in Apify.')
        tag=defaults.get('build')
        build=tagged.get(tag) if isinstance(tag,str) else None
        # Apify also permits a full build number as the default; it must still be
        # present in the published tag map to bind this lookup to a known build.
        if not build and isinstance(tag,str) and re.fullmatch(r'\d+\.\d+\.\d+',tag):
            matches=[item for item in tagged.values() if isinstance(item,dict) and item.get('buildNumber')==tag]
            if matches and all(item.get('buildId')==matches[0].get('buildId') for item in matches):build=matches[0]
        if not isinstance(build,dict):
            raise ApiError('The default published build could not be verified; inspect the Actor in Apify.')
        try:bid=self.identity(build.get('buildId'))
        except ValueError:raise ApiError('The default published build identity could not be verified.') from None
        detail=self.data('actor-builds/'+bid)
        number=detail.get('buildNumber')
        if (detail.get('id')!=bid or detail.get('actId')!=actor_id or detail.get('status')!='SUCCEEDED' or
                not isinstance(number,str) or not re.fullmatch(r'\d+\.\d+\.\d+',number) or build.get('buildNumber')!=number):
            raise ApiError('The current Actor build is not ready or its published identity changed.')
        definition=detail.get('actorDefinition')
        permissions=definition.get('permissions') if isinstance(definition,dict) else None
        if not isinstance(permissions,dict) or permissions.get('type')!='limited':
            raise ApiError('The published build permission declaration is full or unknown; inspect the exact build in Apify.')
        schema=detail.get('inputSchema')
        if isinstance(schema,str):
            try:schema=json.loads(schema)
            except (ValueError,TypeError):raise ApiError('The current Actor input schema could not be inspected.') from None
        if not isinstance(schema,dict) or not isinstance(schema.get('properties'),dict):
            raise ApiError('The current Actor input schema could not be inspected.')
        try:pricing=current_ppe_pricing(actor.get('pricingInfos'))
        except PricingError as exc:raise ApiError(str(exc)) from None
        return {'id':actor_id,'slug':spec['slug'],'build_id':bid,'build_number':number,
                'permission_level':actor['actorPermissionLevel'],'build_permissions':deepcopy(permissions),
                'default_run_options':deepcopy(defaults),'schema':schema,'pricing':pricing,
                'store_url':'https://apify.com/'+spec['slug']}

    def start(self,actor,payload,options):
        if self.public_metadata_only or not self.token:
            raise ApiError('Connect your Apify account before starting a run.')
        stage=next((key for key,spec in self.sources.items() if spec.get('id')==actor),None)
        if stage is None:raise ValueError('Actor is outside this resource’s configured sources.')
        allowed={'build','memory','timeout','maxTotalChargeUsd','restartOnError','expectedMetadataHash'}
        if not isinstance(options,dict) or set(options)-allowed:
            raise ValueError('Unsupported run options.')
        expected_hash=options.get('expectedMetadataHash')
        if 'expectedMetadataHash' in options and (not isinstance(expected_hash,str) or not re.fullmatch(r'[a-f0-9]{64}',expected_hash)):
            raise ValueError('Supply a valid approved metadata hash or prepare a new plan.')
        cap=options.get('maxTotalChargeUsd')
        if not finite_amount(cap) or not 0<cap<=500:
            raise ValueError('A finite positive event cap of no more than $500 is required.')
        timeout=options.get('timeout')
        if type(timeout) is not int or not 1<=timeout<=3600:
            raise ValueError('Set a bounded run timeout between 1 and 3,600 seconds.')
        if options.get('restartOnError',False) is not False:
            raise ValueError('Automatic paid restarts are not supported.')
        if not isinstance(options.get('build'),str) or not re.fullmatch(r'\d+\.\d+\.\d+',options['build']):
            raise ValueError('Pin the exact published build number before starting a run.')
        if 'memory' in options and (type(options['memory']) is not int or not 128<=options['memory']<=32768 or options['memory']&(options['memory']-1)):
            raise ValueError('Choose an Apify memory allocation between 128 and 32,768 MB, in powers of two.')
        if not isinstance(payload,dict):raise ValueError('Supply a JSON object as the Actor input.')
        metadata=self.metadata(stage)
        if expected_hash is not None and metadata_digest(metadata)!=expected_hash:
            raise ApiError('The Actor metadata changed. Prepare and review a new plan before starting a run.')
        if options['build']!=metadata['build_number']:
            raise ApiError('The published build changed. Prepare and review a new plan.')
        if metadata['pricing']['requires_tier_review']:
            raise ApiError('This Actor uses subscription-tier prices. Looksy cannot verify your applicable tier; review pricing and run it directly in Apify.')
        minimum=metadata['pricing']['minimalMaxTotalChargeUsd']
        if minimum is not None and cap<minimum:
            raise ValueError('The event cap is below the current Actor minimum. Prepare a new plan with an adequate cap.')
        validate_input(payload,metadata['schema'])
        params=urllib.parse.urlencode({k:str(v).lower() if isinstance(v,bool) else v
                                      for k,v in {**options,'restartOnError':False,
                                                  'forcePermissionLevel':'LIMITED_PERMISSIONS'}.items()
                                      if k!='expectedMetadataHash'})
        response=self.request('acts/'+actor+'/runs?'+params,payload)
        if not isinstance(response,dict) or not isinstance(response.get('data'),dict):raise ApiError('The paid start did not return a run identity.')
        return response['data']

    def get_run(self,run_id):return self.data('actor-runs/'+self.identity(run_id))

    def items(self,dataset_id,limit):
        dataset_id=self.identity(dataset_id);rows=[]
        while len(rows)<limit:
            size=min(100,limit-len(rows));page=self.request(f'datasets/{dataset_id}/items?format=json&limit={size}&offset={len(rows)}')
            if not isinstance(page,list):raise ApiError('The dataset response was not a list.')
            rows.extend(page)
            if len(page)<size:return rows,False
        extra=self.request(f'datasets/{dataset_id}/items?format=json&limit=1&offset={len(rows)}')
        if not isinstance(extra,list):raise ApiError('The dataset completeness check failed.')
        return rows,bool(extra)

    def record(self,store_id,key):
        if key not in ['OUTPUT','RUN_SUMMARY','INPUT']:raise ValueError('Unsupported evidence record.')
        return self.request('key-value-stores/'+self.identity(store_id)+'/records/'+key,missing_ok=True)
