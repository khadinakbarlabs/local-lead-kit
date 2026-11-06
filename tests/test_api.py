import json
from unittest.mock import patch
from tests.test_pricing import price_fixture
import unittest
from looksy.api import ApifyClient, ApiError, validate_input, metadata_digest

class ApiTests(unittest.TestCase):
    actor_id='9XVfT1vIqqL4fiS4q'
    build_id='Build12345678901'

    def fixtures(self):
        actor={'id':self.actor_id,'username':'khadinakbar','name':'google-maps-leads-scraper',
               'isPublic':True,'isDeprecated':False,'actorPermissionLevel':'LIMITED_PERMISSIONS',
               'defaultRunOptions':{'build':'latest','memoryMbytes':2048,'timeoutSecs':3600},
               'taggedBuilds':{'latest':{'buildId':self.build_id,'buildNumber':'1.8.7'}},
               'pricingInfos':[price_fixture()]}
        build={'id':self.build_id,'actId':self.actor_id,'status':'SUCCEEDED','buildNumber':'1.8.7',
               'actorDefinition':{'permissions':{'type':'limited','permissions':['DATASET']}},
               'inputSchema':{'type':'object','properties':{'maxResults':{'type':'integer'}}}}
        return actor,build

    def client(self, actor=None, build=None, **kwargs):
        fixture_actor,fixture_build=self.fixtures()
        self.calls=[]
        def transport(request):
            self.calls.append(request)
            if request.get_method()=='POST':return {'data':{'id':'Run1234567890','status':'RUNNING'}}
            if '/actor-builds/' in request.full_url:return {'data':fixture_build if build is None else build}
            return {'data':fixture_actor if actor is None else actor}
        return ApifyClient('private-test-token',transport=transport,**kwargs)

    def options(self, **changes):
        return {'build':'1.8.7','maxTotalChargeUsd':2,'timeout':300,'memory':2048,'restartOnError':False,**changes}

    def test_credentials_stay_in_headers_and_paid_start_is_not_retried(self):
        self.client().start(self.actor_id,{'maxResults':500},self.options())
        paid=[r for r in self.calls if r.get_method()=='POST']
        self.assertEqual(len(paid),1)
        self.assertEqual(len(self.calls),3)
        for request in self.calls:
            self.assertNotIn('private-test-token',request.full_url)
            self.assertEqual(request.get_header('Authorization'),'Bearer private-test-token')
        self.assertIn('maxTotalChargeUsd=2',paid[0].full_url)
        self.assertIn('restartOnError=false',paid[0].full_url)
        self.assertIn('forcePermissionLevel=LIMITED_PERMISSIONS',paid[0].full_url)

    def test_metadata_verifies_actor_and_exact_build(self):
        meta=self.client().metadata('maps')
        self.assertEqual(meta['build_id'],self.build_id)
        self.assertEqual(meta['permission_level'],'LIMITED_PERMISSIONS')
        self.assertEqual(meta['build_permissions']['type'],'limited')
        self.assertTrue(meta['pricing']['isPPEPlatformUsagePaidByUser'])
        self.assertIn('minimalMaxTotalChargeUsd',meta['pricing'])
        self.assertEqual(meta['default_run_options']['timeoutSecs'],3600)

    def test_metadata_blocks_unknown_or_full_permissions(self):
        for level in ['FULL_PERMISSIONS',None,'limited','UNKNOWN']:
            actor,build=self.fixtures();actor['actorPermissionLevel']=level
            with self.subTest(level=level),self.assertRaisesRegex(ApiError,'[Pp]ermission'):
                self.client(actor,build).metadata('maps')
        for permissions in [{'type':'full'},{'type':'unknown'},None,{}]:
            actor,build=self.fixtures();build['actorDefinition']['permissions']=permissions
            with self.subTest(permissions=permissions),self.assertRaisesRegex(ApiError,'[Pp]ermission'):
                self.client(actor,build).metadata('maps')

    def test_full_permission_default_override_is_blocked(self):
        actor,build=self.fixtures()
        actor['defaultRunOptions']['forcePermissionLevel']='FULL_PERMISSIONS'
        with self.assertRaisesRegex(ApiError,'[Pp]ermission'):
            self.client(actor,build).metadata('maps')

    def test_metadata_blocks_identity_publication_and_build_drift(self):
        for key,value in [('id','OtherActor123'),('username','someoneelse'),('isPublic',False),('isPublic','true'),('isDeprecated',True)]:
            actor,build=self.fixtures();actor[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ApiError):self.client(actor,build).metadata('maps')
        for key,value in [('id','OtherBuild123'),('actId','OtherActor123'),('status','RUNNING'),('buildNumber','1.8.8')]:
            actor,build=self.fixtures();build[key]=value
            with self.subTest(key=key),self.assertRaises(ApiError):self.client(actor,build).metadata('maps')

    def test_public_metadata_mode_ignores_all_credentials_and_cannot_read_private_resources_or_start(self):
        with patch.dict('os.environ',{'APIFY_TOKEN':'environment-secret'}):
            client=self.client(public_metadata_only=True)
            client.metadata('maps')
            for request in self.calls:self.assertIsNone(request.get_header('Authorization'))
            for path in ['users/me','actor-runs/Run1234567890','acts/'+self.actor_id+'/run-sync',
                         'acts/'+self.actor_id+'?token=x','actor-builds/'+self.build_id+'/log']:
                with self.subTest(path=path),self.assertRaises((ApiError,ValueError)):client.request(path)
            with self.assertRaises(ApiError):client.start(self.actor_id,{},self.options())
            self.assertEqual(len(self.calls),2)

    def test_invalid_caps_timeouts_and_restarts_never_send_a_request(self):
        for cap in [True,0,-1,float('nan'),float('inf'),'2',501]:
            client=self.client()
            with self.subTest(cap=cap),self.assertRaises(ValueError):client.start(self.actor_id,{},self.options(maxTotalChargeUsd=cap))
            self.assertEqual(self.calls,[])
        for timeout in [None,True,0,-1,3601,float('nan'),300.5,'300']:
            client=self.client()
            with self.subTest(timeout=timeout),self.assertRaises(ValueError):client.start(self.actor_id,{},self.options(timeout=timeout))
            self.assertEqual(self.calls,[])
        for restart in [True,None,'false']:
            client=self.client()
            with self.subTest(restart=restart),self.assertRaises(ValueError):client.start(self.actor_id,{},self.options(restartOnError=restart))
            self.assertEqual(self.calls,[])

    def test_start_rechecks_live_permissions_exact_build_and_minimum(self):
        for mutation in ['permission','build','minimum','tier']:
            actor,build=self.fixtures()
            if mutation=='permission':actor['actorPermissionLevel']='FULL_PERMISSIONS'
            if mutation=='build':
                actor['taggedBuilds']['latest']['buildNumber']='1.8.8';build['buildNumber']='1.8.8'
            if mutation=='minimum':actor['pricingInfos'][0]['minimalMaxTotalChargeUsd']=3
            if mutation=='tier':
                event=actor['pricingInfos'][0]['pricingPerEvent']['actorChargeEvents']['result']
                del event['eventPriceUsd'];event['eventTieredPricingUsd']={'FREE':{'tieredEventPriceUsd':1}}
            client=self.client(actor,build)
            with self.subTest(mutation=mutation),self.assertRaises((ApiError,ValueError)):
                client.start(self.actor_id,{},self.options())
            self.assertFalse(any(r.get_method()=='POST' for r in self.calls))

    def test_final_metadata_drift_blocks_flat_price_payer_and_schema_changes(self):
        for change in ['price','payer','schema','minimum']:
            actor,build=self.fixtures()
            client=self.client(actor,build)
            approved=metadata_digest(client.metadata('maps'))
            if change=='price':actor['pricingInfos'][0]['pricingPerEvent']['actorChargeEvents']['result']['eventPriceUsd']=0.02
            if change=='payer':actor['pricingInfos'][0]['isPPEPlatformUsagePaidByUser']=False
            if change=='schema':build['inputSchema']['properties']['newField']={'type':'string'}
            if change=='minimum':actor['pricingInfos'][0]['minimalMaxTotalChargeUsd']=0.1
            with self.subTest(change=change),self.assertRaisesRegex(ApiError,'metadata changed'):
                client.start(self.actor_id,{},self.options(expectedMetadataHash=approved))
            self.assertFalse(any(r.get_method()=='POST' for r in self.calls))

    def test_matching_metadata_hash_is_local_only_and_does_not_mutate_options(self):
        client=self.client()
        approved=metadata_digest(client.metadata('maps'))
        options=self.options(expectedMetadataHash=approved)
        client.start(self.actor_id,{},options)
        paid=[r for r in self.calls if r.get_method()=='POST']
        self.assertEqual(len(paid),1)
        self.assertNotIn('expectedMetadataHash',paid[0].full_url)
        self.assertNotIn(approved,paid[0].full_url)
        self.assertEqual(options['expectedMetadataHash'],approved)
        from looksy.toolbox import digest
        self.assertEqual(metadata_digest({'b':2,'a':1}),digest({'a':1,'b':2}))

    def test_invalid_metadata_hash_is_rejected_before_requests(self):
        for value in [None,False,'','a'*63,'A'*64,'x'*64]:
            client=self.client()
            with self.subTest(value=value),self.assertRaises(ValueError):
                client.start(self.actor_id,{},self.options(expectedMetadataHash=value))
            self.assertEqual(self.calls,[])

    def test_failed_paid_post_has_no_retry(self):
        client=self.client();base=client.transport
        def transport(request):
            response=base(request)
            if request.get_method()=='POST':raise TimeoutError('response lost')
            return response
        client.transport=transport
        with self.assertRaises((ApiError,TimeoutError)):client.start(self.actor_id,{},self.options())
        self.assertEqual(sum(r.get_method()=='POST' for r in self.calls),1)

    def test_dataset_reader_paginates_to_its_declared_limit(self):
        offsets=[]
        def transport(request):
            from urllib.parse import urlsplit,parse_qs
            query=parse_qs(urlsplit(request.full_url).query);offset=int(query['offset'][0]);limit=int(query['limit'][0]);offsets.append(offset)
            return [{'i':i} for i in range(offset,min(205,offset+limit))]
        rows,truncated=ApifyClient('x',transport=transport).items('Dataset1234567890',200)
        self.assertEqual(len(rows),200);self.assertTrue(truncated);self.assertEqual(offsets,[0,100,200])

    def test_schema_changes_block_unsupported_inputs(self):
        schema={'type':'object','properties':{'maxResults':{'type':'integer','minimum':1,'maximum':5000}},'required':['maxResults']}
        validate_input({'maxResults':1000},schema)
        for bad in [{'maxResults':5001},{'maxResults':True},{'unknown':5},{}]:
            with self.assertRaises(ValueError):validate_input(bad,schema)

    def test_unknown_actor_is_not_an_arbitrary_authenticated_url(self):
        client=ApifyClient('x',transport=lambda r:{})
        for actor in ['https://bad.example','../user','unlistedActor']:
            with self.assertRaises(ValueError):client.start(actor,{}, {'maxTotalChargeUsd':1})

    def test_invalid_response_is_an_error_not_an_empty_success(self):
        client=ApifyClient('x',transport=lambda r:{'unexpected':'shape'})
        with self.assertRaises(ApiError):client.get_run('Run1234567890123')

if __name__=='__main__':unittest.main()
