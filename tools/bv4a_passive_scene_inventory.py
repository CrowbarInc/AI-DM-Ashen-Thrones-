#!/usr/bin/env python3
"""BV4A — inventory sealed_passive_scene_pressure_fallback events from refreshed corpus."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_non_strict_stack import _reply_already_has_concrete_interaction  # noqa: E402
from game.final_emission_passive_scene_pressure import (  # noqa: E402
    _passive_scene_pressure_due_for_fallback,
    _passive_scene_pressure_fallback_candidates,
)
from game.final_emission_replay_projection import (  # noqa: E402
    project_sealed_replacement_subkind_from_fem,
)
from game.storage import get_scene_runtime  # noqa: E402
from tools.bv3d_measurement_scope import (  # noqa: E402
    MEASUREMENT_ROOTS,
    iter_measurement_artifact_files,
    scan_measurement_fem_turns,
)
from tools.fallback_projection_gap_reality_audit import (  # noqa: E402
    _load_records,
    _relative,
    _route_kind,
    _walk_mappings,
)

OUTPUT_JSON = ROOT / "artifacts" / "bv4a_passive_scene_inventory.json"

_CONCRETE_STUB = re.compile(
    r'Near the checkpoint a guard shifts his weight\. "Keep moving," he says',
    re.IGNORECASE,
)


def _lineage_fallback_events(turn: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in turn["meta"].get("runtime_lineage_events") or []
        if isinstance(event, dict) and event.get("event_kind") == "fallback_selected"
    ]


def _preceding_fallback_family(fem: dict[str, Any], events: list[dict[str, Any]]) -> str | None:
    if fem.get("referential_clarity_replacement_applied") is True:
        return "referential_clarity_hard_replacement"
    if fem.get("referential_clarity_upstream_repair_applied") is True:
        return "referential_clarity_upstream_repair"
    kinds = [str(e.get("fallback_kind") or "") for e in events]
    if "referential_clarity_hard_replacement" in kinds:
        return "referential_clarity_hard_replacement"
    if fem.get("referential_clarity_bv3e_repair_mode"):
        return f"bv3e_{fem.get('referential_clarity_bv3e_repair_mode')}"
    return "upstream_unsatisfied_passive_pressure"


def _triggering_condition(
    *,
    fem: dict[str, Any],
    session: dict[str, Any] | None,
    scene: dict[str, Any] | None,
    scene_id: str,
    upstream_text: str,
) -> dict[str, Any]:
    runtime = get_scene_runtime(session, scene_id) if isinstance(session, dict) and scene_id else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    recent_leads = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    pressure_due = _passive_scene_pressure_due_for_fallback(
        session=session, scene=scene, scene_id=scene_id
    )
    candidates = _passive_scene_pressure_fallback_candidates(
        session=session, scene=scene, scene_id=scene_id
    )
    upstream_concrete = _reply_already_has_concrete_interaction(upstream_text)
    reasons = fem.get("non_strict_layer_stack_reasons") or fem.get("gate_terminal_reasons") or []
    if isinstance(reasons, str):
        reasons = [reasons]
    return {
        "passive_scene_pressure_due": pressure_due,
        "passive_action_streak": passive_streak,
        "last_player_action_passive": last_passive,
        "recent_contextual_leads_count": len(recent_leads) if isinstance(recent_leads, list) else 0,
        "upstream_text_has_concrete_interaction": upstream_concrete,
        "upstream_stub_pattern": bool(_CONCRETE_STUB.search(upstream_text)),
        "passive_candidate_available": bool(candidates),
        "passive_candidate_kind": (
            candidates[0].fallback_kind if candidates else None
        ),
        "non_strict_stack_reasons": list(reasons) if isinstance(reasons, list) else [],
        "missing_concrete_beat_reason": any(
            "passive_scene_pressure_missing_concrete_beat" in str(r) for r in (reasons or [])
        ),
    }


def _classify_trigger(row: dict[str, Any]) -> str:
    cond = row.get("triggering_condition") or {}
    reasons = cond.get("non_strict_stack_reasons") or []
    reason_text = " ".join(str(r) for r in reasons).lower()
    player = str(row.get("player_text") or "").lower()
    if "passive_scene_pressure_missing_concrete_beat" in reason_text:
        if any(token in player for token in ("look around", "watch", "scan", "observe")):
            return "missing_actor_initiative"
        if cond.get("passive_action_streak", 0) >= 2:
            return "stalled_interaction"
        return "unresolved_scene_pressure"
    if "dialogue" in reason_text or "speaker" in reason_text:
        return "dialogue_dead_end"
    if "no_actionable" in reason_text or "no eligible" in reason_text:
        return "no_actionable_participant"
    if cond.get("missing_concrete_beat_reason"):
        if cond.get("passive_action_streak", 0) >= 2:
            return "stalled_interaction"
        return "missing_actor_initiative"
    if not cond.get("upstream_text_has_concrete_interaction"):
        return "missing_actor_initiative"
    return "other"


def _classify_upstream_gap(row: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    cond = row.get("triggering_condition") or {}
    fem = row.get("fem_snapshot") or {}
    reasons = row.get("rejection_reasons_sample") or cond.get("non_strict_stack_reasons") or []
    if not cond.get("upstream_text_has_concrete_interaction"):
        gaps.append("missing_narrative_obligation")
    if any("passive_scene_pressure_missing_concrete_beat" in str(r) for r in reasons):
        gaps.append("missing_contract")
    if cond.get("passive_scene_pressure_due") or any(
        "passive_scene_pressure" in str(r) for r in reasons
    ):
        if "missing_contract" not in gaps:
            gaps.append("missing_contract")
    if cond.get("missing_concrete_beat_reason"):
        gaps.append("missing_initiative_source")
    if fem.get("referential_clarity_upstream_repair_applied") and not fem.get(
        "referential_clarity_replacement_applied"
    ):
        gaps.append("missing_projection")
    if not fem.get("fallback_selection_owner") or row.get("selection_owner") == "game.final_emission_gate":
        gaps.append("missing_ownership_source")
    return sorted(set(gaps)) or ["missing_contract"]


def _upstream_text_from_fem(fem: dict[str, Any], gm: dict[str, Any]) -> str:
    marker = str(fem.get("context_separation_debug_reason_marker") or "")
    if "before_head=" in marker:
        start = marker.index("before_head=") + len("before_head=")
        end = marker.find("';", start)
        if end == -1:
            end = marker.find("';after_head=", start)
        if end == -1:
            end = len(marker)
        snippet = marker[start:end].strip("'\"")
        if snippet:
            return snippet
    for key in ("upstream_text_preview", "pre_gate_text_preview", "gate_candidate_text_preview"):
        value = fem.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(gm.get("text") or gm.get("narration") or "")


def _load_record_context(artifact: str, locator: str) -> dict[str, Any]:
    path = ROOT / artifact.replace("/", "\\") if "\\" not in artifact else ROOT / artifact
    if not path.is_file():
        path = ROOT / artifact
    records, _errors = _load_records(path)
    for record, loc in records:
        if loc != locator:
            continue
        session = record.get("session") if isinstance(record.get("session"), dict) else None
        scene = record.get("scene") if isinstance(record.get("scene"), dict) else None
        world = record.get("world") if isinstance(record.get("world"), dict) else None
        scene_id = str(record.get("scene_id") or (session or {}).get("current_scene_id") or "")
        player_text = str(
            record.get("player_input") or record.get("player_text") or record.get("text") or ""
        )
        gm = record.get("gm_output") if isinstance(record.get("gm_output"), dict) else {}
        fem_lane = (
            (gm.get("internal_state") or {}).get("emission_debug_lane") or {}
            if isinstance(gm.get("internal_state"), dict)
            else {}
        )
        lane_fem = fem_lane.get("_final_emission_meta") if isinstance(fem_lane, dict) else None
        upstream_text = _upstream_text_from_fem(lane_fem or {}, gm)
        rejection_reasons = []
        if isinstance(lane_fem, dict):
            sample = lane_fem.get("rejection_reasons_sample") or lane_fem.get("non_strict_layer_stack_reasons")
            if isinstance(sample, list):
                rejection_reasons = [str(r) for r in sample]
        return {
            "session": session,
            "scene": scene,
            "world": world,
            "scene_id": scene_id,
            "player_text": player_text,
            "upstream_text": upstream_text,
            "rejection_reasons_sample": rejection_reasons,
            "resolution": record.get("resolution"),
            "prompt_index_hint": int(locator.split("[")[1].rstrip("]")) if "$line[" in locator else None,
        }
    return {}


def build_inventory() -> dict[str, Any]:
    turns, fem_count, _hits = scan_measurement_fem_turns(include_hits=False)
    rows: list[dict[str, Any]] = []
    event_index = 0

    for turn in turns:
        fem = turn["meta"]["final_emission_meta"]
        subkind = project_sealed_replacement_subkind_from_fem(fem)
        events = _lineage_fallback_events(turn)
        psp_events = [
            e for e in events if e.get("fallback_kind") == "sealed_passive_scene_pressure_fallback"
        ]
        if subkind != "sealed_passive_scene_pressure_fallback" and not psp_events:
            continue

        event_index += 1
        measurement = turn.get("_measurement") or {}
        ctx = _load_record_context(
            str(measurement.get("artifact") or ""),
            str(measurement.get("locator") or ""),
        )
        scene_id = str(ctx.get("scene_id") or fem.get("scene_id") or "")
        upstream_text = str(ctx.get("upstream_text") or fem.get("upstream_text_preview") or "")
        rejection_sample = list(ctx.get("rejection_reasons_sample") or [])
        triggering = _triggering_condition(
            fem=fem,
            session=ctx.get("session"),
            scene=ctx.get("scene"),
            scene_id=scene_id,
            upstream_text=upstream_text,
        )
        if rejection_sample:
            triggering["non_strict_stack_reasons"] = rejection_sample
            triggering["missing_concrete_beat_reason"] = any(
                "passive_scene_pressure_missing_concrete_beat" in str(r) for r in rejection_sample
            )
        triggering["upstream_text_has_concrete_interaction"] = _reply_already_has_concrete_interaction(
            upstream_text
        )
        fb_event = psp_events[0] if psp_events else (events[0] if events else {})
        emitted = str(fem.get("final_text_preview") or fem.get("final_text") or "")

        row = {
            "event_id": f"PSP-E{event_index:03d}",
            "turn_id": f"OBS-PSP{event_index:03d}",
            "artifact": measurement.get("artifact"),
            "locator": measurement.get("locator"),
            "source_class": measurement.get("source_class"),
            "route": turn.get("route_kind"),
            "owner_bucket": (
                fem.get("fallback_owner_bucket")
                or fem.get("visibility_fallback_owner_bucket")
                or fb_event.get("fallback_owner_bucket")
            ),
            "selection_owner": fem.get("fallback_selection_owner") or fb_event.get("fallback_selection_owner"),
            "content_owner": fem.get("fallback_content_owner") or fb_event.get("fallback_content_owner"),
            "event_owner": fb_event.get("event_owner"),
            "realization_family": fem.get("realization_fallback_family"),
            "preceding_fallback_family": _preceding_fallback_family(fem, events),
            "triggering_condition": triggering,
            "trigger_taxonomy": None,
            "upstream_gaps": None,
            "player_text": str(ctx.get("player_text") or fem.get("player_text_preview") or "")[:120],
            "player_action_class": (
                "passive_observe"
                if any(
                    token in str(ctx.get("player_text") or "").lower()
                    for token in ("look around", "watch", "scan", "observe")
                )
                else "other"
            ),
            "upstream_text_preview": upstream_text[:120],
            "rejection_reasons_sample": rejection_sample,
            "emitted_content_preview": emitted[:200],
            "emitted_content_source": fem.get("final_emitted_source"),
            "passive_candidate_text_preview": (
                _passive_scene_pressure_fallback_candidates(
                    session=ctx.get("session"),
                    scene=ctx.get("scene"),
                    scene_id=scene_id,
                )[0].text[:200]
                if triggering.get("passive_candidate_available")
                else None
            ),
            "fem_snapshot": {
                "referential_clarity_upstream_repair_applied": fem.get(
                    "referential_clarity_upstream_repair_applied"
                ),
                "referential_clarity_bv3e_repair_mode": fem.get("referential_clarity_bv3e_repair_mode"),
                "referential_clarity_unrepaired_violation_count": fem.get(
                    "referential_clarity_unrepaired_violation_count"
                ),
                "referential_clarity_violation_kinds": fem.get("referential_clarity_violation_kinds"),
                "strict_social_active": fem.get("strict_social_active"),
                "final_route": fem.get("final_route"),
            },
        }
        row["trigger_taxonomy"] = _classify_trigger(row)
        row["upstream_gaps"] = _classify_upstream_gap(row)
        rows.append(row)

    trigger_counts = dict(Counter(r["trigger_taxonomy"] for r in rows))
    gap_counts = dict(Counter(g for r in rows for g in r.get("upstream_gaps") or []))
    owner_counts = dict(Counter(r.get("selection_owner") for r in rows))
    route_counts = dict(Counter(r.get("route") for r in rows))
    preceding_counts = dict(Counter(r.get("preceding_fallback_family") for r in rows))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "measurement_scope": "BV3D filtered post-BV3F refresh",
        "summary": {
            "canonical_fem_instances": fem_count,
            "sealed_passive_scene_pressure_fallback_count": len(rows),
            "observe_route_share": round(
                sum(1 for r in rows if r.get("route") == "observe") / len(rows), 4
            )
            if rows
            else None,
            "trigger_taxonomy_counts": trigger_counts,
            "upstream_gap_counts": gap_counts,
            "selection_owner_counts": owner_counts,
            "route_counts": route_counts,
            "preceding_fallback_family_counts": preceding_counts,
            "unique_emitted_content_shapes": len({r.get("emitted_content_preview") for r in rows}),
            "unique_upstream_text_shapes": len({r.get("upstream_text_preview") for r in rows}),
        },
        "events": rows,
    }


def main() -> int:
    report = build_inventory()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
