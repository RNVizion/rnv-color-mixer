"""RNV-PIL-COMPAT-GUARD -- getdata() is removed in Pillow 14, and this is why
nothing here calls it.

Installed 2026-09-07. `Image.getdata()` was deprecated in Pillow 12.1 and is
removed in Pillow 14, dated 2027-10-15. Every call site now goes through
utils.pil_compat.flat_pixels, which picks the available API at runtime.

WHAT MAKES THIS GUARD HARD TO WRITE HONESTLY. Whichever Pillow the suite runs
on, only ONE branch of the helper executes. A test that exercises the
installed branch and reports green says nothing about the other one -- and the
other one is the one that matters, because it is either the future (removal)
or the past (every version this project still supports). So both branches are
driven explicitly, with stand-in objects, rather than being left to whichever
Pillow happens to be installed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image

from utils.pil_compat import flat_pixels

ROOT = Path(__file__).resolve().parent.parent

#: The one file allowed to name the deprecated API, plus the tests that must
#: mention it to talk about it.
ALLOWED = ('utils/pil_compat.py', 'tests/test_pil_compat.py')


def _images():
    base = Image.new('RGB', (3, 2), (10, 20, 30))
    return {'RGB': base,
            'RGBA': base.convert('RGBA'),
            'L': base.convert('L'),
            'P': base.convert('P')}


@pytest.mark.parametrize('mode', ['RGB', 'RGBA', 'L', 'P'])
def test_flat_pixels_matches_the_api_this_pillow_has(mode):
    """Whatever this Pillow provides, the helper returns exactly it."""
    image = _images()[mode]
    getter = getattr(image, 'get_flattened_data', None)
    expected = list(getter() if getter is not None else image.getdata())
    assert flat_pixels(image) == expected
    assert len(flat_pixels(image)) == image.width * image.height


class _OldPillow:
    """An image object as Pillow 10 through 12.0 present one: getdata, and no
    get_flattened_data. Driving this explicitly is the only way to exercise
    the fallback on a machine running 12.1 or later."""

    def __init__(self, data):
        self._data = data
        self.calls = 0

    def getdata(self):
        self.calls += 1
        return iter(self._data)


class _NewPillow:
    """And the other side: get_flattened_data present. On an older Pillow this
    is the only way to exercise the branch that will be the ONLY branch once
    Pillow 14 removes getdata entirely."""

    def __init__(self, data):
        self._data = data
        self.calls = 0

    def get_flattened_data(self):
        self.calls += 1
        return iter(self._data)

    def getdata(self):  # pragma: no cover -- must never be reached
        raise AssertionError(
            'flat_pixels called getdata() on an object that has '
            'get_flattened_data. After Pillow 14 that method is gone.')


def test_the_old_api_is_used_when_it_is_the_only_one():
    data = [(1, 2, 3), (4, 5, 6)]
    old = _OldPillow(data)
    assert flat_pixels(old) == data
    assert old.calls == 1


def test_the_new_api_is_preferred_when_present():
    data = [(1, 2, 3), (4, 5, 6)]
    new = _NewPillow(data)
    assert flat_pixels(new) == data
    assert new.calls == 1


def test_the_result_is_a_list_not_a_generator():
    """Callers index it, take len() of it, and iterate it more than once.
    Both underlying APIs can return something lazy."""
    result = flat_pixels(_OldPillow([(1, 2, 3), (4, 5, 6)]))
    assert isinstance(result, list)
    assert len(result) == 2
    assert list(result) == list(result)


def test_no_source_file_calls_getdata_directly():
    """The point of the helper. A call that bypasses it is a call that stops
    working on 2027-10-15, and it will not announce itself -- the deprecation
    warning is silent in a passing suite."""
    offenders = []
    for path in sorted(ROOT.rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED or rel.startswith(('build/', '.venv/')):
            continue
        if path.parent == ROOT and path.name.startswith('up'):
            continue          # a delivery script names what it moves
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            if re.search(r'\.getdata\s*\(', line):
                offenders.append(f'{rel}:{lineno}  {line.strip()[:70]}')
    assert not offenders, (
        'these call Image.getdata() directly, which Pillow 14 removes on '
        '2027-10-15:\n  ' + '\n  '.join(offenders)
        + '\n\nUse utils.pil_compat.flat_pixels instead.')


def test_the_sweep_above_can_see_this_repository():
    """Guard the guard. A sweep that walks no files finds no offenders and
    passes, which looks exactly like a clean repository."""
    seen = [p for p in ROOT.rglob('*.py')
            if not p.relative_to(ROOT).as_posix().startswith(('build/', '.venv/'))]
    assert len(seen) > 20, f'only {len(seen)} python files found under {ROOT}'


def test_the_helper_is_reached_from_where_it_is_needed():
    """The other direction: the sweep only proves nothing calls the old API.
    This proves something calls the new one -- otherwise deleting every call
    site would also pass."""
    users = []
    for path in sorted(ROOT.rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(('tests/', 'build/', '.venv/')) or rel == 'utils/pil_compat.py':
            continue
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        if 'flat_pixels' in text:
            users.append(rel)
    assert users, ('nothing imports flat_pixels. Either the call sites were '
                   'removed, or the helper was installed and never wired.')
