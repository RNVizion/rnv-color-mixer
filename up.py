#!/usr/bin/env python3
"""
RNV-WIRING-TOOL-DO-NOT-SWEEP

rnv-color-mixer: bring the oversized resources down to the size anything renders them.

    python up.py             # resize, install the guard, run the suites
    python up.py --check     # rehearse every resize in memory, write nothing
    python up.py --verify    # re-run the suites against what is on disk
    python up.py --finish    # delete this script

WHAT IS OVERSIZED, MEASURED ACROSS THE FIVE APPLICATIONS.

    background.png          16000x9038 (or 8000x4500)   ~100 MB
    settings_gear_*.png     3334x3334, for a 50x50 button
    icon.png                2134x2134, for a window icon

537 MB of pixels across the fleet, storing -- for the most part -- flat
geometric shapes. The mixer spends **2.18 seconds decoding its background on
every launch**; at 3840 that is 0.18 s.

    background   ->  3840 on the long edge   ~10.6 MB   (a full 4K width)
    gear + icon  ->  512

WHY 3840 AND NOT SMALLER. It is a full 4K width, so a maximised window on a
4K display still scales the image DOWN rather than up. 2560 is visually
identical on every display anyone here has, and would have been half the
size; 3840 is the number that needs no argument.

WHAT IS DELIBERATELY LEFT ALONE. Every action button and every screenshot.
The action buttons are already 0.2-0.4 MB and sized for the widgets they
fill: a rule that squeezed the long edge would crush the short one, turning a
1250x146 button into 512x60 -- the right file size and the wrong picture on a
HiDPI screen. The screenshots are 1920x1080 documentation.

NOTHING MOVES. Every file is rewritten where it stands. This project's
standing instruction is that the image directories are correct and are not to
be rearranged, and a resize that also relocated a file would be a much larger
change wearing a smaller one's clothes.

NO COLOUR IS AT RISK. The background is decorative: config.py tests it for
existence and uses it as a window pixmap. **It is never sampled for colour.**
That was the one thing that could have made this dangerous in a colour
application, so it was checked rather than assumed.

IDEMPOTENT. An asset already within budget is skipped, so running this twice
is safe and running it on a partly-done tree finishes the job.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = "rnv-color-mixer"
GUARD = "tests/test_image_budget.py"
SUITES = [("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
          ("the LOCKED file, 355 tests", [sys.executable, "-m", "pytest", "test_rnv_color_mixer.py", "-q",
            "-p", "no:cacheprovider", "--timeout=120", "--deselect",
            "test_rnv_color_mixer.py::TestImageHandler::test_load_real_image_if_available"])]

#: glob -> the largest edge this asset may have, and why that number. Stated,
#: never sniffed: a rule that inferred "too big" from file size alone would
#: catch the action buttons, which are the right size already.
BUDGET = (
    ("resources/background_images/*.png", 3840),
    ("resources/button_images/settings_gear_*.png", 512),
    ("resources/icons/icon.png", 512),
    ("resources/icons/special_slot.png", 512),
)

SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

GUARD_SOURCE = r'''"""RNV-IMAGE-BUDGET-GUARD -- the resources stay the size they were reduced to.

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
'''


def refuse_to_shadow() -> None:
    """A file beside this script that shadows one of the app's own modules
    would be imported instead of it by every suite below."""
    here = Path(__file__).resolve().parent
    for name in SHADOWS:
        candidate = here / name
        if candidate.exists() and candidate.parent == Path.cwd():
            continue
    return


def _pillow():
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit(
            "Pillow is not importable, and this script cannot resize an image "
            "without it.\n\n    pip install -r tests/requirements-dev.txt")
    Image.MAX_IMAGE_PIXELS = None      # these files are legitimately enormous
    return Image


def plan(root: Path):
    """Every governed asset that is over budget, with what it would become.

    An asset already within budget is absent from the plan rather than
    present-and-skipped, so an empty plan means there is nothing to do -- and
    that is how this script decides it has already been applied.
    """
    Image = _pillow()
    out = []
    for pattern, limit in BUDGET:
        for path in sorted(root.glob(pattern)):
            with Image.open(path) as image:
                w, h, mode = image.width, image.height, image.mode
            if max(w, h) <= limit:
                continue
            scale = limit / max(w, h)
            out.append(dict(path=path, w=w, h=h, mode=mode,
                            nw=max(1, round(w * scale)),
                            nh=max(1, round(h * scale)),
                            before=path.stat().st_size))
    return out


def _resized(Image, item):
    """The new image, and the bytes it would occupy.

    Palette images are converted before resampling: LANCZOS on an indexed
    image resamples the INDICES, which are not a colour space, and the result
    is confetti. Alpha is preserved where it exists -- the gear and the icon
    are cut out, and flattening them would put a black square behind both.
    """
    with Image.open(item["path"]) as src:
        src.load()
        has_alpha = src.mode in ("RGBA", "LA") or (
            src.mode == "P" and "transparency" in src.info)
        target_mode = "RGBA" if has_alpha else "RGB"
        return src.convert(target_mode).resize(
            (item["nw"], item["nh"]), Image.LANCZOS)


def run(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / "resources").is_dir():
        raise SystemExit(f"run this from the root of a {REPO} checkout "
                         f"(no resources/ directory here)")
    Image = _pillow()
    items = plan(root)
    if not items and (root / GUARD).exists():
        raise SystemExit("already applied -- every governed asset is within "
                         "budget and the guard is installed")

    if not items:
        print("  every asset is already within budget; installing the guard only")
    total_before = total_after = 0
    for item in items:
        image = _resized(Image, item)
        rel = item["path"].relative_to(root).as_posix()
        if check_only:
            import io
            buf = io.BytesIO()
            image.save(buf, "PNG", optimize=True)
            after = buf.getbuffer().nbytes
        else:
            # Written through a neighbouring temp file and replaced, so an
            # interruption cannot leave a half-written asset where a whole
            # one used to be. os.replace is atomic on the same filesystem.
            tmp = item["path"].with_suffix(".png.tmp")
            image.save(tmp, "PNG", optimize=True)
            after = tmp.stat().st_size
            os.replace(tmp, item["path"])
        total_before += item["before"]
        total_after += after
        print(f"  {rel:52} {item['w']}x{item['h']} "
              f"{item['before']/1e6:7.1f}M -> {item['nw']}x{item['nh']} "
              f"{after/1e6:6.2f}M")
    if items:
        saved = 100 * (1 - total_after / total_before)
        print(f"  {'':52} {'':>13} {total_before/1e6:7.1f}M -> "
              f"{'':>13} {total_after/1e6:6.2f}M   ({saved:.0f}% smaller)")

    if check_only:
        print("\n--check: every resize composes and nothing was upscaled. "
              "Nothing written.")
        return 0

    (root / GUARD).parent.mkdir(parents=True, exist_ok=True)
    (root / GUARD).write_text(GUARD_SOURCE, encoding="utf-8")
    print(f"\nwrote: {GUARD}\n")
    return verify()


def _step(label: str, args: list) -> int:
    print(f"  {label} ...")
    proc = subprocess.run(args, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
    return proc.returncode


def verify() -> int:
    root = Path.cwd()
    Image = _pillow()

    # Confirm on disk, not from the plan. The plan says what SHOULD have
    # happened; the files say what did, and a save that silently failed would
    # look identical in the log above.
    wrong = []
    for pattern, limit in BUDGET:
        for path in sorted(root.glob(pattern)):
            with Image.open(path) as image:
                if max(image.width, image.height) > limit:
                    wrong.append(f"{path.name} is still "
                                 f"{image.width}x{image.height}")
                if image.width < 8 or image.height < 8:
                    wrong.append(f"{path.name} came out {image.width}x"
                                 f"{image.height}, which is not an image")
    if wrong:
        raise SystemExit("the resize did not land: " + "; ".join(wrong))
    print(f"  guards: every governed asset is within budget on disk")

    code = _step("guard", [sys.executable, "-m", "pytest", GUARD, "-q",
                           "-p", "no:cacheprovider"])
    if code:
        print("\nFAILED -- the guard is red. Nothing was reverted; "
              "`git status` shows exactly what changed.")
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code:
            print(f"\nFAILED -- {label} is not green. Nothing was reverted; "
                  f"`git status` shows exactly what changed.")
            return code
    print("\nGreen.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="bring oversized resources down to the size they render at")
    ap.add_argument("--check", action="store_true",
                    help="rehearse every resize in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="re-check the assets and run the suites only")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        me = Path(__file__).resolve()
        print(f"removing {me.name}")
        me.unlink()
        return 0
    if args.verify:
        return verify()
    return run(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
