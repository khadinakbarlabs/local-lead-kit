import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from looksy.connection import load_token
from looksy.settings import Connections, RejectedKey


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = Connections(self.root, verifier=self.verify)

    @staticmethod
    def verify(key):
        if key == 'invalid':
            raise ValueError('Verification failed.')
        return 'account-a' if key != 'another-account' else 'account-b'

    def test_required_step_and_durable_skip(self):
        self.assertFalse(self.settings.status()['onboarded'])
        with self.assertRaises(ValueError):
            self.settings.save_ai({'skip':True})
        with self.assertRaises(ValueError):
            self.settings.save_apify('invalid')
        self.assertFalse(self.settings.status()['apify_configured'])
        self.assertFalse(self.settings.save_apify('valid-key')['onboarded'])
        self.assertTrue(self.settings.save_ai({'skip':True})['onboarded'])
        self.assertTrue(Connections(self.root).status()['onboarded'])
        self.assertEqual(self.settings.path.stat().st_mode & 0o777, 0o600)

    def test_rotation_and_provider_removal(self):
        self.settings.save_apify('valid-key')
        with self.assertRaisesRegex(ValueError,'Apify key'):
            self.settings.save_ai({'provider':'anthropic','key':'valid-key'})
        status=self.settings.save_ai({'provider':'anthropic','key':'provider-secret'})
        self.assertEqual(status['ai_provider'],'anthropic')
        self.assertNotIn('secret',str(status))
        self.assertEqual(self.settings.provider_key('anthropic'),'provider-secret')
        with self.assertRaises(ValueError):
            self.settings.provider_key('openai')
        before=self.settings.path.read_bytes()
        with self.assertRaises(ValueError):
            self.settings.save_apify('invalid')
        self.assertEqual(before,self.settings.path.read_bytes())
        self.settings.save_ai({'skip':True})
        self.assertNotIn('provider-secret',self.settings.path.read_text())
        self.settings.save_ai({'provider':'openai','key':'second-key'})
        status=self.settings.save_apify('another-account')
        self.assertFalse(status['onboarded'])
        self.assertIsNone(status['ai_provider'])

    def test_external_override_change_requires_new_validation(self):
        first=Connections(self.root,override='env-key',verifier=self.verify)
        first.save_apify()
        first.save_ai({'skip':True})
        self.assertNotIn('env-key',first.path.read_text())
        next_config=Connections(self.root,override='changed',verifier=self.verify)
        self.assertFalse(next_config.status()['apify_verified'])
        with self.assertRaisesRegex(ValueError,'environment'):
            next_config.save_apify('unrelated')

    def test_legacy_config_and_cli_share_new_key(self):
        legacy=self.root/'apify.env'
        legacy.write_text('APIFY_TOKEN=old-token\n')
        legacy.chmod(0o600)
        self.assertTrue(self.settings.status()['apify_configured'])
        self.assertFalse(self.settings.status()['apify_verified'])
        with patch('looksy.settings.Path.home',return_value=self.root), patch.dict(os.environ,{},clear=True):
            actual=Connections(verifier=self.verify)
            actual.save_apify('new-token')
            load_token()
            self.assertEqual(os.environ['APIFY_TOKEN'],'new-token')

    def test_rejected_current_key_locks_workspace_until_verified(self):
        self.settings.save_apify('valid-key')
        self.settings.save_ai({'skip':True})
        def rejected(key):
            raise RejectedKey('Key revoked.')
        self.settings.verifier = rejected
        with self.assertRaises(RejectedKey):
            self.settings.save_apify()
        self.assertFalse(self.settings.status()['apify_verified'])
        self.assertFalse(self.settings.status()['onboarded'])

    def test_insecure_file_is_rejected(self):
        self.settings.path.write_text('{}')
        self.settings.path.chmod(0o644)
        with self.assertRaises(ValueError):
            self.settings.status()


    def test_cli_only_sends_the_explicitly_selected_provider_prompt(self):
        from looksy import toolbox
        with patch('looksy.settings.Path.home',return_value=self.root), patch.dict(os.environ,{},clear=True):
            connections=Connections(verifier=self.verify)
            connections.save_apify('valid-key')
            connections.save_ai({'provider':'gemini','key':'fixture-provider'})
            prompt=self.root/'approved.txt'
            prompt.write_text('Summarize these approved observations.')
            argv=['looksy','ask-provider','--provider','gemini','--model','selected-model','--prompt-file',str(prompt),'--confirm-send']
            with patch('looksy.providers.ask',return_value='summary') as ask:
                with patch('sys.argv',argv+['openai']), self.assertRaises(ValueError):
                    toolbox.main()
                ask.assert_not_called()
                with patch('sys.argv',argv+['gemini']):
                    result=toolbox.main()
                self.assertEqual(result['text'],'summary')
                ask.assert_called_once_with('gemini','fixture-provider','selected-model',prompt.read_text())
