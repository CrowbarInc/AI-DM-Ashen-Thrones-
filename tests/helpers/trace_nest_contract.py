"""CF4 — trace nest and dotted protected path contract (read-side).

Documents the four dotted protected registry paths, three trace containers,
and diagnostic-only trace keys on the observed turn.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tests.helpers.golden_replay_projection_registry import (
    _PROTECTED_EXTRACTION_SPECS,
)
from tests.helpers.golden_replay_projection_presence import (
    _TRACE_CONTAINER_RAW_PRESENCE,
    _TRACE_CONTAINER_UNAVAILABLE_KEYS,
)
from tests.helpers.golden_replay_projection_fields import (
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_observation_flat_field_paths,
)

TracePathClassification = Literal[
    "trace_derived",
    "trace_normalized_nest",
    "diagnostic_only",
]

_TRACE_ASSEMBLY_OWNER = "tests.helpers.golden_replay_projection.project_turn_observation"
_TRACE_SOURCE_OWNER = "tests.helpers.golden_replay_projection_extractors._trace_from_payload_or_snapshot"
_LOOKUP_OWNER = "tests.helpers.golden_replay_projection_presence.lookup_observation_path"
_UNAVAILABLE_OWNER = "tests.helpers.golden_replay_projection_presence._unavailable_paths_for_projection"
_REPRESENTATION_OWNER = "tests.helpers.golden_replay_projection_presence.protected_path_is_represented_in_observed_turn"


@dataclass(frozen=True)
class DottedProtectedPathRow:
    protected_path: str
    parent_container: str
    source_path: str
    projection_owner: str
    extraction_owner: str
    test_owner: str
    classification: TracePathClassification
    projection_rule: str
    notes: str


@dataclass(frozen=True)
class TraceContainerRow:
    container_key: str
    observed_key: str
    projection_owner: str
    extraction_owner: str
    unavailable_when: str
    raw_presence_key: str
    protected_leaf_paths: tuple[str, ...]
    diagnostic_keys: tuple[str, ...]


def dotted_protected_field_paths() -> tuple[str, ...]:
    """Return sorted protected registry paths containing a dot."""
    return tuple(path for path in protected_observation_field_paths() if "." in path)


def flat_protected_field_paths() -> tuple[str, ...]:
    """Return sorted flat (non-dotted) protected registry paths."""
    return protected_observation_flat_field_paths()


def build_dotted_path_matrix() -> tuple[DottedProtectedPathRow, ...]:
    rows: list[DottedProtectedPathRow] = []
    for path in dotted_protected_field_paths():
        spec = _PROTECTED_EXTRACTION_SPECS[path]
        leaf = path.split(".")[-1]
        container = spec.trace_container or ""
        parent = f"trace.{container}" if container else "trace"
        if container == "social_contract_trace":
            source = "payload.debug_traces[].turn_trace.social_contract_trace.{leaf}"
            classification: TracePathClassification = "trace_normalized_nest"
            rule = (
                "Extract social_contract_trace from turn_trace; project as "
                f"observed.trace.{container}.{leaf}"
            )
            notes = "Source nested under turn_trace; observed nest flattens to trace sibling"
        else:
            source = f"payload.debug_traces[].canonical_entry.{leaf} or snap.debug.last_debug_trace"
            classification = "trace_derived"
            rule = f"Copy trace.canonical_entry.{leaf} into observed.trace.canonical_entry"
            notes = "Canonical entry leaves are 1:1 from debug trace"
        rows.append(
            DottedProtectedPathRow(
                protected_path=path,
                parent_container=parent,
                source_path=source.format(leaf=leaf),
                projection_owner=_TRACE_ASSEMBLY_OWNER,
                extraction_owner=(
                    "extractor spec owner: "
                    f"tests.helpers.golden_replay_projection_registry._PROTECTED_EXTRACTION_SPECS[{path!r}] "
                    f"trace_container={container!r}"
                ),
                test_owner="test_cf4_trace_nest_dotted_path_contract.py",
                classification=classification,
                projection_rule=rule,
                notes=notes,
            )
        )
    return tuple(rows)


def build_trace_container_matrix() -> tuple[TraceContainerRow, ...]:
    dotted_by_container: dict[str, list[str]] = {}
    for path in dotted_protected_field_paths():
        spec = _PROTECTED_EXTRACTION_SPECS[path]
        container = spec.trace_container or ""
        dotted_by_container.setdefault(container, []).append(path)

    rows: list[TraceContainerRow] = []
    for presence_key, container_key in _TRACE_CONTAINER_RAW_PRESENCE:
        rows.append(
            TraceContainerRow(
                container_key=presence_key,
                observed_key=container_key,
                projection_owner=_TRACE_ASSEMBLY_OWNER,
                extraction_owner=_TRACE_SOURCE_OWNER,
                unavailable_when=(
                    f"observed.trace.{container_key} is empty/falsy; "
                    f"unavailable policy owner: {_UNAVAILABLE_OWNER}; "
                    f"presence policy owner: tests.helpers.golden_replay_projection_presence._build_projection_status"
                ),
                raw_presence_key=presence_key,
                protected_leaf_paths=tuple(sorted(dotted_by_container.get(container_key, []))),
                diagnostic_keys=_diagnostic_keys_for_container(container_key),
            )
        )
    return tuple(rows)


def _diagnostic_keys_for_container(container_key: str) -> tuple[str, ...]:
    if container_key == "canonical_entry":
        return (
            "canonical_entry_path",
            "canonical_entry_reason",
            "canonical_entry_target_actor_id",
        )
    return ()


def trace_diagnostic_only_observed_keys() -> frozenset[str]:
    """Top-level keys under observed['trace'] that are not protected registry paths."""
    protected_under_trace = {path.split(".", 1)[1] for path in dotted_protected_field_paths()}
    protected_under_trace.update(row.observed_key for row in build_trace_container_matrix())
    all_observed_trace_keys = protected_under_trace | {
        "canonical_entry_path",
        "canonical_entry_reason",
        "canonical_entry_target_actor_id",
    }
    diagnostic = {
        "canonical_entry_path",
        "canonical_entry_reason",
        "canonical_entry_target_actor_id",
    }
    return frozenset(diagnostic)


def trace_container_unavailable_keys() -> frozenset[str]:
    return frozenset(_TRACE_CONTAINER_UNAVAILABLE_KEYS)
