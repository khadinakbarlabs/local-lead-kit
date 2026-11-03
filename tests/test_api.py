import json
import unittest
from local_lead_kit.api import ApifyClient, ApiError, validate_input

class ApiTests(unittest.TestCase):
    def test_credentials_stay_in_headers_and_paid_start_is_not_retried(self):
        calls=[]
        def transport(request):
            calls.append(request)
            return {'data':{'id':'R','status':'RUNNING'}}
        client=ApifyClient('private-test-token',transport=transport)
        client.start('9XVfT1vIqqL4fiS4q',{'maxResults':500},{'build':'1.8.7','maxTotalChargeUsd':2,'timeout':300,'memory':2048,'restartOnError':False})
        self.assertEqual(len(calls),1)
        self.assertNotIn('private-test-token',calls[0].full_url)
        self.assertEqual(calls[0].get_header('Authorization'),'Bearer private-test-token')
        self.assertIn('maxTotalChargeUsd=2',calls[0].full_url)

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
