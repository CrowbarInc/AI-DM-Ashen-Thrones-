#!/usr/bin/env python3
"""Small PR-AJ freeform lead-provenance probe. Diagnostic only."""

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


def _narration_ctx(session: dict) -> list[str]:
    return [lid for lid in _lead_ids(session) if "narration_ctx" in lid]


def _pending(session: dict, scene_id: str) -> list[dict]:
    runtime = session.get("scene_runtime") or {}
    scene_rt = runtime.get(scene_id) if isinstance(runtime, dict) else {}
    raw = scene_rt.get("pending_leads") if isinstance(scene_rt, dict) else []
    return [p for p in (raw or []) if isinstance(p, dict)]


def main() -> int:
    from fastapi.testclient import TestClient

    from game.api import app
    from game.campaign_reset import apply_new_campaign_hard_reset
    from game.interaction_context import inspect as inspect_interaction_context

    apply_new_campaign_hard_reset()
    lines = [
        'I turn to the Guard Captain. "Who keeps the watch roster tonight?"',
        "Any chance the roads west of here are closed to carts after dusk?",
        'I stay with the captain. "Who commands the watch here?"',
        "You said something about a watch commander — say that again in your own words.",
        "Captain Thoran again, then? Same person you just named?",
        "I'll go chase that closed western cart road you mentioned.",
        "I look around.",
        "I read the notice board.",
        "I'll follow the missing patrol rumor along that northwest mud track.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "praj_authoritative_lead_provenance" / "freeform_probe"
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
            scene_id = str(session.get("active_scene_id") or "")
            gm = ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400]
            nsc = ((res.get("metadata") or {}).get("narration_state_consistency") or {})
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": scene_id,
                    "interlocutor": ctx.get("active_interaction_target_id"),
                    "npc_id": social.get("npc_id"),
                    "topic_id": (
                        (social.get("topic_revealed") or {}).get("id")
                        if isinstance(social.get("topic_revealed"), dict)
                        else None
                    ),
                    "clue_id": res.get("clue_id"),
                    "gm": gm,
                    "lead_ids": _lead_ids(session),
                    "narration_ctx": _narration_ctx(session),
                    "pending": _pending(session, scene_id),
                    "mismatch_repair": nsc.get("mismatch_repair_applied"),
                    "prose_suppressed": nsc.get("prose_derived_authority_suppressed"),
                    "target_scene_id": res.get("target_scene_id"),
                    "resolved_transition": res.get("resolved_transition"),
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [f"# PR-AJ freeform provenance probe {stamp}", ""]
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
                    f"topic_id: `{turn['topic_id']}` clue_id: `{turn['clue_id']}` "
                    f"repair: `{turn['mismatch_repair']}` suppressed: `{turn['prose_suppressed']}` "
                    f"transition: `{turn['resolved_transition']}` target: `{turn['target_scene_id']}`"
                ),
                f"- lead_ids: `{json.dumps(turn['lead_ids'])}`",
                f"- narration_ctx: `{json.dumps(turn['narration_ctx'])}`",
                f"- pending: `{json.dumps(turn['pending'])}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
