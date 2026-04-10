"""Direct tests for social-response-structure repair helpers (``game.final_emission_repairs``)."""
from __future__ import annotations

import pytest

from game.final_emission_repairs import (
    _collapse_multi_speaker_formatting,
    _flatten_list_like_dialogue,
    _merge_substantive_paragraphs,
    _normalize_dialogue_cadence,
    _reduce_expository_density,
    _restore_spoken_opening,
)

pytestmark = pytest.mark.unit


def test_repair_flattens_list_like_dialogue():
    raw = '- The east gate lies two hundred feet south along the market road.\n- Patrols chart that lane nightly.'
    out = _flatten_list_like_dialogue(raw)
    assert "- " not in out
    assert "east gate" in out.lower()
    assert "patrols" in out.lower()


def test_repair_collapses_multi_speaker_formatting():
    raw = (
        'Alice: "Short nod toward the east gate."\n'
        'Bob: "Patrols hold that lane until dusk, and the sergeant files tallies by lantern light."'
    )
    out = _collapse_multi_speaker_formatting(raw)
    assert "Alice:" not in out
    assert "Bob:" not in out
    assert "patrols" in out.lower()
    assert "sergeant" in out.lower()


def test_repair_merges_overlong_paragraph_dialogue():
    raw = (
        'The guard leans in. "East gate is two hundred feet south."\n\n'
        '"Patrols chart that lane until dusk," he adds.'
    )
    out = _merge_substantive_paragraphs(raw, target_max=1)
    assert "\n\n" not in out
    assert "east gate" in out.lower()


def test_repair_reduces_expository_density():
    raw = (
        "Furthermore, the watch rotates at dawn. Moreover, the east lane stays busiest after noon. "
        "Additionally, the sergeant files tallies by dusk."
    )
    out = _reduce_expository_density(raw, ["expository_monologue_density"])
    assert out != raw or "Furthermore" not in out


def test_repair_restores_spoken_opening():
    raw = "The checkpoint rumor speaks of supply movements and watch rotations without naming officers."
    out = _restore_spoken_opening(raw)
    assert out != raw
    assert out.lower().startswith(("i'll say it plain:", "here's what i can tell you:"))


def test_repair_normalizes_monoblob_cadence():
    parts = ["word"] * 60
    body = " ".join(parts)
    raw = f"Guard says {body}; the lane stays watched after curfew."
    out = _normalize_dialogue_cadence(raw)
    assert ". " in out
    assert "word" in out.lower()
