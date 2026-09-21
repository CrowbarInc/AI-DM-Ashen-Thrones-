#!/usr/bin/env python3
"""Small PR-AK freeform referenced-surface probe. Diagnostic only."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _lead_ids(session: dict) -> list[str]:
    reg = session.get("lead_registry") or {}
    return [str(k) for k in reg.keys()] if isinstance(reg, dict) else []


def main() -> int:
    from fastapi.testclient import TestClient

    from game.api import app
    from game.campaign_reset import apply_new_campaign_hard_reset
    from game.interaction_context import inspect as inspect_interaction_context
    from game.referenced_surface import classify_referenced_surface
    from game.storage import load_active_scene, load_world

    apply_new_campaign_hard_reset()
    lines = [
        "I read the posted notices.",
        "I take a closer look at that soot-dark stone under the banners.",
        "I inspect the brass orrery on the counter.",
        "I look around after that miss.",
        "I ask the nearest watchman whether he checked any duty records tonight.",
        "Then I try to inspect those records.",
        "I examine the board the serjeant keeps glancing at.",
        "I look at the notice again, not the other board.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prak_referenced_surface" / "freeform_probe"
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
            scene = load_active_scene()
            world = load_world()
            classified = classify_referenced_surface(text, scene, world=world)
            gm = ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400]
            md = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": session.get("active_scene_id"),
                    "target_extracted": classified.get("target"),
                    "authority": classified.get("authority") or md.get("referenced_surface_authority"),
                    "binding": classified.get("interactable_id") or md.get("referenced_surface_interactable_id"),
                    "visible_fact": classified.get("visible_fact") or md.get("referenced_surface_visible_fact"),
                    "clue_id": res.get("clue_id"),
                    "interlocutor": ctx.get("active_interaction_target_id"),
                    "gm": gm,
                    "lead_ids": _lead_ids(session),
                    "fallback": md.get("referenced_surface_authority") or md.get("parser_lane"),
                    "invented_name": any(
                        token in gm.lower()
                        for token in ("thoran", "lirael", "marrow", "glassport")
                    ),
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AK freeform interaction probe {stamp}", ""]
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
                    f"target: `{turn['target_extracted']}` authority: `{turn['authority']}` "
                    f"binding: `{turn['binding']}` clue: `{turn['clue_id']}` "
                    f"interlocutor: `{turn['interlocutor']}`"
                ),
                f"- visible_fact: `{turn['visible_fact']}`",
                f"- lead_ids: `{json.dumps(turn['lead_ids'])}`",
                f"- fallback: `{turn['fallback']}` invented_name: `{turn['invented_name']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
