"""Property-based tests for the banner-state persistence round-trip.

Feature: pokemon-banner-tool, Property 1: Round-trip do modelo
Validates: Requirements 4.2, 4.3, 4.4

These tests exercise the pure encode/decode logic ported in ``state_ref.py``
(the Python port of ``encodeState``/``decodeState`` from ``index.html``). The
core property is that decoding an encoded state reproduces the original state
exactly, including unicode/accented text in titles, subtitles, section names,
and card fields.
"""

from __future__ import annotations

from hypothesis import given, settings

from state_ref import (
    banner_state_strategy,
    decode_state,
    encode_state,
)


# ---------------------------------------------------------------------------
# Property 1: Round-trip do modelo (base64 + persistência)
# ---------------------------------------------------------------------------
# Feature: pokemon-banner-tool, Property 1: Round-trip do modelo
# Validates: Requirements 4.2, 4.3, 4.4
@settings(max_examples=200)
@given(state=banner_state_strategy())
def test_round_trip_preserves_state(state):
    """decode_state(encode_state(state)) == state for any valid BannerState."""
    assert decode_state(encode_state(state)) == state


# ---------------------------------------------------------------------------
# Unit tests: specific examples and edge cases that complement the property.
# ---------------------------------------------------------------------------

def test_round_trip_empty_default_like_state():
    """A minimal default-like state (empty sections) round-trips exactly."""
    state = {"title": "", "sub": "", "lang": "pt", "sections": []}
    assert decode_state(encode_state(state)) == state


def test_round_trip_preserves_unicode_and_accents():
    """Accented/unicode text in every field survives the round-trip."""
    state = {
        "title": "Megaevolução 🎴",
        "sub": "Compra ou Troca — coração ✨",
        "lang": "pt",
        "sections": [
            {
                "name": "Escuridão Absoluta",
                "cards": [
                    {
                        "id": "me01-18",
                        "name": "Pikachu ⚡ ção",
                        "image": "https://x/high.webp",
                        "set": "Megaevolução · 18",
                        "variant": "reverse",
                    }
                ],
            }
        ],
    }
    assert decode_state(encode_state(state)) == state


def test_decode_state_strips_whitespace():
    """decode_state tolerates surrounding whitespace on the code (mirrors JS trim())."""
    state = {"title": "olá", "sub": "", "lang": "en", "sections": []}
    code = encode_state(state)
    assert decode_state("  " + code + "\n") == state


def test_round_trip_all_variants():
    """Every variant value is preserved across the round-trip."""
    for variant in ("normal", "reverse", "illust", "altart", "gold", "exreg", "sar"):
        state = {
            "title": "t",
            "sub": "s",
            "lang": "ja",
            "sections": [
                {
                    "name": "sec",
                    "cards": [
                        {
                            "id": "x-1",
                            "name": "n",
                            "image": "i",
                            "set": "s",
                            "variant": variant,
                        }
                    ],
                }
            ],
        }
        assert decode_state(encode_state(state)) == state
