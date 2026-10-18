from __future__ import annotations

import re
import time

from game.storage import (
    append_debug_trace,
    save_session,
    apply_repeated_description_guard,
    update_scene_momentum_runtime,
    list_scene_ids,
    load_scene,
)
from game.output_sanitizer import (
    extract_player_text_from_serialized_payload,
    resembles_serialized_response_payload,
    sanitize_player_facing_output,
    strip_serialized_payload_fragments,
)
from game.upstream_response_repairs import (
    SANITIZER_BOUNDARY_STRIP_ONLY,
    merge_upstream_prepared_emission_into_gm_output,
)
from game.final_emission_runtime import finalize_player_facing_emission as apply_final_emission_gate
from game.final_emission_validators import candidate_satisfies_scene_opening_contract
from game.narration_state_consistency import reconcile_final_text_with_structured_state
from game.social_exchange_policy import strict_social_emission_will_apply
from game.interaction_context import inspect as inspect_interaction_context
from game.bounded_improvisation import (
    IMPROVISATION_AUTHORITY_KEY,
    attach_bounded_improvisation_evaluation,
)
from game.live_resolution import (
    interaction_obligation_from_resolution,
    obligation_preserving_fallback_line,
)
from game.prompt_context import derive_narration_obligations
from game.response_type_gating import compact_response_type_contract
from game.social import SOCIAL_KINDS
from game.clues import get_known_clues_with_presentation
from game.affordances import get_available_affordances
from game.scene_graph import build_scene_graph
from game.opening_visible_fact_selection import select_opening_narration_visible_facts
from game import leads as leads_module


AUTHORITATIVE_TURN_STAGE_ORDER: tuple[str, ...] = (
    'player_input',
    'intent_normalization_expansion',
    'action_classification',
    'engine_resolution',
    'authoritative_state_mutation',
    'prompt_context_construction',
    'gpt_narration',
    'affordance_derivation',
    'response_debug_packaging',
)


def _now_perf() -> float:
    return time.perf_counter()


def _elapsed_ms(start: float) -> int:
    return max(0, int(round((time.perf_counter() - start) * 1000)))


def _accumulate_latency(latency_sink: dict | None, key: str, elapsed_ms: int) -> None:
    if not isinstance(latency_sink, dict):
        return
    latency_sink[key] = max(0, int(latency_sink.get(key, 0) or 0)) + max(0, int(elapsed_ms or 0))


def _scene_for_final_emission_input(scene: dict | None, resolution: dict | None) -> dict | None:
    """Opening turns pass the same curated visible-fact slice used by prompt inputs."""
    if not isinstance(scene, dict):
        return scene
    if not isinstance(resolution, dict) or str(resolution.get("kind") or "").strip().lower() != "scene_opening":
        return scene
    inner = scene.get("scene") if isinstance(scene.get("scene"), dict) else scene
    curated = select_opening_narration_visible_facts(inner if isinstance(inner, dict) else {})
    if not curated or not isinstance(inner, dict):
        return scene
    if isinstance(scene.get("scene"), dict):
        return {**scene, "scene": {**inner, "visible_facts": curated}}
    return {**inner, "visible_facts": curated}


def _merge_emergent_actor_debug_into_action_debug(session: dict) -> None:
    lad = session.get("last_action_debug")
    if not isinstance(lad, dict):
        return
    em = session.get("emergent_actor_debug") if isinstance(session.get("emergent_actor_debug"), dict) else {}
    lad["emergent_actor_enrolled"] = bool(em.get("emergent_actor_enrolled"))
    lad["emergent_actor_id"] = em.get("emergent_actor_id")
    lad["emergent_actor_source_text"] = em.get("emergent_actor_source_text")


def _build_action_debug(
    last_action_type: str,
    player_input: str,
    normalized_action: dict | None,
    resolution: dict | None,
    response_type_contract: dict | None = None,
) -> dict:
    """Build sanitized debug payload for action pipeline. No hidden facts or secrets."""
    debug: dict = {
        'last_action_type': last_action_type,
        'player_input': player_input or '',
        'normalized_action': None,
        'resolution_kind': None,
        'target_scene': None,
        'resolver_result': None,
        'scene_transition': None,
    }
    if normalized_action and isinstance(normalized_action, dict):
        safe_norm = {k: v for k, v in normalized_action.items() if k in ('id', 'label', 'type', 'prompt', 'targetSceneId', 'target_scene_id')}
        debug['normalized_action'] = safe_norm
    if resolution and isinstance(resolution, dict):
        debug['resolution_kind'] = resolution.get('kind')
        if resolution.get('resolved_transition') and resolution.get('target_scene_id'):
            debug['target_scene'] = resolution.get('target_scene_id')
            debug['scene_transition'] = {
                'from': resolution.get('originating_scene_id') or '(previous)',
                'to': resolution.get('target_scene_id'),
            }
        safe_keys = {'kind', 'resolved_transition', 'target_scene_id', 'originating_scene_id',
                     'same_scene_transition_suppressed', 'transition_applied',
                     'action_id', 'label', 'prompt', 'hint', 'attack_id', 'skill_id', 'spell_id',
                     'roll', 'damage', 'total', 'hit', 'round', 'active_actor_id', 'world_tick_events',
                     'clue_id', 'clue_text', 'discovered_clues', 'state_changes', 'success', 'skill_check',
                     'requires_check', 'check_request',
                     'combat', 'social', 'adjudication'}
        debug['resolver_result'] = {k: v for k, v in resolution.items() if k in safe_keys}
        nsc = None
        md = resolution.get('metadata')
        if isinstance(md, dict):
            nsc = md.get('narration_state_consistency')
            if isinstance(nsc, dict):
                debug['narration_state_mismatch_detected'] = bool(nsc.get('narration_state_mismatch_detected'))
                debug['mismatch_kind'] = nsc.get('mismatch_kind') or ''
                debug['mismatch_repair_applied'] = nsc.get('mismatch_repair_applied') or 'none'
                mra = nsc.get('mismatch_repairs_applied')
                debug['mismatch_repairs_applied'] = list(mra) if isinstance(mra, list) else []
            mal = md.get('minimum_actionable_lead')
            if isinstance(mal, dict):
                debug['minimum_actionable_lead_enforced'] = bool(mal.get('minimum_actionable_lead_enforced'))
                debug['enforced_lead_id'] = mal.get('enforced_lead_id')
                debug['enforced_lead_source'] = mal.get('enforced_lead_source')
    compact_contract = compact_response_type_contract(response_type_contract)
    if compact_contract:
        debug["response_type_contract"] = compact_contract
    return debug


def _strip_internal_gm_keys(gm: dict) -> dict:
    out = dict(gm)
    out.pop("_player_facing_emission_finalized", None)
    out.pop("_final_delivery_seal", None)
    # Emission debug/meta sidecar (author channel); must not ship on the public gm_output surface.
    out.pop("internal_state", None)
    return out


def _player_facing_text_for_lead_extraction(gm: dict | None) -> str:
    """Raw GM player-facing string before emission gate, for deterministic lead extraction."""
    if not isinstance(gm, dict):
        return ""
    raw_text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    if resembles_serialized_response_payload(raw_text):
        extracted = extract_player_text_from_serialized_payload(raw_text)
        raw_text = (
            extracted
            if isinstance(extracted, str) and extracted.strip()
            else strip_serialized_payload_fragments(raw_text)
        )
    return raw_text


def _session_ongoing_social_exchange(session: dict | None) -> bool:
    """True when an authoritative social interlocutor is locked (interaction_mode + target)."""
    if not isinstance(session, dict):
        return False
    ctx = inspect_interaction_context(session)
    return (
        str(ctx.get("interaction_mode") or "").strip().lower() == "social"
        and bool(str(ctx.get("active_interaction_target_id") or "").strip())
    )


def _accepted_bounded_resolution_text(gm: dict | None) -> str:
    if not isinstance(gm, dict):
        return ""
    authority = gm.get(IMPROVISATION_AUTHORITY_KEY)
    if not isinstance(authority, dict):
        return ""
    accepted = authority.get("accepted")
    if not isinstance(accepted, list):
        return ""
    for entry in accepted:
        if not isinstance(entry, dict):
            continue
        content = str(entry.get("content") or "").strip()
        if content:
            return content
    return ""


def _looks_like_generic_resolution_fallback(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return True
    return any(
        phrase in low
        for phrase in (
            "do not know enough to answer",
            "don't know enough to answer",
            "cannot answer that from what",
            "can't answer that from what",
            "the murmur around you never tightens",
            "the moment passes without anyone stepping forward",
            "nothing new resolves",
            "closer looking yields nothing further",
            "inspection yields no further",
            "the action resolves",
            "action resolves",
            "the action is resolved",
        )
    )


def _word_tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9']+", str(text or "").lower()) if len(token) >= 3}


def _scene_obj(scene: dict | None) -> dict:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, dict) else scene


def _visible_interactable_text(scene: dict | None, target_id: str) -> str:
    if not target_id:
        return ""
    scene_obj = _scene_obj(scene)
    for item in scene_obj.get("interactables") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("id") or "").strip() != target_id:
            continue
        for key in ("description", "visible_text", "summary", "label"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _authoritative_resolution_fact_text(
    *,
    resolution: dict | None,
    scene: dict | None,
    world: dict | None,
) -> tuple[str, dict]:
    """Build a non-inventive player-facing line from public resolver-owned facts."""
    if not isinstance(resolution, dict):
        return "", {}
    kind = str(resolution.get("kind") or "").strip().lower()
    if resolution.get("success") is False:
        if kind in {"scene_transition", "travel"}:
            target = str(resolution.get("target_scene_id") or "").strip()
            line = (
                f"You try to move toward {target.replace('_', ' ')}, but the route does not open from here."
                if target
                else "You try to move, but no reachable destination is established from here."
            )
            return line, {"kind": kind, "source": "failed_transition"}
        if kind in {"investigate", "observe", "discover_clue", "already_searched"}:
            return "You inspect the target, but nothing new is established.", {
                "kind": kind,
                "source": "failed_inspection",
            }
    if kind in {"scene_transition", "travel"} and resolution.get("resolved_transition") and resolution.get("target_scene_id"):
        scene_obj = _scene_obj(scene)
        location = str(scene_obj.get("location") or "").strip()
        summary = str(scene_obj.get("summary") or "").strip()
        destination = location or str(resolution.get("target_scene_id") or "").replace("_", " ").strip()
        if summary and destination and destination.lower() not in summary.lower():
            return f"You arrive at {destination}. {summary}", {"kind": kind, "source": "scene_transition"}
        if summary:
            return f"You arrive. {summary}", {"kind": kind, "source": "scene_transition"}
        if destination:
            return f"You arrive at {destination}.", {"kind": kind, "source": "scene_transition"}
    if kind in {"discover_clue", "investigate", "observe"}:
        clue_text = str(resolution.get("clue_text") or "").strip()
        if not clue_text:
            clues = resolution.get("discovered_clues")
            if isinstance(clues, list):
                clue_text = next((str(c).strip() for c in clues if isinstance(c, str) and str(c).strip()), "")
        if clue_text:
            target = str(resolution.get("interactable_id") or resolution.get("action_id") or "").strip()
            if target:
                return f"You inspect {target.replace('_', ' ')}. {clue_text}", {
                    "kind": kind,
                    "source": "clue_text",
                }
            return clue_text, {"kind": kind, "source": "clue_text"}
        md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        surface_text = ""
        for key in ("referenced_surface_inspectable_text", "referenced_surface_visible_fact", "scene_grounding_text"):
            value = md.get(key)
            if isinstance(value, str) and value.strip() and not _looks_like_generic_resolution_fallback(value):
                surface_text = value.strip()
                break
        if not surface_text:
            surface_text = _visible_interactable_text(scene, str(resolution.get("action_id") or "").strip())
        if surface_text:
            return surface_text, {"kind": kind, "source": "visible_surface_text"}
    if kind in SOCIAL_KINDS:
        social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else {}
        topic_text = str(topic.get("text") or topic.get("clue_text") or "").strip()
        npc_name = str(social.get("npc_name") or "").strip()
        if topic_text and npc_name:
            return f"{npc_name} answers: {topic_text}", {"kind": kind, "source": "social_topic"}
        if topic_text:
            return topic_text, {"kind": kind, "source": "social_topic"}
    return "", {}


def _preserve_authoritative_resolution_facts_after_gate(
    gm: dict | None,
    *,
    resolution: dict | None,
    scene: dict | None,
    world: dict | None,
) -> None:
    from game.immutable_valid_response import leave_text_unchanged

    if leave_text_unchanged(gm, "_preserve_authoritative_resolution_facts_after_gate"):
        return
    if not isinstance(gm, dict) or not isinstance(resolution, dict):
        return
    candidate, source = _authoritative_resolution_fact_text(resolution=resolution, scene=scene, world=world)
    if not candidate:
        return
    current = str(gm.get("player_facing_text") or "").strip()
    candidate_terms = _word_tokens(candidate)
    current_terms = _word_tokens(current)
    key_terms = {term for term in candidate_terms if len(term) >= 5}
    missing_key_fact = bool(key_terms) and len(key_terms & current_terms) < max(1, min(2, len(key_terms)))
    if current and not _looks_like_generic_resolution_fallback(current) and not missing_key_fact:
        return
    gm["player_facing_text"] = candidate
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    if "authoritative_resolution_fact_preserved" not in tags:
        tags.append("authoritative_resolution_fact_preserved")
    gm["tags"] = tags
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["authoritative_resolution_fact_preservation"] = {
                "applied": True,
                "source": source,
                "replaced_preview": current[:180],
                "candidate_preview": candidate[:180],
            }


def _preserve_accepted_bounded_resolution_after_gate(gm: dict | None, *, before_text: str, after_text: str) -> None:
    from game.immutable_valid_response import leave_text_unchanged

    if leave_text_unchanged(gm, "_preserve_accepted_bounded_resolution_after_gate"):
        return
    if not isinstance(gm, dict):
        return
    accepted_text = _accepted_bounded_resolution_text(gm)
    if not accepted_text:
        return
    before = str(before_text or "").strip()
    after = str(after_text or "").strip()
    if after and not _looks_like_generic_resolution_fallback(after):
        return
    gm["player_facing_text"] = accepted_text
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    if "accepted_bounded_resolution_delivered" not in tag_list:
        tag_list.append("accepted_bounded_resolution_delivered")
    gm["tags"] = tag_list
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["accepted_bounded_resolution_delivery"] = {
                "applied": True,
                "reason": "generic_fallback_after_accepted_bounded_resolution",
                "accepted_text_len": len(accepted_text),
                "pre_gate_text_preview": before[:180],
                "post_gate_text_preview": after[:180],
            }


def _preserve_physical_action_resolution_after_gate(
    gm: dict | None,
    *,
    resolution: dict | None,
    before_text: str,
    after_text: str,
) -> None:
    """Keep a resolved physical action from collapsing into unrelated scene or social fallback."""
    from game.immutable_valid_response import leave_text_unchanged

    if leave_text_unchanged(gm, "_preserve_physical_action_resolution_after_gate"):
        return
    if not isinstance(gm, dict) or not isinstance(resolution, dict) or isinstance(resolution.get("social"), dict):
        return
    md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    obligation = md.get("interaction_obligation") if isinstance(md.get("interaction_obligation"), dict) else {}
    if str(obligation.get("kind") or "").strip().lower() != "action_request":
        return
    before = str(before_text or "").strip()
    after = str(after_text or "").strip()
    if not before or resolution.get("success") is False:
        return
    target_terms = {
        token
        for token in re.findall(r"[a-z0-9']+", str(obligation.get("target") or "").lower())
        if len(token) >= 3
    }
    before_terms = set(re.findall(r"[a-z0-9']+", before.lower()))
    after_terms = set(re.findall(r"[a-z0-9']+", after.lower()))
    action_progress = bool(
        re.search(
            r"\b(?:open(?:s|ed)?|close(?:s|d)?|pull(?:s|ed)?|push(?:es|ed)?|knock(?:s|ed)?|"
            r"yield(?:s|ed)?|catch(?:es)?|move(?:s|d)?|hold(?:s)?|block(?:s|ed)?|fail(?:s|ed)?)\b",
            before,
            re.IGNORECASE,
        )
    )
    if not action_progress or not (target_terms & before_terms):
        return
    if target_terms & after_terms and not _looks_like_generic_resolution_fallback(after):
        return
    gm["player_facing_text"] = before
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    gm["tags"] = [str(t) for t in tags if isinstance(t, str)] + ["physical_action_obligation_preserved"]
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["physical_action_obligation_delivery"] = {
                "applied": True,
                "target": obligation.get("target"),
                "post_gate_preview": after[:180],
            }


def preserve_interaction_obligation_after_gate(
    gm: dict | None,
    *,
    resolution: dict | None,
    before_text: str = "",
) -> None:
    """Replace terminal dead air with the safest response that still resolves the turn."""
    from game.immutable_valid_response import leave_text_unchanged

    if leave_text_unchanged(gm, "preserve_interaction_obligation_after_gate"):
        return
    if not isinstance(gm, dict) or not isinstance(resolution, dict):
        return
    obligation = interaction_obligation_from_resolution(resolution)
    if not obligation:
        return
    from game.social_exchange_projection import interruption_cue_present_in_text

    if interruption_cue_present_in_text(before_text):
        return
    text = str(gm.get("player_facing_text") or "").strip()
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    terse_social_beat = bool(
        social.get("npc_reply_expected")
        and len(text.split()) <= 8
        and '"' not in text
        and not re.search(r"\b(?:yes|no|cannot|can't|won't|will not|because|if|unless)\b", text, re.IGNORECASE)
    )
    if not (_looks_like_generic_resolution_fallback(text) or terse_social_beat):
        return
    replacement = obligation_preserving_fallback_line(resolution).strip()
    if not replacement:
        return
    gm["player_facing_text"] = replacement
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    if "interaction_obligation_terminal_preserved" not in tags:
        tags.append("interaction_obligation_terminal_preserved")
    gm["tags"] = tags
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["interaction_obligation_terminal_preservation"] = {
                "applied": True,
                "kind": obligation.get("kind"),
                "replaced_preview": text[:180],
            }


def _preserve_resolution_contract_after_gate(
    gm: dict | None,
    *,
    resolution: dict | None,
) -> None:
    """Reject an emitted candidate that misses the shared resolution contract.

    This check does not invent a better answer. It only replaces an obvious
    semantic miss with the existing non-inventive obligation fallback.
    """
    from game.immutable_valid_response import leave_text_unchanged

    if leave_text_unchanged(gm, "_preserve_resolution_contract_after_gate"):
        return
    if not isinstance(gm, dict) or not isinstance(resolution, dict):
        return
    from game.resolution_contract import assess_contract_satisfaction, contract_mapping_from_resolution

    contract = contract_mapping_from_resolution(resolution)
    if not contract:
        return
    tags = {str(item) for item in (gm.get("tags") or []) if str(item).strip()}
    if tags & {"referenced_surface_realization", "perception_non_invention", "destination_arrival_realization"}:
        return
    text = str(gm.get("player_facing_text") or "")
    assessment = assess_contract_satisfaction(text, contract)
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["resolution_contract"] = dict(contract)
            debug["resolution_contract_semantic"] = dict(assessment)
    if assessment.get("status") != "unsatisfied":
        return
    reasons = {str(item) for item in (assessment.get("reasons") or [])}
    dimensions = {str(item) for item in (contract.get("dimensions") or []) if str(item).strip()}
    if contract.get("dimension"):
        dimensions.add(str(contract.get("dimension")))
    strict_dimension_miss = bool(
        dimensions & {"sound", "smell", "wear", "use", "change", "source", "confidence"}
        and "dimension_not_addressed" in reasons
    )
    obvious = reasons & {
        "generic_scene_replaced_dimension",
        "generic_scene_replaced_action",
        "clarification_missing",
        "consequential_not_refused",
        "echo_not_answer",
        "action_outcome_missing",
        "perception_routed_to_social_fallback",
        "target_incompatible",
        "topic_acknowledgement",
        "inspection_not_resolved",
        "repeat_not_restated",
        "repeat_new_content",
        "generic_action_refusal",
        "unrelated_fact",
        "operation_not_addressed",
        "literal_referent_reinterpretation",
        "canonical_premise_contradicted",
        "generic_use_nonanswer",
        "atmospheric_avoidance",
        "social_not_resolved",
        "dimension_substituted",
    }
    if not obvious and not strict_dimension_miss:
        return
    replacement = obligation_preserving_fallback_line(resolution).strip()
    operation = str(contract.get("operation") or "")
    if operation in {"act", "follow", "confirm"}:
        action_line = "The requested action cannot be completed here; another route is needed."
        if assess_contract_satisfaction(replacement, contract).get("status") == "unsatisfied":
            replacement = action_line
    if not replacement:
        return
    replacement_assessment = assess_contract_satisfaction(replacement, contract)
    if replacement_assessment.get("status") == "unsatisfied":
        return
    gm["player_facing_text"] = replacement
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    if "resolution_contract_semantic_preserved" not in tags:
        tags.append("resolution_contract_semantic_preserved")
    gm["tags"] = tags
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["resolution_contract_semantic"] = {
                **replacement_assessment,
                "replaced": True,
                "replaced_preview": text[:180],
            }


def _finalize_player_facing_for_turn(
    gm: dict | None,
    *,
    resolution: dict | None,
    session: dict,
    world: dict,
    scene: dict,
    include_resolution_in_sanitizer: bool = True,
    latency_sink: dict | None = None,
) -> tuple[dict | None, dict]:
    """Apply repeated-description guard and scene momentum, then sanitize, emission gate, and mismatch repair.

    Guard/momentum run here (before sanitization) so they match the pre-emission pipeline order; when
    ``_player_facing_emission_finalized`` is set, ``_apply_post_gm_updates`` skips repeating them.

    Must run before ``_apply_post_gm_updates`` so narration supplements use the same text the client receives.

    Returns:
        ``(gm_out, narration_consistency_meta)`` — meta is always a dict (possibly empty flags).
    """
    def _preview(value: object, *, limit: int = 180) -> str:
        text = str(value or "")
        return text[:limit] + ("..." if len(text) > limit else "")

    def _emission_debug(gm_obj: dict) -> dict:
        metadata = gm_obj.setdefault("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
            gm_obj["metadata"] = metadata
        debug = metadata.setdefault("emission_debug", {})
        if not isinstance(debug, dict):
            debug = {}
            metadata["emission_debug"] = debug
        return debug

    def _upstream_prepared_text_candidate(prepared: object) -> str:
        if isinstance(prepared, str):
            return prepared.strip()
        if not isinstance(prepared, dict):
            return ""
        for key in (
            "player_facing_text",
            "prepared_player_facing_text",
            "prepared_scene_opening_text",
            "scene_opening_text",
            "final_text",
            "text",
        ):
            value = prepared.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("gm_output", "emission", "candidate"):
            nested = prepared.get(key)
            if isinstance(nested, dict):
                value = nested.get("player_facing_text")
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return ""

    if not isinstance(gm, dict):
        return gm, {
            "narration_state_mismatch_detected": False,
            "mismatch_kind": "",
            "mismatch_repair_applied": "none",
            "mismatch_repairs_applied": [],
            "repaired_discovered_clue_texts": [],
        }
    from game.immutable_valid_response import accepted_record, restore_accepted_text, run_preserve_if_valid

    if (isinstance(resolution, dict) and isinstance(resolution.get("social"), dict)
            and accepted_record(gm) is None):
        # Legacy retry/fallback constructors can discard an earlier adoption.
        # They must re-enter the same complete decision path before delivery.
        contract = (resolution.get("metadata") or {}).get("resolution_contract") or {}
        gm = run_preserve_if_valid(gm, regenerate=None, resolution=resolution,
            player_text=str(contract.get("raw_input") or resolution.get("prompt") or ""),
            session=session, scene=scene, world=world)
    restore_accepted_text(gm)
    gm_out = dict(gm)
    gm_out = attach_bounded_improvisation_evaluation(
        gm_out,
        session=session,
        scene=scene,
        world=world,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    scene_id = str((scene.get("scene") or {}).get("id") or "").strip()
    tag_list = gm_out.get("tags") if isinstance(gm_out.get("tags"), list) else []
    tag_list = [str(t) for t in tag_list if isinstance(t, str)]
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session,
        world,
        scene_id,
    )
    if scene_id:
        # Repeated-description replacement is exploration-oriented. For strict-social turns
        # under a locked interlocutor, swapping duplicate model output for a generic summary
        # strips interruption cues before build_final / repeat tracking (stall + tracker loss).
        # Non-strict social still runs the guard so repeated stale blobs can converge cleanly.
        is_scene_opening = (
            isinstance(resolution, dict)
            and str(resolution.get("kind") or "").strip().lower() == "scene_opening"
        )
        if not is_scene_opening and not (_session_ongoing_social_exchange(session) and strict_social_turn):
            apply_repeated_description_guard(gm_out, session, scene_id)
        if not _session_ongoing_social_exchange(session):
            update_scene_momentum_runtime(session, scene_id, gm_out)
    raw_text = gm_out.get("player_facing_text") if isinstance(gm_out.get("player_facing_text"), str) else ""
    satisfying_candidate = raw_text
    if resembles_serialized_response_payload(raw_text):
        extracted = extract_player_text_from_serialized_payload(raw_text)
        raw_text = (
            extracted
            if isinstance(extracted, str) and extracted.strip()
            else strip_serialized_payload_fragments(raw_text)
        )
    pre_gate_text = str(raw_text or "")
    merge_upstream_prepared_emission_into_gm_output(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session,
        world=world,
        scene_id=scene_id,
    )
    raw_text_source = "gm_player_facing_text"
    is_scene_opening = (
        isinstance(resolution, dict)
        and str(resolution.get("kind") or "").strip().lower() == "scene_opening"
    )
    upstream_prepared = gm_out.get("upstream_prepared_emission")
    upstream_candidate = _upstream_prepared_text_candidate(upstream_prepared)
    upstream_candidate_ok = False
    if is_scene_opening and upstream_candidate:
        upstream_candidate_ok, _upstream_candidate_reasons = candidate_satisfies_scene_opening_contract(
            upstream_candidate
        )
        if upstream_candidate_ok:
            raw_text = upstream_candidate
            raw_text_source = "upstream_prepared_emission"
    debug = _emission_debug(gm_out)
    debug["opening_upstream_prepared_present"] = bool(upstream_candidate)
    debug["opening_upstream_prepared_len"] = len(upstream_candidate)
    debug["opening_upstream_prepared_promoted"] = bool(
        is_scene_opening and upstream_candidate and upstream_candidate_ok
    )
    debug["opening_raw_text_source"] = raw_text_source
    san_ctx_base = {
        "resolution": resolution if isinstance(resolution, dict) else None,
        "include_resolution": bool(include_resolution_in_sanitizer),
        "session": session,
        "scene_id": scene_id,
        "world": world,
        "tags": tag_list,
        "sanitizer_boundary_mode": SANITIZER_BOUNDARY_STRIP_ONLY,
        "upstream_prepared_emission": gm_out.get("upstream_prepared_emission"),
    }
    gate_scene = _scene_for_final_emission_input(
        scene,
        resolution if isinstance(resolution, dict) else None,
    )
    if strict_social_turn:
        gm_out["player_facing_text"] = raw_text
        pre_gate_text = str(gm_out.get("player_facing_text") or "")
        gate_started = _now_perf()
        gm_out = apply_final_emission_gate(
            gm_out,
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session,
            scene_id=scene_id,
            scene=gate_scene,
            world=world,
        )
        _accumulate_latency(latency_sink, "final_emission_gate", _elapsed_ms(gate_started))
    else:
        gm_out["player_facing_text"] = sanitize_player_facing_output(raw_text, san_ctx_base)
        pre_gate_text = str(gm_out.get("player_facing_text") or "")
        gate_started = _now_perf()
        gm_out = apply_final_emission_gate(
            gm_out,
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session,
            scene_id=scene_id,
            scene=gate_scene,
            world=world,
        )
        _accumulate_latency(latency_sink, "final_emission_gate", _elapsed_ms(gate_started))

    post_gate_text = str(gm_out.get("player_facing_text") or "")
    debug = _emission_debug(gm_out)
    debug["pre_gate_text_len"] = len(pre_gate_text)
    debug["post_final_emission_gate_text_len"] = len(post_gate_text)
    debug["narration_state_consistency_before_preview"] = _preview(post_gate_text)

    narr_meta = reconcile_final_text_with_structured_state(
        session=session,
        scene=scene,
        world=world,
        resolution=resolution if isinstance(resolution, dict) else None,
        gm_output=gm_out,
    )
    post_reconcile_text = str(gm_out.get("player_facing_text") or "")
    is_scene_opening = (
        isinstance(resolution, dict)
        and str(resolution.get("kind") or "").strip().lower() == "scene_opening"
    )
    if is_scene_opening and post_reconcile_text != post_gate_text:
        gate_ok, _gate_reasons = candidate_satisfies_scene_opening_contract(post_gate_text)
        if post_gate_text.strip() and gate_ok:
            gm_out["player_facing_text"] = post_gate_text
            post_reconcile_text = post_gate_text
            narr_meta["scene_opening_reconcile_text_restore_applied"] = True
            narr_meta["scene_opening_reconcile_text_restore_reason"] = (
                "valid_scene_opening_reconciliation_is_telemetry_only"
            )
        else:
            narr_meta["scene_opening_reconcile_text_restore_applied"] = False
            narr_meta["scene_opening_reconcile_text_restore_reason"] = (
                "post_gate_text_empty_or_invalid"
            )
    _preserve_accepted_bounded_resolution_after_gate(
        gm_out,
        before_text=pre_gate_text,
        after_text=post_reconcile_text,
    )
    _preserve_physical_action_resolution_after_gate(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
        before_text=pre_gate_text,
        after_text=str(gm_out.get("player_facing_text") or ""),
    )
    preserve_interaction_obligation_after_gate(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
        before_text=pre_gate_text,
    )
    _preserve_resolution_contract_after_gate(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    _preserve_authoritative_resolution_facts_after_gate(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
        scene=scene,
        world=world,
    )
    if isinstance(resolution, dict):
        from game.resolution_contract import remember_satisfied_candidate, select_preserved_answer

        remember_satisfied_candidate(gm_out, satisfying_candidate, resolution)
        debug_restore = _emission_debug(gm_out)
        stashed = str(debug_restore.get("satisfied_candidate") or "")
        preserved, precedence = select_preserved_answer(
            satisfying_candidate,
            str(gm_out.get("player_facing_text") or ""),
            resolution,
            stashed=stashed,
        )
        from game.immutable_valid_response import response_is_immutable

        if precedence.get("recovery_used") and not response_is_immutable(gm_out):
            gm_out["player_facing_text"] = preserved
            debug_restore = _emission_debug(gm_out)
        debug_restore["outcome_precedence"] = {
            **(debug_restore.get("outcome_precedence") if isinstance(debug_restore.get("outcome_precedence"), dict) else {}),
            **precedence,
        }
        if precedence.get("recovery_used"):
            from game.resolution_contract import semantic_line_view

            semantic_now = debug_restore.get("resolution_contract_semantic")
            if isinstance(semantic_now, dict):
                semantic_now = dict(semantic_now)
            else:
                semantic_now = {}
            semantic_now.update(semantic_line_view(preserved, resolution))
            semantic_now["restored_satisfying_candidate"] = True
            debug_restore["resolution_contract_semantic"] = semantic_now
    post_reconcile_text = str(gm_out.get("player_facing_text") or "")
    debug = _emission_debug(gm_out)
    debug["post_narration_state_consistency_text_len"] = len(post_reconcile_text)
    debug["narration_state_consistency_changed_text"] = post_reconcile_text != post_gate_text
    debug["narration_state_consistency_before_preview"] = _preview(post_gate_text)
    debug["narration_state_consistency_after_preview"] = _preview(post_reconcile_text)
    gm_out["_player_facing_emission_finalized"] = True
    from game.immutable_valid_response import commit_text, restore_accepted_text

    if accepted_record(gm_out) is None:
        contract = (resolution.get("metadata") or {}).get("resolution_contract") or {} if isinstance(resolution, dict) else {}
        gm_out = run_preserve_if_valid(gm_out, regenerate=None, resolution=resolution,
            player_text=str(contract.get("raw_input") or (resolution or {}).get("prompt") or ""),
            session=session, scene=scene, world=world)
    equality = restore_accepted_text(gm_out)
    _emission_debug(gm_out)["accepted_emitted_report"] = equality
    _preserve_authoritative_resolution_facts_after_gate(
        gm_out,
        resolution=resolution if isinstance(resolution, dict) else None,
        scene=scene,
        world=world,
    )
    if isinstance(session, dict) and isinstance(resolution, dict):
        from game.discourse_state import commit_discourse_focus, note_emitted_npc_claim, read_discourse_focus
        from game.resolution_contract import contract_mapping_from_resolution, contract_trace

        emitted_for_commit = commit_text(gm_out)
        if emitted_for_commit:
            note_emitted_npc_claim(
                session,
                emitted_text=emitted_for_commit,
                scene_id=scene_id,
            )
        contract = contract_mapping_from_resolution(resolution)
        if contract:
            catalog = None
            if scene is not None or world is not None:
                from game.scene_referent_catalog import build_canonical_referent_catalog

                catalog = build_canonical_referent_catalog(
                    scene=scene,
                    world=world,
                    session=session,
                    scene_id=scene_id,
                )
            focus = commit_discourse_focus(
                session,
                contract=contract,
                resolution=resolution,
                scene_id=scene_id,
                emitted_text=commit_text(gm_out) or str(gm_out.get("player_facing_text") or ""),
                canonical_referents=catalog,
            )
            from game.discourse_state import commit_active_epistemic_claim
            from game.gm_resolution_decision import (
                remember_temporal_claims,
                sealed_temporal_claims,
            )

            accepted_claims, rejected_claims = sealed_temporal_claims(
                gm_out,
                player_text=str(contract.get("raw_input") or ""),
            )
            temporal = remember_temporal_claims(
                session,
                claims=[*accepted_claims, *rejected_claims],
                scene_id=scene_id,
                source_turn=contract.get("turn_index") if isinstance(contract.get("turn_index"), int) else None,
            )
            commit_active_epistemic_claim(
                session,
                claims=accepted_claims,
                scene_id=scene_id,
                turn_index=contract.get("turn_index") if isinstance(contract.get("turn_index"), int) else None,
            )
            focus = read_discourse_focus(session)
            semantic = {}
            metadata = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
            debug_now = metadata.get("emission_debug") if isinstance(metadata, dict) else {}
            if isinstance(debug_now, dict):
                debug_now["temporal_provenance_commit"] = {
                    "sealed_text": emitted_for_commit,
                    "accepted_claim_count": len(accepted_claims),
                    "rejected_discarded_claim_count": len(rejected_claims),
                    "bucket_counts": {
                        key: len(temporal.get(key) or [])
                        for key in (
                            "gm_inferences",
                            "player_hypotheses",
                            "accepted_incidentals",
                            "rejected_consequential",
                        )
                    },
                }
            if isinstance(debug_now, dict) and isinstance(debug_now.get("resolution_contract_semantic"), dict):
                semantic = debug_now["resolution_contract_semantic"]
            append_debug_trace(
                session,
                contract_trace(
                    contract,
                    focus=focus,
                    obligation_kind=str((interaction_obligation_from_resolution(resolution) or {}).get("kind") or ""),
                    authority_route=str(contract.get("epistemic_mode") or ""),
                    semantic=semantic,
                    retry_preserved=bool(contract.get("retry_preserved")),
                ),
            )
    return gm_out, narr_meta


def _trace_world_updates(updates: dict | None, clocks_changed: dict | None = None) -> list:
    """Summarize world/clock changes for debug trace."""
    out: list = []
    if clocks_changed and isinstance(clocks_changed, dict):
        for k, v in clocks_changed.items():
            out.append(f'clock:{k}={v}')
    if updates and isinstance(updates, dict):
        if updates.get('append_events'):
            out.append(f'append_events:{len(updates["append_events"])}')
        ws = updates.get('world_state') or {}
        for key in ('flags', 'counters', 'clocks'):
            if isinstance(ws.get(key), dict) and ws[key]:
                out.append(f'world_state.{key}:{",".join(str(x) for x in ws[key].keys())}')
        if updates.get('projects'):
            out.append(f'projects:{len(updates["projects"])}')
    return out


def _trace_resolution_path(
    action_type: str,
    resolution: dict | None,
) -> str:
    """Classify which deterministic resolver path produced this turn outcome."""
    if not isinstance(resolution, dict):
        return "none"
    if isinstance(resolution.get("social"), dict):
        return "social_engine"
    if isinstance(resolution.get("combat"), dict):
        return "combat_engine"
    if isinstance(resolution.get("adjudication"), dict):
        return "adjudication_engine"
    if resolution.get("requires_check"):
        return "check_prompt_engine"
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind in {"initiative", "attack", "spell", "skill_check", "enemy_attack", "enemy_turn_skipped", "end_turn"}:
        return "combat_engine"
    if kind:
        return "exploration_engine"
    return f"{action_type}_engine"


def _snapshot_known_clue_presentations(session: dict) -> dict[str, str]:
    """Capture clue presentation by id for before/after visibility comparisons."""
    snapshot: dict[str, str] = {}
    for clue in get_known_clues_with_presentation(session):
        if not isinstance(clue, dict):
            continue
        clue_id = str(clue.get("id") or "").strip()
        presentation = str(clue.get("presentation") or "").strip()
        if clue_id and presentation:
            snapshot[clue_id] = presentation
    return snapshot


def _diff_clue_presentation(
    before: dict[str, str] | None,
    after: dict[str, str] | None,
) -> list[dict]:
    """Return compact clue visibility/presentation changes."""
    before = before or {}
    after = after or {}
    changes: list[dict] = []
    for clue_id in sorted(set(before.keys()) | set(after.keys())):
        prev = before.get(clue_id)
        curr = after.get(clue_id)
        if prev == curr:
            continue
        changes.append({"id": clue_id, "from": prev, "to": curr})
    return changes


def _compact_affordances_for_trace(affordances: list | None) -> list[dict]:
    """Keep affordances trace developer-facing and compact."""
    out: list[dict] = []
    if not isinstance(affordances, list):
        return out
    for a in affordances:
        if not isinstance(a, dict):
            continue
        compact = {
            "id": a.get("id"),
            "type": a.get("type"),
            "label": a.get("label"),
            "targetSceneId": a.get("targetSceneId"),
            "targetEntityId": a.get("targetEntityId") or a.get("target_id"),
        }
        out.append({k: v for k, v in compact.items() if v is not None})
    return out


def _derive_affordances_from_authoritative_state(scene: dict, session: dict, world: dict) -> list[dict]:
    """Derive affordances from current authoritative state (no narration dependency)."""
    affordances = get_available_affordances(
        scene,
        session,
        world,
        mode=scene["scene"].get("mode", "exploration"),
        list_scene_ids_fn=list_scene_ids,
        scene_graph=build_scene_graph(list_scene_ids, load_scene),
    )
    return _compact_affordances_for_trace(affordances)


def _coalesce_social_turn_contract(
    resolution: dict | None,
    normalized_action: dict | None,
    directed_social_entry: dict | None,
) -> dict | None:
    """Prefer ``resolution.metadata``, then normalized action metadata, then directed social entry."""
    if isinstance(resolution, dict):
        md = resolution.get("metadata")
        if isinstance(md, dict):
            stc = md.get("social_turn_contract")
            if isinstance(stc, dict) and stc:
                return dict(stc)
    if isinstance(normalized_action, dict):
        md = normalized_action.get("metadata")
        if isinstance(md, dict):
            stc = md.get("social_turn_contract")
            if isinstance(stc, dict) and stc:
                return dict(stc)
    if isinstance(directed_social_entry, dict):
        stc = directed_social_entry.get("social_turn_contract")
        if isinstance(stc, dict) and stc:
            return dict(stc)
    return None


def _visible_grounded_speaker_id(
    adoption_debug: dict | None,
    stale_invalidation_debug: dict | None,
) -> str | None:
    """Reuse post-emission debug ids only (no text parsing)."""
    if isinstance(stale_invalidation_debug, dict):
        v = stale_invalidation_debug.get("visible_grounded_speaker_id")
        if isinstance(v, str) and v.strip():
            return v.strip()
    if isinstance(adoption_debug, dict) and adoption_debug.get("adopted") is True:
        v = adoption_debug.get("npc_id")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _apply_post_emission_contract_overlays(
    out: dict[str, str | None],
    adoption_debug: dict | None,
    stale_invalidation_debug: dict | None,
) -> None:
    """Overlay ``interlocutor_status`` / ``fallback_anchor_source`` from adoption/stale debug dicts.

    Stale invalidation runs after adoption; its fields win when it clears or contradicts storage.
    Does not re-derive routing; copies canonical debug fields only.
    """
    if isinstance(adoption_debug, dict):
        ar = str(adoption_debug.get("reason") or "")
        adoption_authoritative = bool(adoption_debug.get("adopted") is True) or ar == "already_current_interlocutor"
        if adoption_authoritative and ar not in ("skipped", "scene_changed_or_bad_inputs", "no_scene"):
            ils = adoption_debug.get("interlocutor_status")
            if isinstance(ils, str) and ils.strip():
                out["interlocutor_status"] = ils.strip()
            fas = adoption_debug.get("fallback_anchor_source")
            if isinstance(fas, str) and fas.strip():
                out["fallback_anchor_source"] = fas.strip()
    if isinstance(stale_invalidation_debug, dict):
        if stale_invalidation_debug.get("cleared") or str(
            stale_invalidation_debug.get("reason") or ""
        ).strip() in (
            "visible_speaker_contradicts_stored_interlocutor",
        ):
            ils = stale_invalidation_debug.get("interlocutor_status")
            if isinstance(ils, str) and ils.strip():
                out["interlocutor_status"] = ils.strip()
            fas = stale_invalidation_debug.get("fallback_anchor_source")
            if isinstance(fas, str) and fas.strip():
                out["fallback_anchor_source"] = fas.strip()


def _trace_str(v: object | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def build_social_contract_turn_trace(
    *,
    resolution: dict | None,
    normalized_action: dict | None,
    directed_social_entry: dict | None,
    route_selected: str | None,
    session: dict | None,
    adoption_debug: dict | None = None,
    stale_invalidation_debug: dict | None = None,
) -> dict[str, str | None]:
    """Compact developer trace: canonical ``social_turn_contract`` + post-emission debug + final owner.

    ``final_reply_owner`` is the persisted ``active_interaction_target_id`` after routing and
    post-emission adoption/invalidation (same source manual testers inspect in session).
    """
    stc = _coalesce_social_turn_contract(resolution, normalized_action, directed_social_entry)
    rs = _trace_str(route_selected)

    out: dict[str, str | None] = {
        "route_selected": rs,
        "routing_reason_code": _trace_str(stc.get("routing_reason_code")) if isinstance(stc, dict) else None,
        "social_followup_recovery": _trace_str(stc.get("social_followup_recovery")) if isinstance(stc, dict) else None,
        "reply_owner_actor_id": _trace_str(stc.get("reply_owner_actor_id")) if isinstance(stc, dict) else None,
        "interlocutor_status": _trace_str(stc.get("interlocutor_status")) if isinstance(stc, dict) else None,
        "continuity_status": _trace_str(stc.get("continuity_status")) if isinstance(stc, dict) else None,
        "fallback_anchor_source": _trace_str(stc.get("fallback_anchor_source")) if isinstance(stc, dict) else None,
        "visible_grounded_speaker": _visible_grounded_speaker_id(adoption_debug, stale_invalidation_debug),
        "final_reply_owner": None,
    }
    _apply_post_emission_contract_overlays(out, adoption_debug, stale_invalidation_debug)

    if isinstance(session, dict):
        ic = inspect_interaction_context(session)
        if isinstance(ic, dict):
            aid = str(ic.get("active_interaction_target_id") or "").strip()
            out["final_reply_owner"] = aid or None

    return out


def _build_compact_turn_trace(
    *,
    source: str,
    action_type: str,
    raw_input: str,
    parsed_intent: dict | None,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    implied_context: dict | None,
    resolution: dict | None,
    scene_before: str,
    scene_after: str,
    authoritative_clue_updates: list[str],
    clue_presentation_before: dict[str, str],
    session: dict,
    world: dict,
    scene: dict,
    leads_inspection: dict | None = None,
    response_type_contract: dict | None = None,
    route_selected: str | None = None,
    directed_social_entry: dict | None = None,
    adoption_debug: dict | None = None,
    stale_invalidation_debug: dict | None = None,
    latency_ms: dict | None = None,
) -> dict:
    """Build compact resolved-turn trace grounded in post-resolution authoritative state."""
    social_contract_trace = build_social_contract_turn_trace(
        resolution=resolution if isinstance(resolution, dict) else None,
        normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
        directed_social_entry=directed_social_entry if isinstance(directed_social_entry, dict) else None,
        route_selected=route_selected,
        session=session if isinstance(session, dict) else None,
        adoption_debug=adoption_debug if isinstance(adoption_debug, dict) else None,
        stale_invalidation_debug=stale_invalidation_debug if isinstance(stale_invalidation_debug, dict) else None,
    )
    interaction_after = inspect_interaction_context(session).copy()
    visited = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    trace_session_view = {
        "turn_counter": int(session.get("turn_counter", 0) or 0),
        "visited_scene_count": len(visited),
        "active_interaction_target_id": interaction_after.get("active_interaction_target_id"),
        "active_interaction_kind": interaction_after.get("active_interaction_kind"),
        "interaction_mode": interaction_after.get("interaction_mode"),
    }
    trace_intent_labels: list[str] = []
    if isinstance(parsed_intent, dict):
        parsed_type = str(parsed_intent.get("type") or "").strip().lower()
        if parsed_type in SOCIAL_KINDS:
            trace_intent_labels.append("social_probe")
    narration_obligations = derive_narration_obligations(
        session_view=trace_session_view,
        resolution=resolution if isinstance(resolution, dict) else None,
        intent={"labels": trace_intent_labels} if trace_intent_labels else None,
        recent_log_for_prompt=[],
    )
    clue_presentation_after = _snapshot_known_clue_presentations(session)
    clue_changes = _diff_clue_presentation(clue_presentation_before, clue_presentation_after)
    known_clues = get_known_clues_with_presentation(session)
    clue_counts = {
        "implicit": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "implicit"),
        "explicit": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "explicit"),
        "actionable": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "actionable"),
    }
    deduped_clues: list[str] = []
    for txt in authoritative_clue_updates:
        if isinstance(txt, str):
            clean = txt.strip()
            if clean and clean not in deduped_clues:
                deduped_clues.append(clean)

    return {
        "source": source,
        "player_input": raw_input,
        "intent": {
            "parsed": parsed_intent if isinstance(parsed_intent, dict) else None,
            "segmented_turn": segmented_turn if isinstance(segmented_turn, dict) else None,
            "normalized": (
                {k: normalized_action.get(k) for k in ("id", "label", "type", "prompt", "targetSceneId", "target_scene_id", "targetEntityId", "target_id")}
                if isinstance(normalized_action, dict)
                else None
            ),
            "implied_context": {
                "applied": bool((implied_context or {}).get("applied")),
                "cases": list((implied_context or {}).get("cases") or []),
                "target_id": (implied_context or {}).get("target_id"),
                "commitment_broken": bool((implied_context or {}).get("commitment_broken")),
                "break_reason": (implied_context or {}).get("break_reason"),
            },
        },
        "classification": {
            "action_type": action_type,
            "resolved_kind": (resolution or {}).get("kind") if isinstance(resolution, dict) else None,
            "requires_check": bool((resolution or {}).get("requires_check")) if isinstance(resolution, dict) else False,
        },
        "response_type_contract": compact_response_type_contract(response_type_contract),
        "social_contract_trace": social_contract_trace,
        "resolution_path": _trace_resolution_path(action_type, resolution),
        "authoritative_state_changes": {
            "scene_transition": {"from": scene_before, "to": scene_after} if scene_before != scene_after else None,
            "resolution_state_changes": (resolution or {}).get("state_changes") if isinstance((resolution or {}).get("state_changes"), dict) else {},
            "resolution_world_updates": _trace_world_updates((resolution or {}).get("world_updates")) if isinstance(resolution, dict) else [],
            "check_request": (resolution or {}).get("check_request") if isinstance((resolution or {}).get("check_request"), dict) else None,
        },
        "interaction_after": {
            "active_interaction_target_id": interaction_after.get("active_interaction_target_id"),
            "active_interaction_kind": interaction_after.get("active_interaction_kind"),
            "interaction_mode": interaction_after.get("interaction_mode"),
            "engagement_level": interaction_after.get("engagement_level"),
            "conversation_privacy": interaction_after.get("conversation_privacy"),
            "player_position_context": interaction_after.get("player_position_context"),
        },
        "narration_obligations": narration_obligations,
        "clues": {
            "discovered_texts": deduped_clues,
            "presentation_changes": clue_changes,
            "known_counts": clue_counts,
        },
        "affordances_after": _derive_affordances_from_authoritative_state(scene, session, world),
        "emergent_actor": (
            dict(session.get("emergent_actor_debug"))
            if isinstance(session, dict) and isinstance(session.get("emergent_actor_debug"), dict)
            else None
        ),
        "leads": (
            leads_inspection
            if isinstance(leads_inspection, dict)
            and isinstance(leads_inspection.get("registry_debug"), list)
            and isinstance(leads_inspection.get("delta_after_reconcile"), list)
            and isinstance(leads_inspection.get("changed_count"), int)
            else {
                "registry_debug": [],
                "delta_after_reconcile": [],
                "changed_count": 0,
            }
        ),
        "latency_ms": dict(latency_ms) if isinstance(latency_ms, dict) else {},
    }


def _reconcile_session_lead_progression_after_authoritative_mutation(session: dict) -> None:
    """Apply deterministic lead lifecycle progression for the current session turn.

    Call only after authoritative mutations for the request are complete (including post-narration
    session patches) and before compact turn-trace construction so traces match persisted state.
    """
    leads_module.reconcile_session_lead_progression(session)


def _lead_debug_trace_around_authoritative_reconcile(session: dict) -> dict:
    """Capture compact lead rows before/after the single authoritative reconcile pass."""
    before = leads_module.build_lead_debug_snapshot(session)
    _reconcile_session_lead_progression_after_authoritative_mutation(session)
    after = leads_module.build_lead_debug_snapshot(session)
    delta = leads_module.diff_lead_debug_snapshots(before, after)
    return {
        "registry_debug": leads_module.debug_dump_leads(session),
        "delta_after_reconcile": delta,
        "changed_count": len(delta),
    }


def _finalize_and_append_trace(session: dict, trace: dict, response_ok: bool, error: str | None = None) -> None:
    trace['response_ok'] = response_ok
    trace['error'] = error
    append_debug_trace(session, trace)
    save_session(session)


def _build_turn_response_payload(
    *,
    gm: dict,
    resolution: dict | None,
    include_resolution: bool,
) -> dict:
    """Stages 8-9: derive affordances from authoritative state and package API response."""
    import game.api as _api

    state = _api.compose_state()  # Includes affordances derived from saved authoritative scene/session/world.
    state_session = state.get("session") if isinstance(state.get("session"), dict) else {}
    state_world = state.get("world") if isinstance(state.get("world"), dict) else {}
    state_scene = state.get("scene") if isinstance(state.get("scene"), dict) else {}
    scene_obj = state_scene.get("scene") if isinstance(state_scene.get("scene"), dict) else {}
    scene_id = str(scene_obj.get("id") or "").strip()

    gm_output_debug: dict | None = None
    if isinstance(gm, dict):
        gm = dict(gm)
        from game.immutable_valid_response import response_is_immutable, restore_accepted_text

        restore_accepted_text(gm)
        if response_is_immutable(gm):
            gm["_player_facing_emission_finalized"] = True
        if gm.get("_player_facing_emission_finalized"):
            ist = gm.get("internal_state")
            if isinstance(ist, dict) and isinstance(ist.get("emission_debug_lane"), dict):
                gm_output_debug = {"emission_debug_lane": dict(ist["emission_debug_lane"])}
            gm = _strip_internal_gm_keys(gm)
        else:
            raw_text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
            if resembles_serialized_response_payload(raw_text):
                extracted = extract_player_text_from_serialized_payload(raw_text)
                raw_text = (
                    extracted
                    if isinstance(extracted, str) and extracted.strip()
                    else strip_serialized_payload_fragments(raw_text)
                )
            tag_list = gm.get("tags") if isinstance(gm.get("tags"), list) else []
            tag_list = [str(t) for t in tag_list if isinstance(t, str)]
            strict_social_turn = strict_social_emission_will_apply(
                resolution if isinstance(resolution, dict) else None,
                state_session,
                state_world,
                scene_id,
            )

            merge_upstream_prepared_emission_into_gm_output(
                gm,
                resolution=resolution if isinstance(resolution, dict) else None,
                session=state_session,
                world=state_world,
                scene_id=scene_id,
            )
            san_ctx_base = {
                "resolution": resolution if isinstance(resolution, dict) else None,
                "include_resolution": bool(include_resolution),
                "session": state_session,
                "scene_id": scene_id,
                "world": state_world,
                "tags": tag_list,
                "sanitizer_boundary_mode": SANITIZER_BOUNDARY_STRIP_ONLY,
                "upstream_prepared_emission": gm.get("upstream_prepared_emission"),
            }

            if strict_social_turn:
                gm["player_facing_text"] = raw_text
                gate_scene = _scene_for_final_emission_input(
                    state_scene,
                    resolution if isinstance(resolution, dict) else None,
                )
                gm = apply_final_emission_gate(
                    gm,
                    resolution=resolution if isinstance(resolution, dict) else None,
                    session=state_session,
                    scene_id=scene_id,
                    scene=gate_scene,
                    world=state_world,
                )
                # build_final_strict_social_response (via the gate) is the sole writer; no post-gate sanitizer.
            else:
                gm["player_facing_text"] = sanitize_player_facing_output(raw_text, san_ctx_base)
                gate_scene = _scene_for_final_emission_input(
                    state_scene,
                    resolution if isinstance(resolution, dict) else None,
                )
                gm = apply_final_emission_gate(
                    gm,
                    resolution=resolution if isinstance(resolution, dict) else None,
                    session=state_session,
                    scene_id=scene_id,
                    scene=gate_scene,
                    world=state_world,
                )
            ist = gm.get("internal_state")
            if isinstance(ist, dict) and isinstance(ist.get("emission_debug_lane"), dict):
                gm_output_debug = {"emission_debug_lane": dict(ist["emission_debug_lane"])}
            gm = _strip_internal_gm_keys(gm)

    payload: dict = {'ok': True, 'gm_output': gm, **state}
    if gm_output_debug:
        payload["gm_output_debug"] = gm_output_debug
    if include_resolution:
        payload['resolution'] = resolution
    return payload


def _sanitize_resolution(res: dict | None) -> dict | None:
    """Safe resolution subset for trace. No hidden content."""
    if not res or not isinstance(res, dict):
        return None
    safe = {'kind', 'resolved_transition', 'target_scene_id', 'originating_scene_id',
            'same_scene_transition_suppressed', 'transition_applied',
            'action_id', 'label', 'prompt', 'hint', 'attack_id', 'skill_id', 'spell_id',
            'roll', 'damage', 'total', 'hit', 'round', 'active_actor_id', 'world_tick_events',
            'clue_id', 'clue_text', 'discovered_clues', 'state_changes', 'success', 'metadata',
            'combat', 'social', 'adjudication', 'requires_check', 'check_request',
            'noncombat_resolution'}
    return {k: v for k, v in res.items() if k in safe}


def _compact_segmented_turn(segmented_turn: dict | None) -> dict | None:
    """Keep segmentation payload compact for traces/metadata."""
    if not isinstance(segmented_turn, dict):
        return None
    compact = {
        "spoken_text": segmented_turn.get("spoken_text"),
        "declared_action_text": segmented_turn.get("declared_action_text"),
        "adjudication_question_text": segmented_turn.get("adjudication_question_text"),
        "observation_intent_text": segmented_turn.get("observation_intent_text"),
        "contingency_text": segmented_turn.get("contingency_text"),
    }
    compact = {k: v for k, v in compact.items() if isinstance(v, str) and v.strip()}
    return compact or None
