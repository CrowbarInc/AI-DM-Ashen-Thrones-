"""Part A capture. Run before the C24 production edit. Stubbed. No model calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from game.adjudication import classify_adjudication_query
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.intent_parser import segment_mixed_player_turn
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

C22 = (
    'I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. '
    '"Thank you for the warning. Have you heard anything about who or what might be causing trouble there? '
    "Any chance I could find shelter or supplies nearby before investigating further?"
)


def main() -> None:
    import tempfile
    from unittest.mock import patch

    tmp = Path(tempfile.mkdtemp(prefix="c24_before_"))
    # storage patch via the fixture's monkeypatch-like env: call the helper with a tiny shim
    class MP:
        def setattr(self, target, value):
            if target == "game.storage.DATA_DIR" or True:
                pass

    # Use pytest-free storage redirect copied from the fixture by invoking it through monkeypatch stand-in.
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    mp.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    _seed_campaign_start_storage(tmp, mp)

    def fail_interpretation(*_a, **_k):
        raise AssertionError("interpretation model invoked")

    def stub_gpt(*_a, **_k):
        return _gm_response('The tavern runner says, "The patrol went northwest of the crates."')

    mp.setattr("game.semantic_interpreter._invoke_interpretation_model", fail_interpretation)
    mp.setattr("game.api.call_gpt", stub_gpt)
    mp.setattr("game.gm.call_gpt", stub_gpt)

    segmented = segment_mixed_player_turn(C22)
    clause = segmented.get("adjudication_question_text") or C22
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene("frontier_gate")
    category = classify_adjudication_query(
        clause,
        has_active_interaction=False,
        session=session,
        world=world,
        scene=scene,
    )
    client = TestClient(app)
    first = client.post(
        "/api/chat",
        json={"text": "I ask the tavern runner what he heard about the patrol."},
    ).json()
    second = client.post("/api/chat", json={"text": C22}).json()
    resolution = second.get("resolution") if isinstance(second.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    gm = second.get("gm_output") if isinstance(second.get("gm_output"), dict) else {}
    first_res = first.get("resolution") if isinstance(first.get("resolution"), dict) else {}
    first_meta = first_res.get("metadata") if isinstance(first_res.get("metadata"), dict) else {}
    first_contract = first_meta.get("resolution_contract") if isinstance(first_meta.get("resolution_contract"), dict) else {}
    record = {
        "raw_full_utterance": C22,
        "segmentation": segmented,
        "adjudication_clause": clause,
        "classifier_on_clause": category,
        "first_turn_interlocutor": first_contract.get("interlocutor_id"),
        "first_turn_operation": first_contract.get("operation"),
        "social_context_reason": meta.get("canonical_entry_reason"),
        "route": (meta.get("intent_route_debug") or {}).get("route_reason")
        if isinstance(meta.get("intent_route_debug"), dict)
        else None,
        "kind": resolution.get("kind"),
        "contract_present": bool(contract.get("contract_id")),
        "contract_id": contract.get("contract_id"),
        "visible": gm.get("player_facing_text"),
        "tags": gm.get("tags"),
        "accepted": bool(((gm.get("metadata") or {}).get("accepted_response") or {}).get("text"))
        if isinstance(gm.get("metadata"), dict)
        else False,
        "first_contractless_decision": (
            "game.api.chat unparsed arm: parsed is None and resolve_adjudication_query"
            "(embedded adjudication clause) returns a perception_query. Emission continues"
            " without attach_interaction_obligation. contract == None is accepted there."
        ),
    }
    out = ROOT / "artifacts" / "pr_br_continuation24" / "c22_failure_replay_before.json"
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("kind", "contract_present", "classifier_on_clause", "visible", "social_context_reason", "route")}, indent=2))
    mp.undo()


if __name__ == "__main__":
    main()
