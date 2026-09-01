#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Arm the other half of the gold rule in rnv-color-mixer.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

NO APPLICATION CODE CHANGES. One test file is replaced with a longer version
of itself. Nothing fails the new check today, in this app or in any of the
other four -- which is the reason to add it now rather than the reason not to.

THE RULE IS BIDIRECTIONAL AND THE GUARD WAS NOT

rnv-brand rev 25 published it in both directions:

    On a light ground, gold as TEXT is BRAND_DARK_GOLD_DEEP.
    Gold as a FILL or an EDGE is BRAND_DARK_GOLD.

The second sentence is not a stylistic preference, and the arithmetic is not
symmetric:

    text on #f5f5f5    BRAND_DARK_GOLD 4.1670 FAIL   DEEP 5.0949 pass
    text on #eeeeee    BRAND_DARK_GOLD 3.9156 FAIL   DEEP 4.7875 pass
    fill, black on it  BRAND_DARK_GOLD 4.6226 pass   DEEP 3.7806 FAIL

BRAND_DARK_GOLD carries text on pure white and on nothing else these apps use
as a surface. BRAND_DARK_GOLD_DEEP carries text everywhere and cannot be sat
on. A sweep that read the rule as "prefer DEEP" and replaced every
BRAND_DARK_GOLD would have fixed the text sites and broken the fills -- six of
the sites corrected across these repositories this week are fills and edges.

WHAT WAS ALREADY CHECKED, BY HAND

Every gold fill in all five apps, with the label drawn on it:

    rnv-text-transformer        4 sites   #ffffff throughout       5.5547
    rnv-color-picker            4 sites   inherited white          5.5547
    rnv-icon-builder            1 site    checkbox indicator, no text
    rnv-color-mixer             1 site    checkbox indicator, no text
    rnv-color-palette-manager   0 sites

Ten sites, zero failures. In this app: 1 site — a checkbox indicator, no text of its own.

WHY ADD A GUARD THAT PASSES

Because this is the only moment it is cheap. A guard proposed against a live
defect writes itself; a guard proposed against a clean sweep has to be argued
for, and the argument gets weaker every month the sweep stays clean. The
text direction was clean-looking too until somebody resolved the declarations
through the palettes, and then it was seven defects in three applications.

READING A FILL IS HARDER THAN READING TEXT, AND THE GUARD SAYS SO

Six of those ten sites declare no colour of their own -- a
`QPushButton:hover` that sets only a background takes its label from the base
`QPushButton` rule. The new sweep reads that enclosing rule rather than
guessing, and skips a site where it can find no label at all rather than
assuming one. A rule with no text (a checkbox indicator, a progress chunk)
is counted as unresolved, not as a pass.

And it carries a companion: test_the_fill_sweep_still_finds_things. A sweep
over a clean codebase and a sweep that resolves nothing file the same report,
and that assertion is the only thing that distinguishes them.
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
DESCRIPTION = "arm the fill direction of the gold rule"
SENTINEL_FILE = "tests/test_gold_as_text.py"
SENTINEL = "test_no_gold_fill_carries_a_label_below_the_floor"
GUARD = SENTINEL_FILE
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

#: This script EXTENDS a file an earlier script created, so "the sentinel file
#: is missing" almost always means the prerequisite has not been run -- not
#: that you are in the wrong directory. The default message says the second,
#: which is the more confusing of the two possibilities to be told when you
#: are standing in the right place.
MISSING_HELP = (
    f"{SENTINEL_FILE} is not here, so there is nothing to extend."
    f"\n\nThis script arms the FILL half of the gold rule in a guard that "
    f"the gold-text script installs. Run that one first:"
    f"\n\n    up-for-rnv-color-mixer-gold-text.py"
    f"\n\nthen this one. If you have already run it and the file is still "
    f"missing, you are not at the root of a rnv-color-mixer checkout -- this "
    f"expects to run from the directory that contains tests/."
)

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"])
]

#: The tests the existing file already carries. This pass EXTENDS it; a
#: replacement that quietly dropped one would be a regression wearing the
#: shape of an upgrade.
EXISTING = (
    "test_the_sweep_still_finds_things",
    "test_the_gold_family_is_not_empty",
    "test_the_two_golds_actually_differ_in_light",
    "test_no_gold_is_drawn_as_text_below_the_floor",
    "test_no_exemption_has_outlived_its_reason",
)

NEW = (
    "test_no_gold_fill_carries_a_label_below_the_floor",
    "test_the_fill_sweep_still_finds_things",
)


def edits(tree) -> None:
    """Nothing here. apply() writes GUARD_SOURCE to GUARD, and GUARD is the
    file this pass replaces -- so the whole edit is the new test file."""
    print("  replacing the gold guard with the bidirectional version")


def checks(tree) -> None:
    before = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    after = tree.read(SENTINEL_FILE)

    # Every test that was there is still there. Named individually rather
    # than counted, because a count cannot tell you WHICH one went.
    lost = [name for name in EXISTING if f"def {name}(" not in after]
    if lost:
        raise SystemExit(
            "the replacement drops tests that existed before it:\n  "
            + "\n  ".join(lost)
            + "\n\nThis pass extends the guard. Removing a check while "
              "adding one is a regression in the shape of an upgrade.")
    for name in NEW:
        if f"def {name}(" not in after:
            raise SystemExit(f"the new file does not define {name}")
        if f"def {name}(" in before:
            raise SystemExit(
                f"{name} is already present. This has been applied.")

    # The replacement must be strictly longer. It adds two tests and two
    # helpers and removes nothing.
    if after.count("\n") <= before.count("\n"):
        raise SystemExit(
            f"the new guard is not longer than the old one "
            f"({before.count(chr(10))} -> {after.count(chr(10))} lines), "
            f"which an extension has to be.")

    if SENTINEL not in after:
        raise SystemExit(f"expected {SENTINEL!r} in the new guard")

    # The arithmetic the docstring claims, checked against the register's
    # values rather than trusted from the prose above.
    sys.path.insert(0, str(Path.cwd()))

    def luminance(value):
        channels = [int(value.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                    for c in channels]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    def contrast(a, b):
        high, low = sorted((luminance(a), luminance(b)), reverse=True)
        return (high + 0.05) / (low + 0.05)

    black_on_deep = contrast("#000000", "#7e6529")
    black_on_gold = contrast("#000000", "#8c7337")
    if abs(black_on_deep - 3.7806) > 0.0002 or abs(black_on_gold - 4.6226) > 0.0002:
        raise SystemExit(
            f"the fill arithmetic has moved: black on the deep gold is "
            f"{black_on_deep:.4f} and on the accent {black_on_gold:.4f}; this "
            f"script says 3.7806 and 4.6226. Re-derive before trusting it.")
    if black_on_deep >= 4.5:
        raise SystemExit(
            "black now clears the floor on BRAND_DARK_GOLD_DEEP, so the rule "
            "this guard enforces has stopped being true. Read the register "
            "before applying this.")


GUARD_SOURCE = '"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.\n\nWHY THIS EXISTS. The gold family has two members that look interchangeable and\nare not. BRAND_DARK_GOLD #8c7337 fills and bounds correctly on light surfaces\nand FAILS as text on them; BRAND_DARK_GOLD_DEEP #7e6529 is the derivative that\nexists for text, and the palettes name it `accent_ink` -- "Accent when it\ncarries text". In DARK MODE THE TWO ARE THE SAME VALUE, so every check written\nwhere they coincide is blind to the case where they diverge, and that is\nexactly what happened: gold-as-text sites shipped in light mode at 3.71 and\n4.17 against a 4.5 floor, in more than one application, for as long as the\ndialogs have existed.\n\nWHAT IT DOES. Reads every f-string in the source, pulls `color:` and\n`background-color:` out of each QSS rule, resolves the placeholders through\nthis app\'s own palettes, and measures. A declaration whose foreground is a\ngold-family value and whose contrast falls below the floor fails.\n\nWHAT IT CANNOT SEE, stated because a sweep that reports only what it found\nlooks identical to one that found nothing:\n\n  - a placeholder that is not a palette lookup, a module constant or a local\n    bound to one is UNRESOLVED and skipped\n  - a rule with no background-color of its own INHERITS, and the ground is\n    taken from the palette\'s window or panel value, which is a guess\n\nBoth counts are asserted rather than printed: if the resolved count collapses,\nthe sweep has gone blind and says so instead of passing.\n\nREADING THE MODE. A block written inside `if self._is_dark:` and bound with\n`_d = ThemeManager.DARK_THEME` is dark-only, and scoring it against the light\npalette invents a pairing that never renders. Declarations are restricted to\nthe mode their variable came from. The first version of this sweep, without\nthat, reported five impossible failures including gold on #333333 at 2.78.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nimport pytest\n\nfrom utils import config as colors\nfrom utils.config import ThemeManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\nTEXT_FLOOR = 4.5\nHEX = re.compile(r\'^#[0-9a-fA-F]{6}$\')\nBLOCK = re.compile(r\'([^{}\\n][^{}]*?)\\{\\{(.*?)\\}\\}\', re.S)\nDECL = re.compile(r\'(?<!-)\\bcolor\\s*:\\s*([^;\\n]+)\')\nBGDECL = re.compile(r\'background-color\\s*:\\s*([^;\\n]+)\')\nLOOKUP = re.compile(r"^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\[\\s*[\'\\"]([a-z_0-9]+)[\'\\"]\\s*\\]\\s*\\}$")\n#: `{t.get(\'tab_selected_bg\', bg)}` is a lookup wearing a fallback. Reading it\n#: as unresolvable made the sweep guess the ground from the palette and score\n#: rnv-color-mixer\'s selected tab at 4.1670 when it actually sits on #ffffff\n#: and clears at 4.5429 -- a failure that does not exist.\nGETLOOKUP = re.compile(\n    r"^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\.get\\(\\s*[\'\\"]([a-z_0-9]+)[\'\\"]\\s*(?:,.*)?\\)\\s*\\}$",\n    re.S)\nBARE = re.compile(r\'^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\}$\')\n\nMODE_MARKERS = ((\'DARK\', (\'DARK_THEME\', \'.DARK\', \'DARK_THEME_COLORS\')),\n                (\'LIGHT\', (\'LIGHT_THEME\', \'.LIGHT\', \'LIGHT_THEME_COLORS\')),\n                (\'IMAGE\', (\'IMAGE_THEME\', \'.IMAGE\', \'IMAGE_MODE_COLORS\')))\n\n#: mode -> the live palette.\nPALETTES = {\'DARK\': ThemeManager.DARK_THEME,\n            \'LIGHT\': ThemeManager.LIGHT_THEME,\n            \'IMAGE\': ThemeManager.IMAGE_THEME}\n\n#: Keys tried, in order, when a rule inherits its ground.\nGROUND_KEYS = (\'panel_bg\', \'window_bg\', \'panel_secondary\')\n\n#: Declarations that are below the floor and are CORRECT ANYWAY, keyed by the\n#: declaration text rather than by line number -- an edit above a site shifts\n#: its line and would silently un-review it, while the declaration itself is\n#: stable. Same form as REVIEWED in tests/test_brand_contrast.py.\n#:\n#: An entry here is an exemption, so it has to earn its place twice: the\n#: reason must be true, and test_no_exemption_has_outlived_its_reason below\n#: fails when the site it names has stopped failing, so a fix cannot leave a\n#: licence standing behind it.\nACCEPTED: dict[str, str] = {}\n\n#: Below this, the sweep has stopped finding things and is passing for the\n#: wrong reason.\nMIN_RESOLVED = 8\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\n#: Names that contain GOLD and are not a gold. GOLD_TEXT_GROUND_FLOOR is the\n#: light GROUND the gold family is calibrated against -- #e8e8e8 -- and a\n#: name-based sweep swept it into the family, after which every disabled\n#: control drawn on it was reported as gold-on-gold at 1.8960. Those pairs are\n#: real and already exempt as WCAG-exempt disabled text; they are not gold.\n#: Match what the name CLAIMS, not the substring it contains.\nNOT_A_GOLD = (\'GROUND\', \'FLOOR\', \'RGB\')\n\n\ndef _golds() -> set:\n    """Every gold-family value this app holds, by name rather than by list."""\n    out = set()\n    for name in dir(colors):\n        if \'GOLD\' not in name or any(w in name for w in NOT_A_GOLD):\n            continue\n        value = getattr(colors, name)\n        if isinstance(value, str) and HEX.match(value):\n            out.add(value.lower())\n    return out\n\n\ndef _fstrings(source: str):\n    """(lineno, text, local bindings) for every f-string mentioning a colour.\n\n    Read through ast.JoinedStr, NOT the token stream. Python 3.12 splits an\n    f-string into FSTRING_START/MIDDLE/END tokens (PEP 701) rather than one\n    STRING token, so a tokenising version finds every f-string on 3.11 and none\n    on 3.12 -- reporting zero sites, which reads as clean and is blind.\n    """\n    try:\n        tree = ast.parse(source)\n    except SyntaxError:\n        return []\n    out, seen = [], set()\n    scopes = [n for n in ast.walk(tree)\n              if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef))]\n    for scope in scopes:\n        binds = {}\n        for node in ast.walk(scope):\n            if (isinstance(node, ast.Assign) and len(node.targets) == 1\n                    and isinstance(node.targets[0], ast.Name)):\n                try:\n                    binds[node.targets[0].id] = ast.unparse(node.value)\n                except Exception:\n                    continue\n        for node in ast.walk(scope):\n            if not isinstance(node, ast.JoinedStr):\n                continue\n            segment = ast.get_source_segment(source, node)\n            if not segment or \'color\' not in segment:\n                continue\n            key = (node.lineno, segment[:80])\n            if key in seen:\n                continue\n            seen.add(key)\n            out.append((node.lineno, segment, dict(binds)))\n    return out\n\n\ndef _resolve(expr: str, palette: dict, binds: dict):\n    expr = expr.strip()\n    match = BARE.match(expr)\n    if match and match.group(1) in binds:\n        expr = \'{\' + binds[match.group(1)] + \'}\'\n    if HEX.match(expr):\n        return expr.lower()\n    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)\n    if match:\n        value = palette.get(match.group(2))\n        return value.lower() if isinstance(value, str) and HEX.match(value) else None\n    match = BARE.match(expr)\n    if match:\n        value = getattr(colors, match.group(1), None)\n        return value.lower() if isinstance(value, str) and HEX.match(value) else None\n    return None\n\n\ndef _modes_for(expr: str, binds: dict):\n    expr = expr.strip()\n    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)\n    if not match:\n        return list(PALETTES)\n    bound = binds.get(match.group(1), \'\')\n    for mode, markers in MODE_MARKERS:\n        if any(marker in bound for marker in markers):\n            return [mode] if mode in PALETTES else []\n    return list(PALETTES)\n\n\n#: Rules whose background is what an unstyled child sits on.\nCONTAINER_SELECTORS = (\'body\', \'*\', \'QDialog\', \'QWidget\', \'QFrame\', \'QMainWindow\')\n\n\ndef _enclosing_ground(text: str, palette: dict, binds: dict):\n    """The ground an inheriting rule actually sits on: the background painted\n    by the container rule in the same stylesheet."""\n    for selector, body in BLOCK.findall(text):\n        name = \' \'.join(selector.split())\n        if not any(name == c or name.startswith(c + \' \') or name.startswith(c + \',\')\n                   for c in CONTAINER_SELECTORS):\n            continue\n        decl = BGDECL.search(body)\n        if decl:\n            resolved = _resolve(decl.group(1), palette, binds)\n            if resolved:\n                return resolved\n    return None\n\n\n#: Qt sub-controls that PAINT rather than draw text. A scrollbar handle, a\n#: progress-bar chunk and a checkbox indicator carry no label, so inheriting a\n#: foreground onto them invents a pairing that never renders.\n#:\n#: The first version of this sweep did exactly that and reported eleven\n#: failures in rnv-text-transformer -- APP_TEXT on the brand gold at 1.3616,\n#: on scrollbar handles and progress chunks. Every one impossible.\n#:\n#: Not every sub-control is textless: ::item, ::tab, ::section and ::title all\n#: draw labels, which is why this is a list and not a rule about `::`. The\n#: form and the first seven entries are taken from\n#: tests/test_contrast_pairs.py, which already had to make this distinction.\nTEXTLESS = (\'add-line\', \'add-page\', \'corner\', \'down-button\', \'drop-down\', \'groove\', \'handle\', \'indicator\', \'separator\', \'sub-line\', \'sub-page\', \'up-button\')\n\n\ndef _is_textless(selector: str) -> bool:\n    if \'::\' not in selector:\n        return False\n    part = selector.split(\'::\', 1)[1]\n    name = re.split(r\'[:\\[ ,]\', part)[0].strip()\n    return name in TEXTLESS\n\n\ndef _enclosing_label(text: str, palette: dict, binds: dict):\n    """The label an inheriting rule actually draws: the `color:` declared by\n    the container rule in the same stylesheet.\n\n    A fill rule often sets only a background -- `QPushButton:hover { background\n    -color: ... }` -- and the label comes from the base `QPushButton` rule.\n    Reading it is what makes the fill direction checkable at all: six of the\n    ten gold fills across these apps declare no colour of their own.\n    """\n    for selector, body in BLOCK.findall(text):\n        name = \' \'.join(selector.split())\n        if \':\' in name or \'::\' in name:\n            continue          # a state rule, not the base it inherits from\n        decl = DECL.search(body)\n        if decl:\n            resolved = _resolve(decl.group(1), palette, binds)\n            if resolved:\n                return resolved\n    return None\n\n\ndef _fill_sweep():\n    """(key, mode, label, fill, ratio, where) for every rule whose BACKGROUND\n    is a gold-family value, with the label drawn on it."""\n    rows, unresolved = [], 0\n    golds = _golds()\n    for path in sorted(ROOT.rglob(\'*.py\')):\n        if any(part in {\'.git\', \'tests\', \'build\'} for part in path.parts):\n            continue\n        if path.name == \'up.py\':\n            continue\n        source = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        if \'background-color\' not in source:\n            continue\n        for lineno, text, binds in _fstrings(source):\n            for selector, body in BLOCK.findall(text):\n                bg_decl = BGDECL.search(body)\n                if not bg_decl:\n                    continue\n                fg_decl = DECL.search(body)\n                key = f\'{path.relative_to(ROOT)} :: {" ".join(bg_decl.group(0).split())}\'\n                modes = _modes_for(bg_decl.group(1), binds)\n                if fg_decl is not None:\n                    modes = [m for m in modes\n                             if m in _modes_for(fg_decl.group(1), binds)]\n                for mode in modes:\n                    palette = PALETTES[mode]\n                    fill = _resolve(bg_decl.group(1), palette, binds)\n                    if fill is None:\n                        unresolved += 1\n                        continue\n                    if fill not in golds:\n                        continue\n                    label = (_resolve(fg_decl.group(1), palette, binds)\n                             if fg_decl is not None else None)\n                    if label is None:\n                        if _is_textless(selector):\n                            # A painted sub-control. It has no label to\n                            # inherit, and giving it one manufactures a\n                            # failure that cannot render.\n                            continue\n                        label = _enclosing_label(text, palette, binds)\n                    if label is None:\n                        # No text is drawn here that this reader can find --\n                        # a checkbox indicator or a progress chunk. Counted,\n                        # not guessed at.\n                        unresolved += 1\n                        continue\n                    rows.append((key, mode, label, fill, _contrast(label, fill),\n                                 f\'{path.relative_to(ROOT)}:{lineno} \'\n                                 f\'{" ".join(selector.split())}\'))\n    return rows, unresolved\n\n\ndef _sweep():\n    """(key, mode, fg, bg, ratio, where) for every resolved gold-as-text pair,\n    plus the count of declarations that could not be resolved."""\n    rows, unresolved = [], 0\n    golds = _golds()\n    for path in sorted(ROOT.rglob(\'*.py\')):\n        if any(part in {\'.git\', \'tests\', \'build\'} for part in path.parts):\n            continue\n        if path.name == \'up.py\':\n            continue\n        source = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        if \'color:\' not in source:\n            continue\n        for lineno, text, binds in _fstrings(source):\n            for selector, body in BLOCK.findall(text):\n                fg_decl = DECL.search(body)\n                if not fg_decl:\n                    continue\n                bg_decl = BGDECL.search(body)\n                key = f\'{path.relative_to(ROOT)} :: {" ".join(fg_decl.group(0).split())}\'\n                modes = _modes_for(fg_decl.group(1), binds)\n                if bg_decl is not None:\n                    modes = [m for m in modes\n                             if m in _modes_for(bg_decl.group(1), binds)]\n                for mode in modes:\n                    palette = PALETTES[mode]\n                    fg = _resolve(fg_decl.group(1), palette, binds)\n                    if fg is None:\n                        unresolved += 1\n                        continue\n                    if fg not in golds:\n                        continue\n                    bg = (_resolve(bg_decl.group(1), palette, binds)\n                          if bg_decl is not None else None)\n                    if bg is None:\n                        # INHERITANCE, in three steps, most specific first.\n                        # A rule with no ground of its own sits on whatever the\n                        # enclosing rule painted -- usually `body` or the\n                        # top-level widget in the SAME stylesheet. Reading that\n                        # is the difference between measuring what renders and\n                        # measuring a guess: rnv-text-transformer\'s exported\n                        # h1 inherits #ffffff from `body` and clears at 4.5429,\n                        # and a palette guess of #f5f5f5 scored it 4.1670 and\n                        # called it a failure.\n                        bg = _enclosing_ground(text, palette, binds)\n                    if bg is None:\n                        for candidate in GROUND_KEYS:\n                            value = palette.get(candidate)\n                            if isinstance(value, str) and HEX.match(value):\n                                bg = value.lower()\n                                break\n                    if bg is None:\n                        unresolved += 1\n                        continue\n                    rows.append((key, mode, fg, bg, _contrast(fg, bg),\n                                 f\'{path.relative_to(ROOT)}:{lineno} {" ".join(selector.split())}\'))\n    return rows, unresolved\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_sweep_still_finds_things():\n    """Every assertion below reads this sweep. One that resolves nothing\n    reports no failures and passes -- which is what a blind check looks like\n    from the outside."""\n    rows, _ = _sweep()\n    assert len(rows) >= MIN_RESOLVED, (\n        f\'only {len(rows)} gold-as-text pairs resolved, expected at least \'\n        f\'{MIN_RESOLVED}. Either the QSS moved out of f-strings or the \'\n        f\'resolver stopped following it. A sweep that finds nothing is not a \'\n        f\'clean sweep.\')\n\n\ndef test_the_gold_family_is_not_empty():\n    """The sweep filters on this set. Empty, it matches nothing."""\n    golds = _golds()\n    assert len(golds) >= 3, f\'only {sorted(golds)} found as gold values\'\n\n\ndef test_the_two_golds_actually_differ_in_light():\n    """The premise of this whole file. If accent and accent_ink ever hold the\n    same value in light mode, the distinction it enforces has gone and the\n    tests below would pass without meaning anything."""\n    light = PALETTES.get(\'LIGHT\')\n    if light is None or \'accent\' not in light or \'accent_ink\' not in light:\n        pytest.skip(\'this app does not name accent and accent_ink\')\n    assert light[\'accent\'] != light[\'accent_ink\'], (\n        \'accent and accent_ink are the same value in light mode. In dark they \'\n        \'legitimately are; in light the whole point is that they are not.\')\n\n\n# ------------------------------------------------------------------- the floor\n\ndef test_no_gold_is_drawn_as_text_below_the_floor():\n    rows, _unresolved = _sweep()\n    failures = []\n    for key, mode, fg, bg, ratio, where in rows:\n        if ratio >= TEXT_FLOOR or key in ACCEPTED:\n            continue\n        failures.append(f\'{ratio:.4f}  {mode}  {fg} on {bg}  {where}\')\n    assert not failures, (\n        \'gold drawn as text below the 4.5 floor:\\n  \' + \'\\n  \'.join(sorted(failures))\n        + \'\\n\\nThe palette names a derivative for this: accent_ink. In dark it \'\n          \'is the same value as accent, which is why the difference only shows \'\n          \'in light.\')\n\n\ndef test_no_exemption_has_outlived_its_reason():\n    """An exemption whose site has stopped failing is a licence with no\n    subject -- it would let a future regression at the same declaration pass\n    unseen. Fixing a site means deleting its entry in the same commit."""\n    rows, _unresolved = _sweep()\n    failing = {key for key, _m, _f, _b, ratio, _w in rows if ratio < TEXT_FLOOR}\n    stale = sorted(set(ACCEPTED) - failing)\n    assert not stale, (\n        \'these ACCEPTED entries no longer describe a failing site:\\n  \'\n        + \'\\n  \'.join(stale)\n        + \'\\n\\nDelete the entry in the commit that fixed it.\')\n\n\n# ------------------------------------------------------- the other direction\n\ndef test_no_gold_fill_carries_a_label_below_the_floor():\n    """THE OTHER HALF OF THE RULE, and it is not symmetric.\n\n    rnv-brand rev 25 publishes it bidirectionally:\n\n        On a light ground, gold as TEXT is BRAND_DARK_GOLD_DEEP.\n        Gold as a FILL or an EDGE is BRAND_DARK_GOLD.\n\n    The second sentence is not politeness. BRAND_DARK_GOLD_DEEP is derived for\n    text and FAILS the fill job -- black on it reads 3.7806 against a 4.5\n    floor, where BRAND_DARK_GOLD reads 4.6226. So a sweep that replaced every\n    BRAND_DARK_GOLD with the derivative, reading the rule as "prefer DEEP",\n    would fix the text sites and break the fills.\n\n    Nothing fails this today, in any of the five applications. That is the\n    reason to arm it now: a guard proposed against a live defect writes\n    itself, and a guard proposed against a clean sweep gets harder to justify\n    every month the sweep stays clean.\n    """\n    rows, _unresolved = _fill_sweep()\n    failures = []\n    for key, mode, label, fill, ratio, where in rows:\n        if ratio >= TEXT_FLOOR or key in ACCEPTED:\n            continue\n        failures.append(f\'{ratio:.4f}  {mode}  {label} on {fill}  {where}\')\n    assert not failures, (\n        \'a label falls below the floor on a gold fill:\\n  \'\n        + \'\\n  \'.join(sorted(failures))\n        + \'\\n\\nA FILL takes BRAND_DARK_GOLD, not the text derivative. Black \'\n          \'on the derivative is 3.7806.\')\n\n\ndef test_the_fill_sweep_still_finds_things():\n    """Guard the guard, on the half with no failures. A sweep over a clean\n    codebase and a sweep that resolves nothing produce the same report, and\n    this is the only thing that tells them apart."""\n    rows, _unresolved = _fill_sweep()\n    assert rows, (\n        \'no gold fills resolved at all. Either this app draws none -- in \'\n        \'which case delete this test rather than leave it passing over \'\n        \'nothing -- or the resolver has stopped following the expressions \'\n        \'that reach them.\')\n\n\ndef test_every_textless_entry_is_a_real_sub_control():\n    """TEXTLESS is an exclusion list, so it is an exemption: an entry that\n    names nothing excludes nothing, and one that names a sub-control which\n    actually draws text excludes a site that should be checked.\n\n    Only the first half can be asserted -- that every entry appears as a\n    `::name` somewhere in this app\'s stylesheets. Whether a sub-control draws\n    text is a fact about Qt, not about this repository, and it lives in the\n    comment beside the list.\n    """\n    seen = set()\n    for path in ROOT.rglob(\'*.py\'):\n        if any(part in {\'.git\', \'build\'} for part in path.parts):\n            continue\n        source = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        for match in re.finditer(r\'::([a-z][a-z-]*)\', source):\n            seen.add(match.group(1))\n    stale = [name for name in TEXTLESS if name not in seen]\n    assert not stale, (\n        f\'TEXTLESS names sub-controls this app never styles: {stale}. An \'\n        f\'exclusion that excludes nothing is a licence with no subject -- \'\n        f\'delete it, or find out why the sub-control went away.\')\n'


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
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
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
