from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    base_dir: Path
    database_path: Path
    log_path: Path
    auto_start_enabled: bool
    log_level: str
    config_path: Path | None = None


DEFAULT_CONFIG = {
    "base_dir": ".",
    "database_path": "time-tracking.db",
    "log_path": "logs/app.log",
    "auto_start_enabled": True,
    "log_level": "INFO",
}


def load_config() -> AppConfig:
    config_path = _find_config_path()
    raw = DEFAULT_CONFIG.copy()

    if config_path is not None and config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            raw.update(json.load(handle))
    else:
        config_path = Path.cwd() / "config.json"
        _write_default_config(config_path)

    base_dir = _resolve_path(raw["base_dir"], Path.cwd())
    database_path = _resolve_path(raw["database_path"], base_dir)
    log_path = _resolve_path(raw["log_path"], base_dir)

    return AppConfig(
        base_dir=base_dir,
        database_path=database_path,
        log_path=log_path,
        auto_start_enabled=bool(raw["auto_start_enabled"]),
        log_level=str(raw["log_level"]).upper(),
        config_path=config_path,
    )


def _find_config_path() -> Path | None:
    candidates = [Path.cwd() / "config.json"]
    executable_dir = Path(sys.executable).resolve().parent
    if executable_dir not in {candidate.parent for candidate in candidates}:
        candidates.append(executable_dir / "config.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_path(raw_path: str, anchor: Path) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (anchor / path).resolve()


def _write_default_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(DEFAULT_CONFIG, handle, indent=2)
        handle.write("\n")

