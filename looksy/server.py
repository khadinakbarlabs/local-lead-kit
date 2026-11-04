"""Loopback-only app. API reads and writes require a random local session key."""
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import time
import urllib.parse
from . import notebook
from .api import ApifyClient
from .settings import Connections

STATIC=Path(__file__).parent/'static'

def make_server(service,port=8765,draft=None,connections=None,start_leads=False):
    from .core import validate_request
    draft = validate_request(draft) if draft is not None else None
    connections = connections or Connections.from_environment()
    start_leads = start_leads or draft is not None
    bound_key, bound_account = connections.binding()
    if bound_key:
        service._client = ApifyClient(token=bound_key)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass

        def respond(self,status,body,kind='application/json; charset=utf-8',filename=None,headers=None):
            if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',f"default-src 'self'; script-src 'self' 'nonce-{self.server.nonce}'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            for name,value in (headers or {}).items():self.send_header(name,value)
            self.end_headers();self.wfile.write(body)

        def authenticated(self):
            try:
                cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''))
                supplied=cookies.get('looksy_session')
                return bool(supplied and hmac.compare_digest(supplied.value,self.server.cookie_key))
            except (ValueError,TypeError):return False

        def guard(self,api=False,mutating=False):
            expected='127.0.0.1:'+str(self.server.server_port)
            if self.headers.get('Host')!=expected:return False
            origin=self.headers.get('Origin')
            if (mutating and origin!='http://'+expected) or (origin and origin!='http://'+expected):return False
            if api:
                if not self.authenticated():return False
                supplied=self.headers.get('X-Looksy-Key','')
                try:return hmac.compare_digest(supplied,self.server.session_key)
                except TypeError:return False
            return True

        def do_GET(self):
            parsed=urllib.parse.urlsplit(self.path);path=parsed.path
            if not self.guard(api=path.startswith('/api/')):return self.respond(403,{'error':'This local session is not authorized.'})
            try:
                if path in ('/', '/leads'):
                    if not self.authenticated():
                        return self.respond(200,b'<!doctype html><title>Looksy Agent</title><h1>Looksy Agent</h1><p>Open the private launch link from your assistant or terminal.</p>','text/html; charset=utf-8')
                    leads = path == '/leads' and connections.status()['onboarded']
                    template = 'index.html' if leads else 'dashboard.html'
                    bootstrap = {'session':self.server.session_key}
                    if leads:
                        bootstrap['draft'] = draft
                    else:
                        bootstrap['next'] = '/leads' if path == '/leads' else '/'
                    encoded = json.dumps(bootstrap).replace('<', r'\u003c')
                    page = (STATIC/template).read_text().replace('__BOOTSTRAP__',encoded).replace('__NONCE__',self.server.nonce)
                    return self.respond(200,page.encode(),'text/html; charset=utf-8')
                if path=='/connect':
                    ticket=urllib.parse.parse_qs(parsed.query).get('ticket',[''])[0]
                    with self.server.ticket_lock:
                        if time.monotonic()>self.server.ticket_expires or not self.server.ticket or not hmac.compare_digest(ticket,self.server.ticket):
                            return self.respond(403,{'error':'This private launch link expired or was already used. Ask your assistant for a fresh link.'})
                        self.server.ticket=''
                    return self.respond(303,{},headers={'Location':'/leads' if start_leads else '/','Set-Cookie':'looksy_session='+self.server.cookie_key+'; HttpOnly; SameSite=Strict; Path=/'})
                if path in ['/app.js','/style.css','/dashboard.js','/dashboard.css','/neighborhood.png','/looksy.png']:
                    kind={'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png'}[Path(path).suffix]
                    return self.respond(200,(STATIC/path[1:]).read_bytes(),kind)
                if path=='/api/settings':
                    return self.respond(200,connections.status())
                if path.startswith('/api/') and not connections.status()['onboarded']:
                    return self.respond(403,{'error':'Finish onboarding in the private dashboard first.'})
                if path=='/api/history':
                    return self.respond(200,{'briefs':notebook.history(service.workspace/'toolbox')[:50], 'campaigns':service.list_jobs()})
                if path=='/api/jobs':return self.respond(200,{'jobs':service.list_jobs(),'configured':bool(getattr(service,'_client',None) or os.environ.get('APIFY_TOKEN'))})
                query=urllib.parse.parse_qs(parsed.query)
                ident=query.get('id',[''])[0]
                if path in ['/api/job','/api/export','/api/export-preview']:
                    job=service.load(ident);kind=query.get('kind',['businesses'])[0]
                    if kind not in ['businesses','contacts','analysis']:raise ValueError('Choose a result table.')
                    destination=query.get('destination',['research'])[0]
                    if path in ['/api/export','/api/export-preview'] and destination!='research':
                        from .exports import prepare
                        if kind!='contacts':raise ValueError('Choose Contacts for a destination import.')
                        content,receipt=prepare((job.get('results') or {}).get('contacts',[]),destination)
                        if path=='/api/export-preview':return self.respond(200,receipt)
                        return self.respond(200,content.encode(),'text/csv; charset=utf-8','looksy-'+destination+'.csv')
                    if path=='/api/export-preview':raise ValueError('Choose a destination format.')
                    if path=='/api/export':return self.respond(200,service.export_csv(ident,kind).encode(),'text/csv; charset=utf-8','looksy-'+kind+'.csv')
                    result=job.get('results') or {};rows=result.get(kind,[]);q=query.get('q',[''])[0][:200].casefold()
                    if q:rows=[r for r in rows if q in json.dumps(r,ensure_ascii=False).casefold()]
                    offset=max(0,int(query.get('offset',['0'])[0]));limit=min(100,max(1,int(query.get('limit',['50'])[0])))
                    public={k:job.get(k) for k in ['id','status','created_at','request','progress','analysis_status','imported']}
                    public.update(summary=result.get('summary'),rows=rows[offset:offset+limit],total=len(rows),kind=kind)
                    plan=job.get('plan')
                    if plan:public['plan']={'hash':plan['hash'],'maximum_runs':plan['maximum_runs'],'cost_note':plan['cost_note'],
                        'actors':[{k:a.get(k) for k in ['slug','build_number','store_url','pricing']} for a in plan['actors'].values()]}
                    return self.respond(200,public)
                return self.respond(404,{'error':'This page was not found.'})
            except (ValueError,FileNotFoundError):return self.respond(400,{'error':'Choose a valid saved campaign or result table.'})
            except Exception:return self.respond(500,{'error':'The local result could not be read. Inspect it with your assistant.'})

        def do_POST(self):
            nonlocal bound_key, bound_account
            if not self.guard(api=True,mutating=True):return self.respond(403,{'error':'This local session is not authorized.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<2 or size>1024*1024:raise ValueError('Use a small campaign request.')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):raise ValueError('Use a campaign request object.')
                if self.path=='/api/settings/apify':
                    if set(body)-{'key'}:
                        raise ValueError('Submit only the Apify key.')
                    with service.lock:
                        if service.active:
                            raise ValueError('Wait for the active campaign to finish before changing Apify settings.')
                        status = connections.save_apify(body.get('key'))
                        bound_key, bound_account = connections.binding()
                        service._client = ApifyClient(token=bound_key)
                    return self.respond(200,status)
                if self.path=='/api/settings/ai':
                    return self.respond(200,connections.save_ai(body))
                if not connections.status()['onboarded']:
                    return self.respond(403,{'error':'Finish onboarding in the private dashboard first.'})
                if self.path in ('/api/plan','/api/approve','/api/resume'):
                    with service.lock:
                        if not bound_account or (bound_key, bound_account) != connections.binding():
                            return self.respond(409,{'error':'The Apify connection changed. Relaunch the dashboard to continue.'})
                        if self.path=='/api/plan':
                            job = service.prepare(body, account_id=bound_account)
                            return self.respond(200,{'id':job['id']})
                        job = service.load(body.get('id'))
                        if job.get('apify_account_id') != bound_account:
                            raise ValueError('This campaign has no verified link to the current Apify account. Inspect its saved runs in the original account before continuing.')
                        if self.path=='/api/approve':
                            service.approve(job['id'],body.get('hash'))
                            return self.respond(200,{'started':True})
                        service.resume(job['id'])
                        return self.respond(200,{'observing':True})
                if self.path=='/api/analysis-request':
                    with service.lock:
                        job=service.load(body.get('id'));offer=str(body.get('offer','')).strip()
                        if job['status'] not in ['COMPLETE','PARTIAL','IMPORTED'] or not 3<=len(offer)<=1000:raise ValueError('Add your offer after research results are ready.')
                        job['request'].update(offer=offer,analysis=True);job['analysis_status']='AWAITING_ASSISTANT';service.save(job)
                    return self.respond(200,{'analysis':'AWAITING_ASSISTANT'})
                return self.respond(404,{'error':'This action is not available.'})
            except (ValueError,FileNotFoundError) as exc:return self.respond(400,{'error':str(exc) if isinstance(exc,ValueError) else 'The saved campaign was not found.'})
            except Exception as exc:
                from .api import ApiError
                if isinstance(exc,ApiError):return self.respond(400,{'error':str(exc)})
                return self.respond(500,{'error':'The action stopped. Review the saved campaign with your assistant before trying again.'})

    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.session_key=secrets.token_urlsafe(32);server.nonce=secrets.token_urlsafe(24)
    import threading
    server.cookie_key=secrets.token_urlsafe(40);server.ticket=secrets.token_urlsafe(32)
    server.ticket_lock=threading.Lock();server.ticket_expires=time.monotonic()+300
    return server
