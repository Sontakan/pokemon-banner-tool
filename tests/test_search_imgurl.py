"""Property-based test — Property 2: URL de imagem bem-formada.

Feature: pokemon-banner-tool, Property 2: URL de imagem bem-formada
Validates: Requirements 2.7

Propriedade (do design):
    For any base de imagem não-vazia e qualquer qualidade em {high, low},
    imgUrl(base, quality) retorna exatamente base + "/" + quality + ".webp"
    (e string vazia quando a base é vazia).
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from search_ref import img_url


# Qualidades definidas pela propriedade: {high, low}.
QUALITIES = ["high", "low"]

# Bases não-vazias: qualquer texto que não seja "falsy" em JS.
# Uma base é "falsy" apenas quando vazia (""); portanto exigimos min_size=1.
non_empty_base = st.text(min_size=1)


@settings(max_examples=100)
@given(base=non_empty_base, quality=st.sampled_from(QUALITIES))
def test_img_url_well_formed(base, quality):
    """Feature: pokemon-banner-tool, Property 2: URL de imagem bem-formada

    Para base não-vazia e quality em {high, low}:
        img_url(base, quality) == base + "/" + quality + ".webp"
    """
    assert img_url(base, quality) == base + "/" + quality + ".webp"


@settings(max_examples=100)
@given(quality=st.sampled_from(QUALITIES))
def test_img_url_empty_base_returns_empty(quality):
    """Feature: pokemon-banner-tool, Property 2: URL de imagem bem-formada

    Base vazia sempre resulta em "" independentemente da qualidade.
    """
    assert img_url("", quality) == ""


# Exemplo/known-answer para ancorar a propriedade.
def test_img_url_examples():
    assert img_url("https://x/img", "high") == "https://x/img/high.webp"
    assert img_url("https://x/img", "low") == "https://x/img/low.webp"
    assert img_url("") == ""
