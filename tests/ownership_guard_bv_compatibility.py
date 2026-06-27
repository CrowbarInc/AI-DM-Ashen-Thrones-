"""BV2C/BV10C read-cluster and BV7C/BV12C/BV13C/BV14C compat guards (import-light; no pytest).

Pure validation logic for read-cluster facade routing, compat-barrel regrowth lockdown, and
smoke-monolith import routing. Enforced by ``test_bv2c_*``, ``test_bv10_*``, ``test_bv7c_*``,
``test_bv12c_*``, ``test_bv13c_*``, and ``test_bv14c_*`` in ``tests/test_compat_import_governance.py``.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOWNSTREAM_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"


def _normalize_test_rel_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


# Cycle BV2C: production modules allowed to import ``game.final_emission_meta`` (write/packaging owners).
_BV2C_META_WRITE_OWNER_GAME_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_meta",
        "game.final_emission_meta_read",
        "game.fallback_provenance_debug",
        "game.final_emission_acceptance_quality",
        "game.final_emission_fem_assembly",
        "game.final_emission_finalize",
        "game.final_emission_gate_preflight_defaults",
        "game.final_emission_generic_exit",
        "game.final_emission_narration_constraint_debug",
        "game.final_emission_narrative_mode_output",
        "game.final_emission_opening_fallback",
        "game.final_emission_passive_scene_pressure",
        "game.final_emission_referential_clarity",
        "game.final_emission_repairs",
        "game.final_emission_response_type",
        "game.final_emission_sealed_fallback",
        "game.final_emission_strict_social_stack",
        "game.final_emission_terminal_pipeline",
        "game.final_emission_visibility_fallback",
        "game.gm_retry",
        "game.interaction_continuity",
        "game.output_sanitizer",
        "game.upstream_response_repairs",
    },
)
_BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/test_final_emission_meta.py": "Canonical FEM owner regression suite (BV2C KEEP)",
    "tests/test_compat_import_governance.py": "Import governance / compatibility guard entrypoint owner (BV2C KEEP)",
    "tests/ownership_closeout_delegate_locks.py": (
        "BJ delegate closeout lock helpers extracted from governance owner (CH11/CH13 KEEP)"
    ),
    "tests/test_cf3_raw_normalized_fem_field_matrix.py": "CF3 raw/normalized FEM field matrix owner (CF3 KEEP)",
}
_BV2C_META_READ_FACADE: Final[str] = "game.final_emission_meta_read"
_BV2C_OWNER_BUCKET_VIEWS_FACADE: Final[str] = "game.final_emission_owner_bucket_views"

# Cycle BV10C: read-side authority modules guarded against non-owner direct imports.
_BV10C_META_READ_AUTHORITY: Final[str] = "game.final_emission_meta_read"
_BV10C_BUCKET_VIEWS_AUTHORITY: Final[str] = "game.final_emission_owner_bucket_views"
_BV10C_OWNERSHIP_SCHEMA_AUTHORITY: Final[str] = "game.final_emission_ownership_schema"
_BV10C_READ_CLUSTER_AUTHORITIES: Final[frozenset[str]] = frozenset(
    {
        _BV10C_META_READ_AUTHORITY,
        _BV10C_BUCKET_VIEWS_AUTHORITY,
        _BV10C_OWNERSHIP_SCHEMA_AUTHORITY,
    },
)
_BV10C_ATTRIBUTION_READ_FACADE: Final[str] = "game.attribution_read_views"
_BV10C_OWNERSHIP_PROJECTION_FACADE: Final[str] = "game.ownership_projection_views"
_BV10C_OBSERVABILITY_READ_FACADE: Final[str] = "game.observability_attribution_read"
_BV10C_REPLAY_SMOKE_FACADE: Final[str] = "tests.helpers.replay_fem_read_smoke"
_BV10C_READ_CLUSTER_GAME_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_meta",
        _BV10C_META_READ_AUTHORITY,
        _BV10C_BUCKET_VIEWS_AUTHORITY,
        _BV10C_OWNERSHIP_SCHEMA_AUTHORITY,
        _BV10C_ATTRIBUTION_READ_FACADE,
        _BV10C_OWNERSHIP_PROJECTION_FACADE,
        _BV10C_OBSERVABILITY_READ_FACADE,
        "game.final_emission_visibility_fallback",
        "game.final_emission_sealed_fallback",
        "game.final_emission_replay_projection",
    },
)
_BV10C_READ_CLUSTER_TEST_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/test_final_emission_meta.py": "FEM / schema owner regression suite (BV10C KEEP)",
    "tests/test_opening_fallback_owner_bucket.py": "Opening fallback owner-bucket mapping owner (BV10C KEEP)",
    "tests/test_compat_import_governance.py": "Import governance / compatibility guard entrypoint owner (BV10C KEEP)",
    "tests/test_bv10a_read_facade_delegates.py": "BV10 facade delegate verification owner (BV10C KEEP)",
    "tests/helpers/replay_smoke_assertions.py": "Replay FEM read bridge facade (BV7A/BV10C KEEP)",
    "tests/helpers/replay_fem_read_smoke.py": "Replay FEM read domain facade owner (BV12A KEEP)",
    "tests/helpers/gate_orchestration_smoke.py": "Gate orchestration domain facade owner (BV12A KEEP)",
    "tests/helpers/fallback_bridge_smoke.py": "Fallback dual-bridge import surface (BV12A KEEP)",
    "tests/test_bv12a_smoke_bridge_facade_delegates.py": "BV12A facade delegate verification owner (BV12A KEEP)",
    "tests/test_bv13a_final_emission_text_facade_delegates.py": "BV13A/BV13B text compat delegate verification owner (BV13A KEEP)",
}


def _bv2c_meta_import_replacement(module: str, symbol: str) -> str:
    if symbol.startswith(("OPENING_FALLBACK_OWNER_", "SEALED_FALLBACK_OWNER_", "VISIBILITY_FALLBACK_OWNER_")):
        return _BV2C_OWNER_BUCKET_VIEWS_FACADE
    if symbol.endswith("_owner_bucket_from_meta") or symbol.endswith("_owner_bucket_from_fields"):
        return _BV2C_OWNER_BUCKET_VIEWS_FACADE
    return _BV2C_META_READ_FACADE


def collect_bv2c_final_emission_meta_import_violations(
    rel_path: str,
    source: str,
    *,
    game_allowlist: frozenset[str] = _BV2C_META_WRITE_OWNER_GAME_MODULES,
    test_allowlist: Mapping[str, str] = _BV2C_META_DIRECT_IMPORT_TEST_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports ``game.final_emission_meta`` outside BV2C allowlists."""
    norm = _normalize_test_rel_path(rel_path)
    if norm.startswith("tests/") and norm in test_allowlist:
        return []
    if norm.startswith("game/"):
        module_name = norm.replace("/", ".").removesuffix(".py")
        if module_name in game_allowlist:
            return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "game.final_emission_meta":
            for alias in node.names:
                symbol = alias.name
                key = (node.module, symbol)
                if key in seen:
                    continue
                seen.add(key)
                imported = f"{node.module}.{symbol}"
                replacement = _bv2c_meta_import_replacement(node.module, symbol)
                violations.append(
                    f"{norm}: forbidden direct final_emission_meta import {imported!r} "
                    f"(use facade: {replacement})",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != "game.final_emission_meta":
                    continue
                key = (alias.name, alias.asname or alias.name)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    f"{norm}: forbidden direct final_emission_meta module import "
                    f"(use {_BV2C_META_READ_FACADE} / {_BV2C_OWNER_BUCKET_VIEWS_FACADE} / "
                    f"game.final_emission_replay_projection for read-side access)",
                )
    return violations


def iter_bv2c_final_emission_meta_import_guard_scan_paths(
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """All game/tests Python paths subject to BV2C meta import lockdown."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for subdir in ("game", "tests"):
        for path in sorted((root / subdir).rglob("*.py")):
            paths.append(_normalize_test_rel_path(path.relative_to(root)))
    return tuple(paths)


def _bv10_read_cluster_import_replacement(authority_module: str, symbol: str) -> str:
    if authority_module == _BV10C_BUCKET_VIEWS_AUTHORITY:
        return _BV10C_ATTRIBUTION_READ_FACADE
    if authority_module == _BV10C_OWNERSHIP_SCHEMA_AUTHORITY:
        if any(
            token in symbol
            for token in (
                "LINEAGE",
                "SANITIZER",
                "PROVENANCE",
                "SPEAKER_CONTRACT",
                "normalize_sanitizer",
            )
        ):
            return _BV10C_OWNERSHIP_PROJECTION_FACADE
        return _BV10C_ATTRIBUTION_READ_FACADE
    if symbol in {"read_final_emission_meta_dict", "FINAL_EMISSION_META_KEY"}:
        return f"{_BV10C_REPLAY_SMOKE_FACADE}::final_emission_meta_from_output (tests) or {_BV10C_OBSERVABILITY_READ_FACADE} (production)"
    if symbol.endswith("_owner_bucket_from_meta") or symbol.endswith("_owner_bucket_from_fields"):
        return _BV10C_ATTRIBUTION_READ_FACADE
    if symbol.startswith(("OPENING_FALLBACK_OWNER_", "SEALED_FALLBACK_OWNER_", "VISIBILITY_FALLBACK_OWNER_")):
        return _BV10C_ATTRIBUTION_READ_FACADE
    return _BV10C_OBSERVABILITY_READ_FACADE


def collect_bv10_read_cluster_direct_import_guard_violations(
    rel_path: str,
    source: str,
    *,
    game_allowlist: frozenset[str] = _BV10C_READ_CLUSTER_GAME_ALLOWLIST,
    test_allowlist: Mapping[str, str] = _BV10C_READ_CLUSTER_TEST_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports read-cluster authority outside BV10C allowlists."""
    norm = _normalize_test_rel_path(rel_path)
    if norm.startswith("tests/") and norm in test_allowlist:
        return []
    if norm.startswith("game/"):
        module_name = norm.replace("/", ".").removesuffix(".py")
        if module_name in game_allowlist:
            return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _BV10C_READ_CLUSTER_AUTHORITIES:
            for alias in node.names:
                symbol = alias.name
                key = (node.module, symbol)
                if key in seen:
                    continue
                seen.add(key)
                imported = f"{node.module}.{symbol}"
                replacement = _bv10_read_cluster_import_replacement(node.module, symbol)
                violations.append(
                    f"{norm}: forbidden read-cluster authority import {imported!r} "
                    f"(use facade: {replacement})",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _BV10C_READ_CLUSTER_AUTHORITIES:
                    continue
                key = (alias.name, alias.asname or alias.name)
                if key in seen:
                    continue
                seen.add(key)
                replacement = (
                    f"{_BV10C_ATTRIBUTION_READ_FACADE} / {_BV10C_OWNERSHIP_PROJECTION_FACADE} / "
                    f"{_BV10C_OBSERVABILITY_READ_FACADE}"
                )
                violations.append(
                    f"{norm}: forbidden read-cluster authority module import {alias.name!r} "
                    f"(use facade: {replacement})",
                )
    return violations


def iter_bv10_read_cluster_direct_import_guard_scan_paths(
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """All game/tests Python paths subject to BV10 read-cluster import lockdown."""
    return iter_bv2c_final_emission_meta_import_guard_scan_paths(repo_root)


_BD6_RT_SMOKE_FACADE: Final[str] = "tests/helpers/response_type_smoke.py"
_BD6_AC_SMOKE_FACADE: Final[str] = "tests/helpers/actor_consistency_smoke.py"
_BD6_RD_SMOKE_FACADE: Final[str] = "tests/helpers/route_determinism_smoke.py"
_BV12A_REPLAY_FEM_READ_FACADE: Final[str] = "tests/helpers/replay_fem_read_smoke.py"
_BV12A_GATE_ORCHESTRATION_FACADE: Final[str] = "tests/helpers/gate_orchestration_smoke.py"
_BV12A_FALLBACK_BRIDGE_FACADE: Final[str] = "tests/helpers/fallback_bridge_smoke.py"
_BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS: Final[frozenset[str]] = frozenset(
    {"apply_final_emission_gate_consumer", "gm_response_stub"}
)
_BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS: Final[frozenset[str]] = frozenset(
    {"final_emission_meta_from_output", "read_turn_debug_notes"}
)
_BV7B_EXTRACTED_RT_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "response_type_contract",
        "assert_response_type_meta",
        "assert_response_type_contract_surfaces",
        "enforce_response_type_contract_layer",
    }
)
_BV7B_EXTRACTED_AC_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "validate_answer_completeness",
        "apply_answer_completeness_layer",
        "skip_answer_completeness_layer",
    }
)
_BV7B_EXTRACTED_RD_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "validate_response_delta",
        "apply_response_delta_layer",
        "skip_response_delta_layer",
        "strict_social_answer_pressure_rd_contract_active",
        "inspect_response_delta_failure",
        "assert_response_delta_boundary_validate_only",
        "assert_no_boundary_reorder_repair",
    }
)
_BV7C_EXTRACTED_SYMBOL_TO_FACADE: Final[Mapping[str, str]] = {
    **{symbol: _BD6_RT_SMOKE_FACADE for symbol in _BV7B_EXTRACTED_RT_SYMBOLS},
    **{symbol: _BD6_AC_SMOKE_FACADE for symbol in _BV7B_EXTRACTED_AC_SYMBOLS},
    **{symbol: _BD6_RD_SMOKE_FACADE for symbol in _BV7B_EXTRACTED_RD_SYMBOLS},
    **{symbol: _BV12A_GATE_ORCHESTRATION_FACADE for symbol in _BV7A_EXTRACTED_GATE_BRIDGE_SYMBOLS},
    **{symbol: _BV12A_REPLAY_FEM_READ_FACADE for symbol in _BV7A_EXTRACTED_REPLAY_BRIDGE_SYMBOLS},
}
_BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/helpers/emission_smoke_assertions.py": (
        "compatibility barrel owner re-exports extracted bridge/family symbols"
    ),
}
_BV7C_ALLOWED_MONOLITH_STATIC_IMPORTERS: Final[frozenset[str]] = frozenset(
    {
        "tests/test_answer_completeness_rules.py",
        "tests/test_broad_address_social_bid.py",
        "tests/test_broadcast_open_call_social.py",
        "tests/test_c4_narrative_mode_live_pipeline.py",
        "tests/test_diegetic_fallback_narration.py",
        "tests/test_emission_smoke_assertions_contract.py",
        "tests/test_empty_social_retry_regressions.py",
        "tests/test_interaction_continuity_repair.py",
        "tests/test_mixed_state_recovery_regressions.py",
        "tests/test_opening_start_seam_regressions.py",
        "tests/test_social_exchange_emission.py",
        "tests/test_social_speaker_grounding.py",
        "tests/test_synthetic_smoke.py",
        "tests/test_turn_packet_stage_diff_integration.py",
        "tests/test_turn_pipeline_shared.py",
    }
)
_BV7C_ALLOWED_MONOLITH_DYNAMIC_IMPORTERS: Final[frozenset[str]] = frozenset(
    {
        "tests/test_compat_import_governance.py",
        "tests/test_final_emission_gate_delegator_regression.py",
    }
)
_BV7C_MONOLITH_FI_CAP: Final[int] = 18

# Cycle BV12C: compat smoke bridge barrels are re-export-only; consumers route through domain facades.
_BV12C_REPLAY_COMPAT_MODULE: Final[str] = "tests.helpers.replay_smoke_assertions"
_BV12C_GATE_COMPAT_MODULE: Final[str] = "tests.helpers.gate_integration_smoke"
_BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/helpers/replay_smoke_assertions.py": "compat barrel re-exports replay FEM domain facade",
    "tests/helpers/gate_integration_smoke.py": "compat barrel re-exports gate orchestration domain facade",
    "tests/test_bv12a_smoke_bridge_facade_delegates.py": "BV12A/BV12C delegate verification owner",
    "tests/test_bv13a_final_emission_text_facade_delegates.py": "BV13A text compat delegate verification owner",
    "tests/test_compat_import_governance.py": "Governance module; synthetic violation fixtures",
}
_BV12C_ALLOWED_REPLAY_COMPAT_IMPORTERS: Final[frozenset[str]] = frozenset(
    {"tests/test_bv12a_smoke_bridge_facade_delegates.py"}
)
_BV12C_ALLOWED_GATE_COMPAT_IMPORTERS: Final[frozenset[str]] = frozenset(
    {"tests/test_bv12a_smoke_bridge_facade_delegates.py"}
)
_BV12C_COMPAT_BARREL_FI_CAP: Final[int] = 2
_BV12C_INTENTIONAL_DOMAIN_HUBS: Final[Mapping[str, str]] = {
    "tests.helpers.replay_fem_read_smoke": "FEM read + debug notes (replay acceptance, projection, observability)",
    "tests.helpers.gate_orchestration_smoke": "Gate consumer + HTTP stub (orchestration/integration suites)",
    "tests.helpers.fallback_bridge_smoke": "Dual-bridge fallback suites only (narrow combined surface)",
}
_BV12C_COMPAT_BARREL_SCAN_ROOTS: Final[tuple[str, ...]] = ("tests", "tools", "scripts")

# Cycle BV13C: final_emission_text compat barrel is re-export + fallback wrapper only.
_BV13C_TEXT_COMPAT_MODULE: Final[str] = "game.final_emission_text"
_BV13C_TEXT_FORMATTING_AUTHORITY: Final[str] = "game.final_emission_text_formatting"
_BV13C_TEXT_POLICY_AUTHORITY: Final[str] = "game.final_emission_text_policy"
_BV13C_TEXT_LEGACY_REPAIR_AUTHORITY: Final[str] = "game.final_emission_text_legacy_semantic_repair"
_BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST: Final[Mapping[str, str]] = {
    "game/final_emission_text.py": "compat barrel re-exports formatting/policy/legacy authorities",
    "game/final_emission_fast_fallback_composition.py": "fallback wrapper consumer (_global_narrative_fallback_stock_line)",
    "game/final_emission_scene_emit_integrity.py": "fallback wrapper consumer (_global_narrative_fallback_stock_line)",
    "tests/test_bv13a_final_emission_text_facade_delegates.py": "BV13A/BV13C delegate verification owner",
    "tests/test_diegetic_fallback_block4.py": "fallback wrapper test consumer",
    "tests/test_compat_import_governance.py": "Governance module; synthetic violation fixtures",
}
_BV13C_ALLOWED_TEXT_COMPAT_IMPORTERS: Final[frozenset[str]] = frozenset(
    {
        "game/final_emission_fast_fallback_composition.py",
        "game/final_emission_scene_emit_integrity.py",
        "tests/test_bv13a_final_emission_text_facade_delegates.py",
        "tests/test_diegetic_fallback_block4.py",
    }
)
_BV13C_TEXT_COMPAT_FI_CAP: Final[int] = 8
_BV13C_INTENTIONAL_TEXT_DOMAIN_HUBS: Final[Mapping[str, str]] = {
    "game.final_emission_text_formatting": "Text normalization/sanitization primitives (production-core)",
    "game.final_emission_text_policy": "Validator policy vocabulary tuples (controlled policy surface)",
    "game.final_emission_text_legacy_semantic_repair": "Test-only legacy semantic repair (isolated from compat)",
}
_BV13C_TEXT_COMPAT_SCAN_ROOTS: Final[tuple[str, ...]] = ("game", "tests", "tools", "scripts")

# Cycle BV14C: social_exchange_emission compat barrel is composition authority + re-exports only.
_BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE: Final[str] = "game.social_exchange_emission"
_BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY: Final[str] = "game.social_exchange_fallback_catalog"
_BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY: Final[str] = "game.social_exchange_policy"
_BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY: Final[str] = "game.social_exchange_validation"
_BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY: Final[str] = "game.social_exchange_projection"
_BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST: Final[Mapping[str, str]] = {
    "game/social_exchange_emission.py": "compat barrel re-exports fallback/policy/validation/projection authorities",
    "game/final_emission_strict_social_stack.py": "composition authority consumer (build_final_strict_social_response)",
    "game/social_exchange_validation.py": "BD-2 delegate verification (lazy hard_reject composition import)",
    "tests/test_bv14a_social_exchange_emission_facade_delegates.py": "BV14A/BV14C delegate verification owner",
    "tests/test_narration_transcript_regressions.py": "composition regression consumer",
    "tests/test_output_sanitizer.py": "sanitizer integration consumer (composition filter monkeypatch)",
    "tests/test_compat_import_governance.py": "Governance module; synthetic violation fixtures",
    "tests/test_realization_provenance.py": "composition regression consumer",
    "tests/test_social_answer_candidate.py": "composition regression consumer",
    "tests/test_social_emission_quality.py": "composition regression consumer",
    "tests/test_social_exchange_emission.py": "BD-2 strict-social emission legality owner",
    "tests/test_social_speaker_grounding.py": "composition regression consumer",
    "tests/test_social_target_authority_regressions.py": "composition regression consumer",
    "tests/ownership_closeout_delegate_locks.py": "BJ-115/116 delegate introspection for composition authority seams (CH11 KEEP)",
}
_BV14C_ALLOWED_SOCIAL_EXCHANGE_COMPAT_IMPORTERS: Final[frozenset[str]] = frozenset(
    {
        "game/final_emission_strict_social_stack.py",
        "game/social_exchange_validation.py",
        "tests/test_bv14a_social_exchange_emission_facade_delegates.py",
        "tests/test_narration_transcript_regressions.py",
        "tests/test_output_sanitizer.py",
        "tests/test_realization_provenance.py",
        "tests/test_social_answer_candidate.py",
        "tests/test_social_emission_quality.py",
        "tests/test_social_exchange_emission.py",
        "tests/test_social_speaker_grounding.py",
        "tests/test_social_target_authority_regressions.py",
        "tests/ownership_closeout_delegate_locks.py",
    }
)
_BV14C_SOCIAL_EXCHANGE_COMPAT_FI_CAP: Final[int] = 12
_BV14C_INTENTIONAL_SOCIAL_EXCHANGE_DOMAIN_HUBS: Final[Mapping[str, str]] = {
    "game.social_exchange_fallback_catalog": "Strict-social fallback phrase catalog + terminal recovery (explicit maintenance surface)",
    "game.social_exchange_policy": "Strict-social routing/policy predicates + NPC display helpers (controlled policy surface)",
    "game.social_exchange_validation": "Route legality + interruption shape validators (BD-2 validation authority)",
    "game.social_exchange_projection": "Final-emission logging/trace projection for strict-social paths",
}
_BV14C_SOCIAL_EXCHANGE_COMPAT_SCAN_ROOTS: Final[tuple[str, ...]] = ("game", "tests", "tools", "scripts")

def collect_bv7c_smoke_monolith_import_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports BV7A/BV7B extracted symbols from the monolith barrel."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "tests.helpers.emission_smoke_assertions":
            continue
        for alias in node.names:
            symbol = alias.name
            if symbol == "*":
                key = ("*", _DOWNSTREAM_SMOKE_FACADE)
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    f"{norm}: forbidden star import from {_DOWNSTREAM_SMOKE_FACADE!r} "
                    f"(import extracted symbols from family/bridge facades only)",
                )
                continue
            facade = _BV7C_EXTRACTED_SYMBOL_TO_FACADE.get(symbol)
            if not facade:
                continue
            key = (symbol, facade)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                f"{norm}: forbidden monolith import {symbol!r} from {_DOWNSTREAM_SMOKE_FACADE} "
                f"(use facade replacement: {facade})",
            )
    return violations


def iter_bv7c_smoke_monolith_import_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BV7C_MONOLITH_IMPORT_GUARD_ALLOWLIST,
) -> tuple[str, ...]:
    """All tests/**/*.py paths subject to BV7C monolith import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "tests").rglob("*.py")):
        rel = _normalize_test_rel_path(path.relative_to(root))
        if rel in allowlist:
            continue
        paths.append(rel)
    return tuple(paths)


def collect_bv7c_monolith_static_importers(source_by_rel: Mapping[str, str]) -> frozenset[str]:
    """Return test modules with static ``from tests.helpers.emission_smoke_assertions import``."""
    importers: set[str] = set()
    for rel, source in source_by_rel.items():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "tests.helpers.emission_smoke_assertions":
                importers.add(_normalize_test_rel_path(rel))
                break
    return frozenset(importers)


def collect_bv12c_compat_barrel_import_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports BV12 compat barrels outside the allowlist."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in (
            _BV12C_REPLAY_COMPAT_MODULE,
            _BV12C_GATE_COMPAT_MODULE,
        ):
            if node.module in seen:
                continue
            seen.add(node.module)
            domain = (
                _BV12A_REPLAY_FEM_READ_FACADE
                if node.module == _BV12C_REPLAY_COMPAT_MODULE
                else _BV12A_GATE_ORCHESTRATION_FACADE
            )
            violations.append(
                f"{norm}: forbidden compat barrel import from {node.module!r} "
                f"(use domain facade: {domain})",
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in (_BV12C_REPLAY_COMPAT_MODULE, _BV12C_GATE_COMPAT_MODULE):
                    continue
                if alias.name in seen:
                    continue
                seen.add(alias.name)
                domain = (
                    _BV12A_REPLAY_FEM_READ_FACADE
                    if alias.name == _BV12C_REPLAY_COMPAT_MODULE
                    else _BV12A_GATE_ORCHESTRATION_FACADE
                )
                violations.append(
                    f"{norm}: forbidden compat barrel import {alias.name!r} "
                    f"(use domain facade: {domain})",
                )
    return violations


def iter_bv12c_compat_barrel_import_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BV12C_COMPAT_BARREL_IMPORT_GUARD_ALLOWLIST,
    scan_roots: tuple[str, ...] = _BV12C_COMPAT_BARREL_SCAN_ROOTS,
) -> tuple[str, ...]:
    """All Python paths subject to BV12C compat-barrel import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel in allowlist:
                continue
            paths.append(rel)
    return tuple(paths)


def collect_bv12c_compat_barrel_static_importers(
    repo_root: Path | None = None,
    *,
    compat_module: str,
    scan_roots: tuple[str, ...] = _BV12C_COMPAT_BARREL_SCAN_ROOTS,
) -> frozenset[str]:
    """Return modules with static imports of a BV12 compat barrel."""
    root = _REPO_ROOT if repo_root is None else repo_root
    barrel_paths = {
        "tests/helpers/replay_smoke_assertions.py",
        "tests/helpers/gate_integration_smoke.py",
    }
    importers: set[str] = set()
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel in barrel_paths:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == compat_module:
                    importers.add(rel)
                    break
                if isinstance(node, ast.Import):
                    if any(alias.name == compat_module for alias in node.names):
                        importers.add(rel)
                        break
    return frozenset(importers)


def collect_bv13c_text_compat_import_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports the BV13 text compat barrel outside the allowlist."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == _BV13C_TEXT_COMPAT_MODULE:
            if _BV13C_TEXT_COMPAT_MODULE in seen:
                continue
            seen.add(_BV13C_TEXT_COMPAT_MODULE)
            violations.append(
                f"{norm}: forbidden compat barrel import from {_BV13C_TEXT_COMPAT_MODULE!r} "
                f"(use formatting authority: {_BV13C_TEXT_FORMATTING_AUTHORITY}; "
                f"policy authority: {_BV13C_TEXT_POLICY_AUTHORITY})",
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != _BV13C_TEXT_COMPAT_MODULE:
                    continue
                if alias.name in seen:
                    continue
                seen.add(alias.name)
                violations.append(
                    f"{norm}: forbidden compat barrel import {alias.name!r} "
                    f"(use formatting authority: {_BV13C_TEXT_FORMATTING_AUTHORITY}; "
                    f"policy authority: {_BV13C_TEXT_POLICY_AUTHORITY})",
                )
    return violations


def iter_bv13c_text_compat_import_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BV13C_TEXT_COMPAT_IMPORT_GUARD_ALLOWLIST,
    scan_roots: tuple[str, ...] = _BV13C_TEXT_COMPAT_SCAN_ROOTS,
) -> tuple[str, ...]:
    """All Python paths subject to BV13C text compat-barrel import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel in allowlist:
                continue
            paths.append(rel)
    return tuple(paths)


def collect_bv13c_text_compat_static_importers(
    repo_root: Path | None = None,
    *,
    scan_roots: tuple[str, ...] = _BV13C_TEXT_COMPAT_SCAN_ROOTS,
) -> frozenset[str]:
    """Return modules with static imports of the BV13 text compat barrel."""
    root = _REPO_ROOT if repo_root is None else repo_root
    barrel_path = "game/final_emission_text.py"
    importers: set[str] = set()
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel == barrel_path:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == _BV13C_TEXT_COMPAT_MODULE:
                    importers.add(rel)
                    break
                if isinstance(node, ast.Import):
                    if any(alias.name == _BV13C_TEXT_COMPAT_MODULE for alias in node.names):
                        importers.add(rel)
                        break
    return frozenset(importers)


def _bv14c_social_exchange_compat_authority_guidance() -> str:
    return (
        f"fallback authority: {_BV14C_SOCIAL_EXCHANGE_FALLBACK_AUTHORITY}; "
        f"policy authority: {_BV14C_SOCIAL_EXCHANGE_POLICY_AUTHORITY}; "
        f"validation authority: {_BV14C_SOCIAL_EXCHANGE_VALIDATION_AUTHORITY}; "
        f"projection authority: {_BV14C_SOCIAL_EXCHANGE_PROJECTION_AUTHORITY}"
    )


def collect_bv14c_social_exchange_compat_import_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST,
) -> list[str]:
    """Return violations when a module imports the BV14 social-exchange compat barrel outside the allowlist."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[str] = set()
    guidance = _bv14c_social_exchange_compat_authority_guidance()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE:
            if _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE in seen:
                continue
            seen.add(_BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE)
            violations.append(
                f"{norm}: forbidden compat barrel import from {_BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE!r} "
                f"(use {_bv14c_social_exchange_compat_authority_guidance()})",
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE:
                    continue
                if alias.name in seen:
                    continue
                seen.add(alias.name)
                violations.append(
                    f"{norm}: forbidden compat barrel import {alias.name!r} (use {guidance})",
                )
    return violations


def iter_bv14c_social_exchange_compat_import_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BV14C_SOCIAL_EXCHANGE_COMPAT_IMPORT_GUARD_ALLOWLIST,
    scan_roots: tuple[str, ...] = _BV14C_SOCIAL_EXCHANGE_COMPAT_SCAN_ROOTS,
) -> tuple[str, ...]:
    """All Python paths subject to BV14C social-exchange compat-barrel import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel in allowlist:
                continue
            paths.append(rel)
    return tuple(paths)


def collect_bv14c_social_exchange_compat_static_importers(
    repo_root: Path | None = None,
    *,
    scan_roots: tuple[str, ...] = _BV14C_SOCIAL_EXCHANGE_COMPAT_SCAN_ROOTS,
) -> frozenset[str]:
    """Return modules with static imports of the BV14 social-exchange compat barrel."""
    root = _REPO_ROOT if repo_root is None else repo_root
    barrel_path = "game/social_exchange_emission.py"
    importers: set[str] = set()
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = _normalize_test_rel_path(path.relative_to(root))
            if rel == barrel_path:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE:
                    importers.add(rel)
                    break
                if isinstance(node, ast.Import):
                    if any(alias.name == _BV14C_SOCIAL_EXCHANGE_COMPAT_MODULE for alias in node.names):
                        importers.add(rel)
                        break
    return frozenset(importers)


def bv_governance_documentation_corpus(*, ownership_registry_source: str) -> str:
    """Documentation corpus for BV cycle lock tests (central registry doc + guard module)."""
    return ownership_registry_source + "\n" + Path(__file__).read_text(encoding="utf-8")
