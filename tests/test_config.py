from __future__ import annotations

import json
from pathlib import Path

from time_tracker import config as config_module


def test_load_config_resolves_relative_paths_from_config_file_location(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config-home"
    working_dir = tmp_path / "working-dir"
    config_dir.mkdir()
    working_dir.mkdir()

    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "base_dir": "tracker-data",
                "database_path": "db\\events.db",
                "log_path": "logs\\app.log",
                "auto_start_enabled": False,
                "log_level": "debug",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(working_dir)
    monkeypatch.setattr(config_module, "_find_config_path", lambda: config_path)

    app_config = config_module.load_config()

    assert app_config.config_path == config_path
    assert app_config.base_dir == (config_dir / "tracker-data").resolve()
    assert app_config.database_path == (config_dir / "tracker-data" / "db" / "events.db").resolve()
    assert app_config.log_path == (config_dir / "tracker-data" / "logs" / "app.log").resolve()
    assert app_config.auto_start_enabled is False
    assert app_config.log_level == "DEBUG"


def test_load_config_writes_default_config_in_current_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    app_config = config_module.load_config()

    assert (tmp_path / "config.json").exists()
    assert app_config.config_path == (tmp_path / "config.json")
    assert app_config.base_dir == tmp_path.resolve()
    assert app_config.database_path == (tmp_path / "time-tracking.db").resolve()
    assert app_config.log_path == (tmp_path / "logs" / "app.log").resolve()
