#!/usr/bin/env python3
"""BV3E — extract and classify ambiguous_entity_reference observe turns."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_referential_clarity import (  # noqa: E402
    _violations_eligible_for_bv3e_exact_alias_introducer_repair,
    _violations_eligible_for_non_strict_local_pronoun_repair,
    _violations_eligible_for_non_strict_local_repair,
)
from game.narration_visibility import validate_player_facing_referential_clarity  # noqa: E402
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402

OUTPUT_JSON = ROOT / "artifacts" / "bv3e_violation_clusters.json"


def _cluster_shape(row: dict[str, Any]) -> str:
    kinds = row.get("violation_kinds") or []
    tokens = row.get("violation_tokens") or []
    count = int(row.get("violation_count") or 0)
    if count > 1:
        return "multi_violation"
    if not tokens:
        return "mixed_ambiguity"
    token = str(tokens[0]).lower()
    if token in {"he", "she", "him", "her", "they", "them"}:
        return "ambiguous_speaker"
    if token in {"his", "her", "their", "its"}:
        return "ambiguous_ownership"
    if token in {"guard", "runner", "watch", "serjeant", "sergeant", "watcher"}:
        return "ambiguous_target"
    if "referent_drift" in kinds:
        return "referent_drift"
    return "mixed_ambiguity"


def _live_violations(turn: dict[str, Any]) -> list[dict[str, Any]]:
    fem = turn["meta"]["final_emission_meta"]
    text = str(fem.get("final_text_preview") or "").strip()
    if not text:
        return []
    session = turn.get("session")
    scene = turn.get("scene")
    world = turn.get("world")
    if not isinstance(session, dict) or not isinstance(scene, dict) or not isinstance(world, dict):
        return []
    validation = validate_player_facing_referential_clarity(
        text, session=session, scene=scene, world=world
    )
    return validation.get("violations") if isinstance(validation.get("violations"), list) else []


def build_inventory() -> dict[str, Any]:
    turns, fem_count, _hits = scan_measurement_fem_turns(include_hits=False)
    observe = [t for t in turns if t.get("route_kind") == "observe"]
    rows: list[dict[str, Any]] = []
    clusters: dict[str, list[str]] = defaultdict(list)

    for index, turn in enumerate(observe, start=1):
        fem = turn["meta"]["final_emission_meta"]
        sample = fem.get("referential_clarity_violation_sample") or []
        kinds = fem.get("referential_clarity_violation_kinds") or []
        if "ambiguous_entity_reference" not in kinds and not any(
            isinstance(v, dict) and v.get("kind") == "ambiguous_entity_reference" for v in sample
        ):
            continue
        live = _live_violations(turn)
        violation_kinds = [
            str(v.get("kind") or "")
            for v in (live or sample)
            if isinstance(v, dict) and str(v.get("kind") or "").strip()
        ]
        violation_tokens = [
            str(v.get("token") or "")
            for v in (live or sample)
            if isinstance(v, dict) and str(v.get("kind") or "").strip() == "ambiguous_entity_reference"
        ]
        row = {
            "turn_id": f"OBS-M{index:03d}",
            "artifact": (turn.get("_measurement") or {}).get("artifact"),
            "source_class": (turn.get("_measurement") or {}).get("source_class"),
            "violation_count": len(live) if live else int(fem.get("referential_clarity_unrepaired_violation_count") or 0),
            "violation_kinds": violation_kinds,
            "violation_tokens": violation_tokens,
            "bv3a_eligible": _violations_eligible_for_non_strict_local_pronoun_repair(live or sample),
            "bv3e_eligible": _violations_eligible_for_non_strict_local_repair(
                live or sample,
                session=turn.get("session") if isinstance(turn.get("session"), dict) else None,
                scene=turn.get("scene") if isinstance(turn.get("scene"), dict) else None,
                world=turn.get("world") if isinstance(turn.get("world"), dict) else None,
            ),
            "bv3e_alias_introducer_eligible": False,
            "text_preview": (fem.get("final_text_preview") or "")[:120],
        }
        if live:
            row["bv3e_alias_introducer_eligible"] = _violations_eligible_for_bv3e_exact_alias_introducer_repair(
                live,
                session=turn.get("session"),
                scene=turn.get("scene"),
                world=turn.get("world"),
            )
        shape = _cluster_shape(row)
        row["cluster"] = shape
        clusters[shape].append(row["turn_id"])
        rows.append(row)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "canonical_fem_instances": fem_count,
            "observe_turn_count": len(observe),
            "ambiguous_entity_reference_turns": len(rows),
            "cluster_counts": dict(Counter(r["cluster"] for r in rows)),
            "bv3a_eligible_count": sum(1 for r in rows if r["bv3a_eligible"]),
            "bv3e_eligible_count": sum(1 for r in rows if r["bv3e_eligible"]),
            "bv3e_newly_eligible_count": sum(
                1 for r in rows if r["bv3e_eligible"] and not r["bv3a_eligible"]
            ),
        },
        "clusters": {key: values for key, values in sorted(clusters.items())},
        "turns": rows,
    }


def main() -> int:
    report = build_inventory()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
