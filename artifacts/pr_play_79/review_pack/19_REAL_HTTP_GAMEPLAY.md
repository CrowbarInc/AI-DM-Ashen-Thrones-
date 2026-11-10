# 19 — Real HTTP gameplay

Harness: `artifacts/pr_play_79/cycle.py` `http()`, TestClient, provider disabled, opening stubbed. Isolation directory: `artifacts/pr_play_79/http_data`. Trace: `http_campaigns.json`.

**Campaign A — authored baseline.** Six chat turns: notice, rumor, milestone, commit the report, return to the gate, give the report. Final text: the watch receives the report and `patrol_guards_warned` is set. `patrol_survey` stays unset. Save, new campaign, load: resume matched scene and flags.

**Campaign B — player initiative.** Eight chat turns through follow, wait, marker, look, and memory. Scene ends at `old_milestone`. `patrol_survey` and `patrol_report` stay unset. Resume matched. The memory line recalls the notice and the prints.

No authored-action button was used. These campaigns are not the live-provider session.
