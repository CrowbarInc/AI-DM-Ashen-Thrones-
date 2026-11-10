# PR-PLAY-24 evidence index

Read FINAL_VERDICT, KNOWLEDGE_DIAGNOSTICS and NPC_PIPELINE first. All nine requested reports are present. The exact transcript is in TRANSCRIPT.

Live and offline directories preserve configuration, readiness, provider ledger, sanitized requests/responses, native diagnostics and function traces, public/authoritative snapshots, state diffs, HTTP responses and stop reason. Internal evidence contains hidden game data for review; it was not served through privileged HTTP.

Repository status captures pre-existing work. Test-only execute_validation.py and worker_capture.py are the only execution additions; build_review.py is post-run analysis. No production changes. Source hashes and snapshots preserve the observed implementation. No broad test runs or provider judge calls.

Legacy counters have structural semantics: meaningful_gameplay_turns_completed=1 does not mean the NPC answer was useful. stop_and_quality_analysis.json supplies the explicit quality assessment and conversational stop.
