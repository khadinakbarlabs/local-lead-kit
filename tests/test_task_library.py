import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from looksy import notebook
from looksy.core import atomic_json
from looksy.tasks import browse,library,tree
from looksy.toolbox import digest

class LibraryTests(unittest.TestCase):
    def test_all_actors_are_routable_with_evidence(self):
        catalog=json.loads((Path(__file__).parents[1]/'looksy/catalog.json').read_text())
        cards=library();paths=tree()
        self.assertEqual({r['slug'] for r in catalog['actors']},{c['actor'] for c in cards.values()})
        for c in cards.values():
            self.assertIn(c['subcategory'],paths[c['category']])
            if c['preset']:
                for field in c['preset']:self.assertIn(field,c['input_fields'])
    def test_intents_with_similar_terms(self):
        for query,expected in [('flight prices','google-flights-scraper'),('where does my website rank','keyword-rank-tracker'),('which sources AI answers cite','ai-citations-tracker'),('GitHub issues','github-deep-scraper#mode=issues')]:
            self.assertEqual(browse(query)[0]['id'],expected,query)
        self.assertFalse(browse('set up an unrelated printer'))
    def test_return_visit_uses_only_saved_evidence(self):
        def snapshot(ws,day,row):
            p=dict(actor_id='sampleactor',slug='khadinakbar/keyword-rank-tracker',input={'keyword':'pizza'},observation=day, options={'build':'1.0.0'})
            key=digest(p);atomic_json(ws/key/'plan.json',p);atomic_json(ws/key/'result.json',dict(status='SUCCEEDED',items=[row],additional_rows=False));return key
        with tempfile.TemporaryDirectory() as d:
            ws=Path(d);a=snapshot(ws,'2026-11-01',{'rank':4});b=snapshot(ws,'2026-11-02',{'rank':3})
            brief=notebook.save(ws,'keyword-rank-tracker','rank pizza','table','compare next month',a)
            self.assertTrue(notebook.reopen(ws,brief['id'])['cached_result'])
            self.assertEqual(notebook.report(ws,a)['returned_fields'],['rank'])
            self.assertEqual(notebook.compare(ws,a,b)['distinct_row_values_only_in_second'],1)
            with self.assertRaises(ValueError):notebook.compare(ws,a,a)
