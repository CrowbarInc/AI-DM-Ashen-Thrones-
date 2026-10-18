# PR-EA — Conversational Orchestration Foundation

## 01 — Executive Summary

PR-EA adds a production-integrated conversational decision boundary before `/api/chat` commits to turn advancement, world ticks, clocks, parser fallback, or resolver execution.

Changed:
- Added `game/conversational_orchestration.py` with an inspectable `ConversationalDecision` envelope and explicit categories: `ANSWER`, `CLARIFY`, `DECLINE`, `EXECUTE`, and `PLAN`.
- Routed `/api/chat` through deterministic conversational decisions before mutation.
- Routed stored and live interpretation records through the decision layer before bridge validation.
- Preserved the existing interpretation bridge as the executable-operation gate.
- Added focused PR-EA tests for decision contract, non-mutating answers, focused clarification, and existing resolver handoff.

Now works:
- Incomplete movement such as `I leave.` produces `Where are you trying to go?` without advancing turn counter, clocks, world ticks, or resolver state.
- Unmarked OOC/interface help such as `How do I save the game?` receives a non-mutating answer without provider calls.
- Stored primary-intent-plus-incidental-context turns can execute the single authoritative component while retaining incidental context in the decision envelope.
- Live interpretation bridge rejections for missing movement targets produce focused clarification.

Incomplete:
- Full conversational reference resolution remains deferred to PR-EB.
- Live provider schema still rejects some incidental operation classes before PR-EA can classify them; stored/replay records can demonstrate the architectural behavior.
- Broad social/final-emission regressions remain present in the wider dirty worktree and are not repaired by PR-EA.

Production integration: yes. Actual `/api/chat` reaches the new decision layer at `game/api.py:5951` before turn advancement and resolver selection.

## 02 — Architecture Before and After

Before PR-EA:
Browser chat -> `/api/chat` -> mode handling -> optional live interpretation -> interpretation bridge -> semantic ownership/resolver selection -> authoritative execution or narration -> validation -> persistence.

After PR-EA:
Browser chat -> `/api/chat` -> mode handling -> load current state -> conversational decision -> non-mutating response or existing executable bridge -> semantic ownership/resolver selection -> authoritative execution or narration -> validation -> persistence.

New entry point:
- `deterministic_conversational_decision()` at `game/conversational_orchestration.py:161`
- `decision_from_interpretation_record()` at `game/conversational_orchestration.py:255`
- production call site at `game/api.py:5951`

Authority boundaries preserved:
- PR-EA does not decide action success.
- PR-EA does not mutate world state.
- PR-EA does not invent targets or undiscovered facts.
- EXECUTE still requires the existing bridge and resolver path.

## 03 — Decision Contract

Implemented representation: `ConversationalDecision`.

Fields:
- `category`
- `primary_intention`
- `intent_family`
- `incidental_context`
- `proposed_operation`
- `proposed_target`
- `proposed_record`
- `missing_information`
- `context_references`
- `requires_authoritative_execution`
- `reason`
- `confidence`
- `ambiguity`
- `player_facing_text`

Invariants:
- `EXECUTE` means the turn still requires authoritative bridge/resolver validation.
- `ANSWER`, `CLARIFY`, `DECLINE`, and `PLAN` are non-mutating in PR-EA.
- `proposed_record` is only a handoff shape for existing executable infrastructure.
- Incidental context may be recorded but does not authorize multi-action execution.

Examples:
- `I leave.` -> `CLARIFY`, missing `destination`.
- `How do I save the game?` -> `ANSWER`, no provider call.
- stored `THANK + MOVE(gate)` -> `EXECUTE`, primary `MOVE`, incidental `Thank Sergeant Mara.`
- live `MOVE` without target -> `CLARIFY`, missing `destination`.

Known limitations:
- Recent-context answers are intentionally shallow and conservative.
- Provider-live incidental classifications remain constrained by the upstream PR-DR schema.
- PLAN is represented but not integrated into autonomous multi-step execution.

## 04 — Production Integration Evidence

Source references:
- Decision model: `game/conversational_orchestration.py:16`, `game/conversational_orchestration.py:25`
- Deterministic non-mutating decisions: `game/conversational_orchestration.py:161`
- Interpretation-record decision adaptation: `game/conversational_orchestration.py:255`
- Bridge rejection adaptation: `game/conversational_orchestration.py:359`
- Non-mutating response helper: `game/api.py:729`
- `/api/chat` deterministic decision call: `game/api.py:5951`
- Stored interpretation decision call: `game/api.py:5967`
- Live interpretation decision call: `game/api.py:6007` and `game/api.py:6045`

Executable operations still reach existing resolvers:
- `test_pr_ea_stored_incidental_plus_move_executes_existing_authoritative_resolver` verifies stored incidental-plus-move routes to the existing bridge/resolver and increments `turn_counter`.

Non-mutating responses avoid unintended state changes:
- `test_pr_ea_incomplete_movement_does_not_advance_turn_or_clock`
- `test_pr_ea_unmarked_ooc_help_question_is_nonmutating_without_provider`
- `test_pr_ea_live_missing_move_target_uses_focused_clarification`

## 05 — Behavioral Acceptance Results

1. Start a new campaign — PARTIAL. Existing start campaign path preserved; not newly behaviorally revalidated in PR-EA.
2. Ask a contextual question — PARTIAL. Deterministic visible/recent context answers exist; full reference resolution deferred.
3. Continue an NPC conversation — PARTIAL. Existing resolver path preserved; broad social failures remain inherited.
4. Ask an unmarked OOC question — PASS. `How do I save the game?` returns a non-mutating answer without provider calls.
5. Leave an NPC conversation — PARTIAL. Incomplete movement clarifies; explicit social-focus loosening is not completed.
6. Express incomplete movement — PASS. `I leave.` asks for destination without mutation.
7. Inspect a valid target — PASS via existing PR-DY/PR-DU coverage; executable route preserved.
8. Repeat a previous inspection — DEFERRED. Existing behavior not expanded in PR-EA.
9. Attempt a plausible creative action — PARTIAL. EXECUTE/CLARIFY vocabulary exists; broad creative handling remains existing resolver responsibility.
10. Attempt an impossible action — PARTIAL. Deterministic decline exists for narrow impossible patterns; comprehensive impossibility remains resolver-owned.
11. Ask about an earlier narration detail — PARTIAL. Conservative recent-log answer exists; PR-EB should implement full reference resolution.
12. Resume a saved conversation — DEFERRED. Save/load compatibility not knowingly broken; no new resume behavior verified.

## 06 — Authority and Persistence Audit

Permitted mutations:
- Conversation log append for non-mutating conversational responses.
- Existing resolver mutations after `EXECUTE` passes bridge validation.

Prevented mutations:
- Non-mutating decisions do not increment `turn_counter`.
- Non-mutating decisions do not advance `time_pressure`.
- Non-mutating decisions do not call `advance_world_tick`.
- Non-mutating decisions do not call narration provider.
- Non-mutating decisions do not change active scene, inventory, world, combat, or clues in tested cases.

Resolver ownership:
- Exploration/social/adjudication ownership remains unchanged.
- `normalized_action_from_interpretation()` remains the executable bridge.

Save/load implications:
- No schema migration required.
- Conversation log entries now may include `resolution.metadata.conversational_decision`.

Authority violations discovered:
- None in the targeted PR-EA test slice.

## 07 — Performance Comparison

Measured targeted results:
- Incomplete movement: 0 interpretation requests, 0 narration requests, no resolver.
- Unmarked OOC/interface help: 0 interpretation requests, 0 narration requests, no resolver.
- Live missing movement target: 1 interpretation request, 0 narration requests, no resolver.
- Stored incidental-plus-move: 0 interpretation requests, existing narration/resolver path used.

Baseline comparison:
- PR-DZ recorded no new live latency measurements.
- PR-EA does not add an unavoidable provider call to every turn.
- Deterministic non-mutating cases reduce provider/resolver work compared with the old fall-through path.

Token usage:
- Provider-disabled deterministic tests use no tokens.
- Live interpretation tests use stubbed usage records only.

Retry behavior:
- PR-EA does not add retry behavior.

## 08 — Regression Results

Commands executed:
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ea_conversational_orchestration.py tests\\test_pr_dy_live_gameplay.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ea`
  - Result: 16 passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ea_conversational_orchestration.py tests\\test_pr_dy_live_gameplay.py tests\\test_pr_du_player_pipeline.py::test_pr_dv_rejected_and_ambiguous_stored_interpretations_do_not_fallback_execute tests\\test_turn_pipeline_shared.py::test_chat_covert_concealment_under_observation_prompts_engine_check -q --tb=short --basetemp=codex_pytest_tmp_pr_ea_fix`
  - Result: 18 passed, 1 warning.
- `.\\.venv\\Scripts\\python.exe -m py_compile game\\conversational_orchestration.py game\\api.py`
  - Result: passed.
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_turn_pipeline_shared.py tests\\test_pr_du_player_pipeline.py tests\\test_pr_dq_ic_ooc_messages.py -q --tb=short --basetemp=codex_pytest_tmp_pr_ea_shared`
  - Result: failed with 27 failures.

New regressions fixed during PR-EA:
- Unmarked action-conditioned roll question was too broadly classified as OOC help.
- Stored rejected interpretation changed legacy response shape.

Inherited/broader failures observed:
- Social dialogue/final-emission tests in `tests/test_turn_pipeline_shared.py` still fail on existing dialogue contract, retry, sanitizer, and speaker-grounding surfaces.
- These failures align with PR-DZ's inherited regression-debt cluster and were not repaired in PR-EA.

Tests added:
- `tests/test_pr_ea_conversational_orchestration.py`

## 09 — Remaining Issues

High impact PR-EA limitation:
- Live provider schema cannot carry unknown incidental operation classes such as `THANK` before adaptation rejects them. The decision layer supports the distinction, but live-schema expansion belongs in a follow-up.

PR-EB candidates:
- Full conversational reference resolution.
- Better grounding for earlier narration details and pronouns.
- NPC dialogue continuity through conversational decisions.

PR-EC candidates:
- Movement/partial-intent expansion and social-focus leaving behavior.

PR-ED candidates:
- Live latency and provider-budget measurement across representative real turns.
- Reducing sequential interpretation/narration cost.

Unrelated technical debt:
- Broad social exchange emission failures in the existing dirty worktree.
- Existing final-emission sanitizer and speaker-contract regressions.

## 10 — Final Recommendation

B — PR-EA ACCEPTED WITH LIMITATIONS

Evidence:
- The production chat path reaches the conversational decision layer before authoritative mutation.
- Non-mutating answer/clarify paths are represented and tested.
- Focused clarification works for missing movement destination.
- EXECUTE still passes through existing bridge/resolver authority.
- The architecture does not require an added provider call for every turn.

Limitations:
- Full player-facing conversational completeness is not achieved.
- Several acceptance scenarios are partial or deferred.
- Broad inherited social/final-emission failures remain unresolved.

## Changed-File Inventory

PR-EA touched:
- `game/conversational_orchestration.py`
- `game/api.py`
- `tests/test_pr_ea_conversational_orchestration.py`
- `artifacts/pr_ea_conversational_orchestration/REVIEW.md`
- `artifacts/pr_ea_conversational_orchestration/changed_files.txt`
- `handoff/CURRENT_REVIEW.md`
- `handoff/REVIEW_MANIFEST.json`
- `handoff/CURRENT_REVIEW.zip`

The worktree had many pre-existing modified and untracked files before PR-EA. They were not reverted or cleaned.
