"""
Image handling functionality for the Color Mixer application (PyQt6 version).
Handles image loading, display, zooming, sampling, and related operations.
"""

import os
from typing import TYPE_CHECKING
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal
from core.color_math import ColorMath

if TYPE_CHECKING:
    from PyQt6.QtGui import QImage

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("ImageHandler")
except ImportError:
    logger = None

# Import pixmap cache for efficient zoom operations
try:
    from utils.pixmap_cache import ImagePixmapCache
    _pixmap_cache_available = True
except ImportError:
    _pixmap_cache_available = False

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class ImageHandler(QObject):
    """Handles all image-related operations (PyQt6 version)."""
    
    
    # Safety limits to prevent crashes
    MAX_IMAGE_PIXELS = 100_000_000  # ~100 megapixels (10000x10000)
    MAX_FILE_SIZE_MB = 200  # Maximum file size in megabytes
    # Signals
    image_loaded = pyqtSignal(str)  # image path
    image_cleared = pyqtSignal()
    zoom_changed = pyqtSignal(float)  # zoom level
    status_message = pyqtSignal(str)  # status message
    
    def __init__(self):
        super().__init__()
        self.image: Image.Image | None = None
        self.image_path: str | None = None
        self.zoom_level = 1.0
        self.last_fit_width = None
        self.last_fit_height = None
        
        # QImage cache for performance (avoid repeated PIL to QImage conversion)
        self._cached_qimage = None
        self._cached_zoom = None
        
        # QPixmap cache for efficient zoom operations
        if _pixmap_cache_available:
            self.pixmap_cache = ImagePixmapCache(max_size=15)
        else:
            self.pixmap_cache = None

    def load_image(self, path: str) -> bool:
        """Load an image from file path with enhanced safety checks."""
        try:
            # PHASE 2.4: Validate file path
            if not path or not isinstance(path, str):
                self.status_message.emit("Invalid file path")
                return False
            
            # Check for extremely long paths (Windows MAX_PATH = 260)
            if len(path) > 255:
                self.status_message.emit(
                    f"File path too long ({len(path)} characters). "
                    f"Maximum: 255 characters"
                )
                return False
            
            # Validate file exists
            if not os.path.exists(path):
                self.status_message.emit(f"File not found: {path}")
                return False
            
            # Check if file is readable
            if not os.access(path, os.R_OK):
                self.status_message.emit(f"File is not readable. Check permissions.")
                return False
            
            # Validate file extension
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
            file_ext = os.path.splitext(path)[1].lower()
            if file_ext not in valid_extensions:
                self.status_message.emit(
                    f"Unsupported file type: {file_ext}. "
                    f"Supported: {', '.join(sorted(valid_extensions))}"
                )
                return False
            
            # Check file size BEFORE loading to prevent memory issues
            file_size_mb = os.path.getsize(path) / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                self.status_message.emit(
                    f"Image file too large ({file_size_mb:.1f}MB). "
                    f"Maximum allowed: {self.MAX_FILE_SIZE_MB}MB"
                )
                return False
            
            # === LARGE IMAGE WARNING (>10MB) ===
            from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
            from PyQt6.QtCore import Qt
            
            if file_size_mb > 10:
                reply = QMessageBox.question(
                    None,
                    "Large Image File",
                    f"This image is {file_size_mb:.1f}MB.\n\n"
                    f"Large images may:\n"
                    f"• Use significant memory\n"
                    f"• Take longer to load and zoom\n"
                    f"• Slow down color sampling\n\n"
                    f"Continue loading?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    self.status_message.emit("Image loading cancelled by user")
                    return False
            
            # === PROGRESS DIALOG FOR LARGE FILES (>5MB) ===
            progress = None
            if file_size_mb > 5:
                progress = QProgressDialog(
                    f"Loading image ({file_size_mb:.1f}MB)...",
                    None,  # No cancel button during load
                    0, 0,  # Indeterminate progress
                    None
                )
                progress.setWindowTitle("Loading Image")
                progress.setWindowModality(Qt.WindowModality.ApplicationModal)
                progress.setMinimumDuration(0)
                progress.show()
                QApplication.processEvents()
            
            # Set PIL safety limit for decompression bombs
            Image.MAX_IMAGE_PIXELS = self.MAX_IMAGE_PIXELS
            
            # SAFETY FIX: Quick validation without full decode
            try:
                with Image.open(path) as img_check:
                    width, height = img_check.size
                    
                    # PHASE 2.1: Check for zero or invalid dimensions
                    if width <= 0 or height <= 0:
                        self.status_message.emit(
                            f"Invalid image dimensions: {width}x{height}. "
                            f"Image must have positive width and height."
                        )
                        return False
                    
                    # PHASE 2.1: Warn about extremely thin images (potential display issues)
                    if width < 10 or height < 10:
                        logger.warning(f"⚠️  Warning: Very small image ({width}x{height}). May have display issues.")
                    
                    # PHASE 2.1: Check for unreasonably large single dimensions
                    if width > 50000 or height > 50000:
                        self.status_message.emit(
                            f"Image dimensions too extreme ({width}x{height}). "
                            f"Maximum single dimension: 50,000 pixels"
                        )
                        return False
                    
                    # Check dimensions before loading
                    if width * height > self.MAX_IMAGE_PIXELS:
                        self.status_message.emit(
                            f"Image resolution too high ({width}x{height}). "
                            f"Maximum: ~{int(self.MAX_IMAGE_PIXELS**0.5)}x{int(self.MAX_IMAGE_PIXELS**0.5)}"
                        )
                        return False
                    
                    # Verify image is not corrupted
                    try:
                        img_check.verify()
                    except Exception as verify_error:
                        self.status_message.emit(f"Corrupted or invalid image file: {verify_error}")
                        return False
            except (IOError, OSError) as e:
                self.status_message.emit(f"Cannot read image file: {e}")
                return False
            
            # Now do the actual load (we know it's safe)
            # MEMORY FIX: Close old image before loading new one
            if self.image is not None:
                try:
                    self.image.close()
                except Exception:
                    pass  # Ignore errors during cleanup
            
            self.image = Image.open(path)
            self.image_path = path
            self.zoom_level = 1.0
            
            # PHASE 2.2: Handle animated images (GIF, APNG, WebP)
            if hasattr(self.image, 'n_frames') and self.image.n_frames > 1:
                frame_count = self.image.n_frames
                self.status_message.emit(
                    f"⚠️ Animated image detected ({frame_count} frames). Using first frame only."
                )
                logger.debug(f"📸 Animated image: {frame_count} frames. Using frame 0.")
                # Ensure we're on the first frame
                self.image.seek(0)
                # Convert to static image to prevent issues
                self.image = self.image.copy()
            
            # PHASE 2.3: Enhanced color mode validation and conversion
            original_mode = self.image.mode
            logger.debug(f"📷 Image color mode: {original_mode} ({self.image.size[0]}x{self.image.size[1]})")
            
            # Handle all possible color modes
            if original_mode == 'RGB':
                # Already in RGB, perfect!
                pass
            
            elif original_mode == 'RGBA':
                # Create white background and paste RGBA image
                logger.debug("Converting RGBA to RGB (white background)")
                background = Image.new('RGB', self.image.size, (255, 255, 255))
                background.paste(self.image, mask=self.image.split()[-1])
                self.image = background
            
            elif original_mode == 'L':
                # Grayscale to RGB
                logger.debug("Converting Grayscale to RGB")
                self.image = self.image.convert('RGB')
            
            elif original_mode == 'P':
                # Palette mode to RGB
                logger.debug("Converting Palette mode to RGB")
                self.image = self.image.convert('RGB')
            
            elif original_mode == '1':
                # 1-bit black and white to RGB
                logger.debug("Converting 1-bit B&W to RGB")
                self.image = self.image.convert('RGB')
            
            elif original_mode == 'LA':
                # Grayscale with alpha to RGB
                logger.debug("Converting Grayscale+Alpha to RGB")
                background = Image.new('RGB', self.image.size, (255, 255, 255))
                # Split and use alpha channel
                gray, alpha = self.image.split()
                rgb_img = Image.merge('RGB', (gray, gray, gray))
                background.paste(rgb_img, mask=alpha)
                self.image = background
            
            elif original_mode in ['CMYK', 'YCbCr', 'LAB', 'HSV']:
                # Special color spaces - convert to RGB
                logger.debug(f"Converting {original_mode} color space to RGB")
                try:
                    self.image = self.image.convert('RGB')
                except Exception as conv_error:
                    self.status_message.emit(
                        f"Cannot convert {original_mode} color mode: {conv_error}"
                    )
                    return False
            
            else:
                # Unknown or unsupported mode - try to convert
                logger.debug(f"⚠️  Unknown color mode '{original_mode}', attempting RGB conversion")
                try:
                    self.image = self.image.convert('RGB')
                except Exception as conv_error:
                    self.status_message.emit(
                        f"Unsupported color mode '{original_mode}'. "
                        f"Cannot convert to RGB: {conv_error}"
                    )
                    return False
            
            # Verify final conversion
            if self.image.mode != 'RGB':
                if progress:
                    progress.close()
                self.status_message.emit(
                    f"Color conversion failed. Expected RGB, got {self.image.mode}"
                )
                return False
            
            # === CLOSE PROGRESS DIALOG ===
            if progress:
                progress.close()
            
            filename = os.path.basename(path)
            self.status_message.emit(f"Loaded {filename}")
            self.clear_cache()  # Clear QImage cache for new image
            self.image_loaded.emit(path)
            return True
            
        except (IOError, OSError) as e:
            # SAFETY FIX: Specific handling for file I/O errors
            if 'progress' in locals() and progress:
                progress.close()
            self.status_message.emit(f"Cannot access file: {e}")
            # MEMORY FIX: Close image before clearing reference
            if self.image is not None:
                try:
                    self.image.close()
                except Exception:
                    pass
            self.image = None
            return False
        except Exception as ex:
            # SAFETY FIX: Generic fallback with image cleanup
            if 'progress' in locals() and progress:
                progress.close()
            self.status_message.emit(f"Error loading image: {ex}")
            # MEMORY FIX: Close image before clearing reference
            if self.image is not None:
                try:
                    self.image.close()
                except Exception:
                    pass
            self.image = None
            return False


    def get_image_size(self) -> tuple[int, int] | None:
        """Get original image dimensions."""
        if self.image:
            return self.image.size
        return None

    def get_scaled_size(self) -> tuple[int, int] | None:
        """Get image size at current zoom level."""
        if self.image:
            w, h = self.image.size
            return (int(w * self.zoom_level), int(h * self.zoom_level))
        return None

    def calculate_fit_zoom(self, container_size: tuple[int, int]) -> float:
        """Calculate zoom level to fit image in container."""
        if not self.image:
            return 1.0
            
        container_w, container_h = container_size
        if container_w <= 1 or container_h <= 1:
            return 1.0
            
        img_w, img_h = self.image.size
        zoom = min(container_w / img_w, container_h / img_h)
        return max(0.1, min(10.0, zoom))  # Clamp between 10% and 1000%

    def set_zoom_level(self, zoom: float) -> None:
        """Set the zoom level."""
        old_zoom = self.zoom_level
        self.zoom_level = max(0.1, min(10.0, zoom))  # Clamp between 10% and 1000%
        
        if abs(old_zoom - self.zoom_level) > 0.001:  # Only emit if changed significantly
            self.clear_cache()  # Clear QImage cache when zoom changes
            self.zoom_changed.emit(self.zoom_level)

    def zoom_at_point(self, zoom_factor: float, point: tuple[int, int]) -> tuple[float, float]:
        """
        Zoom at a specific point and return the new scroll position.
        
        Args:
            zoom_factor: Multiplier for current zoom (e.g., 1.1 for zoom in)
            point: (x, y) coordinates of zoom center in scaled image space
            
        Returns:
            (scroll_x, scroll_y) as fractions (0.0-1.0) for new scroll position
        """
        if not self.image:
            return (0.0, 0.0)
            
        old_zoom = self.zoom_level
        # Safety: Ensure old_zoom is reasonable (not zero or too small)
        if old_zoom <= 0.001:
            old_zoom = 1.0
        
        self.set_zoom_level(self.zoom_level * zoom_factor)
        
        # Calculate new position to keep point centered
        # Additional safety: Check old_zoom is significantly greater than zero
        if abs(old_zoom) > 0.001:
            zoom_ratio = self.zoom_level / old_zoom
            new_x = point[0] * zoom_ratio
            new_y = point[1] * zoom_ratio
            
            # Convert to scroll fractions
            scaled_size = self.get_scaled_size()
            if scaled_size:
                scaled_w, scaled_h = scaled_size
                # Safety: Ensure dimensions are reasonable (greater than 1)
                if scaled_w > 1 and scaled_h > 1:
                    scroll_x = max(0.0, min(1.0, new_x / scaled_w))
                    scroll_y = max(0.0, min(1.0, new_y / scaled_h))
                    return (scroll_x, scroll_y)
            
        return (0.0, 0.0)

    def get_pixel_at_coordinates(self, x: int, y: int) -> tuple[int, int, int] | None:
        """
        Get pixel color at image coordinates.
        
        Args:
            x, y: Coordinates in original image space
            
        Returns:
            RGB tuple or None if coordinates are invalid
        """
        if not self.image:
            return None
            
        img_w, img_h = self.image.size
        if 0 <= x < img_w and 0 <= y < img_h:
            try:
                pixel = self.image.getpixel((x, y))
                
                # Handle different pixel formats
                if isinstance(pixel, tuple):
                    # RGB or RGBA
                    return pixel[:3]  # Take RGB, ignore alpha if present
                else:
                    # Grayscale
                    return (pixel, pixel, pixel)
            except Exception:
                return None
        return None

    def sample_region(self, x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int] | None:
        """
        Sample a rectangular region and return average color.
        
        Args:
            x1, y1, x2, y2: Rectangle bounds in original image coordinates
            
        Returns:
            Average RGB color or None if region is invalid
        """
        if not self.image:
            return None
            
        # Ensure valid bounds
        img_w, img_h = self.image.size
        x1, x2 = max(0, min(x1, x2)), min(img_w, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(img_h, max(y1, y2))
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        try:
            # Extract region and get pixel data
            region = self.image.crop((x1, y1, x2, y2))
            pixels = list(region.getdata())
            
            # Convert to RGB if needed and calculate average
            rgb_pixels = []
            for pixel in pixels:
                if isinstance(pixel, tuple):
                    rgb_pixels.append(pixel[:3])
                else:
                    rgb_pixels.append((pixel, pixel, pixel))
                    
            return ColorMath.calculate_average_region_color(rgb_pixels)
        except Exception:
            return None

    def canvas_to_image_coords(self, canvas_x: float, canvas_y: float) -> tuple[int, int]:
        """
        Convert canvas coordinates to original image coordinates.
        
        Args:
            canvas_x, canvas_y: Coordinates in scaled canvas space
            
        Returns:
            (x, y) in original image coordinates
        """
        if not self.image:
            return (0, 0)
            
        img_w, img_h = self.image.size
        scaled_size = self.get_scaled_size()
        
        if not scaled_size:
            return (0, 0)
        
        scaled_w, scaled_h = scaled_size
        
        # SAFETY FIX: Prevent division by zero or extremely small values
        if scaled_w <= 0 or scaled_h <= 0:
            return (0, 0)
        
        # Clamp input coordinates to valid range
        canvas_x = max(0, min(scaled_w - 1, canvas_x))
        canvas_y = max(0, min(scaled_h - 1, canvas_y))
        
        try:
            # Safe division with integer conversion
            img_x = int((canvas_x * img_w) / scaled_w)
            img_y = int((canvas_y * img_h) / scaled_h)
            
            # Ensure result is within image bounds
            img_x = max(0, min(img_w - 1, img_x))
            img_y = max(0, min(img_h - 1, img_y))
            
            return (img_x, img_y)
        except (ZeroDivisionError, OverflowError):
            # Fallback to safe default
            return (0, 0)


    MAX_SIZE = (8192, 8192)
    def get_resized_image(self) -> Image.Image | None:
        """Get image resized to current zoom level."""
        if not self.image:
            return None
            
        scaled_size = self.get_scaled_size()
        if scaled_size:
            scaled_w, scaled_h = scaled_size
            # Clamp to max size
            scaled_w = min(scaled_w, self.MAX_SIZE[0])
            scaled_h = min(scaled_h, self.MAX_SIZE[1])
            if scaled_w > 0 and scaled_h > 0:
                try:
                    return self.image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                except Exception:
                    return self.image.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)
        return None

    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.set_zoom_level(1.0)

    def fit_to_container(self, container_size: tuple[int, int]) -> None:
        """Fit image to container size."""
        zoom = self.calculate_fit_zoom(container_size)
        self.set_zoom_level(zoom)
        self.last_fit_width, self.last_fit_height = container_size


    def clear_cache(self) -> None:
        """Clear all image caches (QImage and QPixmap)."""
        self._cached_qimage = None
        self._cached_zoom = None
        # Also clear pixmap cache
        if self.pixmap_cache:
            cleared = self.pixmap_cache.clear()
            if logger:
                logger.debug(f"Cleared {cleared} cached pixmaps")
    
    def get_qimage(self) -> 'QImage | None':
        """
        Get QImage for display, using cache if possible.
        This avoids expensive PIL to QImage conversion on every display call.
        
        Returns:
            QImage or None if no image loaded
        """
        if not self.image:
            return None
        
        # Check if cache is valid
        if (self._cached_qimage is not None and 
            self._cached_zoom == self.zoom_level):
            # Cache hit - return cached QImage
            return self._cached_qimage
        
        # Cache miss - create new QImage
        try:
            from PyQt6.QtGui import QImage
            
            # Get resized PIL image
            pil_image = self.get_resized_image()
            if not pil_image:
                return None
            
            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to QImage
            width, height = pil_image.size
            img_bytes = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(img_bytes, width, height, width * 3, QImage.Format.Format_RGB888)
            
            # Cache the result
            self._cached_qimage = qimage
            self._cached_zoom = self.zoom_level
            
            return qimage
            
        except Exception as e:
            logger.error(f"Error creating QImage: {e}")
            return None

    def clear_image(self) -> None:
        """Clear the loaded image and free memory."""
        # MEMORY FIX: Properly close PIL image to free memory
        if self.image is not None:
            try:
                self.image.close()
            except Exception:
                pass  # Ignore errors during cleanup
        self.image = None
        self.image_path = None
        self.zoom_level = 1.0
        self.clear_cache()  # Clear QImage cache
        self.image_cleared.emit()
        self.status_message.emit("Image cleared")

    def is_loaded(self) -> bool:
        """Check if an image is currently loaded."""
        return self.image is not None

    def get_image_info(self) -> dict:
        """Get information about the loaded image."""
        if not self.image:
            return {}
            
        return {
            "path": self.image_path,
            "size": self.image.size,
            "mode": self.image.mode,
            "format": getattr(self.image, 'format', 'Unknown'),
            "zoom": self.zoom_level,
            "scaled_size": self.get_scaled_size()
        }

    def get_supported_formats(self) -> list[str]:
        """Get list of supported image formats."""
        return [
            "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", 
            "*.tiff", "*.tif", "*.webp", "*.ico"
        ]

    def zoom_in(self, point: tuple[int, int] | None = None) -> None:
        """Zoom in by 10%."""
        if point:
            self.zoom_at_point(1.1, point)
        else:
            self.set_zoom_level(self.zoom_level * 1.1)

    def zoom_out(self, point: tuple[int, int] | None = None) -> None:
        """Zoom out by 10%."""
        if point:
            self.zoom_at_point(0.9, point)
        else:
            self.set_zoom_level(self.zoom_level * 0.9)
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
Clears image, cache, and references.
        """
        try:
            # Clear the image
            self.clear_image()
            
            # Clear pixmap cache
            if hasattr(self, 'pixmap_cache') and self.pixmap_cache:
                cleared = self.pixmap_cache.clear()
                if logger:
                    logger.debug(f"Cleared {cleared} cached pixmaps")
                self.pixmap_cache = None
            
            # Clear cached QImage
            self._cached_qimage = None
            self._cached_zoom = None
            
            if logger:
                logger.debug("ImageHandler cleanup complete")
                
        except Exception as e:
            if logger:
                logger.error(f"Error during ImageHandler cleanup: {e}")