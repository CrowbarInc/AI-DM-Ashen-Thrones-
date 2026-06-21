"""BU8/BU9/BU10 — BU4 ownership write-path parity and producer-stamp pairing governance (tests only)."""
from __future__ import annotations

import ast
import csv
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BU4_CSV = _REPO_ROOT / "docs" / "audits" / "BU4_ownership_write_paths.csv"
_BU4_SCRIPT = _REPO_ROOT / "scripts" / "bu4_ownership_write_path_discovery.py"
_GAME_ROOT = _REPO_ROOT / "game"

WritePathKey = tuple[str, str, str]  # (rel_path, function, field)

# BU8 — lock stamp helpers and sanitizer trace companions documented in BU4 registry.
REQUIRED_PRODUCTION_WRITE_PATH_KEYS: frozenset[WritePathKey] = frozenset(
    {
        ("game/final_emission_meta.py", "stamp_opening_fallback_owner_bucket", "opening_fallback_owner_bucket"),
        ("game/final_emission_meta.py", "stamp_retry_terminal_fallback_producer_metadata", "opening_fallback_owner_bucket"),
        ("game/final_emission_meta.py", "stamp_upstream_prepared_opening_producer_metadata", "opening_fallback_owner_bucket"),
        ("game/final_emission_meta.py", "stamp_visibility_fallback_owner_bucket_from_fields", "visibility_fallback_owner_bucket"),
        ("game/final_emission_visibility_fallback.py", "stamp_visibility_fallback_metadata", "visibility_fallback_owner_bucket"),
        ("game/final_emission_meta.py", "apply_sanitizer_producer_attribution_to_fem", "sealed_fallback_owner_bucket"),
        ("game/output_sanitizer.py", "_mark_sanitizer_empty_fallback", "sanitizer_empty_fallback_owner_trace_short"),
        ("game/output_sanitizer.py", "_mark_sanitizer_strict_social_fallback", "sanitizer_strict_social_selection_owner_trace_short"),
        ("game/output_sanitizer.py", "_mark_sanitizer_strict_social_fallback", "sanitizer_strict_social_prose_owner_trace_short"),
    }
)

# Explicit non-opening/non-owner attach_realization_fallback_family call sites (BU8).
_ATTACH_REALIZATION_EXEMPT: dict[WritePathKey, str] = {
    ("game/realization_provenance.py", "attach_realization_fallback_family", "realization_fallback_family"): (
        "canonical stamp helper definition"
    ),
    ("game/api.py", "_synthetic_manual_play_gpt_budget_gm", "realization_fallback_family"): (
        "GPT budget synthetic GM metadata — no FEM owner bucket"
    ),
    ("game/api.py", "_build_gpt_narration_from_authoritative_state", "realization_fallback_family"): (
        "upstream API fast-fallback — provenance only until gate merge"
    ),
    ("game/gm.py", "call_gpt", "realization_fallback_family"): (
        "GPT provider failure fallback metadata — no FEM owner bucket"
    ),
    ("game/social_exchange_emission.py", "stamp_strict_social_deterministic_fallback_family", "realization_fallback_family"): (
        "family-only wrapper; sealed owner bucket stamped at gate replacement"
    ),
    ("game/social_exchange_emission.py", "_structured_fact_emission_details", "realization_fallback_family"): (
        "structured-fact emission details — not a main ownership path"
    ),
    ("game/social_exchange_emission.py", "build_final_strict_social_response", "realization_fallback_family"): (
        "strict-social emission details — sealed bucket owned by gate replacement"
    ),
    ("game/upstream_response_repairs.py", "build_upstream_prepared_emission_payload", "realization_fallback_family"): (
        "non-opening upstream prepared bundle — no opening owner bucket"
    ),
    ("game/upstream_response_repairs.py", "merge_upstream_prepared_emission_into_gm_output", "realization_fallback_family"): (
        "upstream prepared merge — answer/action path, not opening bucket"
    ),
    ("game/final_emission_response_type.py", "enforce_response_type_contract", "realization_fallback_family"): (
        "dialogue/answer upstream-prepared repairs — not opening owner bucket paths"
    ),
    ("game/final_emission_sealed_fallback.py", "stamp_sealed_fallback_realization_family", "realization_fallback_family"): (
        "paired stamper owns family + sealed_fallback_owner_bucket"
    ),
    ("game/final_emission_sealed_fallback.py", "stamp_non_strict_sealed_replacement_realization_family", "realization_fallback_family"): (
        "paired stamper owns family + sealed_fallback_owner_bucket"
    ),
}


# BU9/BU10 — visibility-family producer repair kinds that require bucket stamper pairing.
_VISIBILITY_PRODUCER_REPAIR_KINDS: frozenset[str] = frozenset(
    {
        "visibility_enforcement",
        "first_mention_enforcement",
        "referential_clarity_enforcement",
        "referential_clarity_local_substitution",
    }
)

# Explicit visibility producer-stamp pairing exceptions (BU9/BU10).
_VISIBILITY_PRODUCER_STAMP_EXEMPT: dict[WritePathKey, str] = {
    ("game/final_emission_meta.py", "stamp_producer_repair_kind", "producer_repair_kind"): (
        "canonical producer repair kind stamp helper definition"
    ),
    ("game/final_emission_meta.py", "apply_sanitizer_producer_attribution_to_fem", "producer_repair_kind"): (
        "sanitizer trace → FEM merge; visibility bucket owned by sanitizer/sealed paths"
    ),
    ("game/final_emission_meta.py", "stamp_visibility_fallback_owner_bucket_from_fields", "visibility_fallback_owner_bucket"): (
        "canonical visibility owner-bucket stamp helper definition"
    ),
    ("game/final_emission_visibility_fallback.py", "stamp_visibility_fallback_metadata", "visibility_fallback_owner_bucket"): (
        "route-level visibility metadata stamper; repair kind stamped by orchestrators"
    ),
    ("game/final_emission_strict_social_stack.py", "stamp_producer_repair_kind", "producer_repair_kind"): (
        "strict-social repair kind — sealed bucket stamper, not visibility"
    ),
    ("game/final_emission_terminal_pipeline.py", "stamp_producer_repair_kind", "producer_repair_kind"): (
        "strict-social terminal repair kind — sealed bucket stamper, not visibility"
    ),
    ("game/final_emission_repairs.py", "stamp_producer_repair_kind", "producer_repair_kind"): (
        "fallback behavior repair kind — no visibility owner bucket"
    ),
    ("game/final_emission_repairs.py", "repair_fallback_behavior", "producer_repair_kind"): (
        "fallback behavior repair orchestrator — sealed/opening buckets not visibility-scoped"
    ),
}


@dataclass(frozen=True)
class ProducerRepairKindSite:
    rel_path: str
    function: str
    line: int
    repair_kind: str | None


@dataclass(frozen=True)
class VisibilityOwnerBucketWriteSite:
    rel_path: str
    function: str
    line: int


@dataclass(frozen=True)
class AttachRealizationSite:
    rel_path: str
    function: str
    line: int
    family_marker: str | None


def _load_bu4_discovery_module() -> object:
    spec = importlib.util.spec_from_file_location("bu4_ownership_write_path_discovery", _BU4_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load BU4 discovery script: {_BU4_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bu4_csv_path() -> Path:
    return _BU4_CSV


def production_write_path_keys_from_csv(csv_path: Path | None = None) -> frozenset[WritePathKey]:
    path = csv_path or _BU4_CSV
    keys: set[WritePathKey] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rel = str(row.get("rel_path") or "").strip().replace("\\", "/")
            if not rel.startswith("game/"):
                continue
            function = str(row.get("function") or "").strip()
            field = str(row.get("field") or "").strip()
            if function and field:
                keys.add((rel, function, field))
    return frozenset(keys)


def discovered_production_write_path_keys() -> frozenset[WritePathKey]:
    bu4 = _load_bu4_discovery_module()
    game_root = bu4.GAME  # type: ignore[attr-defined]
    hits = bu4.scan_tree(game_root, "game") + bu4.curated_hits()  # type: ignore[attr-defined]
    deduped = bu4.dedupe_hits(hits)  # type: ignore[attr-defined]
    keys = {
        (h.rel_path.replace("\\", "/"), h.function, h.field)
        for h in deduped
        if h.rel_path.startswith("game/")
    }
    return frozenset(keys)


def production_write_path_parity_errors() -> list[str]:
    """Compare BU4 CSV registry to live game/ discovery (order-independent)."""
    csv_keys = production_write_path_keys_from_csv()
    discovered = discovered_production_write_path_keys()
    errors: list[str] = []
    for key in sorted(REQUIRED_PRODUCTION_WRITE_PATH_KEYS - csv_keys):
        errors.append(f"BU4 CSV missing required production write path: {key!r}")
    for key in sorted(discovered - csv_keys):
        errors.append(f"BU4 CSV missing discovered production write path: {key!r}")
    for key in sorted(csv_keys - discovered):
        errors.append(f"BU4 CSV stale production write path not discovered in game/: {key!r}")
    return errors


def _family_marker_from_call(node: ast.Call) -> str | None:
    if len(node.args) < 2:
        return None
    arg = node.args[1]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    if isinstance(arg, ast.Name):
        return arg.id
    if isinstance(arg, ast.Attribute):
        return arg.attr
    return None


def _repair_kind_from_call(node: ast.Call) -> str | None:
    if len(node.args) >= 2:
        arg = node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        if isinstance(arg, ast.Name):
            return arg.id
        if isinstance(arg, ast.Attribute):
            return arg.attr
    for kw in node.keywords:
        if kw.arg == "repair_kind":
            val = kw.value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                return val.value
            if isinstance(val, ast.Name):
                return val.id
            if isinstance(val, ast.Attribute):
                return val.attr
    return None


def _iter_producer_repair_kind_sites() -> list[ProducerRepairKindSite]:
    sites: list[ProducerRepairKindSite] = []
    for path in sorted(_GAME_ROOT.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if not isinstance(child, ast.Call):
                        continue
                    func = child.func
                    name: str | None = None
                    if isinstance(func, ast.Name):
                        name = func.id
                    elif isinstance(func, ast.Attribute):
                        name = func.attr
                    if name != "stamp_producer_repair_kind":
                        continue
                    sites.append(
                        ProducerRepairKindSite(
                            rel_path=rel,
                            function=node.name,
                            line=child.lineno or 0,
                            repair_kind=_repair_kind_from_call(child),
                        )
                    )
    return sites


def _iter_visibility_owner_bucket_write_sites() -> list[VisibilityOwnerBucketWriteSite]:
    sites: list[VisibilityOwnerBucketWriteSite] = []
    for path in sorted(_GAME_ROOT.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if not isinstance(child, ast.Subscript):
                        continue
                    sub = child.value
                    if not isinstance(sub, ast.Name) or sub.id != "meta":
                        continue
                    slice_node = child.slice
                    key: str | None = None
                    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                        key = slice_node.value
                    elif isinstance(slice_node, ast.Index) and isinstance(slice_node.value, ast.Constant):
                        key = slice_node.value.value if isinstance(slice_node.value.value, str) else None
                    if key != "visibility_fallback_owner_bucket":
                        continue
                    if not isinstance(child.ctx, ast.Store):
                        continue
                    sites.append(
                        VisibilityOwnerBucketWriteSite(
                            rel_path=rel,
                            function=node.name,
                            line=child.lineno or 0,
                        )
                    )
    return sites


def _iter_attach_realization_sites() -> list[AttachRealizationSite]:
    sites: list[AttachRealizationSite] = []
    for path in sorted(_GAME_ROOT.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if not isinstance(child, ast.Call):
                        continue
                    func = child.func
                    name: str | None = None
                    if isinstance(func, ast.Name):
                        name = func.id
                    elif isinstance(func, ast.Attribute):
                        name = func.attr
                    if name != "attach_realization_fallback_family":
                        continue
                    sites.append(
                        AttachRealizationSite(
                            rel_path=rel,
                            function=node.name,
                            line=child.lineno or 0,
                            family_marker=_family_marker_from_call(child),
                        )
                    )
    return sites


def _function_source(rel_path: str, function: str) -> str:
    path = _REPO_ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            segment = ast.get_source_segment(text, node)
            if segment is None:
                raise LookupError(f"could not extract source for {rel_path}:{function}")
            return segment
    raise LookupError(f"{function!r} not found in {rel_path}")


def _opening_stamper_present(src: str) -> bool:
    return any(
        marker in src
        for marker in (
            "stamp_opening_fallback_owner_bucket",
            "stamp_upstream_prepared_opening_producer_metadata",
        )
    )


def _sealed_stamper_present(src: str) -> bool:
    return "stamp_sealed_fallback_realization_family" in src or "sealed_fallback_owner_bucket" in src


def _retry_stamper_present(src: str) -> bool:
    return "stamp_retry_terminal_fallback_producer_metadata" in src


def _visibility_bucket_stamper_present(src: str) -> bool:
    return "stamp_visibility_fallback_owner_bucket_from_fields" in src


def _normalized_visibility_repair_kind(marker: str | None) -> str:
    token = (marker or "").strip()
    if token.startswith("PRODUCER_REPAIR_KIND_"):
        return token.removeprefix("PRODUCER_REPAIR_KIND_").lower()
    return token.lower()


def visibility_producer_stamp_pairing_errors() -> list[str]:
    """Ensure visibility-path producer repair kinds pair with bucket stamper helpers."""
    errors: list[str] = []
    for site in _iter_producer_repair_kind_sites():
        repair_kind = _normalized_visibility_repair_kind(site.repair_kind)
        if repair_kind not in _VISIBILITY_PRODUCER_REPAIR_KINDS:
            continue
        key: WritePathKey = (site.rel_path, site.function, "producer_repair_kind")
        if key in _VISIBILITY_PRODUCER_STAMP_EXEMPT:
            continue
        try:
            src = _function_source(site.rel_path, site.function)
        except LookupError as exc:
            errors.append(f"{site.rel_path}:{site.function}@{site.line}: {exc}")
            continue
        if not _visibility_bucket_stamper_present(src):
            errors.append(
                f"{site.rel_path}:{site.function}@{site.line}: {repair_kind!r} "
                "requires stamp_visibility_fallback_owner_bucket_from_fields in same function"
            )

    canonical_bucket_writers = {
        ("game/final_emission_meta.py", "stamp_visibility_fallback_owner_bucket_from_fields"),
        ("game/final_emission_visibility_fallback.py", "stamp_visibility_fallback_metadata"),
    }
    for site in _iter_visibility_owner_bucket_write_sites():
        writer_key = (site.rel_path, site.function)
        if writer_key in canonical_bucket_writers:
            continue
        key = (site.rel_path, site.function, "visibility_fallback_owner_bucket")
        if key in _VISIBILITY_PRODUCER_STAMP_EXEMPT:
            continue
        errors.append(
            f"{site.rel_path}:{site.function}@{site.line}: direct visibility_fallback_owner_bucket "
            "write must route through stamp_visibility_fallback_metadata or "
            "stamp_visibility_fallback_owner_bucket_from_fields"
        )
    return errors


def producer_stamp_pairing_errors() -> list[str]:
    """Ensure attach_realization_fallback_family producers pair with bucket stamper helpers."""
    errors: list[str] = []
    for site in _iter_attach_realization_sites():
        key: WritePathKey = (site.rel_path, site.function, "realization_fallback_family")
        if key in _ATTACH_REALIZATION_EXEMPT:
            continue
        try:
            src = _function_source(site.rel_path, site.function)
        except LookupError as exc:
            errors.append(f"{site.rel_path}:{site.function}@{site.line}: {exc}")
            continue

        marker = (site.family_marker or "").strip()
        if marker == "RETRY_TERMINAL_FALLBACK" and not _retry_stamper_present(src):
            errors.append(
                f"{site.rel_path}:{site.function}@{site.line}: RETRY_TERMINAL_FALLBACK "
                "requires stamp_retry_terminal_fallback_producer_metadata in same function"
            )
        if marker in {"GATE_TERMINAL_REPAIR", "STRICT_SOCIAL_DETERMINISTIC_FALLBACK"}:
            if marker == "GATE_TERMINAL_REPAIR" and not _sealed_stamper_present(src):
                errors.append(
                    f"{site.rel_path}:{site.function}@{site.line}: GATE_TERMINAL_REPAIR "
                    "requires sealed fallback bucket stamper in same function"
                )
        if marker in {"UPSTREAM_PREPARED_EMISSION", "LEGACY_DIEGETIC_FALLBACK"}:
            opening_context = any(
                token in src
                for token in (
                    "opening_fallback",
                    "opening_deterministic",
                    "scene_opening",
                    "build_upstream_prepared_opening_fallback_payload",
                )
            )
            if opening_context and not _opening_stamper_present(src):
                errors.append(
                    f"{site.rel_path}:{site.function}@{site.line}: opening fallback family "
                    "requires stamp_opening_fallback_owner_bucket or "
                    "stamp_upstream_prepared_opening_producer_metadata in same function"
                )
    return errors


def attach_realization_exempt_documentation() -> dict[WritePathKey, str]:
    """Return documented invariant exceptions for governance reporting."""
    return dict(_ATTACH_REALIZATION_EXEMPT)


def visibility_producer_stamp_exempt_documentation() -> dict[WritePathKey, str]:
    """Return documented BU9 visibility producer-stamp pairing exceptions."""
    return dict(_VISIBILITY_PRODUCER_STAMP_EXEMPT)


def visibility_fallback_write_path_inventory() -> dict[str, list[tuple[str, str, int]]]:
    """Return audited visibility fallback stamp/write call sites for BU9 reporting."""
    metadata_sites = [
        (site.rel_path, site.function, site.line)
        for site in _iter_producer_repair_kind_sites()
        if _normalized_visibility_repair_kind(site.repair_kind) in _VISIBILITY_PRODUCER_REPAIR_KINDS
    ]
    bucket_writes = [
        (site.rel_path, site.function, site.line) for site in _iter_visibility_owner_bucket_write_sites()
    ]
    return {
        "visibility_producer_repair_kind_sites": sorted(metadata_sites),
        "visibility_fallback_owner_bucket_writes": sorted(bucket_writes),
    }
