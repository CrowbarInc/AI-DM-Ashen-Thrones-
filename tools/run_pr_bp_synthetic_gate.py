#!/usr/bin/env python3
"""Run PR-BP synthetic playtest gate through the real ``/api/chat`` path.

The player policy uses only player-visible transcript text and persona agenda.
Evaluator output and runtime diagnostics are recorded after each action, but are
not fed back into the next player choice.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from game.api import app  # noqa: E402
from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
    _resolution_kind,
    _session_debug_traces,
)


@dataclass(frozen=True)
class Persona:
    persona_id: str
    tendency: str
    objective: str
    prompts: tuple[str, ...]


PERSONAS: tuple[Persona, ...] = (
    Persona(
        "goal_oriented",
        "goal-oriented",
        "Find a practical path into town, useful authority, work, and shelter.",
        (
            "I take in the gate and look for the most official person nearby.",
            "Who seems to be in charge here?",
            "I approach that person and ask what I need to do to enter safely.",
            "Where could a newcomer find honest work tonight?",
            "I ask for a concrete next step, not a general warning.",
            "I look for posted notices or instructions that might help.",
            "I read the most relevant notice closely.",
            "I ask where I can sleep without causing trouble.",
            "I follow the best lead toward shelter or work.",
            "Before moving on, I confirm what I should do first.",
        ),
    ),
    Persona(
        "curious_explorer",
        "curious/exploratory",
        "Investigate visible details, incidental objects, and mundane local color.",
        (
            "I slowly scan the scene for an odd but harmless detail worth inspecting.",
            "What does the most distinctive visible object look like up close?",
            "I ask someone nearby what that detail usually means around here.",
            "What ordinary sounds and smells stand out where I am?",
            "I inspect a nearby door, sign, stall, or fixture without forcing it.",
            "What can I learn from its wear, marks, or use?",
            "I ask a local for a small piece of everyday advice.",
            "Who told you that?",
            "I compare that answer with what I can see around me.",
            "I choose the most plausible next place to examine.",
        ),
    ),
    Persona(
        "social_persistent",
        "social persistent",
        "Talk naturally, follow up on claims, and persist once when answers are incomplete.",
        (
            "I greet the nearest approachable local and ask what people are worried about today.",
            "What have you heard lately that a traveler should know?",
            "Who told you that?",
            "How certain are you, and who would know more?",
            "Can you introduce me or point me to them?",
            "If you cannot help directly, what is one useful thing you can do?",
            "I ask about food, lodging, or a safe place to wait.",
            "What does that place look like from here?",
            "I thank them and ask for one final warning before I move.",
            "I act on the most concrete lead they gave me.",
        ),
    ),
    Persona(
        "mundane_actor",
        "mundane physical/action",
        "Test everyday physical affordances, safe movement, and action resolution without forcing success.",
        (
            "I look for a door, gate, stall, or posted route that seems usable.",
            "I try the most ordinary non-destructive way to use it.",
            "If it does not work, I ask the nearest person what I should do instead.",
            "Can they point me to someone who can help?",
            "I inspect the suggested place or object before touching it.",
            "I take the next safe step they suggested.",
            "What changes around me when I do that?",
            "I ask whether there is a risk I should avoid.",
            "I choose a cautious route forward.",
            "I confirm the immediate next action before I move on.",
        ),
    ),
)


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _bounded_counts(session: Mapping[str, Any] | None) -> dict[str, Any]:
    ledger = session.get("bounded_improvisation") if isinstance(session, Mapping) else None
    ledger = ledger if isinstance(ledger, Mapping) else {}
    entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
    rejected = ledger.get("rejected") if isinstance(ledger.get("rejected"), list) else []
    claims = [e for e in entries if isinstance(e, Mapping) and e.get("kind") == "npc_claim"]
    incidentals = [e for e in entries if isinstance(e, Mapping) and e.get("kind") == "incidental_fact"]
    return {
        "entries": len(entries),
        "incidentals": len(incidentals),
        "npc_claims": len(claims),
        "rejected": len(rejected),
        "latest": entries[-3:] if len(entries) >= 1 else [],
    }


def _fallback_family(gm_output: Mapping[str, Any]) -> str:
    fem = gm_output.get("_final_emission_meta") if isinstance(gm_output.get("_final_emission_meta"), Mapping) else {}
    for key in ("final_emitted_source", "final_route", "fallback_family", "final_emission_route"):
        value = fem.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _visible_next_prompt(
    persona: Persona,
    turn_index: int,
    prior_visible: str,
    *,
    nonanswer_streak: int = 0,
) -> str:
    base = persona.prompts[turn_index]
    if turn_index == 0:
        return base
    low = prior_visible.lower()
    nonanswer = bool(
        re.search(
            r"\b(do not know enough|can't answer|cannot answer|nothing new|look again|not something i can say)\b",
            low,
        )
    )
    if nonanswer and nonanswer_streak < 2:
        if persona.persona_id == "social_persistent":
            return "I press once, politely: who exactly can answer this, or what can you do for me right now?"
        if persona.persona_id == "curious_explorer":
            return "I rephrase and focus on what I can directly see: give me one concrete visible detail."
        if persona.persona_id == "mundane_actor":
            return "I stop and ask for a clear yes, no, condition, or safer next step."
        return "I ask for one concrete next step I can act on immediately."
    return base


def run_persona(persona: Persona, *, client: TestClient, turns: int) -> dict[str, Any]:
    apply_new_campaign_hard_reset()
    prior_player = ""
    prior_gm = ""
    nonanswer_streak = 0
    out_turns: list[dict[str, Any]] = []
    for idx in range(turns):
        player_text = _visible_next_prompt(
            persona,
            min(idx, len(persona.prompts) - 1),
            prior_gm,
            nonanswer_streak=nonanswer_streak,
        )
        payload = client.post("/api/chat", json={"text": player_text}).json()
        gm_text = _gm_text_from_chat_payload(payload)
        gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), Mapping) else {}
        resolution = payload.get("resolution") if isinstance(payload.get("resolution"), Mapping) else {}
        resolution_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), Mapping) else {}
        evaluation = evaluate_playability(
            _build_eval_payload(
                player_prompt=player_text,
                gm_text=gm_text,
                prior_player=prior_player,
                prior_gm=prior_gm,
                debug_traces=_session_debug_traces(payload),
                gm_output=gm_output,
                resolution_contract=(
                    dict(resolution_meta.get("resolution_contract"))
                    if isinstance(resolution_meta.get("resolution_contract"), Mapping)
                    else None
                ),
            )
        )
        session = payload.get("session") if isinstance(payload.get("session"), Mapping) else {}
        out_turns.append(
            {
                "turn_index": idx,
                "player_text": player_text,
                "player_visible_basis": {"prior_player": prior_player, "prior_gm": prior_gm},
                "gm_text": gm_text,
                "api_ok": bool(payload.get("ok")),
                "api_error": payload.get("error"),
                "resolution_kind": _resolution_kind(payload),
                "semantic_result": evaluation.get("semantic_result"),
                "mandatory_gates": evaluation.get("mandatory_gates"),
                "playability_eval": evaluation,
                "final_emission_meta": _final_emission_meta_from_chat_payload(payload),
                "fallback_family": _fallback_family(gm_output),
                "interaction_obligation": (
                    dict(resolution_meta.get("interaction_obligation"))
                    if isinstance(resolution_meta.get("interaction_obligation"), Mapping)
                    else {}
                ),
                "resolution_contract": (
                    dict(resolution_meta.get("resolution_contract"))
                    if isinstance(resolution_meta.get("resolution_contract"), Mapping)
                    else {}
                ),
                "resolution": dict(resolution),
                "last_action_debug": (
                    dict(session.get("last_action_debug"))
                    if isinstance(session.get("last_action_debug"), Mapping)
                    else {}
                ),
                "runtime_traces": _session_debug_traces(payload),
                "bounded_improvisation": _bounded_counts(session),
            }
        )
        if re.search(
            r"\b(do not know enough|can't answer|cannot answer|nothing new|look again|not something i can say|"
            r"murmur around you never tightens|moment passes without anyone stepping forward)\b",
            gm_text.lower(),
        ):
            nonanswer_streak += 1
        else:
            nonanswer_streak = 0
        prior_player = player_text
        prior_gm = gm_text
    return {
        "persona_id": persona.persona_id,
        "tendency": persona.tendency,
        "objective": persona.objective,
        "turn_count": len(out_turns),
        "turns": out_turns,
    }


def summarize(runs: list[Mapping[str, Any]]) -> dict[str, Any]:
    all_turns = [t for run in runs for t in (run.get("turns") or []) if isinstance(t, Mapping)]
    failures = [t for t in all_turns if t.get("semantic_result") in {"FAIL", "INVALID_RUN", "UNCHECKED"}]
    fallback_repeats = 0
    for run in runs:
        last = ""
        last_text = ""
        streak = 0
        text_streak = 0
        for turn in run.get("turns") or []:
            family = str((turn or {}).get("fallback_family") or "")
            if family and family == last:
                streak += 1
            else:
                streak = 1
                last = family
            if family and streak >= 2:
                fallback_repeats += 1
            gm_text = str((turn or {}).get("gm_text") or "").strip().lower()
            if gm_text and gm_text == last_text:
                text_streak += 1
            else:
                text_streak = 1
                last_text = gm_text
            if gm_text and text_streak >= 2:
                fallback_repeats += 1
    final_counts = [_bounded_counts({"bounded_improvisation": {}})]
    bounded_entries = sum(int((t.get("bounded_improvisation") or {}).get("entries") or 0) for t in all_turns)
    npc_claim_turns = sum(1 for t in all_turns if int((t.get("bounded_improvisation") or {}).get("npc_claims") or 0) > 0)
    incidental_turns = sum(1 for t in all_turns if int((t.get("bounded_improvisation") or {}).get("incidentals") or 0) > 0)
    gate_passed = (
        bool(runs)
        and not failures
        and fallback_repeats == 0
        and incidental_turns > 0
        and npc_claim_turns > 0
    )
    return {
        "total_sessions": len(runs),
        "total_turns": len(all_turns),
        "semantic_failures": len(failures),
        "fallback_repeat_flags": fallback_repeats,
        "bounded_entry_turn_sum": bounded_entries,
        "turns_with_incidental_entries": incidental_turns,
        "turns_with_npc_claim_entries": npc_claim_turns,
        "synthetic_gate_passed": gate_passed,
        "human_playtest_recommended": gate_passed,
        "failure_refs": [
            {
                "persona_id": next((r.get("persona_id") for r in runs if t in (r.get("turns") or [])), None),
                "turn_index": t.get("turn_index"),
                "semantic_result": t.get("semantic_result"),
            }
            for t in failures
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=10)
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts" / "pr_bp_synthetic_gate")
    args = parser.parse_args(argv)
    stamp = _utc_slug()
    out_dir = args.artifact_dir / stamp
    with TestClient(app) as client:
        runs = [run_persona(persona, client=client, turns=max(1, int(args.turns))) for persona in PERSONAS]
    for run in runs:
        run_dir = out_dir / str(run["persona_id"])
        _write_json(run_dir / "run.json", run)
        transcript = [f"# {run['persona_id']}", "", f"Objective: {run['objective']}", ""]
        for turn in run["turns"]:
            transcript.extend(
                [
                    f"## Turn {int(turn['turn_index']) + 1}",
                    "",
                    f"Player: {turn['player_text']}",
                    "",
                    f"GM: {turn['gm_text']}",
                    "",
                    f"Semantic: `{turn['semantic_result']}`",
                    "",
                    f"Bounded: `{json.dumps(turn['bounded_improvisation'], ensure_ascii=False)}`",
                    "",
                ]
            )
        (run_dir / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    summary = summarize(runs)
    summary["campaign_id"] = stamp
    summary["run_paths"] = [str((out_dir / str(run["persona_id"]) / "run.json").resolve()) for run in runs]
    _write_json(out_dir / "campaign_summary.json", summary)
    (out_dir / "campaign_summary.md").write_text(
        "# PR-BP Synthetic Gate\n\n```json\n" + json.dumps(summary, indent=2, ensure_ascii=False) + "\n```\n",
        encoding="utf-8",
    )
    print(str(out_dir.resolve()))
    return 0 if summary["synthetic_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
