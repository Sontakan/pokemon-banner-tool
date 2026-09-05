"""Reference (porta) das funções puras de busca do index.html (pokemon-banner-tool).

Portadas fielmente do JS em `pokemon-banner-tool/index.html`:

    function imgUrl(base, quality) {
        if (!base) return "";
        return base + "/" + (quality || "high") + ".webp";
    }

    function setIdFromCard(cardId) {
        if (!cardId) return "";
        var i = cardId.lastIndexOf("-");
        return i > 0 ? cardId.substring(0, i) : cardId;
    }

    function cardLabel(c) {
        var setId = setIdFromCard(c.id);
        var setName = setMap[setId] || setId;
        var num = c.localId || (c.id ? c.id.substring(c.id.lastIndexOf("-") + 1) : "");
        return setName + (num ? " · " + num : "");
    }

Este módulo é apenas a implementação de referência (reference implementation)
usada pelos testes property-based (tarefas 5.4 e 5.5). Não contém testes.

Notas sobre a fidelidade ao JS:
- Em JS, `!x` é verdadeiro para "" (string vazia), undefined, null, 0, NaN e false.
  Aqui replicamos o comportamento relevante para strings: uma string vazia ou None
  é tratada como "falsy".
- `quality || "high"`: em JS, se `quality` for falsy (ex.: "", None, 0), usa "high".
- `setMap[setId] || setId`: se o set não existe no mapa OU seu nome é falsy (""),
  cai no `setId`.
- `c.localId || (...)`: se `localId` for falsy, usa o sufixo derivado do id.
- `lastIndexOf("-")` e `substring` seguem a semântica do JS (índices e slices).
"""


def _js_falsy(value):
    """Replica a noção de "falsy" do JS para os tipos que aparecem aqui.

    Em JS, os valores falsy são: false, 0, "", null, undefined, NaN.
    Para strings/None (os únicos tipos usados por estas funções), isso equivale a
    "None ou string vazia" (e também 0, caso um número apareça).
    """
    return not value


def img_url(base, quality="high"):
    """Porta de `imgUrl(base, quality)`.

    - Se `base` for falsy (None ou ""), retorna "".
    - Caso contrário, retorna `base + "/" + (quality || "high") + ".webp"`.
      Em JS, `quality || "high"` usa "high" quando `quality` é falsy.
    """
    if _js_falsy(base):
        return ""
    q = quality if not _js_falsy(quality) else "high"
    return base + "/" + q + ".webp"


def set_id_from_card(card_id):
    """Porta de `setIdFromCard(cardId)`.

    Deriva o set-id a partir do id da carta: "swsh4.5-18" -> "swsh4.5".

    - Se `cardId` for falsy (None ou ""), retorna "".
    - `i = cardId.lastIndexOf("-")`.
    - Retorna o prefixo antes do último "-" quando `i > 0`; senão, retorna o id inteiro.

    Detalhe da semântica JS preservado: quando "-" está no início (i == 0) ou
    ausente (i == -1), retorna o `cardId` original inalterado.
    """
    if _js_falsy(card_id):
        return ""
    i = card_id.rfind("-")  # equivalente a String.prototype.lastIndexOf
    return card_id[:i] if i > 0 else card_id


def card_label(card, set_map=None):
    """Porta de `cardLabel(c)`, consultando um `setMap` simulado.

    `card` é um dict com chaves opcionais `id` e `localId` (espelhando o objeto
    de carta do JS). `set_map` é o mapa simulado `{ setId: setName }`
    (o `setMap` global do JS carregado por `loadSetMap`).

    Lógica JS replicada:
        var setId = setIdFromCard(c.id);
        var setName = setMap[setId] || setId;
        var num = c.localId || (c.id ? c.id.substring(c.id.lastIndexOf("-") + 1) : "");
        return setName + (num ? " · " + num : "");

    - `setMap[setId] || setId`: se o mapa não tem `setId` (ou seu valor é falsy),
      usa o próprio `setId` como nome.
    - `num`: usa `localId` se presente (não-falsy); caso contrário, deriva do sufixo
      após o último "-" do `id` (ou "" se não houver `id`).
    - Anexa " · {num}" somente quando `num` é não-falsy.
    """
    if set_map is None:
        set_map = {}

    card_id = card.get("id")
    local_id = card.get("localId")

    set_id = set_id_from_card(card_id)

    # setMap[setId] || setId  -> em JS, chave ausente => undefined (falsy).
    mapped = set_map.get(set_id)
    set_name = mapped if not _js_falsy(mapped) else set_id

    # c.localId || (c.id ? c.id.substring(c.id.lastIndexOf("-")+1) : "")
    if not _js_falsy(local_id):
        num = local_id
    elif not _js_falsy(card_id):
        num = card_id[card_id.rfind("-") + 1:]
    else:
        num = ""

    return set_name + (" · " + num if not _js_falsy(num) else "")
