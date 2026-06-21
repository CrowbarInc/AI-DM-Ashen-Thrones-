"""BV10B consumer migration — import retargeting (analysis + one-shot migration helper)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ATTRIBUTION = "game.attribution_read_views"
PROJECTION = "game.ownership_projection_views"
OBSERVABILITY = "game.observability_attribution_read"
BUCKET = "game.final_emission_owner_bucket_views"
SCHEMA = "game.final_emission_ownership_schema"
META_READ = "game.final_emission_meta_read"

MIGRATIONS: list[tuple[str, str, str, str]] = [
    # file, subsystem, old, new
    ("tests/failure_classification_contract.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/failure_classification_contract.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/helpers/failure_classification_sync.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/helpers/failure_classification_sync.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/helpers/failure_classifier.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/helpers/failure_dashboard_fixtures.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/helpers/failure_dashboard_fixtures.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/helpers/replacement_attribution_inventory.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/test_failure_classification_contract.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/test_failure_classification_contract.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/test_failure_classifier.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/test_failure_classifier.py", "attribution", BUCKET, ATTRIBUTION),
    ("tests/test_replacement_attribution_inventory.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/helpers/opening_fallback_evidence.py", "fallback", BUCKET, ATTRIBUTION),
    ("tests/test_gm_retry.py", "fallback", BUCKET, ATTRIBUTION),
    ("tests/test_final_emission_visibility.py", "tests", BUCKET, ATTRIBUTION),
    ("tests/test_final_emission_gate_selector_snapshots.py", "tests", BUCKET, ATTRIBUTION),
    ("tests/test_final_emission_opening_fallback.py", "fallback", BUCKET, ATTRIBUTION),
    ("tests/test_final_emission_visibility_fallback.py", "fallback", BUCKET, ATTRIBUTION),
    ("tests/test_final_emission_sealed_fallback.py", "fallback", BUCKET, ATTRIBUTION),
    ("tests/test_golden_replay_fallback_projection.py", "replay", SCHEMA, PROJECTION),
    ("tests/test_golden_replay_fallback_projection.py", "replay", BUCKET, ATTRIBUTION),
    ("tests/test_runtime_lineage_telemetry.py", "replay", SCHEMA, PROJECTION),
    ("tests/test_runtime_lineage_telemetry.py", "replay", BUCKET, ATTRIBUTION),
    ("tests/test_golden_replay_projection.py", "replay", SCHEMA, PROJECTION),
    ("tests/test_output_sanitizer.py", "tests", SCHEMA, PROJECTION),
    ("game/runtime_lineage_telemetry.py", "observability", SCHEMA, PROJECTION),
    ("game/output_sanitizer.py", "final emission", SCHEMA, PROJECTION),
    ("game/final_emission_replay_projection.py", "replay", SCHEMA, PROJECTION),
    ("game/dead_turn_report_visibility.py", "diagnostics", META_READ, OBSERVABILITY),
    ("game/playability_eval.py", "diagnostics", META_READ, OBSERVABILITY),
    ("game/narrative_authenticity_eval.py", "diagnostics", META_READ, OBSERVABILITY),
    ("tests/test_observational_telemetry_confidence.py", "observability", META_READ, OBSERVABILITY),
    ("tests/test_dead_turn_detection.py", "diagnostics", META_READ, OBSERVABILITY),
]

LAZY_REPLACEMENTS: list[tuple[str, str, str, str]] = [
    ("tests/test_replacement_attribution_inventory.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/test_failure_classification_contract.py", "attribution", SCHEMA, ATTRIBUTION),
    ("tests/test_validation_layer_separation_runtime.py", "observability", META_READ, OBSERVABILITY),
    ("game/final_emission_replay_projection.py", "replay", BUCKET, ATTRIBUTION),
    ("game/final_emission_replay_projection.py", "replay", META_READ, OBSERVABILITY),
    ("game/stage_diff_telemetry.py", "diagnostics", META_READ, OBSERVABILITY),
    ("tests/test_dead_turn_evaluation_threading.py", "diagnostics", META_READ, OBSERVABILITY),
    ("tests/helpers/behavioral_gauntlet_eval.py", "diagnostics", META_READ, OBSERVABILITY),
]


def _replace_from_import(text: str, old_mod: str, new_mod: str) -> str:
    old_short = old_mod.split(".")[-1]
    new_short = new_mod.split(".")[-1]
    pattern = rf"from {re.escape(old_mod)} import"
    if not re.search(pattern, text):
        return text
    return re.sub(pattern, f"from {new_mod} import", text)


def _replace_lazy_import(text: str, old_mod: str, new_mod: str) -> str:
    pattern = rf"from {re.escape(old_mod)} import"
    return re.sub(pattern, f"from {new_mod} import", text)


def apply_migrations() -> list[tuple[str, str, str, str, str]]:
    applied: list[tuple[str, str, str, str, str]] = []
    touched: set[Path] = set()
    for rel, subsystem, old, new in MIGRATIONS + LAZY_REPLACEMENTS:
        path = ROOT / rel.replace("/", "\\") if "\\" in rel else ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        updated = _replace_from_import(text, old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            applied.append((rel, subsystem, old, new, "import"))
            touched.add(path)
    return applied


if __name__ == "__main__":
    rows = apply_migrations()
    for row in rows:
        print("\t".join(row))
    print(f"applied={len(rows)}")
