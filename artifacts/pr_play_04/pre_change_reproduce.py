"""Pre-change PR-PLAY-04 reproduction. Synthetic SDK only; no network."""
from pathlib import Path
import os, sys, json, socket, copy, uuid, shutil
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
os.environ["ASHEN_DATA_DIR"] = str(ROOT / "development/tmp/pr_play_04/import_data")
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(ROOT / f"development/tmp/pr_play_04/mock_usage_{uuid.uuid4().hex}.jsonl")
for key in (
    "ASHEN_PROVIDER_REQUEST_LIMIT",
    "ASHEN_PROVIDER_INPUT_TOKEN_LIMIT",
    "ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT",
    "ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT",
):
    os.environ.pop(key, None)

CASES = sys.argv[1:] or ["valid_structured", "missing_envelope", "pipeline_exception"]


def denied(*_a, **_k):
    raise AssertionError("Network forbidden in offline reproduction")


with patch.object(socket.socket, "connect", denied), patch.object(socket, "getaddrinfo", denied):
    import pytest
    from starlette.requests import Request
    import game.api as api
    import game.gm as gm
    import game.storage as st
    from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage

    outdir = ROOT / "artifacts/pr_play_04/post_change"
    outdir.mkdir(parents=True, exist_ok=True)
    captures = []
    current = {}

    def create(**kwargs):
        captures.append({"case": current["case"], "kwargs_keys": sorted(kwargs)})
        if current["case"] == "provider_exception":
            raise RuntimeError("synthetic SDK operation failure")
        return SimpleNamespace(
            output_text=current["text"],
            model="offline-stub",
            id="synthetic-response",
            usage=SimpleNamespace(input_tokens=100, output_tokens=40, total_tokens=140),
            status="completed",
        )

    def ctor(**kwargs):
        assert kwargs.get("max_retries") == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))

    def req():
        return Request({
            "type": "http",
            "method": "POST",
            "path": "/api/start_campaign",
            "headers": [],
            "query_string": b"ui_mode=player",
        })

    def decode(response):
        return json.loads(response.body) if hasattr(response, "body") else response

    def faction_rows(world):
        rows = []
        for faction in (world or {}).get("factions") or []:
            if isinstance(faction, dict):
                rows.append({
                    "id": faction.get("id"),
                    "pressure": faction.get("pressure"),
                    "agenda_progress": faction.get("agenda_progress"),
                })
        return rows

    def snap():
        session = st.load_session()
        world = st.load_world()
        return {
            "campaign_started": session.get("campaign_started"),
            "turn_counter": session.get("turn_counter"),
            "clocks": session.get("clocks"),
            "active_scene_id": session.get("active_scene_id"),
            "log_length": len(st.load_log()),
            "campaign_can_start": api._session_allows_structured_start_campaign(session, st.load_log()),
            "factions": faction_rows(world),
            "event_types": [
                row.get("type") for row in (world.get("event_log") or []) if isinstance(row, dict)
            ],
        }

    valid_text = (
        "You stand at Cinderwatch's eastern gate. Rain spatters soot-dark stone; frayed banners hang "
        "above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; "
        "guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and "
        "paid rumor. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. "
        "You can read the notice board, approach the tavern runner, or watch the crowd."
    )
    summaries = []
    for case in CASES:
        mp = pytest.MonkeyPatch()
        current["case"] = case
        current["text"] = (
            json.dumps({"declared_claims": [], "narration": valid_text})
            if case == "valid_structured"
            else "You stand beside the gate in the rain."
        )
        base = ROOT / "development/tmp/pr_play_04" / case
        _seed_campaign_start_storage(base, mp)
        mp.setattr(api, "_compute_upstream_gate_for_live_gameplay", lambda: ({"manual_testing_blocked": False}, {}))
        mp.setattr(gm, "get_openai_api_key", lambda: "offline-placeholder")
        import openai
        mp.setattr(openai, "OpenAI", ctor)
        record = {"case": case, "functions": [
            "api.start_campaign",
            "api._run_resolved_turn_pipeline",
            "api._build_gpt_narration_from_authoritative_state",
            "api._complete_opening_turn_persistence_like_chat",
            "world.advance_world_tick",
            "gm.call_gpt",
        ]}
        try:
            record["new_campaign"] = decode(api.new_campaign(req())).get("ok")
            record["before"] = snap()
            before_calls = len(captures)
            if case == "pipeline_exception":
                mp.setattr(api, "_run_resolved_turn_pipeline", lambda **k: (_ for _ in ()).throw(RuntimeError("synthetic pipeline failure")))
            try:
                response = api.start_campaign(req())
                body = decode(response)
                record["status_code"] = getattr(response, "status_code", 200)
                gm_out = (body.get("gm_output") or {}) if isinstance(body, dict) else {}
                meta = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
                accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
                record["response"] = {
                    "ok": body.get("ok") if isinstance(body, dict) else None,
                    "status": body.get("status") if isinstance(body, dict) else None,
                    "player_facing_text": gm_out.get("player_facing_text"),
                    "provenance": accepted.get("provenance"),
                    "authorization_source": accepted.get("authorization_source"),
                    "structured_contract_failure": meta.get("structured_contract_failure"),
                    "structured_contract_reason": meta.get("structured_contract_reason"),
                    "resolution_kind": (body.get("resolution") or {}).get("kind") if isinstance(body, dict) else None,
                }
            except Exception as exc:
                record["raised"] = {"type": type(exc).__name__, "message": str(exc)}
            record["after"] = snap()
            record["sdk_mock_calls"] = len(captures) - before_calls
        finally:
            mp.undo()
        (outdir / f"{case}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        summaries.append({
            "case": case,
            "status": record.get("status_code"),
            "raised": record.get("raised"),
            "text": (record.get("response") or {}).get("player_facing_text"),
            "provenance": (record.get("response") or {}).get("provenance"),
            "reason": (record.get("response") or {}).get("structured_contract_reason"),
            "before": record["before"],
            "after": record["after"],
            "calls": record["sdk_mock_calls"],
        })
        print(json.dumps(summaries[-1], indent=2))
    (outdir / "summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
