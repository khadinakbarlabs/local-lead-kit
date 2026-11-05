import io
import json
import unittest
from unittest import mock

from looksy import mcp_server as m


def rpc(*messages):
    out = io.StringIO()
    m.serve(io.StringIO(''.join(json.dumps(x) + '\n' for x in messages)), out)
    return [json.loads(line) for line in out.getvalue().splitlines()]


class McpProtocol(unittest.TestCase):
    def test_initialize_and_list(self):
        init, listed = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-03-26'}},
                           {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                           {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        self.assertEqual(init['result']['protocolVersion'], '2025-03-26')
        self.assertEqual(init['result']['serverInfo']['name'], 'looksy')
        names = [t['name'] for t in listed['result']['tools']]
        self.assertEqual(names, ['find_tools', 'list_jobs', 'get_tool', 'run_tool', 'get_run', 'connect', 'account'])
        run_tool = next(t for t in listed['result']['tools'] if t['name'] == 'run_tool')
        self.assertIn('max_charge_usd', run_tool['inputSchema']['required'])
        self.assertFalse(run_tool['annotations']['readOnlyHint'])

    def test_unknown_method_and_bad_json(self):
        out = io.StringIO()
        m.serve(io.StringIO('not json\n' + json.dumps({'jsonrpc': '2.0', 'id': 3, 'method': 'nope'}) + '\n'), out)
        first, second = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(first['error']['code'], -32700)
        self.assertEqual(second['error']['code'], -32601)

    def test_tool_errors_are_reported_not_raised(self):
        (reply,) = rpc({'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                        'params': {'name': 'get_tool', 'arguments': {'tool': 'someone/else'}}})
        self.assertTrue(reply['result']['isError'])


class JobsAndRouting(unittest.TestCase):
    def test_every_job_tool_is_in_catalog(self):
        ids = {j['id'] for j in m.JOBS}
        for job in m.JOBS:
            for slug in job['tools']:
                self.assertIn(slug, m.CATALOG, f"{job['id']} -> {slug}")
            for nxt in job.get('next', []):
                self.assertIn(nxt, ids)

    def test_routing_examples(self):
        cases = {
            'google maps leads for roofers in Austin': 'khadinakbar/google-maps-leads-scraper',
            'which AI answers mention my brand': 'khadinakbar/ai-search-visibility-tracker',
            'keyword search volume': 'khadinakbar/dataforseo-keyword-research',
            'verify email list': 'khadinakbar/email-address-validator',
            'competitor facebook ads': 'khadinakbar/facebook-ads-library-scraper',
        }
        for job, best in cases.items():
            self.assertEqual(m.find_tools(job)['tools'][0]['tool'], best, job)

    def test_cards_carry_evidence(self):
        card = m.find_tools('google maps leads')['tools'][0]
        self.assertIn('success_rate_30d', card['evidence'])
        self.assertIn('price_usd', card['evidence'])

    def test_empty_job_rejected(self):
        with self.assertRaises(ValueError):
            m.find_tools('the a of')

    def test_small_samples_do_not_outrank_proven_tools(self):
        proven = {'evidence': {'success_rate_30d': 0.97, 'runs_30d': 1000}}
        lucky = {'evidence': {'success_rate_30d': 1.0, 'runs_30d': 1}}
        self.assertGreater(m._reliability(proven), m._reliability(lucky))


class RunTool(unittest.TestCase):
    def test_cap_bounds(self):
        for cap in (0, 0.001, 501, 'abc', float('nan')):
            with self.assertRaises(ValueError):
                m.run_tool('google-maps-leads-scraper', {}, cap)

    def test_outside_catalog_rejected(self):
        with self.assertRaises(ValueError):
            m.run_tool('apify/website-content-crawler', {}, 1)

    def test_cost_breakdown(self):
        run = {'status': 'SUCCEEDED', 'usageTotalUsd': 0.03, 'chargedEventCounts': {'place-scraped': 10},
               'pricingInfo': {'isPPEPlatformUsagePaidByUser': True,
                               'pricingPerEvent': {'actorChargeEvents': {'place-scraped': {'eventPriceUsd': 0.004}}}}}
        cost = m._cost(run)
        self.assertAlmostEqual(cost['event_charges_usd'], 0.04)
        self.assertAlmostEqual(cost['total_usd'], 0.07)
        run['pricingInfo']['isPPEPlatformUsagePaidByUser'] = False
        self.assertEqual(m._cost(run)['platform_usage_usd'], 0)

    def test_run_flow_with_fake_client(self):
        row = m.CATALOG['khadinakbar/google-maps-leads-scraper']
        fake = mock.Mock()
        fake.metadata.return_value = {'id': row['id'], 'build_number': '1.8.7',
                                      'schema': {'type': 'object', 'properties': {'searchQuery': {'type': 'string'}}}}
        fake.start.return_value = {'id': 'run12345', 'status': 'SUCCEEDED', 'defaultDatasetId': 'ds123456'}
        fake.identity.side_effect = lambda v: v
        fake.request.return_value = [{'business_name': 'A'}]
        with mock.patch.object(m, '_client', return_value=fake):
            view = m.run_tool('google-maps-leads-scraper', {'searchQuery': 'roofers'}, 0.5, wait_seconds=0)
        options = fake.start.call_args[0][2]
        self.assertEqual(options['maxTotalChargeUsd'], 0.5)
        self.assertEqual(options['build'], '1.8.7')
        self.assertEqual(view['rows'], [{'business_name': 'A'}])
        with mock.patch.object(m, '_client', return_value=fake), self.assertRaises(ValueError):
            m.run_tool('google-maps-leads-scraper', {'unknownField': 1}, 0.5, wait_seconds=0)


class Connect(unittest.TestCase):
    def test_connector_url_exposes_only_looksy_tools(self):
        for pack in m.PACKS:
            url = m.connector_url(pack)
            self.assertTrue(url.startswith('https://mcp.apify.com/?tools='))
            tools = url.split('?tools=')[1].split(',')
            self.assertNotIn('search-actors', tools)
            actors = [t for t in tools if '/' in t]
            self.assertTrue(actors and all(t in m.CATALOG for t in actors), pack)
            self.assertLess(len(url), 4000)

    def test_unknown_pack(self):
        with self.assertRaises(ValueError):
            m.connector_url('nope')

    def test_no_key_recommends_sign_in_before_api_key(self):
        with mock.patch.object(m, '_key_source', return_value=None), mock.patch.object(m, 'load_token'):
            with self.assertRaises(ValueError) as caught:
                m._client()
            self.assertIn('sign in with Apify', str(caught.exception))
            for client in m.CLIENTS:
                status = m.connect(client, 'leads')
                self.assertFalse(status['connected'])
                self.assertEqual(status['recommended'], 'sign_in_with_apify')
                msg = status['message_for_user']
                self.assertLess(msg.index('sign in with Apify'), msg.index('API key instead'), client)
                self.assertIn('never in this chat', msg)

    def test_cli_clients_get_runnable_commands(self):
        with mock.patch.object(m, '_key_source', return_value=None):
            code = m.connect('claude_code')['sign_in']['agent_can_run']
            codex = m.connect('codex')['sign_in']['agent_can_run']
            web = m.connect('claude_web')
        self.assertTrue(code[0].startswith('claude mcp add --transport http looksy'))
        self.assertEqual(codex[-1], 'codex mcp login looksy')
        self.assertEqual(web['sign_in']['agent_can_run'], [])
        self.assertIn(m.connector_url('all'), web['message_for_user'])

    def test_key_present(self):
        with mock.patch.object(m, '_key_source', return_value='environment'):
            status = m.connect()
        self.assertTrue(status['connected'])


class PublishedDocs(unittest.TestCase):
    def test_docs_match_generated_connector_urls(self):
        from pathlib import Path
        docs = Path(m.__file__).parents[1] / 'docs'
        self.assertIn(m.connector_url('all'), (docs / 'llms.txt').read_text())
        connect = (docs / 'connect.md').read_text()
        for pack in m.PACKS:
            self.assertIn(m.connector_url(pack), connect)
