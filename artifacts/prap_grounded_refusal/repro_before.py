"""PR-AP Phase 1: reproduce malformed grounded-refusal realization before repair."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_repairs import (  # noqa: E402
    _remove_fabricated_authority,
    _strip_patterns_from_text,
    repair_fallback_behavior,
)
from game.final_emission_validators import (  # noqa: E402
    _FALLBACK_FABRICATED_AUTHORITY_PATTERNS,
    _contains_fabricated_authority,
    validate_fallback_behavior,
)
from game.playability_eval import _MALFORMED_REFUSAL_FRAGMENT_RE  # noqa: E402
from game.social_exchange_fallback_catalog import (  # noqa: E402
    lawful_strict_social_dialogue_emergency_fallback_line,
    strict_social_ownership_terminal_fallback,
)
from game.social_exchange_policy import _deterministic_index  # noqa: E402
from tests.helpers.fallback_behavior_fixtures import fallback_contract  # noqa: E402


def main() -> int:
    resolution = {
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
        "kind": "question",
        "prompt": "I step over to the tavern runner and ask what the stew costs.",
    }
    catalog = strict_social_ownership_terminal_fallback(resolution)
    emergency = lawful_strict_social_dialogue_emergency_fallback_line(resolution)
    seed = "ownership_terminal|tavern_runner|Tavern Runner"
    idx = _deterministic_index(seed, 3)
    contract = fallback_contract(uncertainty_sources=["unknown_quantity"])
    validation = validate_fallback_behavior(catalog, contract)
    repaired, meta, _ = repair_fallback_behavior(catalog, contract, validation)
    stripped_direct = _remove_fabricated_authority(catalog)
    pattern_hits = [p.pattern for p in _FALLBACK_FABRICATED_AUTHORITY_PATTERNS if p.search(catalog)]
    payload = {
        "catalog_ownership_terminal": catalog,
        "catalog_emergency": emergency,
        "ownership_index": idx,
        "ownership_seed": seed,
        "contains_fabricated_authority": _contains_fabricated_authority(catalog),
        "pattern_hits": pattern_hits,
        "validation_fabricated_authority_detected": validation.get("fabricated_authority_detected"),
        "validation_failure_reasons": validation.get("failure_reasons"),
        "repair_mode": meta.get("fallback_behavior_repair_mode"),
        "repaired_text": repaired,
        "stripped_direct": stripped_direct,
        "strip_patterns_only": _strip_patterns_from_text(
            catalog, patterns=_FALLBACK_FABRICATED_AUTHORITY_PATTERNS
        ),
        "malformed_gate_hits_catalog": bool(_MALFORMED_REFUSAL_FRAGMENT_RE.search(catalog)),
        "malformed_gate_hits_repaired": bool(_MALFORMED_REFUSAL_FRAGMENT_RE.search(repaired)),
        "literal_malformed_in_catalog": "from what." in catalog and "from what I know" not in catalog,
    }
    out = Path(__file__).resolve().parent / "repro_before.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
