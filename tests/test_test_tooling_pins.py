"""RNV-TEST-TOOLING-GUARD -- the five applications share one interpreter, so
their dev-tooling ranges have to be mutually satisfiable.

Installed 2026-09-07. Until today they were not, and it was arithmetic rather
than a matter of taste:

    pytest       picker  ==9.0.2      icon builder  >=8.0.0,<9.0.0
    pytest-cov   picker  ==7.1.0      icon builder  >=5.0.0,<7.0.0

No version of pytest is both exactly 9.0.2 and below 9.0.0. On a development
machine -- one interpreter, five checkouts -- installing one repository's dev
requirements and then the other's UNINSTALLS pytest 9 and installs pytest 8,
and going back undoes it. While pip is mid-swap the _pytest package on disk is
partially populated, which is where

    ModuleNotFoundError: No module named '_pytest.compat'

comes from, seconds after the same command had just succeeded. No install
order avoids it. The constraint itself was impossible.

WHAT THIS FILE GUARDS. Four things, in the order they are likely to break:

  1. This repository's ranges are still the fleet's.
  2. Every file in this repository that declares them agrees with the others.
     Both pyproject.toml files in the fleet SAY IN A COMMENT that they mirror
     tests/requirements-dev.txt. Nothing checked it. Now something does.
  3. No exact `==` pin has come back. That is the mechanism, not the symptom:
     an exact pin on a shared tool makes one repository fight the other four
     every time anything moves.
  4. The pytest actually running this test satisfies what the file declares.
     Points 1 to 3 read files; this one looks at the machine, and it is the
     one that would have caught the failure that started all this.

WHAT IT CANNOT DO. A test in this repository cannot see the other four. If
someone edits a range here, this fails here -- which is the point. If someone
edits it in all five identically, that is a fleet decision and this agrees
with it, as it should.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The fleet standard, identical in all five applications. The floor of each
#: is the highest floor any of the five already declared; the ceiling is the
#: next MAJOR version, so nothing crosses a major boundary without an edit.
#:
#: Measured at the top, not assumed: every one of the five suites was run on
#: pytest 9.1.1, pytest-qt 4.5.0, pytest-cov 7.1.0, pytest-timeout 2.4.0 and
#: pytest-benchmark 5.3.0 -- the exact set a fresh install resolves these to.
FLEET = {
    'pytest': '>=8.0,<10.0',
    'pytest-qt': '>=4.4,<5.0',
    'pytest-cov': '>=5.0,<8.0',
    'pytest-timeout': '>=2.4,<3.0',
    'pytest-benchmark': '>=4.0,<6.0',
}

#: Every file in THIS repository that may declare them. Absent ones are
#: skipped: the five do not all use the same layout, and a repository that
#: has no pyproject.toml is not thereby in breach.
#:
#: THE RETIRED ROOT-LEVEL requirements-dev PATH IS DELIBERATELY NOT HERE. All
#: six RNV repositories moved that file under tests/, and
#: tests/test_dependency_file_placement.py sweeps the tree to keep it moved.
#: The first build of this file listed the root path as a candidate 'just in
#: case', which is how a retired path comes back -- and that sweep caught it,
#: which is exactly what it is for. (Named without its extension here on
#: purpose: the sweep is scoped to the filename WITH extension so that prose
#: can still discuss it.)
CANDIDATES = ('tests/requirements-dev.txt', 'requirements.txt',
              'pyproject.toml')

_LINE = re.compile(
    r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
    r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')


def _declared(path: Path) -> dict:
    """The test-tooling requirements in one file, as {name: specifier}."""
    found = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.lstrip().startswith('#'):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in FLEET:
            found[name] = match.group(2).strip().replace(' ', '').rstrip('",')
    return found


def _files():
    return [ROOT / rel for rel in CANDIDATES if (ROOT / rel).exists()]


def test_the_ranges_are_the_fleet_s():
    """Every test-tooling requirement this repository declares, anywhere, is
    the one all five agree on."""
    wrong = []
    for path in _files():
        for name, spec in _declared(path).items():
            if spec != FLEET[name]:
                wrong.append(
                    f'{path.relative_to(ROOT).as_posix()}: {name}{spec} '
                    f'(fleet: {name}{FLEET[name]})')
    assert not wrong, (
        'these ranges have drifted from the fleet standard:\n  '
        + '\n  '.join(wrong)
        + '\n\nThe five applications share one interpreter. A range only this '
          'repository holds is a range that fights the other four, and pip '
          'resolves that fight by rewriting site-packages.')


def test_the_declaring_files_in_this_repository_agree():
    """pyproject.toml and tests/requirements-dev.txt say the same thing.

    Both pyproject files in the fleet carry a comment claiming exactly this.
    A comment is a promise; this is the part that keeps it.
    """
    per_file = {p.relative_to(ROOT).as_posix(): _declared(p) for p in _files()}
    disagreements = []
    names = {n for d in per_file.values() for n in d}
    for name in sorted(names):
        specs = {rel: d[name] for rel, d in per_file.items() if name in d}
        if len(set(specs.values())) > 1:
            disagreements.append(
                f'{name}: ' + ', '.join(f'{r} says {s}' for r, s in specs.items()))
    assert not disagreements, (
        'two files in this repository declare different versions of the same '
        'package:\n  ' + '\n  '.join(disagreements)
        + '\n\nWhichever one you install from wins, and which one that is '
          'depends on the command someone happened to type.')


def test_no_exact_pin_came_back():
    """`==` is the mechanism, not the symptom.

    An exact pin on a tool five repositories share means this one demands a
    version the others merely tolerate. It is right for a lock file, which
    is regenerated, and wrong for dev requirements that are read by hand.
    """
    exact = []
    for path in _files():
        for name, spec in _declared(path).items():
            if spec.startswith('=='):
                exact.append(f'{path.relative_to(ROOT).as_posix()}: {name}{spec}')
    assert not exact, (
        'exact pins on shared test tooling:\n  ' + '\n  '.join(exact)
        + '\n\nUse a range with a major-version ceiling instead.')


def test_every_range_has_an_upper_bound():
    """A ceiling is the whole reason these are ranges and not floors.

    Without one, the next major release of pytest lands silently on the first
    machine that installs after it ships, and the first anyone knows is a
    suite failing on a commit that changed nothing.
    """
    unbounded = []
    for path in _files():
        for name, spec in _declared(path).items():
            if '<' not in spec:
                unbounded.append(
                    f'{path.relative_to(ROOT).as_posix()}: {name}{spec}')
    assert not unbounded, (
        'these declare a floor and no ceiling:\n  ' + '\n  '.join(unbounded)
        + '\n\nAdd a major-version ceiling.')


def test_the_installed_pytest_satisfies_what_this_repository_declares():
    """The one that looks at the machine rather than the files.

    Everything above reads text. This asks whether the pytest currently
    running is the pytest this repository asked for -- and a mismatch here
    means the last `pip install` someone ran was for a different repository.
    """
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:  # pragma: no cover -- packaging ships with pytest
        pytest.skip('packaging is not importable')

    # EVERY declaring file, separately. Merging them into one dict lets
    # whichever file sorts last overwrite the others, and the file that
    # loses is tests/requirements-dev.txt -- the one people actually
    # install from. The first build of this guard did exactly that and
    # reported green against a range it was not testing.
    running = Version(pytest.__version__)
    declared = [(path.relative_to(ROOT).as_posix(), spec['pytest'])
                for path, spec in ((p, _declared(p)) for p in _files())
                if 'pytest' in spec]
    if not declared:
        pytest.skip('this repository declares no pytest requirement')

    outside = [f'{rel} declares pytest{spec}'
               for rel, spec in declared
               if running not in SpecifierSet(spec)]
    assert not outside, (
        f'pytest {running} is running, but:\n  ' + '\n  '.join(outside)
        + '\n\nOn a machine with all five checkouts this usually means the '
          'last `pip install -r tests/requirements-dev.txt` you ran was in a '
          'different repository. Re-run it here:\n\n'
          '    python -m pip install -r tests/requirements-dev.txt')


def test_this_guard_can_see_the_files_it_judges():
    """Guard the guard. A parser that matches nothing finds no drift and
    passes, which looks exactly like a repository in perfect order."""
    files = _files()
    assert files, f'no requirements files found under {ROOT}'
    total = sum(len(_declared(p)) for p in files)
    assert total >= 2, (
        f'only {total} test-tooling requirement(s) were parsed out of '
        f'{[p.name for p in files]}. Every one of the five declares at least '
        f'pytest and pytest-qt, so this parser is not reading what it thinks.')
