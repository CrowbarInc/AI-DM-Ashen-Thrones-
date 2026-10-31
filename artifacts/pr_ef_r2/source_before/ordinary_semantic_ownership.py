"""Ordinary-gameplay semantic ownership.

One Resolution Contract answers what the player wants resolved. Specialized
systems answer how that contract is resolved. This module is the selection
boundary. It does not replace social, travel, exploration, or combat internals.

C24's adjudication bridge remains the resolver for presence, place, feasibility,
state, and roll questions. This module calls it. It does not reimplement it.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.contract_adjudication_bridge import (
    contract_authorizes_specialized_resolution,
    select_resolver_family,
)
from game.player_commitment import EXECUTED_NOW

# Parser-first owners from C23/C24, after this cycle.
# structural: legitimate pre-contract structural or discourse step.
PEER_PARSER_ROLES: dict[str, str] = {
    "segmentation": "structural",
    "directed_social_entry": "structural",
    "social_parser": "resolver",
    "dialogue_first": "resolver",
    "exploration": "resolver",
    "world_action_recovery": "resolver_helper",
    "generic_intent": "resolver_helper",
    "declared_travel": "resolver",
    "in_chat_attack": "resolver",
    "adjudication": "resolver",
    "offscene_social_text": "downstream_consequence",
    "pending_check_prompt": "downstream_consequence",
    "resolution_contract": "contract_constructor",
    "interpretation_validation": "contract_validator",
}

SEGMENTATION_ROLE = "structural"
OFFSCENE_SOCIAL_CLASS = "downstream_consequence"
PENDING_CHECK_CLASS = "downstream_consequence"

_SOCIAL_ACTION_TYPES = frozenset(
    {
        "question",
        "social_probe",
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
    }
)
_MOVEMENT_TYPES = frozenset({"travel", "scene_transition"})
_PERCEPTION_TYPES = frozenset({"observe", "investigate", "inspect", "search"})
_UNCOMMITTED_OPS = frozenset({"act", "follow", "confirm"})

# Stages a resolver may execute. A stage not listed does not run.
_RESOLVER_STAGES: dict[str, frozenset[str]] = {
    "social": frozenset({"social", "dialogue_first"}),
    "exploration": frozenset({"pursuit", "world_action", "exploration"}),
    "world_action": frozenset({"passive_wait", "world_action", "generic_intent"}),
    "travel": frozenset({"travel", "exploration"}),
    "combat": frozenset({"generic_intent"}),
    "adjudication": frozenset(),
    "generation": frozenset({"passive_wait"}),
}

RESOLVER_CONTRACTS: dict[str, dict[str, Any]] = {
    "social": {
        "required": ("operation", "contract_id"),
        "optional": (
            "interlocutor_id",
            "raw_input",
            "dimension",
            "construction.commitment_status",
            "construction.resolution_subject",
        ),
        "state": ("scene roster", "session discourse focus"),
        "discourse": ("active interlocutor", "requested addressee"),
        "result": "social resolution",
        "state_change": "after accepted resolution",
        "failure": "preserve contract; contract-aware generation or nonresolution",
    },
    "exploration": {
        "required": ("operation", "contract_id"),
        "optional": ("dimension", "raw_input", "target"),
        "state": ("scene", "inspected object"),
        "discourse": ("active inspected target", "current scene"),
        "result": "inspection or perception resolution",
        "state_change": "after accepted resolution",
        "failure": "preserve contract; contract-aware generation",
    },
    "travel": {
        "required": ("operation", "contract_id", "construction.commitment_status"),
        "optional": ("raw_input", "target"),
        "state": ("authored exits", "current location"),
        "discourse": ("current scene",),
        "result": "route resolution or no transition",
        "state_change": "scene change only after accepted committed movement",
        "failure": "preserve contract; do not move",
    },
    "world_action": {
        "required": ("operation", "contract_id"),
        "optional": ("raw_input", "target"),
        "state": ("scene objects",),
        "discourse": ("current scene",),
        "result": "object-action resolution",
        "state_change": "after accepted resolution",
        "failure": "preserve contract; contract-aware generation",
    },
    "combat": {
        "required": ("operation", "contract_id"),
        "optional": ("raw_input",),
        "state": ("combat", "character attacks"),
        "discourse": ("current scene",),
        "result": "attack resolution derived from the contract",
        "state_change": "combat flags after the contract exists",
        "failure": "preserve contract; do not attack",
    },
    "adjudication": {
        "required": ("operation", "contract_id"),
        "optional": ("raw_input", "dimension", "interlocutor_id"),
        "state": ("scene", "character", "world"),
        "discourse": ("active interlocutor",),
        "result": "procedural answer",
        "state_change": "none in the resolver",
        "failure": "preserve contract; generation or safe nonresolution",
    },
    "generation": {
        "required": ("contract_id",),
        "optional": ("operation", "raw_input", "interlocutor_id"),
        "state": ("authoritative scene state",),
        "discourse": ("discourse focus",),
        "result": "narration or nonresolution",
        "state_change": "only from the accepted contract",
        "failure": "preserve contract",
    },
}


def establish_ordinary_gameplay_contract(
    resolution: dict,
    *,
    player_text: str | None,
    session: Mapping[str, Any] | None,
    scene_id: str | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    visible_turns: Any = None,
    normalized_action: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the one ordinary-gameplay contract before any specialized resolver.

    Deterministic fast path first. Structured interpretation runs only when that
    path abstains and the existing policy says a model proposal is appropriate.
    """
    from game.contract_adjudication_bridge import construction_source
    from game.live_resolution import attach_interaction_obligation
    from game.resolution_contract import contract_mapping_from_resolution

    contract_text = player_text
    bridge = (normalized_action or {}).get("metadata", {}).get("stored_interpretation", {})
    if bridge.get("operation") == "MOVE":
        # The visible-id bridge already grounded a committed movement. Feed
        # its canonical operation to the existing contract rather than asking
        # a narrower lexical parser to reinterpret the original declaration.
        contract_text = f"I travel to {normalized_action.get('label') or normalized_action.get('id')}."

    def _attach(enable_model: bool) -> None:
        attach_interaction_obligation(
            resolution,
            player_text=contract_text,
            session=session,
            normalized_action=normalized_action,
            scene_id=scene_id,
            scene=scene,
            world=world,
            visible_turns=visible_turns,
            enable_model_interpretation=enable_model,
        )

    _attach(False)
    contract = contract_mapping_from_resolution(resolution)
    if contract_text != player_text:
        contract["raw_input"] = player_text
        contract.setdefault("construction", {})["bridge_processing_input"] = contract_text
        resolution["metadata"]["resolution_contract"] = contract
    construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
    from game.live_chat_interpretation import live_interpretation_consumed

    if (
        construction.get("fast_path_abstained")
        and construction.get("model_interpretation_appropriate")
        and not live_interpretation_consumed()
    ):
        md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        md.pop("resolution_contract", None)
        md.pop("interaction_obligation", None)
        md.pop("gm_resolution_decision", None)
        resolution["metadata"] = md
        _attach(True)
        contract = contract_mapping_from_resolution(resolution)
    md = resolution.setdefault("metadata", {})
    if not isinstance(md, dict):
        md = {}
        resolution["metadata"] = md
    md["ordinary_contract_established"] = True
    md["semantic_owner"] = "resolution_contract"
    md["contract_before_resolver"] = bool(str(contract.get("contract_id") or "").strip())
    md["contract_construction_source"] = construction_source(contract)
    return contract if isinstance(contract, dict) else {}


def select_ordinary_resolver(
    contract: Mapping[str, Any] | None,
    *,
    in_combat: bool = False,
) -> tuple[str, str | None]:
    """Contract selects the resolver. Raw text does not race peer parsers.

    Returns ``(resolver, adjudication_family)``. An adjudication family is the
    C24 selector's result. ``generation`` means no specialized resolver.
    """
    if not contract_authorizes_specialized_resolution(contract):
        return ("generation", None)
    assert isinstance(contract, Mapping)
    operation = str(contract.get("operation") or "").strip().lower()
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    commitment = str(construction.get("commitment_status") or "").strip()
    subject = str(construction.get("resolution_subject") or "").strip()
    if operation in {"unresolved", "clarify"}:
        return ("generation", None)
    if operation in _UNCOMMITTED_OPS and commitment != EXECUTED_NOW:
        return ("generation", None)
    family = select_resolver_family(contract)
    if family:
        return ("adjudication", family)
    if subject == "combat":
        if in_combat and commitment == EXECUTED_NOW:
            return ("combat", None)
        return ("generation", None)
    if subject == "travel":
        return ("travel", None)
    if subject in {"perception", "exploration"} or operation in {"inspect", "perceive"}:
        return ("exploration", None)
    # An ask is social only when the contract named a social subject.
    # Repeat stays social. A leftover ask with no addressee is narration.
    if subject == "social" or operation == "repeat":
        return ("social", None)
    if subject == "world_action" or (operation in _UNCOMMITTED_OPS and commitment == EXECUTED_NOW):
        return ("world_action", None)
    return ("generation", None)


def stage_permitted(resolver_name: str | None, stage: str, contract: Mapping[str, Any] | None = None) -> bool:
    """Primary resolver stages, plus a committed travel obligation's travel stage.

    Passing no contract preserves the primary-resolver table. A recorded
    executed travel obligation may open the travel stage without making travel
    the contract operation.
    """
    if stage in _RESOLVER_STAGES.get(str(resolver_name or ""), frozenset()):
        return True
    if stage == "travel" and contract is not None:
        from game.player_commitment import committed_travel_recorded

        return committed_travel_recorded(contract)
    return False


def action_contradicts_contract(parsed: Mapping[str, Any] | None, contract: Mapping[str, Any] | None) -> bool:
    """True when a resolver result would replace the contract's operation."""
    if not isinstance(parsed, Mapping) or not isinstance(contract, Mapping):
        return False
    if not contract_authorizes_specialized_resolution(contract):
        return True
    operation = str(contract.get("operation") or "").strip().lower()
    action_type = str(parsed.get("type") or "").strip().lower()
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    commitment = str(construction.get("commitment_status") or "").strip()
    if action_type in _MOVEMENT_TYPES:
        from game.player_commitment import committed_travel_recorded

        # One travel stage owns the move. It does not replace the contract operation.
        if committed_travel_recorded(contract):
            return False
    if action_type in _MOVEMENT_TYPES or action_type == "attack":
        if commitment != EXECUTED_NOW or operation not in _UNCOMMITTED_OPS:
            return True
    if operation == "ask" and action_type in _MOVEMENT_TYPES | _PERCEPTION_TYPES | {"attack", "interact", "custom"}:
        return True
    if operation in {"inspect", "perceive"} and action_type in _SOCIAL_ACTION_TYPES | _MOVEMENT_TYPES | {"attack"}:
        return True
    if operation in _UNCOMMITTED_OPS and commitment == EXECUTED_NOW and action_type in _SOCIAL_ACTION_TYPES:
        return True
    return False


def reject_contradicting_action(parsed: dict | None, contract: Mapping[str, Any] | None) -> dict | None:
    if action_contradicts_contract(parsed, contract):
        return None
    return parsed


def carry_authoritative_contract(source: dict, dest: dict) -> dict:
    """Keep the pre-resolver contract when a resolver replaces the resolution object."""
    if dest is source or not isinstance(dest, dict) or not isinstance(source, dict):
        return dest
    src_md = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    contract = src_md.get("resolution_contract")
    if not isinstance(contract, dict) or not str(contract.get("contract_id") or "").strip():
        return dest
    md = dict(dest.get("metadata") if isinstance(dest.get("metadata"), dict) else {})
    existing = md.get("resolution_contract")
    if not (isinstance(existing, dict) and str(existing.get("contract_id") or "").strip()):
        md["resolution_contract"] = contract
    if src_md.get("interaction_obligation") and not md.get("interaction_obligation"):
        md["interaction_obligation"] = src_md.get("interaction_obligation")
    decision = src_md.get("gm_resolution_decision")
    if isinstance(decision, dict) and str(decision.get("contract_id") or "") == str(contract.get("contract_id") or ""):
        existing_decision = md.get("gm_resolution_decision")
        if not (
            isinstance(existing_decision, dict)
            and str(existing_decision.get("contract_id") or "") == str(contract.get("contract_id") or "")
        ):
            md["gm_resolution_decision"] = decision
    for key in (
        "ordinary_contract_established",
        "semantic_owner",
        "contract_before_resolver",
        "contract_construction_source",
        "selected_resolver",
    ):
        if key in src_md and key not in md:
            md[key] = src_md[key]
    dest["metadata"] = md
    return dest


def stamp_downstream_provenance(gm: dict, resolution: Mapping[str, Any] | None, *, kind: str) -> dict:
    """Mark engine text that is a consequence of an already established contract."""
    if not isinstance(gm, dict):
        return gm
    res_md = resolution.get("metadata") if isinstance(resolution, Mapping) and isinstance(resolution.get("metadata"), Mapping) else {}
    contract = res_md.get("resolution_contract") if isinstance(res_md.get("resolution_contract"), Mapping) else {}
    md = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
    md["emission_provenance"] = {
        "class": "downstream_consequence",
        "kind": kind,
        "contract_id": str(contract.get("contract_id") or ""),
        "operation": str(contract.get("operation") or ""),
        "semantic_owner": "resolution_contract",
    }
    gm["metadata"] = md
    tags = list(gm.get("tags") or [])
    tag = f"provenance:downstream_consequence:{kind}"
    if tag not in tags:
        tags.append(tag)
    gm["tags"] = tags
    return gm
