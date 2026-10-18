"""Candidate C: eight bounded tools. Hand-authored transcripts. No model agent."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from game.combat import player_can_act
from game.exploration import _get_skill_check_config
from game.narration_visibility import build_narration_visibility_contract
from game.scene_referent_catalog import build_canonical_referent_catalog

from experiments.pr_dg.candidate_b import FORBIDDEN, validate_plan
from experiments.pr_dg.resolve import execute_authorized, select_contract
from experiments.pr_dg.state import Bundle, apply_shared_tick, hidden_hits, state_hash, state_tuple

READ_ONLY = {
    "inspect_visible_scene",
    "query_known_entities",
    "inspect_permitted_npc_context",
    "request_rules_adjudication",
    "propose_action",
    "inspect_resulting_state",
}
STATE_CHANGING = {"request_action_execution", "advance_authorized_time"}
ALLOWED_FIELDS = {"scene_id", "visible_facts", "known_clues", "combat_public", "clocks"}
MAX_ROUNDS = 4


def _envelope(tool: str, *, ok: bool, code: str, mutation: str, result: dict) -> dict[str, Any]:
    return {"ok": ok, "tool": tool, "authority": "engine", "mutation": mutation, "code": code, "result": result}


def _visible_entity_ids(bundle: Bundle) -> set[str]:
    contract = build_narration_visibility_contract(session=bundle.session, scene=bundle.scene, world=bundle.world)
    ids = set(contract.get("visible_entity_ids") or [])
    for row in _catalog(bundle):
        if row.get("id"):
            ids.add(str(row["id"]))
    return ids


def _catalog(bundle: Bundle) -> list[dict[str, Any]]:
    rows = build_canonical_referent_catalog(
        scene=bundle.scene,
        world=bundle.world,
        session=bundle.session,
        scene_id=str((bundle.scene.get("scene") or {}).get("id") or ""),
    )
    public = []
    for row in rows:
        public.append(
            {
                "id": row.get("id"),
                "type": row.get("type") or row.get("kind"),
                "label": row.get("label"),
                "aliases": list(row.get("aliases") or []),
                "presence": "active",
            }
        )
    return public


def _inspect_scene(bundle: Bundle, args: dict) -> dict[str, Any]:
    requested = args.get("scene_id")
    current = str((bundle.scene.get("scene") or {}).get("id") or bundle.session.get("active_scene_id") or "")
    if requested not in (None, "", current):
        return _envelope("inspect_visible_scene", ok=False, code="unknown_id", mutation="none", result={})
    body = bundle.scene.get("scene") if isinstance(bundle.scene.get("scene"), dict) else {}
    exits = []
    for exit_row in body.get("exits") or []:
        if isinstance(exit_row, dict):
            exits.append({"label": exit_row.get("label"), "target_scene_id": exit_row.get("target_scene_id")})
    entities = [{"id": row.get("id"), "label": row.get("label")} for row in _catalog(bundle)]
    result = {
        "scene_id": current,
        "location": body.get("location"),
        "visible_facts": list(body.get("visible_facts") or []),
        "entities": entities,
        "exits": exits,
    }
    return _envelope("inspect_visible_scene", ok=True, code="ok", mutation="none", result=result)


def _query_entities(bundle: Bundle, args: dict) -> dict[str, Any]:
    raw = str(args.get("raw") or "").strip()
    proposed = str(args.get("proposed_id") or "").strip()
    if not raw and not proposed:
        return _envelope("query_known_entities", ok=False, code="permission", mutation="none", result={})
    rows = _catalog(bundle)
    if proposed:
        matched = [row for row in rows if str(row.get("id") or "") == proposed]
    else:
        needle = raw.lower()
        matched = [
            row
            for row in rows
            if needle in str(row.get("label") or "").lower()
            or needle in str(row.get("id") or "").lower()
            or any(needle in str(alias).lower() for alias in (row.get("aliases") or []))
        ]
    if len(matched) > 1:
        return _envelope("query_known_entities", ok=True, code="ambiguous", mutation="none", result={"rows": matched})
    return _envelope("query_known_entities", ok=True, code="ok", mutation="none", result={"rows": matched})


def _npc_context(bundle: Bundle, args: dict) -> dict[str, Any]:
    npc_id = str(args.get("npc_id") or "").strip()
    visible = _visible_entity_ids(bundle)
    ctx = bundle.session.get("interaction_context") if isinstance(bundle.session.get("interaction_context"), dict) else {}
    interlocutor = str(ctx.get("active_interaction_target_id") or "")
    if npc_id not in visible and npc_id != interlocutor:
        return _envelope("inspect_permitted_npc_context", ok=False, code="not_visible", mutation="none", result={})
    npc = next((item for item in (bundle.world.get("npcs") or []) if isinstance(item, dict) and item.get("id") == npc_id), {})
    focus = bundle.session.get("discourse_focus") if isinstance(bundle.session.get("discourse_focus"), dict) else {}
    slot = focus.get("interlocutor") if isinstance(focus.get("interlocutor"), dict) else {}
    ledger = bundle.session.get("bounded_improvisation") if isinstance(bundle.session.get("bounded_improvisation"), dict) else {}
    claims = []
    allowed = {"rumor", "hearsay", "uncertain", "speculative", "opinion"}
    for entry in ledger.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") == "npc_claim" and str(entry.get("epistemic_status") or "") in allowed:
            claims.append({"id": entry.get("id"), "epistemic_status": entry.get("epistemic_status")})
    result = {
        "npc_id": npc_id,
        "name": npc.get("name") or npc_id,
        "presence": "active" if npc_id in visible else "interlocutor",
        "relationship": npc.get("disposition") if npc.get("disposition") in {"neutral", "friendly", "hostile"} else None,
        "discourse_focus": slot.get("id") == npc_id,
        "npc_claims": claims,
    }
    return _envelope("inspect_permitted_npc_context", ok=True, code="ok", mutation="none", result=result)


def _preview(bundle: Bundle, args: dict) -> dict[str, Any]:
    kind = str(args.get("kind") or "")
    if kind == "attack":
        try:
            can_act = bool(player_can_act(bundle.character, bundle.combat, bundle.conditions))
        except Exception:
            can_act = False
        enemies = (bundle.scene.get("scene") or {}).get("enemies") or []
        target = str(args.get("target_id") or "")
        present = any(isinstance(enemy, dict) and enemy.get("id") == target for enemy in enemies) if target else bool(enemies)
        return _envelope(
            "request_rules_adjudication",
            ok=True,
            code="ok",
            mutation="none",
            result={
                "combat_active": bool(bundle.combat.get("in_combat")),
                "player_can_act": can_act,
                "target_present": present,
                "would_require_roll": True,
                "check_prompt": None,
            },
        )
    if kind == "skill":
        body = bundle.scene.get("scene") if isinstance(bundle.scene.get("scene"), dict) else {}
        config = _get_skill_check_config(body, "investigate", str(args.get("raw") or "inv"))
        if not isinstance(config, dict):
            return _envelope("request_rules_adjudication", ok=False, code="unsupported", mutation="none", result={})
        return _envelope(
            "request_rules_adjudication",
            ok=True,
            code="ok",
            mutation="none",
            result={
                "requires_check": True,
                "skill_id": config.get("skill_id"),
                "combat_active": bool(bundle.combat.get("in_combat")),
                "dc_omitted": "scene configuration is not repeated; the tool does not guess a DC",
            },
        )
    return _envelope("request_rules_adjudication", ok=False, code="unsupported", mutation="none", result={})


def _step_from_args(args: dict) -> dict:
    step = args.get("step") if isinstance(args.get("step"), dict) else args
    return dict(step)


def _propose(bundle: Bundle, args: dict, turn_state: dict) -> dict[str, Any]:
    step = _step_from_args(args)
    plan = {
        "authority": "non_authoritative_proposal",
        "plan_id": "propose",
        "player_utterance": args.get("player_utterance") or step.get("target_raw") or "",
        "intent_summary": "",
        "referenced_entities": [],
        "uncertainty": {"ambiguous": False, "clarification_question": None, "unresolved_spans": []},
        "world_queries": [],
        "actions": [{key: value for key, value in step.items() if key != "depends_on"} | {"depends_on": []}],
    }
    scratch = bundle.clone()
    validation = validate_plan(scratch, plan)
    blocks = list(validation["errors"])
    if validation["ambiguous"]:
        blocks.append("ambiguous")
    selector = {}
    if not blocks:
        text = str(plan["player_utterance"] or "")
        selector = select_contract(scratch, text)
        if selector.get("resolver") in {None, "generation"}:
            blocks.append("unsupported")
    accepted = not blocks
    if accepted:
        turn_state.setdefault("proposed", set()).add(str(step.get("step_id") or ""))
    return _envelope(
        "propose_action",
        ok=accepted,
        code="ok" if accepted else (blocks[0] if blocks else "unsupported"),
        mutation="none",
        result={"accepted_shape": accepted, "resolver": selector.get("resolver"), "blocks": blocks},
    )


def _execute(bundle: Bundle, args: dict, turn_state: dict) -> dict[str, Any]:
    step = _step_from_args(args)
    if any(key in step or key in args for key in FORBIDDEN):
        return _envelope("request_action_execution", ok=False, code="permission", mutation="refused", result={})
    step_id = str(step.get("step_id") or "")
    if step_id and step_id in turn_state.setdefault("executed", set()):
        return _envelope("request_action_execution", ok=False, code="already_applied", mutation="refused", result={})
    proposed = turn_state.setdefault("proposed", set())
    if step_id and step_id not in proposed:
        proposal = _propose(bundle, {"step": step, "player_utterance": args.get("player_utterance") or step.get("target_raw")}, turn_state)
        if proposal["result"].get("blocks"):
            blocks = proposal["result"]["blocks"]
            code = "unsupported" if "unsupported" in blocks else "permission"
            return _envelope(
                "request_action_execution",
                ok=False,
                code=code,
                mutation="refused",
                result={"blocks": blocks},
            )
    before = state_tuple(bundle)
    text = str(args.get("player_utterance") or step.get("target_raw") or "")
    selector = select_contract(bundle, text)
    if selector.get("resolver") in {None, "generation"}:
        return _envelope("request_action_execution", ok=False, code="unsupported", mutation="refused", result={"resolver": selector.get("resolver")})
    outcome = execute_authorized(bundle, text, selector)
    if outcome.get("unsupported"):
        return _envelope(
            "request_action_execution",
            ok=False,
            code="unsupported",
            mutation="refused",
            result={"reason": outcome.get("unsupported_reason"), "resolver": selector.get("resolver")},
        )
    after = state_tuple(bundle)
    if step_id:
        turn_state["executed"].add(step_id)
    changed = [key for key in ("scene_id", "known_clue_ids", "enemy_hp", "interlocutor_id") if before.get(key) != after.get(key)]
    return _envelope(
        "request_action_execution",
        ok=True,
        code="ok",
        mutation="committed",
        result={
            "resolver": outcome.get("resolver"),
            "success": (outcome.get("resolution") or {}).get("success"),
            "kind": outcome.get("kind"),
            "changed_fields": changed,
            "operations": outcome.get("operations") or [],
            "public": outcome.get("resolution") or {},
        },
    )


def _resulting(bundle: Bundle, args: dict) -> dict[str, Any]:
    fields = args.get("fields")
    if not isinstance(fields, list) or any(field not in ALLOWED_FIELDS for field in fields):
        return _envelope("inspect_resulting_state", ok=False, code="permission", mutation="none", result={})
    tuple_ = state_tuple(bundle)
    result: dict[str, Any] = {}
    if "scene_id" in fields:
        result["scene_id"] = tuple_["scene_id"]
    if "visible_facts" in fields:
        result["visible_facts"] = tuple_["visible_facts"]
    if "known_clues" in fields:
        result["known_clues"] = {"ids": tuple_["known_clue_ids"], "texts": tuple_["known_clue_texts"]}
    if "combat_public" in fields:
        result["combat_public"] = {"in_combat": tuple_["in_combat"], "enemy_hp": tuple_["enemy_hp"]}
    if "clocks" in fields:
        result["clocks"] = {"time_pressure": tuple_["time_pressure"], "tick_event_types": tuple_["tick_event_types"]}
    return _envelope("inspect_resulting_state", ok=True, code="ok", mutation="none", result=result)


def _advance(bundle: Bundle, args: dict) -> dict[str, Any]:
    clock = args.get("clock")
    delta = args.get("delta")
    if clock != "time_pressure" or delta != 1 or args.get("world_tick") is not True:
        return _envelope("advance_authorized_time", ok=False, code="unsupported", mutation="refused", result={})
    if str(args.get("activity") or "") in {"downtime", "long_rest", "short_rest"}:
        return _envelope("advance_authorized_time", ok=False, code="unsupported", mutation="refused", result={"reason": "downtime_engine_not_wired"})
    tick = apply_shared_tick(bundle)
    if tick.get("code") == "already_applied":
        return _envelope("advance_authorized_time", ok=False, code="already_applied", mutation="refused", result=tick)
    return _envelope("advance_authorized_time", ok=True, code="ok", mutation="committed", result=tick)


def dispatch_tool(bundle: Bundle, tool: str, args: dict, *, turn_state: dict) -> dict[str, Any]:
    args = dict(args or {})
    before_hash = state_hash(bundle)
    before = bundle.clone()
    if tool == "inspect_visible_scene":
        result = _inspect_scene(bundle, args)
    elif tool == "query_known_entities":
        result = _query_entities(bundle, args)
    elif tool == "inspect_permitted_npc_context":
        result = _npc_context(bundle, args)
    elif tool == "request_rules_adjudication":
        result = _preview(bundle, args)
    elif tool == "propose_action":
        result = _propose(bundle, args, turn_state)
    elif tool == "inspect_resulting_state":
        result = _resulting(bundle, args)
    elif tool == "request_action_execution":
        return _guard_hidden(_execute(bundle, args, turn_state), bundle)
    elif tool == "advance_authorized_time":
        return _guard_hidden(_advance(bundle, args), bundle)
    else:
        result = _envelope(tool or "unknown", ok=False, code="unsupported", mutation="none", result={})
    if tool in READ_ONLY and state_hash(bundle) != before_hash:
        bundle.session = before.session
        bundle.world = before.world
        bundle.scene = before.scene
        bundle.combat = before.combat
        bundle.character = before.character
        result = _envelope(tool, ok=False, code="conflict", mutation="refused", result={"authority_violation": "read_only_tool_mutated_state"})
        result["authority_violation"] = "read_only_mutation"
    return _guard_hidden(result, bundle)


def _guard_hidden(result: dict, bundle: Bundle) -> dict:
    hits = hidden_hits(result, bundle.hidden_strings)
    if hits:
        result = _envelope(result.get("tool") or "tool", ok=False, code="permission", mutation="refused", result={})
        result["authority_violation"] = "hidden_leak_suppressed"
        result["hidden_hits"] = hits
    return result


def run_transcript(bundle: Bundle, transcript: list[dict], *, tick_first: bool = True) -> dict[str, Any]:
    if tick_first:
        tick = apply_shared_tick(bundle)
    else:
        tick = {"code": "deferred_to_tool"}
    turn_state: dict[str, Any] = {"proposed": set(), "executed": set(), "rounds": 0}
    results = []
    for call in transcript:
        if turn_state["rounds"] >= MAX_ROUNDS:
            results.append(_envelope(str(call.get("tool") or ""), ok=False, code="budget", mutation="refused", result={}))
            continue
        turn_state["rounds"] += 1
        tool = str(call.get("tool") or "")
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        results.append(dispatch_tool(bundle, tool, args, turn_state=turn_state))
    violations = [item.get("authority_violation") for item in results if item.get("authority_violation")]
    committed = [item for item in results if item.get("mutation") == "committed"]
    refused = [item for item in results if item.get("mutation") == "refused" or item.get("ok") is False]
    if violations:
        status = "failed"
        transaction = "unauthorized"
    elif committed and refused:
        transaction = "partially_committed"
        status = "partial"
    elif committed:
        transaction = "atomic_per_resolver_call"
        status = "completed"
    elif refused and not committed:
        transaction = "rejected_before_execution"
        status = "failed"
    else:
        transaction = "read_only"
        status = "completed"
    return {
        "tick": tick,
        "results": results,
        "rounds": turn_state["rounds"],
        "status": status,
        "transaction": transaction,
        "authority_violations": violations,
        "hidden_hits": hidden_hits(results, bundle.hidden_strings),
        "tool_context_bytes": len(
            __import__("json").dumps({"transcript": transcript, "results": _jsonable(results)}, ensure_ascii=False, default=str).encode("utf-8")
        ),
        "state": state_tuple(bundle),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
