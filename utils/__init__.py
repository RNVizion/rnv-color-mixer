"""
Shared utilities for the RNV Color Mixer application.

This package provides cross-cutting services used throughout the
application: configuration, logging, error handling, file I/O, clipboard
access, session and settings persistence, signal-connection tracking,
pixmap caching, and themed dialog helpers.

Only lightweight public names are re-exported at the package level. For
heavier components that pull in PyQt6 (session/settings managers, async
file I/O, pixmap cache, dialog helper), import directly from the
submodule — e.g. ``from utils.session_manager import SessionManager``.
"""

# --- Package metadata ------------------------------------------------------
# VERSION is the single source of truth, owned by utils.config.
from utils.config import VERSION as __version__, APP_NAME as __app_name__

__author__ = "RNV Development"

# --- Lightweight public surface -------------------------------------------
# These are small, dependency-free utilities safe to import eagerly.
from utils.config import VERSION, APP_NAME
from utils.logger import Logger, get_logger, header, separator
from utils.error_handler import ErrorHandler

__all__ = [
    # Package metadata
    "__version__",
    "__app_name__",
    "__author__",
    # Lightweight re-exports
    "VERSION",
    "APP_NAME",
    "Logger",
    "get_logger",
    "header",
    "separator",
    "ErrorHandler",
]
