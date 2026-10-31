"""ATGB-03A: conservative ledger observations and live accounting readiness.

Completed-record ledgers are observations, not proof that every dispatch was
recorded. Host performance counters have a different scope and stay untouched.
No provider adapter, payload, retry policy, or game rule is changed here.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

ACCOUNTING_VERSION = "ATGB-03A-1"


def inspect_ledger(path: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Reconcile durable records with the existing process-local budget owner.

    A missing file, malformed/partial line, duplicate provider id, or differing
    snapshot is unavailable, never zero. This returns an observed subtotal only;
    it deliberately does not certify coverage or an enforceable upper bound.
    """
    result: dict[str, Any] = {
        "version": ACCOUNTING_VERSION, "status": "unavailable",
        "observed_sent_requests": None, "request_upper_bound": None,
        "reason": None,
    }
    try:
        raw = path.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            raise ValueError("incomplete_ledger_line")
        records = [json.loads(line) for line in raw.splitlines()]
        if any(not isinstance(r, dict) or type(r.get("sent")) is not bool or
               not isinstance(r.get("purpose"), str) or not r["purpose"] for r in records):
            raise ValueError("incomplete_ledger_record")
        ids = [r["request_id"] for r in records if r["sent"] and r.get("request_id")]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_provider_request_id")
        if snapshot.get("records") != records:
            raise ValueError("ledger_snapshot_disagreement")
        count = sum(r["sent"] for r in records)
        if type(snapshot.get("requests")) is not int or snapshot["requests"] != count:
            raise ValueError("ledger_counter_disagreement")
        # A sent failure without usage/id may represent an attempt, but does not
        # establish a complete request lifecycle. Stop instead of deduplicating
        # ambiguous records or using invented token counts.
        if any(r["sent"] and (not r.get("request_id") or r.get("usage_consistent") is not True)
               for r in records):
            raise ValueError("incomplete_sent_request")
        if snapshot.get("stopped"):
            raise ValueError("provider_accounting_stopped")
        result.update(status="recorded", observed_sent_requests=count,
                      reason="observed_subtotal_only_coverage_not_established")
    except (OSError, ValueError, TypeError) as exc:
        result["reason"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    return result


def live_accounting_readiness(repo: Path) -> dict[str, Any]:
    """Fail closed on the established completion-ledger coverage limitations.

    Inventory all currently used Responses dispatch sites. This is a refusal
    audit, not a general static proof of provider coverage. Even a changed or
    empty inventory requires review; there is no caller-supplied bypass flag.
    """
    sites = []
    for path in sorted((repo / "game").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call) and
                     isinstance(n.func, ast.Attribute) and n.func.attr == "create" and
                     isinstance(n.func.value, ast.Attribute) and n.func.value.attr == "responses"]
            for call in calls:
                sites.append({"path": path.relative_to(repo).as_posix(),
                              "function": node.name, "line": call.lineno})
    gaps = []
    for site in sites:
        name = site["function"]
        if name == "_invoke_interpretation_model":
            gaps.append({**site, "reason": "dispatch_without_existing_budget_guard_or_ledger"})
        elif name in {"invoke_candidate_provider", "_invoke_provider"} or site["path"] == "game/unified_semantic_planning.py":
            gaps.append({**site, "reason": "completion_ledger_does_not_cover_dispatch_exceptions"})
    return {
        "version": ACCOUNTING_VERSION, "ok": False,
        "stop_reason": "provider_call_ceiling_not_observable",
        "request_upper_bound": None, "dispatch_sites": sites, "established_gaps": gaps,
        "reason": "ledger_coverage_incomplete" if gaps else "changed_provider_coverage_requires_review",
        "note": "Observed ledger totals cannot authorize live continuation. No host field is replaced.",
    }
