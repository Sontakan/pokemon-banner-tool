"""Pure Python reference port of the Pix (BR Code / EMV) functions from
``pokemon-banner-tool/index.html``.

These are faithful ports of the JS pure functions ``emvField``, ``crc16`` and
``buildPixPayload`` so they can be exercised by property-based tests (Hypothesis)
without Node.

Original JS (index.html):

    var PIX_CONFIG = {
        key: "SEU-EMAIL-AQUI@exemplo.com",
        merchantName: "NOME RECEBEDOR",
        merchantCity: "CIDADE",
        txid: "***"
    };

    function emvField(id, value) {
        value = value == null ? "" : String(value);
        var len = String(value.length);
        if (len.length < 2) len = "0" + len; // zero-pad para 2 dígitos
        return id + len + value;
    }

    function crc16(str) {
        var crc = 0xFFFF;
        for (var i = 0; i < str.length; i++) {
            crc ^= (str.charCodeAt(i) & 0xFF) << 8;
            for (var j = 0; j < 8; j++) {
                if (crc & 0x8000) { crc = (crc << 1) ^ 0x1021; }
                else { crc = crc << 1; }
                crc &= 0xFFFF;
            }
        }
        var hex = crc.toString(16).toUpperCase();
        while (hex.length < 4) hex = "0" + hex;
        return hex;
    }

    function buildPixPayload(config) {
        var mai = emvField("00", "br.gov.bcb.pix") + emvField("01", config.key);
        var adf = emvField("05", config.txid);
        var payload =
            emvField("00", "01") +
            emvField("26", mai) +
            emvField("52", "0000") +
            emvField("53", "986") +
            emvField("58", "BR") +
            emvField("59", config.merchantName) +
            emvField("60", config.merchantCity) +
            emvField("62", adf);
        var toCheck = payload + "6304";
        return payload + "63" + "04" + crc16(toCheck);
    }

Fidelity notes:
    - JS strings are UTF-16. ``String(value.length)`` counts UTF-16 code units,
      and ``crc16`` iterates by ``charCodeAt(i)`` (UTF-16 code unit) masking to
      the low byte (``& 0xFF``). This port mirrors that exactly by operating on
      the UTF-16 code-unit view of each string, so results match the browser
      even for non-ASCII / astral characters.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Matches the placeholder PIX_CONFIG in index.html.
PIX_CONFIG: Dict[str, str] = {
    "key": "SEU-EMAIL-AQUI@exemplo.com",
    "merchantName": "NOME RECEBEDOR",
    "merchantCity": "CIDADE",
    "txid": "***",
}


def _utf16_units(s: str) -> List[int]:
    """Return the UTF-16 code units of ``s`` as a list of ints (0..0xFFFF).

    Mirrors how JS exposes strings via ``length`` and ``charCodeAt``: each
    element is one UTF-16 code unit, so astral characters count as 2.
    """
    # Encode to UTF-16-LE (no BOM) then read 2 bytes per code unit.
    raw = s.encode("utf-16-le")
    return [raw[i] | (raw[i + 1] << 8) for i in range(0, len(raw), 2)]


def _js_string_length(s: str) -> int:
    """JS ``String#length`` — number of UTF-16 code units."""
    return len(_utf16_units(s))


def emv_field(field_id: str, value: Any) -> str:
    """Build a TLV field: id (2 chars) + length (2 chars, zero-padded) + value.

    Mirrors JS ``emvField``. The declared length is the JS string length of
    ``value`` (UTF-16 code units), zero-padded to at least 2 digits.
    """
    value = "" if value is None else str(value)
    length = str(_js_string_length(value))
    if len(length) < 2:
        length = "0" + length
    return field_id + length + value


def crc16(s: str) -> str:
    """CRC16-CCITT (poly 0x1021, init 0xFFFF) → 4 uppercase hex chars.

    Faithful port of the JS ``crc16``: iterates UTF-16 code units, masks each
    to its low byte, and folds it into the high byte of the running CRC.
    """
    crc = 0xFFFF
    for unit in _utf16_units(s):
        crc ^= (unit & 0xFF) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    hex_str = format(crc, "X")
    while len(hex_str) < 4:
        hex_str = "0" + hex_str
    return hex_str


def build_pix_payload(config: Dict[str, str]) -> str:
    """Build the static BR Code (Pix Copia e Cola) from a PixConfig.

    TLV fields in order: 00, 26(00/01), 52, 53, 58, 59, 60, 62(05), 63.
    Faithful port of JS ``buildPixPayload``.
    """
    mai = emv_field("00", "br.gov.bcb.pix") + emv_field("01", config["key"])
    adf = emv_field("05", config["txid"])

    payload = (
        emv_field("00", "01")
        + emv_field("26", mai)
        + emv_field("52", "0000")
        + emv_field("53", "986")
        + emv_field("58", "BR")
        + emv_field("59", config["merchantName"])
        + emv_field("60", config["merchantCity"])
        + emv_field("62", adf)
    )

    to_check = payload + "6304"
    return payload + "63" + "04" + crc16(to_check)
