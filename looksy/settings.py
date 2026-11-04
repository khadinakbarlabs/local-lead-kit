"""Owner-only connection storage for the local dashboard and toolbox."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat

from .api import ApifyClient, ApiError, ApifyAccessDenied
from .core import atomic_json
from .private_config import config_lock, decode_record, encode_record

PROVIDERS = frozenset({'anthropic', 'openrouter', 'openai', 'gemini'})


def private_text(path, *, protected=False):
    """Read bounded, owner-only regular files without following a final symlink."""
    try:
        if os.name == 'nt' and os.lstat(path).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('Use a regular file for private settings.')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except FileNotFoundError:
        return None
    except OSError:
        raise ValueError('Cannot open the private settings file.') from None
    with os.fdopen(fd, encoding='utf-8') as handle:
        info = os.fstat(handle.fileno())
        encrypted = protected and os.name == 'nt'
        unsafe_permissions = not encrypted and (info.st_mode & 0o077 or (hasattr(os,'getuid') and info.st_uid != os.getuid()))
        if not stat.S_ISREG(info.st_mode) or unsafe_permissions or info.st_size > 65536:
            raise ValueError('Settings require a small regular file readable only by its owner.')
        return handle.read()


def env_key(path):
    if os.name == 'nt':
        raise ValueError('On Windows, enter your key in the private dashboard or set APIFY_TOKEN. Plaintext key files are not imported.')
    content = private_text(path)
    if content is None:
        return None
    for line in content.splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip() == 'APIFY_TOKEN':
            return valid_key(value.strip().strip('"\''))
    raise ValueError('The selected file does not contain an Apify key.')


def valid_key(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 4096 or not value.isascii()
            or any(char.isspace() or not char.isprintable() for char in value)):
        raise ValueError('Enter a valid API key without spaces.')
    return value


class RejectedKey(ValueError):
    """The service explicitly rejected this credential during verification."""


def verify_apify(key):
    try:
        account = ApifyClient(token=key).data('users/me')
    except ApifyAccessDenied:
        raise RejectedKey('Apify rejected this key or its account-read permission.') from None
    except (ApiError, OSError, ValueError):
        raise ValueError('Apify could not verify this key. Check the key, its account-read permission and your connection.') from None
    if not isinstance(account.get('id'), str) or not account['id']:
        raise ValueError('Apify returned no account identity. Check the key and try again.')
    return account['id']


class Connections:
    def __init__(self, directory=None, override=None, verifier=verify_apify):
        self.directory = Path(directory) if directory else Path.home() / '.config/looksy'
        self.override = override
        self.verifier = verifier
        self.path = self.directory / 'connections.json'

    @classmethod
    def from_environment(cls, path=None):
        override = env_key(path) if path is not None else os.environ.get('APIFY_TOKEN')
        if path is not None and not override:
            raise ValueError('The selected environment file does not exist.')
        return cls(override=override)

    def _read(self):
        content = private_text(self.path, protected=True)
        if content is None:
            return {}
        try:
            value = decode_record(json.loads(content))
        except ValueError:
            value = None
        if not isinstance(value, dict):
            raise ValueError('The private connection settings could not be read.')
        return value

    @contextmanager
    def _update(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory = self.directory.lstat()
        if (not stat.S_ISDIR(directory.st_mode) or
                (os.name != 'nt' and (directory.st_uid != os.getuid() or directory.st_mode & 0o022))):
            raise ValueError('Use a private settings directory owned by your account.')
        with config_lock(self.directory / '.connections.lock'):
            record = self._read()
            yield record
            atomic_json(self.path, encode_record(record))

    def _token(self, record):
        configured = self.override or record.get('apify_key')
        if configured or os.name == 'nt':
            return configured
        return env_key(self.directory / 'apify.env')

    def token(self):
        return self._token(self._read())

    def _status(self, record):
        key = self._token(record)
        verified = bool(key and record.get('verified_key') == hashlib.sha256(key.encode()).hexdigest())
        return {
            'apify_configured': bool(key),
            'apify_verified': verified,
            'apify_external': bool(self.override),
            'ai_provider': record.get('ai_provider') if verified else None,
            'onboarded': verified and record.get('ai_decided') is True,
        }

    def status(self):
        return self._status(self._read())

    def binding(self):
        record = self._read()
        if self._status(record)['apify_verified']:
            return self._token(record), record['account_id']
        return None, None

    def save_apify(self, candidate=None):
        if candidate is not None and not isinstance(candidate, str):
            raise ValueError('Enter a valid API key.')
        if candidate not in (None, '') and self.override and candidate != self.override:
            raise ValueError('The launch environment supplies your Apify key. Verify that key, or restart without the override to replace it.')
        key = valid_key(candidate or self.token())
        fingerprint = hashlib.sha256(key.encode()).hexdigest()
        try:
            account = self.verifier(key)
        except RejectedKey:
            if self._read().get('verified_key') == fingerprint:
                with self._update() as record:
                    if record.get('verified_key') == fingerprint:
                        record.pop('verified_key', None)
                        record['ai_decided'] = False
            raise
        with self._update() as record:
            if record.get('account_id') != account:
                record.clear()
            record.update(account_id=account, verified_key=fingerprint)
            if not self.override:
                record['apify_key'] = key
            else:
                record.pop('apify_key', None)
        return self.status()

    def save_ai(self, body):
        with self._update() as record:
            if not self._status(record)['apify_verified']:
                raise ValueError('Verify your Apify key first.')
            if set(body) == {'skip'} and body['skip'] is True:
                record.pop('ai_key', None)
                record.pop('ai_provider', None)
            else:
                if set(body) != {'provider', 'key'}:
                    raise ValueError('Choose a provider and enter its API key, or skip this step.')
                provider = body.get('provider')
                if not isinstance(provider, str) or provider not in PROVIDERS:
                    raise ValueError('Choose a supported AI provider.')
                key = valid_key(body.get('key'))
                if key == self._token(record) or key.startswith('apify_api_'):
                    raise ValueError('Enter the selected provider’s key instead of an Apify key.')
                record['ai_key'] = key
                record['ai_provider'] = provider
            record['ai_decided'] = True
        return self.status()

    def provider_key(self, requested):
        record = self._read()
        if not self._status(record)['onboarded'] or requested != record.get('ai_provider') or not record.get('ai_key'):
            raise ValueError('Connect this provider in the private dashboard first.')
        return record['ai_key']
