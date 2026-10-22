"""
Colors for the RNV Color Mixer application (PyQt6).

Every color the application draws lives here: the brand's, those derived from
them, and the application's own; the three theme palettes ThemeManager
serves; and the helpers that make a color. Every app in the fleet keeps its
colors in utils/colors.py (#63 A, 2026-10-18).
"""
# RNV-COLOR-SYNC (2026-10-16). Every color value below whose line ends
# "# brand: <name>" or "# app-owned" is written by tools/sync_colors.py from
# brand_map.json: a brand name's value from rnv-brand at the commit pinned in
# tests/requirements-dev.txt, an app-owned value from the map, with its reason.
# To change one, change the map and run `python tools/sync_colors.py`. A value
# edited here is put back by the next sync, and tests/test_colors_in_sync.py
# fails until then. COLORS.md is the chart of them.

from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from utils.config import ThemeManager

# Color settings
DEFAULT_COLOR = (200, 200, 200)  # app-owned

# Initial state — the color shown before the user mixes anything.
# Centralized here so a single change updates preview swatch, hex label,
# rgb label, and any other display that starts at "no color yet".
INITIAL_COLOR_TUPLE = (0, 0, 0)  # app-owned
INITIAL_COLOR_HEX   = "#000000"  # app-owned
INITIAL_COLOR_RGB   = "rgb(0,0,0)"  # app-owned

# Debug overlay colors — diagnostic identifiers for the F12 overlay system.
# Red = main app window overlay, Blue = slots panel overlay.
# Centralized so both creation sites (toggle function + settings apply) stay in sync.
DEBUG_OVERLAY_COLORS = {
    'app_window':  'rgba(255, 80, 80, 220)',
    'slots_panel': 'rgba(80, 80, 255, 220)',
    # RNV-NAMED-AND-USED (2026-10-04): the control panel's two, and the
    # tint an overlay takes when it is given none. Each was written out
    # where it is used; the same values.
    'panel':       'rgba(80, 255, 80, 220)',
    'tabs':        'rgba(255, 200, 80, 220)',
    'default':     'rgba(255, 100, 100, 200)',
    # and what every overlay writes and edges itself in, whatever its tint.
    # The text was the CSS name `white`, which is this value.
    'text':        '#ffffff',
    'edge':        'rgba(255, 255, 255, 230)',
}

# ---------------------------------------------------------------- brand gold
# Mirrored from RNVizion/rnv-brand engine/brand.py. Do not hand-write a gold
# here: derive it, so that a change to the base carries.
#
# The register holds TWO golds and derives the rest. Each mode renders the
# registered gold plus ONE derivative:
#
#   light   BRAND_DARK_GOLD          fills, borders, pressed
#           BRAND_DARK_GOLD_DEEP     text, and hover (which moves DEEPER on a
#                                    light ground -- away from it, not toward)
#   dark    BRAND_GOLD               fills, borders, pressed, text
#           BRAND_GOLD_HOVER         hover (lighter, again away from the ground)
#
# Pressed returns to the accent in both modes. On light that is forced -- no
# darker pressed shade keeps black legible on it. On dark the register records
# the question as OPEN and permits either; this app takes the accent, which is
# what holds the count at two and matches rnv-color-picker and
# rnv-text-transformer.
#
# COVERAGE BOUNDARY: BRAND_DARK_GOLD_DEEP carries text down to #e8e8e8 and no
# further. Below that, gold does not carry text -- a ruling, not a gap. Going
# darker does not help: -29 clears #d0d0d0 and then fails black-on-fill at
# 3.0219, the same exclusion one step down.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    Uniform per-channel, which holds hue exactly -- BRAND_DARK_GOLD and its
    derivative both measure 42.4 degrees. Non-uniform steps do not, which is
    why the hand-written variants this replaces all drifted in hue.
    """
    r, g, b = _to_rgb(hex_color)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, c + step)) for c in (r, g, b))


def _hex6(hex_color: str) -> str:
    """The six hex digits of a color, or ValueError. Shared by the two
    helpers below so they refuse exactly the same inputs."""
    h = hex_color.lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"{hex_color!r} is not a six-digit hex color")
    return h


def _alpha_byte(alpha: int) -> int:
    """An alpha as the 0-255 byte, or an error. A fraction is refused, not
    scaled: Qt TRUNCATES a fractional alpha in a stylesheet -- 0.7 is 178, not
    179 -- and a helper that rounded would move a pixel inside a respelling."""
    if isinstance(alpha, bool) or not isinstance(alpha, int):
        raise TypeError(f"alpha {alpha!r} is not an int byte")
    if not 0 <= alpha <= 255:
        raise ValueError(f"alpha {alpha} is outside 0-255")
    return alpha


def translucent(hex_color: str, alpha: int) -> str:
    """A color at an alpha, as Qt's eight-digit #aarrggbb -- ALPHA FIRST.

    A value computed from another value is computed in code; a written-down
    derivative is orphaned the moment its source moves, and nothing says so.
    #aarrggbb is the one spelling valid in a stylesheet AND in QColor(), which
    reads rgba() as INVALID and paints it opaque black. Lower case, as the
    register writes hex; rnv-icon-builder's helper of the same name agrees.
    """
    return "#%02x%s" % (_alpha_byte(alpha), _hex6(hex_color).lower())


def translucent_rgba(hex_color: str, alpha: int) -> str:
    """The same derivation spelled rgba(r, g, b, a) -- FOR THE STYLESHEET
    TEMPLATES ONLY, where a value can never reach QColor().

    Two reasons it exists here. The locked suite asserts "rgba(" is in
    IMAGE_STYLESHEET, and the lock stands. And tests/test_snapshots.py compares
    the rendered sheets byte for byte, so the templates keep the spelling they
    had and the snapshots move only where a pixel was ruled to.
    tests/test_derived_values.py fails if it is used anywhere else.
    """
    h = _hex6(hex_color)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {_alpha_byte(alpha)})"


BRAND_GOLD: Final[str] = "#d2bc93"  # brand: APP.accent
BRAND_DARK_GOLD: Final[str] = "#8c7337"  # brand: APP.accent-light-mode

# Derived. Steps published in rnv-brand engine/brand.py, rev 17.
BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)   # #7e6529
BRAND_GOLD_HOVER: Final[str] = lighten(BRAND_GOLD, 13)             # #dfc9a0

# Aliases. Named so every rendered hex has a key, even where it repeats.
BRAND_DARK_GOLD_HOVER: Final[str] = BRAND_DARK_GOLD_DEEP
BRAND_DARK_GOLD_PRESSED: Final[str] = BRAND_DARK_GOLD
BRAND_GOLD_PRESSED: Final[str] = BRAND_GOLD

# RNV-NAMED-AND-USED (2026-10-04): the two golds as integer triples stood
# here, and nothing in the application read either. A name is kept for
# what uses it; _to_rgb() above still derives a triple when one is needed.

# Declarative provenance, read by tests/test_brand_mirror.py. A classification
# that lives only in a test drifts from the thing it classifies.
GOLD_PROVENANCE: Final[dict[str, str]] = {
    "BRAND_GOLD": "register",
    "BRAND_DARK_GOLD": "register",
    "BRAND_DARK_GOLD_DEEP": "derived",
    "BRAND_GOLD_HOVER": "derived",
    "BRAND_DARK_GOLD_HOVER": "alias",
    "BRAND_DARK_GOLD_PRESSED": "alias",
    "BRAND_GOLD_PRESSED": "alias",
}

# ==================== APP NEUTRALS ====================
#
# WHY THESE EXIST. The three stylesheet templates, in utils/config.py, used to
# carry 120 hex literals -- 40 dark, 50 light, 30 image -- while the golds
# twenty lines up were already interpolated from constants. A literal cannot
# follow its base: move a value here and the templates keep the old one,
# silently, with nothing to report it. Every rendered hex now has a key, which
# is the same rule the gold aliases above were written for.
#
# NAMED BY ROLE, NOT BY BYTE. A step is named for the job it does, and where
# one value does two jobs the comment says both rather than minting a second
# constant. The one exception is APP_BTN_HOVER_INVERSE, which is assigned FROM
# its base rather than repeating the value, so the two move together.
#
# THIS IS A REWIRE, NOT A RETUNE. Every value below is exactly what the
# templates already rendered. tests/test_snapshots.py compares the three
# stylesheets byte-for-byte against frozen references; if those pass without
# regeneration, nothing moved.

TRUE_BLACK: Final[str] = "#000000"  # brand: PERMANENT.black
"""Window and scroll-area ground in dark; primary text in light; the label on
a pressed control in dark; the selection foreground in every mode."""

WHITE: Final[str] = "#ffffff"  # brand: PERMANENT.white
"""Control surface in light -- button, input, combo, scroll area -- and the
label on a pressed control in light."""

# ---- dark and image ----
APP_SURFACE_DARK: Final[str] = "#1a1a1a"  # brand: APP.panel
"""Control surface in dark and image: button, input, combo, status bar, and
the slider groove."""

APP_BORDER_DARK: Final[str] = "#333333"  # brand: APP.border
"""Every border in dark and image. Also the hover ground and the splitter
handle -- in dark the hover fill deliberately equals the border step, so a
hovered control reads as its own outline filling in."""

APP_TEXT_DARK: Final[str] = "#dddddd"  # brand: APP.text
"""Primary text in dark and image. Also the slider handle, which takes the
brightest step in the ramp rather than a color of its own."""

# RNV-NAMED-AND-USED (2026-10-04): a name for the dark slider handle's hover,
# gray(14), stood here. No sheet painted it: every slider's hovered handle
# takes the accent. It went, and with it the one coincidence it made, a
# second name on APP_ITEM_HOVER_LIGHT's #eeeeee.

APP_CANVAS_DARK: Final[str] = "#0a0a0a"  # brand: APP.canvas
"""engine/brand.py APP["canvas"]. The ground BELOW the panel in dark and image:
the mixing canvas, and the selected tab, which sits flush with it.

Unnamed until 2026-08-29 because the 2026-08-27 rewire's scope was the three
stylesheet templates and this value has never appeared in one -- it is reached
only through ThemeManager's dicts, which seven modules build their own QSS
from.

REGISTERED 2026-08-29 in rnv-brand rev 22, and app-owned here until then. It is
the n=-1 rung of the dark surface ladder:

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

STILL NOT WEB_BLACK, and the distinction is now sharper rather than gone. This
docstring used to say "#0a0a0a is app-owned; the register's canvas is WEB_BLACK
#0a0a0f". The second half was the part that mattered and it survives: the web
ground is a different value, one byte away in the blue channel alone. App
neutrals are pure gray, R = G = B, without exception, and the web carries a
tint the apps do not. That byte is why invert(#0a0a0a) = #f5f5f5 once looked
like a light-ground rule and was not -- the register's canvas inverts to
#f5f5f0. Two canvases one byte apart, deliberately.

MIRRORED, not app-owned -- pinned in tests/test_app_mirror.py alongside the
other register values, so a move upstream is caught here."""

APP_CARD_DARK: Final[str] = "#2a2a2a"  # brand: APP.card
"""engine/brand.py APP["card"]. The raised secondary surface in dark and
image: panel_secondary in the About dialog and the fine-tune panel, and the
ground of the custom tooltip.

MIRRORED, not app-owned -- it is pinned in tests/test_app_mirror.py alongside
the other register values, so a move upstream is caught here."""

APP_PANEL_HOVER_DARK: Final[str] = "#3a3a3a"  # brand: APP.panel-hover
"""engine/brand.py APP["panel-hover"]. Panel hover in dark and image, and the
n=+2 rung of the dark surface ladder.

REGISTERED 2026-08-29 in rnv-brand rev 22. THE REGISTER RULED IT, AND THE
DOUBT THIS DOCSTRING USED TO RECORD WAS MISPLACED. It said the ladder was not
published because "it yields #3a3a3a while APP["border"] is #333333, so two
rungs are in use and two are not" -- treating the border as a missing rung.
It is not a rung at all. #333333 is gray(3) on the INK grid, which governs inks
and EDGES, and a border is an edge. The two families were being compared to
each other. The ladder was complete the whole time:

    BRAND_BLACK + n * 0x10,  n in -1..+2
    #0a0a0a canvas   #1a1a1a panel   #2a2a2a card   #3a3a3a panel-hover

MIRRORED, not app-owned -- pinned in tests/test_app_mirror.py."""

APP_HINT_DARK: Final[str] = "#888888"  # app-owned
"""Hint text in dark and image. gray(8) on the published ink grid, and the
same step the other four apps use for muted text."""

# ---- light ----
APP_WINDOW_LIGHT: Final[str] = "#f5f5f5"  # brand: APP.surface-light-3
"""Window ground in light, the status bar, and the scrollbar track."""

APP_BORDER_LIGHT: Final[str] = "#cccccc"  # app-owned
"""Every border in light. Also the scrollbar handle at rest and the splitter
handle, on the same reasoning as APP_BORDER_DARK."""

APP_ITEM_HOVER_LIGHT: Final[str] = "#eeeeee"  # brand: APP.hover-light
"""engine/brand.py APP["hover-light"]. gray(14). The light interaction plate:
the combo-box item under the cursor and the panel hover. The LIST hover, not
the button hover -- those are different schemes, see APP_BTN_HOVER_INVERSE.

REGISTERED 2026-08-30 in rnv-brand rev 23. It was registered a day earlier as
#e8e8e8 and moved here before any app was wired to it, because #e8e8e8 is the
ground BRAND_DARK_GOLD_DEEP is calibrated against -- rev 24 registered that
role as GOLD_TEXT_GROUND_FLOOR. A plate on the value the gold is pinned to
clears the 4.5 text floor by 0.0334 and fails the moment the gold moves one
step. This value clears by 0.2875. A boundary is not a plate.

THE NAME STAYS AS IT IS. This app names neutrals by role AND mode because it
registers a light set beside the dark one, and tests/test_app_mirror.py maps
those names to register keys explicitly rather than renaming eleven constants
to fit a convention that would then be wrong within this file. The mirror is
what carries the ownership, not the spelling.

MIRRORED, not app-owned -- pinned in tests/test_app_mirror.py."""

APP_HANDLE_LIGHT: Final[str] = "#666666"  # app-owned
"""Slider handle at rest, light."""

APP_HINT_LIGHT: Final[str] = "#666666"  # app-owned
"""gray(6). Hint and muted text in light -- the step the other four apps
use for muted text in light, as APP_HINT_DARK is in dark.

SPLIT, NOT RENAMED, 2026-09-27 (RNV-MUTED-DESCRIPTIONS). LIGHT text_hint read
APP_HANDLE_LIGHT, the same hex doing another job. When the control panel's
ten descriptions joined the fine-tune hint on this key, text would have
moved every time the slider handle did."""

APP_HANDLE_EDGE_LIGHT: Final[str] = "#888888"  # app-owned
"""The emphasized edge of a light handle: the slider handle's border.

RNV-GOLD-HOVER, 2026-09-12: the light scrollbar handle on hover used to read
this too, and now takes BRAND_DARK_GOLD with every other hover on the main
surface. What is left is the border, and the light palette's `menu_disabled`.
The value was #999999, a step this constant held alone in the whole fleet;
against the white menu ground #888888 lifts disabled menu text from 2.85 to
3.54."""

APP_CONTROL_DIM: Final[str] = "#555555"  # app-owned
"""Two unrelated jobs on one step: the light slider handle when hovered, and
the image-mode checkbox indicator border. Worth knowing that dark mode draws
that same checkbox border with APP_BORDER_DARK while rnv-color-picker and
rnv-icon-builder use this step in both -- an inconsistency this pass records
and does not change, because nothing here may move a pixel."""

# ---- the inverse button scheme, both modes ----
APP_BTN_HOVER_INVERSE: Final[str] = APP_BORDER_DARK
"""The basic button's hover ground. Light mode borrows the dark step on
purpose: the scheme inverts on hover, and the label stays put. Assigned from
APP_BORDER_DARK rather than repeating the value so the two cannot drift
apart."""

APP_BTN_PRESSED: Final[str] = "#444444"  # app-owned
"""The basic button's pressed fill, identical in all three modes. The label
flips instead -- TRUE_BLACK on dark, WHITE on light."""

# ---- RNV-MIXER-WIRING (2026-09-06): four names for values the palettes
# ---- already carried as literals. Nothing here is a new color.

APP_CHROME_DARK: Final[str] = "#444444"  # app-owned
"""gray(4). The structural gray of a control in dark and image: the slider
groove, and the border and separator of a menu -- and, from 2026-09-25, the
image-mode scrollbar handle at SCROLLBAR_HANDLE_ALPHA. That handle was
#505050, which RNV-COLLAPSE-505050 ruled onto gray(4) -- GRAY_44 in the
other applications -- and it is resting chrome, not a pressed button.

SPLIT, NOT RENAMED. APP_BTN_PRESSED is the same hex and stays exactly as it
is. That one is a button in its PRESSED state; this one is a resting trough
and a resting edge. Wiring a groove through the pressed name would claim an
interaction state for a piece of chrome on the strength of a shared byte --
the same reasoning this file gives for APP_MENU_DIM_DARK sharing gray(6)
with APP_HANDLE_LIGHT."""

APP_CHROME_LIGHT: Final[str] = "#e0e0e0"  # app-owned
"""The same job in light: the slider groove. Darker than the #f5f5f5 panel, so
the groove reads as recessed rather than raised -- which is why it is this
value and not input_bg's #ffffff.

Soft on its own at 1.21:1 against the panel; the groove's 1px APP_BORDER_LIGHT
edge does most of the defining. That is the appearance the light fine-tune
slider already had, and this pass gives it to the other two sliders as well."""

APP_TEXT_DIM_LIGHT: Final[str] = "#aaaaaa"  # brand: APP.text-dim
"""gray(10). Disabled text in light. The mirror of APP_CONTROL_DIM's gray(5)
by the ink grid's own rule -- invert(n) = 15 - n, and 5 + 10 = 15 -- which is
why the pair is exact and nobody planned it.

RENAMED 2026-10-17 (#51 A) from APP_DIM_LIGHT. It colors text, and it is the
register's text-dim, which the picker, icon builder and palette manager
call APP_TEXT_DIM; this application adds the mode, as APP_TEXT_DARK does."""

APP_MENU_DIM_DARK: Final[str] = "#666666"  # app-owned
"""gray(6). The disabled menu label in dark and image.

SPLIT, NOT RENAMED. APP_HANDLE_LIGHT is the same hex and keeps its own job.
Wiring this through that name would have put a _LIGHT-suffixed constant in the
DARK palette, and named a menu label after a slider handle. Two wrongs out of
one shared byte."""


# Declarative provenance, read by tests/test_neutral_ramp.py, in the same
# shape as GOLD_PROVENANCE above. A classification that lives only in a test
# drifts from the thing it classifies.
NEUTRAL_PROVENANCE: Final[dict[str, str]] = {
    "TRUE_BLACK": "anchor",
    "WHITE": "anchor",
    "APP_SURFACE_DARK": "step",
    "APP_BORDER_DARK": "step",
    "APP_TEXT_DARK": "step",
    "APP_CANVAS_DARK": "step",
    "APP_CARD_DARK": "step",
    "APP_PANEL_HOVER_DARK": "step",
    "APP_HINT_DARK": "step",
    "APP_WINDOW_LIGHT": "step",
    "APP_BORDER_LIGHT": "step",
    "APP_ITEM_HOVER_LIGHT": "step",
    "APP_HANDLE_LIGHT": "step",
    "APP_HANDLE_EDGE_LIGHT": "step",
    "APP_HINT_LIGHT": "step",
    "APP_CONTROL_DIM": "step",
    "APP_BTN_PRESSED": "step",
    "APP_BTN_HOVER_INVERSE": "alias",
    "APP_CHROME_DARK": "step",
    "APP_CHROME_LIGHT": "step",
    "APP_TEXT_DIM_LIGHT": "step",
    "APP_MENU_DIM_DARK": "step",
}


# ==================== COMPOSITE ALPHAS ====================
# A composite is a named color AT AN ALPHA. The color half is a name, so a
# register move reaches it; the alpha half is one of these, so the same move
# carries every alpha form of the color. Each byte is the one its literal
# already carried -- the dark handle's measured, since it was written as 0.7.
#
# SEVERAL BYTES REPEAT UNDER DIFFERENT NAMES, ON PURPOSE. Identical numbers
# doing unrelated jobs stay separate, or retuning one silently retunes the rest.

SCROLLBAR_HANDLE_ALPHA_DARK: Final[int] = 0xB2
"""178. The dark main-surface scrollbar handle (APP_BORDER_DARK). Written
rgba(51, 51, 51, 0.7) until 2026-09-25. 0.7 * 255 is 178.5, and Qt's
stylesheet parser gives 178 -- MEASURED on three grounds, not computed."""

SCROLLBAR_HANDLE_ALPHA: Final[int] = 0x96
"""150. The image-mode scrollbar handle (APP_CHROME_DARK), the byte all five
applications use. Its color was #505050 until 2026-09-25."""

SCROLLBAR_BG_ALPHA: Final[int] = 0x64
"""100. The image-mode scrollbar groove (APP_BORDER_DARK)."""

SCROLL_AREA_BORDER_ALPHA: Final[int] = 0x64
"""100. The image-mode scroll area's edge (APP_BORDER_DARK)."""

IMAGE_FIELD_ALPHA: Final[int] = 0xAB
"""171. The image-mode line edit's ground (TRUE_BLACK)."""

STATUS_BAR_ALPHA: Final[int] = 0xC8
"""200. The image-mode status bar (APP_SURFACE_DARK)."""

IMAGE_CHECKBOX_ALPHA: Final[int] = 0x64
"""100. The image-mode checkbox indicator's ground (TRUE_BLACK)."""

COMBO_ALPHA: Final[int] = 0xBF
"""191. The image-mode combo box and its drop-down list (APP_SURFACE_DARK)."""

HARMONY_DESCRIPTION_ALPHA: Final[int] = 0x19
"""25. The control panel's harmony description: a wash of its own accent ink
(accent_ink -- BRAND_GOLD in dark and image, BRAND_DARK_GOLD_DEEP in light).
Written rgba(r, g, b, 0.1) from channels sliced by hand until 2026-09-26.
0.1 * 255 is 25.5, and Qt's stylesheet parser gives 25 -- MEASURED on five
grounds under both inks, not computed. The same pixels."""

SCREEN_OVERLAY_ALPHA: Final[int] = 0x32
"""50. The screen picker's dim over the whole screen (TRUE_BLACK)."""

SCREEN_GRID_ALPHA: Final[int] = 0x32
"""50. The screen picker's magnifier grid lines (BRAND_GOLD). The same byte
as the dim, for an unrelated job, so it keeps its own name."""

SCREEN_INFO_ALPHA: Final[int] = 0xB4
"""180. The screen picker's color readout panel (TRUE_BLACK)."""

CANVAS_LABEL_ALPHA: Final[int] = 0xB4
"""180. The plate behind a dragged selection's size, on the canvas."""

CANVAS_PREVIEW_ALPHA: Final[int] = 0xC8
"""200. The plate behind the canvas's color preview."""

CANVAS_SELECTION_ALPHA: Final[int] = 0x32
"""50. A dragged selection's fill on the canvas, over the mode's accent: gold
the image shows through. The fill was solid from the first commit, under a
comment that said semi-transparent, so the area being selected could not
be seen. RNV-RULINGS-2026-10-05, item 3, ruled: "i think the comment meant see
through gold". The byte is the one this application's other see-through
gold has, the screen picker's grid (SCREEN_GRID_ALPHA); a different job, so
its own name."""


# ==================== COLORS THE CODE SPELLED OUT ====================
#
# RNV-NAMED-AND-USED (2026-10-04). Ruled: "As long as a color exist in the
# app it should be named and used no hardcoded or pointless literals should
# exist". Each of these was written out where it is used -- a hex in a
# stylesheet, a CSS name, QColor() built from numbers -- so no palette
# reached it and no sweep moved it. They are named here at the value they
# had: NO PIXEL MOVES. One whose value is a color this file already names
# is LINKED to that name and moves with it; one with a value of its own
# holds it, and is this application's alone.
#
# RNV-COLOR-SYNC (2026-10-16), #48 A: the export colors below are DATA, not
# chrome, and the application's own, so a brand change never alters an
# exported file. They were linked to WHITE, TRUE_BLACK and two neutrals until
# then; each holds the value it had.

CANVAS_FAILED_BG: Final[str] = "#ffcccc"  # app-owned
"""The placeholder shown where the canvas failed to start. App-owned."""

CANVAS_FAILED_EDGE: Final[str] = "#ff0000"  # app-owned
"""Its border. Was the CSS name `red`, which is this value. App-owned."""

HISTORY_EXPORT_PAGE_BG: Final[str] = "#f5f5f5"  # app-owned
"""The exported history page's ground. Was #f5f5f5: linked to APP_WINDOW_LIGHT
until 16 October, the application's own since (#48 A)."""

HISTORY_EXPORT_CARD_BG: Final[str] = "#ffffff"  # app-owned
"""Each color's card on that page. Was the CSS name `white`: linked to WHITE
until 16 October, the application's own since (#48 A)."""

HISTORY_EXPORT_INK: Final[str] = "#333333"  # app-owned
"""The page's heading and the edge of each swatch. Was #333, twice, which
is this value in three digits: linked to APP_BORDER_DARK until 16 October,
the application's own since (#48 A)."""

SVG_EXPORT_BG: Final[str] = "#ffffff"  # app-owned
"""Paper for an exported palette: the SVG file and the image sheet. The
name rnv-color-picker and rnv-color-palette-manager give the same job.
Was #ffffff in one and the CSS name `white` in the other: linked to WHITE
until 16 October, the application's own since (#48 A), as it is in those
two."""

SVG_EXPORT_STROKE: Final[str] = "#000000"  # app-owned
"""The edge of a swatch in the exported SVG. Was #000000: linked to
TRUE_BLACK until 16 October, the application's own since (#48 A)."""

CANVAS_PREVIEW_EDGE_DARK: Final[str] = "#e6e6e6"  # app-owned
"""The edge of the canvas's color preview in dark. Was QColor(230, 230,
230). In light the edge is TRUE_BLACK. App-owned."""

CANVAS_LABEL_PLATE_LIGHT: Final[str] = "#c8c8c8"  # app-owned
"""The plate behind a dragged selection's size in light, at
CANVAS_LABEL_ALPHA. Was QColor(200, 200, 200, 180), which was never drawn:
the canvas asked a theme manager of its own for the mode, and a new one
always answers dark. RNV-RULINGS-2026-10-05, item 3: the canvas follows the
mode, so light draws it. In dark and image the plate is TRUE_BLACK.
App-owned."""

# RNV-COLOR-SYNC (2026-10-17), #56 A: colors the application's own code
# still wrote out, named here at the value they had, so no pixel moves.
# #66 A (2026-10-18) wrote them in lower case, as every hex in the source
# is. Each is DATA, the application's own, and a brand move never
# touches it.

HISTORY_SAMPLE_ORANGE_RED: Final[str] = "#ff5733"  # app-owned
"""The first of five sample rows the History tab shows when the history
module cannot be loaded (core/package_d_panel.py,
_populate_history_placeholder). Data, not chrome: each row shows its
color and its hex, in lower case, as a real History row writes its own
(#66 A). App-owned."""

HISTORY_SAMPLE_GREEN: Final[str] = "#33ff57"  # app-owned
"""The second sample row of the History tab's fallback. App-owned."""

HISTORY_SAMPLE_BLUE: Final[str] = "#3357ff"  # app-owned
"""The third sample row of the History tab's fallback. App-owned."""

HISTORY_SAMPLE_MAGENTA: Final[str] = "#ff33f5"  # app-owned
"""The fourth sample row of the History tab's fallback. App-owned."""

HISTORY_SAMPLE_YELLOW: Final[str] = "#f5ff33"  # app-owned
"""The fifth sample row of the History tab's fallback. App-owned."""


# ---------------------------------------------------------------- palettes
# The three theme palettes ThemeManager serves. #63 A (2026-10-18): they were
# its class attributes until the colors moved here; it keeps the same three
# names, pointing at these, so everything that reads ThemeManager.DARK_THEME
# reads the same dict.

DARK_THEME = {
    'name': 'Dark',
    'window_bg': TRUE_BLACK,
    'text_color': APP_TEXT_DARK,
    'border_color': APP_BORDER_DARK,
    'hover_color': APP_CHROME_DARK,
    'main_btn_bg': APP_SURFACE_DARK,
    'main_btn_text': APP_TEXT_DARK,
    'main_btn_hover_bg': APP_BORDER_DARK,
    'main_btn_pressed_bg': APP_BTN_PRESSED,
    'main_btn_pressed_text': TRUE_BLACK,
    # The hover and pressed a DIALOG button takes. Added
    # 2026-09-01, holding what the three dialogs already painted.
    # Before this they read the main family, which is how a gold
    # pressed plate that only a QDialog ever used came to look
    # like the main window's.
    # RNV-NAMED-AND-USED (2026-10-04): the hover is read in dark
    # alone -- the About dialog's tabs, from this palette by name
    # -- so this palette alone holds it. dialog_btn_bg, which only
    # light reads, is in LIGHT_THEME alone: a dark dialog's button
    # takes panel_secondary.
    'dialog_btn_hover_bg': APP_BORDER_DARK,
    'dialog_btn_pressed_bg': BRAND_GOLD_PRESSED,
    'canvas_bg': APP_CANVAS_DARK,
    'scroll_area_bg': TRUE_BLACK,
    'input_bg': APP_SURFACE_DARK,
    'input_text': APP_TEXT_DARK,
    'slot_border': APP_TEXT_DARK,
    'slot_border_width': 2,
    'tooltip_bg': APP_CARD_DARK,
    'tooltip_border': BRAND_GOLD,
    'text_disabled': APP_CONTROL_DIM,
    'accent': BRAND_GOLD,
    'accent_ink': BRAND_GOLD,
    'accent_hover': BRAND_GOLD_HOVER,
    'accent_text': TRUE_BLACK,
    'panel_bg': APP_SURFACE_DARK,
    'panel_secondary': APP_CARD_DARK,
    'panel_hover': APP_PANEL_HOVER_DARK,
    'tab_selected_bg': APP_CANVAS_DARK,
    'scrollbar_bg': APP_SURFACE_DARK,
    'scrollbar_handle': APP_BORDER_DARK,
    'scrollbar_hover': BRAND_GOLD,
    'slider_handle': APP_TEXT_DARK,
    'text_hint': APP_HINT_DARK,
    'menu_disabled': APP_MENU_DIM_DARK,
    # One key for the slider groove. Before this pass three files painted
    # it from three different keys -- panel_bg, hover_color and input_bg --
    # and in dark two of those resolved to the panel's own color, so the
    # groove did not exist. RNV-MIXER-WIRING (2026-09-06).
    'slider_groove': APP_CHROME_DARK,
    # The menu's border and separator. The dark and light branches of
    # core/color_slot.py painted these from different keys -- hover_color
    # and border_color -- so the same two parts had no shared name. Values
    # unchanged; the difference between the modes is now a value, not a key.
    'menu_edge': APP_CHROME_DARK,
    # The label while the main button is hovered. RULED, not chosen: see
    # claude/ruling-interaction-contrast.md -- the transient states of this
    # button are exempt from the 4.5 floor and the label dims on purpose.
    # It held the resting label by inheritance in one file and by an
    # explicit line in another; this states it once, at the same value.
    'main_btn_hover_text': APP_TEXT_DARK,
}

LIGHT_THEME = {
    'name': 'Light',
    'window_bg': APP_WINDOW_LIGHT,
    'text_color': TRUE_BLACK,
    'border_color': APP_BORDER_LIGHT,
    'hover_color': APP_CHROME_LIGHT,
    'main_btn_bg': WHITE,
    'main_btn_text': TRUE_BLACK,
    'main_btn_hover_bg': APP_BTN_HOVER_INVERSE,
    'main_btn_pressed_bg': APP_BTN_PRESSED,
    'main_btn_pressed_text': WHITE,
    # The plate and pressed a DIALOG button takes. Added
    # 2026-09-01, holding what the three dialogs already painted.
    # Before this they read the main family, which is how a gold
    # pressed plate that only a QDialog ever used came to look
    # like the main window's.
    # RNV-NAMED-AND-USED (2026-10-04): the plate is read in light
    # alone, from this palette by name, so this palette alone
    # holds it. dialog_btn_hover_bg, which only dark reads, is in
    # DARK_THEME alone.
    'dialog_btn_bg': WHITE,
    'dialog_btn_pressed_bg': BRAND_DARK_GOLD_PRESSED,
    'canvas_bg': WHITE,
    'scroll_area_bg': WHITE,
    'input_bg': WHITE,
    'input_text': TRUE_BLACK,
    'slot_border': TRUE_BLACK,
    'slot_border_width': 1,
    'tooltip_bg': WHITE,
    'tooltip_border': BRAND_DARK_GOLD,
    'text_disabled': APP_TEXT_DIM_LIGHT,
    'accent': BRAND_DARK_GOLD,
    'accent_ink': BRAND_DARK_GOLD_DEEP,
    'accent_hover': BRAND_DARK_GOLD_HOVER,
    'accent_text': WHITE,
    'panel_bg': APP_WINDOW_LIGHT,
    'panel_secondary': WHITE,
    'panel_hover': APP_ITEM_HOVER_LIGHT,
    'tab_selected_bg': WHITE,
    'scrollbar_bg': APP_WINDOW_LIGHT,
    'scrollbar_handle': APP_BORDER_LIGHT,
    'scrollbar_hover': BRAND_DARK_GOLD,
    'slider_handle': APP_HANDLE_LIGHT,
    # The 10px hint under each fine-tune slider is the only consumer, and
    # it sits on the QFrame that section builds -- panel_secondary, not
    # panel_bg. #888888 read 3.5407:1 there, below AA for text this
    # size. #666666 clears 4.5 on every light ground in this app.
    'text_hint': APP_HINT_LIGHT,
    'menu_disabled': APP_HANDLE_EDGE_LIGHT,
    # One key for the slider groove. Before this pass three files painted
    # it from three different keys -- panel_bg, hover_color and input_bg --
    # and in dark two of those resolved to the panel's own color, so the
    # groove did not exist. RNV-MIXER-WIRING (2026-09-06).
    'slider_groove': APP_CHROME_LIGHT,
    # The menu's border and separator. The dark and light branches of
    # core/color_slot.py painted these from different keys -- hover_color
    # and border_color -- so the same two parts had no shared name. Values
    # unchanged; the difference between the modes is now a value, not a key.
    'menu_edge': APP_BORDER_LIGHT,
    # The label while the main button is hovered. RULED, not chosen: see
    # claude/ruling-interaction-contrast.md -- the transient states of this
    # button are exempt from the 4.5 floor and the label dims on purpose.
    # It held the resting label by inheritance in one file and by an
    # explicit line in another; this states it once, at the same value.
    'main_btn_hover_text': TRUE_BLACK,
}

# Image Theme: the dark palette, under its own name.
# RNV-NAMED-AND-USED (2026-10-04): this was a written copy of
# DARK_THEME, the same forty keys at the same forty values bar the
# name. Image mode's dialogs never read it -- they draw from DARK_THEME
# by name -- so much of the copy was a second spelling of values nothing
# read. It is dark's values now, so nothing is written twice and a key
# image mode looks up is always there. A value image mode is ruled to
# draw differently goes after the spread.
IMAGE_THEME = {**DARK_THEME, 'name': 'Image'}

# Legacy color dictionaries (for backward compatibility)
DARK_THEME_LEGACY = DARK_THEME
LIGHT_THEME_LEGACY = LIGHT_THEME


def get_theme_colors(theme_manager: 'ThemeManager | None' = None, dark_mode: bool = False) -> 'dict[str, Any]':
    """Get theme colors based on mode or theme manager."""
    if theme_manager:
        current = theme_manager.get_current_theme()
        if current:
            return current
    return DARK_THEME_LEGACY if dark_mode else LIGHT_THEME_LEGACY


# RNV-GOLD-GUARD (2026-09-07): the values below are swept by
# tests/test_gold_as_text.py, which resolves every QSS f-string in this
# repository through these palettes and measures the gold family as text
# and as a fill. A gold that reads correctly here can still be drawn on
# the wrong ground three files away, and that is what it is for.
