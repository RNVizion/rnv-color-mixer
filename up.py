"""The mixer: launching adds nothing to the history (ruling 103 A)

Run it from the root of your rnv-color-mixer checkout, at the live head (7a88826), with
that repository's venv active. The script itself can live anywhere; it works on
the folder you run it from.

    python <path to this script> --check     # rehearse in memory, write nothing
    python <path to this script>             # apply, then run the guards and CI's commands
    python <path to this script> --verify    # run the guards and CI's commands, change nothing

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP. This
script is a delivery tool, not application source; those markers tell this
fleet's scanners to skip it, should it be saved inside a checkout as up.py.
It quotes old text in order to replace it, retired key names included.

RULED 2026-10-27, 103 A: the history records only the mixes that follow
something the user did. The mix the app makes as it starts, and a session's
restored at startup (the recovery offer, or Auto-load last session), are
shown and not recorded: every launch had added the default slots' gray, so
the History tab's empty line was never seen. RNV_Color_Mixer.py marks a
change made while the app starts or restores as scheduling a quiet mix; a
change after that is the user's, and its mix is recorded as before.
tests/test_history_records_the_users_mixes.py holds it, and four of its five
tests fail without the change. README and CHANGELOG say so, and the History
test's helper names the ruling. It starts from 7a88826, where the harmony
fix (102 A) and the timer fix landed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import tokenize
import types
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'record=not quiet'
SENTINEL_FILE = 'RNV_Color_Mixer.py'
EARLIER = []
GUARD = 'tests/test_atomic_state_writes.py'
GUARD_FILES = ['tests/test_atomic_state_writes.py', 'tests/test_readme_test_counts.py', 'tests/test_dependency_file_placement.py', 'tests/test_dependency_coherence.py', 'tests/test_colors_in_sync.py', 'tests/test_setup_scripts.py', 'tests/test_workflow_actions.py', 'tests/test_status_carried_by_a_word.py', 'tests/test_no_vacuous_tests.py', 'tests/test_color_values.py', 'tests/test_history_records_the_users_mixes.py']
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *GUARD_FILES]
DESCRIPTION = "The mixer: launching adds nothing to the history (ruling 103 A)"

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = 'ec45a92e92ffa1179b36bf4fe9a37727983b2fb31b7b704448e9fb1c4a75ad1b'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
#: THIS SCRIPT IS LEFT OUT OF THE MEASURE. .coveragerc measures every file in
#: the checkout, run or not, and while this file is in it this file is one:
#: several hundred statements at 0%. CI never sees it, so counting it measured
#: something CI does not, and a long script could fall under the floor on its
#: own weight. Measured 2026-10-04: 69.6 with a 1,030-line script, 73.4 without.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69', '--omit=' + sys.argv[1]])\n"
          "if r.returncode == 2:\n"
          "    raise AssertionError('coverage is under the Linux CI floor of 69')\n"
          "sys.exit(r.returncode)\n")
SUITES = [
    ("CI: locked file integrity", [sys.executable, "-c", _LOCK]),
    ("CI: pytest test_rnv_color_mixer.py under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.unittest",
      "--branch", "-m", "pytest", "test_rnv_color_mixer.py", "-v"]),
    ("CI: pytest tests/ under coverage",
     [sys.executable, "-m", "coverage", "run", "--data-file=.coverage.pytest",
      "--branch", "-m", "pytest", "tests/", "-v"]),
    ("CI: coverage combine",
     [sys.executable, "-m", "coverage", "combine", ".coverage.unittest",
      ".coverage.pytest"]),
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR, Path(__file__).name]),
]

#: The workflows SUITES mirrors, by content hash, as this round leaves them.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '5205e7bd1d447ebe3fc5cb389a02da6d33ef28976a0bdc90ed797069be2ee81a', '.github/workflows/tests-windows.yml': '266a88f9893da598d8ce08dfca63293a6e2f92d4e7f9fc2b316507a282a4a737'}

SHADOWS = ['colors.py', 'conftest.py', 'run_tests.py', 'sync_colors.py', 'test_colors_in_sync.py', 'test_register_pin.py', 'test_rnv_color_mixer.py']

LEFT_ALONE = ['every image and every image path, every color value, and the pin.',
              'every color and every alpha: this round changes what the history records, nothing it shows.',
              'every mix the user makes: it is recorded as before, with Enable color history on.',
              'every feature: none is removed.']

# ======================================================================== this round

#: sha256 of each file the round edits, as the live head holds it
BASE_SHAS = {'CHANGELOG.md': 'e2c382b07670c90e896bffdda2684eeb02c0cd75d5b3337667f5af3d96df19d9', 'README.md': '5f10a883176bf6e66527fe6b65317dcb461b9865c5e31b97afb9ab809d7f2ccf', 'RNV_Color_Mixer.py': 'ada3a59aad7b31e2bc696d1fc01d5a678554d15fd15fef0b340da20a3bedb452', 'tests/test_empty_history_line_draws.py': '2be44990062eacac3bf9e3582951fc75cbe2f8c5d0b79ac7b21dd7300d873893'}

#: (file, anchor, replacement), applied in order; each anchor is found exactly once
SUBS = [('CHANGELOG.md', "\n- **The harmony description reads in Light mode.** Its text, the panel's dark gold, sat on a\n", "\n- **Launching no longer adds to the color history.** As it started, the app mixed its slots\n  and recorded the mix as if you had made it: every launch added the default slots' gray,\n  so the History tab's *No color history yet* line was never seen, and a session restored at\n  startup (recovered, or auto-loaded) was recorded a second time. Now the history records\n  only the mixes that follow something you did.\n- **The harmony description reads in Light mode.** Its text, the panel's dark gold, sat on a\n"), ('README.md', '  1 to 1000): click one to load it into an empty slot, or export the history\n  as JSON, HTML, or text. With Enable color history off, mixes are not added\n\n', "  1 to 1000): click one to load it into an empty slot, or export the history\n  as JSON, HTML, or text. With Enable color history off, mixes are not added.\n  Only your mixes are added: not the mix the app makes as it starts, nor a\n  session's restored at startup, which the history holds from when it was made\n\n"), ('RNV_Color_Mixer.py', '            self._mix_debounce_timer.timeout.connect(self._debounced_mix_colors)\n            \n', "            self._mix_debounce_timer.timeout.connect(self._debounced_mix_colors)\n\n            # Ruling 103 A (2026-10-27): the history records the mixes that\n            # follow something the user did. The app mixes its slots as it\n            # starts, and again when it restores a session at startup (the\n            # crash-recovery offer, or Auto-load last session); those mixes\n            # are not the user's, and every launch added the default slots'\n            # gray. A change made while _starting or _restoring_at_startup\n            # marks the mix it schedules as quiet (on_slot_change).\n            self._starting = True\n            self._restoring_at_startup = False\n            self._quiet_mix = False\n            \n"), ('RNV_Color_Mixer.py', '            \n            logger.success("ColorMixerApp initialization completed successfully")\n', '            \n            self._starting = False                        # ruling 103 A: the user\'s changes from here\n            logger.success("ColorMixerApp initialization completed successfully")\n'), ('RNV_Color_Mixer.py', '        """\n        if self._check_crash_recovery():\n            return\n        self._auto_load_last_session()\n\n', '        """\n        # Ruling 103 A: what this restores is not mixed by the user now. The\n        # history already holds those mixes, from when they were made.\n        self._restoring_at_startup = True\n        try:\n            if self._check_crash_recovery():\n                return\n            self._auto_load_last_session()\n        finally:\n            self._restoring_at_startup = False\n\n'), ('RNV_Color_Mixer.py', '            \n            # Update mixed color\n            self.auto_mix_colors()\n            \n', '            \n            # Update mixed color (ruling 103 A: not recorded when restored at startup)\n            self.auto_mix_colors(record=not self._restoring_at_startup)\n            \n'), ('RNV_Color_Mixer.py', '        def handle_change() -> None:\n            # Debounce color mixing - only recalculate after 100ms of no changes\n', "        def handle_change() -> None:\n            # Ruling 103 A: a change made while the app starts or restores a\n            # session at startup schedules a mix the history does not record;\n            # a change after that, the user's, schedules one it does.\n            self._quiet_mix = bool(getattr(self, '_starting', False)\n                                   or getattr(self, '_restoring_at_startup', False))\n            # Debounce color mixing - only recalculate after 100ms of no changes\n"), ('RNV_Color_Mixer.py', '        """Debounced color mixing - called after slider stops moving."""\n        ErrorHandler.safe_execute(lambda: self.auto_mix_colors(), "debounced color mixing", print)\n\n    def auto_mix_colors(self) -> None:\n        """Mix colors safely with caching."""\n        def mix_colors() -> None:\n', '        """Debounced color mixing - called after slider stops moving."""\n        quiet, self._quiet_mix = getattr(self, \'_quiet_mix\', False), False\n        ErrorHandler.safe_execute(lambda: self.auto_mix_colors(record=not quiet), "debounced color mixing", print)\n\n    def auto_mix_colors(self, record: bool = True) -> None:\n        """Mix colors safely with caching.\n\n        Args:\n            record: False for a mix the user did not make (ruling 103 A): the\n                one the app makes as it starts, and a session\'s restored at\n                startup. It is shown, and not added to the history.\n        """\n        def mix_colors() -> None:\n'), ('RNV_Color_Mixer.py', '                \n                if should_auto_save and self.color_history and mixed_color != (0, 0, 0):\n                    self.color_history.add_color(mixed_color)\n', '                \n                if record and should_auto_save and self.color_history and mixed_color != (0, 0, 0):\n                    self.color_history.add_color(mixed_color)\n'), ('tests/test_empty_history_line_draws.py', '    Chris\'s Windows run of 27 October; a run on a slower machine had always\n    let it land first.\n    """\n', '    Chris\'s Windows run of 27 October; a run on a slower machine had always\n    let it land first. Ruling 103 A (the same day) stopped the history from\n    recording that mix at all (tests/test_history_records_the_users_mixes.py);\n    the wait stays, so no mix pending at the clear can land after it.\n    """\n')]

#: files the round adds, whole
NEW_FILES = {'tests/test_history_records_the_users_mixes.py': '"""The history records the mixes that follow something the user did.\n\nRuling 103 A, 2026-10-27.\n\nWHAT WAS THERE. As it starts, the app mixes its slots: the mix debounce\n(100 ms) runs once on the slots it has just built, and the mix went into the\nhistory as if the user had made it. Every launch added the default slots\'\ngray. Three launches in a fresh home left three entries of it, so the History\ntab\'s empty line was never seen in use, and the history filled with a color\nnobody mixed. A session restored at startup was recorded again the same way:\nthe crash-recovery offer answered Yes, or Auto-load last session. Its mixes\nare in the history already, from when they were made. Found on 27 October,\nfrom a test race on Chris\'s Windows run (tests/test_empty_history_line_draws.py).\n\nWHAT IS THERE NOW. A change made while the app starts, or while it restores a\nsession at startup, schedules a mix the history does not record. A change\nafter that is the user\'s, and its mix is recorded, as before, when Enable\ncolor history and Auto-save mixed colors are on.\n\nEach test launches the app the way a person does, in a home of its own\n(tests/conftest.py, isolated_home).\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtWidgets import QMessageBox\n\nfrom tests.test_settings_that_act import (SESSION_SLOTS, _launch, _record_session,\n                                          _slot_state, _write_settings)\n\npytestmark = pytest.mark.integration\n\n#: Long enough for everything a launch schedules: the mix debounce (100 ms)\n#: and the startup restore (500 ms).\nSETTLE_MS = 900\n\n#: A color a user picks, and its slot weight.\nPICKED = ((40, 90, 200), 60)\n\n\ndef _entries(win) -> list:\n    return [tuple(e.color) for e in win.color_history.get_entries()]\n\n\n@pytest.fixture\ndef answer_yes(monkeypatch):\n    """Answer every question Yes, and every notice OK. Record the titles."""\n    shown: list[str] = []\n\n    def box(answer):\n        def show(parent, title, *args, **kwargs):\n            shown.append(title)\n            return answer\n        return staticmethod(show)\n\n    monkeypatch.setattr(QMessageBox, "question", box(QMessageBox.StandardButton.Yes))\n    monkeypatch.setattr(QMessageBox, "information", box(0))\n    monkeypatch.setattr(QMessageBox, "warning", box(0))\n    return shown\n\n\ndef test_launches_add_nothing_to_the_history(isolated_home, qtbot, main_module):\n    first = _launch(main_module, qtbot, wait_ms=SETTLE_MS)\n    assert first.current_mixed_color, "the launch mixed nothing: nothing was tested"\n    assert _entries(first) == [], f"the first launch recorded {_entries(first)}"\n    first.close()\n    second = _launch(main_module, qtbot, wait_ms=SETTLE_MS)\n    try:\n        assert _entries(second) == [], f"two launches left {_entries(second)} in the history"\n    finally:\n        second.close()\n\n\ndef test_a_session_auto_loaded_at_startup_is_not_recorded(isolated_home, qtbot, main_module, answer_yes):\n    _record_session(isolated_home)\n    _write_settings(isolated_home, preferences={"auto_load_last_session": True})\n    win = _launch(main_module, qtbot, wait_ms=SETTLE_MS)\n    try:\n        assert _slot_state(win) == SESSION_SLOTS, "the session was not loaded: nothing was tested"\n        assert _entries(win) == [], f"the auto-loaded session\'s mix was recorded: {_entries(win)}"\n    finally:\n        win.close()\n\n\ndef test_a_session_recovered_at_startup_is_not_recorded_again(isolated_home, qtbot, main_module,\n                                                               answer_yes):\n    """A run ends without closing, holding a mix the user made; the next launch\n    offers recovery, answered Yes. The recovered mix is shown and not added:\n    the history recorded it when it was made. (Each launch here starts with\n    a history of its own, tests/conftest.py, so the second launch\'s history\n    is compared before and after the recovery.)"""\n    first = _launch(main_module, qtbot, wait_ms=SETTLE_MS)\n    first.slots[0].set_color(PICKED[0])\n    first.slots[0].set_weight(PICKED[1])\n    qtbot.wait(400)\n    assert len(_entries(first)) == 1, f"the user\'s mix was not recorded: {_entries(first)}"\n    first.session_manager._autosave()            # what the 60 s timer does\n    # The process dies here: no closeEvent, so the recovery flag stays.\n    second = _launch(main_module, qtbot)\n    before = _entries(second)\n    qtbot.wait(SETTLE_MS)\n    try:\n        assert "Recover Previous Session?" in answer_yes, "no recovery was offered: nothing was tested"\n        assert second.current_mixed_color == first.current_mixed_color, "the session was not recovered"\n        assert _entries(second) == before, f"the recovered mix was recorded again: {_entries(second)}"\n    finally:\n        second.close()\n        first.close()\n\n\ndef test_a_change_after_the_launch_is_recorded(isolated_home, qtbot, main_module):\n    win = _launch(main_module, qtbot, wait_ms=SETTLE_MS)\n    try:\n        win.slots[0].set_color(PICKED[0])\n        qtbot.wait(400)\n        assert len(_entries(win)) == 1, f"the user\'s change was not recorded: {_entries(win)}"\n    finally:\n        win.close()\n\n\ndef test_a_change_while_the_startup_mix_is_pending_is_recorded(isolated_home, qtbot, main_module):\n    """The user\'s change wins over the quiet startup mix it overtakes: the one\n    mix that runs follows something the user did."""\n    win = _launch(main_module, qtbot)\n    try:\n        assert win._mix_debounce_timer.isActive(), "the startup mix already ran: nothing was tested"\n        win.slots[0].set_color(PICKED[0])\n        qtbot.wait(SETTLE_MS)\n        assert len(_entries(win)) == 1, f"the user\'s change was not recorded: {_entries(win)}"\n    finally:\n        win.close()\n'}

#: sha256 of every file as this round writes it
WANT = {'CHANGELOG.md': 'aee8ac8abb5f65be1ac9c1c6932a4b8b7c6fff50567f2442114f3ed02f5c7f11', 'README.md': '73013676c7b88a8971eb8813713fdb63322c1906267f565db1d68f1270f6f86c', 'RNV_Color_Mixer.py': '383810e9a30e77cb2952fabe9cd075b2cbe2024c7d763db6149c53db19fc8008', 'tests/test_empty_history_line_draws.py': 'dab640a42d31c2c109b7767f1f4032f309ac7da046270992dc83722e819b8af9', 'tests/test_history_records_the_users_mixes.py': 'aa26d316bd523f41c25715469b03741cda8841fd840450906d7c711164351985'}

#: scripts git should record as executable (#91 A)
EXECUTABLE = []


def edits(tree) -> None:
    for rel, mark in EARLIER:
        if (tree.root / rel).exists() and mark in tree.read(rel):
            raise Stop(f"{rel} already holds {mark}: up_tt_ci_time.py, which this script carries, "
                       f"has run here. Nothing was written. If that run is not committed, put the checkout "
                       f"back (git restore .) and run this script alone; if it is committed, ask for this "
                       f"script to be derived again.", EXIT_CANNOT_RUN)
    for rel, was in BASE_SHAS.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        if got != was:
            raise Stop(f"{rel} is not the live head's file this round was derived from ({got[:12]}). "
                       f"Nothing was written. Pull, or ask for the script to be re-derived.",
                       EXIT_CANNOT_RUN)
    for rel in NEW_FILES:
        if (tree.root / rel).exists():
            raise Stop(f"{rel} exists already; this round adds it. Nothing was written.", EXIT_CANNOT_RUN)
    for rel, old, new in SUBS:
        tree.sub(rel, old, new)
    for rel, text in NEW_FILES.items():
        tree.write(rel, text)


def checks(tree) -> None:
    extra_reads = {rel for rel, _ in EARLIER}
    assert set(tree.files) - extra_reads == set(WANT) - extra_reads, f"this round writes {sorted(tree.files)}"
    assert not tree.deleted, f"this round deletes {sorted(tree.deleted)}"
    british = re.compile(r"\b(colour|grey|behaviour|centre|organis|favourite|licence\b)", re.I)
    for rel in WANT:
        if rel.endswith(".md"):
            hit = british.search(tree.read(rel))
            assert hit is None, f"{rel}: British spelling {hit.group(0)!r}"
    assert "HARMONY_DESCRIPTION_ALPHA: Final[int] = 0x10" in tree.read("utils/colors.py")
    assert "record=not quiet" in tree.read("RNV_Color_Mixer.py"), "the startup mix is still recorded"
    for rel, want in WANT.items():
        got = hashlib.sha256(tree.read(rel).encode("utf-8")).hexdigest()
        assert got == want, f"{rel} is not the file this round writes: {got[:12]}"


def _set_executable() -> None:
    """#91 A. The file's mode where the file system has one, and git's index either way."""
    for rel in EXECUTABLE:
        p = Path.cwd() / rel
        if not p.exists():
            continue
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        r = subprocess.run(["git", "update-index", "--chmod=+x", "--", rel], capture_output=True, text=True)
        if r.returncode != 0:
            raise Stop(f"git could not mark {rel} executable: {r.stderr.strip()}", EXIT_INCOMPLETE)
    if EXECUTABLE:
        print("marked executable in git: " + ", ".join(EXECUTABLE))


_ci_post_write = globals().get("post_write")


def post_write() -> None:
    _set_executable()
    if _ci_post_write is not None:
        _ci_post_write()

def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalized the way Tree.read() normalizes it."""
    raw = (tree.root / rel).read_bytes()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("utf-8")
    crlf = text.count("\r\n")
    if crlf and crlf == text.count("\n"):
        text = text.replace("\r\n", "\n")
    return text


def _function(src: str, name: str, cls: str | None = None):
    """The named function, at module level or inside the named class."""
    body = ast.parse(src).body
    if cls is not None:
        body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == cls).body
    return next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)


def _top(src: str) -> dict:
    """Module-level NAME -> ast.dump of the value it is assigned."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            t = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(t, ast.Name):
                out[t.id] = ast.dump(node.value)
    return out


def _entries(node) -> dict:
    """A dict display's literal keys -> ast.dump of each value; ** spreads
    under their own ast.dump, so a moved spread is seen too."""
    return {(k.value if k is not None else "**" + ast.dump(v)): ast.dump(v)
             for k, v in zip(node.keys, node.values)}


def _sheet_parts(call) -> list:
    """The literal text of a setStyleSheet(f"...") call, the parts between
    its placeholders, in order."""
    arg = call.args[0]
    assert isinstance(arg, ast.JoinedStr), ast.unparse(arg)[:80]
    return [v.value for v in arg.values if isinstance(v, ast.Constant)]


def _calls(fn, attr: str) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call)
            and getattr(c.func, "attr", getattr(c.func, "id", None)) == attr]


# ------------------------------------------------------------------ plumbing
#
# EXIT CODES ARE A TAXONOMY, NOT A BOOLEAN. Rev 6 §3.0.1. A harness that
# returns non-zero for everything tells the operator something is wrong and
# nothing about what, and the three non-zero cases want three different
# actions: read the diff, install something, re-run.
EXIT_CLEAN = 0       # everything agreed
EXIT_DISAGREES = 1   # something ran and disagreed -- read it
EXIT_CANNOT_RUN = 2  # the environment is not ready -- nothing was asked
EXIT_INCOMPLETE = 3  # it ran and did not finish -- re-run before believing it


class Stop(SystemExit):
    """A refusal this script chose, as opposed to a crash.

    Carries an exit code from the taxonomy. Bare SystemExit('message') exits 1,
    which says A TEST DISAGREED -- so every refusal used to arrive wearing the
    one verdict it was not.
    """

    def __init__(self, message: str, code: int = EXIT_CANNOT_RUN) -> None:
        super().__init__(message)
        self.code = code


#: Two files per repository that exist there and in none of the others.
#: Verified against the live fleet by _fingerprint_check.py at build time,
#: because a fingerprint that has been renamed away identifies nothing and
#: would refuse every correct checkout.
FINGERPRINTS = {
    "rnv-color-mixer": ("core/image_handler.py", "ui/canvas_view.py"),
    "rnv-color-palette-manager": ("core/color_extractor.py",
                                  "ui/batch_export_dialog.py"),
    "rnv-color-picker": ("core/hilbert_curve.py", "ui/color_swatch_widget.py"),
    "rnv-icon-builder": ("core/icon_builder_core.py", "core/project_manager.py"),
    "rnv-text-transformer": ("core/diff_engine.py", "core/text_cleaner.py"),
}


def refuse_wrong_repository(root) -> None:
    """Refuse a checkout that is not the repository this script was built for.

    CALLED FIRST IN apply(), BEFORE THE SENTINEL AND BEFORE ANY ANCHOR, and the
    order is the whole point. The five applications share file names -- four of
    them have a utils/config.py or a ui/colors.py, and several share a
    tests/conftest.py. Run in the wrong sibling, a sentinel check says "already
    applied" or "not a checkout" and an anchor check says "the file moved",
    and BOTH of those are the script guessing at the wrong question.

    A fingerprint is a file only the right repository has. Two, because one
    that gets renamed takes the check with it.
    """
    want = FINGERPRINTS.get(REPO)
    if not want:
        return
    missing = [f for f in want if not (root / f).exists()]
    if missing:
        raise Stop(
            f"this is not a {REPO} checkout.\n"
            f"  expected to find: {', '.join(want)}\n"
            f"  missing here:     {', '.join(missing)}\n"
            f"Run it from the root of {REPO}. Nothing was read or written.",
            EXIT_CANNOT_RUN)


def _left_alone() -> None:
    """Print what this round deliberately did not touch.

    LEFT_ALONE is optional and is prose, not a guard. It exists because a
    reader of a diff can see what changed and cannot see what was considered
    and declined, and the second is where a round's scope actually lives.
    """
    items = globals().get("LEFT_ALONE")
    if not items:
        return
    print("\nleft alone, deliberately:")
    for line in items:
        print(f"  - {line}")


def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        raise Stop(f"refusing to run as {name} -- it would shadow a module on "
                   f"sys.path. Rename to up.py and run again.", EXIT_CANNOT_RUN)


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        self.deleted: set[str] = set()
        #: rel -> (had a BOM, line endings were CRLF throughout). What a file
        #: was on disk, so flush() can put back exactly that around the edit.
        self.form: dict[str, tuple[bool, bool]] = {}

    def read(self, rel: str) -> str:
        """The file as text with LF line endings, whatever it is on disk.

        A FILE IS ITS BYTES, AND AN EDIT MUST NOT CHANGE THE ONES IT DID NOT
        MEAN TO. This used to read with read_text('utf-8-sig') and flush with
        encode('utf-8'). The first strips a byte-order mark and folds CRLF to
        LF; the second puts neither back. So a one-line edit to a CRLF file
        rewrote every line ending in it, and any edit to a file with a BOM
        deleted its first three bytes. rnv-color-picker's utils/config.py --
        the picker's palette -- carries a BOM, so its next round would have.

        Anchors are written with \\n, so a CRLF file is held as LF in memory
        and its endings are restored on write. A file that MIXES endings is
        held exactly as it is: anchors then match only its LF lines, and
        everything else round-trips untouched.
        """
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise Stop(f"missing file: {rel}", EXIT_CANNOT_RUN)
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            text = (raw[3:] if bom else raw).decode("utf-8")
            crlf = text.count("\r\n")
            all_crlf = crlf > 0 and crlf == text.count("\n")
            if all_crlf:
                text = text.replace("\r\n", "\n")
            self.files[rel] = text
            self.form[rel] = (bom, all_crlf)
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def delete(self, rel: str) -> None:
        """Mark a file for removal. Nothing leaves disk until flush()."""
        if not (self.root / rel).exists() and rel not in self.files:
            raise Stop(f"cannot delete {rel}: it is not in this checkout",
                       EXIT_CANNOT_RUN)
        self.files.pop(rel, None)
        self.deleted.add(rel)

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise Stop(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.", EXIT_CANNOT_RUN)
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        """Compare and write BYTES, not decoded text.

        read_text('utf-8') here raised on a file that was not valid UTF-8 --
        which is precisely the file some scripts exist to fix. Bytes compare
        identically for everything else and cannot refuse to look."""
        touched = []
        for rel in sorted(self.deleted):
            p = self.root / rel
            if p.exists():
                p.unlink()
                touched.append(f"{rel} (deleted)")
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = self.encode(rel, text)
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
                touched.append(rel)
        return touched

    def encode(self, rel: str, text: str) -> bytes:
        """Text back to bytes in the form the file had when it was read.

        A file never read -- one this script creates -- has no form to keep
        and is written as plain UTF-8 with LF, which is what every file in
        this fleet is unless it says otherwise.
        """
        bom, all_crlf = self.form.get(rel, (False, False))
        if all_crlf:
            text = text.replace("\n", "\r\n")
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort", "killed" or "env" -- only exit code 1 means a
    test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (-9, 137, -15, 143):
        return "killed"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        # EXIT 1 IS NOT ALWAYS A TEST DISAGREEING, and this used to assume it
        # was. A missing pytest PLUGIN or a missing pinned package does not
        # stop collection -- the tests are found, then fail at setup -- so
        # pytest exits 1, the same code a real regression gives.
        #
        # It shipped that way. A fresh Codespace with the app requirements and
        # none of tests/requirements-dev.txt ran a round that had landed
        # cleanly and got 85 errors ("fixture 'qtbot' not found": pytest-qt)
        # and 3 failures ("No module named 'engine'": the rnv-brand pin), and
        # the verdict was "FAILED -- the suite is not green". Not one of the 88
        # was the change disagreeing with anything.
        #
        # The discriminator is the assertion. A regression raises
        # AssertionError; a missing dependency raises nothing of the kind. If
        # the run carries environment signatures and NO assertion failure, it
        # is the environment. If it carries both, it is a failure -- the
        # conservative direction, because under-reporting a real regression is
        # the one way this verdict must never be wrong.
        if _missing_dependency(out) and not _ASSERTION.search(out):
            return "env"
        return "fail"
    return "env"


#: A dependency that is not installed, as pytest reports it. Each of these
#: arrived in a real run of this fleet's suites.
_ENV_SIGNS = (
    re.compile(r"fixture '\w+' not found"),                 # a pytest plugin
    re.compile(r"ModuleNotFoundError: No module named"),    # a package
    re.compile(r"\bis not importable\b"),                   # the register pin
    re.compile(r"ImportError: lib[\w.+-]+\.so"),            # a system library
)
#: A real regression. pytest prints the failing line under `E   ` and the
#: exception class in the summary.
_ASSERTION = re.compile(r"^E\s+assert\b|\bAssertionError\b", re.M)


def _missing_dependency(out: str) -> bool:
    return any(sign.search(out) for sign in _ENV_SIGNS)


#: verdict -> taxonomy. "abort" and "killed" are EXIT_INCOMPLETE rather than
#: EXIT_CANNOT_RUN: the environment WAS ready and the run started, which is a
#: different instruction to the operator -- re-run, do not go installing things.
_VERDICT_CODE = {
    "pass": EXIT_CLEAN,
    "fail": EXIT_DISAGREES,
    "env": EXIT_CANNOT_RUN,
    "abort": EXIT_INCOMPLETE,
    "killed": EXIT_INCOMPLETE,
}


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""

KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    # WINDOWS (2026-10-22). A child writing to a file, not a console, encodes
    # in the locale's code page there (cp1252), and a test that prints an
    # emoji -- the mixer's logger does -- raises in the child. UTF-8 is what
    # this temp file is read as, and what CI's Linux runners already use.
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return _VERDICT_CODE[verdict]


def verify() -> int:
    # A script that changes the ENVIRONMENT its suites run in does it here,
    # not in checks(): checks() runs against the in-memory tree before
    # anything is on disk. The register pin is the case that needed it -- it
    # writes a dependency line and then runs tests that import what the line
    # declares, and DECLARING IS NOT INSTALLING.
    #
    # In verify() rather than apply() so that `--verify` gets it too; that is
    # the entry point someone uses to re-check a repository, and it has to
    # prepare the same environment.
    hook = globals().get("post_write")
    if hook is not None:
        hook()
        print()

    # GUARD_CMD is OPTIONAL and exists for a repository with no pytest. Every
    # round until 2026-09-12 ran inside one of the five applications, where a
    # guard is a test file; rnv-brand has no tests directory, no pytest
    # dependency, and a deliberate ZERO-IMPORT policy in engine/brand.py --
    # its own idiom is a function that runs AT IMPORT and raises. Installing
    # pytest there to satisfy this harness would change the shape of someone
    # else's repository to suit a tool, which is backwards. GUARD still names
    # the file that holds the check; GUARD_CMD says how to run it.
    guard_cmd = globals().get("GUARD_CMD") or [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", GUARD]
    code = _step("guard", guard_cmd)
    if code != EXIT_CLEAN:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != EXIT_CLEAN:
            return code
    print("\nGreen.")
    return EXIT_CLEAN


def apply(check_only: bool) -> int:
    root = Path.cwd()

    # FIRST. Before the sentinel, before any anchor. See the docstring.
    refuse_wrong_repository(root)

    if not (root / SENTINEL_FILE).exists():
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise Stop(globals().get("MISSING_HELP") or
                   f"run this from the root of a {REPO} checkout "
                   f"(no {SENTINEL_FILE} here)", EXIT_CANNOT_RUN)

    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8-sig"):
        # ALREADY APPLIED IS NOT AN ERROR, AND USED TO EXIT 1.
        #
        # The operator runs this from a phone and the honest question behind a
        # second run is "did this land?". Exiting 1 answered "something
        # disagreed", which is the one thing that had not happened. Re-running
        # the suites answers the question that was actually asked, and a
        # repository that has the change and passes its tests is CLEAN.
        print(f"already applied -- {SENTINEL!r} is present in "
              f"{SENTINEL_FILE}.\nNothing to write. Re-running the suites so "
              f"the answer is measured rather than assumed.\n")
        return verify()

    tree = Tree(root)
    edits(tree)

    # THE SCRIPT MUST WRITE ITS OWN SENTINEL WHERE apply() LOOKS FOR IT.
    #
    # Checked here, against the in-memory tree, before anything reaches disk.
    #
    # WHY THIS IS NOT A BUILD-TIME CHECK. The build's `sentinel-written` guard
    # asserts the marker appears at least twice in the composed script -- its
    # own declaration plus somewhere it gets written. That is a PROXY. A round
    # can carry the marker in a new guard file and never put it in
    # SENTINEL_FILE, and the build passes while the already-applied branch can
    # never fire. That shipped once, on 2026-09-24: the operator ran a landed
    # script a second time and got "expected 1 occurrence of the anchor, found
    # 0. The file moved" -- about a file that had not moved, from a script
    # that could not tell it had already run.
    #
    # Here the question is exact rather than approximated: after every edit,
    # is the marker in the file apply() reads? It fires on the FIRST run, in
    # the author's verification, rather than on the operator's second.
    if SENTINEL not in tree.read(SENTINEL_FILE):
        raise Stop(
            f"this script never writes {SENTINEL!r} into {SENTINEL_FILE}, "
            f"which is the file it reads to tell whether it has already run.\n"
            f"Applied once it would work; run again it would re-attempt "
            f"anchors that are already replaced and report them as missing.\n"
            f"Add an edit that marks {SENTINEL_FILE}. Nothing was written.",
            EXIT_CANNOT_RUN)
    # GUARD_SOURCE is OPTIONAL. Every round until 2026-09-12 installed a new
    # guard file, so the harness assumed one; the ramp-condense round adopts
    # three that already exist -- the mixer's SPLITS table and two RETIRED
    # tuples -- and adding a fourth rule for what they already watch is how a
    # suite grows checks that disagree. GUARD still names the file verify()
    # runs first; it just does not have to be a file this script wrote.
    source = globals().get("GUARD_SOURCE")
    if source is not None:
        tree.write(GUARD, source)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        _left_alone()
        return EXIT_CLEAN

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    code = verify()
    if code == EXIT_CLEAN:
        _left_alone()
    return code


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    # A terminal that is not a Windows console (Git Bash's mintty) gets the
    # locale's code page, and one character it cannot encode would end the
    # run mid-report. Say it some other way instead.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    try:
        refuse_to_shadow()
        if args.finish:
            finish()
            return EXIT_CLEAN
        if args.verify:
            return verify()
        return apply(args.check)
    except Stop as stop:
        # Print it ourselves and return the taxonomy code. Letting SystemExit
        # propagate would print the message and exit 1 regardless of .code.
        print(stop.args[0] if stop.args else "", file=sys.stderr)
        return stop.code


if __name__ == "__main__":
    raise SystemExit(main())
