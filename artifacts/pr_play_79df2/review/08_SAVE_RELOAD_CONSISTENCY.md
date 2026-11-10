# Save and reload

Final-source snapshot: `artifacts/pr_play_79df2/browser_data/snapshots/2026-11-08T16-20-50_7bf157dc.json`, label `79DF2 final source`.

Page reload of `http://127.0.0.1:8112/` restored the isolated campaign: scene `frontier_gate`, 2 clues, 23 log entries, and the accepted Gate Guard sentence. No new campaign opening. No cross-campaign snapshot was loaded.

Development tests cover save/reload of a fallback pointer and a second session that keeps its own sentence and `campaign_run_id`.
