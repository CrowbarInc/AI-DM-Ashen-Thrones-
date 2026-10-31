# Campaign

Campaign: ATGB-R1-02 Mechanical Revision Boundary Repair
Identifier: `atgb_r1_02_mechanical_revision_boundary`
Date: 2026-10-18
Generated: 2026-10-19T01:55:35.094314+00:00
Purpose: Minimal mechanical revision-entry repair with deterministic regressions and separate downstream response inspection.

# Executive Summary

S08.2 no longer enters pending-intention revision solely from “I meant” or a CORRECTION purpose. Implicit revisions require an existing intention referent and interpreted action components; explicit revision requests still reach established safeguards. Legitimate revision holdouts remain intact. Failure class: contract. Targeted tests: 133 passed. Broader: 443 passed / 9 failed; the same nine failures reproduce before repair (338 passed / 347 existing tests). No new failures in the matched slice. Routing PASS in both controlled S08.2 stubs. Empty-evidence response adequacy FAIL: “That has not been established in the information available to you.” Production adequacy NOT EVALUABLE because the historical interpretation/evidence refs were not retained and live calls are prohibited. Verdict B reflects the broader red regression surface and unestablished end-to-end adequacy, not a claim that unrelated failures were caused here. 3,564 protected files unchanged. No live provider calls, unrelated production edits authored, extra model authority or experimental integration. Stop for external review; no ATGB-R1-03.

Objective status: `B — CONDITIONAL; BOUNDED ROUTING REPAIR DEMONSTRATED; EXTERNAL REVIEW REQUIRED`.

# Changes Made

## Production changes

- Only game/conversational_orchestration.py: revision regex/entry gate and CORRECTION fallthrough; existing action/status/scene/disclosure owners retained.

## Validation changes

- 105 new deterministic boundary, counterexample, ambiguity, response-plan and API-state tests. Existing tests, frozen fixtures and ATGB judgments unchanged.

## Tooling changes

- Campaign-local offline trace/evidence/report scripts; no reusable tool or production framework changed.

## Documentation changes

- Eight requested reports plus index and canonical docs/NEXT_SESSION.md update.

## Generated artifacts

- Exact test commands, exit codes, XML/logs, matched baseline failure evidence, S08.2 before/after trace, hashes, scoped diffs, repository status, standardized evidence packet and review ZIP.

# What Was Tested

- **Focused tests:** 133 passed, 0 failed, exit 0: 105 new regressions + all 28 frozen PR-EF-R4 authorization tests.
- **Broader relevant tests:** 452 tests: 443 passed / 9 failed, exit 1. Matched pre-repair existing slice: 347 tests, 338 passed / identical 9 failures, exit 1. Exact IDs/logs and commands included.
- **Full suite:** Not run; no full-suite-green claim.
- **Runtime validation:** Two S08.2 response-plan stubs (GM/DESCRIPTION and GM/CORRECTION), preserved prior delivered context, empty selected evidence. Saved original source and repaired source both executed. Routing PASS, stub adequacy FAIL, production adequacy NOT EVALUABLE.
- **Model/runtime boundary:** No live providers. Pytest live-model guard active. HTTP tests ran outside sandbox only to allow Windows local socketpair. Source-level trace has no provider calls.
- **New regressions:** No new failures in matched existing slice. All new tests pass. Initial three new API assertion errors corrected to allow existing delivered-history/save metadata writes while preserving gameplay/intention invariants.
- **Pre-existing failures:** Nine in tests/test_pr_eg_r6_r2_r1_referents.py: eight clarification-vs-unknown failures and missing bound_referent_id in historical-id test. Pre-repair source reproduces all nine. Initial sandbox HTTP attempts interrupted on socketpair accept; environment issue, not game failure.
- **Self-contained bundle review:** Bundle includes eight reports, source/diff/tests, exact commands/exits/counts, original transcript, before/after response-plan trace, matched nine baseline failures, protected hashes, authority/performance/limitations and repository status. ZIP CRC and included-source hashes verified during generation.

# Behavioral Evidence

## Evidence Packet: atgb_r1_02

Runs / turns: `2` / `2`
Runtime/model boundary: Host response plan; interpretation stubbed, no live provider, no expression.

### Representative success

No example observed in this campaign.

### Representative failure

Example: `s08_2_description`
Player classification: `representative_player_behavior, boundary_case`
Player: I meant the people, not the weather.
GM: That has not been established in the information available to you.
Automated result: `FAIL`
Human review: `UNREVIEWED` - External review pending; no authenticated human judgment.
Source: `artifacts/atgb/atgb_r1_02/s08_2_trace.json`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review the bounded repair and conditional verdict before any next pass.
- Separately authorize a controlled new live S08.2 trial only after review if actual evidence selection/response adequacy should be assessed. No live call or ATGB-R1-03 is authorized by this package.

# Known Problems / Unresolved Findings

## Campaign-specific

- Empty-evidence ordinary GM fallback is still inadequate for S08.2; no downstream repair authorized.
- Raw historical provider record missing; actual new production response not evaluated.
- Existing explicit instead/make-that/revise cues remain conservative and can be broad; no universal language classifier claim.

## Pre-existing baseline

- Nine matched PR-EG referent failures remain.
- PR-EG-R6-R4-R1 integration ban remains; R5 is diagnostic only.
- Extensive dirty/untracked worktree predates this pass; no commit/push. Authenticated human ATGB review remains pending.

# Missing Concepts / Future Capabilities

- No new subsystem introduced. Downstream evidence selection/response sufficiency is an observed separate boundary, deferred.

# What This Campaign Does NOT Prove

- End-to-end S08.2 success, broad conversational competence, independent held-out generalization, full-suite green, ATGB performance improvement or any measured latency/token saving.
- No improvement is claimed for PR-EG-R6-R5 historical 0/25 correction results.

# Recommended Next Step

Stop for external review of CURRENT_REVIEW ZIP. After acceptance, consider a separately authorized controlled live S08.2 trial. Do not begin ATGB-R1-03 or another repair in this pass.

# Review Bundle Contents

Bundle file count: `48`
Bundle ZIP size: `000000266925` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_02_mechanical_revision_boundary.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_02_mechanical_revision_boundary.md`.
- `support/artifacts/validation_evidence/atgb_r1_02/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_02/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r1_02/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_02/evidence_manifest.json`.
- `support/game/conversational_orchestration.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `game/conversational_orchestration.py`.
- `support/tests/test_atgb_r1_02_revision_boundary.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `tests/test_atgb_r1_02_revision_boundary.py`.
- `support/tests/test_pr_ef_r4_authorization.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `tests/test_pr_ef_r4_authorization.py`.
- `support/tests/fixtures/pr_ef_r4_holdouts.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `tests/fixtures/pr_ef_r4_holdouts.json`.
- `support/docs/NEXT_SESSION.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `docs/NEXT_SESSION.md`.
- `support/development/reports/atgb_r1_01_s08_2_causal_trace.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_01_s08_2_causal_trace.md`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/data/validation/atgb/visible/S08.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/pr_eg_r6_r5/36_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/pr_eg_r6_r5/32_REPAIR_PRIORITIZATION.md`.
- `support/development/reports/atgb_r1_02/01_implementation_summary.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/01_implementation_summary.md`.
- `support/development/reports/atgb_r1_02/02_routing_contract.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/02_routing_contract.md`.
- `support/development/reports/atgb_r1_02/03_regression_evidence.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/03_regression_evidence.md`.
- `support/development/reports/atgb_r1_02/04_s08_2_before_after_trace.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/04_s08_2_before_after_trace.md`.
- `support/development/reports/atgb_r1_02/05_authority_preservation.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/05_authority_preservation.md`.
- `support/development/reports/atgb_r1_02/06_performance_assessment.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/06_performance_assessment.md`.
- `support/development/reports/atgb_r1_02/07_remaining_conversational_limitations.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/07_remaining_conversational_limitations.md`.
- `support/development/reports/atgb_r1_02/08_final_verdict.md`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `development/reports/atgb_r1_02/08_final_verdict.md`.
- `support/artifacts/atgb/atgb_r1_02/implementation.diff`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/implementation.diff`.
- `support/artifacts/atgb/atgb_r1_02/session_handoff.diff`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/session_handoff.diff`.
- `support/artifacts/atgb/atgb_r1_02/s08_2_trace.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/s08_2_trace.json`.
- `support/artifacts/atgb/atgb_r1_02/capture_trace.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/capture_trace.py`.
- `support/artifacts/atgb/atgb_r1_02/orchestration_before.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/orchestration_before.py`.
- `support/artifacts/atgb/atgb_r1_02/baseline_hashes.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/baseline_hashes.json`.
- `support/artifacts/atgb/atgb_r1_02/preservation_check.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/preservation_check.json`.
- `support/artifacts/atgb/atgb_r1_02/test_commands.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/test_commands.json`.
- `support/artifacts/atgb/atgb_r1_02/test_summary.json`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/test_summary.json`.
- `support/artifacts/atgb/atgb_r1_02/targeted.xml`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/targeted.xml`.
- `support/artifacts/atgb/atgb_r1_02/targeted.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/targeted.txt`.
- `support/artifacts/atgb/atgb_r1_02/targeted_exit.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/targeted_exit.txt`.
- `support/artifacts/atgb/atgb_r1_02/final.xml`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/final.xml`.
- `support/artifacts/atgb/atgb_r1_02/final.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/final.txt`.
- `support/artifacts/atgb/atgb_r1_02/final_exit.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/final_exit.txt`.
- `support/artifacts/atgb/atgb_r1_02/pre_repair.xml`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/pre_repair.xml`.
- `support/artifacts/atgb/atgb_r1_02/pre_repair.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/pre_repair.txt`.
- `support/artifacts/atgb/atgb_r1_02/verified.xml`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/verified.xml`.
- `support/artifacts/atgb/atgb_r1_02/verified.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/verified.txt`.
- `support/artifacts/atgb/atgb_r1_02/diagnose.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/diagnose.txt`.
- `support/artifacts/atgb/atgb_r1_02/repository_status_before.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r1_02/repository_status_after.txt`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r1_02/run_pre_repair_regression.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/run_pre_repair_regression.py`.
- `support/artifacts/atgb/atgb_r1_02/build_evidence.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/build_evidence.py`.
- `support/artifacts/atgb/atgb_r1_02/prepare_reports.py`: Explicit implementation, validation, preserved-baseline or review provenance supporting the eight requested reports. Canonical source: `artifacts/atgb/atgb_r1_02/prepare_reports.py`.

## Explicit omissions

- `artifacts/atgb/atgb_r1_02/pre_repair_exit.txt`: duplicate content of artifacts/atgb/atgb_r1_02/final_exit.txt; canonical reference retained
- `artifacts/atgb/atgb_r1_02/verified_exit.txt`: duplicate content of artifacts/atgb/atgb_r1_02/final_exit.txt; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
