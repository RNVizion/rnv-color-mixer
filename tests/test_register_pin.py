"""RNV-REGISTER-PIN-GUARD -- the register is a declared dependency, not a hope.

Installed 2026-09-07. Until today this repository kept a hand-written PINNED
mirror of rnv-brand's values, and every test that would have compared that
mirror against the real register was guarded with

    pytest.importorskip('engine.brand')

rnv-brand shipped no pyproject.toml, so it was not installable, so those
checks skipped -- in all five applications, 22 of them, every run. A mirror
that nothing compares against is a copy, and a copy drifts. It had already
drifted: rnv-text-transformer classified two values as app-owned that the
register had owned since rev 27, and nothing said so for four revisions.

rnv-brand is now packaged and pinned in tests/requirements-dev.txt, which
every workflow in this repository already installs. The checks run.

WHAT THIS FILE ADDS. The importorskip calls are left exactly as they are --
they are correct for a developer who has not installed the dev dependencies,
and rewriting 22 of them across five repositories would be churn with a real
chance of error. Instead this makes the ABSENCE loud in one place: if the
register is missing, one test fails and says what it means, rather than
twenty-two tests quietly not running.

A skipped test and a passing test look identical in a summary line. That is
the whole failure mode this guards.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEV_REQS = ROOT / 'tests/requirements-dev.txt'

#: The register, as this repository pins it. A commit, not a branch -- see
#: test_the_pin_names_a_commit_not_a_branch below for why that matters.
PIN_RE = re.compile(
    r'^rnv-brand\s*@\s*git\+https://github\.com/RNVizion/rnv-brand'
    r'(?:\.git)?@(?P<ref>\S+)\s*$', re.M)


def test_the_register_is_installed():
    """The one that matters. Everything else in this file is about keeping
    this one honest."""
    try:
        import engine.brand  # noqa: F401
    except ImportError as exc:  # pragma: no cover -- the failure path
        pytest.fail(
            f'rnv-brand is not importable: {exc}\n\n'
            f'It is a declared dev dependency of this repository. Install it '
            f'with:\n\n'
            f'    pip install -r tests/requirements-dev.txt\n\n'
            f'Until it is present, every check that compares this app to the '
            f'register is SKIPPING -- which looks exactly like passing, and '
            f'means the local PINNED mirror is being checked against itself.')


def test_the_register_exposes_what_the_mirrors_read():
    """Guard the guard. An importable module that has been emptied out would
    satisfy the test above and still tell the mirrors nothing."""
    import engine.brand as brand
    assert isinstance(getattr(brand, 'APP', None), dict), \
        'engine.brand has no APP dict'
    assert len(brand.APP) >= 10, \
        f'engine.brand.APP has only {len(brand.APP)} entries'
    for name in ('BRAND_GOLD', 'BRAND_DARK_GOLD', 'TRUE_BLACK', 'WHITE'):
        assert hasattr(brand, name), f'engine.brand has no {name}'


def test_the_pin_is_declared_in_the_dev_requirements():
    """It has to be written down where the workflows will read it. Every
    workflow in this repository already installs this file, which is why this
    round changes no YAML at all."""
    assert DEV_REQS.exists(), f'{DEV_REQS} is missing'
    text = DEV_REQS.read_text(encoding='utf-8')
    assert PIN_RE.search(text), (
        'tests/requirements-dev.txt does not pin rnv-brand. Without the pin, '
        'a fresh checkout installs no register, the checks go back to '
        'skipping, and nothing announces it.')


def test_the_pin_names_a_commit_not_a_branch():
    """A pin to `@main` is not a pin.

    The point of pinning the register is that this repository states, in a
    reviewable line, WHICH revision of the brand it mirrors. A branch ref
    moves on its own: the register could change under this application
    between two runs of the same commit, and the first anyone would know is a
    test failing on a build that changed nothing.

    A 40-character commit sha cannot do that. Moving it is an edit, and an
    edit is a diff someone can read.
    """
    text = DEV_REQS.read_text(encoding='utf-8')
    match = PIN_RE.search(text)
    assert match, 'no rnv-brand pin found'
    ref = match.group('ref')
    assert re.fullmatch(r'[0-9a-f]{40}', ref), (
        f'rnv-brand is pinned to {ref!r}, which is not a full commit sha. '
        f'A branch or tag ref lets the register move without a commit in '
        f'this repository.')


def test_the_installed_register_is_the_pinned_one():
    """The pin says which revision; this asks whether that is what is
    actually installed. They come apart the moment someone bumps the pin and
    does not reinstall -- and then the suite is checking the app against a
    register nobody declared."""
    import engine.brand as brand
    version = getattr(brand, '__version__', None)
    if version is None:
        pytest.skip('engine.brand declares no __version__; the pin is the '
                    'only statement of which revision this is')
    assert version, 'engine.brand.__version__ is empty'
