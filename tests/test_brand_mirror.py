"""
Brand mirror and provenance guard.   RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN

This file NAMES RETIRED VALUES ON PURPOSE. Any sweep for a gold literal must
exclude it by the marker above, or it will rewrite the very list that says
which values must never come back.

Ported from rnv-text-transformer, wired to this app's ThemeManager.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from utils import config

TM = config.ThemeManager
PALETTES = {"DARK": TM.DARK_THEME, "LIGHT": TM.LIGHT_THEME, "IMAGE": TM.IMAGE_THEME}

# Values that used to render here and must not return.
RETIRED = {
    "#b19145": "old dark gold -- 2.997638 on white, under every floor it claimed",
    "#c4a458": "a tint of #b19145; orphaned the moment the accent moved",
    "#dcc9a3": "hand-written dark hover, +10/+13/+16 -- non-uniform, hue-shifting",
    "#bfb145": "the magnifier grid pen; neither brand gold, invisible as a tuple",
}

GOLD_KEYS = ("accent", "accent_hover", "accent_text", "tooltip_border",
             "scrollbar_hover", "button_pressed_bg", "button_pressed_border")


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:
        h = h[2:]
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chans = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ----------------------------------------------------------------- provenance

def test_provenance_covers_every_gold_constant():
    named = {n for n in dir(config)
             if n.startswith("BRAND_") and isinstance(getattr(config, n), str)}
    missing = named - set(config.GOLD_PROVENANCE)
    assert not missing, f"gold constants with no provenance entry: {sorted(missing)}"


def test_provenance_has_no_phantom_entries():
    phantom = [n for n in config.GOLD_PROVENANCE if not hasattr(config, n)]
    assert not phantom, f"provenance names nothing: {phantom}"


def test_provenance_groups_are_valid():
    bad = {k: v for k, v in config.GOLD_PROVENANCE.items()
           if v not in ("register", "derived", "alias")}
    assert not bad, f"invented provenance groups: {bad}"


def test_register_values_match_rnv_brand():
    assert config.BRAND_GOLD == "#d2bc93"
    assert config.BRAND_DARK_GOLD == "#8c7337"


def test_derived_constants_are_actually_derived():
    """A derivative written down as a literal is orphaned the moment the base
    moves. #c4a458 is what that looks like: a tint of a gold already retired,
    still rendering, with nothing anywhere to flag it."""
    src = pathlib.Path(config.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    literals = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                literals.add(node.target.id)
    for name, kind in config.GOLD_PROVENANCE.items():
        if kind == "derived":
            assert name not in literals, (
                f"{name} is classified derived but is written as a literal")


def test_register_constants_are_literals_not_computed():
    src = pathlib.Path(config.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    computed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Call):
                computed.add(node.target.id)
    for name, kind in config.GOLD_PROVENANCE.items():
        if kind == "register":
            assert name not in computed, f"{name} mirrors the register; do not compute it"


def test_the_derivation_steps_are_the_published_ones():
    assert config.BRAND_DARK_GOLD_DEEP == config.lighten(config.BRAND_DARK_GOLD, -14)
    assert config.BRAND_GOLD_HOVER == config.lighten(config.BRAND_GOLD, 13)
    assert config.BRAND_DARK_GOLD_DEEP == "#7e6529"
    assert config.BRAND_GOLD_HOVER == "#dfc9a0"


def test_lighten_holds_hue():
    """Uniform per-channel is the whole point; a non-uniform step drifts hue."""
    base = config._to_rgb(config.BRAND_DARK_GOLD)
    deep = config._to_rgb(config.BRAND_DARK_GOLD_DEEP)
    deltas = {b - d for b, d in zip(base, deep)}
    assert deltas == {14}, f"step is not uniform: {deltas}"


# ------------------------------------------------------- two golds per mode

@pytest.mark.parametrize("name", sorted(PALETTES))
def test_two_golds_per_mode(name):
    """One registered gold and one derivative. A third means a role went
    unshared -- and no contrast check would object, because an orphaned gold
    can be perfectly legible."""
    palette = PALETTES[name]
    golds = {palette[k].lower() for k in GOLD_KEYS}
    assert len(golds) == 2, (
        f"{name} renders {len(golds)} golds: {sorted(golds)}. "
        f"Expected the registered gold plus exactly one derivative.")


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_the_gold_key_list_still_matches_the_palette(name):
    """Guard the guard: if a gold key is renamed, test_two_golds_per_mode would
    silently measure fewer keys and keep passing."""
    palette = PALETTES[name]
    missing = [k for k in GOLD_KEYS if k not in palette]
    assert not missing, f"{name} no longer has {missing}; the count is measuring less"


def test_pressed_returns_to_the_accent_in_every_mode():
    for name, palette in PALETTES.items():
        assert palette["button_pressed_bg"] == palette["accent"], name


def test_hover_moves_away_from_the_ground():
    """One rule for both modes. Stated as 'a lighter tint for hover', which is
    what the local docs said, it is wrong half the time."""
    light = PALETTES["LIGHT"]
    assert _luminance(light["accent_hover"]) < _luminance(light["accent"]), \
        "light hover must go deeper, away from a light ground"
    for name in ("DARK", "IMAGE"):
        p = PALETTES[name]
        assert _luminance(p["accent_hover"]) > _luminance(p["accent"]), \
            f"{name} hover must go lighter, away from a dark ground"


def test_light_text_gold_clears_every_ground_it_draws_on():
    deep = PALETTES["LIGHT"]["accent_text"]
    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
        ratio = contrast(deep, ground)
        assert ratio >= 4.5, f"{deep} on {ground} = {ratio:.4f}"


def test_dark_reuses_its_accent_for_text():
    for name in ("DARK", "IMAGE"):
        assert PALETTES[name]["accent_text"] == PALETTES[name]["accent"], name


def test_white_on_the_light_fill_clears():
    """The inversion is deliberate and both values pass at the new gold."""
    assert contrast("#ffffff", PALETTES["LIGHT"]["accent"]) >= 4.5


def test_black_on_the_dark_fill_clears():
    assert contrast("#000000", PALETTES["DARK"]["accent"]) >= 4.5


# ------------------------------------------------------------ retired values

def _tracked_sources():
    import subprocess
    root = pathlib.Path(config.__file__).resolve().parent.parent
    out = subprocess.run(["git", "ls-files"], cwd=root,
                         capture_output=True, text=True).stdout.split()
    for rel in out:
        path = root / rel
        if path.suffix.lower() not in (".py", ".qss", ".css"):
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf")
                              else "utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="surrogateescape")
        # Files whose JOB is to talk about these values are not call sites.
        if "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN" in text or "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP" in text:
            continue
        yield rel, text


def test_retired_values_do_not_render():
    hits = []
    for rel, text in _tracked_sources():
        low = text.lower()
        for value, why in RETIRED.items():
            if value in low:
                hits.append(f"{rel}: {value} ({why})")
    assert not hits, "retired golds still present --\n  " + "\n  ".join(hits)


def test_the_retired_scan_is_still_looking():
    """Guard the guard. If the exclusion ever swallowed the repository, the
    test above would pass by reading nothing."""
    files = list(_tracked_sources())
    assert len(files) > 20, f"the source scan found only {len(files)} files"
    assert any(rel == "utils/config.py" for rel, _ in files), \
        "the scan is not reading the colour file"


def test_the_tuple_form_is_covered_too():
    """#bfb145 lived as QColor(191, 177, 69, 50) and every hex census reported
    the repo clean. Search the notation the value actually used."""
    for rel, text in _tracked_sources():
        assert "191, 177, 69" not in text, f"{rel} still holds the off-brand tuple"
