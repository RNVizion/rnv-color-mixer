"""chart rulings 2-5: remove what nothing reads, restyle on switch, derive the wash

    python up.py             # apply, then run the guards and CI's own commands
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the guards and CI's commands, change nothing

For rnv-color-mixer, derived against a fresh clone at the live head (61b6574).

RNV-DELIVERY-SCRIPT-DO-NOT-SWEEP. This script is a delivery tool, not
application source, and it names what it retires. That marker is what tells
this fleet's scanners to skip it.

RULED 2026-09-26, four of the five decisions the colour chart put in view.

  2. "Render to make sure, then if not used at all we can remove." The three
     CSS-name entries in LIGHT_THEME -- checkbox_border 'gray', label_bg
     'white', label_border 'black' -- and their keys in DARK and IMAGE.
  5. "Removed if not used; render first." checkbox_bg in all three palettes,
     and the two alphas that existed only for it.
     Rendered first (probes/unused_render.py): all twelve entries set to
     #ff00ff changed no pixel in 105 captures and no text in 1,020 sheet and
     palette entries; a control that moved DARK's canvas_bg changed 1 capture
     and 10 entries.
  3. "Yes." Restyle on mode switch: the preview's border (stale until the
     next mix), the slot swatches' border and hover (always dark: they asked
     a fresh ThemeManager), the control panel's shortcut badges and the About
     dialog's gold text (always dark: styled once, before the mode was known).
  4. "Yes." The harmony description's wash, rgba(r, g, b, 0.1) from channels
     sliced by hand, is translucent(accent, HARMONY_DESCRIPTION_ALPHA). Qt
     makes 0.1 the byte 0x19; the same pixels.

Rendered after (probes/restyle_render.py): of 105 captures, 13 change, all in
light mode -- dark and image render pixel for pixel as shipped.
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
SENTINEL = 'RNV-CHART-RULINGS'
SENTINEL_FILE = 'tests/test_derived_values.py'
GUARD = 'tests/test_mode_switch_restyle.py'
#: Every guard this round touches, run before CI's own commands.
GUARD_CMD = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             'tests/test_derived_values.py', 'tests/test_mode_switch_restyle.py']
DESCRIPTION = 'chart rulings 2-5: remove what nothing reads, restyle on switch, derive the wash'

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

SHADOWS = {"config.py", "conftest.py", "about_dialog.py", "color_slot.py", "package_d_panel.py", "test_rnv_color_mixer.py"}

LEFT_ALONE = ["ruling 1, the gray/grey description text: rendered, waiting on a pick between #888888 and the app's own muted-text key.", "the About dialog's constructor. The app passes its ui_handler where the dark flag belongs; with both gold texts restyled in _apply_theme() it no longer shows, so the call is left as it is.", "the Presets tab's empty-state line ('No user presets yet'), gold text set as a list item's foreground when the tab fills. It keeps the old mode's gold across a switch until the list refills -- the same kind of fault, but not one of the seven the chart saw, so it is for a ruling.", 'every other element the chart could not see live (196 in this app). The seven were what the read-back found; a sweep of the rest is a round of its own.']


def edits(tree) -> None:
    """Every substitution, against the in-memory tree. Each anchor is
    checked for its exact number of occurrences before anything is
    written."""
    tree.sub('utils/config.py',
             'CHECKBOX_BG_ALPHA_DARK: Final[int] = 0xE6\n"""230. checkbox_bg in the dark and image palettes (APP_SURFACE_DARK). Nothing\nreads that key today; derived all the same, so it cannot fall behind."""\n\nCHECKBOX_BG_ALPHA_LIGHT: Final[int] = 0xC8\n"""200. checkbox_bg in the light palette (WHITE). Unread, like its dark twin."""\n',
             'HARMONY_DESCRIPTION_ALPHA: Final[int] = 0x19\n"""25. The control panel\'s harmony description: a wash of its own accent ink\n(accent_ink -- BRAND_GOLD in dark and image, BRAND_DARK_GOLD_DEEP in light).\nWritten rgba(r, g, b, 0.1) from channels sliced by hand until 2026-09-26.\n0.1 * 255 is 25.5, and Qt\'s stylesheet parser gives 25 -- MEASURED on five\ngrounds under both inks, not computed. The same pixels."""\n')
    tree.sub('utils/config.py',
             "        'checkbox_bg': translucent(APP_SURFACE_DARK, CHECKBOX_BG_ALPHA_DARK),\n        'checkbox_border': APP_BORDER_DARK,\n",
             '', times=2)
    tree.sub('utils/config.py',
             "        'checkbox_bg': translucent(WHITE, CHECKBOX_BG_ALPHA_LIGHT),\n        'checkbox_border': 'gray',\n",
             '')
    tree.sub('utils/config.py',
             "        'label_bg': APP_SURFACE_DARK,\n        'label_border': APP_BORDER_DARK,\n",
             '', times=2)
    tree.sub('utils/config.py',
             "        'label_bg': 'white',\n        'label_border': 'black',\n",
             '')
    tree.sub('core/package_d_panel.py',
             'def _style_harmony_description(panel) -> None:\n    accent = _theme_colors(bool(getattr(panel, "_is_dark", True)))["accent_ink"]\n    r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)\n    panel.harmony_description.setStyleSheet(\n        f"color: {accent}; font-size: {config.FONT_SIZES[\'small\']}px; "\n        f"padding: 8px; background-color: rgba({r}, {g}, {b}, 0.1); "\n        f"border-radius: 4px;")\n',
             'def _style_harmony_description(panel) -> None:\n    """The description in the accent ink, on a wash of the same ink.\n\n    The wash is DERIVED, translucent(accent, HARMONY_DESCRIPTION_ALPHA).\n    Until 2026-09-26 it was rgba(r, g, b, 0.1) from channels sliced out of\n    the hex by hand -- the one derived value in the fleet that did not go\n    through a helper. Qt makes 0.1 the byte 25, so the pixels are the same.\n    """\n    accent = _theme_colors(bool(getattr(panel, "_is_dark", True)))["accent_ink"]\n    wash = config.translucent(accent, config.HARMONY_DESCRIPTION_ALPHA)\n    panel.harmony_description.setStyleSheet(\n        f"color: {accent}; font-size: {config.FONT_SIZES[\'small\']}px; "\n        f"padding: 8px; background-color: {wash}; "\n        f"border-radius: 4px;")\n\n\ndef _style_key_badge(panel, badge) -> None:\n    """A shortcut key badge on the Quick Actions tab -- accent plate, accent\n    text -- registered for re-theming, as the tips and headers are.\n\n    RNV-CHART-RULINGS, 2026-09-26 (ruling 3). The nine badges were styled\n    once, while the tab was built. That is before set_theme() has run, so\n    always from the dark palette, and set_theme() never reached them: light\n    mode showed dark\'s gold plate. set_theme() now restyles every one.\n    """\n    badges = panel.__dict__.setdefault("_themed_key_badges", [])\n    if badge not in badges:\n        badges.append(badge)\n    t = _theme_colors(bool(getattr(panel, "_is_dark", True)))\n    badge.setStyleSheet(f"""\n                background-color: {t[\'accent\']};\n                color: {t[\'accent_text\']};\n                padding: 3px 8px;\n                border-radius: 3px;\n                font-weight: bold;\n                font-size: {config.FONT_SIZES[\'small\']}px;\n            """)\n')
    tree.sub('core/package_d_panel.py',
             '            key_label = QLabel(shortcut)\n            _t_k = _theme_colors(getattr(self, \'_is_dark\', True))\n            key_label.setStyleSheet(f"""\n                background-color: {_t_k[\'accent\']};\n                color: {_t_k[\'accent_text\']};\n                padding: 3px 8px;\n                border-radius: 3px;\n                font-weight: bold;\n                font-size: {config.FONT_SIZES[\'small\']}px;\n            """)\n',
             '            key_label = QLabel(shortcut)\n            _style_key_badge(self, key_label)\n')
    tree.sub('core/package_d_panel.py',
             "        for _hdr in getattr(self, '_themed_headers', []):\n            try:\n                _hdr.setStyleSheet(_section_header_style(accent_ink))\n            except RuntimeError:\n                pass\n",
             "        for _hdr in getattr(self, '_themed_headers', []):\n            try:\n                _hdr.setStyleSheet(_section_header_style(accent_ink))\n            except RuntimeError:\n                pass\n        for _badge in getattr(self, '_themed_key_badges', []):\n            try:\n                _style_key_badge(self, _badge)\n            except RuntimeError:\n                pass\n")
    tree.sub('core/color_slot.py',
             "            theme_manager.current_theme = 'dark' if is_dark else 'light'\n            theme = theme_manager.get_current_theme()\n        \n        if theme:\n",
             "            theme_manager.current_theme = 'dark' if is_dark else 'light'\n            theme = theme_manager.get_current_theme()\n        # Kept for _update_swatch_display(), which a colour change calls\n        # without a theme.\n        self._theme = theme\n        \n        if theme:\n")
    tree.sub('core/color_slot.py',
             '        # Get border styling based on theme\n        theme = config.ThemeManager().get_current_theme()\n',
             "        # The theme set_theme() last gave this slot. Before it has run -- the\n        # swatch is first painted from __init__ -- a fresh ThemeManager\n        # answers, and a fresh ThemeManager is always in dark mode.\n        #\n        # RNV-CHART-RULINGS, 2026-09-26 (ruling 3). This asked ONLY the fresh\n        # ThemeManager, so every swatch kept dark's border and dark's gold\n        # hover in light mode, however often set_theme() ran.\n        theme = getattr(self, '_theme', None) or config.ThemeManager().get_current_theme()\n")
    tree.sub('RNV_Color_Mixer.py',
             '            for slot in self.slots:\n                if hasattr(slot, \'set_theme\'):\n                    slot.set_theme(is_dark, self.ui_handler)\n        \n        ErrorHandler.safe_execute(apply_theme, "applying theme to components", print)\n',
             '            for slot in self.slots:\n                if hasattr(slot, \'set_theme\'):\n                    slot.set_theme(is_dark, self.ui_handler)\n\n            # The preview\'s border is the mode\'s border_color, and only\n            # _update_preview() writes it. RNV-CHART-RULINGS, 2026-09-26\n            # (ruling 3): until this, a mode switch left the previous mode\'s\n            # border on the preview until the next colour was mixed.\n            if getattr(self, \'preview_label\', None) is not None:\n                self._update_preview(self.current_mixed_color)\n        \n        ErrorHandler.safe_execute(apply_theme, "applying theme to components", print)\n')
    tree.sub('ui/about_dialog.py',
             '        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME\n        version_label = QLabel(f"Version {app_info[\'version\']}")\n        version_label.setStyleSheet(f"font-size: 14px; color: {_t[\'accent_ink\']}; border: none; background: transparent;")\n',
             '        version_label = QLabel(f"Version {app_info[\'version\']}")\n        self._version_label = version_label\n        self._style_version_label()\n')
    tree.sub('ui/about_dialog.py',
             '        _t = config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME\n        credits_text = f"""\n<h3>Credits & Acknowledgments</h3>\n\n<h4>Development</h4>\n<p>RNV Color Mixer was created with passion for color science and \npractical tools for artists and designers.</p>\n\n<h4>Technologies</h4>\n<table width="100%">\n<tr><td width="40%"><b>Framework</b></td><td>PyQt6</td></tr>\n<tr><td><b>Language</b></td><td>Python 3</td></tr>\n<tr><td><b>Image Processing</b></td><td>Pillow (PIL)</td></tr>\n<tr><td><b>Color Science</b></td><td>Custom Kubelka-Munk Implementation</td></tr>\n</table>\n\n<h4>Color Science References</h4>\n<ul>\n<li><b>Kubelka-Munk Theory</b> - Paint mixing simulation</li>\n<li><b>CIE LAB Color Space</b> - Perceptually uniform color mixing</li>\n<li><b>RYB Color Model</b> - Traditional artist color wheel</li>\n</ul>\n\n<h4>Special Thanks</h4>\n<ul>\n<li>The PyQt community for excellent documentation</li>\n<li>Color science researchers and educators</li>\n<li>Beta testers and early adopters</li>\n<li>Everyone who provided feedback and suggestions</li>\n</ul>\n\n<hr>\n\n<p style="text-align: center; color: {_t[\'accent_ink\']};">\n<b>RNV Color Mixer</b><br>\nBringing real-world paint mixing to the digital palette<br>\n© 2026 RNV Development. All rights reserved.\n</p>\n"""\n        \n        credits_label = QLabel(credits_text)\n',
             '        credits_label = QLabel(self._credits_html())\n        self._credits_label = credits_label\n')
    tree.sub('ui/about_dialog.py',
             '    def set_theme(self, is_dark: bool) -> None:\n        """Set the dialog theme (dark or light)."""\n',
             '    def _palette(self) -> dict:\n        """The palette the dialog is drawn in -- the choice _apply_theme() makes."""\n        return config.ThemeManager.DARK_THEME if self._is_dark else config.ThemeManager.LIGHT_THEME\n\n    def _style_version_label(self) -> None:\n        _t = self._palette()\n        self._version_label.setStyleSheet(f"font-size: 14px; color: {_t[\'accent_ink\']}; border: none; background: transparent;")\n\n    def _credits_html(self) -> str:\n        """The Credits tab\'s text. Its footer is in the palette\'s accent ink,\n        so _apply_theme() sets the text again when the palette changes."""\n        _t = self._palette()\n        return f"""\n<h3>Credits & Acknowledgments</h3>\n\n<h4>Development</h4>\n<p>RNV Color Mixer was created with passion for color science and \npractical tools for artists and designers.</p>\n\n<h4>Technologies</h4>\n<table width="100%">\n<tr><td width="40%"><b>Framework</b></td><td>PyQt6</td></tr>\n<tr><td><b>Language</b></td><td>Python 3</td></tr>\n<tr><td><b>Image Processing</b></td><td>Pillow (PIL)</td></tr>\n<tr><td><b>Color Science</b></td><td>Custom Kubelka-Munk Implementation</td></tr>\n</table>\n\n<h4>Color Science References</h4>\n<ul>\n<li><b>Kubelka-Munk Theory</b> - Paint mixing simulation</li>\n<li><b>CIE LAB Color Space</b> - Perceptually uniform color mixing</li>\n<li><b>RYB Color Model</b> - Traditional artist color wheel</li>\n</ul>\n\n<h4>Special Thanks</h4>\n<ul>\n<li>The PyQt community for excellent documentation</li>\n<li>Color science researchers and educators</li>\n<li>Beta testers and early adopters</li>\n<li>Everyone who provided feedback and suggestions</li>\n</ul>\n\n<hr>\n\n<p style="text-align: center; color: {_t[\'accent_ink\']};">\n<b>RNV Color Mixer</b><br>\nBringing real-world paint mixing to the digital palette<br>\n© 2026 RNV Development. All rights reserved.\n</p>\n"""\n\n    def set_theme(self, is_dark: bool) -> None:\n        """Set the dialog theme (dark or light)."""\n')
    tree.sub('ui/about_dialog.py',
             '                QPushButton:pressed {{\n                    background-color: {_l[\'accent\']};\n                    color: {_l[\'accent_text\']};\n                }}\n            """)\n    \n    def cleanup(self) -> None:\n',
             '                QPushButton:pressed {{\n                    background-color: {_l[\'accent\']};\n                    color: {_l[\'accent_text\']};\n                }}\n            """)\n\n        # RNV-CHART-RULINGS, 2026-09-26 (ruling 3). The dialog\'s two gold\n        # texts carry their colour inline, so the sheet above cannot reach\n        # them. Each was written once, with the palette of the moment --\n        # always dark, since the app passes its ui_handler where the flag\n        # belongs -- and nothing wrote it again: light mode showed dark\'s gold.\n        if getattr(self, \'_version_label\', None) is not None:\n            self._style_version_label()\n        if getattr(self, \'_credits_label\', None) is not None:\n            self._credits_label.setText(self._credits_html())\n    \n    def cleanup(self) -> None:\n')
    tree.sub('tests/test_derived_values.py',
             "have reached every opaque use and none of these. Each is now\ntranslucent_rgba(BASE, ALPHA) inside the template, and the palettes' three\ncheckbox grounds are translucent(BASE, ALPHA).\n",
             "have reached every opaque use and none of these. Each is now\ntranslucent_rgba(BASE, ALPHA) inside the template. The palettes' three\ncheckbox grounds were translucent(BASE, ALPHA) too, until a render proved\nnothing read them and they were removed -- RNV-CHART-RULINGS, 2026-09-26,\nwhich also moved the control panel's hand-sliced harmony wash onto\ntranslucent(). Both are held at the end of this file.\n")
    tree.sub('tests/test_derived_values.py',
             '    "COMBO_ALPHA": 0xBF,\n    "CHECKBOX_BG_ALPHA_DARK": 0xE6,\n    "CHECKBOX_BG_ALPHA_LIGHT": 0xC8,\n}\n',
             '    "COMBO_ALPHA": 0xBF,\n    "HARMONY_DESCRIPTION_ALPHA": 0x19,\n}\n')
    tree.sub('tests/test_derived_values.py',
             'PALETTE_MADE_OF = {\n    "DARK_THEME": ("APP_SURFACE_DARK", "CHECKBOX_BG_ALPHA_DARK"),\n    "LIGHT_THEME": ("WHITE", "CHECKBOX_BG_ALPHA_LIGHT"),\n    "IMAGE_THEME": ("APP_SURFACE_DARK", "CHECKBOX_BG_ALPHA_DARK"),\n}\n',
             '#: The palettes hold no derived value now. Their only ones were the three\n#: checkbox_bg grounds, which nothing read; see REMOVED_KEYS below.\nPALETTE_MADE_OF: dict[str, tuple[str, str]] = {}\n')
    tree.sub('tests/test_derived_values.py',
             '    assert derived == ["checkbox_bg"] * 3, derived\n',
             "    # The three checkbox_bg grounds were the palettes' only derived values,\n    # and nothing read them. Removed 2026-09-26 (RNV-CHART-RULINGS).\n    assert derived == [], derived\n")
    tree.sub('tests/test_derived_values.py',
             '    """Held BY NAME: each template call\'s (base, alpha) names, and each\n    palette entry\'s, are what this round made them. A value re-made from\n    another constant fails here even when the sheet still agrees with its\n    own source. The byte-for-byte before-and-after is tests/test_snapshots.py,\n    which compares all three rendered sheets whole."""\n    for template, made_of in MADE_OF.items():\n        names = sorted(_names(c) for c in _template_calls()[template])\n        assert names == sorted(made_of), f"{template}: {names}"\n    for palette, (base, alpha) in PALETTE_MADE_OF.items():\n        node = _palette_nodes()[palette]\n        entry = next(v for k, v in zip(node.keys, node.values)\n                     if isinstance(k, ast.Constant) and k.value == "checkbox_bg")\n        assert _names(entry) == (base, alpha), palette\n        live = getattr(C.ThemeManager, palette)["checkbox_bg"]\n        assert decompose(live) == (getattr(C, base).lower(), getattr(C, alpha))\n',
             '    """Held BY NAME: each template call\'s (base, alpha) names are what this\n    round made them. A value re-made from another constant fails here even\n    when the sheet still agrees with its own source. The byte-for-byte\n    before-and-after is tests/test_snapshots.py, which compares all three\n    rendered sheets whole. The palettes carried three derived entries\n    until 2026-09-26; the test that holds them removed is below."""\n    for template, made_of in MADE_OF.items():\n        names = sorted(_names(c) for c in _template_calls()[template])\n        assert names == sorted(made_of), f"{template}: {names}"\n    assert not PALETTE_MADE_OF, "a palette entry is derived again: hold it here"\n')
    tree.sub('tests/test_derived_values.py',
             'named colours still spelled in integers, where no "\n                        "register move reaches them:\\n  " + "\\n  ".join(strays))\n',
             'named colours still spelled in integers, where no "\n                        "register move reaches them:\\n  " + "\\n  ".join(strays))\n\n\n# RNV-CHART-RULINGS\n# ------------------------------------------ what nothing read, and the wash\n\n#: Palette keys nothing read, proven by render and removed: rulings 2 and 5\n#: of 2026-09-26.\nREMOVED_KEYS = ("checkbox_bg", "checkbox_border", "label_bg", "label_border")\n#: The two alphas that existed only for checkbox_bg.\nREMOVED_ALPHAS = ("CHECKBOX_BG_ALPHA_DARK", "CHECKBOX_BG_ALPHA_LIGHT")\n\n\ndef test_the_unread_palette_keys_stay_removed():\n    """RNV-CHART-RULINGS, rulings 2 and 5. Four keys in all three palettes\n    painted nothing: checkbox_bg, derived at 0xE6 and 0xC8, and\n    checkbox_border, label_bg and label_border -- the last three spelled in\n    LIGHT_THEME with the CSS names gray, white and black, which a hex census\n    cannot see. A render set all twelve entries to #ff00ff. No pixel changed\n    in 105 captures of the main window, the control panel and the About\n    dialog in all three modes, and no text changed in 1,020 stylesheet and\n    palette entries, while a control that moved DARK\'s canvas_bg changed 1\n    capture and 10 entries. So they went, with the two alphas that existed\n    only for checkbox_bg.\n\n    Gone from every palette and named nowhere in the application. A key\n    brought back is a colour on no element, and has to be decided rather\n    than inherited."""\n    for palette in PALETTES:\n        back = [k for k in REMOVED_KEYS if k in getattr(C.ThemeManager, palette)]\n        assert not back, f"{palette} declares {back} again"\n    for name in REMOVED_ALPHAS:\n        assert not hasattr(C, name), f"utils.config declares {name} again"\n    sources = list(_sources())\n    assert any(rel.as_posix() == "utils/config.py" for rel, _ in sources), (\n        "the sweep cannot see the palettes, so it proves nothing")\n    named = [f"{rel}:{node.lineno}  {node.value}" for rel, tree in sources\n             for node in ast.walk(tree)\n             if isinstance(node, ast.Constant) and isinstance(node.value, str)\n             and node.value in REMOVED_KEYS]\n    named += [f"{rel}:{node.lineno}  {node.id}" for rel, tree in sources\n              for node in ast.walk(tree)\n              if isinstance(node, ast.Name) and node.id in REMOVED_ALPHAS]\n    assert not named, "named again:\\n  " + "\\n  ".join(named)\n\n\ndef test_the_harmony_description_derives_its_wash(qapp):\n    """RNV-CHART-RULINGS, ruling 4. The control panel\'s harmony description\n    sits on a wash of its own accent ink. It was rgba(r, g, b, 0.1) from\n    channels sliced out of the hex by hand, the one derived value in the\n    fleet that did not go through a helper. Now it is translucent(accent,\n    HARMONY_DESCRIPTION_ALPHA), and 0x19 is the byte Qt makes of 0.1:\n    measured on five grounds under both inks, and the panel renders pixel for\n    pixel as it did.\n\n    Held twice: in the source, the helper by name and no rgba() built by hand\n    left in the function; and in the sheet the function actually sets, in\n    both palettes, the wash taken apart to (accent_ink, 0x19)."""\n    from types import SimpleNamespace\n\n    from PyQt6.QtWidgets import QLabel\n\n    from core import package_d_panel as panel_module\n    tree = ast.parse((ROOT / "core" / "package_d_panel.py").read_text(encoding="utf-8-sig"))\n    fn = next(n for n in tree.body\n              if isinstance(n, ast.FunctionDef) and n.name == "_style_harmony_description")\n    body = fn.body[1:] if ast.get_docstring(fn) else fn.body\n    code = "\\n".join(ast.unparse(s) for s in body)\n    calls = [ast.unparse(c) for s in body for c in ast.walk(s)\n             if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "translucent"]\n    assert calls == ["config.translucent(accent, config.HARMONY_DESCRIPTION_ALPHA)"], calls\n    assert "rgba(" not in code and "[1:3]" not in code, "the wash is built by hand again"\n    for is_dark, palette in ((True, "DARK_THEME"), (False, "LIGHT_THEME")):\n        panel = SimpleNamespace(_is_dark=is_dark, harmony_description=QLabel())\n        panel_module._style_harmony_description(panel)\n        sheet = panel.harmony_description.styleSheet()\n        wash = re.search(r"background-color:\\s*([^;]+);", sheet).group(1).strip()\n        ink = getattr(C.ThemeManager, palette)["accent_ink"].lower()\n        assert decompose(wash) == (ink, C.HARMONY_DESCRIPTION_ALPHA), (palette, sheet)\n')
    if (tree.root / 'tests/test_mode_switch_restyle.py').exists():
        raise Stop('tests/test_mode_switch_restyle.py' + ' exists already: this round creates it', EXIT_CANNOT_RUN)
    tree.write('tests/test_mode_switch_restyle.py', '"""RNV-CHART-RULINGS, ruling 3 of 2026-09-26: every widget follows a mode switch.\n\nWHAT THE CHART FOUND. Reading back every stylesheet and palette the app sets,\nmode by mode, found widgets in light mode carrying dark mode\'s colours:\n\n  * the preview\'s border               stale: only _update_preview() writes it,\n                                       and a mode switch did not call it, so the\n                                       border waited for the next colour mixed;\n  * the colour slots\' swatch borders,  always dark: _update_swatch_display()\n    and their gold hover and press     asked a FRESH ThemeManager, whose mode is\n                                       always dark, however often set_theme() ran;\n  * the control panel\'s nine shortcut  always dark: styled while the panel was\n    key badges                         built, before set_theme() had run, and\n                                       set_theme() never reached them;\n  * the About dialog\'s gold text, the  always dark: written once, when the\n    version line and the credits       dialog was built -- and the app passes\n    footer                             its ui_handler where the dark flag\n                                       belongs, which is truthy.\n\nEach test below drives the app the way a person does -- the theme button for\nthe main window and the panel, the About opener for the About dialog, which\nthe app restyles each time it opens it -- and asks every widget, in every mode\nthe cycle offers, for the mode\'s own values. Dark and image draw the panel and\nthe About dialog from the dark palette, as the app has always done.\n"""\nfrom __future__ import annotations\n\nimport pytest\nfrom PyQt6.QtWidgets import QApplication, QLabel\n\nfrom utils.config import ThemeManager\n\npytestmark = pytest.mark.integration\n\n#: The Quick Actions tab\'s shortcut badges, by the text each one shows.\nSHORTCUT_KEYS = ("Ctrl+O", "Ctrl+S", "Ctrl+C", "Ctrl+N", "Ctrl+P or Ctrl+,",\n                 "Ctrl+/", "Ctrl+Shift+C", "F11", "F12")\n\n\ndef _cycle(app_window):\n    """Click the theme button until the cycle comes back round to where it\n    started, yielding the mode after each click. Dark, light and image when\n    the image assets are present; dark and light when they are not."""\n    start = app_window.ui_handler.theme_manager.current_theme\n    for _ in range(4):\n        app_window._on_theme_button_clicked()\n        QApplication.processEvents()\n        mode = app_window.ui_handler.theme_manager.current_theme\n        yield mode\n        if mode == start:\n            return\n    raise AssertionError("the theme cycle never came back round to its start")\n\n\ndef _dialog_palette(mode: str) -> dict:\n    """The panel and the About dialog draw dark and image from DARK_THEME."""\n    return ThemeManager.LIGHT_THEME if mode == "light" else ThemeManager.DARK_THEME\n\n\ndef test_the_cycle_reaches_light_mode(app_window):\n    """Every test here would pass vacuously if the cycle never left dark."""\n    assert "light" in list(_cycle(app_window))\n\n\ndef test_the_preview_border_follows_every_mode(app_window):\n    for mode in _cycle(app_window):\n        theme = app_window.ui_handler.get_current_theme_dict()\n        sheet = app_window.preview_label.styleSheet()\n        assert f"solid {theme[\'border_color\']};" in sheet, (\n            f"{mode}: the preview\'s border is not {theme[\'border_color\']}:\\n{sheet}")\n\n\ndef _assert_swatch(slot, theme: dict, where: str) -> None:\n    sheet = slot.swatch_btn.styleSheet()\n    plate, _, rest = sheet.partition("QPushButton:hover")\n    hover, _, pressed = rest.partition("QPushButton:pressed")\n    edge = f"{theme[\'slot_border_width\']}px solid"\n    assert f"{edge} {theme[\'slot_border\']};" in plate, f"{where}: border\\n{sheet}"\n    assert f"{edge} {theme[\'accent\']};" in hover, f"{where}: hover\\n{sheet}"\n    assert f"{edge} {theme[\'accent\']};" in pressed, f"{where}: pressed\\n{sheet}"\n\n\ndef test_the_slot_swatches_follow_every_mode(app_window):\n    assert app_window.slots, "the app starts with no slots, so this sees nothing"\n    for mode in _cycle(app_window):\n        theme = app_window.ui_handler.get_current_theme_dict()\n        for i, slot in enumerate(app_window.slots):\n            _assert_swatch(slot, theme, f"{mode}, slot {i}")\n\n\ndef test_a_swatch_keeps_its_mode_through_a_colour_change_and_a_new_slot(app_window):\n    """A colour change repaints the swatch without being told the mode, and\n    a slot added in light mode is built there: both must stay in the mode."""\n    for mode in _cycle(app_window):\n        if mode == "light":\n            break\n    theme = app_window.ui_handler.get_current_theme_dict()\n    app_window.slots[0].set_color((12, 120, 200))\n    _assert_swatch(app_window.slots[0], theme, "light, after a colour change")\n    app_window.add_color_slot()\n    _assert_swatch(app_window.slots[-1], theme, "light, a slot added there")\n\n\ndef test_the_panel_key_badges_follow_every_mode(app_window):\n    app_window.open_package_d_panel()\n    panel = app_window._package_d_panel\n    badges = [w for w in panel.findChildren(QLabel) if w.text() in SHORTCUT_KEYS]\n    assert len(badges) == len(SHORTCUT_KEYS), [w.text() for w in badges]\n    try:\n        for mode in _cycle(app_window):\n            t = _dialog_palette(mode)\n            for badge in badges:\n                sheet = badge.styleSheet()\n                assert f"background-color: {t[\'accent\']};" in sheet, (\n                    f"{mode}: {badge.text()!r} plate\\n{sheet}")\n                assert f"color: {t[\'accent_text\']};" in sheet, (\n                    f"{mode}: {badge.text()!r} text\\n{sheet}")\n    finally:\n        panel.close()\n\n\ndef test_the_about_dialog_gold_follows_every_mode(app_window):\n    app_window.open_about_dialog()\n    about = app_window._about_dialog\n    labels = about.findChildren(QLabel)\n    version = [w for w in labels if w.text().startswith("Version ")]\n    credits = [w for w in labels if "Credits &amp; Acknowledgments" in w.text()\n               or "Credits & Acknowledgments" in w.text()]\n    assert len(version) == 1 and len(credits) == 1, (len(version), len(credits))\n    about.close()\n    try:\n        for mode in _cycle(app_window):\n            app_window.open_about_dialog()\n            assert app_window._about_dialog is about, "the About dialog was rebuilt"\n            ink = _dialog_palette(mode)["accent_ink"]\n            assert f"color: {ink};" in version[0].styleSheet(), (\n                f"{mode}: the version line\\n{version[0].styleSheet()}")\n            assert f"color: {ink};" in credits[0].text(), f"{mode}: the credits footer"\n            about.close()\n    finally:\n        about.close()\n')


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
    removed = ("checkbox_bg", "checkbox_border", "label_bg", "label_border")
    old_cfg, new_cfg = _original(tree, "utils/config.py"), tree.read("utils/config.py")

    # ruling 2 and 5: four keys out of all three palettes, and nothing else moves
    def palettes(src):
        cls = next(n for n in ast.parse(src).body
                   if isinstance(n, ast.ClassDef) and n.name == "ThemeManager")
        out, rest = {}, []
        for node in cls.body:
            t = (node.targets[0] if isinstance(node, ast.Assign) else
                 node.target if isinstance(node, ast.AnnAssign) else None)
            if getattr(t, "id", None) in ("DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"):
                out[t.id] = _entries(node.value)
            else:
                rest.append(ast.dump(node))
        return out, rest
    (before, rest_b), (after, rest_a) = palettes(old_cfg), palettes(new_cfg)
    assert rest_a == rest_b, "ThemeManager changed outside its three palettes"
    assert set(before) == set(after) == {"DARK_THEME", "LIGHT_THEME", "IMAGE_THEME"}
    for name in before:
        assert set(removed) <= set(before[name]), f"{name} never had all four keys"
        assert after[name] == {k: v for k, v in before[name].items()
                               if k not in removed}, f"{name} moved beyond the four keys"
    assert set(after["DARK_THEME"]) == set(after["LIGHT_THEME"]) == set(after["IMAGE_THEME"]), (
        "the three palettes' key sets differ; the locked suite requires them equal")
    old_top, new_top = _top(old_cfg), _top(new_cfg)
    assert set(old_top) - set(new_top) == {"CHECKBOX_BG_ALPHA_DARK", "CHECKBOX_BG_ALPHA_LIGHT"}
    assert set(new_top) - set(old_top) == {"HARMONY_DESCRIPTION_ALPHA"}
    assert new_top["HARMONY_DESCRIPTION_ALPHA"] == ast.dump(ast.Constant(0x19))
    moved = [n for n in old_top if n in new_top and old_top[n] != new_top[n]]
    assert not moved, f"module-level values moved: {moved}"

    # ruling 4: the wash through the helper, the rest of the sheet as it was
    old_p, new_p = _original(tree, "core/package_d_panel.py"), tree.read("core/package_d_panel.py")
    fn = _function(new_p, "_style_harmony_description")
    assert [ast.unparse(c) for c in _calls(fn, "translucent")] == [
        "config.translucent(accent, config.HARMONY_DESCRIPTION_ALPHA)"]
    code = "\n".join(ast.unparse(s) for s in fn.body[1:])
    assert "rgba(" not in code and "[1:3]" not in code, "the wash is still sliced by hand"
    old_parts = _sheet_parts(_calls(_function(old_p, "_style_harmony_description"),
                                    "setStyleSheet")[0])
    new_parts = _sheet_parts(_calls(fn, "setStyleSheet")[0])
    assert "".join(old_parts).replace("background-color: rgba(, , , 0.1); ",
                                      "background-color: ; ") == "".join(new_parts), (
        old_parts, new_parts)

    # ruling 3, the panel: the badge sheet moved into a helper, text unchanged
    old_tab = _function(old_p, "_create_quick_actions_tab", "PackageDPanel")
    badge = _function(new_p, "_style_key_badge")
    old_sheet = next(c for c in _calls(old_tab, "setStyleSheet")
                     if "accent_text" in ast.unparse(c))
    new_sheet = _calls(badge, "setStyleSheet")[0]
    assert _sheet_parts(old_sheet) == _sheet_parts(new_sheet), "the badge sheet's text moved"
    assert ast.unparse(old_sheet.args[0]).replace("_t_k[", "t[") == ast.unparse(new_sheet.args[0])
    assert "_style_key_badge(self, key_label)" in ast.unparse(
        _function(new_p, "_create_quick_actions_tab", "PackageDPanel"))
    assert "_style_key_badge(self, _badge)" in ast.unparse(
        _function(new_p, "_apply_widget_stylesheet", "PackageDPanel"))

    # ruling 3, the swatches and the preview
    slot = tree.read("core/color_slot.py")
    assert "self._theme = theme" in ast.unparse(_function(slot, "set_theme", "ColorSlot"))
    assert "getattr(self, '_theme', None)" in ast.unparse(
        _function(slot, "_update_swatch_display", "ColorSlot"))
    main = tree.read("RNV_Color_Mixer.py")
    assert "self._update_preview(self.current_mixed_color)" in ast.unparse(
        _function(main, "_apply_theme_to_all", "ColorMixerApp"))

    # ruling 3, the About dialog: the same text, written again on each theme
    old_a, new_a = _original(tree, "ui/about_dialog.py"), tree.read("ui/about_dialog.py")
    old_credits = next(n.value for n in ast.walk(_function(old_a, "_create_credits_tab", "AboutDialog"))
                       if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "credits_text")
    new_credits = next(n.value for n in ast.walk(_function(new_a, "_credits_html", "AboutDialog"))
                       if isinstance(n, ast.Return))
    assert ast.dump(old_credits) == ast.dump(new_credits), "the credits text changed in the move"
    old_ver = next(c for c in _calls(_function(old_a, "_create_header", "AboutDialog"), "setStyleSheet")
                   if "accent_ink" in ast.unparse(c))
    new_ver = _calls(_function(new_a, "_style_version_label", "AboutDialog"), "setStyleSheet")[0]
    assert ast.dump(old_ver.args[0]) == ast.dump(new_ver.args[0]), "the version sheet changed"
    tail = ast.unparse(_function(new_a, "_apply_theme", "AboutDialog").body[-2:])
    assert "self._style_version_label()" in tail and "self._credits_html()" in tail

    # nothing in the files this round edits names what was removed
    alphas = ("CHECKBOX_BG_ALPHA_DARK", "CHECKBOX_BG_ALPHA_LIGHT")
    for rel in ("utils/config.py", "core/package_d_panel.py", "core/color_slot.py",
                "RNV_Color_Mixer.py", "ui/about_dialog.py"):
        for node in ast.walk(ast.parse(tree.read(rel))):
            assert not (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and node.value in removed), f"{rel} still names {node.value!r}"
            assert not (isinstance(node, ast.Name) and node.id in alphas), (
                f"{rel} still names {node.id}")

    # the guards
    for rel, tests in (("tests/test_derived_values.py", 2), ("tests/test_mode_switch_restyle.py", 6)):
        src = tree.read(rel)
        assert SENTINEL in src, f"{rel} does not carry {SENTINEL}"
        found = sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                    for n in ast.parse(src).body)
        assert found >= tests, (rel, found)
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
