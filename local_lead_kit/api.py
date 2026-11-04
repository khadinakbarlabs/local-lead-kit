"""Small fixed-origin Apify client. No paid request is automatically retried."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

from .core import ACTORS

class ApiError(RuntimeError):pass

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
    def __init__(self,token=None,transport=None):
        self.token=token or os.environ.get('APIFY_TOKEN','')
        if not self.token:raise ApiError('Connect your Apify account through secure APIFY_TOKEN configuration first.')
        self.transport=transport
        cafile=os.getenv('SSL_CERT_FILE')
        if not cafile and Path('/etc/ssl/cert.pem').exists():cafile='/etc/ssl/cert.pem'
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=cafile)))

    def request(self,path,payload=None,missing_ok=False):
        if not path or path.startswith('/') or '..' in path or '://' in path:raise ValueError('Unsupported API path.')
        request=urllib.request.Request('https://api.apify.com/v2/'+path,
            data=None if payload is None else json.dumps(payload,allow_nan=False).encode(),
            headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json','User-Agent':'local-lead-kit/0.2.0'})
        if self.transport:return self.transport(request)
        try:
            with self.opener.open(request,timeout=40) as response:
                body=response.read(32*1024*1024+1)
                if len(body)>32*1024*1024:raise ApiError('The response exceeded the safe read limit.')
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code==404 and missing_ok:return None
            if exc.code in [401,403]:raise ApiError('Apify access was denied. Reconnect or review this account’s access.') from None
            raise ApiError(f'Apify returned HTTP {exc.code}. Review the existing stage before retrying.') from None
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            raise ApiError('The Apify connection did not return a confirmed response.') from exc
        except json.JSONDecodeError:
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
        spec=self.sources[stage];actor=self.data('acts/'+spec['id'])
        if (actor.get('id')!=spec['id'] or not actor.get('isPublic') or
                f"{actor.get('username')}/{actor.get('name')}"!=spec['slug']):raise ApiError('The configured Actor is unavailable for public use.')
        tag=actor.get('defaultRunOptions',{}).get('build','latest')
        build=actor.get('taggedBuilds',{}).get(tag,{})
        if not build:raise ApiError('The default published build could not be verified; inspect the Actor in the Store.')
        bid=self.identity(build.get('buildId'))
        detail=self.data('actor-builds/'+bid)
        if detail.get('actId')!=spec['id'] or detail.get('status')!='SUCCEEDED':raise ApiError('The current Actor build is not ready.')
        schema=detail.get('inputSchema')
        if isinstance(schema,str):schema=json.loads(schema)
        if not isinstance(schema,dict) or not isinstance(schema.get('properties'),dict):raise ApiError('The current Actor input schema could not be inspected.')
        now=datetime.now(timezone.utc)
        prices=[]
        for price in actor.get('pricingInfos',[]):
            try:started=datetime.fromisoformat(price['startedAt'].replace('Z','+00:00'))
            except (KeyError,ValueError,TypeError):continue
            if started<=now:prices.append((started,price))
        if not prices:raise ApiError('Current Actor pricing could not be verified.')
        price=max(prices,key=lambda item:item[0])[1]
        if price.get('pricingModel')!='PAY_PER_EVENT':raise ApiError('The current pricing model needs review before this resource can run it.')
        events={name:{'price_usd':event.get('eventPriceUsd'),'title':event.get('eventTitle',name)}
                for name,event in price.get('pricingPerEvent',{}).get('actorChargeEvents',{}).items()}
        if not events:raise ApiError('The current event prices could not be inspected.')
        return {'id':spec['id'],'slug':spec['slug'],'build_id':bid,'build_number':detail.get('buildNumber'),
                'schema':schema,'pricing':{'model':price['pricingModel'],'started_at':price['startedAt'],'events':events},
                'store_url':'https://apify.com/'+spec['slug']}

    def start(self,actor,payload,options):
        if actor not in {s['id'] for s in self.sources.values()}:raise ValueError('Actor is outside this resource’s configured sources.')
        allowed={'build','memory','timeout','maxTotalChargeUsd','restartOnError'}
        if set(options)-allowed or not options.get('maxTotalChargeUsd',0)>0:raise ValueError('A bounded run allowance is required.')
        params=urllib.parse.urlencode({k:str(v).lower() if isinstance(v,bool) else v for k,v in options.items()})
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
