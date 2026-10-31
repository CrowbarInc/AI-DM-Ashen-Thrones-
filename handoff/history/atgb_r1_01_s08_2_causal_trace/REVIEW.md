# Campaign

Campaign: ATGB-R1-01 S08.2 Causal Trace and PR-EG Reconciliation
Identifier: `atgb_r1_01_s08_2_causal_trace`
Date: 2026-10-18
Generated: 2026-10-19T01:35:05Z
Purpose: Read-only causal trace of ATGB S08.2 and a comparison with PR-EG-R6-R5. No repair.

# Executive Summary

S08.2 answered "I meant the people, not the weather." with the host template "I don't have an unexecuted intention to revise. What do you want to change?" The earliest demonstrated incorrect decision is `_pending_revision_decision` in `game/conversational_orchestration.py`: `_REVISION_RE` matches `i meant`, no pending or executed intention existed, and the function returned reason `no_pending_intention`. The stored purpose `CORRECTION` is written by that return and does not prove the model label. The raw interpretation record was not retained. One live interpretation call ran; narration count was 0; `bind()` did not run. Failure class: contract. Relationship to PR-EG-R6-R5: C, different mechanism. R5 corrections are 0/25 on the full 164-turn corpus (validation subset 0/8). All 25 called `semantic_plan` and heard bind/witness lines. None heard S08.2's sentence. R5 production success is 59/164. Validation is 18/54. I8 is 44/54 and I10B is 45/54 on the validation intervention slice; those are not production forecasts. Restricted hits were 0. R4-R1 remains C and is an integration ban; R5's B grade does not replace it. NEXT_SESSION had not mentioned R5; that was staleness. The justified next pass is a narrower intention-control entry condition that preserves the three PR-EF-R4 revision holdouts. Whether the ordinary answer path would then name the visible people is unproven. No production code, test expectation, frozen baseline, or authority boundary changed. No live provider call was made.

Objective status: `COMPLETE: ROOT CAUSE OF THE CAPTURED SENTENCE ESTABLISHED; PR-EG R1 INAPPLICABLE; IMPLEMENTATION NOT STARTED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No test expectations, corpus files, rubric, or benchmark framework changed.

## Tooling changes

- No changes in this category.

## Documentation changes

- Investigation report and session orientation updated. PR-EG-R6-R4-R1 integration ban and PR-EG-R6-R5 diagnostic grade are both recorded, without treating R5 as integration acceptance.

## Generated artifacts

- Standard review handoff only. No new gameplay capture.

# What Was Tested

- **Focused tests:** No new tests. Existing captures and PR-EG baseline rows were read. Correction-tag recount: 0/25 overall, 0/8 validation, 0/8 development, 0/9 holdout. All 25 correction rows used semantic_plan and bind/witness host lines.
- **Broader relevant tests:** Not run. Read-only investigation.
- **Full suite:** Not run.
- **Runtime validation:** No new provider request and no gameplay rerun. Trace uses the frozen ATGB-03C S08 capture.
- **Model/runtime boundary:** Historical S08.2 call: gpt-4.1-mini-2025-04-14, one interpretation request, zero narration requests, request id resp_0ffffc99ed67ac1d006ad548fcc5e887d2af53b020d7776c33. PR-EG figures are prior measurements, not rerun.
- **New regressions:** None. Production modules were not edited.
- **Pre-existing failures:** ATGB conversational failures remain. PR-EG correction tag remains 0/25. Authenticated human scoring remains pending.
- **Self-contained bundle review:** From the extracted ZIP, identify the captured S08.2 sentence, the host reason no_pending_intention, the PR-EG classification C, the 0/25 correction population, and the three holdouts that must stay intact. Confirm the bundle states that production code was unchanged and no live provider call was made.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or reject classification C and the contract failure class before any code change.
- Accept or reject ATGB-R1-02 as only the intention-control entry condition, preserving correction_pending, correction_already_executed, and correction_nothing_pending.
- Do not authorize PR-EG R1 as the repair for S08.2.

# Known Problems / Unresolved Findings

## Campaign-specific

- Model communication purpose for S08.2 was not persisted. The host regex is sufficient without it.
- Leaving the intention gate does not by itself prove the reply will name the visible people.
- S02.2–S02.4, S03.3, S05.3, S01.4, S07.2, S06.4, and S04.2 fail on other branches.

## Pre-existing baseline

- PR-EG-R6-R4-R1 stays C, do not integrate. PR-EG-R6-R5 stays B as a diagnosis, with R1–R3 unimplemented.
- ATGB provisional assessment is not attested human scoring.
- S07/S09 openings were not delivered; S08.1's scene reply was delivered.
- Extensive pre-existing dirty worktree retained.

# Missing Concepts / Future Capabilities

- No new semantic classifier, phrase list, router, or planner is proposed.
- The follow-on answer after leaving the intention gate is a separate observation, not part of this repair claim.

# What This Campaign Does NOT Prove

- Conversational competence, a live rerun of S08.2, naming of the visible people after the gate change, improvement on the PR-EG 0/25 correction tag, independent generalization, or full-suite regression.
- The unobserved model purpose label. The host regex accounts for the captured sentence.
- That I8's 44/54 or I10B's 45/54 predict production behavior.

# Recommended Next Step

Await review. If accepted, ATGB-R1-02 records the section-06 contract and changes only the revision entry condition and the CORRECTION set-aside arm. Preserve the three PR-EF-R4 holdouts, add S08.2 stubs, and do not change bind(), prompts, world authority, ATGB expectations, or the frozen baseline. No live provider call in that pass unless separately authorized.

# Review Bundle Contents

Bundle file count: `12`
Bundle ZIP size: `000000040911` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_01_s08_2_causal_trace.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_01_s08_2_causal_trace.md`.
- `support/docs/NEXT_SESSION.md`: Current orientation after this investigation, including the R4-R1 versus R5 verdict distinction. Canonical source: `docs/NEXT_SESSION.md`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Exact S08 trial-1 player and AI-DM text, including S08.2. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/data/validation/atgb/visible/S08.json`: Authored S08 opening, facts, and the correction expectation. Not a scored result. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`: PR-EG-R6-R5 diagnosis grade B and its stated limits. Canonical source: `artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r5/11_PRODUCTION_BASELINE.md`: Population definitions for 59/164, 18/54, and the correction tag. Canonical source: `artifacts/pr_eg_r6_r5/11_PRODUCTION_BASELINE.md`.
- `support/artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`: Unimplemented R1 bind/witness proposal, compared and found inapplicable to S08.2. Canonical source: `artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`.
- `support/artifacts/pr_eg_r6_r5/34_REMAINING_UNKNOWNS.md`: States that the live-interpretation path is outside the R5 causal map. Canonical source: `artifacts/pr_eg_r6_r5/34_REMAINING_UNKNOWNS.md`.
- `support/artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`: R4-R1 integration verdict C, which R5 does not replace. Canonical source: `artifacts/pr_eg_r6_r4_r1/38_FINAL_VERDICT.md`.
- `support/tests/fixtures/pr_ef_r4_holdouts.json`: Legitimate revision, undo refusal, and empty-pending safeguard that a repair must preserve. Canonical source: `tests/fixtures/pr_ef_r4_holdouts.json`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
