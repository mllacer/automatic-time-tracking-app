from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from time_tracker.models import EventType, SessionEvent


class EventStore:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path)
        self._connection.row_factory = sqlite3.Row

    def initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                occurred_at_utc TEXT NOT NULL,
                local_time TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def append(self, event: SessionEvent) -> SessionEvent:
        cursor = self._connection.execute(
            """
            INSERT INTO events (event_type, occurred_at_utc, local_time, source)
            VALUES (?, ?, ?, ?)
            """,
            (
                event.event_type.value,
                event.occurred_at_utc.isoformat(),
                event.local_time.isoformat(),
                event.source,
            ),
        )
        self._connection.commit()
        return SessionEvent(
            id=int(cursor.lastrowid),
            event_type=event.event_type,
            occurred_at_utc=event.occurred_at_utc,
            local_time=event.local_time,
            source=event.source,
        )

    def list_events(self) -> list[SessionEvent]:
        rows = self._connection.execute(
            """
            SELECT id, event_type, occurred_at_utc, local_time, source
            FROM events
            ORDER BY occurred_at_utc ASC, id ASC
            """
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def close(self) -> None:
        self._connection.close()

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> SessionEvent:
        return SessionEvent(
            id=int(row["id"]),
            event_type=EventType(row["event_type"]),
            occurred_at_utc=datetime.fromisoformat(row["occurred_at_utc"]),
            local_time=datetime.fromisoformat(row["local_time"]),
            source=str(row["source"]),
        )

