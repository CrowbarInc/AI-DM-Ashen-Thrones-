"""Human scoring worksheet.

The sheet records three separate judgments. It does not score the turn itself.
"""

from __future__ import annotations

from typing import Any, Mapping

from tools.atgb.fixtures import authoritative_context

QUALITATIVE_PROMPTS = (
    "repetitive responses",
    "unnatural phrasing",
    "excessive clarification",
    "poor conversational pacing",
    "failure to sustain initiative",
    "mechanical or validation-like dialogue",
)


def _banner(result: Mapping[str, Any]) -> str:
    mode = result.get("execution_mode")
    if mode == "provider_disabled_simulated":
        return (
            "These responses come from a simulated test double. "
            "They are not AI-DM responses and must not be scored as gameplay benchmark performance."
        )
    if mode == "provider_disabled_host":
        return (
            "These responses are host output with providers disabled. "
            "Natural conversational competence is unchecked. "
            "This sheet is not an Ashen Thrones Gameplay Benchmark result."
        )
    if mode == "live_provider":
        return (
            "These responses are from a live-provider execution. "
            "Enter interpretation, response, and authority separately. "
            "Uncertain is available when the evidence is insufficient. "
            "Do not collapse the three judgments into one score."
        )
    return "Execution mode is unrecognized. Do not treat this sheet as a gameplay result."


def build_worksheet(result: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    scenarios = {item["scenario_id"]: item for item in result.get("scenario_records") or []}
    conversations = []
    current_id = None
    bucket: list[dict[str, Any]] = []
    for turn in result.get("turns") or []:
        if turn["scenario_id"] != current_id:
            if bucket:
                conversations.append(_conversation_block(current_id, bucket, scenarios, manifest, result))
            current_id = turn["scenario_id"]
            bucket = [turn]
        else:
            bucket.append(turn)
    if bucket:
        conversations.append(_conversation_block(current_id, bucket, scenarios, manifest, result))
    return {
        "worksheet_version": 1,
        "benchmark_version": result.get("benchmark_version"),
        "rubric_version": result.get("rubric_version"),
        "execution_mode": result.get("execution_mode"),
        "evidence_distinction": result.get("evidence_distinction"),
        "gameplay_performance_claim": False if result.get("execution_mode") != "live_provider" else bool(result.get("gameplay_performance_claim")),
        "banner": _banner(result),
        "judgment_instructions": {
            "interpretation": "Did the system understand the player's communicative intent?",
            "response": "Did the response adequately address that intent?",
            "authority": "Did the system preserve established world facts and state?",
            "uncertain": "Use uncertain when the captured evidence is insufficient.",
            "acceptable": "Yes only when response and authority are both pass. Interpretation stays visible beside them.",
            "qualitative": "Conversation notes are not a numerical score.",
        },
        "conversations": conversations,
    }


def _conversation_block(
    scenario_id: str | None,
    turns: list[Mapping[str, Any]],
    scenarios: Mapping[str, Any],
    manifest: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    record = scenarios.get(scenario_id or "", {})
    context = record.get("authoritative_context")
    if context is None:
        context = {"scenario_id": scenario_id}
    saved = next((item for item in result.get("conversations") or [] if item.get("scenario_id") == scenario_id), {})
    return {
        "scenario_id": scenario_id,
        "title": record.get("title"),
        "partition": record.get("partition"),
        "evidence_status": record.get("evidence_status"),
        "authoritative_context": context,
        "turns": [_turn_row(turn) for turn in turns],
        "qualitative": {
            "prompts": list(QUALITATIVE_PROMPTS),
            "observations": list(saved.get("qualitative_observations") or []),
            "notes": saved.get("qualitative_notes") or "",
            "scored": False,
        },
    }


def _turn_row(turn: Mapping[str, Any]) -> dict[str, Any]:
    judgment = turn["judgment"]
    return {
        "scenario_id": turn["scenario_id"],
        "turn_id": turn["turn_id"],
        "partition": turn["partition"],
        "primary_capability": turn["primary_capability"],
        "player_input": turn["player_input"],
        "ai_dm_response": turn["response_text"],
        "response_origin": turn["response_origin"],
        "simulated": bool(turn.get("simulated")),
        "authoritative_context": turn.get("turn_context"),
        "state_evidence": turn.get("state_evidence"),
        "interpretation_assessment": judgment["interpretation"],
        "response_assessment": judgment["response"],
        "authority_assessment": judgment["authority"],
        "failure_severity": judgment["severity"],
        "clarification_assessment": {
            "expected": turn.get("clarification_expected"),
            "reviewer": judgment["clarification"],
            "applicable": True,
        },
        "continuity_assessment": {
            "expected": turn.get("continuity_expected"),
            "reviewer": judgment["continuity"],
        },
        "reviewer_notes": judgment.get("reviewer_notes") or "",
        "human_review_status": judgment["human_review_status"],
        "evidence_references": turn.get("evidence_references") or [],
    }


def render_worksheet(worksheet: Mapping[str, Any]) -> str:
    lines = [
        "# ATGB human scoring worksheet",
        "",
        worksheet["banner"],
        "",
        f"Benchmark `{worksheet.get('benchmark_version')}`, rubric `{worksheet.get('rubric_version')}`, mode `{worksheet.get('execution_mode')}`.",
        "",
        "Interpretation, response, and authority stay separate. Mark a judgment `uncertain` when the evidence is insufficient.",
        "",
    ]
    for conversation in worksheet["conversations"]:
        lines.extend(
            [
                f"## {conversation['scenario_id']} — {conversation.get('title')}",
                "",
                f"Partition: `{conversation.get('partition')}`. Evidence status: `{conversation.get('evidence_status')}`.",
                "",
                "### Conversation quality",
                "",
                "Not a score. A conversation may be technically successful and still feel unnatural.",
                "",
            ]
        )
        for prompt in conversation["qualitative"]["prompts"]:
            lines.append(f"- [ ] {prompt}")
        lines.extend(["", "Reviewer observations:", "", conversation["qualitative"]["notes"] or "(none yet)", ""])
        for turn in conversation["turns"]:
            lines.extend(
                [
                    f"### {turn['turn_id']}",
                    "",
                    f"- Player input: {turn['player_input']}",
                    f"- AI-DM response: {turn['ai_dm_response']}",
                    f"- Response origin: `{turn['response_origin']}`",
                    f"- Relevant authoritative context: {turn['authoritative_context']}",
                    f"- Interpretation assessment: `{turn['interpretation_assessment']}`",
                    f"- Response assessment: `{turn['response_assessment']}`",
                    f"- Authority assessment: `{turn['authority_assessment']}`",
                    f"- Failure severity: `{turn['failure_severity']}`",
                    f"- Clarification assessment: expected `{turn['clarification_assessment']['expected']}`; "
                    f"reviewer `{turn['clarification_assessment']['reviewer']}`",
                    f"- Reviewer notes: {turn['reviewer_notes'] or '(none yet)'}",
                    f"- Evidence references: {', '.join(turn['evidence_references']) or '(none)'}",
                    "",
                ]
            )
    return "\n".join(lines)


def context_for_turn(scenario: Mapping[str, Any], turn: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    shared = authoritative_context(scenario, manifest)
    return {
        "scenario": shared,
        "communicative_act": turn.get("communicative_act"),
        "interpretation_pass": turn.get("interpretation_pass"),
        "response_pass": turn.get("response_pass"),
        "authority_pass": turn.get("authority_pass"),
        "acceptable_variations": turn.get("acceptable_variations"),
        "unacceptable_behaviors": turn.get("unacceptable_behaviors"),
    }
