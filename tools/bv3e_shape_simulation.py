#!/usr/bin/env python3
"""BV3E — simulate eligibility/repair on frozen observe FEM shapes with live world state."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import game.storage as storage  # noqa: E402
from game.defaults import default_scene  # noqa: E402
from game.final_emission_referential_clarity import (  # noqa: E402
    _violations_eligible_for_non_strict_local_pronoun_repair,
    _violations_eligible_for_non_strict_local_repair,
    apply_observe_referential_clarity_upstream_repair,
)
from game.interaction_context import rebuild_active_scene_entities  # noqa: E402
from game.narration_visibility import validate_player_facing_referential_clarity  # noqa: E402
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world  # noqa: E402
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402
from tools.fallback_projection_gap_reality_audit import _load_records  # noqa: E402

OUTPUT_PATH = ROOT / "artifacts" / "bv3e_shape_simulation.json"


def _full_text_for_turn(turn: dict) -> str:
    fem = turn["meta"]["final_emission_meta"]
    preview = str(fem.get("final_text_preview") or "").strip()
    artifact = str((turn.get("_measurement") or {}).get("artifact") or "")
    locator = str((turn.get("_measurement") or {}).get("locator") or "")
    if artifact and locator.startswith("$line["):
        path = ROOT / artifact.replace("/", "\\") if "\\" in str(ROOT) else ROOT / artifact
        if path.is_file():
            try:
                line_no = int(locator.split("[")[1].split("]")[0]) - 1
                records, _errors = _load_records(path)
                if 0 <= line_no < len(records):
                    record = records[line_no][0]
                    gm = record.get("gm_output") if isinstance(record.get("gm_output"), dict) else {}
                    text = str(gm.get("player_facing_text") or "").strip()
                    if text:
                        return text
            except (ValueError, IndexError, TypeError):
                pass
    return preview


def _live_world_bundle():
    seed_frontier_gate_world()
    session = storage.load_session()
    world = storage.load_world()
    sid = "frontier_gate"
    scene = storage.load_scene(sid)
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def simulate() -> dict:
    session, world, scene, sid = _live_world_bundle()
    turns, fem_count, _hits = scan_measurement_fem_turns()
    observe = [t for t in turns if t.get("route_kind") == "observe"]
    rows: list[dict] = []
    bv3a_eligible = 0
    bv3e_eligible = 0
    newly_eligible = 0
    simulated_applied = 0

    for index, turn in enumerate(observe, start=1):
        fem = turn["meta"]["final_emission_meta"]
        text = _full_text_for_turn(turn)
        if not text:
            continue
        validation = validate_player_facing_referential_clarity(
            text, session=session, scene=scene, world=world
        )
        violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
        if not violations:
            continue
        a_ok = _violations_eligible_for_non_strict_local_pronoun_repair(violations)
        e_ok = _violations_eligible_for_non_strict_local_repair(
            violations, session=session, scene=scene, world=world
        )
        if a_ok:
            bv3a_eligible += 1
        if e_ok:
            bv3e_eligible += 1
        if e_ok and not a_ok:
            newly_eligible += 1

        applied = False
        if e_ok:
            out = apply_observe_referential_clarity_upstream_repair(
                {"player_facing_text": text, "tags": []},
                session=session,
                scene=scene,
                world=world,
                scene_id=sid,
                eff_resolution={"kind": "observe"},
                active_interlocutor="",
                res_kind="observe",
                strict_social_active=False,
            )
            meta = final_emission_meta_from_output(out)
            applied = meta.get("referential_clarity_upstream_repair_applied") is True
            if applied:
                simulated_applied += 1

        rows.append(
            {
                "turn_id": f"OBS-M{index:03d}",
                "artifact": (turn.get("_measurement") or {}).get("artifact"),
                "source_class": (turn.get("_measurement") or {}).get("source_class"),
                "violation_count": len(violations),
                "bv3a_eligible": a_ok,
                "bv3e_eligible": e_ok,
                "simulated_upstream_applied": applied,
                "text_preview": text[:120],
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "canonical_fem_instances": fem_count,
            "observe_turn_count": len(observe),
            "live_validation_violation_turns": len(rows),
            "bv3a_eligible_count": bv3a_eligible,
            "bv3e_eligible_count": bv3e_eligible,
            "newly_eligible_turn_count": newly_eligible,
            "simulated_upstream_applied_count": simulated_applied,
        },
        "turns": rows,
    }


def main() -> int:
    report = simulate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
