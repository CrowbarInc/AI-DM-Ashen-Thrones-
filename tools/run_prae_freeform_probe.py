#!/usr/bin/env python3
"""Small PR-AE freeform stay/leave/pursuit probe. Diagnostic only."""

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
        "I walk up to the guard and ask what's posted on that notice.",
        "Alright, I'll stay here a moment and hear you out. When did that patrol go missing?",
        "Okay. I'm heading out after them along that northwest track.",
        "Now that I've left the gate, I look at the road ahead.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prae_stay_leave" / "freeform_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    turns: list[dict] = []
    with TestClient(app) as client:
        for text in lines:
            resp = client.post("/api/chat", json={"text": text})
            data = resp.json() if resp.status_code == 200 else {"ok": False, "status_code": resp.status_code}
            session = data.get("session") or {}
            res = data.get("resolution") or {}
            ctx = inspect_interaction_context(session)
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "resolved_transition": res.get("resolved_transition"),
                    "target_scene_id": res.get("target_scene_id"),
                    "scene": session.get("active_scene_id"),
                    "interlocutor": ctx.get("active_interaction_target_id"),
                    "mode": ctx.get("interaction_mode"),
                    "gm": ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400],
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [f"# PR-AE freeform probe {stamp}", ""]
    for i, turn in enumerate(turns, 1):
        md.extend(
            [
                f"## Turn {i}",
                "",
                f"**Player:** {turn['player']}",
                "",
                f"**GM:** {turn['gm']}",
                "",
                f"- kind: `{turn['kind']}` scene: `{turn['scene']}` transition: `{turn['resolved_transition']}` target: `{turn['target_scene_id']}` interlocutor: `{turn['interlocutor']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
