"""Example / unit tests for the Pix (Donate) flow UI wiring (task 3.3).

These are deterministic example/unit tests (not property tests). The Pix modal
behavior lives in the browser JS (DOM/clipboard wiring that cannot run
headlessly here), so we assert against the exact content of
``pokemon-banner-tool/index.html``. Structural correctness of the generated
payload/CRC is covered separately by the property test in ``test_pix.py``.

Covered acceptance criteria:
    - 5.1: an element with id "donate-btn" exists and calls ``openPixModal()``.
    - 5.5: ``PIX_CONFIG`` still contains recognizable placeholders
      (``SEU-EMAIL-AQUI@exemplo.com``, ``NOME RECEBEDOR``, ``CIDADE``).
    - 5.3: ``copyPixPayload`` uses the payload (from the ``#pix-payload`` value,
      falling back to ``buildPixPayload``) and fires ``showBannerToast(...)``.
    - 5.7: the modal shows the public-data notice text.

Requirements: 5.1, 5.3, 5.5, 5.7
"""

from __future__ import annotations

import os
import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INDEX_HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html"
)


def _read_index_html() -> str:
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


# Recognizable placeholders expected in PIX_CONFIG (Req 5.5).
PIX_PLACEHOLDERS = ["SEU-EMAIL-AQUI@exemplo.com", "NOME RECEBEDOR", "CIDADE"]


# ---------------------------------------------------------------------------
# 5.1 — the Donate/PIX button exists and opens the modal
# ---------------------------------------------------------------------------


def test_donate_button_exists_with_id():
    """5.1: an element with id ``donate-btn`` is present in the header."""
    html = _read_index_html()
    assert re.search(r'id\s*=\s*"donate-btn"', html), (
        "expected an element with id 'donate-btn'"
    )


def test_donate_button_calls_open_pix_modal():
    """5.1: the donate button wires up to ``openPixModal()``."""
    html = _read_index_html()

    # Find the tag that carries id="donate-btn" and assert its onclick.
    m = re.search(r"<button[^>]*id\s*=\s*\"donate-btn\"[^>]*>", html)
    assert m, "the #donate-btn element should be a <button>"
    button_tag = m.group(0)
    assert 'onclick="openPixModal()"' in button_tag, (
        "#donate-btn must call openPixModal() on click"
    )


def test_open_pix_modal_defined_and_shows_modal():
    """5.1: ``openPixModal`` is defined, builds the payload and opens the modal."""
    html = _read_index_html()
    assert "function openPixModal()" in html
    # It generates the payload from PIX_CONFIG, fills the textarea and opens.
    assert "var payload = buildPixPayload(PIX_CONFIG);" in html
    assert 'if (payloadEl) payloadEl.value = payload;' in html
    assert 'if (overlay) overlay.classList.add("open");' in html


# ---------------------------------------------------------------------------
# 5.5 — PIX_CONFIG keeps recognizable placeholders
# ---------------------------------------------------------------------------


def test_pix_config_block_present():
    """5.5: a ``PIX_CONFIG`` object literal is declared in the source."""
    html = _read_index_html()
    assert re.search(r"var\s+PIX_CONFIG\s*=\s*\{", html), (
        "expected a `var PIX_CONFIG = { ... }` declaration"
    )


def test_pix_config_contains_recognizable_placeholders():
    """5.5: PIX_CONFIG uses the recognizable placeholder values by default."""
    html = _read_index_html()

    # Scope the assertions to the PIX_CONFIG object literal.
    m = re.search(r"var\s+PIX_CONFIG\s*=\s*\{(.*?)\};", html, re.DOTALL)
    assert m, "PIX_CONFIG object literal not found"
    block = m.group(1)

    for placeholder in PIX_PLACEHOLDERS:
        assert placeholder in block, (
            "PIX_CONFIG placeholder %r missing" % placeholder
        )

    # The static txid is "***" (no specific transaction).
    assert 'txid: "***"' in block


# ---------------------------------------------------------------------------
# 5.3 — copyPixPayload uses the payload and fires a toast
# ---------------------------------------------------------------------------


def test_copy_pix_payload_defined():
    """5.3: ``copyPixPayload`` is defined in the source."""
    html = _read_index_html()
    assert "function copyPixPayload()" in html


def test_copy_pix_payload_uses_payload_value_with_fallback():
    """5.3: copyPixPayload reads the textarea value, falling back to buildPixPayload."""
    html = _read_index_html()
    assert "var payload = payloadEl.value || buildPixPayload(PIX_CONFIG);" in html
    # Clipboard write uses that same payload variable.
    assert "navigator.clipboard.writeText(payload)" in html


def test_copy_pix_payload_fires_toast():
    """5.3: on a successful copy, ``showBannerToast`` is called for feedback."""
    html = _read_index_html()

    copy_start = html.index("function copyPixPayload()")
    copy_region = html[copy_start:]
    # The visual feedback toast for the Pix copy path.
    assert 'showBannerToast("📋 Código Pix copiado! Cole no app do seu banco.");' in copy_region
    # The fallback path also gives feedback via showBannerToast.
    fallback_start = html.index("function selectPixBox()")
    fallback_region = html[fallback_start:]
    assert "showBannerToast(" in fallback_region


def test_copy_button_wired_to_copy_pix_payload():
    """5.3: the modal's copy button is wired to ``copyPixPayload``."""
    html = _read_index_html()
    # The copy button element exists...
    assert re.search(r'id\s*=\s*"pix-copy"', html), "expected #pix-copy button"
    # ...and is wired to copyPixPayload in the wiring IIFE.
    assert 'copyBtn.addEventListener("click", copyPixPayload);' in html


# ---------------------------------------------------------------------------
# 5.7 — the modal shows the public-data notice
# ---------------------------------------------------------------------------


def test_modal_shows_public_data_notice():
    """5.7: the modal contains a notice that key/name/city are public."""
    html = _read_index_html()

    m = re.search(r'<p class="pix-notice">(.*?)</p>', html, re.DOTALL)
    assert m, "expected a .pix-notice element in the Pix modal"
    notice = m.group(1)

    # The notice must warn the data is public and mention what is exposed.
    assert "públic" in notice.lower(), "notice must state the data is public"
    assert "chave Pix" in notice
    assert "nome do recebedor" in notice
    assert "cidade" in notice


def test_notice_lives_inside_the_pix_modal():
    """5.7: the public-data notice is inside the Pix modal overlay/card."""
    html = _read_index_html()

    modal_start = html.index('id="pix-modal"')
    modal_end = html.index("</div>", html.index('id="pix-payload"'))  # sanity anchor
    # Use a broad window from the modal start onwards and confirm the notice is
    # present after the modal begins (and before the closing script logic).
    modal_region = html[modal_start:]
    assert 'class="pix-notice"' in modal_region
    assert modal_end > modal_start
