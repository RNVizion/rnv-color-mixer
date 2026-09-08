#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: stop the Linux CI abort at its cause.

    python up.py             # apply, then verify
    python up.py --check     # rehearse, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT IS ACTUALLY WRONG. Linux CI has aborted three times -- SIGABRT, exit
134, core dumped -- at three different tests:

    2026-08-31  tests/test_lifecycle_handlers.py   TestAsyncFileOpsFormatPaths
    (earlier)   tests/test_error_recovery_paths.py TestAsyncFileOpsErrorPaths
    2026-09-07  tests/test_threading.py            TestColorHistoryThreading

Each looked like a new flake and two were handled by deselecting the class
on Linux, recorded in KNOWN_ISSUES.md as "platform/environment workarounds,
not code defects". They are one code defect with SEVENTEEN instances, and
deselecting moved the next abort to the next member of the family.

THE MECHANISM, MEASURED. FileWriterThread and FileReaderThread each declare

    finished = pyqtSignal(bool, str)

which SHADOWS QThread.finished(). The custom signal is emitted from INSIDE
run(). Asking the thread directly at the moment these tests return:

    custom `finished` shadows QThread.finished : True
    QThread still running after waitSignal      : True

So seventeen tests wait for the work, then return, leaving a RUNNING QThread
with no Python reference. Nothing collects it immediately -- prompt
collection is safe, and was tested. It is destroyed at whatever LATER
allocation happens to trigger a collection, which is exactly why the abort
lands inside a later test's call frame with no frame of its own:

    Current thread (most recent call first):
      File ".../_pytest/python.py", line 167 in pytest_pyfunc_call

Reproduced here on a two-core container under `coverage run`, the same shape
as the runner: one abort in three full passes, at
test_file_writer_thread_emits_failure_on_invalid_path -- a different member
of the same seventeen, which is the point.

THE APPLICATION DOES NOT HAVE THIS BUG. core/color_history.py holds
self._save_thread and checks isRunning() before releasing it;
AsyncFileManager keeps _active_threads and filters on isRunning(). Every
release path in the application re-checks. Only the tests let go. **No
application file is touched by this script.**

WHAT THIS DOES. Adds an `adopt` fixture to tests/conftest.py that owns any
thread a test starts and waits for it in teardown, and routes 17 test
site(s) through it. A fixture rather than a wait() at the end of each test
because TEARDOWN STILL RUNS WHEN AN ASSERTION FAILS -- otherwise a failing
assertion would abandon the thread and the abort would bury the real
failure.

WHAT IT DOES NOT DO. It does not remove the two existing CI deselects.
Those tests are in the seventeen and should come back, but restoring them
is a separate decision with its own verification, and this round is the
repair.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "tests/conftest.py"
SENTINEL = "RNV-THREAD-OWNERSHIP"
GUARD = "tests/test_thread_ownership.py"
DESCRIPTION = "stop the tests abandoning running QThreads"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-THREAD-OWNERSHIP-GUARD -- a test that starts a thread finishes it.

Installed 2026-09-07, after Linux CI aborted for the third time.

WHAT WAS ACTUALLY WRONG. Three aborts, at three different tests, over a
week -- SIGABRT, exit 134, core dumped:

    tests/test_error_recovery_paths.py   TestAsyncFileOpsErrorPaths
    tests/test_lifecycle_handlers.py     TestAsyncFileOpsFormatPaths
    tests/test_threading.py              TestColorHistoryThreading

Each looked like a separate flake. Two were handled by deselecting the class
on Linux and recording it in KNOWN_ISSUES.md as a "platform/environment
workaround, not a code defect". They were one code defect with seventeen
instances, and each deselect moved the next abort onto the next member of
the family.

THE MECHANISM. FileWriterThread and FileReaderThread each declare

    finished = pyqtSignal(bool, str)

which SHADOWS QThread.finished(). The custom signal is emitted from INSIDE
run(), so waiting on it says the WORK finished -- not that the THREAD
stopped. Seventeen tests waited on it and returned, leaving a running
QThread with no Python reference behind.

Prompt collection turns out to be harmless, and was tested. The damage comes
from a DEFERRED collection: the object is destroyed at whatever later
allocation happens to trigger one, which is why the abort appears inside a
later test's call frame with no frame of its own.

THE APPLICATION IS NOT AFFECTED, and this guard checks that too.
core/color_history.py holds self._save_thread and checks isRunning() before
releasing it; AsyncFileManager keeps _active_threads and filters on
isRunning(). Every release path re-checks. That is the property worth
keeping, so it is asserted rather than assumed.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The two QThread subclasses whose `finished` shadows QThread's.
THREADS = {'FileWriterThread', 'FileReaderThread'}


def _functions(text, tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node, (ast.get_source_segment(text, node) or '')


def _test_files():
    return sorted(p for p in (ROOT / 'tests').glob('*.py'))


def test_no_test_abandons_a_running_thread():
    """The whole point.

    A test may own its thread three ways: adopt() it, wait() for it, or poll
    isRunning() until it stops. Anything else returns while the thread is
    alive, and the interpreter dies later somewhere that looks unrelated.
    """
    stranded = []
    for path in _test_files():
        text = path.read_text(encoding='utf-8')
        tree = ast.parse(text)
        for fn, fnsrc in _functions(text, tree):
            for node in ast.walk(fn):
                if not (isinstance(node, ast.Assign)
                        and isinstance(node.value, ast.Call)):
                    continue
                if getattr(node.value.func, 'id', None) not in THREADS:
                    continue
                target = node.targets[0]
                var = target.id if isinstance(target, ast.Name) else None
                if var is None:
                    continue
                owned = (f'{var}.wait(' in fnsrc
                         or f'not {var}.isRunning()' in fnsrc
                         or f'{var} = adopt(' in fnsrc)
                if not owned:
                    stranded.append(
                        f'{path.relative_to(ROOT).as_posix()}:{node.lineno} '
                        f'{fn.name} (local `{var}`)')
    assert not stranded, (
        'these start a thread and return without stopping it:\n  '
        + '\n  '.join(stranded)
        + '\n\nThe `finished` signal on these classes is emitted from inside '
          'run(), so waiting on it does NOT mean the thread has stopped. '
          'Wrap the construction in the adopt() fixture:\n\n'
          '    thread = adopt(FileWriterThread(path, data, "json"))')


def test_the_signal_really_does_shadow_qthreads():
    """The premise, asserted rather than remembered.

    If someone renames the custom signal, waiting on `finished` would start
    meaning what everyone assumed it meant -- and this guard, and the fixture
    it defends, would be solving a problem that no longer exists. Better to
    be told.
    """
    from PyQt6.QtCore import QThread

    from utils.async_file_ops import FileReaderThread, FileWriterThread

    for cls in (FileWriterThread, FileReaderThread):
        assert cls.finished is not QThread.finished, (
            f'{cls.__name__}.finished no longer shadows QThread.finished. '
            f'That is an improvement -- but the adopt() fixture and this '
            f'guard exist because it did, so re-read both before deciding '
            f'they are still needed.')


def test_the_application_still_checks_before_it_lets_a_thread_go():
    """The other half, and the reason no application file was edited.

    The tests were the only place that abandoned a thread. Every release
    path in the application re-checks isRunning() first. That is a real
    property of the source, so it is checked rather than trusted.
    """
    history = (ROOT / 'core' / 'color_history.py').read_text(encoding='utf-8')
    assert 'isRunning()' in history, (
        'core/color_history.py no longer checks isRunning() before releasing '
        '_save_thread')
    assert '_save_thread.wait(' in history, (
        'core/color_history.py no longer waits for _save_thread in cleanup()')

    ops = (ROOT / 'utils' / 'async_file_ops.py').read_text(encoding='utf-8')
    assert 'isRunning()' in ops, (
        'utils/async_file_ops.py no longer checks isRunning() before '
        'dropping threads from _active_threads')


def test_this_guard_can_see_the_files_it_judges():
    """A walk that finds no test files finds no stranded threads and passes,
    which looks exactly like a repository in good order."""
    files = _test_files()
    assert len(files) > 10, f'only {len(files)} test file(s) found under {ROOT}'
    built = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        for node in ast.walk(ast.parse(text)):
            if (isinstance(node, ast.Call)
                    and getattr(node.func, 'id', None) in THREADS):
                built += 1
    assert built >= 10, (
        f'only {built} thread construction(s) found across {len(files)} test '
        f'files. There were seventeen when this guard was written, so this '
        f'walk is not reading what it thinks it is.')
'''

EDITS = [('tests/test_error_recovery_paths.py', '    def test_writer_thread_with_invalid_format_raises_internally(\n        self, tmp_path, qtbot\n    ):\n', '    def test_writer_thread_with_invalid_format_raises_internally(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_error_recovery_paths.py', 'FileWriterThread(\n            str(target), {"data": "x"}, format="unknown_format_xyz"\n        )', 'adopt(FileWriterThread(\n            str(target), {"data": "x"}, format="unknown_format_xyz"\n        ))', 1), ('tests/test_error_recovery_paths.py', '    def test_writer_thread_with_unwritable_path_emits_failure(\n        self, tmp_path, qtbot\n    ):\n', '    def test_writer_thread_with_unwritable_path_emits_failure(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_error_recovery_paths.py', 'FileWriterThread(\n            str(bogus), {"data": "x"}, format="json"\n        )', 'adopt(FileWriterThread(\n            str(bogus), {"data": "x"}, format="json"\n        ))', 1), ('tests/test_error_recovery_paths.py', '    def test_reader_thread_with_missing_file_emits_failure(\n        self, tmp_path, qtbot\n    ):\n', '    def test_reader_thread_with_missing_file_emits_failure(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_error_recovery_paths.py', 'FileReaderThread(bogus, format="json")', 'adopt(FileReaderThread(bogus, format="json"))', 1), ('tests/test_error_recovery_paths.py', '    def test_reader_thread_with_corrupted_json_emits_failure(\n        self, tmp_path, qtbot\n    ):\n', '    def test_reader_thread_with_corrupted_json_emits_failure(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_error_recovery_paths.py', 'FileReaderThread(str(bad), format="json")', 'adopt(FileReaderThread(str(bad), format="json"))', 1), ('tests/test_lifecycle_handlers.py', '    def test_writer_text_format_writes_string_data(\n        self, tmp_path, qtbot\n    ):\n', '    def test_writer_text_format_writes_string_data(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileWriterThread(\n            str(target), "string content here", format="text"\n        )', 'adopt(FileWriterThread(\n            str(target), "string content here", format="text"\n        ))', 1), ('tests/test_lifecycle_handlers.py', '    def test_writer_binary_format_writes_bytes(self, tmp_path, qtbot):\n', '    def test_writer_binary_format_writes_bytes(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileWriterThread(str(target), data, format="binary")', 'adopt(FileWriterThread(str(target), data, format="binary"))', 1), ('tests/test_lifecycle_handlers.py', '    def test_writer_unsupported_format_emits_failure(\n        self, tmp_path, qtbot\n    ):\n', '    def test_writer_unsupported_format_emits_failure(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileWriterThread(\n            str(target), {"x": 1}, format="totally_made_up"\n        )', 'adopt(FileWriterThread(\n            str(target), {"x": 1}, format="totally_made_up"\n        ))', 1), ('tests/test_lifecycle_handlers.py', '    def test_reader_text_format_reads_string(self, tmp_path, qtbot):\n', '    def test_reader_text_format_reads_string(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileReaderThread(str(src), format="text")', 'adopt(FileReaderThread(str(src), format="text"))', 1), ('tests/test_lifecycle_handlers.py', '    def test_reader_binary_format_reads_bytes(self, tmp_path, qtbot):\n', '    def test_reader_binary_format_reads_bytes(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileReaderThread(str(src), format="binary")', 'adopt(FileReaderThread(str(src), format="binary"))', 1), ('tests/test_lifecycle_handlers.py', '    def test_reader_unsupported_format_emits_failure(\n        self, tmp_path, qtbot\n    ):\n', '    def test_reader_unsupported_format_emits_failure(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_lifecycle_handlers.py', 'FileReaderThread(str(src), format="weird_format_xyz")', 'adopt(FileReaderThread(str(src), format="weird_format_xyz"))', 1), ('tests/test_threading.py', '    def test_save_async_emits_finished_with_success_true(\n        self, real_color_history, tmp_path, qtbot\n    ):\n', '    def test_save_async_emits_finished_with_success_true(\n        self, real_color_history, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_threading.py', 'FileWriterThread(ch.history_file, data, "json")', 'adopt(FileWriterThread(ch.history_file, data, "json"))', 1), ('tests/test_threading.py', '    def test_file_writer_thread_emits_finished_with_success_true(\n        self, tmp_path, qtbot\n    ):\n', '    def test_file_writer_thread_emits_finished_with_success_true(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_threading.py', 'FileWriterThread(path, {"alpha": 1, "beta": [2, 3]}, "json")', 'adopt(FileWriterThread(path, {"alpha": 1, "beta": [2, 3]}, "json"))', 1), ('tests/test_threading.py', "    def test_file_writer_thread_emits_failure_on_invalid_path(\n        self, tmp_path, qtbot\n    ):\n        # A directory path that doesn't exist as a parent — write will fail\n", "    def test_file_writer_thread_emits_failure_on_invalid_path(\n        self, tmp_path, adopt, qtbot\n    ):\n        # A directory path that doesn't exist as a parent — write will fail\n", 1), ('tests/test_threading.py', 'FileWriterThread(bad_path, {"x": 1}, "json")', 'adopt(FileWriterThread(bad_path, {"x": 1}, "json"))', 1), ('tests/test_threading.py', '    def test_file_writer_thread_progress_signal_reaches_100(\n        self, tmp_path, qtbot\n    ):\n', '    def test_file_writer_thread_progress_signal_reaches_100(\n        self, tmp_path, adopt, qtbot\n    ):\n', 1), ('tests/test_threading.py', 'FileWriterThread(path, {"k": "v"}, "json")', 'adopt(FileWriterThread(path, {"k": "v"}, "json"))', 1), ('tests/test_threading.py', '    def test_file_reader_thread_round_trip(self, tmp_path, qtbot):\n', '    def test_file_reader_thread_round_trip(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_threading.py', 'FileReaderThread(str(path), "json")', 'adopt(FileReaderThread(str(path), "json"))', 1), ('tests/test_utility_modules.py', '    def test_file_writer_thread_writes_text_data(self, tmp_path, qtbot):\n', '    def test_file_writer_thread_writes_text_data(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_utility_modules.py', 'FileWriterThread(str(target), "hello world", format="text")', 'adopt(FileWriterThread(str(target), "hello world", format="text"))', 1), ('tests/test_utility_modules.py', '    def test_file_reader_thread_reads_known_json_file(self, tmp_path, qtbot):\n', '    def test_file_reader_thread_reads_known_json_file(self, tmp_path, adopt, qtbot):\n', 1), ('tests/test_utility_modules.py', 'FileReaderThread(str(src), format="json")', 'adopt(FileReaderThread(str(src), format="json"))', 1)]

FIXTURE = '\n# ── Thread ownership (RNV-THREAD-OWNERSHIP, 2026-09-07) ───────────────────\n# See tests/test_thread_ownership.py for the whole story. In short:\n# FileWriterThread.finished and FileReaderThread.finished SHADOW\n# QThread.finished() and are emitted from INSIDE run(), so waiting on one\n# means the work is done -- not that the thread has stopped.\n\n\n@pytest.fixture\ndef adopt(qtbot):\n    """Own any QThread this test starts, and stop it before the test ends.\n\n    WHY THIS EXISTS. Seventeen tests built a FileWriterThread or a\n    FileReaderThread, waited on its custom `finished` signal, and returned.\n    That signal is emitted from inside run(), so the QThread was still\n    RUNNING -- and the local name was the only reference to it. Nothing\n    collected it straight away; it was destroyed at whatever later\n    allocation happened to trigger a collection, which is why Linux CI\n    aborted (SIGABRT, exit 134) inside a LATER test\'s frame, three times,\n    at three different tests, each of which looked like a separate flake.\n\n    WHY A FIXTURE AND NOT A wait() AT THE END OF EACH TEST. Teardown runs\n    even when an assertion fails. A trailing wait() does not -- so a failing\n    assertion would abandon the thread and the abort would bury the real\n    failure underneath it.\n\n    Usage:\n\n        thread = adopt(FileWriterThread(path, data, "json"))\n    """\n    owned = []\n\n    def _adopt(thread):\n        owned.append(thread)\n        return thread\n\n    yield _adopt\n\n    for thread in owned:\n        if thread.isRunning():\n            thread.quit()\n            assert thread.wait(5000), (\n                "a thread this test started was still running at teardown "\n                "and did not stop within 5s. Leaving it running is what "\n                "aborts the interpreter later.")\n'


def edits(tree) -> None:
    conftest = tree.read(SENTINEL_FILE)
    if SENTINEL in conftest:
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    tree.write(SENTINEL_FILE, conftest.rstrip("\n") + "\n" + FIXTURE)
    files = sorted({e[0] for e in EDITS})
    print(f"  installed the `adopt` fixture in {SENTINEL_FILE}")
    print(f"  {len(EDITS) // 2} test site(s) adopted across {len(files)} file(s)")
    for rel in files:
        print(f"    {rel}  ({len([e for e in EDITS if e[0] == rel]) // 2})")


def checks(tree) -> None:
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise SystemExit("the fixture did not land")

    # Not one test still builds a thread it does not own. This is the same
    # walk the guard does, run against the in-memory tree before anything
    # reaches disk.
    THREADS = {"FileWriterThread", "FileReaderThread"}
    stranded = []
    for rel in sorted(tree.files):
        if not rel.startswith("tests/") or not rel.endswith(".py"):
            continue
        text = tree.files[rel]
        try:
            parsed = ast.parse(text)
        except SyntaxError as exc:
            raise SystemExit(f"{rel} does not parse after the edit: {exc}")
        for fn in [n for n in ast.walk(parsed) if isinstance(n, ast.FunctionDef)]:
            fnsrc = ast.get_source_segment(text, fn) or ""
            for node in ast.walk(fn):
                if not (isinstance(node, ast.Assign)
                        and isinstance(node.value, ast.Call)):
                    continue
                called = getattr(node.value.func, "id", None)
                if called not in THREADS:
                    continue
                var = (node.targets[0].id
                       if isinstance(node.targets[0], ast.Name) else "?")
                if f"{var}.wait(" in fnsrc or f"not {var}.isRunning()" in fnsrc:
                    continue
                stranded.append(f"{rel}:{node.lineno} {fn.name}")
    if stranded:
        raise SystemExit("threads are still abandoned: " + ", ".join(stranded))

    n = len([e for e in EDITS if e[1].lstrip().startswith(("thread", "t "))])
    print(f"  guards: 0 abandoned threads across every test file")


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = text.encode("utf-8")
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

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
        return "fail"
    return "env"


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
    return code


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

    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
