"""Exercise onboarding on loopback with temporary settings and a simulated account."""
from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from looksy import notebook
from looksy.server import make_server
from looksy.service import CampaignService
from looksy.settings import Connections


def verify_fixture(key):
    if key != 'offline-test-token':
        raise ValueError('Verification failed.')
    return 'offline-account'


def check(width, screenshot=None):
    from playwright.sync_api import sync_playwright, expect
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        workspace = root / 'workspace'
        connections = Connections(root/'settings', verifier=verify_fixture)
        service = CampaignService(workspace)
        notebook.save(workspace/'toolbox', 'google-maps-leads-scraper', 'Bookstore shortlist', 'CSV', 'Inspect sources')
        server = make_server(service, 0, connections=connections)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as w:
                browser = w.chromium.launch(channel='chrome')
                page = browser.new_page(viewport={'width':width, 'height':850}, reduced_motion='reduce')
                origin = f'http://127.0.0.1:{server.server_port}'
                errors, outside = [], []
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('request',lambda request:outside.append(request.url) if not request.url.startswith(origin+'/') else None)
                page.goto(origin+'/connect?ticket='+server.ticket)
                expect(page.locator('#setup-title')).to_have_text('Connect your Apify account')
                if screenshot:
                    page.screenshot(path=screenshot)
                page.locator('#apify-key').fill('invalid')
                page.locator('#verify').click()
                expect(page.locator('#apify-error')).to_be_visible()
                page.locator('#apify-key').fill('offline-test-token')
                page.locator('#verify').click()
                expect(page.locator('#skip-ai')).to_be_visible()
                page.locator('#skip-ai').click()
                expect(page.locator('#home-title')).to_be_visible()
                page.locator('#nav a[href="#history"]').click()
                expect(page.locator('#brief-list')).to_contain_text('Bookstore shortlist')
                page.locator('#nav a[href="#settings"]').click()
                page.locator('#edit-ai').click()
                page.locator('#provider').select_option('openrouter')
                page.locator('#ai-key').fill('offline-provider-test')
                page.locator('#save-ai').click()
                page.locator('#nav a[href="#settings"]').click()
                expect(page.locator('#ai-state')).to_contain_text('OpenRouter')
                page.locator('#remove-ai').click()
                expect(page.locator('#ai-state')).to_contain_text('current assistant')
                page.reload()
                expect(page.locator('#settings-title')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth') <= width
                assert not outside and not errors,(outside,errors)
                assert 'offline-provider-test' not in connections.path.read_text()
                assert page.evaluate('localStorage.length + sessionStorage.length') == 0
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    for size in [320,390,1280]:
        check(size)
    print('PASS private dashboard: required verification, optional provider/skip, settings, history, reload and responsive layouts.')
