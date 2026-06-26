"""Lightweight direct-owner registry + governance checks (tests only; no runtime hooks).

This module answers: *who may authoritatively define a new legality rule or shipped contract
edge case?* It does **not** claim to catalog all meaningful coverage.

Design notes (read before extending):
- **Direct owner** = exactly one canonical test module that is allowed to introduce detailed
  normative assertions for the responsibility. Other suites may overlap behaviorally.
- **Neighbor** paths (smoke, transcript, gauntlet, evaluator, downstream consumer, compatibility
  residue) are *supporting* surfaces. They must not be named as the direct owner for **live
  legality** responsibilities (gate-era rules, sanitizer post-processing, shipped policy
  materialization, etc.).
- **Downstream consumer** suites (Cycle AD-3 / AL4): integration-visible smoke only — player-facing
  text hygiene, repair/replacement evidence, contract threading through HTTP/API, and
  layer-specific checked/failed/repaired fields owned by that consumer (e.g. answer
  completeness, response delta). They must **not** restate exact gate orchestration tables
  (``final_route``, ``final_emitted_source``, owner-bucket mapping, repair-kind enumeration)
  already owned by ``tests/test_final_emission_gate.py``; prefer
  ``tests/helpers/emission_smoke_assertions.py`` for route/phrase smoke helpers.
- **Smoke facade** (Cycle AL4): ``tests/helpers/emission_smoke_assertions.py`` is the intended
  downstream assertion surface for HTTP/pipeline wiring — intentionally weaker than owner
  legality suites. Replay/golden projection helpers stay separate
  (``tests/helpers/golden_replay_projection.py``, ``tests/helpers/opening_fallback_evidence.py``).
- **Smoke suites**: survival / wiring / one-phrase hygiene checks; not full legality matrices.
- **Gauntlet / replay neighbors** (e.g. ``tests/test_golden_replay.py`` redirect stub and
  ``tests/test_golden_replay_*.py`` focused integration files): intentional
  diagnostic observation and drift projection locks — not runtime gate orchestration owners.
  Classifier/dashboard FEM bucket columns follow the same rule (diagnostic projection, not
  gate ownership).
- New validation rules should land with a clear direct owner first; only then add broad
  regression, transcript, or gauntlet coverage so failures stay attributable.
- **Gate magnet guard** (Cycle BA-7 / AG-10): gate-layer direct-owner suites (except FEM meta
  projection and gauntlet) must not import ``golden_replay_projection``, classifier, or
  dashboard read-side helpers, or accumulate replay/dashboard/classifier projection assertions.
  Enforced by ``test_ba7_gate_direct_owners_*`` in this module.
- **Gate dependency compression guard** (Cycle BD-6): non-owner tests must not reintroduce
  direct imports of gate entry, FEM read, replay projection, or owner-bucket constants already
  routed through helper facades during BD-2–BD-5. Enforced by ``test_bd6_gate_dependency_compression_*``.
- **BV7C smoke monolith import lockdown** (Cycle BV7C): non-barrel modules must not import
  BV7A/BV7B extracted bridge or consumer-layer symbols from
  ``tests/helpers/emission_smoke_assertions.py``; route through
  ``response_type_smoke``, ``actor_consistency_smoke``, ``route_determinism_smoke``,
  ``replay_fem_read_smoke``, ``gate_orchestration_smoke``, or ``fallback_bridge_smoke``.
  Compatibility barrels ``replay_smoke_assertions`` and ``gate_integration_smoke`` remain
  re-export-only shims (BV12B consumer migration complete). Monolith FI capped at 18 static
  importers (phrase/route/speaker smoke only). Enforced by ``test_bv7c_smoke_monolith_*``.
- **BV12A/BV12B smoke-bridge domain facades** (Cycle BV12A/BV12B): replay FEM read, gate
  orchestration, and fallback dual-bridge surfaces live in ``replay_fem_read_smoke``,
  ``gate_orchestration_smoke``, and ``fallback_bridge_smoke``. BV12B migrated consumers off
  compatibility barrels onto domain facades; barrels remain re-export shims for BV12C governance.
- **BV12C compat barrel regrowth lockdown** (Cycle BV12C): non-barrel modules must not import
  ``replay_smoke_assertions`` or ``gate_integration_smoke`` directly; route through
  ``replay_fem_read_smoke``, ``gate_orchestration_smoke``, or ``fallback_bridge_smoke``.
  Compat barrel FI capped at 2 each (delegate verification residual only). Enforced by
  ``test_bv12c_compat_barrel_*``. Intentional domain hubs:
  ``tests.helpers.replay_fem_read_smoke`` (FEM read + debug notes),
  ``tests.helpers.gate_orchestration_smoke`` (gate consumer + HTTP stub),
  ``tests.helpers.fallback_bridge_smoke`` (dual-bridge fallback suites).
- **BV13A final-emission text extraction** (Cycle BV13A): formatting primitives live in
  ``final_emission_text_formatting``; validator policy vocabulary in ``final_emission_text_policy``;
  legacy semantic repair in ``final_emission_text_legacy_semantic_repair``. Compatibility barrel
  ``final_emission_text`` re-exports only until Phase 2 consumer migration. Enforced by
  ``test_bv13a_final_emission_text_facade_delegates``.
- **BV13B text consumer migration** (Cycle BV13B): production/tests import formatting and policy
  authorities directly; compat barrel reserved for fallback wrapper and legacy re-exports.
  Enforced by ``test_bv13a_*`` delegate identity + AST fan-in reports in ``docs/audits/BV13B_*``.
- **BV13C text compat barrel regrowth lockdown** (Cycle BV13C): non-barrel modules must not import
  ``game.final_emission_text`` for formatting or policy symbols; route through
  ``final_emission_text_formatting`` or ``final_emission_text_policy``. Compat barrel FI capped at
  8 (fallback wrapper + delegate verification residual only). Enforced by
  ``test_bv13c_text_compat_*``. Intentional text domain hubs:
  ``game.final_emission_text_formatting`` (text normalization/sanitization primitives),
  ``game.final_emission_text_policy`` (validator policy vocabulary tuples),
  ``game.final_emission_text_legacy_semantic_repair`` (test-only legacy semantic repair).
- **BV14A social-exchange emission extraction** (Cycle BV14A): fallback catalog, policy, validation,
  and projection live in ``social_exchange_fallback_catalog``, ``social_exchange_policy``,
  ``social_exchange_validation``, and ``social_exchange_projection``. Compatibility barrel
  ``social_exchange_emission`` retains strict-social composition authority only. Enforced by
  ``test_bv14a_social_exchange_emission_facade_delegates``.
- **BV14B social-exchange consumer migration** (Cycle BV14B): production/tests import fallback,
  policy, validation, and projection authorities directly; compat barrel reserved for composition
  assembly and BD-2 legality surfaces. Enforced by ``test_bv14a_*`` delegate identity + AST fan-in
  reports in ``docs/audits/BV14B_*``.
- **BV14C social-exchange compat barrel regrowth lockdown** (Cycle BV14C): non-barrel modules must
  not import ``game.social_exchange_emission`` for fallback, policy, validation, or projection
  symbols; route through ``social_exchange_fallback_catalog``, ``social_exchange_policy``,
  ``social_exchange_validation``, or ``social_exchange_projection``. Compat barrel FI capped at 12
  (composition authority + BD-2 legality + delegate verification residual only). Enforced by
  ``test_bv14c_social_exchange_compat_*``. Intentional social-exchange domain hubs:
  ``game.social_exchange_fallback_catalog`` (strict-social fallback phrase catalog),
  ``game.social_exchange_policy`` (strict-social routing/policy predicates),
  ``game.social_exchange_validation`` (route legality + interruption shape validators),
  ``game.social_exchange_projection`` (final-emission logging/trace projection).
- **BV2C meta import lockdown** (Cycle BV2C): non-owner ``game/`` and ``tests/`` modules must not
  import ``game.final_emission_meta`` directly except production write owners and the FEM owner /
  governance suites. Read traffic routes through ``final_emission_meta_read``,
  ``final_emission_owner_bucket_views``, or ``final_emission_replay_projection``. Enforced by
  ``test_bv2c_final_emission_meta_direct_import_guard_*``.
- **BV10 read-cluster facade routing** (Cycle BV10C): non-owner modules must not import
  ``final_emission_meta_read``, ``final_emission_owner_bucket_views``, or
  ``final_emission_ownership_schema`` directly except production write owners, vocabulary
  authority modules, facade delegates, and allowlisted owner suites. Route attribution reads
  through ``game.attribution_read_views``; lineage/sanitizer projection through
  ``game.ownership_projection_views``; observability/FEM dict reads through
  ``game.observability_attribution_read`` or ``tests/helpers/replay_fem_read_smoke``.
  Enforced by ``test_bv10_read_cluster_direct_import_guard_*``.
- **Runtime gate entry guard** (Cycle BN1): non-owner ``game/`` modules must not import
  ``apply_final_emission_gate`` from ``game.final_emission_gate``; runtime/API callers use
  ``game.final_emission_runtime.finalize_player_facing_emission``. Enforced by
  ``test_bn1_runtime_gate_entry_*``.
- **Lazy gate namespace guard** (Cycle BN2): ``final_emission_non_strict_stack`` and
  ``final_emission_terminal_pipeline`` must not lazy-import ``game.final_emission_gate as feg``
  or access ``feg.<symbol>``; layer owners are imported directly. Enforced by
  ``test_bn2_lazy_gate_namespace_*``.
- **Gate context preflight import guard** (Cycle BN3): ``final_emission_gate_context`` must not
  regrow direct layer-meta owner imports after preflight-defaults extraction; use
  ``final_emission_gate_preflight_defaults``. Enforced by ``test_bn3_gate_context_*``.
- **Gate context telemetry import guard** (Cycle BN4): ``final_emission_gate_context`` must not
  regrow direct telemetry/provenance imports after preflight-telemetry extraction; use
  ``final_emission_gate_preflight_telemetry``. Enforced by ``test_bn4_gate_context_*``.
- **Gate context upstream attach import guard** (Cycle BN5): ``final_emission_gate_context`` must
  not regrow direct upstream attach imports after preflight-upstream extraction; use
  ``final_emission_gate_preflight_upstream``. Enforced by ``test_bn5_gate_context_*``.
- **Gate context turn-packet import guard** (Cycle BN6): ``final_emission_gate_context`` must not
  regrow direct response-policy / turn-packet setup imports after preflight turn-packet extraction;
  use ``final_emission_gate_preflight_turn_packet``. Enforced by ``test_bn6_gate_context_*``.
- **Gate context interaction metadata import guard** (Cycle BN7): ``final_emission_gate_context``
  must not regrow direct interaction inspection imports after preflight interaction extraction; use
  ``final_emission_gate_preflight_interaction``. Enforced by ``test_bn7_gate_context_*``.
- **Gate context strict-social routing import guard** (Cycle BN8): ``final_emission_gate_context``
  must not regrow direct strict-social routing/sanitizer imports after preflight strict-social
  extraction; use ``final_emission_gate_preflight_strict_social``. Enforced by
  ``test_bn8_gate_context_*``.
- **Gate context pregate text import guard** (Cycle BN9): ``final_emission_gate_context`` must not
  regrow direct ``final_emission_text`` imports after preflight pregate-text extraction; use
  ``final_emission_gate_preflight_pregate_text``. Enforced by ``test_bn9_gate_context_*``.
- **Gate context branch-flag derivation guard** (Cycle BN10): branch flags must route through
  ``final_emission_gate_preflight_branch_flags``. Enforced by ``test_bn10_gate_context_*``.
- **Gate context preflight-only import allowlist** (Cycle BN11): ``final_emission_gate_context``
  may import only stdlib/typing plus ``final_emission_gate_preflight_*`` helpers. Enforced by
  ``test_bn11_gate_context_*``.

Governance consumes the live inventory from ``tests/test_inventory_governance.json`` (regenerate via
``py -3 tools/test_audit.py``). Unclassified test files elsewhere in the repo do not affect
these checks.

Cycle AL4 legality-owner quick reference (downstream suites assert wiring/smoke only):
- Final emission gate orchestration / route tables → ``tests/test_final_emission_gate.py``
  (redirect stub; practical coverage in ``tests/test_final_emission_gate_*.py`` owner files)
- FEM projection / lineage → ``tests/test_final_emission_meta.py`` (``final_emission_meta_projection``)
- Dialogue route classification table → ``tests/test_dialogue_routing_lock.py`` (pure
  ``choose_interaction_route``; HTTP packaging smoke → ``tests/test_turn_pipeline_shared.py``)
- Sanitizer phrase legality → ``tests/test_output_sanitizer.py`` (``output_sanitizer_final_string_cleanup``)
- Strict-social phrase/source legality → ``tests/test_social_exchange_emission.py``
  (``social_emission_legality_surface``)
- Downstream HTTP smoke/wiring → ``tests/test_turn_pipeline_shared.py`` (registered neighbor)
- Downstream smoke facade → ``tests/helpers/emission_smoke_assertions.py`` (helpers module)

Cycle BE6 — triple-layer scaffold / phrase split (documentation lock; **do not merge**):

1. ``tests/test_output_sanitizer.py`` — full sanitizer/procedural phrase **legality matrices**
2. ``tests/helpers/emission_smoke_assertions.py`` — weak HTTP/pipeline **smoke** phrases only
3. ``tests/helpers/golden_replay_projection.py`` — replay **scaffold-leakage projection**
   (``final_text_has_scaffold_leakage``, protected observation path)

Assertion-economy blocks must not unify these into one shared phrase matrix. Enforced by
``test_be6_scaffold_phrase_triple_layer_split_locked``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import types
from dataclasses import replace
from pathlib import Path
from typing import AbstractSet, Final, Mapping, Tuple

import pytest

from tests.ownership_registry_contract import (
    RESPONSIBILITY_REGISTRY,
    ResponsibilityRecord,
    _CROSS_FILE_DUPLICATE_ALLOWLIST,
    _REQUIRED_GROUP_IDS,
    build_ownership_registry_index,
)
from tests.ownership_inventory_governance import (
    CANONICAL_VALIDATION_LAYERS,
    DEFAULT_GOVERNANCE_INVENTORY_PATH,
    DOWNSTREAM_INTEGRATION_SMOKE_ONLY,
    LIVE_LEGALITY_GROUP_IDS,
    collect_ownership_governance_errors,
    direct_owner_inventory_layer_ok,
    full_inventory_by_path,
    inventory_paths,
    load_governance_inventory,
)
from tests.ownership_guard_bd_dependency_compression import (
    _BD6_GATE_BRIDGE_FACADE,
    _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
    _BD6_GOLDEN_REPLAY_FACADE,
    _BD6_REPLAY_BRIDGE_FACADE,
    collect_gate_dependency_compression_guard_violations,
    iter_gate_dependency_compression_guard_scan_paths,
)
from tests.ownership_guard_bi8_golden_replay_boundary import (
    BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS,
    BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS,
    BI8_GOLDEN_REPLAY_OWNED_EXPORTS,
    BI8_GOLDEN_REPLAY_TARGETS,
    collect_bi8_golden_replay_documentation_phrase_violations,
    collect_bi8_golden_replay_forbidden_export_violations,
    collect_bi8_golden_replay_forbidden_source_fragment_violations,
    load_bi8_golden_replay_target_sources,
    parse_bi8_golden_replay_api_exports,
)
from tests.ownership_guard_bn_gate_context import (
    BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT,
    BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
    BN1_RUNTIME_GATE_ENTRY_REPLACEMENT,
    BN2_LAZY_GATE_NAMESPACE_FILES,
    BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE,
    BN3_GATE_CONTEXT_OWNER_MODULE,
    BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE,
    BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE,
    BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE,
    BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE,
    BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE,
    BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE,
    BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE,
    BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE,
    BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES,
    BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS,
    collect_bn1_runtime_gate_entry_guard_violations,
    collect_bn2_lazy_gate_namespace_violations,
    collect_bn3_gate_context_layer_meta_import_violations,
    collect_bn4_gate_context_telemetry_import_violations,
    collect_bn4_preflight_telemetry_helper_gate_import_violations,
    collect_bn5_gate_context_upstream_import_violations,
    collect_bn5_preflight_upstream_helper_gate_import_violations,
    collect_bn6_gate_context_turn_packet_import_violations,
    collect_bn6_preflight_turn_packet_helper_gate_import_violations,
    collect_bn7_gate_context_interaction_import_violations,
    collect_bn7_preflight_interaction_helper_gate_import_violations,
    collect_bn8_gate_context_strict_social_import_violations,
    collect_bn8_preflight_strict_social_helper_import_violations,
    collect_bn9_gate_context_pregate_text_import_violations,
    collect_bn9_preflight_pregate_text_helper_import_violations,
    collect_bn10_gate_context_branch_flags_violations,
    collect_bn10_preflight_branch_flags_helper_import_violations,
    collect_bn11_gate_context_preflight_only_import_violations,
    collect_bn11_scan_logic_runtime_gate_import_violations,
    gate_context_import_modules,
    iter_bn1_runtime_gate_entry_guard_scan_paths,
)
from tests.ownership_guard_bv16c_terminal_monkeypatch import (
    BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS,
    BV16C_IC_OWNER,
    BV16C_N4_OWNER,
    BV16C_OPENING_OWNER,
    BV16C_REPAIRS_OWNER,
    BV16C_TERMINAL_ORCHESTRATION_SYMBOLS,
    BV16C_TERMINAL_PIPELINE_MODULE,
    BV16C_VISIBILITY_OWNER,
    collect_bv16c_terminal_delegate_monkeypatch_violations,
    iter_bv16c_terminal_monkeypatch_scan_paths,
)
from tests.ownership_guard_bv_compatibility import (
    _BD6_AC_SMOKE_FACADE,
    _BD6_RD_SMOKE_FACADE,
    _BD6_RT_SMOKE_FACADE,
    _BV10C_ATTRIBUTION_READ_FACADE,
    _BV10C_OBSERVABILITY_READ_FACADE,
    _BV10C_READ_CLUSTER_TEST_ALLOWLIST,
    _BV12A_FALLBACK_BRIDGE_FACADE,
    _BV12A_GATE_ORCHESTRATION_FACADE,
    _BV12A_REPLAY_FEM_READ_FACADE,
    _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS,
    _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS,
    _BV12C_COMPAT_BARREL_FI_CAP,
    _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST,
    _BV12C_COMPAT_BARREL_SCAN_ROOTS,
    _BV12C_GATE_COMPAT_MODULE,
    _BV12C_INTENTIONAL_DOMAIN_HUBS,
    _BV12C_REPLAY_COMPAT_MODULE,
    _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS,
    _BV13C_INTENTIONAL_TEXT_DOMAIN_HUBS,
    _BV13C_TEXT_COMPAT_FI_CAP,
    _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST,
    _BV13C_TEXT_COMPAT_MODULE,
    _BV13C_TEXT_COMPAT_SCAN_ROOTS,
    _BV13C_TEXT_FORMATTING_AUTHORITY,
    _BV13C_TEXT_LEGACY_REPAIR_AUTHORITY,
    _BV13C_TEXT_POLICY_AUTHORITY,
    _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS,
    _BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE,
    _BV14C_SOCIAL_EXCHANGE_COMPAT_SCAN_ROOTS,
    _BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY,
    _BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY,
    _BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST,
    _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS,
    _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS,
    _BV7B_EXTRACTED_AC_SYMBOLS,
    _BV7B_EXTRACTED_RD_SYMBOLS,
    _BV7B_EXTRACTED_RT_SYMBOLS,
    _BV7C_ALLOWED_MONOLITH_DYNAMIC_IMPORTERS,
    _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS,
    _BV7C_EXTRACTED_SYMBOL_TO_FACADE,
    _BV7C_MONOLITH_FI_CAP,
    _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST,
    collect_bv10_read_cluster_direct_import_guard_violations,
    collect_bv12c_compat_barrel_import_guard_violations,
    collect_bv12c_compat_barrel_static_importers,
    collect_bv13c_text_compat_import_guard_violations,
    collect_bv13c_text_compat_static_importers,
    collect_bv14c_social_exchange_compat_import_guard_violations,
    collect_bv14c_social_exchange_compat_static_importers,
    collect_bv2c_final_emission_meta_import_violations,
    collect_bv7c_monolith_static_importers,
    collect_bv7c_smoke_monolith_import_guard_violations,
    iter_bv10_read_cluster_direct_import_guard_scan_paths,
    iter_bv12c_compat_barrel_import_guard_scan_paths,
    iter_bv13c_text_compat_import_guard_scan_paths,
    iter_bv14c_social_exchange_compat_import_guard_scan_paths,
    iter_bv2c_final_emission_meta_import_guard_scan_paths,
    iter_bv7c_smoke_monolith_import_guard_scan_paths,
)
from tests.ownership_guard_gate_magnet import (
    collect_gate_magnet_guard_import_violations,
    collect_gate_magnet_guard_source_fragment_violations,
    gate_magnet_guard_paths,
)


from tests.ownership_closeout_delegate_locks import (
    verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly,
    verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly,
    verify_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly,
    verify_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly,
    verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly,
    verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly,
    verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly,
    verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly,
    verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly,
    verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly,
    verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly,
    verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly,
    verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly,
    verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly,
    verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly,
    verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly,
    verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly,
    verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly,
    verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly,
    verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly,
    verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly,
    verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly,
    verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly,
    verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly,
    verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly,
    verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly,
    verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly,
    verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly,
    verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly,
    verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly,
    verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly,
    verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly,
    verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly,
    verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly,
    verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly,
    verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly,
    verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly,
    verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly,
    verify_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly,
    verify_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly,
    verify_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly,
    verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly,
    verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly,
    verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly,
    verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly,
    verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly,
    verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly,
    verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly,
    verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate,
    verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate,
    verify_bj120_ownership_registry_harness_patches_canonical_owner_seams,
    verify_bj121_ownership_registry_strict_social_build_patches_use_stack_seam,
    verify_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings,
    verify_bj123_ownership_registry_harness_patches_no_stale_feg_seams,
    verify_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports,
    verify_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate,
    verify_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate,
    verify_bj127_ownership_registry_global_stale_gate_harness_scan,
    verify_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports,
    verify_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked,
)


try:
    from game import validation_layer_contracts as vlc
except ImportError:  # pragma: no cover - repo layout guard
    vlc = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEST_AUDIT_PATH = _REPO_ROOT / "tools" / "test_audit.py"

_INVENTORY_PATH = DEFAULT_GOVERNANCE_INVENTORY_PATH

# Cycle AL4: documented downstream smoke facade (helpers module — not a pytest suite path).
_DOWNSTREAM_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"

# Cycle AL4: legality owners locked by AL1–AL3 convergence (see module docstring).
_AL4_LEGALITY_OWNER_PATHS: Final[Mapping[str, str]] = {
    "final_emission_gate": "tests/test_final_emission_gate.py",
    "final_emission_meta": "tests/test_final_emission_meta.py",
    "dialogue_route_classification": "tests/test_dialogue_routing_lock.py",
    "output_sanitizer": "tests/test_output_sanitizer.py",
    "social_exchange_emission": "tests/test_social_exchange_emission.py",
    "turn_pipeline_http_smoke": "tests/test_turn_pipeline_shared.py",
}

# Cycle BE6: scaffold/phrase ownership layers — intentional separation; do not merge matrices.
_BE6_SCAFFOLD_PHRASE_LAYER_OWNERS: Final[Mapping[str, str]] = {
    "sanitizer_legality": "tests/test_output_sanitizer.py",
    "http_smoke_facade": _DOWNSTREAM_SMOKE_FACADE,
    "replay_scaffold_projection": _BD6_GOLDEN_REPLAY_FACADE,
}

_BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_final_emission_gate_consumer",
        "enforce_response_type_contract_layer",
        "final_emission_meta_from_output",
        "read_turn_debug_notes",
    }
)
_BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_answer_completeness_layer",
        "apply_response_delta_layer",
        "assert_no_boundary_reorder_repair",
        "assert_response_delta_boundary_validate_only",
        "inspect_response_delta_failure",
        "skip_answer_completeness_layer",
        "skip_response_delta_layer",
        "strict_social_answer_pressure_rd_contract_active",
        "validate_answer_completeness",
        "validate_response_delta",
    }
)
_BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS: Final[Mapping[str, str]] = {
    "gate_legality": "full gate legality matrices belong to tests/test_final_emission_gate.py",
    "legality_matrix": "legality matrices belong to owner suites",
    "route_enum": "route enum tables belong to route/gate owner suites",
    "route_table": "route tables belong to route/gate owner suites",
    "sanitizer_legality": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "sanitizer_phrase": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "repair_matrix": "AC/RD repair semantics belong to owner suites",
    "repair_semantic": "AC/RD repair semantics belong to owner suites",
}



@pytest.fixture(scope="module")
def inventory() -> dict:
    return load_governance_inventory(_INVENTORY_PATH)


@pytest.fixture(scope="module")
def inventory_by_path(inventory: dict) -> dict[str, dict]:
    return inventory_paths(inventory)


@pytest.fixture(scope="module")
def test_audit_module() -> types.ModuleType:
    """Load ``tools/test_audit.py`` once per module (BF1: avoid repeated importlib loads)."""
    spec = importlib.util.spec_from_file_location("_inv_audit", _TEST_AUDIT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def full_inventory(test_audit_module: types.ModuleType) -> dict:
    """Fresh full audit payload once per module (BF1: single pytest collect-only per run)."""
    return test_audit_module.build_inventory_payload()


def test_registry_defines_all_required_groups() -> None:
    assert set(RESPONSIBILITY_REGISTRY) == _REQUIRED_GROUP_IDS

def test_inventory_schema_version_matches_audit_tool(test_audit_module: types.ModuleType, inventory: dict) -> None:
    """Block A: inventory generator and governance tests agree on schema generation."""
    assert inventory.get('summary', {}).get('inventory_schema_version') == test_audit_module.INVENTORY_SCHEMA_VERSION

def test_governance_inventory_contains_required_fields(inventory: dict) -> None:
    """AQ9: committed artifact retains stable governance sections only."""
    for key in ('summary', 'files'):
        assert key in inventory, f'missing governance inventory key {key!r}'
    assert 'cross_file_duplicate_test_names' not in inventory, 'governance JSON must not store cross_file_duplicate_test_names; derive via tools/test_audit.py --check'
    assert 'tests' not in inventory, 'governance JSON must not store tests[]; derive per-test marker coverage via tools/test_audit.py --check'
    assert 'block_b_overlap_clusters' not in inventory, 'governance JSON must not store block_b_overlap_clusters; use --full diagnostic output'
    assert 'import_hub_modules' not in inventory, 'governance JSON must not store import_hub_modules; use --full diagnostic output'
    assert 'ownership_registry_index' not in inventory, 'governance JSON must not embed ownership_registry_index; derive via build_ownership_registry_index()'
    assert inventory.get('summary', {}).get('inventory_kind') == 'governance'
    sample = inventory['files'][0]
    for key in ('path',):
        assert key in sample, f'missing governance file row key {key!r}'
    assert 'marker_set' not in sample, 'governance file rows must not store marker_set; derive via tools/test_audit.py --check'
    assert 'likely_architecture_layer' not in sample, 'governance file rows must not store likely_architecture_layer; derive via tools/test_audit.py --check'
    assert 'pytest_collected' not in sample, 'governance file rows must not store pytest_collected; derive via tools/test_audit.py --check'
    assert 'collected_duplicate_base_names' not in sample, 'governance file rows must not store collected_duplicate_base_names; derive via tools/test_audit.py --check'
    assert 'ownership_registry_positions' not in sample, 'governance file rows must not store ownership_registry_positions; derive via build_ownership_registry_index()'

def test_governance_summary_contains_stable_metadata_only(inventory: dict) -> None:
    """AQ9: committed summary retains stable metadata; counts are derived at --check."""
    summary = inventory.get('summary')
    assert isinstance(summary, dict)
    assert set(summary) == {'inventory_schema_version', 'inventory_kind', 'declared_pytest_markers'}
    assert summary.get('inventory_kind') == 'governance'

def test_governance_omits_cross_file_duplicate_test_names(inventory: dict) -> None:
    """AQ9: cross-file duplicate rows are derived from full audit, not committed."""
    assert 'cross_file_duplicate_test_names' not in inventory

def test_governance_rejects_stored_cross_file_duplicate_test_names(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ9: committed governance must not embed derived duplicate-name rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['cross_file_duplicate_test_names'] = [{'base_name': 'test_x', 'files': ['tests/test_a.py']}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store cross_file_duplicate_test_names' in e for e in errs))

def test_governance_file_rows_omit_committed_per_test_rows(inventory: dict) -> None:
    """AQ6: per-test marker rows are derived at check time, not committed."""
    assert 'tests' not in inventory

def test_governance_rejects_stored_per_test_rows(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ6: committed governance must not embed derived per-test marker rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['tests'] = [{'nodeid': 'tests/test_x.py::test_y', 'marker_set': ['unit']}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store tests[]' in e for e in errs))

def test_governance_file_rows_omit_marker_set(inventory: dict) -> None:
    """BF7: per-file marker sets are derived at check time, not committed."""
    with_markers = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'marker_set' in row]
    assert not with_markers, f'governance files must not store marker_set: {with_markers[:3]!r}'

def test_governance_rejects_stored_marker_set(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF7: committed governance must not embed derived per-file marker sets."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['marker_set'] = ['unit']
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store marker_set' in e for e in errs))

def test_governance_file_rows_omit_likely_architecture_layer(inventory: dict) -> None:
    """BF6: architecture-layer heuristics are derived at check time, not committed."""
    with_layers = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'likely_architecture_layer' in row]
    assert not with_layers, f'governance files must not store likely_architecture_layer: {with_layers[:3]!r}'

def test_governance_rejects_stored_likely_architecture_layer(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF6: committed governance must not embed derived architecture-layer heuristics."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['likely_architecture_layer'] = 'gate'
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store likely_architecture_layer' in e for e in errs))

def test_governance_file_rows_omit_collected_duplicate_base_names(inventory: dict) -> None:
    """BF5: in-file duplicate base names are derived at check time, not committed."""
    with_dups = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'collected_duplicate_base_names' in row]
    assert not with_dups, f'governance files must not store collected_duplicate_base_names: {with_dups[:3]!r}'

def test_governance_rejects_stored_collected_duplicate_base_names(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF5: committed governance must not embed derived in-file duplicate-base-name lists."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['collected_duplicate_base_names'] = ['test_dup']
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store collected_duplicate_base_names' in e for e in errs))

def test_governance_file_rows_omit_pytest_collected(inventory: dict) -> None:
    """BF4: per-file collect counts are derived at check time, not committed."""
    with_counts = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'pytest_collected' in row]
    assert not with_counts, f'governance files must not store pytest_collected: {with_counts[:3]!r}'

def test_governance_rejects_stored_pytest_collected(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF4: committed governance must not embed derived per-file collect counts."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['pytest_collected'] = 99
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store pytest_collected' in e for e in errs))

def test_governance_file_rows_omit_registry_positions(inventory: dict) -> None:
    """AQ5: per-file registry positions are derived, not committed."""
    with_positions = [row.get('path') for row in inventory.get('files', []) if isinstance(row, dict) and 'ownership_registry_positions' in row]
    assert not with_positions, f'governance files must not store ownership_registry_positions: {with_positions[:3]!r}'

def test_governance_committed_files_exclude_non_registry_paths(inventory: dict, full_inventory: dict, test_audit_module: types.ModuleType) -> None:
    """AQ8: committed governance files[] retains registry-owned paths only (+ cross-file dup files)."""
    allowed = test_audit_module.governance_committed_file_paths(full_inventory)
    committed = {str(row['path']).replace('\\', '/') for row in inventory.get('files', []) if isinstance(row, dict)}
    extra = sorted(committed - allowed)
    assert not extra, f'governance files[] includes non-governance paths: {extra[:5]!r}'

def test_governance_committed_files_include_all_registry_paths(inventory_by_path: dict[str, dict]) -> None:
    """AQ8: every registry-owned path appears in committed governance files[]."""
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted((fp for fp in files_roles if fp not in inventory_by_path))
    assert not missing, f'registry-owned paths missing from committed governance: {missing[:5]!r}'

def test_governance_rejects_non_registry_committed_file_row(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ8: committed governance must not embed non-registry file rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'] = list(polluted.get('files', [])) + [{'path': 'tests/test_non_registry_module.py'}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store non-governance path' in e for e in errs))

def test_derived_registry_paths_present_in_inventory(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """AQ5: derived files_roles paths remain inventory-backed for direct-owner/neighbor checks."""
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted((fp for fp in files_roles if fp not in inventory_by_path))
    assert not missing, f'derived registry paths missing from inventory: {missing[:5]!r}'
    gate = 'tests/test_final_emission_gate.py'
    assert gate in files_roles
    assert files_roles[gate] == [{'group_id': 'final_emission_gate_orchestration', 'role': 'direct_owner'}]
    full_by_path = full_inventory_by_path(full_inventory)
    assert full_by_path[gate].get('likely_architecture_layer') == 'gate'

def test_derived_registry_index_matches_live_registry() -> None:
    """AQ4: neighbor/group maps are derived from Python registry, not committed JSON."""
    idx = build_ownership_registry_index()
    assert idx.get('available') is True
    groups = idx.get('groups')
    roles = idx.get('files_roles')
    assert isinstance(groups, dict) and isinstance(roles, dict)
    assert set(groups) == _REQUIRED_GROUP_IDS
    assert 'final_emission_gate_orchestration' in groups
    gate = groups['final_emission_gate_orchestration']
    assert isinstance(gate, dict)
    assert gate.get('direct_owner') == 'tests/test_final_emission_gate.py'
    assert isinstance(gate.get('transcript_suites'), list)
    for key in ('smoke_suites', 'transcript_suites', 'gauntlet_suites', 'evaluator_suites', 'downstream_consumer_suites', 'compatibility_residue_suites'):
        assert key in gate, f'missing derived registry groups field {key!r}'

def test_governance_omits_triage_aggregates(inventory: dict) -> None:
    """AQ7: diagnostic triage aggregates are full-only, not committed."""
    assert 'block_b_overlap_clusters' not in inventory
    assert 'import_hub_modules' not in inventory

def test_governance_rejects_stored_triage_aggregates(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ7: committed governance must not embed full-only triage aggregates."""
    polluted = json.loads(json.dumps(inventory))
    polluted['block_b_overlap_clusters'] = [{'kind': 'dense_ownership_theme_by_architecture_layer', 'cells': []}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store block_b_overlap_clusters' in e for e in errs))

def test_inventory_block_b_schema_v2_coherence(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """AQ7: triage aggregates and registry paths are validated; clusters/hubs derived from full audit."""
    clusters = full_inventory.get('block_b_overlap_clusters')
    assert isinstance(clusters, list) and clusters, 'block_b_overlap_clusters must be a non-empty list in full output'
    kinds = {c.get('kind') for c in clusters if isinstance(c, dict)}
    assert 'dense_ownership_theme_by_architecture_layer' in kinds
    hubs = full_inventory.get('import_hub_modules')
    assert isinstance(hubs, list)
    files_roles = build_ownership_registry_index().get('files_roles', {})
    assert isinstance(files_roles, dict)
    for fp, roles in files_roles.items():
        assert fp in inventory_by_path, f'derived registry path not in inventory: {fp}'
        assert isinstance(roles, list) and roles

def test_evaluator_neighbor_may_have_general_inventory_layer(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """Heuristic ``general`` is allowed for non-owner paths; governance only sharpens direct owners."""
    p = 'tests/test_player_agency_evaluator.py'
    assert p in inventory_by_path
    full_row = full_inventory_by_path(full_inventory).get(p)
    assert full_row is not None and full_row.get('likely_architecture_layer') == 'general'
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=LIVE_LEGALITY_GROUP_IDS, full_inventory_by_path=full_inventory_by_path(full_inventory))
    assert not any((p in e for e in errs))

def test_governance_rejects_stored_registry_positions(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ5: committed governance rows must not embed derived registry positions."""
    polluted = json.loads(json.dumps(inventory))
    polluted['files'][0]['ownership_registry_positions'] = [{'group_id': 'x', 'role': 'direct_owner'}]
    polluted_by_path = inventory_paths(polluted)
    errs = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, polluted, polluted_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('must not store ownership_registry_positions' in e for e in errs))

def test_governance_rejects_duplicate_direct_owner(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    owner = 'tests/test_save_load.py'
    reg = {'a': replace(RESPONSIBILITY_REGISTRY['engine_truth_persistence_mechanics'], direct_owner=owner), 'b': replace(RESPONSIBILITY_REGISTRY['planner_prompt_bundle_shipped_contract'], direct_owner=owner)}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('duplicate direct_owner' in e for e in errs))

def test_governance_rejects_missing_inventory_path(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    reg = {'__missing__': ResponsibilityRecord(human_title='Synthetic', declared_architecture_layer='engine', direct_owner='tests/__this_file_should_not_exist__.py')}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset())
    assert any(('not in inventory' in e for e in errs))

def test_direct_owner_general_disallowed_when_declared_layer_set() -> None:
    assert not direct_owner_inventory_layer_ok('engine', 'general')
    assert not direct_owner_inventory_layer_ok('gate', 'General')
    assert direct_owner_inventory_layer_ok(None, 'general')
    assert direct_owner_inventory_layer_ok('engine', 'smoke')
    assert direct_owner_inventory_layer_ok('engine', 'engine')

def test_governance_rejects_sharp_direct_owner_layer_mismatch(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    reg = {'__layer__': ResponsibilityRecord(human_title='Synthetic layer mismatch', declared_architecture_layer='gate', direct_owner='tests/test_save_load.py')}
    errs = collect_ownership_governance_errors(reg, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=frozenset(), full_inventory_by_path=full_inventory_by_path(full_inventory))
    assert any(('inventory layer incompatible' in e for e in errs))

def test_inventory_per_test_rows_include_marker_set(test_audit_module: types.ModuleType, full_inventory: dict) -> None:
    """AQ6: per-test marker_set is derived from fresh audit output, not committed JSON."""
    rows = test_audit_module.derive_per_test_marker_rows(full_inventory)
    assert rows, 'expected derived per-test marker rows from fresh inventory'
    missing = [r.get('nodeid') for r in rows if not isinstance(r, dict) or 'marker_set' not in r]
    assert not missing, f'missing marker_set on {len(missing)} derived rows (first: {missing[:3]!r})'

def test_governance_registry_paths_have_derived_marker_sets(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF7: registry-owned paths retain marker_set data in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        marker_set = frow.get('marker_set')
        assert isinstance(marker_set, list)

def test_governance_registry_paths_have_derived_architecture_layers(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF6: registry-owned paths retain architecture-layer heuristics in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        layer = frow.get('likely_architecture_layer')
        assert isinstance(layer, str) and layer.strip()

def test_governance_registry_paths_have_derived_duplicate_base_names(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF5: registry-owned paths retain in-file duplicate-base-name data in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        dup_bases = frow.get('collected_duplicate_base_names')
        assert isinstance(dup_bases, list)

def test_governance_registry_paths_have_live_collected_counts(inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    """BF4: registry-owned paths retain live per-file collect counts in derived full audit."""
    full_by_path = full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f'{fp} missing from full inventory'
        collected = frow.get('pytest_collected')
        nodeids = frow.get('collected_nodeids')
        assert isinstance(collected, int) and collected >= 0
        assert isinstance(nodeids, list)
        assert collected == len(nodeids), f'{fp}: pytest_collected mismatch vs collected_nodeids'

def test_cross_file_duplicate_allowlist_from_derived_full_audit(test_audit_module: types.ModuleType, full_inventory: dict) -> None:
    """AQ9: duplicate allowlist enforcement uses derived full audit output."""
    dups = full_inventory.get('cross_file_duplicate_test_names')
    assert isinstance(dups, list)
    errs = test_audit_module.collect_cross_file_duplicate_governance_errors(dups, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST)
    assert not errs, 'derived cross-file duplicate allowlist failures:\n' + '\n'.join(errs)

def test_canonical_validation_layers_importable() -> None:
    assert vlc is not None, 'game.validation_layer_contracts must import for layer alignment'
    assert set(vlc.CANONICAL_VALIDATION_LAYERS) == CANONICAL_VALIDATION_LAYERS

def test_ownership_registry_governance(inventory: dict, inventory_by_path: dict[str, dict], full_inventory: dict) -> None:
    derived_dups = full_inventory.get('cross_file_duplicate_test_names')
    errors = collect_ownership_governance_errors(RESPONSIBILITY_REGISTRY, inventory, inventory_by_path, cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST, live_legality_group_ids=LIVE_LEGALITY_GROUP_IDS, cross_file_duplicate_test_names=derived_dups if isinstance(derived_dups, list) else None, full_inventory_by_path=full_inventory_by_path(full_inventory))
    assert not errors, 'ownership governance failures:\n' + '\n'.join(errors)

def test_allowlist_entries_have_non_empty_reasons() -> None:
    for name, reason in _CROSS_FILE_DUPLICATE_ALLOWLIST.items():
        assert name.startswith('test_'), name
        assert reason.strip(), f'empty allowlist reason for {name!r}'

def test_final_emission_meta_projection_read_side_ownership_boundaries() -> None:
    """Cycle AE4: read-side lineage/projection edits stay in meta projection ownership."""
    meta_proj = RESPONSIBILITY_REGISTRY['final_emission_meta_projection']
    gate_orch = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    assert meta_proj.direct_owner == 'tests/test_final_emission_meta.py'
    assert gate_orch.direct_owner == 'tests/test_final_emission_gate.py'
    assert meta_proj.direct_owner != gate_orch.direct_owner
    gate_path = 'tests/test_final_emission_gate.py'
    assert gate_path not in meta_proj.downstream_consumer_suites
    assert gate_path not in meta_proj.smoke_suites
    assert gate_path not in meta_proj.transcript_suites
    assert gate_path not in meta_proj.gauntlet_suites
    assert gate_path not in meta_proj.evaluator_suites
    assert gate_path not in meta_proj.compatibility_residue_suites
    title = meta_proj.human_title.lower()
    assert 'read path' in title or 'replay read path' in title
    assert 'projection' in title
    assert 'gate orchestration' not in title

def test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners() -> None:
    """BA-7: magnet guard spans gate-layer direct owners except meta projection and gauntlet."""
    guarded = gate_magnet_guard_paths()
    assert 'tests/test_final_emission_gate.py' in guarded
    assert 'tests/test_final_emission_validators.py' in guarded
    assert 'tests/test_output_sanitizer.py' in guarded
    assert 'tests/test_final_emission_meta.py' not in guarded
    assert 'tests/test_gauntlet_regressions.py' not in guarded

def test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not import replay/dashboard/classifier projection helpers."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing gate magnet-guard path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_gate_magnet_guard_import_violations(rel, source))
    assert not violations, 'gate magnet-guard import violations:\n' + '\n'.join(violations)

def test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not re-own replay/dashboard/classifier projection contracts."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_gate_magnet_guard_source_fragment_violations(rel, source))
    assert not violations, 'gate magnet-guard source-fragment violations:\n' + '\n'.join(violations)

def test_final_emission_gate_does_not_accumulate_read_side_projection_assertions() -> None:
    """AG-10: primary gate owner stays free of replay read-side projection assertion creep."""
    rel = 'tests/test_final_emission_gate.py'
    source = (_REPO_ROOT / rel).read_text(encoding='utf-8')
    violations = collect_gate_magnet_guard_source_fragment_violations(rel, source)
    assert not violations, 'tests/test_final_emission_gate.py owns gate orchestration/wrappers, not read-side replay projection assertions. Move these contracts to tests/test_final_emission_meta.py:\n' + '\n'.join(violations)

def test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons() -> None:
    """BD-6: every compression-guard allowlist path documents why it may import compressed gate symbols."""
    for path, reason in _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST.items():
        assert path.startswith('tests/'), path
        assert reason.strip(), f'empty BD-6 allowlist reason for {path!r}'

def test_bd6_gate_dependency_compression_guard_detects_synthetic_violation() -> None:
    """BD-6: guard flags representative compressed imports with facade guidance."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\nfrom game.final_emission_meta import read_final_emission_meta_from_turn_payload, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED\nimport game.final_emission_replay_projection as replay\n'
    rel = 'tests/test_synthetic_bd6_violation.py'
    violations = collect_gate_dependency_compression_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert any(('apply_final_emission_gate' in v for v in violations))
    assert any(('read_final_emission_meta_from_turn_payload' in v for v in violations))
    assert any(('OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED' in v for v in violations))
    assert any(('final_emission_replay_projection' in v for v in violations))
    assert 'apply_final_emission_gate_consumer' in joined
    assert 'final_emission_meta_from_output' in joined
    assert 'opening_fallback_evidence' in joined
    assert 'build_fem_runtime_lineage_events' in joined

def test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports() -> None:
    """BD-6: non-owner tests must not reintroduce direct imports compressed during BD-2–BD-5."""
    violations: list[str] = []
    for rel in iter_gate_dependency_compression_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BD-6 scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_gate_dependency_compression_guard_violations(rel, source))
    assert not violations, 'gate dependency compression-guard import violations:\n' + '\n'.join(violations)

def test_bv2c_final_emission_meta_direct_import_allowlist_entries_have_non_empty_reasons() -> None:
    """BV2C: every meta direct-import allowlist path documents why it may import the write owner."""
    for path, reason in _BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST.items():
        assert path.startswith('tests/'), path
        assert reason.strip(), f'empty BV2C allowlist reason for {path!r}'

def test_bv2c_final_emission_meta_direct_import_guard_detects_synthetic_violation() -> None:
    """BV2C: guard flags representative read-side imports with facade guidance."""
    synthetic = 'from game.final_emission_meta import read_final_emission_meta_dict, default_response_type_debug\nimport game.final_emission_meta as emission_meta\n'
    rel = 'tests/test_synthetic_bv2c_violation.py'
    violations = collect_bv2c_final_emission_meta_import_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert any(('read_final_emission_meta_dict' in v for v in violations))
    assert any(('default_response_type_debug' in v for v in violations))
    assert 'game.final_emission_meta_read' in joined

def test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades() -> None:
    """BV2C: non-owner modules must not import game.final_emission_meta directly."""
    violations: list[str] = []
    for rel in iter_bv2c_final_emission_meta_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV2C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv2c_final_emission_meta_import_violations(rel, source))
    assert not violations, 'BV2C final_emission_meta direct-import violations:\n' + '\n'.join(violations)

def test_bv10_read_cluster_direct_import_allowlist_entries_have_non_empty_reasons() -> None:
    """BV10C: every read-cluster allowlist path documents why it may import authority modules."""
    for path, reason in _BV10C_READ_CLUSTER_TEST_ALLOWLIST.items():
        assert path.startswith('tests/'), path
        assert reason.strip(), f'empty BV10C allowlist reason for {path!r}'

def test_bv10_read_cluster_direct_import_guard_detects_synthetic_violation() -> None:
    """BV10C: guard flags representative read-cluster authority imports with facade guidance."""
    synthetic = 'from game.final_emission_meta_read import read_final_emission_meta_dict\nfrom game.final_emission_owner_bucket_views import opening_fallback_owner_bucket_from_meta\nfrom game.final_emission_ownership_schema import ALLOWED_FALLBACK_SELECTION_OWNERS\n'
    rel = 'tests/test_synthetic_bv10c_violation.py'
    violations = collect_bv10_read_cluster_direct_import_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert any(('read_final_emission_meta_dict' in v for v in violations))
    assert any(('opening_fallback_owner_bucket_from_meta' in v for v in violations))
    assert any(('ALLOWED_FALLBACK_SELECTION_OWNERS' in v for v in violations))
    assert _BV10C_ATTRIBUTION_READ_FACADE in joined
    assert _BV10C_OBSERVABILITY_READ_FACADE in joined

def test_bv10_read_cluster_direct_import_guard_non_owners_route_through_facades() -> None:
    """BV10C: non-owner modules must not import read-cluster authority modules directly."""
    violations: list[str] = []
    for rel in iter_bv10_read_cluster_direct_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV10C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv10_read_cluster_direct_import_guard_violations(rel, source))
    assert not violations, 'BV10C read-cluster direct-import violations:\n' + '\n'.join(violations)

def test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons() -> None:
    """BN1: every runtime gate-entry allowlist path documents why it may import gate entry."""
    for path, reason in BN1_RUNTIME_GATE_ENTRY_ALLOWLIST.items():
        assert path.startswith('game/'), path
        assert reason.strip(), f'empty BN1 allowlist reason for {path!r}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN1' in registry_doc

def test_bn1_runtime_gate_entry_guard_detects_synthetic_violation() -> None:
    """BN1: guard flags direct gate entry imports in non-owner game modules."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\n'
    rel = 'game/synthetic_bn1_violation.py'
    violations = collect_bn1_runtime_gate_entry_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'apply_final_emission_gate' in joined
    assert BN1_RUNTIME_GATE_ENTRY_REPLACEMENT in joined
    assert BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT in joined

def test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import() -> None:
    """BN1: non-owner game modules must not import apply_final_emission_gate from the gate owner."""
    violations: list[str] = []
    for rel in iter_bn1_runtime_gate_entry_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BN1 scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bn1_runtime_gate_entry_guard_violations(rel, source))
    assert not violations, 'BN1 runtime gate-entry import violations:\n' + '\n'.join(violations)

def test_bn1_runtime_delegate_seam_remains_narrow() -> None:
    """BN1: final_emission_runtime stays a thin delegate with no policy imports."""
    import game.final_emission_runtime as runtime
    runtime_src = Path(runtime.__file__).read_text(encoding='utf-8')
    assert 'def finalize_player_facing_emission' in runtime_src
    assert 'from game.final_emission_gate import apply_final_emission_gate' in runtime_src
    assert 'return apply_final_emission_gate(' in runtime_src
    forbidden_markers = ('from game.final_emission_meta import', 'from game.final_emission_replay_projection import', 'from game.output_sanitizer import', 'from game.final_emission_validators import')
    for marker in forbidden_markers:
        assert marker not in runtime_src, f'runtime seam must not import policy surface: {marker!r}'

def test_bn2_lazy_gate_namespace_allowlist_covers_scan_files() -> None:
    """BN2: retained-symbol map spans every lazy-namespace scan file."""
    assert BN2_LAZY_GATE_NAMESPACE_FILES == frozenset(BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN2' in registry_doc

def test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation() -> None:
    """BN2: guard flags stale lazy feg namespace markers."""
    synthetic = 'def _gate_module():\n    import game.final_emission_gate as feg\n    return feg\ndef run():\n    feg = _gate_module()\n    feg._apply_visibility_enforcement(out)\n'
    rel = 'game/final_emission_terminal_pipeline.py'
    violations = collect_bn2_lazy_gate_namespace_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'def _gate_module(' in joined
    assert 'import game.final_emission_gate' in joined
    assert '_apply_visibility_enforcement' in joined

def test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg() -> None:
    """BN2: non_strict_stack and terminal_pipeline must not lazy-import gate namespace."""
    violations: list[str] = []
    for rel in sorted(BN2_LAZY_GATE_NAMESPACE_FILES):
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BN2 scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bn2_lazy_gate_namespace_violations(rel, source))
    assert not violations, 'BN2 lazy gate namespace violations:\n' + '\n'.join(violations)

def test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked() -> None:
    """BN3: preflight layer-meta defaults live on dedicated helper owner."""
    import game.final_emission_gate_preflight_defaults as gpfd
    assert callable(getattr(gpfd, 'initialize_gate_preflight_layer_meta_defaults', None))
    assert callable(getattr(gpfd, 'GatePreflightLayerMetaDefaults', None))

def test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation() -> None:
    """BN3: guard flags regrown direct layer-meta owner imports on gate_context."""
    synthetic = 'from game.final_emission_tone_escalation import default_tone_escalation_meta\ndef initialize_gate_execution_context():\n    return default_tone_escalation_meta()\n'
    violations = collect_bn3_gate_context_layer_meta_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_tone_escalation' in joined
    assert 'preflight_defaults' in joined

def test_bn3_gate_context_avoids_direct_layer_meta_owner_imports() -> None:
    """BN3: gate_context routes layer-meta defaults through preflight_defaults helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN3 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn3_gate_context_layer_meta_import_violations(source)
    assert not violations, 'BN3 gate_context import violations:\n' + '\n'.join(violations)
    defaults_path = _REPO_ROOT / BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE
    assert defaults_path.is_file(), f'missing BN3 helper: {BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN3' in registry_doc

def test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked() -> None:
    """BN4: preflight telemetry/containment lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_telemetry as gpft
    assert callable(getattr(gpft, 'apply_gate_preflight_telemetry_and_containment', None))
    assert callable(getattr(gpft, 'GatePreflightTelemetryResult', None))

def test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation() -> None:
    """BN4: guard flags regrown direct telemetry/provenance imports on gate_context."""
    synthetic = "from game.stage_diff_telemetry import record_stage_snapshot\ndef initialize_gate_execution_context():\n    record_stage_snapshot(out, 'final_emission_gate_entry')\n"
    violations = collect_bn4_gate_context_telemetry_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'stage_diff_telemetry' in joined
    assert 'preflight_telemetry' in joined

def test_bn4_gate_context_avoids_direct_telemetry_provenance_imports() -> None:
    """BN4: gate_context routes telemetry/containment through preflight_telemetry helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN4 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn4_gate_context_telemetry_import_violations(source)
    assert not violations, 'BN4 gate_context import violations:\n' + '\n'.join(violations)
    telemetry_path = _REPO_ROOT / BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE
    assert telemetry_path.is_file(), f'missing BN4 helper: {BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}'
    telemetry_source = telemetry_path.read_text(encoding='utf-8')
    helper_violations = collect_bn4_preflight_telemetry_helper_gate_import_violations(telemetry_source)
    assert not helper_violations, 'BN4 telemetry helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN4' in registry_doc

def test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked() -> None:
    """BN5: preflight upstream attach lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_upstream as gpfu
    assert callable(getattr(gpfu, 'apply_gate_preflight_upstream_attach', None))
    assert callable(getattr(gpfu, 'upstream_prepared_emission_payload', None))

def test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation() -> None:
    """BN5: guard flags regrown direct upstream attach imports on gate_context."""
    synthetic = 'from game.upstream_response_repairs import merge_upstream_prepared_emission_into_gm_output\ndef initialize_gate_execution_context():\n    merge_upstream_prepared_emission_into_gm_output(out)\n'
    violations = collect_bn5_gate_context_upstream_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'upstream_response_repairs' in joined
    assert 'preflight_upstream' in joined

def test_bn5_gate_context_avoids_direct_upstream_attach_imports() -> None:
    """BN5: gate_context routes upstream attach through preflight_upstream helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN5 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn5_gate_context_upstream_import_violations(source)
    assert not violations, 'BN5 gate_context import violations:\n' + '\n'.join(violations)
    upstream_path = _REPO_ROOT / BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE
    assert upstream_path.is_file(), f'missing BN5 helper: {BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}'
    upstream_source = upstream_path.read_text(encoding='utf-8')
    helper_violations = collect_bn5_preflight_upstream_helper_gate_import_violations(upstream_source)
    assert not helper_violations, 'BN5 upstream helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN5' in registry_doc

def test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked() -> None:
    """BN6: preflight turn-packet/policy setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_turn_packet as gpfttp
    assert callable(getattr(gpfttp, 'initialize_gate_preflight_turn_packet', None))

def test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation() -> None:
    """BN6: guard flags regrown direct turn-packet/policy imports on gate_context."""
    synthetic = "from game.turn_packet import get_turn_packet\ndef initialize_gate_execution_context():\n    out['_gate_turn_packet_cache'] = get_turn_packet(out)\n"
    violations = collect_bn6_gate_context_turn_packet_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'turn_packet' in joined
    assert 'preflight_turn_packet' in joined

def test_bn6_gate_context_avoids_direct_turn_packet_policy_imports() -> None:
    """BN6: gate_context routes turn-packet/policy setup through preflight_turn_packet helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN6 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn6_gate_context_turn_packet_import_violations(source)
    assert not violations, 'BN6 gate_context import violations:\n' + '\n'.join(violations)
    turn_packet_path = _REPO_ROOT / BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE
    assert turn_packet_path.is_file(), f'missing BN6 helper: {BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}'
    turn_packet_source = turn_packet_path.read_text(encoding='utf-8')
    helper_violations = collect_bn6_preflight_turn_packet_helper_gate_import_violations(turn_packet_source)
    assert not helper_violations, 'BN6 turn-packet helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN6' in registry_doc

def test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked() -> None:
    """BN7: preflight interaction metadata lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_interaction as gpfi
    assert callable(getattr(gpfi, 'resolve_gate_preflight_interaction_metadata', None))
    assert callable(getattr(gpfi, 'GatePreflightInteractionMetadata', None))

def test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation() -> None:
    """BN7: guard flags regrown direct interaction inspection imports on gate_context."""
    synthetic = 'from game.interaction_context import inspect as inspect_interaction_context\ndef initialize_gate_execution_context():\n    return inspect_interaction_context(session)\n'
    violations = collect_bn7_gate_context_interaction_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'interaction_context' in joined
    assert 'preflight_interaction' in joined

def test_bn7_gate_context_avoids_direct_interaction_inspection_imports() -> None:
    """BN7: gate_context routes interaction metadata through preflight_interaction helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN7 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn7_gate_context_interaction_import_violations(source)
    assert not violations, 'BN7 gate_context import violations:\n' + '\n'.join(violations)
    interaction_path = _REPO_ROOT / BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE
    assert interaction_path.is_file(), f'missing BN7 helper: {BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}'
    interaction_source = interaction_path.read_text(encoding='utf-8')
    helper_violations = collect_bn7_preflight_interaction_helper_gate_import_violations(interaction_source)
    assert not helper_violations, 'BN7 interaction helper gate import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN7' in registry_doc

def test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked() -> None:
    """BN8: preflight strict-social routing lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_strict_social as gpfs
    assert callable(getattr(gpfs, 'resolve_gate_preflight_strict_social_routing', None))
    assert callable(getattr(gpfs, 'GatePreflightStrictSocialRouting', None))

def test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation() -> None:
    """BN8: guard flags regrown direct strict-social routing imports on gate_context."""
    synthetic = "from game.social_exchange_emission import strict_social_emission_will_apply\ndef initialize_gate_execution_context():\n    return strict_social_emission_will_apply(None, None, None, '')\n"
    violations = collect_bn8_gate_context_strict_social_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'social_exchange_emission' in joined
    assert 'preflight_strict_social' in joined

def test_bn8_gate_context_avoids_direct_strict_social_routing_imports() -> None:
    """BN8: gate_context routes strict-social setup through preflight_strict_social helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN8 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn8_gate_context_strict_social_import_violations(source)
    assert not violations, 'BN8 gate_context import violations:\n' + '\n'.join(violations)
    strict_social_path = _REPO_ROOT / BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE
    assert strict_social_path.is_file(), f'missing BN8 helper: {BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE}'
    strict_social_source = strict_social_path.read_text(encoding='utf-8')
    helper_violations = collect_bn8_preflight_strict_social_helper_import_violations(strict_social_source)
    assert not helper_violations, 'BN8 strict-social helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN8' in registry_doc

def test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked() -> None:
    """BN9: preflight pregate text/tag setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_pregate_text as gpfpt
    assert callable(getattr(gpfpt, 'resolve_gate_preflight_pregate_text', None))
    assert callable(getattr(gpfpt, 'GatePreflightPregateText', None))

def test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation() -> None:
    """BN9: guard flags regrown direct pregate text imports on gate_context."""
    synthetic = "from game.final_emission_text_formatting import _normalize_text\ndef initialize_gate_execution_context():\n    return _normalize_text(out.get('player_facing_text'))\n"
    violations = collect_bn9_gate_context_pregate_text_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_text_formatting' in joined
    assert 'preflight_pregate_text' in joined

def test_bn9_gate_context_avoids_direct_pregate_text_imports() -> None:
    """BN9: gate_context routes pregate text/tag setup through preflight_pregate_text helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN9 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn9_gate_context_pregate_text_import_violations(source)
    assert not violations, 'BN9 gate_context import violations:\n' + '\n'.join(violations)
    pregate_text_path = _REPO_ROOT / BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE
    assert pregate_text_path.is_file(), f'missing BN9 helper: {BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE}'
    pregate_text_source = pregate_text_path.read_text(encoding='utf-8')
    helper_violations = collect_bn9_preflight_pregate_text_helper_import_violations(pregate_text_source)
    assert not helper_violations, 'BN9 pregate text helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN9' in registry_doc

def test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked() -> None:
    """BN10: preflight branch-flag derivation lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_branch_flags as gpfb
    assert callable(getattr(gpfb, 'resolve_gate_preflight_branch_flags', None))
    assert callable(getattr(gpfb, 'GatePreflightBranchFlags', None))

def test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation() -> None:
    """BN10: guard flags inline branch-flag derivation regrown on gate_context."""
    synthetic = "def initialize_gate_execution_context():\n    retry_output = any('question_retry_fallback' in t for t in tag_list)\n"
    violations = collect_bn10_gate_context_branch_flags_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'question_retry_fallback' in joined
    assert 'preflight_branch_flags' in joined

def test_bn10_gate_context_routes_branch_flags_through_helper() -> None:
    """BN10: gate_context routes branch flags through preflight_branch_flags helper."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN10 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn10_gate_context_branch_flags_violations(source)
    assert not violations, 'BN10 gate_context branch-flag violations:\n' + '\n'.join(violations)
    branch_flags_path = _REPO_ROOT / BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE
    assert branch_flags_path.is_file(), f'missing BN10 helper: {BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE}'
    branch_flags_source = branch_flags_path.read_text(encoding='utf-8')
    helper_violations = collect_bn10_preflight_branch_flags_helper_import_violations(branch_flags_source)
    assert not helper_violations, 'BN10 branch-flags helper import violations:\n' + '\n'.join(helper_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN10' in registry_doc

def test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation() -> None:
    """BN11: guard flags non-preflight game imports on gate_context."""
    synthetic = 'from game.final_emission_gate import apply_final_emission_gate\nfrom game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults\ndef initialize_gate_execution_context():\n    return apply_final_emission_gate({})\n'
    violations = collect_bn11_gate_context_preflight_only_import_violations(synthetic)
    joined = '\n'.join(violations)
    assert violations
    assert 'final_emission_gate' in joined
    assert 'preflight' in joined

def test_bn11_gate_context_preflight_only_import_allowlist_locked() -> None:
    """BN11: live gate_context imports only stdlib/typing and preflight helper owners."""
    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f'missing BN11 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}'
    source = path.read_text(encoding='utf-8')
    violations = collect_bn11_gate_context_preflight_only_import_violations(source)
    assert not violations, 'BN11 gate_context preflight-only import violations:\n' + '\n'.join(violations)
    imported_game = {mod for mod in gate_context_import_modules(source) if mod.startswith('game.')}
    assert imported_game == BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES, f'BN11 gate_context game import set mismatch:\n  imported: {sorted(imported_game)!r}\n  allowed:  {sorted(BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)!r}'
    for required in BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS:
        assert required in source, f'missing BN11 required preflight import: {required!r}'
    lock_path = _REPO_ROOT / 'tests/ownership_guard_bn_gate_context.py'
    lock_source = lock_path.read_text(encoding='utf-8')
    scan_violations = collect_bn11_scan_logic_runtime_gate_import_violations(lock_source)
    assert not scan_violations, 'BN11 scan-logic runtime gate import violations:\n' + '\n'.join(scan_violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BN11' in registry_doc

def test_ad3_gate_orchestration_direct_owner_is_final_emission_gate() -> None:
    """Cycle AD-3: gate orchestration normative owner stays on the gate module."""
    rec = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    assert rec.direct_owner.replace('\\', '/') == 'tests/test_final_emission_gate.py'

def test_ad3_downstream_integration_smoke_suites_registered_as_neighbors() -> None:
    """Cycle AD-3: AD-thinned suites are downstream neighbors, never direct owners."""
    gate = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    sanitizer = RESPONSIBILITY_REGISTRY['output_sanitizer_final_string_cleanup']
    visibility = RESPONSIBILITY_REGISTRY['final_emission_visibility_semantics']
    social = RESPONSIBILITY_REGISTRY['social_emission_legality_surface']
    gate_downstream = frozenset((p.replace('\\', '/') for p in gate.downstream_consumer_suites))
    assert DOWNSTREAM_INTEGRATION_SMOKE_ONLY.issubset(gate_downstream)
    turn_pipeline = 'tests/test_turn_pipeline_shared.py'
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in frozenset((p.replace('\\', '/') for p in sanitizer.downstream_consumer_suites))
    assert turn_pipeline in frozenset((p.replace('\\', '/') for p in visibility.downstream_consumer_suites))
    ac_rd = frozenset({'tests/test_answer_completeness_rules.py', 'tests/test_response_delta_requirement.py'})
    assert ac_rd.issubset(gate_downstream)
    assert ac_rd.issubset(frozenset((p.replace('\\', '/') for p in social.downstream_consumer_suites)))
    for gid, rec in RESPONSIBILITY_REGISTRY.items():
        owner = rec.direct_owner.replace('\\', '/')
        assert owner not in DOWNSTREAM_INTEGRATION_SMOKE_ONLY, f'{gid} must not list {owner!r} as direct_owner (downstream integration smoke only).'

def test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner() -> None:
    """Cycle AD-3: replay observation locks live under gauntlet neighbor, not gate orchestration."""
    gate = RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration']
    gauntlet = RESPONSIBILITY_REGISTRY['gauntlet_playability_validation']
    golden = 'tests/test_golden_replay.py'
    assert golden in frozenset((p.replace('\\', '/') for p in gauntlet.gauntlet_suites))
    assert gauntlet.direct_owner.replace('\\', '/') != gate.direct_owner.replace('\\', '/')
    assert golden not in frozenset((p.replace('\\', '/') for p in gate.downstream_consumer_suites))

def test_bi8_golden_replay_ownership_boundary_is_locked() -> None:
    """Cycle BI-8: replay remains an orchestration/observation bridge, not a subsystem owner."""
    target_sources = load_bi8_golden_replay_target_sources(_REPO_ROOT)
    combined_docs = '\n'.join(list(target_sources.values()))
    doc_violations = collect_bi8_golden_replay_documentation_phrase_violations(combined_docs)
    assert not doc_violations, '\n'.join(doc_violations)
    api_exports = parse_bi8_golden_replay_api_exports(target_sources)
    assert BI8_GOLDEN_REPLAY_OWNED_EXPORTS <= api_exports
    export_violations = collect_bi8_golden_replay_forbidden_export_violations(api_exports)
    assert not export_violations, '\n'.join(export_violations)
    helper_api_source = '\n'.join((target_sources['tests/helpers/golden_replay.py'], target_sources['tests/helpers/golden_replay_api.py']))
    fragment_violations = collect_bi8_golden_replay_forbidden_source_fragment_violations(helper_api_source)
    assert not fragment_violations, '\n'.join(fragment_violations)

def test_bg1_protected_replay_manifest_registry_parity() -> None:
    """Cycle BG-1: manifest generation stays registry-backed and parity-checked."""
    import importlib.util
    import tests.helpers.golden_replay_projection as acceptance_projection
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('refresh_protected_replay_manifest', root / 'tools' / 'refresh_protected_replay_manifest.py')
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)
    manifest_text = refresh_mod.MANIFEST_PATH.read_text(encoding='utf-8')
    assert acceptance_projection.protected_observation_manifest_registry_parity_errors(manifest_text) == []
    assert acceptance_projection.protected_observation_manifest_section_is_current(manifest_text)
    registry_paths = {field.path for field in acceptance_projection.protected_observation_field_registry()}
    assert registry_paths == set(acceptance_projection.protected_observation_field_paths())
    assert tuple((path for path, _bucket in acceptance_projection.protected_observation_manifest_field_rows())) == acceptance_projection.protected_observation_field_paths()
    registry_buckets = {field.path: field.drift_bucket for field in acceptance_projection.protected_observation_field_registry()}
    manifest_buckets = dict(acceptance_projection.protected_observation_manifest_field_rows())
    assert manifest_buckets == {path: acceptance_projection.protected_observation_drift_bucket(path) for path in acceptance_projection.protected_observation_field_paths()}
    for path, bucket in registry_buckets.items():
        assert acceptance_projection.protected_observation_drift_bucket(path) == bucket

def test_ao5_runtime_and_acceptance_projection_modules_remain_separate() -> None:
    """Cycle AO5: runtime lineage projection and acceptance observation projection stay split."""
    import game.final_emission_replay_projection as runtime_projection
    import tests.helpers.golden_replay_projection as acceptance_projection
    runtime_doc = (runtime_projection.__doc__ or '').lower()
    acceptance_doc = (acceptance_projection.__doc__ or '').lower()
    assert 'do not merge' in runtime_doc
    assert 'do not merge' in acceptance_doc
    assert 'golden_replay_projection' in runtime_doc
    assert 'final_emission_replay_projection' in acceptance_doc
    assert runtime_projection.__name__ == 'game.final_emission_replay_projection'
    assert acceptance_projection.__name__ == 'tests.helpers.golden_replay_projection'
    lineage_surface = runtime_projection.read_side_lineage_projection_surface()
    assert lineage_surface['mutation_lineage_key'] == 'final_emission_mutation_lineage'
    assert len(acceptance_projection.protected_observation_field_registry()) == len(acceptance_projection.protected_observation_field_paths())
    meta_proj = RESPONSIBILITY_REGISTRY['final_emission_meta_projection']
    gauntlet = RESPONSIBILITY_REGISTRY['gauntlet_playability_validation']
    assert 'tests/test_golden_replay.py' in frozenset((p.replace('\\', '/') for p in gauntlet.gauntlet_suites))
    assert meta_proj.direct_owner.replace('\\', '/') == 'tests/test_final_emission_meta.py'
    assert 'game.final_emission_replay_projection' not in frozenset((p.replace('\\', '/') for p in meta_proj.downstream_consumer_suites))

def test_al4_legality_owners_and_smoke_facade_locked() -> None:
    """Cycle AL4: AL1–AL3 convergence boundaries stay aligned with registry direct owners."""
    assert RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration'].direct_owner.replace('\\', '/') == _AL4_LEGALITY_OWNER_PATHS['final_emission_gate']
    assert RESPONSIBILITY_REGISTRY['final_emission_meta_projection'].direct_owner.replace('\\', '/') == _AL4_LEGALITY_OWNER_PATHS['final_emission_meta']
    assert RESPONSIBILITY_REGISTRY['output_sanitizer_final_string_cleanup'].direct_owner.replace('\\', '/') == _AL4_LEGALITY_OWNER_PATHS['output_sanitizer']
    assert RESPONSIBILITY_REGISTRY['social_emission_legality_surface'].direct_owner.replace('\\', '/') == _AL4_LEGALITY_OWNER_PATHS['social_exchange_emission']
    turn_pipeline = _AL4_LEGALITY_OWNER_PATHS['turn_pipeline_http_smoke']
    gate_downstream = frozenset((p.replace('\\', '/') for p in RESPONSIBILITY_REGISTRY['final_emission_gate_orchestration'].downstream_consumer_suites))
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in DOWNSTREAM_INTEGRATION_SMOKE_ONLY
    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    assert facade_path.is_file(), f'missing downstream smoke facade: {_DOWNSTREAM_SMOKE_FACADE}'
    route_owner = (_REPO_ROOT / _AL4_LEGALITY_OWNER_PATHS['dialogue_route_classification']).resolve()
    assert route_owner.is_file(), 'dialogue route legality owner must remain tests/test_dialogue_routing_lock.py'

def test_bj4_emission_smoke_facade_stays_weak_consumer_bridge() -> None:
    """Cycle BJ-4 / BV7A / BV7B: smoke facade stays weak; bridges live in dedicated modules."""
    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    source = facade_path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    public_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef) and (not node.name.startswith('_'))}
    bv7b_extracted_repair = _BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES & (_BV7B_EXTRACTED_AC_SYMBOLS | _BV7B_EXTRACTED_RD_SYMBOLS)
    for expected_bridge in _BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES - bv7b_extracted_repair:
        assert expected_bridge in public_functions
    for expected_bridge in _BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES - _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS - _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS - _BV7B_EXTRACTED_RT_SYMBOLS:
        assert expected_bridge in public_functions
    gate_bridge_path = (_REPO_ROOT / _BD6_GATE_BRIDGE_FACADE).resolve()
    replay_bridge_path = (_REPO_ROOT / _BD6_REPLAY_BRIDGE_FACADE).resolve()
    replay_fem_path = (_REPO_ROOT / _BV12A_REPLAY_FEM_READ_FACADE).resolve()
    gate_orch_path = (_REPO_ROOT / _BV12A_GATE_ORCHESTRATION_FACADE).resolve()
    fallback_bridge_path = (_REPO_ROOT / _BV12A_FALLBACK_BRIDGE_FACADE).resolve()
    rt_bridge_path = (_REPO_ROOT / _BD6_RT_SMOKE_FACADE).resolve()
    ac_bridge_path = (_REPO_ROOT / _BD6_AC_SMOKE_FACADE).resolve()
    rd_bridge_path = (_REPO_ROOT / _BD6_RD_SMOKE_FACADE).resolve()
    assert gate_bridge_path.is_file(), f'missing BV7A gate bridge: {_BD6_GATE_BRIDGE_FACADE}'
    assert replay_bridge_path.is_file(), f'missing BV7A replay bridge: {_BD6_REPLAY_BRIDGE_FACADE}'
    assert replay_fem_path.is_file(), f'missing BV12A replay FEM facade: {_BV12A_REPLAY_FEM_READ_FACADE}'
    assert gate_orch_path.is_file(), f'missing BV12A gate orchestration facade: {_BV12A_GATE_ORCHESTRATION_FACADE}'
    assert fallback_bridge_path.is_file(), f'missing BV12A fallback bridge: {_BV12A_FALLBACK_BRIDGE_FACADE}'
    assert rt_bridge_path.is_file(), f'missing BV7B RT bridge: {_BD6_RT_SMOKE_FACADE}'
    assert ac_bridge_path.is_file(), f'missing BV7B AC bridge: {_BD6_AC_SMOKE_FACADE}'
    assert rd_bridge_path.is_file(), f'missing BV7B RD bridge: {_BD6_RD_SMOKE_FACADE}'

    def _public_functions(module_path: Path) -> set[str]:
        module_tree = ast.parse(module_path.read_text(encoding='utf-8'))
        return {node.name for node in module_tree.body if isinstance(node, ast.FunctionDef) and (not node.name.startswith('_'))}

    def _module_all_exports(module_path: Path) -> set[str]:
        module_tree = ast.parse(module_path.read_text(encoding='utf-8'))
        for node in module_tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == '__all__' and isinstance(node.value, (ast.List, ast.Tuple)):
                    return {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
        return set()
    gate_functions = _public_functions(gate_orch_path)
    replay_functions = _public_functions(replay_fem_path)
    gate_compat_exports = _module_all_exports(gate_bridge_path)
    replay_compat_exports = _module_all_exports(replay_bridge_path)
    rt_functions = _public_functions(rt_bridge_path)
    ac_functions = _public_functions(ac_bridge_path)
    rd_functions = _public_functions(rd_bridge_path)
    for expected_gate in _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS:
        assert expected_gate in gate_functions, f'expected gate bridge {expected_gate!r} in {_BV12A_GATE_ORCHESTRATION_FACADE}'
        assert expected_gate in gate_compat_exports, f'expected gate compat re-export {expected_gate!r} in {_BD6_GATE_BRIDGE_FACADE}'
    for expected_replay in _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS:
        assert expected_replay in replay_functions, f'expected replay bridge {expected_replay!r} in {_BV12A_REPLAY_FEM_READ_FACADE}'
        assert expected_replay in replay_compat_exports, f'expected replay compat re-export {expected_replay!r} in {_BD6_REPLAY_BRIDGE_FACADE}'
    for expected_rt in _BV7B_EXTRACTED_RT_SYMBOLS:
        assert expected_rt in rt_functions, f'expected RT bridge {expected_rt!r} in {_BD6_RT_SMOKE_FACADE}'
    for expected_ac in _BV7B_EXTRACTED_AC_SYMBOLS:
        assert expected_ac in ac_functions, f'expected AC bridge {expected_ac!r} in {_BD6_AC_SMOKE_FACADE}'
    for expected_rd in _BV7B_EXTRACTED_RD_SYMBOLS:
        assert expected_rd in rd_functions, f'expected RD bridge {expected_rd!r} in {_BD6_RD_SMOKE_FACADE}'
    facade_all = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == '__all__' and isinstance(node.value, (ast.List, ast.Tuple)):
                facade_all = {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
    bv7_extracted = _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS | _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS | _BV7B_EXTRACTED_RT_SYMBOLS | _BV7B_EXTRACTED_AC_SYMBOLS | _BV7B_EXTRACTED_RD_SYMBOLS
    for expected_bridge in bv7_extracted:
        assert expected_bridge in facade_all, f'compatibility facade must re-export {expected_bridge!r} via __all__'
    public_names = set(public_functions)
    public_table_lengths: dict[str, int] = {}
    for node in tree.body:
        target_name: str | None = None
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        if not target_name or target_name.startswith('_'):
            continue
        public_names.add(target_name)
        if target_name.isupper() and isinstance(value, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            public_table_lengths[target_name] = len(value.keys if isinstance(value, ast.Dict) else value.elts)
    forbidden_public_names = {name: reason for name in public_names for fragment, reason in _BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS.items() if fragment in name.lower()}
    assert not forbidden_public_names, f'emission_smoke_assertions.py must not grow public legality-owner helpers/constants: {forbidden_public_names!r}'
    oversized_public_tables = {name: size for name, size in public_table_lengths.items() if size > 8}
    assert not oversized_public_tables, f'emission_smoke_assertions.py must not grow large public phrase/route/repair tables; move legality matrices to owner suites: {oversized_public_tables!r}'
    low = source.lower()
    assert 'ownership note' in low
    assert 'weak downstream smoke/consumer bridges' in low
    assert 'must not become the owner' in low
    assert 'full gate legality matrices' in low
    assert 'route enum tables' in low
    assert 'sanitizer phrase legality' in low
    assert 'ac/rd repair semantics' in low

def test_be6_scaffold_phrase_triple_layer_split_locked() -> None:
    """Cycle BE6: sanitizer legality, HTTP smoke phrases, and replay scaffold projection stay separate."""
    for label, rel_path in _BE6_SCAFFOLD_PHRASE_LAYER_OWNERS.items():
        path = (_REPO_ROOT / rel_path).resolve()
        assert path.is_file(), f'BE6 layer {label!r} missing owner path: {rel_path}'
    smoke_doc = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).read_text(encoding='utf-8')
    assert 'BE6' in smoke_doc, 'emission_smoke_assertions must document Cycle BE6 triple-layer split'
    assert 'do not merge' in smoke_doc.lower(), 'emission_smoke_assertions must warn against merging phrase matrices'
    assert 'tests/test_output_sanitizer.py' in smoke_doc
    assert 'golden_replay_projection' in smoke_doc
    assert 'final_text_has_scaffold_leakage' in smoke_doc
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BE6' in registry_doc, 'ownership registry must document Cycle BE6 triple-layer split'
    assert 'do not merge' in registry_doc.lower()

def test_bv7c_smoke_monolith_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV7C: every monolith import-guard allowlist path documents why it may import extracted symbols."""
    for path, reason in _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST.items():
        assert path.startswith('tests/'), path
        assert reason.strip(), f'empty BV7C allowlist reason for {path!r}'

def test_bv7c_smoke_monolith_import_guard_detects_synthetic_violation() -> None:
    """BV7C: guard flags representative extracted-symbol imports with facade guidance."""
    synthetic = 'from tests.helpers.emission_smoke_assertions import response_type_contract\nfrom tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer\nfrom tests.helpers.emission_smoke_assertions import final_emission_meta_from_output\nfrom tests.helpers.emission_smoke_assertions import validate_answer_completeness\nfrom tests.helpers.emission_smoke_assertions import apply_response_delta_layer\n'
    rel = 'tests/test_synthetic_bv7c_violation.py'
    violations = collect_bv7c_smoke_monolith_import_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert any(('response_type_contract' in v for v in violations))
    assert any(('apply_final_emission_gate_consumer' in v for v in violations))
    assert any(('final_emission_meta_from_output' in v for v in violations))
    assert any(('validate_answer_completeness' in v for v in violations))
    assert any(('apply_response_delta_layer' in v for v in violations))
    assert _BD6_RT_SMOKE_FACADE in joined
    assert _BV12A_GATE_ORCHESTRATION_FACADE in joined
    assert _BV12A_REPLAY_FEM_READ_FACADE in joined
    assert _BD6_AC_SMOKE_FACADE in joined
    assert _BD6_RD_SMOKE_FACADE in joined

def test_bv7c_smoke_monolith_import_guard_non_owners_route_through_family_facades() -> None:
    """BV7C: non-barrel modules must not reimport BV7A/BV7B extracted symbols from monolith."""
    violations: list[str] = []
    for rel in iter_bv7c_smoke_monolith_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV7C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv7c_smoke_monolith_import_guard_violations(rel, source))
    assert not violations, 'BV7C smoke monolith import-guard violations:\n' + '\n'.join(violations)

def test_bv7c_emission_smoke_assertions_concentration_locked() -> None:
    """BV7C: monolith FI stays within smoke-core band; no new static importers without registry update."""
    source_by_rel: dict[str, str] = {}
    for rel in iter_bv7c_smoke_monolith_import_guard_scan_paths():
        source_by_rel[rel] = (_REPO_ROOT / rel).read_text(encoding='utf-8')
    static_importers = collect_bv7c_monolith_static_importers(source_by_rel)
    assert len(static_importers) <= _BV7C_MONOLITH_FI_CAP, f'emission_smoke_assertions static importer count {len(static_importers)} exceeds BV7C cap {_BV7C_MONOLITH_FI_CAP}: {sorted(static_importers - _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS)!r}'
    unexpected = static_importers - _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS
    assert not unexpected, f'new static emission_smoke_assertions importers require BV7C registry update: {sorted(unexpected)!r}'
    missing = _BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS - static_importers
    assert not missing, f'BV7C allowed importer registry drift — remove stale entries or restore imports: {sorted(missing)!r}'
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV7C' in registry_doc

def test_bv12c_compat_barrel_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV12C: every compat-barrel import-guard allowlist path documents why it may import compat barrels."""
    for path, reason in _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST.items():
        assert path.startswith(('tests/', 'tools/', 'scripts/')), path
        assert reason.strip(), f'empty BV12C allowlist reason for {path!r}'

def test_bv12c_compat_barrel_import_guard_detects_synthetic_violation() -> None:
    """BV12C: guard flags compat-barrel imports with domain-facade guidance."""
    synthetic = 'import tests.helpers.replay_smoke_assertions as replay_smoke_assertions\nimport tests.helpers.gate_integration_smoke as gate_integration_smoke\nfrom tests.helpers.replay_smoke_assertions import final_emission_meta_from_output\nfrom tests.helpers.gate_integration_smoke import apply_final_emission_gate_consumer\n'
    rel = 'tests/test_synthetic_bv12c_violation.py'
    violations = collect_bv12c_compat_barrel_import_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert _BV12C_REPLAY_COMPAT_MODULE in joined
    assert _BV12C_GATE_COMPAT_MODULE in joined
    assert _BV12A_REPLAY_FEM_READ_FACADE in joined
    assert _BV12A_GATE_ORCHESTRATION_FACADE in joined
    assert len(violations) >= 2

def test_bv12c_compat_barrel_import_guard_non_owners_route_through_domain_facades() -> None:
    """BV12C: non-barrel modules must not import compat smoke bridge barrels directly."""
    violations: list[str] = []
    for rel in iter_bv12c_compat_barrel_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV12C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv12c_compat_barrel_import_guard_violations(rel, source))
    assert not violations, 'BV12C compat-barrel import-guard violations:\n' + '\n'.join(violations)

def test_bv12c_compat_barrel_fi_cap_locked() -> None:
    """BV12C: compat barrel FI stays at delegate-verification residual; domain hubs documented separately."""
    replay_importers = collect_bv12c_compat_barrel_static_importers(compat_module=_BV12C_REPLAY_COMPAT_MODULE)
    gate_importers = collect_bv12c_compat_barrel_static_importers(compat_module=_BV12C_GATE_COMPAT_MODULE)
    assert len(replay_importers) <= _BV12C_COMPAT_BARREL_FI_CAP, f'replay_smoke_assertions static importer count {len(replay_importers)} exceeds BV12C cap {_BV12C_COMPAT_BARREL_FI_CAP}: {sorted(replay_importers - _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS)!r}'
    assert len(gate_importers) <= _BV12C_COMPAT_BARREL_FI_CAP, f'gate_integration_smoke static importer count {len(gate_importers)} exceeds BV12C cap {_BV12C_COMPAT_BARREL_FI_CAP}: {sorted(gate_importers - _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS)!r}'
    unexpected_replay = replay_importers - _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS
    unexpected_gate = gate_importers - _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS
    assert not unexpected_replay, f'new replay_smoke_assertions importers require BV12C registry update: {sorted(unexpected_replay)!r}'
    assert not unexpected_gate, f'new gate_integration_smoke importers require BV12C registry update: {sorted(unexpected_gate)!r}'
    assert replay_importers == _BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS
    assert gate_importers == _BV12C_ALLOWED_GATE_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV12C' in registry_doc
    for hub, role in _BV12C_INTENTIONAL_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty domain hub role for {hub!r}'

def test_bv13c_text_compat_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV13C: every text compat-barrel import-guard allowlist path documents why it may import compat."""
    for path, reason in _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST.items():
        assert path.startswith(('game/', 'tests/', 'tools/', 'scripts/')), path
        assert reason.strip(), f'empty BV13C allowlist reason for {path!r}'

def test_bv13c_text_compat_import_guard_detects_synthetic_violation() -> None:
    """BV13C: guard flags compat-barrel imports with formatting/policy authority guidance."""
    synthetic = 'from game.final_emission_text import _normalize_text\nimport game.final_emission_text as emission_text\n'
    rel = 'tests/test_synthetic_bv13c_violation.py'
    violations = collect_bv13c_text_compat_import_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert _BV13C_TEXT_COMPAT_MODULE in joined
    assert _BV13C_TEXT_FORMATTING_AUTHORITY in joined
    assert _BV13C_TEXT_POLICY_AUTHORITY in joined
    assert len(violations) >= 1

def test_bv13c_text_compat_import_guard_non_owners_route_through_authorities() -> None:
    """BV13C: non-barrel modules must not import final_emission_text compat barrel directly."""
    violations: list[str] = []
    for rel in iter_bv13c_text_compat_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV13C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv13c_text_compat_import_guard_violations(rel, source))
    assert not violations, 'BV13C text compat-barrel import-guard violations:\n' + '\n'.join(violations)

def test_bv13c_text_compat_fi_cap_locked() -> None:
    """BV13C: text compat barrel FI stays at fallback-wrapper residual; domain hubs documented separately."""
    importers = collect_bv13c_text_compat_static_importers()
    assert len(importers) <= _BV13C_TEXT_COMPAT_FI_CAP, f'final_emission_text static importer count {len(importers)} exceeds BV13C cap {_BV13C_TEXT_COMPAT_FI_CAP}: {sorted(importers - _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS)!r}'
    unexpected = importers - _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS
    assert not unexpected, f'new final_emission_text importers require BV13C registry update: {sorted(unexpected)!r}'
    assert importers == _BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV13C' in registry_doc
    for hub, role in _BV13C_INTENTIONAL_TEXT_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional text domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty text domain hub role for {hub!r}'

def test_bv14c_social_exchange_compat_import_guard_allowlist_entries_have_non_empty_reasons() -> None:
    """BV14C: every social-exchange compat-barrel import-guard allowlist path documents why it may import compat."""
    for path, reason in _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST.items():
        assert path.startswith(('game/', 'tests/', 'tools/', 'scripts/')), path
        assert reason.strip(), f'empty BV14C allowlist reason for {path!r}'

def test_bv14c_social_exchange_compat_import_guard_detects_synthetic_violation() -> None:
    """BV14C: guard flags compat-barrel imports with fallback/policy/validation/projection authority guidance."""
    synthetic = 'from game.social_exchange_emission import strict_social_emission_will_apply\nimport game.social_exchange_emission as social_exchange_emission\n'
    rel = 'tests/test_synthetic_bv14c_violation.py'
    violations = collect_bv14c_social_exchange_compat_import_guard_violations(rel, synthetic)
    joined = '\n'.join(violations)
    assert _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE in joined
    assert _BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY in joined
    assert _BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY in joined
    assert _BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY in joined
    assert _BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY in joined
    assert len(violations) >= 1

def test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities() -> None:
    """BV14C: non-barrel modules must not import social_exchange_emission compat barrel directly."""
    violations: list[str] = []
    for rel in iter_bv14c_social_exchange_compat_import_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f'missing BV14C scan path: {rel}'
        source = path.read_text(encoding='utf-8')
        violations.extend(collect_bv14c_social_exchange_compat_import_guard_violations(rel, source))
    assert not violations, 'BV14C social-exchange compat-barrel import-guard violations:\n' + '\n'.join(violations)

def test_bv14c_social_exchange_compat_fi_cap_locked() -> None:
    """BV14C: social-exchange compat barrel FI stays at composition-authority residual; domain hubs documented separately."""
    importers = collect_bv14c_social_exchange_compat_static_importers()
    assert len(importers) <= _BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP, f'social_exchange_emission static importer count {len(importers)} exceeds BV14C cap {_BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP}: {sorted(importers - _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS)!r}'
    unexpected = importers - _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS
    assert not unexpected, f'new social_exchange_emission importers require BV14C registry update: {sorted(unexpected)!r}'
    assert importers == _BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV14C' in registry_doc
    for hub, role in _BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS.items():
        assert hub in registry_doc, f'intentional social-exchange domain hub {hub!r} must be documented in registry'
        assert role.strip(), f'empty social-exchange domain hub role for {hub!r}'

def test_bj27_referential_clarity_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-27/BJ-50: referential-clarity orchestration lives on visibility fallback owner."""
    import game.final_emission_visibility_fallback as visibility_fallback
    assert callable(getattr(visibility_fallback, 'apply_referential_clarity_enforcement', None))

def test_bj50_visibility_enforcement_gate_wrapper_collapsed() -> None:
    """Cycle BJ-50/BJ-73: visibility enforcement lives on final_emission_visibility_fallback owner."""
    from tests.helpers.gate_delegator_governance import SEALED_FALLBACK, VISIBILITY_FALLBACK, assert_gate_lacks, assert_owner_callable, load_game_module
    assert_gate_lacks('_apply_visibility_enforcement')
    assert_gate_lacks('_standard_visibility_safe_fallback')
    assert_gate_lacks('_apply_first_mention_enforcement')
    assert_gate_lacks('_apply_referential_clarity_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_visibility_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_first_mention_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'apply_referential_clarity_enforcement')
    assert_owner_callable(VISIBILITY_FALLBACK, 'standard_visibility_safe_fallback')
    assert_owner_callable(SEALED_FALLBACK, 'select_visibility_safe_fallback')
    assert load_game_module(SEALED_FALLBACK).select_visibility_safe_fallback.__module__ == 'game.final_emission_sealed_fallback'

def test_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """Cycle BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    verify_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly()

def test_bj28_speaker_contract_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-28/BJ-77/BJ-78: speaker-contract orchestration lives on speaker_contract_enforcement owner."""
    import game.final_emission_gate as feg
    import game.speaker_contract_enforcement as sce
    assert callable(getattr(sce, 'enforce_emitted_speaker_with_contract', None))
    assert callable(getattr(sce, '_sync_eff_social_to_resolution', None))
    assert not hasattr(feg, 'enforce_emitted_speaker_with_contract')
    assert not hasattr(feg, '_sync_eff_social_to_resolution')
    assert feg.get_speaker_selection_contract is sce.get_speaker_selection_contract

def test_bj29_interaction_continuity_emission_owner_entrypoint_locked() -> None:
    """Cycle BJ-29/BJ-51/BJ-75/BJ-76: interaction-continuity orchestration lives on interaction_continuity owner."""
    import game.final_emission_gate as feg
    import game.interaction_continuity as ic
    assert callable(getattr(ic, 'apply_interaction_continuity_emission_step', None))
    assert callable(getattr(ic, 'attach_interaction_continuity_validation', None))
    assert not hasattr(feg, '_apply_interaction_continuity_emission_step')
    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation

def test_bj51_interaction_continuity_gate_wrappers_fully_collapsed() -> None:
    """Cycle BJ-51/BJ-75/BJ-76: all IC gate delegators removed; owners called from stack modules."""
    import game.final_emission_gate as feg
    import game.interaction_continuity as ic
    assert not hasattr(feg, '_apply_interaction_continuity_emission_step')
    assert not hasattr(feg, '_attach_interaction_continuity_validation')
    assert callable(getattr(ic, 'apply_interaction_continuity_emission_step', None))
    assert callable(getattr(ic, 'attach_interaction_continuity_validation', None))

def test_bj52_fallback_provenance_gate_wrappers_collapsed() -> None:
    """Cycle BJ-52/BN4: upstream fallback provenance containment wrappers removed from gate."""
    import game.fallback_provenance_debug as fpd
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_gate_context as gc
    import game.final_emission_gate_preflight_telemetry as gpft
    assert not hasattr(feg, '_upstream_fallback_canonical_provenance')
    assert not hasattr(feg, '_apply_upstream_fallback_pregate_containment')
    assert not hasattr(feg, '_finalize_upstream_fallback_overwrite_containment')
    assert callable(getattr(fpd, 'upstream_fallback_canonical_provenance', None))
    assert callable(getattr(fpd, 'apply_upstream_fallback_pregate_containment', None))
    assert callable(getattr(fpd, 'finalize_upstream_fallback_overwrite_containment', None))
    assert not hasattr(gc, 'apply_upstream_fallback_pregate_containment')
    assert callable(getattr(gpft, 'apply_gate_preflight_telemetry_and_containment', None))
    assert callable(getattr(fin, 'finalize_upstream_fallback_overwrite_containment', None))

def test_bj53_referent_clarity_pre_finalize_gate_wrapper_collapsed() -> None:
    """Cycle BJ-53: referent pre-finalize wrapper removed from gate; terminal pipeline owns the hook."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    assert not hasattr(feg, '_apply_referent_clarity_pre_finalize')
    assert callable(getattr(tp, '_apply_referent_clarity_pre_finalize', None))

def test_bj54_narration_constraint_debug_merge_gate_wrapper_collapsed() -> None:
    """BU2-B: narration-constraint debug merge owned by final_emission_narration_constraint_debug."""
    import inspect
    import game.final_emission_gate as feg
    import game.final_emission_narration_constraint_debug as narration_constraint_debug
    import game.final_emission_terminal_pipeline as tp
    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert not hasattr(feg, '_merge_narration_constraint_debug_into_outputs')
    assert not hasattr(tp, '_merge_narration_constraint_debug_into_outputs')
    assert 'merge_narration_constraint_debug_into_outputs(' in tp_src
    assert callable(getattr(narration_constraint_debug, 'merge_narration_constraint_debug_into_outputs', None))

def test_bj55_gate_fem_text_fingerprint_helper_collapsed() -> None:
    """Cycle BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns fingerprint patch."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    assert not hasattr(feg, '_patch_gate_fem_text_fingerprint')
    assert callable(getattr(tp, '_patch_fem_text_fingerprint', None))

def test_bj56_scene_opening_finalize_delegators_collapsed() -> None:
    """BU2-C: scene-opening accept debug owned by final_emission_opening_fallback."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_opening_fallback as opening_fallback
    assert not hasattr(feg, '_patch_scene_opening_candidate_emission_debug')
    assert not hasattr(feg, '_reassert_scene_opening_accepted_candidate')
    assert opening_fallback.patch_scene_opening_candidate_emission_debug.__module__ == 'game.final_emission_opening_fallback'
    assert opening_fallback.reassert_scene_opening_accepted_candidate.__module__ == 'game.final_emission_opening_fallback'
    assert getattr(fin, 'reassert_scene_opening_accepted_candidate', None) is opening_fallback.reassert_scene_opening_accepted_candidate

def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_collapsed() -> None:
    """Cycle BJ-57: route-illegal strip wrapper removed from gate; finalize owner owns strip helper."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    assert not hasattr(feg, '_strip_appended_route_illegal_contamination_sentences')
    assert callable(getattr(fin, 'strip_appended_route_illegal_contamination_sentences', None))

def test_bj30_dialogue_social_plan_strict_social_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-30: strict-social dialogue plan enforcement lives on dialogue_social_plan owner."""
    import game.dialogue_social_plan as dsp
    assert callable(getattr(dsp, 'enforce_dialogue_plan_invariant_on_strict_social', None))
    assert callable(getattr(dsp, 'strip_dialogue_from_text', None))
    assert callable(getattr(dsp, 'strict_social_line_matches_terminal_emission_pool', None))
    assert callable(getattr(dsp, 'is_bare_speech_attribution_shell_line', None))

def test_bj59_dialogue_social_plan_gate_delegators_collapsed() -> None:
    """Cycle BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls owner directly."""
    import game.dialogue_social_plan as dsp
    import game.final_emission_gate as feg
    assert not hasattr(feg, '_enforce_dialogue_plan_invariant_on_strict_social')
    assert not hasattr(feg, '_strip_dialogue_from_text')
    assert not hasattr(feg, '_strict_social_line_matches_terminal_emission_pool')
    assert not hasattr(feg, '_is_bare_speech_attribution_shell_line')
    assert callable(getattr(dsp, 'enforce_dialogue_plan_invariant_on_strict_social', None))
    assert callable(getattr(dsp, 'strip_dialogue_from_text', None))

def test_bj60_sealed_fallback_selector_gate_delegator_collapsed() -> None:
    """Cycle BJ-60: non-strict sealed selector wrapper removed from gate; owner resolves opening provider."""
    import game.final_emission_gate as feg
    import game.final_emission_sealed_fallback as sf
    assert not hasattr(feg, '_select_non_strict_replace_path_terminal_sealed_fallback_selection')
    assert callable(getattr(sf, 'select_non_strict_replace_path_terminal_sealed_fallback_selection', None))

def test_bj61_sealed_fallback_stamp_gate_delegators_collapsed() -> None:
    """Cycle BJ-61: sealed FEM stamp/route-meta import aliases removed from gate; generic_exit calls owner."""
    import game.final_emission_gate as feg
    import game.final_emission_sealed_fallback as sf
    for name in ('_stamp_sealed_fallback_realization_family', '_stamp_non_strict_sealed_replacement_realization_family', '_prepare_sealed_replacement_route_meta'):
        assert not hasattr(feg, name), name
    for name in ('stamp_sealed_fallback_realization_family', 'stamp_non_strict_sealed_replacement_realization_family', 'prepare_sealed_replacement_route_meta'):
        assert callable(getattr(sf, name, None)), name

def test_bj62_generic_exit_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-62: generic exit calls FEM assembly owner directly."""
    import inspect
    import game.final_emission_fem_assembly as fa
    import game.final_emission_generic_exit as ge
    accept_src = inspect.getsource(ge.run_generic_accept_exit)
    replace_src = inspect.getsource(ge.run_generic_replace_exit)
    assert 'fem_assembly.build_gate_accept_fem_base' in accept_src
    assert 'fem_assembly.merge_gate_layer_metas_into_fem' in accept_src
    assert '_build_gate_accept_fem_base' not in accept_src
    assert '_merge_gate_layer_metas_into_fem' not in accept_src
    assert 'fem_assembly.build_gate_replace_fem_base' in replace_src
    assert 'fem_assembly.merge_gate_layer_metas_into_fem' in replace_src
    assert '_build_gate_replace_fem_base' not in replace_src
    assert '_merge_gate_layer_metas_into_fem' not in replace_src
    assert callable(getattr(fa, 'build_gate_accept_fem_base', None))
    assert callable(getattr(fa, 'build_gate_replace_fem_base', None))
    assert callable(getattr(fa, 'merge_gate_layer_metas_into_fem', None))

def test_bj63_strict_social_stack_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-63: strict-social stack calls FEM assembly owner; gate FEM delegators removed."""
    import inspect
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert 'fem_assembly.build_gate_accept_fem_base' in src
    assert 'fem_assembly.build_gate_replace_fem_base' in src
    assert src.count('fem_assembly.merge_gate_layer_metas_into_fem') == 2
    assert 'fem_assembly.merge_pre_terminal_layer_debug' in src
    assert '_build_gate_accept_fem_base' not in src
    assert '_build_gate_replace_fem_base' not in src
    assert '_merge_gate_layer_metas_into_fem' not in src
    for name in ('_build_gate_accept_fem_base', '_build_gate_replace_fem_base', '_merge_gate_layer_metas_into_fem'):
        assert not hasattr(feg, name), name
    assert callable(getattr(fa, 'build_gate_accept_fem_base', None))
    assert callable(getattr(fa, 'build_gate_replace_fem_base', None))
    assert callable(getattr(fa, 'merge_gate_layer_metas_into_fem', None))

def test_bj64_non_strict_stack_opening_rt_promotion_calls_owner_directly() -> None:
    """Cycle BJ-64: non-strict stack calls opening RT promotion owner; gate alias removed."""
    import inspect
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_opening_fallback as ob
    src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert 'opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate' in src
    assert '_scene_opening_rt_contract_accept_path_promotes_candidate' not in src
    assert not hasattr(feg, '_scene_opening_rt_contract_accept_path_promotes_candidate')
    assert callable(getattr(ob, 'scene_opening_rt_contract_accept_path_promotes_candidate', None))

def test_bj65_stacks_opening_upstream_prepare_observability_merge_calls_owner_directly() -> None:
    """Cycle BJ-65: stacks call response_type owner for opening upstream-prepare observability merge."""
    import inspect
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_response_type as rt
    import game.final_emission_strict_social_stack as ss
    marker = 'response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug'
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert 'feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug' not in nss_src
    assert 'feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug' not in ss_src
    assert not hasattr(feg, '_merge_opening_upstream_prepare_attach_observability_into_response_type_debug')
    assert callable(getattr(rt, '_merge_opening_upstream_prepare_attach_observability_into_response_type_debug', None))

def test_bj31_tone_escalation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-31/BJ-79: tone escalation layer lives on final_emission_tone_escalation owner."""
    import game.final_emission_gate as feg
    import game.final_emission_tone_escalation as te
    assert callable(getattr(te, 'apply_tone_escalation_layer', None))
    assert callable(getattr(te, 'resolve_tone_escalation_contract', None))
    assert not hasattr(feg, '_apply_tone_escalation_layer')

def test_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly() -> None:
    """Cycle BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    verify_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly()

def test_bj32_narrative_authority_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-32/BJ-80: narrative authority layer lives on final_emission_narrative_authority owner."""
    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na
    assert callable(getattr(na, 'apply_narrative_authority_layer', None))
    assert callable(getattr(na, 'resolve_narrative_authority_contract', None))
    assert not hasattr(feg, '_apply_narrative_authority_layer')

def test_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly() -> None:
    """Cycle BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    verify_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly()

def test_bj58_contract_resolver_gate_delegators_collapsed() -> None:
    """Cycle BJ-58: contract resolver wrappers removed from gate; tone/authority owners resolve directly."""
    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na
    import game.final_emission_tone_escalation as te
    assert not hasattr(feg, '_resolve_tone_escalation_contract')
    assert not hasattr(feg, '_resolve_narrative_authority_contract')
    assert callable(getattr(te, 'resolve_tone_escalation_contract', None))
    assert callable(getattr(na, 'resolve_narrative_authority_contract', None))

def test_bj33_anti_railroading_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-33/BJ-81: anti-railroading layer lives on final_emission_anti_railroading owner."""
    import game.final_emission_anti_railroading as ar
    import game.final_emission_gate as feg
    assert callable(getattr(ar, 'apply_anti_railroading_layer', None))
    assert callable(getattr(ar, 'resolve_anti_railroading_contract', None))
    assert not hasattr(feg, '_apply_anti_railroading_layer')

def test_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly() -> None:
    """Cycle BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    verify_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly()

def test_bj34_context_separation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-34/BJ-82: context separation layer lives on final_emission_context_separation owner."""
    import game.final_emission_context_separation as cs
    import game.final_emission_gate as feg
    assert callable(getattr(cs, 'apply_context_separation_layer', None))
    assert callable(getattr(cs, 'resolve_context_separation_contract', None))
    assert not hasattr(feg, '_apply_context_separation_layer')

def test_bj82_ownership_registry_stacks_call_context_separation_owner_directly() -> None:
    """Cycle BJ-82: strict and non-strict stacks call context_separation owner directly."""
    verify_bj82_ownership_registry_stacks_call_context_separation_owner_directly()

def test_bj35_player_facing_narration_purity_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-35/BJ-83: narration purity layer lives on final_emission_player_facing_narration_purity owner."""
    import game.final_emission_gate as feg
    import game.final_emission_player_facing_narration_purity as pfp
    assert callable(getattr(pfp, 'apply_player_facing_narration_purity_layer', None))
    assert callable(getattr(pfp, 'resolve_player_facing_narration_purity_contract', None))
    assert not hasattr(feg, '_apply_player_facing_narration_purity_layer')

def test_bj83_ownership_registry_stacks_call_narration_purity_owner_directly() -> None:
    """Cycle BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    verify_bj83_ownership_registry_stacks_call_narration_purity_owner_directly()

def test_bj36_answer_shape_primacy_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-36/BJ-84: answer-shape primacy layer lives on final_emission_answer_shape_primacy owner."""
    import game.final_emission_answer_shape_primacy as asp
    import game.final_emission_gate as feg
    assert callable(getattr(asp, 'apply_answer_shape_primacy_layer', None))
    assert callable(getattr(asp, 'validate_answer_shape_primacy', None))
    assert not hasattr(feg, '_apply_answer_shape_primacy_layer')

def test_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """Cycle BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    verify_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly()

def test_bj37_scene_state_anchor_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-37/BJ-85: scene state anchor apply layer lives on final_emission_scene_state_anchor owner."""
    import game.final_emission_gate as feg
    import game.final_emission_scene_state_anchor as ssa
    assert callable(getattr(ssa, 'apply_scene_state_anchor_layer', None))
    assert not hasattr(feg, '_apply_scene_state_anchor_layer')

def test_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly() -> None:
    """Cycle BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    verify_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly()

def test_bj42_terminal_enforcement_pipeline_owner_entrypoint_locked() -> None:
    """Cycle BJ-42/BJ-69: terminal enforcement pipeline lives on final_emission_terminal_pipeline owner."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    assert callable(getattr(tp, 'run_gate_terminal_enforcement_pipeline', None))
    assert not hasattr(feg, '_run_gate_terminal_enforcement_pipeline')

def test_bj43_non_strict_layer_stack_owner_entrypoint_locked() -> None:
    """Cycle BJ-43/BJ-71: non-strict pre-fork layer stack lives on final_emission_non_strict_stack owner."""
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    assert callable(getattr(nss, 'run_non_strict_layer_stack', None))
    assert not hasattr(feg, '_run_non_strict_layer_stack')

def test_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly() -> None:
    """Cycle BJ-71: apply_final_emission_gate calls non_strict_stack owner directly."""
    verify_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly()

def test_bj44_strict_social_composition_trunk_owner_entrypoint_locked() -> None:
    """Cycle BJ-44/BJ-70: strict-social composition trunk lives on final_emission_strict_social_stack owner."""
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as sss
    assert callable(getattr(sss, 'run_strict_social_composition_trunk', None))
    assert not hasattr(feg, '_run_strict_social_composition_trunk')

def test_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly() -> None:
    """Cycle BJ-70: apply_final_emission_gate calls generic/strict-social exit owners directly."""
    verify_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly()

def test_bj69_ownership_registry_exit_stacks_call_terminal_finalize_owners_directly() -> None:
    """Cycle BJ-69: exit stacks call terminal pipeline and finalize owners directly."""
    import inspect
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_terminal_pipeline as tp
    ge_accept_src = inspect.getsource(ge.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(ge.run_generic_replace_exit)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    for src in (ge_accept_src, ge_replace_src, ss_src):
        assert 'terminal_pipeline.run_gate_terminal_enforcement_pipeline' in src
        assert 'emission_finalize.finalize_emission_output' in src
        assert 'emission_finalize.final_emission_fast_path_eligible' in src
        assert 'feg._run_gate_terminal_enforcement_pipeline' not in src
        assert 'feg._finalize_emission_output' not in src
        assert 'feg._final_emission_fast_path_eligible' not in src
    for name in ('_run_gate_terminal_enforcement_pipeline', '_finalize_emission_output', '_final_emission_fast_path_eligible'):
        assert not hasattr(feg, name), name
    assert callable(getattr(tp, 'run_gate_terminal_enforcement_pipeline', None))
    assert callable(getattr(fin, 'finalize_emission_output', None))
    assert callable(getattr(fin, 'final_emission_fast_path_eligible', None))

def test_bj45_generic_exit_owner_entrypoints_locked() -> None:
    """Cycle BJ-45/BJ-70: generic accept/replace exits live on final_emission_generic_exit owner."""
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge
    assert callable(getattr(ge, 'run_generic_accept_exit', None))
    assert callable(getattr(ge, 'run_generic_replace_exit', None))
    assert not hasattr(feg, '_run_generic_accept_exit')
    assert not hasattr(feg, '_run_generic_replace_exit')

def test_bj46_fem_assembly_owner_entrypoints_locked() -> None:
    """Cycle BJ-46/BJ-63: FEM accept/replace base assembly lives on final_emission_fem_assembly owner."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg
    assert callable(getattr(fa, 'build_gate_accept_fem_base', None))
    assert callable(getattr(fa, 'build_gate_replace_fem_base', None))
    assert not hasattr(feg, '_build_gate_accept_fem_base')
    assert not hasattr(feg, '_build_gate_replace_fem_base')

def test_bj47_fem_assembly_merge_gate_layer_metas_owner_entrypoint_locked() -> None:
    """Cycle BJ-47/BJ-63: FEM layer-meta merge lives on final_emission_fem_assembly owner."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg
    assert callable(getattr(fa, 'merge_gate_layer_metas_into_fem', None))
    assert not hasattr(feg, '_merge_gate_layer_metas_into_fem')

def test_bj48_fast_fallback_neutral_composition_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-48/BJ-86: FFNC layer apply/default-meta live on final_emission_fast_fallback_composition owner."""
    import game.final_emission_fast_fallback_composition as ffnc
    import game.final_emission_gate as feg
    assert callable(getattr(ffnc, 'default_fast_fallback_neutral_composition_meta', None))
    assert callable(getattr(ffnc, 'apply_fast_fallback_neutral_composition_layer', None))
    assert not hasattr(feg, '_apply_fast_fallback_neutral_composition_layer')

def test_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """Cycle BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    verify_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly()

def test_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """Cycle BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    verify_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly()

def test_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """Cycle BJ-88: stacks call final_emission_repairs answer exposition plan directly."""
    verify_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly()

def test_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly() -> None:
    """Cycle BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    verify_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly()

def test_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """Cycle BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    verify_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly()

def test_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """Cycle BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    verify_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly()

def test_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """Cycle BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    verify_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly()

def test_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-93: stacks call final_emission_repairs fallback debug/meta merge helpers directly."""
    verify_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly()

def test_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BU2-A: conversational memory debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly()

def test_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BU2-A: scene_state_anchor debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly()

def test_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: tone_escalation debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly()

def test_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narrative_authority debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly()

def test_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BU2-A: anti_railroading debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly()

def test_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BU2-A: context_separation debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly()

def test_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BU2-A: narration_purity debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly()

def test_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BU2-A: answer_shape_primacy debug merge consolidated on fem_assembly pre-terminal helper."""
    verify_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly()

def test_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """Cycle BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    verify_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly()

def test_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """Cycle BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    verify_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly()

def test_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """Cycle BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    verify_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly()

def test_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """Cycle BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    verify_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly()

def test_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly() -> None:
    """Cycle BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    verify_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly()

def test_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """Cycle BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    verify_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly()

def test_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """Cycle BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    verify_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly()

def test_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly() -> None:
    """Cycle BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    verify_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly()

def test_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """Cycle BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    verify_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly()

def test_bj111_ownership_registry_callers_use_normalize_text_owner_directly() -> None:
    """Cycle BJ-111: stack/exit callers use final_emission_text_formatting._normalize_text directly."""
    verify_bj111_ownership_registry_callers_use_normalize_text_owner_directly()

def test_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """Cycle BJ-112: strict_social_stack calls final_emission_text_formatting._normalize_text_preserve_paragraphs directly."""
    verify_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly()

def test_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """Cycle BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    verify_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly()

def test_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """Cycle BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    verify_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly()

def test_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """Cycle BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    verify_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly()

def test_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """Cycle BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    verify_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly()

def test_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """Cycle BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    verify_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly()

def test_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate() -> None:
    """Cycle BJ-118: should_replace_candidate_intro_fallback lives on anti_reset owner, not gate."""
    verify_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate()

def test_bj119_ownership_registry_stage_diff_telemetry_not_on_gate() -> None:
    """Cycle BJ-119: stage_diff_telemetry helpers live on stage_diff owner, not gate."""
    verify_bj119_ownership_registry_stage_diff_telemetry_not_on_gate()

def test_bj120_ownership_registry_harness_patches_canonical_owner_seams() -> None:
    """Cycle BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    verify_bj120_ownership_registry_harness_patches_canonical_owner_seams()

def test_bj121_ownership_registry_strict_social_build_patches_use_stack_seam() -> None:
    """Cycle BJ-121: strict-social build monkeypatches target strict_social_stack, not gate."""
    verify_bj121_ownership_registry_strict_social_build_patches_use_stack_seam()

def test_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings() -> None:
    """Cycle BJ-122: scene_state_anchoring tests use final_emission_scene_state_anchor owner bindings."""
    verify_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings()
_BJ123_ALLOWED_FEG_PATCH_SYMBOLS: Final[frozenset[str]] = frozenset({'get_speaker_selection_contract', 'apply_final_emission_gate'})
_BJ123_STALE_FEG_PATCH_FRAGMENTS: Final[tuple[str, ...]] = ('monkeypatch.setattr(feg, "_apply_visibility_enforcement"', 'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"', '"game.final_emission_gate._apply_visibility_enforcement"', 'monkeypatch.setattr(feg, "minimal_social_emergency_fallback_line"', 'monkeypatch.setattr(feg, "strict_social_emission_will_apply"', 'monkeypatch.setattr(_feg, "strict_social_emission_will_apply"', 'feg._finalize_emission_output(', 'feg._final_emission_fast_path_eligible(', 'feg._default_response_type_debug(', '"game.final_emission_gate.strict_social_emission_will_apply"', 'final_emission_gate.validate_player_facing_referential_clarity', 'final_emission_gate._try_strict_social_local_pronoun_substitution_repair', 'monkeypatch.setattr(feg, "build_final_strict_social_response"', 'monkeypatch.setattr(feg, "record_stage_snapshot"', 'monkeypatch.setattr(feg, "_repair_location_opening"', 'monkeypatch.setattr(feg, "validate_scene_state_anchoring"', 'import game.final_emission_gate as _feg', 'from game.final_emission_gate import _global_narrative_fallback_stock_line', 'from game.final_emission_gate import validate_answer_completeness', 'from game.final_emission_gate import inspect_answer_completeness_failure')
_BJ123_HARNESS_PATCH_SCAN_PATHS: Final[tuple[str, ...]] = ('tests/helpers/gate_equivalence_monkeypatch.py', 'tests/helpers/post_speaker_finalize_probe.py', 'tests/helpers/speaker_relocation_shadow_harness.py', 'tests/helpers/strict_social_harness.py', 'tests/helpers/emission_smoke_assertions.py', 'tests/test_final_emission_boundary_convergence.py', 'tests/test_final_emission_boundary_no_semantic_repair.py', 'tests/test_anti_railroading_transcript_regressions.py', 'tests/test_prompt_context.py', 'tests/test_social_exchange_emission.py', 'tests/test_final_emission_sealed_fallback.py', 'tests/test_final_emission_visibility.py', 'tests/test_manual_play_latency.py', 'tests/test_tone_escalation_rules.py', 'tests/test_referential_clarity_strict_social_local_repair.py', 'tests/test_lead_npc_payoff_and_fallback.py', 'tests/test_strict_social_answer_pressure_cashout.py', 'tests/test_anti_reset_emission_guard.py', 'tests/test_narration_transcript_regressions.py', 'tests/test_answer_completeness_rules.py', 'tests/test_interaction_continuity_repair.py', 'tests/test_narrative_authority_rules.py', 'tests/test_player_facing_narration_purity.py', 'tests/test_context_separation.py', 'tests/test_anti_railroading.py', 'tests/test_fallback_behavior_gate.py', 'tests/test_final_emission_opening_fallback.py', 'tests/test_diegetic_fallback_block4.py')

def test_bj123_ownership_registry_harness_patches_no_stale_feg_seams() -> None:
    """Cycle BJ-123: tests/helpers patch canonical owner modules, not removed feg re-exports."""
    verify_bj123_ownership_registry_harness_patches_no_stale_feg_seams()
_BJ124_DEAD_GATE_REEXPORT_SYMBOLS: Final[frozenset[str]] = frozenset({'_apply_visibility_enforcement', 'strict_social_emission_will_apply', 'minimal_social_emergency_fallback_line', '_finalize_emission_output', '_final_emission_fast_path_eligible', '_default_response_type_debug', '_default_response_delta_meta', 'validate_player_facing_referential_clarity', '_try_strict_social_local_pronoun_substitution_repair'})
_BJ124_DEAD_GATE_IMPORT_MARKERS: Final[tuple[str, ...]] = ('strict_social_emission_will_apply', '_default_response_type_debug', '_default_response_delta_meta', '_apply_visibility_enforcement', 'minimal_social_emergency_fallback_line', '_finalize_emission_output', '_final_emission_fast_path_eligible', 'validate_player_facing_referential_clarity', '_try_strict_social_local_pronoun_substitution_repair')

def test_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports() -> None:
    """Cycle BJ-124: gate module must not re-export BJ-123-dead harness seams."""
    verify_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports()

def test_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-125/BN8: anti-reset tests patch social_exchange_emission + preflight strict-social seam."""
    verify_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate()

def test_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-126/BN8: narration transcript tests patch owner + preflight strict-social seam."""
    verify_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate()
_BJ127_GLOBAL_SCAN_EXCLUDE: Final[frozenset[str]] = frozenset({'tests/test_ownership_registry.py', 'tests/test_final_emission_gate.py', 'tests/test_architecture_audit_tool.py'})
_BJ127_FEG_ALIAS_IMPORT_ALLOWLIST: Final[frozenset[str]] = frozenset({'tests/helpers/gate_equivalence_monkeypatch.py', 'tests/test_final_emission_gate.py', 'tests/test_ownership_registry.py', 'tests/test_speaker_contract_enforcement_extraction.py', 'tests/test_diegetic_fallback_narration.py', 'tests/test_final_emission_acceptance_quality.py', 'tests/test_final_emission_response_type.py', 'tests/test_final_emission_scene_state_anchor.py', 'tests/test_final_emission_visibility.py', 'tests/test_final_emission_sealed_fallback.py', 'tests/test_c4_narrative_mode_live_pipeline.py', 'tests/test_answer_shape_primacy.py', 'tests/test_final_emission_fast_fallback_composition.py', 'tests/test_final_emission_visibility_fallback.py', 'tests/test_dialogue_social_plan.py'})
_BJ127_FEG_ALIAS_IMPORT_MARKERS: Final[tuple[str, ...]] = ('import game.final_emission_gate as feg', 'import game.final_emission_gate as _feg', 'import game.final_emission_gate as feg_module')

def test_bj127_ownership_registry_global_stale_gate_harness_scan() -> None:
    """Cycle BJ-127: global scan — no stale feg monkeypatches or dead feg alias imports."""
    verify_bj127_ownership_registry_global_stale_gate_harness_scan()

def test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance() -> None:
    """Cycle BV16C: tests must monkeypatch finalize-tail owner modules, not terminal_pipeline delegates."""
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    violations: list[str] = []
    for rel in iter_bv16c_terminal_monkeypatch_scan_paths(repo_root):
        source = (repo_root / rel).read_text(encoding='utf-8')
        violations.extend(collect_bv16c_terminal_delegate_monkeypatch_violations(rel, source))
    assert not violations, 'BV16C terminal delegate monkeypatch violations:\n' + '\n'.join(violations)
    registry_doc = Path(__file__).read_text(encoding='utf-8')
    assert 'BV16C' in registry_doc
    assert BV16C_TERMINAL_PIPELINE_MODULE in registry_doc
    assert BV16C_VISIBILITY_OWNER in registry_doc
    assert BV16C_N4_OWNER in registry_doc
    assert BV16C_IC_OWNER in registry_doc
    assert BV16C_OPENING_OWNER in registry_doc
    assert BV16C_REPAIRS_OWNER in registry_doc
    assert 'run_gate_terminal_enforcement_pipeline' in BV16C_TERMINAL_ORCHESTRATION_SYMBOLS
    assert BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS
from tests.helpers.gate_thin_boundary_locks import BJ128_DEAD_GATE_IMPORT_MARKERS as _BJ128_DEAD_GATE_IMPORT_MARKERS, BJ128_DEAD_GATE_REEXPORT_SYMBOLS as _BJ128_DEAD_GATE_REEXPORT_SYMBOLS, BJ128_LIVE_GATE_SEAM_SYMBOLS as _BJ128_LIVE_GATE_SEAM_SYMBOLS, BJ129_ALLOWED_GATE_IMPORT_MODULES as _BJ129_ALLOWED_GATE_IMPORT_MODULES, BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES as _BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES, assert_gate_bj128_no_dead_import_reexports, assert_gate_bj129_thin_boundary_shape, gate_import_modules

def test_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports() -> None:
    """Cycle BJ-128: gate module keeps orchestration + live seams only; no import-only residue."""
    verify_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports()

def test_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked() -> None:
    """Cycle BJ-129: gate module must not regrow beyond orchestration + documented live seams."""
    verify_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked()

def test_bj49_gate_context_owner_entrypoint_locked() -> None:
    """Cycle BJ-49/BJ-72: gate entry/preflight context lives on final_emission_gate_context owner."""
    from tests.helpers.gate_delegator_governance import GATE_CONTEXT, assert_gate_lacks, assert_owner_callable
    assert_owner_callable(GATE_CONTEXT, 'initialize_gate_execution_context')
    assert_owner_callable(GATE_CONTEXT, 'GateExecutionContext')
    assert_gate_lacks('_initialize_gate_execution_context')

def test_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly() -> None:
    """Cycle BJ-72: apply_final_emission_gate calls gate_context owner directly."""
    verify_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly()

def test_bj41_finalize_emission_output_owner_entrypoint_locked() -> None:
    """Cycle BJ-41/BJ-69: finalize packaging and fast-path eligibility live on final_emission_finalize owner."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    assert callable(getattr(fin, 'finalize_emission_output', None))
    assert callable(getattr(fin, 'final_emission_fast_path_eligible', None))
    assert not hasattr(feg, '_finalize_emission_output')
    assert not hasattr(feg, '_final_emission_fast_path_eligible')

def test_bj40_acceptance_quality_n4_floor_seam_owner_entrypoint_locked() -> None:
    """Cycle BJ-40/BJ-74: N4 floor seam lives on final_emission_acceptance_quality owner."""
    import game.final_emission_acceptance_quality as aq
    import game.final_emission_gate as feg
    assert callable(getattr(aq, 'apply_acceptance_quality_n4_floor_seam', None))
    assert not hasattr(feg, '_apply_acceptance_quality_n4_floor_seam')

def test_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """Cycle BJ-74: terminal pipeline calls acceptance_quality N4 floor seam owner directly."""
    verify_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly()

def test_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """Cycle BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    verify_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly()

def test_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly() -> None:
    """Cycle BJ-76: terminal pipeline and non_strict_stack call IC emission-step owner directly."""
    verify_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly()

def test_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """Cycle BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    verify_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly()

def test_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly() -> None:
    """Cycle BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    verify_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly()

def test_bj39_response_type_contract_owner_entrypoint_locked() -> None:
    """Cycle BJ-39/BJ-67/BJ-68: response-type contract enforcement lives on final_emission_response_type owner."""
    import inspect
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_response_type as rt
    import game.final_emission_strict_social_stack as ss
    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness
    assert callable(getattr(rt, 'enforce_response_type_contract', None))
    assert not hasattr(feg, '_enforce_response_type_contract')
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert 'response_type.enforce_response_type_contract' in nss_src
    assert ss_src.count('response_type.enforce_response_type_contract') == 2
    assert 'feg._enforce_response_type_contract' not in nss_src
    assert 'feg._enforce_response_type_contract' not in ss_src
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert 'response_type.enforce_response_type_contract' in ob_src
    assert 'final_emission_response_type' in smoke_fn_src

def test_bj38_fallback_debug_merge_helpers_live_on_repairs_owner() -> None:
    """Cycle BJ-38/BJ-93/BJ-94: fallback/conversational-memory emission_debug merges live on final_emission_repairs."""
    import game.final_emission_gate as feg
    import game.final_emission_repairs as fer
    assert callable(getattr(fer, 'merge_fallback_behavior_into_emission_debug', None))
    assert callable(getattr(fer, 'merge_conversational_memory_inspection_into_emission_debug', None))
    assert not hasattr(feg, '_merge_fallback_behavior_into_emission_debug')
    assert not hasattr(feg, '_merge_conversational_memory_inspection_into_emission_debug')

def test_bu8_bu4_production_ownership_write_paths_parity_locked() -> None:
    """BU8: BU4 CSV registry stays parity-locked with live game/ ownership write-path discovery."""
    from tests.helpers.ownership_write_path_governance import bu4_csv_path, production_write_path_keys_from_csv, production_write_path_parity_errors, REQUIRED_PRODUCTION_WRITE_PATH_KEYS
    assert bu4_csv_path().is_file()
    csv_keys = production_write_path_keys_from_csv()
    assert REQUIRED_PRODUCTION_WRITE_PATH_KEYS <= csv_keys
    assert production_write_path_parity_errors() == []

def test_bu8_attach_realization_fallback_family_producer_stamp_pairing_locked() -> None:
    """BU8: attach_realization_fallback_family call sites pair with bucket stamper helpers."""
    from tests.helpers.ownership_write_path_governance import attach_realization_exempt_documentation, producer_stamp_pairing_errors
    assert producer_stamp_pairing_errors() == []
    assert attach_realization_exempt_documentation()

def test_bu9_visibility_fallback_producer_stamp_pairing_locked() -> None:
    """BU9/BU10: visibility-family producer repair kinds pair with bucket stamper helpers."""
    from tests.helpers.ownership_write_path_governance import visibility_fallback_write_path_inventory, visibility_producer_stamp_exempt_documentation, visibility_producer_stamp_pairing_errors
    assert visibility_producer_stamp_pairing_errors() == []
    assert visibility_producer_stamp_exempt_documentation()
    inventory = visibility_fallback_write_path_inventory()
    assert inventory['visibility_producer_repair_kind_sites']
    assert inventory['visibility_fallback_owner_bucket_writes']
    first_mention_site = ('game/final_emission_visibility_fallback.py', 'apply_first_mention_enforcement')
    referential_site = ('game/final_emission_visibility_fallback.py', 'apply_referential_clarity_enforcement')
    producer_sites = inventory['visibility_producer_repair_kind_sites']
    assert any((site[0] == first_mention_site[0] and site[1] == first_mention_site[1] for site in producer_sites))
    assert sum((1 for site in producer_sites if site[0] == referential_site[0] and site[1] == referential_site[1])) >= 2
