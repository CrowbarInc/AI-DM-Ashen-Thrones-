# 18 — Changed-File Inventory

The worktree at `d31beb7` was already dirty. This list is the dialogue-quality work. It is not `git status`.

## Production

- `game/dialogue_authority.py` — new. Request classification, posture, determined line, plan reconciliation, prompt-safe codes, rejection reasons, non-canonical commitments.
- `game/social.py` — sufficiency and both authored-knowledge matchers require the topic to support the requested information. Personal and opinion questions may use the harmless-subjective plan. Both social result paths call `attach_dialogue_authority`. The missing-topic plan is built with `topic_revealed` false.
- `game/ordinary_semantic_ownership.py` — `social_narration_unnecessary` is also true when the authority record says narration is determined, speech authority is none, and incidental speech is off.
- `game/immutable_valid_response.py` — safe fallback uses the determined line instead of “settled here” when an authority record exists. Dialogue rejection reasons are applied. A named incidental reaction need not be a quotation. Quote recovery seals one harmless remark and skips the retry.
- `game/noncombat_resolution.py` — copies `authority_codes` onto narration constraints.
- `game/dialogue_social_plan.py` — copies that record onto the plan sent toward the provider, omitting it when absent so older plan equality still holds.
- `game/prompt_context.py` — four dialogue-authority instructions after the existing invention limit.
- `game/api.py` — `remember_dialogue_commitment` at the opening-turn persistence point, using `player_text_for_eval`.

## Tests

- `tests/fixtures/pr_eg_dialogue_holdouts.json` — frozen behavioral cases.
- `tests/test_pr_eg_dialogue_quality.py` — per-dimension scores, sufficiency, plan reconciliation, commitment save/load, narration skip on the watched-road chat, quote recovery without a retry.

## Tooling

- `tools/validate_pr_eg.py` — twelve-turn fresh `/api/chat` qualification. Writes `artifacts/pr_eg/live_qualification.json` and `live.usage.jsonl`.
- `artifacts/pr_eg/package_review.py` — handoff packaging.

## Evidence

- `artifacts/pr_eg/baseline_junit.xml`, `baseline_output.txt`
- `artifacts/pr_eg/regression_junit.xml`, `regression_output.txt`
- `artifacts/pr_eg/live_qualification.json`, `live.usage.jsonl`
- `artifacts/pr_eg/live_qualification_before_quote_recovery.json`, `live_before_quote_recovery.usage.jsonl`
- Reports 01–18
