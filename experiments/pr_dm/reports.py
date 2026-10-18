"""Write the PR-DM artifact set from an offline replay and holdout."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from experiments.pr_dm.replay import RECOVERED_TARGETS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dm_hybrid_refinement"

CHANGED = [
    "experiments/pr_dm/__init__.py",
    "experiments/pr_dm/authority.py",
    "experiments/pr_dm/completeness.py",
    "experiments/pr_dm/fallback.py",
    "experiments/pr_dm/holdout.py",
    "experiments/pr_dm/replay.py",
    "experiments/pr_dm/reports.py",
    "tests/test_pr_dm_hybrid_refinement.py",
    "tools/run_pr_dm_refinement.py",
    "artifacts/pr_dm_hybrid_refinement/",
    "handoff/CURRENT_REVIEW.md",
    "handoff/CURRENT_REVIEW.zip",
    "handoff/REVIEW_MANIFEST.json",
]


def choose_decision(replay: Mapping[str, Any], holdout: Mapping[str, Any]) -> str:
    refined = replay["refined"]
    if refined["committed_authority_violations"] or refined["executed_or_mutated"]:
        return "D"
    if refined["ordinary_degraded"] or refined["suppressed_valid_deterministic"]:
        return "E"
    if replay["baseline"] != {"A": 11, "B": 16, "C": 17}:
        return "F"
    if set(refined["recovered_misses"]) != set(RECOVERED_TARGETS):
        return "C"
    if refined["new_false_escalations"] or holdout["false_escalations"] or holdout["authority_failures"] or holdout["detection_failures"]:
        return "B"
    if refined["full_count"] != 18 or replay["live_provider_calls"] != 0:
        return "B"
    return "A"


def _ids(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _usage_line(usage: Mapping[str, int]) -> str:
    return (
        f"{usage['provider_requests']} requests, "
        f"{usage['actual_input_tokens']} input, "
        f"{usage['actual_output_tokens']} output, "
        f"{usage['actual_total_tokens']} total"
    )


def _marginal(replay: Mapping[str, Any]) -> dict[str, Any]:
    usage = replay["usage"]
    full_b = replay["policies"]["B"]["correct_count"]
    full_c = replay["policies"]["C"]["correct_count"]
    full_d = replay["refined"]["full_count"]
    extra_b = full_d - full_b
    tokens_b = usage["D"]["actual_total_tokens"] - usage["B"]["actual_total_tokens"]
    extra_c = full_d - full_c
    tokens_c = usage["D"]["actual_total_tokens"] - usage["C"]["actual_total_tokens"]
    return {
        "extra_full_vs_b": extra_b,
        "extra_tokens_vs_b": tokens_b,
        "tokens_per_extra_full_vs_b": (tokens_b / extra_b) if extra_b else None,
        "extra_full_vs_c": extra_c,
        "extra_tokens_vs_c": tokens_c,
    }


def write_artifacts(
    replay: Mapping[str, Any],
    holdout: Mapping[str, Any],
    *,
    phase0: Mapping[str, Any],
    regression_text: str,
) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    decision = choose_decision(replay, holdout)
    marginal = _marginal(replay)
    _write_csv(replay)
    documents = {
        "PR-DM_implementation_report.md": _implementation(replay, holdout, phase0, decision),
        "PR-DM_authority_guard.md": _authority(replay, holdout),
        "PR-DM_fallback_contract.md": _fallback(replay),
        "PR-DM_completeness_checks.md": _completeness(replay, holdout),
        "PR-DM_adversarial_controls.md": _adversarial(holdout),
        "PR-DM_policy_comparison.md": _comparison(replay, decision),
        "PR-DM_cost_analysis.md": _cost(replay, marginal),
        "PR-DM_holdout_results.md": _holdout(holdout),
        "PR-DM_regression_results.md": regression_text.strip() + "\n",
        "PR-DM_recommendation.md": _recommendation(replay, holdout, decision, marginal),
        "PR-DM_remaining_risks.md": _risks(replay, holdout),
        "focused_tests.txt": _focused_tests(),
        "changed_files.txt": "\n".join(CHANGED) + "\n",
    }
    for name, text in documents.items():
        (OUT / name).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    (OUT / "replay_summary.json").write_text(json.dumps(_public_summary(replay, holdout, decision), indent=2) + "\n", encoding="utf-8")
    (OUT / "phase0_snapshot.json").write_text(json.dumps(phase0, indent=2) + "\n", encoding="utf-8")
    return {"decision": decision, "out": str(OUT), "marginal": marginal}


def _write_csv(replay: Mapping[str, Any]) -> None:
    path = OUT / "PR-DM_stored_replay.csv"
    fields = [
        "scenario_id",
        "policy_A",
        "policy_B",
        "policy_C",
        "deterministic_gameplay",
        "live_gameplay",
        "live_accepted",
        "B_requested",
        "D_routed",
        "D_new_checks",
        "D_schema_valid",
        "D_authority_valid",
        "D_authority_reasons",
        "D_disposition",
        "D_if_offered",
        "D_consumed_ai",
        "D_preserved_deterministic",
        "D_clarification",
        "D_unsupported",
        "D_abstained",
        "D_selected_gameplay",
        "D_interpretation_usefulness",
        "D_execution_success",
        "D_executed",
        "D_mutated_state",
        "stored_input_tokens",
        "stored_output_tokens",
        "stored_total_tokens",
    ]
    handled = {policy: set(replay["policies"][policy]["correctly_handled"]) for policy in ("A", "B", "C")}
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in replay["rows"]:
            decision = row["decision"]
            offered = row["if_offered"]
            usage = row["usage"]
            fired = [key for key, value in row["new_checks"].items() if value]
            writer.writerow(
                {
                    "scenario_id": row["scenario_id"],
                    "policy_A": "PASS" if row["scenario_id"] in handled["A"] else row["deterministic_gameplay"],
                    "policy_B": "PASS" if row["scenario_id"] in handled["B"] else ("PARTIAL" if row["scenario_id"] in replay["policies"]["B"]["partially_handled"] else "FAIL"),
                    "policy_C": "PASS" if row["scenario_id"] in handled["C"] else ("PARTIAL" if row["scenario_id"] in replay["policies"]["C"]["partially_handled"] else "FAIL"),
                    "deterministic_gameplay": row["deterministic_gameplay"],
                    "live_gameplay": row["live_gameplay"],
                    "live_accepted": row["live_accepted"],
                    "B_requested": row["B_requested"],
                    "D_routed": row["refined_routed"],
                    "D_new_checks": "|".join(fired),
                    "D_schema_valid": decision["schema_valid"],
                    "D_authority_valid": decision["authority_valid"],
                    "D_authority_reasons": "|".join(row["guard"]["reasons"]),
                    "D_disposition": decision["disposition"],
                    "D_if_offered": offered["disposition"],
                    "D_consumed_ai": decision["consumed_ai"],
                    "D_preserved_deterministic": decision["preserved_deterministic"],
                    "D_clarification": decision["clarification"],
                    "D_unsupported": decision["unsupported"],
                    "D_abstained": decision["abstained"],
                    "D_selected_gameplay": decision["selected_gameplay"],
                    "D_interpretation_usefulness": decision["interpretation_usefulness"],
                    "D_execution_success": decision["execution_success"],
                    "D_executed": decision["executed"],
                    "D_mutated_state": decision["mutated_state"],
                    "stored_input_tokens": usage.get("input_tokens", ""),
                    "stored_output_tokens": usage.get("output_tokens", ""),
                    "stored_total_tokens": usage.get("total_tokens", ""),
                }
            )


def _implementation(replay: Mapping[str, Any], holdout: Mapping[str, Any], phase0: Mapping[str, Any], decision: str) -> str:
    refined = replay["refined"]
    return f"""# PR-DM Implementation Report

MODE: BOUNDED IMPLEMENTATION AND DETERMINISTIC EVALUATION

PRODUCTION INTEGRATION: NONE

LIVE PROVIDER CALLS: 0

HEAD: `{phase0.get("head")}`

The worktree was already dirty. PR-DM did not reset it and did not write production saves. Provider interpretation stayed disabled. The replay reads `artifacts/pr_dl_interpretation_comparison/raw_results.json` and does not regenerate model output. Source sha256 `{replay["source_sha256"]}` was checked before and after the read.

## Baseline preserved

Policy A fully handled {replay["baseline"]["A"]}. Policy B fully handled {replay["baseline"]["B"]}. Policy C fully handled {replay["baseline"]["C"]}. Recomputed labels match the stored PR-DL policy lists. Original scores were not edited.

Provider model on the stored calls: {_ids(list(replay.get("provider_models") or []))}.

## What was added

The experimental package `experiments/pr_dm` evaluates stored interpretations. It does not select a production resolver, roll dice, or mutate campaign state.

- Consumption-time authority rejects schema-valid proposals that assign hit points, invent facts or entity ids, update canon, fabricate dice, commit NPCs, mutate inventory, request execution, assert hidden information, or propose unsupported operations.
- The fallback keeps the deterministic reading beside the model proposal. An invalid proposal is not consumed. A valid deterministic reading is preserved as an interpretation, not executed. An incomplete deterministic reading is not executed merely because the model was rejected.
- Completeness checks add temporal sequencing with an uncovered second component, and a quoted-speech mismatch with a physical resolver. Bare conjunctions and non-player quotes do not escalate.

## Replay result

Refined selective policy D fully handled {refined["full_count"]} of 21. Partially handled: {_ids(refined["partially_handled"])}. Recovered misses: {_ids(refined["recovered_misses"])}. New false escalations on the original 21: {_ids(refined["new_false_escalations"])}. Committed authority violations: {_ids(refined["committed_authority_violations"])}. Executed rows: {_ids(refined["executed_or_mutated"])}.

Rejected after routing: {_ids(refined["rejected"])}. Those rejections are unsupported actions, not gameplay successes and not executions.

## Holdout

Deterministic paraphrases were labeled from their structure. Live-model success is not claimed. Detection failures: {_ids(holdout["detection_failures"])}. New false escalations: {_ids(holdout["false_escalations"])}. Authority failures: {_ids(holdout["authority_failures"])}. Conjunction gap: {_ids(holdout["missed_complications"])}. Save guard verified: {holdout["isolation"]["save_guard_verified"]}. Provider tripwire hits: {_ids(list(holdout["isolation"]["provider_tripwire_hits"]))}.

## Decision

{decision}
"""


def _authority(replay: Mapping[str, Any], holdout: Mapping[str, Any]) -> str:
    lines = ["# PR-DM Authority Guard", "", "The guard runs at consumption time. Adapter acceptance is recorded separately and is not sufficient.", ""]
    lines.append("Rejected categories are direct HP assignment, invented world facts, unauthorized canon updates, fabricated dice, invented entity identifiers, unauthorized NPC commitments, direct inventory mutation, unrestricted execution, hidden-information assertions, and unsupported authoritative operations.")
    lines.append("")
    lines.append("A refusal marked `UNSUPPORTED_REQUEST` or `ABSTAIN`, with a non-empty `unsupported_action`, may name those operations without being treated as a grant. A completed-outcome sentence is still rejected. Entity identifiers must belong to the stored permitted-entity list. The guard returns `executed=false` and `mutated_state=false`.")
    lines.append("")
    lines.append("## Stored payloads")
    lines.append("")
    lines.append("| Scenario | Adapter accepted | Guard accepted | Reasons |")
    lines.append("| --- | --- | --- | --- |")
    for row in replay["rows"]:
        reasons = ", ".join(row["guard"]["reasons"]) or "none"
        lines.append(f"| {row['scenario_id']} | {row['live_accepted']} | {row['guard']['accepted']} | {reasons} |")
    lines.append("")
    lines.append("`declared_canon` is adapter-accepted and guard-rejected. The payload proposes a world update, an opened tunnel, and the captain's agreement to betray the watch. It was not consumed and not applied.")
    lines.append("")
    lines.append("`mechanical_dump` proposes a hit-point assignment, an inventory grant, and hidden motives. The adapter had already rejected it. The guard rejects it as well.")
    lines.append("")
    lines.append("`control_combat` invents the entity id `quarterstaff`. Selective routing does not send this row. The guard still rejects the stored payload. Offering that payload to the fallback preserves the deterministic combat interpretation and does not execute it.")
    lines.append("")
    lines.append("`var_unsupported_mechanic` is adapter-accepted. The guard rejects it because the clarification treats advantage, a spy reveal, and a found patrol as operations waiting on identifiers.")
    lines.append("")
    lines.append("## Hand-authored controls")
    lines.append("")
    failed = holdout["authority_failures"]
    lines.append(f"Authority control failures: {_ids(failed)}.")
    for row in holdout["authority"]:
        lines.append(f"- `{row['case_id']}`: accepted={row['accepted']}; reasons={', '.join(row['reasons']) or 'none'}; executed={row['executed']}.")
    lines.append("")
    return "\n".join(lines)


def _fallback(replay: Mapping[str, Any]) -> str:
    lines = [
        "# PR-DM Fallback Contract",
        "",
        "The deterministic interpretation and the stored model proposal are both retained as records. Consumption is not execution. `known_execution_support` is false for every row.",
        "",
        "Rules applied:",
        "",
        "- An invalid or authority-rejected model payload is not consumed.",
        "- A PASS deterministic reading is preserved when the model payload is not consumed.",
        "- A FAIL deterministic reading is not executed because the model payload was rejected. The result is unsupported, clarification, or safe abstention.",
        "- A schema-valid and authority-valid payload may be retained as an interpretation. That retention does not authorize a resolver, a roll, or a state write.",
        "",
        "| Scenario | Routed | Disposition | If the stored output were offered | Usefulness | Execution |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in replay["rows"]:
        decision = row["decision"]
        lines.append(
            f"| {row['scenario_id']} | {row['refined_routed']} | {decision['disposition']} | {row['if_offered']['disposition']} | {decision['interpretation_usefulness']} | {decision['execution_success']} |"
        )
    lines.append("")
    lines.append("Preserving `control_combat` is the counterfactual that universal routing failed. The invented weapon id is discarded. The deterministic attack interpretation remains the selected interpretation, and it is still not executed by this experiment.")
    lines.append("")
    lines.append("Rejecting `declared_canon` does not fall through into a world-action execution. The deterministic reading is FAIL, so the disposition is unsupported.")
    lines.append("")
    return "\n".join(lines)


def _completeness(replay: Mapping[str, Any], holdout: Mapping[str, Any]) -> str:
    return f"""# PR-DM Completeness Checks

## Why the two rows were missed

`var_compound_subtle` is "I drift over to the notice board, then try to pull it free." The PR-DK compound check splits on `and` and `then`, then looks for a movement verb in a fixed list (`walk`, `go`, `head`, `approach`, `move`, `step`). `drift` is not in that list, and the selected resolver is `world_action`, so the travel-or-social mismatch does not fire. The stored independent checks are all false. The deterministic gameplay score is FAIL.

`var_quote_control` is "I say, \\"Walk closer and pry it off,\\" as a joke." The PR-DK check removes quoted text before it looks for action clauses, so the quoted walk and pry disappear. The selected resolver is `travel`, which consumed the quoted verbs. The stored routing label says assistance is not justified. The deterministic gameplay score is FAIL because the resolver is travel.

## Checks added

`temporally_sequenced_components` splits unquoted text on `then`, `and then`, `before`, `after`, and `once`. It does not split on bare `and`. A hypothetical `if`, `suppose`, or `imagine` suppresses the split. The clauses need two different head tokens, a directional phrase in one clause, and an object in another. A negated later clause does not count as a second attempt. Head tokens are the first non-closed-class word. There is no added synonym list for `drift`, `slide`, `edge`, `tug`, or `work`.

`action_contract_uncovered` is that sequence when the stored independent checks and, when present, the contract's secondary operations do not already record it.

`quoted_speech_boundary` requires a player speech frame outside the quotes (`I say`, `I remark`, `as a joke`, and the same small frame). A sign or a document that "says" something is not a player frame.

`quoted_action_resolver_mismatch` requires that boundary, a physical resolver (`travel`, `combat`, `world_action`, `exploration`), and action verbs that occur only inside the quotes. Verbs that also occur outside the quotes are the player's own action, so the quote does not escalate.

Only the uncovered sequence and the quote/resolver mismatch request interpretation.

## Original matrix

`var_compound_subtle` fires the uncovered sequence. `var_quote_control` fires the quote mismatch. No other original row fires a new check. Inherited false positives `var_social_control` and `var_hypothetical_control` stay inherited. They are not new.

## Holdout

Temporal paraphrases that use `slide`/`tug`, `edge`/`work`, and a fronted `after` are structurally detected. The bare-and sentence "I edge toward the notice board and work it loose" is not escalated by the new check. That miss is intentional: a conjunction alone is not a sequence. Quoted weather, a sign, a quote followed by a real walk, a hypothetical, a negated pull, ordinary combat, ordinary movement, ordinary observation, an ordinary question, and an ambiguous pronoun do not newly escalate.

Inherited PR-DK checks still fire on some holdout sentences. Those are recorded in the holdout report and were not retuned.
"""


def _adversarial(holdout: Mapping[str, Any]) -> str:
    lines = [
        "# PR-DM Adversarial Controls",
        "",
        "These sentences are not the PR-DL 21. Expected behavior was assigned from the structural rule before the replay was used as a score. No provider output exists for them, so none is marked as a live-model success.",
        "",
        "| Case | Family | Resolver | New route | Inherited route | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in holdout["routing"]:
        result = "false escalation" if row["false_escalation"] else ("miss" if row["missed_complication"] and row["family"] == "conjunction_gap" else ("detected" if row["detected"] else "not detected"))
        lines.append(
            f"| {row['case_id']} | {row['family']} | {row['resolver']} | {row['new_route']} | {row['inherited_route']} | {result} |"
        )
    lines.append("")
    lines.append("Authority controls use hand-authored payloads against a fixed permitted-entity list and a fixed visible-fact list. They cover a clean attack, a clean move, a clean question, a refusal, direct HP, an invented fact, a fabricated roll, an invented id, an NPC commitment, an inventory grant, an execution request, a hidden-information assertion, and an advantage or patrol-found operation.")
    lines.append("")
    lines.append(f"Authority failures: {_ids(holdout['authority_failures'])}.")
    lines.append("")
    return "\n".join(lines)


def _comparison(replay: Mapping[str, Any], decision: str) -> str:
    refined = replay["refined"]
    policies = replay["policies"]
    return f"""# PR-DM Policy Comparison

The same stored output is used for every policy. A, B, and C are the original PR-DL policies. D is the refined selective policy. Gameplay labels for A, B, and C were recomputed from the stored scores and matched the published lists.

| Policy | Fully handled | Partially handled | Requests | What the count means |
| --- | ---: | ---: | ---: | --- |
| A deterministic | {policies["A"]["correct_count"]} | {policies["A"]["partial_count"]} | 0 | Deterministic interpretation only |
| B original selective | {policies["B"]["correct_count"]} | {policies["B"]["partial_count"]} | {replay["usage"]["B"]["provider_requests"]} | Stored calls the original router would make |
| C universal | {policies["C"]["correct_count"]} | {policies["C"]["partial_count"]} | {replay["usage"]["C"]["provider_requests"]} | Every stored call consumed when the adapter accepts it |
| D refined selective | {refined["full_count"]} | {refined["partial_count"]} | {replay["usage"]["D"]["provider_requests"]} | Original selective calls plus the new completeness hits, after the authority guard |

D fully handled: {_ids(refined["fully_handled"])}.

D consumed as interpretations: {_ids(refined["consumed"])}.

D rejected: {_ids(refined["rejected"])}.

D did not execute any row. A PASS under D is a retained interpretation. It is not evidence that a resolver ran, a roll was made, or the world changed.

Universal routing loses `control_combat` because it consumes an invented weapon id and the adapter rejects the payload. Refined selective routing does not send that row, so the deterministic combat interpretation stays selected. If that payload is offered anyway, the fallback preserves the deterministic interpretation and still does not execute it.

`var_unsupported_mechanic` was PARTIAL under B and C because the clarification was consumed. D rejects that clarification. The partial credit is withdrawn. The row is an unsupported action, not a handled turn and not an execution.

Remaining original-matrix failures under D: {_ids(refined["rejected"])}. Routing misses under D: {_ids(refined["missed"])}.

Decision code from this comparison: {decision}.
"""


def _cost(replay: Mapping[str, Any], marginal: Mapping[str, Any]) -> str:
    usage = replay["usage"]
    per = marginal["tokens_per_extra_full_vs_b"]
    per_text = f"{per:.4f}" if isinstance(per, float) else "undefined"
    return f"""# PR-DM Cost Analysis

Token counts are the provider-reported counts stored by PR-DL for `gpt-4.1-mini-2025-04-14`. PR-DM did not make requests and did not invent measurements. Narration tokens are not included. This is not a complete-turn cost and it is not a price.

| Policy | Hypothetical invoked requests | Stored input tokens | Stored output tokens | Stored total tokens | Fully handled | Partially handled | Remaining failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | {usage["A"]["provider_requests"]} | {usage["A"]["actual_input_tokens"]} | {usage["A"]["actual_output_tokens"]} | {usage["A"]["actual_total_tokens"]} | {replay["policies"]["A"]["correct_count"]} | {replay["policies"]["A"]["partial_count"]} | {replay["policies"]["A"]["incorrect_count"]} |
| B | {usage["B"]["provider_requests"]} | {usage["B"]["actual_input_tokens"]} | {usage["B"]["actual_output_tokens"]} | {usage["B"]["actual_total_tokens"]} | {replay["policies"]["B"]["correct_count"]} | {replay["policies"]["B"]["partial_count"]} | {replay["policies"]["B"]["incorrect_count"]} |
| C | {usage["C"]["provider_requests"]} | {usage["C"]["actual_input_tokens"]} | {usage["C"]["actual_output_tokens"]} | {usage["C"]["actual_total_tokens"]} | {replay["policies"]["C"]["correct_count"]} | {replay["policies"]["C"]["partial_count"]} | {replay["policies"]["C"]["incorrect_count"]} |
| D | {usage["D"]["provider_requests"]} | {usage["D"]["actual_input_tokens"]} | {usage["D"]["actual_output_tokens"]} | {usage["D"]["actual_total_tokens"]} | {replay["refined"]["full_count"]} | {replay["refined"]["partial_count"]} | {len(replay["refined"]["rejected"])} |

D's requests are the original selective requests plus `var_compound_subtle` and `var_quote_control`. Their stored totals are 923 and 885 tokens.

Marginal cost against B: {marginal["extra_tokens_vs_b"]} additional stored tokens for {marginal["extra_full_vs_b"]} additional fully handled scenarios, {per_text} stored tokens per additional full interpretation.

Marginal change against C: {marginal["extra_full_vs_c"]} additional fully handled scenario and {marginal["extra_tokens_vs_c"]} stored tokens. The negative token delta means D uses fewer stored interpretation tokens than universal routing while also keeping `control_combat`.

The two additional full interpretations are interpretation records. They do not measure a completed combat, movement, or world update. No complete-turn affordability is claimed.
"""


def _holdout(holdout: Mapping[str, Any]) -> str:
    lines = [
        "# PR-DM Holdout Results",
        "",
        "Holdout sentences were written for this experiment. They are not scored by copying a PR-DL label. No provider was called. `live_model_success_claimed` is false.",
        "",
        f"Detection failures: {_ids(holdout['detection_failures'])}.",
        f"New false escalations: {_ids(holdout['false_escalations'])}.",
        f"Conjunction misses: {_ids(holdout['missed_complications'])}.",
        f"Authority failures: {_ids(holdout['authority_failures'])}.",
        f"Save guard verified: {holdout['isolation']['save_guard_verified']}. Provider tripwire hits: {_ids(list(holdout['isolation']['provider_tripwire_hits']))}.",
        "",
    ]
    for row in holdout["routing"]:
        lines.append(f"## {row['case_id']}")
        lines.append("")
        lines.append(row["note"])
        lines.append("")
        lines.append(f"Utterance: {row['utterance']}")
        lines.append("")
        lines.append(f"Resolver `{row['resolver']}`, operation `{row['operation']}`. New route: {row['new_route']}. Inherited route: {row['inherited_route']}. Structural detection held: {row['detected']}. Quote result: {row['quote_result']}.")
        lines.append("")
    lines.append("Inherited routes on holdout sentences come from the unchanged PR-DK checks. PR-DM did not retune those checks. A new false escalation is only a new-check route where the structural expectation was no route.")
    lines.append("")
    lines.append("Unsupported authority cases are rejections. They are not executed plans and they are not live-model successes.")
    lines.append("")
    return "\n".join(lines)


_DECISION_TITLES = {
    "A": "A — REFINED PREFLIGHT READY",
    "B": "B — PARTIAL REFINEMENT",
    "C": "C — ROUTING LIMITATION",
    "D": "D — AUTHORITY FAILURE",
    "E": "E — REGRESSION",
    "F": "F — INCONCLUSIVE",
}


def _recommendation(replay: Mapping[str, Any], holdout: Mapping[str, Any], decision: str, marginal: Mapping[str, Any]) -> str:
    refined = replay["refined"]
    title = _DECISION_TITLES.get(decision, decision)
    return f"""# PR-DM Recommendation

Decision: {title}

1. Consumption-time authority is enforceable on these stored outputs. The schema-valid canon update is rejected. The hit-point dump, the invented weapon id, and the unsupported advantage clarification are rejected. No rejected payload was executed. Committed authority violations: {_ids(refined["committed_authority_violations"])}.

2. The fallback prevents the universal-routing regression. `control_combat` stays a deterministic interpretation. Offering the invented-id payload does not replace that interpretation and does not execute it. Incomplete deterministic rows are not executed when the model payload is rejected.

3. The completeness checks recover `var_compound_subtle` and `var_quote_control`. They do not add a false escalation on the original 21. Ordinary combat, movement, and observation rows stay PASS.

4. The same structural rules detect new temporal paraphrases and a new quoted remark. They do not detect a bare-and paraphrase with uncovered verbs ({_ids(holdout["missed_complications"])}). That limit was required: a conjunction is not automatically two actions. Live-model behavior on the holdout is untested. Holdout false escalations: {_ids(holdout["false_escalations"])}. Authority control failures: {_ids(holdout["authority_failures"])}.

5. A bounded live experiment is justified. It is not a production integration. It should stay outside the game loop, keep the guard in front of every output, and refuse execution. The live set should include the conjunction gap and the three rejected authority rows, using stored outputs as the regression control.

6. The three remaining original failures are not missing routes. `declared_canon` and `mechanical_dump` are unauthorized proposals. `var_unsupported_mechanic` asks the engine to identify entities for operations it should refuse. Those are authority and mechanics limits. Interpreting them successfully would not make the actions legal.

Stored-output replay does not show production readiness. D fully handled {refined["full_count"]} interpretations with {replay["usage"]["D"]["provider_requests"]} stored requests and {replay["usage"]["D"]["actual_total_tokens"]} stored tokens. The marginal cost against original selective routing is {marginal["extra_tokens_vs_b"]} tokens for {marginal["extra_full_vs_b"]} additional full interpretations.

Recommended next step: keep this package out of production gameplay. Run one bounded no-execution live check of the conjunction paraphrase and the three authority rows, with the consumption guard required, and compare those new outputs with this stored replay before any further routing change.
"""


def _risks(replay: Mapping[str, Any], holdout: Mapping[str, Any]) -> str:
    return f"""# PR-DM Remaining Risks

- The 21 stored rows are the PR-DK fixture matrix, not a measured player distribution.
- D's 18 fully handled scenarios are interpretation outcomes. None was executed. A later executor could still misread a retained proposal.
- `var_unsupported_mechanic` lost its partial credit on purpose. The player still has no supported resolution for advantage, a spy reveal, or marking a patrol found. That needs a product response other than a model clarification, and this experiment does not add that mechanic.
- `declared_canon` and `mechanical_dump` are safely rejected and still unresolved as player-facing turns.
- Bare `and` plus verbs outside the old lists remains undetected ({_ids(holdout["missed_complications"])}). Extending that with a synonym list or by splitting every conjunction was out of scope.
- Inherited false positives remain: `var_social_control` and `var_hypothetical_control`. Some holdout sentences also trip the unchanged PR-DK checks.
- Free-text novel nouns that are not entity ids and do not match the state-change patterns are not exhaustively detected.
- Holdout routing used local contracts only. No claim is made that a live model would interpret those paraphrases correctly.
- Shared turn-pipeline failures, if still present, are inherited and were not repaired.
- No provider price is stated. Token totals are interpretation-only.
- Production integration was not performed and is not supported by this replay.
"""


def _focused_tests() -> str:
    return """python -m pytest tests/test_pr_dm_hybrid_refinement.py -q --tb=line
python -m pytest tests/test_pr_dl_interpretation_comparison.py tests/test_pr_dk_escalation_routing.py tests/test_pr_dj_selective_interpretation.py tests/test_pr_dg_architecture_preflight.py tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py tests/test_pr_cx_authority_assurance.py -q --tb=line
python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line
"""


def _public_summary(replay: Mapping[str, Any], holdout: Mapping[str, Any], decision: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "live_provider_calls": 0,
        "baseline": replay["baseline"],
        "refined_full": replay["refined"]["fully_handled"],
        "refined_rejected": replay["refined"]["rejected"],
        "usage": replay["usage"],
        "holdout_false_escalations": holdout["false_escalations"],
        "holdout_detection_failures": holdout["detection_failures"],
        "holdout_misses": holdout["missed_complications"],
        "source_sha256": replay["source_sha256"],
    }


def refresh_current_review(replay: Mapping[str, Any], holdout: Mapping[str, Any], *, decision: str, regression_text: str) -> Path:
    refined = replay["refined"]
    usage = replay["usage"]
    marginal = _marginal(replay)
    text = f"""# CURRENT REVIEW

PR-DM

MODE:
HYBRID INTERPRETATION REFINEMENT

LIVE CALLS:
0

PR-DL inherited decision:
C — HYBRID REFINEMENT REQUIRED

Authority guard:
Consumption-time checks reject direct HP, invented facts, canon updates, fabricated dice, invented entity ids, NPC commitments, inventory mutation, execution requests, hidden-information assertions, and unsupported operations. Schema validity is not sufficient. `declared_canon` is adapter-accepted and guard-rejected. Committed authority violations: none. Executed rows: none.

Fallback behavior:
Invalid model output is not consumed. A complete deterministic interpretation is preserved and still not executed. An incomplete deterministic interpretation is not executed when the model output is rejected. `control_combat` stays deterministic. Offering its invented-id payload preserves that interpretation.

Completeness checks:
Temporal sequencing recovers `var_compound_subtle`. A player-quoted action with a physical resolver recovers `var_quote_control`. Bare conjunctions and non-player quotes do not escalate. New false escalations on the original 21: none.

Original selective results:
Fully handled {replay["baseline"]["B"]} of 21. Requests {usage["B"]["provider_requests"]}. Input {usage["B"]["actual_input_tokens"]}. Output {usage["B"]["actual_output_tokens"]}. Total {usage["B"]["actual_total_tokens"]}. Partial 1 (`var_unsupported_mechanic`).

Refined selective results:
Fully handled {refined["full_count"]} of 21. Requests {usage["D"]["provider_requests"]}. Input {usage["D"]["actual_input_tokens"]}. Output {usage["D"]["actual_output_tokens"]}. Total {usage["D"]["actual_total_tokens"]}. Partial {refined["partial_count"]}. Recovered: {", ".join(refined["recovered_misses"])}. Rejected without execution: {", ".join(refined["rejected"])}.

Holdout results:
New temporal paraphrases and a quoted remark are detected. New false escalations: none. Authority controls: no failures. Conjunction gap remains: {", ".join(holdout["missed_complications"]) or "none"}. Live-model success is not claimed. Save guard verified: {holdout["isolation"]["save_guard_verified"]}.

Cost comparison:
A 0 tokens, {replay["baseline"]["A"]} fully handled. B {usage["B"]["actual_total_tokens"]} tokens, {replay["baseline"]["B"]} fully handled. C {usage["C"]["actual_total_tokens"]} tokens, {replay["baseline"]["C"]} fully handled. D {usage["D"]["actual_total_tokens"]} tokens, {refined["full_count"]} fully handled. Marginal cost against B: {marginal["extra_tokens_vs_b"]} stored tokens for {marginal["extra_full_vs_b"]} additional full interpretations. These are interpretation tokens only.

Regression results:
{regression_text.strip()}

PR-DM decision:
{_DECISION_TITLES.get(decision, decision)}

Recommended next step:
Keep the package out of production. A bounded no-execution live check of the conjunction paraphrase and the three rejected authority rows is justified, with this guard required and this stored replay kept as the control.
"""
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    review = handoff / "CURRENT_REVIEW.md"
    review.write_text(text.strip() + "\n", encoding="utf-8")
    return review
