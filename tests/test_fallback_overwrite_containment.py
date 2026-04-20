"""Block I regressions: upstream fast-fallback overwrite containment from canonical provenance only."""

from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

import pytest

from game.fallback_provenance_debug import attach_upstream_fast_fallback_provenance
from game.final_emission_gate import apply_final_emission_gate
import game.final_emission_gate as feg


def _fallback_gm(selector_text: str) -> dict:
    gm = {
        "player_facing_text": selector_text,
        "tags": ["upstream_api_fast_fallback"],
        "metadata": {},
    }
    attach_upstream_fast_fallback_provenance(gm)
    return gm


def test_upstream_fast_fallback_no_overwrite_no_containment():
    text = "Fog rolls low between the river tents."
    gm = _fallback_gm(text)
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I watch the fog."},
        session={},
        scene_id="test_scene",
        world={},
    )
    prov = (out.get("metadata") or {}).get("fallback_provenance") or {}
    assert prov.get("gate_exit_vs_selector_match") is True
    assert prov.get("mismatch_detected") is False
    assert "overwrite_containment_applied" not in prov


def test_upstream_fast_fallback_pregate_overwrite_contained():
    gm = _fallback_gm("The gate stands closed against the wind.")
    gm["player_facing_text"] = "Unrelated bridge line inserted by a buggy pre-gate rewriter."
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I look at the gate."},
        session={},
        scene_id="test_scene",
        world={},
    )
    assert "gate stands closed" in (out.get("player_facing_text") or "").lower()
    prov = (out.get("metadata") or {}).get("fallback_provenance") or {}
    assert prov.get("overwrite_containment_applied") == "pre_gate"
    trace = (read_final_emission_meta_dict(out) or {}).get("fallback_provenance_trace") or {}
    assert trace.get("gate_exit_vs_selector_match") is True


def test_upstream_fast_fallback_in_finalize_overwrite_contained(monkeypatch: pytest.MonkeyPatch):
    gm = _fallback_gm("Rain drums steady on the slate roof above.")
    orig_decomp = feg._decompress_overpacked_sentences

    def _inject(t: str) -> str:
        return str(t) + " INJECT_BAD_FINALIZE_SEGMENT"

    monkeypatch.setattr(feg, "_decompress_overpacked_sentences", _inject)
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="test_scene",
        world={},
    )
    monkeypatch.setattr(feg, "_decompress_overpacked_sentences", orig_decomp)
    assert "INJECT_BAD_FINALIZE_SEGMENT" not in (out.get("player_facing_text") or "")
    assert "Rain drums" in (out.get("player_facing_text") or "")
    prov = (out.get("metadata") or {}).get("fallback_provenance") or {}
    assert prov.get("overwrite_containment_applied") == "in_gate_finalize"
    trace = (read_final_emission_meta_dict(out) or {}).get("fallback_provenance_trace") or {}
    assert trace.get("gate_exit_vs_selector_match") is True


def test_non_fallback_output_has_no_fallback_containment():
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Torchlight trembles on wet stone.",
            "tags": [],
            "metadata": {},
        },
        resolution={"kind": "observe", "prompt": "I study the walls."},
        session={},
        scene_id="test_scene",
        world={},
    )
    assert "fallback_provenance" not in (out.get("metadata") or {})
    assert (read_final_emission_meta_dict(out) or {}).get("fallback_overwrite_contained") is None


def test_upstream_fallback_finalize_strip_survives_containment_fingerprint_mismatch():
    """Selector may include appended global stock; finalize strips it even if Block I reverts to selector."""
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    gm = _fallback_gm(selector)
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="test_scene",
        world={},
    )
    pft = (out.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
