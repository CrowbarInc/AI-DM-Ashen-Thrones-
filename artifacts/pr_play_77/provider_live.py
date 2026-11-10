"""One real provider-assisted multi-step interpretation. No key material is written."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
from tests.helpers.storage_isolation import install

install(OUT / "provider_live_run")
for key in (
    "ASHEN_EXPERIMENTAL_BRANCHING", "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS",
    "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
    "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", "ASHEN_PHYSICAL_PROVIDER",
):
    os.environ[key] = "1"

from game.bounded_improvisation import LEDGER_KEY
from game.physical_adjudication import commit_physical, interpret_plan_with_provider, provider_usage
from tests.test_pr_play_76_physical import add, door, stage

attempts = []
executed = None
chosen = None
for text in (
    "I open the door and look inside.",
    "Open the door, then check inside.",
    "I push the crate aside and inspect it.",
):
    session, scene, world = stage()
    if "crate" in text:
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
        target = "crate"
    else:
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
        target = "door"
    verdict = interpret_plan_with_provider(text, session=session, scene=scene, world=world)
    attempts.append({"input": text, "accepted": bool(verdict.get("accepted")), "reason": verdict.get("reason"),
                     "detail": verdict.get("detail"), "proposed": verdict.get("proposed")})
    if verdict.get("accepted") and executed is None:
        chosen = text
        executed = commit_physical(scene, session, world, {"id": target, "target_id": target},
                                   prompt=text, action_id=target, label="physical")
        open_state = (session.get(LEDGER_KEY) or {}).get("entries", [{}])[0].get("properties", {})
        break
usage = provider_usage()
record = {
    "accepted": bool(executed),
    "chosen_input": chosen,
    "attempts": attempts,
    "committed_by_provider": False,
    "used_for_execution": bool(executed and executed["metadata"]["physical_adjudication"].get("provider_plan") == "accepted"),
    "publication": (executed or {}).get("metadata", {}).get("engine_publication") if executed else None,
    "resulting_properties": open_state if executed else None,
    "prior_rejected_requests": 1,
    "prior_rejected_tokens": 264,
    "requests": usage["requests"] + 1,
    "tokens": usage["tokens"] + 264,
    "retries": usage["retries"],
    "blocked": executed is None,
}
(OUT / "provider_live.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record))
