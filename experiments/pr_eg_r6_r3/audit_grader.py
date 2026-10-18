"""Compare PR-EG-R6-R2-R2 automated grades with explicit local intent labels.

This audit reads preserved artifacts only. It does not call a provider and
does not treat grader output as ground truth.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_eg_r6_r2_r2"


def load_json(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def load_grades():
    blind = load_json("grading_blind_map.json")
    rows = []
    for line in (OUT / "independent_grades.jsonl").read_text(encoding="utf-8").splitlines():
        packet = json.loads(line)
        meta = blind.get(packet["packet"])
        if not meta:
            continue
        grades = packet.get("output", {}).get("grades") or []
        for grade in grades:
            rows.append({
                "run": meta["run"],
                "conversation": meta["conversation"],
                "turn": grade.get("turn"),
                **{key: grade.get(key) for key in (
                    "operation_correct", "referent_correct", "roles_preserved",
                    "correction_success", "follow_up_success", "false_clarification",
                    "relevant", "sufficient", "genuine_clarification_correct",
                )},
            })
    return rows


def paired(local_rows, grade_rows):
    index = {(row["conversation"], row["turn"]): row for row in grade_rows}
    joined = []
    for row in local_rows:
        grade = index.get((row["conversation"], row["turn"]))
        if grade:
            joined.append((row, grade))
    return joined


def count_disagreements(joined, field):
    both_true = grader_only = local_only = both_false = grader_null = 0
    examples = []
    for local, grade in joined:
        left = local.get(field)
        right = grade.get(field)
        if right is None:
            grader_null += 1
            if left is True and len(examples) < 8:
                examples.append({
                    "conversation": local["conversation"], "turn": local["turn"],
                    "player": local.get("player"), "local": left, "grader": right,
                    "issue": "grader_null_on_labeled_turn",
                })
            continue
        if left is None:
            continue
        if left and right:
            both_true += 1
        elif right and not left:
            grader_only += 1
            if len(examples) < 12:
                examples.append({
                    "conversation": local["conversation"], "turn": local["turn"],
                    "player": local.get("player"), "local": left, "grader": right,
                    "actual_act": local.get("actual_act"),
                    "issue": "grader_false_positive",
                })
        elif left and not right:
            local_only += 1
        else:
            both_false += 1
    labeled = both_true + grader_only + local_only + both_false
    return {
        "comparable_turns": labeled,
        "grader_null_while_local_labeled": grader_null,
        "both_true": both_true,
        "grader_only_false_positive": grader_only,
        "local_only": local_only,
        "both_false": both_false,
        "grader_positive": both_true + grader_only,
        "local_positive": both_true + local_only,
        "examples": examples,
    }


def main():
    local = load_json("local_assessment.json")["final_turns"]
    grades = [row for row in load_grades() if row["run"] == "final"]
    final_joined = paired(local, grades)
    metrics = {}
    for field in ("operation_correct", "referent_correct", "correction_success", "follow_up_success", "false_clarification"):
        metrics[field] = count_disagreements(final_joined, field)
    local_corrections = [row for row in local if row.get("correction_success") is not None]
    local_follows = [row for row in local if row.get("follow_up_success") is not None]
    grade_index = {(row["conversation"], row["turn"]): row for row in grades}
    missing_correction_labels = 0
    missing_follow_labels = 0
    structural_credit = []
    for row in local_corrections:
        grade = grade_index.get((row["conversation"], row["turn"]))
        if not grade or grade.get("correction_success") is None:
            missing_correction_labels += 1
        elif grade.get("correction_success") and not row.get("correction_success"):
            if grade.get("operation_correct") and grade.get("relevant"):
                structural_credit.append({
                    "conversation": row["conversation"], "turn": row["turn"], "player": row.get("player"),
                    "local_act": row.get("actual_act"), "local_success": row.get("correction_success"),
                })
    for row in local_follows:
        grade = grade_index.get((row["conversation"], row["turn"]))
        if not grade or grade.get("follow_up_success") is None:
            missing_follow_labels += 1
    relevant_and_sufficient = Counter()
    for row in local:
        grade = grade_index.get((row["conversation"], row["turn"]))
        if not grade:
            continue
        if grade.get("relevant") and grade.get("sufficient") and row.get("operation_correct") is False:
            relevant_and_sufficient["wrong_operation_still_relevant_and_sufficient"] += 1
        if grade.get("referent_correct") and row.get("referent_correct") is False:
            relevant_and_sufficient["referent_false_positive"] += 1
    report = {
        "source": "artifacts/pr_eg_r6_r2_r2 local_assessment.json final_turns joined to independent_grades.jsonl via grading_blind_map.json",
        "local_turns": len(local),
        "final_grade_rows": len(grades),
        "joined_turns": len(final_joined),
        "intended_corrections": len(local_corrections),
        "intended_followups": len(local_follows),
        "grader_missing_correction_label": missing_correction_labels,
        "grader_missing_followup_label": missing_follow_labels,
        "structural_or_relevance_credit_on_failed_corrections": structural_credit[:15],
        "bias_counts": dict(relevant_and_sufficient),
        "metrics": metrics,
        "findings": [
            "Local denominators use explicit intended-turn labels. The grader was instructed to use null unless it independently judged the turn to be a correction or follow-up.",
            "When the grader fails to recognize an intended correction or follow-up, that turn leaves the grader denominator and cannot count as a failure.",
            "Local correction and follow-up success also required the automated relevant/sufficient/roles flags, so those local rates are optimistic upper bounds, not a second human gold set.",
            "A grade can mark operation_correct and relevant while the explicit label says the conversational act was wrong.",
            "Referent credit can be assigned to a bound id that is not the labeled active referent.",
        ],
    }
    destination = ROOT / "artifacts" / "pr_eg_r6_r3"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "grader_reliability_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "joined": len(final_joined),
        "missing_correction_labels": missing_correction_labels,
        "missing_follow_labels": missing_follow_labels,
        "correction_false_positives": metrics["correction_success"]["grader_only_false_positive"],
        "follow_false_positives": metrics["follow_up_success"]["grader_only_false_positive"],
        "referent_false_positives": metrics["referent_correct"]["grader_only_false_positive"],
    }, indent=2))


if __name__ == "__main__":
    main()
