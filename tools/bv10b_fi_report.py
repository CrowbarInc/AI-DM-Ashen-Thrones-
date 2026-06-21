import csv
from pathlib import Path

rows = list(csv.DictReader(Path("docs/audits/BU_import_fan_in_fan_out.csv").open()))
mods = [
    "game.final_emission_meta_read",
    "game.final_emission_owner_bucket_views",
    "game.final_emission_ownership_schema",
    "game.attribution_read_views",
    "game.ownership_projection_views",
    "game.observability_attribution_read",
]
cluster_authority = 0
facade = 0
for m in mods:
    r = next((x for x in rows if x["module"] == m), None)
    if not r:
        print(f"{m:45} NOT IN ECOSYSTEM")
        continue
    fi = int(r["fan_in_total"])
    if m in mods[:3]:
        cluster_authority += fi
    else:
        facade += fi
    print(
        f"{m.split('.')[-1]:35} FI={fi:3} "
        f"prod={r['fan_in_production']} test={r['fan_in_tests']} helper={r['fan_in_helpers']}"
    )
print(f"authority_cluster={cluster_authority} facade_cluster={facade} grand_total={cluster_authority+facade}")
