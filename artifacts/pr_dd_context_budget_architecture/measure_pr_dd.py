"""PR-DD deterministic provider-context inventory. No provider calls. No saves."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import game.gm as gm
from game.defaults import default_campaign, default_character, default_combat, default_conditions
from game.gm_retry import build_retry_prompt_for_failure
from game.storage import DATA_DIR, list_scene_ids, load_scene
from tests.test_combat_resolution import _scene_with_goblin
from tests.test_pr_db_speaker_grounding import (
    TURN_1,
    TURN_2,
    TURN_3,
    _bind_guard,
    _focus,
    _gate_session_scene,
    play_turn,
)

OUT = Path(__file__).resolve().parent
WATCH = [
    DATA_DIR / "session.json",
    DATA_DIR / "world.json",
    DATA_DIR / "combat.json",
    DATA_DIR / "session_log.jsonl",
    DATA_DIR / "character.json",
    DATA_DIR / "campaign.json",
]


def _mtimes() -> dict:
    out = {}
    for path in WATCH:
        out[str(path.name)] = path.stat().st_mtime_ns if path.exists() else None
    return out


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bytes(value) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def _messages_for(result_resolution, session, scene, world, player, *, history=None, combat=None, character=None):
    from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, build_runtime_ctir_for_narration
    from game.narration_plan_bundle import build_narration_plan_bundle, ensure_narration_plan_bundle_for_turn

    scene = dict(scene)
    scene.pop("_is_canon", None)
    combat = combat if isinstance(combat, dict) else default_combat()
    character = character if isinstance(character, dict) else default_character()
    history = list(history or [])
    stamp = "pr-dd"
    attach_ctir(
        session,
        build_runtime_ctir_for_narration(
            turn_id=stamp,
            scene_id=str((scene.get("scene") or {}).get("id") or session.get("active_scene_id") or ""),
            player_input=player,
            builder_source="artifacts.pr_dd_context_budget_architecture",
            resolution=result_resolution,
            normalized_action={"type": "question", "prompt": player, "label": player},
            combat=combat,
            session=session,
            world=world,
        ),
    )
    session[SESSION_CTIR_STAMP_KEY] = stamp
    with patch.object(gm, "get_effective_scene", return_value=scene):
        kwargs = gm.collect_narration_context_call_kwargs(
            default_campaign(),
            world,
            session,
            character,
            scene,
            combat,
            history,
            player,
            resolution=result_resolution,
            scene_runtime={},
        )
    bundle_kwargs = dict(kwargs)
    bundle_kwargs.pop("known_answer_hint", None)
    ensure_narration_plan_bundle_for_turn(
        session,
        turn_stamp=stamp,
        builder=lambda: build_narration_plan_bundle(session=session, narration_context_kwargs=bundle_kwargs),
    )
    return gm.build_messages(
        default_campaign(),
        world,
        session,
        character,
        scene,
        combat,
        history,
        player,
        resolution=result_resolution,
        scene_runtime={},
        narration_context_call_kwargs=kwargs,
    )


def _split(messages):
    system = ""
    user_parts = []
    for item in messages:
        role = item.get("role")
        content = item.get("content") if isinstance(item, dict) else ""
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        if role == "system":
            system += content
        else:
            user_parts.append(content)
    blob = "\n".join([system, *user_parts])
    payload = None
    for part in user_parts:
        try:
            parsed = json.loads(part)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and ("player_input" in parsed or "response_policy" in parsed or "scene" in parsed):
            payload = parsed
            break
    return blob, system, user_parts, payload


def _social(text: str, *, prior: list[str] | None = None, bind: bool = False):
    session, scene, world = _gate_session_scene()
    if bind:
        _bind_guard(session)
        _focus(session, "guard_captain", "Guard Captain")
    for earlier in prior or []:
        play_turn(session, scene, world, earlier)
        session["turn_counter"] = int(session.get("turn_counter") or 0) + 1
    result = play_turn(session, scene, world, text)
    return session, scene, world, result["resolution"], result


def _explore(text: str):
    from game.intent_parser import parse_freeform_to_action
    from game.live_resolution import attach_interaction_obligation
    from game.noncombat_resolution import resolve_noncombat_action
    from game.ordinary_semantic_ownership import select_ordinary_resolver

    session, scene, world = _gate_session_scene()
    parsed = parse_freeform_to_action(text, scene)
    if not isinstance(parsed, dict):
        parsed = {"type": "custom", "label": text, "prompt": text}
    parsed = dict(parsed)
    parsed.setdefault("label", text)
    parsed.setdefault("prompt", text)
    parsed.setdefault("id", "pr_dd_explore")
    resolution = resolve_noncombat_action(
        scene,
        session,
        world,
        parsed,
        raw_player_text=text,
        character=default_character(),
        turn_counter=int(session.get("turn_counter") or 0),
        exploration_kwargs={
            "list_scene_ids": list_scene_ids,
            "load_scene_fn": load_scene,
        },
    )
    attach_interaction_obligation(
        resolution,
        player_text=text,
        session=session,
        normalized_action=parsed,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
        enable_model_interpretation=False,
    )
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = metadata.get("resolution_contract") if isinstance(metadata.get("resolution_contract"), dict) else {}
    resolver = None
    if contract:
        resolver, _family = select_ordinary_resolver(contract)
        metadata["selected_resolver"] = resolver
        metadata["ordinary_contract_established"] = True
    return session, scene, world, resolution, {"parsed_type": parsed.get("type"), "resolver": resolver, "kind": resolution.get("kind")}


def _inventory(label, player, messages, *, source, limitation, meta):
    blob, system, user_parts, payload = _split(messages)
    total = len(blob.encode("utf-8"))
    system_bytes = len(system.encode("utf-8"))
    rows = []
    projection = None
    policy = {}
    if isinstance(payload, dict):
        projection = payload.get("provider_context_projection")
        policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
        for key, value in payload.items():
            size = _bytes({key: value})
            rows.append({"section": key, "bytes": size, "pct_of_request": round(100 * size / total, 2) if total else 0})
    rows.sort(key=lambda row: row["bytes"], reverse=True)
    policy_children = []
    if isinstance(policy, dict):
        policy_bytes = _bytes(policy)
        for key, value in policy.items():
            size = _bytes({key: value})
            policy_children.append({
                "section": f"response_policy.{key}",
                "bytes": size,
                "pct_of_policy": round(100 * size / policy_bytes, 2) if policy_bytes else 0,
                "pct_of_request": round(100 * size / total, 2) if total else 0,
            })
        policy_children.sort(key=lambda row: row["bytes"], reverse=True)
    instructions = payload.get("instructions") if isinstance(payload, dict) else []
    instruction_bytes = 0
    exact_system_dup_bytes = 0
    exact_system_dup_count = 0
    if isinstance(instructions, list):
        for item in instructions:
            if not isinstance(item, str):
                continue
            size = len(item.encode("utf-8"))
            instruction_bytes += size
            if item and item in system:
                exact_system_dup_bytes += size
                exact_system_dup_count += 1
    mirrors = []
    if isinstance(payload, dict) and isinstance(policy, dict):
        for key, value in policy.items():
            for top in (key, f"{key}_contract"):
                if top in payload and top != "response_policy":
                    same = json.dumps(payload.get(top), ensure_ascii=False, sort_keys=True) == json.dumps(value, ensure_ascii=False, sort_keys=True)
                    mirrors.append({"policy_key": key, "top_key": top, "exact_equal": same, "top_bytes": _bytes(payload.get(top))})
    hidden = []
    scene = meta.get("hidden_facts") or []
    for fact in scene:
        if isinstance(fact, str) and fact and fact in blob:
            hidden.append(_sha(fact)[:12])
    social = {}
    mechanical = payload.get("mechanical_resolution") if isinstance(payload, dict) and isinstance(payload.get("mechanical_resolution"), dict) else {}
    if isinstance(mechanical.get("social"), dict):
        social = mechanical["social"]
    return {
        "label": label,
        "player": player,
        "source": source,
        "limitation": limitation,
        "message_count": len(messages),
        "roles": [item.get("role") for item in messages],
        "serialized_bytes": total,
        "serialized_chars": len(blob),
        "estimated_tokens_ceil_chars_div_4": (len(blob) + 3) // 4,
        "tokenizer": "unavailable_estimate_ceil_chars_div_4",
        "sha256": _sha(blob),
        "system_bytes": system_bytes,
        "system_estimated_tokens": (len(system) + 3) // 4,
        "user_message_count": len(user_parts),
        "structured_context_bytes": sum(len(part.encode("utf-8")) for part in user_parts),
        "response_policy_bytes": _bytes(policy) if policy else 0,
        "instructions_bytes": _bytes(instructions) if isinstance(instructions, list) else 0,
        "recent_history_bytes": _bytes({
            "recent_log": (payload or {}).get("recent_log"),
            "selected_conversational_memory": (payload or {}).get("selected_conversational_memory"),
            "conversational_memory_window": (payload or {}).get("conversational_memory_window"),
        }) if isinstance(payload, dict) else 0,
        "retry_only_bytes": 0,
        "envelope": gm._provider_response_contract_from_messages(messages),
        "projection_selected": isinstance(projection, dict) and projection.get("selected") is True,
        "projection_mode": projection.get("mode") if isinstance(projection, dict) else None,
        "omitted_sections": projection.get("omitted_sections") if isinstance(projection, dict) else [],
        "compacted_sections": projection.get("compacted_sections") if isinstance(projection, dict) else [],
        "top_sections": rows[:25],
        "section_count": len(rows),
        "policy_children": policy_children[:20],
        "instruction_count": len(instructions) if isinstance(instructions, list) else 0,
        "instruction_text_bytes": instruction_bytes,
        "exact_system_duplicate_instruction_count": exact_system_dup_count,
        "exact_system_duplicate_instruction_bytes": exact_system_dup_bytes,
        "policy_top_level_mirrors": mirrors,
        "hidden_fact_sha12_present": hidden,
        "resolution_kind": (payload or {}).get("resolution_kind") or meta.get("kind") or mechanical.get("kind"),
        "selected_resolver": ((mechanical.get("metadata") or {}) if isinstance(mechanical.get("metadata"), dict) else {}).get("selected_resolver") or meta.get("resolver"),
        "reply_plan_kind": social.get("reply_plan_kind"),
        "contract_operation": ((payload or {}).get("resolution_contract") or {}).get("operation") if isinstance((payload or {}).get("resolution_contract"), dict) else None,
        "skill_check_present": bool((payload or {}).get("skill_check") or mechanical.get("skill_check")),
        "combat_in_payload": (payload or {}).get("combat") if isinstance(payload, dict) else None,
        "top_level_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
    }


def _history(n: int) -> list[dict]:
    fact = "The notice board lists taxes, curfew rules, and a warning about a missing patrol."
    rows = []
    for i in range(n):
        rows.append({
            "player_input": TURN_1,
            "gm_output": {"player_facing_text": fact},
            "request": {"chat": TURN_1},
        })
    return rows


def main() -> None:
    before = _mtimes()
    cases = []

    def add_social(label, text, *, prior=None, bind=False, source="authored frontier_gate via tests.test_pr_db_speaker_grounding.play_turn"):
        session, scene, world, resolution, view = _social(text, prior=prior, bind=bind)
        messages = _messages_for(resolution, session, scene, world, text)
        hidden = ((scene.get("scene") or {}).get("hidden_facts") or [])
        cases.append(_inventory(
            label, text, messages, source=source, limitation="",
            meta={"hidden_facts": hidden, "kind": view.get("parsed_type"), "resolver": view.get("resolver")},
        ))

    add_social("01_harmless_npc_preference", TURN_1)
    add_social("02_npc_experiential_followup", TURN_2, prior=[TURN_1])
    add_social(
        "03_authored_npc_factual",
        "Captain, what do you know about the missing patrol?",
        bind=True,
        source="authored frontier_gate; player line from tests/test_pr_cp_authorized_finalization.py",
    )
    add_social(
        "07_consequential_social",
        "Does rain make it easier to assassinate the captain?",
        bind=True,
        source="authored frontier_gate; player line from PR-DC negative control",
    )
    add_social(
        "10_hidden_information_question",
        "Where is the secret tunnel?",
        bind=True,
        source="authored frontier_gate; player line from PR-DC negative control",
    )
    add_social("12_multiturn_continuation", TURN_3, prior=[TURN_1, TURN_2])

    explore_lines = [
        ("04_notice_board_inspection", "I examine the notice board for anything unusual.", "player line from tests/test_pr_cp_authorized_finalization.py and PR-CO"),
        ("05_ordinary_scene_observation", "I look around.", "parser pattern observe; authored frontier_gate"),
        ("05b_pr_co_observation_line", "Describe what I can see around me here at the gate.", "exact PR-CO turn 5 line"),
        ("06_ordinary_movement", "I walk closer to the notice board.", "movement-shaped line on authored frontier_gate; record actual resolver"),
        ("11_scene_transition", "Enter Cinderwatch", "authored exit label on frontier_gate"),
    ]
    for label, text, source in explore_lines:
        session, scene, world, resolution, view = _explore(text)
        messages = _messages_for(resolution, session, scene, world, text)
        hidden = ((scene.get("scene") or {}).get("hidden_facts") or [])
        cases.append(_inventory(
            label, text, messages,
            source=source,
            limitation="" if view.get("kind") else "resolution kind missing",
            meta={"hidden_facts": hidden, **view},
        ))

    # Authored frontier gate has no skill_check config and no enemies.
    session, scene, world, resolution, view = _explore("I search the muddy approach for tracks.")
    messages = _messages_for(resolution, session, scene, world, "I search the muddy approach for tracks.")
    cases.append(_inventory(
        "08_mechanical_skill_check_authored_attempt",
        "I search the muddy approach for tracks.",
        messages,
        source="authored frontier_gate; no skill_check config exists in data/scenes",
        limitation="no authored skill_check fired" if not view else "",
        meta={"hidden_facts": (scene.get("scene") or {}).get("hidden_facts") or [], **view},
    ))

    # Existing synthetic skill fixture from tests/test_exploration_skill_checks.py. Not campaign canon.
    from game.exploration import resolve_exploration_action
    from game.scene_actions import normalize_scene_action

    skill_scene = {"scene": {"id": "x", "location": "X", "skill_check_defaults": {"investigate": {"skill_id": "perception", "dc": 8}}}}
    skill_character = default_character()
    skill_character.setdefault("skills", {})["perception"] = 2
    action = normalize_scene_action({"id": "inv", "label": "Investigate", "type": "investigate", "prompt": "Search."})
    skill_session = {"active_scene_id": "x", "turn_counter": 1, "scene_state": {"active_scene_id": "x"}}
    skill_world = {"npcs": []}
    skill_resolution = resolve_exploration_action(
        skill_scene, skill_session, skill_world, action, raw_player_text="Search.", character=skill_character, list_scene_ids=lambda: []
    )
    from game.live_resolution import attach_interaction_obligation
    attach_interaction_obligation(
        skill_resolution, player_text="Search.", session=skill_session, normalized_action=action,
        scene_id="x", scene=skill_scene, world=skill_world, enable_model_interpretation=False,
    )
    skill_messages = _messages_for(skill_resolution, skill_session, skill_scene, skill_world, "Search.", character=skill_character)
    cases.append(_inventory(
        "08b_mechanical_skill_check_synthetic_fixture",
        "Search.",
        skill_messages,
        source="existing fixture tests/test_exploration_skill_checks.py::test_gpt_payload_includes_skill_check_when_resolved",
        limitation="synthetic scene id x; not authored campaign state; included only to expose skill-check prompt shape",
        meta={"hidden_facts": [], "kind": skill_resolution.get("kind"), "resolver": None},
    ))

    # Existing synthetic combat fixture. Fixed die so the hash is reproducible.
    combat_scene = {"scene": _scene_with_goblin()["scene"]}
    combat_state = {"in_combat": True, "round": 1, "initiative_order": [], "turn_index": 0, "active_actor_id": "galinor", "player_turn_used": False}
    with patch("game.combat.roll_die", return_value=10):
        from game.combat import resolve_attack
        attack = resolve_attack(default_character(), combat_scene, "quarterstaff", "goblin_1", [], default_conditions())
    combat_session = {"active_scene_id": "frontier_gate", "turn_counter": 1, "scene_state": {"active_scene_id": "frontier_gate"}}
    combat_world = {"npcs": []}
    from game.live_resolution import attach_interaction_obligation as attach_ob
    attach_ob(
        attack, player_text="I attack the goblin with my quarterstaff.", session=combat_session,
        normalized_action={"type": "attack", "prompt": "I attack the goblin with my quarterstaff.", "label": "Attack"},
        scene_id="frontier_gate", scene=combat_scene, world=combat_world, enable_model_interpretation=False,
    )
    combat_messages = _messages_for(
        attack, combat_session, combat_scene, combat_world, "I attack the goblin with my quarterstaff.", combat=combat_state,
    )
    cases.append(_inventory(
        "09_combat_action_synthetic_fixture",
        "I attack the goblin with my quarterstaff.",
        combat_messages,
        source="existing fixture tests/test_combat_resolution.py::_scene_with_goblin; roll_die patched to 10",
        limitation="authored scenes have empty enemies; goblin is a test fixture, not campaign canon",
        meta={"hidden_facts": [], "kind": attack.get("kind"), "resolver": None},
    ))

    # History growth on the harmless preference, using authored visible fact snippets.
    session, scene, world, resolution, view = _social(TURN_1)
    for n in (0, 4, 8):
        messages = _messages_for(resolution, session, scene, world, TURN_1, history=_history(n))
        row = _inventory(
            f"H{n}_history_growth_preference",
            TURN_1,
            messages,
            source="same harmless preference resolution; recent_log entries repeat an authored visible fact",
            limitation="size probe, not a played transcript",
            meta={"hidden_facts": [], "kind": view.get("parsed_type"), "resolver": view.get("resolver")},
        )
        cases.append(row)

    # Hypothetical retry append. Not a captured provider retry.
    pref = next(row for row in cases if row["label"] == "01_harmless_npc_preference")
    # Rebuild once to get the policy object.
    session, scene, world, resolution, _view = _social(TURN_1)
    messages = _messages_for(resolution, session, scene, world, TURN_1)
    _blob, _system, _users, payload = _split(messages)
    policy = payload.get("response_policy") if isinstance(payload, dict) else {}
    retry = build_retry_prompt_for_failure(
        {"failure_class": "unresolved_question", "reasons": ["first_sentence_not_explicit_answer"]},
        response_policy=policy if isinstance(policy, dict) else {},
        gm_output={"player_facing_text": "The rain keeps falling."},
        player_text=TURN_1,
    )
    retry_bytes = len(retry.encode("utf-8"))
    pref["hypothetical_retry_instruction_bytes"] = retry_bytes
    pref["hypothetical_retry_estimated_tokens"] = (len(retry) + 3) // 4
    pref["hypothetical_retry_sha256"] = _sha(retry)

    after = _mtimes()
    summary = {
        "tokenizer": "tiktoken not installed; estimates are ceil(chars/4)",
        "live_provider_calls": 0,
        "production_mtime_unchanged": before == after,
        "mtimes_before": before,
        "mtimes_after": after,
        "system_prompt_bytes": len(gm.SYSTEM_PROMPT.encode("utf-8")),
        "narration_only_system_prompt_bytes": len(gm.NARRATION_ONLY_SYSTEM_PROMPT.encode("utf-8")),
        "cases": cases,
    }
    (OUT / "_inventory.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "production_mtime_unchanged": before == after,
        "cases": [
            {
                "label": row["label"],
                "bytes": row["serialized_bytes"],
                "est_tokens": row["estimated_tokens_ceil_chars_div_4"],
                "sha256": row["sha256"][:16],
                "envelope": row["envelope"],
                "projection": row["projection_selected"],
                "kind": row["resolution_kind"],
                "resolver": row["selected_resolver"],
                "reply": row["reply_plan_kind"],
                "op": row["contract_operation"],
                "skill": row["skill_check_present"],
                "messages": row["message_count"],
                "system": row["system_bytes"],
                "policy": row["response_policy_bytes"],
                "instructions": row["instructions_bytes"],
                "history": row["recent_history_bytes"],
                "hidden_leaks": row["hidden_fact_sha12_present"],
                "limitation": row["limitation"],
                "top3": [(item["section"], item["bytes"], item["pct_of_request"]) for item in row["top_sections"][:3]],
            }
            for row in cases
        ],
        "retry_bytes": pref.get("hypothetical_retry_instruction_bytes"),
    }, indent=2))


if __name__ == "__main__":
    main()
