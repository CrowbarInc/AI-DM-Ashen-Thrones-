"""BD-6 gate dependency compression guards (import-light; no pytest).

Pure validation logic for non-owner test import compression during BD-2–BD-5 facade migration.
Enforced by ``test_bd6_gate_dependency_compression_*`` in ``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Mapping

from tests.ownership_guard_bv_compatibility import (
    _BV12A_GATE_ORCHESTRATION_FACADE,
    _BV12A_REPLAY_FEM_READ_FACADE,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Cycle BD-6: compressed gate-owned imports non-owner tests must not reintroduce (BD-2–BD-5).
_BD6_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"
_BD6_GATE_BRIDGE_FACADE: Final[str] = "tests/helpers/gate_integration_smoke.py"
_BD6_REPLAY_BRIDGE_FACADE: Final[str] = "tests/helpers/replay_smoke_assertions.py"
_BD6_GOLDEN_REPLAY_FACADE: Final[str] = "tests/helpers/golden_replay_projection.py"
_BD6_OPENING_FACADE: Final[str] = "tests/helpers/opening_fallback_evidence.py"
_BD6_FORBIDDEN_FEM_READ_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "read_final_emission_meta_from_turn_payload",
        "read_emission_debug_lane_from_turn_payload",
    },
)
_BD6_FORBIDDEN_OWNER_BUCKET_PREFIXES: Final[tuple[str, ...]] = (
    "OPENING_FALLBACK_OWNER_",
    "SEALED_FALLBACK_OWNER_",
    "VISIBILITY_FALLBACK_OWNER_",
)
_BD6_COMPRESSED_OWNER_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate",
        "game.final_emission_meta",
        "game.final_emission_replay_projection",
    },
)
# Narrow allowlist: primary owners, BD-2–BD-5 KEEP suites, facade delegates, gate monkeypatch helpers,
# and audit fixture modules that embed gate-import strings intentionally.
_BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/test_final_emission_gate.py": "Gate orchestration redirect stub (BM decomposition; BD-2/BD-5 KEEP)",
    "tests/test_final_emission_gate_delegator_regression.py": "BJ delegator/re-export regression owner (BM decomposition; BJ-41–BJ-129 KEEP)",
    "tests/test_final_emission_gate_diagnostics.py": "Gate FEM/debug diagnostics owner (BM decomposition; BD-2 KEEP)",
    "tests/test_final_emission_gate_n4.py": "N4 acceptance-quality gate placement owner (BM decomposition; BD-2 KEEP)",
    "tests/test_final_emission_gate_orchestration_order.py": "Gate behavioral layer-order owner (BM decomposition; BD-2 KEEP)",
    "tests/test_final_emission_gate_selector_snapshots.py": "Gate selector/source snapshot owner (BM decomposition; BD-2 KEEP)",
    "tests/test_final_emission_meta.py": "FEM projection / runtime-lineage owner (BD-3/BD-4/BD-5 KEEP)",
    "tests/test_fallback_behavior_gate.py": "Gate-adjacent behavior owner (BD-2 KEEP)",
    "tests/test_final_emission_boundary_no_semantic_repair.py": "Gate boundary owner; terminal_pipeline visibility noop (BJ-123 KEEP)",
    "tests/test_block_s_speaker_local_rebind_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_t_speaker_relocation_shadow_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_u_finalize_stack_divergence.py": "Finalize-stack divergence proof (BD-2 KEEP)",
    "tests/test_social_exchange_emission.py": "Strict-social emission legality owner (BD-2 KEEP)",
    "tests/test_speaker_contract_enforcement.py": "Speaker contract enforcement owner (BJ-28 KEEP)",
    "tests/test_interaction_continuity_repair.py": "Interaction continuity emission owner (BJ-29 KEEP)",
    "tests/test_dialogue_social_plan.py": "Dialogue social plan + strict-social enforcement owner (BJ-30 KEEP)",
    "tests/test_tone_escalation_rules.py": "Tone escalation layer owner (BJ-31 KEEP)",
    "tests/test_narrative_authority_rules.py": "Narrative authority layer owner (BJ-32 KEEP)",
    "tests/test_anti_railroading.py": "Anti-railroading layer owner (BJ-33 KEEP)",
    "tests/test_context_separation.py": "Context separation layer owner (BJ-34 KEEP)",
    "tests/test_player_facing_narration_purity.py": "Player-facing narration purity layer owner (BJ-35 KEEP)",
    "tests/test_answer_shape_primacy.py": "Answer-shape primacy layer owner (BJ-36 KEEP)",
    "tests/test_final_emission_visibility.py": "Visibility semantics owner (BD-3 KEEP)",
    "tests/test_final_emission_channel_separation.py": "FEM channel packaging owner-adjacent (BD-3 KEEP)",
    "tests/test_opening_fallback_owner_bucket.py": "Opening fallback owner-bucket mapping owner (BD-5 KEEP)",
    "tests/test_final_emission_opening_fallback.py": "Opening fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_sealed_fallback.py": "Sealed fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_visibility_fallback.py": "Visibility fallback owner-adjacent (BD-5/BJ-27/BJ-73 KEEP)",
    "tests/test_final_emission_first_mention_composition.py": "First-mention composition owner (BJ-7 KEEP)",
    "tests/test_final_emission_fast_fallback_composition.py": "Fast-fallback composition owner (BJ-8 KEEP)",
    "tests/test_final_emission_passive_scene_pressure.py": "Passive scene pressure owner (BJ-9 KEEP)",
    "tests/test_final_emission_scene_emit_integrity.py": "Scene emit integrity owner (BJ-10 KEEP)",
    "tests/test_final_emission_scene_state_anchor.py": "Scene state anchor owner (BJ-11/BJ-37 KEEP)",
    "tests/test_final_emission_scene_facts.py": "Scene facts owner (BJ-12 KEEP)",
    "tests/test_final_emission_referential_clarity.py": "Referential clarity owner (BJ-13 KEEP)",
    "tests/test_final_emission_response_type.py": "Response-type contract helper + enforce owner (BJ-18/BJ-39 KEEP)",
    "tests/test_final_emission_narrative_mode_output.py": "Narrative mode output validation owner (BJ-19 KEEP)",
    "tests/test_final_emission_acceptance_quality.py": "Acceptance quality N4 helper + floor seam owner (BJ-20/BJ-40/BJ-74 KEEP)",
    _BD6_SMOKE_FACADE: "Downstream smoke facade delegate (BD-2/BD-3 internal imports)",
    _BD6_GOLDEN_REPLAY_FACADE: "Golden replay / replay-projection facade delegate (BD-3/BD-4/BD-5)",
    _BD6_OPENING_FACADE: "Opening fallback evidence facade delegate (BD-5)",
    "tests/helpers/gate_equivalence_monkeypatch.py": "Gate namespace monkeypatch equivalence helper (BD-2 KEEP)",
    "tests/helpers/opening_fallback_gate_harness.py": "Opening attach-then gate harness; response_type owner seams (BJ-123 KEEP)",
    "tests/helpers/post_speaker_finalize_probe.py": "Gate finalize-stack probe wrappers (BD-2 KEEP)",
    "tests/helpers/speaker_relocation_shadow_harness.py": "Speaker relocation shadow harness; feg namespace (BD-2 KEEP)",
    "tests/helpers/strict_social_harness.py": "Strict-social harness; feg monkeypatch + consumer entry (BD-2 KEEP)",
    "tests/test_architecture_audit_tool.py": "Audit fixture strings embed gate-import examples",
    "tests/test_validation_layer_audit_smoke.py": "Audit fixture strings embed gate-import examples",
    "tests/test_test_audit_tool.py": "Inventory audit fixture strings embed gate-import examples",
    "tests/test_realization_layer_audit.py": "Realization audit fixture strings embed gate-import examples",
    "tests/test_run_scenario_spine_validation.py": "Scenario-spine validation; canonical FEM/lineage read for opening attribution diagnostics (BL1)",
    "tests/test_ownership_registry.py": "Governance module; AO5 runtime vs acceptance boundary check imports replay projection",
    # BD-6 facade sub-delegates and authority helpers (CE/CF/CG cycles).
    "tests/helpers/golden_replay_projection_extractors.py": "Golden replay projection internal extractor delegate (CE5/BD-4)",
    "tests/helpers/golden_replay_projection_fallbacks.py": "Golden replay projection internal fallback delegate (CE5/BD-4)",
    "tests/helpers/fem_normalization_contract.py": "CF3 FEM normalization contract helper; routes through replay projection facade (CF3)",
    "tests/helpers/attribution_contract.py": "CG attribution contract authority helper (CG-1)",
    "tests/helpers/failure_classification_builders.py": "CG failure-classification row builder authority (CG-1)",
    "tests/helpers/failure_classification_split_owner.py": "CG split-owner classification vocabulary authority (CG-1)",
    "tests/helpers/failure_classifier.py": "CG failure classifier behavior authority (CG-1)",
    "tests/helpers/replacement_attribution_inventory.py": "CG replacement attribution inventory authority (CG-1)",
    "tests/helpers/bx_guard_speaker_parity.py": "BX speaker parity guard; gate consumer via orchestration smoke (BX)",
    # BD-6 replay/projection owner suites (CE4/CF/CG cycles).
    "tests/test_attribution_contract.py": "CG attribution contract owner suite (CG-1 KEEP)",
    "tests/test_failure_classifier.py": "CG failure classifier owner suite (CG-1 KEEP)",
    "tests/test_replacement_attribution_inventory.py": "CG replacement attribution inventory owner (CG-1 KEEP)",
    "tests/test_runtime_lineage_telemetry.py": "Runtime lineage telemetry owner (AO5/BD-4 KEEP)",
    "tests/test_cf1_fallback_family_precedence.py": "CF1 fallback-family precedence matrix owner (CF1 KEEP)",
    "tests/test_cf3_raw_normalized_fem_field_matrix.py": "CF3 raw/normalized FEM field matrix owner (CF3 KEEP)",
    "tests/test_bx_speaker_identity_end_to_end_parity.py": "BX speaker identity end-to-end parity owner (BX KEEP)",
    "tests/test_by_first_semantic_mutation_attribution.py": "BY first semantic mutation attribution owner (BY KEEP)",
    "tests/test_speaker_contract_risk.py": "Speaker contract risk owner; gate consumer via orchestration smoke (KEEP)",
    "tests/test_golden_replay_fallback_acceptance_matrix.py": "CE4 golden replay fallback acceptance matrix owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_long_session_summary.py": "CE4 golden replay fallback long-session summary owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_opening_projection.py": "CE4 golden replay fallback opening projection owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_sanitizer_projection.py": "CE4 golden replay fallback sanitizer projection owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_sealed_projection.py": "CE4 golden replay fallback sealed projection owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_upstream_fast_projection.py": "CE4 golden replay fallback upstream-fast projection owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_upstream_projection.py": "CE4 golden replay fallback upstream projection owner (CE4 KEEP)",
    "tests/test_golden_replay_fallback_visibility_projection.py": "CE4 golden replay fallback visibility projection owner (CE4 KEEP)",
}


def _normalize_test_rel_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _bd6_is_forbidden_owner_bucket_symbol(module: str, symbol: str) -> bool:
    if module not in _BD6_COMPRESSED_OWNER_MODULES:
        return False
    if symbol == "FINAL_EMISSION_META_KEY":
        return True
    return any(symbol.startswith(prefix) for prefix in _BD6_FORBIDDEN_OWNER_BUCKET_PREFIXES)


def _bd6_facade_replacement(module: str, symbol: str) -> str:
    if module == "game.final_emission_gate" and symbol == "apply_final_emission_gate":
        return f"{_BV12A_GATE_ORCHESTRATION_FACADE}::apply_final_emission_gate_consumer"
    if module == "game.final_emission_meta" and symbol in _BD6_FORBIDDEN_FEM_READ_SYMBOLS:
        return (
            f"{_BV12A_REPLAY_FEM_READ_FACADE}::final_emission_meta_from_output "
            f"(integration/smoke) or game.final_emission_meta.read_final_emission_meta_dict "
            f"(gate-output FEM read)"
        )
    if module == "game.final_emission_replay_projection":
        return (
            f"game.final_emission_replay_projection "
            f"(e.g. build_fem_runtime_lineage_events, SEALED_REPLACEMENT_SUBKINDS)"
        )
    if _bd6_is_forbidden_owner_bucket_symbol(module, symbol):
        if symbol.startswith("OPENING_FALLBACK_OWNER_"):
            return f"{_BD6_OPENING_FACADE} (opening bucket/route constants)"
        return f"{_BD6_GOLDEN_REPLAY_FACADE} (sealed/visibility bucket constants)"
    return "tests.helpers emission/golden/opening facades per BD-2–BD-5"


def collect_gate_dependency_compression_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
) -> list[str]:
    """Return import violations when a non-owner test reintroduces compressed gate-owned imports."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
            for alias in node.names:
                symbol = alias.name
                forbidden = False
                if module == "game.final_emission_gate" and symbol == "apply_final_emission_gate":
                    forbidden = True
                elif module == "game.final_emission_meta" and symbol in _BD6_FORBIDDEN_FEM_READ_SYMBOLS:
                    forbidden = True
                elif module == "game.final_emission_replay_projection":
                    forbidden = True
                elif _bd6_is_forbidden_owner_bucket_symbol(module, symbol):
                    forbidden = True
                if not forbidden:
                    continue
                key = (module, symbol)
                if key in seen:
                    continue
                seen.add(key)
                imported = f"{module}.{symbol}"
                replacement = _bd6_facade_replacement(module, symbol)
                violations.append(
                    f"{norm}: forbidden compressed gate import {imported!r} "
                    f"(use facade replacement: {replacement})",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                if module != "game.final_emission_replay_projection" and not module.startswith(
                    "game.final_emission_replay_projection.",
                ):
                    continue
                key = (module, "")
                if key in seen:
                    continue
                seen.add(key)
                replacement = _bd6_facade_replacement(
                    "game.final_emission_replay_projection",
                    module.rsplit(".", 1)[-1] or module,
                )
                violations.append(
                    f"{norm}: forbidden compressed gate import {module!r} "
                    f"(use facade replacement: {replacement})",
                )
    return violations


def iter_gate_dependency_compression_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
) -> tuple[str, ...]:
    """All tests/**/*.py paths subject to BD-6 import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "tests").rglob("*.py")):
        rel = _normalize_test_rel_path(path.relative_to(root))
        if rel in allowlist:
            continue
        paths.append(rel)
    return tuple(paths)
