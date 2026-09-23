#!/usr/bin/env python3
"""Kiln-yard PR-AU freeform probe. Uses artifact-local storage, not canonical data/."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INVENTION_MARKERS = (
    "two coppers",
    "before dawn",
    "seven dozen",
    "mira",
    "ward clerk",
    "three hired tilers",
    "recaulked",
)


def _seed(runtime: Path) -> None:
    from game import storage
    from game.defaults import (
        default_campaign,
        default_character,
        default_combat,
        default_conditions,
        default_scene,
        default_session,
        default_world,
    )

    storage.BASE_DIR = runtime
    storage.DATA_DIR = runtime / "data"
    storage.WORLD_PATH = storage.DATA_DIR / "world.json"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    storage.CHARACTER_PATH = storage.DATA_DIR / "character.json"
    storage.CAMPAIGN_PATH = storage.DATA_DIR / "campaign.json"
    storage.SESSION_PATH = storage.DATA_DIR / "session.json"
    storage.COMBAT_PATH = storage.DATA_DIR / "combat.json"
    storage.CONDITIONS_PATH = storage.DATA_DIR / "conditions.json"
    storage.SESSION_LOG_PATH = storage.DATA_DIR / "session_log.jsonl"
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)

    scene = {
        "scene": {
            "id": "kiln_yard",
            "location": "Kiln Yard",
            "summary": "A brick kiln, a tally slate, and a night porter.",
            "visible_facts": [
                "A brick kiln smokes under a tin roof.",
                "A tally slate hangs by the kiln door.",
                "A kettle of mash sits on the porter's brazier.",
            ],
            "hidden_facts": [],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "night_porter",
                    "name": "Night Porter",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["porter"],
                }
            ],
            "interactables": [
                {
                    "id": "tally_slate",
                    "label": "Tally slate",
                    "aliases": ["slate", "board"],
                    "type": "investigate",
                }
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }
    storage._save_json(storage.scene_path("kiln_yard"), scene)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    world = default_world()
    world["npcs"] = [
        {
            "id": "night_porter",
            "name": "Night Porter",
            "location": "kiln_yard",
            "aliases": ["porter"],
            "topics": [
                {"id": "mash_exists", "text": "A kettle of mash sits on the porter's brazier."}
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "kiln_yard"
    session["visited_scene_ids"] = ["kiln_yard"]
    storage.save_session(session)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def main() -> int:
    from fastapi.testclient import TestClient

    from game.api import app
    from game.social import classify_social_question_dimension

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prau_grounded_social_absence" / "freeform_probe"
    runtime = out_dir / "runtime"
    out_dir.mkdir(parents=True, exist_ok=True)
    _seed(runtime)

    lines = [
        "I ask the night porter how much the mash costs.",
        "I ask the night porter when the kiln crew actually left.",
        "I ask the night porter how many bricks are left in that stack.",
        "I ask the night porter who last read that tally slate.",
        "I ask the night porter who recaulked the chimney flue, and how many tilers did the job.",
        "I ask the night porter what sits on the brazier.",
    ]
    turns: list[dict] = []
    client = TestClient(app)
    for text in lines:
        try:
            resp = client.post("/api/chat", json={"text": text})
            data = resp.json() if resp.status_code == 200 else {"ok": False, "status_code": resp.status_code}
        except Exception as exc:
            data = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "gm_output": {},
                "session": {},
                "resolution": {},
            }
        res = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
        social = res.get("social") if isinstance(res.get("social"), dict) else {}
        gm = str(((data.get("gm_output") or {}).get("player_facing_text") or ""))
        low = gm.lower()
        topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else {}
        turns.append(
            {
                "player": text,
                "ok": data.get("ok"),
                "error": data.get("error"),
                "kind": res.get("kind"),
                "dimension": classify_social_question_dimension(text),
                "topic_id": topic.get("id") if isinstance(topic, dict) else None,
                "reply_kind": social.get("reply_kind"),
                "npc": social.get("npc_id"),
                "invented_markers": [m for m in INVENTION_MARKERS if m in low],
                "internal_term": any(
                    token in low
                    for token in (
                        "authored answer",
                        "not in state",
                        "clue_knowledge",
                        "topic_revealed",
                        "grounded absence",
                    )
                ),
                "gm": gm[:500],
            }
        )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AU kiln-yard social-absence probe {stamp}", ""]
    for i, turn in enumerate(turns, 1):
        md_lines.extend(
            [
                f"## Turn {i}",
                "",
                f"**Player:** {turn['player']}",
                "",
                f"**GM:** {turn['gm']}",
                "",
                (
                    f"- kind: `{turn['kind']}` dimension: `{turn['dimension']}` "
                    f"topic: `{turn['topic_id']}` reply: `{turn['reply_kind']}` npc: `{turn['npc']}`"
                ),
                f"- invented_markers: `{turn['invented_markers']}` internal_term: `{turn['internal_term']}`",
                f"- ok: `{turn['ok']}` error: `{turn.get('error')}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
