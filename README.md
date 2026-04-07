# Automatic Time Tracking App

Automatic Time Tracking App is a Windows background utility that listens for workstation lock, unlock, suspend, resume, logoff, and shutdown events, stores the raw event stream in SQLite, and exports computed work sessions to yearly Excel workbooks.

## What the application does

- Runs silently in the background on Windows.
- Persists session events to a local SQLite database.
- Rebuilds work sessions from the raw event history every time it exports.
- Generates one Excel workbook per year with monthly detail sheets and monthly weekly-summary sheets.
- Prevents multiple instances from running against the same data directory.
- Creates a shortcut in the Windows Startup folder so the tracker can relaunch automatically after sign-in.

## Project layout

- `src/time_tracker/app.py`: main application orchestration.
- `src/time_tracker/windows_listener.py`: Win32 message loop for session and power events.
- `src/time_tracker/event_store.py`: SQLite persistence for raw events.
- `src/time_tracker/session_builder.py`: conversion from events to work sessions.
- `src/time_tracker/excel_exporter.py`: Excel workbook generation with monthly and weekly summaries.
- `src/time_tracker/startup.py`: Startup shortcut creation and launch command resolution.
- `run_time_tracker.pyw`: source launcher for a silent background start.

## Prerequisites

- Windows 10 or Windows 11.
- Python 3.11 or newer.
- A Python environment with `pywin32` available.

## Installation

Create a virtual environment and install the project with development tools:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If you only need runtime dependencies, `pip install -r requirements.txt` is enough.

## Configuration

The application reads `config.json` from the current working directory first and then from the executable directory. Relative paths are resolved from the directory that contains the config file.

Default configuration:

```json
{
  "base_dir": ".",
  "database_path": "time-tracking.db",
  "log_path": "logs/app.log",
  "auto_start_enabled": true,
  "log_level": "INFO"
}
```

Notes:

- `base_dir` is the root folder for generated runtime files.
- `database_path` is where the SQLite event store is written.
- `log_path` controls the application log output.
- `auto_start_enabled` enables or disables Startup shortcut management.
- `log_level` accepts standard Python logging levels such as `INFO` and `DEBUG`.

## Running from source

For the normal background launch:

```powershell
python run_time_tracker.pyw
```

For a console-visible run while debugging:

```powershell
python -m time_tracker
```

## Startup behavior

On launch, the application can create or refresh a shortcut in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`. The shortcut points to:

- the packaged executable when running as a frozen build
- `pythonw.exe` plus `run_time_tracker.pyw` when running from the repository
- `pythonw.exe -m time_tracker` as a fallback when the source launcher is not available

This keeps the Startup shortcut resilient across source runs, editable installs, and packaged builds.

## Running tests

```powershell
pytest
```

The automated tests cover session building, Excel export generation, single-instance mutex naming, configuration resolution, and startup command resolution.

## Building a standalone executable

Install `pyinstaller` in the same environment and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

## Runtime output

- SQLite database: `time-tracking.db`
- Excel exports: `time-tracking-<year>.xlsx`
- Application log: `logs/app.log`

All of these default to the configured `base_dir`.

## Current limitations

- The listener is Windows-only in the current implementation.
- Workbook export happens after each persisted event, so frequent event bursts rewrite the yearly file.
- The project does not yet ship with an installer or service wrapper.
