"""The two accent role names -- and proof the retired ones are gone.

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
