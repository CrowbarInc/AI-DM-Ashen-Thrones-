"""Canonical observational telemetry vocabulary (leaf module).

Owns normalized **phase / action / scope** tokens, stable **reason** list shaping, and the
shared **canonical observational event** envelope from :func:`build_telemetry_event`
(``phase``, ``owner``, ``action``, ``reasons``, ``scope``, ``data``). FEM, stage-diff, and
evaluator modules keep their **raw** dict shapes; projections into this envelope are
read-side comparisons only — **observational**, not legality, routing, retries, repairs, or
scoring.

**Pure leaf:** no imports from gate, evaluator, prompt, or API modules so packaging paths
stay dependency-light.

**Invalid inputs → safe shapes** (``unknown`` phase/action, empty ``reasons``/``data``).
Coercion must not raise; consumers treat ``unknown`` as absent structured signal.

**Projection-time alias notes** (normalize at the domain boundary; do not rename stable FEM keys):

- **Reason families** — Merge raw lists (for example FEM ``failure_reasons`` vs
  ``reason_codes``, evaluator ``reasons``) into canonical ``reasons`` only; no parallel
  reason keys on the event.
- **Status vs pass/fail** — Raw ``checked`` / ``passed`` / ``failed`` / ``status`` /
  ``verdict`` differ by layer; canonical ``action`` is a coarse outcome; fine detail lives in
  bounded ``data`` allow-lists where a projection defines them.
- **Repair flags** — ``repaired``, ``repair_applied``, and ``repair_flags_changed`` are
  different surfaces; normalize per projection instead of overloading one token.
- **Missing / skipped / excluded** — ``missing`` = no signal; ``skipped`` = not evaluated
  this turn; ``excluded_from_scoring`` stays evaluator ``data``, not a stand-in for FEM
  ``skip_reason``.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

# --- Canonical phase labels (gate-adjacent layers map to ``gate`` at FEM projection time). ---

TELEMETRY_PHASE_ENGINE: str = "engine"
TELEMETRY_PHASE_PLANNER: str = "planner"
TELEMETRY_PHASE_GPT: str = "gpt"
TELEMETRY_PHASE_GATE: str = "gate"
TELEMETRY_PHASE_EVALUATOR: str = "evaluator"
TELEMETRY_PHASE_UNKNOWN: str = "unknown"

TELEMETRY_PHASES: frozenset[str] = frozenset(
    {
        TELEMETRY_PHASE_ENGINE,
        TELEMETRY_PHASE_PLANNER,
        TELEMETRY_PHASE_GPT,
        TELEMETRY_PHASE_GATE,
        TELEMETRY_PHASE_EVALUATOR,
        TELEMETRY_PHASE_UNKNOWN,
    }
)

# --- Canonical action labels ---

TELEMETRY_ACTION_APPLIED: str = "applied"
TELEMETRY_ACTION_SKIPPED: str = "skipped"
TELEMETRY_ACTION_REJECTED: str = "rejected"
TELEMETRY_ACTION_OBSERVED: str = "observed"
TELEMETRY_ACTION_REPAIRED: str = "repaired"
TELEMETRY_ACTION_NORMALIZED: str = "normalized"
TELEMETRY_ACTION_EMITTED: str = "emitted"
TELEMETRY_ACTION_MISSING: str = "missing"
TELEMETRY_ACTION_UNKNOWN: str = "unknown"

TELEMETRY_ACTIONS: frozenset[str] = frozenset(
    {
        TELEMETRY_ACTION_APPLIED,
        TELEMETRY_ACTION_SKIPPED,
        TELEMETRY_ACTION_REJECTED,
        TELEMETRY_ACTION_OBSERVED,
        TELEMETRY_ACTION_REPAIRED,
        TELEMETRY_ACTION_NORMALIZED,
        TELEMETRY_ACTION_EMITTED,
        TELEMETRY_ACTION_MISSING,
        TELEMETRY_ACTION_UNKNOWN,
    }
)

# Verb-ish / participle tokens that are not the canonical spelling in ``TELEMETRY_ACTIONS``.
_TELEMETRY_ACTION_ALIASES: dict[str, str] = {
    "apply": TELEMETRY_ACTION_APPLIED,
    "skip": TELEMETRY_ACTION_SKIPPED,
    "reject": TELEMETRY_ACTION_REJECTED,
    "observe": TELEMETRY_ACTION_OBSERVED,
    "observing": TELEMETRY_ACTION_OBSERVED,
    "repair": TELEMETRY_ACTION_REPAIRED,
    "normalize": TELEMETRY_ACTION_NORMALIZED,
    "emit": TELEMETRY_ACTION_EMITTED,
}

# --- Canonical scope labels ---

TELEMETRY_SCOPE_TURN: str = "turn"
TELEMETRY_SCOPE_CLAUSE: str = "clause"
TELEMETRY_SCOPE_SYSTEM: str = "system"
TELEMETRY_SCOPE_UNKNOWN: str = "unknown"

TELEMETRY_SCOPES: frozenset[str] = frozenset(
    {
        TELEMETRY_SCOPE_TURN,
        TELEMETRY_SCOPE_CLAUSE,
        TELEMETRY_SCOPE_SYSTEM,
        TELEMETRY_SCOPE_UNKNOWN,
    }
)


def _norm_token(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    return ""


def normalize_telemetry_phase(value: Any) -> str:
    tok = _norm_token(value)
    if tok in TELEMETRY_PHASES:
        return tok
    return TELEMETRY_PHASE_UNKNOWN


def normalize_telemetry_action(value: Any) -> str:
    tok = _norm_token(value)
    if tok in TELEMETRY_ACTIONS:
        return tok
    mapped = _TELEMETRY_ACTION_ALIASES.get(tok)
    if mapped is not None:
        return mapped
    return TELEMETRY_ACTION_UNKNOWN


def normalize_telemetry_scope(value: Any) -> str:
    tok = _norm_token(value)
    if tok in TELEMETRY_SCOPES:
        return tok
    return TELEMETRY_SCOPE_UNKNOWN


def normalize_reason_list(value: Any) -> list[str]:
    """Return a new stable list of non-empty trimmed strings (order-preserving de-dupe)."""
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        s = str(value).strip()
        return [s] if s else []
    if isinstance(value, Mapping):
        return []
    out: list[str] = []
    if isinstance(value, Iterable):
        for x in value:
            s = str(x).strip()
            if s:
                out.append(s)
    deduped = list(dict.fromkeys(out))
    return deduped


def normalize_owner(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def build_telemetry_event(
    *,
    phase: Any = None,
    owner: Any = None,
    action: Any = None,
    reason: Any = None,
    reasons: Any = None,
    scope: Any = None,
    data: Any = None,
) -> dict[str, Any]:
    """Return one canonical observational event (fixed top-level keys).

    Merges ``reason`` then ``reasons`` into canonical ``reasons`` (de-duplicated). Domain
    code should pass raw lists here instead of adding extra top-level keys on the event.
    """
    merged_reasons: list[str] = []
    if reason is not None:
        merged_reasons.extend(normalize_reason_list(reason))
    merged_reasons.extend(normalize_reason_list(reasons))
    merged_reasons = list(dict.fromkeys(merged_reasons))

    data_out: dict[str, Any]
    if isinstance(data, Mapping):
        data_out = {str(k): v for k, v in data.items()}
    else:
        data_out = {}

    return {
        "phase": normalize_telemetry_phase(phase),
        "owner": normalize_owner(owner),
        "action": normalize_telemetry_action(action),
        "reasons": merged_reasons,
        "scope": normalize_telemetry_scope(scope),
        "data": data_out,
    }
