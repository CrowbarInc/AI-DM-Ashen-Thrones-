# ATGB-02 — Benchmark infrastructure

Date: 2026-10-18
Status: infrastructure implemented. Live baseline not run.
Identifier: `atgb_02_conversational_benchmark_infrastructure`

## Outcome

The conversational benchmark now has fixtures, an isolated driver, a provider-disabled validation mode, a human worksheet, and a result format. Production gameplay code was not modified. No live provider request was made. This package does not show that player–AI-DM communication improved.

Original reproduction: not applicable. This pass repairs no gameplay failure.
Related generalization: not applicable.
Independent generalization: not evaluated. The held-out partition is stored and labeled previously exposed.
Regression: the playability evaluator, the review-handoff generator, and the validation-evidence packet tests were run and passed. The full suite was not run.
Gameplay benchmark: no performance result. Provider-disabled runs validated the harness only.

## What was added

Fixtures under `data/validation/atgb/` transcribe the ATGB-01 catalog. S07 is held-out. The catalog file itself still lists S07 as development-visible; `corpus.json` records that discrepancy. Counts from the fixtures are 25, 4, and 8.

`tools/atgb/` loads those fixtures, rejects unsafe data directories, builds the existing chat request, and writes a result, a report, and a worksheet. `tools/run_atgb.py` is the command. `provider_disabled_simulated` uses a test double and does not import the game. `provider_disabled_host` posts to `POST /api/chat` in a subprocess whose `ASHEN_DATA_DIR` was set before import. `live_provider` is implemented and refused unless the operator confirms it and sets an explicit call ceiling and time ceiling. No dollar default exists.

The worksheet asks for interpretation, response, and authority separately, plus an unscored conversation note. The report keeps critical failures ahead of any rate and does not emit a universal score.

`docs/validation_evidence_standard.md` now points at this corpus and forbids a performance claim from infrastructure, host-only, or unscored output. `evaluate_playability`, protected replay, and semantic calibration are unchanged.

## Validation

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_atgb_infrastructure.py -q --tb=short
```

Result: 9 passed.

Those tests cover fixture loading, the 25/4/8 counts, exact catalog player lines, behavioral criteria that are not exact-response matches, conversation order, separate stores, rejection of the canonical data directory, unchanged hashes of `session.json`, `session_log.jsonl`, `world.json`, and `combat.json`, simulated labeling, unavailable telemetry, worksheet fields, reproducible infrastructure projections, an elapsed-time stop, refusal of an unconfirmed live run, refusal of a live run that omits a required ceiling, and a cost ceiling without a price. A provider-disabled host run of S06 captured four ordered replies through chat, reset only the isolated store, and kept `gameplay_performance_claim` false.

Adjacent regression:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_playability_eval.py tests\test_review_handoff.py tests\test_validation_evidence_standard.py -q --tb=line
```

Result: 49 passed.

The full suite was not run. No live-provider evaluation was run.

The host probe's player-facing texts, recorded as host output and not as a score, were: the existing OOC acknowledgement on S06.1 and S06.3; `Tavern Runner says, "I couldn't tell you."` on S06.2; and `Provider calls are disabled for this run, so no live narration was generated.` on S06.4. S06.4's performance counter reported one provider call while the reply was stamped provider-disabled and tokens were null. The harness preserves that count and does not treat it as a sent request.

## Known limitations

- Simulated mode does not establish a campaign and does not call chat. It validates the harness.
- Host mode shows the provider-disabled path. Naturalness stays unchecked.
- The first live baseline has not been run. Trial count for that baseline is still one unless a later checkpoint says otherwise. Rubric 01 still records efficiency and does not score it.
- Held-out scenarios were visible in the ATGB-01 review. They are not strong independent evidence.
- The runner does not reconstruct a clean `world.json` from git. It copies the repository file and uses the existing playthrough reset.
- No historical build is executed. There is no compatibility adapter.
- Sampling controls are `uncontrolled`. Cost is unavailable without a supplied price and recorded tokens.
- `docs/product_realization_validation.md` already had an uncommitted generalization paragraph before this pass. This pass does not adopt that diff as its own change.
- The session orientation's product narrative remains the 2026-09-26 PR-BL closeout. Later PR-EG history is still unreconciled. This pass does not reconcile it and does not start another product campaign.

## Next step

Review this infrastructure. Do not start a live ATGB baseline until that review accepts the corpus. Do not change production gameplay to improve a score that has not been run.
