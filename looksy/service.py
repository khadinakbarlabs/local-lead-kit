"""Private campaign workspace and a bounded, resumable three-Actor worker."""
from datetime import datetime, timezone
import csv
import io
import json
import math
import os
from pathlib import Path
import re
import threading
import time
import uuid

from .api import ApifyClient, ApiError, validate_input
from .core import ACTORS, Ledger, NeedsAttention, atomic_json, build_plan, domain, normalize_results, public_url, safe_csv, start_once, validate_analysis, validate_request

class StillRunning(RuntimeError):pass

class CampaignService:
    def __init__(self,workspace,client=None,poll_seconds=5):
        self.workspace=Path(workspace).resolve();self.workspace.mkdir(parents=True,exist_ok=True,mode=0o700)
        self._client=client;self.poll_seconds=poll_seconds;self.lock=threading.RLock();self.active=set()

    @property
    def client(self):
        if self._client is None:self._client=ApifyClient()
        return self._client

    def folder(self,job_id):
        if not isinstance(job_id,str) or not re.fullmatch(r'[a-f0-9]{32}',job_id):raise ValueError('Choose a valid campaign.')
        return self.workspace/job_id

    def load(self,job_id):return json.loads((self.folder(job_id)/'campaign.json').read_text())
    def save(self,job):atomic_json(self.folder(job['id'])/'campaign.json',job)

    def list_jobs(self):
        result=[]
        for path in self.workspace.glob('*/campaign.json'):
            if re.fullmatch('[a-f0-9]{32}',path.parent.name):
                job=json.loads(path.read_text());result.append({k:job[k] for k in ['id','status','created_at','request']})
        return sorted(result,key=lambda j:j['created_at'],reverse=True)[:50]

    def prepare(self,value,account_id=None):
        request=validate_request(value);stages=['maps','contacts','validator'] if request['include_contacts'] else ['maps']
        metadata={stage:self.client.metadata(stage) for stage in stages};plan=build_plan(request,metadata)
        for payload in plan['maps_inputs']:validate_input(payload,metadata['maps']['schema'])
        for reservation in plan['reservations']:
            events=metadata[reservation['stage']]['pricing'].get('events',{})
            startup=events.get('apify-actor-start',{}).get('price_usd',0)
            if isinstance(startup,(int,float)) and reservation['cap_usd']<startup:raise ValueError('The allowance is below the current minimum for one of the planned runs. Increase it or reduce the target.')
        job={'id':uuid.uuid4().hex,'status':'PLANNED','created_at':datetime.now(timezone.utc).isoformat(),
             'request':request,'plan':plan,'approved':False,'progress':{'message':'Review the plan before any paid run.'},'results':None,'runs':[]}
        if account_id:
            job['apify_account_id'] = account_id
        self.save(job);return job

    def approve(self,job_id,plan_hash,background=True):
        with self.lock:
            job=self.load(job_id)
            if job['status']!='PLANNED' or job['plan']['hash']!=plan_hash:raise ValueError('The plan changed or already started. Review its current state.')
            for stage,expected in job['plan']['actors'].items():
                current=self.client.metadata(stage)
                if current['build_id']!=expected['build_id'] or current['pricing']!=expected['pricing']:raise ValueError('The Actor build or price changed. Create a fresh plan before running.')
            job['approved']=True;job['status']='QUEUED';self.save(job)
        if background:self.resume(job_id)
        else:self.execute(job_id)

    def resume(self,job_id):
        with self.lock:
            job=self.load(job_id)
            if not job.get('approved') or job.get('imported'):raise ValueError('This campaign is not an approved live collection.')
            if self.active:raise ValueError('One campaign is already active in this app. Review it before starting another.')
            self.active.add(job_id)
            def run():
                try:self.execute(job_id)
                finally:
                    with self.lock:self.active.discard(job_id)
            threading.Thread(target=run,daemon=True).start()

    def _stage(self,job,stage,index,payload,limit):
        key=f'{stage}:{index}';plan=job['plan'];meta=plan['actors'][stage]
        validate_input(payload,meta['schema'])
        reservation=next((r for r in plan['reservations'] if r['key']==key),None)
        if reservation is None:raise NeedsAttention('This stage exceeds the approved campaign plan.')
        ledger=Ledger(self.folder(job['id'])/'ledger.json',job['request']['budget_usd'])
        if key not in ledger.read()['entries']:
            current=self.client.metadata(stage)
            if current['build_id']!=meta['build_id'] or current['pricing']!=meta['pricing']:raise NeedsAttention('A source changed since approval. Review a new plan before another paid start.')
        options={'build':meta['build_number'],'memory':ACTORS[stage]['memory'],'timeout':ACTORS[stage]['timeout'],
                 'maxTotalChargeUsd':reservation['cap_usd'],'restartOnError':False}
        job['progress']={'stage':stage,'batch':index+1,'message':{'maps':'Finding businesses','contacts':'Reading public website contacts','validator':'Checking extracted addresses'}[stage]};job['status']='RUNNING';self.save(job)
        run=start_once(self.client,ledger,key,meta['id'],payload,options)
        if run.get('actId')!=meta['id'] or run.get('buildId')!=meta['build_id']:raise NeedsAttention('The returned run identity or build differs from the approved source.')
        deadline=time.monotonic()+ACTORS[stage]['timeout']+120
        while run['status'] in ['READY','RUNNING','TIMING-OUT','ABORTING']:
            if time.monotonic()>deadline:raise StillRunning('The saved run is still active. Resume observation of the same run; no new start is needed.')
            time.sleep(self.poll_seconds);run=self.client.get_run(run['id'])
        rows,truncated=self.client.items(run['defaultDatasetId'],limit)
        output=self.client.record(run['defaultKeyValueStoreId'],'OUTPUT')
        summary=self.client.record(run['defaultKeyValueStoreId'],'RUN_SUMMARY')
        bundle={'stage':stage,'key':key,'run':{k:run.get(k) for k in ['id','actId','buildId','status','startedAt','finishedAt','usageTotalUsd','chargedEventCounts','pricingInfo']},
                'rows':rows,'output':output,'summary':summary,'truncated':truncated}
        atomic_json(self.folder(job['id'])/(key.replace(':','-')+'.json'),bundle)
        receipt={k:bundle['run'][k] for k in ['id','actId','buildId','status','usageTotalUsd']};receipt.update(stage=stage,key=key)
        job['runs']=[r for r in job['runs'] if r['key']!=key]+[receipt];self.save(job)
        if run['status']!='SUCCEEDED':raise NeedsAttention('A source run did not finish successfully. Its saved results need review before another stage.')
        outcomes=[r.get('outcome','') for r in [output,summary] if isinstance(r,dict)]
        if not rows and any(str(o).upper() in ['FAILED','ERROR','BLOCKED'] for o in outcomes):raise NeedsAttention('The source failed to return useful data; this is not an empty market result.')
        partial=truncated or any(str(o).upper()=='PARTIAL' for o in outcomes) or not outcomes
        useful=any(isinstance(row,dict) and row.get({'maps':'business_name','contacts':'source_url','validator':'normalizedEmail'}[stage]) for row in rows)
        errors=any(any(record.get(field) for field in ['error','errors','errorCount','failureReason']) for record in [output,summary] if isinstance(record,dict))
        if not useful and (stage!='maps' or partial or errors or rows):
            raise NeedsAttention('The source did not return useful records and needs inspection; it is not a complete empty-market result.')
        return rows,partial

    def execute(self,job_id):
        job=self.load(job_id)
        if not job.get('approved') or job.get('imported'):raise ValueError('Approve the actual campaign plan before live collection.')
        maps=[];sites=[];checks=[];partial=False
        try:
            for i,payload in enumerate(job['plan']['maps_inputs']):
                if len({r.get('place_id') or r.get('google_maps_url') for r in maps})>=job['request']['target']:break
                rows,p=self._stage(job,'maps',i,payload,job['request']['target']);maps.extend(rows);partial|=p
            # Branch-aware normalization selects real unique records up to the requested target.
            keys=set();unique=[]
            for row in maps:
                if not isinstance(row,dict) or not row.get('business_name'):continue
                identity=row.get('place_id') or row.get('google_maps_url') or json.dumps(row,sort_keys=True)
                if identity not in keys:keys.add(identity);unique.append(row)
                if len(unique)>=job['request']['target']:break
            maps=unique
            if job['request']['include_contacts'] and maps:
                urls={}
                for row in maps:
                    url=public_url(row.get('website',''))
                    if url:urls.setdefault(domain(url),url)
                ordered=list(urls.values())
                for i,start in enumerate(range(0,len(ordered),50)):
                    batch=ordered[start:start+50]
                    rows,p=self._stage(job,'contacts',i,{'startUrls':[{'url':url} for url in batch],
                        'maxPagesPerDomain':3,'maxResults':len(batch),'followContactPages':True},len(batch))
                    sites.extend(rows);partial|=p
                emails=sorted({str(e).strip().lower() for r in sites for e in r.get('emails',[]) if isinstance(e,str) and 3<=len(e)<=320})
                cap=job['request']['target']*5
                if len(emails)>cap:partial=True
                for i,start in enumerate(range(0,min(len(emails),cap),250)):
                    rows,p=self._stage(job,'validator',i,{'emails':emails[start:min(start+250,cap)],'checkSmtp':False,
                        'checkCatchAll':False,'concurrency':5,'timeoutMs':8000},250)
                    checks.extend(rows);partial|=p
            result=normalize_results(maps,sites,checks,partial=partial)
            result['summary']['target']=job['request']['target']
            job['results']=result
            job['status']='EMPTY' if not result['businesses'] else 'PARTIAL' if partial else 'COMPLETE'
            if job['request']['analysis'] and result['businesses']:job['analysis_status']='AWAITING_ASSISTANT'
            job['progress']={'message':'Results are ready to review.','actual_businesses':len(result['businesses'])}
        except (NeedsAttention,StillRunning,ApiError,ValueError) as exc:
            # Include already saved useful records; no silent success or paid retry.
            job['status']='WAITING' if isinstance(exc,StillRunning) else 'ATTENTION'
            job['progress']={'message':str(exc)}
            saved=self.saved_rows(job_id)
            job['results']=normalize_results(saved['maps'] or maps,saved['contacts'] or sites,saved['validator'] or checks,partial=True)
        except Exception:
            job['status']='ATTENTION';job['progress']={'message':'The campaign stopped unexpectedly. Inspect its saved checkpoint with your assistant before resuming.'}
            saved=self.saved_rows(job_id)
            job['results']=normalize_results(saved['maps'] or maps,saved['contacts'] or sites,saved['validator'] or checks,partial=True)
        self.save(job);return job

    def saved_rows(self,job_id):
        result={stage:[] for stage in ACTORS}
        for path in sorted(self.folder(job_id).glob('*-*.json')):
            value=json.loads(path.read_text());stage=value.get('stage')
            if stage in result and isinstance(value.get('rows'),list):result[stage].extend(value['rows'])
        return result

    def apply_analysis(self,job_id,rows):
        with self.lock:
            job=self.load(job_id)
            if job['status'] not in ['COMPLETE','PARTIAL','IMPORTED']:raise ValueError('Wait for research results before adding AI review.')
            rows=validate_analysis(rows,job['results']['businesses'])
            names={business['business_id']:business['business_name'] for business in job['results']['businesses']}
            job['results']['analysis']=[dict(row,business_name=names[row['business_id']]) for row in rows]
            job['analysis_status']='COMPLETE' if len(rows)>=min(25,len(job['results']['businesses'])) else 'PARTIAL'
            job['results']['summary']['ai_reviewed']=len(rows);self.save(job);return job

    def export_csv(self,job_id,kind):
        if kind not in ['businesses','contacts','analysis']:raise ValueError('Choose a result table.')
        job=self.load(job_id);rows=(job.get('results') or {}).get(kind,[])
        output=io.StringIO(newline='')
        if rows:
            fields=list(dict.fromkeys(key for row in rows for key in row))
            writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
            for row in rows:writer.writerow({k:safe_csv(json.dumps(v) if isinstance(v,(list,dict)) else v) for k,v in row.items()})
        return output.getvalue()

    def import_runs(self,run_ids):
        if set(run_ids)!=set(ACTORS):raise ValueError('Provide exactly the three saved run IDs.')
        bundles={};partial=False
        for stage,ident in run_ids.items():
            run=self.client.get_run(ident)
            if run.get('actId')!=ACTORS[stage]['id'] or run.get('status') not in ['SUCCEEDED','FAILED','TIMED-OUT','ABORTED']:raise ValueError('Use finished runs from the configured exact Actors.')
            rows,truncated=self.client.items(run['defaultDatasetId'],5000 if stage!='validator' else 25000)
            output=self.client.record(run['defaultKeyValueStoreId'],'OUTPUT')
            inputs=self.client.record(run['defaultKeyValueStoreId'],'INPUT')
            bundles[stage]={'run_id':ident,'build_id':run.get('buildId'),'rows':rows,'output':output,'input':inputs}
            partial|=truncated or run['status']!='SUCCEEDED' or not output or output.get('outcome')=='PARTIAL'
        request=bundles['maps']['input'] or {}
        result=normalize_results(bundles['maps']['rows'],bundles['contacts']['rows'],bundles['validator']['rows'],partial=partial)
        target=request.get('maxResults',len(result['businesses']));result['summary']['target']=target
        job={'id':uuid.uuid4().hex,'status':'IMPORTED','imported':True,'created_at':datetime.now(timezone.utc).isoformat(),
             'request':{'niche':request.get('searchQuery','Saved research'),'locations':[request.get('location','Saved territory')],
                'target':target,'budget_usd':0,'include_contacts':True,'analysis':False,'offer':''},
             'approved':False,'plan':None,'results':result,'runs':[{'stage':stage,'id':b['run_id'],'buildId':b['build_id']} for stage,b in bundles.items()],
             'progress':{'message':'Saved trial results are ready to review.'}}
        for stage,bundle in bundles.items():atomic_json(self.folder(job['id'])/(stage+'-import.json'),bundle)
        self.save(job);return job
