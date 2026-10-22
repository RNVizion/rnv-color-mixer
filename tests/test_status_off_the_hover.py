"""STATUS TEXT STAYS OFF THE HOVER PLATE (#76 A, 2026-10-22).

The same file in all five RNV desktop applications.

THE FAULT IT KEEPS AWAY. The register's dark status text colors were walked
against the card, APP["card"]. The hover plate, APP["panel-hover"], is lighter,
and on it they read 3.61 (success-text), 3.64 (warning-text) and 3.58
(error-text): under the 4.5:1 floor. BRAND_GOLD clears every dark surface;
these do not.

WHY A GUARD AND NOT NEW VALUES. Measured on 2026-09-06 and again on
2026-10-22: no status color sits in a :hover rule or on a hover plate in any
of the five apps, so nothing fails on screen. #74 A keeps the transition
exemption to the main button alone, so status text on a hover plate would be
a real failure, not a ruled dim. #76 A: hold the apps to where they are,
rather than move register values for a pairing nothing draws.

WHAT IT READS. Every stylesheet rule written in the application's own source
(tests and delivery scripts left out). It fails on a rule that
  - carries :hover and names a status color in its body, or
  - names a status color and a hover plate in the same body.
A status color is a name with success, warning or error in it, or status_active; a
hover plate is panel_hover, hover_bg, main_btn_hover_bg, APP_PANEL_HOVER, or
the register's values for APP["panel-hover"] and APP["border"] written out.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import engine.brand as B

ROOT = Path(__file__).resolve().parent.parent

STATUS = re.compile(r"(?i)success|warning|error|status_active")
PLATE = re.compile(r"(?i)panel_hover|\bhover_bg\b|main_btn_hover_bg|APP_PANEL_HOVER|"
                   + re.escape(B.APP["panel-hover"]) + "|" + re.escape(B.APP["border"]))
#: a rule inside a string: selector, then a body with no nested braces
RULE = re.compile(r"(?P<sel>[^{}]+)\{(?P<body>[^{}]*)\}")

#: folders that are not the application's: its tests, a venv, a build, a cache,
#: and any folder whose name starts with a dot (.git, .venv)
SKIP_DIRS = {"tests", "snapshots", "venv", "env", "build", "dist", "__pycache__", "site-packages", "node_modules"}

#: a sweep that finds fewer rules than this is not reading the stylesheets
MIN_HOVER_RULES = 10


def _sources() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        folders = rel.split("/")[:-1]
        if (any(f in SKIP_DIRS or f.startswith(".") for f in folders)
                or p.name.startswith(("test_", "up")) or p.name == "conftest.py"):
            continue
        out.append(p)
    return out


def _strings(tree: ast.AST) -> list[str]:
    """Every string the source writes, f-strings included. A placeholder is kept
    as <<expr>>, so a stylesheet's own braces are the only braces left."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                else:
                    parts.append("<<" + ast.unparse(v.value) + ">>")
            out.append("".join(parts))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _rules() -> list[tuple[str, str, str]]:
    found = []
    for path in _sources():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError as exc:  # a file the sweep cannot read is not a clean file
            raise AssertionError(f"cannot parse {path}: {exc}") from exc
        for s in _strings(tree):
            if "{" not in s:
                continue
            for m in RULE.finditer(s):
                sel = " ".join(m.group("sel").split())[-120:]
                found.append((path.relative_to(ROOT).as_posix(), sel, m.group("body")))
    return found


RULES = _rules()


def test_the_sweep_reads_the_stylesheets() -> None:
    hovers = [r for r in RULES if ":hover" in r[1]]
    assert len(hovers) >= MIN_HOVER_RULES, (
        f"found {len(hovers)} :hover rules; fewer than {MIN_HOVER_RULES} means the sweep is not "
        f"reading this app's stylesheets, and would pass by looking at nothing")


def test_no_status_color_in_a_hover_rule() -> None:
    bad = [(f, s) for f, s, body in RULES if ":hover" in s and STATUS.search(body)]
    assert not bad, (
        f"status color in a :hover rule: {bad}. The dark status text reads about 3.6:1 on the "
        f"hover plate (#76 A); the transition exemption is the main button's alone (#74 A).")


def test_no_status_color_on_a_hover_plate() -> None:
    bad = [(f, s) for f, s, body in RULES if STATUS.search(body) and PLATE.search(body)]
    assert not bad, (
        f"status color on a hover plate: {bad}. The dark status text reads about 3.6:1 there (#76 A).")


def test_the_sweep_would_see_one() -> None:
    """The guard, pointed at a rule that breaks it, must see it."""
    planted = ast.parse('sheet = f"QLabel:hover {{ color: {theme[\'error_text\']}; '
                        'background-color: {theme[\'panel_hover\']}; }}"')
    m = [r for s in _strings(planted) for r in RULE.finditer(s)]
    assert m and ":hover" in m[0].group("sel") and STATUS.search(m[0].group("body")) \
        and PLATE.search(m[0].group("body")), "the sweep cannot read a planted violation"
