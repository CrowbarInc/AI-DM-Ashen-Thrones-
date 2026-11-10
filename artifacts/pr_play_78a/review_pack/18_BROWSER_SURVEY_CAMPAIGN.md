# Browser survey campaign

Host: `http://127.0.0.1:8093/` from `artifacts/pr_play_78a/browser_host.py`. Provider calls and expression generation were off. No authored-action button was clicked.

Typed sequence that completed the branch:

- I examine the notice board. -> northwest mud clue.
- I follow the missing patrol rumor. -> arrived at Old Milestone.
- I examine the weathered milestone. -> overlapping prints.
- I'll survey the uncertain trail myself. -> authored survey consequence.
- I write down the limits of the survey. -> authored record consequence.
- What can I do here? -> Old Milestone, no further authored continuation.

An earlier typing pass raced the send button. Two utterances were not delivered. The milestone examine that did land while still at the gate was refused ("Nothing further is established"). The completed sequence above was then typed on the same campaign.

Snapshot `2026-11-08T00-51-20_3b52cf10`. Reload restored Old Milestone, 2 clues. Loading that snapshot and asking again kept Old Milestone and the recorded survey.

Screenshots: `browser_shots/campaign_a_before_reload.png`, `campaign_a_after_resume.png`.

Visible chat latencies from `ASHEN_UI_READY` are listed in the performance report.
