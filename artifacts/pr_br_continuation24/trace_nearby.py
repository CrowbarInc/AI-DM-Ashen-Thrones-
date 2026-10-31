import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from game.api import app
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from tests.test_nearby_place_existence_knowledge_ownership import (
    INVENTED_TAVERN,
    KILN,
    _kiln_world,
    _seed,
)

mp = MonkeyPatch()
tmp = Path(tempfile.mkdtemp())
_seed(tmp, mp, KILN, world=_kiln_world())
client = TestClient(app)
turns = (
    ("What's nearby?", "I don't know what's nearby."),
    ("Who is nearby?", INVENTED_TAVERN),
    ("Night Porter, is there a tavern nearby?", INVENTED_TAVERN),
)
for text, stub in turns:
    mp.setattr("game.api.call_gpt", lambda *_a, _stub=stub, **_k: _gm_response(_stub))
    data = client.post("/api/chat", json={"text": text}).json()
    res = data.get("resolution") or {}
    meta = res.get("metadata") or {}
    gm = data.get("gm_output") or {}
    print("---", text)
    print("kind", res.get("kind"))
    print("before", meta.get("contract_before_resolver"))
    print("family", meta.get("adjudication_resolver_family"))
    print("op", (meta.get("resolution_contract") or {}).get("operation"))
    print("text", (gm.get("player_facing_text") or "")[:200])
