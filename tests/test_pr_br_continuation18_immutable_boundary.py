"""PR-BR Continuation 18: preserve hard-valid responses, retry once, then stop.

The 16-turn replay uses the recorded C16 and failed-smoke candidates.
No paid model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.bounded_improvisation import (
    attach_bounded_improvisation_evaluation,
    promote_accepted_bounded_improvisation,
)
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, read_discourse_focus
from game.final_emission_gate import apply_final_emission_gate
from game.immutable_valid_response import (
    MUTATOR_MIGRATION,
    PROVENANCE_INITIAL,
    PROVENANCE_REGENERATION,
    PROVENANCE_SAFE,
    effects_allowed,
    mark_candidate_rejected,
    mutator_statuses_are_complete,
    player_utterance_in_line,
    response_is_immutable,
    run_preserve_if_valid,
    safe_nonresolution,
    same_clause_locates,
    semantic_equal,
    validate_generated_response,
)
from game.perception_grounding import apply_perception_non_invention_to_gm
from game.resolution_contract import enforce_emitted_contract_monotonicity
from game.social import apply_authored_knowledge_realization_to_gm
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
C16_PATH = ROOT / "artifacts" / "pr_br_continuation16" / "20261001T113214Z" / "turns.json"
SMOKE_PATH = ROOT / "artifacts" / "pr_br_independent_smoke" / "20261001T104551Z" / "turns.json"

# C16 turn 1 contains three straight quotation marks. Preservation-integrity
# validation now correctly treats that recorded candidate as structurally invalid.
HARD_INVALID = {("c16", 1), ("smoke", 4), ("smoke", 5), ("smoke", 7), ("smoke", 9)}
DOWNSTREAM_CREATED = {("c16", 3), ("c16", 5), ("c16", 6), ("smoke", 1), ("smoke", 3), ("smoke", 10)}
AUTHORED_BOARD = "The notice board lists taxes, curfew rules, and a warning about a missing patrol."


def _load(path: Path, source: str) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    turns = payload if isinstance(payload, list) else payload.get("turns") or []
    rows = []
    for turn in turns:
        contract = turn.get("contract") if isinstance(turn.get("contract"), dict) else {}
        if not contract.get("operation"):
            discourse = turn.get("discourse_ref") if isinstance(turn.get("discourse_ref"), dict) else {}
            target_label = turn.get("canonical_target")
            if isinstance(target_label, dict):
                target_label = target_label.get("label") or target_label.get("id")
            contract = {
                "operation": turn.get("operation"),
                "interlocutor_id": turn.get("interlocutor_id"),
                "discourse_ref": discourse,
                "target_ref": {
                    "type": str(discourse.get("type") or "interlocutor"),
                    "id_or_text": str(target_label or discourse.get("label") or ""),
                },
                "raw_input": turn.get("player_text"),
                "ambiguous": turn.get("ambiguous"),
                "expected_resolution": turn.get("expected_resolution"),
            }
        construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
        referents = [
            row for row in (construction.get("canonical_candidates") or []) if isinstance(row, dict)
        ]
        rows.append(
            {
                "source": source,
                "turn": int(turn.get("turn_number") or 0),
                "player": str(turn.get("player_text") or ""),
                "initial": str(turn.get("generated_candidate") or ""),
                "final": str(turn.get("gm_text") or ""),
                "contract": contract,
                "referents": referents,
            }
        )
    return rows


def _rows() -> list[dict]:
    return _load(C16_PATH, "c16") + _load(SMOKE_PATH, "smoke")


def _resolution(row: dict, *, mechanical_success: bool | None = None) -> dict:
    resolution = {
        "kind": "question",
        "prompt": row["player"],
        "metadata": {"resolution_contract": dict(row["contract"])},
    }
    if mechanical_success is not None:
        resolution["mechanical_success"] = mechanical_success
    return resolution


def _validate(row: dict) -> dict:
    return validate_generated_response(
        row["initial"],
        contract=row["contract"],
        player_text=row["player"],
        resolution=_resolution(row),
        referents=row["referents"],
        authored_corpus=AUTHORED_BOARD,
    )


def test_mutator_inventory_has_no_ambiguous_status():
    assert mutator_statuses_are_complete()
    assert len(MUTATOR_MIGRATION) >= 35
    assert "best_safe_tournament" in MUTATOR_MIGRATION
    assert MUTATOR_MIGRATION["best_safe_tournament"] == "RETAINED AS OBSERVABILITY"
    assert MUTATOR_MIGRATION["satisfaction_rank_chooser"] == "RETAINED AS OBSERVABILITY"
    assert MUTATOR_MIGRATION["generic_ask_completion"] == "RETAINED AS LAST-RESORT SAFE NONRESOLUTION"


def test_sixteen_turn_counterfactual_classifies_c17_boundary():
    rows = _rows()
    assert len(rows) == 16
    hard_valid = []
    hard_invalid = []
    for row in rows:
        verdict = _validate(row)
        key = (row["source"], row["turn"])
        if verdict["hard_valid"]:
            hard_valid.append(key)
        else:
            hard_invalid.append((key, verdict["reasons"]))
    assert set(hard_invalid_key for hard_invalid_key, _reasons in hard_invalid) == HARD_INVALID
    assert len(hard_valid) == 11
    preserved = 0
    for row in rows:
        key = (row["source"], row["turn"])
        if key in HARD_INVALID:
            continue

        def _fail_retry(_feedback: str) -> dict:
            raise AssertionError(f"regeneration invoked for hard-valid {key}")

        sealed = run_preserve_if_valid(
            {"player_facing_text": row["initial"], "metadata": {}, "tags": []},
            regenerate=_fail_retry,
            resolution=_resolution(row),
            player_text=row["player"],
            referents=row["referents"],
            authored_corpus=AUTHORED_BOARD,
        )
        assert sealed["player_facing_text"] == row["initial"]
        assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_INITIAL
        sealed["metadata"]["emission_debug"]["best_safe_candidate"] = "Closer looking yields nothing further."
        enforce_emitted_contract_monotonicity(sealed, _resolution(row))
        apply_authored_knowledge_realization_to_gm(
            sealed,
            player_text=row["player"],
            resolution=_resolution(row),
            session={},
            world={},
            scene={},
        )
        apply_perception_non_invention_to_gm(sealed, resolution=_resolution(row), session={}, world={}, scene={})
        apply_final_emission_gate(
            sealed,
            resolution=_resolution(row),
            session={},
            scene_id="frontier_gate",
            scene={},
            world={},
        )
        assert sealed["player_facing_text"] == row["initial"]
        assert response_is_immutable(sealed)
        preserved += 1
    assert preserved == 11
    blocked = 0
    for row in rows:
        key = (row["source"], row["turn"])
        if key not in HARD_INVALID:
            continue
        calls = {"n": 0}

        def _retry(feedback: str) -> dict:
            calls["n"] += 1
            assert "rejected for" in feedback
            assert row["initial"] not in feedback
            return {
                "player_facing_text": "The person in front of you says, \"I cannot settle that from here.\"",
                "metadata": {},
                "tags": [],
            }

        sealed = run_preserve_if_valid(
            {"player_facing_text": row["initial"], "metadata": {}, "tags": []},
            regenerate=_retry,
            resolution=_resolution(row),
            player_text=row["player"],
            referents=row["referents"],
            authored_corpus=AUTHORED_BOARD,
        )
        assert calls["n"] == 1
        assert sealed["player_facing_text"] != row["initial"]
        assert sealed["metadata"]["accepted_response"]["provenance"] in {PROVENANCE_REGENERATION, PROVENANCE_SAFE}
        blocked += 1
    assert blocked == 5


def test_seven_downstream_created_failures_stay_preserved():
    rows = [row for row in _rows() if (row["source"], row["turn"]) in DOWNSTREAM_CREATED]
    assert len(rows) == 6
    for row in rows:
        verdict = _validate(row)
        assert verdict["hard_valid"], verdict["reasons"]
        assert row["final"].strip() != row["initial"].strip()


def test_c16_turn3_locate_false_positive_is_soft_only():
    row = next(item for item in _rows() if item["source"] == "c16" and item["turn"] == 3)
    verdict = _validate(row)
    assert verdict["hard_valid"] is True
    assert "low_confidence_locate" in verdict["soft_flags"]
    assert same_clause_locates(row["initial"], ["guard captain", "Guard Captain"]) is False


def test_low_confidence_heuristic_does_not_replace_text():
    text = (
        "The guard captain replies, \"You'll find the specifics on the notice board, "
        "or by speaking to the serjeant.\""
    )
    contract = {"operation": "ask", "discourse_ref": {"label": "Guard Captain"}, "raw_input": "What does that mean?"}
    verdict = validate_generated_response(text, contract=contract, player_text=contract["raw_input"])
    assert verdict["hard_valid"] is True
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    gm = {"player_facing_text": text, "metadata": {}, "tags": []}
    sealed = run_preserve_if_valid(gm, regenerate=lambda _fb: {"player_facing_text": "replaced"}, resolution=resolution, player_text=contract["raw_input"])
    sealed["metadata"].setdefault("emission_debug", {})["best_safe_candidate"] = "Word is, captain Thoran commands the gate watch tonight."
    enforce_emitted_contract_monotonicity(sealed, resolution)
    assert sealed["player_facing_text"] == text


def test_case_a_invalid_then_valid_emits_attempt_two_unchanged():
    contract = {"operation": "ask", "contract_id": "rc_case_a", "discourse_ref": {"label": "Gate Guard"}, "raw_input": "What do I need to pass?"}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}, "mechanical_success": None}
    calls = {"n": 0}

    def _retry(feedback: str) -> dict:
        calls["n"] += 1
        assert "wrong_interlocutor" in feedback
        return {"player_facing_text": "The gate guard says, \"You wait with the line until the watch calls you.\"", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": "The tavern runner says, \"Ask someone else about the gate.\"", "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert calls["n"] == 1
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert sealed["metadata"]["accepted_response"]["attempt"] == 2
    assert "wait with the line" in sealed["player_facing_text"]


def test_case_b_double_invalid_emits_safe_nonresolution_and_stops():
    contract = {
        "operation": "ask",
        "contract_id": "rc_case_b",
        "discourse_ref": {"label": "Gate Guard"},
        "raw_input": "What do I need to show or pay to pass this gate today please?",
    }
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    calls = {"n": 0}

    def _retry(_feedback: str) -> dict:
        calls["n"] += 1
        return {"player_facing_text": "The tavern runner says, \"Still not the guard.\"", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": "The tavern runner says, \"I will answer for the guard.\"", "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert calls["n"] == 1
    assert sealed["metadata"]["generation_attempt_count"] == 2
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_SAFE
    assert player_utterance_in_line(sealed["player_facing_text"], contract["raw_input"]) is False
    assert "tavern runner" not in sealed["player_facing_text"].lower()
    line = safe_nonresolution(contract, player_text=contract["raw_input"])
    assert semantic_equal(sealed["player_facing_text"], line)


def test_case_c_valid_initial_does_not_retry():
    contract = {"operation": "ask", "discourse_ref": {"label": "Tavern Runner"}, "raw_input": "What does the stew cost?"}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    text = "The tavern runner says, \"I can't say the price tonight.\""

    def _retry(_feedback: str) -> dict:
        raise AssertionError("retry")

    sealed = run_preserve_if_valid(
        {"player_facing_text": text, "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert sealed["metadata"]["accepted_response"]["attempt"] == 1
    assert sealed["player_facing_text"] == text


def test_rejected_bounded_invention_does_not_persist_and_attempt_two_does():
    session = {"active_scene_id": "market_yard", "debug_traces": []}
    scene = {"scene": {"id": "market_yard", "visible_facts": ["A soup seller works beside the covered pump."]}}
    rejected = {
        "player_facing_text": "The soup is barley, leek, and pepper broth.",
        "improvisation_proposals": [
            {
                "kind": "incidental_fact",
                "category": "food_composition",
                "content": "The soup is barley, leek, and pepper broth.",
                "scope": "scene",
                "consequence_level": "low",
                "source": "dm_improvisation",
            }
        ],
    }
    attach_bounded_improvisation_evaluation(rejected, session=session, scene=scene, world={}, resolution=None)
    mark_candidate_rejected(rejected, rejected["player_facing_text"], ["wrong_interlocutor"])
    blocked = promote_accepted_bounded_improvisation(rejected, session=session, scene=scene, world={}, resolution=None)
    assert blocked["promoted_count"] == 0
    assert effects_allowed(rejected) is False

    accepted_text = "Rain beads on the barrel beside the pump."
    accepted = {
        "player_facing_text": accepted_text,
        "metadata": {},
        "improvisation_proposals": [
            {
                "kind": "incidental_fact",
                "category": "environmental_elaboration",
                "content": accepted_text,
                "scope": "scene",
                "consequence_level": "low",
                "source": "dm_improvisation",
            }
        ],
    }
    contract = {"operation": "inspect", "discourse_ref": {"type": "object", "label": "Notice board"}, "raw_input": "I read the board."}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    sealed = run_preserve_if_valid(
        accepted,
        regenerate=lambda _fb: None,
        resolution=resolution,
        player_text=contract["raw_input"],
        authored_corpus=AUTHORED_BOARD,
    )
    attach_bounded_improvisation_evaluation(sealed, session=session, scene=scene, world={}, resolution=resolution)
    promoted = promote_accepted_bounded_improvisation(sealed, session=session, scene=scene, world={}, resolution=resolution)
    assert promoted["promoted_count"] == 1
    contents = [str(entry.get("content") or "") for entry in session["bounded_improvisation"]["entries"]]
    assert accepted_text in contents
    assert "barley, leek, and pepper broth" not in contents


def test_rejected_npc_claim_does_not_become_active_claim():
    session = {"active_scene_id": "frontier_gate", "debug_traces": []}
    scene = {"scene": {"id": "frontier_gate", "visible_facts": [AUTHORED_BOARD]}}
    rumor = "Travelers say the northwest track is watched after dark."
    rejected = {
        "player_facing_text": f"The runner says, \"{rumor}\"",
        "improvisation_proposals": [
            {
                "kind": "npc_claim",
                "category": "rumor",
                "content": rumor,
                "scope": "scene",
                "consequence_level": "low",
                "epistemic_status": "hearsay",
                "speaker_id": "tavern_runner",
                "source": "dm_improvisation",
            }
        ],
    }
    attach_bounded_improvisation_evaluation(rejected, session=session, scene=scene, world={}, resolution=None)
    mark_candidate_rejected(rejected, rejected["player_facing_text"], ["wrong_interlocutor"])
    promote_accepted_bounded_improvisation(rejected, session=session, scene=scene, world={}, resolution=None)
    focus = read_discourse_focus(session)
    assert focus.get("active_claim") in (None, {})
    accepted_claim = "The captain says the toll is not fixed today."
    contract = {"operation": "ask", "discourse_ref": {"label": "Guard Captain"}, "raw_input": "What is the toll?"}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    sealed = run_preserve_if_valid(
        {
            "player_facing_text": f"The guard captain says, \"{accepted_claim}\"",
            "metadata": {},
            "improvisation_proposals": [
                {
                    "kind": "npc_claim",
                    "category": "rumor",
                    "content": accepted_claim,
                    "scope": "scene",
                    "consequence_level": "low",
                    "epistemic_status": "hearsay",
                    "speaker_id": "guard_captain",
                    "source": "dm_improvisation",
                }
            ],
        },
        regenerate=lambda _fb: None,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    attach_bounded_improvisation_evaluation(sealed, session=session, scene=scene, world={}, resolution=resolution)
    promote_accepted_bounded_improvisation(sealed, session=session, scene=scene, world={}, resolution=resolution)
    from game.discourse_state import note_emitted_npc_claim

    note_emitted_npc_claim(session, emitted_text=sealed["player_facing_text"], scene_id="frontier_gate")
    claim = read_discourse_focus(session).get("active_claim")
    assert isinstance(claim, dict)
    assert rumor.lower() not in str(claim).lower()


def test_mechanical_contradiction_regenerates_then_accepts_the_failure():
    contract = {"operation": "act", "raw_input": "I attack the guard."}
    resolution = {"kind": "attack", "metadata": {"resolution_contract": contract}, "mechanical_success": False}
    calls = {"n": 0}

    def _retry(feedback: str) -> dict:
        calls["n"] += 1
        assert "mechanical_contradiction" in feedback
        return {"player_facing_text": "You swing and miss. The guard is unhurt.", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": "You hit. The blow lands and the guard falls.", "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert calls["n"] == 1
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert sealed["player_facing_text"].startswith("You swing and miss")


def test_attribution_shell_regenerates_to_a_real_answer():
    contract = {"operation": "ask", "discourse_ref": {"label": "Tavern Runner"}, "raw_input": "What does the stew cost?"}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    calls = {"n": 0}

    def _retry(_feedback: str) -> dict:
        calls["n"] += 1
        return {"player_facing_text": "The tavern runner says, \"I can't give you a price tonight.\"", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": "Tavern Runner says with a tight shrug, voice low and hurried,", "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert calls["n"] == 1
    assert "can't give you a price" in sealed["player_facing_text"]
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION


def test_historical_hard_invalid_patterns_stay_blocked():
    samples = [
        ("The secret is the captain's true name.", "hidden_information"),
        ("The dead sentry says, \"Follow me.\"", "impossible_entity_state"),
        ("adding,", "malformed_or_truncated"),
        ("All non-essential traffic must clear by dusk sharp, less than three hours away.", "consequential_invention"),
    ]
    contract = {"operation": "inspect", "raw_input": "I read the notice."}
    for text, reason in samples:
        verdict = validate_generated_response(
            text,
            contract=contract,
            player_text=contract["raw_input"],
            dead_actor_labels=["dead sentry"],
            authored_corpus=AUTHORED_BOARD,
        )
        assert verdict["hard_valid"] is False
        assert reason in verdict["reasons"]


def test_safe_nonresolution_does_not_invent_or_quote():
    player = "I keep my voice down. A number, then. What are you charging for one bowl right now, and who are these right people?"
    contract = {"operation": "ask", "discourse_ref": {"label": "Tavern Runner"}, "raw_input": player}
    line = safe_nonresolution(contract, player_text=player)
    assert player_utterance_in_line(line, player) is False
    assert "thoran" not in line.lower()
    assert "mud track" not in line.lower()
    assert "closer looking yields nothing further" not in line.lower()


def test_presentation_normalization_keeps_semantic_text():
    original = "The guard captain says, \"The toll is not fixed.\""
    padded = "  The   guard captain says, \"The toll is not fixed.\"  "
    marked = "<b>The guard captain says, \"The toll is not fixed.\"</b>"
    assert semantic_equal(original, padded)
    assert semantic_equal(original, marked)


def test_raw_chat_stub_preserves_valid_and_contains_invalid(tmp_path, monkeypatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["turn_counter"] = 1
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    calls = {"n": 0}
    valid = "The tavern runner says, \"I can't say what the stew costs tonight.\""
    invalid = "The tavern runner says, \"I will answer for the guard.\""
    retry_valid = "The gate guard says, \"You need a reason the watch will accept.\""

    def fake_gpt(messages, **kwargs):
        calls["n"] += 1
        reason = str(kwargs.get("retry_reason") or "")
        if reason == "hard_invalid" or int(kwargs.get("retry_attempt") or 0) >= 1:
            return _gm_response(retry_valid)
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        if "nearest guard" in user.lower() or "pass this gate" in user.lower():
            return _gm_response(invalid)
        return _gm_response(valid)

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    first = client.post(
        "/api/chat",
        json={"text": "I catch the tavern runner's eye and ask what one bowl of stew costs tonight."},
    ).json()
    assert first.get("ok") is not False
    visible = first["gm_output"]["player_facing_text"]
    assert "can't say what the stew costs" in visible
    record = (first["gm_output"].get("metadata") or {}).get("accepted_response") or {}
    assert record.get("provenance") == PROVENANCE_INITIAL
    assert record.get("immutable") is True
    before = calls["n"]
    second = client.post(
        "/api/chat",
        json={"text": "I leave the runner and step up to the nearest guard holding the line. I ask what a traveler has to do to pass this gate."},
    ).json()
    second_text = second["gm_output"]["player_facing_text"]
    second_record = (second["gm_output"].get("metadata") or {}).get("accepted_response") or {}
    assert "I will answer for the guard" not in second_text
    assert second_record.get("provenance") in {PROVENANCE_REGENERATION, PROVENANCE_SAFE}
    assert calls["n"] - before <= 2
    assert "Closer looking yields nothing further" not in second_text
    assert "I have heard talk, but I cannot verify it" not in second_text
    focus = second.get("session", {}).get(DISCOURSE_FOCUS_KEY) if isinstance(second.get("session"), dict) else None
    if focus is None:
        saved = storage.load_session()
        focus = saved.get(DISCOURSE_FOCUS_KEY) if isinstance(saved, dict) else None
    assert isinstance(focus, dict)


@pytest.mark.parametrize("source,turn", sorted(HARD_INVALID))
def test_each_hard_invalid_initial_is_blocked(source, turn):
    row = next(item for item in _rows() if item["source"] == source and item["turn"] == turn)
    verdict = _validate(row)
    assert verdict["hard_valid"] is False
    assert verdict["reasons"]
