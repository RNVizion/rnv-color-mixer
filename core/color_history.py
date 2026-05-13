"""
Color History Module - Track and recall mixed colors
Stores color mixing history with timestamps for easy recall
"""

import json
import os
from datetime import datetime
from core.color_math import ColorMath

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("ColorHistory")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class ColorHistoryEntry:
    """Single color history entry with metadata."""
    
    def __init__(self, color: tuple[int, int, int], timestamp: str | None = None, 
                 name: str | None = None):
        self.color = color
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.name = name or ColorMath.rgb_to_hex(color)
        
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            "color": self.color,
            "timestamp": self.timestamp,
            "name": self.name
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'ColorHistoryEntry':
        """Create entry from dictionary."""
        return ColorHistoryEntry(
            color=tuple(data["color"]),
            timestamp=data["timestamp"],
            name=data.get("name")
        )
    
    def get_display_time(self) -> str:
        """Get formatted display time (e.g., '2:15 PM')."""
        try:
            dt = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%I:%M %p")
        except Exception:
            # Malformed timestamp — fall back to raw stored string
            return self.timestamp


class ColorHistory:
    """Manages color mixing history."""
    
    def __init__(self, max_entries: int = 20):
        self.max_entries = max_entries
        self.entries: list[ColorHistoryEntry] = []
        self.history_file = os.path.join(os.path.expanduser("~"), ".color_mixer_history.json")
        
        # Load existing history
        self.load()
        
    def add_color(self, color: tuple[int, int, int], name: str | None = None) -> None:
        """
        Add a color to history.
        
        Args:
            color: RGB color tuple
            name: Optional custom name for the color
        """
        # Validate color
        color = ColorMath.validate_rgb(color)
        
        # Check if this exact color was just added (avoid duplicates in quick succession)
        if self.entries and self.entries[0].color == color:
            # Same color as last entry - check timestamp
            last_time = datetime.strptime(self.entries[0].timestamp, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            if (now - last_time).total_seconds() < 2:  # Within 2 seconds
                return  # Skip duplicate
        
        # Create new entry
        entry = ColorHistoryEntry(color, name=name)
        
        # Add to beginning of list (most recent first)
        self.entries.insert(0, entry)
        
        # Trim to max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]
        
        # Auto-save asynchronously (non-blocking)
        self.save_async()
        
    def get_entries(self) -> list[ColorHistoryEntry]:
        """Get all history entries (most recent first)."""
        return self.entries.copy()
        
    def clear(self) -> None:
        """Clear all history."""
        self.entries = []
        self.save_async()  # Non-blocking save
        
    def remove_entry(self, index: int) -> bool:
        """
        Remove entry at index.
        
        Args:
            index: Index of entry to remove
            
        Returns:
            True if removed successfully
        """
        try:
            if 0 <= index < len(self.entries):
                self.entries.pop(index)
                self.save_async()  # Non-blocking save
                return True
        except Exception as e:
            logger.error(f"Error removing history entry: {e}")
        return False
        
    def get_by_index(self, index: int) -> ColorHistoryEntry | None:
        """Get entry by index."""
        try:
            if 0 <= index < len(self.entries):
                return self.entries[index]
        except Exception:
            # Index or entry access may fail during concurrent modification
            pass
        return None
        
    def save(self) -> bool:
        """
        Save history to JSON file (synchronous).
        
        Returns:
            True if saved successfully
        """
        try:
            data = {
                "version": "1.0",
                "max_entries": self.max_entries,
                "entries": [entry.to_dict() for entry in self.entries]
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving color history: {e}")
            return False
    
    def save_async(self, on_complete: callable = None) -> None:
        """
        Save history to JSON file asynchronously (non-blocking).
        
        Uses background thread to prevent UI freeze.
        
        Args:
            on_complete: Optional callback(success: bool, message: str)
        """
        try:
            from utils.async_file_ops import FileWriterThread
            
            data = {
                "version": "1.0",
                "max_entries": self.max_entries,
                "entries": [entry.to_dict() for entry in self.entries]
            }
            
            # Create and start writer thread
            self._save_thread = FileWriterThread(self.history_file, data, 'json')
            
            if on_complete:
                self._save_thread.finished.connect(on_complete)
            else:
                # Default: just log result
                self._save_thread.finished.connect(
                    lambda success, msg: logger.success(msg) if success else logger.error(msg)
                )
            
            self._save_thread.start()
            
        except ImportError:
            # Fallback to sync if async not available
            logger.warning("Async file ops not available, using sync save")
            result = self.save()
            if on_complete:
                on_complete(result, "Saved" if result else "Save failed")
            
    def load(self) -> bool:
        """
        Load history from JSON file.
        
        Returns:
            True if loaded successfully
        """
        try:
            if not os.path.exists(self.history_file):
                return False
                
            with open(self.history_file, 'r') as f:
                data = json.load(f)
            
            # Load max_entries setting
            self.max_entries = data.get("max_entries", 20)
            
            # Load entries
            self.entries = [
                ColorHistoryEntry.from_dict(entry_data) 
                for entry_data in data.get("entries", [])
            ]
            
            logger.success(f"Loaded {len(self.entries)} color history entries")
            return True
            
        except Exception as e:
            logger.error(f"Error loading color history: {e}")
            self.entries = []
            return False
            
    def export_to_file(self, filepath: str) -> bool:
        """
        Export history to a file.
        
        Args:
            filepath: Path to export file
            
        Returns:
            True if exported successfully
        """
        try:
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.json':
                return self._export_json(filepath)
            elif ext in ['.txt', '.log']:
                return self._export_text(filepath)
            elif ext == '.html':
                return self._export_html(filepath)
            else:
                # Default to text
                return self._export_text(filepath)
                
        except Exception as e:
            logger.error(f"Error exporting history: {e}")
            return False
            
    def _export_json(self, filepath: str) -> bool:
        """Export as JSON."""
        try:
            data = {
                "exported": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_colors": len(self.entries),
                "colors": [entry.to_dict() for entry in self.entries]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False
            
    def _export_text(self, filepath: str) -> bool:
        """Export as plain text."""
        try:
            with open(filepath, 'w') as f:
                f.write("Color Mixer - Color History\n")
                f.write("=" * 60 + "\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Colors: {len(self.entries)}\n")
                f.write("\n")
                
                for i, entry in enumerate(self.entries, 1):
                    hex_color = ColorMath.rgb_to_hex(entry.color)
                    f.write(f"{i:3d}. {hex_color}  rgb{entry.color}  -  {entry.timestamp}\n")
            
            return True
        except Exception as e:
            logger.error(f"Error exporting text: {e}")
            return False
            
    def _export_html(self, filepath: str) -> bool:
        """Export as HTML with color swatches."""
        try:
            with open(filepath, 'w') as f:
                f.write("<!DOCTYPE html>\n")
                f.write("<html>\n<head>\n")
                f.write("<title>Color Mixer - Color History</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }\n")
                f.write(".color { display: flex; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }\n")
                f.write(".swatch { width: 60px; height: 40px; border: 2px solid #333; margin-right: 15px; border-radius: 3px; }\n")
                f.write(".info { flex: 1; }\n")
                f.write("h1 { color: #333; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write("<h1>Color Mixer - Color History</h1>\n")
                f.write(f"<p>Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n")
                f.write(f"<p>Total Colors: {len(self.entries)}</p>\n")
                f.write("<hr>\n")
                
                for i, entry in enumerate(self.entries, 1):
                    hex_color = ColorMath.rgb_to_hex(entry.color)
                    f.write('<div class="color">\n')
                    f.write(f'  <div class="swatch" style="background-color: {hex_color};"></div>\n')
                    f.write('  <div class="info">\n')
                    f.write(f'    <strong>Color {i}</strong><br>\n')
                    f.write(f'    {hex_color} &nbsp; rgb{entry.color}<br>\n')
                    f.write(f'    <small>{entry.timestamp}</small>\n')
                    f.write('  </div>\n')
                    f.write('</div>\n')
                
                f.write("</body>\n</html>\n")
            
            return True
        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            return False
            
    def get_statistics(self) -> dict:
        """Get statistics about color history."""
        if not self.entries:
            return {
                "total": 0,
                "oldest": None,
                "newest": None,
                "most_recent_color": None
            }
        
        return {
            "total": len(self.entries),
            "oldest": self.entries[-1].timestamp if self.entries else None,
            "newest": self.entries[0].timestamp if self.entries else None,
            "most_recent_color": self.entries[0].color if self.entries else None
        }
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
        Stops any running threads and clears entries.
        """
        try:
            # Stop any running save thread
            if hasattr(self, '_save_thread') and self._save_thread:
                if self._save_thread.isRunning():
                    self._save_thread.quit()
                    self._save_thread.wait(1000)  # Wait up to 1 second
                self._save_thread = None
            
            # Clear entries to free memory
            self.entries.clear()
            
            if logger:
                logger.debug("ColorHistory cleanup complete")
                
        except Exception as e:
            if logger:
                logger.error(f"Error during ColorHistory cleanup: {e}")
