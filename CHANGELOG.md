# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-04-07

### Changed

- Hardened config path resolution so relative paths follow the loaded `config.json` location, which improves Startup and packaged-launch behavior.
- Made startup launch resolution fall back to `pythonw.exe -m time_tracker` when the repository-level `.pyw` launcher is unavailable.
- Expanded the README with setup, configuration, runtime, testing, packaging, and limitation details.
- Migrated the project into the dedicated `automatic-time-tracking-app` repository.

### Added

- Unit tests for config path anchoring and startup command resolution.

## [0.1.0] - Initial local release

### Added

- Windows background event tracking for lock, unlock, suspend, resume, logoff, and shutdown events.
- SQLite event persistence and yearly Excel export with monthly detail and weekly summary sheets.
- Single-instance locking and automatic Startup shortcut creation.
