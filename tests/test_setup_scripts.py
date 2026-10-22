"""THE TWO SETUP SCRIPTS SAY THE SAME THING (#82 A, 2026-10-22).

The same file in all five RNV desktop applications.

in.sh sets a Codespace up: it installs the app's packages and its test tools,
then the Linux libraries Qt needs. in.ps1 is its Windows twin. It makes a venv
here if there is none, then installs the same two files into it. Windows needs
no system libraries, because PyQt6's Windows wheel carries Qt itself.

Two scripts that say how to set a repository up drift the day one of them is
edited alone. This file holds them to the same requirements, holds in.ps1's
Python to the version CI sets up, and keeps in.ps1 in plain ASCII. Windows
PowerShell 5.1 reads a script with no byte-order mark in the machine's code
page, so a single curly quote would break it there.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH, PS1 = ROOT / "in.sh", ROOT / "in.ps1"

#: the requirements files both scripts install, in this order
FILES = ("requirements.txt", "tests/requirements-dev.txt")


def _installs(text: str) -> list[str]:
    """The -r files of every pip install the script runs, in order, with / for \\."""
    found = []
    for line in text.splitlines():
        if line.lstrip().startswith("#") or "pip" not in line or "install" not in line:
            continue
        found += [f.replace("\\", "/") for f in re.findall(r"-r\s+(\S+)", line)]
    return found


def test_both_scripts_are_here() -> None:
    assert SH.is_file() and PS1.is_file(), "in.sh and in.ps1 are each other's twin; one is missing"


def test_both_install_the_same_files() -> None:
    sh, ps1 = _installs(SH.read_text(encoding="utf-8")), _installs(PS1.read_text(encoding="utf-8"))
    assert sh == list(FILES), f"in.sh installs {sh}, not {list(FILES)}"
    assert ps1 == list(FILES), f"in.ps1 installs {ps1}, not {list(FILES)}"


def test_the_venv_is_the_python_ci_tests_on() -> None:
    ci = set()
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        ci |= set(re.findall(r"""python-version:\s*["']?(\d+\.\d+)""", wf.read_text(encoding="utf-8")))
        ci |= set(re.findall(r"""python-version:\s*\[\s*["']?(\d+\.\d+)""", wf.read_text(encoding="utf-8")))
    ps1 = PS1.read_text(encoding="utf-8")
    made = set(re.findall(r"py -(\d+\.\d+) -m venv", ps1))
    assert ci, "no python-version found in .github/workflows; the check would pass by reading nothing"
    assert made and made <= ci, f"in.ps1 makes its venv with Python {sorted(made)}; CI tests on {sorted(ci)}"


def test_in_ps1_is_plain_ascii() -> None:
    raw = PS1.read_bytes()
    bad = sorted({chr(b) for b in raw if b > 0x7f})
    assert not bad, f"in.ps1 holds non-ASCII bytes; Windows PowerShell 5.1 would misread them: {bad[:5]}"


def test_the_reader_sees_a_planted_drift() -> None:
    assert _installs("pip install -r requirements.txt -r tests/requirements-dev.txt") == list(FILES)
    assert _installs("& $p -m pip install -r requirements.txt -r tests/requirements-dev.txt") == list(FILES)
    assert _installs("pip install -r requirements.txt") != list(FILES)
