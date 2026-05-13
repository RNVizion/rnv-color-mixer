"""
Unified test runner for RNV Color Mixer.

Runs both test sources under coverage with branch analysis, then merges
the data files into a single coverage report.

  Suite 1 — test_rnv_color_mixer.py    (LOCKED, 356 unittest tests, ~18 s)
  Suite 2 — tests/                     (Phase 1–6 pytest-qt + hypothesis tests, ~5 s)

Usage:
    python run_tests.py              # run everything, merge, show report
    python run_tests.py --report     # regenerate report from existing data
    python run_tests.py --summary    # report with --skip-covered (gaps only)
    python run_tests.py --no-merge   # debug: don't combine, leave both .coverage.* files

Exit code is non-zero if either suite has failures.

Notes
-----
Coverage configuration (source dirs, branch mode, omit patterns) is read
from `.coveragerc` at the project root. We pass `--branch` explicitly here
too as a safety net in case the rc file is missing or modified.

Unlike the original RNV Color Picker version of this runner, the main
`RNV_Color_Mixer.py` file IS included in coverage measurement here:
Phase 4 landed app-level integration tests for it (currently at ~41%
coverage).
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# `.coveragerc` at the root specifies source=. and the omit patterns.
# We pass --branch on the command line as a defensive duplicate so this
# runner works even if .coveragerc is somehow missing or overridden.
COVERAGE_BRANCH = "--branch"

# Per-suite coverage data files so the two suites don't overwrite each
# other before `coverage combine` merges them into the canonical .coverage.
UNITTEST_DATA = ".coverage.unittest"
PYTEST_DATA = ".coverage.pytest"

# Headless Qt is non-negotiable on CI / no-display dev machines.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _run(label, cmd):
    """Run a subprocess, stream its output, return its exit code."""
    print()
    print("=" * 72)
    print(f"  {label}")
    print("=" * 72)
    print(f"  $ {' '.join(cmd)}")
    print()
    return subprocess.call(cmd, cwd=ROOT)


def run_unittest_suite():
    """Suite 1: locked root-level test file under unittest.

    Loads as a module name (no .py extension), per unittest convention.
    """
    return _run(
        "Suite 1 / 2 — unittest (test_rnv_color_mixer.py)",
        ["coverage", "run",
         f"--data-file={UNITTEST_DATA}",
         COVERAGE_BRANCH,
         "-m", "unittest", "test_rnv_color_mixer"],
    )


def run_pytest_suite():
    """Suite 2: every test_*.py under /tests/ — Phases 1–6."""
    if not (ROOT / "tests").is_dir():
        print("\n[skip] tests/ directory not found — pytest suite skipped.")
        return 0
    return _run(
        "Suite 2 / 2 — pytest (tests/)",
        ["coverage", "run",
         f"--data-file={PYTEST_DATA}",
         COVERAGE_BRANCH,
         "-m", "pytest", "tests/", "-v"],
    )


def merge_data_files():
    """Combine the two per-suite .coverage.* files into the canonical .coverage.

    `coverage combine` deletes the input files after a successful merge,
    so the canonical .coverage ends up with the union of both runs.
    """
    parts = [p for p in (UNITTEST_DATA, PYTEST_DATA) if (ROOT / p).exists()]
    if not parts:
        print("\n[error] no coverage data files found — cannot merge.")
        return 1
    return subprocess.call(["coverage", "combine", *parts], cwd=ROOT)


def print_report(summary=False):
    """Print the combined coverage report. `summary=True` hides 100%-covered files.

    Always also writes the full report to `coverage_report.txt` for archiving.
    """
    print()
    print("=" * 72)
    print("  Coverage report" + ("  (--skip-covered)" if summary else ""))
    print("=" * 72)
    cmd = ["coverage", "report", "-m"]
    if summary:
        cmd.append("--skip-covered")
    rc = subprocess.call(cmd, cwd=ROOT)
    with open(ROOT / "coverage_report.txt", "w", encoding="utf-8") as f:
        subprocess.call(["coverage", "report", "-m"], cwd=ROOT, stdout=f)
    # Also generate the browsable HTML report
    subprocess.call(["coverage", "html"], cwd=ROOT)
    return rc


def main():
    args = set(sys.argv[1:])
    summary = "--summary" in args

    # Report-only mode: skip both suites, just regenerate from existing data.
    if "--report" in args:
        return print_report(summary=summary)

    rc1 = run_unittest_suite()
    rc2 = run_pytest_suite()

    if "--no-merge" not in args:
        merge_data_files()
        print_report(summary=summary)

    # Non-zero exit if either suite failed — useful for CI gates.
    return max(rc1, rc2)


if __name__ == "__main__":
    sys.exit(main())
