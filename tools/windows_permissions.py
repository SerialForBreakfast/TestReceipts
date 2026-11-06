"""Scoped privilege controls for Windows permission tests, not application runtime."""
from contextlib import contextmanager


@contextmanager
def ordinary_file_access():
    """Temporarily disable backup/restore privileges; restore their exact old state.

    Elevated hosted runners can otherwise bypass file DACLs with backup semantics.
    No privileges are added, removed, or permanently changed.
    """
    import ctypes
    from ctypes import wintypes

    class LUID(ctypes.Structure):
        _fields_ = [('LowPart', wintypes.DWORD), ('HighPart', wintypes.LONG)]

    class LUIDAttributes(ctypes.Structure):
        _fields_ = [('Luid', LUID), ('Attributes', wintypes.DWORD)]

    class TokenPrivileges(ctypes.Structure):
        _fields_ = [('PrivilegeCount', wintypes.DWORD), ('Privileges', LUIDAttributes * 1)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    api.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    api.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
    api.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TokenPrivileges),
                                        wintypes.DWORD, ctypes.POINTER(TokenPrivileges), ctypes.POINTER(wintypes.DWORD)]
    token = wintypes.HANDLE()
    if not api.OpenProcessToken(kernel.GetCurrentProcess(), 0x0020 | 0x0008, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    previous = []
    observations = {}
    try:
        for name in ['SeBackupPrivilege', 'SeRestorePrivilege']:
            luid = LUID()
            if not api.LookupPrivilegeValueW(None, name, ctypes.byref(luid)):
                raise ctypes.WinError(ctypes.get_last_error())
            disable, old = TokenPrivileges(), TokenPrivileges()
            disable.PrivilegeCount = 1
            disable.Privileges[0].Luid = luid
            disable.Privileges[0].Attributes = 0
            returned = wintypes.DWORD()
            ctypes.set_last_error(0)
            if not api.AdjustTokenPrivileges(token, False, ctypes.byref(disable), ctypes.sizeof(old),
                                             ctypes.byref(old), ctypes.byref(returned)):
                raise ctypes.WinError(ctypes.get_last_error())
            error = ctypes.get_last_error()
            if error not in [0, 1300]:
                raise ctypes.WinError(error)
            previous.append(old)
            observations[name] = {'present': error != 1300, 'changed': old.PrivilegeCount > 0,
                                  'previouslyEnabled': bool(old.PrivilegeCount and old.Privileges[0].Attributes & 2)}
        yield observations
    finally:
        try:
            for old in reversed(previous):
                if old.PrivilegeCount and not api.AdjustTokenPrivileges(token, False, ctypes.byref(old), 0, None, None):
                    raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel.CloseHandle(token)
