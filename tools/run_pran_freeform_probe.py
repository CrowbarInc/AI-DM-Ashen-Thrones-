#!/usr/bin/env python3
"""Small PR-AN freeform question-sufficiency probe. Diagnostic only."""

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
    from game.social import (
        authored_answer_sufficient_for_question,
        authored_topic_relevant_to_question,
        classify_social_question_dimension,
        npc_dict_by_id,
    )
    from game.storage import load_world

    apply_new_campaign_hard_reset()
    lines = [
        "I walk over to the tavern runner. Do you know the name of whoever last checked that board?",
        "When did that missing patrol vanish, exactly?",
        "Where was the patrol last seen?",
        "Why is the stew even out here in the rain?",
        "How many bowls do you have left?",
        "What is posted on that board?",
        "Alright, what does the stew cost then?",
        "I turn to the Guard Captain. Who commands the watch here?",
        "I stay with the captain. Who last checked the notice board?",
        "I step back to the runner. Tell me about the missing patrol.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pran_question_dimension" / "freeform_probe"
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
            nid = str(social.get("npc_id") or ctx.get("active_interaction_target_id") or "").strip()
            world = load_world()
            npc = npc_dict_by_id(world, nid) if nid else None
            dimension = classify_social_question_dimension(text)
            candidates = []
            if isinstance(npc, dict):
                for rec in npc.get("topics") or []:
                    if not isinstance(rec, dict):
                        continue
                    candidates.append(
                        {
                            "id": rec.get("id"),
                            "relevant": authored_topic_relevant_to_question(text, rec, npc=npc),
                            "sufficient": authored_answer_sufficient_for_question(text, rec),
                            "clue_id": rec.get("clue_id"),
                        }
                    )
            leads = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "scene": session.get("active_scene_id"),
                    "speaker": nid or None,
                    "mode": ctx.get("interaction_mode"),
                    "dimension": dimension,
                    "topic_revealed": (social.get("topic_revealed") or {}).get("id")
                    if isinstance(social.get("topic_revealed"), dict)
                    else None,
                    "clue_id": res.get("clue_id"),
                    "candidates": candidates,
                    "leads": sorted(str(k) for k in leads.keys()) if isinstance(leads, dict) else [],
                    "gm": gm,
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AN freeform question-sufficiency probe {stamp}", ""]
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
                    f"speaker: `{turn['speaker']}` mode: `{turn['mode']}`"
                ),
                f"- dimension: `{turn['dimension']}` topic: `{turn['topic_revealed']}` clue: `{turn['clue_id']}`",
                f"- candidates: `{json.dumps(turn['candidates'])}`",
                f"- leads: `{turn['leads']}`",
                "",
            ]
        )
    (out_dir / f"{stamp}_probe.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / (stamp + '_probe.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
