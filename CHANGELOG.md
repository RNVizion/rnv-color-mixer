# Changelog

All notable changes to RNV Color Mixer are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
