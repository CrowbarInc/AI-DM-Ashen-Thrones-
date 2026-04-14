# Architecture Audit Readme

This audit is a static, inspectable architecture check for the repo's deterministic integrity stack. It reads source, tests, docs, and audit tooling, then emits:

- `artifacts/architecture_audit/architecture_audit.json`
- `artifacts/architecture_audit/architecture_audit.md`

It does not import runtime modules from `game/`, does not make gameplay changes, and does not call an LLM.

## What The Audit Does

- Infers likely runtime owners for seeded subsystems from docstrings, ownership language, role signals, overlap heuristics, coupling indicators, and archaeology markers.
- Reconciles runtime owners against practical test homes and documentation claims.
- Produces subsystem verdicts and a repo-level verdict.
- Surfaces inspectable evidence for overlap, residue, coupling, test spread, transcript-lock seams, and inventory-doc drift.

## What It Cannot Prove

- It cannot prove semantic correctness.
- It cannot prove gameplay quality.
- It cannot prove that a heuristic overlap is a real duplicate invariant.
- It cannot prove that a documented owner is actually obeyed at runtime.

Treat it as a deterministic triage layer, not as a formal proof system.

## How To Run It

Use the normal repo command:

```shell
py -3 tools/architecture_audit.py
```

Useful CLI options:

```shell
py -3 tools/architecture_audit.py --print-summary
py -3 tools/architecture_audit.py --focus-subsystem "prompt contracts"
py -3 tools/architecture_audit.py --strict-doc-check
py -3 tools/architecture_audit.py --strict-test-check
```

`--print-summary` prints the repo-level verdict, scorecard, and top hotspots after writing artifacts.

`--focus-subsystem <name>` prints:

- declared owner
- inferred owner
- overlap counts
- coupling summary
- archaeology summary
- test ownership alignment
- key evidence lines

## How To Interpret Subsystem Verdicts

Each seeded subsystem has:

- `declared_owner`
- `inferred_owner`
- `ownership_confidence`
- `role_labels`
- `overlap_findings`
- `coupling_indicators`
- `archaeology_markers`
- `test_ownership_alignment`
- `audit_scores`
- `verdict`

Interpretation:

- `green`: the subsystem looks bounded enough that the owner is visible and adjacent overlap is limited.
- `yellow`: the subsystem still looks real, but change safety depends on cleanup, residue trimming, or tighter test/doc convergence.
- `red`: ownership, overlap, or alignment evidence is weak enough that the subsystem should not be treated as cleanly consolidated.

## How To Interpret Repo-Level Verdicts

The repo-level rubric uses existing audit fields only. It scores six dimensions:

- ownership clarity
- overlap severity
- archaeology burden
- coupling centrality
- test alignment
- documentation coherence

Possible repo verdicts:

- `structurally real, under-consolidated`: ownership is mostly real and hotspots are localized cleanup work.
- `transitional but coherent`: the architecture still looks intentional, but extraction residue and drift are still active.
- `mixed / caution`: some seams look real, but important areas drift enough that new features should wait for targeted ownership cleanup.
- `high ambiguity / architecture risk`: ownership smear, unclear docs/tests, or broad drift are strong enough that growth should pause.

The repo-level scorecard is the first place to look when you want to know whether problems are local or systemic.

## How To Interpret Runtime/Test/Doc Mismatches

AR3 reconciliation appears in:

- `subsystem_reports[*].test_ownership_alignment`
- `summary.test_alignment_overview`
- `summary.top_test_runtime_doc_mismatches`
- `summary.concerns_with_widest_test_ownership_spread`
- `summary.inventory_docs_authority_status`
- `summary.manual_review_shortlist`

Alignment states mean:

- `aligned`: runtime owner, docs, and practical tests converge.
- `partial`: one layer still drifts, but the concern is still partially anchored.
- `conflict`: practical protection is centered somewhere meaningfully different from the runtime-looking owner.
- `unclear`: the audit cannot yet identify a stable owner/test/doc triangle.

Important: `unclear` lowers confidence, but does not automatically force the harshest repo verdict. The repo verdict also distinguishes localized hotspots from system-wide smear.

## Transcript-Lock Vs Contract-Lock Risk

Use:

- `summary.likely_transcript_lock_seams`
- `summary.likely_contract_owned_seams_with_weak_direct_tests`
- `summary.transcript_contract_lock_risk_summary`

Interpretation:

- Transcript-lock risk means a seam is being preserved mainly through scenario or transcript-style protection.
- Contract-lock risk means a seam looks runtime contract-owned, but weak direct tests leave that contract under-protected.

If transcript-style suites dominate a concern that looks contract-owned at runtime, treat that as a warning that behavior may be preserved through broad regression locks instead of clean ownership.

## Module With A Contract Vs Sediment Layer

In repo terms:

- A module with a contract is a file that the audit can treat as a stable owner or direct boundary for a concern. It tends to have clearer role labels, better owner evidence, and more direct test alignment.
- A sediment layer is a file that still carries historical, compatibility, extracted-from, or overlap residue after ownership moved elsewhere. These often show up in archaeology markers, compatibility overlap findings, or partial/conflict reconciliation.

The audit's hotspot classification names this difference directly:

- `localized under-consolidation`
- `transitional residue`
- `possible ownership smear`
- `unclear / needs human review`

## Output Sections

The Markdown report now includes:

- Executive verdict
- Repo-level scorecard
- Subsystem verdicts
- Strongest evidence that the architecture is real
- Strongest evidence that the architecture may be patch-accumulating
- Known ambiguity hotspots
- Runtime/test/doc mismatch review
- Transcript-lock vs contract-lock risk summary
- Manual spot-check list
- Cleanup-only opportunities
- Stop-before-feature warnings

Read the Markdown first for operator guidance, then drop into the JSON when you need the exact evidence payloads.
