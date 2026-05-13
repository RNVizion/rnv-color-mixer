"""
RNV Color Mixer — Snapshot Tests  (Phase 2 deliverable)
========================================================

Locks the byte-exact output of each palette export format and the exact
text of each theme stylesheet against silent drift. A regression in any
exporter or a casual edit to a stylesheet will fail loudly here.

Reference data lives in /snapshots/ at the project root.

Total tests: 19
  • 16 palette format snapshots (all of `PaletteFormats.export_palette` dispatch keys)
  •  3 stylesheet snapshots (DARK / LIGHT / IMAGE)

Updating snapshots
------------------
NEVER auto-update. Snapshots stay frozen until intentionally regenerated.
When a deliberate change is made to an exporter or stylesheet, run with:

    RNV_UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py

… or equivalently:

    pytest tests/test_snapshots.py --rnv-update-snapshots

Both forms make every snapshot test SKIP (with the new bytes written), so a
clean re-run afterwards is required to confirm the new state passes.

Determinism notes (verified 2026-04-30)
---------------------------------------
All 16 export formats are byte-deterministic for the SNAPSHOT_PALETTE input:
no timestamps, no UUIDs, no random padding. Direct byte-compare is safe for
every format, including binary ones (ASE / ACO / ACB / CLR / SWATCHES).
"""

from __future__ import annotations

import os
import pytest

# Project imports — conftest.py has already configured sys.path
from core.palette_formats import PaletteFormats
from utils.config import DARK_STYLESHEET, LIGHT_STYLESHEET, IMAGE_STYLESHEET


# ═══════════════════════════════════════════════════════════════════════════
# Reference data — FROZEN. Changing any of these is a snapshot-regen event.
# ═══════════════════════════════════════════════════════════════════════════

SNAPSHOT_PALETTE: list[tuple[tuple[int, int, int], int]] = [
    ((255,   0,   0), 25),  # red
    ((  0, 255,   0), 25),  # green
    ((  0,   0, 255), 25),  # blue
    ((210, 188, 147), 25),  # brand gold
]

# All extensions handled by PaletteFormats.export_palette's dispatch table.
PALETTE_FORMATS: tuple[str, ...] = (
    "gpl", "json", "xml", "css", "svg",
    "hex", "hsv", "hsl", "txt", "colors",
    "afpalette", "ase", "aco", "acb", "clr", "swatches",
)

STYLESHEETS: dict[str, str] = {
    "dark":  DARK_STYLESHEET,
    "light": LIGHT_STYLESHEET,
    "image": IMAGE_STYLESHEET,
}


# ═══════════════════════════════════════════════════════════════════════════
# Update-mode mechanism — env var OR CLI flag, both honoured
# ═══════════════════════════════════════════════════════════════════════════

def _update_mode_active(request) -> bool:
    """True when snapshots should be (re)written instead of compared."""
    if os.environ.get("RNV_UPDATE_SNAPSHOTS") == "1":
        return True
    try:
        return bool(request.config.getoption("--rnv-update-snapshots"))
    except (ValueError, KeyError):
        return False


def _byte_diff_message(label: str, produced: bytes, expected: bytes) -> str:
    """Concise diagnostic for a byte-level snapshot mismatch."""
    if len(produced) != len(expected):
        size_note = (
            f"   produced size: {len(produced)} bytes\n"
            f"   snapshot size: {len(expected)} bytes\n"
        )
    else:
        size_note = f"   size: {len(produced)} bytes (same)\n"

    for i, (a, b) in enumerate(zip(produced, expected)):
        if a != b:
            ctx_lo = max(0, i - 8)
            ctx_hi = min(len(produced), i + 8)
            return (
                f"\n[{label}] First differing byte at offset {i}:\n"
                f"   produced byte: {a:#04x}  ({chr(a) if 32 <= a < 127 else '.'})\n"
                f"   snapshot byte: {b:#04x}  ({chr(b) if 32 <= b < 127 else '.'})\n"
                f"   produced context: {produced[ctx_lo:ctx_hi]!r}\n"
                f"   snapshot context: {expected[ctx_lo:ctx_hi]!r}\n"
                f"{size_note}"
            )
    return f"\n[{label}] One file is a strict prefix of the other.\n{size_note}"


def _line_diff_message(label: str, produced: bytes, expected: bytes) -> str:
    """Line-level diagnostic for stylesheet-style text snapshots."""
    p_lines = produced.decode("utf-8", errors="replace").splitlines()
    e_lines = expected.decode("utf-8", errors="replace").splitlines()
    for i, (pl, el) in enumerate(zip(p_lines, e_lines), start=1):
        if pl != el:
            return (
                f"\n[{label}] Mismatch at line {i}:\n"
                f"   produced: {pl!r}\n"
                f"   snapshot: {el!r}\n"
                f"   produced lines total: {len(p_lines)}\n"
                f"   snapshot lines total: {len(e_lines)}\n"
            )
    return (
        f"\n[{label}] Line count differs: produced {len(p_lines)} "
        f"vs snapshot {len(e_lines)}\n"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Palette format snapshots — 16 tests, one per supported export extension
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.snapshot
class TestPaletteFormatSnapshots:
    """Byte-exact snapshots of every PaletteFormats export format."""

    @pytest.mark.parametrize("ext", PALETTE_FORMATS)
    def test_palette_format(self, ext, tmp_path, snapshots_dir, request):
        snapshot_path = snapshots_dir / f"palette_4color.{ext}"

        # Generate fresh export
        out_path = tmp_path / f"out.{ext}"
        PaletteFormats.export_palette(str(out_path), SNAPSHOT_PALETTE)
        produced = out_path.read_bytes()

        # Update mode: write new snapshot, skip the test
        if _update_mode_active(request):
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_bytes(produced)
            pytest.skip(
                f"snapshot regenerated: {snapshot_path.name} "
                f"({len(produced)} bytes)"
            )

        # Compare mode: must exist and match exactly
        if not snapshot_path.exists():
            pytest.fail(
                f"Snapshot missing: {snapshot_path}\n"
                f"To create initial snapshots: RNV_UPDATE_SNAPSHOTS=1 pytest "
                f"tests/test_snapshots.py"
            )

        expected = snapshot_path.read_bytes()
        if produced != expected:
            pytest.fail(_byte_diff_message(f".{ext}", produced, expected))


# ═══════════════════════════════════════════════════════════════════════════
# Stylesheet snapshots — 3 tests, one per theme
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.snapshot
class TestStylesheetSnapshots:
    """Byte-exact snapshots of each theme's stylesheet string.

    Stylesheets are encoded UTF-8 and stored as bytes so that line-ending
    behaviour is identical across Windows and Linux (avoids text-mode CRLF
    translation surprises)."""

    @pytest.mark.parametrize("name", sorted(STYLESHEETS.keys()))
    def test_stylesheet(self, name, snapshots_dir, request):
        snapshot_path = snapshots_dir / f"stylesheet_{name}.txt"
        produced = STYLESHEETS[name].encode("utf-8")

        if _update_mode_active(request):
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_bytes(produced)
            pytest.skip(
                f"snapshot regenerated: {snapshot_path.name} "
                f"({len(produced)} bytes)"
            )

        if not snapshot_path.exists():
            pytest.fail(
                f"Snapshot missing: {snapshot_path}\n"
                f"To create initial snapshots: RNV_UPDATE_SNAPSHOTS=1 pytest "
                f"tests/test_snapshots.py"
            )

        expected = snapshot_path.read_bytes()
        if produced != expected:
            pytest.fail(_line_diff_message(f"stylesheet_{name}", produced, expected))
