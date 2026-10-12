"""Every action the workflows use is at a version built for the Node the runners have.

RNV-RULINGS-2026-10-05, item 14. Ruled 2026-10-05: "Yes do it".
RNV-RULINGS-2026-10-11, item 22. Ruled 2026-10-11: "A". An upload names no
hidden file.

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

AN UPLOAD NAMES NO HIDDEN FILE. upload-artifact leaves out a file or a
folder whose name begins with a dot, unless the step sets
include-hidden-files: true; its default is false, at v4 and at v6. Until
2026-10-11 three steps, in the picker and the palette manager, named only
.coverage files: they uploaded nothing, and said so to no one, since each
was told to ignore finding nothing. Ruled A: they went. The mixer's step
named .coverage beside its two reports, which it uploads; that line went.

WHAT THIS GUARD HOLDS.

1. Every `uses:` in every workflow names an action in FLOOR, at that major
   version or a later one. An action that is not in FLOOR is a new one: read
   which Node it is built for, then add it.
2. Every path an upload-artifact step names is a file or folder it can
   upload: none is hidden, unless the step includes hidden files.
3. The reader is looking. It finds the steps of every workflow, in either
   way YAML writes one, and it flags a version under the floor. It finds
   every upload step's paths, written on one line or as a block.

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
#: A path with a part whose name begins with a dot: what upload-artifact leaves out.
HIDDEN = re.compile(r"(?:^|/)\.[^./]")
UPLOAD = "actions/upload-artifact"


def _uses(text: str) -> list:
    """(line number, action, ref) for every step that uses an action."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = USES.match(line)
        if match:
            action, _, ref = match.group(1).partition("@")
            found.append((number, action, ref))
    return found


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _uploads(text: str) -> list:
    """(line number of its `uses:`, the paths it names, whether it includes
    hidden files) for every step that uses upload-artifact."""
    lines = text.splitlines()
    found = []
    for number, action, _ref in _uses(text):
        if action != UPLOAD:
            continue
        start = number - 1
        while start > 0 and not lines[start].lstrip().startswith("- "):
            start -= 1
        end = start + 1
        while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > _indent(lines[start])):
            end += 1
        step = lines[start:end]
        paths, hidden_too = [], False
        for i, line in enumerate(step):
            key, _, value = line.strip().partition(":")
            value = value.strip()
            if key == "include-hidden-files":
                hidden_too = value.strip("'\"").lower() == "true"
            elif key == "path" and value in ("|", "|-", ">", ">-"):
                block = i + 1
                while block < len(step) and (not step[block].strip() or _indent(step[block]) > _indent(line)):
                    if step[block].strip():
                        paths.append(step[block].strip())
                    block += 1
            elif key == "path":
                paths.append(value)
        found.append((number, paths, hidden_too))
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


def test_an_upload_names_no_hidden_file():
    problems = [f"{name}:{number}: {path}" for name, text in _workflows().items()
                for number, paths, hidden_too in _uploads(text) if not hidden_too
                for path in paths if HIDDEN.search(path)]
    assert not problems, (
        "upload-artifact leaves hidden files out unless the step sets include-hidden-files: "
        "true, so these upload nothing:\n  " + "\n  ".join(problems))


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

    for name, text in workflows.items():
        steps = [n for n, action, _ref in _uses(text) if action == UPLOAD]
        assert [n for n, _p, _h in _uploads(text)] == steps, f"{name}: the reader misses an upload step"
        assert all(paths for _n, paths, _h in _uploads(text)), f"{name}: the reader finds an upload with no path"
    uploads = ("    steps:\n"
               "      - name: Two reports and the data\n"
               "        # a comment\n"
               "        uses: actions/upload-artifact@v6\n"
               "        with:\n"
               "          name: coverage\n"
               "          path: |\n"
               "            htmlcov/\n"
               "            .coverage\n"
               "          retention-days: 14\n"
               "      - uses: actions/upload-artifact@v6\n"
               "        with:\n"
               "          path: reports/.hidden.txt\n"
               "          include-hidden-files: true\n"
               "      - name: One line\n"
               "        uses: actions/upload-artifact@v6\n"
               "        with: {path: dist/}\n")
    assert _uploads(uploads) == [(4, ["htmlcov/", ".coverage"], False), (11, ["reports/.hidden.txt"], True),
                                 (16, [], False)], _uploads(uploads)
    assert [p for p in ("htmlcov/", ".coverage", ".coverage.*", "reports/.hidden.txt", "./out", "../x")
            if HIDDEN.search(p)] == [".coverage", ".coverage.*", "reports/.hidden.txt"]
