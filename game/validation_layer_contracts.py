"""Declarative validation-layer ownership (governance contract; not runtime enforcement).

This module is a **leaf**: stdlib + typing only. It names the five canonical validation
layers, governed responsibility domains, and helper predicates for tests and audits.

It does **not** import orchestration, validators, repairs, or GPT surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final, FrozenSet, Mapping, Tuple

# ---------------------------------------------------------------------------
# Canonical layer ids (stable; used by tests and docs)
# ---------------------------------------------------------------------------

ENGINE: Final[str] = "engine"
PLANNER: Final[str] = "planner"
GPT: Final[str] = "gpt"
GATE: Final[str] = "gate"
EVALUATOR: Final[str] = "evaluator"

CANONICAL_VALIDATION_LAYERS: Final[Tuple[str, ...]] = (
    ENGINE,
    PLANNER,
    GPT,
    GATE,
    EVALUATOR,
)

# Stable failure-reason token: NA may append this after a **non-owning** shadow read of
# ``validate_response_delta`` (same predicate as the gate stack). Canonical pass/fail,
# repair, and ``response_delta_*`` legality metadata remain exclusively gate-owned.
NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON: Final[str] = "follow_up_missing_signal_shadow_response_delta"

# ---------------------------------------------------------------------------
# Responsibility kinds (orthogonal to runtime module names)
# ---------------------------------------------------------------------------

KIND_TRUTH: Final[str] = "truth"
KIND_STRUCTURE: Final[str] = "structure"
KIND_EXPRESSION: Final[str] = "expression"
KIND_LEGALITY: Final[str] = "legality"
KIND_SCORING: Final[str] = "scoring"

RESPONSIBILITY_KINDS: Final[Tuple[str, ...]] = (
    KIND_TRUTH,
    KIND_STRUCTURE,
    KIND_EXPRESSION,
    KIND_LEGALITY,
    KIND_SCORING,
)

KIND_TO_CANONICAL_LAYER: Final[Mapping[str, str]] = {
    KIND_TRUTH: ENGINE,
    KIND_STRUCTURE: PLANNER,
    KIND_EXPRESSION: GPT,
    KIND_LEGALITY: GATE,
    KIND_SCORING: EVALUATOR,
}


@dataclass(frozen=True)
class ResponsibilityDomainSpec:
    """One governed concern: stable id, kind, and short meaning for docs/tests."""

    domain_id: str
    kind: str
    meaning: str


# Governed domains: each id appears exactly once; kind must match canonical layer.
_RESPONSIBILITY_DOMAINS: Final[Tuple[ResponsibilityDomainSpec, ...]] = (
    # Truth -> engine
    ResponsibilityDomainSpec(
        "world_simulation_and_persistence_truth",
        KIND_TRUTH,
        "Authoritative world/scene/session commits and simulation outcomes.",
    ),
    ResponsibilityDomainSpec(
        "resolved_turn_semantics_truth",
        KIND_TRUTH,
        "Normalized resolved-turn meaning (CTIR-class shapes) after authoritative mutation.",
    ),
    ResponsibilityDomainSpec(
        "interaction_authority_truth",
        KIND_TRUTH,
        "Authoritative interaction framing and social-target precedence (engine-owned).",
    ),
    # Structure -> planner / prompt-side assembly (consumes engine truth; does not replace it)
    ResponsibilityDomainSpec(
        "prompt_and_guard_structure",
        KIND_STRUCTURE,
        "Prompt bundle assembly, shipped instruction structure, guard-facing contract export.",
    ),
    ResponsibilityDomainSpec(
        "shipped_response_policy_structure",
        KIND_STRUCTURE,
        "Materialization of shipped policy/contract *shapes* the writer must satisfy (not legality verdicts).",
    ),
    ResponsibilityDomainSpec(
        "turn_intent_and_routing_structure",
        KIND_STRUCTURE,
        "Coarse routing, planner-visible intent packets, bootstrap structure feeding narration.",
    ),
    # Expression -> GPT surfaces only
    ResponsibilityDomainSpec(
        "model_text_and_json_surfaces",
        KIND_EXPRESSION,
        "Prose and model-shaped JSON drafts within supplied contracts (non-authoritative for truth).",
    ),
    # Legality -> gate + deterministic validator/repair stack (orchestrated as one layer)
    ResponsibilityDomainSpec(
        "deterministic_post_generation_checks",
        KIND_LEGALITY,
        "Pure validators and inspectors over emitted or candidate text/artifacts.",
    ),
    ResponsibilityDomainSpec(
        "bounded_deterministic_repairs",
        KIND_LEGALITY,
        "Bounded subtractive/deterministic repairs and skip policies wired under gate orchestration.",
    ),
    ResponsibilityDomainSpec(
        "final_emission_gate_orchestration",
        KIND_LEGALITY,
        "Legality orchestration: layer ordering, sanitizer integration, pass/fail sealing (not scoring).",
    ),
    ResponsibilityDomainSpec(
        "response_delta_enforcement_and_repair",
        KIND_LEGALITY,
        "Primary ownership of response-delta obligation checks and delta-class repairs (not NA).",
    ),
    # Scoring -> offline evaluators only
    ResponsibilityDomainSpec(
        "offline_evaluator_scoring",
        KIND_SCORING,
        "Numeric or axis scores and verdict summaries for artifacts; read-only to live legality.",
    ),
    ResponsibilityDomainSpec(
        "offline_playability_or_quality_judgments",
        KIND_SCORING,
        "Harness-level judgments that do not mutate live pipeline output.",
    ),
)

RESPONSIBILITY_DOMAIN_BY_ID: Final[Dict[str, ResponsibilityDomainSpec]] = {
    spec.domain_id: spec for spec in _RESPONSIBILITY_DOMAINS
}


def responsibility_domains() -> Tuple[ResponsibilityDomainSpec, ...]:
    """All governed responsibility domains (immutable tuple)."""
    return _RESPONSIBILITY_DOMAINS


def owner_layer_for_responsibility_domain(domain_id: str) -> str:
    """Return the single canonical validation layer that owns ``domain_id``."""
    spec = RESPONSIBILITY_DOMAIN_BY_ID.get(domain_id)
    if spec is None:
        msg = f"unknown responsibility domain id: {domain_id!r}"
        raise KeyError(msg)
    owner = KIND_TO_CANONICAL_LAYER.get(spec.kind)
    if owner is None:
        msg = f"unknown responsibility kind on domain {domain_id!r}: {spec.kind!r}"
        raise ValueError(msg)
    return owner


def canonical_layer_for_kind(kind: str) -> str:
    """Map a responsibility kind to its canonical owning layer."""
    if kind not in KIND_TO_CANONICAL_LAYER:
        msg = f"unknown responsibility kind: {kind!r}"
        raise KeyError(msg)
    return KIND_TO_CANONICAL_LAYER[kind]


# ---------------------------------------------------------------------------
# Predicate helpers (pure)
# ---------------------------------------------------------------------------


def is_truth_owner(layer_id: str, *, domain_id: str | None = None) -> bool:
    """True if ``layer_id`` is the canonical truth owner (``engine``), optionally for a domain."""
    if domain_id is not None:
        return owner_layer_for_responsibility_domain(domain_id) == ENGINE and layer_id == ENGINE
    return layer_id == ENGINE


def is_structure_owner(layer_id: str, *, domain_id: str | None = None) -> bool:
    """True if ``layer_id`` is the canonical structure owner (``planner``), optionally for a domain."""
    if domain_id is not None:
        return owner_layer_for_responsibility_domain(domain_id) == PLANNER and layer_id == PLANNER
    return layer_id == PLANNER


def is_expression_owner(layer_id: str, *, domain_id: str | None = None) -> bool:
    """True if ``layer_id`` is the canonical expression owner (``gpt``), optionally for a domain."""
    if domain_id is not None:
        return owner_layer_for_responsibility_domain(domain_id) == GPT and layer_id == GPT
    return layer_id == GPT


def is_legality_owner(layer_id: str, *, domain_id: str | None = None) -> bool:
    """True if ``layer_id`` is the canonical legality owner (``gate``), optionally for a domain."""
    if domain_id is not None:
        return owner_layer_for_responsibility_domain(domain_id) == GATE and layer_id == GATE
    return layer_id == GATE


def is_scoring_owner(layer_id: str, *, domain_id: str | None = None) -> bool:
    """True if ``layer_id`` is the canonical scoring owner (``evaluator``), optionally for a domain."""
    if domain_id is not None:
        return owner_layer_for_responsibility_domain(domain_id) == EVALUATOR and layer_id == EVALUATOR
    return layer_id == EVALUATOR


def classify_layer_read_only_non_enforcement(layer_id: str) -> bool:
    """True when ``layer_id`` must not enforce live legality (evaluator)."""
    return layer_id == EVALUATOR


def classify_layer_non_scoring_gate(layer_id: str) -> bool:
    """True when ``layer_id`` is the live gate (legality) and must not own scoring domains."""
    return layer_id == GATE


def classify_layer_non_truth_non_legality_expression(layer_id: str) -> bool:
    """True for GPT: expression-only relative to this contract (no truth/legality ownership)."""
    return layer_id == GPT


def classify_layer_non_truth_authority_planner(layer_id: str) -> bool:
    """True for planner: may structure consumption of truth but not author engine truth."""
    return layer_id == PLANNER


def _build_forbidden_layer_kind_claims() -> FrozenSet[Tuple[str, str]]:
    """Pairs (layer_id, kind) where ``layer_id`` must not own ``kind`` (single-owner matrix)."""
    out: set[Tuple[str, str]] = set()
    for layer in CANONICAL_VALIDATION_LAYERS:
        for kind in RESPONSIBILITY_KINDS:
            canonical = KIND_TO_CANONICAL_LAYER[kind]
            if layer != canonical:
                out.add((layer, kind))
    return frozenset(out)


_FORBIDDEN_LAYER_KIND_CLAIMS: Final[FrozenSet[Tuple[str, str]]] = _build_forbidden_layer_kind_claims()


def forbidden_layer_kind_claims() -> Tuple[Tuple[str, str], ...]:
    """Inspectable forbidden (layer, kind) ownership claims for audits (sorted tuple)."""
    return tuple(sorted(_FORBIDDEN_LAYER_KIND_CLAIMS))


def is_forbidden_layer_kind_claim(layer_id: str, kind: str) -> bool:
    """True if ``layer_id`` must not be treated as owner of ``kind``."""
    return (layer_id, kind) in _FORBIDDEN_LAYER_KIND_CLAIMS


def assert_domain_maps_to_kind_owner(domain_id: str) -> None:
    """Assert internal consistency: domain kind matches canonical owner layer."""
    spec = RESPONSIBILITY_DOMAIN_BY_ID[domain_id]
    expected_layer = KIND_TO_CANONICAL_LAYER[spec.kind]
    actual = owner_layer_for_responsibility_domain(domain_id)
    if actual != expected_layer:
        msg = f"domain {domain_id!r} maps to {actual!r}, expected {expected_layer!r}"
        raise AssertionError(msg)


def assert_layer_does_not_claim_forbidden_kind(layer_id: str, kind: str) -> None:
    """Raise ``AssertionError`` if ``layer_id`` is forbidden from owning ``kind``."""
    if is_forbidden_layer_kind_claim(layer_id, kind):
        msg = f"layer {layer_id!r} must not claim ownership of kind {kind!r}"
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
# Read/write collaboration matrix (validation phases, not state_authority)
# ---------------------------------------------------------------------------
# Rows: reader layer. Values: layers whose *outputs* may be consulted as inputs.
# Writes are implicit: each layer writes only its own phase outputs; downstream
# readers must not back-write upstream truth.

_LAYER_READS: Final[Mapping[str, FrozenSet[str]]] = {
    ENGINE: frozenset({ENGINE}),
    PLANNER: frozenset({ENGINE, PLANNER}),
    GPT: frozenset({ENGINE, PLANNER, GPT}),
    GATE: frozenset({ENGINE, PLANNER, GPT, GATE}),
    EVALUATOR: frozenset({ENGINE, PLANNER, GPT, GATE, EVALUATOR}),
}


def allowed_reader_layers_for_writer(writer_layer: str) -> FrozenSet[str]:
    """Layers that may read outputs produced by ``writer_layer`` in the forward pipeline."""
    allowed: set[str] = set()
    for reader, writers in _LAYER_READS.items():
        if writer_layer in writers:
            allowed.add(reader)
    return frozenset(allowed)


def layer_may_read_layer(reader_layer: str, writer_layer: str) -> bool:
    """True if ``reader_layer`` may consume ``writer_layer`` outputs (forward direction)."""
    readers_allowed = _LAYER_READS.get(reader_layer)
    if readers_allowed is None:
        return False
    return writer_layer in readers_allowed


def assert_forward_read_path(reader_layer: str, writer_layer: str) -> None:
    """Raise ``AssertionError`` if ``reader_layer`` is not allowed to read ``writer_layer``."""
    if not layer_may_read_layer(reader_layer, writer_layer):
        msg = f"layer {reader_layer!r} may not read outputs of {writer_layer!r}"
        raise AssertionError(msg)
