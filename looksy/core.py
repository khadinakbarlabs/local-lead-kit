"""Campaign contracts, durable starts and honest result normalization."""
from contextlib import contextmanager
from decimal import Decimal, ROUND_DOWN
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import tempfile
import threading
from urllib.parse import urlsplit

ACTORS = {
    'maps': {'id':'9XVfT1vIqqL4fiS4q','slug':'khadinakbar/google-maps-leads-scraper','memory':2048,'timeout':300},
    'contacts': {'id':'TwNeQtj5TfaKDkcCK','slug':'khadinakbar/bulk-website-contact-extractor','memory':1024,'timeout':300},
    'validator': {'id':'Gvo4zJ8A4otiyCclv','slug':'khadinakbar/email-address-validator','memory':1024,'timeout':120},
}

class NeedsAttention(RuntimeError):
    """A paid effect may exist; never create another automatically."""

def atomic_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def validate_request(value):
    if not isinstance(value,dict):raise ValueError('Enter campaign information.')
    niche=str(value.get('niche','')).strip()
    if not 2<=len(niche)<=120 or any(ord(c)<32 for c in niche):raise ValueError('Enter a business niche, up to 120 characters.')
    locations=value.get('locations',[])
    if isinstance(locations,str):locations=locations.splitlines()
    if not isinstance(locations,list):raise ValueError('Enter one city or territory per line.')
    clean=[];seen=set()
    for location in locations:
        if not isinstance(location,str):raise ValueError('Territories must be text.')
        location=location.strip()
        if not location:continue
        if len(location)>120 or any(ord(c)<32 for c in location):raise ValueError('Use short city or territory names.')
        if location.casefold() not in seen:clean.append(location);seen.add(location.casefold())
    if not 1<=len(clean)<=20:raise ValueError('Use between one and twenty territories.')
    target=value.get('target',500)
    if isinstance(target,bool) or not isinstance(target,int) or not 1<=target<=5000:raise ValueError('Choose a business target between 1 and 5,000.')
    budget=value.get('budget_usd',10)
    try:budget=Decimal(str(budget))
    except Exception as exc:raise ValueError('Enter a positive run allowance.') from exc
    if not budget.is_finite() or not Decimal('.50')<=budget<=Decimal('500'):raise ValueError('Set a run allowance between $0.50 and $500.')
    if any(key in value and not isinstance(value[key],bool) for key in ['analysis','include_contacts']):raise ValueError('Choose contacts and AI review using the on/off controls.')
    analysis=value.get('analysis',False);offer=str(value.get('offer','')).strip()
    if len(offer)>1000 or (analysis and len(offer)<3):raise ValueError('For AI review, add a short description of your offer.')
    return {'niche':niche,'locations':clean,'target':target,'budget_usd':float(budget.quantize(Decimal('.01'))),
            'include_contacts':bool(value.get('include_contacts',True)),'analysis':analysis,'offer':offer}

def build_plan(request, metadata):
    count=request['target'];batch_count=math.ceil(count/50)
    groups=[('maps',len(request['locations']),Decimal('.35'))]
    if request['include_contacts']:groups.extend([('contacts',batch_count,Decimal('.50')),('validator',batch_count,Decimal('.15'))])
    else:groups=[('maps',len(request['locations']),Decimal('1'))]
    available=Decimal(str(request['budget_usd']))-Decimal('.0001')
    reservations=[]
    for stage,runs,share in groups:
        cap=(available*share/runs).quantize(Decimal('.0001'),rounding=ROUND_DOWN)
        if cap<=0:raise ValueError('The allowance is too small for this campaign size.')
        for i in range(runs):reservations.append({'key':f'{stage}:{i}','stage':stage,'cap_usd':float(cap)})
    per_location=math.ceil(count/len(request['locations']))
    inputs=[{'searchQuery':request['niche'],'location':location,'maxResults':min(5000,per_location),
             'enrichEmails':False,'requireEmail':False,'requireWebsite':False,'minLeadScore':0,'maxReviews':0}
            for location in request['locations']]
    plan={'request':request,'actors':metadata,'maps_inputs':inputs,'reservations':reservations,
          'maximum_runs':len(reservations),'approved':False,
          'cost_note':'Research runs share your approved campaign allowance. Check your account for final charges; assistant-model usage is separate.'}
    plan['hash']=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
    return plan

class Ledger:
    def __init__(self,path,allowance):
        self.path=Path(path);self.allowance=Decimal(str(allowance));self.lock=threading.RLock()

    def read(self):
        return json.loads(self.path.read_text()) if self.path.exists() else {'allowance_usd':str(self.allowance),'entries':{}}

    def write(self,value):atomic_json(self.path,value)

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        lock_path=self.path.with_suffix('.lock')
        with self.lock:
            try:fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            except FileExistsError as exc:raise NeedsAttention('Another worker or an interrupted start holds this campaign. Inspect it before resuming.') from exc
            try:
                os.write(fd,str(os.getpid()).encode());os.close(fd)
                yield
            finally:
                lock_path.unlink(missing_ok=True)

def start_once(client,ledger,key,actor,payload,options):
    with ledger.locked():
        data=ledger.read()
        if Decimal(str(data['allowance_usd']))!=ledger.allowance:raise NeedsAttention('The original allowance changed. Review the campaign.')
        entries=data['entries'];existing=entries.get(key)
        fingerprint=hashlib.sha256(json.dumps({'actor':actor,'input':payload,'options':options},sort_keys=True).encode()).hexdigest()
        if existing:
            if existing['fingerprint']!=fingerprint:raise NeedsAttention('This stage already has a different approved input.')
            if existing.get('run_id'):return client.get_run(existing['run_id'])
            raise NeedsAttention('A previous start has an uncertain outcome. Reconcile it; do not start another.')
        cap=Decimal(str(options['maxTotalChargeUsd']))
        reserved=sum((Decimal(str(entry['reserved_usd'])) for entry in entries.values()),Decimal('0'))
        if cap<=0 or reserved+cap>ledger.allowance:raise ValueError('This run would exceed the approved allowance.')
        entries[key]={'state':'STARTING','reserved_usd':str(cap),'actor':actor,'fingerprint':fingerprint}
        ledger.write(data)
        try:
            run=client.start(actor,payload,options)
            if not run.get('id'):raise ValueError('Run identity missing')
        except Exception as exc:
            entries[key]['state']='UNKNOWN';ledger.write(data)
            raise NeedsAttention('The start could not be confirmed. Its reserved allowance stays held; reconcile the existing run.') from exc
        entries[key].update(state='RUNNING',run_id=run['id']);ledger.write(data)
        return run

def public_url(value):
    if not isinstance(value,str) or len(value)>3000:return None
    try:
        url=urlsplit(value.strip());host=(url.hostname or '').lower().rstrip('.')
        if url.scheme not in ['http','https'] or url.username or url.password or not host:return None
        if '.' not in host or host.endswith(('.localhost','.local','.internal')) or host=='localhost':return None
        if all(part.isdigit() for part in host.split('.')):
            if not ipaddress.ip_address(host).is_global:return None
        try:
            if not ipaddress.ip_address(host).is_global:return None
        except ValueError:
            if all(part.isdigit() for part in host.split('.')):return None
        _=url.port
        return value.strip()
    except (ValueError,TypeError):return None

def domain(url):
    return (urlsplit(url or '').hostname or '').lower().removeprefix('www.')

def safe_csv(value):
    value=str(value if value is not None else '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value

def normalize_results(maps,websites,validations,partial=False):
    sites={}
    for row in websites:
        url=public_url(row.get('source_url',''))
        if not url:continue
        key=domain(url)
        previous=sites.get(key,{})
        emails=sorted({str(x).strip().lower() for x in previous.get('emails',[])+row.get('emails',[]) if isinstance(x,str) and 3<=len(x)<=320})
        sites[key]={**previous,**row,'emails':emails,'pages_crawled':max(previous.get('pages_crawled',0) or 0,row.get('pages_crawled',0) or 0)}
    checks={str(row.get('normalizedEmail','')).lower():row for row in validations if row.get('normalizedEmail')}
    businesses={};contacts={}
    for i,row in enumerate(maps):
        if not isinstance(row,dict) or not row.get('business_name'):continue
        website=public_url(row.get('website','')) or ''
        key=row.get('place_id') or public_url(row.get('google_maps_url',''))
        if not key:key='review_'+hashlib.sha256(json.dumps([row.get('business_name'),row.get('full_address'),website,i]).encode()).hexdigest()[:24]
        site=sites.get(domain(website),{});emails=site.get('emails',[])
        coverage='email_found' if emails else 'site_not_reached' if site and not site.get('pages_crawled') else 'no_email_found' if site else 'not_processed'
        businesses[key]={'business_id':key,'business_name':str(row['business_name']),'address':str(row.get('full_address','')),
            'phone':str(row.get('phone','')),'website':website,'maps_source':public_url(row.get('google_maps_url','')) or '',
            'coverage':coverage,'email_count':len(emails),'pages_crawled':site.get('pages_crawled',0),
            'identity_review':str(key).startswith('review_')}
        for email in emails:
            check=checks.get(email,{});flags=[]
            if re.match(r'^[\d+() -]{7,}[a-z]',email):flags.append('possible_phone_text_joined_to_email')
            if check.get('status')=='invalid':flags.append('validation_failed')
            contacts[(key,email)]={'business_id':key,'business_name':str(row['business_name']),'email':email,
                'validation_status':check.get('status','not_checked'),'validation_reason':'; '.join(check.get('reasons',[])),
                'mailbox_confirmed':False,'source_website':site.get('source_url',''),
                'extraction_review':'; '.join(flags) or 'review_source_before_use'}
    values=list(contacts.values())
    return {'businesses':list(businesses.values()),'contacts':values,'analysis':[],
        'summary':{'businesses':len(businesses),'unique_emails':len({row['email'] for row in values}),
        'sites_with_email':sum(bool(site['emails']) for site in sites.values()),'mailboxes_confirmed':0,
        'partial':bool(partial),'coverage_note':'Source websites provide context; individual mailboxes were not confirmed.'}}

def validate_analysis(rows,businesses):
    if not isinstance(rows,list) or len(rows)>100:raise ValueError('Use at most 100 reviewed businesses per analysis.')
    lookup={row['business_id']:row for row in businesses};seen=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)-{'business_id','note','confidence','sources','next_step'}:raise ValueError('Use the analysis record fields.')
        key=row.get('business_id')
        if key not in lookup or key in seen:raise ValueError('Analysis must refer to distinct existing businesses.')
        seen.add(key)
        if not isinstance(row.get('note'),str) or not 1<=len(row['note'])<=2000:raise ValueError('Add a short evidence-led review note.')
        if row.get('confidence') not in ['low','medium','high']:raise ValueError('Choose an analysis confidence.')
        sources=row.get('sources',[])
        allowed={domain(lookup[key].get(field,'')) for field in ['website','maps_source']}-{''}
        if not isinstance(sources,list) or not 1<=len(sources)<=5 or any(not public_url(url) or domain(url) not in allowed for url in sources):
            raise ValueError('Use source URLs from the business website or its Maps context.')
        if len(str(row.get('next_step','')))>1000:raise ValueError('Keep the next step concise.')
    return rows
