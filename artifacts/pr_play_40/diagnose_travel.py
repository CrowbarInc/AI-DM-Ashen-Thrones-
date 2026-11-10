"""PR-PLAY-40 travel-failure diagnosis. No provider calls."""
from __future__ import annotations

import json
import os

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.conversational_orchestration import (
    authored_travel_admission,
    deterministic_conversational_decision,
)
from game.intent_parser import (
    _match_follow_pursuit_exit,
    looks_like_explicit_leave_or_pursuit_intent,
    looks_like_explicit_stay_intent,
    parse_freeform_to_action,
    recover_actionable_stay_leave_or_pursuit,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from tests.test_generalized_destination_exit_resolution import _seed_at_old_milestone_http
from tests.test_stay_leave_social_lock_override import (
    T7_PURSUIT,
    _engaged_session,
    _gate_scene,
    _gate_world,
    _seed_engaged_gate_http,
)

HEADING = "Okay. I'm heading out after them along that northwest track."
LEAVE = "I'm leaving. I'll head down the road after the patrol."
STAY = "I'll remain at the gate."
VEREVIN = "I'll go to House Verevin."


def _brief(data: dict) -> dict:
    res = data.get("resolution") or {}
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    decision = meta.get("conversational_decision") if isinstance(meta.get("conversational_decision"), dict) else {}
    return {
        "keys": sorted(data.keys()),
        "text": (data.get("gm_output") or {}).get("player_facing_text"),
        "kind": res.get("kind"),
        "resolved_transition": res.get("resolved_transition"),
        "target_scene_id": res.get("target_scene_id"),
        "body_scene": (data.get("session") or {}).get("active_scene_id") if isinstance(data.get("session"), dict) else None,
        "stored_scene": storage.load_session().get("active_scene_id"),
        "parser_lane": (res.get("metadata") or {}).get("parser_lane") if isinstance(res.get("metadata"), dict) else None,
        "intent": ((res.get("metadata") or {}).get("intent") if isinstance(res.get("metadata"), dict) else None),
        "decision_reason": decision.get("reason"),
        "decision_category": decision.get("category"),
        "narration_invoked": meta.get("narration_invoked"),
        "resolver_invoked": meta.get("resolver_invoked"),
        "tags": (data.get("gm_output") or {}).get("tags"),
    }


def _post(seed, text, stub):
    seed()
    with __import__("pytest").MonkeyPatch().context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(stub))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": text})
    return resp.status_code, _brief(resp.json())


def main() -> None:
    scene = _gate_scene()
    session = _engaged_session(_gate_world())
    inner = scene["scene"]
    exits = inner["exits"]
    rows = []
    for text in (HEADING, LEAVE, STAY, T7_PURSUIT, VEREVIN):
        parsed = parse_freeform_to_action(text, scene, session=session, world=_gate_world())
        recovered = recover_actionable_stay_leave_or_pursuit(
            text, scene, session=session, world=_gate_world(),
        )
        decision = deterministic_conversational_decision(
            player_text=text, scene=scene, world=_gate_world(), session=session, log=[],
        )
        rows.append({
            "text": text,
            "stay": looks_like_explicit_stay_intent(text),
            "leave": looks_like_explicit_leave_or_pursuit_intent(text),
            "pursuit_exit": _match_follow_pursuit_exit(text, exits, scene=inner, session=session),
            "admission_category": None if decision is None else decision.category.value,
            "admission_reason": None if decision is None else decision.reason,
            "admission_operation": None if decision is None else decision.proposed_operation,
            "admission_target": None if decision is None else decision.proposed_target,
            "admission_text": None if decision is None else decision.player_facing_text,
            "travel_admission": None if authored_travel_admission(
                text, scene=scene, world=_gate_world(), session=session,
            ) is None else authored_travel_admission(
                text, scene=scene, world=_gate_world(), session=session,
            ).reason,
            "parsed_type": None if parsed is None else parsed.get("type"),
            "parsed_target": None if parsed is None else parsed.get("target_scene_id"),
            "parsed_lane": None if parsed is None else (parsed.get("metadata") or {}).get("parser_lane"),
            "recovered_type": None if recovered is None else recovered.get("type"),
            "recovered_target": None if recovered is None else recovered.get("target_scene_id"),
            "recovered_lane": None if recovered is None else (recovered.get("metadata") or {}).get("parser_lane"),
        })

    import tempfile
    from pathlib import Path

    import pytest

    http = []
    http_stay_filter = {}
    cases = [
        ("pursuit", T7_PURSUIT, 'Guard Captain mutters, "Word is, the missing patrol was last seen taking the northwest mud track."', "frontier"),
        ("leave", LEAVE, "The captain keeps talking as if you had asked another question.", "frontier"),
        ("stay", STAY, "You leave the gate and enter Cinderwatch.", "frontier"),
        ("verevin_gate", VEREVIN, "You arrive at House Verevin's rooftop.", "frontier"),
        ("verevin_milestone", VEREVIN, "You leave the milestone and arrive at House Verevin.", "milestone"),
    ]
    for name, text, stub, where in cases:
        monkeypatch = pytest.MonkeyPatch()
        tmp = Path(tempfile.mkdtemp(prefix=f"play40-{name}-"))
        if where == "frontier":
            _seed_engaged_gate_http(tmp, monkeypatch)
        else:
            _seed_at_old_milestone_http(tmp, monkeypatch)
        seen = {}

        def _spy(gm_output, *, resolution=None, origin_scene_id=None):
            if name == "stay":
                meta = (resolution or {}).get("metadata") if isinstance(resolution, dict) else None
                seen["filter_kind"] = (resolution or {}).get("kind") if isinstance(resolution, dict) else None
                seen["filter_lane"] = (meta or {}).get("parser_lane") if isinstance(meta, dict) else None
                seen["filter_intent"] = (meta or {}).get("intent") if isinstance(meta, dict) else None
                seen["filter_text"] = (gm_output or {}).get("player_facing_text") if isinstance(gm_output, dict) else None
                seen["filter_origin"] = origin_scene_id
            from game.narration_state_consistency import apply_stay_leave_narration_agreement_to_gm as real
            return real(gm_output, resolution=resolution, origin_scene_id=origin_scene_id)

        with monkeypatch.context() as scoped:
            scoped.setattr("game.api.call_gpt", lambda _messages, _stub=stub: _gm_response(_stub))
            scoped.setattr("game.api.apply_stay_leave_narration_agreement_to_gm", _spy)
            client = TestClient(app)
            resp = client.post("/api/chat", json={"text": text})
        if name == "stay":
            http_stay_filter = seen
        http.append({"name": name, "status": resp.status_code, **_brief(resp.json())})
        monkeypatch.undo()
    print(json.dumps({"parser": rows, "http": http, "stay_filter": http_stay_filter}, indent=2))


if __name__ == "__main__":
    main()
