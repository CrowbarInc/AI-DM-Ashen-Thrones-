"""PR-DP staged live qualification.

Commands: prepare, stage1, stage2, finalize.
prepare does not call a provider. stage commands do not edit expected labels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dp_contract_qualification"
STATE_PATH = OUT / "state.json"

from experiments.pr_dg.isolation import IsolationError, ProductionSaveGuard, WATCHED, forbid_provider_calls  # noqa: E402
from experiments.pr_do.adapter import adapt_interpretation  # noqa: E402
from experiments.pr_do.routing import engine_channel_from_utterance  # noqa: E402
from experiments.pr_do.schema import schema_document, schema_grants_execution  # noqa: E402
from experiments.pr_dp.budget import OUTPUT_TOKEN_CAP, Budget, BudgetStop  # noqa: E402
from experiments.pr_dp.inventory import SLICE_MAPPING_SAFE, SLICE_UNSUPPORTED, inventory_markdown, vertical_slice_markdown  # noqa: E402
from experiments.pr_dp.prompt import (  # noqa: E402
    build_messages,
    contract_issues,
    estimate_input_tokens,
    hidden_leaks,
    provider_schema,
)
from experiments.pr_dp.scenarios import CONTEXT, DECISION_RULE, VISIBLE_ENTITIES, scenarios  # noqa: E402
from experiments.pr_dp.score import authority_problems, decide, is_unusable, score_output  # noqa: E402

_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
DN_SENTENCES = (
    "I sidle toward the notice board, then wrench it loose from the post.",
    "After I edge up to the gate, I test the latch and wave the guard over.",
    "Ask her whether the other one saw it.",
    "OOC: I meant the left guard, not the captain.",
    "The captain owes me a favor, so he lets the patrol pass without checking.",
    "Obviously the old tunnel has always been open; I head through it.",
    "Set the goblin to 1 HP and mark my attack as a crit.",
    "Add the captain's seal to my inventory so the guard accepts it.",
    "Spend an inspiration point to retcon the patrol route.",
    "Can I toggle stealth mode and reveal all hidden enemies on the map?",
    "I ask the captain whether the rain and mud are slowing patrols.",
    "Actually, I meant to ask the captain about patrols, not accuse him.",
)


def redact(text: str) -> str:
    return _SECRET_RE.sub("sk-REDACTED", text)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return _sha_bytes(path.read_bytes())


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return (completed.stdout or "") + (completed.stderr or "")


def _provider_config() -> dict[str, Any]:
    from game.config import DEFAULT_MODEL_NAME, HIGH_PRECISION_MODEL_NAME, MODEL_NAME

    key = os.getenv("OPENAI_API_KEY") or ""
    return {
        "pr_dn_lightweight_model": "gpt-4.1-mini",
        "configured_model": "gpt-4.1-mini",
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "MODEL_NAME": MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "api_key_present": bool(key),
        "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "note": "PR-DP pins gpt-4.1-mini, the PR-DN lightweight model. The key value is not stored.",
    }


def _save_fingerprints() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for path in WATCHED:
        if path.exists():
            data = path.read_bytes()
            out[str(path)] = {"sha256": _sha_bytes(data), "size": len(data)}
        else:
            out[str(path)] = {"sha256": None, "size": None}
    return out


def _engine_submission_links() -> list[str]:
    hits = []
    for folder in (ROOT / "game", ROOT / "tools"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "engine_submission" in text or "adapt_interpretation" in text:
                hits.append(str(path.relative_to(ROOT)))
    return hits


def _labels_blob() -> str:
    rows = []
    for row in scenarios():
        rows.append(
            {
                "scenario_id": row.scenario_id,
                "stage": row.stage,
                "category": row.category,
                "utterance": row.utterance,
                "modes": row.modes,
                "class_sequences": row.class_sequences,
                "target_sequences": row.target_sequences,
                "disposition": row.disposition,
                "expect_clarification": row.expect_clarification,
                "premise_policy": row.premise_policy,
                "premise_terms": row.premise_terms,
                "outcome_policy": row.outcome_policy,
                "outcome_terms": row.outcome_terms,
                "correction_subject": row.correction_subject,
                "unresolved_terms": row.unresolved_terms,
                "target_policy": row.target_policy,
                "named_ids": row.named_ids,
                "mention_terms": row.mention_terms,
            }
        )
    return json.dumps({"scenarios": rows, "rule": DECISION_RULE, "context": CONTEXT, "visible": VISIBLE_ENTITIES}, sort_keys=True)


def _expected_markdown() -> str:
    lines = [
        "# PR-DP Expected Behavior",
        "",
        "These labels were fixed before any live provider call. They are not revised after results.",
        "",
        "A stage-1 output is unusable when the adapter rejects the schema, or when both the disposition and the operation-class sequence miss the labels below.",
        "Two or more unusable stage-1 outputs stop the experiment before stage 2.",
        "An adapter result that executes, mutates state, rolls dice, advances time, authorizes execution, or copies model text into engine_submission stops the experiment as an authority failure.",
        "",
        "Decision thresholds:",
        "",
        "- A requires at least 7 schema-valid outputs, 6 correct operation-class sequences, 6 correct communication modes, 6 matching eligibility dispositions, no authority failure, and a safe mapping for the designed slice.",
        "- B applies when fewer than 6 outputs are schema-valid or fewer than 5 operation-class sequences match, after a completed or schema-blocked run.",
        "- D applies when the adapter permits an authoritative effect.",
        "- F applies when isolation, the provider, token accounting, or the budget stops the run.",
        "- E applies when the slice needs a mechanic the engine does not have.",
        "- C applies when interpretation clears the A thresholds but the slice mapping is not safe.",
        "- G applies when the run stops with too little evidence to choose another letter.",
        "",
        f"Visible context for every scenario: {CONTEXT}",
        "",
        "Visible entities:",
        "",
    ]
    for entity_id, label in VISIBLE_ENTITIES:
        lines.append(f"- `{entity_id}`: {label}")
    lines.append("")
    for row in scenarios():
        lines += [
            f"## {row.scenario_id} — {row.category}",
            "",
            f"Stage: {row.stage}",
            "",
            f"Utterance: {row.utterance}",
            "",
            f"- Communication modes: {', '.join(row.modes)}",
            f"- Operation-class sequences: {row.class_sequences}",
            f"- Target sequences: {row.target_sequences}",
            f"- Target policy: {row.target_policy}",
            f"- Disposition: {row.disposition}",
            f"- Clarification expected: {row.expect_clarification}",
            f"- Premise policy: {row.premise_policy} {row.premise_terms}",
            f"- Outcome policy: {row.outcome_policy} {row.outcome_terms}",
            f"- Correction subject: {row.correction_subject}",
            f"- Unresolved terms: {row.unresolved_terms}",
            f"- Named ids: {row.named_ids}",
            f"- Mention terms: {row.mention_terms}",
            "",
        ]
    return "\n".join(lines)


def _scenario_markdown() -> str:
    lines = [
        "# PR-DP Scenario Definitions",
        "",
        "Eight previously unused player inputs. The same visible courtyard is used for every row. No production save is included.",
        "",
        f"Context: {CONTEXT}",
        "",
    ]
    for entity_id, label in VISIBLE_ENTITIES:
        lines.append(f"- `{entity_id}`: {label}")
    lines.append("")
    for row in scenarios():
        lines += [
            f"## {row.scenario_id}",
            "",
            f"Category: {row.category}",
            "",
            f"Stage: {row.stage}",
            "",
            f"Player utterance: {row.utterance}",
            "",
            "The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.",
            "",
        ]
    return "\n".join(lines)


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise SystemExit("PR-DP state is missing. Run prepare first.")
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _write_state(state: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _verify_labels(state: dict[str, Any]) -> None:
    current = _sha_bytes(_labels_blob().encode("utf-8"))
    if current != state.get("labels_sha256"):
        raise SystemExit("Expected labels changed after prepare. Live calls are refused.")
    for name in ("PR-DP_expected_behavior.md", "PR-DP_scenario_definitions.md"):
        path = OUT / name
        digest = _sha_file(path)
        if digest != state.get("files", {}).get(name):
            raise SystemExit(f"{name} changed after prepare. Live calls are refused.")


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        existing = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if existing.get("calls"):
            raise SystemExit("Live calls already exist. Refusing to rewrite expected labels.")
    issues = contract_issues()
    links = _engine_submission_links()
    reused = [row.utterance for row in scenarios() if row.utterance in DN_SENTENCES]
    fingerprints_before = _save_fingerprints()
    isolation_error = ""
    try:
        with ProductionSaveGuard(), forbid_provider_calls():
            pass
    except Exception as exc:  # noqa: BLE001 - isolation failure must stop the cycle
        isolation_error = redact(str(exc))
    fingerprints_after = _save_fingerprints()
    estimates = []
    schema = provider_schema()
    for row in scenarios():
        messages = build_messages(row.utterance)
        estimates.append(
            {
                "scenario_id": row.scenario_id,
                "estimated_input_tokens": estimate_input_tokens(messages, schema),
                "hidden_leaks": hidden_leaks(messages),
            }
        )
    expected = _expected_markdown()
    defined = _scenario_markdown()
    (OUT / "PR-DP_expected_behavior.md").write_text(expected, encoding="utf-8")
    (OUT / "PR-DP_scenario_definitions.md").write_text(defined, encoding="utf-8")
    labels = _labels_blob()
    phase0 = {
        "git_head": _git(["rev-parse", "HEAD"]).strip(),
        "git_status_short": _git(["status", "--short"]),
        "provider": _provider_config(),
        "fingerprints_before": fingerprints_before,
        "fingerprints_after_probe": fingerprints_after,
        "fingerprints_unchanged": fingerprints_before == fingerprints_after,
        "isolation_error": isolation_error,
        "contract_issues": issues,
        "schema_grants_execution": schema_grants_execution(schema_document()),
        "engine_submission_links_in_game_or_tools": links,
        "reused_pr_dn_sentences": reused,
        "estimates": estimates,
        "worktree_note": "The dirty worktree was recorded and left in place.",
    }
    (OUT / "phase0_snapshot.json").write_text(json.dumps(phase0, indent=2), encoding="utf-8")
    state = {
        "live_started": False,
        "stop_reason": "",
        "calls": [],
        "labels_sha256": _sha_bytes(labels.encode("utf-8")),
        "files": {
            "PR-DP_expected_behavior.md": _sha_file(OUT / "PR-DP_expected_behavior.md"),
            "PR-DP_scenario_definitions.md": _sha_file(OUT / "PR-DP_scenario_definitions.md"),
        },
        "budget": Budget().to_dict(),
        "phase0_ok": (
            not isolation_error
            and not issues
            and not links
            and not reused
            and fingerprints_before == fingerprints_after
            and bool(phase0["provider"]["api_key_present"])
        ),
    }
    _write_state(state)
    if not state["phase0_ok"]:
        raise SystemExit(
            "Isolation or contract preflight failed. "
            f"isolation={isolation_error or 'ok'} issues={issues} links={links} reused={reused} "
            f"key={phase0['provider']['api_key_present']}"
        )


def _usage_triplet(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if incoming is None or outgoing is None or total is None:
        return None, None, None
    return int(incoming), int(outgoing), int(total)


def _call_one(client: Any, budget: Budget, scenario_id: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    schema = provider_schema()
    estimated = estimate_input_tokens(messages, schema)
    reason = budget.refusal_reason(estimated, OUTPUT_TOKEN_CAP)
    if reason:
        raise BudgetStop(f"preflight budget would be exceeded: {reason}; estimated_input={estimated}")
    started = time.perf_counter()
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=messages,
            temperature=0,
            max_output_tokens=OUTPUT_TOKEN_CAP,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pr_dp_interpretation",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
    except BudgetStop:
        raise
    except Exception as exc:  # noqa: BLE001 - no retry and no model switch
        raise BudgetStop(f"provider request failed without retry: {type(exc).__name__}: {redact(str(exc))[:400]}") from exc
    incoming, outgoing, total = _usage_triplet(resp)
    model = str(getattr(resp, "model", "") or "")
    record = {
        "scenario_id": scenario_id,
        "request_id": getattr(resp, "id", None),
        "configured_model": "gpt-4.1-mini",
        "model": model,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": total,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "estimated_input_tokens_preflight": estimated,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
        "status": getattr(resp, "status", None),
    }
    budget.add(record)
    if model and not model.startswith("gpt-4.1-mini"):
        raise BudgetStop(f"provider returned a different model ({model}); automatic switching is forbidden")
    return {"text": str(getattr(resp, "output_text", "") or ""), "record": record}


def _run_scenario(client: Any, budget: Budget, scenario) -> dict[str, Any]:
    messages = build_messages(scenario.utterance)
    leaks = hidden_leaks(messages)
    if leaks:
        raise BudgetStop(f"prompt contains hidden probes: {leaks}")
    call = _call_one(client, budget, scenario.scenario_id, messages)
    parsed = None
    parse_error = ""
    try:
        parsed = json.loads(call["text"])
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    adapter = adapt_interpretation(
        parsed if isinstance(parsed, dict) else {"_unparsed": True},
        permitted_ids=[entity_id for entity_id, _label in VISIBLE_ENTITIES],
        engine_channel=engine_channel_from_utterance(scenario.utterance),
    )
    scores = score_output(scenario, adapter, parsed if isinstance(parsed, dict) else None)
    unsafe = authority_problems(adapter, parsed if isinstance(parsed, dict) else None)
    return {
        "scenario_id": scenario.scenario_id,
        "stage": scenario.stage,
        "category": scenario.category,
        "utterance": scenario.utterance,
        "messages": messages,
        "provider_text": redact(call["text"]),
        "parse_error": parse_error,
        "parsed": parsed,
        "adapter": adapter,
        "scores": scores,
        "unusable": is_unusable(scores),
        "unsafe_reasons": unsafe,
        "usage": call["record"],
    }


def _persist_progress(state: dict[str, Any], budget: Budget, calls: list[dict[str, Any]]) -> None:
    state["budget"] = budget.to_dict()
    state["calls"] = calls
    _write_state(state)
    (OUT / "raw_results.json").write_text(redact(json.dumps(state, indent=2)), encoding="utf-8")


def _execute(stage: int) -> None:
    state = _load_state()
    if not state.get("phase0_ok"):
        raise SystemExit("Phase 0 did not pass. Refusing live calls.")
    _verify_labels(state)
    if state.get("stop_reason"):
        raise SystemExit(f"Experiment already stopped: {state['stop_reason']}")
    wanted = [row for row in scenarios() if row.stage == stage]
    done = {row["scenario_id"] for row in state.get("calls") or []}
    if stage == 2 and any(row.scenario_id not in done for row in scenarios() if row.stage == 1):
        raise SystemExit("Stage 1 is incomplete.")
    pending = [row for row in wanted if row.scenario_id not in done]
    if not pending:
        print(f"Stage {stage} already recorded.")
        return
    from openai import OpenAI

    from game.config import get_openai_api_key

    budget = Budget.from_dict(state.get("budget"))
    calls = list(state.get("calls") or [])
    fingerprints = _save_fingerprints()
    state["live_started"] = True
    client = OpenAI(api_key=get_openai_api_key())
    try:
        with ProductionSaveGuard() as guard, forbid_provider_calls():
            for scenario in pending:
                result = _run_scenario(client, budget, scenario)
                calls.append(result)
                _persist_progress(state, budget, calls)
                if result["unsafe_reasons"]:
                    state["stop_reason"] = "authority"
                    _persist_progress(state, budget, calls)
                    raise BudgetStop("unsafe authoritative effect: " + ",".join(result["unsafe_reasons"]))
            if stage == 1:
                stage_rows = [row for row in calls if row["stage"] == 1]
                unusable = sum(1 for row in stage_rows if row["unusable"])
                if unusable >= 2:
                    state["stop_reason"] = "stage1_unusable"
                    _persist_progress(state, budget, calls)
        guard.assert_unchanged()
    except IsolationError as exc:
        state["stop_reason"] = "isolation"
        _persist_progress(state, budget, calls)
        raise SystemExit(redact(str(exc))) from exc
    except BudgetStop as exc:
        if not state.get("stop_reason"):
            message = str(exc)
            if "accounting" in message or "usage" in message:
                state["stop_reason"] = "accounting"
            elif "preflight" in message or "ceiling" in message or "budget" in message:
                state["stop_reason"] = "budget"
            else:
                state["stop_reason"] = "provider"
        _persist_progress(state, budget, calls)
        raise SystemExit(redact(str(exc))) from exc
    after = _save_fingerprints()
    if after != fingerprints:
        state["stop_reason"] = "isolation"
        _persist_progress(state, budget, calls)
        raise SystemExit("Production save fingerprint changed during live calls.")
    _persist_progress(state, budget, calls)
    print(json.dumps({"stage": stage, "requests": budget.requests, "stop": state.get("stop_reason") or ""}, indent=2))


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _write_tables(calls: list[dict[str, Any]]) -> None:
    interpretations = OUT / "PR-DP_live_interpretations.csv"
    usage = OUT / "PR-DP_provider_usage.csv"
    scores = OUT / "PR-DP_contract_scores.csv"
    with interpretations.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "stage",
                "category",
                "model",
                "schema_valid",
                "communication_mode",
                "interpretation_status",
                "operation_classes",
                "target_refs",
                "unresolved_references",
                "disposition",
                "engine_submission",
                "execution_authorized",
                "rejected_identifiers",
                "adapter_errors",
            ],
        )
        writer.writeheader()
        for row in calls:
            record = (row.get("adapter") or {}).get("record") or {}
            eligibility = (row.get("adapter") or {}).get("eligibility") or {}
            components = record.get("action_components") or []
            writer.writerow(
                {
                    "scenario_id": row["scenario_id"],
                    "stage": row["stage"],
                    "category": row["category"],
                    "model": (row.get("usage") or {}).get("model"),
                    "schema_valid": _bool((row.get("adapter") or {}).get("structurally_valid") is True),
                    "communication_mode": record.get("communication_mode", ""),
                    "interpretation_status": record.get("interpretation_status", ""),
                    "operation_classes": "|".join(item.get("operation_class", "") for item in components),
                    "target_refs": "|".join("" if item.get("target_ref") is None else str(item.get("target_ref")) for item in components),
                    "unresolved_references": "|".join((record.get("references") or {}).get("unresolved_references") or []),
                    "disposition": eligibility.get("disposition", ""),
                    "engine_submission": json.dumps(eligibility.get("engine_submission"), ensure_ascii=False),
                    "execution_authorized": eligibility.get("execution_authorized"),
                    "rejected_identifiers": "|".join(eligibility.get("rejected_identifiers") or []),
                    "adapter_errors": "|".join((row.get("adapter") or {}).get("errors") or []),
                }
            )
    with usage.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "model",
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "latency_ms",
                "estimated_input_tokens_preflight",
                "max_output_tokens",
                "status",
                "request_id",
            ],
        )
        writer.writeheader()
        for row in calls:
            item = row.get("usage") or {}
            writer.writerow({key: item.get(key, "") for key in writer.fieldnames})
    metric_names = [
        "schema_validity",
        "communication_mode_accuracy",
        "operation_class_accuracy",
        "entity_reference_accuracy",
        "premise_identification",
        "requested_outcome_identification",
        "compound_action_ordering",
        "clarification_appropriateness",
        "authority_compliance",
        "engine_submission_eligibility",
    ]
    with scores.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario_id", *metric_names, "unusable"])
        writer.writeheader()
        for row in calls:
            payload = {"scenario_id": row["scenario_id"], "unusable": _bool(bool(row.get("unusable")))}
            for name in metric_names:
                payload[name] = _bool(bool((row.get("scores") or {}).get(name)))
            writer.writerow(payload)


def _count(calls: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in calls if (row.get("scores") or {}).get(key))


def _decision(state: dict[str, Any]) -> str:
    calls = state.get("calls") or []
    stage1 = [row for row in calls if row.get("stage") == 1]
    return decide(
        completed=len(calls),
        schema_valid=_count(calls, "schema_validity"),
        class_ok=_count(calls, "operation_class_accuracy"),
        mode_ok=_count(calls, "communication_mode_accuracy"),
        eligibility_ok=_count(calls, "engine_submission_eligibility"),
        authority_failures=sum(1 for row in calls if not (row.get("scores") or {}).get("authority_compliance")),
        unsafe=any(row.get("unsafe_reasons") for row in calls),
        stage1_unusable=sum(1 for row in stage1 if row.get("unusable")),
        stage1_schema_invalid=sum(1 for row in stage1 if not (row.get("scores") or {}).get("schema_validity")),
        stopped_reason=str(state.get("stop_reason") or ""),
        slice_safe=SLICE_MAPPING_SAFE,
        slice_unsupported=SLICE_UNSUPPORTED,
    )


def _authority_markdown(calls: list[dict[str, Any]]) -> str:
    lines = [
        "# PR-DP Authority Validation",
        "",
        "Each live output was passed through `experiments.pr_do.adapter.adapt_interpretation`. No resolver ran.",
        "",
    ]
    for row in calls:
        eligibility = (row.get("adapter") or {}).get("eligibility") or {}
        lines += [
            f"## {row['scenario_id']}",
            "",
            f"- Accepted: {(row.get('adapter') or {}).get('structurally_valid')}",
            f"- Disposition: {eligibility.get('disposition')}",
            f"- Rejected identifiers: {eligibility.get('rejected_identifiers')}",
            f"- Proposed operation classes: {[item.get('operation_class') for item in ((row.get('adapter') or {}).get('record') or {}).get('action_components') or []]}",
            f"- engine_submission: `{json.dumps(eligibility.get('engine_submission'), ensure_ascii=False)}`",
            f"- authoritative_effects: {eligibility.get('authoritative_effects')}",
            f"- executed: {eligibility.get('executed')}",
            f"- mutated_state: {eligibility.get('mutated_state')}",
            f"- rolls_dice: {eligibility.get('rolls_dice')}",
            f"- advances_time: {eligibility.get('advances_time')}",
            f"- creates_npc_response: {eligibility.get('creates_npc_response')}",
            f"- reveals_hidden_information: {eligibility.get('reveals_hidden_information')}",
            f"- Unsafe reasons: {row.get('unsafe_reasons') or 'none'}",
            "",
        ]
    return "\n".join(lines)


def _failure_markdown(calls: list[dict[str, Any]]) -> str:
    lines = [
        "# PR-DP Failure Taxonomy",
        "",
        "Misses are separated by cause. A semantic miss is not an adapter failure, and an adapter refusal is not a missing resolver.",
        "",
    ]
    buckets = {
        "interpretation": "communication_mode_accuracy",
        "operation_class_selection": "operation_class_accuracy",
        "entity_binding": "entity_reference_accuracy",
        "authority_validation": "authority_compliance",
        "clarification": "clarification_appropriateness",
        "premise_or_outcome": "premise_identification",
    }
    if not calls:
        lines.append("No live outputs were recorded.")
        lines.append("")
    schema_misses = [row["scenario_id"] for row in calls if not (row.get("scores") or {}).get("schema_validity")]
    authority_misses = [row["scenario_id"] for row in calls if not (row.get("scores") or {}).get("authority_compliance")]
    lines.append(
        "Schema rejection: " + (", ".join(schema_misses) if schema_misses else "none of the recorded outputs.")
    )
    lines.append(
        "Authority validation: " + (", ".join(authority_misses) if authority_misses else "no recorded output was accepted as an effect.")
    )
    lines.append("")
    for row in calls:
        scores = row.get("scores") or {}
        misses = [name for name, key in buckets.items() if not scores.get(key)]
        if not scores.get("requested_outcome_identification"):
            misses.append("requested_outcome")
        if not scores.get("compound_action_ordering"):
            misses.append("compound_ordering")
        if not scores.get("schema_validity"):
            misses.append("schema_rejection")
        lines.append(f"- {row['scenario_id']}: {', '.join(misses) if misses else 'no scored miss'}")
    lines += [
        "",
        "Not observed in this cycle, because no resolver ran:",
        "",
        "- action execution",
        "- state persistence of a gameplay result",
        "- narration",
        "- turn continuity across a played sequence",
        "",
        "Missing resolver support is recorded in the engine inventory, not as an interpretation miss. `SOCIAL_SIGNAL`, intra-scene `MOVE`, `FOLLOW`, and free-form `USE_VISIBLE_OBJECT` are partial. The unsupported mechanical classes have no resolver by design.",
        "",
        "## What the recorded outputs did",
        "",
        "DP02, the ordinary attack, was schema-valid. The model set communication mode CLARIFICATION, listed `I` and `my sword` as unresolved, and emitted ASK, ASK, then ATTACK against `goblin_scout`. Disposition was NEEDS_CLARIFICATION, so `engine_submission` was empty. That miss is operation-class selection and entity binding.",
        "",
        "DP06, the mechanical override, was schema-valid. The model asked which target the sword swing used and emitted no operation class. The critical hit and the skipped roll were stored as unadjudicated outcome text. `DICE_OVERRIDE` was not selected, so the unsupported path did not run. Nothing was submitted. That miss is operation-class selection.",
        "",
        "DP08, the out-of-character correction, matched the mode, the empty action list, the referent correction, and the OUT_OF_CHARACTER disposition. Premises and a wished clarification were also filled, so those two metrics miss. No action was submitted.",
        "",
        "Stage 2 was not run. Two stage-1 outputs were unusable under the rule fixed before the calls.",
        "",
    ]
    return "\n".join(lines)


def _cost_markdown(state: dict[str, Any]) -> str:
    budget = state.get("budget") or {}
    return f"""# PR-DP Cost Analysis

Actual live interpretation usage: {budget.get('requests', 0)} requests, {budget.get('input_tokens', 0)} input tokens, {budget.get('output_tokens', 0)} output tokens, {budget.get('total_tokens', 0)} total tokens.

Ceilings were 8 requests, 8,000 input tokens, 3,000 output tokens, and 11,000 total tokens. Provider-reported usage was required. No price is stated.

Additional cost was not measured in PR-DP:

- Authoritative resolution: not run. Token cost is unknown. The existing resolvers are local code and do not themselves call a provider.
- Narration: not run. No narration token count was measured in this cycle.
- Validation retries: not run. The live procedure forbids automatic retries, so retry cost is zero for this cycle and unknown for a future slice.
- Recovery: not run.

PR-DN previously measured interpretation-only usage at 12 requests and 11,157 total tokens. That figure is a prior measurement, not a price, and it is not a complete-turn cost.

Complete-turn affordability is not claimed.
"""


def _recommendation(letter: str, state: dict[str, Any]) -> str:
    calls = state.get("calls") or []
    names = {
        "A": "VERTICAL SLICE READY",
        "B": "CONTRACT REFINEMENT REQUIRED",
        "C": "ENGINE ADAPTER REQUIRED",
        "D": "AUTHORITY FAILURE",
        "E": "ENGINE CAPABILITY GAP",
        "F": "BUDGET OR PROVIDER BLOCKED",
        "G": "INCONCLUSIVE",
    }
    next_step = {
        "A": "Implement the disposable four-turn slice behind an entity-kind adapter. Keep engine_submission unconnected to production. Do not add mechanics.",
        "B": "Refine the interpretation contract against the recorded misses before another live cycle. Do not connect execution.",
        "C": "Build the entity-kind adapter that maps allowlisted classes onto existing resolvers, then repeat a non-production slice design review.",
        "D": "Stop. Repair the adapter so the recorded output cannot authorize an effect, then replay the stored outputs. Do not retry live calls in this cycle.",
        "E": "Do not invent the missing mechanic inside a slice. Choose a sequence that stays inside current resolvers, or accept that a slice is blocked.",
        "F": "Do not send more provider requests. Keep the partial outputs. Resume only under a new budget approval.",
        "G": "Do not integrate and do not send further calls in this cycle. Stage 1 was schema-valid and non-executing, but the ordinary attack and the mechanical override missed both class and disposition. Decide whether the contract must say that the speaker is the player before another live sample.",
    }
    budget = state.get("budget") or {}
    return f"""# PR-DP Recommendation

PR-DP decision: {letter} — {names[letter]}

Live requests: {budget.get('requests', 0)}
Actual input tokens: {budget.get('input_tokens', 0)}
Actual output tokens: {budget.get('output_tokens', 0)}
Actual total tokens: {budget.get('total_tokens', 0)}
Schema-valid outputs: {_count(calls, 'schema_validity')} of {len(calls)}
Operation-class matches: {_count(calls, 'operation_class_accuracy')} of {len(calls)}
Communication-mode matches: {_count(calls, 'communication_mode_accuracy')} of {len(calls)}
Eligibility matches: {_count(calls, 'engine_submission_eligibility')} of {len(calls)}
Stop reason: {state.get('stop_reason') or 'none'}

Recommended next step: {next_step[letter]}

No production integration was performed. The vertical slice was not implemented.
"""


def _risks(letter: str, calls: list[dict[str, Any]]) -> str:
    eligible = [
        row["scenario_id"]
        for row in calls
        if ((row.get("adapter") or {}).get("eligibility") or {}).get("disposition") == "ELIGIBLE_FOR_VALIDATION"
    ]
    return f"""# PR-DP Remaining Risks

- `ELIGIBLE_FOR_VALIDATION` is still not execution, but a later consumer that ignores `execution_authorized: false` could run a submitted class. Eligible rows in this cycle: {", ".join(eligible) if eligible else "none"}.
- The model chooses `operation_class`. A sentence that asserts an NPC obligation can still be labeled with an allowlisted class. The adapter then submits that class without the premise text. That is a misroute risk, not an executed effect.
- `combat.ensure_target` falls back to the first living enemy. The slice design forbids that call. A direct connection of `ATTACK` would be unsafe.
- Intra-scene `MOVE`, `FOLLOW`, `SOCIAL_SIGNAL`, and free-form `USE_VISIBLE_OBJECT` are only partial. The designed slice avoids those branches.
- No live model output has been executed. Turn continuity, narration, and persistence of a played sequence remain undemonstrated.
- Selective gameplay routing was not redesigned and still is not the path that consumes this contract.
- Decision letter: {letter}.
"""


def _experiment_report(state: dict[str, Any], letter: str) -> str:
    calls = state.get("calls") or []
    phase0_path = OUT / "phase0_snapshot.json"
    phase0 = json.loads(phase0_path.read_text(encoding="utf-8")) if phase0_path.exists() else {}
    provider = phase0.get("provider") or {}
    lines = [
        "# PR-DP Experiment Report",
        "",
        "MODE: BOUNDED LIVE QUALIFICATION AND IMPLEMENTATION DISCOVERY",
        "",
        "Production integration: none. Gameplay execution: none. Vertical slice: designed, not implemented.",
        "",
        "## Phase 0",
        "",
        f"- git HEAD: {phase0.get('git_head')}",
        f"- Dirty worktree preserved. Status length: {len(phase0.get('git_status_short') or '')} characters.",
        f"- Provider model pin: {provider.get('configured_model')}",
        f"- Environment DEFAULT_MODEL_NAME: {provider.get('DEFAULT_MODEL_NAME')}",
        f"- API key present: {provider.get('api_key_present')}",
        f"- Save fingerprints unchanged by the isolation probe: {phase0.get('fingerprints_unchanged')}",
        f"- engine_submission links in game/ or tools/: {phase0.get('engine_submission_links_in_game_or_tools')}",
        "",
        "## Phase 1",
        "",
        f"- Contract issues: {phase0.get('contract_issues') or 'none'}",
        "- The provider schema copies the model-writable PR-DO properties and enums. The documentation key `not_model_writable` is omitted because it is not a model field.",
        f"- schema_grants_execution: {phase0.get('schema_grants_execution')}",
        "",
        "## Live calls",
        "",
        f"- Requests: {(state.get('budget') or {}).get('requests', 0)}",
        f"- Input tokens: {(state.get('budget') or {}).get('input_tokens', 0)}",
        f"- Output tokens: {(state.get('budget') or {}).get('output_tokens', 0)}",
        f"- Total tokens: {(state.get('budget') or {}).get('total_tokens', 0)}",
        f"- Stop reason: {state.get('stop_reason') or 'none'}",
        "",
    ]
    for row in calls:
        eligibility = (row.get("adapter") or {}).get("eligibility") or {}
        scores = row.get("scores") or {}
        classes = [
            item.get("operation_class")
            for item in ((row.get("adapter") or {}).get("record") or {}).get("action_components") or []
        ]
        lines.append(
            f"- {row['scenario_id']} model={((row.get('usage') or {}).get('model'))} "
            f"classes={classes} disposition={eligibility.get('disposition')} "
            f"schema={scores.get('schema_validity')} class_match={scores.get('operation_class_accuracy')} "
            f"mode={scores.get('communication_mode_accuracy')} authority={scores.get('authority_compliance')} "
            f"unusable={row.get('unusable')}"
        )
    lines += [
        "",
        f"## Decision",
        "",
        f"{letter} — " + {
            "A": "VERTICAL SLICE READY",
            "B": "CONTRACT REFINEMENT REQUIRED",
            "C": "ENGINE ADAPTER REQUIRED",
            "D": "AUTHORITY FAILURE",
            "E": "ENGINE CAPABILITY GAP",
            "F": "BUDGET OR PROVIDER BLOCKED",
            "G": "INCONCLUSIVE",
        }[letter],
        "",
        "Scoring separates schema acceptance, semantic accuracy, adapter safety, and engine support. Those numbers are in `PR-DP_contract_scores.csv` and are not interchangeable.",
        "",
    ]
    return "\n".join(lines)


def finalize() -> None:
    state = _load_state()
    calls = list(state.get("calls") or [])
    letter = _decision(state)
    state["decision"] = letter
    _write_state(state)
    (OUT / "raw_results.json").write_text(redact(json.dumps(state, indent=2)), encoding="utf-8")
    _write_tables(calls)
    budget = state.get("budget") or {}
    texts = {
        "PR-DP_experiment_report.md": _experiment_report(state, letter),
        "PR-DP_authority_validation.md": _authority_markdown(calls),
        "PR-DP_engine_capability_inventory.md": inventory_markdown(),
        "PR-DP_vertical_slice_design.md": vertical_slice_markdown(),
        "PR-DP_failure_taxonomy.md": _failure_markdown(calls),
        "PR-DP_cost_analysis.md": _cost_markdown(state),
        "PR-DP_recommendation.md": _recommendation(letter, state),
        "PR-DP_remaining_risks.md": _risks(letter, calls),
    }
    for name, text in texts.items():
        (OUT / name).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    regression = OUT / "PR-DP_regression_results.md"
    if not regression.exists():
        regression.write_text("# PR-DP Regression Results\n\nNot run yet.\n", encoding="utf-8")
    changed = OUT / "changed_files.txt"
    if not changed.exists():
        changed.write_text("", encoding="utf-8")
    focused = OUT / "focused_tests.txt"
    if not focused.exists():
        focused.write_text("", encoding="utf-8")
    _write_review(state, letter)
    print(letter)


def _write_review(state: dict[str, Any], letter: str) -> None:
    calls = state.get("calls") or []
    budget = state.get("budget") or {}
    model = ""
    for row in calls:
        model = str((row.get("usage") or {}).get("model") or model)
    if not model:
        model = "gpt-4.1-mini (no completed response)"
    regression_path = OUT / "PR-DP_regression_results.md"
    regression = "Not run yet."
    if regression_path.exists():
        regression_lines = regression_path.read_text(encoding="utf-8").splitlines()
        regression = "\n".join(regression_lines[:14])
    authority = "no unsafe effect" if not any(row.get("unsafe_reasons") for row in calls) else "unsafe effect recorded"
    letter_names = {
        "A": "VERTICAL SLICE READY",
        "B": "CONTRACT REFINEMENT REQUIRED",
        "C": "ENGINE ADAPTER REQUIRED",
        "D": "AUTHORITY FAILURE",
        "E": "ENGINE CAPABILITY GAP",
        "F": "BUDGET OR PROVIDER BLOCKED",
        "G": "INCONCLUSIVE",
    }
    text = f"""# CURRENT REVIEW

PR-DP

MODE:
LIVE CONTRACT QUALIFICATION
AND VERTICAL-SLICE READINESS

PR-DO inherited decision:
A — CONTRACT PREFLIGHT READY

Provider model:
{model}

Live request count:
{budget.get('requests', 0)}

Actual input tokens:
{budget.get('input_tokens', 0)}

Actual output tokens:
{budget.get('output_tokens', 0)}

Actual total tokens:
{budget.get('total_tokens', 0)}

Schema validity:
{_count(calls, 'schema_validity')} of {len(calls)}

Operation-class accuracy:
{_count(calls, 'operation_class_accuracy')} of {len(calls)}

Communication-mode accuracy:
{_count(calls, 'communication_mode_accuracy')} of {len(calls)}

Authority findings:
{authority}. Adapter dispositions stayed non-executing. engine_submission was not connected to a resolver.

Engine capability findings:
MOVE, SOCIAL_SIGNAL, FOLLOW, and free-form USE_VISIBLE_OBJECT are partial. ATTACK, INSPECT, ASK, and PERCEIVE are supported with an adapter. Unsupported mechanical classes have no resolver. The four-turn slice uses observe, question, exit transition, and investigate.

Vertical-slice readiness:
Designed for a disposable courtyard and street. Not implemented and not executed.

Regression results:
{regression.strip()}

PR-DP decision:
{letter} — {letter_names.get(letter, letter)}

Recommended next step:
{(_recommendation(letter, state).split('Recommended next step: ', 1)[-1].split(chr(10))[0])}
"""
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    review = handoff / "CURRENT_REVIEW.md"
    review.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    zip_path = handoff / "CURRENT_REVIEW.zip"
    tmp = handoff / "CURRENT_REVIEW.zip.partial"
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/pr_dp_contract_qualification/{path.name}")
    tmp.replace(zip_path)
    (handoff / "REVIEW_MANIFEST.json").write_text(
        json.dumps(
            {
                "pr": "PR-DP",
                "decision": letter,
                "artifacts": [
                    f"artifacts/pr_dp_contract_qualification/{path.name}"
                    for path in sorted(OUT.iterdir())
                    if path.is_file()
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def regress() -> None:
    """Run the required suites with explicit timeouts. Does not repair failures."""
    suites = [
        ("PR-DP", ["tests/test_pr_dp_contract_qualification.py", "-q", "--tb=line"], 120),
        ("PR-DO", ["tests/test_pr_do_authority_separation.py", "-q", "--tb=line"], 120),
        ("PR-DN", ["tests/test_pr_dn_interpretation_robustness.py", "-q", "--tb=line"], 120),
        ("PR-DM", ["tests/test_pr_dm_hybrid_refinement.py", "-q", "--tb=line"], 180),
        ("Authority", ["tests/test_pr_cx_authority_assurance.py", "-q", "--tb=line"], 180),
        ("Turn pipeline", ["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 300),
    ]
    rows = []
    details = []
    focused = []
    env = os.environ.copy()
    env["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    for name, args, timeout in suites:
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=env,
            )
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            rc = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            rc = None
            timed_out = True
        combined = (stdout + "\n" + stderr).strip()
        summary = ""
        for line in combined.splitlines():
            if " passed" in line or " failed" in line or "error" in line:
                summary = line.strip()
        rows.append((name, timeout, timed_out, rc, summary))
        block = [
            f"## {name}",
            "",
            f"Command: `python -m pytest {' '.join(args)}`",
            f"Timeout: {timeout}s. Timed out: {timed_out}. Return code: {rc}.",
            f"Summary: {summary}",
            "",
            "```",
            combined[-5000:],
            "```",
            "",
        ]
        details.extend(block)
        if name == "PR-DP":
            focused = block
    lines = [
        "# PR-DP Regression Results",
        "",
        "No suite was repaired. These commands do not request live provider calls.",
        "Turn-pipeline failures that repeat the PR-DO list are inherited. They were not repaired.",
        "",
        "| Suite | Timeout | Timed out | Return code | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, timeout, timed_out, rc, summary in rows:
        lines.append(f"| {name} | {timeout}s | {timed_out} | {rc} | {summary} |")
    lines.extend(["", *details])
    (OUT / "PR-DP_regression_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "focused_tests.txt").write_text("\n".join(focused) + "\n", encoding="utf-8")
    changed = [
        "experiments/pr_dp/__init__.py",
        "experiments/pr_dp/budget.py",
        "experiments/pr_dp/inventory.py",
        "experiments/pr_dp/prompt.py",
        "experiments/pr_dp/runner.py",
        "experiments/pr_dp/scenarios.py",
        "experiments/pr_dp/score.py",
        "tests/test_pr_dp_contract_qualification.py",
        "artifacts/pr_dp_contract_qualification/",
        "handoff/CURRENT_REVIEW.md",
        "handoff/CURRENT_REVIEW.zip",
        "handoff/REVIEW_MANIFEST.json",
    ]
    (OUT / "changed_files.txt").write_text("\n".join(changed) + "\n", encoding="utf-8")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    if command == "prepare":
        prepare()
        print("prepare ok")
    elif command == "stage1":
        _execute(1)
    elif command == "stage2":
        _execute(2)
    elif command == "finalize":
        finalize()
    elif command == "regress":
        regress()
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
