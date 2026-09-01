"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. Before this pass the main family here was called button_* -- the same
name that holds the GOLD DIALOG scheme in rnv-color-picker and
rnv-icon-builder. One name, two schemes, decided by which repository you had
open. These tests are what stop it drifting back.

Worth knowing about this application specifically: the main window's buttons
are painted by the QSS blocks in utils/config.py from module constants, not
from these palette keys at all. The keys are read by ColorSlot and by the UI
handler in the main window, and by three dialogs. The dialogs now read a
family of their own.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = ("button_bg", "button_text", "button_hover_bg", "button_pressed_bg",
       "button_pressed_text", "button_pressed_border")
NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)
DIALOG = ("dialog_btn_bg", "dialog_btn_hover_bg", "dialog_btn_pressed_bg")

PINNED_MAIN = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",
             "main_btn_pressed_text": "#000000",
             "main_btn_pressed_border": "#d2bc93"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#8c7337",
              "main_btn_pressed_text": "#ffffff",
              "main_btn_pressed_border": "#8c7337"},
    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
              "main_btn_hover_bg": "#333333", "main_btn_pressed_bg": "#d2bc93",
              "main_btn_pressed_text": "#000000",
              "main_btn_pressed_border": "#d2bc93"},
}

#: What the three dialogs painted before the rename, key for key.
PINNED_DIALOG = {
    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",
             "dialog_btn_pressed_bg": "#d2bc93"},
    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_hover_bg": "#333333",
              "dialog_btn_pressed_bg": "#8c7337"},
    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_hover_bg": "#333333",
              "dialog_btn_pressed_bg": "#d2bc93"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE from a MENTION. The two files certain
#: to mention the old names are this guard -- which lists them in order to
#: forbid them -- and the delivery script that performs the rename. Skipped by
#: marker rather than by filename: the script arrives under whatever name it
#: is saved as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")

DIALOG_FILES = ("ui/about_dialog.py", "core/color_fine_tune.py",
                "core/package_d_panel.py")
MAIN_FILES = ("ui/ui_handler.py", "core/color_slot.py")


def _palettes():
    from utils.config import ThemeManager
    return {"dark": ThemeManager.DARK_THEME, "light": ThemeManager.LIGHT_THEME,
            "image": ThemeManager.IMAGE_THEME}


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these keys must say where the button lives:\n  " + "\n  ".join(offenders))


TOOL_MARKER = "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP"


def test_no_application_file_is_exempt_from_the_sweep():
    """The exemption is by marker, and the marker is how a file could hide.

    An earlier version of this counted marked files and allowed two. That
    failed in a working tree holding a second copy of the delivery script --
    a guard failing on the state of somebody's checkout rather than on a
    defect in the application, which is the wrong thing to fail on.

    What actually matters is that no APPLICATION file is exempt. This guard
    may carry a marker; it lists the old names in order to forbid them.
    Everything else must be a delivery script, identified by the tool marker
    in its own header -- those arrive under whatever name they are saved as,
    there can be several of them lying around, and none is application source.
    """
    here = Path(__file__).resolve()
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if not any(marker in text for marker in MARKERS):
            continue
        if path.resolve() == here or TOOL_MARKER in text:
            continue
        strays.append(str(path.relative_to(ROOT)))
    assert not strays, (
        "these files are skipped by the name sweep but are not a delivery "
        f"script: {strays}")
    assert MARKERS[0] in here.read_text(encoding="utf-8-sig"), (
        "this guard lost its own marker and is now sweeping itself")


def test_all_three_palettes_carry_both_families():
    for mode, palette in _palettes().items():
        missing = [n for n in NEW + DIALOG if n not in palette]
        assert not missing, f"{mode} palette missing {missing}"


def test_the_rename_moved_no_value():
    for mode, pins in PINNED_MAIN.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} main button values changed.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_dialog_family_holds_what_the_dialogs_already_painted():
    for mode, pins in PINNED_DIALOG.items():
        actual = {k: _palettes()[mode].get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} dialog button values are not what those dialogs "
            f"painted before the rename.\n  wanted {pins}\n  found  {actual}")


def test_dialogs_read_the_dialog_family_and_not_the_main_one():
    for rel in DIALOG_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "dialog_btn_" in src, f"{rel} no longer reads the dialog family"
        assert not re.search(r"(['\"])main_btn_", src), (
            f"{rel} reads the main family. Dialogs open later and take the "
            f"dialog scheme; wiring one to main_btn_* refuses the distinction "
            f"this rename exists to make.")


def test_the_main_window_reads_the_main_family():
    for rel in MAIN_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert re.search(r"(['\"])main_btn_", src), (
            f"{rel} no longer reads the main family")
        assert "dialog_btn_" not in src, (
            f"{rel} is main-window code and must not read the dialog family")


def test_the_gold_press_belongs_to_the_dialog_family_too():
    """The gold pressed plate is read by exactly one place, and it is a dialog.

    This is the finding that made the rename worth doing here. Reading
    button_pressed_bg out of the palette suggested the MAIN button pressed to
    gold; it does not -- the main window's pressed plate is #444444, written
    into the QSS blocks in utils/config.py as APP_BTN_PRESSED. The gold was
    always the dialog's. The name now says so.
    """
    config = (ROOT / "utils" / "config.py").read_text(encoding="utf-8-sig")
    assert "APP_BTN_PRESSED" in config
    panel = (ROOT / "core" / "package_d_panel.py").read_text(encoding="utf-8-sig")
    assert "dialog_btn_pressed_bg" in panel
