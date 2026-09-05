"""Property-based test — Property 3: Rótulo de carta contém set e número.

Feature: pokemon-banner-tool, Property 3: Rótulo de carta contém set e número
Validates: Requirements 2.6

Propriedade (do design):
    For any carta com `id` no formato "{setId}-{num}", cardLabel(card) contém o
    nome do set (ou o setId quando o nome é desconhecido) e, quando houver número
    (localId ou sufixo do id), inclui esse número.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from search_ref import card_label, set_id_from_card


# setId: texto não-vazio que NÃO contém "-" para que "{setId}-{num}" tenha um
# único separador previsível (o último "-" delimita o sufixo/número).
set_id_st = st.text(
    alphabet=st.characters(blacklist_characters="-"),
    min_size=1,
).filter(lambda s: bool(s))

# num: sufixo não-vazio após o último "-". Também sem "-" para manter o formato
# "{setId}-{num}" com exatamente um separador relevante.
num_st = st.text(
    alphabet=st.characters(blacklist_characters="-"),
    min_size=1,
).filter(lambda s: bool(s))

# setName: nome amigável do set. Pode ou não estar presente no setMap.
set_name_st = st.text(min_size=1)


@settings(max_examples=100)
@given(
    set_id=set_id_st,
    num=num_st,
    provide_name=st.booleans(),
    set_name=set_name_st,
)
def test_card_label_contains_set_and_number(set_id, num, provide_name, set_name):
    """Feature: pokemon-banner-tool, Property 3: Rótulo de carta contém set e número

    Para id "{setId}-{num}": o rótulo contém o nome do set (quando conhecido no
    setMap) ou o setId (quando desconhecido), e sempre contém o número.
    """
    card_id = set_id + "-" + num
    card = {"id": card_id}

    # setMap opcionalmente contém um nome amigável para o setId.
    set_map = {set_id: set_name} if provide_name else {}

    label = card_label(card, set_map)

    # O identificador do set derivado do id deve bater com o setId gerado.
    assert set_id_from_card(card_id) == set_id

    # Nome esperado: setName quando fornecido (e não-falsy), caso contrário o setId.
    expected_name = set_name if provide_name else set_id
    assert expected_name in label

    # O número deve aparecer no rótulo.
    assert num in label


@settings(max_examples=100)
@given(
    set_id=set_id_st,
    num=num_st,
    local_id=num_st,
    provide_name=st.booleans(),
    set_name=set_name_st,
)
def test_card_label_prefers_local_id_as_number(
    set_id, num, local_id, provide_name, set_name
):
    """Feature: pokemon-banner-tool, Property 3: Rótulo de carta contém set e número

    Quando localId está presente, ele é usado como número no rótulo, e o nome do
    set (ou setId) também aparece.
    """
    card_id = set_id + "-" + num
    card = {"id": card_id, "localId": local_id}

    set_map = {set_id: set_name} if provide_name else {}

    label = card_label(card, set_map)

    expected_name = set_name if provide_name else set_id
    assert expected_name in label
    # localId tem prioridade sobre o sufixo do id.
    assert local_id in label


@settings(max_examples=100)
@given(set_id=set_id_st, num=num_st, provide_name=st.booleans(), set_name=set_name_st)
def test_card_label_exact_format(set_id, num, provide_name, set_name):
    """Feature: pokemon-banner-tool, Property 3: Rótulo de carta contém set e número

    Formato exato: "{setName ou setId} · {num}".
    """
    card_id = set_id + "-" + num
    card = {"id": card_id}
    set_map = {set_id: set_name} if provide_name else {}

    label = card_label(card, set_map)

    expected_name = set_name if provide_name else set_id
    assert label == expected_name + " · " + num


# Exemplos/known-answer para ancorar a propriedade.
def test_card_label_examples():
    # Set conhecido no mapa: usa o nome amigável.
    assert (
        card_label({"id": "me01-18"}, {"me01": "Megaevolução"})
        == "Megaevolução · 18"
    )
    # Set desconhecido: cai no setId.
    assert card_label({"id": "me01-18"}, {}) == "me01 · 18"
    # localId tem prioridade como número.
    assert (
        card_label({"id": "swsh4.5-25", "localId": "SV107"}, {})
        == "swsh4.5 · SV107"
    )
