"""Engine-owned non-combat resolution contract (orchestration + vocabulary).

This module defines the canonical seam for investigation, perception, social probing,
exploration, and downtime. Domain mechanics remain in ``game.exploration`` and
``game.social``; this layer classifies intent, delegates resolution, and normalizes
outcomes for downstream consumers (for example CTIR).

Fail-closed: ambiguous, unsupported, or under-specified actions yield structured
``blocked`` / ``ambiguous`` / ``unsupported`` outcomes—no prose hints, no LLM calls,
no narration-driven mechanics inside this contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

from game.exploration import EXPLORATION_KINDS
from game.models import make_check_request
from game.social import SOCIAL_KINDS
from game.state_authority import INTERACTION_STATE, SCENE_STATE, WORLD_STATE

# ---------------------------------------------------------------------------
# Stable framework identity
# ---------------------------------------------------------------------------

NONCOMBAT_FRAMEWORK_VERSION = "2026.04.noncombat.v1"

NoncombatKind = Literal["perception", "investigation", "social_probe", "exploration", "downtime"]

NONCOMBAT_KINDS: Tuple[str, ...] = (
    "perception",
    "investigation",
    "social_probe",
    "exploration",
    "downtime",
)

OutcomeType = Literal["closed", "blocked", "ambiguous", "unsupported", "pending_check"]

SuccessState = Literal["success", "failure", "neutral", "unknown"]

ResolutionRoute = Literal["exploration", "social", "none"]

_MAX_ENTITIES = 32
_MAX_FACTS = 32
_MAX_STATE_KEYS = 48
_MAX_AUTH_OUTPUTS = 16
_MAX_REASON_CODES = 16


@dataclass(frozen=True)
class NoncombatClassification:
    """Deterministic classification of a normalized action into the non-combat taxonomy."""

    kind: str
    subkind: str
    route: ResolutionRoute
    authority_domain: str
    ambiguous_reason_codes: Tuple[str, ...]
    unsupported_reason_codes: Tuple[str, ...]

    @property
    def routable(self) -> bool:
        return self.route in ("exploration", "social")


def _bounded_list(items: List[Any], limit: int) -> List[Any]:
    if len(items) <= limit:
        return items
    return items[:limit]


def _bounded_mapping(m: Dict[str, Any], max_keys: int) -> Dict[str, Any]:
    if not m:
        return {}
    keys = sorted(m.keys())[:max_keys]
    return {k: m[k] for k in keys}


def classify_noncombat_kind(
    normalized_action: Optional[Dict[str, Any]],
    *,
    explicit_route: Optional[ResolutionRoute] = None,
) -> NoncombatClassification:
    """Map a normalized engine action to canonical non-combat ``kind`` / ``subkind``.

    Does not parse freeform text; callers must supply a structured ``normalized_action``.
    Unknown ``type`` values, missing types, and route/action mismatches return ``route="none"``
    so :func:`resolve_noncombat_action` will not delegate to a domain owner by mistake.
    """
    amb: List[str] = []
    unsup: List[str] = []

    if not isinstance(normalized_action, dict):
        amb.append("missing_normalized_action")
        return NoncombatClassification(
            kind="exploration",
            subkind="unspecified",
            route="none",
            authority_domain=SCENE_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    raw_type = str(normalized_action.get("type") or "").strip().lower()
    if not raw_type:
        amb.append("missing_action_type")
        return NoncombatClassification(
            kind="exploration",
            subkind="unspecified",
            route="none",
            authority_domain=SCENE_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    if raw_type == "attack":
        unsup.append("combat_action_not_noncombat")
        return NoncombatClassification(
            kind="exploration",
            subkind="attack",
            route="none",
            authority_domain=SCENE_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    if raw_type in ("downtime", "downtime_activity", "camp", "long_rest", "short_rest"):
        unsup.append("downtime_engine_not_wired")
        return NoncombatClassification(
            kind="downtime",
            subkind=raw_type,
            route="none",
            authority_domain=WORLD_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    if explicit_route == "social" and raw_type not in SOCIAL_KINDS:
        amb.append("route_explicit_mismatch")
        return NoncombatClassification(
            kind="exploration",
            subkind=raw_type,
            route="none",
            authority_domain=SCENE_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )
    if explicit_route == "exploration" and raw_type in SOCIAL_KINDS:
        amb.append("route_explicit_mismatch")
        return NoncombatClassification(
            kind="social_probe",
            subkind=raw_type,
            route="none",
            authority_domain=INTERACTION_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    inferred_social = raw_type in SOCIAL_KINDS
    inferred_explore = raw_type in EXPLORATION_KINDS

    if explicit_route == "social" or (explicit_route is None and inferred_social):
        sub = raw_type if inferred_social else "social_probe"
        return NoncombatClassification(
            kind="social_probe",
            subkind=sub,
            route="social",
            authority_domain=INTERACTION_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    if explicit_route == "exploration" or (explicit_route is None and inferred_explore and not inferred_social):
        if not inferred_explore:
            amb.append("unknown_action_type_for_noncombat")
            return NoncombatClassification(
                kind="exploration",
                subkind=raw_type,
                route="none",
                authority_domain=SCENE_STATE,
                ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
                unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
            )

        if raw_type == "observe":
            return NoncombatClassification(
                kind="perception",
                subkind="observe",
                route="exploration",
                authority_domain=SCENE_STATE,
                ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
                unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
            )
        if raw_type in ("investigate", "discover_clue", "already_searched"):
            return NoncombatClassification(
                kind="investigation",
                subkind=raw_type,
                route="exploration",
                authority_domain=SCENE_STATE,
                ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
                unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
            )
        return NoncombatClassification(
            kind="exploration",
            subkind=raw_type,
            route="exploration",
            authority_domain=SCENE_STATE,
            ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
            unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
        )

    amb.append("unknown_action_type_for_noncombat")
    return NoncombatClassification(
        kind="exploration",
        subkind=raw_type,
        route="none",
        authority_domain=SCENE_STATE,
        ambiguous_reason_codes=tuple(_bounded_list(amb, _MAX_REASON_CODES)),
        unsupported_reason_codes=tuple(_bounded_list(unsup, _MAX_REASON_CODES)),
    )


def _success_state_from_raw(success: Any) -> SuccessState:
    if success is True:
        return "success"
    if success is False:
        return "failure"
    if success is None:
        return "neutral"
    return "unknown"


def _outcome_and_codes(
    raw: Dict[str, Any],
    *,
    classification: NoncombatClassification,
    route: ResolutionRoute,
) -> Tuple[OutcomeType, SuccessState, List[str], List[str], List[str]]:
    blocked: List[str] = []
    ambiguous: List[str] = []
    unsupported: List[str] = list(classification.unsupported_reason_codes)

    if not raw:
        success_state: SuccessState = "neutral"
        if unsupported:
            return "unsupported", success_state, blocked, ambiguous, unsupported
        if classification.ambiguous_reason_codes:
            ambiguous.extend(classification.ambiguous_reason_codes)
            return "ambiguous", success_state, blocked, ambiguous, unsupported
        return "closed", success_state, blocked, ambiguous, unsupported

    success_state = _success_state_from_raw(raw.get("success"))

    meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    social = raw.get("social") if isinstance(raw.get("social"), dict) else {}

    outcome: OutcomeType = "closed"

    if classification.unsupported_reason_codes:
        outcome = "unsupported"
        return outcome, success_state, blocked, ambiguous, unsupported

    if route == "social":
        if social.get("offscene_target"):
            outcome = "blocked"
            blocked.append("offscene_target")
        elif social.get("broad_address_bid") or social.get("open_social_solicitation"):
            outcome = "ambiguous"
            ambiguous.append("social_target_unresolved")
        elif not social.get("target_resolved") and classification.subkind not in ("question", "social_probe"):
            outcome = "ambiguous"
            ambiguous.append("social_target_unresolved")

    if route == "exploration":
        kind = str(raw.get("kind") or "").strip().lower()
        if meta.get("destination_binding_conflict"):
            outcome = "blocked"
            blocked.append("destination_binding_conflict")
        elif meta.get("compatibility_clear_target") or meta.get("destination_compatibility_passed") is False:
            outcome = "blocked"
            blocked.append("incompatible_scene_transition")
        elif kind in ("scene_transition", "travel"):
            if not raw.get("resolved_transition") and (
                meta.get("effective_target_scene_id") or raw.get("target_scene_id")
            ):
                outcome = "blocked"
                blocked.append("unreachable_scene_transition")
            elif not raw.get("resolved_transition") and not (
                raw.get("target_scene_id") or meta.get("effective_target_scene_id")
            ):
                outcome = "ambiguous"
                ambiguous.append("travel_target_unresolved")

    pending_roll = bool(raw.get("requires_check")) and not isinstance(raw.get("skill_check"), dict)
    if pending_roll and outcome == "closed":
        outcome = "pending_check"
    if pending_roll and outcome not in ("blocked", "unsupported"):
        ambiguous.append("check_not_executed")

    if classification.ambiguous_reason_codes:
        ambiguous.extend(classification.ambiguous_reason_codes)

    # De-duplicate while preserving order
    def _dedupe(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return (
        outcome,
        success_state,
        _dedupe(blocked),
        _dedupe(ambiguous),
        _dedupe(unsupported),
    )


def _discovered_entities(raw: Dict[str, Any], route: ResolutionRoute) -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []
    social = raw.get("social") if isinstance(raw.get("social"), dict) else {}
    nid = str(social.get("npc_id") or "").strip()
    if nid:
        entities.append({"entity_kind": "npc", "entity_id": nid})
    tid = str(raw.get("target_scene_id") or "").strip()
    if tid:
        entities.append({"entity_kind": "scene", "entity_id": tid})
    iid = str(raw.get("interactable_id") or "").strip()
    if iid:
        entities.append({"entity_kind": "interactable", "entity_id": iid})
    if route == "exploration":
        sc = raw.get("scene") if isinstance(raw.get("scene"), dict) else None
        if not sc:
            meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
            ost = str(meta.get("originating_scene_id") or "").strip()
            if ost:
                entities.append({"entity_kind": "scene", "entity_id": ost})
    return _bounded_list(entities, _MAX_ENTITIES)


def _surfaced_facts(raw: Dict[str, Any]) -> List[str]:
    facts: List[str] = []
    cid = str(raw.get("clue_id") or "").strip()
    if cid:
        facts.append(f"clue:{cid}")
    for clue in raw.get("discovered_clues") or []:
        if isinstance(clue, str) and clue.strip():
            slug = clue.strip()
            if len(slug) > 120:
                slug = slug[:120]
            facts.append(f"clue_text_digest:{hash(slug) & 0xFFFFFFFF:x}")
    social = raw.get("social") if isinstance(raw.get("social"), dict) else {}
    topic = social.get("topic_revealed") or social.get("topic_id")
    if isinstance(topic, str) and topic.strip():
        facts.append(f"topic:{topic.strip()[:120]}")
    return _bounded_list(facts, _MAX_FACTS)


def _deterministic_resolved(
    outcome: OutcomeType,
    raw: Dict[str, Any],
) -> bool:
    if outcome in ("ambiguous", "unsupported", "pending_check"):
        return False
    if outcome == "blocked":
        # Blocked outcomes are still engine-deterministic judgments.
        return True
    if isinstance(raw.get("skill_check"), dict):
        return True
    if raw.get("requires_check") and not isinstance(raw.get("skill_check"), dict):
        return False
    return True


def _narration_constraints(raw: Dict[str, Any], route: ResolutionRoute) -> Dict[str, Any]:
    """Structured, engine-authored hints only (no prose)."""
    nc: Dict[str, Any] = {}
    social = raw.get("social") if isinstance(raw.get("social"), dict) else {}
    if route == "social":
        if "npc_reply_expected" in social:
            nc["npc_reply_expected"] = bool(social.get("npc_reply_expected"))
        rk = social.get("reply_kind")
        if isinstance(rk, str) and rk.strip():
            nc["reply_kind"] = rk.strip()[:64]
    if raw.get("resolved_transition") is True:
        nc["scene_transition_occurred"] = True
    meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    if meta.get("passive_interruption_wait") is True:
        nc["passive_interruption_wait"] = True
    return nc


def normalize_noncombat_resolution(
    raw_engine_result: Dict[str, Any],
    classification: NoncombatClassification,
    *,
    route: ResolutionRoute,
    source_engine: str,
) -> Dict[str, Any]:
    """Project a domain engine dict into the canonical non-combat contract.

    Strips prose fields (``hint``, ``prompt``, ``label``) from the normalized payload;
    keep machine-readable facts only.
    """
    raw = dict(raw_engine_result) if isinstance(raw_engine_result, dict) else {}

    has_roll = isinstance(raw.get("skill_check"), dict)
    requires_check_out = bool(raw.get("requires_check")) and not has_roll
    check_request = raw.get("check_request") if isinstance(raw.get("check_request"), dict) else None
    if requires_check_out and check_request is None:
        check_request = make_check_request(
            requires_check=True,
            reason="engine_pending_check",
            player_prompt=None,
        )

    outcome_type, success_state, blocked_c, amb_c, unsup_c = _outcome_and_codes(
        raw, classification=classification, route=route
    )

    det_res = _deterministic_resolved(outcome_type, raw)

    state_changes = raw.get("state_changes") if isinstance(raw.get("state_changes"), dict) else {}
    bounded_state = _bounded_mapping(state_changes, _MAX_STATE_KEYS)

    auth_outputs: List[Dict[str, Any]] = [
        {
            "output_kind": "resolution_trace",
            "source_engine": source_engine,
            "route": route,
            "engine_action_id": str(raw.get("action_id") or "")[:128] or None,
        }
    ]
    wu = raw.get("world_updates")
    if isinstance(wu, dict) and wu:
        auth_outputs.append({"output_kind": "world_updates_ref", "keys": sorted(wu.keys())[:24]})

    narration_constraints = _narration_constraints(raw, route)
    narration_block: Dict[str, Any] = {}
    if narration_constraints:
        narration_block["narration_constraints"] = narration_constraints

    return {
        "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
        "kind": classification.kind,
        "subkind": classification.subkind,
        "authority_domain": classification.authority_domain,
        "deterministic_resolved": det_res,
        "requires_check": requires_check_out,
        "check_request": check_request if isinstance(check_request, dict) else None,
        "outcome_type": outcome_type,
        "success_state": success_state,
        "discovered_entities": _discovered_entities(raw, route),
        "surfaced_facts": _surfaced_facts(raw),
        "state_changes": bounded_state,
        "blocked_reason_codes": _bounded_list(blocked_c, _MAX_REASON_CODES),
        "ambiguous_reason_codes": _bounded_list(amb_c, _MAX_REASON_CODES),
        "unsupported_reason_codes": _bounded_list(unsup_c, _MAX_REASON_CODES),
        "authoritative_outputs": _bounded_list(auth_outputs, _MAX_AUTH_OUTPUTS),
        **narration_block,
    }


def resolve_noncombat_action(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    normalized_action: Dict[str, Any],
    *,
    raw_player_text: Optional[str] = None,
    character: Optional[Dict[str, Any]] = None,
    explicit_route: Optional[ResolutionRoute] = None,
    turn_counter: int = 0,
    exploration_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Classify → delegate to exploration or social owner → normalize to the canonical contract.

    ``exploration_kwargs`` is forwarded to :func:`game.exploration.resolve_exploration_action`
    (for example ``list_scene_ids``, ``load_scene_fn``, ``scene_graph``) when routing is
    exploration.

    When ``route`` is ``exploration`` or ``social``, returns the **domain resolution dict**
    (same shape as :func:`game.exploration.resolve_exploration_action` /
    :func:`game.social.resolve_social_action`) with ``noncombat_resolution`` embedded.
    When ``route`` is ``none``, returns the **canonical contract dict only** (no domain
    delegation occurred).
    """
    classification = classify_noncombat_kind(normalized_action, explicit_route=explicit_route)
    route = classification.route

    if route == "none":
        return normalize_noncombat_resolution(
            {},
            classification,
            route="none",
            source_engine="noncombat_router",
        )

    ex_kw = dict(exploration_kwargs or {})

    if route == "social":
        from game.social import resolve_social_action

        raw = resolve_social_action(
            scene_envelope,
            session,
            world,
            normalized_action,
            raw_player_text=raw_player_text,
            character=character,
            turn_counter=turn_counter,
        )
        nc = normalize_noncombat_resolution(raw, classification, route="social", source_engine="game.social")
        out = dict(raw)
        out["noncombat_resolution"] = nc
        return out

    if route == "exploration":
        from game.exploration import resolve_exploration_action

        raw = resolve_exploration_action(
            scene_envelope,
            session,
            world,
            normalized_action,
            raw_player_text=raw_player_text,
            character=character,
            **ex_kw,
        )
        nc = normalize_noncombat_resolution(
            raw, classification, route="exploration", source_engine="game.exploration"
        )
        out = dict(raw)
        out["noncombat_resolution"] = nc
        return out

    return normalize_noncombat_resolution(
        {},
        classification,
        route="none",
        source_engine="noncombat_router",
    )


def attach_noncombat_contract(
    raw_engine_result: Dict[str, Any],
    normalized_action: Dict[str, Any],
    *,
    explicit_route: Optional[ResolutionRoute] = None,
) -> Dict[str, Any]:
    """Return ``raw_engine_result`` with ``noncombat_resolution`` embedded (side-effect free)."""
    cls = classify_noncombat_kind(normalized_action, explicit_route=explicit_route)
    r: ResolutionRoute = cls.route if cls.route in ("exploration", "social", "none") else "none"
    if r == "social":
        src = "game.social"
    elif r == "exploration":
        src = "game.exploration"
    else:
        src = "noncombat_router"
    nc = normalize_noncombat_resolution(raw_engine_result, cls, route=r, source_engine=src)
    out = dict(raw_engine_result)
    out["noncombat_resolution"] = nc
    return out
