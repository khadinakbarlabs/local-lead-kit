import tempfile
import unittest
from pathlib import Path

from looksy import notebook
from looksy.tasks import browse, route


class UsabilityTests(unittest.TestCase):
    def test_natural_local_requests(self):
        for query in ['find 25 roofers in Austin', 'find 50 dentists in London', 'local leads']:
            self.assertEqual(browse(query)[0]['id'], 'google-maps-leads-scraper')

    def test_actions_are_not_actor_searches(self):
        for query, intent in [
            ('turn my Apify CSV into a client report', 'existing_data'),
            ('analyze my dataset', 'existing_data'),
            ('reopen my last report', 'saved_research'),
            ('open recent research', 'saved_research'),
        ]:
            answer = route(query)
            self.assertEqual(answer['intent'], intent)
            self.assertEqual(answer['tasks'], [])
            self.assertEqual(answer['request'], query)
            self.assertEqual(browse(query), [])

    def test_csv_output_does_not_override_collection(self):
        for query in ['find local leads and export a CSV', 'find dental practices in London, compare prices, export CSV']:
            self.assertEqual(route(query)['intent'], 'new_collection')

    def test_explicit_platform_is_preserved(self):
        self.assertIn('instagram', browse('Find Instagram profiles of dentists')[0]['id'])

    def test_mentions_and_citations_are_distinct(self):
        self.assertEqual(browse('prove my client appears in AI answers')[0]['id'], 'ai-search-visibility-tracker')
        self.assertEqual(browse('which sources AI answers cite')[0]['id'], 'ai-citations-tracker')

    def test_unknown_request_and_task_identity(self):
        self.assertEqual(browse('set up an unrelated printer'), [])
        self.assertEqual(browse('999999'), [])
        self.assertEqual(browse('keyword-rank-tracker')[0]['id'], 'keyword-rank-tracker')

    def test_latest_reopens_cached_brief_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            ws = Path(folder)
            with self.assertRaisesRegex(ValueError, 'saved research'):
                notebook.latest(ws)
            saved = notebook.save(ws, 'keyword-rank-tracker', 'Client A ranks', 'table', 'review')
            self.assertEqual(notebook.latest(ws)['id'], saved['id'])
