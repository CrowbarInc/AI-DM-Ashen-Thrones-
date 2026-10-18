"""Package the PR-EG-R6-R3 discovery review from preserved comparison outputs."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_eg_r6_r3"
VERDICT = "B — DECISION SUPPORTED WITH LIMITATIONS"


def load_rows():
    return [json.loads(line) for line in (OUT / "per_case_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def rate(rows, field):
    values = [row["scores"][field] for row in rows if row["scores"].get(field) is not None]
    return sum(bool(value) for value in values), len(values)


def fmt(pair):
    count, denom = pair
    return f"{count}/{denom}"


def write(name, text):
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    freeze = json.loads((OUT / "freeze.json").read_text(encoding="utf-8"))
    audit = json.loads((OUT / "grader_reliability_audit.json").read_text(encoding="utf-8"))
    rows = load_rows()
    by = summary["by_architecture"]
    hold = summary["by_partition"]["holdout"]
    val = summary["by_partition"]["validation"]
    paired_hold = summary["paired"]["holdout"]["A_vs_C"]
    paired_val = summary["paired"]["validation"]["A_vs_C"]

    def arch_rows(name):
        return [row for row in rows if row["architecture"] == name]

    acceptance = {name: sum(row["scores"]["accepted"] for row in arch_rows(name)) for name in "ABC"}
    a_correction_reasons = Counter(
        row["normalized"].get("validation_reason") or "none"
        for row in arch_rows("A") if row["intended_operation"] == "correction" and not row["scores"]["correction_success"]
    )
    leaks = [row["case_id"] for row in rows if row["restricted_leaks"]]
    examples = []
    for row in arch_rows("C"):
        if row["partition"] == "holdout" and row["scores"]["correction_success"]:
            examples.append(f"{row['case_id']}: {row['utterance']} -> {row['normalized'].get('transformation')}")
        if len(examples) >= 4:
            break
    a_reject_example = next(
        (row for row in arch_rows("A")
         if row["intended_operation"] == "correction"
         and row["normalized"].get("validation_reason") == "no_relevant_source"
         and row["scores"]["operation_correct"]),
        None,
    )

    sections = {}
    sections[1] = f"""
# 01 — Executive Summary

**{VERDICT}.** Architecture C, host-built candidates with provider selection, is the only option that materially improves referent binding under the pre-registered rule. On the frozen holdout it binds 22/30 dependent referents against Architecture A's 6/30 (paired net +16). Validation moves the same way (paired net +20). Security leaks are 0/396. The composite correction and follow-up scores are not a fair production comparison: A accepted 5/132 interpretations because production authorization rejects uncovered propositions, while C accepted 124/132 compiled selections. Absolute holdout correction success for C is still 6/13 and follow-up success 6/13. Ambiguity remains unsolved (C 2/13). Do not migrate production in this cycle.
"""
    sections[2] = """
# 02 — Repository Baseline

HEAD is `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`). The working tree is dirty with a large uncommitted Product Realization history. PR-EG-R6-R2-R2 is the uncommitted semantic-operation implementation identified by `game/unified_semantic_planning.py` (`PLAN_VERSION = pr-eg-r6-r2-r2.1`), `game/semantic_operations.py`, `game/conversational_referents.py`, and `game/semantic_correspondence.py`, plus `artifacts/pr_eg_r6_r2_r2`.

`ASHEN_UNIFIED_SEMANTIC_PLANNING` defaults off. The configured model is `gpt-4.1-mini`. This cycle did not modify those production modules. Prototypes live under `experiments/pr_eg_r6_r3/`.
"""
    sections[3] = """
# 03 — Historical Failure Inventory

Preserved qualification evidence exists for R6, R6-R1, R6-R1-R1, R6-R2, R6-R2-R1, and R6-R2-R2 under `artifacts/pr_eg_r6*`, including frozen holdouts, live turns, semantic traces, and review markdown. R6-R2-R2 is the direct predecessor. Its explicit local assessment of the fresh 150-turn run is the source of the mission figures: operation 130/150, referent 25/74, communication roles 4/8, correction 5/23, follow-up 20/51, false clarification 16/150. Those correction and follow-up figures were labeled optimistic because they also required the automated grader's relevance flags.

Raw provider traces for that run are in `artifacts/pr_eg_r6_r2_r2/final/semantic_traces.jsonl` and `final/live_turns.jsonl`. This cycle did not replay those live conversations. Earlier cycles' executive summaries were not reused as measurements.
"""
    corr = audit["metrics"]["correction_success"]
    follow = audit["metrics"]["follow_up_success"]
    ref = audit["metrics"]["referent_correct"]
    sections[4] = """
# 04 — Failure Taxonomy

Each compared turn has one earliest code from the mission list. F01 wrong operation, F02 wrong referent, F03 wrong role, F05 bad correction, F06 bad follow-up, F07 malformed output, F08 host rejection, F09 false clarification, F10 wrong source, F11 insufficient answer, F12 unauthorized disclosure. F04 relationship errors are carried inside F03/F05 when the predicate or protected roles miss. F13–F15 are not scored on this isolated interpretation harness: there is no sealed player-facing narration, no production save, and the grader under test is the historical one.
"""
    sections[5] = f"""
# 05 — Grader Reliability Audit

Joined 150 final-run turns from `independent_grades.jsonl` to `local_assessment.json` through `grading_blind_map.json`.

The grader omitted {audit['grader_missing_correction_label']} of {audit['intended_corrections']} intended corrections and {audit['grader_missing_followup_label']} of {audit['intended_followups']} intended follow-ups by leaving the label null. Those turns left its denominator. On comparable turns it marked {corr['grader_only_false_positive']} correction successes the local label rejected, {follow['grader_only_false_positive']} follow-up successes the local label rejected, and {ref['grader_only_false_positive']} referent bindings the local label rejected. Wrong operations were still marked relevant and sufficient {audit['bias_counts'].get('wrong_operation_still_relevant_and_sufficient', 0)} times.

Causes: null labels shrink the denominator; structural or fluent answers are credited as relevance; the grader sees the engine's accepted act and bound id in the packet. The local rates remain optimistic upper bounds because they imported the grader's relevance flags. Neither set is human gold. This cycle did not use that grader.
"""
    sections[6] = """
# 06 — Independent Evaluation Contract

Labels were written in `experiments/pr_eg_r6_r3/corpus.py` and `CONTRACT.md` before the official provider run. Success is a match to those labels. The engine's chosen operation is not evidence that the operation was right. Protected role names (speaker, recipient, courier, debtor, creditor, and the listed kin) must match by name. Other filled slots match by value. A parsed witness failure is a host rejection, not a malformed output. The missing-slot name is reported and is not required for correction or follow-up success.

Decision rule, hashed in the freeze: recommend an architecture only if the holdout paired net gain is at least 8 on correction success, follow-up success, or referent binding; validation moves the same way by at least 5; no core holdout metric loses more than 3; leaks are zero; and the method is not a keyword classifier.
"""
    sections[7] = """
# 07 — Test Corpus Design

132 labeled cases. Tags overlap. Counts: correction 40, follow-up 41, multi-role cases across harbor, chapel, kiln, mine, ferry, and map situations, ambiguity 13 genuine plus explicit and false-ambiguity controls. Situations use distinct wording: coppicing, caulking, surety, glass-tax rolls, shaft tallies, speaker/recipient reversals, debtor/creditor swaps, and restricted ciphers. They are not the predecessor's reliquary script with names swapped. Authorized public sources and secret topics are separate fields. Secret strings are `gray-lantern`, `salt-ledger-key`, and `iron-moth`.
"""
    sections[8] = f"""
# 08 — Corpus Partitioning and Hashes

Development 42, validation 48, holdout 42. Official freeze was written before the 396 scored calls.

- Corpus `{freeze['corpus_sha256']}`
- Development `{freeze['partitions']['development']['sha256']}`
- Validation `{freeze['partitions']['validation']['sha256']}`
- Holdout `{freeze['partitions']['holdout']['sha256']}`

Holdout ids were not edited after the run. A one-case smoke (`D01`) ran before the freeze to fix witness failures being counted as malformed output. That smoke is not in the 396 and was not used to change labels.
"""
    sections[9] = """
# 09 — Common Experimental Conditions

Same utterance, participants, referent records, public sources, restricted topics, model `gpt-4.1-mini`, temperature 0, and max output 1800. Prompts differ because that is the architecture. A uses the production planner prompt and `authorize_information_turn`. B and C use shorter experimental prompts and do not run production source authorization. That acceptance difference is recorded as a limitation, not hidden.
"""
    sections[10] = f"""
# 10 — Architecture A Specification

A is the current structured planner. The provider returns `conversational_act`, a referent operation, a full proposition, and source propositions. The host validates schema, witnesses, and disclosure. Overall: operation {fmt(rate(arch_rows('A'), 'operation_correct'))}, referent {fmt(rate(arch_rows('A'), 'referent_correct'))}, roles {fmt(rate(arch_rows('A'), 'roles_correct'))}, correction {fmt(rate(arch_rows('A'), 'correction_success'))}, follow-up {fmt(rate(arch_rows('A'), 'follow_up_success'))}, malformed {fmt(rate(arch_rows('A'), 'malformed'))}, false clarification {fmt(rate(arch_rows('A'), 'false_clarification'))}. Accepted interpretations: {acceptance['A']}/132.
"""
    sections[11] = f"""
# 11 — Architecture B Specification

B asks for a move (`fresh_question`, `revise_previous`, `ask_about_previous`, `unresolved`), an anchor, only the changed roles, and a gap name. It does not emit referent ids or operation opcodes. The host copies unmentioned roles and derives the opcode. The free-text `meaning` field is ignored by the compiler. This is not A's schema with renamed fields: preservation is by host copy, and the model never names `replace_role_value` or `source_attribution`.

Result: referent {fmt(rate(arch_rows('B'), 'referent_correct'))} versus A's {fmt(rate(arch_rows('B') and arch_rows('A'), 'referent_correct'))}. Role preservation fell to {fmt(rate(arch_rows('B'), 'roles_correct'))} against A's {fmt(rate(arch_rows('A'), 'roles_correct'))}. False clarifications rose to {fmt(rate(arch_rows('B'), 'false_clarification'))}. The distinction is real, and on this evidence it does not win.
"""
    sections[12] = f"""
# 12 — Architecture C Specification

C builds candidates only from referent structure: replace each existing role, reverse speaker and recipient when both exist, replace predicate or qualifier, and the closed follow-up kinds, plus `new` and `clarify`. The utterance is not read by the generator. The model must return one supplied id. Unknown ids are rejected with no nearest-id repair.

Exact candidate kind matched the label on 94 of 126 non-open cases. Full selection success, which also requires the resulting meaning, is {fmt(rate(arch_rows('C'), 'selection_correct'))}. Missing-candidate count is 0 because the generator already offered a broad set, including `new`. That means this run did not show C forbidding an available meaning; it showed selection errors. Six cases were labeled `open` because debtor/creditor or multi-field swaps are not speaker/recipient reversal.
"""
    sections[13] = """
# 13 — Prototype Isolation

B and C are `experiments/pr_eg_r6_r3/architecture_b.py` and `architecture_c.py`. A calls production `_invoke_provider` and `authorize_information_turn` on an in-memory fixture. No production module was edited. Canonical world files, disclosure policy, final-response sealing, and session persistence were not changed. Restricted topics stay on the NPC with `disclosure: secret` and are omitted from provider context by the same `_topic_rows` filter A already uses.
"""
    sections[14] = """
# 14 — Experimental Output Contract

Each turn stores raw provider JSON separately from a normalized record: operation, referent, predicate, roles, transformation, follow-up, validation, ambiguity, and response class. Normalization does not rewrite a wrong role into the labeled role. Witness rejection keeps the attempted operation and marks validation rejected.
"""
    sections[15] = """
# 15 — Provider-Call Discipline

One call per turn per architecture. No hidden repair call. No retry on malformed JSON. Temperature 0. Max output tokens 1800. Calls: 132 per architecture, 396 total. Smoke calls are extra and excluded. Interpretation cost is not mixed with narration; these prototypes do not call the strict-social or expression paths.
"""
    sections[16] = f"""
# 16 — Correction Experiments

Denominator 40. A {fmt(rate(arch_rows('A'), 'correction_success'))}, B {fmt(rate(arch_rows('B'), 'correction_success'))}, C {fmt(rate(arch_rows('C'), 'correction_success'))}. Holdout paired C minus A is {paired_hold['correction_success']['net_C_minus_A']} (below the pre-registered clear-gain line of 8). Validation paired net is {paired_val['correction_success']['net_C_minus_A']}.

A's 40 correction failures include {a_correction_reasons.get('no_relevant_source', 0)} `no_relevant_source` and {a_correction_reasons.get('invalid_correction_operation', 0)} `invalid_correction_operation`. The first is production source authorization, which B and C do not apply. Example of an operation A classified correctly and then rejected: {a_reject_example['case_id'] if a_reject_example else 'none'} — {a_reject_example['utterance'] if a_reject_example else ''}.

Holdout corrections C accepted include: {'; '.join(examples) if examples else 'none recorded'}.
"""
    sections[17] = f"""
# 17 — Follow-Up Experiments

Denominator 41. A {fmt(rate(arch_rows('A'), 'follow_up_success'))}, B {fmt(rate(arch_rows('B'), 'follow_up_success'))}, C {fmt(rate(arch_rows('C'), 'follow_up_success'))}. Holdout paired net C minus A is {paired_hold['follow_up_success']['net_C_minus_A']}. Validation paired net is {paired_val['follow_up_success']['net_C_minus_A']}. The follow-up composite has the same acceptance confound as corrections. Referent binding, which does not require acceptance, still favors C.
"""
    sections[18] = """
# 18 — Multi-Role Experiments

Speaker, recipient, courier, debtor, creditor, assigner, and assignee are protected names. Reversals of speaker and recipient are a generated C candidate. Debtor/creditor swaps are labeled `open` because reversal would be the wrong structural operation. C's overall role score is higher than A's by a small margin (see the comparison matrix). B's copy-on-write did not preserve roles as reliably as A's full proposition, because omitted or extra role updates failed the value multiset.
"""
    sections[19] = f"""
# 19 — Ambiguity Experiments

Genuine clarification success: A {fmt(rate(arch_rows('A'), 'clarification_success'))}, B {fmt(rate(arch_rows('B'), 'clarification_success'))}, C {fmt(rate(arch_rows('C'), 'clarification_success'))}. False clarification flags: A {fmt(rate(arch_rows('A'), 'false_clarification'))}, B {fmt(rate(arch_rows('B'), 'false_clarification'))}, C {fmt(rate(arch_rows('C'), 'false_clarification'))}. B asks for clarification too often. C does not improve genuine ambiguity in a meaningful way. Explicit corrections were scored as corrections. Implicit bare replacements were scored as corrections, not as ambiguity.
"""
    sections[20] = f"""
# 20 — Security Experiments

Restricted source strings in provider context outside the player utterance: {len(leaks)}. Authorized answer text containing a secret: none. Forbidden forged or cross-conversation targets accepted: none that failed `security_pass`. Security pass is {fmt(rate(rows, 'security_pass'))} across all architectures. No prototype required a weaker disclosure check. A still applies production authorization. B and C never set a disclosure grant; they also do not yet prove that a later production binding of their output would keep that property. That reattachment is future work.
"""
    sections[21] = f"""
# 21 — Cost and Latency

Interpretation only.

| Architecture | Calls | Mean input tokens | Mean output tokens | Mean latency ms | P95 latency ms |
|---|---:|---:|---:|---:|---:|
| A | {by['A']['calls']} | {by['A']['input_tokens_mean']} | {by['A']['output_tokens_mean']} | {by['A']['latency_ms_mean']} | {by['A']['latency_ms_p95']} |
| B | {by['B']['calls']} | {by['B']['input_tokens_mean']} | {by['B']['output_tokens_mean']} | {by['B']['latency_ms_mean']} | {by['B']['latency_ms_p95']} |
| C | {by['C']['calls']} | {by['C']['input_tokens_mean']} | {by['C']['output_tokens_mean']} | {by['C']['latency_ms_mean']} | {by['C']['latency_ms_p95']} |

C is the cheapest of the three. Production narration cost is not included. A's previous live path sometimes added expression and strict-social calls; those are unchanged and outside this comparison.
"""
    sections[22] = f"""
# 22 — Generalization

| Partition | A meaning | B meaning | C meaning | A referent | C referent | A operation | C operation |
|---|---|---|---|---|---|---|---|
| Development | {val and summary['by_partition']['development']['A']['meaning_success']['count']}/{summary['by_partition']['development']['A']['meaning_success']['denominator']} | {summary['by_partition']['development']['B']['meaning_success']['count']}/{summary['by_partition']['development']['B']['meaning_success']['denominator']} | {summary['by_partition']['development']['C']['meaning_success']['count']}/{summary['by_partition']['development']['C']['meaning_success']['denominator']} | {summary['by_partition']['development']['A']['referent_correct']['count']}/{summary['by_partition']['development']['A']['referent_correct']['denominator']} | {summary['by_partition']['development']['C']['referent_correct']['count']}/{summary['by_partition']['development']['C']['referent_correct']['denominator']} | {summary['by_partition']['development']['A']['operation_correct']['count']}/{summary['by_partition']['development']['A']['operation_correct']['denominator']} | {summary['by_partition']['development']['C']['operation_correct']['count']}/{summary['by_partition']['development']['C']['operation_correct']['denominator']} |
| Validation | {val['A']['meaning_success']['count']}/{val['A']['meaning_success']['denominator']} | {val['B']['meaning_success']['count']}/{val['B']['meaning_success']['denominator']} | {val['C']['meaning_success']['count']}/{val['C']['meaning_success']['denominator']} | {val['A']['referent_correct']['count']}/{val['A']['referent_correct']['denominator']} | {val['C']['referent_correct']['count']}/{val['C']['referent_correct']['denominator']} | {val['A']['operation_correct']['count']}/{val['A']['operation_correct']['denominator']} | {val['C']['operation_correct']['count']}/{val['C']['operation_correct']['denominator']} |
| Holdout | {hold['A']['meaning_success']['count']}/{hold['A']['meaning_success']['denominator']} | {hold['B']['meaning_success']['count']}/{hold['B']['meaning_success']['denominator']} | {hold['C']['meaning_success']['count']}/{hold['C']['meaning_success']['denominator']} | {hold['A']['referent_correct']['count']}/{hold['A']['referent_correct']['denominator']} | {hold['C']['referent_correct']['count']}/{hold['C']['referent_correct']['denominator']} | {hold['A']['operation_correct']['count']}/{hold['A']['operation_correct']['denominator']} | {hold['C']['operation_correct']['count']}/{hold['C']['operation_correct']['denominator']} |

C's holdout meaning rate is lower than its validation rate. The referent advantage remains on the holdout. The corpus is internally authored.
"""
    sections[23] = """
# 23 — Per-Case Results

Every scored turn is in `artifacts/pr_eg_r6_r3/per_case_results.jsonl` (396 rows). Each row has the utterance, raw provider output, normalized interpretation, label-derived scores, and earliest failure. `summary.json` aggregates them. Do not treat a missing row as success.
"""
    sections[24] = """
# 24 — Failure Attribution

Earliest codes, owner from the pre-registered rules:

- A: F01 provider 44, F08 host 26, F03 provider 23, F02 provider 22, F11 provider 11. Two turns had no failure code.
- B: F03 provider 47, F01 provider 30, F09 provider 12, F06 provider 7. Thirty-four turns had no failure code.
- C: F03 provider 37, F01 provider 25, F05 provider 5, F06 provider 3. Fifty-eight turns had no failure code.

A's host slice is mostly production bind and source rejection. B and C host rejections are witness and anchor failures inside the experimental compilers. The dominant remaining error for B and C is still the provider choosing the wrong role or the wrong move, not a random transport failure. Malformed JSON was 0/132 for each architecture.
"""
    sections[25] = f"""
# 25 — Comparison Matrix

| Measure | A | B | C | Reading |
|---|---:|---:|---:|---|
| Operation | {fmt(rate(arch_rows('A'), 'operation_correct'))} | {fmt(rate(arch_rows('B'), 'operation_correct'))} | {fmt(rate(arch_rows('C'), 'operation_correct'))} | C ahead; B tied with A |
| Referent | {fmt(rate(arch_rows('A'), 'referent_correct'))} | {fmt(rate(arch_rows('B'), 'referent_correct'))} | {fmt(rate(arch_rows('C'), 'referent_correct'))} | Clear C gain, B also above A |
| Roles | {fmt(rate(arch_rows('A'), 'roles_correct'))} | {fmt(rate(arch_rows('B'), 'roles_correct'))} | {fmt(rate(arch_rows('C'), 'roles_correct'))} | B worse; C marginal versus A |
| Correction composite | {fmt(rate(arch_rows('A'), 'correction_success'))} | {fmt(rate(arch_rows('B'), 'correction_success'))} | {fmt(rate(arch_rows('C'), 'correction_success'))} | Confounded by acceptance |
| Follow-up composite | {fmt(rate(arch_rows('A'), 'follow_up_success'))} | {fmt(rate(arch_rows('B'), 'follow_up_success'))} | {fmt(rate(arch_rows('C'), 'follow_up_success'))} | Confounded by acceptance |
| Genuine clarification | {fmt(rate(arch_rows('A'), 'clarification_success'))} | {fmt(rate(arch_rows('B'), 'clarification_success'))} | {fmt(rate(arch_rows('C'), 'clarification_success'))} | Unsolved |
| False clarification | {fmt(rate(arch_rows('A'), 'false_clarification'))} | {fmt(rate(arch_rows('B'), 'false_clarification'))} | {fmt(rate(arch_rows('C'), 'false_clarification'))} | B regresses |
| Malformed | {fmt(rate(arch_rows('A'), 'malformed'))} | {fmt(rate(arch_rows('B'), 'malformed'))} | {fmt(rate(arch_rows('C'), 'malformed'))} | None |
| Accepted | {acceptance['A']}/132 | {acceptance['B']}/132 | {acceptance['C']}/132 | Not the same gate |
| Security | {fmt(rate(arch_rows('A'), 'security_pass'))} | {fmt(rate(arch_rows('B'), 'security_pass'))} | {fmt(rate(arch_rows('C'), 'security_pass'))} | No leaks |
| Mean input tokens | {by['A']['input_tokens_mean']} | {by['B']['input_tokens_mean']} | {by['C']['input_tokens_mean']} | C smallest |
| Complexity | Production planner | Delta compiler | Candidate generator plus selection | C is the smaller contract |
| Production risk | Current behavior | New compiler can drop roles | Selection must still pass bind | Do not ship C raw |
"""
    sections[26] = f"""
# 26 — Statistical Limitations

Paired holdout C minus A: correction {paired_hold['correction_success']['net_C_minus_A']}, follow-up {paired_hold['follow_up_success']['net_C_minus_A']}, referent {paired_hold['referent_correct']['net_C_minus_A']}, roles {paired_hold['roles_correct']['net_C_minus_A']}, meaning {paired_hold['meaning_success']['net_C_minus_A']}. Only referent and meaning clear the pre-registered net of 8. Correction and follow-up do not. Role gain is marginal. Validation agrees on referent (net {paired_val['referent_correct']['net_C_minus_A']}).

No confidence interval is claimed. The labels were written by the implementing agent. One model family graded nothing in this cycle; the provider under test is also `gpt-4.1-mini`. Absolute success remains a minority of turns.
"""
    sections[27] = """
# 27 — Regression Review

The 14 R6-R2-R2 failures were re-read, not rewritten, and not re-executed in this cycle. Production modules were not edited here, so the prior execution remains the latest run.

Contract-expectation changes, safe unknown instead of player clarification, authorization still rejected: the three `test_forged_authority_or_entity_rejected` cases, both `test_bad_prior_target_cannot_launder_history` cases, and seven `test_untrusted_operations_fail_closed_without_losing_focus` cases (`forged`, `cross_conversation`, `stale`, `speaker`, `field`, `operation`, `unwitnessed`, `substitution` — eight parametrized ids, all in that family). These are legitimate disposition changes if the product wants fail-closed unknown rather than a clarification prompt. They are still red tests.

`test_unqualified_historical_id_cannot_override_focus` is a stricter design choice than the no-silent-topic-override invariant. It needs an explicit product decision before anyone relaxes or keeps it.

Five inherited failures remain outside this cycle: three reference-eligibility holdouts, expression sufficiency, and the immutable preseal ignorance case. They were not corrected.
"""
    sections[28] = f"""
# 28 — Architecture Decision

Recommend Architecture C as the next implementation direction. Do not recommend B. Do not keep investing in a larger A schema as the way to fix binding.

C meets the pre-registered referent rule on holdout and validation, does not lose a core holdout metric by more than 3, leaks nothing, and does not classify the utterance with keywords. B improves binding somewhat and loses role fidelity and clarification discipline. A still describes roles slightly more carefully than B, and its production gate is the right authority boundary, but the provider is unreliable at emitting the full operation.

The recommendation is limited. C's composite success used a compiler that accepts interpretations A's source gate rejects. Shipping C's compiler output as a player-facing answer would skip disclosure control. The next implementation must feed a selected candidate back through existing `bind` and disclosure checks.
"""
    sections[29] = """
# 29 — Implementation Readiness

Not started. When a later cycle is authorized:

- Add a host candidate generator beside `game/conversational_referents.py`. Do not replace referent storage.
- Replace the provider operation schema with a candidate-id selection schema behind `ASHEN_UNIFIED_SEMANTIC_PLANNING`, default off.
- Keep `authorize_information_turn`, disclosure, and final sealing. A selected candidate that fails witness or source policy stays unaccepted.
- Preserve `game/dialogue_authority.py` and `game/immutable_valid_response.py`.
- Regression set: this corpus's frozen validation and holdout files, plus the existing forged-referent and disclosure tests. Do not edit those tests to match a new disposition without a separate decision.
- Qualification is a new live run after the gate is wired, not this isolated prototype.
"""
    sections[30] = """
# 30 — Remaining Unknowns

Whether C's selections survive production `bind` at anything like the prototype acceptance rate. Whether a narrower candidate list would start hiding legitimate meanings; this run's missing-candidate count was zero because the list was wide. Whether another model family would keep the referent gain. Whether genuine ambiguity needs a separate policy rather than another schema. Human review of the 132 labels has not happened.
"""
    sections[31] = """
# 31 — Recommended Next Cycle

Stop after PR-EG-R6-R3. Await external review. Do not begin PR-EH. Do not tune against the frozen holdout. If review accepts the limited C decision, the next cycle is a gated implementation that compiles a selected candidate into the existing host operation and then runs the current witness and disclosure checks. New holdouts would be required for that implementation cycle. The 14 red contract tests stay red until their expected disposition is explicitly changed.
"""
    sections[32] = f"""
# 32 — Final Verdict

**{VERDICT}.**

Comparable inputs, one real provider, frozen partitions, and a pre-registered referent gain support choosing C over A and B as the interpretation boundary to implement next. Limitations that block a stronger verdict: composite success is not on the same acceptance gate, holdout correction and follow-up gains are below the clear-gain line, ambiguity is unsolved, labels are internal, and no production migration was qualified.
"""
    sections[33] = """
# 33 — Source and Evidence Inventory

Experiment code: `experiments/pr_eg_r6_r3/`. Results: `artifacts/pr_eg_r6_r3/per_case_results.jsonl`, `summary.json`, `freeze.json`, partition JSON, `grader_reliability_audit.json`. Predecessor evidence: `artifacts/pr_eg_r6_r2_r2/`. Production planner untouched: `game/unified_semantic_planning.py` and the referent modules. Credentials and live campaign `data/` files are not part of this package.
"""
    # Fix the awkward B sentence that double-calls rate. Rewrite section 11 cleanly.
    sections[11] = f"""
# 11 — Architecture B Specification

B asks for a move (`fresh_question`, `revise_previous`, `ask_about_previous`, `unresolved`), an anchor, only the changed roles, and a gap name. It does not emit referent ids or operation opcodes. The host copies unmentioned roles and derives the opcode. The free-text `meaning` field is ignored by the compiler. This is not A's schema with renamed fields: preservation is by host copy, and the model never names `replace_role_value` or `source_attribution`.

Referent binding rose to {fmt(rate(arch_rows('B'), 'referent_correct'))} from A's {fmt(rate(arch_rows('A'), 'referent_correct'))}. Role preservation fell to {fmt(rate(arch_rows('B'), 'roles_correct'))} from A's {fmt(rate(arch_rows('A'), 'roles_correct'))}. False clarifications rose to {fmt(rate(arch_rows('B'), 'false_clarification'))}. The distinction is real, and on this evidence it does not win.
"""
    titles = {
        1: "EXECUTIVE_SUMMARY", 2: "REPOSITORY_BASELINE", 3: "HISTORICAL_FAILURE_INVENTORY",
        4: "FAILURE_TAXONOMY", 5: "GRADER_RELIABILITY_AUDIT", 6: "INDEPENDENT_EVALUATION_CONTRACT",
        7: "TEST_CORPUS_DESIGN", 8: "CORPUS_PARTITIONING_AND_HASHES", 9: "COMMON_EXPERIMENTAL_CONDITIONS",
        10: "ARCHITECTURE_A_SPECIFICATION", 11: "ARCHITECTURE_B_SPECIFICATION", 12: "ARCHITECTURE_C_SPECIFICATION",
        13: "PROTOTYPE_ISOLATION", 14: "EXPERIMENTAL_OUTPUT_CONTRACT", 15: "PROVIDER_CALL_DISCIPLINE",
        16: "CORRECTION_EXPERIMENTS", 17: "FOLLOW_UP_EXPERIMENTS", 18: "MULTI_ROLE_EXPERIMENTS",
        19: "AMBIGUITY_EXPERIMENTS", 20: "SECURITY_EXPERIMENTS", 21: "COST_AND_LATENCY",
        22: "GENERALIZATION", 23: "PER_CASE_RESULTS", 24: "FAILURE_ATTRIBUTION",
        25: "COMPARISON_MATRIX", 26: "STATISTICAL_LIMITATIONS", 27: "REGRESSION_REVIEW",
        28: "ARCHITECTURE_DECISION", 29: "IMPLEMENTATION_READINESS", 30: "REMAINING_UNKNOWNS",
        31: "RECOMMENDED_NEXT_CYCLE", 32: "FINAL_VERDICT", 33: "SOURCE_AND_EVIDENCE_INVENTORY",
    }
    for number, body in sections.items():
        write(f"{number:02}_{titles[number]}.md", body)
    summary_text = sections[1].split("\n", 2)[-1].strip()
    config = {
        "campaign_id": "pr_eg_r6_r3_interpretation_boundary_20261017",
        "campaign_name": "PR-EG-R6-R3 — Conversational Interpretation Boundary Reassessment",
        "campaign_date": "2026-10-17",
        "purpose": "Compare structured planning, host compilation, and host-constrained candidate selection without a production rewrite.",
        "objective_status": VERDICT,
        "executive_summary": summary_text,
        "self_contained_review_test": "Structural package verification only. This is not independent human review.",
        "changes": {
            "production": [],
            "validation": ["tests/test_pr_eg_r6_r3_harness.py"],
            "tooling": [
                "experiments/pr_eg_r6_r3/corpus.py",
                "experiments/pr_eg_r6_r3/common.py",
                "experiments/pr_eg_r6_r3/architecture_a.py",
                "experiments/pr_eg_r6_r3/architecture_b.py",
                "experiments/pr_eg_r6_r3/architecture_c.py",
                "experiments/pr_eg_r6_r3/run_eval.py",
                "experiments/pr_eg_r6_r3/audit_grader.py",
                "experiments/pr_eg_r6_r3/CONTRACT.md",
                "tools/write_pr_eg_r6_r3_review.py",
            ],
            "documentation": ["33 numbered review artifacts."],
        },
        "testing": {
            "focused": "Harness tests passed without provider calls. Official comparison: 396 real provider calls.",
            "broader": "The 14 inherited contract failures were re-read and not re-run. Five older inherited failures were not re-run.",
            "full_suite": "Not run.",
            "runtime_validation": "Isolated interpretation comparison, not production /api/chat qualification.",
            "model_runtime_boundary": "gpt-4.1-mini, temperature 0, one call per turn, no retries.",
            "new_regressions": "[]",
            "pre_existing_failures": "14 R6-R2-R2 contract-expectation failures plus 5 inherited failures.",
        },
        "known_problems": {
            "campaign_specific": ["Composite success confounded by production source rejection on A.", "Ambiguity unsolved.", "Internal labels.", "C compiler does not yet pass production bind."],
            "pre_existing": ["Fourteen red contract tests and five inherited failures."],
        },
        "decisions_requiring_human_review": ["Whether to authorize a gated Architecture C implementation that still ends in current bind and disclosure checks."],
        "does_not_prove": ["Production qualification, human gold labels, equal acceptance gates, or ambiguity competence."],
        "recommended_next_step": "Stop after PR-EG-R6-R3. Await external review. Do not begin PR-EH or migrate the production planner.",
        "primary_report": "artifacts/pr_eg_r6_r3/01_EXECUTIVE_SUMMARY.md",
        "supporting_files": [],
        "max_file_bytes": 50000000,
        "warn_bundle_bytes": 100000000,
    }
    supporting = []
    for path in [
        *sorted(OUT.glob("*.md")),
        OUT / "summary.json", OUT / "freeze.json", OUT / "per_case_results.jsonl",
        OUT / "grader_reliability_audit.json", OUT / "development_cases.json",
        OUT / "validation_cases.json", OUT / "holdout_cases.json",
        ROOT / "experiments/pr_eg_r6_r3/CONTRACT.md",
        ROOT / "experiments/pr_eg_r6_r3/corpus.py",
        ROOT / "experiments/pr_eg_r6_r3/architecture_a.py",
        ROOT / "experiments/pr_eg_r6_r3/architecture_b.py",
        ROOT / "experiments/pr_eg_r6_r3/architecture_c.py",
        ROOT / "experiments/pr_eg_r6_r3/common.py",
        ROOT / "experiments/pr_eg_r6_r3/run_eval.py",
        ROOT / "tests/test_pr_eg_r6_r3_harness.py",
    ]:
        if path.name in {"handoff_config.json", "evidence_inventory.json"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        supporting.append({
            "path": rel, "role": "cycle_evidence",
            "why": "Interpretation-boundary comparison evidence.",
            "behavioral_evidence": path.name == "per_case_results.jsonl",
            "human_review_required": path.suffix in {".md", ".py"},
        })
    config["supporting_files"] = supporting
    (OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    from tools.build_review_handoff import build_handoff
    result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff")
    print(json.dumps({"verdict": VERDICT, "bundle": result.get("file_count"), "zip": result.get("zip_path")}, indent=2))


if __name__ == "__main__":
    main()
