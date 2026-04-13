#!/usr/bin/env python3
"""Interactive CLI to run manual gauntlets G1–G12 against the real ``game.api.chat`` path.

Full scenarios, rubric, and placeholders live in ``docs/manual_gauntlets.md`` (source of truth).
This script only stores compact labels, one-line intent summaries, and optional template lines
so the operator can substitute ``[PLACEHOLDER]`` values and drive turns from the terminal.

Transcripts are written as Markdown under ``artifacts/manual_gauntlets/``.
A compact JSON report bundle (summary, key events, snippets) is emitted alongside
each run unless disabled; use ``--raw-trace`` for an optional full record dump.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.api import chat  # noqa: E402
from game.api_upstream_preflight import (  # noqa: E402
    get_latest_upstream_api_preflight,
    log_upstream_api_preflight_at_startup,
)
from game.upstream_dependent_run_gate import compute_upstream_dependent_run_gate  # noqa: E402
from game.upstream_dependent_run_gate_presentation import build_upstream_dependent_run_gate_operator  # noqa: E402
from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.dead_turn_report_visibility import (  # noqa: E402
    build_dead_turn_run_report,
    markdown_dead_turn_header_block,
)
from game.models import ChatRequest  # noqa: E402
from tests.helpers.behavioral_gauntlet_eval import evaluate_behavioral_gauntlet  # noqa: E402
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
    axis_tags: tuple[str, ...] = ()


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
    "g9": GauntletSpec(
        "g9",
        "Neutral prompt should not provoke ungrounded hostility",
        "Calm look-around or read-aloud should not meet insults or accusations without grounding.",
        (
            "What do I see at [LOCATION]?",
            "I read the posted notice calmly — what does it actually say?",
        ),
        axis_tags=("neutrality",),
    ),
    "g10": GauntletSpec(
        "g10",
        "Escalation should track player pressure, not jump or flatten",
        "Neutral beats stay non-combat; clear hostility should not be met with fawning compliance alone.",
        (
            "I listen quietly — what can you tell me about the mood here?",
            "I'm done being patient: I curse you and draw steel; this ends now.",
        ),
        axis_tags=("escalation_correctness",),
    ),
    "g11": GauntletSpec(
        "g11",
        "Re-engagement after uncertainty should progress the exchange",
        "After the player narrows scope, GM should add new fiction — not repeat generic clarification.",
        (
            "What rumors matter around [PLACE]?",
            "The [WARD] quarter, last night — be concrete.",
        ),
        axis_tags=("reengagement_quality",),
    ),
    "g12": GauntletSpec(
        "g12",
        "Multi-turn dialogue should remain locally coherent",
        "Adjacent beats should not contradict, tutorial-reset, or drift speaker without a player handoff cue.",
        (
            "What is posted at [GATE_OR_POSTING]?",
            "I acknowledge that — what happens if we ignore it?",
        ),
        axis_tags=("dialogue_coherence",),
    ),
}

ARTIFACTS_DIR = ROOT / "artifacts" / "manual_gauntlets"

REPORT_VERSION = 2

# High-signal key substrings for generic trace walking (schema-tolerant).
_SIGNAL_KEY_RE = re.compile(
    r"(validator|repair|fallback|violation|emission|bridge|continuity|gate|sanitiz|mismatch|coercion)",
    re.IGNORECASE,
)


@dataclass
class RunSummary:
    """Serialization-friendly run header for ``summary.json``."""

    gauntlet_id: str
    label: str
    description: str
    started_utc: str
    git_branch: str
    git_commit: str
    mode: str
    hard_reset_before_run: bool
    turn_count: int
    transcript_path: str
    report_version: int = REPORT_VERSION
    event_count: int = 0
    raw_trace_written: bool = False
    operator_verdict: str | None = None
    operator_notes: str | None = None


@dataclass
class KeyEvent:
    turn: int
    stage: str
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SnippetRecord:
    turn: int
    kind: str
    before: str | None = None
    after: str | None = None
    reason: str | None = None


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _artifact_base_name(spec: GauntletSpec, prefix: str | None = None) -> str:
    if prefix is not None:
        p = str(prefix).strip()
        p = p.replace("\\", "_").replace("/", "_").strip(".")
        if p:
            return p
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}_{spec.gauntlet_id}"


def _safe_get(mapping: Any, *path: str, default: Any = None) -> Any:
    cur: Any = mapping
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _normalize_bool(value: Any) -> bool | None:
    """Coerce common truthy/falsey string forms; return None when unknown."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "1", "yes", "on"):
            return True
        if low in ("false", "0", "no", "off", ""):
            return False
    return None


def _truncate_text(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    if max_chars <= 3:
        return t[:max_chars]
    return t[: max_chars - 3] + "..."


def _record_turn_one_based(record: dict[str, Any]) -> int:
    try:
        idx = int(record.get("turn_index", 0))
    except (TypeError, ValueError):
        idx = 0
    return idx + 1


def _iter_nested_dicts(obj: Any, *, max_depth: int = 10, _depth: int = 0) -> Iterator[dict[str, Any]]:
    if _depth > max_depth:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _iter_nested_dicts(v, max_depth=max_depth, _depth=_depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_nested_dicts(item, max_depth=max_depth, _depth=_depth + 1)


def _slim_details(d: dict[str, Any], *, max_keys: int = 12, max_str: int = 200) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i, (k, v) in enumerate(d.items()):
        if i >= max_keys:
            out["_truncated_keys"] = max(0, len(d) - max_keys)
            break
        if isinstance(v, str):
            out[str(k)] = _truncate_text(v, max_str)
        elif isinstance(v, (bool, int, float)) or v is None:
            out[str(k)] = v
        elif isinstance(v, list):
            out[str(k)] = v[:8] if len(v) > 8 else v
        elif isinstance(v, dict):
            out[str(k)] = _slim_details(v, max_keys=min(8, max_keys), max_str=max_str)
        else:
            out[str(k)] = _truncate_text(str(v), max_str)
    return out


def _scan_emission_debug_events(turn: int, em: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key, raw in em.items():
        ks = str(key)
        low = ks.lower()
        if isinstance(raw, bool):
            if not raw:
                continue
            if low.endswith("_failed") or low.endswith("_violation"):
                st = "failed"
            elif (
                low.endswith("_repaired")
                or low.endswith("_applied")
                or low.endswith("_enforced")
                or low.endswith("_blocked")
                or low.endswith("_replaced")
                or "fallback_applied" in low
                or "violation_before_repair" in low
            ):
                st = "applied"
            else:
                continue
            events.append(
                {
                    "turn": turn,
                    "stage": "emission_debug",
                    "name": ks,
                    "status": st,
                    "details": {"value": True},
                }
            )
            continue
        if isinstance(raw, str) and raw.strip() and raw.strip().lower() not in ("none", "null", ""):
            if low.endswith("_repair_mode") or "fallback" in low or low.endswith("_reason"):
                events.append(
                    {
                        "turn": turn,
                        "stage": "repair" if "repair" in low else "emission_debug",
                        "name": ks,
                        "status": _truncate_text(raw.strip(), 120),
                        "details": {},
                    }
                )
        if isinstance(raw, list) and raw and low.endswith("_reasons"):
            events.append(
                {
                    "turn": turn,
                    "stage": "emission_debug",
                    "name": ks,
                    "status": "raised",
                    "details": _slim_details({"items": raw[:12]}, max_keys=2, max_str=160),
                }
            )
        if ks == "interaction_continuity_repair" and isinstance(raw, dict):
            applied = bool(raw.get("applied"))
            rtype = raw.get("repair_type")
            if applied or rtype:
                events.append(
                    {
                        "turn": turn,
                        "stage": "repair",
                        "name": "interaction_continuity_repair",
                        "status": "applied" if applied else "recorded",
                        "details": _slim_details(
                            {
                                "repair_type": rtype,
                                "violations": raw.get("violations"),
                                "strategy_notes": raw.get("strategy_notes"),
                            },
                            max_keys=6,
                        ),
                    }
                )
        if ks == "interaction_continuity_validation" and isinstance(raw, dict):
            ok = raw.get("ok")
            if ok is False or (raw.get("violations") and isinstance(raw.get("violations"), list)):
                viol = raw.get("violations") if isinstance(raw.get("violations"), list) else []
                events.append(
                    {
                        "turn": turn,
                        "stage": "validator",
                        "name": "interaction_continuity_validation",
                        "status": "failed" if ok is False else "checked",
                        "details": _slim_details({"violations": viol[:12]}, max_keys=3),
                    }
                )
        if ks == "interaction_continuity_speaker_binding_bridge" and isinstance(raw, dict):
            if raw.get("applied") or raw.get("bridge_applied"):
                events.append(
                    {
                        "turn": turn,
                        "stage": "bridge",
                        "name": "interaction_continuity_speaker_binding_bridge",
                        "status": "applied",
                        "details": _slim_details(raw, max_keys=8),
                    }
                )
        if ks == "interaction_continuity_enforced" and raw is True:
            events.append(
                {
                    "turn": turn,
                    "stage": "emission",
                    "name": "interaction_continuity_enforced",
                    "status": "true",
                    "details": {},
                }
            )
    return events


def _events_from_last_action_debug(turn: int, lad: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if bool(lad.get("narration_state_mismatch_detected")):
        out.append(
            {
                "turn": turn,
                "stage": "narration_state",
                "name": "narration_state_mismatch",
                "status": "detected",
                "details": _slim_details(
                    {
                        "mismatch_kind": lad.get("mismatch_kind"),
                        "mismatch_repair_applied": lad.get("mismatch_repair_applied"),
                        "mismatch_repairs_applied": lad.get("mismatch_repairs_applied"),
                    },
                    max_keys=5,
                ),
            }
        )
    if bool(lad.get("minimum_actionable_lead_enforced")):
        out.append(
            {
                "turn": turn,
                "stage": "lead",
                "name": "minimum_actionable_lead_enforced",
                "status": "applied",
                "details": _slim_details(
                    {
                        "enforced_lead_id": lad.get("enforced_lead_id"),
                        "enforced_lead_source": lad.get("enforced_lead_source"),
                    },
                    max_keys=3,
                ),
            }
        )
    rtc = lad.get("response_type_contract")
    if isinstance(rtc, dict) and rtc:
        out.append(
            {
                "turn": turn,
                "stage": "emission_gate",
                "name": "response_type_contract",
                "status": "resolved",
                "details": _slim_details(rtc, max_keys=10),
            }
        )
    return out


def _events_from_turn_trace(turn: int, tt: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    intent = _safe_get(tt, "intent", "implied_context", default={}) or {}
    if isinstance(intent, dict) and intent.get("commitment_broken"):
        out.append(
            {
                "turn": turn,
                "stage": "intent",
                "name": "implied_context_commitment_broken",
                "status": "true",
                "details": _slim_details(
                    {
                        "break_reason": intent.get("break_reason"),
                        "target_id": intent.get("target_id"),
                    },
                    max_keys=4,
                ),
            }
        )
    rtc = tt.get("response_type_contract")
    if isinstance(rtc, dict) and rtc:
        out.append(
            {
                "turn": turn,
                "stage": "emission_gate",
                "name": "turn_trace.response_type_contract",
                "status": "resolved",
                "details": _slim_details(rtc, max_keys=10),
            }
        )
    return out


def _generic_signal_events_from_obj(turn: int, root: Any, *, max_hits: int = 24) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for d in _iter_nested_dicts(root, max_depth=9):
        if len(hits) >= max_hits:
            break
        for k, v in d.items():
            if len(hits) >= max_hits:
                break
            ks = str(k)
            if not _SIGNAL_KEY_RE.search(ks):
                continue
            if isinstance(v, bool) and v:
                hits.append(
                    {
                        "turn": turn,
                        "stage": "trace_signal",
                        "name": ks,
                        "status": "true",
                        "details": {},
                    }
                )
            elif isinstance(v, str) and v.strip() and len(v) < 220:
                if v.strip().lower() in ("none", "null"):
                    continue
                hits.append(
                    {
                        "turn": turn,
                        "stage": "trace_signal",
                        "name": ks,
                        "status": _truncate_text(v.strip(), 120),
                        "details": {},
                    }
                )
    return hits


def _extract_candidate_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for rec in records:
        turn = _record_turn_one_based(rec)
        dbg = rec.get("debug") if isinstance(rec.get("debug"), dict) else {}
        lad = dbg.get("last_action_debug") if isinstance(dbg.get("last_action_debug"), dict) else {}
        candidates.extend(_events_from_last_action_debug(turn, lad))

        trace = dbg.get("last_debug_trace")
        if isinstance(trace, dict):
            res = trace.get("resolution")
            if isinstance(res, dict):
                md = res.get("metadata")
                if isinstance(md, dict):
                    em = md.get("emission_debug")
                    if isinstance(em, dict):
                        candidates.extend(_scan_emission_debug_events(turn, em))
            tt = trace.get("turn_trace")
            if isinstance(tt, dict):
                candidates.extend(_events_from_turn_trace(turn, tt))
            candidates.extend(_generic_signal_events_from_obj(turn, trace, max_hits=20))

        if not rec.get("ok"):
            candidates.append(
                {
                    "turn": turn,
                    "stage": "engine",
                    "name": "chat_error",
                    "status": "error",
                    "details": _slim_details({"error": rec.get("error")}, max_keys=2, max_str=300),
                }
            )

    return candidates


def _event_fingerprint(ev: dict[str, Any]) -> tuple[Any, ...]:
    return (
        ev.get("turn"),
        ev.get("stage"),
        ev.get("name"),
        ev.get("status"),
        json.dumps(ev.get("details") or {}, sort_keys=True, default=str),
    )


def _collapse_key_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = _extract_candidate_events(records)
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for ev in candidates:
        fp = _event_fingerprint(ev)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(ev)
    return out


def _serialize_key_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ev in _collapse_key_events(records):
        out.append(
            asdict(
                KeyEvent(
                    turn=int(ev.get("turn") or 0),
                    stage=str(ev.get("stage") or ""),
                    name=str(ev.get("name") or ""),
                    status=str(ev.get("status") or ""),
                    details=dict(ev.get("details") or {}),
                )
            )
        )
    return out


def _behavioral_turn_rows_from_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape per-turn records for ``evaluate_behavioral_gauntlet`` (D2 Layer A preferred).

    Input rows are already chat snapshot dicts (D2 Layer B compatible); we still emit
    compact simplified rows when possible so sparse/minimal paths match smoke tests.
    """
    rows: list[dict[str, Any]] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        try:
            player = str(rec.get("player_text") or "").strip()
            ok = bool(rec.get("ok", True))
            gm = str(rec.get("gm_text") or "").strip()
            if not ok:
                gm = gm or ""

            dbg = rec.get("debug") if isinstance(rec.get("debug"), dict) else {}
            rc_compact = dbg.get("resolution_compact") if isinstance(dbg.get("resolution_compact"), dict) else {}
            rk_raw = rc_compact.get("kind")
            resolution_kind = str(rk_raw).strip() if rk_raw is not None and str(rk_raw).strip() else None

            sc = rec.get("scene_id")
            scene_id = str(sc).strip() if sc is not None and str(sc).strip() else None

            sid_src = latest_target_id(rec) or rec.get("current_interlocutor")
            speaker_id = str(sid_src).strip() if sid_src is not None and str(sid_src).strip() else None

            ti = rec.get("turn_index")
            metadata: dict[str, Any] = {"ok": ok}
            if ti is not None:
                metadata["turn_index"] = ti

            row_out: dict[str, Any] = {
                "player_text": player,
                "gm_text": gm,
                "resolution_kind": resolution_kind,
                "speaker_id": speaker_id,
                "scene_id": scene_id,
                "metadata": metadata,
            }
            fem = rec.get("_final_emission_meta") if isinstance(rec.get("_final_emission_meta"), dict) else {}
            if fem:
                row_out["_final_emission_meta"] = fem
            rows.append(row_out)
        except Exception:
            rows.append(rec)
    return rows


def try_behavioral_eval_for_run(
    spec: GauntletSpec, records: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, str | None]:
    """Advisory behavioral bundle for ``summary.json``; never raises."""
    try:
        if not records:
            return None, None
        turns = _behavioral_turn_rows_from_records(records)
        if not turns:
            return None, None
        expected_axis: set[str] | None = set(spec.axis_tags) if spec.axis_tags else None
        result = evaluate_behavioral_gauntlet(turns, expected_axis=expected_axis)
        return result, None
    except ValueError as exc:
        return None, f"behavioral_eval axis_tags: {exc}"
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}".strip()
        if len(msg) > 180:
            msg = msg[:177] + "..."
        return None, f"behavioral_eval skipped ({msg})"


def _build_summary(
    spec: GauntletSpec,
    freeform: bool,
    reset_applied: bool,
    records: list[dict[str, Any]],
    *,
    started_utc: str,
    transcript_path: Path,
    raw_trace_written: bool,
    event_count: int,
    operator_verdict: str | None = None,
    operator_notes: str | None = None,
    behavioral_eval: dict[str, Any] | None = None,
    behavioral_eval_warning: str | None = None,
    dead_turn_report: dict[str, Any] | None = None,
    upstream_dependent_run_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    branch, commit = _git_meta()
    summary = RunSummary(
        gauntlet_id=spec.gauntlet_id,
        label=spec.label,
        description=spec.description,
        started_utc=started_utc,
        git_branch=branch,
        git_commit=commit,
        mode="freeform" if freeform else "preset templates",
        hard_reset_before_run=reset_applied,
        turn_count=len(records),
        transcript_path=str(transcript_path.resolve()),
        report_version=REPORT_VERSION,
        event_count=event_count,
        raw_trace_written=raw_trace_written,
        operator_verdict=operator_verdict,
        operator_notes=operator_notes,
    )
    out: dict[str, Any] = asdict(summary)
    if spec.axis_tags:
        out["axis_tags"] = list(spec.axis_tags)
    if behavioral_eval is not None:
        out["behavioral_eval"] = behavioral_eval
    if behavioral_eval_warning:
        out["behavioral_eval_warning"] = behavioral_eval_warning
    if dead_turn_report is not None:
        out["dead_turn_report"] = dead_turn_report
    if upstream_dependent_run_gate is not None:
        out["upstream_dependent_run_gate"] = dict(upstream_dependent_run_gate)
        out["upstream_dependent_run_gate_operator"] = build_upstream_dependent_run_gate_operator(
            upstream_dependent_run_gate
        )
    return out


def _extract_snippets(
    records: list[dict[str, Any]],
    *,
    max_items: int = 5,
    max_chars: int = 400,
) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []
    for rec in records:
        if len(snippets) >= max_items:
            break
        turn = _record_turn_one_based(rec)
        dbg = rec.get("debug") if isinstance(rec.get("debug"), dict) else {}
        trace = dbg.get("last_debug_trace")
        em: dict[str, Any] | None = None
        if isinstance(trace, dict):
            res = trace.get("resolution")
            if isinstance(res, dict):
                md = res.get("metadata")
                if isinstance(md, dict):
                    hit = md.get("emission_debug")
                    if isinstance(hit, dict):
                        em = hit
        if em:
            ic_rep = em.get("interaction_continuity_repair")
            if isinstance(ic_rep, dict) and (ic_rep.get("applied") or ic_rep.get("repair_type")):
                gm_final = str(rec.get("gm_text") or "")
                before_t = ic_rep.get("input_text") or ic_rep.get("candidate_text") or ic_rep.get("pre_repair_text")
                after_t = ic_rep.get("repaired_text") or gm_final
                b = _truncate_text(str(before_t), max_chars) if before_t else None
                a = _truncate_text(str(after_t), max_chars) if after_t else None
                reason = str(ic_rep.get("repair_type") or "interaction_continuity_repair")
                notes = ic_rep.get("strategy_notes") if isinstance(ic_rep.get("strategy_notes"), list) else []
                if notes:
                    reason = f"{reason}: {_truncate_text('; '.join(str(x) for x in notes[:3]), 200)}"
                snippets.append(
                    asdict(
                        SnippetRecord(
                            turn=turn,
                            kind="repair_before_after",
                            before=b,
                            after=a,
                            reason=reason,
                        )
                    )
                )
                continue

        if not rec.get("ok"):
            err = str(rec.get("error") or "")
            snippets.append(
                asdict(
                    SnippetRecord(
                        turn=turn,
                        kind="engine_error",
                        before=None,
                        after=None,
                        reason=_truncate_text(err, max_chars),
                    )
                )
            )
            continue

        if isinstance(trace, dict):
            res = trace.get("resolution")
            md = res.get("metadata") if isinstance(res, dict) and isinstance(res.get("metadata"), dict) else {}
            em2 = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
            if em2.get("social_emission_integrity_replaced") or (
                str(em2.get("social_emission_integrity_fallback_kind") or "").strip()
            ):
                gm_t = _truncate_text(str(rec.get("gm_text") or ""), max_chars)
                snippets.append(
                    asdict(
                        SnippetRecord(
                            turn=turn,
                            kind="fallback_response",
                            before=None,
                            after=gm_t,
                            reason=_truncate_text(
                                str(em2.get("social_emission_integrity_fallback_kind") or "social_emission_integrity"),
                                200,
                            ),
                        )
                    )
                )
                continue

        gm = str(rec.get("gm_text") or "")
        if _suspicious_speaker_fragment(gm):
            snippets.append(
                asdict(
                    SnippetRecord(
                        turn=turn,
                        kind="suspicious_speaker_fragment",
                        before=None,
                        after=_truncate_text(gm, max_chars),
                        reason="Possible malformed speaker / quote pattern in player-facing text",
                    )
                )
            )

    return snippets[:max_items]


def _suspicious_speaker_fragment(text: str) -> bool:
    if not text or len(text) < 12:
        return False
    # Heuristic: multiple quoted segments with different capitalized labels (lightweight).
    if text.count('"') >= 4 and re.search(r"\b(says|said|asks|replies)\b", text, re.I):
        return True
    if re.search(r'[A-Za-z][^.!?"]{0,40}says,\s*"[A-Za-z][^.!?"]{0,40}says,', text):
        return True
    return False


def _sanitize_raw_trace_payload(obj: Any, *, max_str: int = 12000) -> Any:
    if isinstance(obj, dict):
        return {str(k): _sanitize_raw_trace_payload(v, max_str=max_str) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_raw_trace_payload(x, max_str=max_str) for x in obj]
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + f"...(truncated {len(obj) - max_str} chars)"
    return obj


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
    fem_dt = record.get("_final_emission_meta") if isinstance(record.get("_final_emission_meta"), dict) else {}
    dead = fem_dt.get("dead_turn") if isinstance(fem_dt.get("dead_turn"), dict) else {}
    if dead.get("is_dead_turn"):
        parts.append("#### Dead turn (test metadata — not player-facing)")
        parts.append(f"- **Class:** `{dead.get('dead_turn_class')}`")
        rc = dead.get("dead_turn_reason_codes")
        if isinstance(rc, list) and rc:
            parts.append(f"- **Reason codes:** `{', '.join(str(x) for x in rc[:16])}`")
        parts.append(f"- **manual_test_valid:** `{dead.get('manual_test_valid')}`")
        parts.append("")
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
    dead_turn_markdown_block: str | None = None,
    upstream_dependent_run_gate: dict[str, Any] | None = None,
) -> None:
    branch, commit = _git_meta()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Manual gauntlet transcript — {spec.gauntlet_id}",
        "",
    ]
    gate_op: dict[str, Any] | None = None
    if upstream_dependent_run_gate:
        gate_op = build_upstream_dependent_run_gate_operator(upstream_dependent_run_gate)
        banner = gate_op.get("compact_banner")
        if isinstance(banner, str) and banner.strip():
            lines.append(f"**{banner.strip()}**")
            lines.append("")
    lines.extend(
        [
            f"- **Started:** {started}",
            f"- **Git branch:** `{branch}`",
            f"- **Git commit:** `{commit}`",
            f"- **Label:** {spec.label}",
            f"- **Mode:** {'freeform' if freeform else 'preset templates'}",
            f"- **Hard reset before run:** {'yes' if reset_applied else 'no'}",
            "",
        ]
    )
    if upstream_dependent_run_gate and gate_op is not None:
        op = gate_op
        disp = op.get("upstream_gate_disposition")
        if disp != "healthy":
            lines.extend(
                [
                    "## Operator upstream gate surface (BHC3)",
                    "",
                    _md_fence(json.dumps(op, indent=2, sort_keys=True)),
                    "",
                ]
            )
        lines.extend(
            [
                "## Upstream-dependent run gate (BHC2)",
                "",
                _md_fence(json.dumps(upstream_dependent_run_gate, indent=2, sort_keys=True)),
                "",
            ]
        )
    lines.extend(
        [
            "## Summary",
            "",
            spec.description,
            "",
            "> Full scenario, rubric, and failure modes: `docs/manual_gauntlets.md`.",
            "",
        ]
    )
    if dead_turn_markdown_block:
        lines.extend([dead_turn_markdown_block.rstrip(), ""])
    lines.extend(
        [
            "## Turns",
            "",
        ]
    )
    for rec in records:
        lines.append(_format_turn_markdown(rec))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_artifact_summary(
    *,
    transcript: Path,
    summary: Path | None,
    key_events: Path | None,
    snippets: Path | None,
    raw_trace: Path | None,
    operator_verdict: str | None = None,
    operator_notes: str | None = None,
    dead_turn_banner: str | None = None,
    upstream_gate_banner: str | None = None,
) -> None:
    print("\n=== Gauntlet artifacts ===")
    if upstream_gate_banner:
        print(f"\n*** {upstream_gate_banner} ***")
        print("(See summary upstream_dependent_run_gate_operator for disposition and action_hint.)\n")
    if dead_turn_banner:
        print(f"\n*** {dead_turn_banner} ***")
        print("(This run is not valid for gameplay-quality conclusions; see summary dead_turn_report.)\n")
    print(f"- transcript:    {transcript.resolve()}")
    if summary is not None:
        print(f"- summary:       {summary.resolve()}")
    if key_events is not None:
        print(f"- key_events:    {key_events.resolve()}")
    if snippets is not None:
        print(f"- snippets:      {snippets.resolve()}")
    if raw_trace is not None:
        print(f"- raw_trace:     {raw_trace.resolve()}")
    if operator_verdict:
        print(f"Verdict: {operator_verdict}")
    if operator_notes:
        print(f"Notes: {operator_notes}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run a manual gauntlet (G1–G12) through the real chat pipeline and save a Markdown transcript."
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
        help="Gauntlet id (g1 … g12). Required unless --list.",
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
    p.add_argument(
        "--report",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Emit summary.json, key_events.json, and snippets.json next to the transcript (default: on).",
    )
    p.add_argument(
        "--raw-trace",
        action="store_true",
        help="Also write raw_trace.json (sanitized full per-turn record dump).",
    )
    p.add_argument(
        "--artifact-prefix",
        default=None,
        metavar="NAME",
        help="Override the timestamp-based artifact basename (files become NAME_transcript.md, etc.).",
    )
    p.add_argument(
        "--verdict",
        default=None,
        metavar="VALUE",
        help="Optional operator verdict (e.g. PASS, FAIL, PARTIAL, or freeform). Non-interactive; no prompt.",
    )
    p.add_argument(
        "--notes",
        default=None,
        metavar="TEXT",
        help="Optional short operator notes for summary.json. Non-interactive; no prompt.",
    )
    return p


def main() -> int:
    args = _build_parser().parse_args()
    if not args.list and get_latest_upstream_api_preflight() is None:
        log_upstream_api_preflight_at_startup()
    if args.list:
        for gid in sorted(GAUNTLETS.keys()):
            g = GAUNTLETS[gid]
            n = len(g.prompt_templates)
            print(f"{gid}: {g.label} ({n} template line{'s' if n != 1 else ''})")
        return 0

    if not args.gauntlet:
        print("error: --gauntlet is required unless using --list", file=sys.stderr)
        return 2

    gate = compute_upstream_dependent_run_gate()
    gate_op = build_upstream_dependent_run_gate_operator(gate)
    if gate.get("manual_testing_blocked"):
        b = gate_op.get("compact_banner")
        if isinstance(b, str) and b.strip():
            print(f"[upstream_dependent_run_gate] {b.strip()}", file=sys.stderr)
        print(f"[upstream_dependent_run_gate] action_hint: {gate_op.get('action_hint')}", file=sys.stderr)
        print(
            "[upstream_dependent_run_gate] Manual gauntlet blocked: cached upstream preflight "
            f"invalidates live narration (health_class={gate.get('preflight_health_class')!r}).",
            file=sys.stderr,
        )
        return 1
    if not gate.get("preflight_available"):
        b = gate_op.get("compact_banner")
        if isinstance(b, str) and b.strip():
            print(f"[upstream_dependent_run_gate] {b.strip()}", file=sys.stderr)
        print(f"[upstream_dependent_run_gate] action_hint: {gate_op.get('action_hint')}", file=sys.stderr)
        print(
            "[upstream_dependent_run_gate] Preflight unavailable — startup_run_valid is false; "
            "do not treat this run as authoritative live-upstream validation "
            f"(block_reason={gate.get('block_reason')!r}).",
            file=sys.stderr,
        )

    spec = GAUNTLETS[args.gauntlet]
    started_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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

    base = _artifact_base_name(spec, args.artifact_prefix)
    transcript_path = ARTIFACTS_DIR / f"{base}_transcript.md"
    dead_turn_report_payload = build_dead_turn_run_report(records)
    dead_md = markdown_dead_turn_header_block(dead_turn_report_payload)
    _write_transcript(
        transcript_path,
        spec=spec,
        freeform=bool(args.freeform),
        reset_applied=reset_applied,
        records=records,
        dead_turn_markdown_block=dead_md,
        upstream_dependent_run_gate=gate,
    )

    summary_path: Path | None = None
    key_events_path: Path | None = None
    snippets_path: Path | None = None
    raw_trace_path: Path | None = None
    raw_written = bool(args.raw_trace)

    key_events_serialized = _serialize_key_events(records)
    event_count = len(key_events_serialized)

    operator_verdict: str | None = None
    operator_notes: str | None = None
    if args.verdict is not None:
        v = str(args.verdict).strip()
        operator_verdict = v if v else None
    elif sys.stdin.isatty():
        try:
            raw_v = input("Enter verdict (PASS / FAIL / PARTIAL / ENTER to skip): ")
        except EOFError:
            raw_v = ""
        v = raw_v.strip()
        operator_verdict = v if v else None
        try:
            raw_n = input("Notes (optional, ENTER to skip): ")
        except EOFError:
            raw_n = ""
        n = raw_n.strip()
        operator_notes = n if n else None
    if args.notes is not None:
        n2 = str(args.notes).strip()
        operator_notes = n2 if n2 else None

    if args.report:
        summary_path = ARTIFACTS_DIR / f"{base}_summary.json"
        key_events_path = ARTIFACTS_DIR / f"{base}_key_events.json"
        snippets_path = ARTIFACTS_DIR / f"{base}_snippets.json"
        be_payload, be_warn = try_behavioral_eval_for_run(spec, records)
        summary_payload = _build_summary(
            spec,
            bool(args.freeform),
            reset_applied,
            records,
            started_utc=started_utc,
            transcript_path=transcript_path,
            raw_trace_written=raw_written,
            event_count=event_count,
            operator_verdict=operator_verdict,
            operator_notes=operator_notes,
            behavioral_eval=be_payload,
            behavioral_eval_warning=be_warn,
            dead_turn_report=dead_turn_report_payload,
            upstream_dependent_run_gate=gate,
        )
        _json_dump(summary_path, summary_payload)
        _json_dump(key_events_path, key_events_serialized)
        _json_dump(snippets_path, _extract_snippets(records))

    if raw_written:
        raw_trace_path = ARTIFACTS_DIR / f"{base}_raw_trace.json"
        _json_dump(
            raw_trace_path,
            {"records": _sanitize_raw_trace_payload(records), "report_version": REPORT_VERSION},
        )

    ug_banner = build_upstream_dependent_run_gate_operator(gate).get("compact_banner")
    ug_banner_s = str(ug_banner).strip() if isinstance(ug_banner, str) else None
    _print_artifact_summary(
        transcript=transcript_path,
        summary=summary_path,
        key_events=key_events_path,
        snippets=snippets_path,
        raw_trace=raw_trace_path if raw_written else None,
        operator_verdict=operator_verdict,
        operator_notes=operator_notes,
        dead_turn_banner=str(dead_turn_report_payload.get("banner") or "").strip() or None,
        upstream_gate_banner=ug_banner_s,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
