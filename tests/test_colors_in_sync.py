"""The color file is what the brand and the map say it is.   RNV-COLOR-SYNC

Installed 2026-10-16, ruled in #36 to #48. brand_map.json says where each
color in this application's color file comes from: a name in rnv-brand, or a
value this application owns, with the reason. tools/sync_colors.py writes the
value on each of those lines from the map and from the brand at the commit
pinned in tests/requirements-dev.txt, and writes COLORS.md, the chart of them.
The same two files, this one and the tool, are in all five applications;
brand_map.json is what differs.

WHAT THIS REPLACES. Until this date each brand value was written out by hand
in two places, the color file and a test beside it, and a brand move meant
editing both (#39). The tests that wrote a value as its hex code now hold the
name it takes; this file holds every value, once, against the brand itself.
The few sample colors it needs are named in tests/color_values.py (#53 A).

WHAT THIS GUARD HOLDS.

1. The color file and COLORS.md are exactly what the sync would write. A
   value edited by hand, a map entry changed without a sync, or a pin moved
   without one, and this names the file and says what to run.
2. Every color the color file writes as a value is in the map, and every
   color the application owns says why.
3. The provenance maps in the color file agree with the map: a register
   value is a brand name there, an application's ramp step or semantic color
   is its own, a derived value is code.
4. The sync is looking: it puts back a value edited by hand, refuses a color
   the map does not hold, refuses a derived color in the map, refuses a
   brand that is not the pinned one, and carries a brand move to the one line
   that takes it.
5. The daily workflow runs the sync against the brand's head and opens a pull
   request only when the color file moved.
"""
from __future__ import annotations

import importlib
import importlib.util
import pathlib
import re
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "brand-sync.yml"


def _sync():
    """tools/sync_colors.py, loaded by path: tools/ is not a package."""
    spec = importlib.util.spec_from_file_location(
        "sync_colors", ROOT / "tools" / "sync_colors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SYNC = _sync()


def _color_values():
    """tests/color_values.py, loaded by path, so this file is the same in every
    application whichever way its tests import one another (#53 A)."""
    spec = importlib.util.spec_from_file_location(
        "color_values_for_sync", pathlib.Path(__file__).with_name("color_values.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CV = _color_values()
MAPPING = SYNC.load_map(ROOT)
COLORS = MAPPING["colors"]
COLOR_FILE = MAPPING["color_file"]
MODULE = importlib.import_module(COLOR_FILE[:-3].replace("/", "."))

#: What each provenance class in the color file means for the map. A class
#: not listed here -- the mixer's "step", which covers register values and its
#: own alike -- places no constraint.
KINDS = {"register": "brand", "anchor": "brand",
         "app-ramp": "own", "app-canvas": "own", "app-semantic": "own",
         "derived": "code", "register-overlay": "code", "alias": "code"}


def _brand():
    """The register as installed, refused unless it is the pinned commit."""
    try:
        brand, _ = SYNC.load_brand(ROOT)
    except SYNC.SyncError as exc:
        pytest.fail(str(exc))
    return brand


def _text():
    return SYNC.read(ROOT / COLOR_FILE)[0]


# ------------------------------------------------------------------ in sync

def test_the_color_file_and_the_chart_are_what_the_sync_writes():
    try:
        plan = SYNC.build(ROOT)
    except SYNC.SyncError as exc:
        pytest.fail(str(exc))
    stale = [path.relative_to(ROOT).as_posix()
             for path, (before, after, _form) in plan.items() if before != after]
    assert not stale, (
        f"out of date: {', '.join(stale)}. Run: python tools/sync_colors.py\n"
        f"A value in {COLOR_FILE} is written from brand_map.json and the brand "
        f"at the pin; change the map, not the value.")


def test_every_color_the_file_writes_is_in_the_map():
    written = SYNC.color_constants(_text())
    missing = sorted(set(written) - set(COLORS))
    phantom = sorted(n for n in COLORS if not hasattr(MODULE, n))
    assert not missing, f"colors brand_map.json does not hold: {missing}"
    assert not phantom, f"brand_map.json names what {COLOR_FILE} does not have: {phantom}"
    assert len(written) >= 20, f"only {len(written)} colors found -- the reader is blind"


def test_every_color_the_app_owns_says_why():
    owned = {n: e for n, e in COLORS.items() if isinstance(e, dict)}
    assert owned, "the map holds no color of the application's own -- the reader is blind"
    silent = [n for n, e in owned.items() if len(e.get("why", "").split()) < 3]
    assert not silent, f"app-owned colors with no reason: {silent}"


def test_the_provenance_maps_agree_with_the_map():
    """Each *PROVENANCE dict in the color file classifies names. A register
    value is a brand name in the map; an application's ramp step, canvas or
    semantic color is its own; a derived, overlay or alias value is code, and
    not in the map."""
    tables = [v for k, v in vars(MODULE).items()
              if k.endswith("PROVENANCE") and isinstance(v, dict)]
    assert tables, f"{COLOR_FILE} has no provenance map -- the reader is blind"
    wrong, read = [], 0
    for table in tables:
        for name, kind in table.items():
            want = KINDS.get(kind)
            entry = COLORS.get(name)
            if want is None:
                continue
            read += 1
            if want == "brand" and not isinstance(entry, str):
                wrong.append(f"{name} is {kind} and the map has {entry!r}")
            elif want == "own" and not isinstance(entry, dict):
                wrong.append(f"{name} is {kind} and the map has {entry!r}")
            elif want == "code" and entry is not None:
                wrong.append(f"{name} is {kind} and the map writes it as a value")
    assert read >= 2, f"only {read} provenance entries read -- the reader is blind"
    assert not wrong, "the provenance maps and brand_map.json disagree:\n  " + "\n  ".join(wrong)


# ---------------------------------------------------------- the sync is looking

def _a_brand_line(text):
    """A mapped brand color written as a plain hex, and its line."""
    for name, entry in COLORS.items():
        if not isinstance(entry, str):
            continue
        value = getattr(MODULE, name)
        for line in text.split("\n"):
            if re.match(rf"{name}\s*(:[^=]+)?=", line) and value in line:
                return name, value, line
    raise AssertionError("no brand color written as a hex -- the reader is blind")


def test_the_sync_puts_back_a_value_edited_by_hand():
    text = _text()
    name, value, line = _a_brand_line(text)
    other = CV.EXAMPLE_HAND_EDIT if value.lower() != CV.EXAMPLE_HAND_EDIT \
        else CV.EXAMPLE_HAND_EDIT_FALLBACK
    edited = text.replace(line, line.replace(value, other), 1)
    assert edited != text
    assert SYNC.rewrite(edited, SYNC.resolve(MAPPING, _brand()), COLOR_FILE) == text


def test_the_sync_refuses_a_color_the_map_does_not_hold():
    text = _text() + f'\nSTRAY_COLOR: Final[str] = "{CV.EXAMPLE_HAND_EDIT}"\n'
    with pytest.raises(SYNC.SyncError, match="STRAY_COLOR"):
        SYNC.rewrite(text, SYNC.resolve(MAPPING, _brand()), COLOR_FILE)


def _a_derived_line(text):
    """A color the file works out in code, on one line with no comment."""
    for line in text.split("\n"):
        match = re.match(r"([A-Z][A-Z0-9_]*)\s*:[^=]+=\s*(\w+\(.*\)|[A-Z][A-Z0-9_]*)$", line)
        if match and "#" not in line and match.group(1) not in COLORS \
                and SYNC.is_color(getattr(MODULE, match.group(1), None)):
            return match.group(1)
    raise AssertionError("no derived color on a line of its own -- the reader is blind")


def test_the_sync_refuses_a_derived_color_in_the_map():
    name = _a_derived_line(_text())
    resolved = dict(SYNC.resolve(MAPPING, _brand()))
    resolved[name] = (getattr(MODULE, name), "app-owned")
    with pytest.raises(SYNC.SyncError, match="code, not a value"):
        SYNC.rewrite(_text(), resolved, COLOR_FILE)


def test_the_sync_refuses_a_brand_that_is_not_the_pin(monkeypatch):
    monkeypatch.setattr(SYNC, "installed_commit", lambda: "0" * 40)
    with pytest.raises(SYNC.SyncError, match="pins"):
        SYNC.load_brand(ROOT)


def test_a_brand_move_reaches_the_one_line_that_takes_it():
    brand = _brand()
    moved = types.SimpleNamespace(**{k: (dict(v) if isinstance(v, dict) else v)
                                     for k, v in vars(brand).items() if not k.startswith("__")})
    elsewhere = CV.EXAMPLE_MOVED_ACCENT if brand.APP["accent"].lower() != CV.EXAMPLE_MOVED_ACCENT \
        else CV.EXAMPLE_MOVED_ACCENT_FALLBACK
    moved.APP["accent"] = elsewhere
    text = _text()
    after = SYNC.rewrite(text, SYNC.resolve(MAPPING, moved), COLOR_FILE)
    changed = [b for a, b in zip(text.split("\n"), after.split("\n")) if a != b]
    assert len(changed) == 1 and changed[0].startswith("BRAND_GOLD") \
        and elsewhere in changed[0] and changed[0].endswith("# brand: APP.accent"), changed


# ------------------------------------------------------------- the daily check

def test_the_daily_workflow_syncs_the_head_and_asks_only_when_a_color_moved():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"^\s+schedule:\s*$", text, re.M), "the workflow runs on no schedule"
    assert "git ls-remote https://github.com/RNVizion/rnv-brand" in text, \
        "the workflow does not read the brand's head"
    assert "python tools/sync_colors.py" in text, "the workflow does not run the sync"
    assert f"git diff --quiet -- {COLOR_FILE}" in text, \
        "the workflow does not ask whether the color file moved"
    assert "set -o pipefail" in text, "a sync that refuses would pass as nothing moved"
    assert "gh pr create" in text and "gh pr view" in text, \
        "the workflow does not open, or look for, its pull request"
