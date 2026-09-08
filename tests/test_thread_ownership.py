"""RNV-THREAD-OWNERSHIP-GUARD -- a test that starts a thread finishes it.

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
