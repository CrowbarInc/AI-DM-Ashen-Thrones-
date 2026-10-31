"""Structured ATGB results and the human-readable checkpoint report.

The report keeps critical failures ahead of any rate. It does not emit a
universal gameplay score.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from tools.atgb import (
    EVIDENCE_HOST,
    EVIDENCE_HUMAN,
    EVIDENCE_INFRASTRUCTURE,
    EVIDENCE_LIVE,
    RESULT_SCHEMA_VERSION,
    UNAVAILABLE,
    UNSCORED,
)

JUDGMENT_VALUES = frozenset({"pass", "fail", "uncertain", "unchecked", UNSCORED})
SEVERITY_VALUES = frozenset({"minor", "major", "critical", "uncertain", UNSCORED})
CLARIFICATION_VALUES = frozenset(
    {"none", "necessary_pass", "unnecessary_fail", "missing_when_needed_fail", "uncertain", UNSCORED}
)
CONTINUITY_VALUES = frozenset({"not_applicable", "preserved", "lost", "uncertain", UNSCORED})
REVIEW_VALUES = frozenset({"HUMAN_ACCEPTED", "HUMAN_REJECTED", "HUMAN_AMBIGUOUS", "not_reviewed"})


def unavailable_telemetry() -> dict[str, Any]:
    return {
        "elapsed_ms": {"status": UNAVAILABLE, "value": None},
        "provider_call_count": {"status": UNAVAILABLE, "value": None},
        "input_tokens": {"status": UNAVAILABLE, "value": None},
        "output_tokens": {"status": UNAVAILABLE, "value": None},
        "retry_count": {"status": UNAVAILABLE, "value": None},
        "estimated_cost": {"status": UNAVAILABLE, "value": None},
    }


def recorded_or_missing(value: Any) -> dict[str, Any]:
    """Preserve a host null. Use unavailable only when the field was not observed."""

    if value is None:
        return {"status": "host_reported_null", "value": None}
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return {"status": UNAVAILABLE, "value": None}
    return {"status": "recorded", "value": value}


def blank_judgment() -> dict[str, Any]:
    return {
        "interpretation": "unchecked",
        "response": "unchecked",
        "authority": "unchecked",
        "acceptable": "not_established",
        "severity": UNSCORED,
        "clarification": UNSCORED,
        "continuity": UNSCORED,
        "human_review_status": "not_reviewed",
        "reviewer_notes": "",
    }


def acceptable_from(judgment: Mapping[str, Any]) -> str:
    response = judgment.get("response")
    authority = judgment.get("authority")
    if response == "pass" and authority == "pass":
        return "yes"
    if response in {"unchecked", "uncertain", UNSCORED} or authority in {"unchecked", "uncertain", UNSCORED}:
        return "not_established"
    return "no"


def evidence_distinction(*, mode: str, human_review_complete: bool) -> str:
    if mode == "provider_disabled_simulated":
        return EVIDENCE_INFRASTRUCTURE
    if mode == "provider_disabled_host":
        return EVIDENCE_HOST
    if mode == "live_provider" and human_review_complete:
        return EVIDENCE_HUMAN
    if mode == "live_provider":
        return EVIDENCE_LIVE
    return EVIDENCE_INFRASTRUCTURE


def gameplay_performance_claim(distinction: str) -> bool:
    """True only for a live transcript that a person has reviewed. Never true for infrastructure."""

    return distinction == EVIDENCE_HUMAN


def apply_scores(result: dict[str, Any], scores: Mapping[str, Any]) -> dict[str, Any]:
    """Merge a human score file. Unknown turns and illegal values are rejected, not coerced to pass."""

    turn_scores = scores.get("turns")
    if not isinstance(turn_scores, dict):
        raise ValueError("Score file needs a turns object.")
    known = {turn["turn_id"]: turn for turn in result["turns"]}
    for turn_id, payload in turn_scores.items():
        if turn_id not in known:
            raise ValueError(f"Score file names unknown turn {turn_id}.")
        if not isinstance(payload, dict):
            raise ValueError(f"Score for {turn_id} must be an object.")
        judgment = known[turn_id]["judgment"]
        for key, allowed in (
            ("interpretation", JUDGMENT_VALUES),
            ("response", JUDGMENT_VALUES),
            ("authority", JUDGMENT_VALUES),
            ("severity", SEVERITY_VALUES),
            ("clarification", CLARIFICATION_VALUES),
            ("continuity", CONTINUITY_VALUES),
            ("human_review_status", REVIEW_VALUES),
        ):
            if key not in payload:
                continue
            if payload[key] not in allowed:
                raise ValueError(f"{turn_id} {key} has unsupported value {payload[key]!r}.")
            judgment[key] = payload[key]
        if "reviewer_notes" in payload:
            judgment["reviewer_notes"] = str(payload["reviewer_notes"])
        judgment["acceptable"] = acceptable_from(judgment)
    conversations = scores.get("conversations")
    if conversations is not None:
        if not isinstance(conversations, dict):
            raise ValueError("Score file conversations must be an object.")
        for scenario_id, notes in conversations.items():
            match = next((item for item in result["conversations"] if item["scenario_id"] == scenario_id), None)
            if match is None:
                raise ValueError(f"Score file names unknown scenario {scenario_id}.")
            if not isinstance(notes, dict):
                raise ValueError(f"Conversation notes for {scenario_id} must be an object.")
            observations = notes.get("observations") or []
            if not isinstance(observations, list) or not all(isinstance(item, str) for item in observations):
                raise ValueError(f"Conversation observations for {scenario_id} must be strings.")
            match["qualitative_observations"] = list(observations)
            match["qualitative_notes"] = str(notes.get("notes") or "")
    result["human_review_complete"] = all(
        turn["judgment"]["human_review_status"] in {"HUMAN_ACCEPTED", "HUMAN_REJECTED", "HUMAN_AMBIGUOUS"}
        for turn in result["turns"]
    )
    result["evidence_distinction"] = evidence_distinction(
        mode=result["execution_mode"],
        human_review_complete=result["human_review_complete"],
    )
    result["gameplay_performance_claim"] = gameplay_performance_claim(result["evidence_distinction"])
    result["report"] = build_report(result)
    return result


def _full_exchange(turn: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": turn["turn_id"],
        "scenario_id": turn["scenario_id"],
        "partition": turn["partition"],
        "primary_capability": turn["primary_capability"],
        "player_input": turn["player_input"],
        "response_text": turn["response_text"],
        "response_origin": turn["response_origin"],
        "judgment": turn["judgment"],
        "prior_turn_id": turn.get("prior_turn_id"),
    }


def summarize_counts(result: Mapping[str, Any]) -> dict[str, Any]:
    """Raw counts. Percentages are derived beside them and are not a score."""

    turns = list(result.get("turns") or [])
    critical = [turn for turn in turns if turn["judgment"]["severity"] == "critical"]
    major = [turn for turn in turns if turn["judgment"]["severity"] == "major"]
    unnecessary = [turn for turn in turns if turn["judgment"]["clarification"] == "unnecessary_fail"]
    missing_clarification = [turn for turn in turns if turn["judgment"]["clarification"] == "missing_when_needed_fail"]
    continuity_lost = [turn for turn in turns if turn["judgment"]["continuity"] == "lost"]
    by_capability: dict[str, Any] = {}
    for turn in turns:
        bucket = by_capability.setdefault(
            turn["primary_capability"],
            {
                partition: {"pass": 0, "fail": 0, "uncertain": 0, "unchecked": 0, "unscored": 0}
                for partition in ("development_visible", "related_variation", "held_out")
            },
        )
        cell = bucket[turn["partition"]]
        response = turn["judgment"]["response"]
        if response not in cell:
            cell[response] = 0
        cell[response] += 1
    return {
        "turns_captured": len(turns),
        "critical_failures": [_full_exchange(turn) for turn in critical],
        "major_failures": [_full_exchange(turn) for turn in major],
        "unnecessary_clarifications": [turn["turn_id"] for turn in unnecessary],
        "missing_clarifications": [turn["turn_id"] for turn in missing_clarification],
        "continuity_failures": [turn["turn_id"] for turn in continuity_lost],
        "capability_response_counts": by_capability,
        "conversation_qualitative": [
            {
                "scenario_id": item["scenario_id"],
                "observations": item.get("qualitative_observations") or [],
                "notes": item.get("qualitative_notes") or "",
            }
            for item in result.get("conversations") or []
        ],
    }


def _percent(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(100.0 * numerator / denominator, 1)


def build_report(result: Mapping[str, Any]) -> str:
    counts = summarize_counts(result)
    claim = bool(result.get("gameplay_performance_claim"))
    lines = [
        "ATGB REPORT",
        f"Benchmark: {result.get('benchmark_version')}",
        f"Scenario version: {result.get('scenario_version')}",
        f"Rubric: {result.get('rubric_version')}",
        f"Partition revision: {result.get('partition_revision')}",
        f"Revision: {result.get('repository_revision')}",
        f"Execution mode: {result.get('execution_mode')}",
        f"Evidence distinction: {result.get('evidence_distinction')}",
        f"Trial: {result.get('trial_number')}",
        f"Gameplay performance claim: {str(claim).lower()}",
        "",
    ]
    if not claim:
        lines.extend(
            [
                "This package is not an Ashen Thrones Gameplay Benchmark performance result.",
                "Provider-disabled and unscored transcripts do not measure conversational competence.",
                "",
            ]
        )
    lines.extend(["## Starting-state preflight", ""])
    for record in result.get("scenario_records") or []:
        preflight = record.get("preflight")
        if not preflight:
            lines.append(f"- {record['scenario_id']}: not verified ({record.get('context_establishment')}).")
            continue
        status = "verified machine prerequisites" if preflight.get("ok") else "BLOCKED prerequisites"
        lines.append(f"- {record['scenario_id']}: {status}.")
        for failure in preflight.get("critical_failures") or []:
            lines.append(f"  - {failure}")
    lines.extend(["", "Narrative assumptions remain unverified; see each scenario's preflight record. Prerequisite failures are not conversational failures.", ""])
    lines.append("## Critical failures")
    lines.append("")
    critical = counts["critical_failures"]
    if not critical:
        if result.get("human_review_complete") and claim:
            lines.append("None recorded in the human review.")
        else:
            lines.append("Not established. Failure severity is unscored or this lane cannot carry a gameplay claim.")
    else:
        lines.append("The checkpoint has a state-integrity or authority breach.")
        for index, turn in enumerate(critical, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. {turn['turn_id']} ({turn['partition']}, {turn['primary_capability']}).",
                    f"Player: {turn['player_input']}",
                    f"Reply: {turn['response_text']}",
                    f"Interpretation: {turn['judgment']['interpretation']}. "
                    f"Response: {turn['judgment']['response']}. "
                    f"Authority: {turn['judgment']['authority']}.",
                ]
            )
    lines.extend(["", "## Major conversational failures", ""])
    major = counts["major_failures"]
    if not major:
        lines.append("None recorded." if result.get("human_review_complete") and claim else "Not established.")
    else:
        for turn in major:
            lines.append(
                f"- {turn['turn_id']} {turn['primary_capability']}. "
                f"Player: {turn['player_input']} Reply: {turn['response_text']}"
            )
    lines.extend(["", "## Capability counts", ""])
    lines.append("Counts are response judgments by primary capability and partition. They are not a gameplay score.")
    lines.append("")
    for capability, partitions in counts["capability_response_counts"].items():
        for partition, cell in partitions.items():
            scored = cell["pass"] + cell["fail"]
            lines.append(
                f"- {capability} / {partition}: pass {cell['pass']} / scored {scored} "
                f"({_percent(cell['pass'], scored) if claim else 'percent withheld'}); "
                f"fail {cell['fail']}; uncertain {cell['uncertain']}; "
                f"unchecked {cell['unchecked']}; unscored {cell['unscored']}"
            )
    lines.extend(
        [
            "",
            "## Clarification and continuity",
            "",
            f"- Unnecessary clarifications: {len(counts['unnecessary_clarifications'])} "
            f"({', '.join(counts['unnecessary_clarifications']) or 'none'})",
            f"- Missing clarifications: {len(counts['missing_clarifications'])} "
            f"({', '.join(counts['missing_clarifications']) or 'none'})",
            f"- Continuity failures: {len(counts['continuity_failures'])} "
            f"({', '.join(counts['continuity_failures']) or 'none'})",
            "",
            "## Conversation-level qualitative findings",
            "",
            "These notes are not a second score. A conversation can be technically successful and still feel unnatural.",
            "",
        ]
    )
    qualitative = counts["conversation_qualitative"]
    if not any(item["observations"] or item["notes"] for item in qualitative):
        lines.append("No qualitative notes have been entered.")
    else:
        for item in qualitative:
            if item["observations"] or item["notes"]:
                lines.append(
                    f"- {item['scenario_id']}: {', '.join(item['observations']) or 'no pattern tag'}. {item['notes']}"
                )
    lines.extend(["", "## Latency, provider usage, and cost", ""])
    latencies = []
    calls = 0
    calls_known = True
    cost_values = []
    cost_known_for_all_acceptable = True
    acceptable = 0
    for turn in result.get("turns") or []:
        elapsed = (turn.get("telemetry") or {}).get("elapsed_ms") or {}
        if elapsed.get("status") == "recorded" and isinstance(elapsed.get("value"), (int, float)):
            latencies.append((turn["turn_id"], elapsed["value"]))
        call = (turn.get("telemetry") or {}).get("provider_call_count") or {}
        if call.get("status") == "recorded" and isinstance(call.get("value"), int):
            calls += int(call["value"])
        else:
            calls_known = False
        if turn["judgment"]["acceptable"] == "yes":
            acceptable += 1
            cost = (turn.get("telemetry") or {}).get("estimated_cost") or {}
            if cost.get("status") == "recorded" and isinstance(cost.get("value"), (int, float)):
                cost_values.append(cost["value"])
            else:
                cost_known_for_all_acceptable = False
    if latencies:
        slowest = max(latencies, key=lambda item: item[1])
        lines.append(f"- Captured latencies: {len(latencies)} of {len(result.get('turns') or [])}.")
        lines.append(f"- Slowest captured turn: {slowest[0]} at {slowest[1]} ms.")
    else:
        lines.append("- Response latency: unavailable.")
    lines.append(
        f"- Provider calls: {calls if calls_known else UNAVAILABLE}."
    )
    if acceptable and cost_known_for_all_acceptable and cost_values:
        total = sum(cost_values)
        lines.append(
            f"- Cost per successful turn: {total / acceptable} "
            f"(total {total} across {acceptable} acceptable turns)."
        )
    else:
        lines.append(
            f"- Cost per successful turn: {UNAVAILABLE} "
            f"(acceptable turns with a gameplay judgment: {acceptable})."
        )
    if result.get("stop_reason"):
        lines.extend(["", "## Budget stop", "", f"- {result['stop_reason']}"])
    lines.extend(
        [
            "",
            "## Held-out evidence",
            "",
            "Held-out turns keep that partition. In this corpus they were already visible in the ATGB-01 review, "
            "so they are not fully independent unseen evaluation data.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def result_document(**fields: Any) -> dict[str, Any]:
    document = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "gameplay_performance_claim": False,
        "human_review_complete": False,
        "compatibility": {
            "historical_adapter": False,
            "limitations": [
                "No historical compatibility adapter is implemented.",
                "An older build is comparable only when it can boot the same isolated data directory, accept the same player lines through chat, and emit player-facing text plus state evidence.",
                "A model change is a comparability limitation, not automatically a product regression.",
                "S07 is held-out in ATGB-02. The ATGB-01 catalog table still lists it as development-visible. Compare S07 by the partition stored in the result.",
                "Held-out scenarios in this corpus were exposed in the ATGB-01 review package.",
            ],
        },
    }
    document.update(fields)
    document["report"] = build_report(document)
    return document


def write_json(path: Any, document: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
