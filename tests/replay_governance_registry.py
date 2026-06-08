"""Static replay governance decision registry.

Governance-only mapping from existing replay drift classes to AV2 governance
decisions. This module intentionally imports only the governance contract and
does not import replay runners, classifiers, dashboards, scorecards, or runtime
game code.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tests.replay_governance_contract import (
    REPLAY_GOVERNANCE_DECISION_ACCEPTED,
    REPLAY_GOVERNANCE_DECISION_BLOCKED,
    REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
)

_PROTECTED_REPLAY_MANIFEST = "docs/testing/protected_replay_manifest.md"
_K4_THRESHOLD_POLICY = "docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md"
_AV1_INVENTORY = "audits/cycle_av_governance_registry_inventory.md"
_STABILITY_CONTRACT = "tests/stability_reporting_contract.py"

_REPLAY_GOVERNANCE_REGISTRY: tuple[dict[str, str], ...] = (
    {
        "drift_bucket": "exact_drift",
        "owner_bucket": "replay_drift_unclassified",
        "category": "replay_drift",
        "severity": "low",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_ACCEPTED,
        "governance_reason": "Exact prose identity is opt-in and not a default protected replay gate.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "route_drift",
        "category": "route",
        "severity": "high",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected route invariant mismatches block when asserted by protected replay.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "speaker_drift",
        "category": "speaker",
        "severity": "critical",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected speaker ownership mismatches block when asserted by protected replay.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "fallback_drift",
        "category": "fallback",
        "severity": "high",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected fallback source, family, or timeframe mismatches block when asserted.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "ownership_drift",
        "category": "fallback",
        "severity": "high",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected fallback ownership/source invariants block when asserted.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "emission_drift",
        "category": "emission",
        "severity": "high",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected final-emission and response-type invariants block when asserted.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "semantic_drift",
        "owner_bucket": "semantic_drift",
        "category": "sanitizer",
        "severity": "critical",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected player-facing semantic violations, including scaffold leakage, block acceptance.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "semantic_drift",
        "owner_bucket": "semantic_drift",
        "category": "semantic_mutation",
        "severity": "high",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Broader semantic degradation signals require review unless tied to an existing protected assertion.",
        "policy_source": f"{_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "structural_drift",
        "owner_bucket": "projection_drift",
        "category": "projection",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Projection health issues outside required protected fields should be investigated, not silently gated.",
        "policy_source": f"{_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "lineage_drift",
        "owner_bucket": "lineage_drift",
        "category": "lineage",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Runtime lineage is diagnostic/read-side and requires review or future monitoring before promotion.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "rerun_scorecard_drift",
        "owner_bucket": "lineage_drift",
        "category": "stability",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Rerun and stability scorecard signals are advisory/report-only and require operator review.",
        "policy_source": f"{_PROTECTED_REPLAY_MANIFEST}; {_STABILITY_CONTRACT}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "unasserted_fallback_telemetry",
        "owner_bucket": "fallback_drift",
        "category": "fallback",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Non-asserted fallback telemetry shifts are warning/review evidence, not independent blockers.",
        "policy_source": f"{_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "unasserted_sanitizer_telemetry",
        "owner_bucket": "emission_drift",
        "category": "sanitizer",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Sanitizer lineage/change evidence without player-visible violation requires review, not automatic blocking.",
        "policy_source": f"{_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "post_gate_mutation_signal",
        "owner_bucket": "emission_drift",
        "category": "emission",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Standalone mutation-path evidence is diagnostic until allowed and denied mutation paths are declared.",
        "policy_source": f"{_K4_THRESHOLD_POLICY}; {_AV1_INVENTORY}",
    },
    {
        "drift_bucket": "unclassified_drift",
        "owner_bucket": "replay_drift_unclassified",
        "category": "replay_drift",
        "severity": "medium",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        "governance_reason": "Unclassified drift should be reviewed because it reduces diagnostic confidence.",
        "policy_source": _AV1_INVENTORY,
    },
)


def replay_governance_registry() -> tuple[Mapping[str, str], ...]:
    """Return the static replay governance registry in deterministic order."""
    return tuple(dict(record) for record in _REPLAY_GOVERNANCE_REGISTRY)


def governance_record_key(record: Mapping[str, Any]) -> tuple[str, str, str, str]:
    """Return the registry identity key for duplicate checks."""
    return (
        str(record.get("drift_bucket") or ""),
        str(record.get("owner_bucket") or ""),
        str(record.get("category") or ""),
        str(record.get("severity") or ""),
    )


def governance_records_for_bucket(drift_bucket: str) -> tuple[Mapping[str, str], ...]:
    """Return registry records matching ``drift_bucket``."""
    bucket = str(drift_bucket or "")
    return tuple(record for record in replay_governance_registry() if record.get("drift_bucket") == bucket)


def governance_records_for_owner_bucket(owner_bucket: str) -> tuple[Mapping[str, str], ...]:
    """Return registry records matching ``owner_bucket``."""
    bucket = str(owner_bucket or "")
    return tuple(record for record in replay_governance_registry() if record.get("owner_bucket") == bucket)
