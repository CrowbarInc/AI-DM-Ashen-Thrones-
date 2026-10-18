"""PR-DL orchestration. Deterministic matrix first; one live call per scenario."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

from experiments.pr_dg.isolation import ProductionSaveGuard, forbid_provider_calls  # noqa: E402
from experiments.pr_dg.state import state_hash  # noqa: E402
from experiments.pr_dj.adapter import validate_hand_authored_interpretation  # noqa: E402
from experiments.pr_dk.runner import run_comparison  # noqa: E402
from experiments.pr_dl.budget import OUTPUT_TOKEN_CAP, Budget, BudgetStop  # noqa: E402
from experiments.pr_dl.evidence import evidence_corrections  # noqa: E402
from experiments.pr_dl.live import call_interpretation, redact  # noqa: E402
from experiments.pr_dl.prompt import (  # noqa: E402
    build_messages,
    estimate_input_tokens,
    hidden_leaks,
    interpretation_schema,
    permitted_entities,
    schema_is_non_authoritative,
)
from experiments.pr_dl.scoring import deterministic_gameplay, score_live  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dl_interpretation_comparison"
STAGE_1 = ("S1", "ambiguous", "compound")
EXPECTED_METRICS = {
    "A": {"true_positive": 3, "false_positive": 0, "false_negative": 6},
    "B": {"true_positive": 8, "false_positive": 2, "false_negative": 1},
    "C": {"true_positive": 9, "false_positive": 12, "false_negative": 0},
}


class IsolationStop(RuntimeError):
    """Raised when live calls must not start."""


def _specs_by_id() -> dict[str, dict[str, Any]]:
    from experiments.pr_dk.runner import _scenario_specs

    return {spec["scenario_id"]: spec for spec in _scenario_specs()}


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return json.loads(json.dumps(value, default=str))


def _discourse_focus(bundle: Any, hidden: list[str]) -> dict[str, Any] | None:
    focus = bundle.session.get("discourse_focus")
    if not isinstance(focus, dict):
        return None
    blob = json.dumps(focus, default=str)
    if any(item and item.casefold() in blob.casefold() for item in hidden):
        return None
    interlocutor = focus.get("interlocutor") if isinstance(focus.get("interlocutor"), dict) else {}
    return {
        "interlocutor": {
            "id": interlocutor.get("id"),
            "label": interlocutor.get("label") or interlocutor.get("name"),
        }
    }


def prepare_matrix() -> dict[str, Any]:
    """Run the preserved PR-DK matrix with live interpretation and saves blocked."""
    if not schema_is_non_authoritative(interpretation_schema()):
        raise IsolationStop("interpretation schema contains authoritative fields")
    specs = _specs_by_id()
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as hits:
            payload = run_comparison()
            if hits:
                raise IsolationStop(f"unrelated provider path fired during deterministic preparation: {hits}")
        guard.assert_unchanged()
        isolation = {
            "save_guard_verified": guard.verified,
            "provider_tripwire_hits": list(hits),
            "save_attempts_after_probe": list(guard.attempts),
        }
    metrics = payload["metrics"]
    for key, expected in EXPECTED_METRICS.items():
        actual = metrics[key]
        for field, value in expected.items():
            if actual[field] != value:
                raise IsolationStop(f"PR-DK matrix drifted for {key}.{field}: {actual[field]} != {value}")
    rows = []
    schema = interpretation_schema()
    for source in payload["rows"]:
        spec = specs[source["scenario_id"]]
        bundle = spec["factory"]()
        before = state_hash(bundle)
        if state_hash(spec["factory"]()) != before:
            raise IsolationStop(f"scenario factory is not stable for {source['scenario_id']}")
        messages, public = build_messages(bundle, source["utterance"])
        after = state_hash(bundle)
        hidden = [str(item) for item in bundle.hidden_strings if str(item).strip()]
        leaks = hidden_leaks(messages, hidden)
        if leaks:
            raise IsolationStop(f"prompt for {source['scenario_id']} contains hidden information")
        if before != after or before != public["state_hash"]:
            raise IsolationStop(f"prompt construction mutated {source['scenario_id']}")
        estimate = estimate_input_tokens(messages, schema)
        rows.append(
            {
                **{key: _jsonable(source[key]) for key in source},
                "deterministic_gameplay": deterministic_gameplay(source["scenario_id"], source["contract_trace"]),
                "messages": messages,
                "public_context": public,
                "discourse_focus": _discourse_focus(bundle, hidden),
                "canonical_referents": permitted_entities(bundle),
                "estimated_input_tokens": estimate,
                "hidden_leak_count": len(leaks),
                "state_hash": before,
            }
        )
    evidence = evidence_corrections(ROOT, payload["rows"])
    if evidence["manual_trace"]["provider_calls_observed"]:
        raise IsolationStop("deterministic preparation invoked the interpretation provider")
    return {
        "rows": rows,
        "metrics": _jsonable(metrics),
        "live_provider_calls_during_preparation": payload["live_provider_calls"],
        "isolation": isolation,
        "evidence": evidence,
        "output_token_cap": OUTPUT_TOKEN_CAP,
        "configured_model_source": "game.config.DEFAULT_MODEL_NAME",
    }


def _unusable(record: Mapping[str, Any]) -> bool:
    return not bool(record.get("accepted"))


def run_live(prepared: Mapping[str, Any], *, scenario_ids: list[str], budget: Budget | None = None) -> dict[str, Any]:
    """Issue one interpretation call per listed scenario. No retries."""
    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from openai import OpenAI

    remaining = [row for row in prepared["rows"] if row["scenario_id"] in scenario_ids]
    if len(remaining) != len(scenario_ids):
        missing = sorted(set(scenario_ids) - {row["scenario_id"] for row in remaining})
        raise IsolationStop(f"unknown scenarios: {missing}")
    budget = budget or Budget()
    client = OpenAI(api_key=get_openai_api_key())
    results: dict[str, Any] = {}
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as hits:
            for row in remaining:
                bundle_hash_before = row["state_hash"]
                try:
                    call = call_interpretation(
                        client,
                        budget,
                        scenario_id=row["scenario_id"],
                        messages=row["messages"],
                        configured_model=DEFAULT_MODEL_NAME,
                    )
                except BudgetStop as exc:
                    results[row["scenario_id"]] = {"error": redact(str(exc)), "accepted": False, "stopped": True}
                    guard.assert_unchanged()
                    return {
                        "results": results,
                        "budget": budget,
                        "stopped": redact(str(exc)),
                        "provider_tripwire_hits": list(hits),
                        "save_guard_verified": True,
                    }
                payload = None
                parse_error = ""
                try:
                    payload = json.loads(call["text"])
                except json.JSONDecodeError as exc:
                    parse_error = f"JSON decode: {exc}"
                if not isinstance(payload, dict):
                    adapter = {"accepted": False, "status": "ABSTAIN", "errors": [parse_error or "payload was not an object"], "executed": False, "mutated_state": False}
                else:
                    adapter_result = validate_hand_authored_interpretation(
                        payload,
                        raw_input=row["utterance"],
                        discourse_focus=row.get("discourse_focus"),
                        canonical_referents=row.get("canonical_referents"),
                    )
                    adapter = adapter_result.as_dict()
                spec = _specs_by_id()[row["scenario_id"]]
                after = state_hash(spec["factory"]())
                if after != bundle_hash_before:
                    raise IsolationStop(f"state hash changed around the live call for {row['scenario_id']}")
                if adapter.get("executed") or adapter.get("mutated_state"):
                    raise IsolationStop("adapter reported execution or state mutation")
                results[row["scenario_id"]] = {
                    "raw_text": call["text"],
                    "payload": payload if isinstance(payload, dict) else None,
                    "parse_error": parse_error,
                    "adapter": adapter,
                    "accepted": bool(adapter.get("accepted")),
                    "usage": call["record"],
                    "stopped": False,
                }
            if hits:
                raise IsolationStop(f"unrelated provider path fired during live calls: {hits}")
        guard.assert_unchanged()
    return {
        "results": results,
        "budget": budget,
        "stopped": None,
        "provider_tripwire_hits": [],
        "save_guard_verified": True,
        "configured_model": DEFAULT_MODEL_NAME,
    }


def stage1_unusable(results: Mapping[str, Mapping[str, Any]]) -> bool:
    present = [results[sid] for sid in STAGE_1 if sid in results]
    return len(present) == len(STAGE_1) and all(_unusable(item) for item in present)


def assemble(prepared: Mapping[str, Any], live_results: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source in prepared["rows"]:
        live = live_results.get(source["scenario_id"])
        scores = score_live(
            source["scenario_id"],
            (live or {}).get("payload"),
            (live or {}).get("adapter"),
            raw_text=str((live or {}).get("raw_text") or ""),
        )
        rows.append(
            {
                "scenario_id": source["scenario_id"],
                "utterance": source["utterance"],
                "assistance_justified": source["assistance_justified"],
                "selected_resolver": source["selected_resolver"],
                "operation": source["operation"],
                "A_requested": source["A_requested"],
                "B_requested": source["B_requested"],
                "C_requested": source["C_requested"],
                "A_classification": source["A_classification"],
                "B_classification": source["B_classification"],
                "C_classification": source["C_classification"],
                "existing_signals": source["existing_signals"],
                "independent_checks": source["independent_checks"],
                "deterministic_gameplay": source["deterministic_gameplay"],
                "state_changed": source["state_changed"],
                "estimated_input_tokens": source["estimated_input_tokens"],
                "messages": source.get("messages"),
                "public_context": source.get("public_context"),
                "live_accepted": bool((live or {}).get("accepted")),
                "live_payload": (live or {}).get("payload"),
                "live_raw_text": (live or {}).get("raw_text"),
                "live_adapter": (live or {}).get("adapter"),
                "live_error": (live or {}).get("error") or (live or {}).get("parse_error"),
                "usage": (live or {}).get("usage"),
                "live_gameplay": scores["gameplay_usefulness"] if live else None,
                "live_authority": scores["authority_compliance"] if live else None,
                "live_schema": scores["schema_validity"] if live else None,
                "live_clarification_useful": scores["clarification_usefulness"] if live else None,
                "live_asserted_outcome": scores["asserted_outcome"] if live else None,
                "scores": scores if live else None,
            }
        )
    return rows
