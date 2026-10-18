"""Independent scoring for PR-EG-R6-R3-R1 production transcripts.

Labels describe the player's meaning. They are not read from the engine's
selected candidate.
"""
import json
import sys
from pathlib import Path


EVEN = [
    ("information_question", "cistern", "cracked"),
    ("correction", "reversal", None),
    ("follow_up", "source", None),
    ("information_question", "amber lens", "surveyor"),
    ("correction", "slate", None),
    ("follow_up", "evidence", None),
    ("information_question", "viaduct", "unknown"),
    ("follow_up", "source", "ambiguous_ok"),
    ("information_question", "roster", "someone"),
    ("follow_up", "roster", None),
    ("information_question", "skiff", "dawn"),
    ("follow_up", "temporal", "not_dawn"),
    ("information_question", "countersign", "withhold"),
    ("information_question", "cistern", "cracked_or_clarify"),
    ("correction", "switch", "clarify_ok"),
]
ODD = [
    ("information_question", "amber lens", "surveyor"),
    ("correction", "slate", None),
    ("follow_up", "explanation", None),
    ("information_question", "cistern", "cracked"),
    ("follow_up", "speech", None),
    ("information_question", "skiff", "unknown"),
    ("follow_up", "spatial", None),
    ("information_question", "roster", "someone"),
    ("follow_up", "source", "ambiguous_ok"),
    ("information_question", "countersign", "withhold"),
    ("information_question", "countersign", "withhold"),
    ("information_question", "cistern", "cracked_or_clarify"),
    ("correction", "reversal", None),
    ("follow_up", "evidence", "ambiguous_ok"),
    ("information_question", "amber lens", "surveyor"),
]


def _roles(plan):
    prop = (plan or {}).get("request_proposition") or {}
    return {str(role.get("name") or ""): str(role.get("value") or "").casefold() for role in prop.get("roles") or []}


def _blob(plan):
    return " ".join(_roles(plan).values())


def score_turn(row):
    index = int(row["turn"]) - 1
    block = ODD if int(row["conversation"].rsplit("_", 1)[-1]) % 2 else EVEN
    operation, topic, answer = block[index]
    plan = row.get("plan") or {}
    act = str(plan.get("conversational_act") or "")
    follow = str((plan.get("referent_operation") or {}).get("follow_up_relationship") or "")
    text = str(row.get("text") or "").casefold()
    kind = str(plan.get("response_kind") or "")
    roles = _roles(plan)
    values = _blob(plan)
    leaked = "gray-lantern" in text
    operation_ok = act == operation or (operation == "follow_up" and act in {"follow_up", "reference_to_prior_speech"})
    if answer == "clarify_ok" and kind == "clarification":
        operation_ok = True
    if answer == "ambiguous_ok" and kind == "clarification":
        operation_ok = True
    role_ok = False
    if operation == "information_question" and topic == "cistern":
        role_ok = "cala" in values and "brin" in values and "cistern" in values
    elif operation == "information_question":
        role_ok = topic in values
    elif operation == "correction" and topic == "reversal":
        role_ok = "brin" in values and "cala" in values and "cistern" in values
    elif operation == "correction" and topic == "slate":
        role_ok = "slate" in values
    else:
        role_ok = operation_ok
    answer_ok = False
    if leaked:
        answer_ok = False
    elif answer == "withhold":
        answer_ok = operation_ok and not leaked and kind in {"unknown", "refusal"}
    elif answer == "cracked":
        answer_ok = operation_ok and "cracked" in text
    elif answer == "cracked_or_clarify":
        answer_ok = "cracked" in text or (operation_ok and kind == "clarification")
    elif answer == "surveyor":
        answer_ok = operation_ok and "surveyor" in text
    elif answer == "someone":
        answer_ok = operation_ok and ("someone" in text or "roster" in text)
    elif answer == "dawn":
        answer_ok = operation_ok and "dawn" in text
    elif answer == "unknown":
        answer_ok = operation_ok and kind in {"unknown", "refusal"} and topic in values
    elif answer == "not_dawn":
        answer_ok = operation_ok and "dawn" not in text
    elif answer in {None, "ambiguous_ok", "clarify_ok"}:
        answer_ok = operation_ok and kind in {"unknown", "refusal", "clarification", "partial"} and not leaked
    return {
        "operation_ok": bool(operation_ok),
        "role_ok": bool(role_ok),
        "answer_ok": bool(answer_ok),
        "leaked": leaked,
        "intended": operation,
        "actual": act,
        "kind": kind,
        "follow": follow,
    }


def summarize(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    scored = [score_turn(row) for row in rows]
    def count(key):
        return sum(bool(item[key]) for item in scored)
    corrections = [item for item, row in zip(scored, rows) if item["intended"] == "correction"]
    follows = [item for item in scored if item["intended"] == "follow_up"]
    return {
        "turns": len(rows),
        "operation": [count("operation_ok"), len(scored)],
        "roles": [count("role_ok"), len(scored)],
        "answers": [count("answer_ok"), len(scored)],
        "corrections": [sum(item["operation_ok"] and item["role_ok"] for item in corrections), len(corrections)],
        "follow_ups": [sum(item["operation_ok"] for item in follows), len(follows)],
        "leaks": count("leaked"),
        "integrity_failures": sum(not all(row["checks"].values()) for row in rows),
    }


if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), indent=2))
