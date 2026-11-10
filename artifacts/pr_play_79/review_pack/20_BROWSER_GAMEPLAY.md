# 20 — Browser gameplay

Host: `artifacts/pr_play_79/browser_host.py` at `http://127.0.0.1:8094/`. Provider calls disabled. `call_gpt` stubbed with the existing rich opening. This is not live narration.

Both campaigns were typed into `#chatInput` and sent with the Send button. No suggested-action button was clicked. Combat controls were not used.

**Campaign A.** New Campaign, Start Campaign, then the six authored lines. The log shows the notice clue, arrival at Old Milestone, the print clue, the report commitment, return to the gate, and the watch receiving the report. Snapshot label `authored` was created and loaded. The log then said "Snapshot restored." A follow-up recalled the report. Screenshot: `review_pack/machine/browser_campaign_a.png`.

**Campaign B.** New campaign and start, then follow, wait, marker, the mixed look-and-ask, "Before I report, I want to keep looking," and the memory question. The header after resume is Old Milestone. The mixed reply includes the observation and "that conversation was not started." "Before I report" says no survey or report was chosen. Snapshot `initiative` was created and loaded. The following "I look around" stayed at Old Milestone. Screenshot: `review_pack/machine/browser_campaign_b.png`. Save status on that screen: active scene `old_milestone`, 2 clues.

Browser-visible per-turn latency was not instrumented. Each send returned inside the page poll (under 8 seconds) and the resulting text is in the log.

The Load control for Campaign A was not painted until the save-slot list was filled from `/api/state` and the details element was opened. The click then used the page's existing load listener. The snapshot itself was created by the Create Snapshot button.
