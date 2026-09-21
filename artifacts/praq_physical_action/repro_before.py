"""PR-AQ Phase 1: reproduce T16 untyped walk/listen before production changes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.human_adjacent_focus import classify_human_adjacent_intent_family  # noqa: E402
from game.intent_parser import (  # noqa: E402
    TRAVEL_PREFIXES,
    _strip_speaker_commitment_prefix,
    parse_freeform_to_action,
    parse_intent,
)
from game.interaction_routing import is_world_action  # noqa: E402
from game.scene_destination_binding import (  # noqa: E402
    extract_travel_destination_phrase,
    resolve_authored_exit_from_player_travel,
)

T16 = "I walk a few steps along the muddy gate line and listen"
FRONTIER = {
    "scene": {
        "id": "frontier_gate",
        "exits": [
            {"label": "Enter Cinderwatch", "target_scene_id": "market_quarter"},
            {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"},
        ],
        "visible_facts": [
            "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
            "A gate serjeant manages the crowd and keeps one eye on the roster board.",
            "A tavern runner trades hot stew and rumors near the rain barrel.",
            "Threadbare watchers and refugees cluster along the muddy gate line.",
        ],
        "interactables": [{"id": "notice_board", "label": "Notice board", "type": "investigate"}],
        "discoverable_clues": [],
    }
}


def _trace(text: str, scene=None) -> dict:
    low = text.strip().lower()
    stripped = _strip_speaker_commitment_prefix(text)
    prefix_hits = [p for p in TRAVEL_PREFIXES if stripped.lower().startswith(p) or low.startswith(p)]
    dest = extract_travel_destination_phrase(text)
    authored = resolve_authored_exit_from_player_travel(text, (scene or FRONTIER)["scene"]["exits"])
    parsed = parse_freeform_to_action(text, scene or FRONTIER)
    fallback = parse_intent(text)
    return {
        "raw": text,
        "normalized": text.strip(),
        "ha_family": classify_human_adjacent_intent_family(text),
        "stripped_commitment": stripped,
        "travel_prefix_hits": prefix_hits,
        "extracted_dest": dest,
        "authored_exit": authored,
        "is_world_action": is_world_action(text),
        "parsed": parsed,
        "parse_intent_fallback": fallback,
        "kind": (parsed or {}).get("type") if parsed else None,
        "lane": ((parsed or {}).get("metadata") or {}).get("parser_lane") if parsed else None,
    }


def main() -> int:
    cases = [
        T16,
        "I walk a few steps along the muddy gate line.",
        "I listen.",
        "I listen by the gate line.",
        "I walk along the gate line and listen.",
        "I walk toward the northern road.",
        "I leave through the eastern arch.",
        "I head for the silver road.",
        "I step closer to the fountain.",
        "I pace beside the wall.",
        "I walk to the market.",
        "I eavesdrop on the refugees",
        "I move closer to the gossiping group and listen in",
    ]
    payload = {c: _trace(c) for c in cases}
    out = Path(__file__).resolve().parent / "repro_before.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
