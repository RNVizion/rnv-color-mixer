"""every colour named, and every name used: the mixer's unread palette keys and constants go

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (ac54325 with up_mx_theme_save.py applied).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-04, items 6 to 9 of decisions-pending-2026-09-29.md:

  "As long as a color exist in the app it should be named and used no
   hardcoded or pointless literals should exist, only literals with a
   purpose, like data or comparison are allowed. Colors are name for swap
   ability and alignment."

USED. Two palette keys no mode read go from the dark and light palettes:
main_btn_pressed_bg and main_btn_pressed_border. The image palette was the
dark one written out a second time, the same forty keys at the same values;
it is the dark palette under its own name now, so nothing image mode never
reads is written. Two dialog keys were each read in one mode only, from that
mode's palette by name: dialog_btn_hover_bg stays in dark alone and
dialog_btn_bg in light alone. Three constants nothing in the application
read go: BRAND_GOLD_RGB, BRAND_DARK_GOLD_RGB and APP_HANDLE_HOVER_DARK.

NAMED. The colours the code spelled out each get a name in utils/config.py
at the value they had: the canvas-failed placeholder, the history export's
page, the canvas's labels and their plates, the debug overlays, and the
paper and ink of the exported palette. A slot's starting grey was written
out eleven times beside DEFAULT_COLOR, the name it always had and nothing
read; it is read from that name.

EVERY NEW NAME WAS PROVEN TO PAINT. Each was set to magenta, or its alpha
moved, on a copy of the tree, and the captures or the exported files
changed. Two colours failed that test and are NOT named, because a name
for either would paint nothing. Both are left as written and listed in the
guard as held, for a ruling:
  - the empty-history line's QColor(128, 128, 128): the list's stylesheet
    colours every item, so the line is drawn in the list's own text colour;
  - the light plate behind a dragged selection's size, QColor(200, 200,
    200, 180): the canvas asks a theme manager of its own, which always
    answers dark, so the canvas's light branch never runs.

THE LOCKED SUITE. test_all_themes_same_keys required dark and light to hold
the same keys. It now states the two keys by which they differ, and that
image holds what dark holds. Ruled: "for the locked key test if we don't use
these values we Can fix the test and remove unused values". The SHA-256 both
workflows record for the file is re-baselined to match, here and in the
digest check this script itself runs.

PROVEN BEFORE BUILDING. No line of the application looks up either removed
key. Every lookup of the two dialog keys is on the palette that keeps it, by
name. And the application draws and writes what it did: every window, tab
and combo in every mode, the canvas's labels in all three modes, the five
overlays, the placeholder, the palette SVG byte for byte, and the swatch
and instruction images pixel for pixel. The history
page's colours are the same colours, spelled #ffffff and #333333 where they
were spelled white and #333.

This script builds on up_mx_theme_save.py and refuses without it: that
script checks the locked suite against the digest this round replaces.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'RNV-NAMED-AND-USED'
SENTINEL_FILE = 'utils/config.py'
GUARD = 'tests/test_named_and_used.py'
GUARD_FILES = ['tests/test_named_and_used.py', 'tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_contrast_pairs.py', 'tests/test_derived_values.py', 'tests/test_ladder_and_plate.py', 'tests/test_mixer_wiring.py', 'tests/test_locked_file_digest.py']
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_named_and_used.py', 'tests/test_app_mirror.py', 'tests/test_brand_mirror.py', 'tests/test_button_key_names.py', 'tests/test_contrast_pairs.py', 'tests/test_derived_values.py', 'tests/test_ladder_and_plate.py', 'tests/test_mixer_wiring.py', 'tests/test_locked_file_digest.py']
DESCRIPTION = "every colour named, and every name used: the mixer's unread palette keys and constants go"

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = 'e00c2424a8c64affdaf67547e59c633e7958427ad26f0186253ae599fb992edb'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
#: THIS SCRIPT IS LEFT OUT OF THE MEASURE. .coveragerc measures every file in
#: the checkout, run or not, and while this file is in it this file is one:
#: several hundred statements at 0%. CI never sees it, so counting it measured
#: something CI does not, and a long script could fall under the floor on its
#: own weight. Measured 2026-10-04: 69.6 with a 1,030-line script, 73.4 without.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69', '--omit=' + sys.argv[1]])\n"
          "if r.returncode == 2:\n"
          "    raise AssertionError('coverage is under the Linux CI floor of 69')\n"
          "sys.exit(r.returncode)\n")
SUITES = [
    ("CI: locked file integrity", [sys.executable, "-c", _LOCK]),
    ("CI: pytest test_rnv_color_mixer.py under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.unittest",
      "--branch", "-m", "pytest", "test_rnv_color_mixer.py", "-v"]),
    ("CI: pytest tests/ under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.pytest",
      "--branch", "-m", "pytest", "tests/", "-v"]),
    ("CI: coverage combine",
     [sys.executable, "-m", "coverage", "combine", ".coverage.unittest",
      ".coverage.pytest"]),
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR, Path(__file__).name]),
]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '769b9b7034c0599b5d655cfb502741706693e765d51e2db95406c140a6b92ffd', '.github/workflows/tests-windows.yml': 'd123e5da015c9b988e5c52e9c0bb9879d492365b6db6c1f3672dc1b34f57d967'}

SHADOWS = {"config.py", "conftest.py", "canvas_view.py", "debug_overlay.py", "package_d_panel.py", "color_history.py", "palette_formats.py", "color_slot.py", "test_rnv_color_mixer.py"}

LEFT_ALONE = ["the fine-tune dialog's default colour, the picker's starting black, the ground a loaded image is flattened onto and the sample history rows: data, each listed with its reason in the guard's DATA table.", 'the preference default_slot_color: its stored default is listed as data. Nothing reads the preference, which is a ruling of its own.', "the empty-history line's grey, QColor(128, 128, 128): set on the item and never drawn, because the list's stylesheet colours every item. Not named; listed in the guard as held. Drawing it, or dropping the call, is a ruling.", "the canvas's light branch: the view asks a theme manager of its own, which always answers dark, so in light mode the canvas's labels are drawn as in dark and the light plate, QColor(200, 200, 200, 180), is never drawn. Not named; listed in the guard as held. Making the canvas follow the mode would move pixels, and is a ruling.", "image mode's entries as KEYS: they come through the spread with dark's values, read where image mode reads them and unwritten where it does not.", "clear: 'transparent', alpha 0 and Qt's transparent are how a widget is told to paint nothing, and are left as written.", 'the stay-removed tests of earlier rounds: each restricts a name that was ruled away, and is not a list of what is unused.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    # This round builds on up_mx_theme_save.py: its anchors are that round's text.
    # Without it they would all be "missing", which says the wrong thing.
    if 'RNV-THEME-SAVE' not in tree.read('RNV_Color_Mixer.py'):
        raise Stop("this round builds on up_mx_theme_save.py, which has not been applied here: RNV_Color_Mixer.py has no 'RNV-THEME-SAVE'.\nRun that script first, then this one. Nothing was written.",
                   EXIT_CANNOT_RUN)
    tree.sub('utils/config.py',
             "DEBUG_OVERLAY_COLORS = {\n    'app_window':  'rgba(255, 80, 80, 220)',\n    'slots_panel': 'rgba(80, 80, 255, 220)',\n}\n",
             "DEBUG_OVERLAY_COLORS = {\n    'app_window':  'rgba(255, 80, 80, 220)',\n    'slots_panel': 'rgba(80, 80, 255, 220)',\n    # RNV-NAMED-AND-USED (2026-10-04): the control panel's two, and the\n    # tint an overlay takes when it is given none. Each was written out\n    # where it is used; the same values.\n    'panel':       'rgba(80, 255, 80, 220)',\n    'tabs':        'rgba(255, 200, 80, 220)',\n    'default':     'rgba(255, 100, 100, 200)',\n    # and what every overlay writes and edges itself in, whatever its tint.\n    # The text was the CSS name `white`, which is this value.\n    'text':        '#ffffff',\n    'edge':        'rgba(255, 255, 255, 230)',\n}\n")
    tree.sub('utils/config.py',
             'BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD\n\nBRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)\nBRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)\n',
             'BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD\n\n# RNV-NAMED-AND-USED (2026-10-04): the two golds as integer triples stood\n# here, and nothing in the application read either. A name is kept for\n# what uses it; _to_rgb() above still derives a triple when one is needed.\n')
    tree.sub('utils/config.py',
             'APP_HANDLE_HOVER_DARK: Final[str] = "#eeeeee"\n"""Slider handle when hovered, dark and image. One step above the\ntext: grey(14), where APP_TEXT_DARK is grey(13), on the published\nink grid. Held #f0f0f0 until 2026-08-28, when the gap to #e0e0e0 was\n0x10 -- the surface ladder step, not the grid step -- and the\nsentence was true by accident.\n\nAPP-OWNED, AND IT SHARES A HEX WITH APP_ITEM_HOVER_LIGHT. Both are #eeeeee and\nthey are not the same thing: that one is APP["hover-light"], a LIGHT surface\nthe register owns; this is a DARK handle, an ink-grid step doing an ink job.\ngrey(14) is reachable from both families, which is exactly the sort of\ncoincidence the ink grid makes possible and the reason it has to be named\nrather than noticed. If the register moves the light plate, this must NOT\nfollow. tests/test_ladder_and_plate.py asserts the coincidence in both\ndirections."""\n\n',
             "# RNV-NAMED-AND-USED (2026-10-04): a name for the dark slider handle's hover,\n# grey(14), stood here. No sheet painted it: every slider's hovered handle\n# takes the accent. It went, and with it the one coincidence it made, a\n# second name on APP_ITEM_HOVER_LIGHT's #eeeeee.\n\n")
    tree.sub('utils/config.py',
             'interaction state for a piece of chrome on the strength of a shared byte --\nthe same reasoning this file already gives for APP_HANDLE_HOVER_DARK sharing\ngrey(14) with APP_ITEM_HOVER_LIGHT."""\n',
             'interaction state for a piece of chrome on the strength of a shared byte --\nthe same reasoning this file gives for APP_MENU_DIM_DARK sharing grey(6)\nwith APP_HANDLE_LIGHT."""\n')
    tree.sub('utils/config.py',
             '    "APP_TEXT_DARK": "step",\n    "APP_HANDLE_HOVER_DARK": "step",\n',
             '    "APP_TEXT_DARK": "step",\n')
    tree.sub('utils/config.py',
             'SCREEN_INFO_ALPHA: Final[int] = 0xB4\n"""180. The screen picker\'s colour readout panel (TRUE_BLACK)."""\n',
             'SCREEN_INFO_ALPHA: Final[int] = 0xB4\n"""180. The screen picker\'s colour readout panel (TRUE_BLACK)."""\n\nCANVAS_LABEL_ALPHA: Final[int] = 0xB4\n"""180. The plate behind a dragged selection\'s size, on the canvas."""\n\nCANVAS_PREVIEW_ALPHA: Final[int] = 0xC8\n"""200. The plate behind the canvas\'s colour preview."""\n\n\n# ==================== COLOURS THE CODE SPELLED OUT ====================\n#\n# RNV-NAMED-AND-USED (2026-10-04). Ruled: "As long as a color exist in the\n# app it should be named and used no hardcoded or pointless literals should\n# exist". Each of these was written out where it is used -- a hex in a\n# stylesheet, a CSS name, QColor() built from numbers -- so no palette\n# reached it and no sweep moved it. They are named here at the value they\n# had: NO PIXEL MOVES. One whose value is a colour this file already names\n# is LINKED to that name and moves with it; one with a value of its own\n# holds it, and is this application\'s alone.\n\nCANVAS_FAILED_BG: Final[str] = "#ffcccc"\n"""The placeholder shown where the canvas failed to start. App-owned."""\n\nCANVAS_FAILED_EDGE: Final[str] = "#ff0000"\n"""Its border. Was the CSS name `red`, which is this value. App-owned."""\n\nHISTORY_EXPORT_PAGE_BG: Final[str] = APP_WINDOW_LIGHT\n"""The exported history page\'s ground. Was #f5f5f5: linked."""\n\nHISTORY_EXPORT_CARD_BG: Final[str] = WHITE\n"""Each colour\'s card on that page. Was the CSS name `white`: linked."""\n\nHISTORY_EXPORT_INK: Final[str] = APP_BORDER_DARK\n"""The page\'s heading and the edge of each swatch. Was #333, twice, which\nis this value in three digits: linked."""\n\nSVG_EXPORT_BG: Final[str] = WHITE\n"""Paper for an exported palette: the SVG file and the image sheet. The\nname rnv-color-picker and rnv-color-palette-manager give the same job.\nWas #ffffff in one and the CSS name `white` in the other: linked."""\n\nSVG_EXPORT_STROKE: Final[str] = TRUE_BLACK\n"""The edge of a swatch in the exported SVG. Was #000000: linked."""\n\nCANVAS_PREVIEW_EDGE_DARK: Final[str] = "#e6e6e6"\n"""The edge of the canvas\'s colour preview in dark. Was QColor(230, 230,\n230). In light the edge is TRUE_BLACK. App-owned."""\n')
    tree.sub('utils/config.py',
             "    DARK_THEME = {\n        'name': 'Dark',\n        'window_bg': TRUE_BLACK,\n        'text_color': APP_TEXT_DARK,\n        'border_color': APP_BORDER_DARK,\n        'hover_color': APP_CHROME_DARK,\n        'main_btn_bg': APP_SURFACE_DARK,\n        'main_btn_text': APP_TEXT_DARK,\n        'main_btn_hover_bg': APP_BORDER_DARK,\n        'main_btn_pressed_bg': BRAND_GOLD_PRESSED,\n        'main_btn_pressed_text': TRUE_BLACK,\n        'main_btn_pressed_border': BRAND_GOLD,\n        # The plate, hover and pressed a DIALOG button takes. Added\n        # 2026-09-01, holding what the three dialogs already painted.\n        # Before this they read the main family, which is how a gold\n        # pressed plate that only a QDialog ever used came to look\n        # like the main window's.\n        'dialog_btn_bg': APP_SURFACE_DARK,\n        'dialog_btn_hover_bg': APP_BORDER_DARK,\n",
             "    DARK_THEME = {\n        'name': 'Dark',\n        'window_bg': TRUE_BLACK,\n        'text_color': APP_TEXT_DARK,\n        'border_color': APP_BORDER_DARK,\n        'hover_color': APP_CHROME_DARK,\n        'main_btn_bg': APP_SURFACE_DARK,\n        'main_btn_text': APP_TEXT_DARK,\n        'main_btn_hover_bg': APP_BORDER_DARK,\n        'main_btn_pressed_text': TRUE_BLACK,\n        # The hover and pressed a DIALOG button takes. Added\n        # 2026-09-01, holding what the three dialogs already painted.\n        # Before this they read the main family, which is how a gold\n        # pressed plate that only a QDialog ever used came to look\n        # like the main window's.\n        # RNV-NAMED-AND-USED (2026-10-04): the hover is read in dark\n        # alone -- the About dialog's tabs, from this palette by name\n        # -- so this palette alone holds it. dialog_btn_bg, which only\n        # light reads, is in LIGHT_THEME alone: a dark dialog's button\n        # takes panel_secondary.\n        'dialog_btn_hover_bg': APP_BORDER_DARK,\n")
    tree.sub('utils/config.py',
             "        'main_btn_hover_bg': APP_BTN_HOVER_INVERSE,\n        'main_btn_pressed_bg': BRAND_DARK_GOLD_PRESSED,\n        'main_btn_pressed_text': WHITE,\n        'main_btn_pressed_border': BRAND_DARK_GOLD,\n        # The plate, hover and pressed a DIALOG button takes. Added\n        # 2026-09-01, holding what the three dialogs already painted.\n        # Before this they read the main family, which is how a gold\n        # pressed plate that only a QDialog ever used came to look\n        # like the main window's.\n        'dialog_btn_bg': WHITE,\n        'dialog_btn_hover_bg': APP_BTN_HOVER_INVERSE,\n",
             "        'main_btn_hover_bg': APP_BTN_HOVER_INVERSE,\n        'main_btn_pressed_text': WHITE,\n        # The plate and pressed a DIALOG button takes. Added\n        # 2026-09-01, holding what the three dialogs already painted.\n        # Before this they read the main family, which is how a gold\n        # pressed plate that only a QDialog ever used came to look\n        # like the main window's.\n        # RNV-NAMED-AND-USED (2026-10-04): the plate is read in light\n        # alone, from this palette by name, so this palette alone\n        # holds it. dialog_btn_hover_bg, which only dark reads, is in\n        # DARK_THEME alone.\n        'dialog_btn_bg': WHITE,\n")
    tree.sub('utils/config.py',
             "    # NEW: Image Theme - Copy of Dark Theme for Image Mode\n    IMAGE_THEME = {\n        'name': 'Image',\n        'window_bg': TRUE_BLACK,\n        'text_color': APP_TEXT_DARK,\n        'border_color': APP_BORDER_DARK,\n        'hover_color': APP_CHROME_DARK,\n        'main_btn_bg': APP_SURFACE_DARK,\n        'main_btn_text': APP_TEXT_DARK,\n        'main_btn_hover_bg': APP_BORDER_DARK,\n        'main_btn_pressed_bg': BRAND_GOLD_PRESSED,\n        'main_btn_pressed_text': TRUE_BLACK,\n        'main_btn_pressed_border': BRAND_GOLD,\n        # The plate, hover and pressed a DIALOG button takes. Added\n        # 2026-09-01, holding what the three dialogs already painted.\n        # Before this they read the main family, which is how a gold\n        # pressed plate that only a QDialog ever used came to look\n        # like the main window's.\n        'dialog_btn_bg': APP_SURFACE_DARK,\n        'dialog_btn_hover_bg': APP_BORDER_DARK,\n        'dialog_btn_pressed_bg': BRAND_GOLD_PRESSED,\n        'canvas_bg': APP_CANVAS_DARK,\n        'scroll_area_bg': TRUE_BLACK,\n        'input_bg': APP_SURFACE_DARK,\n        'input_text': APP_TEXT_DARK,\n        'slot_border': APP_TEXT_DARK,\n        'slot_border_width': 2,\n        'tooltip_bg': APP_CARD_DARK,\n        'tooltip_border': BRAND_GOLD,\n        'text_disabled': APP_CONTROL_DIM,\n        'accent': BRAND_GOLD,\n        'accent_ink': BRAND_GOLD,\n        'accent_hover': BRAND_GOLD_HOVER,\n        'accent_text': TRUE_BLACK,\n        'panel_bg': APP_SURFACE_DARK,\n        'panel_secondary': APP_CARD_DARK,\n        'panel_hover': APP_PANEL_HOVER_DARK,\n        'tab_selected_bg': APP_CANVAS_DARK,\n        'scrollbar_bg': APP_SURFACE_DARK,\n        'scrollbar_handle': APP_BORDER_DARK,\n        'scrollbar_hover': BRAND_GOLD,\n        'slider_handle': APP_TEXT_DARK,\n        'text_hint': APP_HINT_DARK,\n        'menu_disabled': APP_MENU_DIM_DARK,\n        # One key for the slider groove. Before this pass three files painted\n        # it from three different keys -- panel_bg, hover_color and input_bg --\n        # and in dark two of those resolved to the panel's own colour, so the\n        # groove did not exist. RNV-MIXER-WIRING (2026-09-06).\n        'slider_groove': APP_CHROME_DARK,\n        # The menu's border and separator. The dark and light branches of\n        # core/color_slot.py painted these from different keys -- hover_color\n        # and border_color -- so the same two parts had no shared name. Values\n        # unchanged; the difference between the modes is now a value, not a key.\n        'menu_edge': APP_CHROME_DARK,\n        # The label while the main button is hovered. RULED, not chosen: see\n        # claude/ruling-interaction-contrast.md -- the transient states of this\n        # button are exempt from the 4.5 floor and the label dims on purpose.\n        # It held the resting label by inheritance in one file and by an\n        # explicit line in another; this states it once, at the same value.\n        'main_btn_hover_text': APP_TEXT_DARK,\n    }\n    \n",
             "    # Image Theme: the dark palette, under its own name.\n    # RNV-NAMED-AND-USED (2026-10-04): this was a written copy of\n    # DARK_THEME, the same forty keys at the same forty values bar the\n    # name. Image mode's dialogs never read it -- they draw from DARK_THEME\n    # by name -- so much of the copy was a second spelling of values nothing\n    # read. It is dark's values now, so nothing is written twice and a key\n    # image mode looks up is always there. A value image mode is ruled to\n    # draw differently goes after the spread.\n    IMAGE_THEME = {**DARK_THEME, 'name': 'Image'}\n    \n")
    tree.sub('RNV_Color_Mixer.py',
             '            placeholder.setStyleSheet("background-color: #ffcccc; border: 2px solid red;")\n',
             '            # RNV-NAMED-AND-USED (2026-10-04): was #ffcccc and the CSS name red.\n            placeholder.setStyleSheet(\n                f"background-color: {config.CANVAS_FAILED_BG}; border: 2px solid {config.CANVAS_FAILED_EDGE};")\n')
    tree.sub('RNV_Color_Mixer.py',
             '            for i in range(len(slots_data), len(self.slots)):\n                self.slots[i].set_color((200, 200, 200))\n',
             '            for i in range(len(slots_data), len(self.slots)):\n                self.slots[i].set_color(config.DEFAULT_COLOR)\n')
    tree.sub('RNV_Color_Mixer.py',
             "                    'color': list(slot.get_color()) if slot.get_color() else [200, 200, 200],\n",
             "                    'color': list(slot.get_color()) if slot.get_color() else list(config.DEFAULT_COLOR),\n")
    tree.sub('RNV_Color_Mixer.py',
             "                    color = tuple(slot_info.get('color', [200, 200, 200]))\n",
             "                    color = tuple(slot_info.get('color', config.DEFAULT_COLOR))\n")
    tree.sub('RNV_Color_Mixer.py',
             "                color = tuple(slot_data.get('color', [200, 200, 200]))\n",
             "                color = tuple(slot_data.get('color', config.DEFAULT_COLOR))\n")
    tree.sub('RNV_Color_Mixer.py',
             '                self.current_rgb = config.INITIAL_COLOR_RGB\n                self._update_preview((0, 0, 0))\n',
             '                self.current_rgb = config.INITIAL_COLOR_RGB\n                self._update_preview(config.INITIAL_COLOR_TUPLE)\n')
    tree.sub('RNV_Color_Mixer.py',
             '            if not color:\n                color_to_use = (0, 0, 0)\n',
             '            if not color:\n                color_to_use = config.INITIAL_COLOR_TUPLE\n')
    tree.sub('RNV_Color_Mixer.py',
             '            text_color = "white" if brightness < 128 else "black"\n',
             '            # RNV-NAMED-AND-USED (2026-10-04): were the CSS names white and black.\n            text_color = config.WHITE if brightness < 128 else config.TRUE_BLACK\n')
    tree.sub('RNV_Color_Mixer.py',
             '            img = Image.new("RGB", (800, 600), "white")\n',
             '            img = Image.new("RGB", (800, 600), config.SVG_EXPORT_BG)\n')
    tree.sub('core/color_slot.py',
             '        self.color = (200, 200, 200)\n        self._weight = 0\n        self.is_dark = True\n',
             "        # RNV-NAMED-AND-USED (2026-10-04): config.DEFAULT_COLOR is this\n        # colour's name. Nothing read it; it was written out here five times.\n        self.color = config.DEFAULT_COLOR\n        self._weight = 0\n        self.is_dark = True\n")
    tree.sub('core/color_slot.py',
             '        self._color_history = [(200, 200, 200)]  # Initial color\n',
             '        self._color_history = [config.DEFAULT_COLOR]  # Initial color\n')
    tree.sub('core/color_slot.py',
             '        self.color = (200, 200, 200)\n        self._weight = 0\n        self.weight_slider.setValue(0)\n        \n        # Reset history\n        self._color_history = [(200, 200, 200)]\n',
             '        self.color = config.DEFAULT_COLOR\n        self._weight = 0\n        self.weight_slider.setValue(0)\n        \n        # Reset history\n        self._color_history = [config.DEFAULT_COLOR]\n')
    tree.sub('core/color_slot.py',
             '        self.set_color((200, 200, 200))\n',
             '        self.set_color(config.DEFAULT_COLOR)\n')
    tree.sub('core/color_history.py',
             'from core.color_math import ColorMath\n',
             'from core.color_math import ColorMath\nfrom utils import config\n')
    tree.sub('core/color_history.py',
             '                f.write("body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }\\n")\n                f.write(".color { display: flex; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }\\n")\n                f.write(".swatch { width: 60px; height: 40px; border: 2px solid #333; margin-right: 15px; border-radius: 3px; }\\n")\n                f.write(".info { flex: 1; }\\n")\n                f.write("h1 { color: #333; }\\n")\n',
             '                # RNV-NAMED-AND-USED (2026-10-04): the page\'s four colours, by\n                # name. They were #f5f5f5, white, #333 and #333; the same colours.\n                f.write(f"body {{ font-family: Arial, sans-serif; padding: 20px; background: {config.HISTORY_EXPORT_PAGE_BG}; }}\\n")\n                f.write(f".color {{ display: flex; align-items: center; margin: 10px 0; padding: 10px; background: {config.HISTORY_EXPORT_CARD_BG}; border-radius: 5px; }}\\n")\n                f.write(f".swatch {{ width: 60px; height: 40px; border: 2px solid {config.HISTORY_EXPORT_INK}; margin-right: 15px; border-radius: 3px; }}\\n")\n                f.write(".info { flex: 1; }\\n")\n                f.write(f"h1 {{ color: {config.HISTORY_EXPORT_INK}; }}\\n")\n')
    tree.sub('core/palette_formats.py',
             'from core.color_math import ColorMath\n',
             'from core.color_math import ColorMath\nfrom utils import config\n')
    tree.sub('core/palette_formats.py',
             '            f.write(\'  <rect width="100%" height="100%" fill="#ffffff"/>\\n\')\n',
             '            # RNV-NAMED-AND-USED (2026-10-04): paper, edge and the two inks by\n            # name. They were #ffffff, #000000, #ffffff and #000000.\n            f.write(f\'  <rect width="100%" height="100%" fill="{config.SVG_EXPORT_BG}"/>\\n\')\n')
    tree.sub('core/palette_formats.py',
             '                f.write(f\'fill="{hex_color}" stroke="#000000" stroke-width="1"/>\\n\')\n',
             '                f.write(f\'fill="{hex_color}" stroke="{config.SVG_EXPORT_STROKE}" stroke-width="1"/>\\n\')\n')
    tree.sub('core/palette_formats.py',
             '                text_color = "#ffffff" if brightness < 128 else "#000000"\n',
             '                text_color = config.WHITE if brightness < 128 else config.TRUE_BLACK\n')
    tree.sub('core/package_d_panel.py',
             '        self.debug_overlay_panel = DebugOverlay(self, "Package D Panel", "rgba(80, 255, 80, 220)")\n',
             '        self.debug_overlay_panel = DebugOverlay(self, "Package D Panel", config.DEBUG_OVERLAY_COLORS[\'panel\'])\n')
    tree.sub('core/package_d_panel.py',
             '        self.debug_overlay_tabs = DebugOverlay(self.tabs, "Tabs Widget", "rgba(255, 200, 80, 220)")\n',
             '        self.debug_overlay_tabs = DebugOverlay(self.tabs, "Tabs Widget", config.DEBUG_OVERLAY_COLORS[\'tabs\'])\n')
    tree.sub('ui/debug_overlay.py',
             'from utils.signal_manager import SignalMixin\n',
             "from utils.signal_manager import SignalMixin\n# RNV-NAMED-AND-USED (2026-10-04): an overlay's tint, text and edge are\n# named in config.DEBUG_OVERLAY_COLORS. They were written out in this file.\nfrom utils import config\n")
    tree.sub('ui/debug_overlay.py',
             'label_text: str = "Debug", color: str = "rgba(255, 100, 100, 200)") -> None:\n',
             'label_text: str = "Debug", color: str = config.DEBUG_OVERLAY_COLORS[\'default\']) -> None:\n', times=2)
    tree.sub('ui/debug_overlay.py',
             '                color: white;\n',
             "                color: {config.DEBUG_OVERLAY_COLORS['text']};\n", times=2)
    tree.sub('ui/debug_overlay.py',
             '                border: 2px solid rgba(255, 255, 255, 230);\n',
             "                border: 2px solid {config.DEBUG_OVERLAY_COLORS['edge']};\n", times=2)
    tree.sub('ui/canvas_view.py',
             "                        corner_color = QColor(theme['accent'])\n                        text_color = QColor(255, 255, 255)\n",
             "                        corner_color = QColor(theme['accent'])\n                        # RNV-NAMED-AND-USED (2026-10-04): the labels this\n                        # view paints took QColor() built from numbers; each\n                        # is the same colour, by its name in config.\n                        text_color = QColor(config.WHITE)\n")
    tree.sub('ui/canvas_view.py',
             '                        corner_color = QColor(_accent)\n                        text_color = QColor(0, 0, 0)\n',
             '                        corner_color = QColor(_accent)\n                        text_color = QColor(config.TRUE_BLACK)\n')
    tree.sub('ui/canvas_view.py',
             '                            painter.fillRect(bg_rect, QColor(0, 0, 0, 180))\n                        else:\n                            painter.fillRect(bg_rect, QColor(200, 200, 200, 180))\n',
             '                            painter.fillRect(bg_rect, QColor(config.translucent(\n                                config.TRUE_BLACK, config.CANVAS_LABEL_ALPHA)))\n                        else:\n                            painter.fillRect(bg_rect, QColor(200, 200, 200, 180))\n')
    tree.sub('ui/canvas_view.py',
             '                bg_color = QColor(0, 0, 0, 200)\n                border_color = QColor(230, 230, 230)\n            else:\n                bg_color = QColor(255, 255, 255, 200)\n                border_color = QColor(0, 0, 0)\n',
             '                bg_color = QColor(config.translucent(config.TRUE_BLACK, config.CANVAS_PREVIEW_ALPHA))\n                border_color = QColor(config.CANVAS_PREVIEW_EDGE_DARK)\n            else:\n                bg_color = QColor(config.translucent(config.WHITE, config.CANVAS_PREVIEW_ALPHA))\n                border_color = QColor(config.TRUE_BLACK)\n')
    tree.sub('ui/canvas_view.py',
             '                shadow_pen = QPen(QColor(255, 255, 255), 1)\n                text_color = QColor(0, 0, 0)\n            else:\n                shadow_pen = QPen(QColor(0, 0, 0), 1)\n                text_color = QColor(255, 255, 255)\n',
             '                shadow_pen = QPen(QColor(config.WHITE), 1)\n                text_color = QColor(config.TRUE_BLACK)\n            else:\n                shadow_pen = QPen(QColor(config.TRUE_BLACK), 1)\n                text_color = QColor(config.WHITE)\n')
    tree.sub('test_rnv_color_mixer.py',
             '    # ── All three themes must have identical key sets ─────────────────────────\n    def test_all_themes_same_keys(self):\n        dk=set(self.tm.DARK_THEME.keys())\n        lk=set(self.tm.LIGHT_THEME.keys())\n        ik=set(self.tm.IMAGE_THEME.keys())\n        self.assertEqual(dk,lk,\n            f"DARK vs LIGHT key mismatch: {dk.symmetric_difference(lk)}")\n        self.assertEqual(dk,ik,\n            f"DARK vs IMAGE key mismatch: {dk.symmetric_difference(ik)}")\n',
             '    # ── The themes hold the same keys, bar the two a single mode reads ────────\n    def test_all_themes_same_keys(self):\n        dk=set(self.tm.DARK_THEME.keys())\n        lk=set(self.tm.LIGHT_THEME.keys())\n        ik=set(self.tm.IMAGE_THEME.keys())\n        # RNV-NAMED-AND-USED 2026-10-04: a key only one mode reads is in that\n        # mode\'s palette alone; its other half was a value nothing showed.\n        # Dark\'s dialogs alone read dialog_btn_hover_bg and light\'s alone read\n        # dialog_btn_bg, each from its own palette by name.\n        self.assertEqual(dk-lk,{"dialog_btn_hover_bg"},\n            f"keys only DARK holds: {dk-lk}")\n        self.assertEqual(lk-dk,{"dialog_btn_bg"},\n            f"keys only LIGHT holds: {lk-dk}")\n        self.assertEqual(dk,ik,\n            f"DARK vs IMAGE key mismatch: {dk.symmetric_difference(ik)}")\n')
    tree.sub('.github/workflows/tests-linux.yml',
             "        # digest below is that file's, and tests/test_locked_file_\n        # digest.py now checks it in the suite as well as here.\n",
             "        # digest below is that file's, and tests/test_locked_file_\n        # digest.py now checks it in the suite as well as here.\n        # RNV-NAMED-AND-USED 2026-10-04: re-baselined. Ruled: the\n        # same-keys test may change so that a palette holds no value\n        # its mode never reads. One test moved; the digest is its file's.\n")
    tree.sub('.github/workflows/tests-linux.yml',
             "          expected = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd'\n",
             "          expected = 'e00c2424a8c64affdaf67547e59c633e7958427ad26f0186253ae599fb992edb'\n")
    tree.sub('.github/workflows/tests-windows.yml',
             "e='0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd';",
             "e='e00c2424a8c64affdaf67547e59c633e7958427ad26f0186253ae599fb992edb';")
    tree.sub('tests/test_app_mirror.py',
             'def test_image_mode_carries_the_same_ink():\n    """IMAGE_THEME is a separate literal block here, not a spread of DARK, so\n    the move has to be made twice and asserted twice."""\n    node = _dict_node(\'IMAGE_THEME\')\n    literals = []\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if not (isinstance(value, ast.Name) and value.id == \'APP_TEXT_DARK\'):\n            literals.append(\n                f\'{key} = {ast.unparse(value) if value is not None else "missing"}\')\n    assert not literals, (\'image ink still written as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n',
             'def test_image_mode_carries_the_same_ink():\n    """IMAGE_THEME is the dark palette under its own name -- `{**DARK_THEME,\n    \'name\': \'Image\'}` since RNV-NAMED-AND-USED, 2026-10-04 -- so the ink\n    arrives through the spread and the move is made once. Asserted all the\n    same: the spread is of DARK_THEME, an ink written after it is still the\n    constant, and the palette the application reads resolves to it."""\n    node = _dict_node(\'IMAGE_THEME\')\n    spreads = [ast.unparse(v) for k, v in zip(node.keys, node.values) if k is None]\n    assert spreads == [\'DARK_THEME\'], (\n        f\'IMAGE_THEME spreads {spreads}, not the dark palette alone\')\n    literals = []\n    for key in INK_KEYS:\n        value = _entry(node, key)\n        if value is not None and not (isinstance(value, ast.Name)\n                                      and value.id == \'APP_TEXT_DARK\'):\n            literals.append(f\'{key} = {ast.unparse(value)}\')\n    assert not literals, (\'image ink written over the spread as literals:\\n  \'\n                          + \'\\n  \'.join(literals))\n')
    tree.sub('tests/test_app_mirror.py',
             'def test_the_handle_hover_is_still_one_step_above_the_text():\n    """APP_HANDLE_HOVER_DARK is documented as \'one step above the text\'. That\n    sentence was true of #f0f0f0 above #e0e0e0 only by accident -- the gap was\n    0x10, not a grid step. Both are on the grid now and the relationship is\n    asserted rather than described."""\n    assert colors.APP_HANDLE_HOVER_DARK == grey(14) == \'#eeeeee\'\n    assert colors.APP_HANDLE_HOVER_DARK == grey(\n        (int(colors.APP_TEXT_DARK[1:3], 16) // GRID_STEP) + 1)\n',
             "# RNV-NAMED-AND-USED, 2026-10-04: a test stood here for a name one grid step\n# above the text, the dark slider handle's hover. No sheet painted that name:\n# a hovered handle takes the accent. The name went, and its test with it.\n")
    tree.sub('tests/test_brand_mirror.py',
             'GOLD_KEYS = ("accent", "accent_hover", "accent_ink", "tooltip_border",\n             "scrollbar_hover", "main_btn_pressed_bg", "main_btn_pressed_border")\n',
             '# RNV-NAMED-AND-USED, 2026-10-04: the pressed fill is dialog_btn_pressed_bg,\n# the key the control panel presses to. Two main-window keys stood here that\n# no sheet read; they went from the palettes.\nGOLD_KEYS = ("accent", "accent_hover", "accent_ink", "tooltip_border",\n             "scrollbar_hover", "dialog_btn_pressed_bg")\n')
    tree.sub('tests/test_brand_mirror.py',
             '    for name, palette in PALETTES.items():\n        assert palette["main_btn_pressed_bg"] == palette["accent"], name\n',
             '    for name, palette in PALETTES.items():\n        assert palette["dialog_btn_pressed_bg"] == palette["accent"], name\n')
    tree.sub('tests/test_button_key_names.py',
             'NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)\nDIALOG = ("dialog_btn_bg", "dialog_btn_hover_bg", "dialog_btn_pressed_bg")\n\nPINNED_MAIN = {\n    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n             "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",\n             "main_btn_pressed_text": "#000000",\n             "main_btn_pressed_border": "#d2bc93"},\n    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",\n              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#8c7337",\n              "main_btn_pressed_text": "#ffffff",\n              "main_btn_pressed_border": "#8c7337"},\n    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",\n              "main_btn_pressed_text": "#000000",\n              "main_btn_pressed_border": "#d2bc93"},\n}\n\n#: What the three dialogs painted before the rename, key for key.\nPINNED_DIALOG = {\n    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",\n             "dialog_btn_pressed_bg": "#d2bc93"},\n    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_hover_bg": "#333333",\n              "dialog_btn_pressed_bg": "#8c7337"},\n    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",\n              "dialog_btn_pressed_bg": "#d2bc93"},\n}\n',
             '#: RNV-NAMED-AND-USED, 2026-10-04: the families as the application reads\n#: them. The rename carried six names across. The main window reads four;\n#: the other two went with the ruling that a palette holds what is used. A\n#: dialog key one mode alone reads is in that mode\'s palette alone: the\n#: About dialog\'s tabs hover to dialog_btn_hover_bg in dark, a light dialog\'s\n#: button rests on dialog_btn_bg, and the control panel presses to\n#: dialog_btn_pressed_bg in every mode. Image mode is the dark palette under\n#: its own name.\nNEW = ("main_btn_bg", "main_btn_text", "main_btn_hover_bg",\n       "main_btn_pressed_text")\nDIALOG = {\n    "dark": ("dialog_btn_hover_bg", "dialog_btn_pressed_bg"),\n    "light": ("dialog_btn_bg", "dialog_btn_pressed_bg"),\n    "image": ("dialog_btn_hover_bg", "dialog_btn_pressed_bg"),\n}\n\nPINNED_MAIN = {\n    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n             "main_btn_hover_bg": "#333333",\n             "main_btn_pressed_text": "#000000"},\n    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",\n              "main_btn_hover_bg": "#333333",\n              "main_btn_pressed_text": "#ffffff"},\n    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",\n              "main_btn_hover_bg": "#333333",\n              "main_btn_pressed_text": "#000000"},\n}\n\n#: What the three dialogs painted before the rename, key for key.\nPINNED_DIALOG = {\n    "dark": {"dialog_btn_hover_bg": "#333333",\n             "dialog_btn_pressed_bg": "#d2bc93"},\n    "light": {"dialog_btn_bg": "#ffffff",\n              "dialog_btn_pressed_bg": "#8c7337"},\n    "image": {"dialog_btn_hover_bg": "#333333",\n              "dialog_btn_pressed_bg": "#d2bc93"},\n}\n')
    tree.sub('tests/test_button_key_names.py',
             '        missing = [n for n in NEW + DIALOG if n not in palette]\n',
             '        missing = [n for n in NEW + DIALOG[mode] if n not in palette]\n')
    tree.sub('tests/test_contrast_pairs.py',
             '    light = config.ThemeManager.LIGHT_THEME\n    assert light["main_btn_pressed_bg"] == light["accent"] == config.BRAND_DARK_GOLD\n',
             '    # RNV-NAMED-AND-USED, 2026-10-04: read from dialog_btn_pressed_bg, the key\n    # a dialog fills from. This read a main-window key that no sheet used.\n    light = config.ThemeManager.LIGHT_THEME\n    assert light["dialog_btn_pressed_bg"] == light["accent"] == config.BRAND_DARK_GOLD\n')
    tree.sub('tests/test_contrast_pairs.py',
             '        assert palette["main_btn_pressed_bg"] == palette["accent"] == config.BRAND_GOLD\n',
             '        assert palette["dialog_btn_pressed_bg"] == palette["accent"] == config.BRAND_GOLD\n')
    tree.sub('tests/test_derived_values.py',
             '#: Found when this was written; below a floor, the sweep has gone blind.\nLOWER8_FLOOR = 5\nLOWER8_FILES = 32\nLOWER8_NAMED = 21\n',
             "#: Found when this was written; below a floor, the sweep has gone blind.\n#: RNV-NAMED-AND-USED, 2026-10-04: three of the canvas's plates are built\n#: by translucent() now, and three colours the code spelled out have names\n#: with a value of their own.\nLOWER8_FLOOR = 8\nLOWER8_FILES = 32\nLOWER8_NAMED = 24\n")
    tree.sub('tests/test_ladder_and_plate.py',
             '"""Three neutrals reclassified from app-owned to mirrored, and one deliberate\ncoincidence that must not join them.\n',
             '"""Three neutrals reclassified from app-owned to mirrored.\n')
    tree.sub('tests/test_ladder_and_plate.py',
             'THE COINCIDENCE. APP_HANDLE_HOVER_DARK is also #eeeeee. It is the dark slider\nhandle when hovered -- grey(14) on the ink grid, one step above APP_TEXT_DARK\nat grey(13), doing an ink job in a dark palette. APP["hover-light"] is a LIGHT\nSURFACE. grey(14) is reachable from both families, which is the sort of\ncoincidence a published grid makes possible, and it must be named rather than\nnoticed.\n"""\n',
             'THE COINCIDENCE THAT WENT. Until RNV-NAMED-AND-USED, 2026-10-04, a second\nname held #eeeeee here: the dark slider handle\'s hover, grey(14) on the ink\ngrid, kept apart from APP["hover-light"] by a table and three tests in this\nfile. No sheet painted that name -- a hovered handle takes the accent -- so\nit went, and the plate\'s hex has one name again. With nothing left to keep\napart, the table and its tests went with it.\n"""\n')
    tree.sub('tests/test_ladder_and_plate.py',
             '#: App-owned values that DELIBERATELY share a hex with a register entry.\n#: Sharing a VALUE is not playing the same ROLE, and a value check cannot tell\n#: the difference -- so the intentional ones are named here, with what they\n#: share and why they must NOT follow if the register moves.\n#:\n#: name -> (register key, why it is not the same role)\nCOINCIDENT = {\n    \'APP_HANDLE_HOVER_DARK\': (\n        \'hover-light\',\n        \'Both are #eeeeee. The register entry is a LIGHT SURFACE -- the \'\n        \'interaction plate a light-mode control hovers to. This is the DARK \'\n        \'slider handle when hovered: an ink-grid step, grey(14), one above \'\n        \'APP_TEXT_DARK at grey(13), drawn on a dark ground. Different mode, \'\n        \'different family, different job. grey(14) is simply reachable from \'\n        \'both. If APP["hover-light"] moves off grey(14) this must NOT follow \'\n        \'it, which is why it is named here rather than mirrored.\'),\n}\n\n',
             '')
    tree.sub('tests/test_ladder_and_plate.py',
             '    for name in list(NEW) + list(COINCIDENT):\n',
             '    for name in NEW:\n')
    tree.sub('tests/test_ladder_and_plate.py',
             '\n\n# -------------------------------------------------------------- the coincidence\n\ndef test_every_coincidence_still_coincides():\n    """A named coincidence that no longer shares a value is a dead exemption,\n    and a dead exemption is a licence waiting for a defect: it would let a\n    genuinely misclassified value hide behind it."""\n    brand = pytest.importorskip(\'engine.brand\', reason=\'rnv-brand not importable\')\n    stale = []\n    for name, (key, _why) in COINCIDENT.items():\n        mine = getattr(config, name).lower()\n        theirs = brand.APP.get(key)\n        if theirs is None:\n            stale.append(f\'{name}: the register no longer holds APP[{key!r}]\')\n        elif mine != theirs.lower():\n            stale.append(f\'{name} = {mine} no longer matches APP[{key!r}] {theirs}\')\n    assert not stale, (\n        \'COINCIDENT entries that no longer describe reality:\\n  \'\n        + \'\\n  \'.join(stale)\n        + \'\\n\\nDelete the entry or correct it -- do not leave it standing.\')\n\n\ndef test_no_coincidence_is_also_mirrored():\n    """Guard the guard. The exemption is only for app-owned values; a name in\n    both tables would quietly exempt a mirrored value from its own mirror."""\n    for name in COINCIDENT:\n        assert name not in NEW, f\'{name} is both mirrored and exempt from the mirror\'\n    mirror = pathlib.Path(__file__).with_name(\'test_app_mirror.py\')\n    source = mirror.read_text(encoding=\'utf-8\')\n    for name in COINCIDENT:\n        assert f"\'{name}\':" not in source, (\n            f\'{name} is a named coincidence and is also pinned in \'\n            f\'test_app_mirror.py. It cannot be both.\')\n\n\ndef test_the_coincidence_is_in_the_other_mode():\n    """What actually separates the two: one is a light surface, the other a\n    dark ink. If the handle hover ever appears in a light palette, the reason\n    it is exempt has gone."""\n    for dict_name in (\'LIGHT_THEME\',):\n        for key, value in PALETTES[dict_name].items():\n            assert value != config.APP_HANDLE_HOVER_DARK or \\\n                value == config.APP_ITEM_HOVER_LIGHT, (\n                    f\'{dict_name}[{key!r}] carries the dark handle hover\')\n',
             '')
    tree.sub('tests/test_mixer_wiring.py',
             "PALETTES = ['DARK_THEME', 'LIGHT_THEME', 'IMAGE_THEME']\n",
             "PALETTES = ['DARK_THEME', 'LIGHT_THEME', 'IMAGE_THEME']\n#: RNV-NAMED-AND-USED, 2026-10-04: a palette written as another one spread\n#: under its own name -> the palette it spreads.\nSPREADS = {'IMAGE_THEME': 'DARK_THEME'}\n")
    tree.sub('tests/test_mixer_wiring.py',
             '    \'#eeeeee\': {\'APP_HANDLE_HOVER_DARK\': \'a dark ink-grid step, app-owned\',\n                \'APP_ITEM_HOVER_LIGHT\': \'the light register plate APP["hover-light"]\'},\n',
             "    # RNV-NAMED-AND-USED, 2026-10-04: #eeeeee was declared here as a split, the\n    # light register plate and a dark slider handle's hover. Nothing painted the\n    # handle's name, so it went, and the plate's hex has one name again.\n")
    tree.sub('tests/test_mixer_wiring.py',
             'def _entries(d):\n    """(key, value) for the literal entries of a dict node, skipping any\n    `**OTHER` expansion, which ast records as a key of None."""\n    for k, v in zip(d.keys, d.values):\n        if k is None:\n            continue\n        yield ast.literal_eval(k), v\n',
             'def _entries(d):\n    """(key, value) for the literal entries of a dict node, skipping any\n    `**OTHER` expansion, which ast records as a key of None."""\n    for k, v in zip(d.keys, d.values):\n        if k is None:\n            continue\n        yield ast.literal_eval(k), v\n\n\ndef _spread(d):\n    """The names a dict node spreads: the `**OTHER` expansions _entries skips."""\n    return [ast.unparse(v) for k, v in zip(d.keys, d.values) if k is None]\n\n\ndef _keys(palette):\n    """The keys a palette holds: its own entries, and those of any palette it\n    spreads."""\n    d = _palette_dicts()[palette]\n    keys = {k for k, _ in _entries(d)}\n    for other in _spread(d):\n        keys |= _keys(other)\n    return keys\n')
    tree.sub('tests/test_mixer_wiring.py',
             '    for name, d in found.items():\n        assert len(list(_entries(d))) > 20, (\n',
             "    for name, d in found.items():\n        if name in SPREADS:\n            # RNV-NAMED-AND-USED, 2026-10-04: a palette that is another under\n            # its own name writes almost nothing, and is swept through the one\n            # it spreads. What it must do is spread that one and no other.\n            assert _spread(d) == [SPREADS[name]], (\n                f'{name} spreads {_spread(d)}, not {SPREADS[name]} alone')\n            continue\n        assert not _spread(d), (\n            f'{name} spreads {_spread(d)}; the sweep below reads literals')\n        assert len(list(_entries(d))) > 20, (\n")
    tree.sub('tests/test_mixer_wiring.py',
             "    for palette in PALETTES:\n        keys = {k for k, _ in _entries(_palette_dicts()[palette])}\n        assert key in keys, f'{palette} has no {key!r}'\n",
             "    for palette in PALETTES:\n        assert key in _keys(palette), f'{palette} has no {key!r}'\n")
    tree.sub('tests/test_mixer_wiring.py',
             "    d = dict(_entries(_palette_dicts()['LIGHT_THEME']))\n    for key in ('main_btn_hover_bg', 'dialog_btn_hover_bg'):\n",
             "    d = dict(_entries(_palette_dicts()['LIGHT_THEME']))\n    # RNV-NAMED-AND-USED, 2026-10-04: the main button's hover alone. The light\n    # palette held a dialog hover at the same alias and no light sheet read it:\n    # a light dialog's button hovers to panel_hover.\n    for key in ('main_btn_hover_bg',):\n")
    if (tree.root / 'tests/test_named_and_used.py').exists():
        raise Stop('tests/test_named_and_used.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_named_and_used.py', '"""\ntests/test_named_and_used.py\n============================\nRNV-NAMED-AND-USED, 2026-10-04. Every colour in the application is named,\nand every name is used.\n\nRuled 2026-10-04: "As long as a color exist in the app it should be named\nand used no hardcoded or pointless literals should exist, only literals with\na purpose, like data or comparison are allowed. Colors are name for swap\nability and alignment."\n\nIn this application that removed two palette keys no mode read, made the\nimage palette the dark palette under its own name instead of a written copy,\nkept each of the two dialog keys in the one palette whose mode reads it, and\nremoved three constants only tests held; and it named the canvas-failed\nplaceholder, the history export\'s page, the canvas\'s labels, the debug\noverlays, the empty-history line and the palette exports\' paper and ink.\n\nThree sweeps hold it, each over the application\'s own source:\n\n1. NAMED. No colour is written out in the code. Every spelling is read: hex,\n   rgb() and rgba(), a CSS colour name, QColor built from numbers, a Qt\n   global colour, a tuple or a list of channels, an alpha set as a number.\n   A colour is written once, in the colour module, under a name; everything\n   else reads the name. What stays written is DATA, each entry with its\n   reason, and the sweep fails for an entry that no longer matches anything.\n2. USED, the palettes. Every colour a palette holds is looked up by key\n   somewhere in the application.\n3. USED, the constants. Every colour the colour module names is read\n   somewhere in the application: by the palettes, by another constant, or by\n   the code.\n\nClear is not a colour: \'transparent\', alpha 0 and Qt\'s transparent are how a\nwidget is told to paint nothing, and are left as written.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport importlib\nimport pathlib\nimport re\n\nimport pytest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: Where this application writes its colours: the one place a literal belongs.\nCOLOUR_MODULES = ("utils/config.py",)\n#: Where its palettes are written: their own keys are not lookups.\nPALETTE_MODULES = COLOUR_MODULES\nSKIP_DIRS = {"tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__"}\n\nfrom utils.config import ThemeManager  # noqa: E402\n\nPALETTES = {"DARK_THEME": ThemeManager.DARK_THEME, "LIGHT_THEME": ThemeManager.LIGHT_THEME,\n            "IMAGE_THEME": ThemeManager.IMAGE_THEME}\n\n#: Below these a sweep has gone blind.\nMIN_FILES = 30\nMIN_ENTRIES = 100\nMIN_CONSTANTS = 30\n\n#: What stays written, and why: (file, literal) -> the reason. "*" covers a\n#: file that is a table of data. Data a person starts from, or an image is\n#: made of, is not the application\'s look, and a brand move should not change it.\nDATA = {\n    ("core/preset_palettes.py", "*"):\n        "the preset palettes: colours a person picks from, as data",\n    **{("core/package_d_panel.py", sample):\n       "a sample row for the History tab when the history module cannot be loaded: data"\n       for sample in ("#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33")},\n    ("core/color_fine_tune.py", "(200, 200, 200)"):\n        "the fine-tune dialog opened with no colour given: a default, as data",\n    ("core/color_math.py", "(0, 0, 0)"):\n        "what safe_rgb() hands back for channels it cannot use: a fallback, as data",\n    ("core/image_handler.py", "(255, 255, 255)"):\n        "the ground a loaded image\'s transparency is flattened onto: part of the image, not of the look",\n    ("core/screen_color_picker.py", "(0, 0, 0)"):\n        "the colour under the cursor before the first reading: where the picker starts",\n    ("core/screen_color_picker.py", "#000000"):\n        "the same starting colour, as the readout\'s text",\n    ("core/screen_color_picker.py", "QColor(0, 0, 0)"):\n        "the same starting colour, as the readout\'s swatch",\n    ("core/screen_color_picker.py", "Qt.GlobalColor.black"):\n        "the gaps between monitors in the captured desktop: part of the screenshot, not of the look",\n    ("ui/canvas_view.py", "(0, 0, 0)"):\n        "the canvas preview\'s colour before a pixel is hovered: where it starts",\n    ("utils/settings_manager.py", "[200, 200, 200]"):\n        "the stored default of a preference, default_slot_color: data in the settings file, not the look",\n    ("core/package_d_panel.py", "QColor(128, 128, 128)"):\n        "HELD, and not data. Set on the empty-history line\'s item and never drawn: the list\'s stylesheet "\n        "colours every item, and the sheet wins. Proven 2026-10-04 with a magenta control. A ruling is "\n        "asked: draw the line in the muted text, or drop the call",\n    ("ui/canvas_view.py", "QColor(200, 200, 200, 180)"):\n        "HELD, and not data. The light plate behind a dragged selection\'s size, never drawn: the view asks "\n        "a theme manager of its own, which always answers dark, so its light branch never runs. Proven "\n        "2026-10-04 with a magenta control. A ruling is asked: make the canvas follow the mode, or drop "\n        "the branch",\n}\n\nCSS_NAMES = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue\nblueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue\ndarkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid\ndarkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink\ndeepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold\ngoldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush\nlawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey\nlightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime\nlimegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen\nmediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin\nnavajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise\npalevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue\nsaddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow\nspringgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow\nyellowgreen""".split())\nQT_GLOBAL = frozenset({"white", "black", "red", "darkRed", "green", "darkGreen", "blue", "darkBlue", "cyan",\n                       "darkCyan", "magenta", "darkMagenta", "yellow", "darkYellow", "gray", "darkGray",\n                       "lightGray"})\nHEX = re.compile(r"(?<![\\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])")\nFUNC = re.compile(r"\\b(?:rgba?|hsla?|hsva?)\\(\\s*[0-9.]+%?\\s*,[^)]*\\)", re.I)\nPROP = re.compile(r"(?:^|[;{\\s\\"\'])((?:[a-z-]*color|background(?:-color)?|border(?:-[a-z]+)*|outline(?:-[a-z]+)*|"\n                  r"fill|stroke))\\s*[:=]\\s*([^;{}<>]*)", re.I)\nWORD = re.compile(r"(?<![\\w#.-])([a-z]+)(?![\\w(-])", re.I)\nNOT_A_COLOUR = re.compile(r"margin|padding|spacing|size|offset|geometry|rect|pos|range|version|ratio|weight", re.I)\nA_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})|rgba?\\([^)]*\\)")\n\n\ndef _sources():\n    """(repo-relative path, text) of every file of the application: not the\n    tests, not a delivery script, not what a build leaves behind."""\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT).as_posix()\n        parts = rel.split("/")\n        if any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1]):\n            continue\n        if len(parts) == 1 and (parts[0].startswith(("test_", "up", "conftest", "run_tests"))):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, text\n\n\ndef _prose(tree) -> set:\n    """ids of the strings that are prose: docstrings and bare string statements."""\n    return {id(n.value) for n in ast.walk(tree)\n            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}\n\n\ndef _clear(literal: str) -> bool:\n    """rgba(..., 0) and QColor(..., 0): clear, not a colour."""\n    nums = re.findall(r"[0-9.]+", literal)\n    return len(nums) == 4 and float(nums[3]) == 0\n\n\ndef _written(rel: str, text: str) -> list:\n    """(line, kind, literal) for every colour this file writes out."""\n    tree = ast.parse(text)\n    prose, out = _prose(tree), []\n    parent = {}\n    for node in ast.walk(tree):\n        for child in ast.iter_child_nodes(node):\n            parent[id(child)] = node\n\n    def named_like(node) -> str:\n        """The name a value is given: its assignment target, keyword or parameter."""\n        up = parent.get(id(node))\n        while isinstance(up, (ast.IfExp, ast.BoolOp, ast.Tuple, ast.List)):\n            node, up = up, parent.get(id(up))\n        if isinstance(up, ast.keyword):\n            return up.arg or ""\n        if isinstance(up, (ast.Assign, ast.AnnAssign)):\n            target = up.targets[0] if isinstance(up, ast.Assign) else up.target\n            return ast.unparse(target)\n        if isinstance(up, ast.arguments):\n            both = up.posonlyargs + up.args\n            if node in up.defaults:\n                return both[len(both) - len(up.defaults) + up.defaults.index(node)].arg\n            if node in up.kw_defaults:\n                return up.kwonlyargs[up.kw_defaults.index(node)].arg\n        return ""\n\n    def a_name_on_its_own(node, up) -> bool:\n        """A CSS colour name that is the whole string, where a colour is given:\n        handed to a call, chosen by an if, assigned, returned, a default or a\n        value in a table. A key, an index and a comparison are not a colour\n        given to anything."""\n        s = node.value\n        if isinstance(up, (ast.Call, ast.keyword, ast.IfExp)):\n            return s.lower() in CSS_NAMES              # Qt and PIL read a name in any case\n        if s not in CSS_NAMES:\n            return False\n        if isinstance(up, ast.Dict):\n            return any(v is node for v in up.values)\n        if isinstance(up, ast.arguments):\n            return node in up.defaults or node in up.kw_defaults\n        return isinstance(up, (ast.Assign, ast.AnnAssign, ast.Return)) and up.value is node\n\n    for node in ast.walk(tree):\n        up = parent.get(id(node))\n        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in prose:\n            s = node.value\n            for m in HEX.finditer(s):\n                out.append((node.lineno, "hex", m.group(0)))\n            for m in FUNC.finditer(s):\n                if not _clear(m.group(0)):\n                    out.append((node.lineno, "func", " ".join(m.group(0).split())))\n            for m in PROP.finditer(s):\n                for w in WORD.finditer(m.group(2)):\n                    if w.group(1).lower() in CSS_NAMES:\n                        out.append((node.lineno, "name", f"{m.group(1).lower()}: {w.group(1)}"))\n            # a colour name on its own: QColor("yellow"), fill="white", ink = "black"\n            if a_name_on_its_own(node, up):\n                out.append((node.lineno, "name", s))\n        elif isinstance(node, ast.Call):\n            name = getattr(node.func, "id", getattr(node.func, "attr", None))\n            if name in ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba") and node.args \\\n                    and all(isinstance(a, ast.Constant) and not isinstance(a.value, str) for a in node.args):\n                literal = ast.unparse(node)\n                if not _clear(literal):\n                    out.append((node.lineno, "qcolor", literal))\n            # an alpha set as a number: colour.setAlpha(171). Clear and solid are not a choice of alpha.\n            elif name in ("setAlpha", "setAlphaF") and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) \\\n                    and type(node.args[0].value) in (int, float) \\\n                    and node.args[0].value not in ((0, 255) if name == "setAlpha" else (0, 1)):\n                out.append((node.lineno, "alpha", f"{name}({node.args[0].value!r})"))\n        elif isinstance(node, ast.Attribute) and node.attr in QT_GLOBAL \\\n                and ast.unparse(node.value) in ("Qt.GlobalColor", "Qt", "QtCore.Qt.GlobalColor", "QtCore.Qt"):\n            out.append((node.lineno, "global", ast.unparse(node)))\n        elif isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4) and all(\n                isinstance(e, ast.Constant) and type(e.value) is int and 0 <= e.value <= 255 for e in node.elts):\n            if (isinstance(up, (ast.comprehension, ast.For)) and up.iter is node) \\\n                    or isinstance(up, (ast.Compare, ast.Subscript)):\n                continue                                   # an index, a membership or a comparison\n            if isinstance(up, ast.Call) and getattr(up.func, "id", getattr(up.func, "attr", "")) in QCOLOR_CALLS:\n                continue                                   # counted with its QColor(...)\n            if len(node.elts) == 4 and node.elts[3].value == 0:\n                continue                                   # clear\n            if NOT_A_COLOUR.search(named_like(node)):\n                continue\n            out.append((node.lineno, "list" if isinstance(node, ast.List) else "tuple", ast.unparse(node)))\n    return out\n\n\nQCOLOR_CALLS = ("QColor", "fromRgb", "fromRgbF", "qRgb", "qRgba")\n\n\ndef _all_written() -> list:\n    """(rel, line, kind, literal) outside the colour module."""\n    out = []\n    for rel, text in _sources():\n        if rel in COLOUR_MODULES:\n            continue\n        out += [(rel, line, kind, literal) for line, kind, literal in _written(rel, text)]\n    return out\n\n\ndef _data(rel: str, literal: str):\n    """The DATA entry that covers this literal, or None."""\n    for (where, what) in DATA:\n        if where == rel and what in ("*", literal):\n            return (where, what)\n    return None\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_sweep_reads_the_application():\n    files = [rel for rel, _text in _sources()]\n    assert len(files) >= MIN_FILES, f"only {len(files)} files swept: the sweep has gone blind"\n    for rel in COLOUR_MODULES:\n        assert rel in files, f"{rel} is not among the files swept"\n    assert not [f for f in files if f.startswith("tests/")], "the sweep reads the tests"\n\n\ndef test_the_sweep_reads_every_spelling():\n    """Each spelling of a colour, in a line of the kind the application\n    writes, is seen; clear, an index and a margin are not."""\n    seen = {(kind, literal) for _line, kind, literal in _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background-color: #ffcccc; border: 2px solid red;\'\\n"\n        "b = f\'color: rgba(255, 255, 255, 230); padding: {4}px\'\\n"\n        "c = QColor(128, 128, 128)\\n"\n        "d = Qt.GlobalColor.darkGreen\\n"\n        "e = QColor(\'yellow\')\\n"\n        "text_color = (0, 0, 0) if a else (255, 255, 255)\\n"\n        "f = saved.get(\'color\', [200, 200, 200])\\n"\n        "ink = \'white\'\\n"\n        "g = {\'ground\': \'black\'}\\n"\n        "h = Image.new(\'RGB\', (8, 8), \'Gray\')\\n"\n        "c.setAlpha(171)\\n"))}\n    assert seen == {("hex", "#ffcccc"), ("name", "border: red"), ("func", "rgba(255, 255, 255, 230)"),\n                    ("qcolor", "QColor(128, 128, 128)"), ("global", "Qt.GlobalColor.darkGreen"),\n                    ("name", "yellow"), ("tuple", "(0, 0, 0)"), ("tuple", "(255, 255, 255)"),\n                    ("list", "[200, 200, 200]"), ("name", "white"), ("name", "black"), ("name", "Gray"),\n                    ("alpha", "setAlpha(171)")}, seen\n    quiet = _written("probe.py", (\n        "from PyQt6.QtGui import QColor\\n"\n        "from PyQt6.QtCore import Qt\\n"\n        "a = \'background: transparent; border: none; color: rgba(0, 0, 0, 0);\'\\n"\n        "b = QColor(0, 0, 0, 0)\\n"\n        "b.setAlpha(0)\\n"\n        "b.setAlpha(255)\\n"\n        "c = Qt.GlobalColor.transparent\\n"\n        "d = [int(h[i:i + 2], 16) for i in (0, 2, 4)]\\n"\n        "margins = (10, 10, 10, 10)\\n"\n        "sizes = [16, 32, 48]\\n"\n        "\'\'\'a bare string is prose: color: red, #ffcccc\'\'\'\\n"\n        "if d in (5, 10, 20) or d == (0, 0, 0) or a == \'red\':\\n"\n        "    pass\\n"\n        "for size in [16, 32, 48]:\\n"\n        "    e = {\'red\': 1}[\'red\']\\n"))\n    assert quiet == [], quiet\n\n\n# ----------------------------------------------------------------- 1. named\n\ndef test_no_colour_is_written_out_in_the_code():\n    stray = [f"{rel}:{line}  {literal}" for rel, line, _kind, literal in _all_written()\n             if _data(rel, literal) is None]\n    assert not stray, (\n        "a colour is written out where a name belongs. Name it in "\n        f"{COLOUR_MODULES[0]} and read the name; or, if it is data, add it to DATA "\n        "with its reason:\\n  " + "\\n  ".join(stray))\n\n\ndef test_every_data_entry_still_covers_something():\n    """An exemption that outlives what it excused is a licence for the next\n    literal written in that file."""\n    used = {_data(rel, literal) for rel, _line, _kind, literal in _all_written()}\n    stale = [f"{where}: {what}" for (where, what) in DATA if (where, what) not in used]\n    assert not stale, "DATA entries that match nothing now:\\n  " + "\\n  ".join(stale)\n    assert all(reason.strip() for reason in DATA.values()), "a DATA entry has no reason"\n\n\n# ---------------------------------------------------- 2. used: the palettes\n\ndef _strings_the_application_reads() -> set:\n    """Every string the code holds outside the palettes\' own keys: what a\n    lookup by key, or a table of keys, is written with. A module\'s __all__\n    is a list of the names it exports, not of keys, and is left out: a\n    function called warning() does not look up a palette\'s \'warning\'."""\n    out = set()\n    for rel, text in _sources():\n        tree = ast.parse(text)\n        not_keys = _prose(tree)\n        if rel in PALETTE_MODULES:\n            for node in ast.walk(tree):\n                if isinstance(node, ast.Dict):\n                    not_keys |= {id(k) for k in node.keys if k is not None}\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == "__all__" and node.value is not None:\n                not_keys |= {id(n) for n in ast.walk(node.value)}\n        for node in ast.walk(tree):\n            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in not_keys:\n                out.add(node.value)\n    return out\n\n\ndef test_every_colour_a_palette_holds_is_looked_up():\n    read = _strings_the_application_reads()\n    unread = sorted({f"{name}[{key!r}]" for name, palette in PALETTES.items() for key, value in palette.items()\n                     if isinstance(value, str) and (A_COLOUR.fullmatch(value) or value == "transparent")\n                     and key not in read})\n    assert not unread, (\n        "palette entries nothing in the application looks up. A colour is kept "\n        "for what uses it:\\n  " + "\\n  ".join(unread))\n    assert sum(len(p) for p in PALETTES.values()) >= MIN_ENTRIES, "the palettes have gone missing"\n\n\n# --------------------------------------------------- 3. used: the constants\n\ndef _colour_constants() -> dict:\n    """NAME -> where it is defined, for every module-level constant of the\n    colour module whose value is a colour: a hex string, an rgb() string, or\n    channels under a name that says so."""\n    out = {}\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))\n        for node in tree.body:\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if not isinstance(target, ast.Name) or not target.id.isupper():\n                continue\n            value = getattr(module, target.id, None)\n            if isinstance(value, str) and A_COLOUR.fullmatch(value):\n                out[target.id] = rel\n            elif isinstance(value, tuple) and len(value) in (3, 4) and all(type(v) is int for v in value) \\\n                    and re.search(r"RGB|COLOR|COLOUR|OVERLAY", target.id):\n                out[target.id] = rel\n    return out\n\n\ndef _names_the_application_reads() -> dict:\n    """NAME -> how many times the code reads it: as a name or as an attribute."""\n    counts: dict[str, int] = {}\n    for _rel, text in _sources():\n        for node in ast.walk(ast.parse(text)):\n            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):\n                counts[node.id] = counts.get(node.id, 0) + 1\n            elif isinstance(node, ast.Attribute):\n                counts[node.attr] = counts.get(node.attr, 0) + 1\n    return counts\n\n\ndef test_every_colour_constant_is_read():\n    constants = _colour_constants()\n    assert len(constants) >= MIN_CONSTANTS, f"only {len(constants)} colour constants found"\n    reads = _names_the_application_reads()\n    unread = sorted(name for name in constants if not reads.get(name))\n    assert not unread, (\n        "colour constants nothing in the application reads. A name is kept for "\n        "what uses it:\\n  " + "\\n  ".join(f"{name}  ({constants[name]})" for name in unread))\n\n\ndef test_every_exported_name_exists():\n    """__all__ names what the colour module offers. A name it lists and does\n    not define makes `from module import *` fail."""\n    for rel in COLOUR_MODULES:\n        module = importlib.import_module(rel[:-3].replace("/", "."))\n        missing = [n for n in getattr(module, "__all__", []) if not hasattr(module, n)]\n        assert not missing, f"{rel} exports names it does not define: {missing}"\n\n\n# ------------------------------------------- the keys one mode alone holds\n\n#: A key one mode alone reads is in that mode\'s palette alone, and is read\n#: from that palette BY NAME: key -> (the palette that holds it, how the code\n#: spells that palette). Read through "the palette in force" it would be a\n#: KeyError in the mode that does not hold it.\nMODE_ONLY = {\n    \'dialog_btn_bg\': (\'LIGHT_THEME\', \'config.ThemeManager.LIGHT_THEME\'),\n    \'dialog_btn_hover_bg\': (\'DARK_THEME\', \'config.ThemeManager.DARK_THEME\'),\n}\n\n\ndef _lookups_of(key: str) -> list:\n    """(rel, line, what the receiver is) for every lookup of key outside the\n    palettes\' own modules. A receiver that is a name stands for everything\n    that name is assigned in the function the lookup is in."""\n    out = []\n    for rel, text in _sources():\n        if rel in PALETTE_MODULES:\n            continue\n        tree = ast.parse(text)\n        owner = {}\n        for fn in ast.walk(tree):                  # outer functions first, so the innermost is kept\n            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):\n                for node in ast.walk(fn):\n                    owner[id(node)] = fn\n        for node in ast.walk(tree):\n            receiver = None\n            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == key:\n                receiver = node.value\n            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get" and node.args \\\n                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:\n                receiver = node.func.value\n            if receiver is None:\n                continue\n            if isinstance(receiver, ast.Name):\n                is_a = {ast.unparse(n.value) for n in ast.walk(owner.get(id(node), tree))\n                        if isinstance(n, ast.Assign) and len(n.targets) == 1\n                        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == receiver.id}\n            else:\n                is_a = {ast.unparse(receiver)}\n            out.append((rel, node.lineno, is_a))\n    return out\n\n\n@pytest.mark.parametrize("key", sorted(MODE_ONLY))\ndef test_a_key_one_mode_holds_is_read_from_that_palette_by_name(key):\n    palette, spelled = MODE_ONLY[key]\n    assert key in PALETTES[palette], f"{palette} does not hold {key!r}"\n    lookups = _lookups_of(key)\n    assert lookups, f"nothing looks up {key!r}"\n    astray = [f"{rel}:{line}  read from {sorted(is_a) or \'a receiver this test cannot follow\'}"\n              for rel, line, is_a in lookups if is_a != {spelled}]\n    assert not astray, (\n        f"{key!r} is in {palette} alone. Read from anything but {spelled} it is a "\n        "KeyError in the mode that does not hold it:\\n  " + "\\n  ".join(astray))\n\n\ndef test_the_palettes_differ_only_by_the_keys_one_mode_reads():\n    """Dark and light hold the same keys but for MODE_ONLY, and image mode\n    holds every key dark does: a lookup through the current palette cannot\n    miss in any mode."""\n    dark, light = PALETTES["DARK_THEME"], PALETTES["LIGHT_THEME"]\n    assert set(dark) ^ set(light) == set(MODE_ONLY), sorted(set(dark) ^ set(light))\n    assert set(PALETTES["IMAGE_THEME"]) == set(dark), sorted(set(PALETTES["IMAGE_THEME"]) ^ set(dark))\n\n\n# ---------------------------------------------- image mode\'s own palette\n\n#: Image mode is the dark palette under its own name and, after the spread,\n#: the entries image mode reads and draws for itself. A new one is a\n#: decision: it is added here with the entry.\nIMAGE_OWN = ()\n\n\ndef _palette_display(name: str) -> ast.Dict:\n    """The dict display NAME is assigned, at module level or in a class body."""\n    for rel in PALETTE_MODULES:\n        for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8-sig"))):\n            target = (node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else\n                      node.target if isinstance(node, ast.AnnAssign) else None)\n            if getattr(target, "id", None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f"{name} is not written as a dict display")\n\n\ndef test_image_mode_is_the_dark_palette_and_its_own_entries():\n    node = _palette_display("IMAGE_THEME")\n    spreads = [ast.unparse(v) for k, v in zip(node.keys, node.values) if k is None]\n    assert spreads == ["DARK_THEME"] and node.keys[0] is None, (\n        f"IMAGE_THEME spreads {spreads}: it is the dark palette first, and no other")\n    written = sorted(k.value for k in node.keys if k is not None and k.value != "name")\n    assert written == sorted(IMAGE_OWN), (\n        "the entries image mode writes for itself are not the ones listed. An entry "\n        f"image mode never reads is a value nothing shows:\\n  written {written}\\n  listed  {sorted(IMAGE_OWN)}")\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    import hashlib
    CFG = "utils/config.py"
    LOCKED = "test_rnv_color_mixer.py"
    KEYS_GONE = ('main_btn_pressed_bg', 'main_btn_pressed_border')
    MODE_ONLY = {'dialog_btn_bg': 'LIGHT_THEME', 'dialog_btn_hover_bg': 'DARK_THEME'}
    NAMES_GONE = ('BRAND_GOLD_RGB', 'BRAND_DARK_GOLD_RGB', 'APP_HANDLE_HOVER_DARK')
    NEW_VALUES = {'CANVAS_LABEL_ALPHA': '0xB4', 'CANVAS_PREVIEW_ALPHA': '0xC8', 'CANVAS_FAILED_BG': "'#ffcccc'", 'CANVAS_FAILED_EDGE': "'#ff0000'", 'HISTORY_EXPORT_PAGE_BG': 'APP_WINDOW_LIGHT', 'HISTORY_EXPORT_CARD_BG': 'WHITE', 'HISTORY_EXPORT_INK': 'APP_BORDER_DARK', 'SVG_EXPORT_BG': 'WHITE', 'SVG_EXPORT_STROKE': 'TRUE_BLACK', 'CANVAS_PREVIEW_EDGE_DARK': "'#e6e6e6'"}
    LINKED = {'APP_WINDOW_LIGHT': '#f5f5f5', 'WHITE': '#ffffff', 'TRUE_BLACK': '#000000', 'APP_BORDER_DARK': '#333333'}
    OVERLAY_NEW = {'panel': 'rgba(80, 255, 80, 220)', 'tabs': 'rgba(255, 200, 80, 220)', 'default': 'rgba(255, 100, 100, 200)', 'text': '#ffffff', 'edge': 'rgba(255, 255, 255, 230)'}
    MOVED = {'RNV_Color_Mixer.py': ['ColorMixerApp._build_image_section', 'ColorMixerApp._load_session_file', 'ColorMixerApp._on_load_session', 'ColorMixerApp._update_preview', 'ColorMixerApp.auto_mix_colors', 'ColorMixerApp.get_current_state', 'ColorMixerApp.save_color_swatch', 'ColorMixerApp.save_instruction_image'], 'core/color_history.py': ['ColorHistory._export_html'], 'core/color_slot.py': ['ColorSlot.__init__', 'ColorSlot._reset_color', 'ColorSlot.clear'], 'core/package_d_panel.py': ['PackageDPanel._create_debug_overlays'], 'core/palette_formats.py': ['PaletteFormats._export_svg'], 'ui/canvas_view.py': ['ImageDisplayLabel._draw_color_preview', 'ImageDisplayLabel.paintEvent'], 'ui/debug_overlay.py': ['DebugOverlay.__init__', 'DebugOverlayDetailed.__init__'], 'utils/config.py': [], 'test_rnv_color_mixer.py': ['TestConfigExtended.test_all_themes_same_keys']}
    LOST = {'tests/test_app_mirror.py': ['test_the_handle_hover_is_still_one_step_above_the_text'], 'tests/test_ladder_and_plate.py': ['test_every_coincidence_still_coincides', 'test_no_coincidence_is_also_mirrored', 'test_the_coincidence_is_in_the_other_mode']}
    OLD_DIGEST, NEW_DIGEST = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd', 'e00c2424a8c64affdaf67547e59c633e7958427ad26f0186253ae599fb992edb'
    old_cfg, new_cfg = _original(tree, CFG), tree.read(CFG)

    def value(expr):
        return ast.dump(ast.parse(expr, mode="eval").body)

    def palettes(src):
        """ThemeManager's three palettes: NAME -> its entries."""
        cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
        out = dict()
        for node in cls.body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) in ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"):
                out[t.id] = _entries(node.value)
        assert sorted(out) == ["DARK_THEME", "IMAGE_THEME", "LIGHT_THEME"], sorted(out)
        return out

    def functions(src):
        """name -> ast.dump, for module functions and for methods as Class.method."""
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name] = ast.dump(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name] = ast.dump(sub)
        return out

    def app_sources():
        for p in sorted(tree.root.rglob("*.py")):
            rel = p.relative_to(tree.root).as_posix()
            parts = rel.split("/")
            if any(q in ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__")
                   or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "up", "conftest", "run_tests")):
                continue
            text = tree.read(rel) if rel in tree.files else p.read_text(encoding="utf-8-sig", errors="replace")
            if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    # ---- the premise: image mode was dark written out again, entry for entry, so the spread moves nothing
    before, after = palettes(old_cfg), palettes(new_cfg)
    name_is = value("'Image'")
    differ = sorted(k for k in set(before["DARK_THEME"]) | set(before["IMAGE_THEME"])
                    if k != "name" and before["DARK_THEME"].get(k) != before["IMAGE_THEME"].get(k))
    assert not differ and before["IMAGE_THEME"].get("name") == name_is, \
        f"image mode is not the dark palette written out again: {differ} differ. The spread would move them"

    # ---- the palettes: two keys out of dark and light, each mode-only key out of the other, image the spread
    for palette, also in (("DARK_THEME", "dialog_btn_bg"), ("LIGHT_THEME", "dialog_btn_hover_bg")):
        gone = set(KEYS_GONE) | {also}
        assert MODE_ONLY[also] != palette
        assert set(before[palette]) - set(after[palette]) == gone, \
            f"{palette} lost {sorted(set(before[palette]) - set(after[palette]))}"
        assert after[palette] == {k: v for k, v in before[palette].items() if k not in gone}, \
            f"{palette} moved beyond the keys removed"
    spread = "**" + value("DARK_THEME")
    assert after["IMAGE_THEME"] == {spread: value("DARK_THEME"), "name": name_is}, \
        f"IMAGE_THEME is not the dark palette under its own name: {sorted(after['IMAGE_THEME'])}"

    # ---- the module: three names go, ten come at the values the code had, and nothing else moves
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(old_top) - set(new_top) == set(NAMES_GONE), sorted(set(old_top) - set(new_top))
    assert set(new_top) - set(old_top) == set(NEW_VALUES), sorted(set(new_top) - set(old_top))
    for name, expr in NEW_VALUES.items():
        assert new_top[name] == value(expr), f"{name} is not {expr}"
    for name, written in LINKED.items():
        assert old_top.get(name) == value(repr(written)), \
            f"{name} is not {written}: a colour linked to it would move"
    moved = sorted(n for n in new_top if n in old_top and old_top[n] != new_top[n])
    assert moved == ["DEBUG_OVERLAY_COLORS", "NEUTRAL_PROVENANCE"], f"config.py: these names moved: {moved}"

    def table(src, name):
        for node in ast.parse(src).body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) == name:
                return ast.literal_eval(node.value)
        raise AssertionError(f"no {name}")
    was, now = table(old_cfg, "DEBUG_OVERLAY_COLORS"), table(new_cfg, "DEBUG_OVERLAY_COLORS")
    assert now == {**was, **OVERLAY_NEW} and not set(was) & set(OVERLAY_NEW), \
        "DEBUG_OVERLAY_COLORS moved beyond the five entries added"
    was, now = table(old_cfg, "NEUTRAL_PROVENANCE"), table(new_cfg, "NEUTRAL_PROVENANCE")
    assert now == {k: v for k, v in was.items() if k != "APP_HANDLE_HOVER_DARK"} and "APP_HANDLE_HOVER_DARK" in was, \
        "NEUTRAL_PROVENANCE moved beyond the name removed"

    def without_palettes(src):
        cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
        cls.body = [n for n in cls.body if getattr(n.targets[0] if isinstance(n, ast.Assign) else None, "id", None)
                    not in ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME")]
        return ast.dump(cls)
    assert without_palettes(old_cfg) == without_palettes(new_cfg), "ThemeManager moved beyond its three palettes"

    # ---- the code: the functions named, and no other, in every file this round writes
    for rel, want in MOVED.items():
        fo, fn = functions(_original(tree, rel)), functions(tree.read(rel))
        assert set(fo) == set(fn), f"{rel}: functions came or went: {sorted(set(fo) ^ set(fn))}"
        got = sorted(k for k in fo if fo[k] != fn[k])
        assert got == want, f"{rel}: the functions that moved are {got}"

    # ---- derived, over the whole application: nothing reads what went, and a mode's own key is read by name
    for rel, text in app_sources():
        mod = ast.parse(text)
        bound = dict()
        for node in ast.walk(mod):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                bound.setdefault(node.targets[0].id, set()).add(ast.unparse(node.value))
        for node in ast.walk(mod):
            key = receiver = None
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                key, receiver = node.slice.value, node.value
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("get", "pop", "setdefault") \
                    and node.args and isinstance(node.args[0], ast.Constant):
                key, receiver = node.args[0].value, node.func.value
            if isinstance(key, str):
                assert key not in KEYS_GONE, f"{rel}:{node.lineno} looks up {key!r}, a key this round removes"
                if key in MODE_ONLY and rel != CFG:
                    is_a = bound.get(receiver.id, set()) if isinstance(receiver, ast.Name) else {ast.unparse(receiver)}
                    assert is_a == {"config.ThemeManager." + MODE_ONLY[key]}, \
                        f"{rel}:{node.lineno} reads {key!r} from {sorted(is_a)}: it is in {MODE_ONLY[key]} alone"
            name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else \
                [a.name for a in node.names] if isinstance(node, ast.ImportFrom) else None
            for n in ([name] if isinstance(name, str) else name or []):
                assert n not in NAMES_GONE, f"{rel}:{node.lineno} still names {n}, which this round removes"

    # ---- the locked suite: every test kept, and the digest both workflows record is the file's
    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert tests_in(_original(tree, LOCKED)) == tests_in(tree.read(LOCKED)), "the locked root suite gained or lost a test"
    on_disk = hashlib.sha256((tree.root / LOCKED).read_bytes()).hexdigest()
    assert on_disk == OLD_DIGEST, f"the locked suite here is not the one the workflows record: {on_disk}"
    to_write = hashlib.sha256(tree.encode(LOCKED, tree.read(LOCKED))).hexdigest()
    assert to_write == NEW_DIGEST, f"the locked suite this writes has the digest {to_write}, not the one recorded"
    for wf in (".github/workflows/tests-linux.yml", ".github/workflows/tests-windows.yml"):
        was, now = _original(tree, wf), tree.read(wf)
        assert was.count(OLD_DIGEST) == 1 and OLD_DIGEST not in now and now.count(NEW_DIGEST) == 1, \
            f"{wf}: does not record the new digest once"
        kept = [line for line in now.replace(NEW_DIGEST, OLD_DIGEST).splitlines()
                if line in was.splitlines() or not line.strip().startswith("#")]
        assert kept == was.splitlines(), f"{wf}: moved beyond the digest and the note beside it"
    lock = next(cmd for label, cmd in SUITES if "locked file" in label)
    assert NEW_DIGEST in lock[-1] and OLD_DIGEST not in lock[-1], "this script's own digest check is not the new one"

    # ---- the guards: what each loses, and the new one's tests
    assert tests_in(tree.read(GUARD)) == ['test_the_sweep_reads_the_application', 'test_the_sweep_reads_every_spelling', 'test_no_colour_is_written_out_in_the_code', 'test_every_data_entry_still_covers_something', 'test_every_colour_a_palette_holds_is_looked_up', 'test_every_colour_constant_is_read', 'test_every_exported_name_exists', 'test_a_key_one_mode_holds_is_read_from_that_palette_by_name', 'test_the_palettes_differ_only_by_the_keys_one_mode_reads', 'test_image_mode_is_the_dark_palette_and_its_own_entries'], f"{GUARD}: its tests are {tests_in(tree.read(GUARD))}"
    for rel in GUARD_FILES[1:]:
        if not (tree.root / rel).exists() or rel not in tree.files:
            continue
        lost = sorted(set(tests_in(_original(tree, rel))) - set(tests_in(tree.read(rel))))
        assert lost == LOST.get(rel, []), f"{rel} lost {lost}"
    assert SENTINEL in new_cfg and SENTINEL in tree.read(GUARD), "the sentinel is not in the palette and its guard"
# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""

KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
