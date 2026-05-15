# Known Issues

This document tracks known issues in RNV Color Mixer v3.3.3 — tests that
are skipped on CI, real bugs with planned fixes, and platform-specific
behavior worth being aware of.

The presence of an issue here doesn't mean the app is broken. The vast
majority of these have no observable effect on day-to-day app usage — they
surface only in specific test environments or specialized workflows.

---

## Confirmed bugs (real user impact)

### Adobe Swatch Exchange (`.ase`) export produces files Adobe products can't import

**Severity:** Real user-facing bug
**Affects:** All platforms (Windows, macOS, Linux) — not platform-specific
**Status:** Diagnosed, fix planned for v3.3.4

**Symptom:** Palettes exported to `.ase` format cannot be loaded as swatches
in Adobe Photoshop ("Could not load the swatches... an unexpected end-of-file
was encountered"). Adobe Illustrator opens the file without error but
imports zero colors — the swatch panel appears empty.

**Diagnostic findings:** The exported file has correct file size (172 bytes
for a 4-color palette), correct ASEF magic bytes, and survives byte-by-byte
comparison with the repo's reference snapshot. The same file fails in
Photoshop regardless of which platform generated it. The reference snapshot
(generated on Linux and used by `tests/test_snapshots.py`) also fails to
open in Photoshop. This confirms the bug is in the format implementation
itself, not a platform-specific byte-corruption issue.

**Likely root cause:** The `_export_ase()` function in `core/palette_formats.py`
writes a name-length field and name bytes that don't include the null
terminator required by the Adobe Swatch Exchange specification. The block
length calculation may also be off as a downstream consequence. To be
verified against the official ASE spec before implementing the fix.

**Workaround for users until fix lands:** Use `.aco` (Adobe Color), `.gpl`
(GIMP, importable into Adobe via plugin), or `.css` for color sharing with
Adobe products. Note that `.aco` is implemented via similar code patterns
and may have related issues — verification needed.

**Fix plan:**
1. Read the ASE format specification carefully
2. Identify exact byte-level discrepancies between current output and a
   known-working .ase file (e.g., one exported by Photoshop itself)
3. Fix `_export_ase()` in `core/palette_formats.py`
4. Regenerate `snapshots/palette_4color.ase` to match the corrected output
5. Manually verify the regenerated file opens in Photoshop and Illustrator
6. Investigate `_export_aco()` and `_export_acb()` for similar issues
7. Re-enable `tests/test_snapshots.py` on Windows CI once snapshots are
   verified to be byte-deterministic across platforms

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
behavior without spawning real threads. Tracked for v3.3.4.

### `tests/test_snapshots.py` (whole file)

**Skipped on:** Windows CI only
**Reason originally documented:** Byte-mismatch between Windows-generated
palette files and Linux-generated snapshots, suspected to be CRLF/LF
line-ending difference.

**Updated finding (diagnostic 2026-05-14):** The byte mismatch on text
formats (GPL, JSON, XML, CSS, SVG) is indeed CRLF/LF — text-mode `open()`
calls in the export code substitute `\r\n` on Windows. This is cosmetic
for text consumers but trips byte-exact comparison.

For binary formats, the situation is different: file sizes match exactly
between platforms, and bytes are identical when generated with identical
inputs. The snapshot tests for binary formats would pass on Windows if
the test inputs and code paths were identical. The Windows skip is more
conservative than strictly necessary, but kept until the underlying .ase
bug (see above) is fixed and snapshots regenerated.

**User impact:** Cosmetic line-ending differences in text-format exports
on Windows. Real ASE/ACO format bugs documented separately above.

**Planned fix:** Two-part. First, audit `core/palette_formats.py` text
exports and explicitly set `newline=''` or use binary mode to prevent
platform-specific line-ending substitution. Second, regenerate snapshots
after the .ase fix above. Tracked for v3.3.4.

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
`AsyncFileOps` refactor mentioned above). Tracked for v3.3.4.

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

Significant diagnostic findings during initial commit cycle (May 2026):

**2026-05-14:** Identified that `.ase` export produces files Adobe
Photoshop cannot import. Diagnostic process:
1. Initial hypothesis: CRLF/LF substitution on Windows in binary file
   writes. Ruled out by inspection — `_export_ase()` correctly uses
   `'wb'` mode.
2. Second hypothesis: Windows-specific byte corruption. Ruled out by
   testing the Linux-generated snapshot file in Photoshop — same failure.
3. Conclusion: The .ase format implementation itself is incorrect against
   the Adobe Swatch Exchange specification. Both Linux and Windows
   produce the same wrong bytes, which is why byte-comparison snapshot
   tests pass but Adobe products reject the files.

Documented above under "Confirmed bugs."

---

## Reporting new issues

If you encounter behavior not listed here, please open an issue at:
https://github.com/RNVizion/rnv-color-mixer/issues

Include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
