@echo off
REM ============================================================
REM build_windows.bat — Build RNV Color Mixer for Windows
REM ============================================================
REM
REM Usage:
REM   build_windows.bat
REM
REM Output:
REM   dist\RNV_Color_Mixer\RNV_Color_Mixer.exe
REM
REM Requirements:
REM   pip install pyinstaller
REM
REM ============================================================

echo ================================================================
echo RNV Color Mixer - Windows Build
echo ================================================================
echo.

REM --- Change to the directory containing this script ---
cd /d "%~dp0"

REM --- Confirm PyInstaller is installed ---
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found.
    echo Install it with:
    echo   pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM --- Clean previous build artifacts ---
echo Cleaning previous build artifacts...
if exist "build"       rmdir /s /q build
if exist "dist"        rmdir /s /q dist
echo.

REM --- Run PyInstaller ---
echo Building RNV Color Mixer...
echo.
python -m PyInstaller RNV_Color_Mixer.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ================================================================
    echo BUILD FAILED - check output above for details
    echo ================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================
echo BUILD SUCCESSFUL
echo ================================================================
echo.
echo Executable: dist\RNV_Color_Mixer\RNV_Color_Mixer.exe
echo.
echo To distribute, zip the entire 'dist\RNV_Color_Mixer' folder.
echo.
pause
