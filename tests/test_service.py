import tempfile
import unittest
import csv
import io
from looksy.core import ACTORS
from looksy.service import CampaignService

class FakeApify:
    def __init__(self,partial=False):self.starts=[];self.runs={};self.partial=partial;self.drift=False
    def metadata(self,stage):
        fields={'maps':['searchQuery','location','maxResults','enrichEmails','requireEmail','requireWebsite','minLeadScore','maxReviews'],
            'contacts':['startUrls','maxPagesPerDomain','maxResults','followContactPages'],
            'validator':['emails','checkSmtp','checkCatchAll','concurrency','timeoutMs']}[stage]
        return {'id':ACTORS[stage]['id'],'slug':ACTORS[stage]['slug'],'build_id':('Changed' if self.drift else 'Build')+stage,
            'build_number':'1.0.0','schema':{'type':'object','properties':{k:{} for k in fields}},
            'pricing':{'events':{'apify-actor-start':{'price_usd':.001}}}}
    def start(self,actor,payload,options):
        stage=next(k for k,v in ACTORS.items() if v['id']==actor);self.starts.append(stage)
        r={'id':'Run'+stage,'actId':actor,'buildId':'Build'+stage,'status':'SUCCEEDED','defaultDatasetId':'Dataset'+stage,'defaultKeyValueStoreId':'Store'+stage,'usageTotalUsd':.01}
        self.runs[r['id']]=r;return r
    def get_run(self,ident):return self.runs[ident]
    def items(self,ident,limit):
        if ident=='Datasetmaps':return [{'place_id':'p','business_name':'Example Roofing','website':'https://example.org','full_address':'1 Example Street','google_maps_url':'https://maps.google.com/?q=example'}],False
        if ident=='Datasetcontacts':return [{'source_url':'https://example.org','pages_crawled':1,'emails':['info@example.org']}],False
        return [{'normalizedEmail':'info@example.org','status':'risky','reasons':['role_based','smtp_skipped']}],False
    def record(self,store,key):return {'outcome':'PARTIAL' if self.partial and store=='Storemaps' else 'COMPLETE'}

class ServiceTests(unittest.TestCase):
    def test_ai_notes_keep_the_real_business_name_in_app_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            service=CampaignService(folder,client=FakeApify(),poll_seconds=0)
            job=service.prepare({'niche':'Roofing','locations':['Example City'],'target':250,'budget_usd':10})
            service.approve(job['id'],job['plan']['hash'],background=False)
            business=service.load(job['id'])['results']['businesses'][0]
            reviewed=service.apply_analysis(job['id'],[{'business_id':business['business_id'],'note':'Inspect the contact page.','confidence':'low','sources':['https://example.org']}])
            self.assertEqual(reviewed['results']['analysis'][0]['business_name'],'Example Roofing')
            exported=list(csv.DictReader(io.StringIO(service.export_csv(job['id'],'analysis'))))
            self.assertEqual(exported[0]['business_name'],'Example Roofing')

    def test_csv_keeps_optional_review_fields_and_neutralizes_formulas(self):
        with tempfile.TemporaryDirectory() as folder:
            service=CampaignService(folder)
            ident='a'*32
            service.save({'id':ident,'results':{'analysis':[
                {'business_id':'one','note':'=HYPERLINK("https://example.com")'},
                {'business_id':'two','note':'Review the source.','next_step':'Inspect the contact page.'}
            ]}})
            rows=list(csv.DictReader(io.StringIO(service.export_csv(ident,'analysis'))))
            self.assertEqual(rows[0]['next_step'],'')
            self.assertEqual(rows[1]['next_step'],'Inspect the contact page.')
            self.assertTrue(rows[0]['note'].startswith("'="))
    def test_plan_is_read_only_then_approval_runs_the_three_exact_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            client=FakeApify(partial=True);service=CampaignService(directory,client=client,poll_seconds=0)
            job=service.prepare({'niche':'Roofing','locations':['Example City'],'target':500,'budget_usd':10})
            self.assertEqual(client.starts,[])
            with self.assertRaises(ValueError):service.approve(job['id'],'different-hash',background=False)
            service.approve(job['id'],job['plan']['hash'],background=False)
            state=service.load(job['id'])
            self.assertEqual(client.starts,['maps','contacts','validator'])
            self.assertEqual(state['status'],'PARTIAL')
            self.assertEqual(state['results']['summary']['businesses'],1)
            self.assertEqual(state['results']['summary']['mailboxes_confirmed'],0)
            service.execute(job['id'])
            self.assertEqual(client.starts,['maps','contacts','validator'])
            self.assertEqual(service.load(job['id'])['results']['summary']['businesses'],1)

    def test_changed_build_requires_a_new_review(self):
        with tempfile.TemporaryDirectory() as directory:
            client=FakeApify();service=CampaignService(directory,client=client)
            job=service.prepare({'niche':'Roofing','locations':['Example City'],'target':500,'budget_usd':10});client.drift=True
            with self.assertRaises(ValueError):service.approve(job['id'],job['plan']['hash'],background=False)
            self.assertEqual(client.starts,[])

    def test_paths_cannot_escape_private_job_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            service=CampaignService(directory,client=FakeApify())
            for bad in ['../../secrets','abc/../def','not-a-job']:
                with self.assertRaises(ValueError):service.load(bad)

    def test_partial_source_without_useful_rows_is_not_an_empty_market_success(self):
        class EmptyPartial(FakeApify):
            def items(self,ident,limit):return [],False
        with tempfile.TemporaryDirectory() as directory:
            client=EmptyPartial(partial=True);service=CampaignService(directory,client=client,poll_seconds=0)
            job=service.prepare({'niche':'Roofing','locations':['Example City'],'target':500,'budget_usd':10})
            service.approve(job['id'],job['plan']['hash'],background=False)
            self.assertEqual(service.load(job['id'])['status'],'ATTENTION')
            self.assertEqual(client.starts,['maps'])

    def test_failed_contact_stage_preserves_useful_rows_and_stops_paid_starts(self):
        class FailedContact(FakeApify):
            def start(self,actor,payload,options):
                run=super().start(actor,payload,options)
                if actor==ACTORS['contacts']['id']:run['status']='FAILED'
                return run
        with tempfile.TemporaryDirectory() as directory:
            client=FailedContact();service=CampaignService(directory,client=client,poll_seconds=0)
            job=service.prepare({'niche':'Roofing','locations':['Example City'],'target':500,'budget_usd':10})
            service.approve(job['id'],job['plan']['hash'],background=False);state=service.load(job['id'])
            self.assertEqual(state['status'],'ATTENTION');self.assertEqual(client.starts,['maps','contacts'])
            self.assertEqual(len(state['results']['businesses']),1);self.assertEqual(len(state['results']['contacts']),1)

if __name__=='__main__':unittest.main()
