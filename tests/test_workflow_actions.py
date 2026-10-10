"""Every action the workflows use is at a version built for the Node the runners have.

RNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".

WHAT WAS THERE. actions/checkout@v4, actions/setup-python@v5 and, where a
workflow keeps something from the run, actions/upload-artifact@v4. Each of
those declares `using: node20` in its own action.yml. GitHub took Node 20
off its hosted runners on 2026-09-23. Since then an action that declares it
is run on Node 24 instead, and the job carries a warning that names it.

WHAT IS THERE NOW. The first version of each that declares node24: checkout
v5, setup-python v6, upload-artifact v6. They are the versions the brand
repository moved its own workflows to on 2026-10-04.

READ, NOT ASSUMED. Each action's action.yml was read at both tags on
2026-10-05. Every input these workflows pass is an input of the newer
version, with the same default and the same `required`. No input the older
version had is gone from the newer one.

WHAT THIS GUARD HOLDS.

1. Every `uses:` in every workflow names an action in FLOOR, at that major
   version or a later one. An action that is not in FLOOR is a new one: read
   which Node it is built for, then add it.
2. The reader is looking. It finds the steps of every workflow, in either
   way YAML writes one, and it flags a version under the floor.

WHAT IT CANNOT HOLD. That a workflow runs. Only a run on GitHub shows that.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

#: The lowest major version of each action that declares node24.
FLOOR = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "actions/upload-artifact": 6,
}

#: Every workflow checks the repository out and sets Python up.
EVERY_WORKFLOW_USES = ("actions/checkout", "actions/setup-python")

USES = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)")
VERSION = re.compile(r"^v(\d+)(?:\.\d+)*$")


def _uses(text: str) -> list:
    """(line number, action, ref) for every step that uses an action."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = USES.match(line)
        if match:
            action, _, ref = match.group(1).partition("@")
            found.append((number, action, ref))
    return found


def _problems(name: str, text: str) -> list:
    out = []
    for number, action, ref in _uses(text):
        where = f"{name}:{number}: {action}@{ref}"
        if action not in FLOOR:
            out.append(f"{where} is not an action this guard knows. Read which Node its "
                       f"action.yml declares at that version, then add it to FLOOR.")
            continue
        version = VERSION.match(ref)
        if not version:
            out.append(f"{where} is pinned by something other than a version tag, which "
                       f"this guard cannot compare.")
        elif int(version.group(1)) < FLOOR[action]:
            out.append(f"{where} is under v{FLOOR[action]}, the first version built for "
                       f"Node 24.")
    return out


def _workflows() -> dict:
    return {path.name: path.read_text(encoding="utf-8")
            for path in sorted(WORKFLOWS.glob("*.y*ml"))}


def test_every_action_is_at_a_version_built_for_node_24():
    problems = [p for name, text in _workflows().items() for p in _problems(name, text)]
    assert not problems, (
        "GitHub's runners no longer have Node 20:\n  " + "\n  ".join(problems))


def test_the_reader_is_looking():
    """A reader that finds no step passes the test above."""
    workflows = _workflows()
    assert workflows, f"no workflow found under {WORKFLOWS}"
    for name, text in workflows.items():
        used = {action for _n, action, _ref in _uses(text)}
        missing = [a for a in EVERY_WORKFLOW_USES if a not in used]
        assert not missing, f"{name}: the reader finds no step that uses {missing}"

    sample = ("    steps:\n"
              "      - uses: actions/checkout@v4\n"
              "      - name: Python\n"
              "        uses: actions/setup-python@v6  # a comment\n"
              "      - name: Something new\n"
              "        uses: someone/something@v1\n"
              "      - name: Pinned\n"
              "        uses: actions/upload-artifact@main\n"
              "      - run: echo uses: actions/checkout@v1\n")
    assert _uses(sample) == [(2, "actions/checkout", "v4"), (4, "actions/setup-python", "v6"),
                             (6, "someone/something", "v1"), (8, "actions/upload-artifact", "main")], \
        "the reader does not find a step written as a list item, or under a name"
    flagged = _problems("sample.yml", sample)
    assert len(flagged) == 3, flagged
    assert "under v5" in flagged[0] and "not an action this guard knows" in flagged[1] \
        and "other than a version tag" in flagged[2], flagged
