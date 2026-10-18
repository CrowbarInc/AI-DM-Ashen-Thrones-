"""Candidate B: hand-authored plans validated, then executed by existing resolvers."""
from __future__ import annotations

from typing import Any

from game.live_resolution import obligation_preserving_fallback_line
from game.scene_referent_catalog import build_canonical_referent_catalog

from experiments.pr_dg.resolve import execute_authorized, select_contract, serialized_bytes
from experiments.pr_dg.state import Bundle, apply_shared_tick, hidden_hits, state_tuple

OPERATIONS = {"perceive", "inspect", "ask", "repeat", "confirm", "follow", "act", "advance_time"}
RESOLVERS = {"social", "exploration", "combat", "travel", "adjudication", "none"}
EXPECTS = {"none", "scene", "world", "combat", "clock", "interaction"}
ROLES = {"target", "addressee", "destination", "speaker"}
FORBIDDEN = {
    "rolled_total",
    "rolled_totals",
    "roll",
    "hit_points",
    "hp",
    "clue_ids",
    "clue_id",
    "hidden_facts",
    "hidden_fact",
    "gm_only_hidden_facts",
    "world_flags",
    "world_flag",
    "narration",
    "narration_prose",
    "damage",
    "set_hp",
    "commitment_status",
    "world_updates",
    "remove_entity",
}


def _drop_forbidden(value: Any, found: list[str]) -> Any:
    if isinstance(value, dict):
        kept = {}
        for key, item in value.items():
            if key in FORBIDDEN:
                found.append(key)
                continue
            kept[key] = _drop_forbidden(item, found)
        return kept
    if isinstance(value, list):
        return [_drop_forbidden(item, found) for item in value]
    return value


def _cycle(steps: list[dict]) -> bool:
    graph = {str(step.get("step_id") or ""): [str(item) for item in (step.get("depends_on") or [])] for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> bool:
        if node not in graph:
            return False
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph[node]:
            if walk(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(walk(node) for node in graph)


def _order(steps: list[dict]) -> list[dict]:
    pending = {str(step.get("step_id") or ""): step for step in steps}
    done: list[dict] = []
    while pending:
        ready = [
            step
            for step_id, step in pending.items()
            if all(dep not in pending for dep in (step.get("depends_on") or []))
        ]
        if not ready:
            break
        ready.sort(key=lambda step: str(step.get("step_id")))
        chosen = ready[0]
        done.append(chosen)
        del pending[str(chosen.get("step_id"))]
    return done


def validate_plan(bundle: Bundle, plan: dict) -> dict[str, Any]:
    found: list[str] = []
    forbidden_steps: list[str] = []
    raw_actions = plan.get("actions") if isinstance(plan.get("actions"), list) else []
    for step in raw_actions:
        if isinstance(step, dict) and any(key in step for key in FORBIDDEN):
            forbidden_steps.append(str(step.get("step_id") or ""))
            found.extend(key for key in step if key in FORBIDDEN)
    cleaned = _drop_forbidden(plan, [])
    errors: list[str] = []
    if not isinstance(cleaned, dict):
        return {"ok": False, "errors": ["plan_not_object"], "plan": {}, "dropped_fields": found}
    if cleaned.get("authority") != "non_authoritative_proposal":
        errors.append("authority")
    actions = cleaned.get("actions")
    if not isinstance(actions, list):
        errors.append("actions")
        actions = []
    if len(actions) > 4:
        errors.append("step_cap")
    for step in actions:
        if not isinstance(step, dict):
            errors.append("step_not_object")
            continue
        if step.get("operation") not in OPERATIONS:
            errors.append(f"operation:{step.get('operation')}")
        if step.get("proposed_resolver") not in RESOLVERS:
            errors.append(f"resolver:{step.get('proposed_resolver')}")
        if step.get("expects_mutation") not in EXPECTS:
            errors.append(f"expects:{step.get('expects_mutation')}")
        if not str(step.get("step_id") or "").strip():
            errors.append("missing_step_id")
    if actions and _cycle([step for step in actions if isinstance(step, dict)]):
        errors.append("dependency_cycle")
    for ref in cleaned.get("referenced_entities") or []:
        if isinstance(ref, dict) and ref.get("role") not in ROLES:
            errors.append(f"role:{ref.get('role')}")
    catalog = build_canonical_referent_catalog(
        scene=bundle.scene,
        world=bundle.world,
        session=bundle.session,
        scene_id=str((bundle.scene.get("scene") or {}).get("id") or ""),
    )
    ids = {str(row.get("id") or "") for row in catalog}
    enemy_ids = {
        str(enemy.get("id") or "")
        for enemy in ((bundle.scene.get("scene") or {}).get("enemies") or [])
        if isinstance(enemy, dict) and enemy.get("id")
    }
    # The referent catalog does not list combat enemies. Those ids already exist
    # on the scene document resolve_attack reads. They are not invented here.
    ids.update(item for item in enemy_ids if item)
    cleared: list[str] = []
    for step in actions:
        if not isinstance(step, dict):
            continue
        proposed = step.get("target_id")
        if proposed and str(proposed) not in ids and step.get("operation") != "advance_time":
            cleared.append(str(proposed))
            step["target_id"] = None
    uncertainty = cleaned.get("uncertainty") if isinstance(cleaned.get("uncertainty"), dict) else {}
    ambiguous = bool(uncertainty.get("ambiguous"))
    if cleared and not ambiguous:
        ambiguous = True
        uncertainty = dict(uncertainty)
        uncertainty["ambiguous"] = True
        uncertainty.setdefault("clarification_question", "Which do you mean?")
        cleaned["uncertainty"] = uncertainty
    if found and not forbidden_steps:
        errors.append("forbidden_field")
    return {
        "ok": not errors,
        "errors": errors,
        "plan": cleaned,
        "dropped_fields": found,
        "forbidden_steps": forbidden_steps,
        "cleared_ids": cleared,
        "ambiguous": ambiguous,
        "catalog_ids": sorted(item for item in ids if item),
        "enemy_ids_absent_from_referent_catalog": sorted(enemy_ids),
    }


def _step_text(plan: dict, step: dict) -> str:
    actions = plan.get("actions") or []
    raw = str(step.get("target_raw") or "").strip()
    if len(actions) > 1 and len(raw.split()) >= 3:
        return raw
    return str(plan.get("player_utterance") or raw)


def _query(bundle: Bundle, query: dict) -> dict[str, Any]:
    from experiments.pr_dg.candidate_c import dispatch_tool

    kind = str(query.get("kind") or "")
    args = query.get("args") if isinstance(query.get("args"), dict) else {}
    if kind == "visible_scene":
        return dispatch_tool(bundle, "inspect_visible_scene", {"scene_id": args.get("scene_id")}, turn_state={})
    if kind == "known_entity":
        return dispatch_tool(bundle, "query_known_entities", {"raw": args.get("raw") or "", "proposed_id": args.get("proposed_id")}, turn_state={})
    if kind == "npc_context":
        return dispatch_tool(bundle, "inspect_permitted_npc_context", {"npc_id": args.get("npc_id") or ""}, turn_state={})
    if kind == "clock":
        clocks = bundle.session.get("clocks") if isinstance(bundle.session.get("clocks"), dict) else {}
        return {"ok": True, "code": "ok", "mutation": "none", "result": {"time_pressure": clocks.get("time_pressure")}}
    if kind == "scheduled_event":
        events = [
            {"type": item.get("type"), "npc_id": item.get("npc_id")}
            for item in (bundle.world.get("event_log") or [])
            if isinstance(item, dict)
        ]
        return {"ok": True, "code": "ok", "mutation": "none", "result": {"events": events[-8:]}}
    return {"ok": False, "code": "unsupported", "mutation": "none", "result": {}}


def execute_plan(bundle: Bundle, plan: dict, *, tick: bool = True) -> dict[str, Any]:
    if tick:
        tick_result = apply_shared_tick(bundle)
    else:
        tick_result = {"code": "not_requested"}
    validation = validate_plan(bundle, plan)
    queries = []
    for query in (validation["plan"].get("world_queries") or [])[:1]:
        if isinstance(query, dict):
            queries.append(_query(bundle, query))
    if validation["ambiguous"] or not validation["ok"]:
        shell = {"metadata": {"resolution_contract": {"ambiguous": True, "operation": "ask"}}}
        try:
            line = obligation_preserving_fallback_line(shell)
        except Exception:
            line = "The reference cannot be identified clearly enough to resolve without clarification."
        question = ((validation["plan"].get("uncertainty") or {}).get("clarification_question") if validation["ambiguous"] else None)
        player_visible = question or line
        hits = hidden_hits(player_visible, bundle.hidden_strings)
        if hits:
            player_visible = "The reference cannot be identified clearly enough to resolve without clarification."
            hits = hidden_hits(player_visible, bundle.hidden_strings)
        return {
            "validation": validation,
            "tick": tick_result,
            "queries": queries,
            "steps": [],
            "executed": False,
            "status": "failed" if not validation["ok"] else "completed",
            "transaction": "rejected_before_execution",
            "player_visible": player_visible,
            "hidden_hits": hits,
            "authority_violations": ["hidden_in_player_visible"] if hits else [],
            "planner_context_bytes": serialized_bytes(
                {"plan": plan, "utterance": plan.get("player_utterance"), "catalog_ids": validation.get("catalog_ids")}
            ),
        }
    steps_out = []
    rejected: set[str] = set(validation.get("forbidden_steps") or [])
    committed = 0
    for step in _order(validation["plan"].get("actions") or []):
        step_id = str(step.get("step_id") or "")
        deps = [str(item) for item in (step.get("depends_on") or [])]
        if step_id in set(validation.get("forbidden_steps") or []):
            rejected.add(step_id)
            steps_out.append({"step_id": step_id, "status": "rejected", "code": "forbidden_field"})
            continue
        if any(dep in rejected for dep in deps):
            rejected.add(step_id)
            steps_out.append({"step_id": step_id, "status": "rejected", "code": "invalid_dependency"})
            continue
        if step.get("operation") == "advance_time":
            second = apply_shared_tick(bundle)
            code = "already_applied" if second.get("code") == "already_applied" else "unexpected_second_tick"
            if code != "already_applied":
                rejected.add(step_id)
            steps_out.append({"step_id": step_id, "status": "acknowledged" if code == "already_applied" else "rejected", "code": code, "tick": second})
            continue
        if step.get("expects_mutation") == "combat" and step.get("operation") != "act":
            rejected.add(step_id)
            steps_out.append({"step_id": step_id, "status": "rejected", "code": "unauthorized_mutation"})
            continue
        text = _step_text(validation["plan"], step)
        selector = select_contract(bundle, text)
        proposed = step.get("proposed_resolver")
        disagreement = None
        if proposed and proposed != "none" and proposed != selector.get("resolver"):
            disagreement = {"proposed": proposed, "selector": selector.get("resolver")}
        if selector.get("resolver") in {None, "generation"}:
            rejected.add(step_id)
            steps_out.append(
                {
                    "step_id": step_id,
                    "status": "unsupported",
                    "code": "unsupported",
                    "selector": selector,
                    "disagreement": disagreement,
                }
            )
            continue
        outcome = execute_authorized(bundle, text, selector)
        if outcome.get("unsupported"):
            rejected.add(step_id)
            steps_out.append(
                {
                    "step_id": step_id,
                    "status": "unsupported",
                    "code": outcome.get("unsupported_reason") or "unsupported",
                    "selector": selector,
                    "disagreement": disagreement,
                    "operations": outcome.get("operations") or [],
                }
            )
            continue
        committed += 1
        steps_out.append(
            {
                "step_id": step_id,
                "status": "committed",
                "selector": selector,
                "disagreement": disagreement,
                "operations": outcome.get("operations") or [],
                "resolver": outcome.get("resolver"),
                "resolution": outcome.get("resolution"),
                "mutator": outcome.get("mutator"),
                "elapsed_ms": outcome.get("elapsed_ms"),
            }
        )
    if committed and rejected:
        transaction = "partially_committed"
        status = "partial"
    elif committed:
        transaction = "atomic_per_resolver_call"
        status = "completed"
    elif rejected:
        transaction = "rejected_before_execution" if committed == 0 and not any(
            step.get("status") == "committed" for step in steps_out
        ) else "partially_committed"
        status = "failed" if committed == 0 else "partial"
    else:
        transaction = "atomic_per_resolver_call"
        status = "completed"
    return {
        "validation": {key: validation[key] for key in ("ok", "errors", "dropped_fields", "cleared_ids", "ambiguous", "forbidden_steps")},
        "tick": tick_result,
        "queries": queries,
        "steps": steps_out,
        "executed": committed > 0,
        "status": status,
        "transaction": transaction,
        "player_visible": "",
        "hidden_hits": hidden_hits(steps_out, bundle.hidden_strings),
        "authority_violations": ["hidden_in_step_result"] if hidden_hits(steps_out, bundle.hidden_strings) else [],
        "planner_context_bytes": serialized_bytes(
            {"plan": plan, "utterance": plan.get("player_utterance"), "catalog_ids": validation.get("catalog_ids")}
        ),
        "state": state_tuple(bundle),
    }
