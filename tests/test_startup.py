from __future__ import annotations

import sys
from pathlib import Path

from time_tracker.startup import resolve_launch_command


def test_resolve_launch_command_uses_pythonw_and_repo_launcher(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    module_path = repo_root / "src" / "time_tracker" / "startup.py"
    launcher = repo_root / "run_time_tracker.pyw"
    interpreter = tmp_path / "python.exe"
    gui_interpreter = tmp_path / "pythonw.exe"

    module_path.parent.mkdir(parents=True)
    module_path.write_text("# marker\n", encoding="utf-8")
    launcher.write_text("# launcher\n", encoding="utf-8")
    interpreter.write_text("", encoding="utf-8")
    gui_interpreter.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "executable", str(interpreter))
    monkeypatch.delattr(sys, "frozen", raising=False)

    target, arguments = resolve_launch_command(module_path=module_path)

    assert target == str(gui_interpreter.resolve())
    assert arguments == f'"{launcher.resolve()}"'


def test_resolve_launch_command_falls_back_to_module_launch(tmp_path: Path, monkeypatch) -> None:
    site_packages = tmp_path / "site-packages"
    module_path = site_packages / "time_tracker" / "startup.py"
    interpreter = tmp_path / "python.exe"
    gui_interpreter = tmp_path / "pythonw.exe"

    module_path.parent.mkdir(parents=True)
    module_path.write_text("# marker\n", encoding="utf-8")
    interpreter.write_text("", encoding="utf-8")
    gui_interpreter.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "executable", str(interpreter))
    monkeypatch.delattr(sys, "frozen", raising=False)

    target, arguments = resolve_launch_command(module_path=module_path)

    assert target == str(gui_interpreter.resolve())
    assert arguments == "-m time_tracker"


def test_resolve_launch_command_uses_frozen_executable(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "TimeTracker.exe"
    executable.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    target, arguments = resolve_launch_command()

    assert target == str(executable.resolve())
    assert arguments == ""
