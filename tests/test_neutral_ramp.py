"""
Neutral ramp guard.

The three stylesheet templates in utils/config.py carried 120 hex literals
while the golds twenty lines above them were already interpolated. A literal
cannot follow its base: move APP_BORDER_DARK and a literal template keeps the
old value, silently, with nothing to report it.

These tests hold the templates literal-free and keep NEUTRAL_PROVENANCE
honest. They do NOT check what the values are -- tests/test_snapshots.py
already compares all three rendered stylesheets byte-for-byte against frozen
references, which is a stronger statement than any assertion here could make.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

from utils import config

HEX6 = re.compile(r"#[0-9a-fA-F]{6}\b")
TEMPLATES = ("DARK_STYLESHEET", "LIGHT_STYLESHEET", "IMAGE_STYLESHEET")


def _source() -> str:
    return pathlib.Path(config.__file__).read_text(encoding="utf-8")


def _template_bodies() -> dict[str, str]:
    """The raw source text of each template, before f-string interpolation."""
    lines = _source().splitlines()
    bodies: dict[str, str] = {}
    for i, line in enumerate(lines):
        m = re.match(r'^(DARK_STYLESHEET|LIGHT_STYLESHEET|IMAGE_STYLESHEET)\s*=\s*f?"""', line)
        if not m:
            continue
        for j in range(i + 1, len(lines)):
            if '"""' in lines[j]:
                bodies[m.group(1)] = "\n".join(lines[i:j + 1])
                break
    return bodies


def test_the_locator_still_finds_all_three_templates():
    """Guard the guard. Every check below reads the bodies this returns; if the
    locator silently found nothing, they would all pass on an empty string."""
    bodies = _template_bodies()
    assert set(bodies) == set(TEMPLATES), f"located {sorted(bodies)}"
    for name, body in bodies.items():
        assert body.count("QPushButton") >= 1, f"{name} does not look like a stylesheet"
        assert len(body.splitlines()) > 100, f"{name} body is suspiciously short"


@pytest.mark.parametrize("name", TEMPLATES)
def test_no_hex_literal_survives_in_the_template(name):
    body = _template_bodies()[name]
    found = sorted(set(HEX6.findall(body)))
    assert not found, (
        f"{name} carries hex literals again: {found}. Every rendered hex needs "
        f"a constant key -- add one to the APP NEUTRALS block and interpolate it.")


def test_provenance_names_exactly_the_neutral_constants():
    for name in config.NEUTRAL_PROVENANCE:
        assert hasattr(config, name), (
            f"NEUTRAL_PROVENANCE names {name}, which does not exist. An entry "
            f"that outlives its constant is a classification of nothing.")


def test_the_alias_is_assigned_from_its_base_not_repeated():
    """APP_BTN_HOVER_INVERSE exists so light-mode hover borrows the dark border
    step. Written as its own literal it would stop borrowing the moment
    APP_BORDER_DARK moved, and both would still render."""
    tree = ast.parse(_source())
    literals = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                literals.add(node.target.id)
    for name, kind in config.NEUTRAL_PROVENANCE.items():
        if kind == "alias":
            assert name not in literals, (
                f"{name} is classified alias but is written as a literal")
    assert config.APP_BTN_HOVER_INVERSE == config.APP_BORDER_DARK


def test_anchors_are_literals_not_computed():
    tree = ast.parse(_source())
    computed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Call):
                computed.add(node.target.id)
    for name, kind in config.NEUTRAL_PROVENANCE.items():
        if kind == "anchor":
            assert name not in computed, f"{name} is an anchor but is computed"


def test_every_neutral_constant_is_actually_rendered():
    """A constant nothing renders is dead weight, and dead weight is where the
    next wrong value hides.

    WIDENED 2026-08-29, and the widening is a correction rather than a
    relaxation. This app renders through TWO paths:

      1. the three stylesheet templates above -- main-window chrome, and the
         only thing this test used to look at;
      2. ThemeManager's three theme dicts, which ui/about_dialog.py,
         core/color_fine_tune.py, ui/canvas_view.py, core/color_slot.py,
         core/package_d_panel.py, ui/ui_handler.py and RNV_Color_Mixer.py each
         build their own QSS from.

    The templates style no QToolTip, QGroupBox, QFrame or QDialog at all, so
    path 2 paints most of the dialogs. Checking only path 1 measured "reaches a
    stylesheet template" while claiming "is rendered" -- and would have called
    a constant used by every dialog in the app dead weight.

    The strength is unchanged: a constant reached by NEITHER path still fails.
    """
    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()
    in_dicts = {str(v).lower()
                for theme in (config.ThemeManager.DARK_THEME,
                              config.ThemeManager.LIGHT_THEME,
                              config.ThemeManager.IMAGE_THEME)
                for v in theme.values()}
    orphans = [n for n in config.NEUTRAL_PROVENANCE
               if getattr(config, n).lower() not in rendered
               and getattr(config, n).lower() not in in_dicts]
    assert not orphans, f"neutral constants that render nowhere: {orphans}"


def test_both_rendering_paths_are_still_carrying_something():
    """Guard the guard for the widening. If either path stopped resolving, the
    union above would still pass on the other one -- quietly halving what this
    test covers."""
    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()
    in_dicts = {str(v).lower()
                for theme in (config.ThemeManager.DARK_THEME,
                              config.ThemeManager.LIGHT_THEME,
                              config.ThemeManager.IMAGE_THEME)
                for v in theme.values()}
    from_templates = [n for n in config.NEUTRAL_PROVENANCE
                      if getattr(config, n).lower() in rendered]
    from_dicts = [n for n in config.NEUTRAL_PROVENANCE
                  if getattr(config, n).lower() in in_dicts]
    assert len(from_templates) >= 10, f"only {len(from_templates)} reach a template"
    assert len(from_dicts) >= 10, f"only {len(from_dicts)} reach a theme dict"


def test_the_neutrals_are_pure_greys():
    """Every neutral in all five desktop apps is R = G = B. A neutral that
    picks up a cast is a colour wearing a neutral's name."""
    bad = []
    for name in config.NEUTRAL_PROVENANCE:
        h = getattr(config, name).lstrip("#")
        if not (h[0:2] == h[2:4] == h[4:6]):
            bad.append(f"{name}=#{h}")
    assert not bad, f"neutrals that are not pure greys: {bad}"
