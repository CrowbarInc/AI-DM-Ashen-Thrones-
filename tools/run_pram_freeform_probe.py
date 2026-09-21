#!/usr/bin/env python3
"""Small PR-AM freeform world-action / social-lock probe. Diagnostic only."""

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
        "I walk over to the tavern runner and ask what the stew costs.",
        "Alright. I inspect the notice board now.",
        "I read the notice again.",
        "I look at the roster board the serjeant keeps watching.",
        "Fine. I'll follow the missing patrol rumor along that northwest mud track.",
        "Why?",
        "What happened to the patrol, exactly?",
        "I turn to nobody and inspect the silver obelisk.",
        "I'll head back to the gate.",
        "I step over to the runner again. Who last checked that board?",
        "I glance at the notice board after that.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pram_explicit_world_action" / "freeform_probe"
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
            ctx = inspect_interaction_context(session)
            gm = ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400]
            meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": session.get("active_scene_id"),
                    "interlocutor_before_kind": ctx.get("active_interaction_kind"),
                    "interlocutor": ctx.get("active_interaction_target_id"),
                    "mode": ctx.get("interaction_mode"),
                    "target_id": res.get("target_id") or res.get("targetEntityId"),
                    "surface_authority": meta.get("referenced_surface_authority"),
                    "gm": gm,
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AM freeform routing probe {stamp}", ""]
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
                    f"- kind: `{turn['kind']}` scene: `{turn['scene']}` "
                    f"interlocutor: `{turn['interlocutor']}` mode: `{turn['mode']}`"
                ),
                f"- target: `{turn['target_id']}` authority: `{turn['surface_authority']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
