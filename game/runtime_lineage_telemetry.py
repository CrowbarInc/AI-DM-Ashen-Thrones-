"""Read-side vocabulary for countable runtime lineage events.

This leaf module normalizes already-observed runtime evidence into compact,
JSON-serializable event dictionaries. It does not inspect live runtime objects,
select fallbacks, apply repairs, mutate emitted text, or influence scoring.

H2/H3 wire finalized fallback/gate-outcome/speaker-repair/mutation FEM reads through
``game.final_emission_meta.build_fem_runtime_lineage_events``. Future read-side
consumers may derive additional events from stage-diff, post-emission state, or
state-mutation metadata after those owners have already recorded decisions.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

from game.telemetry_vocab import normalize_owner, normalize_reason_list

RUNTIME_LINEAGE_EVENT_TYPE: str = "runtime_lineage"

RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED: str = "fallback_selected"
RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR: str = "speaker_repair"
RUNTIME_LINEAGE_EVENT_MUTATION: str = "mutation"
RUNTIME_LINEAGE_EVENT_GATE_OUTCOME: str = "gate_outcome"
RUNTIME_LINEAGE_EVENT_UNKNOWN: str = "unknown"

RUNTIME_LINEAGE_EVENT_KINDS: frozenset[str] = frozenset(
    {
        RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED,
        RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR,
        RUNTIME_LINEAGE_EVENT_MUTATION,
        RUNTIME_LINEAGE_EVENT_GATE_OUTCOME,
    }
)

RUNTIME_LINEAGE_STAGE_ENGINE: str = "engine"
RUNTIME_LINEAGE_STAGE_PLANNER: str = "planner"
RUNTIME_LINEAGE_STAGE_GPT: str = "gpt"
RUNTIME_LINEAGE_STAGE_RETRY: str = "retry"
RUNTIME_LINEAGE_STAGE_GATE: str = "gate"
RUNTIME_LINEAGE_STAGE_SANITIZER: str = "sanitizer"
RUNTIME_LINEAGE_STAGE_POST_EMISSION: str = "post_emission"
RUNTIME_LINEAGE_STAGE_UNKNOWN: str = "unknown"

RUNTIME_LINEAGE_STAGES: frozenset[str] = frozenset(
    {
        RUNTIME_LINEAGE_STAGE_ENGINE,
        RUNTIME_LINEAGE_STAGE_PLANNER,
        RUNTIME_LINEAGE_STAGE_GPT,
        RUNTIME_LINEAGE_STAGE_RETRY,
        RUNTIME_LINEAGE_STAGE_GATE,
        RUNTIME_LINEAGE_STAGE_SANITIZER,
        RUNTIME_LINEAGE_STAGE_POST_EMISSION,
    }
)

_TOKEN_BREAKS_RE = re.compile(r"[\s-]+")
_TOKEN_UNSAFE_RE = re.compile(r"[^a-z0-9_.]+")


def _normalize_token(value: Any) -> str | None:
    """Normalize one bounded vocabulary token while preserving dotted names."""
    if not isinstance(value, str):
        return None
    token = _TOKEN_BREAKS_RE.sub("_", value.strip().lower())
    token = _TOKEN_UNSAFE_RE.sub("_", token).strip("_")
    return token or None


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def normalize_runtime_lineage_event_kind(value: Any) -> str:
    token = _normalize_token(value)
    if token in RUNTIME_LINEAGE_EVENT_KINDS:
        return token
    return RUNTIME_LINEAGE_EVENT_UNKNOWN


def normalize_runtime_lineage_stage(value: Any) -> str:
    token = _normalize_token(value)
    if token in RUNTIME_LINEAGE_STAGES:
        return token
    return RUNTIME_LINEAGE_STAGE_UNKNOWN


def build_recurrence_key(
    *,
    event_kind: Any = None,
    stage: Any = None,
    owner: Any = None,
    fallback_kind: Any = None,
    repair_kind: Any = None,
    mutation_kind: Any = None,
    gate_path: Any = None,
) -> str:
    """Build a stable key for future cross-turn aggregation.

    The detail token preference is fallback, repair, mutation, then gate path,
    matching the most specific current lineage signal when several are present.
    """
    kind = RUNTIME_LINEAGE_EVENT_UNKNOWN
    for value in (fallback_kind, repair_kind, mutation_kind, gate_path):
        token = _normalize_token(value)
        if token:
            kind = token
            break
    normalized_owner = normalize_owner(owner) or "unknown"
    return ":".join(
        (
            normalize_runtime_lineage_event_kind(event_kind),
            normalize_runtime_lineage_stage(stage),
            normalized_owner,
            kind,
        )
    )


def make_runtime_lineage_event(
    *,
    event_kind: Any = None,
    stage: Any = None,
    owner: Any = None,
    source: Any = None,
    gate_path: Any = None,
    mutation_kind: Any = None,
    fallback_kind: Any = None,
    repair_kind: Any = None,
    notes: Any = None,
) -> dict[str, Any]:
    """Return one compact normalized runtime lineage event."""
    event_kind_out = normalize_runtime_lineage_event_kind(event_kind)
    stage_out = normalize_runtime_lineage_stage(stage)
    owner_out = normalize_owner(owner)
    gate_path_out = _normalize_token(gate_path)
    mutation_kind_out = _normalize_token(mutation_kind)
    fallback_kind_out = _normalize_token(fallback_kind)
    repair_kind_out = _normalize_token(repair_kind)
    generated_key = build_recurrence_key(
        event_kind=event_kind_out,
        stage=stage_out,
        owner=owner_out,
        fallback_kind=fallback_kind_out,
        repair_kind=repair_kind_out,
        mutation_kind=mutation_kind_out,
        gate_path=gate_path_out,
    )
    return {
        "event_type": RUNTIME_LINEAGE_EVENT_TYPE,
        "event_kind": event_kind_out,
        "stage": stage_out,
        "owner": owner_out,
        "source": _normalize_text(source),
        "gate_path": gate_path_out,
        "mutation_kind": mutation_kind_out,
        "fallback_kind": fallback_kind_out,
        "repair_kind": repair_kind_out,
        "recurrence_key": generated_key,
        "notes": normalize_reason_list(notes),
    }


def normalize_runtime_lineage_events(events: Any) -> list[dict[str, Any]]:
    """Normalize a sequence of event-like mappings without mutating inputs."""
    if isinstance(events, (str, bytes, Mapping)) or not isinstance(events, Iterable):
        return []
    out: list[dict[str, Any]] = []
    for raw in events:
        if not isinstance(raw, Mapping):
            continue
        out.append(
            make_runtime_lineage_event(
                event_kind=raw.get("event_kind"),
                stage=raw.get("stage"),
                owner=raw.get("owner"),
                source=raw.get("source"),
                gate_path=raw.get("gate_path"),
                mutation_kind=raw.get("mutation_kind"),
                fallback_kind=raw.get("fallback_kind"),
                repair_kind=raw.get("repair_kind"),
                notes=raw.get("notes"),
            )
        )
    return out
