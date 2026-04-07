from __future__ import annotations

import ctypes
import hashlib
from ctypes import wintypes
from pathlib import Path


ERROR_ALREADY_EXISTS = 183
KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)

CreateMutexW = KERNEL32.CreateMutexW
CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
CreateMutexW.restype = wintypes.HANDLE

CloseHandle = KERNEL32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL


def build_mutex_name(base_dir: Path) -> str:
    normalized = str(base_dir.expanduser().resolve()).lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"Local\\TimeTracker-{digest}"


class SingleInstanceLock:
    def __init__(self, base_dir: Path) -> None:
        self.name = build_mutex_name(base_dir)
        self._handle: int | None = None

    def acquire(self) -> bool:
        handle = CreateMutexW(None, False, self.name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())

        self._handle = handle
        return ctypes.get_last_error() != ERROR_ALREADY_EXISTS

    def close(self) -> None:
        if self._handle is None:
            return
        CloseHandle(self._handle)
        self._handle = None

