"""Unified state authority registry (governance helpers; not a persistence engine).

This module names **non-overlapping state domains**, their canonical runtime owners,
and deterministic guard helpers for adoption at mutation seams.

GPT / model-originated output is **never** an authoritative mutator of runtime truth.
Call sites should pass ``owner_module`` as ``__name__`` of the engine module performing
the write (for example ``\"game.storage\"``), never a model role string.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Final, FrozenSet, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# Domain ids (stable string constants; JSON- and log-friendly)
# ---------------------------------------------------------------------------

WORLD_STATE: Final[str] = "world_state"
SCENE_STATE: Final[str] = "scene_state"
INTERACTION_STATE: Final[str] = "interaction_state"
PLAYER_VISIBLE_STATE: Final[str] = "player_visible_state"
HIDDEN_STATE: Final[str] = "hidden_state"

STATE_DOMAINS: Final[Tuple[str, ...]] = (
    WORLD_STATE,
    SCENE_STATE,
    INTERACTION_STATE,
    PLAYER_VISIBLE_STATE,
    HIDDEN_STATE,
)

# Owners that must never pass mutation guards (deterministic identity checks).
_NON_AUTHORITATIVE_MUTATION_OWNERS: Final[FrozenSet[str]] = frozenset(
    {
        "gpt",
        "gpt_output",
        "llm",
        "model",
        "model_output",
        "openai",
    }
)


class StateAuthorityError(ValueError):
    """Raised when a state-authority guard is violated."""


@dataclass(frozen=True)
class StateDomainSpec:
    """Inspectable, immutable description of one state domain."""

    domain_id: str
    meaning: str
    runtime_owner_modules: Tuple[str, ...]
    reads_allowed_from: FrozenSet[str]
    forbidden_write_targets: FrozenSet[str]
    visibility_class: str  # "player_facing" | "hidden" | "mixed" | "derived"
    may_be_directly_narrated: bool
    gpt_may_mutate: bool  # always False for required domains; kept for explicit audits
    mutable_by_modules: FrozenSet[str]


@dataclass(frozen=True)
class CrossDomainWriteSpec:
    """Explicit narrow seam: ``source`` may mutate ``target`` only for ``operations``."""

    source: str
    target: str
    operations: FrozenSet[str]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_CROSS_DOMAIN_WRITE_ALLOWLIST: Final[Tuple[CrossDomainWriteSpec, ...]] = (
    CrossDomainWriteSpec(
        SCENE_STATE,
        WORLD_STATE,
        frozenset(
            {
                "npc_promotion",
                "resolution_world_mutations",
            }
        ),
    ),
    CrossDomainWriteSpec(
        HIDDEN_STATE,
        SCENE_STATE,
        frozenset(
            {
                "reveal_clue_runtime",
                "reveal_hidden_fact_runtime",
                "merge_pending_lead_runtime",
            }
        ),
    ),
    CrossDomainWriteSpec(
        HIDDEN_STATE,
        WORLD_STATE,
        frozenset(
            {
                "publish_progression_to_world_state",
            }
        ),
    ),
    CrossDomainWriteSpec(
        INTERACTION_STATE,
        SCENE_STATE,
        frozenset(
            {
                "promotion_map_update",
                "interlocutor_binding",
                "scene_runtime_hygiene",
                # Session-local exchange interruption counters mirrored under scene_state (and legacy session root).
                "exchange_interruption_tracker_slot",
            }
        ),
    ),
    CrossDomainWriteSpec(
        HIDDEN_STATE,
        PLAYER_VISIBLE_STATE,
        frozenset(
            {
                # Runtime revealed-hidden facts merged into player journal ``known_facts`` (derived view only).
                "journal_merge_revealed_hidden_facts",
            }
        ),
    ),
    CrossDomainWriteSpec(
        SCENE_STATE,
        INTERACTION_STATE,
        frozenset(
            {
                "scene_transition_hygiene",
                "clear_interaction_context",
            }
        ),
    ),
)

_REGISTRY: Final[Dict[str, StateDomainSpec]] = {
    WORLD_STATE: StateDomainSpec(
        domain_id=WORLD_STATE,
        meaning=(
            "Persistent campaign/world truth: settlements, factions, NPC records, projects, "
            "``world['world_state']`` flags/counters/clocks, clues ledger, and other world.json "
            "fields mutated by the engine after authoritative resolution. ``game.storage`` participates "
            "via world.json load/save and read-time shape normalization only—not semantic policy."
        ),
        runtime_owner_modules=("game.world", "game.storage"),
        reads_allowed_from=frozenset({WORLD_STATE, SCENE_STATE}),
        forbidden_write_targets=frozenset(
            {SCENE_STATE, INTERACTION_STATE, PLAYER_VISIBLE_STATE, HIDDEN_STATE}
        ),
        visibility_class="mixed",
        may_be_directly_narrated=False,
        gpt_may_mutate=False,
        mutable_by_modules=frozenset({"game.world", "game.world_progression", "game.storage", "game.api"}),
    ),
    SCENE_STATE: StateDomainSpec(
        domain_id=SCENE_STATE,
        meaning=(
            "Session scene anchoring and per-scene playthrough progress: ``session['scene_state']``, "
            "``session['scene_runtime']``, ``session['active_scene_id']`` / visit bookkeeping, and "
            "authored scene templates on disk (``data/scenes/*.json``) via ``game.storage`` I/O. "
            "``game.storage`` provides document load/save and lazy session-root materialization; "
            "orchestrated transitions and hygiene stay with ``game.api`` / owners. "
            "Distinct from interaction mode/target selection (see interaction_state)."
        ),
        runtime_owner_modules=("game.storage", "game.api"),
        reads_allowed_from=frozenset(
            {WORLD_STATE, SCENE_STATE, INTERACTION_STATE, HIDDEN_STATE}
        ),
        forbidden_write_targets=frozenset({PLAYER_VISIBLE_STATE}),
        visibility_class="mixed",
        may_be_directly_narrated=False,
        gpt_may_mutate=False,
        mutable_by_modules=frozenset(
            {"game.storage", "game.api", "game.world", "game.interaction_context"}
        ),
    ),
    INTERACTION_STATE: StateDomainSpec(
        domain_id=INTERACTION_STATE,
        meaning=(
            "Session-local interaction framing: ``session['interaction_context']`` (mode, engagement, "
            "privacy, active target, player position hints) and authoritative social-target resolution "
            "mutations owned by ``game.interaction_context``."
        ),
        runtime_owner_modules=("game.interaction_context", "game.api"),
        reads_allowed_from=frozenset({WORLD_STATE, SCENE_STATE, INTERACTION_STATE}),
        forbidden_write_targets=frozenset(
            {WORLD_STATE, PLAYER_VISIBLE_STATE, HIDDEN_STATE}
        ),
        visibility_class="mixed",
        may_be_directly_narrated=False,
        gpt_may_mutate=False,
        mutable_by_modules=frozenset({"game.interaction_context", "game.api"}),
    ),
    PLAYER_VISIBLE_STATE: StateDomainSpec(
        domain_id=PLAYER_VISIBLE_STATE,
        meaning=(
            "Governed publication and inspection **view** of what may be narrated or shown: "
            "``narration_visibility`` exports, ``scene_state_anchor_contract``, curated prompt slices "
            "such as ``public_scene``, and emitted ``player_facing_text``. Not a persistence root; "
            "must not be written back as hidden or world truth."
        ),
        runtime_owner_modules=(
            "game.narration_visibility",
            "game.scene_state_anchoring",
            "game.prompt_context",
            "game.journal",
        ),
        reads_allowed_from=frozenset(STATE_DOMAINS),
        forbidden_write_targets=frozenset(
            {WORLD_STATE, SCENE_STATE, INTERACTION_STATE, HIDDEN_STATE}
        ),
        visibility_class="derived",
        may_be_directly_narrated=True,
        gpt_may_mutate=False,
        mutable_by_modules=frozenset(
            {
                "game.final_emission_gate",
                "game.final_emission_repairs",
                "game.api",
                "game.journal",
            }
        ),
    ),
    HIDDEN_STATE: StateDomainSpec(
        domain_id=HIDDEN_STATE,
        meaning=(
            "Authoritative facts not yet published to the player: template ``hidden_facts`` and "
            "undiscovered clue records, GM-only prompt bundles under ``scene['gm_only']``, "
            "unpublished intent/plan fields carried for prompting, and engine-only counters/flags "
            "until a reveal seam runs. ``game.storage`` persists authoritative documents; publication "
            "to ``player_visible_state`` uses explicit seams (for example ``game.journal``). "
            "Not a junk drawer—each key should map to a typed reveal rule."
        ),
        runtime_owner_modules=("game.storage", "game.world", "game.api"),
        reads_allowed_from=frozenset(
            {WORLD_STATE, SCENE_STATE, INTERACTION_STATE, HIDDEN_STATE}
        ),
        forbidden_write_targets=frozenset({PLAYER_VISIBLE_STATE}),
        visibility_class="hidden",
        may_be_directly_narrated=False,
        gpt_may_mutate=False,
        mutable_by_modules=frozenset({"game.storage", "game.world", "game.api"}),
    ),
}


def _normalize_domain(domain: str) -> str:
    if domain not in _REGISTRY:
        raise StateAuthorityError(
            f"Unknown state domain {domain!r}. Expected one of: {', '.join(STATE_DOMAINS)}"
        )
    return domain


def _normalize_owner(owner_module: str) -> str:
    if not isinstance(owner_module, str) or not owner_module.strip():
        raise StateAuthorityError("owner_module must be a non-empty str (use __name__ of the mutator module)")
    return owner_module.strip()


@lru_cache(maxsize=1)
def all_state_domain_specs() -> Tuple[StateDomainSpec, ...]:
    """Return every domain spec in stable order (inspectable, deterministic)."""
    return tuple(_REGISTRY[d] for d in STATE_DOMAINS)


def get_state_domain_spec(domain: str) -> StateDomainSpec:
    """Return the spec for ``domain`` or raise ``StateAuthorityError``."""
    return _REGISTRY[_normalize_domain(domain)]


def get_runtime_owner_for_domain(domain: str) -> Tuple[str, ...]:
    """Canonical runtime owner modules for ``domain`` (declarative; not runtime dispatch)."""
    return get_state_domain_spec(domain).runtime_owner_modules


def is_domain_player_facing(domain: str) -> bool:
    """True when the domain is classified as player-facing or derived for publication."""
    spec = get_state_domain_spec(domain)
    return spec.visibility_class in {"player_facing", "derived", "mixed"}


def can_domain_read_domain(reader_domain: str, target_domain: str) -> bool:
    """Return True when ``reader_domain`` may depend on ``target_domain`` for engine reads."""
    reader = _normalize_domain(reader_domain)
    target = _normalize_domain(target_domain)
    if reader == target:
        return True
    spec = _REGISTRY[reader]
    return target in spec.reads_allowed_from


def can_owner_mutate_domain(owner_module: str, domain: str) -> bool:
    """True when ``owner_module`` is in the declared mutator set for ``domain`` and is authoritative."""
    owner = _normalize_owner(owner_module)
    if owner in _NON_AUTHORITATIVE_MUTATION_OWNERS:
        return False
    spec = _REGISTRY[_normalize_domain(domain)]
    return owner in spec.mutable_by_modules


def assert_owner_can_mutate_domain(
    owner_module: str,
    domain: str,
    *,
    operation: Optional[str] = None,
) -> None:
    """Raise ``StateAuthorityError`` if this owner may not mutate the domain."""
    owner = _normalize_owner(owner_module)
    dom = _normalize_domain(domain)
    if owner in _NON_AUTHORITATIVE_MUTATION_OWNERS:
        op = f" (operation={operation!r})" if operation else ""
        raise StateAuthorityError(
            f"Non-authoritative owner {owner!r} cannot mutate domain {dom!r}{op}. "
            "Model-originated output must not write runtime truth."
        )
    if not can_owner_mutate_domain(owner, dom):
        op = f" for operation={operation!r}" if operation else ""
        allowed = ", ".join(sorted(get_state_domain_spec(dom).mutable_by_modules)) or "(none)"
        raise StateAuthorityError(
            f"Module {owner!r} is not a declared mutator for domain {dom!r}{op}. "
            f"Declared mutators: {allowed}."
        )


def assert_cross_domain_write_allowed(
    source_domain: str,
    target_domain: str,
    *,
    operation: str,
) -> None:
    """Raise ``StateAuthorityError`` unless a declared cross-domain write seam matches."""
    src = _normalize_domain(source_domain)
    tgt = _normalize_domain(target_domain)
    if not isinstance(operation, str) or not operation.strip():
        raise StateAuthorityError("cross-domain writes require a non-empty operation name")
    op = operation.strip()
    if src == tgt:
        return
    for edge in _CROSS_DOMAIN_WRITE_ALLOWLIST:
        if edge.source == src and edge.target == tgt and op in edge.operations:
            return
    raise StateAuthorityError(
        f"Cross-domain write not allow-listed: {src!r} -> {tgt!r} (operation={op!r}). "
        "Add an explicit seam entry in game.state_authority._CROSS_DOMAIN_WRITE_ALLOWLIST "
        "or perform the write through the target domain's canonical owner API."
    )


def build_state_mutation_trace(
    *,
    domain: str,
    owner_module: str,
    operation: Optional[str] = None,
    cross_domain: Optional[Tuple[str, str, str]] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Compact, JSON-friendly trace payload for logs and ``storage.append_debug_trace``."""
    _normalize_domain(domain)
    trace: Dict[str, Any] = {
        "kind": "state_mutation",
        "domain": domain,
        "owner_module": _normalize_owner(owner_module),
    }
    if operation is not None:
        trace["operation"] = str(operation)
    if cross_domain is not None:
        src, tgt, cross_op = cross_domain
        trace["cross_domain"] = {
            "source": _normalize_domain(src),
            "target": _normalize_domain(tgt),
            "operation": str(cross_op),
        }
    if extra:
        for k, v in extra.items():
            trace[str(k)] = v
    return trace
