"""ATGB-03B: durable admission reconciliation and accounting readiness.

Completed-record ledgers are observations, not proof that every dispatch was
recorded. Host performance counters have a different scope and stay untouched.
No provider adapter, payload, retry policy, or game rule is changed here.
"""

from __future__ import annotations

import ast
import json
import hashlib
from pathlib import Path
from typing import Any

ACCOUNTING_VERSION = "ATGB-03B-1"


def inspect_ledger(path: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Reconcile durable records with the existing process-local budget owner.

    A missing file, malformed/partial line, duplicate provider id, or differing
    snapshot is unavailable, never zero. This returns an observed subtotal only;
    Legacy completion-only rows remain observations. Versioned admission events
    can bound attempts when they reconcile with the existing budget owner.
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
        if records and isinstance(records[0], dict) and records[0].get("event") == "initialized":
            return _inspect_lifecycle(records, snapshot)
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


def _inspect_lifecycle(events: list[dict], snapshot: dict) -> dict:
    try:
        first = events[0]
        if first.get("version") != ACCOUNTING_VERSION or not first.get("run_id"):
            raise ValueError("ledger_version_or_identity_unavailable")
        states = {}
        completions = []
        for event in events[1:]:
            if event.get("run_id") != first["run_id"] or event.get("version") != ACCOUNTING_VERSION:
                raise ValueError("ledger_run_identity_disagreement")
            aid = event.get("attempt_id")
            kind = event.get("event")
            if kind == "rejected" and aid and event.get("sent") is False and event.get("refusal"):
                continue  # A refusal is evidence, never an admitted outbound request.
            if not aid or not event.get("purpose") or not event.get("owner") or not event.get("admitted_at"):
                raise ValueError("incomplete_attempt_identity")
            if kind == "admitted" and aid not in states:
                states[aid] = "admitted"
            elif kind == "dispatch_attempted" and states.get(aid) == "admitted":
                states[aid] = "dispatched"
            elif kind == "completed" and states.get(aid) in {"admitted", "dispatched"}:
                if type(event.get("sent")) is not bool or event["sent"] != (states[aid] == "dispatched"):
                    raise ValueError("dispatch_completion_disagreement")
                states[aid] = "completed"
                completions.append(event)
            else:
                raise ValueError("duplicate_or_invalid_lifecycle_event")
        if snapshot.get("events") != events or snapshot.get("records") != completions:
            raise ValueError("ledger_snapshot_disagreement")
        if snapshot.get("requests") != len(states) or snapshot.get("run_id") != first["run_id"]:
            raise ValueError("ledger_counter_disagreement")
        return {"version": ACCOUNTING_VERSION, "status": "recorded",
                "request_upper_bound": len(states),
                "observed_sent_requests": sum(e["event"] == "dispatch_attempted" for e in events),
                "pending_requests": sum(v != "completed" for v in states.values()),
                "reason": "durable_admissions_bound_dispatches",
                "usage_status": "recorded" if snapshot.get("total_tokens") is not None else "unavailable"}
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"version": ACCOUNTING_VERSION, "status": "unavailable", "request_upper_bound": None,
                "observed_sent_requests": None, "reason": str(exc)}


def live_accounting_readiness(repo: Path) -> dict[str, Any]:
    """Verify reviewed owner/core fingerprints and guarded SDK boundaries.

    Fingerprints are review evidence, not regenerated during execution. New,
    missing, changed or unguarded provider sites fail closed, including preflight.
    """
    sites, gaps = [], []
    try:
        manifest = json.loads((repo / "tools/atgb/provider_accounting_integrity.json").read_text())
        expected = manifest["dispatch_owners"]
        if manifest.get("version") != ACCOUNTING_VERSION:
            raise ValueError("accounting_manifest_version")
        # Pin the reviewed application surface as well as known dispatch owners:
        # a new HTTP client or indirect dispatch must not evade the SDK scan.
        sources = {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (repo / "game").rglob("*.py")}
        sources["run.py"] = hashlib.sha256((repo / "run.py").read_bytes()).hexdigest()
        if sources != manifest["application_source_sha256"]:
            gaps.append({"reason": "reviewed_application_surface_changed"})
        for path in sorted((repo / "game").rglob("*.py")):
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
            parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
            for ref in ast.walk(tree):
                if not (isinstance(ref, ast.Attribute) and ref.attr == "create" and
                        isinstance(ref.value, ast.Attribute) and ref.value.attr in {"responses", "completions"}):
                    continue
                fn = parents.get(ref)
                while fn is not None and not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn = parents.get(fn)
                key = path.relative_to(repo).as_posix() + ":" + (fn.name if fn else "<module>")
                parent = parents.get(ref)
                guarded = (isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute)
                           and parent.func.attr == "dispatch" and ref in parent.args)
                digest = hashlib.sha256(ast.get_source_segment(source, fn).encode()).hexdigest() if fn else None
                site = {"path": path.relative_to(repo).as_posix(), "function": fn.name if fn else None,
                        "line": ref.lineno, "guarded": guarded, "owner_key": key}
                sites.append(site)
                if not guarded or expected.get(key) != digest:
                    gaps.append({**site, "reason": "unguarded_unknown_or_changed_dispatch_owner"})
        actual = [s["owner_key"] for s in sites]
        if sorted(actual) != sorted(expected):
            gaps.append({"reason": "dispatch_inventory_changed"})
        core = repo / "game/provider_budget.py"
        if hashlib.sha256(core.read_bytes()).hexdigest() != manifest["budget_sha256"]:
            gaps.append({"reason": "accounting_implementation_changed"})
        if not expected:
            gaps.append({"reason": "empty_dispatch_inventory"})
    except (OSError, ValueError, KeyError, SyntaxError, TypeError) as exc:
        gaps.append({"reason": "accounting_verification_unavailable", "error": type(exc).__name__})
    return {"version": ACCOUNTING_VERSION, "ok": not gaps,
            "stop_reason": "provider_call_ceiling_not_observable" if gaps else None,
            "dispatch_sites": sites, "established_gaps": gaps,
            "reason": "verified_reviewed_lifecycle_coverage" if not gaps else "provider_lifecycle_coverage_unverified",
            "note": "Static scope is current application game package; deterministic dispatch-owner tests supplement fingerprints. No live execution implied."}
