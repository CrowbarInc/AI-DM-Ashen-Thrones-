#!/usr/bin/env python3
"""Interactive CLI to run manual gauntlets G1–G8 against the real ``game.api.chat`` path.

Full scenarios, rubric, and placeholders live in ``docs/manual_gauntlets.md`` (source of truth).
This script only stores compact labels, one-line intent summaries, and optional template lines
so the operator can substitute ``[PLACEHOLDER]`` values and drive turns from the terminal.

Transcripts are written as Markdown under ``artifacts/manual_gauntlets/``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.api import chat  # noqa: E402
from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.models import ChatRequest  # noqa: E402
from tests.helpers.transcript_runner import (  # noqa: E402
    latest_target_id,
    latest_target_source,
    snapshot_from_chat_payload,
)


@dataclass(frozen=True)
class GauntletSpec:
    gauntlet_id: str
    label: str
    description: str
    prompt_templates: tuple[str, ...]


# Compact mapping only — see docs/manual_gauntlets.md for setup, rubric, and subsystems.
GAUNTLETS: dict[str, GauntletSpec] = {
    "g1": GauntletSpec(
        "g1",
        "Same NPC follow-up should advance, not restate",
        "Second line should build on the lead instead of re-introducing it.",
        (
            "What do you know about [LEAD_TOPIC]?",
            "Right — you mentioned that before. What happens if we pursue it?",
        ),
    ),
    "g2": GauntletSpec(
        "g2",
        "Hint upgrades to explicit without reset",
        "Vague → specific; later turns must not revert to hint-only posture.",
        (
            "I heard there's trouble around [VAGUE_HOOK]. Anything you can share?",
            "You're holding something back. Spell it out — who's involved?",
            "So we're clear: [SHORT_SUMMARY_OF_WHAT_THEY_SAID]. What's the risk if we ignore it?",
        ),
    ),
    "g3": GauntletSpec(
        "g3",
        "Acknowledged lead becomes shared local context",
        "After acknowledgement, NPC should move to procedural next beats, not re-derive the premise.",
        (
            "What's the real story on [LEAD_TOPIC]?",
            "Understood — I'll treat that as our working assumption. What should we do first?",
            "And if that first step goes wrong, what's our fallback?",
        ),
    ),
    "g4": GauntletSpec(
        "g4",
        "Same lead across NPCs must not bleed continuity",
        "NPC B must not inherit A's private thread state.",
        (
            "What do you know about [LEAD_TOPIC]?",
            "Thanks — I'm with you. I'll act on that.",
            "What's your take on [LEAD_TOPIC]?",
        ),
    ),
    "g5": GauntletSpec(
        "g5",
        "Off-scene / absent NPC must not steal narration",
        "Present interlocutor should own the reply when topic touches an absent NPC.",
        (
            "Speaking to you directly — what do you make of [TOPIC_TIED_TO_ABSENT_NPC]?",
        ),
    ),
    "g6": GauntletSpec(
        "g6",
        "Follow-up answer must materially differ from prior reply",
        "Follow-up should add actionable detail, not paraphrase turn 1.",
        (
            "What do you know about [LEAD_TOPIC]?",
            "Narrow it down: where exactly should we look first, and what are we avoiding?",
        ),
    ),
    "g7": GauntletSpec(
        "g7",
        "Qualified pursuit to invalid target must fail closed",
        "Named pursuit that cannot resolve must not invent a seamless hop.",
        (
            "I follow the lead to [NONEXISTENT_NPC_OR_PLACE].",
            "No — I mean I go after the lead specifically toward [NONEXISTENT_NPC_OR_PLACE].",
        ),
    ),
    "g8": GauntletSpec(
        "g8",
        "Scene change should prevent stale NPC carryover",
        "New scene should not continue as the old NPC unless they are actually present.",
        (
            "I need everything you have on [LEAD_TOPIC] — hold nothing back.",
            "[Use your build's normal scene-change affordance — travel, exit, or equivalent — "
            "so you are no longer in the same scene as [NPC_OLD].]",
            "What's going on here?",
        ),
    ),
}

ARTIFACTS_DIR = ROOT / "artifacts" / "manual_gauntlets"


def _git_meta() -> tuple[str, str]:
    def _one(args: list[str]) -> str:
        try:
            p = subprocess.run(
                ["git", *args],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            out = (p.stdout or "").strip()
            return out if out else "unknown"
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"

    return _one(["rev-parse", "--abbrev-ref", "HEAD"]), _one(["rev-parse", "HEAD"])


def _md_fence(text: str) -> str:
    body = (text or "").replace("```", "``\u200b`")
    return f"```\n{body}\n```"


def _prompt_line(message: str, default: str) -> str:
    print(message)
    if default:
        print(f"Template (Enter = use verbatim):\n{_md_fence(default)}")
    try:
        raw = input("> ")
    except EOFError:
        return default
    stripped = raw.strip()
    return stripped if stripped else default


def _collect_preset_turns(spec: GauntletSpec) -> list[str]:
    lines: list[str] = []
    total = len(spec.prompt_templates)
    print(f"\n=== {spec.gauntlet_id.upper()} — {spec.label} ===")
    print("Substitute placeholders per docs/manual_gauntlets.md before sending.\n")
    for i, template in enumerate(spec.prompt_templates, start=1):
        text = _prompt_line(f"Turn {i}/{total}", template)
        lines.append(text)
    return lines


def _collect_freeform_turns() -> list[str]:
    print("\n=== Freeform entry ===")
    print("Type player lines. End with a line containing only /end (or EOF).\n")
    lines: list[str] = []
    while True:
        try:
            raw = input("> ")
        except EOFError:
            break
        if raw.strip() == "/end":
            break
        if raw.strip() == "":
            continue
        lines.append(raw)
    return lines


def _run_chat_turn(turn_index: int, player_text: str) -> dict[str, Any]:
    payload = chat(ChatRequest(text=player_text))
    if not isinstance(payload, dict):
        return {
            "turn_index": turn_index,
            "player_text": player_text,
            "ok": False,
            "error": "chat returned non-dict payload",
        }
    if not payload.get("ok"):
        return {
            "turn_index": turn_index,
            "player_text": player_text,
            "ok": False,
            "error": str(payload.get("error") or "unknown error"),
            "payload_excerpt": {
                "session_active_scene_id": (
                    (payload.get("session") or {}).get("active_scene_id")
                    if isinstance(payload.get("session"), dict)
                    else None
                ),
            },
        }
    snap = snapshot_from_chat_payload(turn_index, player_text, payload)
    sess = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    snap["active_scene_id"] = str(sess.get("active_scene_id") or "").strip() or None
    snap["ok"] = True
    return snap


def _format_turn_markdown(record: dict[str, Any]) -> str:
    t = record.get("turn_index", 0) + 1
    player = str(record.get("player_text") or "")
    parts = [f"### Turn {t}", "", f"**Player:**", _md_fence(player), ""]
    if not record.get("ok"):
        parts.append(f"**Engine error:** `{record.get('error')}`")
        ex = record.get("payload_excerpt")
        if isinstance(ex, dict) and ex.get("session_active_scene_id"):
            parts.append("")
            parts.append(f"- session `active_scene_id`: `{ex.get('session_active_scene_id')}`")
        parts.append("")
        return "\n".join(parts)

    gm = str(record.get("gm_text") or "")
    parts.extend([f"**GM (player-facing):**", _md_fence(gm), ""])
    parts.append(f"- `scene_id` (envelope): `{record.get('scene_id')}`")
    parts.append(f"- `session.active_scene_id`: `{record.get('active_scene_id')}`")
    parts.append(f"- `current_interlocutor`: `{record.get('current_interlocutor')}`")
    tgt = latest_target_id(record)
    src = latest_target_source(record)
    parts.append(f"- resolved target: `{tgt}` (source: {src})")
    ic = record.get("interaction_context") if isinstance(record.get("interaction_context"), dict) else {}
    ic_slim = {
        k: ic.get(k)
        for k in (
            "active_interaction_target_id",
            "interaction_mode",
            "active_interaction_kind",
            "engagement_level",
        )
    }
    if ic_slim:
        parts.append("- interaction_context (subset):")
        parts.append(_md_fence(json.dumps(ic_slim, indent=2, sort_keys=True)))
    dbg = record.get("debug") if isinstance(record.get("debug"), dict) else {}
    compact = dbg.get("resolution_compact")
    if compact:
        parts.append("- routing (compact resolution):")
        parts.append(_md_fence(json.dumps(compact, indent=2, sort_keys=True)))
    soc = record.get("social_resolution")
    if isinstance(soc, dict) and soc:
        slim = {k: soc[k] for k in ("target_id", "npc_id", "offscene_target", "resolved_target_id") if k in soc}
        if slim:
            parts.append("- social resolution (subset):")
            parts.append(_md_fence(json.dumps(slim, indent=2, sort_keys=True)))
    parts.append("")
    return "\n".join(parts)


def _write_transcript(
    path: Path,
    *,
    spec: GauntletSpec,
    freeform: bool,
    reset_applied: bool,
    records: list[dict[str, Any]],
) -> None:
    branch, commit = _git_meta()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Manual gauntlet transcript — {spec.gauntlet_id}",
        "",
        f"- **Started:** {started}",
        f"- **Git branch:** `{branch}`",
        f"- **Git commit:** `{commit}`",
        f"- **Label:** {spec.label}",
        f"- **Mode:** {'freeform' if freeform else 'preset templates'}",
        f"- **Hard reset before run:** {'yes' if reset_applied else 'no'}",
        "",
        "## Summary",
        "",
        spec.description,
        "",
        "> Full scenario, rubric, and failure modes: `docs/manual_gauntlets.md`.",
        "",
        "## Turns",
        "",
    ]
    for rec in records:
        lines.append(_format_turn_markdown(rec))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote transcript: {path}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run a manual gauntlet (G1–G8) through the real chat pipeline and save a Markdown transcript."
        ),
        epilog="Canonical definitions: docs/manual_gauntlets.md",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="Print gauntlet ids, labels, and template turn counts, then exit.",
    )
    p.add_argument(
        "--gauntlet",
        choices=sorted(GAUNTLETS.keys()),
        metavar="ID",
        help="Gauntlet id (g1 … g8). Required unless --list.",
    )
    p.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip apply_new_campaign_hard_reset() before the run (default: reset).",
    )
    p.add_argument(
        "--freeform",
        action="store_true",
        help="Type arbitrary player lines instead of stepping through preset templates.",
    )
    return p


def main() -> int:
    args = _build_parser().parse_args()
    if args.list:
        for gid in sorted(GAUNTLETS.keys()):
            g = GAUNTLETS[gid]
            n = len(g.prompt_templates)
            print(f"{gid}: {g.label} ({n} template line{'s' if n != 1 else ''})")
        return 0

    if not args.gauntlet:
        print("error: --gauntlet is required unless using --list", file=sys.stderr)
        return 2

    spec = GAUNTLETS[args.gauntlet]
    reset_applied = False
    if not args.no_reset:
        meta = apply_new_campaign_hard_reset()
        reset_applied = True
        rid = meta.get("campaign_run_id") if isinstance(meta, dict) else None
        print(f"Hard reset applied (campaign_run_id={rid!r}).")

    if args.freeform:
        turns = _collect_freeform_turns()
    else:
        turns = _collect_preset_turns(spec)

    if not turns:
        print("No turns entered; nothing to run.")
        return 1

    records: list[dict[str, Any]] = []
    for i, text in enumerate(turns):
        print(f"\n--- Sending turn {i + 1}/{len(turns)} ---")
        rec = _run_chat_turn(i, text)
        records.append(rec)
        if rec.get("ok"):
            gm_preview = str(rec.get("gm_text") or "")
            one_line = " ".join(gm_preview.split())
            if len(one_line) > 160:
                one_line = one_line[:157] + "..."
            print(f"GM: {one_line}")
        else:
            print(f"Error: {rec.get('error')}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = ARTIFACTS_DIR / f"{spec.gauntlet_id}_{stamp}.md"
    _write_transcript(
        out,
        spec=spec,
        freeform=bool(args.freeform),
        reset_applied=reset_applied,
        records=records,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
