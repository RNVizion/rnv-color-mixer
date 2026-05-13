"""
Session Manager
Handles saving and loading Color Mixer workspace sessions.
Includes auto-save, recent sessions, and state management.
"""

import json
import traceback
import os
from datetime import datetime
from typing import Any, Callable
from pathlib import Path

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("SessionManager")
except ImportError:
    logger = None

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False
    def _log(msg: str) -> None: print(msg)


class SessionManager:
    """Manages Color Mixer sessions (save/load workspace state)."""
    
    SESSION_VERSION = "1.0"
    SESSION_EXTENSION = ".session"
    MAX_RECENT_SESSIONS = 10
    MAX_AUTOSAVES = 6  # Keep last 6 auto-saves (separate from manual saves)
    AUTOSAVE_PREFIX = ".autosave_"  # Prefix for auto-save files
    
    def __init__(self, sessions_dir: str | None = None):
        """
        Initialize Session Manager.
        
        Args:
            sessions_dir: Directory to store session files. 
                         If None, uses default location.
        """
        if sessions_dir:
            self.sessions_dir = Path(sessions_dir)
        else:
            # Default: sessions folder in user's home directory
            home = Path.home()
            self.sessions_dir = home / ".color_mixer" / "sessions"
        
        # Create sessions directory if it doesn't exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Recent sessions cache file
        self.recent_file = self.sessions_dir / ".recent_sessions.json"
        
        # === AUTO-SAVE SETUP ===
        from PyQt6.QtCore import QTimer
        
        self.autosave_enabled = True
        self.autosave_interval = 60  # seconds
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave)
        self.main_app = None  # Set by main app via start_autosave()
        # Auto-saves use timestamped filenames: .autosave_YYYYMMDD_HHMMSS.session
        # Each app session gets ONE auto-save file that gets overwritten during the session
        # New auto-save file is only created on new app startup
        self.current_autosave_path = None  # Set on first autosave of this session
        # === END AUTO-SAVE SETUP ===
        
        logger.success(f"Session Manager initialized: {self.sessions_dir}") if logger else print(f"Session Manager initialized: {self.sessions_dir}")
    
    def cleanup(self) -> None:
        """
        Clean up resources before deletion.
        
Stops the autosave timer and disconnects signals.
        """
        try:
            if hasattr(self, 'autosave_timer') and self.autosave_timer:
                self.autosave_timer.stop()
                try:
                    self.autosave_timer.timeout.disconnect()
                except Exception:
                    pass  # May not be connected
                logger.debug("Session Manager autosave timer stopped") if logger else None
        except Exception as e:
            logger.error(f"Error during session manager cleanup: {e}") if logger else None
    
    def save_session(self, 
                    filepath: str,
                    slots_data: list[dict[str, Any]],
                    mixed_color: tuple[int, int, int] | None = None,
                    settings: dict[str, Any] | None = None,
                    name: str | None = None,
                    description: str | None = None) -> bool:
        """
        Save a session to a file.
        
        Args:
            filepath: Path to save session file
            slots_data: List of slot data dictionaries
            mixed_color: Current mixed color (r, g, b)
            settings: Additional settings to save
            name: Session name
            description: Session description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure proper extension
            if not filepath.endswith(self.SESSION_EXTENSION):
                filepath += self.SESSION_EXTENSION
            
            # Get session name from filename if not provided
            if not name:
                name = Path(filepath).stem
            
            # Build session data
            session_data = {
                "version": self.SESSION_VERSION,
                "name": name,
                "description": description or "",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                
                "slots": slots_data,
                "mixed_color": list(mixed_color) if mixed_color else None,
                
                "settings": settings or {},
                
                "metadata": {
                    "color_count": sum(1 for s in slots_data if s.get('weight', 0) > 0),
                    "total_slots": len(slots_data)
                }
            }
            
            # Write to file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Add to recent sessions
            self._add_to_recent(filepath)
            
            logger.success(f"Session saved: {filepath}") if logger else print(f"Session saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error("Error saving session", error=e) if logger else print(f"Error saving session: {e}")
            traceback.print_exc()
            return False
    
    def load_session(self, filepath: str) -> dict[str, Any] | None:
        """
        Load a session from a file.
        
        Args:
            filepath: Path to session file
            
        Returns:
            Session data dictionary or None if failed
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Session file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Validate version
            if session_data.get('version') != self.SESSION_VERSION:
                logger.warning(f"Warning: Session version mismatch. Expected {self.SESSION_VERSION}, got {session_data.get('version')}")
            
            # Update modified time
            session_data['modified'] = datetime.now().isoformat()
            
            # Add to recent sessions
            self._add_to_recent(filepath)
            
            logger.success(f"Session loaded: {filepath}") if logger else print(f"Session loaded: {filepath}")
            return session_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error: Invalid session file format: {e}")
            return None
        except Exception as e:
            logger.error("Error loading session", error=e) if logger else print(f"Error loading session: {e}")
            traceback.print_exc()
            return None
    
    def get_recent_sessions(self) -> list[dict[str, str]]:
        """
        Get list of recent sessions with metadata.
        
        Returns:
            List of session info dictionaries with keys:
            - filepath: Full path to session
            - name: Session name
            - modified: Last modified timestamp
            - color_count: Number of colors
        """
        try:
            if not self.recent_file.exists():
                return []
            
            with open(self.recent_file, 'r', encoding='utf-8') as f:
                recent_paths = json.load(f)
            
            # Build session info list
            sessions = []
            for filepath in recent_paths:
                if not os.path.exists(filepath):
                    continue  # Skip deleted files
                
                try:
                    # Quick read just for metadata
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        'filepath': filepath,
                        'name': data.get('name', Path(filepath).stem),
                        'modified': data.get('modified', data.get('created', 'Unknown')),
                        'color_count': data.get('metadata', {}).get('color_count', 0),
                        'description': data.get('description', '')
                    })
                except Exception:
                    continue  # Skip corrupted files
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return []
    
    def _add_to_recent(self, filepath: str) -> None:
        """
        Add a session to the recent sessions list.
        Skips auto-save files (they are tracked separately).
        
        Args:
            filepath: Path to session file
        """
        try:
            # Skip autosave files - they are managed separately
            if self.AUTOSAVE_PREFIX in Path(filepath).name:
                return
            
            # Load existing recent list
            if self.recent_file.exists():
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    recent = json.load(f)
            else:
                recent = []
            
            # Remove if already in list (will re-add at front)
            if filepath in recent:
                recent.remove(filepath)
            
            # Add to front
            recent.insert(0, filepath)
            
            # Limit to MAX_RECENT_SESSIONS
            recent = recent[:self.MAX_RECENT_SESSIONS]
            
            # Save updated list
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(recent, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating recent sessions: {e}")
    
    def delete_session(self, filepath: str) -> bool:
        """
        Delete a session file.
        
        Args:
            filepath: Path to session file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                
                # Remove from recent list
                self._remove_from_recent(filepath)
                
                logger.success(f"Session deleted: {filepath}")
                return True
            else:
                logger.warning(f"Session file not found: {filepath}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def _remove_from_recent(self, filepath: str) -> None:
        """
        Remove a session from the recent sessions list.
        
        Args:
            filepath: Path to session file
        """
        try:
            if not self.recent_file.exists():
                return
            
            with open(self.recent_file, 'r', encoding='utf-8') as f:
                recent = json.load(f)
            
            if filepath in recent:
                recent.remove(filepath)
            
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(recent, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error removing from recent sessions: {e}")
    
    def rename_session(self, old_path: str, new_path: str) -> bool:
        """
        Rename a session file.
        
        Args:
            old_path: Current file path
            new_path: New file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(old_path):
                logger.warning(f"Session file not found: {old_path}")
                return False
            
            # Ensure proper extension
            if not new_path.endswith(self.SESSION_EXTENSION):
                new_path += self.SESSION_EXTENSION
            
            # Load, update name, and save to new path
            session_data = self.load_session(old_path)
            if not session_data:
                return False
            
            session_data['name'] = Path(new_path).stem
            session_data['modified'] = datetime.now().isoformat()
            
            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Delete old file
            os.remove(old_path)
            
            # Update recent list
            self._remove_from_recent(old_path)
            self._add_to_recent(new_path)
            
            logger.success(f"Session renamed: {old_path} → {new_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error renaming session: {e}")
            return False
    
    def generate_session_filename(self, base_name: str | None = None) -> str:
        """
        Generate a unique session filename.
        
        Args:
            base_name: Base name for the session. If None, uses timestamp.
            
        Returns:
            Full path to session file
        """
        if not base_name:
            # Use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"session_{timestamp}"
        
        # Make filename safe
        base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_'))
        base_name = base_name.strip().replace(' ', '_')
        
        # Generate unique filename
        filepath = self.sessions_dir / f"{base_name}{self.SESSION_EXTENSION}"
        
        # If exists, add number suffix
        counter = 1
        while filepath.exists():
            filepath = self.sessions_dir / f"{base_name}_{counter}{self.SESSION_EXTENSION}"
            counter += 1
        
        return str(filepath)
    
    def get_session_info(self, filepath: str) -> dict[str, Any] | None:
        """
        Get session metadata without loading full session.
        
        Args:
            filepath: Path to session file
            
        Returns:
            Session info dictionary or None if failed
        """
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'name': data.get('name', Path(filepath).stem),
                'description': data.get('description', ''),
                'created': data.get('created', 'Unknown'),
                'modified': data.get('modified', data.get('created', 'Unknown')),
                'color_count': data.get('metadata', {}).get('color_count', 0),
                'total_slots': data.get('metadata', {}).get('total_slots', 0),
                'filepath': filepath
            }
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of sessions deleted
        """
        try:
            from datetime import timedelta
            
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get all session files
            for filepath in self.sessions_dir.glob(f"*{self.SESSION_EXTENSION}"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modified = datetime.fromisoformat(data.get('modified', data.get('created', '')))
                    
                    if modified < cutoff_date:
                        self.delete_session(str(filepath))
                        deleted_count += 1
                except Exception:
                    continue
            
            if deleted_count > 0:
                logger.success(f"Cleaned up {deleted_count} old sessions")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0

    # ===== AUTO-SAVE METHODS =====
    
    def start_autosave(self, main_app: Any) -> None:
        """
        Start auto-save timer (called by main app on startup).
        Creates a new auto-save file for this session and cleans up old ones.
        
        Args:
            main_app: Reference to main application for getting state
        """
        self.main_app = main_app
        
        # Generate a new autosave filename for THIS session
        # This file will be overwritten during the session, not create new files
        self.current_autosave_path = self._generate_autosave_filename()
        
        # Clean up old auto-saves on startup (keep last MAX_AUTOSAVES - 1 to make room for new one)
        self._cleanup_old_autosaves()
        
        if self.autosave_enabled:
            self.autosave_timer.start(self.autosave_interval * 1000)
            logger.success(f"Auto-save enabled (every {self.autosave_interval}s)") if logger else print(f"Auto-save enabled")
    
    def stop_autosave(self) -> None:
        """Stop auto-save timer (call on clean exit)."""
        if self.autosave_timer.isActive():
            self.autosave_timer.stop()
            logger.success("Auto-save stopped")
    
    def _generate_autosave_filename(self) -> Path:
        """Generate a timestamped auto-save filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.sessions_dir / f"{self.AUTOSAVE_PREFIX}{timestamp}{self.SESSION_EXTENSION}"
    
    def _get_autosave_files(self) -> list[Path]:
        """
        Get all auto-save files sorted by modification time (newest first).
        
        Returns:
            List of auto-save file paths, newest first
        """
        autosaves = list(self.sessions_dir.glob(f"{self.AUTOSAVE_PREFIX}*{self.SESSION_EXTENSION}"))
        # Sort by modification time, newest first
        autosaves.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return autosaves
    
    def _cleanup_old_autosaves(self) -> int:
        """
        Remove old auto-saves, keeping only the most recent MAX_AUTOSAVES.
        
        Returns:
            Number of auto-saves deleted
        """
        try:
            autosaves = self._get_autosave_files()
            deleted = 0
            
            # Delete all but the newest MAX_AUTOSAVES
            for old_autosave in autosaves[self.MAX_AUTOSAVES:]:
                try:
                    old_autosave.unlink()
                    deleted += 1
                    logger.debug(f"Deleted old auto-save: {old_autosave.name}") if logger else None
                except Exception as e:
                    logger.error(f"Failed to delete old auto-save {old_autosave}: {e}") if logger else None
            
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old auto-saves: {e}") if logger else None
            return 0
    
    def _autosave(self) -> None:
        """
        Auto-save current session (called by timer).
        Overwrites the same file for the entire session - doesn't create new files.
        """
        try:
            if not self.main_app:
                return
            
            if not self.current_autosave_path:
                # Should have been set in start_autosave, but create if missing
                self.current_autosave_path = self._generate_autosave_filename()
            
            # Get current state from main app
            if hasattr(self.main_app, 'get_current_state'):
                state = self.main_app.get_current_state()
                
                if state and state.get('slots'):
                    self.save_session(
                        str(self.current_autosave_path),
                        slots_data=state.get('slots', []),
                        mixed_color=state.get('mixed_color'),
                        settings=state.get('settings'),
                        name="Auto-save",
                        description="Automatic backup - recoverable on next startup"
                    )
                    logger.success("Auto-saved session")
                    
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
    
    def save_exit_autosave(self) -> bool:
        """
        Save a final auto-save when the program exits cleanly.
        Call this in closeEvent before cleanup.
        Overwrites this session's auto-save file (same as periodic auto-saves).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.main_app:
                return False
            
            if not self.current_autosave_path:
                # Should have been set in start_autosave, but create if missing
                self.current_autosave_path = self._generate_autosave_filename()
            
            if hasattr(self.main_app, 'get_current_state'):
                state = self.main_app.get_current_state()
                
                if state and state.get('slots'):
                    result = self.save_session(
                        str(self.current_autosave_path),
                        slots_data=state.get('slots', []),
                        mixed_color=state.get('mixed_color'),
                        settings=state.get('settings'),
                        name="Auto-save",
                        description="Session saved on exit"
                    )
                    
                    if result:
                        logger.success("Exit auto-save created")
                    
                    return result
            
            return False
        except Exception as e:
            logger.error(f"Exit auto-save failed: {e}")
            return False
    
    def check_for_autosave(self) -> str | None:
        """
        Check if any autosave exists (call on startup for crash recovery).
        Returns the most recent auto-save if any exist.
        
        Returns:
            Path to most recent autosave file if exists, None otherwise
        """
        autosaves = self._get_autosave_files()
        if autosaves:
            return str(autosaves[0])  # Return newest
        return None
    
    def get_autosave_count(self) -> int:
        """Get the number of auto-save files."""
        return len(self._get_autosave_files())
    
    def get_autosave_sessions(self) -> list[dict[str, str]]:
        """
        Get list of auto-save sessions with metadata.
        
        Returns:
            List of session info dictionaries with keys:
            - filepath: Full path to session
            - name: Session name (Auto-save)
            - modified: Last modified timestamp
            - color_count: Number of colors
        """
        try:
            autosaves = self._get_autosave_files()
            sessions = []
            
            for filepath in autosaves:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        'filepath': str(filepath),
                        'name': f"Auto-save",
                        'modified': data.get('modified', data.get('created', 'Unknown')),
                        'color_count': data.get('metadata', {}).get('color_count', 0),
                        'description': data.get('description', ''),
                        'is_autosave': True
                    })
                except Exception:
                    continue  # Skip corrupted files
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting auto-save sessions: {e}")
            return []
    
    def delete_autosave(self, filepath: str | None = None) -> None:
        """
        Delete a specific autosave file or the oldest one.
        
        Args:
            filepath: Specific autosave to delete, or None to delete oldest
        """
        try:
            if filepath and os.path.exists(filepath):
                os.unlink(filepath)
                logger.success("Auto-save file deleted")
            else:
                # Delete oldest autosave if we have more than MAX
                autosaves = self._get_autosave_files()
                if len(autosaves) > self.MAX_AUTOSAVES:
                    oldest = autosaves[-1]
                    oldest.unlink()
                    logger.debug(f"Deleted oldest auto-save: {oldest.name}")
        except Exception as e:
            logger.error(f"Error deleting autosave: {e}")
    
    def clear_all_autosaves(self) -> int:
        """
        Delete all auto-save files.
        
        Returns:
            Number of files deleted
        """
        try:
            autosaves = self._get_autosave_files()
            deleted = 0
            for autosave in autosaves:
                try:
                    autosave.unlink()
                    deleted += 1
                except Exception:
                    pass
            
            if deleted > 0:
                logger.success(f"Cleared {deleted} auto-save files")
            
            return deleted
        except Exception as e:
            logger.error(f"Error clearing auto-saves: {e}")
            return 0
    
    def set_autosave_interval(self, seconds: int) -> None:
        """
        Change auto-save interval.
        
        Args:
            seconds: New interval in seconds (minimum 30)
        """
        if seconds < 30:
            seconds = 30
        self.autosave_interval = seconds
        
        # Restart timer if active
        if self.autosave_timer.isActive():
            self.autosave_timer.stop()
            self.autosave_timer.start(self.autosave_interval * 1000)
            logger.success(f"Auto-save interval changed to {seconds}s")



# Convenience functions
def save_session(filepath: str, slots_data: list[dict], **kwargs) -> bool:
    """Quick save session."""
    manager = SessionManager()
    return manager.save_session(filepath, slots_data, **kwargs)


def load_session(filepath: str) -> dict | None:
    """Quick load session."""
    manager = SessionManager()
    return manager.load_session(filepath)

# ErrorHandler utility for safe file operations
def safe_file_operation(operation: Callable[[], Any], context: str, fallback: Any = None) -> Any:
    """
    Execute a file operation safely with ErrorHandler if available.
    
    Args:
        operation: Callable to execute
        context: Description for error messages
        fallback: Value to return if operation fails
        
    Returns:
        Operation result or fallback value
    """
    if _error_handler_available:
        return ErrorHandler.safe_execute(operation, context, fallback_value=fallback)
    else:
        try:
            return operation()
        except Exception as e:
            if logger:
                logger.error(f"Error in {context}: {e}")
            return fallback