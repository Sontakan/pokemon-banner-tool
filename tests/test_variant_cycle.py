"""Property-based test for the variant cycle (Property 6).

Feature: pokemon-banner-tool, Property 6: Ciclo de variante é cíclico de período 3

This test exercises the pure Python reference port of the ``cycle_variant``
state operation from ``sections_ref.py``, which mirrors the JS ``cycleVariant``
logic in ``pokemon-banner-tool/index.html``.

Property 6 (design.md):
    For any card with any initial variant in {normal, reverse, foil}, one
    application of ``cycle_variant`` advances to the next variant in the order
    normal -> reverse -> foil, and three consecutive applications return to the
    initial variant.

Validates: Requirements 3.4
"""

from __future__ import annotations

from typing import Any, Dict, List

from hypothesis import given, settings
from hypothesis import strategies as st

from sections_ref import VARIANTS, cycle_variant


# Expected one-step transition: the next variant in VARIANTS, wrapping around.
NEXT_VARIANT = {
    v: VARIANTS[(i + 1) % len(VARIANTS)] for i, v in enumerate(VARIANTS)
}


def _make_sections(variant: str) -> List[Dict[str, Any]]:
    """Build a minimal sections list holding a single card with ``variant``."""
    return [
        {
            "name": "S",
            "cards": [
                {
                    "id": "me01-1",
                    "name": "Card",
                    "image": "img",
                    "set": "Set · 1",
                    "variant": variant,
                }
            ],
        }
    ]


@settings(max_examples=100)
@given(initial=st.sampled_from(VARIANTS))
def test_variant_cycle_is_cyclic(initial: str):
    """Feature: pokemon-banner-tool, Property 6: Ciclo de variante é cíclico

    One step advances to the next variant in VARIANTS; len(VARIANTS) steps
    return to the initial variant.
    """
    secs = _make_sections(initial)

    # One application advances to the next variant in the defined order.
    cycle_variant(secs, 0, 0)
    assert secs[0]["cards"][0]["variant"] == NEXT_VARIANT[initial]

    # Completing a full cycle returns to the initial variant.
    for _ in range(len(VARIANTS) - 1):
        cycle_variant(secs, 0, 0)
    assert secs[0]["cards"][0]["variant"] == initial
