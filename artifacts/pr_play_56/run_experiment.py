"""PR-PLAY-56 live quarantine experiment.

Resolves existing investigation scenarios, then asks the existing expression
adapter for one quarantined prelude. The PR-PLAY-55 validator is called as it
stands. This script does not edit it, does not edit campaign fixtures, and
does not retry by clearing the quarantine stop flag.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import socket
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_56"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
# The quarantine module refuses a seventh live request. Stay inside that
# ceiling. The cycle ceiling is 8; this path cannot reach it without editing
# the hook.
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "6"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "11300"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "700"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "12000"

LEDGER = OUT / "provider_usage.jsonl"
EVIDENCE = OUT / "hook_evidence"
SOURCE = OUT / "frozen_validator"
RAW: list[dict] = []
CREATE_CALLS = 0
EXPERIMENT_REQUEST_CEILING = 6
EXPERIMENT_OUTPUT_CEILING = 700
EXPERIMENT_TOTAL_CEILING = 12000

CANARIES = (
    "CANARY_UNDISCOVERED_CLUE",
    "CANARY_GM_NOTE",
    "CANARY_NPC_MOTIVE",
    "CANARY_HIDDEN_DESTINATION",
    "CANARY_QUEST_TWIST",
    "CANARY_MECHANICAL_ID",
    "CANARY_UNRELATED_WORLD",
)
ROUTE = "The missing patrol was last seen taking the northwest mud track past the crates."
PRINTS = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
VALIDATOR_FILES = (
    "game/consequential_narration_validation.py",
    "game/anchored_investigation_narration.py",
    "game/immutable_valid_response.py",
    "game/quarantined_investigation_narration.py",
    "game/offline_investigation_projection.py",
    "game/expressive_dialogue.py",
    "game/provider_budget.py",
)
PRIMARY_VALIDATOR = "game/consequential_narration_validation.py"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def secret_blobs() -> list[bytes]:
    blobs = []
    for name in ("OPENAI_API_KEY", "API_KEY", "OPENAI_TOKEN"):
        value = os.environ.get(name, "").strip()
        if len(value) > 8:
            blobs.append(value.encode())
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if len(value) > 8 and any(part in key.lower() for part in ("key", "secret", "token", "password")):
                blobs.append(value.encode())
    return blobs


def redact(value):
    if isinstance(value, str):
        text = value
        for blob in secret_blobs():
            text = text.replace(blob.decode(), "[REDACTED]")
        return text
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def write_json(name: str, value) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(redact(value), indent=2, ensure_ascii=False) + "\n"
    for blob in secret_blobs():
        if blob.decode() in text:
            raise RuntimeError("credential leaked into " + name)
    (OUT / name).write_text(text, encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes(paths: tuple[str, ...]) -> dict:
    rows = {}
    for relative in paths:
        path = ROOT / relative
        rows[relative] = {
            "exists": path.exists(),
            "sha256": sha(path) if path.exists() else None,
            "bytes": path.stat().st_size if path.exists() else None,
        }
    return rows


def freeze_validator() -> dict:
    SOURCE.mkdir(parents=True, exist_ok=True)
    recorded = file_hashes(VALIDATOR_FILES)
    primary = ROOT / PRIMARY_VALIDATOR
    frozen = SOURCE / primary.name
    frozen.write_bytes(primary.read_bytes())
    recorded["frozen_copy"] = {
        "path": frozen.relative_to(ROOT).as_posix(),
        "sha256": sha(frozen),
        "matches_primary": sha(frozen) == recorded[PRIMARY_VALIDATOR]["sha256"],
    }
    write_json("validator_hashes_before.json", {"time": now(), "files": recorded})
    return recorded


def campaign_hashes() -> dict:
    data = ROOT / "data"
    files = {}
    if data.exists():
        for path in sorted(item for item in data.rglob("*") if item.is_file()):
            if "__pycache__" in path.parts:
                continue
            files[path.relative_to(data).as_posix()] = sha(path)
    env_path = ROOT / ".env"
    return {"files": files, "env_sha256": sha(env_path) if env_path.exists() else None}


def hidden_facts() -> list[str]:
    found = []
    for scene_id in ("frontier_gate", "old_milestone"):
        path = ROOT / "data" / "scenes" / f"{scene_id}.json"
        scene = json.loads(path.read_text(encoding="utf-8"))
        for item in scene["scene"].get("hidden_facts") or []:
            if isinstance(item, str) and item not in found:
                found.append(item)
    return found


def install_capture():
    import openai
    from openai import OpenAI as RealOpenAI

    class _Responses:
        def __init__(self, real):
            self._real = real

        def create(self, **kwargs):
            global CREATE_CALLS
            if CREATE_CALLS >= EXPERIMENT_REQUEST_CEILING:
                raise RuntimeError("experiment request ceiling")
            output_cap = kwargs.get("max_output_tokens")
            if isinstance(output_cap, int) and output_cap > EXPERIMENT_OUTPUT_CEILING:
                raise RuntimeError("output cap exceeds experiment")
            CREATE_CALLS += 1
            started = now()
            perf = time.perf_counter()
            try:
                response = self._real.create(**kwargs)
            except Exception as exc:
                RAW.append({
                    "create_index": CREATE_CALLS,
                    "ok": False,
                    "started_at": started,
                    "completed_at": now(),
                    "latency_ms": round((time.perf_counter() - perf) * 1000, 3),
                    "error_type": type(exc).__name__,
                    "error": redact(str(exc))[:500],
                    "max_output_tokens": output_cap,
                    "temperature": kwargs.get("temperature"),
                    "model": kwargs.get("model"),
                })
                raise
            payload = {
                "create_index": CREATE_CALLS,
                "ok": True,
                "started_at": started,
                "completed_at": now(),
                "latency_ms": round((time.perf_counter() - perf) * 1000, 3),
                "max_output_tokens": output_cap,
                "temperature": kwargs.get("temperature"),
                "model": kwargs.get("model"),
            }
            try:
                dumped = response.model_dump(mode="json") if hasattr(response, "model_dump") else {}
                payload["response"] = json.loads(json.dumps(dumped, default=str))
            except Exception as exc:
                payload["response"] = {
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "output_text": getattr(response, "output_text", None),
                    "serialization_error": type(exc).__name__,
                }
            usage = getattr(response, "usage", None)
            payload["provider_usage"] = None if usage is None else {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            RAW.append(redact(payload))
            return response

    class _Client:
        def __init__(self, real):
            self.responses = _Responses(real.responses)

    def factory(*args, **kwargs):
        return _Client(RealOpenAI(*args, **kwargs))

    openai.OpenAI = factory


def isolate(tmp: Path):
    from game import storage

    storage.BASE_DIR = tmp
    storage.DATA_DIR = tmp / "data"
    storage.WORLD_PATH = storage.DATA_DIR / "world.json"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    storage.CHARACTER_PATH = storage.DATA_DIR / "character.json"
    storage.CAMPAIGN_PATH = storage.DATA_DIR / "campaign.json"
    storage.SESSION_PATH = storage.DATA_DIR / "session.json"
    storage.COMBAT_PATH = storage.DATA_DIR / "combat.json"
    storage.CONDITIONS_PATH = storage.DATA_DIR / "conditions.json"
    storage.SESSION_LOG_PATH = storage.DATA_DIR / "session_log.jsonl"
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if storage.SCENES_DIR.exists():
        shutil.rmtree(storage.SCENES_DIR)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "data" / "scenes").glob("*.json"):
        shutil.copy2(path, storage.SCENES_DIR / path.name)


def seed(tmp: Path, scene_id: str) -> None:
    from game import storage
    from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world

    isolate(tmp)
    scene_path = storage.scene_path(scene_id)
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    hidden = list(scene["scene"].get("hidden_facts") or [])
    hidden.append("CANARY_HIDDEN_DESTINATION")
    scene["scene"]["hidden_facts"] = hidden
    scene["scene"]["gm_notes"] = ["CANARY_GM_NOTE"]
    scene["scene"]["private_notes"] = "CANARY_NPC_MOTIVE"
    scene["scene"]["discoverable_clues"] = list(scene["scene"].get("discoverable_clues") or [])
    scene["scene"]["discoverable_clues"].append({"id": "CANARY_MECHANICAL_ID", "text": "CANARY_UNDISCOVERED_CLUE"})
    storage._save_json(scene_path, scene)
    world = default_world()
    world["gm_only"] = {"motivation": "CANARY_NPC_MOTIVE", "quest": "CANARY_QUEST_TWIST"}
    world["unrelated_state"] = "CANARY_UNRELATED_WORLD"
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["campaign_started"] = True
    session["turn_counter"] = 1
    storage.save_session(session)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def snapshot():
    from game import storage

    return {
        "session": storage.load_session(),
        "world": storage.load_world(),
        "character": storage.load_character(),
        "combat": storage.load_combat(),
        "conditions": storage.load_conditions() if storage.CONDITIONS_PATH.exists() else None,
        "log": storage.load_log(),
    }


def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if "timestamp" not in str(key) and "latency" not in str(key) and "stamp" not in str(key)
            and str(key) not in {"run_id", "trace_id", "campaign_run_id", "session_id", "canonical_gm_object_id"}
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def diff(left, right, path="$"):
    if type(left) is not type(right):
        return [f"{path}: {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        rows = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                rows.append(f"{path}.{key}: present {key in left} vs {key in right}")
            else:
                rows.extend(diff(left[key], right[key], f"{path}.{key}"))
        return rows
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: len {len(left)} != {len(right)}"]
        rows = []
        for index, (a, b) in enumerate(zip(left, right)):
            rows.extend(diff(a, b, f"{path}[{index}]"))
        return rows
    if left != right:
        return [f"{path}: values differ"]
    return []


def authority_slice(body: dict) -> dict:
    character = body.get("character") if isinstance(body.get("character"), dict) else {}
    world = body.get("world") if isinstance(body.get("world"), dict) else {}
    session = body.get("session") if isinstance(body.get("session"), dict) else {}
    return {
        "inventory": character.get("inventory"),
        "conditions": body.get("conditions"),
        "combat": body.get("combat"),
        "world_without_canary_slots": {
            key: value for key, value in world.items() if key not in {"gm_only", "unrelated_state"}
        },
        "active_scene_id": session.get("active_scene_id"),
        "visited_scene_ids": session.get("visited_scene_ids"),
        "quest_keys_present": sorted(key for key in session if "quest" in str(key).casefold()),
    }


def mechanical(body: dict) -> dict:
    resolution = body.get("resolution") if isinstance(body.get("resolution"), dict) else {}
    changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "action_id": resolution.get("action_id"),
        "interactable_id": resolution.get("interactable_id"),
        "clue_id": resolution.get("clue_id"),
        "clue_text": resolution.get("clue_text"),
        "discovered_clues": resolution.get("discovered_clues"),
        "state_changes": {
            "clue_revealed": changes.get("clue_revealed"),
            "already_searched": changes.get("already_searched"),
            "skill_check_failed": changes.get("skill_check_failed"),
            "interactable_id": changes.get("interactable_id"),
        },
    }


def facing(body: dict) -> str:
    gm = body.get("gm_output") if isinstance(body.get("gm_output"), dict) else {}
    return str(gm.get("player_facing_text") or "")


def leaks(value) -> list[str]:
    blob = json.dumps(value, ensure_ascii=False)
    found = [item for item in CANARIES if item in blob]
    for token in ("notice_patrol_route", "milestone_mud_prints", "CANARY_MECHANICAL_ID", "skill_check", "gm_notes"):
        if token in blob:
            found.append(token)
    found.extend(item for item in hidden_facts() if item in blob)
    return found


def contained(text: str, blob: str) -> bool:
    stripped = (text or "").strip()
    return bool(stripped) and stripped in blob


def play_sequence(tmp: Path, scene_id: str, turns: list[dict], label: str) -> dict:
    from fastapi.testclient import TestClient

    from game import api, storage
    from game.quarantined_investigation_narration import (
        EVIDENCE_ENV,
        FAULT_ENV,
        GATE_ENV,
        LABEL_ENV,
        LIVE_ENV,
        clear_evidence,
        evidence_records,
    )

    seed(tmp, scene_id)
    before = snapshot()
    clear_evidence()
    started_at = now()
    perf = time.perf_counter()
    creates_before = CREATE_CALLS
    client = TestClient(api.app)
    client.__enter__()
    turn_rows = []
    try:
        for index, turn in enumerate(turns, start=1):
            live = bool(turn.get("live"))
            fault = str(turn.get("fault") or "")
            turn_label = f"{label}_t{index}"
            if live or fault:
                os.environ[GATE_ENV] = "1"
                os.environ[LIVE_ENV] = "1" if live else "0"
                os.environ[FAULT_ENV] = fault
                os.environ[LABEL_ENV] = turn_label
                os.environ[EVIDENCE_ENV] = str(EVIDENCE)
            else:
                os.environ.pop(GATE_ENV, None)
                os.environ.pop(LIVE_ENV, None)
                os.environ[FAULT_ENV] = ""
            prior_records = len(evidence_records())
            prior_creates = CREATE_CALLS
            response = client.post("/api/chat?ui_mode=player", json={"text": turn["text"]})
            status = response.status_code
            body = response.json()
            record = evidence_records()[-1] if len(evidence_records()) > prior_records else None
            turn_rows.append({
                "turn": index,
                "player_text": turn["text"],
                "live": live,
                "fault": fault or None,
                "status_code": status,
                "player_facing": facing(body),
                "mechanical": mechanical(body),
                "quarantine": record,
                "provider_creates_this_turn": CREATE_CALLS - prior_creates,
                "context_leaks": leaks({
                    "hook_input": None if record is None else record.get("hook_input"),
                    "message": None if record is None else (record.get("live_provider") or {}).get("sanitized_provider_user_message"),
                }),
            })
    finally:
        completed_at = now()
        elapsed_ms = round((time.perf_counter() - perf) * 1000, 3)
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass
    after = snapshot()
    return {
        "label": label,
        "scene_id": scene_id,
        "scenes_dir": str(storage.SCENES_DIR),
        "started_at": started_at,
        "completed_at": completed_at,
        "sequence_latency_ms": elapsed_ms,
        "provider_creates": CREATE_CALLS - creates_before,
        "turns": turn_rows,
        "authority_before": authority_slice(before),
        "authority_after": authority_slice(after),
        "state_differences_within_sequence": diff(scrub(before), scrub(after)),
        "final_scrubbed_hash": hashlib.sha256(
            json.dumps(scrub(after), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest(),
    }


def generation_parameters() -> dict:
    from game.expressive_dialogue import _OUTPUT_CAP, request_expression
    from game.gm import provider_timeout_seconds
    from game.provider_budget import sdk_retry_options
    from game.quarantined_investigation_narration import (
        LIVE_SYSTEM_PROMPT,
        MAX_LIVE_OUTPUT_TOKENS,
        MAX_LIVE_REQUESTS,
        MAX_LIVE_TOTAL_TOKENS,
    )

    source = inspect.getsource(request_expression)
    return {
        "adapter": "game.expressive_dialogue.request_expression",
        "endpoint": "responses.create",
        "temperature_in_source": "temperature=0.2" in source.replace(" ", ""),
        "max_output_tokens_constant": _OUTPUT_CAP,
        "timeout_seconds": provider_timeout_seconds(),
        "sdk_retry_options": sdk_retry_options(),
        "host_retries_disabled": os.environ.get("ASHEN_DISABLE_PROVIDER_RETRIES") == "1",
        "hook_forbids_second_generate": True,
        "hook_request_ceiling": MAX_LIVE_REQUESTS,
        "hook_output_ceiling": MAX_LIVE_OUTPUT_TOKENS,
        "hook_total_token_ceiling": MAX_LIVE_TOTAL_TOKENS,
        "cycle_request_ceiling": 8,
        "cycle_output_ceiling": EXPERIMENT_OUTPUT_CEILING,
        "cycle_total_token_ceiling": EXPERIMENT_TOTAL_CEILING,
        "system_prompt": LIVE_SYSTEM_PROMPT,
    }


def preflight() -> dict:
    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.expressive_dialogue import _OUTPUT_CAP
    from game.provider_budget import provider_calls_disabled

    key_present = False
    try:
        key_present = len(get_openai_api_key()) > 8
    except Exception:
        key_present = False
    dns_error = None
    try:
        socket.getaddrinfo("api.openai.com", 443)
    except Exception as exc:
        dns_error = type(exc).__name__
    parameters = generation_parameters()
    blockers = []
    if not key_present:
        blockers.append("credentials_unavailable")
    if dns_error:
        blockers.append("provider_dns_unavailable:" + dns_error)
    if _OUTPUT_CAP > EXPERIMENT_OUTPUT_CEILING:
        blockers.append("configured_output_cap_exceeds_experiment")
    if not DEFAULT_MODEL_NAME:
        blockers.append("model_unconfigured")
    if parameters["hook_request_ceiling"] > 8:
        blockers.append("hook_ceiling_above_cycle")
    report = {
        "time": now(),
        "provider": "openai",
        "model": DEFAULT_MODEL_NAME,
        "gameplay_provider_calls_disabled": provider_calls_disabled(),
        "player_facing_narration": "disabled; quarantine prelude is not written into player_facing_text",
        "feature_flags": {
            "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
            "ASHEN_DISABLE_EXPRESSION_GENERATION": os.environ.get("ASHEN_DISABLE_EXPRESSION_GENERATION"),
            "ASHEN_DISABLE_PROVIDER_CALLS": os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS"),
            "ASHEN_PLAYTEST_DISABLE_SDK_RETRIES": os.environ.get("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"),
            "ASHEN_DISABLE_PROVIDER_RETRIES": os.environ.get("ASHEN_DISABLE_PROVIDER_RETRIES"),
            "ASHEN_QUARANTINE_INVESTIGATION_NARRATION": "set only on a live or fault turn",
            "ASHEN_QUARANTINE_NARRATION_LIVE": "set only on a live turn",
        },
        "usage_ledger": str(LEDGER),
        "key_present": key_present,
        "dns_ok": dns_error is None,
        "generation": {key: value for key, value in parameters.items() if key != "system_prompt"},
        "system_prompt_sha256": hashlib.sha256(parameters["system_prompt"].encode("utf-8")).hexdigest(),
        "blockers": blockers,
        "estimated_cost_supported": False,
        "automatic_retries": "0. A timeout, authentication failure, or connection failure sets the hook stop flag. This script does not clear it.",
    }
    write_json("preflight.json", report)
    write_json("generation_parameters.json", parameters)
    return report


def scenario_manifest() -> dict:
    manifest = {
        "time": now(),
        "selection_rule": "Existing deterministic investigations from the PR-PLAY-52 through PR-PLAY-53 fixtures. No new campaign facts.",
        "request_plan": "Two generations for authorized discovery and incidental detail. One generation for the repeat search and the footprint paraphrase. Total planned live requests: 6, the existing hook ceiling.",
        "scenarios": [
            {
                "id": "A",
                "category": "authorized_discovery",
                "scene_id": "frontier_gate",
                "player_text": "I examine the notice board.",
                "expected_outcome": "discover_clue success, clue text is the northwest mud track sentence",
                "generations": 2,
                "supports_category": True,
            },
            {
                "id": "B",
                "category": "unsuccessful_investigation",
                "scene_id": "frontier_gate",
                "player_text": "I examine the notice board.",
                "setup": "The same action is resolved once with the provider off, then repeated.",
                "expected_outcome": "already_searched, success false, no new clue",
                "generations": 1,
                "supports_category": True,
                "limitation": "These scenes have no authored skill-check failure. A dice failure would not be deterministic. The repeat search is the existing unsuccessful outcome.",
            },
            {
                "id": "C",
                "category": "incidental_environmental_detail",
                "scene_id": "frontier_gate",
                "player_text": "I examine the rain barrel.",
                "expected_outcome": "investigate success true, no discovered clue, status observed",
                "generations": 2,
                "supports_category": True,
            },
            {
                "id": "D",
                "category": "authorized_paraphrase",
                "scene_id": "old_milestone",
                "player_text": "I examine the footprints.",
                "expected_outcome": "discover_clue success, hedged print sentence appended by the engine",
                "generations": 1,
                "supports_category": True,
                "limitation": "The live prompt tells the provider not to repeat the discovery. The engine appends the authorized sentence. A paraphrase inside the prelude is what this generation measures.",
            },
            {
                "id": "E",
                "category": "ambiguous_discovery",
                "supports_category": False,
                "limitation": "No separate live fixture states a visible detail that the engine itself leaves ambiguous between scenery and a clue. The milestone prints are already the authorized discovery in scenario D. The PR-PLAY-55 ambiguous lines are authored sentences, not resolvable player actions. This category is not executed.",
            },
        ],
    }
    write_json("scenario_manifest.json", manifest)
    return manifest


def direct_validation(record: dict | None) -> dict:
    """Call the frozen validator on the exact candidate. Do not treat its result as ground truth."""
    if not isinstance(record, dict):
        return {"decision": "VALIDATION_ERROR", "reasons": ["no_quarantine_record"], "claims": []}
    text = record.get("raw_provider_text")
    hook = record.get("hook_input") if isinstance(record.get("hook_input"), dict) else {}
    if not isinstance(text, str):
        return {"decision": "VALIDATION_ERROR", "reasons": ["no_candidate_text"], "claims": [], "pipeline_diagnostic": record.get("diagnostic")}
    from game.anchored_investigation_narration import authorize_anchored_investigation
    from game.consequential_narration_validation import authority_from_anchored, validate_consequential_narration
    from game.immutable_valid_response import validate_generated_response
    from game.resolution_contract import contract_mapping_from_resolution

    try:
        contract = authorize_anchored_investigation(hook["resolution"], hook["narration_payload"])
    except Exception as exc:
        return {
            "decision": "VALIDATION_ERROR",
            "reasons": ["authority_reconstruction_failed"],
            "error_type": type(exc).__name__,
            "claims": [],
            "pipeline_diagnostic": record.get("diagnostic"),
            "pipeline_validation": record.get("validation"),
        }
    authority = authority_from_anchored(contract)
    started = time.perf_counter()
    decision = validate_consequential_narration(text, authority)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    resolution = {
        "kind": "investigate",
        "success": contract.outcome.success,
        "discovered_clues": list(contract.outcome.revealed),
        "state_changes": {},
    }
    legacy_started = time.perf_counter()
    try:
        legacy = validate_generated_response(
            text,
            resolution=resolution,
            contract=contract_mapping_from_resolution(resolution),
        )
        legacy_error = None
    except Exception as exc:
        legacy = None
        legacy_error = type(exc).__name__
    legacy_ms = round((time.perf_counter() - legacy_started) * 1000, 3)
    return {
        "decision": decision.get("decision"),
        "reasons": decision.get("reasons"),
        "claims": decision.get("claims"),
        "provider_requests": decision.get("provider_requests"),
        "coverage": decision.get("coverage"),
        "direct_validator_latency_ms": latency_ms,
        "legacy_validation": legacy,
        "legacy_error": legacy_error,
        "legacy_latency_ms": legacy_ms,
        "pipeline_diagnostic": record.get("diagnostic"),
        "pipeline_used_fallback": record.get("used_fallback"),
        "pipeline_validation_ms": record.get("validation_ms"),
        "pipeline_validation": record.get("validation"),
        "authority": {
            "observable_scene": list(authority.observable_scene),
            "authorized_discoveries": list(authority.authorized_discoveries),
            "authorized_outcomes": list(authority.authorized_outcomes),
            "restricted": list(authority.restricted),
            "success": authority.success,
        },
    }


def worksheet(scenario_id: str, generation: int, row: dict, validation: dict) -> dict:
    record = None
    for turn in row.get("turns") or []:
        if turn.get("live") and isinstance(turn.get("quarantine"), dict):
            record = turn["quarantine"]
    text = None if record is None else record.get("raw_provider_text")
    return {
        "scenario_id": scenario_id,
        "generation": generation,
        "label": row.get("label"),
        "raw_narration": text,
        "authorized_facts": validation.get("authority"),
        "mechanical": [turn.get("mechanical") for turn in row.get("turns") or []],
        "pipeline_diagnostic": None if record is None else record.get("diagnostic"),
        "validator_decision": validation.get("decision"),
        "validator_reasons": validation.get("reasons"),
        "candidate_claims_from_validator": validation.get("claims"),
        "proposed_semantic_classification": "EVALUATION_INCOMPLETE",
        "classification_status": "awaiting_independent_review",
        "supporting_evidence": "Not filled by the validator. A later review compares the raw sentence with the authorized facts.",
        "uncertainty_notes": "",
        "human_confirmed": False,
    }


def invariant_checks() -> dict:
    """Offline checks. They do not call a provider and do not change the validator."""
    from game.consequential_narration_validation import (
        PASS,
        REVIEW_REQUIRED,
        SemanticAuthority,
        apply_consequential_gate,
        validate_consequential_narration,
    )

    before = file_hashes((PRIMARY_VALIDATOR,))
    fabrication = validate_consequential_narration(
        "You find a silver key beneath the board.",
        SemanticAuthority(observable_scene=("The notice board lists taxes.",), success=True),
    )
    review = validate_consequential_narration(
        "An unfamiliar mark is cut into the board.",
        SemanticAuthority(observable_scene=("The notice board lists taxes.",), success=True),
    )
    gated = apply_consequential_gate({"hard_valid": True, "reasons": []}, review)
    after = file_hashes((PRIMARY_VALIDATOR,))
    checks = {
        "fabrication_is_not_pass": fabrication.get("decision") != PASS,
        "review_is_not_pass": review.get("decision") == REVIEW_REQUIRED,
        "gate_blocks_review": gated.get("hard_valid") is False,
        "validator_makes_no_provider_request": fabrication.get("provider_requests") == 0 and review.get("provider_requests") == 0,
        "validator_bytes_unchanged": before == after,
    }
    checks["passed"] = all(checks.values())
    write_json("invariant_checks.json", checks)
    return checks


def pair(live_row: dict, base_row: dict) -> dict:
    live_turns = live_row["turns"]
    base_turns = base_row["turns"]
    facing_match = [a["player_facing"] == b["player_facing"] for a, b in zip(live_turns, base_turns)]
    mechanical_match = [a["mechanical"] == b["mechanical"] for a, b in zip(live_turns, base_turns)]
    authority_diff = diff(scrub(live_row["authority_after"]), scrub(base_row["authority_after"]))
    candidates = []
    persisted = []
    for turn in live_turns:
        record = turn.get("quarantine") if isinstance(turn.get("quarantine"), dict) else {}
        text = record.get("raw_provider_text") if isinstance(record.get("raw_provider_text"), str) else ""
        assembled = record.get("assembled") if isinstance(record.get("assembled"), str) else ""
        facing_text = turn["player_facing"]
        candidates.append(text)
        if contained(text, facing_text) or contained(assembled, facing_text):
            persisted.append("player_facing")
        blob = json.dumps(live_row["authority_after"], ensure_ascii=False, default=str)
        if contained(text, blob):
            persisted.append("authority_slice")
    return {
        "scenario": live_row["label"],
        "turn_count_match": len(live_turns) == len(base_turns),
        "player_facing_identical": facing_match,
        "mechanical_identical": mechanical_match,
        "authority_slice_differences": authority_diff,
        "narration_persisted": persisted,
        "context_leaks": [item for turn in live_turns for item in turn.get("context_leaks") or []],
        "provider_creates": live_row["provider_creates"],
        "baseline_provider_creates": base_row["provider_creates"],
    }


def stop_reason(pairs: list[dict], usage: dict) -> str:
    for row in pairs:
        if not all(row["player_facing_identical"]):
            return "player_facing_changed"
        if not all(row["mechanical_identical"]):
            return "mechanical_outcome_changed"
        if row["authority_slice_differences"]:
            return "authoritative_slice_changed"
        if row["narration_persisted"]:
            return "experimental_narration_persisted"
        if row["context_leaks"]:
            return "restricted_context_leaked"
        if row["baseline_provider_creates"]:
            return "baseline_called_provider"
    total = usage.get("total_tokens")
    if isinstance(total, int) and total >= EXPERIMENT_TOTAL_CEILING:
        return "token_budget"
    if usage.get("stopped") and str(usage.get("stop_reason") or "") not in {"", "experiment_request_ceiling"}:
        return "provider_accounting_stopped:" + str(usage.get("stop_reason"))
    return ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    freeze_validator()
    before = campaign_hashes()
    write_json("campaign_hashes_before.json", before)
    scenario_manifest()
    checks = invariant_checks()
    if not checks["passed"]:
        write_json("dispatch_aborted.json", {"time": now(), "reason": "invariant_checks_failed", "checks": checks})
        print(json.dumps({"aborted": "invariant_checks_failed"}, indent=2))
        return 2
    report = preflight()
    if report["blockers"]:
        write_json("dispatch_aborted.json", {"time": now(), "blockers": report["blockers"], "provider_requests": 0})
        print(json.dumps({"aborted": report["blockers"]}, indent=2))
        return 2
    if LEDGER.exists():
        raise RuntimeError("usage ledger already exists")
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(LEDGER)
    from game.provider_budget import initialize_accounting, snapshot as usage_snapshot
    from game.quarantined_investigation_narration import reset_live_budget

    initialize_accounting()
    install_capture()
    reset_live_budget()
    tmp = OUT / "tmp_runs"
    if tmp.exists():
        shutil.rmtree(tmp)
    notice = "I examine the notice board."
    barrel = "I examine the rain barrel."
    prints = "I examine the footprints."
    results = {}
    validations = []
    worksheets = []
    pairs = []
    halted = ""
    try:
        fault = play_sequence(tmp / "fault", "frontier_gate", [{"text": notice, "live": False, "fault": "timeout"}], "F_fault")
        results["F_fault"] = fault
        if fault["provider_creates"] != 0:
            halted = "fault_injection_called_provider"
        else:
            plan = [
                ("A1", "A_baseline", "frontier_gate", [{"text": notice, "live": True}], [{"text": notice, "live": False}]),
                ("A2", None, "frontier_gate", [{"text": notice, "live": True}], None),
                ("B1", "B_baseline", "frontier_gate", [
                    {"text": notice, "live": False},
                    {"text": notice, "live": True},
                ], [
                    {"text": notice, "live": False},
                    {"text": notice, "live": False},
                ]),
                ("C1", "C_baseline", "frontier_gate", [{"text": barrel, "live": True}], [{"text": barrel, "live": False}]),
                ("C2", None, "frontier_gate", [{"text": barrel, "live": True}], None),
                ("D1", "D_baseline", "old_milestone", [{"text": prints, "live": True}], [{"text": prints, "live": False}]),
            ]
            for label, baseline_label, scene_id, turns, baseline_turns in plan:
                if halted:
                    break
                if CREATE_CALLS >= EXPERIMENT_REQUEST_CEILING:
                    halted = "experiment_request_ceiling"
                    break
                usage = usage_snapshot()
                total = usage.get("total_tokens")
                if isinstance(total, int) and total >= min(EXPERIMENT_TOTAL_CEILING, 10000):
                    halted = "token_budget"
                    break
                if usage.get("stopped"):
                    halted = "provider_accounting_stopped:" + str(usage.get("stop_reason") or "")
                    break
                live_row = play_sequence(tmp / label, scene_id, turns, label)
                results[label] = live_row
                base_row = None
                if baseline_turns is not None and baseline_label is not None:
                    base_row = play_sequence(tmp / baseline_label, scene_id, baseline_turns, baseline_label)
                    results[baseline_label] = base_row
                    compared = pair(live_row, base_row)
                    pairs.append(compared)
                    halted = stop_reason([compared], usage_snapshot())
                record = next((turn.get("quarantine") for turn in live_row["turns"] if turn.get("live")), None)
                validation = direct_validation(record if isinstance(record, dict) else None)
                validation["label"] = label
                validations.append(validation)
                worksheets.append(worksheet(label[0], int(label[1]), live_row, validation))
                provider = (record or {}).get("live_provider") if isinstance(record, dict) else {}
                error = str((provider or {}).get("provider_error") or "")
                if error in {"AuthenticationError", "PermissionDeniedError", "APIConnectionError", "APITimeoutError"}:
                    halted = "provider_failure:" + error
                leaked_output = []
                text = (record or {}).get("raw_provider_text") if isinstance(record, dict) else ""
                if isinstance(text, str):
                    leaked_output = [item for item in list(CANARIES) + hidden_facts() if item in text]
                if leaked_output:
                    halted = "restricted_information_in_output"
    except Exception:
        write_json("experiment_exception.json", {
            "time": now(),
            "traceback": redact(traceback.format_exc()[-4000:]),
            "create_calls": CREATE_CALLS,
        })
        raise
    finally:
        after = campaign_hashes()
        changed = sorted(name for name, digest in before["files"].items() if after["files"].get(name) != digest)
        added = sorted(set(after["files"]) - set(before["files"]))
        write_json("campaign_hashes_after.json", {
            "changed": changed,
            "added": added,
            "env_unchanged": before["env_sha256"] == after["env_sha256"],
        })
        final_hashes = file_hashes(VALIDATOR_FILES)
        initial = json.loads((OUT / "validator_hashes_before.json").read_text(encoding="utf-8"))["files"]
        comparisons = {}
        for relative in VALIDATOR_FILES:
            comparisons[relative] = {
                "before": initial[relative]["sha256"],
                "after": final_hashes[relative]["sha256"],
                "match": initial[relative]["sha256"] == final_hashes[relative]["sha256"],
            }
        frozen = SOURCE / "consequential_narration_validation.py"
        comparisons[PRIMARY_VALIDATOR]["matches_frozen_copy"] = sha(frozen) == final_hashes[PRIMARY_VALIDATOR]["sha256"]
        write_json("validator_hashes_after.json", {"time": now(), "files": comparisons, "all_match": all(row["match"] for row in comparisons.values())})
    from game.provider_budget import snapshot as usage_snapshot

    usage = usage_snapshot()
    write_json("scenario_results.json", {
        "time": now(),
        "halted": halted,
        "create_calls": CREATE_CALLS,
        "usage": usage,
        "pairs": pairs,
        "results": results,
        "raw_provider_responses": RAW,
    })
    write_json("validator_decisions.json", validations)
    write_json("independent_review_worksheets.json", worksheets)
    summary = {
        "create_calls": CREATE_CALLS,
        "halted": halted,
        "usage": {
            "requests": usage.get("dispatched_requests"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "stopped": usage.get("stopped"),
            "stop_reason": usage.get("stop_reason"),
        },
        "pairs": [
            {
                "scenario": row["scenario"],
                "facing": row["player_facing_identical"],
                "mechanical": row["mechanical_identical"],
                "authority_diffs": len(row["authority_slice_differences"]),
                "persisted": row["narration_persisted"],
                "leaks": row["context_leaks"],
            }
            for row in pairs
        ],
        "decisions": [
            {"label": row["label"], "decision": row.get("decision"), "pipeline": row.get("pipeline_diagnostic")}
            for row in validations
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0 if not halted else 3


if __name__ == "__main__":
    raise SystemExit(main())
