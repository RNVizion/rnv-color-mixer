"""A STATUS IS NEVER SHOWN BY COLOR ALONE (#85 A, 2026-10-22).

The same file in all five RNV desktop applications.

THE RULING. Chris, 22 October 2026, on the brand chat's deuteranopia finding
(the register's success and warning text sit 7.3 to 8.2 apart under
deuteranopia, below the 8.40 bar held for normal vision): a status is never
shown by color alone. Every place a status color is painted, a word or a
glyph says the same thing, so the color can be a second reading and not the
only one. Surveyed the same day across the five applications: one place
carried its meaning in color alone, the text transformer's encoding dialog,
where the detection confidence was tinted success, warning or error with no
word. It now reads "95.0% (high)", "75.0% (medium)", "40.0% (low)".

WHAT IT READS. Every function in the application's own source (tests, tools
and the two color files left out) that both names a status color and paints
with it. A status color is a name from utils/colors.py with success, warning
or error in it, a palette key 'success', 'warning', 'error' or
'status_active', or a helper named for one. Painting is setStyleSheet,
QColor, setForeground, setBackground, setPen, setBrush or the application's
own stylesheet helpers.

WHAT IT HOLDS. Every such function is listed in CARRIED for this
application, with the words or glyphs that carry the status, and those
strings are still in its source. A function the sweep finds that is not
listed fails: look at it, give its status a word, and list it with the
evidence. A listed function that has gone, or lost its words, fails too.
In the text transformer, the three confidence tiers are also exercised.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"tests", "tools", ".git", ".venv", "venv", "build", "dist", "__pycache__", "site-packages"}
LEFT_OUT = {"utils/colors.py", "utils/config.py"}

#: (module, qualified function name, strings that carry the status in words,
#: note) for every status-color consumer, by application name.
CARRIED: dict[str, tuple[tuple[str, str, tuple[str, ...], str], ...]] = {
    "RNV Color Picker": (
        ("ui/settings_panel.py", "SettingsPanel._create_harmony_tab",
         ("Color Harmony module not available.",),
         "the error-colored label is that sentence"),
        ("ui/settings_panel.py", "SettingsPanel._create_accessibility_tab",
         ("Accessibility module not available.",),
         "the error-colored label is that sentence"),
        ("ui/settings_panel.py", "SettingsPanel._update_contrast_check",
         ('" - PASS"', '" - FAIL"'),
         "the WCAG labels end in PASS or FAIL on the success or error plate"),
        ("ui/settings_panel.py", "SettingsPanel._update_contrast_check.set_pass_fail",
         ('" - PASS"', '" - FAIL"'),
         "the same, in the inner function that paints"),
        ("utils/cache.py", "StylesheetCache.get_error_stylesheet",
         ("def get_error_stylesheet",),
         "helper that builds the error label's sheet; the words are at its callers, the two settings tabs"),
    ),
    "RNV Color Mixer": (),
    "RNV Icon Builder": (
        ("ui/ico_analyzer.py", "IcoAnalyzerDialog._mark_png_rows",
         ("item.text() == 'PNG'",),
         "the marked cells read PNG; the word is the format itself, and BMP cells are not marked"),
        ("ui/settings_dialog.py", "SettingsDialog.update_watch_status",
         ("Watching: {folder}", "Not watching"),
         "the label says Watching or Not watching"),
        ("ui/settings_dialog.py", "SettingsDialog._apply_theme",
         ("watch_status_label",),
         "restyles the watch label on a theme switch; its words are set in update_watch_status"),
    ),
    "RNV Color Palette Manager": (
        ("ui/batch_export_dialog.py", "BatchExportDialog.accept",
         ("Please select a valid output folder.", "Select at least one format."),
         "the error-colored status says what is wrong, with a warning glyph"),
        ("ui/batch_export_dialog.py", "BatchExportDialog._error_text_color",
         ("def _error_text_color",),
         "helper that picks the mode's error text color; the words are at its callers, in accept"),
    ),
    "RNV Text Transformer": (
        ("ui/compare_dialog.py", "ChangeWidget._setup_ui",
         ('setText("+")', 'setText("-")', 'setText("~")'),
         "insert, delete and replace carry their own glyph"),
        ("ui/compare_dialog.py", "ChangeWidget._update_status",
         ('"Accepted"', '"Rejected"'),
         "the status label says Accepted or Rejected"),
        ("ui/encoding_dialog.py", "EncodingDialog._on_detection_complete",
         ("({tier_word})",),
         "the confidence reads high, medium or low beside the percent (#85 A)"),
        ("ui/export_dialog.py", "ExportDialog._update_format_status",
         ('f"✔ {message}"', 'f"✘ {message}"'),
         "a check or a cross before the dependency message"),
        ("ui/preset_dialog.py", "StepEditorWidget._setup_ui",
         ('QPushButton("✕")', '"Delete this step"'),
         "the delete button is a cross with a tooltip; its error color is a second reading"),
        ("ui/regex_builder_dialog.py", "RegexBuilderDialog._on_pattern_changed",
         ('"Pattern is valid"', 'f"Error: {error}"'),
         "the status says valid or Error"),
        ("ui/regex_builder_dialog.py", "RegexBuilderDialog._update_matches",
         ('f"Error: {error}"', "Found {count} match"),
         "the status says Error or how many matches"),
        ("ui/watch_folder_dialog.py", "WatchFolderDialog._setup_ui",
         ("requires the 'watchdog' library",),
         "the error-colored label is that sentence, with a warning glyph"),
    ),
}

STATUS_KEY = re.compile(r"""\[\s*['"](success|warning|error|status_active)['"]\s*\]""")
LOOSE = re.compile(
    r"(?i)\b\w*(error|warning|success)\w*(color|text|bg|fg|brush|pen)\w*\b"
    r"|\b(color|text|bg|fg|brush|pen)\w*(error|warning|success)\w*\b"
    r"""|_set_status_color\(\s*['"](success|warning|error)""")
PAINT = re.compile(
    r"setStyleSheet|QColor\(|setForeground|setBackground|setPen\(|setBrush\(|fillRect"
    r"|setTextColor|setColor\(|setNamedColor|_style_for_mode|_set_status_color"
    r"|_error_text_color|StyleSheet|stylesheet")


def _app_name() -> str:
    return json.loads((ROOT / "brand_map.json").read_text(encoding="utf-8"))["app"]


def _status_names() -> set[str]:
    tree = ast.parse((ROOT / "utils" / "colors.py").read_text(encoding="utf-8-sig"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and re.search(r"(?i)success|warning|error|status_active", t.id):
                    names.add(t.id)
    return names


def _functions(tree: ast.Module) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                if not isinstance(child, ast.ClassDef):
                    out[name] = child
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(tree, "")
    return out


def _source_files():
    for py in sorted(ROOT.rglob("*.py")):
        rel = py.relative_to(ROOT)
        if any(p in SKIP_DIRS or p.startswith(".") for p in rel.parts):
            continue
        if rel.name.startswith("test_") or rel.as_posix() in LEFT_OUT:
            continue
        yield rel.as_posix(), py


def _function_source(path: Path, fn: ast.AST) -> str:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return "\n".join(lines[fn.lineno - 1: fn.end_lineno])


def _consumers() -> list[tuple[str, str]]:
    names = _status_names()
    name_re = re.compile(r"\b(" + "|".join(sorted(map(re.escape, names))) + r")\b") if names else None
    found = []
    for rel, py in _source_files():
        try:
            tree = ast.parse(py.read_text(encoding="utf-8-sig"), filename=rel)
        except SyntaxError:
            continue
        for qualname, fn in _functions(tree).items():
            body = _function_source(py, fn)
            named = STATUS_KEY.search(body) or LOOSE.search(body) or (name_re and name_re.search(body))
            if named and PAINT.search(body):
                found.append((rel, qualname))
    return found


def _carried():
    name = _app_name()
    assert name in CARRIED, f"brand_map.json names {name!r}; CARRIED has no entry for it"
    return CARRIED[name]


def test_every_status_color_consumer_is_listed_with_its_words():
    listed = {(m, q) for m, q, _, _ in _carried()}
    unlisted = [f"{m}: {q}" for m, q in _consumers() if (m, q) not in listed]
    assert not unlisted, (
        "these functions paint a status color and are not listed in CARRIED; "
        "make sure each says its status in a word or a glyph, then list it with that evidence:\n"
        + "\n".join(unlisted))


def test_every_listed_consumer_exists_and_still_carries_its_words():
    failures = []
    for module, qualname, evidence, _note in _carried():
        path = ROOT / module
        if not path.exists():
            failures.append(f"{module}: file not found")
            continue
        fn = _functions(ast.parse(path.read_text(encoding="utf-8-sig"), filename=module)).get(qualname)
        if fn is None:
            failures.append(f"{module}: {qualname} not found")
            continue
        assert evidence, f"{module}: {qualname} is listed with no evidence"
        body = _function_source(path, fn)
        for s in evidence:
            if s not in body:
                failures.append(f"{module}: {qualname} no longer holds {s!r}")
    assert not failures, "\n".join(failures)


def test_the_sweep_sees_the_listed_consumers():
    """The detector finds what the list names, so the list is not a dead letter.

    A listed function the sweep cannot see is one whose status could go back
    to color alone unnoticed; it is allowed only with a note saying why.
    """
    seen = set(_consumers())
    unseen = [f"{m}: {q}" for m, q, _, note in _carried()
              if (m, q) not in seen and "(#85 A)" not in note and "helper" not in note]
    assert not unseen, "listed but not found by the sweep:\n" + "\n".join(unseen)


# ------------------------------------------------- the text transformer's tiers

def test_confidence_tiers_carry_a_word():
    if _app_name() != "RNV Text Transformer":
        pytest.skip("the encoding dialog is the text transformer's")
    from ui.encoding_dialog import CONFIDENCE_TIERS, confidence_tier
    assert [w for _, w, _ in CONFIDENCE_TIERS] == ["high", "medium", "low"]
    assert confidence_tier(95.0) == ("high", "success")
    assert confidence_tier(90.0) == ("high", "success")
    assert confidence_tier(89.9) == ("medium", "warning")
    assert confidence_tier(70.0) == ("medium", "warning")
    assert confidence_tier(69.9) == ("low", "error")
    assert confidence_tier(0.0) == ("low", "error")


def test_confidence_label_says_its_tier(qtbot):
    if _app_name() != "RNV Text Transformer":
        pytest.skip("the encoding dialog is the text transformer's")
    from core.theme_manager import ThemeManager
    from ui.encoding_dialog import EncodingDialog, EncodingResult
    tm = ThemeManager()
    tm.current_theme = "dark"
    dlg = EncodingDialog(tm, input_text="some text")
    qtbot.addWidget(dlg)
    for confidence, word in ((0.95, "high"), (0.75, "medium"), (0.40, "low")):
        dlg._on_detection_complete(EncodingResult(True, "utf-8", confidence, "some text", "Detected"))
        text = dlg.confidence_label.text()
        assert f"({word})" in text, text
        assert f"{confidence * 100:.1f}%" in text, text
