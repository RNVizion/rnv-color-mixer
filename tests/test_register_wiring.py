"""
mixer's dark palettes, wired to the names the same pass created.

WHY THIS APP NEEDED NAMING FIRST. The 2026-08-27 neutral rewire covered the
three stylesheet templates. Seven other modules build their own QSS from
ThemeManager's theme dicts, and four dark greys lived only there -- so they had
never been named, and there was nothing to wire them to.

NOTHING MOVED. The delivery script resolved every palette before and after and
refused to write unless they matched entry for entry.
"""
from __future__ import annotations

import ast
import pathlib

from utils import config
from utils.config import ThemeManager

DARK = ThemeManager.DARK_THEME
IMAGE = ThemeManager.IMAGE_THEME
LIGHT = ThemeManager.LIGHT_THEME
PALETTES = {"DARK_THEME": DARK, "IMAGE_THEME": IMAGE}

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "utils" / "config.py"

SUBSTITUTE = {
    "#000000": "TRUE_BLACK",
    "#0a0a0a": "APP_CANVAS_DARK",
    "#1a1a1a": "APP_SURFACE_DARK",
    "#2a2a2a": "APP_CARD_DARK",
    "#333333": "APP_BORDER_DARK",
    "#3a3a3a": "APP_PANEL_HOVER_DARK",
    "#888888": "APP_HINT_DARK",
}
NEW_NAMES = ("APP_CANVAS_DARK", "APP_CARD_DARK", "APP_PANEL_HOVER_DARK",
             "APP_HINT_DARK")


def _dicts(names):
    tree = ast.parse(SRC.read_text(encoding="utf-8-sig"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, "id", None) in names and isinstance(node.value, ast.Dict):
                out[getattr(target, "id")] = node.value
    missing = set(names) - set(out)
    assert not missing, f"palettes that are no longer dict literals: {missing}"
    return out


# ------------------------------------------------------------- guard the guard

def test_the_names_this_file_reads_exist():
    for name in NEW_NAMES:
        assert hasattr(config, name), f"utils.config has no {name}"
        assert name in config.NEUTRAL_PROVENANCE, f"{name} has no provenance"
    assert _dicts(PALETTES)


def test_the_new_names_hold_the_values_they_were_created_for():
    assert config.APP_CANVAS_DARK == "#0a0a0a"
    assert config.APP_CARD_DARK == "#2a2a2a"
    assert config.APP_PANEL_HOVER_DARK == "#3a3a3a"
    assert config.APP_HINT_DARK == "#888888"


# ------------------------------------------------------------ the substitution

def test_no_allowlisted_value_is_spelled_as_a_literal_in_dark():
    """A literal cannot follow its base. There must not be one left."""
    literals = []
    for dict_name, node in _dicts(PALETTES).items():
        for key, value in zip(node.keys, node.values):
            if not isinstance(key, ast.Constant):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                const = SUBSTITUTE.get(value.value.lower())
                if const:
                    literals.append(f"{dict_name}[{key.value!r}] = {value.value} "
                                    f"(should read {const})")
    assert not literals, ("values still written as literals:\n  "
                          + "\n  ".join(literals))


def test_every_dark_name_resolves_to_the_value_it_replaced():
    wrong = []
    by_name = {v: k for k, v in SUBSTITUTE.items()}
    for dict_name, node in _dicts(PALETTES).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Name) and value.id in by_name:
                actual = PALETTES[dict_name].get(key.value)
                if actual != by_name[value.id]:
                    wrong.append(f"{dict_name}[{key.value!r}] -> {value.id} "
                                 f"resolves to {actual}")
    assert not wrong, "names resolving wrongly:\n  " + "\n  ".join(wrong)


def test_no_light_name_leaked_into_a_dark_palette():
    """The trap the allowlist exists for. DARK['menu_disabled'] is #666666 and
    the only constant holding #666666 is APP_HANDLE_LIGHT -- a value-keyed
    substitution across every constant would have written a light name into the
    dark palette, true by value and false by name."""
    leaked = []
    for dict_name, node in _dicts(PALETTES).items():
        for key, value in zip(node.keys, node.values):
            if isinstance(value, ast.Name) and value.id.endswith("_LIGHT"):
                leaked.append(f"{dict_name}[{key.value!r}] -> {value.id}")
    assert not leaked, ("light names inside a dark palette:\n  "
                        + "\n  ".join(leaked))


def test_menu_disabled_is_still_the_literal_that_proves_the_point():
    """Guard the guard for the test above: it can only catch a leak while the
    value that would leak is still there to leak."""
    assert DARK.get("menu_disabled") == "#666666", (
        "menu_disabled moved; the allowlist reasoning above needs re-checking")


def test_the_light_palette_was_left_alone():
    """The light ladder is unruled. Two of its greys -- #aaaaaa and #e0e0e0 --
    are deliberately still unnamed. If a later pass wires light, this test has
    to be deleted on purpose."""
    named = []
    for key, value in zip(*(lambda n: (n.keys, n.values))(_dicts(("LIGHT_THEME",))["LIGHT_THEME"])):
        if isinstance(value, ast.Name) and value.id in SUBSTITUTE.values():
            named.append(f"LIGHT_THEME[{key.value!r}] -> {value.id}")
    assert not named, ("the light palette now references the dark names:\n  "
                       + "\n  ".join(named))
