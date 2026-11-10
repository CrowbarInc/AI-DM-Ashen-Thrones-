"""Provider-free twelve-turn replay for T04 local-action completion."""
from __future__ import annotations

import ast
import json
import os
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "after" / "twelve_turn"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", None)
os.environ.pop("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", None)
os.environ.pop("ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", None)
os.environ.pop("ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION", None)
os.environ.pop("OPENAI_API_KEY", None)

_source = (ROOT / "artifacts/pr_play_t05_composition/run_sequence.py").read_text(encoding="utf-8")
TURNS = ast.literal_eval(_source.split("TURNS = ", 1)[1].split("\n]\n", 1)[0] + "\n]")


def main() -> None:
    from fastapi.testclient import TestClient

    from game import storage
    from game.api import app
    from tests.helpers.storage_isolation import install
    from tests.pr_play_79df3_harness import seed_gate

    network = []
    real_connect = socket.create_connection

    def guarded_connect(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else str(address)
        if host not in {"127.0.0.1", "localhost", "::1"}:
            network.append(host)
            raise OSError(f"blocked non-local connect to {host}")
        return real_connect(address, *args, **kwargs)

    socket.create_connection = guarded_connect
    install(OUT / "run_data")

    class Monkey:
        def setenv(self, key, value):
            os.environ[key] = str(value)

        def delenv(self, key, raising=True):
            os.environ.pop(key, None)

        def setattr(self, target, name, value, raising=True):
            if isinstance(target, str):
                module_name, attr = target.rsplit(".", 1)
                setattr(sys.modules[module_name], attr, value)
            else:
                setattr(target, name, value)

    seed_gate(OUT / "run_data", Monkey())
    rows = []
    started = time.perf_counter()
    with TestClient(app) as client:
        for turn in TURNS:
            before = storage.load_session()
            response = client.post("/api/chat?ui_mode=player", json={"text": turn["text"]})
            body = response.json()
            log = storage.load_log()[-1]
            resolution = log.get("resolution") if isinstance(log, dict) else {}
            meta = resolution.get("metadata") if isinstance(resolution, dict) else {}
            decision = meta.get("conversational_decision") if isinstance(meta, dict) else {}
            after = storage.load_session()
            visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
            row = {
                "id": turn["id"],
                "text": turn["text"],
                "status": response.status_code,
                "visible": visible,
                "kind": resolution.get("kind"),
                "success": resolution.get("success"),
                "resolved_transition": resolution.get("resolved_transition"),
                "target_scene_id": resolution.get("target_scene_id"),
                "reason": (decision or {}).get("reason") if isinstance(decision, dict) else None,
                "action_owner": meta.get("action_owner"),
                "scene_before": before.get("active_scene_id"),
                "scene_after": after.get("active_scene_id"),
                "publication": (after.get("last_publication") or {}).get("visible"),
                "clues": sorted((after.get("clue_knowledge") or {}).keys()) if isinstance(after.get("clue_knowledge"), dict) else after.get("clue_knowledge"),
                "discovered": after.get("discovered_clues"),
            }
            if turn["id"] == "T04":
                row["transient_local_action"] = meta.get("transient_local_action")
                gm = log.get("gm_output") if isinstance(log, dict) else {}
                accepted = (gm.get("metadata") or {}).get("accepted_response") if isinstance(gm, dict) else {}
                row["accepted"] = {
                    "text": (accepted or {}).get("text"),
                    "immutable": (accepted or {}).get("immutable"),
                    "hard_valid": ((accepted or {}).get("hard_validation") or {}).get("hard_valid"),
                    "authorization_source": (accepted or {}).get("authorization_source"),
                }
            rows.append(row)
            print(turn["id"], response.status_code, visible[:160], flush=True)
    summary = {
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "live_provider_calls": 0,
        "network_blocks": network,
        "turns": rows,
    }
    (OUT / "sequence_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"turns": len(rows), "elapsed_ms": summary["elapsed_ms"], "network": network}))


if __name__ == "__main__":
    main()
