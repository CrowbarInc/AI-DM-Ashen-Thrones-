#!/usr/bin/env python3
"""Small PR-AQ freeform physical-action / listen probe. Diagnostic only."""

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
        "I pace beside the notice board.",
        "I listen.",
        "I walk a few steps and listen.",
        "I step closer to the notice board.",
        "I look around after that.",
        "I walk toward the northern road.",
        "I head for the silver road.",
        "I leave through a door that is not here.",
        "I step over to the tavern runner and ask what the stew costs.",
        "I walk a few steps along the gate line and listen.",
        "I turn back to the tavern runner. \"What fills that pot?\"",
        "I stay here and head to the village.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "praq_physical_action" / "freeform_probe"
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
                    "gm": gm[:400],
                    "complete": bool(gm.strip()) and gm.strip()[-1] in ".!?\"'",
                    "ellipsis": gm.rstrip().endswith("…") or gm.rstrip().endswith("..."),
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AQ freeform physical-action probe {stamp}", ""]
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
                    f"complete: `{turn['complete']}` ellipsis: `{turn['ellipsis']}`"
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
