"""
RNV Color Mixer — /tests/ Pytest Configuration  (Phase 1 deliverable)
=====================================================================

This is the conftest.py for the /tests/ directory. It provides bootstrap
and fixtures for all NEW test files added in Phases 1–6.

The locked root-level file `test_rnv_color_mixer.py` has its OWN equivalent
bootstrap inline; this conftest does NOT touch that file and is loaded in
addition to (not in place of) its inline setup.

What this conftest provides
----------------------------
1. Headless Qt platform setup (offscreen QPA)
2. QApplication singleton creation
3. sys.path setup that handles both flat and subdirectory project layouts
4. Capture of pristine ColorHistory.__init__ / load / save_async references
   BEFORE the locked file's module-level monkey-patches fire, so Phase 3
   threading tests can opt back into real threading via the
   `real_color_history` fixture.
5. Idempotent application of the same no-op ColorHistory patches the locked
   file applies, so /tests/ files always see safe defaults regardless of
   pytest's collection order.

Pytest import-order guarantee
------------------------------
Pytest loads conftest.py files during session configuration, BEFORE
importing any test module. The pristine-method capture in section 5
therefore always runs while ColorHistory is still in its original state.

LOCKED-FILE INVARIANT
---------------------
This file MUST NOT modify, rename, or import-by-side-effect the locked
test_rnv_color_mixer.py at the project root. SHA-256 of the locked file
is verified at every phase boundary.
"""

from __future__ import annotations

import os
import sys
import types
import tempfile
import importlib.util
from pathlib import Path

# ═════════════════════════════════════════════════════════════════════════
# 1. Headless Qt platform — must be set before any Qt module is imported
# ═════════════════════════════════════════════════════════════════════════
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ═════════════════════════════════════════════════════════════════════════
# 2. Project-root resolution — handles flat AND subdirectory layouts
# ═════════════════════════════════════════════════════════════════════════
_THIS_DIR = Path(__file__).resolve().parent              # …/RNV_Color_Mixer/tests
_DEFAULT_ROOT_HINT = _THIS_DIR.parent                    # …/RNV_Color_Mixer


def _looks_like_project_root(p: Path) -> bool:
    """Recognise the project root by entry-point script, subdir layout,
    or known top-level modules (covers all three deployment scenarios)."""
    if (p / "RNV_Color_Mixer.py").exists():
        return True
    if (p / "core").is_dir() and (p / "utils").is_dir():
        return True
    if (p / "color_math.py").exists() and (p / "session_manager.py").exists():
        return True
    return False


_FLAT: str | None = None
for _candidate in [_DEFAULT_ROOT_HINT,
                   _DEFAULT_ROOT_HINT.parent,
                   Path("/mnt/project"),
                   Path.home() / "RNV_Color_Mixer"]:
    if _looks_like_project_root(_candidate):
        _FLAT = str(_candidate)
        break

if _FLAT is None:
    raise RuntimeError(
        "tests/conftest.py: cannot locate the RNV_Color_Mixer project root.\n"
        f"Hint: this file lives at {Path(__file__).resolve()}; expected the "
        "parent directory to contain RNV_Color_Mixer.py or a core/ + utils/ "
        "layout."
    )


# ═════════════════════════════════════════════════════════════════════════
# 3. sys.path + virtual packages (mirrors the locked file's logic exactly)
# ═════════════════════════════════════════════════════════════════════════
_SUBDIR_LAYOUT = os.path.isdir(os.path.join(_FLAT, "core"))

if _SUBDIR_LAYOUT:
    # Subdirectory layout: core/, utils/, ui/
    for _path in (_FLAT,
                  os.path.join(_FLAT, "core"),
                  os.path.join(_FLAT, "utils"),
                  os.path.join(_FLAT, "ui")):
        if _path not in sys.path:
            sys.path.insert(0, _path)
else:
    # Flat layout: create virtual packages pointing at the single directory
    if _FLAT not in sys.path:
        sys.path.insert(0, _FLAT)
    for _pkg in ("core", "utils", "ui"):
        if _pkg in sys.modules:
            continue
        _m = types.ModuleType(_pkg)
        _m.__path__ = [_FLAT]
        _m.__package__ = _pkg
        sys.modules[_pkg] = _m

    _LOAD = {
        "utils": ["logger", "config", "error_handler", "settings_manager",
                  "session_manager", "signal_manager", "file_utils",
                  "clipboard", "pixmap_cache", "async_file_ops",
                  "dialog_helper"],
        "core":  ["color_math", "color_history", "color_harmony",
                  "palette_formats", "preset_palettes", "image_handler"],
    }
    for _pkg, _names in _LOAD.items():
        for _name in _names:
            _full = f"{_pkg}.{_name}"
            if _full in sys.modules:
                continue
            _spec = importlib.util.spec_from_file_location(
                _full, os.path.join(_FLAT, f"{_name}.py"))
            if not _spec:
                continue
            _mod = importlib.util.module_from_spec(_spec)
            _mod.__package__ = _pkg
            sys.modules[_full] = _mod
            sys.modules[_name] = _mod
            try:
                _spec.loader.exec_module(_mod)
            except Exception:
                pass  # Qt-heavy modules may fail in headless mode — skip silently


# ═════════════════════════════════════════════════════════════════════════
# 4. QApplication policy — DELIBERATELY do NOT create one here
# ═════════════════════════════════════════════════════════════════════════
# The locked test_rnv_color_mixer.py creates the session's QApplication
# during its own bootstrap (line 23). That bootstrap has a known limitation:
# the local name `_qapp` is only assigned when `QApplication.instance()`
# returns None. If we created the QApplication first here, the locked file
# would find an existing instance, skip its `_qapp` assignment, and crash
# at line 1242 where `_qapp` is referenced inside an `@unittest.skipUnless`
# decorator that runs at import (collection) time.
#
# Because the locked file is LOCKED, we cannot fix the bug there. We avoid
# triggering it by letting the locked file create the QApplication itself.
#
# /tests/ files that need Qt should request the standard pytest-qt `qtbot`
# fixture, which creates a QApplication on demand and reuses an existing
# one if present (e.g., the one the locked file created during collection).
#
# ColorHistory and its transitive imports (color_math, etc.) do not require
# a live QApplication at import time, so section 5 below is safe.


# ═════════════════════════════════════════════════════════════════════════
# 5. Capture pristine ColorHistory references — BEFORE the locked file's
#    monkey-patches replace them. Used by Phase 3's `real_color_history`.
# ═════════════════════════════════════════════════════════════════════════
import pytest  # noqa: E402

try:
    from core.color_history import ColorHistory as _ColorHistory  # noqa: E402
    PRISTINE_CH_INIT       = _ColorHistory.__init__
    PRISTINE_CH_LOAD       = _ColorHistory.load
    PRISTINE_CH_SAVE_ASYNC = _ColorHistory.save_async
    _CH_AVAILABLE = True
except Exception:
    _ColorHistory = None
    PRISTINE_CH_INIT = PRISTINE_CH_LOAD = PRISTINE_CH_SAVE_ASYNC = None
    _CH_AVAILABLE = False


# ═════════════════════════════════════════════════════════════════════════
# 6. Apply same safe no-op patches the locked file applies — idempotent,
#    so that /tests/ files see safe defaults regardless of pytest's
#    collection order. The locked file may then re-apply equivalent
#    patches; both produce identical semantics.
# ═════════════════════════════════════════════════════════════════════════
_HIST_TMP_DIR = tempfile.mkdtemp(prefix="rnv_tests_history_")
_HIST_SAFE_FILE = os.path.join(_HIST_TMP_DIR, "tests_history.json")

if _CH_AVAILABLE:
    def _tests_safe_ch_init(self, max_entries=20):
        self.max_entries  = max_entries
        self.entries      = []
        self.history_file = _HIST_SAFE_FILE
        self._save_thread = None

    _ColorHistory.load       = lambda self: True
    _ColorHistory.save_async = lambda self, on_complete=None: None
    _ColorHistory.__init__   = _tests_safe_ch_init


# ═════════════════════════════════════════════════════════════════════════
# 7. Fixtures
# ═════════════════════════════════════════════════════════════════════════

@pytest.fixture
def real_color_history():
    """
    Phase 3 fixture: temporarily restore the original (unpatched) ColorHistory
    methods so threading tests can exercise the real FileWriterThread,
    save_async file I/O, and the cleanup() teardown path.

    Usage (Phase 3+):
        def test_save_async_actually_writes(real_color_history, tmp_path):
            ch = real_color_history()
            ch.history_file = str(tmp_path / "h.json")
            ch.add_color((255, 0, 0))
            ch.save_async()
            ...
            ch.cleanup()

    On teardown, the no-op patches are restored so subsequent tests see
    safe defaults again.
    """
    if not _CH_AVAILABLE:
        pytest.skip("core.color_history not importable in this environment")

    cls = _ColorHistory

    # Save whatever patches are currently installed (the no-ops from §6 above)
    saved_init       = cls.__init__
    saved_load       = cls.load
    saved_save_async = cls.save_async

    # Swap in the pristine originals captured at conftest import time
    cls.__init__    = PRISTINE_CH_INIT
    cls.load        = PRISTINE_CH_LOAD
    cls.save_async  = PRISTINE_CH_SAVE_ASYNC

    try:
        yield cls
    finally:
        # Always restore the no-op patches, even if the test failed
        cls.__init__    = saved_init
        cls.load        = saved_load
        cls.save_async  = saved_save_async


@pytest.fixture(scope="session")
def project_root() -> str:
    """Absolute path to the resolved project root.
    Useful for tests that construct paths to source files or fixture data."""
    return _FLAT


@pytest.fixture(scope="session")
def is_subdir_layout() -> bool:
    """True if the project uses the core/ utils/ ui/ subdirectory layout,
    False if it's flat. Useful for layout-aware path construction."""
    return _SUBDIR_LAYOUT


@pytest.fixture(scope="session")
def snapshots_dir() -> Path:
    """Path to the root-level /snapshots/ directory (Phase 2 reference data)."""
    return Path(_FLAT) / "snapshots"


@pytest.fixture(scope="session")
def main_module():
    """Load RNV_Color_Mixer.py as a uniquely-named module.

    Why: in the flat testing layout, the project directory is named
    `RNV_Color_Mixer/` AND contains a file named `RNV_Color_Mixer.py`. With
    a top-level `__init__.py` present, Python resolves
    `from RNV_Color_Mixer import ColorMixerApp` against the (mostly empty)
    package, never the file. Loading by absolute path under a different
    sys.modules key bypasses the collision.

    Phase 4 (app-level integration tests) is the first phase that imports
    ColorMixerApp; earlier phases only import from core/ and utils/, which
    are unaffected.
    """
    if "_rnv_main_module" in sys.modules:
        return sys.modules["_rnv_main_module"]

    main_path = Path(_FLAT) / "RNV_Color_Mixer.py"
    if not main_path.exists():
        pytest.skip(f"RNV_Color_Mixer.py not found at {main_path}")

    spec = importlib.util.spec_from_file_location(
        "_rnv_main_module", str(main_path)
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_rnv_main_module"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────
# App-level fixtures (used by Phase 4+ integration tests across multiple
# files: test_app_integration.py, test_package_d_panel.py, etc.)
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def isolated_home(monkeypatch, tmp_path):
    """Redirect every plausible 'user data' path to a per-test tmp dir.

    Covers:
      • Linux: $HOME, $XDG_CONFIG_HOME → ~/.config/ColorMixer
      • Windows: %USERPROFILE%, %APPDATA% → AppData/Roaming/ColorMixer
      • macOS: $HOME → ~/Library/Application Support/ColorMixer
      • ColorHistory's ~/.color_mixer_history.json
      • SessionManager's ~/.color_mixer/sessions/
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData" / "Roaming"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    return tmp_path


@pytest.fixture
def app_window(isolated_home, qtbot, main_module):
    """Fresh ColorMixerApp instance, isolated and auto-cleaned.

    Yields the live window. On teardown we trigger the real `closeEvent`
    so each test exercises the same shutdown path the user does.
    """
    win = main_module.ColorMixerApp()
    qtbot.addWidget(win)  # registers for Qt-side cleanup
    yield win
    # Drive the real shutdown path (this is what the regression guards)
    try:
        win.close()
    except Exception:
        pass


# ═════════════════════════════════════════════════════════════════════════
# 8. Pytest plugin hooks
# ═════════════════════════════════════════════════════════════════════════

def pytest_addoption(parser):
    """Register custom CLI flags. Must live in a conftest.py to be honoured."""
    parser.addoption(
        "--rnv-update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Regenerate /snapshots/ reference files instead of comparing. "
            "Use ONLY when an exporter or stylesheet has been intentionally "
            "changed and the new output is correct. Equivalent env var: "
            "RNV_UPDATE_SNAPSHOTS=1"
        ),
    )
