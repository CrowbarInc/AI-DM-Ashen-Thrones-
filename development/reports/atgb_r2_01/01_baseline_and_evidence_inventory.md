# 01 — Baseline and Evidence Inventory

ATGB-R2-01 • 2026-10-19 • offline investigation • no implementation authority.

## Current repository and authority

The branch and HEAD are captured in `artifacts/atgb/atgb_r2_01/repository_identity.json`. The working tree was already extensively dirty, including production modules, canonical play-session data, governance, tests/evidence and current review exports. HEAD alone does not identify the running baseline. `repository_status_before.txt` and `entry_hashes.json` record this pass's entry state; `integrity_verification.json` compares protected bytes at exit. Existing changes are preserved. No commit or push.

Mandatory authorities read: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`; also `docs/review_handoff_standard.md` and `docs/state_authority_model.md`. Requested `support/docs/NEXT_SESSION.md` is absent from the checkout: `support/` is the portable review layout, not a second authority. Canonical `docs/NEXT_SESSION.md` is used. No AGENTS.md was found in the project file inventory; `.agents` contains no additional instruction file.

## Frozen historical baseline, recomputed

Authoritative assessment: `artifacts/atgb/atgb_05a/assessment/ATGB_04_review_judgments.json`, alongside its original summary. The import-verification closeout is `development/reports/atgb_05_baseline_preservation.md`. This pass recomputed the counts from the preserved judgments (`baseline_verification.json`):

| Dimension | Pass | Fail | Uncertain | Determinate fraction |
|---|---:|---:|---:|---:|
| Interpretation | 18 | 16 | 3 | 18/34 |
| Response adequacy | 10 | 25 | 2 | 10/35 |
| Authority | 35 | 0 | 2 | 35/35 |

These are historical AI-assisted judgments, not authenticated human scoring (`human_review_attestation: false`) and not current post-repair performance. Authority has two uncertain cases (S03.4/S05.4 faction flags); 35/35 is not an overall safety rate. No critical authority violation was confirmed by that bounded assessment. No historical judgment was edited.

The 37 authoritative turns are original S01–S03, continuation S04 trial 2 and S05–S10 trial 1. Partial S04 trial 1 is separate evidence. Partition counts are 25 development-visible, four related variations, eight previously exposed held-out turns; the latter are not unseen independent generalization. Missing authored openings in S07/S09 limit opening-dependent criteria. They do not make a rules fallback to an ordinary remark appropriate.

## R1-01 through R1-09 status

| Pass | Established result | What it does not establish |
|---|---|---|
| R1-01 | Historical S08.2 host revision-entry misrouting diagnosed; PR-EG bind distinct | Raw model label was not retained in that initial reconstruction; no repair |
| R1-02 | Mechanical correction routing implemented; 105 new + 28 frozen tests pass; wider 443/9 matches nine entry failures | Empty-evidence response still fails; no end-to-end adequacy |
| R1-03 | One valid live paraphrase shows redundant clarification/empty refs; original attempts fail; L4 invalid due import environment leakage | Invalid L4 cannot prove live safety; old claim guard not reached is superseded by raw-trace review |
| R1-04 | Import-safe readiness/control recovery; 167 targeted tests pass | Infrastructure result, not semantic repair |
| R1-05 | Two valid original-wording trials avoid mechanical revision; legitimate pending revision control works within tested scope | Both conversations remain inadequate; topic/recipient issues remain |
| R1-06 | Actual saved requests contain public people passages and prior reply; earliest wrong completion is disposition/selection | Prompt clause causality not proven; raw L3 guard is reached and returns null |
| R1-07 | Conversational correction contract and bounded answer receipt implemented; main slice 238 passes (209 existing, 29 new), broader 23/1 matches entry | Substituted interpretations are deterministic controls, not live acceptance |
| R1-08 | One failed dispatch, mandatory stop; no model interpretation | No live effect, regression or acceptance result |
| R1-09 | DNS failure documented; zero live admissions; DEFER | Connectivity remains unresolved; no inference about model behavior |

Mechanical correction routing is repaired and validated within tested scope. The conversational correction contract is implemented and deterministically validated. Latest live conversational acceptance remains pending. R2 does not reopen S08.2 implementation.

## Evidence inventory and precedence

1. Original `artifacts/atgb/atgb_03/S01–S03/{transcript.md,result.json,stores/.../session_log.jsonl}` and `artifacts/atgb/atgb_03c/S05,S07,S08/...`: exact inputs, outputs, raw interpretations, adapted records, routing, bounded state and telemetry. Selected exact fields with canonical path/hash are in `representative_traces.json`; full result files and selected transcripts accompany the bundle.
2. Frozen `data/validation/atgb/`: scenario intent, authorized facts and disclosure constraints, not proof of provider-message contents. S02 hours are explicitly unauthored; route clue is gated by investigation.
3. R1 reports and original R1-03/05 traces, R1-06 reconstruction, R1-07 change review and R1-08/09 verdicts: repair chronology and limits. Original error records remain historical.
4. Final `artifacts/pr_eg_r6_r5/`: baseline.jsonl, summary.json, first_failures.json, intervention reports 13–22, attribution 25, performance 30, prioritization 32 and verdict 36. Raw baseline counts verified here: 59/164; correction tag 0/25. Validation 18/54; authorized-plan intervention 44/54, expression-disabled control 45/54. These are different populations/arms, not ATGB gains or production forecasts.
5. Relevant Chapter II owner documentation: PR-EA orchestration REVIEW, PR-EB continuity REVIEW, PR-EF conversational authority contract and remaining issues, PR-EF-R4 authorization/ambiguity contract and final recommendation. Final PR-EG-R6-R4-R1 verdict still forbids integration; R5 is a diagnostic, not migration acceptance. Existing owners already cover conversation, interaction focus, grounding, evidence and emission.
6. Current source: `interaction_completion.py`, `ordinary_semantic_ownership.py`, `conversational_orchestration.py`, `live_chat_interpretation.py`, `conversational_continuity.py`; proposals remain subordinate to deterministic authority.

## Limits

No fresh gameplay execution, tests of repair effect, provider calls, DNS diagnostics or benchmark run occurred. Initial ATGB raw requests are not retained in the selected original captures; do not assume evaluation-only facts were sent. Raw model JSON and projected public evidence ARE retained in the session logs. Later R1 actual messages are available for their separate correction cases. Current-source static reconstruction and isolated unmodified regex probes explain a path; they are not a historical instruction-pointer trace or a repaired-system run. Human review remains pending; exposure estimates beyond observed examples are qualitative inferences. New reports/evidence and a concise canonical orientation update are permitted review outputs, not production changes.
