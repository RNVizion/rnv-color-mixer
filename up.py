"""the theme button files the mode it set, for rnv-color-mixer

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (ac54325).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-30: "Yes do this" -- item 4 of decisions-pending-2026-09-29.md.

The theme button changed the mode for the session only. Only the control
panel's Save wrote preferences.theme, so a switch made with the button was
lost at the next launch, which opened in whatever the file held. The picker's
and the transformer's theme buttons file the mode on every press. The mixer's
does now: after the switch has reached every part of the window, including
the control panel, it writes the one key the panel's Save writes, to the same
file, through the same settings manager. A saved Auto (follow system) gives
way to the mode the app is in, as it does in the picker.

The theme-box guard's docstring said the button did not write the mode. That
sentence is corrected; the tests in that file are unchanged and still pass.
"""
from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = 'rnv-color-mixer'
SENTINEL = 'RNV-THEME-SAVE'
SENTINEL_FILE = 'RNV_Color_Mixer.py'
GUARD = 'tests/test_theme_button_saves.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_theme_button_saves.py', 'tests/test_theme_box.py']
DESCRIPTION = 'the theme button files the mode it set, for rnv-color-mixer'

#: EXACTLY WHAT THE LINUX WORKFLOW RUNS: the locked file's hash first, both
#: suites under coverage, the combine, and the floor. The Windows workflow runs
#: the same two suites without coverage.
_LOCK = ("import hashlib, sys\n"
         "want = '0827b02dbaa946087da83a27b391065aaa6114cfe43a78c958f6b0a502b0eddd'\n"
         "got = hashlib.sha256(open('test_rnv_color_mixer.py', 'rb').read()).hexdigest()\n"
         "if got != want:\n"
         "    raise AssertionError(f'locked file changed: {got}')\n"
         "print('Locked file SHA-256 matches:', got)\n")
#: coverage exits 2 for a shortfall, which this harness would read as the
#: environment; wrapped so falling under the floor reads as a failure.
_FLOOR = ("import subprocess, sys\n"
          "r = subprocess.run([sys.executable, '-m', 'coverage', 'report', "
          "'--fail-under=69'])\n"
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
    ("CI: coverage floor 69", [sys.executable, "-c", _FLOOR]),
]

#: The workflows SUITES was written from, by content hash.
CI_MIRRORS = {'.github/workflows/tests-linux.yml': '769b9b7034c0599b5d655cfb502741706693e765d51e2db95406c140a6b92ffd', '.github/workflows/tests-windows.yml': 'd123e5da015c9b988e5c52e9c0bb9879d492365b6db6c1f3672dc1b34f57d967'}

SHADOWS = {"config.py", "conftest.py", "package_d_panel.py", "settings_manager.py", "test_rnv_color_mixer.py", "test_theme_box.py", "test_theme_button_saves.py"}

LEFT_ALONE = ["the panel's Save: it still writes the box's mode with the panel's other choices, and after a switch the box names the mode the app is in (RNV-THEME-BOX), so Save and the button agree.", 'closing the app: it does not write the mode, as before. The button has already filed it.', "Export Settings: it copies the panel to the settings manager's memory and writes an export file, not the settings file, as before. A press of the button after an export files that memory too."]


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('RNV_Color_Mixer.py',
             '                self._package_d_panel.set_theme(is_dark)\n                logger.debug(f"Theme applied to Package D panel (dark={is_dark})")\n        \n        ErrorHandler.safe_execute(cycle_theme, "cycling theme", print)\n',
             '                self._package_d_panel.set_theme(is_dark)\n                logger.debug(f"Theme applied to Package D panel (dark={is_dark})")\n            \n            # RNV-THEME-SAVE 2026-09-30: file the mode this press set, as the\n            # picker\'s and the transformer\'s theme buttons do. Until now only\n            # the control panel\'s Save wrote it, so a switch made here was\n            # lost at the next launch. The same key Save writes, and the\n            # same file; a saved Auto gives way to the mode the app is in.\n            if self.settings_manager:\n                self.settings_manager.set("preferences.theme",\n                                          self.ui_handler.theme_manager.current_theme)\n                self.settings_manager.save_settings()\n        \n        ErrorHandler.safe_execute(cycle_theme, "cycling theme", print)\n')
    tree.sub('tests/test_theme_box.py',
             "launch opened in it. The theme button does not write the mode itself, so the\npanel's Save is the one thing that does.\n",
             "launch opened in it. When this was written the theme button did not write\nthe mode itself, so the panel's Save was the one thing that did; since\nRNV-THEME-SAVE (2026-09-30) the button files it too, and\ntest_theme_button_saves.py holds that.\n")
    if (tree.root / 'tests/test_theme_button_saves.py').exists():
        raise Stop('tests/test_theme_button_saves.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_theme_button_saves.py', '"""RNV-THEME-SAVE, 2026-09-30: the theme button files the mode it set.\n\nWHAT WAS WRONG. The button changed the mode for the session only. Only the\ncontrol panel\'s Save wrote preferences.theme, so a switch made with the\nbutton was lost at the next launch, which opened in whatever the file held.\nThe picker\'s and the transformer\'s buttons file the mode on every press;\nruled 2026-09-30 that the mixer\'s should too.\n\nEach test drives the app the way a person does: the theme button, the\npanel\'s opener, the panel\'s Save, a second launch. What is asserted is read\nback from the settings FILE on disk, not from memory, because the file is\nwhat the next launch reads.\n"""\nfrom __future__ import annotations\n\nimport json\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton\n\npytestmark = pytest.mark.integration\n\n\ndef _mode(app_window) -> str:\n    return app_window.ui_handler.theme_manager.current_theme\n\n\ndef _switch(app_window) -> str:\n    """One press of the theme button."""\n    app_window._on_theme_button_clicked()\n    QApplication.processEvents()\n    return _mode(app_window)\n\n\ndef _on_disk(app_window) -> dict:\n    """The settings file as it is now, re-read from disk."""\n    with open(app_window.settings_manager.settings_file, encoding="utf-8") as f:\n        return json.load(f)\n\n\ndef _without_theme(settings: dict) -> dict:\n    prefs = {k: v for k, v in settings.get("preferences", {}).items() if k != "theme"}\n    rest = {k: v for k, v in settings.items() if k != "preferences"}\n    return {**rest, "preferences": prefs}\n\n\ndef test_the_button_files_the_mode_it_set(app_window):\n    seen = []\n    for _ in range(3):                                  # every mode, and back\n        mode = _switch(app_window)\n        seen.append(mode)\n        assert _on_disk(app_window)["preferences"]["theme"] == mode, mode\n    assert {"dark", "light", "image"} <= set(seen), seen\n\n\ndef test_the_button_writes_the_mode_and_nothing_else(app_window):\n    before = _without_theme(_on_disk(app_window))\n    for _ in range(3):\n        _switch(app_window)\n        assert _without_theme(_on_disk(app_window)) == before, \\\n            "a press of the theme button changed a setting other than the mode on disk"\n\n\ndef test_the_next_launch_opens_in_the_mode_the_button_set(app_window, main_module, qtbot):\n    for _ in range(2):\n        mode = _switch(app_window)\n        again = main_module.ColorMixerApp()\n        qtbot.addWidget(again)\n        try:\n            QApplication.processEvents()\n            assert _mode(again) == mode, (mode, _mode(again))\n            assert again.theme_button.text() == app_window.theme_button.text()\n        finally:\n            again.close()\n            QApplication.processEvents()\n\n\ndef test_a_saved_auto_gives_way_to_the_mode_the_button_set(app_window):\n    """The panel can save Auto (follow system). The app starts in dark for it\n    and follows no system scheme. A press of the button files the mode the\n    app is in, as the picker\'s does, so the next launch opens in that mode."""\n    app_window.settings_manager.set("preferences.theme", "auto")\n    assert app_window.settings_manager.save_settings()\n    assert _on_disk(app_window)["preferences"]["theme"] == "auto"\n    mode = _switch(app_window)\n    assert _on_disk(app_window)["preferences"]["theme"] == mode\n\n\ndef test_save_still_files_the_mode_and_the_panel_s_other_choices(app_window, monkeypatch):\n    """The panel\'s Save is unchanged: it writes the box\'s mode with the rest\n    of the panel, and after a switch the box names the mode the app is in\n    (RNV-THEME-BOX), so Save and the button agree."""\n    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: 0)\n    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: 0)\n    app_window.open_package_d_panel()\n    QApplication.processEvents()\n    panel = app_window._package_d_panel\n    save = [b for b in panel.findChildren(QPushButton) if b.text().strip() == "Save"]\n    assert len(save) == 1\n    mode = _switch(app_window)\n    panel.tooltips_check.setChecked(not panel.tooltips_check.isChecked())\n    save[0].click()\n    QApplication.processEvents()\n    disk = _on_disk(app_window)\n    assert disk["preferences"]["theme"] == mode\n    assert disk["preferences"]["show_tooltips"] == panel.tooltips_check.isChecked()\n')


def _original(tree, rel: str) -> str:
    """The file as it is on disk, which checks() runs before flush() changes,
    normalised the way Tree.read() normalises it."""
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


def checks(tree) -> None:
    """Against the IN-MEMORY tree, before anything reaches disk."""
    def methods(src, cls):
        body = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == cls).body
        return {n.name: n for n in body if isinstance(n, ast.FunctionDef)}

    # ---- the app: one method gains one block at the end of its inner function
    old_src, new_src = _original(tree, "RNV_Color_Mixer.py"), tree.read("RNV_Color_Mixer.py")
    o, n = methods(old_src, "ColorMixerApp"), methods(new_src, "ColorMixerApp")
    assert set(o) == set(n), f"ColorMixerApp: methods added or removed: {sorted(set(o) ^ set(n))}"
    moved = sorted(k for k in o if ast.dump(o[k]) != ast.dump(n[k]))
    assert moved == ["_on_theme_button_clicked"], f"ColorMixerApp: moved {moved}"
    inner_o = next(x for x in o["_on_theme_button_clicked"].body if isinstance(x, ast.FunctionDef))
    inner_n = next(x for x in n["_on_theme_button_clicked"].body if isinstance(x, ast.FunctionDef))
    assert [ast.dump(s) for s in inner_n.body[:-1]] == [ast.dump(s) for s in inner_o.body], \
        "the button's switch changed beyond filing the mode at its end"
    rest_o = [ast.dump(s) for s in o["_on_theme_button_clicked"].body if not isinstance(s, ast.FunctionDef)]
    rest_n = [ast.dump(s) for s in n["_on_theme_button_clicked"].body if not isinstance(s, ast.FunctionDef)]
    assert rest_o == rest_n, "the button's handler changed outside its inner function"
    last = inner_n.body[-1]
    assert isinstance(last, ast.If) and ast.unparse(last.test) == "self.settings_manager" and not last.orelse, \
        "the write is not guarded on the settings manager"
    calls = [ast.unparse(s.value) for s in last.body if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)]
    assert calls == ["self.settings_manager.set('preferences.theme', "
                     "self.ui_handler.theme_manager.current_theme)",
                     "self.settings_manager.save_settings()"], f"the write is not the one derived: {calls}"
    outside = lambda src: [ast.dump(x) for x in ast.parse(src).body   # noqa: E731
                           if not (isinstance(x, ast.ClassDef) and x.name == "ColorMixerApp")]
    assert outside(old_src) == outside(new_src), "the module moved beyond the app class"

    # ---- the premise: the key the button writes is the one the launch reads
    # and the one the panel's Save writes, through the same manager
    launch = ast.unparse(n["_apply_all_settings"])
    assert "prefs.get('theme'" in launch and "self._apply_theme_setting(theme)" in launch, \
        "the launch no longer applies preferences.theme: the write would reach nothing"
    panel = tree.read("core/package_d_panel.py")
    save = _function(panel, "_save_ui_to_settings", "PackageDPanel")
    assert "self.settings_manager.set('preferences.theme', theme)" in ast.unparse(save), \
        "the panel's Save no longer writes preferences.theme: the two would disagree"
    # every panel road that writes the manager's memory also writes a file, so
    # the button's save_settings() never files a change a person did not save
    pcls = next(x for x in ast.parse(panel).body if isinstance(x, ast.ClassDef) and x.name == "PackageDPanel")
    for fn in (x for x in pcls.body if isinstance(x, ast.FunctionDef)):
        text = ast.unparse(fn)
        if "self._save_ui_to_settings(" in text:
            called = {getattr(c.func, "attr", None) for c in ast.walk(fn) if isinstance(c, ast.Call)}
            assert called & {"save_settings", "export_settings"}, \
                f"PackageDPanel.{fn.name}() writes settings to memory and not to a file: " \
                "the button's save would file it"
    mgr = tree.read("utils/settings_manager.py")
    assert "json.dump(self.settings, f" in ast.unparse(_function(mgr, "save_settings", "SettingsManager")), \
        "save_settings() no longer writes the manager's settings to the file"

    # ---- the theme-box guard: its docstring only
    def sans_doc(src):
        mod = ast.parse(src)
        if mod.body and isinstance(mod.body[0], ast.Expr) and isinstance(mod.body[0].value, ast.Constant):
            mod.body = mod.body[1:]
        return ast.dump(mod)
    assert sans_doc(_original(tree, "tests/test_theme_box.py")) == sans_doc(tree.read("tests/test_theme_box.py")), \
        "test_theme_box.py changed beyond its docstring"
    assert SENTINEL in ast.get_docstring(ast.parse(tree.read("tests/test_theme_box.py"))), \
        "the theme-box guard's docstring does not name this round"

    guard = tree.read(GUARD)
    ast.parse(guard)
    for name in ("test_the_button_files_the_mode_it_set", "test_the_button_writes_the_mode_and_nothing_else",
                 "test_the_next_launch_opens_in_the_mode_the_button_set",
                 "test_a_saved_auto_gives_way_to_the_mode_the_button_set",
                 "test_save_still_files_the_mode_and_the_panel_s_other_choices"):
        assert f"def {name}(" in guard, f"the guard lost {name}"
    assert SENTINEL in guard, "the guard is not the one this round writes"
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
