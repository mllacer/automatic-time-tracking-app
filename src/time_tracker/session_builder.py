from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, time, timedelta

from time_tracker.models import EventType, SessionEvent, WorkSession


class SessionBuilder:
    _START_EVENTS = {EventType.SESSION_START, EventType.UNLOCK}
    _END_EVENTS = {EventType.LOCK, EventType.SUSPEND, EventType.LOGOFF, EventType.SHUTDOWN}

    def build(self, events: Iterable[SessionEvent]) -> list[WorkSession]:
        ordered_events = sorted(
            events,
            key=lambda event: (event.occurred_at_utc, event.id or 0),
        )
        sessions: list[WorkSession] = []
        open_start: datetime | None = None

        for event in ordered_events:
            if event.event_type in self._START_EVENTS:
                if open_start is not None and event.local_time.date() > open_start.date():
                    sessions.extend(
                        split_session_by_day(
                            start_at=open_start,
                            end_at=next_midnight(open_start),
                            end_reason="stale_session",
                        )
                    )
                    open_start = None
                if open_start is None:
                    open_start = event.local_time
                continue

            if event.event_type in self._END_EVENTS:
                if open_start is None:
                    continue
                if event.local_time <= open_start:
                    open_start = None
                    continue
                sessions.extend(
                    split_session_by_day(
                        start_at=open_start,
                        end_at=event.local_time,
                        end_reason=event.event_type.value,
                    )
                )
                open_start = None

        return sessions


def split_session_by_day(start_at: datetime, end_at: datetime, end_reason: str) -> list[WorkSession]:
    if end_at <= start_at:
        return []

    fragments: list[WorkSession] = []
    current_start = start_at

    while current_start.date() < end_at.date():
        next_midnight_at = next_midnight(current_start)
        fragments.append(
            WorkSession(
                start_at=current_start,
                end_at=next_midnight_at,
                end_reason="day_boundary",
            )
        )
        current_start = next_midnight_at

    if current_start < end_at:
        fragments.append(
            WorkSession(
                start_at=current_start,
                end_at=end_at,
                end_reason=end_reason,
            )
        )
    return fragments


def next_midnight(value: datetime) -> datetime:
    return datetime.combine(
        value.date() + timedelta(days=1),
        time.min,
        tzinfo=value.tzinfo,
    )
