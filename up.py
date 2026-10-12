"""the mixer's rulings of 11 October: the Presets list's empty lines drawn in the muted text, the crosshair written as the one colour it always was, and an upload that stops naming a hidden file

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (4178009).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-11, items 20, 22 and 26 of the list of 5 October:

  20  "B"
  22  "A"
  26  "A"

ITEM 20. Two lines stand in the Presets list when it has nothing to show:
"No user presets yet", with User Presets chosen and none saved, and the line
a category shows when it holds no preset. The code gave the first the gold
text and the second dark's disabled grey in every mode, and neither was
drawn in it: the list's sheet coloured every item, the fault the History
tab's empty line had until 5 October. The Presets list's item rule sets no
colour now, as the History list's does, and both lines take text_hint:
#888888 in dark and image, #666666 in light. A preset holds no colour of its
own, so presets are drawn as before, in the list's text colour. The
rendering sent on 5 October shows B.

ITEM 26. The crosshair the canvas draws under the pointer is the dark gold,
#8c7337, in every mode, as it always was: two branches, dark and not dark,
drew the same pen from the light palette's accent. One line now, reading
BRAND_DARK_GOLD. It is drawn over the image, which is the same in every
mode, and this gold shows at both ends of it: 4.17:1 on white, 3.83:1 on
black. The same pixels.

ITEM 22. The Linux workflow's upload named htmlcov/, coverage_report.txt and
.coverage. The last is a hidden file, which upload-artifact leaves out
unless a step sets include-hidden-files: true, so it was never uploaded. It
goes from the list, and a comment says why; the two reports are uploaded as
before. tests/test_workflow_actions.py, the same file in all five apps, now
holds that no upload names a hidden file.

THE COUNT GUARD. tests/test_readme_test_counts.py is the same code in all
five apps, and now reads every document an app names. Here, the README
alone, as before.

The locked suite, test_rnv_color_mixer.py, is not touched.
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
SENTINEL = 'RNV-RULINGS-2026-10-11'
SENTINEL_FILE = 'tests/test_readme_test_counts.py'
GUARD = 'tests/test_empty_presets_lines_draw.py'
GUARD_FILES = ['tests/test_empty_presets_lines_draw.py', 'tests/test_empty_history_line_draws.py', 'tests/test_canvas_follows_the_mode.py', 'tests/test_readme_test_counts.py', 'tests/test_workflow_actions.py']
ROOT_SUITE = 'test_rnv_color_mixer.py'
ACTIONS_GUARD = 'tests/test_workflow_actions.py'
COUNTS_GUARD = 'tests/test_readme_test_counts.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_empty_presets_lines_draw.py', 'tests/test_empty_history_line_draws.py', 'tests/test_canvas_follows_the_mode.py', 'tests/test_readme_test_counts.py', 'tests/test_workflow_actions.py']
DESCRIPTION = "the mixer's rulings of 11 October: the Presets list's empty lines drawn in the muted text, the crosshair written as the one colour it always was, and an upload that stops naming a hidden file"

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
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '5ad021d7752b7d7e7850fd3b732bb5034b977a76234647129a07c55eaef437d1', '.github/workflows/tests-windows.yml': '94d4128fa4a1e56af5b6924bbd8db78b9ee6614c00117845cd59116a024672cf'}

SHADOWS = {"package_d_panel.py", "canvas_view.py", "conftest.py", "test_rnv_color_mixer.py", "test_empty_presets_lines_draw.py", "test_empty_history_line_draws.py", "test_canvas_follows_the_mode.py", "test_workflow_actions.py", "test_readme_test_counts.py"}

LEFT_ALONE = ['the locked suite, test_rnv_color_mixer.py: not touched. Its digest is the one both workflows record.', "the crosshair's colour: the same dark gold in every mode, as it was. Ruled A.", 'the coverage figures printed beside the counts: a coverage figure depends on the platform it was taken on.', "the rulings still open on the list of 11 October: the Find and Replace dialog's clipped buttons (item 12, asked about on 11 October) and the transformer's Export tab (9). Nothing here touches them."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('core/package_d_panel.py',
             "        # RNV-RULINGS-2026-10-05, item 2. The item rule's own `color` is handed in:\n        # a sheet that colours every item wins over an item's own colour, and\n        # the History tab's empty line has one. That list takes the sheet\n        # without the line. An item there with no colour of its own takes the\n        # list's: QListWidget's `color` and the palette's Text, the same value.\n        # The other three lists take the sheet as it was.\n",
             "        # RNV-RULINGS-2026-10-05, item 2. The item rule's own `color` is handed in:\n        # a sheet that colours every item wins over an item's own colour, and\n        # the History tab's empty line has one. That list takes the sheet\n        # without the line. An item there with no colour of its own takes the\n        # list's: QListWidget's `color` and the palette's Text, the same value.\n        # RNV-RULINGS-2026-10-11, item 20: so does the Presets list, whose two\n        # empty lines have one too. The other two lists take the sheet as it was.\n")
    tree.sub('core/package_d_panel.py',
             '        list_ss = list_sheet(f"\\n                    color: {text_col};")\n        history_ss = list_sheet("")\n',
             '        list_ss = list_sheet(f"\\n                    color: {text_col};")\n        bare_ss = list_sheet("")\n')
    tree.sub('core/package_d_panel.py',
             "            is_history = widget is getattr(self, 'history_list', None)\n            widget.setStyleSheet(history_ss if is_history else list_ss)\n",
             "            bare = any(widget is getattr(self, name, None) for name in ('history_list', 'presets_list'))\n            widget.setStyleSheet(bare_ss if bare else list_ss)\n")
    tree.sub('core/package_d_panel.py',
             '        # The empty line holds the muted text of the mode it was made in.\n        self._colour_empty_history_line()\n',
             '        # The empty lines hold the muted text of the mode they were made in.\n        self._colour_empty_history_line()\n        self._colour_empty_presets_lines()\n')
    tree.sub('core/package_d_panel.py',
             "                    item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable\n                    item.setForeground(QColor(_theme_colors(getattr(self, '_is_dark', True))['accent_ink']))  # Gold text\n                    self.presets_list.addItem(item)\n",
             '                    item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable\n                    self.presets_list.addItem(item)\n                    self._colour_empty_presets_lines()\n')
    tree.sub('core/package_d_panel.py',
             "                    item.setFlags(Qt.ItemFlag.NoItemFlags)\n                    item.setForeground(QColor(_theme_colors(True).get('text_disabled', config.ThemeManager.DARK_THEME['text_disabled'])))\n                    self.presets_list.addItem(item)\n",
             '                    item.setFlags(Qt.ItemFlag.NoItemFlags)\n                    self.presets_list.addItem(item)\n                    self._colour_empty_presets_lines()\n')
    tree.sub('core/package_d_panel.py',
             '            if item.data(Qt.ItemDataRole.UserRole) is None:\n                item.setForeground(muted)\n        \n    def _populate_history_placeholder(self) -> None:\n',
             '            if item.data(Qt.ItemDataRole.UserRole) is None:\n                item.setForeground(muted)\n    \n    def _colour_empty_presets_lines(self) -> None:\n        """\n        Draw the Presets list\'s empty lines in the muted text.\n        \n        RNV-RULINGS-2026-10-11, item 20, ruled B. Two lines stand in the\n        list when it has nothing to show: "No user presets yet", with User\n        Presets chosen and none saved, and the line a category shows when it\n        holds no preset. The first was given the gold text and the second\n        dark\'s disabled grey in every mode, and neither was drawn in it: the\n        list\'s sheet coloured every item, the fault the History tab\'s empty\n        line had (RNV-RULINGS-2026-10-05, item 2). This list\'s item rule no\n        longer sets a colour, and both lines take text_hint, as that line does.\n        \n        An empty line is the one item here that holds nothing in its data:\n        every preset, and every placeholder, carries one. Called when a line\n        is made and when the theme is applied, so a line made in one mode is\n        not left in another\'s colour.\n        """\n        presets_list = getattr(self, \'presets_list\', None)\n        if presets_list is None:\n            return\n        muted = QColor(_theme_colors(getattr(self, \'_is_dark\', True))[\'text_hint\'])\n        for row in range(presets_list.count()):\n            item = presets_list.item(row)\n            if item.data(Qt.ItemDataRole.UserRole) is None:\n                item.setForeground(muted)\n        \n    def _populate_history_placeholder(self) -> None:\n')
    tree.sub('tests/test_empty_history_line_draws.py',
             "THE OTHER THREE LISTS keep the sheet they had. Two more lines in this panel\nset a colour of their own, both in the Presets list, whose sheet colours\nevery item as this one's did. They were found while this was built, and a\nruling is asked on them.\n",
             "THE OTHER THREE LISTS kept the sheet they had. Two more lines in this panel\nset a colour of their own, both in the Presets list, whose sheet coloured\nevery item as this one's did. RNV-RULINGS-2026-10-11, item 20, ruled B: that\nlist's item rule sets no colour either, and both lines are drawn in the\nmuted text (tests/test_empty_presets_lines_draw.py). The Sessions list and\nthe harmony preview keep the sheet they had.\n")
    tree.sub('tests/test_empty_history_line_draws.py',
             "4. The History list's item rule sets no colour, and the other three lists'\n   rules still do.\n",
             "4. The History and Presets lists' item rules set no colour, and the other\n   two lists' rules still do.\n")
    tree.sub('tests/test_empty_history_line_draws.py',
             'def test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do(app_window):',
             '#: The lists whose item rule sets no colour: each holds a line with a colour of its own.\nBARE = ("history_list", "presets_list")\n\n\ndef test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do(app_window):')
    tree.sub('tests/test_empty_history_line_draws.py',
             '            if name == "history_list":\n                assert "color" not in properties, (\n                    f"{mode}: the History list\'s item rule sets a colour again. A sheet wins over an "\n                    f"item\'s own colour, so the empty line would stop being drawn in the muted text.")\n',
             '            if name in BARE:\n                assert "color" not in properties, (\n                    f"{mode}: {name}\'s item rule sets a colour again. A sheet wins over an "\n                    f"item\'s own colour, so its empty line would stop being drawn in the muted text.")\n')
    tree.sub('ui/canvas_view.py',
             "                    if theme and theme['name'] == 'Dark':\n                        pen = QPen(QColor(config.ThemeManager.LIGHT_THEME['accent']), 1)\n                    else:\n                        pen = QPen(QColor(config.ThemeManager.LIGHT_THEME['accent']), 1)\n                    \n",
             "                    # RNV-RULINGS-2026-10-11, item 26: the dark gold in every mode,\n                    # as it always was. The crosshair is drawn over the image, which\n                    # is the same in every mode, and this gold shows at both ends of\n                    # it: 4.17:1 on white, 3.83:1 on black. It was light's accent,\n                    # read in two branches that drew this same pen.\n                    pen = QPen(QColor(config.BRAND_DARK_GOLD), 1)\n                    \n")
    tree.sub('tests/test_canvas_follows_the_mode.py',
             '5. Without a handler, the label takes the theme `is_dark` names.\n',
             '5. Without a handler, the label takes the theme `is_dark` names.\n6. The crosshair does not follow the mode. RNV-RULINGS-2026-10-11, item 26,\n   ruled A: it is drawn over the image, which is the same in every mode, in\n   the dark gold, which shows on both white and black. Read back from the\n   pixels, in each mode.\n')
    tree.sub('tests/test_canvas_follows_the_mode.py',
             'def test_without_a_handler_the_label_takes_the_theme_is_dark_names(app_window):',
             'def test_the_crosshair_is_the_dark_gold_in_every_mode(app_window):\n    """RNV-RULINGS-2026-10-11, item 26. Not the mode\'s accent: the same gold\n    over the same image in each mode. Read back from the pixels, which are the\n    ones the crosshair always drew: two arms, ten pixels each way from the\n    centre and one pixel wide, each pixel of them the pen\'s colour, and the\n    image untouched all round them."""\n    want = QColor(config.BRAND_DARK_GOLD).name()\n    centre = (200, 150)\n    for mode in _every_mode(app_window):\n        label = _label(app_window)\n        label.show_preview = False\n        label.is_dragging, label.selection_rect = False, None\n        label.crosshair_pos = centre\n        image = label.grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n        label.crosshair_pos = None\n        x, y = centre\n        arms = ({image.pixelColor(x + d, y).name() for d in range(-10, 11)}\n                | {image.pixelColor(x, y + d).name() for d in range(-10, 11)})\n        assert arms == {want}, f"{mode}: the crosshair is drawn in {sorted(arms)}, not the dark gold {want}"\n        off = [(dx, dy) for dx in range(-14, 15) for dy in range(-14, 15)\n               if not ((dy == 0 and abs(dx) <= 10) or (dx == 0 and abs(dy) <= 10))\n               and not _near(image.pixelColor(x + dx, y + dy), GROUND, 0)]\n        assert not off, f"{mode}: the crosshair is not the two arms it was: it paints off them, at {off[:6]}"\n\n\ndef test_without_a_handler_the_label_takes_the_theme_is_dark_names(app_window):')
    tree.sub('.github/workflows/tests-linux.yml',
             '          name: coverage-report-linux\n          path: |\n            htmlcov/\n            coverage_report.txt\n            .coverage\n          retention-days: 14\n',
             '          name: coverage-report-linux\n          # RNV-RULINGS-2026-10-11, item 22: .coverage went from this list. It is\n          # a hidden file, which upload-artifact leaves out; the two reports go.\n          path: |\n            htmlcov/\n            coverage_report.txt\n          retention-days: 14\n')
    tree.sub('tests/test_workflow_actions.py',
             '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n',
             '"""Every action the workflows use is at a version built for the Node the runners have.\n\nRNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".\nRNV-RULINGS-2026-10-11, item 22. Ruled 2026-10-11: "A". An upload names no\nhidden file.\n\nWHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a\nworkflow keeps something from the run, actions/upload-artifact@v4. Each of\nthose declares `using: node20` in its own action.yml. GitHub took Node 20\noff its hosted runners on 2026-09-23. Since then an action that declares it\nis run on Node 24 instead, and the job carries a warning that names it.\n\nWHAT IS THERE NOW. The first version of each that declares node24: checkout\nv5, setup-python v6, upload-artifact v6. They are the versions the brand\nrepository moved its own workflows to on 2026-10-04.\n\nREAD, NOT ASSUMED. Each action\'s action.yml was read at both tags on\n2026-10-05. Every input these workflows pass is an input of the newer\nversion, with the same default and the same `required`. No input the older\nversion had is gone from the newer one.\n\nAN UPLOAD NAMES NO HIDDEN FILE. upload-artifact leaves out a file or a\nfolder whose name begins with a dot, unless the step sets\ninclude-hidden-files: true; its default is false, at v4 and at v6. Until\n2026-10-11 three steps, in the picker and the palette manager, named only\n.coverage files: they uploaded nothing, and said so to no one, since each\nwas told to ignore finding nothing. Ruled A: they went. The mixer\'s step\nnamed .coverage beside its two reports, which it uploads; that line went.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every `uses:` in every workflow names an action in FLOOR, at that major\n   version or a later one. An action that is not in FLOOR is a new one: read\n   which Node it is built for, then add it.\n2. Every path an upload-artifact step names is a file or folder it can\n   upload: none is hidden, unless the step includes hidden files.\n3. The reader is looking. It finds the steps of every workflow, in either\n   way YAML writes one, and it flags a version under the floor. It finds\n   every upload step\'s paths, written on one line or as a block.\n\nWHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nWORKFLOWS = ROOT / ".github" / "workflows"\n\n#: The lowest major version of each action that declares node24.\nFLOOR = {\n    "actions/checkout": 5,\n    "actions/setup-python": 6,\n    "actions/upload-artifact": 6,\n}\n\n#: Every workflow checks the repository out and sets Python up.\nEVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")\n\nUSES = re.compile(r"^\\s*(?:-\\s+)?uses:\\s*([^\\s#]+)")\nVERSION = re.compile(r"^v(\\d+)(?:\\.\\d+)*$")\n#: A path with a part whose name begins with a dot: what upload-artifact leaves out.\nHIDDEN = re.compile(r"(?:^|/)\\.[^./]")\nUPLOAD = "actions/upload-artifact"\n\n\ndef _uses(text: str) -> list:\n    """(line number, action, ref) for every step that uses an action."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        match = USES.match(line)\n        if match:\n            action, _, ref = match.group(1).partition("@")\n            found.append((number, action, ref))\n    return found\n\n\ndef _indent(line: str) -> int:\n    return len(line) - len(line.lstrip())\n\n\ndef _uploads(text: str) -> list:\n    """(line number of its `uses:`, the paths it names, whether it includes\n    hidden files) for every step that uses upload-artifact."""\n    lines = text.splitlines()\n    found = []\n    for number, action, _ref in _uses(text):\n        if action != UPLOAD:\n            continue\n        start = number - 1\n        while start > 0 and not lines[start].lstrip().startswith("- "):\n            start -= 1\n        end = start + 1\n        while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > _indent(lines[start])):\n            end += 1\n        step = lines[start:end]\n        paths, hidden_too = [], False\n        for i, line in enumerate(step):\n            key, _, value = line.strip().partition(":")\n            value = value.strip()\n            if key == "include-hidden-files":\n                hidden_too = value.strip("\'\\"").lower() == "true"\n            elif key == "path" and value in ("|", "|-", ">", ">-"):\n                block = i + 1\n                while block < len(step) and (not step[block].strip() or _indent(step[block]) > _indent(line)):\n                    if step[block].strip():\n                        paths.append(step[block].strip())\n                    block += 1\n            elif key == "path":\n                paths.append(value)\n        found.append((number, paths, hidden_too))\n    return found\n\n\ndef _problems(name: str, text: str) -> list:\n    out = []\n    for number, action, ref in _uses(text):\n        where = f"{name}:{number}: {action}@{ref}"\n        if action not in FLOOR:\n            out.append(f"{where} is not an action this guard knows. Read which Node its "\n                       f"action.yml declares at that version, then add it to FLOOR.")\n            continue\n        version = VERSION.match(ref)\n        if not version:\n            out.append(f"{where} is pinned by something other than a version tag, which "\n                       f"this guard cannot compare.")\n        elif int(version.group(1)) < FLOOR[action]:\n            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "\n                       f"Node 24.")\n    return out\n\n\ndef _workflows() -> dict:\n    return {path.name: path.read_text(encoding="utf-8")\n            for path in sorted(WORKFLOWS.glob("*.y*ml"))}\n\n\ndef test_every_action_is_at_a_version_built_for_node_24():\n    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]\n    assert not problems, (\n        "GitHub\'s runners no longer have Node 20:\\n  " + "\\n  ".join(problems))\n\n\ndef test_an_upload_names_no_hidden_file():\n    problems = [f"{name}:{number}: {path}" for name, text in _workflows().items()\n                for number, paths, hidden_too in _uploads(text) if not hidden_too\n                for path in paths if HIDDEN.search(path)]\n    assert not problems, (\n        "upload-artifact leaves hidden files out unless the step sets include-hidden-files: "\n        "true, so these upload nothing:\\n  " + "\\n  ".join(problems))\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds no step passes the test above."""\n    workflows = _workflows()\n    assert workflows, f"no workflow found under {WORKFLOWS}"\n    for name, text in workflows.items():\n        used = {action for _n, action, _ref in _uses(text)}\n        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]\n        assert not missing, f"{name}: the reader finds no step that uses {missing}"\n\n    sample = ("    steps:\\n"\n              "      - uses: actions/checkout@v4\\n"\n              "      - name: Python\\n"\n              "        uses: actions/setup-python@v6  # a comment\\n"\n              "      - name: Something new\\n"\n              "        uses: someone/something@v1\\n"\n              "      - name: Pinned\\n"\n              "        uses: actions/upload-artifact@main\\n"\n              "      - run: echo uses: actions/checkout@v1\\n")\n    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),\n                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \\\n        "the reader does not find a step written as a list item, or under a name"\n    flagged = _problems("sample.yml", sample)\n    assert len(flagged) == 3, flagged\n    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \\\n        and "other than a version tag" in flagged[2], flagged\n\n    for name, text in workflows.items():\n        steps = [n for n, action, _ref in _uses(text) if action == UPLOAD]\n        assert [n for n, _p, _h in _uploads(text)] == steps, f"{name}: the reader misses an upload step"\n        assert all(paths for _n, paths, _h in _uploads(text)), f"{name}: the reader finds an upload with no path"\n    uploads = ("    steps:\\n"\n               "      - name: Two reports and the data\\n"\n               "        # a comment\\n"\n               "        uses: actions/upload-artifact@v6\\n"\n               "        with:\\n"\n               "          name: coverage\\n"\n               "          path: |\\n"\n               "            htmlcov/\\n"\n               "            .coverage\\n"\n               "          retention-days: 14\\n"\n               "      - uses: actions/upload-artifact@v6\\n"\n               "        with:\\n"\n               "          path: reports/.hidden.txt\\n"\n               "          include-hidden-files: true\\n"\n               "      - name: One line\\n"\n               "        uses: actions/upload-artifact@v6\\n"\n               "        with: {path: dist/}\\n")\n    assert _uploads(uploads) == [(4, ["htmlcov/", ".coverage"], False), (11, ["reports/.hidden.txt"], True),\n                                 (16, [], False)], _uploads(uploads)\n    assert [p for p in ("htmlcov/", ".coverage", ".coverage.*", "reports/.hidden.txt", "./out", "../x")\n            if HIDDEN.search(p)] == [".coverage", ".coverage.*", "reports/.hidden.txt"]\n')
    tree.sub('tests/test_readme_test_counts.py',
             '"""The README says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 886 tests and pytest collected 1,206.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests the README states is a floor. An exact count,\n   written as a sentence, as a badge or as a cell of the suites\' table, is\n   how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the README\'s number.\n3. The reader is looking. It finds the README\'s floors, and it tells an\n   exact count from a floor in each of the three ways one is written.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nREADME = ROOT / "README.md"\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_color_mixer.py"\n\n#: The README states this many floors. Fewer and the reader has gone blind,\n#: or the README has stopped saying.\nMIN_FLOORS = 6\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nCELL = re.compile(rf"\\|\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\s*(?=\\|)", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\nA_SUITE_ROW = re.compile(r"unittest|pytest|\\btests\\b|coverage", re.I)\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    for number, line in enumerate(text.splitlines(), 1):\n        seen = set()\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if line.lstrip().startswith("|") and A_SUITE_ROW.search(line):\n            for match in CELL.finditer(line):\n                add(match, bool(match.group("over")))\n    return found\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_the_readme_states_is_a_floor():\n    exact = [f"README.md:{line}: {n:,}" for line, n, floor, _s in\n             _claims(README.read_text(encoding="utf-8")) if not floor]\n    assert not exact, (\n        "the README states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"README.md:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for line, n, floor, suites in _claims(README.read_text(encoding="utf-8"))\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "the README promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the README\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    floors = [c for c in _claims(README.read_text(encoding="utf-8")) if c[2]]\n    assert len(floors) >= MIN_FLOORS, f"the reader finds {len(floors)} floors in the README, not {MIN_FLOORS}"\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | Frozen |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Ctrl+T | 12 | a row of some other table |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (4, 398, False, "root"),\n        (5, 600, True, "pytest"),\n    ], _claims(sample)\n',
             '"""Every document says how many tests there are in a way that stays true.\n\nRNV-RULINGS-2026-10-05, item 18. Ruled 2026-10-05: "Do B".\nRNV-RULINGS-2026-10-11, item 23. Ruled 2026-10-11: "Yes". The other\ndocuments that state how many tests there are take the README\'s floors, and\nthis guard reads them too.\n\nWHAT WAS THERE. Exact totals, written once and kept in step by nothing. On\n2026-10-05 the README said 886 tests and pytest collected 1,206.\nNo other document here states a total.\n\nWHAT IS THERE NOW. Every figure is a floor: "over N". N is the number of\ntest functions the suites define, rounded down to the hundred. A test added\nleaves it true, so there is nothing to keep in step. pytest collects more\nthan that number, because a parametrised function is written once and\ncollected once for each case.\n\nA DATED RECORD IS LEFT AS IT WAS. A section that records the counts at a\nmoment past, such as the log of the campaign that built the suite, says\nwhat was true then; a floor would make it say something else. Each such\nsection is named in RECORDS, and its counts are not read.\n\nWHAT THIS GUARD HOLDS.\n\n1. Every number of tests a document in DOCUMENTS states, outside a dated\n   record, is a floor. An exact count, written as a sentence, as a badge\n   or as a cell of a table of suites, is how the old ones went stale.\n2. Every floor is true. The suite it speaks of defines more test functions\n   than it says. Take tests away until one is not, and this names it: lower\n   the document\'s number.\n3. The reader is looking. It finds each document\'s floors, and every dated\n   record it is told to leave alone, still holding counts; it tells an\n   exact count from a floor in each of the three ways one is written; and\n   it reads a table\'s cell for its column\'s heading alone, as for its row\'s\n   label alone.\n\nWHAT IT DOES NOT HOLD. The coverage figures beside the counts: a coverage\nfigure depends on the platform it was taken on.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\n#: The unittest suite at the repository root.\nROOT_SUITE = "test_rnv_color_mixer.py"\n\n#: Every document that says how many tests there are, and how many floors it\n#: states. Fewer and the reader has gone blind, or the document has stopped\n#: saying. The README is the first.\nDOCUMENTS = {\'README.md\': 6}\n\n#: Sections that are dated records, by the document and the heading\'s text.\n#: Their counts are what was true when they were written, and are not read.\nRECORDS = {}\n\nNUMBER = r"\\d{1,3}(?:,\\d{3})+|\\d+"\nSENTENCE = re.compile(rf"(?P<n>{NUMBER})\\s+(?:(?:unittest|pytest|passing|automated)\\s+)?tests\\b", re.I)\nBADGE = re.compile(r"\\btests-(?P<n>\\d+)(?P<plus>%2B)?", re.I)\nOVER_BEFORE = re.compile(r"over\\s+\\**$", re.I)\n#: A table\'s cell holds a count of tests when its column is headed so, or\n#: when its row is labelled so ("Total tests"). A cell is its number alone.\nSEPARATOR = re.compile(r"^\\s*\\|?(?:\\s*:?-{2,}:?\\s*\\|)+\\s*:?-*:?\\s*$")\nCOUNT_COLUMN = re.compile(r"\\b(?:tests?|count)\\b", re.I)\nTEST_ROW = re.compile(r"\\btests?\\b|unittest|pytest", re.I)\nCELL = re.compile(rf"^\\s*\\**(?P<over>over\\s+)?(?P<n>{NUMBER})\\**\\*?\\s*$", re.I)\nHEADING = re.compile(r"^(?P<level>#{1,6})\\s+(?P<text>.+?)\\s*$")\nFENCE = re.compile(r"^\\s*(```|~~~)")\n\n\ndef _cells(line: str) -> list:\n    """(where it starts in the line, its text) for each cell of a table\'s row."""\n    edges = [i for i, ch in enumerate(line) if ch == "|"]\n    return [(a + 1, line[a + 1:b]) for a, b in zip(edges, edges[1:])]\n\n\ndef _claims(text: str) -> list:\n    """(line number, the number, whether it is a floor, which suites it\n    counts) for every number of tests the text states."""\n    found = []\n    lines = text.splitlines()\n    header = None\n    for number, line in enumerate(lines, 1):\n        seen = set()\n        in_table = line.lstrip().startswith("|")\n        if not in_table:\n            header = None\n        elif SEPARATOR.match(line):\n            continue\n        elif number < len(lines) and SEPARATOR.match(lines[number]):\n            header = [cell.strip() for _at, cell in _cells(line)]\n            continue\n\n        def add(match, floor: bool) -> None:\n            if match.start("n") in seen:\n                return\n            seen.add(match.start("n"))\n            low = line.lower()\n            root = "unittest" in low or ROOT_SUITE.lower() in low\n            modern = "pytest" in low or "`tests/`" in low\n            suites = "root" if root and not modern else "pytest" if modern and not root else "all"\n            found.append((number, int(match.group("n").replace(",", "")), floor, suites))\n\n        for match in BADGE.finditer(line):\n            add(match, bool(match.group("plus")))\n        for match in SENTENCE.finditer(line):\n            add(match, bool(OVER_BEFORE.search(line[:match.start("n")])))\n        if in_table and header is not None:\n            cells = _cells(line)\n            labelled = bool(cells) and bool(TEST_ROW.search(cells[0][1]))\n            for column, (at, cell) in enumerate(cells):\n                match = CELL.match(cell)\n                headed = column < len(header) and bool(COUNT_COLUMN.search(header[column]))\n                if match and column and (headed or labelled):\n                    add(_Shifted(match, at), bool(match.group("over")))\n    return found\n\n\nclass _Shifted:\n    """A match in a cell, read as a match in its line."""\n\n    def __init__(self, match, at: int) -> None:\n        self.match, self.at = match, at\n\n    def start(self, group: str) -> int:\n        return self.at + self.match.start(group)\n\n    def group(self, name: str):\n        return self.match.group(name)\n\n\ndef _records(text: str, headings) -> dict:\n    """heading -> the line numbers of its section, for each dated record a\n    text holds: from its heading to the next heading of its level or above.\n    A heading inside a fenced block of code is not one."""\n    lines, fenced, found = text.splitlines(), False, {}\n    marks = []\n    for number, line in enumerate(lines, 1):\n        if FENCE.match(line):\n            fenced = not fenced\n            continue\n        match = None if fenced else HEADING.match(line)\n        if match:\n            marks.append((number, len(match.group("level")), match.group("text")))\n    for i, (number, level, title) in enumerate(marks):\n        if title in headings:\n            end = next((n for n, lv, _t in marks[i + 1:] if lv <= level), len(lines) + 1)\n            found.setdefault(title, []).append(range(number, end))\n    return found\n\n\ndef _read(rel: str) -> str:\n    return (ROOT / rel).read_text(encoding="utf-8-sig")\n\n\ndef _stated(rel: str) -> list:\n    """The claims a document makes, outside its dated records."""\n    text = _read(rel)\n    skipped = set()\n    for spans in _records(text, RECORDS.get(rel, ())).values():\n        for span in spans:\n            skipped.update(span)\n    return [claim for claim in _claims(text) if claim[0] not in skipped]\n\n\ndef _defined_in(source: str, unittest_file: bool) -> int:\n    """How many test functions a file\'s text defines: a lower bound on what\n    is collected from it, since a function is collected at least once."""\n    tree = ast.parse(source)\n    count = 0\n    for node in tree.body:\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            count += node.name.startswith("test_") and not unittest_file\n        elif isinstance(node, ast.ClassDef) and (unittest_file or node.name.startswith("Test")):\n            prefix = "test" if unittest_file else "test_"\n            count += sum(1 for member in node.body\n                         if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))\n                         and member.name.startswith(prefix))\n    return count\n\n\ndef _defined(path: pathlib.Path, unittest_file: bool) -> int:\n    return _defined_in(path.read_text(encoding="utf-8-sig"), unittest_file)\n\n\ndef _suites() -> dict:\n    root = _defined(ROOT / ROOT_SUITE, unittest_file=True)\n    modern = sum(_defined(path, unittest_file=False)\n                 for path in sorted((ROOT / "tests").glob("test_*.py")))\n    return {"root": root, "pytest": modern, "all": root + modern}\n\n\ndef test_every_number_of_tests_a_document_states_is_a_floor():\n    exact = [f"{rel}:{line}: {n:,}" for rel in DOCUMENTS\n             for line, n, floor, _s in _stated(rel) if not floor]\n    assert not exact, (\n        "a document states an exact number of tests, which goes stale with the next "\n        "test:\\n  " + "\\n  ".join(exact) + "\\nSay it as a floor: over N. A section that records the "\n        "counts at a moment past is named in RECORDS instead.")\n\n\ndef test_every_floor_is_true():\n    defined = _suites()\n    names = {"root": ROOT_SUITE, "pytest": "tests/", "all": "the two suites together"}\n    false = [f"{rel}:{line}: over {n:,}, and {names[suites]} defines {defined[suites]:,}"\n             for rel in DOCUMENTS for line, n, floor, suites in _stated(rel)\n             if floor and not n < defined[suites]]\n    assert not false, (\n        "a document promises more tests than the suites define:\\n  " + "\\n  ".join(false)\n        + "\\nLower the document\'s number.")\n\n\ndef test_the_reader_is_looking():\n    """A reader that finds nothing passes both tests above."""\n    readme = next(iter(DOCUMENTS))\n    assert readme == "README.md", f"the README is not the first document: {list(DOCUMENTS)}"\n    for rel, least in DOCUMENTS.items():\n        floors = [c for c in _stated(rel) if c[2]]\n        assert len(floors) >= least, f"the reader finds {len(floors)} floors in {rel}, not {least}"\n    floors = [c for c in _stated(readme) if c[2]]\n    assert {c[3] for c in floors} == {"root", "pytest", "all"}, \\\n        f"the README\'s floors speak of {sorted({c[3] for c in floors})}, not of each suite and of both"\n    for rel, headings in RECORDS.items():\n        text = _read(rel)\n        found = _records(text, headings)\n        for heading in headings:\n            spans = found.get(heading, [])\n            assert len(spans) == 1, f"{rel}: the dated record {heading!r} is there {len(spans)} times"\n            held = [c for c in _claims(text) if c[0] in spans[0]]\n            assert held, f"{rel}: the dated record {heading!r} holds no count: it needs no exemption"\n    defined = _suites()\n    assert defined["root"] > 100 and defined["pytest"] > 100, f"the count of test functions has gone blind: {defined}"\n\n    sample = ("![Tests](https://img.shields.io/badge/tests-786%20passing-brightgreen)\\n"\n              "![Tests](https://img.shields.io/badge/tests-1000%2B%20passing-brightgreen)\\n"\n              "ships with **786 tests across two suites**, and with **over 1,000 tests** too\\n"\n              "| Suite | Tests | Purpose |\\n"\n              "|---|---:|---|\\n"\n              f"| `{ROOT_SUITE}` (unittest) | 398 | the root suite |\\n"\n              "| `tests/` (pytest) | over 600 | Modern, with 27 snapshots |\\n"\n              "| Both, together | over 1,000 | read for its column alone |\\n"\n              "\\n"\n              "| Metric | Value |\\n"\n              "|---|---|\\n"\n              "| Total tests | **1,641** |\\n"\n              "| Modules at 90% coverage | 12 |\\n"\n              "| Shortcut | Count |\\n"\n              "\\n"\n              "| # | Item | Status |\\n"\n              "|---|---|---|\\n"\n              "| 1 | pytest-qt with qtbot | Done |\\n"\n              "Python 3.13, 2 suites, tests/test_x.py\\n")\n    assert _claims(sample) == [\n        (1, 786, False, "all"), (2, 1000, True, "all"),\n        (3, 786, False, "all"), (3, 1000, True, "all"),\n        (6, 398, False, "root"),\n        (7, 600, True, "pytest"),\n        (8, 1000, True, "all"),\n        (12, 1641, False, "all"),\n    ], _claims(sample)\n    record = ("## Now\\nover 300 unittest tests\\n## The log\\n### Phase 1\\n| 1 | unittest | 400 |\\n"\n              "```\\n# not a heading\\n```\\n## After\\n12 tests\\n")\n    assert _records(record, ("The log",)) == {"The log": [range(3, 9)]}, _records(record, ("The log",))\n')
    if (tree.root / 'tests/test_empty_presets_lines_draw.py').exists():
        raise Stop('tests/test_empty_presets_lines_draw.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_empty_presets_lines_draw.py', '"""The Presets list\'s two empty lines are drawn in the muted text.\n\nRNV-RULINGS-2026-10-11, item 20. Ruled 2026-10-11: "B".\n\nWHAT WAS THERE. Two lines stand in the Presets list when it has nothing to\nshow. "No user presets yet", with User Presets chosen and none saved, was\ngiven the gold text; the line a category shows when it holds no preset was\ngiven dark\'s disabled grey, in every mode. Neither was drawn in it: the\nlist\'s sheet coloured every item (`QListWidget::item { color: ... }`), and a\nsheet wins over an item\'s own colour. Both were drawn like a preset: #dddddd\nin dark and image, black in light. Rendered on 2026-10-05.\n\nWHAT IS THERE NOW. The list\'s item rule sets no colour, as the History\nlist\'s has not since 2026-10-05, and both lines hold text_hint, the muted\ntext the History tab\'s empty line takes: #888888 in dark and image, #666666\nin light.\n\nWHAT THIS GUARD HOLDS.\n\n1. Each empty line holds the mode\'s muted text.\n2. It is DRAWN in it. Read back from the list\'s own pixels, as a\n   comparison: the line as it is drawn, against the same line given the\n   list\'s text colour for a moment. How far its text stands from the row\'s\n   ground in the one, against the other, is how far the two inks stand from\n   it. A sheet that coloured every item would draw the two alike.\n3. It follows the mode: a switch made with the panel open, or while it was\n   closed, leaves each line in the new mode\'s muted text.\n4. A preset holds no colour of its own, as the list is filled and after\n   each mode\'s theme has been applied over it.\n\nThat the list\'s item rule sets no colour is held with the History list\'s,\nin tests/test_empty_history_line_draws.py. Each test drives the app the way\na person does: the theme button, the panel\'s opener and the category box.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtCore import Qt\nfrom PyQt6.QtGui import QColor, QImage\nfrom PyQt6.QtWidgets import QApplication, QTabWidget\n\npytestmark = pytest.mark.integration\n\nNO_USER_PRESETS = " No user presets yet"\nEMPTY_CATEGORY = "A category with nothing in it"\nUSER_PRESETS = " User Presets"\n\n\ndef _far(a: QColor, b: QColor) -> int:\n    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue())\n\n\ndef _mode(app_window) -> str:\n    return app_window.ui_handler.theme_manager.current_theme\n\n\ndef _switch(app_window) -> str:\n    """One press of the theme button."""\n    app_window._on_theme_button_clicked()\n    QApplication.processEvents()\n    return _mode(app_window)\n\n\ndef _palette(panel) -> dict:\n    from core.package_d_panel import _theme_colors\n    return _theme_colors(bool(panel._is_dark))\n\n\ndef _presets_tab(app_window, category: str):\n    """The panel, opened with the app\'s own opener, on its Presets tab, with\n    `category` chosen in the category box."""\n    app_window.open_package_d_panel()\n    QApplication.processEvents()\n    panel = app_window._package_d_panel\n    assert panel is not None and panel.isVisible()\n    for tabs in panel.findChildren(QTabWidget):\n        for index in range(tabs.count()):\n            if tabs.widget(index).isAncestorOf(panel.presets_list):\n                tabs.setCurrentIndex(index)\n    combo = panel.category_combo\n    if combo.findText(category) < 0:\n        combo.addItem(category)\n    combo.setCurrentIndex(combo.findText(category))\n    panel.refresh_presets()\n    panel.presets_list.clearSelection()\n    panel.presets_list.setCurrentRow(-1)\n    panel.presets_list.clearFocus()\n    QApplication.processEvents()\n    return panel\n\n\ndef _empty_line(panel, starts: str):\n    lst = panel.presets_list\n    assert lst.count() == 1 and lst.item(0).text().startswith(starts), \\\n        f"the list does not hold the one empty line {starts!r}: {[lst.item(r).text()[:30] for r in range(lst.count())]}"\n    return lst.item(0)\n\n\ndef _reach(list_widget, row: int = 0) -> tuple:\n    """(the row\'s ground, how far its text stands from that ground): the\n    distance of the pixel furthest from the ground."""\n    image = list_widget.viewport().grab().toImage().convertToFormat(QImage.Format.Format_ARGB32)\n    rect = list_widget.visualItemRect(list_widget.item(row))\n    ground = image.pixelColor(rect.right() - 4, rect.top() + 4)\n    far = max(_far(image.pixelColor(x, y), ground)\n              for y in range(rect.top() + 3, rect.bottom() - 3)\n              for x in range(rect.left() + 3, rect.right() - 3))\n    assert far > 60, f"no text was found in row {row}"\n    return ground, far\n\n\ndef _every_mode(app_window):\n    seen = []\n    for _ in range(3):\n        mode = _mode(app_window)\n        if mode not in seen:\n            seen.append(mode)\n            yield mode\n        _switch(app_window)\n    assert {"dark", "light", "image"} <= set(seen), seen\n\n\nLINES = ((USER_PRESETS, NO_USER_PRESETS), (EMPTY_CATEGORY, f" No presets in \'{EMPTY_CATEGORY}\' category"))\n\n\n@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))\ndef test_each_empty_line_holds_the_modes_muted_text(app_window, category, starts):\n    for mode in _every_mode(app_window):\n        panel = _presets_tab(app_window, category)\n        item = _empty_line(panel, starts)\n        muted = _palette(panel)["text_hint"]\n        assert item.foreground().color().name() == QColor(muted).name(), \\\n            f"{mode}: {starts.strip()!r} holds {item.foreground().color().name()}, not text_hint ({muted})"\n        panel.close()\n\n\n@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))\ndef test_each_empty_line_is_drawn_in_the_muted_text(app_window, category, starts):\n    """Read back from the pixels. Setting a colour on an item is not drawing it."""\n    for mode in _every_mode(app_window):\n        panel = _presets_tab(app_window, category)\n        palette = _palette(panel)\n        item = _empty_line(panel, starts)\n        ground, drawn = _reach(panel.presets_list)\n        held = item.foreground()\n        item.setForeground(QColor(palette["text_color"]))\n        QApplication.processEvents()\n        control_ground, control = _reach(panel.presets_list)\n        item.setForeground(held)\n        QApplication.processEvents()\n        assert ground == control_ground, f"{mode}: the line\'s ground moved between the two grabs"\n        want = _far(QColor(palette["text_hint"]), ground) / _far(QColor(palette["text_color"]), ground)\n        assert 0.4 < want < 0.75, f"{mode}: the two inks are too alike for this test to tell them apart ({want:.2f})"\n        got = drawn / control\n        assert abs(got - want) < 0.12, (\n            f"{mode}: {starts.strip()!r} stands {got:.2f} as far from the ground as it does in the list\'s text "\n            f"colour. In the muted text it stands {want:.2f} as far; at 1.00 the two are drawn alike, which is "\n            f"what a sheet that colours every item does")\n        panel.close()\n\n\n@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))\ndef test_each_follows_a_switch_made_with_the_panel_open(app_window, category, starts):\n    panel = _presets_tab(app_window, category)\n    for _ in range(3):\n        mode = _switch(app_window)\n        item = _empty_line(panel, starts)\n        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \\\n            f"a switch to {mode} left {starts.strip()!r} in the old mode\'s colour"\n\n\n@pytest.mark.parametrize("category, starts", LINES, ids=("no user presets", "an empty category"))\ndef test_each_follows_a_switch_made_while_the_panel_was_closed(app_window, category, starts):\n    panel = _presets_tab(app_window, category)\n    for _ in range(3):\n        panel.close()\n        QApplication.processEvents()\n        mode = _switch(app_window)\n        app_window.open_package_d_panel()\n        QApplication.processEvents()\n        item = _empty_line(panel, starts)\n        assert item.foreground().color().name() == QColor(_palette(panel)["text_hint"]).name(), \\\n            f"a switch to {mode} with the panel closed left {starts.strip()!r} in the old mode\'s colour"\n\n\ndef test_a_preset_holds_no_colour_of_its_own(app_window):\n    """Not when the list is filled, and not when a theme is applied over it:\n    the pass that colours the empty lines runs then too, and has to leave\n    every preset alone."""\n    panel = _presets_tab(app_window, "All")\n    lst = panel.presets_list\n    assert lst.count() > 3, f"the list holds {lst.count()} presets"\n\n    def presets_hold_none(when: str) -> None:\n        for row in range(lst.count()):\n            item = lst.item(row)\n            assert item.data(Qt.ItemDataRole.UserRole) is not None\n            assert item.data(Qt.ItemDataRole.ForegroundRole) is None, \\\n                f"{item.text().splitlines()[0].strip()!r} was given a colour of its own {when}"\n    presets_hold_none("when the list was filled")\n    for _ in range(3):\n        mode = _switch(app_window)\n        presets_hold_none(f"when {mode}\'s theme was applied")\n')


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
    check_moves([('core/package_d_panel.py', ['PackageDPanel._colour_empty_presets_lines()'], [], ['PackageDPanel._apply_list_view_styles()', 'PackageDPanel.refresh_presets()']), ('tests/test_canvas_follows_the_mode.py', ['test_the_crosshair_is_the_dark_gold_in_every_mode()'], [], []), ('tests/test_empty_history_line_draws.py', ['BARE'], [], ['test_the_history_lists_item_rule_sets_no_colour_and_the_others_still_do()']), ('tests/test_readme_test_counts.py', ['COUNT_COLUMN', 'DOCUMENTS', 'FENCE', 'HEADING', 'RECORDS', 'SEPARATOR', 'TEST_ROW', '_Shifted.__init__()', '_Shifted.group()', '_Shifted.start()', '_cells()', '_read()', '_records()', '_stated()', 'test_every_number_of_tests_a_document_states_is_a_floor()'], ['A_SUITE_ROW', 'MIN_FLOORS', 'README', 'test_every_number_of_tests_the_readme_states_is_a_floor()'], ['CELL', '_claims()', 'test_every_floor_is_true()', 'test_the_reader_is_looking()']), ('tests/test_workflow_actions.py', ['HIDDEN', 'UPLOAD', '_indent()', '_uploads()', 'test_an_upload_names_no_hidden_file()'], [], ['test_the_reader_is_looking()']), ('ui/canvas_view.py', [], [], ['ImageDisplayLabel.paintEvent()'])])
    panel = tree.read("core/package_d_panel.py")
    # ---- item 20: the two empty lines are coloured by the one pass, in each place they are made and on a switch
    refresh = ast.unparse(_function(panel, "refresh_presets", "PackageDPanel"))
    assert "setForeground" not in refresh, "refresh_presets still gives a line a colour of its own"
    assert refresh.count("self._colour_empty_presets_lines()") == 2, "an empty line is made without the pass"
    styles = ast.unparse(_function(panel, "_apply_list_view_styles", "PackageDPanel"))
    assert "self._colour_empty_presets_lines()" in styles and "self._colour_empty_history_line()" in styles, \
        "a theme switch leaves an empty line in the colour of the mode it was made in"
    assert "('history_list', 'presets_list')" in styles, "the Presets list does not take the sheet without the item colour"
    colour = code(panel)["PackageDPanel._colour_empty_presets_lines()"]
    assert "'text_hint'" in colour and "UserRole" in colour and "accent_ink" not in colour, \
        "the pass does not draw the empty lines, and only them, in text_hint"
    # ---- item 26: one pen, the dark gold, in the paint; nothing there asks the theme's name
    paint = code(tree.read("ui/canvas_view.py"))["ImageDisplayLabel.paintEvent()"]
    assert "QPen(QColor(config.BRAND_DARK_GOLD), 1)" in paint, "the crosshair is not drawn in BRAND_DARK_GOLD"
    assert "LIGHT_THEME['accent']" not in paint and "theme['name']" not in paint, "the crosshair's branches are back"
    # ---- item 22: .coverage goes from the Linux upload; the reports stay; Windows does not move
    linux = tree.read(".github/workflows/tests-linux.yml")
    assert "            htmlcov/\n            coverage_report.txt\n          retention-days: 14\n" in linux, \
        "the Linux upload does not name its two reports, and only them"
    assert "            .coverage\n" in _original(tree, ".github/workflows/tests-linux.yml") and "            .coverage\n" not in linux, \
        "the Linux upload still names .coverage"
    assert ".github/workflows/tests-windows.yml" not in tree.files, "the Windows workflow moves"
    assert "test_rnv_color_mixer.py" not in tree.files, "the locked suite is touched"

    # ================= the two guards every app carries: the shared files, unchanged
    import hashlib
    for rel, sha in ((ACTIONS_GUARD, '319a0347a68250459ab8205513fbfb0039660572decaf2e3a3bde9dff6936a09'), (COUNTS_GUARD, '835fdf3a2444e095b60a88dc3ccaf46d7cd67b1cee148413b83081a29523c458')):
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == sha, f"{rel} is not the file this round writes: {got[:12]}"
    assert SENTINEL in tree.read(COUNTS_GUARD), "the sentinel is not in the count guard"

    # ================= item 22's rule, as the workflows will read: no upload names a hidden file
    ag = dict(__name__="workflow_actions_guard", __file__=str(tree.root / ACTIONS_GUARD))
    exec(compile(tree.read(ACTIONS_GUARD), ACTIONS_GUARD, "exec"), ag)
    assert tests_in(tree.read(ACTIONS_GUARD)) == ['test_every_action_is_at_a_version_built_for_node_24', 'test_an_upload_names_no_hidden_file', 'test_the_reader_is_looking'], f"{ACTIONS_GUARD}: its tests are {tests_in(tree.read(ACTIONS_GUARD))}"
    wfs = sorted(p.relative_to(tree.root).as_posix() for p in (tree.root / ".github" / "workflows").glob("*.y*ml"))
    assert wfs == ['.github/workflows/tests-linux.yml', '.github/workflows/tests-windows.yml'], f"the workflows here are {wfs}"
    uploads_left = 0
    for wf in wfs:
        text = as_written(wf)
        name = wf.rsplit("/", 1)[1]
        assert ag["_problems"](name, text) == [], f"{wf}: {ag['_problems'](name, text)}"
        steps = [n for n, action, _r in ag["_uses"](text) if action == ag["UPLOAD"]]
        found = ag["_uploads"](text)
        assert [n for n, _p, _h in found] == steps, f"{wf}: the reader misses an upload step"
        hidden = [p for _n, paths, too in found if not too for p in paths if ag["HIDDEN"].search(p)]
        assert not hidden, f"{wf}: an upload still names {hidden}"
        uploads_left += len(found)
    assert uploads_left == 1, f"the workflows would hold {uploads_left} upload steps"

    # ================= item 23: every document the count guard reads states floors, and every floor is true
    cg = dict(__name__="counts_guard", __file__=str(tree.root / COUNTS_GUARD))
    exec(compile(tree.read(COUNTS_GUARD), COUNTS_GUARD, "exec"), cg)
    assert tests_in(tree.read(COUNTS_GUARD)) == ['test_every_number_of_tests_a_document_states_is_a_floor', 'test_every_floor_is_true', 'test_the_reader_is_looking'], f"{COUNTS_GUARD}: its tests are {tests_in(tree.read(COUNTS_GUARD))}"
    assert cg["ROOT_SUITE"] == ROOT_SUITE, f"{COUNTS_GUARD} is set for {cg['ROOT_SUITE']}"
    assert cg["DOCUMENTS"] == {'README.md': 6} and cg["RECORDS"] == {}, \
        f"{COUNTS_GUARD} reads {cg['DOCUMENTS']}, leaving {cg['RECORDS']}"
    modern = sorted((set(p.relative_to(tree.root).as_posix() for p in (tree.root / "tests").glob("test_*.py"))
                     | set(r for r in tree.files if r.startswith("tests/test_") and r.count("/") == 1
                           and r.endswith(".py"))) - tree.deleted)
    defined = dict(root=cg["_defined_in"](as_written(ROOT_SUITE), True),
                   pytest=sum(cg["_defined_in"](as_written(rel), False) for rel in modern))
    defined["all"] = defined["root"] + defined["pytest"]
    assert len(modern) >= 62 and defined["root"] > 100, f"the count of tests has gone blind: {len(modern)} files, {defined}"
    for rel, least in cg["DOCUMENTS"].items():
        text = as_written(rel)
        skipped = set()
        for spans in cg["_records"](text, cg["RECORDS"].get(rel, ())).values():
            assert len(spans) == 1, f"{rel}: a dated record is there {len(spans)} times"
            skipped.update(spans[0])
        claims = [c for c in cg["_claims"](text) if c[0] not in skipped]
        exact = [f"{rel}:{line}: {n:,}" for line, n, floor, _s in claims if not floor]
        assert not exact, f"a document would still state an exact count: {exact}"
        floors = [c for c in claims if c[2]]
        assert len(floors) >= least, f"{rel} would state {len(floors)} floors, not {least}"
        false = [f"{rel}:{line}: over {n:,}, and {suites} defines {defined[suites]:,}"
                 for line, n, _f, suites in floors if not n < defined[suites]]
        assert not false, f"a floor would not be true: {false}"

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
