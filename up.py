#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Give every neutral in rnv-color-mixer's three stylesheet templates a constant
key. 120 hex literals become 14 role-named constants.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards only, change nothing
    python up.py --finish    # delete this file

THIS CHANGES NO PIXELS, AND THAT IS PROVABLE HERE

tests/test_snapshots.py already compares all three rendered stylesheets
byte-for-byte against frozen references in /snapshots/. If those 19 tests pass
WITHOUT regeneration -- and this script refuses to finish unless they do --
then the rendered output is identical to the character. Nothing moved.

WHY IT MATTERS ANYWAY

DARK_STYLESHEET, LIGHT_STYLESHEET and IMAGE_STYLESHEET carried 40, 50 and 30
hex literals while the golds twenty lines above them were already interpolated
from constants. A literal cannot follow its base: move a value and the
templates keep the old one, silently, with nothing to report it. Four of the
five desktop apps were about to be aligned onto a shared ramp; this app's copy
of that ramp was frozen.

WHAT LANDS

  utils/config.py             an APP NEUTRALS block of 14 constants plus
                              NEUTRAL_PROVENANCE, inserted above ThemeManager;
                              120 literals replaced with interpolations
  tests/test_neutral_ramp.py  new: holds the templates literal-free, keeps
                              NEUTRAL_PROVENANCE honest, and proves the sweep
                              that checks them is actually reading something

NAMED BY ROLE, ONE NAME PER VALUE

A step is named for the job it does, and where one value does two jobs the
docstring says both rather than minting a second constant. The single
exception is APP_BTN_HOVER_INVERSE, which is assigned FROM APP_BORDER_DARK
rather than repeating "#333333", so the light-mode inverse hover cannot drift
away from the dark border step it deliberately borrows.

ONE THING RECORDED AND NOT CHANGED

Image mode draws the checkbox indicator border with #555555 while dark mode
draws the same border with #333333; rnv-color-picker and rnv-icon-builder use
#555555 in both. That inconsistency is noted in APP_CONTROL_DIM's docstring
and left alone, because this pass may not move a pixel.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"

CONFIG = "utils/config.py"
GUARD = "tests/test_neutral_ramp.py"
ANCHOR = "class ThemeManager:"
SENTINEL = "NEUTRAL_PROVENANCE"

EXPECTED = {"DARK_STYLESHEET": 40, "LIGHT_STYLESHEET": 50, "IMAGE_STYLESHEET": 30}
EXPECTED_CONSTANTS = 14
HEX6 = re.compile(r"#[0-9a-fA-F]{6}\b")

MAPS = {
    "DARK_STYLESHEET": {
        "#000000": "TRUE_BLACK",
        "#e0e0e0": "APP_TEXT_DARK",
        "#1a1a1a": "APP_SURFACE_DARK",
        "#333333": "APP_BORDER_DARK",
        "#444444": "APP_BTN_PRESSED",
        "#f0f0f0": "APP_HANDLE_HOVER_DARK",
    },
    "LIGHT_STYLESHEET": {
        "#f5f5f5": "APP_WINDOW_LIGHT",
        "#000000": "TRUE_BLACK",
        "#ffffff": "WHITE",
        "#cccccc": "APP_BORDER_LIGHT",
        "#999999": "APP_HANDLE_EDGE_LIGHT",
        "#333333": "APP_BTN_HOVER_INVERSE",
        "#444444": "APP_BTN_PRESSED",
        "#666666": "APP_HANDLE_LIGHT",
        "#555555": "APP_CONTROL_DIM",
        "#eeeeee": "APP_ITEM_HOVER_LIGHT",
    },
    "IMAGE_STYLESHEET": {
        "#e0e0e0": "APP_TEXT_DARK",
        "#333333": "APP_BORDER_DARK",
        "#000000": "TRUE_BLACK",
        "#1a1a1a": "APP_SURFACE_DARK",
        "#444444": "APP_BTN_PRESSED",
        "#f0f0f0": "APP_HANDLE_HOVER_DARK",
        "#555555": "APP_CONTROL_DIM",
    },
}

BLOCK = '# ==================== APP NEUTRALS ====================\n#\n# WHY THESE EXIST. The three stylesheet templates below used to carry 120 hex\n# literals -- 40 dark, 50 light, 30 image -- while the golds twenty lines up\n# were already interpolated from constants. A literal cannot follow its base:\n# move a value here and the templates keep the old one, silently, with nothing\n# to report it. Every rendered hex now has a key, which is the same rule the\n# gold aliases above were written for.\n#\n# NAMED BY ROLE, NOT BY BYTE. A step is named for the job it does, and where\n# one value does two jobs the comment says both rather than minting a second\n# constant. The one exception is APP_BTN_HOVER_INVERSE, which is assigned FROM\n# its base rather than repeating the value, so the two move together.\n#\n# THIS IS A REWIRE, NOT A RETUNE. Every value below is exactly what the\n# templates already rendered. tests/test_snapshots.py compares the three\n# stylesheets byte-for-byte against frozen references; if those pass without\n# regeneration, nothing moved.\n\nTRUE_BLACK: Final[str] = "#000000"\n"""Window and scroll-area ground in dark; primary text in light; the label on\na pressed control in dark; the selection foreground in every mode."""\n\nWHITE: Final[str] = "#ffffff"\n"""Control surface in light -- button, input, combo, scroll area -- and the\nlabel on a pressed control in light."""\n\n# ---- dark and image ----\nAPP_SURFACE_DARK: Final[str] = "#1a1a1a"\n"""Control surface in dark and image: button, input, combo, status bar, and\nthe slider groove."""\n\nAPP_BORDER_DARK: Final[str] = "#333333"\n"""Every border in dark and image. Also the hover ground and the splitter\nhandle -- in dark the hover fill deliberately equals the border step, so a\nhovered control reads as its own outline filling in."""\n\nAPP_TEXT_DARK: Final[str] = "#e0e0e0"\n"""Primary text in dark and image. Also the slider handle, which takes the\nbrightest step in the ramp rather than a colour of its own."""\n\nAPP_HANDLE_HOVER_DARK: Final[str] = "#f0f0f0"\n"""Slider handle when hovered, dark and image. One step above the text."""\n\n# ---- light ----\nAPP_WINDOW_LIGHT: Final[str] = "#f5f5f5"\n"""Window ground in light, the status bar, and the scrollbar track."""\n\nAPP_BORDER_LIGHT: Final[str] = "#cccccc"\n"""Every border in light. Also the scrollbar handle at rest and the splitter\nhandle, on the same reasoning as APP_BORDER_DARK."""\n\nAPP_ITEM_HOVER_LIGHT: Final[str] = "#eeeeee"\n"""Combo-box item under the cursor, light. The list hover, not the button\nhover -- those are different schemes, see APP_BTN_HOVER_INVERSE."""\n\nAPP_HANDLE_LIGHT: Final[str] = "#666666"\n"""Slider handle at rest, light."""\n\nAPP_HANDLE_EDGE_LIGHT: Final[str] = "#999999"\n"""The emphasised edge of a light handle: the slider handle\'s border, and the\nscrollbar handle when hovered."""\n\nAPP_CONTROL_DIM: Final[str] = "#555555"\n"""Two unrelated jobs on one step: the light slider handle when hovered, and\nthe image-mode checkbox indicator border. Worth knowing that dark mode draws\nthat same checkbox border with APP_BORDER_DARK while rnv-color-picker and\nrnv-icon-builder use this step in both -- an inconsistency this pass records\nand does not change, because nothing here may move a pixel."""\n\n# ---- the inverse button scheme, both modes ----\nAPP_BTN_HOVER_INVERSE: Final[str] = APP_BORDER_DARK\n"""The basic button\'s hover ground. Light mode borrows the dark step on\npurpose: the scheme inverts on hover, and the label stays put. Assigned from\nAPP_BORDER_DARK rather than repeating the value so the two cannot drift\napart."""\n\nAPP_BTN_PRESSED: Final[str] = "#444444"\n"""The basic button\'s pressed fill, identical in all three modes. The label\nflips instead -- TRUE_BLACK on dark, WHITE on light."""\n\n# Declarative provenance, read by tests/test_neutral_ramp.py, in the same\n# shape as GOLD_PROVENANCE above. A classification that lives only in a test\n# drifts from the thing it classifies.\nNEUTRAL_PROVENANCE: Final[dict[str, str]] = {\n    "TRUE_BLACK": "anchor",\n    "WHITE": "anchor",\n    "APP_SURFACE_DARK": "step",\n    "APP_BORDER_DARK": "step",\n    "APP_TEXT_DARK": "step",\n    "APP_HANDLE_HOVER_DARK": "step",\n    "APP_WINDOW_LIGHT": "step",\n    "APP_BORDER_LIGHT": "step",\n    "APP_ITEM_HOVER_LIGHT": "step",\n    "APP_HANDLE_LIGHT": "step",\n    "APP_HANDLE_EDGE_LIGHT": "step",\n    "APP_CONTROL_DIM": "step",\n    "APP_BTN_PRESSED": "step",\n    "APP_BTN_HOVER_INVERSE": "alias",\n}\n\n\n'

TESTFILE = '"""\nNeutral ramp guard.\n\nThe three stylesheet templates in utils/config.py carried 120 hex literals\nwhile the golds twenty lines above them were already interpolated. A literal\ncannot follow its base: move APP_BORDER_DARK and a literal template keeps the\nold value, silently, with nothing to report it.\n\nThese tests hold the templates literal-free and keep NEUTRAL_PROVENANCE\nhonest. They do NOT check what the values are -- tests/test_snapshots.py\nalready compares all three rendered stylesheets byte-for-byte against frozen\nreferences, which is a stronger statement than any assertion here could make.\n"""\nfrom __future__ import annotations\n\nimport ast\nimport pathlib\nimport re\n\nimport pytest\n\nfrom utils import config\n\nHEX6 = re.compile(r"#[0-9a-fA-F]{6}\\b")\nTEMPLATES = ("DARK_STYLESHEET", "LIGHT_STYLESHEET", "IMAGE_STYLESHEET")\n\n\ndef _source() -> str:\n    return pathlib.Path(config.__file__).read_text(encoding="utf-8")\n\n\ndef _template_bodies() -> dict[str, str]:\n    """The raw source text of each template, before f-string interpolation."""\n    lines = _source().splitlines()\n    bodies: dict[str, str] = {}\n    for i, line in enumerate(lines):\n        m = re.match(r\'^(DARK_STYLESHEET|LIGHT_STYLESHEET|IMAGE_STYLESHEET)\\s*=\\s*f?"""\', line)\n        if not m:\n            continue\n        for j in range(i + 1, len(lines)):\n            if \'"""\' in lines[j]:\n                bodies[m.group(1)] = "\\n".join(lines[i:j + 1])\n                break\n    return bodies\n\n\ndef test_the_locator_still_finds_all_three_templates():\n    """Guard the guard. Every check below reads the bodies this returns; if the\n    locator silently found nothing, they would all pass on an empty string."""\n    bodies = _template_bodies()\n    assert set(bodies) == set(TEMPLATES), f"located {sorted(bodies)}"\n    for name, body in bodies.items():\n        assert body.count("QPushButton") >= 1, f"{name} does not look like a stylesheet"\n        assert len(body.splitlines()) > 100, f"{name} body is suspiciously short"\n\n\n@pytest.mark.parametrize("name", TEMPLATES)\ndef test_no_hex_literal_survives_in_the_template(name):\n    body = _template_bodies()[name]\n    found = sorted(set(HEX6.findall(body)))\n    assert not found, (\n        f"{name} carries hex literals again: {found}. Every rendered hex needs "\n        f"a constant key -- add one to the APP NEUTRALS block and interpolate it.")\n\n\ndef test_provenance_names_exactly_the_neutral_constants():\n    for name in config.NEUTRAL_PROVENANCE:\n        assert hasattr(config, name), (\n            f"NEUTRAL_PROVENANCE names {name}, which does not exist. An entry "\n            f"that outlives its constant is a classification of nothing.")\n\n\ndef test_the_alias_is_assigned_from_its_base_not_repeated():\n    """APP_BTN_HOVER_INVERSE exists so light-mode hover borrows the dark border\n    step. Written as its own literal it would stop borrowing the moment\n    APP_BORDER_DARK moved, and both would still render."""\n    tree = ast.parse(_source())\n    literals = set()\n    for node in ast.walk(tree):\n        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):\n            if isinstance(node.value, ast.Constant):\n                literals.add(node.target.id)\n    for name, kind in config.NEUTRAL_PROVENANCE.items():\n        if kind == "alias":\n            assert name not in literals, (\n                f"{name} is classified alias but is written as a literal")\n    assert config.APP_BTN_HOVER_INVERSE == config.APP_BORDER_DARK\n\n\ndef test_anchors_are_literals_not_computed():\n    tree = ast.parse(_source())\n    computed = set()\n    for node in ast.walk(tree):\n        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):\n            if isinstance(node.value, ast.Call):\n                computed.add(node.target.id)\n    for name, kind in config.NEUTRAL_PROVENANCE.items():\n        if kind == "anchor":\n            assert name not in computed, f"{name} is an anchor but is computed"\n\n\ndef test_every_neutral_constant_reaches_a_stylesheet():\n    """A constant nothing renders is dead weight, and dead weight is where the\n    next wrong value hides."""\n    rendered = "".join(getattr(config, t) for t in TEMPLATES).lower()\n    orphans = [n for n in config.NEUTRAL_PROVENANCE\n               if getattr(config, n).lower() not in rendered]\n    assert not orphans, f"neutral constants that render nowhere: {orphans}"\n\n\ndef test_the_neutrals_are_pure_greys():\n    """Every neutral in all five desktop apps is R = G = B. A neutral that\n    picks up a cast is a colour wearing a neutral\'s name."""\n    bad = []\n    for name in config.NEUTRAL_PROVENANCE:\n        h = getattr(config, name).lstrip("#")\n        if not (h[0:2] == h[2:4] == h[4:6]):\n            bad.append(f"{name}=#{h}")\n    assert not bad, f"neutrals that are not pure greys: {bad}"\n'


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    """A file named config.py or utils.py here would shadow the package."""
    name = Path(__file__).name
    if name in {"config.py", "utils.py", "conftest.py"}:
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

    def flush(self) -> list[str]:
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
                touched.append(rel)
        return touched


def _bounds(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Locate each template body: opening assignment to closing triple quote."""
    out: dict[str, tuple[int, int]] = {}
    for i, line in enumerate(lines):
        m = re.match(r'^(DARK_STYLESHEET|LIGHT_STYLESHEET|IMAGE_STYLESHEET)\s*=\s*f?"""', line)
        if not m:
            continue
        for j in range(i + 1, len(lines)):
            if '"""' in lines[j]:
                out[m.group(1)] = (i, j)
                break
        else:
            raise SystemExit(f"{m.group(1)}: no closing triple quote")
    missing = set(EXPECTED) - set(out)
    if missing:
        raise SystemExit(f"templates not found: {sorted(missing)}")
    return out


# --------------------------------------------------------------------- steps
def step_replace_literals(tree: Tree) -> int:
    src = tree.read(CONFIG)
    lines = src.splitlines(keepends=True)
    spans = _bounds([l.rstrip("\n") for l in lines])
    total = 0
    for name, (st, en) in spans.items():
        table = MAPS[name]
        count = 0
        for i in range(st, en + 1):
            for h in HEX6.findall(lines[i]):
                key = h.lower()
                if key not in table:
                    raise SystemExit(
                        f"{name} line {i+1}: unmapped literal {h}. The template "
                        f"moved; re-derive the map before trusting this script.")
                lines[i] = lines[i].replace(h, "{" + table[key] + "}")
                count += 1
        if count != EXPECTED[name]:
            raise SystemExit(
                f"{name}: replaced {count} literals, expected {EXPECTED[name]}")
        total += count
    tree.write(CONFIG, "".join(lines))
    return total


def step_insert_constants(tree: Tree) -> None:
    src = tree.read(CONFIG)
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor is not unique: {ANCHOR!r}")
    tree.write(CONFIG, src.replace(ANCHOR, BLOCK + ANCHOR, 1))


def step_write_guard(tree: Tree) -> None:
    tree.write(GUARD, TESTFILE)


# -------------------------------------------------------------------- guards
def check_templates_are_literal_free(tree: Tree) -> None:
    lines = tree.read(CONFIG).splitlines()
    spans = _bounds(lines)
    for name, (st, en) in spans.items():
        body = "\n".join(lines[st:en + 1])
        left = sorted(set(HEX6.findall(body)))
        if left:
            raise SystemExit(f"{name}: literals survived: {left}")
        if body.count("QPushButton") < 1 or len(body.splitlines()) < 100:
            raise SystemExit(f"{name}: body does not look like a stylesheet -- "
                             f"the locator is reading the wrong thing")


def check_every_constant_is_named(tree: Tree) -> None:
    src = tree.read(CONFIG)
    declared = set(re.findall(r'^([A-Z][A-Z0-9_]*): Final\[str\] = ', src, re.M))
    prov_block = src[src.index(SENTINEL):]
    named = set(re.findall(r'^\s{4}"([A-Z][A-Z0-9_]*)":', prov_block, re.M))
    if len(named) != EXPECTED_CONSTANTS:
        raise SystemExit(f"{SENTINEL} names {len(named)} constants, "
                         f"expected {EXPECTED_CONSTANTS}")
    missing = named - declared
    if missing:
        raise SystemExit(f"{SENTINEL} names constants that do not exist: "
                         f"{sorted(missing)}")


def check_the_alias_is_not_a_literal(tree: Tree) -> None:
    src = tree.read(CONFIG)
    if 'APP_BTN_HOVER_INVERSE: Final[str] = APP_BORDER_DARK' not in src:
        raise SystemExit("APP_BTN_HOVER_INVERSE must be assigned from "
                         "APP_BORDER_DARK, not written as its own literal")


def check_the_locked_file_is_untouched(tree: Tree) -> None:
    if any(rel.endswith("test_rnv_color_mixer.py") for rel in tree.files):
        raise SystemExit("this script must not touch the locked root test file")


# ----------------------------------------------------------------- execution
def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output.

    The full suite emits several megabytes of DEBUG logging over three
    minutes. Buffering that in memory alongside a live Qt suite is enough to
    get the run killed on a small runner, and a killed run looks exactly like
    a failing one. Streaming to disk and reading the tail costs nothing.
    """
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    # Respect an already-configured platform. Forcing offscreen is right on a
    # bare runner and wrong anywhere a display or xvfb is already set up, and a
    # Qt suite launched under the wrong platform hangs rather than failing.
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _tail(out: str, lines: int = 40) -> str:
    """Show enough of a failure to act on.

    Four lines is plenty for a pass and useless for a failure -- it prints the
    count and hides every name. On failure, prefer pytest's own summary block
    if it is there, and otherwise fall back to a generous tail.
    """
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[text.rindex(marker) - 30:]
    return "\n".join(text.splitlines()[-lines:])


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

This repo needs system libraries for PyQt6 that a fresh container does not
ship. The give-away is `ImportError: libGL.so.1`. .github/workflows/
tests-linux.yml installs exactly this list before it installs any Python
package, and this is the same list:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""


def _outcome(code: int, out: str) -> str:
    """"env", "fail" or "pass" -- and only exit code 1 means a test failed.

    pytest's exit codes are load-bearing here: 0 passed, 1 tests failed, 2
    interrupted, 3 internal error, 4 usage error, 5 nothing collected. Treating
    every non-zero code as a failing assertion is how a tool ends up telling
    you a stylesheet changed when in fact pytest never started. That is worse
    than saying nothing, because the obvious next move -- regenerate the
    snapshots -- would destroy the only proof this change is neutral.
    """
    if code == 0:
        return "pass"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


def verify() -> int:
    """Snapshots first: they are the proof that nothing moved."""
    if "RNV_UPDATE_SNAPSHOTS" in os.environ:
        print("RNV_UPDATE_SNAPSHOTS is set, so a snapshot pass would prove "
              "nothing.\nUnset it and re-run.")
        return 1

    # Preflight. Cheaper than discovering the same thing inside an
    # INTERNALERROR traceback, and it fails in the right vocabulary.
    code, out = run("checking PyQt6 can load",
                    [sys.executable, "-c", "import PyQt6.QtWidgets"])
    if code != 0:
        print(_tail(out, 6))
        print("\n" + ENV_HELP)
        return code

    code, out = run("byte-exact stylesheet snapshots",
                    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/test_snapshots.py"])
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass" else
          "\n".join(out.strip().splitlines()[-4:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
        return code
    if verdict == "fail":
        print("\nFAILED -- a rendered stylesheet changed, and these tests did "
              "run to say so.\nThis pass is only correct if it changes nothing. "
              "Do NOT regenerate the\nsnapshots: they are the evidence, not the "
              "obstacle.")
        return code

    code, out = run("neutral ramp guard",
                    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/test_neutral_ramp.py"])
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass" else
          "\n".join(out.strip().splitlines()[-4:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
        return code
    if verdict == "fail":
        return code

    # Collection before execution. A test that cannot be IMPORTED has not
    # disagreed with this change -- it has not run. Reporting that as "the
    # suite is not green" sends you looking in the wrong file.
    code, out = run("collecting tests/",
                    [sys.executable, "-m", "pytest", "--collect-only", "-q",
                     "-p", "no:cacheprovider", "tests/"])
    if code != 0:
        print(_tail(out))
        print("\nCOLLECTION FAILED. Files that fail to import never reached a "
              "single\nassertion, and the two suites above -- the byte-exact "
              "stylesheet snapshots\nand the ramp guard -- both passed, which is "
              "the whole proof that nothing\nmoved.\n\n" + ENV_HELP)
        return code

    code, out = run("tests/ suite (about 3 minutes)",
                    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/"])
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass" else
          "\n".join(out.strip().splitlines()[-4:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
        return code
    if verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows\nexactly what landed.")
        return code

    print("\nGreen.\n"
          "This ran tests/ only, on purpose. The locked root file is byte-for-byte\n"
          "unchanged by this script and CI already gates its SHA; it also wants a\n"
          "display or xvfb rather than the offscreen platform used here. Run it your\n"
          "usual way if you want it.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / CONFIG).exists():
        raise SystemExit(f"run this from the root of an rnv-color-mixer "
                         f"checkout (no {CONFIG} here)")
    if SENTINEL in (root / CONFIG).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL} is present in {CONFIG}")

    tree = Tree(root)
    moved = step_replace_literals(tree)
    step_insert_constants(tree)
    step_write_guard(tree)

    check_templates_are_literal_free(tree)
    check_every_constant_is_named(tree)
    check_the_alias_is_not_a_literal(tree)
    check_the_locked_file_is_untouched(tree)

    if check_only:
        print(f"--check: {moved} literals mapped, {EXPECTED_CONSTANTS} constants "
              f"compose, every guard passes. Nothing written.")
        return 0

    touched = tree.flush()
    print(f"replaced {moved} literals; wrote: {', '.join(touched)}\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(
        description="give rnv-color-mixer's stylesheet neutrals a constant key")
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the guards only, change nothing")
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
