# Known Issues

This document tracks known issues in RNV Color Mixer v3.3.3 — tests that
are skipped on CI, real bugs with planned fixes, and platform-specific
behavior worth being aware of.

The presence of an issue here doesn't mean the app is broken. The vast
majority of these have no observable effect on day-to-day app usage — they
surface only in specific test environments or specialized workflows.

---

## Confirmed bugs (real user impact)

*No open user-facing bugs at this time.*

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

### `ColorHistory` async-write tests

**Skipped on:** Both CI runners (annotated inline via
`@pytest.mark.skip` decorators).

Six tests in `tests/test_error_recovery_paths.py` exercise the
`ColorHistory` constructor + `add_color()` + `save()` chain. The save
path spawns a QThread for async filesystem writes, and the test harness's
interaction with that thread crashes Python natively on Windows.

**User impact:** None. These tests were attempts to extend coverage on
existing code paths; the code itself works correctly at runtime.

**Planned fix:** Split QThread machinery off from `ColorHistory`
construction. Same architectural pattern as the `AsyncFileOps` refactor
listed above — both classes mix lifecycle management of background
threads into operations that conceptually shouldn't require them.

### `FileWriterThread` signal tests — intermittent SIGABRT, deliberately not skipped

**Runs on:** both CI runners, and green there.

Measured 22 Aug 2026 on offscreen Linux:
`tests/test_threading.py::TestColorHistoryThreading::test_save_async_emits_finished_with_success_true`
aborts Python natively (`Fatal Python error: Aborted`) in roughly one run
in thirty, and much more readily when the machine is under load. It did so
on an **untouched checkout of `main`** as well as on a modified tree, so it
is the thread lifecycle and the environment, not any particular change.

That last point is the reason this entry exists. The abort surfaces during
whatever work happens to be in flight, and it reads exactly like a
regression in that work. It is not one.

Same root cause as the two entries above. `qtbot.waitSignal` returns the
instant `finished` fires; the `thread` local then goes out of scope at the
end of the test, and Qt can find itself destroying a `QThread` that has not
finished unwinding. `test_file_writer_thread_progress_signal_reaches_100`
is in the same family.

**User impact:** None. Nothing in the running app destroys a
`FileWriterThread` this way — the owning object holds the reference for as
long as the thread lives.

**Why it is not skipped:** it passes on both runners and covers a real
path. Skipping would trade a rare red for permanently missing coverage.
If it becomes noisy, deselect it the way `TestAsyncFileOpsErrorPaths` is
deselected rather than marking it skip, so the cost stays visible.

**Planned fix:** the same refactor as above — hold the thread on the
object, not on the stack.

---

## Cross-project audit findings

The three RNV projects (Color Mixer, Color Picker, Color Palette
Manager) share a substantial amount of code structure, including
`palette_formats.py`, theme management, and the background image used
for Image Mode. As of 2026-05-21, all three projects use the same
16000×9038 background image (~95 MB on disk).

A timing diagnostic confirmed that PIL's pipeline for opening, decoding,
resizing, and re-encoding this image takes ~2 seconds in isolation
across all three projects. This is moderate latency — noticeable but
acceptable for production app startup. Color Picker and Color Palette
Manager were audited for the same eager-load anti-pattern that affected
Color Mixer; both already structure their image-loading in ways that
don't block testing. No corresponding refactor is planned for those
projects at this time.

Earlier cross-project comparisons also surfaced bugs that Color Mixer
inherited and the other two projects had already fixed independently:
the HSL channel swap and the hex/`.colors` comment-handling issue
documented under Resolved Issues below. The audit pattern continues to
be valuable as a bug-finding tool.

---

## Coverage threshold

**Status:** CI threshold set to 69%, locally measured higher after the
2026-05-21 UIHandler refactor (the 15 newly-enabled tests added
meaningful coverage on theme application and slot styling code paths).

The CI coverage threshold was set to 69% during the period when the
UIHandler and ColorHistory tests were skipped. With UIHandler tests
now back in the suite, CI coverage should rise — the threshold has not
yet been moved to reflect this; the conservative 69% gate remains in
place pending one or two CI runs to confirm the new baseline.

**Path back to 72%+ CI coverage:** Refactor the remaining skipped
tests (decoupled QThread/file ops in `ColorHistory` and
`AsyncFileOpsErrorPaths`). Once those land, coverage rises further and
the threshold can move accordingly.

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
identified additional bugs:

1. `_import_hsl()` was passing `(h, s, l)` to a function expecting
   `(h, l, s)`, silently corrupting HSL palette imports. Other two
   projects had already fixed this independently; Color Mixer was the
   holdout. Resolved.
2. `_import_hex()` and `_import_colors()` rejected every line starting
   with `#`, including the data lines (which begin with `#RRGGBB`).
   Self-export-then-import returned 0 colors. Cross-project comparison
   showed Color Picker used a `_HEX_DATA_LINE` regex helper that
   correctly distinguished data lines from comments, and Palette Manager
   used a different-but-functional inline comment check. Color Mixer was
   the only project where both importers were broken. Ported the Color
   Picker regex approach to Color Mixer for both methods. Resolved.

**2026-05-20:** Investigated CRLF/LF line-ending divergence in
text-format palette exports. Diagnostic process:

1. Initial trigger: `tests/test_snapshots.py` failing on Linux CI after
   Adobe binary format fixes landed, despite previously passing.
2. Discovered 11 text-format snapshots had Windows CRLF endings
   committed to the repo, while Linux CI produced LF on export.
3. Root cause located in `palette_formats.py` itself — Python's
   text-mode `open()` substitutes `\n` for `\r\n` on Windows, affecting
   all 12 text-format export methods.
4. Initial fix (2026-05-19): converted 11 of 12 text-format snapshots
   to LF as a stopgap so Linux CI would pass; Windows CI continued to
   deselect `test_snapshots.py`. (One snapshot — txt — was missed in
   the normalization.)
5. Real fix (today): audited all 12 export methods, applied
   `newline='\n'` to text-mode `open()` calls and switched ElementTree
   exports to binary mode with explicit file objects. Converted the
   missed txt snapshot. All 19 snapshot tests now pass on both
   platforms. Windows CI deselect removed. Resolved.

**2026-05-21:** Investigated UIHandler construction cost as the cause
of 15 skipped tests. Diagnostic process:

1. The pre-existing skip decorators on `TestUIHandlerLineFill` and
   `TestUIHandlerThemeChain` cited ">10s per construction" as the
   reason for skipping. The measurement was old and unverified.
2. Wrote a standalone PIL timing diagnostic that measures the bare
   open + decode + resize + encode pipeline on the production image.
   Ran in all three RNV projects (same image file shared across all
   three). Result: ~2 seconds per load, not >10 seconds.
3. The original 10-second figure most likely reflected pytest's
   instrumented execution (coverage tracking, assertion rewriting,
   subprocess overhead) on top of the bare PIL work — not the PIL
   work itself. Either figure is enough to make 15 tests skipped at
   default timeouts; the smaller number doesn't change the conclusion.
4. Cross-project audit confirmed Color Picker and Color Palette
   Manager already structure their image-loading in ways compatible
   with testing, so no corresponding refactor was needed in those
   projects.

Resolution documented below under "Resolved Issues."

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

### Hex and `.colors` import returned 0 colors for files exported by this app

**Status:** Resolved 2026-05-19.

**Original symptom:** Exporting a palette to `.hex` or `.colors` format
and importing the same file back into the app produced an empty palette.
The files on disk were correctly formed and human-readable; the bug was
in the import parsers.

**Root cause:** `_import_hex()` and `_import_colors()` skipped every
line starting with `#`, on the assumption that all `#` lines were
comments. The corresponding exporters write data lines that begin with
`#RRGGBB`, so every data line was treated as a comment and discarded,
leaving only the actual comment lines — which have no parseable hex
content — as input. The result was an empty color list.

**Fix:** Added a module-level `_HEX_DATA_LINE` regex helper:

```python
_HEX_DATA_LINE = re.compile(
    r'^(#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3}))(?![0-9A-Fa-f])'
)
```

Both importers use the regex to classify each line: if it matches, the
line is a data line and gets parsed; if not, the line is a comment or
header and gets skipped. The trailing inline `# Comment` text within a
data line is stripped before splitting fields, so it doesn't interfere
with parsing.

The fix matches the existing implementation in RNV Color Picker. RNV
Color Palette Manager uses a different (but also correct) inline check
that distinguishes pure-`#` and `# `-prefixed lines from data lines.
Cross-project verification confirmed all three projects now round-trip
both formats cleanly.

**Verification:** Round-trip test for both `.hex` and `.colors` produces
colors identical to the originals — `(255, 0, 0)`, `(0, 255, 0)`,
`(0, 0, 255)`, and `(210, 188, 147)` all round-trip exactly.

### Text-format palette exports produced CRLF line endings on Windows

**Status:** Resolved 2026-05-20.

**Original symptom:** Text-format palette exports (`gpl`, `json`, `xml`,
`css`, `svg`, `hex`, `hsv`, `hsl`, `colors`, `afpalette`, `clr`, `txt`)
produced Windows CRLF line endings on Windows but LF on Linux. The
byte-level mismatch caused `tests/test_snapshots.py` to fail on Windows
CI, which is why the whole test file had been deselected via
`--ignore=tests/test_snapshots.py` in the Windows workflow.

**Root cause:** Python's text-mode `open(path, 'w')` performs universal
newline translation — `\n` characters in the program's output are
substituted for `\r\n` on Windows. Twelve `_export_*` methods in
`core/palette_formats.py` used text mode, all of them affected. The
two ElementTree-based methods (`_export_xml`, `_export_clr`) had the
same underlying issue because `tree.write(path, ...)` opens the file
internally in text mode.

**Fix:** Three patterns of change, depending on how the method writes
to the file:

1. **Plain text mode with `f.write()`** (8 methods: gpl, colors, css,
   svg, hex, hsv, hsl, txt): change `open(path, 'w')` to
   `open(path, 'w', newline='\n')`. The explicit `newline` argument
   disables universal newline translation.
2. **Text mode with `json.dump()`** (2 methods: json, affinity): same
   fix — add `newline='\n'` to the `open()` call. `json.dump` writes
   `\n` characters directly; the text-mode translation was the
   intermediate culprit.
3. **ElementTree `tree.write()`** (2 methods: xml, clr): open the file
   manually in binary mode and pass the file object to `tree.write()`:
   `with open(path, 'wb') as f: tree.write(f, encoding='utf-8',
   xml_declaration=True)`. When given a binary file object, ElementTree
   writes raw bytes without text-mode translation.

The txt snapshot file (`snapshots/palette_4color.txt`) was missed in
the 2026-05-19 normalization and was converted to LF as part of this
fix.

**Verification:** Diagnostic script confirmed all 12 text-format
exports produce LF only after the fix. All 19 snapshot tests pass on
both Windows and Linux. Removed `--ignore=tests/test_snapshots.py`
from the Windows CI workflow.

### UIHandler eagerly loaded background image, slowing 15 tests

**Status:** Resolved 2026-05-21.

**Original symptom:** Fifteen tests (5 in `TestUIHandlerLineFill`,
10 in `TestUIHandlerThemeChain`) were skipped at runtime with
`@pytest.mark.skip` decorators citing slow `UIHandler()` construction.
The decorators noted that constructing a `UIHandler` triggered a
PIL-based load of the 16000×9038 background image, which took long
enough to make repeated construction across many tests impractical.

**Root cause:** `UIHandler.__init__` called `_load_background_image()`
unconditionally whenever `theme_manager.image_mode_available` was True.
The expensive PIL pipeline (open + decode + resize + re-encode to PNG
bytes for QPixmap) ran at construction time, even though the result was
only used in Image Mode. Tests that needed a `UIHandler` for any reason
paid the load cost even when they did not exercise Image Mode at all.

A timing diagnostic (run 2026-05-21) measured ~2 seconds per load on
the production image file across all three RNV projects. This is less
than the ">10s" figure cited in the original skip decorators, which
appears to have included pytest's instrumented-execution overhead on
top of the bare PIL work. Either way, the cost was enough to make
repeated construction impractical for the affected tests.

**Fix:** Replaced the eager load with a `background_pixmap` property:

```python
@property
def background_pixmap(self) -> QPixmap | None:
    if not self._background_image_load_attempted:
        self._background_image_load_attempted = True
        if self.theme_manager.image_mode_available:
            self._background_pixmap = self._load_background_image()
    return self._background_pixmap
```

The `_background_image_load_attempted` flag ensures one-shot semantics
— the load runs at most once per UIHandler instance, on first access
to the property, regardless of whether the load succeeded. This matches
the pre-refactor behavior where the eager load also happened at most
once at construction time.

Internal call sites (`_apply_image_mode`, `_debounced_resize`) were
updated to use `self.background_pixmap` (property) instead of
`self._background_pixmap` (private attribute). The `cleanup()` method
still nulls the private attribute since that's teardown, not access.

**Side benefit:** Production app construction is now faster for users
who never enter Image Mode — the ~2-second image work only happens when
something actually needs the pixmap. For users who never enter Image
Mode at all, the work never happens.

**Test fixes alongside the refactor:** Both `TestUIHandlerLineFill` and
`TestUIHandlerThemeChain` contained assertions that assumed "default
theme is dark." On developer machines where
`resources/background_images/background.png` exists,
`detect_image_resources()` auto-promotes the default theme to `'image'`,
so this assumption fails. Added a `monkeypatch` (per-test for one
cluster, an autouse class-level fixture for the other) that forces
`image_mode_available = False` for the affected tests, isolating their
assertions from environment state.

**Verification:** All 15 newly-enabled tests pass —
`TestUIHandlerLineFill` 5/5 in 3.45s, `TestUIHandlerThemeChain` 10/10
in 0.95s. Full pytest suite: 551 passed, 10 skipped in 4 minutes, no
regressions.

---

## Reporting new issues

If you encounter behavior not listed here, please open an issue at:
https://github.com/RNVizion/rnv-color-mixer/issues

Include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
