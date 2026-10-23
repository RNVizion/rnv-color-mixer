"""STATE FILES ARE WRITTEN ATOMICALLY (#83 A, 2026-10-22).

The same file in all five RNV desktop applications.

THE FAULT IT KEEPS AWAY. A settings, session, history or preset file written
with open(path, "w") is truncated before its new content arrives. A crash or
a full disk in between leaves an empty or half-written file, and the next
start reads it as corrupt. utils/atomic_write.py writes a temporary file of its own
beside the target, flushes and fsyncs it, and os.replace()s it in, so a
reader sees the old file or the new one, never a mixture.

WHAT IT HOLDS.
  1. The helper's own behavior: a value json cannot serialize is refused
     before any file is touched; a failure while writing leaves the old file
     as it was and no .tmp beside it; two writers on one file both finish
     and leave a whole file, also when a replace is refused for a moment,
     as Windows does while another replace onto the file is finishing; it
     creates no directory.
  2. Every state writer named for this application in STATE_WRITERS calls the
     helper, and holds no open() in a write mode, no Path.write_text() or
     write_bytes(), and no json.dump() to a file. The list is the writers
     found on 2026-10-22; it is read by the application's name in
     brand_map.json, and it is not empty.
  3. Each named writer exists, so a rename does not leave the list stale.

WHAT IT LEAVES ALONE. Exports the user asks for (PNG, CSS, JSON the user
names, batch output) are not state and keep their own writers. QSettings
(the palette manager and the text transformer) is atomic by itself.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: (module, qualified function name) of every writer of a file the application
#: keeps for itself, by application name.
STATE_WRITERS: dict[str, tuple[tuple[str, str], ...]] = {
    "RNV Color Picker": (
        ("utils/settings_manager.py", "SettingsManager.save_settings"),
        ("utils/session_manager.py", "SessionManager.save_session"),
        ("utils/session_manager.py", "SessionManager._add_to_recent"),
        ("utils/session_manager.py", "SessionManager._remove_from_recent"),
        ("core/color_history.py", "ColorHistoryManager.save_history"),
        ("utils/async_file_ops.py", "FileWriterThread.run"),
    ),
    "RNV Color Mixer": (
        ("core/color_history.py", "ColorHistory.save"),
        ("utils/async_file_ops.py", "FileWriterThread.run"),
        ("core/preset_palettes.py", "PresetPalettes.save_custom_presets"),
        ("utils/settings_manager.py", "SettingsManager.save_settings"),
        ("utils/session_manager.py", "SessionManager.save_session"),
        ("utils/session_manager.py", "SessionManager._add_to_recent"),
        ("utils/session_manager.py", "SessionManager._remove_from_recent"),
        ("utils/session_manager.py", "SessionManager.rename_session"),
    ),
    "RNV Icon Builder": (
        ("core/session_manager.py", "SessionManager.save_session"),
        ("core/session_manager.py", "SessionManager._set_recovery_flag"),
        ("utils/async_file_ops.py", "FileWriterThread._write_json"),
        ("utils/async_file_ops.py", "FileWriterThread._write_text"),
        ("utils/async_file_ops.py", "FileWriterThread._write_binary"),
        ("core/export_history.py", "ExportHistory._save_history"),
        ("core/recent_files.py", "RecentFilesManager._save"),
        ("core/preset_manager.py", "PresetManager._save_presets"),
        ("core/project_manager.py", "ProjectManager.save_project"),
    ),
    "RNV Color Palette Manager": (
        ("utils/session_manager.py", "SessionManager.save_session"),
        ("utils/session_manager.py", "SessionManager._set_recovery_flag"),
        ("utils/export_history.py", "ExportHistory._save"),
    ),
    "RNV Text Transformer": (
        ("core/preset_manager.py", "PresetManager.save_presets._do_save"),
    ),
}

HELPERS = {"atomic_write_json", "atomic_write_text", "atomic_write_bytes"}
WRITE_MODES = ("w", "a", "x")


def _app_name() -> str:
    return json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["app"]


def _functions(tree: ast.Module) -> dict[str, ast.AST]:
    """Qualified name -> def node, for every function in the module, nested ones too."""
    out: dict[str, ast.AST] = {}

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                if not isinstance(child, ast.ClassDef):
                    out[name] = child
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(tree, "")
    return out


def _call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def _is_write_open(node: ast.Call) -> bool:
    if _call_name(node) != "open":
        return False
    mode = None
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        mode = node.args[1].value
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = kw.value.value
    return isinstance(mode, str) and any(m in mode for m in WRITE_MODES)


# ---------------------------------------------------------------- 1. the helper

@pytest.fixture
def aw():
    from utils import atomic_write
    return atomic_write


def test_helper_writes_json_the_reader_can_load(aw, tmp_path):
    target = tmp_path / "state.json"
    aw.atomic_write_json(target, {"a": [1, 2], "s": "é"}, indent=2, ensure_ascii=False)
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": [1, 2], "s": "é"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_helper_refuses_an_unserializable_value_before_touching_the_file(aw, tmp_path):
    target = tmp_path / "state.json"
    target.write_text('{"old": true}', encoding="utf-8")
    with pytest.raises(TypeError):
        aw.atomic_write_json(target, {"when": object()})
    assert target.read_text(encoding="utf-8") == '{"old": true}'
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_helper_leaves_the_old_file_and_no_tmp_when_the_write_fails(aw, tmp_path, monkeypatch):
    target = tmp_path / "state.json"
    target.write_text('{"old": true}', encoding="utf-8")

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        aw.atomic_write_text(target, '{"new": true}')
    assert target.read_text(encoding="utf-8") == '{"old": true}'
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_helper_leaves_the_old_file_when_the_replace_fails(aw, tmp_path, monkeypatch):
    target = tmp_path / "state.json"
    target.write_text("old", encoding="utf-8")

    def fail(*args, **kwargs):
        raise PermissionError("in use")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(PermissionError):
        aw.atomic_write_bytes(target, b"new")
    assert target.read_text(encoding="utf-8") == "old"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_two_writers_on_one_file_both_finish_and_leave_a_whole_file(aw, tmp_path):
    """The mixer keeps a retired history writer running beside the current one:
    two writers, as there. On Windows this meets the refused replace for real;
    the test below makes it happen everywhere, with four."""
    import threading
    target = tmp_path / "state.json"
    payloads = [{"writer": i, "rows": list(range(200))} for i in range(2)]
    errors: list[BaseException] = []

    def write(i: int) -> None:
        try:
            for _ in range(50):
                aw.atomic_write_json(target, payloads[i])
        except BaseException as e:  # noqa: BLE001 - collected and asserted below
            errors.append(e)

    threads = [threading.Thread(target=write, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    assert json.loads(target.read_text(encoding="utf-8")) in payloads
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_a_replace_refused_for_a_moment_is_tried_again(aw, tmp_path, monkeypatch):
    """Windows refuses a replace onto a file while another replace onto it is
    finishing ("Access is denied"). Seen on Chris's machine, 2026-10-23, in the
    test above; Linux never does it, so here it is made to happen: a replace
    onto a file another replace is still busy with raises PermissionError."""
    import threading
    import time as _time

    real_replace = os.replace
    busy: set[str] = set()
    lock = threading.Lock()
    refused = []

    def windows_replace(src, dst):
        key = os.fspath(dst)
        with lock:
            if key in busy:
                refused.append(key)
                raise PermissionError(13, "Access is denied")
            busy.add(key)
        try:
            _time.sleep(0.001)
            real_replace(src, dst)
        finally:
            with lock:
                busy.discard(key)

    monkeypatch.setattr(os, "replace", windows_replace)
    target = tmp_path / "state.json"
    payloads = [{"writer": i, "rows": list(range(50))} for i in range(4)]
    errors: list[BaseException] = []

    def write(i: int) -> None:
        try:
            for _ in range(25):
                aw.atomic_write_json(target, payloads[i])
        except BaseException as e:  # noqa: BLE001 - collected and asserted below
            errors.append(e)

    threads = [threading.Thread(target=write, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert refused, "the writers never met, so this proved nothing"
    assert not errors, errors
    assert json.loads(target.read_text(encoding="utf-8")) in payloads
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_helper_creates_no_directory(aw, tmp_path):
    target = tmp_path / "no" / "such" / "dir" / "state.json"
    with pytest.raises(FileNotFoundError):
        aw.atomic_write_text(target, "x")
    assert not (tmp_path / "no").exists()


# ------------------------------------------------------- 2 and 3. the writers

def _writers() -> tuple[tuple[str, str], ...]:
    name = _app_name()
    assert name in STATE_WRITERS, f"brand_map.json names {name!r}; STATE_WRITERS has no entry for it"
    return STATE_WRITERS[name]


def test_this_application_has_state_writers_listed():
    assert _writers(), "the list of state writers is empty"


def test_every_listed_state_writer_exists_and_calls_the_helper():
    failures = []
    for module, qualname in _writers():
        path = ROOT / module
        if not path.exists():
            failures.append(f"{module}: file not found")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=module)
        fn = _functions(tree).get(qualname)
        if fn is None:
            failures.append(f"{module}: {qualname} not found")
            continue
        calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)]
        names = {_call_name(c) for c in calls}
        if not names & HELPERS:
            failures.append(f"{module}: {qualname} does not call utils.atomic_write")
        for c in calls:
            if _is_write_open(c):
                failures.append(f"{module}: {qualname} opens a file for writing (line {c.lineno})")
            if _call_name(c) in ("write_text", "write_bytes"):
                failures.append(f"{module}: {qualname} calls .{_call_name(c)}() (line {c.lineno})")
            if _call_name(c) == "dump" and isinstance(c.func, ast.Attribute) \
                    and isinstance(c.func.value, ast.Name) and c.func.value.id == "json":
                failures.append(f"{module}: {qualname} streams json.dump to a file (line {c.lineno})")
    assert not failures, "\n".join(failures)
