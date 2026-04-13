"""BHC2: upstream-dependent run validity from cached preflight only (BHC1).

Reads ``get_latest_upstream_api_preflight()`` — no extra network probes.
Uses ``upstream_api_preflight_disabled_by_env()`` only to explain empty cache (not as a second classifier).
"""

from __future__ import annotations

from typing import Any

from game.api_upstream_preflight import (
    get_latest_upstream_api_preflight,
    upstream_api_preflight_disabled_by_env,
)


def compute_upstream_dependent_run_gate() -> dict[str, Any]:
    """Return a JSON-serializable gate for manual QA, validation CLIs, and ``/api/new_campaign``.

    Fields (stable keys for reports and API payloads):
    - ``upstream_runtime_healthy``: True / False / None (unknown when no cached preflight)
    - ``preflight_available``: whether a canonical preflight row exists in-process
    - ``startup_run_valid``: whether live-upstream gameplay testing should be treated as valid
    - ``manual_testing_blocked``: hard block signal (only True with cached unhealthy preflight)
    - ``block_reason``: machine-oriented reason string, or None
    - ``preflight_health_class``: from cache, or None
    - ``preflight_checked_at``: from cache ``checked_at``, or None
    """
    latest = get_latest_upstream_api_preflight()
    if latest is not None:
        inv = latest.get("invalidates_upstream_dependent_runs") is True
        hc = latest.get("health_class")
        hc_s = str(hc).strip() if isinstance(hc, str) and hc.strip() else None
        checked = latest.get("checked_at")
        checked_s = str(checked).strip() if isinstance(checked, str) and checked.strip() else None
        return {
            "upstream_runtime_healthy": not inv,
            "preflight_available": True,
            "startup_run_valid": not inv,
            "manual_testing_blocked": inv,
            "block_reason": "upstream_unhealthy_preflight" if inv else None,
            "preflight_health_class": hc_s,
            "preflight_checked_at": checked_s,
        }

    skipped = upstream_api_preflight_disabled_by_env()
    reason = "preflight_skipped_by_env" if skipped else "preflight_not_checked"
    return {
        "upstream_runtime_healthy": None,
        "preflight_available": False,
        "startup_run_valid": False,
        "manual_testing_blocked": False,
        "block_reason": reason,
        "preflight_health_class": None,
        "preflight_checked_at": None,
    }
