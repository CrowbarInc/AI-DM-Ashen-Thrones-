# PR-DL Experiment Report

MODE: BOUNDED LIVE COMPARATIVE EXPERIMENT

PRODUCTION INTEGRATION: NONE

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty. PR-DL preserved it. Production saves were guarded during preparation and during both live stages.

Provider configuration: `DEFAULT_MODEL_NAME=gpt-4.1-mini`, temperature 0, Responses API, strict JSON schema, `max_output_tokens` 400. The response model was `gpt-4.1-mini-2025-04-14`. The PR-DH planner schema was not reused because it includes `proposed_resolver`, `advance_time`, and `expects_mutation`.

PR-DK matrix, recomputed before live calls: A TP=3 FP=0 FN=6; B TP=8 FP=2 FN=1; C TP=9 FP=12 FN=0.

Live requests: 21
Actual input tokens: 15943
Actual output tokens: 2811
Actual total tokens: 18754

One interpretation was stored per scenario and replayed.

- Policy A fully handled 11 scenarios.
- Policy B fully handled 16 scenarios with 10 calls.
- Policy C fully handled 17 scenarios with 21 calls.

Stage 1 (ordinary social, ambiguous pronouns, compound action) returned usable schema-valid interpretations with no execution and no state mutation. Stage 2 used the remaining scenarios once.

PR-DL decision: C — HYBRID REFINEMENT REQUIRED
