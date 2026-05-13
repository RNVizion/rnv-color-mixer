# -*- coding: utf-8 -*-
"""
Preset Palettes Module - Built-in color schemes
Contains professionally designed color palettes ready to use
"""

import json
import os

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("PresetPalettes")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class PresetPalette:
    """A single preset palette with colors and metadata."""
    
    def __init__(self, name: str, colors: list[tuple[int, int, int]], 
                 description: str = "", category: str = "General", icon: str = "🎨"):
        self.name = name
        self.colors = colors
        self.description = description
        self.category = category
        self.icon = icon
        
    def get_colors_with_weights(self, default_weight: int = 50) -> list[tuple[tuple[int, int, int], int]]:
        """Get colors with default weights."""
        return [(color, default_weight) for color in self.colors]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "colors": self.colors,
            "description": self.description,
            "category": self.category,
            "icon": self.icon
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PresetPalette':
        """Create from dictionary."""
        return PresetPalette(
            name=data["name"],
            colors=[tuple(c) for c in data["colors"]],
            description=data.get("description", ""),
            category=data.get("category", "General"),
            icon=data.get("icon", "🎨")
        )


class PresetPalettes:
    """Manages preset color palettes."""
    
    # Built-in presets
    BUILT_IN_PRESETS = [
        PresetPalette(
            name="Rainbow",
            colors=[
                (255, 0, 0),      # Red
                (255, 127, 0),    # Orange
                (255, 255, 0),    # Yellow
                (0, 255, 0),      # Green
                (0, 0, 255),      # Blue
                (75, 0, 130),     # Indigo
                (148, 0, 211),    # Violet
            ],
            description="Classic rainbow spectrum - 7 vibrant colors",
            category="Basic",
            icon="🌈"
        ),
        PresetPalette(
            name="Earth Tones",
            colors=[
                (139, 90, 43),    # Saddle Brown
                (160, 82, 45),    # Sienna
                (205, 133, 63),   # Peru
                (210, 180, 140),  # Tan
                (107, 142, 35),   # Olive Drab
                (85, 107, 47),    # Dark Olive Green
                (128, 128, 0),    # Olive
            ],
            description="Natural browns, greens, and earth colors",
            category="Nature",
            icon="🌍"
        ),
        PresetPalette(
            name="Pastels",
            colors=[
                (255, 179, 186),  # Pastel Pink
                (255, 223, 186),  # Pastel Peach
                (255, 255, 186),  # Pastel Yellow
                (186, 255, 201),  # Pastel Mint
                (186, 225, 255),  # Pastel Blue
                (221, 186, 255),  # Pastel Purple
                (255, 186, 238),  # Pastel Magenta
            ],
            description="Soft, delicate pastel colors",
            category="Soft",
            icon="🎨"
        ),
        PresetPalette(
            name="Grayscale",
            colors=[
                (0, 0, 0),        # Black
                (64, 64, 64),     # Dark Gray
                (128, 128, 128),  # Gray
                (192, 192, 192),  # Light Gray
                (255, 255, 255),  # White
            ],
            description="Black to white spectrum",
            category="Basic",
            icon="⚫"
        ),
        PresetPalette(
            name="Neon",
            colors=[
                (255, 0, 255),    # Neon Magenta
                (0, 255, 255),    # Neon Cyan
                (255, 255, 0),    # Neon Yellow
                (57, 255, 20),    # Neon Green
                (255, 20, 147),   # Neon Pink
                (255, 69, 0),     # Neon Orange Red
            ],
            description="Bright, electric neon colors",
            category="Bright",
            icon="💡"
        ),
        PresetPalette(
            name="Ocean",
            colors=[
                (0, 105, 148),    # Deep Ocean
                (0, 119, 182),    # Ocean Blue
                (3, 169, 244),    # Sky Blue
                (77, 208, 225),   # Turquoise
                (128, 222, 234),  # Light Cyan
                (176, 224, 230),  # Powder Blue
            ],
            description="Blues and teals inspired by the ocean",
            category="Nature",
            icon="🌊"
        ),
        PresetPalette(
            name="Fire",
            colors=[
                (139, 0, 0),      # Dark Red
                (178, 34, 34),    # Firebrick
                (220, 20, 60),    # Crimson
                (255, 69, 0),     # Red Orange
                (255, 140, 0),    # Dark Orange
                (255, 215, 0),    # Gold
            ],
            description="Reds, oranges, and yellows like flames",
            category="Warm",
            icon="🔥"
        ),
        PresetPalette(
            name="Sunset",
            colors=[
                (253, 94, 83),    # Sunset Red
                (255, 107, 107),  # Sunset Pink
                (255, 159, 64),   # Sunset Orange
                (255, 202, 58),   # Sunset Yellow
                (255, 234, 167),  # Sunset Cream
            ],
            description="Warm sunset colors",
            category="Warm",
            icon="🌆"
        ),
        PresetPalette(
            name="Forest",
            colors=[
                (34, 139, 34),    # Forest Green
                (46, 125, 50),    # Dark Forest
                (76, 175, 80),    # Green
                (139, 195, 74),   # Light Green
                (205, 220, 57),   # Lime
                (130, 119, 23),   # Olive
            ],
            description="Greens inspired by forests",
            category="Nature",
            icon="🌲"
        ),
        PresetPalette(
            name="Candy",
            colors=[
                (255, 105, 180),  # Hot Pink
                (255, 182, 193),  # Light Pink
                (173, 216, 230),  # Light Blue
                (221, 160, 221),  # Plum
                (255, 218, 185),  # Peach
                (152, 251, 152),  # Pale Green
            ],
            description="Sweet candy colors",
            category="Soft",
            icon="🍂"
        ),
        PresetPalette(
            name="Autumn",
            colors=[
                (139, 69, 19),    # Saddle Brown
                (165, 42, 42),    # Brown
                (184, 134, 11),   # Dark Goldenrod
                (218, 165, 32),   # Goldenrod
                (240, 128, 128),  # Light Coral
                (205, 92, 92),    # Indian Red
            ],
            description="Autumn leaf colors",
            category="Nature",
            icon="🌺"
        ),
        PresetPalette(
            name="Monochrome Blue",
            colors=[
                (25, 25, 112),    # Midnight Blue
                (0, 0, 128),      # Navy
                (0, 0, 255),      # Blue
                (30, 144, 255),   # Dodger Blue
                (135, 206, 250),  # Light Sky Blue
                (173, 216, 230),  # Light Blue
            ],
            description="Shades of blue from dark to light",
            category="Monochrome",
            icon="❄️"
        ),
        PresetPalette(
            name="Monochrome Red",
            colors=[
                (128, 0, 0),      # Maroon
                (139, 0, 0),      # Dark Red
                (255, 0, 0),      # Red
                (255, 99, 71),    # Tomato
                (255, 160, 122),  # Light Salmon
                (255, 192, 203),  # Pink
            ],
            description="Shades of red from dark to light",
            category="Monochrome",
            icon="☁️"
        ),
        PresetPalette(
            name="Vintage",
            colors=[
                (188, 143, 143),  # Rosy Brown
                (205, 175, 149),  # Vintage Tan
                (189, 183, 107),  # Dark Khaki
                (188, 143, 143),  # Vintage Rose
                (176, 196, 222),  # Light Steel Blue
                (216, 191, 216),  # Thistle
            ],
            description="Muted vintage colors",
            category="Soft",
            icon="📩"
        ),
        PresetPalette(
            name="Tropical",
            colors=[
                (255, 20, 147),   # Deep Pink
                (255, 165, 0),    # Orange
                (255, 215, 0),    # Gold
                (50, 205, 50),    # Lime Green
                (0, 191, 255),    # Deep Sky Blue
                (138, 43, 226),   # Blue Violet
            ],
            description="Vibrant tropical colors",
            category="Bright",
            icon="👤"
        ),
    ]
    
    def __init__(self):
        self.custom_presets: list[PresetPalette] = []
        self.presets_file = os.path.join(os.path.expanduser("~"), ".color_mixer_presets.json")
        
        # Load custom presets
        self.load_custom_presets()
    
    def get_all_presets(self) -> list[PresetPalette]:
        """Get all presets (built-in + custom)."""
        return self.BUILT_IN_PRESETS + self.custom_presets
    
    def get_preset_by_name(self, name: str) -> PresetPalette | None:
        """Get a preset by name."""
        for preset in self.get_all_presets():
            if preset.name == name:
                return preset
        return None
    
    def get_presets_by_category(self, category: str) -> list[PresetPalette]:
        """Get presets in a specific category."""
        return [p for p in self.get_all_presets() if p.category == category]
    
    def get_categories(self) -> list[str]:
        """Get list of all categories."""
        categories = set(p.category for p in self.get_all_presets())
        return sorted(categories)
    
    def add_custom_preset(self, preset: PresetPalette) -> bool:
        """
        Add a custom preset.
        
        Args:
            preset: PresetPalette to add
            
        Returns:
            True if added successfully
        """
        try:
            # Check for duplicate names
            if any(p.name == preset.name for p in self.custom_presets):
                logger.debug(f"Preset '{preset.name}' already exists")
                return False
            
            self.custom_presets.append(preset)
            self.save_custom_presets()
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom preset: {e}")
            return False
    
    def remove_custom_preset(self, name: str) -> bool:
        """
        Remove a custom preset by name.
        
        Args:
            name: Name of preset to remove
            
        Returns:
            True if removed successfully
        """
        try:
            self.custom_presets = [p for p in self.custom_presets if p.name != name]
            self.save_custom_presets()
            return True
        except Exception as e:
            logger.error(f"Error removing custom preset: {e}")
            return False
    
    def save_custom_presets(self) -> bool:
        """Save custom presets to file."""
        try:
            data = {
                "version": "1.0",
                "presets": [p.to_dict() for p in self.custom_presets]
            }
            
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving custom presets: {e}")
            return False
    
    def load_custom_presets(self) -> bool:
        """Load custom presets from file."""
        try:
            if not os.path.exists(self.presets_file):
                return False
            
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.custom_presets = [
                PresetPalette.from_dict(p) 
                for p in data.get("presets", [])
            ]
            
            logger.info(f" Loaded {len(self.custom_presets)} custom presets")
            return True
            
        except Exception as e:
            logger.error(f"Error loading custom presets: {e}")
            self.custom_presets = []
            return False
    
    def create_preset_from_current_colors(
        self, 
        colors: list[tuple[int, int, int]], 
        name: str,
        description: str = "",
        category: str = "Custom",
        icon: str = "⭐"
    ) -> PresetPalette | None:
        """
        Create a new preset from current colors.
        
        Args:
            colors: List of RGB colors
            name: Preset name
            description: Optional description
            category: Category name
            icon: Icon emoji
            
        Returns:
            Created PresetPalette or None if failed
        """
        try:
            preset = PresetPalette(name, colors, description, category, icon)
            if self.add_custom_preset(preset):
                return preset
        except Exception as e:
            logger.error(f"Error creating preset: {e}")
        return None