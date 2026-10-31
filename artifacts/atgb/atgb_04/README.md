# Independent human review — ATGB-04

Start with `review.html` in a browser (offline). Read the instructions and each
conversation in order; all 37 baseline exchanges are included verbatim. Its blank
fields export `human_judgments.json`. Save that export before closing; this form
does not automatically save. Import an earlier export to continue. An optional
plain-text form is in `blank_scoring_forms.md`; transfer it into a copy of
`blank_judgments.json` for reporting. Keep each reviewer's file separate and retain
disagreements; do not average reviewers or silently adjudicate them.

Authority: ATGB-02 / ATGB-01 / atgb-rubric-01 / ATGB-02-s07-held-out.
Approved definitions and behavioral criteria are reproduced, not amended.
Interpretation, response adequacy, and authority each use pass/fail/uncertain;
unchecked means the dimension was not judged. `not_evaluated` explicitly records
that no supported judgment was made. Blank means still pending. Neither is pass.
These are review statuses, not new gameplay scoring categories.

Failure severity uses only minor, major, critical. Leave it blank when no defect
is assigned; blank is not a finding of no defect. Minor: usable reply with stiff
or repetitive wording. Major: communicative job missed, wrong addressee, lost
referent, evasive restatement or needless clarification; response fails. Critical:
consequential invented/hidden fact or unauthorized state; authority fails.
Explain failures, uncertainty, skipped criteria, and any setup dependence in the
reviewer explanation. An explanation is requested for each entered judgment.

Clarification: none (no question needed), necessary_pass (one focused question
for a real ambiguity), unnecessary_fail (already specific enough), or
missing_when_needed_fail (needed but guessed/evaded/refused without asking).
Continuity: not_applicable, preserved, or lost. S02.4, S03.4, S05.2, S08.4 and
S10.2 require context older than the last sentence. All earlier exchanges in the
same trial are linked in the index and shown immediately above each later turn.

Response and authority both passing define acceptability under the approved
rubric; interpretation remains separate. Major/critical defects cannot be
acceptable. No universal score is calculated. Conversation observations cover
repetition, phrasing, clarification, pacing, sustained initiative and mechanical
or validation-like dialogue without a new numerical category.

S07/S09 require special review: authored facts in state were not delivered as an
opening before turn 1. Browser/journal delivery is unverified. Do not presume
player knowledge or score missing setup as conversational failure. Explain which
criteria remain supported by explicit lines and actual preceding replies; use
uncertain/not_evaluated for unsupported judgments. Preserve independently
evaluable interpretation, text, clarification, continuity and state evidence.
See `scenario_qualifications.md` for turn-specific review questions.

Technical capture is not human scoring. Individual replies may be host-owned
despite live-enabled execution. State snapshots show scene, clue IDs, flag names,
interlocutor and transcript count; they are bounded projections, not proof that
all hidden values were unchanged. Raw results and final state are available in
the ZIP for deeper inspection. Raw harness diagnostic zeros are not human
findings. Do not use the old worksheet placeholders as judgments.

Original S04 trial 1 is a separate two-turn historical observation, excluded
from all 37-turn reporting. It is retained in `historical_S04_trial_1.md` and
its original evidence files. Do not splice it into trial 2.

Reporting (Python standard library only, no provider or gameplay imports):

`python support/tools/atgb/report_human_review.py --index support/artifacts/atgb/atgb_04/review_index.json --judgments human_judgments.json --output report.json`

Run that command from the extracted ZIP root. In the repository, omit `support/`.
Rates use pass/(pass+fail) separately per dimension, capability and partition;
raw numerators, denominators, pending/uncertain/not-evaluated/unchecked counts
remain alongside them. Continuity loss uses lost/(preserved+lost), with
not_applicable separate. Clarification counts retain all four approved tags.
Partial judgments produce explicitly partial reports. Critical and major
exchanges appear before aggregate data. With no human judgments, rates are null.
Review metadata is human-entered attribution, not authentication of identity.

One environment, single selected trial per scenario, uncontrolled sampling,
API-only delivery, differing original/continuation accounting, and previously
exposed held-out material limit claims. No independent unseen generalization,
gameplay improvement, browser validation or completed performance baseline is
established by this preparation. Stop and await independent human evaluation.
