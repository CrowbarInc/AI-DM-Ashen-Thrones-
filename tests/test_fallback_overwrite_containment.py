"""Block I regressions for upstream fast-fallback overwrite containment.

Ownership:
- ``game.fallback_provenance_debug`` owns canonical upstream fast-fallback provenance
  packaging (fingerprints, selector snapshots, FEM ``fallback_provenance_trace``).
- ``game.final_emission_finalize`` owns finalize packaging at the finalize boundary.
- ``game.final_emission_gate`` owns containment at gate entry and delegates finalize packaging.
- This file owns overwrite containment and gate-exit-vs-selector protection.

Failures here should point first to final-emission containment unless the
provenance/fingerprint payload itself is malformed, in which case
``game.fallback_provenance_debug`` is the likely owner. Repeated provenance
assertions are intentional incident-boundary locks, not accidental duplication.
"""

from __future__ import annotations

from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output

import pytest

from game.fallback_provenance_debug import (
    FALLBACK_PROVENANCE_SELECTOR_KEYS,
    attach_upstream_fast_fallback_provenance,
)
from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer


def _fallback_gm(selector_text: str) -> dict:
    gm = {
        "player_facing_text": selector_text,
        "tags": ["upstream_api_fast_fallback"],
        "metadata": {},
    }
    attach_upstream_fast_fallback_provenance(gm)
    return gm


def test_attach_upstream_fast_fallback_provenance_selector_shape_is_stable() -> None:
    gm = _fallback_gm("Fog rolls low between the river tents.")
    prov = (gm.get("metadata") or {}).get("fallback_provenance") or {}
    assert set(prov.keys()) >= set(FALLBACK_PROVENANCE_SELECTOR_KEYS)
    assert prov["source"] == "fallback"
    assert prov["stage"] == "fallback_selector"
    assert prov["selector_player_facing_text"] == "Fog rolls low between the river tents."
    assert isinstance(prov.get("content_fingerprint"), str) and len(prov["content_fingerprint"]) == 64


def test_upstream_fast_fallback_no_overwrite_no_containment():
    text = "Fog rolls low between the river tents."
    gm = _fallback_gm(text)
    out, _ = apply_final_emission_gate_consumer(
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
    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I look at the gate."},
        session={},
        scene_id="test_scene",
        world={},
    )
    assert "gate stands closed" in (out.get("player_facing_text") or "").lower()
    prov = (out.get("metadata") or {}).get("fallback_provenance") or {}
    assert prov.get("overwrite_containment_applied") == "pre_gate"
    trace = (final_emission_meta_from_output(out) or {}).get("fallback_provenance_trace") or {}
    assert trace.get("gate_exit_vs_selector_match") is True


def test_upstream_fast_fallback_in_finalize_overwrite_contained():
    """Finalize is packaging-only (C2); upstream fast-fallback text survives without semantic repair hooks."""
    gm = _fallback_gm("Rain drums steady on the slate roof above.")
    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="test_scene",
        world={},
    )
    assert "Rain drums" in (out.get("player_facing_text") or "")
    prov = (out.get("metadata") or {}).get("fallback_provenance") or {}
    assert prov.get("gate_exit_vs_selector_match") is True
    trace = (final_emission_meta_from_output(out) or {}).get("fallback_provenance_trace") or {}
    assert trace.get("gate_exit_vs_selector_match") is True


def test_non_fallback_output_has_no_fallback_containment():
    out, _ = apply_final_emission_gate_consumer(
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
    assert (final_emission_meta_from_output(out) or {}).get("fallback_overwrite_contained") is None


def test_upstream_fallback_finalize_strip_survives_containment_fingerprint_mismatch():
    """Selector may include appended global stock; finalize strips it even if Block I reverts to selector."""
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    gm = _fallback_gm(selector)
    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="test_scene",
        world={},
    )
    pft = (out.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
