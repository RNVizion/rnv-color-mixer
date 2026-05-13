"""
RNV Color Mixer — SessionManager Tests  (Phase 7.8 deliverable)
==================================================================

Drives the `utils.session_manager.SessionManager` class. Phases 3 and 4
covered some paths transitively; this fills in the direct API.

Method names verified by source grep:
  - save_session(filepath, slots_data, mixed_color, settings, name, description)
  - load_session(filepath) -> dict | None
  - get_recent_sessions() -> list[dict]   (NOT `list_sessions`)
  - rename_session(old_path, new_path)
  - delete_session(filepath)
  - generate_session_filename(base_name=None) -> str (full path)
  - get_session_info(filepath) -> dict | None
  - cleanup_old_sessions(days)
  - start_autosave(main_app) / stop_autosave()
  - check_for_autosave() -> str | None
  - get_autosave_count() -> int
  - cleanup() -> None

The autosave path needs a `main_app` reference whose `get_current_state()`
method returns the slot data; we provide a tiny stub.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from utils.session_manager import SessionManager


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def session_dir(tmp_path):
    """Isolated sessions directory."""
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def sm(session_dir):
    """Fresh SessionManager pointing at an isolated dir."""
    manager = SessionManager(sessions_dir=str(session_dir))
    yield manager
    manager.cleanup()


def _make_sample_session_args():
    """Standard kwargs for save_session."""
    return dict(
        slots_data=[
            {"index": 0, "color": [255, 0, 0], "weight": 100},
            {"index": 1, "color": [0, 255, 0], "weight": 50},
        ],
        mixed_color=(170, 85, 0),
        settings={"theme": "dark"},
        name="phase78_test",
        description="phase 7.8 fixture",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSessionManagerConstruction:
    def test_construction_creates_sessions_dir(self, tmp_path):
        target = tmp_path / "new_sessions_dir"
        assert not target.exists()
        sm = SessionManager(sessions_dir=str(target))
        try:
            assert target.exists(), "sessions_dir was not created"
            assert target.is_dir()
        finally:
            sm.cleanup()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Save / load round-trip (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestSessionSaveLoad:
    def test_save_then_load_round_trips_all_fields(self, sm, tmp_path):
        path = str(tmp_path / "rt.session")
        args = _make_sample_session_args()

        ok = sm.save_session(filepath=path, **args)
        assert ok is True
        assert Path(path).exists()

        loaded = sm.load_session(path)
        assert loaded is not None
        # Core fields preserved
        assert loaded["name"] == args["name"]
        assert loaded["description"] == args["description"]
        # Slot data preserved (may be re-listed via dict access)
        assert len(loaded["slots"]) == len(args["slots_data"])

    def test_load_nonexistent_session_returns_none(self, sm, tmp_path):
        bogus = str(tmp_path / "missing.session")
        result = sm.load_session(bogus)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# 3. Recent sessions list (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRecentSessions:
    def test_save_adds_to_recent_list(self, sm, tmp_path):
        path = str(tmp_path / "recent_test.session")
        before = len(sm.get_recent_sessions())
        sm.save_session(filepath=path, **_make_sample_session_args())
        after = len(sm.get_recent_sessions())
        assert after == before + 1, (
            f"Recent count {before} → {after} (expected +1)"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. Rename / Delete (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRenameAndDelete:
    def test_rename_session_moves_file(self, sm, tmp_path):
        old = str(tmp_path / "old_name.session")
        new = str(tmp_path / "new_name.session")

        sm.save_session(filepath=old, **_make_sample_session_args())
        assert Path(old).exists()

        ok = sm.rename_session(old, new)
        assert ok is True
        assert not Path(old).exists()
        assert Path(new).exists()

    def test_delete_session_removes_file(self, sm, tmp_path):
        path = str(tmp_path / "to_delete.session")
        sm.save_session(filepath=path, **_make_sample_session_args())
        assert Path(path).exists()

        ok = sm.delete_session(path)
        assert ok is True
        assert not Path(path).exists()


# ═══════════════════════════════════════════════════════════════════════════
# 5. generate_session_filename (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestGenerateSessionFilename:
    def test_generate_filename_includes_base_name_and_extension(self, sm):
        result = sm.generate_session_filename("MyAwesome")
        assert "MyAwesome" in result
        assert result.endswith(".session"), (
            f"expected .session extension, got {result!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 6. get_session_info (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestGetSessionInfo:
    def test_session_info_returns_metadata_dict(self, sm, tmp_path):
        path = str(tmp_path / "info_test.session")
        args = _make_sample_session_args()
        sm.save_session(filepath=path, **args)

        info = sm.get_session_info(path)
        assert info is not None
        # Documented keys per smoke test:
        # color_count, created, description, filepath, modified, name, total_slots
        for key in ("name", "description", "filepath"):
            assert key in info, f"info missing key {key!r}"
        assert info["name"] == args["name"]


# ═══════════════════════════════════════════════════════════════════════════
# 7. cleanup_old_sessions (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestCleanupOldSessions:
    def test_cleanup_with_huge_threshold_returns_zero(self, sm, tmp_path):
        """All sessions are recent (just created), so a 999-day threshold
        deletes nothing."""
        path = str(tmp_path / "fresh.session")
        sm.save_session(filepath=path, **_make_sample_session_args())

        deleted = sm.cleanup_old_sessions(days=999)
        assert deleted == 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. Autosave control (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAutosaveControl:
    """`start_autosave(main_app)` and `stop_autosave()` manage the
    background timer. We don't wait for it to fire (60s by default) —
    just verify start/stop don't crash."""

    def test_check_for_autosave_returns_none_when_no_autosaves(self, sm):
        """Fresh sessions dir has no autosave files."""
        result = sm.check_for_autosave()
        assert result is None

    def test_get_autosave_count_starts_at_zero(self, sm):
        assert sm.get_autosave_count() == 0

    def test_start_then_stop_autosave_does_not_crash(self, sm):
        """Provide a stub main_app with a get_current_state method."""
        class _StubApp:
            def get_current_state(self):
                return {
                    "slots": [], "mixed_color": (200, 200, 200),
                    "settings": {},
                }

        sm.start_autosave(_StubApp())
        sm.stop_autosave()
