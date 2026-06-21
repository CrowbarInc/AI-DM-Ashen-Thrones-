#!/usr/bin/env python3
"""BV14A — extract social_exchange_emission domain modules (one-time refactor helper)."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "game" / "social_exchange_emission.py"
BACKUP = ROOT / "game" / "social_exchange_emission.py.bv14a_backup"

PROJECTION = {
    "stamp_strict_social_deterministic_fallback_family",
    "strict_social_deterministic_fallback_family_token",
    "project_strict_social_replace_realization_family",
    "log_final_emission_decision",
    "log_final_emission_trace",
    "emission_gate_uncertainty_source",
    "emission_gate_pressure_active",
    "emission_gate_interruption_active",
    "_extract_uncertainty_source_from_tags",
    "_is_pressure_active",
    "_UNCERTAINTY_TAG_PREFIX",
    "_MOMENTUM_TAG_PREFIX",
}

POLICY = {
    "effective_scene_npc_roster",
    "is_social_exchange_resolution",
    "is_scene_directed_watch_question",
    "merged_player_prompt_for_gate",
    "_merge_prompt_for_strict_gate",
    "_question_prompt_for_resolution_early",
    "_scene_runtime_player_hint",
    "_SCENE_DIRECTED_WATCH_QUESTION_RE",
    "_DIRECT_QUESTION_WORDS_FOR_EMIT",
    "resolve_strict_social_npc_target_id",
    "is_conversational_npc_dialogue_line",
    "looks_like_npc_directed_question",
    "player_line_triggers_strict_social_emission",
    "strict_social_emission_will_apply",
    "minimal_social_resolution_for_directed_question_guard",
    "should_apply_strict_social_exchange_emission",
    "synthetic_social_exchange_resolution_for_emission",
    "coerce_resolution_for_strict_social_emission",
    "reconcile_strict_social_resolution_speaker",
    "effective_strict_social_resolution_for_emission",
    "coerced_strict_social_allowed_by_merged_prompt",
    "strict_social_suppress_non_native_coercion_for_narration_beat",
    "_active_social_target_matches_npc",
    "_npc_display_name_for_emission",
    "_normalized_action_from_resolution",
    "_merged_prompt_opens_reflective_or_world_action_beat",
    "_session_turn_counter",
    "_auth_after_social_promotion_binding",
    "_scene_envelope_for_strict_social",
    "_legacy_strict_basis_from_authoritative",
    "_speaker_label",
    "_deterministic_index",
    "_question_prompt_for_resolution",
    "_speaker_label_for_emission_seed",
    "_REFLECTIVE_OR_MOVEMENT_NARRATION_OPEN_RE",
    "_IMPERATIVE_SOCIAL_CONTINUATION_RE",
}

FALLBACK = {
    "minimal_social_emergency_fallback_line",
    "lawful_strict_social_dialogue_emergency_fallback_line",
    "_text_is_strict_social_minimal_emergency_fallback",
    "strict_social_ownership_terminal_fallback",
    "strict_social_terminal_dialogue_fallback_valid",
    "_strict_social_emergency_fallback_npc_dialogue_substantive",
    "_active_interlocutor_matches_resolution_social_npc",
    "apply_strict_social_terminal_dialogue_fallback_if_needed",
    "repair_strict_social_terminal_dialogue_fallback_if_needed",
    "deterministic_social_fallback_line",
    "social_fallback_line_for_sanitizer",
    "select_strict_social_emergency_fallback_line",
    "StrictSocialEmergencyFallbackSurface",
    "build_open_social_solicitation_recovery",
    "apply_social_exchange_retry_fallback_gm",
    "_social_integrity_fallback_line_candidates",
    "_STALL_OPEN_SOCIAL_FRAGMENT_RE",
    "_STALL_OPEN_SOCIAL_ANYWHERE_RE",
    "_ensure_sentence_end",
    "_open_social_visible_leads_surface",
    "_open_social_anchor_phrase",
    "_open_social_responder_templates",
    "_open_social_lead_templates",
    "_open_social_recovery_passes_anti_stall",
    "_shorten_visible_fact_for_lead",
    "_open_social_fact_lead_line",
    "_speaker_contract_allows_candidate",
    "_merge_open_social_recovery_emission_debug",
    "_standard_mode_social_retry_payload_floor",
}

VALIDATION = {
    "is_route_illegal_global_or_sanitizer_fallback_text",
    "replacement_is_route_legal_social",
    "social_final_emission_malformed_player_echo",
    "_collapse_ws",
    "_split_sentences",
    "_normalize_gate_text",
    "_SENTENCE_TERMINATORS",
    "_CLOSING_PUNCT_OR_QUOTES",
    "_SCENE_CONTAMINATION_PATTERNS",
    "_INTERRUPTION_PATTERNS",
    "_EXPLICIT_INTERRUPTION_JOIN_PATTERNS",
    "_NPC_SETUP_HINTS",
    "_looks_like_interruption_breakoff_text",
    "_has_explicit_interruption_shape",
    "_interruption_sentence_index",
    "_sentence_is_scene_contaminated",
    "_sentence_is_npc_setup",
    "_sentence_has_speaker_speculation_frame",
    "_sentence_is_detached_omniscient_analysis",
    "_sentence_is_bounded_social_signal",
    "_sentence_is_clue_or_analytical_substitute",
    "_speaker_display_prefixes",
    "_sentence_opens_with_resolved_npc_beat",
    "_sentence_is_speaker_owned_social",
    "_echo_token_set",
    "_player_final_token_overlap_ratio",
    "_social_text_shows_refusal_realization",
    "_social_line_has_playable_npc_substance",
    "_social_text_shows_redirect_realization",
    "_social_text_shows_explanation_realization",
    "_npc_dialogue_has_player_request_framing",
    "_final_paragraph_ends_with_question",
    "_PLAYER_REQUEST_IN_DIALOGUE_RE",
    "_REDIRECT_REALIZATION_RE",
    "_EXPLANATION_REALIZATION_RE",
    "_DETACHED_OMNISCIENT_PATTERNS",
    "_CLUE_OR_ANALYTICAL_SUBSTITUTE_PATTERNS",
    "_REFUSAL_SIGNAL_PATTERNS",
    "_IGNORANCE_SIGNAL_PATTERNS",
}

EXTRACTED = PROJECTION | POLICY | FALLBACK | VALIDATION

MODULE_HEADERS = {
    "projection": '''\
"""Strict-social telemetry and FEM/realization projection (BV14A canonical owner)."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from game.realization_provenance import (
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    attach_realization_fallback_family,
    normalize_realization_fallback_family,
)

_log = logging.getLogger(__name__)

''',
    "policy": '''\
"""Strict-social eligibility and resolution policy (BV14A canonical owner)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from game.dialogue_targeting import line_opens_with_comma_vocative
from game.interaction_context import (
    assert_valid_speaker,
    effective_in_scene_npc_roster,
    inspect as inspect_interaction_context,
    resolve_authoritative_social_target,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.social import (
    apply_social_reply_speaker_grounding,
    finalize_social_target_with_promotion,
)
from game.storage import get_scene_runtime

effective_scene_npc_roster = effective_in_scene_npc_roster

''',
    "fallback_catalog": '''\
"""Strict-social fallback phrase catalog and selection (BV14A canonical owner)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Tuple

from game.interaction_context import inspect as inspect_interaction_context
from game.prompt_context import canonical_interaction_target_npc_id
from game.response_policy_contracts import response_type_contract_requires_dialogue
from game.social_exchange_policy import (
    _deterministic_index,
    _speaker_label,
    strict_social_emission_will_apply,
)
from game.social_exchange_projection import (
    _is_pressure_active,
    emission_gate_interruption_active,
    emission_gate_pressure_active,
    emission_gate_uncertainty_source,
)
from game.social_exchange_validation import (
    _collapse_ws,
    _looks_like_interruption_breakoff_text,
    _sentence_is_bounded_social_signal,
    _sentence_opens_with_resolved_npc_beat,
    _split_sentences,
    is_route_illegal_global_or_sanitizer_fallback_text,
)

''',
    "validation": '''\
"""Strict-social route legality and emission validation helpers (BV14A canonical owner)."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.social_exchange_policy import looks_like_npc_directed_question

''',
}


def _node_names(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Assign):
        out: set[str] = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                out.add(target.id)
        return out
    return set()


def _partition_source(source: str) -> tuple[dict[str, list[str]], list[str]]:
    tree = ast.parse(source)
    segments: dict[str, list[str]] = {
        "projection": [],
        "policy": [],
        "fallback_catalog": [],
        "validation": [],
        "composition": [],
    }
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        seg = ast.get_source_segment(source, node)
        if not seg:
            continue
        names = _node_names(node)
        if not names:
            continue
        if names <= PROJECTION:
            segments["projection"].append(seg)
        elif names <= POLICY:
            segments["policy"].append(seg)
        elif names <= FALLBACK:
            segments["fallback_catalog"].append(seg)
        elif names <= VALIDATION:
            segments["validation"].append(seg)
        elif names & EXTRACTED:
            # mixed node — keep in composition for safety
            segments["composition"].append(seg)
        else:
            segments["composition"].append(seg)
    return segments, [ast.get_source_segment(source, n) or "" for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]


def _patch_validation_replacement(source: str) -> str:
    old = '''def replacement_is_route_legal_social(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> bool:
    """True if text is acceptable final social_exchange output (or intentional interruption path)."""
    return not hard_reject_social_exchange_text(
        text,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )'''
    new = '''def replacement_is_route_legal_social(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> bool:
    """True if text is acceptable final social_exchange output (or intentional interruption path)."""
    from game.social_exchange_emission import hard_reject_social_exchange_text

    return not hard_reject_social_exchange_text(
        text,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )'''
    return source.replace(old, new)


def _write_domain(path: Path, kind: str, body_parts: list[str]) -> None:
    body = "\n\n".join(body_parts).strip() + "\n"
    if kind == "validation":
        body = _patch_validation_replacement(body)
    content = MODULE_HEADERS[kind] + body
    path.write_text(content, encoding="utf-8")


def _composition_header() -> str:
    return textwrap.dedent(
        '''\
        """Route-isolated downstream emission helpers for active social_exchange turns.

        Ensures player-facing text is speaker-owned, single-form, and never pulled from
        scene/ambient uncertainty pools except as an explicit interruption breakoff.

        BV14A: compatibility barrel for strict-social composition authority. Fallback, policy,
        validation, and projection symbols are re-exported from canonical domain modules.
        """
        from __future__ import annotations

        import json
        import logging
        import re
        from typing import Any, Dict, List, Literal, MutableMapping, Optional, Tuple

        from game.dialogue_targeting import (
            line_opens_with_comma_vocative,
            npc_id_from_vocative_line,
        )
        from game.exploration import EXPLORATION_KINDS
        from game.interaction_context import (
            assert_valid_speaker,
            canonical_scene_addressable_roster,
            clear_social_exchange_interruption_tracker,
            get_social_exchange_interruption_tracker,
            inspect as inspect_interaction_context,
            npc_id_from_explicit_generic_role_address,
            resolve_authoritative_social_target,
            scene_addressable_actor_ids,
            session_allows_implicit_social_reply_authority,
            set_social_exchange_interruption_tracker,
        )
        from game.response_policy_contracts import response_type_contract_requires_dialogue
        from game.social import (
            apply_social_reply_speaker_grounding,
            classify_social_question_dimension,
            format_structured_fact_social_line,
            neutral_reply_speaker_grounding_bridge_line,
            resolve_grounded_social_speaker,
            select_best_social_answer_candidate,
            topic_pressure_speaker_id_for_social_exchange,
        )
        from game.social import SOCIAL_KINDS
        from game.storage import get_scene_runtime
        from game.utils import slugify

        from game.social_exchange_fallback_catalog import (
            StrictSocialEmergencyFallbackSurface,
            _social_integrity_fallback_line_candidates,
            _text_is_strict_social_minimal_emergency_fallback,
            apply_social_exchange_retry_fallback_gm,
            apply_strict_social_terminal_dialogue_fallback_if_needed,
            build_open_social_solicitation_recovery,
            deterministic_social_fallback_line,
            lawful_strict_social_dialogue_emergency_fallback_line,
            minimal_social_emergency_fallback_line,
            repair_strict_social_terminal_dialogue_fallback_if_needed,
            select_strict_social_emergency_fallback_line,
            social_fallback_line_for_sanitizer,
            strict_social_ownership_terminal_fallback,
            strict_social_terminal_dialogue_fallback_valid,
        )
        from game.social_exchange_policy import (
            _auth_after_social_promotion_binding,
            _legacy_strict_basis_from_authoritative,
            _merged_prompt_opens_reflective_or_world_action_beat,
            _npc_display_name_for_emission,
            _normalized_action_from_resolution,
            _scene_envelope_for_strict_social,
            _session_turn_counter,
            _speaker_label,
            _speaker_label_for_emission_seed,
            coerce_resolution_for_strict_social_emission,
            coerced_strict_social_allowed_by_merged_prompt,
            effective_scene_npc_roster,
            effective_strict_social_resolution_for_emission,
            is_conversational_npc_dialogue_line,
            is_scene_directed_watch_question,
            is_social_exchange_resolution,
            looks_like_npc_directed_question,
            merged_player_prompt_for_gate,
            minimal_social_resolution_for_directed_question_guard,
            player_line_triggers_strict_social_emission,
            reconcile_strict_social_resolution_speaker,
            resolve_strict_social_npc_target_id,
            should_apply_strict_social_exchange_emission,
            strict_social_emission_will_apply,
            strict_social_suppress_non_native_coercion_for_narration_beat,
            synthetic_social_exchange_resolution_for_emission,
        )
        from game.social_exchange_projection import (
            emission_gate_interruption_active,
            emission_gate_pressure_active,
            emission_gate_uncertainty_source,
            log_final_emission_decision,
            log_final_emission_trace,
            project_strict_social_replace_realization_family,
            stamp_strict_social_deterministic_fallback_family,
            strict_social_deterministic_fallback_family_token,
        )
        from game.social_exchange_validation import (
            _collapse_ws,
            _final_paragraph_ends_with_question,
            _has_explicit_interruption_shape,
            _looks_like_interruption_breakoff_text,
            _normalize_gate_text,
            _sentence_is_bounded_social_signal,
            _sentence_is_clue_or_analytical_substitute,
            _sentence_is_detached_omniscient_analysis,
            _sentence_is_npc_setup,
            _sentence_is_scene_contaminated,
            _sentence_is_speaker_owned_social,
            _sentence_opens_with_resolved_npc_beat,
            _split_sentences,
            is_route_illegal_global_or_sanitizer_fallback_text,
            replacement_is_route_legal_social,
            social_final_emission_malformed_player_echo,
        )

        _log = logging.getLogger(__name__)

        _EXPLORATION_RESOLUTION_KINDS = frozenset(str(k).strip().lower() for k in EXPLORATION_KINDS)

        '''
    )


def _reexport_block() -> str:
    return textwrap.dedent(
        '''

        # --- BV14A compatibility re-exports (canonical implementations in domain modules) ---
        __all__ = [
            "StrictSocialEmergencyFallbackSurface",
            "apply_social_exchange_retry_fallback_gm",
            "apply_strict_social_ownership_enforcement",
            "apply_strict_social_sentence_ownership_filter",
            "apply_strict_social_terminal_dialogue_fallback_if_needed",
            "build_final_strict_social_response",
            "build_open_social_solicitation_recovery",
            "coerce_resolution_for_strict_social_emission",
            "coerced_strict_social_allowed_by_merged_prompt",
            "deterministic_social_fallback_line",
            "effective_scene_npc_roster",
            "effective_strict_social_resolution_for_emission",
            "emission_gate_interruption_active",
            "emission_gate_pressure_active",
            "emission_gate_uncertainty_source",
            "hard_reject_social_exchange_text",
            "interruption_cue_present_in_text",
            "is_conversational_npc_dialogue_line",
            "is_route_illegal_global_or_sanitizer_fallback_text",
            "is_scene_directed_watch_question",
            "is_social_exchange_resolution",
            "lawful_strict_social_dialogue_emergency_fallback_line",
            "log_final_emission_decision",
            "log_final_emission_trace",
            "looks_like_npc_directed_question",
            "merged_player_prompt_for_gate",
            "minimal_social_emergency_fallback_line",
            "minimal_social_resolution_for_directed_question_guard",
            "normalize_social_exchange_candidate",
            "player_line_triggers_strict_social_emission",
            "project_strict_social_replace_realization_family",
            "reconcile_strict_social_resolution_speaker",
            "repair_strict_social_terminal_dialogue_fallback_if_needed",
            "replacement_is_route_legal_social",
            "resolve_strict_social_npc_target_id",
            "select_best_grounded_social_answer_text",
            "select_strict_social_emergency_fallback_line",
            "should_apply_strict_social_exchange_emission",
            "social_fallback_line_for_sanitizer",
            "social_final_emission_malformed_player_echo",
            "stamp_strict_social_deterministic_fallback_family",
            "strict_social_deterministic_fallback_family_token",
            "strict_social_emission_will_apply",
            "strict_social_ownership_terminal_fallback",
            "strict_social_suppress_non_native_coercion_for_narration_beat",
            "strict_social_terminal_dialogue_fallback_valid",
            "synthetic_social_exchange_resolution_for_emission",
        ]
        '''
    )


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8-sig")
    if not BACKUP.exists():
        BACKUP.write_text(source, encoding="utf-8")

    segments, _ = _partition_source(source)
    game = ROOT / "game"
    _write_domain(game / "social_exchange_projection.py", "projection", segments["projection"])
    _write_domain(game / "social_exchange_policy.py", "policy", segments["policy"])
    _write_domain(game / "social_exchange_validation.py", "validation", segments["validation"])
    _write_domain(game / "social_exchange_fallback_catalog.py", "fallback_catalog", segments["fallback_catalog"])

    comp_body = "\n\n".join(segments["composition"]).strip()
    # composition uses _normalize_gate_text — ensure it's in validation extract or composition
    comp_content = _composition_header() + comp_body + _reexport_block() + "\n"
    SOURCE.write_text(comp_content, encoding="utf-8")
    print("BV14A extraction complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
