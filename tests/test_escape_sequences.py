r"""RNV-ESCAPE-SEQUENCES-GUARD -- every string literal here is still legal
Python, and will still be legal in Python 3.14.

THIS DOCSTRING IS RAW ON PURPOSE, and the first draft was not. It quotes the
offending text, so it reproduced the offence: the guard against invalid
escape sequences contained an invalid escape sequence, and failed itself on
the first run. Use versus mention -- the eleventh instance in this
programme. A file that must SHOW a bad escape has to be raw, or say it in
words.

Installed 2026-09-08. tests/test_contrast_pairs.py carried

    A regex over `\{\{([^{}]*)\}\}` once found 23 of 173 rules ...

inside a NON-RAW docstring. Backslash-brace is not a recognised escape, so
Python kept the backslash and warned. That warning has been:

    3.6 - 3.11   DeprecationWarning  (invisible unless you look)
    3.12         SyntaxWarning       (visible on every run)
    3.14         SyntaxError         (the file stops importing)

A dated removal, like Pillow's, and this one takes the whole module with it.

WHY IT SURFACED NOW. tests/test_thread_ownership.py walks every test file
with ast.parse, which re-triggers the warning on each pass -- one warning
became three in the CI log. Fixing the string fixes all three; suppressing
them in the walker would have hidden a real deadline.

WHY A GUARD FOR A ONE-CHARACTER FIX. Because the fix is one character, the
next one will be too, and nothing would have caught it. The whole fleet was
swept when this was written: exactly one instance in five repositories. A
guard armed against a clean sweep is the cheapest it will ever be.
"""
from __future__ import annotations

import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {'.git', 'build', 'dist', '__pycache__', '.venv', '.pytest_cache',
             'htmlcov', '.benchmarks', '.hypothesis'}


def _sources():
    for path in sorted(ROOT.rglob('*.py')):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # a delivery script is a tool passing through, not application source
        if path.parent == ROOT and path.name.startswith('up'):
            continue
        yield path


def _offenders():
    found = []
    for path in _sources():
        try:
            source = path.read_text(encoding='utf-8-sig')
        except OSError:  # pragma: no cover
            continue
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                compile(source, str(path), 'exec')
            except SyntaxError:  # a different problem, and a louder one
                continue
            for entry in caught:
                if 'invalid escape sequence' in str(entry.message):
                    found.append(
                        f'{path.relative_to(ROOT).as_posix()}:{entry.lineno}  '
                        f'{entry.message}')
    return found


def test_no_source_file_has_an_invalid_escape_sequence():
    """The one that matters.

    An invalid escape is a SyntaxError from Python 3.14. Until then it is a
    warning that everyone scrolls past -- which is exactly how it survives
    long enough to become a build failure.

    The fix is almost always to make the string raw (r'...'), which is also
    what you wanted if it contains a regex.
    """
    offenders = _offenders()
    assert not offenders, (
        'these contain escape sequences Python does not recognise:\n  '
        + '\n  '.join(offenders)
        + "\n\nPython 3.14 turns these into SyntaxError and the module stops "
          "importing. Make the string raw -- r'...' -- or double the "
          "backslash.")


def test_this_guard_can_see_the_files_it_judges():
    """A sweep that compiles nothing reports nothing and passes, which looks
    exactly like a repository with no invalid escapes."""
    files = list(_sources())
    assert len(files) > 20, f'only {len(files)} python file(s) found under {ROOT}'


def test_the_sweep_actually_detects_one():
    """Guard the guard, in the direction that matters.

    A warnings filter set elsewhere in the suite, or a Python that stops
    reporting these, would make the sweep above silently blind. So an
    offender is compiled on purpose and must be seen.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        compile('x = "\\{"\n', '<probe>', 'exec')
        seen = [w for w in caught if 'invalid escape sequence' in str(w.message)]
    assert seen, (
        'compiling a known-bad escape produced no warning, so the sweep in '
        'this file cannot detect one either. Check whether a warnings filter '
        'is being applied suite-wide.')
