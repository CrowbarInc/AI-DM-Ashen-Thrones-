"""BV10C fan-in closeout report — authority cluster + facade modules."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = (
    "game.final_emission_meta_read",
    "game.final_emission_owner_bucket_views",
    "game.final_emission_ownership_schema",
)
FACADES = (
    "game.attribution_read_views",
    "game.ownership_projection_views",
    "game.observability_attribution_read",
    "game.final_emission_replay_projection",
)
REPLAY_ADAPTER = "game.final_emission_replay_projection"


def _load_csv_fi() -> dict[str, int]:
    csv_path = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    return {row["module"]: int(row["fan_in_total"]) for row in rows}


def _load_ast_importers() -> dict[str, int]:
    inventory_path = ROOT / "artifacts" / "bv10_dependency_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    return {target: len(rows) for target, rows in inventory.items()}


def main() -> None:
    csv_fi = _load_csv_fi()
    ast_counts = _load_ast_importers()
    authority_sum = 0
    facade_sum = 0
    print("=== BV10C authority cluster (BU CSV when present, else AST) ===")
    for module in AUTHORITY:
        fi = csv_fi.get(module, ast_counts.get(module, 0))
        authority_sum += fi
        print(f"{module.split('.')[-1]:35} FI={fi:3}")
    print(f"authority_cluster_sum={authority_sum}")
    print()
    print("=== BV10C facade + replay adapter ===")
    for module in FACADES:
        fi = csv_fi.get(module, 0)
        if module != REPLAY_ADAPTER:
            facade_sum += fi
        label = "replay_adapter" if module == REPLAY_ADAPTER else "facade"
        print(f"{module.split('.')[-1]:35} FI={fi:3} ({label})")
    print(f"facade_cluster_sum={facade_sum}")
    print(f"replay_adapter_FI={csv_fi.get(REPLAY_ADAPTER, 0)}")


if __name__ == "__main__":
    main()
