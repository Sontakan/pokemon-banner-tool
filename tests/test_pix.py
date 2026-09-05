"""Property-based tests for the Pix BR Code generator (Property 8).

Feature: pokemon-banner-tool, Property 8: BR Code estático é estruturalmente válido e o CRC confere

These tests exercise the pure Python reference port of the Pix functions
(``emv_field``, ``crc16``, ``build_pix_payload``) from ``pix_ref.py``, which
mirrors the JS logic in ``pokemon-banner-tool/index.html``.

Property 8 (design.md):
    For any valid PixConfig (key, name <= 25 chars, city <= 15 chars), the
    payload produced by ``build_pix_payload(config)``:
      - is a sequence of well-formed TLV fields, where each field's declared
        length equals the real size of its value;
      - ends with field ``63`` of length ``04`` followed by 4 hex characters;
      - has CRC16-CCITT (poly 0x1021, init 0xFFFF) recomputed over all the
        preceding content plus ``"6304"`` equal to the value in field 63.
    Additionally (known-answer, verified in the same test):
      crc16("123456789") == "29B1".

Validates: Requirements 5.6
"""

from __future__ import annotations

import re
from typing import List, Tuple

from hypothesis import given, settings
from hypothesis import strategies as st

from pix_ref import build_pix_payload, crc16, emv_field


def _utf16_units(s: str) -> int:
    """JS String#length: number of UTF-16 code units in ``s``."""
    return len(s.encode("utf-16-le")) // 2


def parse_tlv(payload: str) -> List[Tuple[str, str]]:
    """Parse a payload into a list of (id, value) TLV fields.

    Reproduces the EMV framing exactly as the JS ``emvField`` produces it:
    2-char id, 2-char decimal length (declared in UTF-16 code units, matching
    JS ``String#length``), then the value spanning that many code units.

    Raises ``ValueError`` if the framing is malformed (declared length does not
    line up with the real value size), which is what the property asserts must
    never happen for a generated payload.
    """
    units = payload.encode("utf-16-le")
    fields: List[Tuple[str, str]] = []
    pos = 0  # byte position in utf-16-le buffer
    total = len(units)

    def read(n_units: int) -> str:
        nonlocal pos
        end = pos + n_units * 2
        if end > total:
            raise ValueError("TLV truncated: not enough code units")
        chunk = units[pos:end].decode("utf-16-le")
        pos = end
        return chunk

    while pos < total:
        field_id = read(2)
        length_str = read(2)
        if not re.fullmatch(r"\d{2}", length_str):
            raise ValueError(f"TLV length not 2 digits: {length_str!r}")
        declared = int(length_str)
        value = read(declared)
        # The declared length must equal the real size of the parsed value
        # (in UTF-16 code units, the unit JS counts).
        if _utf16_units(value) != declared:
            raise ValueError(
                f"declared length {declared} != real length {_utf16_units(value)}"
            )
        fields.append((field_id, value))

    return fields


# ---------- smart generator constrained to valid PixConfig ----------

# Keep merchant name/city within the EMV-ish limits from the design
# (name <= 25 chars, city <= 15 chars). Use a broad-but-safe alphabet:
# printable text excluding control chars; single-code-unit chars keep the
# UTF-16 length equal to Python len for these fields, but the ref/parser
# handle multi-unit chars correctly regardless.
# The Pix key lives inside the Merchant Account Information template (26),
# alongside the fixed GUI "br.gov.bcb.pix". EMV declares each field's length in
# 2 decimal digits, so every field value must be <= 99 code units for the
# framing to stay well-formed. The GUI sub-field + the key wrapper consume
# 18 + 4 = 22 units, so the key must be <= 77 units (which is also the real
# Pix email-key limit). Values are single-code-unit here, so len == UTF-16 len.
_KEY_MAX = 77
_key_alphabet = st.characters(
    min_codepoint=0x20, max_codepoint=0x7E, blacklist_categories=("Cs",)
)

pix_configs = st.fixed_dictionaries(
    {
        "key": st.emails().filter(lambda s: len(s) <= _KEY_MAX)
        | st.text(alphabet=_key_alphabet, min_size=0, max_size=_KEY_MAX),
        "merchantName": st.text(
            alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x24F, blacklist_categories=("Cs",)),
            min_size=0,
            max_size=25,
        ),
        "merchantCity": st.text(
            alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x24F, blacklist_categories=("Cs",)),
            min_size=0,
            max_size=15,
        ),
        "txid": st.just("***") | st.text(alphabet="ABCDEFabcdef0123456789*", max_size=25),
    }
)


def test_crc16_known_answer():
    """Feature: pokemon-banner-tool, Property 8: BR Code estático é estruturalmente válido e o CRC confere

    Known-answer vector for CRC-16/CCITT-FALSE: crc16("123456789") == "29B1".
    """
    assert crc16("123456789") == "29B1"


@settings(max_examples=200)
@given(config=pix_configs)
def test_pix_payload_structural_and_crc(config):
    """Feature: pokemon-banner-tool, Property 8: BR Code estático é estruturalmente válido e o CRC confere

    For any valid PixConfig, the payload is well-formed TLV, ends with
    63 04 + 4 hex, and the recomputed CRC matches field 63.
    """
    payload = build_pix_payload(config)

    # 1) Ends with field 63, length 04, then exactly 4 uppercase hex chars.
    assert re.search(r"6304[0-9A-F]{4}$", payload), payload

    # 2) All TLV fields are well-formed: declared length == real value size.
    fields = parse_tlv(payload)

    # 3) The last field is the CRC field (id "63", value = 4 hex chars).
    assert fields[-1][0] == "63"
    crc_value = fields[-1][1]
    assert re.fullmatch(r"[0-9A-F]{4}", crc_value)

    # 4) Expected EMV field ids appear in order (top-level).
    top_ids = [fid for fid, _ in fields]
    assert top_ids == ["00", "26", "52", "53", "58", "59", "60", "62", "63"]

    # 5) The CRC recomputed over everything before it plus "6304" matches.
    to_check = payload[: -len("6304" + crc_value)] + "6304"
    assert crc16(to_check) == crc_value

    # 6) Merchant sub-fields carry the configured name/city and the txid.
    field_map = dict(fields)
    assert field_map["59"] == config["merchantName"]
    assert field_map["60"] == config["merchantCity"]
    # Fixed EMV constants.
    assert field_map["00"] == "01"
    assert field_map["52"] == "0000"
    assert field_map["53"] == "986"
    assert field_map["58"] == "BR"

    # 7) Merchant Account Info (26) contains the GUI and the Pix key.
    mai_fields = dict(parse_tlv(field_map["26"]))
    assert mai_fields["00"] == "br.gov.bcb.pix"
    assert mai_fields["01"] == config["key"]

    # 8) Additional Data Field (62) contains the txid under sub-field 05.
    adf_fields = dict(parse_tlv(field_map["62"]))
    assert adf_fields["05"] == config["txid"]


@settings(max_examples=100)
@given(
    field_id=st.text(alphabet="0123456789", min_size=2, max_size=2),
    value=st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x24F, blacklist_categories=("Cs",)),
        max_size=98,
    ),
)
def test_emv_field_declares_correct_length(field_id, value):
    """Feature: pokemon-banner-tool, Property 8: BR Code estático é estruturalmente válido e o CRC confere

    emv_field declares a length (>= 2 digits) equal to the value's UTF-16 length.
    """
    out = emv_field(field_id, value)
    assert out.startswith(field_id)
    length_str = out[2:4]
    assert re.fullmatch(r"\d{2}", length_str)
    assert int(length_str) == _utf16_units(value)
    # The remainder is exactly the value.
    assert out[4:] == value
