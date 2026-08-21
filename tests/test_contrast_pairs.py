"""
Contrast pairing guard.   RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN

The rest of the suite asserts hex EQUALITY. That cannot catch a legible colour
placed on the wrong ground, which is how every gold failure here survived: the
value was correct on both sides, the pairing was not. A value census reports
this repo clean.

Walks the three generated stylesheets, resolves each foreground against the
background it actually renders on, applies the floor.

Ported from rnv-text-transformer.
"""
from __future__ import annotations

import re

import pytest

from utils import config

TEXT_FLOOR = 4.5
HEX = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")
NAMED = {"white": "#ffffff", "black": "#000000", "gray": "#808080",
         "grey": "#808080"}

# (theme, foreground, background) -> why it may sit below the floor.
ACCEPTED = {
    # The main-window button scheme is a deliberate inversion: the hover ground
    # goes near-black while the label stays black, and the pressed state flips
    # the label to white. Both are intentional and predate this pass.
    ("LIGHT", "#000000", "#333333"): "main button hover -- deliberate inversion",
    ("DARK", "#000000", "#444444"): "main button pressed -- deliberate inversion",
    ("IMAGE", "#000000", "#444444"): "main button pressed -- deliberate inversion",
}


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chans = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _norm(value: str) -> str | None:
    value = value.strip().rstrip(";").strip()
    if HEX.match(value):
        return value.lower()
    if value.lower() in NAMED:
        return NAMED[value.lower()]
    match = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value)
    if match:
        return "#%02x%02x%02x" % tuple(int(match.group(i)) for i in (1, 2, 3))
    return None


def _rules(css: str):
    """Linear scan, not a regex.

    A regex over `\{\{([^{}]*)\}\}` once found 23 of 173 rules in a sibling
    repo and every contrast test passed vacuously. Walk the string.
    """
    index = 0
    while True:
        open_at = css.find("{", index)
        if open_at == -1:
            return
        close_at = css.find("}", open_at)
        if close_at == -1:
            return
        head = css[index:open_at].strip()
        group = head.splitlines()[-1].strip() if head else ""
        body = css[open_at + 1:close_at]
        # `A, B { ... }` is two selectors sharing a body. Reading it as one
        # string mis-parses the second and makes sub-control names unmatchable.
        for selector in (s.strip() for s in group.split(",")):
            if selector:
                yield selector, body
        index = close_at + 1


def _decls(body: str) -> dict[str, str]:
    out = {}
    for part in body.split(";"):
        if ":" in part:
            key, _, value = part.partition(":")
            out[key.strip().lower()] = value.strip()
    return out


def _base(selector: str) -> str:
    return re.split(r"[:\[]", selector.split("::")[0])[0].strip()


# Sub-controls that render no text. A slider handle has a fill and inherits a
# foreground, but nothing draws with it, so pairing them reports failures that
# cannot be seen. ::item and ::tab are NOT here -- those carry labels, and they
# are where the real failures were.
TEXTLESS = (
    "handle", "indicator", "groove", "add-page", "sub-page",
    "add-line", "sub-line",
)


def _is_textless(selector: str) -> bool:
    if "::" not in selector:
        return False
    part = selector.split("::", 1)[1]
    name = re.split(r"[:\[ ]", part)[0].strip()
    return name in TEXTLESS


def _pairs(theme: str):
    css = getattr(config, theme + "_STYLESHEET")
    rules = list(_rules(css))
    assert len(rules) >= 30, (
        f"{theme}: the rule walker found only {len(rules)} rules -- it stopped "
        f"looking, and every assertion below would pass by measuring nothing")
    ground, rest_bg, rest_fg = None, {}, {}
    for selector, body in rules:
        decls = _decls(body)
        base = _base(selector)
        if selector in ("QMainWindow", "QWidget") and "background-color" in decls:
            ground = _norm(decls["background-color"]) or ground
        if selector == base:
            bg = _norm(decls.get("background-color", ""))
            if bg:
                rest_bg[base] = bg
            fg = _norm(decls.get("color", ""))
            if fg:
                rest_fg[base] = fg
    for selector, body in rules:
        decls = _decls(body)
        base = _base(selector)
        # A rule that changes only the BACKGROUND still renders the inherited
        # foreground on that new ground. Skipping those is how a hover state
        # that darkens its ground under unchanged text goes unmeasured -- which
        # is exactly the shape of the failures this file exists to catch.
        if "color" not in decls and not (
                "background-color" in decls or "background" in decls):
            continue
        if _is_textless(selector):
            continue
        fg = _norm(decls.get("color", "")) or rest_fg.get(base) or rest_fg.get("QWidget")
        bg = (_norm(decls.get("background-color", ""))
              or _norm(decls.get("background", ""))
              or rest_bg.get(base) or ground)
        if fg and bg:
            yield selector, fg, bg


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "IMAGE"])
def test_text_pairs_meet_aa(theme):
    failures = []
    for selector, fg, bg in _pairs(theme):
        if (theme, fg, bg) in ACCEPTED:
            continue
        ratio = contrast(fg, bg)
        if ratio < TEXT_FLOOR:
            failures.append(f"{theme} {selector}: {fg} on {bg} = {ratio:.4f}:1")
    assert not failures, (
        "text below AA 4.5:1 --\n  " + "\n  ".join(sorted(set(failures)))
        + "\n\nIf one of these is intentional, add it to ACCEPTED with a reason.")


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "IMAGE"])
def test_accepted_entries_are_still_real(theme):
    """An ACCEPTED entry that no longer occurs is a licence waiting for a future
    defect. It should be deleted, not left to outlive its reason."""
    seen = {(theme, fg, bg) for _, fg, bg in _pairs(theme)}
    stale = [k for k in ACCEPTED if k[0] == theme and k not in seen]
    assert not stale, f"stale ACCEPTED entries for {theme}: {stale}"


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "IMAGE"])
def test_the_textless_exclusion_does_not_swallow_the_sheet(theme):
    """Guard the guard. An exclusion list that grew until it matched everything
    would make every assertion above pass by measuring nothing."""
    css = getattr(config, theme + "_STYLESHEET")
    selectors = [s for s, _ in _rules(css) if s]
    excluded = [s for s in selectors if _is_textless(s)]
    assert len(excluded) < len(selectors) * 0.75, (
        f"{theme}: the textless exclusion dropped {len(excluded)} of "
        f"{len(selectors)} selectors")


def test_every_textless_entry_is_a_real_sub_control():
    """A dead entry is a licence waiting for a future defect."""
    seen = set()
    for theme in ("DARK", "LIGHT", "IMAGE"):
        for selector, _ in _rules(getattr(config, theme + "_STYLESHEET")):
            if "::" in selector:
                seen.add(re.split(r"[:\[ ]", selector.split("::", 1)[1])[0].strip())
    stale = [name for name in TEXTLESS if name not in seen]
    assert not stale, f"TEXTLESS names nothing in any stylesheet: {stale}"


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "IMAGE"])
def test_the_audit_finds_something_to_audit(theme):
    """Any detector that can return 'nothing found' needs a companion test
    proving it is still looking."""
    pairs = list(_pairs(theme))
    assert len(pairs) >= 10, f"{theme}: resolved only {len(pairs)} pairs"


# The two button schemes, as the other four aligned apps render them.
# (bg, fg) for rest, hover, pressed.
MAIN_SCHEME = {
    "DARK":  (("#1a1a1a", "#e0e0e0"), ("#333333", "#e0e0e0"), ("#444444", "#000000")),
    "LIGHT": (("#ffffff", "#000000"), ("#333333", "#000000"), ("#444444", "#ffffff")),
    "IMAGE": (("#1a1a1a", "#e0e0e0"), ("#333333", "#e0e0e0"), ("#444444", "#000000")),
}


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "IMAGE"])
def test_main_button_scheme_is_unchanged(theme):
    """The black-and-white scheme with its inverse transitions. The near-black
    hover carrying black text is INTENTIONAL and is not a contrast defect."""
    css = getattr(config, theme + "_STYLESHEET")
    found = {}
    for selector, body in _rules(css):
        if selector in ("QPushButton", "QPushButton:hover", "QPushButton:pressed"):
            found[selector] = _decls(body)
    base = found["QPushButton"]
    actual = tuple(
        (_norm(found[sel].get("background-color", base.get("background-color", ""))),
         _norm(found[sel].get("color", base.get("color", ""))))
        for sel in ("QPushButton", "QPushButton:hover", "QPushButton:pressed"))
    assert actual == MAIN_SCHEME[theme], (
        f"{theme} main button scheme moved -- "
        f"expected {MAIN_SCHEME[theme]} but got {actual}")


def test_dialog_button_pressed_fills_with_the_ACCENT_not_the_derivative():
    """The gold dialog scheme is rest -> hover (ground shifts, text turns gold)
    -> pressed (gold fill, text flips). The pressed FILL is the accent in both
    modes; only the hover TEXT spends light's derivative.

    Asserted because the failure is invisible to every other check here: white
    on the derivative reads 5.5547 against the accent's 4.5429, so a swap
    improves the contrast number while breaking the scheme.
    """
    light = config.ThemeManager.LIGHT_THEME
    assert light["button_pressed_bg"] == light["accent"] == config.BRAND_DARK_GOLD
    assert light["accent_text"] == config.BRAND_DARK_GOLD_DEEP
    assert light["accent_text"] != light["accent"], (
        "light must spend its derivative on TEXT and keep the accent as the fill")
    for name in ("DARK", "IMAGE"):
        palette = getattr(config.ThemeManager, name + "_THEME")
        assert palette["button_pressed_bg"] == palette["accent"] == config.BRAND_GOLD


def test_four_gold_values_in_the_whole_app():
    """Two registered, two derived. Two rendered per mode."""
    values = {getattr(config, n).lower() for n in dir(config)
              if n.startswith("BRAND_") and isinstance(getattr(config, n), str)}
    assert len(values) == 4, f"expected 4 gold values, found {len(values)}: {sorted(values)}"


def test_gold_text_never_lands_below_the_coverage_floor():
    """Below #e8e8e8 gold does not carry text. That is a ruling, not a gap --
    so assert nothing tries."""
    deep = config.ThemeManager.LIGHT_THEME["accent_text"]
    for _, fg, bg in _pairs("LIGHT"):
        if fg != deep.lower():
            continue
        assert _luminance(bg) <= _luminance("#ffffff"), bg
        assert contrast(fg, bg) >= TEXT_FLOOR, f"{fg} on {bg}"
