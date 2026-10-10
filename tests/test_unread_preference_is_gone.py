"""The stored preference nothing read is gone, and stays gone.

RNV-RULINGS-2026-10-05, item 5. Ruled 2026-10-05: "Yes."

WHAT WENT. The settings' defaults stored a colour for a new slot under one
key that nothing read and no control set. A new slot starts from
config.DEFAULT_COLOR; the stored value only looked as if it decided that.
A settings file that already holds the key keeps it: the key is carried and
ignored, as it always was.

WHAT THIS GUARD HOLDS.

1. The defaults do not store it.
2. No Python in the repository names it. This file names it in order to
   forbid it, and is the one file the sweep leaves out.
3. The sweep is looking.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: What went. A new slot's colour is config.DEFAULT_COLOR.
PREFERENCE_GONE = "default_slot_color"

MENTION_ONLY = {pathlib.Path(__file__).name}
DELIVERY_MARK = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"
SKIP_DIRS = {"build", "dist", "__pycache__", "venv", "env", "node_modules", "htmlcov"}
MIN_PYTHON = 60


def _python():
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        parts = rel.split("/")
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts[:-1]):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if len(parts) == 1 and DELIVERY_MARK in text:
            continue                                  # a delivery script names what it retires
        yield rel, text


def _named(pairs) -> list:
    return [f"{rel}:{number}" for rel, text in pairs
            if pathlib.PurePosixPath(rel).name not in MENTION_ONLY
            for number, line in enumerate(text.splitlines(), 1) if PREFERENCE_GONE in line]


def test_the_defaults_do_not_store_it():
    from utils.settings_manager import SettingsManager
    defaults = SettingsManager.DEFAULT_SETTINGS if hasattr(SettingsManager, "DEFAULT_SETTINGS") \
        else SettingsManager._get_default_settings()
    assert PREFERENCE_GONE not in defaults["preferences"], \
        f"the settings' defaults store {PREFERENCE_GONE} again, and nothing reads it"
    assert "default_slot_weight" in defaults["preferences"], \
        "the slot's other default is not where this test looks: it would pass on anything"


def test_nothing_names_it():
    found = _named(_python())
    assert not found, (
        f"{PREFERENCE_GONE} is written again:\n  " + "\n  ".join(found)
        + "\nIt was removed on 2026-10-05: nothing read it. A new slot starts from config.DEFAULT_COLOR.")


def test_the_sweep_is_looking():
    pairs = list(_python())
    assert len(pairs) >= MIN_PYTHON, f"the sweep only found {len(pairs)} Python files"
    assert "utils/settings_manager.py" in {rel for rel, _ in pairs}
    assert _named([("utils/sample.py", f'    "{PREFERENCE_GONE}": [1, 2, 3],\n')]) == ["utils/sample.py:1"]
    assert _named([("tests/" + next(iter(MENTION_ONLY)), PREFERENCE_GONE)]) == []
    assert _named([("tests/other.py", pathlib.Path(__file__).read_text(encoding="utf-8"))]), \
        "this file no longer names it: drop the exemption"
