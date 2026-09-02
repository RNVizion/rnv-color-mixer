"""The locked test file and the digest that gates it must agree.

RNV-LOCKED-DIGEST-GUARD

test_rnv_color_mixer.py is the gate of last resort, and CI refuses the build if
its SHA-256 moves. That check lives only in the two workflow files, so until
now the first thing to notice a legitimate edit was a red build on GitHub --
after the commit, after the push, and with a message that reads like tampering
rather than like a re-baseline that was forgotten.

These tests move that check into the suite, where it fires in the same run as
the edit that caused it, and they check something CI cannot: that the two
workflows still record the SAME digest.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCKED = ROOT / "test_rnv_color_mixer.py"
WORKFLOWS = (ROOT / ".github" / "workflows" / "tests-linux.yml",
             ROOT / ".github" / "workflows" / "tests-windows.yml")

_SHA256 = re.compile(r"\b([0-9a-f]{64})\b")


def _recorded(path: Path) -> list[str]:
    return _SHA256.findall(path.read_text(encoding="utf-8"))


def test_every_workflow_records_exactly_one_digest():
    for path in WORKFLOWS:
        found = _recorded(path)
        assert len(found) == 1, (
            f"{path.name} records {len(found)} SHA-256 values: {found}. This "
            f"guard reads the digest by shape, so a second one would make it "
            f"ambiguous which gate it is checking.")


def test_both_workflows_record_the_same_digest():
    """CI cannot catch this. Each workflow checks only its own copy, so the
    two can drift apart and both builds still pass -- until one platform
    re-baselines and the other does not."""
    digests = {path.name: _recorded(path)[0] for path in WORKFLOWS}
    assert len(set(digests.values())) == 1, (
        f"the workflows disagree about the locked file's digest: {digests}")


def test_the_locked_file_matches_its_recorded_digest():
    actual = hashlib.sha256(LOCKED.read_bytes()).hexdigest()
    expected = _recorded(WORKFLOWS[0])[0]
    assert actual == expected, (
        "test_rnv_color_mixer.py no longer matches the digest the workflows "
        "gate on.\n"
        f"  recorded: {expected}\n"
        f"  actual:   {actual}\n"
        "If the edit was deliberate, re-baseline BOTH workflow files to the "
        "actual value in the same commit. If it was not, this is the gate "
        "doing its job.")


def test_the_digest_is_read_from_the_file_and_not_from_this_test():
    """A guard that carried its own copy of the digest would pass while the
    workflows were wrong, which is the failure it exists to prevent."""
    source = Path(__file__).read_text(encoding="utf-8")
    assert not _SHA256.search(source), (
        "this test module contains a literal SHA-256. The digest must come "
        "from the workflow files, or this guard is checking itself.")
