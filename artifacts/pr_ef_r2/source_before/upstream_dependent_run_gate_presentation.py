"""BHC3: operator-facing summaries derived only from ``upstream_dependent_run_gate`` payloads.

No policy decisions, no extra network I/O, no secrets. Safe to attach to API responses and artifacts.
"""

from __future__ import annotations

from typing import Any, Mapping

# Stable vocabulary for operators (matches task spec; do not rename casually).
DISPOSITION_HEALTHY = "healthy"
DISPOSITION_BLOCKED_UNHEALTHY = "blocked_unhealthy_preflight"
DISPOSITION_PREFLIGHT_SKIPPED = "preflight_skipped_by_env"
DISPOSITION_PREFLIGHT_NOT_CHECKED = "preflight_not_checked"


def upstream_gate_disposition(gate: Mapping[str, Any]) -> str:
    """High-level bucket from canonical gate fields only."""
    if gate.get("manual_testing_blocked") is True:
        return DISPOSITION_BLOCKED_UNHEALTHY
    if gate.get("preflight_available") is True and gate.get("startup_run_valid") is True:
        return DISPOSITION_HEALTHY
    br = gate.get("block_reason")
    if br == "preflight_skipped_by_env":
        return DISPOSITION_PREFLIGHT_SKIPPED
    if br == "preflight_not_checked":
        return DISPOSITION_PREFLIGHT_NOT_CHECKED
    # Defensive: unknown gate shape still maps to “not established”.
    return DISPOSITION_PREFLIGHT_NOT_CHECKED


def _action_hint_for_health_class(hc: str | None) -> str | None:
    if not hc or not isinstance(hc, str):
        return None
    key = hc.strip().lower()
    if key == "insufficient_quota":
        return "Add credits or enable auto-recharge, then retry."
    if key == "auth_failure":
        return "Verify API key and how it is loaded (environment / .env)."
    if key == "permission_failure":
        return "Verify project and model permissions for this API key."
    if key == "model_access_failure":
        return "Verify model access (project allowlist) or pick an available model."
    if key == "transient_upstream_failure":
        return "Transient upstream error — retry when the API is reachable."
    if key == "healthy":
        return None
    if key == "unknown_failure":
        return "Inspect cached preflight fields (status_code / error_code); fix upstream configuration."
    return None


def action_hint_for_gate(gate: Mapping[str, Any]) -> str:
    """Single-line operator guidance; never includes secrets or raw excerpts."""
    disp = upstream_gate_disposition(gate)
    hc = gate.get("preflight_health_class")
    hc_s = str(hc).strip() if isinstance(hc, str) else None

    if disp == DISPOSITION_BLOCKED_UNHEALTHY:
        hint = _action_hint_for_health_class(hc_s)
        if hint:
            return hint
        return "Fix upstream API health (see startup [API preflight] block), then retry."

    if disp == DISPOSITION_PREFLIGHT_SKIPPED:
        return (
            "Unset ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT (or set to 0) so startup preflight "
            "runs for live manual testing."
        )

    if disp == DISPOSITION_PREFLIGHT_NOT_CHECKED:
        return (
            "Run or inspect startup upstream API preflight before treating results as live-upstream gameplay evidence."
        )

    if disp == DISPOSITION_HEALTHY:
        return "Upstream preflight cache is healthy; live-upstream gameplay conclusions may be valid."

    return "Review upstream_dependent_run_gate fields and startup preflight logs."


def compact_operator_banner(gate: Mapping[str, Any]) -> str | None:
    """One-line banner; None when disposition is healthy (avoid noisy headers)."""
    disp = upstream_gate_disposition(gate)
    if disp == DISPOSITION_HEALTHY:
        return None
    hc = gate.get("preflight_health_class")
    hc_s = str(hc).strip() if isinstance(hc, str) and str(hc).strip() else None
    br = gate.get("block_reason")
    br_s = str(br).strip() if isinstance(br, str) and str(br).strip() else None

    if disp == DISPOSITION_BLOCKED_UNHEALTHY:
        detail = hc_s or br_s or "upstream_unhealthy"
        return f"UPSTREAM RUN GATE: BLOCKED - {detail} - gameplay testing invalid"

    if disp == DISPOSITION_PREFLIGHT_SKIPPED:
        return "UPSTREAM RUN GATE: WARNING - preflight skipped by env - live-upstream conclusions not established"

    if disp == DISPOSITION_PREFLIGHT_NOT_CHECKED:
        return "UPSTREAM RUN GATE: WARNING - preflight not checked - live-upstream conclusions not established"

    return f"UPSTREAM RUN GATE: WARNING - {br_s or 'unknown'} - review gate output"


def build_upstream_dependent_run_gate_operator(gate: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-serializable operator mirror; derived only from canonical gate keys."""
    disp = upstream_gate_disposition(gate)
    banner = compact_operator_banner(gate)
    return {
        "upstream_gate_disposition": disp,
        "startup_run_valid": bool(gate.get("startup_run_valid")),
        "manual_testing_blocked": bool(gate.get("manual_testing_blocked")),
        "upstream_runtime_healthy": gate.get("upstream_runtime_healthy"),
        "preflight_available": bool(gate.get("preflight_available")),
        "preflight_health_class": gate.get("preflight_health_class"),
        "preflight_checked_at": gate.get("preflight_checked_at"),
        "block_reason": gate.get("block_reason"),
        "gameplay_conclusions_valid": bool(gate.get("startup_run_valid")),
        "action_hint": action_hint_for_gate(gate),
        "compact_banner": banner,
    }


def print_upstream_gate_startup_operator_summary(gate: Mapping[str, Any]) -> None:
    """Stdout lines after ``log_upstream_api_preflight_at_startup()`` (developer-facing)."""
    op = build_upstream_dependent_run_gate_operator(gate)
    disp = op["upstream_gate_disposition"]
    if disp == DISPOSITION_HEALTHY:
        print(
            "[upstream_dependent_run_gate] healthy - startup_run_valid=true; "
            "preflight_available=true; live-upstream gameplay evidence may be treated as valid.",
            flush=True,
        )
        return
    b = op.get("compact_banner")
    if isinstance(b, str) and b.strip():
        print(f"[upstream_dependent_run_gate] {b.strip()}", flush=True)
    hint = op.get("action_hint")
    if isinstance(hint, str) and hint.strip():
        print(f"[upstream_dependent_run_gate] action_hint: {hint.strip()}", flush=True)
