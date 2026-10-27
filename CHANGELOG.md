# Changelog

All notable changes to RNV Color Mixer are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

Everything since 2026-05-21, by theme. The version number is held at
3.3.3; no release has been cut.

### Changed

- **Python 3.13 is the floor.** `pyproject.toml` requires `>=3.13` and
  both CI workflows run 3.13. The project had declared 3.10+ while CI ran
  only 3.11. `tests/test_fleet_floor.py` keeps the declaration and the CI
  version in step.

- **Colors come from rnv-brand.** Every color moved out of
  `utils/config.py` into `utils/colors.py`, and none is a bare hex in a
  palette any more. `brand_map.json` says where each one comes from: a
  name in rnv-brand, or a value this app owns, with the reason.
  `tools/sync_colors.py` writes the values and `COLORS.md`, the chart of
  the app's colors; `--check` writes nothing. A daily `brand-sync`
  workflow opens a pull request when a brand color the app uses moves.
  Hex values are written in lower case.

- **rnv-brand is pinned to a commit** in `tests/requirements-dev.txt`.
  The tests that compare the app's colors with the brand used to skip
  when rnv-brand was not installed; they now run against the pinned
  revision.

- **Dependencies.** The test requirements moved from
  `requirements-test.txt` at the root to `tests/requirements-dev.txt`.
  pytest, pytest-qt, pytest-timeout, coverage and hypothesis take the
  ranges shared by the five RNV apps, `requirements.txt` and
  `pyproject.toml` declare the same runtime ranges, and PyQt6 is capped
  below 7 in both.

- **State files are written atomically.** Settings, sessions, the recent
  sessions list, the color history and saved presets go through
  `utils/atomic_write.py`, so a crash during a save leaves the old file or
  the new one, never half of each.

- **The theme button remembers the mode** for the next launch, and the
  Settings tab's Default Theme box follows the mode the app is in.

- **Contrast.** Text and control colors were checked in all three modes
  and adjusted where they fell short: the muted descriptions and hints,
  gold used as text, the empty lines of the History and Presets lists,
  the canvas's selection and color preview in light mode (a dragged
  selection is now see-through gold), the About dialog's light
  scrollbar, the slot's weight slider and Remove button. A status is
  never shown by color alone.

- **Smaller images.** The Image mode background is now 3840×2169 (it was
  16000×9038), and the settings gear images, `icon.png` and
  `special_slot.png` are 512×512.
  `tests/test_image_budget.py` holds those sizes.

- **The history keeps 50 colors by default**, the History Size Limit's
  default, where it kept 20 whatever the setting said. Lowering the limit
  removes the oldest colors beyond it.

- **The Default Theme box shows Auto (follow system)** while Auto is the
  saved choice, so a later Save no longer replaces Auto with the mode it
  gave.

- **Subtractive CMY mixes like inks.** Each color is a filter that passes
  part of each channel's light, and the mix multiplies them (a weighted
  geometric mean), so yellow and blue make a dark green. It used to
  average the cyan, magenta and yellow values, which always gave the same
  color as weighted RGB. The RNV Color Palette Manager uses the same
  formula, and the two agree.

- American spelling throughout, file names included.

- The CI actions are at their Node 24 versions.

### Added

- **The Settings tab's choices take effect.** Each was saved and then
  ignored:
  - **Color Mixing Algorithm**: the mix uses the chosen one of six,
    weighted RGB (still the default), HSV, LAB, subtractive CMY, RYB and
    Kubelka-Munk, and Save mixes the slots again at once. The choice is
    kept for the next launch.
  - **History Size Limit** (1 to 1000) holds the history at startup and as
    soon as it is saved.
  - **Enable color history**: when it is off, mixed colors are not added.
  - **Auto (follow system)** opens in Light or Dark as the operating system
    is set (Dark when it can't tell), and follows the system when it
    changes while the app runs. It never picks Image mode; a press of the
    theme button ends it.
  - **Auto-load last session** opens the session at the top of Recent
    Sessions at startup. When the app offers to recover a run that did not
    close, that offer comes instead.
  - **Default Export Format**: PNG or JPEG is the type Save Color Swatch
    opens on, and JSON, ASE or GPL the format Export Palette opens on.
- `in.sh` (Linux and Codespaces; also installs the Qt system libraries)
  and `in.ps1` (Windows; makes `.venv` with Python 3.13) set up a
  checkout from `requirements.txt` and `tests/requirements-dev.txt`.
- `tools/accent_images.py` and `ACCENT_IMAGES.md`, the list of images
  with the gold drawn into their pixels.
- Guard tests, among them `test_colors_in_sync`, `test_register_pin`,
  `test_atomic_state_writes`, `test_status_carried_by_a_word`,
  `test_accent_images`, `test_setup_scripts`, `test_readme_test_counts`
  (the test counts in the README are floors that hold),
  `test_locked_file_digest` (the locked suite's SHA-256 matches the one
  CI checks) and `test_no_vacuous_tests`.

### Fixed

- **The harmony description reads in Light mode.** Its text, the panel's dark gold, sat on a
  wash of the same gold that read 4.49:1, just under the 4.5 the brand sets for text on a
  see-through color. The wash is lighter now: 4.71:1 in Light, 8.39:1 in Dark and Image.
- **Loading an image over 10 MB could hang** wherever no one could
  answer: the question was asked inside `ImageHandler.load_image`. It
  moved to the window's own load path, with the wording unchanged.
- **Importing a palette could block on a dialog** in the same way;
  `FileUtils.import_palette_data` returns the problem instead of showing it.
- **Two quick history saves could abort the app**, by destroying a writer
  thread that was still running. A writer is now kept until it finishes.
- **Deferred callbacks no longer run after their widget is gone.**
- `Image.getdata()`, which Pillow 14 removes, is reached through
  `utils/pil_compat.py`.
- An invalid escape sequence in a test docstring, which Python reports as
  a `SyntaxWarning`.
- An unread settings default, a new slot's color, is no longer stored.
- **Every launch after a normal close offered to recover the previous
  session.** Any auto-save on disk triggered the offer, and a normal close
  leaves the auto-saves in place. A flag, `.recovery_needed` in the sessions
  folder, now marks a run in progress and a normal close removes it, so the
  offer comes only after a run that did not close. The 6 newest auto-saves
  are still kept.
- **`pip install .` left out `resources/`**, so an installed copy had no
  font, icons or images and no Image mode. The fonts, icons, button images
  and background now install beside the code, where the app looks for them.
- Every skipped and deselected test was restored. Several had been hiding
  the defects above; both CI runners now run both suites complete (see
  `KNOWN_ISSUES.md`).

### Documentation

- Documentation checked against the code and corrected throughout, and the About dialog's help text with it (#87 A).

---

## [3.3.3] - 2026-05-12 to 2026-05-21

Initial public release, followed by a bug-fix sweep covering Adobe
binary format compatibility, palette import correctness, and
cross-platform export consistency.

The version number is held at 3.3.3 throughout this period because
all fixes are line-level correctness improvements behind existing
features — no public API changes, no user-visible feature changes.

### Initial release (2026-05-12)

The first version published to GitHub with green CI badges on both
Linux and Windows, a polished README, `KNOWN_ISSUES.md` documenting
test skips and confirmed bugs, and the full feature set:

- Kubelka-Munk paint mixing alongside multi-algorithm mixers
  (RGB, LAB, RYB, CMY)
- 16+ palette export/import formats including Adobe Swatch Exchange
- Three themes (Dark, Light, Image Mode)
- Screen color picker with multi-monitor support
- Auto-save and session restore
- Custom tooltip system and async file I/O
- Comprehensive logging
- ~19,000 lines of Python 3.10+ PyQt6 code across 31 files

### Fixed (2026-05-19 through 2026-05-21)

- **Adobe Swatch Exchange (`.ase`) export** now produces files Adobe
  Photoshop and Illustrator accept. Two compounding bugs were
  identified: color name UTF-16BE strings missing the null terminator
  required by the ASE spec, and the block length constant being `22`
  instead of `20`. Both contributed to the file declaring incorrect
  byte boundaries, causing Adobe parsers to misalign and fail with
  "unexpected end-of-file."

- **Adobe Color (`.aco`) export** now produces files Photoshop accepts.
  The ACO V2 name length field was being written as a 2-byte `uint16`
  but the spec requires 4-byte `uint32`. Photoshop was reading the next
  two bytes as the high half of a 32-bit length, attempting to read
  megabytes of name data, and failing at EOF.

- **Adobe Color (`.aco`) import** from Photoshop-written files now
  returns the original color values. Photoshop encodes 8-bit colors
  into 16-bit storage using a non-canonical scaling (e.g., 210 →
  `0xD2D1`, not `0xD2D2` as canonical `X * 257` would produce). The
  importer used floor division (`X // 257`), losing one unit per
  channel on Photoshop-written files. Replaced with rounding
  (`round(X / 257)`), which recovers correct values without affecting
  round-trips of self-written canonically-encoded files.

- **HSL (`.hsl`) import** no longer silently corrupts colors. The
  importer was passing `(h, s, l)` to `ColorMath.hsl_to_rgb()`, but
  that function wraps Python's `colorsys.hls_to_rgb` and unpacks
  tuples in `(h, l, s)` order (HLS convention, not HSL). Saturation
  and lightness were silently swapped on every import. Bug caught via
  cross-project comparison; the other two RNV projects had already
  fixed this independently.

- **Hex (`.hex`) and `.colors` import** now correctly returns palette
  contents instead of an empty list. Both importers skipped every line
  starting with `#`, on the assumption that all `#` lines were
  comments. The corresponding exporters write data lines beginning
  with `#RRGGBB`, so every data line was being discarded. Fixed with
  a module-level `_HEX_DATA_LINE` regex that distinguishes data lines
  (`#` followed by 6 hex digits) from comment lines (`#` followed by
  text or whitespace).

- **Text-format exports** now produce byte-identical output across
  Windows, macOS, and Linux. All 12 text-format export methods (gpl,
  json, xml, css, svg, hex, hsv, hsl, colors, afpalette, clr, txt)
  used Python's text-mode `open()`, which substitutes `\r\n` for `\n`
  on Windows only. This produced inconsistent palette files when
  shared across platforms and broke cross-platform snapshot testing.
  Fix applied across three patterns: simple text writes (8 methods)
  use `newline='\n'`, JSON writes (2 methods) use the same fix, and
  ElementTree XML/CLR exports (2 methods) switched to binary mode
  with explicit file objects.

- **`.gitattributes` precedence**: the `snapshots/** binary` rule was
  being overridden by `*.txt text` and other extension rules later in
  the file, due to git's last-matching-rule-wins precedence. This
  caused snapshot `.txt` files (palette and stylesheets) to receive
  native line-ending conversion on Windows checkout, breaking
  byte-exact comparison. Moved the rule to the last line of
  `.gitattributes` so it overrides all extension-specific rules.

### Added

- `tests/test_snapshots.py` re-enabled on Windows CI. The previous
  `--ignore=tests/test_snapshots.py` flag has been removed from
  `.github/workflows/tests-windows.yml`. Both Linux and Windows CI
  now run the full pytest suite without deselects for snapshot tests.

- `KNOWN_ISSUES.md` Resolved Issues section now documents the
  diagnostic narrative for each fix, preserving the rationale for
  future maintainers (including future-me).

### Changed

- `_HEX_DATA_LINE` regex added at module level in
  `core/palette_formats.py`, used by both `_import_hex` and
  `_import_colors`.

- `hex`, `colors`, and `hsl` promoted from quirky-format tests to
  the `CLEAN_FORMATS` parameterized test list in
  `tests/test_palette_format_imports.py`, now that their round-trips
  are exact. Three obsolete tests that pinned the buggy behavior were
  removed.

### Engineering notes

This bug-fix sweep was driven by a cross-project audit: the same
`palette_formats.py` module exists in three RNV projects (Color Mixer,
Color Picker, Color Palette Manager) with minor variations. Diffing
the implementations of identical methods surfaced four bugs in Color
Mixer that the other projects had already fixed independently — the
HSL channel swap was caught this way, as were the hex/`.colors`
comment-handling issues.

The Adobe binary format bugs (ASE/ACO) were discovered by Color
Mixer's snapshot tests passing while Photoshop rejected the files.
The tests were comparing the app's output to itself, not against the
spec. Byte-level comparison against Photoshop-generated reference
files revealed the actual structural problems. **Snapshot tests
validate relative consistency, not spec compliance** — a passing
snapshot test only proves the app is self-consistent, not that the
output is correct against an external standard. The two are easy to
conflate.

The CRLF/LF fix was triggered by a Linux CI failure that surfaced
only after the Adobe binary fixes regenerated some snapshots on
Windows. The `binary` attribute in `.gitattributes` faithfully
preserved whatever bytes were committed, including the wrong ones.
**Snapshot regeneration should happen on the canonical platform
(Linux, matching CI), or the binary attribute will lock in
platform-specific bytes forever.**

All five fixes were verified end-to-end: Adobe binary fixes confirmed
in Photoshop, HSL and hex/colors verified with round-trip tests, line
endings verified with hex dump and CI on both platforms.
