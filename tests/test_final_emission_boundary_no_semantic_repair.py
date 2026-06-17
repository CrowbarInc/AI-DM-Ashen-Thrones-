"""Block C / D: final emission must not apply SEMANTIC_DISALLOWED boundary repairs (integration)."""
from __future__ import annotations

from typing import Any

import pytest

from game.final_emission_gate import apply_final_emission_gate
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.final_emission_text import _normalize_text
from game.narrative_authenticity import build_narrative_authenticity_contract
from tests.helpers.boundary_semantic_repair_fixtures import (
    assert_fem_has_no_semantic_repair_success_flags,
    dialogue_policy_with_social_structure,
)
from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output
from tests.helpers.objective7_referent_fixtures import minimal_full_referent_artifact, referent_compact_mirror
from tests.helpers.narrative_mode_validator_fixtures import (
    build_validator_narrative_mode_contract,
    minimal_ctir_continuation,
)
from tests.helpers.repairs_consumer_facade import (
    apply_narrative_authenticity_layer,
    apply_response_delta_layer,
    apply_social_response_structure_layer,
)

pytestmark = pytest.mark.unit


def _minimal_n4_narrative_plan(*, acceptance_quality: dict[str, Any] | None = None) -> dict[str, Any]:
    nmc = build_validator_narrative_mode_contract(ctir=minimal_ctir_continuation())
    plan: dict[str, Any] = {"narrative_mode_contract": nmc}
    if acceptance_quality is not None:
        plan["acceptance_quality_contract"] = acceptance_quality
    return plan


def test_list_like_dialogue_stays_list_like(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    pol = dialogue_policy_with_social_structure()
    bullet = '- "Line one," he says.\n- "Line two follows."'
    before = _normalize_text(bullet)
    out = apply_final_emission_gate(
        {"player_facing_text": bullet, "tags": [], "response_policy": pol},
        resolution={"kind": "question", "prompt": "What did he say?"},
        session=None,
        scene_id="s1",
        world={},
    )
    txt = str(out.get("player_facing_text") or "")
    assert _normalize_text(txt) == before
    assert any(ln.lstrip().startswith("-") for ln in txt.splitlines() if ln.strip())
    fem = final_emission_meta_from_output(out)
    assert_fem_has_no_semantic_repair_success_flags(fem)
    assert fem.get("social_response_structure_repair_applied") is False
    if fem.get("social_response_structure_checked") and not fem.get("social_response_structure_passed"):
        assert fem.get("social_response_structure_boundary_semantic_repair_disabled") is True


def test_weak_response_delta_candidate_not_rewritten_at_boundary():
    """Response-delta layer is validate-only at final emission (no echo rewrite)."""
    prev = "The east gate is sealed until dawn; patrols hold the market lane overnight."
    pol = {
        "response_type_contract": {
            "required_response_type": "dialogue",
            "allowed_response_types": ["dialogue"],
            "contract_version": 1,
        },
        "response_delta": {
            "enabled": True,
            "delta_required": True,
            "allowed_delta_kinds": ["correction", "qualification"],
            "previous_answer_snippet": prev,
            "trace": {"trigger_source": "strict_social_answer_pressure"},
        },
    }
    candidate = f'Guard says "{prev}"'
    gm = {"response_policy": pol}
    text, meta, _ = apply_response_delta_layer(
        candidate,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": False},
        strict_social_path=False,
    )
    assert text == candidate
    assert meta.get("response_delta_repaired") is False
    assert meta.get("response_delta_boundary_semantic_repair_disabled") is True


def test_multi_speaker_format_not_collapsed(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    pol = dialogue_policy_with_social_structure()
    multi = 'Alice: "North road."\nBob: "South pier is faster."'
    before = _normalize_text(multi)
    out = apply_final_emission_gate(
        {"player_facing_text": multi, "tags": [], "response_policy": pol},
        resolution={"kind": "question", "prompt": "Which route?"},
        session=None,
        scene_id="s1",
        world={},
    )
    txt = str(out.get("player_facing_text") or "")
    assert _normalize_text(txt) == before
    assert "Alice:" in txt and "Bob:" in txt
    fem = final_emission_meta_from_output(out)
    assert_fem_has_no_semantic_repair_success_flags(fem)


def test_awkward_but_legal_narration_not_polished(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    awkward = "The rain; the gate; the lamps—all of it sits wrong, heavy, not quite matching how still the yard is."
    before = _normalize_text(awkward)
    out = apply_final_emission_gate(
        {"player_facing_text": awkward, "tags": []},
        resolution={"kind": "observe", "prompt": "What do I notice?"},
        session=None,
        scene_id="s1",
        world={},
    )
    assert before == _normalize_text(str(out.get("player_facing_text") or ""))
    fem = final_emission_meta_from_output(out)
    assert_fem_has_no_semantic_repair_success_flags(fem)


def test_awkward_legalistic_narration_not_semantically_rewritten(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    legalish = (
        "The party acknowledges that the aforesaid provision, being contingent upon circumstances "
        "not yet placed in the record, may not admit of further elaboration herein."
    )
    before = _normalize_text(legalish)
    out = apply_final_emission_gate(
        {"player_facing_text": legalish, "tags": []},
        resolution={"kind": "observe", "prompt": "What is the legal posture?"},
        session=None,
        scene_id="s1",
        world={},
    )
    assert _normalize_text(str(out.get("player_facing_text") or "")) == before
    fem = final_emission_meta_from_output(out)
    assert_fem_has_no_semantic_repair_success_flags(fem)


def test_n4_hard_illegal_still_sealed_fallback(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    trailer = "Nothing will ever be the same."
    out = apply_final_emission_gate(
        {"player_facing_text": trailer, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    fem = final_emission_meta_from_output(out)
    assert fem.get("acceptance_quality_gate_replaced_candidate") is True
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()
    assert_fem_has_no_semantic_repair_success_flags(fem)


def test_referent_ambiguity_not_rewritten_when_semantic_repair_disabled(monkeypatch):
    monkeypatch.setattr(
        terminal_pipeline,
        "apply_visibility_enforcement",
        lambda out, **kwargs: out,
    )
    art = minimal_full_referent_artifact(referential_ambiguity_class="none", ambiguity_risk=5)
    text = "They halt near the posted orders."
    before = _normalize_text(text)
    out = {
        "player_facing_text": text,
        "tags": [],
        "prompt_context": {"referent_tracking": art},
        "_gate_turn_packet_cache": {
            "referent_tracking_compact": referent_compact_mirror(
                referential_ambiguity_class="ambiguous_singular",
                ambiguity_risk=40,
            )
        },
    }
    terminal_pipeline._apply_referent_clarity_pre_finalize(out, pre_gate_text=text)
    assert _normalize_text(str(out.get("player_facing_text") or "")) == before
    fem = final_emission_meta_from_output(out)
    assert fem.get("referent_repair_applied") is False
    assert fem.get("referent_boundary_semantic_repair_disabled") is True
    assert_fem_has_no_semantic_repair_success_flags(fem)


def test_narrative_authenticity_failure_records_metadata_without_repair():
    na_contract = build_narrative_authenticity_contract()
    gm = {"response_policy": {"narrative_authenticity": na_contract}}
    text = "The mist holds along the quay."
    out_text, meta, _ = apply_narrative_authenticity_layer(
        text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert out_text == text
    assert meta.get("narrative_authenticity_checked") is True
    assert meta.get("narrative_authenticity_failed") is True
    assert meta.get("narrative_authenticity_repaired") is False
    assert meta.get("narrative_authenticity_repair_applied") is False
    assert meta.get("narrative_authenticity_boundary_semantic_repair_disabled") is True
    assert "low_signal_generic_reply" in (meta.get("narrative_authenticity_failure_reasons") or [])


def test_social_response_structure_failure_records_metadata_without_repair():
    pol = dialogue_policy_with_social_structure()
    bullet = (
        '- "East gate lies two hundred feet south," he mutters.\n'
        '- "Patrols chart that lane nightly."'
    )
    text, meta, _ = apply_social_response_structure_layer(
        bullet,
        gm_output={"response_policy": pol},
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": False},
        strict_social_path=False,
    )
    assert text == bullet
    assert meta.get("social_response_structure_checked") is True
    assert meta.get("social_response_structure_passed") is False
    assert meta.get("social_response_structure_repair_applied") is False
    assert meta.get("social_response_structure_boundary_semantic_repair_disabled") is True
    assert "list_like_or_bulleted_dialogue" in (meta.get("social_response_structure_failure_reasons") or [])
