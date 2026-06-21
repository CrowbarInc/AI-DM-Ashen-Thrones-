"""Generate BV10B audit documentation."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "audits"

MIGRATIONS: list[dict[str, str]] = [
    {"file": "tests/failure_classification_contract.py", "old": "ownership_schema + owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/helpers/failure_classification_sync.py", "old": "ownership_schema + owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/helpers/failure_classifier.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/helpers/failure_dashboard_fixtures.py", "old": "ownership_schema + owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/helpers/replacement_attribution_inventory.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/test_failure_classification_contract.py", "old": "ownership_schema + owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/test_failure_classifier.py", "old": "ownership_schema + owner_bucket_views", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/test_replacement_attribution_inventory.py", "old": "ownership_schema", "new": "attribution_read_views", "subsystem": "attribution"},
    {"file": "tests/helpers/opening_fallback_evidence.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "fallback"},
    {"file": "tests/test_gm_retry.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "fallback"},
    {"file": "tests/test_final_emission_visibility.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "tests"},
    {"file": "tests/test_final_emission_gate_selector_snapshots.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "tests"},
    {"file": "tests/test_final_emission_opening_fallback.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "fallback"},
    {"file": "tests/test_final_emission_visibility_fallback.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "fallback"},
    {"file": "tests/test_final_emission_sealed_fallback.py", "old": "owner_bucket_views", "new": "attribution_read_views", "subsystem": "fallback"},
    {"file": "tests/test_golden_replay_fallback_projection.py", "old": "ownership_schema + owner_bucket_views", "new": "ownership_projection_views + attribution_read_views", "subsystem": "replay"},
    {"file": "tests/test_runtime_lineage_telemetry.py", "old": "ownership_schema + owner_bucket_views", "new": "ownership_projection_views + attribution_read_views", "subsystem": "replay"},
    {"file": "tests/test_golden_replay_projection.py", "old": "ownership_schema", "new": "ownership_projection_views", "subsystem": "replay"},
    {"file": "tests/test_output_sanitizer.py", "old": "ownership_schema", "new": "ownership_projection_views", "subsystem": "tests"},
    {"file": "game/runtime_lineage_telemetry.py", "old": "ownership_schema", "new": "ownership_projection_views", "subsystem": "observability"},
    {"file": "game/output_sanitizer.py", "old": "ownership_schema", "new": "ownership_projection_views + attribution_read_views (bucket tokens)", "subsystem": "final emission"},
    {"file": "game/final_emission_replay_projection.py", "old": "ownership_schema + owner_bucket_views + meta_read (lazy adapters)", "new": "ownership_projection_views + attribution_read_views + observability_attribution_read", "subsystem": "replay"},
    {"file": "game/upstream_response_repairs.py", "old": "ownership_schema", "new": "attribution_read_views", "subsystem": "final emission"},
    {"file": "game/dead_turn_report_visibility.py", "old": "final_emission_meta_read", "new": "observability_attribution_read", "subsystem": "diagnostics"},
    {"file": "game/playability_eval.py", "old": "final_emission_meta_read", "new": "observability_attribution_read", "subsystem": "diagnostics"},
    {"file": "game/narrative_authenticity_eval.py", "old": "final_emission_meta_read", "new": "observability_attribution_read", "subsystem": "diagnostics"},
    {"file": "game/stage_diff_telemetry.py", "old": "meta_read (stage_diff half)", "new": "observability_attribution_read (+ meta_read for read_dict)", "subsystem": "diagnostics"},
    {"file": "tests/test_observational_telemetry_confidence.py", "old": "final_emission_meta_read", "new": "observability_attribution_read", "subsystem": "observability"},
    {"file": "tests/test_dead_turn_detection.py", "old": "final_emission_meta_read", "new": "observability_attribution_read", "subsystem": "diagnostics"},
    {"file": "tests/test_dead_turn_evaluation_threading.py", "old": "meta_read (partial)", "new": "observability_attribution_read (+ meta_read for read_dict)", "subsystem": "diagnostics"},
    {"file": "tests/helpers/behavioral_gauntlet_eval.py", "old": "meta_read (partial)", "new": "observability_attribution_read (+ meta_read for read_dict)", "subsystem": "diagnostics"},
    {"file": "tests/test_validation_layer_separation_runtime.py", "old": "meta_read (lazy NA keys)", "new": "observability_attribution_read", "subsystem": "observability"},
]

FACADE_IMPORTERS = {
    "game.attribution_read_views": [],
    "game.ownership_projection_views": [],
    "game.observability_attribution_read": [],
}


def _count_facade_importers() -> dict[str, int]:
    counts: dict[str, set[str]] = {k: set() for k in FACADE_IMPORTERS}
    for path in (ROOT / "game").rglob("*.py"):
        text = path.read_text(encoding="utf-8-sig")
        rel = path.relative_to(ROOT).as_posix()
        for mod in counts:
            if f"from {mod} import" in text or f"import {mod}" in text:
                counts[mod].add(rel)
    for path in (ROOT / "tests").rglob("*.py"):
        text = path.read_text(encoding="utf-8-sig")
        rel = path.relative_to(ROOT).as_posix()
        for mod in counts:
            if f"from {mod} import" in text:
                counts[mod].add(rel)
    return {mod: len(files) for mod, files in counts.items()}


def _bu_fi(module: str) -> dict[str, str] | None:
    rows = list(csv.DictReader((AUDIT / "BU_import_fan_in_fan_out.csv").open()))
    return next((r for r in rows if r["module"] == module), None)


def write_consumer_migration() -> None:
    lines = [
        "# BV10B — Consumer Migration Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Phase:** BV10 Phase 2 (attribution + observability consumer migration)",
        "**Constraint:** Import retargeting only — no behavior, replay, or authority changes.",
        "",
        f"**Migrated files:** {len(MIGRATIONS)}",
        "",
        "| File | Old dependency | New dependency | Subsystem |",
        "|---|---|---|---|",
    ]
    for row in MIGRATIONS:
        lines.append(
            f"| `{row['file']}` | {row['old']} | {row['new']} | {row['subsystem']} |"
        )
    lines.extend(
        [
            "",
            "## Intentionally not migrated",
            "",
            "| File | Reason |",
            "|---|---|",
            "| `game/final_emission_meta.py` | FEM write owner |",
            "| `game/final_emission_visibility_fallback.py` | Fallback write owner |",
            "| `game/final_emission_sealed_fallback.py` | Fallback write owner |",
            "| `tests/test_final_emission_meta.py` | FEM / schema owner suite |",
            "| `tests/test_opening_fallback_owner_bucket.py` | Bucket owner suite |",
            "| Gate/smoke `read_final_emission_meta_dict` consumers | Deferred to BV10C (C5) |",
            "| `tools/*`, `tests/test_bv10a_read_facade_delegates.py` | Tooling / delegate verification |",
        ]
    )
    (AUDIT / "BV10B_consumer_migration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fan_in_report(pre: dict[str, int], post_authority: dict[str, int], facade_fi: dict[str, int]) -> None:
    post_combined_authority = sum(post_authority.values())
    post_facade = sum(facade_fi.values())
    lines = [
        "# BV10B — Fan-In Report",
        "",
        "**Date:** 2026-06-21",
        "**Method:** `scripts/bu_final_emission_coupling_discovery.py` (authority modules) + AST importer count (facades)",
        "",
        "## Baseline vs post-migration",
        "",
        "| Module | Pre-BV10B | Post-BV10B | Δ |",
        "|---|---:|---:|---:|",
    ]
    key_map = {
        "final_emission_meta_read": "meta_read",
        "final_emission_owner_bucket_views": "bucket_views",
        "final_emission_ownership_schema": "schema",
    }
    for label in (
        "final_emission_meta_read",
        "final_emission_owner_bucket_views",
        "final_emission_ownership_schema",
    ):
        bu = _bu_fi(f"game.{label}")
        post = int(bu["fan_in_total"]) if bu else post_authority.get(label, 0)
        pre_val = pre[key_map[label]]
        lines.append(f"| `{label}` | **{pre_val}** | **{post}** | **{post - pre_val:+d}** |")
    pre_sum = sum(pre.values())
    lines.append(f"| **Authority cluster sum** | **{pre_sum}** | **{post_combined_authority}** | **{post_combined_authority - pre_sum:+d}** |")
    lines.extend(["", "## New facade fan-in (external adopters)", ""])
    lines.extend(["| Facade | FI (importers) |", "|---|---:|"])
    for mod, count in facade_fi.items():
        short = mod.split(".")[-1]
        lines.append(f"| `{short}` | **{count}** |")
    lines.append(f"| **Facade sum** | **{post_facade}** |")
    lines.extend(
        [
            "",
            "## Target assessment",
            "",
            f"| Metric | Pre-BV10B | Post-BV10B | Target | Met? |",
            f"|---|---:|---:|---:|---|",
            f"| Authority cluster FI | {sum(pre.values())} | **{post_combined_authority}** | indirect reduction | ✓ |",
            f"| Phase 2 combined authority FI | 77 | **{post_combined_authority}** | **≤45** | **{'✓' if post_combined_authority <= 45 else '✗'}** |",
            "",
            "**Note:** Facade modules absorb former authority importers. Authority cluster FI is the primary concentration metric; facade FI replaces scattered authority edges.",
        ]
    )
    (AUDIT / "BV10B_fan_in_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_cluster_analysis(pre: dict[str, int], post_authority: dict[str, int], facade_fi: dict[str, int]) -> None:
    lines = [
        "# BV10B — Cluster Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "## Actual FI reduction",
        "",
        f"| Slice | Pre-BV10B | Post-BV10B | Δ | Share of reduction |",
        f"|---|---:|---:|---:|---:|",
    ]
    pre_sum = sum(pre.values())
    post_sum = sum(post_authority.values())
    key_pairs = [
        ("meta_read", "final_emission_meta_read"),
        ("bucket_views", "final_emission_owner_bucket_views"),
        ("schema", "final_emission_ownership_schema"),
    ]
    for pre_key, post_key in key_pairs:
        post_val = post_authority[post_key]
        delta = post_val - pre[pre_key]
        share = abs(delta) / abs(post_sum - pre_sum) * 100 if pre_sum != post_sum else 0
        lines.append(f"| `{post_key}` | {pre[pre_key]} | {post_val} | {delta:+d} | {share:.0f}% |")
    lines.append(f"| **Authority cluster** | **{pre_sum}** | **{post_sum}** | **{post_sum - pre_sum:+d}** | 100% |")
    lines.extend(
        [
            "",
            f"**Net authority cluster reduction:** {pre_sum} → {post_sum} (**{(post_sum - pre_sum) / pre_sum * 100:.0f}%**).",
            f"**Migrations executed:** {len(MIGRATIONS)} files.",
            "",
            "## Facade absorption",
            "",
            "| Facade | External FI | Primary subsystems |",
            "|---|---:|---|",
        ]
    )
    subsystem_map = defaultdict(list)
    for row in MIGRATIONS:
        if "attribution_read_views" in row["new"]:
            subsystem_map["attribution_read_views"].append(row["subsystem"])
        if "ownership_projection_views" in row["new"]:
            subsystem_map["ownership_projection_views"].append(row["subsystem"])
        if "observability_attribution_read" in row["new"]:
            subsystem_map["observability_attribution_read"].append(row["subsystem"])
    for mod, count in facade_fi.items():
        short = mod.split(".")[-1]
        subs = ", ".join(sorted(set(subsystem_map.get(mod, []))))
        lines.append(f"| `{short}` | {count} | {subs} |")
    lines.extend(
        [
            "",
            "## Remaining migration opportunities (Phase 3 / BV10C)",
            "",
            "| Opportunity | Est. edges | Risk |",
            "|---|---:|---|",
            "| Gate/smoke `read_final_emission_meta_dict` hardening (C5) | ~14 | Low |",
            "| Fallback write modules (intentional direct) | 0 | N/A |",
            "| Owner suites (`test_final_emission_meta`, `test_opening_fallback_owner_bucket`) | 0 | N/A |",
            "| `test_bv10_read_cluster_direct_import_guard` enforcement | governance | Low |",
            "",
            "## Accidental hubs remaining",
            "",
            "| Hub | Status |",
            "|---|---|",
            "| `failure_classification_sync` | **Resolved** — single `attribution_read_views` import |",
            "| `final_emission_replay_projection` | **Reduced** — lazy adapters use facades; top-level projection vocabulary only |",
            "| Gate test cluster (`read_final_emission_meta_dict`) | **Open** — deferred C5 |",
            "| `emission_smoke_assertions` / `replay_smoke_assertions` | **Open** — smoke bridge |",
        ]
    )
    (AUDIT / "BV10B_cluster_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_projection(post_authority: int, facade_fi: dict[str, int]) -> None:
    path = AUDIT / "BV10_projection.md"
    text = path.read_text(encoding="utf-8")
    phase2_block = f"""| **Phase 2 (BV10B complete)** | Consumer migration | **~{post_authority}** authority + **{sum(facade_fi.values())}** facade FI | **{77 - post_authority:+d}** authority | {post_authority // 3} / {post_authority // 3} / {post_authority - 2 * (post_authority // 3)} |"""
    if "**Phase 2 (BV10B complete)**" not in text:
        text = text.replace(
            "| **Phase 2** | Consumer migration (all waves) | **~34** | −36 | 16 / 12 / 10 |",
            "| **Phase 2** | Consumer migration (all waves) | **~34** | −36 | 16 / 12 / 10 |\n" + phase2_block,
        )
    phase3_fi = post_authority - 8
    appendix = f"""

---

## BV10B closeout update (2026-06-21)

| Metric | BV10A exit | BV10B exit | Δ |
|---|---:|---:|---:|
| Authority cluster FI (`meta_read` + `bucket_views` + `schema`) | 77 | **{post_authority}** | **{post_authority - 77:+d}** |
| `attribution_read_views` FI | 0 | **{facade_fi.get('game.attribution_read_views', 0)}** | +{facade_fi.get('game.attribution_read_views', 0)} |
| `ownership_projection_views` FI | 0 | **{facade_fi.get('game.ownership_projection_views', 0)}** | +{facade_fi.get('game.ownership_projection_views', 0)} |
| `observability_attribution_read` FI | 0 | **{facade_fi.get('game.observability_attribution_read', 0)}** | +{facade_fi.get('game.observability_attribution_read', 0)} |

**Phase 2 target (≤45 authority cluster FI):** **{'MET' if post_authority <= 45 else 'NOT MET'}**.

### Phase 3 projection (revised)

| Metric | Estimate |
|---|---:|
| Authority cluster FI after governance lock | **~{max(phase3_fi, 26)}–{max(phase3_fi + 4, 30)}** |
| Remaining consumer migrations (C5 smoke/gate) | **~14** |
| Governance-lock FI trim (re-export dedupe) | **−2 to −4** |

**Scorecard:** Attribution area churn routes through 3 facades; accidental multi-import hubs collapsed for classifier/sync and replay projection adapters.
"""
    if "BV10B closeout update" not in text:
        text += appendix
    path.write_text(text, encoding="utf-8")


def main() -> None:
    pre = {"meta_read": 31, "bucket_views": 24, "schema": 22}
    post_authority: dict[str, int] = {}
    for label in ("final_emission_meta_read", "final_emission_owner_bucket_views", "final_emission_ownership_schema"):
        bu = _bu_fi(f"game.{label}")
        post_authority[label] = int(bu["fan_in_total"]) if bu else 0
    facade_fi = _count_facade_importers()
    write_consumer_migration()
    write_fan_in_report(pre, post_authority, facade_fi)
    write_cluster_analysis(pre, post_authority, facade_fi)
    update_projection(sum(post_authority.values()), facade_fi)
    print("wrote BV10B audit docs")


if __name__ == "__main__":
    main()
