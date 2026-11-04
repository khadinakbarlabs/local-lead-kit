import json
from pathlib import Path
import unittest

from looksy.tasks import library
from looksy.workflows import areas, compose, recipes


class WorkflowTests(unittest.TestCase):
    def test_every_actor_and_operation_has_explicit_area(self):
        catalog = json.loads((Path(__file__).parents[1] / 'looksy/catalog.json').read_text())
        cards = library()
        found = areas()
        self.assertGreaterEqual(len(found), 32)
        self.assertEqual(len({row['id'] for row in found}), len(found))
        task_ids = set().union(*(set(row['task_ids']) for row in found))
        self.assertEqual(task_ids, set(cards))
        self.assertEqual({cards[key]['actor'] for key in task_ids},
                         {row['slug'] for row in catalog['actors']})
        for row in found:
            self.assertEqual(row['count'], len(row['task_ids']))
            self.assertTrue(row['description'])
            self.assertGreater(row['count'], 0)
        # Multi-label membership is intentional, including video/social/creator research.
        self.assertGreater(sum(row['count'] for row in found), len(cards))

    def test_every_area_has_actionable_exact_task_recipes(self):
        rows = recipes()
        self.assertGreaterEqual(len(rows), 32)
        self.assertEqual({r['area'] for r in rows}, {a['id'] for a in areas()})
        self.assertEqual(len({r['id'] for r in rows}), len(rows))
        cards = library()
        for recipe in rows:
            self.assertTrue(recipe['goal'])
            self.assertTrue(recipe['intake'])
            self.assertTrue(recipe['artifact']['contents'])
            self.assertTrue(recipe['quality_rules'])
            self.assertTrue(recipe['access_constraints'])
            preceding = set()
            for step in recipe['steps']:
                self.assertIn(step['task_id'], cards)
                self.assertTrue(set(step['depends_on']).issubset(preceding))
                self.assertTrue(step['handoff'])
                preceding.add(step['id'])

    def test_representative_goals_retrieve_relevant_recipe(self):
        cases = [
            ('Find roofers in Austin', 'local-lead-map'),
            ('Compare competitor prices for Amazon products', 'price-comparison'),
            ('Research keywords and search volume for a bakery', 'keyword-plan'),
            ('Audit backlinks and referring domains', 'backlink-audit'),
            ('Check SERP rank positions', 'serp-baseline'),
            ('Measure AI visibility and citations', 'ai-citation-brief'),
            ('AI content detection for my article', 'detector-review'),
            ('Humanize this copy', 'humanize-copy'),
            ('Plan a newsletter and editorial calendar', 'newsletter-plan'),
            ('Compare Meta ad creatives', 'meta-ads'),
            ('Research TikTok ads', 'tiktok-ads'),
            ('Research LinkedIn ads', 'linkedin-ads'),
            ('Research Pinterest ads', 'pinterest-ads'),
            ('Research B2B accounts with Apollo', 'b2b-account-list'),
            ('Find startups on Product Hunt', 'startup-launches'),
            ('Analyze public Facebook comments', 'facebook-social'),
            ('Analyze Instagram comments', 'instagram-social'),
            ('Instagram reels analysis', 'instagram-social'),
            ('Analyze Telegram discussion themes', 'telegram-discussions'),
            ('Analyze Reddit audience pain points', 'reddit-social'),
            ('Analyze authorized Discord conversations', 'discord-conversations'),
            ('Analyze YouTube video transcripts and comments', 'youtube-analysis'),
            ('Extract OCR text from an image', 'ocr-evidence'),
            ('Compare forex and financial events', 'finance-events'),
            ('Research crypto markets', 'crypto-market'),
            ('Calculate maps directions and driving distance', 'route-planning'),
            ('Compare hotels and accommodation', 'hotel-comparison'),
            ('Find housing listings on Zillow', 'property-comparison'),
            ('Compare eBay listings', 'ebay-comparison'),
            ('Research government public databases', 'public-records'),
        ]
        for goal, expected in cases:
            with self.subTest(goal=goal):
                self.assertIn(expected, [r['id'] for r in compose(goal)['candidates']])

    def test_goal_is_preserved_and_execution_is_only_a_plan(self):
        goal = 'Find 25 roofing companies in Austin in November; export a CSV; max $4.'
        result = compose(goal, area='local_business', limit=1)
        self.assertEqual(result['goal'], goal)
        self.assertEqual(result['execution'], 'planning_only')
        self.assertEqual(result['candidates'][0]['id'], 'local-lead-map')
        self.assertIn('bounded approval', result['instruction'])
        self.assertIn('live schemas', result['instruction'])
        self.assertIn('reopen', result['instruction'])
        self.assertIn('unverified', result['capability_evidence'])

    def test_unsupported_access_and_named_alternatives_are_not_assumed(self):
        lusha = compose('Use Lusha to find contacts')
        self.assertTrue(any('Direct Lusha service access is unverified' in x for x in lusha['unknowns']))
        private = compose('Analyze private Discord messages')
        self.assertTrue(any('user authorization' in x for x in private['unknowns']))
        forex = compose('Build a forex economic calendar')
        self.assertTrue(any('must be checked' in x for x in forex['unknowns']))
        self.assertFalse(compose('unrelated printer setup')['candidates'])

    def test_explicit_subjects_exclude_generic_unrelated_recipes(self):
        self.assertEqual([r['id'] for r in compose('forex market lookup')['candidates']], ['finance-events'])
        self.assertNotIn('discord-conversations', [r['id'] for r in compose('YouTube analysis')['candidates']])

    def test_inputs_and_returned_templates_are_isolated(self):
        with self.assertRaises(ValueError): compose('')
        with self.assertRaises(ValueError): compose('research', area='imaginary')
        for invalid in (0, 11, True, '3'):
            with self.assertRaises(ValueError): compose('research', limit=invalid)
        result = compose('backlinks')
        result['candidates'][0]['steps'][0]['task_id'] = 'not-real'
        self.assertNotEqual(compose('backlinks')['candidates'][0]['steps'][0]['task_id'], 'not-real')
