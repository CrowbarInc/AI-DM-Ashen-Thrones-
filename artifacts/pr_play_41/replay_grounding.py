"""Offline replay of addressee grounding against the saved PR-PLAY-41 store.

Does not start a worker and does not call a provider. Used only to compare
the persisted scene with the live clarification record.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from game.conversational_orchestration import authored_travel_admission
from game.storage import build_effective_scene
from game.incidental_entity import public_scene_text
from game.ordinary_semantic_ownership import (
    _DETERMINERS,
    _PUBLIC_REFERENCE_STOPWORDS,
    _npc_reference_words,
    _public_npc_candidates,
    _reference_token,
    _visible_npcs,
    assess_addressee_grounding,
)

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "artifacts" / "atgb" / "pr_play_41" / "live" / "20261102T110016Z-47c71d381798"


def unwrap(document):
    if isinstance(document, dict) and isinstance(document.get("payload"), dict):
        return document["payload"]
    return document


def load(label):
    base = RUN / label / "persistent"
    scene = json.loads((base / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
    world = unwrap(json.loads((base / "world.json").read_text(encoding="utf-8")))
    session = unwrap(json.loads((base / "session.json").read_text(encoding="utf-8")))
    return scene, world, session


def tokens(text):
    out = []
    for word in re.findall(r"[a-z0-9']+", text.lower()):
        if len(word) < 4 or word in _PUBLIC_REFERENCE_STOPWORDS or word in _DETERMINERS:
            continue
        out.append(word)
        stem = _reference_token(word)
        if stem != word and stem not in _PUBLIC_REFERENCE_STOPWORDS and len(stem) >= 4:
            out.append(stem)
    return out


CASES = (
    ("turns/T2/before", "Have you heard any interesting rumors lately?", "tavern_runner"),
    ("turns/T3/before", "I examine the notice board.", "notice_board"),
    ("turns/T4/before", "I want to follow the trail connected to the missing patrol.", "leave_for_follow_the_missing_patrol_rumor"),
    ("turns/T4/before", "Go to Follow the missing patrol rumor.", "leave_for_follow_the_missing_patrol_rumor"),
)


def main():
    for label, text, proposed in CASES:
        scene, world, session = load(label)
        overlay = (session.get("runtime_scene_overlays") or {}).get("frontier_gate") or {}
        scene = build_effective_scene(scene, overlay)
        npcs = _visible_npcs(scene, world)
        print("====", label)
        print("TEXT", text)
        print("TOKENS", tokens(text))
        print("PUBLIC_LEN", len(public_scene_text(scene)))
        for npc in npcs:
            words = _npc_reference_words(npc, scene)
            hit = [token for token in tokens(text) if token in words]
            if hit:
                print(" HIT", npc.get("id"), hit)
        kind, chosen = _public_npc_candidates(text, npcs, scene)
        print("PUBLIC", kind, [row.get("id") for row in chosen])
        ctx = session.get("conversational_context")
        print("CONTEXT", sorted(ctx) if isinstance(ctx, dict) else ctx)
        grounding = assess_addressee_grounding(
            text, scene=scene, world=world, session=session, proposed_target_id=proposed,
        )
        print(
            "GROUND",
            grounding.get("target_resolution"),
            grounding.get("target_id"),
            grounding.get("operation_eligibility"),
            grounding.get("direct_address"),
            grounding.get("clarification"),
        )
        travel = authored_travel_admission(text, scene=scene, world=world, session=session)
        if travel is None:
            print("TRAVEL none")
        else:
            print("TRAVEL", travel.category, travel.reason, travel.primary_intention, travel.proposed_target)


if __name__ == "__main__":
    main()
