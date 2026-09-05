# 🎴 Pokémon Banner Tool — Gerador de Banner "Compra ou Troca"

Ferramenta web de **página única** (`index.html`, sem backend) para montar banners de
"Compra ou Troca" de cartas Pokémon, prontos para postar no WhatsApp. Você busca cartas
na API pública **TCGdex**, organiza em seções, marca a variante que procura de cada carta
(Normal / Reverse / Foil), edita os textos do banner e exporta tudo como imagem **PNG**.

Todo o processamento acontece no navegador — não há servidor, build step nem chaves
secretas. As dependências externas (html2canvas e, opcionalmente, uma lib de QR Code)
entram apenas via CDN.

## ✨ Funcionalidades

- **Busca de cartas (TCGdex):** pesquisa por **nome** ou **ilustrador**, filtrando por
  **coleção** e por **idioma das imagens** (PT / EN / JP), com _fallback_ automático para EN
  quando o idioma escolhido não retorna resultados.
- **Seções e variantes:** organize as cartas em seções editáveis (criar, renomear e apagar)
  e marque a variante procurada de cada carta alternando entre ⚪ Normal → ◇ Reverse → ⭐ Foil.
- **Textos do banner:** edite título e subtítulo com atualização do preview em tempo real.
- **Salvar/Carregar por código:** exporte o estado do banner como um **código base64**
  ("Copiar código") e restaure depois ("Carregar código"). O rascunho também é salvo
  automaticamente no `localStorage`.
- **Exportar PNG:** baixe o banner como imagem em escala 2x (via html2canvas), com os
  botões de remover ocultos na imagem final.
- **Donate / PIX:** barra superior com botão de doação que exibe o **Pix Copia e Cola**
  (BR Code estático, padrão EMV/BACEN) gerado 100% no cliente, com botão para copiar e
  QR Code opcional — sem backend.

## 🚀 Como rodar localmente

O projeto é um único `index.html`, então basta servi-lo por HTTP. No **Windows/PowerShell**,
com Python 3 disponível (`py`):

```powershell
# a partir da pasta pokemon-banner-tool/
py -m http.server 8000
```

Depois abra no navegador: <http://localhost:8000>

> Servir por HTTP (em vez de abrir o arquivo com `file://`) evita bloqueios de CORS na
> busca da API e na exportação da imagem.

## 📡 Origem dos dados

Os dados de cartas e coleções vêm da **API pública TCGdex** (`https://api.tcgdex.net/v2`),
que é **gratuita e não exige API key**. As URLs de imagem são montadas a partir da base
retornada pela API (`.../high.webp` e `.../low.webp`).

## 🔒 Sobre os dados do PIX

O botão "Donate / PIX" gera um BR Code estático a partir de dados **públicos** (chave Pix,
nome do recebedor e cidade). Como o arquivo é público, esses campos ficam **visíveis no
código-fonte** — o que é aceitável para uma chave Pix de doação. Por padrão, esses valores
são **placeholders** claramente identificáveis, para serem substituídos pelos dados reais.

## 🌐 Site publicado

<!-- PLACEHOLDER: link do GitHub Pages — a ser preenchido na tarefa 11.3 após publicar o site -->
🔗 _Link do GitHub Pages: (a ser adicionado após a publicação)_

## 🛠️ Detalhes técnicos

- Arquivo único (`index.html`) com HTML, CSS e JS inline; sem toolchain Node.
- Testes de propriedade em **Python + Hypothesis** (`py -m pytest`) na pasta `tests/`.
- Dependências externas apenas via CDN (html2canvas e, opcionalmente, lib de QR Code).
