# Time Tracking App

Windows background time tracker that records lock and unlock activity, stores raw events in SQLite, and exports worked intervals to yearly Excel files.

## Run from source

1. Install Python 3.11 or newer.
2. Create a virtual environment and install dependencies with `pip install -r requirements.txt`.
3. Run `python run_time_tracker.pyw` for a silent launch.

## Build a standalone executable

Install `pyinstaller` in the same environment, then run `powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1`.
