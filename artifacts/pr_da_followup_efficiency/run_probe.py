#!/usr/bin/env python3
"""PR-DA follow-up efficiency verification.

Artifact-only diagnostic. Does not modify application code or production saves.
Reconstructs the PR-CY post-Turn-1 session, preflights resolution with no
provider call, then allows at most one live gameplay turn.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EVIDENCE = OUT / "evidence"
PR_CY = ROOT / "artifacts" / "pr_cy_live_social_efficiency" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

MAX_REQUESTS = 2
MAX_TOKENS = 75_000
MAX_TURNS = 1
REQUIRED_RESPONSE_MODEL = "gpt-4.1-mini-2025-04-14"
ALLOWED_REQUEST_MODELS = {"gpt-4.1-mini", REQUIRED_RESPONSE_MODEL}
FOLLOWUP = "Does the rain make it harder to keep watch?"
TURN1_PLAYER = "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"
TURN1_ANSWER_MARK = "I suppose most would prefer dry ground"
PR_CY_FOLLOWUP_TOTAL = 72_065
PR_CY_RETRY_TOKENS = 39_593

_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
CALLS: list[dict[str, Any]] = []
HALT: str | None = None
ACCOUNTING_FAILED = False
CURRENT = {"turn": "preflight", "kind": "generation", "retry_attempt": 0, "retry_reason": None}
MODE = {"phase": "preflight"}
PROJECTOR_CAPTURES: list[dict[str, Any]] = []


class BudgetStop(BaseException):
    """Not an Exception, so provider fallback code cannot swallow it."""


class PreflightStop(BaseException):
    """Abort the provider call after the request has been captured."""


def redact(text: str) -> str:
    return _SECRET.sub("sk-REDACTED", text)


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(dump_json(value)) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(text), encoding="utf-8")


def status(text: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    with (EVIDENCE / "status.txt").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def git(args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args.split()], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception as exc:
        return f"git command failed: {exc}"


def production_mtimes() -> dict[str, int]:
    paths = [
        ROOT / "data" / "session.json",
        ROOT / "data" / "world.json",
        ROOT / "data" / "combat.json",
        ROOT / "data" / "session_log.jsonl",
        ROOT / "data" / "character.json",
        ROOT / "data" / "campaign.json",
        ROOT / "data" / "scenes" / "frontier_gate.json",
    ]
    return {str(path.relative_to(ROOT)): path.stat().st_mtime_ns for path in paths if path.exists()}


BEFORE_MTIMES = production_mtimes()

from fastapi.testclient import TestClient

import game.api as api
import game.gm as gm_module
import game.semantic_interpreter as interpreter
from game import storage
from game.config import (
    DEFAULT_MODEL_NAME,
    ENABLE_MODEL_ROUTING,
    HIGH_PRECISION_MODEL_NAME,
    MODEL_NAME,
    RETRY_ESCALATION_MODEL_NAME,
    get_openai_api_key,
)
from game.persistence_contract import wrap_runtime_payload


def spent_tokens() -> int:
    total = 0
    for call in CALLS:
        usage = call.get("usage") or {}
        if isinstance(usage.get("total_tokens"), int):
            total += usage["total_tokens"]
        else:
            total += int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
    return total


def budget_block_reason() -> str | None:
    if ACCOUNTING_FAILED:
        return "usage accounting unavailable"
    if len(CALLS) >= MAX_REQUESTS:
        return f"provider request budget reached ({MAX_REQUESTS})"
    if spent_tokens() >= MAX_TOKENS:
        return f"token budget reached ({spent_tokens()})"
    return None


def usage_from_response_dump(dump: dict[str, Any]) -> dict[str, Any]:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    details_in = usage.get("input_tokens_details") if isinstance(usage.get("input_tokens_details"), dict) else {}
    details_out = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_input_tokens": details_in.get("cached_tokens"),
        "input_tokens_details": details_in,
        "output_tokens_details": details_out,
    }


def narration_from_raw(raw: Any) -> str:
    text = str(raw or "")
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return text
    if isinstance(data, dict):
        for key in ("narration", "player_facing_text", "text"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key]
    return text


import openai.resources.responses as responses_module

Responses = responses_module.Responses
ORIGINAL_CREATE = Responses.create


def observe_create(self, *args, **kwargs):
    global ACCOUNTING_FAILED, HALT
    requested = str(kwargs.get("model") or "")
    turn = str(CURRENT.get("turn") or "unknown")
    attempt = int(CURRENT.get("retry_attempt") or 0) + 1
    kind = str(CURRENT.get("kind") or "generation")
    save_json(
        EVIDENCE / turn / f"provider_request_{kind}_{attempt}.json",
        {
            "phase": MODE["phase"],
            "model": kwargs.get("model"),
            "kind": kind,
            "retry_attempt": CURRENT.get("retry_attempt"),
            "retry_reason": CURRENT.get("retry_reason"),
            "create_kwarg_keys": sorted(key for key in kwargs if key != "input"),
            "provider_input": kwargs.get("input"),
        },
    )
    if MODE["phase"] == "preflight":
        raise PreflightStop("provider request captured; no network call")

    reason = budget_block_reason()
    if requested and requested not in ALLOWED_REQUEST_MODELS:
        reason = f"refusing model substitution: requested {requested}"
    if reason:
        HALT = reason
        raise BudgetStop(reason)

    started = time.perf_counter()
    row: dict[str, Any] = {
        "index": len(CALLS) + 1,
        "turn": turn,
        "kind": kind,
        "retry_attempt": CURRENT.get("retry_attempt") or 0,
        "retry_reason": CURRENT.get("retry_reason"),
        "model": kwargs.get("model"),
        "started": datetime.now(timezone.utc).isoformat(),
        "create_kwarg_keys": sorted(key for key in kwargs if key != "input"),
    }
    CALLS.append(row)
    try:
        result = ORIGINAL_CREATE(self, *args, **kwargs)
        response_dump = result.model_dump(mode="json")
        save_json(EVIDENCE / turn / f"provider_response_{kind}_{attempt}.json", response_dump)
        row["raw_output"] = getattr(result, "output_text", None)
        row["parsed_narration"] = narration_from_raw(row["raw_output"])
        row["response_id"] = response_dump.get("id")
        row["response_model"] = response_dump.get("model")
        row["usage"] = usage_from_response_dump(response_dump)
        row["status"] = response_dump.get("status")
        row["error"] = None
        if not row["usage"] or row["usage"].get("total_tokens") in (None, ""):
            ACCOUNTING_FAILED = True
            HALT = "usage accounting unavailable after provider response"
        elif str(row["response_model"] or "") != REQUIRED_RESPONSE_MODEL:
            HALT = f"response model {row['response_model']!r} is not {REQUIRED_RESPONSE_MODEL}"
        return result
    except BudgetStop:
        raise
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["usage"] = {}
        row["raw_output"] = None
        row["parsed_narration"] = ""
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save_json(EVIDENCE / "model_calls.json", CALLS)


Responses.create = observe_create


def wrap_provider(fn, kind: str):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(
            kind=kind,
            retry_attempt=kwargs.get("retry_attempt", 0),
            retry_reason=kwargs.get("retry_reason"),
        )
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)

    return observed


api.call_gpt = wrap_provider(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap_provider(interpreter._invoke_interpretation_model, "interpretation")

_REAL_PROJECTOR = gm_module._project_harmless_social_provider_context


def _capturing_projector(payload, *, provider_response_contract):
    PROJECTOR_CAPTURES.append(
        {
            "phase": MODE["phase"],
            "provider_response_contract": provider_response_contract,
            "payload": deepcopy(payload),
        }
    )
    return _REAL_PROJECTOR(payload, provider_response_contract=provider_response_contract)


gm_module._project_harmless_social_provider_context = _capturing_projector


def verify_config() -> dict[str, Any]:
    key = get_openai_api_key() or ""
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or ""
    models = {
        "MODEL_NAME": MODEL_NAME,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
    }
    unknown = sorted({value for value in models.values() if value not in ALLOWED_REQUEST_MODELS})
    report = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "provider": "OpenAI",
        "billing_path": "OpenAI Python SDK Responses API via client.responses.create.",
        "endpoint": "https://api.openai.com/v1/responses" if not base_url else "base_url_override",
        "base_url_override_present": bool(base_url),
        "models": models,
        "enable_model_routing": ENABLE_MODEL_ROUTING,
        "required_response_model": REQUIRED_RESPONSE_MODEL,
        "api_key_present": bool(key.startswith("sk-")),
        "api_key_length": len(key),
        "startup_preflight": "skipped by ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1; no billable preflight request used.",
        "live_interpretation": "disabled by ASHEN_DISABLE_LIVE_INTERPRETATION=1.",
        "hard_budget": {
            "max_completed_gameplay_turns": MAX_TURNS,
            "max_provider_requests": MAX_REQUESTS,
            "max_combined_tokens": MAX_TOKENS,
        },
        "unknown_models": unknown,
        "git_head": git("rev-parse HEAD"),
        "note": "Verification runs the dirty worktree, including untracked PR-CZ modules. HEAD alone does not contain the repair.",
    }
    save_json(EVIDENCE / "phase0_config.json", report)
    if unknown or base_url or not report["api_key_present"] or MODEL_NAME != "gpt-4.1-mini":
        raise SystemExit("STOP config")
    return report


def point_storage(base: Path) -> None:
    storage.BASE_DIR = base
    storage.DATA_DIR = base / "data"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    for attr, filename in {
        "WORLD_PATH": "world.json",
        "SESSION_PATH": "session.json",
        "CAMPAIGN_PATH": "campaign.json",
        "CHARACTER_PATH": "character.json",
        "COMBAT_PATH": "combat.json",
        "CONDITIONS_PATH": "conditions.json",
        "SESSION_LOG_PATH": "session_log.jsonl",
    }.items():
        setattr(storage, attr, storage.DATA_DIR / filename)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def snapshot() -> dict[str, Any]:
    session = storage.load_session()
    world = storage.load_world()
    sid = session.get("active_scene_id")
    scene_doc = storage.load_scene(sid) if sid else {}
    scene = scene_doc.get("scene") if isinstance(scene_doc, dict) else {}
    character = storage.load_character()
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    interlocutor = focus.get("active_interlocutor") if isinstance(focus.get("active_interlocutor"), dict) else {}
    return {
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": sid,
        "interaction_context": session.get("interaction_context"),
        "discourse_focus": session.get("discourse_focus"),
        "active_interlocutor_id": interlocutor.get("id"),
        "conversation_fields_empty": not (session.get("chat_history") or session.get("conversation_history")),
        "known_clues": session.get("known_clues") or session.get("clue_knowledge"),
        "scene_runtime": storage.get_scene_runtime(session, sid) if sid else {},
        "npc_runtime": session.get("npc_runtime") if isinstance(session.get("npc_runtime"), dict) else {},
        "scene": {
            "id": scene.get("id"),
            "location": scene.get("location"),
            "summary": scene.get("summary"),
            "mode": scene.get("mode"),
            "visible_facts": list(scene.get("visible_facts") or []),
            "hidden_facts": list(scene.get("hidden_facts") or []),
            "addressable_ids": [
                item.get("id") for item in (scene.get("addressables") or []) if isinstance(item, dict)
            ],
        },
        "world_npc_ids": [npc.get("id") for npc in (world.get("npcs") or []) if isinstance(npc, dict)],
        "character": {
            "name": character.get("name"),
            "hp": character.get("hp"),
            "inventory": character.get("inventory"),
            "spells": character.get("spells"),
            "conditions": character.get("conditions"),
        },
        "log_player_inputs": [
            entry.get("player_input") for entry in storage.load_log() if isinstance(entry, dict)
        ],
    }


def canonical(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


def reconstruct(isolated: Path) -> dict[str, Any]:
    """Restore the engine session returned immediately after PR-CY Turn 1."""
    if isolated.exists():
        shutil.rmtree(isolated)
    shutil.copytree(PR_CY / "isolated_session", isolated)
    point_storage(isolated)

    t1_api = json.loads((PR_CY / "T1" / "api_response.json").read_text(encoding="utf-8"))
    t1_after = json.loads((PR_CY / "T1" / "state_after.json").read_text(encoding="utf-8"))
    t2_before = json.loads((PR_CY / "T2" / "state_before.json").read_text(encoding="utf-8"))
    session = t1_api.get("session")
    if not isinstance(session, dict):
        raise SystemExit("STOP reconstruction: T1 API response has no session")

    saved_at = str(session.get("last_saved_at") or datetime.now(timezone.utc).isoformat())
    envelope = wrap_runtime_payload(
        kind="session",
        payload=session,
        saved_at=saved_at,
        include_integrity=True,
    )
    storage._save_json(storage.SESSION_PATH, envelope)

    log_lines = (PR_CY / "isolated_session" / "data" / "session_log.jsonl").read_text(encoding="utf-8").splitlines()
    if len(log_lines) < 2:
        raise SystemExit("STOP reconstruction: PR-CY log does not contain two turns")
    first = json.loads(log_lines[0])
    second = json.loads(log_lines[1])
    if first.get("player_input") != TURN1_PLAYER or TURN1_ANSWER_MARK not in str(
        (first.get("gm_output") or {}).get("player_facing_text") or ""
    ):
        raise SystemExit("STOP reconstruction: turn 1 log does not match the accepted answer")
    if second.get("player_input") != FOLLOWUP:
        raise SystemExit("STOP reconstruction: turn 2 log is not the rain follow-up")
    storage.SESSION_LOG_PATH.write_text(log_lines[0] + "\n", encoding="utf-8")

    def choose_document(label: str, api_value: Any, disk_path: Path) -> str:
        if not isinstance(api_value, dict) or not disk_path.exists():
            return "kept_isolated_copy"
        disk = json.loads(disk_path.read_text(encoding="utf-8"))
        if disk_path.name in {"session.json", "combat.json"} and isinstance(disk.get("payload"), dict):
            disk_payload = disk["payload"]
        else:
            disk_payload = disk
        if canonical(api_value) == canonical(disk_payload):
            return "isolated_copy_matches_t1_api"
        storage._save_json(disk_path, api_value)
        return "replaced_with_t1_api_document"

    document_choices = {
        "world": choose_document("world", t1_api.get("world"), storage.WORLD_PATH),
        "character": choose_document("character", t1_api.get("character"), storage.CHARACTER_PATH),
        "campaign": choose_document("campaign", t1_api.get("campaign"), storage.CAMPAIGN_PATH),
        "conditions": choose_document("conditions", t1_api.get("conditions"), storage.CONDITIONS_PATH),
        "combat": choose_document("combat", t1_api.get("combat"), storage.COMBAT_PATH),
    }
    # Combat from the API is an unwrapped payload. If we replaced the envelope
    # with a raw payload, rewrap so load_combat accepts it.
    if document_choices["combat"] == "replaced_with_t1_api_document":
        combat_payload = t1_api.get("combat")
        combat_saved = str((combat_payload or {}).get("last_saved_at") or saved_at) if isinstance(combat_payload, dict) else saved_at
        storage._save_json(
            storage.COMBAT_PATH,
            wrap_runtime_payload(
                kind="combat",
                payload=combat_payload if isinstance(combat_payload, dict) else {},
                saved_at=combat_saved,
                include_integrity=True,
            ),
        )

    loaded = snapshot()
    problems = []
    if loaded["turn_counter"] != 2:
        problems.append(f"turn_counter={loaded['turn_counter']}")
    if loaded["active_scene_id"] != "frontier_gate":
        problems.append(f"scene={loaded['active_scene_id']}")
    if loaded["active_interlocutor_id"] != "guard_captain":
        problems.append(f"interlocutor={loaded['active_interlocutor_id']}")
    interaction = loaded.get("interaction_context") or {}
    if interaction.get("active_interaction_target_id") != "guard_captain":
        problems.append(f"interaction_target={interaction.get('active_interaction_target_id')}")
    if loaded["log_player_inputs"] != [TURN1_PLAYER]:
        problems.append(f"log={loaded['log_player_inputs']}")
    if loaded["scene"]["hidden_facts"] != t1_after["scene"]["hidden_facts"]:
        problems.append("hidden_facts_differ_from_t1_state_after")
    if "guard_captain" not in loaded["scene"]["addressable_ids"]:
        problems.append("guard_captain_not_addressable")
    if "guard_captain" not in loaded["world_npc_ids"]:
        problems.append("guard_captain_missing_from_world")
    runtime = loaded.get("scene_runtime") or {}
    if runtime.get("last_player_action_text") != TURN1_PLAYER:
        problems.append("last_player_action_text_mismatch")
    focus_match = canonical(loaded.get("discourse_focus")) == canonical(t1_after.get("discourse_focus"))
    if not focus_match:
        problems.append("discourse_focus_differs_from_t1_state_after")
    if canonical(t1_after) != canonical(t2_before):
        problems.append("t1_state_after_differs_from_t2_state_before")

    report = {
        "method": (
            "Session payload is the session object returned by the PR-CY Turn 1 API response. "
            "The transcript is the first session_log line only. Documents that differ from the "
            "post-Turn-2 isolated copies are replaced with the Turn 1 API documents."
        ),
        "t1_state_after_matches_t2_state_before": canonical(t1_after) == canonical(t2_before),
        "document_choices": document_choices,
        "discourse_focus_matches_t1_snapshot": focus_match,
        "verification_problems": problems,
        "loaded_snapshot": loaded,
        "accepted_turn1_text": (first.get("gm_output") or {}).get("player_facing_text"),
        "turn2_log_excluded": True,
    }
    save_json(EVIDENCE / "reconstructed_state.json", report)
    if problems:
        raise SystemExit("STOP reconstruction: " + "; ".join(problems))
    return report


def _check(rows: list[dict[str, Any]], name: str, required: Any, actual: Any, source: str) -> bool:
    ok = actual == required if not isinstance(required, dict) or "predicate" not in required else bool(required["predicate"](actual))
    if isinstance(required, dict) and "predicate" in required:
        ok = bool(required["predicate"](actual))
        shown_required = required.get("label")
    else:
        shown_required = required
        ok = actual == required
    display_actual = actual
    if isinstance(actual, (dict, list)):
        display_actual = json.dumps(actual, ensure_ascii=False, default=str)[:500]
    rows.append(
        {
            "name": name,
            "required": shown_required,
            "actual": display_actual,
            "pass": bool(ok),
            "authority_source": source,
        }
    )
    return bool(ok)


def evaluate_predicates(payload: dict[str, Any], provider_response_contract: str) -> list[dict[str, Any]]:
    """Evaluate PR-CW projector predicates in source order. Do not change them."""
    rows: list[dict[str, Any]] = []
    if not _check(rows, "payload_is_dict", "dict", type(payload).__name__, "projector payload argument"):
        return rows
    if not _check(
        rows,
        "provider_response_contract",
        "narration_only",
        provider_response_contract,
        "build_messages selected envelope passed into the projector",
    ):
        return rows

    recipe = payload.get("decision_facing_answer_recipe")
    turn_operation = recipe.get("turn_operation") if isinstance(recipe, dict) else None
    decision = payload.get("gm_resolution_decision")
    contract = payload.get("resolution_contract")
    response_policy = payload.get("response_policy")
    speaker_selection = payload.get("speaker_selection")
    active_interlocutor = payload.get("active_interlocutor")
    dialogue_plan = payload.get("dialogue_social_plan")
    scene = payload.get("scene")
    permitted_inference = recipe.get("permitted_inference") if isinstance(recipe, dict) else None
    combat = payload.get("combat")
    mechanical = payload.get("mechanical_resolution")
    metadata = mechanical.get("metadata") if isinstance(mechanical, dict) else None
    social = mechanical.get("social") if isinstance(mechanical, dict) else None
    npc_id = str(active_interlocutor.get("npc_id") or "").strip() if isinstance(active_interlocutor, dict) else ""
    allowed = speaker_selection.get("allowed_speaker_ids") if isinstance(speaker_selection, dict) else None

    checks = [
        ("recipe_is_dict", True, isinstance(recipe, dict), "payload.decision_facing_answer_recipe"),
        ("turn_operation_is_dict", True, isinstance(turn_operation, dict), "payload.decision_facing_answer_recipe.turn_operation"),
        ("response_operation", "incidental_dialogue", (turn_operation or {}).get("response_operation") if isinstance(turn_operation, dict) else None, "turn_operation.response_operation"),
        ("declaration_expectation", "reply_not_required", (turn_operation or {}).get("declaration_expectation") if isinstance(turn_operation, dict) else None, "turn_operation.declaration_expectation"),
        ("decision_is_dict", True, isinstance(decision, dict), "payload.gm_resolution_decision"),
        ("permitted_state_mutations", [], (decision or {}).get("permitted_state_mutations") if isinstance(decision, dict) else None, "gm_resolution_decision.permitted_state_mutations"),
        ("unresolved_qualifiers", [], (decision or {}).get("unresolved_qualifiers") if isinstance(decision, dict) else None, "gm_resolution_decision.unresolved_qualifiers"),
        ("unresolved_content_absent", True, not (recipe.get("unresolved_content") if isinstance(recipe, dict) else True), "decision_facing_answer_recipe.unresolved_content"),
        ("permitted_inference_is_dict", True, isinstance(permitted_inference, dict), "decision_facing_answer_recipe.permitted_inference"),
        ("permitted_inference_allowed", False, (permitted_inference or {}).get("allowed") if isinstance(permitted_inference, dict) else None, "permitted_inference.allowed"),
        ("contract_is_dict", True, isinstance(contract, dict), "payload.resolution_contract"),
        ("contract_operation", "ask", str((contract or {}).get("operation") or "").strip().lower() if isinstance(contract, dict) else None, "resolution_contract.operation"),
        ("contract_target_nonempty", True, bool(str((contract or {}).get("target") or "").strip()) if isinstance(contract, dict) else False, "resolution_contract.target"),
        ("response_policy_is_dict", True, isinstance(response_policy, dict), "payload.response_policy"),
        ("scene_is_dict", True, isinstance(scene, dict), "payload.scene"),
        ("dialogue_plan_is_dict", True, isinstance(dialogue_plan, dict), "payload.dialogue_social_plan"),
        ("speaker_selection_is_dict", True, isinstance(speaker_selection, dict), "payload.speaker_selection"),
        ("allowed_speaker_ids_is_list", True, isinstance(allowed, list), "speaker_selection.allowed_speaker_ids"),
        ("exactly_one_allowed_speaker", 1, len(allowed) if isinstance(allowed, list) else None, "speaker_selection.allowed_speaker_ids length"),
        ("active_interlocutor_is_dict", True, isinstance(active_interlocutor, dict), "payload.active_interlocutor"),
        ("active_interlocutor_npc_id_nonempty", True, bool(npc_id), "active_interlocutor.npc_id"),
        ("allowed_speakers_match_interlocutor", [npc_id] if npc_id else ["<missing>"], allowed, "speaker_selection.allowed_speaker_ids == [active_interlocutor.npc_id]"),
        ("primary_speaker_matches_interlocutor", npc_id or "<missing>", (speaker_selection or {}).get("primary_speaker_id") if isinstance(speaker_selection, dict) else None, "speaker_selection.primary_speaker_id"),
        ("contract_interlocutor_matches", npc_id or "<missing>", (contract or {}).get("interlocutor") if isinstance(contract, dict) else None, "resolution_contract.interlocutor"),
        ("mechanical_metadata_is_dict", True, isinstance(metadata, dict), "mechanical_resolution.metadata"),
        ("selected_resolver", "social", (metadata or {}).get("selected_resolver") if isinstance(metadata, dict) else None, "mechanical_resolution.metadata.selected_resolver"),
        ("ordinary_contract_established", True, (metadata or {}).get("ordinary_contract_established") if isinstance(metadata, dict) else None, "mechanical_resolution.metadata.ordinary_contract_established"),
        ("social_is_dict", True, isinstance(social, dict), "mechanical_resolution.social"),
        ("social_npc_id", npc_id or "<missing>", (social or {}).get("npc_id") if isinstance(social, dict) else None, "mechanical_resolution.social.npc_id"),
        ("social_target_resolved", True, (social or {}).get("target_resolved") if isinstance(social, dict) else None, "mechanical_resolution.social.target_resolved"),
        ("reply_plan_kind", "harmless_subjective_response_permitted", (social or {}).get("reply_plan_kind") if isinstance(social, dict) else None, "mechanical_resolution.social.reply_plan_kind"),
        ("incidental_subjective_allowed", True, (social or {}).get("incidental_subjective_allowed") if isinstance(social, dict) else None, "mechanical_resolution.social.incidental_subjective_allowed"),
        ("objective_world_fact_authority", "none", (social or {}).get("objective_world_fact_authority") if isinstance(social, dict) else None, "mechanical_resolution.social.objective_world_fact_authority"),
        ("npc_speech_authority", "claim_only", (social or {}).get("npc_speech_authority") if isinstance(social, dict) else None, "mechanical_resolution.social.npc_speech_authority"),
        ("durable_state_mutation_allowed", False, (social or {}).get("durable_state_mutation_allowed") if isinstance(social, dict) else None, "mechanical_resolution.social.durable_state_mutation_allowed"),
        ("topic_revealed_absent", True, not bool((social or {}).get("topic_revealed")) if isinstance(social, dict) else False, "mechanical_resolution.social.topic_revealed"),
        ("skill_check_absent", True, not bool((social or {}).get("skill_check")) if isinstance(social, dict) else False, "mechanical_resolution.social.skill_check"),
        ("requires_check_false", False, (mechanical or {}).get("requires_check") if isinstance(mechanical, dict) else None, "mechanical_resolution.requires_check"),
        ("state_changes_absent", True, not bool((mechanical or {}).get("state_changes")) if isinstance(mechanical, dict) else False, "mechanical_resolution.state_changes"),
        ("world_updates_absent", True, not bool((mechanical or {}).get("world_updates")) if isinstance(mechanical, dict) else False, "mechanical_resolution.world_updates"),
        ("discovered_clues_absent", True, not bool((mechanical or {}).get("discovered_clues")) if isinstance(mechanical, dict) else False, "mechanical_resolution.discovered_clues"),
        ("resolved_transition_absent", True, not bool((mechanical or {}).get("resolved_transition")) if isinstance(mechanical, dict) else False, "mechanical_resolution.resolved_transition"),
        ("combat_is_dict", True, isinstance(combat, dict), "payload.combat"),
        ("not_in_combat", False, (combat or {}).get("in_combat") if isinstance(combat, dict) else None, "payload.combat.in_combat"),
    ]
    failed = False
    for name, required, actual, source in checks:
        passed = _check(rows, name, required, actual, source)
        if not passed:
            failed = True
            break
    if failed:
        return rows

    opening = payload.get("opening_narration_obligations")
    advancement = payload.get("scene_advancement")
    if not _check(rows, "opening_is_dict", True, isinstance(opening, dict), "payload.opening_narration_obligations"):
        return rows
    if not _check(rows, "opening_mode_false", False, opening.get("opening_mode") if isinstance(opening, dict) else None, "opening_narration_obligations.opening_mode"):
        return rows
    if not _check(rows, "scene_advancement_is_dict", True, isinstance(advancement, dict), "payload.scene_advancement"):
        return rows
    _check(
        rows,
        "scene_advancement_all_falsy",
        True,
        isinstance(advancement, dict) and not any(advancement.values()),
        "payload.scene_advancement values",
    )
    return rows


def hypothetical_reduced(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the projector's omission steps without treating the result as selected."""
    projected = deepcopy(payload)
    omitted: list[str] = []
    compacted: list[str] = []
    for key in (
        "opening_narration_obligations",
        "opening_scene_realization",
        "opening_inputs_are_curated",
        "opening_selector_source_used",
        "opening_selector_selected_facts",
        "opening_curated_facts",
        "opening_fact_telemetry",
        "transition",
        "scene_advancement",
        "world_progression_summary",
    ):
        if key in projected:
            projected.pop(key, None)
            omitted.append(key)
    if gm_module._social_projection_empty_combat(projected.get("combat")):
        projected.pop("combat", None)
        omitted.append("combat")
    for key in ("lead_context", "interlocutor_lead_context", "interlocutor_lead_behavior_hints"):
        if key in projected and not gm_module._social_projection_nonempty(projected.get(key)):
            projected.pop(key, None)
            omitted.append(key)
    compact_turn = gm_module._compact_social_turn_packet(projected.get("turn_packet"))
    if compact_turn is not None:
        projected["turn_packet"] = compact_turn
        compacted.append("turn_packet")
    compact_mechanical = gm_module._compact_social_mechanical_resolution(projected.get("mechanical_resolution"))
    if compact_mechanical is not None:
        projected["mechanical_resolution"] = compact_mechanical
        compacted.append("mechanical_resolution")
    compact_plan = gm_module._compact_social_narrative_plan(projected.get("narrative_plan"))
    if compact_plan is not None:
        projected["narrative_plan"] = compact_plan
        compacted.append("narrative_plan")
    projected["hypothetical_provider_context_projection"] = {
        "selected": False,
        "note": "Omission steps applied only as a size estimate. The live projector did not select reduced context.",
        "omitted_sections": omitted,
        "compacted_sections": compacted,
    }
    return projected


def measure_messages(system: str, payload: dict[str, Any]) -> dict[str, int]:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    serialized = json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {
        "serialized_prompt_bytes": len(serialized),
        "estimated_tokens_bytes_over_4": round(len(serialized) / 4),
        "user_payload_bytes": len(messages[1]["content"].encode("utf-8")),
    }


def provider_messages_from_request(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    messages = data.get("provider_input")
    return messages if isinstance(messages, list) else []


def preflight_summary(rows: list[dict[str, Any]], capture: dict[str, Any] | None, request_path: Path) -> dict[str, Any]:
    payload = capture["payload"] if capture else {}
    contract = payload.get("resolution_contract") if isinstance(payload.get("resolution_contract"), dict) else {}
    mechanical = payload.get("mechanical_resolution") if isinstance(payload.get("mechanical_resolution"), dict) else {}
    metadata = mechanical.get("metadata") if isinstance(mechanical.get("metadata"), dict) else {}
    social = mechanical.get("social") if isinstance(mechanical.get("social"), dict) else {}
    obligation = metadata.get("interaction_obligation") if isinstance(metadata.get("interaction_obligation"), dict) else {}
    speaker = payload.get("speaker_selection") if isinstance(payload.get("speaker_selection"), dict) else {}
    dialogue = payload.get("dialogue_social_plan") if isinstance(payload.get("dialogue_social_plan"), dict) else {}
    decision = payload.get("gm_resolution_decision") if isinstance(payload.get("gm_resolution_decision"), dict) else {}
    recipe = payload.get("decision_facing_answer_recipe") if isinstance(payload.get("decision_facing_answer_recipe"), dict) else {}
    messages = provider_messages_from_request(request_path)
    system = messages[0]["content"] if messages else ""
    post_payload = {}
    if len(messages) > 1 and isinstance(messages[1], dict):
        try:
            post_payload = json.loads(messages[1].get("content") or "{}")
        except json.JSONDecodeError:
            post_payload = {}
    projection = post_payload.get("provider_context_projection") if isinstance(post_payload.get("provider_context_projection"), dict) else {}
    first_fail = next((row for row in rows if not row["pass"]), None)
    full_measure = measure_messages(system, payload) if system and payload else {}
    reduced_payload = hypothetical_reduced(payload) if payload else {}
    reduced_measure = measure_messages(system, reduced_payload) if system and reduced_payload else {}
    recent = payload.get("recent_log") if isinstance(payload.get("recent_log"), list) else []
    retained = []
    for entry in recent:
        if not isinstance(entry, dict):
            continue
        retained.append(
            {
                "player_input": (entry.get("log_meta") or {}).get("player_input") if isinstance(entry.get("log_meta"), dict) else entry.get("player_input"),
                "gm_snippet": entry.get("gm_snippet") or (entry.get("gm_output") or {}).get("player_facing_text"),
            }
        )
    return {
        "selected_resolver": metadata.get("selected_resolver"),
        "resolution_contract": {
            "operation": contract.get("operation"),
            "interlocutor_id": contract.get("interlocutor_id") or contract.get("interlocutor"),
            "interlocutor_id_key_present": "interlocutor_id" in contract,
            "interlocutor": contract.get("interlocutor"),
            "interlocutor_field_note": "The provider payload copies authoritative contract.interlocutor_id into resolution_contract.interlocutor.",
            "target": contract.get("target"),
            "subject": contract.get("subject"),
            "contract_id": contract.get("contract_id"),
            "discourse_ref": contract.get("discourse_ref"),
            "scene_id": contract.get("scene_id"),
        },
        "interaction_obligation": {
            "interlocutor_id": obligation.get("interlocutor_id"),
            "resolution_mode": obligation.get("resolution_mode"),
            "target": obligation.get("target"),
        },
        "speaker_selection": {
            "primary_speaker_id": speaker.get("primary_speaker_id"),
            "allowed_speaker_ids": speaker.get("allowed_speaker_ids"),
            "authoritative_reason": (speaker.get("debug") or {}).get("authoritative_reason") if isinstance(speaker.get("debug"), dict) else None,
        },
        "dialogue_speaker_id": dialogue.get("speaker_id"),
        "social_npc_id": social.get("npc_id"),
        "social_target_resolved": social.get("target_resolved"),
        "active_interlocutor": payload.get("active_interlocutor"),
        "scene_id": (payload.get("scene") or {}).get("id") if isinstance(payload.get("scene"), dict) else None,
        "response_envelope": gm_module._provider_response_contract_from_payload(payload) if payload else None,
        "provider_context_projection_selected": projection.get("selected"),
        "authorized_answer_scope": {
            "permitted_state_mutations": decision.get("permitted_state_mutations"),
            "objective_world_fact_authority": social.get("objective_world_fact_authority"),
            "npc_speech_authority": social.get("npc_speech_authority"),
            "reply_plan_kind": social.get("reply_plan_kind"),
            "incidental_subjective_allowed": social.get("incidental_subjective_allowed"),
            "durable_state_mutation_allowed": social.get("durable_state_mutation_allowed"),
            "turn_operation": recipe.get("turn_operation"),
        },
        "predicate_rows": rows,
        "first_failing_predicate": first_fail,
        "full_context": full_measure,
        "hypothetical_reduced_context": reduced_measure,
        "hypothetical_note": "Hypothetical bytes apply the omission steps on a copy. They are not live savings and were not sent.",
        "recent_log_entries": len(recent),
        "retained_history": retained,
        "preflight_request_captured": request_path.exists(),
    }


def validation_slice(payload: dict[str, Any]) -> dict[str, Any]:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    return {
        "regeneration_invoked": meta.get("regeneration_invoked"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "hard_validation_attempt_1": meta.get("hard_validation_attempt_1"),
        "hard_validation_attempt_2": meta.get("hard_validation_attempt_2"),
        "accepted_response": meta.get("accepted_response"),
        "decision_review": meta.get("decision_review"),
        "player_facing_text": gm.get("player_facing_text"),
    }


def claim_rows(audit: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(audit, dict):
        return rows
    buckets = [audit]
    narration = audit.get("narration_validation")
    if isinstance(narration, dict):
        buckets.append(narration)
    for bucket in buckets:
        for name in ("violations", "claim_results", "proposed_facts", "accepted_realized_claims"):
            for item in bucket.get(name) or []:
                if isinstance(item, dict):
                    rows.append(
                        {
                            "bucket": name,
                            "text": item.get("text"),
                            "outcome_classification": item.get("outcome_classification"),
                            "reason_codes": item.get("reason_codes"),
                            "authorized": item.get("authorized"),
                            "consequence": item.get("consequence"),
                            "epistemic_status": item.get("epistemic_status"),
                        }
                    )
    return rows


def severe_mutation(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    problems = []
    if before.get("active_scene_id") != after.get("active_scene_id"):
        problems.append("active_scene_changed")
    if before.get("character") != after.get("character"):
        problems.append("character_sheet_changed")
    if before.get("world_npc_ids") != after.get("world_npc_ids"):
        problems.append("npc_roster_changed")
    if before["scene"]["hidden_facts"] != after["scene"]["hidden_facts"]:
        problems.append("hidden_facts_changed")
    hidden = {item.strip() for item in before["scene"]["hidden_facts"] if isinstance(item, str)}
    for fact in after["scene"]["visible_facts"]:
        if isinstance(fact, str) and fact.strip() in hidden and fact not in before["scene"]["visible_facts"]:
            problems.append("hidden_fact_promoted")
    before_clues = (before.get("scene_runtime") or {}).get("discovered_clues")
    after_clues = (after.get("scene_runtime") or {}).get("discovered_clues")
    if before_clues != after_clues:
        problems.append("discovered_clues_changed")
    return problems


def hidden_disclosure(text: str, hidden: list[str]) -> list[str]:
    hits = []
    lowered = text.lower()
    for fact in hidden:
        if isinstance(fact, str) and len(fact) > 24 and fact.lower() in lowered:
            hits.append(fact[:80])
    return hits


def score_answer(text: str, interlocutor_id: str | None, hidden_hits: list[str], accepted: bool) -> dict[str, Any]:
    lower = (text or "").lower()
    names_captain = "guard captain" in lower or "captain" in lower
    correct = 2 if interlocutor_id == "guard_captain" and names_captain else (1 if interlocutor_id == "guard_captain" and text else 0)
    answers_hardness = any(token in lower for token in ("harder", "hard", "difficult", "hampers", "hinders", "easier", "vigilance", "alert", "watch"))
    mentions_rain = "rain" in lower
    intent = 2 if answers_hardness and mentions_rain else (1 if answers_hardness or mentions_rain else 0)
    relevance = 2 if mentions_rain and ("watch" in lower or "alert" in lower or "vigil" in lower) else (1 if text and (mentions_rain or "watch" in lower) else 0)
    refusal = "cannot answer" in lower or "not settled" in lower
    naturalness = 0 if refusal or not text else (2 if len(text.split()) >= 12 else 1)
    authority = 0 if hidden_hits else 2
    notes = []
    if refusal:
        notes.append("Refusal does not receive full naturalness credit.")
    if not accepted:
        notes.append("Final text was not the accepted provider candidate.")
    if hidden_hits:
        notes.append("Hidden-fact overlap detected.")
    return {
        "correct_interlocutor": correct,
        "intent_comprehension": intent,
        "answer_relevance": relevance,
        "naturalness": naturalness,
        "authority_integrity": authority,
        "total": correct + intent + relevance + naturalness + authority,
        "notes": notes,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def backup_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def restore_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def run_chat(turn_id: str) -> dict[str, Any]:
    CURRENT["turn"] = turn_id
    before = snapshot()
    save_json(EVIDENCE / turn_id / "state_before.json", before)
    started = time.perf_counter()
    error = None
    payload: dict[str, Any] = {}
    http_status = None
    try:
        with TestClient(api.app) as client:
            response = client.post("/api/chat", json={"text": FOLLOWUP})
            http_status = response.status_code
            payload = response.json()
    except PreflightStop as exc:
        error = f"PreflightStop: {exc}"
    except BudgetStop as exc:
        error = f"BudgetStop: {exc}"
    except Exception:
        error = traceback.format_exc()
    after = snapshot()
    save_json(EVIDENCE / turn_id / "state_after.json", after)
    if isinstance(payload, dict):
        save_json(EVIDENCE / turn_id / "api_response.json", payload)
    return {
        "turn": turn_id,
        "http_status": http_status,
        "error": error,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "before": before,
        "after": after,
        "payload": payload if isinstance(payload, dict) else {},
        "mutations": severe_mutation(before, after),
    }


def judgment_for_failure(row: dict[str, Any] | None) -> str:
    if row is None:
        return "No eligibility predicate failed. Reduced context was eligible."
    name = row["name"]
    restrictive = {
        "reply_plan_kind",
        "incidental_subjective_allowed",
        "contract_interlocutor_matches",
        "allowed_speakers_match_interlocutor",
        "primary_speaker_matches_interlocutor",
        "social_npc_id",
        "active_interlocutor_npc_id_nonempty",
        "topic_revealed_absent",
        "unresolved_content_absent",
        "permitted_inference_allowed",
        "response_operation",
        "declaration_expectation",
    }
    genuine = {
        "not_in_combat",
        "selected_resolver",
        "requires_check_false",
        "state_changes_absent",
        "world_updates_absent",
        "discovered_clues_absent",
        "resolved_transition_absent",
        "durable_state_mutation_allowed",
        "objective_world_fact_authority",
        "npc_speech_authority",
        "skill_check_absent",
        "opening_mode_false",
        "scene_advancement_all_falsy",
        "exactly_one_allowed_speaker",
        "permitted_state_mutations",
        "contract_operation",
    }
    if name == "exactly_one_allowed_speaker":
        return (
            "The follow-up is genuinely ineligible for reduced context. "
            "`speaker_selection.allowed_speaker_ids` is empty, and the projector requires exactly one grounded speaker. "
            "That predicate is doing the safety job it was written to do. "
            "The upstream speaker selector reported `no addressable target resolved` even though "
            "`resolution_contract.interlocutor` is `guard_captain`. "
            "The predicate was not modified and eligibility was not forced."
        )
    if name in genuine:
        return (
            f"`{name}` is an authority or scope gate. The follow-up is genuinely outside the "
            "current reduced-context contract for this predicate. The predicate was not modified."
        )
    if name in restrictive:
        return (
            f"`{name}` blocks reduced context even though the follow-up is an ordinary continuation "
            "with Guard Captain in scene. The predicate is overly restrictive relative to that "
            "conversational purpose. It was not modified and eligibility was not forced."
        )
    return (
        f"`{name}` failed. Whether it is overly restrictive depends on the actual value recorded above. "
        "The predicate was not modified."
    )


def main() -> None:
    global HALT, MODE
    config = verify_config()
    phase0 = {
        "git_head": config["git_head"],
        "git_status_short": git("status --short"),
        "git_diff_stat": git("diff --stat"),
        "config": config,
        "production_mtimes_before": BEFORE_MTIMES,
        "dirty_worktree_preserved": True,
    }
    save_json(EVIDENCE / "phase0_worktree.json", phase0)
    status("PHASE0 RECORDED")

    isolated = EVIDENCE / "isolated_session"
    backup = EVIDENCE / "reconstructed_backup"
    reconstruction = reconstruct(isolated)
    backup_tree(isolated, backup)
    status("PHASE1 RECONSTRUCTED")

    MODE["phase"] = "preflight"
    CURRENT["turn"] = "preflight"
    preflight_run = run_chat("preflight")
    restore_tree(backup, isolated)
    point_storage(isolated)
    status(f"PHASE2 PREFLIGHT error={preflight_run.get('error')}")

    preflight_capture = next((item for item in PROJECTOR_CAPTURES if item["phase"] == "preflight"), None)
    rows = (
        evaluate_predicates(preflight_capture["payload"], preflight_capture["provider_response_contract"])
        if preflight_capture
        else []
    )
    request_path = EVIDENCE / "preflight" / "provider_request_generation_1.json"
    summary = preflight_summary(rows, preflight_capture, request_path)
    save_json(EVIDENCE / "preflight_summary.json", summary)
    interlocutor = (summary.get("resolution_contract") or {}).get("interlocutor")
    interlocutor_id = (summary.get("resolution_contract") or {}).get("interlocutor_id")
    resolver = summary.get("selected_resolver")
    if interlocutor != "guard_captain" or interlocutor_id != "guard_captain" or resolver != "social":
        HALT = f"STOP interlocutor preflight failed: resolver={resolver} interlocutor={interlocutor} interlocutor_id={interlocutor_id}"
        status(HALT)
        live_run = None
    else:
        MODE["phase"] = "live"
        PROJECTOR_CAPTURES.clear()
        live_run = run_chat("T2")
        status(f"PHASE5 LIVE http={live_run.get('http_status')} error={live_run.get('error')} tokens={spent_tokens()} halt={HALT}")

    after_mtimes = production_mtimes()
    drift = [key for key, value in BEFORE_MTIMES.items() if after_mtimes.get(key) != value]
    save_json(EVIDENCE / "production_mtime_drift.json", drift)
    write_reports(config, reconstruction, summary, preflight_run, live_run, drift)


def write_reports(config, reconstruction, summary, preflight_run, live_run, drift) -> None:
    payload = (live_run or {}).get("payload") or {}
    validation = validation_slice(payload) if live_run else {}
    final_text = str(validation.get("player_facing_text") or "")
    attempt1 = validation.get("hard_validation_attempt_1") if isinstance(validation.get("hard_validation_attempt_1"), dict) else {}
    attempt2 = validation.get("hard_validation_attempt_2") if isinstance(validation.get("hard_validation_attempt_2"), dict) else {}
    accepted = validation.get("accepted_response") if isinstance(validation.get("accepted_response"), dict) else {}
    first_accepted = attempt1.get("hard_valid") is True
    retry_used = any(int(call.get("retry_attempt") or 0) > 0 for call in CALLS)
    hidden_hits = hidden_disclosure(final_text, ((live_run or {}).get("before") or {}).get("scene", {}).get("hidden_facts") or [])
    for call in CALLS:
        hidden_hits.extend(hidden_disclosure(str(call.get("parsed_narration") or ""), ((live_run or {}).get("before") or {}).get("scene", {}).get("hidden_facts") or []))
    scores = score_answer(
        final_text,
        ((live_run or {}).get("after") or {}).get("active_interlocutor_id"),
        hidden_hits,
        bool(accepted.get("text")),
    )
    mutations = (live_run or {}).get("mutations") or []
    useful = bool(final_text) and "cannot answer" not in final_text.lower() and scores["total"] >= 8 and not hidden_hits and not mutations

    if HALT and live_run is None and "interlocutor" in (HALT or ""):
        decision = "D - CONTINUITY FAILURE REMAINS"
    elif HALT and "budget" in (HALT or ""):
        decision = "G - BUDGET EXHAUSTED"
    elif HALT and live_run is None:
        decision = "F - PROVIDER / ENVIRONMENT BLOCKED"
    elif not live_run or live_run.get("error") or live_run.get("http_status") != 200 or not CALLS:
        decision = "F - PROVIDER / ENVIRONMENT BLOCKED" if not CALLS else "H - INCONCLUSIVE"
    elif mutations or hidden_hits:
        decision = "H - INCONCLUSIVE"
    elif first_accepted and useful and not retry_used:
        decision = "A - LIVE FOLLOW-UP VERIFIED"
    elif useful and retry_used:
        decision = "B - FOLLOW-UP WORKS WITH RETRY"
    elif (not first_accepted) and attempt1 and not useful:
        # Distinguish false positive from evasive fallback after a correct rejection.
        audit_text = json.dumps(attempt1, ensure_ascii=False).lower()
        candidate = str(CALLS[0].get("parsed_narration") or attempt1.get("text") or "")
        harmless = bool(re.search(r"\brain|watch|vigilance|alert|discomfort|harder|hampers|perhaps|maybe\b", candidate, re.I))
        consequential = bool(re.search(r"\bborn\b|\bsecret\b|\btunnel\b|\bunlock|\byou discover\b|\bmurdered\b", candidate, re.I))
        if harmless and not consequential and "unauthorized_resolution_decision_fact" in audit_text:
            decision = "C - VALIDATION FALSE POSITIVE REMAINS"
        elif "cannot answer" in final_text.lower():
            decision = "E - NARRATIVE QUALITY FAILURE"
        else:
            decision = "E - NARRATIVE QUALITY FAILURE"
    elif final_text and not useful:
        decision = "E - NARRATIVE QUALITY FAILURE"
    else:
        decision = "H - INCONCLUSIVE"

    input_tokens = sum(int((call.get("usage") or {}).get("input_tokens") or 0) for call in CALLS)
    output_tokens = sum(int((call.get("usage") or {}).get("output_tokens") or 0) for call in CALLS)
    total_tokens = spent_tokens()
    retry_tokens = sum(int((call.get("usage") or {}).get("total_tokens") or 0) for call in CALLS if int(call.get("retry_attempt") or 0) > 0)
    first_fail = summary.get("first_failing_predicate") or {}

    usage_rows = []
    for call in CALLS:
        usage = call.get("usage") or {}
        attempt_name = "hard_validation_attempt_2" if int(call.get("retry_attempt") or 0) > 0 else "hard_validation_attempt_1"
        attempt = validation.get(attempt_name) if isinstance(validation.get(attempt_name), dict) else {}
        usage_rows.append(
            {
                "gameplay_turn": call.get("turn"),
                "request_number": call.get("index"),
                "kind": call.get("kind"),
                "model": call.get("response_model") or call.get("model"),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "cached_input_tokens": usage.get("cached_input_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "latency_seconds": call.get("latency_seconds"),
                "retry_status": "retry" if int(call.get("retry_attempt") or 0) > 0 else "initial",
                "validation_outcome": attempt.get("hard_valid", ""),
                "rejection_reasons": json.dumps(attempt.get("reasons") or [], ensure_ascii=False),
            }
        )
    write_csv(OUT / "PR-DA_provider_usage.csv", usage_rows or [{"gameplay_turn": "", "request_number": "", "kind": "", "model": "", "input_tokens": "", "output_tokens": "", "total_tokens": "", "retry_status": ""}])

    predicate_lines = [
        "| Predicate | Required | Actual | Result | Authority source |",
        "|---|---|---|---|---|",
    ]
    for row in summary.get("predicate_rows") or []:
        predicate_lines.append(
            f"| `{row['name']}` | `{row['required']}` | `{row['actual']}` | {'PASS' if row['pass'] else 'FAIL'} | `{row['authority_source']}` |"
        )
    write_text(
        OUT / "PR-DA_projection_eligibility.md",
        "\n".join(
            [
                "# PR-DA Projection Eligibility",
                "",
                "Predicates are the PR-CW conditions in `game.gm._project_harmless_social_provider_context`, evaluated in source order on the pre-projection payload of the reconstructed follow-up.",
                "",
                "Reduced context was not forced.",
                "",
                f"First failing predicate: `{first_fail.get('name') or 'none'}`.",
                "",
                judgment_for_failure(summary.get("first_failing_predicate")),
                "",
                f"Response envelope: `{summary.get('response_envelope')}`.",
                "",
                f"Projector selected on the captured request: `{summary.get('provider_context_projection_selected')}`.",
                "",
                "## Measurements",
                "",
                "Full-context serialized bytes are measured from the pre-projection payload plus the system prompt captured for this follow-up.",
                "",
                f"- Full-context serialized bytes: {summary.get('full_context', {}).get('serialized_prompt_bytes')}",
                f"- Full-context estimated tokens (bytes/4): {summary.get('full_context', {}).get('estimated_tokens_bytes_over_4')}",
                f"- Hypothetical reduced-context serialized bytes: {summary.get('hypothetical_reduced_context', {}).get('serialized_prompt_bytes')}",
                f"- Hypothetical reduced-context estimated tokens (bytes/4): {summary.get('hypothetical_reduced_context', {}).get('estimated_tokens_bytes_over_4')}",
                "",
                summary.get("hypothetical_note") or "",
                "",
                f"Retained history entries: {summary.get('recent_log_entries')}.",
                "",
                "```json",
                dump_json(summary.get("retained_history")),
                "```",
                "",
                *predicate_lines,
                "",
            ]
        ),
    )

    write_text(
        OUT / "PR-DA_reconstructed_state.md",
        "\n".join(
            [
                "# PR-DA Reconstructed State",
                "",
                reconstruction["method"],
                "",
                f"Turn 1 player input: {TURN1_PLAYER}",
                "",
                f"Accepted Turn 1 answer marker present: {TURN1_ANSWER_MARK}",
                "",
                "Preserved from the Turn 1 engine return and the Turn 1 log line:",
                "",
                "- Scene: frontier_gate.",
                "- NPC: guard_captain, still addressable and present in the world roster.",
                "- Discourse focus active interlocutor: guard_captain.",
                "- Interaction target: guard_captain.",
                "- Turn counter: 2, the value recorded after the successful Turn 1.",
                "- Recent conversation: the Turn 1 exchange only. The Turn 2 refusal log line was excluded.",
                "",
                f"T1 state_after matches T2 state_before: {reconstruction['t1_state_after_matches_t2_state_before']}.",
                "",
                f"Document choices: `{json.dumps(reconstruction['document_choices'])}`.",
                "",
                f"Verification problems: {reconstruction['verification_problems'] or 'none'}.",
                "",
                "The reconstructed session is stored under `artifacts/pr_da_followup_efficiency/evidence/isolated_session/`. Production saves were not used as the gameplay session.",
                "",
            ]
        ),
    )

    contract = summary.get("resolution_contract") or {}
    write_text(
        OUT / "PR-DA_resolver_preflight.md",
        "\n".join(
            [
                "# PR-DA Resolver Preflight",
                "",
                "The follow-up was submitted through the chat route with the provider call aborted before the network.",
                "",
                f"Player: {FOLLOWUP}",
                "",
                f"Selected resolver: `{summary.get('selected_resolver')}`.",
                "",
                f"Operation: `{contract.get('operation')}`.",
                "",
                f"Authoritative interlocutor id, projected as `resolution_contract.interlocutor`: `{contract.get('interlocutor')}`.",
                "",
                "The provider payload does not carry a separate `interlocutor_id` key. `resolution_contract.py` copies `contract.interlocutor_id` into that `interlocutor` field.",
                "",
                f"interaction_obligation.interlocutor_id: `{(summary.get('interaction_obligation') or {}).get('interlocutor_id')}`.",
                "",
                f"interaction_obligation.resolution_mode: `{(summary.get('interaction_obligation') or {}).get('resolution_mode')}`.",
                "",
                f"active_interlocutor payload: `{json.dumps(summary.get('active_interlocutor'), ensure_ascii=False)}`.",
                "",
                f"social.npc_id: `{summary.get('social_npc_id')}`. social.target_resolved: `{summary.get('social_target_resolved')}`.",
                "",
                f"Speaker selection: `{json.dumps(summary.get('speaker_selection'), ensure_ascii=False)}`.",
                "",
                f"Scene payload id: `{summary.get('scene_id')}`. Session scene remains frontier_gate in the reconstructed state.",
                "",
                f"Response envelope: `{summary.get('response_envelope')}`.",
                "",
                "Authorized answer scope:",
                "",
                "```json",
                dump_json(summary.get("authorized_answer_scope")),
                "```",
                "",
                f"Preflight HTTP/error: {preflight_run.get('http_status')} / {preflight_run.get('error')}.",
                "",
                "The isolated session was restored from the reconstructed backup after this preflight, because the chat route advances the world tick before narration.",
                "",
            ]
        ),
    )

    transcript = ["# PR-DA Live Transcript", "", f"Player: {FOLLOWUP}", ""]
    if not live_run:
        transcript.append("No live gameplay turn was submitted.")
    else:
        transcript += [
            f"HTTP status: {live_run.get('http_status')}",
            "",
            f"Final player-facing answer: {final_text}",
            "",
            "Provider candidates:",
            "",
        ]
        for call in CALLS:
            transcript += [
                f"## Request {call.get('index')} retry_attempt={call.get('retry_attempt')}",
                "",
                f"Model requested: {call.get('model')}",
                "",
                f"Response model: {call.get('response_model')}",
                "",
                f"Usage: {json.dumps(call.get('usage'), ensure_ascii=False)}",
                "",
                f"Latency seconds: {call.get('latency_seconds')}",
                "",
                f"Error: {call.get('error')}",
                "",
                "Narration:",
                "",
                str(call.get("parsed_narration") or ""),
                "",
            ]
    write_text(OUT / "PR-DA_live_transcript.md", "\n".join(transcript) + "\n")

    trace = ["# PR-DA Validation Trace", ""]
    if not validation:
        trace.append("No live validation trace was produced.")
    else:
        trace += [
            f"Regeneration invoked: {validation.get('regeneration_invoked')}",
            "",
            f"Accepted attempt: {(accepted or {}).get('attempt')}",
            "",
            f"Accepted provenance: {(accepted or {}).get('provenance')}",
            "",
            f"Authority result: {(accepted or {}).get('authority_result')}",
            "",
            "## Attempt 1",
            "",
            "```json",
            dump_json(attempt1),
            "```",
            "",
            "## Attempt 2",
            "",
            "```json",
            dump_json(attempt2),
            "```",
            "",
        ]
    write_text(OUT / "PR-DA_validation_trace.md", "\n".join(trace))

    rejection_correct = "not applicable"
    rejected_text = ""
    if attempt1 and attempt1.get("hard_valid") is False:
        rejected_text = str(CALLS[0].get("parsed_narration") or attempt1.get("text") or "") if CALLS else str(attempt1.get("text") or "")
        claims = claim_rows(attempt1.get("gm_resolution_decision_audit"))
        consequential = any(
            isinstance(row.get("reason_codes"), list)
            and any("consequential" in str(code) or "hidden" in str(code) or "discovery" in str(code) for code in row["reason_codes"])
            for row in claims
        )
        rejection_correct = "correct" if consequential else "incorrect or overly broad for a qualified low-stakes observation"
        write_text(
            OUT / "PR-DA_validation_trace.md",
            (OUT / "PR-DA_validation_trace.md").read_text(encoding="utf-8")
            + "\n".join(
                [
                    "",
                    "## Rejected candidate analysis",
                    "",
                    "This analysis does not assume the rejection is a PR-CZ regression.",
                    "",
                    f"Exact rejected text:",
                    "",
                    rejected_text,
                    "",
                    f"Reasons: `{json.dumps(attempt1.get('reasons'), ensure_ascii=False)}`.",
                    "",
                    f"Rejection assessment: {rejection_correct}.",
                    "",
                    "Extracted claims:",
                    "",
                    "```json",
                    dump_json(claims),
                    "```",
                    "",
                ]
            ),
        )

    authority = [
        "# PR-DA Authority Assessment",
        "",
        f"Severe state mutations: {mutations or 'none'}.",
        "",
        f"Hidden-fact disclosure hits: {hidden_hits or 'none'}.",
        "",
        f"Discovered clues before: {((live_run or {}).get('before') or {}).get('scene_runtime', {}).get('discovered_clues') if live_run else 'n/a'}.",
        "",
        f"Discovered clues after: {((live_run or {}).get('after') or {}).get('scene_runtime', {}).get('discovered_clues') if live_run else 'n/a'}.",
        "",
        f"Interlocutor after: {((live_run or {}).get('after') or {}).get('active_interlocutor_id') if live_run else 'n/a'}.",
        "",
        f"Scores: `{json.dumps(scores)}`.",
        "",
        "A refusal without a useful answer does not receive full quality credit. Invented consequential facts fail authority integrity. Ordinary uncertainty is allowed.",
        "",
        f"Final narration matches validated content: {final_text == str(accepted.get('text') or final_text) if accepted else 'no accepted response recorded'}.",
        "",
    ]
    write_text(OUT / "PR-DA_authority_assessment.md", "\n".join(authority))

    write_text(
        OUT / "PR-DA_cost_comparison.md",
        "\n".join(
            [
                "# PR-DA Cost Comparison",
                "",
                "Historical measurements are from PR-CY provider usage. They are not remeasured here.",
                "",
                f"- PR-CY historical follow-up total tokens: {PR_CY_FOLLOWUP_TOTAL}",
                f"- PR-CY historical retry tokens: {PR_CY_RETRY_TOKENS}",
                "",
                "PR-DA actual live measurements:",
                "",
                f"- Input tokens: {input_tokens if CALLS else 'no live call'}",
                f"- Output tokens: {output_tokens if CALLS else 'no live call'}",
                f"- Total tokens: {total_tokens if CALLS else 'no live call'}",
                f"- Retry tokens: {retry_tokens if CALLS else 'no live call'}",
                f"- Successful first attempt: {'yes' if first_accepted else 'no' if CALLS else 'not run'}",
                f"- Useful final answer: {'yes' if useful else 'no'}",
                "",
                f"- Total token difference versus PR-CY follow-up: {total_tokens - PR_CY_FOLLOWUP_TOTAL if CALLS else 'not applicable'}",
                f"- Retry token difference versus PR-CY retry: {retry_tokens - PR_CY_RETRY_TOKENS if CALLS else 'not applicable'}",
                "",
                "Reconstructed byte estimates in the eligibility report are not live savings.",
                "",
                "Differences are not attributed solely to PR-CZ. The live prompt also depends on session history, routing, and whatever context the projector actually selected.",
                "",
            ]
        ),
    )

    write_text(
        OUT / "PR-DA_remaining_risks.md",
        "\n".join(
            [
                "# PR-DA Remaining Risks",
                "",
                f"- First failing reduced-context predicate: `{first_fail.get('name') or 'none'}`.",
                "- Hypothetical reduced-context size is not a live saving.",
                "- One follow-up sample does not establish that every ordinary continuation will validate on the first attempt.",
                "- The shared turn-pipeline suite was not rerun.",
                "- Production saves were left untouched; this result is from an isolated copy of the PR-CY Turn 1 state.",
                "",
            ]
        ),
    )

    write_text(
        OUT / "PR-DA_verification_report.md",
        "\n".join(
            [
                "# PR-DA Verification Report",
                "",
                "Mode: FOLLOW-UP EFFICIENCY VERIFICATION.",
                "",
                "Implementation changes: none.",
                "",
                f"Git HEAD: `{config['git_head']}`.",
                "",
                "The worktree was already dirty and was not reset. PR-CZ modules are present as untracked working-tree files, so this run exercises the dirty tree rather than HEAD alone.",
                "",
                f"Provider: {config['provider']} Responses API. Startup preflight skipped. Live interpretation disabled.",
                "",
                f"Configured models: `{json.dumps(config['models'])}`.",
                "",
                f"Required response model: {REQUIRED_RESPONSE_MODEL}.",
                "",
                f"Reconstructed prior state: {'yes' if not reconstruction['verification_problems'] else 'no'}.",
                "",
                f"Interlocutor preflight: `{contract.get('interlocutor_id')}` via resolver `{summary.get('selected_resolver')}`.",
                "",
                f"Reduced-context selected: `{summary.get('provider_context_projection_selected')}`.",
                "",
                f"First failing predicate: `{first_fail.get('name') or 'none'}`.",
                "",
                f"Live provider requests: {len(CALLS)}.",
                "",
                f"Input tokens: {input_tokens if CALLS else 'no live call'}.",
                "",
                f"Output tokens: {output_tokens if CALLS else 'no live call'}.",
                "",
                f"Total tokens: {total_tokens if CALLS else 'no live call'}.",
                "",
                f"Retry tokens: {retry_tokens if CALLS else 'no live call'}.",
                "",
                f"Final player-facing answer: {final_text or 'none'}.",
                "",
                f"Quality scores: `{json.dumps(scores)}`.",
                "",
                f"Production mtime drift: {drift or 'none'}.",
                "",
                f"Halt: {HALT or 'none'}.",
                "",
                f"PR-DA decision: {decision}.",
                "",
            ]
        ),
    )

    changed = [
        "artifacts/pr_da_followup_efficiency/",
        "handoff/CURRENT_REVIEW.md",
        "handoff/REVIEW_MANIFEST.json",
        "handoff/CURRENT_REVIEW.zip",
    ]
    write_text(OUT / "changed_files.txt", "\n".join(changed) + "\n")

    full = summary.get("full_context") or {}
    reduced = summary.get("hypothetical_reduced_context") or {}
    current = f"""PR-DA

MODE:
FOLLOW-UP EFFICIENCY VERIFICATION

PR-CZ inherited decision:
A — FOLLOW-UP RELIABILITY REPAIRED

Live provider calls:
{len(CALLS)}

Model:
{REQUIRED_RESPONSE_MODEL if CALLS else config['models']['MODEL_NAME']}

Reconstructed prior state:
{'yes — PR-CY Turn 1 API session plus Turn 1 log only' if not reconstruction['verification_problems'] else 'no'}

Interlocutor preflight:
{contract.get('interlocutor_id')} / resolver {summary.get('selected_resolver')}

Reduced-context eligibility:
selected={summary.get('provider_context_projection_selected')}

Failing eligibility predicate:
{first_fail.get('name') or 'none'}

Provider input tokens:
{input_tokens if CALLS else 'no live call'}

Provider output tokens:
{output_tokens if CALLS else 'no live call'}

Total tokens:
{total_tokens if CALLS else 'no live call'}

Retry tokens:
{retry_tokens if CALLS else 'no live call'}

Final player-facing answer:
{final_text or 'none'}

Authority integrity:
{scores['authority_integrity']} / 2; hidden disclosure={bool(hidden_hits)}; severe mutations={bool(mutations)}

Historical PR-CY follow-up:
72,065 tokens

Actual PR-DA follow-up:
{total_tokens if CALLS else 'no live call'} tokens

PR-DA decision:
{decision}

Recommended next step:
Review the failing reduced-context predicate and the live validation trace before any further projection or validator change.
"""
    review_path = ROOT / "handoff" / "CURRENT_REVIEW.md"
    try:
        write_text(review_path, current)
    except OSError:
        temp_path = review_path.with_suffix(".md.pr_da_tmp")
        write_text(temp_path, current)
        temp_path.replace(review_path)
    manifest = {
        "pr": "PR-DA",
        "mode": "FOLLOW-UP EFFICIENCY VERIFICATION",
        "decision": decision,
        "artifacts": [
            str(path.relative_to(ROOT))
            for path in sorted(OUT.glob("PR-DA_*"))
        ] + [str((OUT / "changed_files.txt").relative_to(ROOT))],
        "provider_requests": len(CALLS),
        "total_tokens": total_tokens,
        "full_context_serialized_bytes": full.get("serialized_prompt_bytes"),
        "hypothetical_reduced_serialized_bytes": reduced.get("serialized_prompt_bytes"),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    save_json(ROOT / "handoff" / "REVIEW_MANIFEST.json", manifest)
    zip_path = ROOT / "handoff" / "CURRENT_REVIEW.zip"
    if zip_path.exists():
        zip_path.unlink()
    import zipfile

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / "handoff" / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        archive.write(ROOT / "handoff" / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for path in sorted(OUT.glob("PR-DA_*")):
            archive.write(path, path.name)
        archive.write(OUT / "changed_files.txt", "changed_files.txt")
        for path in sorted(EVIDENCE.rglob("*")):
            if path.is_file() and path.suffix in {".json", ".md", ".txt", ".csv"} and "isolated_session" not in path.parts and "reconstructed_backup" not in path.parts:
                archive.write(path, str(path.relative_to(OUT)))
    save_json(EVIDENCE / "run_finished.json", {"decision": decision, "halt": HALT, "calls": len(CALLS), "tokens": total_tokens})
    status(f"DONE {decision}")


if __name__ == "__main__":
    main()
