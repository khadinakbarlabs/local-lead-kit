import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from looksy import notebook
from looksy.server import make_server
from looksy.service import CampaignService
from looksy.settings import Connections


class DashboardTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.service = CampaignService(root/'workspace')
        self.store = Connections(root/'settings', verifier=self.verify)
        self.server = make_server(self.service, 0, connections=self.store)
        self.origin = 'http://127.0.0.1:'+str(self.server.server_port)
        self.headers = {'Cookie':'looksy_session='+self.server.cookie_key,
                        'X-Looksy-Key':self.server.session_key, 'Origin':self.origin}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    @staticmethod
    def verify(key):
        if key != 'fixture-apify':
            raise ValueError('Apify could not verify this key.')
        return 'fixture-account'

    def call(self, path, payload=None, **headers):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.origin+path, data=data, headers=self.headers | headers)
        try:
            with urlopen(request,timeout=4) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()

    def test_setup_gate_skip_history_and_dashboard_routes(self):
        self.assertEqual(self.call('/api/history')[0],403)
        self.assertEqual(self.call('/api/plan',{})[0],403)
        self.assertEqual(self.call('/api/settings/ai',{'skip':True})[0],400)
        self.assertEqual(self.call('/api/settings/apify',{'key':'wrong'})[0],400)
        self.assertEqual(self.call('/api/settings/apify',{'key':'fixture-apify'},Origin='http://elsewhere.test')[0],403)
        status, body = self.call('/api/settings/apify',{'key':'fixture-apify'})
        self.assertEqual(status,200)
        self.assertNotIn(b'fixture-apify',body)
        self.assertTrue(json.loads(body)['apify_verified'])
        self.assertEqual(self.call('/api/history')[0],403)
        self.assertTrue(json.loads(self.call('/api/settings/ai',{'skip':True})[1])['onboarded'])
        item=notebook.save(self.service.workspace/'toolbox','google-maps-leads-scraper','Example clients','CSV','Review')
        self.assertEqual(json.loads(self.call('/api/history')[1])['briefs'][0]['id'],item['id'])
        self.assertIn(b'/dashboard.js',self.call('/')[1])
        self.assertIn(b'/app.js',self.call('/leads')[1])

    def test_credentials_stay_out_of_responses_and_history(self):
        self.call('/api/settings/apify',{'key':'fixture-apify'})
        code, body=self.call('/api/settings/ai',{'provider':'gemini','key':'fixture-provider'})
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['ai_provider'],'gemini')
        for path in ['/','/leads','/api/settings','/api/history']:
            content=self.call(path)[1]
            self.assertNotIn(b'fixture-apify',content)
            self.assertNotIn(b'fixture-provider',content)
        self.assertIsNone(json.loads(self.call('/api/settings/ai',{'skip':True})[1])['ai_provider'])

    def test_active_research_preserves_its_connection(self):
        self.service.active.add('fixture-job')
        self.assertEqual(self.call('/api/settings/apify',{'key':'fixture-apify'})[0],400)
        self.assertFalse(self.store.status()['apify_verified'])


    def test_campaign_approval_and_resume_are_account_bound(self):
        self.call('/api/settings/apify',{'key':'fixture-apify'})
        self.call('/api/settings/ai',{'skip':True})
        job={'id':'a'*32, 'status':'PLANNED', 'request':{}, 'created_at':'fixture'}
        for account in [None,'other-account']:
            job['apify_account_id']=account
            self.service.save(job)
            for action in ['approve','resume']:
                code,body=self.call('/api/'+action,{'id':job['id'],'hash':'fixture'})
                self.assertEqual(code,400)
                self.assertIn(b'no verified link',body)
