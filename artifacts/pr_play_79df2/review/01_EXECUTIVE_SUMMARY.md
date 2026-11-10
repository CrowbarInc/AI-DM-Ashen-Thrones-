# PR-PLAY-79D-F2 executive summary

Verdict: **B / PARTIAL**. The NPC publication-state defect from PR-PLAY-79D-F is repaired. PR-PLAY-79 is not closed.

`session.last_publication` means the latest completed gameplay sentence. Accepted NPC dialogue keeps the composer record when that record's visible sentence is the sentence just delivered. A grounded fallback replaces a stale pointer and is marked `dialogue_accepted: false`. The campaign stamp uses `campaign_run_id`, the identity key historical comparisons already treat as volatile.

Final-source live check, fingerprint `game/publication_contract.py` `36f8416c168ea456412fd4e2fec8aefc1898f552a223e16f338fb31774ed54ba`:

- Player input: `Hello, Gate Guard.`
- Visible sentence: `Gate Guard says, "Hello again. The notice board has some updates about taxes and curfew, and it also mentions a missing patrol, though I don’t know any more than that."`
- Publication event: `accepted_expression`, owner `integrated_play.commit_integrated`.
- Session pointer visible text, turn 21, and `campaign_run_id` match that sentence.
- Page reload showed 23 log entries, 2 clues, scene `frontier_gate`, and the same sentence.

Development tests: 36 passed. Developer-authored holdout: 28/28. Historical lanes versus PR-PLAY-78A: focused 1,065/20, boundary 101/6, broader 0/9, new identities 0. An earlier revision that stored `campaign_id` produced 17 new identities and is not part of this verdict.

Remaining blocker: a non-mutating interpretation admission refusal still delivers a player-facing sentence and a publication event, while `session.last_publication` stays on the previous gameplay sentence. Two such refusals occurred while bringing the repaired server up. Neither sent a provider request.

Provider totals for sent calls: 4 requests, 1853 input, 205 output, 2058 total, 0 retries, 0 openings. Protected files: 150/150.
