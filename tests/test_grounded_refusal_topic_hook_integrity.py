"""PR-AV: a refusal topic hook must be a meaningful asked subject.

Kiln-yard / cedar-wharf vocabulary is the scenario-independent gate.
Frontier Gate / stew strings are calibration residue only.
"""
from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.final_emission_validators import _contains_fabricated_authority
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import (
    apply_authored_knowledge_realization_to_gm,
    player_facing_invents_unauthored_social_fact,
    realize_authored_knowledge_answer,
    resolve_social_action,
)
from game.social_exchange_emission import build_final_strict_social_response
from game.social_exchange_fallback_catalog import (
    _integrity_topic_hook,
    social_integrity_fallback_line_candidates,
    strict_social_ownership_terminal_fallback,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "stew",
    "tavern_runner",
    "notice_board",
    "frontier_gate",
    "missing_patrol",
    "Cinderwatch",
    "Captain Thoran",
    "guard_captain",
    "old_milestone",
    "roster_board",
)
INTERNAL_TERMS = (
    "authored answer",
    "not in state",
    "dimension is unsupported",
    "eligible topic candidate",
    "clue_knowledge",
    "topic_revealed",
    "grounded absence",
    "answer sufficiency",
)
MASH_EXISTS = "A kettle of mash sits on the porter's brazier."
LEDGER_OWNER = "Clerk Harun at the tally desk keeps the firing ledgers."
BROTH_EXISTS = "A kettle of broth sits on the brazier."
INVENTED_PRICE = 'Night Porter says, "Two coppers a ladle, and the kettle is still hot."'
INVENTED_TIME = 'Night Porter mutters, "Word is, they were due to leave sometime before dawn."'
INVENTED_COUNT = 'Night Porter says, "Seven dozen, stacked against the north wall."'
INVENTED_IDENTITY = 'Night Porter says, "Mira from the dock office checked it after the second bell."'
INVENTED_REDIRECT = 'Night Porter says, "Speak to the ward clerk by the main gate if that still matters."'
KNOWN_STEP = "I step back to the tavern runner and ask who last checked that board."
KNOWN_NIGHT = "I ask the night porter when the kiln crew actually left."
ABOUT_TOKEN_RE = re.compile(r"\babout\s+([a-z]{3,})\b", re.IGNORECASE)


def _kiln_scene() -> dict:
    return {
        "scene": {
            "id": "kiln_yard",
            "location": "Kiln Yard",
            "summary": "A brick kiln, a tally slate, and a night porter.",
            "visible_facts": [
                "A brick kiln smokes under a tin roof.",
                "A tally slate hangs by the kiln door.",
                MASH_EXISTS,
            ],
            "hidden_facts": [],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "night_porter",
                    "name": "Night Porter",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["porter"],
                }
            ],
            "interactables": [
                {
                    "id": "tally_slate",
                    "label": "Tally slate",
                    "aliases": ["slate", "board"],
                    "type": "investigate",
                }
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _kiln_world(*, porter_topics: list[dict] | None = None) -> dict:
    return {
        "npcs": [
            {
                "id": "night_porter",
                "name": "Night Porter",
                "location": "kiln_yard",
                "aliases": ["porter"],
                "topics": porter_topics
                if porter_topics is not None
                else [{"id": "mash_exists", "text": MASH_EXISTS}],
            }
        ]
    }


def _wharf_scene() -> dict:
    return {
        "scene": {
            "id": "cedar_wharf",
            "location": "Cedar Wharf",
            "summary": "A quiet wharf and a lamp clerk.",
            "visible_facts": [BROTH_EXISTS],
            "hidden_facts": [],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "lamp_clerk",
                    "name": "Lamp Clerk",
                    "scene_id": "cedar_wharf",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["clerk"],
                }
            ],
            "interactables": [],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _wharf_world() -> dict:
    return {
        "npcs": [
            {
                "id": "lamp_clerk",
                "name": "Lamp Clerk",
                "location": "cedar_wharf",
                "aliases": ["clerk"],
                "topics": [{"id": "broth_exists", "text": BROTH_EXISTS}],
            }
        ]
    }


def _session_for(world: dict, scene: dict) -> dict:
    session = default_session()
    session["active_scene_id"] = scene["scene"]["id"]
    rebuild_active_scene_entities(session, world, scene["scene"]["id"], scene_envelope=scene)
    return session


def _ask(world: dict, session: dict, npc_id: str, player_text: str, scene: dict) -> dict:
    return resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question",
            "label": player_text,
            "type": "question",
            "prompt": player_text,
            "target_id": npc_id,
        },
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=int(session.get("turn_counter") or 1),
    )


def _refusal_resolution(npc_id: str, npc_name: str) -> dict:
    return {
        "kind": "question",
        "prompt": "",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": npc_name,
            "reply_kind": "refusal",
            "npc_reply_expected": True,
        },
    }


def _integrity_refusal_line(player_text: str, *, npc_id: str, npc_name: str) -> str:
    resolution = _refusal_resolution(npc_id, npc_name)
    cands = social_integrity_fallback_line_candidates(
        resolution=resolution,
        player_text=player_text,
        session=default_session(),
        scene_id="kiln_yard",
        tag_list=[],
        seed="prav-hook",
    )
    for line, kind in cands:
        if kind == "integrity_refusal_boundary":
            return line
    raise AssertionError(f"no integrity refusal for {player_text!r}: {cands}")


def _about_tokens(text: str) -> list[str]:
    return [m.group(1).lower() for m in ABOUT_TOKEN_RE.finditer(str(text or ""))]


def _assert_grounded_refusal(text: str) -> str:
    raw = str(text or "").strip()
    assert raw
    low = raw.lower()
    for term in INTERNAL_TERMS:
        assert term not in low
    assert not raw.endswith("…")
    assert raw[-1] in '.!?"”\''
    return raw


def test_known_step_case_does_not_hook_step():
    player = KNOWN_STEP
    resolution = _refusal_resolution("tavern_runner", "Tavern Runner")
    hook = _integrity_topic_hook(player, resolution)
    assert hook != "step"
    line = _integrity_refusal_line(player, npc_id="tavern_runner", npc_name="Tavern Runner")
    assert "about step" not in line.lower()
    about = _about_tokens(line)
    assert "step" not in about
    if about:
        assert about[0] in {"board", "checked"}


def test_known_night_case_does_not_hook_night():
    player = KNOWN_NIGHT
    resolution = _refusal_resolution("night_porter", "Night Porter")
    hook = _integrity_topic_hook(player, resolution)
    assert hook != "night"
    assert hook != "porter"
    line = _integrity_refusal_line(player, npc_id="night_porter", npc_name="Night Porter")
    assert "about night" not in line.lower()
    about = _about_tokens(line)
    assert "night" not in about
    if about:
        assert about[0] in {"kiln", "crew"}


def test_novel_movement_token_cannot_become_refusal_topic():
    player = "I amble past the lamp clerk and ask how many barrels remain."
    resolution = _refusal_resolution("lamp_clerk", "Lamp Clerk")
    hook = _integrity_topic_hook(player, resolution)
    assert hook != "amble"
    line = _integrity_refusal_line(player, npc_id="lamp_clerk", npc_name="Lamp Clerk")
    assert "about amble" not in line.lower()
    about = _about_tokens(line)
    assert "amble" not in about
    assert hook == "barrels" or (about and about[0] == "barrels")


def test_novel_temporal_token_cannot_become_refusal_topic():
    player = "I ask the lamp clerk this morning how many barrels remain."
    resolution = _refusal_resolution("lamp_clerk", "Lamp Clerk")
    hook = _integrity_topic_hook(player, resolution)
    assert hook not in {"morning", "lamp", "clerk"}
    line = _integrity_refusal_line(player, npc_id="lamp_clerk", npc_name="Lamp Clerk")
    low = line.lower()
    assert "about morning" not in low
    assert "about lamp" not in low
    about = _about_tokens(line)
    assert "morning" not in about
    assert hook == "barrels" or (about and about[0] == "barrels")


def test_legitimate_semantic_topic_can_still_hook():
    player = "I ask the lamp clerk about the tarred coils."
    resolution = _refusal_resolution("lamp_clerk", "Lamp Clerk")
    hook = _integrity_topic_hook(player, resolution)
    assert hook == "coils"
    line = _integrity_refusal_line(player, npc_id="lamp_clerk", npc_name="Lamp Clerk")
    assert "about coils" in line.lower()
    assert "about lamp" not in line.lower()


def test_no_trustworthy_topic_degrades_without_about_hook():
    player = "I ask the lamp clerk."
    resolution = _refusal_resolution("lamp_clerk", "Lamp Clerk")
    hook = _integrity_topic_hook(player, resolution)
    assert hook == ""
    assert _integrity_topic_hook(player) == ""
    line = _integrity_refusal_line(player, npc_id="lamp_clerk", npc_name="Lamp Clerk")
    assert "about " not in line.lower()
    assert "won't answer that" in line.lower()
    assert "not here" in line.lower()


def test_integrity_echo_path_does_not_mint_bogus_step_or_night_topics():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_for(world, scene)
    set_social_target(session, "night_porter")
    player = KNOWN_NIGHT
    resolution = _ask(world, session, "night_porter", player, scene)
    echo = f'Night Porter tilts their head. "{player}"'
    out, details = build_final_strict_social_response(
        echo,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id="kiln_yard",
        world=world,
    )
    low = out.lower()
    _assert_grounded_refusal(out)
    assert "about night" not in low
    assert "about porter" not in low
    assert "two coppers" not in low
    assert "before dawn" not in low
    assert details.get("social_emission_integrity_replaced") is True or "won't answer" in low or "do not know" in low or "don't know" in low


def test_novel_sidle_question_does_not_hook_movement_on_echo_path():
    scene = _wharf_scene()
    world = _wharf_world()
    session = _session_for(world, scene)
    set_social_target(session, "lamp_clerk")
    player = "I sidle up to the lamp clerk and ask how many barrels remain."
    resolution = _ask(world, session, "lamp_clerk", player, scene)
    echo = f'Lamp Clerk repeats, "{player}"'
    out, details = build_final_strict_social_response(
        echo,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id="cedar_wharf",
        world=world,
    )
    low = out.lower()
    _assert_grounded_refusal(out)
    assert "about sidle" not in low
    assert "about lamp" not in low
    assert "seven dozen" not in low
    about = _about_tokens(out)
    assert "sidle" not in about
    if about:
        assert about[0] == "barrels"
    assert details.get("social_emission_integrity_replaced") is True or "barrels" in low or "don't know" in low or "do not know" in low


def test_refusal_does_not_invent_the_missing_answer():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_for(world, scene)
    player = KNOWN_NIGHT
    resolution = _ask(world, session, "night_porter", player, scene)
    line = _integrity_refusal_line(player, npc_id="night_porter", npc_name="Night Porter")
    assert realize_authored_knowledge_answer(
        session=session,
        scene_id="kiln_yard",
        player_text=player,
        resolution=resolution,
        world=world,
        scene=scene,
    ) is None
    assert not player_facing_invents_unauthored_social_fact(
        line,
        speaker_id="night_porter",
        speaker_name="Night Porter",
    )
    low = line.lower()
    assert "before dawn" not in low
    assert "left at" not in low
    assert "second bell" not in low


def test_prau_price_time_count_identity_redirect_non_invention_remains():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_for(world, scene)
    cases = (
        ("I ask the night porter how much the mash costs.", INVENTED_PRICE, ("two coppers", "copper")),
        ("I ask the night porter when the kiln crew actually left.", INVENTED_TIME, ("before dawn",)),
        ("I ask the night porter how many bricks are left in that stack.", INVENTED_COUNT, ("seven dozen",)),
        ("I ask the night porter who last read that tally slate.", INVENTED_IDENTITY, ("mira", "dock office")),
        ("I ask the night porter who keeps the firing ledgers.", INVENTED_REDIRECT, ("ward clerk", "main gate")),
    )
    for player, invented, banned in cases:
        resolution = _ask(world, session, "night_porter", player, scene)
        gm = apply_authored_knowledge_realization_to_gm(
            {"player_facing_text": invented, "tags": []},
            player_text=player,
            resolution=resolution,
            session=session,
            world=world,
            scene=scene,
            scene_id="kiln_yard",
        )
        text = str(gm.get("player_facing_text") or "")
        _assert_grounded_refusal(text)
        low = text.lower()
        for token in banned:
            assert token not in low
        assert text != invented


def test_prap_from_what_i_know_hedge_remains_intact():
    resolution = _refusal_resolution("night_porter", "Night Porter")
    catalog = strict_social_ownership_terminal_fallback(resolution)
    assert "from what." not in catalog.lower()
    if "from what i know" in catalog.lower():
        assert _contains_fabricated_authority(catalog) is False


def test_authored_social_fact_still_realizes():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_for(world, scene)
    player = "I ask the night porter what sits on the brazier."
    resolution = _ask(world, session, "night_porter", player, scene)
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": 'Night Porter mutters, "Word is, a kettle of mash sits on the porter\'s brazier."', "tags": []},
        player_text=player,
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
        scene_id="kiln_yard",
    )
    soc = resolution.get("social") or {}
    assert isinstance(soc.get("topic_revealed"), dict)
    text = str(gm.get("player_facing_text") or "").lower()
    assert "kettle of mash" in text


def test_authored_redirect_still_realizes():
    scene = _kiln_scene()
    world = _kiln_world(porter_topics=[{"id": "ledger_owner", "text": LEDGER_OWNER}])
    session = _session_for(world, scene)
    player = "I ask the night porter who keeps the firing ledgers."
    resolution = _ask(world, session, "night_porter", player, scene)
    gm = apply_authored_knowledge_realization_to_gm(
        {
            "player_facing_text": 'Night Porter mutters, "Word is, Clerk Harun at the tally desk keeps the firing ledgers."',
            "tags": [],
        },
        player_text=player,
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
        scene_id="kiln_yard",
    )
    text = str(gm.get("player_facing_text") or "").lower()
    assert "harun" in text
    assert "tally desk" in text


def _seed_kiln_http(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    envelope = _kiln_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = _kiln_world()["npcs"]
    storage._save_json(storage.WORLD_PATH, w)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    rebuild_active_scene_entities(session, w, sid, scene_envelope=envelope)
    set_social_target(session, "night_porter")
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return sid


def test_http_known_night_question_does_not_emit_about_night(tmp_path, monkeypatch):
    _seed_kiln_http(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda _messages: _gm_response(f'Night Porter tilts their head. "{KNOWN_NIGHT}"'),
    )
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": KNOWN_NIGHT})
    assert resp.status_code == 200
    text = str(((resp.json().get("gm_output") or {}).get("player_facing_text")) or "")
    _assert_grounded_refusal(text)
    low = text.lower()
    assert "about night" not in low
    assert "before dawn" not in low
    assert "two coppers" not in low


def test_no_hardcoded_step_or_night_special_case_in_hook_owner():
    blob = Path("game/social_exchange_fallback_catalog.py").read_text(encoding="utf-8")
    start = blob.find("def _question_span_for_integrity_hook")
    end = blob.find("def minimal_social_emergency_fallback_line")
    helper = blob[start:end]
    assert helper
    assert re.search(r'["\']step["\']', helper) is None
    assert re.search(r'["\']night["\']', helper) is None
    for term in CALIBRATION_ENGINE_TERMS:
        assert term.lower() not in helper.lower(), f"{term} in PR-AV hook helper"


def test_no_frontier_gate_special_case_in_touched_engine():
    catalog = Path("game/social_exchange_fallback_catalog.py").read_text(encoding="utf-8")
    start = catalog.find("def _question_span_for_integrity_hook")
    end = catalog.find("def minimal_social_emergency_fallback_line")
    helper = catalog[start:end]
    assert helper
    for term in CALIBRATION_ENGINE_TERMS:
        assert term.lower() not in helper.lower(), f"{term} in new catalog hook helper"
