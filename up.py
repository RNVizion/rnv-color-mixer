#!/usr/bin/env python3
"""rnv-color-mixer -- rename the two accent role keys to match the family.

WHAT THIS CHANGES

  Nothing renders differently. Not one colour value moves. This is a rename
  of two dictionary keys and the local variables that read them, so that
  `accent_text` means the same thing here as it does in rnv-text-transformer
  and rnv-color-palette-manager.

    role                        was            becomes
    -------------------------   ------------   ------------
    the gold, used AS text      accent_text    accent_ink
    the colour drawn ON gold    accent_on      accent_text

  I introduced the mixer's naming without checking the transformer's and gave
  the same identifier the opposite meaning. Internally consistent, guarded,
  nothing rendering wrong -- but it is exactly the failure the brand register
  retired "identifiers are local by design" to prevent, one level down.

THE HAZARD THIS SCRIPT IS BUILT AROUND

  This is a SWAP THROUGH A SHARED NAME. `accent_on` becomes `accent_text`
  while `accent_text` becomes `accent_ink`. Applied as two sequential
  passes in the wrong order, the first pass creates the very token the
  second pass is looking for, and both roles collapse onto one value.
  Every substitution here is therefore ATOMIC: one regex alternation over
  all old names at once, resolved through a dict, so no intermediate state
  exists for the next rule to trip over.

  Two token classes, kept apart because they do not map the same way:

    quoted   'accent_text' / "accent_on"     -> palette KEYS, one global map
    bare      accent_text  /  accent_on      -> LOCAL VARIABLES, per-file map

  In core/color_slot.py the local named `accent_text` already holds the
  text-on-gold value, so after the key rename that line reads
  `accent_text = _ct['accent_text']` and the local keeps its name. That is
  not an oversight; it is the line becoming correct.

  Word boundaries do the rest: `\\baccent_on\\b` cannot match inside
  `accent_on_col`, because `_` is a word character. Those longer names are
  listed explicitly instead of being caught by accident.

THE LOCKED FILE

  test_rnv_color_mixer.py:1934 carries "accent_on" in its required-keys
  list, and the file is SHA-256 gated at 58e6313c... by BOTH
  .github/workflows/tests-linux.yml and tests-windows.yml. One line changes,
  so both pins are recomputed and rewritten from the file this script just
  produced -- never from a value typed in by hand.

USAGE

    python scripts/up.py --check     # dry run, writes nothing
    python scripts/up.py             # apply
    python scripts/up.py --finish    # delete this script

Safe to run twice: a second run detects the work is already done and exits 0.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

# --------------------------------------------------------------------------
# 0. Do not let this file shadow a package the suite imports.
# --------------------------------------------------------------------------

def refuse_to_shadow() -> None:
    """A script in a directory on sys.path shadows any module of that name.

    Learned on rnv-color-mcp, where a delivery script named mcp.py shadowed
    the installed `mcp` package and took the entire suite down with an
    ImportError that named neither file.
    """
    stem = os.path.splitext(os.path.basename(__file__))[0]
    forbidden = {
        "config", "core", "ui", "utils", "tests", "pytest", "test",
        "resources", "snapshots", "colors", "run_tests",
    }
    if stem in forbidden:
        sys.exit(
            f"refusing to run: this script is named {stem}.py, which shadows "
            f"a module the suite imports. Rename it and run again."
        )


# --------------------------------------------------------------------------
# 1. Fingerprint -- prove we are standing on the tree this was written against
# --------------------------------------------------------------------------

FINGERPRINT = (
    # path, must-contain, what it proves
    ("utils/config.py", "'accent_on': '#000000'",
     "the light/image palettes still use the retired key name"),
    ("utils/config.py", "'accent_text': BRAND_DARK_GOLD_DEEP",
     "the dark-gold text role is still under the old name"),
    ("core/color_slot.py", "accent_text_role = _ct['accent_text']",
     "the local that gives away the collision is still present"),
    ("core/package_d_panel.py", "accent_on   = t['accent_on']",
     "the panel still reads the retired key"),
    ("test_rnv_color_mixer.py", '"accent_on"',
     "the locked file still asserts the retired key"),
)

ALREADY_DONE = (
    ("utils/config.py", "'accent_ink'", "the rename has already been applied"),
)


# --------------------------------------------------------------------------
# 2. The maps
# --------------------------------------------------------------------------

# Quoted palette keys. One map, every file. Atomic.
KEY_MAP = {
    "accent_text": "accent_ink",   # the gold used AS text
    "accent_on": "accent_text",    # the colour drawn ON the gold
}
KEY_RE = re.compile(r"(['\"])(" + "|".join(sorted(KEY_MAP, key=len, reverse=True)) + r")\1")

# Bare local variables, per file. Also atomic, and deliberately NOT the same
# map -- see the module docstring on core/color_slot.py.
LOCAL_MAP = {
    "core/color_slot.py": {
        # accent_text already holds the text-on-gold value; it keeps its name
        # and simply becomes correct.
        "accent_text_role": "accent_ink",
    },
    "core/package_d_panel.py": {
        "accent_on": "accent_text",      # swap, same scope, same statement block
        "accent_text": "accent_ink",     # -- which is why this must be one pass
        "accent_on_col": "accent_text_col",
        "accent_text_col": "accent_ink_col",
    },
    "ui/ui_handler.py": {
        "accent_on_text": "accent_text_col",
    },
}


def _local_re(names) -> re.Pattern:
    """Bare identifiers ONLY -- a quoted token must not match.

    This is the sharpest edge in the whole script. After the key pass,
    core/package_d_panel.py legitimately contains `t['accent_text']`: that is
    the NEW key, the one the rename just created. But `accent_text` is also an
    OLD local name in the same file, mapped to `accent_ink`. A plain
    \\b...\\b pattern matches the identifier inside the quotes just as
    happily as the bare one, so the local pass would rewrite that brand-new
    correct key to `'accent_ink'` -- moving it two steps down the map and
    pointing the text-on-gold role at a gold.

    Nothing would have caught it. Every palette would still have three keys
    and every value would still be a real brand colour; the list widget would
    just quietly start drawing gold text on a gold selection bar.

    The lookarounds refuse any occurrence flanked by a quote. Interpolations
    are unaffected: inside an f-string a bare local is flanked by braces,
    `{accent_text}`, not quotes.
    """
    longest_first = "|".join(sorted(names, key=len, reverse=True))
    return re.compile(r"(?<!['\"])\b(" + longest_first + r")\b(?!['\"])")


# Files that carry quoted keys. Listed rather than globbed so that a file
# appearing later is a visible failure rather than a silent miss -- the count
# is asserted below.
KEY_FILES = (
    "utils/config.py",
    "ui/about_dialog.py",
    "ui/ui_handler.py",
    "core/color_fine_tune.py",
    "core/color_slot.py",
    "core/package_d_panel.py",
    "tests/test_contrast_pairs.py",
    "tests/test_brand_mirror.py",
    "test_rnv_color_mixer.py",
)

# Measured on the tree this was written against, not estimated. A hand-written
# list needs a companion that proves nothing fell off it -- see
# assert_no_key_file_was_missed().
EXPECTED_KEY_HITS = 44
EXPECTED_LOCAL_HITS = 17


# --------------------------------------------------------------------------
# 3. The guard test
# --------------------------------------------------------------------------

GUARD_PATH = "tests/test_accent_naming.py"

GUARD_SOURCE = r'''"""The two accent role names -- and proof the retired ones are gone.

    accent_ink   the brand gold, used AS text
    accent_text  the colour drawn ON the gold

This matches rnv-text-transformer and rnv-color-palette-manager. The mixer
previously called these accent_text and accent_on, which gave `accent_text`
the opposite meaning it carries in the other two repositories.

This file MENTIONS the retired names. It is therefore excluded from the sweep
that forbids them -- the use/mention distinction, which has produced a false
"clean" in this family more than once.
"""

import pathlib
import re

import pytest

from utils import config

REPO = pathlib.Path(__file__).resolve().parents[1]
PALETTES = {
    "DARK": config.ThemeManager.DARK_THEME,
    "LIGHT": config.ThemeManager.LIGHT_THEME,
    "IMAGE": config.ThemeManager.IMAGE_THEME,
}

RETIRED = ("accent_on", "accent_on_col", "accent_on_text", "accent_text_role")

# Only this file may say the retired names out loud.
MENTION_ONLY = {pathlib.Path(__file__).name}

# The app packages. Asserted to be represented in every sweep, so that
# skipping delivery scripts can never quietly become skipping real code.
APP_PACKAGES = ("core", "ui", "utils", "tests")

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".pytest_cache",
             "htmlcov"}


def _is_delivery_script(path: pathlib.Path) -> bool:
    """A one-shot migration script is neither app code nor test code.

    It has to name the values and identifiers it is retiring, so it will
    always trip a sweep like this one, and it deletes itself once its change
    is applied. Excluding it is correct -- but the exclusion is deliberately
    NOT asserted live, because after `--finish` there is nothing left to
    assert against, and an exemption that fails when it becomes unnecessary
    is just a different way to break the build.

    What IS asserted is that excluding it did not also exclude anything real:
    see test_that_sweep_is_actually_looking.
    """
    if "scripts" in path.parts:
        return True
    return path.parent == REPO and path.name.startswith("up")


def _sources():
    for path in sorted(REPO.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in MENTION_ONLY:
            continue
        if _is_delivery_script(path):
            continue
        yield path


# ---------------------------------------------------------------- the keys

@pytest.mark.parametrize("name", sorted(PALETTES))
def test_every_palette_carries_both_role_keys(name):
    palette = PALETTES[name]
    assert "accent_ink" in palette, name
    assert "accent_text" in palette, name


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_accent_ink_is_a_brand_gold(name):
    """accent_ink is the gold. If it ever holds black or white, the swap
    ran in the wrong direction."""
    golds = {getattr(config, n).lower() for n in dir(config)
             if n.startswith("BRAND_") and isinstance(getattr(config, n), str)}
    assert PALETTES[name]["accent_ink"].lower() in golds, PALETTES[name]["accent_ink"]


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_accent_text_is_the_ink_drawn_on_gold(name):
    """accent_text is black or white -- never a gold. This is the assertion
    that fails loudly if the two names are ever swapped back."""
    assert PALETTES[name]["accent_text"].lower() in {"#000000", "#ffffff"}, \
        PALETTES[name]["accent_text"]


def test_the_two_roles_never_hold_the_same_value():
    for name, palette in PALETTES.items():
        assert palette["accent_ink"] != palette["accent_text"], name


# ------------------------------------------------------- the retired names

def test_no_source_file_uses_a_retired_name():
    offenders = []
    for path in _sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        for retired in RETIRED:
            if re.search(r"\b" + retired + r"\b", text):
                offenders.append(f"{path.relative_to(REPO)}: {retired}")
    assert not offenders, "retired accent names still in use:\n  " + \
        "\n  ".join(offenders)


def test_that_sweep_is_actually_looking():
    """Guard the guard.

    test_no_source_file_uses_a_retired_name can only report a problem if it
    reads files and its pattern still matches. A sweep that walks an empty
    list passes forever. Both halves are asserted here: that the walk is
    non-empty and reaches the modules that were renamed, and that the
    pattern still fires on a planted string.
    """
    walked = {p.relative_to(REPO).as_posix() for p in _sources()}
    assert len(walked) > 40, f"the sweep only found {len(walked)} files"

    # Every file the rename touched must still be inside the sweep.
    for required in ("utils/config.py", "core/package_d_panel.py",
                     "core/color_slot.py", "ui/ui_handler.py",
                     "core/color_fine_tune.py", "ui/about_dialog.py"):
        assert required in walked, f"{required} is not being swept"

    # And every app package must be represented, so that the delivery-script
    # exclusion can never widen into skipping real code.
    for package in APP_PACKAGES:
        covered = [w for w in walked if w.startswith(package + "/")]
        assert len(covered) >= 3, \
            f"only {len(covered)} files swept under {package}/"

    planted = "x = theme['accent_on']"
    assert any(re.search(r"\b" + r + r"\b", planted) for r in RETIRED), \
        "the retired-name pattern no longer matches a known offender"


def test_the_mention_exemption_is_not_dead():
    """An exemption list is asserted in BOTH directions. A dead exemption is
    a licence waiting for a future defect."""
    here = pathlib.Path(__file__)
    assert here.name in MENTION_ONLY
    text = here.read_text(encoding="utf-8")
    assert "accent_on" in text, \
        "this file no longer mentions the retired names -- drop the exemption"


# ------------------------------------------------------ nothing else moved

def test_the_rename_did_not_change_what_light_renders():
    """The whole point: a rename, not a revalue."""
    light = PALETTES["LIGHT"]
    assert light["accent"] == config.BRAND_DARK_GOLD
    assert light["accent_ink"] == config.BRAND_DARK_GOLD_DEEP
    assert light["accent_text"] == "#ffffff"


def test_the_rename_did_not_change_what_dark_renders():
    for name in ("DARK", "IMAGE"):
        palette = PALETTES[name]
        assert palette["accent"] == config.BRAND_GOLD
        assert palette["accent_ink"] == config.BRAND_GOLD
        assert palette["accent_text"] == "#000000"
'''


# --------------------------------------------------------------------------
# 3b. A flake found while proving this change, recorded rather than skipped
# --------------------------------------------------------------------------

KNOWN_ISSUES = "KNOWN_ISSUES.md"

KNOWN_ISSUES_ANCHOR = """**Planned fix:** Split QThread machinery off from `ColorHistory`
construction. Same architectural pattern as the `AsyncFileOps` refactor
listed above — both classes mix lifecycle management of background
threads into operations that conceptually shouldn't require them.
"""

KNOWN_ISSUES_ADDITION = """
### `FileWriterThread` signal tests — intermittent SIGABRT, deliberately not skipped

**Runs on:** both CI runners, and green there.

Measured 22 Aug 2026 on offscreen Linux:
`tests/test_threading.py::TestColorHistoryThreading::test_save_async_emits_finished_with_success_true`
aborts Python natively (`Fatal Python error: Aborted`) in roughly one run
in thirty, and much more readily when the machine is under load. It did so
on an **untouched checkout of `main`** as well as on a modified tree, so it
is the thread lifecycle and the environment, not any particular change.

That last point is the reason this entry exists. The abort surfaces during
whatever work happens to be in flight, and it reads exactly like a
regression in that work. It is not one.

Same root cause as the two entries above. `qtbot.waitSignal` returns the
instant `finished` fires; the `thread` local then goes out of scope at the
end of the test, and Qt can find itself destroying a `QThread` that has not
finished unwinding. `test_file_writer_thread_progress_signal_reaches_100`
is in the same family.

**User impact:** None. Nothing in the running app destroys a
`FileWriterThread` this way — the owning object holds the reference for as
long as the thread lives.

**Why it is not skipped:** it passes on both runners and covers a real
path. Skipping would trade a rare red for permanently missing coverage.
If it becomes noisy, deselect it the way `TestAsyncFileOpsErrorPaths` is
deselected rather than marking it skip, so the cost stays visible.

**Planned fix:** the same refactor as above — hold the thread on the
object, not on the stack.
"""


def record_the_threading_flake(tree: Tree) -> None:
    src = tree.get(KNOWN_ISSUES)
    if "intermittent SIGABRT" in src:
        print(f"  {KNOWN_ISSUES}: already recorded")
        return
    if src.count(KNOWN_ISSUES_ANCHOR) != 1:
        raise Halt(
            f"{KNOWN_ISSUES}: could not find the ColorHistory async-write "
            f"entry to file this beneath. Refusing to guess a location.")
    tree.set(KNOWN_ISSUES,
             src.replace(KNOWN_ISSUES_ANCHOR,
                         KNOWN_ISSUES_ANCHOR + KNOWN_ISSUES_ADDITION))
    print(f"  {KNOWN_ISSUES}: filed under the existing ColorHistory entry")


# --------------------------------------------------------------------------
# 4. Machinery
#
# Every pass operates on an in-memory Tree and returns. Nothing touches the
# working copy until flush() runs, at the very end, after verification.
#
# Two things fall out of that, both of which cost a defect to learn:
#
#   * --check is a real rehearsal. When the passes wrote straight to disk, the
#     dry run could not exercise the local-variable pass at all, because that
#     pass asserts the key pass has already run and in dry mode it had not.
#     A dry run that cannot reach step 2 is not checking step 2.
#   * A failure part-way through leaves the repository untouched rather than
#     half-renamed. Given that this change is a SWAP, a half-applied run is
#     the worst possible state: both roles pointing at one value, with tests
#     that would mostly still pass.
# --------------------------------------------------------------------------

class Halt(SystemExit):
    pass


def _this_script() -> str:
    """Where this script sits, relative to the repository root.

    A migration script has to spell out the names it is retiring, so it will
    always look like an offender to its own sweep. The first cut of this
    excluded the `scripts/` directory and stopped there -- which was fine
    while the script lived in `scripts/`, and refused to run the moment it
    was invoked from the repository root as `up.py`. It swept itself, found
    `accent_text` and `accent_on` in its own KEY_MAP, and halted.

    Excluding by resolved path rather than by directory or filename means it
    does not matter where or under what name this file is run from.
    """
    return os.path.relpath(os.path.realpath(__file__),
                           os.path.realpath(os.getcwd())).replace(os.sep, "/")


class Tree:
    """The working copy, held in memory until it is proven."""

    SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "scripts",
                 ".pytest_cache", "htmlcov"}

    def __init__(self) -> None:
        self.files: dict[str, str] = {}      # path -> text, loaded lazily
        self.dirty: set[str] = set()

    # -- reading ---------------------------------------------------------

    def get(self, path: str) -> str:
        """Strict UTF-8. For a file this script is going to rewrite."""
        if path not in self.files:
            with open(path, "r", encoding="utf-8") as handle:
                self.files[path] = handle.read()
        return self.files[path]

    def sweep_text(self, path: str) -> str:
        """Lenient. For SWEEPS only -- never for a file about to be rewritten.

        Every pattern swept for here is pure ASCII, so a replacement character
        can neither invent a hit nor hide one. Reading strictly would mean a
        single bad byte anywhere in the tree blinds the whole audit, which is
        the opposite of what a sweep is for. This tree had exactly such a
        byte; see fix_the_cp1252_byte.
        """
        if path in self.files:
            return self.files[path]
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def set(self, path: str, text: str) -> None:
        self.files[path] = text
        self.dirty.add(path)

    def sources(self):
        """Every .py file in the repository, except this script itself.

        The exclusion is by resolved path, so it holds whether this file is
        run as `scripts/up.py`, as `up.py` from the root, or under any other
        name. See _this_script().
        """
        me = _this_script()
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for name in sorted(names):
                if not name.endswith(".py"):
                    continue
                path = os.path.relpath(os.path.join(root, name),
                                       ".").replace(os.sep, "/")
                if path == me:
                    continue
                yield path

    # -- writing ---------------------------------------------------------

    def flush(self) -> int:
        for path in sorted(self.dirty):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.files[path])
        return len(self.dirty)


# --------------------------------------------------------------------------
# 5. The passes
# --------------------------------------------------------------------------

MOJIBAKE = ("core/palette_formats.py", 0x97, "—")


def fix_the_cp1252_byte(tree: Tree) -> None:
    """core/palette_formats.py carries a single 0x97 byte inside a comment.

    0x97 is the cp1252 em-dash. As UTF-8 it is not a valid start byte, so the
    file is not valid UTF-8 -- and every tool that opens this tree's .py files
    with encoding="utf-8" and no errors= handler dies on this one file. That
    included the sweep in this script, which is how it was found.

    CPython compiles it anyway and CI is green, so nothing is broken today.
    It becomes the real U+2014 the author meant, which is what the rest of the
    tree already uses. One byte becomes three, inside a comment; no behaviour
    changes.
    """
    path, bad, good = MOJIBAKE
    with open(path, "rb") as handle:
        raw = handle.read()
    if bad not in raw:
        print(f"  {path}: already clean")
        return
    count = raw.count(bytes([bad]))
    if count != 1:
        raise Halt(f"{path} holds {count} 0x97 bytes, expected exactly 1")
    fixed = raw.replace(bytes([bad]), good.encode("utf-8"))
    tree.set(path, fixed.decode("utf-8"))   # decode proves it before we keep it
    print(f"  {path}: 0x97 -> U+2014, the em-dash it was always meant to be")


def check_fingerprint(tree: Tree) -> bool:
    """True to proceed; False if this tree already has the change."""
    if all(os.path.exists(p) and n in tree.sweep_text(p) for p, n, _ in ALREADY_DONE):
        print("Already applied -- utils/config.py already defines accent_ink.")
        print("Nothing to do. This is the idempotent exit, not an error.")
        return False

    missing = []
    for path, needle, why in FINGERPRINT:
        if not os.path.exists(path):
            missing.append(f"  {path} does not exist")
        elif needle not in tree.sweep_text(path):
            missing.append(f"  {path}: expected {needle!r}\n      ({why})")
    if missing:
        raise Halt(
            "This is not the tree this script was written against:\n"
            + "\n".join(missing)
            + "\n\nRun it from the root of a clean checkout of main."
        )
    return True


def assert_no_key_file_was_missed(tree: Tree) -> None:
    """KEY_FILES is spelled out by hand so a reviewer can read it, which makes
    it exactly the kind of list that goes stale in silence. Sweep the whole
    repository for the same pattern and assert the two agree in BOTH
    directions -- a file that stops carrying keys is as loud as one that
    starts."""
    found = {p for p in tree.sources() if KEY_RE.search(tree.sweep_text(p))}
    listed = set(KEY_FILES)
    if found != listed:
        extra = sorted(found - listed)
        hint = ""
        if any(os.path.basename(p).startswith("up") for p in extra):
            hint = ("\n\n  One of those looks like a delivery script. This "
                    "script excludes\n  ITSELF by resolved path, so a SECOND "
                    "migration script left in the\n  tree will trip this. "
                    "Remove it and run again.")
        raise Halt(
            "KEY_FILES does not match a repository sweep.\n"
            f"  carrying keys but not listed: {extra or 'none'}\n"
            f"  listed but carrying none:     {sorted(listed - found) or 'none'}"
            + hint
        )
    me = _this_script()
    where = f", ignoring this script at {me}" if not me.startswith("..") else ""
    print(f"  file list agrees with a repo sweep ({len(listed)} files{where})")


def rename_keys(tree: Tree) -> int:
    total = 0
    for path in KEY_FILES:
        if not os.path.exists(path):
            raise Halt(f"expected file is missing: {path}")
        src = tree.get(path)
        hits = len(KEY_RE.findall(src))
        if not hits:
            raise Halt(
                f"{path} is listed as carrying palette keys but has none. "
                f"Either the file moved or the list is stale -- both need a look."
            )
        tree.set(path, KEY_RE.sub(
            lambda m: m.group(1) + KEY_MAP[m.group(2)] + m.group(1), src))
        print(f"  {path}: {hits} key{'s' if hits != 1 else ''}")
        total += hits
    return total


def rename_locals(tree: Tree) -> int:
    """Bare identifiers only. See _local_re for why that qualifier is the
    whole ballgame.

    Before touching anything, prove on this file's own text that the pattern
    genuinely skips quoted tokens. Asserting the property here, against the
    real content rather than a toy string, is what stops a future edit to the
    regex from silently removing the protection.
    """
    total = 0
    for path, mapping in LOCAL_MAP.items():
        src = tree.get(path)
        pattern = _local_re(mapping)
        for old in mapping:
            for quote in ("'", '"'):
                token = quote + old + quote
                if token in src and pattern.search(token):
                    raise Halt(
                        f"{path}: the local pattern matches the quoted key "
                        f"{token}. It would rewrite a key the previous pass "
                        f"just corrected. Refusing to run.")
        hits = len(pattern.findall(src))
        if not hits:
            raise Halt(f"{path}: no local variables matched {sorted(mapping)}")
        tree.set(path, pattern.sub(lambda m: mapping[m.group(1)], src))
        print(f"  {path}: {hits} local{'s' if hits != 1 else ''}")
        total += hits
    return total


LOCKED = "test_rnv_color_mixer.py"
OLD_DIGEST = "58e6313c8622cb93d777bdf69f4cd0cea7030f84f06f20f151c054c8c665ec9f"
WORKFLOWS = (".github/workflows/tests-linux.yml",
             ".github/workflows/tests-windows.yml")


def repin_locked_file(tree: Tree) -> str:
    """Recompute the digest from the pending content and rewrite both pins.

    The digest is never typed in. It is taken from the exact bytes flush()
    is about to write, so the pin cannot drift from the content it pins --
    and because both workflows are rewritten from that one value, they cannot
    drift from each other either.
    """
    pending = tree.get(LOCKED).encode("utf-8")
    digest = hashlib.sha256(pending).hexdigest()
    if digest == OLD_DIGEST:
        raise Halt("the locked file did not change; refusing to re-pin a "
                   "digest that already matches")
    for workflow in WORKFLOWS:
        src = tree.get(workflow)
        count = src.count(OLD_DIGEST)
        if count != 1:
            raise Halt(
                f"{workflow} holds the old digest {count} times, expected 1. "
                f"Refusing to guess which one to move.")
        tree.set(workflow, src.replace(OLD_DIGEST, digest))
        print(f"  {workflow}: pin -> {digest[:16]}...")
    return digest


def install_guard(tree: Tree) -> None:
    tree.set(GUARD_PATH, GUARD_SOURCE)
    print(f"  {GUARD_PATH}: {len(GUARD_SOURCE.splitlines())} lines")


RETIRED = ("accent_on", "accent_on_col", "accent_on_text", "accent_text_role")


def verify(tree: Tree, digest: str) -> None:
    """Post-conditions on the PENDING tree, so a failure writes nothing."""
    problems = []

    guard_name = os.path.basename(GUARD_PATH)
    swept = 0
    for path in tree.sources():
        if os.path.basename(path) == guard_name:
            continue           # the one file whose job is to mention them
        swept += 1
        text = tree.sweep_text(path)
        for retired in RETIRED:
            if re.search(r"\b" + retired + r"\b", text):
                problems.append(f"{path} still uses {retired}")
    if swept < 40:
        problems.append(f"the sweep only visited {swept} files; it is not looking")

    # Guard the guard: the pattern must still fire on a known offender.
    if not any(re.search(r"\b" + r + r"\b", "x = theme['accent_on']")
               for r in RETIRED):
        problems.append("the retired-name pattern no longer matches a real offender")

    if hashlib.sha256(tree.get(LOCKED).encode("utf-8")).hexdigest() != digest:
        problems.append("the locked file changed after the digest was taken")
    for workflow in WORKFLOWS:
        if digest not in tree.get(workflow):
            problems.append(f"{workflow} does not carry the new digest")

    # The palettes. Parsed as text, not imported -- importing config pulls in
    # PyQt6, which this script must never require.
    config_src = tree.get("utils/config.py")
    for key, want in (("'accent_ink'", 3), ("'accent_text'", 3)):
        got = config_src.count(key)
        if got != want:
            problems.append(f"expected {want} {key} in config, found {got}")

    # And neither side of the swap collapsed onto the other's value. These
    # four assertions are the ones that fail loudly if the rename ran in the
    # wrong direction, which is the only way this change can do damage.
    if "'accent_ink': BRAND_DARK_GOLD_DEEP" not in config_src:
        problems.append("light accent_ink is not BRAND_DARK_GOLD_DEEP")
    if "'accent_text': '#ffffff'" not in config_src:
        problems.append("light accent_text is not #ffffff")
    if config_src.count("'accent_text': '#000000'") != 2:
        problems.append("dark/image accent_text is not #000000 in both")

    if problems:
        raise Halt("VERIFY FAILED -- nothing was written:\n  "
                   + "\n  ".join(problems))
    print(f"  verify: {swept} files swept, retired names gone, pins agree, "
          f"palettes intact")


def finish() -> None:
    here = os.path.abspath(__file__)
    os.remove(here)
    print(f"Removed {here}")
    parent = os.path.dirname(here)
    try:
        if not os.listdir(parent):
            print(f"note: {parent}/ is empty now. Git does not track empty "
                  f"directories, so it disappears on commit. That is what "
                  f"happened to rnv-color-mcp's scripts/ folder.")
    except OSError:
        pass


# --------------------------------------------------------------------------
# 6. Driver
# --------------------------------------------------------------------------

def main() -> int:
    refuse_to_shadow()

    if "--finish" in sys.argv:
        finish()
        return 0

    dry = "--check" in sys.argv

    if not os.path.exists("utils/config.py"):
        raise Halt("run this from the repository root "
                   "(utils/config.py not found)")

    tree = Tree()
    if not check_fingerprint(tree):
        return 0

    print("DRY RUN -- every pass runs, nothing is written\n" if dry
          else "Applying\n")

    print("0. one stray cp1252 byte, so the tree is valid UTF-8 end to end")
    fix_the_cp1252_byte(tree)

    print("\n1. palette keys  accent_text -> accent_ink, accent_on -> accent_text")
    assert_no_key_file_was_missed(tree)
    keys = rename_keys(tree)
    print(f"   {keys} total (expected {EXPECTED_KEY_HITS})")
    if keys != EXPECTED_KEY_HITS:
        raise Halt(
            f"expected {EXPECTED_KEY_HITS} quoted keys, found {keys}. The tree "
            f"has moved since this was written; stopping rather than applying "
            f"a partial rename.")

    print("\n2. local variables the swap would otherwise leave misleading")
    local_hits = rename_locals(tree)
    print(f"   {local_hits} total (expected {EXPECTED_LOCAL_HITS})")
    if local_hits != EXPECTED_LOCAL_HITS:
        raise Halt(f"expected {EXPECTED_LOCAL_HITS} local renames, "
                   f"found {local_hits}")

    print("\n3. locked-file digest, recomputed and re-pinned in both workflows")
    digest = repin_locked_file(tree)

    print("\n4. guard test")
    install_guard(tree)

    print("\n5. a threading flake found while proving this, recorded not skipped")
    record_the_threading_flake(tree)

    print("\n6. verify the pending tree")
    verify(tree, digest)

    if dry:
        print(f"\nDry run complete. {len(tree.dirty)} files would change; "
              f"none were written.")
        return 0

    written = tree.flush()
    print(f"\n7. wrote {written} files")

    print("\nDone. Now run, from the repository root:")
    print('    QT_QPA_PLATFORM=offscreen python -m pytest test_rnv_color_mixer.py'
          ' -q --deselect "test_rnv_color_mixer.py::TestImageHandler::'
          'test_load_real_image_if_available"')
    print("    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q --deselect "
          "tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths")
    print(f"\nThen, once both are green:  python {_this_script()} --finish")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Halt as stop:
        print(f"\n{stop}", file=sys.stderr)
        sys.exit(1)
