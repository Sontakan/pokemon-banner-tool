"""Property-based test for adding a card to a section (Property 5).

Feature: pokemon-banner-tool, Property 5: Adicionar carta cresce a seção e preserva a carta

This test exercises the pure Python reference port of the ``add_card`` state
operation from ``sections_ref.py``, which mirrors the JS ``addCard`` logic in
``pokemon-banner-tool/index.html``.

Property 5 (design.md):
    For any state with a valid selected target section and any card,
    ``add_card(card)``:
      - increases the number of cards of the target section by exactly 1;
      - does not change the other sections;
      - the last card of the target section equals the provided card
        (including its variant).

Validates: Requirements 3.3
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from hypothesis import given, settings
from hypothesis import strategies as st

from sections_ref import VARIANTS, add_card


# ---------- smart generators constrained to the section/card input space ----------

# Card shape mirrors design Data Models: id/name/image/set/variant.
cards = st.fixed_dictionaries(
    {
        "id": st.text(min_size=0, max_size=12),
        "name": st.text(min_size=0, max_size=20),
        "image": st.text(min_size=0, max_size=30),
        "set": st.text(min_size=0, max_size=20),
        "variant": st.sampled_from(VARIANTS),
    }
)

# Section shape: a name plus a (possibly empty) list of cards.
sections = st.fixed_dictionaries(
    {
        "name": st.text(min_size=0, max_size=25),
        "cards": st.lists(cards, max_size=4),
    }
)

# A non-empty list of sections is required so there is a valid target index.
non_empty_section_lists = st.lists(sections, min_size=1, max_size=6)


@st.composite
def sections_with_target(draw):
    """Generate a non-empty section list together with a valid target index."""
    secs = draw(non_empty_section_lists)
    idx = draw(st.integers(min_value=0, max_value=len(secs) - 1))
    return secs, idx


@settings(max_examples=100)
@given(data=sections_with_target(), card=cards)
def test_add_card_grows_target_and_preserves_card(data, card: Dict[str, Any]):
    """Feature: pokemon-banner-tool, Property 5: Adicionar carta cresce a seção e preserva a carta

    add_card: +1 card in the target section, other sections unchanged, and the
    last card of the target section equals the provided card (with variant).
    """
    secs, target_idx = data
    before = copy.deepcopy(secs)
    original_target_len = len(secs[target_idx]["cards"])

    add_card(secs, target_idx, card)

    # The target section grew by exactly one card.
    assert len(secs[target_idx]["cards"]) == original_target_len + 1
    # The last card of the target section is exactly the provided card,
    # including its variant.
    assert secs[target_idx]["cards"][-1] == card
    # The prefix of the target section's cards is untouched.
    assert secs[target_idx]["cards"][:original_target_len] == before[target_idx]["cards"]
    # Every other section is completely unchanged.
    for j in range(len(secs)):
        if j != target_idx:
            assert secs[j] == before[j]
