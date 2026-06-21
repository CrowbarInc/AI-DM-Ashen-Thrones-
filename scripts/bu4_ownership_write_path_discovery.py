"""Generate BU4 ownership write-path registry artifacts.

Read-only with respect to runtime behavior: parses Python with ``ast`` and writes audit data
under ``docs/audits``.
"""
from __future__ import annotations

import ast
import csv
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
TESTS = ROOT / "tests"
OUTPUT_MD = ROOT / "docs" / "audits" / "BU4_ownership_write_path_registry.md"
OUTPUT_CSV = ROOT / "docs" / "audits" / "BU4_ownership_write_paths.csv"

# Fields in scope for BU4 (production write-path enumeration).
OWNERSHIP_FIELDS: frozenset[str] = frozenset(
    {
        "owner_bucket",
        "opening_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "visibility_fallback_owner_bucket",
        "fallback_owner_bucket",
        "fallback_owner",
        "fallback_family",
        "fallback_family_used",
        "realization_fallback_family",
        "fallback_temporal_frame",
        "opening_fallback_authorship_source",
        "fallback_authorship_source",
        "fallback_selection_owner",
        "fallback_content_owner",
        "sanitizer_empty_fallback_owner",
        "sanitizer_strict_social_selection_owner",
        "sanitizer_strict_social_prose_owner",
        "sanitizer_empty_fallback_owner_trace_short",
        "sanitizer_strict_social_selection_owner_trace_short",
        "sanitizer_strict_social_prose_owner_trace_short",
        "speaker_attribution",
        "speaker_contract_enforcement",
        "speaker_contract_enforcement_reason",
        "fem_runtime_lineage_events",
        "fallback_provenance_trace",
        "producer_repair_kind",
    }
)

# Regex for kwargs / assignment outside easy AST subscript detection.
_FIELD_RE = re.compile(
    r"\b(" + "|".join(re.escape(f) for f in sorted(OWNERSHIP_FIELDS)) + r")\s*="
)


@dataclass
class WriteHit:
    module: str
    rel_path: str
    function: str
    field: str
    line: int
    mechanism: str
    writer_class: str
    schema_source: str
    notes: str


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT)
    return ".".join(rel.with_suffix("").parts)


# Curated production write paths not captured by AST subscript/regex alone.
CURATED_WRITERS: list[tuple[str, str, str, str, str, str]] = [
    # rel_path, function, field, writer_class, schema_source, notes
    (
        "game/realization_provenance.py",
        "attach_realization_fallback_family",
        "realization_fallback_family",
        "FEM schema writer",
        "game.realization_provenance + game.realization_authority",
        "Canonical governed-family stamp helper",
    ),
    (
        "game/final_emission_replay_projection.py",
        "build_fem_runtime_lineage_events",
        "fallback_owner_bucket",
        "replay projection writer",
        "game.final_emission_replay_projection",
        "Projects fallback_owner_bucket on lineage events via make_runtime_lineage_event",
    ),
    (
        "game/final_emission_replay_projection.py",
        "build_fem_runtime_lineage_events",
        "fallback_authorship_source",
        "replay projection writer",
        "game.final_emission_replay_projection",
        "Projects opening fallback_authorship_source onto lineage events",
    ),
    (
        "game/final_emission_replay_projection.py",
        "build_fem_runtime_lineage_events",
        "fallback_selection_owner",
        "replay projection writer",
        "game.final_emission_replay_projection",
        "Split-owner projection from _fallback_split_owners_for_kind",
    ),
    (
        "game/final_emission_replay_projection.py",
        "build_fem_runtime_lineage_events",
        "fallback_content_owner",
        "replay projection writer",
        "game.final_emission_replay_projection",
        "Split-owner projection from _fallback_split_owners_for_kind",
    ),
    (
        "game/runtime_lineage_telemetry.py",
        "make_runtime_lineage_event",
        "fallback_owner_bucket",
        "replay projection writer",
        "game.runtime_lineage_telemetry",
        "Lineage event dict schema field",
    ),
    (
        "game/runtime_lineage_telemetry.py",
        "make_runtime_lineage_event",
        "fallback_authorship_source",
        "replay projection writer",
        "game.runtime_lineage_telemetry",
        "Lineage event dict schema field",
    ),
    (
        "game/runtime_lineage_telemetry.py",
        "make_runtime_lineage_event",
        "fallback_selection_owner",
        "replay projection writer",
        "game.runtime_lineage_telemetry",
        "Lineage event dict schema field",
    ),
    (
        "game/runtime_lineage_telemetry.py",
        "make_runtime_lineage_event",
        "fallback_content_owner",
        "replay projection writer",
        "game.runtime_lineage_telemetry",
        "Lineage event dict schema field",
    ),
    (
        "game/social_exchange_emission.py",
        "stamp_strict_social_deterministic_fallback_family",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "Strict-social deterministic fallback family stamp",
    ),
    (
        "game/social_exchange_emission.py",
        "_structured_fact_emission_details",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "attach_realization_fallback_family on structured fact emission details",
    ),
    (
        "game/gm_retry.py",
        "_attach_retry_terminal_family",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "Retry terminal fallback stamps gm_output/metadata/_final_emission_meta",
    ),
    (
        "game/api.py",
        "_synthetic_manual_play_gpt_budget_gm",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "Manual-play GPT budget exhausted synthetic GM metadata",
    ),
    (
        "game/api.py",
        "_build_gpt_narration_from_authoritative_state",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "Upstream API fast-fallback path stamps metadata after force_terminal_retry_fallback",
    ),
    (
        "game/gm.py",
        "call_gpt",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "GPT budget/provider failure fallback metadata",
    ),
    (
        "game/upstream_response_repairs.py",
        "maybe_attach_upstream_prepared_opening_fallback_payload",
        "realization_fallback_family",
        "debug-only writer",
        "game.realization_provenance",
        "Upstream prepared opening payload composition",
    ),
    (
        "game/final_emission_response_type.py",
        "enforce_response_type_contract",
        "realization_fallback_family",
        "debug-only writer",
        "game.realization_provenance",
        "attach_realization_fallback_family on response-type debug",
    ),
    (
        "game/final_emission_sealed_fallback.py",
        "stamp_sealed_fallback_realization_family",
        "realization_fallback_family",
        "fallback selection writer",
        "game.realization_provenance",
        "Sealed route realization family + owner bucket",
    ),
    (
        "game/fallback_provenance_debug.py",
        "record_final_emission_gate_exit",
        "fallback_provenance_trace",
        "debug-only writer",
        "game.final_emission_meta.FEM_FALLBACK_PROVENANCE_TRACE_KEY",
        "Packages upstream fast-fallback provenance trace onto FEM",
    ),
    (
        "game/diegetic_fallback_narration.py",
        "fallback_template_metadata",
        "fallback_family_used",
        "fallback selection writer",
        "game.diegetic_fallback_narration",
        "Diegetic template → fallback_family_used taxonomy",
    ),
    (
        "game/final_emission_opening_fallback.py",
        "build_upstream_prepared_opening_composition_meta",
        "opening_fallback_authorship_source",
        "fallback selection writer",
        "game.final_emission_opening_fallback",
        "Upstream composition meta authorship stamp (success path)",
    ),
    (
        "game/final_emission_opening_fallback.py",
        "build_opening_fallback_result_meta",
        "opening_fallback_authorship_source",
        "fallback selection writer",
        "game.final_emission_opening_fallback",
        "Result meta may include authorship when mirrored from upstream",
    ),
    (
        "game/final_emission_meta.py",
        "normalize_fem_for_replay_observation",
        "fem_runtime_lineage_events",
        "replay projection writer",
        "game.final_emission_replay_projection.build_fem_runtime_lineage_events",
        "Read-side FEM packaging adds projected lineage sibling field",
    ),
    (
        "game/final_emission_response_type.py",
        "enforce_response_type_contract",
        "opening_fallback_owner_bucket",
        "FEM schema writer",
        "game.final_emission_meta.stamp_opening_fallback_owner_bucket",
        "Stamps opening bucket on response-type debug before FEM merge",
    ),
    (
        "game/final_emission_meta.py",
        "stamp_retry_terminal_fallback_producer_metadata",
        "opening_fallback_owner_bucket",
        "FEM schema writer",
        "game.final_emission_meta",
        "Retry terminal fallback owner bucket stamper paired with attach_realization_fallback_family",
    ),
    (
        "game/final_emission_meta.py",
        "stamp_upstream_prepared_opening_producer_metadata",
        "opening_fallback_owner_bucket",
        "FEM schema writer",
        "game.final_emission_meta",
        "Upstream-prepared opening owner bucket stamper paired with opening payload composition",
    ),
    (
        "game/output_sanitizer.py",
        "_mark_sanitizer_empty_fallback",
        "sanitizer_empty_fallback_owner_trace_short",
        "fallback selection writer",
        "game.final_emission_ownership_schema (trace short companion)",
        "Legacy short companion stamped alongside canonical sanitizer_empty_fallback_owner",
    ),
    (
        "game/output_sanitizer.py",
        "_mark_sanitizer_strict_social_fallback",
        "sanitizer_strict_social_selection_owner_trace_short",
        "fallback selection writer",
        "game.final_emission_ownership_schema (trace short companion)",
        "Legacy short companion stamped alongside canonical strict-social selection owner",
    ),
    (
        "game/output_sanitizer.py",
        "_mark_sanitizer_strict_social_fallback",
        "sanitizer_strict_social_prose_owner_trace_short",
        "fallback selection writer",
        "game.final_emission_ownership_schema (trace short companion)",
        "Legacy short companion stamped alongside canonical strict-social prose owner",
    ),
]


def _classify(rel_path: str, function: str, field: str) -> tuple[str, str, str]:
    """Return (writer_class, schema_source, notes)."""
    m = rel_path.replace("/", ".").replace(".py", "")
    fn = function

    if rel_path.startswith("tests/"):
        return (
            "test/governance writer",
            "tests/helpers/attribution_contract.py or golden_replay_projection",
            "Read-side inventory / governance; not production FEM stamping",
        )

    if rel_path == "game/final_emission_replay_projection.py":
        if field in {"fallback_owner_bucket", "fallback_authorship_source", "fallback_selection_owner", "fallback_content_owner"}:
            return (
                "replay projection writer",
                "game.final_emission_replay_projection + game.runtime_lineage_telemetry",
                "Projects lineage events from finalized FEM; does not stamp FEM owner buckets",
            )
        if fn == "build_fem_runtime_lineage_events":
            return (
                "replay projection writer",
                "game.final_emission_replay_projection",
                "Builds fem_runtime_lineage_events list from FEM",
            )

    if rel_path == "game/runtime_lineage_telemetry.py":
        return (
            "replay projection writer",
            "game.runtime_lineage_telemetry",
            "Canonical lineage event dict schema (make_runtime_lineage_event)",
        )

    if rel_path == "game/speaker_contract_enforcement.py":
        return (
            "speaker contract writer",
            "game.speaker_contract_enforcement",
            "Writes emission_debug.speaker_contract_enforcement payload",
        )

    if rel_path == "game/output_sanitizer.py":
        return (
            "fallback selection writer",
            "game.final_emission_meta (bucket constants) + trace split-owner literals",
            "Sanitizer trace stamps; copied to FEM via apply_sanitizer_producer_attribution_to_fem",
        )

    if rel_path in {
        "game/final_emission_sealed_fallback.py",
        "game/final_emission_visibility_fallback.py",
        "game/final_emission_opening_fallback.py",
    }:
        return (
            "fallback selection writer",
            "game.final_emission_meta (owner-bucket registry)",
            "Route-level fallback selection stamps owner buckets / diegetic family on FEM",
        )

    if rel_path == "game/final_emission_meta.py":
        if fn.startswith("stamp_") or fn == "apply_sanitizer_producer_attribution_to_fem":
            return (
                "FEM schema writer",
                "game.final_emission_meta",
                "Canonical stamp/copy helpers for owner buckets and sanitizer attribution",
            )
        if fn in {"apply_opening_fallback_projection_fields", "opening_fallback_projection_fields"}:
            return (
                "FEM schema writer",
                "game.final_emission_meta (OPENING_FALLBACK_PROJECTION_FIELDS)",
                "Metadata-only projection copy; authorship stamped upstream",
            )
        return (
            "FEM schema writer",
            "game.final_emission_meta",
            "FEM packaging / registry surface",
        )

    if rel_path == "game.realization_provenance.py":
        return (
            "FEM schema writer",
            "game.realization_provenance + game.realization_authority",
            "Canonical realization_fallback_family stamp",
        )

    if rel_path == "game/final_emission_fem_assembly.py":
        return (
            "FEM schema writer",
            "game.final_emission_meta + game.realization_provenance",
            "Terminal FEM merge; copies strict-social / speaker reason fields",
        )

    if rel_path in {
        "game/final_emission_response_type.py",
        "game/final_emission_validators.py",
        "game/final_emission_generic_exit.py",
        "game/upstream_response_repairs.py",
    }:
        return (
            "debug-only writer",
            "game.final_emission_meta + game.realization_provenance",
            "Response-type debug / upstream composition; merged into FEM observability",
        )

    if rel_path in {
        "game/social_exchange_emission.py",
        "game/gm_retry.py",
        "game/api.py",
        "game/gm.py",
    }:
        return (
            "fallback selection writer",
            "game.realization_provenance",
            "attach_realization_fallback_family at social/retry/API fast-fallback paths",
        )

    if rel_path == "game/diegetic_fallback_narration.py":
        return (
            "fallback selection writer",
            "game.diegetic_fallback_narration",
            "Diegetic fallback_family_used taxonomy (template metadata)",
        )

    if rel_path == "game/fallback_provenance_debug.py":
        return (
            "debug-only writer",
            "game.final_emission_meta (FEM_FALLBACK_PROVENANCE_TRACE_KEY)",
            "Packages fallback_provenance_trace onto FEM",
        )

    if "emission_debug" in fn or field == "speaker_contract_enforcement":
        return (
            "debug-only writer",
            "layer-specific emission_debug merge",
            "Patches metadata.emission_debug before FEM finalize",
        )

    return (
        "FEM schema writer",
        "game.final_emission_meta (review)",
        "Unclassified production writer — review in BU5",
    )


class WriteVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.module = _module_name(path)
        self.func_stack: list[str] = ["<module>"]
        self.hits: list[WriteHit] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def _record(self, field: str, line: int, mechanism: str) -> None:
        rel_path = str(self.path.relative_to(ROOT)).replace("\\", "/")
        fn = self.func_stack[-1] if len(self.func_stack) > 1 else self.func_stack[0]
        writer_class, schema_source, notes = _classify(rel_path, fn, field)
        self.hits.append(
            WriteHit(
                module=self.module,
                rel_path=rel_path,
                function=fn,
                field=field,
                line=line,
                mechanism=mechanism,
                writer_class=writer_class,
                schema_source=schema_source,
                notes=notes,
            )
        )

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.ctx, ast.Store):
            key = self._slice_key(node.slice)
            if key in OWNERSHIP_FIELDS:
                self._record(key, node.lineno, "subscript_store")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Subscript):
            key = self._slice_key(node.target.slice)
            if key in OWNERSHIP_FIELDS:
                self._record(key, node.lineno, "annotated_subscript")
        self.generic_visit(node)

    def _slice_key(self, slice_node: ast.expr) -> str | None:
        if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
            return slice_node.value
        return None

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "update":
            if node.args:
                self._dict_update_keys(node.args[0], node.lineno)
        self.generic_visit(node)

    def _dict_update_keys(self, node: ast.expr, line: int) -> None:
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if key.value in OWNERSHIP_FIELDS:
                        self._record(key.value, line, "dict_update")


def _function_at_line(tree: ast.Module, line: int) -> str:
    best = "<module>"
    best_start = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.lineno <= line and node.lineno >= best_start:
                best = node.name
                best_start = node.lineno
    return best


def _docstring_line_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            doc = ast.get_docstring(node, clean=False)
            if not doc:
                continue
            start = getattr(node, "lineno", 1)
            if node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    if isinstance(first.value.value, str):
                        end = first.end_lineno or first.lineno
                        ranges.append((start, end))
    return ranges


def _line_in_docstring(line: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in ranges)


def scan_file(path: Path) -> list[WriteHit]:
    rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []
    visitor = WriteVisitor(path)
    visitor.visit(tree)
    doc_ranges = _docstring_line_ranges(tree)
    lines = source.splitlines()
    seen = {(h.field, h.line, h.function) for h in visitor.hits}
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        if _line_in_docstring(i, doc_ranges):
            continue
        if not _FIELD_RE.search(line):
            continue
        for match in _FIELD_RE.finditer(line):
            field = match.group(1)
            fn = _function_at_line(tree, i)
            key = (field, i, fn)
            if key in seen:
                continue
            writer_class, schema_source, notes = _classify(rel_path, fn, field)
            visitor.hits.append(
                WriteHit(
                    module=visitor.module,
                    rel_path=rel_path,
                    function=fn,
                    field=field,
                    line=i,
                    mechanism="assignment_or_kwarg",
                    writer_class=writer_class,
                    schema_source=schema_source,
                    notes=notes,
                )
            )
            seen.add(key)
    return visitor.hits


def scan_tree(root: Path, prefix: str) -> list[WriteHit]:
    hits: list[WriteHit] = []
    for path in sorted(root.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        hits.extend(scan_file(path))
    return hits


def dedupe_hits(hits: list[WriteHit]) -> list[WriteHit]:
    """Collapse duplicate field hits in same function to one row."""
    best: dict[tuple[str, str, str], WriteHit] = {}
    for h in hits:
        key = (h.rel_path, h.function, h.field)
        existing = best.get(key)
        if existing is None:
            best[key] = h
            continue
        if existing.mechanism == "curated":
            continue
        if h.mechanism == "curated":
            best[key] = h
            continue
        if h.line < existing.line:
            best[key] = h
    return sorted(best.values(), key=lambda x: (x.rel_path, x.line or 9999, x.field))


def production_writers(hits: list[WriteHit]) -> list[WriteHit]:
    return [h for h in hits if h.rel_path.startswith("game/")]


def write_csv(hits: list[WriteHit]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "module",
                "rel_path",
                "function",
                "field",
                "line",
                "mechanism",
                "writer_class",
                "schema_source",
                "notes",
            ],
        )
        writer.writeheader()
        for h in hits:
            writer.writerow(
                {
                    "module": h.module,
                    "rel_path": h.rel_path,
                    "function": h.function,
                    "field": h.field,
                    "line": h.line,
                    "mechanism": h.mechanism,
                    "writer_class": h.writer_class,
                    "schema_source": h.schema_source,
                    "notes": h.notes,
                }
            )


def literal_drift_scan() -> list[tuple[str, int, str, str]]:
    """Find scattered bucket/family string literals in game/ outside registry modules."""
    bucket_literals = re.compile(
        r'"((?:upstream-prepared|sealed-gate|strict-social(?:-sealed|-visibility)?|opening-visibility|unknown-(?:none|ambiguous)|retry))"'
    )
    registry_modules = {
        "game/final_emission_meta.py",
        "game/final_emission_sealed_fallback.py",
        "game/final_emission_visibility_fallback.py",
        "game/final_emission_replay_projection.py",
        "game/realization_authority.py",
        "game/realization_provenance.py",
    }
    findings: list[tuple[str, int, str, str]] = []
    for path in sorted(GAME.rglob("*.py")):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel in registry_modules:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            m = bucket_literals.search(line)
            if m:
                findings.append((rel, i, m.group(1), line.strip()[:100]))
    return findings


def render_markdown(prod: list[WriteHit], test_hits: list[WriteHit], drift: list[tuple[str, int, str, str]]) -> str:
    by_class: dict[str, list[WriteHit]] = {}
    for h in prod:
        by_class.setdefault(h.writer_class, []).append(h)

    by_field: dict[str, int] = {}
    for h in prod:
        by_field[h.field] = by_field.get(h.field, 0) + 1

    unique_functions = len({(h.rel_path, h.function) for h in prod})
    unique_modules = len({h.rel_path for h in prod})
    prod_modules = sorted({h.rel_path for h in prod})

    lines = [
        "# BU4 — Ownership Write-Path Registry",
        "",
        "Date: 2026-06-20",
        "",
        "## Executive summary",
        "",
        f"BU4 enumerates **{len(prod)}** deduplicated production write-path rows across "
        f"**{unique_modules}** `game/` modules and **{unique_functions}** functions. "
        "Owner buckets, fallback families, authorship sources, split-owner lineage fields, "
        "and replay-visible lineage projection are still authored through multiple surfaces, "
        "but `game.final_emission_meta` now holds the canonical owner-bucket vocabulary (Cycle BK1) "
        "and `game.final_emission_replay_projection` owns read-side lineage projection (Cycle AO5).",
        "",
        "No runtime behavior was changed in BU4. This block is discovery + registry only.",
        "",
        "## Method",
        "",
        "`scripts/bu4_ownership_write_path_discovery.py` parses `game/` and `tests/` with AST plus "
        "a field-name assignment regex. Rows are deduplicated per `(file, function, field)`. "
        "Writer classification is heuristic (module + function); see CSV for per-row detail.",
        "",
        "Machine-readable inventory: `docs/audits/BU4_ownership_write_paths.csv`.",
        "",
        "## Production writer counts by class",
        "",
        "| Writer class | Rows | Modules |",
        "|---|---:|---:|",
    ]
    for cls in sorted(by_class):
        mods = len({h.rel_path for h in by_class[cls]})
        lines.append(f"| {cls} | {len(by_class[cls])} | {mods} |")

    lines.extend(
        [
            "",
            "## Production modules with ownership writes",
            "",
        ]
    )
    for rel in prod_modules:
        module_hits = [h for h in prod if h.rel_path == rel]
        fields = sorted({h.field for h in module_hits})
        lines.append(f"- `{rel}` — {len(module_hits)} row(s): {', '.join(f'`{f}`' for f in fields)}")

    lines.extend(
        [
            "",
            "## Production writer counts by field",
            "",
            "| Field | Writers (deduped rows) |",
            "|---|---:|",
        ]
    )
    for field, count in sorted(by_field.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{field}` | {count} |")

    lines.extend(
        [
            "",
            "## Schema vocabulary surfaces (read/consume, not necessarily write)",
            "",
            "| Surface | Role |",
            "|---|---|",
            "| `game.final_emission_meta` | Owner-bucket constants, stamp helpers, opening projection field registry, sanitizer→FEM copy |",
            "| `game.final_emission_replay_projection` | `build_fem_runtime_lineage_events`, split-owner maps, fallback_kind taxonomy |",
            "| `game.runtime_lineage_telemetry` | Lineage event dict schema (`make_runtime_lineage_event`) |",
            "| `game.realization_provenance` | `realization_fallback_family` stamp normalizer |",
            "| `game.realization_authority` | Governed family token constants |",
            "| `game.diegetic_fallback_narration` | Diegetic `fallback_family_used` template taxonomy |",
            "| `tests/helpers/attribution_contract.py` | BS semantic-replacement attribution vocabulary (read-side inventory) |",
            "| `tests/helpers/replacement_attribution_inventory.py` | Cross-source attribution record builder (read-side) |",
            "",
            "## Top schema drift risks",
            "",
        ]
    )

    drift_risks = [
        (
            "Dual fallback-family vocabularies",
            "`fallback_family_used` (diegetic) vs `realization_fallback_family` (governed) are stamped "
            "by different modules (`diegetic_fallback_narration`, `realization_provenance`, route owners). "
            "Golden replay projects diegetic-first; lineage uses path-specific `fallback_kind`.",
        ),
        (
            "Split-owner literals outside replay projection",
            "`output_sanitizer` stamps `sanitizer_strict_social_selection_owner=\"output_sanitizer\"` and "
            "`sanitizer_strict_social_prose_owner=\"strict_social_emission\"` as short names; "
            "`final_emission_replay_projection` maps these to canonical `game.*` module owners.",
        ),
        (
            "Owner-bucket assignment is distributed",
            "Opening buckets via `stamp_opening_fallback_owner_bucket` (read-side mapper), sealed via "
            "`stamp_sealed_fallback_realization_family`, visibility via `stamp_visibility_fallback_metadata` "
            "— constants live in `final_emission_meta` but write paths remain per-route.",
        ),
        (
            "Compatibility-local authorship residue",
            "`OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES` in `final_emission_meta` maps "
            "retired tokens to `unknown-ambiguous`; never written in production but still in read-side mapper.",
        ),
        (
            "emission_debug vs FEM lane duplication",
            "Speaker contract, response-type debug, and layer merges write `metadata.emission_debug` keys "
            "that are later copied or projected into FEM / lineage — two packaging surfaces for same semantics.",
        ),
        (
            "Scattered bucket string literals",
            f"{len(drift)} literal bucket hits outside primary registry modules (see drift table below).",
        ),
    ]
    for title, detail in drift_risks:
        lines.append(f"- **{title}** — {detail}")

    lines.extend(
        [
            "",
            "## Scattered bucket literals (outside registry modules)",
            "",
            "| File | Line | Literal |",
            "|---|---:|---|",
        ]
    )
    for rel, line_no, literal, _ in drift[:25]:
        lines.append(f"| `{rel}` | {line_no} | `{literal}` |")
    if len(drift) > 25:
        lines.append(f"| … | | +{len(drift) - 25} more (grep game/ for bucket strings) |")

    lines.extend(
        [
            "",
            "## Recommended BU5 block",
            "",
            "1. **Narrow ownership schema module** — export owner-bucket constants + split-owner module "
            "tokens from one import surface (re-home from `final_emission_meta` / `replay_projection` without "
            "behavior change).",
            "2. **Unify sanitizer trace owner literals** — replace short names with canonical "
            "`game.*` owners at write time (or single normalizer used by sanitizer + replay projection).",
            "3. **Producer stamp convergence** — ensure every fallback selection path calls one of "
            "`stamp_opening_fallback_owner_bucket`, `stamp_sealed_fallback_realization_family`, "
            "`stamp_visibility_fallback_metadata` / `stamp_visibility_fallback_owner_bucket_from_fields` "
            "before FEM finalize (audit shows gaps on retry/API-only `attach_realization_fallback_family` paths).",
            "4. **Governance lock** — extend `tests/test_ownership_registry.py` with BU4 write-path parity "
            "test mirroring CSV inventory (similar to BN lazy-import guards).",
            "",
            "## Test / governance writers (summary)",
            "",
            f"Deduplicated test/helper rows: **{len(test_hits)}** across "
            f"{len({h.rel_path for h in test_hits})} files. Primary surfaces: "
            "`tests/helpers/replacement_attribution_inventory.py`, "
            "`tests/helpers/opening_fallback_evidence.py`, "
            "`tests/failure_classification_contract.py`, golden replay fixtures.",
            "",
        ]
    )
    return "\n".join(lines)


def curated_hits() -> list[WriteHit]:
    hits: list[WriteHit] = []
    for rel_path, function, field, writer_class, schema_source, notes in CURATED_WRITERS:
        module = rel_path.replace("/", ".").replace(".py", "")
        hits.append(
            WriteHit(
                module=module,
                rel_path=rel_path,
                function=function,
                field=field,
                line=0,
                mechanism="curated",
                writer_class=writer_class,
                schema_source=schema_source,
                notes=notes,
            )
        )
    return hits


def main() -> None:
    all_hits = scan_tree(GAME, "game") + scan_tree(TESTS, "tests") + curated_hits()
    deduped = dedupe_hits(all_hits)
    prod = [h for h in deduped if h.rel_path.startswith("game/")]
    test_hits = [h for h in deduped if h.rel_path.startswith("tests/")]
    drift = literal_drift_scan()
    write_csv(deduped)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(render_markdown(prod, test_hits, drift), encoding="utf-8")
    print(f"Wrote {OUTPUT_CSV} ({len(deduped)} rows)")
    print(f"Wrote {OUTPUT_MD}")
    print(f"Production writers: {len(prod)} rows, {len({h.rel_path for h in prod})} modules")


if __name__ == "__main__":
    main()
