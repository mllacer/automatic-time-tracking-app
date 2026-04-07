from __future__ import annotations

from datetime import datetime, timedelta, timezone

from time_tracker.models import EventType, SessionEvent
from time_tracker.session_builder import SessionBuilder


LOCAL_TZ = timezone(timedelta(hours=1))


def make_event(event_type: EventType, hour: int, minute: int = 0, day: int = 1) -> SessionEvent:
    local_time = datetime(2026, 1, day, hour, minute, tzinfo=LOCAL_TZ)
    return SessionEvent(
        id=None,
        event_type=event_type,
        occurred_at_utc=local_time.astimezone(timezone.utc),
        local_time=local_time,
        source="test",
    )


def test_startup_then_lock_creates_one_session() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 8),
            make_event(EventType.LOCK, 13),
        ]
    )

    assert len(sessions) == 1
    assert sessions[0].local_date.isoformat() == "2026-01-01"
    assert sessions[0].decimal_hours == 5.0
    assert sessions[0].end_reason == EventType.LOCK.value


def test_lock_unlock_shutdown_creates_two_sessions() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 8),
            make_event(EventType.LOCK, 13),
            make_event(EventType.UNLOCK, 14),
            make_event(EventType.SHUTDOWN, 18),
        ]
    )

    assert len(sessions) == 2
    assert [session.decimal_hours for session in sessions] == [5.0, 4.0]


def test_multiple_unlock_cycles_same_day_create_multiple_sessions() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 8),
            make_event(EventType.LOCK, 10),
            make_event(EventType.UNLOCK, 10, 30),
            make_event(EventType.LOCK, 12),
            make_event(EventType.UNLOCK, 13),
            make_event(EventType.SHUTDOWN, 17),
        ]
    )

    assert len(sessions) == 3
    assert [session.decimal_hours for session in sessions] == [2.0, 1.5, 4.0]


def test_duplicate_consecutive_events_do_not_create_duplicate_sessions() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 8),
            make_event(EventType.SESSION_START, 8, 5),
            make_event(EventType.LOCK, 12),
            make_event(EventType.LOCK, 12, 5),
            make_event(EventType.UNLOCK, 13),
            make_event(EventType.UNLOCK, 13, 1),
            make_event(EventType.SHUTDOWN, 18),
        ]
    )

    assert len(sessions) == 2
    assert [session.decimal_hours for session in sessions] == [4.0, 5.0]


def test_suspend_resume_and_unlock_sequence_respects_lock_state() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 8),
            make_event(EventType.SUSPEND, 11),
            make_event(EventType.RESUME, 11, 30),
            make_event(EventType.UNLOCK, 12),
            make_event(EventType.SHUTDOWN, 15),
        ]
    )

    assert len(sessions) == 2
    assert [session.decimal_hours for session in sessions] == [3.0, 3.0]


def test_cross_midnight_session_is_split_by_day() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 22, day=1),
            make_event(EventType.SHUTDOWN, 2, day=2),
        ]
    )

    assert len(sessions) == 2
    assert sessions[0].local_date.isoformat() == "2026-01-01"
    assert sessions[0].decimal_hours == 2.0
    assert sessions[0].end_reason == "day_boundary"
    assert sessions[1].local_date.isoformat() == "2026-01-02"
    assert sessions[1].decimal_hours == 2.0
    assert sessions[1].end_reason == EventType.SHUTDOWN.value


def test_later_day_start_caps_stale_open_session_at_midnight() -> None:
    sessions = SessionBuilder().build(
        [
            make_event(EventType.SESSION_START, 22, day=1),
            make_event(EventType.SESSION_START, 8, day=3),
            make_event(EventType.LOCK, 10, day=3),
        ]
    )

    assert len(sessions) == 2
    assert [session.local_date.isoformat() for session in sessions] == ["2026-01-01", "2026-01-03"]
    assert [session.decimal_hours for session in sessions] == [2.0, 2.0]
    assert [session.end_reason for session in sessions] == ["day_boundary", EventType.LOCK.value]
