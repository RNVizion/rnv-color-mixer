"""chart ruling 1: the control panel's descriptions in the muted text

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (d057935).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-27, decision 1 of the colour chart: "If they all split it for
each mode then it's fine to have 2 values, but make sure they are values we
are already using." They all split it the same way. Muted text is #888888 in
dark and image and #666666 in light in all five applications, and the
description labels that wrote `color: gray`/`grey` -- #808080 in every mode,
4.40:1 on the dark panels and 3.62:1 in light, under the 4.5 floor -- now read
the app's own muted key. No new colour: both values are already painted.

Here: the control panel's ten descriptions, through a helper beside the tips'
own that registers them for re-theming -- the panel is built before it knows
its mode. The mixer's muted key is text_hint. Its light value read the slider
handle's constant; it gets its own, APP_HINT_LIGHT, at the same #666666, the
split-not-renamed rule this app already applies to APP_MENU_DIM_DARK.
Rendered: 21 of 105 captures change, 7 per mode, every changed pixel the grey
recoloured.
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
SENTINEL = 'RNV-MUTED-DESCRIPTIONS'
SENTINEL_FILE = 'tests/test_hint_text.py'
GUARD = 'tests/test_hint_text.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_hint_text.py', 'tests/test_mixer_wiring.py', 'tests/test_mode_switch_restyle.py']
DESCRIPTION = "chart ruling 1: the control panel's descriptions in the muted text"

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69'])\n"
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
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR]),
]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '769b9b7034c0599b5d655cfb502741706693e765d51e2db95406c140a6b92ffd', '.github/workflows/tests-windows.yml': 'd123e5da015c9b988e5c52e9c0bb9879d492365b6db6c1f3672dc1b34f57d967'}

SHADOWS = {"config.py", "conftest.py", "package_d_panel.py", "test_rnv_color_mixer.py"}

LEFT_ALONE = ['the fine-tune hint, which already reads text_hint and keeps its grounds.', "LIGHT menu_disabled, still APP_HANDLE_EDGE_LIGHT: that constant's second role is already declared in tests/test_mixer_wiring.py's SPLITS."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('utils/config.py',
             'APP_HANDLE_LIGHT: Final[str] = "#666666"\n"""Slider handle at rest, light."""\n',
             'APP_HANDLE_LIGHT: Final[str] = "#666666"\n"""Slider handle at rest, light."""\n\nAPP_HINT_LIGHT: Final[str] = "#666666"\n"""grey(6). Hint and muted text in light -- the step the other four apps\nuse for muted text in light, as APP_HINT_DARK is in dark.\n\nSPLIT, NOT RENAMED, 2026-09-27 (RNV-MUTED-DESCRIPTIONS). LIGHT text_hint read\nAPP_HANDLE_LIGHT, the same hex doing another job. When the control panel\'s\nten descriptions joined the fine-tune hint on this key, text would have\nmoved every time the slider handle did."""\n')
    tree.sub('utils/config.py',
             '    "APP_HANDLE_EDGE_LIGHT": "step",\n',
             '    "APP_HANDLE_EDGE_LIGHT": "step",\n    "APP_HINT_LIGHT": "step",\n')
    tree.sub('utils/config.py',
             "        'text_hint': APP_HANDLE_LIGHT,\n",
             "        'text_hint': APP_HINT_LIGHT,\n")
    tree.sub('core/package_d_panel.py',
             'def _section_header_style(accent: str) -> str:\n',
             'def _style_description(panel, widget, tail: str) -> None:\n    """Paint a description in the muted text, and register it for\n    re-theming, as the tips are.\n\n    RNV-MUTED-DESCRIPTIONS, 2026-09-27 (ruling 1). These ten were\n    `color: gray` -- #808080 in every mode, under the 4.5 floor on this\n    panel\'s light ground. text_hint is #888888 in dark and image and\n    #666666 in light: the muted text all five applications already paint.\n    """\n    descriptions = panel.__dict__.setdefault("_themed_descriptions", [])\n    entry = (widget, tail)\n    if entry not in descriptions:\n        descriptions.append(entry)\n    muted = _theme_colors(bool(getattr(panel, "_is_dark", True)))["text_hint"]\n    widget.setStyleSheet(f"color: {muted}; " + tail)\n\n\ndef _section_header_style(accent: str) -> str:\n')
    tree.sub('core/package_d_panel.py',
             '        desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES[\'small\']}px;")\n',
             '        _style_description(self, desc, f"font-size: {config.FONT_SIZES[\'small\']}px;")\n', times=6)
    tree.sub('core/package_d_panel.py',
             '        export_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n',
             '        _style_description(self, export_desc, f"font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n')
    tree.sub('core/package_d_panel.py',
             '        palette_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n',
             '        _style_description(self, palette_desc, f"font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n')
    tree.sub('core/package_d_panel.py',
             '        picker_desc.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n',
             '        _style_description(self, picker_desc, f"font-size: {config.FONT_SIZES[\'small\']}px; margin-bottom: 6px;")\n')
    tree.sub('core/package_d_panel.py',
             '        self.algo_desc_label.setStyleSheet(f"color: gray; font-size: {config.FONT_SIZES[\'small\']}px; margin-left: 5px;")\n',
             '        _style_description(self, self.algo_desc_label, f"font-size: {config.FONT_SIZES[\'small\']}px; margin-left: 5px;")\n')
    tree.sub('core/package_d_panel.py',
             "        for _badge in getattr(self, '_themed_key_badges', []):\n            try:\n                _style_key_badge(self, _badge)\n            except RuntimeError:\n                pass\n",
             '        for _badge in getattr(self, \'_themed_key_badges\', []):\n            try:\n                _style_key_badge(self, _badge)\n            except RuntimeError:\n                pass\n        for _desc, _desc_tail in getattr(self, \'_themed_descriptions\', []):\n            try:\n                _desc.setStyleSheet(f"color: {t[\'text_hint\']}; " + _desc_tail)\n            except RuntimeError:\n                pass\n')
    tree.sub('tests/test_hint_text.py',
             '"""\nThe fine-tune hint label, measured against the ground it actually sits on.\n\n`text_hint` has exactly one consumer: core/color_fine_tune.py, a 10px QLabel\nunder each slider. It is added into the QFrame built by\n`_create_sliders_section`, so its ground is `panel_secondary` -- NOT\n`panel_bg`, which paints the QDialog behind that frame. Measuring against the\ndialog would have said light was fine when it was not.\n',
             '"""\nThe muted text, measured against the grounds it actually sits on.\n\n`text_hint` has two consumers. The fine-tune hint in core/color_fine_tune.py\nis a 10px QLabel under each slider, added into the QFrame built by\n`_create_sliders_section`, so its ground is `panel_secondary` -- NOT\n`panel_bg`, which paints the QDialog behind that frame. Measuring against the\ndialog would have said light was fine when it was not. The control panel\'s\nten descriptions in core/package_d_panel.py sit on its tab pages, measured\nin the running app at #000000 in dark, #1a1a1a in image and #f5f5f5 in\nlight. `panel_bg` is #1a1a1a in dark -- the lighter, so the harder, ground\nfor a light ink -- and #f5f5f5 in light, so holding the hint on `panel_bg`\nbelow covers them.\n\nRNV-MUTED-DESCRIPTIONS, 2026-09-27 (ruling 1): the descriptions were\n`color: gray`, #808080 in every mode, until they joined this key -- the\nmuted text all five applications paint, #888888 in dark and image and\n#666666 in light.\n')
    tree.sub('tests/test_hint_text.py',
             'def test_the_hint_key_still_has_exactly_one_consumer():\n    """Guard the guard, and guard the docstring with it.\n\n    Every figure here assumes the label is the one in color_fine_tune. A second\n    consumer on a different ground would make this file measure the wrong pair\n    while still passing.\n    """\n',
             'def test_the_hint_key_has_exactly_its_two_consumers():\n    """Guard the guard, and guard the docstring with it.\n\n    Every figure here assumes the two consumers above and their two grounds.\n    A third consumer on a different ground would make this file measure the\n    wrong pair while still passing.\n    """\n')
    tree.sub('tests/test_hint_text.py',
             '    assert sites == ["core/color_fine_tune.py"], (\n        f"text_hint is read in {sites}. The grounds in this file were derived "\n        f"from color_fine_tune alone; re-derive them before trusting these "\n        f"figures.")\n',
             '    assert sorted(sites) == ["core/color_fine_tune.py", "core/package_d_panel.py"], (\n        f"text_hint is read in {sites}. The grounds in this file were derived "\n        f"from color_fine_tune and the control panel; re-derive them before "\n        f"trusting these figures.")\n')
    tree.sub('tests/test_hint_text.py',
             '        "the light hint is back to #888888, which reads 3.5407:1 on this "\n        "app\'s white frame")\n    assert contrast(light["text_hint"], light["panel_secondary"]) >= TEXT_FLOOR\n',
             '        "the light hint is back to #888888, which reads 3.5407:1 on this "\n        "app\'s white frame")\n    assert contrast(light["text_hint"], light["panel_secondary"]) >= TEXT_FLOOR\n\n\n# RNV-MUTED-DESCRIPTIONS\n# -------------------------------------------------- the descriptions (ruling 1)\n\ndef test_the_muted_values_are_the_ones_the_fleet_already_uses():\n    """Ruling 1 was conditional: two values are fine if every app splits it by\n    mode, and only with values already in use. Both halves, held here."""\n    assert THEMES["DARK"]["text_hint"] == THEMES["IMAGE"]["text_hint"] == "#888888"\n    assert THEMES["LIGHT"]["text_hint"] == "#666666"\n\n\ndef test_the_light_hint_has_its_own_name():\n    """Not the slider handle\'s: APP_HANDLE_LIGHT holds the same hex for\n    another job, and wired through it, text would move with the handle."""\n    import ast\n    import pathlib\n    from utils import config\n    src = pathlib.Path(config.__file__).read_text(encoding="utf-8-sig")\n    cls = next(n for n in ast.parse(src).body\n               if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")\n    light = next(n.value for n in cls.body\n                 if isinstance(n, (ast.Assign, ast.AnnAssign))\n                 and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target,\n                             "id", None) == "LIGHT_THEME")\n    value = next(v for k, v in zip(light.keys, light.values)\n                 if isinstance(k, ast.Constant) and k.value == "text_hint")\n    assert isinstance(value, ast.Name) and value.id == "APP_HINT_LIGHT", ast.unparse(value)\n    assert config.APP_HINT_LIGHT == config.APP_HANDLE_LIGHT == "#666666"\n\n\ndef test_no_label_is_written_in_a_css_grey():\n    """The literal the ruling retired, anywhere the application EVALUATES a\n    string. Docstrings and comments may still name it; code may not."""\n    import ast\n    import pathlib\n    import re\n    root = pathlib.Path(__file__).resolve().parent.parent\n    css_grey = re.compile(r"color\\s*:\\s*(gray|grey)\\b", re.I)\n    found, files = [], 0\n    for path in sorted(root.rglob("*.py")):\n        rel = path.relative_to(root)\n        if any(p in {"tests", ".git", "__pycache__", "build", "dist", ".venv", "snapshots"}\n               for p in rel.parts):\n            continue\n        if len(rel.parts) == 1 and rel.name.startswith(("test_", "up")):\n            continue\n        text = path.read_text(encoding="utf-8-sig", errors="replace")\n        if "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP" in text:\n            continue\n        files += 1\n        tree = ast.parse(text)\n        docs = {id(st.value) for node in ast.walk(tree)\n                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])\n                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}\n        found += [f"{rel}:{node.lineno}" for node in ast.walk(tree)\n                  if isinstance(node, ast.Constant) and isinstance(node.value, str)\n                  and id(node) not in docs and css_grey.search(node.value)]\n    assert files >= 20, f"only {files} files swept -- the walk has gone blind"\n    assert not found, "CSS grey still written as a colour:\\n  " + "\\n  ".join(found)\n')
    tree.sub('tests/test_mixer_wiring.py',
             "    '#666666': {'APP_HANDLE_LIGHT': 'the light slider handle at rest',\n                'APP_MENU_DIM_DARK': 'the disabled menu label in dark and image'},\n",
             "    '#666666': {'APP_HANDLE_LIGHT': 'the light slider handle at rest',\n                'APP_MENU_DIM_DARK': 'the disabled menu label in dark and image',\n                # RNV-MUTED-DESCRIPTIONS, 2026-09-27: hint and muted text,\n                # which had borrowed the handle's name.\n                'APP_HINT_LIGHT': 'hint and muted text in light'},\n")
    tree.sub('tests/test_mode_switch_restyle.py',
             '            assert f"color: {ink};" in credits[0].text(), f"{mode}: the credits footer"\n            about.close()\n    finally:\n        about.close()\n',
             '            assert f"color: {ink};" in credits[0].text(), f"{mode}: the credits footer"\n            about.close()\n    finally:\n        about.close()\n\n\ndef test_the_panel_descriptions_follow_every_mode(app_window):\n    """RNV-MUTED-DESCRIPTIONS, ruling 1 of 2026-09-27. The control panel\'s ten\n    descriptions were `color: gray` in every mode. They draw in text_hint now\n    -- #888888 in dark and image, #666666 in light -- and like the badges they\n    are built before the panel knows its mode, so set_theme() redraws them."""\n    app_window.open_package_d_panel()\n    panel = app_window._package_d_panel\n    descriptions = [w for w, _tail in getattr(panel, "_themed_descriptions", [])]\n    assert len(descriptions) == 10, len(descriptions)\n    try:\n        for mode in _cycle(app_window):\n            ink = _dialog_palette(mode)["text_hint"]\n            for widget in descriptions:\n                sheet = widget.styleSheet()\n                assert sheet.startswith(f"color: {ink}; "), (mode, widget.text()[:40], sheet)\n                assert "gray" not in sheet and "grey" not in sheet, sheet\n    finally:\n        panel.close()\n')


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
    def css_greys(src):
        tree = ast.parse(src)
        docs = {id(st.value) for node in ast.walk(tree)
                for st in (node.body if isinstance(getattr(node, "body", None), list) else [])
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)}
        pat = re.compile(r"color\s*:\s*(gray|grey)\b", re.I)
        return [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docs and pat.search(n.value)]

    # the light hint's own name: one constant, one provenance entry, one key
    old_cfg, new_cfg = _original(tree, "utils/config.py"), tree.read("utils/config.py")
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(new_top) - set(old_top) == {"APP_HINT_LIGHT"}, set(new_top) ^ set(old_top)
    assert new_top["APP_HINT_LIGHT"] == ast.dump(ast.Constant("#666666"))
    assert old_top["APP_HANDLE_LIGHT"] == new_top["APP_HANDLE_LIGHT"]
    moved = sorted(n for n in old_top if old_top[n] != new_top.get(n))
    assert moved == ["NEUTRAL_PROVENANCE"], moved
    assert "'APP_HINT_LIGHT': 'step'" in ast.unparse(ast.parse(new_cfg)) or \
        '"APP_HINT_LIGHT": "step"' in new_cfg

    def palettes(src):
        cls = next(n for n in ast.parse(src).body
                   if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
        out = {}
        for node in cls.body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) in ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"):
                out[t.id] = _entries(node.value)
        return out
    before, after = palettes(old_cfg), palettes(new_cfg)
    for name in before:
        changed = sorted(k for k in before[name] if before[name][k] != after[name].get(k))
        assert changed == (["text_hint"] if name == "LIGHT_THEME" else []), (name, changed)
        assert set(before[name]) == set(after[name]), name
    assert after["LIGHT_THEME"]["text_hint"] == ast.dump(ast.Name("APP_HINT_LIGHT", ast.Load()))

    # the ten descriptions: through the helper, each with the tail it had
    old_p, new_p = _original(tree, "core/package_d_panel.py"), tree.read("core/package_d_panel.py")
    assert css_greys(old_p) and not css_greys(new_p), css_greys(new_p)
    def was(src):
        out = []
        for c in ast.walk(ast.parse(src)):
            if (isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "setStyleSheet"
                    and c.args and isinstance(c.args[0], ast.JoinedStr)
                    and isinstance(c.args[0].values[0], ast.Constant)
                    and c.args[0].values[0].value.startswith("color: gray; ")):
                js = c.args[0]
                head = ast.Constant(js.values[0].value[len("color: gray; "):])
                rest = ast.JoinedStr([head] + js.values[1:])
                out.append((ast.unparse(c.func.value), ast.unparse(rest)))
        return sorted(out)
    def now(src):
        return sorted((ast.unparse(c.args[1]), ast.unparse(c.args[2]))
                      for c in ast.walk(ast.parse(src))
                      if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "_style_description")
    assert len(was(old_p)) == 10 and was(old_p) == now(new_p), (was(old_p), now(new_p))
    loop = ast.unparse(_function(new_p, "_apply_widget_stylesheet", "PackageDPanel"))
    assert "_themed_descriptions" in loop and "t['text_hint']" in loop

    for rel in ("tests/test_hint_text.py", "tests/test_mixer_wiring.py",
                "tests/test_mode_switch_restyle.py"):
        ast.parse(tree.read(rel))
    assert SENTINEL in tree.read("tests/test_hint_text.py")
    assert "'APP_HINT_LIGHT': 'hint and muted text in light'" in tree.read("tests/test_mixer_wiring.py")
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
