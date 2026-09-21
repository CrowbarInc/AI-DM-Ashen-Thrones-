#!/usr/bin/env python3
"""Small PR-AR freeform perception-authority probe. Diagnostic only."""

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
    from game.human_adjacent_focus import classify_human_adjacent_intent_family
    from game.intent_parser import parse_freeform_to_action
    from game.interaction_context import inspect as inspect_interaction_context
    from game.leads import SESSION_LEAD_REGISTRY_KEY
    from game.storage import load_active_scene

    apply_new_campaign_hard_reset()
    lines = [
        "I listen.",
        "I listen for whispers.",
        "I listen for footsteps.",
        "I keep listening.",
        "I look around.",
        "I watch the road.",
        "I listen at the door.",
        "I walk a few steps along the gate line and listen.",
        "I glance at the notice board after that.",
        "I listen for that sound I thought I heard.",
        "I step closer to the tavern runner and listen.",
        "I look toward the tower.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prar_perception_authority" / "freeform_probe"
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
                    "scene": {},
                }
            session = data.get("session") or {}
            res = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
            gm = str(((data.get("gm_output") or {}).get("player_facing_text") or ""))
            ctx = inspect_interaction_context(session)
            leads = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
            scene_env = load_active_scene()
            parsed = parse_freeform_to_action(text, scene_env if isinstance(scene_env, dict) else None)
            low = gm.lower()
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "parsed_type": (parsed or {}).get("type"),
                    "lane": ((parsed or {}).get("metadata") or {}).get("parser_lane") if parsed else None,
                    "ha_family": classify_human_adjacent_intent_family(text),
                    "scene": session.get("active_scene_id"),
                    "mode": ctx.get("interaction_mode"),
                    "npc": ctx.get("active_interaction_target_id"),
                    "leads": sorted(str(k) for k in leads.keys()) if isinstance(leads, dict) else [],
                    "gm": gm[:500],
                    "complete": bool(gm.strip()) and gm.strip()[-1] in ".!?\"'",
                    "invented_whisper": "whisper" in low,
                    "invented_complaint": "complaint" in low,
                    "invented_footstep": "footstep" in low,
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AR freeform perception-authority probe {stamp}", ""]
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
                    f"- kind: `{turn['kind']}` parsed: `{turn['parsed_type']}` "
                    f"lane: `{turn['lane']}` ha: `{turn['ha_family']}`"
                ),
                (
                    f"- scene: `{turn['scene']}` mode: `{turn['mode']}` npc: `{turn['npc']}` "
                    f"complete: `{turn['complete']}`"
                ),
                (
                    f"- invented whisper/complaint/footstep: "
                    f"`{turn['invented_whisper']}` / `{turn['invented_complaint']}` / `{turn['invented_footstep']}`"
                ),
                f"- leads: `{turn['leads']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
