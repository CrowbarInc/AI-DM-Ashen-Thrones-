#!/usr/bin/env python3
"""PR-BX narration-only envelope micro-live gate.

Measurement only. Same P1/P2/P3 fixtures and player wording as the PR-BV
live gate. No prompt edits, no validator changes, no selector changes, no
repairs, and no extra semantic probes. Production retries are recorded and
are not suppressed. One infrastructure rerun is allowed only when a probe
fails before a meaningful model generation; the first execution is preserved.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "evidence"
PRIOR = ROOT / "artifacts" / "pr_bv_turn_operation_projection_micro_live" / "evidence"
CALLS: list[dict] = []
CURRENT = {"probe": None, "kind": "other", "retry_attempt": 0}

PROBES = (
    {
        "id": "P1",
        "scene": "chapel",
        "player": (
            "I examine the split wooden yoke and the torn leather hanger closely. "
            "What does this damage suggest?"
        ),
    },
    {
        "id": "P2",
        "scene": "baker",
        "player": "Baker, which loaf do you usually keep for yourself?",
    },
    {
        "id": "P3",
        "scene": "chapel",
        "player": (
            "Looking at the split wooden yoke and the torn leather hanger, "
            "maybe someone cut it deliberately. Does that fit what I'm seeing?"
        ),
    },
)
EXPECTED_ENVELOPE = {
    "P1": "structured_realization",
    "P2": "narration_only",
    "P3": "structured_realization",
}


def save(name: str, value) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    if "sk-" in text:
        text = text.replace("sk-", "sk-REDACTED-")
    path.write_text(text, encoding="utf-8")


def status(text: str) -> None:
    (OUT / "status.txt").write_text(text, encoding="utf-8")
    print(text, flush=True)


import openai.resources.responses as responses_module
from game.gm import NARRATION_ONLY_RESPONSE_CONTRACT, NARRATION_ONLY_SYSTEM_PROMPT, _safe_json
from game.gm_resolution_decision import select_provider_response_envelope

Responses = responses_module.Responses
original_create = Responses.create


def _usage(dump: dict) -> dict:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    details_in = usage.get("input_tokens_details")
    details_out = usage.get("output_tokens_details")
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "input_tokens_details": details_in if isinstance(details_in, dict) else details_in,
        "output_tokens_details": details_out if isinstance(details_out, dict) else details_out,
    }


def _contract_view(provider_input) -> dict:
    system = ""
    if isinstance(provider_input, list) and provider_input and isinstance(provider_input[0], dict):
        system = str(provider_input[0].get("content") or "")
    narration = NARRATION_ONLY_RESPONSE_CONTRACT in system
    return {
        "provider_response_contract": "narration_only" if narration else "structured_realization",
        "exact_narration_only_contract_present": narration,
        "declared_claims_in_system_prompt": "declared_claims" in system,
        "system_prompt_chars": len(system),
        "response_contract_tail": system[-500:],
    }


def _extract_request(input_value) -> dict:
    texts: list[str] = []
    roles: list[str] = []
    if isinstance(input_value, list):
        for message in input_value:
            if not isinstance(message, dict):
                continue
            roles.append(str(message.get("role") or ""))
            texts.append(str(message.get("content") or ""))
    elif isinstance(input_value, str):
        texts.append(input_value)
    blob = "\n".join(texts)
    recipe = None
    for text in texts:
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("decision_facing_answer_recipe"), dict):
            recipe = parsed["decision_facing_answer_recipe"]
            break
    serialized = json.dumps(input_value, ensure_ascii=False, default=str)
    contract = _contract_view(input_value)
    return {
        "roles": roles,
        "input_chars": len(serialized),
        "recipe_present": recipe is not None,
        "recipe": recipe,
        "retry_context_present": "AUTHORITATIVE RETRY CONTEXT" in blob,
        "provider_input": input_value,
        "contract": contract,
    }


def observe_create(self, *args, **kwargs):
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    request = _extract_request(kwargs.get("input"))
    schema_keys = sorted(key for key in kwargs if key not in {"input", "model"})
    row = {
        "index": len(CALLS) + 1,
        "probe": CURRENT.get("probe"),
        "kind": CURRENT.get("kind"),
        "retry_attempt": kwargs.get("retry_attempt", CURRENT.get("retry_attempt", 0)),
        "model": kwargs.get("model"),
        "started": started_at,
        "input_chars": request["input_chars"],
        "roles": request["roles"],
        "recipe_present": request["recipe_present"],
        "retry_context_present": request["retry_context_present"],
        "provider_response_contract": request["contract"]["provider_response_contract"],
        "exact_narration_only_contract_present": request["contract"]["exact_narration_only_contract_present"],
        "declared_claims_in_system_prompt": request["contract"]["declared_claims_in_system_prompt"],
        "create_kwarg_keys": schema_keys,
        "api_response_schema_present": any(
            key in kwargs for key in ("response_format", "text", "tools", "tool_choice")
        ),
    }
    CALLS.append(row)
    probe = str(CURRENT.get("probe") or "startup")
    attempt = int(row["retry_attempt"] or 0) + 1
    prefix = OUT / probe
    prefix.mkdir(parents=True, exist_ok=True)
    save(
        f"{probe}/provider_request_attempt_{row['kind']}_{attempt}.json",
        {
            "measurements": {
                k: request[k] for k in ("roles", "input_chars", "recipe_present", "retry_context_present")
            },
            "contract": request["contract"],
            "create_kwarg_keys": schema_keys,
            "api_response_schema_present": row["api_response_schema_present"],
            "decision_facing_answer_recipe": request["recipe"],
            "provider_input": request["provider_input"],
        },
    )
    save("model_calls.json", [{k: v for k, v in call.items() if k != "provider_input"} for call in CALLS])
    try:
        result = original_create(self, *args, **kwargs)
        dump = result.model_dump(mode="json")
        row["raw_output"] = result.output_text
        row["response_id"] = dump.get("id")
        row["response_model"] = dump.get("model")
        row["usage"] = _usage(dump)
        row["status"] = dump.get("status")
        row["meaningful_generation"] = bool(result.output_text) and bool(row["usage"])
        return result
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["meaningful_generation"] = False
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save("model_calls.json", [{k: v for k, v in call.items()} for call in CALLS])


Responses.create = observe_create

from fastapi.testclient import TestClient
from game import storage
import game.api as api
import game.semantic_interpreter as interpreter
import game.api_upstream_preflight as preflight
import game.live_resolution as live_resolution
from game.defaults import (
    default_scene,
    default_session,
    default_world,
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
)
from game.gm_resolution_decision import build_decision_facing_answer_recipe


def phase0_prelive() -> dict:
    """Confirm selector, contract, and normalization before any API call."""
    rows = []
    failures: list[str] = []
    for probe, expected in EXPECTED_ENVELOPE.items():
        decision = json.loads((PRIOR / probe / "gm_resolution_decision.json").read_text(encoding="utf-8"))
        contract = json.loads((PRIOR / probe / "resolution_contract.json").read_text(encoding="utf-8"))
        selected = select_provider_response_envelope(decision, contract)
        row = {
            "probe": probe,
            "expected_envelope": expected,
            "selected_envelope": selected.get("selected_envelope"),
            "response_operation": selected.get("response_operation"),
            "declaration_expectation": selected.get("declaration_expectation"),
            "consequential_realization_required": selected.get("consequential_realization_required"),
            "declaration_channel_exposed": selected.get("declaration_channel_exposed"),
            "projection_only": selected.get("projection_only"),
            "authority_owner": selected.get("authority_owner"),
            "reason": selected.get("reason"),
        }
        rows.append(row)
        if row["selected_envelope"] != expected:
            failures.append(f"{probe} envelope {row['selected_envelope']} != {expected}")
        if row["projection_only"] is not True or row["authority_owner"] != "gm_resolution_decision":
            failures.append(f"{probe} selector is not a projection of gm_resolution_decision")
    if rows[0]["response_operation"] != "bounded_interpretation":
        failures.append("P1 response_operation drifted")
    if rows[1]["response_operation"] != "incidental_dialogue":
        failures.append("P2 response_operation drifted")
    if rows[1]["declaration_expectation"] != "reply_not_required":
        failures.append("P2 declaration_expectation drifted")
    if rows[1]["consequential_realization_required"] not in (False, None) and rows[1]["consequential_realization_required"]:
        failures.append("P2 consequential realization required")
    if rows[1]["declaration_channel_exposed"] is not False:
        failures.append("P2 declaration channel exposed by selector")
    if rows[2]["response_operation"] != "player_hypothesis_discussion":
        failures.append("P3 response_operation drifted")
    contract_ok = (
        '{"narration": "player-facing response"}' in NARRATION_ONLY_RESPONSE_CONTRACT
        and "declared_claims" not in NARRATION_ONLY_RESPONSE_CONTRACT
        and "declared_claims" not in NARRATION_ONLY_SYSTEM_PROMPT
    )
    if not contract_ok:
        failures.append("narration-only response contract is not the single-field shape")
    sample = '{"narration": "The baker glances at the cooling rack."}'
    parsed = _safe_json(sample, require_structured_claims=True, provider_response_contract="narration_only")
    envelope = (parsed.get("metadata") or {}).get("realization_envelope") or {}
    normalization_ok = (
        envelope.get("declared_claims") == []
        and envelope.get("normalized_empty_declarations") is True
        and envelope.get("declaration_authorship") is False
        and parsed.get("player_facing_text") == "The baker glances at the cooling rack."
    )
    if not normalization_ok:
        failures.append("narration-only normalization did not yield canonical empty declared_claims")
    smuggled = _safe_json(
        '{"declared_claims": [], "narration": "No."}',
        require_structured_claims=True,
        provider_response_contract="narration_only",
    )
    if not (smuggled.get("metadata") or {}).get("structured_contract_failure"):
        failures.append("narration-only path accepted a smuggled declaration field")
    report = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_decisions": "artifacts/pr_bv_turn_operation_projection_micro_live/evidence",
        "selection": rows,
        "narration_only_response_contract": NARRATION_ONLY_RESPONSE_CONTRACT,
        "declared_claims_in_narration_only_system_prompt": "declared_claims" in NARRATION_ONLY_SYSTEM_PROMPT,
        "normalization": {
            "declared_claims": envelope.get("declared_claims"),
            "normalized_empty_declarations": envelope.get("normalized_empty_declarations"),
            "declaration_authorship": envelope.get("declaration_authorship"),
            "player_facing_text": parsed.get("player_facing_text"),
        },
        "smuggled_declaration_rejected": bool((smuggled.get("metadata") or {}).get("structured_contract_failure")),
        "failures": failures,
        "passed": not failures,
    }
    save("phase0_prelive.json", report)
    return report


def temporal_slice(session: dict | None) -> dict:
    session = session or {}
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    provenance = session.get("narration_temporal_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return {
        "gm_inferences": provenance.get("gm_inferences") or [],
        "player_hypotheses": provenance.get("player_hypotheses") or [],
        "accepted_incidentals": provenance.get("accepted_incidentals") or [],
        "rejected_consequential": provenance.get("rejected_consequential") or [],
        "active_claim": focus.get("active_claim"),
        "discourse_focus": focus,
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": session.get("active_scene_id"),
    }


def scene_slice(scene_doc: dict | None) -> dict:
    scene = (scene_doc or {}).get("scene") if isinstance(scene_doc, dict) else {}
    if not isinstance(scene, dict):
        scene = {}
    return {
        "id": scene.get("id"),
        "location": scene.get("location"),
        "summary": scene.get("summary"),
        "visible_facts": list(scene.get("visible_facts") or []),
        "hidden_facts": list(scene.get("hidden_facts") or []),
        "discoverable_clues": list(scene.get("discoverable_clues") or []),
        "exits": list(scene.get("exits") or []),
        "enemies": list(scene.get("enemies") or []),
        "actions": list(scene.get("actions") or []),
        "interactables": list(scene.get("interactables") or []),
        "addressables": list(scene.get("addressables") or []),
    }


def world_slice(world: dict | None) -> dict:
    world = world or {}
    return {
        "npcs": world.get("npcs") or [],
        "factions": world.get("factions") or [],
        "clues": world.get("clues") or {},
        "world_flags": world.get("world_flags") or [],
        "assets": world.get("assets") or [],
    }


def snapshot() -> dict:
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene(session["active_scene_id"])
    return {
        "temporal": temporal_slice(session),
        "scene": scene_slice(scene),
        "world": world_slice(world),
    }


def wrap(fn, kind):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(kind=kind, retry_attempt=kwargs.get("retry_attempt", 0))
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)

    return observed


DECISIONS: list[dict] = []
original_attach = live_resolution.attach_gm_resolution_decision


def observe_decision(resolution, **kwargs):
    result = original_attach(resolution, **kwargs)
    metadata = resolution.get("metadata") if isinstance(resolution, dict) else {}
    contract = metadata.get("resolution_contract") if isinstance(metadata, dict) else {}
    decision = metadata.get("gm_resolution_decision") if isinstance(metadata, dict) else {}
    recipe = build_decision_facing_answer_recipe(
        decision if isinstance(decision, dict) else None,
        contract if isinstance(contract, dict) else None,
    )
    selected = select_provider_response_envelope(
        decision if isinstance(decision, dict) else None,
        contract if isinstance(contract, dict) else None,
    )
    row = {
        "index": len(DECISIONS) + 1,
        "probe": CURRENT.get("probe"),
        "contract": contract if isinstance(contract, dict) else {},
        "decision": decision if isinstance(decision, dict) else {},
        "decision_facing_answer_recipe": recipe,
        "envelope_selection": selected,
    }
    DECISIONS.append(row)
    return result


live_resolution.attach_gm_resolution_decision = observe_decision
api.call_gpt = wrap(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap(interpreter._invoke_interpretation_model, "interpretation")
api.run_upstream_api_preflight = wrap(api.run_upstream_api_preflight, "preflight")
preflight.run_upstream_api_preflight = api.run_upstream_api_preflight


def point_storage(probe_id: str) -> None:
    base = OUT / probe_id / "isolated"
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


def seed(probe_id: str, scene_kind: str) -> None:
    point_storage(probe_id)
    for base_sid in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(base_sid), default_scene(base_sid))
    if scene_kind == "chapel":
        sid = "chapel_belfry"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Chapel belfry",
            summary="A bronze bell hangs from a timber frame.",
            visible_facts=[
                "The bell's wooden yoke is split.",
                "The bell's leather hanger is torn.",
            ],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            interactables=[
                {
                    "id": "chapel_bell",
                    "label": "chapel bell",
                    "aliases": ["bell", "wooden yoke", "yoke", "leather hanger", "hanger"],
                }
            ],
        )
        world = default_world()
        world["npcs"] = []
    else:
        sid = "bread_stall"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Bread stall",
            summary="A baker stands at a bread stall.",
            visible_facts=["A baker stands beside loaves at a bread stall."],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            addressables=[
                {
                    "id": "baker",
                    "name": "Baker",
                    "scene_id": sid,
                    "kind": "npc",
                    "addressable": True,
                    "address_priority": 0,
                    "address_roles": ["baker", "vendor"],
                    "aliases": ["baker"],
                }
            ],
            interactables=[],
        )
        world = default_world()
        world["npcs"] = [
            {
                "id": "baker",
                "name": "Baker",
                "location": sid,
                "topics": [],
            }
        ]
    session = default_session()
    session.update(active_scene_id=sid, visited_scene_ids=[sid], turn_counter=1)
    for path, value in [
        (storage.WORLD_PATH, world),
        (storage.SESSION_PATH, session),
        (storage.CAMPAIGN_PATH, default_campaign()),
        (storage.CHARACTER_PATH, default_character()),
        (storage.COMBAT_PATH, default_combat()),
        (storage.CONDITIONS_PATH, default_conditions()),
        (storage.scene_path(sid), scene),
    ]:
        storage._save_json(path, value)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _faction_clock_only(before_rows, after_rows) -> bool:
    if not isinstance(before_rows, list) or not isinstance(after_rows, list):
        return False
    if len(before_rows) != len(after_rows):
        return False
    for before, after in zip(before_rows, after_rows):
        if not isinstance(before, dict) or not isinstance(after, dict):
            return False
        if before.get("id") != after.get("id"):
            return False
        for key, value in before.items():
            if key in {"pressure", "agenda_progress"}:
                continue
            if after.get(key) != value:
                return False
        try:
            if int(after.get("pressure") or 0) - int(before.get("pressure") or 0) != 1:
                return False
            if int(after.get("agenda_progress") or 0) - int(before.get("agenda_progress") or 0) != 1:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _promoted(row: dict) -> bool:
    status_value = str(row.get("epistemic_status") or "")
    authority = str(row.get("authority") or "")
    provenance = str(row.get("provenance") or "")
    return status_value == "established" or authority == "world_truth" or provenance == "authored_world_fact"


def authority_problems(before: dict, after: dict) -> list[str]:
    problems: list[str] = []
    for key in (
        "visible_facts",
        "hidden_facts",
        "discoverable_clues",
        "summary",
        "exits",
        "enemies",
        "actions",
        "interactables",
    ):
        if before["scene"].get(key) != after["scene"].get(key):
            problems.append(f"scene.{key}_changed")
    before_world = dict(before["world"])
    after_world = dict(after["world"])
    if not _faction_clock_only(before_world.get("factions"), after_world.get("factions")):
        if before_world.get("factions") != after_world.get("factions"):
            problems.append("factions_changed_beyond_default_clock")
    before_world.pop("factions", None)
    after_world.pop("factions", None)
    if before_world != after_world:
        problems.append("world_authoritative_slice_changed")
    temporal = after["temporal"]
    visible = " ".join(str(item) for item in after["scene"].get("visible_facts") or [])
    for bucket in ("gm_inferences", "player_hypotheses", "accepted_incidentals"):
        for row in temporal.get(bucket) or []:
            if isinstance(row, dict) and _promoted(row):
                problems.append(
                    f"{bucket}_promoted:{row.get('epistemic_status')}:{row.get('authority')}:{row.get('provenance')}"
                )
    for row in temporal.get("rejected_consequential") or []:
        text = str(row.get("text") or "").strip() if isinstance(row, dict) else ""
        if text and text in visible:
            problems.append("rejected_consequential_entered_visible_facts")
    return problems


def c18_report(gm: dict) -> dict:
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    accepted_text = accepted.get("text")
    emitted = gm.get("player_facing_text")
    debug = meta.get("emission_debug") if isinstance(meta.get("emission_debug"), dict) else {}
    equality = debug.get("accepted_emitted_equality") if isinstance(debug.get("accepted_emitted_equality"), dict) else {}
    exact = accepted_text == emitted and accepted_text is not None
    mutation_blocked = bool(equality.get("mutation_blocked"))
    envelope = meta.get("realization_envelope") if isinstance(meta.get("realization_envelope"), dict) else {}
    return {
        "accepted": accepted_text,
        "sealed": accepted_text,
        "emitted": emitted,
        "exact_equal": bool(exact) and not mutation_blocked,
        "string_equal": bool(exact),
        "mutation_blocked": mutation_blocked,
        "equality_debug": equality,
        "provenance": accepted.get("provenance"),
        "attempt": accepted.get("attempt"),
        "accepted_realization_envelope": envelope,
    }


def _structural_shape(raw: str) -> dict:
    try:
        parsed = json.loads(raw or "")
    except json.JSONDecodeError as exc:
        return {"json_object": False, "error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(parsed, dict):
        return {"json_object": False, "python_type": type(parsed).__name__}
    return {"json_object": True, "keys": sorted(str(key) for key in parsed)}


def parse_generation(raw: str, contract: str) -> dict:
    shape = _structural_shape(raw)
    try:
        parsed = _safe_json(raw or "", require_structured_claims=True, provider_response_contract=contract)
    except Exception as exc:
        return {"parse_error": f"{type(exc).__name__}: {exc}", "raw_output": raw, "structural_shape": shape}
    if not isinstance(parsed, dict):
        return {"parse_error": "non_object", "raw_output": raw, "structural_shape": shape}
    metadata = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
    envelope = metadata.get("realization_envelope") if isinstance(metadata.get("realization_envelope"), dict) else {}
    return {
        "player_facing_text": parsed.get("player_facing_text"),
        "declared_claims": envelope.get("declared_claims"),
        "normalized_empty_declarations": envelope.get("normalized_empty_declarations"),
        "declaration_authorship": envelope.get("declaration_authorship"),
        "structured_contract_failure": metadata.get("structured_contract_failure"),
        "structured_contract_reason": metadata.get("structured_contract_reason"),
        "provider_response_contract": metadata.get("provider_response_contract"),
        "tags": parsed.get("tags"),
        "metadata_keys": sorted(metadata.keys()),
        "structural_shape": shape,
        "raw_output": raw,
    }


def player_facing_leakage(text: str | None) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    lowered = text.lower()
    hits = []
    for marker in (
        "declared_claims",
        "declaration_mode",
        "semantic_identity",
        "gm_resolution_decision",
        "narration-only response contract",
        "structured_contract",
        "provenance",
        "validator",
        "unauthorized_",
        "source_claim_id",
    ):
        if marker in lowered:
            hits.append(marker)
    stripped = text.strip()
    if stripped.startswith("{") or '"narration"' in text or stripped.endswith("}"):
        hits.append("json_structure")
    return hits


def compact_call(call: dict) -> dict:
    usage = call.get("usage") or {}
    return {
        "index": call.get("index"),
        "kind": call.get("kind"),
        "retry_attempt": call.get("retry_attempt"),
        "model": call.get("response_model") or call.get("model"),
        "response_id": call.get("response_id"),
        "input_chars": call.get("input_chars"),
        "recipe_present": call.get("recipe_present"),
        "retry_context_present": call.get("retry_context_present"),
        "provider_response_contract": call.get("provider_response_contract"),
        "exact_narration_only_contract_present": call.get("exact_narration_only_contract_present"),
        "declared_claims_in_system_prompt": call.get("declared_claims_in_system_prompt"),
        "api_response_schema_present": call.get("api_response_schema_present"),
        "create_kwarg_keys": call.get("create_kwarg_keys"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "latency_seconds": call.get("latency_seconds"),
        "status": call.get("status"),
        "error": call.get("error"),
        "meaningful_generation": call.get("meaningful_generation"),
    }


def _token_sum(calls: list[dict], field: str) -> int:
    total = 0
    for call in calls:
        value = (call.get("usage") or {}).get(field)
        if isinstance(value, int):
            total += value
    return total


def run_probe(client: TestClient, spec: dict, *, infrastructure_rerun: bool) -> dict:
    probe_id = spec["id"]
    seed(probe_id, spec["scene"])
    before = snapshot()
    save(f"{probe_id}/state_before.json", before)
    decisions_at = len(DECISIONS)
    calls_at = len(CALLS)
    CURRENT["probe"] = probe_id
    status(f"RUNNING {probe_id}{' infrastructure_rerun' if infrastructure_rerun else ''}")
    error = None
    payload: dict = {}
    http_status = None
    try:
        response = client.post("/api/chat", json={"text": spec["player"]})
        http_status = response.status_code
        payload = response.json()
    except Exception:
        error = traceback.format_exc()
        payload = {}
    after = snapshot()
    calls = CALLS[calls_at:]
    decisions = DECISIONS[decisions_at:]
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    c18 = c18_report(gm)
    problems = authority_problems(before, after)
    generations = [call for call in calls if call.get("kind") == "generation"]
    parsed = []
    for index, call in enumerate(generations, start=1):
        contract = str(call.get("provider_response_contract") or "structured_realization")
        parsed_row = parse_generation(str(call.get("raw_output") or ""), contract)
        parsed.append(parsed_row)
        save(
            f"{probe_id}/raw_generation_attempt_{index}.json",
            {
                "response_id": call.get("response_id"),
                "model": call.get("response_model") or call.get("model"),
                "usage": call.get("usage"),
                "latency_seconds": call.get("latency_seconds"),
                "input_chars": call.get("input_chars"),
                "recipe_present": call.get("recipe_present"),
                "retry_context_present": call.get("retry_context_present"),
                "provider_response_contract": contract,
                "declared_claims_in_system_prompt": call.get("declared_claims_in_system_prompt"),
                "api_response_schema_present": call.get("api_response_schema_present"),
                "error": call.get("error"),
                "parsed": parsed_row,
            },
        )
    first_decision = decisions[0] if decisions else {}
    recipe = first_decision.get("decision_facing_answer_recipe")
    selected = first_decision.get("envelope_selection") if isinstance(first_decision.get("envelope_selection"), dict) else {}
    save(f"{probe_id}/resolution_contract.json", first_decision.get("contract") or {})
    save(f"{probe_id}/gm_resolution_decision.json", first_decision.get("decision") or {})
    save(f"{probe_id}/decision_facing_answer_recipe.json", recipe or {})
    save(f"{probe_id}/envelope_selection.json", selected)
    save(f"{probe_id}/state_after.json", after)
    save(f"{probe_id}/api_response.json", payload)
    validation = {
        "attempt_1": review.get("attempt_1"),
        "attempt_2": review.get("attempt_2"),
        "retry_context": review.get("retry_context"),
        "acceptance": review.get("acceptance"),
        "hard_validation_attempt_1": meta.get("hard_validation_attempt_1"),
        "hard_validation_attempt_2": meta.get("hard_validation_attempt_2"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "regeneration_invoked": meta.get("regeneration_invoked"),
        "provider_response_contract": meta.get("provider_response_contract"),
    }
    save(f"{probe_id}/validation.json", validation)
    save(f"{probe_id}/c18.json", c18)
    accepted_envelope = c18.get("accepted_realization_envelope") or {}
    normalization = {
        "application_realization_envelope": accepted_envelope,
        "parser_attempts": [
            {
                "attempt": index,
                "provider_response_contract": row.get("provider_response_contract"),
                "structural_shape": row.get("structural_shape"),
                "declared_claims": row.get("declared_claims"),
                "normalized_empty_declarations": row.get("normalized_empty_declarations"),
                "declaration_authorship": row.get("declaration_authorship"),
                "structured_contract_failure": row.get("structured_contract_failure"),
                "structured_contract_reason": row.get("structured_contract_reason"),
                "player_facing_text": row.get("player_facing_text"),
            }
            for index, row in enumerate(parsed, start=1)
        ],
    }
    save(f"{probe_id}/normalization.json", normalization)
    upstream = bool(meta.get("upstream_api_error")) if isinstance(meta, dict) else False
    meaningful = any(bool(call.get("meaningful_generation")) for call in generations)
    generation_contracts = [str(call.get("provider_response_contract") or "") for call in generations]
    emitted = c18.get("emitted")
    leakage = player_facing_leakage(emitted if isinstance(emitted, str) else None)
    claims = accepted_envelope.get("declared_claims")
    authored = bool(accepted_envelope.get("declaration_authorship")) or (
        isinstance(claims, list) and any(isinstance(item, dict) and item for item in claims)
    )
    digest = {
        "probe": probe_id,
        "player": spec["player"],
        "scene": spec["scene"],
        "infrastructure_rerun": infrastructure_rerun,
        "http_status": http_status,
        "error": error,
        "upstream_api_error": meta.get("upstream_api_error") if isinstance(meta, dict) else None,
        "meaningful_model_generation": meaningful and not upstream,
        "emitted": emitted,
        "sealed": c18["sealed"],
        "accepted": c18["accepted"],
        "c18_exact_equal": c18["exact_equal"],
        "c18_mutation_blocked": c18["mutation_blocked"],
        "provenance": c18["provenance"],
        "attempt": c18["attempt"],
        "acceptance": review.get("acceptance"),
        "selected_envelope": selected.get("selected_envelope"),
        "response_operation": selected.get("response_operation"),
        "declaration_expectation": selected.get("declaration_expectation"),
        "consequential_realization_required": selected.get("consequential_realization_required"),
        "declaration_channel_exposed": selected.get("declaration_channel_exposed"),
        "selector_projection_only": selected.get("projection_only"),
        "selector_authority_owner": selected.get("authority_owner"),
        "selector_reason": selected.get("reason"),
        "provider_response_contracts": generation_contracts,
        "declared_claims_in_any_generation_system_prompt": any(
            bool(call.get("declared_claims_in_system_prompt")) for call in generations
        ),
        "api_response_schema_present": any(bool(call.get("api_response_schema_present")) for call in generations),
        "normalized_declared_claims": accepted_envelope.get("declared_claims"),
        "normalized_empty_declarations": accepted_envelope.get("normalized_empty_declarations"),
        "declaration_authorship": accepted_envelope.get("declaration_authorship"),
        "accepted_model_authored_declarations": authored,
        "provider_attempts": len(generations),
        "retry": len(generations) > 1 or bool(meta.get("regeneration_invoked")),
        "input_tokens": _token_sum(generations, "input_tokens"),
        "output_tokens": _token_sum(generations, "output_tokens"),
        "total_tokens": _token_sum(generations, "total_tokens"),
        "initial_player_facing_text": (parsed[0].get("player_facing_text") if parsed else None),
        "initial_structural_shape": (parsed[0].get("structural_shape") if parsed else None),
        "initial_declared_claims": (parsed[0].get("declared_claims") if parsed else None),
        "initial_contract_failure": (parsed[0].get("structured_contract_failure") if parsed else None),
        "initial_contract_reason": (parsed[0].get("structured_contract_reason") if parsed else None),
        "retry_player_facing_text": (parsed[1].get("player_facing_text") if len(parsed) > 1 else None),
        "retry_structural_shape": (parsed[1].get("structural_shape") if len(parsed) > 1 else None),
        "retry_declared_claims": (parsed[1].get("declared_claims") if len(parsed) > 1 else None),
        "validation_attempt_1_reasons": (
            (review.get("attempt_1") or {}).get("reasons") if isinstance(review.get("attempt_1"), dict) else None
        ),
        "validation_attempt_2_reasons": (
            (review.get("attempt_2") or {}).get("reasons") if isinstance(review.get("attempt_2"), dict) else None
        ),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "player_facing_leakage": leakage,
        "authority_problems": problems,
        "temporal_after": after["temporal"],
        "calls": [compact_call(call) for call in calls],
        "contract_id": (first_decision.get("contract") or {}).get("contract_id")
        if isinstance(first_decision.get("contract"), dict)
        else None,
        "recipe_schema": (recipe or {}).get("schema") if isinstance(recipe, dict) else None,
        "recipe_turn_operation": (recipe or {}).get("turn_operation") if isinstance(recipe, dict) else None,
    }
    save(f"{probe_id}/digest.json", digest)
    return digest


def _already_recorded(probe_id: str) -> dict | None:
    path = OUT / probe_id / "digest.json"
    if not path.exists():
        return None
    digest = json.loads(path.read_text(encoding="utf-8"))
    if digest.get("meaningful_model_generation") and not digest.get("infrastructure_rerun"):
        return digest
    return None


def stop_reason(digest: dict) -> str | None:
    probe = str(digest.get("probe") or "")
    envelope = digest.get("selected_envelope")
    if probe == "P2" and envelope != "narration_only":
        return f"P2 selected {envelope} unexpectedly"
    if probe in {"P1", "P3"} and envelope == "narration_only":
        return f"{probe} selected narration_only unexpectedly"
    if digest.get("consequential_realization_required") and envelope == "narration_only":
        return f"{probe} consequential realization entered narration_only"
    if envelope == "narration_only" and digest.get("accepted_model_authored_declarations"):
        return f"{probe} narration-only path accepted model-authored declarations"
    if digest.get("meaningful_model_generation") and not digest.get("c18_exact_equal"):
        return f"C18 divergence on {probe}"
    if digest.get("authority_problems"):
        return f"unauthorized state/provenance on {probe}: {digest.get('authority_problems')}"
    models = {
        str(call.get("model") or "")
        for call in digest.get("calls") or []
        if call.get("kind") == "generation" and call.get("model")
    }
    if models and not all("gpt-4.1-mini" in model for model in models):
        return f"model family mismatch on {probe}: {sorted(models)}"
    return None


def preserve_probe(probe_id: str, label: str) -> None:
    src = OUT / probe_id
    dest = OUT / f"{probe_id}_{label}"
    if dest.exists():
        shutil.rmtree(dest)
    if src.exists():
        shutil.copytree(src, dest)


def main(prelive_only: bool = False) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prelive = phase0_prelive()
    if not prelive["passed"]:
        status("PHASE0 FAIL " + "; ".join(prelive["failures"]))
        return 3
    status("PHASE0 PASS")
    if prelive_only:
        status("PRELIVE ONLY")
        return 0
    if not (OUT / "run_started.json").exists():
        save(
            "run_started.json",
            {
                "utc": datetime.now(timezone.utc).isoformat(),
                "probes": [row["id"] for row in PROBES],
                "note": "Same P1/P2/P3 fixtures and wording as PR-BV. P3 uses a fresh chapel scene.",
                "phase0_passed": True,
            },
        )
    completed: list[dict] = []
    halt = None
    status("STARTING")
    with TestClient(api.app) as client:
        save("preflight.json", preflight.get_latest_upstream_api_preflight())
        for spec in PROBES:
            recorded = _already_recorded(spec["id"])
            if recorded is not None:
                status(f"SKIP {spec['id']} already recorded")
                completed.append(recorded)
                save("completed.json", completed)
                continue
            digest = run_probe(client, spec, infrastructure_rerun=False)
            completed.append(digest)
            save("completed.json", completed)
            if not digest["meaningful_model_generation"]:
                preserve_probe(spec["id"], "infrastructure_attempt_1")
                status(f"INFRASTRUCTURE {spec['id']} — one rerun, first execution preserved")
                digest = run_probe(client, spec, infrastructure_rerun=True)
                completed.append(digest)
                save("completed.json", completed)
                if not digest["meaningful_model_generation"]:
                    halt = f"infrastructure failure on {spec['id']} after one rerun"
                    break
            reason = stop_reason(digest)
            if reason:
                halt = reason
                status(f"HALT {halt}")
                break
            status(f"DONE {spec['id']}")
    save(
        "run_finished.json",
        {
            "halt": halt,
            "probes_recorded": [row.get("probe") for row in completed],
            "model_calls": len(CALLS),
            "gameplay_generations": sum(1 for call in CALLS if call.get("kind") == "generation"),
        },
    )
    status(f"FINISHED halt={halt}")
    return 0 if halt is None else 2


if __name__ == "__main__":
    raise SystemExit(main(prelive_only="--prelive-only" in sys.argv))
