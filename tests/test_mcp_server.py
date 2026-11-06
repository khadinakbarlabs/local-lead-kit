import io
import json
import copy
import unittest
import tempfile
from pathlib import Path
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
        run = {'status': 'SUCCEEDED', 'usageTotalUsd': 0.07, 'chargedEventCounts': {'place-scraped': 10},
               'eventUsage': {'place-scraped': {'eventTotalUsd': 0.04}},
               'usageUsd': {'ACTOR_COMPUTE_UNITS': 0.03},
               'pricingInfo': {'isPPEPlatformUsagePaidByUser': True,
                               'pricingPerEvent': {'actorChargeEvents': {'place-scraped': {'eventPriceUsd': 0.004}}}}}
        cost = m._cost(run)
        self.assertAlmostEqual(cost['event_charges_usd'], 0.04)
        self.assertAlmostEqual(cost['total_usd'], 0.07)
        run.pop('usageUsd')
        run['pricingInfo']['isPPEPlatformUsagePaidByUser'] = False
        self.assertEqual(m._cost(run)['platform_usage_usd'], 0)
        self.assertTrue(cost['provisional'])

    def test_run_flow_with_fake_client(self):
        row = m.CATALOG['khadinakbar/google-maps-leads-scraper']
        fake = mock.Mock()
        fake.metadata.return_value = {'id': row['id'], 'build_id': 'build12345', 'build_number': '1.8.7',
                                      'permission_level': 'LIMITED_PERMISSIONS',
                                      'pricing': {'model': 'PAY_PER_EVENT', 'events': {'result': {'price_usd': 0.01}}},
                                      'schema': {'type': 'object', 'properties': {'searchQuery': {'type': 'string'}}}}
        fake.data.return_value = {'id': 'account12345', 'plan': {'id': 'STARTER'}}
        fake.start.return_value = {'id': 'run12345', 'status': 'SUCCEEDED', 'defaultDatasetId': 'ds123456'}
        fake.identity.side_effect = lambda v: v
        fake.request.return_value = [{'business_name': 'A'}]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(m, 'workspace', return_value=Path(tmp)), mock.patch.object(m, '_client', return_value=fake):
            preview = m.run_tool('google-maps-leads-scraper', {'searchQuery': 'roofers'}, 0.5, wait_seconds=0)
            fake.start.assert_not_called()
            self.assertEqual(preview['state'], 'PREVIEW')
            view = m.run_tool('google-maps-leads-scraper', {'searchQuery': 'roofers'}, 0.5, wait_seconds=0, approval=preview['approval'])
            fake.get_run.return_value = fake.start.return_value
            repeated = m.run_tool('google-maps-leads-scraper', {'searchQuery': 'roofers'}, 0.5, wait_seconds=0, approval=preview['approval'])
            self.assertEqual(repeated['run_id'], view['run_id'])
            self.assertEqual(fake.start.call_count, 1)
        options = fake.start.call_args[0][2]
        self.assertEqual(options['maxTotalChargeUsd'], 0.5)
        self.assertEqual(options['build'], '1.8.7')
        self.assertEqual(view['rows'], [{'business_name': 'A'}])
        with mock.patch.object(m, '_client', return_value=fake), self.assertRaises(ValueError):
            m.run_tool('google-maps-leads-scraper', {'unknownField': 1}, 0.5, wait_seconds=0)


class Connect(unittest.TestCase):
    def test_connector_url_selects_curated_tools_and_disables_telemetry(self):
        for pack in m.PACKS:
            url = m.connector_url(pack)
            self.assertTrue(url.startswith('https://mcp.apify.com/?tools='))
            self.assertIn('&telemetry-enabled=false', url)
            tools = url.split('?tools=')[1].split('&')[0].split(',')
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
        self.assertEqual(codex[-1], 'codex mcp login looksy-apify')
        self.assertEqual(web['sign_in']['agent_can_run'], [])
        self.assertIn(m.connector_url('all'), web['message_for_user'])

    def test_key_present(self):
        with mock.patch.object(m, '_key_source', return_value='environment'):
            status = m.connect()
        self.assertFalse(status['connected'])
        self.assertTrue(status['configured'])
        self.assertFalse(status['verified'])


class ApprovalSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fake = mock.Mock()
        self.slug = 'khadinakbar/google-maps-leads-scraper'
        self.fake.metadata.return_value = {
            'id': m.CATALOG[self.slug]['id'], 'build_id': 'build12345', 'build_number': '1.8.7',
            'permission_level': 'LIMITED_PERMISSIONS',
            'schema': {'type': 'object', 'properties': {'query': {'type': 'string'}}},
            'pricing': {'model': 'PAY_PER_EVENT', 'minimalMaxTotalChargeUsd': 0.01,
                        'isPPEPlatformUsagePaidByUser': True,
                        'events': {'result': {'price_usd': 0.01}}}}
        self.fake.data.return_value = {'id': 'account12345', 'plan': {'id': 'STARTER'}}
        self.fake.start.return_value = {'id': 'run12345', 'status': 'SUCCEEDED',
                                       'defaultDatasetId': 'dataset12345',
                                       'actId': m.CATALOG[self.slug]['id']}
        self.fake.get_run.return_value = self.fake.start.return_value
        self.fake.request.return_value = [{'result': 'A'}]
        self.fake.identity.side_effect = lambda value: value
        self.fake.record.return_value = None
        self.args = {'tool': self.slug, 'input': {'query': 'roofers'}, 'max_charge_usd': 0.5, 'wait_seconds': 0}
        for patcher in (mock.patch.object(m, '_client', return_value=self.fake),
                        mock.patch.object(m, 'workspace', return_value=Path(self.tmp.name))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_changed_paid_arguments_require_new_approval(self):
        preview = m.run_tool(**self.args)
        for changes in ({'input': {'query': 'dentists'}}, {'max_charge_usd': 0.6},
                        {'memory_mb': 2048}, {'timeout_seconds': 301}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                m.run_tool(**{**self.args, **changes}, approval=preview['approval'])
        self.fake.start.assert_not_called()
        self.assertEqual(preview['request']['input'], self.args['input'])
        self.assertEqual(preview['options']['timeout'], 300)
        self.assertEqual(preview['options']['memory'], 1024)

    def test_account_and_live_metadata_changes_invalidate_approval(self):
        preview = m.run_tool(**self.args)
        original = copy.deepcopy(self.fake.metadata.return_value)
        for changes in ({'build_id': 'newbuild12345'}, {'permission_level': 'FULL_PERMISSIONS'},
                        {'pricing': {**original['pricing'], 'isPPEPlatformUsagePaidByUser': False}}):
            self.fake.metadata.return_value = {**original, **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                m.run_tool(**self.args, approval=preview['approval'])
        self.fake.metadata.return_value = original
        for account in ({'id': 'another12345'}, {'id': 'account12345', 'plan': {'id': 'SCALE'}}):
            self.fake.data.return_value = account
            with self.assertRaises(ValueError):
                m.run_tool(**self.args, approval=preview['approval'])
        self.fake.start.assert_not_called()

    def test_ambiguous_start_is_durable_and_never_replayed(self):
        preview = m.run_tool(**self.args)
        self.fake.start.side_effect = m.ApiError('secret upstream payload')
        for _ in range(2):
            with self.assertRaises(m.NeedsAttention):
                m.run_tool(**self.args, approval=preview['approval'])
        self.assertEqual(self.fake.start.call_count, 1)
        ledger = next(Path(self.tmp.name).rglob('ledger.json'))
        self.assertEqual(json.loads(ledger.read_text())['entries']['actor']['state'], 'UNKNOWN')

    def test_read_failure_preserves_known_run_and_retry_does_not_restart(self):
        preview = m.run_tool(**self.args)
        self.fake.start.return_value['status'] = 'RUNNING'
        self.fake.get_run.side_effect = m.ApiError('https://host/?token=secret')
        with mock.patch.object(m.time, 'sleep'):
            result = m.run_tool(**{**self.args, 'wait_seconds': 1}, approval=preview['approval'])
        self.assertEqual(result['run_id'], 'run12345')
        self.assertTrue(result['observation_incomplete'])
        repeated = m.run_tool(**self.args, approval=preview['approval'])
        self.assertEqual(repeated['run_id'], 'run12345')
        self.assertEqual(self.fake.start.call_count, 1)
        self.assertNotIn('secret', json.dumps(result))

    def test_rows_failure_preserves_run(self):
        preview = m.run_tool(**self.args)
        self.fake.request.side_effect = OSError('secret response body')
        result = m.run_tool(**self.args, approval=preview['approval'])
        self.assertEqual(result['run_id'], 'run12345')
        self.assertTrue(result['observation_incomplete'])
        self.assertIn('get_run', result['next'])
        self.assertNotIn('secret', json.dumps(result))

    def test_empty_success_reads_evidence_without_inventing_cause(self):
        self.fake.request.return_value = []
        self.fake.start.return_value['defaultKeyValueStoreId'] = 'store12345'
        self.fake.record.side_effect = [{'error': 'upstream failed'}, {'rows': 0}]
        preview = m.run_tool(**self.args)
        result = m.run_tool(**self.args, approval=preview['approval'])
        self.assertIn('cause is unknown', result['note'])
        self.assertEqual(result['output'], {'error': 'upstream failed'})
        self.assertEqual(result['run_summary'], {'rows': 0})
        self.assertEqual(self.fake.record.call_args_list,
                         [mock.call('store12345', 'OUTPUT'), mock.call('store12345', 'RUN_SUMMARY')])

    def test_invalid_options_fail_before_any_account_read_or_start(self):
        for changes in ({'wait_seconds': '1'}, {'wait_seconds': True}, {'wait_seconds': -1},
                        {'memory_mb': 129}, {'memory_mb': 0}, {'memory_mb': False},
                        {'timeout_seconds': 0}, {'timeout_seconds': 3601},
                        {'input': {'query': float('nan')}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                m.run_tool(**{**self.args, **changes})
        self.fake.data.assert_not_called()
        self.fake.start.assert_not_called()

    def test_all_terminal_states_preserve_records_and_partial_rows(self):
        run = {**self.fake.start.return_value, 'defaultKeyValueStoreId': 'store12345'}
        for status in m.TERMINAL:
            with self.subTest(status=status):
                self.fake.record.side_effect = [{'partial': True}, {'coverage': 'incomplete'}]
                result = m._run_view(self.fake, {**run, 'status': status})
                self.assertEqual(result['rows'], [{'result': 'A'}])
                self.assertEqual(result['output'], {'partial': True})
                self.assertEqual(result['run_summary'], {'coverage': 'incomplete'})
                self.assertEqual(result['run_id'], 'run12345')
        self.fake.record.side_effect = [m.ApiError('SECRET'), {'coverage': 'partial'}]
        result = m._run_view(self.fake, run)
        self.assertTrue(result['observation_incomplete'])
        self.assertIsNone(result['output'])
        self.assertEqual(result['run_summary'], {'coverage': 'partial'})
        self.assertEqual(result['rows'], [{'result': 'A'}])
        self.assertNotIn('SECRET', json.dumps(result))

    def test_get_run_malformed_billing_retains_known_run_id(self):
        self.fake.get_run.return_value = {**self.fake.start.return_value,
                                          'chargedEventCounts': ['result'], 'eventUsage': {'result': {'eventTotalUsd': 1}}}
        result = m.get_run('run12345')
        self.assertEqual(result['run_id'], 'run12345')
        self.assertTrue(result['observation_incomplete'])
        self.assertIn('get_run', result['next'])
        self.fake.start.assert_not_called()

    def test_tiered_preview_discloses_prices_but_blocks_start(self):
        self.fake.metadata.return_value['pricing']['requires_tier_review'] = True
        preview = m.run_tool(**self.args)
        self.assertTrue(preview['pricing']['requires_tier_review'])
        with self.assertRaises(ValueError):
            m.run_tool(**self.args, approval=preview['approval'])
        self.fake.start.assert_not_called()

    def test_minimum_cap_enforced_before_start(self):
        self.fake.metadata.return_value['pricing']['minimalMaxTotalChargeUsd'] = 1.0
        with self.assertRaises(ValueError):
            m.run_tool(**self.args)
        self.fake.start.assert_not_called()

    def test_get_tool_uses_exact_public_metadata_and_snapshot_date(self):
        with mock.patch.object(m, 'ApifyClient', return_value=self.fake) as factory:
            result = m.get_tool(self.slug)
        factory.assert_called_once_with(public_metadata_only=True)
        self.fake.metadata.assert_called_once_with(self.slug)
        self.fake.request.assert_not_called()
        self.assertEqual(result['build_id'], 'build12345')
        self.assertEqual(result['input_schema'], self.fake.metadata.return_value['schema'])
        self.assertEqual(result['evidence']['snapshot_date'], m._CATALOG_DOC['updated'])

    def test_explicit_collection_label_allows_a_separately_approved_new_run(self):
        first = m.run_tool(**self.args)
        m.run_tool(**self.args, approval=first['approval'])
        repeated = m.run_tool(**self.args)
        self.assertEqual(repeated['approval'], first['approval'])
        fresh = m.run_tool(**self.args, request_id='requested-refresh-2')
        self.assertNotEqual(fresh['approval'], first['approval'])
        self.assertEqual(self.fake.start.call_count, 1)
        with self.assertRaises(ValueError):
            m.run_tool(**self.args, request_id='requested-refresh-2', approval=first['approval'])
        m.run_tool(**self.args, request_id='requested-refresh-2', approval=fresh['approval'])
        self.assertEqual(self.fake.start.call_count, 2)
        m.run_tool(**self.args, request_id='requested-refresh-2', approval=fresh['approval'])
        self.assertEqual(self.fake.start.call_count, 2)


class BillingAndProtocolSafety(unittest.TestCase):
    def test_authoritative_discounted_events_and_total_are_not_recomputed(self):
        run = {'status': 'SUCCEEDED', 'usageTotalUsd': 0.06, 'usageUsd': {'COMPUTE': 0.02},
               'chargedEventCounts': {'result': 10}, 'eventUsage': {'result': {'eventTotalUsd': 0.04}},
               'pricingInfo': {'pricingPerEvent': {'actorChargeEvents': {'result': {'eventPriceUsd': 0.1}}}}}
        cost = m._cost(run)
        self.assertEqual(cost['event_charges_usd'], 0.04)
        self.assertEqual(cost['platform_usage_usd'], 0.02)
        self.assertEqual(cost['total_usd'], 0.06)
        self.assertTrue(cost['provisional'])

    def test_unknown_tiers_and_missing_payer_do_not_become_zero(self):
        run = {'status': 'SUCCEEDED', 'chargedEventCounts': {'result': 5},
               'pricingInfo': {'pricingPerEvent': {'actorChargeEvents': {'result': {
                   'eventPriceUsd': 0.1, 'eventTieredPricingUsd': {'FREE': {'tieredEventPriceUsd': 0.2}}}}}}}
        cost = m._cost(run)
        for key in ('event_charges_usd', 'platform_usage_usd', 'total_usd'):
            self.assertIsNone(cost[key])
        self.assertIsNone(m._cost({'eventUsage': {'result': {'eventTotalUsd': 1}}})['total_usd'])

    def test_malicious_exception_payloads_are_not_echoed(self):
        for error in (m.ApiError, ValueError, TypeError, OSError, RuntimeError):
            original = m.TOOLS['account']
            with mock.patch.dict(m.TOOLS, account=(mock.Mock(side_effect=error('https://bad/?token=SECRET <body>')),
                                                  *original[1:])):
                reply, ping = rpc({'id': 1, 'method': 'tools/call', 'params': {'name': 'account'}},
                                  {'id': 2, 'method': 'ping'})
            self.assertTrue(reply['result']['isError'])
            self.assertNotIn('SECRET', json.dumps(reply))
            self.assertNotIn('https://bad', json.dumps(reply))
            self.assertEqual(ping['result'], {})

    def test_invalid_argument_types_never_invoke_tool(self):
        original = m.TOOLS['run_tool']
        fake = mock.Mock()
        cases = ([], None, {'tool': 'x', 'input': {}, 'max_charge_usd': True},
                 {'tool': 'x', 'input': [], 'max_charge_usd': 1},
                 {'tool': 'x', 'input': {}, 'max_charge_usd': 1, 'wait_seconds': '2'},
                 {'tool': 'x', 'input': {}, 'max_charge_usd': 1, 'extra': 'value'})
        with mock.patch.dict(m.TOOLS, run_tool=(fake, *original[1:])):
            for args in cases:
                (reply,) = rpc({'id': 1, 'method': 'tools/call', 'params': {'name': 'run_tool', 'arguments': args}})
                self.assertTrue(reply['result']['isError'])
        fake.assert_not_called()

    def test_malformed_protocol_messages_do_not_stop_server(self):
        replies = rpc({'id': 1, 'method': 'initialize', 'params': []},
                      {'id': 2, 'method': 'tools/call', 'params': {'name': []}},
                      {'id': 3, 'method': []}, {'id': 4, 'method': 'ping'})
        self.assertTrue(all('error' in reply for reply in replies[:-1]))
        self.assertEqual(replies[-1]['result'], {})


class PublishedDocs(unittest.TestCase):
    def test_docs_match_generated_connector_urls(self):
        from pathlib import Path
        docs = Path(m.__file__).parents[1] / 'docs'
        self.assertIn(m.connector_url('all'), (docs / 'llms.txt').read_text())
        connect = (docs / 'connect.md').read_text()
        for pack in m.PACKS:
            self.assertIn(m.connector_url(pack), connect)
