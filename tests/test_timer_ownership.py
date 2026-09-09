"""RNV-TIMER-OWNERSHIP-GUARD -- a deferred callback checks what it acts on.

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
