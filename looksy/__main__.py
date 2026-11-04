import argparse
import json
import os
from pathlib import Path
import time

from .service import CampaignService
from .server import make_server
from .core import atomic_json
from .connection import connect, load_token, workspace

def main():
    parser=argparse.ArgumentParser(description='Looksy — private local business campaigns')
    parser.add_argument('--workspace',default=str(workspace()))
    parser.add_argument('--env-file',type=Path,help='Explicit private environment file containing APIFY_TOKEN')
    commands=parser.add_subparsers(dest='command',required=True)
    serve=commands.add_parser('serve');serve.add_argument('--port',type=int,default=8765)
    commands.add_parser('connect',help='Save your Apify key in your own terminal')
    commands.add_parser('list')
    status=commands.add_parser('status');status.add_argument('id')
    wait=commands.add_parser('wait');wait.add_argument('id');wait.add_argument('--seconds',type=int,default=45)
    imported=commands.add_parser('import-runs')
    for stage in ['maps','contacts','validator']:imported.add_argument('--'+stage,required=True)
    analysis=commands.add_parser('analysis-input');analysis.add_argument('id');analysis.add_argument('--limit',type=int,default=25)
    apply=commands.add_parser('apply-analysis');apply.add_argument('id');apply.add_argument('--file',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command == 'connect':
            connect()
            return
        load_token(args.env_file)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc)+'\n')
    service=CampaignService(args.workspace)
    if args.command=='serve':
        server=make_server(service,args.port)
        atomic_json(service.workspace/'server-access.json',{'pid':os.getpid(),'port':server.server_port,'cookie':server.cookie_key,'csrf':server.session_key,'ticket':server.ticket})
        print('Open Looksy: http://127.0.0.1:'+str(server.server_port)+'/connect?ticket='+server.ticket,flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
        return
    if args.command=='list':value=service.list_jobs()
    elif args.command in ['status','wait']:
        deadline=time.monotonic()+min(55,max(1,getattr(args,'seconds',1)))
        while True:
            job=service.load(args.id)
            if args.command=='status' or job['status'] not in ['PLANNED','QUEUED','RUNNING'] or time.monotonic()>=deadline:break
            time.sleep(2)
        value={k:job.get(k) for k in ['id','status','progress','analysis_status','request']};value['summary']=(job.get('results') or {}).get('summary')
    elif args.command=='import-runs':
        job=service.import_runs({s:getattr(args,s) for s in ['maps','contacts','validator']});value={'id':job['id'],'status':job['status'],'summary':job['results']['summary']}
    elif args.command=='analysis-input':
        job=service.load(args.id);limit=min(100,max(1,args.limit));result=job.get('results') or {}
        value={'id':job['id'],'offer':job['request'].get('offer',''),'businesses':result.get('businesses',[])[:limit],
               'summary':result.get('summary'),'instructions':'Use only observed facts and cited business website/Maps sources. Identify uncertainty. Never infer willingness to buy or mailbox deliverability.'}
    else:
        rows=json.loads(args.file.read_text());job=service.apply_analysis(args.id,rows);value={'id':job['id'],'analysis_status':job['analysis_status'],'reviewed':len(rows)}
    print(json.dumps(value,indent=2))

if __name__=='__main__':main()
