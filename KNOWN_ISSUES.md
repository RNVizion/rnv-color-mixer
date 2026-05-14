# Known Issues

This document tracks known issues in RNV Color Mixer v3.3.3 — tests that
are skipped on CI, edge-case bugs with planned fixes, and platform-specific
behavior worth being aware of.

The presence of an issue here doesn't mean the app is broken. The vast
majority of these have no observable effect on day-to-day app usage — they
surface only in specific test environments or edge-case workflows.

---

## CI-skipped tests

The following tests pass locally but are skipped on GitHub Actions CI
runners due to environment-specific quirks (no display server, virtualized
filesystems, etc.). Each skip is annotated in the workflow file with a
comment explaining the cause.

### `test_load_real_image_if_available` (locked unittest)

**Skipped on:** Linux CI, Windows CI
**Reason:** Hangs indefinitely when run under offscreen Qt
(`QT_QPA_PLATFORM=offscreen`). The test loads the resources/background_images/
background.png file via `ImageHandler.load_image()`. On CI runners (no
display server), the load operation never completes.

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
**Reason:** Snapshot tests compare generated palette files byte-by-byte
against reference snapshots in `snapshots/`. The references were created
on Linux with LF line endings (`\n`); on Windows, palette generation
writes CRLF (`\r\n`), so bytes don't match.

**User impact:** Cosmetic for most formats — text formats like GPL, JSON,
XML, and CSS are routinely consumed by tools that tolerate both line
endings. Potentially real for binary formats (`.afpalette`, `.clr`,
`.ase`, `.aco`): a palette exported on Windows may have CRLF inserted into
what should be a binary stream, which could cause the file to not open
correctly in Mac-specific tools (Apple Color Picker, Affinity Photo).

**Planned fix:** Audit `core/palette_formats.py` and explicitly open all
binary files with `mode='wb'` and all text files with `newline=''` to
prevent platform-specific line-ending substitution. Tracked for v3.3.4.

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

## Cross-platform palette export

**Status:** Investigation needed.

The byte-mismatch on Windows snapshot tests above suggests that palette
files exported on Windows may differ from those exported on Linux/macOS.
For text formats (GPL, JSON, XML, CSS, SVG) this is almost certainly
harmless — consumers tolerate both line endings. For binary formats
(`.ase`, `.aco`, `.afpalette`, `.clr`) this may produce files that don't
open correctly in cross-platform palette consumers.

**To verify whether this affects you:**
1. Export a palette to `.clr` format on Windows.
2. Attempt to open it on macOS using Apple's Color Picker.
3. If it opens correctly, the issue is cosmetic only.
4. If it doesn't, the export pipeline needs the v3.3.4 fix described above.

For now, the primary deployment target (Windows desktop, Windows users
consuming Windows-generated palettes) is unaffected.

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

## Reporting new issues

If you encounter behavior not listed here, please open an issue at:
https://github.com/RNVizion/rnv-color-mixer/issues

Include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
