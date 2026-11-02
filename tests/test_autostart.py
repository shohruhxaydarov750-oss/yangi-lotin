from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from yangi_lotin import autostart


class FakeKey:
    def __init__(self, registry: FakeRegistry) -> None:
        self.registry = registry

    def __enter__(self) -> FakeKey:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self) -> None:
        self.values: dict[str, tuple[str, int]] = {}

    def OpenKey(self, _hive: object, _path: str, _reserved: int, _access: int) -> FakeKey:
        return FakeKey(self)

    def CreateKeyEx(self, _hive: object, _path: str, _reserved: int, _access: int) -> FakeKey:
        return FakeKey(self)

    def QueryValueEx(self, _key: FakeKey, name: str) -> tuple[str, int]:
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name]

    def SetValueEx(self, _key: FakeKey, name: str, _reserved: int, kind: int, value: str) -> None:
        self.values[name] = (value, kind)

    def DeleteValue(self, _key: FakeKey, name: str) -> None:
        del self.values[name]


class AutostartTests(unittest.TestCase):
    CURRENT = '"C:\\Users\\Test User\\YangiLotin.exe" --tray'

    def setUp(self) -> None:
        self.registry = FakeRegistry()
        self.registry_patch = mock.patch.object(autostart, "winreg", self.registry)
        self.windows_patch = mock.patch.object(autostart.os, "name", "nt")
        self.command_patch = mock.patch.object(
            autostart, "startup_command", return_value=self.CURRENT
        )
        self.registry_patch.start()
        self.windows_patch.start()
        self.command_patch.start()
        self.addCleanup(self.registry_patch.stop)
        self.addCleanup(self.windows_patch.stop)
        self.addCleanup(self.command_patch.stop)

    def test_register_status_and_remove_only_our_value(self) -> None:
        self.registry.values["OtherApp"] = ("other.exe", self.registry.REG_SZ)
        self.assertFalse(autostart.is_enabled())
        autostart.enable()
        self.assertTrue(autostart.is_enabled())
        self.assertEqual(self.registry.values[autostart.VALUE_NAME][0], self.CURRENT)
        autostart.disable()
        self.assertFalse(autostart.is_enabled())
        self.assertEqual(self.registry.values["OtherApp"], ("other.exe", 1))

    def test_stale_copy_can_be_replaced_or_disabled(self) -> None:
        stale = '"D:\\Old Folder\\YangiLotin.exe" --startup'
        self.registry.values[autostart.VALUE_NAME] = (stale, self.registry.REG_SZ)
        self.assertFalse(autostart.is_enabled())
        autostart.enable()
        self.assertTrue(autostart.is_enabled())
        self.registry.values[autostart.VALUE_NAME] = (stale, self.registry.REG_SZ)
        autostart.disable()
        self.assertNotIn(autostart.VALUE_NAME, self.registry.values)

    def test_unrelated_value_with_same_name_is_protected(self) -> None:
        unrelated = '"C:\\Windows\\notepad.exe" --tray'
        self.registry.values[autostart.VALUE_NAME] = (unrelated, self.registry.REG_SZ)
        with self.assertRaises(autostart.AutostartConflictError):
            autostart.enable()
        with self.assertRaises(autostart.AutostartConflictError):
            autostart.disable()
        self.assertEqual(self.registry.values[autostart.VALUE_NAME][0], unrelated)

    def test_frozen_executable_path_is_quoted(self) -> None:
        self.command_patch.stop()
        with mock.patch.object(sys, "frozen", True, create=True):
            with mock.patch.object(
                autostart,
                "installed_executable_path",
                return_value=Path(r"C:\Users\Test User\AppData\Local\Programs\YangiLotin\YangiLotin.exe"),
            ):
                command = autostart.startup_command()
        self.assertEqual(
            command,
            '"C:\\Users\\Test User\\AppData\\Local\\Programs\\YangiLotin\\YangiLotin.exe" --tray',
        )

    def test_enable_copies_frozen_exe_to_stable_location(self) -> None:
        self.command_patch.stop()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "download" / "YangiLotin.exe"
            source.parent.mkdir()
            source.write_bytes(b"new executable")
            destination = Path(directory) / "Programs" / "YangiLotin" / "YangiLotin.exe"
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.object(sys, "executable", str(source)):
                    with mock.patch.object(
                        autostart, "installed_executable_path", return_value=destination
                    ):
                        autostart.enable()
                        self.assertTrue(autostart.is_enabled())
            self.assertEqual(destination.read_bytes(), b"new executable")
            self.assertEqual(
                self.registry.values[autostart.VALUE_NAME][0],
                autostart.subprocess.list2cmdline([str(destination), "--tray"]),
            )

    def test_failed_copy_preserves_old_exe_and_registry(self) -> None:
        self.command_patch.stop()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "download" / "YangiLotin.exe"
            source.parent.mkdir()
            source.write_bytes(b"new executable")
            destination = Path(directory) / "Programs" / "YangiLotin" / "YangiLotin.exe"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"old executable")
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.object(sys, "executable", str(source)):
                    with mock.patch.object(
                        autostart, "installed_executable_path", return_value=destination
                    ):
                        with mock.patch.object(
                            autostart.os, "replace", side_effect=PermissionError("locked")
                        ):
                            with self.assertRaises(PermissionError):
                                autostart.enable()
            self.assertEqual(destination.read_bytes(), b"old executable")
            self.assertNotIn(autostart.VALUE_NAME, self.registry.values)
            self.assertEqual(list(destination.parent.glob("*.tmp")), [])

    def test_new_portable_exe_refreshes_registered_startup_copy(self) -> None:
        self.command_patch.stop()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "download" / "YangiLotin.exe"
            source.parent.mkdir()
            source.write_bytes(b"new version")
            destination = Path(directory) / "Programs" / "YangiLotin" / "YangiLotin.exe"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"old version")
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.object(sys, "executable", str(source)):
                    with mock.patch.object(
                        autostart, "installed_executable_path", return_value=destination
                    ):
                        command = autostart.startup_command()
                        self.registry.values[autostart.VALUE_NAME] = (
                            command, self.registry.REG_SZ
                        )
                        self.assertTrue(autostart.refresh_if_enabled())
            self.assertEqual(destination.read_bytes(), b"new version")
            self.assertEqual(self.registry.values[autostart.VALUE_NAME][0], command)

    def test_refresh_does_nothing_when_startup_is_off(self) -> None:
        self.command_patch.stop()
        with mock.patch.object(sys, "frozen", True, create=True):
            with mock.patch.object(autostart, "_install_frozen_executable") as install:
                self.assertFalse(autostart.refresh_if_enabled())
                install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
