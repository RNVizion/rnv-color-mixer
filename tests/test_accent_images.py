"""THE LIST OF IMAGES THAT CARRY THE ACCENT IS CURRENT (#86 A, 2026-10-23).

The same file in all five RNV desktop applications.

WHY. The code moves every gold it draws in ten lines; the images have the
gold drawn into them and do not move (the gold-swap trial, 2026-10-16). Big
art changes are hand-made (#84), so if the accent ever moves, what has to be
remade should be a list. ACCENT_IMAGES.md is that list, written by
tools/accent_images.py from the images themselves. Nothing here changes an
image.

WHAT IT HOLDS.
  1. ACCENT_IMAGES.md is exactly what the tool writes from the images as
     they are. An image added, changed or removed without running the tool,
     and this says what to run.
  2. The tool is looking. On images made here from the application's own
     golds: a flat two-gold image is accent and flat; a shaded run of golds is
     shaded; the same shapes turned half way round the color wheel, a gray
     of the gold's own value, and the gold's hue nearly grayed out, are not
     accent; a gold image under screenshots
     is a screenshot and under test a fixture; two identical files are counted
     once; and the list is in the order of its paths as text, so a capital
     letter sorts the same on Windows, which compares paths without case.
  3. The list is not empty: the application has art that carries the accent.
"""
from __future__ import annotations

import colorsys
import importlib.util
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "accent_images.py"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("_rnv_accent_images", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _turned(rgb, degrees):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb((h + degrees / 360) % 1.0, s, v))


def test_the_list_is_what_the_tool_writes(tool):
    current = (ROOT / tool.OUTPUT).read_text(encoding="utf-8")
    assert current == tool.render(ROOT), (
        f"{tool.OUTPUT} is not what the images say. An image was added, changed or removed. "
        f"Run: python tools/accent_images.py")


def test_the_application_has_art_that_carries_the_accent(tool):
    rows = tool.inventory(ROOT, tool.golds(ROOT))
    assert rows, "no images found under resources/"
    assert any(r["kind"] in ("shaded", "flat") for r in rows), "no art carries the accent"


def test_the_tool_is_looking(tool, tmp_path):
    golds = tool.golds(ROOT)
    gold, dark = _rgb(golds["BRAND_GOLD"]), _rgb(golds["BRAND_DARK_GOLD"])
    art = tmp_path / "resources" / "button_images"
    art.mkdir(parents=True)

    flat = Image.new("RGBA", (40, 20), gold + (255,))
    flat.paste(Image.new("RGBA", (20, 20), dark + (255,)), (20, 0))
    flat.save(art / "flat.png")
    flat.save(art / "flat_copy.png")

    shaded = Image.new("RGBA", (64, 4))
    for x in range(64):
        step = tuple(round(dark[i] + (gold[i] - dark[i]) * x / 63) for i in range(3))
        for y in range(4):
            shaded.putpixel((x, y), step + (255,))
    shaded.save(art / "shaded.png")

    turned = Image.new("RGBA", (40, 20), _turned(gold, 180) + (255,))
    turned.paste(Image.new("RGBA", (20, 20), _turned(dark, 180) + (255,)), (20, 0))
    turned.save(art / "turned.png")

    level = max(gold)
    Image.new("RGBA", (20, 20), (level, level, level, 255)).save(art / "gray.png")

    # the gold's own hue and value, nearly gray (saturation 0.05): under the floor
    h, _s, v = colorsys.rgb_to_hsv(*(c / 255 for c in gold))
    warm = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, 0.05, v))
    Image.new("RGBA", (20, 20), warm + (255,)).save(art / "warm_gray.png")

    for folder in ("screenshots", "test"):
        (tmp_path / "resources" / folder).mkdir()
        flat.save(tmp_path / "resources" / folder / "gold.png")

    # a capital letter sorts the same on every system (Windows compares paths without case)
    flat.save(art / "Upper.png")

    listed = [r["file"] for r in tool.inventory(tmp_path, golds)]
    assert listed == sorted(listed), "the list is not in the order of its paths as text"
    assert listed.index("resources/button_images/Upper.png") < listed.index("resources/button_images/flat.png")
    rows = {r["file"]: r for r in tool.inventory(tmp_path, golds)}
    assert rows["resources/button_images/flat.png"]["kind"] == "flat"
    assert rows["resources/button_images/flat.png"]["share"] == 1.0
    assert rows["resources/button_images/flat_copy.png"]["same_as"] == "resources/button_images/Upper.png"
    assert rows["resources/button_images/shaded.png"]["kind"] == "shaded"
    assert rows["resources/button_images/shaded.png"]["shades"] > 3
    assert rows["resources/button_images/turned.png"]["share"] == 0.0
    assert rows["resources/button_images/turned.png"]["kind"] == "none"
    assert rows["resources/button_images/gray.png"]["kind"] == "none"
    assert rows["resources/button_images/warm_gray.png"]["kind"] == "none"
    assert rows["resources/screenshots/gold.png"]["kind"] == "screenshot"
    assert rows["resources/test/gold.png"]["kind"] == "fixture"
    text = tool.render(tmp_path, golds)
    # Upper, flat, its copy and shaded: four images of art, two pieces
    assert "**4 images of art carry the accent, 2 of them distinct.**" in text
    assert rows["resources/button_images/flat.png"]["same_as"] == "resources/button_images/Upper.png"
