# 18 — State integrity

Authoritative state and the visible transcript were checked separately.

After the final browser load of Campaign A:

- `campaign_run_id` `b71d9ab269b14913826d9790`
- `active_scene_id` `old_milestone`
- `campaign_started` true
- World flags `patrol_survey` and `patrol_survey_recorded` are true
- `patrol_report` and `patrol_guards_warned` are absent from the live world file
- Visible log matches the survey slot, including one survey record and the track continuation

The report snapshot `2026-11-06T04-34-47_853e96fc` still contains campaign `9d6a1a036881996f1883786c`, scene `frontier_gate`, and the report flags. Loading it earlier in the same session restored the warned sentence and hid the survey-recorded sentence.

No tested resume applied the unchosen branch. No tested save reported success when the write had failed. Experimental enrollment stayed on only for the verification hosts that set the flags.

## Protected files

At the start of the cycle, 150 protected `data/` hashes matched the PR-PLAY-71 baseline. An isolated pytest later wrote `data/session.json`, `data/combat.json`, `data/world.json`, and `data/session_log.jsonl` at 11:32:55 PM. Session, combat, and world were restored to the protected bytes. The protected session log was not found in temp directories, editor history, or review archives. The log now holds the committed blob, whose hash is not the protected hash. `artifacts/pr_play_71v/session_log_truncation.json` records that gap. The other 149 protected entries match.
