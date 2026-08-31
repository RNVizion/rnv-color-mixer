#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Reclassify three rnv-color-mixer neutrals from app-owned to mirrored, and
correct the three docstrings that argued they were not.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES: NOTHING. Not one rendered pixel, and only one line of the palettes.

This app already NAMED these three values -- the 2026-08-29 pass did that. What
it could not do was classify them correctly, because the register had not yet
ruled. It has:

    APP_CANVAS_DARK       #0a0a0a  ->  APP["canvas"]       rev 22
    APP_PANEL_HOVER_DARK  #3a3a3a  ->  APP["panel-hover"]  rev 22
    APP_ITEM_HOVER_LIGHT  #eeeeee  ->  APP["hover-light"]  rev 23

So the change is provenance: three entries in PINNED, three in MIRRORS, and
three docstrings that currently say the opposite of what is now true.

THE DOCSTRINGS ARE THE POINT OF THIS PASS, NOT A SIDE EFFECT

    APP_CANVAS_DARK says  "NOT A BRAND VALUE ... #0a0a0a is app-owned."
    APP_PANEL_HOVER_DARK  "that ladder is not published ... two rungs are in
                           use and two are not. Named as an app value until
                           the register rules it."

Both were accurate when written and both are now false. A wrong docstring
beside a right value is worse than no docstring: it is evidence, and the next
person to read it will believe it. This programme has already been bitten once
by a guard docstring that described the wrong app's history and passed every
test, because nothing checks prose.

The ladder claim was wrong in an instructive way. It treated APP["border"]
#333333 as a missing rung of the surface ladder. #333333 is grey(3) on the INK
grid, which governs inks and EDGES -- a border is an edge, and was never a rung.
Two families compared to each other. The ladder was complete when the doubt was
first written down.

ONE SUBSTITUTION

    LIGHT_THEME  panel_hover  '#eeeeee'  ->  APP_ITEM_HOVER_LIGHT

It is the same value; the constant already existed and already held it. The
literal was the last place in the light palette that spelled the plate out.

A COINCIDENCE, NAMED

APP_HANDLE_HOVER_DARK is also #eeeeee, and it is NOT the register's plate. It
is the dark slider handle when hovered -- grey(14) on the ink grid, one step
above APP_TEXT_DARK at grey(13), doing an INK job in a DARK palette. The
register's hover-light is a LIGHT SURFACE. grey(14) is reachable from both
families, which is exactly the coincidence the published grid makes possible.
It is recorded in tests/test_ladder_and_plate.py and asserted in both
directions: one that stops coinciding fails, and so does one that turns out to
be mirrored after all.

WHY THE PLATE IS #eeeeee AND NOT #e8e8e8

#e8e8e8 is the ground BRAND_DARK_GOLD_DEEP is calibrated against -- the
smallest uniform step that clears it is -14, and -13 gives 4.4675 and fails.
rev 24 registered that role as GOLD_TEXT_GROUND_FLOOR. A hover plate on that
value clears the 4.5 floor by 0.0334 and fails the moment the gold moves.
#eeeeee is grey(14), one step inside, and clears by 0.2875.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
DESCRIPTION = "reclassify three neutrals as mirrored, and fix their docstrings"
SENTINEL_FILE = "utils/config.py"
SENTINEL = "APP_ITEM_HOVER_LIGHT,"
MIRROR = "tests/test_app_mirror.py"
GUARD = "tests/test_ladder_and_plate.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_color_mixer"]),
]

#: palette -> {value: constant}. An ALLOWLIST, not a sweep.
SUBSTITUTE = {"LIGHT_THEME": {"#eeeeee": "APP_ITEM_HOVER_LIGHT"}}
EXPECTED_SUBS = 1

#: The palettes are class attributes of ThemeManager, so they are indented.
ALL_DICTS = ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME")

OLD_CANVAS_DOC = '"""The ground BELOW the panel in dark and image: the mixing canvas, and the\nselected tab, which sits flush with it.\n\nUnnamed until 2026-08-29 because the 2026-08-27 rewire\'s scope was the three\nstylesheet templates and this value has never appeared in one -- it is reached\nonly through ThemeManager\'s dicts, which seven modules build their own QSS\nfrom.\n\nNOT A BRAND VALUE, and worth saying so here because it was briefly mistaken\nfor one. #0a0a0a is app-owned. The register\'s canvas is WEB_BLACK #0a0a0f, one\nbyte away in the blue channel alone, and a rule derived from the resemblance\nwould have pinned fifteen light uses to a colour the register does not hold.\nSee rnv-brand@8ab1174 BRAND_COLORS.md:270."""'
NEW_CANVAS_DOC = '"""engine/brand.py APP["canvas"]. The ground BELOW the panel in dark and image:\nthe mixing canvas, and the selected tab, which sits flush with it.\n\nUnnamed until 2026-08-29 because the 2026-08-27 rewire\'s scope was the three\nstylesheet templates and this value has never appeared in one -- it is reached\nonly through ThemeManager\'s dicts, which seven modules build their own QSS\nfrom.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22, and app-owned here until then. It is\nthe n=-1 rung of the dark surface ladder:\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nSTILL NOT WEB_BLACK, and the distinction is now sharper rather than gone. This\ndocstring used to say "#0a0a0a is app-owned; the register\'s canvas is WEB_BLACK\n#0a0a0f". The second half was the part that mattered and it survives: the web\nground is a different value, one byte away in the blue channel alone. App\nneutrals are pure grey, R = G = B, without exception, and the web carries a\ntint the apps do not. That byte is why invert(#0a0a0a) = #f5f5f5 once looked\nlike a light-ground rule and was not -- the register\'s canvas inverts to\n#f5f5f0. Two canvases one byte apart, deliberately.\n\nMIRRORED, not app-owned -- pinned in tests/test_app_mirror.py alongside the\nother register values, so a move upstream is caught here."""'
OLD_HOVER_DOC = '"""Panel hover in dark and image. One step above APP_CARD_DARK on the 0x10\nsurface spacing, though that ladder is not published: rnv-brand@8ab1174 notes\nit yields #3a3a3a while APP["border"] is #333333, so two rungs are in use and\ntwo are not. Named as an app value until the register rules it."""'
NEW_HOVER_DOC = '"""engine/brand.py APP["panel-hover"]. Panel hover in dark and image, and the\nn=+2 rung of the dark surface ladder.\n\nREGISTERED 2026-08-29 in rnv-brand rev 22. THE REGISTER RULED IT, AND THE\nDOUBT THIS DOCSTRING USED TO RECORD WAS MISPLACED. It said the ladder was not\npublished because "it yields #3a3a3a while APP["border"] is #333333, so two\nrungs are in use and two are not" -- treating the border as a missing rung.\nIt is not a rung at all. #333333 is grey(3) on the INK grid, which governs inks\nand EDGES, and a border is an edge. The two families were being compared to\neach other. The ladder was complete the whole time:\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nMIRRORED, not app-owned -- pinned in tests/test_app_mirror.py."""'
OLD_ITEM_DOC = '"""Combo-box item under the cursor, light. The list hover, not the button\nhover -- those are different schemes, see APP_BTN_HOVER_INVERSE."""'
NEW_ITEM_DOC = '"""engine/brand.py APP["hover-light"]. grey(14). The light interaction plate:\nthe combo-box item under the cursor and the panel hover. The LIST hover, not\nthe button hover -- those are different schemes, see APP_BTN_HOVER_INVERSE.\n\nREGISTERED 2026-08-30 in rnv-brand rev 23. It was registered a day earlier as\n#e8e8e8 and moved here before any app was wired to it, because #e8e8e8 is the\nground BRAND_DARK_GOLD_DEEP is calibrated against -- rev 24 registered that\nrole as GOLD_TEXT_GROUND_FLOOR. A plate on the value the gold is pinned to\nclears the 4.5 text floor by 0.0334 and fails the moment the gold moves one\nstep. This value clears by 0.2875. A boundary is not a plate.\n\nTHE NAME STAYS AS IT IS. This app names neutrals by role AND mode because it\nregisters a light set beside the dark one, and tests/test_app_mirror.py maps\nthose names to register keys explicitly rather than renaming eleven constants\nto fit a convention that would then be wrong within this file. The mirror is\nwhat carries the ownership, not the spelling.\n\nMIRRORED, not app-owned -- pinned in tests/test_app_mirror.py."""'
OLD_HANDLE_DOC = '"""Slider handle when hovered, dark and image. One step above the\ntext: grey(14), where APP_TEXT_DARK is grey(13), on the published\nink grid. Held #f0f0f0 until 2026-08-28, when the gap to #e0e0e0 was\n0x10 -- the surface ladder step, not the grid step -- and the\nsentence was true by accident."""'
NEW_HANDLE_DOC = '"""Slider handle when hovered, dark and image. One step above the\ntext: grey(14), where APP_TEXT_DARK is grey(13), on the published\nink grid. Held #f0f0f0 until 2026-08-28, when the gap to #e0e0e0 was\n0x10 -- the surface ladder step, not the grid step -- and the\nsentence was true by accident.\n\nAPP-OWNED, AND IT SHARES A HEX WITH APP_ITEM_HOVER_LIGHT. Both are #eeeeee and\nthey are not the same thing: that one is APP["hover-light"], a LIGHT surface\nthe register owns; this is a DARK handle, an ink-grid step doing an ink job.\ngrey(14) is reachable from both families, which is exactly the sort of\ncoincidence the ink grid makes possible and the reason it has to be named\nrather than noticed. If the register moves the light plate, this must NOT\nfollow. tests/test_ladder_and_plate.py asserts the coincidence in both\ndirections."""'
PINNED = "    'APP_CANVAS_DARK': '#0a0a0a',\n    'APP_PANEL_HOVER_DARK': '#3a3a3a',\n    'APP_ITEM_HOVER_LIGHT': '#eeeeee',\n"
MIRRORS = "    'APP_CANVAS_DARK': ('APP', 'canvas'),\n    'APP_PANEL_HOVER_DARK': ('APP', 'panel-hover'),\n    'APP_ITEM_HOVER_LIGHT': ('APP', 'hover-light'),\n"

EXPECTED_ADDED = {
    SENTINEL_FILE: (NEW_CANVAS_DOC.count("\n") - OLD_CANVAS_DOC.count("\n")
                    + NEW_HOVER_DOC.count("\n") - OLD_HOVER_DOC.count("\n")
                    + NEW_ITEM_DOC.count("\n") - OLD_ITEM_DOC.count("\n")
                    + NEW_HANDLE_DOC.count("\n") - OLD_HANDLE_DOC.count("\n")),
    MIRROR: PINNED.count("\n") + MIRRORS.count("\n"),
}


def _resolve(source: str) -> dict:
    """Every palette, resolved to plain values, whether an entry is written as
    a literal or a name. This is what makes "nothing moved" checkable."""
    tree = ast.parse(source.lstrip("\ufeff"))
    consts = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                consts[target.id] = node.value.value
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = getattr(target, "id", None)
            if name in ALL_DICTS and isinstance(node.value, ast.Dict):
                palette = {}
                for key, value in zip(node.value.keys, node.value.values):
                    if not isinstance(key, ast.Constant):
                        continue
                    if isinstance(value, ast.Constant):
                        palette[key.value] = value.value
                    elif isinstance(value, ast.Name):
                        palette[key.value] = consts.get(value.id, f"<{value.id}>")
                    else:
                        palette[key.value] = ast.unparse(value)
                out[name] = palette
    return out


def _bounds(lines):
    """The palettes carry identically-spelled key lines, so a plain string
    replace cannot tell dark from light. Every edit is scoped to its own.
    These are class attributes, hence the leading indent in the pattern."""
    starts = {}
    pattern = re.compile(r"^\s+(" + "|".join(ALL_DICTS) + r")\s*[:=]")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            starts[m.group(1)] = i
    if len(starts) != len(ALL_DICTS):
        raise SystemExit(f"expected {len(ALL_DICTS)} palettes, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def edits(tree) -> None:
    # The docstrings first. Each is matched whole, so a file that has moved
    # underneath this script fails here rather than editing the wrong prose.
    tree.sub(SENTINEL_FILE, OLD_CANVAS_DOC, NEW_CANVAS_DOC)
    tree.sub(SENTINEL_FILE, OLD_HOVER_DOC, NEW_HOVER_DOC)
    tree.sub(SENTINEL_FILE, OLD_ITEM_DOC, NEW_ITEM_DOC)
    tree.sub(SENTINEL_FILE, OLD_HANDLE_DOC, NEW_HANDLE_DOC)

    source = tree.read(SENTINEL_FILE)
    lines = source.splitlines(keepends=True)
    bounds = _bounds(lines)
    swapped = 0
    for dict_name, table in SUBSTITUTE.items():
        start, end = bounds[dict_name]
        for i in range(start, end):
            line = lines[i]
            # Match the line WITHOUT its ending and put the ending back
            # verbatim. Python's `$` also matches just before a trailing
            # newline, so a pattern ending in `(,.*)$` silently drops it, and
            # the result is still valid Python -- every test passes while the
            # palette is reflowed onto one line.
            body = line.rstrip("\r\n")
            ending = line[len(body):]
            m = re.match(r"^(\s*'[a-z_0-9]+':\s*)'(#[0-9a-fA-F]{6})'(,.*)$", body)
            if not m:
                continue
            const = table.get(m.group(2).lower())
            if const:
                lines[i] = f"{m.group(1)}{const}{m.group(3)}{ending}"
                swapped += 1
    if swapped != EXPECTED_SUBS:
        raise SystemExit(f"expected {EXPECTED_SUBS} substitution, made "
                         f"{swapped}. Re-derive this script before trusting it.")
    tree.write(SENTINEL_FILE, "".join(lines))
    print(f"  substituted {swapped} literal for its name")

    tree.sub(MIRROR, "    'APP_CARD_DARK': '#2a2a2a',\n",
             "    'APP_CARD_DARK': '#2a2a2a',\n" + PINNED)
    tree.sub(MIRROR, "    'APP_CARD_DARK': ('APP', 'card'),\n",
             "    'APP_CARD_DARK': ('APP', 'card'),\n" + MIRRORS)


def checks(tree) -> None:
    for rel, added in EXPECTED_ADDED.items():
        before = (Path.cwd() / rel).read_text(encoding="utf-8-sig")
        after = tree.read(rel)
        delta = after.count("\n") - before.count("\n")
        if delta != added:
            raise SystemExit(
                f"{rel} changed shape by {delta} lines; this pass adds exactly "
                f"{added}. A substitution that eats or adds a line ending "
                f"leaves every value identical and every test green.")

    original = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    edited = tree.read(SENTINEL_FILE)

    before, after = _resolve(original), _resolve(edited)
    if set(before) != set(after):
        raise SystemExit(f"a palette appeared or vanished: {set(before) ^ set(after)}")
    moved = []
    for name in before:
        for key in set(before[name]) | set(after[name]):
            was, now = before[name].get(key), after[name].get(key)
            if was != now:
                moved.append(f"{name}[{key!r}]: {was} -> {now}")
    if moved:
        raise SystemExit("THIS PASS MUST NOT MOVE A VALUE, and it moved these:\n  "
                         + "\n  ".join(moved))

    # The three constants keep their values. This pass changes what is SAID
    # about them, and a docstring edit that also moved a value would be the
    # worst possible outcome of a pass whose whole subject is provenance.
    for name, want in (("APP_CANVAS_DARK", "#0a0a0a"),
                       ("APP_PANEL_HOVER_DARK", "#3a3a3a"),
                       ("APP_ITEM_HOVER_LIGHT", "#eeeeee"),
                       ("APP_HANDLE_HOVER_DARK", "#eeeeee")):
        if f'{name}: Final[str] = "{want}"' not in edited:
            raise SystemExit(f"{name} is no longer {want} in the edited file")

    # The claims this pass exists to remove must actually be gone.
    for stale in ("NOT A BRAND VALUE", "that ladder is not published",
                  "Named as an app value until the register rules it"):
        if stale in edited:
            raise SystemExit(
                f"the edited file still says {stale!r}. Three values have been "
                f"reclassified as mirrored; prose that contradicts that is "
                f"evidence pointing the wrong way.")

    # ... and the sweep that finds them must still be able to see. A negative
    # check with nothing proving it is looking passes on an empty file.
    if "WEB_BLACK" not in edited:
        raise SystemExit("the canvas docstring no longer mentions WEB_BLACK; "
                         "the seam between #0a0a0a and #0a0a0f is the part of "
                         "that note worth keeping")

    if SENTINEL not in edited:
        raise SystemExit(f"expected {SENTINEL!r} in the edited palette")


GUARD_SOURCE = '"""Three neutrals reclassified from app-owned to mirrored, and one deliberate\ncoincidence that must not join them.\n\nWHAT THIS PASS DID. This app already NAMED these values -- the 2026-08-29 pass\ndid that. What it could not do was classify them, because the register had not\nruled. rnv-brand rev 22 registered APP["canvas"] #0a0a0a and\nAPP["panel-hover"] #3a3a3a; rev 23 registered APP["hover-light"] #eeeeee. So\nthe change is provenance, and the docstrings that argued the other way.\n\n    BRAND_BLACK + n * 0x10,  n in -1..+2\n    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover\n\nWHY THE LADDER LOOKED INCOMPLETE. The register had called it "two-thirds\nspecified" because APP["border"] #333333 is not #3a3a3a, treating the border as\na missing rung. It is not a rung: #333333 is grey(3) on the INK grid, which\ngoverns inks and EDGES. Two families compared to each other.\n\nTHE COINCIDENCE. APP_HANDLE_HOVER_DARK is also #eeeeee. It is the dark slider\nhandle when hovered -- grey(14) on the ink grid, one step above APP_TEXT_DARK\nat grey(13), doing an ink job in a dark palette. APP["hover-light"] is a LIGHT\nSURFACE. grey(14) is reachable from both families, which is the sort of\ncoincidence a published grid makes possible, and it must be named rather than\nnoticed.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\n\nimport pytest\n\nfrom utils import config\nfrom utils.config import ThemeManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \'utils\' / \'config.py\'\n\nGRID_STEP = 0x11\nLADDER_STEP = 0x10\nTEXT_FLOOR = 4.5\n\n#: Constant -> (register dict, key, the value both hold). This app names its\n#: neutrals by role AND mode because it registers a light set beside the dark\n#: one, so the APP_<KEY> convention the other apps resolve by does not apply --\n#: the map is explicit, exactly as tests/test_app_mirror.py does it.\nNEW = {\n    \'APP_CANVAS_DARK\': (\'canvas\', \'#0a0a0a\'),\n    \'APP_PANEL_HOVER_DARK\': (\'panel-hover\', \'#3a3a3a\'),\n    \'APP_ITEM_HOVER_LIGHT\': (\'hover-light\', \'#eeeeee\'),\n}\n\n#: dict NAME -> the live palette.\nPALETTES = {\'DARK_THEME\': ThemeManager.DARK_THEME,\n            \'LIGHT_THEME\': ThemeManager.LIGHT_THEME,\n            \'IMAGE_THEME\': ThemeManager.IMAGE_THEME}\n\n#: App-owned values that DELIBERATELY share a hex with a register entry.\n#: Sharing a VALUE is not playing the same ROLE, and a value check cannot tell\n#: the difference -- so the intentional ones are named here, with what they\n#: share and why they must NOT follow if the register moves.\n#:\n#: name -> (register key, why it is not the same role)\nCOINCIDENT = {\n    \'APP_HANDLE_HOVER_DARK\': (\n        \'hover-light\',\n        \'Both are #eeeeee. The register entry is a LIGHT SURFACE -- the \'\n        \'interaction plate a light-mode control hovers to. This is the DARK \'\n        \'slider handle when hovered: an ink-grid step, grey(14), one above \'\n        \'APP_TEXT_DARK at grey(13), drawn on a dark ground. Different mode, \'\n        \'different family, different job. grey(14) is simply reachable from \'\n        \'both. If APP["hover-light"] moves off grey(14) this must NOT follow \'\n        \'it, which is why it is named here rather than mirrored.\'),\n}\n\n#: The value the plate is NOT, and the reason the distinction is worth a test.\nFLOOR = \'#e8e8e8\'\n\n\ndef grey(n: int) -> str:\n    v = n * GRID_STEP\n    return \'#%02x%02x%02x\' % (v, v, v)\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef _palette_node(name: str) -> ast.Dict:\n    tree = ast.parse(SRC.read_text(encoding=\'utf-8-sig\'))\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(target, \'id\', None) == name and isinstance(node.value, ast.Dict):\n                return node.value\n    raise AssertionError(f\'{name} is not a dict literal in utils/config.py\')\n\n\ndef _entry(node: ast.Dict, key: str):\n    for k, v in zip(node.keys, node.values):\n        if isinstance(k, ast.Constant) and k.value == key:\n            return v\n    return None\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_everything_this_file_reads_still_exists():\n    """Renaming a constant must fail loudly here rather than let the rest of\n    this file pass quietly over nothing."""\n    for name in list(NEW) + list(COINCIDENT):\n        assert hasattr(config, name), f\'utils.config has no {name}\'\n    for dict_name, live in PALETTES.items():\n        assert live, f\'{dict_name} is empty\'\n\n\n# ------------------------------------------------------------------ the values\n\ndef test_the_reclassified_constants_still_hold_their_values():\n    """This pass changes what is SAID about three constants. If it moved one of\n    them, that would be the worst possible outcome of a provenance pass."""\n    drift = {n: getattr(config, n) for n, (_, v) in NEW.items()\n             if getattr(config, n) != v}\n    assert not drift, f\'values moved during a reclassification: {drift}\'\n\n\ndef test_the_reclassified_constants_match_rnv_brand():\n    """The upstream half. Skips where rnv-brand is not importable, which is why\n    tests/test_app_mirror.py pins the same three locally."""\n    brand = pytest.importorskip(\n        \'engine.brand\',\n        reason=\'rnv-brand not importable here; the local pin is doing the work\')\n    drift = []\n    for name, (key, _) in NEW.items():\n        theirs, mine = brand.APP[key], getattr(config, name)\n        if mine.lower() != theirs.lower():\n            drift.append(f\'{name}: ours {mine}, theirs APP[{key!r}] {theirs}\')\n    assert not drift, \'drift from rnv-brand:\\n  \' + \'\\n  \'.join(drift)\n\n\ndef test_all_three_are_pinned_and_mirrored():\n    """The reclassification IS the two tables. A docstring saying a value is\n    mirrored, with no entry making it so, is the failure this pass is fixing in\n    the opposite direction."""\n    mirror = pathlib.Path(__file__).with_name(\'test_app_mirror.py\')\n    source = mirror.read_text(encoding=\'utf-8\')\n    for name in NEW:\n        assert f"\'{name}\':" in source, (\n            f\'{name} is not in tests/test_app_mirror.py. It is declared \'\n            f\'mirrored in its docstring; without a PINNED and a MIRRORS entry \'\n            f\'that claim is decorative.\')\n\n\n# ------------------------------------------------------------------ the ladder\n\ndef test_the_dark_rungs_are_exact_steps_on_the_ladder():\n    """BRAND_BLACK + n * 0x10. Two of these were app-owned on the argument that\n    the ladder might not be real. It is, and this is what says so."""\n    base = int(config.APP_SURFACE_DARK.lstrip(\'#\'), 16)\n    for n, name in ((-1, \'APP_CANVAS_DARK\'), (0, \'APP_SURFACE_DARK\'),\n                    (1, \'APP_CARD_DARK\'), (2, \'APP_PANEL_HOVER_DARK\')):\n        want = base + n * (LADDER_STEP * 0x010101)\n        assert int(getattr(config, name).lstrip(\'#\'), 16) == want, (\n            f\'{name} is {getattr(config, name)}, not rung n={n} of \'\n            f\'APP_SURFACE_DARK + n*0x10\')\n\n\ndef test_the_border_is_an_edge_and_not_a_rung():\n    """The distinction that made the ladder look incomplete for a week."""\n    assert config.APP_BORDER_DARK == grey(3)\n    base = int(config.APP_SURFACE_DARK.lstrip(\'#\'), 16)\n    rungs = {base + n * (LADDER_STEP * 0x010101) for n in range(-1, 3)}\n    assert int(config.APP_BORDER_DARK.lstrip(\'#\'), 16) not in rungs\n\n\ndef test_the_canvas_is_not_the_web_ground():\n    """One byte apart, deliberately. The docstring used to say #0a0a0a was\n    app-owned BECAUSE the register\'s canvas was WEB_BLACK. The first half is\n    now wrong and the second half was always the part that mattered."""\n    r, g, b = (int(config.APP_CANVAS_DARK.lstrip(\'#\')[i:i + 2], 16)\n               for i in (0, 2, 4))\n    assert r == g == b, f\'{config.APP_CANVAS_DARK} is not a pure grey\'\n    brand = pytest.importorskip(\'engine.brand\', reason=\'rnv-brand not importable\')\n    assert config.APP_CANVAS_DARK.lower() != brand.WEB_BLACK.lower()\n\n\n# ------------------------------------------------------------------- the plate\n\ndef test_the_plate_is_a_step_on_the_ink_grid():\n    assert config.APP_ITEM_HOVER_LIGHT == grey(14) == \'#eeeeee\'\n\n\ndef test_the_plate_is_not_the_gold_text_floor():\n    """Both clear the 4.5 floor. Only one clears it by enough to survive the\n    gold moving, and the other is the value the gold is calibrated against."""\n    gold = config.BRAND_DARK_GOLD_DEEP\n    here = _contrast(gold, config.APP_ITEM_HOVER_LIGHT)\n    edge = _contrast(gold, FLOOR)\n    assert config.APP_ITEM_HOVER_LIGHT.lower() != FLOOR\n    assert here - TEXT_FLOOR >= 0.2, (\n        f\'the plate clears the floor by only {here - TEXT_FLOOR:.4f}. The \'\n        f\'register moved APP["hover-light"] here for margin, not for a pass.\')\n    assert edge - TEXT_FLOOR < 0.05, (\n        f\'{FLOOR} now clears by {edge - TEXT_FLOOR:.4f}, so it is no longer the \'\n        f\'knife-edge this ruling was about. Either the gold moved or the floor \'\n        f\'did; re-derive before trusting the value above.\')\n\n\ndef test_the_light_panel_hover_names_the_plate():\n    """The last literal in the light palette that spelled the plate out. A\n    literal cannot follow its base."""\n    node = _palette_node(\'LIGHT_THEME\')\n    value = _entry(node, \'panel_hover\')\n    assert isinstance(value, ast.Name) and value.id == \'APP_ITEM_HOVER_LIGHT\', (\n        f\'LIGHT_THEME["panel_hover"] is \'\n        f\'{ast.unparse(value) if value else "missing"}, not the plate constant\')\n    assert ThemeManager.LIGHT_THEME[\'panel_hover\'] == config.APP_ITEM_HOVER_LIGHT\n\n\n# -------------------------------------------------------------- the coincidence\n\ndef test_every_coincidence_still_coincides():\n    """A named coincidence that no longer shares a value is a dead exemption,\n    and a dead exemption is a licence waiting for a defect: it would let a\n    genuinely misclassified value hide behind it."""\n    brand = pytest.importorskip(\'engine.brand\', reason=\'rnv-brand not importable\')\n    stale = []\n    for name, (key, _why) in COINCIDENT.items():\n        mine = getattr(config, name).lower()\n        theirs = brand.APP.get(key)\n        if theirs is None:\n            stale.append(f\'{name}: the register no longer holds APP[{key!r}]\')\n        elif mine != theirs.lower():\n            stale.append(f\'{name} = {mine} no longer matches APP[{key!r}] {theirs}\')\n    assert not stale, (\n        \'COINCIDENT entries that no longer describe reality:\\n  \'\n        + \'\\n  \'.join(stale)\n        + \'\\n\\nDelete the entry or correct it -- do not leave it standing.\')\n\n\ndef test_no_coincidence_is_also_mirrored():\n    """Guard the guard. The exemption is only for app-owned values; a name in\n    both tables would quietly exempt a mirrored value from its own mirror."""\n    for name in COINCIDENT:\n        assert name not in NEW, f\'{name} is both mirrored and exempt from the mirror\'\n    mirror = pathlib.Path(__file__).with_name(\'test_app_mirror.py\')\n    source = mirror.read_text(encoding=\'utf-8\')\n    for name in COINCIDENT:\n        assert f"\'{name}\':" not in source, (\n            f\'{name} is a named coincidence and is also pinned in \'\n            f\'test_app_mirror.py. It cannot be both.\')\n\n\ndef test_the_coincidence_is_in_the_other_mode():\n    """What actually separates the two: one is a light surface, the other a\n    dark ink. If the handle hover ever appears in a light palette, the reason\n    it is exempt has gone."""\n    for dict_name in (\'LIGHT_THEME\',):\n        for key, value in PALETTES[dict_name].items():\n            assert value != config.APP_HANDLE_HOVER_DARK or \\\n                value == config.APP_ITEM_HOVER_LIGHT, (\n                    f\'{dict_name}[{key!r}] carries the dark handle hover\')\n'


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

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
        return "fail"
    return "env"


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
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        raise SystemExit(f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
