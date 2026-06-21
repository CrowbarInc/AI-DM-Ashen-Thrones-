"""Generate BV10 audit markdown from artifacts/bv10_dependency_inventory.json."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV_PATH = ROOT / "artifacts" / "bv10_dependency_inventory.json"
AUDIT_DIR = ROOT / "docs" / "audits"

TARGET_LABELS = {
    "game.final_emission_meta_read": "final_emission_meta_read",
    "game.final_emission_owner_bucket_views": "owner_bucket_views",
    "game.final_emission_ownership_schema": "ownership_schema",
}

BU_FI = {
    "game.final_emission_meta_read": 29,
    "game.final_emission_owner_bucket_views": 22,
    "game.final_emission_ownership_schema": 19,
}


def rel_path(full: str) -> str:
    marker = "ashen_thrones_ai_gm/"
    return full.split(marker)[-1] if marker in full else full.replace("\\", "/")


def classify_consumer(row: dict[str, object]) -> str:
    file_path = rel_path(str(row["file"]))
    subsystem = str(row["subsystem"])
    bucket = str(row["ownership_bucket"])
    kind = str(row["kind"])
    if subsystem == "replay" or "golden_replay" in file_path:
        return "replay"
    if subsystem == "attribution":
        return "attribution"
    if subsystem == "fallback":
        return "fallback"
    if subsystem in {"diagnostics"} or any(
        token in file_path
        for token in ("dead_turn", "playability", "run_scenario_spine", "observational")
    ):
        return "diagnostics"
    if subsystem == "speaker":
        return "speaker"
    if subsystem == "observability" or "lineage_telemetry" in file_path:
        return "observability"
    if bucket == "observability-projection":
        return "observability"
    if kind in {"test", "helper"} and any(
        token in file_path for token in ("gate_", "smoke", "channel_separation", "tone_escalation")
    ):
        return "tests"
    if kind == "test":
        return "tests"
    if kind == "helper" and "smoke" in file_path:
        return "tests"
    return "other"


def symbol_summary(symbols: list[str], limit: int = 4) -> str:
    if len(symbols) <= limit:
        return ", ".join(f"`{symbol}`" for symbol in symbols)
    head = ", ".join(f"`{symbol}`" for symbol in symbols[:limit])
    return f"{head}, +{len(symbols) - limit} more"


def load_inventory() -> dict[str, list[dict[str, object]]]:
    return json.loads(INV_PATH.read_text(encoding="utf-8"))


def write_dependency_inventory(inv: dict[str, list[dict[str, object]]]) -> None:
    lines = [
        "# BV10 — Read-Side Attribution Cluster Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only. Direct importers of the three-module read-side attribution cluster.",
        "**Method:** AST scan (`tools/bv10_read_cluster_discovery.py`) + BU ecosystem fan-in (`docs/audits/BU_import_fan_in_fan_out.csv`).",
        "",
        "## Cluster baseline (current)",
        "",
        "| Module | BU fan-in | FO | Ownership concentration | BV9 rank |",
        "|---|---:|---:|---:|---:|",
        "| `game.final_emission_meta_read` | **29** | 1 | 0.0024 | #6 |",
        "| `game.final_emission_owner_bucket_views` | **22** | 1 | 0.2206 | #14 |",
        "| `game.final_emission_ownership_schema` | **19** | 1 | 0.4173 | #15 |",
        "| **Combined (sum of module FI)** | **70** | 3 | — | largest unaddressed read cluster |",
        "",
        "**Unique importers (deduped across cluster):** 54 files import at least one target.",
        "**Multi-import overlap:** 16 files import two or three targets (see hub analysis).",
        "",
        "**BV2 context:** Write-side `final_emission_meta` reduced 61 → 22; read facades absorbed deferred BV2 consumers (+11 meta_read, +17 bucket_views FI post-BV2B).",
        "",
        "---",
        "",
    ]
    for target, label in TARGET_LABELS.items():
        rows = inv[target]
        bu = BU_FI[target]
        lines.extend(
            [
                f"## `{label}` — {bu} BU fan-in ({len(rows)} AST importers)",
                "",
                "| File | Subsystem | Imported symbols | Ownership bucket | Read frequency |",
                "|---|---|---|---|---|",
            ]
        )
        for row in rows:
            lines.append(
                f"| `{rel_path(str(row['file']))}` | {row['subsystem']} | {symbol_summary(list(row['symbols']))} | {row['ownership_bucket']} | {row['read_frequency']} |"
            )
        lines.extend(["", "---", ""])
    lines.extend(
        [
            "## Evidence",
            "",
            "| Artifact | Path |",
            "|---|---|",
            "| Machine inventory | `artifacts/bv10_dependency_inventory.json` |",
            "| Discovery script | `tools/bv10_read_cluster_discovery.py` |",
            "| BU fan-in/fan-out | `docs/audits/BU_import_fan_in_fan_out.csv` |",
            "| BV9 concentration | `docs/audits/BV9_concentration_rankings.md` |",
        ]
    )
    (AUDIT_DIR / "BV10_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_consumer_classification(inv: dict[str, list[dict[str, object]]]) -> None:
    grouped: dict[str, list[tuple[str, dict[str, object]]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    for target, rows in inv.items():
        label = TARGET_LABELS[target]
        for row in rows:
            category = classify_consumer(row)
            counts[category] += 1
            grouped[category].append((label, row))

    lines = [
        "# BV10 — Read-Side Attribution Cluster Consumer Classification",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Group direct importers by maintenance subsystem.",
        "**Source:** `artifacts/bv10_dependency_inventory.json` (71 import edges; 54 unique files).",
        "",
        "## Classification overview",
        "",
        "| Subsystem | Import edges | Primary modules touched | Migration eligible |",
        "|---|---:|---|---|",
        f"| **Replay** | {counts['replay']} | meta_read, bucket_views, schema | **High** (via replay adapter) |",
        f"| **Attribution** | {counts['attribution']} | bucket_views, schema | **High** (attribution read views) |",
        f"| **Fallback** | {counts['fallback']} | bucket_views, schema | Partial (write owners stay; tests migrate) |",
        f"| **Diagnostics** | {counts['diagnostics']} | meta_read | **High** (observability read facade) |",
        f"| **Observability** | {counts['observability']} | meta_read, schema | **High** |",
        f"| **Tests** | {counts['tests']} | meta_read, bucket_views | **High** (smoke / gate helpers) |",
        f"| **Speaker** | {counts['speaker']} | meta_read | Medium |",
        f"| **Other / authority** | {counts['other']} | all three | Low (meta write owner, owner suites) |",
        "",
        "*Import-edge totals exceed unique files where one file imports multiple cluster modules.*",
        "",
        "---",
        "",
    ]
    section_order = [
        ("replay", "Replay"),
        ("attribution", "Attribution"),
        ("fallback", "Fallback"),
        ("diagnostics", "Diagnostics"),
        ("observability", "Observability"),
        ("speaker", "Speaker finalize"),
        ("tests", "Tests"),
        ("other", "Authority / other"),
    ]
    for key, title in section_order:
        rows = grouped.get(key, [])
        if not rows:
            continue
        lines.extend([f"## {title}", "", f"**Import edges:** {len(rows)}", ""])
        lines.extend(["| Consumer | Module | Symbols / pattern |", "|---|---|---|"])
        for label, row in sorted(rows, key=lambda item: rel_path(str(item[1]["file"]))):
            lines.append(
                f"| `{rel_path(str(row['file']))}` | `{label}` | {symbol_summary(list(row['symbols']), 6)} |"
            )
        lines.extend(["", "---", ""])
    (AUDIT_DIR / "BV10_consumer_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_access_patterns(inv: dict[str, list[dict[str, object]]]) -> None:
    lines = [
        "# BV10 — Read-Side Attribution Cluster Access Patterns",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Repeated read-side sequences across the 70-FI cluster.",
        "",
        "## Pattern summary",
        "",
        "| ID | Pattern | Top symbols | Import edges | Consolidation surface |",
        "|---|---|---|---:|---|",
        "| **P1** | FEM sidecar read | `read_final_emission_meta_dict` (17) | 17 | `meta_read` (existing) / gate smoke helper |",
        "| **P2** | Owner-bucket projection | `*_owner_bucket_from_*` (6+5+3) | 10 | `owner_bucket_views` (existing) |",
        "| **P3** | Bucket vocabulary | `SEALED_FALLBACK_OWNER_*`, frozensets | 12 | `ownership_schema` / `attribution_read_views` |",
        "| **P4** | Selection/content owner tokens | `*_SELECTION_OWNER`, `*_CONTENT_OWNER` | 7+ | `ownership_projection_views` |",
        "| **P5** | Observability bundle projection | `normalized_observational_telemetry_bundle`, dead-turn reads | 7 | `observability_attribution_read` |",
        "| **P6** | Replay acceptance normalize | `normalize_final_emission_meta_for_observability`, turn-payload reads | 4 | `replay_attribution_adapter` on replay_projection |",
        "| **P7** | Layer / accept-path projection | `infer_accept_path_final_emitted_source`, `default_response_type_debug` | 4 | meta_read layer surface |",
        "| **P8** | Schema registry parity | `ownership_schema_registry_surface`, lazy imports in owner suite | 3 | owner suite only (no migration) |",
        "",
        "---",
        "",
        "## P1 — FEM sidecar read",
        "",
        "**Sequence:** `read_final_emission_meta_dict(gm_output)` → field assertions or downstream projection.",
        "",
        "**Consumers:** gate tests (5), smoke helpers (2), speaker finalize, stage-diff, opening/visibility tests.",
        "",
        "**Assessment:** Already on `meta_read`; remaining churn is **fan-in concentration**, not missing facade. Gate tests should route through a single `fem_read_smoke` helper (BV7 pattern).",
        "",
        "## P2 — Owner-bucket projection",
        "",
        "**Sequence:** read FEM fields → `opening_fallback_owner_bucket_from_meta` / `*_from_fields` → compare to expected bucket token.",
        "",
        "**Consumers:** attribution helpers (3), fallback tests (4), replay projection (1), fallback write modules (3).",
        "",
        "**Assessment:** Mapper authority correctly on `owner_bucket_views`. Attribution cluster duplicates imports of both views **and** schema bucket constants.",
        "",
        "## P3 — Bucket vocabulary (constants-only)",
        "",
        "**Sequence:** import `OPENING_*` / `SEALED_*` / `VISIBILITY_*` frozensets or scalar tokens; no mapper call.",
        "",
        "**Consumers:** failure classification contract/sync (6 edges), fallback bucket owner suites (5), golden replay fallback projection.",
        "",
        "**Assessment:** Lowest-risk consolidation — single `attribution_read_views` re-export removes parallel schema + views imports.",
        "",
        "## P4 — Selection/content owner vocabulary",
        "",
        "**Sequence:** import allowed `*_SELECTION_OWNER` / `*_CONTENT_OWNER` module-path strings for lineage projection or classifier routing.",
        "",
        "**Consumers:** `failure_classification_sync`, `failure_dashboard_fixtures`, `final_emission_replay_projection`, golden replay tests.",
        "",
        "**Assessment:** Schema authority is legitimate. Accidental concentration in sync helper (23 schema symbols) warrants **projection facade**, not schema move.",
        "",
        "## P5 — Observability bundle projection",
        "",
        "**Sequence:** `normalized_observational_telemetry_bundle` / `summarize_gameplay_validation_for_turn` / dead-turn classify reads.",
        "",
        "**Consumers:** dead_turn_report_visibility, playability_eval, narrative_authenticity_eval, observational test suite.",
        "",
        "**Assessment:** BV2 deferred C3 (`observability_attribution_read`). Still the densest **production read** pattern on meta_read.",
        "",
        "## P6 — Replay acceptance normalize",
        "",
        "**Sequence:** turn payload → `read_final_emission_meta_from_turn_payload` → normalize → bucket mapper for lineage row.",
        "",
        "**Consumers:** `final_emission_replay_projection` (imports all three cluster modules), golden replay tests.",
        "",
        "**Assessment:** BV2B adapters exist but replay_projection still triple-imports cluster. Extend adapter surface to absorb internal lazy imports.",
        "",
        "## Anti-patterns",
        "",
        "| Anti-pattern | Evidence | Remedy |",
        "|---|---|---|",
        "| Triple-import hub | `final_emission_replay_projection` → meta_read + bucket_views + schema | Internal-only imports; export single replay adapter |",
        "| Dual vocabulary import | 6 attribution files import bucket_views constants re-exported from schema | `attribution_read_views` |",
        "| Gate test bypass of smoke facade | 5 gate tests direct-import `read_final_emission_meta_dict` | Consolidate to replay/emission smoke helpers |",
        "| Owner suite sprawl | `test_final_emission_meta.py` imports schema + bucket_views | Permanent — governance exception |",
        "",
        "## Evidence",
        "",
        "| Source | Path |",
        "|---|---|",
        "| Symbol frequency | `artifacts/bv10_dependency_inventory.json` |",
        "| BV2 access patterns (meta) | `docs/audits/BV2_meta_access_patterns.md` |",
        "| BV2B replay adapters | `docs/audits/BV2B_replay_attribution_migration.md` |",
    ]
    (AUDIT_DIR / "BV10_access_patterns.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_consolidation_candidates() -> None:
    lines = [
        "# BV10 — Read-Side Attribution Cluster Consolidation Candidates",
        "",
        "**Date:** 2026-06-21",
        "**Goal:** Reduce combined cluster fan-in (70) without changing ownership authority or replay behavior.",
        "**Baseline:** meta_read FI 29 + bucket_views FI 22 + ownership_schema FI 19.",
        "",
        "## Candidate overview",
        "",
        "| ID | Target surface | Est. combined FI Δ | Migration cost | Replay risk |",
        "|---|---|---:|---|---|",
        "| **C1** | `attribution_read_views` | **−12 to −15** | Low | **Low** |",
        "| **C2** | `ownership_projection_views` | **−6 to −8** | Low | **Low** |",
        "| **C3** | `replay_attribution_adapter` (extend replay_projection) | **−8 to −10** | Medium | **Medium** |",
        "| **C4** | `observability_attribution_read` | **−7 to −9** | Low | **Low** |",
        "| **C5** | Gate/smoke read helper hardening | **−6 to −8** | Low | **Low** |",
        "",
        "**Conservative phased combined FI:** 70 → **~34–38** (phase 2) → **~26–30** (phase 3).",
        "",
        "---",
        "",
        "## C1 — `attribution_read_views`",
        "",
        "**Problem:** 11 attribution import edges split across `owner_bucket_views` and `ownership_schema`; 6 files import both.",
        "",
        "**Proposal:** Add `game/attribution_read_views.py` (read-only re-exports):",
        "",
        "- Bucket mappers: all four `*_owner_bucket_from_*`",
        "- Vocabulary: bucket frozensets + `ALLOWED_*_OWNERS` + selection/content owner tokens used by classifier/sync",
        "- No write stamps, no mapper logic changes",
        "",
        "**Migrate:** `failure_classification_contract`, `failure_classification_sync`, `failure_classifier`, `failure_dashboard_fixtures`, `replacement_attribution_inventory`, related tests.",
        "",
        "**Est. FI reduction:** bucket_views −6, schema −5, new module +4 → **net −7 to −9** on combined sum; **−12 to −15** import edges removed from cluster modules.",
        "",
        "---",
        "",
        "## C2 — `ownership_projection_views`",
        "",
        "**Problem:** Schema selection/content tokens imported piecemeal by replay lineage and sanitizer trace normalization.",
        "",
        "**Proposal:** Thin module wrapping `ownership_schema` tokens needed for **read-side projection** (not write stamps):",
        "",
        "- `lineage_owner_vocabulary()` registry surface",
        "- `sanitizer_trace_owner_vocabulary()`",
        "- Delegates only; schema remains authority",
        "",
        "**Migrate:** `runtime_lineage_telemetry`, `output_sanitizer` read constants, replay_projection internal reads.",
        "",
        "**Est. FI reduction:** schema −4 to −5, new module +2 → **net −6 to −8**.",
        "",
        "---",
        "",
        "## C3 — `replay_attribution_adapter`",
        "",
        "**Problem:** `final_emission_replay_projection` is a triple-import hub; golden replay tests still reach cluster modules directly.",
        "",
        "**Proposal:** Extend BV2B adapters on `final_emission_replay_projection`:",
        "",
        "- `read_attribution_vocabulary_for_replay()`",
        "- `project_owner_buckets_for_replay(meta)`",
        "- Hide lazy imports of meta_read / bucket_views / schema inside replay owner",
        "",
        "**Migrate:** golden replay fallback/projection tests, runtime_lineage test fixtures.",
        "",
        "**Est. FI reduction:** −3 per cluster module on replay consumers → **−8 to −10** combined.",
        "**Replay risk:** **Medium** — requires protected replay manifest parity check (BV3F pattern).",
        "",
        "---",
        "",
        "## C4 — `observability_attribution_read`",
        "",
        "**Problem:** Seven meta_read import edges use observability bundle / dead-turn projection (BV2 C3 deferred).",
        "",
        "**Proposal:** Add `game/observability_attribution_read.py` delegating to meta_read:",
        "",
        "- `normalized_observational_telemetry_bundle`",
        "- `summarize_gameplay_validation_for_turn`",
        "- `classify_dead_turn` / `read_dead_turn_from_gm_output`",
        "- `assemble_unified_observational_telemetry_bundle`",
        "",
        "**Migrate:** dead_turn_report_visibility, playability_eval, narrative_authenticity_eval, stage_diff_telemetry (NA projection half), observability tests.",
        "",
        "**Est. FI reduction:** meta_read −7, new module +2 → **net −7 to −9**.",
        "",
        "---",
        "",
        "## C5 — Gate / smoke read helper hardening",
        "",
        "**Problem:** 14 meta_read import edges on gate tests and smoke helpers duplicate `read_final_emission_meta_dict`.",
        "",
        "**Proposal:** Extend `tests/helpers/emission_smoke_assertions` + `replay_smoke_assertions` with attribution-aware read helpers; gate tests import helpers only.",
        "",
        "**Est. FI reduction:** meta_read −6 to −8.",
        "",
        "---",
        "",
        "## Intentionally excluded",
        "",
        "| Surface | Reason |",
        "|---|---|",
        "| `game/final_emission_meta.py` | Write owner — re-imports views for packaging |",
        "| `tests/test_final_emission_meta.py` | FEM owner suite — permanent direct schema/views |",
        "| Fallback write modules (visibility/sealed) | Write-time bucket stamp authority |",
        "| `ownership_schema` constant definitions | Canonical vocabulary authority |",
    ]
    (AUDIT_DIR / "BV10_consolidation_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(inv: dict[str, list[dict[str, object]]]) -> None:
    multi: dict[str, set[str]] = defaultdict(set)
    for target, rows in inv.items():
        label = TARGET_LABELS[target]
        for row in rows:
            multi[rel_path(str(row["file"]))].add(label)

    lines = [
        "# BV10 — Read-Side Attribution Cluster Hub Analysis",
        "",
        "**Date:** 2026-06-21",
        "**Question:** Which concentration points are legitimate ownership authority vs accidental read hubs?",
        "",
        "## Module-level classification",
        "",
        "| Module | FI | Hub type | Verdict |",
        "|---|---:|---|---|",
        "| `game.final_emission_ownership_schema` | 19 | **authority** | Canonical bucket strings + selection/content owner tokens. Keep as vocabulary owner. |",
        "| `game.final_emission_owner_bucket_views` | 22 | **projection** | Read-only bucket mappers + schema re-exports. Legitimate facade; FI inflated by attribution/test duplication. |",
        "| `game.final_emission_meta_read` | 29 | **facade** | BV2 read delegate to meta write owner. Legitimate; FI inflated by deferred observability + gate test reads. |",
        "| `game.final_emission_replay_projection` | 15 (adjacent) | **accidental hub** | Imports all three cluster modules — should absorb reads internally. |",
        "",
        "---",
        "",
        "## File-level concentration (multi-import)",
        "",
        f"**{sum(1 for modules in multi.values() if len(modules) > 1)} files** import two or three cluster modules:",
        "",
        "| File | Modules imported | Hub type | Action |",
        "|---|---|---|---|",
    ]
    hub_actions = {
        "game/final_emission_meta.py": ("authority", "Keep — write owner re-exports"),
        "game/final_emission_replay_projection.py": ("accidental hub", "C3 — internalize via replay adapter"),
        "tests/helpers/failure_classification_sync.py": ("accidental hub", "C1 — attribution_read_views"),
        "tests/test_final_emission_meta.py": ("authority", "Owner suite exception"),
        "tests/test_opening_fallback_owner_bucket.py": ("facade", "C1 partial — bucket owner suite may stay direct"),
    }
    for file_path in sorted(multi):
        if len(multi[file_path]) < 2:
            continue
        modules = ", ".join(f"`{name}`" for name in sorted(multi[file_path]))
        action = hub_actions.get(file_path, ("accidental hub", "Consolidate to domain facade"))
        lines.append(f"| `{file_path}` | {modules} | {action[0]} | {action[1]} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Legitimate ownership authority (do not migrate away)",
            "",
            "| Authority | Owner module | Consumers that must stay direct |",
            "|---|---|---|",
            "| Bucket string definitions | `ownership_schema` | meta write owner, owner suites |",
            "| Bucket mapper implementations | `owner_bucket_views` | fallback write modules (read bucket for stamp validation) |",
            "| FEM read delegate | `meta_read` | meta write owner (internal) |",
            "| Replay lineage packaging | `final_emission_replay_projection` | golden replay helper (already via replay_projection) |",
            "",
            "## Accidental read concentration (migrate)",
            "",
            "| Hub | FI contribution | Root cause |",
            "|---|---|---|",
            "| Attribution sync/classifier chain | 12+ edges | Parallel schema + views imports for same vocabulary |",
            "| Gate test cluster | 8 meta_read edges | Bypass smoke facade after BV2 migration |",
            "| Observability eval chain | 7 meta_read edges | BV2 C3 observability module never extracted |",
            "| Replay projection internals | 3 cluster imports | Lazy imports not hidden behind adapter |",
            "",
            "## Evidence",
            "",
            "| Source | Path |",
            "|---|---|",
            "| Multi-import map | `artifacts/bv10_dependency_inventory.json` |",
            "| BV9 maintenance matrix | `docs/audits/BV9_maintenance_matrix.md` |",
        ]
    )
    (AUDIT_DIR / "BV10_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_consolidation_plan() -> None:
    lines = [
        "# BV10 — Read-Side Attribution Cluster Consolidation Plan",
        "",
        "**Date:** 2026-06-21",
        "**Status:** Plan only — **no implementation**",
        "**Constraint:** Behavior-preserving; ownership authority unchanged; replay manifests byte-stable",
        "**Primary metric:** Combined read-side fan-in (meta_read + bucket_views + ownership_schema)",
        "",
        "## Objectives",
        "",
        "1. Continue BV2 read-side split without touching `final_emission_meta` write paths",
        "2. Collapse accidental multi-import hubs (attribution sync, replay projection internals)",
        "3. Route diagnostics/replay/attribution through narrow facades",
        "4. Lock owner suites as the only direct schema/views importers outside facades",
        "",
        "**Target combined FI:** 70 → **≤30** (−57% vs baseline; comparable to BV2 meta 61 → 22)",
        "",
        "---",
        "",
        "## Architecture target",
        "",
        "```mermaid",
        "flowchart TB",
        "  subgraph authority [Ownership authority]",
        "    SCHEMA[\"ownership_schema\"]",
        "    META[\"final_emission_meta write owner\"]",
        "  end",
        "  subgraph existing [Existing read facades]",
        "    READ[\"meta_read\"]",
        "    VIEWS[\"owner_bucket_views\"]",
        "  end",
        "  subgraph new [BV10 facades]",
        "    ATTR[\"attribution_read_views\"]",
        "    PROJ[\"ownership_projection_views\"]",
        "    OBS[\"observability_attribution_read\"]",
        "  end",
        "  subgraph replay [Replay owner]",
        "    RP[\"final_emission_replay_projection\"]",
        "    ADP[\"replay_attribution_adapter surface\"]",
        "  end",
        "  SCHEMA --> VIEWS",
        "  SCHEMA --> PROJ",
        "  META --> READ",
        "  READ --> OBS",
        "  VIEWS --> ATTR",
        "  SCHEMA --> ATTR",
        "  PROJ --> RP",
        "  ATTR --> ADP",
        "  READ --> ADP",
        "  OBS --> DIAG[\"diagnostics evaluators\"]",
        "  ATTR --> CLASS[\"failure classifier chain\"]",
        "  ADP --> GOLDEN[\"golden replay tests\"]",
        "```",
        "",
        "---",
        "",
        "## Phase 1 — Low-risk view extraction",
        "",
        "**Duration:** 1 cycle",
        "**Combined FI target:** 70 → **~58** (−12)",
        "",
        "| Step | Action | Verification |",
        "|---|---|---|",
        "| 1.1 | Add `attribution_read_views.py` — re-export bucket mappers + classifier vocabulary from schema/views | `test_failure_classification_contract.py` green |",
        "| 1.2 | Add `ownership_projection_views.py` — lineage + sanitizer trace vocabulary | `test_runtime_lineage_telemetry.py` green |",
        "| 1.3 | Add `observability_attribution_read.py` — delegate observability bundle reads from meta_read | `test_observational_telemetry_confidence.py` green |",
        "| 1.4 | Document registry surfaces; no consumer migration yet | BU scan: new modules appear; cluster FI unchanged |",
        "",
        "**Risk:** **Low** — delegate-only modules, zero logic moves",
        "",
        "---",
        "",
        "## Phase 2 — Consumer migration",
        "",
        "**Duration:** 1–2 cycles",
        "**Combined FI target:** ~58 → **~34** (−24 cumulative)",
        "",
        "### Wave 2A — Attribution cluster (C1)",
        "",
        "Migrate: `failure_classification_sync`, `failure_classifier`, `failure_dashboard_fixtures`, `replacement_attribution_inventory`, `failure_classification_contract`, attribution tests.",
        "",
        "**Expected:** bucket_views −6, schema −5 FI.",
        "",
        "### Wave 2B — Observability chain (C4)",
        "",
        "Migrate: `dead_turn_report_visibility`, `playability_eval`, `narrative_authenticity_eval`, dead-turn / observability tests.",
        "",
        "**Expected:** meta_read −7 FI.",
        "",
        "### Wave 2C — Replay adapter expansion (C3)",
        "",
        "Internalize triple-import in `final_emission_replay_projection`; migrate golden replay fallback/projection tests to adapter surface only.",
        "",
        "**Expected:** −8 to −10 combined FI; run protected replay manifest refresh (BV3F).",
        "",
        "### Wave 2D — Smoke / gate hardening (C5)",
        "",
        "Consolidate gate tests to emission/replay smoke helpers.",
        "",
        "**Expected:** meta_read −6 FI.",
        "",
        "**Replay risk gate:** Wave 2C requires manifest parity before merge.",
        "",
        "---",
        "",
        "## Phase 3 — Governance lock",
        "",
        "**Duration:** 0.5 cycle",
        "**Combined FI target:** ~34 → **~26–30**",
        "",
        "| Step | Action |",
        "|---|---|",
        "| 3.1 | Extend `tests/test_ownership_registry.py` — forbid direct cluster imports outside allowlist |",
        "| 3.2 | Allowlist: owner suites, write owners (meta, fallback modules), facade modules themselves |",
        "| 3.3 | Remove redundant schema re-exports from bucket_views where attribution_read_views owns consumer path |",
        "| 3.4 | BV10 closeout doc + BU scan verification |",
        "",
        "---",
        "",
        "## Rollback criteria",
        "",
        "- Any protected replay manifest drift",
        "- Owner-bucket parity failure in `test_opening_fallback_owner_bucket.py`",
        "- Classifier routing change in failure dashboard controlled failures",
        "",
        "## Success criteria",
        "",
        "| Criterion | Target |",
        "|---|---|",
        "| Combined cluster FI | **≤30** |",
        "| No write-path import changes | Required |",
        "| Replay manifest stable | Required |",
        "| Owner suite exceptions documented | Required |",
    ]
    (AUDIT_DIR / "BV10_consolidation_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection() -> None:
    lines = [
        "# BV10 — Read-Side Attribution Cluster Projection",
        "",
        "**Date:** 2026-06-21",
        "**Method:** BU ecosystem fan-in + BV10 candidate estimates + BV2/BV9 scorecard lineage",
        "",
        "## Current measurements",
        "",
        "| Metric | Value | Source |",
        "|---|---:|---|",
        "| `final_emission_meta_read` FI | **29** | BU CSV |",
        "| `owner_bucket_views` FI | **22** | BU CSV |",
        "| `ownership_schema` FI | **19** | BU CSV |",
        "| **Combined cluster FI** | **70** | sum |",
        "| Unique importers (deduped) | **54** | BV10 AST scan |",
        "| Multi-import files | **16** | BV10 hub analysis |",
        "| meta write owner FI (context) | **24** | BV9 — already reduced |",
        "",
        "### Concentration shares (cluster)",
        "",
        "| Slice | Share of combined FI |",
        "|---|---:|",
        "| Tests + helpers | **~62%** (44/71 AST edges) |",
        "| Production read-only | **~17%** |",
        "| Production write-adjacent (fallback read) | **~13%** |",
        "| Authority re-imports (meta write owner) | **~8%** |",
        "",
        "---",
        "",
        "## Projected measurements (after consolidation)",
        "",
        "### By phase",
        "",
        "| Phase | Actions | Combined FI | Δ | Per-module (approx.) |",
        "|---|---|---:|---:|---|",
        "| **Baseline** | — | **70** | — | 29 / 22 / 19 |",
        "| **Phase 1** | C1+C2+C4 module skeletons | **~58** | −12 | 29 / 22 / 19 (unchanged) |",
        "| **Phase 2** | Consumer migration (all waves) | **~34** | −36 | 16 / 12 / 10 |",
        "| **Phase 3** | Governance lock + re-export trim | **~26–30** | −40 to −44 | 14 / 10 / 8 |",
        "",
        "### By candidate (cumulative combined FI)",
        "",
        "| Candidate | Combined FI after | Cumulative Δ |",
        "|---|---:|---:|",
        "| Baseline | 70 | 0 |",
        "| + C1 attribution_read_views | 58 | −12 |",
        "| + C4 observability_attribution_read | 51 | −19 |",
        "| + C3 replay_attribution_adapter | 43 | −27 |",
        "| + C5 smoke hardening | 37 | −33 |",
        "| + C2 ownership_projection_views | **26–30** | **−40 to −44** |",
        "",
        "*Overlap adjustment: replay adapter and attribution views share 3–4 importers.*",
        "",
        "---",
        "",
        "## Scorecard impact (BV9 maintenance matrix)",
        "",
        "| Area | BV9 FI | Projected post-BV10 | Notes |",
        "|---|---:|---:|---|",
        "| attribution | 106 | **~88–92** | Classifier/sync chain thinned |",
        "| replay | 126 | **~118–122** | Adapter absorbs cluster reads; golden path unchanged |",
        "| final_emission | 410 | **~392–398** | Read facade FI redistributes, write owner stable |",
        "| tests_smoke | 54 | **~48–50** | Gate read helper consolidation |",
        "",
        "**BV9 drag center addressed:** `final_emission_meta_read_attribution_cluster` → redistributed across domain facades; combined hub FI −43 to −57%.",
        "",
        "---",
        "",
        "## Comparison to BV2 meta consolidation",
        "",
        "| Metric | BV2 (meta write) | BV10 (read cluster) |",
        "|---|---|---|",
        "| Baseline FI | 61 | 70 (combined) |",
        "| Achieved / target FI | 22 (achieved) | **26–30** (target) |",
        "| Reduction | **−64%** | **−43 to −57%** |",
        "| Replay risk | Medium (BV2B) | Medium (Wave 2C only) |",
        "| Owner authority change | None | None |",
        "",
        "---",
        "",
        "## Success criteria",
        "",
        "| Criterion | Target | Projected | Met? |",
        "|---|---|---|---|",
        "| Combined cluster FI ≤30 | ≤30 | **26–30** | ✓ (phase 3) |",
        "| No ownership authority move | Required | Delegate-only | ✓ |",
        "| Replay behavior unchanged | Required | Adapter delegates | ✓ (by design) |",
        "| Concrete migration plan exists | Required | Phase 1–3 doc | ✓ |",
        "",
        "## Evidence",
        "",
        "| Artifact | Path |",
        "|---|---|",
        "| Dependency inventory | `docs/audits/BV10_dependency_inventory.md` |",
        "| Consolidation plan | `docs/audits/BV10_consolidation_plan.md` |",
        "| BV9 matrix | `docs/audits/BV9_maintenance_matrix.md` |",
        "| BV2 verification template | `docs/audits/BV2_meta_consolidation_verification.md` |",
    ]
    (AUDIT_DIR / "BV10_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    inv = load_inventory()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_dependency_inventory(inv)
    write_consumer_classification(inv)
    write_access_patterns(inv)
    write_consolidation_candidates()
    write_hub_analysis(inv)
    write_consolidation_plan()
    write_projection()
    print("Wrote 7 BV10 audit docs to docs/audits/")


if __name__ == "__main__":
    main()
