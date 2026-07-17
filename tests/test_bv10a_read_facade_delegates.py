"""BV10A delegate verification — facades must re-export authority without new logic."""
from __future__ import annotations

import ast
from pathlib import Path

import game.attribution_read_views as attribution_read_views
import game.final_emission_meta_read as meta_read
import game.final_emission_owner_bucket_views as bucket_views
import game.final_emission_ownership_schema as ownership_schema
import game.observability_attribution_read as observability_attribution_read
import game.ownership_projection_views as ownership_projection_views

from tests.failure_classification_contract import ALLOWED_PRODUCER_REPAIR_KINDS

ROOT = Path(__file__).resolve().parents[1]
_FACADE_PATHS = (
    ROOT / "game" / "attribution_read_views.py",
    ROOT / "game" / "ownership_projection_views.py",
    ROOT / "game" / "observability_attribution_read.py",
)
_WRITE_FORBIDDEN = (
    "ensure_",
    "patch_",
    "merge_",
    "stamp_",
    "apply_",
    "package_",
    "refresh_",
)


def _function_delegates_to(module, symbol: str, authority) -> None:
    facade_fn = getattr(module, symbol)
    authority_fn = getattr(authority, symbol)
    assert facade_fn is authority_fn, f"{symbol} must delegate to authority unchanged"


def test_bv10a_attribution_read_views_bucket_mappers_delegate_to_bucket_views() -> None:
    for symbol in (
        "opening_fallback_owner_bucket_from_fields",
        "opening_fallback_owner_bucket_from_meta",
        "visibility_fallback_owner_bucket_from_fields",
        "sealed_fallback_owner_bucket_from_fields",
    ):
        _function_delegates_to(attribution_read_views, symbol, bucket_views)


def test_bv10a_attribution_read_views_schema_constants_delegate_to_schema() -> None:
    for symbol in (
        "ALLOWED_FALLBACK_SELECTION_OWNERS",
        "ALLOWED_FALLBACK_CONTENT_OWNERS",
        "OPENING_FALLBACK_SELECTION_OWNER",
        "OPENING_FALLBACK_CONTENT_OWNER",
    ):
        assert getattr(attribution_read_views, symbol) is getattr(ownership_schema, symbol)


def test_bv10a_ownership_projection_views_delegate_to_schema() -> None:
    _function_delegates_to(
        ownership_projection_views,
        "normalize_sanitizer_trace_owner_to_lineage_owner",
        ownership_schema,
    )
    assert (
        ownership_projection_views.OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS
        is ownership_schema.OWNERSHIP_LINEAGE_ATTRIBUTION_FIELDS
    )


def test_bv10a_observability_attribution_read_delegates_to_meta_read() -> None:
    for symbol in (
        "FINAL_EMISSION_META_KEY",
        "default_response_type_debug",
        "infer_accept_path_final_emitted_source",
        "normalized_observational_telemetry_bundle",
        "summarize_gameplay_validation_for_turn",
        "classify_dead_turn",
        "read_dead_turn_from_gm_output",
        "read_debug_notes_from_turn_payload",
        "read_emission_debug_lane",
        "read_final_emission_meta_dict",
        "assemble_unified_observational_telemetry_bundle",
        "build_fem_observability_events",
        "normalize_final_emission_meta_for_observability",
        "stage_diff_narrative_authenticity_projection",
    ):
        _function_delegates_to(observability_attribution_read, symbol, meta_read)


def test_bv10a_facade_registry_surfaces_are_diagnostic_only() -> None:
    attr_surface = attribution_read_views.attribution_read_views_surface()
    proj_surface = ownership_projection_views.ownership_projection_views_surface()
    obs_surface = observability_attribution_read.observability_attribution_read_surface()
    assert attr_surface["facade"] == "game.attribution_read_views"
    assert proj_surface["facade"] == "game.ownership_projection_views"
    assert obs_surface["facade"] == "game.observability_attribution_read"
    assert "bucket_mappers" in attr_surface
    assert "lineage_owner_vocabulary" in proj_surface
    assert "observability_symbols" in obs_surface
    assert "producer_repair_kind_constants" in obs_surface


def test_bv10a_observability_producer_repair_kind_constants_match_classifier_vocabulary() -> None:
    """CO79: facade producer-repair-kind surface stays parity-locked to classifier vocabulary."""
    obs_surface = observability_attribution_read.observability_attribution_read_surface()
    constant_names = obs_surface["producer_repair_kind_constants"]
    facade_values = frozenset(
        getattr(observability_attribution_read, name) for name in constant_names
    )
    assert facade_values == ALLOWED_PRODUCER_REPAIR_KINDS, (
        "observability facade producer repair kind values "
        f"{sorted(facade_values)!r} must match classifier "
        f"ALLOWED_PRODUCER_REPAIR_KINDS {sorted(ALLOWED_PRODUCER_REPAIR_KINDS)!r}; "
        f"extra={sorted(facade_values - ALLOWED_PRODUCER_REPAIR_KINDS)!r}, "
        f"missing={sorted(ALLOWED_PRODUCER_REPAIR_KINDS - facade_values)!r}"
    )
    assert len(constant_names) == len(ALLOWED_PRODUCER_REPAIR_KINDS), (
        "observability facade must expose one constant name per classifier producer repair kind"
    )


def test_bv10a_facade_modules_contain_no_write_authority_symbols() -> None:
    for path in _FACADE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        defined: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    defined.add(node.name)
        offenders = [
            name
            for name in defined
            if any(name.startswith(prefix) for prefix in _WRITE_FORBIDDEN)
        ]
        assert not offenders, f"{path.name} must not define write paths: {offenders}"


def test_bv10a_facade_modules_only_define_registry_surfaces_and_vocabulary_helpers() -> None:
    allowed_public_defs = {
        "attribution_read_views.py": {"attribution_read_views_surface"},
        "ownership_projection_views.py": {
            "lineage_owner_vocabulary",
            "sanitizer_trace_owner_vocabulary",
            "ownership_projection_views_surface",
        },
        "observability_attribution_read.py": {"observability_attribution_read_surface"},
    }
    for path in _FACADE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        defined = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        }
        assert defined == allowed_public_defs[path.name], path.name
