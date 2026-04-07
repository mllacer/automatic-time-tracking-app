from __future__ import annotations

import logging
from collections.abc import Callable

import win32api
import win32con
import win32gui
import win32ts

from time_tracker.models import EventType


WM_WTSSESSION_CHANGE = 0x02B1
WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012
ENDSESSION_LOGOFF = 0x80000000
NOTIFY_FOR_THIS_SESSION = getattr(win32ts, "NOTIFY_FOR_THIS_SESSION", 0x0)
WTS_SESSION_LOCK = getattr(win32ts, "WTS_SESSION_LOCK", 0x7)
WTS_SESSION_UNLOCK = getattr(win32ts, "WTS_SESSION_UNLOCK", 0x8)


class WindowsEventListener:
    def __init__(
        self,
        handler: Callable[[EventType, str], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self._handler = handler
        self._logger = logger or logging.getLogger(__name__)
        self._hwnd: int | None = None
        self._class_name = "TimeTrackerWindow"

    def run(self) -> None:
        hinst = win32api.GetModuleHandle(None)
        wndclass = win32gui.WNDCLASS()
        wndclass.hInstance = hinst
        wndclass.lpszClassName = self._class_name
        wndclass.lpfnWndProc = self._wnd_proc
        class_atom = win32gui.RegisterClass(wndclass)
        try:
            self._hwnd = win32gui.CreateWindowEx(
                0,
                class_atom,
                self._class_name,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                hinst,
                None,
            )
            win32ts.WTSRegisterSessionNotification(self._hwnd, NOTIFY_FOR_THIS_SESSION)
            self._logger.info("Windows event listener started")
            win32gui.PumpMessages()
        finally:
            if self._hwnd is not None:
                try:
                    win32ts.WTSUnRegisterSessionNotification(self._hwnd)
                except win32gui.error:
                    pass

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_WTSSESSION_CHANGE:
            self._handle_session_change(wparam)
            return 0

        if msg == WM_POWERBROADCAST:
            self._handle_power_broadcast(wparam)
            return 1

        if msg == win32con.WM_QUERYENDSESSION:
            return 1

        if msg == win32con.WM_ENDSESSION:
            if wparam:
                event_type = EventType.LOGOFF if (lparam & ENDSESSION_LOGOFF) else EventType.SHUTDOWN
                self._emit(event_type, "windows_endsession")
            return 0

        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _handle_session_change(self, wparam: int) -> None:
        if wparam == WTS_SESSION_LOCK:
            self._emit(EventType.LOCK, "windows_wts")
        elif wparam == WTS_SESSION_UNLOCK:
            self._emit(EventType.UNLOCK, "windows_wts")

    def _handle_power_broadcast(self, wparam: int) -> None:
        if wparam == PBT_APMSUSPEND:
            self._emit(EventType.SUSPEND, "windows_power")
        elif wparam in {PBT_APMRESUMESUSPEND, PBT_APMRESUMEAUTOMATIC}:
            self._emit(EventType.RESUME, "windows_power")

    def _emit(self, event_type: EventType, source: str) -> None:
        try:
            self._logger.info("Received %s from %s", event_type.value, source)
            self._handler(event_type, source)
        except Exception:
            self._logger.exception("Failed handling %s event from %s", event_type.value, source)
