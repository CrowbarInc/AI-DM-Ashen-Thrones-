# Development Constitution

Date established: 2026-09-19
Last amended: 2026-10-18

`docs/DEVELOPMENT_CONSTITUTION.md` is the standing repository-wide authority for
how development agents enter, conduct, and hand off material work on Ashen
Thrones.

It governs development process. It does not replace specialized authorities for
architecture, validation, Product Realization, documentation, review exports,
gameplay rules, or other domains.

It applies regardless of implementation agent or interface, including Codex,
Cursor, ChatGPT-assisted workflows, and future agents.

## Authority and Delegation

This Constitution governs repository-wide development process only.

When a specialized authoritative document governs a domain, follow that
authority for domain-specific behavior unless a later explicit authority
supersedes it. Being repository-wide does not let this Constitution silently
override established domain doctrine.

Current specialized authorities include, without attempting a complete catalog:

- architecture doctrine (`development/campaigns/reconciliation/AR-AD_target_architecture_doctrine.md`
  and later Reconciliation closeouts);
- state-authority doctrine (`docs/state_authority_model.md`);
- validation doctrine, including the current handoff's validation-authority
  hierarchy;
- Product Realization portfolio and process (`development/campaigns/product_realization/PR-AA_product_realization_portfolio_bootstrap.md`);
- documentation governance (`docs/audits/documentation_governance.md`);
- generated-governance refresh (`docs/governance_refresh_workflow.md`);
- review-handoff export (`docs/review_handoff_standard.md` →
  `handoff/CURRENT_REVIEW.*`);
- development failure classes and task proportion, stated in this
  Constitution and not in a separate document; they do not modify replay
  failure classification;
- the Ashen Thrones Gameplay Benchmark, stated in
  `docs/validation_evidence_standard.md`, for checkpoint claims about
  player-AI-DM communication;
- campaign-specific authoritative reports under `development/campaigns/`;
- current-session orientation (`docs/NEXT_SESSION.md`).

Review handoff and session handoff are different surfaces. Generated
`handoff/CURRENT_REVIEW.*` files are review exports. `docs/NEXT_SESSION.md` is
the human-maintained session orientation file. Do not edit generated review
mirrors as source.

If two authorities genuinely conflict, investigate provenance and scope. Do not
silently choose the more convenient instruction.

## Session Entry

Before beginning substantive repository work, a development agent MUST read:

1. `docs/DEVELOPMENT_CONSTITUTION.md`
2. `docs/NEXT_SESSION.md`
3. the authoritative documents `NEXT_SESSION.md` identifies as necessary for
   the current task

Then inspect task-specific repository evidence as needed. Do not reread the
entire historical repository. The goal is low-context continuity.

## Agent Working Set

Agents should normally load only:

1. this Constitution
2. `docs/NEXT_SESSION.md`
3. authorities and evidence that `NEXT_SESSION.md` explicitly names
4. the current task's source, tests, and data

Historical campaign reports and archive material should be retrieved only when
`NEXT_SESSION.md` points to them, current evidence requires reopening a settled
decision, or an audit explicitly requires historical comparison.

Do not recursively load `development/campaigns/`, `development/archive/`,
`docs/audits/`, `audits/`, `handoff/history/`, or `artifacts/` by default.

## Settled Decisions

Do not casually reopen decisions that the current handoff or authoritative
documents identify as settled.

A settled decision may be revisited when new repository or runtime evidence
materially challenges the assumptions or behavior on which that decision was
based. A new agent, new session, different implementation preference, or
alternate stylistic preference is not sufficient reason to reopen settled work.

This protects continuity. It does not freeze architecture permanently.

Settled-decision contents live in the current handoff and the specialized
authorities it points to. Do not copy those decisions into this Constitution.

## Minimal Change

Make the smallest change justified by the active task and evidence.

Material unrelated defects may be documented or deferred. Do not absorb them
automatically into the current task, and do not turn every discovered problem
into an architectural redesign, broad cleanup, refactor, new framework, or
policy reconsideration.

This is scope control, not a ban on architectural evolution. When evidence
shows existing architecture cannot represent required behavior, record that
friction and escalate it through the appropriate process.

A new subsystem, fallback mechanism, or decision authority needs an
explicit justification in the campaign report. The justification names
the existing owner that was considered and why that owner cannot carry
the behavior without breaking a settled contract. Where practical, the
change consolidates or replaces an existing responsibility instead of
adding a parallel path.

That justification is not an architectural review. Open an architectural
review only under the existing Product Realization rule in
`development/campaigns/product_realization/PR-AA_product_realization_portfolio_bootstrap.md`:
missing ownership, an unusable contract, contradictory state ownership,
unavoidable hidden coupling, or a real product requirement the chassis
cannot satisfy.

## Validation Discipline

Preserve and use the repository's established validation authorities. Do not
invent convenient PASS criteria.

Detailed validation semantics belong to the existing validation documents and
the current handoff. In substance:

- run validation appropriate to the work performed;
- do not weaken tests or redefine expected behavior merely to make a change
  pass;
- distinguish environmental or tooling failures from product failures when
  evidence supports that distinction;
- do not claim semantic or product success solely from structural validation
  when repository doctrine distinguishes them.

Keep these claims separate. Do not collapse them into one PASS:

- implementation completion: the scoped change exists and its focused
  checks passed;
- original reproduction: the reported failure no longer occurs in its
  original scenario;
- related variations: additional scenarios exercising the same capability
  demonstrate improvement;
- independent generalization: previously unseen or genuinely held-out
  scenarios demonstrate improvement;
- regression: established behavior outside the change still holds, at the
  scope actually run;
- gameplay benchmark: the designated communication benchmark was run;
- remaining limitations: what is still unproven or uncertain.

Report a claim only when the task made it. A missing benchmark or
generalization run is a stated limitation when the report would otherwise
imply that result. It is not a required checkbox on a small repair.

A repair may be accepted within its limited scope without demonstrating
related variations and independent generalization. A repair that resolves
only its original reproduction is a reproduced repair. That result alone
is not a generalized solution and is not a claim of broad conversational
improvement.

A claim of broad conversational improvement must identify which of those
evidence levels supports it. Related variations authored alongside the
implementation are not independent held-out evidence.

Unrelated established behavior is regression, and it uses the lanes
already defined for the work. A systemic engine claim remains governed by
`docs/product_realization_validation.md`, including its
scenario-independent fixture gate.

Passing implementation tests is not improved gameplay. Routine repairs do
not require a live-provider evaluation. Protected replay, the playability
evaluator, and semantic calibration keep their existing authorities and
do not become a gameplay benchmark by being green.

## Failure Investigation

A significant failure is classified before a substantial repair is
described as complete. The classification is a provisional investigative
judgment, not a permanent label. Use one primary class when the evidence
supports one:

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

The category may change when further investigation reveals an earlier or
more fundamental cause. Select the primary class the current evidence
supports. Do not assign multiple labels in order to hedge, and revise
the class when the evidence changes.

These classes guide the repair. An implementation defect is fixed in the
owning code. A contract defect is decided as a contract change before
product behavior is changed to satisfy it. An architectural defect is
escalated under Minimal Change rather than patched with another local
path. A semantic defect needs player-facing evidence. An evaluation
defect is fixed in the instrument or the claim, not by changing the
product to satisfy a bad instrument. Unresolved stays unresolved.

This vocabulary is for development decisions. It does not change replay
failure classification. Do not add these classes to the replay taxonomy,
and do not rename replay categories to match them. Development class
`semantic` is not replay category `semantic_mutation`. Development class
`evaluation` is not replay category `evaluator`.

For a substantial failure, name the earliest demonstrable incorrect
decision and repair that cause when it is established. Do not spend the
repair on a downstream symptom while that earlier cause is already
shown. Stop at the earliest decision the evidence already demonstrates.

A trivial or isolated defect does not require that investigation, a
failure essay, or multiple labels. A normal defect note is enough.

## Task Proportion

Match the procedure to the task. Do not put a benchmark run or a live
provider call on routine work.

A small, isolated repair uses focused checks around the owner. It does
not require a failure essay, a related-variation suite, a full suite, a
provider call, or a gameplay benchmark. Use a lightweight handoff or an
ordinary completion note, as the review-handoff standard already allows.

A moderate functional change uses focused checks and the relevant
regression slice. It may be accepted within that scope when the original
reproduction is resolved, even if related variations and independent
generalization were not run. If the report claims improvement beyond
that reproduction, name the evidence level that supports the claim.
Related variations written with the implementation are not independent
held-out evidence. State the limitation when a claimed level was not
run. A claim of a general owner still meets
`docs/product_realization_validation.md`. A full suite or a provider
call is required only when the change touches a boundary those lanes
actually protect. Generate the standard review handoff when that
standard says a full handoff is required.

A major architectural change includes the Minimal Change justification
when it adds a subsystem, fallback, or decision authority. It includes
architectural review when the existing trigger is met. It reports what
was consolidated or replaced. A gameplay benchmark is still not
automatic. Run it when the change is intended to move player-AI-DM
communication, or when a benchmark checkpoint is otherwise due.

Communication-related development does not continue indefinitely without
reconsidering a benchmark checkpoint. The cadence is not a fixed block
count and not a per-block provider call. It is stated in
`docs/validation_evidence_standard.md`.

A benchmark or evaluation-only pass does not change production behavior
in order to improve a score. Instrument results and product claims stay
separate. Provider calls and benchmark execution belong to this class
and to declared checkpoints.

## Canonical Session Handoff

`docs/NEXT_SESSION.md` is the canonical low-context session handoff for Ashen
Thrones.

Any development, investigation, calibration, policy, architecture, governance,
or Product Realization work package that materially changes project state MUST
update `docs/NEXT_SESSION.md` before completion. This applies regardless of
which agent performed the work.

The handoff is an orientation and continuity document. It must remain concise.
Detailed evidence stays in its authoritative report, source document, or
artifact. The handoff should point to those authorities.

`NEXT_SESSION.md` must not become a second architecture document, a duplicate
campaign report, a comprehensive backlog, or a substitute for detailed
evidence.

Where applicable, the handoff must identify:

- Project
- Current era
- Current objective
- Last completed cycle or material work package
- Established facts the next agent may rely upon
- Decisions made
- Decisions still pending
- Current known defects or blockers
- Authoritative documents for the current state
- Current validation baseline
- Deliberately deferred work
- Decisions, architecture, policy, or validation doctrine that must not be
  reopened without new evidence
- Recommended next action
- Recommended next cycle identifier or title when known
- Minimum files and artifacts the next agent should inspect
- Relevant Git or worktree caveats
- Last-updated date and originating cycle or work package

Sections that genuinely do not apply may be omitted or may state that none
exist.

## Session Exit

Before declaring material work complete, the acting agent MUST:

- perform validation appropriate to the task;
- inspect the resulting repository state and diff as appropriate;
- distinguish new changes from relevant pre-existing worktree state;
- update `docs/NEXT_SESSION.md`;
- identify unresolved blockers and deferred findings;
- provide enough provenance for the next agent to find the detailed evidence.

Updating the handoff is part of completion, not optional documentation cleanup.

Generated-file placement is part of session exit. Before finishing material
work, inspect newly created files and place them under the correct owner. Do
not leave miscellaneous reports, scratch files, or test output in repository
root.

Future campaign or investigation blocks do not need to recopy this
specification. A completion condition such as:

```text
Update docs/NEXT_SESSION.md in accordance with docs/DEVELOPMENT_CONSTITUTION.md.
```

is sufficient.

Validation follows Task Proportion. A small repair does not grow into a
benchmark run or a full-suite claim.

When the review-handoff standard requires a full handoff, generate
`handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`. That bundle
is the review surface. For applicable changes it distinguishes
implementation outcome, original reproduction, related generalization,
independent generalization when evaluated, regression results, Ashen
Thrones Gameplay Benchmark results when available, known limitations,
remaining uncertainty, and the failure class when Failure Investigation
applies. Do not create a second bundle for the same facts.
`docs/NEXT_SESSION.md` points to that review and stays an orientation
document.

## Handoff and Authority Conflicts

`NEXT_SESSION.md` is authoritative for current orientation and pointers. It
does not replace the detailed authority of the reports, documents, or artifacts
it references.

If `NEXT_SESSION.md`, a detailed authoritative report, and current repository
evidence appear inconsistent, investigate the discrepancy. Do not silently
choose one.

If the handoff is merely stale, update it from the authoritative evidence. If
the underlying authorities genuinely conflict, report or escalate the conflict
rather than inventing a resolution.

## Amending This Constitution

Amend this document only when development experience reveals another genuinely
repository-wide invariant or process requirement.

Do not amend it for campaign-specific behavior, one-off implementation details,
temporary defects, individual feature rules, information that belongs in
`docs/NEXT_SESSION.md`, or information already governed adequately by a
specialized authority.

The Constitution must remain small and durable.

## Repository File Placement and Generated Artifacts

Repository root is not a default output directory. Agents must not place
reports, scratch files, test output, replay output, temporary directories,
exports, or generated evidence in repository root merely because root is the
current working directory.

1. Runtime files stay with their existing owners: `game/`, `data/` (canonical
   and playthrough state), `static/`, `run.py`, and runtime configuration.
2. Active governance belongs in `docs/`. Standing architecture, validation,
   and process documents, plus `docs/NEXT_SESSION.md`, remain there.
3. Campaign reports belong under `development/campaigns/`:
   - Architecture Reconciliation: `development/campaigns/reconciliation/`
   - Product Realization: `development/campaigns/product_realization/`
   - Earlier foundation campaigns: `development/campaigns/foundation/`
   Create AR/PR reports directly in those directories. Do not write them at
   root and move them later.
4. Housekeeping or organization reports belong under `development/reports/`.
5. Generated evidence belongs under `artifacts/<topic>/`. Replay artifacts,
   audit output, campaign-specific generated validation evidence, and similar
   records use that established sink.
6. Temporary Cursor, Codex, and pytest output belongs under
   `development/tmp/`. Disposable scratch must not accumulate in root and is
   Git-ignored.
7. Tests remain under `tests/`. Reusable tools remain under `tools/` or
   `scripts/`. Do not archive active engineering infrastructure merely because
   it is not runtime code.
8. Canonical validation inputs remain under `data/validation/` while tests or
   tools depend on that path.
9. Do not invent new top-level directories casually. If an existing owner
   fits, use it. A new top-level organizational category requires an explicit
   architectural reason.
10. Historical evidence remains retrievable. Archiving means organizational
    separation, not deletion.
11. References must move with files. When a tracked file is relocated, update
    repository references, scripts, tests, documentation, handoffs, and
    tooling that depend on its path. Distinguish historical prose mentions
    from live operational paths.
12. `docs/NEXT_SESSION.md` must use current paths and must not perpetuate
    obsolete root locations.
