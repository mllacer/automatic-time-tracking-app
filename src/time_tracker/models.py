from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum


class EventType(StrEnum):
    SESSION_START = "session_start"
    UNLOCK = "unlock"
    LOCK = "lock"
    SUSPEND = "suspend"
    RESUME = "resume"
    LOGOFF = "logoff"
    SHUTDOWN = "shutdown"


@dataclass(frozen=True, slots=True)
class SessionEvent:
    event_type: EventType
    occurred_at_utc: datetime
    local_time: datetime
    source: str
    id: int | None = None

    def __post_init__(self) -> None:
        if self.occurred_at_utc.tzinfo is None:
            raise ValueError("occurred_at_utc must be timezone-aware")
        if self.local_time.tzinfo is None:
            raise ValueError("local_time must be timezone-aware")
        if self.occurred_at_utc.utcoffset() != timedelta(0):
            raise ValueError("occurred_at_utc must be normalized to UTC")


@dataclass(frozen=True, slots=True)
class WorkSession:
    start_at: datetime
    end_at: datetime
    end_reason: str

    def __post_init__(self) -> None:
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("WorkSession datetimes must be timezone-aware")
        if self.end_at < self.start_at:
            raise ValueError("end_at must be greater than or equal to start_at")

    @property
    def local_date(self) -> date:
        return self.start_at.date()

    @property
    def duration(self) -> timedelta:
        return self.end_at - self.start_at

    @property
    def decimal_hours(self) -> float:
        return round(self.duration.total_seconds() / 3600, 2)


def build_event(event_type: EventType, source: str, local_time: datetime | None = None) -> SessionEvent:
    event_local_time = local_time or datetime.now().astimezone()
    if event_local_time.tzinfo is None:
        raise ValueError("local_time must be timezone-aware")
    utc_time = event_local_time.astimezone(timezone.utc)
    return SessionEvent(
        event_type=event_type,
        occurred_at_utc=utc_time,
        local_time=event_local_time,
        source=source,
    )

