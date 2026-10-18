"""Every colour value the tests need that is not the application's colour.

RNV-COLOUR-SYNC, #53 A (2026-10-17). The application's own colours and the
brand's are named in utils/config.py, which brand_map.json names, and a test
reads them from there. Every other colour value a test or the root suite
writes is named here, once, with why: samples given to a helper (EXAMPLE_),
what a user, a file or the clipboard supplies (DATA_), values the
application no longer uses (RETIRED_), a value the brand publishes that this
application does not draw (REGISTER_), and values written wrongly on purpose
(INVALID_). tests/test_colour_values.py holds this file: no colour value is
written anywhere else in tests/ or in test_rnv_color_mixer.py, and every name
here says what kind it is, says why, and is used.

Tests under tests/ import from here by name (`from colour_values import ...`);
the root suite and tests/test_colours_in_sync.py load it by path.

RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN
This file names the retired golds on purpose (the RETIRED_ section), so the
retired-gold sweep in tests/test_brand_mirror.py skips it.
"""

# ------------------------------------------------------------------ examples

EXAMPLE_BLACK = "#000000"
"""Black as the colour maths and the readers spell it: what rgb_to_hex() makes
of (0, 0, 0) and hex_to_rgb() reads back, what the integer sweep reports for
(0, 0, 0, 50), and what the ink reader makes of EXAMPLE_BLACK_SHORT. A
sample, not TRUE_BLACK: it must not follow a brand move."""

EXAMPLE_BLACK_SHORT = "#000"
"""Black in three digits, as a sample stylesheet writes it for the ink reader
in tests/test_ink_on_the_golds.py; the reader must read it as EXAMPLE_BLACK."""

EXAMPLE_WHITE = "#ffffff"
"""White as the colour maths and the readers spell it: rgb_to_hex() of
(255, 255, 255), what the ink reader makes of the CSS word `white`, and the
ink of a sample rule that reader is given. Also one of the grounds Qt's
alpha byte for 0.7 was measured on. A sample, not WHITE."""

EXAMPLE_PURE_RED = "#ff0000"
"""What rgb_to_hex() makes of (255, 0, 0): lower case, as it writes."""

EXAMPLE_PURE_RED_UPPER = "#FF0000"
"""The same red in upper case, for the test that hex_to_rgb() reads either
case; the case is the point. Without its #, it is what a copied palette must
hold for (255, 0, 0)."""

EXAMPLE_PURE_GREEN_UPPER = "#00FF00"
"""(0, 255, 0) in upper-case hex. Without its #, it is what a copied palette
and an exported history page must hold for that colour, read in either
case."""

EXAMPLE_PURE_BLUE_DIGITS = "0000FF"
"""(0, 0, 255) as six hex digits with no #: one way an exported history text
file may write that colour."""

EXAMPLE_TAN = "#d2bc93"
"""What rgb_to_hex() makes of (210, 188, 147), one of the bases the alpha
helpers are tried on, and one of the grounds Qt's alpha byte for 0.7 was
measured on. It is the bright gold's value today, but a
sample: the channels beside it are written out, so it must not follow the
brand."""

EXAMPLE_DARK_GREY = "#444444"
"""A base the alpha helpers are tried on, and what the integer sweep reports
for QColor(68, 68, 68). A sample, in lower case as the helpers write."""

EXAMPLE_NEAR_BLACK = "#1a1a1a"
"""The base the alpha helpers are tried on, and the good base passed while
bad alphas are tried. Six digits in lower case: decompose() hands it back
in that form. Also one of the grounds Qt's alpha byte for 0.7 was
measured on."""

EXAMPLE_NEAR_BLACK_AT_BF = "#bf1a1a1a"
"""What translucent() makes of EXAMPLE_NEAR_BLACK at alpha 0xBF: eight
digits, alpha first, lower case."""

EXAMPLE_NEAR_BLACK_AT_BF_RGBA = "rgba(26, 26, 26, 191)"
"""What translucent_rgba() makes of EXAMPLE_NEAR_BLACK at alpha 0xBF, spelled
exactly as it writes it."""

EXAMPLE_NEAR_BLACK_AT_ED = "#ed1a1a1a"
"""Eight-digit hex as the register writes it, in lower case: the example the
ruling of 2026-09-25 gave (RNV-LOWER-EIGHT)."""

EXAMPLE_HAND_EDIT = "#123456"
"""A value planted on one of the colour file's lines, as a hand edit the sync
must put back (tests/test_colours_in_sync.py). Any colour the map does not
hold will do."""

EXAMPLE_HAND_EDIT_FALLBACK = "#654321"
"""The planted value to use when the line already holds EXAMPLE_HAND_EDIT."""

EXAMPLE_MOVED_ACCENT = "#6f94bc"
"""Where a pretend brand move puts APP.accent, so the test can see that one
line, and only that one, takes it (tests/test_colours_in_sync.py)."""

EXAMPLE_MOVED_ACCENT_FALLBACK = "#456c91"
"""The pretend move to use when the brand's accent already is
EXAMPLE_MOVED_ACCENT."""

EXAMPLE_PALE_PINK = "#ffcccc"
"""A hex in the probe line test_named_and_used's sweep must read, and in the
bare string of prose its quiet probe must not read. Each probe is built from
this name, so the two cannot drift."""

EXAMPLE_WHITE_AT_230_RGBA = "rgba(255, 255, 255, 230)"
"""An rgba() in the same probe, spelled as the sweep reports it."""

EXAMPLE_CLEAR_RGBA = "rgba(0, 0, 0, 0)"
"""Clear written as rgba() at alpha 0, in the quiet probe of
test_named_and_used: clear is not a colour, so the sweep must not report it."""

EXAMPLE_ORANGE_UPPER = "#FF8040"
"""What the screen picker's readout writes for (255, 128, 64): upper case,
as it formats. Without its #, it is what a slot copies to the clipboard for
that colour, read in upper case."""

EXAMPLE_ZERO_PADDED_BLUE = "#0500FA"
"""What the screen picker's readout writes for (5, 0, 250): each channel
padded to two digits, upper case."""

EXAMPLE_BROWN_DIGITS = "804020"
"""(128, 64, 32) as six hex digits with no #: what a slot's colour data holds
as its hex, read in lower case without the #."""

EXAMPLE_PALE_BLUE_DIGITS = "abcdef"
"""(171, 205, 239) as six hex digits with no #: what a slot copies to the
clipboard, read in lower case without the #."""

EXAMPLE_MAGENTA = "#ff00ff"
"""The control colour a render set the unread palette entries to
(RNV-CHART-RULINGS, 2026-09-26): a value nothing else draws, so any pixel
it reached would show."""

# ---------------------------------------------------------------------- data

DATA_TYPED_ORANGE = "#ff8040"
"""A hex a person types into a slot's hex entry, in lower case as typed."""

DATA_CLIPBOARD_ORANGE = "#FF8040"
"""A hex on the clipboard, for the clipboard parser to read."""

DATA_CLIPBOARD_ORANGE_SHORT = "#F80"
"""The same orange on the clipboard in three-digit form; the short form is
the point."""

DATA_CLIPBOARD_ORANGE_RGB = "rgb(255, 128, 64)"
"""The same orange on the clipboard as an rgb() string."""

DATA_CLIPBOARD_ORANGE_PADDED = "   #FF8040   "
"""The same orange on the clipboard with spaces round it; the spaces are the
point."""

DATA_CSS_WHITE = "#ffffff"
"""What the CSS word `white` means where a stylesheet writes it, for the
contrast reader. CSS's value, not the brand's WHITE: it never moves."""

DATA_CSS_BLACK = "#000000"
"""What the CSS word `black` means where a stylesheet writes it. CSS's value,
not TRUE_BLACK."""

DATA_CSS_GREY = "#808080"
"""What the CSS words `gray` and `grey` mean where a stylesheet writes them:
the grey the History tab's empty line and the control panel's descriptions
were given before they took the muted text."""

# ------------------------------------------------------------------- retired

RETIRED_OLD_DARK_GOLD = "#b19145"
"""The old dark gold, 2.997638:1 on white. It must not come back
(tests/test_brand_mirror.py); the root suite also holds a stylesheet's
scrollbar hover clear of it."""

RETIRED_OLD_DARK_GOLD_TINT = "#c4a458"
"""A tint of RETIRED_OLD_DARK_GOLD, written out as a literal. It must not
come back."""

RETIRED_OLD_DARK_HOVER = "#dcc9a3"
"""The hand-written dark hover, a non-uniform step that shifted hue. It must
not come back."""

RETIRED_MAGNIFIER_GRID_PEN = "#bfb145"
"""The screen picker's old grid pen, neither brand gold. It must not come
back, as a hex or as channels."""

RETIRED_OLD_DARK_GOLD_AT_BF_MIXED = "#BFb19145"
"""The old dark gold at alpha 0xBF, in the mixed case the stylesheets once
held it in. The root suite checks no stylesheet does; the case is the
point."""

RETIRED_OLD_DARK_GOLD_AT_BF_UPPER = "#BFB19145"
"""The same value in upper case, which the root suite checks for too."""

RETIRED_IMAGE_SCROLLBAR_HANDLE = "#505050"
"""The image scrollbar handle's old grey, ruled onto grey(4) on 2026-09-02
and gone on 2026-09-25 (RNV-COLLAPSE-505050). It must not come back in any
spelling."""

RETIRED_IMAGE_SCROLLBAR_HANDLE_RGBA = "rgba(80, 80, 80, 150)"
"""The same handle as the image stylesheet spelled it, given to the colour
decoder to prove the decoder still sees it."""

RETIRED_DARK_SCROLLBAR_HANDLE_RGBA = "rgba(51, 51, 51, 0.7)"
"""The dark scrollbar handle as the dark stylesheet spelled it until
2026-09-25: APP_BORDER_DARK at alpha 0.7, written out. The stylesheet no
longer writes it."""

RETIRED_LIGHT_HINT = "#888888"
"""The light hint's value until it failed 10px text on white (3.5407:1). The
light hint no longer uses it; the value lives on in other roles, which is
why the test that light is not back to it names it here and not from the
colour file."""

# ------------------------------------------------------------------ register

REGISTER_GOLD_TEXT_GROUND_FLOOR = "#e8e8e8"
"""The register's floor for gold text: the darkest light ground the gold
family still carries text on. A boundary the brand publishes, not a colour
this application draws."""

# ------------------------------------------------------------------- invalid

INVALID_EIGHT_DIGIT_BASE = "#1a1a1a1a"
"""Eight digits where the alpha helpers want a six-digit base. They must
refuse it."""

INVALID_UPPER_EIGHT_DIGIT = "#ED1A1A1A"
"""EXAMPLE_NEAR_BLACK_AT_ED in upper case, the spelling the ruling of
2026-09-25 refuses: eight digits are hex, and hex is written in lower case."""

INVALID_FIVE_DIGIT = "#1a1a1"
"""Five digits: no colour. The alpha helpers must refuse it."""

INVALID_NOT_HEX = "#gggggg"
"""Six characters that are not hex. The alpha helpers must refuse it."""

INVALID_ONE_LETTER = "#z"
"""A hex entry half typed, with a letter that is not hex. The slot must not
take it."""

INVALID_TWO_DIGIT = "#12"
"""A hex entry half typed. The slot must not take it."""

INVALID_SEVEN_DIGIT = "#1234567"
"""A hex entry typed one digit too long. The slot must not take it."""

#: The brand's name for each REGISTER_ value; tests/test_colour_values.py
#: holds each to the brand at the pinned commit.
REGISTER_REFS = {
    "REGISTER_GOLD_TEXT_GROUND_FLOOR": "GOLD_TEXT_GROUND_FLOOR",
}
