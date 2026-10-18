# PR-DP Experiment Report

MODE: BOUNDED LIVE QUALIFICATION AND IMPLEMENTATION DISCOVERY

Production integration: none. Gameplay execution: none. Vertical slice: designed, not implemented.

## Phase 0

- git HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff
- Dirty worktree preserved. Status length: 17612 characters.
- Provider model pin: gpt-4.1-mini
- Environment DEFAULT_MODEL_NAME: gpt-4.1-mini
- API key present: True
- Save fingerprints unchanged by the isolation probe: True
- engine_submission links in game/ or tools/: []

## Phase 1

- Contract issues: none
- The provider schema copies the model-writable PR-DO properties and enums. The documentation key `not_model_writable` is omitted because it is not a model field.
- schema_grants_execution: False

## Live calls

- Requests: 3
- Input tokens: 1804
- Output tokens: 695
- Total tokens: 2499
- Stop reason: stage1_unusable

- DP02 model=gpt-4.1-mini-2025-04-14 classes=['ASK', 'ASK', 'ATTACK'] disposition=NEEDS_CLARIFICATION schema=True class_match=False mode=False authority=True unusable=True
- DP06 model=gpt-4.1-mini-2025-04-14 classes=[] disposition=NEEDS_CLARIFICATION schema=True class_match=False mode=False authority=True unusable=True
- DP08 model=gpt-4.1-mini-2025-04-14 classes=[] disposition=OUT_OF_CHARACTER schema=True class_match=True mode=True authority=True unusable=False

## Decision

G — INCONCLUSIVE

Scoring separates schema acceptance, semantic accuracy, adapter safety, and engine support. Those numbers are in `PR-DP_contract_scores.csv` and are not interchangeable.
