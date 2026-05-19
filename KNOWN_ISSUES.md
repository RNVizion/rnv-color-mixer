# Known Issues

This document tracks known issues in RNV Color Mixer v3.3.3 — tests that
are skipped on CI, real bugs with planned fixes, and platform-specific
behavior worth being aware of.

The presence of an issue here doesn't mean the app is broken. The vast
majority of these have no observable effect on day-to-day app usage — they
surface only in specific test environments or specialized workflows.

---

## Confirmed bugs (real user impact)

### Hex and `.colors` import returns 0 colors for files exported by this app

**Severity:** Real user-facing bug, narrow scope
**Affects:** All platforms
**Status:** Discovered during 2026-05-19 audit, fix planned

**Symptom:** Exporting a palette to `.hex` or `.colors` format and then
importing the same file back into the app produces an empty palette. The
file on disk is correctly formed and human-readable; the bug is in the
import parser.

**Root cause:** `_export_hex()` and `_export_colors()` write data lines
that begin with `#RRGGBB`, while the corresponding importers
(`_import_hex()` and `_import_colors()`) skip any line beginning with `#`
on the assumption that all `#` lines are comments. Every data line gets
treated as a comment and discarded, leaving only the comments — which
have no parseable hex content — as input. The result is an empty color
list.

**Workaround for users until fix lands:** Edit the exported file in a
text editor and prefix each data line with a non-`#` character (e.g., a
space) before importing. Or use `.json`, `.gpl`, or `.ase` for
round-trip-safe storage.

**Fix plan:** Refactor the comment-detection logic in both importers to
distinguish between true comment lines (starting with `#` followed by
non-hex characters or whitespace) and hex data lines (starting with
`#RRGGBB`). A shared regex helper such as
`re.compile(r'^(#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3}))(?![0-9A-Fa-f])')`
can be used by both importers. Round-trip tests should be added to
prevent regression.

---

## CI-skipped tests

The following tests pass locally but are skipped on GitHub Actions CI
runners due to environment-specific quirks (no display server, virtualized
filesystems, etc.). Each skip is annotated in the workflow file with a
comment explaining the cause.

### `test_load_real_image_if_available` (locked unittest)

**Skipped on:** Linux CI, Windows CI
**Reason:** Hangs indefinitely when run under offscreen Qt
(`QT_QPA_PLATFORM=offscreen`). The test loads the
resources/background_images/background.png file via
`ImageHandler.load_image()`. On CI runners (no display server), the load
operation never completes.

**User impact:** None. Production users always run with a real display
server, where the load completes instantly. The test passes in the local
development environment for the same reason.

**Planned fix:** None required. This is a test-environment artifact, not
a code defect.

### `TestAsyncFileOpsErrorPaths` class (pytest)

**Skipped on:** Linux CI only
**Reason:** Tests in this class spawn QThread workers and exercise error
recovery paths (missing files, invalid paths). On offscreen Linux, the
QThread lifecycle interacts with the test harness in a way that causes
Python to abort with SIGABRT (exit code 134). Tests pass cleanly on
Windows CI and on local Linux desktops with a real display.

**User impact:** Theoretically none — production users have a real
display, where these code paths work correctly. The crash conditions
(offscreen Qt + filesystem error in a worker thread) don't occur in
normal app usage.

**Planned fix:** Refactor `utils/async_file_ops.py` to decouple QThread
lifecycle from filesystem operations, allowing the tests to verify
behavior without spawning real threads.

### `tests/test_snapshots.py` (whole file)

**Skipped on:** Windows CI only
**Reason originally documented:** Byte-mismatch between Windows-generated
palette files and Linux-generated snapshots, suspected to be CRLF/LF
line-ending difference.

**Updated finding (diagnostic 2026-05-14):** The byte mismatch on text
formats (GPL, JSON, XML, CSS, SVG, HEX, HSV, HSL, .colors, .afpalette,
.clr) is indeed CRLF/LF — text-mode `open()` calls in the export code
substitute `\r\n` on Windows. This is cosmetic for text consumers but
trips byte-exact comparison.

For binary formats (ASE, ACO, ACB, swatches, txt), the situation is
different: file sizes match exactly between platforms, and bytes are
identical when generated with identical inputs. These five binary-format
tests pass on Windows locally even today.

**Updated finding (2026-05-19):** With the ASE and ACO export fixes
landed (see Resolved section below), the binary-format snapshots are now
correct against the official Adobe specifications. The Windows skip is
more conservative than strictly necessary for binary formats, but kept
in place until the CRLF/LF issue is also resolved — otherwise enabling
the suite would surface 11 newline-related failures on Windows.

**User impact:** Cosmetic line-ending differences in text-format exports
on Windows. No effect on file readability or correctness in consuming
applications.

**Planned fix:** Audit `core/palette_formats.py` text exports and
explicitly set `newline=''` or use binary mode with manual `\n`
delimiters to prevent platform-specific line-ending substitution. Once
landed, regenerate text-format snapshots and re-enable the whole suite
on Windows CI.

### Phase 9.3 platform-dependent test skips

**Skipped on:** Both CI runners (already documented inline via
`@pytest.mark.skip` decorators).

These are 21 tests across three classes that were added in Phase 9.3 but
proved incompatible with the default test environment:

- 15 `UIHandler` tests skipped in `tests/test_core_module_apis.py` and
  `tests/test_lifecycle_handlers.py` — `UIHandler()` construction loads
  and PNG-encodes the ~8 MB background image via PIL, exceeding
  reasonable test timeouts (>10s per test).
- 6 `ColorHistory` tests skipped in `tests/test_error_recovery_paths.py`
  — constructor + `add_color()` + `save()` chain spawns a QThread for
  async filesystem writes that crashes Python natively on Windows.

**User impact:** None. These tests were attempts to extend coverage on
existing code paths; the code itself works correctly at runtime.

**Planned fix:** Refactor `UIHandler` to lazy-load the background image
on first access (rather than at construction), and split QThread
machinery off from `ColorHistory` construction (same as the
`AsyncFileOps` refactor mentioned above).

---

## Coverage threshold

**Status:** CI threshold set to 69%, locally 72%.

The CI coverage threshold sits at 69% rather than the local-measured 72%
because the skipped tests above exercise real code paths (image loading,
async file operations, error recovery). With those tests excluded, CI
measures lower coverage. The 69% gate accommodates this with a 0.4%
safety margin against the typical CI run.

**Path back to 70%+ CI coverage:** Refactor the skipped test conditions
(lazy image loading, decoupled QThread/file ops). Once those land, the
currently-skipped tests can run on CI, coverage rises back to ~72%, and
the threshold can move with it.

---

## Slow test suite runtime

**Status:** Acknowledged, deferred.

The full test suite (`python run_tests.py`) takes 18-25 minutes on a
typical development machine. CI runs are similar. Most of this time is
spent in pytest fixtures that reconstruct the full `ColorMixerApp()`
instance per test, rather than reusing one instance across tests.

**User impact:** None. This affects developer workflow only.

**Planned fix:** Refactor the `app_window` pytest fixture in
`tests/conftest.py` to be session-scoped rather than function-scoped.
Estimated 4-8 hours of investigation and verification work. Tracked for
a future release.

---

## Investigation log

Significant diagnostic findings during ongoing development (May 2026):

**2026-05-14:** Identified that `.ase` export produces files Adobe
Photoshop cannot import. Diagnostic process:

1. Initial hypothesis: CRLF/LF substitution on Windows in binary file
   writes. Ruled out by inspection — `_export_ase()` correctly uses
   `'wb'` mode.
2. Second hypothesis: Windows-specific byte corruption. Ruled out by
   testing the Linux-generated snapshot file in Photoshop — same failure.
3. Conclusion: The .ase format implementation itself was incorrect
   against the Adobe Swatch Exchange specification. Both Linux and
   Windows produced the same wrong bytes, which is why byte-comparison
   snapshot tests passed but Adobe products rejected the files.

Resolution documented below under "Resolved Issues."

**2026-05-19:** Extended investigation to `.aco` (same failure mode as
.ase) and identified a separate precision bug in `.aco` import from
Photoshop-written files. Diagnostic process:

1. Generated reference `.aco` and `.ase` files from Photoshop's own
   "Save Swatches" export to use as ground truth.
2. Compared byte-by-byte against the app's exports.
3. For ASE, found two compounding bugs: missing null terminator on
   UTF-16BE names, plus block length constant off by 2.
4. For ACO export, found name length field was written as 2-byte uint16
   instead of 4-byte uint32 per spec.
5. For ACO import, found that floor division (`X // 257`) lost one unit
   per channel on files using Photoshop's non-canonical 16-bit encoding.
   Rounding (`round(X / 257)`) recovers the original values without
   affecting round-trips of canonically-encoded files.

End-to-end verification in Photoshop confirmed each fix produces/accepts
files Photoshop handles correctly. Resolution details under "Resolved
Issues" below.

**2026-05-19 (audit):** Survey of palette format parity across the three
RNV projects (Color Mixer, Color Picker, Color Palette Manager)
identified a fourth bug: `_import_hsl()` was passing `(h, s, l)` to a
function expecting `(h, l, s)`, silently corrupting HSL palette imports.
Other two projects had already fixed this independently; Color Mixer was
the holdout. Resolved.

Also discovered during the same audit: `_import_hex()` and
`_import_colors()` reject lines starting with `#`, but the corresponding
exporters write data lines starting with `#`. Documented above as the
sole remaining open user-facing bug.

---

## Resolved Issues

Resolved issues are retained below as a diagnostic record. Each entry
documents the original symptom, root cause, and fix so the rationale
remains accessible after the code change is no longer fresh in memory.

### Adobe Swatch Exchange (`.ase`) export rejected by Photoshop/Illustrator

**Status:** Resolved 2026-05-19.

**Original symptom:** Files exported as `.ase` were rejected by Photoshop
with "unexpected end-of-file" and loaded as empty palettes in
Illustrator.

**Root cause:** Two compounding bugs in `_export_ase()`:

1. Color name UTF-16BE strings were not null-terminated. The ASE spec
   requires names to end with `0x0000` and the name length field to
   count characters including the terminator.
2. The block length constant was `22` instead of `20`, declaring every
   color block two bytes longer than its actual content. Adobe parsers
   misaligned when reading the next block, eventually hit EOF, and
   rejected the file.

**Fix:** Append `b'\x00\x00'` to encoded name bytes, update name length
calculation accordingly, and correct the block length constant from 22
to 20. The two changes compound: with both applied, the block length
declared in the file matches the actual block content byte-for-byte.

**Verification:** Photoshop accepts exports and displays all colors with
correct names. Snapshot regenerated from 172 bytes to 180 bytes (the
8-byte increase is two null-terminator bytes per color × 4 colors).

### Adobe Color (`.aco`) export rejected by Photoshop

**Status:** Resolved 2026-05-19.

**Original symptom:** Files exported as `.aco` were rejected by Photoshop
with "unexpected end-of-file".

**Root cause:** The ACO V2 name length field is a 4-byte unsigned integer
per the published spec (confirmed against Cyotek's reverse engineering
and Larry Tesler's ACO documentation). The exporter was writing a 2-byte
unsigned integer, causing Photoshop to misinterpret the name length as a
massive number (because the next two bytes were read as the high half of
a uint32), then attempt to read megabytes of name data before hitting
EOF.

**Fix:** Change `struct.pack('>H', len(name))` to
`struct.pack('>I', len(name))` in the V2 section of `_export_aco()`.

**Verification:** Photoshop accepts exports and displays all colors with
correct names. Snapshot regenerated to 168 bytes (was 160).

### Adobe Color (`.aco`) import showed colors off by 1 per channel

**Status:** Resolved 2026-05-19.

**Original symptom:** Importing an `.aco` file written by Photoshop
showed each color channel one value lower than Photoshop's color picker
displayed for the same swatch. For example, RGB(210, 188, 147) in
Photoshop's color picker appeared as RGB(209, 187, 146) in the app after
import.

**Root cause:** Photoshop encodes 8-bit color values into 16-bit storage
using a non-canonical scaling — for example, 210 encodes to `0xD2D1`
(53969), not the canonical `X * 257 = 53970`. The import used floor
division (`X // 257`), which on these non-canonical values produces
`X - 1`. Files written with the canonical `X * 257` encoding (including
this app's own exports) round-tripped correctly under floor division,
which masked the issue against any test that didn't involve
Photoshop-written files.

**Fix:** Replace floor division with rounding:
`round(X / 257)` per channel. Photoshop's non-canonical values round to
the intended 8-bit value, and canonical `X * 257` values continue to
produce identical results under both methods (so self-written file
round-trips are unchanged).

**Verification:** Photoshop reference files now display matching color
values in the app's color picker. Round-trip of self-written ACO files
preserved exactly.

### HSL import silently corrupted color values

**Status:** Resolved 2026-05-19.

**Original symptom:** Importing a `.hsl` palette file produced colors
substantially different from what was exported. Example: brand gold
(210, 188, 147) round-tripped as (178, 127, 31) — a different color
family entirely.

**Root cause:** `_import_hsl()` passed `(h, s, l)` to
`ColorMath.hsl_to_rgb()`, but that function unpacks tuples in `(h, l, s)`
order (it wraps Python's `colorsys.hls_to_rgb`, which uses HLS
convention rather than HSL). Saturation and lightness were silently
swapped on every import, with no error or warning.

The bug was caught by cross-project comparison: RNV Color Picker and RNV
Color Palette Manager had already fixed this independently (both
contained comments explaining the `(h, l, s)` requirement), and the
audit revealed Color Mixer as the lone holdout.

**Fix:** Pass `(h, l, s)` to match the function's actual unpacking
order. The fix matches the existing correct implementations in the two
sibling projects.

**Verification:** Round-trip drift on the test palette is now within ±1
per channel, the inherent precision limit of the `.hsl` text format's
one-decimal-place output. Increasing decimal precision in the export
was tested and made drift slightly worse on some values; one decimal
place is empirically the sweet spot for this format.

---

## Reporting new issues

If you encounter behavior not listed here, please open an issue at:
https://github.com/RNVizion/rnv-color-mixer/issues

Include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
