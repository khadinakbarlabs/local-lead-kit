"""Cross-process settings locks and Windows current-user credential protection."""
from contextlib import contextmanager
import base64
import json
import os


@contextmanager
def config_lock(path):
    flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'r+b') as handle:
        if os.name == 'nt':
            import msvcrt
            if not os.fstat(fd).st_size:
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield  # Closing the descriptor also releases the lock on process exit.


def _dpapi(content, protect):
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('data', ctypes.c_void_p)]

    buffer = ctypes.create_string_buffer(content)
    source = Blob(len(content), ctypes.addressof(buffer))
    result = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    transform = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    transform.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    transform.restype = wintypes.BOOL
    # CRYPTPROTECT_UI_FORBIDDEN. Omit LOCAL_MACHINE so the current user owns the key.
    if not transform(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise ValueError('Windows could not access the private connection settings.')
    try:
        return ctypes.string_at(result.data, result.length)
    finally:
        free = ctypes.WinDLL('kernel32').LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(result.data)


def encode_record(record):
    if os.name != 'nt':
        return record
    raw = json.dumps(record).encode('utf-8')
    return {'dpapi': base64.b64encode(_dpapi(raw, True)).decode('ascii')}


def decode_record(record):
    if os.name != 'nt':
        return record
    try:
        raw = base64.b64decode(record['dpapi'], validate=True)
        return json.loads(_dpapi(raw, False).decode('utf-8'))
    except (KeyError, TypeError, ValueError):
        raise ValueError('Windows could not read the current user’s private connection settings.') from None
