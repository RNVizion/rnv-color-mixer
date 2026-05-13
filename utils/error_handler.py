"""
Centralized error handling utilities for the RNV Color Mixer.

Provides three ways to handle exceptions consistently across the codebase:
a `safe_execute()` helper for direct calls with fallback values, a
`@safe_method` decorator for class methods, and an `ErrorContext` context
manager for arbitrary blocks. All three log errors through the shared
logger and optionally forward status messages to the UI.

Usage Examples:
    # Direct execution with fallback
    result = ErrorHandler.safe_execute(
        lambda: load_file(path),
        "loading file",
        status_callback=self.status_updated.emit,
        fallback_value=None
    )
    
    # Method decorator
    @ErrorHandler.safe_method("adding color slot")
    def add_color_slot(self):
        # ... method code ...
        pass
    
    # Context manager
    with ErrorContext("processing image", self.status_updated.emit):
        process_image()
"""

import traceback
from types import TracebackType
from typing import Callable, Any, TypeVar
from functools import wraps

# Import logger
try:
    from utils.logger import Logger
    _logger = Logger("ErrorHandler")
    _use_logger = True
except ImportError:
    _use_logger = False
    _logger = None

T = TypeVar('T')


def _log_error(context: str, error: Exception, show_traceback: bool = True) -> None:
    """Internal logging helper that uses logger if available."""
    if _use_logger and _logger:
        _logger.error(f"Error in {context}", error=error)
        if show_traceback:
            traceback.print_exc()
    else:
        # Fallback to print when logger not available
        print(f"ERROR: Error in {context}: {error}")
        if show_traceback:
            traceback.print_exc()


def _log_warning(message: str) -> None:
    """Internal warning helper."""
    if _use_logger and _logger:
        _logger.warning(message)
    else:
        # Fallback to print when logger not available
        print(f"WARNING: {message}")


class ErrorHandler:
    """Centralized error handling with consistent logging and user feedback."""
    
    # Global configuration
    SHOW_TRACEBACK = True  # Set to False in production
    LOG_TO_FILE = False  # Enable for debugging
    LOG_FILE_PATH = "color_mixer_errors.log"
    
    @staticmethod
    def handle_exception(
        error: Exception,
        context: str,
        status_callback: Callable[[str], None] | None = None,
        show_traceback: bool = True,
        user_message: str | None = None
    ) -> None:
        """
        Handle exception with consistent logging and user feedback.
        
        Args:
            error: The exception that occurred
            context: Description of what was being done (e.g., "loading image")
            status_callback: Optional callback for status updates (e.g., self.status_updated.emit)
            show_traceback: Whether to print full traceback to console
            user_message: Custom message for user (auto-generated if None)
        """
        # Console logging
        error_msg = f"Error in {context}: {error}"
        _log_error(context, error, show_traceback=False)
        
        if show_traceback and ErrorHandler.SHOW_TRACEBACK:
            traceback.print_exc()
        
        # File logging (optional, for debugging)
        if ErrorHandler.LOG_TO_FILE:
            ErrorHandler._log_to_file(error, context)
        
        # User feedback via status bar
        if status_callback:
            user_msg = user_message or f"{context.capitalize()} failed"
            try:
                status_callback(user_msg)
            except Exception as callback_error:
                # Don't let callback errors crash the app
                _log_warning(f"Status callback failed: {callback_error}")
    
    @staticmethod
    def _log_to_file(error: Exception, context: str) -> None:
        """Log error to file for debugging."""
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            with open(ErrorHandler.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Context: {context}\n")
                f.write(f"Error: {error}\n")
                f.write(f"Traceback:\n")
                traceback.print_exc(file=f)
                f.write(f"{'='*80}\n")
        except Exception as log_error:
            _log_warning(f"Failed to log error to file: {log_error}")
    
    @staticmethod
    def safe_execute(
        func: Callable[[], T],
        context: str,
        status_callback: Callable[[str], None] | None = None,
        fallback_value: T = None,
        reraise: bool = False,
        user_message: str | None = None
    ) -> T:
        """
        Execute function with error handling.
        
        Args:
            func: Function to execute
            context: Description for error messages (e.g., "loading settings")
            status_callback: Optional status update callback
            fallback_value: Value to return if exception occurs
            reraise: Whether to re-raise exception after handling
            user_message: Custom user message
        
        Returns:
            Function result or fallback_value if exception occurs
            
        Example:
            result = ErrorHandler.safe_execute(
                lambda: json.load(f),
                "parsing JSON",
                self.status_updated.emit,
                fallback_value={}
            )
        """
        try:
            return func()
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context, 
                status_callback,
                user_message=user_message
            )
            if reraise:
                raise
            return fallback_value
    
    @staticmethod
    def safe_method(
        context: str,
        fallback_value: Any = None,
        user_message: str | None = None
    ) -> Callable[[Callable], Callable]:
        """
        Decorator for safe method execution.
        
        Args:
            context: Description of what method does (e.g., "adding color slot")
            fallback_value: Value to return if exception occurs
            user_message: Custom user message
        
        Usage:
            @ErrorHandler.safe_method("loading image")
            def load_image(self, path: str):
                # ... method code ...
                # No try/except needed!
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args: Any, **kwargs: Any) -> Any:
                # Try to find status callback
                status_callback = None
                if hasattr(self, 'status_updated'):
                    status_callback = self.status_updated.emit
                elif hasattr(self, 'status_message'):
                    status_callback = self.status_message.emit
                
                return ErrorHandler.safe_execute(
                    lambda: func(self, *args, **kwargs),
                    context,
                    status_callback,
                    fallback_value,
                    user_message=user_message
                )
            return wrapper
        return decorator


class ErrorContext:
    """
    Context manager for error handling.
    
    Usage:
        with ErrorContext("processing image", self.status_updated.emit):
            # ... code that might raise exceptions ...
            process_image()
            apply_filters()
    """
    
    def __init__(
        self,
        context: str,
        status_callback: Callable[[str], None] | None = None,
        reraise: bool = False,
        user_message: str | None = None
    ) -> None:
        self.context = context
        self.status_callback = status_callback
        self.reraise = reraise
        self.user_message = user_message
    
    def __enter__(self) -> "ErrorContext":
        return self
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            ErrorHandler.handle_exception(
                exc_val,
                self.context,
                self.status_callback,
                user_message=self.user_message
            )
            return not self.reraise  # Suppress exception if not reraising
        return True


# Convenience functions for common patterns
def safe_file_operation(func: Callable, filepath: str, operation: str = "file operation") -> Any:
    """
    Safely execute file operations with helpful error messages.
    
    Args:
        func: File operation to execute
        filepath: Path to file
        operation: Description (e.g., "reading", "writing")
    
    Returns:
        Function result or None on error
    """
    import os
    
    try:
        return func()
    except FileNotFoundError:
        _log_warning(f"File not found: {filepath}")
        return None
    except PermissionError:
        _log_warning(f"Permission denied: {filepath}")
        return None
    except Exception as e:
        _log_error(f"{operation} file {filepath}", e)
        traceback.print_exc()
        return None


def safe_widget_operation(widget: Any, operation: Callable, description: str = "widget operation") -> bool:
    """
    Safely execute widget operations (for Qt widgets).
    
    Args:
        widget: Qt widget
        operation: Operation to perform on widget
        description: Description for error messages
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if widget is None:
            _log_warning(f"Cannot perform {description} - widget is None")
            return False
        
        operation()
        return True
        
    except Exception as e:
        _log_error(description, e)
        traceback.print_exc()
        return False


# Example usage patterns (for documentation)
"""
USAGE PATTERNS:

1. SIMPLE FUNCTION WRAPPING:
   result = ErrorHandler.safe_execute(
       lambda: load_image(path),
       "loading image",
       self.status_updated.emit
   )

2. METHOD DECORATOR:
   @ErrorHandler.safe_method("adding color slot")
   def add_color_slot(self):
       slot = ColorSlot()
       self.slots.append(slot)

3. CONTEXT MANAGER:
   with ErrorContext("processing palette", self.status_updated.emit):
       colors = extract_colors(image)
       save_palette(colors)

4. FILE OPERATIONS:
   data = safe_file_operation(
       lambda: json.load(open(path)),
       path,
       "reading JSON"
   )

5. WIDGET OPERATIONS:
   safe_widget_operation(
       self.preview_label,
       lambda: self.preview_label.setText("Updated"),
       "updating preview label"
   )
"""