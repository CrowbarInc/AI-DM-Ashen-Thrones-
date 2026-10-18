"""PR-BT selective epistemic guidance. Inspects constructed provider requests. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

from tools.measure_pr_bt_policy_instruction_payloads import PROBES, reconstruct_probe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_bt_selective_epistemic_guidance_tests"
LIVE = ROOT / "artifacts" / "pr_bt_provider_deduplication_micro_live" / "evidence"
OPTIMIZED_SYSTEM_PROMPT_CHARS = 9012
REPLACED_SENTENCE_CHARS = len(
    "If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic."
)

# Phrases the constructed system prompt must still lack. These are the verbose
# PR-BS carriers the differential told this slice not to restore.
_STILL_DELETED = (
    "provide the best grounded partial answer and state uncertainty in-character",
    "state the strongest grounded known edge plus the unknown edge",
    "anchor it to visible scene circumstances rather than generic omniscient wording",
    "Do not assert hidden causes or hidden truths as confirmed without basis in published visible/engine state",
    "omniscient conclusions are not",
    "give the strongest grounded partial answer and keep the limit diegetic",
)

_P1_GUIDANCE = {
    "visible_evidence_grounds_the_answer": "state the authorized observations first",
    "permitted_inference_is_useful": "add one possibility tied to those observations",
    "inference_stays_explicitly_qualified": "say explicitly that cause, actor, time, and history stay unresolved",
    "cause_and_history_stay_unresolved": "cause, actor, time, and history stay unresolved",
    "unsupported_history_is_not_encouraged": "Do not add a mechanism, setting, maintenance history, or causal chain",
    "uncertainty_is_not_a_refusal": "Prefer partial truth over refusal",
}

_P3_GUIDANCE = {
    "player_hypotheses_may_be_discussed": "when the player offers a hypothesis",
    "hypotheses_remain_conditional": "A player hypothesis stays hypothetical",
    "fit_is_evaluated_against_evidence": "the visible facts may be compatible with it",
    "proposal_does_not_become_truth": "observation alone does not settle it",
    "certainty_language_stays_inside_epistemic_status": "Do not use certainty wording for inferred or hypothetical material",
    "useful_discussion_is_permitted": "the visible facts may be compatible with it",
}


def _row(probe_id: str) -> dict:
    player = next(player for pid, _scene, player in PROBES if pid == probe_id)
    return reconstruct_probe(probe_id, player, out_dir=OUT)


def _constructed(probe_id: str) -> tuple[str, dict, dict]:
    _row(probe_id)
    request = json.loads(
        (OUT / "evidence" / probe_id / "provider_request_generation_1.json").read_text(encoding="utf-8")
    )
    system = ""
    payload: dict = {}
    for msg in request["provider_input"]:
        if msg.get("role") == "system":
            system = str(msg.get("content") or "")
        elif msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                payload = parsed
    return system, payload, request["measurements"]


def _live_payload(probe_id: str) -> dict:
    request = json.loads(
        (LIVE / probe_id / "provider_request_attempt_generation_1.json").read_text(encoding="utf-8")
    )
    for msg in request["provider_input"]:
        if msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                return parsed
    raise AssertionError(f"{probe_id} live user payload missing")


def _assert_prior_recipe_preserved(recipe: dict, live: dict, *changed: str) -> None:
    """PR-BV adds turn_operation and may align the named fields. Everything else stays."""
    assert set(recipe) - set(live) == {"turn_operation"}
    skipped = set(changed)
    for key, value in live.items():
        if key in skipped:
            continue
        assert recipe[key] == value, key


def _assert_deleted_prose_stays_deleted(system: str, payload: dict) -> None:
    instructions = "\n".join(str(item) for item in payload.get("instructions") or [])
    text = system + "\n" + instructions
    present = [phrase for phrase in _STILL_DELETED if phrase in text]
    assert present == []


def test_p1_provider_guidance_teaches_qualified_observation_tied_inference() -> None:
    system, payload, counts = _constructed("P1")
    missing = [name for name, phrase in _P1_GUIDANCE.items() if phrase not in system]
    assert missing == [], missing
    assert system.count("EPISTEMIC REALIZATION:") == 1
    assert "add one possibility tied to those observations" in system
    recipe = payload["decision_facing_answer_recipe"]
    assert "EPISTEMIC REALIZATION" not in json.dumps(recipe)
    assert "could, may, or might" in recipe["answer_strategy"]
    assert "Do not explain an unauthorized cause" in recipe["answer_strategy"]
    assert recipe["turn_operation"]["response_operation"] == "bounded_interpretation"
    assert counts["system_prompt_chars"] - OPTIMIZED_SYSTEM_PROMPT_CHARS == 651 - REPLACED_SENTENCE_CHARS
    _assert_deleted_prose_stays_deleted(system, payload)
    live = _live_payload("P1")
    _assert_prior_recipe_preserved(recipe, live["decision_facing_answer_recipe"], "answer_strategy")
    assert payload["gm_resolution_decision"] == live["gm_resolution_decision"]
    assert payload["response_policy"]["narrative_authority"] == live["response_policy"]["narrative_authority"]
    assert payload["response_policy"]["uncertainty"] == live["response_policy"]["uncertainty"]


def test_p3_provider_guidance_keeps_player_hypotheses_conditional() -> None:
    system, payload, _counts = _constructed("P3")
    missing = [name for name, phrase in _P3_GUIDANCE.items() if phrase not in system]
    assert missing == [], missing
    assert system.count("EPISTEMIC REALIZATION:") == 1
    assert "unless the supplied decision/claims authorize more" in system
    recipe = payload["decision_facing_answer_recipe"]
    assert recipe["answer_strategy"] == (
        "Realize the listed claims. Discuss the player's hypothesis conditionally. Do not establish it."
    )
    assert recipe["declaration_guidance"]["epistemic_premise"] == (
        "A player hypothesis on this turn may be discussed conditionally. "
        "It is not an authorized claim and it is not world truth."
    )
    assert recipe["turn_operation"]["response_operation"] == "player_hypothesis_discussion"
    assert recipe["permitted_inference"]["allowed"] is False
    assert "EPISTEMIC REALIZATION" not in json.dumps(recipe)
    _assert_deleted_prose_stays_deleted(system, payload)
    live = _live_payload("P3")
    _assert_prior_recipe_preserved(
        recipe,
        live["decision_facing_answer_recipe"],
        "answer_strategy",
        "declaration_guidance",
    )
    live_guidance = live["decision_facing_answer_recipe"]["declaration_guidance"]
    for key, value in live_guidance.items():
        if key == "epistemic_premise":
            continue
        assert recipe["declaration_guidance"][key] == value
    assert payload["gm_resolution_decision"] == live["gm_resolution_decision"]
    assert payload["response_policy"]["narrative_authority"] == live["response_policy"]["narrative_authority"]
    assert payload["response_policy"]["uncertainty"] == live["response_policy"]["uncertainty"]


def test_p2_mundane_npc_path_stays_incidental_dialogue() -> None:
    system, payload, _counts = _constructed("P2")
    assert "Mundane NPC dialogue and low-stakes texture may be bounded incidental realization" in system
    assert "EPISTEMIC REALIZATION:" not in system
    assert "NARRATION-ONLY RESPONSE CONTRACT" in system
    assert '{"narration": "player-facing response"}' in system
    assert "declared_claims" not in system
    recipe = payload["decision_facing_answer_recipe"]
    assert "ordinary dialogue" in recipe["answer_strategy"]
    assert "refusal" in recipe["answer_strategy"]
    assert "hesitation" in recipe["answer_strategy"]
    assert "ordinary NPC dialogue, refusal, hesitation, and mannerism" not in system
    incidental = recipe["incidental_improvisation_guidance"]
    assert "refusal" in incidental
    assert "hesitation" in incidental
    assert "mannerism" in incidental
    assert "phrasing" in incidental
    instructions = "\n".join(str(item) for item in payload.get("instructions") or [])
    assert "Narrate a refusal, uncertainty, or inability without inventing facts" in instructions
    assert recipe["turn_operation"]["response_operation"] == "incidental_dialogue"
    assert recipe["turn_operation"]["declaration_expectation"] == "reply_not_required"
    assert "The reply itself belongs in narration" in recipe["turn_operation"]["instruction"]
    assert "turn-local reply is narration" in recipe["declaration_guidance"]["consequential_authorized_claim"]
    assert "EPISTEMIC REALIZATION" not in json.dumps(recipe)
    _assert_deleted_prose_stays_deleted(system, payload)
    live = _live_payload("P2")
    _assert_prior_recipe_preserved(recipe, live["decision_facing_answer_recipe"], "declaration_guidance")
    live_guidance = live["decision_facing_answer_recipe"]["declaration_guidance"]
    for key, value in live_guidance.items():
        if key == "consequential_authorized_claim":
            continue
        assert recipe["declaration_guidance"][key] == value
    assert payload["gm_resolution_decision"] == live["gm_resolution_decision"]
    assert payload["response_policy"]["narrative_authority"] == live["response_policy"]["narrative_authority"]
    assert payload["response_policy"]["uncertainty"] == live["response_policy"]["uncertainty"]
