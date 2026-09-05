"""Property-based tests for set ordering (Property 7).

Feature: pokemon-banner-tool, Property 7: Ordenação de sets é o reverso da API

These tests exercise the pure Python reference port of the set-ordering logic
from ``populateSetDropdown`` (see ``setorder_ref.py``), which mirrors the JS in
``pokemon-banner-tool/index.html``:

    var list = setList.slice().reverse();
    list.forEach(function (s) {
        if (!s.name) return;              // ignora sets sem nome
        ...
    });

Property 7 (design.md):
    For any list of sets returned by the API, the order shown in the collection
    dropdown (options, ignoring the fixed "Todas as coleções" option) is the
    exact reverse of the order received from the API — so the most recent sets
    appear first.

Since the reference drops sets without a name, the property compares the
dropdown output against the reverse of the API list *restricted to named sets*.

Validates: Requirements 2.4
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from hypothesis import given, settings
from hypothesis import strategies as st

from setorder_ref import _has_name, dropdown_options, order_sets


# ---------- smart generators constrained to the sets input space ----------

# A set as returned by TCGdex /{lang}/sets: always has an id; name is optional
# and may be missing, empty, or a real string. We include falsy names (empty
# string, missing key) so the "drop sets without a name" behaviour is exercised.
_ids = st.text(min_size=1, max_size=10)
_names = st.one_of(
    st.text(min_size=1, max_size=20),  # real names (kept)
    st.just(""),  # falsy name (dropped)
)


@st.composite
def _sets(draw):
    """Generate a single set descriptor, sometimes omitting the name key."""
    s: Dict[str, Any] = {"id": draw(_ids)}
    # Sometimes include a name key (real or empty), sometimes omit it entirely.
    if draw(st.booleans()):
        s["name"] = draw(_names)
    return s


set_lists = st.lists(_sets(), max_size=12)


# ---------- Property 7: dropdown order is the reverse of the (named) API list ----------


@settings(max_examples=100)
@given(set_list=set_lists)
def test_dropdown_order_is_reverse_of_named_api_list(set_list: List[Dict[str, Any]]):
    """Feature: pokemon-banner-tool, Property 7: Ordenação de sets é o reverso da API

    The ordered sets (ignoring the fixed "Todas as coleções" option) equal the
    reverse of the API list restricted to named sets.
    """
    before = copy.deepcopy(set_list)

    ordered = order_sets(set_list)

    # Expected: reverse of the API list, keeping only sets with a truthy name.
    expected = [s for s in reversed(set_list) if _has_name(s)]
    assert ordered == expected

    # The input list must not be mutated (slice() semantics in the JS).
    assert set_list == before


@settings(max_examples=100)
@given(set_list=set_lists)
def test_dropdown_options_match_ordered_sets(set_list: List[Dict[str, Any]]):
    """Feature: pokemon-banner-tool, Property 7: Ordenação de sets é o reverso da API

    The option descriptors are one-per-named-set, in reverse-of-API order, and
    carry value=id and text="name (id)".
    """
    ordered = order_sets(set_list)
    options = dropdown_options(set_list)

    # One option per named set, in the same (reversed) order.
    assert len(options) == len(ordered)
    for opt, s in zip(options, ordered):
        assert opt["value"] == str(s.get("id", ""))
        assert opt["text"] == "{} ({})".format(s.get("name"), s.get("id", ""))
