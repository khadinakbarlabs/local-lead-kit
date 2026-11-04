"""Shared local setup for the Looksy plugin and the standalone app."""
import getpass
import os
from pathlib import Path
import sys
import tempfile
import warnings


def workspace():
    root = Path.home() / '.local/share'
    previous = root / 'local-lead-kit'
    if previous.is_dir() and not (root / 'looksy').exists():
        return previous
    return root / 'looksy'


def settings_file():
    return Path.home() / '.config/looksy/apify.env'


def load_token(path=None):
    if path is None:
        if os.environ.get('APIFY_TOKEN'):
            return
        path = settings_file()
        if not path.exists():
            return
    if path.stat().st_mode & 0o077:
        raise ValueError('Choose an environment file readable only by your account.')
    for line in path.read_text().splitlines():
        name, sep, value = line.partition('=')
        if name.strip() == 'APIFY_TOKEN' and sep:
            os.environ['APIFY_TOKEN'] = value.strip().strip('"\'')
            return
    raise ValueError('The selected file does not define APIFY_TOKEN.')


def connect():
    if not sys.stdin.isatty():
        raise ValueError('Run the connect command in your own interactive terminal.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            token = getpass.getpass('Paste your Apify API key (input hidden): ').strip()
        except getpass.GetPassWarning:
            raise ValueError('A terminal with hidden keyboard input is required.') from None
    if not token.isascii() or not token or any(c.isspace() or not c.isprintable() for c in token):
        raise ValueError('Enter an API key without whitespace.')
    path = settings_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write('APIFY_TOKEN=' + token + '\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print('Key saved for Looksy Agent. Apify access will be checked on your first live preview. Return to your assistant to continue.')
