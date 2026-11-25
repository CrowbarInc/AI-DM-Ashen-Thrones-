"""Category scores. PARTIAL is never counted as PASS."""
from __future__ import annotations

from controlled_model_evaluation.cases import CLUE, Case

PASS = "PASS"
PARTIAL = "PARTIAL"
FAIL = "FAIL"
INDETERMINATE = "INDETERMINATE"
NOT_APPLICABLE = "NOT_APPLICABLE"
LABELS = (PASS, PARTIAL, FAIL, INDETERMINATE, NOT_APPLICABLE)
SAFE_ADMISSIONS = {"withheld", "clarified", "informational", "unsupported"}
CATEGORIES = (
    "intent",
    "reference",
    "admission",
    "consequence",
    "continuity",
    "narrative",
    "operational",
)


def _mutated(trace: dict) -> bool:
    return bool(
        trace.get("authoritative_mutation")
        or trace.get("inventory_changed")
        or trace.get("stance_changed")
        or trace.get("receipts_added")
    )


def _narration(trace: dict) -> str:
    return str(trace.get("narration") or "")


def _contains(text: str, fragment: str) -> bool:
    return fragment.casefold() in text.casefold()


def score_intent(case: Case, trace: dict) -> str:
    observed = trace.get("interpreted_intent")
    if trace.get("provider_error") and not observed:
        return INDETERMINATE
    if not observed:
        return INDETERMINATE
    if observed == case.intent_id:
        return PASS
    if observed in case.partial_intent_ids:
        return PARTIAL
    return FAIL


def score_reference(case: Case, trace: dict) -> str:
    if trace.get("provider_error") and "reference_ids" not in trace:
        return INDETERMINATE
    bound = set(trace.get("reference_ids") or ())
    clarified = set(trace.get("clarification_ids") or ())
    prohibited = set(case.prohibited_reference_ids)
    expected = set(case.expected_reference_ids)
    if bound & prohibited:
        return FAIL
    if not expected:
        return PASS if not bound else FAIL
    if expected <= bound:
        return PASS
    if trace.get("admission") == "clarified" and expected <= clarified and not (bound & prohibited):
        return PARTIAL
    if not bound and not clarified and trace.get("provider_error"):
        return INDETERMINATE
    return FAIL


def score_admission(case: Case, trace: dict) -> str:
    admission = trace.get("admission")
    if not admission:
        return INDETERMINATE
    mutated = _mutated(trace)
    if case.withholding_is_required:
        if admission in SAFE_ADMISSIONS and not mutated:
            return PASS
        return FAIL
    if admission == case.expected_admission and not (mutated and case.state_rule == "unchanged"):
        return PASS
    if admission in SAFE_ADMISSIONS and not mutated:
        return PARTIAL
    return FAIL


def _unchanged(trace: dict) -> bool:
    return (
        trace.get("turn_delta") == 0
        and trace.get("scene_after") == trace.get("scene_before")
        and not trace.get("inventory_changed")
        and not trace.get("stance_changed")
        and not trace.get("receipts_added")
    )


def score_consequence(case: Case, trace: dict) -> str:
    if not trace.get("snapshot_present"):
        return INDETERMINATE
    rule = case.state_rule
    narration = _narration(trace)
    if rule == "unchanged":
        return PASS if _unchanged(trace) else FAIL
    if rule == "notice_inspection":
        if trace.get("admission") == "admitted":
            ok = (
                trace.get("turn_delta") == 1
                and trace.get("scene_after") == trace.get("scene_before")
                and _contains(narration, CLUE)
                and not trace.get("inventory_changed")
                and not trace.get("stance_changed")
            )
            return PASS if ok else FAIL
        clean = _unchanged(trace) and not _contains(narration, "northwest mud track")
        return PASS if clean else FAIL
    if rule == "speech_or_withhold":
        if trace.get("inventory_changed") or trace.get("stance_changed") or trace.get("receipts_added"):
            return FAIL
        if trace.get("scene_after") != trace.get("scene_before"):
            return FAIL
        if trace.get("admission") == "admitted":
            return PASS if trace.get("turn_delta") in {0, 1} else FAIL
        return PASS if trace.get("turn_delta") == 0 else FAIL
    if rule == "authoritative_scene":
        expected = trace.get("authoritative_scene")
        if not expected:
            return INDETERMINATE
        ok = trace.get("scene_after") == expected and trace.get("turn_delta") == 0 and trace.get("scene_claim") == expected
        return PASS if ok and not trace.get("inventory_changed") else FAIL
    if rule == "recall_clue":
        if not _unchanged(trace):
            return FAIL
        committed = trace.get("prior_committed")
        if committed is None:
            return INDETERMINATE
        leaked = _contains(narration, "northwest mud track")
        if committed:
            return PASS if leaked else FAIL
        return FAIL if leaked else PASS
    if rule == "travel_or_withhold":
        if trace.get("admission") == "admitted":
            ok = trace.get("scene_after") == "old_milestone" and trace.get("turn_delta") == 1
            return PASS if ok else FAIL
        stayed = _unchanged(trace) and trace.get("scene_claim") != "old_milestone"
        return PASS if stayed else FAIL
    if rule == "recall_speaker":
        if not _unchanged(trace):
            return FAIL
        if trace.get("prior_committed") is None:
            return INDETERMINATE
        return PASS
    return INDETERMINATE


def score_continuity(case: Case, trace: dict) -> str:
    if trace.get("provider_error") and "invented_prior_success" not in trace:
        return INDETERMINATE
    if case.turn_index == 1 and not trace.get("invented_prior_success"):
        return NOT_APPLICABLE
    if not trace.get("snapshot_present"):
        return INDETERMINATE
    if trace.get("invented_prior_success"):
        return FAIL
    if trace.get("respected_committed_state") is False:
        return FAIL
    return PASS


def score_narrative(case: Case, trace: dict) -> str:
    if trace.get("narration") is None and trace.get("provider_error"):
        return INDETERMINATE
    narration = _narration(trace)
    if any(_contains(narration, fragment) for fragment in case.prohibited_narration):
        return FAIL
    if (
        trace.get("admission") == case.expected_admission
        and case.required_if_admitted
        and any(not _contains(narration, fragment) for fragment in case.required_if_admitted)
    ):
        return FAIL
    if trace.get("narrative_limitation"):
        return PARTIAL
    return PASS


def score_operational(trace: dict) -> str:
    error = trace.get("provider_error")
    if error == "timeout":
        return FAIL
    if error == "transport":
        return FAIL
    if not trace.get("live"):
        return NOT_APPLICABLE
    if trace.get("usage_complete") and trace.get("within_timeout") and not error:
        return PASS
    return INDETERMINATE


def attribute(scores: dict[str, str], trace: dict) -> dict:
    troubled = [name for name in CATEGORIES if scores[name] in {PARTIAL, FAIL}]
    contributing: list[str] = []
    primary = None
    if not troubled:
        return {"primary": None, "contributing": []}
    error = trace.get("provider_error")
    if error == "timeout":
        primary = "PROVIDER_TIMEOUT"
    elif error == "transport":
        primary = "PROVIDER_TRANSPORT"
    elif scores["intent"] in {PARTIAL, FAIL} and trace.get("model_invoked") and trace.get("model_intent_matches") is False:
        primary = "MODEL_INTERPRETATION"
    elif scores["intent"] in {PARTIAL, FAIL} and not trace.get("model_invoked"):
        primary = "ACTION_CLASSIFICATION"
    elif trace.get("model_intent_matches") is True and scores["admission"] in {PARTIAL, FAIL}:
        primary = "ACTION_ADMISSION"
    elif scores["reference"] in {PARTIAL, FAIL}:
        primary = "REFERENCE_GROUNDING"
    elif scores["consequence"] == FAIL:
        primary = "STATE_COMMITMENT"
    elif scores["narrative"] == FAIL:
        primary = "NARRATIVE_PUBLICATION"
    elif scores["continuity"] == FAIL:
        primary = "MODEL_CONTEXT_USE" if trace.get("model_invoked") else "PERSISTENCE"
    else:
        primary = "UNKNOWN"
    for cause, category in (
        ("MODEL_INTERPRETATION", "intent"),
        ("REFERENCE_GROUNDING", "reference"),
        ("ACTION_ADMISSION", "admission"),
        ("STATE_COMMITMENT", "consequence"),
        ("MODEL_CONTEXT_USE", "continuity"),
        ("NARRATIVE_PUBLICATION", "narrative"),
        ("PROVIDER_TRANSPORT", "operational"),
    ):
        if scores[category] in {PARTIAL, FAIL} and cause != primary:
            contributing.append(cause)
    return {"primary": primary, "contributing": contributing}


def score_trace(case: Case, trace: dict) -> dict:
    scores = {
        "intent": score_intent(case, trace),
        "reference": score_reference(case, trace),
        "admission": score_admission(case, trace),
        "consequence": score_consequence(case, trace),
        "continuity": score_continuity(case, trace),
        "narrative": score_narrative(case, trace),
        "operational": score_operational(trace),
    }
    execution = (
        scores["intent"] == PASS
        and scores["reference"] in {PASS, NOT_APPLICABLE}
        and scores["admission"] == PASS
        and scores["consequence"] == PASS
        and case.execution_expected
        and not case.withholding_is_required
    )
    return {
        "case_id": case.case_id,
        "scores": scores,
        "execution_success": execution,
        "withholding_required_held": case.withholding_is_required and scores["admission"] == PASS,
        "attribution": attribute(scores, trace),
    }


def summarize(results: list[dict]) -> dict:
    summary = {}
    for category in CATEGORIES:
        counts = {label: 0 for label in LABELS}
        for result in results:
            counts[result["scores"][category]] += 1
        assessable = counts[PASS] + counts[PARTIAL] + counts[FAIL]
        summary[category] = {
            **{label.lower(): counts[label] for label in LABELS},
            "assessable_denominator": assessable,
            "success_percentage": None if assessable == 0 else round(100 * counts[PASS] / assessable, 2),
            "partial_counted_as_pass": False,
        }
    summary["execution_success"] = sum(1 for result in results if result["execution_success"])
    summary["cases"] = len(results)
    return summary
