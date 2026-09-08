"""RNV-RESTORED-CLASSES-GUARD -- the 12 tests Linux CI stopped skipping
actually run there, and keep running.

Installed 2026-09-08. `tests/test_error_recovery_paths.py::TestAsyncFileOpsErrorPaths`
and `tests/test_lifecycle_handlers.py::TestAsyncFileOpsFormatPaths` were
deselected on Linux from 31 August because they aborted the interpreter
(SIGABRT, exit 134). The thread-ownership fix removed the cause, measured on
the tree before and after with both classes included:

    before   70 aborts / 120 runs   (58.3%)
    after     0 aborts / 120 runs

WHAT THIS ADDS THAT tests/test_ci_deselects.py DOES NOT. That file reads the
workflow: it proves the arguments are gone and that the prose agrees. This
one proves the tests THEMSELVES are real, present and exercising the thing
they were written for -- because a restored deselect achieves nothing if the
class was quietly emptied or renamed in the meantime, and both files would
pass over the silence.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (file, class, the number of tests it held when the deselects came off)
RESTORED = (
    ('tests/test_error_recovery_paths.py', 'TestAsyncFileOpsErrorPaths', 4),
    ('tests/test_lifecycle_handlers.py', 'TestAsyncFileOpsFormatPaths', 6),
)


def _methods(rel: str, cls: str):
    path = ROOT / rel
    assert path.exists(), f'{rel} is missing'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return [n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name.startswith('test')]
    return None


def test_both_restored_classes_still_exist():
    """A class that was renamed or removed leaves the workflow clean and the
    coverage gone, with nothing to say so."""
    missing = [f'{rel}::{cls}' for rel, cls, _ in RESTORED
               if _methods(rel, cls) is None]
    assert not missing, (
        'these classes were restored to Linux CI on 2026-09-08 and no longer '
        'exist:\n  ' + '\n  '.join(missing))


def test_they_still_hold_the_tests_they_held():
    """Counted, not assumed. Twelve tests came back; if that number falls,
    it should be because somebody decided so."""
    thin = []
    for rel, cls, expected in RESTORED:
        names = _methods(rel, cls) or []
        if len(names) < expected:
            thin.append(f'{rel}::{cls} has {len(names)}, had {expected}')
    assert not thin, (
        'restored classes have lost tests:\n  ' + '\n  '.join(thin)
        + '\n\nIf that was deliberate, lower the count in this file in the '
          'same commit, so the loss is written down rather than absorbed.')


def test_they_are_not_skipped_by_decorator_instead():
    """The other way to make a test quiet.

    Removing a --deselect and adding @pytest.mark.skip has the same effect
    on coverage and a much smaller diff. KNOWN_ISSUES.md is explicit that
    this family should be deselected visibly rather than marked skip, "so
    the cost stays countable" -- and that reasoning survives the fix.
    """
    marked = []
    for rel, cls, _ in RESTORED:
        text = (ROOT / rel).read_text(encoding='utf-8')
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == cls):
                continue
            targets = [node] + [n for n in node.body
                                if isinstance(n, ast.FunctionDef)]
            for target in targets:
                for dec in target.decorator_list:
                    src = ast.get_source_segment(text, dec) or ''
                    if 'skip' in src and 'skipif' not in src:
                        marked.append(f'{rel}::{cls}::{getattr(target, "name", "?")}'
                                      f'  @{src.strip()[:40]}')
    assert not marked, (
        'these are skipped by decorator, which hides them as effectively as '
        'the deselect did:\n  ' + '\n  '.join(marked))


def test_the_thread_ownership_fixture_is_what_they_depend_on():
    """Name the coupling, so it cannot be removed by accident.

    These classes are only safe to run because every thread they build is
    adopted. If the fixture disappears, this round's premise disappears with
    it, and the aborts come back at 58%.
    """
    conftest = (ROOT / 'tests' / 'conftest.py').read_text(encoding='utf-8')
    assert 'def adopt(' in conftest, (
        'the adopt() fixture is gone from tests/conftest.py. The two '
        'AsyncFileOps classes were restored to Linux CI on the strength of '
        'it; without it they abort roughly three runs in five.')
    for rel, cls, _ in RESTORED:
        text = (ROOT / rel).read_text(encoding='utf-8')
        assert 'adopt(' in text, (
            f'{rel} no longer uses adopt(), so the threads it starts are '
            f'abandoned again.')
