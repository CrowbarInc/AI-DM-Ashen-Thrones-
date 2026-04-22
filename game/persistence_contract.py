"""Runtime persistence envelope contract.

This module defines a *pure* document-envelope schema for runtime persistence.
It contains no game semantics and must not invoke GPT or domain mutation.

Storage owns I/O; this module owns:
- the canonical envelope shape
- deterministic validation + failure categories
- acceptance/normalization rules for legacy (unenveloped) payloads
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Optional, Tuple


PERSISTENCE_FORMAT_VERSION = 1


class PersistenceFailureCategory(str, Enum):
    MISSING_ENVELOPE = "missing_envelope"
    UNSUPPORTED_VERSION = "unsupported_version"
    MALFORMED_PAYLOAD = "malformed_payload"
    INTEGRITY_MISMATCH = "integrity_mismatch"
    WRONG_DOCUMENT_KIND = "wrong_document_kind"


class PersistenceAcceptance(str, Enum):
    ACCEPTED_AS_IS = "accepted_as_is"
    NORMALIZED_FORWARD = "normalized_forward"


@dataclass(frozen=True)
class PersistenceDecision:
    acceptance: PersistenceAcceptance
    reason: str
    category: Optional[PersistenceFailureCategory] = None
    observed_version: Optional[int] = None
    observed_kind: Optional[str] = None


class PersistenceContractError(ValueError):
    def __init__(
        self,
        category: PersistenceFailureCategory,
        message: str,
        *,
        observed_version: Optional[int] = None,
        observed_kind: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.observed_version = observed_version
        self.observed_kind = observed_kind


def _canonical_json_bytes(value: Any) -> bytes:
    # Deterministic canonicalization: sorted keys, no whitespace.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_payload_sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def wrap_runtime_payload(
    *,
    kind: str,
    payload: Dict[str, Any],
    saved_at: str,
    include_integrity: bool = True,
) -> Dict[str, Any]:
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError("kind must be a non-empty string")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    if not isinstance(saved_at, str) or not saved_at.strip():
        raise ValueError("saved_at must be a non-empty string")

    env: Dict[str, Any] = {
        "persistence_version": PERSISTENCE_FORMAT_VERSION,
        "kind": kind.strip(),
        "saved_at": saved_at,
        "payload": payload,
    }
    if include_integrity:
        env["integrity"] = {
            "payload_sha256": compute_payload_sha256(payload),
            "canonicalization": "json/sort_keys,separators",
            "hash": "sha256",
        }
    return env


def is_envelope(data: Any) -> bool:
    return isinstance(data, dict) and "persistence_version" in data and "payload" in data and "kind" in data


def unwrap_and_validate(
    data: Any,
    *,
    expected_kind: str,
    allow_legacy_missing_envelope: bool = True,
    require_integrity_if_present: bool = True,
) -> Tuple[Dict[str, Any], PersistenceDecision]:
    """Return (payload, decision) or raise PersistenceContractError.

    Deterministic behavior:
    - If data is not an envelope:
      - If allow_legacy_missing_envelope and data is a dict -> accept as legacy payload, NORMALIZED_FORWARD.
      - Else -> raise MISSING_ENVELOPE.
    - If envelope version unsupported -> raise UNSUPPORTED_VERSION.
    - If kind mismatch -> raise WRONG_DOCUMENT_KIND.
    - If payload malformed -> raise MALFORMED_PAYLOAD.
    - If integrity present and mismatched -> raise INTEGRITY_MISMATCH.
    """
    exp_kind = str(expected_kind or "").strip()
    if not exp_kind:
        raise ValueError("expected_kind must be a non-empty string")

    if not is_envelope(data):
        if allow_legacy_missing_envelope and isinstance(data, dict):
            return data, PersistenceDecision(
                acceptance=PersistenceAcceptance.NORMALIZED_FORWARD,
                reason="legacy_missing_envelope",
                category=PersistenceFailureCategory.MISSING_ENVELOPE,
                observed_kind=None,
                observed_version=None,
            )
        raise PersistenceContractError(
            PersistenceFailureCategory.MISSING_ENVELOPE,
            "Persistence data is missing the runtime envelope.",
        )

    env = data
    ver_raw = env.get("persistence_version")
    kind_raw = env.get("kind")
    observed_kind = kind_raw.strip() if isinstance(kind_raw, str) else None
    observed_version = int(ver_raw) if isinstance(ver_raw, int) else None

    if not isinstance(ver_raw, int):
        raise PersistenceContractError(
            PersistenceFailureCategory.MALFORMED_PAYLOAD,
            "Envelope persistence_version must be an int.",
            observed_version=observed_version,
            observed_kind=observed_kind,
        )
    if ver_raw != PERSISTENCE_FORMAT_VERSION:
        raise PersistenceContractError(
            PersistenceFailureCategory.UNSUPPORTED_VERSION,
            f"Unsupported persistence_version: {ver_raw}",
            observed_version=ver_raw,
            observed_kind=observed_kind,
        )

    if not isinstance(kind_raw, str) or not kind_raw.strip():
        raise PersistenceContractError(
            PersistenceFailureCategory.MALFORMED_PAYLOAD,
            "Envelope kind must be a non-empty string.",
            observed_version=ver_raw,
            observed_kind=observed_kind,
        )
    if kind_raw.strip() != exp_kind:
        raise PersistenceContractError(
            PersistenceFailureCategory.WRONG_DOCUMENT_KIND,
            f"Wrong document kind: expected {exp_kind}, got {kind_raw.strip()}",
            observed_version=ver_raw,
            observed_kind=kind_raw.strip(),
        )

    payload = env.get("payload")
    if not isinstance(payload, dict):
        raise PersistenceContractError(
            PersistenceFailureCategory.MALFORMED_PAYLOAD,
            "Envelope payload must be a dict.",
            observed_version=ver_raw,
            observed_kind=kind_raw.strip(),
        )

    integrity = env.get("integrity")
    if integrity is not None:
        if not isinstance(integrity, dict):
            raise PersistenceContractError(
                PersistenceFailureCategory.MALFORMED_PAYLOAD,
                "Envelope integrity must be an object when present.",
                observed_version=ver_raw,
                observed_kind=kind_raw.strip(),
            )
        if require_integrity_if_present:
            expected = integrity.get("payload_sha256")
            if not isinstance(expected, str) or not expected.strip():
                raise PersistenceContractError(
                    PersistenceFailureCategory.MALFORMED_PAYLOAD,
                    "Envelope integrity.payload_sha256 must be a non-empty string when integrity is present.",
                    observed_version=ver_raw,
                    observed_kind=kind_raw.strip(),
                )
            actual = compute_payload_sha256(payload)
            if actual != expected.strip():
                raise PersistenceContractError(
                    PersistenceFailureCategory.INTEGRITY_MISMATCH,
                    "Integrity mismatch: payload hash does not match envelope metadata.",
                    observed_version=ver_raw,
                    observed_kind=kind_raw.strip(),
                )

    return payload, PersistenceDecision(
        acceptance=PersistenceAcceptance.ACCEPTED_AS_IS,
        reason="envelope_valid",
        observed_version=ver_raw,
        observed_kind=kind_raw.strip(),
    )

