import json
import http.cookiejar
import threading
import unittest
import urllib.error
import urllib.request
from looksy.server import make_server

class StubService:
    _client=None
    def list_jobs(self):return []

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server=make_server(StubService(),port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self,path,headers=None,data=None):
        request=urllib.request.Request(self.base+path,data=data,headers=headers or {})
        try:
            with urllib.request.urlopen(request,timeout=2) as r:return r.status,r.headers,r.read()
        except urllib.error.HTTPError as e:return e.code,e.headers,e.read()
    def test_api_rejects_unauthenticated_reads_and_cross_origin_writes(self):
        self.assertEqual(self.request('/api/jobs')[0],403)
        headers={'X-Looksy-Key':self.server.session_key,'Cookie':'looksy_session='+self.server.cookie_key,'Origin':'https://unrelated.example','Content-Type':'application/json'}
        self.assertEqual(self.request('/api/plan',headers,b'{}')[0],403)
        headers['Origin']=self.base
        self.assertEqual(self.request('/api/jobs',headers)[0],200)
        headers.pop('Cookie')
        self.assertEqual(self.request('/api/jobs',headers)[0],403)
    def test_host_check_and_frame_policy_protect_the_local_app(self):
        self.assertEqual(self.request('/',{'Host':'attacker.example'})[0],403)
        status,headers,body=self.request('/')
        self.assertEqual(status,200)
        self.assertEqual(headers['X-Frame-Options'],'DENY')
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertNotIn(b'APIFY_TOKEN=',body)
        self.assertNotIn(self.server.session_key.encode(),body)

    def test_private_launcher_is_single_use_and_cookie_scopes_api_access(self):
        jar=http.cookiejar.CookieJar()
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        ticket=self.server.ticket
        with opener.open(self.base+'/connect?ticket='+ticket,timeout=2) as response:
            body=response.read()
            self.assertEqual(response.url,self.base+'/')
            self.assertIn(self.server.session_key.encode(),body)
        cookies=list(jar)
        self.assertEqual(len(cookies),1)
        self.assertIn('HttpOnly',cookies[0]._rest)
        self.assertEqual(cookies[0]._rest.get('SameSite'),'Strict')
        self.assertEqual(self.request('/connect?ticket='+ticket)[0],403)
        self.assertEqual(self.request('/api/jobs',{'Cookie':'looksy_session='+cookies[0].value})[0],403)
        request=urllib.request.Request(self.base+'/api/jobs',headers={'X-Looksy-Key':self.server.session_key})
        with opener.open(request,timeout=2) as response:self.assertEqual(response.status,200)

if __name__=='__main__':unittest.main()
