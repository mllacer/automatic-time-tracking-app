from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

SHORTCUT_NAME = "TimeTracker.lnk"


def ensure_startup_shortcut(base_dir: Path, logger: logging.Logger | None = None) -> Path:
    import win32com.client

    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    shortcut_path = startup_dir / SHORTCUT_NAME

    target, arguments = resolve_launch_command()
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = str(base_dir)
    shortcut.IconLocation = target
    shortcut.Description = "Time tracking background app"
    shortcut.Save()

    if logger is not None:
        logger.info("Ensured startup shortcut at %s", shortcut_path)
    return shortcut_path


def resolve_launch_command(module_path: Path | None = None) -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve()), ""

    interpreter = Path(sys.executable).resolve()
    if interpreter.name.lower() == "python.exe":
        candidate = interpreter.with_name("pythonw.exe")
        if candidate.exists():
            interpreter = candidate

    launcher = (module_path or Path(__file__)).resolve().parents[2] / "run_time_tracker.pyw"
    if launcher.exists():
        arguments = f'"{launcher}"'
    else:
        arguments = "-m time_tracker"
    return str(interpreter), arguments
