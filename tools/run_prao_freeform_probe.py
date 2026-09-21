#!/usr/bin/env python3
"""Small PR-AO freeform investigation-provenance probe. Diagnostic only."""

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
    from game.leads import SESSION_LEAD_REGISTRY_KEY
    from game.referenced_surface import classify_referenced_surface
    from game.storage import load_active_scene

    apply_new_campaign_hard_reset()
    lines = [
        "I glance toward the rain barrel.",
        "I investigate the rain barrel.",
        "I look at the notice board.",
        "I search the mud by the crates for tracks.",
        "I inspect the board to see who last wrote on it.",
        "I examine the board to learn exactly when the patrol vanished.",
        "I search the rain barrel for proof that Rowan poisoned the well.",
        "I look for signs that Rowan was here.",
        "I walk over to the tavern runner. Who oiled that hinge last?",
        "I inspect the rain barrel after that.",
        "I search the square for evidence Mara took the key.",
        "I read the notice board carefully.",
        "I investigate the rain barrel again.",
        "I look toward the doorway of the townhouse.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prao_investigation_provenance" / "freeform_probe"
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
            res = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
            scene = load_active_scene()
            classified = classify_referenced_surface(text, scene)
            ctx = inspect_interaction_context(session)
            leads = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
            runtime = (session.get("scene_runtime") or {}).get(str(session.get("active_scene_id") or ""), {})
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "clue_id": res.get("clue_id"),
                    "scene": session.get("active_scene_id"),
                    "mode": ctx.get("interaction_mode"),
                    "authority": classified.get("authority"),
                    "target": classified.get("target"),
                    "skip": (res.get("metadata") or {}).get("skip_unrelated_clue_discovery")
                    if isinstance(res.get("metadata"), dict)
                    else None,
                    "leads": sorted(str(k) for k in leads.keys()) if isinstance(leads, dict) else [],
                    "discovered": list(runtime.get("discovered_clues") or []) if isinstance(runtime, dict) else [],
                    "gm": str(((data.get("gm_output") or {}).get("player_facing_text") or ""))[:400],
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AO freeform investigation-provenance probe {stamp}", ""]
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
                    f"mode: `{turn['mode']}` clue: `{turn['clue_id']}`"
                ),
                (
                    f"- authority: `{turn['authority']}` target: `{turn['target']}` "
                    f"skip: `{turn['skip']}`"
                ),
                f"- leads: `{turn['leads']}`",
                f"- discovered: `{turn['discovered']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
