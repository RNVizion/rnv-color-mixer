"""
test_subtractive_cmy.py — Subtractive CMY mixes like inks
=========================================================

Each color is a filter that passes c/255 of each channel's light. Inks
and filters in layers multiply what they pass, so the mix is the weighted
geometric mean of the transmittances, times 255 and rounded. A channel
at 0 passes nothing, so the mix is 0 there whenever a weighted color has
0 in it. A color with weight 0 is left out.

Before this, the function averaged 1 - RGB and turned it back, which is
the same average as weighted RGB, so the two always gave the same color.
The same formula is in the RNV Color Palette Manager, and the two agree
to the last digit.
"""
from __future__ import annotations

import pytest

from core.color_math import ColorMath

YELLOW = (245, 208, 0)
BLUE = (31, 79, 191)


def test_yellow_and_blue_make_a_dark_green():
    # sqrt(245 * 31) = 87.1, sqrt(208 * 79) = 128.2, and yellow passes no blue
    assert ColorMath.subtractive_cmy_mix([(YELLOW, 1), (BLUE, 1)]) == (87, 128, 0)


def test_yellow_and_blue_differ_from_weighted_rgb():
    pair = [(YELLOW, 1), (BLUE, 1)]
    assert ColorMath.weighted_rgb_mix(pair) == (138, 143, 95)
    assert ColorMath.subtractive_cmy_mix(pair) != ColorMath.weighted_rgb_mix(pair)


def test_known_weighted_case():
    # Three parts of (200, 100, 50) to one of (50, 200, 100):
    # 200^(3/4) * 50^(1/4) = 100 * sqrt(2) = 141.42, and the other two
    # channels are 100 * 2^(1/4) = 118.92 and 50 * 2^(1/4) = 59.46.
    mixed = ColorMath.subtractive_cmy_mix([((200, 100, 50), 3), ((50, 200, 100), 1)])
    assert mixed == (141, 119, 59)


def test_weights_scale_out():
    # Only the shares count: 3:1 and 30:10 are the same mix
    a, b = (200, 100, 50), (50, 200, 100)
    assert (ColorMath.subtractive_cmy_mix([(a, 30), (b, 10)])
            == ColorMath.subtractive_cmy_mix([(a, 3), (b, 1)]))


@pytest.mark.parametrize("weights", [(1, 1), (3, 2), (7, 1), (1, 99)])
def test_a_color_mixed_with_itself_is_itself(weights):
    for v in range(256):
        color = (v, 255 - v, (v * 7) % 256)
        mixed = ColorMath.subtractive_cmy_mix([(color, weights[0]), (color, weights[1])])
        assert mixed == color, f"{color} at {weights}: {mixed}"


def test_a_channel_at_zero_absorbs_it():
    # Yellow ink takes out blue and cyan ink takes out red: green is left
    assert ColorMath.subtractive_cmy_mix(
        [((255, 255, 0), 1), ((0, 255, 255), 1)]) == (0, 255, 0)
    # However little of it there is
    assert ColorMath.subtractive_cmy_mix(
        [((200, 200, 200), 99), ((200, 0, 200), 1)])[1] == 0


def test_mixing_darkens():
    # A filter never adds light: the mix is no lighter than the lighter
    # color in any channel, and no darker than the darker one
    a, b = (230, 120, 40), (60, 200, 180)
    mixed = ColorMath.subtractive_cmy_mix([(a, 1), (b, 1)])
    for m, x, y in zip(mixed, a, b):
        assert min(x, y) <= m <= max(x, y)
    assert sum(mixed) < sum(ColorMath.weighted_rgb_mix([(a, 1), (b, 1)]))


def test_a_color_with_weight_zero_is_ignored():
    assert ColorMath.subtractive_cmy_mix([(YELLOW, 5), ((0, 0, 0), 0)]) == YELLOW
    assert ColorMath.subtractive_cmy_mix([((0, 0, 0), 0)]) is None
    assert ColorMath.subtractive_cmy_mix([]) is None
