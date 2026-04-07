from __future__ import annotations

import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

from time_tracker.config import AppConfig, load_config
from time_tracker.event_store import EventStore
from time_tracker.excel_exporter import ExcelExporter
from time_tracker.logging_utils import configure_logging
from time_tracker.models import EventType, SessionEvent, build_event
from time_tracker.single_instance import SingleInstanceLock
from time_tracker.startup import ensure_startup_shortcut
from time_tracker.win32_helpers import is_session_locked
from time_tracker.windows_listener import WindowsEventListener


class TimeTrackerApp:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._store = EventStore(config.database_path)
        self._exporter = ExcelExporter(config.base_dir, logger=self._logger)

    def run(self) -> int:
        self._store.initialize()

        if self._config.auto_start_enabled:
            try:
                ensure_startup_shortcut(self._config.base_dir, logger=self._logger)
            except Exception:
                self._logger.exception("Failed to create or update the startup shortcut.")

        self._export_all()
        self._record_startup_state()

        listener = WindowsEventListener(self._handle_runtime_event, logger=self._logger)
        listener.run()
        return 0

    def close(self) -> None:
        self._store.close()

    def _record_startup_state(self) -> None:
        try:
            unlocked = not is_session_locked()
        except OSError:
            self._logger.exception("Could not determine startup lock state; assuming unlocked.")
            unlocked = True

        if unlocked:
            self._persist_events([build_event(EventType.SESSION_START, "startup")])

    def _handle_runtime_event(self, event_type: EventType, source: str) -> None:
        now = datetime.now().astimezone()
        events = [build_event(event_type, source, local_time=now)]

        if event_type == EventType.RESUME:
            try:
                if not is_session_locked():
                    events.append(build_event(EventType.UNLOCK, "resume_probe", local_time=now))
            except OSError:
                self._logger.exception("Could not determine resume lock state; waiting for a real unlock event.")

        self._persist_events(events)

    def _persist_events(self, events: list[SessionEvent]) -> None:
        stored = [self._store.append(event) for event in events]
        for event in stored:
            self._logger.info(
                "Recorded %s at %s from %s",
                event.event_type.value,
                event.local_time.isoformat(),
                event.source,
            )
        self._export_all()

    def _export_all(self) -> None:
        events = self._store.list_events()
        if not events:
            return
        try:
            self._exporter.export(events)
        except Exception:
            self._logger.exception("Failed to export workbook data.")


def main() -> int:
    if platform.system() != "Windows":
        raise RuntimeError("This application only supports Windows in v1.")

    config = load_config()
    config.base_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(config.log_path, config.log_level)
    logger = logging.getLogger(__name__)
    logger.info(
        "Application launch detected. base_dir=%s executable=%s cwd=%s argv=%s",
        config.base_dir,
        Path(sys.executable).resolve(),
        Path.cwd(),
        sys.argv,
    )

    instance_lock = SingleInstanceLock(config.base_dir)
    acquired_lock = instance_lock.acquire()
    if not acquired_lock:
        logger.info("Another tracker instance is already running for %s. Exiting.", config.base_dir)
        instance_lock.close()
        return 0

    logger.info("Single-instance lock acquired: %s", instance_lock.name)

    try:
        app = TimeTrackerApp(config)
        try:
            return app.run()
        finally:
            app.close()
    finally:
        logger.info("Application shutdown. base_dir=%s pid=%s", config.base_dir, os.getpid())
        instance_lock.close()
