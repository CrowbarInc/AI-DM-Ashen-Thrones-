# Baseline and scope

Commit: `d40f1ed198236c604085f1c842ead267a8104ce2`. Entry working-tree status is preserved in
artifacts/pr_play_62/baseline.json. There were extensive existing tracked and
untracked changes, including already-dirty protected data/baselines. No AGENTS.md
was found in the workspace; .agents contained no files. Entry source copies and
an entry-to-current implementation.diff distinguish this work from prior edits.

Read: Development Constitution, NEXT_SESSION, Validation Evidence Standard,
Product Realization Validation, Review Handoff Standard, ATGB-05 baseline
preservation, and relevant PR61 evidence/reports. No frozen ATGB corpus edit,
benchmark execution or score claim. Canonical campaign fixtures are not rewritten.

Relevant owners: game/api.py resolution/publication; game/exploration.py outcome
resolution; quarantine and integrated investigation modules context, provider,
validation and fallback; anchored/offline projection modules authority views;
legacy, consequential, persistent and mandatory validators. static/app.js
sendChat posts to /api/chat and reloads state/log. game/storage.py persists.

Changed production files: game/integrated_investigation_narration.py and
game/quarantined_investigation_narration.py. Also added PR62 tests, tooling,
reports/evidence and a NEXT_SESSION entry. game/api.py was already dirty and was
not edited here. No frontend redesign or new gameplay mechanic.

Existing configuration: exact quarantine=1, mode=integrated, live=1, publication=1
with matching campaign_run_id, retries disabled. Existing expression output cap
80 retained. Experiment bound: 8 requests / 15,000 tokens. New repeat-fast-path
flag is process-local and default off. server_config.json records nonsecret flags.
No .env or credential export. Known baseline failures: 3 focused, 9 broader.

Supported categories: discover_clue, investigate, observe, already_searched.
Native inventory-taking remains unsupported. The governed frontier_gate fixture
was copied with private canaries into disposable storage using the PR61 helper.
