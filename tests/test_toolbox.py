import tempfile
import unittest
from pathlib import Path
from looksy.toolbox import catalog, search, plan, start, result

SLUG = 'khadinakbar/keyword-rank-tracker'

class Fake:
    price = .01
    calls = 0
    def metadata(self, slug):
        return dict(id='abcdefgh12345678',slug=slug,schema={'type':'object','properties':{'term':{'type':'string'}},'required':['term']},build_number='1.0.1', pricing={'events':{'row':{'price_usd':self.price}}})
    def start(self, actor, payload, options):
        assert options['build']=='1.0.1' and options['maxTotalChargeUsd']==2
        self.calls+=1
        return {'id':'known123456','status':'RUNNING'}
    def get_run(self, rid):
        return {'id':rid,'actId':'abcdefgh12345678','status':'SUCCEEDED','defaultDatasetId':'dataset1234'}
    def items(self, did, limit):return [],False

class ToolboxTests(unittest.TestCase):
    def test_search_and_identity(self):
        rows=catalog()
        self.assertEqual(len(rows),len({r['id'] for r in rows}))
        self.assertTrue(all(r['slug'].startswith('khadinakbar/') for r in rows))
        self.assertIn(SLUG,[r['slug'] for r in search('keyword rank tracker','rank-tracking')])
        self.assertIn('khadinakbar/ai-text-humanizer',[r['slug'] for r in search('humanizer','writing')])
    def test_plan_payment_binding_and_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            ws=Path(directory); c=Fake()
            p=plan(c,ws,SLUG,{'term':'pizza'},2)
            self.assertEqual(c.calls,0)
            with self.assertRaises(ValueError):start(c,ws,p['approval'],'0'*64)
            c.price=.02
            with self.assertRaises(ValueError):start(c,ws,p['approval'],p['approval'])
            self.assertEqual(c.calls,0)
            c.price=.01
            start(c,ws,p['approval'],p['approval'])
            start(c,ws,p['approval'],p['approval'])
            self.assertEqual(c.calls,1)
            out=result(c,ws,p['approval'],10)
            self.assertEqual(out['assessment'],'no dataset rows or output')
    def test_disallow_unknown_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as d:
            for slug,payload,budget in [('another/actor',{},2),(SLUG,{},2),(SLUG,{'term':'test'},float('nan'))]:
                with self.assertRaises(ValueError):plan(Fake(),Path(d),slug,payload,budget)
