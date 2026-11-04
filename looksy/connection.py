"""Shared local setup for the Looksy plugin and the standalone app."""
import getpass
import os
from pathlib import Path
import sys
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
    from .settings import Connections
    token = Connections.from_environment(path).token()
    if token:
        os.environ['APIFY_TOKEN'] = token


def connect(path=None):
    from .settings import Connections
    settings = Connections.from_environment(path)
    if settings.override:
        settings.save_apify()
        print('Configured Apify key verified. Open the private dashboard to finish setup.')
        return
    if not sys.stdin.isatty():
        raise ValueError('Run the connect command in your own interactive terminal.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            token = getpass.getpass('Paste your Apify API key (input hidden): ').strip()
        except getpass.GetPassWarning:
            raise ValueError('A terminal with hidden keyboard input is required.') from None
    settings.save_apify(token)
    print('Apify key verified. Open the private dashboard to finish setup.')
