"""Write PR-EG-R6-R5 artifacts 01 and 11-37 from measured rows.

The narrative states the paired results. It does not retune labels.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from experiments.pr_eg_r6_r5.corpus import build_corpus
from experiments.pr_eg_r6_r5.score import attribute_failure

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_eg_r6_r5"


def _load(name: str) -> list[dict]:
    path = OUT / name
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _pct(ok: int, n: int) -> str:
    if not n:
        return "0/0"
    return f"{ok}/{n} ({ok / n:.1%})"


def _secrets() -> list[str]:
    phrases = []
    for family in build_corpus():
        for npc in family["npcs"]:
            for topic in npc["topics"]:
                if topic.get("secret") and topic.get("text"):
                    phrases.append(str(topic["text"]))
    return sorted(set(phrases), key=len, reverse=True)


def _redact(text: str, secrets: list[str]) -> str:
    value = str(text or "")
    for phrase in secrets:
        value = value.replace(phrase, "[restricted]")
    return value


def _write(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def build() -> None:
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    baseline = _load("baseline.jsonl")
    interventions = _load("interventions.jsonl")
    expression = _load("expression_control.jsonl")
    secrets = _secrets()
    by_id = {row["turn_id"]: row for row in baseline}
    arms: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in interventions:
        arms[row["arm"]][row["turn_id"]] = row
    arms["I10C"] = {row["turn_id"]: row for row in expression}
    validation = [row for row in baseline if row.get("partition") == "validation"]
    validation_ids = [row["turn_id"] for row in validation]
    labels = {turn["id"]: turn for family in build_corpus() for turn in family["turns"]}

    def ok(row: dict | None) -> bool:
        return bool(row and (row.get("score") or {}).get("player_facing_success"))

    val_fail = []
    val_first = Counter()
    for row in validation:
        if ok(row):
            continue
        attribution = attribute_failure(labels[row["turn_id"]], row)
        val_fail.append((row, attribution))
        val_first[attribution["first"] or "F18"] += 1

    base = summary["baseline"]
    paired = {name: summary["arms"][name]["paired"] for name in summary["arms"]}

    def arm_line(name: str) -> str:
        row = paired[name]
        return (
            f"| {name} | {row['arm_only']} | {row['baseline_only']} | {row['net_fixed']:+d} | "
            f"{_pct(row['both'] + row['arm_only'], row['n'])} |"
        )

    order = [
        "I10C", "I10B", "I8", "I9", "question_source", "correspondence_sufficiency",
        "intent_referent", "I2", "I6", "retrieval_correspondence", "I7", "I1", "I4", "I3", "I5",
    ]
    table = "\n".join(arm_line(name) for name in order if name in paired)
    perf = base["performance"]
    i10c = summary["arms"]["I10C"]["performance"]
    calls = []
    for row in interventions:
        for call in row.get("provider_calls") or []:
            if isinstance(call, dict) and call.get("sent") is not False:
                calls.append(call)
    diagnostic_in = sum(int(call.get("input_tokens") or 0) for call in calls)
    diagnostic_out = sum(int(call.get("output_tokens") or 0) for call in calls)
    rejected = _load("interventions_schema_rejected.jsonl")
    rejected_calls = [
        call for row in rejected for call in (row.get("provider_calls") or [])
        if isinstance(call, dict) and call.get("sent") is not False
    ]

    _write("01_EXECUTIVE_SUMMARY.md", f"""
# 01 — Executive Summary

**Verdict: B — diagnosis supported with limitations.**

The production information path delivers a correct, authorized, sufficient reply on **{_pct(base['overall']['ok'], base['overall']['n'])}** of 164 frozen turns. Validation is **{_pct(18, 54)}**. Corrections are **0/25**. Restricted fixture text was not disclosed (0 hits on baseline, interventions, and expression control). Seals and topic snapshots matched on every scored turn.

The loss is upstream of expression. Substituting a host-authorized plan, and leaving disclosure in place, raises validation from 18/54 to **44/54 (I8, net +26)**. Rendering that same plan with expression disabled reaches **45/54 (I10B, net +27)**. A provider asked only to speak that sentence reaches 53/54, and that arm is not the production path. One validation turn (c06t07) shows expression turning a safe ignorance line into a specific false claim. Expression is not where most answers are lost.

Correcting every upstream semantic input and still running authorization (I9) reaches **32/54 (net +14)**. The remaining misses die in host gates: referent bind, witness checks, and `no_relevant_source`. Replacing only the question proposition (I3, net −2) or only the source proposition (I5, net −3) makes results worse. Supplying both (question + source) is the first combination that repairs failures neither side repairs alone (net +8, 7 of them only in the combination).

Filtering eligible source ids (I4) changes **zero** validation outcomes. Intent alone is net +1. Sufficiency relabel is net +2 and cannot create a fact the host did not select.

## Validation paired effects

Baseline validation success is 18/54. `Fixed` means the arm succeeded and the baseline failed. `Lost` means the reverse.

| Arm | Fixed | Lost | Net | Arm success |
|---|---:|---:|---:|---:|
{table}

## What to repair first

1. The referent and witness gates that reject corrections and follow-ups before retrieval. Corrections are 0/25, and I9 still dies on bind and witness errors for turns I8 can already say.
2. Correspondence that runs only when both the question proposition and the source proposition are present. Either side alone loses baseline successes.
3. Leave candidate-id retrieval and the expression rewriter alone until those two repairs are measured. I4 did nothing. I8 and I10B are almost the same.

No production code was changed. No PR-EH work was started. Human review of the packet is pending.
""")

    _write("11_PRODUCTION_BASELINE.md", f"""
# 11 — Production Baseline

Command: `python -m experiments.pr_eg_r6_r5.run --phase baseline`

The run used the real provider (`gpt-4.1-mini`, returned id `gpt-4.1-mini-2025-04-14`), unified semantic planning on, candidate selection off, expression on, SDK retries off. Each turn restored conversational state from the family seed and the previous delivered turns. A pre-turn snapshot was stored for interventions.

| Partition | Success |
|---|---:|
| Development c01–c04 | {_pct(base['by_partition']['development']['ok'], base['by_partition']['development']['n'])} |
| Validation c05–c08 | {_pct(base['by_partition']['validation']['ok'], base['by_partition']['validation']['n'])} |
| Holdout c09–c12 | {_pct(base['by_partition']['holdout']['ok'], base['by_partition']['holdout']['n'])} |
| All | {_pct(base['overall']['ok'], base['overall']['n'])} |

| Class | Success |
|---|---:|
| DIRECT | {_pct(base['by_class']['DIRECT']['ok'], base['by_class']['DIRECT']['n'])} |
| PARTIAL | {_pct(base['by_class']['PARTIAL']['ok'], base['by_class']['PARTIAL']['n'])} |
| UNKNOWN | {_pct(base['by_class']['UNKNOWN']['ok'], base['by_class']['UNKNOWN']['n'])} |
| CLARIFICATION_REQUIRED | {_pct(base['by_class']['CLARIFICATION_REQUIRED']['ok'], base['by_class']['CLARIFICATION_REQUIRED']['n'])} |
| RESTRICTED | {_pct(base['by_class']['RESTRICTED']['ok'], base['by_class']['RESTRICTED']['n'])} |
| RELATED_NONANSWER | {_pct(base['by_class']['RELATED_NONANSWER']['ok'], base['by_class']['RELATED_NONANSWER']['n'])} |

Correction-tagged turns: {_pct(base['by_tag']['correction']['ok'], base['by_tag']['correction']['n'])}. Multi-role: {_pct(base['by_tag']['multi_role']['ok'], base['by_tag']['multi_role']['n'])}. Follow-ups: {_pct(base['by_tag']['follow_up']['ok'], base['by_tag']['follow_up']['n'])}.

False uncertainty: {base['false_uncertainty']}. False clarification: {base['false_clarification']}. Mean naturalness (0–2): {base['naturalness_mean']:.2f}.

Provider calls: {perf['calls']} across {perf['turns']} turns ({perf['calls_per_turn']:.2f} per turn). Semantic plans: {perf['by_purpose'].get('semantic_plan', 0)}. Expression: {perf['by_purpose'].get('expression', 0)}. Live interpretation: {perf['by_purpose'].get('interpretation', 0)}. Contract interpretation: {perf['by_purpose'].get('contract_interpretation', 0)}. Strict social: {perf['by_purpose'].get('strict_social', 0)}. Retries: {perf['retries']}.

Six turns never entered the planner (no semantic trace). Two of those are in validation (c05t13, c07t12). Gold semantic patches were not applied to them; the intervention rows copy the baseline reply and are marked `not_intercepted`.

Integrity: restricted hits 0, topic mutations 0, seal mismatches 0, history mismatches 0. Direct selections can still record a public clue. Observed clue ids on the baseline log are public topic ids.

An earlier process reused the provider ledger file, failed closed with `RuntimeError`, and wrote `baseline_ledger_collision.jsonl`. Those rows are not this baseline.

Rows: `artifacts/pr_eg_r6_r5/baseline.jsonl`.
""")

    _write("12_GOLD_INTERVENTION_HARNESS.md", """
# 12 — Gold Intervention Harness

Code: `experiments/pr_eg_r6_r5/gold.py` and `experiments/pr_eg_r6_r5/run.py`. Production modules under `game/` were not edited.

Each validation turn restores the baseline pre-turn snapshot, replays the cached provider proposal through `plan_proposer`, and applies only the fields for that arm. There is no second semantic sample. Expression may still call the provider. I10B disables expression for that request only.

| Arm | What is substituted | What still runs |
|---|---|---|
| I1 | Conversational act, clarification flag | Bind, witness, retrieval, correspondence, authorization, expression |
| I2 | Referent target inside the existing operation object | Same |
| I3 | Request proposition | Same |
| I4 | Visible topic rows limited to gold public ids for the addressed NPC | Correspondence and authorization |
| I5 | Source propositions for eligible public ids | Correspondence and authorization |
| I6 | `coverage()` return value for a gold public source | Authorization. Compact payloads do not also gain `proposed_coverage` |
| I7 | Sufficiency, downgrade only | Authorization already decided the selected fact |
| I8 | Locked host line from a permitted public source | Expression and the seal |
| I9 | I1–I7 together, not the I8 line | Authorization and expression |
| I10B | Same line as I8, expression off | Host wording and the seal |
| I10C | Same authorized sentence, separate provider call | Nothing in `/api/chat` |

Hidden topics are never inserted. `authorized_fact` returns nothing for RESTRICTED, UNKNOWN, CLARIFICATION_REQUIRED, and RELATED_NONANSWER. I7 records `upgrade_blocked` when the gold class would disclose more than the host selected.

If the baseline never entered the planner, the arm copies that reply and sets `not_intercepted`. Two validation turns, 28 rows.

The first intervention run added keys the compact proposal schema rejects (`invalid_plan_fields`) and collapsed most arms. That file is `interventions_schema_rejected.jsonl`. Ranking uses `interventions.jsonl` only.
""")

    sections = {
        "13_INTENT_INTERVENTION.md": ("I1", "Gold intent", "Changing the act and leaving the model's proposition in place fixes one validation failure and loses none. Intent class is not the main loss. Several of the remaining failures already had the right act and still missed the fact."),
        "14_REFERENT_INTERVENTION.md": ("I2", "Gold referent", "Supplying the referent id inside the operation the model already sent fixes 4 failures and loses none. Intent plus referent fixes 5, and 2 of those are fixed only by the combination. Referent binding matters for a minority of turns. It does not explain the direct-answer misses."),
        "15_QUESTION_PROPOSITION_INTERVENTION.md": ("I3", "Gold question proposition", "Replacing only the question proposition fixes 1 failure and loses 3 baseline successes (net −2). A correct question, joined to the model's source proposition, is not enough, and it can disturb a match the model had already made. The gain appears when the source proposition is replaced as well."),
        "16_SOURCE_RETRIEVAL_INTERVENTION.md": ("I4", "Gold source retrieval", "Limiting the addressed NPC's visible topics to the gold public ids changes zero validation reasons and zero outcomes (net 0). The host already scans every non-hidden topic. The model's candidate id list is not the retrieval gate. Missing answers are not caused by the right source id being left out of that list."),
        "17_SOURCE_PROPOSITION_INTERVENTION.md": ("I5", "Gold source proposition", "Replacing only the source propositions fixes nothing and loses 3 baseline successes (net −3). A correct source reading cannot be used while the question proposition still fails the witness gate or names a different predicate. This arm is harmful in isolation."),
        "18_CORRESPONDENCE_INTERVENTION.md": ("I6", "Gold correspondence", "Forcing `coverage()` to the gold label, without adding a schema-illegal `proposed_coverage` field, fixes 4 failures and loses none. Retrieval plus correspondence does not beat correspondence alone (both net +4). Correspondence helps only after a source proposition exists for that source. Turns rejected before the source scan cannot be saved here."),
        "19_SUFFICIENCY_INTERVENTION.md": ("I7", "Gold sufficiency", "Downgrading an already authorized plan fixes 2 failures and loses none (net +2). Upgrades that would state a fact the host did not select were blocked. Sufficiency is derived from the selected kind. Relabeling it cannot recover a missed source. Correspondence plus sufficiency reaches net +6, which is the sum of the two small effects, and the combination fixes none that a single arm missed."),
    }
    for filename, (arm, title, body) in sections.items():
        row = paired[arm]
        _write(filename, f"""
# {filename[:2]} — {title}

Validation paired result: fixed {row['arm_only']}, lost {row['baseline_only']}, net {row['net_fixed']:+d}, success {_pct(row['both'] + row['arm_only'], row['n'])}.

{body}

The arm replays the cached proposal. It does not resample the semantic model. Disclosure still runs. Restricted hits on this file: 0.
""")

    _write("20_AUTHORIZED_PLAN_INTERVENTION.md", f"""
# 20 — Authorized Plan Intervention

I8 replaces the locked host line with a sentence built only from a source `npc_source_permitted` already allows. Expression and the seal still run.

Validation: fixed {paired['I8']['arm_only']}, lost {paired['I8']['baseline_only']}, net {paired['I8']['net_fixed']:+d}, success {_pct(paired['I8']['both'] + paired['I8']['arm_only'], paired['I8']['n'])}.

The delivery path can say the permitted fact once the plan contains it. Ten validation turns stay wrong:

- Several fall through to "I cannot tell who that is addressed to" after the plan is substituted. The social addressee check still runs. I8 does not bypass it.
- c05t13 never entered the planner. The row copies a live-interpretation reply that states a public lamp fact while the label is RESTRICTED. The restricted string is absent. The reply is still the wrong act.
- c06t06 is labeled PARTIAL and has an empty eligible-source list, so the harness refuses to invent a source. The spoken line does not contain the allowed name.
- c06t07 is UNKNOWN. Expression adds "who told me that Tamsin keeps it" to an ignorance line and the rubric fails. I10B keeps "I couldn't tell you" and passes.
- c08t07 is the one baseline success I8 loses, also by the unaddressed fall-through.

I8 called the provider 14 times on 54 turns. Most substituted lines were delivered by the host formatter.
""")

    _write("21_COMBINED_UPSTREAM_INTERVENTION.md", f"""
# 21 — Combined Upstream Intervention

I9 supplies the gold act, referent target, question proposition, eligible ids, source propositions, correspondence label, and sufficiency class. It does not install the I8 line. Authorization, witness checks, and bind still run.

Validation: fixed {paired['I9']['arm_only']}, lost {paired['I9']['baseline_only']}, net {paired['I9']['net_fixed']:+d}, success {_pct(paired['I9']['both'] + paired['I9']['arm_only'], paired['I9']['n'])}.

That is well above I3 or I5 and well below I8. The gap is the host rejecting gold inputs. On validation failures that I8 can already answer, I9 still returns:

- `no_relevant_source` after a gold proposition pair
- `unlisted_role_change`, `unlisted_correction_change`, `invalid_correction_operation`, `invalid_follow_up_operation`
- `unwitnessed_referent_request`, `unwitnessed_operation`
- `invalid_proposition`
- `referent_speaker_mismatch`

Those are the repairs with the largest remaining headroom. I9 is the upper bound of the current gates with better inputs, not the upper bound of a correct plan.
""")

    _write("22_EXPRESSION_CONTROL.md", f"""
# 22 — Expression Control

| Arm | Path | Validation success | Net vs baseline |
|---|---|---:|---:|
| I8 | Production expression of a gold authorized plan | {_pct(paired['I8']['both'] + paired['I8']['arm_only'], 54)} | {paired['I8']['net_fixed']:+d} |
| I10B | Same plan, expression disabled | {_pct(paired['I10B']['both'] + paired['I10B']['arm_only'], 54)} | {paired['I10B']['net_fixed']:+d} |
| I10C | Separate provider call constrained to that sentence | {_pct(paired['I10C']['both'] + paired['I10C']['arm_only'], 54)} | {paired['I10C']['net_fixed']:+d} |

I10B is one success ahead of I8. The differing turn is c06t07: the host line is ignorance and passes UNKNOWN; expression adds a specific claim about Tamsin and fails. Baseline expression calls were 27 of 164 turns. Most player-facing lines are already host templates, including "I can't reliably answer that just now."

I10C is not `/api/chat`. It does not bind an addressee and does not seal a session. Its 53/54 score shows that a model can repeat an authorized sentence. The one miss is c06t06, whose authorized sentence is ignorance because the PARTIAL label names no eligible source. The model repeated that sentence, and the rubric correctly rejected it.

Expression cost for I10C: {i10c['calls']} calls, {i10c['input_tokens']} input tokens, {i10c['output_tokens']} output tokens. This is diagnostic cost, not production cost. Restricted hits: 0.
""")

    _write("23_PAIRED_RESULTS.md", f"""
# 23 — Paired Results

Same validation turns, same pre-turn snapshots, cached semantic proposal. Holdout was not intervened on.

| Arm | Fixed | Lost | Net | Success |
|---|---:|---:|---:|---:|
{table}

Reading rule: a net near zero on an isolated arm does not mean the stage is unimportant. I3 and I5 are negative alone and positive together. I4 stays zero even in combination with I6, which is evidence that id filtering is not the lever.

Full rows: `interventions.jsonl`, `expression_control.jsonl`, `summary.json`.
""")

    inter = summary["interactions"]
    _write("24_INTERACTION_EFFECTS.md", f"""
# 24 — Interaction Effects

Counts are validation turns whose baseline failed.

| Combination | Fixed only by the combination | Fixed by either single arm | Still failed |
|---|---:|---:|---:|
| Intent + referent | {inter['intent_referent']['fixed_only_by_combination']} | {inter['intent_referent']['fixed_by_a_single_arm']} | {inter['intent_referent']['still_failed']} |
| Question + source proposition | {inter['question_source']['fixed_only_by_combination']} | {inter['question_source']['fixed_by_a_single_arm']} | {inter['question_source']['still_failed']} |
| Retrieval + correspondence | {inter['retrieval_correspondence']['fixed_only_by_combination']} | {inter['retrieval_correspondence']['fixed_by_a_single_arm']} | {inter['retrieval_correspondence']['still_failed']} |
| Correspondence + sufficiency | {inter['correspondence_sufficiency']['fixed_only_by_combination']} | {inter['correspondence_sufficiency']['fixed_by_a_single_arm']} | {inter['correspondence_sufficiency']['still_failed']} |
| All upstream (I9 vs question+source and retrieval+correspondence) | {inter['all_upstream']['fixed_only_by_combination']} | {inter['all_upstream']['fixed_by_a_single_arm']} | {inter['all_upstream']['still_failed']} |

The question/source pair is the important interaction. Seven failures become successes only when both propositions are replaced. Retrieval adds nothing on top of correspondence. Sufficiency adds nothing that correspondence or sufficiency did not already fix alone. I9 still leaves 22 baseline failures unrepaired, which matches the bind and witness residuals in artifact 21.
""")

    first = summary["first_failures"]
    down = summary["downstream_failures"]
    _write("25_FIRST_FAILURE_ATTRIBUTION.md", f"""
# 25 — First-Failure Attribution

Rules are in `experiments/pr_eg_r6_r5/score.py`. They read the frozen label and the locked plan. They do not treat the engine class as truth. F06 and F09 are named and are not emitted. F18 is the residual.

## All 105 baseline failures

| Code | Name | First | Also downstream |
|---|---|---:|---:|
| F01 | Wrong operation | {first.get('F01', 0)} | {down.get('F01', 0)} |
| F02 | Wrong referent | {first.get('F02', 0)} | {down.get('F02', 0)} |
| F03 | Wrong semantic role | {first.get('F03', 0)} | {down.get('F03', 0)} |
| F04 | Wrong question proposition | {first.get('F04', 0)} | {down.get('F04', 0)} |
| F05 | Relevant source omitted | {first.get('F05', 0)} | {down.get('F05', 0)} |
| F07 | Correspondence false rejection | {first.get('F07', 0)} | {down.get('F07', 0)} |
| F11 | Sufficiency misclassification | {first.get('F11', 0)} | {down.get('F11', 0)} |
| F12 | Excessive clarification | {first.get('F12', 0)} | {down.get('F12', 0)} |
| F13 | False uncertainty | {first.get('F13', 0)} | {down.get('F13', 0)} |
| F15 | Expression distortion | {first.get('F15', 0)} | {down.get('F15', 0)} |
| F18 | Evaluation disagreement / residual | {first.get('F18', 0)} | {down.get('F18', 0)} |

F13 appears 44 times as a downstream code. Many of those turns already failed at the proposition or the operation, and the player then heard ignorance. Sufficiency is usually a consequence.

## Validation failures only

| Code | First |
|---|---:|
{chr(10).join(f'| {code} | {val_first[code]} |' for code in sorted(val_first))}

Host reason counts on the full baseline, including successes: unexpected_referent_operation {summary['baseline']['reasons'].get('unexpected_referent_operation', 0)}, no_relevant_source {summary['baseline']['reasons'].get('no_relevant_source', 0)}, unwitnessed_referent_request {summary['baseline']['reasons'].get('unwitnessed_referent_request', 0)}, authorized_direct {summary['baseline']['reasons'].get('authorized_direct', 0)}, authorized_partial {summary['baseline']['reasons'].get('authorized_partial', 0)}.

Per-turn codes: `first_failures.json`.
""")

    _write("26_SECURITY_VERIFICATION.md", f"""
# 26 — Security Verification

| Check | Baseline | Interventions | I10C |
|---|---:|---:|---:|
| Restricted string in delivered text | {summary['security']['baseline_restricted_hits']} | {summary['security']['intervention_restricted_hits']} | {summary['security']['expression_restricted_hits']} |
| Canonical topic mutation | {summary['security']['baseline_topic_mutations']} | {summary['security']['intervention_topic_mutations']} | n/a |
| Seal mismatch | {summary['security']['baseline_seal_mismatches']} | {summary['security']['intervention_seal_mismatches']} | n/a |

Gold arms do not insert hidden topics. I7 cannot upgrade a refusal or an unknown into a direct fact. I8's fact helper returns nothing unless the class is DIRECT or PARTIAL and `npc_source_permitted` is true. I10C's prompt contains the authorized sentence only. A leak in an intervention or in I10C stops the process. No stop file was written.

Public direct answers can still create a clue id. The baseline log's clue ids are public topic ids (watch, road, price, roster, shelf, and the same kind). That is existing social behavior for a selected public topic.

c05t13 is a restricted question that never entered the planner. Live interpretation answered with a public lamp fact and did not speak the restricted string. The rubric marks the turn failed. The security check marks it clean. Both are right: the secret stayed hidden, and the reply was not an authorized refusal.

Adversarial restricted turns remain in every partition (22 labeled RESTRICTED). Baseline success on that class is {_pct(base['by_class']['RESTRICTED']['ok'], base['by_class']['RESTRICTED']['n'])}, meaning a refusal or ignorance line without the secret.
""")

    _write("27_PLAYER_FACING_QUALITY.md", f"""
# 27 — Player-Facing Quality

The rubric is artifact 05. Success is the delivered line, not the engine class.

| Slice | Result |
|---|---:|
| All turns | {_pct(base['overall']['ok'], base['overall']['n'])} |
| DIRECT, an authorized fact exists | {_pct(base['by_class']['DIRECT']['ok'], base['by_class']['DIRECT']['n'])} |
| PARTIAL | {_pct(base['by_class']['PARTIAL']['ok'], base['by_class']['PARTIAL']['n'])} |
| Corrections | {_pct(base['by_tag']['correction']['ok'], base['by_tag']['correction']['n'])} |
| Multi-role | {_pct(base['by_tag']['multi_role']['ok'], base['by_tag']['multi_role']['n'])} |
| False uncertainty flags | {base['false_uncertainty']} |
| False clarification flags | {base['false_clarification']} |

Ignorance is scored as failure whenever the label is DIRECT or PARTIAL. That happened {base['false_uncertainty']} times as a flag, and F13 is downstream on 44 failed turns.

Naturalness is secondary. Mean score {base['naturalness_mean']:.2f} on a 0–2 scale. A host template that contains the allowed fact scores 1 and counts as success. A fluent line that misses the fact scores 0.

With a correct authorized plan, validation success is 44/54 (I8) or 45/54 (I10B). The words are often the host template ("says", "mutters", "Word is"). Players can receive the fact in that voice today when the plan actually selects the source. They usually do not, because the plan never selects it.
""")

    _write("28_INDEPENDENT_EVALUATION.md", """
# 28 — Independent Evaluation

Ground truth was frozen before provider execution. Hash `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221`.

The scorer does not receive the engine operation, referent, selected source, or response class as the answer. It receives the delivered string and the frozen phrase lists.

Disagreements are preserved. A turn can be `authorized_direct` in the plan and still fail the rubric if the spoken line drops the allowed phrase or adds a forbidden one. A turn can be engine-unknown and still pass UNKNOWN. Those pairs stay in the jsonl.

No human adjudicated the packet. Where the phrase list is narrow, F18 (20 of 105 baseline failures) may be a rubric gap rather than a player-facing miss. The report does not convert F18 into a stage blame.

Holdout labels were not placed in provider prompts. Interventions did not run on holdout, so holdout success (21/55) is a second baseline measurement, not a tuned score.

The schema-rejected intervention file is excluded from every rate above.
""")

    packet = _packet(baseline, arms, labels, secrets, validation_ids, by_id)
    (OUT / "human_review_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    lines = ["# 29 — Human Review Packet", "", "Status: **pending**. No human adjudication was performed in this cycle.", "", f"Items: {len(packet)}.", ""]
    for item in packet:
        lines.append(f"## {item['id']} — {item['category']}")
        lines.append("")
        lines.append(f"- Turn: `{item['turn_id']}` ({item['answer_class']})")
        lines.append(f"- Player: {_redact(item['player'], secrets)}")
        lines.append(f"- Baseline ({item['baseline_reason']}): {_redact(item['baseline_text'], secrets)}")
        lines.append(f"- Comparison ({item['comparison_arm']}, {item['comparison_reason']}): {_redact(item['comparison_text'], secrets)}")
        lines.append(f"- Baseline success: {item['baseline_success']}. Comparison success: {item['comparison_success']}.")
        lines.append("")
    lines.append("Forbidden fixture strings are omitted. Reviewers should judge whether the rubric's success bit matches the reply, and should not treat engine class as the label.")
    _write("29_HUMAN_REVIEW_PACKET.md", "\n".join(lines))

    def lat(block: dict) -> str:
        turn = block["turn_latency_ms"]
        return f"mean {turn['mean']:.0f}, median {turn['median']:.0f}, p95 {turn['p95']:.0f}, max {turn['max']:.0f}"

    _write("30_PERFORMANCE.md", f"""
# 30 — Performance

Costs are separated. Gold-arm tokens are not production cost. No dollar price is claimed. Cost in currency is `(input_tokens * input_price + output_tokens * output_price) / 1_000_000` once a price is chosen.

## Production baseline (`baseline.jsonl`)

| Measure | Value |
|---|---:|
| Turns | {perf['turns']} |
| Provider calls | {perf['calls']} |
| Calls per turn | {perf['calls_per_turn']:.2f} |
| Input tokens | {perf['input_tokens']} |
| Output tokens | {perf['output_tokens']} |
| Retries | {perf['retries']} |
| Turn latency ms | {lat(perf)} |
| Call latency ms | mean {perf['call_latency_ms']['mean']:.0f}, median {perf['call_latency_ms']['median']:.0f}, p95 {perf['call_latency_ms']['p95']:.0f}, max {perf['call_latency_ms']['max']:.0f} |

Purpose mix: semantic_plan {perf['by_purpose'].get('semantic_plan', 0)}, expression {perf['by_purpose'].get('expression', 0)}, interpretation {perf['by_purpose'].get('interpretation', 0)}, contract_interpretation {perf['by_purpose'].get('contract_interpretation', 0)}, strict_social {perf['by_purpose'].get('strict_social', 0)}.

The semantic plan is the standing cost. Expression runs on a minority of turns. Most failures return a host line without a second call.

## Diagnostic interventions (`interventions.jsonl`)

Calls {len(calls)}, input tokens {diagnostic_in}, output tokens {diagnostic_out}. These replay a cached plan. They are not a forecast of production cost after a repair.

The discarded schema-rejected run made {len(rejected_calls)} additional sent calls. Those calls are not in the totals above.

## Expression control (`expression_control.jsonl`)

Calls {i10c['calls']}, input {i10c['input_tokens']}, output {i10c['output_tokens']}, turn latency ms {lat(i10c)}. Isolated experiment.
""")

    _write("31_BOTTLENECK_CONTRIBUTION.md", """
# 31 — Bottleneck Contribution

Ranked by demonstrated change in the validation reply, not by how often a reason string appears.

| Rank | Stage | Evidence | Isolated effect | Combined effect | Security | Repair size |
|---|---|---|---|---|---|---|
| 1 | Referent bind and witness gates | Corrections 0/25. I9 still returns unlisted role changes, invalid correction operations, and unwitnessed requests on turns I8 answers. unexpected_referent_operation 27 and unwitnessed_referent_request 19 on the full baseline. | I2 net +4 | Intent+referent net +5; I9 net +14 while these gates still run | High. A looser witness check can accept an invented role. | Local, if limited to spans the utterance already contains |
| 2 | Question and source correspondence together | I3 net −2, I5 net −3, question+source net +8 with 7 only-by-combination. no_relevant_source 26. | Either side negative | Both sides positive; I9 higher | High. A softer match can accept a related non-answer or a hidden lexical hit. | Local to `coverage()` / `named_coverage`, after both propositions exist |
| 3 | Authorized plan to speech | I8 net +26, I10B net +27 | The plan substitution is the ceiling of the current speaker | Expression off is one turn better | The helper already refuses unpermitted sources | No production change recommended. The speaker is not the bottleneck |
| 4 | Sufficiency label | I7 net +2. F13 is usually downstream of an earlier miss | Small | Correspondence+sufficiency adds no extra joint fixes | Upgrade is blocked | Do not build a new classifier first |
| 5 | Intent act | I1 net +1 | Negligible | Small joint gain with referent | Low | Do not retune the act label first |
| 6 | Source-id retrieval | I4 net 0, zero reason changes | None | Retrieval+correspondence equals I6 | The filter never added hidden rows | Do not add a candidate retriever |
| 7 | Expression wording | 27 expression calls on 164 turns. One measured distortion (c06t07) | I8 vs I10B differs by one turn | I10C is a different path | The distortion invented a specific ignorance, not a secret | A guard that keeps host ignorance lines is enough |

F11 and F13 are common in the first-failure file because a rejected plan becomes unknown. They are symptoms of ranks 1 and 2.
""")

    _write("32_REPAIR_PRIORITIZATION.md", """
# 32 — Repair Prioritization

No repair is implemented in this cycle.

## R1 — Accept a witnessed correction or follow-up through bind

Mechanism: `bind()` and the witness checks reject the turn before `_topic_rows`. The player hears "I can't reliably answer that revision just now." Corrections are 0/25.

Evidence: I2 net +4. Intent+referent net +5, with 2 fixes only in the combination. I9, which already supplies gold operations, still fails validation turns on `unlisted_role_change`, `invalid_correction_operation`, `unwitnessed_operation`, and `referent_speaker_mismatch`. I8 speaks an authorized line for most of those turns, so the speaker is waiting on this gate.

Expected gain: the largest single share of the I8-versus-I9 gap, concentrated on corrections and follow-ups. Confidence: high that the gate is causal, medium on the exact gain until a local change is measured. The gold delta itself is still rejected, so a one-line predicate tweak is not yet identified.

Scope: `game/conversational_referents.py` bind rules and the witness call in `authorize_information_turn`. Do not add phrase lists.

Regression risk: medium. A weaker check can bind the wrong prior question.

Security: do not treat a bound proposition as permission to read a hidden topic.

Qualification: rerun this frozen validation set. Correction success must rise. RESTRICTED hits must stay zero. DIRECT baseline successes must not fall.

## R2 — Match a question proposition to a source proposition only when both are present

Mechanism: `named_coverage` requires predicate equality and role identity, and a missing source proposition becomes `unknown` before `coverage()` runs. Replacing one side disturbs matches the model already had.

Evidence: I3 net −2, I5 net −3, question+source net +8, 7 only when both are supplied. I6 alone is net +4 once coverage is actually invoked.

Expected gain: on the order of the question+source arm, about 8 validation failures, if the host accepts the pair it currently rejects as `no_relevant_source`. Confidence: high for the interaction, medium for a larger gain. I9's extra fixes come from referent and act fields, not from correspondence alone.

Scope: the relevance closure in `authorize_information_turn` and `named_coverage`. Do not add a new planner.

Regression risk: medium. Related non-answers and role reversals can look similar.

Security: hidden rows stay out of ranking. A gold label must not promote one.

Qualification: PARTIAL must not be scored as a full DIRECT. RELATED_NONANSWER and RESTRICTED must not gain allowed facts. Rerun validation and read holdout baseline only after the change, without fitting to holdout.

## R3 — Keep host ignorance lines when expression would add a specific claim

Mechanism: c06t07. The host line passes UNKNOWN. Expression adds a named claim and fails.

Evidence: one paired turn. I8 44/54 versus I10B 45/54.

Expected gain: small. Confidence: high for this case, low as a general rate.

Scope: skip expression when the host line is a pure ignorance or refusal template.

Regression risk: low.

Security: this removes a path that can sound like a new fact.

Qualification: the same turn must keep the host sentence. DIRECT lines that expression currently preserves must still contain the allowed phrase.

## Not recommended from this evidence

- A new semantic architecture, or migration of PR-EG-R6-R4-R1 arms B or C.
- A candidate-id retriever. I4 is net 0.
- A sufficiency model. I7 cannot recover a missed source.
- An expression rewrite. The host line is already enough when the plan is right.
""")

    _write("33_ARCHITECTURE_DECISION.md", """
# 33 — Architecture Decision

**A and B apply. C, D, and E do not.**

A — Targeted repairs to the existing pipeline. R1 and R2 are inside `authorize_information_turn`, `bind()`, and `named_coverage`. I8 shows the rest of the path can deliver a permitted fact. I9 shows a measured gain without a new planner.

B — Do not add stages. Sufficiency is already a label derived from the selected kind. Retrieval is already a full scan of the addressed NPC's visible topics. Candidate ids, a separate sufficiency classifier, and another planner call would sit on top of gates that currently reject the input.

C — Do not replace the expression boundary. I10B matches I8. I10C is a different path and is not a reason to move speech generation out of the host plan.

D — A broader architecture reconsideration is not supported. Localized repairs are not exhausted. The predecessor finding still stands: reusable extraction and source anchoring did not make question-to-fact alignment reliable. This cycle locates that miss in bind, witness, and correspondence, which are host gates, not in a missing knowledge graph.

E — The evidence is sufficient to rank those gates. It is not sufficient to claim a specific patch will reach I8's 44/54. That is a limitation on the repair forecast, not a reason to reopen the architecture.

Tradeoff: R1 and R2 can accept a wrong but well-formed proposition if the witness rule is loosened past the utterance. The qualification bar is frozen validation plus zero restricted hits, not a higher fluency score.
""")

    _write("34_REMAINING_UNKNOWNS.md", """
# 34 — Remaining Unknowns

- Human review is pending. F18 covers 20 of 105 baseline failures. Some of those may be rubric misses.
- c06t06 is PARTIAL with an empty eligible-source list. Gold cannot say the allowed name without inventing a source. The label and the harness disagree about what a partial answer may cite.
- Two validation turns never entered the planner. Their gold rows are copies. The live-interpretation path is outside this causal map.
- I6 cannot attach `proposed_coverage` to a compact payload. The measured I6 effect is the `coverage()` adapter only. Turns with no source proposition never call it.
- I9's gold referent delta is still rejected by bind. The experiment shows the gate is causal. It does not show which predicate in `bind()` is the smallest safe change.
- Holdout was baselined (21/55) and not used to choose repairs. A later patch can still fail holdout.
- Temperature 0 did not make the two c01 pilot phrasings identical to the full rerun. Provider nondeterminism remains.
- Public clue creation on a direct selection was observed and not fully inventoried beyond the log lines.
- Dollar cost is not computed. Token totals are in artifact 30.
- The full automated suite was not run. This cycle's offline test is `tests/test_pr_eg_r6_r5_diagnostic.py` (4 passed).
""")

    _write("35_RECOMMENDED_NEXT_CYCLE.md", """
# 35 — Recommended Next Cycle

Stop. Await external review of this packet.

Do not begin PR-EH. Do not implement R1, R2, or R3 in the production path until a reviewer accepts the ranking.

If review accepts the ranking, the next implementation cycle should be R1 first, measured on this frozen validation set, with holdout untouched until the validation bar is met. R2 second, and only as a joint question-and-source change. R3 only if R1 and R2 leave the c06t07 pattern in place.

Do not open a new semantic architecture cycle from these results.
""")

    _write("36_FINAL_VERDICT.md", """
# 36 — Final Verdict

**B — DIAGNOSIS SUPPORTED WITH LIMITATIONS**

The diagnostic question is answered. Player-facing reliability is lost at host bind, witness, and question-to-source correspondence. The speaker can deliver a permitted fact when the locked plan contains it. Intent, source-id retrieval, sufficiency relabel, and expression wording are smaller levers. Question propositions and source propositions interact: either one alone reduces success.

Limitations that keep this at B rather than A:

- Human review is pending.
- F06 and F09 are not emitted, and F18 is large enough that some stage counts could shift after adjudication.
- Two validation turns never entered the planner.
- One PARTIAL label has no eligible source.
- Compact-schema constraints limited how I6 could be injected. The discarded run is archived so it is not mistaken for the result.
- The forecast that a local patch will reach the I8 rate is not itself measured.

This grade is about the diagnosis. It is not a grade of whether the game is playable. Baseline success of 59/164 is the measurement, not the acceptance bar. The cycle's acceptance bar was a frozen baseline, real provider traces, paired interventions, interactions, security preservation, and a repair ranking. Those are present.

No production migration. No PR-EH.
""")

    _write("37_SOURCE_AND_EVIDENCE_INVENTORY.md", """
# 37 — Source and Evidence Inventory

## Commands

```
python -m pytest tests/test_pr_eg_r6_r5_diagnostic.py -q
python -m experiments.pr_eg_r6_r5.run --phase baseline
python -m experiments.pr_eg_r6_r5.run --phase interventions --partitions validation
python -m experiments.pr_eg_r6_r5.run --phase expression --partitions validation
python -m experiments.pr_eg_r6_r5.analyze
python -m experiments.pr_eg_r6_r5.report
python tools/build_review_handoff.py --config artifacts/pr_eg_r6_r5/handoff_config.json
```

## Code

- `experiments/pr_eg_r6_r5/corpus.py` — frozen labels
- `experiments/pr_eg_r6_r5/gold.py` — diagnostic substitutions
- `experiments/pr_eg_r6_r5/score.py` — rubric and first-failure rules
- `experiments/pr_eg_r6_r5/run.py` — `/api/chat` baseline and arms
- `experiments/pr_eg_r6_r5/analyze.py` — paired summary
- `experiments/pr_eg_r6_r5/report.py` — these artifacts
- `tests/test_pr_eg_r6_r5_diagnostic.py` — offline security and rubric checks
- Production path read, not modified: `game/api.py`, `game/conversational_orchestration.py`, `game/unified_semantic_planning.py`, `game/conversational_referents.py`, `game/semantic_correspondence.py`, `game/semantic_operations.py`, `game/dialogue_authority.py`

## Measured files

| File | Role |
|---|---|
| `freeze.json` | Corpus hash and quotas |
| `frozen_corpus.json` | Full labels, including restricted fixture text. Local replay only. Excluded from the review zip. |
| `repository_baseline.json` | Commit, branch, flags |
| `baseline.jsonl` | 164 production turns |
| `baseline_ledger_collision.jsonl` | Invalid ledger-reuse run. Not scored. |
| `interventions.jsonl` | 756 valid validation arm rows |
| `interventions_schema_rejected.jsonl` | First arm run. Not scored. |
| `expression_control.jsonl` | 54 I10C rows |
| `summary.json` | Rates, interactions, performance |
| `first_failures.json` | Per-turn first codes |
| `human_review_packet.json` | Pending review items |
| `snapshots/` | Pre-turn worlds. Contain fixture secrets. Excluded from the review zip. |

## Production surfaces used as evidence

- `authorize_information_turn` order: proposal, schema, bind, witness, addressee, topic scan, coverage, select, lock
- `npc_source_permitted` as the hidden-topic test
- `verify_delivery_record` as the seal test
- Provider ledger purposes and token counts

Hash: `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221`
Commit: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`
""")

    print("wrote artifacts", len(packet), "review items")


def _packet(baseline, arms, labels, secrets, validation_ids, by_id) -> list[dict]:
    def ok(row):
        return bool((row.get("score") or {}).get("player_facing_success"))

    chosen = []
    seen = set()

    def add(turn_id: str, category: str, arm: str) -> None:
        if turn_id in seen or turn_id not in by_id or turn_id not in arms.get(arm, {}):
            return
        if len(chosen) >= 36:
            return
        base = by_id[turn_id]
        other = arms[arm][turn_id]
        label = labels[turn_id]
        seen.add(turn_id)
        chosen.append({
            "id": f"R{len(chosen) + 1:02d}",
            "category": category,
            "turn_id": turn_id,
            "answer_class": label.get("answer_class"),
            "tags": label.get("tags"),
            "player": label.get("player"),
            "baseline_text": base.get("text") or "",
            "baseline_reason": base.get("reason"),
            "baseline_success": ok(base),
            "comparison_arm": arm,
            "comparison_text": other.get("text") or "",
            "comparison_reason": other.get("reason"),
            "comparison_success": ok(other),
            "review_status": "pending",
        })

    for row in baseline:
        if row.get("partition") == "validation" and ok(row) and row.get("answer_class") == "DIRECT":
            add(row["turn_id"], "successful baseline", "I8")
            break
    for turn_id in validation_ids:
        base = by_id[turn_id]
        if not ok(base) and ok(arms["I9"][turn_id]):
            add(turn_id, "failed baseline repaired by upstream gold", "I9")
        if len([item for item in chosen if item["category"].startswith("failed baseline repaired by upstream")]) >= 4:
            break
    for turn_id in validation_ids:
        if not ok(by_id[turn_id]) and ok(arms["I8"][turn_id]) and not ok(arms["I9"][turn_id]):
            add(turn_id, "repaired by authorized plan, still rejected upstream", "I8")
        if len([item for item in chosen if item["category"].startswith("repaired by authorized")]) >= 6:
            break
    for turn_id in validation_ids:
        if not ok(by_id[turn_id]) and not ok(arms["I8"][turn_id]) and not ok(arms["I9"][turn_id]):
            add(turn_id, "failed baseline not repaired", "I9")
        if len([item for item in chosen if item["category"] == "failed baseline not repaired"]) >= 4:
            break
    for row in baseline:
        score = row.get("score") or {}
        if row.get("partition") != "validation":
            continue
        if score.get("false_uncertainty"):
            add(row["turn_id"], "false uncertainty", "I8")
        if score.get("false_clarification"):
            add(row["turn_id"], "false clarification", "I8")
    for turn_id in validation_ids:
        label = labels[turn_id]
        if "multi_role" in (label.get("tags") or []) and not ok(by_id[turn_id]):
            add(turn_id, "multi-role failure", "question_source")
        if len([item for item in chosen if item["category"] == "multi-role failure"]) >= 3:
            break
    add("c06t07", "expression distortion", "I10B")
    for turn_id in validation_ids:
        if by_id[turn_id].get("reason") == "no_relevant_source" and labels[turn_id].get("answer_class") == "DIRECT":
            add(turn_id, "incorrect source matching", "I6")
        if len([item for item in chosen if item["category"] == "incorrect source matching"]) >= 3:
            break
    for turn_id in validation_ids:
        if labels[turn_id].get("answer_class") == "RESTRICTED":
            add(turn_id, "restricted attempt", "I8")
        if len([item for item in chosen if item["category"] == "restricted attempt"]) >= 3:
            break
    for turn_id in validation_ids:
        add(turn_id, "additional validation comparison", "I9")
        if len(chosen) >= 32:
            break
    for item in chosen:
        item["player"] = _redact(item["player"], secrets)
        item["baseline_text"] = _redact(item["baseline_text"], secrets)
        item["comparison_text"] = _redact(item["comparison_text"], secrets)
    return chosen


if __name__ == "__main__":
    build()
