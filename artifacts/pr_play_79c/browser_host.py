"""Live browser host for PR-PLAY-79C.

Uses the initialized campaign seed. It does not stub the provider and it does
not start a second campaign opening.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install

install(OUT / "browser_data")
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
for key in (
    "ASHEN_DISABLE_PROVIDER_CALLS",
    "ASHEN_DISABLE_LIVE_INTERPRETATION",
    "ASHEN_DISABLE_EXPRESSION_GENERATION",
):
    os.environ.pop(key, None)
for key in (
    "ASHEN_EXPERIMENTAL_BRANCHING",
    "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS",
    "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
    "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
    "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
    "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS",
    "ASHEN_BOUNDED_SPEECH",
    "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION",
):
    os.environ[key] = "1"

from game import api

api.log_upstream_api_preflight_at_startup = lambda: None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api.app, host="127.0.0.1", port=8097, log_level="warning")
