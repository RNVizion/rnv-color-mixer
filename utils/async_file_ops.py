"""
Non-blocking file I/O for the RNV Color Mixer.

Runs read and write operations on a background QThread so the UI stays
responsive during large palette imports, session saves, and image
processing. Completion is reported via callback so callers can update
status text or trigger follow-up actions on the main thread.

Usage Examples:
    # Write file asynchronously
    manager = AsyncFileManager(self.status_updated.emit)
    manager.write_file_async(
        'palette.json',
        data,
        on_complete=self._on_save_complete
    )
    
    # Read file asynchronously
    manager.read_file_async(
        'palette.json',
        on_complete=self._on_load_complete
    )
"""

from PyQt6.QtCore import QThread, pyqtSignal
import json
from typing import Any, Callable

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("AsyncFileOps")
except ImportError:
    logger = None

# Import VERSION from config
from utils.config import VERSION

# Import ErrorHandler for consistent error handling
try:
    from utils.error_handler import ErrorHandler
    _error_handler_available = True
except ImportError:
    _error_handler_available = False



class FileWriterThread(QThread):
    """Background thread for writing files without blocking UI."""
    
    finished = pyqtSignal(bool, str)  # (success, message)
    progress = pyqtSignal(int)  # percentage (0-100)
    
    def __init__(self, filepath: str, data: Any, format: str = 'json'):
        """
        Initialize file writer thread.
        
        Args:
            filepath: Path to file
            data: Data to write
            format: File format ('json', 'text', 'binary')
        """
        super().__init__()
        self.filepath = filepath
        self.data = data
        self.format = format
    
    def run(self) -> None:
        """Execute file write in background."""
        try:
            self.progress.emit(10)
            
            if self.format == 'json':
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    self.progress.emit(30)
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                    self.progress.emit(90)
            
            elif self.format == 'text':
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    self.progress.emit(30)
                    f.write(str(self.data))
                    self.progress.emit(90)
            
            elif self.format == 'binary':
                with open(self.filepath, 'wb') as f:
                    self.progress.emit(30)
                    f.write(self.data)
                    self.progress.emit(90)
            
            else:
                raise ValueError(f"Unsupported format: {self.format}")
            
            self.progress.emit(100)
            self.finished.emit(True, f"✔ Saved to {self.filepath}")
            
        except Exception as e:
            self.finished.emit(False, f"Save failed: {e}")


class FileReaderThread(QThread):
    """Background thread for reading files without blocking UI."""
    
    finished = pyqtSignal(bool, object, str)  # (success, data, message)
    progress = pyqtSignal(int)  # percentage (0-100)
    
    def __init__(self, filepath: str, format: str = 'json'):
        """
        Initialize file reader thread.
        
        Args:
            filepath: Path to file
            format: File format ('json', 'text', 'binary')
        """
        super().__init__()
        self.filepath = filepath
        self.format = format
    
    def run(self) -> None:
        """Execute file read in background."""
        try:
            self.progress.emit(10)
            
            if self.format == 'json':
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.progress.emit(30)
                    data = json.load(f)
                    self.progress.emit(90)
            
            elif self.format == 'text':
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.progress.emit(30)
                    data = f.read()
                    self.progress.emit(90)
            
            elif self.format == 'binary':
                with open(self.filepath, 'rb') as f:
                    self.progress.emit(30)
                    data = f.read()
                    self.progress.emit(90)
            
            else:
                raise ValueError(f"Unsupported format: {self.format}")
            
            self.progress.emit(100)
            self.finished.emit(True, data, f"✔ Loaded from {self.filepath}")
            
        except Exception as e:
            self.finished.emit(False, None, f"Load failed: {e}")


class AsyncFileManager:
    """
    Manager for asynchronous file operations.
    
    Handles:
    - Non-blocking file I/O
    - Progress reporting
    - Thread lifecycle management
    - Error handling
    """
    
    def __init__(
        self, 
        status_callback: Callable[[str], None] | None = None,
        progress_callback: Callable[[int], None] | None = None
    ):
        """
        Initialize async file manager.
        
        Args:
            status_callback: Callback for status messages
            progress_callback: Callback for progress updates (0-100)
        """
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self._active_threads = []
    
    def write_file_async(
        self,
        filepath: str,
        data: Any,
        on_complete: Callable[[bool, str], None] | None = None,
        format: str = 'json'
    ) -> None:
        """
        Write file asynchronously without blocking UI.
        
        Args:
            filepath: Path to file
            data: Data to write
            on_complete: Callback(success, message) when done
            format: File format ('json', 'text', 'binary')
        
        Example:
            manager.write_file_async(
                'palette.json',
                {'colors': [(255, 0, 0), (0, 255, 0)]},
                on_complete=lambda success, msg: print(msg)
            )
        """
        thread = FileWriterThread(filepath, data, format)
        
        # Connect signals
        thread.finished.connect(
            lambda success, msg: self._on_write_complete(success, msg, on_complete)
        )
        
        if self.progress_callback:
            thread.progress.connect(self.progress_callback)
        
        if self.status_callback:
            self.status_callback("Writing file...")
        
        # Track thread to prevent garbage collection
        self._active_threads.append(thread)
        
        # Start background operation
        thread.start()
    
    def read_file_async(
        self,
        filepath: str,
        on_complete: Callable[[bool, Any, str], None] | None = None,
        format: str = 'json'
    ) -> None:
        """
        Read file asynchronously without blocking UI.
        
        Args:
            filepath: Path to file
            on_complete: Callback(success, data, message) when done
            format: File format ('json', 'text', 'binary')
        
        Example:
            manager.read_file_async(
                'palette.json',
                on_complete=lambda ok, data, msg: self.load_palette(data) if ok else None
            )
        """
        thread = FileReaderThread(filepath, format)
        
        # Connect signals
        thread.finished.connect(
            lambda success, data, msg: self._on_read_complete(success, data, msg, on_complete)
        )
        
        if self.progress_callback:
            thread.progress.connect(self.progress_callback)
        
        if self.status_callback:
            self.status_callback("Reading file...")
        
        # Track thread
        self._active_threads.append(thread)
        
        # Start background operation
        thread.start()
    
    def _on_write_complete(
        self, 
        success: bool, 
        message: str, 
        callback: Callable | None
    ) -> None:
        """Handle write completion."""
        if self.status_callback:
            self.status_callback(message)
        
        if callback:
            try:
                callback(success, message)
            except Exception as e:
                logger.error(f"Error in write completion callback: {e}")
        
        # Cleanup finished threads
        self._cleanup_threads()
    
    def _on_read_complete(
        self, 
        success: bool, 
        data: Any, 
        message: str, 
        callback: Callable | None
    ) -> None:
        """Handle read completion."""
        if self.status_callback:
            self.status_callback(message)
        
        if callback:
            try:
                callback(success, data, message)
            except Exception as e:
                logger.error(f"Error in read completion callback: {e}")
        
        # Cleanup finished threads
        self._cleanup_threads()
    
    def _cleanup_threads(self) -> None:
        """Remove finished threads from tracking list with proper Qt cleanup."""
        # Identify finished threads
        finished_threads = [t for t in self._active_threads if not t.isRunning()]
        
        # Schedule Qt cleanup for finished threads
        for thread in finished_threads:
            try:
                thread.deleteLater()  # Ensure proper Qt object cleanup
            except Exception:
                pass  # Ignore cleanup errors
        
        # Keep only running threads
        self._active_threads = [t for t in self._active_threads if t.isRunning()]
    
    def wait_all(self, timeout: int = 5000) -> bool:
        """
        Wait for all active operations to complete.
        
        Args:
            timeout: Maximum time to wait in milliseconds
        
        Returns:
            True if all operations completed, False if timeout
        """
        for thread in self._active_threads:
            if not thread.wait(timeout):
                return False
        return True
    
    def cancel_all(self) -> None:
        """Cancel all active file operations."""
        for thread in self._active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        self._active_threads.clear()
        
        if self.status_callback:
            self.status_callback("File operations cancelled")
    
    def get_active_count(self) -> int:
        """Get number of currently active file operations."""
        return sum(1 for t in self._active_threads if t.isRunning())


# Convenience functions
def async_save_json(
    filepath: str,
    data: dict,
    on_complete: Callable[[bool, str], None] | None = None,
    status_callback: Callable[[str], None] | None = None
) -> AsyncFileManager:
    """
    Quick function to save JSON asynchronously.
    
    Returns:
        AsyncFileManager instance for advanced control
    """
    manager = AsyncFileManager(status_callback)
    manager.write_file_async(filepath, data, on_complete, 'json')
    return manager


def async_load_json(
    filepath: str,
    on_complete: Callable[[bool, dict, str], None] | None = None,
    status_callback: Callable[[str], None] | None = None
) -> AsyncFileManager:
    """
    Quick function to load JSON asynchronously.
    
    Returns:
        AsyncFileManager instance for advanced control
    """
    manager = AsyncFileManager(status_callback)
    manager.read_file_async(filepath, on_complete, 'json')
    return manager


# Example integration patterns
"""
INTEGRATION EXAMPLES:

1. IN __init__:
   self.file_manager = AsyncFileManager(
       status_callback=self.status_updated.emit,
       progress_callback=self._on_file_progress
   )

2. EXPORT PALETTE:
   def export_palette(self, filepath: str, colors: list):
       data = {'colors': colors, 'version': VERSION}
       self.file_manager.write_file_async(
           filepath,
           data,
           on_complete=self._on_export_complete
       )
   
   def _on_export_complete(self, success: bool, message: str):
       if success:
           logger.success(f"Export successful: {message}")
       else:
           logger.error(f"Export failed: {message}")

3. IMPORT PALETTE:
   def import_palette(self, filepath: str):
       self.file_manager.read_file_async(
           filepath,
           on_complete=self._on_import_complete
       )
   
   def _on_import_complete(self, success: bool, data: dict, message: str):
       if success and data:
           self.load_colors(data.get('colors', []))
       else:
           logger.error(f"Import failed: {message}")

4. WITH PROGRESS BAR:
   def _on_file_progress(self, percentage: int):
       self.status_updated.emit(f"Progress: {percentage}%")
       # Or update a QProgressBar:
       # self.progress_bar.setValue(percentage)
"""