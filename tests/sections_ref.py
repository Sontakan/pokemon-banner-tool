"""Pure Python reference port of the section/card state operations from
``pokemon-banner-tool/index.html``.

These functions model the JS logic that manipulates the ``sections`` state
without any DOM/render side effects. Only the state transformations are
reproduced here so they can be exercised by property-based tests.

Original JS (index.html):

    var VARIANTS = ["normal", "reverse", "foil"];

    function addSection() {
        sections.push({ name: "Nova coleção", cards: [] });
        // ...renders (DOM side effects, omitted here)
    }

    function removeSection(i) {
        sections.splice(i, 1);
        // ...renders
    }

    function renameSection(i, val) {
        sections[i].name = val;
        // ...renders
    }

    function addCard(card) {
        var idx = parseInt(document.getElementById("target-section").value);
        if (isNaN(idx) || !sections[idx]) { alert("Crie/selecione uma seção primeiro."); return; }
        sections[idx].cards.push(card);
        // ...renders
    }

    function cycleVariant(si, ci) {
        var cur = sections[si].cards[ci].variant;
        var next = VARIANTS[(VARIANTS.indexOf(cur) + 1) % VARIANTS.length];
        sections[si].cards[ci].variant = next;
        // ...renders
    }

Data shapes (mirroring the design's Data Models):

    Card    = {"id": str, "name": str, "image": str, "set": str, "variant": str}
    Section = {"name": str, "cards": list[Card]}

The functions below operate on a ``sections`` list (``list[Section]``) and
mutate it in place, exactly like the JS versions (which mutate the global
``sections`` array via ``push``/``splice`` and property assignment).
"""

from __future__ import annotations

from typing import Any, Dict, List

# Matches `var VARIANTS` in index.html.
# Variant cycle order: normal -> reverse -> foil -> exreg -> illust -> ultra -> hyper (-> normal).
VARIANTS: List[str] = ["normal", "reverse", "illust", "altart", "gold", "exreg", "sar"]

# Default new-section name used by the JS `addSection` (sections.push({ name: "Nova coleção", cards: [] })).
NEW_SECTION_NAME = "Nova coleção"

Card = Dict[str, Any]
Section = Dict[str, Any]


def add_section(sections: List[Section]) -> List[Section]:
    """Append a new empty section named "Nova coleção" to the end.

    Mirrors JS ``addSection``: ``sections.push({ name: "Nova coleção", cards: [] })``.
    Mutates ``sections`` in place and returns it for convenience.
    """
    sections.append({"name": NEW_SECTION_NAME, "cards": []})
    return sections


def remove_section(sections: List[Section], i: int) -> List[Section]:
    """Remove the i-th section, preserving the order of the others.

    Mirrors JS ``removeSection(i)``: ``sections.splice(i, 1)``.
    Mutates ``sections`` in place and returns it.
    """
    del sections[i]
    return sections


def rename_section(sections: List[Section], i: int, val: str) -> List[Section]:
    """Set the name of the i-th section to ``val``.

    Mirrors JS ``renameSection(i, val)``: ``sections[i].name = val``.
    Only the name of the i-th section changes; its cards and every other
    section remain untouched. Mutates ``sections`` in place and returns it.
    """
    sections[i]["name"] = val
    return sections


def add_card(sections: List[Section], target_idx: Any, card: Card) -> List[Section]:
    """Append ``card`` to the target section's cards.

    Mirrors JS ``addCard(card)``. In the JS, the target index comes from the
    ``#target-section`` select via ``parseInt(...)``; here it is passed in as
    ``target_idx``. The guard reproduces the JS semantics:

        var idx = parseInt(...);
        if (isNaN(idx) || !sections[idx]) { alert(...); return; }
        sections[idx].cards.push(card);

    If the target index is invalid (not a usable integer index, or out of
    range), the state is left unchanged (the JS ``alert`` + early ``return``).
    Mutates ``sections`` in place and returns it.
    """
    idx = _parse_int(target_idx)
    if idx is None or not _section_exists(sections, idx):
        # JS: alert("Crie/selecione uma seção primeiro."); return; (state unchanged)
        return sections
    sections[idx]["cards"].append(card)
    return sections


def cycle_variant(sections: List[Section], si: int, ci: int) -> List[Section]:
    """Advance the variant of the card at (si, ci) to the next in VARIANTS.

    Mirrors JS ``cycleVariant(si, ci)``:
        var next = VARIANTS[(VARIANTS.indexOf(cur) + 1) % VARIANTS.length];
    Cycle order is normal -> reverse -> foil -> normal. Mutates ``sections``
    in place and returns it.
    """
    cur = sections[si]["cards"][ci]["variant"]
    nxt = VARIANTS[(VARIANTS.index(cur) + 1) % len(VARIANTS)]
    sections[si]["cards"][ci]["variant"] = nxt
    return sections


# ---------- helpers mirroring JS coercion semantics ----------

def _parse_int(value: Any) -> Any:
    """Approximate JS ``parseInt`` for the values relevant to ``addCard``.

    Returns an ``int`` when the value can be interpreted as an integer index,
    otherwise ``None`` (mirroring JS ``NaN``, which fails the ``isNaN`` guard).
    """
    if isinstance(value, bool):
        # In JS, parseInt(true) is NaN. Guard against Python treating bools as ints.
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        # parseInt truncates towards zero for finite numbers.
        if value != value:  # NaN
            return None
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            # JS: parseInt("") -> NaN
            return None
        # parseInt reads leading integer digits; keep it simple for index-like strings.
        sign = ""
        if s[0] in "+-":
            sign, s = s[0], s[1:]
        digits = ""
        for ch in s:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            return None
        n = int(sign + digits) if sign == "-" else int(digits)
        return n
    return None


def _section_exists(sections: List[Section], idx: int) -> bool:
    """Reproduce the JS truthiness check ``!sections[idx]``.

    JS array access with a negative or out-of-range index yields ``undefined``
    (falsy); a valid index yields the (truthy) section object.
    """
    return 0 <= idx < len(sections)
