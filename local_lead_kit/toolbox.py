"""Discover Store Actors offline, preview one exact run, then observe it by ID."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from .api import ApifyClient, ApiError, validate_input
from .core import atomic_json, Ledger, NeedsAttention, start_once

INDEX = Path(__file__).with_name('catalog.json')

def catalog():
    return json.loads(INDEX.read_text())['actors']

def search(query='', shelf=None):
    terms = re.findall(r'[\w]+',query.lower())
    found=[]
    for row in catalog():
        if shelf and shelf not in row['shelves']: continue
        title=(row['title']+' '+row['slug'].split('/')[1]).lower().replace('-',' ')
        tags=' '.join(row['shelves']+row['categories']).lower().replace('-', ' ').replace('_',' ')
        if all(t in title+' '+tags for t in terms):
            found.append((sum(3*(t in title.split())+(t in title) for t in terms),row))
    return [r for _,r in sorted(found,key=lambda pair:(-pair[0],pair[1]['slug']))]

class ToolboxClient(ApifyClient):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.sources={r['slug']:r for r in catalog()}

    def metadata(self,stage):
        meta=super().metadata(stage)
        charges=[event.get('price_usd') for event in meta['pricing']['events'].values()]
        if not charges or not all(type(price) in (int,float) and math.isfinite(price) and price>=0 for price in charges):
            raise ApiError('Event pricing needs manual review before running this Actor.')
        return meta

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def plan(client,ws,slug,payload,budget,observation=None):
    if slug not in {r['slug'] for r in catalog()}: raise ValueError('Choose an exact Actor from the catalog.')
    try: cap=Decimal(str(budget))
    except InvalidOperation: raise ValueError('Enter a dollar allowance.') from None
    if not cap.is_finite() or not Decimal('.01')<=cap<=500 or cap!=cap.quantize(Decimal('.01')):
        raise ValueError('Enter an event charge cap between $0.01 and $500, to the nearest cent.')
    m=client.metadata(slug)
    if not isinstance(payload,dict):raise ValueError('Supply a JSON object as the Actor input.')
    validate_input(payload,m['schema'])
    if not re.fullmatch(r'\d+\.\d+\.\d+',str(m.get('build_number',''))):
        raise ValueError('Cannot pin the published build.')
    data={'slug':slug,'actor_id':m['id'],'input':payload,'metadata_hash':digest(m),
          'options':{'build':m['build_number'],'maxTotalChargeUsd':float(cap),'restartOnError':False}}
    if observation: data["observation"]=date.fromisoformat(observation).isoformat()
    key=digest(data)
    atomic_json(ws/key/'plan.json',data)
    return {'approval':key,**data,'pricing':m['pricing'],'notice':'Cap applies to Actor event charges. Platform usage may be billed separately.'}

def load_plan(ws,key):
    if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('Unknown plan.')
    data=json.loads((ws/key/'plan.json').read_text())
    if digest(data)!=key:raise ValueError('Plan changed; prepare a new plan.')
    return data

def start(client,ws,key,approval):
    p=load_plan(ws,key)
    if approval!=key:raise ValueError('Approval must match this exact plan.')
    ledger=Ledger(ws/key/'ledger.json',p['options']['maxTotalChargeUsd'])
    if not ledger.read()['entries'] and digest(client.metadata(p['slug']))!=p['metadata_hash']:
        raise ValueError('Published metadata changed. Prepare and review a new plan.')
    r=start_once(client,ledger,'actor',p['actor_id'],p['input'],p['options'])
    return {'run_id':r['id'],'status':r.get('status')}

def result(client,ws,key,limit):
    if not 1<=limit<=1000:raise ValueError('Read between one and 1,000 rows.')
    p=load_plan(ws,key)
    entry=Ledger(ws/key/'ledger.json',p['options']['maxTotalChargeUsd']).read()['entries'].get('actor',{})
    if not entry.get('run_id'):raise ValueError('No confirmed run to read.')
    r=client.get_run(entry['run_id'])
    if r.get('actId')!=p['actor_id']:raise ApiError('Run belongs to a different Actor.')
    state=r['status']
    summary={'status':state,'run_id':r['id']}
    if state not in {'SUCCEEDED','FAILED','ABORTED','TIMED-OUT'}:return summary
    rows,more=client.items(r['defaultDatasetId'],limit) if r.get('defaultDatasetId') else ([],False)
    store=r.get('defaultKeyValueStoreId')
    output=client.record(store,'OUTPUT') if store else None
    report=client.record(store,'RUN_SUMMARY') if store else None
    path=ws/key/'result.json'
    atomic_json(path,{**summary,'items':rows,'additional_rows':more,'output':output,'run_summary':report})
    assessment=('incomplete run; inspect evidence' if state!='SUCCEEDED' else
                'inspect returned evidence' if rows or output else 'no dataset rows or output')
    return {**summary,'rows_read':len(rows),'additional_rows':more,'assessment':assessment,'private_file':str(path)}

def main():
    parser=argparse.ArgumentParser(description='Looksy: search, preview and use a public Apify Actor.')
    parser.add_argument('--workspace',type=Path,default=Path.home()/'.local/share/local-lead-kit/toolbox')
    parser.add_argument('--env-file',type=Path)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('menu')
    f=commands.add_parser('find');f.add_argument('query',nargs='?',default='');f.add_argument('--shelf');f.add_argument('--limit',type=int,default=12)
    s=commands.add_parser('schema');s.add_argument('slug')
    p=commands.add_parser('plan');p.add_argument('slug');p.add_argument('--input-file',type=Path,required=True);p.add_argument('--budget',required=True);p.add_argument('--observation',help='Date label for a separately approved snapshot (YYYY-MM-DD)')
    s=commands.add_parser('start');s.add_argument('plan');s.add_argument('--approve',required=True)
    r=commands.add_parser('result');r.add_argument('plan');r.add_argument('--limit',type=int,default=100)
    a=parser.parse_args()
    if a.command=='menu':return dict(sorted(Counter(s for row in catalog() for s in row['shelves']).items()))
    if a.command=='find':
        matches=search(a.query,a.shelf)
        return {'matches':len(matches),'actors':matches[:max(1,min(1000,a.limit))]}
    if a.env_file:
        if a.env_file.stat().st_mode&0o077:raise ValueError('Choose an owner-readable private configuration file.')
        for line in a.env_file.read_text().splitlines():
            key,sep,value=line.partition('=')
            if key.strip()=='APIFY_TOKEN' and sep:os.environ['APIFY_TOKEN']=value.strip().strip('"\'')
    client=ToolboxClient()
    if a.command in ('plan','schema') and a.slug not in client.sources:raise ValueError('Unknown catalog Actor.')
    if a.command=='schema':return client.metadata(a.slug)
    if a.command=='plan':return plan(client,a.workspace,a.slug,json.loads(a.input_file.read_text()),a.budget,a.observation)
    if a.command=='start':return start(client,a.workspace,a.plan,a.approve)
    return result(client,a.workspace,a.plan,a.limit)

def cli():
    try:print(json.dumps(main(),indent=2))
    except (OSError,ValueError,ApiError,NeedsAttention) as err:sys.exit(str(err))

if __name__=='__main__':cli()
