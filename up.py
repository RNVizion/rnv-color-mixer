#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: a deferred callback should not outlive what it acts on.

    python up.py             # apply, install the guard, run the suites
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT IS WRONG. ColorMixerApp.__init__ queues three deferred callbacks -- at
100 ms, 150 ms and 500 ms -- through SafeQTimer, whose body ends in

    QTimer.singleShot(msec, safe_wrapper)

safe_wrapper is a plain closure, so that connection has **no receiver
QObject**, and Qt has nothing whose destruction could cancel it. The
callback is delivered msec later whatever happened in between.

MEASURED, NOT ASSUMED. On an untouched checkout of the live head, a window
constructed and then destroyed before its startup timers fired produced
**four** swallowed RuntimeErrors, not the one on record:

    Error applying themed mode:  ... ColorMixerApp has been deleted
    Error applying slot themes:  ... ColorSlot has been deleted
    Error applying theme:        ... ColorMixerApp has been deleted
    Error in updating preview:   ... QLabel has been deleted

The last is the one KNOWN_ISSUES.md names, in _update_preview.

THE PART WORTH KNOWING. Handing singleShot a BOUND METHOD of a QObject is
already safe: PyQt ties the connection to that object and Qt cancels it on
destruction. Verified here in both directions. SafeQTimer wrapped every
callable in a try/except closure in order to be careful -- and a closure is
a plain function, so **the wrapper added to make the call safe is what made
it unsafe**. Its except clause then logged the consequence and carried on.

WHAT CHANGES.

    SafeQTimer.safe_single_shot(150, ...)   ->   (self, 150, ...)

Seven call sites, all methods of ColorMixerApp, all passing `self`. The
callback then checks that context before it runs, and returns quietly if
its C++ side has gone. Nothing else can answer that question: on PyQt6 6.11,
against a QLabel whose parent had been deleted,

    bool(label)              -> True          hasattr(label, 'width') -> True
    label.width()            -> RuntimeError  sip.isdeleted(label)    -> True

so every `if self.some_widget:` in a deferred callback is a test for None
and nothing more. Measured, not assumed.

TWO DESIGNS WERE TRIED AND WITHDRAWN, WHICH IS WHY THIS ONE LOOKS PLAIN.

  1. singleShot's context-object overload, QTimer.singleShot(ms, obj, slot).
     PyQt6 6.11 does not expose it. Rejected on a TypeError, not on taste.

  2. Parenting the timer: QTimer(context), destroyed with its parent, so Qt
     cancels the callback and no check is needed anywhere. Tidier, and it
     **segfaulted on the fourth window** of tests/test_app_event_handlers.py
     -- a file the untouched tree passes -- because ui_handler calls
     QApplication.processEvents() inside _apply_image_mode and so dispatches
     timer events re-entrantly while a window is being built. Identified by
     discriminating rather than guessing: the identical helper with an
     UNPARENTED timer passes the same file. The guard asserts the timer
     stays unowned, so the tidier version cannot come back by accident.

ONE DEAD LINE GOES WITH IT. The line KNOWN_ISSUES.md names reads

    current_size = self.preview_label.width() if hasattr(...) else 140

inside `if self.preview_label:`, so the attribute provably exists and the
fallback is unreachable. It also guards the wrong thing: hasattr returns
True for a destroyed C++ object, and so does bool(). Both were measured. A
check that cannot fail, in the place everyone looks first, is worse than no
check.

NO FEATURE IS REMOVED. Every callback that runs today still runs, with the
same delay and the same arguments -- the guard asserts both. What stops is
callbacks running after their window is gone.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-mixer"
SENTINEL_FILE = "RNV_Color_Mixer.py"
SENTINEL = "RNV-TIMER-OWNERSHIP"
GUARD = "tests/test_timer_ownership.py"
DESCRIPTION = "stop deferred callbacks outliving what they act on"
SUITES = [("\"pytest tests/\"",
           [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("\"the LOCKED file, 355 tests\"",
           [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-TIMER-OWNERSHIP-GUARD -- a deferred callback checks what it acts on.

Installed 2026-09-09, closing the lifecycle item KNOWN_ISSUES.md has carried
since the thread-ownership round.

WHAT WAS WRONG. ColorMixerApp.__init__ queues three deferred callbacks --
at 100 ms, 150 ms and 500 ms -- through a helper that ends in

    QTimer.singleShot(msec, safe_wrapper)

safe_wrapper is a plain closure, so that connection has no receiver QObject
and Qt has nothing whose destruction could cancel it. A test that builds the
window and tears it down inside half a second leaves all three firing
against a destroyed C++ object. Reproduced on an untouched checkout of the
live head: a window deleted straight after construction produced FOUR
swallowed RuntimeErrors, not the one on record --

    Error applying themed mode:  ... ColorMixerApp has been deleted
    Error applying slot themes:  ... ColorSlot has been deleted
    Error applying theme:        ... ColorMixerApp has been deleted
    Error in updating preview:   ... QLabel has been deleted

the last from _update_preview, which is the one KNOWN_ISSUES.md names. With
the context check in place, the same reproduction produces zero.

THE PART WORTH REMEMBERING. Handing singleShot a BOUND METHOD of a QObject
is already safe: PyQt ties the connection to that object and Qt cancels it
on destruction. The helper wrapped every callable in a try/except closure in
order to be careful, and a closure is a plain function -- so the wrapper
added to make the call safe destroyed the association that made it safe, and
its except clause then hid the consequence.

WHY THE TIMER IS NOT OWNED BY THE CONTEXT. Parenting it -- QTimer(context),
destroyed with its parent, cancelled by Qt with no check needed -- was the
first fix and is the tidier one. It **segfaulted on the fourth window** of
tests/test_app_event_handlers.py, a file the untouched tree passes, because
ui_handler calls QApplication.processEvents() inside _apply_image_mode and
so dispatches timer events re-entrantly during construction. The identical
helper with an unparented QTimer passes that file, which is how the
ownership was identified as the hazard rather than guessed at.
test_the_helper_does_not_own_the_timer_it_starts below is there so nobody
re-derives the tidier version and rediscovers the crash.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: Directories that are not the application. `tests` is excluded on purpose:
#: the rule below is about the application's own deferred callbacks, and a
#: test docstring that quotes a call is a mention, not a call. Reading the
#: syntax tree rather than the text makes that distinction for free.
NOT_THE_APP = ("tests", ".git", "build", "dist", ".venv", "__pycache__")

HELPER = "safe_single_shot"


def _app_sources():
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in NOT_THE_APP or rel.name.startswith("up"):
            continue
        yield path


def _calls_to(attribute: str):
    """Every Call node in the application whose function is `.attribute`."""
    for path in _app_sources():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == attribute):
                yield path, node


def _helper_def():
    for path in _app_sources():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == HELPER:
                return path, node
    return None, None


def _pump(milliseconds: int) -> None:
    from PyQt6.QtCore import QEventLoop, QTimer
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_every_deferred_callback_names_the_object_it_acts_on():
    """The rule, stated over the syntax tree.

    A delay is an integer literal; a context is not. Checking the shape of
    the first argument rather than its spelling lets a call pass `self`,
    `self.window` or a local, and stops a call that has simply not been
    updated.
    """
    bad = []
    for path, node in _calls_to(HELPER):
        rel = path.relative_to(ROOT).as_posix()
        first = node.args[0] if node.args else None
        if first is None or (isinstance(first, ast.Constant)
                             and isinstance(first.value, int)):
            bad.append(f'{rel}:{node.lineno}  {ast.unparse(node)[:88]}')
    assert not bad, (
        'these deferred callbacks do not name the object they act on, so '
        'nothing stops them running after it is destroyed:\n  '
        + '\n  '.join(bad)
        + '\n\nPass the object first: '
          'SafeQTimer.safe_single_shot(self, 150, ...)')


def test_the_helper_checks_its_context_before_it_runs():
    """A context nothing reads is decoration.

    The call sites could all be updated, every argument in the right place,
    and the helper could still ignore what it was given. So the context has
    to be referenced inside the closure that actually runs -- not merely
    accepted by the function that schedules it.
    """
    path, node = _helper_def()
    assert node is not None, f'{HELPER} is not defined anywhere in the app'
    rel = path.relative_to(ROOT).as_posix()

    names = [a.arg for a in node.args.args]
    assert names and names[0] == 'context', (
        f'{rel}: {HELPER} should take the context first, not {names}')

    inner = [n for n in ast.walk(node)
             if isinstance(n, ast.FunctionDef) and n is not node]
    assert inner, f'{rel}: {HELPER} no longer defines a wrapper to schedule'

    reads_context = any(
        isinstance(n, ast.Name) and n.id == 'context'
        for wrapper in inner for n in ast.walk(wrapper))
    assert reads_context, (
        f'{rel}: {HELPER} accepts a context and never reads it inside the '
        f'callback. The parameter is then documentation, and the callback '
        f'still runs against destroyed objects.')


def test_the_helper_does_not_own_the_timer_it_starts():
    """A regression test for a fix that was tried and withdrawn.

    QTimer(context) is the tidier answer -- Qt cancels the callback when the
    parent dies and no check is needed. It segfaults here, on the fourth
    window of tests/test_app_event_handlers.py, because ui_handler pumps the
    event loop re-entrantly during construction. This test costs nothing and
    saves the next person the afternoon it cost to find.
    """
    path, node = _helper_def()
    assert node is not None
    rel = path.relative_to(ROOT).as_posix()

    parented = [ast.unparse(n) for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == 'QTimer' and n.args]
    assert not parented, (
        f'{rel}: {HELPER} constructs a QTimer with a parent:\n  '
        + '\n  '.join(parented)
        + '\n\nThat is the tidier fix and it segfaults in this codebase: '
          'ui_handler calls QApplication.processEvents() inside '
          '_apply_image_mode, so timer events are dispatched re-entrantly '
          'while a window is being built, and a timer owned by a window '
          'being torn down is dispatched after its owner is gone. Use the '
          'context check instead.')


def test_a_destroyed_context_really_does_stop_its_callback(qapp, main_module):
    """The part the syntax tree cannot answer.

    Every static test above would pass a helper that reads `context` in a
    log line and runs the callback anyway. This one destroys the context and
    asserts silence; the next asserts that silence is not all it can do.
    """
    sip = pytest.importorskip('PyQt6.sip')
    from PyQt6.QtCore import QObject

    fired = []
    holder = QObject()
    main_module.SafeQTimer.safe_single_shot(holder, 10, lambda: fired.append('ran'))
    sip.delete(holder)
    _pump(150)

    assert fired == [], (
        'a callback deferred against a destroyed context still ran. That is '
        'the whole defect: it acts on widgets that no longer exist, and the '
        'helper logs the RuntimeError and carries on.')


def test_a_live_context_still_gets_its_callback(qapp, main_module):
    """The converse, without which "fixed" could mean "never fires"."""
    from PyQt6.QtCore import QObject

    fired = []
    holder = QObject()
    main_module.SafeQTimer.safe_single_shot(holder, 10, lambda: fired.append('ran'))
    _pump(300)

    assert fired == ['ran'], (
        'a callback deferred against a LIVE context did not run. The point '
        'is to stop callbacks whose target is gone, not to stop deferring.')


def test_arguments_still_reach_the_callback(qapp, main_module):
    """Two call sites pass an argument through. That path is easy to lose in
    a rewrite, and nothing else here would notice."""
    from PyQt6.QtCore import QObject

    seen = []
    holder = QObject()
    main_module.SafeQTimer.safe_single_shot(holder, 10, seen.append, 'payload')
    _pump(300)

    assert seen == ['payload'], f'arguments did not reach the callback: {seen}'


def test_the_liveness_check_says_nothing_when_it_cannot_tell(main_module):
    """"Unknown" must behave the way this code behaved before the check.

    A liveness test that answered "gone" for anything it did not recognise
    would silently stop callbacks from running -- a much quieter bug than
    the one being fixed, and one no suite would attribute to this change.
    """
    check = getattr(main_module, '_qt_object_is_gone', None)
    assert check is not None, (
        'the liveness helper is gone; the context check has nothing to ask')
    assert check(None) is True, 'None is gone by definition'
    assert check(object()) is False, (
        'a plain Python object is not a wrapped Qt object, so nothing is '
        'known about it and the answer must be False')
    assert check('not a qt object') is False


def _helper_line_span():
    """The lines the helper occupies, per file.

    The helper makes a receiverless deferred call on purpose -- it is the
    one place that checks the target first. Excluding it is the rule stated
    properly, not an exemption from it: a receiverless deferred call is safe
    exactly when something checks before running, and by design there is one
    such place. The first draft of the test below omitted the qualifier and
    flagged the fix itself as the defect.
    """
    spans = {}
    for path in _app_sources():
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == HELPER:
                spans.setdefault(path, set()).update(
                    range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return spans


def test_no_deferred_call_is_made_from_a_receiverless_callable():
    """The same rule one level down, for direct uses of the Qt call.

    `QTimer.singleShot(200, self.method)` is fine -- PyQt ties that
    connection to the QObject the method is bound to, and Qt cancels it on
    destruction. A lambda or a bare function name has no receiver and
    nothing can cancel it, so it must go through the helper instead.
    """
    spans = _helper_line_span()
    bad = []
    for path, node in _calls_to('singleShot'):
        rel = path.relative_to(ROOT).as_posix()
        if not node.args:
            continue
        if node.lineno in spans.get(path, ()):
            continue
        slot = node.args[-1]
        if isinstance(slot, (ast.Lambda, ast.Name)):
            bad.append(f'{rel}:{node.lineno}  {ast.unparse(node)[:88]}')
    assert not bad, (
        'these deferred calls hand Qt a callable with no receiver, so '
        'nothing can cancel them:\n  '
        + '\n  '.join(bad)
        + '\n\nUse a bound method of the object, or route it through '
          'SafeQTimer with an explicit context.')


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that finds nothing passes every assertion above.

    Not a hypothetical: the image-budget guard shipped with a rule whose
    glob matched no file in three of five repositories, and every other test
    in it was green. A sweep states how much it found.
    """
    files = list(_app_sources())
    assert any(p.name == 'RNV_Color_Mixer.py' for p in files), (
        f'the application entry point is not among the {len(files)} files '
        f'this guard reads; the exclusion list is wrong')

    found = list(_calls_to(HELPER))
    assert len(found) >= 7, (
        f'expected at least seven deferred callbacks in the application, '
        f'found {len(found)}. Either they were removed -- in which case this '
        f'guard has no subject and should go with them -- or the sweep has '
        f'stopped seeing the file they live in.')
'''

EDITS = [('RNV_Color_Mixer.py', 'class SafeQTimer(QObject):\n    """Safe timer wrapper that catches exceptions"""\n    \n    def __init__(self, parent: QObject | None = None) -> None:\n        super().__init__(parent)\n        \n    @staticmethod\n    def safe_single_shot(msec: int, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:\n        """Execute function with exception handling"""\n        def safe_wrapper() -> None:\n            try:\n                if args or kwargs:\n                    func(*args, **kwargs)\n                else:\n                    func()\n            except Exception as e:\n                logger.error("Timer callback error", error=e)\n                traceback.print_exc()\n        \n        QTimer.singleShot(msec, safe_wrapper)', 'def _qt_object_is_gone(obj: object) -> bool:\n    """True when a Qt object\'s C++ side has been destroyed under its wrapper.\n\n    Nothing else can answer this. Measured on PyQt6 6.11 against a QLabel\n    whose parent had been deleted:\n\n        bool(label)                 -> True\n        hasattr(label, \'width\')     -> True\n        label.width()               -> RuntimeError: wrapped C/C++ object\n                                       of type QLabel has been deleted\n        sip.isdeleted(label)        -> True\n\n    So `if self.some_widget:` is a test for None and nothing more, which is\n    why every such guard in a deferred callback has been passing and then\n    raising on the next line.\n\n    Returns False when it cannot tell -- sip missing, or the object not a\n    wrapped one -- because "unknown" must behave the way this code behaved\n    before the check existed. A liveness test that guessed "gone" would\n    silently stop callbacks from running.\n    """\n    if obj is None:\n        return True\n    if _sip is None:\n        return False\n    try:\n        return bool(_sip.isdeleted(obj))\n    except TypeError:\n        return False\n\n\nclass SafeQTimer(QObject):\n    """A single-shot timer whose callback will not run against a dead object.\n\n    RNV-TIMER-OWNERSHIP, 2026-09-09. See tests/test_timer_ownership.py.\n\n    WHY THIS TAKES A CONTEXT. QTimer.singleShot(msec, a_plain_function)\n    creates a connection with no receiver QObject, so Qt has nothing whose\n    destruction could cancel it: the callback is delivered msec later\n    whatever happened in between. Handing that call a BOUND METHOD of a\n    QObject would be tied to that object and cancelled on destruction -- but\n    this helper wraps every callable in a try/except closure, and a closure\n    is a plain function. **The wrapper added in order to be careful is what\n    removed Qt\'s own care**, and its except clause then logged the result\n    and carried on.\n\n    Measured on a window destroyed before its startup timers fired: four\n    swallowed "RuntimeError: wrapped C/C++ object of type ... has been\n    deleted" per teardown, one of them from _update_preview -- the one\n    KNOWN_ISSUES.md names. With the check below: zero.\n\n    WHY THE TIMER IS NOT PARENTED TO THE CONTEXT, WHICH WOULD BE TIDIER.\n    That was the first fix, and it was withdrawn. A QTimer built as\n    QTimer(context) is destroyed with its parent, which cancels the callback\n    at the Qt level and needs no check at all -- but ui_handler calls\n    QApplication.processEvents() inside _apply_image_mode, so timer events\n    are dispatched re-entrantly during window construction. With the timers\n    owned by the window, that **segfaulted on the fourth window** of\n    tests/test_app_event_handlers.py, on a file the untouched tree passes.\n    Confirmed by discriminating: the identical helper with an UNPARENTED\n    QTimer passes the same file. So the ownership is the hazard, and the\n    check below is the fix that survives contact with this codebase.\n    """\n\n    def __init__(self, parent: QObject | None = None) -> None:\n        super().__init__(parent)\n\n    @staticmethod\n    def safe_single_shot(context: QObject, msec: int, func: Callable[..., Any],\n                         *args: Any, **kwargs: Any) -> None:\n        """Call func after msec, unless context has been destroyed by then.\n\n        `context` is the object the callback acts on -- for a method of a\n        window, that window. It is required, and deliberately first: an\n        optional context is one that gets left out at exactly the call site\n        that needed it.\n        """\n        def safe_wrapper() -> None:\n            if _qt_object_is_gone(context):\n                return\n            try:\n                if args or kwargs:\n                    func(*args, **kwargs)\n                else:\n                    func()\n            except Exception as e:\n                logger.error("Timer callback error", error=e)\n                traceback.print_exc()\n\n        QTimer.singleShot(msec, safe_wrapper)', 1), ('RNV_Color_Mixer.py', 'import traceback\nfrom types import TracebackType\n', 'import traceback\ntry:\n    from PyQt6 import sip as _sip\nexcept ImportError:                 # sip ships with PyQt6; degrade, do not fail\n    _sip = None\nfrom types import TracebackType\n', 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(100, self._force_initial_theme_update)', 'SafeQTimer.safe_single_shot(self, 100, self._force_initial_theme_update)', 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(150, lambda: self._update_preview(self.current_mixed_color))', 'SafeQTimer.safe_single_shot(self, 150, lambda: self._update_preview(self.current_mixed_color))', 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(500, self._check_crash_recovery)', 'SafeQTimer.safe_single_shot(self, 500, self._check_crash_recovery)', 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(50, self._do_image_load, path)', 'SafeQTimer.safe_single_shot(self, 50, self._do_image_load, path)', 1), ('RNV_Color_Mixer.py', "SafeQTimer.safe_single_shot(100, lambda: setattr(slot, '_being_removed', False) if hasattr(slot, '_being_removed') else None)", "SafeQTimer.safe_single_shot(self, 100, lambda: setattr(slot, '_being_removed', False) if hasattr(slot, '_being_removed') else None)", 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(100, self._update_image_display)', 'SafeQTimer.safe_single_shot(self, 100, self._update_image_display)', 1), ('RNV_Color_Mixer.py', 'SafeQTimer.safe_single_shot(10, self._do_image_load, path)', 'SafeQTimer.safe_single_shot(self, 10, self._do_image_load, path)', 1), ('RNV_Color_Mixer.py', "current_size = self.preview_label.width() if hasattr(self, 'preview_label') else 140", 'current_size = self.preview_label.width()', 1), ('tests/test_app_event_handlers.py', 'and queues `_do_image_load` via `SafeQTimer.safe_single_shot(10, ...)`.', 'and queues `_do_image_load` via\n        `SafeQTimer.safe_single_shot(self, 10, ...)`.', 1), ('tests/test_main_app_dispatchers.py', '`SafeQTimer.safe_single_shot(50, _do_image_load, path)` so we', '`SafeQTimer.safe_single_shot(self, 50, _do_image_load, path)` so we', 1), ('KNOWN_ISSUES.md', '`RNV_Color_Mixer.py:2365` — a preview callback firing after its label is\ngone — which is the same lifecycle smell described above and is worth its\nown look.', "`RNV_Color_Mixer.py` — a preview callback firing after its label is\ngone. **Fixed 2026-09-09.** `SafeQTimer` wrapped every callable in a\ntry/except closure; a closure is a plain function, so `singleShot` had no\nreceiver QObject to cancel against and the callback ran `msec` later\nwhatever had happened to the window in between. Each deferred call now\nnames the object it acts on and returns quietly when that object's C++\nside is gone. A window destroyed straight after construction produced\nfour such swallowed RuntimeErrors before the change and none after.\nGuarded by `tests/test_timer_ownership.py`.", 1), ('KNOWN_ISSUES.md', 'Deselected on Linux only, in the manner this entry already prescribed:\nvisible in the workflow, not marked skip, so the cost stays countable. The\nplanned fix is unchanged and is still the right one.', '**No longer deselected.** Both classes were restored to Linux CI on\n2026-09-08, once the thread-ownership fix landed, and the workflow records\nthe restoration in place. This paragraph went on describing the deselect\nas current after it had been removed, which is the ordinary fate of prose\nthat nothing checks.', 1)]

HELPER = "safe_single_shot"


def edits(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if SENTINEL in src:
        raise SystemExit("already applied")
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    # Counted from the data, not by subtracting a constant. The line that
    # said "N - 5 call sites" was accurate until two documentation edits
    # were added, and then quietly was not.
    by_file: dict = {}
    for rel, *_ in EDITS:
        by_file[rel] = by_file.get(rel, 0) + 1
    print("  " + ", ".join(f"{n} in {rel}" for rel, n in sorted(by_file.items())))


def checks(tree) -> None:
    text = tree.files[SENTINEL_FILE]

    # 1. it parses. Every later check reads the syntax tree, and a file that
    #    does not parse would make all of them vacuous rather than red.
    try:
        module = ast.parse(text, SENTINEL_FILE)
    except SyntaxError as exc:
        raise SystemExit(f"{SENTINEL_FILE} does not parse after the edits: {exc}")

    # 2. the helper owns its timer and takes the context first
    node = next((n for n in ast.walk(module)
                 if isinstance(n, ast.FunctionDef) and n.name == HELPER), None)
    if node is None:
        raise SystemExit(f"{HELPER} is gone; this round replaces it, not removes it")
    names = [a.arg for a in node.args.args]
    if not names or names[0] != "context":
        raise SystemExit(f"{HELPER} takes {names}, not context first")

    # the context must be READ by the closure that runs, not merely accepted
    inner = [n for n in ast.walk(node)
             if isinstance(n, ast.FunctionDef) and n is not node]
    if not any(isinstance(n, ast.Name) and n.id == "context"
               for wrapper in inner for n in ast.walk(wrapper)):
        raise SystemExit(f"{HELPER} never reads its context inside the "
                         f"callback, so the parameter is decoration")

    # and the timer must NOT be owned by that context. The tidier fix --
    # QTimer(context), cancelled by Qt on destruction -- segfaulted on the
    # fourth window of tests/test_app_event_handlers.py, because ui_handler
    # pumps the event loop re-entrantly inside _apply_image_mode. Identified
    # by discriminating against the same helper with an unparented timer,
    # which passes. Asserted here so a later tidy-up cannot reintroduce it.
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "QTimer" and n.args for n in ast.walk(node)):
        raise SystemExit(f"{HELPER} parents its timer to the context; that "
                         f"shape segfaults in this codebase")

    if "_qt_object_is_gone" not in text:
        raise SystemExit("the liveness helper did not land")

    # 3. every call site names a context, and NOTHING ELSE about it moved.
    #    The delay and the arguments are compared against the checkout, so a
    #    substitution that quietly changed a timing or dropped an argument
    #    fails here rather than in a suite twenty minutes later.
    calls = [n for n in ast.walk(module)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == HELPER]
    if len(calls) < 7:
        raise SystemExit(f"only {len(calls)} call sites survive; expected 7+")
    for call in sorted(calls, key=lambda n: n.lineno):
        if len(call.args) < 3:
            raise SystemExit(f"line {call.lineno}: {ast.unparse(call)[:70]} "
                             f"has no context")
        if not (isinstance(call.args[1], ast.Constant)
                and isinstance(call.args[1].value, int)):
            raise SystemExit(f"line {call.lineno}: the delay is no longer the "
                             f"second argument")

    before = {('100', 'self._force_initial_theme_update'): 1, ('150', 'lambda: self._update_preview(self.current_mixed_color)'): 1, ('50', 'self._do_image_load', 'path'): 1, ('100', "lambda: setattr(slot, '_being_removed', False) if hasattr(slot, '_being_removed') else None"): 1, ('500', 'self._check_crash_recovery'): 1, ('100', 'self._update_image_display'): 1, ('10', 'self._do_image_load', 'path'): 1}
    now = {}
    for call in calls:
        rest = tuple(ast.unparse(a) for a in call.args[1:])
        now[rest] = now.get(rest, 0) + 1
    for rest, count in before.items():
        if now.get(rest, 0) != count:
            raise SystemExit(
                f"a deferred call changed shape: {rest} appeared {count} "
                f"time(s) before and {now.get(rest, 0)} now")

    # 4. the dead line is gone, and the live one it guarded is intact
    if "if hasattr(self, 'preview_label') else 140" in text:
        raise SystemExit("the unreachable fallback survived")
    if "current_size = self.preview_label.width()" not in text:
        raise SystemExit("the width lookup went with it; that one is live")

    # 5. no deferred call anywhere in the app hands Qt a receiverless
    #    callable -- EXCEPT inside the helper itself, which is the one place
    #    that compensates with a liveness check. That is not an exemption;
    #    it is the rule stated properly. A receiverless deferred call is
    #    safe exactly when something checks the target before running, and
    #    there is precisely one such place by design. The first draft of
    #    this check omitted the qualifier and flagged the fix as the defect.
    root = Path.cwd()
    loose = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.split("/")[0] in ("tests", ".git", "build", "dist", ".venv"):
            continue
        if path.parent == root and path.name.startswith("up"):
            continue
        body = tree.files.get(rel)
        if body is None:
            try:
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
        try:
            sub = ast.parse(body, rel)
        except SyntaxError:
            continue
        inside_helper = set()
        for n in ast.walk(sub):
            if isinstance(n, ast.FunctionDef) and n.name == HELPER:
                inside_helper.update(
                    range(n.lineno, (n.end_lineno or n.lineno) + 1))
        for n in ast.walk(sub):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "singleShot" and n.args
                    and isinstance(n.args[-1], (ast.Lambda, ast.Name))
                    and n.lineno not in inside_helper):
                loose.append(f"{rel}:{n.lineno}")
    if loose:
        raise SystemExit("deferred calls with no receiver survive: "
                         + ", ".join(loose))

    # 6. the prose says what happened. Read with whitespace collapsed: a
    #    markdown paragraph wraps where the width runs out, and a check that
    #    looked for a phrase the file had split across a line break has
    #    failed here before on the line break rather than the meaning.
    known = " ".join(tree.files["KNOWN_ISSUES.md"].split())
    if "worth its own look" in known:
        raise SystemExit("KNOWN_ISSUES.md still calls this an open smell")
    if "test_timer_ownership.py" not in known:
        raise SystemExit("KNOWN_ISSUES.md does not name the guard")
    if "Deselected on Linux only" in known:
        raise SystemExit("KNOWN_ISSUES.md still describes a deselect the "
                         "workflow removed on 2026-09-08")

    print(f"  guards: {len(calls)} call sites carry a context, delays and "
          f"arguments unchanged, 0 receiverless deferred calls")


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
