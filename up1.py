#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Draw Package D's tab and button labels in the gold the palette reserves for
text.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THIS MOVES THREE PIXELS, ALL IN LIGHT MODE. TWO ARE FAILURES; ONE IS NOT.

core/package_d_panel.py draws label text in {accent}. In light that is
BRAND_DARK_GOLD #8c7337 -- the gold that fills and bounds correctly on light
surfaces and does not carry TEXT on them:

    QTabBar::tab:hover     #8c7337 on panel_hover #eeeeee   3.9156   fails
    QPushButton:hover      #8c7337 on panel_hover #eeeeee   3.9156   fails
    QTabBar::tab:selected  #8c7337 on #ffffff               4.5429   passes

The palette already names the answer. accent_ink is BRAND_DARK_GOLD_DEEP
#7e6529, derived for exactly this:

    QTabBar::tab:hover     #7e6529 on #eeeeee   4.7875
    QPushButton:hover      #7e6529 on #eeeeee   4.7875
    QTabBar::tab:selected  #7e6529 on #ffffff   5.5547

THE THIRD ONE IS A JUDGEMENT AND YOU SHOULD KNOW IT IS IN HERE. tab:selected
clears today, by 0.0429. It is changed anyway because it is TEXT, and accent_ink
is what this palette means by "gold that carries text" -- and because a margin
of four hundredths fails the moment either the gold or the ground moves one
step. That is the same reasoning the register used when it moved
APP["hover-light"] off #e8e8e8 rather than sitting the hover plate on the value
the gold is calibrated against. If you would rather leave a passing site alone,
this is the one to pull.

WHAT DOES NOT CHANGE

    border-bottom: 2px solid {accent}   an EDGE, 3.0 floor, 4.5429 -- correct
    border-color: {accent}              same
    background-color: {accent}          a FILL -- correct
    color: {accent_text}                already the on-gold label

accent is the right value for a fill and for an edge. A script that swept every
{accent} would change six sites that are right.

DARK MODE CANNOT MOVE. There accent and accent_ink hold the same value, and the
script refuses to run if that has stopped being true.

WHY NOTHING CAUGHT IT

Because of that same equality. A check written against the dark palette, where
the two golds coincide, is structurally incapable of seeing the light case
where they diverge. rnv-text-transformer has the same defect from the same
cause, and its tests/test_contrast_pairs.py asserts
dark['accent_ink'] == dark['accent'] -- true, correct, and blind to this.

WHAT THIS SCRIPT ADDS SO IT CANNOT RECUR

tests/test_gold_as_text.py sweeps every f-string in the app, pulls `color:` and
`background-color:` out of each QSS rule, resolves the placeholders through
this app's own palettes, and fails any gold-family foreground under 4.5:1 on
the ground it is drawn on. Its own blind spots are assertions rather than
prose: if the number of pairs it can resolve collapses, it fails instead of
passing quietly.

It reads two things a first version got wrong, both of which invented failures
that cannot render:

  - a block bound with `_d = ThemeManager.DARK_THEME` inside `if self._is_dark:`
    is DARK ONLY. Scored against the light palette it reported gold on #333333
    at 2.78 in this very app -- a pairing the program never draws.
  - `{t.get('tab_selected_bg', bg)}` is a lookup wearing a fallback. Read as
    unresolvable, the ground fell back to a palette guess and scored the
    selected tab at 4.1670 when it sits on #ffffff and clears.
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
DESCRIPTION = "draw Package D's labels in accent_ink"
SENTINEL_FILE = "core/package_d_panel.py"
SENTINEL = "border-color: {accent};\n                color: {accent_ink};"
#: The bare `color: {accent_ink};` already appears three times in this file --
#: _style_tip and _section_header_style bind `accent` to accent_ink and have
#: always been right. The sentinel has to be something this pass CREATES, or
#: the script refuses to run before it has done anything.
GUARD = "tests/test_gold_as_text.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('pytest tests/',
     [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    ('unittest suite',
     [sys.executable, "-m", "unittest", "test_rnv_color_mixer"]),
]

EDITS = [('            QTabBar::tab:hover {{\n                background-color: {bg_hover};\n                color: {accent};\n            }}', '            QTabBar::tab:hover {{\n                background-color: {bg_hover};\n                color: {accent_ink};\n            }}'), ('            QPushButton:hover {{\n                background-color: {bg_hover};\n                border-color: {accent};\n                color: {accent};\n            }}', '            QPushButton:hover {{\n                background-color: {bg_hover};\n                border-color: {accent};\n                color: {accent_ink};\n            }}'), ("            QTabBar::tab:selected {{\n                background-color: {t.get('tab_selected_bg', bg)};\n                color: {accent};\n                border-bottom: 2px solid {accent};\n            }}", "            QTabBar::tab:selected {{\n                background-color: {t.get('tab_selected_bg', bg)};\n                color: {accent_ink};\n                border-bottom: 2px solid {accent};\n            }}")]

#: (label, ground key, before, after). The arithmetic this script claims,
#: checked against the app's own palette rather than trusted from the note.
EXPECTED = [
    ("QTabBar::tab:hover", "panel_hover", 3.9156, 4.7875),
    ("QPushButton:hover", "panel_hover", 3.9156, 4.7875),
    ("QTabBar::tab:selected", "tab_selected_bg", 4.5429, 5.5547),
]

#: Declarations that must survive untouched. accent is correct for a fill and
#: for an edge; only text moves.
KEEP = ("border-bottom: 2px solid {accent};",
        "border-color: {accent};",
        "background-color: {accent};")


def _luminance(value: str) -> float:
    channels = [int(value.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def edits(tree) -> None:
    for old, new in EDITS:
        tree.sub(SENTINEL_FILE, old, new)
    print(f"  redirected {len(EDITS)} label declarations to accent_ink")


def checks(tree) -> None:
    original = (Path.cwd() / SENTINEL_FILE).read_text(encoding="utf-8-sig")
    edited = tree.read(SENTINEL_FILE)

    if edited.count("\n") != original.count("\n"):
        raise SystemExit(
            f"the file changed shape: {original.count(chr(10))} lines before, "
            f"{edited.count(chr(10))} after. A substitution adds and removes "
            f"nothing.")

    # Exactly three text declarations move, and the rest of {accent} stays.
    if edited.count("color: {accent_ink};") - original.count("color: {accent_ink};") != 3:
        raise SystemExit("expected exactly three new accent_ink declarations")
    for keep in KEEP:
        if keep not in edited:
            raise SystemExit(
                f"{keep!r} is gone. This pass moves gold used as TEXT and "
                f"nothing else -- accent is the correct value for a fill or an "
                f"edge, which have a 3.0 floor rather than 4.5.")

    sys.path.insert(0, str(Path.cwd()))
    try:
        from utils.config import ThemeManager
    except Exception as exc:                       # pragma: no cover
        raise SystemExit(f"cannot import the palettes to verify the fix: {exc}")
    light, dark = ThemeManager.LIGHT_THEME, ThemeManager.DARK_THEME
    accent, ink = light["accent"], light["accent_ink"]
    if accent == ink:
        raise SystemExit(
            "accent and accent_ink hold the same value in light mode, so this "
            "change would be a no-op. In dark they legitimately coincide; in "
            "light the difference is the entire point.")
    for label, key, before, after in EXPECTED:
        ground = light[key]
        was, now = _contrast(accent, ground), _contrast(ink, ground)
        if abs(was - before) > 0.0002 or abs(now - after) > 0.0002:
            raise SystemExit(
                f"{label} on {key} {ground}: measured {was:.4f} -> {now:.4f}, "
                f"but this script says {before} -> {after}. A value moved "
                f"underneath it; re-derive before trusting the note.")
        if now < 4.5:
            raise SystemExit(f"{label} still fails at {now:.4f}")
    if dark["accent"] != dark["accent_ink"]:
        raise SystemExit(
            "dark accent and accent_ink have diverged. This pass is safe in "
            "dark precisely because they are the same value there.")


GUARD_SOURCE = '"""Gold drawn as TEXT must clear the text floor on the ground it is drawn on.\n\nWHY THIS EXISTS. The gold family has two members that look interchangeable and\nare not. BRAND_DARK_GOLD #8c7337 fills and bounds correctly on light surfaces\nand FAILS as text on them; BRAND_DARK_GOLD_DEEP #7e6529 is the derivative that\nexists for text, and the palettes name it `accent_ink` -- "Accent when it\ncarries text". In DARK MODE THE TWO ARE THE SAME VALUE, so every check written\nwhere they coincide is blind to the case where they diverge, and that is\nexactly what happened: gold-as-text sites shipped in light mode at 3.71 and\n4.17 against a 4.5 floor, in more than one application, for as long as the\ndialogs have existed.\n\nWHAT IT DOES. Reads every f-string in the source, pulls `color:` and\n`background-color:` out of each QSS rule, resolves the placeholders through\nthis app\'s own palettes, and measures. A declaration whose foreground is a\ngold-family value and whose contrast falls below the floor fails.\n\nWHAT IT CANNOT SEE, stated because a sweep that reports only what it found\nlooks identical to one that found nothing:\n\n  - a placeholder that is not a palette lookup, a module constant or a local\n    bound to one is UNRESOLVED and skipped\n  - a rule with no background-color of its own INHERITS, and the ground is\n    taken from the palette\'s window or panel value, which is a guess\n\nBoth counts are asserted rather than printed: if the resolved count collapses,\nthe sweep has gone blind and says so instead of passing.\n\nREADING THE MODE. A block written inside `if self._is_dark:` and bound with\n`_d = ThemeManager.DARK_THEME` is dark-only, and scoring it against the light\npalette invents a pairing that never renders. Declarations are restricted to\nthe mode their variable came from. The first version of this sweep, without\nthat, reported five impossible failures including gold on #333333 at 2.78.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nimport pytest\n\nfrom utils import config as colors\nfrom utils.config import ThemeManager\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\n\nTEXT_FLOOR = 4.5\nHEX = re.compile(r\'^#[0-9a-fA-F]{6}$\')\nBLOCK = re.compile(r\'([^{}\\n][^{}]*?)\\{\\{(.*?)\\}\\}\', re.S)\nDECL = re.compile(r\'(?<!-)\\bcolor\\s*:\\s*([^;\\n]+)\')\nBGDECL = re.compile(r\'background-color\\s*:\\s*([^;\\n]+)\')\nLOOKUP = re.compile(r"^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\[\\s*[\'\\"]([a-z_0-9]+)[\'\\"]\\s*\\]\\s*\\}$")\n#: `{t.get(\'tab_selected_bg\', bg)}` is a lookup wearing a fallback. Reading it\n#: as unresolvable made the sweep guess the ground from the palette and score\n#: rnv-color-mixer\'s selected tab at 4.1670 when it actually sits on #ffffff\n#: and clears at 4.5429 -- a failure that does not exist.\nGETLOOKUP = re.compile(\n    r"^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\.get\\(\\s*[\'\\"]([a-z_0-9]+)[\'\\"]\\s*(?:,.*)?\\)\\s*\\}$",\n    re.S)\nBARE = re.compile(r\'^\\{\\s*([A-Za-z_][A-Za-z_0-9]*)\\s*\\}$\')\n\nMODE_MARKERS = ((\'DARK\', (\'DARK_THEME\', \'.DARK\', \'DARK_THEME_COLORS\')),\n                (\'LIGHT\', (\'LIGHT_THEME\', \'.LIGHT\', \'LIGHT_THEME_COLORS\')),\n                (\'IMAGE\', (\'IMAGE_THEME\', \'.IMAGE\', \'IMAGE_MODE_COLORS\')))\n\n#: mode -> the live palette.\nPALETTES = {\'DARK\': ThemeManager.DARK_THEME,\n            \'LIGHT\': ThemeManager.LIGHT_THEME,\n            \'IMAGE\': ThemeManager.IMAGE_THEME}\n\n#: Keys tried, in order, when a rule inherits its ground.\nGROUND_KEYS = (\'panel_bg\', \'window_bg\', \'panel_secondary\')\n\n#: Declarations that are below the floor and are CORRECT ANYWAY, keyed by the\n#: declaration text rather than by line number -- an edit above a site shifts\n#: its line and would silently un-review it, while the declaration itself is\n#: stable. Same form as REVIEWED in tests/test_brand_contrast.py.\n#:\n#: An entry here is an exemption, so it has to earn its place twice: the\n#: reason must be true, and test_no_exemption_has_outlived_its_reason below\n#: fails when the site it names has stopped failing, so a fix cannot leave a\n#: licence standing behind it.\nACCEPTED: dict[str, str] = {}\n\n#: Below this, the sweep has stopped finding things and is passing for the\n#: wrong reason.\nMIN_RESOLVED = 8\n\n\ndef _luminance(value: str) -> float:\n    channels = [int(value.lstrip(\'#\')[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4\n                for c in channels]\n    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)\n    return (high + 0.05) / (low + 0.05)\n\n\ndef _golds() -> set:\n    """Every gold-family value this app holds, by name rather than by list."""\n    out = set()\n    for name in dir(colors):\n        if \'GOLD\' not in name:\n            continue\n        value = getattr(colors, name)\n        if isinstance(value, str) and HEX.match(value):\n            out.add(value.lower())\n    return out\n\n\ndef _fstrings(source: str):\n    """(lineno, text, local bindings) for every f-string mentioning a colour.\n\n    Read through ast.JoinedStr, NOT the token stream. Python 3.12 splits an\n    f-string into FSTRING_START/MIDDLE/END tokens (PEP 701) rather than one\n    STRING token, so a tokenising version finds every f-string on 3.11 and none\n    on 3.12 -- reporting zero sites, which reads as clean and is blind.\n    """\n    try:\n        tree = ast.parse(source)\n    except SyntaxError:\n        return []\n    out, seen = [], set()\n    scopes = [n for n in ast.walk(tree)\n              if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef))]\n    for scope in scopes:\n        binds = {}\n        for node in ast.walk(scope):\n            if (isinstance(node, ast.Assign) and len(node.targets) == 1\n                    and isinstance(node.targets[0], ast.Name)):\n                try:\n                    binds[node.targets[0].id] = ast.unparse(node.value)\n                except Exception:\n                    continue\n        for node in ast.walk(scope):\n            if not isinstance(node, ast.JoinedStr):\n                continue\n            segment = ast.get_source_segment(source, node)\n            if not segment or \'color\' not in segment:\n                continue\n            key = (node.lineno, segment[:80])\n            if key in seen:\n                continue\n            seen.add(key)\n            out.append((node.lineno, segment, dict(binds)))\n    return out\n\n\ndef _resolve(expr: str, palette: dict, binds: dict):\n    expr = expr.strip()\n    match = BARE.match(expr)\n    if match and match.group(1) in binds:\n        expr = \'{\' + binds[match.group(1)] + \'}\'\n    if HEX.match(expr):\n        return expr.lower()\n    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)\n    if match:\n        value = palette.get(match.group(2))\n        return value.lower() if isinstance(value, str) and HEX.match(value) else None\n    match = BARE.match(expr)\n    if match:\n        value = getattr(colors, match.group(1), None)\n        return value.lower() if isinstance(value, str) and HEX.match(value) else None\n    return None\n\n\ndef _modes_for(expr: str, binds: dict):\n    expr = expr.strip()\n    match = LOOKUP.match(expr) or GETLOOKUP.match(expr)\n    if not match:\n        return list(PALETTES)\n    bound = binds.get(match.group(1), \'\')\n    for mode, markers in MODE_MARKERS:\n        if any(marker in bound for marker in markers):\n            return [mode] if mode in PALETTES else []\n    return list(PALETTES)\n\n\n#: Rules whose background is what an unstyled child sits on.\nCONTAINER_SELECTORS = (\'body\', \'*\', \'QDialog\', \'QWidget\', \'QFrame\', \'QMainWindow\')\n\n\ndef _enclosing_ground(text: str, palette: dict, binds: dict):\n    """The ground an inheriting rule actually sits on: the background painted\n    by the container rule in the same stylesheet."""\n    for selector, body in BLOCK.findall(text):\n        name = \' \'.join(selector.split())\n        if not any(name == c or name.startswith(c + \' \') or name.startswith(c + \',\')\n                   for c in CONTAINER_SELECTORS):\n            continue\n        decl = BGDECL.search(body)\n        if decl:\n            resolved = _resolve(decl.group(1), palette, binds)\n            if resolved:\n                return resolved\n    return None\n\n\ndef _sweep():\n    """(key, mode, fg, bg, ratio, where) for every resolved gold-as-text pair,\n    plus the count of declarations that could not be resolved."""\n    rows, unresolved = [], 0\n    golds = _golds()\n    for path in sorted(ROOT.rglob(\'*.py\')):\n        if any(part in {\'.git\', \'tests\', \'build\'} for part in path.parts):\n            continue\n        if path.name == \'up.py\':\n            continue\n        source = path.read_text(encoding=\'utf-8-sig\', errors=\'replace\')\n        if \'color:\' not in source:\n            continue\n        for lineno, text, binds in _fstrings(source):\n            for selector, body in BLOCK.findall(text):\n                fg_decl = DECL.search(body)\n                if not fg_decl:\n                    continue\n                bg_decl = BGDECL.search(body)\n                key = f\'{path.relative_to(ROOT)} :: {" ".join(fg_decl.group(0).split())}\'\n                modes = _modes_for(fg_decl.group(1), binds)\n                if bg_decl is not None:\n                    modes = [m for m in modes\n                             if m in _modes_for(bg_decl.group(1), binds)]\n                for mode in modes:\n                    palette = PALETTES[mode]\n                    fg = _resolve(fg_decl.group(1), palette, binds)\n                    if fg is None:\n                        unresolved += 1\n                        continue\n                    if fg not in golds:\n                        continue\n                    bg = (_resolve(bg_decl.group(1), palette, binds)\n                          if bg_decl is not None else None)\n                    if bg is None:\n                        # INHERITANCE, in three steps, most specific first.\n                        # A rule with no ground of its own sits on whatever the\n                        # enclosing rule painted -- usually `body` or the\n                        # top-level widget in the SAME stylesheet. Reading that\n                        # is the difference between measuring what renders and\n                        # measuring a guess: rnv-text-transformer\'s exported\n                        # h1 inherits #ffffff from `body` and clears at 4.5429,\n                        # and a palette guess of #f5f5f5 scored it 4.1670 and\n                        # called it a failure.\n                        bg = _enclosing_ground(text, palette, binds)\n                    if bg is None:\n                        for candidate in GROUND_KEYS:\n                            value = palette.get(candidate)\n                            if isinstance(value, str) and HEX.match(value):\n                                bg = value.lower()\n                                break\n                    if bg is None:\n                        unresolved += 1\n                        continue\n                    rows.append((key, mode, fg, bg, _contrast(fg, bg),\n                                 f\'{path.relative_to(ROOT)}:{lineno} {" ".join(selector.split())}\'))\n    return rows, unresolved\n\n\n# ------------------------------------------------------------- guard the guard\n\ndef test_the_sweep_still_finds_things():\n    """Every assertion below reads this sweep. One that resolves nothing\n    reports no failures and passes -- which is what a blind check looks like\n    from the outside."""\n    rows, _ = _sweep()\n    assert len(rows) >= MIN_RESOLVED, (\n        f\'only {len(rows)} gold-as-text pairs resolved, expected at least \'\n        f\'{MIN_RESOLVED}. Either the QSS moved out of f-strings or the \'\n        f\'resolver stopped following it. A sweep that finds nothing is not a \'\n        f\'clean sweep.\')\n\n\ndef test_the_gold_family_is_not_empty():\n    """The sweep filters on this set. Empty, it matches nothing."""\n    golds = _golds()\n    assert len(golds) >= 3, f\'only {sorted(golds)} found as gold values\'\n\n\ndef test_the_two_golds_actually_differ_in_light():\n    """The premise of this whole file. If accent and accent_ink ever hold the\n    same value in light mode, the distinction it enforces has gone and the\n    tests below would pass without meaning anything."""\n    light = PALETTES.get(\'LIGHT\')\n    if light is None or \'accent\' not in light or \'accent_ink\' not in light:\n        pytest.skip(\'this app does not name accent and accent_ink\')\n    assert light[\'accent\'] != light[\'accent_ink\'], (\n        \'accent and accent_ink are the same value in light mode. In dark they \'\n        \'legitimately are; in light the whole point is that they are not.\')\n\n\n# ------------------------------------------------------------------- the floor\n\ndef test_no_gold_is_drawn_as_text_below_the_floor():\n    rows, _unresolved = _sweep()\n    failures = []\n    for key, mode, fg, bg, ratio, where in rows:\n        if ratio >= TEXT_FLOOR or key in ACCEPTED:\n            continue\n        failures.append(f\'{ratio:.4f}  {mode}  {fg} on {bg}  {where}\')\n    assert not failures, (\n        \'gold drawn as text below the 4.5 floor:\\n  \' + \'\\n  \'.join(sorted(failures))\n        + \'\\n\\nThe palette names a derivative for this: accent_ink. In dark it \'\n          \'is the same value as accent, which is why the difference only shows \'\n          \'in light.\')\n\n\ndef test_no_exemption_has_outlived_its_reason():\n    """An exemption whose site has stopped failing is a licence with no\n    subject -- it would let a future regression at the same declaration pass\n    unseen. Fixing a site means deleting its entry in the same commit."""\n    rows, _unresolved = _sweep()\n    failing = {key for key, _m, _f, _b, ratio, _w in rows if ratio < TEXT_FLOOR}\n    stale = sorted(set(ACCEPTED) - failing)\n    assert not stale, (\n        \'these ACCEPTED entries no longer describe a failing site:\\n  \'\n        + \'\\n  \'.join(stale)\n        + \'\\n\\nDelete the entry in the commit that fixed it.\')\n'


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
