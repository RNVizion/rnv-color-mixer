"""Every colour value the tests use is named once.   RNV-COLOUR-SYNC (#53 A)

Installed 2026-10-17, ruled in #52 to #57. The application's own colours and
the brand's are named in the colour file, which brand_map.json names, and a
test reads them from there. Every other colour value a test needs is named in
tests/colour_values.py, once, with why:

  EXAMPLE_   a sample given to a helper or to the colour maths
  DATA_      what a user, a file, the clipboard or the search box supplies
  RETIRED_   a value the application no longer uses, kept so a test can say so
  REGISTER_  a value the brand publishes that this application does not draw;
             REGISTER_REFS says which brand name, and this file holds it there
  INVALID_   a value written wrongly on purpose, for a test that refuses it

WHAT THIS GUARD HOLDS.

1. No test under tests/, and no root suite, writes a colour value anywhere
   but tests/colour_values.py: a string that is only a colour -- a hex code
   of three, six or eight digits, or an rgb() or rgba() value (#54 A).
2. No sentence in a test -- a comment, a docstring, a message -- writes a hex
   code or an rgb() value either. It says the name, and a message prints the
   value through it, in an f-string (#57 A). What a value is, and why it was
   retired, is said once, beside it, in tests/colour_values.py.
3. The readers are looking: they find every value in tests/colour_values.py,
   and a planted sentence.
4. Every name there says what kind it is, says why, and is used by a test.
5. Every REGISTER_ value is the brand's, at the pinned commit.

The same file in all five applications.
"""
from __future__ import annotations

import ast
import importlib.util
import io
import json
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
VALUES_FILE = TESTS / "colour_values.py"
KINDS = ("EXAMPLE_", "DATA_", "RETIRED_", "REGISTER_", "INVALID_")
COLOUR = re.compile(r"^\s*(?:#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})"
                    r"|rgba?\([^()]*\))\s*$")
#: A hex code, or the start of an rgb() value, inside a sentence.
IN_A_SENTENCE = re.compile(
    r"(?<![0-9A-Za-z&/])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9A-Za-z_])"
    r"|\brgba?\(\s*\d")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALUES = _load("colour_values_under_guard", VALUES_FILE)


def colour_strings(source: str) -> list[tuple[int, str]]:
    """(line, value) for every string in the source that is only a colour."""
    found = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type != tokenize.STRING:
            continue
        try:
            value = ast.literal_eval(tok.string)
        except (ValueError, SyntaxError):
            continue
        if isinstance(value, str) and COLOUR.match(value):
            found.append((tok.start[0], value))
    return found


def sentence_colours(source: str) -> list[tuple[int, str]]:
    """(line, text) for every hex code or rgb() value inside a comment, a
    docstring, a message, or any other string that is not only a colour."""
    found = []
    middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.STRING:
            try:
                value = ast.literal_eval(tok.string)
            except (ValueError, SyntaxError):
                value = None
            if isinstance(value, str) and COLOUR.match(value):
                continue
        elif tok.type not in (tokenize.COMMENT, middle):
            continue
        # An escape such as \\n before a hex code would hide it from the
        # look-behind; read it as the space it stands for.
        for match in IN_A_SENTENCE.finditer(re.sub(r"\\[ntr]", " ", tok.string)):
            found.append((tok.start[0], match.group(0)))
    return found


def _test_files() -> list[Path]:
    files = sorted(p for p in TESTS.rglob("*.py")
                   if "__pycache__" not in p.parts and p != VALUES_FILE)
    return files + sorted(ROOT.glob("test_rnv_*.py"))


def _named() -> dict[str, str]:
    """Each name tests/colour_values.py gives a value, with that value."""
    return {k: v for k, v in vars(VALUES).items() if k.isupper() and isinstance(v, str)}


def test_no_colour_value_is_written_outside_colour_values():
    strays = []
    for path in _test_files():
        for line, value in colour_strings(path.read_text(encoding="utf-8-sig")):
            strays.append(f"{path.relative_to(ROOT).as_posix()}:{line} {value!r}")
    assert not strays, (
        "a colour value written in a test. Read it from the colour file if it is the "
        "application's colour, or name it in tests/colour_values.py:\n  " + "\n  ".join(strays))


def test_no_sentence_in_a_test_writes_a_colour():
    found = []
    for path in _test_files():
        for line, text in sentence_colours(path.read_text(encoding="utf-8-sig")):
            found.append(f"{path.relative_to(ROOT).as_posix()}:{line} {text!r}")
    assert not found, (
        "a hex code or an rgb() value written in a comment, a docstring or a "
        "message. Say the name, and print the value through it:\n  " + "\n  ".join(found))


def test_the_sentence_reader_is_looking():
    hexes = [VALUES.EXAMPLE_HAND_EDIT, VALUES.EXAMPLE_MOVED_ACCENT]
    planted = (f"# was {hexes[0]}\n"
               f"z = 'one\\n{hexes[0]}'\n"
               f"x = f'{{a}} on {hexes[1]}'\n"
               f"y = 'rgb({0}, {0}, {0}) is not a name'\n")
    assert [t for _, t in sentence_colours(planted)] == [hexes[0]] + hexes + [f"rgb({0}"], \
        "the sentence reader misses a hex code in a comment or a message -- it is blind"


def test_the_reader_finds_every_value_in_colour_values():
    found = {value for _, value in colour_strings(VALUES_FILE.read_text(encoding="utf-8-sig"))}
    colours = {v for v in _named().values() if COLOUR.match(v)}
    assert colours, "tests/colour_values.py names no colour -- the reader is blind"
    assert colours <= found, f"the reader misses {sorted(colours - found)}"


def test_every_name_says_what_kind_it_is():
    wrong = sorted(n for n in _named() if not n.startswith(KINDS))
    assert not wrong, f"names without one of {KINDS}: {wrong}"


def test_every_name_says_why():
    body = ast.parse(VALUES_FILE.read_text(encoding="utf-8-sig")).body
    silent = []
    for here, after in zip(body, body[1:] + [None]):
        targets = here.targets if isinstance(here, ast.Assign) else \
            [here.target] if isinstance(here, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Name) and target.id in _named():
                said = isinstance(after, ast.Expr) and isinstance(after.value, ast.Constant) \
                    and isinstance(after.value.value, str) and after.value.value.strip()
                if not said:
                    silent.append(target.id)
    assert not silent, f"names with no docstring under them saying why: {silent}"


def test_every_name_is_used_by_a_test():
    text = "\n".join(p.read_text(encoding="utf-8-sig") for p in _test_files())
    unused = sorted(n for n in _named() if not re.search(rf"\b{n}\b", text))
    assert not unused, f"named in tests/colour_values.py and used by no test: {unused}"


def test_every_register_value_is_the_brands():
    refs = getattr(VALUES, "REGISTER_REFS", {})
    names = sorted(n for n in _named() if n.startswith("REGISTER_"))
    assert sorted(refs) == names, "REGISTER_REFS must name the brand's name for each REGISTER_ value"
    if not names:
        return
    sync = _load("sync_colors_for_values", ROOT / "tools" / "sync_colors.py")
    try:
        brand, _ = sync.load_brand(ROOT)
    except sync.SyncError as exc:
        pytest.fail(str(exc))
    wrong = {n: (getattr(VALUES, n), sync.brand_value(brand, refs[n])) for n in names
             if getattr(VALUES, n).lower() != str(sync.brand_value(brand, refs[n])).lower()}
    assert not wrong, f"not the brand's value at the pin (here, brand): {wrong}"
