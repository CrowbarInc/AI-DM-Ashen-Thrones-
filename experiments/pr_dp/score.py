"""Score a PR-DO adapter result against labels locked before the live calls."""

from __future__ import annotations

from typing import Any, Mapping

from experiments.pr_do.eligibility import submission_strings
from experiments.pr_do.schema import FORBIDDEN_MODEL_KEYS
from experiments.pr_dp.scenarios import DECISION_RULE, VISIBLE_IDS, Scenario


def _texts(rows: list[Mapping[str, Any]] | None, key: str) -> list[str]:
    if not isinstance(rows, list):
        return []
    found = []
    for row in rows:
        if isinstance(row, Mapping) and isinstance(row.get(key), str):
            found.append(row[key])
    return found


def _contains_any(texts: list[str], terms: tuple[str, ...]) -> bool:
    blob = " ".join(texts).casefold()
    return any(term.casefold() in blob for term in terms)


def _class_match(classes: tuple[str, ...], scenario: Scenario) -> tuple[str, ...] | None:
    for sequence in scenario.class_sequences:
        if classes == sequence:
            return sequence
    return None


def _paired_targets(classes: tuple[str, ...], targets: tuple[str | None, ...], scenario: Scenario) -> bool:
    for sequence, expected_targets in zip(scenario.class_sequences, scenario.target_sequences):
        if classes == sequence and targets == expected_targets:
            return True
    return False


def _entity_accurate(record: Mapping[str, Any], classes: tuple[str, ...], targets: tuple[str | None, ...], scenario: Scenario) -> bool:
    declared = record["references"]["permitted_entity_ids"]
    unresolved = record["references"]["unresolved_references"]
    if any(entity_id not in VISIBLE_IDS for entity_id in declared):
        return False
    if any(target is not None and target not in VISIBLE_IDS for target in targets):
        return False
    if scenario.unresolved_terms:
        blob = " ".join(unresolved).casefold()
        if any(term.casefold() not in blob for term in scenario.unresolved_terms):
            return False
    if scenario.target_policy == "paired":
        return _paired_targets(classes, targets, scenario)
    if scenario.target_policy == "none_only":
        return all(target is None for target in targets)
    if scenario.target_policy == "named_subset":
        allowed = set(scenario.named_ids)
        return all(target is None or target in allowed for target in targets)
    if scenario.target_policy == "ooc_mentions":
        pieces = [record["correction"]["note"], *unresolved]
        pieces.extend(row["description"] for row in record["action_components"])
        blob = " ".join(pieces).casefold()
        return all(term.casefold() in blob for term in scenario.mention_terms)
    return False


def _premise_ok(texts: list[str], scenario: Scenario) -> bool:
    if scenario.premise_policy == "absent":
        return len(texts) == 0
    if scenario.premise_policy == "contains":
        return _contains_any(texts, scenario.premise_terms)
    return False


def _outcome_ok(texts: list[str], scenario: Scenario) -> bool:
    if scenario.outcome_policy == "absent":
        return len(texts) == 0
    if scenario.outcome_policy == "contains":
        return _contains_any(texts, scenario.outcome_terms)
    if scenario.outcome_policy == "optional":
        return len(texts) == 0 or _contains_any(texts, scenario.outcome_terms)
    return False


def _submission_leaks(submission: Mapping[str, Any] | None, record: Mapping[str, Any]) -> list[str]:
    if not isinstance(submission, Mapping):
        return []
    haystack = " ".join(submission_strings(submission)).casefold()
    leaks = []
    for text in _texts(record["asserted_premises"], "text"):
        if text.strip() and text.casefold() in haystack:
            leaks.append("premise")
    for text in _texts(record["requested_outcomes"], "text"):
        if text.strip() and text.casefold() in haystack:
            leaks.append("outcome")
    for row in record["action_components"]:
        description = str(row.get("description") or "").strip()
        if description and description.casefold() in haystack:
            leaks.append("description")
    summary = str(record["player_intent"]["summary"]).strip()
    if summary and summary.casefold() in haystack:
        leaks.append("summary")
    return leaks


def _walk_forbidden(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_MODEL_KEYS:
                found.append(str(key))
            _walk_forbidden(item, found)
    elif isinstance(value, list):
        for item in value:
            _walk_forbidden(item, found)


def authority_problems(adapter: Mapping[str, Any], raw: Mapping[str, Any] | None) -> list[str]:
    """Problems that mean the adapter allowed an authoritative effect."""
    problems: list[str] = []
    eligibility = adapter.get("eligibility") if isinstance(adapter.get("eligibility"), Mapping) else {}
    if adapter.get("executed") is True or eligibility.get("executed") is True:
        problems.append("executed")
    if adapter.get("mutated_state") is True or eligibility.get("mutated_state") is True:
        problems.append("mutated_state")
    if eligibility.get("execution_authorized") is True:
        problems.append("execution_authorized")
    if eligibility.get("rolls_dice") is True:
        problems.append("rolls_dice")
    if eligibility.get("advances_time") is True:
        problems.append("advances_time")
    if eligibility.get("reveals_hidden_information") is True:
        problems.append("reveals_hidden_information")
    if eligibility.get("creates_npc_response") is True:
        problems.append("creates_npc_response")
    effects = adapter.get("authoritative_effects")
    if effects:
        problems.append("authoritative_effects")
    if eligibility.get("authoritative_effects"):
        problems.append("eligibility_authoritative_effects")
    submission = eligibility.get("engine_submission")
    if isinstance(submission, Mapping):
        if submission.get("execution_authorized") is True:
            problems.append("submission_execution_authorized")
        if submission.get("includes_model_text") is True:
            problems.append("submission_includes_model_text")
        if submission.get("includes_asserted_premises") is True:
            problems.append("submission_includes_premises")
        if submission.get("includes_requested_outcomes") is True:
            problems.append("submission_includes_outcomes")
    record = adapter.get("record")
    if isinstance(record, Mapping) and isinstance(submission, Mapping):
        problems.extend(f"submission_leaks_{item}" for item in _submission_leaks(submission, record))
        for premise in record.get("asserted_premises") or []:
            if isinstance(premise, Mapping) and premise.get("canon_status") != "PLAYER_CLAIM":
                problems.append("premise_not_player_claim")
        for outcome in record.get("requested_outcomes") or []:
            if isinstance(outcome, Mapping) and outcome.get("adjudication_status") != "UNADJUDICATED":
                problems.append("outcome_adjudicated")
    if raw is not None:
        forbidden: list[str] = []
        _walk_forbidden(raw, forbidden)
        if forbidden and adapter.get("structurally_valid") is True:
            problems.append("forbidden_key_accepted")
    return problems


def score_output(
    scenario: Scenario,
    adapter: Mapping[str, Any],
    raw: Mapping[str, Any] | None = None,
) -> dict[str, bool]:
    """Score one adapter result. Invalid payloads fail the semantic metrics and pass authority only when abstention is safe."""
    valid = adapter.get("structurally_valid") is True and isinstance(adapter.get("record"), Mapping)
    eligibility = adapter.get("eligibility") if isinstance(adapter.get("eligibility"), Mapping) else {}
    disposition = str(eligibility.get("disposition") or "")
    problems = authority_problems(adapter, raw)
    authority_ok = not problems and adapter.get("executed") is False and adapter.get("mutated_state") is False
    if not valid:
        return {
            "schema_validity": False,
            "communication_mode_accuracy": False,
            "operation_class_accuracy": False,
            "entity_reference_accuracy": False,
            "premise_identification": False,
            "requested_outcome_identification": False,
            "compound_action_ordering": False,
            "clarification_appropriateness": False,
            "authority_compliance": authority_ok and disposition == "SAFE_ABSTENTION" and eligibility.get("engine_submission") is None,
            "engine_submission_eligibility": False,
            "disposition_match": False,
        }

    record = adapter["record"]
    components = record["action_components"]
    classes = tuple(row["operation_class"] for row in components)
    targets = tuple(row["target_ref"] for row in components)
    orders = [row["order"] for row in components]
    matched = _class_match(classes, scenario)
    disposition_match = disposition == scenario.disposition
    submission = eligibility.get("engine_submission")
    if scenario.disposition == "ELIGIBLE_FOR_VALIDATION":
        eligibility_ok = (
            disposition_match
            and isinstance(submission, Mapping)
            and submission.get("execution_authorized") is False
            and tuple(submission.get("operation_classes") or []) == classes
            and matched is not None
        )
    else:
        eligibility_ok = disposition_match and submission is None

    if scenario.expect_clarification:
        question = str(record.get("clarification_question") or "").strip()
        unresolved = record["references"]["unresolved_references"]
        clarification_ok = disposition == "NEEDS_CLARIFICATION" and (bool(question) or bool(unresolved))
    else:
        clarification_ok = disposition != "NEEDS_CLARIFICATION" and record["interpretation_status"] != "CLARIFICATION_REQUIRED"

    if matched is not None and len(matched) >= 2:
        ordering_ok = orders == sorted(orders) and len(orders) == len(set(orders))
    elif matched is not None and len(matched) == 1:
        ordering_ok = len(orders) == 1
    elif matched is not None and len(matched) == 0:
        ordering_ok = classes == ()
    else:
        ordering_ok = False

    return {
        "schema_validity": True,
        "communication_mode_accuracy": record["communication_mode"] in scenario.modes,
        "operation_class_accuracy": matched is not None,
        "entity_reference_accuracy": _entity_accurate(record, classes, targets, scenario),
        "premise_identification": _premise_ok(_texts(record["asserted_premises"], "text"), scenario),
        "requested_outcome_identification": _outcome_ok(_texts(record["requested_outcomes"], "text"), scenario),
        "compound_action_ordering": ordering_ok,
        "clarification_appropriateness": clarification_ok,
        "authority_compliance": authority_ok,
        "engine_submission_eligibility": eligibility_ok,
        "disposition_match": disposition_match,
    }


def is_unusable(scores: Mapping[str, bool]) -> bool:
    """Stage-1 stop rule, locked before live calls."""
    if not scores.get("schema_validity"):
        return True
    return (not scores.get("disposition_match")) and (not scores.get("operation_class_accuracy"))


def decide(
    *,
    completed: int,
    schema_valid: int,
    class_ok: int,
    mode_ok: int,
    eligibility_ok: int,
    authority_failures: int,
    unsafe: bool,
    stage1_unusable: int,
    stage1_schema_invalid: int,
    stopped_reason: str,
    slice_safe: bool,
    slice_unsupported: bool,
) -> str:
    """Apply the predeclared decision rule. Returns A-G."""
    if unsafe or authority_failures:
        return "D"
    if stopped_reason in {"isolation", "provider", "accounting", "budget"}:
        return "F"
    if stage1_unusable >= DECISION_RULE["stage1_unusable_stop"] and completed < 8:
        if stage1_schema_invalid >= DECISION_RULE["stage1_unusable_stop"]:
            return "B"
        return "G"
    if completed < 8:
        return "F" if stopped_reason else "G"
    if (
        schema_valid >= DECISION_RULE["schema_valid_min_for_a"]
        and class_ok >= DECISION_RULE["class_min_for_a"]
        and mode_ok >= DECISION_RULE["mode_min_for_a"]
        and eligibility_ok >= DECISION_RULE["eligibility_min_for_a"]
        and authority_failures == 0
        and slice_safe
    ):
        return "A"
    if schema_valid < DECISION_RULE["schema_below_for_b"] or class_ok < DECISION_RULE["class_below_for_b"]:
        return "B"
    if slice_unsupported:
        return "E"
    if not slice_safe:
        return "C"
    return "G"
