# 01 — Baseline and Historical Evidence

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

Baseline HEAD: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`. The entry tree already contained extensive modified and
untracked work; `entry_status.txt` records it. This pass changes only the current
opening ceiling/status boundary, targeted tests, offline evidence tools and handoff.
Task-relative diff compares the saved entry files, rather than claiming the full
dirty-tree Git diff as this pass. No commit/push.

Read the Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
Product Realization validation, review-handoff standard and PR-PLAY-02–05 reports,
source owners and controls. Requested support/docs/NEXT_SESSION.md is absent; used
the canonical docs/NEXT_SESSION.md named by the Constitution. No authority change.

The historical directory `artifacts/pr_play_05/manual-20261028-214900/` is present.
Its durable ledger confirms one admission/dispatch, SDK retries 0, host retries
disabled; model gpt-4.1-mini-2025-04-14, 26,593 input, 600 output, ceiling 600,
provider_status incomplete, finish max_output_tokens, extracted length 2,275,
JSON false, envelope false, opening accepted false, gameplay committed false.
Host accounting completion_status=completed is distinct from provider completion.
`historical_evidence.json` preserves ledger rows, SHA-256 and original public
snapshots. Historical PowerShell state encoding requires cp1252 fallback.
Before and after public snapshots both show turn 0, campaign_started false and
time_pressure 0; world (including factions), scene and character compare equal.
No original raw response is available; no reconstruction of its contents is claimed.

Primary failure class: implementation/configuration. The earliest demonstrated
constraint is a shared controlled narration ceiling exhausted by the structured
opening. Offline evidence separately demonstrates complete JSON marked incomplete
could previously be committed; this pass closes that status-admission hole.
Baseline tests show both incomplete positive fragments accepted before the change.
The baseline aggregate-output case admitted under 600 and is correctly refused
after reserving 3000. Its initial expected HTTP assertion was corrected to the
existing 409 budget-refusal contract. The historical rich fixture remains rejected;
that baseline failure was retained as an explicit negative control.

Authority: limited implementation, no live/provider-connectivity authority. Existing
opening completion, validation, rollback, repetition/concurrency controls, admission,
retry suppression, diagnostics, hidden-information and deterministic state owners
are preserved. 257 protected data/experiment files and inventory remain unchanged.
