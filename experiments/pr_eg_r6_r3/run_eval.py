"""Run the frozen A/B/C comparison. One official run, no prompt retry.

The validation and holdout hash is written before the first provider call.
A later edit to the corpus or adapters aborts rather than mixing tunings.
"""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts" / "pr_eg_r6_r3"
CODE_FILES = [
    "experiments/pr_eg_r6_r3/corpus.py",
    "experiments/pr_eg_r6_r3/common.py",
    "experiments/pr_eg_r6_r3/architecture_a.py",
    "experiments/pr_eg_r6_r3/architecture_b.py",
    "experiments/pr_eg_r6_r3/architecture_c.py",
    "experiments/pr_eg_r6_r3/CONTRACT.md",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(cases: list[dict]) -> str:
    return json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def manifest_body(cases: list[dict]) -> dict:
    partitions = {}
    for name in ("development", "validation", "holdout"):
        chosen = [case for case in cases if case["partition"] == name]
        partitions[name] = {
            "count": len(chosen),
            "sha256": hashlib.sha256(_canonical(chosen).encode("utf-8")).hexdigest(),
            "ids": [case["id"] for case in chosen],
        }
    return {
        "corpus_sha256": hashlib.sha256(_canonical(cases).encode("utf-8")).hexdigest(),
        "partitions": partitions,
        "code": {path: _sha(ROOT / path) for path in CODE_FILES},
        "decision_rule": (
            "Recommend an architecture only if frozen-holdout paired net gain is at least 8 "
            "on correction success or follow-up success or referent binding, validation moves "
            "the same direction by at least 5, no core holdout metric loses more than 3, "
            "security leaks are zero, and the gain is not a keyword classifier."
        ),
    }


def _adapters():
    from experiments.pr_eg_r6_r3.architecture_a import run as run_a
    from experiments.pr_eg_r6_r3.architecture_b import run as run_b
    from experiments.pr_eg_r6_r3.architecture_c import run as run_c
    return {"A": run_a, "B": run_b, "C": run_c}


def _execute(architecture: str, case: dict) -> dict:
    from experiments.pr_eg_r6_r3.common import earliest_failure, score_case

    try:
        result = _adapters()[architecture](case)
    except Exception as exc:  # noqa: BLE001 - one case must not abort the comparison
        result = {
            "architecture": architecture, "calls": 1, "malformed": True, "raw": "",
            "usage": {}, "latency_ms": 0, "restricted_leaks": [], "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-800],
            "normalized": {"operation": "malformed", "validation": "rejected", "response_class": "unknown",
                           "roles": {}, "malformed": True, "referent_target": "", "relationship": "",
                           "requested_role": "", "temporal": "", "spatial": "", "negated": False,
                           "follow_up": "", "ambiguity": False, "disclosure_granted": False,
                           "authorized_text": "", "selected_source_ids": [], "candidate_available": None},
        }
    normalized = dict(result.get("normalized") or {})
    normalized["restricted_leaks"] = list(result.get("restricted_leaks") or [])
    normalized["malformed"] = bool(result.get("malformed") or normalized.get("malformed"))
    scores = score_case(case, normalized)
    failure = earliest_failure(case, normalized, scores)
    usage = result.get("usage") or {}
    return {
        "case_id": case["id"], "partition": case["partition"], "tags": case["tags"],
        "architecture": architecture, "utterance": case["utterance"],
        "intended_operation": case["intended"]["operation"],
        "raw": result.get("raw") or "", "proposal": result.get("proposal"),
        "normalized": normalized, "scores": scores, "failure": failure,
        "usage": {key: usage.get(key) for key in ("input_tokens", "output_tokens", "total_tokens", "latency_ms")},
        "latency_ms": result.get("latency_ms"), "calls": result.get("calls") or 1,
        "restricted_leaks": result.get("restricted_leaks") or [], "error": result.get("error") or "",
    }


def _rate(rows, field):
    values = [row["scores"][field] for row in rows if row["scores"].get(field) is not None]
    return {"count": sum(bool(value) for value in values), "denominator": len(values)}


def _paired(rows, left, right, field):
    index = {(row["architecture"], row["case_id"]): row for row in rows}
    both = only_left = only_right = neither = 0
    for case_id in sorted({row["case_id"] for row in rows}):
        a = index.get((left, case_id))
        b = index.get((right, case_id))
        if not a or not b:
            continue
        av = a["scores"].get(field)
        bv = b["scores"].get(field)
        if av is None or bv is None:
            continue
        if av and bv:
            both += 1
        elif av and not bv:
            only_left += 1
        elif bv and not av:
            only_right += 1
        else:
            neither += 1
    return {"both": both, "only_" + left: only_left, "only_" + right: only_right, "neither": neither,
            "net_" + right + "_minus_" + left: only_right - only_left}


def summarize(rows: list[dict]) -> dict:
    summary = {"by_architecture": {}, "paired": {}, "by_partition": {}}
    fields = ["operation_correct", "referent_correct", "roles_correct", "correction_success",
              "follow_up_success", "false_clarification", "clarification_success", "meaning_success",
              "malformed", "security_pass", "source_correct", "selection_correct"]
    for architecture in ("A", "B", "C"):
        chosen = [row for row in rows if row["architecture"] == architecture]
        summary["by_architecture"][architecture] = {field: _rate(chosen, field) for field in fields}
        latencies = sorted(row["latency_ms"] or 0 for row in chosen)
        inputs = [row["usage"].get("input_tokens") or 0 for row in chosen]
        outputs = [row["usage"].get("output_tokens") or 0 for row in chosen]
        summary["by_architecture"][architecture]["latency_ms_mean"] = round(sum(latencies) / len(latencies), 1) if latencies else 0
        summary["by_architecture"][architecture]["latency_ms_p95"] = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0
        summary["by_architecture"][architecture]["input_tokens_mean"] = round(sum(inputs) / len(inputs), 1) if inputs else 0
        summary["by_architecture"][architecture]["output_tokens_mean"] = round(sum(outputs) / len(outputs), 1) if outputs else 0
        summary["by_architecture"][architecture]["calls"] = sum(row["calls"] for row in chosen)
    for partition in ("development", "validation", "holdout"):
        summary["by_partition"][partition] = {}
        for architecture in ("A", "B", "C"):
            chosen = [row for row in rows if row["architecture"] == architecture and row["partition"] == partition]
            summary["by_partition"][partition][architecture] = {
                field: _rate(chosen, field) for field in (
                    "meaning_success", "correction_success", "follow_up_success", "referent_correct",
                    "roles_correct", "operation_correct", "false_clarification", "security_pass", "malformed")
            }
    core = ["correction_success", "follow_up_success", "referent_correct", "roles_correct", "meaning_success"]
    for partition in ("validation", "holdout", "development"):
        chosen = [row for row in rows if row["partition"] == partition]
        summary["paired"][partition] = {
            f"{left}_vs_{right}": {field: _paired(chosen, left, right, field) for field in core}
            for left, right in (("A", "B"), ("A", "C"), ("B", "C"))
        }
    return summary


def main():
    from experiments.pr_eg_r6_r3.corpus import cases

    smoke = "--smoke" in sys.argv
    official = not smoke
    loaded = cases()
    OUT.mkdir(parents=True, exist_ok=True)
    body = manifest_body(loaded)
    freeze_path = OUT / "freeze.json"
    if official:
        if freeze_path.exists():
            existing = json.loads(freeze_path.read_text(encoding="utf-8"))
            if existing.get("corpus_sha256") != body["corpus_sha256"] or existing.get("code") != body["code"]:
                raise SystemExit("Freeze/code hash changed after the official manifest. Refusing to mix runs.")
        else:
            freeze_path.write_text(json.dumps(body, indent=2), encoding="utf-8")
            for name in ("development", "validation", "holdout"):
                chosen = [case for case in loaded if case["partition"] == name]
                (OUT / f"{name}_cases.json").write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    selected = [case for case in loaded if case["id"] == "D01"] if smoke else loaded
    architectures = ("A", "B", "C")
    result_path = OUT / ("smoke_results.jsonl" if smoke else "per_case_results.jsonl")
    done = set()
    if result_path.exists() and official:
        for line in result_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done.add((row["architecture"], row["case_id"]))
    jobs = [(architecture, case) for case in selected for architecture in architectures if (architecture, case["id"]) not in done]
    print(f"jobs {len(jobs)} smoke={smoke}", flush=True)
    with result_path.open("a", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=1 if smoke else 4) as pool:
            futures = {pool.submit(_execute, architecture, case): (architecture, case["id"]) for architecture, case in jobs}
            for future in as_completed(futures):
                row = future.result()
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                score = row["scores"]["meaning_success"]
                print(f"{row['architecture']} {row['case_id']} meaning={score} op={row['normalized'].get('operation')} err={row['error'][:80]}", flush=True)
    if official:
        rows = [json.loads(line) for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        (OUT / "summary.json").write_text(json.dumps(summarize(rows), indent=2), encoding="utf-8")
        print("summary written", len(rows), flush=True)


if __name__ == "__main__":
    main()
