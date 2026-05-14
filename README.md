# RNV Color Mixer

[![Tests (Linux)](https://github.com/RNVizion/rnv-color-mixer/actions/workflows/tests-linux.yml/badge.svg)](https://github.com/RNVizion/rnv-color-mixer/actions/workflows/tests-linux.yml)
[![Tests (Windows)](https://github.com/RNVizion/rnv-color-mixer/actions/workflows/tests-windows.yml/badge.svg)](https://github.com/RNVizion/rnv-color-mixer/actions/workflows/tests-windows.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-41CD52.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*Bringing real-world paint mixing to the digital palette.*

A professional desktop color-mixing application for artists, designers, and
color enthusiasts. Simulates real-world paint mixing behavior using color
science (including Kubelka-Munk theory), and offers a full suite of tools
for sampling, harmonizing, and exporting colors.

Built with Python 3.10+ and PyQt6.

---

## Screenshots

<table>
  <tr>
    <td width="50%" align="center">
      <img src="resources/screenshots/01_main_window.png" alt="Main application window" />
      <br/><sub><b>Main window</b> — multi-slot color mixing with real-time preview</sub>
    </td>
    <td width="50%" align="center">
      <img src="resources/screenshots/02_image_sampling.png" alt="Image color sampling" />
      <br/><sub><b>Image sampling</b> — click or drag to sample colors from any loaded image</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="resources/screenshots/03_screen_picker.png" alt="Screen color picker" />
      <br/><sub><b>Screen picker</b> — magnified crosshair sampling across all monitors</sub>
    </td>
    <td width="50%" align="center">
      <img src="resources/screenshots/04_color_harmonies.png" alt="Color harmony generator" />
      <br/><sub><b>Color harmonies</b> — complementary, triadic, tetradic, and more</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="resources/screenshots/05_palette_export.png" alt="Palette export formats" />
      <br/><sub><b>Palette export</b> — 16+ formats including ASE, ACO, GPL, CSS, SCSS</sub>
    </td>
    <td width="50%" align="center">
      <img src="resources/screenshots/06_themes.png" alt="Theme modes" />
      <br/><sub><b>Theme modes</b> — Dark, Light, and Image mode with custom backgrounds</sub>
    </td>
  </tr>
</table>

---

## Features

**Color mixing**
- Weighted mixing with up to 12 color slots, each with its own slider
- Six algorithms: RGB, HSV, LAB, CMY (subtractive), RYB (weighted), and Kubelka-Munk
- Real-time preview with hex / RGB / HSV readouts
- Right-click fine-tune dialog (lighten, darken, saturate, hue shift, temperature, tint/shade)

**Image sampling**
- Drag-and-drop image loading
- Click to sample individual pixels; drag to average a region
- Scroll-wheel zoom and pan for large images
- Cross-monitor screen color picker with magnified crosshair overlay

**Color harmonies**
- Complementary, analogous, triadic, split-complementary, tetradic, and square schemes
- One-click apply to fill all slots with a generated palette

**Palette I/O (16+ formats)**
- Export: ASE (Adobe), ACO (Photoshop), GPL (GIMP/Inkscape), PAL, ACT, CSS, SCSS, JSON, XML, SVG, and more
- Import: auto-detect format from extension
- Preset palettes: built-in schemes plus user-defined palettes

**Session management**
- Auto-save with crash recovery
- Six persistent session slots plus manual save/load
- Color history (last 20 mixed colors, searchable and reloadable)

**Theming**
- Three visual themes: Dark mode, Light mode, and Image mode (with custom background)
- Custom tooltip system with full CSS control (bypasses native OS tooltip rendering)
- Embedded Montserrat Black font for consistent typography

---

## Installation

Requirements: **Python 3.10 or newer**.

```bash
# Clone or download the project, then from the project root:
pip install -r requirements.txt
python RNV_Color_Mixer.py
```

If you want an isolated environment (recommended):

```bash
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
python RNV_Color_Mixer.py
```

### Alternative: install as a package

The project ships with a `pyproject.toml`, so you can install it like any
other Python package. After installation, the app is available as a
`rnv-color-mixer` command on your PATH:

```bash
pip install .
rnv-color-mixer
```

Use `pip install -e .` instead for an editable install that picks up
code changes without reinstalling.

### Building a standalone executable

The project ships with a PyInstaller spec file and convenience wrapper
scripts for both Windows and Linux:

```bash
pip install pyinstaller

# Windows:
build_windows.bat

# Linux (first run: chmod +x build_linux.sh):
./build_linux.sh

# Or invoke PyInstaller directly (any platform):
pyinstaller RNV_Color_Mixer.spec
```

The build output lands in `dist/RNV_Color_Mixer/`. On Windows, zip the
folder and share it — end users can run `RNV_Color_Mixer.exe` without
installing Python or any dependencies. On Linux, tar the folder
(`tar -czf RNV_Color_Mixer-linux.tar.gz -C dist RNV_Color_Mixer`) and
distribute that.

The build uses **one-folder mode** rather than one-file mode. One-file
builds unpack to a temp directory on every launch, adding ~3 seconds
to startup; one-folder is larger on disk but launches instantly.

Note: Linux binaries built with PyInstaller are tied to the glibc
version of the build host. For maximum compatibility, build on the
oldest distro you want to support (e.g. Ubuntu 22.04 LTS).

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | Add color slot |
| `Ctrl+O` | Upload image |
| `Ctrl+C` | Copy mixed color as hex |
| `Ctrl+S` | Save mixed color as image swatch |
| `Ctrl+Shift+C` | Launch screen color picker |
| `Ctrl+,` or `Ctrl+P` | Open settings & features panel |
| `Ctrl+/` | About dialog |
| `F11` | Toggle tooltips |
| `F12` | Toggle debug overlays |

---

## Project structure

```
rnv-color-mixer/
├── RNV_Color_Mixer.py       Main application entry point
├── test_rnv_color_mixer.py  Comprehensive test suite (Suite 1, locked)
├── verify_files.py          Project integrity checker
├── run_tests.py             Unified test runner (both suites + coverage)
├── pytest.ini               Pytest configuration
├── .coveragerc              Coverage.py configuration
├── pyproject.toml           Project metadata & packaging config
├── requirements.txt         Runtime dependencies
├── requirements-test.txt    Test dependencies
├── py.typed                 PEP 561 type-hint marker
├── RNV_Color_Mixer.spec     PyInstaller build specification
├── build_windows.bat        Windows build convenience script
├── build_linux.sh           Linux build convenience script
├── clean_python_cache.bat   Cache cleaner (Windows)
├── clean_python_cache.sh    Cache cleaner (macOS / Linux)
├── .github/workflows/       GitHub Actions CI (Linux + Windows)
├── tests/                   Suite 2 — pytest test files
├── snapshots/               Reference data for byte-locked tests
├── core/                    Color science, palettes, data models
├── ui/                      Visual layer
├── utils/                   Cross-cutting services
├── resources/               Fonts, icons, button images, backgrounds
└── docs/                    Developer documentation
```

For a deeper module-by-module breakdown, see [`docs/INTERNALS.md`](docs/INTERNALS.md).

---

## Development

**Run the test suite:**

The project ships with a unified test runner that executes both test
suites under coverage and merges the results into a single report:

```bash
# One-time setup
pip install -r requirements-test.txt

# Run all tests with coverage
python run_tests.py

# Other modes
python run_tests.py --report     # regenerate report from existing data
python run_tests.py --summary    # gaps view (skip 100%-covered files)
python run_tests.py --no-merge   # debug: leave per-suite .coverage.* files
```

Two suites run back-to-back:

- **Suite 1** — `test_rnv_color_mixer.py` at the project root: **356 unittest
  tests** covering color math, palette formats, sessions, settings.
  This file is **byte-locked** — its SHA-256 is verified by CI before
  every test run. Modifications to it are rejected at the CI gate.
- **Suite 2** — `tests/`: **530 pytest tests** (with pytest-qt and
  hypothesis) covering app lifecycle, threading, snapshots, property-based
  color-math invariants, and integration scenarios. Plus 25 documented
  skips for tests that exercise platform-specific behavior incompatible
  with the default test environment (full UIHandler construction with
  real background images, async ColorHistory writes on Windows). See
  the inline `@pytest.mark.skip` notes in `tests/` for individual rationale.

Combined: **886 tests, 25 documented skips, 0 failures.**

Branch coverage is enabled in `.coveragerc`; CI gates on a 70% TOTAL
coverage threshold.

**Continuous integration:**

Two GitHub Actions workflows run on every push and pull request:

- **`tests-linux.yml`** — full dual-suite under coverage on Ubuntu,
  with the 70% threshold enforced via `coverage report --fail-under=70`.
- **`tests-windows.yml`** — locked unittest suite + pytest suite on
  Windows (the deployment target).

Both workflows verify the locked file's SHA-256 hash *before* running
any tests; an integrity violation fails the build immediately.

**Verify project integrity:**

```bash
python verify_files.py
```

This script confirms every expected file is present, that version constants
are defined, and that no stale Python cache files would cause import issues.

**Clean Python cache files:**

```bash
# Windows
clean_python_cache.bat

# macOS / Linux (first run: chmod +x clean_python_cache.sh)
./clean_python_cache.sh
```

Stale `__pycache__` directories can cause confusing import errors after
updating files — run the appropriate script for your OS if you see
unexpected behavior.

---

## Architecture notes

- **Theme system** is centralized in `utils/config.py` via the `ThemeManager`
  class. Dark and Image modes share the same palette (Image mode overlays a
  background image); Light mode inverts for print work.
- **Signal management** uses a tracked-connection pattern via
  `utils/signal_manager.py` to prevent memory leaks in long-running sessions.
  Widgets can inherit from `SignalMixin` for per-object tracking.
- **Qt tooltips** are implemented as a custom `_ThemedToolTip` widget with
  `WA_TranslucentBackground`, because native Qt tooltips on Windows ignore
  CSS border-radius.
- **Error handling** is centralized in `utils/error_handler.py` with three
  complementary patterns: `safe_execute()` function, `@safe_method` decorator,
  and `ErrorContext` context manager.
- **Image sampling** uses a `QPixmap` LRU cache (`utils/pixmap_cache.py`) to
  avoid re-rendering at repeated zoom levels.
- **Type-annotated codebase** using PEP 604 modern syntax (`X | None` over
  legacy `Optional[X]`). Ships with a `py.typed` marker (PEP 561) and a
  `[tool.mypy]` config block in `pyproject.toml` for static type checking.

For deeper implementation details, see [`docs/INTERNALS.md`](docs/INTERNALS.md).

---

## Related projects

Part of a suite of color and design tools by [@RNVizion](https://github.com/RNVizion):

- **[RNV Color Picker](https://github.com/RNVizion/rnv-color-picker)** — Professional color extraction and palette management for designers and developers
- **[RNV Color Palette Manager](https://github.com/RNVizion/rnv-color-palette-manager)** — A professional desktop application for creating, managing, and exporting color palettes

---

## License

MIT. See [`LICENSE`](LICENSE) for full text.

---

## Credits

Built with Python, PyQt6, and Pillow. Uses custom implementations of:

- Kubelka-Munk theory for paint mixing simulation
- CIE LAB color space for perceptually uniform blending
- Traditional RYB color model for artist-style mixing

---

## Links

- **Repository:** [github.com/RNVizion/rnv-color-mixer](https://github.com/RNVizion/rnv-color-mixer)
- **Report an issue:** [github.com/RNVizion/rnv-color-mixer/issues](https://github.com/RNVizion/rnv-color-mixer/issues)
- **Author:** [@RNVizion](https://github.com/RNVizion)
