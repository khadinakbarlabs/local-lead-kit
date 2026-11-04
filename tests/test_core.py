import tempfile
import unittest
from pathlib import Path

from looksy.core import (
    Ledger, NeedsAttention, build_plan, normalize_results, public_url,
    safe_csv, start_once, validate_request, validate_analysis,
)


class FakeClient:
    def __init__(self, fail=False):
        self.starts=0
        self.fail=fail

    def start(self, actor, payload, options):
        self.starts+=1
        if self.fail:
            raise TimeoutError('No response after dispatch')
        return {'id':'Run1234567890123','actId':actor,'status':'RUNNING'}

    def get_run(self, run_id):
        return {'id':run_id,'status':'RUNNING'}


class CampaignTests(unittest.TestCase):
    def request(self, **changes):
        return validate_request(dict(niche='Roofers',locations=['Austin, TX'],target=500,budget_usd=10,**changes))

    def test_default_target_and_multiple_territories(self):
        request=validate_request({'niche':'Dentists','locations':'Denver\nBoulder\ndenver','budget_usd':10})
        self.assertEqual(request['target'],500)
        self.assertEqual(request['locations'],['Denver','Boulder'])

    def test_volume_is_bounded_and_not_a_spend_authorization(self):
        for target in [0,True,5001,1.5]:
            with self.assertRaises(ValueError):
                validate_request({'niche':'Roofers','locations':['Austin'],'target':target,'budget_usd':10})
        with self.assertRaises(ValueError):
            validate_request({'niche':'Roofers','locations':['Austin'],'target':1000,'budget_usd':0})

    def test_plan_reserves_no_more_than_approved_allowance(self):
        request=self.request()
        plan=build_plan(request,{'maps':{'id':'M','build_id':'B'},'contacts':{'id':'C','build_id':'D'},'validator':{'id':'V','build_id':'E'}})
        self.assertLessEqual(sum(r['cap_usd'] for r in plan['reservations']),10)
        self.assertEqual(plan['request']['target'],500)
        self.assertFalse(plan['approved'])
        self.assertEqual(plan['maps_inputs'][0]['enrichEmails'],False)

    def test_shared_domain_does_not_merge_business_locations(self):
        maps=[{'place_id':str(i),'business_name':'Test Co','website':'https://example.org','full_address':str(i),'google_maps_url':'https://maps.google.com/?q='+str(i)} for i in [1,2]]
        sites=[{'source_url':'https://example.org','pages_crawled':1,'emails':['INFO@example.org','info@example.org']}]
        result=normalize_results(maps,sites,[],partial=True)
        self.assertEqual(len(result['businesses']),2)
        self.assertEqual(len(result['contacts']),2)
        self.assertEqual(result['summary']['unique_emails'],1)
        self.assertTrue(result['summary']['partial'])
        replay=normalize_results(maps*2,sites*2,[],partial=True)
        self.assertEqual(result,replay)

    def test_basic_checks_never_become_confirmed_mailboxes(self):
        maps=[{'place_id':'p','business_name':'Test','website':'https://example.org'}]
        sites=[{'source_url':'https://example.org','pages_crawled':1,'emails':['info@example.org','123456789info@example.org']}]
        checks=[{'normalizedEmail':'info@example.org','status':'valid','smtpCheck':'skipped','reasons':['syntax_valid','smtp_skipped']}]
        result=normalize_results(maps,sites,checks)
        self.assertEqual(result['summary']['mailboxes_confirmed'],0)
        self.assertEqual(result['contacts'][0]['mailbox_confirmed'],False)
        self.assertTrue(any(c['extraction_review']!='review_source_before_use' for c in result['contacts']))

    def test_missing_and_unreached_sites_remain_distinct(self):
        maps=[{'place_id':str(i),'business_name':'Test','website':f'https://site{i}.example.org'} for i in range(3)]
        sites=[{'source_url':'https://site0.example.org','pages_crawled':1,'emails':[]},{'source_url':'https://site1.example.org','pages_crawled':0,'emails':[]}]
        result=normalize_results(maps,sites,[])
        self.assertEqual([r['coverage'] for r in result['businesses']],['no_email_found','site_not_reached','not_processed'])

    def test_csv_and_public_url_safety(self):
        self.assertTrue(safe_csv(' =HYPERLINK("bad")').startswith("'"))
        for url in ['file:///etc/passwd','http://127.0.0.1','http://2130706433','http://user:pass@example.org','http://host.local','javascript:alert(1)']:
            self.assertIsNone(public_url(url))
        self.assertEqual(public_url('https://example.org/contact'),'https://example.org/contact')

    def test_uncertain_start_cannot_be_automatically_repeated(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=Ledger(Path(directory)/'ledger.json',5)
            client=FakeClient(fail=True)
            with self.assertRaises(NeedsAttention):
                start_once(client,ledger,'maps:0','M',{'maxResults':500},{'maxTotalChargeUsd':2})
            with self.assertRaises(NeedsAttention):
                start_once(client,ledger,'maps:0','M',{'maxResults':500},{'maxTotalChargeUsd':2})
            self.assertEqual(client.starts,1)
            self.assertEqual(ledger.read()['entries']['maps:0']['state'],'UNKNOWN')

    def test_known_start_is_read_back_and_budget_is_durable(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger.json';client=FakeClient();ledger=Ledger(path,3)
            first=start_once(client,ledger,'maps:0','M',{}, {'maxTotalChargeUsd':2})
            second=start_once(client,Ledger(path,3),'maps:0','M',{}, {'maxTotalChargeUsd':2})
            self.assertEqual(first['id'],second['id']);self.assertEqual(client.starts,1)
            with self.assertRaises(ValueError):
                start_once(client,Ledger(path,3),'maps:1','M',{}, {'maxTotalChargeUsd':2})

    def test_analysis_cannot_invent_companies_or_lose_source_context(self):
        businesses=[{'business_id':'a','website':'https://example.org','maps_source':'https://maps.google.com/?q=a'}]
        valid=[{'business_id':'a','note':'Review the website for the stated offer.','confidence':'low','sources':['https://example.org'] }]
        self.assertEqual(validate_analysis(valid,businesses),valid)
        for invalid in [[dict(valid[0],business_id='unknown')],[dict(valid[0],sources=['http://127.0.0.1'])],[dict(valid[0],sources=[])]]:
            with self.assertRaises(ValueError):validate_analysis(invalid,businesses)


if __name__=='__main__':
    unittest.main()
