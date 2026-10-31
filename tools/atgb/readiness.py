"""Validation-only configuration gate. Never dispatches a provider request.

Use a fresh process/store per future live trial. Old R1-03 execute_trial.py is
historical evidence and must not be reused. No test or experiment imports here.
"""
from __future__ import annotations

import copy
import importlib
import os
from contextlib import contextmanager
from pathlib import Path

FLAG = "ASHEN_DISABLE_LIVE_INTERPRETATION"
FLAGS = (FLAG, "ASHEN_DISABLE_PROVIDER_CALLS", "ASHEN_DISABLE_PROVIDER_RETRIES",
         "ASHEN_DISABLE_EXPRESSION_GENERATION", "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT")


def flag_snapshot():
    return {key: os.environ.get(key) for key in FLAGS}


@contextmanager
def execution_mode(live: bool):
    """Same scoped MonkeyPatch convention as repository fixtures; restores on error."""
    from pytest import MonkeyPatch
    with MonkeyPatch.context() as patch:
        patch.setenv(FLAG, "0" if live else "1")
        yield


def import_fixture(module: str):
    """Reject and restore observable import configuration changes, including errors."""
    before = dict(os.environ)
    try:
        result = importlib.import_module(module)
        if dict(os.environ) != before:
            raise RuntimeError("validation_fixture_import_side_effect")
        return result
    finally:
        # Only undo differences; do not dump environment values into evidence.
        for key in set(os.environ) - set(before):
            del os.environ[key]
        for key, value in before.items():
            if os.environ.get(key) != value:
                os.environ[key] = value


def pending_errors(session, scene, world, character):
    """Validate an existing intention; never constructs or blesses a proposed action."""
    pending = (session.get("conversational_context") or {}).get("pending_intention") or {}
    scene_id = (scene.get("scene") or scene).get("id")
    npcs = {row["id"] for row in world.get("npcs", []) if row.get("location") == scene_id}
    choices = pending.get("choices") or []
    checks = {
        "pending_exists": bool(pending),
        "pending_unexecuted": pending.get("status") == "pending" and not
            (session.get("conversational_context") or {}).get("last_executed_intention"),
        "pending_scene": pending.get("scene_id") == scene_id == session.get("active_scene_id"),
        "pending_operation": pending.get("operation") == "ASK",
        "pending_actor": bool(character.get("name") or character.get("id")),
        "pending_targets": bool(choices) and all(c.get("entity_id") in npcs for c in choices),
        "pending_ambiguous": pending.get("target_resolution") == "ambiguous",
    }
    return [name for name, ok in checks.items() if not ok]


def preflight(*, live, model, limit, store, session, scene, world, character,
              imports_before, require_pending=True):
    """Nonsecret local readiness evidence; availability means configured, not reachable."""
    from game import config, storage
    from game.live_chat_interpretation import production_live_interpretation_enabled, _contract
    from game.provider_budget import snapshot, accounting_active, limits
    from tools.atgb.isolation import assert_safe_benchmark_data_dir

    effective = production_live_interpretation_enabled()
    # _contract already restores legacy experimental import flags, caches schema/model.
    selected_model = _contract()[4]
    flags = flag_snapshot()
    accounting = snapshot()
    try:
        provider_configured = bool(config.get_openai_api_key())
    except RuntimeError:
        provider_configured = False
    try:
        bounds = limits()
    except (ValueError, TypeError):
        bounds = None
    try:
        safe = assert_safe_benchmark_data_dir(Path(store)) == Path(storage.DATA_DIR).resolve()
    except RuntimeError:
        safe = False
    failures = []
    checks = {
        "execution_mode": effective == live,
        "provider_configured": not live or provider_configured,
        "provider_sdk": importlib.util.find_spec("openai") is not None,
        "selected_model": selected_model == model and config.DEFAULT_MODEL_NAME == model,
        "routing_models": config.HIGH_PRECISION_MODEL_NAME == model and
            config.RETRY_ESCALATION_MODEL_NAME == model,
        "fixture_import_flags": imports_before == flags,
        "isolated_store": safe,
        "fixture_matches_store": safe and session == storage.load_session() and
            scene == storage.load_active_scene() and world == storage.load_world() and
            character == storage.load_character(),
        "admission_limit": accounting_active() and bool(bounds) and bounds[0] == limit and 0 < limit <= 2,
        "token_limits": bool(bounds) and all(n > 0 for n in bounds),
        "durable_ledger": accounting.get("request_upper_bound") == 0,
        "fresh_accounting": accounting.get("requests") == 0 and not accounting.get("stopped"),
        "retries_disabled": flags["ASHEN_DISABLE_PROVIDER_RETRIES"] == "1",
        "startup_preflight_skipped": flags["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] == "1",
    }
    failures.extend(name for name, ok in checks.items() if not ok)
    if require_pending:
        failures.extend(pending_errors(session, scene, world, character))
    return {
        "evidence_scope": "structural_only", "classification": "validation_setup_failure" if failures else "ready",
        "failed_assertions": failures, "requested_live": live, "effective_live": effective,
        "provider_configured": provider_configured, "provider_reachability": "unprobed",
        "model": selected_model, "flags": flags, "admission_limit": bounds[0] if bounds else None,
        "model_routing_enabled": config.ENABLE_MODEL_ROUTING,
        "routing_models": [config.DEFAULT_MODEL_NAME, config.HIGH_PRECISION_MODEL_NAME,
                           config.RETRY_ESCALATION_MODEL_NAME],
        "provider_admissions": accounting.get("requests"), "gameplay_state_changed": False,
    }


def guarded_trial(*, evidence_path, execute, **configuration):
    """Mandatory gate before a future caller can invoke chat or admit a request."""
    import json
    try:
        result = preflight(**configuration)
    except Exception as error:
        from game.provider_budget import snapshot
        result = {"classification": "validation_setup_failure",
                  "failed_assertions": ["preflight_configuration_exception"],
                  "exception_type": type(error).__name__, "flags": flag_snapshot(),
                  "provider_admissions": snapshot().get("requests"),
                  "gameplay_state_changed": False}
    Path(evidence_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["failed_assertions"]:
        return result
    return execute()


def seed_control(path, patch):
    """Replay only captured base world; production chat must create the pending ask.

    Uses R1-03 L4's preserved pre-execution content, never imports its experimental
    fixture. Clears its manually seeded intention so tests can establish provenance.
    """
    from game import storage
    import json
    root = Path(__file__).resolve().parents[2]
    base = json.loads((root / "artifacts/atgb/atgb_r1_03/L4/before.json").read_text(encoding="utf-8"))
    data = Path(path) / "data"
    data.mkdir(parents=True, exist_ok=False)
    patch.setattr(storage, "DATA_DIR", data)
    patch.setattr(storage, "BASE_DIR", Path(path))
    patch.setattr(storage, "SCENES_DIR", data / "scenes")
    storage.SCENES_DIR.mkdir()
    for name in ("WORLD", "CHARACTER", "SESSION", "COMBAT", "CAMPAIGN", "CONDITIONS"):
        patch.setattr(storage, name + "_PATH", data / (name.lower() + ".json"))
    patch.setattr(storage, "SESSION_LOG_PATH", data / "session_log.jsonl")
    session = copy.deepcopy(base["session"])
    session["conversational_context"] = {}
    for key in ("world", "character", "combat"):
        storage._save_json(getattr(storage, key.upper() + "_PATH"), base[key])
    storage.save_session(session)
    storage.save_scene(base["scene"])
    storage._save_json(storage.CAMPAIGN_PATH, {"title": "ATGB revision control"})
    storage._save_json(storage.CONDITIONS_PATH, {"conditions": []})
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return data
