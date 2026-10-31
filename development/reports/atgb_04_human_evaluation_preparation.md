# ATGB-04 — Independent human evaluation preparation

2026-10-18. Evaluation/reporting only. Prepared; human evaluation pending.

The authoritative review set contains exactly 37 unique turns: original S01–S03,
S04 full trial 2, and S05–S10 trial 1. Original S04 trial 1's two observations remain
separate historical evidence. No trials were merged. No gameplay behavior,
benchmark scenarios, rubric, model configuration or production defaults changed;
no provider requests or gameplay execution occurred.

## Review materials

Start with `artifacts/atgb/atgb_04/README.md`, then `review.html` (offline browser)
or `conversational_review.md`. The HTML shows complete conversations, unchanged
approved expectations, bounded before/after state and blank scoring controls.
It exports/imports a human judgment JSON file. The Markdown document includes
the same conversations and blank fields; `blank_scoring_forms.md` and
`blank_judgments.json` provide standalone forms. Save exported work before closing.

`review_index.json` records scenario, turn, trial, exact player/AI text, full actual
preceding same-trial exchanges, authoritative context, state, partition, setup
limitations, and source pointers. `review_index.md` is the compact navigation index.
S07/S09's six observations are marked for special review. Opening-dependent criteria
cannot assume world facts reached the player; see `scenario_qualifications.md`.
Other independently supported evidence remains reviewable. Missing setup is not
automatically a conversational failure. Actual prior delivery matters in S03,
S05 and S08 as well; the intended script does not replace a failed earlier reply.

## Reporting and independence

`tools/atgb/report_human_review.py` consumes completed or partial human exports.
It reports coverage, separate interpretation/response/authority counts, raw
numerators and denominators, severity, clarification, continuity, capability and
partition breakdowns, qualitative observations and unreviewed/uncertain/skipped
counts. Critical and major exchanges precede aggregate data. Rates are excluded
from overall coverage and retained only within evidence partitions. No universal
gameplay score, automated judgment, LLM judge or inferred human outcome is added.
Blank inputs produce null performance rates. `pending_report.json` demonstrates
that behavior and contains no human findings.

Reviewers work independently in separate files; preserve disagreement. The tool
validates explicit human attribution, allowed labels, exact selected trial IDs,
and approved severity consistency. Attribution is self-attested, not proof of
identity. It does not change a human's labels or decide eligibility. Explanation
fields document uncertainty and partial criterion support. Supplied entries alone
do not automatically authorize a performance or improvement claim.

## Verification and preservation

Focused offline integrity and aggregation checks cover exact 37-turn selection,
verbatim source correspondence, full prior context, six setup flags, blank forms,
null rates without review, denominator handling, severe-exchange retention, and
rejection of invalid or duplicate/wrong-trial judgments. HTML structure and form
JavaScript are checked offline. The browser tool refused local `file:` navigation;
rendered layout is not verified and no workaround was attempted. Markdown remains
an ordinary human-readable review surface. No broad/full-suite or gameplay
regression claim is made. Results: `artifacts/atgb/atgb_04/validation_results.json`.

Protected hashes and ZIP verification distinguish this pass from the extensive
pre-existing dirty/untracked worktree. All selected ATGB-03/03C sources, corpus,
frozen baseline, production sources, canonical campaign data and existing harness
are preserved. ATGB-04 adds two offline preparation/reporting tools and focused
tests; session orientation and generated standard handoff are updated. No commit.
Source/history and accounting boundaries: `evidence_provenance.md`.

## Limitations and next action

Human judgments remain pending. S07/S09 opening delivery, one environment,
single selected trials, uncontrolled sampling, API rather than browser evidence,
bounded state projections and previously exposed held-out content limit claims.
No independent unseen generalization or conversational improvement is established.
The completed capture is not a completed gameplay-performance measurement.

The standard review handoff is `handoff/CURRENT_REVIEW.md` and
`handoff/CURRENT_REVIEW.zip`. Extract the ZIP and open
`support/artifacts/atgb/atgb_04/review.html` or the Markdown review document.
Stop after preparation and await independent human evaluation. No rerun, repair
or Product Realization campaign is initiated.
