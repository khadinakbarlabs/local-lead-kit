import os
from pathlib import Path
import tempfile
import unittest

from looksy.settings import Connections, env_key


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI credential store')
class WindowsSettingsTests(unittest.TestCase):
    def test_encrypted_roundtrip_and_removal(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Connections(Path(folder),verifier=lambda key:'fixture-user')
            store.save_apify('apify-fixture-key')
            store.save_ai({'provider':'openai','key':'ai-fixture-key'})
            disk=store.path.read_text()
            self.assertNotIn('apify-fixture-key',disk)
            self.assertNotIn('ai-fixture-key',disk)
            self.assertIn('dpapi',disk)
            reopened=Connections(Path(folder))
            self.assertTrue(reopened.status()['onboarded'])
            self.assertEqual(reopened.provider_key('openai'),'ai-fixture-key')
            reopened.save_ai({'skip':True})
            self.assertIsNone(reopened.status()['ai_provider'])

    def test_windows_prefers_encrypted_settings_or_environment(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            legacy=Path(folder)/'apify.env'
            legacy.write_text('APIFY_TOKEN=legacy-plaintext')
            self.assertIsNone(Connections(Path(folder)).token())
            with self.assertRaisesRegex(ValueError,'On Windows'):
                env_key(legacy)
            with patch.dict(os.environ,{'APIFY_TOKEN':'environment-fixture'}):
                self.assertEqual(Connections.from_environment().token(),'environment-fixture')
