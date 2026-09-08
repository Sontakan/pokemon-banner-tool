"""Reference implementation (Python port) of the banner-state encode/decode logic.

This module ports the *pure* persistence functions from
``pokemon-banner-tool/index.html`` so they can be exercised with property-based
tests (Hypothesis) without a Node/browser runtime.

JS reference (from index.html)::

    function collectState() {
        return { title, sub, lang, sections };
    }

    function encodeState() {
        var json = JSON.stringify(collectState());
        return btoa(unescape(encodeURIComponent(json)));   // UTF-8 -> base64
    }

    function decodeState(code) {
        var json = decodeURIComponent(escape(atob(code.trim())));  // base64 -> UTF-8
        return JSON.parse(json);
    }

Equivalences used here:

* ``btoa(unescape(encodeURIComponent(json)))`` encodes ``json`` as UTF-8 bytes
  and then base64-encodes them. The Python equivalent is
  ``base64.b64encode(json.encode("utf-8"))``.
* ``decodeURIComponent(escape(atob(code)))`` is the exact inverse: base64-decode
  to UTF-8 bytes, then decode as UTF-8. The Python equivalent is
  ``base64.b64decode(code).decode("utf-8")``.
* ``JSON.stringify`` (with no replacer/space) produces compact JSON with no
  whitespace between tokens. The matching Python call is
  ``json.dumps(state, ensure_ascii=False, separators=(",", ":"))``.

This module intentionally contains only the reference implementation and the
Hypothesis strategies (generators). The actual property test lives in task 5.2.
"""

from __future__ import annotations

import base64
import json as _json
from typing import Any, Dict, List

from hypothesis import strategies as st

# The variants a card can be tagged with, matching VARIANTS in the JS.
VARIANTS: List[str] = ["normal", "reverse", "illust", "altart", "gold", "exreg", "sar"]


# ---------------------------------------------------------------------------
# Reference implementation (pure functions)
# ---------------------------------------------------------------------------

def encode_state(state: Dict[str, Any]) -> str:
    """Port of ``encodeState`` — serialize ``state`` to compact JSON and base64.

    Mirrors ``btoa(unescape(encodeURIComponent(JSON.stringify(state))))``.
    """
    json_str = _json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(json_str.encode("utf-8")).decode("ascii")


def decode_state(code: str) -> Dict[str, Any]:
    """Port of ``decodeState`` — inverse of :func:`encode_state`.

    Mirrors ``JSON.parse(decodeURIComponent(escape(atob(code.trim()))))``.
    """
    json_str = base64.b64decode(code.strip()).decode("utf-8")
    return _json.loads(json_str)


# ---------------------------------------------------------------------------
# Hypothesis strategies (generators) for the BannerState data model
# ---------------------------------------------------------------------------
#
# Data model (from design.md):
#
#   Card    = { id, name, image, set, variant }
#   Section = { name, cards: Card[] }
#   State   = { title, sub, lang, sections: Section[] }
#
# The strategies below produce structurally valid states with unicode/accented
# text so the round-trip is exercised against tricky characters.

# Text with unicode/accents. We exclude surrogate code points because they are
# not representable in UTF-8 and therefore cannot survive a JSON/UTF-8 round-trip
# (JS strings can hold lone surrogates, but the encodeState/decodeState pipeline
# goes through UTF-8, matching this constraint).
unicode_text = st.text(
    alphabet=st.characters(
        min_codepoint=0x20,
        max_codepoint=0x2FFF,
        blacklist_categories=("Cs",),  # exclude surrogates
    ),
    min_size=0,
    max_size=40,
)

# Language code — matches the {pt, en, ja} options exposed by the UI.
lang_strategy = st.sampled_from(["pt", "en", "ja"])

# Variant — one of the three valid values.
variant_strategy = st.sampled_from(VARIANTS)


def card_strategy() -> st.SearchStrategy[Dict[str, Any]]:
    """A single Card object matching the JS shape produced by addCard(...)."""
    return st.fixed_dictionaries(
        {
            "id": unicode_text,
            "name": unicode_text,
            "image": unicode_text,
            "set": unicode_text,
            "variant": variant_strategy,
        }
    )


def section_strategy(max_cards: int = 4) -> st.SearchStrategy[Dict[str, Any]]:
    """A Section with a name and M cards (0..max_cards)."""
    return st.fixed_dictionaries(
        {
            "name": unicode_text,
            "cards": st.lists(card_strategy(), min_size=0, max_size=max_cards),
        }
    )


def banner_state_strategy(
    max_sections: int = 4, max_cards: int = 4
) -> st.SearchStrategy[Dict[str, Any]]:
    """A full BannerState with N sections, each holding M cards.

    Field order matches ``collectState()`` (title, sub, lang, sections) so the
    generated dicts closely mirror what the app persists.
    """
    return st.fixed_dictionaries(
        {
            "title": unicode_text,
            "sub": unicode_text,
            "lang": lang_strategy,
            "sections": st.lists(
                section_strategy(max_cards=max_cards),
                min_size=0,
                max_size=max_sections,
            ),
        }
    )
