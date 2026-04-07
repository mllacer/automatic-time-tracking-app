from __future__ import annotations

from pathlib import Path

from time_tracker.single_instance import build_mutex_name


def test_build_mutex_name_is_stable_for_same_folder(tmp_path: Path) -> None:
    first = build_mutex_name(tmp_path)
    second = build_mutex_name(tmp_path)

    assert first == second
    assert first.startswith("Local\\TimeTracker-")


def test_build_mutex_name_changes_for_different_folders(tmp_path: Path) -> None:
    first = build_mutex_name(tmp_path / "one")
    second = build_mutex_name(tmp_path / "two")

    assert first != second
