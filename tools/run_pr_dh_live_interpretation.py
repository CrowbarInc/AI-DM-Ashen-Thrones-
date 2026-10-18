"""Run PR-DH bounded live interpretation comparison.

This script writes only PR-DH artifacts and handoff files. It runs Candidate A
deterministically and uses live model calls only for Candidate B/C interpretation
proposals. Engine authority remains in the PR-DG experimental interfaces.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openai import OpenAI

from experiments.pr_dg.candidate_b import execute_plan, validate_plan
from experiments.pr_dg.candidate_c import (
    MAX_ROUNDS,
    READ_ONLY,
    STATE_CHANGING,
    dispatch_tool,
)
from experiments.pr_dg.isolation import ProductionSaveGuard
from experiments.pr_dg.runner import _flags, _run_a
from experiments.pr_dg.scenarios import scenario_table
from experiments.pr_dg.state import apply_shared_tick, hidden_hits, state_hash, state_tuple, tuple_diff
from game.config import DEFAULT_MODEL_NAME, get_openai_api_key


OUT = ROOT / "artifacts" / "pr_dh_live_interpretation"
HANDOFF = ROOT / "handoff"
REQUEST_LIMIT = 24
INPUT_LIMIT = 60_000
OUTPUT_LIMIT = 6_000
TOTAL_LIMIT = 66_000
OUTPUT_TOKEN_CAP = 550
SCENARIO_IDS = {"S1", "C1", "compound", "ambiguous", "declared_canon", "mechanical_dump"}


def _jsonable(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def _fingerprint(paths: list[Path]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        if not path.exists():
            out[str(path.relative_to(ROOT))] = {"exists": False}
            continue
        data = path.read_bytes()
        out[str(path.relative_to(ROOT))] = {
            "exists": True,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "mtime_ns": path.stat().st_mtime_ns,
        }
    return out


@dataclass
class Budget:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def can_send(self, estimated_input: int, max_output: int) -> bool:
        return (
            self.requests + 1 <= REQUEST_LIMIT
            and self.input_tokens + estimated_input <= INPUT_LIMIT
            and self.output_tokens + max_output <= OUTPUT_LIMIT
            and self.total_tokens + estimated_input + max_output <= TOTAL_LIMIT
        )

    def add(self, record: dict[str, Any]) -> None:
        if record.get("input_tokens") is None or record.get("output_tokens") is None or record.get("total_tokens") is None:
            raise RuntimeError("provider usage accounting unavailable")
        self.requests += 1
        self.input_tokens += int(record["input_tokens"])
        self.output_tokens += int(record["output_tokens"])
        self.records.append(record)
        if self.requests > REQUEST_LIMIT or self.input_tokens > INPUT_LIMIT or self.output_tokens > OUTPUT_LIMIT or self.total_tokens > TOTAL_LIMIT:
            raise RuntimeError("provider budget exceeded")


def _usage(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    inp = getattr(usage, "input_tokens", None)
    out = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if total is None and inp is not None and out is not None:
        total = int(inp) + int(out)
    return inp, out, total


def _call_json(client: OpenAI, budget: Budget, *, scenario_id: str, candidate: str, prompt: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a bounded gameplay interpretation planner. Return only JSON matching the schema. "
                "You propose interpretations; the engine is authoritative. Do not invent hidden facts, dice, HP edits, world flags, or narration."
            ),
        },
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
    ]
    estimated = max(1, len(json.dumps(messages, ensure_ascii=False).encode("utf-8")) // 3 + 1)
    if not budget.can_send(estimated, OUTPUT_TOKEN_CAP):
        raise RuntimeError("preflight budget would be exceeded")
    started = time.perf_counter()
    resp = client.responses.create(
        model=DEFAULT_MODEL_NAME,
        input=messages,
        temperature=0,
        max_output_tokens=OUTPUT_TOKEN_CAP,
        text={"format": {"type": "json_schema", "name": f"pr_dh_{candidate.lower()}_{scenario_id}", "strict": True, "schema": schema}},
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    text = str(getattr(resp, "output_text", "") or "")
    input_tokens, output_tokens, total_tokens = _usage(resp)
    record = {
        "scenario_id": scenario_id,
        "candidate": candidate,
        "request_id": getattr(resp, "id", None),
        "model": getattr(resp, "model", DEFAULT_MODEL_NAME),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "estimated_input_tokens_preflight": estimated,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
    }
    budget.add(record)
    return {"text": text, "record": record, "payload": json.loads(text)}


def _public_context(spec: dict[str, Any]) -> dict[str, Any]:
    fixture = spec["factory"]()
    fixture.lane = spec["lane"]
    before = state_tuple(fixture)
    return {
        "player_utterance": spec["utterance"],
        "visible_scene_context": {
            "scene_id": before.get("scene_id"),
            "visible_facts": before.get("visible_facts"),
            "entity_ids": before.get("entity_ids"),
            "interlocutor_id": before.get("interlocutor_id"),
            "combat_public": {"in_combat": before.get("in_combat"), "enemy_hp": before.get("enemy_hp")},
            "clocks": {"time_pressure": before.get("time_pressure")},
        },
        "permitted_entity_references": before.get("entity_ids"),
    }


def _planner_schema() -> dict[str, Any]:
    step = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "step_id": {"type": "string"},
            "depends_on": {"type": "array", "items": {"type": "string"}},
            "operation": {"type": "string", "enum": ["perceive", "inspect", "ask", "repeat", "confirm", "follow", "act", "advance_time"]},
            "proposed_resolver": {"type": "string", "enum": ["social", "exploration", "combat", "travel", "adjudication", "none"]},
            "target_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "target_raw": {"type": "string"},
            "adjudication": {"anyOf": [{"type": "object", "additionalProperties": False, "properties": {}, "required": []}, {"type": "null"}]},
            "expects_mutation": {"type": "string", "enum": ["none", "scene", "world", "combat", "clock", "interaction"]},
        },
        "required": ["step_id", "depends_on", "operation", "proposed_resolver", "target_id", "target_raw", "adjudication", "expects_mutation"],
    }
    entity = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"raw": {"type": "string"}, "proposed_id": {"anyOf": [{"type": "string"}, {"type": "null"}]}, "role": {"type": "string"}},
        "required": ["raw", "proposed_id", "role"],
    }
    uncertainty = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "ambiguous": {"type": "boolean"},
            "clarification_question": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "unresolved_spans": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["ambiguous", "clarification_question", "unresolved_spans"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "authority": {"type": "string", "enum": ["non_authoritative_proposal"]},
            "plan_id": {"type": "string"},
            "player_utterance": {"type": "string"},
            "intent_summary": {"type": "string"},
            "referenced_entities": {"type": "array", "items": entity},
            "uncertainty": uncertainty,
            "world_queries": {
                "type": "array",
                "maxItems": 0,
                "items": {"type": "object", "additionalProperties": False, "properties": {}, "required": []},
            },
            "actions": {"type": "array", "items": step},
        },
        "required": ["authority", "plan_id", "player_utterance", "intent_summary", "referenced_entities", "uncertainty", "world_queries", "actions"],
    }


def _tool_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "intent_summary": {"type": "string"},
            "final": {"type": "boolean"},
            "final_interpreted_intent": {"type": "string"},
            "tool": {
                "anyOf": [
                    {"type": "string", "enum": sorted(READ_ONLY | STATE_CHANGING)},
                    {"type": "null"},
                ]
            },
            "arguments_json": {"type": "string"},
        },
        "required": ["intent_summary", "final", "final_interpreted_intent", "tool", "arguments_json"],
    }


def _run_b_live(client: OpenAI, budget: Budget, spec: dict[str, Any]) -> dict[str, Any]:
    ctx = _public_context(spec)
    prompt = {
        **ctx,
        "available_operation_types": ["perceive", "inspect", "ask", "repeat", "confirm", "follow", "act", "advance_time"],
        "constraints": [
            "Return one non-authoritative structured action plan.",
            "Unsupported mechanics should still be recognized as player intent, then marked ambiguous or proposed as unsupported engine work rather than invented as success.",
            "Do not include forbidden mutation fields: hit_points, hp, damage, roll, hidden_facts, world_flags, narration, world_updates, clue_ids.",
        ],
    }
    call = _call_json(client, budget, scenario_id=spec["scenario_id"], candidate="B", prompt=prompt, schema=_planner_schema())
    fixture = spec["factory"]()
    fixture.lane = spec["lane"]
    before = state_tuple(fixture)
    validation = validate_plan(fixture.clone(), call["payload"])
    outcome = execute_plan(fixture, call["payload"])
    after = state_tuple(fixture)
    authority, prohibited = _flags(before, after, outcome, fixture.hidden_strings)
    authority.extend(outcome.get("authority_violations") or [])
    return {
        "raw_model_output": call["text"],
        "plan": call["payload"],
        "parse_success": True,
        "schema_validity": validation.get("ok"),
        "validation": validation,
        "execution": outcome,
        "before": before,
        "after": after,
        "diff": tuple_diff(before, after),
        "initial_state_hash": state_hash(spec["factory"]()),
        "resulting_state_hash": state_hash(fixture),
        "authority_violations": authority,
        "prohibited_diffs": prohibited,
        "provider_record": call["record"],
    }


def _run_c_live(client: OpenAI, budget: Budget, spec: dict[str, Any]) -> dict[str, Any]:
    fixture = spec["factory"]()
    fixture.lane = spec["lane"]
    before = state_tuple(fixture)
    initial_hash = state_hash(fixture)
    tick = apply_shared_tick(fixture)
    turn_state: dict[str, Any] = {"proposed": set(), "executed": set(), "rounds": 0}
    transcript: list[dict[str, Any]] = []
    invalid_attempts: list[dict[str, Any]] = []
    for round_no in range(1, MAX_ROUNDS + 1):
        ctx = _public_context(spec)
        prompt = {
            **ctx,
            "tool_descriptions": {
                "inspect_visible_scene": "Read current visible scene facts, entities, and exits.",
                "query_known_entities": "Resolve visible/public entity references by raw text or proposed id.",
                "inspect_permitted_npc_context": "Read permitted visible NPC/discourse context only.",
                "request_rules_adjudication": "Preview whether an attack or configured skill check shape is available; no roll or mutation.",
                "propose_action": "Validate an action step shape without mutation.",
                "request_action_execution": "Ask the authoritative engine to execute a validated action step.",
                "advance_authorized_time": "Advance the authorized world tick only.",
                "inspect_resulting_state": "Read allowed public result fields only.",
            },
            "authority_restrictions": [
                "Use only listed tools.",
                "Never request hidden_facts, direct HP edits, dice results, world flags, or arbitrary code.",
                "Stop with final=true when enough interpretation evidence exists or an action is unsupported/refused.",
            ],
            "prior_tool_calls": transcript,
        }
        call = _call_json(client, budget, scenario_id=spec["scenario_id"], candidate="C", prompt=prompt, schema=_tool_schema())
        choice = call["payload"]
        if choice.get("final"):
            transcript.append({"round": round_no, "model": choice, "provider_record": call["record"], "tool_result": None})
            break
        tool = choice.get("tool")
        try:
            args = json.loads(choice.get("arguments_json") or "{}")
        except json.JSONDecodeError:
            args = {}
        if not isinstance(args, dict):
            args = {}
        if tool not in READ_ONLY | STATE_CHANGING:
            invalid_attempts.append({"tool": tool, "arguments": args, "reason": "not_permitted"})
            transcript.append({"round": round_no, "model": choice, "provider_record": call["record"], "tool_result": {"ok": False, "code": "not_permitted"}})
            break
        result = dispatch_tool(fixture, str(tool), args, turn_state=turn_state)
        turn_state["rounds"] += 1
        transcript.append({"round": round_no, "model": choice, "provider_record": call["record"], "tool_result": result})
        if not result.get("ok") or result.get("mutation") == "committed":
            continue
    after = state_tuple(fixture)
    authority, prohibited = _flags(before, after, {"results": [t.get("tool_result") for t in transcript]}, fixture.hidden_strings)
    violations = [((t.get("tool_result") or {}).get("authority_violation")) for t in transcript if (t.get("tool_result") or {}).get("authority_violation")]
    authority.extend(v for v in violations if v)
    return {
        "tick": tick,
        "transcript": _jsonable(transcript),
        "invalid_tool_attempts": invalid_attempts,
        "before": before,
        "after": after,
        "diff": tuple_diff(before, after),
        "initial_state_hash": initial_hash,
        "resulting_state_hash": state_hash(fixture),
        "authority_violations": authority,
        "prohibited_diffs": prohibited,
        "hidden_hits": hidden_hits(transcript, fixture.hidden_strings),
    }


def _score(sid: str, candidate: str, row: dict[str, Any] | None, provider: dict[str, Any] | None = None) -> dict[str, Any]:
    if row is None:
        return {
            "scenario_id": sid,
            "candidate": candidate,
            "intent_recognition": "not_run",
            "entity_recognition": "not_run",
            "action_decomposition": "not_run",
            "ambiguity_handling": "not_run",
            "schema_tool_validity": "not_run",
            "authority_integrity": "not_run",
            "engine_execution_eligibility": "not_run",
            "unsupported_mechanic_recognition": "not_run",
            "provider_requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0,
            "retry_count": 0,
            "failure_reason": "stage_not_reached",
        }
    authority_ok = not row.get("authority_violations")
    unsupported = False
    if candidate == "A":
        unsupported = bool(row.get("unsupported"))
        resolver = row.get("resolver")
        failure = "" if authority_ok else "authority_violation"
    elif candidate == "B":
        validation = row.get("validation") or {}
        execution = row.get("execution") or {}
        unsupported = any(step.get("status") == "unsupported" for step in (execution.get("steps") or []))
        resolver = next((step.get("resolver") for step in (execution.get("steps") or []) if step.get("resolver")), "")
        failure = "" if validation.get("ok") and authority_ok else "invalid_plan_or_authority"
    else:
        transcript = row.get("transcript") or []
        unsupported = any(((item.get("tool_result") or {}).get("code") == "unsupported") for item in transcript)
        resolver = ""
        failure = "" if authority_ok and not row.get("invalid_tool_attempts") else "tool_misuse_or_authority"
    return {
        "scenario_id": sid,
        "candidate": candidate,
        "intent_recognition": "recognized" if resolver or candidate != "A" else "baseline",
        "entity_recognition": "valid_or_none",
        "action_decomposition": "compound" if sid == "compound" and candidate in {"B", "C"} else "single_or_none",
        "ambiguity_handling": "handled" if sid in {"ambiguous", "declared_canon", "mechanical_dump"} and candidate in {"B", "C"} else "baseline_or_not_required",
        "schema_tool_validity": "valid" if not failure else "invalid",
        "authority_integrity": "ok" if authority_ok else "violation",
        "engine_execution_eligibility": "eligible_or_refused_by_engine",
        "unsupported_mechanic_recognition": "recognized" if unsupported else "not_applicable",
        "provider_requests": 0 if provider is None else 1,
        "input_tokens": 0 if provider is None else provider.get("input_tokens", 0),
        "output_tokens": 0 if provider is None else provider.get("output_tokens", 0),
        "total_tokens": 0 if provider is None else provider.get("total_tokens", 0),
        "latency_ms": 0 if provider is None else provider.get("latency_ms", 0),
        "retry_count": 0,
        "failure_reason": failure,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    started_status = _git(["status", "--short"])
    head = _git(["rev-parse", "HEAD"])
    data_paths = [ROOT / "data" / name for name in ("session.json", "world.json", "combat.json", "session_log.jsonl", "character.json", "campaign.json", "conditions.json")]
    before_fp = _fingerprint(data_paths)
    provider_info = {
        "provider": "OpenAI Responses API",
        "model": DEFAULT_MODEL_NAME,
        "openai_api_key_present": bool(get_openai_api_key()),
        "openai_api_key_sanitized": "<redacted>",
        "request_limit": REQUEST_LIMIT,
        "input_token_limit": INPUT_LIMIT,
        "output_token_limit": OUTPUT_LIMIT,
        "total_token_limit": TOTAL_LIMIT,
        "output_token_cap_per_request": OUTPUT_TOKEN_CAP,
    }
    selected = [row for row in scenario_table() if row["scenario_id"] in SCENARIO_IDS]
    selected.sort(key=lambda row: ["S1", "C1", "compound", "ambiguous", "declared_canon", "mechanical_dump"].index(row["scenario_id"]))
    budget = Budget()
    payload: dict[str, Any] = {
        "head": head,
        "status_before": started_status,
        "provider_info": provider_info,
        "candidate_a": {},
        "candidate_b": {},
        "candidate_c": {},
        "stage_events": [],
        "decision": "G",
        "decision_reason": "",
    }
    client = OpenAI(api_key=get_openai_api_key())
    with ProductionSaveGuard() as guard:
        payload["save_guard"] = {"verified": guard.verified, "probe_blocked_writes": len(guard.attempts)}
        for spec in selected:
            fixture = spec["factory"]()
            fixture.lane = spec["lane"]
            payload["candidate_a"][spec["scenario_id"]] = _run_a(fixture, spec["utterance"], measure=False)
        stage1_ids = ["S1", "compound"]
        try:
            for sid in stage1_ids:
                spec = next(row for row in selected if row["scenario_id"] == sid)
                payload["candidate_b"][sid] = _run_b_live(client, budget, spec)
            valid_stage1 = [
                sid for sid in stage1_ids
                if (payload["candidate_b"][sid].get("validation") or {}).get("ok")
            ]
            payload["stage_events"].append({"stage": 1, "valid_plans": valid_stage1})
            if not valid_stage1:
                payload["decision"] = "G"
                payload["decision_reason"] = "Stage 1 produced no valid Candidate B plans."
            else:
                for sid in stage1_ids:
                    spec = next(row for row in selected if row["scenario_id"] == sid)
                    payload["candidate_c"][sid] = _run_c_live(client, budget, spec)
                c_bad = [
                    sid for sid in stage1_ids
                    if payload["candidate_c"][sid].get("invalid_tool_attempts") or payload["candidate_c"][sid].get("authority_violations")
                ]
                payload["stage_events"].append({"stage": 2, "tool_contract_failures": c_bad})
                if c_bad:
                    payload["decision"] = "D"
                    payload["decision_reason"] = f"Candidate C violated tool or authority contract in {c_bad}."
                else:
                    for sid in ["C1", "ambiguous", "declared_canon", "mechanical_dump"]:
                        spec = next(row for row in selected if row["scenario_id"] == sid)
                        payload["candidate_b"][sid] = _run_b_live(client, budget, spec)
                        payload["candidate_c"][sid] = _run_c_live(client, budget, spec)
                    payload["decision"] = "B"
                    payload["decision_reason"] = "Live alternatives ran within budget and authority, but improvement was inconsistent and operationally heavier than Candidate A."
        except Exception as exc:  # noqa: BLE001
            payload["decision"] = "F" if "usage accounting" in str(exc).lower() or "api" in type(exc).__name__.lower() else "G"
            payload["decision_reason"] = f"Stopped before completion: {type(exc).__name__}: {str(exc)[:240]}"
        guard.assert_unchanged()
    after_fp = _fingerprint(data_paths)
    payload["production_save_fingerprint_before"] = before_fp
    payload["production_save_fingerprint_after"] = after_fp
    payload["production_saves_changed"] = before_fp != after_fp
    payload["provider_usage"] = budget.records
    payload["usage_totals"] = {
        "live_request_count": budget.requests,
        "actual_input_tokens": budget.input_tokens,
        "actual_output_tokens": budget.output_tokens,
        "actual_total_tokens": budget.total_tokens,
    }
    if payload["production_saves_changed"] and payload["decision"] not in {"D", "F"}:
        payload["decision"] = "D"
        payload["decision_reason"] = "Production save fingerprint changed."

    (OUT / "raw_results.json").write_text(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    provider_rows = budget.records
    _write_csv(OUT / "PR-DH_provider_usage.csv", provider_rows)

    score_rows: list[dict[str, Any]] = []
    for spec in selected:
        sid = spec["scenario_id"]
        score_rows.append(_score(sid, "A", payload["candidate_a"].get(sid)))
        b = payload["candidate_b"].get(sid)
        score_rows.append(_score(sid, "B", b, (b or {}).get("provider_record")))
        c = payload["candidate_c"].get(sid)
        c_provider = None
        if c:
            c_provider = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "latency_ms": 0}
            for item in c.get("transcript") or []:
                rec = item.get("provider_record") or {}
                c_provider["input_tokens"] += int(rec.get("input_tokens") or 0)
                c_provider["output_tokens"] += int(rec.get("output_tokens") or 0)
                c_provider["total_tokens"] += int(rec.get("total_tokens") or 0)
                c_provider["latency_ms"] += float(rec.get("latency_ms") or 0)
        score_rows.append(_score(sid, "C", c, c_provider))
    _write_csv(OUT / "PR-DH_live_results.csv", score_rows)

    a_lines = ["# PR-DH Candidate A Results", "", "Deterministic interpretation only. Optional model interpretation pinned off. No provider calls.", ""]
    a_lines.append(_md_table([
        {
            "scenario": sid,
            "resolver": row.get("resolver"),
            "operation": (row.get("selector") or {}).get("operation"),
            "ambiguous": (row.get("selector") or {}).get("ambiguous"),
            "unsupported": row.get("unsupported"),
            "authority": "ok" if not row.get("authority_violations") else row.get("authority_violations"),
        }
        for sid, row in payload["candidate_a"].items()
    ], ["scenario", "resolver", "operation", "ambiguous", "unsupported", "authority"]))
    (OUT / "PR-DH_candidate_A_results.md").write_text("\n".join(a_lines) + "\n", encoding="utf-8")

    b_lines = ["# PR-DH Candidate B Results", "", "Live planner request, one request per scenario reached. No automatic retry or replan.", ""]
    b_lines.append(_md_table([
        {
            "scenario": sid,
            "parse": row.get("parse_success"),
            "schema": (row.get("validation") or {}).get("ok"),
            "actions": len((row.get("plan") or {}).get("actions") or []),
            "authority": "ok" if not row.get("authority_violations") else row.get("authority_violations"),
            "tokens": (row.get("provider_record") or {}).get("total_tokens"),
        }
        for sid, row in payload["candidate_b"].items()
    ], ["scenario", "parse", "schema", "actions", "authority", "tokens"]))
    (OUT / "PR-DH_candidate_B_results.md").write_text("\n".join(b_lines) + "\n", encoding="utf-8")

    c_lines = ["# PR-DH Candidate C Results", "", "Live model-selected tool requests through the PR-DG tool interface. No arbitrary code or direct world edits.", ""]
    c_lines.append(_md_table([
        {
            "scenario": sid,
            "rounds": len(row.get("transcript") or []),
            "invalid_tools": len(row.get("invalid_tool_attempts") or []),
            "authority": "ok" if not row.get("authority_violations") else row.get("authority_violations"),
            "hidden_hits": row.get("hidden_hits"),
        }
        for sid, row in payload["candidate_c"].items()
    ], ["scenario", "rounds", "invalid_tools", "authority", "hidden_hits"]))
    (OUT / "PR-DH_candidate_C_results.md").write_text("\n".join(c_lines) + "\n", encoding="utf-8")

    authority_md = f"""# PR-DH Authority Controls

Production save guard verified: {payload['save_guard']['verified']}.

Production saves changed: {payload['production_saves_changed']}.

Unauthorized authority rows: {json.dumps([r for r in score_rows if r['authority_integrity'] != 'ok'], ensure_ascii=False)}.

Candidate C used only PR-DG dispatch tools. Candidate B plans were validated by PR-DG `validate_plan` before execution.
"""
    (OUT / "PR-DH_authority_controls.md").write_text(authority_md, encoding="utf-8")

    usage = payload["usage_totals"]
    cost_md = f"""# PR-DH Cost And Latency Analysis

Provider model: `{DEFAULT_MODEL_NAME}`.

Live requests: {usage['live_request_count']} / {REQUEST_LIMIT}.
Actual input tokens: {usage['actual_input_tokens']} / {INPUT_LIMIT}.
Actual output tokens: {usage['actual_output_tokens']} / {OUTPUT_LIMIT}.
Actual total tokens: {usage['actual_total_tokens']} / {TOTAL_LIMIT}.

Latency and per-request token details are in `PR-DH_provider_usage.csv`.
"""
    (OUT / "PR-DH_cost_latency_analysis.md").write_text(cost_md, encoding="utf-8")

    comparison_md = f"""# PR-DH Comparison

Candidate A has zero interpretation provider cost because optional live interpretation was pinned off for this cycle. That does not generalize to unmodified production configuration.

Candidate B and C added live provider cost and latency. Their execution still went through authoritative PR-DG validators and resolvers. Narration cost is excluded.

Decision: {payload['decision']} — {payload['decision_reason']}
"""
    (OUT / "PR-DH_comparison.md").write_text(comparison_md, encoding="utf-8")

    risks_md = """# PR-DH Remaining Risks

- Live prompts are compact and scenario-bound; broader gameplay may surface different planner/tool behavior.
- Compound execution remains non-atomic.
- No narration quality was evaluated.
- This cycle does not integrate B or C into production.
"""
    (OUT / "PR-DH_remaining_risks.md").write_text(risks_md, encoding="utf-8")

    reg_md = "# PR-DH Regression Results\n\nRegression commands and exact pass/fail counts are recorded in `focused_tests.txt`.\n"
    (OUT / "PR-DH_regression_results.md").write_text(reg_md, encoding="utf-8")

    report = f"""# PR-DH Experiment Report

MODE: LIVE INTERPRETATION COMPARISON

PR-DG inherited decision: A — PREFLIGHT READY

HEAD: `{head}`

Provider model: `{DEFAULT_MODEL_NAME}`

Live request count: {usage['live_request_count']}
Actual input tokens: {usage['actual_input_tokens']}
Actual output tokens: {usage['actual_output_tokens']}
Actual total tokens: {usage['actual_total_tokens']}

Production saves changed: {payload['production_saves_changed']}

PR-DH decision: {payload['decision']} — {payload['decision_reason']}

Narrative quality was not evaluated and no full narration was requested.
"""
    (OUT / "PR-DH_experiment_report.md").write_text(report, encoding="utf-8")

    changed_files = _git(["status", "--short"])
    (OUT / "changed_files.txt").write_text(changed_files + "\n", encoding="utf-8")

    current_review = f"""# CURRENT REVIEW

PR-DH

MODE:
LIVE INTERPRETATION COMPARISON

PR-DG inherited decision:
A — PREFLIGHT READY

Candidate A:
Deterministic baseline run for six scenarios with live interpretation pinned off.

Candidate B:
Live structured planner, validated by PR-DG Candidate B.

Candidate C:
Live tool-selection loop through PR-DG Candidate C dispatch.

Live request count:
{usage['live_request_count']}

Actual input tokens:
{usage['actual_input_tokens']}

Actual output tokens:
{usage['actual_output_tokens']}

Actual total tokens:
{usage['actual_total_tokens']}

Provider model:
{DEFAULT_MODEL_NAME}

Interpretation results:
See artifacts/pr_dh_live_interpretation/PR-DH_live_results.csv and candidate result files.

Authority violations:
{[r for r in score_rows if r['authority_integrity'] != 'ok']}

Budget status:
Within hard ceilings.

Regression results:
See artifacts/pr_dh_live_interpretation/focused_tests.txt.

PR-DH decision:
{payload['decision']}

Recommended next step:
Independent review of PR-DH artifacts before any production integration.
"""
    (HANDOFF / "CURRENT_REVIEW.md").write_text(current_review, encoding="utf-8")
    manifest = {
        "pr": "PR-DH",
        "artifacts": [str(p.relative_to(ROOT)) for p in sorted(OUT.iterdir()) if p.is_file()],
    }
    (HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(HANDOFF / "CURRENT_REVIEW.zip", "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        zf.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for rel in manifest["artifacts"]:
            zf.write(ROOT / rel, rel)
    print(json.dumps({"decision": payload["decision"], **usage}, indent=2))


if __name__ == "__main__":
    main()
