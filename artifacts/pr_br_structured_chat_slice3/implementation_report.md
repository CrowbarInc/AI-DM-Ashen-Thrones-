# PR-BR Slice 3 — Production Enforcement and Chat-Path Closure

Generated: 2026-10-04
Scope: make the existing one-call envelope unavoidable on ordinary GM generation.
Architecture kept: `GMResolutionDecision.realization_claims[]` owns consequential semantics; the model returns `declared_claims[]` plus `narration`; validation is declarations, then decision authority, then narration audit, then the C18 seal.
Gameplay/model API calls: 0. No live validation. No 4x10 gate. No commit. No push.

## 1. Executive conclusion

Ordinary live GM generation now requires a structured claim envelope before model text can become narration. `call_gpt` parses with `require_structured_claims=True`. Plain prose, malformed JSON, and legacy `player_facing_text`-only JSON become an empty candidate marked `structured_contract_failure` with `legacy_fallback` false. The existing one-retry path asks for the same envelope and includes the resolution contract, decision, accepted realization claims, rejected declarations, validation reason, and envelope schema. Exhaustion uses `safe_nonresolution`, a fixed local sentence, not another unrestricted model call.

Raw `/api/chat` tests stub only the OpenAI transport and traverse contract, decision, declaration audit, narration audit, seal, temporal commit, and emission. Authorized facts seal. Declared unauthorized causes, undeclared causes, and plain prose are rejected before emission. The saved bathhouse cause sentence is not emitted and is not stored as `gm_inference` or scene fact. An authorized inference persists as `gm_inference` and is not promoted on the next turn. A mundane NPC mannerism persists in the incidental ledger and is not written as world truth. Social and movement player texts that reach the model use the same transport and reject plain prose. Six malformed envelope shapes emit no raw JSON.

The five previously stalled raw-chat nodes terminate. Their mechanism is a Windows shared pytest basetemp collision, measured in isolation at about 1.6–3.5 seconds each. They are not an orchestration deadlock.

## 2. Production-path invariant

For ordinary model-generated gameplay:

structured envelope -> declaration validation -> narration validation -> seal

or

missing or malformed envelope -> one structured retry -> `safe_nonresolution` if still invalid.

`call_gpt` is the only player-facing model transport. It always calls `_safe_json(..., require_structured_claims=True)`. A string such as "The cracked beam probably failed in the storm." is `output_form=plain`, `structured_contract_failure=True`, `player_facing_text=""`, `legacy_fallback=False`. `_check` adds reason `structured_contract_failure` and forces the candidate hard-invalid. `_bounded_keep` is skipped for that candidate, so the prose cannot be sentence-preserved under the old authority rules.

## 3. Model-output entry-point audit

| Entry point | Output form | Structured required | Decision attached | Declaration validation | Narration validation | Retry structured | Seal | Temporal commit | Player-facing emission | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game.gm.call_gpt` | model `output_text` | yes | after parse, in chat | yes, via preserve-if-valid | yes | yes, same `call_gpt` | yes, when valid | yes, after seal in `api_turn_support` | only after seal | A. Structured-required production |
| `_safe_json(..., require_structured_claims=True)` | envelope or contract failure | yes | no, parser only | no, parser only | no | n/a | n/a | n/a | empty text on failure | A. Structured-required production |
| `_safe_json` default (`require_structured_claims=False`) | plain, malformed, or structured | no | no | no | no | no | no | no | only if a caller emits it | B. Legacy test/migration helper. Live `call_gpt` does not use this default |
| `classify_model_output` | form label | no | no | no | no | no | no | no | no | Classifier only. Live path rejects plain after classification |
| `/api/chat` -> `_build_gpt_narration_from_authoritative_state` -> `_bounded_call_gpt` | GM dict | yes | yes | yes | yes | yes | yes | yes | yes | A. Structured-required production |
| Social and movement player texts that reach that builder | same GM dict | yes | yes | yes | yes | yes | yes | yes | yes | A. Same boundary. Proven by raw-chat transport calls |
| `regeneration_feedback` + `retry_authority_context` | retry user message | yes | yes, JSON context | n/a | n/a | yes | n/a | n/a | no | A. Structured retry instruction |
| `safe_nonresolution` | fixed local sentence | n/a | uses contract operation | n/a | n/a | no further model call | sealed as safe provenance | no new consequential claim | yes | D. Safe fallback |
| `call_gpt` provider exception | fixed unavailable sentence | n/a | n/a | n/a | n/a | no | existing fallback family | no | yes, non-model sentence | D. Safe fallback |
| Local observation overwrite (`realize_local_observation_line`) | deterministic line | only a failed envelope is stripped | decision already built | deterministic line replaces failed model text | existing lifecycle | n/a | yes | existing | yes | C/D. Non-model replacement. A valid structured envelope is left intact |
| `_build_adjudication_gm_output` | deterministic, `regenerate=None` | no model | yes | existing preserve path | existing | no model retry | yes | existing | yes | C. Non-model internal path |
| `_build_offscene_target_gm_output`, `_build_check_prompt_gm_output`, scene opening | deterministic | no model | scene/contract | n/a | n/a | no | existing | existing | yes | C. Non-model internal path |
| Semantic interpreter and upstream preflight | non-narration model clients | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no player narration | C. Non-GM model path. Disabled by the test guard and env flags |
| Continuation raw-chat tests that monkeypatch `game.api.call_gpt` to a prose dict | dict, bypasses `_safe_json` | no | test fixture | whatever the later lifecycle does | yes, if lifecycle applies | fixture-defined | yes | existing | yes, in tests | B. Explicit legacy test path. Not reachable from live `call_gpt` |
| `planner_input_manifest` `LEGACY_FALLBACK` | planning label | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no | Unrelated CTIR-absence label. Not narration authority |

No entry point was left classified as an unknown live bypass.

## 4. Plain-prose enforcement

`_structured_contract_failure` returns empty player-facing text, tags `structured_output_rejected` and `structured_contract_failure`, and `legacy_fallback: False`.

Live reasons:

- malformed JSON: `malformed_envelope`
- plain prose: `missing_structured_envelope`
- structured JSON without a `declared_claims` list, including legacy `player_facing_text` JSON: `missing_declared_claims`

`run_preserve_if_valid` treats that flag as hard-invalid and refuses bounded sentence-keep of the failed candidate and of a failed retry. The first failure requests a structured retry. The second failure seals `safe_nonresolution`.

`test_call_gpt_rejects_plain_prose_before_it_can_be_narration` and `test_raw_chat_plain_prose_is_a_structured_contract_failure` both passed. The chat case emitted the retry sentence "The beam is cracked." with regeneration provenance. The exhausted case emitted the safe inspection sentence and never the stub prose.

## 5. Structured retry behavior

`regeneration_feedback` special-cases `structured_contract_failure` first. The message names the reason, requires JSON `declared_claims` plus `narration`, includes the envelope example, and states that plain prose is not valid. `_with_retry_authority` appends `retry_authority_context`, whose JSON contains:

- `resolution_contract`
- `gm_resolution_decision`
- `accepted_realization_claims`
- `rejected_declarations`
- `validation_failure`
- `structured_envelope_schema`

The retry is another `call_gpt`, so it is parsed again with `require_structured_claims=True`. Case B asserted those four context keys on the retry message and emitted only the retry narration. Case D asserted `structured_contract_failure` and `declared_claims` in the retry feedback.

Other hard validation reasons also tell the retry to return `declared_claims` plus `narration`.

## 6. Safe fallback behavior

`safe_nonresolution` is local text chosen from the contract operation. For a single-dimension inspection it is "The inspection establishes no further reliable detail about the {dimension}." It does not call the model and does not splice the rejected prose. The exhausted plain-prose chat test asserted safe provenance, absence of the stub sentence, absence of envelope keys, and at most three transport calls.

Provider exceptions inside `call_gpt` still become the existing fixed unavailable sentence through `attach_realization_fallback_family`. That path is not unrestricted prose generation.

## 7. Exact diagnosis of each previously stalled node

Each node was run alone with the live-model guard, `--override-ini="addopts="`, and its own `--basetemp`. Parallel runs against the shared `development/tmp/pytest` basetemp from `pytest.ini` collide on Windows (`WinError 183` file exists, `WinError 145` directory not empty, and `FileNotFoundError` when a sibling process deletes the tree mid-test). That collision is the stall mechanism. It is not a deadlock, TestClient lifecycle hang, retry loop, contract loop, state lock, or model call.

| Node | Isolated result | Mechanism |
| --- | --- | --- |
| `tests/test_pr_br_continuation18_immutable_boundary.py::test_raw_chat_stub_preserves_valid_and_contains_invalid` | passed, about 2.7s | Shared basetemp collision when run beside other raw-chat processes. Alone it completes. The stub patches `call_gpt` and returns a prose dict; that is the allowed legacy test path and was not the stall. |
| `tests/test_pr_br_continuation19_hard_authority.py::test_raw_chat_stub_authority_and_contracts` | passed, about 3.5s | Same shared-basetemp collision. Isolated run completes. |
| `tests/test_pr_br_continuation20_incidental_entity.py::test_raw_chat_stub_covers_incidental_binding_and_authority` | passed, 2.10s | Parallel shared basetemp raised `FileNotFoundError` for `world.json` because another pytest removed the tree. Isolated run completes. |
| `tests/test_pr_br_continuation23_precontract_routes.py::test_q_probes_do_not_call_models` | passed, 2.79s | Parallel shared basetemp raised `FileNotFoundError` for `frontier_gate.json`. Isolated run completes. The node does not call models. |
| `tests/test_pr_br_continuation25_semantic_ownership.py::test_chat_turns_keep_one_contract_and_do_not_execute_uncommitted_travel` | passed, 1.62s | Parallel shared basetemp raised `FileExistsError` creating `development/tmp/pytest` plus `rm_rf` `WinError 145`. Isolated run completes. |

After this slice, the full C18–C25 files, including those five nodes, passed: 139 passed in 19.24s on isolated basetemp `development/tmp/pytest_br_slice3_c18`.

## 8. Stub migrations

The five continuation nodes were not migrated. They already terminate, and they patch `call_gpt` with a dict. Wrapping their expected sentences in empty `declared_claims` would change the authority surface those tests assert. They remain the explicit legacy test path.

New raw-chat coverage stubs the OpenAI `responses.create` transport and returns the envelope. `test_model_routing_runtime.py` and `test_model_routing_escalation.py` restore `production_call_gpt()` after installing a fake OpenAI client, so they exercise the real parser. One routing mock of `_safe_json` now accepts `**kwargs` because live `call_gpt` passes `require_structured_claims=True`. Those tests passed in the final unit batch.

A declaration matcher fix was required for live chat: `_declared_identity_matches_realization` now treats exact normalized text as a match before the short-token cover check. "The beam is cracked." is two content tokens after the length-4 filter, so the older cover rule rejected an exact authored sentence as `unauthorized_declared_claim` and the chat path sealed the safe inspection line. Exact equality is the match. Modality strengthening still runs after the match. This is not a new detector and not new vocabulary.

## 9. Raw-chat composition test design

File: `tests/test_pr_br_structured_chat_path.py`.

The primary seam is `TestClient` `POST /api/chat`. The test restores production `call_gpt` on `game.gm` and `game.api` and replaces `openai.OpenAI`. It does not call `audit_realization_envelope_against_decision` as the seam. `_exact` records initial raw output, parsed envelope, accepted text, sealed text, and emitted text, and asserts accepted == sealed == emitted, with no envelope keys and no leading brace in the emission.

- Case A `test_raw_chat_accepts_authorized_fact_and_seals_it`: authorized "The beam is cracked." Initial provenance. Passed.
- Case B `test_raw_chat_rejects_unauthorized_cause_and_emits_only_the_retry`: storm-cause declaration rejected; only the retry sentence emitted. Passed.
- Case C `test_raw_chat_rejects_undeclared_cause`: declaration is the authored observation; narration "The storm cracked the beam." is rejected; retry sentence emitted. Passed.
- Case D `test_raw_chat_plain_prose_is_a_structured_contract_failure` and the exhausted-fallback sibling: plain prose is a contract failure; retry or safe fallback. Passed.

## 10. Saved Turn-3 raw-chat result

`test_saved_turn3_cause_is_not_emitted_or_promoted` seeds bowed handle and sheared pin as visible facts and stores sudden pressure as a player hypothesis. The first stub declares those observations plus sudden pressure as a likely cause, with the saved narration "I can't swear to it, but from what I saw, sudden, violent pressure seems a likely cause of the bowed handle and sheared pin."

Result: that narration is absent from the emission; "likely cause" is absent; "bowed" is present; a retry occurred; `gm_inferences` contain no "sudden"; scene visible facts contain no "sudden". Passed.

## 11. Temporal inference raw-chat result

`test_authorized_inference_persists_without_promotion` uses player text "I inspect the cracked axle. What does the damage suggest?" so the contract includes interpretation and the decision permits infer. The stub proposes excessive strain as a possible cause. Narration "Excessive strain is one possibility." is sealed. Session `gm_inferences` contain the proposition with provenance `gm_inference` and authority other than world truth. The next chat turn reads that claim as `AUTH_INFERENCE`. The second emission keeps "possibility" and does not say "established". Visible facts do not contain excessive strain. The test does not call the ledger writer itself. Passed.

A bare "What can I infer from the damage?" routes to deterministic adjudication and never calls the model. That is a non-model path, documented in section 13.

## 12. NPC incidental raw-chat result

`test_mundane_npc_improvisation_persists_without_world_truth` declares no consequential claims and narrates "The porter folds the cloth lengthwise and says he prefers lavender soap." with an incidental mannerism proposal. The sentence is emitted. The bounded improvisation ledger contains lavender soap. Visible facts do not. The second turn, "I mention the soap he preferred.", still emits soap continuity and the ledger entry remains. Passed.

## 13. Social/movement path audit

Social and movement narration that calls the model goes through `_build_gpt_narration_from_authoritative_state` and therefore `call_gpt`. `test_social_and_movement_model_paths_reject_plain_prose` posted "I ask the gate guard who keeps the watch." and "I walk toward the notice board." Both invoked the transport (`calls` non-empty), rejected the first plain-prose response, and emitted the structured retry. Neither emission contained `declared_claims` or the rejected prose. Passed.

Deterministic builders that do not call the model remain non-model paths: adjudication (`regenerate=None`), off-scene target, check prompt, and scene opening. They do not parse model prose into narration. No resolver-specific model path was found that emits player-facing GM narration without `call_gpt`.

## 14. Malformed-envelope raw-chat results

`test_malformed_envelopes_do_not_leak_and_fall_back` repeats each sample on both attempts:

1. truncated JSON
2. JSON missing narration
3. JSON missing `declared_claims`
4. prose wrapping JSON
5. two concatenated envelopes
6. `declaration_mode` `world_truth` with narration "The storm caused the crack."

Each emission contains no `declared_claims`, no `player_facing_text`, no `world_truth`, no storm sentence, and no `{`. Transport calls were between 1 and 4. Passed.

## 15. C18 exactness evidence

`_exact` asserts `accepted_response.text == player_facing_text` for every raw-chat structured test, and that the emission does not contain `declared_claims` or `player_facing_text` and does not start with `{`. Case A additionally asserts accepted == sealed == emitted == "The beam is cracked." with initial provenance. Retry cases assert regeneration provenance and that the first narration is absent. Safe cases assert safe provenance. No post-seal mutation was observed in these tests.

## 16. Legacy-fallback audit

| Occurrence | Classification |
| --- | --- |
| `call_gpt` -> `_safe_json(..., require_structured_claims=True)` | Live path. `legacy_fallback` is false on both success and contract failure. Plain prose is not accepted. |
| `_safe_json` plain branch when `require_structured_claims` is false | Explicit legacy helper for direct unit tests. `metadata.legacy_fallback` is true. `call_gpt` does not take this branch. |
| Envelope field `legacy_fallback` when the live parser has `declared_claims` | False on the live path. True only for the non-required helper when `declared_claims` is absent. |
| Local-observation replacement of a contract-failure envelope | Sets `legacy_fallback` false and `deterministic_realization` true. It does not restore model prose. |
| `planner_input_manifest.LEGACY_FALLBACK` | Planning label for non-CTIR resolution when CTIR is absent. Not player-facing model prose. |
| Continuation tests that replace `call_gpt` with a prose dict | Explicit legacy test path. Not reachable by live generation. |

Normal GM model generation has no silent prose fallback. The remaining plain-prose acceptance is the named helper default and the named test patches.

## 17. Static authority audit

Search of production narration authority:

- Player-facing model text enters through `call_gpt` -> `_safe_json(require_structured_claims=True)` -> `run_preserve_if_valid` -> `audit_realization_envelope_against_decision` when `declared_claims` is present. A missing envelope never reaches that audit as narration; it is hard-invalid first.
- No ordinary live path was found that copies model narration into `world_truth` or authored visible facts without an accepted decision claim.
- `scene_update` remains a separate structured field on the parsed envelope. Adoption still goes through the existing scene-update validator. This slice did not move that field into realization claims. It is not a prose-authority bypass, and changing it would be a new semantic design.
- Deterministic adjudication, opening, off-scene, and check-prompt text is not model output.

Expected result on the ordinary live GM generation path: no narration-to-authored-authority path without an accepted decision claim, and no model emission without structured declaration validation. That is the state after this slice.

## 18. Broad regression totals

All runs used the live-model guard, skipped upstream preflight, disabled live interpretation, and used an isolated basetemp. No gameplay generation, interpretation model, preflight model, or external transport was invoked.

| Suite | Result |
| --- | --- |
| Slice 3 raw-chat structured tests (`tests/test_pr_br_structured_chat_path.py`) | 11 passed in 2.75s |
| Slice 2 envelope, Slice 1 decision-owned claims, claim control 1/2, semantic fidelity, GMResolutionDecision, decision ownership, C19 free text, qualifier/movement/mixed intent, bounded improvisation, NPC promotion, claim-control regex bound, live-model guard, model routing, C26, C27 | 138 passed in 12.45s |
| C18–C25, including the five previously stalled nodes | 139 passed in 19.24s |
| Routing plus envelope plus chat confirmation after the routing mock fix | 39 passed in 3.10s (subset of the rows above) |

Counted unique file runs for the required list: 11 + 138 + 139 = 288 passed. Zero failures in those runs.

## 19. Unrelated failures

None remain in the required deterministic set.

During the first unit batch, ten model-routing tests raised `LiveModelCallForbidden` because the autouse guard replaces `game.gm.call_gpt` and those tests stub OpenAI while still calling the guarded function. That guard predates this slice's envelope requirement. Classification: test harness interaction with the live-model guard, not a gameplay-authority regression. Repair inside the test helpers: restore `production_call_gpt()` when the test installs its own OpenAI stub, and accept the new `_safe_json` keyword in the one metadata mock. After that repair those tests pass inside the 138.

No unrelated gameplay defect was repaired.

## 20. Files changed

Production:

- `game/gm.py` — live `_safe_json` requires `declared_claims`; plain and legacy JSON are contract failures.
- `game/immutable_valid_response.py` — structured-contract failure is hard-invalid, skips bounded keep, and the retry message demands the envelope.
- `game/gm_resolution_decision.py` — retry context includes the decision, accepted claims, rejected declarations, and schema; exact normalized declaration text matches an authored claim.
- `game/api.py` — a deterministic local-observation replacement clears a contract-failure envelope so the replacement is not poisoned. A valid structured envelope is left intact.

Tests:

- `tests/test_pr_br_structured_chat_path.py` — raw-chat composition, Turn-3, temporal, NPC, social/movement, and malformation cases.
- `tests/helpers/live_model_guard.py` — captures production `call_gpt` before the guard replaces it.
- `tests/test_model_routing_runtime.py` and `tests/test_model_routing_escalation.py` — restore production `call_gpt` under the fake OpenAI client; metadata mock accepts the new keyword.

No commit. No push.

## 21. Known limitations

- Direct callers of `_safe_json` without `require_structured_claims=True` can still parse plain prose. Live `call_gpt` does not.
- Old tests that replace `call_gpt` with a prose dict bypass the parser. They are explicit fixtures.
- `scene_update` adoption remains the existing validator, not a realization claim.
- A question with no concrete action can be answered by deterministic adjudication and never reach the model. That text is not model prose.
- Short authored facts now match by exact normalized text. Fuzzy cover for phrases shorter than three content tokens is unchanged.
- This slice did not run a live model, the 4x10 gate, or PR-BS.

## 22. Exact gameplay/model API call count

0.

The chat tests stub `openai.OpenAI`. The autouse guard raises `LiveModelCallForbidden` if a test reaches the real client, the interpreter, or preflight. Environment flags skip upstream preflight and disable live interpretation. `[MODEL ROUTE]` lines in test output are local log statements from the routing helper after the stubbed transport returns.

## 23. Recommendation

The structured claim boundary is enforced on the live chat path, including retry and safe fallback. The five stalled nodes have a measured harness cause and now terminate. The next useful spend is a small live-token check of real model envelopes, not another deterministic semantic layer.

A.
STRUCTURED CLAIM BOUNDARY IS ENFORCED THROUGH THE LIVE CHAT PATH;
PROCEED TO SMALL LIVE VALIDATION
