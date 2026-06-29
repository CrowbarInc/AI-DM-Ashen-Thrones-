"""CU4 prompt/policy semantic write-site attribution locks."""
from __future__ import annotations

import pytest

import game.upstream_response_repairs as upstream_repairs
from game.final_emission_meta import SEMANTIC_MUTATION_WRITE_SITES_KEY
from game.final_emission_response_type import enforce_response_type_contract
from game.response_policy_enforcement import apply_response_policy_enforcement
from game.semantic_mutation_attribution import reconcile_semantic_mutation_owner
from game.upstream_response_repairs import build_upstream_prepared_emission_payload

pytestmark = pytest.mark.unit


def _records(mapping: dict) -> list[dict]:
    records = mapping.get(SEMANTIC_MUTATION_WRITE_SITES_KEY)
    assert isinstance(records, list)
    return records


def test_cu4_policy_rewrite_records_policy_write_site() -> None:
    out = apply_response_policy_enforcement(
        {
            "player_facing_text": "As an AI, I cannot answer that. The guard points east.",
            "tags": [],
        },
        response_policy={"diegetic_only": True, "no_validator_voice": {"enabled": True}},
        player_text="Look east.",
        scene_envelope={"scene": {"id": "gate", "visible_facts": []}},
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "Look east."},
    )

    records = _records(out["_final_emission_meta"])
    assert records[-1]["write_site_family"] == "policy"
    assert records[-1]["source"] == "diegetic_only.no_validator_voice"
    assert records[-1]["selected_active_stream"] is True
    assert records[-1]["candidate_only"] is False


def test_cu4_policy_noop_does_not_record_write_site() -> None:
    out = apply_response_policy_enforcement(
        {"player_facing_text": "The guard points east.", "tags": []},
        response_policy={"diegetic_only": True, "no_validator_voice": {"enabled": True}},
        player_text="Look east.",
        scene_envelope={"scene": {"id": "gate", "visible_facts": []}},
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "Look east."},
    )

    assert SEMANTIC_MUTATION_WRITE_SITES_KEY not in out.get("_final_emission_meta", {})


def test_cu4_prompt_semantic_transformation_records_prompt_write_site(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(upstream_repairs, "strict_social_emission_will_apply", lambda *args, **kwargs: True)
    monkeypatch.setattr(upstream_repairs, "_strict_social_answer_pressure_ac_contract_active_upstream", lambda gm: True)
    monkeypatch.setattr(upstream_repairs, "_refinement_relevant_to_answer_pressure", lambda *args, **kwargs: True)

    out = upstream_repairs.apply_spoken_state_refinement_cash_out(
        {"player_facing_text": '"I do not know more."', "response_policy": {"answer_completeness": {"enabled": True}}},
        resolution={
            "kind": "question",
            "prompt": "Who carried the seal?",
            "metadata": {"minimum_actionable_lead": {"minimum_actionable_lead_enforced": True, "enforced_lead_id": "clue-1"}},
        },
        session={"clue_knowledge": {"clue-1": {"text": "The pay chit carried a black ash-wax seal."}}},
        world={},
        scene_id="gate",
    )

    records = _records(out["_final_emission_meta"])
    assert records[-1]["write_site_family"] == "prompt"
    assert records[-1]["mutation_reason"].startswith("spoken_state_refinement_cash_out")
    assert records[-1]["selected_active_stream"] is True


def test_cu4_candidate_only_upstream_response_is_ignored_by_reconciliation() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={"kind": "question", "prompt": "Is the gate open?"},
        session={},
        world={},
        scene_id="gate",
    )

    reconciled = reconcile_semantic_mutation_owner(fem=payload)
    assert reconciled.authoritative_mutation_owner is None
    assert reconciled.authoritative_evidence_source is None
    assert all(row["candidate_only"] is True for row in _records(payload))


def test_cu4_selected_upstream_response_wins_reconciliation() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={"kind": "question", "prompt": "Is the gate open?"},
        session={},
        world={},
        scene_id="gate",
    )
    payload["prepared_answer_fallback_text"] = "Yes. The east gate is open until dusk."
    text, debug = enforce_response_type_contract(
        "Mist gathers without answering.",
        gm_output={
            "response_policy": {"response_type_contract": {"required_response_type": "answer"}},
            "upstream_prepared_emission": payload,
        },
        resolution={"kind": "question", "prompt": "Is the east gate open?"},
        session={},
        scene_id="gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == "Yes. The east gate is open until dusk."
    reconciled = reconcile_semantic_mutation_owner(fem=debug)
    assert reconciled.authoritative_mutation_owner == "game.final_emission_response_type"
    assert reconciled.authoritative_evidence_source == "write_site"


def test_cu4_mixed_pipeline_earliest_selected_write_site_is_authoritative() -> None:
    fem = {
        SEMANTIC_MUTATION_WRITE_SITES_KEY: [
            {
                "write_site_family": "prompt",
                "write_site_file": "game/upstream_response_repairs.py",
                "write_site_function": "apply_spoken_state_refinement_cash_out",
                "owner": "game.upstream_response_repairs",
                "selected_active_stream": True,
                "candidate_only": False,
            },
            {
                "write_site_family": "policy",
                "write_site_file": "game/response_policy_enforcement.py",
                "write_site_function": "_apply_diegetic_validator_voice_enforcement",
                "owner": "game.response_policy_enforcement",
                "selected_active_stream": True,
                "candidate_only": False,
            },
            {
                "write_site_family": "sanitizer",
                "write_site_file": "game/output_sanitizer.py",
                "write_site_function": "sanitize_player_facing_output",
                "owner": "game.output_sanitizer",
                "selected_active_stream": True,
                "candidate_only": False,
            },
            {
                "write_site_family": "fallback",
                "write_site_file": "game/fallback_provenance_debug.py",
                "write_site_function": "finalize_upstream_fallback_overwrite_containment",
                "owner": "game.fallback_provenance_debug",
                "selected_active_stream": True,
                "candidate_only": False,
            },
        ]
    }

    reconciled = reconcile_semantic_mutation_owner(fem=fem)
    assert reconciled.authoritative_mutation_owner == "game.upstream_response_repairs"
    assert reconciled.authoritative_mutation_family == "prompt"
