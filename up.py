#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Brand gold alignment for rnv-color-mixer.

Run from the repository root:

    python up.py              # apply, then verify
    python up.py --verify     # verify only, change nothing
    python up.py --finish     # delete this file (independent of applying)
    python up.py --install-deps   # print the apt/pip commands and exit

WHAT THIS CHANGES

  light  accent          #b19145 -> #8c7337   (BRAND_DARK_GOLD, register rev 16)
  light  accent_hover    #c4a458 -> #7e6529   (derived, lighten(dark, -14))
  dark   accent_hover    #dcc9a3 -> #dfc9a0   (derived, lighten(gold,  13))
  new    accent_text     light #7e6529, dark/image #d2bc93

Two golds per mode, before and after. The light derivative is spent once and
serves both hover and text; dark's text role reuses the accent. Asserted per
palette by tests/test_brand_mirror.py rather than remembered.

WHAT THIS DELIBERATELY DOES NOT CHANGE

  - Text on gold stays #000000 in dark and #ffffff in light. Both clear 4.5:1
    at the new value; the register prefers black and permits white where it
    serves a deliberate inversion. The inversion is not flattened.
  - The main-window button scheme. #ffffff/black -> #333333/black ->
    #444444/#ffffff is intentional and stays exactly as it is.
  - The two 8-digit values #BFb19145 / #BFB19145. The handoff note says to
    rewrite them to #BF8c7337. They occur ONLY inside
    test_no_old_gold_in_stylesheets as assertNotIn arguments -- mentions in a
    guard, not uses. Rewriting them would delete the guard against the retired
    value and replace it with one forbidding the NEW gold at 75% alpha.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"
GUARD_MARKER = "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN"

ROOT = Path.cwd()

OLD_LIGHT_GOLD = "#b" "19145"
OLD_LIGHT_HOVER = "#c" "4a458"
OLD_DARK_HOVER = "#d" "cc9a3"
GOLD = "#d" "2bc93"
DARK_GOLD = "#8" "c7337"
DEEP = "#7" "e6529"
GOLD_HOVER = "#d" "fc9a0"

LOCKED = "test_rnv_color_mixer.py"
GUARD_MIRROR = "tests/test_brand_mirror.py"
GUARD_PAIRS = "tests/test_contrast_pairs.py"

WORKFLOWS = (".github/workflows/tests-linux.yml",
             ".github/workflows/tests-windows.yml")

# Files this pass creates or edits. Used to split test failures into ours and
# pre-existing, derived from the change rather than guessed from keywords.
OUR_FILES = (
    "utils/config.py",
    "core/screen_color_picker.py",
    "core/package_d_panel.py",
    "core/color_fine_tune.py",
    "core/color_slot.py",
    "ui/about_dialog.py",
    LOCKED,
    GUARD_MIRROR,
    GUARD_PAIRS,
)


# --------------------------------------------------------------- file access

def read_any(path: Path) -> tuple[str, str]:
    """Read a file that may carry a BOM or non-UTF-8 bytes, losslessly.

    core/palette_formats.py in this repo holds a cp1252 0x97 at byte 28806.
    Decoding it strictly raises; decoding it lossily corrupts it on write.
    """
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "bom"
    try:
        return raw.decode("utf-8"), "plain"
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="surrogateescape"), "surrogate"


def write_any(path: Path, text: str, kind: str) -> None:
    if kind == "bom":
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    elif kind == "surrogate":
        path.write_bytes(text.encode("utf-8", errors="surrogateescape"))
    else:
        path.write_text(text, encoding="utf-8")


def parses(text: str, where: str) -> None:
    try:
        ast.parse(text)
    except SyntaxError as exc:
        raise SystemExit(f"ABORT: {where} would not parse after editing: {exc}")


def edit(rel: str, fn) -> bool:
    """Apply fn(src) -> src to a tracked file, refusing to write broken Python."""
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"ABORT: {rel} not found. Run from the repository root.")
    src, kind = read_any(path)
    out = fn(src)
    if out == src:
        return False
    if rel.endswith(".py"):
        parses(out, rel)
    write_any(path, out, kind)
    return True


def sub_once(src: str, old: str, new: str, where: str) -> str:
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: expected exactly 1 occurrence of {old!r} in "
                         f"{where}, found {n}. The file has moved on; stopping "
                         f"rather than guessing.")
    return src.replace(old, new)


# ------------------------------------------------------- AST-bounded regions

def dict_span(src: str, name: str) -> tuple[int, int]:
    """Byte span of a module- or class-level dict assignment, from the AST.

    Scanning forward from `name` for a closing brace finds the docstring's
    mention of the dict 30 lines above the dict, then swallows to EOF. This
    reads the parse tree instead.
    """
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                if not isinstance(node.value, ast.Dict):
                    continue
                lines = src.splitlines(keepends=True)
                start = sum(len(x) for x in lines[:node.lineno - 1])
                end = sum(len(x) for x in lines[:node.end_lineno])
                span = node.end_lineno - node.lineno
                if not (5 <= span <= 80):
                    raise SystemExit(
                        f"ABORT: {name} spans {span} lines, which is not a "
                        f"palette dict. Refusing to edit a region I cannot "
                        f"identify.")
                return start, end
    raise SystemExit(f"ABORT: no dict assignment named {name} found.")


# --------------------------------------------------------------- step 1: header

BRAND_HEADER = '''
# ---------------------------------------------------------------- brand gold
# Mirrored from RNVizion/rnv-brand engine/brand.py. Do not hand-write a gold
# here: derive it, so that a change to the base carries.
#
# The register holds TWO golds and derives the rest. Each mode renders the
# registered gold plus ONE derivative:
#
#   light   BRAND_DARK_GOLD          fills, borders, pressed
#           BRAND_DARK_GOLD_DEEP     text, and hover (which moves DEEPER on a
#                                    light ground -- away from it, not toward)
#   dark    BRAND_GOLD               fills, borders, pressed, text
#           BRAND_GOLD_HOVER         hover (lighter, again away from the ground)
#
# Pressed returns to the accent in both modes. On light that is forced -- no
# darker pressed shade keeps black legible on it. On dark the register records
# the question as OPEN and permits either; this app takes the accent, which is
# what holds the count at two and matches rnv-color-picker and
# rnv-text-transformer.
#
# COVERAGE BOUNDARY: BRAND_DARK_GOLD_DEEP carries text down to #e8e8e8 and no
# further. Below that, gold does not carry text -- a ruling, not a gap. Going
# darker does not help: -29 clears #d0d0d0 and then fails black-on-fill at
# 3.0219, the same exclusion one step down.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    Uniform per-channel, which holds hue exactly -- BRAND_DARK_GOLD and its
    derivative both measure 42.4 degrees. Non-uniform steps do not, which is
    why the hand-written variants this replaces all drifted in hue.
    """
    r, g, b = _to_rgb(hex_color)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, c + step)) for c in (r, g, b))


BRAND_GOLD: Final[str] = "@GOLD@"                       # registered
BRAND_DARK_GOLD: Final[str] = "@DARK_GOLD@"             # registered

# Derived. Steps published in rnv-brand engine/brand.py, rev 17.
BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)   # @DEEP@
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)             # @GOLD_HOVER@

# Aliases. Named so every rendered hex has a key, even where it repeats.
BRAND_DARK_GOLD_HOVER: Final[str] = BRAND_DARK_GOLD_DEEP
BRAND_DARK_GOLD_PRESSED: Final[str] = BRAND_DARK_GOLD
BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)
BRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)

# Declarative provenance, read by tests/test_brand_mirror.py. A classification
# that lives only in a test drifts from the thing it classifies.
GOLD_PROVENANCE: Final[dict[str, str]] = {
    "BRAND_GOLD": "register",
    "BRAND_DARK_GOLD": "register",
    "BRAND_DARK_GOLD_DEEP": "derived",
    "BRAND_GOLD_HOVER": "derived",
    "BRAND_DARK_GOLD_HOVER": "alias",
    "BRAND_DARK_GOLD_PRESSED": "alias",
    "BRAND_GOLD_PRESSED": "alias",
}
'''.replace("@GOLD@", GOLD).replace("@DARK_GOLD@", DARK_GOLD) \
   .replace("@DEEP@", DEEP).replace("@GOLD_HOVER@", GOLD_HOVER)


def step_header(src: str) -> str:
    if "BRAND_DARK_GOLD_DEEP" in src:
        return src
    # Final is needed by the annotations above; add it to the typing import
    # only if the import line itself lacks it, scoped to that line rather than
    # to the whole file, which would see the annotations we are about to write.
    lines = src.splitlines(keepends=True)
    out, added_final = [], False
    for line in lines:
        if (not added_final and line.startswith(("from typing import",
                                                 "import typing"))):
            if "Final" not in line:
                line = line.rstrip("\n").rstrip() + ", Final\n"
            added_final = True
        out.append(line)
    src = "".join(out)
    if not added_final:
        anchor = "import os\n"
        if anchor not in src:
            raise SystemExit("ABORT: no import anchor in utils/config.py")
        src = src.replace(anchor, anchor + "from typing import Final\n", 1)

    start, _ = dict_span(src, "DARK_THEME")
    # back up to the start of the enclosing class statement
    head = src.rfind("\nclass ThemeManager", 0, start)
    if head == -1:
        raise SystemExit("ABORT: class ThemeManager not found before DARK_THEME")
    return src[:head + 1] + BRAND_HEADER + "\n" + src[head + 1:]


# ---------------------------------------------------- step 2: palette values

DARK_MAP = {
    "'button_pressed_bg': '%s'" % GOLD: "'button_pressed_bg': BRAND_GOLD_PRESSED",
    "'button_pressed_border': '%s'" % GOLD: "'button_pressed_border': BRAND_GOLD",
    "'tooltip_border': '%s'" % GOLD: "'tooltip_border': BRAND_GOLD",
    "'accent': '%s'" % GOLD: "'accent': BRAND_GOLD",
    "'accent_hover': '%s'" % OLD_DARK_HOVER: "'accent_hover': BRAND_GOLD_HOVER",
    "'scrollbar_hover': '%s'" % GOLD: "'scrollbar_hover': BRAND_GOLD",
}
LIGHT_MAP = {
    "'button_pressed_bg': '%s'" % OLD_LIGHT_GOLD: "'button_pressed_bg': BRAND_DARK_GOLD_PRESSED",
    "'button_pressed_border': '%s'" % OLD_LIGHT_GOLD: "'button_pressed_border': BRAND_DARK_GOLD",
    "'tooltip_border': '%s'" % OLD_LIGHT_GOLD: "'tooltip_border': BRAND_DARK_GOLD",
    "'accent': '%s'" % OLD_LIGHT_GOLD: "'accent': BRAND_DARK_GOLD",
    "'accent_hover': '%s'" % OLD_LIGHT_HOVER: "'accent_hover': BRAND_DARK_GOLD_HOVER",
    "'scrollbar_hover': '%s'" % OLD_LIGHT_GOLD: "'scrollbar_hover': BRAND_DARK_GOLD",
}
# accent_text is a ROUTING key, not a new value. Light spends the derivative it
# already holds; dark reuses its accent. The count stays at two per mode.
ACCENT_TEXT = {
    "DARK_THEME": "        'accent_text': BRAND_GOLD,\n",
    "LIGHT_THEME": "        'accent_text': BRAND_DARK_GOLD_DEEP,\n",
    "IMAGE_THEME": "        'accent_text': BRAND_GOLD,\n",
}


def step_palettes(src: str) -> str:
    for name, mapping in (("DARK_THEME", DARK_MAP),
                          ("LIGHT_THEME", LIGHT_MAP),
                          ("IMAGE_THEME", DARK_MAP)):
        start, end = dict_span(src, name)
        block = src[start:end]
        for old, new in mapping.items():
            if old not in block:
                raise SystemExit(f"ABORT: {old!r} missing from {name}")
            block = block.replace(old, new)
        if "'accent_text'" not in block:
            anchor = "        'accent_hover':"
            if anchor not in block:
                raise SystemExit(f"ABORT: no accent_hover anchor in {name}")
            block = block.replace(anchor, ACCENT_TEXT[name] + anchor, 1)
        src = src[:start] + block + src[end:]
    return src


# ------------------------------------------------- step 3: stylesheet literals

def step_stylesheets(src: str) -> str:
    """Point the three module stylesheets at the constants.

    Only the LIGHT text-role declaration moves to the derivative; every other
    light gold is a fill or a border, where BRAND_DARK_GOLD clears its floor.
    """
    # the one text-role gold in LIGHT_STYLESHEET (combo popup item hover)
    src = sub_once(src, "    color: %s;\n" % OLD_LIGHT_GOLD,
                   "    color: {BRAND_DARK_GOLD_DEEP};\n", "LIGHT_STYLESHEET")
    for prop in ("selection-background-color", "border-color",
                 "background-color", "color"):
        src = src.replace("    %s: %s;" % (prop, OLD_LIGHT_GOLD),
                          "    %s: {BRAND_DARK_GOLD};" % prop)
        src = src.replace("    %s: %s;" % (prop, GOLD),
                          "    %s: {BRAND_GOLD};" % prop)
    return src


# ------------------------------------------------- step 4: text-role routing

# (file, old, new). Every one of these is a `color:` declaration -- gold used as
# TEXT. In dark accent_text IS accent, so dark renders identically; only light
# moves, onto the derivative that clears #f5f5f5 and #eeeeee.
TEXT_EDITS: dict[str, list[tuple[str, str]]] = {
    "core/color_fine_tune.py": [
        ("color: {_t['accent']};\")", "color: {_t['accent_text']};\")"),
        # ANCHORED ON INDENTATION. Unanchored, "color: {_l['accent']};" is a
        # substring of "background-color: {_l['accent']};" and of
        # "border-color: ...", so it rewrites the pressed FILL and both borders
        # as well as the hover text -- swapping a pairing this pass has no
        # business touching. Every contrast test still passed, because white on
        # the derivative reads 5.5547, better than on the accent.
        ("                    color: {_l['accent']};",
         "                    color: {_l['accent_text']};"),
    ],
    "ui/about_dialog.py": [
        ("color: {_t['accent']}; border: none;",
         "color: {_t['accent_text']}; border: none;"),
        ("color: {_t['accent']};\">", "color: {_t['accent_text']};\">"),
        ("                    color: {_l['accent']};",
         "                    color: {_l['accent_text']};"),
    ],
    "core/color_slot.py": [
        # A conditional whose arms are identical: someone reached for a
        # different light value, wrote the branch and never filled it in.
        ("color: {accent if use_dark else accent};",
         "color: {accent_text_role};"),
    ],
    "core/package_d_panel.py": [
        ("f\"color: {accent}; margin-top: 15px; margin-bottom: 5px;\"",
         "f\"color: {accent_text}; margin-top: 15px; margin-bottom: 5px;\""),
        ("                color: {accent}; font-weight: bold;",
         "                color: {accent_text}; font-weight: bold;"),
        ("                    color: {accent_col};",
         "                    color: {accent_text_col};"),
    ],
}


def step_text_roles() -> list[str]:
    touched = []
    for rel, pairs in TEXT_EDITS.items():
        def apply(src: str, pairs=pairs, rel=rel) -> str:
            for old, new in pairs:
                if old not in src:
                    raise SystemExit(f"ABORT: {rel}: {old!r} not found")
                src = src.replace(old, new)
            return src
        if edit(rel, apply):
            touched.append(rel)

    # bind the new local names next to the ones they mirror
    def slot(src: str) -> str:
        return sub_once(
            src,
            "        accent_text = _ct['accent_on']\n",
            "        accent_text = _ct['accent_on']\n"
            "        accent_text_role = _ct['accent_text']\n",
            "core/color_slot.py")
    edit("core/color_slot.py", slot)

    def panel(src: str) -> str:
        src = sub_once(
            src,
            "        accent_hov  = t['accent_hover']\n",
            "        accent_hov  = t['accent_hover']\n"
            "        accent_text = t['accent_text']\n",
            "core/package_d_panel.py:_apply_widget_stylesheet")
        # Labels built during __init__ never see a later set_theme unless they
        # are re-styled here. The panel already does this for four labels via
        # _shortcuts_label and friends; the tips and section headers were the
        # ones it missed, which is why they kept the dark gold on a light panel.
        src = sub_once(
            src,
            "        for attr in ('_shortcuts_label', '_export_label', "
            "'_palette_label', '_picker_label'):\n",
            "        for _tip_widget, _tip_tail in getattr(self, '_themed_tips', []):\n"
            "            try:\n"
            "                _tip_widget.setStyleSheet(f\"color: {accent_text}; \" + _tip_tail)\n"
            "            except RuntimeError:\n"
            "                pass\n"
            "        if hasattr(self, 'harmony_description'):\n"
            "            try:\n"
            "                _style_harmony_description(self)\n"
            "            except RuntimeError:\n"
            "                pass\n"
            "        for _hdr in getattr(self, '_themed_headers', []):\n"
            "            try:\n"
            "                _hdr.setStyleSheet(_section_header_style(accent_text))\n"
            "            except RuntimeError:\n"
            "                pass\n"
            "        for attr in ('_shortcuts_label', '_export_label', "
            "'_palette_label', '_picker_label'):\n",
            "core/package_d_panel.py:_apply_widget_stylesheet label loop")
        src = sub_once(
            src,
            "        accent_on_col = t['accent_on']\n",
            "        accent_on_col = t['accent_on']\n"
            "        accent_text_col = t['accent_text']\n",
            "core/package_d_panel.py:_apply_list_view_styles")
        return src
    edit("core/package_d_panel.py", panel)
    return touched


# ------------------------------- step 5: one ground raised, one site

def step_tab_ground(src: str) -> str:
    """The light about-dialog tab hover paints gold text on #e0e0e0.

    #e0e0e0 is below the derivative's coverage floor -- #7e6529 measures 4.2078
    there and still fails. Rather than mint a third gold, the tab hover moves to
    the ground the button hover two rules below already uses, #eeeeee, where the
    derivative clears at 4.7875. No value changes; one key does.
    """
    old = ("                QTabBar::tab:hover:!selected {{\n"
           "                    background-color: {_l['hover_color']};\n")
    new = ("                QTabBar::tab:hover:!selected {{\n"
           "                    background-color: {_l['panel_hover']};\n")
    return sub_once(src, old, new, "ui/about_dialog.py light tab hover")


# ------------------------------------------- step 6: the magnifier grid pen

def step_screen_picker(src: str) -> str:
    """QColor(191, 177, 69, 50) is #bfb145 -- neither brand gold.

    Invisible to every hex census because it is an RGB tuple. Set to the primary
    gold at the same alpha, matching its own sibling _GOLD_BRAND one line above
    and what rnv-color-picker has shipped for the identical pen since its first
    release.
    """
    src = sub_once(src, "_GOLD_BRAND = QColor('%s')" % GOLD,
                   "_GOLD_BRAND = QColor(BRAND_GOLD)",
                   "core/screen_color_picker.py")
    src = sub_once(src, "_GOLD_TRANSPARENT = QColor(191, 177, 69, 50)",
                   "_GOLD_TRANSPARENT = QColor(*BRAND_GOLD_RGB, 50)",
                   "core/screen_color_picker.py")
    if "from utils.config import BRAND_GOLD" not in src:
        anchor = "_OVERLAY_COLOR = QColor(0, 0, 0, 50)"
        src = sub_once(
            src, anchor,
            "from utils.config import BRAND_GOLD, BRAND_GOLD_RGB\n\n" + anchor,
            "core/screen_color_picker.py import")
    return src


# -------------------------------- step 7: labels that never reached the gold

TIPS = [
    ('        info.setStyleSheet(f"color: {{config.ThemeManager().DARK_THEME[\'accent\']}}; '
     'font-size: {config.FONT_SIZES[\'small\']}px;")',
     '        info.setStyleSheet(f"color: {_tip_accent(self)}; '
     'font-size: {config.FONT_SIZES[\'small\']}px;")'),
]


def step_tips(src: str) -> str:
    """Four labels whose gold declaration never reaches Qt.

    f"color: {{x}}" emits the literal text `color: {x}`; Qt discards the
    declaration and the label falls back to the inherited body colour. Measured
    live: #e0e0e0 in dark, #000000 in light. Not missing -- just never gold.
    """
    # Capture the widget name and the trailing declarations so the label can be
    # RE-styled on a theme change. Styling it once at construction is not
    # enough: these tabs are built in __init__, before set_theme runs, so a
    # label styled only at build time keeps whichever palette it was born with.
    broken_re = re.compile(
        r'(?m)^([ \t]*)(\w+)\.setStyleSheet\(f"color: '
        r'\{\{config\.ThemeManager\(\)\.DARK_THEME\[\'accent\'\]\}\}; '
        r'(.*?)"\)$')
    n = len(broken_re.findall(src))
    if n != 4:
        raise SystemExit(f"ABORT: expected 4 doubled-brace tip labels, found {n}")
    src = broken_re.sub(r'\1_style_tip(self, \2, f"\3")', src)

    helper = '''

def _style_tip(panel, widget, tail: str) -> None:
    """Paint a tip label in the accent, and register it for re-theming.

    These four labels were written as f"color: {{...}}", which emits the
    literal text `color: {...}`; Qt discards the declaration and the label
    falls back to the inherited body colour. Measured live before the fix:
    #e0e0e0 in dark, #000000 in light -- legible, and never gold.
    """
    tips = panel.__dict__.setdefault("_themed_tips", [])
    entry = (widget, tail)
    if entry not in tips:
        tips.append(entry)
    accent = _theme_colors(bool(getattr(panel, "_is_dark", True)))["accent_text"]
    widget.setStyleSheet(f"color: {accent}; " + tail)


def _section_header_style(accent: str) -> str:
    return (f"font-weight: bold; font-size: {config.FONT_SIZES['medium']}px; "
            f"color: {accent}; padding-top: 10px; padding-bottom: 5px;")


def _style_harmony_description(panel) -> None:
    accent = _theme_colors(bool(getattr(panel, "_is_dark", True)))["accent_text"]
    r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
    panel.harmony_description.setStyleSheet(
        f"color: {accent}; font-size: {config.FONT_SIZES['small']}px; "
        f"padding: 8px; background-color: rgba({r}, {g}, {b}, 0.1); "
        f"border-radius: 4px;")
'''
    # Check for the DEFINITION, not the name. The regex above has just written
    # `_tip_accent(self)` into the file, so a bare name check reads what we
    # wrote and skips the insert -- the same ordering slip that once shipped a
    # NameError from a sibling repo.
    anchor = "\n\nclass PackageDPanel(QDialog):"
    if "def _tip_accent" not in src:
        src = sub_once(src, anchor, helper + anchor,
                       "core/package_d_panel.py helper")
    return src


# --------------------------- step 8: the dark palette painted on light ground

def step_hardcoded_dark(src: str) -> str:
    """Four sites choose the palette with a literal True.

    Measured in the running panel, light mode: the Settings tab headers render
    #d2bc93 at 1.6964 on #f5f5f5 while the Quick Actions headers render the
    light gold at 2.7495 -- two different golds on screen at once, same role.
    """
    # The harmony description tints its own background from the accent's
    # channels, so it cannot share the plain label style. Its own helper, called
    # at build and again on every theme change.
    src = sub_once(
        src,
        "        _acc = config.ThemeManager.DARK_THEME['accent']\n"
        "        _r, _g, _b = int(_acc[1:3], 16), int(_acc[3:5], 16), int(_acc[5:7], 16)\n"
        "        self.harmony_description.setStyleSheet(\n"
        "            f\"color: {_acc}; font-size: {config.FONT_SIZES['small']}px; \"\n"
        "            f\"padding: 8px; background-color: rgba({_r}, {_g}, {_b}, 0.1); border-radius: 4px;\"\n"
        "        )\n",
        "        _style_harmony_description(self)\n",
        "core/package_d_panel.py:harmony_description")
    src = src.replace("        _t_h = _theme_colors(True)\n",
                      "        _t_h = _theme_colors(getattr(self, '_is_dark', True))\n")
    src = src.replace("            _t_k = _theme_colors(True)\n",
                      "            _t_k = _theme_colors(getattr(self, '_is_dark', True))\n")
    src = src.replace(
        "item.setForeground(QColor(_theme_colors(True)['accent']))",
        "item.setForeground(QColor(_theme_colors(getattr(self, '_is_dark', True))['accent_text']))")
    # _create_section_header reads 'accent'; route it to the text role
    old_header = ("        header = QLabel(text)\n"
                  "        _t_h = _theme_colors(getattr(self, '_is_dark', True))\n")
    new_header = ("        header = QLabel(text)\n"
                  "        self.__dict__.setdefault('_themed_headers', []).append(header)\n"
                  "        _t_h = _theme_colors(getattr(self, '_is_dark', True))\n")
    src = sub_once(src, old_header, new_header,
                   "core/package_d_panel.py:_create_section_header")
    src = src.replace("            color: {_t_h['accent']};",
                      "            color: {_t_h['accent_text']};")
    return src


def step_is_dark_flag(src: str) -> str:
    """set_theme knows the mode; nothing else did. Record it on the panel."""
    old = ('    def set_theme(self, is_dark: bool) -> None:\n'
           '        """Apply theme to the dialog — all colors sourced from ThemeManager."""\n'
           '        t = _theme_colors(is_dark)\n')
    new = ('    def set_theme(self, is_dark: bool) -> None:\n'
           '        """Apply theme to the dialog — all colors sourced from ThemeManager."""\n'
           '        self._is_dark = bool(is_dark)\n'
           '        t = _theme_colors(is_dark)\n')
    if old not in src:
        raise SystemExit("ABORT: set_theme signature has moved")
    return src.replace(old, new, 1)


# ---------------------------------------------- step 9: the locked test file

LOCKED_EDITS = [
    ('self.assertEqual(self.tm.LIGHT_THEME["tooltip_border"], "%s")' % OLD_LIGHT_GOLD,
     'self.assertEqual(self.tm.LIGHT_THEME["tooltip_border"], "%s")' % DARK_GOLD),
    ('self.assertIn("%s",config.LIGHT_STYLESHEET)' % OLD_LIGHT_GOLD,
     'self.assertIn("%s",config.LIGHT_STYLESHEET)' % DARK_GOLD),
    ('self.assertEqual(self.tm.LIGHT_THEME["scrollbar_hover"],"%s")' % OLD_LIGHT_GOLD,
     'self.assertEqual(self.tm.LIGHT_THEME["scrollbar_hover"],"%s")' % DARK_GOLD),
    # Stale since the rev-15 lowercase normalisation; red on main, unreported
    # because CI runs zero tests from this file (see the workflow step below).
    ('self.assertIn("F5F5F5",ss)', 'self.assertIn("f5f5f5",ss)'),
    # This regex searches the RENDERED stylesheet for `{{`. Rendered stylesheets
    # hold single braces, so it matched nothing and the loop never ran.
    (r'r"handle:(?:vertical|horizontal):hover\s*\{\{[^}]*background-color:\s*([^;]+);"',
     r'r"handle:(?:vertical|horizontal):hover\s*\{[^}]*background-color:\s*([^;]+);"'),
]


def step_locked(src: str) -> str:
    for old, new in LOCKED_EDITS:
        if old not in src:
            raise SystemExit(f"ABORT: locked file: {old!r} not found")
        src = src.replace(old, new)
    # the guard's own retired-value list must survive untouched
    if "#BFb19145" not in src or "#BFB19145" not in src:
        raise SystemExit("ABORT: the retired-value guard was damaged")
    return src


LOCKED_DIGEST_BEFORE: list[str] = []


def remember_locked_digest() -> None:
    """Capture the pre-edit digest so the workflows can be re-baselined by
    exact string, not by guessing the shape of the assignment.

    tests-linux.yml writes it as `expected = '<sha>'`; tests-windows.yml
    inlines it inside a one-line `python -c` as `e='<sha>'`. A pattern fitted
    to one silently skips the other, and the lock then fires on that platform.
    """
    import hashlib
    LOCKED_DIGEST_BEFORE.append(
        hashlib.sha256((ROOT / LOCKED).read_bytes()).hexdigest())


def step_workflows() -> list[str]:
    """Re-baseline the lock, and make the gate actually run.

    `python -m unittest FILE -k "not test_x"` -- unittest's -k is a SUBSTRING
    pattern, not a pytest expression. The string matches no test name, so the
    step reports `Ran 0 tests ... OK`. The gate of last resort has been passing
    by running nothing. pytest executes unittest.TestCase classes natively and
    does support exclusion.
    """
    import hashlib
    digest = hashlib.sha256((ROOT / LOCKED).read_bytes()).hexdigest()
    if not LOCKED_DIGEST_BEFORE:
        raise SystemExit("ABORT: the pre-edit digest was never captured")
    before = LOCKED_DIGEST_BEFORE[0]
    touched = []
    old_cmd = ('coverage run --data-file=.coverage.unittest --branch -m unittest '
               'test_rnv_color_mixer -v -k "not test_load_real_image_if_available"')
    new_cmd = ('coverage run --data-file=.coverage.unittest --branch -m pytest '
               'test_rnv_color_mixer.py -v --deselect '
               '"test_rnv_color_mixer.py::TestImageHandler::'
               'test_load_real_image_if_available"')
    for rel in WORKFLOWS:
        path = ROOT / rel
        if not path.exists():
            continue

        def apply(src: str, digest=digest, before=before) -> str:
            if before in src:
                src = src.replace(before, digest)
            elif digest not in src:
                raise SystemExit(
                    f"ABORT: {rel} pins a SHA this run did not produce. "
                    f"Expected to find {before[:12]}...; re-baselining blind "
                    f"would hide a real drift.")
            if old_cmd in src:
                src = src.replace(old_cmd, new_cmd)
            elif "-m unittest test_rnv_color_mixer" in src:
                src = re.sub(
                    r"-m unittest test_rnv_color_mixer[^\n]*",
                    '-m pytest test_rnv_color_mixer.py -v --deselect '
                    '"test_rnv_color_mixer.py::TestImageHandler::'
                    'test_load_real_image_if_available"',
                    src)
            return src
        if edit(rel, apply):
            touched.append(rel)
    return touched


# ------------------------------------------------------------ the guard tests

GUARD_MIRROR_SRC = '''"""
Brand mirror and provenance guard.   ''' + GUARD_MARKER + '''

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
    assert config.BRAND_GOLD == "''' + GOLD + '''"
    assert config.BRAND_DARK_GOLD == "''' + DARK_GOLD + '''"


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
    assert config.BRAND_DARK_GOLD_DEEP == "''' + DEEP + '''"
    assert config.BRAND_GOLD_HOVER == "''' + GOLD_HOVER + '''"


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
    assert _luminance(light["accent_hover"]) < _luminance(light["accent"]), \\
        "light hover must go deeper, away from a light ground"
    for name in ("DARK", "IMAGE"):
        p = PALETTES[name]
        assert _luminance(p["accent_hover"]) > _luminance(p["accent"]), \\
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
            text = raw.decode("utf-8-sig" if raw.startswith(b"\\xef\\xbb\\xbf")
                              else "utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="surrogateescape")
        # Files whose JOB is to talk about these values are not call sites.
        if "''' + GUARD_MARKER + '''" in text or "''' + TOOL_MARKER + '''" in text:
            continue
        yield rel, text


def test_retired_values_do_not_render():
    hits = []
    for rel, text in _tracked_sources():
        low = text.lower()
        for value, why in RETIRED.items():
            if value in low:
                hits.append(f"{rel}: {value} ({why})")
    assert not hits, "retired golds still present --\\n  " + "\\n  ".join(hits)


def test_the_retired_scan_is_still_looking():
    """Guard the guard. If the exclusion ever swallowed the repository, the
    test above would pass by reading nothing."""
    files = list(_tracked_sources())
    assert len(files) > 20, f"the source scan found only {len(files)} files"
    assert any(rel == "utils/config.py" for rel, _ in files), \\
        "the scan is not reading the colour file"


def test_the_tuple_form_is_covered_too():
    """#bfb145 lived as QColor(191, 177, 69, 50) and every hex census reported
    the repo clean. Search the notation the value actually used."""
    for rel, text in _tracked_sources():
        assert "191, 177, 69" not in text, f"{rel} still holds the off-brand tuple"
'''

GUARD_PAIRS_SRC = '''"""
Contrast pairing guard.   ''' + GUARD_MARKER + '''

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
    match = re.match(r"rgba?\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)", value)
    if match:
        return "#%02x%02x%02x" % tuple(int(match.group(i)) for i in (1, 2, 3))
    return None


def _rules(css: str):
    """Linear scan, not a regex.

    A regex over `\\{\\{([^{}]*)\\}\\}` once found 23 of 173 rules in a sibling
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
    return re.split(r"[:\\[]", selector.split("::")[0])[0].strip()


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
    name = re.split(r"[:\\[ ]", part)[0].strip()
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
        "text below AA 4.5:1 --\\n  " + "\\n  ".join(sorted(set(failures)))
        + "\\n\\nIf one of these is intentional, add it to ACCEPTED with a reason.")


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
                seen.add(re.split(r"[:\\[ ]", selector.split("::", 1)[1])[0].strip())
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
'''


# ------------------------------------------------------------------ environment

def probe() -> None:
    """Run the real thing in a subprocess rather than asking if it is findable.

    importlib.util.find_spec proves a module is FINDABLE, not importable. That
    distinction cost a half-applied repository in a sibling repo: the probe
    passed, the run then died on ImportError: libGL.so.1.
    """
    code = ("import PyQt6.QtWidgets, pytest, hypothesis; "
            "from PyQt6.QtWidgets import QApplication; print('ok')")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        return
    err = (proc.stderr or "").strip()
    print("\nThis environment cannot run the suite yet.\n")
    print(err.splitlines()[-1] if err else "(no error text)")
    print("\nFix it with:\n")
    if "libGL" in err or "libEGL" in err or "xcb" in err:
        print("  sudo apt-get update && sudo apt-get install -y \\")
        print("      libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\")
        print("      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\")
        print("      libxcb-randr0 libxcb-render-util0 libxcb-shape0 \\")
        print("      libxcb-sync1 libxcb-xfixes0 libxcb-xkb1")
        print()
    print("  pip install -r requirements.txt -r requirements-test.txt")
    print("\nThat is a SHELL command. Run it in the terminal, not with python.")
    print("Nothing has been changed. Re-run `python up.py` afterwards.\n")
    raise SystemExit(2)


def split_failures(output: str) -> tuple[list[str], list[str]]:
    """Ours vs pre-existing, by whether the file is one this pass touched.

    A keyword rule ('anything with "color" in the name') would have claimed
    tests/test_color_history.py and missed a break in a file not named for a
    colour. Derive it from the change.
    """
    ours, other = [], []
    # pytest writes `FAILED path::Class::test - reason`. The app also logs lines
    # beginning `ERROR    | Handler | ...`, which an unanchored prefix match
    # reads as test results and reports as failures that do not exist.
    pattern = re.compile(r"^(FAILED|ERROR) (\S+\.py)(::\S+)?")
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        rel = match.group(2)
        (ours if rel in OUR_FILES else other).append(line.strip())
    return ours, other


def run_tests(label: str, args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    print(f"\n--- {label} ---")
    proc = subprocess.run([sys.executable, "-m", "pytest", *args],
                          capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    tail = [l for l in out.splitlines()
            if l.startswith(("FAILED", "ERROR")) or " passed" in l
            or " failed" in l or "error" in l.lower()[:6]]
    print("\n".join(tail[-14:]) or out.splitlines()[-1:])
    if proc.returncode < 0:
        names = {
            6: "SIGABRT -- the offscreen QThread teardown documented in "
               "KNOWN_ISSUES.md; nondeterministic, and not a result",
            9: "SIGKILL (out of memory)",
            15: "SIGTERM (session reclaimed)",
        }
        sig = -proc.returncode
        print(f"\nKILLED by signal {sig} -- {names.get(sig, 'signal %d' % sig)}.")
        print("Killed is not failed. Nothing is concluded from this run.")
    return proc.returncode, out


# ------------------------------------------------------------------ the steps

def apply() -> None:
    print("applying gold alignment to rnv-color-mixer\n")

    edit("utils/config.py", step_header);        print("  1  brand header + derivation rule")
    edit("utils/config.py", step_palettes);      print("  2  palette values + accent_text routing key")
    edit("utils/config.py", step_stylesheets);   print("  3  stylesheet literals -> constants")
    step_text_roles();                           print("  4  gold-as-text routed to accent_text")
    edit("ui/about_dialog.py", step_tab_ground); print("  5  light tab hover ground #e0e0e0 -> #eeeeee")
    edit("core/screen_color_picker.py", step_screen_picker)
    print("  6  magnifier grid pen -> brand gold at alpha 50")
    edit("core/package_d_panel.py", step_is_dark_flag)
    edit("core/package_d_panel.py", step_tips);  print("  7  four tip labels reach the gold")
    edit("core/package_d_panel.py", step_hardcoded_dark)
    print("  8  hardcoded dark palette -> the mode the panel is in")
    remember_locked_digest()
    edit(LOCKED, step_locked);                   print("  9  locked file: 3 stale golds, 1 stale case, 1 dead regex")

    (ROOT / "tests").mkdir(exist_ok=True)
    (ROOT / GUARD_MIRROR).write_text(GUARD_MIRROR_SRC, encoding="utf-8")
    (ROOT / GUARD_PAIRS).write_text(GUARD_PAIRS_SRC, encoding="utf-8")
    print(" 10  guard tests installed (mirror + pairings)")

    touched = step_workflows()
    print(f" 11  workflows: lock re-baselined, gate switched to pytest "
          f"({len(touched)} file(s))")

    regenerate_snapshots()
    print(" 12  stylesheet snapshots regenerated")


def regenerate_snapshots() -> None:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", RNV_UPDATE_SNAPSHOTS="1")
    subprocess.run([sys.executable, "-m", "pytest", "tests/test_snapshots.py",
                    "-q", "-p", "no:cacheprovider"],
                   capture_output=True, text=True, env=env)


def verify() -> int:
    print("\nverifying\n")
    failed = False

    # every edited module must still import
    for rel in OUR_FILES:
        if not rel.endswith(".py") or not (ROOT / rel).exists():
            continue
        if rel.startswith("tests/") or rel == LOCKED:
            continue
        mod = rel[:-3].replace("/", ".")
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        proc = subprocess.run(
            [sys.executable, "-c",
             "from PyQt6.QtWidgets import QApplication; "
             "a=QApplication([]); import %s; print('ok')" % mod],
            capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            print(f"  IMPORT FAILED  {rel}")
            print("    " + (proc.stderr.strip().splitlines() or ["?"])[-1])
            failed = True
    if not failed:
        print("  every edited module imports")

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); from utils import config; "
         "TM=config.ThemeManager; "
         "ks=('accent','accent_hover','accent_text','tooltip_border',"
         "'scrollbar_hover','button_pressed_bg','button_pressed_border'); "
         "[print(' ', n, sorted({p[k].lower() for k in ks})) "
         "for n,p in (('DARK',TM.DARK_THEME),('LIGHT',TM.LIGHT_THEME),"
         "('IMAGE',TM.IMAGE_THEME))]"],
        capture_output=True, text=True, env=env)
    print("\n  golds rendered per palette:")
    print(proc.stdout.rstrip() or proc.stderr.strip())

    rc_guard, _ = run_tests("guard suite (the gate)",
                            [GUARD_MIRROR, GUARD_PAIRS, "-q",
                             "-p", "no:cacheprovider"])
    rc_lock, out_lock = run_tests(
        "locked file (now actually running)",
        [LOCKED, "-q", "-p", "no:cacheprovider", "--deselect",
         "%s::TestImageHandler::test_load_real_image_if_available" % LOCKED])
    rc_rest, out_rest = run_tests(
        "tests/",
        ["tests/", "-q", "-p", "no:cacheprovider", "--deselect",
         "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths"])

    ours, other = split_failures(out_lock + out_rest)
    if other:
        print("\n  pre-existing failures, not from this pass:")
        for line in other:
            print("   ", line)
    if ours:
        print("\n  FAILURES IN FILES THIS PASS TOUCHED:")
        for line in ours:
            print("   ", line)

    ok = (rc_guard == 0 and not ours and not failed)
    # A killed run proves nothing either way, so say which legs actually
    # finished rather than letting PASS imply the whole suite was seen.
    # These runs take minutes and a browser-tethered codespace gets reclaimed;
    # reporting an unqualified PASS over an incomplete suite is how a real
    # failure in the unseen 40% would get waved through.
    incomplete = [name for name, rc in (("locked file", rc_lock),
                                        ("tests/", rc_rest)) if rc < 0]
    if not ok:
        print("\nNOT CLEAN -- see above. Nothing was reverted; re-run after fixing.")
        return 1
    if incomplete:
        print("\nPASS ON THE GATE -- the guard suite is green and nothing this "
              "pass touched failed.")
        print("   But " + " and ".join(incomplete) + " was KILLED before "
              "finishing, so it did not report.")
        print("   Push and let CI run them: it is not tethered to this tab.")
    else:
        print("\nPASS -- the gate is green, every suite finished, and nothing "
              "this pass touched failed.")
    return 0


def finish() -> None:
    """Delete this file. Independent of applying, on purpose.

    Conflating the two meant --finish once verified an unchanged repository,
    and once wrote a guard file into an unaligned one.
    """
    me = Path(__file__).resolve()
    me.unlink()
    cache = me.parent / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache, ignore_errors=True)
    print("removed", me.name)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--finish", action="store_true")
    parser.add_argument("--install-deps", action="store_true")
    args = parser.parse_args()

    if args.install_deps:
        print("  sudo apt-get update && sudo apt-get install -y \\")
        print("      libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\")
        print("      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\")
        print("      libxcb-randr0 libxcb-render-util0 libxcb-shape0 \\")
        print("      libxcb-sync1 libxcb-xfixes0 libxcb-xkb1")
        print("  pip install -r requirements.txt -r requirements-test.txt")
        return 0

    if args.finish:
        finish()
        return 0

    if not (ROOT / "utils" / "config.py").exists():
        raise SystemExit("ABORT: run this from the repository root.")

    probe()
    if not args.verify:
        apply()
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
