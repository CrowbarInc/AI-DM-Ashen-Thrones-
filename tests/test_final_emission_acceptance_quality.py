"""Owner tests for acceptance quality (N4) gate helper module.

Direct owner for ``game.final_emission_acceptance_quality``, including
``apply_acceptance_quality_n4_floor_seam``. Gate integration, order pins, and
full orchestration paths remain in ``tests/test_final_emission_gate.py``;
validator semantics remain in ``tests/test_acceptance_quality.py``.
"""

from __future__ import annotations

import game.final_emission_acceptance_quality as acceptance_quality_gate
import game.final_emission_terminal_pipeline as terminal_pipeline
import game.final_emission_gate as feg
from game.acceptance_quality import validate_and_repair_acceptance_quality
from game.final_emission_meta import FINAL_EMISSION_META_KEY
from game.realization_provenance import GATE_TERMINAL_REPAIR, REALIZATION_FALLBACK_FAMILY_FIELD


_N4_TRAILER_LINE = "Nothing will ever be the same."


def test_resolve_acceptance_quality_contract_disabled_without_narrative_plan() -> None:
    contract = acceptance_quality_gate._resolve_acceptance_quality_contract_for_gate({})
    assert contract.get("enabled") is False


def test_resolve_acceptance_quality_contract_default_on_with_plan_bundle() -> None:
    gm_output = {"prompt_context": {"narrative_plan": {"narrative_mode_contract": {}}}}
    contract = acceptance_quality_gate._resolve_acceptance_quality_contract_for_gate(gm_output)
    assert contract.get("enabled") is True


def test_shipped_acceptance_quality_overrides_from_plan() -> None:
    overrides = {"enabled": False, "trailer_phrase_patterns_version": "v1"}
    gm_output = {
        "prompt_context": {
            "narrative_plan": {"acceptance_quality_contract": overrides},
        },
    }
    assert acceptance_quality_gate._shipped_acceptance_quality_overrides_from_gm_output(gm_output) == overrides
    contract = acceptance_quality_gate._resolve_acceptance_quality_contract_for_gate(gm_output)
    assert contract.get("enabled") is False


def test_merge_acceptance_quality_n4_results_into_gate_fem() -> None:
    out: dict = {}
    bundle = validate_and_repair_acceptance_quality(
        "Rain falls on the stones.",
        acceptance_quality_gate._resolve_acceptance_quality_contract_for_gate(
            {"prompt_context": {"narrative_plan": {}}},
        ),
    )
    acceptance_quality_gate._merge_acceptance_quality_n4_results_into_gate_fem(out, bundle)
    fem = out[FINAL_EMISSION_META_KEY]
    assert "acceptance_quality_trace" in fem
    assert "acceptance_quality_checked" in fem


def test_bj40_apply_acceptance_quality_n4_floor_seam_replace_path_reruns_on_fallback(
    monkeypatch,
) -> None:
    plan = {"acceptance_quality_contract": {"enabled": True}}
    gm_output = {
        "player_facing_text": _N4_TRAILER_LINE,
        "tags": [],
        "prompt_context": {"narrative_plan": plan},
    }
    calls: list[str] = []

    def _spy(text: str, contract: dict) -> dict:
        calls.append(str(text or ""))
        return validate_and_repair_acceptance_quality(text, contract)

    monkeypatch.setattr(acceptance_quality_gate, "validate_and_repair_acceptance_quality", _spy)
    out = dict(gm_output)
    pre_gate_text = str(out.get("player_facing_text") or "")
    acceptance_quality_gate.apply_acceptance_quality_n4_floor_seam(
        out,
        gm_output_for_contract=gm_output,
        candidate_text=pre_gate_text,
        strict_social_path=False,
        eff_resolution={"kind": "narrate", "prompt": "I wait."},
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene=None,
        world={},
        scene_id="lane_scene",
        res_kind="narrate",
        response_type_required="",
        pre_gate_text=pre_gate_text,
    )

    assert len(calls) == 2
    assert calls[0].lower().strip() == _N4_TRAILER_LINE.lower().strip()
    assert calls[0] != calls[1]
    fem = out[FINAL_EMISSION_META_KEY]
    assert fem.get("acceptance_quality_gate_replaced_candidate") is True
    assert fem.get("final_route") == "replaced"
    assert fem.get("final_emitted_source") == "acceptance_quality_global_scene_fallback"
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) == GATE_TERMINAL_REPAIR
    tags = list(out.get("tags") or [])
    assert "final_emission_gate:acceptance_quality" in tags
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()


def test_bj74_acceptance_quality_n4_owner_entrypoint_locked() -> None:
    """BJ-74: N4 floor seam gate delegator removed; owner entrypoint only."""
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")
    assert callable(getattr(acceptance_quality_gate, "apply_acceptance_quality_n4_floor_seam", None))


def test_bj74_acceptance_quality_terminal_pipeline_calls_owner_directly() -> None:
    """BJ-74: terminal pipeline calls acceptance_quality owner directly."""
    import inspect

    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src
