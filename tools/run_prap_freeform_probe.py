#!/usr/bin/env python3
"""Small PR-AP freeform grounded-refusal realization probe. Diagnostic only."""

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
    from game.playability_eval import _MALFORMED_REFUSAL_FRAGMENT_RE
    from game.social import classify_social_question_dimension
    from game.storage import load_active_scene

    apply_new_campaign_hard_reset()
    lines = [
        "I walk over to the tavern runner. Who oiled that hinge last?",
        "When did that patrol actually leave?",
        "Where did they go after the crates?",
        "Why is the stew even out here?",
        "How many bowls are left in that pot?",
        "How much does a bowl of stew cost?",
        "Who last checked that board?",
        "What rumors have you heard about the missing patrol?",
        "What's being done about the missing patrol?",
        "I ask the runner again what the stew costs.",
        "I look toward the notice board.",
        "I ask the runner who last checked that board.",
        "I ask the runner what sits in that pot.",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "prap_grounded_refusal" / "freeform_probe"
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
            social = res.get("social") if isinstance(res.get("social"), dict) else {}
            gm = str(((data.get("gm_output") or {}).get("player_facing_text") or ""))
            ctx = inspect_interaction_context(session)
            leads = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
            turns.append(
                {
                    "player": text,
                    "ok": data.get("ok"),
                    "kind": res.get("kind"),
                    "dimension": classify_social_question_dimension(text),
                    "topic_id": ((social.get("topic_revealed") or {}) or {}).get("id")
                    if isinstance(social.get("topic_revealed"), dict)
                    else None,
                    "scene": session.get("active_scene_id"),
                    "mode": ctx.get("interaction_mode"),
                    "npc": social.get("npc_id") or ctx.get("active_interaction_target_id"),
                    "malformed": bool(_MALFORMED_REFUSAL_FRAGMENT_RE.search(gm)),
                    "internal_term": any(
                        token in gm.lower()
                        for token in (
                            "authored answer",
                            "not in state",
                            "clue_knowledge",
                            "topic_revealed",
                            "dimension is unsupported",
                        )
                    ),
                    "leads": sorted(str(k) for k in leads.keys()) if isinstance(leads, dict) else [],
                    "gm": gm[:400],
                }
            )
    report = {"stamp": stamp, "turns": turns}
    (out_dir / f"{stamp}_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [f"# PR-AP freeform refusal-realization probe {stamp}", ""]
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
                    f"- kind: `{turn['kind']}` dimension: `{turn['dimension']}` "
                    f"topic: `{turn['topic_id']}` npc: `{turn['npc']}`"
                ),
                (
                    f"- malformed: `{turn['malformed']}` internal_term: `{turn['internal_term']}` "
                    f"mode: `{turn['mode']}`"
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
