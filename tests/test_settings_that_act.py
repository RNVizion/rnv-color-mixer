"""Settings that did nothing now do what they say (#95 A, 24 October 2026).

WHAT WAS WRONG. The Settings tab offered six choices the app never read:

  * the Color Mixing Algorithm: every mix was weighted RGB;
  * History Size Limit: the history kept 20, whatever the box said;
  * Enable color history: turning it off only wrote a log line;
  * Auto (follow system): it always gave Dark;
  * Auto-load last session on startup: nothing loaded;
  * Default Export Format: no save dialog opened on it.

Each test below drives the app the way a person does where it can: the
settings file a launch reads, the panel's Save, the theme button, the save
dialogs (whose static call is replaced by one that records it). Each one
fails on the code before the change, except the guards that say so.

The system's light or dark preference cannot be set on the offscreen
platform the suite runs on (Qt reports Unknown there, and setColorScheme()
changes nothing), so the tests that need one replace the app's
_system_color_scheme() with a stand-in, and emit Qt's own
colorSchemeChanged signal for a change while running.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from core.color_math import ColorMath

pytestmark = pytest.mark.integration

#: Two slots every algorithm mixes differently.
SLOTS = [((250, 210, 40), 60), ((30, 90, 200), 40)]

#: The Settings box's rows, in order, and the function each must mix with.
ALGORITHMS = [
    ("weighted_rgb", "Weighted RGB (Standard)", ColorMath.weighted_rgb_mix),
    ("weighted_hsv", "Weighted HSV (Perceptual)", ColorMath.weighted_hsv_mix),
    ("lab_perceptual", "LAB Perceptual (Uniform)", ColorMath.lab_perceptual_mix),
    ("subtractive_cmy", "Subtractive CMY (Inks)", ColorMath.subtractive_cmy_mix),
    ("weighted_ryb", "Weighted RYB (Artist)", ColorMath.weighted_ryb_mix),
    ("kubelka_munk", "Kubelka-Munk (Paint)", ColorMath.kubelka_munk_mix),
]


# ─────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────

def _settings_file(home: Path) -> Path:
    """Where the app reads its settings on this system, asked of the app itself.

    The path differs by system (APPDATA on Windows, ~/Library on macOS,
    ~/.config on Linux); the isolated_home fixture points every one of them
    into the test's home. A path written here by hand held on Linux only, and
    on Windows every launch read the defaults instead (found on the first
    Windows run, 26 October).
    """
    from utils.settings_manager import SettingsManager

    probe = SettingsManager.__new__(SettingsManager)
    probe._setup_settings_path()
    path = Path(probe.settings_file)
    assert Path(home) in path.parents, f"the settings path {path} is outside the test's home {home}"
    return path


def _write_settings(home: Path, preferences: dict | None = None,
                    advanced: dict | None = None) -> None:
    """The settings file a launch reads (the rest comes from the defaults)."""
    path = _settings_file(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"preferences": preferences or {},
                                "advanced": advanced or {}}), encoding="utf-8")


def _launch(main_module, qtbot, wait_ms: int = 0):
    win = main_module.ColorMixerApp()
    qtbot.addWidget(win)
    if wait_ms:
        qtbot.wait(wait_ms)
    return win


def _set_slots(win, slots=SLOTS) -> None:
    while len(win.slots) < len(slots):
        win.add_color_slot()
    for slot, (color, weight) in zip(win.slots, slots):
        slot.set_color(color)
        slot.set_weight(weight)
    for slot in win.slots[len(slots):]:
        slot.set_weight(0)


def _mix(win, slots=SLOTS):
    _set_slots(win, slots)
    win.auto_mix_colors()
    win._mix_debounce_timer.stop()      # the mix the slot changes queued is this one
    return win.current_mixed_color


def _panel(win):
    win.open_package_d_panel()
    QApplication.processEvents()
    return win._package_d_panel


def _press_save(panel, monkeypatch) -> None:
    """The Settings tab's Save button, with its "saved" box answered."""
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: 0)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: 0)
    save = [b for b in panel.findChildren(QPushButton) if b.text().strip() == "Save"]
    assert len(save) == 1
    save[0].click()
    QApplication.processEvents()


@pytest.fixture
def dialogs(monkeypatch):
    """Record each save dialog the app opens, and cancel it (or return
    `answer`, if a test sets one)."""
    calls: list[tuple] = []
    state = {"answer": ("", "")}

    def get_save_file_name(*args, **kwargs):
        calls.append(args)
        return state["answer"]

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(get_save_file_name))
    return calls, state


# ═════════════════════════════════════════════════════════════════════════
# 1. Color Mixing Algorithm
# ═════════════════════════════════════════════════════════════════════════

def test_the_slots_mix_differently_by_each_algorithm():
    """Not a test of the app: the premise of the tests below. Each algorithm
    gives these slots its own color, so a mix shows which made it.

    Subtractive CMY used to be the exception: it averaged 1 - RGB and turned
    the average back, which is the RGB average again. Since #98 A it
    multiplies the colors' transmittances, like inks, and differs too. The
    tests below still watch which function the app calls."""
    results = {key: fn(SLOTS) for key, _label, fn in ALGORITHMS}
    assert len(set(results.values())) == len(results), results


def test_color_math_mixes_by_name():
    for key, _label, fn in ALGORITHMS:
        assert ColorMath.mix(SLOTS, key) == fn(SLOTS), key
    assert list(ColorMath.MIXING_ALGORITHMS) == [key for key, _l, _f in ALGORITHMS]
    assert ColorMath.mix(SLOTS, "no_such_algorithm") == ColorMath.weighted_rgb_mix(SLOTS)
    assert ColorMath.DEFAULT_MIXING_ALGORITHM == "weighted_rgb"


def test_the_settings_box_lists_the_algorithms_color_math_mixes_by(app_window):
    """Row n of the box saves the key of the nth function, and loads back.
    A guard, true before the change too: the box and the stored keys were
    already in step; nothing read them."""
    panel = _panel(app_window)
    combo = panel.mixing_algo_combo
    assert [combo.itemText(i) for i in range(combo.count())] == [l for _k, l, _f in ALGORITHMS]
    for row, (key, _label, _fn) in enumerate(ALGORITHMS):
        combo.setCurrentIndex(row)
        panel._save_ui_to_settings(skip_theme=True)
        assert app_window.settings_manager.get("advanced.color_mixing_algorithm") == key
        combo.setCurrentIndex((row + 1) % combo.count())
        panel._load_settings_into_ui()
        assert combo.currentIndex() == row


def test_weighted_rgb_stays_the_default(app_window):
    """A guard, true before the change too: nobody's mix changes until they
    choose another algorithm."""
    assert app_window.settings_manager.get("advanced.color_mixing_algorithm") == "weighted_rgb"
    assert _mix(app_window) == ColorMath.weighted_rgb_mix(SLOTS)


@pytest.mark.parametrize("key,label,fn", ALGORITHMS[1:], ids=[a[0] for a in ALGORITHMS[1:]])
def test_a_launch_mixes_by_the_saved_algorithm(key, label, fn, isolated_home, qtbot,
                                               main_module, monkeypatch):
    called: list[str] = []
    for other_key, _label, other_fn in ALGORITHMS:
        function_name = other_fn.__name__
        real = getattr(ColorMath, function_name)

        def spy(colors_weights, _real=real, _key=other_key):
            called.append(_key)
            return _real(colors_weights)
        monkeypatch.setattr(ColorMath, function_name, staticmethod(spy))
    _write_settings(isolated_home, advanced={"color_mixing_algorithm": key})
    win = _launch(main_module, qtbot)
    try:
        win._mix_debounce_timer.stop()
        called.clear()
        assert _mix(win) == fn(SLOTS), label
        assert called == [key], called
    finally:
        win.close()


def test_saving_another_algorithm_mixes_again_at_once(app_window, monkeypatch):
    """Save in the Settings tab re-mixes the slots as they are; nothing else
    has to move for the preview to change."""
    rgb = _mix(app_window)
    panel = _panel(app_window)
    panel.mixing_algo_combo.setCurrentText("Kubelka-Munk (Paint)")
    _press_save(panel, monkeypatch)
    expected = ColorMath.kubelka_munk_mix(SLOTS)
    assert expected != rgb
    assert app_window.current_mixed_color == expected
    assert app_window.hex_label.text() == ColorMath.rgb_to_hex(expected)


def test_the_saved_algorithm_is_there_at_the_next_launch(app_window, monkeypatch, main_module, qtbot):
    panel = _panel(app_window)
    panel.mixing_algo_combo.setCurrentText("Weighted RYB (Artist)")
    _press_save(panel, monkeypatch)
    disk = json.loads(Path(app_window.settings_manager.settings_file).read_text(encoding="utf-8"))
    assert disk["advanced"]["color_mixing_algorithm"] == "weighted_ryb"
    again = _launch(main_module, qtbot)
    try:
        assert _mix(again) == ColorMath.weighted_ryb_mix(SLOTS)
        again_panel = _panel(again)
        assert again_panel.mixing_algo_combo.currentText() == "Weighted RYB (Artist)"
    finally:
        again.close()


def test_the_mix_cache_does_not_serve_another_algorithm_s_color(app_window):
    """The cache is keyed by the algorithm too: the same slots, mixed again
    after a change, are not answered with the old algorithm's color."""
    assert _mix(app_window) == ColorMath.weighted_rgb_mix(SLOTS)
    app_window.settings_manager.set("advanced.color_mixing_algorithm", "lab_perceptual")
    assert _mix(app_window) == ColorMath.lab_perceptual_mix(SLOTS)


# ═════════════════════════════════════════════════════════════════════════
# 2. History Size Limit
# ═════════════════════════════════════════════════════════════════════════

def _add_colors(history, n: int) -> None:
    for i in range(n):
        history.add_color((10 * i + 5, 100, 200 - 10 * i))


def test_a_launch_keeps_the_history_to_the_saved_limit(isolated_home, qtbot, main_module):
    _write_settings(isolated_home, preferences={"history_size_limit": 3})
    win = _launch(main_module, qtbot)
    try:
        assert win.color_history.max_entries == 3
        _add_colors(win.color_history, 6)
        assert len(win.color_history.get_entries()) == 3
    finally:
        win.close()


def test_the_limit_applies_when_saved_and_the_list_shows_it(app_window, monkeypatch):
    history = app_window.color_history
    _mix(app_window)                    # so Save has no algorithm change to re-mix for
    _add_colors(history, 6)
    newest = [e.color for e in history.get_entries()[:2]]
    panel = _panel(app_window)
    assert panel.history_list.count() == len(history.get_entries()) > 2
    panel.history_limit_spin.setText("2")
    _press_save(panel, monkeypatch)
    assert history.max_entries == 2
    assert [e.color for e in history.get_entries()] == newest
    assert panel.history_list.count() == 2


def test_the_limit_is_held_to_its_range(app_window, monkeypatch):
    panel = _panel(app_window)
    panel.history_limit_spin.setText("0")
    _press_save(panel, monkeypatch)
    assert app_window.settings_manager.get("preferences.history_size_limit") == 1
    assert app_window.color_history.max_entries == 1
    assert panel.history_limit_spin.text() == "1"


def test_set_max_entries_drops_the_oldest(real_color_history, tmp_path):
    history = real_color_history(max_entries=20)
    history.history_file = str(tmp_path / "h.json")
    history.entries = []
    history.save_async = lambda on_complete=None: None
    _add_colors(history, 5)
    newest_three = [e.color for e in history.get_entries()[:3]]
    assert history.set_max_entries(3) == 3
    assert [e.color for e in history.get_entries()] == newest_three
    assert history.set_max_entries(5000) == history.MAX_LIMIT


# ═════════════════════════════════════════════════════════════════════════
# 3. Enable color history
# ═════════════════════════════════════════════════════════════════════════

def test_with_history_off_a_mix_is_not_added(app_window, monkeypatch):
    panel = _panel(app_window)
    panel.history_enabled_check.setChecked(False)
    _press_save(panel, monkeypatch)
    before = len(app_window.color_history.get_entries())
    _mix(app_window)
    _mix(app_window, [((12, 34, 56), 50), ((200, 100, 0), 50)])
    assert len(app_window.color_history.get_entries()) == before


def test_with_history_on_a_mix_is_added(app_window):
    """A guard, true before the change too: the switch did not stop the
    history from working."""
    before = len(app_window.color_history.get_entries())
    _mix(app_window)
    assert len(app_window.color_history.get_entries()) == before + 1


# ═════════════════════════════════════════════════════════════════════════
# 4. Auto (follow system)
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("system,mode", [("light", "light"), ("dark", "dark"), (None, "dark")],
                         ids=["light-system", "dark-system", "unknown-system"])
def test_auto_opens_in_the_system_s_mode(system, mode, isolated_home, qtbot, main_module, monkeypatch):
    monkeypatch.setattr(main_module, "_system_color_scheme", lambda: system, raising=False)
    _write_settings(isolated_home, preferences={"theme": "auto"})
    win = _launch(main_module, qtbot)
    try:
        assert win.ui_handler.theme_manager.current_theme == mode
        assert not win.ui_handler.is_image_mode()
        assert win.theme_button.text() == {"light": "Light Mode", "dark": "Dark Mode"}[mode]
    finally:
        win.close()


def test_auto_follows_a_change_while_running_until_the_button_is_pressed(
        isolated_home, qtbot, main_module, monkeypatch):
    system = {"scheme": "dark"}
    monkeypatch.setattr(main_module, "_system_color_scheme", lambda: system["scheme"],
                        raising=False)
    _write_settings(isolated_home, preferences={"theme": "auto"})
    win = _launch(main_module, qtbot)
    hints = QGuiApplication.styleHints()
    try:
        assert win.ui_handler.theme_manager.current_theme == "dark"
        system["scheme"] = "light"
        hints.colorSchemeChanged.emit(Qt.ColorScheme.Light)
        QApplication.processEvents()
        assert win.ui_handler.theme_manager.current_theme == "light"
        system["scheme"] = "dark"
        hints.colorSchemeChanged.emit(Qt.ColorScheme.Dark)
        QApplication.processEvents()
        assert win.ui_handler.theme_manager.current_theme == "dark"

        win._on_theme_button_clicked()                 # a mode chosen by hand
        QApplication.processEvents()
        chosen = win.ui_handler.theme_manager.current_theme
        assert win.settings_manager.get("preferences.theme") == chosen
        system["scheme"] = "light" if chosen != "light" else "dark"
        hints.colorSchemeChanged.emit(Qt.ColorScheme.Light)
        QApplication.processEvents()
        assert win.ui_handler.theme_manager.current_theme == chosen, "Auto did not end"
    finally:
        win.close()


def test_a_closed_window_no_longer_hears_the_system(isolated_home, qtbot, main_module, monkeypatch):
    """A guard (the window before the change heard nothing at all): the
    system's signal outlives every window, so a closed one must let go."""
    system = {"scheme": "dark"}
    monkeypatch.setattr(main_module, "_system_color_scheme", lambda: system["scheme"],
                        raising=False)
    _write_settings(isolated_home, preferences={"theme": "auto"})
    win = _launch(main_module, qtbot)
    heard = []
    monkeypatch.setattr(win, "_apply_theme_setting", lambda theme: heard.append(theme))
    win.close()
    QApplication.processEvents()
    system["scheme"] = "light"
    QGuiApplication.styleHints().colorSchemeChanged.emit(Qt.ColorScheme.Light)
    QApplication.processEvents()
    assert heard == []


def test_the_default_theme_box_names_auto_while_it_is_saved(
        isolated_home, qtbot, main_module, monkeypatch):
    """The box named the mode Auto gave, so the next Save filed that mode and
    Auto was gone."""
    monkeypatch.setattr(main_module, "_system_color_scheme", lambda: "light", raising=False)
    _write_settings(isolated_home, preferences={"theme": "auto"})
    win = _launch(main_module, qtbot)
    try:
        panel = _panel(win)
        assert panel.theme_combo.currentText() == "Auto (follow system)"
        panel.tooltips_check.setChecked(not panel.tooltips_check.isChecked())
        _press_save(panel, monkeypatch)
        assert win.settings_manager.get("preferences.theme") == "auto"
        win._on_theme_button_clicked()
        QApplication.processEvents()
        assert panel.theme_combo.currentText() != "Auto (follow system)"
    finally:
        win.close()


# ═════════════════════════════════════════════════════════════════════════
# 5. Auto-load last session
# ═════════════════════════════════════════════════════════════════════════

SESSION_SLOTS = [((10, 200, 30), 70), ((200, 10, 30), 30), ((0, 0, 250), 20)]


def _record_session(home: Path, name: str = "last") -> Path:
    """A session saved in the Sessions tab, at the top of Recent Sessions."""
    from utils.session_manager import SessionManager
    sm = SessionManager(str(home / ".color_mixer" / "sessions"))
    path = sm.generate_session_filename(name)
    assert sm.save_session(path, [{"index": i, "color": list(c), "weight": w}
                                  for i, (c, w) in enumerate(SESSION_SLOTS)], name=name)
    return Path(path)


def _slot_state(win):
    return [(tuple(s.get_color()), s.get_weight()) for s in win.slots if s.get_weight() > 0]


@pytest.fixture
def no_boxes(monkeypatch):
    """Answer every question No and record every box the app shows."""
    shown: list[str] = []

    def record(answer):
        def box(parent, title, *args, **kwargs):
            shown.append(title)
            return answer
        return staticmethod(box)

    monkeypatch.setattr(QMessageBox, "question", record(QMessageBox.StandardButton.No))
    monkeypatch.setattr(QMessageBox, "information", record(0))
    monkeypatch.setattr(QMessageBox, "warning", record(0))
    return shown


def test_auto_load_loads_the_last_session_at_startup(isolated_home, qtbot, main_module, no_boxes):
    _record_session(isolated_home, "older")
    _record_session(isolated_home, "last")
    _write_settings(isolated_home, preferences={"auto_load_last_session": True})
    win = _launch(main_module, qtbot, wait_ms=800)
    try:
        assert _slot_state(win) == SESSION_SLOTS
        assert no_boxes == [], "the startup load asked or announced something"
    finally:
        win.close()


def test_auto_load_off_loads_nothing(isolated_home, qtbot, main_module, no_boxes):
    """A guard, true before the change too: off is the default, and loads nothing."""
    _record_session(isolated_home)
    win = _launch(main_module, qtbot, wait_ms=800)
    try:
        assert win.settings_manager.get("preferences.auto_load_last_session") is False
        assert _slot_state(win) != SESSION_SLOTS
    finally:
        win.close()


def test_the_recovery_offer_wins_over_auto_load(isolated_home, qtbot, main_module, no_boxes):
    """A run that did not close leaves the recovery flag. The next launch
    offers recovery, and does not auto-load as well, whatever the answer
    (here No)."""
    _record_session(isolated_home)
    _write_settings(isolated_home, preferences={"auto_load_last_session": True})
    first = _launch(main_module, qtbot, wait_ms=800)
    first.session_manager._autosave()          # what the 60 s timer does
    # The process dies here: no closeEvent, so the recovery flag stays.
    first_state = _slot_state(first)
    second = _launch(main_module, qtbot, wait_ms=800)
    try:
        assert "Recover Previous Session?" in no_boxes
        assert _slot_state(second) != SESSION_SLOTS
    finally:
        second.close()
        first.close()
    assert first_state == SESSION_SLOTS        # the first launch did auto-load


# ═════════════════════════════════════════════════════════════════════════
# 6. Default Export Format
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("fmt,initial", [("gpl", "GIMP Palette (*.gpl)"),
                                         ("json", "JSON (*.json)"),
                                         ("ase", None)])
def test_export_palette_opens_on_the_default_format(fmt, initial, app_window, dialogs):
    """ASE is the dialog's first format already, so it is not passed."""
    calls, _ = dialogs
    app_window.settings_manager.set("preferences.default_export_format", fmt)
    app_window.export_palette()
    assert len(calls) == 1
    args = calls[0]
    assert args[1] == "Export Palette"
    if initial is None:
        assert len(args) == 4
    else:
        assert args[4] == initial and initial in args[3].split(";;")


def test_save_color_swatch_opens_on_jpeg_and_writes_one(app_window, dialogs, tmp_path):
    from PIL import Image
    calls, state = dialogs
    app_window.settings_manager.set("preferences.default_export_format", "jpeg")
    state["answer"] = (str(tmp_path / "swatch"), "JPEG Files (*.jpg *.jpeg)")
    app_window.save_color_swatch()
    assert calls[0][1] == "Save Color Swatch"
    assert calls[0][4] == "JPEG Files (*.jpg *.jpeg)"
    out = tmp_path / "swatch.jpg"
    assert out.exists(), list(tmp_path.iterdir())
    with Image.open(out) as img:
        assert img.format == "JPEG"


@pytest.mark.parametrize("fmt", ["png", "json", "ase", "gpl"])
def test_the_swatch_dialog_is_unchanged_for_other_formats(fmt, app_window, dialogs):
    """A guard: PNG is the swatch dialog's first type, and JSON, ASE and GPL
    are not image types, so the call is the one the app always made."""
    calls, _ = dialogs
    app_window.settings_manager.set("preferences.default_export_format", fmt)
    app_window.save_color_swatch()
    assert len(calls[0]) == 4


@pytest.mark.parametrize("fmt", ["png", "jpeg"])
def test_the_palette_dialog_is_unchanged_for_image_formats(fmt, app_window, dialogs):
    calls, _ = dialogs
    app_window.settings_manager.set("preferences.default_export_format", fmt)
    app_window.export_palette()
    assert len(calls[0]) == 4
