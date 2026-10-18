# 18 — Changed-File Inventory

| File | Purpose | Tests |
| --- | --- | --- |
| `game/ordinary_semantic_ownership.py` | `assess_addressee_grounding`, authorization record, contract binding, narration-skip predicate | `tests/test_pr_ef_r4_authorization.py`, R1/R2 authority tests |
| `game/conversational_orchestration.py` | Ownership reclassification, unresolved-address clarification, correction, confirmation, withdrawal, decision `authorization` field | `tests/test_pr_ef_r1_semantic_handoff.py`, `tests/test_pr_ea_conversational_orchestration.py` |
| `game/player_interpretation_bridge.py` | ASK accepted only when grounding is executable, or when a pending candidate was confirmed | R4 holdouts, R2 captured-authority tests |
| `game/api.py` | Pre-tick gate, pending/executed intention persistence, narration skip and retry break | Live `/api/chat`, pipeline family |
| `game/interaction_completion.py` | Speech-act nominal, including tell/warn and question-to; “Instead” is not a vocative | Compound correction, location and movement regressions |
| `game/immutable_valid_response.py` | Safe line uses the authorization clarification when the target is unresolved | Historical “one of them” test |
| `tests/fixtures/pr_ef_r4_holdouts.json` | Frozen expressions. Not edited to match results | Live and scripted holdouts |
| `tests/test_pr_ef_r4_authorization.py` | Scripted state-integrity harness | 28 passes in the family junit |
| `tools/validate_pr_ef_r4.py` | Fresh-provider conversation, holdouts, and performance cases | `artifacts/pr_ef_r4/live_qualification.json` |

Resolvers in `game/social.py`, travel, exploration, combat, and `game/world.py` were not given a new outcome path.

No commit was created.
