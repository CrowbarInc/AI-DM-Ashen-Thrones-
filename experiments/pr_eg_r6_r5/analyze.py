"""Paired causal summary for PR-EG-R6-R5. Reads frozen labels and recorded replies."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from experiments.pr_eg_r6_r5.corpus import build_corpus
from experiments.pr_eg_r6_r5.score import attribute_failure, engine_class

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_eg_r6_r5"

FAILURES = {
    "F01": "Wrong operation",
    "F02": "Wrong referent",
    "F03": "Wrong semantic role",
    "F04": "Wrong question proposition",
    "F05": "Relevant source omitted",
    "F06": "Wrong source proposition",
    "F07": "Correspondence false rejection",
    "F08": "Correspondence false acceptance",
    "F09": "NPC knowledge rejection",
    "F10": "Disclosure rejection",
    "F11": "Sufficiency misclassification",
    "F12": "Excessive clarification",
    "F13": "False uncertainty",
    "F14": "Authorized plan inadequate",
    "F15": "Expression distortion",
    "F16": "Final adoption mismatch",
    "F17": "Persistence/state error",
    "F18": "Evaluation disagreement",
}


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _ok(row: dict) -> bool:
    return bool((row.get("score") or {}).get("player_facing_success"))


def _rate(rows: list[dict]) -> dict:
    n = len(rows)
    ok = sum(1 for row in rows if _ok(row))
    return {"n": n, "ok": ok, "rate": (ok / n) if n else None}


def _percentile(values: list[float], p: float):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((p / 100) * (len(ordered) - 1)))))
    return ordered[index]


def _calls(rows: list[dict]) -> dict:
    calls = [call for row in rows for call in (row.get("provider_calls") or []) if isinstance(call, dict)]
    sent = [call for call in calls if call.get("sent") is not False]
    latency = [float(row["latency_ms"]) for row in rows if isinstance(row.get("latency_ms"), (int, float))]
    call_latency = [float(call["latency_ms"]) for call in sent if isinstance(call.get("latency_ms"), (int, float))]

    def total(key: str) -> int:
        return sum(int(call.get(key) or 0) for call in sent)

    by_purpose = Counter(str(call.get("purpose") or "") for call in sent)
    return {
        "turns": len(rows),
        "calls": len(sent),
        "calls_per_turn": (len(sent) / len(rows)) if rows else None,
        "input_tokens": total("input_tokens"),
        "output_tokens": total("output_tokens"),
        "retries": sum(1 for call in calls if call.get("refusal") or call.get("purpose") == "retry"),
        "by_purpose": dict(by_purpose),
        "turn_latency_ms": {
            "mean": (sum(latency) / len(latency)) if latency else None,
            "median": _percentile(latency, 50),
            "p95": _percentile(latency, 95),
            "max": max(latency) if latency else None,
        },
        "call_latency_ms": {
            "mean": (sum(call_latency) / len(call_latency)) if call_latency else None,
            "median": _percentile(call_latency, 50),
            "p95": _percentile(call_latency, 95),
            "max": max(call_latency) if call_latency else None,
        },
    }


def _paired(baseline: dict[str, dict], arm_rows: list[dict]) -> dict:
    both = base_only = arm_only = neither = 0
    compared = 0
    for row in arm_rows:
        base = baseline.get(row.get("turn_id"))
        if not base:
            continue
        compared += 1
        left, right = _ok(base), _ok(row)
        if left and right:
            both += 1
        elif left and not right:
            base_only += 1
        elif right and not left:
            arm_only += 1
        else:
            neither += 1
    return {
        "n": compared,
        "both": both,
        "baseline_only": base_only,
        "arm_only": arm_only,
        "neither": neither,
        "net_fixed": arm_only - base_only,
        "arm_success": (both + arm_only) / compared if compared else None,
        "baseline_success": (both + base_only) / compared if compared else None,
    }


def _interaction(baseline: dict[str, dict], left: dict[str, dict], right: dict[str, dict], combo: dict[str, dict]) -> dict:
    only_combo = either_single = combo_fail = 0
    n = 0
    for turn_id, base in baseline.items():
        if not all(turn_id in pool for pool in (left, right, combo)):
            continue
        n += 1
        if _ok(base):
            continue
        single = _ok(left[turn_id]) or _ok(right[turn_id])
        combined = _ok(combo[turn_id])
        if combined and not single:
            only_combo += 1
        elif single:
            either_single += 1
        else:
            combo_fail += 1
    return {"n": n, "fixed_only_by_combination": only_combo, "fixed_by_a_single_arm": either_single, "still_failed": combo_fail}


def _group(rows: list[dict], key: str) -> dict:
    pools = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if isinstance(value, list):
            for item in value:
                pools[str(item)].append(row)
        else:
            pools[str(value)].append(row)
    return {name: _rate(pool) for name, pool in sorted(pools.items())}


def analyze() -> dict:
    labels = {turn["id"]: turn for _family, turn in ((family, turn) for family in build_corpus() for turn in family["turns"])}
    baseline_rows = _rows(OUT / "baseline.jsonl")
    intervention_rows = _rows(OUT / "interventions.jsonl")
    expression_rows = _rows(OUT / "expression_control.jsonl")
    baseline = {row["turn_id"]: row for row in baseline_rows}
    by_arm = defaultdict(list)
    for row in intervention_rows:
        by_arm[row.get("arm") or ""].append(row)
    by_arm["I10C"] = expression_rows
    failed = []
    first = Counter()
    downstream = Counter()
    reasons = Counter()
    for row in baseline_rows:
        turn = labels.get(row.get("turn_id"))
        if not turn:
            continue
        reasons[str(row.get("reason") or "no_plan")] += 1
        if _ok(row):
            continue
        attribution = attribute_failure(turn, row)
        failed.append({"turn_id": row["turn_id"], "first": attribution["first"], "downstream": attribution["downstream"], "reason": row.get("reason"), "text": row.get("text")})
        first[attribution["first"] or "F18"] += 1
        for code in attribution["downstream"]:
            downstream[code] += 1
    arms = {}
    for name, rows in sorted(by_arm.items()):
        paired = _paired(baseline, rows)
        arms[name] = {"rows": _rate(rows), "paired": paired, "performance": _calls(rows)}
    arm_index = {name: {row["turn_id"]: row for row in rows} for name, rows in by_arm.items()}

    def pool(name: str) -> dict[str, dict]:
        return arm_index.get(name) or {}

    interactions = {
        "intent_referent": _interaction(baseline, pool("I1"), pool("I2"), pool("intent_referent")),
        "question_source": _interaction(baseline, pool("I3"), pool("I5"), pool("question_source")),
        "retrieval_correspondence": _interaction(baseline, pool("I4"), pool("I6"), pool("retrieval_correspondence")),
        "correspondence_sufficiency": _interaction(baseline, pool("I6"), pool("I7"), pool("correspondence_sufficiency")),
        "all_upstream": _interaction(baseline, pool("question_source"), pool("retrieval_correspondence"), pool("I9")),
    }
    security = {
        "baseline_restricted_hits": sum(1 for row in baseline_rows if row.get("restricted_hits")),
        "intervention_restricted_hits": sum(1 for row in intervention_rows if row.get("restricted_hits")),
        "expression_restricted_hits": sum(1 for row in expression_rows if row.get("restricted_hits")),
        "baseline_topic_mutations": sum(1 for row in baseline_rows if (row.get("checks") or {}).get("topics_unchanged") is False),
        "intervention_topic_mutations": sum(1 for row in intervention_rows if (row.get("checks") or {}).get("topics_unchanged") is False),
        "baseline_seal_mismatches": sum(1 for row in baseline_rows if (row.get("checks") or {}).get("exact") is False),
        "intervention_seal_mismatches": sum(1 for row in intervention_rows if (row.get("checks") or {}).get("exact") is False),
    }
    ranked = sorted(
        ((name, info["paired"].get("net_fixed") or 0, info["paired"].get("arm_success"), info["paired"].get("n")) for name, info in arms.items()),
        key=lambda item: (item[1], item[2] or 0),
        reverse=True,
    )
    summary = {
        "baseline": {
            "overall": _rate(baseline_rows),
            "by_partition": _group(baseline_rows, "partition"),
            "by_class": _group(baseline_rows, "answer_class"),
            "by_tag": _group(baseline_rows, "tags"),
            "engine_class_on_success": Counter(engine_class(row.get("plan") or {}) for row in baseline_rows if _ok(row)),
            "reasons": dict(reasons),
            "false_uncertainty": sum(1 for row in baseline_rows if (row.get("score") or {}).get("false_uncertainty")),
            "false_clarification": sum(1 for row in baseline_rows if (row.get("score") or {}).get("false_clarification")),
            "naturalness_mean": (
                sum(int((row.get("score") or {}).get("naturalness") or 0) for row in baseline_rows) / len(baseline_rows)
            ) if baseline_rows else None,
            "performance": _calls(baseline_rows),
        },
        "failed_baseline": len(failed),
        "first_failures": dict(first),
        "downstream_failures": dict(downstream),
        "arms": arms,
        "interactions": interactions,
        "security": security,
        "ranked_net_fixed": [{"arm": name, "net_fixed": net, "arm_success": rate, "n": n} for name, net, rate, n in ranked],
        "failure_names": FAILURES,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "first_failures.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"baseline": result["baseline"]["overall"], "arms": result["ranked_net_fixed"], "first": result["first_failures"]}, indent=2))
