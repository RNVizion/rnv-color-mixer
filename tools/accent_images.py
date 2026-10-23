"""Which images carry the accent, and how much of it (#86 A, 2026-10-23).   RNV-ACCENT-IMAGES

The same file in all five RNV desktop applications. Run it from the
application's root after adding or changing an image:

    python tools/accent_images.py            # write ACCENT_IMAGES.md
    python tools/accent_images.py --check    # exit 1 if ACCENT_IMAGES.md is out of date

WHY. Ten lines move every gold the application's code draws (the gold-swap
trial of 2026-10-16). The images do not move with them: the button art, the
settings gear, the icons and the background have the gold drawn into them.
Chris, 2026-10-22: big art changes are hand-made, not swaps (#84). This keeps
the count, so that if the accent ever moves, what has to be remade is a list,
not a search. It reads the images; it never changes one.

WHAT IT MEASURES, for every image under resources/:
  - accent share: of the pixels at least half opaque, the share whose hue is
    within WINDOW degrees of the hue of BRAND_GOLD or BRAND_DARK_GOLD (read
    from utils/colors.py), with saturation and value at least FLOOR. WINDOW
    is 6, measured on 2026-10-23: of the gold-colored pixels in the five
    apps' 120 button images (hue 19 to 65), 98.8% sit within 6 degrees of a
    gold's hue; the rest is mostly the pressed buttons' dark olive face shading,
    which a 20-degree window would count as gold. The oranges in the
    screenshots' palettes sit 7 to 9 degrees from the bright gold;
  - shades: how many exact colors those accent pixels take;
  - kind, from the folder and the measure:
      screenshot  under a folder called screenshots: a picture of the app,
                  retaken after a swap, not recolored;
      fixture     under a folder called test or tests: a test input, not art;
      none        less than CARRIES of its pixels are accent;
      flat        its three most common accent colors cover at least FLAT of
                  its accent pixels: a swap of exact colors could recolor it;
      shaded      anything else: hand-made, shaded art, remade by hand (#84).
  - same as: an earlier file in the list with the same bytes, so one piece of
    art is counted once.
"""
from __future__ import annotations

import colorsys
import hashlib
import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageChops

WINDOW = 6.0      # degrees of hue either side of a gold
FLOOR = 0.15      # least saturation and value of an accent pixel
CARRIES = 0.01    # least accent share that counts as carrying the accent
FLAT = 0.90       # least share of accent pixels in its three commonest colors
EXTENSIONS = (".png", ".jpg", ".jpeg", ".ico", ".bmp", ".gif", ".webp")
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", "site-packages"}
OUTPUT = "ACCENT_IMAGES.md"


def golds(root: Path) -> dict[str, str]:
    """BRAND_GOLD and BRAND_DARK_GOLD, from the application's color file."""
    spec = importlib.util.spec_from_file_location("_rnv_colors_for_images", root / "utils" / "colors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {"BRAND_GOLD": module.BRAND_GOLD, "BRAND_DARK_GOLD": module.BRAND_DARK_GOLD}


def _hue(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def _hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _at_least(fraction: float) -> list[int]:
    return [255 if i / 255 >= fraction else 0 for i in range(256)]


def measure(path: Path, hues: list[float]) -> dict:
    """Accent share, shades and top-three cover of one image, at full size."""
    with Image.open(path) as image:
        image.load()
        rgba = image.convert("RGBA")
    rgb = rgba.convert("RGB")
    h, s, v = rgb.convert("HSV").split()
    hue_lut = [255 if min(_hue_distance(i * 360 / 255, x) for x in hues) <= WINDOW else 0 for i in range(256)]
    opaque_mask = rgba.getchannel("A").point(_at_least(0.5))
    mask = ImageChops.multiply(
        ImageChops.multiply(h.point(hue_lut), s.point(_at_least(FLOOR))),
        ImageChops.multiply(v.point(_at_least(FLOOR)), opaque_mask))
    opaque = opaque_mask.histogram()[255]
    accent = mask.histogram()[255]
    # pure black is never accent (its value is 0), so it marks the pixels left out
    kept = Image.composite(rgb, Image.new("RGB", rgb.size), mask)
    counts = sorted((n for n, c in kept.getcolors(rgb.width * rgb.height) if c != (0, 0, 0)), reverse=True)
    return {
        "size": f"{rgba.width}x{rgba.height}",
        "share": accent / opaque if opaque else 0.0,
        "shades": len(counts),
        "top3": sum(counts[:3]) / accent if accent else 0.0,
    }


def kind(rel: str, m: dict) -> str:
    parts = rel.lower().split("/")[:-1]
    if "screenshots" in parts:
        return "screenshot"
    if "test" in parts or "tests" in parts:
        return "fixture"
    if m["share"] < CARRIES:
        return "none"
    return "flat" if m["top3"] >= FLAT else "shaded"


def images(root: Path) -> list[str]:
    """Every image under resources/, in the order of its path as text.

    Sorted as strings, not as paths: Windows compares paths without regard to
    case, so `Image-mode.png` sorted differently there and the list came out
    in another order (Chris's machine, 2026-10-23).
    """
    base = root / "resources"
    found = []
    for path in base.rglob("*") if base.is_dir() else []:
        rel = path.relative_to(root)
        if any(p in SKIP_DIRS or p.startswith(".") for p in rel.parts):
            continue
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            found.append(rel.as_posix())
    return sorted(found)


def inventory(root: Path, gold_values: dict[str, str]) -> list[dict]:
    hues = [_hue(v) for v in gold_values.values()]
    rows, first = [], {}
    for rel in images(root):
        m = measure(root / rel, hues)
        digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        rows.append({"file": rel, **m, "kind": kind(rel, m), "same_as": first.get(digest, "")})
        first.setdefault(digest, rel)
    return rows


def render(root: Path, gold_values: dict[str, str] | None = None) -> str:
    rows = inventory(root, gold_values or golds(root))
    folders: dict[str, list[dict]] = {}
    for r in rows:
        folders.setdefault(r["file"].rsplit("/", 1)[0], []).append(r)
    kinds = ("shaded", "flat", "screenshot", "fixture", "none")
    art = [r for r in rows if r["kind"] in ("shaded", "flat")]
    lines = [
        "# Images that carry the accent",
        "",
        "Written by `tools/accent_images.py` (#86 A). Do not edit by hand: after adding or "
        "changing an image, run `python tools/accent_images.py`. "
        "`tests/test_accent_images.py` fails until this file is what the tool writes.",
        "",
        "If the accent ever moves, the code moves it in ten lines; these images do not move with it. "
        "**shaded** art is hand-made and is remade by hand (#84). **flat** art could be recolored by "
        "swapping exact colors. A **screenshot** is retaken. A **fixture** is a test input. "
        f"Accent: hue within {WINDOW:g} degrees of `BRAND_GOLD` or `BRAND_DARK_GOLD`, saturation and value "
        f"at least {FLOOR:g}; an image carries it from {CARRIES:.0%} of its pixels; flat means its three "
        f"commonest accent colors cover at least {FLAT:.0%} of them. The tool's docstring says why.",
        "",
        f"**{len(art)} images of art carry the accent, "
        f"{len([r for r in art if not r['same_as']])} of them distinct.**",
        "",
        "| folder | files | " + " | ".join(kinds) + " |",
        "|---|---|" + "---|" * len(kinds),
    ]
    for folder, rs in folders.items():
        lines.append(f"| `{folder}` | {len(rs)} | "
                     + " | ".join(str(sum(r["kind"] == k for r in rs)) for k in kinds) + " |")
    for folder, rs in folders.items():
        lines += ["", f"## `{folder}`", "", "| file | size | accent | shades | kind | same as |",
                  "|---|---|---|---|---|---|"]
        for r in rs:
            same = f"`{r['same_as'].rsplit('/', 1)[-1]}`" if r["same_as"] else ""
            lines.append(f"| `{r['file'].rsplit('/', 1)[-1]}` | {r['size']} | {r['share'] * 100:.1f}% | "
                         f"{r['shades']} | {r['kind']} | {same} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if not (root / "utils" / "colors.py").is_file():
        print("Run this from the application's root (no utils/colors.py here).", file=sys.stderr)
        return 2
    text = render(root)
    target = root / OUTPUT
    if "--check" in argv:
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if current != text:
            print(f"{OUTPUT} is out of date. Run: python tools/accent_images.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT} is up to date.")
        return 0
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
