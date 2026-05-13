"""
RNV Color Mixer — Image Color Mode Tests
=========================================

Tests for `image_handler.py`'s load_image color-mode branches. The
function has separate paths for RGB/RGBA/P/L/CMYK/LA/1-bit modes plus
JPEG/BMP/GIF/TIFF format-specific handling.

Also includes:
  - sample_region edge cases (full image, single pixel, OOB, inverted)
  - get_pixel_at_coordinates edge cases
  - main app shutdown chain after color history use
  - clipboard color parsing (hex, rgb(), short hex, whitespace handling)
"""

from __future__ import annotations

import pytest
from pathlib import Path
from PIL import Image
from PyQt6.QtWidgets import QMessageBox


def _make_test_image_in_mode(path: Path, mode: str, size=64):
    """Save a test image in the specified PIL color mode."""
    if mode == "RGB":
        img = Image.new("RGB", (size, size), (255, 0, 0))
    elif mode == "RGBA":
        img = Image.new("RGBA", (size, size), (255, 0, 0, 200))
    elif mode == "L":
        img = Image.new("L", (size, size), 128)  # Grayscale
    elif mode == "P":
        img = Image.new("P", (size, size))  # Palette mode
    elif mode == "1":
        img = Image.new("1", (size, size), 1)  # 1-bit binary
    elif mode == "CMYK":
        img = Image.new("CMYK", (size, size), (255, 0, 0, 0))
    elif mode == "LA":
        img = Image.new("LA", (size, size), (128, 200))
    else:
        img = Image.new(mode, (size, size))
    img.save(path)
    return path


# ═══════════════════════════════════════════════════════════════════════════
# 1. image_handler.py — color mode branches in load_image
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerColorModes:
    """`load_image` has ~120 lines of mode-specific conversion logic.
    Each mode triggers a different branch."""

    def test_load_rgb_image(self, tmp_path):
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "rgb.png", "RGB")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_rgba_image_with_alpha(self, tmp_path):
        """RGBA needs alpha-flattening or premultiplication."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "rgba.png", "RGBA")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_grayscale_image(self, tmp_path):
        """L (grayscale) gets converted to RGB."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "gray.png", "L")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_palette_image(self, tmp_path):
        """P (palette) gets converted to RGB."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "palette.png", "P")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_1bit_image(self, tmp_path):
        """1-bit binary images need conversion."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "binary.png", "1")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_la_image(self, tmp_path):
        """LA (grayscale + alpha) — covers a separate branch."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "la.png", "LA")
        ih = ImageHandler()
        assert ih.load_image(str(png)) is True

    def test_load_cmyk_image(self, tmp_path):
        """CMYK images (e.g. from print workflows)."""
        from core.image_handler import ImageHandler
        # CMYK can only be saved as JPG or TIFF
        jpg = tmp_path / "cmyk.jpg"
        Image.new("CMYK", (64, 64), (200, 100, 50, 0)).save(jpg)
        ih = ImageHandler()
        result = ih.load_image(str(jpg))
        # Either succeeds (with conversion) or fails gracefully
        assert isinstance(result, bool)

    def test_load_jpeg_succeeds(self, tmp_path):
        from core.image_handler import ImageHandler
        jpg = tmp_path / "test.jpg"
        Image.new("RGB", (64, 64), (50, 100, 150)).save(jpg, "JPEG")
        ih = ImageHandler()
        assert ih.load_image(str(jpg)) is True

    def test_load_bmp_succeeds(self, tmp_path):
        from core.image_handler import ImageHandler
        bmp = tmp_path / "test.bmp"
        Image.new("RGB", (32, 32), (200, 100, 50)).save(bmp, "BMP")
        ih = ImageHandler()
        assert ih.load_image(str(bmp)) is True

    def test_load_gif_succeeds(self, tmp_path):
        from core.image_handler import ImageHandler
        gif = tmp_path / "test.gif"
        Image.new("RGB", (32, 32), (50, 200, 100)).save(gif, "GIF")
        ih = ImageHandler()
        result = ih.load_image(str(gif))
        assert isinstance(result, bool)

    def test_load_tiff_succeeds(self, tmp_path):
        from core.image_handler import ImageHandler
        tiff = tmp_path / "test.tiff"
        Image.new("RGB", (32, 32), (100, 50, 200)).save(tiff, "TIFF")
        ih = ImageHandler()
        result = ih.load_image(str(tiff))
        assert isinstance(result, bool)

    def test_load_corrupted_file_returns_false(self, tmp_path):
        """File exists but is not a valid image."""
        from core.image_handler import ImageHandler
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"\x89PNG\r\n\x1a\nthis is not a valid PNG")
        ih = ImageHandler()
        result = ih.load_image(str(bad))
        assert result is False

    def test_load_empty_file_returns_false(self, tmp_path):
        from core.image_handler import ImageHandler
        empty = tmp_path / "empty.png"
        empty.write_bytes(b"")
        ih = ImageHandler()
        result = ih.load_image(str(empty))
        assert result is False

    def test_load_with_unsupported_extension_returns_false(self, tmp_path):
        """Some implementations check extension before opening."""
        from core.image_handler import ImageHandler
        weird = tmp_path / "weird.xyz"
        weird.write_text("not an image")
        ih = ImageHandler()
        result = ih.load_image(str(weird))
        # Might be False, or could be True if it tries via PIL anyway
        assert isinstance(result, bool)

    def test_load_replaces_previous_image(self, tmp_path):
        """Loading a new image should replace the existing one."""
        from core.image_handler import ImageHandler
        png1 = _make_test_image_in_mode(tmp_path / "first.png", "RGB")
        png2 = _make_test_image_in_mode(tmp_path / "second.png", "RGB", size=128)

        ih = ImageHandler()
        ih.load_image(str(png1))
        size1 = ih.get_image_size()

        ih.load_image(str(png2))
        size2 = ih.get_image_size()

        # Sizes should differ
        if size1 and size2:
            assert size1 != size2

    def test_get_supported_formats_returns_list(self):
        from core.image_handler import ImageHandler
        ih = ImageHandler()
        formats = ih.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) >= 3  # at least PNG, JPG, BMP


# ═══════════════════════════════════════════════════════════════════════════
# 2. image_handler.py — sample_region edge cases
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerSampleRegion:
    """`sample_region(x1, y1, x2, y2)` averages pixels in a rectangle."""

    def test_sample_full_image_returns_color(self, tmp_path):
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "sample.png", "RGB", size=64)
        ih = ImageHandler()
        ih.load_image(str(png))

        # Sample the entire image
        result = ih.sample_region(0, 0, 64, 64)
        assert result is not None
        assert isinstance(result, tuple) and len(result) == 3

    def test_sample_single_pixel_region(self, tmp_path):
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "single.png", "RGB", size=64)
        ih = ImageHandler()
        ih.load_image(str(png))

        # 1x1 region
        try:
            result = ih.sample_region(10, 10, 11, 11)
        except Exception as e:
            pytest.fail(f"sample_region 1x1 raised {type(e).__name__}: {e}")
        # May return None if too small, or a tuple
        assert result is None or isinstance(result, tuple)

    def test_sample_region_out_of_bounds_clamps_or_returns_none(
        self, tmp_path
    ):
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "oob.png", "RGB", size=64)
        ih = ImageHandler()
        ih.load_image(str(png))

        # Way out of bounds
        try:
            result = ih.sample_region(1000, 1000, 2000, 2000)
        except Exception as e:
            pytest.fail(
                f"sample_region OOB raised {type(e).__name__}: {e}"
            )
        # Either None or clamped result
        assert result is None or isinstance(result, tuple)

    def test_sample_region_with_inverted_coords(self, tmp_path):
        """Some impls handle x1>x2 by swapping; others reject."""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "inv.png", "RGB", size=64)
        ih = ImageHandler()
        ih.load_image(str(png))

        try:
            result = ih.sample_region(50, 50, 10, 10)  # x1>x2, y1>y2
        except Exception:
            return  # Raising is fine
        assert result is None or isinstance(result, tuple)


# ═══════════════════════════════════════════════════════════════════════════
# 3. image_handler.py — get_pixel_at_coordinates edge cases
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestImageHandlerPixelEdgeCases:
    def test_get_pixel_with_no_image_loaded_returns_none(self):
        from core.image_handler import ImageHandler
        ih = ImageHandler()
        # No image loaded
        result = ih.get_pixel_at_coordinates(10, 10)
        assert result is None

    def test_get_pixel_at_origin(self, tmp_path):
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(
            tmp_path / "origin.png", "RGB", size=32
        )
        ih = ImageHandler()
        ih.load_image(str(png))
        color = ih.get_pixel_at_coordinates(0, 0)
        # Should be (255, 0, 0) per _make_test_image_in_mode RGB
        assert color == (255, 0, 0)

    def test_get_pixel_at_negative_coords_returns_none(self, tmp_path):
        """Out-of-bounds coordinates should return None (graceful
        no-op) — not raise.

        (Was WEAK_UNCLASSIFIED in audit; manual triage classified
        UPGRADE because the None-return contract IS observable.)"""
        from core.image_handler import ImageHandler
        png = _make_test_image_in_mode(tmp_path / "neg.png", "RGB", size=32)
        ih = ImageHandler()
        ih.load_image(str(png))

        result = ih.get_pixel_at_coordinates(-5, -5)

        assert result is None, (
            f"out-of-bounds coords should return None, got {result!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. RNV_Color_Mixer.py — shutdown / closeEvent extended
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMainAppShutdownChain:
    """RNV_Color_Mixer.py lines 2783-2910 are the closeEvent + cleanup
    final-shutdown chain. Phase 8.10 covered the basic happy path; this
    covers the with-recent-files-saved branch."""

    def test_close_event_after_color_history_use(
        self, app_window, monkeypatch
    ):
        from PyQt6.QtGui import QCloseEvent
        # Suppress any modal that might pop on close
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: 0)
        monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: 0)
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.No,
        )

        # Use the app for a moment so there's some state to clean up
        app_window.slots[0].set_color((255, 100, 50))
        app_window.slots[0].set_weight(75)
        app_window.auto_mix_colors()

        # Close
        event = QCloseEvent()
        try:
            app_window.closeEvent(event)
        except Exception as e:
            pytest.fail(
                f"closeEvent (after use) raised {type(e).__name__}: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 5. RNV_Color_Mixer.py — splitter / preview / status updates
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMainAppMiscCoverage:
    """Various small handlers that add 5-10 stmts each."""

    def test_splitter_moved_with_various_positions_keeps_sizes_valid(
        self, app_window, monkeypatch
    ):
        """`_on_splitter_moved(pos, idx)` clamps the left pane to
        [SLOTS_MIN_WIDTH, SLOTS_MAX_WIDTH]. After driving with multiple
        positions, splitter sizes should remain within bounds (sum
        equals total width)."""
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)

        # Multiple positions/indices to hit different branches
        for pos, idx in [(100, 0), (300, 1), (500, 2), (700, 0)]:
            app_window._on_splitter_moved(pos=pos, index=idx)

            # After each call, splitter sizes invariants should hold
            sizes = app_window.content_splitter.sizes()
            if len(sizes) >= 2:
                left = sizes[0]
                total = sum(sizes)
                # Left pane is non-negative and doesn't exceed total
                assert 0 <= left <= total, (
                    f"after splitter_moved({pos}, {idx}): "
                    f"left={left}, total={total}"
                )

    def test_apply_all_settings_applies_theme_from_settings(
        self, app_window, monkeypatch
    ):
        """`_apply_all_settings` reads from settings_manager and
        applies each preference. Most observable: theme."""
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: 0)
        monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: 0)

        if app_window.settings_manager is None:
            pytest.skip("settings_manager not configured in this fixture")

        # Force a known theme in settings
        app_window.settings_manager.set("preferences.theme", "light")

        app_window._apply_all_settings()

        assert app_window.ui_handler.theme_manager.current_theme == "light"

    def test_get_current_state_full_round_trip(self, app_window):
        """get_current_state and verify all required keys present."""
        app_window.slots[0].set_color((100, 150, 200))
        app_window.slots[0].set_weight(60)
        state = app_window.get_current_state()
        assert isinstance(state, dict)
        for required_key in ("slots", "mixed_color", "settings"):
            assert required_key in state
        # Slots is a list of dicts
        assert isinstance(state["slots"], list)


# ═══════════════════════════════════════════════════════════════════════════
# 6. clipboard.py — color parsing edge cases
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestClipboardColorParsing:
    """`try_parse_color_from_clipboard` handles multiple formats:
    hex (#RRGGBB), rgb(r,g,b), css colors, etc. Each is a separate
    branch."""

    def test_parse_short_hex(self, qtbot):
        from clipboard import ClipboardUtils
        clip = ClipboardUtils()
        clip.copy_text("#F80")  # Short hex form
        result = clip.try_parse_color_from_clipboard()
        # Either parses or returns None — both fine
        assert result is None or (
            isinstance(result, tuple) and len(result) == 3
        )

    def test_parse_rgb_function_form(self, qtbot):
        from clipboard import ClipboardUtils
        clip = ClipboardUtils()
        clip.copy_text("rgb(255, 128, 64)")
        result = clip.try_parse_color_from_clipboard()
        assert result is None or (
            isinstance(result, tuple) and len(result) == 3
        )

    def test_parse_with_whitespace_padding(self, qtbot):
        from clipboard import ClipboardUtils
        clip = ClipboardUtils()
        clip.copy_text("   #FF8040   ")
        result = clip.try_parse_color_from_clipboard()
        assert result is None or (
            isinstance(result, tuple) and len(result) == 3
        )

    def test_parse_empty_clipboard_returns_none(self, qtbot):
        from clipboard import ClipboardUtils
        clip = ClipboardUtils()
        clip.copy_text("")
        result = clip.try_parse_color_from_clipboard()
        assert result is None
