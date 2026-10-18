# PR-EB - Conversational Continuity & Interpretation

## 01 - Executive Summary

PR-EB extends the PR-EA conversational orchestration boundary instead of replacing it.

Implemented:
- Active NPC follow-up questions are converted into the existing authoritative `ASK` bridge record, preserving resolver ownership.
- Natural conversation exit phrases produce a non-mutating conversational answer and clear active interlocutor context.
- Ambiguous pronoun inspection such as "I examine it" creates a bounded pending clarification with visible choices.
- Short clarification replies such as "the lantern" resume the original inspection through the existing bridge/resolver.
- The public decision envelope now carries a compact `context_update` field for pending clarification and conversation exit state.

Primary source references:
- `game/conversational_orchestration.py:40` adds bounded context update metadata to the decision envelope.
- `game/conversational_orchestration.py:250` builds focused ambiguous-reference clarification.
- `game/conversational_orchestration.py:302` resumes pending clarification.
- `game/conversational_orchestration.py:353` routes active-interlocutor follow-ups.
- `game/api.py:784` persists non-mutating conversational context updates.
- `game/api.py:809` applies the bounded continuation update.
- `game/api.py:5989` passes session/world context into deterministic orchestration.
- `game/api.py:6001` allows deterministic `EXECUTE` decisions to enter the existing bridge.

Decision: B - PR-EB ACCEPTED WITH LIMITATIONS.

Why: the central multi-turn continuity path works in focused production-entry tests, ambiguity is clarified and resumable, executable outcomes still go through existing authority, and provider calls are not added to every turn. Limitations remain around broader social/final-emission regressions and richer factual grounding.

## 02 - Architecture Comparison

PR-EA flow:
Browser `/api/chat` -> communication mode -> deterministic conversational decision -> non-mutating answer/clarify/decline or existing bridge/resolver.

PR-EB flow:
Browser `/api/chat` -> communication mode -> deterministic conversational decision with session/world context -> optional bounded context update -> non-mutating answer/clarify or deterministic bridge record -> existing bridge/resolver.

Context ownership:
- Authoritative world state and visible catalog remain owned by existing scene/world/session structures.
- Active interlocutor remains in `session["interaction_context"]`.
- Pending clarification is stored in `session["conversational_context"]["pending_clarification"]`.
- No unrestricted knowledge graph or canonical speculative fact store was added.

## 03 - Conversational Context Contract

Fields introduced:
- `ConversationalDecision.context_update`
- `session.conversational_context.pending_clarification`

Pending clarification stores:
- original intention text
- missing operation slot
- visible choices
- scene id

Reference rules:
- Active social interlocutor is the default addressee for ordinary follow-up questions.
- Pronoun inspection resolves only when exactly one visible inspect/perceive target exists.
- Multiple plausible visible targets produce a focused clarification.
- Clarification expires when the scene changes.
- Conversation exit clears active social interlocutor without advancing world state.

## 04 - Production Integration Evidence

Actual `/api/chat` routing:
- `chat()` now passes `scene`, `world`, `session`, and recent log into `deterministic_conversational_decision`.
- If the decision is `EXECUTE`, `/api/chat` hands `decision.proposed_record` to `normalized_action_from_interpretation`.
- The existing bridge still validates operation, target visibility, compatibility, and movement destination before any resolver sees it.

Resolver handoff:
- `test_pr_eb_active_npc_followup_routes_to_existing_social_resolver` demonstrates "Which captain?" becomes an `ASK` to the active NPC and resolves as `kind == "question"`.
- `test_pr_eb_ambiguous_pronoun_inspection_resumes_after_clarification` demonstrates "the lantern" resumes an original inspection through the existing investigation/observation resolver.

## 05 - Behavioral Acceptance Results

1. NPC Follow-Up - PASS. Active interlocutor retained and existing social resolver invoked.
2. Pronoun Resolution - PARTIAL. Unambiguous/ambiguous visible object pronouns work for inspection; named-person motive grounding remains resolver/NPC knowledge dependent.
3. Subject Change - PARTIAL. Active interlocutor is retained for follow-up questions, but no full topic stack was introduced.
4. Conversation Exit - PASS. "That's enough for now." clears active interlocutor with no world mutation.
5. Dialogue to Movement - PARTIAL. Deterministic bridge can preserve primary movement when represented; full multi-action execution remains out of scope.
6. Clarification Continuation - PASS. Ambiguous "I examine it." followed by "the lantern" restores the original inspection.
7. Earlier Narration Reference - PARTIAL. PR-EA recent-visible answer remains; richer reference recovery is not complete.
8. Unknown NPC Knowledge - PARTIAL. Existing social resolver still owns uncertainty; PR-EB does not promote NPC claims to world truth.
9. Save/Load Continuity - PARTIAL. Pending context is persisted in session; explicit reload scenario was not separately exercised.
10. Ambiguous Reference - PASS. Multiple visible targets produce focused clarification, no arbitrary inspection.
11. Unmarked OOC Question - PASS via PR-EA compatibility test.
12. Ordinary Executable Action - PASS via PR-DU production chat sequence and PR-EA compatibility tests.

## 06 - Grounding and Authority Audit

Permitted:
- Restating bounded conversation-exit text.
- Asking focused clarification from visible choices.
- Routing follow-up questions to an already active NPC.
- Resuming a previously stored pending inspection intent.

Prevented:
- No new world facts are created by reference resolution.
- No NPC answer is treated as objective world truth by orchestration.
- Ambiguous "it" does not choose a target arbitrarily.
- Conversation exit does not imply movement.
- Follow-up dialogue does not bypass social resolver authority.

Known limitation:
- The current architecture still lacks a safe mechanism for rich incidental factual invention. PR-EB therefore routes or clarifies rather than inventing.

## 07 - Persistence Validation

Validated:
- Non-mutating conversation exit saves cleared interaction context.
- Ambiguous inspection saves pending clarification.
- Clarification reply clears pending clarification after authoritative resolver handoff.

Not fully validated:
- A separate save/reload process boundary was not run. The data lives in persisted session JSON, so the implementation is save-compatible, but the acceptance scenario is classified PARTIAL rather than PASS.

## 08 - Performance Comparison

Live provider calls during validation: 0 real live calls.

Focused deterministic observations:
- Conversation exit: 0 interpretation requests, 0 narration requests, 0 retries.
- Ambiguous pronoun clarification: 0 interpretation requests, 0 narration requests, 0 retries.
- Active NPC follow-up: 0 extra interpretation requests; existing social narration path was stubbed in tests.
- Clarification continuation: no extra interpretation request; existing resolver/narration path was used.

No mandatory provider call was added to every conversational turn.

## 09 - Regression Comparison

Important limitation: a complete before-implementation broad baseline was not captured before code edits began. This review therefore does not label broad failures as inherited solely by assumption.

Post-change focused validation:
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_eb_conversational_continuity.py -q --tb=short --basetemp=codex_pytest_tmp_pr_eb`
  - Result: 3 passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ea_conversational_orchestration.py tests\\test_pr_eb_conversational_continuity.py tests\\test_social.py::test_follow_up_without_explicit_target_id_keeps_guard_captain_via_continuity tests\\test_social.py::test_active_interaction_target_set_and_switches_on_social_exchange tests\\test_social.py::test_non_social_context_update_clears_target tests\\test_turn_pipeline_shared.py::test_chat_explicit_ooc_boundary_is_nonmutating_before_gameplay_pipeline tests\\test_turn_pipeline_shared.py::test_chat_active_target_location_question_routes_to_social_exchange tests\\test_pr_du_player_pipeline.py::test_pr_du_four_action_sequence_and_ooc_through_production_chat -q --tb=short --basetemp=codex_pytest_tmp_pr_eb_suite`
  - Result: 22 passed, 1 Starlette/httpx deprecation warning.
- `.\\.venv\\Scripts\\python.exe -m py_compile game\\conversational_orchestration.py game\\api.py tests\\test_pr_eb_conversational_continuity.py`
  - Result: passed.

Post-change broad comparison:
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_turn_pipeline_shared.py tests\\test_pr_du_player_pipeline.py tests\\test_pr_dq_ic_ooc_messages.py -q --tb=short --basetemp=codex_pytest_tmp_pr_eb_shared`
  - Result: failed with 26 failures.

Failure families:
- endpoint-specific no-resolution shape mismatch
- social/final-emission filler or stock phrase leakage
- dialogue reply kind and strict-social speaker contract mismatches
- targeted retry expectations not reached
- mixed action/adjudication metadata differences
- repeated social interruption/refusal progression defects

Classification:
- Focused PR-EB tests: resolved target behaviors.
- Broad failures: unclassified/residual because no exact pre-change rerun was captured before edits, though the family aligns with PR-EA's documented wider social/final-emission failures.
- New regression evidence in focused PR-EB surface: none observed.

## 10 - Remaining Issues

PR-EB limitations:
- No full topic stack.
- No general named-person pronoun knowledge resolver beyond active interlocutor routing and object inspection.
- Save/load tested through persisted session state, not an explicit reload scenario.
- Earlier narration reference recovery remains shallow.

PR-EC candidates:
- Conversation subject stack and topic-change metadata.
- Richer but still bounded prior-dialogue quote recovery.
- Movement-plus-social multi-intent negotiation.

PR-ED candidates:
- Live-provider measurements with real token and latency data.
- Broader social/final-emission regression repair.

## 11 - Final Recommendation

B - PR-EB ACCEPTED WITH LIMITATIONS.

The implementation demonstrates the core player-facing continuity improvements without expanding execution authority or adding mandatory provider calls. The remaining limitations are real but bounded, and the broad regression debt remains outside the coherent PR-EB surface.

## 12 - Changed-File Inventory

PR-EB modified or added:
- `game/conversational_orchestration.py` - context updates, active-dialogue follow-up routing, ambiguous-reference clarification, clarification continuation.
- `game/api.py` - persistence of bounded context updates and deterministic `EXECUTE` bridge handoff.
- `tests/test_pr_eb_conversational_continuity.py` - focused production-entry acceptance tests.
- `artifacts/pr_eb_conversational_continuity/REVIEW.md` - review evidence.
- `artifacts/pr_eb_conversational_continuity/changed_files.txt` - file inventory.
- `handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, `handoff/CURRENT_REVIEW.zip` - CURRENT_REVIEW package.

Workspace note: the repository already contained many modified and untracked files before PR-EB. They were not reverted or cleaned.
