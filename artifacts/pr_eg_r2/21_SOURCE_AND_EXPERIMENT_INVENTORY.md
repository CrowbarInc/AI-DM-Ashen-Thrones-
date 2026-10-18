# 21 — Source and Experiment Inventory


`artifact_inventory.json` lists retained artifacts and SHA-256 hashes at report generation; `source_integrity.json` lists before/after hashes of 316 protected game/source and active data files, with zero changes. Review packaging additionally creates its own manifest. This report and the inventory itself are not recursively self-hashed; the handoff manifest covers the packaged versions.

Source snapshots under `sources/game/` preserve 29 relevant production files with the exact reviewed line references. They include routing/authorization, resolver/knowledge, authority, continuity, prompt builder, provider/retry, hard validation/preseal, final emission, world updates and storage. They are copies, not modified production modules. Selected history under `predecessors/` contains 19 reports/transcripts/usage/junit files.

Experimental runners: investigate.py (baseline/capture and provider matrix), live_single.py (single synthetic access proof), analyze.py (local tokenizer/validator/persistence), trace_preference.py (exact seeded production trace), build_reports.py (retrospective review), package_review.py (established workflow). measure.py is an unexecuted optional full-prompt egress measurement script blocked by automatic review; it must not be mistaken for collected evidence.

Prompts: system_prompt.txt, frozen_cases.json, prompts/*.json. Every experiment row contains exact context, requested/returned model, configuration, raw output, parsed narration, measured input/output tokens, latency, validation and SHA-256 of serialized messages. The initial failed connection is a retained row. The separate access probe is single_provider_access.json. No unfavorable generation was removed.

Measurements: local_prompt_attribution.json; summary_measurements.json; provider_validator_results.json (all 130, direct with decision plus preseal); validator_control_matrix.json (18 labeled controls); persistence_probe.json; investigator_review.json and failure_inventory.json (post-hoc ratings/causes); exact_preference_trace.json; production_captures_offline.json and production_baseline_offline.json (scripted local capture, not fresh provider); focused_local_junit.xml (71 passing); focused_junit.xml (initial sandbox failures).

Reproducibility: use the repository Python environment plus tiktoken 0.14.0 for offline measurements. The tokenizer and public vocabulary cache were installed only under the experiment directory; neither dependencies nor caches are packaged as project requirements. Provider phases require explicit network permission and the local configured credential. Never package .env. Raw disposable storage/test temp trees and unrelated active saves are excluded. All source hashes and model configuration remain in the bundle.

Measurement status: fresh A–G matrix complete; full-prompt fresh baseline not run; full regression not rerun; complete production compact-generation qualification not performed. Run commands and definitions are retained in the scripts. External review is the next step.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
