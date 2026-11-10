"""Score frozen corpora. The holdout file is not an editing target."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
import tracemalloc
from pathlib import Path

from game.consequential_narration_validation import SemanticAuthority, validate_consequential_narration
from tests.pr_play_54_corpus import CASES as PREVIOUS, authority_for
from tests.pr_play_55_development import CASES as DEVELOPMENT

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_PATH = ROOT / "tests" / "pr_play_55_holdout.json"
MANIFEST_PATH = ROOT / "tests" / "pr_play_55_holdout_manifest.json"


def _authority(spec: dict) -> SemanticAuthority:
    return SemanticAuthority(
        observable_scene=tuple(spec.get("observable_scene") or ()),
        authorized_discoveries=tuple(spec.get("authorized_discoveries") or ()),
        authorized_outcomes=tuple(spec.get("authorized_outcomes") or ()),
        restricted=tuple(spec.get("restricted") or ()),
        success=spec.get("success"),
        items_added=tuple(spec.get("items_added") or ()),
        items_removed=tuple(spec.get("items_removed") or ()),
        routes_unlocked=tuple(spec.get("routes_unlocked") or ()),
        objectives_completed=tuple(spec.get("objectives_completed") or ()),
        conditions_applied=tuple(spec.get("conditions_applied") or ()),
        conditions_removed=tuple(spec.get("conditions_removed") or ()),
        dialogue=tuple(spec.get("dialogue") or ()),
    )


def _latency(rows: list[dict]) -> dict:
    samples = [row["latency_ms"] for row in rows]
    return {
        "average_ms": round(statistics.fmean(samples), 4),
        "median_ms": round(statistics.median(samples), 4),
        "maximum_ms": round(max(samples), 4),
        "count": len(samples),
    }


def _score(rows: list[dict]) -> dict:
    def group(name):
        return [row for row in rows if row["group"] == name]

    fabrications = group("fabrication") + group("negative")
    harmless = group("harmless") + group("positive")
    paraphrases = group("paraphrase")
    ambiguous = group("ambiguous")
    critical = [row for row in fabrications if row["expected"] == "FAIL" and row["actual"] == "PASS"]
    fabrication_fail = [row for row in fabrications if row["actual"] == "FAIL"]
    fabrication_review = [row for row in fabrications if row["actual"] == "REVIEW_REQUIRED"]
    harmless_fail = [row for row in harmless if row["actual"] == "FAIL"]
    harmless_review = [row for row in harmless if row["actual"] == "REVIEW_REQUIRED"]
    paraphrase_pass = [row for row in paraphrases if row["actual"] == "PASS"]
    reviews = [row for row in rows if row["actual"] == "REVIEW_REQUIRED"]
    errors = [row for row in rows if row["actual"] == "VALIDATION_ERROR"]
    correct = [row for row in rows if row["actual"] == row["expected"]]
    matrix = {}
    for row in rows:
        key = row["expected"] + "->" + row["actual"]
        matrix[key] = matrix.get(key, 0) + 1
    return {
        "total": len(rows),
        "fabrication_total": len(fabrications),
        "fabrication_fail": len(fabrication_fail),
        "fabrication_review": len(fabrication_review),
        "fabrication_pass": len(critical),
        "critical_false_negative_ids": [row["id"] for row in critical],
        "harmless_total": len(harmless),
        "harmless_false_fail_ids": [row["id"] for row in harmless_fail],
        "harmless_false_review_ids": [row["id"] for row in harmless_review],
        "paraphrase_total": len(paraphrases),
        "paraphrase_pass": len(paraphrase_pass),
        "ambiguous_total": len(ambiguous),
        "ambiguous_correct": sum(1 for row in ambiguous if row["actual"] == "REVIEW_REQUIRED"),
        "review_required": len(reviews),
        "validation_errors": len(errors),
        "correct": len(correct),
        "mismatch_ids": [row["id"] for row in rows if row["actual"] != row["expected"]],
        "confusion": matrix,
        "latency": _latency(rows),
    }


def score_development() -> dict:
    rows = []
    for case in DEVELOPMENT:
        started = time.perf_counter()
        actual = validate_consequential_narration(case["text"], authority_for(case["authority"]))
        rows.append({
            "id": case["id"],
            "group": case["group"],
            "category": case["category"],
            "text": case["text"],
            "expected": case["expected"],
            "actual": actual["decision"],
            "reasons": actual["reasons"],
            "reason_codes": [claim.get("reason_code") for claim in actual["claims"] if claim.get("reason_code")],
            "provider_requests": actual["provider_requests"],
            "latency_ms": (time.perf_counter() - started) * 1000,
        })
    summary = _score(rows)
    summary["provider_requests"] = sum(row["provider_requests"] for row in rows)
    summary["rows"] = rows
    return summary


def repeated_development_latency(repeats: int = 30) -> dict:
    samples = []
    tracemalloc.start()
    started = time.perf_counter()
    for _ in range(repeats):
        for case in DEVELOPMENT:
            one = time.perf_counter()
            validate_consequential_narration(case["text"], authority_for(case["authority"]))
            samples.append((time.perf_counter() - one) * 1000)
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "repeats": repeats,
        "validations": len(samples),
        "average_ms": round(statistics.fmean(samples), 4),
        "median_ms": round(statistics.median(samples), 4),
        "maximum_ms": round(max(samples), 4),
        "throughput_per_second": round(len(samples) / elapsed, 1) if elapsed else None,
        "tracemalloc_peak_bytes": peak,
        "provider_requests": 0,
        "additional_tokens": 0,
    }


def load_holdout() -> tuple[dict, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw = HOLDOUT_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != manifest["sha256"]:
        raise RuntimeError("holdout hash mismatch; classification aborted")
    return json.loads(raw), manifest


def score_holdout() -> dict:
    """One classification pass over the frozen file."""
    payload, manifest = load_holdout()
    authorities = payload["authorities"]
    rows = []
    for case in payload["cases"]:
        started = time.perf_counter()
        actual = validate_consequential_narration(case["text"], _authority(authorities[case["authority"]]))
        rows.append({
            "id": case["id"],
            "group": case["group"],
            "category": case["category"],
            "text": case["text"],
            "expected": case["expected"],
            "actual": actual["decision"],
            "reasons": actual["reasons"],
            "reason_codes": [claim.get("reason_code") for claim in actual["claims"] if claim.get("reason_code")],
            "provider_requests": actual["provider_requests"],
            "latency_ms": (time.perf_counter() - started) * 1000,
        })
    summary = _score(rows)
    summary["provider_requests"] = sum(row["provider_requests"] for row in rows)
    summary["manifest_sha256"] = manifest["sha256"]
    summary["rows"] = rows
    return summary


def score_previous() -> dict:
    rows = []
    for case in PREVIOUS:
        started = time.perf_counter()
        actual = validate_consequential_narration(case["text"], authority_for(case["authority"]))
        rows.append({
            "id": case["id"],
            "group": case["group"],
            "expected": case["expected"],
            "actual": actual["decision"],
            "latency_ms": (time.perf_counter() - started) * 1000,
            "provider_requests": actual["provider_requests"],
        })
    negatives = [row for row in rows if row["group"] == "negative"]
    positives = [row for row in rows if row["group"] in {"positive", "paraphrase"}]
    paraphrases = [row for row in rows if row["group"] == "paraphrase"]
    return {
        "total": len(rows),
        "fabrication_fail": sum(1 for row in negatives if row["actual"] == "FAIL"),
        "fabrication_total": len(negatives),
        "critical_false_negatives": [row["id"] for row in negatives if row["actual"] == "PASS"],
        "harmless_and_paraphrase_not_pass": [
            row["id"] for row in positives if row["actual"] != "PASS"
        ],
        "paraphrase_pass": sum(1 for row in paraphrases if row["actual"] == "PASS"),
        "paraphrase_total": len(paraphrases),
        "review_required": sum(1 for row in rows if row["actual"] == "REVIEW_REQUIRED"),
        "latency": _latency(rows),
        "provider_requests": sum(row["provider_requests"] for row in rows),
    }
