PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 01 — Baseline and Failure Reproduction

HEAD remains `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`, branch feature/product-realization. The tree was extensively dirty on entry. `artifacts/pr_play_05/status_before.txt`, `head.txt`, `entry_hashes.json` and `entry/` retain the exact baseline. Git HEAD alone does not represent the tested source. No reset, discard, commit or push occurred.

PR-PLAY-04 changes were uncommitted: opening rejection before persistence, preventing generic answer adoption for rejected openings, `_OpeningScope` rollback/serialization, and opening tests. Its recorded `artifacts/pr_play_04/source.diff`, eight reports and original HTTP output were inspected. Preexisting unrelated edits include other provider/interpretation owners, runtime saves, audit artifacts and documentation. They were preserved. The pass-specific diff is against entry snapshots, not cumulative Git HEAD.

Read the Constitution, canonical NEXT_SESSION, validation evidence standard, Product Realization validation, review standard, PR-PLAY-01 findings, PR-PLAY-02 controls/manual, PR-PLAY-03 causal evidence and PR-PLAY-04 implementation/regression reports. `support/docs/NEXT_SESSION.md` is absent in the workspace; support/ is the review ZIP prefix. Used canonical `docs/NEXT_SESSION.md`. No applicable AGENTS.md was found.

Original manual ZIP was opened directly: one admitted request, 26,593 input / 600 output / 27,193 total tokens; original log contains missing_structured_envelope. Neither raw provider output nor authoritative finish metadata survives. `historical_facts.json` preserves this limited finding. Usage at a 600-token limit is possible-truncation evidence only.

## Five original tests, run individually

All use disposable `_seed_campaign_start_storage`, TestClient, New Campaign, then Start; call_gpt is replaced with a fixture. No SDK dispatch occurs in these five tests. Tests 1–3 use legacy rich response dictionaries; tests 4–5 use `[Narration]`.

| Test in tests/test_start_campaign_api.py | Expected / original actual | Final classification |
|---|---|---|
| test_start_campaign_emits_opening_and_sets_started | 200 and rich text/persistence; actual 200, substring assertion fails | Confirmed preexisting defect; excluded |
| test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text | forced reconciliation cannot shorten accepted text; actual 200, debug 781 > 800 fails | Confirmed preexisting defect; excluded |
| test_start_campaign_promotes_valid_upstream_prepared_scene_opening | prepared rich candidate replaces short text; actual 200, short text persists | Confirmed preexisting defect; excluded |
| test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent | 200 with selected journal facts; actual 422 scene_opening_not_scene_establishing | Resolved obsolete fixture |
| test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts | 200 and journal basis; actual 422 same placeholder reason | Resolved obsolete fixture |

The historical output's first/third failures are substring assertions, not length assertions. `entry_1..5.txt/json` reproduce all five on preserved PR-PLAY-05 entry source; `fixed_1..5` contain final individual runs. `http/entry_*/` and `http/fixed_*/` retain relevant response bodies, emitted text and application metadata. Reproduction is consistent across the historical report, entry runs and current rich cases. Group A now passes individually.

Each run is capped at 55 seconds. Initial setup lacked the pytest temp parent; corrected without product changes. Sandboxed TestClient executions then timed out; those subprocesses were killed by subprocess timeout. Outside-sandbox, guarded offline HTTP runs completed in seconds. Their provider guard remained active. `baseline_*` and `repeat_*` preserve environment failures rather than hiding them.

## Isolated comparison

`prepare_comparison.py` copied source/tests/static/data/docs to ignored development/tmp/pr_play_05/pre04, reconstructed API from PR-PLAY-02 saved source plus its recorded delta, and verified the exact SHA-256 against PR-PLAY-03's source attestation. Other production owners match entry. No active source was overwritten. `comparison_provenance.json` records the matching pre-PR-PLAY-04 API hash. All five ran individually there (`pre04_1..5`): 1–3 fail identically; 4 passes; 5 already fails its journal-text assertion. After pre04 boundary capture, the isolated API was replaced by the saved PR-PLAY-05 entry API for entry baseline tests. This is a source-overlay comparison, not a claim that Git HEAD represents pre04.
