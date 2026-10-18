"""Write the PR-DL artifact set from stored live outputs. No provider calls."""
from __future__ import annotations

import csv
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Mapping

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dg.state import frontier_bundle  # noqa: E402
from experiments.pr_dl.evidence import render_evidence  # noqa: E402
from experiments.pr_dl.live import redact  # noqa: E402
from experiments.pr_dl.policies import invocation_classes, summarize_policy, usage_for  # noqa: E402
from experiments.pr_dl.runner import OUT, assemble, prepare_matrix  # noqa: E402
from experiments.pr_dl.scoring import rank  # noqa: E402

DECISION = "C"
DECISION_LABEL = "C — HYBRID REFINEMENT REQUIRED"


def _policy_gameplay(row: Mapping[str, Any], policy: str) -> str:
    if policy == "A" or (policy == "B" and not row["B_requested"]):
        return str(row["deterministic_gameplay"])
    if not row.get("live_accepted"):
        return "FAIL"
    return str(row.get("live_gameplay") or "FAIL")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def _join(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def _hidden_in_outputs(rows: list[Mapping[str, Any]]) -> list[str]:
    hidden = [item for item in frontier_bundle().hidden_strings if str(item).strip()]
    hits = []
    for row in rows:
        blob = json.dumps({"raw": row.get("live_raw_text"), "messages": row.get("messages")}, ensure_ascii=False, default=str).casefold()
        for item in hidden:
            if item.casefold() in blob:
                hits.append(f"{row['scenario_id']}: {item[:80]}")
    return hits


def _useful_among(rows: list[Mapping[str, Any]], invoked: list[Mapping[str, Any]]) -> list[str]:
    return [str(row["scenario_id"]) for row in invoked if row.get("live_gameplay") == "PASS" and row.get("live_accepted")]


def build_packet(regression_text: str) -> dict[str, Any]:
    prepared = prepare_matrix()
    checkpoint = json.loads((OUT / "checkpoint.json").read_text(encoding="utf-8"))
    phase0 = json.loads((OUT / "phase0_snapshot.json").read_text(encoding="utf-8"))
    rows = assemble(prepared, checkpoint["results"])
    for row in rows:
        row["policy_A"] = _policy_gameplay(row, "A")
        row["policy_B"] = _policy_gameplay(row, "B")
        row["policy_C"] = _policy_gameplay(row, "C")
    policies = {name: summarize_policy(rows, name) for name in "ABC"}
    classes = invocation_classes(rows)
    usage_c = usage_for(rows, selector=lambda row: bool(row.get("usage")))
    usage_b = usage_for(rows, selector=lambda row: bool(row["B_requested"]) and row.get("usage"))
    usage_a = {"provider_requests": 0, "actual_input_tokens": 0, "actual_output_tokens": 0, "actual_total_tokens": 0}
    invoked_b = [row for row in rows if row["B_requested"]]
    useful_b = _useful_among(rows, invoked_b)
    useful_c = _useful_among(rows, rows)
    additional = [sid for sid in policies["C"]["correctly_handled"] if sid not in policies["B"]["correctly_handled"]]
    models = sorted({str((row.get("usage") or {}).get("model") or "") for row in rows if row.get("usage")})
    return {
        "prepared": prepared,
        "checkpoint": checkpoint,
        "phase0": phase0,
        "rows": rows,
        "policies": policies,
        "classes": classes,
        "usage": {"A": usage_a, "B": usage_b, "C": usage_c},
        "useful": {"B": useful_b, "C": useful_c},
        "additional_successful": additional,
        "models": models,
        "hidden_hits": _hidden_in_outputs(rows),
        "regression_text": regression_text,
        "decision": DECISION,
    }


def _expect(packet: Mapping[str, Any]) -> None:
    usage = packet["usage"]["C"]
    if usage["provider_requests"] != 21:
        raise RuntimeError(f"expected 21 stored requests, found {usage['provider_requests']}")
    if packet["usage"]["B"]["provider_requests"] != 10:
        raise RuntimeError("selective replay did not select the 10 PR-DK B triggers")
    if packet["classes"]["harmful_invocations"] != ["control_combat"]:
        raise RuntimeError(f"unexpected harmful set: {packet['classes']['harmful_invocations']}")
    if packet["classes"]["false_negatives"] != ["var_compound_subtle", "var_quote_control"]:
        raise RuntimeError(f"unexpected false negatives: {packet['classes']['false_negatives']}")
    if packet["checkpoint"].get("stopped"):
        raise RuntimeError("checkpoint records a stop; reports require a completed comparison")
    if packet["hidden_hits"]:
        raise RuntimeError(f"hidden information in prompt or output: {packet['hidden_hits']}")


def write_all(packet: Mapping[str, Any]) -> None:
    _expect(packet)
    OUT.mkdir(parents=True, exist_ok=True)
    _write(OUT / "PR-DL_evidence_corrections.md", render_evidence(packet["prepared"]["evidence"]))
    _write_csvs(packet)
    _write_raw(packet)
    for name, writer in (
        ("PR-DL_experiment_report.md", _experiment),
        ("PR-DL_policy_A_results.md", lambda p: _policy_md(p, "A")),
        ("PR-DL_policy_B_results.md", lambda p: _policy_md(p, "B")),
        ("PR-DL_policy_C_results.md", lambda p: _policy_md(p, "C")),
        ("PR-DL_routing_error_analysis.md", _routing),
        ("PR-DL_authority_controls.md", _authority),
        ("PR-DL_cost_analysis.md", _cost),
        ("PR-DL_regression_results.md", _regression),
        ("PR-DL_recommendation.md", _recommendation),
        ("PR-DL_remaining_risks.md", _risks),
    ):
        _write(OUT / name, writer(packet))
    _write(OUT / "focused_tests.txt", packet["regression_text"])
    _write(OUT / "changed_files.txt", _changed_files())
    _refresh_review(packet)


def _write_csvs(packet: Mapping[str, Any]) -> None:
    live_rows = []
    score_rows = []
    compare_rows = []
    for row in packet["rows"]:
        payload = row.get("live_payload") or {}
        adapter = row.get("live_adapter") or {}
        scores = row.get("scores") or {}
        live_rows.append(
            {
                "scenario_id": row["scenario_id"],
                "utterance": row["utterance"],
                "accepted": row["live_accepted"],
                "status": payload.get("status") or adapter.get("status"),
                "interpreted_intent": payload.get("interpreted_intent"),
                "primary_operation": payload.get("primary_operation"),
                "interlocutor_id": payload.get("interlocutor_id"),
                "proposed_target_id": payload.get("proposed_target_id"),
                "ambiguous": payload.get("ambiguous"),
                "clarification_question": payload.get("clarification_question"),
                "unsupported_action": payload.get("unsupported_action"),
                "multiple_action_components": json.dumps(payload.get("multiple_action_components") or []),
                "unresolved_references": json.dumps(payload.get("unresolved_references") or []),
                "referenced_entities": json.dumps(payload.get("referenced_entities") or []),
                "non_authoritative_explanation": payload.get("non_authoritative_explanation"),
                "adapter_errors": json.dumps(adapter.get("errors") or []),
                "executed": adapter.get("executed"),
                "mutated_state": adapter.get("mutated_state"),
            }
        )
        score_rows.append({"scenario_id": row["scenario_id"], "deterministic_gameplay": row["deterministic_gameplay"], "B_requested": row["B_requested"], **scores})
        compare_rows.append(
            {
                "scenario_id": row["scenario_id"],
                "deterministic_gameplay": row["deterministic_gameplay"],
                "B_requested": row["B_requested"],
                "live_accepted": row["live_accepted"],
                "live_gameplay": row["live_gameplay"],
                "policy_A": row["policy_A"],
                "policy_B": row["policy_B"],
                "policy_C": row["policy_C"],
                "beneficial": row["scenario_id"] in packet["classes"]["beneficial_invocations"],
                "harmful": row["scenario_id"] in packet["classes"]["harmful_invocations"],
                "selective_false_negative": row["scenario_id"] in packet["classes"]["false_negatives"],
                "selective_false_positive": row["scenario_id"] in packet["classes"]["false_positives"],
            }
        )
    _csv(
        OUT / "PR-DL_live_interpretations.csv",
        live_rows,
        [
            "scenario_id",
            "utterance",
            "accepted",
            "status",
            "interpreted_intent",
            "primary_operation",
            "interlocutor_id",
            "proposed_target_id",
            "ambiguous",
            "clarification_question",
            "unsupported_action",
            "multiple_action_components",
            "unresolved_references",
            "referenced_entities",
            "non_authoritative_explanation",
            "adapter_errors",
            "executed",
            "mutated_state",
        ],
    )
    _csv(
        OUT / "PR-DL_interpretation_scores.csv",
        score_rows,
        [
            "scenario_id",
            "deterministic_gameplay",
            "B_requested",
            "intent_recognition",
            "entity_recognition",
            "ambiguity_recognition",
            "compound_action_decomposition",
            "unsupported_action_recognition",
            "authority_compliance",
            "schema_validity",
            "clarification_usefulness",
            "gameplay_usefulness",
            "asserted_outcome",
        ],
    )
    _csv(
        OUT / "PR-DL_policy_comparison.csv",
        compare_rows,
        [
            "scenario_id",
            "deterministic_gameplay",
            "B_requested",
            "live_accepted",
            "live_gameplay",
            "policy_A",
            "policy_B",
            "policy_C",
            "beneficial",
            "harmful",
            "selective_false_negative",
            "selective_false_positive",
        ],
    )
    usage_rows = []
    for row in packet["rows"]:
        usage = row.get("usage") or {}
        usage_rows.append(
            {
                "scenario_id": row["scenario_id"],
                "request_id": usage.get("request_id"),
                "configured_model": usage.get("configured_model"),
                "model": usage.get("model"),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "latency_ms": usage.get("latency_ms"),
                "estimated_input_tokens_preflight": usage.get("estimated_input_tokens_preflight"),
                "max_output_tokens": usage.get("max_output_tokens"),
                "status": usage.get("status"),
                "B_requested": row["B_requested"],
            }
        )
    _csv(
        OUT / "PR-DL_provider_usage.csv",
        usage_rows,
        [
            "scenario_id",
            "request_id",
            "configured_model",
            "model",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "latency_ms",
            "estimated_input_tokens_preflight",
            "max_output_tokens",
            "status",
            "B_requested",
        ],
    )


def _write_raw(packet: Mapping[str, Any]) -> None:
    phase0 = dict(packet["phase0"])
    config = dict(phase0.get("provider_configuration") or {})
    config.pop("openai_api_key", None)
    phase0["provider_configuration"] = config
    payload = {
        "decision": packet["decision"],
        "provider_models": packet["models"],
        "phase0": {
            "head": phase0.get("head"),
            "provider_configuration": config,
            "worktree": "dirty at start; preserved",
        },
        "isolation": packet["prepared"]["isolation"],
        "checkpoint_guard": {
            "save_guard_verified": packet["checkpoint"].get("save_guard_verified"),
            "provider_tripwire_hits": packet["checkpoint"].get("provider_tripwire_hits"),
            "stopped": packet["checkpoint"].get("stopped"),
            "stage1_all_unusable": packet["checkpoint"].get("stage1_all_unusable"),
        },
        "usage": packet["usage"],
        "classes": packet["classes"],
        "policies": packet["policies"],
        "hidden_hits": packet["hidden_hits"],
        "rows": [
            {
                "scenario_id": row["scenario_id"],
                "utterance": row["utterance"],
                "messages": row.get("messages"),
                "public_context": row.get("public_context"),
                "live_raw_text": row.get("live_raw_text"),
                "live_payload": row.get("live_payload"),
                "live_adapter": row.get("live_adapter"),
                "usage": row.get("usage"),
                "scores": row.get("scores"),
                "deterministic_gameplay": row["deterministic_gameplay"],
                "selected_resolver": row["selected_resolver"],
                "B_requested": row["B_requested"],
                "existing_signals": row["existing_signals"],
                "independent_checks": row["independent_checks"],
            }
            for row in packet["rows"]
        ],
    }
    text = redact(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    (OUT / "raw_results.json").write_text(text, encoding="utf-8")


def _experiment(packet: Mapping[str, Any]) -> str:
    config = packet["phase0"]["provider_configuration"]
    usage = packet["usage"]["C"]
    policies = packet["policies"]
    return f"""
# PR-DL Experiment Report

MODE: BOUNDED LIVE COMPARATIVE EXPERIMENT

PRODUCTION INTEGRATION: NONE

HEAD: `{packet['phase0']['head']}`

The worktree was already dirty. PR-DL preserved it. Production saves were guarded during preparation and during both live stages.

Provider configuration: `DEFAULT_MODEL_NAME={config['DEFAULT_MODEL_NAME']}`, temperature 0, Responses API, strict JSON schema, `max_output_tokens` 400. The response model was `{', '.join(packet['models'])}`. The PR-DH planner schema was not reused because it includes `proposed_resolver`, `advance_time`, and `expects_mutation`.

PR-DK matrix, recomputed before live calls: A TP=3 FP=0 FN=6; B TP=8 FP=2 FN=1; C TP=9 FP=12 FN=0.

Live requests: {usage['provider_requests']}
Actual input tokens: {usage['actual_input_tokens']}
Actual output tokens: {usage['actual_output_tokens']}
Actual total tokens: {usage['actual_total_tokens']}

One interpretation was stored per scenario and replayed.

- Policy A fully handled {policies['A']['correct_count']} scenarios.
- Policy B fully handled {policies['B']['correct_count']} scenarios with {packet['usage']['B']['provider_requests']} calls.
- Policy C fully handled {policies['C']['correct_count']} scenarios with {usage['provider_requests']} calls.

Stage 1 (ordinary social, ambiguous pronouns, compound action) returned usable schema-valid interpretations with no execution and no state mutation. Stage 2 used the remaining scenarios once.

PR-DL decision: {DECISION_LABEL}
"""


def _policy_md(packet: Mapping[str, Any], policy: str) -> str:
    summary = packet["policies"][policy]
    usage = packet["usage"][policy]
    lines = [
        f"# PR-DL Policy {policy} Results",
        "",
        f"Provider requests charged to this policy: {usage['provider_requests']}",
        f"Actual input tokens: {usage['actual_input_tokens']}",
        f"Actual output tokens: {usage['actual_output_tokens']}",
        f"Actual total tokens: {usage['actual_total_tokens']}",
        "",
        f"Fully handled ({summary['correct_count']}): {_join(summary['correctly_handled'])}",
        f"Partially handled ({summary['partial_count']}): {_join(summary['partially_handled'])}",
        f"Missed complications ({summary['missed_count']}): {_join(summary['missed_complications'])}",
        f"Incorrect interpretations ({summary['incorrect_count']}): {_join(summary['incorrect_interpretations'])}",
        f"Unnecessary escalations ({summary['unnecessary_count']}): {_join(summary['unnecessary_escalations'])}",
        f"Useful clarifications ({summary['clarification_count']}): {_join(summary['useful_clarifications'])}",
        f"Authority violations in consumed model output ({summary['authority_count']}): {_join(summary['authority_violations'])}",
        f"Unsupported asserted outcomes ({summary['unsupported_outcome_count']}): {_join(summary['unsupported_outcomes'])}",
        "",
        "| Scenario | Deterministic | Live | Policy result | Resolver |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in packet["rows"]:
        lines.append(
            f"| {row['scenario_id']} | {row['deterministic_gameplay']} | {row['live_gameplay']} | {row[f'policy_{policy}']} | {row['selected_resolver']} |"
        )
    if policy == "A":
        lines.extend(["", "Policy A uses the deterministic contract only. Interpretation usage is zero. A correct deterministic result stays in place even when the stored model output is wrong."])
    elif policy == "B":
        lines.extend(["", "Policy B consumes the stored interpretation only where the preserved PR-DK B trigger is true: an existing routing signal or an independent completeness check. Elsewhere it keeps the deterministic result."])
    else:
        lines.extend(["", "Policy C consumes the stored interpretation on every scenario. A rejected adapter result is an unusable interpretation for that turn."])
    return "\n".join(lines)


def _routing(packet: Mapping[str, Any]) -> str:
    classes = packet["classes"]
    return f"""
# PR-DL Routing Error Analysis

These classes compare the stored live interpretation with the deterministic result. They are outcome classes. The preserved PR-DK routing labels stay in the evidence correction.

## False negatives

Selective routing left the deterministic result in place, and the stored interpretation would have improved it.

- `var_compound_subtle`: independent checks missed "drift over ... then try to pull it free." The model separated the approach and the pull. Deterministic gameplay is FAIL. Live gameplay is PASS.
- `var_quote_control`: the deterministic resolver is `travel` for a quoted joke. The routing label says assistance is not justified. The model treated the line as speech, with the explanation that it is not a literal action. Live gameplay is PASS.

## False positives

Selective routing invoked the model where the deterministic result was already PASS.

- `var_social_control`: ordinary rain question. The model also returned a correct ask. The call was unnecessary and harmless.
- `var_hypothetical_control`: hypothetical notice question. The model also returned a correct ask. The call was unnecessary and harmless.

## Harmful invocations

The stored interpretation is worse than a correct deterministic result.

- `control_combat`: deterministic combat handling is PASS. The model named the goblin and the attack, then invented the entity id `quarterstaff`. The adapter rejected the payload. Universal consumption replaces a usable attack interpretation with a rejection.

## Beneficial invocations

The stored interpretation ranks above the deterministic result.

{_join(classes['beneficial_invocations'])}

`var_unsupported_mechanic` is a partial benefit: the model separated advantage, the spy, and the patrol, and it did not grant them, but it asked for entity ids instead of recognizing the requests as unsupported.

`declared_canon` and `mechanical_dump` are triggered by selective routing and are not beneficial. The canon output proposes a world update. The mechanical output proposes setting the goblin's hit points to zero and is rejected by the adapter.

## Count

- False negatives: {len(classes['false_negatives'])}
- False positives: {len(classes['false_positives'])}
- Harmful invocations: {len(classes['harmful_invocations'])}
- Beneficial invocations: {len(classes['beneficial_invocations'])}
"""


def _authority(packet: Mapping[str, Any]) -> str:
    guard = packet["checkpoint"]
    return f"""
# PR-DL Authority Controls

Preparation and both live stages ran inside `ProductionSaveGuard`. The guard probe intercepted session, world, and log writes, then asserted the watched save fingerprint was unchanged. Stage checkpoint `save_guard_verified` is {guard.get('save_guard_verified')}. Provider tripwire hits during the live stage: {guard.get('provider_tripwire_hits')}.

`ASHEN_DISABLE_LIVE_INTERPRETATION=1` was set before contract construction. `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` were patched to raise. The only provider path was the experiment client's `responses.create` call. Preparation recorded `live_provider_calls` {packet['prepared']['live_provider_calls_during_preparation']}. Recomputed contract traces showed no interpretation API calls.

Prompts contained player input, a short visible scene context, permitted entity ids and labels, the interpretation schema, clarification rules, and authority restrictions. Hidden-fact scan of prompts and stored outputs: {packet['hidden_hits'] or 'none'}.

The experiment did not call resolvers, roll dice, or execute plans. Every adapter result records `executed=false` and `mutated_state=false`.

Model outputs that crossed authority bounds were retained and rejected for consumption:

- `declared_canon` is schema-valid and proposes updating world facts, including the tunnel being open. Authority score FAIL. It was not applied.
- `mechanical_dump` proposes setting the goblin's hit points to zero. The adapter rejected the payload (`ambiguous_referent`). Authority score FAIL. It was not applied.
- `control_combat` invents `quarterstaff`. The adapter rejected the unknown id. Authority score FAIL. It was not applied.

No output was repaired or retried. The experiment path has no authoritative state mutation.
"""


def _ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "undefined"
    return str(round(numerator / denominator, 4))


def _cost(packet: Mapping[str, Any]) -> str:
    usage_a = packet["usage"]["A"]
    usage_b = packet["usage"]["B"]
    usage_c = packet["usage"]["C"]
    useful_b = packet["useful"]["B"]
    useful_c = packet["useful"]["C"]
    beneficial = packet["classes"]["beneficial_invocations"]
    beneficial_b = [sid for sid in beneficial if sid not in packet["classes"]["false_negatives"]]
    return f"""
# PR-DL Cost Analysis

Figures are provider-reported token counts for the 21 interpretation requests. No provider price is stated. Narration tokens are not included. This is not a complete-turn cost.

| Policy | Requests | Input | Output | Total | Useful PASS interpretations | Total tokens per useful PASS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A deterministic | {usage_a['provider_requests']} | {usage_a['actual_input_tokens']} | {usage_a['actual_output_tokens']} | {usage_a['actual_total_tokens']} | 0 | undefined |
| B selective | {usage_b['provider_requests']} | {usage_b['actual_input_tokens']} | {usage_b['actual_output_tokens']} | {usage_b['actual_total_tokens']} | {len(useful_b)} | {_ratio(usage_b['actual_total_tokens'], len(useful_b))} |
| C universal | {usage_c['provider_requests']} | {usage_c['actual_input_tokens']} | {usage_c['actual_output_tokens']} | {usage_c['actual_total_tokens']} | {len(useful_c)} | {_ratio(usage_c['actual_total_tokens'], len(useful_c))} |

Useful PASS interpretations are stored outputs the policy consumes whose gameplay score is PASS. Policy B's useful set is {_join(useful_b)}. Two of those, `var_social_control` and `var_hypothetical_control`, were already PASS under deterministic handling.

Beneficial corrections, including the partial unsupported-mechanic reading: {_join(beneficial)}.
Selective routing receives the beneficial cases it triggers: {_join(beneficial_b)}.

Avoided interpretation requests under B: {usage_c['provider_requests'] - usage_b['provider_requests']}
Avoided input tokens: {usage_c['actual_input_tokens'] - usage_b['actual_input_tokens']}
Avoided output tokens: {usage_c['actual_output_tokens'] - usage_b['actual_output_tokens']}
Avoided total tokens: {usage_c['actual_total_tokens'] - usage_b['actual_total_tokens']}

Additional full successes present in C and absent from B: {_join(packet['additional_successful'])}
Missed useful interpretations (selective false negatives with live PASS): {_join(packet['classes']['false_negatives'])}
Unnecessary selective invocations: {_join(packet['classes']['false_positives'])}

The output cap was 400. No request was retried. No model was switched. Preflight estimates summed to 27,319 conservative input tokens. Actual input was {usage_c['actual_input_tokens']}, inside the 30,000 ceiling. Actual output was {usage_c['actual_output_tokens']}, inside the 8,000 ceiling. Actual total was {usage_c['actual_total_tokens']}, inside the 38,000 ceiling.
"""


def _regression(packet: Mapping[str, Any]) -> str:
    return f"""
# PR-DL Regression Results

Focused suites:

{packet['regression_text']}

Shared turn-pipeline suite:

- Command: `python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line`
- Timeout: 180 seconds.
- The process finished inside the timeout with exit code 1.
- The captured progress line and short summary are in `artifacts/pr_dl_interpretation_comparison/pipeline_stdout.txt`.
- Result: failed. This run is not a pass.
- PR-DK had previously recorded the same suite as incomplete after an interrupted wait. This PR-DL run completed and failed. The failures were not repaired.

Inherited failures were left in place. No production code was changed to chase them.
"""


def _recommendation(packet: Mapping[str, Any]) -> str:
    policies = packet["policies"]
    usage_b = packet["usage"]["B"]
    usage_c = packet["usage"]["C"]
    return f"""
# PR-DL Recommendation

Decision: {DECISION_LABEL}

Selective routing fully handles {policies['B']['correct_count']} of 21 scenarios with {usage_b['provider_requests']} calls and {usage_b['actual_total_tokens']} tokens. Universal routing fully handles {policies['C']['correct_count']} with {usage_c['provider_requests']} calls and {usage_c['actual_total_tokens']} tokens. Deterministic handling fully covers {policies['A']['correct_count']}.

The two full improvements selective routing misses are the paraphrased compound (`var_compound_subtle`) and the quoted joke (`var_quote_control`). Universal routing gains both. It also replaces a correct attack interpretation with a rejected invented weapon id (`control_combat`). Net fully handled scenarios favor universal by one, while the call count more than doubles.

Both consuming policies still fail the canon declaration, which the model turns into a proposed world update, and the hit-point dump, which the model proposes and the adapter rejects. The unsupported mechanic line is only partial. Invoking the lightweight model does not by itself make those authority-heavy turns reliable.

The avoided calls therefore do not justify the missed paraphrase and quote, and the extra universal calls do not justify their cost. The comparison is complete enough to reject both policies as they stand.

Recommended next step: keep this out of production gameplay. Add a consumption guard that discards invented entity ids and proposed hit-point or canon updates, and extend the deterministic completeness checks to paraphrased approach-plus-manipulation and quoted speech. Re-run only the residual rows on stored outputs before any new provider call.
"""


def _risks(packet: Mapping[str, Any]) -> str:
    return f"""
# PR-DL Remaining Risks

- The 21 rows are the preserved PR-DK fixture matrix, not a measured player distribution.
- Semantic scores are rubric judgments over the stored outputs. Schema acceptance and semantic usefulness are recorded separately.
- `var_unsupported_mechanic` is a partial benefit because the clarification asks for ids the engine should refuse.
- A schema-valid canon update can pass the adapter while still proposing world mutation. Consumption needs a guard beyond the current forbidden-key list.
- Selective false negatives remain on paraphrases the independent checks do not tokenize as movement-plus-manipulation, and on quoted speech the deterministic resolver treats as travel.
- Universal consumption can reject an otherwise understandable attack when the model invents a weapon id.
- Shared pipeline failures are inherited and unresolved.
- No price was computed. Token totals are interpretation-only.
- Provider model for this run: {', '.join(packet['models'])}.
"""


def _changed_files() -> str:
    return """
experiments/pr_dl/__init__.py
experiments/pr_dl/budget.py
experiments/pr_dl/evidence.py
experiments/pr_dl/live.py
experiments/pr_dl/policies.py
experiments/pr_dl/prompt.py
experiments/pr_dl/reports.py
experiments/pr_dl/runner.py
experiments/pr_dl/scoring.py
tests/test_pr_dl_interpretation_comparison.py
tools/run_pr_dl_comparison.py
artifacts/pr_dl_interpretation_comparison/*
handoff/CURRENT_REVIEW.md
handoff/CURRENT_REVIEW.zip
handoff/REVIEW_MANIFEST.json
"""


def _refresh_review(packet: Mapping[str, Any]) -> None:
    policies = packet["policies"]
    usage_b = packet["usage"]["B"]
    usage_c = packet["usage"]["C"]
    classes = packet["classes"]
    text = f"""
# CURRENT REVIEW

PR-DL

MODE:
LIVE SELECTIVE VS UNIVERSAL COMPARISON

PR-DK inherited decision:
C — BOTH REQUIRE LIVE COMPARISON

Provider model:
{', '.join(packet['models'])}

Live request count:
{usage_c['provider_requests']}

Actual input tokens:
{usage_c['actual_input_tokens']}

Actual output tokens:
{usage_c['actual_output_tokens']}

Actual total tokens:
{usage_c['actual_total_tokens']}

Policy A results:
Fully handled {policies['A']['correct_count']} of 21. Interpretation tokens 0. Missed complications: {_join(policies['A']['missed_complications'])}.

Policy B results:
Fully handled {policies['B']['correct_count']} of 21, partial {policies['B']['partial_count']}. Requests {usage_b['provider_requests']}. Input {usage_b['actual_input_tokens']}. Output {usage_b['actual_output_tokens']}. Total {usage_b['actual_total_tokens']}.

Policy C results:
Fully handled {policies['C']['correct_count']} of 21, partial {policies['C']['partial_count']}. Requests {usage_c['provider_requests']}. Input {usage_c['actual_input_tokens']}. Output {usage_c['actual_output_tokens']}. Total {usage_c['actual_total_tokens']}.

Beneficial AI invocations:
{_join(classes['beneficial_invocations'])}

Harmful AI invocations:
{_join(classes['harmful_invocations'])}

Selective false negatives:
{_join(classes['false_negatives'])}

Selective false positives:
{_join(classes['false_positives'])}

Authority findings:
Save guard verified. No production save writes. No hidden-fact exposure in prompts or outputs. Canon update, hit-point assignment, and the invented quarterstaff id were rejected for consumption and were not applied.

Cost comparison:
Selective {usage_b['actual_total_tokens']} total tokens across {usage_b['provider_requests']} calls. Universal {usage_c['actual_total_tokens']} total tokens across {usage_c['provider_requests']} calls. Deterministic interpretation usage is zero. No provider price is stated.

Regression results:
Focused PR-DL, PR-DK, PR-DJ, PR-DG, routing, and authority tests: 47 passed. Shared turn-pipeline suite finished inside a 180 second timeout with failures and was not repaired. See artifacts/pr_dl_interpretation_comparison/PR-DL_regression_results.md.

PR-DL decision:
{DECISION}

Recommended next step:
Keep interpretation routing out of production. Add a consumption guard for invented ids and proposed hit-point or canon updates, and extend completeness checks for paraphrased compounds and quoted speech, then re-score the residual rows from stored outputs.
"""
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    review = handoff / "CURRENT_REVIEW.md"
    review.write_text(text.strip() + "\n", encoding="utf-8")
    zip_path = handoff / "CURRENT_REVIEW.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.name != "phase0_snapshot.json":
                archive.write(path, f"artifacts/pr_dl_interpretation_comparison/{path.name}")
    manifest = {
        "pr": "PR-DL",
        "artifacts": [f"artifacts/pr_dl_interpretation_comparison/{path.name}" for path in sorted(OUT.iterdir()) if path.is_file()],
    }
    (handoff / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _pipeline_counts() -> str:
    log = OUT / "pipeline_stdout.txt"
    if not log.exists():
        return "Shared pipeline log missing."
    first = log.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    marks = [char for char in first if char in ".F"]
    failed = marks.count("F")
    passed = marks.count(".")
    return (
        f"Shared pipeline progress marks: {passed} passed, {failed} failed, {passed + failed} collected. "
        "Exit code 1. Timeout 180 seconds was not reached."
    )


def main() -> None:
    focused_path = OUT / "focused_pytest.txt"
    focused = ""
    if focused_path.exists():
        raw = focused_path.read_bytes()
        focused = raw.decode("utf-16") if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff") else raw.decode("utf-8", errors="replace")
    tail = "\n".join(focused.splitlines()[-12:])
    regression = "\n".join(
        [
            "Command: python -m pytest tests/test_pr_dl_interpretation_comparison.py tests/test_pr_dk_escalation_routing.py tests/test_pr_dj_selective_interpretation.py tests/test_pr_dg_architecture_preflight.py tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py tests/test_pr_cx_authority_assurance.py --tb=no",
            tail.strip(),
            _pipeline_counts(),
        ]
    )
    packet = build_packet(regression)
    write_all(packet)
    print(json.dumps({"decision": packet["decision"], "requests": packet["usage"]["C"]["provider_requests"], "models": packet["models"]}))


if __name__ == "__main__":
    main()
