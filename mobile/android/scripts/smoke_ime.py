"""Exercise the installed IME through real on-screen taps in an emulator."""

from __future__ import annotations

import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


PACKAGE = "uz.shohruhxaydarov.yangilotin"
IME = f"{PACKAGE}/.YangiLotinImeService"
ACTIVITY = f"{PACKAGE}/.MainActivity"
HINT = "Matn yozing yoki qo‘ying…"


def adb(*args: str) -> str:
    result = subprocess.run(["adb", *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"adb {' '.join(args)} failed ({result.returncode}): "
            f"{result.stdout.strip()} {result.stderr.strip()}"
        )
    return result.stdout.strip()


def tree() -> ET.Element:
    adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
    return ET.fromstring(adb("shell", "cat", "/sdcard/window.xml"))


def nodes() -> list[ET.Element]:
    return list(tree().iter("node"))


def find_button(label: str) -> ET.Element:
    for _ in range(10):
        matches = [
            node for node in nodes()
            if node.get("class") == "android.widget.Button"
            and node.get("text") == label
        ]
        if matches:
            return matches[-1]
        time.sleep(0.4)
    raise AssertionError(f"Keyboard button {label!r} was not visible")


def tap_node(node: ET.Element) -> None:
    bounds = node.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise AssertionError(f"No usable bounds for {node.get('text')!r}: {bounds}")
    x1, y1, x2, y2 = map(int, match.groups())
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
    time.sleep(0.2)


def tap(label: str) -> None:
    tap_node(find_button(label))


def input_node() -> ET.Element:
    for node in nodes():
        if node.get("class") == "android.widget.EditText":
            return node
    raise AssertionError("The converter's input field was not visible")


def assert_text(expected: str) -> None:
    actual = input_node().get("text", "")
    if actual == HINT:
        actual = ""
    if actual != expected:
        raise AssertionError(f"Expected input {expected!r}; saw {actual!r}")
    print(f"PASS {expected!r}", flush=True)


def erase_one() -> None:
    tap("⌫")
    assert_text("")


def main(apk: Path) -> None:
    print(adb("install", "-r", str(apk.resolve())), flush=True)
    adb("shell", "settings", "put", "secure", "show_ime_with_hard_keyboard", "1")
    available = ""
    for _ in range(12):
        available = adb("shell", "ime", "list", "-a", "-s")
        matches = [line.strip() for line in available.splitlines() if PACKAGE in line]
        if matches:
            break
        time.sleep(1)
    else:
        raise AssertionError(f"IME not registered after install; available: {available!r}")
    ime_id = matches[0]
    print(f"Enabling {ime_id}", flush=True)
    print(adb("shell", "ime", "enable", ime_id), flush=True)
    print(adb("shell", "ime", "set", ime_id), flush=True)
    adb("shell", "am", "start", "-n", ACTIVITY)
    time.sleep(2)
    field = input_node()
    print(f"Input field bounds: {field.get('bounds')}", flush=True)
    tap_node(field)
    print(f"Input focused: {input_node().get('focused')}", flush=True)
    find_button("ESKI→Y")

    tap("s")
    tap("h")
    assert_text("ş")
    erase_one()

    tap("c")
    tap("h")
    assert_text("ç")
    erase_one()

    tap("o")
    tap("ʼ")
    assert_text("ö")
    erase_one()

    tap("g")
    tap("?123")
    tap("'")
    assert_text("ğ")
    tap("ABC")
    erase_one()

    tap("⇧")
    tap("s")
    tap("h")
    assert_text("Ş")
    erase_one()

    tap("КИР→Y")
    tap("ш")
    assert_text("ş")
    erase_one()

    tap("Y→КИР")
    tap("s")
    tap("h")
    assert_text("ш")
    erase_one()

    tap("OFF")
    tap("s")
    tap("h")
    assert_text("sh")
    tap("⌫")
    assert_text("s")
    erase_one()


if __name__ == "__main__":
    try:
        main(Path(sys.argv[1]))
    except Exception:
        try:
            print("Visible nodes:", [
                (n.get("class"), n.get("text")) for n in nodes()
                if n.get("text")
            ], flush=True)
        except Exception as inspection_error:
            print(f"Could not inspect emulator UI: {inspection_error}")
        try:
            with open("mobile/android/keyboard-smoke.png", "wb") as screenshot:
                subprocess.run(["adb", "exec-out", "screencap", "-p"],
                               check=True, stdout=screenshot)
        except Exception as inspection_error:
            print(f"Could not capture emulator screen: {inspection_error}")
        raise
