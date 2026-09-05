"""Property-based tests for section operations (Property 4).

Feature: pokemon-banner-tool, Property 4: Operações de seção preservam invariantes

These tests exercise the pure Python reference port of the section state
operations (``add_section``, ``remove_section``, ``rename_section``) from
``sections_ref.py``, which mirrors the JS logic in
``pokemon-banner-tool/index.html``.

Property 4 (design.md):
    For any list of sections:
      - ``add_section()`` increases the total number of sections by exactly 1
        (a new empty section appended at the end);
      - ``remove_section(i)`` decreases it by exactly 1 and removes the i-th
        section, preserving the order of the others;
      - ``rename_section(i, v)`` changes only the name of the i-th section to
        ``v``, leaving cards and every other section unchanged.

Validates: Requirements 3.2
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from hypothesis import given, settings
from hypothesis import strategies as st

from sections_ref import (
    NEW_SECTION_NAME,
    VARIANTS,
    add_section,
    remove_section,
    rename_section,
)


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

# A non-empty list of sections is required to have a valid index for
# remove/rename; keep the list bounded so tests stay fast.
non_empty_section_lists = st.lists(sections, min_size=1, max_size=6)
any_section_lists = st.lists(sections, max_size=6)


@st.composite
def sections_with_index(draw):
    """Generate a non-empty section list together with a valid index into it."""
    secs = draw(non_empty_section_lists)
    idx = draw(st.integers(min_value=0, max_value=len(secs) - 1))
    return secs, idx


# ---------- Property 4: add_section ----------


@settings(max_examples=100)
@given(secs=any_section_lists)
def test_add_section_appends_one_empty_section_at_end(secs: List[Dict[str, Any]]):
    """Feature: pokemon-banner-tool, Property 4: Operações de seção preservam invariantes

    add: +1 empty section appended at the end; existing sections unchanged.
    """
    before = copy.deepcopy(secs)
    original_len = len(secs)

    add_section(secs)

    # Exactly one more section.
    assert len(secs) == original_len + 1
    # The prefix (all pre-existing sections) is untouched and keeps its order.
    assert secs[:original_len] == before
    # The appended section is a new empty section with the default name.
    assert secs[-1] == {"name": NEW_SECTION_NAME, "cards": []}


# ---------- Property 4: remove_section ----------


@settings(max_examples=100)
@given(data=sections_with_index())
def test_remove_section_drops_ith_and_preserves_order(data):
    """Feature: pokemon-banner-tool, Property 4: Operações de seção preservam invariantes

    remove(i): -1 section; the i-th is removed and the remaining order is preserved.
    """
    secs, i = data
    before = copy.deepcopy(secs)
    original_len = len(secs)

    remove_section(secs, i)

    # Exactly one fewer section.
    assert len(secs) == original_len - 1
    # Order preserved: everything before i stays, everything after i shifts left by one.
    expected = before[:i] + before[i + 1 :]
    assert secs == expected


# ---------- Property 4: rename_section ----------


@settings(max_examples=100)
@given(data=sections_with_index(), new_name=st.text(max_size=30))
def test_rename_section_changes_only_ith_name(data, new_name: str):
    """Feature: pokemon-banner-tool, Property 4: Operações de seção preservam invariantes

    rename(i, v): only the i-th section's name changes; its cards and every
    other section are left unchanged.
    """
    secs, i = data
    before = copy.deepcopy(secs)

    rename_section(secs, i, new_name)

    # Same number of sections.
    assert len(secs) == len(before)
    # The i-th section's name is exactly the new value; its cards are unchanged.
    assert secs[i]["name"] == new_name
    assert secs[i]["cards"] == before[i]["cards"]
    # Every other section is completely unchanged.
    for j in range(len(secs)):
        if j != i:
            assert secs[j] == before[j]
