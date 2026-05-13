@echo off
echo ================================================================
echo Python Cache Cleaner for Color Mixer
echo ================================================================
echo.
echo This will delete all Python cache files (.pyc and __pycache__)
echo in the current directory and all subdirectories.
echo.
echo Current directory: %CD%
echo.
pause

echo.
echo Deleting .pyc files...
del /s /q *.pyc 2>nul
echo.

echo Deleting __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo Deleting: %%d
    rd /s /q "%%d"
)

echo.
echo ================================================================
echo DONE! All Python cache files deleted.
echo ================================================================
echo.
echo You can now run your app with fresh files.
echo.
pause
