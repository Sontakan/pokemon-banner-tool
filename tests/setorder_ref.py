"""Reference port of the pure set-ordering logic from ``populateSetDropdown``.

Origin: ``pokemon-banner-tool/index.html`` — function ``populateSetDropdown``.

The JS builds the collection dropdown like this (relevant, pure part):

    // a API devolve dos mais antigos aos mais novos; invertemos para os
    // recentes ficarem no topo
    var list = setList.slice().reverse();
    list.forEach(function (s) {
        if (!s.name) return;              // ignora sets sem nome
        var o = document.createElement("option");
        o.value = s.id;
        o.textContent = s.name + " (" + s.id + ")";
        sel.appendChild(o);
    });

This module isolates that transformation (no DOM) so it can be exercised by
property-based tests. It intentionally does NOT reproduce the fixed
"Todas as coleções" option — the dropdown always prepends that option before
the ordered sets; the tests compare against the *sets* portion only.

Requirements: 2.4
"""

from __future__ import annotations

from typing import Any, Dict, List


def _has_name(s: Dict[str, Any]) -> bool:
    """Replicate JS truthiness of ``s.name`` (``if (!s.name) return;``).

    In JS, ``""``, ``None``/``undefined``, ``0`` and ``False`` are all falsy,
    so those sets are skipped. Any other value keeps the set.
    """
    return bool(s.get("name"))


def order_sets(set_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return sets in dropdown order: reverse of the API list, dropping
    entries without a ``name``.

    Mirrors ``setList.slice().reverse()`` followed by the ``if (!s.name) return;``
    filter inside ``populateSetDropdown``. The input list is not mutated
    (``slice()`` semantics).

    Args:
        set_list: sets as returned by the TCGdex ``/{lang}/sets`` endpoint,
            oldest-to-newest. Each set is a mapping with at least ``id`` and,
            optionally, ``name``.

    Returns:
        A new list, newest-first, containing only sets that have a truthy name.
    """
    reversed_list = list(reversed(set_list))  # slice().reverse() — copy, no mutation
    return [s for s in reversed_list if _has_name(s)]


def dropdown_options(set_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build the option descriptors for the ordered sets (sets portion only).

    Mirrors the per-set option built in the JS ``forEach``:
        o.value = s.id;
        o.textContent = s.name + " (" + s.id + ")";

    The fixed leading "Todas as coleções" option is intentionally omitted.

    Args:
        set_list: sets from the API (oldest-to-newest).

    Returns:
        One ``{"value", "text"}`` descriptor per named set, newest-first.
    """
    options: List[Dict[str, str]] = []
    for s in order_sets(set_list):
        options.append(
            {
                "value": str(s.get("id", "")),
                "text": "{} ({})".format(s.get("name"), s.get("id", "")),
            }
        )
    return options
