"""
File handling utilities for the Color Mixer application (PyQt6 version).
Provides path handling and file dialog wrappers.
Now supports all palette formats.
"""

import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from utils import config

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("FileUtils")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class FileUtils:
    """Utilities for file operations and dialog handling (PyQt6 version)."""
    
    def __init__(self, parent: QWidget | None = None):
        self.parent = parent

    def select_image_file(self, title: str = "Select Image") -> str | None:
        """
        Open file dialog to select an image file.
        
        Args:
            title: Dialog window title
            
        Returns:
            Selected file path or None if cancelled
        """
        file_filter = "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.ico);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            title,
            "",
            file_filter
        )
        return file_path if file_path else None

    def select_save_location(self, title: str = "Save File", 
                           default_ext: str = ".png",
                           file_types: list[str] | None = None) -> str | None:
        """
        Open file dialog to select save location.
        
        Args:
            title: Dialog window title
            default_ext: Default file extension
            file_types: List of file type filters
            
        Returns:
            Selected file path or None if cancelled
        """
        if file_types is None:
            file_filter = "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        else:
            file_filter = ";;".join(file_types) + ";;All Files (*)"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            title,
            "",
            file_filter
        )
        
        if file_path:
            # Ensure file has proper extension
            if not os.path.splitext(file_path)[1]:
                file_path += default_ext
        
        return file_path if file_path else None

    def select_palette_export_location(self) -> str | None:
        """
        Open file dialog to select palette export location.
        Supports all palette formats.
        
        Returns:
            Selected file path or None if cancelled
        """
        file_filters = [
            "Adobe Swatch Exchange (*.ase)",
            "Adobe Color (*.aco)",
            "Adobe Color Book (*.acb)",
            "GIMP Palette (*.gpl)",
            "Procreate Swatches (*.swatches)",
            "Affinity Palette (*.afpalette)",
            "macOS Colors (*.clr)",
            "Colors File (*.colors)",
            "CSS Variables (*.css)",
            "JSON (*.json)",
            "XML (*.xml)",
            "SVG Palette (*.svg)",
            "HEX Text (*.hex)",
            "HSV Text (*.hsv)",
            "HSL Text (*.hsl)",
            "Plain Text (*.txt)",
            "All Files (*)"
        ]
        
        file_filter = ";;".join(file_filters)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.parent,
            "Export Palette",
            "",
            file_filter
        )
        
        if file_path:
            # Auto-add extension based on selected filter if no extension provided
            if not os.path.splitext(file_path)[1]:
                # Extract extension from filter
                import re
                match = re.search(r'\*(\.\w+)', selected_filter)
                if match:
                    file_path += match.group(1)
        
        return file_path if file_path else None

    def select_palette_import_file(self) -> str | None:
        """
        Open file dialog to select palette import file.
        Supports all importable palette formats including optional ones.
        
        Returns:
            Selected file path or None if cancelled
        """
        file_filters = [
            "All Supported Formats (*.gpl *.ase *.aco *.afpalette *.colors *.css *.json *.xml *.hex *.hsv *.hsl *.txt *.svg *.clr *.swatches)",
            "GIMP Palette (*.gpl)",
            "Adobe Swatch Exchange (*.ase)",
            "Adobe Color (*.aco)",
            "Affinity Palette (*.afpalette)",
            "Colors File (*.colors)",
            "CSS Variables (*.css)",
            "JSON (*.json)",
            "XML (*.xml)",
            "HEX Text (*.hex)",
            "HSV Text (*.hsv)",
            "HSL Text (*.hsl)",
            "Plain Text (*.txt)",
            "SVG Palette - extraction only (*.svg)",
            "macOS Colors - XML variant only (*.clr)",
            "Procreate Swatches - basic format (*.swatches)",
            "All Files (*)"
        ]
        
        file_filter = ";;".join(file_filters)
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Import Palette",
            "",
            file_filter
        )
        return file_path if file_path else None

    @staticmethod
    def ensure_file_extension(filepath: str, default_ext: str) -> str:
        """
        Ensure file has proper extension.
        
        Args:
            filepath: Original file path
            default_ext: Default extension to add if missing
            
        Returns:
            File path with proper extension
        """
        if not os.path.splitext(filepath)[1]:
            return filepath + default_ext
        return filepath

    @staticmethod
    def validate_file_path(filepath: str, must_exist: bool = False) -> bool:
        """
        Validate a file path.
        
        Args:
            filepath: Path to validate
            must_exist: Whether file must already exist
            
        Returns:
            True if path is valid
        """
        if not filepath:
            return False
            
        try:
            # Check if directory exists (for save operations)
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                return False
                
            # Check if file exists (for load operations)
            if must_exist and not os.path.exists(filepath):
                return False
                
            return True
        except Exception:
            # Filesystem check failed (permission, I/O, or missing path)
            return False

    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """
        Create a safe filename by removing invalid characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = ''.join(c for c in filename if c not in invalid_chars)
        
        # Limit length
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length-len(ext)] + ext
            
        return safe_name

    def show_error_dialog(self, title: str, message: str) -> None:
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self.parent, title, message)

    def show_warning_dialog(self, title: str, message: str) -> None:
        """
        Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Warning message
        """
        QMessageBox.warning(self.parent, title, message)

    def show_info_dialog(self, title: str, message: str) -> None:
        """
        Show an info dialog.
        
        Args:
            title: Dialog title
            message: Info message
        """
        QMessageBox.information(self.parent, title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """
        Ask user a yes/no question.
        
        Args:
            title: Dialog title
            message: Question message
            
        Returns:
            True if user clicked Yes, False otherwise
        """
        result = QMessageBox.question(
            self.parent, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return result == QMessageBox.StandardButton.Yes

    def show_format_info_dialog(self, filepath: str) -> None:
        """
        Show information about the selected palette format.
        
        Args:
            filepath: Path to palette file
        """
        try:
            from core.palette_formats import PaletteFormats
            
            ext = os.path.splitext(filepath)[1].lower()
            info = PaletteFormats.get_format_info(ext)
            
            if info.get('name') != 'Unknown':
                # Use list join instead of string concatenation
                parts = [
                    f"Format: {info['name']}",
                    f"Type: {info['type']}",
                    f"Support: {info['support']}",
                    f"Compatible Apps: {', '.join(info['apps'])}"
                ]
                message = "\n".join(parts)
                
                self.show_info_dialog("Palette Format Info", message)
        except Exception as e:
            logger.error(f"Error showing format info: {e}")

    @staticmethod
    def create_directory_if_not_exists(directory: str) -> bool:
        """
        Create directory if it doesn't exist.
        
        Args:
            directory: Directory path to create
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False

    @staticmethod
    def get_file_size_mb(filepath: str) -> float | None:
        """
        Get file size in megabytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in MB or None if file doesn't exist
        """
        try:
            size_bytes = os.path.getsize(filepath)
            return size_bytes / (1024 * 1024)
        except Exception:
            # File may not exist or be inaccessible — size is unknown
            return None

    @staticmethod
    def backup_file(filepath: str, backup_suffix: str = ".bak") -> str | None:
        """
        Create a backup copy of a file.
        
        Args:
            filepath: Original file path
            backup_suffix: Suffix to add to backup filename
            
        Returns:
            Backup file path or None if failed
        """
        try:
            if not os.path.exists(filepath):
                return None
                
            backup_path = filepath + backup_suffix
            
            # Read and write file content
            with open(filepath, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
                
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup of {filepath}: {e}")
            return None

    def get_recent_files(self, max_files: int = 10) -> list[str]:
        """
        Get list of recently opened files.
        
        Reserved for future persistence via application settings. Currently
        returns an empty list; callers should handle this as "no history yet."
        
        Args:
            max_files: Maximum number of files to return
            
        Returns:
            List of recent file paths (empty until persistence is wired up)
        """
        return []

    def add_to_recent_files(self, filepath: str) -> None:
        """
        Add a file to the recent files list.
        
        Reserved for future persistence via application settings. Currently
        a no-op; safe to call without side effects.
        
        Args:
            filepath: File path to add
        """
        # Reserved for future implementation — intentionally a no-op
        return

    @staticmethod
    def get_supported_palette_extensions() -> list[str]:
        """
        Get list of all supported palette file extensions.
        
        Returns:
            List of extensions (with dots)
        """
        return [
            '.ase', '.aco', '.acb', '.gpl', '.swatches', '.afpalette',
            '.clr', '.colors', '.css', '.json', '.xml', '.svg',
            '.hex', '.hsv', '.hsl', '.txt'
        ]

    @staticmethod
    def is_palette_file(filepath: str) -> bool:
        """
        Check if file is a supported palette format.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file has a supported palette extension
        """
        ext = os.path.splitext(filepath)[1].lower()
        return ext in FileUtils.get_supported_palette_extensions()

    def auto_detect_and_import_palette(self, filepath: str) -> list[tuple[tuple[int, int, int], int]] | None:
        """
        Auto-detect palette format and import.
        
        Args:
            filepath: Path to palette file
            
        Returns:
            List of (color, weight) tuples or None if failed
        """
        try:
            from core.palette_formats import PaletteFormats
            
            # Try to detect format
            detected_ext = PaletteFormats.detect_format(filepath)
            if detected_ext:
                logger.debug(f"Detected format: {detected_ext}")
            
            # Import palette
            colors = PaletteFormats.import_palette(filepath)
            
            if colors:
                # Validate colors
                colors = PaletteFormats.validate_colors(colors)
                return colors
            else:
                self.show_warning_dialog(
                    "Import Warning",
                    "No valid colors found in the file."
                )
                return None
                
        except Exception as e:
            self.show_error_dialog(
                "Import Error",
                f"Failed to import palette:\n{str(e)}"
            )
            return None