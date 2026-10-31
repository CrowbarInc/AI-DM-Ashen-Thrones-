# Constitution Amendment Proposal — Progress, Failure, and Benchmark Governance

Date: 2026-10-18
Status: adopted 2026-10-18 with refinements. The adopted text is in `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/review_handoff_standard.md`, `docs/validation_evidence_standard.md`, and `docs/product_realization_validation.md`. This file is the historical proposal. Where its wording differs from those documents, the adopted documents govern. Adoption record: `development/reports/constitution_amendment_adoption_progress_and_benchmark_governance.md`.
Pass type: historical proposal. The adoption pass is separate.
Identifier: `constitution_progress_governance_review_20261018`

This file records the proposal pass. That pass did not implement the amendments. A later pass the same day adopted them with the refinements named in the adoption record. Do not apply the wording in §5 over the adopted documents. The proposal pass did not create the Ashen Thrones Gameplay Benchmark and did not change production code, evaluators, or replay classification.

## 1. Summary of existing governance

`docs/DEVELOPMENT_CONSTITUTION.md` (established 2026-09-19) is the standing repository-wide development process. No separate amendment file exists. The document is 255 lines and already says it must stay small, must not copy specialized doctrine, and must not be amended for campaign-specific behavior.

What it already requires:

- Read the Constitution, `docs/NEXT_SESSION.md`, and the authorities that handoff names before substantive work.
- Keep the working set small. Do not reload historical campaigns by default.
- Leave settled decisions settled unless new evidence challenges them.
- Make the smallest change the evidence justifies. Escalate when the current architecture cannot represent the required behavior. Do not turn every defect into a redesign.
- Use existing validation authorities. Do not invent PASS criteria, weaken tests, or treat structural validation as semantic success.
- Update `docs/NEXT_SESSION.md` when material work changes project state. The listed orientation fields are already long. Detailed evidence stays in the report the handoff points to.
- On exit, validate in proportion to the task, inspect the diff, separate pre-existing worktree state, and place new files with their owners.
- If authorities conflict, investigate. Do not pick the convenient one.

The Constitution delegates domain doctrine. The authorities that matter for this proposal are:

| Concern | Authority | What it already decides |
| --- | --- | --- |
| Session orientation | `docs/NEXT_SESSION.md` | Current objective, settled decisions, validation baseline, next action. Human-maintained. Not a generated review. |
| Review ZIP | `docs/review_handoff_standard.md` | When a full `handoff/CURRENT_REVIEW.md` + `CURRENT_REVIEW.zip` is required, what the summary must contain, and how a review-requiring campaign ends. |
| Player-facing evidence | `docs/validation_evidence_standard.md` | Structural, runtime, semantic, human-realism, stress, and human-reviewed claims stay separate. A green check is not semantic quality. Packets record what remains unproven. |
| Systemic Product Realization claims | `docs/product_realization_validation.md` | Scenario content may be specific. A claimed general owner needs scenario-independent fixtures with unrelated vocabulary. |
| Playability scores | `docs/playability_validation.md` | Scores come only from `evaluate_playability`. Four short scenarios. PASS is the heuristic contract, not proof that gameplay is acceptable. |
| Calibrated semantic authority | `docs/semantic_validation_calibration.md` | Mandatory gates include `player_intent_addressed` and `malformed_output`. Diagnostic score is not semantic authority. |
| Structural replay acceptance | `docs/testing/protected_replay_manifest.md`, `tests/README_TESTS.md` | Protected replay is a hard structural CI check. Stubbed GM text. PASS does not establish live semantic or narrative quality. |
| Test cost lanes | `tests/README_TESTS.md` | Fast lane excludes `transcript` and `slow`. Full lane is for pre-merge, milestones, or the whole regression surface. |
| Portfolio procedure | `development/campaigns/product_realization/PR-AA_product_realization_portfolio_bootstrap.md` §16 | Focused owner tests. Architectural review only for missing ownership, unusable contracts, contradictory state ownership, unavoidable hidden coupling, or a product requirement the chassis cannot satisfy. |
| Architecture ownership | `development/campaigns/reconciliation/AR-AD_target_architecture_doctrine.md` | One transaction spine, domain owners, narration that does not create runtime truth. New simplification only when it improves understanding and preserves behavior. Multi-axis ownership is intentional for fallback, final emission, and replay. |
| Replay failure rows | `tests/failure_classification_contract.py`, `docs/audits/CG_failure_classification_authority_registry.md` | Closed taxonomy for replay rows: `route`, `speaker`, `fallback`, `emission`, `semantic_mutation`, `replay_drift`, `projection`, `validator`, `evaluator`, `continuity`, `normalization`, `sanitizer`. |
| Generated governance refresh | `docs/governance_refresh_workflow.md` | Refresh the smallest downstream artifact. A refresh must not add enforcement. |
| Where this proposal lives | `docs/audits/documentation_governance.md` | Organization reports belong in `development/reports/` until they become standing governance. |

Codex and Cursor do not have a second standing pass manual. The Constitution already binds both. `docs/realization_cursor_handoff.md`, `docs/realization_triage_ledger.md`, and `docs/audits/scaffolds/codex_bg_recon_blocks.txt` are Realization-era seam notes and block lists. They are not the current development-block procedure. `.cursor/rules/oc-actionability.mdc` governs in-character option blocks, not development process.

The mandatory ZIP is not in the Constitution. `docs/review_handoff_standard.md` requires a full handoff for player-facing, semantic, architectural, evaluator, or externally reviewed work, and explicitly allows a lightweight handoff or ordinary completion note for tiny structural changes, routine maintenance, and local unit-only work. Campaign exit order is: implement, validate, write the report and evidence packets, update the handoff config, generate the ZIP, verify it, stop.

Habit, not standing rule:

- Product Realization closeouts often name a "first incorrect decision" and refuse a second router, embeddings, or a new subsystem. Those refusals live in `docs/NEXT_SESSION.md` as settled decisions. They are not a general justification rule.
- `docs/remaining_baseline_triage_and_root_cause_confirmation.md` classified one baseline as product, architecture, validation, stale expectation, fixture, governance drift, policy, or unresolved. That was a campaign method. It says classification is not root-cause proof.
- `docs/rc11_rc13_unresolved_root_cause_investigation.md` is a specific unresolved investigation, not a general procedure.

No Ashen Thrones Gameplay Benchmark exists. The nearest instruments are the four-scenario playability runner, the semantic calibration corpus, protected replay, and campaign-specific holdouts such as PR-EG. None of them is a 30–40 turn communication benchmark with a fixed set and held-out variations.

## 2. Gap and overlap analysis

### Already covered, do not copy

- Smallest-change and "do not redesign from one defect" are Minimal Change.
- Structural PASS is not semantic success. Validation Discipline, the evidence standard, playability doctrine, and protected-replay doctrine all say this.
- Scenario reproduction is not a systemic owner. `docs/product_realization_validation.md` already makes unrelated-vocabulary fixtures a hard gate for that claim.
- Full ZIP versus lightweight completion is already proportional.
- Fast lane versus full suite already keeps expensive tests off routine changes.
- Architectural review already has a trigger in PR-AA §16. A new review board would duplicate it.
- Evidence packets already require representative success and failure, disagreements, and what remains unproven.
- The review summary already separates focused, broader, full-suite, and runtime evidence, and has "What This Campaign Does NOT Prove."

### Missing

- A development failure class that selects the repair. Replay categories answer a different question and must not be reused as the labels below.
- A standing requirement to name the earliest demonstrable incorrect decision for a substantial failure, and an explicit exemption for trivial isolated defects.
- A required distinction between "the original case is fixed," "related variations improved," and "unrelated behavior was preserved." Campaigns can currently describe the first as a general solution.
- A short justification rule when someone adds a subsystem, fallback, or decision authority. Campaign habit does this. The Constitution only says to escalate when the chassis cannot represent the behavior.
- A required progress split: implementation completion, regression, generalization, gameplay benchmark, remaining limitations. Current reports can put all of that under one PASS.
- Any governance for a communication-focused gameplay benchmark, including checkpoint cadence and fixed versus held-out cases.
- Review-summary wording that forces those distinctions into the ZIP the project already generates.

### Overlap to avoid

- Do not add development classes to `ALLOWED_FAILURE_CATEGORIES`. "Semantic" and "evaluation" would collide with `semantic_mutation` and `evaluator`.
- Do not turn protected replay, the playability evaluator, or semantic calibration into the gameplay benchmark.
- Do not add a second ZIP, a second session handoff, or a mandatory provider call.
- Do not copy the scenario-independent fixture gate into the Constitution. Point to it.
- Do not require architectural review for every new helper. Justification is a paragraph. Review stays on the existing PR-AA trigger.
- Do not extend `docs/NEXT_SESSION.md`'s field list. It is already too long for the Constitution's own "remain concise" rule. Put the new distinctions in the review summary.

### Contradictions and stale surfaces

- The instruction for this review described the ZIP as constitutional. The ZIP is a specialized authority the Constitution names and does not restate. That is delegation, not a conflict. A one-line pointer is enough so a reader of the Constitution can find it.
- `docs/NEXT_SESSION.md` was last updated 2026-09-26 for PR-BL and still says stop and do not start PR-BM. `handoff/CURRENT_REVIEW.md` at the start of this pass was PR-EG-R6-R4-R1 (2026-10-18) and says stop and await external review, do not begin PR-EH. The Constitution says to investigate that kind of discrepancy. This pass did not reconcile product orientation. The PR-EG review remains at `handoff/history/pr_eg_r6_r4_r1_source_alignment_20261018/`. Reconciling those two handoffs is a separate product-orientation task.
- `docs/playability_validation.md` forbids a second scorer that reinterprets `evaluate_playability`. A gameplay benchmark that emits its own pass/fail by wrapping that function would violate that authority. The benchmark has to be a separate, transcript-backed checkpoint, not a new mode of the playability runner.
- Calling every development block a full ZIP would contradict the review standard's lightweight exception. This proposal keeps that exception.

### Mapping the requested items

| Request | Disposition |
| --- | --- |
| A. Failure classification | New short Constitution section. Six development classes. Explicitly not the replay taxonomy. |
| B. Root-cause analysis | Same section. Earliest demonstrable incorrect decision for substantial failures only. |
| C. Generalization testing | Constitution claim rule, plus two sentences in `docs/product_realization_validation.md` so systemic claims still use the existing fixture gate. |
| D. Architectural restraint | Extend Minimal Change. Reuse the PR-AA architectural-review trigger. Do not add a new review process. |
| E. Progress measurement | Extend Validation Discipline. Surface the split through the existing review summary. |
| F. Benchmark governance | New section in `docs/validation_evidence_standard.md`, not a new manual and not a corpus. Constitution only limits cadence and claims. |
| G. Handoff integration | Extend the review-summary contract. No generator change in the amendment. Existing fields hold the facts. |

## 3. Recommended amendments

Adopt the wording in §5 as one review package:

1. Amend the Constitution in place. Add two short sections, Failure Investigation and Task Proportion. Extend Minimal Change, Validation Discipline, and Session Exit. Add two delegated authorities. Do not add progress fields to the NEXT_SESSION list.
2. Amend `docs/review_handoff_standard.md` so a full review summary states the progress split, using the sections it already has.
3. Amend `docs/validation_evidence_standard.md` with the benchmark rules. Do not add scenarios, runners, or provider calls.
4. Amend `docs/product_realization_validation.md` with a cross-reference only.

Do not adopt a new top-level governance document. The evidence standard already owns "what player-facing evidence means." The benchmark section belongs there because a benchmark that does not produce inspectable exchanges would recreate the failure that standard was written to stop.

Do not change `tools/build_review_handoff.py` in the same amendment. The current summary can carry purpose, outcome, failure class, original versus related results, regression, benchmark, limitations, and what changed. A later tooling change is justified only if those prose fields prove easy to skip.

## 4. Exact sections that should change

| Document | Section | Change |
| --- | --- | --- |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Authority and Delegation | Add two bullets to the specialized-authority list. |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Minimal Change | Append the architectural-restraint paragraphs. |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Validation Discipline | Append the progress-claim rules. |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Failure Investigation | Insert a new section after Validation Discipline. |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Task Proportion | Insert a new section after Failure Investigation. |
| `docs/DEVELOPMENT_CONSTITUTION.md` | Session Exit | Append the ZIP pointer and the proportion sentence. |
| `docs/review_handoff_standard.md` | Review summary contract | Append the progress-claim paragraph. |
| `docs/validation_evidence_standard.md` | Ashen Thrones Gameplay Benchmark | Insert a new section after Completion-report requirement. |
| `docs/product_realization_validation.md` | Content may be specific. Systems must be general. | Append the cross-reference paragraph. |

No change to Canonical Session Handoff's field list. No change to the replay failure contract, playability runner, protected replay, semantic calibration corpus, or handoff generator.

## 5. Proposed wording

Wording below is the text to insert. It is not in force.

### `docs/DEVELOPMENT_CONSTITUTION.md` — Authority and Delegation

Add to the specialized-authority list:

```text
- development failure classes and task proportion, stated in this
  Constitution; they do not modify replay failure classification;
- the Ashen Thrones Gameplay Benchmark, stated in
  `docs/validation_evidence_standard.md`, for checkpoint claims about
  player–AI-DM communication.
```

### `docs/DEVELOPMENT_CONSTITUTION.md` — Minimal Change

Append:

```text
A new subsystem, fallback mechanism, or decision authority needs an
explicit justification in the campaign report. The justification names
the existing owner that was considered and why that owner cannot carry
the behavior without breaking a settled contract. Where practical, the
change consolidates or replaces an existing responsibility instead of
adding a parallel path.

That justification is not an architectural review. Open an architectural
review only under the existing Product Realization rule: missing
ownership, an unusable contract, contradictory state ownership,
unavoidable hidden coupling, or a product requirement the current owners
cannot satisfy.
```

### `docs/DEVELOPMENT_CONSTITUTION.md` — Validation Discipline

Append:

```text
Keep these claims separate. Do not collapse them into one PASS:

- implementation completion: the scoped change exists and its focused
  checks passed;
- regression: established behavior outside the change still holds, at
  the scope actually run;
- generalization: related variations improved, not only the original
  reproduction;
- gameplay benchmark: the designated communication benchmark was run;
- remaining limitations: what is still unproven or uncertain.

A repair that resolves only its original reproduction is a reproduced
repair. That result alone is not a generalized solution.

Unrelated established behavior is regression, and it uses the lanes
already defined for the work. A systemic engine claim remains governed
by `docs/product_realization_validation.md`.

Passing implementation tests is not improved gameplay. Protected replay,
the playability evaluator, and semantic calibration keep their existing
authorities and do not become a gameplay benchmark by being green.
```

### `docs/DEVELOPMENT_CONSTITUTION.md` — new section after Validation Discipline

```text
## Failure Investigation

A significant failure is classified before a substantial repair is
described as complete. Use one primary class:

- implementation: the intended contract was not carried out in code or
  data;
- contract: the stated contract is incomplete, contradictory, or is not
  the behavior the product requires;
- architectural: no current owner can represent the required behavior,
  or owners conflict;
- semantic: player-facing meaning is wrong even though the structural
  path ran;
- evaluation: the test, scorer, or benchmark misstates the behavior;
- unresolved: the evidence does not yet support one of the above.

These classes guide the repair. An implementation defect is fixed in the
owning code. A contract defect is decided as a contract change before
product behavior is changed to satisfy it. An architectural defect is
escalated under Minimal Change rather than patched with another local
path. A semantic defect needs player-facing evidence. An evaluation
defect is fixed in the instrument or the claim, not by changing the
product to satisfy a bad instrument. Unresolved stays unresolved.

This vocabulary is for development decisions. It does not change replay
failure classification.

For a substantial failure, name the earliest demonstrable incorrect
decision and repair that cause when it is established. Do not spend the
repair on a downstream symptom while that earlier cause is already
shown.

A trivial, isolated defect does not require that investigation. A normal
defect note is enough.
```

### `docs/DEVELOPMENT_CONSTITUTION.md` — new section after Failure Investigation

```text
## Task Proportion

Match the procedure to the task. Do not put a benchmark run or a live
provider call on routine work.

A small, isolated repair uses focused checks around the owner. It does
not require a failure essay, a related-variation suite, a full suite, a
provider call, or a gameplay benchmark. Use a lightweight handoff or an
ordinary completion note, as the review-handoff standard already allows.

A moderate functional change uses focused checks and the relevant
regression slice. If the report claims a systemic or player-facing
improvement, include at least one related variation and say whether it
passed. State the limitation if that variation was not run. A full suite
or a provider call is required only when the change touches a boundary
those lanes actually protect. Generate the standard review handoff when
that standard says a full handoff is required.

A major architectural change includes the Minimal Change justification
when it adds a subsystem, fallback, or decision authority. It includes
architectural review when the existing trigger is met. It reports what
was consolidated or replaced. A gameplay benchmark is still not
automatic. Run it when the change is intended to move player–AI-DM
communication, or when a benchmark checkpoint is otherwise due.

A benchmark or evaluation-only pass does not change production behavior
in order to improve a score. Instrument results and product claims stay
separate. Provider calls and benchmark execution belong to this class
and to declared checkpoints.
```

### `docs/DEVELOPMENT_CONSTITUTION.md` — Session Exit

Append:

```text
Validation follows Task Proportion. A small repair does not grow into a
benchmark run or a full-suite claim.

When the review-handoff standard requires a full handoff, generate
`handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`. That bundle
is the review surface for purpose, outcome, failure class, original and
related results, regression, benchmark results when a benchmark was run,
known limitations, and what changed. Do not create a second bundle for
the same facts. `docs/NEXT_SESSION.md` points to that review and stays
an orientation document.
```

### `docs/review_handoff_standard.md` — Review summary contract

Append:

```text
When the campaign investigated a significant failure or claims a repair,
the summary keeps these facts distinct, using the sections already
defined above rather than a new report:

- purpose and outcome;
- failure class, when Failure Investigation applies;
- the original reproduction, separate from related variations;
- regression scope and result, separate from generalization;
- gameplay benchmark result, or an explicit statement that no benchmark
  was run;
- known limitations and uncertainty;
- a concise description of what changed.

A reproduced repair is not described as a generalized solution. A green
implementation test is not described as improved gameplay. No benchmark
result is reported unless the Ashen Thrones Gameplay Benchmark section
of the Validation Evidence Standard was actually used.
```

### `docs/validation_evidence_standard.md` — new section after Completion-report requirement

```text
## Ashen Thrones Gameplay Benchmark

The Ashen Thrones Gameplay Benchmark is a checkpoint instrument for
player–AI-DM communication. It is not in force until a reviewed corpus
exists. This section governs that future corpus. It does not create one,
does not add a scorer, and does not change `evaluate_playability`,
semantic calibration, or protected replay.

The initial benchmark is about communication: intent recognition,
conversational continuity, corrections, relevance, dialogue coherence,
IC/OOC separation, ambiguity handling, conversational initiative,
narration quality, and response efficiency. Combat, inventory, character
creation, and other mechanical systems are outside that initial
benchmark except where a turn needs them in order to exercise
conversational interpretation.

The initial corpus is about 30–40 representative turns. Each turn is
labeled before any run as either a fixed scenario or a held-out
variation. Held-out variations are for measuring generalization. They
are not a tuning set for the change under test. Fixed and held-out
results are reported separately.

A benchmark run produces inspectable exchanges under this evidence
standard. An aggregate is orientation only. The run states the runtime
and model boundary, what was not covered, and which results are
human-reviewed. It does not report a single PASS that means the AI-DM
works.

Run the benchmark at a meaningful checkpoint: a declared communication
milestone, a major change whose purpose is to move player–AI-DM
communication, or when the previous benchmark no longer describes
current behavior. Do not run it after every development block. Do not
require a provider call merely because a block closed.

Until a reviewed corpus is adopted, no campaign may report an Ashen
Thrones Gameplay Benchmark result.
```

### `docs/product_realization_validation.md` — end of "Content may be specific. Systems must be general."

Append:

```text
A systemic claim is a generalization claim under the Constitution. The
original reproduction, the scenario-independent variations, and the
unrelated regression result stay separate. Passing the original
calibration scenario does not satisfy the fixture gate in this
document.
```

## 6. Requirements that should remain outside the Constitution

Leave these where they are, or leave them unimplemented:

- Replay failure categories, owners, and recurrence keys.
- The scenario-independent fixture gate, except for the one-paragraph cross-reference above.
- Evidence-packet schema, deterministic selection, and human-review states.
- Playability scenario ids, evaluator axes, and the prohibition on a second scorer.
- Semantic calibration cases and mandatory-gate definitions.
- Protected replay manifests and CI hard-fail rules.
- Fast-lane and full-lane pytest commands.
- The actual 30–40 benchmark turns, grading sheets, and any runner. Those wait for a later corpus review. This proposal does not authorize writing them.
- Generator fields for failure class or benchmark status. Use the existing summary until practice shows the prose is being skipped.
- Codex-versus-Cursor seam lists from the Realization era.
- Product-era reconciliation of `docs/NEXT_SESSION.md` with later PR cycles. That is orientation maintenance, not a constitutional rule.
- Provider, model, and cost policy. The proportion rules only say routine blocks do not require a provider call.

## 7. Expected effects on ordinary development passes

A small isolated repair is unchanged: focused tests, a short completion note, no provider call, no benchmark, no failure essay.

A moderate functional change adds a few sentences to the review summary the campaign already generates: original result, whether a related variation was run, regression scope, and what is still unproven. It does not add a new artifact type. A provider call or full suite is still justified by the boundary that was touched, not by the existence of this amendment.

A major architectural change adds the justification paragraph when a new subsystem, fallback, or decision authority is introduced, and it reuses the existing architectural-review trigger. The benchmark runs only if that change is a communication checkpoint.

An evaluation-only pass may run the benchmark after a corpus exists. It must not edit production code to chase the score.

`docs/NEXT_SESSION.md` still records outcome, pending decisions, and pointers. It does not gain a second copy of the benchmark report.

No new mandatory command is added to session exit except the ZIP the review standard already requires for review-requiring work.

## 8. Procedural overhead and conflicts

- The six classes will become ceremony if they are applied to typos. Task Proportion forbids that. Reviewers should reject class labels on trivial defects.
- "Earliest incorrect decision" can turn into an unbounded trace. The rule stops at the earliest decision the evidence already demonstrates. It does not require a new tracing subsystem.
- "Meaningful checkpoint" can be stretched to mean every block, or avoided forever. The benchmark section names three triggers and forbids per-block runs. A checkpoint still needs a human decision until a corpus exists.
- Putting the benchmark in the evidence standard keeps one evidence language. It will be a conflict if a later change adds an automatic benchmark score. The proposed section forbids that.
- The development class `evaluation` is not the replay category `evaluator`. The development class `semantic` is not `semantic_mutation`. The Constitution wording says the vocabularies are distinct. Do not "synchronize" them in a governance refresh.
- Architectural restraint can be misread as a ban on new owners. The wording allows a new owner when an existing owner cannot carry the behavior, and it points at the existing review trigger.
- Replacing `handoff/CURRENT_REVIEW.*` is how the review standard works. This review's generation does that. The previous PR-EG-R6-R4-R1 export remains in `handoff/history/pr_eg_r6_r4_r1_source_alignment_20261018/`. This proposal does not close that campaign.
- `docs/NEXT_SESSION.md` is stale relative to that PR-EG review. Updating it to match later product cycles was out of scope. A pending-decision pointer for this proposal is the only orientation edit this pass makes.
- Adopting the Constitution pointer to the benchmark section before adopting that section would create a dangling authority. Adopt the four document edits together, or do not adopt the pointer.

## What this pass did not do

- Did not edit the Constitution or the specialized standards.
- Did not implement a benchmark corpus, runner, or provider evaluation.
- Did not change production code, tests, evaluators, or replay classification.
- Did not reconcile PR-BL session orientation with later Product Realization cycles.
- Did not treat a read of governance documents as permission to start the next product cycle.
