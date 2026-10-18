"""The mixer, in American spelling: color, gray, behavior, center

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (aebfb2e).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-10-18: #59 A, "colour" becomes "color" everywhere: code, comments,
file names, map keys, markers, test names, the root suite and documents; #60 A,
and the other British spellings with it, "grey" (GREY_44 is GRAY_44),
"behaviour" and "centre"; #62 A, and the rest the census found: -ise is -ize,
licence, programme, labelled, dialled, honour, judgement, neighbour, maths.
"cancelled" stays: it is American too, and it names signals. In one round, one
file per app. A dictionary census of the result finds no British-only word.

NO GUARD IN THE APP. The rule lives in the brand, so that everything made from
scratch starts on it: a note goes to the brand chat for rnv-brand, and the
practice doc carries it (Chris, 18 October).

THE RULES, inside words and names, keeping case (COLOUR_FILE is COLOR_FILE):
  colour     -> color
  grey       -> gray
  behaviour  -> behavior
  centre(s?)(?![A-Za-z]) -> center\1
  centr(ed|ing) -> center\1
  centre(?=line|piece|point) -> center
  (normal|recogn|optim|parametr|parameter|serial|token|maxim|minim|neutral|general|organ|real|visual|util|summar|custom|initial|synchron|capital|categor|character|priorit|standard|final|local|sanit|random|stabil|memor|author|apolog|critic|special|material|raster|harmon|emphas|quant|linear|central|rational)is(e|ed|es|ing|er|ers|ation|ations|able|ably|ability) -> \1iz\2
  licenc(e|es|ed|ing) -> licens\1
  (?<![A-Za-z])programme(s?)(?![A-Za-z]) -> program\1
  (?<![A-Za-z])maths(?![A-Za-z]) -> math
  (label|travel|model|level|signal|dial|equal|fuel|channel|tunnel|total|spiral|pedal|marvel|rival|quarrel|counsel|libel|shovel|swivel|unravel|bevel|enamel|jewel|panel|pencil|stencil|duel|barrel|grovel|revel|towel|funnel)l(ed|ing|er|ers) -> \1\2
  (hon|neighb|fav|flav|hum|lab|rum|vap|harb|arm|endeav|sav|od|splend|val|clam|parl|tum|savi)our -> \1or
  dgement    -> dgment
  (off|def|pret)ence -> \1ense
  (met|lit|fib|theat|calib|spect|lust)re(s?)(?![A-Za-z]) -> \1er\2
  practis(e|ed|es|ing) -> practic\1
  sceptic    -> skeptic
  aluminium  -> aluminum
  artefact   -> artifact
  and a note beside a tree diagram keeps its column when a name before it gets shorter.

LEFT AS THEY ARE:
  CSS's own color keywords. CSS defines grey, lightgrey and the rest beside
  gray; a string that holds nothing but CSS keywords, or a regex for them, is
  CSS, and what the user can type (a search for "grey") keeps working.
  LICENSE files, which are legal text.
  Every one this round leaves, by file and count. A plain scan of the whole
  checkout, with no exception applied, must find exactly these and no more:
  tests/test_contrast_pairs.py (1): NAMED: CSS's color keywords, and the
      values they stand for.
  tests/test_hint_text.py (1): a regex for CSS's gray in either spelling,
      which code must not paint with.
  tests/test_mode_switch_restyle.py (1): a check that a stylesheet names
      neither of CSS's grays.
  tests/test_named_and_used.py (7): CSS_NAMES: CSS's own color keywords, one
      of which a color written by name must be.

WHAT LANDS.
  66 files, the same text in American spelling, 3 of them renamed:
    tests/colour_values.py -> tests/color_values.py
    tests/test_colour_values.py -> tests/test_color_values.py
    tests/test_colours_in_sync.py -> tests/test_colors_in_sync.py
  .github/workflows/tests-linux.yml: the root suite's digest, as this round leaves it
  .github/workflows/tests-windows.yml: the root suite's digest, as this round leaves it
NO VALUE MOVES. Every value utils/config.py defines is what it was, under its new name.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'RNV-COLOR-SYNC'   # written only by this round: the marker was spelled the other way
SENTINEL_FILE = 'tools/sync_colors.py'
GUARD = 'tests/test_colors_in_sync.py'
GUARD_FILES = ['tests/test_color_values.py', 'tests/test_colors_in_sync.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The mixer, in American spelling"

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = '9a9379bc7f3b6dd2e0970a44d3c2633c9e34d4f97f988283be8222d41525026e'\n"
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

#: The workflows SUITES mirrors, by content hash, as this round leaves them.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '975398ddbcadba6efc11ab6a1b81feb2081e799070ffc5675f110821c145cc65', '.github/workflows/tests-windows.yml': 'defcd6c4e78688941486dd9d4e4b593adf8693ad6688dc846fde49ad5c2feb15'}

SHADOWS = ['conftest.py', 'run_tests.py', 'sync_colors.py', 'test_color_values.py', 'test_colors_in_sync.py', 'test_rnv_color_mixer.py']

LEFT_ALONE = ["every value the application draws: the same, under its American name.",
              "CSS's own color keywords, in data: a table of CSS names, a regex for them, a search the user types.",
              "LICENSE files, which are legal text.",
              "rnv-brand, which the brand chat keeps: a note goes to it."]

# ======================================================================== the transform

import ast
import io
import re
import tokenize

_L = "(?<![A-Za-z])"   # no letter before
_R = "(?![A-Za-z])"    # no letter after

#: (British pattern, American replacement), each tried case-insensitively; the
#: replacement takes the case of the letters it replaces. Patterns match inside
#: names, so COLOUR_FILE and _normalise are reached.
BASE_RULES: list[tuple[str, str]] = [
    ("colour", "color"),                       # colours, coloured, recolour, COLOUR_FILE
    ("grey", "gray"),                          # greys, greyscale, GREY_44
    ("behaviour", "behavior"),                 # behaviours, behavioural
    ("centre(s?)" + _R, r"center\1"),          # centre, centres -> center, centers
    ("centr(ed|ing)", r"center\1"),            # centred, centring -> centered, centering
    ("centre(?=line|piece|point)", "center"),  # centreline
]

#: #62 A: the further British spellings, the -ise family by its stems, so that
#: realistic, organism, criticism and optimism are not touched.
_ISE_STEMS = ("normal recogn optim parametr parameter serial token maxim minim neutral general organ real "
              "visual util summar custom initial synchron capital categor character priorit standard final "
              "local sanit random stabil memor author apolog critic special material raster harmon emphas "
              "quant linear central rational").split()
#: A final l doubled before -ed, -ing, -er: American keeps it single. Not
#: "cancelled", which is American too (#62 A).
_LL_STEMS = ("label travel model level signal dial equal fuel channel tunnel total spiral pedal marvel "
             "rival quarrel counsel libel shovel swivel unravel bevel enamel jewel panel pencil stencil "
             "duel barrel grovel revel towel funnel").split()
EXTRA_RULES: list[tuple[str, str]] = [
    ("(" + "|".join(_ISE_STEMS) + ")is(e|ed|es|ing|er|ers|ation|ations|able|ably|ability)",
     r"\1iz\2"),
    ("licenc(e|es|ed|ing)", r"licens\1"),
    (_L + "programme(s?)" + _R, r"program\1"),
    (_L + "maths" + _R, "math"),
    ("(" + "|".join(_LL_STEMS) + ")l(ed|ing|er|ers)", r"\1\2"),
    ("(hon|neighb|fav|flav|hum|lab|rum|vap|harb|arm|endeav|sav|od|splend|val|clam|parl|tum|savi)our",
     r"\1or"),
    ("dgement", "dgment"),                     # judgement, acknowledgement
    ("(off|def|pret)ence", r"\1ense"),
    ("(met|lit|fib|theat|calib|spect|lust)re(s?)" + _R, r"\1er\2"),
    ("practis(e|ed|es|ing)", r"practic\1"),
    ("sceptic", "skeptic"),
    ("aluminium", "aluminum"),
    ("artefact", "artifact"),
]

#: CSS color keywords spelled with grey; a string of only these is CSS, kept.
CSS_GREYS = frozenset({"grey", "lightgrey", "darkgrey", "dimgrey", "slategrey",
                       "darkslategrey", "lightslategrey"})
#: Every CSS color keyword (CSS Color Module Level 4), and words a regex or a
#: CSS declaration about them carries.
CSS_WORDS = frozenset("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue
darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink
deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold
goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush
lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime
limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise
palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue
saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow
springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
yellowgreen color s b""".split())

DELIVERY_MARKER = "RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP"


def rules() -> list[tuple[str, str]]:
    return BASE_RULES + EXTRA_RULES


_COMPILED: list[tuple[re.Pattern, str]] = []


def _compiled() -> list[tuple[re.Pattern, str]]:
    if len(_COMPILED) != len(rules()):
        _COMPILED[:] = [(re.compile(p, re.I), r) for p, r in rules()]
    return _COMPILED


def _cased(found: str, american: str) -> str:
    """american, in the case found was written in."""
    letters = [c for c in found if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return american.upper()
    if found[:1].isupper():
        return american[:1].upper() + american[1:]
    return american


def fix(text: str) -> str:
    """Every British spelling in text, in American spelling, keeping its case."""
    for pattern, repl in _compiled():
        text = pattern.sub(lambda m: _cased(m.group(0), m.expand(repl).lower()), text)
    return text


def is_css_data(value: str) -> bool:
    """A string of nothing but CSS color keywords and regex or CSS syntax."""
    words = re.findall(r"[A-Za-z]+", value)
    return bool(words) and any(w in CSS_GREYS for w in words) and all(w in CSS_WORDS for w in words)


def _docstring_lines(src: str) -> set[int]:
    """The line numbers that hold a docstring, or an attribute docstring."""
    lines: set[int] = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for i, item in enumerate(body):
            if isinstance(item, ast.Expr) and isinstance(getattr(item, "value", None), ast.Constant) \
                    and isinstance(item.value.value, str):
                if i == 0 and isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) \
                        or i > 0 and isinstance(body[i - 1], (ast.Assign, ast.AnnAssign)):
                    lines.update(range(item.lineno, item.end_lineno + 1))
    return lines


def _python_spans(src: str) -> list[tuple[int, int]]:
    """(start, end) offsets of the string literals that are CSS data, to keep."""
    keep = []
    docs = _docstring_lines(src)
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, SyntaxError):
        return keep
    for tok in tokens:
        if tok.type != tokenize.STRING or tok.start[0] in docs:
            continue
        try:
            value = ast.literal_eval(tok.string)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, str) and is_css_data(value):
            keep.append((starts[tok.start[0] - 1] + tok.start[1], starts[tok.end[0] - 1] + tok.end[1]))
    return keep


def skipped(rel: str, text: str | None = None) -> bool:
    """LICENSE files, and a delivery script at the root (up.py) that carries the
    marker. A test that only mentions the marker, to skip such a script, is
    English like any other file."""
    name = rel.rsplit("/", 1)[-1]
    if name.upper().startswith("LICENSE") or name.upper().startswith("LICENCE"):
        return True
    return "/" not in rel and re.fullmatch(r"up(_\w+)?\.py", name) is not None \
        and text is not None and DELIVERY_MARKER in text


#: A line of a tree diagram, and the gap before the note written beside it.
_TREE_LINE = re.compile("[├└]──")   # a branch drawn with box characters
_NOTE_GAP = re.compile("(?<=\\S)( {2,})(?=[#←])")  # two spaces or more, then '#' or a left arrow


def _keep_column(old: str, new: str) -> str:
    """A note beside a tree diagram keeps its column when a name before it gets
    shorter: colour_values.py is color_values.py, and the arrow after it stays
    where the arrows of the lines around it are."""
    if old == new or not _TREE_LINE.search(old):
        return new
    o, n = _NOTE_GAP.search(old), _NOTE_GAP.search(new)
    if not o or not n or o.end() == n.end():
        return new
    gap = max(2, len(n.group(1)) + o.end() - n.end())
    return new[:n.start()] + " " * gap + new[n.end():]


def _columns(old: str, new: str) -> str:
    if old == new or "──" not in old:
        return new
    old_lines, new_lines = old.split("\n"), new.split("\n")
    if len(old_lines) != len(new_lines):
        return new
    return "\n".join(_keep_column(o, n) for o, n in zip(old_lines, new_lines))


def transform_text(text: str, rel: str) -> str:
    if skipped(rel, text):
        return text
    if not rel.endswith(".py"):
        return _columns(text, fix(text))
    out, at = [], 0
    for start, end in _python_spans(text):
        out.append(fix(text[at:start]))
        out.append(text[start:end])
        at = end
    out.append(fix(text[at:]))
    return _columns(text, "".join(out))


def transform_path(rel: str) -> str:
    return fix(rel)


def british(text: str, rel: str) -> list[tuple[int, str]]:
    """Every British spelling left in text: (line, the word it is in)."""
    if skipped(rel, text):
        return []
    keep = _python_spans(text) if rel.endswith(".py") else []
    found = []
    for pattern, _ in _compiled():
        for m in pattern.finditer(text):
            if any(s <= m.start() < e for s, e in keep):
                continue
            lo, hi = m.start(), m.end()
            while lo > 0 and (text[lo - 1].isalnum() or text[lo - 1] == "_"):
                lo -= 1
            while hi < len(text) and (text[hi].isalnum() or text[hi] == "_"):
                hi += 1
            found.append((text.count("\n", 0, m.start()) + 1, text[lo:hi]))
    return sorted(found)

# ======================================================================== this round

#: Hand edits before the transform, where a renamed word would meet a name already there.
PRE = {}

#: sha256 of each file the round reaches, as the head holds it (under its old name if renamed)
BASE_SHAS = {'.github/workflows/brand-sync.yml': '25f7e55805623ce1267dd131c012d6f7eb2eddee341415d28a9ccb539ca6cde0', '.github/workflows/tests-linux.yml': 'f8f9b2cba1f6ecb79c7bb1c3747696b507d838ed60f8f3d1f33190f58154e5c2', '.github/workflows/tests-windows.yml': '17e7cdc97050e3deb9fac64b9d736296bf7362a53ef9cd4f95283ecf0c693412', 'COLORS.md': '2c7297874d4ee9d7c51c4791101dc102a97ca4d377d67996c65f257b33e82141', 'KNOWN_ISSUES.md': '2bb53979c801d073b658934886970c2629acee5cefe94b45676c2fdaa4a38a2c', 'README.md': 'd2e1a7d0abb11009e5bab801f18d0ea1a76045ff52e35054a6bb5a23402b289e', 'RNV_Color_Mixer.py': 'f08d2e7f08364102773790ff1d757cfb1f47d9b789a87524cc7080ad62f4cf16', 'brand_map.json': '27723556ee8abe2a433ceccc50179bf3048814075a2049dc905899c0184f4409', 'core/color_history.py': 'c6e186efe7779968009b3e59013b0d82ed9d3276dbfedb6c5af4ab0dc3f64805', 'core/color_slot.py': '48ceaa633b0931e717b4a10437e04cfbed34dab27ee0efc262a8ad2b84536e7f', 'core/image_handler.py': 'bb7d7f12a08fd20f4191590f7433e96bf3287a052c09bb1b85472d83d7deedab', 'core/package_d_panel.py': 'ab358f03b959f886671367a568687a5fac3f4523da1c7b9c9d8a2bf62a777073', 'core/screen_color_picker.py': 'b3f8fe68196ac7acbc0d3eee2d72c1fc4b28f00fb63e921e958ff8be35a51432', 'test_rnv_color_mixer.py': '01083d8d16ccb31f83e55b314ddf9d91885eb6e72eae1e365edbecf1209d3129', 'tests/conftest.py': '46cb00d583286c0c3f03c2c9097cf9d16df9cb20cdb27042c63e038abc5407b4', 'tests/test_accent_naming.py': 'beb6de3f27bd43c37119100718a40559d626e85c78205ac4ff2d52a1c59a072e', 'tests/test_app_integration.py': '173f5f8c0139c6e02646d8e9d2963c12104ad08d14ad419fe9101db1cd1f7dd6', 'tests/test_app_mirror.py': 'c96a80388c21ffb57a4b786a2b0094a51c43577505062ecf02b8945683ae2c52', 'tests/test_brand_mirror.py': '4c1d34a4debf7b3ce17b2891b875914b8441ffdc5bca913ea0e85b38f84ba6eb', 'tests/test_button_key_names.py': '9a9042974d583f83de963675f4cf52f5bb778efd929118f98f691b54faf61075', 'tests/test_canvas_follows_the_mode.py': 'a67aa9544a388dcbbd3ebb9a7164ad06b1fd2b0c75a79ce9ad2bb517baba9e55', 'tests/test_color_fine_tune.py': 'e51673df20c38f909489d94c12baac52d9324599359fc38c420061a1fafb48e5', 'tests/test_color_math_properties.py': '16fd9e611e1212928e67eb271def410c668aa7dcdb8822aa944891fd5b8d8079', 'tests/test_color_slot.py': '9436449f4324862c65090873cd8edbb2d54c2a3ddd40ad696a0e1814815116ea', 'tests/test_color_slot_menu.py': '5956d7551c91505e4ee28f1059d75fb793f94a7432c0a5e1ee44c89cc9d0b561', 'tests/test_contrast_pairs.py': '0fd714363d0c920ad4ba5bb779af1c73ef75e465d4bd99e9039aa84322aa8a53', 'tests/test_dependency_coherence.py': '40b3b9ecd6a7fa8d9db76bb17aa3125b367ca8b234f231dfa848e096cea3a0ad', 'tests/test_dependency_file_placement.py': '32fc156e9437e291dc941fbb52ec661b61ae1c00f900daac618b3cf21085f441', 'tests/test_derived_values.py': '56a68560898d05bc4ef1f3dc058014024b38b97f409909c2e485607d24b35fd8', 'tests/test_dialog_helper.py': '2a627058dbd5195141689084d3660caad107e0d8e181256f229dcb1379672f85', 'tests/test_empty_history_line_draws.py': 'd4efbce638225c17dc9ca94f2c86de793695150609cbfd8f8b5e027f21b4de00', 'tests/test_empty_presets_lines_draw.py': '8590d2c8c4d52d76b1679d1490386b47553e590f569012ee82353e8c42ecdff1', 'tests/test_error_recovery_paths.py': 'c277fb51cb189ff10041038f55120ddf31daddb6050ee77f2b8ac142f80e2f0e', 'tests/test_escape_sequences.py': 'cbe3707ab16aceca276bb86983d5eebd19c127946bbe3ded96844ddad0a871b8', 'tests/test_fleet_floor.py': '4cc6dba16ba1f616ca3e8ceec0f5497e3e01f166410b3c75d9077707967a86b9', 'tests/test_gold_as_text.py': '32bf73f7a6636783c6888e5c1d8e326558974e55a5e3f17a3ee607479eb00f40', 'tests/test_helper_modules.py': '3cdee49a9517279d8c46ff309cf60b9e1a4c7378eeb476c3339ac7a4db7ae2bb', 'tests/test_hint_text.py': '35728adff4c278859ba2a0d25241611323cc9490502b1a13f3b8bd272775e868', 'tests/test_history_writer_ownership.py': 'd076f31627ee89c4f2d2f5c2513be03d5859c114fba7c456145f744e2f1b0816', 'tests/test_image_budget.py': '340002991c919a65bdaab20ec0ecb3ccc01b1b130fd35cdba12434453bba9d94', 'tests/test_image_color_modes.py': 'ce7a2f15fb6e07fc28b7926497b0bfa6aabcd7f87ae7a3e8455eea168c7ebafc', 'tests/test_image_confirm.py': 'd364b81a9bf17ddd3762aceeded9f9e82669afde956346523cbf21ea56939243', 'tests/test_image_handler.py': 'ceb4dcd04ecb7d4b81d9580b1ba84120ab02fc51b53b044efd38f00dede74e6f', 'tests/test_ink_on_the_golds.py': '2884079166e9731b17dd511d95017862892d83fadb6a97532d466b9266600f27', 'tests/test_ladder_and_plate.py': 'f2930e9c96319622b326bdd41c4ddf60cfcc006a9fac0adf347713064c54782f', 'tests/test_mixer_wiring.py': '6e15f9e1a48f7560d3c4b711b8c482a1d0a98a692730599b3fbdd813e67f3c7d', 'tests/test_mode_switch_restyle.py': '58feb62fcb2598df1751cdaa07233be699817a24c6279b39c47a808fb2946162', 'tests/test_named_and_used.py': 'f43a536e2a5b6e7e8262debf2b80e57c87dbf68ac51f85ae114bca669a29795c', 'tests/test_neutral_ramp.py': '5da6dae50d5494e2ad22570c1760f33a93c1178754d09b16789320349443bb95', 'tests/test_palette_format_imports.py': 'af0f04e98cf4762d59ba4ab235d4396d5f9225cbd0ad7a34dc73b50aa39070aa', 'tests/test_palette_import.py': '82316d44526d8c0c0987f3e9261dfbb7a8f89610f008decf2e8e4e04c3eb33bb', 'tests/test_readme_test_counts.py': '835fdf3a2444e095b60a88dc3ccaf46d7cd67b1cee148413b83081a29523c458', 'tests/test_register_wiring.py': 'a3b6d61f85f214187ae6eadd3b22f42d036526d1f094f90a0a8ab8907fdd6eb4', 'tests/test_screen_color_picker.py': 'b04760230bc47f3e79f9b60b6d195823b6cec7b80f4a6f84356b7eb97cce60c4', 'tests/test_snapshots.py': '9d3b12cf08fe16312996bfb4fc5e88a0e0d007e92fdef4e8a6651547434bb0b8', 'tests/test_timer_ownership.py': 'a68681e68971cd38378a85f4f9d58b4632ddcc9b4be5115a54ba2ebffd401bee', 'tests/test_unread_preference_is_gone.py': '7fd33bd5277adce7ad19d3db1c76097e95962dbf8c0bea2932f23cbf3f31bcd1', 'tests/test_utility_modules.py': '9eefb506e5283a79ed5b1f93f1500b9381e3a9e497c017fab8ab513a194858bc', 'tools/sync_colors.py': '80e6d14160f3148bcf512e2df1cf4e7edd69311d888533fd9a50bcdb4116391e', 'ui/about_dialog.py': 'e3180b1822ae95f9f7beabae361fa4e5fb9a00bcdc279daa57a0fd72bc07c815', 'ui/canvas_view.py': '6432e59499fb1c5c83453de248c99085445113995558848250ef2161c4213f4f', 'utils/config.py': '18ae7b0e7a4bc985b90abebe04c3e756a6e2a1412b9c8f7c01e302372d8e2525', 'utils/pil_compat.py': '2f54221b7f62f4bd05f78c6a3b18baf2ad91a9efb654544674e2d16b3131425c', 'tests/colour_values.py': 'faa3826ab9ebb36150183d46c5572fd1628665e7b89a6eae0f193bb6a352d369', 'tests/test_colour_values.py': '53ca63f0c39796dbecbc378eac1657ee876209b2dd3d9e2c5aad26dc68116b1b', 'tests/test_colours_in_sync.py': 'f7d986594bdb4fc83ceed7e668ffa156c246f2dd0173a440f3c14cc0cf1e7caf'}

#: (new name, old name)
RENAMES = [('tests/color_values.py', 'tests/colour_values.py'), ('tests/test_color_values.py', 'tests/test_colour_values.py'), ('tests/test_colors_in_sync.py', 'tests/test_colours_in_sync.py')]

NEW_FILES = {}

#: The root suite's digest, where CI holds it: (file, the head's, this round's)
DIGESTS = [('.github/workflows/tests-linux.yml', '01083d8d16ccb31f83e55b314ddf9d91885eb6e72eae1e365edbecf1209d3129', '9a9379bc7f3b6dd2e0970a44d3c2633c9e34d4f97f988283be8222d41525026e'), ('.github/workflows/tests-windows.yml', '01083d8d16ccb31f83e55b314ddf9d91885eb6e72eae1e365edbecf1209d3129', '9a9379bc7f3b6dd2e0970a44d3c2633c9e34d4f97f988283be8222d41525026e')]

#: sha256 of every file as this round writes it
WANT = {'.github/workflows/brand-sync.yml': '137a62d18cfd07d5d46f2ccb74c81178aa73738a8bfb150583ae79e2cbac8e71', '.github/workflows/tests-linux.yml': '975398ddbcadba6efc11ab6a1b81feb2081e799070ffc5675f110821c145cc65', '.github/workflows/tests-windows.yml': 'defcd6c4e78688941486dd9d4e4b593adf8693ad6688dc846fde49ad5c2feb15', 'COLORS.md': '833ef8878085be3b09b2253df69c4ac89987e5243284dbdc0a62a936c7fc3553', 'KNOWN_ISSUES.md': '9461893eb26849c63674550211c57bcb239dd8b077741ab018f96f12ea556c99', 'README.md': 'f3eddfd004515dc78f47184a57b4b6a2c6447eeed76e5dfa2b8c5079f4216be6', 'RNV_Color_Mixer.py': '1883761993c6a5b164bff08bcace0a8b504f1d8ea6cea9352d72548e61f51d31', 'brand_map.json': '4eb0f47fc3fbfc6fbd86a900cd1dc61e746ef0f309d81c58e7d3400d7b4ac1be', 'core/color_history.py': 'b91bf074282f633e4bc1f1b46e743530d120e8cd7fe0f3e063402b0a8ca2177c', 'core/color_slot.py': 'e89eb23da546526985dd41fe111dc95fa2678bd7455bf7332d2f33dbd4d161f1', 'core/image_handler.py': 'ec8ce636109c6236c2e0622ae81155967a52e4c6c37ad410c9f2fee9061958e6', 'core/package_d_panel.py': 'abf73d2962cba727517e6e86fd461768b77f6002deecb7bb2139749354402782', 'core/screen_color_picker.py': 'b8a0c177fce2e515d7b8e56aa73cd936e5e6b98cef16fbc71a62ce66887ad3ee', 'test_rnv_color_mixer.py': '9a9379bc7f3b6dd2e0970a44d3c2633c9e34d4f97f988283be8222d41525026e', 'tests/color_values.py': '4a62e105b0e53b8343503c5b8e13cf08c10f27ac57e130f4f786c06fc828c0fa', 'tests/conftest.py': 'ca10a48e1914f55fee902b9839fb72449cc8c065954a9d4f9188740c64486908', 'tests/test_accent_naming.py': '5fcf4aac475499781b57d3e7fcf7a19dbafa880f09365f672723d32aa9b46012', 'tests/test_app_integration.py': 'bb74758f88f132932cdb0cdf97b5ced8a966dfff1517910b659998bcbab9a634', 'tests/test_app_mirror.py': '1e87a344e888624378f966a3d57ccf55b2e46e375de68709c1462d4ccce57c36', 'tests/test_brand_mirror.py': 'edf33e841b16488ee632b46f654752c9962830d566c076e936768a2cf32a68ec', 'tests/test_button_key_names.py': '181c0754016bb9377b82522d9f592100d1c136af053312875e945e125fefc548', 'tests/test_canvas_follows_the_mode.py': '1d98ef17ac054759b55c03819142f881ef302e183e986067193b8ab81bd7894f', 'tests/test_color_fine_tune.py': '23883b0ca46babf82a4c3136e964e51d8c0946adec3ba482e7afb9037a7cd96b', 'tests/test_color_math_properties.py': 'c86048b151fb08d1e45a7591a1052bde63fb705d525a9247b41bfafd80c8e7a1', 'tests/test_color_slot.py': '16653e3e237b076c20c7048efaab4ed68789d6ea1366bf803c9350ff975ac5a2', 'tests/test_color_slot_menu.py': '6e7b33658385b3cce414ccae5cb315e7a4d5679ea4529b733af9cc1de9367776', 'tests/test_color_values.py': 'e523afd0781788a0255f32df2fb0d12b14089160606d46db1735f91790e7a7f7', 'tests/test_colors_in_sync.py': 'da711394c4c0fc08865d800155020ad715fde11d49d2887d7aa4ccbef8f1c4ed', 'tests/test_contrast_pairs.py': 'fe5ea35f7717b77e783649f4599dcede285333358a9815a9248129bfb9d6d0d3', 'tests/test_dependency_coherence.py': '841e21255aee937e747c7a38e7c15b87fbbff73f3c92508a53ceecf26e6b1332', 'tests/test_dependency_file_placement.py': '1f308e54893fee418ae6a534eb3d85c68a0702d94ad046f916434c589b1b0c23', 'tests/test_derived_values.py': 'd86d2de8e09baf2a3afd2a0084c16aba5e963449709c67710bb1d9843fba150f', 'tests/test_dialog_helper.py': '741cab6978d3ce1fb10083069452e86b5a152750b52228ceebcae7d2e866ca7d', 'tests/test_empty_history_line_draws.py': 'aef62a720765abfe7c7bb97d6b5379064d0bf997fa0157359dea369fbfbe168f', 'tests/test_empty_presets_lines_draw.py': '40c6288135130b6656353ac0ff86a25792fd157eaa6db8111d51003b70b7c4da', 'tests/test_error_recovery_paths.py': '9fd4fa86143dcd79ddd003e6590538232918a99a485fa7005cfc38cd6ee68c0c', 'tests/test_escape_sequences.py': 'a8695c3b17aaa079852d8cb5a16045bbc3088fa890dca5803421c9760aab3459', 'tests/test_fleet_floor.py': '99e8a8a1d5214d21b9b269f39ac25f6c2b79f7240f14aefa53966409300901e6', 'tests/test_gold_as_text.py': 'a1d21c69c7285f278efab283813e48adeca14284b573113b365a39516b07e5a2', 'tests/test_helper_modules.py': '5c5704dbe0f0231a15a53c6cb75349c51f7e9912bb7c1184dd84e3cf475b0e3f', 'tests/test_hint_text.py': '93445b672b671a817d8f3d4bf3f0709e0c55ac9595e4b24859983fedd5180cfd', 'tests/test_history_writer_ownership.py': '7b34585bc7e3245e47b35b46c7d27af7828f7fa52b3271fc5ef0349210079866', 'tests/test_image_budget.py': '2c7b876e57bbaa369f686624b6a0e793dfe1bfd00b09c6e57c363a9fc13cba40', 'tests/test_image_color_modes.py': '966eebd9911a3d0d40b89f9754057286a6ce99c5e1ef976fde7d87d3fb8ee388', 'tests/test_image_confirm.py': '7c3a0e925612539d8ae57f3b537d3b83507f5aa8d931bfca80b448b956a1994c', 'tests/test_image_handler.py': 'bad17ff8c635403752f46b8c884d0abfe0411f916e307ac10179cec1c34e20cc', 'tests/test_ink_on_the_golds.py': 'e8cb52ce4a079add9b64ad506328d727443952b607c9555900b87b24c3743812', 'tests/test_ladder_and_plate.py': 'db2bb1c73e3afd78ab340333a07facc09e57e15f9d720c6eb1fb108ff9d846e1', 'tests/test_mixer_wiring.py': 'e1302d5c72d1a205d3b295c4ac9b62984e7895a3259d6ba7b8db7d608caaecd6', 'tests/test_mode_switch_restyle.py': 'a33cfc6b7f6c4e5fda5e1b01956c467f37b8ae49f56a6e0f8559817b2236bf5b', 'tests/test_named_and_used.py': '52ce2f9dc0481263ee0613cf524459fc4c8b533f818b268eb6e2d61228e943da', 'tests/test_neutral_ramp.py': 'd87c757a0ba01bc2c90f11f4a16225663a4ade6dde6decfc0dea6176b93a5e8c', 'tests/test_palette_format_imports.py': 'cad13a4eb3af30dd3b12a031d0006ecb81cdbbd93bf46860941166700df0fae7', 'tests/test_palette_import.py': '41379d966ca3689fbb4fc3eaa7d685d953518812d43d5bb337e42e4ddce1d903', 'tests/test_readme_test_counts.py': 'bd48562c51b731ec3d001e5ad0e1f286672ebe12348d2fadcc66c2c8e1e5d503', 'tests/test_register_wiring.py': 'ebc55ec5a36e0f3dfa5715bbc4ee109dc93e30d689561f28d1ec70df80430932', 'tests/test_screen_color_picker.py': 'e74551a737337c13bb3700e1a499ef485167ec88174063ecc042dedc3614ec76', 'tests/test_snapshots.py': '9c7f600cfd4bab3167813f8aa65e5064c001d1ad49e960feb355d4e7a7c9d60f', 'tests/test_timer_ownership.py': 'da05403754a64754f7adda46ff06b68714c2832e4d27ec544c23351cd8301288', 'tests/test_unread_preference_is_gone.py': '5c8ff5f353dcfa34d65cefb29c4c0d43a89a88a5c6db7f7d2e7291136b59378a', 'tests/test_utility_modules.py': '5b1a5e0ad9ae7f06617983c1f42e205c48f92fd4080c47b89eeeaeb5958d0df6', 'tools/sync_colors.py': 'b9bbd1c2785e5fbc56bd4f0e2b280a902874bd8ac27bdeca5768cf25e2c0818a', 'ui/about_dialog.py': 'b3319bf60acb1cb34b690088ff1ec49179828fac7588dddb9b7378786d33bfc0', 'ui/canvas_view.py': '632d382b34c98452dba6a893de2f78e4d65e23ec3e0d169f88c86913ce70acf9', 'utils/config.py': '1f9a2f68660de9529038f396b9fec759c1e0c12bfd88a7fb02c443df28a6bbd2', 'utils/pil_compat.py': '1164f16f611bd0531b923a2f17e381afb606b236ac24099226761b9ad42fce7c'}

#: Every British spelling the round leaves, {file: count}: CSS's keywords, in data (above).
KEPT = {'tests/test_contrast_pairs.py': 1, 'tests/test_hint_text.py': 1, 'tests/test_mode_switch_restyle.py': 1, 'tests/test_named_and_used.py': 7}

COLOR_FILE = 'utils/config.py'


def edits(tree) -> None:
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. The file moved; re-derive before trusting the script.",
                       EXIT_CANNOT_RUN)
    old_names = {old: new for new, old in RENAMES}
    for rel in BASE_SHAS:
        text = tree.read(rel)
        for a, b in PRE.get(rel, []):
            if text.count(a) != 1:
                raise Stop(f"{rel}: the hand edit's anchor is not there once", EXIT_CANNOT_RUN)
            text = text.replace(a, b)
        new = transform_text(text, rel)
        if rel in old_names:
            tree.delete(rel)
            tree.write(old_names[rel], new)
            tree.form[old_names[rel]] = tree.form[rel]   # a renamed file keeps its BOM and line endings
        else:
            tree.write(rel, new)
    for rel, was, now in DIGESTS:
        tree.sub(rel, was, now)
    for rel, body in NEW_FILES.items():
        if (tree.root / rel).exists():
            raise Stop(f"{rel} already exists here, and this round creates it. Nothing was written.",
                       EXIT_CANNOT_RUN)
        tree.write(rel, body)


#: What the rules must do, written out, so a changed rule is refused by name.
SAMPLES = {"colour": "color", "Colours": "Colors", "COLOUR_FILE": "COLOR_FILE", "grey": "gray", "GREY_44": "GRAY_44",
           "greyscale": "grayscale", "behaviour": "behavior", "centre": "center", "centred": "centered",
           "normalise": "normalize", "optimisation": "optimization", "licence": "license", "programme": "program",
           "labelled": "labeled", "honours": "honors", "judgement": "judgment", "neighbours": "neighbors",
           "maths": "math", "Maths": "Math", "quantisation": "quantization", "linearised": "linearized",
           "centralised": "centralized", "parameterised": "parameterized", "dialled": "dialed",
           "equalled": "equaled", "mathsy": "mathsy",
           "cancelled": "cancelled", "realistic": "realistic", "programmer": "programmer", "organism": "organism",
           "central": "central", "criticism": "criticism", "emphasis": "emphasis"}


#: Where the exceptions end, written out: (text, file, what this round makes of it, what that shows).
NL = chr(10)
_TREE_WAS = "\u2502   \u251c\u2500\u2500 colour_values.py   \u2190 a" + NL
_TREE_IS = "\u2502   \u251c\u2500\u2500 color_values.py    \u2190 a" + NL
_TREE_NEXT = "\u2502   \u251c\u2500\u2500 conftest.py        \u2190 b" + NL
BOUNDARY = [
    ("names = {'grey': 1, 'lightgrey': 2}" + NL, "x.py", "names = {'grey': 1, 'lightgrey': 2}" + NL,
     "CSS's own keywords, in data, are kept"),
    ("PATTERN = r'(gray|grey)'" + NL, "x.py", "PATTERN = r'(gray|grey)'" + NL, "a regex for CSS's keywords is kept"),
    ("x = 'a grey line'" + NL, "x.py", "x = 'a gray line'" + NL, "a sentence in a string is English"),
    ('\"\"\"grey\"\"\"' + NL, "x.py", '\"\"\"gray\"\"\"' + NL, "a docstring is English, whatever its words"),
    ("# grey" + NL, "x.py", "# gray" + NL, "a comment is English"),
    ("grey" + NL, "notes.md", "gray" + NL, "a file that is not Python is English"),
    ("licence, colour" + NL, "LICENSE", "licence, colour" + NL, "legal text is kept"),
    (_TREE_WAS + _TREE_NEXT, "README.md", _TREE_IS + _TREE_NEXT, "a note beside a tree diagram keeps its column"),
]


def _checkout(tree) -> list[str]:
    """Every file git tracks here, as this round leaves them: a renamed one under its new name."""
    try:
        out = subprocess.run(["git", "-C", str(tree.root), "ls-files", "-z"], capture_output=True,
                             check=True).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as e:
        raise Stop(f"git could not list this checkout's files ({e}). This round reads every one of them, "
                   f"to see that nothing British is left. Nothing was written.", EXIT_CANNOT_RUN)
    tracked = {rel for rel in out.split(chr(0)) if rel}
    return sorted((tracked - tree.deleted) | set(tree.files))


def _plain(tree, rel: str) -> int:
    """How many British spellings a file holds, found with no exception applied."""
    if rel in tree.files:
        text = tree.files[rel]
    else:
        path = tree.root / rel
        if not path.is_file():
            return 0
        raw = path.read_bytes()
        if b"\0" in raw:
            return 0
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return 0
    if skipped(rel, text):
        return 0
    return sum(len(pattern.findall(text)) for pattern, _ in _compiled())


def checks(tree) -> None:
    # ---- the rules do what they say, and leave what they say they leave
    wrong = {b: fix(b) for b, a in SAMPLES.items() if fix(b) != a}
    assert not wrong, f"the spelling rules give {wrong}"
    for text, rel, want, shows in BOUNDARY:
        got = transform_text(text, rel)
        assert got == want, f"{shows}, and the round makes {text!r} into {got!r}"
    # ---- no value moves: every value the color file defined is what it was, under its new name
    def values(text):
        root = str(tree.root)
        added = root not in sys.path
        if added:
            sys.path.insert(0, root)
        try:
            ns = {"__file__": str(tree.root / COLOR_FILE), "__name__": COLOR_FILE[:-3].replace("/", ".")}
            exec(compile(text, COLOR_FILE, "exec"), ns)
        finally:
            if added:
                sys.path.remove(root)
        return {k: v for k, v in ns.items() if not k.startswith("__") and not callable(v)
                and type(v).__name__ not in ("TypeAliasType", "module", "Logger")
                and not (isinstance(v, str) and os.sep in v)}
    before, after = values(_original(tree, COLOR_FILE)), values(tree.read(COLOR_FILE))
    assert sorted(fix(k) for k in before) == sorted(after), \
        f"{COLOR_FILE} defines other names: {sorted(set(map(fix, before)) ^ set(after))}"
    moved_values = sorted(k for k in before if fix(repr(before[k])) != repr(after[fix(k)]))
    assert not moved_values, f"a value moved: {moved_values}"
    assert len(before) >= 40, f"only {len(before)} values compared -- the comparison is blind"
    # ---- the map: the same entries, under the new names
    was_map = json.loads(_original(tree, "brand_map.json"))
    now_map = json.loads(tree.read("brand_map.json"))
    assert json.loads(fix(json.dumps(was_map))) == now_map, "brand_map.json holds other entries"
    assert "colors" in now_map and "color_file" in now_map, "the map's keys are not in American spelling"
    # ---- nothing British is left, outside CSS's keywords and LICENSE files
    left = [(rel, b) for rel, t in tree.files.items() for b in british(t, rel)]
    assert not left, f"British spelling left: {left[:20]}"
    # ---- the whole checkout, read plainly: exactly what this round leaves (KEPT), and no more
    found = {rel: n for rel in _checkout(tree) if (n := _plain(tree, rel))}
    differ = {rel: (found.get(rel, 0), KEPT.get(rel, 0)) for rel in sorted(set(found) | set(KEPT))
              if found.get(rel, 0) != KEPT.get(rel, 0)}
    moved = sorted(rel for rel in differ if rel not in tree.files)
    if moved:
        raise Stop(f"British spelling in files this round does not write, other than it was derived with: "
                   f"{ {rel: differ[rel] for rel in moved[:10]} } as (found, expected). The checkout moved; "
                   f"re-derive before trusting the script. Nothing was written.", EXIT_CANNOT_RUN)
    assert not differ, f"British spelling left, as (found, what this round leaves): {differ}"
    # ---- every file this round writes, as it writes it
    assert sorted(tree.files) == sorted(WANT), f"this round writes {sorted(tree.files)}"
    assert sorted(tree.deleted) == sorted(old for _, old in RENAMES), f"this round removes {sorted(tree.deleted)}"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"

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
