"""RNV-DEPENDENCY-COHERENCE-GUARD -- one repository, one answer per package.

Installed 2026-09-07, as the second half of the pytest round. That round
fixed the conflict that was actively breaking:

    pytest       picker  ==9.0.2      icon builder  >=8.0.0,<9.0.0

No version is both. On one interpreter, pip rewrote site-packages on every
switch between those two repositories, and a half-rewritten _pytest package
is where `ModuleNotFoundError: No module named '_pytest.compat'` came from.

This file guards the same CLASS of defect in the packages that had not yet
bitten -- and one of them is PyQt6, where it would have cost a great deal
more than a morning.

WHAT THIS FILE GUARDS.

  1. Two files in this repository do not declare different ranges for the
     same package. Six such disagreements existed across the fleet. Both
     pyproject.toml files in it carry a comment SAYING they mirror the
     requirements; a comment is a promise, and this is the part that keeps
     it. Whichever file you install from wins, and which one that is
     depends on the command somebody happened to type.
  2. No exact `==` pin. Two were left -- PyQt6==6.10.2 and
     hypothesis==6.152.4, both in rnv-color-picker. Neither was breaking
     anything, which is the point: neither was pytest==9.0.2 either, until
     the day another repository disagreed with it.
  3. Pillow matches the range all five share. It is the one package with a
     DATED deadline behind it: the old pixel-access method is removed in
     Pillow 14 on 2027-10-15, and `get_flattened_data` -- the replacement
     that utils/pil_compat.py prefers -- arrived in Pillow 12.1. The old
     `<12.0` cap excluded it.

     (Named indirectly on purpose. tests/test_pil_compat.py sweeps every
     file for the retired call and this one is not exempt from that sweep,
     so writing the call form here -- even in prose -- fails it. Use versus
     mention, and this file was the tenth instance in this programme.)
  4. What is installed satisfies what is declared. Everything above reads
     text; this one looks at the machine, and it is the shape of check that
     would have caught the failure that started all this.

WHAT IT DELIBERATELY DOES NOT DO.

  It does not require every range to have a ceiling, and it does not require
  the five to agree on floors other than Pillow's. Applications legitimately
  support different minimum versions of the same library. What they may not
  do is contradict themselves, pin exactly, or make a version no combination
  can satisfy.

  The test-tooling packages are excluded here. They have a fleet standard of
  their own and their own guard, tests/test_test_tooling_pins.py, because a
  tool five repositories run on one interpreter is a different question from
  a library one application imports.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The one package with a fleet-wide range this round. See the docstring for
#: why it is the one: a dated removal, and an API the fleet has already
#: adopted that the old cap excluded.
FLEET = {'pillow': '>=10.0.0,<13.0'}

#: Governed by tests/test_test_tooling_pins.py instead. Checking them here
#: as well would mean two files disagreeing about the same thing, which is
#: the exact failure this one exists to prevent.
TEST_TOOLING = {'pytest', 'pytest-qt', 'pytest-cov', 'pytest-timeout',
                'pytest-benchmark'}

#: Lines that look like a requirement and are not. `line-length = 100` in
#: ruff's config and `precision = 0` in coverage's both parse as a name
#: followed by a number, and a sweep that rewrote them would break the tool
#: rather than the pin.
NOT_REQUIREMENTS = {'line-length', 'precision', 'python', 'name', 'version',
                    'requires-python', 'description', 'target-version'}

CANDIDATES = ('pyproject.toml', 'requirements.txt',
              'tests/requirements-dev.txt')

_LINE = re.compile(
    r'^(?:\s*"?)([A-Za-z0-9_.-]+)'
    r'(\s*(?:[<>=!~]=?\s*[0-9][^,"#\n]*)(?:\s*,\s*[<>=!~]=?\s*[0-9][^,"#\n]*)*)')


def _declared(path: Path) -> dict:
    """The dependencies one file declares, as {name: specifier}."""
    found = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.lstrip().startswith('#'):
            continue
        match = _LINE.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in NOT_REQUIREMENTS or name in TEST_TOOLING:
            continue
        found[name] = match.group(2).strip().replace(' ', '').rstrip('",')
    return found


def _files():
    return [ROOT / rel for rel in CANDIDATES if (ROOT / rel).exists()]


def _per_file():
    return {p.relative_to(ROOT).as_posix(): _declared(p) for p in _files()}


def test_this_repository_does_not_contradict_itself():
    """One package, one answer.

    Six of these existed across the five applications. None of them broke
    anything on its own -- they decide which range applies based on which
    file somebody installed from, which is a coin flip dressed as a
    declaration.
    """
    per_file = _per_file()
    disagreements = []
    for name in sorted({n for d in per_file.values() for n in d}):
        specs = {rel: d[name] for rel, d in per_file.items() if name in d}
        if len(set(specs.values())) > 1:
            disagreements.append(
                f'{name}: ' + ', '.join(f'{r} says {s}' for r, s in specs.items()))
    assert not disagreements, (
        'two files in this repository declare different ranges for the same '
        'package:\n  ' + '\n  '.join(disagreements)
        + '\n\nWhichever one you install from wins, and which one that is '
          'depends on the command someone happened to type.')


def test_no_dependency_is_pinned_exactly():
    """`==` is the mechanism behind the pytest failure, not the symptom.

    An exact pin means this repository demands a version the others merely
    tolerate. Installing it downgrades or upgrades the package for every
    checkout sharing that interpreter, and the window while pip is mid-swap
    is a partially-populated package on disk.

    It is right in a lock file, which is regenerated. It is wrong in a
    declaration that is read by hand.
    """
    exact = []
    for rel, declared in _per_file().items():
        for name, spec in declared.items():
            if spec.startswith('=='):
                exact.append(f'{rel}: {name}{spec}')
    assert not exact, (
        'exact pins:\n  ' + '\n  '.join(exact)
        + '\n\nUse a range whose floor is the version you know works.')


def test_pillow_matches_the_range_all_five_share():
    """The one package with a dated deadline behind it.

    Pillow 14 removes the old pixel-access method on 2027-10-15.
    `get_flattened_data`, which utils/pil_compat.py prefers, arrived in
    Pillow 12.1 -- so the old `<12.0` cap excluded the API the fleet had
    just adopted. The ceiling is what makes somebody look before 14 lands.
    """
    wrong = []
    for rel, declared in _per_file().items():
        for name, want in FLEET.items():
            if name in declared and declared[name] != want:
                wrong.append(f'{rel}: {name}{declared[name]} (fleet: {name}{want})')
    assert not wrong, (
        'these have drifted from the range all five applications share:\n  '
        + '\n  '.join(wrong))


def test_what_is_installed_satisfies_what_is_declared():
    """The one that looks at the machine rather than the files.

    A package that is not installed is skipped -- plenty of these are
    optional development tools. A package installed at a version this
    repository forbids is a real disagreement between the declaration and
    the environment, and one of the two is wrong.
    """
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:  # pragma: no cover -- packaging ships with pytest
        pytest.skip('packaging is not importable')
    from importlib.metadata import PackageNotFoundError, version as installed_version

    # Every declaring file separately. Merging them into one mapping lets
    # whichever file sorts last silently overwrite the others, and then the
    # check reports green against a range it never tested.
    outside = []
    for rel, declared in _per_file().items():
        for name, spec in sorted(declared.items()):
            try:
                have = Version(installed_version(name))
            except PackageNotFoundError:
                continue
            except Exception:               # pragma: no cover
                continue
            if have not in SpecifierSet(spec):
                outside.append(f'{rel} declares {name}{spec}, but {have} is installed')
    assert not outside, (
        'the environment does not match the declarations:\n  '
        + '\n  '.join(outside)
        + '\n\nEither the declaration is wrong or the install is stale:\n\n'
          '    python -m pip install -r requirements.txt')


def test_this_guard_can_see_the_files_it_judges():
    """Guard the guard. A parser that matches nothing finds no disagreement
    and passes, which looks exactly like a repository in perfect order."""
    files = _files()
    assert files, f'no dependency files found under {ROOT}'
    total = sum(len(_declared(p)) for p in files)
    assert total >= 3, (
        f'only {total} dependency declaration(s) parsed out of '
        f'{[p.name for p in files]}. Every one of the five declares at least '
        f'PyQt6 and Pillow, so this parser is not reading what it thinks.')


def test_a_tool_setting_is_not_read_as_a_dependency():
    """The exclusion list, tested by behaviour rather than by census.

    `line-length = 100` in ruff's config and `precision = 0` in coverage's
    both parse as a name followed by a comparison and a number -- the regex
    cannot tell them from `chardet >= 5.2.0`, because structurally they are
    the same. A sweep without the exclusion would report ruff's config as a
    dependency disagreement, and a REWRITE without it would set
    `line-length` to a version range.

    Driven with a stand-in file rather than asserted against this
    repository's, so it holds whether or not this particular repository
    happens to configure those tools today.
    """
    import tempfile
    sample = ('[tool.ruff]\n'
              'line-length = 100\n'
              'target-version = "py311"\n'
              '\n'
              '[tool.coverage.report]\n'
              'precision = 0\n'
              '\n'
              'dependencies = [\n'
              '    "Pillow>=10.0.0,<13.0",\n'
              ']\n')
    with tempfile.NamedTemporaryFile('w', suffix='.toml', delete=False,
                                     encoding='utf-8') as handle:
        handle.write(sample)
        path = Path(handle.name)
    try:
        found = _declared(path)
    finally:
        path.unlink()
    assert 'line-length' not in found, 'ruff config read as a dependency'
    assert 'precision' not in found, 'coverage config read as a dependency'
    assert found.get('pillow') == '>=10.0.0,<13.0', (
        f'the parser missed the real requirement in the same file: {found}')
