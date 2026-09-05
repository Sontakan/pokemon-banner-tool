"""Example / edge-case (unit) tests for the preserved features (task 8.1).

These are deterministic example/unit tests (not property tests). Where the
behavior is covered by the pure Python reference ports in this ``tests/``
folder, we assert against those modules directly. For behaviors that only exist
in the browser JS (DOM/network/UI wiring that cannot run headlessly here), we
assert against the exact content of ``pokemon-banner-tool/index.html``.

Covered acceptance criteria:
    - 3.1: initial state has the 3 default sections
      ("Megaevolução", "Escuridão Absoluta", "Caos Ascendente").
    - 2.2 / 2.3: ``searchLang`` builds ``name=`` / ``illustrator=`` per the mode
      and appends ``set=`` when a collection filter is present.
    - 2.5: fallback to ``en`` when the chosen language returns no results
      (and ``en`` itself does not trigger a second call).
    - 2.8 / 3.6: validations that fire ``alert`` and keep the state unchanged.
    - 4.5: ``clearDraft`` gated by ``confirm`` (true restores default; false keeps state).
    - 4.7: ``.card-remove`` gets ``display:none`` before ``html2canvas`` is called.

Requirements: 2.2, 2.3, 2.5, 2.8, 3.1, 3.6, 4.5, 4.7
"""

from __future__ import annotations

import copy
import os
import re
from typing import List, Optional

from search_ref import img_url  # sanity import: reference modules are importable
from sections_ref import add_card


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INDEX_HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html"
)


def _read_index_html() -> str:
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


# Default section names shared by the initial state and by clearDraft's reset.
DEFAULT_SECTION_NAMES = ["Megaevolução", "Escuridão Absoluta", "Caos Ascendente"]


def build_search_url(base, lang, q, mode, set_filter):
    """Deterministic Python port of ``searchLang``'s URL construction.

    Mirrors the pure part of the JS:

        var params = [];
        if (q) {
            var param = (mode === "illustrator") ? "illustrator" : "name";
            params.push(param + "=" + encodeURIComponent(q));
        }
        if (setFilter) params.push("set=" + encodeURIComponent(setFilter));
        var url = TCGDEX_URL + "/" + lang + "/cards?" + params.join("&");

    Only ASCII/simple values are used by the callers below, so a plain join is
    a faithful stand-in for ``encodeURIComponent`` here (the tests use values
    that need no escaping, keeping them deterministic and readable).
    """
    params: List[str] = []
    if q:
        param = "illustrator" if mode == "illustrator" else "name"
        params.append(param + "=" + q)
    if set_filter:
        params.append("set=" + set_filter)
    return base + "/" + lang + "/cards?" + "&".join(params)


class FakeSearch:
    """Records ``searchLang`` calls and returns scripted results per language.

    Used to model the ``doSearch`` fallback loop without a browser/network:

        results = searchLang(q, lang, mode, setFilter)
        if results and len(results) == 0 and lang != "en":
            results = searchLang(q, "en", mode, setFilter)
    """

    def __init__(self, by_lang):
        self.by_lang = by_lang
        self.calls: List[str] = []

    def __call__(self, q, lang, mode, set_filter) -> Optional[list]:
        self.calls.append(lang)
        return self.by_lang.get(lang)


def run_search_with_fallback(fake: FakeSearch, q, lang, mode, set_filter):
    """Port of the ``doSearch`` result/fallback logic (post-validation)."""
    results = fake(q, lang, mode, set_filter)
    if results is not None and len(results) == 0 and lang != "en":
        results = fake(q, "en", mode, set_filter)
    return results


# ---------------------------------------------------------------------------
# 3.1 — initial state has the 3 default sections
# ---------------------------------------------------------------------------


def test_initial_state_has_three_default_sections_in_source():
    """3.1: the JS initial ``sections`` array declares the 3 default sections."""
    html = _read_index_html()

    # Locate the initial state declaration: `var sections = [ ... ];`
    m = re.search(r"var\s+sections\s*=\s*\[(.*?)\];", html, re.DOTALL)
    assert m, "initial `var sections = [...]` declaration not found"
    block = m.group(1)

    # Exactly the three default sections, each empty, in order.
    for name in DEFAULT_SECTION_NAMES:
        assert '{ name: "%s", cards: [] }' % name in block, (
            "default section %r missing from initial state" % name
        )

    # No extra sections declared in the initial array.
    assert block.count("name:") == 3


def test_default_section_names_content_and_order():
    """3.1: the default section names/order match the spec exactly."""
    assert DEFAULT_SECTION_NAMES == [
        "Megaevolução",
        "Escuridão Absoluta",
        "Caos Ascendente",
    ]


# ---------------------------------------------------------------------------
# 2.2 / 2.3 — searchLang builds name=/illustrator= and adds set=
# ---------------------------------------------------------------------------

BASE = "https://api.tcgdex.net/v2"


def test_search_url_uses_name_param_in_name_mode():
    """2.2: name mode builds ``name=<q>``."""
    url = build_search_url(BASE, "pt", "pikachu", "name", "")
    assert url == BASE + "/pt/cards?name=pikachu"


def test_search_url_uses_illustrator_param_in_illustrator_mode():
    """2.2: illustrator mode builds ``illustrator=<q>``."""
    url = build_search_url(BASE, "pt", "arita", "illustrator", "")
    assert url == BASE + "/pt/cards?illustrator=arita"


def test_search_url_appends_set_filter():
    """2.3: a selected collection appends ``set=<id>``."""
    url = build_search_url(BASE, "en", "pikachu", "name", "me01")
    assert url == BASE + "/en/cards?name=pikachu&set=me01"


def test_search_url_set_only_without_name():
    """2.3: searching by collection alone yields only ``set=`` (no name/illustrator)."""
    url = build_search_url(BASE, "en", "", "name", "me01")
    assert url == BASE + "/en/cards?set=me01"


def test_search_url_construction_present_in_source():
    """2.2 / 2.3: the JS source contains the exact param-building logic."""
    html = _read_index_html()
    assert 'var param = (mode === "illustrator") ? "illustrator" : "name";' in html
    assert 'params.push(param + "=" + encodeURIComponent(q));' in html
    assert 'if (setFilter) params.push("set=" + encodeURIComponent(setFilter));' in html


# ---------------------------------------------------------------------------
# 2.5 — fallback to en when the chosen language returns no results
# ---------------------------------------------------------------------------


def test_fallback_to_en_when_chosen_lang_empty():
    """2.5: empty results in a non-en language triggers a second call in ``en``."""
    fake = FakeSearch({"pt": [], "en": [{"id": "me01-1", "image": "x"}]})
    results = run_search_with_fallback(fake, "pikachu", "pt", "name", "")

    assert fake.calls == ["pt", "en"], "expected pt then en fallback"
    assert results == [{"id": "me01-1", "image": "x"}]


def test_no_fallback_when_chosen_lang_has_results():
    """2.5: a non-empty result set does not trigger a fallback call."""
    fake = FakeSearch({"pt": [{"id": "me01-1", "image": "x"}]})
    results = run_search_with_fallback(fake, "pikachu", "pt", "name", "")

    assert fake.calls == ["pt"], "no fallback expected when results are present"
    assert len(results) == 1


def test_en_does_not_trigger_second_call_when_empty():
    """2.5: ``en`` itself never triggers a second (redundant) fallback call."""
    fake = FakeSearch({"en": []})
    results = run_search_with_fallback(fake, "pikachu", "en", "name", "")

    assert fake.calls == ["en"], "en must not fall back to itself"
    assert results == []


def test_no_fallback_on_network_error():
    """2.5: a network error (None) is returned as-is, no fallback."""
    fake = FakeSearch({"pt": None})
    results = run_search_with_fallback(fake, "pikachu", "pt", "name", "")

    assert fake.calls == ["pt"]
    assert results is None


def test_fallback_logic_present_in_source():
    """2.5: the JS source contains the fallback condition."""
    html = _read_index_html()
    assert 'if (results && results.length === 0 && lang !== "en") {' in html
    assert 'results = await searchLang(q, "en", mode, setFilter);' in html


# ---------------------------------------------------------------------------
# 2.8 — search with neither name nor collection alerts and does not query
# ---------------------------------------------------------------------------


def test_empty_search_alerts_and_does_not_call_network():
    """2.8: no name and no collection => alert, and no ``searchLang`` call.

    Models the guard: ``if (!q && !setFilter) { alert(...); return; }``.
    """
    fake = FakeSearch({"pt": [{"id": "x", "image": "y"}]})

    q, set_filter = "", ""
    alerted = False
    if not q and not set_filter:
        alerted = True  # JS: alert("Digite um nome ou escolha uma coleção."); return;
    else:  # pragma: no cover - not exercised in this case
        run_search_with_fallback(fake, q, "pt", "name", set_filter)

    assert alerted is True
    assert fake.calls == [], "no network call should happen on empty search"


def test_empty_search_guard_present_in_source():
    """2.8: the JS source contains the empty-search guard + alert message."""
    html = _read_index_html()
    assert 'if (!q && !setFilter) { alert("Digite um nome ou escolha uma coleção."); return; }' in html


# ---------------------------------------------------------------------------
# 3.6 — addCard with no valid section alerts and keeps the state unchanged
# ---------------------------------------------------------------------------

SAMPLE_CARD = {
    "id": "me01-18",
    "name": "Pikachu",
    "image": "https://img/high.webp",
    "set": "Megaevolução · 18",
    "variant": "reverse",
}


def test_add_card_with_no_sections_keeps_state_unchanged():
    """3.6: adding a card when there are no sections leaves the state unchanged."""
    sections: list = []
    before = copy.deepcopy(sections)

    add_card(sections, "", SAMPLE_CARD)  # empty select value => parseInt -> NaN

    assert sections == before


def test_add_card_with_invalid_index_keeps_state_unchanged():
    """3.6: an out-of-range target index leaves the state unchanged."""
    sections = [{"name": "A", "cards": []}]
    before = copy.deepcopy(sections)

    add_card(sections, 5, SAMPLE_CARD)  # index 5 does not exist

    assert sections == before


def test_add_card_with_valid_index_appends_card():
    """3.6 (contrast): a valid target index does append the card (state changes)."""
    sections = [{"name": "A", "cards": []}]

    add_card(sections, 0, SAMPLE_CARD)

    assert len(sections[0]["cards"]) == 1
    assert sections[0]["cards"][0] == SAMPLE_CARD


def test_add_card_guard_present_in_source():
    """3.6: the JS source contains the no-section guard + alert message."""
    html = _read_index_html()
    assert 'if (isNaN(idx) || !sections[idx]) { alert("Crie/selecione uma seção primeiro.");' in html


# ---------------------------------------------------------------------------
# 4.5 — clearDraft gated by confirm
# ---------------------------------------------------------------------------


def default_state():
    """The default state clearDraft restores (title/sub/lang + 3 sections)."""
    return {
        "title": "COMPRA OU TROCA",
        "sub": "",
        "lang": "pt",
        "sections": [{"name": n, "cards": []} for n in DEFAULT_SECTION_NAMES],
    }


def clear_draft(state, confirm_result):
    """Port of ``clearDraft``'s control flow gated by ``confirm``.

    JS: ``if (!confirm("Apagar o modelo atual e começar do zero?")) return;``
    then it removes the draft and applies the default state. When ``confirm``
    returns false, the state is left unchanged.
    """
    if not confirm_result:
        return state  # early return: nothing changes
    return default_state()


def test_clear_draft_confirm_true_restores_default():
    """4.5: confirm() == True restores the default 3-section state."""
    current = {
        "title": "algo",
        "sub": "outro",
        "lang": "en",
        "sections": [{"name": "Custom", "cards": [SAMPLE_CARD]}],
    }

    result = clear_draft(current, confirm_result=True)

    assert result == default_state()
    assert [s["name"] for s in result["sections"]] == DEFAULT_SECTION_NAMES


def test_clear_draft_confirm_false_keeps_state():
    """4.5: confirm() == False leaves the current state untouched."""
    current = {
        "title": "algo",
        "sub": "outro",
        "lang": "en",
        "sections": [{"name": "Custom", "cards": [SAMPLE_CARD]}],
    }
    before = copy.deepcopy(current)

    result = clear_draft(current, confirm_result=False)

    assert result == before


def test_clear_draft_confirm_gate_present_in_source():
    """4.5: the JS source gates the reset behind ``confirm`` and restores defaults."""
    html = _read_index_html()
    assert 'if (!confirm("Apagar o modelo atual e começar do zero?")) return;' in html
    # The reset restores the same three default sections.
    reset_region = html[html.index("function clearDraft()"):]
    for name in DEFAULT_SECTION_NAMES:
        assert '{ name: "%s", cards: [] }' % name in reset_region


# ---------------------------------------------------------------------------
# 4.7 — .card-remove display:none is set before html2canvas is called
# ---------------------------------------------------------------------------


def test_card_remove_hidden_before_html2canvas_in_export():
    """4.7: ``exportImage`` hides ``.card-remove`` before calling ``html2canvas``."""
    html = _read_index_html()

    export_start = html.index("async function exportImage()")
    export_region = html[export_start:]

    hide_snippet = (
        'banner.querySelectorAll(".card-remove").forEach('
        'function(b){ b.style.display = "none"; });'
    )
    hide_idx = export_region.find(hide_snippet)
    canvas_idx = export_region.find("html2canvas(banner")

    assert hide_idx != -1, "card-remove hide statement not found in exportImage"
    assert canvas_idx != -1, "html2canvas(banner ...) call not found in exportImage"
    # The hide statement must appear BEFORE the html2canvas capture.
    assert hide_idx < canvas_idx, (
        "card-remove must be hidden before html2canvas is invoked"
    )


def test_export_uses_scale_2():
    """4.7 (context): the capture runs at scale 2x as specified (Req 4.6)."""
    html = _read_index_html()
    export_region = html[html.index("async function exportImage()"):]
    assert "scale: 2," in export_region


def test_card_remove_default_hidden_in_css():
    """4.7 (context): ``.card-remove`` is ``display:none`` by default in the CSS."""
    html = _read_index_html()
    assert re.search(r"\.card-remove\s*\{[^}]*display:\s*none;", html), (
        ".card-remove should be display:none by default in CSS"
    )


# A tiny sanity check that the reference imports resolve in this test module.
def test_reference_modules_importable():
    assert img_url("base", "high") == "base/high.webp"
