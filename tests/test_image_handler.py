"""
RNV Color Mixer — ImageHandler Tests  (Phase 7.5 deliverable)
================================================================

Drives the `core.image_handler.ImageHandler` class with PIL-generated
test images. Phase 4 covered transitive construction via ColorMixerApp;
this phase covers the load/sample/clear pipeline directly.

Test fixture strategy
---------------------
Every test gets its own PIL-generated PNG in `tmp_path`. Images are tiny
(16x16 or 32x32) with solid quadrant colours so we can sample at known
coordinates and assert exact RGB values. No reliance on the project's
own `resources/` folder.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from core.image_handler import ImageHandler


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

def _make_quadrant_png(path: Path, size: int = 32) -> Path:
    """Generate a PNG with 4 known-colour quadrants for sampling tests.

    Layout (size=32):
        TL=red(255,0,0)        TR=green(0,255,0)
        BL=blue(0,0,255)       BR=yellow(255,255,0)
    """
    from PIL import Image

    img = Image.new("RGB", (size, size), (255, 0, 0))
    pixels = img.load()
    half = size // 2
    for x in range(size):
        for y in range(size):
            if x < half and y < half:
                pixels[x, y] = (255, 0, 0)
            elif x >= half and y < half:
                pixels[x, y] = (0, 255, 0)
            elif x < half and y >= half:
                pixels[x, y] = (0, 0, 255)
            else:
                pixels[x, y] = (255, 255, 0)
    img.save(path, "PNG")
    return path


def _make_solid_png(path: Path, color: tuple, size: int = 16) -> Path:
    """PNG filled with a single colour."""
    from PIL import Image
    Image.new("RGB", (size, size), color).save(path, "PNG")
    return path


@pytest.fixture
def handler():
    """Fresh ImageHandler — no Qt parent needed (it's a QObject not a QWidget)."""
    return ImageHandler()


@pytest.fixture
def quadrant_png(tmp_path):
    return _make_quadrant_png(tmp_path / "quadrants.png")


@pytest.fixture
def solid_red_png(tmp_path):
    return _make_solid_png(tmp_path / "red.png", (255, 0, 0))


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerConstruction:
    def test_default_state_after_construction(self, handler):
        assert handler.get_image_size() is None
        # Signals must be real
        from PyQt6.QtCore import pyqtBoundSignal
        for sig_name in ("image_loaded", "image_cleared",
                         "zoom_changed", "status_message"):
            sig = getattr(handler, sig_name)
            assert isinstance(sig, pyqtBoundSignal), (
                f"{sig_name} not a pyqtBoundSignal"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Load image — happy path (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerLoadHappyPath:
    def test_load_valid_png_returns_true_and_sets_size(
        self, handler, solid_red_png
    ):
        ok = handler.load_image(str(solid_red_png))
        assert ok is True
        size = handler.get_image_size()
        assert size == (16, 16), f"expected (16, 16), got {size}"

    def test_load_image_emits_image_loaded_signal(
        self, handler, solid_red_png, qtbot
    ):
        with qtbot.waitSignal(handler.image_loaded, timeout=2000) as blocker:
            handler.load_image(str(solid_red_png))
        assert blocker.args == [str(solid_red_png)]


# ═══════════════════════════════════════════════════════════════════════════
# 3. Load image — error paths (4 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerLoadErrorPaths:
    """Each input-validation branch in `load_image` returns False and
    emits a status message rather than crashing."""

    def test_load_empty_path_returns_false(self, handler):
        assert handler.load_image("") is False
        assert handler.get_image_size() is None

    def test_load_none_path_returns_false(self, handler):
        # `None` is not a string — should fail the isinstance check
        assert handler.load_image(None) is False  # type: ignore[arg-type]

    def test_load_nonexistent_path_returns_false(self, handler, tmp_path):
        bogus = tmp_path / "does_not_exist.png"
        assert handler.load_image(str(bogus)) is False
        assert handler.get_image_size() is None

    def test_load_invalid_extension_returns_false(self, handler, tmp_path):
        """Files with unsupported extensions are rejected before any
        decoding attempt."""
        txt = tmp_path / "not_an_image.txt"
        txt.write_text("hello")
        assert handler.load_image(str(txt)) is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Pixel sampling (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerPixelSampling:
    def test_get_pixel_at_known_quadrant_returns_correct_color(
        self, handler, quadrant_png
    ):
        """4-quadrant fixture: top-left red, top-right green, bottom-left
        blue, bottom-right yellow. Sample one pixel from each quadrant."""
        handler.load_image(str(quadrant_png))

        # The quadrant fixture is 32x32 with quadrants at (0..15, 0..15)
        # for top-left, etc. Sample well inside each quadrant.
        assert handler.get_pixel_at_coordinates(5, 5) == (255, 0, 0)
        assert handler.get_pixel_at_coordinates(20, 5) == (0, 255, 0)
        assert handler.get_pixel_at_coordinates(5, 20) == (0, 0, 255)
        assert handler.get_pixel_at_coordinates(20, 20) == (255, 255, 0)

    def test_sample_region_returns_average_of_known_solid_color(
        self, handler, solid_red_png
    ):
        """Solid-red fixture: any region must average to red."""
        handler.load_image(str(solid_red_png))
        result = handler.sample_region(0, 0, 8, 8)
        assert result == (255, 0, 0), (
            f"sample_region of pure-red image gave {result}, expected "
            f"(255, 0, 0)"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 5. Clear (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerClear:
    def test_clear_image_resets_state_and_emits_signal(
        self, handler, solid_red_png, qtbot
    ):
        handler.load_image(str(solid_red_png))
        assert handler.get_image_size() == (16, 16)

        with qtbot.waitSignal(handler.image_cleared, timeout=1000):
            handler.clear_image()

        assert handler.get_image_size() is None


# ═══════════════════════════════════════════════════════════════════════════
# 6. Public API helpers (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerHelpers:
    def test_get_supported_formats_returns_known_extensions(self, handler):
        """The supported-formats list is consumed by file dialogs.
        Catches accidental rename or reformatting of the constant."""
        formats = handler.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) >= 5, (
            f"get_supported_formats returned only {len(formats)} entries; "
            f"expected ≥ 5 (at minimum: png, jpg, jpeg, bmp, gif)"
        )
        # Common formats must be present
        formats_lower = " ".join(formats).lower()
        for required in ("png", "jpg", "bmp"):
            assert required in formats_lower, (
                f".{required} missing from get_supported_formats(): {formats}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 7. Image info (1 test)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerInfo:
    def test_get_image_info_returns_full_metadata(
        self, handler, solid_red_png
    ):
        """`get_image_info` returns a dict consumed by the UI for the
        status bar display."""
        handler.load_image(str(solid_red_png))
        info = handler.get_image_info()
        assert info is not None, "get_image_info returned None after load"
        for key in ("size", "path", "format", "mode"):
            assert key in info, f"info dict missing key {key!r}"
        assert info["size"] == (16, 16)
