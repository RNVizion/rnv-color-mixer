#!/usr/bin/env bash
#
# Python cache cleaner for the RNV Color Mixer (macOS / Linux).
# Removes all __pycache__ directories and .pyc bytecode files from the
# project tree. Windows users should run clean_python_cache.bat instead.
#
# Usage:
#   chmod +x clean_python_cache.sh   # first time only
#   ./clean_python_cache.sh

set -euo pipefail

# Move to the directory containing this script so relative paths work
# regardless of where the user invoked it from.
cd "$(dirname "$0")"

echo "================================================================"
echo "Python Cache Cleaner for RNV Color Mixer"
echo "================================================================"
echo
echo "This will delete all Python cache files (.pyc and __pycache__)"
echo "in the current directory and all subdirectories."
echo
echo "Current directory: $(pwd)"
echo

# Confirmation prompt (matches the .bat's pause behavior)
read -rp "Press Enter to continue, or Ctrl+C to cancel..."
echo

# --- Delete __pycache__ directories ---
echo "Deleting __pycache__ directories..."
pycache_count=0
while IFS= read -r -d '' dir; do
    echo "  Deleting: $dir"
    rm -rf "$dir"
    pycache_count=$((pycache_count + 1))
done < <(find . -type d -name "__pycache__" -print0)

# --- Delete .pyc files (catches any orphaned ones outside __pycache__) ---
echo
echo "Deleting .pyc files..."
pyc_count=0
while IFS= read -r -d '' file; do
    echo "  Deleting: $file"
    rm -f "$file"
    pyc_count=$((pyc_count + 1))
done < <(find . -type f -name "*.pyc" -print0)

echo
echo "================================================================"
echo "DONE! Removed $pycache_count __pycache__ directories and $pyc_count .pyc files."
echo "================================================================"
echo
echo "You can now run your app with fresh files:"
echo "  python RNV_Color_Mixer.py"
echo
