#!/usr/bin/env python3
"""Small PR-AL freeform social-relevance probe. Diagnostic only."""

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
    from game.social import (
        _match_present_npc_topic_authored_knowledge,
        _next_topic_to_reveal,
        authored_topic_relevant_to_question,
        classify_social_question_dimension,
    )
    from game.storage import get_npc_runtime, load_active_scene, load_world
    from game.world import get_world_npc_by_id

    apply_new_campaign_hard_reset()
    lines = [
        "I walk over to the tavern runner. What's in the stew today?",
        "Fine, then tell me about the missing patrol.",
        "How much for a bowl?",
        "I turn to the Guard Captain. Who posted the night watch list?",
        "I ask the runner whether the stew is salted.",
        "What happened to that patrol, exactly?",
        "What do you mean?",
        "I ask the captain about the missing patrol instead.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pral_social_question_relevance" / "freeform_probe"
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
            world = load_world()
            scene = load_active_scene()
            sid = str(session.get("active_scene_id") or "")
            nid = str(ctx.get("active_interaction_target_id") or "")
            npc = get_world_npc_by_id(world, nid) if nid else None
            topic = ((res.get("social") or {}).get("topic_revealed") or {}) if isinstance(res.get("social"), dict) else {}
            gm = ((data.get("gm_output") or {}).get("player_facing_text") or "")[:400]
            candidates = []
            if isinstance(npc, dict):
                for rec in npc.get("topics") or []:
                    if not isinstance(rec, dict):
                        continue
                    candidates.append(
                        {
                            "id": rec.get("id"),
                            "authorized": True,
                            "relevant": authored_topic_relevant_to_question(text, rec, npc=npc),
                            "has_clue": bool(rec.get("clue_id")),
                        }
                    )
            extra = _match_present_npc_topic_authored_knowledge(
                world=world,
                session=session,
                scene_id=sid,
                player_text=text,
                dimension=classify_social_question_dimension(text),
                restrict_npc_id=nid or None,
                scene=scene,
                speaker_name=str((npc or {}).get("name") or "") or None,
            )
            runtime = get_npc_runtime(session, nid) if nid else {}
            next_topic = _next_topic_to_reveal(npc, runtime, None, player_text=text) if isinstance(npc, dict) else None
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": sid,
                    "interlocutor": nid,
                    "normalized_question": " ".join(text.strip().split()),
                    "dimension": classify_social_question_dimension(text),
                    "candidates": candidates,
                    "selected_topic": topic.get("id"),
                    "rejected": [c["id"] for c in candidates if c["id"] and c["id"] != topic.get("id")],
                    "clue_id": res.get("clue_id"),
                    "next_unrevealed_relevant": (next_topic or {}).get("id") if isinstance(next_topic, dict) else None,
                    "authored_match": (extra or {}).get("source"),
                    "gm": gm,
                    "lead_ids": _lead_ids(session),
                    "patrol_in_gm": "patrol" in gm.lower() and "stew" in text.lower(),
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AL freeform social-relevance probe {stamp}", ""]
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
                    f"interlocutor: `{turn['interlocutor']}` selected: `{turn['selected_topic']}` "
                    f"clue: `{turn['clue_id']}`"
                ),
                f"- dimension: `{turn['dimension']}` authored_match: `{turn['authored_match']}`",
                f"- candidates: `{json.dumps(turn['candidates'])}`",
                f"- rejected: `{json.dumps(turn['rejected'])}`",
                f"- lead_ids: `{json.dumps(turn['lead_ids'])}`",
                f"- patrol_in_gm_on_stew_ask: `{turn['patrol_in_gm']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
