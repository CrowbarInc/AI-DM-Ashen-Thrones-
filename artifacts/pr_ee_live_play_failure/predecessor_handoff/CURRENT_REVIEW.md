# CURRENT REVIEW - PR-ED

PR-ED

MODE:
IMPLEMENTATION - PROVIDER EFFICIENCY AND RESPONSIVENESS

LIVE PROVIDER CALLS:
Bounded. Clean samples, same courtyard and `gpt-4.1-mini`, before and after edits: one ordinary move and one NPC dialogue initiation. An earlier 10-turn live run used a 600-token output cap and is not the comparison baseline.

PRODUCTION CODE CHANGES:
Yes

Primary changes:
- A completed scene transition emits the existing arrival sentence and does not call the narration provider.
- A local observation the engine already overwrites does not call the narration provider.
- An unsent narration retry, or a retry whose text is identical to the previous attempt, stops without another provider call and without resolving the action again.
- Duplicate turn-packet policy is omitted when it matches the root policy.
- Narration and interpretation use a 45-second provider timeout.
- Turn traces record call count, token counts, latency, and retry metadata. Prompts and credentials are not stored.

Key source references:
- `game/api.py` narration skip, retry stop, and performance record.
- `game/gm.py` timeout, duplicate-policy omission, and provider-call stamp.
- `tests/test_pr_ed_provider_efficiency.py`
- `tools/measure_pr_ed_turn_profile.py`

Validation:
- Preimplementation regression: 249 passed, 30 failed, 20.09s.
- Final comparison suite: 256 passed, 30 failed, 20.87s. The seven new passes are the PR-ED tests. The 30 failures are the inherited set.
- One intermediate scene-transition assertion failed because narration was skipped. The test now requires the destination scene and the arrival sentence. It passed in the final suite.
- One save/load WinError 5 failed in an intermediate suite, passed in isolation, and passed in the final suite.
- Live movement: 16646 ms and 2 discarded provider calls became 101 ms and 0 calls. The player sentence is unchanged. The scene still changes.
- Live dialogue: 3111 ms, 23469 input tokens, one call became 2777 ms, 23035 input tokens, one call. The player sentence is unchanged. The 334 ms difference is one sample.

Decision:
B - PR-ED ACCEPTED WITH LIMITATIONS

Why:
The measured player wait on a completed move was the provider, and that call was discarded. Removing it keeps the resolver's arrival sentence and cuts that turn from about 17 seconds to about a tenth of a second. Dialogue is still about 3 seconds and about 23 thousand input tokens. Eight of the ten representative turns were not remeasured live. Inherited social and exploration failures remain.

Review package:
- Primary report: `artifacts/pr_ed_provider_efficiency/REVIEW.md`
- Baseline: `PR-ED_preimplementation_baseline.md`
- Manifest: `handoff/REVIEW_MANIFEST.json`
- Zip: `handoff/CURRENT_REVIEW.zip`

Stop here. Do not begin another cycle until this review is accepted.
