"""PR-BR Slice 3: structured claims through the raw /api/chat path.

Deterministic. The OpenAI transport is stubbed. call_gpt, the resolution
contract, the GM resolution decision, declaration validation, narration
validation, the C18 seal, and temporal commit all run.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import openai
from fastapi.testclient import TestClient

import game.api as api_mod
import game.gm as gm_mod
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.gm import _safe_json
from game.gm_resolution_decision import (
    AUTH_INFERENCE,
    AUTH_WORLD,
    DECISION_METADATA_KEY,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_PLAYER_HYPOTHESIS,
    REL_CAUSAL,
    REL_OBSERVATION,
    ROLE_MAY_INFER,
    ROLE_MUST_STATE,
    STATUS_ESTABLISHED,
    STATUS_HYPOTHESIS,
    STATUS_POSSIBLE,
    TEMPORAL_PROVENANCE_KEY,
    TEMPORAL_PROVENANCE_VERSION,
)
from game.immutable_valid_response import PROVENANCE_INITIAL, PROVENANCE_REGENERATION, PROVENANCE_SAFE
from game import storage
from tests.helpers.live_model_guard import production_call_gpt
from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage

PLAIN_PROSE = "The cracked beam probably failed in the storm."
TURN3_NARRATION = (
    "I can't swear to it, but from what I saw, sudden, violent pressure "
    "seems a likely cause of the bowed handle and sheared pin."
)
INFERENCE_NARRATION = "Excessive strain is one possibility."
NPC_NARRATION = "The porter folds the cloth lengthwise and says he prefers lavender soap."


def _decl(text: str, *, mode: str = "realize", relation: str = REL_OBSERVATION, **extra) -> dict:
    return {
        "declaration_id": extra.pop("declaration_id", "d_" + str(abs(hash(text)))[:8]),
        "declaration_mode": mode,
        "source_claim_id": extra.pop("source_claim_id", ""),
        "semantic_identity": extra.pop("semantic_identity", {}),
        "provenance_requested": extra.pop("provenance_requested", "authored_world_fact"),
        "epistemic_status": extra.pop("epistemic_status", STATUS_ESTABLISHED),
        "modality": extra.pop("modality", STATUS_ESTABLISHED),
        "realization_role": extra.pop("realization_role", ROLE_MUST_STATE),
        "relation_kind": relation,
        "text": text,
        **extra,
    }


def _seed(tmp_path, monkeypatch, *, facts: list[str], session_extra: dict | None = None) -> None:
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-live")
    _seed_campaign_start_storage(
        tmp_path,
        monkeypatch,
        frontier_gate_overrides={"visible_facts": list(facts), "summary": "A worked gate."},
    )
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["turn_counter"] = 1
    if session_extra:
        session.update(session_extra)
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())


def _install_transport(monkeypatch, script):
    monkeypatch.setattr(api_mod, "call_gpt", production_call_gpt())
    monkeypatch.setattr(gm_mod, "call_gpt", production_call_gpt())
    calls: list[dict] = []

    class _Client:
        def __init__(self, *_args, **_kwargs) -> None:
            self.responses = self

        def create(self, **kwargs):
            messages = kwargs.get("input") or []
            blob = json.dumps(messages, default=str)
            retry = "previous attempt was rejected" in blob.lower()
            raw = script(retry=retry, call_index=len(calls), blob=blob)
            text = raw if isinstance(raw, str) else json.dumps(raw)
            calls.append({"raw": text, "retry": retry, "feedback": blob})
            return SimpleNamespace(output_text=text)

    monkeypatch.setattr(openai, "OpenAI", _Client)
    return calls


def _post(client: TestClient, text: str) -> dict:
    payload = client.post("/api/chat", json={"text": text}).json()
    assert isinstance(payload, dict)
    assert isinstance(payload.get("gm_output"), dict), payload.get("error")
    return payload


def _exact(payload: dict, calls: list[dict]) -> dict:
    gm = payload["gm_output"]
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    record = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    hard = record.get("hard_validation") if isinstance(record.get("hard_validation"), dict) else {}
    audit = hard.get("gm_resolution_decision_audit") if isinstance(hard.get("gm_resolution_decision_audit"), dict) else {}
    accepted = str(record.get("text") or "")
    emitted = str(gm.get("player_facing_text") or "")
    assert accepted == emitted
    assert "declared_claims" not in emitted
    assert not emitted.strip().startswith("{")
    return {
        "initial_raw": calls[0]["raw"] if calls else "",
        "retry_raw": next((row["raw"] for row in calls if row["retry"]), ""),
        "parsed_envelope": meta.get("realization_envelope"),
        "declaration_audit": audit.get("declaration_validation"),
        "narration_audit": audit.get("narration_validation"),
        "attempt_1": review.get("attempt_1"),
        "attempt_2": review.get("attempt_2"),
        "accepted": accepted,
        "sealed": accepted,
        "emitted": emitted,
        "provenance": record.get("provenance"),
    }


def _decision(payload: dict) -> dict:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    decision = meta.get(DECISION_METADATA_KEY)
    return decision if isinstance(decision, dict) else {}


def test_call_gpt_rejects_plain_prose_before_it_can_be_narration(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-live")
    monkeypatch.setattr(gm_mod, "call_gpt", production_call_gpt())

    class _Client:
        def __init__(self, *_args, **_kwargs) -> None:
            self.responses = self

        def create(self, **_kwargs):
            return SimpleNamespace(output_text=PLAIN_PROSE)

    monkeypatch.setattr(openai, "OpenAI", _Client)
    out = gm_mod.call_gpt([{"role": "user", "content": "Inspect the beam."}])
    assert out["player_facing_text"] == ""
    assert PLAIN_PROSE not in out["player_facing_text"]
    assert out["metadata"]["structured_contract_failure"] is True
    assert out["metadata"]["output_form"] == "plain"
    assert out["metadata"]["legacy_fallback"] is False


def test_raw_chat_accepts_authorized_fact_and_seals_it(tmp_path, monkeypatch) -> None:
    fact = "The beam is cracked."
    _seed(tmp_path, monkeypatch, facts=[fact])
    calls = _install_transport(
        monkeypatch,
        lambda **_kwargs: {"declared_claims": [_decl(fact)], "narration": fact},
    )
    payload = _post(TestClient(app), "I inspect the beam.")
    exact = _exact(payload, calls)
    assert exact["emitted"] == fact
    assert exact["provenance"] == PROVENANCE_INITIAL
    assert exact["accepted"] == exact["sealed"] == exact["emitted"]
    assert calls[0]["retry"] is False
    decision = _decision(payload)
    assert decision.get("realization_claims")


def test_raw_chat_rejects_unauthorized_cause_and_emits_only_the_retry(tmp_path, monkeypatch) -> None:
    fact = "The beam is cracked."
    stolen = "The storm caused the crack."
    _seed(tmp_path, monkeypatch, facts=[fact])

    def script(*, retry, **_kwargs):
        if not retry:
            return {
                "declared_claims": [
                    _decl(fact),
                    _decl(stolen, mode="propose", relation=REL_CAUSAL, modality=STATUS_ESTABLISHED),
                ],
                "narration": "The beam is cracked from last night's storm.",
            }
        return {"declared_claims": [_decl(fact)], "narration": fact}

    calls = _install_transport(monkeypatch, script)
    payload = _post(TestClient(app), "I inspect the beam.")
    exact = _exact(payload, calls)
    assert "last night's storm" not in exact["emitted"]
    assert exact["emitted"] == fact
    assert exact["provenance"] == PROVENANCE_REGENERATION
    assert any(row["retry"] for row in calls)
    feedback = next(row["feedback"] for row in calls if row["retry"])
    assert "structured_envelope_schema" in feedback
    assert "accepted_realization_claims" in feedback
    assert "rejected_declarations" in feedback
    assert "gm_resolution_decision" in feedback


def test_raw_chat_rejects_undeclared_cause(tmp_path, monkeypatch) -> None:
    fact = "The beam is cracked."
    _seed(tmp_path, monkeypatch, facts=[fact])

    def script(*, retry, **_kwargs):
        if not retry:
            return {
                "declared_claims": [_decl(fact)],
                "narration": "The storm cracked the beam.",
            }
        return {"declared_claims": [_decl(fact)], "narration": fact}

    calls = _install_transport(monkeypatch, script)
    payload = _post(TestClient(app), "I inspect the beam.")
    exact = _exact(payload, calls)
    assert "storm" not in exact["emitted"].lower()
    assert exact["emitted"] == fact
    assert exact["provenance"] == PROVENANCE_REGENERATION
    assert len(calls) >= 2


def test_raw_chat_plain_prose_is_a_structured_contract_failure(tmp_path, monkeypatch) -> None:
    fact = "The beam is cracked."
    _seed(tmp_path, monkeypatch, facts=[fact])

    def script(*, retry, **_kwargs):
        if not retry:
            return PLAIN_PROSE
        return {"declared_claims": [_decl(fact)], "narration": fact}

    calls = _install_transport(monkeypatch, script)
    payload = _post(TestClient(app), "I inspect the beam.")
    exact = _exact(payload, calls)
    assert PLAIN_PROSE not in exact["emitted"]
    assert exact["emitted"] == fact
    assert exact["provenance"] == PROVENANCE_REGENERATION
    feedback = next(row["feedback"] for row in calls if row["retry"])
    assert "structured_contract_failure" in feedback
    assert "declared_claims" in feedback
    parsed = _safe_json(calls[0]["raw"], require_structured_claims=True)
    assert parsed["player_facing_text"] == ""
    assert parsed["metadata"]["legacy_fallback"] is False


def test_raw_chat_plain_prose_exhausted_uses_safe_fallback_not_model_prose(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch, facts=["The beam is cracked."])
    calls = _install_transport(monkeypatch, lambda **_kwargs: PLAIN_PROSE)
    payload = _post(TestClient(app), "I inspect the beam.")
    exact = _exact(payload, calls)
    assert PLAIN_PROSE not in exact["emitted"]
    assert "declared_claims" not in exact["emitted"]
    assert exact["provenance"] == PROVENANCE_SAFE
    assert len(calls) <= 3


def test_saved_turn3_cause_is_not_emitted_or_promoted(tmp_path, monkeypatch) -> None:
    facts = ["The pump handle is bowed.", "The pin is sheared."]
    _seed(
        tmp_path,
        monkeypatch,
        facts=facts,
        session_extra={
            TEMPORAL_PROVENANCE_KEY: {
                "version": TEMPORAL_PROVENANCE_VERSION,
                "gm_inferences": [],
                "player_hypotheses": [
                    {
                        "text": "Sudden, violent pressure caused the bowed handle and sheared pin.",
                        "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
                        "authority": "observation",
                        "epistemic_status": STATUS_HYPOTHESIS,
                        "semantic_identity": {
                            "subject": "sudden pressure",
                            "relation": "possible_cause",
                            "value": "bowed handle",
                            "epistemic_status": STATUS_HYPOTHESIS,
                            "modality": "hypothetical",
                        },
                    }
                ],
                "accepted_incidentals": [],
                "rejected_consequential": [],
            }
        },
    )

    def script(*, retry, **_kwargs):
        if not retry:
            return {
                "declared_claims": [
                    _decl(facts[0]),
                    _decl(facts[1]),
                    _decl(
                        "Sudden, violent pressure is a likely cause of the bowed handle and sheared pin.",
                        mode="propose",
                        relation=REL_CAUSAL,
                        provenance_requested=PROVENANCE_GM_INFERENCE,
                        epistemic_status="likely",
                        modality="likely",
                        realization_role=ROLE_MAY_INFER,
                        semantic_identity={
                            "subject": "sudden pressure",
                            "relation": "cause",
                            "value": "bowed handle",
                        },
                    ),
                ],
                "narration": TURN3_NARRATION,
            }
        return {
            "declared_claims": [_decl(facts[0]), _decl(facts[1])],
            "narration": "The pump handle is bowed. The pin is sheared.",
        }

    calls = _install_transport(monkeypatch, script)
    payload = _post(TestClient(app), "I inspect the pump handle.")
    exact = _exact(payload, calls)
    assert TURN3_NARRATION not in exact["emitted"]
    assert "likely cause" not in exact["emitted"].lower()
    assert "bowed" in exact["emitted"].lower()
    saved = storage.load_session()
    temporal = saved.get(TEMPORAL_PROVENANCE_KEY) if isinstance(saved, dict) else {}
    inferences = temporal.get("gm_inferences") if isinstance(temporal, dict) else []
    assert not any("sudden" in str(row.get("text") or "").lower() for row in inferences if isinstance(row, dict))
    scene = storage.load_scene("frontier_gate")
    visible = " ".join(str(item) for item in (scene.get("scene") or {}).get("visible_facts") or [])
    assert "sudden" not in visible.lower()
    assert any(row["retry"] for row in calls)


def test_authorized_inference_persists_without_promotion(tmp_path, monkeypatch) -> None:
    fact = "The cart axle is cracked."
    claim = _decl(
        "Excessive strain is a possible cause.",
        mode="propose",
        relation=REL_CAUSAL,
        provenance_requested=PROVENANCE_GM_INFERENCE,
        epistemic_status=STATUS_POSSIBLE,
        modality=STATUS_POSSIBLE,
        realization_role=ROLE_MAY_INFER,
        semantic_identity={"subject": "excessive strain", "relation": "possible_cause", "value": "cracked axle"},
    )
    _seed(tmp_path, monkeypatch, facts=[fact])
    calls = _install_transport(
        monkeypatch,
        lambda **_kwargs: {"declared_claims": [claim], "narration": INFERENCE_NARRATION},
    )
    client = TestClient(app)
    first = _post(client, "I inspect the cracked axle. What does the damage suggest?")
    exact = _exact(first, calls)
    assert exact["emitted"] == INFERENCE_NARRATION
    assert exact["provenance"] == PROVENANCE_INITIAL
    saved = storage.load_session()
    temporal = saved.get(TEMPORAL_PROVENANCE_KEY) if isinstance(saved, dict) else {}
    inferences = [row for row in (temporal.get("gm_inferences") or []) if isinstance(row, dict)]
    assert any("excessive strain" in str(row.get("text") or "").lower() for row in inferences)
    assert all(row.get("authority") != AUTH_WORLD for row in inferences)
    assert all(row.get("provenance") == PROVENANCE_GM_INFERENCE for row in inferences)

    before = len(calls)
    second = _post(client, "I inspect the cracked axle again. What does the damage suggest?")
    exact_2 = _exact(second, calls[before:])
    assert "possibility" in exact_2["emitted"].lower()
    assert "established" not in exact_2["emitted"].lower()
    decision = _decision(second)
    realized = [
        row
        for row in (decision.get("realization_claims") or [])
        if isinstance(row, dict) and row.get("provenance") == PROVENANCE_GM_INFERENCE
    ]
    assert realized
    assert all(row.get("authority") == AUTH_INFERENCE for row in realized)
    scene = storage.load_scene("frontier_gate")
    visible = " ".join(str(item) for item in (scene.get("scene") or {}).get("visible_facts") or [])
    assert "excessive strain" not in visible.lower()


def test_mundane_npc_improvisation_persists_without_world_truth(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch, facts=["A porter waits beside the gate."])
    proposal = {
        "kind": "incidental_fact",
        "category": "mannerism",
        "content": "He prefers lavender soap.",
        "scope": "scene",
        "consequence_level": "incidental",
        "source": "dm_improvisation",
    }

    def script(*, retry, **_kwargs):
        if retry:
            return {"declared_claims": [], "narration": "He still prefers lavender soap."}
        return {
            "declared_claims": [],
            "narration": NPC_NARRATION,
            "improvisation_proposals": [proposal],
        }

    calls = _install_transport(monkeypatch, script)
    client = TestClient(app)
    first = _post(client, "I watch the porter for a moment.")
    exact = _exact(first, calls)
    assert "lavender soap" in exact["emitted"].lower()
    assert exact["provenance"] == PROVENANCE_INITIAL
    saved = storage.load_session()
    entries = ((saved.get("bounded_improvisation") or {}).get("entries") or []) if isinstance(saved, dict) else []
    assert any("lavender soap" in str(row.get("content") or "").lower() for row in entries if isinstance(row, dict))
    scene = storage.load_scene("frontier_gate")
    visible = " ".join(str(item) for item in (scene.get("scene") or {}).get("visible_facts") or [])
    assert "lavender" not in visible.lower()

    before = len(calls)
    second = _post(client, "I mention the soap he preferred.")
    exact_2 = _exact(second, calls[before:])
    assert "lavender" in exact_2["emitted"].lower() or "soap" in exact_2["emitted"].lower()
    saved_2 = storage.load_session()
    entries_2 = ((saved_2.get("bounded_improvisation") or {}).get("entries") or []) if isinstance(saved_2, dict) else []
    assert any("lavender soap" in str(row.get("content") or "").lower() for row in entries_2 if isinstance(row, dict))


def test_social_and_movement_model_paths_reject_plain_prose(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch, facts=["The gate is shut.", "The road runs east."])
    client = TestClient(app)
    cases = [
        ("I ask the gate guard who keeps the watch.", "The gate guard says, \"I cannot name the watch from here.\""),
        ("I walk toward the notice board.", "You stay where you are. The notice board is still ahead."),
    ]

    def _run(player: str, narration: str) -> dict:
        def script(*, retry, **_kwargs):
            if not retry:
                return PLAIN_PROSE
            return {"declared_claims": [], "narration": narration}

        calls = _install_transport(monkeypatch, script)
        payload = _post(client, player)
        exact = _exact(payload, calls)
        assert PLAIN_PROSE not in exact["emitted"]
        assert calls, player
        return exact

    social = _run(cases[0][0], cases[0][1])
    movement = _run(cases[1][0], cases[1][1])
    assert social["emitted"]
    assert movement["emitted"]
    assert "declared_claims" not in social["emitted"]
    assert "declared_claims" not in movement["emitted"]


def test_malformed_envelopes_do_not_leak_and_fall_back(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, monkeypatch, facts=["The beam is cracked."])
    client = TestClient(app)
    samples = {
        "malformed_json": '{"declared_claims": [',
        "missing_narration": {"declared_claims": [], "tags": ["x"]},
        "missing_claims": {"narration": "The gate is closed.", "tags": ["x"]},
        "prose_wrap": 'Here is the answer {"declared_claims": [], "narration": "The gate is closed."}',
        "duplicate": '{"declared_claims": [], "narration": "One."}{"declared_claims": [], "narration": "Two."}',
        "wrong_type": {
            "declared_claims": [{"text": 12, "declaration_mode": "world_truth"}],
            "narration": "The storm caused the crack.",
        },
    }
    for name, raw in samples.items():
        calls = _install_transport(monkeypatch, lambda retry, raw=raw, **_kwargs: raw)
        payload = _post(client, f"I inspect the beam. ({name})")
        exact = _exact(payload, calls)
        emitted = exact["emitted"]
        assert "declared_claims" not in emitted, name
        assert "player_facing_text" not in emitted, name
        assert "world_truth" not in emitted, name
        assert "The storm caused the crack." not in emitted, name
        assert "{" not in emitted, name
        assert len(calls) >= 1, name
        assert len(calls) <= 4, name
