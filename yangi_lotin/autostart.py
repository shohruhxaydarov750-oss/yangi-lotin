"""Per-user Windows startup registration for the portable desktop app."""

from __future__ import annotations

import os
import filecmp
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import winreg
except ImportError:  # Allows the pure package to be imported outside Windows.
    winreg = None  # type: ignore[assignment]


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "YangiLotin.UzbekLatin.Desktop"
STARTUP_ARGUMENT = "--tray"


class AutostartConflictError(RuntimeError):
    """The application's named startup slot contains an unrelated command."""


def _require_windows() -> None:
    if os.name != "nt" or winreg is None:
        raise OSError("Windows startup registration is available only on Windows")


def installed_executable_path() -> Path:
    """Stable per-user location used when the portable EXE is moved later."""

    local_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return base / "Programs" / "YangiLotin" / "YangiLotin.exe"


def startup_command() -> str:
    """Return a Windows-quoted command for the installed EXE or source tree."""

    if getattr(sys, "frozen", False):
        arguments = [str(installed_executable_path()), STARTUP_ARGUMENT]
    else:
        interpreter = Path(sys.executable).resolve()
        windowless = interpreter.with_name("pythonw.exe")
        if windowless.is_file():
            interpreter = windowless
        entry = Path(__file__).resolve().parents[1] / "app.py"
        arguments = [str(interpreter), str(entry), STARTUP_ARGUMENT]
    return subprocess.list2cmdline(arguments)


def _read_entry() -> tuple[str, int] | None:
    _require_windows()
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            value, kind = winreg.QueryValueEx(key, VALUE_NAME)
    except FileNotFoundError:
        return None
    return value, kind


def _command_parts(command: str) -> list[str]:
    try:
        return [part.strip('"') for part in shlex.split(command, posix=False)]
    except ValueError:
        return []


def _is_ours(command: str) -> bool:
    """Recognise an older path of this app while protecting other commands."""

    parts = _command_parts(command)
    if not parts or parts[-1] not in {STARTUP_ARGUMENT, "--startup"}:
        return False
    if len(parts) == 2 and Path(parts[0]).name.casefold() == "yangilotin.exe":
        return True
    if len(parts) == 3:
        interpreter = Path(parts[0]).name.casefold()
        entry = Path(parts[1])
        return (
            interpreter in {"python.exe", "pythonw.exe"}
            and entry.name.casefold() == "app.py"
            and entry.parent.name.casefold() == "uzbek-yangi-lotin"
        )
    return False


def is_enabled() -> bool:
    """Report whether Windows will start this particular copy of the app."""

    entry = _read_entry()
    return bool(
        entry is not None
        and entry[1] == winreg.REG_SZ
        and entry[0] == startup_command()
        and (
            not getattr(sys, "frozen", False)
            or installed_executable_path().is_file()
        )
    )


def _install_frozen_executable() -> None:
    """Copy the running EXE into a stable folder, keeping the old copy intact on failure."""

    source = Path(sys.executable).resolve(strict=True)
    destination = installed_executable_path()
    if source == destination.resolve(strict=False):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and filecmp.cmp(source, destination, shallow=False):
        return

    handle, temporary_name = tempfile.mkstemp(
        prefix=".YangiLotin-", suffix=".tmp", dir=destination.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def enable() -> None:
    """Register this copy for the current Windows user without elevation."""

    command = startup_command()
    if len(command) > 260:
        raise ValueError("Application path is too long for Windows startup")
    existing = _read_entry()
    if existing is not None and not _is_ours(existing[0]):
        raise AutostartConflictError("Startup slot is used by another command")
    if getattr(sys, "frozen", False):
        _install_frozen_executable()
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)


def refresh_if_enabled() -> bool:
    """Update the stable startup copy after a newer portable EXE is opened."""

    if not getattr(sys, "frozen", False):
        return False
    existing = _read_entry()
    if (
        existing is None
        or existing[1] != winreg.REG_SZ
        or existing[0] != startup_command()
    ):
        return False
    _install_frozen_executable()
    return True


def disable() -> None:
    """Remove only this application's startup value, leaving others intact."""

    existing = _read_entry()
    if existing is None:
        return
    if not _is_ours(existing[0]):
        raise AutostartConflictError("Startup slot is used by another command")
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.DeleteValue(key, VALUE_NAME)


__all__ = [
    "AutostartConflictError",
    "RUN_KEY",
    "VALUE_NAME",
    "STARTUP_ARGUMENT",
    "installed_executable_path",
    "startup_command",
    "is_enabled",
    "enable",
    "refresh_if_enabled",
    "disable",
]
