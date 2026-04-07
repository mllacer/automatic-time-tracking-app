from __future__ import annotations

import ctypes
from ctypes import wintypes


USER32 = ctypes.WinDLL("user32", use_last_error=True)
UOI_NAME = 2
DESKTOP_SWITCHDESKTOP = 0x0100

OpenInputDesktop = USER32.OpenInputDesktop
OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenInputDesktop.restype = wintypes.HANDLE

CloseDesktop = USER32.CloseDesktop
CloseDesktop.argtypes = [wintypes.HANDLE]
CloseDesktop.restype = wintypes.BOOL

GetUserObjectInformationW = USER32.GetUserObjectInformationW
GetUserObjectInformationW.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
GetUserObjectInformationW.restype = wintypes.BOOL


def is_session_locked() -> bool:
    desktop = OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    if not desktop:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        needed = wintypes.DWORD(0)
        GetUserObjectInformationW(desktop, UOI_NAME, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_unicode_buffer(needed.value // ctypes.sizeof(ctypes.c_wchar))
        if not GetUserObjectInformationW(desktop, UOI_NAME, buffer, needed, ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value.lower() != "default"
    finally:
        CloseDesktop(desktop)

