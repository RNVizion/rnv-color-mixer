"""RNV-IMAGE-BUDGET-GUARD -- the resources stay the size they were reduced to.

Installed 2026-09-08. This repository shipped a window background of
16000x9038 (or 8000x4500) and a settings gear of 3334x3334 for a button that
renders at 50x50. Across the five applications that was 537 MB of pixels
reproducing, for the most part, flat geometric shapes.

The backgrounds are now 3840 on the long edge -- a full 4K width, so a
maximised window on a 4K display still scales DOWN rather than up -- and the
oversized square assets are 512.

WHAT THIS GUARD IS FOR. Nothing about a resize sticks. The next export from a
design tool lands at whatever that tool defaults to, the file is committed
because it looks right, and the repository quietly grows back. A dimension is
checkable, so it is checked.

WHAT IT DELIBERATELY DOES NOT COVER. The action buttons and the screenshots.
The action buttons are already 0.2-0.4 MB and sized for the widgets they
fill -- a rule that squeezed their long edge would crush their short one,
which is how a 1250x146 button becomes 512x60 and looks wrong on a HiDPI
screen. The screenshots are 1920x1080 documentation. Neither is a problem, so
neither is governed here.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: glob -> the largest edge this asset may have, and why that number.
BUDGET = (
    ('resources/background_images/*.png', 3840,
     'a window background; 3840 is a full 4K width, so even a maximised '
     'window on a 4K display scales it down rather than up'),
    ('resources/button_images/settings_gear_*.png', 512,
     'renders inside a 50x50 button; 512 leaves headroom for 3x HiDPI '
     'several times over'),
    ('resources/icons/icon.png', 512,
     'the window and dock icon; 512 is the largest size any desktop asks for'),
    ('resources/icons/special_slot.png', 512, 'a slot badge'),
)

#: A file over this, in a directory the budget governs, is the thing that
#: went wrong. Stated separately from the dimensions because a file can be
#: the right dimensions and still be enormous if it was saved badly.
MAX_BYTES = 16 * 1024 * 1024


def _governed():
    for pattern, limit, why in BUDGET:
        for path in sorted(ROOT.glob(pattern)):
            yield path, limit, why


def test_every_governed_asset_is_within_its_budget():
    """The one that matters.

    A dimension is the cheapest possible check and the whole reason the
    reduction holds: the next re-export from a design tool will be whatever
    that tool defaults to, and nobody looks at a file size in a diff.
    """
    pytest.importorskip('PIL', reason='Pillow is a declared dependency')
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None

    over = []
    for path, limit, why in _governed():
        with Image.open(path) as image:
            longest = max(image.width, image.height)
        if longest > limit:
            over.append(
                f'{path.relative_to(ROOT).as_posix()}  {image.width}x{image.height}'
                f'  (limit {limit} on the long edge — {why})')
    assert not over, (
        'these assets are larger than the size anything renders them at:\n  '
        + '\n  '.join(over)
        + '\n\nResize in place; the path must not move.')


def test_no_governed_asset_is_absurdly_heavy():
    """Dimensions and bytes are different failures.

    A 3840px PNG saved without optimisation, or as 16-bit, is the right shape
    and still ten times the weight. This catches that without pretending to
    know what a good size is.
    """
    heavy = [f'{p.relative_to(ROOT).as_posix()}  {p.stat().st_size / 1e6:.1f} MB'
             for p, _limit, _why in _governed() if p.stat().st_size > MAX_BYTES]
    assert not heavy, (
        'these are within their dimensions but very heavy:\n  '
        + '\n  '.join(heavy)
        + f'\n\nThe ceiling is {MAX_BYTES / 1e6:.0f} MB. Check the save '
          f'settings rather than the dimensions.')


def test_the_budget_still_matches_real_files():
    """Guard the guard, both ways.

    A glob that matches nothing passes every assertion above, which looks
    exactly like a repository in good order. And an entry that has stopped
    matching is a rule with no subject -- worth deleting deliberately rather
    than leaving to pass over silence.
    """
    empty = [pattern for pattern, _l, _w in BUDGET
             if not list(ROOT.glob(pattern))]
    assert not empty, (
        'these budget entries match no file in this repository:\n  '
        + '\n  '.join(empty)
        + '\n\nIf the asset was retired, remove its entry in the same commit.')


def test_the_assets_are_where_they_were():
    """No path moved.

    The reduction was done in place on purpose: this project's standing
    instruction is that the image directories are correct and are not to be
    rearranged. A resize that also relocated a file would be a much larger
    change wearing a smaller one's clothes.
    """
    for directory in ('resources/background_images', 'resources/button_images',
                      'resources/icons'):
        assert (ROOT / directory).is_dir(), (
            f'{directory} is missing. The image resize was done in place and '
            f'must not have moved anything.')
