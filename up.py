"""derive every alpha-carrying colour from its base

    python up.py             # apply, then run the guard and CI's own steps
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guard and CI's steps, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head.

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-24. Every colour this application writes at an alpha becomes a named
base at a declared byte, so a change to a base ripples to every alpha form of it.
Inside the three stylesheet templates the spelling stays rgba(), which keeps them
byte-identical and the locked suite's rgba() assertion true; elsewhere it is
#aarrggbb, which QColor() can also read.

ONE PIXEL MOVES, BY RULING: the image scrollbar handle leaves #505050 for
grey(4) at 150. The locked file is not touched, and its hash is checked first.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'RNV-DERIVE-ALPHA'
SENTINEL_FILE = "tests/conftest.py"
GUARD = "tests/test_derived_values.py"
DESCRIPTION = 'derive every alpha-carrying colour from its base'

LOCKED = "test_rnv_color_mixer.py"
LOCKED_SHA = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd'

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS, in its order, floor included. The
#: Windows workflow runs the same two suites without coverage. The floor is
#: wrapped so that falling under it reads as a failure: coverage exits 2 for
#: that, which this harness would otherwise read as the environment.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69'])\n"
          "if r.returncode == 2:\n"
          "    raise AssertionError('coverage is under the Linux CI floor of 69')\n"
          "sys.exit(r.returncode)\n")
_LOCK = ("import hashlib, sys\n"
         "d = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if d != '" + LOCKED_SHA + "':\n"
         "    raise AssertionError(f'LOCKED FILE INTEGRITY VIOLATION: {d}')\n"
         "print(f'Locked file SHA-256 matches: {d}')\n")
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
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR]),
]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '769b9b7034c0599b5d655cfb502741706693e765d51e2db95406c140a6b92ffd', '.github/workflows/tests-windows.yml': 'd123e5da015c9b988e5c52e9c0bb9879d492365b6db6c1f3672dc1b34f57d967'}

SHADOWS = {"config.py", "conftest.py", "test_rnv_color_mixer.py"}

LEFT_ALONE = [
    "test_rnv_color_mixer.py, which is SHA-256-locked by both workflows. "
    "Nothing here edits it, and the first suite step checks its hash exactly "
    "as CI does.",
    "the debug overlays -- DEBUG_OVERLAY_COLORS, ui/debug_overlay.py and "
    "PackageDPanel._create_debug_overlays. Diagnostic, so outside the brand "
    "by rule; a test now says so.",
    "rgba(0, 0, 0, 0) in ui/canvas_view.py, twice. Alpha zero draws no "
    "colour, so there is nothing for a register row to control.",
    "the integer tuples -- the screen picker's QColor(0, 0, 0, 50) and "
    "(0, 0, 0, 180), the canvas labels' QColor(..., 200), and the rest. "
    "Tuples get a fleet round of their own.",
    "the Windows workflow, which runs the same two suites without coverage "
    "and cannot be run here.",
]

GUARD_SOURCE = '"""Derived values: a colour that is a named colour AT AN ALPHA.\n\nThe three stylesheet templates were made literal-free for HEX on 2026-09-06 --\ntests/test_neutral_ramp.py holds that -- and eleven rgba() literals stayed\nbehind, because a hex sweep cannot see them. rgba(26, 26, 26, 191) IS\nAPP_SURFACE_DARK at alpha 191; written out, a move of APP_SURFACE_DARK would\nhave reached every opaque use and none of these. Each is now\ntranslucent_rgba(BASE, ALPHA) inside the template, and the palettes\' three\ncheckbox grounds are translucent(BASE, ALPHA).\n\nWHY TWO SPELLINGS, AND WHERE EACH IS ALLOWED. rgba() is valid in a stylesheet\nand INVALID in QColor(), which reads it as opaque black. So rgba() is allowed\nonly INSIDE a stylesheet template -- where a value can never travel to a\nQColor -- and the locked suite needs it there (test_image_stylesheet_rgba).\nEverywhere else a derived value is #aarrggbb, which both accept.\n\nWHAT MOVES A PIXEL: ONE THING, BY RULING. The image scrollbar handle leaves\n#505050 for APP_CHROME_DARK -- grey(4), #444444, the GREY_44 of the ruling --\nat the same alpha, 150. The dark handle\'s rgba(51, 51, 51, 0.7) is respelled\nwith the byte Qt makes of 0.7, 178, MEASURED through Qt\'s stylesheet parser on\nthree grounds; the same pixels. Everything else renders byte for byte as\nbefore, and tests/test_snapshots.py still compares all three sheets whole.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nfrom utils import config as C\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / "utils" / "config.py"\nPALETTES = ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME")\nTEMPLATES = ("DARK_STYLESHEET", "LIGHT_STYLESHEET", "IMAGE_STYLESHEET")\nHELPERS = ("translucent", "translucent_rgba")\n\n#: constant -> the byte. Each is the alpha its literal already carried; the\n#: dark handle\'s is the byte Qt MEASURES for 0.7 (0.7 * 255 = 178.5, and Qt\n#: gives 178 -- the same on #1a1a1a, #ffffff and #d2bc93 grounds).\nALPHAS = {\n    "SCROLLBAR_HANDLE_ALPHA_DARK": 0xB2,\n    "SCROLLBAR_HANDLE_ALPHA": 0x96,\n    "SCROLLBAR_BG_ALPHA": 0x64,\n    "SCROLL_AREA_BORDER_ALPHA": 0x64,\n    "IMAGE_FIELD_ALPHA": 0xAB,\n    "STATUS_BAR_ALPHA": 0xC8,\n    "IMAGE_CHECKBOX_ALPHA": 0x64,\n    "COMBO_ALPHA": 0xBF,\n    "CHECKBOX_BG_ALPHA_DARK": 0xE6,\n    "CHECKBOX_BG_ALPHA_LIGHT": 0xC8,\n}\n\n#: What each template\'s derived values are MADE OF, by NAME: (base, alpha).\n#: A register move passes through; a value re-made from something else fails.\nMADE_OF = {\n    "DARK_STYLESHEET": [("APP_BORDER_DARK", "SCROLLBAR_HANDLE_ALPHA_DARK")] * 2,\n    "LIGHT_STYLESHEET": [],\n    "IMAGE_STYLESHEET": sorted(\n        [("TRUE_BLACK", "IMAGE_FIELD_ALPHA"),\n         ("APP_BORDER_DARK", "SCROLL_AREA_BORDER_ALPHA")]\n        + [("APP_BORDER_DARK", "SCROLLBAR_BG_ALPHA")] * 2\n        + [("APP_CHROME_DARK", "SCROLLBAR_HANDLE_ALPHA")] * 2       # ruled\n        + [("APP_SURFACE_DARK", "STATUS_BAR_ALPHA"),\n           ("TRUE_BLACK", "IMAGE_CHECKBOX_ALPHA")]\n        + [("APP_SURFACE_DARK", "COMBO_ALPHA")] * 2),\n}\nPALETTE_MADE_OF = {\n    "DARK_THEME": ("APP_SURFACE_DARK", "CHECKBOX_BG_ALPHA_DARK"),\n    "LIGHT_THEME": ("WHITE", "CHECKBOX_BG_ALPHA_LIGHT"),\n    "IMAGE_THEME": ("APP_SURFACE_DARK", "CHECKBOX_BG_ALPHA_DARK"),\n}\n\n#: Diagnostic, and so outside the brand by rule: the debug overlay must read on\n#: any window whatever the theme.\nDIAGNOSTIC_FILES = {"ui/debug_overlay.py"}\nDIAGNOSTIC_FUNCTIONS = {"_create_debug_overlays"}\nDIAGNOSTIC_NAMES = {"DEBUG_OVERLAY_COLORS"}\n\n_HEX8 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{6})$")\n_RGBA = re.compile(r"rgba\\((\\d{1,3}), (\\d{1,3}), (\\d{1,3}), (\\d{1,3})\\)")\n_COMPOSED = re.compile(r"#[0-9a-fA-F]{8}\\b|\\brgba\\(\\s*\\d{1,3}\\s*,\\s*\\d{1,3}"\n                       r"\\s*,\\s*\\d{1,3}\\s*,\\s*[0-9]*\\.?[0-9]+\\s*\\)")\n_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\\b")\n_FUNC = re.compile(r"\\brgba?\\(\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})\\s*,\\s*(\\d{1,3})"\n                   r"\\s*(?:,\\s*[0-9]*\\.?[0-9]+\\s*)?\\)")\nSKIP_DIRS = {".git", "tests", "snapshots", "build", "dist", ".venv", "venv",\n             "__pycache__"}\n\n\ndef decompose(value: str) -> tuple[str, int] | None:\n    """(base \'#rrggbb\', alpha byte) -- taken apart, never rebuilt."""\n    m = _HEX8.match(value)\n    if m:\n        return "#" + m.group(2).lower(), int(m.group(1), 16)\n    m = _RGBA.fullmatch(value)\n    if m:\n        r, g, b, a = (int(x) for x in m.groups())\n        return "#%02x%02x%02x" % (r, g, b), a\n    return None\n\n\ndef _parts_of(spelled: str) -> tuple[str, int]:\n    if spelled.startswith("#"):\n        return "#" + spelled[3:].lower(), int(spelled[1:3], 16)\n    numbers = re.findall(r"[0-9]*\\.?[0-9]+", spelled)\n    r, g, b = (int(x) for x in numbers[:3])\n    a = numbers[3]\n    return "#%02x%02x%02x" % (r, g, b), (int(float(a) * 255) if "." in a\n                                         else int(a))\n\n\ndef colours_in(text: str) -> set[str]:\n    found = set()\n    for m in _HEX.finditer(text):\n        h = m.group(0)[1:].lower()\n        h = h[2:] if len(h) == 8 else ("".join(c * 2 for c in h) if len(h) == 3 else h)\n        found.add("#" + h)\n    for m in _FUNC.finditer(text):\n        channels = [int(g) for g in m.groups()]\n        if all(c <= 255 for c in channels):\n            found.add("#%02x%02x%02x" % tuple(channels))\n    return found\n\n\ndef _module() -> ast.Module:\n    return ast.parse(SRC.read_text(encoding="utf-8-sig"))\n\n\ndef _palette_nodes() -> dict[str, ast.Dict]:\n    cls = next(n for n in _module().body\n               if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")\n    out = {}\n    for node in cls.body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            t = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(t, "id", None) in PALETTES and isinstance(node.value, ast.Dict):\n                out[t.id] = node.value\n    return out\n\n\ndef _template_calls(tree: ast.Module | None = None) -> dict[str, list[ast.Call]]:\n    """The helper calls inside each stylesheet template, in source order.\n    Pass the tree when the caller compares node identities: two parses of one\n    file are two sets of objects, and an id() from one never matches the\n    other -- which is how the first version of the rgba check below flagged\n    all twelve calls as outside the templates they sat in."""\n    out = {}\n    for node in (tree or _module()).body:\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            t = node.targets[0] if isinstance(node, ast.Assign) else node.target\n            if getattr(t, "id", None) in TEMPLATES:\n                out[t.id] = [c for c in ast.walk(node.value)\n                             if isinstance(c, ast.Call)\n                             and getattr(c.func, "id", None) in HELPERS]\n    return out\n\n\ndef _names(call: ast.Call) -> tuple[str, str] | None:\n    if len(call.args) == 2 and all(isinstance(a, ast.Name) for a in call.args):\n        return call.args[0].id, call.args[1].id\n    return None\n\n\ndef _bare_strings(tree: ast.AST) -> set[int]:\n    bare = set()\n    for node in ast.walk(tree):\n        body = getattr(node, "body", None)\n        if isinstance(body, list):\n            for st in body:\n                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):\n                    bare.add(id(st.value))\n    return bare\n\n\ndef _sources():\n    for path in sorted(ROOT.rglob("*.py")):\n        rel = path.relative_to(ROOT)\n        if any(p in SKIP_DIRS for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_bytes().decode("utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        yield rel, ast.parse(text)\n\n\n# ------------------------------------------------------------ guard the guard\n\ndef test_the_helpers_compose_alpha_first_and_agree():\n    assert C.translucent("#1a1a1a", 0xBF) == "#bf1a1a1a"\n    assert C.translucent_rgba("#1a1a1a", 0xBF) == "rgba(26, 26, 26, 191)"\n    for base in ("#1a1a1a", "#d2bc93", "#444444"):\n        for alpha in (0, 0x64, 0xB2, 255):\n            assert (decompose(C.translucent(base, alpha))\n                    == decompose(C.translucent_rgba(base, alpha))\n                    == (base, alpha))\n\n\ndef test_the_helpers_refuse_what_they_cannot_compose():\n    for helper in (C.translucent, C.translucent_rgba):\n        for bad in (-1, 256, 0.7, True):\n            try:\n                helper("#1a1a1a", bad)\n            except (ValueError, TypeError):\n                pass\n            else:\n                raise AssertionError(f"{helper.__name__} took alpha {bad!r}")\n        for bad in ("#1a1a1", "#1a1a1a1a", "nonsense", "#gggggg"):\n            try:\n                helper(bad, 0xBF)\n            except ValueError:\n                pass\n            else:\n                raise AssertionError(f"{helper.__name__} took base {bad!r}")\n\n\ndef test_the_alphas_are_the_declared_bytes():\n    for name, byte in ALPHAS.items():\n        assert hasattr(C, name), f"utils.config has no {name}"\n        value = getattr(C, name)\n        assert type(value) is int, f"{name} is {value!r}, not an int byte"\n        assert value == byte, f"{name} is {value:#x}, declared {byte:#x}"\n\n\ndef test_the_derivation_sweep_is_looking():\n    calls = _template_calls()\n    assert set(calls) == set(TEMPLATES), sorted(calls)\n    assert sum(len(v) for v in calls.values()) == 12, (\n        {k: len(v) for k, v in calls.items()})\n    palettes = _palette_nodes()\n    assert set(palettes) == set(PALETTES)\n    derived = [k.value for p in palettes.values() for k, v in zip(p.keys, p.values)\n               if isinstance(v, ast.Call)\n               and getattr(v.func, "id", None) in HELPERS]\n    assert derived == ["checkbox_bg"] * 3, derived\n\n\n# ----------------------------------------------------------- the derivations\n\ndef test_every_derived_value_names_constants_that_exist():\n    bad = []\n    everything = [(f"{t}#{i}", c) for t, calls in _template_calls().items()\n                  for i, c in enumerate(calls)]\n    everything += [(f"{p}[{k.value!r}]", v) for p, d in _palette_nodes().items()\n                   for k, v in zip(d.keys, d.values)\n                   if isinstance(v, ast.Call) and getattr(v.func, "id", None) in HELPERS]\n    for where, call in everything:\n        names = _names(call)\n        if names is None or call.keywords:\n            bad.append(f"{where}: {ast.unparse(call)} is not (BASE, ALPHA) by name")\n            continue\n        base, alpha = names\n        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(getattr(C, base, ""))):\n            bad.append(f"{where}: {base} is not a six-digit colour in utils.config")\n        if alpha not in ALPHAS:\n            bad.append(f"{where}: {alpha} is not a declared composite alpha")\n    assert not bad, "derived values that do not derive:\\n  " + "\\n  ".join(bad)\n\n\ndef test_rgba_is_spelled_only_inside_the_templates():\n    """translucent_rgba() anywhere but a stylesheet template is a value that\n    can reach QColor(), which reads rgba() as opaque black. And the pin that\n    requires rgba() in IMAGE_STYLESHEET is re-read from the locked suite, so\n    the reason outlives nothing."""\n    tree = _module()\n    inside = {id(c) for calls in _template_calls(tree).values() for c in calls}\n    assert len(inside) == 12, f"the template sweep sees {len(inside)} calls"\n    stray = [f"line {n.lineno}" for n in ast.walk(tree)\n             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "translucent_rgba"\n             and id(n) not in inside]\n    assert not stray, f"translucent_rgba() outside a stylesheet template: {stray}"\n    locked = (ROOT / "test_rnv_color_mixer.py").read_text(encoding="utf-8-sig")\n    assert \'self.assertIn("rgba(",config.IMAGE_STYLESHEET)\' in locked\n\n\ndef test_every_template_value_decomposes_to_what_it_is_made_of():\n    """The rendered sheet, TAKEN APART: every rgba() in it, read back to a\n    (base, alpha) pair, must be exactly the multiset its calls name -- by the\n    constants\' values now, so a register move passes straight through."""\n    for template, made_of in MADE_OF.items():\n        rendered = getattr(C, template)\n        found = sorted((("#%02x%02x%02x" % (int(r), int(g), int(b))), int(a))\n                       for r, g, b, a in _RGBA.findall(rendered))\n        want = sorted((getattr(C, base).lower(), getattr(C, alpha))\n                      for base, alpha in made_of)\n        assert found == want, f"{template}: rendered {found}, made of {want}"\n\n\ndef test_nothing_moved_that_was_not_ruled():\n    """Held BY NAME: each template call\'s (base, alpha) names, and each\n    palette entry\'s, are what this round made them. A value re-made from\n    another constant fails here even when the sheet still agrees with its\n    own source. The byte-for-byte before-and-after is tests/test_snapshots.py,\n    which compares all three rendered sheets whole."""\n    for template, made_of in MADE_OF.items():\n        names = sorted(_names(c) for c in _template_calls()[template])\n        assert names == sorted(made_of), f"{template}: {names}"\n    for palette, (base, alpha) in PALETTE_MADE_OF.items():\n        node = _palette_nodes()[palette]\n        entry = next(v for k, v in zip(node.keys, node.values)\n                     if isinstance(k, ast.Constant) and k.value == "checkbox_bg")\n        assert _names(entry) == (base, alpha), palette\n        live = getattr(C.ThemeManager, palette)["checkbox_bg"]\n        assert decompose(live) == (getattr(C, base).lower(), getattr(C, alpha))\n\n\ndef test_the_image_scrollbar_handle_is_grey_44_at_150():\n    """RNV-COLLAPSE-505050, closed here 2026-09-25: rgba(80, 80, 80, 150) in\n    both of IMAGE_STYLESHEET\'s handles, ruled onto grey(4) on 2026-09-02."""\n    handles = re.findall(r"QScrollBar::handle:(?:vertical|horizontal)\\s*\\{\\s*"\n                         r"background-color:\\s*([^;]+);", C.IMAGE_STYLESHEET)\n    assert len(handles) == 2, handles\n    for h in handles:\n        assert decompose(h.strip()) == ("#444444", 150) == (\n            C.APP_CHROME_DARK, C.SCROLLBAR_HANDLE_ALPHA), h\n\n\ndef test_no_composed_literal_is_left_in_the_application():\n    """Every EVALUATED string in the application\'s own source that spells a\n    named colour at an alpha. Docstrings are mentions; alpha 0 is not a\n    colour; a base no constant names has no row; and the debug overlay is\n    diagnostic, outside the brand by rule."""\n    named = {v.lower() for n, v in vars(C).items()\n             if n.isupper() and isinstance(v, str)\n             and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}\n    strays, files = [], 0\n    for rel, tree in _sources():\n        if rel.as_posix() in DIAGNOSTIC_FILES:\n            continue\n        files += 1\n        skip = set(_bare_strings(tree))\n        for node in ast.walk(tree):\n            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \\\n                    and node.name in DIAGNOSTIC_FUNCTIONS:\n                skip |= {id(n) for n in ast.walk(node)}\n            if isinstance(node, (ast.Assign, ast.AnnAssign)):\n                t = node.targets[0] if isinstance(node, ast.Assign) else node.target\n                if getattr(t, "id", None) in DIAGNOSTIC_NAMES:\n                    skip |= {id(n) for n in ast.walk(node)}\n        for node in ast.walk(tree):\n            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):\n                continue\n            if id(node) in skip:\n                continue\n            for spelled in _COMPOSED.findall(node.value):\n                base, alpha = _parts_of(spelled)\n                if alpha and base in named:\n                    strays.append(f"{rel}:{node.lineno}  {spelled}")\n    # 32 application files on 2026-09-25; below 20 the walk has lost a package.\n    assert files >= 20, f"only {files} files swept -- the walk has gone blind"\n    assert not strays, ("composed values still written out rather than "\n                        "derived:\\n  " + "\\n  ".join(strays))\n\n\ndef test_the_debug_overlay_stays_outside_the_brand():\n    """The exclusion rule, asserted: DEBUG_OVERLAY_COLORS holds literals, and\n    no brand constant or helper call appears in it."""\n    node = next(n for n in _module().body if isinstance(n, (ast.Assign, ast.AnnAssign))\n                and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target,\n                            "id", None) == "DEBUG_OVERLAY_COLORS")\n    bound = [ast.unparse(v) for v in node.value.values\n             if not isinstance(v, ast.Constant)]\n    assert not bound, f"the debug overlay follows the application\'s values: {bound}"\n    # ... and nothing rebinds it after the literal: the dict is written before\n    # any brand constant exists, so a later assignment is the only way in\n    assert C.DEBUG_OVERLAY_COLORS == ast.literal_eval(node.value), (\n        "DEBUG_OVERLAY_COLORS is changed after it is written")\n\n\ndef test_the_collapsed_value_is_gone_in_every_spelling():\n    found = []\n    for rel, tree in _sources():\n        bare = _bare_strings(tree)\n        for node in ast.walk(tree):\n            if (isinstance(node, ast.Constant) and isinstance(node.value, str)\n                    and id(node) not in bare and "#505050" in colours_in(node.value)):\n                found.append(f"{rel}:{node.lineno}")\n            values = None\n            if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in (3, 4):\n                values = node.elts\n            elif isinstance(node, ast.Call) and len(node.args) >= 3 and (\n                    getattr(node.func, "id", None) or getattr(node.func, "attr", None)\n                    ) in ("QColor", "fromRgb", "QPen", "QBrush"):\n                values = node.args\n            if values:\n                ints = tuple(v.value for v in values[:3]\n                             if isinstance(v, ast.Constant) and type(v.value) is int)\n                if ints == (80, 80, 80):\n                    found.append(f"{rel}:{node.lineno}  (80, 80, 80)")\n    assert not found, "#505050 is still here:\\n  " + "\\n  ".join(found)\n    assert "#505050" not in colours_in(C.IMAGE_STYLESHEET)\n    assert colours_in("rgba(80, 80, 80, 150)") == {"#505050"}, "the decoder is blind"\n\n# RNV-DERIVE-ALPHA\n'

SNAPSHOT_OLD = {'snapshots/stylesheet_dark.txt': '\nQMainWindow {\n    background-color: #000000;\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQWidget {\n    background-color: #000000;\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQPushButton {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 2px;\n    border-radius: 4px;\n    font-weight: bold;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQPushButton:hover {\n    background-color: #333333;\n    border-color: #333333;\n}\n\nQPushButton:pressed {\n    background-color: #444444;\n    color: #000000;\n    border-color: #333333;\n}\n\nQLineEdit {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n    min-height: 16px;\n    selection-background-color: #d2bc93;\n    selection-color: #000000;\n}\n\nQLineEdit:focus {\n    border-color: #d2bc93;\n}\n\nQLabel {\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQSlider::groove:horizontal {\n    border: 1px solid #333333;\n    height: 8px;\n    background: #1a1a1a;\n    border-radius: 4px;\n}\n\nQSlider::handle:horizontal {\n    background: #dddddd;\n    border: 1px solid #333333;\n    width: 18px;\n    border-radius: 9px;\n    margin: -5px 0;\n}\n\nQSlider::handle:horizontal:hover {\n    background: #d2bc93;\n}\n\nQScrollArea {\n    background-color: #000000;\n    border: 1px solid #333333;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQScrollBar:vertical {\n    background-color: transparent;\n    width: 15px;\n    border: none;\n}\n\nQScrollBar::handle:vertical {\n    background-color: rgba(51, 51, 51, 0.7);\n    min-height: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:vertical:hover {\n    background-color: #d2bc93;\n}\n\nQScrollBar::sub-page:vertical {\n    background-color: transparent;\n}\n\nQScrollBar::add-page:vertical {\n    background-color: transparent;\n}\n\nQScrollBar:horizontal {\n    background-color: transparent;\n    height: 15px;\n    border: none;\n}\n\nQScrollBar::handle:horizontal {\n    background-color: rgba(51, 51, 51, 0.7);\n    min-width: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:horizontal:hover {\n    background-color: #d2bc93;\n}\n\nQScrollBar::sub-page:horizontal {\n    background-color: transparent;\n}\n\nQScrollBar::add-page:horizontal {\n    background-color: transparent;\n}\n\nQScrollBar::add-line, QScrollBar::sub-line {\n    border: none;\n    background: none;\n}\n\nQStatusBar {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    border-top: 1px solid #333333;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQStatusBar QLabel {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    padding: 2px 4px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQCheckBox {\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQCheckBox::indicator {\n    width: 13px;\n    height: 13px;\n    background-color: #1a1a1a;\n    border: 1px solid #333333;\n}\n\nQCheckBox::indicator:checked {\n    background-color: #d2bc93;\n    border-color: #d2bc93;\n}\n\nQSplitter::handle {\n    background-color: #333333;\n}\n\nQSplitter::handle:horizontal {\n    width: 3px;\n}\n\nQSplitter::handle:vertical {\n    height: 3px;\n}\n\nQComboBox {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQComboBox:hover {\n    border-color: #d2bc93;\n}\n\nQComboBox QAbstractItemView {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    selection-background-color: #d2bc93;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQComboBox QAbstractItemView::item:hover {\n    background-color: #333333;\n    color: #d2bc93;\n}\n\nQComboBox QAbstractItemView::item:selected {\n    background-color: #d2bc93;\n    color: #000000;\n}\n', 'snapshots/stylesheet_image.txt': '\nQMainWindow {\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQMainWindow > QWidget {\n    background-color: transparent;\n}\n\nQWidget {\n    background-color: transparent;\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQFrame, QScrollArea, QLabel {\n    background-color: transparent;\n}\n\nQPushButton {\n    background-color: #1a1a1a;\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 2px;\n    border-radius: 4px;\n    font-weight: bold;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQPushButton:hover {\n    background-color: #333333;\n    border-color: #333333;\n}\n\nQPushButton:pressed {\n    background-color: #444444;\n    color: #000000;\n    border-color: #333333;\n}\n\nQLineEdit {\n    background-color: rgba(0, 0, 0, 171);\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n    min-height: 16px;\n    selection-background-color: #d2bc93;\n    selection-color: #000000;\n}\n\nQLineEdit:focus {\n    border-color: #d2bc93;\n}\n\nQLabel {\n    color: #dddddd;\n    background-color: transparent;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQSlider::groove:horizontal {\n    border: 1px solid #333333;\n    height: 8px;\n    background: #1a1a1a;\n    border-radius: 4px;\n}\n\nQSlider::handle:horizontal {\n    background: #dddddd;\n    border: 1px solid #333333;\n    width: 18px;\n    border-radius: 9px;\n    margin: -5px 0;\n}\n\nQSlider::handle:horizontal:hover {\n    background: #d2bc93;\n}\n\nQScrollArea {\n    background-color: transparent;\n    border: 1px solid rgba(51, 51, 51, 100);\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQScrollArea::viewport {\n    background-color: transparent;\n}\n\nQScrollArea QWidget {\n    background-color: transparent;\n}\n\nQScrollArea::corner {\n    background-color: transparent;\n}\n\nQScrollBar:vertical {\n    background-color: rgba(51, 51, 51, 100);\n    width: 15px;\n    border: none;\n}\n\nQScrollBar::handle:vertical {\n    background-color: rgba(80, 80, 80, 150);\n    min-height: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:vertical:hover {\n    background-color: #d2bc93;\n}\n\nQScrollBar::sub-page:vertical {\n    background-color: transparent;\n}\n\nQScrollBar::add-page:vertical {\n    background-color: transparent;\n}\n\nQScrollBar:horizontal {\n    background-color: rgba(51, 51, 51, 100);\n    height: 15px;\n    border: none;\n}\n\nQScrollBar::handle:horizontal {\n    background-color: rgba(80, 80, 80, 150);\n    min-width: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:horizontal:hover {\n    background-color: #d2bc93;\n}\n\nQScrollBar::sub-page:horizontal {\n    background-color: transparent;\n}\n\nQScrollBar::add-page:horizontal {\n    background-color: transparent;\n}\n\nQScrollBar::add-line, QScrollBar::sub-line {\n    border: none;\n    background: none;\n}\n\nQStatusBar {\n    background-color: rgba(26, 26, 26, 200);\n    color: #dddddd;\n    border-top: 1px solid #333333;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQStatusBar QLabel {\n    background-color: transparent;\n    color: #dddddd;\n    padding: 2px 4px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQCheckBox {\n    color: #dddddd;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQCheckBox::indicator {\n    width: 13px;\n    height: 13px;\n    background-color: rgba(0, 0, 0, 100);\n    border: 1px solid #555555;\n}\n\nQCheckBox::indicator:checked {\n    background-color: #d2bc93;\n    border-color: #d2bc93;\n}\n\nQSplitter::handle {\n    background-color: #333333;\n}\n\nQSplitter::handle:horizontal {\n    width: 3px;\n}\n\nQSplitter::handle:vertical {\n    height: 3px;\n}\n\nQComboBox {\n    background-color: rgba(26, 26, 26, 191);\n    color: #dddddd;\n    border: 1px solid #333333;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQComboBox:hover {\n    border-color: #d2bc93;\n}\n\nQComboBox QAbstractItemView {\n    background-color: rgba(26, 26, 26, 191);\n    color: #dddddd;\n    selection-background-color: #d2bc93;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQComboBox QAbstractItemView::item:hover {\n    background-color: #333333;\n    color: #d2bc93;\n}\n\nQComboBox QAbstractItemView::item:selected {\n    background-color: #d2bc93;\n    color: #000000;\n}\n', 'snapshots/stylesheet_light.txt': '\nQMainWindow {\n    background-color: #f5f5f5;\n    color: #000000;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQWidget {\n    background-color: #f5f5f5;\n    color: #000000;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQPushButton {\n    background-color: #ffffff;\n    color: #000000;\n    border: 1px solid #cccccc;\n    padding: 2px;\n    border-radius: 4px;\n    font-weight: bold;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQPushButton:hover {\n    background-color: #333333;\n    border-color: #cccccc;\n}\n\nQPushButton:pressed {\n    background-color: #444444;\n    color: #ffffff;\n    border-color: #cccccc;\n}\n\nQLineEdit {\n    background-color: #ffffff;\n    color: #000000;\n    border: 1px solid #cccccc;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n    min-height: 16px;\n    selection-background-color: #8c7337;\n    selection-color: #ffffff;\n}\n\nQLineEdit:focus {\n    border-color: #8c7337;\n}\n\nQLabel {\n    color: #000000;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQSlider::groove:horizontal {\n    border: 1px solid #cccccc;\n    height: 8px;\n    background: #ffffff;\n    border-radius: 4px;\n}\n\nQSlider::handle:horizontal {\n    background: #666666;\n    border: 1px solid #888888;\n    width: 18px;\n    border-radius: 9px;\n    margin: -5px 0;\n}\n\nQSlider::handle:horizontal:hover {\n    background: #8c7337;\n}\n\nQScrollArea {\n    background-color: #ffffff;\n    border: 1px solid #cccccc;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQScrollBar:vertical {\n    background-color: #f5f5f5;\n    width: 15px;\n    border: none;\n}\n\nQScrollBar::handle:vertical {\n    background-color: #cccccc;\n    min-height: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:vertical:hover {\n    background-color: #8c7337;\n}\n\nQScrollBar::sub-page:vertical {\n    background-color: #f5f5f5;\n}\n\nQScrollBar::add-page:vertical {\n    background-color: #f5f5f5;\n}\n\nQScrollBar:horizontal {\n    background-color: #f5f5f5;\n    height: 15px;\n    border: none;\n}\n\nQScrollBar::handle:horizontal {\n    background-color: #cccccc;\n    min-width: 20px;\n    border-radius: 7px;\n}\n\nQScrollBar::handle:horizontal:hover {\n    background-color: #8c7337;\n}\n\nQScrollBar::sub-page:horizontal {\n    background-color: #f5f5f5;\n}\n\nQScrollBar::add-page:horizontal {\n    background-color: #f5f5f5;\n}\n\nQScrollBar::add-line, QScrollBar::sub-line {\n    border: none;\n    background: none;\n}\n\nQStatusBar {\n    background-color: #f5f5f5;\n    color: #000000;\n    border-top: 1px solid #cccccc;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQStatusBar QLabel {\n    background-color: #f5f5f5;\n    color: #000000;\n    padding: 2px 4px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 9px;\n}\n\nQCheckBox {\n    color: #000000;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQCheckBox::indicator {\n    width: 13px;\n    height: 13px;\n    background-color: #ffffff;\n    border: 1px solid #cccccc;\n}\n\nQCheckBox::indicator:checked {\n    background-color: #8c7337;\n    border-color: #8c7337;\n}\n\nQSplitter::handle {\n    background-color: #cccccc;\n}\n\nQSplitter::handle:horizontal {\n    width: 3px;\n}\n\nQSplitter::handle:vertical {\n    height: 3px;\n}\n\nQComboBox {\n    background-color: #ffffff;\n    color: #000000;\n    border: 1px solid #cccccc;\n    padding: 4px;\n    border-radius: 3px;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n    font-size: 10px;\n}\n\nQComboBox:hover {\n    border-color: #8c7337;\n}\n\nQComboBox QAbstractItemView {\n    background-color: #ffffff;\n    color: #000000;\n    selection-background-color: #8c7337;\n    font-family: "Montserrat Black", "Arial Black", "Arial", sans-serif;\n}\n\nQComboBox QAbstractItemView::item:hover {\n    background-color: #eeeeee;\n    color: #7e6529;\n}\n\nQComboBox QAbstractItemView::item:selected {\n    background-color: #8c7337;\n    color: #ffffff;\n}\n'}


def edits(tree) -> None:
    """Every substitution, against the in-memory tree, each anchor checked
    for its exact count first. test_rnv_color_mixer.py is not touched: it
    is SHA-256-locked, and verify() checks its hash exactly as CI does."""
    tree.sub('utils/config.py',
             '        max(0, min(255, c + step)) for c in (r, g, b))\n',
             '        max(0, min(255, c + step)) for c in (r, g, b))\n\n\ndef _hex6(hex_color: str) -> str:\n    """The six hex digits of a colour, or ValueError. Shared by the two\n    helpers below so they refuse exactly the same inputs."""\n    h = hex_color.lstrip("#")\n    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):\n        raise ValueError(f"{hex_color!r} is not a six-digit hex colour")\n    return h\n\n\ndef _alpha_byte(alpha: int) -> int:\n    """An alpha as the 0-255 byte, or an error. A fraction is refused, not\n    scaled: Qt TRUNCATES a fractional alpha in a stylesheet -- 0.7 is 178, not\n    179 -- and a helper that rounded would move a pixel inside a respelling."""\n    if isinstance(alpha, bool) or not isinstance(alpha, int):\n        raise TypeError(f"alpha {alpha!r} is not an int byte")\n    if not 0 <= alpha <= 255:\n        raise ValueError(f"alpha {alpha} is outside 0-255")\n    return alpha\n\n\ndef translucent(hex_color: str, alpha: int) -> str:\n    """A colour at an alpha, as Qt\'s eight-digit #aarrggbb -- ALPHA FIRST.\n\n    A value computed from another value is computed in code; a written-down\n    derivative is orphaned the moment its source moves, and nothing says so.\n    #aarrggbb is the one spelling valid in a stylesheet AND in QColor(), which\n    reads rgba() as INVALID and paints it opaque black. Lower case, as the\n    register writes hex; rnv-icon-builder\'s helper of the same name agrees.\n    """\n    return "#%02x%s" % (_alpha_byte(alpha), _hex6(hex_color).lower())\n\n\ndef translucent_rgba(hex_color: str, alpha: int) -> str:\n    """The same derivation spelled rgba(r, g, b, a) -- FOR THE STYLESHEET\n    TEMPLATES ONLY, where a value can never reach QColor().\n\n    Two reasons it exists here. The locked suite asserts "rgba(" is in\n    IMAGE_STYLESHEET, and the lock stands. And tests/test_snapshots.py compares\n    the rendered sheets byte for byte, so the templates keep the spelling they\n    had and the snapshots move only where a pixel was ruled to.\n    tests/test_derived_values.py fails if it is used anywhere else.\n    """\n    h = _hex6(hex_color)\n    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))\n    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"\n', 1)
    tree.sub('utils/config.py',
             'APP_CHROME_DARK: Final[str] = "#444444"\n"""grey(4). The structural grey of a control in dark and image: the slider\ngroove, and the border and separator of a menu.\n',
             'APP_CHROME_DARK: Final[str] = "#444444"\n"""grey(4). The structural grey of a control in dark and image: the slider\ngroove, and the border and separator of a menu -- and, from 2026-09-25, the\nimage-mode scrollbar handle at SCROLLBAR_HANDLE_ALPHA. That handle was\n#505050, which RNV-COLLAPSE-505050 ruled onto grey(4) -- GREY_44 in the\nother applications -- and it is resting chrome, not a pressed button.\n', 1)
    tree.sub('utils/config.py',
             'class ThemeManager:\n',
             '# ==================== COMPOSITE ALPHAS ====================\n# A composite is a named colour AT AN ALPHA. The colour half is a name, so a\n# register move reaches it; the alpha half is one of these, so the same move\n# carries every alpha form of the colour. Each byte is the one its literal\n# already carried -- the dark handle\'s measured, since it was written as 0.7.\n#\n# SEVERAL BYTES REPEAT UNDER DIFFERENT NAMES, ON PURPOSE. Identical numbers\n# doing unrelated jobs stay separate, or retuning one silently retunes the rest.\n\nSCROLLBAR_HANDLE_ALPHA_DARK: Final[int] = 0xB2\n"""178. The dark main-surface scrollbar handle (APP_BORDER_DARK). Written\nrgba(51, 51, 51, 0.7) until 2026-09-25. 0.7 * 255 is 178.5, and Qt\'s\nstylesheet parser gives 178 -- MEASURED on three grounds, not computed."""\n\nSCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96\n"""150. The image-mode scrollbar handle (APP_CHROME_DARK), the byte all five\napplications use. Its colour was #505050 until 2026-09-25."""\n\nSCROLLBAR_BG_ALPHA: Final[int] = 0x64\n"""100. The image-mode scrollbar groove (APP_BORDER_DARK)."""\n\nSCROLL_AREA_BORDER_ALPHA: Final[int] = 0x64\n"""100. The image-mode scroll area\'s edge (APP_BORDER_DARK)."""\n\nIMAGE_FIELD_ALPHA: Final[int] = 0xAB\n"""171. The image-mode line edit\'s ground (TRUE_BLACK)."""\n\nSTATUS_BAR_ALPHA: Final[int] = 0xC8\n"""200. The image-mode status bar (APP_SURFACE_DARK)."""\n\nIMAGE_CHECKBOX_ALPHA: Final[int] = 0x64\n"""100. The image-mode checkbox indicator\'s ground (TRUE_BLACK)."""\n\nCOMBO_ALPHA: Final[int] = 0xBF\n"""191. The image-mode combo box and its drop-down list (APP_SURFACE_DARK)."""\n\nCHECKBOX_BG_ALPHA_DARK: Final[int] = 0xE6\n"""230. checkbox_bg in the dark and image palettes (APP_SURFACE_DARK). Nothing\nreads that key today; derived all the same, so it cannot fall behind."""\n\nCHECKBOX_BG_ALPHA_LIGHT: Final[int] = 0xC8\n"""200. checkbox_bg in the light palette (WHITE). Unread, like its dark twin."""\n\n\nclass ThemeManager:\n', 1)
    tree.sub('utils/config.py',
             "        'checkbox_bg': 'rgba(26, 26, 26, 230)',\n",
             "        'checkbox_bg': translucent(APP_SURFACE_DARK, CHECKBOX_BG_ALPHA_DARK),\n", 2)
    tree.sub('utils/config.py',
             "        'checkbox_bg': 'rgba(255, 255, 255, 200)',\n",
             "        'checkbox_bg': translucent(WHITE, CHECKBOX_BG_ALPHA_LIGHT),\n", 1)
    tree.sub('utils/config.py',
             '    background-color: rgba(51, 51, 51, 0.7);\n',
             '    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_HANDLE_ALPHA_DARK)};\n', 2)
    tree.sub('utils/config.py',
             '    background-color: rgba(0, 0, 0, 171);\n',
             '    background-color: {translucent_rgba(TRUE_BLACK, IMAGE_FIELD_ALPHA)};\n', 1)
    tree.sub('utils/config.py',
             '    border: 1px solid rgba(51, 51, 51, 100);\n',
             '    border: 1px solid {translucent_rgba(APP_BORDER_DARK, SCROLL_AREA_BORDER_ALPHA)};\n', 1)
    tree.sub('utils/config.py',
             '    background-color: rgba(51, 51, 51, 100);\n',
             '    background-color: {translucent_rgba(APP_BORDER_DARK, SCROLLBAR_BG_ALPHA)};\n', 2)
    tree.sub('utils/config.py',
             '    background-color: rgba(80, 80, 80, 150);\n',
             '    background-color: {translucent_rgba(APP_CHROME_DARK, SCROLLBAR_HANDLE_ALPHA)};\n', 2)
    tree.sub('utils/config.py',
             '    background-color: rgba(26, 26, 26, 200);\n',
             '    background-color: {translucent_rgba(APP_SURFACE_DARK, STATUS_BAR_ALPHA)};\n', 1)
    tree.sub('utils/config.py',
             '    background-color: rgba(0, 0, 0, 100);\n',
             '    background-color: {translucent_rgba(TRUE_BLACK, IMAGE_CHECKBOX_ALPHA)};\n', 1)
    tree.sub('utils/config.py',
             '    background-color: rgba(26, 26, 26, 191);\n',
             '    background-color: {translucent_rgba(APP_SURFACE_DARK, COMBO_ALPHA)};\n', 2)
    tree.sub('snapshots/stylesheet_dark.txt',
             '    background-color: rgba(51, 51, 51, 0.7);\n',
             '    background-color: rgba(51, 51, 51, 178);\n', 2)
    tree.sub('snapshots/stylesheet_image.txt',
             '    background-color: rgba(80, 80, 80, 150);\n',
             '    background-color: rgba(68, 68, 68, 150);\n', 2)
    tree.sub('tests/conftest.py',
             '# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the\n',
             '# RNV-DERIVE-ALPHA, 2026-09-25 -- every colour this application writes\n# at an alpha is DERIVED: rgba() inside the three stylesheet templates,\n# #aarrggbb everywhere else, both from a named base and a declared byte.\n# The image scrollbar handle left #505050 for grey(4), APP_CHROME_DARK, at\n# 150 -- RNV-COLLAPSE-505050, by ruling. tests/test_derived_values.py.\n# RNV-GOLD-HOVER, 2026-09-12 -- every hover on the main surface takes the\n', 1)


def _evaluate(src: str, root: Path) -> dict:
    """The edited utils/config.py, run in memory WITHOUT its logger import --
    the one statement with a side effect. Everything else at module level is
    a definition or a constant expression, so this writes nothing."""
    module = ast.parse(src)
    module.body = [n for n in module.body
                   if not (isinstance(n, ast.Try) and 'Logger' in ast.unparse(n))]
    ns = {'__file__': str(root / 'utils' / 'config.py'), '__name__': 'utils.config'}
    exec(compile(module, 'utils/config.py (edited)', 'exec'), ns)
    return ns


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    root = Path.cwd()
    ns = _evaluate(tree.read('utils/config.py'), root)

    # EVERY RENDERED SHEET IS BYTE-IDENTICAL TO ITS EDITED SNAPSHOT -- the
    # same comparison tests/test_snapshots.py makes, made before writing.
    for name, rel in (('DARK_STYLESHEET', 'snapshots/stylesheet_dark.txt'),
                      ('LIGHT_STYLESHEET', 'snapshots/stylesheet_light.txt'),
                      ('IMAGE_STYLESHEET', 'snapshots/stylesheet_image.txt')):
        assert ns[name] == tree.read(rel), f'{name} does not render its snapshot'

    # AND EACH SNAPSHOT MOVED BY EXACTLY ITS NAMED LINES
    for rel, old in SNAPSHOT_OLD.items():
        new_lines, old_lines = tree.read(rel).splitlines(), old.splitlines()
        assert len(new_lines) == len(old_lines), rel
        moved = [(a, b) for a, b in zip(old_lines, new_lines) if a != b]
        want = {'snapshots/stylesheet_dark.txt':
                    [('    background-color: rgba(51, 51, 51, 0.7);',
                      '    background-color: rgba(51, 51, 51, 178);')] * 2,
                'snapshots/stylesheet_image.txt':
                    [('    background-color: rgba(80, 80, 80, 150);',
                      '    background-color: rgba(68, 68, 68, 150);')] * 2,
                'snapshots/stylesheet_light.txt': []}[rel]
        assert moved == want, f'{rel} moved {moved}'

    # the locked suite's own assertions about these sheets still hold
    assert 'rgba(' in ns['IMAGE_STYLESHEET']
    assert '#d2bc93' in ns['DARK_STYLESHEET']
    assert '#8c7337' in ns['LIGHT_STYLESHEET']
    assert 'background-color: transparent' in ns['IMAGE_STYLESHEET']
    # ... and the locked file itself is untouched
    assert hashlib.sha256((root / LOCKED).read_bytes()).hexdigest() == LOCKED_SHA

    # the palettes' checkbox grounds, derived
    tm = ns['ThemeManager']
    assert tm.DARK_THEME['checkbox_bg'] == tm.IMAGE_THEME['checkbox_bg'] == '#e61a1a1a'
    assert tm.LIGHT_THEME['checkbox_bg'] == '#c8ffffff'

    # no rgba() literal is left in config.py but the debug overlay's, which
    # is diagnostic and outside the brand by rule; docstrings are mentions
    code = ast.parse(tree.read('utils/config.py'))
    skip = set()
    for n in ast.walk(code):
        body = getattr(n, 'body', None)
        if isinstance(body, list):
            skip |= {id(st.value) for st in body
                      if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}
    for n in code.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            t = n.targets[0] if isinstance(n, ast.Assign) else n.target
            if getattr(t, 'id', None) == 'DEBUG_OVERLAY_COLORS':
                skip |= {id(x) for x in ast.walk(n)}
    left = [n.lineno for n in ast.walk(code)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in skip
            and re.search(r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,', n.value)]
    assert not left, f'rgba() literals left in utils/config.py at lines {left}'
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
