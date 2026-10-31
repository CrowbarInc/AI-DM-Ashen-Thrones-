# Constitution Amendment Adoption — Progress, Failure, and Benchmark Governance

Date: 2026-10-18
Status: adopted
Pass type: governance amendment. No gameplay change.
Identifier: `constitution_progress_governance_amendment_20261018`

Starting point: `development/reports/constitution_amendment_proposal_progress_and_benchmark_governance.md`.

This pass adopted that proposal inside the existing authorities and applied the accepted refinements. It did not create a second Constitution, handoff process, or validation authority. It did not implement the Ashen Thrones Gameplay Benchmark.

## Amendment summary

Adopted in place:

| Document | What changed |
| --- | --- |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Failure classes and task proportion stay in this Constitution. Minimal Change now requires a justification before a new subsystem, fallback, or decision authority, and it points at the existing PR-AA architectural-review trigger. Validation Discipline separates implementation, original reproduction, related variations, independent generalization, regression, benchmark, and limitations. Session Exit points at the existing review ZIP. |
| `docs/review_handoff_standard.md` | A full review summary keeps those facts distinct in the sections it already has. No new report and no new generator fields. |
| `docs/validation_evidence_standard.md` | New Ashen Thrones Gameplay Benchmark section. It governs a future corpus. It does not create one. |
| `docs/product_realization_validation.md` | Cross-reference only. The scenario-independent fixture gate remains the hard gate for a claimed general owner. |

`docs/README.md` index line for the Constitution was updated so the layout list matches that delegation. `docs/NEXT_SESSION.md` records adoption and leaves product orientation unchanged.

## Refinements applied to the proposal

- Failure classes are provisional investigative judgments. One primary class is selected when the evidence supports one. The class may change when later evidence shows an earlier or more fundamental cause. Trivial defects do not get multiple labels or a failure essay.
- Repair evidence has three levels: original reproduction, related variations, and independent generalization. A limited repair may be accepted without all three. A claim of broad conversational improvement has to name the level that supports it. Variations written with the implementation are not held-out evidence.
- Routine repairs do not require a live-provider evaluation.
- ATGB's primary purpose is player-AI-DM communication: natural communication, coherent conversation, relevant responses, and recovery from ambiguity or misunderstanding. Combat mechanics, inventory management, character creation, economy, and other mechanical subsystems stay outside the initial scope except where a turn needs them to exercise communication.
- ATGB stays distinct from the playability evaluator, protected replay, semantic calibration, and campaign-specific regression suites. It does not reinterpret playability PASS or FAIL.
- Benchmark results are reported by capability and evidence level.
- Checkpoint triggers remain milestone-based. Communication-related development cannot continue indefinitely without reconsidering a rerun. The interval belongs to a future operating procedure. No block count is a constitutional requirement. Closing a block does not require a provider call.
- Until a reviewed corpus exists, no ATGB result may be claimed.
- The architectural-review sentence uses the existing PR-AA trigger, including "a real product requirement the chassis cannot satisfy," so this amendment does not publish a second trigger.

## Documentation consistency findings

1. The Constitution delegates specialized authority. ATGB claims point at `docs/validation_evidence_standard.md`. Systemic owner claims still point at `docs/product_realization_validation.md`. Full review export still points at `docs/review_handoff_standard.md` and `handoff/CURRENT_REVIEW.*`. Architectural review still points at PR-AA. Failure classes and task proportion are reserved in the Constitution and are not a separate document.
2. The new development classes do not enter replay classification. `semantic` is not `semantic_mutation`. `evaluation` is not `evaluator`. `tests/failure_classification_contract.py` was not edited.
3. ATGB does not wrap `evaluate_playability`, does not add a scorer, and does not reinterpret playability PASS or FAIL. `docs/playability_validation.md` was not edited.
4. No new mandatory provider call was added. Routine work, block close, and reconsideration before a corpus all refuse a required provider call.
5. Small repairs keep the lightweight handoff or ordinary completion note. The new summary distinctions apply when a campaign investigated a significant failure or claims a repair. A routine repair does not need placeholder lines.
6. `handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip` remain the review artifact. The generator was not changed. Existing summary sections can carry implementation outcome, evidence levels, regression, ATGB availability, limitations, uncertainty, and failure class in prose.
7. The amended documents name one another. The historical proposal now says the adopted documents govern where §5 differs.

No gameplay improvement is claimed. Documentation changes do not show that players can communicate more successfully.

## Unresolved governance conflicts

One item remains open, and it is outside this amendment:

`docs/NEXT_SESSION.md` still orients the product at the 2026-09-26 PR-BL closeout and says stop, do not start PR-BM. Later Product Realization history, including PR-EG-R6-R4-R1, remains at `handoff/history/pr_eg_r6_r4_r1_source_alignment_20261018/`. This pass records that discrepancy as pending maintenance. It does not reconcile it. Session orientation stays `docs/NEXT_SESSION.md`.

No conflict was found between the adopted text and the playability evaluator, the replay classification contract, or the review ZIP. The absence of a reviewed ATGB corpus is intentional: the benchmark section governs that future corpus and forbids claiming a result until the corpus is adopted.

## What this pass did not do

- Did not implement ATGB scenarios, runners, scoring tools, or a benchmark operating procedure.
- Did not change production gameplay, tests, evaluators, calibration cases, or replay classification.
- Did not add generator fields to `tools/build_review_handoff.py`.
- Did not reconcile PR-BL session orientation with later Product Realization cycles.
- Did not call a model provider.
