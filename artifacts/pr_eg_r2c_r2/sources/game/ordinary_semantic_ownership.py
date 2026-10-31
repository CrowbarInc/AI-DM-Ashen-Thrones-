"""Ordinary-gameplay semantic ownership.

One Resolution Contract answers what the player wants resolved. Specialized
systems answer how that contract is resolved. This module is the selection
boundary. It does not replace social, travel, exploration, or combat internals.

C24's adjudication bridge remains the resolver for presence, place, feasibility,
state, and roll questions. This module calls it. It does not reimplement it.
"""
from __future__ import annotations

import re
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
    if bridge.get("operation") == "ASK" and bridge.get("target_ref"):
        # A validated id may settle an abstention. It may not replace an
        # unresolved explicit person, and it may not outrank lexical grounding.
        import copy
        contract = copy.deepcopy(contract)
        proposed_id = str(bridge["target_ref"])
        prior = contract.get("interlocutor_id")
        construction = contract.setdefault("construction", {})
        construction["pre_bridge_addressee_binding"] = copy.deepcopy(construction.get("entity_binding"))
        old_binding = construction.get("entity_binding") or {}
        grounding = assess_addressee_grounding(
            player_text or "",
            scene=scene,
            world=world,
            session=session,
            proposed_target_id=proposed_id,
        )
        lexical_unresolved = bool(
            old_binding.get("explicit_new_interlocutor")
            and old_binding.get("status") in {"unresolved", "ambiguous", "rejected_consequential"}
        )
        grounded_id = str(grounding.get("target_id") or "")
        provider_not_authorized = grounding.get("operation_eligibility") == "requires_clarification" or (
            lexical_unresolved and grounding.get("operation_eligibility") != "executable"
        )
        if provider_not_authorized:
            construction["candidate_target_ids"] = list(grounding.get("candidate_target_ids") or [proposed_id])
            construction["conversational_authorization"] = conversational_authorization_record(
                grounding,
                player_text=player_text or "",
                authority_provenance="resolution_contract",
            )
            construction["authority_conflict"] = {
                "lexical_status": old_binding.get("status"),
                "bridge_target": proposed_id,
                "grounded_target": grounded_id or None,
            }
            contract["ambiguous"] = True
            contract["operation"] = "unresolved"
            contract["interlocutor_id"] = None
            contract["expected_resolution"] = "clarification"
        elif prior and prior != (grounded_id or proposed_id) and old_binding.get("explicit_new_interlocutor") and old_binding.get("status") == "bound_canonical":
            construction["authority_conflict"] = {"contract_target": prior, "bridge_target": proposed_id}
            construction["validation_status"] = "abstained"
            contract["ambiguous"] = True
            contract["operation"] = "unresolved"
        else:
            target_id = grounded_id or proposed_id
            contract.update(operation="ask", interlocutor_id=target_id, expected_resolution="answer", ambiguous=False)
            binding = construction.setdefault("entity_binding", {})
            binding.update(status="bound_canonical", bound_interlocutor_id=target_id,
                           entity_id=target_id, label=normalized_action.get("label") or target_id,
                           authority_reasons=["identity:validated_interpretation_bridge"])
            construction.update(interlocutor_rejected=False, addressee_binding_status="bound_canonical")
            construction["conversational_authorization"] = conversational_authorization_record(
                grounding if grounded_id else {**grounding, "target_id": target_id, "operation_eligibility": "executable", "mutation_eligibility": True},
                player_text=player_text or "",
                authority_provenance="resolution_contract",
            )
        resolution["metadata"]["resolution_contract"] = contract
        obligation = resolution["metadata"].get("interaction_obligation")
        if isinstance(obligation, dict) and not construction.get("authority_conflict"):
            obligation["interlocutor_id"] = contract.get("interlocutor_id")
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
    if isinstance(contract, dict):
        construction = contract.setdefault("construction", {})
        if "conversational_authorization" not in construction:
            binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), dict) else {}
            blocked_addressee = bool(
                binding.get("explicit_new_interlocutor")
                and binding.get("status") in {"unresolved", "ambiguous", "rejected_consequential"}
                and str(contract.get("operation") or "") == "ask"
            )
            if blocked_addressee:
                contract["ambiguous"] = True
                contract["operation"] = "unresolved"
                contract["interlocutor_id"] = None
                construction["conversational_authorization"] = conversational_authorization_record(
                    {
                        "communication_ownership": "ambiguous_unresolved",
                        "intent_purpose": "address_npc",
                        "target_resolution": "ambiguous" if binding.get("status") == "ambiguous" else "unresolved",
                        "target_provenance": "none",
                        "target_id": None,
                        "candidate_target_ids": [],
                        "operation_eligibility": "requires_clarification",
                        "mutation_eligibility": False,
                        "conflict_status": "none",
                        "pending_intention_relationship": "requires_clarification",
                        "allowed_operation": None,
                        "clarification": "Which person do you mean? Nothing has been attempted.",
                    },
                    player_text=player_text or "",
                    authority_provenance="lexical_addressee",
                )
                resolution["metadata"]["resolution_contract"] = contract
            else:
                operation = str(contract.get("operation") or "")
                consequential = operation not in {"", "unresolved", "clarify"}
                construction["conversational_authorization"] = conversational_authorization_record(
                    {
                        "communication_ownership": "character_action" if consequential else "gm_directed",
                        "intent_purpose": "perform_action" if consequential else "request_information",
                        "target_resolution": "explicit" if contract.get("interlocutor_id") else "none_required",
                        "target_provenance": "explicit_canonical" if contract.get("interlocutor_id") else "none",
                        "target_id": contract.get("interlocutor_id"),
                        "candidate_target_ids": [],
                        "operation_eligibility": "executable" if consequential else "no_consequential_operation",
                        "mutation_eligibility": consequential,
                        "conflict_status": "none",
                        "pending_intention_relationship": "starts_new" if consequential else "none",
                        "allowed_operation": operation or None,
                    },
                    player_text=player_text or "",
                    authority_provenance="resolution_contract",
                )
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
    social = dest.get("social")
    if isinstance(social, dict) and social.get("target_resolved") is True:
        # Compact provenance over the existing result; this grants no knowledge
        # beyond the selected topic and never authorizes extra state changes.
        md["authoritative_result"] = {
            "source": "social_resolver", "operation": "ask",
            "target_id": social.get("npc_id"), "target_label": social.get("npc_name"),
            "target_resolved": True, "outcome": social.get("reply_kind"),
            "state_changes": dest.get("state_changes") or {},
            "player_visible_facts": social.get("topic_revealed"),
            "information_authority": social.get("npc_speech_authority"),
            "response_constraints": ["preserve_speaker", "selected_topic_only", "no_unapproved_mutations"],
        }
        import copy
        held = copy.deepcopy(md["resolution_contract"])
        construction = held.setdefault("construction", {})
        binding = construction.get("entity_binding") or {}
        target = str(social.get("npc_id") or "")
        prior = held.get("interlocutor_id")
        unresolved_explicit = (binding.get("explicit_new_interlocutor")
                               and binding.get("status") in {"unresolved", "ambiguous", "rejected_consequential"})
        # A legacy unresolved explicit person remains protected. The earlier
        # validated-id bridge can settle it; a fallback NPC cannot.
        if construction.get("authority_conflict") or (prior and prior != target) or unresolved_explicit:
            construction["authority_conflict"] = {"contract_target": prior, "social_target": target,
                                                   "unresolved_explicit": bool(unresolved_explicit)}
        elif target and held.get("operation") in {"ask", "unresolved"}:
            construction["pre_social_binding"] = copy.deepcopy(binding)
            held.update(operation="ask", interlocutor_id=target, expected_resolution="answer")
            binding = dict(binding)
            binding.update(status="bound_canonical", bound_interlocutor_id=target,
                           label=social.get("npc_name") or target,
                           authority_reasons=["identity:social_resolver"])
            construction["entity_binding"] = binding
        md["resolution_contract"] = held
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


_NONUNIQUE_ADDRESSEE_RE = re.compile(
    r"\b(?:one|some|any|either|another)\s+of\s+(?:them|those|these|the\b)|"
    r"\b(?:someone|somebody|anyone|anybody)\b",
    re.IGNORECASE,
)
_ASK_VERB_RE = re.compile(
    r"\b(?:ask|asking|tell|warn|inform|address|speak|talk)\b",
    re.IGNORECASE,
)
_SECOND_PERSON_RE = re.compile(r"\b(?:you|your|you're|youre)\b", re.IGNORECASE)
_THIRD_PERSON_RE = re.compile(r"\b(?:she|he|her|him|his|hers)\b", re.IGNORECASE)
_SINGULAR_PRONOUNS = frozenset({"him", "her", "he", "she"})
_PLURAL_PRONOUNS = frozenset({"them", "they", "those"})
_DETERMINERS = frozenset({"the", "a", "an", "that", "this"})
# Narration is unnecessary only when the resolver has already closed the
# reply. A missing fact, a characterization opening, or claim_only speech
# stays eligible for generation. PR-EG may later attach a non-persisted
# proposal; this predicate must not treat every unknown as a refusal.
DETERMINED_NONRESOLUTION_PLANS = frozenset({
    "consequential_information_request",
})


def conversational_authorization_record(
    grounding: Mapping[str, Any],
    *,
    player_text: str,
    authority_provenance: str,
) -> dict[str, Any]:
    """One disposition record. Later stages read it; they do not replace it."""
    return {
        "communication_ownership": grounding.get("communication_ownership") or "ambiguous_unresolved",
        "intent_purpose": grounding.get("intent_purpose") or "address_npc",
        "target_resolution": grounding.get("target_resolution") or "unresolved",
        "target_provenance": grounding.get("target_provenance") or "none",
        "target_id": grounding.get("target_id"),
        "candidate_target_ids": list(grounding.get("candidate_target_ids") or []),
        "operation_eligibility": grounding.get("operation_eligibility") or "requires_clarification",
        "mutation_eligibility": bool(grounding.get("mutation_eligibility")),
        "authority_provenance": authority_provenance,
        "conflict_status": grounding.get("conflict_status") or "none",
        "conflict_details": dict(grounding.get("conflict_details") or {}),
        "pending_intention_relationship": grounding.get("pending_intention_relationship") or "none",
        "allowed_operation": grounding.get("allowed_operation"),
        "clarification": grounding.get("clarification") or "",
        "choices": list(grounding.get("choices") or []),
        "direct_address": bool(grounding.get("direct_address")),
        "player_text": player_text[:500],
    }


def _visible_npcs(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    from game.player_interpretation_bridge import visible_catalog

    catalog = visible_catalog(scene if isinstance(scene, dict) else {}, world if isinstance(world, dict) else {})
    return [dict(info["row"]) for info in catalog.values() if info.get("kind") == "npc" and isinstance(info.get("row"), dict)]


def _npc_words(npc: Mapping[str, Any]) -> set[str]:
    parts = [npc.get("name"), npc.get("label"), str(npc.get("id") or "").replace("_", " "), npc.get("role")]
    parts.extend(npc.get("aliases") or [])
    words: set[str] = set()
    for part in parts:
        words.update(re.findall(r"[a-z0-9']+", str(part or "").lower()))
    return {word for word in words if word and word not in _DETERMINERS}


def _content_words(nominal: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9']+", nominal.lower()) if word not in _DETERMINERS]


def _npc_public_blob(npc: Mapping[str, Any], scene: Mapping[str, Any] | None) -> str:
    """Own description plus scene sentences that name this person.

    A shared scene sentence does not make every visible person the referent
    of a distinguishing word.
    """
    from game.incidental_entity import public_scene_text

    pieces = [
        str(npc.get("name") or ""),
        str(npc.get("description") or ""),
        str(npc.get("summary") or ""),
        str(npc.get("role") or ""),
    ]
    name = str(npc.get("name") or "").lower()
    if name:
        for sentence in re.split(r"[.!?]", public_scene_text(scene)):
            if name in sentence.lower():
                pieces.append(sentence)
    return " ".join(pieces).lower()


def _scene_id_of(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    inner = scene.get("scene") if isinstance(scene.get("scene"), Mapping) else scene
    return str(inner.get("id") or "")


def _active_npc_id(session: Mapping[str, Any] | None, npcs: list[Mapping[str, Any]]) -> str:
    if not isinstance(session, Mapping):
        return ""
    ctx = session.get("interaction_context")
    if not isinstance(ctx, Mapping):
        return ""
    if str(ctx.get("active_interaction_kind") or "").lower() != "social":
        return ""
    target = str(ctx.get("active_interaction_target_id") or "")
    ids = {str(npc.get("id") or "") for npc in npcs}
    return target if target in ids else ""


def _choice(npc: Mapping[str, Any]) -> dict[str, str]:
    label = str(npc.get("name") or npc.get("label") or npc.get("id") or "")
    return {"entity_id": str(npc.get("id") or ""), "label": label}


def _clarification_for(npcs: list[Mapping[str, Any]], *, single_offer: bool) -> str:
    labels = [str(npc.get("name") or npc.get("label") or npc.get("id")) for npc in npcs]
    labels = [label for label in labels if label]
    if single_offer and len(labels) == 1:
        return f"Do you mean {labels[0]}? Nothing has been attempted."
    if labels:
        return "Which person do you mean: " + " or ".join(labels) + "? Nothing has been attempted."
    return "Which person do you mean? Nothing has been attempted."


def assess_addressee_grounding(
    player_text: str,
    *,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    proposed_target_id: str | None = None,
) -> dict[str, Any]:
    """Decide whether a person reference is grounded enough to attempt.

    A provider id is a candidate. It authorizes nothing by itself. Explicit
    names and unique contextual referents resolve. Quantified or unmatched
    references stay unresolved even when one visible person would be convenient.
    """
    from game.interaction_completion import addressed_person_nominal

    text = " ".join(str(player_text or "").split())
    npcs = _visible_npcs(scene, world)
    proposed = str(proposed_target_id or "").strip() or None
    nominal = addressed_person_nominal(text)
    direct = bool(nominal) or bool(_ASK_VERB_RE.search(text) and nominal)
    words = _content_words(nominal)
    base = {
        "communication_ownership": "npc_directed" if direct else "gm_directed",
        "intent_purpose": "address_npc" if direct else "request_information",
        "target_resolution": "none_required",
        "target_provenance": "none",
        "target_id": None,
        "candidate_target_ids": [proposed] if proposed else [],
        "operation_eligibility": "not_assessed",
        "mutation_eligibility": True,
        "conflict_status": "none",
        "conflict_details": {},
        "pending_intention_relationship": "none",
        "allowed_operation": None,
        "clarification": "",
        "choices": [_choice(npc) for npc in npcs],
        "direct_address": bool(nominal),
    }
    if not npcs or not nominal:
        if nominal and not npcs:
            return base
        third_person_about_npc = bool(_THIRD_PERSON_RE.search(text)) and not _SECOND_PERSON_RE.search(text)
        if not nominal and proposed and _active_npc_id(session, npcs) == proposed and not third_person_about_npc:
            return {
                **base,
                "communication_ownership": "npc_directed",
                "intent_purpose": "address_npc",
                "target_resolution": "contextual",
                "target_provenance": "established_interlocutor",
                "target_id": proposed,
                "operation_eligibility": "executable",
                "mutation_eligibility": True,
                "allowed_operation": "ask",
                "pending_intention_relationship": "continues",
                "direct_address": False,
            }
        if not nominal and proposed and _ASK_VERB_RE.search(text):
            mentioned = [
                npc for npc in npcs
                if _npc_words(npc) & set(_content_words(text)) and any(len(word) > 2 and word in text.lower() for word in _npc_words(npc))
            ]
            if len(mentioned) == 1:
                npc = mentioned[0]
                target_id = str(npc.get("id") or "")
                provenance = "explicit_canonical" if str(npc.get("name") or "").lower() in text.lower() else "unique_contextual"
                return {
                    **base,
                    "communication_ownership": "npc_directed",
                    "direct_address": True,
                    "target_resolution": "explicit" if provenance == "explicit_canonical" else "contextual",
                    "target_provenance": provenance,
                    "target_id": target_id,
                    "operation_eligibility": "executable",
                    "mutation_eligibility": True,
                    "allowed_operation": "ask",
                    "pending_intention_relationship": "starts_new",
                    "conflict_status": "resolved_by_explicit_wording" if proposed and proposed != target_id else "none",
                    "conflict_details": {"provider_target": proposed, "grounded_target": target_id} if proposed and proposed != target_id else {},
                }
            # An ask that names nobody is not an unresolved person reference.
            # Continuation, mixed intent, and the bridge decide it.
        return base

    nonunique = bool(_NONUNIQUE_ADDRESSEE_RE.search(nominal)) or bool(
        re.search(r"\b(?:either|any|another)\s+(?!of\b)", nominal, re.IGNORECASE)
    )
    if any(word in _PLURAL_PRONOUNS for word in words) or nonunique or _NONUNIQUE_ADDRESSEE_RE.search(nominal):
        return {
            **base,
            "direct_address": True,
            "communication_ownership": "ambiguous_unresolved",
            "target_resolution": "ambiguous",
            "target_provenance": "provider_candidate_only" if proposed else "none",
            "operation_eligibility": "requires_clarification",
            "mutation_eligibility": False,
            "allowed_operation": None,
            "pending_intention_relationship": "requires_clarification",
            "clarification": _clarification_for(npcs, single_offer=len(npcs) == 1),
            "conflict_status": "unresolved" if proposed else "none",
            "conflict_details": {"provider_target": proposed} if proposed else {},
        }

    if len(words) == 1 and words[0] in _SINGULAR_PRONOUNS:
        active = _active_npc_id(session, npcs)
        chosen = ""
        provenance = ""
        if active and (not proposed or proposed == active):
            chosen, provenance = active, "established_interlocutor"
        elif len(npcs) == 1 and (not proposed or proposed == str(npcs[0].get("id") or "")):
            chosen, provenance = str(npcs[0].get("id") or ""), "unique_contextual"
        elif active and proposed and proposed != active:
            return {
                **base,
                "direct_address": True,
                "communication_ownership": "ambiguous_unresolved",
                "target_resolution": "ambiguous",
                "target_provenance": "provider_candidate_only",
                "operation_eligibility": "requires_clarification",
                "mutation_eligibility": False,
                "clarification": _clarification_for(npcs, single_offer=False),
                "conflict_status": "unresolved",
                "conflict_details": {"established_interlocutor": active, "provider_target": proposed},
                "pending_intention_relationship": "requires_clarification",
            }
        elif len(npcs) != 1:
            return {
                **base,
                "direct_address": True,
                "communication_ownership": "ambiguous_unresolved",
                "target_resolution": "ambiguous",
                "target_provenance": "none",
                "operation_eligibility": "requires_clarification",
                "mutation_eligibility": False,
                "clarification": _clarification_for(npcs, single_offer=False),
                "pending_intention_relationship": "requires_clarification",
                "conflict_status": "unresolved" if proposed else "none",
            }
        if chosen:
            return {
                **base,
                "direct_address": True,
                "communication_ownership": "npc_directed",
                "target_resolution": "contextual",
                "target_provenance": provenance,
                "target_id": chosen,
                "operation_eligibility": "executable",
                "mutation_eligibility": True,
                "allowed_operation": "ask",
                "pending_intention_relationship": "continues" if provenance == "established_interlocutor" else "starts_new",
            }

    hits = [npc for npc in npcs if set(words) & _npc_words(npc)]
    extras = [word for word in words if not any(word in _npc_words(npc) for npc in hits)]
    ambiguous_extras = False
    else_provenance = ""
    if len(hits) > 1 and extras:
        narrowed = [npc for npc in hits if all(extra in _npc_public_blob(npc, scene) for extra in extras)]
        if len(narrowed) == 1:
            hits = narrowed
            else_provenance = "authoritative_world_state"
        else:
            hits = []
            ambiguous_extras = True
    elif len(hits) > 1:
        ambiguous_extras = True
    if len(hits) == 1:
        npc = hits[0]
        target_id = str(npc.get("id") or "")
        proper = str(npc.get("name") or "").lower() in text.lower() or target_id.replace("_", " ") in text.lower()
        provenance = else_provenance or ("explicit_canonical" if proper else "unique_contextual")
        conflict = "resolved_by_explicit_wording" if proposed and proposed != target_id else "none"
        return {
            **base,
            "direct_address": True,
            "communication_ownership": "npc_directed",
            "target_resolution": "explicit" if provenance == "explicit_canonical" else "contextual",
            "target_provenance": provenance,
            "target_id": target_id,
            "operation_eligibility": "executable",
            "mutation_eligibility": True,
            "allowed_operation": "ask",
            "pending_intention_relationship": "starts_new",
            "conflict_status": conflict,
            "conflict_details": {"provider_target": proposed, "grounded_target": target_id} if conflict != "none" else {},
        }
    if ambiguous_extras or hits:
        return {
            **base,
            "direct_address": True,
            "communication_ownership": "ambiguous_unresolved",
            "target_resolution": "ambiguous",
            "target_provenance": "provider_candidate_only" if proposed else "none",
            "operation_eligibility": "requires_clarification",
            "mutation_eligibility": False,
            "clarification": _clarification_for(hits or npcs, single_offer=False),
            "choices": [_choice(npc) for npc in (hits or npcs)],
            "pending_intention_relationship": "requires_clarification",
            "conflict_status": "unresolved" if proposed else "none",
        }
    return {
        **base,
        "direct_address": True,
        "communication_ownership": "ambiguous_unresolved",
        "target_resolution": "unresolved",
        "target_provenance": "provider_candidate_only" if proposed else "none",
        "operation_eligibility": "requires_clarification",
        "mutation_eligibility": False,
        "clarification": _clarification_for(npcs, single_offer=len(npcs) == 1),
        "pending_intention_relationship": "requires_clarification",
        "conflict_status": "unresolved" if proposed else "none",
    }


def pending_addressee_clarification(grounding: Mapping[str, Any], player_text: str, scene: Mapping[str, Any] | None) -> dict[str, Any]:
    choices = list(grounding.get("choices") or [])
    return {
        "kind": "ambiguous_addressee",
        "operation": "ASK",
        "status": "pending",
        "scene_id": _scene_id_of(scene),
        "original_text": player_text,
        "choices": choices,
        "clarification": grounding.get("clarification") or "",
        "target_resolution": grounding.get("target_resolution") or "ambiguous",
    }


def social_narration_unnecessary(resolution: Mapping[str, Any] | None) -> bool:
    """True when no generated alternative can be accepted.

    Requires a resolved social result whose speech authority is already none,
    whose reply plan is a closed nonresolution, and which did not select an
    authored topic or permit subjective characterization. Ordinary missing
    details and claim_only characterization stay on the provider path.
    """
    if not isinstance(resolution, Mapping):
        return False
    social = resolution.get("social")
    if not isinstance(social, Mapping):
        return False
    if social.get("target_resolved") is not True:
        return False
    if social.get("topic_revealed"):
        authority = social.get("dialogue_authority")
        if (
            isinstance(authority, Mapping)
            and authority.get("reuse_prior_speech")
            and str(authority.get("player_line") or "").strip()
        ):
            return True
        return False
    if social.get("incidental_subjective_allowed") is True:
        return False
    authority = social.get("dialogue_authority")
    if (
        isinstance(authority, Mapping)
        and authority.get("narration_determined") is True
        and social.get("incidental_subjective_allowed") is not True
        and str(social.get("npc_speech_authority") or "") == "none"
    ):
        return True
    if str(social.get("npc_speech_authority") or "") != "none":
        return False
    return str(social.get("reply_plan_kind") or "") in DETERMINED_NONRESOLUTION_PLANS
