"""Optional browser regressions. Requires Playwright and a local Chrome installation."""
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from looksy.server import make_server
from looksy.tasks import browse, route
from looksy.workflows import compose


def main():
    from playwright.sync_api import sync_playwright, expect
    queries = ['find 25 roofers in Austin', 'prove my client appears in AI answers',
               'turn my Apify CSV into a client report', 'local leads', 'keyword demand',
               'brand mentions', 'Find Instagram profiles of dentists', 'find dental practices in London, compare prices, export CSV', 'reopen my last report', 'GitHub issues', 'flight prices', 'forex market lookup', 'YouTube video analysis', 'Analyze Instagram comments', 'Analyze Telegram discussions',
               '999999', 'set up an unrelated printer', 'find local leads and export a CSV']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((ROOT / 'docs/index.html').as_uri())
        for name in ['SEO repair list', 'AI citation report', 'Prospect spreadsheet']:
            page.locator('#sample-next').click()
            expect(page.locator('#sample-title')).to_have_text(name)
        page.locator('#sample-use').click()
        expect(page.locator('#q')).to_have_value('Find 25 roofers in Austin')
        assert page.locator('#goal-step').is_visible()

        def enter_goal(query):
            if not page.locator('#goal-step').is_visible():
                page.locator('#guide-start-over').click()
            page.locator('#q').fill(query)
            page.locator('#guide-next').click()

        for query in queries:
            enter_goal(query)
            observed = page.locator('#list li').evaluate_all('(rows) => rows.map(row => row.dataset.taskId)')
            expected = [task['id'] for task in browse(query)][:6]
            assert observed == expected, (query, observed, expected)
            if route(query)['intent']=='new_collection' and query.strip():
                actual=page.locator('#recipes>li').evaluate_all('(rows) => rows.map(row => row.dataset.recipeId)')
                expected_recipes=[recipe['id'] for recipe in compose(query)['candidates']]
                assert actual==expected_recipes,(query,actual,expected_recipes)
            if route(query)['intent'] != 'new_collection':
                assert page.locator('#action').is_visible(), query
        page.locator('#guide-start-over').click()
        page.locator('[data-path=existing_data]').click()
        page.locator('#q').fill('Identify customer trends')
        page.locator('#guide-next').click()
        expect(page.locator('#action-title')).to_have_text('Analyze data I have')
        page.locator('#guide-start-over').click()
        page.locator('[data-path=saved_research]').click()
        page.locator('#q').fill('Client A')
        page.locator('#guide-next').click()
        expect(page.locator('#action-title')).to_have_text('Open recent research')
        page.locator('#guide-start-over').click()
        page.locator('[data-path=new_collection]').click()
        enter_goal('Analyze Discord discussion and plan content')
        page.locator('#area').select_option('communities')
        page.locator('#recipes summary').first.click()
        page.get_by_text('Use this workflow', exact=True).first.click()
        assert 'Analyze Discord discussion and plan content' in page.locator('#request').input_value()
        assert 'Workflow\n' in page.locator('#request').input_value()
        assert page.locator('#area option').count() == 37
        enter_goal('Find 25 roofers in Austin')
        page.locator('#area').select_option('')
        page.locator('#advanced>summary').click()
        page.locator('#list summary').first.click()
        page.locator('#list li').first.get_by_text('Use this task', exact=True).click()
        request = page.locator('#request')
        assert 'Find 25 roofers in Austin' in request.input_value()
        assert 'google-maps-leads-scraper' in request.input_value()
        request.fill(request.input_value() + '\nDeliver a CSV for Client A.')
        assert 'Client A' in request.input_value()
        for width in [320, 390, 1280]:
            page.set_viewport_size({'width': width, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth') <= width
        enter_goal('Find 25 roofers in Austin')
        page.locator('#advanced>summary').click()
        page.locator('#list summary').first.click()
        page.locator('#list li').first.get_by_text('Save template', exact=True).click()
        assert page.locator('#advanced').get_attribute('open') is not None
        page.reload()
        enter_goal('Find 25 roofers in Austin')
        page.locator('#advanced>summary').click()
        page.locator('#saved').click()
        assert page.locator('#list>li').count() == 1
        page.locator('#reset').click()
        expect(page.locator('#q')).to_have_value('Find 25 roofers in Austin')
        assert not errors, errors
        browser.close()
    print('PASS guide: routing parity, existing-data/recent actions, editable contextual handoff and mobile/desktop layout.')
    check_campaign()


def check_campaign():
    from playwright.sync_api import sync_playwright, expect
    saved = dict(niche='Dentists', locations=['London'], target=77, budget_usd=3,
                 include_contacts=False, analysis=True, offer='Website design')
    draft = dict(saved, niche='Roofers', locations=['Austin'], target=25,
                 offer='</script><script>window.draftInjected=true</script>')

    class Service:
        _client = None
        state = 'PLANNED'

        def list_jobs(self):
            return [{'id': 'saved', 'request': saved}]

        def load(self, ident):
            assert ident == 'saved'
            return dict(id='saved', status=self.state, request=saved,
                        results={'contacts': [{'email': 'public@example.test', 'business_name': 'Sample business'}, {'email': 'public@example.test'}, {'email': ''}]},
                        plan=dict(hash='fixture', maximum_runs=0, cost_note='Offline fixture', actors={}))

    server = make_server(Service(), port=0, draft=draft)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            page.goto(f'http://127.0.0.1:{server.server_port}/connect?ticket={server.ticket}')
            expect(page.locator('#niche')).to_have_value('Roofers')
            assert page.locator('#target').input_value() == '25'
            assert page.locator('#locations').input_value() == 'Austin'
            assert page.evaluate('window.draftInjected') is None
            assert page.locator('#offer').input_value() == draft['offer']
            assert not page.locator('#options-fields').is_visible()
            page.locator('#target-next').click()
            assert page.locator('#options-fields').is_visible()
            page.locator('#target-back').click()
            assert page.locator('#niche').input_value() == 'Roofers'
            page.locator('#saved-jobs').select_option('saved')
            page.locator('#edit-button').click()
            assert page.locator('#niche').input_value() == 'Dentists'
            assert page.locator('#locations').input_value() == 'London'
            assert page.locator('#target').input_value() == '77'
            assert not page.locator('[name=include_contacts]').is_checked()
            assert page.locator('[name=analysis]').is_checked()
            assert page.locator('#offer').input_value() == 'Website design'
            assert page.locator('#budget').input_value() == '3'
            page.locator('#target-next').click()
            page.locator('#target').fill('55')
            page.locator('#target-back').click()
            page.locator('#target-next').click()
            assert page.locator('#target').input_value() == '55'
            Service.state = 'COMPLETE'
            page.locator('#saved-jobs').select_option('')
            page.locator('#saved-jobs').select_option('saved')
            page.get_by_role('tab', name='Contacts', exact=True).click()
            page.locator('#export-destination').select_option('instantly')
            expect(page.locator('#export-status')).to_contain_text('1 of 3')
            with page.expect_download() as download:
                page.locator('#export-button').click()
            content = Path(download.value.path()).read_text()
            assert 'company_name' in content and 'Sample business' in content
            assert content.count('public@example.test') == 1
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    print('PASS Local Leads: validated draft preserved, script text inert, saved campaign edit restores all fields.')


if __name__ == '__main__':
    main()
