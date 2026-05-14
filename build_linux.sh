#!/usr/bin/env bash
# ============================================================
# build_linux.sh — Build RNV Color Mixer for Linux
# ============================================================
#
# Usage:
#   chmod +x build_linux.sh   # first time only
#   ./build_linux.sh
#
# Output:
#   dist/RNV_Color_Mixer/RNV_Color_Mixer
#
# Requirements:
#   pip install pyinstaller
#
# Notes:
#   - Produces a one-folder bundle (matches the Windows build).
#   - Linux binaries are tied to the glibc version of the build host.
#     Build on the oldest distro you want to support for max
#     compatibility (e.g. Ubuntu 22.04 LTS).
#   - PyInstaller will emit a warning that the .ico icon in the .spec
#     is not a supported Linux icon format. This is harmless — the
#     binary still builds. Desktop integration (taskbar icon, .desktop
#     file) is a separate concern not covered by this script.
#
# ============================================================

set -euo pipefail

# Move to the directory containing this script so relative paths work
# regardless of where the user invoked it from.
cd "$(dirname "$0")"

echo "================================================================"
echo "RNV Color Mixer - Linux Build"
echo "================================================================"
echo

# --- Confirm PyInstaller is installed ---
if ! python3 -m PyInstaller --version >/dev/null 2>&1; then
    echo "ERROR: PyInstaller not found."
    echo "Install it with:"
    echo "  pip install pyinstaller"
    echo
    exit 1
fi

# --- Clean previous build artifacts ---
echo "Cleaning previous build artifacts..."
rm -rf build dist
echo

# --- Run PyInstaller ---
echo "Building RNV Color Mixer..."
echo
if ! python3 -m PyInstaller RNV_Color_Mixer.spec --clean --noconfirm; then
    echo
    echo "================================================================"
    echo "BUILD FAILED - check output above for details"
    echo "================================================================"
    exit 1
fi

echo
echo "================================================================"
echo "BUILD SUCCESSFUL"
echo "================================================================"
echo
echo "Executable: dist/RNV_Color_Mixer/RNV_Color_Mixer"
echo
echo "To run:"
echo "  ./dist/RNV_Color_Mixer/RNV_Color_Mixer"
echo
echo "To distribute, tar the entire 'dist/RNV_Color_Mixer' folder:"
echo "  tar -czf RNV_Color_Mixer-linux.tar.gz -C dist RNV_Color_Mixer"
echo
