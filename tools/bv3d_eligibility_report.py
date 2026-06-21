#!/usr/bin/env python3
"""BV3D — eligible observe-turn coverage report for BV3A measurement validity."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_referential_clarity import (  # noqa: E402
    _violations_eligible_for_non_strict_local_pronoun_repair,
)
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402

REPORT_PATH = ROOT / "artifacts" / "bv3d_eligibility_report.json"


def _primary_violation(fem: dict[str, Any]) -> dict[str, Any]:
    sample = fem.get("referential_clarity_violation_sample") or []
    if sample and isinstance(sample[0], dict):
        return sample[0]
    kinds = fem.get("referential_clarity_violation_kinds") or []
    if kinds:
        return {"kind": kinds[0]}
    return {}


def _bv3a_eligibility_from_fem(fem: dict[str, Any]) -> str:
    attempted = fem.get("referential_clarity_upstream_repair_attempted")
    eligible = fem.get("referential_clarity_upstream_repair_eligible")
    applied = fem.get("referential_clarity_upstream_repair_applied")
    if applied is True:
        return "applied"
    if eligible is True:
        return "eligible_not_applied"
    if attempted is True:
        return "attempted_ineligible"
    if attempted is False and fem.get("referential_clarity_validation_passed") is not False:
        return "validation_passed_no_attempt"
    if attempted is None:
        return "no_upstream_instrumentation"
    return "unknown"


def _expected_contract_eligibility(fem: dict[str, Any], primary: dict[str, Any]) -> str:
    kind = str(primary.get("kind") or "")
    token = str(primary.get("token") or "").lower()
    unrepaired = int(fem.get("referential_clarity_unrepaired_violation_count") or 0)
    if kind != "ambiguous_entity_reference":
        if not kind and fem.get("referential_clarity_validation_passed") is not False:
            return "contract_pass"
        return "contract_ineligible_kind"
    if token not in {"he", "she", "him", "her", "they", "them"}:
        return "contract_ineligible_token"
    if unrepaired > 1:
        return "contract_ineligible_multi_violation"
    cids = primary.get("candidate_entity_ids")
    if isinstance(cids, list) and len(cids) > 1:
        return "contract_ineligible_multi_entity"
    interlocutor = str(fem.get("active_interlocutor") or "").strip()
    if not interlocutor:
        checked = fem.get("referential_clarity_checked_entities") or []
        person_count = len(checked) if isinstance(checked, list) else 0
        if person_count > 1:
            return "contract_ineligible_multi_person_no_grounding"
    return "contract_eligible_shape"


def build_report() -> dict[str, Any]:
    turns, fem_count, _hits = scan_measurement_fem_turns(include_hits=False)
    observe = [t for t in turns if t.get("route_kind") == "observe"]
    rows: list[dict[str, Any]] = []

    for index, turn in enumerate(observe, start=1):
        fem = turn["meta"]["final_emission_meta"]
        primary = _primary_violation(fem)
        measurement = turn.get("_measurement") or {}
        rows.append(
            {
                "turn_id": f"OBS-M{index:03d}",
                "artifact": measurement.get("artifact"),
                "locator": measurement.get("locator"),
                "source_class": measurement.get("source_class"),
                "violation_count": int(fem.get("referential_clarity_unrepaired_violation_count") or 0)
                or len(fem.get("referential_clarity_violation_kinds") or []),
                "ambiguity_type": primary.get("kind")
                or ((fem.get("referential_clarity_violation_kinds") or [None])[0]),
                "ambiguity_token": primary.get("token"),
                "interlocutor_present": bool(
                    str(fem.get("active_interlocutor") or fem.get("active_interlocutor_id") or "").strip()
                ),
                "social_npc_present": bool(
                    str(
                        ((turn.get("resolution") or {}).get("social") or {}).get("npc_id")
                        or fem.get("npc_id")
                        or ""
                    ).strip()
                ),
                "validator_passed": fem.get("referential_clarity_validation_passed"),
                "bv3a_eligibility_result": _bv3a_eligibility_from_fem(fem),
                "contract_eligibility": _expected_contract_eligibility(fem, primary),
                "upstream_attempted": fem.get("referential_clarity_upstream_repair_attempted"),
                "upstream_eligible": fem.get("referential_clarity_upstream_repair_eligible"),
                "upstream_applied": fem.get("referential_clarity_upstream_repair_applied"),
                "text_preview": (fem.get("final_text_preview") or "")[:120],
            }
        )

    attempted = sum(1 for r in rows if r.get("upstream_attempted") is True)
    eligible = sum(1 for r in rows if r.get("upstream_eligible") is True)
    applied = sum(1 for r in rows if r.get("upstream_applied") is True)
    contract_eligible = sum(
        1
        for r in rows
        if r.get("upstream_eligible") is True or r.get("upstream_applied") is True
    )
    fixture_eligible = sum(
        1
        for r in rows
        if r.get("source_class") == "measurement fixture" and r.get("upstream_applied") is True
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "measurement_scope": "BV3D filtered (see docs/audits/BV3D_measurement_scope.md)",
        "summary": {
            "canonical_fem_instances": fem_count,
            "observe_turn_count": len(observe),
            "contract_eligible_shape_count": contract_eligible,
            "upstream_repair_attempted_count": attempted,
            "upstream_repair_eligible_count": eligible,
            "upstream_repair_applied_count": applied,
            "eligible_observe_turn_coverage": round(applied / contract_eligible, 4) if contract_eligible else None,
            "repair_activation_rate_all_observe": round(applied / len(observe), 4) if observe else None,
            "replay_only_eligible_count": max(0, contract_eligible - fixture_eligible),
            "measurement_fixture_applied_count": fixture_eligible,
            "source_class_counts": dict(Counter(r.get("source_class") for r in rows)),
            "bv3a_eligibility_counts": dict(Counter(r.get("bv3a_eligibility_result") for r in rows)),
            "contract_eligibility_counts": dict(Counter(r.get("contract_eligibility") for r in rows)),
        },
        "observe_turns": rows,
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
