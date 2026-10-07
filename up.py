"""the mixer's rulings of 5 October: the canvas follows the mode and a dragged selection is see-through gold, the History tab's empty line is drawn in the muted text, an unread preference goes, the workflows' actions are at the versions built for Node 24, and the README's test counts cannot go stale

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (1fc8e13).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-05, items 2, 3, 5, 14 and 18 of the list of 4 October:

  2   "Yes"
  3   "Yes, also i think the comment meant see through gold."
  5   "Yes."
  14  "Yes do it."
  18  "Do B."

ITEM 3, THE CANVAS. Three faults in one paint.
  The canvas asked a theme manager it made itself for the mode, and a new
  one always answers dark. In light mode a dragged selection and the colour
  preview were drawn as in dark. Now the canvas hands its label the theme
  the application is in, as each slot is handed it.
  A dragged selection was filled with SOLID gold, under a comment that said
  semi-transparent: the area being selected could not be seen. The fill is
  the mode's accent at CANVAS_SELECTION_ALPHA now, 0x32, the byte of this
  application's other see-through gold (the screen picker's grid). Its edge
  and corners stay solid.
  The branches asked whether the theme was NAMED Dark. Handed the
  application's theme, image mode, whose palette is the dark one under its
  own name, would have taken light's black figures and grey plate. Dark and
  image take the dark look; only light takes the light one.
The light plate behind a selection's size was written as numbers and never
drawn. It has a name now, CANVAS_LABEL_PLATE_LIGHT, at the value it had.

ITEM 2, THE EMPTY HISTORY LINE. With no history the tab shows one line, and
the code gave it CSS gray. It was never drawn in it: the list's stylesheet
coloured every item, and a stylesheet wins over an item's own colour. The
History list's item rule sets no colour now, so an item's own colour is
drawn, and an entry, which has none, takes the list's, the value the rule
gave it. The line holds text_hint, the muted text the panel's descriptions
take: 4.91:1 in dark and image, 5.27:1 in light. The other three lists keep
the sheet they had.

ITEM 5. The stored preference default_slot_color goes from the settings'
defaults. Nothing read it and no control set it; a new slot starts from
config.DEFAULT_COLOR.

PROVEN BEFORE BUILDING, on the pixels, in dark, light and image. With a
selection dragged, the canvas differs on the selection and nowhere else:
inside its edge in dark and image, and in light on its edge and corners as
well, which were dark's gold. With the History tab empty, the panel differs
on the empty line's text and nowhere else; entries and the other three
lists are drawn as they were. The colour preview differs in light only,
where it was drawn as dark.

ITEM 14. The workflows used actions/checkout@v4 and
actions/setup-python@v5, and the Linux one actions/upload-artifact@v4.
Each is built for Node 20, which GitHub took off its runners on
2026-09-23; since then they are run on Node 24 with a warning on every job.
They move to the first versions built for Node 24: checkout v5,
setup-python v6, upload-artifact v6, the versions the brand repository
moved to on 2026-10-04. Each action's own action.yml was read at both
versions: every input these workflows pass is an input of the newer one,
with the same default.

ITEM 18. The README stated 886 tests; pytest collected 1,206. Every count
is a floor now: over 1,100 tests, over 300 in the locked suite, over 700
under tests/. A floor is the number of test functions the suite defines,
rounded down to the hundred, so the next test leaves it true.

THE GUARDS. tests/test_canvas_follows_the_mode.py and
tests/test_empty_history_line_draws.py read what is drawn back from the
widgets' own pixels. tests/test_unread_preference_is_gone.py keeps the
preference from being written again. tests/test_workflow_actions.py holds
every action at its floor. tests/test_readme_test_counts.py holds every
count in the README to a floor, and every floor to the truth.

THE LOCKED SUITE is not touched: its digest is the one both workflows
record.

WHAT ONLY A RUN ON GITHUB SHOWS. That the workflows run with the newer
actions. The first run after this is committed is that test.
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
SENTINEL = 'RNV-RULINGS-2026-10-05'
SENTINEL_FILE = '.github/workflows/tests-linux.yml'
GUARD = 'tests/test_canvas_follows_the_mode.py'
GUARD_FILES = ['tests/test_canvas_follows_the_mode.py', 'tests/test_empty_history_line_draws.py', 'tests/test_unread_preference_is_gone.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
ROOT_SUITE = 'test_rnv_color_mixer.py'
ACTIONS_GUARD = 'tests/test_workflow_actions.py'
README_GUARD = 'tests/test_readme_test_counts.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_canvas_follows_the_mode.py', 'tests/test_empty_history_line_draws.py', 'tests/test_unread_preference_is_gone.py', 'tests/test_workflow_actions.py', 'tests/test_readme_test_counts.py']
DESCRIPTION = "the mixer's rulings of 5 October: the canvas follows the mode and a dragged selection is see-through gold, the History tab's empty line is drawn in the muted text, an unread preference goes, the workflows' actions are at the versions built for Node 24, and the README's test counts cannot go stale"

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
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '8d27c680c0cbc3e6b413456e5ba897855b7fad67cb07a1f4f9acc7d380933c85', '.github/workflows/tests-windows.yml': '088a22a9c5ea4c1aa1db7954777d8888cc65f39a2f00bdea95f3f79139ea58bf'}

SHADOWS = {"package_d_panel.py", "canvas_view.py", "config.py", "conftest.py", "settings_manager.py", "test_rnv_color_mixer.py", "test_derived_values.py", "test_named_and_used.py", "test_canvas_follows_the_mode.py", "test_empty_history_line_draws.py", "test_unread_preference_is_gone.py", "test_workflow_actions.py", "test_readme_test_counts.py"}

LEFT_ALONE = ['two more lines that set a colour of their own, both in the Presets list, whose sheet colours every item as the History list\'s did: "No user presets yet", measured as drawn in the list\'s own text colour in all three modes, and the line a category shows when it is empty, set the same way. Found while the History line was built. A ruling is asked.', "the canvas's crosshair: its two branches draw the same pen, so which one runs changes nothing. Left as written.", 'a settings file that already holds default_slot_color: the key is carried and ignored, as it always was.', 'the locked suite, test_rnv_color_mixer.py: not touched. Its digest is the one both workflows record.', 'the `.coverage` file the Linux workflow lists among its artifacts: a hidden file, which upload-artifact leaves out unless it is told otherwise. The HTML report and the text report beside it are uploaded, as before.', 'the coverage figures printed beside the counts: a coverage figure depends on the platform it was taken on.', "the rulings still open on the list of 5 October: white or black text on the light gold fill (item 4), the Find and Replace dialog's clipped buttons (12), the transformer's line-number editor (7) and its Export tab (9). Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('core/package_d_panel.py',
             '                empty_item = QListWidgetItem("No color history yet. Mix some colors to get started!")\n                empty_item.setForeground(QColor(128, 128, 128))\n                self.history_list.addItem(empty_item)\n                return\n',
             '                empty_item = QListWidgetItem("No color history yet. Mix some colors to get started!")\n                self.history_list.addItem(empty_item)\n                self._colour_empty_history_line()\n                return\n')
    tree.sub('core/package_d_panel.py',
             '            self.history_list.itemClicked.connect(self._on_history_item_clicked)\n        finally:\n            # Re-enable updates - triggers single repaint\n            self.history_list.setUpdatesEnabled(True)\n        \n    def _populate_history_placeholder(self) -> None:\n',
             '            self.history_list.itemClicked.connect(self._on_history_item_clicked)\n        finally:\n            # Re-enable updates - triggers single repaint\n            self.history_list.setUpdatesEnabled(True)\n        \n    def _colour_empty_history_line(self) -> None:\n        """\n        Draw the History tab\'s empty line in the muted text.\n        \n        RNV-RULINGS-2026-10-05, item 2. The line was given CSS gray, #808080, and\n        was never drawn in it: the list\'s sheet coloured every item, and a\n        sheet wins over an item\'s own colour. This list\'s item rule no\n        longer sets one (see _apply_list_view_styles), and the line takes\n        text_hint, the muted text the panel\'s descriptions take.\n        \n        The empty line is the one item here that holds no colour to load:\n        every entry, and every sample row, carries one in its data.\n        Called when the list is filled and when the theme is applied, so\n        a line made in one mode is not left in another\'s colour.\n        """\n        history_list = getattr(self, \'history_list\', None)\n        if history_list is None:\n            return\n        muted = QColor(_theme_colors(getattr(self, \'_is_dark\', True))[\'text_hint\'])\n        for row in range(history_list.count()):\n            item = history_list.item(row)\n            if item.data(Qt.ItemDataRole.UserRole) is None:\n                item.setForeground(muted)\n        \n    def _populate_history_placeholder(self) -> None:\n')
    tree.sub('core/package_d_panel.py',
             '        list_ss = f"""\n                QListWidget {{\n                    background-color: {bg_col};\n                    color: {text_col};\n                    border: 1px solid {border_col};\n                    outline: 0;\n                }}\n                QListWidget::item {{\n                    padding: 8px 10px;\n                    border-bottom: 1px solid {border_col};\n                    color: {text_col};\n                }}\n                QListWidget::item:hover {{\n                    background-color: {hover_bg};\n                    color: {accent_ink_col};\n                }}\n                QListWidget::item:selected,\n                QListWidget::item:selected:active,\n                QListWidget::item:selected:!active {{\n                    background-color: {accent_col};\n                    color: {accent_text_col};\n                }}\n            """\n',
             '        # RNV-RULINGS-2026-10-05, item 2. The item rule\'s own `color` is handed in:\n        # a sheet that colours every item wins over an item\'s own colour, and\n        # the History tab\'s empty line has one. That list takes the sheet\n        # without the line. An item there with no colour of its own takes the\n        # list\'s: QListWidget\'s `color` and the palette\'s Text, the same value.\n        # The other three lists take the sheet as it was.\n        def list_sheet(item_ink: str) -> str:\n            return f"""\n                QListWidget {{\n                    background-color: {bg_col};\n                    color: {text_col};\n                    border: 1px solid {border_col};\n                    outline: 0;\n                }}\n                QListWidget::item {{\n                    padding: 8px 10px;\n                    border-bottom: 1px solid {border_col};{item_ink}\n                }}\n                QListWidget::item:hover {{\n                    background-color: {hover_bg};\n                    color: {accent_ink_col};\n                }}\n                QListWidget::item:selected,\n                QListWidget::item:selected:active,\n                QListWidget::item:selected:!active {{\n                    background-color: {accent_col};\n                    color: {accent_text_col};\n                }}\n            """\n        list_ss = list_sheet(f"\\n                    color: {text_col};")\n        history_ss = list_sheet("")\n')
    tree.sub('core/package_d_panel.py',
             '            if widget is None:\n                continue\n            widget.setStyleSheet(list_ss)\n',
             "            if widget is None:\n                continue\n            is_history = widget is getattr(self, 'history_list', None)\n            widget.setStyleSheet(history_ss if is_history else list_ss)\n")
    tree.sub('core/package_d_panel.py',
             '                palette.setColor(group, QPalette.ColorRole.Text,            text)\n            widget.setPalette(palette)\n\n    def _apply_combo_view_styles(self, is_dark: bool = True) -> None:\n',
             '                palette.setColor(group, QPalette.ColorRole.Text,            text)\n            widget.setPalette(palette)\n\n        # The empty line holds the muted text of the mode it was made in.\n        self._colour_empty_history_line()\n\n    def _apply_combo_view_styles(self, is_dark: bool = True) -> None:\n')
    tree.sub('utils/config.py',
             'CANVAS_PREVIEW_ALPHA: Final[int] = 0xC8\n"""200. The plate behind the canvas\'s colour preview."""\n',
             'CANVAS_PREVIEW_ALPHA: Final[int] = 0xC8\n"""200. The plate behind the canvas\'s colour preview."""\n\nCANVAS_SELECTION_ALPHA: Final[int] = 0x32\n"""50. A dragged selection\'s fill on the canvas, over the mode\'s accent: gold\nthe image shows through. The fill was solid from the first commit, under a\ncomment that said semi-transparent, so the area being selected could not\nbe seen. RNV-RULINGS-2026-10-05, item 3, ruled: "i think the comment meant see\nthrough gold". The byte is the one this application\'s other see-through\ngold has, the screen picker\'s grid (SCREEN_GRID_ALPHA); a different job, so\nits own name."""\n')
    tree.sub('utils/config.py',
             'CANVAS_PREVIEW_EDGE_DARK: Final[str] = "#e6e6e6"\n"""The edge of the canvas\'s colour preview in dark. Was QColor(230, 230,\n230). In light the edge is TRUE_BLACK. App-owned."""\n',
             'CANVAS_PREVIEW_EDGE_DARK: Final[str] = "#e6e6e6"\n"""The edge of the canvas\'s colour preview in dark. Was QColor(230, 230,\n230). In light the edge is TRUE_BLACK. App-owned."""\n\nCANVAS_LABEL_PLATE_LIGHT: Final[str] = "#c8c8c8"\n"""The plate behind a dragged selection\'s size in light, at\nCANVAS_LABEL_ALPHA. Was QColor(200, 200, 200, 180), which was never drawn:\nthe canvas asked a theme manager of its own for the mode, and a new one\nalways answers dark. RNV-RULINGS-2026-10-05, item 3: the canvas follows the\nmode, so light draws it. In dark and image the plate is TRUE_BLACK.\nApp-owned."""\n')
    tree.sub('ui/canvas_view.py',
             '        # Theme\n        self.is_dark = True\n        \n        # Drag threshold (pixels to move before it counts as drag)\n',
             '        # Theme\n        self.is_dark = True\n        # The theme set_theme() last gave this label: the one the app is in.\n        self._theme: dict | None = None\n        \n        # Drag threshold (pixels to move before it counts as drag)\n')
    tree.sub('ui/canvas_view.py',
             '    def set_theme(self, is_dark: bool) -> None:\n        """Set theme for preview colors."""\n        self.is_dark = is_dark\n        self.update()\n',
             '    def set_theme(self, is_dark: bool, theme: dict | None = None) -> None:\n        """Set theme for preview colors."""\n        self.is_dark = is_dark\n        self._theme = theme\n        self.update()\n\n    def _canvas_theme(self) -> dict | None:\n        """\n        The theme the selection and the preview are drawn for.\n        \n        RNV-RULINGS-2026-10-05, item 3. paintEvent() asked a ThemeManager it\n        made itself, and a new one is always in dark mode: in light the\n        selection and the preview were drawn as in dark, however often\n        set_theme() ran. The slots had the same fault until 2026-09-26.\n        This is the theme set_theme() last gave the label. Before it has\n        run, a fresh ThemeManager answers, as it always did.\n        """\n        if not config:\n            return None\n        return self._theme or config.ThemeManager().get_current_theme()\n\n    @staticmethod\n    def _draws_dark(theme: dict | None) -> bool:\n        """\n        Whether a theme takes the dark look: dark does, and image does.\n        \n        The branches asked whether the theme was NAMED Dark, so image\n        mode, whose palette is the dark one under its own name, would have\n        taken light\'s black figures and grey plate. Only light draws light.\n        """\n        return bool(theme) and theme[\'name\'] != \'Light\'\n\n    @staticmethod\n    def _selection_fill(theme: dict | None) -> str:\n        """\n        A dragged selection\'s fill: the theme\'s accent at\n        CANVAS_SELECTION_ALPHA, so the area being selected shows through.\n        \n        RNV-RULINGS-2026-10-05, item 3. The fill was the accent itself, solid,\n        under a comment that said semi-transparent. With no theme to\n        ask, dark\'s accent, as the border and the corners take.\n        """\n        accent = theme[\'accent\'] if theme else config.ThemeManager.DARK_THEME[\'accent\']\n        return config.translucent(accent, config.CANVAS_SELECTION_ALPHA)\n')
    tree.sub('ui/canvas_view.py',
             '                # Get theme colors\n                theme = config.ThemeManager().get_current_theme() if config else None\n',
             "                # Get theme colors: the theme the app is in, not a new manager's\n                theme = self._canvas_theme()\n")
    tree.sub('ui/canvas_view.py',
             "                    # Determine colors based on theme\n                    if theme and theme['name'] == 'Dark':\n                        overlay_color = QColor(theme['accent'])\n                        border_color = QColor(theme['accent'])\n",
             "                    # Determine colors based on theme\n                    if self._draws_dark(theme):\n                        overlay_color = QColor(self._selection_fill(theme))\n                        border_color = QColor(theme['accent'])\n")
    tree.sub('ui/canvas_view.py',
             "                        _accent = theme['accent'] if theme else config.ThemeManager.DARK_THEME['accent']\n                        overlay_color = QColor(_accent)\n",
             "                        _accent = theme['accent'] if theme else config.ThemeManager.DARK_THEME['accent']\n                        overlay_color = QColor(self._selection_fill(theme))\n")
    tree.sub('ui/canvas_view.py',
             '                    # Draw semi-transparent overlay\n                    painter.fillRect(self.selection_rect, overlay_color)\n',
             '                    # Draw semi-transparent overlay: the accent at\n                    # CANVAS_SELECTION_ALPHA, so the area selected shows through\n                    painter.fillRect(self.selection_rect, overlay_color)\n')
    tree.sub('ui/canvas_view.py',
             "                        if theme and theme['name'] == 'Dark':\n                            painter.fillRect(bg_rect, QColor(config.translucent(\n                                config.TRUE_BLACK, config.CANVAS_LABEL_ALPHA)))\n                        else:\n                            painter.fillRect(bg_rect, QColor(200, 200, 200, 180))\n",
             '                        if self._draws_dark(theme):\n                            painter.fillRect(bg_rect, QColor(config.translucent(\n                                config.TRUE_BLACK, config.CANVAS_LABEL_ALPHA)))\n                        else:\n                            painter.fillRect(bg_rect, QColor(config.translucent(\n                                config.CANVAS_LABEL_PLATE_LIGHT, config.CANVAS_LABEL_ALPHA)))\n')
    tree.sub('ui/canvas_view.py',
             "            # Background\n            if theme and theme['name'] == 'Dark':\n                bg_color = QColor(config.translucent(config.TRUE_BLACK, config.CANVAS_PREVIEW_ALPHA))\n",
             '            # Background\n            if self._draws_dark(theme):\n                bg_color = QColor(config.translucent(config.TRUE_BLACK, config.CANVAS_PREVIEW_ALPHA))\n')
    tree.sub('ui/canvas_view.py',
             "            # Text shadow\n            if theme and theme['name'] == 'Dark':\n                shadow_pen = QPen(QColor(config.WHITE), 1)\n",
             '            # Text shadow\n            if self._draws_dark(theme):\n                shadow_pen = QPen(QColor(config.WHITE), 1)\n')
    tree.sub('ui/canvas_view.py',
             "        try:\n            self.image_label.set_theme(is_dark)\n            \n            # Check if we're in Image Mode\n",
             "        try:\n            # RNV-RULINGS-2026-10-05, item 3: the label is handed the theme the app\n            # is in, as each slot is. Without a handler, the one is_dark names.\n            if ui_handler and hasattr(ui_handler, 'theme_manager'):\n                label_theme = ui_handler.theme_manager.get_current_theme()\n            else:\n                theme_manager = config.ThemeManager()\n                theme_manager.current_theme = 'dark' if is_dark else 'light'\n                label_theme = theme_manager.get_current_theme()\n            self.image_label.set_theme(is_dark, label_theme)\n            \n            # Check if we're in Image Mode\n")
    tree.sub('tests/test_derived_values.py',
             "INT_DATA = {'INITIAL_COLOR_TUPLE': 'the colour shown before anything is mixed -- data, like the hex and rgb() twins beside it'}\n",
             "INT_DATA = {'INITIAL_COLOR_TUPLE': 'the colour shown before anything is mixed -- data, like the hex and rgb() twins beside it',\n            # RNV-RULINGS-2026-10-05, item 3: the canvas label's light plate has a name now,\n            # CANVAS_LABEL_PLATE_LIGHT, and its value is this one's. They are two things: the\n            # plate is the look, and this is data.\n            'DEFAULT_COLOR': 'the colour a slot holds until one is set, and what a session file falls back to -- data a person starts from'}\n")
    tree.sub('tests/test_derived_values.py',
             '#: with a value of their own.\nLOWER8_FLOOR = 8\n',
             "#: with a value of their own.\n#: RNV-RULINGS-2026-10-05, item 3: the canvas's light plate, and its selection\n#: fill for each palette and for no theme.\nLOWER8_FLOOR = 13\n")
    tree.sub('tests/test_derived_values.py',
             'LOWER8_READ_WHERE_SET = {("core/package_d_panel.py", "_style_harmony_description")}\n',
             'LOWER8_READ_WHERE_SET = {("core/package_d_panel.py", "_style_harmony_description"),\n                         ("ui/canvas_view.py", "_selection_fill")}\n')
    tree.sub('tests/test_derived_values.py',
             '        built.append((f"the harmony wash, {\'dark\' if is_dark else \'light\'}", wash))\n    return built, unread\n',
             '        built.append((f"the harmony wash, {\'dark\' if is_dark else \'light\'}", wash))\n    # RNV-RULINGS-2026-10-05, item 3: the canvas\'s selection fill, whose base is the\n    # accent of the theme it is handed. Read from the method that builds it,\n    # for each palette and for no theme at all.\n    from ui.canvas_view import ImageDisplayLabel\n    for palette in PALETTES:\n        built.append((f"the canvas\'s selection fill, {palette}",\n                      ImageDisplayLabel._selection_fill(getattr(C.ThemeManager, palette))))\n    built.append(("the canvas\'s selection fill, no theme", ImageDisplayLabel._selection_fill(None)))\n    return built, unread\n')
    tree.sub('utils/settings_manager.py',
             '            "default_slot_weight": 50,\n            "default_slot_color": [200, 200, 200],  # RGB\n            "max_color_slots": 12,\n',
             '            "default_slot_weight": 50,\n            "max_color_slots": 12,\n')
    tree.sub('tests/test_named_and_used.py',
             '    ("utils/settings_manager.py", "[200, 200, 200]"):\n        "the stored default of a preference, default_slot_color: data in the settings file, not the look",\n    ("core/package_d_panel.py", "QColor(128, 128, 128)"):\n        "HELD, and not data. Set on the empty-history line\'s item and never drawn: the list\'s stylesheet "\n        "colours every item, and the sheet wins. Proven 2026-10-04 with a magenta control. A ruling is "\n        "asked: draw the line in the muted text, or drop the call",\n    ("ui/canvas_view.py", "QColor(200, 200, 200, 180)"):\n        "HELD, and not data. The light plate behind a dragged selection\'s size, never drawn: the view asks "\n        "a theme manager of its own, which always answers dark, so its light branch never runs. Proven "\n        "2026-10-04 with a magenta control. A ruling is asked: make the canvas follow the mode, or drop "\n        "the branch",\n}\n\n',
             '}\n\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/checkout@v4\n',
             'uses: actions/checkout@v5\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/setup-python@v5\n',
             'uses: actions/setup-python@v6\n')
    tree.sub('.github/workflows/tests-linux.yml',
             'uses: actions/upload-artifact@v4\n',
             'uses: actions/upload-artifact@v6\n')
    tree.sub('.github/workflows/tests-linux.yml',
             '\njobs:\n',
             '\n# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version\n# built for Node 24: checkout v5, setup-python v6 and upload-artifact v6.\n# GitHub took Node 20 off its runners on 2026-09-23, and ran the versions\n# before these on Node 24 with a warning. tests/test_workflow_actions.py\n# holds the floor.\njobs:\n')
    tree.sub('.github/workflows/tests-windows.yml',
             'uses: actions/checkout@v4\n',
             'uses: actions/checkout@v5\n')
    tree.sub('.github/workflows/tests-windows.yml',
             'uses: actions/setup-python@v5\n',
             'uses: actions/setup-python@v6\n')
    tree.sub('.github/workflows/tests-windows.yml',
             '\njobs:\n',
             '\n# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version\n# built for Node 24: checkout v5 and setup-python v6.\n# GitHub took Node 20 off its runners on 2026-09-23, and ran the versions\n# before these on Node 24 with a warning. tests/test_workflow_actions.py\n# holds the floor.\njobs:\n')
    tree.sub('README.md',
             '![Tests](https://img.shields.io/badge/tests-886-brightgreen)\n',
             '![Tests](https://img.shields.io/badge/tests-1100%2B-brightgreen)\n')
    tree.sub('README.md',
             'The project carries 886 tests across two harnesses:\n',
             'The project carries over 1,100 tests across two harnesses:\n')
    tree.sub('README.md',
             '| `unittest` | 356 | Locked byte-integrity suite (`test_rnv_color_mixer.py`) |\n',
             '| `unittest` | over 300 | Locked byte-integrity suite (`test_rnv_color_mixer.py`) |\n')
    tree.sub('README.md',
             '| `pytest` | 530 | Modern suite',
             '| `pytest` | over 700 | Modern suite')
    tree.sub('README.md',
             '| **Total** | **886** | **~72% local coverage**',
             '| **Total** | **over 1,100** | **~72% local coverage**')
    tree.sub('README.md',
             '  Built with PyQt6 · 886 tests · ~72% local coverage · Cross-platform CI\n',
             '  Built with PyQt6 · over 1,100 tests · ~72% local coverage · Cross-platform CI\n')
    if (tree.root / 'tests/test_empty_history_line_draws.py').exists():
        raise Stop('tests/test_empty_history_line_draws.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_empty_history_line_draws.py', '"""The History tab\'s empty line is drawn in the muted text.\n\nRNV-RULINGS-2026-10-05, item 2. Ruled 2026-10-05: "Yes".\n\nWHAT WAS THERE. With no history, the tab shows one line: "No color history\nyet. Mix some colors to get started!". The code gave it CSS gray, #808080,\nand it was never drawn in it: the list\'s sheet coloured every item\n(`QListWidget::item { color: ... }`), and a sheet wins over an item\'s own\ncolour. The line was drawn like an entry: #dddddd in dark and image, black\nin light. Shown on 2026-10-04 with a magenta control.\n\nWHAT IS THERE NOW. The History list\'s item rule sets no colour, so an item\'s\nown colour is drawn; an item that has none takes the list\'s, which is the\ncolour the rule gave it. And the line holds `text_hint`, the muted text the\npanel\'s ten descriptions take: 4.91:1 in dark and image, 5.27:1 in light.\n\nTHE OTHER THREE LISTS keep the sheet they had. Two more lines in this panel\nset a colour of their own, both in the Presets list, whose sheet colours\nevery item as this one\'s did. They were found while this was built, and a\nruling is asked on them.\n\nWHAT THIS GUARD HOLDS.\n\n1. The empty line holds the mode\'s muted text.\n2. It is DRAWN in it, and an entry is drawn in the list\'s own text colour\n   as it always was. Read back from the list\'s own pixels, as a comparison:\n   how far the empty line\'s text stands from the row\'s ground, against how\n   far an entry\'s does. Text is drawn with soft edges, more or less so from\n   one machine to the next, and the comparison does not care how soft. This\n   is the test the old line would have failed.\n3. It follows the mode: a switch made with the panel open, or while it was\n   closed, leaves the line in the new mode\'s muted text.\n4. The History list\'s item rule sets no colour, and the other three lists\'\n   rules still do.\n5. An entry holds no colour of its own, as filled and after each mode\'s\n   theme has been applied over it.\n6. The muted text can be read on the list\'s ground: 4.5:1 or better.\n\nEach test drives the app the way a person does: the theme button and the\npanel\'s opener.\n"""\nfrom __future__ import annotations\n\nimport re\n\nimport pytest\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QColor, QImage\nfrom PyQt6.QtWidgets import QApplication, QTabWidget\n\npytestmark = pytest.mark.integration\n\nEMPTY = "No color history yet"\nLISTS = ("history_list", "presets_list", "sessions_list", "harmony_preview_list")\n\n\ndef _far(a: QColor, b: QColor) -> int:\n    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())\n\n\ndef _lum(colour: str) -> float:\n    c = QColor(colour)\n\n    def lin(v):\n        v /= 255\n        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4\n    return 0.2126 * lin(c.red()) + 0.7152 * lin(c.green()) + 0.0722 * lin(c.blue())\n\n\ndef _ratio(a: str, b: str) -> float:\n    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef _mode(app_window) -> str:\n    return app_window.ui_handler.theme_manager.current_theme\n\n\ndef _switch(app_window) -> str:\n    """One press of the theme button."""\n    app_window._on_theme_button_clicked()\n    QApplication.processEvents()\n    return _mode(app_window)\n\n\ndef _palette(panel) -> dict:\n    from core.package_d_panel import _theme_colors\n    return _theme_colors(bool(panel._is_dark))\n\n\ndef _history_tab(app_window, entries=()):\n    """The panel, opened with the app\'s own opener, on its History tab, with\n    the history holding `entries`."""\n    app_window.open_package_d_panel()\n    QApplication.processEvents()\n    panel = app_window._package_d_panel\n    assert panel is not None and panel.isVisible()\n    panel.color_history.clear()\n    for colour in entries:\n        panel.color_history.add_color(colour)\n    panel.refresh_history()\n    for tabs in panel.findChildren(QTabWidget):\n        for index in range(tabs.count()):\n            if tabs.widget(index).isAncestorOf(panel.history_list):\n                tabs.setCurrentIndex(index)\n    panel.history_list.clearSelection()\n    panel.history_list.setCurrentRow(-1)\n    panel.history_list.clearFocus()\n    QApplication.processEvents()\n    return panel\n\n\ndef _reach(list_widget, row: int = 0, skip_left: int = 0) -> tuple:\n    """(the row\'s ground, how far its text stands from that ground): the\n    distance of the pixel furthest from the ground. `skip_left` leaves out\n    an entry\'s colour square."""\n    image = list_widget.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n    rect = list_widget.visualItemRect(list_widget.item(row))\n    ground = image.pixelColor(rect.right() - 4, rect.top() + 4)\n    far = max(_far(image.pixelColor(x, y), ground)\n              for y in range(rect.top() + 3, rect.bottom() - 3)\n              for x in range(rect.left() + 3 + skip_left, rect.right() - 3))\n    assert far > 60, f"no text was found in row {row}"\n    return ground, far\n\n\ndef _every_mode(app_window):\n    """Each mode the theme button reaches, once: (mode, the panel on its History tab)."""\n    seen = []\n    for _ in range(3):\n        mode = _mode(app_window)\n        if mode not in seen:\n            seen.append(mode)\n            yield mode\n        _switch(app_window)\n    assert {"dark", "light", "image"} <= set(seen), seen\n\n\ndef test_the_empty_line_holds_the_modes_muted_text(app_window):\n    for mode in _every_mode(app_window):\n        panel = _history_tab(app_window)\n        item = panel.history_list.item(0)\n        assert panel.history_list.count() == 1 and item.text().startswith(EMPTY), (mode, item.text())\n        muted = _palette(panel)["text_hint"]\n        assert item.foreground().color().name() == QColor(muted).name(), \\\n            f"{mode}: the empty line holds {item.foreground().color().name()}, not text_hint ({muted})"\n        panel.close()\n\n\ndef test_the_empty_line_is_drawn_in_the_muted_text_and_an_entry_in_the_lists(app_window):\n    """Read back from the pixels. Setting a colour on an item is not drawing it."""\n    for mode in _every_mode(app_window):\n        panel = _history_tab(app_window)\n        palette = _palette(panel)\n        assert panel.history_list.item(0).text().startswith(EMPTY)\n        ground, empty = _reach(panel.history_list)\n        panel = _history_tab(app_window, entries=[(40, 90, 200)])\n        assert not panel.history_list.item(0).text().startswith(EMPTY)\n        entry_ground, entry = _reach(panel.history_list, skip_left=40)\n        assert ground == entry_ground, f"{mode}: the two rows are not on one ground"\n        want = _far(QColor(palette["text_hint"]), ground) / _far(QColor(palette["text_color"]), ground)\n        assert 0.4 < want < 0.75, f"{mode}: the two inks are too alike for this test to tell them apart ({want:.2f})"\n        got = empty / entry\n        assert abs(got - want) < 0.12, (\n            f"{mode}: the empty line\'s text stands {got:.2f} as far from the ground as an entry\'s. In the "\n            f"muted text it stands {want:.2f} as far; at 1.00 it is drawn like an entry, which is what a "\n            f"sheet that colours every item does")\n        panel.color_history.clear()\n        panel.close()\n\n\ndef test_it_follows_a_switch_made_with_the_panel_open(app_window):\n    panel = _history_tab(app_window)\n    for _ in range(3):\n        mode = _switch(app_window)\n        palette = _palette(panel)\n        item = panel.history_list.item(0)\n        assert item.foreground().color().name() == QColor(palette["text_hint"]).name(), \\\n            f"a switch to {mode} left the empty line in the old mode\'s colour"\n\n\ndef test_it_follows_a_switch_made_while_the_panel_was_closed(app_window):\n    panel = _history_tab(app_window)\n    for _ in range(3):\n        panel.close()\n        QApplication.processEvents()\n        mode = _switch(app_window)\n        app_window.open_package_d_panel()\n        QApplication.processEvents()\n        item = panel.history_list.item(0)\n        assert item.text().startswith(EMPTY)\n        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \\\n            f"a switch to {mode} with the panel closed left the empty line in the old mode\'s colour"\n\n\ndef test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do(app_window):\n    for mode in _every_mode(app_window):\n        panel = _history_tab(app_window)\n        text = _palette(panel)["text_color"]\n        for name in LISTS:\n            sheet = getattr(panel, name).styleSheet()\n            rules = re.findall(r"QListWidget::item \\{([^}]*)\\}", sheet)\n            assert len(rules) == 1, f"{mode}: {name} has {len(rules)} plain item rules"\n            properties = {line.split(":")[0].strip(): line.split(":", 1)[1].strip()\n                          for line in rules[0].split(";") if ":" in line}\n            if name == "history_list":\n                assert "color" not in properties, (\n                    f"{mode}: the History list\'s item rule sets a colour again. A sheet wins over an "\n                    f"item\'s own colour, so the empty line would stop being drawn in the muted text.")\n            else:\n                assert properties.get("color") == text, \\\n                    f"{mode}: {name}\'s item rule no longer colours its items {text}: {properties}"\n            list_rule = re.search(r"QListWidget \\{([^}]*)\\}", sheet)\n            assert list_rule and re.search(r"(?<![a-z-])color:\\s*" + re.escape(text), list_rule.group(1)), \\\n                f"{mode}: {name} no longer gives its items the list\'s text colour"\n        panel.close()\n\n\ndef test_an_entry_holds_no_colour_of_its_own(app_window):\n    """Not when the list is filled, and not when a theme is applied over it:\n    the pass that colours the empty line runs then too, and has to leave\n    every entry alone."""\n    panel = _history_tab(app_window, entries=[(40, 90, 200), (200, 90, 40)])\n    assert panel.history_list.count() == 2\n\n    def entries_hold_none(when: str) -> None:\n        for row in range(2):\n            item = panel.history_list.item(row)\n            assert item.data(Qt.ItemDataRole.UserRole) is not None and not item.text().startswith(EMPTY)\n            assert item.data(Qt.ItemDataRole.ForegroundRole) is None, \\\n                f"an entry was given a colour of its own {when}"\n    entries_hold_none("when the list was filled")\n    for _ in range(3):\n        mode = _switch(app_window)\n        entries_hold_none(f"when {mode}\'s theme was applied")\n    panel.color_history.clear()\n\n\n@pytest.mark.parametrize("is_dark", [True, False])\ndef test_the_muted_text_can_be_read_on_the_lists_ground(is_dark):\n    from core.package_d_panel import _theme_colors\n    palette = _theme_colors(is_dark)\n    ground = palette.get("scroll_bg", palette["panel_bg"])\n    ratio = _ratio(palette["text_hint"], ground)\n    assert ratio >= 4.5, f"text_hint on the list\'s ground is {ratio:.2f}:1, under 4.5"\n')
    if (tree.root / 'tests/test_canvas_follows_the_mode.py').exists():
        raise Stop('tests/test_canvas_follows_the_mode.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_canvas_follows_the_mode.py', '"""The canvas draws its selection and its preview for the mode the app is in.\n\nRNV-RULINGS-2026-10-05, item 3. Ruled 2026-10-05: "Yes, also i think the\ncomment meant see through gold."\n\nWHAT WAS THERE. Three faults in one paint.\n\n  The canvas asked a ThemeManager it made itself for the mode, and a new one\n  always answers dark. So in light mode a dragged selection and the colour\n  preview were drawn as in dark: dark\'s gold, a black plate, white figures.\n  The slots had the same fault until 2026-09-26.\n\n  The selection was filled with SOLID gold, under a comment that said\n  semi-transparent. The area being selected could not be seen.\n\n  The branches asked whether the theme was NAMED Dark. Had the canvas been\n  handed the app\'s theme, image mode, whose palette is the dark one under\n  its own name, would have taken light\'s black figures and grey plate.\n\nWHAT IS THERE NOW. The canvas hands its label the theme the app is in, as\neach slot is handed it. The fill is the mode\'s accent at\nCANVAS_SELECTION_ALPHA, the byte of this application\'s other see-through\ngold. Dark and image draw the dark look; only light draws the light one.\nThe light plate, which was written as numbers and never drawn, has a name.\n\nWHAT THIS GUARD HOLDS.\n\n1. The label holds the theme the app is in, after every switch.\n2. Dark and image take the dark look. Light takes the light one.\n3. A dragged selection is see-through gold: inside it the image shows\n   through the mode\'s accent at CANVAS_SELECTION_ALPHA, and its edge is the\n   accent, solid. Read back from the label\'s own pixels, and from the\n   string the paint is handed.\n4. The size label and the colour preview are drawn for the mode: light\n   figures on a dark plate in dark and image, dark figures on a light plate\n   in light.\n5. Without a handler, the label takes the theme `is_dark` names.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtCore import QRect\nfrom PyQt6.QtGui import QColor, QImage, QPixmap\nfrom PyQt6.QtWidgets import QApplication\n\nfrom utils import config\n\npytestmark = pytest.mark.integration\n\nGROUND = (90, 120, 150)                     # the image under the selection\nSIZE = (420, 300)\nSELECTION = QRect(60, 50, 240, 150)\nINSIDE = (80, 70)                           # in the selection, clear of its edge, corners and size label\nEDGE = (60, 125)                            # on its left edge, half way down\nLABEL = QRect(165, 119, 30, 12)             # on the size label\'s plate, at the selection\'s centre\nTHEMES = {"dark": "DARK_THEME", "light": "LIGHT_THEME", "image": "IMAGE_THEME"}\n\n\ndef _mode(app_window) -> str:\n    return app_window.ui_handler.theme_manager.current_theme\n\n\ndef _switch(app_window) -> str:\n    """One press of the theme button."""\n    app_window._on_theme_button_clicked()\n    QApplication.processEvents()\n    return _mode(app_window)\n\n\ndef _every_mode(app_window):\n    seen = []\n    for _ in range(3):\n        mode = _mode(app_window)\n        if mode not in seen:\n            seen.append(mode)\n            yield mode\n        _switch(app_window)\n    assert {"dark", "light", "image"} <= set(seen), seen\n\n\ndef _over(under: tuple, colour: str, alpha: int) -> tuple:\n    """`colour` at `alpha` painted over `under`: what a painter leaves."""\n    c = QColor(colour)\n    return tuple(round(top * alpha / 255 + bottom * (255 - alpha) / 255)\n                 for top, bottom in zip((c.red(), c.green(), c.blue()), under))\n\n\ndef _near(pixel: QColor, want: tuple, slack: int = 3) -> bool:\n    return all(abs(got - w) <= slack for got, w in zip((pixel.red(), pixel.green(), pixel.blue()), want))\n\n\ndef _rgb(pixel: QColor) -> tuple:\n    return pixel.red(), pixel.green(), pixel.blue()\n\n\ndef _lum(pixel: QColor) -> float:\n    def lin(v):\n        v /= 255\n        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4\n    return 0.2126 * lin(pixel.red()) + 0.7152 * lin(pixel.green()) + 0.0722 * lin(pixel.blue())\n\n\ndef _label(app_window):\n    label = app_window.canvas_view.image_label\n    ground = QPixmap(*SIZE)\n    ground.fill(QColor(*GROUND))\n    label.setPixmap(ground)\n    label.resize(*SIZE)\n    label.crosshair_pos = None\n    return label\n\n\ndef _dragging(app_window) -> QImage:\n    label = _label(app_window)\n    label.show_preview = False\n    label.is_dragging, label.selection_rect = True, QRect(SELECTION)\n    image = label.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n    label.is_dragging, label.selection_rect = False, None\n    return image\n\n\ndef _previewing(app_window) -> QImage:\n    label = _label(app_window)\n    label.is_dragging, label.selection_rect = False, None\n    label.show_preview, label.preview_color = True, (210, 188, 147)\n    image = label.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n    label.show_preview = False\n    return image\n\n\ndef _plate_and_figures(image: QImage, rect: QRect) -> tuple:\n    """(the darkest, the middle, the lightest) luminance of a region that\n    holds figures on a plate. The middle is the plate: most of the region."""\n    lums = sorted(_lum(image.pixelColor(x, y)) for y in range(rect.top(), rect.bottom() + 1)\n                  for x in range(rect.left(), rect.right() + 1))\n    return lums[0], lums[len(lums) // 2], lums[-1]\n\n\ndef test_the_label_holds_the_theme_the_app_is_in(app_window):\n    label = app_window.canvas_view.image_label\n    for mode in _every_mode(app_window):\n        want = getattr(config.ThemeManager, THEMES[mode])\n        assert label._theme is want, f"{mode}: the canvas label holds {label._theme and label._theme[\'name\']}"\n        assert label._canvas_theme() is want\n\n\ndef test_dark_and_image_take_the_dark_look_and_light_the_light_one():\n    from ui.canvas_view import ImageDisplayLabel\n    assert ImageDisplayLabel._draws_dark(config.ThemeManager.DARK_THEME) is True\n    assert ImageDisplayLabel._draws_dark(config.ThemeManager.IMAGE_THEME) is True, \\\n        "image mode would draw light\'s black figures and grey plate"\n    assert ImageDisplayLabel._draws_dark(config.ThemeManager.LIGHT_THEME) is False\n    assert ImageDisplayLabel._draws_dark(None) is False\n    assert config.ThemeManager.IMAGE_THEME["accent"] == config.ThemeManager.DARK_THEME["accent"]\n\n\ndef test_the_fill_is_the_accent_at_the_named_alpha():\n    """In the string the paint is handed: each palette\'s accent at\n    CANVAS_SELECTION_ALPHA, and dark\'s when there is no theme to ask."""\n    from ui.canvas_view import ImageDisplayLabel\n    manager = config.ThemeManager\n    assert config.CANVAS_SELECTION_ALPHA == 0x32 == config.SCREEN_GRID_ALPHA\n    for palette in THEMES.values():\n        theme = getattr(manager, palette)\n        fill = ImageDisplayLabel._selection_fill(theme)\n        assert fill == config.translucent(theme["accent"], config.CANVAS_SELECTION_ALPHA), (palette, fill)\n        assert fill == "#32" + theme["accent"][1:].lower(), (palette, fill)\n    assert ImageDisplayLabel._selection_fill(None) == ImageDisplayLabel._selection_fill(manager.DARK_THEME)\n    assert ImageDisplayLabel._selection_fill(manager.LIGHT_THEME) != ImageDisplayLabel._selection_fill(manager.DARK_THEME), \\\n        "light and dark share an accent: the test of the mode above would pass with either"\n\n\ndef test_a_dragged_selection_is_see_through_gold(app_window):\n    """Read back from the pixels: the image shows through the mode\'s accent."""\n    for mode in _every_mode(app_window):\n        accent = getattr(config.ThemeManager, THEMES[mode])["accent"]\n        image = _dragging(app_window)\n        assert _near(image.pixelColor(5, 5), GROUND, 0), f"{mode}: the image itself is not what the test laid down"\n        inside = image.pixelColor(*INSIDE)\n        want = _over(GROUND, accent, config.CANVAS_SELECTION_ALPHA)\n        assert _near(inside, want), (\n            f"{mode}: inside the selection the canvas draws {_rgb(inside)}, not the image under "\n            f"{accent} at alpha {config.CANVAS_SELECTION_ALPHA}, which is {want}")\n        solid = QColor(accent)\n        assert not _near(inside, _rgb(solid), 12), f"{mode}: the selection is filled solid: the image cannot be seen"\n        assert not _near(inside, GROUND, 6), f"{mode}: the selection has no fill at all"\n        edge = image.pixelColor(*EDGE)\n        assert _near(edge, _rgb(solid)), f"{mode}: the selection\'s edge is {_rgb(edge)}, not the accent {accent}"\n\n\ndef test_the_size_label_is_drawn_for_the_mode(app_window):\n    """Light figures on a dark plate, or dark figures on a light one. The\n    plate is a fill and is read exactly; the figures are text, with soft\n    edges, and are only asked to stand clear of it on the right side."""\n    for mode in _every_mode(app_window):\n        accent = getattr(config.ThemeManager, THEMES[mode])["accent"]\n        under = _over(GROUND, accent, config.CANVAS_SELECTION_ALPHA)\n        darkest, plate, lightest = _plate_and_figures(_dragging(app_window), LABEL)\n        if mode == "light":\n            want = _over(under, config.CANVAS_LABEL_PLATE_LIGHT, config.CANVAS_LABEL_ALPHA)\n            assert abs(plate - _lum(QColor(*want))) < 0.03, f"light: the size is not on the light plate {want}"\n            assert plate - darkest > 0.2, "light: the size is not in dark figures"\n        else:\n            want = _over(under, config.TRUE_BLACK, config.CANVAS_LABEL_ALPHA)\n            assert abs(plate - _lum(QColor(*want))) < 0.03, f"{mode}: the size is not on the dark plate {want}"\n            assert lightest - plate > 0.3, f"{mode}: the size is not in light figures"\n\n\ndef test_the_preview_is_drawn_for_the_mode(app_window):\n    half = 60                                # the preview is 120 square, at the label\'s centre\n    corner = (SIZE[0] // 2 - half + 3, SIZE[1] // 2 - half + 3)      # on its plate, outside the colour square\n    for mode in _every_mode(app_window):\n        plate = _previewing(app_window).pixelColor(*corner)\n        ink = config.WHITE if mode == "light" else config.TRUE_BLACK\n        want = _over(GROUND, ink, config.CANVAS_PREVIEW_ALPHA)\n        assert _near(plate, want), (\n            f"{mode}: the preview\'s plate is {_rgb(plate)}, not {ink} at alpha "\n            f"{config.CANVAS_PREVIEW_ALPHA} over the image, which is {want}")\n\n\ndef test_without_a_handler_the_label_takes_the_theme_is_dark_names(app_window):\n    canvas = app_window.canvas_view\n    canvas.set_theme(False)\n    assert canvas.image_label._theme is config.ThemeManager.LIGHT_THEME\n    canvas.set_theme(True)\n    assert canvas.image_label._theme is config.ThemeManager.DARK_THEME\n    canvas.set_theme(app_window.ui_handler.is_dark_mode(), app_window.ui_handler)      # as the app left it\n')
    if (tree.root / 'tests/test_unread_preference_is_gone.py').exists():
        raise Stop('tests/test_unread_preference_is_gone.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_unread_preference_is_gone.py', '"""The stored preference nothing read is gone, and stays gone.\n\nRNV-RULINGS-2026-10-05, item 5. Ruled 2026-10-05: "Yes."\n\nWHAT WENT. The settings\' defaults stored a colour for a new slot under one\nkey that nothing read and no control set. A new slot starts from\nconfig.DEFAULT_COLOR; the stored value only looked as if it decided that.\nA settings file that already holds the key keeps it: the key is carried and\nignored, as it always was.\n\nWHAT THIS GUARD HOLDS.\n\n1. The defaults do not store it.\n2. No Python in the repository names it. This file names it in order to\n   forbid it, and is the one file the sweep leaves out.\n3. The sweep is looking.\n"""\nfrom __future__ import annotations\n\nimport pathlib\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: What went. A new slot\'s colour is config.DEFAULT_COLOR.\nPREFERENCE_GONE = "default_slot_color"\n\nMENTION_ONLY = {pathlib.Path(__file__).name}\nDELIVERY_MARK = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"\nSKIP_DIRS = {"build", "dist", "__pycache__", "venv", "env", "node_modules", "htmlcov"}\nMIN_PYTHON = 60\n\n\ndef _python():\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT).as_posix()\n        parts = rel.split("/")\n        if any(part in SKIP_DIRS or part.startswith(".") for part in parts[:-1]):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if len(parts) == 1 and DELIVERY_MARK in text:\n            continue                                  # a delivery script names what it retires\n        yield rel, text\n\n\ndef _named(pairs) -> list:\n    return [f"{rel}:{number}" for rel, text in pairs\n            if pathlib.PurePosixPath(rel).name not in MENTION_ONLY\n            for number, line in enumerate(text.splitlines(), 1) if PREFERENCE_GONE in line]\n\n\ndef test_the_defaults_do_not_store_it():\n    from utils.settings_manager import SettingsManager\n    defaults = SettingsManager.DEFAULT_SETTINGS if hasattr(SettingsManager, "DEFAULT_SETTINGS") \\\n        else SettingsManager._get_default_settings()\n    assert PREFERENCE_GONE not in defaults["preferences"], \\\n        f"the settings\' defaults store {PREFERENCE_GONE} again, and nothing reads it"\n    assert "default_slot_weight" in defaults["preferences"], \\\n        "the slot\'s other default is not where this test looks: it would pass on anything"\n\n\ndef test_nothing_names_it():\n    found = _named(_python())\n    assert not found, (\n        f"{PREFERENCE_GONE} is written again:\\n  " + "\\n  ".join(found)\n        + "\\nIt was removed on 2026-10-05: nothing read it. A new slot starts from config.DEFAULT_COLOR.")\n\n\ndef test_the_sweep_is_looking():\n    pairs = list(_python())\n    assert len(pairs) >= MIN_PYTHON, f"the sweep only found {len(pairs)} Python files"\n    assert "utils/settings_manager.py" in {rel for rel, _ in pairs}\n    assert _named([("utils/sample.py", f\'    "{PREFERENCE_GONE}": [1, 2, 3],\\n\')]) == ["utils/sample.py:1"]\n    assert _named([("tests/" + next(iter(MENTION_ONLY)), PREFERENCE_GONE)]) == []\n    assert _named([("tests/other.py", pathlib.Path(__file__).read_text(encoding="utf-8"))]), \\\n        "this file no longer names it: drop the exemption"\n')
    if (tree.root / 'tests/test_workflow_actions.py').exists():
        raise Stop('tests/test_workflow_actions.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_workflow_actions.py', '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n')
    if (tree.root / 'tests/test_readme_test_counts.py').exists():
        raise Stop('tests/test_readme_test_counts.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_readme_test_counts.py', '"""The README says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 886 tests and pytest collected 1,206.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests the README states is a floor. An exact count,\n   written as a sentence, as a badge or as a cell of the suites\' table, is\n   how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the README\'s number.\n3. The reader is looking. It finds the README\'s floors, and it tells an\n   exact count from a floor in each of the three ways one is written.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nREADME = ROOT / "README.md"\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_color_mixer.py"\n\n#: The README states this many floors. Fewer and the reader has gone blind,\n#: or the README has stopped saying.\nMIN_FLOORS = 6\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nCELL = re.compile(rf"\\|\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\s*(?=\\|)", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\nA_SUITE_ROW = re.compile(r"unittest|pytest|\\btests\\b|coverage", re.I)\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        seen = set()\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):\n            for match in CELL.finditer(line):\n                add(match, bool(match.group("over")))\n    return found\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_the_readme_states_is_a_floor():\n    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in\n             _claims(README.read_text(encoding="utf-8")) if not floor]\n    assert not exact, (\n        "the README states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "the README promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the README\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]\n    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Ctrl+T | 12 | a row of some other table |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (4, 398, False, "root"),\n        (5, 600, True, "pytest"),\n    ], _claims(sample)\n')


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
    def units(src):
        """Every function, method and assignment a source defines, each under its
        name -> its text. A comment is not part of it; a docstring is."""
        out = dict()
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[node.name + "()"] = ast.unparse(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[node.name + "." + sub.name + "()"] = ast.unparse(sub)
                    elif isinstance(sub, (ast.Assign, ast.AnnAssign)) and sub.value is not None:
                        t = sub.targets[0] if isinstance(sub, ast.Assign) else sub.target
                        if isinstance(t, ast.Name):
                            out[node.name + "." + t.id] = ast.unparse(sub.value)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                t = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if isinstance(t, ast.Name):
                    out[t.id] = ast.unparse(node.value)
        return out

    def code(src):
        """units() of a source with every docstring taken out: what the code
        does, not what it says of itself."""
        module = ast.parse(src)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    node.body = node.body[1:] or [ast.Pass()]
        return units(ast.unparse(module))

    def moved(was_src, now_src):
        """(what arrives, what goes, what changes) between two sources, by name."""
        was, now = units(was_src), units(now_src)
        return (sorted(set(now) - set(was)), sorted(set(was) - set(now)),
                sorted(k for k in set(was) & set(now) if was[k] != now[k]))

    def as_written(rel):
        """A file as this round leaves it: from the tree if the round holds it, else from disk."""
        if rel in tree.files:
            return tree.files[rel]
        return (tree.root / rel).read_text(encoding="utf-8-sig", errors="replace")

    def app_sources():
        """(path, text) of the application's Python as this round leaves it: no
        tests, no runner, no delivery script."""
        skip = ("tests", "build", "dist", "docs", "resources", "scripts", "snapshots", "__pycache__",
                "venv", "env", "htmlcov", "node_modules")
        paths = set(p.relative_to(tree.root).as_posix() for p in tree.root.rglob("*.py"))
        paths |= set(r for r in tree.files if r.endswith(".py"))
        for rel in sorted(paths - tree.deleted):
            parts = rel.split("/")
            if any(q in skip or q.startswith(".") for q in parts[:-1]):
                continue
            if len(parts) == 1 and parts[0].startswith(("test_", "conftest", "run_tests")):
                continue
            text = as_written(rel)
            if len(parts) == 1 and "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:
                continue
            yield rel, text

    def names_in(text):
        """Every name, attribute and imported name a source reaches for, and
        every string it writes out whole."""
        found = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name):
                found.add(node.id)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.add(node.name)
        return found

    def tests_in(src):
        return [n.name for n in ast.walk(ast.parse(src))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")]

    def check_moves(table):
        """Each file moves by what the table lists for it, and by nothing else."""
        for rel, arrives, goes, changes in table:
            got = moved(_original(tree, rel), tree.read(rel))
            assert got == (arrives, goes, changes), (
                f"{rel} moved by other than what this round lists: arrives {got[0]}, goes {got[1]}, "
                f"changes {got[2]}")
    PANEL, CANVAS, CFG, SETTINGS = "core/package_d_panel.py", "ui/canvas_view.py", "utils/config.py", "utils/settings_manager.py"
    NAMED = "tests/test_named_and_used.py"
    MOVES = [('core/package_d_panel.py', ['PackageDPanel._colour_empty_history_line()'], [], ['PackageDPanel._apply_list_view_styles()', 'PackageDPanel.refresh_history()']), ('tests/test_derived_values.py', [], [], ['INT_DATA', 'LOWER8_FLOOR', 'LOWER8_READ_WHERE_SET', '_lower8_values()']), ('tests/test_named_and_used.py', [], [], ['DATA']), ('ui/canvas_view.py', ['ImageDisplayLabel._canvas_theme()', 'ImageDisplayLabel._draws_dark()', 'ImageDisplayLabel._selection_fill()'], [], ['CanvasView.set_theme()', 'ImageDisplayLabel.__init__()', 'ImageDisplayLabel._draw_color_preview()', 'ImageDisplayLabel.paintEvent()', 'ImageDisplayLabel.set_theme()']), ('utils/config.py', ['CANVAS_LABEL_PLATE_LIGHT', 'CANVAS_SELECTION_ALPHA'], [], []), ('utils/settings_manager.py', [], [], ['SettingsManager.DEFAULT_SETTINGS'])]
    PREFERENCE = 'default_slot_color'
    check_moves(MOVES)

    # ---- item 5, over the whole application as this round leaves it: nothing reaches for the preference
    swept = []
    for rel, text in app_sources():
        swept.append(rel)
        assert PREFERENCE not in names_in(text), f"{rel} reaches for {PREFERENCE!r}: it is not unread here"
    assert len(swept) >= 31 and all(rel in swept for rel in (PANEL, CANVAS, CFG, SETTINGS)), \
        f"the sweep read {len(swept)} files of the application"

    def default_keys(src):
        cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "SettingsManager")
        table = next(n.value for n in cls.body if isinstance(n, (ast.Assign, ast.AnnAssign))
                     and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, "id", None) == "DEFAULT_SETTINGS")
        return sorted(k.value for d in ast.walk(table) if isinstance(d, ast.Dict)
                      for k in d.keys if isinstance(k, ast.Constant))
    was_keys, now_keys = default_keys(_original(tree, SETTINGS)), default_keys(tree.read(SETTINGS))
    assert [k for k in was_keys if k not in now_keys] == [PREFERENCE] and len(was_keys) - len(now_keys) == 1, \
        f"{SETTINGS}: the defaults moved by other than {PREFERENCE}"

    # ---- item 3: the two names the canvas gains, at the values the code held
    top = units(tree.read(CFG))
    assert top["CANVAS_SELECTION_ALPHA"] == top["SCREEN_GRID_ALPHA"] == "50", (
        f"CANVAS_SELECTION_ALPHA is {top['CANVAS_SELECTION_ALPHA']} and the screen picker's see-through gold "
        f"is at {top['SCREEN_GRID_ALPHA']}")
    assert top["CANVAS_LABEL_PLATE_LIGHT"] == repr("#c8c8c8"), \
        f"the light plate is {top['CANVAS_LABEL_PLATE_LIGHT']}, not the (200, 200, 200) the code wrote out"
    assert top["CANVAS_LABEL_ALPHA"] == "180", "the plate's alpha is not the 180 the code wrote out beside it"

    # ---- the canvas: its paint makes no theme manager, one place says what draws dark, one builds the fill
    label = dict((name, text) for name, text in code(tree.read(CANVAS)).items() if name.startswith("ImageDisplayLabel."))
    makers = sorted(name for name, text in label.items() if "config.ThemeManager()" in text)
    assert makers == ["ImageDisplayLabel._canvas_theme()"], \
        f"{makers} make a theme manager of their own: a new one always answers dark"
    by_name = sorted(name for name, text in label.items() if "['name'] == 'Dark'" in text)
    assert by_name == ["ImageDisplayLabel.paintEvent()"] \
        and label["ImageDisplayLabel.paintEvent()"].count("['name'] == 'Dark'") == 1, (
        f"{by_name} still ask whether the theme is named Dark; only the crosshair may, whose two "
        f"branches draw the same")
    assert sum(text.count("self._draws_dark(theme)") for text in label.values()) == 4, \
        "the four branches that draw differently do not all ask _draws_dark()"
    fills = sorted(name for name, text in label.items() if "CANVAS_SELECTION_ALPHA" in text)
    built = [ast.unparse(n.value) for n in ast.walk(_function(tree.read(CANVAS), "_selection_fill", cls="ImageDisplayLabel"))
             if isinstance(n, ast.Return)]
    assert fills == ["ImageDisplayLabel._selection_fill()"] \
        and built == ["config.translucent(accent, config.CANVAS_SELECTION_ALPHA)"] \
        and label["ImageDisplayLabel.paintEvent()"].count("QColor(self._selection_fill(theme))") == 2, (
        f"the selection's fill is built in {fills} as {built}, and not as the accent at its alpha, once for "
        f"each branch of the paint")
    assert "QColor(200, 200, 200" not in tree.read(CANVAS), "the light plate is written as numbers again"
    handed = code(tree.read(CANVAS))["CanvasView.set_theme()"]
    assert "self.image_label.set_theme(is_dark, label_theme)" in handed \
        and "ui_handler.theme_manager.get_current_theme()" in handed, \
        "the canvas does not hand its label the theme the application is in"

    # ---- item 2: the empty line takes the palette's muted text in one place, and its list a sheet without an ink
    panel = code(tree.read(PANEL))
    line = panel["PackageDPanel._colour_empty_history_line()"]
    assert "['text_hint']" in line and line.count("setForeground(") == 1, "the empty line does not take text_hint"
    assert not [name for name, text in panel.items() if "QColor(128, 128, 128)" in text], \
        "CSS gray is written out in the panel again"
    callers = sorted(name for name, text in panel.items()
                     if "self._colour_empty_history_line()" in text)
    assert callers == ["PackageDPanel._apply_list_view_styles()", "PackageDPanel.refresh_history()"], \
        f"the line is coloured by {callers}: it has to be when the list is filled and when the theme is applied"
    styles = _function(tree.read(PANEL), "_apply_list_view_styles", cls="PackageDPanel")
    text = ast.unparse(styles)
    assert "history_ss = list_sheet('')" in text and "is_history = widget is getattr(self, 'history_list', None)" in text \
        and "widget.setStyleSheet(history_ss if is_history else list_ss)" in text, \
        "the History list does not take the sheet whose item rule sets no colour"
    assert text.count("list_sheet(") == 3, "the sheet is built other than once for each of its two forms"

    # ---- the locked suite is not touched, and the guard that listed the three as held lists them no more
    assert ROOT_SUITE not in tree.files, f"{ROOT_SUITE} is locked, and this round holds an edit to it"

    def table_keys(src):
        node = next(n for n in ast.parse(src).body
                    if isinstance(n, (ast.Assign, ast.AnnAssign))
                    and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target, "id", None) == "DATA")
        return [ast.literal_eval(k) for k in node.value.keys if k is not None]
    was_rows, now_rows = table_keys(_original(tree, NAMED)), table_keys(tree.read(NAMED))
    assert sorted(k for k in was_rows if k not in now_rows) == [('core/package_d_panel.py', 'QColor(128, 128, 128)'), ('ui/canvas_view.py', 'QColor(200, 200, 200, 180)'), ('utils/settings_manager.py', '[200, 200, 200]')] \
        and [k for k in now_rows if k not in was_rows] == [], f"{NAMED}: its table moved by other than the three settled"
    for rel, tests in [('tests/test_canvas_follows_the_mode.py', ['test_the_label_holds_the_theme_the_app_is_in', 'test_dark_and_image_take_the_dark_look_and_light_the_light_one', 'test_the_fill_is_the_accent_at_the_named_alpha', 'test_a_dragged_selection_is_see_through_gold', 'test_the_size_label_is_drawn_for_the_mode', 'test_the_preview_is_drawn_for_the_mode', 'test_without_a_handler_the_label_takes_the_theme_is_dark_names']), ('tests/test_empty_history_line_draws.py', ['test_the_empty_line_holds_the_modes_muted_text', 'test_the_empty_line_is_drawn_in_the_muted_text_and_an_entry_in_the_lists', 'test_it_follows_a_switch_made_with_the_panel_open', 'test_it_follows_a_switch_made_while_the_panel_was_closed', 'test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do', 'test_an_entry_holds_no_colour_of_its_own', 'test_the_muted_text_can_be_read_on_the_lists_ground']), ('tests/test_unread_preference_is_gone.py', ['test_the_defaults_do_not_store_it', 'test_nothing_names_it', 'test_the_sweep_is_looking'])]:
        assert tests_in(tree.read(rel)) == tests, f"{rel}: its tests are {tests_in(tree.read(rel))}"

    # ================= item 14: the workflows' actions, each at the first version built for Node 24
    ACTIONS = (('actions/checkout', 'v4', 'v5'), ('actions/setup-python', 'v5', 'v6'), ('actions/upload-artifact', 'v4', 'v6'))
    WORKFLOW_STEPS = (('.github/workflows/tests-linux.yml', (('actions/checkout', 1), ('actions/setup-python', 1), ('actions/upload-artifact', 1))), ('.github/workflows/tests-windows.yml', (('actions/checkout', 1), ('actions/setup-python', 1))))
    NOTE_OPENS = '# RNV-RULINGS-2026-10-05, item 14. Each action below is at the first version'
    here = sorted(p.relative_to(tree.root).as_posix()
                  for p in (tree.root / ".github" / "workflows").glob("*.y*ml"))
    assert here == [wf for wf, _steps in WORKFLOW_STEPS], f"the workflows here are {here}"
    ag = dict(__name__="workflow_actions_guard", __file__=str(tree.root / ACTIONS_GUARD))
    exec(compile(tree.read(ACTIONS_GUARD), ACTIONS_GUARD, "exec"), ag)
    assert ag["FLOOR"] == dict((action, int(new[1:])) for action, _old, new in ACTIONS), \
        f"{ACTIONS_GUARD}: its floor is {ag['FLOOR']}"
    assert tests_in(tree.read(ACTIONS_GUARD)) == ['test_every_action_is_at_a_version_built_for_node_24', 'test_the_reader_is_looking'], f"{ACTIONS_GUARD}: its tests are {tests_in(tree.read(ACTIONS_GUARD))}"
    for wf, steps in WORKFLOW_STEPS:
        was, now = _original(tree, wf).splitlines(), tree.read(wf).splitlines()
        opens = [n for n, line in enumerate(now) if line == NOTE_OPENS]
        assert len(opens) == 1, f"{wf}: the note is there {len(opens)} times"
        ends = opens[0]
        while now[ends].startswith("#"):
            ends += 1
        assert now[ends] == "jobs:" and ends - opens[0] == 5, f"{wf}: the note is not the five lines above jobs:"
        short = [action.split("/")[1] + " " + new for action, _old, new in ACTIONS if dict(steps).get(action)]
        said = (", ".join(short[:-1]) + " and " + short[-1]) if len(short) > 1 else short[0]
        assert now[opens[0] + 1] == f"# built for Node 24: {said}.", \
            f"{wf}: the note names {now[opens[0] + 1]!r}, and the file's steps are {said}"
        rest = now[:opens[0]] + now[ends:]
        assert len(rest) == len(was), f"{wf}: lines came or went beyond the note"
        counted = dict()
        for before, after in zip(was, rest):
            if before == after:
                continue
            hit = [action for action, old, new in ACTIONS
                   if before.strip() in (f"uses: {action}@{old}", f"- uses: {action}@{old}")
                   and after == before.replace(f"{action}@{old}", f"{action}@{new}")]
            assert len(hit) == 1, (
                f"{wf}: a line moved that is not one of the three actions going to its new version: "
                f"{before.strip()!r} -> {after.strip()!r}")
            counted[hit[0]] = counted.get(hit[0], 0) + 1
        assert sorted(counted.items()) == sorted(steps), f"{wf}: the steps moved are {sorted(counted.items())}"
        name = wf.rsplit("/", 1)[1]
        flagged = ag["_problems"](name, "\n".join(was))
        assert len(flagged) == sum(n for _a, n in steps) and all("is under v" in p for p in flagged), \
            f"{wf}: as it is here, the guard names {flagged}"
        still = ag["_problems"](name, "\n".join(now))
        assert still == [], f"{wf}: the guard would still name {still}"

    # ================= item 18: every count the README states is a floor, and true of this checkout as it will be
    FLOORS = [(300, 'root'), (700, 'pytest'), (1100, 'all'), (1100, 'all'), (1100, 'all'), (1100, 'all')]
    WAS_EXACT = 6
    rg = dict(__name__="readme_counts_guard", __file__=str(tree.root / README_GUARD))
    exec(compile(tree.read(README_GUARD), README_GUARD, "exec"), rg)
    assert rg["ROOT_SUITE"] == ROOT_SUITE and rg["MIN_FLOORS"] == len(FLOORS), \
        f"{README_GUARD}: it is set for {rg['ROOT_SUITE']} and {rg['MIN_FLOORS']} floors"
    assert tests_in(tree.read(README_GUARD)) == ['test_every_number_of_tests_the_readme_states_is_a_floor', 'test_every_floor_is_true', 'test_the_reader_is_looking'], f"{README_GUARD}: its tests are {tests_in(tree.read(README_GUARD))}"
    was_claims, now_claims = rg["_claims"](_original(tree, "README.md")), rg["_claims"](tree.read("README.md"))
    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in was_claims if not floor]
    assert len(exact) == WAS_EXACT and len(was_claims) == WAS_EXACT, \
        f"README.md states {len(exact)} exact counts here, of {len(was_claims)} counts: {exact}"
    left = [f"README.md:{line}: {n:,}" for line, n, floor, _s in now_claims if not floor]
    assert not left, f"README.md would still state an exact count: {left}"
    assert sorted((n, s) for _l, n, _f, s in now_claims) == FLOORS, \
        f"README.md would state {sorted((n, s) for _l, n, _f, s in now_claims)}"
    modern = sorted((set(p.relative_to(tree.root).as_posix() for p in (tree.root / "tests").glob("test_*.py"))
                     | set(r for r in tree.files if r.startswith("tests/test_") and r.count("/") == 1
                           and r.endswith(".py"))) - tree.deleted)
    defined = dict(root=rg["_defined_in"](as_written(ROOT_SUITE), True),
                   pytest=sum(rg["_defined_in"](as_written(rel), False) for rel in modern))
    defined["all"] = defined["root"] + defined["pytest"]
    assert len(modern) >= 57 and defined["root"] > 100, f"the count of tests has gone blind: {len(modern)} files, {defined}"
    for number, suites in FLOORS:
        assert number < defined[suites], \
            f"README.md would say over {number:,}, and here {suites} defines {defined[suites]:,}"
    for wf, _steps in WORKFLOW_STEPS[:1]:
        assert SENTINEL in tree.read(wf) and SENTINEL in tree.read(ACTIONS_GUARD) and SENTINEL in tree.read(README_GUARD), \
            "the sentinel is not in the workflow and the two guards"
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
