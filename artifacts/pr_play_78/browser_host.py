"""Isolated browser host. Provider calls stay off; gameplay flags match this cycle."""
import copy
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install

install(OUT / "browser_data")
for key in (
    "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "ASHEN_DISABLE_PROVIDER_CALLS",
    "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION",
    "ASHEN_DISABLE_PROVIDER_RETRIES", "ASHEN_EXPERIMENTAL_BRANCHING",
    "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS", "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
    "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION", "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
    "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "ASHEN_BOUNDED_SPEECH",
):
    os.environ[key] = "1"
from game import api
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE

api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api.app, host="127.0.0.1", port=8092, log_level="warning")
