"""Write the PR-PLAY-77 review reports from recorded evidence. No new gameplay."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "development" / "campaigns" / "product_realization" / "pr_play_77"
OUT.mkdir(parents=True, exist_ok=True)

reports = {}

reports["01_EXECUTIVE_SUMMARY.md"] = """# PR-PLAY-77 Executive Summary

Verdict: **B / PARTIAL**.

Ashen Thrones can execute a bounded sequence of up to three grounded actions through the existing physical adjudicator. Each eligible step is revalidated against the current ledger, legitimate consequences commit, and a later failure does not roll back an earlier success. Dependent steps stop. A genuinely independent later action may continue. The plan is an interpretation record. It is not authoritative state, and it does not resume by itself after save or reload.

Two-step and three-step execution were demonstrated on normal HTTP campaigns and in the typed browser. The three-step stone request moved the stone farther, declined the unconfigured climb, and did not attempt the elevated look. The stone stayed moved. Save, reload, and resume preserved that position. "continue" did not restart the unfinished plan.

One live provider proposal was accepted and executed by the host: "I push the crate aside and inspect it." The provider did not commit state. Two broader door proposals were rejected because they inserted an approach the player did not say. An earlier disagreement used 1 request and 264 tokens. Combined live usage is 4 requests and 1,037 tokens.

The frozen developer holdout ran once at 106/110. The four misses are noncritical wording and policy-versus-oracle cases. They were not retuned. That holdout gap, the still-unsupported climb, and limited carrying keep the verdict partial. Execution itself is safe: blocked looks were not narrated as success, read-only questions did not open or move objects, and no hidden information was published.

Protected repository files: 150/150 unchanged. Focused regression 1065 passed / 20 failed, boundary 101/6, broader 0/9, isolated lifecycle 39/39. Failure identities match PR-PLAY-75 and PR-PLAY-76. New regression identities: 0.

Recommended next cycle: PR-PLAY-78, open-ended player intent and narrative consequence integration. Do not start it in this closure.
"""

reports["02_REPOSITORY_BASELINE.md"] = """# Repository Baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD message: fix: restore clarification recency and resolve planner audit false positive
- No commit and no push in this cycle.

The working tree was already dirty with uncommitted PR-PLAY-55 through PR-PLAY-76 work. This cycle did not revert that work.

PR-PLAY-77 extended the existing physical adjudicator. It did not add a parallel action engine.

Files added or extended for this cycle:

- `game/physical_adjudication.py` (untracked since PR-PLAY-76; multi-step planning, dependencies, partial success, H93 phrase grounding, and provider-plan validation live here)
- `tests/test_pr_play_77_multistep.py`
- `tests/test_pr_play_77_holdout.py`
- `tests/test_pr_play_77_http.py`
- `artifacts/pr_play_77/` evidence, including the frozen holdout and the browser host
- `development/campaigns/product_realization/pr_play_77/`
- `docs/NEXT_SESSION.md` handoff prepended at closure

Governance read at the start of the cycle: `docs/DEVELOPMENT_CONSTITUTION.md` and `docs/NEXT_SESSION.md`. The handoff file still opened on the PR-PLAY-75 closure. The PR-PLAY-76 mission and reports were the operative baseline.
"""

reports["03_TEST_DATA_ISOLATION.md"] = """# Test-Data Isolation

Protected set recorded before edits: `artifacts/pr_play_77/protected_before.json`.

Recount after gameplay, tests, and regression:

- Compared: 150
- Changed: 0
- Missing: 0

Preservation count: **150/150**.

Pytest basetemp for this cycle stayed under `development/tmp/pr77_multistep` and `development/tmp/pr77_regression`. The isolation hook still refuses a pytest basetemp inside `artifacts/`.

The browser host used `artifacts/pr_play_77/browser_data` through the existing isolation install. Campaign storage, session storage, snapshots, and the browser network log were written there. Canonical `data/` was not the browser store.

`ASHEN_TEST_EVIDENCE_DIR` was used only for the earlier HTTP evidence write. The regression runner removed that variable before launching pytest.
"""

reports["04_MULTISTEP_ARCHITECTURE.md"] = """# Multi-Step Architecture

The path stays inside the existing owners:

1. Player text enters the initiative and controlled-improvisation request.
2. `plan_physical` interprets a bounded plan. The plan is proposed state only.
3. `commit_physical` walks eligible steps in order.
4. Each step calls the existing `_apply` path, which commits through the physical ledger.
5. The next step is planned again from the updated ledger.
6. `physical_plans` records statuses and sets `automatic_resume` false.
7. Player-facing text comes from the existing publication path.

The provider may propose an operation list. The host re-parses, compares the normalized operations with the deterministic plan, and adjudicates. A stamp is process-local. The provider does not write the ledger.

Combat blocks multi-step execution only. A single action is unchanged. No turn cost is invented. Multi-step play demonstrated here is noncombat exploration.

Statuses used: PROPOSED, READY, EXECUTING, SUCCEEDED, FAILED, BLOCKED, SKIPPED, UNSUPPORTED, CLARIFICATION.
"""

reports["05_ACTION_DECOMPOSITION.md"] = """# Action Decomposition

A request splits on sequential language: and, then, and then, semicolons, and comma-and forms when every piece is an action. The bound is three actions.

More than three meaningful actions asks for clarification and attempts nothing.

One action is not expanded into an autonomous plan. A consequential compound whose first clause is not an operation returns a refusal for that clause and states that the rest was not attempted.

Questions stay questions. "Can I move the crate, and is it heavy?" does not move the crate.

Compound traversal, gesture, and vantage inspection are recognized only when the request is compound, so a single "read the notice board" is not captured as a physical plan.

Development coverage: 120 tests in `tests/test_pr_play_77_multistep.py`, re-run after the provider alias and admission-message edits. Result: 120 passed.
"""

reports["06_PLAN_REPRESENTATION.md"] = """# Plan Representation

Each step carries an identifier, the player wording, a proposed action, a target reference, the intended outcome, explicit and inferred dependencies, preconditions, mechanical requirements, execution status, the authoritative result, a consequence reference when one exists, a failure reason, and publication status.

`physical_plans` stores the record on the ledger. A proposed plan is not published as a completed fact. Successful steps publish only the consequence the adjudicator committed.

"continue" and "resume the plan" do not execute leftover steps. The player must say the next action.
"""

reports["07_DEPENDENCY_MODEL.md"] = """# Dependency Model

Kinds distinguished in the planner:

- Explicit: "if the door opens", "if I am beside the notice board".
- Physical: move or open, then inspect what that change reveals.
- Target: the same grounded entity across steps.
- Positional: approach, then read.
- Mechanical: climb, then look from the new vantage.
- Independent: stand, greet, or wave when the later action does not need the earlier result.
- Uncertain: stop rather than guess.

Player order is kept. Adjacent actions are not treated as dependent merely because they share a sentence.

If the first step has no grounded target, later steps are not attempted. That preserves the earlier "open the hatch and sit" behavior when the hatch is not established.
"""

reports["08_SEQUENTIAL_EXECUTION.md"] = """# Sequential Execution

`commit_physical` re-reads authoritative state before each step. A successful earlier step can enable a later one. A failed or unsupported earlier step blocks dependents. A success can also invalidate a later assumption because the later step is checked against the new state.

Demonstrated order:

- Push the loose stone aside, then look where it was. Both steps ran. The stone is aside.
- Push the loose stone farther, climb the milestone, and look down the road. The push committed. The climb was unsupported. The look was not attempted.

Single travel wording still returns to the existing travel path. A multi-step sentence that contains a walk is not discarded as a whole.
"""

reports["09_PARTIAL_SUCCESS.md"] = """# Partial Success

Primary case, HTTP and browser:

Player: "I push the loose stone farther, climb the milestone, and look down the road."

Published result: the ordinary loose stone is farther aside from the stonework. The weathered milestone is here, but no climbing check is configured, so the climb is not resolved and the position is unchanged. A later part was not attempted because it depended on a step that did not succeed.

Authoritative result:

- Stone position: farther.
- Character elevation: unchanged.
- No invented road observation.
- The word "hidden" is absent from the publication.

The earlier aside move from the two-step request also remained. Later failure did not roll it back.
"""

reports["10_CONDITIONAL_AND_INDEPENDENT_ACTIONS.md"] = """# Conditional and Independent Actions

Conditional, before the character was beside the board:

"If I am beside the notice board, step back from it."

Result: "That condition is not met, so the later action was skipped. Nothing was changed."

The same sentence after a restored beside position: "You step back from the Notice board."

Independent sequence: "I stand up and approach the notice board." Result: already standing, then beside the notice board. The approach did not depend on the skipped step-back.

Policy: a grounded precondition failure continues into later steps only when every later step is independent and is an interact. Dependents of a failed or unsupported step are blocked. Uncertain later steps stop.

The frozen holdout expected a full stop on H068 and H089, where a refused door was followed by standing. The engine continued the independent stand and said the character was already standing. Those two oracle misses are preserved. The door stayed locked and closed.
"""

reports["11_TARGET_CONTINUITY.md"] = """# Target Continuity

"I push the loose stone aside and look where it was" resolves both steps to the same ordinary loose stone. The look does not create a second object.

"I push the crate aside and inspect it" on the live provider path likewise kept one oak crate and reported it aside.

Pronouns and "where it was" reuse the grounded id from the earlier step. Structural ids for posture, position, inspection, doorway, and vantage are not object ids.

Zero local seat matches are not a clarification. One match grounds. Several local matches ask which seat. A one-token alias such as the milestone alias "stone" does not claim "stone seat".
"""

reports["12_MECHANICAL_AND_TURN_BOUNDARIES.md"] = """# Mechanical and Turn Boundaries

Climbing the milestone has no configured check. The step is unsupported. No DC, modifier, roll, or success is invented. The dependent look is not attempted.

Existing authored checks remain the only dice path. This cycle did not add a Pathfinder turn economy. Multi-step execution is limited to noncombat exploration. Combat blocks the multi-step path and leaves single actions on their existing route.

No turn cost was fabricated for the two-step or three-step requests.
"""

reports["13_CONSEQUENCE_PERSISTENCE.md"] = """# Consequence Persistence

HTTP campaign A saved after the partial success, loaded that snapshot into a new campaign identity, and asked where the loose stone was. The answer still placed it farther aside. "continue" replied that no unfinished sequence resumes on its own.

Browser campaign A did the same through the Save Slots control, a page reload, and Load. "Where is the loose stone?" returned "The ordinary loose stone is farther aside from the stonework."

Browser campaign B saved after the character was beside the notice board, reloaded, loaded snapshot `2026-11-07T20-24-57_6c2a784b`, and was told "You are beside the Notice board." The following conditional then stepped back.

Completed consequences persisted. The blocked climb and the blocked look were not replayed by the load.
"""

reports["14_H93_REPAIR.md"] = """# H93 Repair

PR-PLAY-76 holdout H93 said "I sit on the bench" in a campaign with no local bench. A bench existed only in another campaign. The old result asked which seat.

The seat matcher now requires every token of the player's seat phrase to appear in the local seat name.

- Zero local matches: not established. Category E. Posture unchanged. No object created. No other campaign is read.
- One local match: grounded.
- Several local matches: clarification.

Generic "sit down" with one local seat still sits. Several local seats still ask which seat.

The PR-PLAY-76 frozen manifest was not edited. During implementation that frozen holdout was re-run and H93 published that the seat is not established. This cycle's development matrix includes the missing-target regression. The PR-PLAY-77 frozen file was not used to retune that repair.
"""

reports["15_PROVIDER_ASSISTED_PLANNING.md"] = """# Provider-Assisted Planning

Live model: `gpt-4.1-mini`. Purpose: `physical_plan`. Owner: `physical_adjudication`.

| Call | Utterance | Result | Tokens | Latency |
| --- | --- | --- | --- | --- |
| 1 | Earlier door-and-look wording | Rejected, deterministic disagreement | 264 | 2253 ms |
| 2 | "I open the door and look inside." | Rejected. Proposal added approach, open, and inspect. | 264 | 1479 ms |
| 3 | "Open the door, then check inside." | Rejected for the same extra approach. | 264 | 835 ms |
| 4 | "I push the crate aside and inspect it." | Accepted. Host executed. | 245 | 1255 ms |

Totals: 4 requests, 1,037 tokens, 0 retries. Budget ceiling was 8 requests and 16,000 tokens.

Accepted publication: "You push the oak crate. It is now aside from where it was. The oak crate is aside from where it was."

`committed_by_provider` is false. The second process could not reuse the first usage ledger because admission opens that file exclusively. The accepted run used a fresh ledger at `artifacts/pr_play_77/provider_live_run`.

The browser host had provider calls disabled. Browser success is deterministic and is not counted as a live provider success.
"""

reports["16_PLAYER_SAFE_PUBLICATION.md"] = """# Player-Safe Publication

Player text distinguishes completed, skipped, unsupported, and unattempted actions.

Examples retained verbatim:

- "That condition is not met, so the later action was skipped. Nothing was changed."
- "The Weathered milestone is here, but no climbing check is configured, so the climb is not resolved and your position is unchanged. A later part was not attempted, because it depended on a step that did not succeed."
- "No unfinished sequence resumes on its own. Say the next action you want. Nothing further was attempted."
- "Nothing on the other side is established, and nothing was opened or moved."

A scan of browser `player_facing` text found no GM-only markers, hidden-fact labels, internal plan dumps, or provider proposals.

Rejected provider plans were not shown to the player. The accepted crate sentence published only the committed push and the inspection of that same object.
"""

reports["17_DEVELOPMENT_TESTS.md"] = """# Development Tests

File: `tests/test_pr_play_77_multistep.py`.

Re-run after the provider alias map and the admission error change:

`py -3 -m pytest tests/test_pr_play_77_multistep.py --tb=line -q --basetemp=development/tmp/pr77_multistep`

Result: 120 passed, exit code 0, elapsed about 3.5 seconds.

The matrix covers single-action preservation, two- and three-step decomposition, the more-than-three clarification, conditionals, shared targets, dependency kinds, partial success, blocked and skipped and unsupported steps, read-only compounds, H93 missing targets, save and resume without automatic continuation, provider accept and reject paths, and isolation. Deferred features were not marked passing. Climb stays unsupported in the tests that exercise it.
"""

reports["18_FROZEN_HOLDOUT.md"] = """# Frozen Holdout

This is a developer-authored holdout. It is not external validation.

- File: `artifacts/pr_play_77/frozen_holdout.json`
- Cases: 110
- Hash: `556191b095698ead786b1feb9860ffd86c93f957378418ad7e7d302cae3d5fad`
- Official one-pass result: 106 passed, 4 failed
- Multi-turn cases in the manifest: 70
- Save/resume cases: 20
- The manifest was not edited after the run.

Retained failures:

- H017. "Heave the cup and set the cup aside." The cup was lifted. "Set aside" is not the place pattern, so the second step was not established. The lift remained.
- H068. A guarded door was refused and the independent stand continued. The door was unchanged. The oracle expected a full stop.
- H073. "I sit on the bench and stand up." succeeded with "You sit on the wooden bench. You stand." The oracle fragment looked for the word "standing".
- H089. "I open the locked door and stand up." The door stayed locked and closed. The independent stand produced category A. The oracle expected category D.

No safety defect was identified in those four. They were not repaired against the frozen file.
"""

reports["19_REAL_HTTP_GAMEPLAY.md"] = """# Real HTTP Gameplay

Harness: `tests/test_pr_play_77_http.py` using `TestClient` against the normal campaign routes. No developer-only seed API.

Campaign A, survey branch:

- Established a small loose stone by asking whether one could be shifted. It had not been moved.
- "I push the loose stone aside and look where it was." Both consequences published. Elapsed 306.8 ms.
- "I push the loose stone farther, climb the milestone, and look down the road." Farther, no climbing check, look not attempted, not elevated. Elapsed 792.0 ms.
- Snapshot, new campaign, load. "Where is the loose stone?" still farther. "continue" did not resume the plan.

Campaign B, report branch:

- Conditional step-back skipped. Position unchanged. Elapsed 42.9 ms.
- "I stand up and approach the notice board." Beside the board. Elapsed 839.7 ms.
- "Is the notice board here, and what is on the hidden side?" did not approach again, did not add clues, and did not change position or flags. Elapsed 43.6 ms.
- Snapshot, load. Beside persisted. The same conditional then stepped back. Elapsed 908.1 ms.

All ten measured chat turns: mean 364.25 ms, median 175.2 ms, maximum 908.1 ms. HTTP 200 was not the acceptance check. State and publication assertions passed.
"""

reports["20_BROWSER_GAMEPLAY.md"] = """# Browser Gameplay

Host: `artifacts/pr_play_77/runtime.py` on `http://127.0.0.1:8091/`. Provider calls disabled on this host. Network log: `artifacts/pr_play_77/browser_network.jsonl`.

Campaign A, typed in the chat composer:

- New Campaign, Start Campaign, examine the notice board, follow the rumor, examine the milestone.
- Survey the uncertain trail yourself. Record the limits of your survey.
- "Is there a small loose stone I could shift aside?"
- "I push the loose stone aside and look where it was."
- "I push the loose stone farther, climb the milestone, and look down the road."
- Create Snapshot labeled partial. Reload. Load. "Where is the loose stone?" The stone was farther aside. "continue" did not resume the plan.

Screenshot: `artifacts/pr_play_77/screenshots/browser_a_partial.png` shows the partial-success narration at Old Milestone.

Campaign B:

- New Campaign, Start, the same investigation, Return to report the uncertain trail, return to the gate, Give the watch your patrol report.
- Conditional step-back skipped.
- "I stand up and approach the notice board." Beside the board.
- "Is the notice board here, and what is on the hidden side?" Nothing on the other side was established, and nothing was opened or moved.
- Those two requests overlapped in the page script. The read-only response completed before the stand response. The read-only text still reported no mutation. The stand then committed beside.
- Snapshot `beside-after` was taken after that stand. Reload and Load restored beside. "Am I beside the notice board?" yes. The conditional then stepped back.

Screenshot: `artifacts/pr_play_77/screenshots/browser_b_resume.png`.

Browser chat requests: 19. Server-side mean 551.42 ms, median 424.55 ms, maximum 1683.87 ms. Authored action clicks: 4, mean 252.63 ms, maximum 305.26 ms. Paint time was not instrumented. Browser success is not inferred from the HTTP suite.
"""

reports["21_REGRESSION_RESULTS.md"] = """# Regression Results

Runner: `artifacts/pr_play_77/run_regression.py`.

Baselines: `development/tmp/pr77_regression`. Provider calls disabled. Evidence-dir variable cleared.

| Lane | Passed | Failed | Identity delta vs PR-PLAY-75 |
| --- | --- | --- | --- |
| Focused | 1065 | 20 | none |
| Boundary | 101 | 6 | none |
| Broader | 0 | 9 | none |
| Isolated lifecycle | 39 | 0 | none |

The 20 focused, 6 boundary, and 9 broader failures are the same identities as PR-PLAY-75 and PR-PLAY-76. They are historical. New regression count: 0.

Isolated lifecycle remains 39/39, including persistence recovery and the PR-PLAY-71V verification file.
"""

reports["22_LATENCY_AND_PROVIDER_USAGE.md"] = """# Latency and Provider Usage

Deterministic HTTP, ten campaign turns:

- Mean 364.25 ms
- Median 175.2 ms
- Maximum 908.1 ms

Selected HTTP steps:

- Two-step push and look: 306.8 ms
- Three-step partial success: 792.0 ms
- Conditional skip: 42.9 ms
- Independent stand and approach: 839.7 ms
- Read-only compound: 43.6 ms
- Resumed state question: 40.7 ms
- Conditional after resume: 908.1 ms

Browser server time, 19 chat posts: mean 551.42 ms, median 424.55 ms, maximum 1683.87 ms. The maximum is the stand-and-approach request. Paint time was not captured.

Provider, measured separately:

- 4 requests
- 1,037 tokens
- 0 retries
- 1 plan accepted and executed by the host
- 3 plans rejected
- Latencies 2253 ms, 1479 ms, 835 ms, and 1255 ms

Provider time is not folded into the deterministic HTTP mean.
"""

reports["23_LIMITATIONS_AND_OPEN_RISKS.md"] = """# Limitations and Open Risks

- The frozen holdout is 106/110. H017 does not treat "set aside" as place. H068 and H089 continue an independent stand after a refused door. H073 says "You stand." rather than the oracle's "standing".
- Climbing remains unsupported wherever no check is configured.
- Inventory and carrying remain limited.
- Live NPC dialogue was not expanded in this cycle.
- The provider accepted one shared-target physical plan. It rejected door plans that added an unstated approach. Broader live wording is still narrow.
- A browser script overlapped the campaign B read-only question with the stand request. The engine answered each request from the state it saw. The final snapshot was taken after the stand committed.
- Multi-step execution is noncombat exploration. There is no invented action economy.
- Browser paint latency is not instrumented.
- The working tree contains extensive uncommitted work from earlier cycles. This closure does not commit it.
"""

reports["24_NEXT_SESSION.md"] = """# Next Session

Verdict remains **B / PARTIAL**. Multi-step execution is safe. Partial success persists. Dependencies are respected. Authoritative consequences survive save and resume. The remaining gaps are noncritical.

Proceed to PR-PLAY-78: open-ended player intent and narrative consequence integration.

Goal: connect bounded action execution to broader narrative interpretation, so the AI-DM can answer player initiative coherently without inventing unauthorized world facts or bypassing mechanics.

Do not implement PR-PLAY-78 in the PR-PLAY-77 closure.

Do not open another stabilization cycle only because climbing is unavailable, inventory is limited, NPC dialogue is shallow, provider latency varies, or the historical 20/6/9 regression failures remain.

Do not edit `artifacts/pr_play_77/frozen_holdout.json`. Do not commit or push without authorization.
"""

for name, text in reports.items():
    (OUT / name).write_text(text, encoding="utf-8")
print(len(reports), OUT)
