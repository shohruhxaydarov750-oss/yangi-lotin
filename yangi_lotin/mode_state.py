"""Independent live conversion switches and their small local preference file."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModeSnapshot:
    cyrillic: bool
    old_latin: bool
    latin_to_cyrillic: bool = False

    def __post_init__(self) -> None:
        if self.latin_to_cyrillic and (self.cyrillic or self.old_latin):
            raise ValueError("Opposite conversion directions cannot be active together")

    @property
    def any_enabled(self) -> bool:
        return self.cyrillic or self.old_latin or self.latin_to_cyrillic


class ModeSelection:
    """Remember the active switches so one tray click can pause and restore."""

    def __init__(
        self,
        cyrillic: bool = True,
        old_latin: bool = True,
        last_nonempty: ModeSnapshot | None = None,
        *,
        latin_to_cyrillic: bool = False,
    ) -> None:
        self._current = ModeSnapshot(
            bool(cyrillic), bool(old_latin), bool(latin_to_cyrillic)
        )
        if self._current.any_enabled:
            self._last_nonempty = self._current
        elif last_nonempty is not None and last_nonempty.any_enabled:
            self._last_nonempty = last_nonempty
        else:
            self._last_nonempty = ModeSnapshot(True, True)

    @property
    def current(self) -> ModeSnapshot:
        return self._current

    @property
    def last_nonempty(self) -> ModeSnapshot:
        return self._last_nonempty

    def set_modes(
        self,
        cyrillic: bool,
        old_latin: bool,
        latin_to_cyrillic: bool = False,
    ) -> ModeSnapshot:
        self._current = ModeSnapshot(
            bool(cyrillic), bool(old_latin), bool(latin_to_cyrillic)
        )
        if self._current.any_enabled:
            self._last_nonempty = self._current
        return self._current

    def set_mode(self, name: str, enabled: bool) -> ModeSnapshot:
        if name == "cyrillic":
            return self.set_modes(
                enabled,
                self._current.old_latin,
                self._current.latin_to_cyrillic and not enabled,
            )
        if name == "old_latin":
            return self.set_modes(
                self._current.cyrillic,
                enabled,
                self._current.latin_to_cyrillic and not enabled,
            )
        if name == "latin_to_cyrillic":
            if enabled:
                return self.set_modes(False, False, True)
            return self.set_modes(self._current.cyrillic, self._current.old_latin)
        raise ValueError(f"Unknown conversion mode: {name}")

    def toggle_mode(self, name: str) -> ModeSnapshot:
        if name == "cyrillic":
            return self.set_mode(name, not self._current.cyrillic)
        if name == "old_latin":
            return self.set_mode(name, not self._current.old_latin)
        if name == "latin_to_cyrillic":
            return self.set_mode(name, not self._current.latin_to_cyrillic)
        raise ValueError(f"Unknown conversion mode: {name}")

    def toggle_all(self) -> ModeSnapshot:
        if self._current.any_enabled:
            return self.set_modes(False, False, False)
        return self.set_modes(
            self._last_nonempty.cyrillic,
            self._last_nonempty.old_latin,
            self._last_nonempty.latin_to_cyrillic,
        )

    @classmethod
    def load(cls, path: Path | None = None) -> ModeSelection:
        """Use safe defaults if the preference file is missing or damaged."""

        target = path or settings_path()
        try:
            with target.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError):
            return cls()

        if not isinstance(data, dict):
            return cls()
        version = data.get("version")
        if type(version) is not int or version not in (1, 2):
            return cls()
        names = ("cyrillic", "old_latin", "last_cyrillic", "last_old_latin")
        if version == 2:
            names += ("latin_to_cyrillic", "last_latin_to_cyrillic")
        if any(type(data.get(name)) is not bool for name in names):
            return cls()

        reverse = data.get("latin_to_cyrillic", False)
        last_reverse = data.get("last_latin_to_cyrillic", False)
        if reverse and (data["cyrillic"] or data["old_latin"]):
            return cls()
        if last_reverse and (data["last_cyrillic"] or data["last_old_latin"]):
            return cls()

        return cls(
            cyrillic=data["cyrillic"],
            old_latin=data["old_latin"],
            last_nonempty=ModeSnapshot(
                data["last_cyrillic"], data["last_old_latin"], last_reverse
            ),
            latin_to_cyrillic=reverse,
        )

    def save(self, path: Path | None = None) -> None:
        """Write only switch preferences, replacing the previous file atomically."""

        target = path or settings_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 2,
            "cyrillic": self._current.cyrillic,
            "old_latin": self._current.old_latin,
            "latin_to_cyrillic": self._current.latin_to_cyrillic,
            "last_cyrillic": self._last_nonempty.cyrillic,
            "last_old_latin": self._last_nonempty.old_latin,
            "last_latin_to_cyrillic": self._last_nonempty.latin_to_cyrillic,
        }
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target.parent,
                prefix="settings-", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def settings_path() -> Path:
    local_data = os.environ.get("LOCALAPPDATA")
    if local_data:
        base = Path(local_data)
    elif os.name == "nt":
        base = Path.home() / "AppData" / "Local"
    else:
        base = Path.home() / ".config"
    return base / "YangiLotin" / "settings.json"


__all__ = ["ModeSelection", "ModeSnapshot", "settings_path"]
