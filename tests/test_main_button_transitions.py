"""THE MAIN BUTTON'S TRANSITIONS, AS RULED (#74 A, #75 A, 2026-10-22).

The same file in all five RNV desktop applications.

THE RULING. Chris, 2026-09-01, decided from a real Qt render of every state in
both modes (claude/ruling-interaction-contrast.md): the main black-and-white
button's TRANSIENT states are not held to the 4.5:1 text floor. The label is
permitted to dim as the plate crosses to the other side of the scheme:

    LIGHT hover     black on the border gray, APP["border"]   1.66:1
    DARK  pressed   black on gray step 4 of the ink grid       2.16:1
                    (image mode is dark's)

The label dims; it does not disappear. The plate travels toward the ink in
light and away from it in dark, so the state at which label and plate
converge is a different one in each mode: symmetric intent, not symmetric
numbers.

HOW FAR IT REACHES, #74 A (2026-10-22): the main button only. "The floor
still governs every resting state, in both modes, and every dialog button at
every state." Every other control holds 4.5:1 in every state.

WHY THIS FILE EXISTS. The ruling asks that any sweep scoring foreground
against background exempt these two states AND SAY WHY, rather than list them
as known failures: a suppressed failure invites a later pass to "fix" it.
Until 2026-10-22 only the mixer cited the ruling; two apps exempted the same
pairs as "deliberate inversion" with no reference to it, and two never
measured the main button at all (#75 A).

What it holds, for every palette that carries the main button's keys:
  - every state names its label and its plate;
  - every state clears 4.5:1, except the two ruled transitions;
  - each ruled transition is exactly the ruled pair, and dims without vanishing;
  - the hover label is the resting label: the dimming is the plate crossing,
    not a recolor.
"""
from __future__ import annotations

import pytest

import engine.brand as B
import utils.colors as C

FLOOR = 4.5

def _ink(n: int) -> str:
    """Step n of the register's ink grid: gray(n) = n * 0x11 on every channel."""
    return "#" + f"{n * 0x11:02x}" * 3


#: (base mode, state) -> the (label, plate) the ruling of 2026-09-01 names, read from the register
RULED = {
    ("light", "hover"): (B.PERMANENT["black"].lower(), B.APP["border"].lower()),
    ("dark", "pressed"): (B.PERMANENT["black"].lower(), _ink(4)),
}

#: the floor a ruled transition may dim to and still read: "it does not disappear"
VISIBLE = 1.5

STATES = {
    "rest": ("main_btn_text", "main_btn_bg"),
    "hover": ("main_btn_hover_text", "main_btn_hover_bg"),
    "pressed": ("main_btn_pressed_text", "main_btn_pressed_bg"),
}


def _palettes() -> list[tuple[str, str, dict]]:
    """(name, base mode, palette) for every palette in utils/colors.py that
    carries the main button. An alias of a palette is counted once. Image mode
    is dark-based in every app, so its base mode is dark."""
    seen, out = set(), []
    for name, value in vars(C).items():
        if not (isinstance(value, dict) and "main_btn_bg" in value) or id(value) in seen:
            continue
        seen.add(id(value))
        upper = name.upper()
        base = "light" if "LIGHT" in upper else "dark"
        out.append((name, base, value))
    return out


def _lum(hex_color: str) -> float:
    h = hex_color.strip().lower().lstrip("#")
    assert len(h) == 6, f"{hex_color!r} is not an opaque six-digit color"
    chans = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        chans.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def _ratio(fg: str, bg: str) -> float:
    a, b = _lum(fg), _lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


PALETTES = _palettes()


def test_the_sweep_reads_both_modes() -> None:
    bases = {base for _, base, _ in PALETTES}
    assert bases == {"dark", "light"}, (
        f"found main-button palettes for {sorted(bases)} only; a sweep that reads one "
        f"mode passes by looking at half the app")


@pytest.mark.parametrize("name,base,palette", PALETTES, ids=[p[0] for p in PALETTES])
def test_every_state_names_its_label_and_plate(name, base, palette) -> None:
    missing = [k for pair in STATES.values() for k in pair if k not in palette]
    assert not missing, f"{name} has no {missing}: a state the palette does not name is inherited, not stated"


@pytest.mark.parametrize("name,base,palette", PALETTES, ids=[p[0] for p in PALETTES])
def test_the_floor_holds_except_where_ruled(name, base, palette) -> None:
    low = []
    for state, (fg_key, bg_key) in STATES.items():
        if (base, state) in RULED:
            continue
        r = _ratio(palette[fg_key], palette[bg_key])
        if r < FLOOR:
            low.append(f"{state}: {palette[fg_key]} on {palette[bg_key]} = {r:.2f}")
    assert not low, (
        f"{name}: under {FLOOR}:1 outside the two ruled transitions: {low}. "
        f"#74 A: the exemption reaches the main button's light hover and dark press only.")


@pytest.mark.parametrize("name,base,palette", PALETTES, ids=[p[0] for p in PALETTES])
def test_the_ruled_transitions_are_the_ruled_pairs(name, base, palette) -> None:
    for (mode, state), (fg, bg) in RULED.items():
        if mode != base:
            continue
        fg_key, bg_key = STATES[state]
        got = (palette[fg_key].lower(), palette[bg_key].lower())
        assert got == (fg, bg), (
            f"{name} {state} is {got[0]} on {got[1]}, not the ruled {fg} on {bg}. This is a change "
            f"to a RULED transition (claude/ruling-interaction-contrast.md, 2026-09-01), not a fix.")
        r = _ratio(*got)
        assert VISIBLE <= r < FLOOR, f"{name} {state} reads {r:.2f}: the ruled label dims, it does not vanish"


@pytest.mark.parametrize("name,base,palette", PALETTES, ids=[p[0] for p in PALETTES])
def test_the_hover_label_is_the_resting_label(name, base, palette) -> None:
    assert palette["main_btn_hover_text"].lower() == palette["main_btn_text"].lower(), (
        f"{name}: the hover label is {palette['main_btn_hover_text']}, the resting label "
        f"{palette['main_btn_text']}. The ruled dimming is the plate crossing under the "
        f"same label, not a recolor.")
