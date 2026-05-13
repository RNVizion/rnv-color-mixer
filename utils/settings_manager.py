"""
Settings Manager for Color Mixer Application
Handles user preferences, persistence, and configuration management.
"""

import json
import os
from typing import Any
from pathlib import Path

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("SettingsManager")
except ImportError:
    logger = None


class SettingsManager:
    """Manages application settings and user preferences."""
    
    # Default settings configuration
    DEFAULT_SETTINGS = {
        "version": "3.0",
        "preferences": {
            # General Preferences
            "theme": "dark",  # "dark", "light", "image", "auto"
            "auto_save_colors": True,
            "auto_load_last_session": False,
            
            # Color Slot Defaults
            "default_slot_weight": 50,
            "default_slot_color": [200, 200, 200],  # RGB
            "max_color_slots": 12,
            
            # History Settings
            "history_enabled": True,
            "history_size_limit": 50,  # Maximum colors to keep
            "auto_add_to_history": True,
            
            # Preset Palettes
            "default_palette_category": "All",
            "show_palette_previews": True,
            
            # Color Harmony
            "default_harmony_type": "Complementary",
            "auto_generate_harmony": False,
            
            # Export Settings
            "default_export_format": "png",  # png, json, ase, etc.
            "export_location": "",  # Empty = ask each time
            
            # UI Preferences
            "show_tooltips": True,
            "show_debug_overlays": False,
            "compact_mode": False,
        },
        "keyboard_shortcuts": {
            "upload_image": "Ctrl+O",
            "save_swatch": "Ctrl+S",
            "copy_hex": "Ctrl+C",
            "add_slot": "Ctrl+N",
            "open_panel": "Ctrl+P,Ctrl+,",  # Multiple shortcuts separated by comma
            "pick_screen_color": "Ctrl+Shift+C",
            "toggle_debug": "F12",
        },
        "window": {
            "main_width": 1130,
            "main_height": 610,  # Updated to accommodate HSV label
            "package_d_width": 630,
            "package_d_height": 666,
            "remember_size": True,
            "remember_position": False,
        },
        "advanced": {
            # Available mixing algorithms:
            # "weighted_rgb" - Standard digital mixing (default)
            # "weighted_hsv" - HSV perceptual mixing
            # "lab_perceptual" - LAB color space mixing
            # "subtractive_cmy" - Subtractive CMY (inks/dyes)
            # "weighted_ryb" - Artist's RYB color wheel
            # "kubelka_munk" - Kubelka-Munk paint theory
            "color_mixing_algorithm": "weighted_rgb",
            "decimal_precision": 2,
            "show_rgb_values": True,
            "show_hsv_values": False,
            "enable_animations": True,
        }
    }
    
    def __init__(self):
        """Initialize the settings manager."""
        self.settings: dict[str, Any] = {}
        self.settings_file: Path | None = None
        self._setup_settings_path()
        self.load_settings()
    
    def _setup_settings_path(self) -> None:
        """Determine the settings file path based on OS."""
        try:
            if os.name == 'nt':  # Windows
                app_data = os.getenv('APPDATA')
                if app_data:
                    settings_dir = Path(app_data) / "ColorMixer"
                else:
                    settings_dir = Path.home() / "ColorMixer"
            elif os.name == 'posix':
                if os.uname().sysname == 'Darwin':  # macOS
                    settings_dir = Path.home() / "Library" / "Application Support" / "ColorMixer"
                else:  # Linux
                    settings_dir = Path.home() / ".config" / "ColorMixer"
            else:
                # Fallback
                settings_dir = Path.home() / ".colormixer"
            
            # Create directory if it doesn't exist
            settings_dir.mkdir(parents=True, exist_ok=True)
            
            self.settings_file = settings_dir / "settings.json"
            logger.info(f"Settings file: {self.settings_file}") if logger else None
            
        except Exception as e:
            logger.error(f"Error setting up settings path: {e}")
            # Fallback to local directory
            self.settings_file = Path("settings.json")
    
    def load_settings(self) -> None:
        """Load settings from file, or create defaults if not found."""
        try:
            if self.settings_file and self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                self.settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), loaded_settings)
                logger.success(f"Settings loaded from {self.settings_file}") if logger else None
            else:
                # Use defaults
                import copy
                self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
                logger.info("Using default settings")
                # Save defaults
                self.save_settings()
        
        except Exception as e:
            logger.error("Error loading settings", error=e) if logger else None
            import copy
            self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            if not self.settings_file:
                logger.warning("No settings file path configured")
                return False
            
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            logger.success(f"Settings saved to {self.settings_file}") if logger else None
            return True
        
        except Exception as e:
            logger.error("Error saving settings", error=e) if logger else None
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation.
        
        Example:
            settings.get("preferences.theme")
            settings.get("keyboard_shortcuts.upload_image")
        """
        try:
            keys = key_path.split('.')
            value = self.settings
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        
        except Exception as e:
            logger.error(f"Error getting setting '{key_path}': {e}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set a setting value using dot notation.
        
        Example:
            settings.set("preferences.theme", "dark")
            settings.set("keyboard_shortcuts.upload_image", "Ctrl+O")
        """
        try:
            keys = key_path.split('.')
            current = self.settings
            
            # Navigate to the parent of the final key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            return True
        
        except Exception as e:
            logger.error(f"Error setting '{key_path}': {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        import copy
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        logger.info("Settings reset to defaults")
    
    def export_settings(self, filepath: str) -> bool:
        """Export settings to a specific file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.success(f"Settings exported to {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """Import settings from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            self.settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), imported_settings)
            
            # Save the imported settings
            self.save_settings()
            
            logger.success(f"Settings imported from {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False
    
    def _merge_settings(self, defaults: dict, loaded: dict) -> dict:
        """
        Recursively merge loaded settings with defaults.
        This ensures new settings added in updates are included.
        """
        result = defaults.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = self._merge_settings(result[key], value)
            else:
                # Use loaded value
                result[key] = value
        
        return result
    
    def get_all_preferences(self) -> dict:
        """Get all user preferences."""
        return self.settings.get("preferences", {})
    
    def get_all_shortcuts(self) -> dict:
        """Get all keyboard shortcuts."""
        return self.settings.get("keyboard_shortcuts", {})
    
    def validate_settings(self) -> tuple[bool, list[str]]:
        """
        Validate settings and return (is_valid, errors).
        """
        errors = []
        
        try:
            # Check version
            if "version" not in self.settings:
                errors.append("Missing version field")
            
            # Check required sections
            required_sections = ["preferences", "keyboard_shortcuts", "window"]
            for section in required_sections:
                if section not in self.settings:
                    errors.append(f"Missing section: {section}")
            
            # Validate numeric ranges
            prefs = self.settings.get("preferences", {})
            
            # Weight should be 0-100
            weight = prefs.get("default_slot_weight", 50)
            if not 0 <= weight <= 100:
                errors.append(f"Invalid default_slot_weight: {weight} (must be 0-100)")
            
            # History limit should be positive
            history_limit = prefs.get("history_size_limit", 50)
            if not 1 <= history_limit <= 1000:
                errors.append(f"Invalid history_size_limit: {history_limit} (must be 1-1000)")
            
            # Theme should be valid
            theme = prefs.get("theme", "dark")
            if theme not in ["dark", "light", "image", "auto"]:
                errors.append(f"Invalid theme: {theme}")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def get_settings_info(self) -> dict:
        """Get information about settings file."""
        info = {
            "file_path": str(self.settings_file) if self.settings_file else "Not set",
            "exists": self.settings_file.exists() if self.settings_file else False,
            "valid": False,
            "errors": []
        }
        
        if self.settings_file and self.settings_file.exists():
            try:
                file_size = self.settings_file.stat().st_size
                info["file_size"] = f"{file_size} bytes"
            except Exception:
                info["file_size"] = "Unknown"
        
        is_valid, errors = self.validate_settings()
        info["valid"] = is_valid
        info["errors"] = errors
        
        return info


# Singleton instance
_settings_instance: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance


# Convenience functions
def get_setting(key_path: str, default: Any = None) -> Any:
    """Get a setting value."""
    return get_settings_manager().get(key_path, default)


def set_setting(key_path: str, value: Any) -> bool:
    """Set a setting value."""
    return get_settings_manager().set(key_path, value)


def save_settings() -> bool:
    """Save settings to file."""
    return get_settings_manager().save_settings()