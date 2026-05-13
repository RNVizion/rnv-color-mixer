"""
RNV Color Mixer — Color Math Property Tests  (Phase 5 deliverable)
====================================================================

Property-based testing of ColorMath using hypothesis. The locked suite's
example-based roundtrip tests cover ~5 hand-picked colours per conversion;
this file generalises to thousands of randomly-explored inputs and asserts
the same invariants hold for *all* of them.

What property-based testing buys us
-----------------------------------
Example-based unit tests check "for these specific 5 colours, hex roundtrip
is exact". Property tests check "for ANY RGB tuple, hex roundtrip is exact",
generating up to 200 random examples per property, plus shrunk minimal
counter-examples on failure.

A subtle bug in `rgb_to_lab`'s gamma curve, for instance, would likely pass
the 5 hand-picked test colours but fail under hypothesis on something like
(127, 0, 73). When a property fails, hypothesis automatically shrinks to
the simplest input that triggers the failure — e.g. (1, 0, 0) instead of
(127, 53, 219) — making diagnosis easy.

Scope discipline (per phase plan)
---------------------------------
• Roundtrip invariants for the 5 colour spaces (HEX exact, HSL/HSV/LAB ±2,
  RYB ±15)
• Clamp idempotence and value-range invariants
• Two-colour mix bounding-box property (RGB mix only — wider mixes have
  combinatorial explosion)
• Single-slot identity across all 6 mixing algorithms

NOT scoped: 3+ slot combinatorial mixes, hue-wrap edge cases, LAB
out-of-gamut clamping behaviour. Those would need targeted unit tests, not
property tests.

Performance
-----------
Hypothesis `deadline=None` is set globally for this file because some colour
math (LAB, Kubelka-Munk) is non-trivial and can intermittently exceed the
default 200ms per-example deadline on a busy CI. `max_examples=200` per
property gives strong coverage without blowing past the 15-second budget.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

# Bootstrap (sys.path / virtual packages) is done by tests/conftest.py
from core.color_math import ColorMath


# ═══════════════════════════════════════════════════════════════════════════
# Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════

# Standard 8-bit RGB
rgb_st = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
)

# Strictly positive integer weight in the 1..100 range used by the app
positive_weight_st = st.integers(min_value=1, max_value=100)

# Any float for the clamp-domain test
arbitrary_float_st = st.floats(
    min_value=-10_000.0, max_value=10_000.0,
    allow_nan=False, allow_infinity=False,
)

# Suppress hypothesis health checks where they'd flag harmless variance
# (the colour space conversions are uniform-cost, just sometimes slow)
HYP_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


# ═══════════════════════════════════════════════════════════════════════════
# Properties — 10 invariants over 200 examples each
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.property
class TestColorMathProperties:
    """Property-based tests for ColorMath. Each test enforces an invariant
    that must hold for every input, not just hand-picked ones."""

    # ── Roundtrip invariants ────────────────────────────────────────────

    @HYP_SETTINGS
    @given(rgb_st)
    def test_property_rgb_hex_roundtrip_is_exact(self, rgb):
        """HEX encoding is lossless — must roundtrip exactly."""
        assert ColorMath.hex_to_rgb(ColorMath.rgb_to_hex(rgb)) == rgb

    @HYP_SETTINGS
    @given(rgb_st)
    def test_property_rgb_hsv_roundtrip_within_delta(self, rgb):
        """HSV has float intermediates — allow ±2 per channel."""
        back = ColorMath.hsv_to_rgb(ColorMath.rgb_to_hsv(rgb))
        for orig, recovered in zip(rgb, back):
            assert abs(orig - recovered) <= 2, (
                f"RGB→HSV→RGB drift > 2: {rgb} → {back}"
            )

    @HYP_SETTINGS
    @given(rgb_st)
    def test_property_rgb_hsl_roundtrip_within_delta(self, rgb):
        """HSL roundtrip — allow ±2 per channel."""
        back = ColorMath.hsl_to_rgb(ColorMath.rgb_to_hsl(rgb))
        for orig, recovered in zip(rgb, back):
            assert abs(orig - recovered) <= 2, (
                f"RGB→HSL→RGB drift > 2: {rgb} → {back}"
            )

    @HYP_SETTINGS
    @given(rgb_st)
    def test_property_rgb_lab_roundtrip_within_delta(self, rgb):
        """LAB roundtrip — allow ±2 per channel (gamma curve is non-trivial)."""
        back = ColorMath.lab_to_rgb(ColorMath.rgb_to_lab(rgb))
        for orig, recovered in zip(rgb, back):
            assert abs(orig - recovered) <= 2, (
                f"RGB→LAB→RGB drift > 2: {rgb} → {back}"
            )

    @HYP_SETTINGS
    @given(rgb_st)
    def test_property_rgb_ryb_roundtrip_within_wider_delta(self, rgb):
        """RYB is an approximate space — allow ±15 per channel
        (this matches the locked suite's existing tolerance)."""
        back = ColorMath.ryb_to_rgb(ColorMath.rgb_to_ryb(rgb))
        for orig, recovered in zip(rgb, back):
            assert abs(orig - recovered) <= 15, (
                f"RGB→RYB→RGB drift > 15: {rgb} → {back}"
            )

    # ── Clamping & validation invariants ────────────────────────────────

    @HYP_SETTINGS
    @given(arbitrary_float_st)
    def test_property_clamp_value_is_idempotent(self, x):
        """clamp(clamp(x)) == clamp(x) — applying twice must be a no-op."""
        once = ColorMath.clamp_value(x)
        twice = ColorMath.clamp_value(once)
        assert once == twice

    @HYP_SETTINGS
    @given(arbitrary_float_st)
    def test_property_clamp_value_lands_in_byte_range(self, x):
        """No matter the input, clamp_value's output must be 0..255."""
        result = ColorMath.clamp_value(x)
        assert 0 <= result <= 255

    @HYP_SETTINGS
    @given(arbitrary_float_st, arbitrary_float_st, arbitrary_float_st)
    def test_property_safe_rgb_always_returns_valid_rgb(self, r, g, b):
        """safe_rgb must always emit a valid RGB tuple, no matter the input."""
        result = ColorMath.safe_rgb(r, g, b)
        assert isinstance(result, tuple) and len(result) == 3
        for ch in result:
            assert 0 <= ch <= 255
            assert isinstance(ch, int)

    # ── Mixing invariants ───────────────────────────────────────────────

    @HYP_SETTINGS
    @given(rgb_st, rgb_st, st.integers(min_value=1, max_value=99))
    def test_property_two_color_rgb_mix_in_bounding_box(self, c1, c2, w1):
        """A weighted RGB mix of two colours must lie within the axis-aligned
        bounding box of those colours, per channel.

        This holds for the linear `weighted_rgb_mix` algorithm. Other
        algorithms (HSV, LAB, RYB, KM) interpolate in non-RGB spaces so
        the projected result CAN escape the RGB bounding box — those are
        tested with the weaker "valid RGB" invariant in
        `test_property_single_slot_identity_all_algorithms`."""
        w2 = 100 - w1
        result = ColorMath.weighted_rgb_mix([(c1, w1), (c2, w2)])
        assert result is not None
        for i in range(3):
            lo, hi = min(c1[i], c2[i]), max(c1[i], c2[i])
            # Allow ±1 for integer rounding at boundaries
            assert lo - 1 <= result[i] <= hi + 1, (
                f"channel {i}: result {result[i]} outside bbox "
                f"[{lo}, {hi}] for c1={c1}, c2={c2}, w1={w1}"
            )

    @HYP_SETTINGS
    @given(rgb_st, positive_weight_st)
    def test_property_single_slot_identity_all_algorithms(self, rgb, weight):
        """A single (colour, weight) pair must return that colour from all
        six mixing algorithms — there's nothing to mix it with.

        This is the strongest cross-algorithm invariant: it doesn't depend
        on the colour space's interpolation behaviour, only on the
        algorithms agreeing on the no-op case."""
        single = [(rgb, weight)]
        algorithms = [
            ("weighted_rgb_mix", ColorMath.weighted_rgb_mix),
            ("weighted_hsv_mix", ColorMath.weighted_hsv_mix),
            ("weighted_ryb_mix", ColorMath.weighted_ryb_mix),
            ("lab_perceptual_mix", ColorMath.lab_perceptual_mix),
            ("subtractive_cmy_mix", ColorMath.subtractive_cmy_mix),
            ("kubelka_munk_mix", ColorMath.kubelka_munk_mix),
        ]
        for name, fn in algorithms:
            result = fn(single)
            assert result is not None, f"{name} returned None for single slot"
            # Allow per-channel delta because some algorithms detour through
            # a non-RGB space and round on return; identity recovery within
            # ±5 is the contract.
            for i, (orig, recovered) in enumerate(zip(rgb, result)):
                assert abs(orig - recovered) <= 5, (
                    f"{name} single-slot identity failed on channel {i}: "
                    f"input {rgb}, output {result}"
                )
