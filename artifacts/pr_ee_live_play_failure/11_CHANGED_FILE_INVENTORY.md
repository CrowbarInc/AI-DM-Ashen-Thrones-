# 11 — Changed-File Inventory

PR-EE changed only investigation artifacts under `artifacts/pr_ee_live_play_failure/` and the established handoff files `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip`. `package_inventory.json` lists every package member with byte count and SHA-256 (except the inventory itself, whose hash appears in REVIEW_MANIFEST). `source_hashes.json` fingerprints the copied current sources; source_snapshot contains copies, not production edits.

- Documents: 01–11 reports and combined REVIEW.md.
- Original evidence: original_session_log.json, original_session.json, original_provider_totals.json; original data is read/copied only.
- Diagnostic evidence: recorded_output_http_replay.json, recognized_fresh_start_replay.json, lifecycle_gate_probes.json, semantic_alternatives_static_probes.json, replay_environment.json, replay_preservation_check.json, production_hashes_before.json, final_preservation_check.json, live_probe_access_limit.json, validation_results.json, root_cause_register.json.
- Runners: investigate.py and build_review.py. Temporary instrumentation is process-local wrapping of request_interpretation to inject recorded raw outputs and capture reconstructed requests; no instrumentation edits in production modules. Optional --live mode remains unexecuted and requires explicit approval of payload/destination.
- Context: git_status_at_review.txt, git_revision.txt, prior_cycle_reports/, predecessor_handoff/ (PR-ED's prior CURRENT_REVIEW files preserved), source_snapshot/, source_hashes.json.
- Generated packaging: package_inventory.json; handoff manifest and zip.

Disposable copied state directories named pr_ee_* inside this artifact directory are diagnostic runtime copies, excluded from CURRENT_REVIEW.zip. Failed sandbox attempts also used temporary state; no live campaign was targeted. Runtime copies may be removed after review; reproducibility comes from runner plus current source snapshot and captured before/after records. No sensitive environment file or credentials are copied into the review package.

Before/after SHA-256 checks cover every game Python file, static asset, top-level data JSON/JSONL and scene JSON. The replay check and final check require zero changes in those paths. The repository already had extensive unrelated dirty/untracked work (including game and data changes from earlier cycles). PR-EE neither reverts nor claims those changes. The new CURRENT_REVIEW intentionally supersedes PR-ED's handoff, whose prior files remain archived in predecessor_handoff.
