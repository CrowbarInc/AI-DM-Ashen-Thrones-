#!/usr/bin/env python3
"""Small PR-AI freeform social-knowledge probe. Diagnostic only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from fastapi.testclient import TestClient

    from game.api import app
    from game.campaign_reset import apply_new_campaign_hard_reset
    from game.interaction_context import inspect as inspect_interaction_context

    apply_new_campaign_hard_reset()
    lines = [
        "I turn to the Guard Captain. \"Who's in charge of the watch tonight?\"",
        "What are you doing about the missing patrol?",
        "Who stole the chapel relic?",
        "I step over to the tavern runner. \"Who commands the watch here?\"",
        "What does a bowl of stew cost?",
        "Who last spoke to that patrol before they left?",
        "What's nearby from here?",
        "I look around.",
        "I'll follow the missing patrol rumor along that northwest mud track.",
        "I look for signs of the patrol.",
        "Let's go back.",
        "I turn to the Gate Serjeant. \"Did the census choke change the route?\"",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prai_bound_speaker_knowledge" / "freeform_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    turns: list[dict] = []
    with TestClient(app) as client:
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
            session = data.get("session") or {}
            res = data.get("resolution") or {}
            social = res.get("social") if isinstance(res.get("social"), dict) else {}
            ctx = inspect_interaction_context(session)
            gm = ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400]
            gm_low = gm.lower()
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": session.get("active_scene_id"),
                    "interlocutor": ctx.get("active_interaction_target_id"),
                    "npc_id": social.get("npc_id"),
                    "topic_id": (
                        (social.get("topic_revealed") or {}).get("id")
                        if isinstance(social.get("topic_revealed"), dict)
                        else None
                    ),
                    "gm": gm,
                    "ignorance": any(
                        marker in gm_low
                        for marker in ("i don't know", "i do not know enough", "not something i can say")
                    ),
                    "thoran": "thoran" in gm_low,
                    "stew": "stew" in gm_low,
                    "phantom_guard": "the guard says" in gm_low,
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [f"# PR-AI freeform social-knowledge probe {stamp}", ""]
    for i, turn in enumerate(turns, 1):
        md.extend(
            [
                f"## Turn {i}",
                "",
                f"**Player:** {turn['player']}",
                "",
                f"**GM:** {turn['gm']}",
                "",
                (
                    f"- kind: `{turn['kind']}` scene: `{turn['scene']}` "
                    f"interlocutor: `{turn['interlocutor']}` npc_id: `{turn['npc_id']}` "
                    f"topic_id: `{turn['topic_id']}` ignorance: `{turn['ignorance']}` "
                    f"thoran: `{turn['thoran']}` stew: `{turn['stew']}` "
                    f"phantom_guard: `{turn['phantom_guard']}`"
                ),
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
