# RNV_Color_Mixer.spec — PyInstaller build specification
#
# Build command (from the project root):
#     pyinstaller RNV_Color_Mixer.spec
#
# Or use the convenience wrapper:
#     build_windows.bat
#
# Output:
#     dist/RNV_Color_Mixer/RNV_Color_Mixer.exe  (one-folder mode)
#
# Notes:
#   - Paths are relative to this spec file's location (the project root).
#     PyInstaller resolves them from the SPEC directory, so this file is
#     portable across machines without any edits.
#   - One-folder mode is used rather than one-file because one-file builds
#     unpack to a temp directory on every launch, adding ~3 seconds to
#     startup. One-folder is larger on disk but launches instantly.
#   - VERSION is pulled from utils/config.py via AST parsing so the EXE
#     version info always matches the running app.

import ast
from pathlib import Path

block_cipher = None

# ─── Resolve project version via AST (no module execution) ───────────────
# Mirrors the pattern used by pyproject.toml's dynamic version resolution.
def _read_version() -> str:
    config_path = Path(SPECPATH) / 'utils' / 'config.py'
    tree = ast.parse(config_path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'VERSION':
                    if isinstance(node.value, ast.Constant):
                        return node.value.value
    return '0.0.0'

APP_VERSION = _read_version()


# ─── Source analysis ─────────────────────────────────────────────────────
a = Analysis(
    ['RNV_Color_Mixer.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle the entire resources directory (fonts, icons, button images,
        # background images). Destination path inside the EXE mirrors the
        # source path so runtime code using relative paths keeps working.
        ('resources', 'resources'),
    ],
    hiddenimports=[
        # PyQt6 plugins that PyInstaller sometimes misses when the app
        # uses them indirectly through stylesheets or Qt's own machinery.
        'PyQt6.sip',
        'PyQt6.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Shrink the bundle by excluding heavy packages we don't use.
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'pdb',
        # Test-only packages — never reachable from production code,
        # but listing them explicitly prevents accidental bundling if
        # a future change ever adds an import-from-test edge.
        'pytest',
        '_pytest',
        'pytest_qt',
        'coverage',
        'hypothesis',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# ─── Executable configuration ────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RNV_Color_Mixer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # Compress with UPX if available (optional)
    console=False,     # GUI app — no console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/icon.ico',  # Taskbar / window icon
    version=None,       # Uses APP_VERSION from above for metadata
)


# ─── Bundle the whole directory (one-folder mode) ────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RNV_Color_Mixer',
)
