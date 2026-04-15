"""Downstream strict-social answer-pressure + spoken cash-out regression suite.

Locks strict-social escalation, validator-layer application, and spoken cash-out
behavior once prompt contracts are already shipped. This module consumes local
contract-shaped fixtures rather than owning prompt-contract derivation.
"""
from __future__ import annotations

import pytest

from game.final_emission_gate import (
    _apply_answer_completeness_layer,
    _apply_response_delta_layer,
    _skip_answer_completeness_layer,
    _skip_response_delta_layer,
    apply_spoken_state_refinement_cash_out,
)
from game.social import determine_social_escalation_outcome
from tests.test_social_escalation import _session_with_pressure

pytestmark = pytest.mark.unit

_STRICT_SOCIAL_ALLOWED_PARTIAL_REASONS = ("uncertainty", "lack_of_knowledge", "gated_information")


def _response_type_debug_ok() -> dict:
    return {
        "response_type_required": "dialogue",
        "response_type_contract_source": "test",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def _bridge_strict_social_details() -> dict:
    return {
        "used_internal_fallback": False,
        "final_emitted_source": "neutral_reply_speaker_grounding_bridge",
    }


def _tavern_patrol_pressure_log() -> list[dict]:
    """Manual failure transcript: patrol dodge → direct pressure → confirm probes → terminal pressure."""
    return [
        {
            "player_input": "Runner, what do you know about the missing patrol?",
            "gm_snippet": (
                'The runner keeps his voice low. "Word is thin—watch circles rumors, not names."'
            ),
        },
        {
            "player_input": "Answer directly.",
            "gm_snippet": (
                'He exhales. "I can\'t give you ink-and-seal truth; too many ears."'
            ),
        },
        {
            "player_input": "Can you confirm anything?",
            "gm_snippet": (
                "He spreads his hands. Hard to pin anything down without naming names—"
                "talk travels fast in a busy house."
            ),
        },
    ]


def _correction_reask_answer_pressure_details() -> dict:
    return {
        "same_interlocutor_followup": True,
        "prior_answer_substantive": True,
        "answer_pressure_followup_detected": True,
        "correction_reask_followup_detected": True,
        "answer_pressure_family": "correction_reask_followup",
    }


def _strict_social_answer_completeness_contract(
    *,
    answer_required: bool = True,
    strict_social_override: bool = True,
) -> dict:
    return {
        "enabled": bool(answer_required),
        "answer_required": bool(answer_required),
        "trace": {
            "strict_social_answer_seek_override": bool(strict_social_override),
        },
    }


def _strict_social_response_delta_contract(
    *,
    previous_answer_snippet: str,
    enabled: bool = True,
) -> dict:
    return {
        "enabled": bool(enabled),
        "delta_required": bool(enabled),
        "trigger_source": "strict_social_answer_pressure" if enabled else "none",
        "previous_answer_snippet": previous_answer_snippet,
        "allowed_delta_kinds": ["refinement"],
        "delta_must_come_early": False,
        "allow_short_bridge_before_delta": True,
        "forbid_semantic_restatement": bool(enabled),
        "trace": {
            "trigger_source": "strict_social_answer_pressure" if enabled else "none",
            "strict_social_answer_seek_override": bool(enabled),
            "suppressed_because": [] if enabled else ["social_lock"],
        },
    }


# --- A. Transcript regression (downstream layers + cash-out) ----------


def test_transcript_runner_correction_reask_followup_drives_downstream_escalation():
    """Correction/re-ask follow-up must stay on the existing strict-social thread."""
    correction = "What? I asked you why people here wouldn't be friendly to newcomers."
    ap = _correction_reask_answer_pressure_details()

    session = _session_with_pressure("scene_tavern", "runner_local_gossip", "tavern_runner", 1)
    soc = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_tavern",
        npc_id="tavern_runner",
        topic_key="runner_local_gossip",
        reply_kind="answer",
        progress_signals={"npc_knowledge_exhausted": False},
        player_text=correction,
        answer_pressure_details=ap,
    )
    assert soc["valid_followup_detected"] is True
    assert soc["prior_same_dimension_answer_exists"] is True
    assert soc["escalation_reason"] != "first_attempt_same_topic"
    assert soc["escalation_reason"] == "explicit_question_reassertion"

def test_transcript_missing_patrol_turn4_applies_layers_and_cashout(monkeypatch):
    log = _tavern_patrol_pressure_log()
    turn4 = "Then what can you confirm?"
    resolution = {
        "kind": "question",
        "prompt": turn4,
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
        "clue_id": "lid_patrol_milestone",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_patrol_milestone",
                "enforced_lead_source": "extracted_social",
            },
            "lead_landing": {"authoritative_promoted_ids": ["lid_patrol_milestone"]},
        },
    }
    prior = str(log[-1]["gm_snippet"] or "")
    assert len(prior) >= 12
    ac = _strict_social_answer_completeness_contract()
    rd = _strict_social_response_delta_contract(previous_answer_snippet=prior)
    # Echo prior answer to exercise RD under bridge ownership (Block 2 bypass).
    gm_line = f'Tavern Runner says, "{prior}"'
    gm = {
        "player_facing_text": gm_line,
        "tags": [],
        "response_policy": {"answer_completeness": ac, "response_delta": rd},
    }
    bridge = _bridge_strict_social_details()
    rt = _response_type_debug_ok()

    assert (
        _skip_answer_completeness_layer(
            strict_social_details=bridge,
            response_type_debug=rt,
            gm_output=gm,
        )
        is None
    )
    assert (
        _skip_response_delta_layer(
            contract=rd,
            emitted_text=gm_line,
            strict_social_details=bridge,
            response_type_debug=rt,
            answer_completeness_meta={"answer_completeness_failed": False},
            gm_output=gm,
        )
        is None
    )

    text, ac_meta, _ = _apply_answer_completeness_layer(
        gm_line,
        gm_output=gm,
        resolution=resolution,
        strict_social_details=bridge,
        response_type_debug=rt,
        strict_social_path=True,
    )
    text2, rd_meta, _ = _apply_response_delta_layer(
        text,
        gm_output=gm,
        strict_social_details=bridge,
        response_type_debug=rt,
        answer_completeness_meta=ac_meta,
        strict_social_path=True,
    )
    assert ac_meta.get("answer_completeness_skip_reason") is None
    assert ac_meta.get("answer_completeness_checked") is True
    assert rd_meta.get("response_delta_skip_reason") is None
    assert rd_meta.get("response_delta_checked") is True

    gm_layers = {**gm, "player_facing_text": text2}
    raw_before_cashout = gm_layers["player_facing_text"]

    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    session = {
        "lead_registry": {
            "lid_patrol_milestone": {
                "id": "lid_patrol_milestone",
                "title": "Re-check where the patrol crossed the old milestone marker by the east trace",
                "summary": "",
            }
        },
    }
    out = apply_spoken_state_refinement_cash_out(
        gm_layers,
        resolution=resolution,
        session=session,
        world={},
        scene_id="frontier_gate",
    )
    assert out["player_facing_text"] != raw_before_cashout
    low = out["player_facing_text"].lower()
    assert "milestone" in low
    assert '"' in out["player_facing_text"]
    cash = out.get("_spoken_refinement_cash_out") or {}
    assert cash.get("applied") is True
    assert "spoken_state_refinement_cash_out" in (out.get("debug_notes") or "")


# --- B. Cash-out branches -------------------------------------------------------


def test_cash_out_minimum_actionable_lead_enforced_appends_bounded_line(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_milestone": {
                "id": "lid_milestone",
                "title": "Investigate the old milestone",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Where was the patrol last seen?",
        "clue_id": "lid_milestone",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_milestone",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    gm = {
        "player_facing_text": "I can't name names.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    tail = out["player_facing_text"].replace(gm["player_facing_text"], "").strip()
    assert any(
        tail.startswith(p)
        for p in ("I can only add this:", "What I can say is:", "I don't know more than this:")
    )
    assert out.get("_spoken_refinement_cash_out", {}).get("source") == "extracted_social"
    assert "spoken_state_refinement_cash_out:extracted_social" in (out.get("debug_notes") or "")


def test_cash_out_authoritative_promoted_ids_without_mal(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_promo_only": {
                "id": "lid_promo_only",
                "title": "Scout the granary yard for fresh wagon ruts",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "What about wagon traffic near the granary yard?",
        "clue_id": "lid_promo_only",
        "metadata": {
            "minimum_actionable_lead": {},
            "lead_landing": {"authoritative_promoted_ids": ["lid_promo_only"]},
        },
    }
    gm = {
        "player_facing_text": "Hard to say from here.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert "granary" in out["player_facing_text"].lower()
    assert out.get("_spoken_refinement_cash_out", {}).get("source") == "authoritative_promotion"


def test_cash_out_skips_when_emitted_token_overlap_covers_refinement(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_x": {
                "id": "lid_x",
                "title": "Patrol sighting near the old milestone marker",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Where was the patrol?",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_x",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    text = "They mention the old milestone marker in passing; take that for what it is."
    gm = {"player_facing_text": text, "tags": [], "response_policy": {"answer_completeness": ac}}
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert out["player_facing_text"] == text
    assert "_spoken_refinement_cash_out" not in out


def test_cash_out_irrelevant_promoted_lead_no_append(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_xyzzy": {
                "id": "lid_xyzzy",
                "title": "Consult the zzqxym archivist beneath plugh hall",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Where was the missing patrol last routed?",
        "metadata": {
            "lead_landing": {"authoritative_promoted_ids": ["lid_xyzzy"]},
        },
    }
    gm = {
        "player_facing_text": "I cannot say more about the patrol routes.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert out["player_facing_text"] == gm["player_facing_text"]
    assert "_spoken_refinement_cash_out" not in out


def test_cash_out_discoverable_clue_requires_topic_overlap(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_gate": {
                "id": "lid_gate",
                "title": "zzqxym vault inventory under plugh seal",
                "summary": "",
            }
        }
    }
    base_mal = {
        "minimum_actionable_lead_enforced": True,
        "enforced_lead_id": "lid_gate",
        "enforced_lead_source": "discoverable_clue",
    }
    res_no_overlap = {
        "kind": "question",
        "prompt": "Tell me about the missing patrol route.",
        "metadata": {"minimum_actionable_lead": dict(base_mal)},
    }
    gm = {
        "player_facing_text": "No names, no routes.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out_skip = apply_spoken_state_refinement_cash_out(
        gm, resolution=res_no_overlap, session=session, world={}, scene_id="frontier_gate"
    )
    assert out_skip["player_facing_text"] == gm["player_facing_text"]

    res_overlap = {
        "kind": "question",
        "prompt": "Does the zzqxym vault tie to the patrol rumor?",
        "metadata": {"minimum_actionable_lead": dict(base_mal)},
    }
    out_hit = apply_spoken_state_refinement_cash_out(
        gm, resolution=res_overlap, session=session, world={}, scene_id="frontier_gate"
    )
    assert "zzqxym" in out_hit["player_facing_text"].lower()


def test_cash_out_clue_id_matches_promoted_list_without_title_overlap(monkeypatch):
    """Promotion picked via resolution clue_id still cashes out (tight id match path)."""
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    cid = "clue_patrol_echo"
    session = {
        "clue_knowledge": {
            cid: {"text": "Patrol hoofprints pressed deep near the east lane fork."},
        },
        "lead_registry": {},
    }
    resolution = {
        "kind": "question",
        "prompt": "Anything solid on the patrol?",
        "clue_id": cid,
        "metadata": {
            "lead_landing": {"authoritative_promoted_ids": [cid, "other_lead"]},
        },
    }
    gm = {
        "player_facing_text": "Talk is cheap tonight.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert "hoofprints" in out["player_facing_text"].lower() or "east" in out["player_facing_text"].lower()


# --- C. Session last_turn_response_policy probe ---------------------------------


def test_cash_out_uses_session_last_turn_response_policy_when_gm_lacks_policy(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    rd = {
        "enabled": True,
        "delta_required": True,
        "trigger_source": "strict_social_answer_pressure",
        "trace": {"trigger_source": "strict_social_answer_pressure"},
    }
    session = {
        "last_turn_response_policy": {"response_delta": rd},
        "lead_registry": {
            "lid_s": {
                "id": "lid_s",
                "title": "Follow the riverside cairn stack",
                "summary": "",
            }
        },
    }
    resolution = {
        "kind": "question",
        "prompt": "Where next?",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_s",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    gm = {"player_facing_text": "Couldn’t tell you.", "tags": []}
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert "cairn" in out["player_facing_text"].lower()
    assert out.get("_spoken_refinement_cash_out", {}).get("applied") is True


# --- D. Guardrails (do not over-fire) -------------------------------------------


def test_non_answer_seeking_social_turn_does_not_cash_out_despite_promoted_lead(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    resolution = {
        "kind": "question",
        "prompt": "I nod and let the crowd noise fill the silence.",
        "social": {"npc_id": "tavern_runner"},
        "metadata": {
            "lead_landing": {"authoritative_promoted_ids": ["lid_xyzzy"]},
        },
    }
    ac = _strict_social_answer_completeness_contract(
        answer_required=False,
        strict_social_override=False,
    )
    session = {
        "lead_registry": {
            "lid_xyzzy": {"id": "lid_xyzzy", "title": "Secret ledger under the hearth", "summary": ""}
        }
    }
    gm = {
        "player_facing_text": "The runner watches the room.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert out["player_facing_text"] == gm["player_facing_text"]
    assert "_spoken_refinement_cash_out" not in out


def test_answer_pressure_without_promoted_or_enforced_leaves_text_unchanged(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    resolution = {
        "kind": "question",
        "prompt": "Then what can you confirm?",
        "metadata": {"minimum_actionable_lead": {}, "lead_landing": {}},
    }
    text = "Hard to pin anything down."
    gm = {"player_facing_text": text, "tags": [], "response_policy": {"answer_completeness": ac}}
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session={}, world={}, scene_id="frontier_gate"
    )
    assert out["player_facing_text"] == text
    assert "_spoken_refinement_cash_out" not in out


def test_non_social_scene_skips_cash_out(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: False,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    resolution = {
        "kind": "question",
        "prompt": "Then what?",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_x",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    gm = {
        "player_facing_text": "Fog on the moor.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm,
        resolution=resolution,
        session={"lead_registry": {"lid_x": {"id": "lid_x", "title": "North cairn line", "summary": ""}}},
        world={},
        scene_id="wild_moors",
    )
    assert out == gm


# --- E. Block 2 preservation + AC/RD when cash-out not needed --------------------


def test_block2_ac_and_rd_skip_bypass_together_under_bridge_answer_pressure():
    """Narrow lock: both layers honor answer-pressure bypass for bridge ownership."""
    ac = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "expected_voice": "npc",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(_STRICT_SOCIAL_ALLOWED_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "fact"],
        "trace": {"strict_social_answer_seek_override": True},
    }
    rd = {
        "enabled": True,
        "delta_required": True,
        "trigger_source": "strict_social_answer_pressure",
        "trace": {"trigger_source": "strict_social_answer_pressure"},
        "previous_answer_snippet": "East road past the mill toward the bonded warehouse district.",
        "allowed_delta_kinds": ["refinement"],
    }
    gm = {
        "player_facing_text": "Line.",
        "tags": [],
        "response_policy": {"answer_completeness": ac, "response_delta": rd},
    }
    bridge = {
        "used_internal_fallback": False,
        "final_emitted_source": "structured_fact_candidate_emission",
    }
    rt = _response_type_debug_ok()
    assert _skip_answer_completeness_layer(strict_social_details=bridge, response_type_debug=rt, gm_output=gm) is None
    assert (
        _skip_response_delta_layer(
            contract=rd,
            emitted_text=gm["player_facing_text"],
            strict_social_details=bridge,
            response_type_debug=rt,
            answer_completeness_meta={"answer_completeness_failed": False},
            gm_output=gm,
        )
        is None
    )


def test_ac_rd_layers_pass_clean_when_cash_out_skipped(monkeypatch):
    """Validators still run; no repair trail when emitted already satisfies contracts."""
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_x": {
                "id": "lid_x",
                "title": "Patrol sighting near the old milestone marker",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Where was the patrol?",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_x",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    text = "Tavern Runner says, \"They were last seen near the old milestone marker.\""
    gm = {"player_facing_text": text, "tags": [], "response_policy": {"answer_completeness": ac}}
    out = apply_spoken_state_refinement_cash_out(
        gm, resolution=resolution, session=session, world={}, scene_id="frontier_gate"
    )
    assert out["player_facing_text"] == text
    assert "_spoken_refinement_cash_out" not in out

    rd = {
        "enabled": True,
        "delta_required": True,
        "trigger_source": "strict_social_answer_pressure",
        "trace": {"trigger_source": "strict_social_answer_pressure"},
        "previous_answer_snippet": "They were last seen near the old mill road fork.",
        "allowed_delta_kinds": ["refinement", "new_information"],
        "delta_must_come_early": False,
        "allow_short_bridge_before_delta": True,
    }
    gm2 = {**gm, "response_policy": {**gm["response_policy"], "response_delta": rd}}
    rt = _response_type_debug_ok()
    _, ac_meta, ac_extra = _apply_answer_completeness_layer(
        text,
        gm_output=gm2,
        resolution=resolution,
        strict_social_details=_bridge_strict_social_details(),
        response_type_debug=rt,
        strict_social_path=True,
    )
    _, rd_meta, rd_extra = _apply_response_delta_layer(
        text,
        gm_output=gm2,
        strict_social_details=_bridge_strict_social_details(),
        response_type_debug=rt,
        answer_completeness_meta=ac_meta,
        strict_social_path=True,
    )
    assert ac_meta.get("answer_completeness_failed") is not True
    assert ac_meta.get("answer_completeness_repaired") is not True
    assert ac_extra == []
    assert rd_meta.get("response_delta_failed") is not True
    assert rd_meta.get("response_delta_repaired") is not True
    assert rd_extra == []
