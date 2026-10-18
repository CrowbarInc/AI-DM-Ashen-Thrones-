# PR-BR Structured One-Call Claim Boundary Report

## 1. Executive conclusion

Structured one-call claim declaration is implemented on the production-facing parsing and hard-validation path. Model declarations expose intended consequential semantics, but authority remains owned by `GMResolutionDecision`.

## 2. Structured envelope design

Added `GMRealizationEnvelope` and `DeclaredRealizationClaim` in `game/gm_resolution_decision.py`. The production-facing JSON shape is `declared_claims[]` plus `narration`; `player_facing_text` remains only temporary legacy compatibility.

## 3. Production generation-path integration

`game/gm.py` prompt contract now asks for the one-call envelope. `_safe_json` parses `declared_claims` and `narration`, stores declarations in `metadata.realization_envelope`, and never emits raw JSON to the player.

## 4. Declaration validation

`validate_declared_claims_against_decision` validates every declared claim before prose audit. `realize` must match a `GMResolutionDecision.realization_claims` row. Declarations do not self-authorize.

## 5. Proposal acceptance

`propose` is accepted only as bounded inference when the decision explicitly permits `infer`. World-truth requests, negative evidence, actor/time/history/state mutation, and specific leads are rejected.

## 6. Inference handling

Accepted proposals become `gm_inference` with `authority=inference`, non-world-truth persistence, and bounded temporal eligibility.

## 7. Player-hypothesis handling

Player hypotheses can be realized only at hypothesis strength. Establish-like declaration or narration is rejected unless a later authored/explicit promotion claim exists.

## 8. Negative-evidence handling

Negative evidence proposals such as “no footprints” fail without a source-owned realization claim.

## 9. Gameplay-lead handling

Specific leads such as “dockworkers may know” fail as unauthorized proposals unless a corresponding source-owned claim exists.

## 10. Incidental-freedom behavior

Mundane incidental/NPC texture remains accepted without exhaustive declaration. Consequential NPC accusations must be declared and authorized.

## 11. Narration/backstop responsibility

Residual detectors remain as a backstop for undeclared consequential content. Their role is now contract enforcement, not primary semantic discovery.

## 12. Retry behavior

`regeneration_feedback` requires retries to return the same structured envelope shape and forbids repeating rejected declarations/prose.

## 13. Malformed-envelope behavior

Malformed envelopes are rejected by `classify_model_output`/`_safe_json` and emit no raw JSON to player text.

## 14. Temporal persistence

Temporal persistence still flows through sealed accepted response audits. Accepted declaration claims enter `claim_results`; rejected proposals do not become world truth.

## 15. Saved Turn-1 result

Synthetic Turn-1-style cause proposals are visible as declarations. Without infer permission they reject; with infer permission they are accepted only as `gm_inference`.

## 16. Saved Turn-3 result

Synthetic Turn-3 cause strengthening is rejected before prose authority. Authored observations do not promote the cause to world truth.

## 17. Saved Turn-4 result

Mundane NPC/incidental behavior remains accepted without requiring declaration of every harmless phrase.

## 18. Full composition-test architecture

`tests/test_pr_br_structured_realization_envelope.py` exercises parser, declaration validation, narration backstop, retry through `run_preserve_if_valid`, malformed envelopes, and temporal commit behavior.

## 19. What is mocked

Only model transport is mocked by deterministic synthetic envelopes. Resolution Contract, `GMResolutionDecision`, declaration validation, narration validation, retry, seal, and temporal persistence are not mocked in the composition tests.

## 20. Broad-suite stall diagnosis

The known stall family is exact-node raw chat/API integration tests:

- `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `tests/test_pr_br_continuation19_hard_authority.py::test_raw_chat_stub_authority_and_contracts`
- `tests/test_pr_br_continuation20_incidental_entity.py::test_raw_chat_stub_covers_incidental_binding_and_authority`
- `tests/test_pr_br_continuation23_precontract_routes.py::test_q_probes_do_not_call_models`
- `tests/test_pr_br_continuation25_semantic_ownership.py::test_chat_turns_keep_one_contract_and_do_not_execute_uncommitted_travel`

These are classified as unrelated API/chat integration long runners for this deterministic envelope slice, not model/API calls from this implementation.

## 21. Broad regression totals

Completed deterministic totals:

- Structured envelope suite: 11 passed.
- Adjacent PR-BR decision/claim-control suites: 40 passed.
- Pure semantic fidelity/C19/qualifier-movement: 21 passed.
- Bounded improvisation/NPC/response policy/live-model guard: 62 passed.
- C26 malformed/semantic closure: 8 passed.
- Total completed and counted: 142 passed.

Interrupted/excluded exact raw chat/API nodes are listed in section 20.

## 22. Static production-path audit

Current production path: `call_gpt -> _safe_json -> metadata.realization_envelope -> run_preserve_if_valid -> validate_generated_response -> audit_realization_envelope_against_decision -> seal`.

Legacy fallback: prose-only output is explicitly `metadata.output_form=plain` and `realization_envelope.legacy_fallback` is absent/false only for structured paths; prose-only compatibility remains for migration/tests.

Remaining legacy/post-emission authorities:

- `promote_accepted_bounded_improvisation`: current production path, bounded policy/accepted seal dependent.
- `note_emitted_npc_claim`: current production path, discourse claim tracking.
- `apply_social_narration_lead_supplements` and emergent actor adoption: current production path with validation gates; not redesigned in this slice.

No new prose-to-world-truth path was added.

## 23. Files changed

- `game/gm_resolution_decision.py`
- `game/gm.py`
- `game/structured_player_output.py`
- `game/immutable_valid_response.py`
- `tests/test_pr_br_structured_realization_envelope.py`
- `artifacts/pr_br/structured_one_call_claim_boundary_report.md`

## 24. Known limitations

Plain prose fallback still exists for transition compatibility. The undeclared-content backstop is deliberately conservative and not a general NLI system. Raw chat/API continuation nodes remain long-running blockers outside this slice.

## 25. Exact gameplay/model API call count

0 gameplay/model API calls were made by this implementation and test pass. All generation inputs were deterministic synthetic envelopes.

## 26. Recommendation

Proceed to another deterministic slice only for reducing/removing legacy prose fallback and integrating structured declarations more deeply into the remaining API/chat continuation paths.

B.
STRUCTURED BOUNDARY IS IMPLEMENTED BUT LOCALLY INCOMPLETE;
ANOTHER DETERMINISTIC SLICE IS REQUIRED
