# Actual acceptance and publication trace

Milestone `pr_play_claim_acceptance_audit`. One-based source locations refer to current hash-verified files. Instrumentation wraps functions, records arguments/results and delegates once. It changes no implementation behavior. Three-case trace retains seven nested completion events per defect; return ordering is not an invented linear call graph.

| Actual stage | Owner / source location | Evidence |
|---|---|---|
| Interpret/classify | referenced_surface.py:350; exploration.py:396/:566 | Hidden, abstract or unsupported inspect target |
| Structured resolution | exploration.py:591 onward | investigate success=True; no clue, retrieval, state_changes or transition |
| Authority assembly / mutation | api.py:4739 `_run_resolved_turn_pipeline` | attach interaction obligation, apply authoritative mutation, reconcile movement BEFORE candidate generation |
| Candidate | api.py:3298 builder, :3877 guard around bounded call; existing test `_chat` :149 | Local fixture game.api.call_gpt stub; exact sentence survives guard |
| Preparation | immutable_valid_response.py:1624 | Host speech not adopted; resolver-fact and selected-information preparation do not replace candidate |
| Claim and hard validation | `_check` :1703 → validate_generated_response :623 → gm_resolution_decision.py:3410 | authority=[], mechanical claims=[], audit proposed_facts/claim_results/violations=[]; hard_valid=True |
| Pre-seal perception check | immutable file :1256 → perception_grounding.py:491 | checked=True, flags=[], unsupported=False |
| Acceptance / seal | immutable file :1860–1893, seal_accepted_response :1301, _finish :1811 | initial_hard_valid; attempt 1; immutable=True; initial_generation; no regeneration |
| Grounding | api.py:4461; perception_grounding.py:757/:771 | leave_text_unchanged returns before evidence and force_surface; skipped mutator recorded |
| Effects / persistence | api.py:2119, :6308 persistence helper, :6525 effects, :6705 restore | Separate effect owners; inventory/NPCs unchanged; text stored in log/exchange/publication |
| Publication | api.py:6782 finalizer, :6792 note_completed_publication; :5377 DTO projection | HTTP text equals candidate; resolution becomes empty public compatibility placeholder |

Chat enters `_chat_turn` (:7149), resolved exploration uses the shared resolved-turn pipeline, then `_complete_opening_turn_persistence_like_chat` (:8360), despite that helper's name. These three seal in the normal initial-generation lifecycle at :4021. Other routes can adopt host speech, use an engine-authored consequence before narration, or reach a second unresolved guard (:4397). No universal pipeline is claimed.

Accepted metadata in each case: adoption_status=candidate_accepted; authorization_source=initial_generation; immutable=true; authority_result=accepted; attempt=1; hard_valid=true; reasons=[], soft_flags=[]; contract_satisfying=true; grounding_result=not_a_replacement_trigger. A literal candidate_status field is absent in these acceptance records; adoption_status carries the recorded disposition. That grounding label is not proof downstream grounding evaluated the surface. The delivery digest binds accepted text; final player-visible text is identical.

Claim extraction is present but incomplete. `_check` selects audit_narration_against_decision because realization_envelope.declared_claims is absent on this legacy GM response fixture. The audit calls audit_narrated_claims and then classify_narrated_fact, which calls that recognizer again. Both calls return []. Nothing is extracted and discarded. Each governing GM decision separately contains four authored facts and no permitted mutations. Audit proposed_facts, decision proposed_facts and bounded improvisation proposals are different collections.

Mechanical recognition (mechanical_claims.py:167) does not match coordinated “You pry … and pocket …”. GM decision structural/proposition patterns do not match these record list/count sentences. Perception's hidden-fact detector (:472) compares a first six-word span: “brass token is sealed under the” is absent from the acquisition prose. Its bounded evidence/event categories do not recognize these record contents. `_unsupported_perception` checks classifier.unsupported, not the downstream force_surface policy (:821). Thus the explicit restriction is available but unenforced before sealing.

Post-seal leave_text_unchanged (:234) and restore_accepted_text (:1368) intentionally protect identity. Grounding is skipped, not applied then undone. effects_allowed (:256) is not an item/world grant. Player projection is a privacy/shape adapter, not semantic authority; public resolution={} is PR-PLAY-67's contract. No separate model fact-check pass or accepted new-world proposal occurs.
