"""Run with repo Python from repository root; writes sanitized synthetic HTTP evidence."""
import hashlib
import json
import os
import socket
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"

import pytest
from fastapi.testclient import TestClient
import game.api as api
from game import storage as st
from game.state_channels import is_author_key, is_debug_key
from tests.helpers.live_model_guard import install_live_model_guard
from tests.test_ui_mode_backend_integration import _seed_minimal_with_spoilers

SENTINEL = "PR_PLAY_21_PRIVILEGED_SENTINEL"


def sanitize(value, restricted=False):
    if isinstance(value, dict):
        return {k: sanitize(v, restricted or is_author_key(k) or is_debug_key(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, restricted) for v in value]
    if restricted and isinstance(value, str) and SENTINEL not in value:
        return "[REDACTED]"
    return value


def main(destination):
    with tempfile.TemporaryDirectory(dir="development/tmp") as directory, pytest.MonkeyPatch.context() as patch:
        install_live_model_guard(patch)
        original_connect = socket.socket.connect
        def no_network(sock, address):
            if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
                return original_connect(sock, address)  # Windows asyncio socketpair
            raise AssertionError("PR-PLAY-21: external network forbidden")
        patch.setattr(socket.socket, "connect", no_network)
        _seed_minimal_with_spoilers(Path(directory).resolve(), patch)
        patch.setattr(st, "SNAPSHOTS_DIR", st.DATA_DIR / "snapshots")
        scene = st.load_active_scene()
        scene["scene"]["hidden_facts"] = [SENTINEL]
        st._save_json(st.scene_path("test_scene"), scene)
        session = st.load_session()
        session["debug_traces"] = [{"detail": SENTINEL + "_DEBUG"}]
        st.save_session(session)
        st.append_log({"timestamp": "synthetic", "request": {"chat": "Public input"},
                       "gm_output": {"player_facing_text": "Public narration"},
                       "resolution": {"internal_state": SENTINEL + "_LOG"}})
        patch.setattr(api, "log_upstream_api_preflight_at_startup", lambda: None)
        rows = []
        with TestClient(api.app) as client:
            for path in ("/api/state", "/api/state?ui_mode=author", "/api/state?ui_mode=debug",
                         "/api/log", "/api/log?ui_mode=author", "/api/log?ui_mode=debug",
                         "/api/debug_trace", "/api/debug_trace?ui_mode=debug", "/api/snapshots"):
                response = client.get(path)
                rows.append({"path": path, "status": response.status_code,
                             "requested_mode": path.split("ui_mode=")[-1] if "ui_mode=" in path else "player",
                             "effective_mode": response.json().get("ui_mode"),
                             "response_keys": sorted(response.json()),
                             "sentinel_in_serialized_http": SENTINEL in response.text,
                             "response_text_sanitized": json.dumps(sanitize(response.json()), sort_keys=True)})
        result = {"transport": "actual ASGI HTTP TestClient with application lifespan",
                  "live_provider_requests": 0, "rows": rows,
                  "authoritative_sentinel_preserved": st.load_active_scene()["scene"]["hidden_facts"] == [SENTINEL],
                  "resolver_sha256": hashlib.sha256(Path("game/api_ui_mode.py").read_bytes()).hexdigest()}
        Path(destination).write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
