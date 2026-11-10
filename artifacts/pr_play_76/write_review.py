"""Write the PR-PLAY-76 evidence reports from recorded results. Does not invent missing runs."""
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "development" / "campaigns" / "product_realization" / "pr_play_76"
ART = ROOT / "artifacts" / "pr_play_76"
OUT.mkdir(parents=True, exist_ok=True)

reports = {}

reports["01_EXECUTIVE_SUMMARY.md"] = """# PR-PLAY-76 Executive Summary

Verdict: **B / PARTIAL**.

Ashen Thrones can resolve ordinary physical actions from natural language when the target is grounded and its relevant properties are already established. The pathway reuses initiative, controlled facts, skill checks, the world-fact ledger, and player-safe publication. It does not replace authored action resolution.

Four or more operations work: sit, stand, open, close, push, pull, move, lift, approach, and retreat. Persistent consequence families include object position, open/closed state, character posture, and character position beside or back from a target. Routine cases commit without a roll. Mechanical uncertainty is recognized. An authored skill check is rolled only when the object already carries a skill id and an integer DC. Missing mechanics, including the unconfigured climb onto broken stonework, are declined. No DC, modifier, roll, or success is invented.

Both normal HTTP campaigns passed. Both browser campaigns passed with typed chat, a snapshot, a reload, a resume, and a later state question. Protected files remained 150/150. Focused regression failures are the same 20 identities recorded for PR-PLAY-75. Isolated lifecycle remained 39/39. Hidden-information exposures observed: 0.

The frozen holdout completed 99/100. Case H93 asked which seat when the named bench belonged to another campaign and no seat was visible. Nothing was mutated. That noncritical classification miss, together with deferred carrying and the unsupported unconfigured climb, keeps the verdict at partial rather than a full pass.

Recommended next cycle: PR-PLAY-77, multi-step player intent and consequence-aware planning.
"""

reports["02_REPOSITORY_BASELINE.md"] = """# Repository Baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD message: fix: restore clarification recency and resolve planner audit false positive
- No commit and no push were made.

The working tree already contained unrelated uncommitted files before this cycle. Those files were left in place. This cycle owns:

- `game/physical_adjudication.py` (new)
- physical planning and commit hooks in `game/bounded_improvisation.py`
- the routine-turn extension in `game/api.py` so physical routines do not advance the world clock
- `tests/test_pr_play_76_physical.py`
- `tests/test_pr_play_76_matrix.py`
- `tests/test_pr_play_76_holdout.py`
- `tests/test_pr_play_76_http_trace.py`
- evidence under `artifacts/pr_play_76/`

The pathway is the existing one: player initiative calls `controlled_request`, which calls `plan_physical` when `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION=1` and the controlled-improvisation gates are on. `resolve_controlled_fact` calls `commit_physical` only for an interact plan. Flag off leaves the previous seat path and general-purpose actions unchanged.
"""

reports["03_TEST_DATA_ISOLATION.md"] = """# Test-Data Isolation

Protected repository data is `data/`. `tests/conftest.py` installs `tests/helpers/storage_isolation.py` before game imports. Campaign, session, save, provider-log, and pytest storage stay outside `data/`.

Protected hashes were recorded in `artifacts/pr_play_76/protected_before.json` before edits and checked again after the campaigns.

- Protected files: 150
- Matching after the cycle: 150
- Missing: 0
- Differing: 0

No protected file was restored silently because none changed. HTTP traces wrote under `artifacts/pr_play_76/http/` through the evidence-directory exception. The browser host used `artifacts/pr_play_76/browser_data`, created by the same isolation helper.
"""

reports["04_ACTION_ARCHITECTURE.md"] = """# Action Architecture

```
player text
  -> plan_physical
  -> intent / operation
  -> target grounding
  -> current ledger and scene objects
  -> category A-F
  -> preconditions
  -> mechanical requirement, only from an authored skill_check
  -> commit_physical
  -> ledger consequence
  -> engine_publication
```

The provider is not on this path for routine wording. `interpret_with_provider` can propose an operation and a target reference. It cannot roll, set a DC, declare success, or write the ledger. The host re-parses the player text at commit time and refuses a plan whose id does not match.

Read-only questions use the existing ledger and do not create ledger keys. Writes go through the existing session save. A failed session write in the HTTP rollback test left the prior bytes unchanged.
"""

reports["05_ACTION_CLASSIFICATION.md"] = """# Action Classification

| Category | Meaning | Observed behavior |
| --- | --- | --- |
| A | Routine | Sit, stand, open, close, push, pull, move, lift of a light movable object, approach, retreat |
| B | Mechanically uncertain | Authored skill check, or a heavy movable object with no strength mechanic |
| C | Consequential | Break, steal, guarded, owned, or restricted targets are declined |
| D | Unsupported | Missing mechanic, unknown open or lock state, deferred carrying |
| E | Impossible | Missing, inaccessible, immovable, invalid destination, teleport through a wall |
| F | Ambiguous | Two matching names, or two seats with no unique name |

Classification is property-based. A crate is not treated as light, a door is not treated as unlocked, and a stone is not treated as movable unless those properties are established.
"""

reports["06_OBJECT_AFFORDANCES.md"] = """# Object Affordances

Objects come from accepted controlled facts in the active campaign and scene, plus visible interactables. A ledger overlay stores open state and position so authored scene JSON is not rewritten.

Properties that are consulted when present: accessible, visible, mobility, weight, openable, locked, open, obstructed, obstructs, use, ownership, consequential, skill_check, position.

Unknown consequential properties are not guessed. The only low-impact improvisation in this cycle is a small loose stone, and only when the player asks whether a small loose stone is present and the scene already has a public stone or stonework fact. Its properties are fixed by the engine: small, light, movable, accessible, visible, beside the stonework. A painted or negated stone fact does not qualify. The notice board can be approached. It is not treated as openable.
"""

reports["07_ROUTINE_ACTION_RESOLUTION.md"] = """# Routine Action Resolution

A routine action commits without a roll when the target exists, is grounded, is accessible and visible, the needed properties are explicit, no authored check is configured, and no consequential restriction applies.

Demonstrated without a check:

- Sit on an accessible seat, including a non-stone bench.
- Stand.
- Open an unlocked, unobstructed door whose open state is known.
- Close that door.
- Approach a visible object.
- Step back from it.

Already-seated and already-open states do not add a second consequence. Questions such as "Can I move the crate?" answer and do not move it.
"""

reports["08_OBJECT_MANIPULATION.md"] = """# Object Manipulation

Push, pull, and move require mobility `movable`. An immovable target is category E. Unknown mobility is category D. Weight other than `light` is category B and is not lifted, because the character has no strength-check owner.

A successful push updates position. "Away from the doorway" clears an obstruction only when the object already obstructs a doorway or its position says it is blocking one. Otherwise the engine says no doorway obstruction is established and does not claim the doorway is clear.

"Farther" extends the current aside position and then stays idempotent. Pronouns use the physical focus set by the last committed object action.

Lift of an explicitly light movable object sets position to "raised in place". It does not enter inventory. Place works only from that raised position. Take and drop are deferred because ordinary carrying has no safe owner.
"""

reports["09_MECHANICAL_UNCERTAINTY.md"] = """# Mechanical Uncertainty

`game.skill_checks.resolve_skill_check` is used only when `properties.skill_check` has a skill id and an integer DC. Boolean DCs are rejected. The seed uses turn, scene, target, skill, and DC. A DC of 30 with modifier 0 fails. A DC of 1 succeeds. The publication includes the roll only when a roll happened. `skill_check` is omitted from the result when no roll occurred.

A heavy movable object with no authored check returns category B and states that no strength check is configured. Nothing is lifted. No DC is hardcoded to force a demonstration.
"""

reports["10_CLIMBING_INVESTIGATION.md"] = """# Climbing Investigation

Player line: "I climb onto the broken stonework to get a better view of the road."

The character skills are knowledge (arcana), spellcraft, perception, sense motive, stealth, diplomacy, intimidate, and bluff. There is no climb skill and no authored climb DC on the gate or milestone stonework.

With the physical flag on, that line is category D or E. In the live gate campaign the feature is not established, so the position is unchanged and no elevated vantage is created. If a test object carries an explicit climb check, the existing skill-check function rolls it. Success records a ledger position of kind `elevated` and says no additional view is established. It does not set scene-state elevation, which would unlock general-purpose observation views.

The safe unsupported outcome is the live result. Other physical actions still succeed.
"""

reports["11_CONSEQUENCE_MODEL.md"] = """# Consequence Model

Each successful state change appends one ledger item under `physical_consequences`:

- id `pc_` plus a hash
- target id
- action
- prior state
- resulting state
- campaign id
- scene id
- turn
- provenance `physical_adjudication`

An identical prior and result does not add another item. Posture and character position live on the ledger. Open state and object position live on the fact or the overlay. Narration is copied from `engine_publication` and is not a separate state write.
"""

reports["12_CONSEQUENCE_CONTINUITY.md"] = """# Consequence Continuity

Development and HTTP sequences:

1. Open a door, ask whether it is open, close it, save, reload, ask again, open it again.
2. Push the loose stone aside, ask whether it is still beside the stonework, push it farther, snapshot, start another campaign, load the snapshot, ask where it is.
3. Approach the notice board, ask whether the character is beside it, snapshot, reload, ask again, step back.

The reloaded answers used the stored position. The original "beside the stonework" and "not yet moved" text was not regenerated after the push. World flags on the survey branch stayed unchanged across the routine pushes.
"""

reports["13_REFERENCE_AND_TARGET_GROUNDING.md"] = """# Reference and Target Grounding

Named targets match a token subset of the label or aliases. The highest token count wins. A tie asks which object is meant. Pronouns use `physical_focus`, otherwise the only object. Sit prefers objects whose use is `seat`, so "sit on it" can reach the only seat.

No match does not create an object, except the explicit loose-stone question described in the affordance report. Hidden interactables are skipped and their hidden notes are not published. An inaccessible seat is refused. Objects from another campaign or scene are not visible.
"""

reports["14_COMPOUND_ACTIONS.md"] = """# Compound Actions

Utterances split on "and then", "and", or "then", with a maximum of two clauses. Each clause is classified on its own text.

If either clause is ambiguous, nothing is attempted. If the first clause is not an interact action, the rest is not attempted. If the first succeeds and the second fails, the first consequence remains and the publication says the earlier part stands and the rest was not carried out.

Demonstrated: open a door and look inside, with no invented room or contents; push a crate away from a doorway and then check that doorway; lift a cup and place it aside. "Look inside" and "check the doorway" are inspections. They do not discover clues, passages, or contents.
"""

reports["15_READ_ONLY_AND_FAILURE_SAFETY.md"] = """# Read-Only and Failure Safety

"Is the door open?", "Can I move the crate?", and "Am I beside the notice board?" do not commit the corresponding action. They do not change posture, position, open state, or inventory.

Failed or refused actions leave no successful consequence:

- missing target
- ambiguous target
- inaccessible target
- locked or obstructed door
- immovable target
- missing mechanic
- failed authored check
- invalid destination, including through a wall
- deferred take, drop, and place-from-inventory
- consequential break or steal

The HTTP test that injects a session-write failure returns HTTP 500, does not publish the success sentence, and leaves the prior session bytes unchanged.
"""

reports["16_PROVIDER_INTERPRETATION.md"] = """# Provider Interpretation

`validate_provider_interpretation` accepts only an operation and a target reference that the host can already ground. Extra fields, invented targets, hidden sentinels, and an operation that disagrees with the deterministic parse are rejected. There is no retry. The proposal does not commit.

Live campaigns used deterministic wording. `ASHEN_PHYSICAL_PROVIDER` was off on the browser host, and the HTTP trace disabled provider calls. Live physical provider requests: 0. Live provider tokens: 0. The unit tests cover malformed, timeout, disagreement, and candidate acceptance with a stub. Those stubs are not counted as live traffic.
"""

reports["17_DEVELOPMENT_TESTS.md"] = """# Development Tests

`tests/test_pr_play_76_physical.py` and `tests/test_pr_play_76_matrix.py` were run together after the last expectation correction.

- Result: 121 passed, 0 failed.
- Physical file: 55 cases, including both HTTP campaign branches and the failed-write rollback.
- Matrix file: 66 parametrized cases, M00 through M65.

Deferred take, drop, and unheld place are asserted as refusals. They are not counted as working inventory operations. The matrix case "I place the cup down." expects the carrying refusal. The matrix case "Can I unlatch the door?" on a locked door expects a locked refusal and no open state change.
"""

reports["18_FROZEN_HOLDOUT.md"] = """# Frozen Holdout

Manifest: `artifacts/pr_play_76/frozen_holdout.json`

- Cases: 100
- SHA-256: `23376bbe834138b4f5735d1917dcff4c55bdacca6c0d88d74c4b7b77b1410026`
- Multi-turn cases: 31
- Save/resume cases: 15
- Groups: 20 routine, 15 manipulation, 15 persistence, 10 mechanical, 10 ambiguity, 10 compound, 10 save, 5 isolation, 5 publication

The manifest was hashed before the run and the test asserts that hash. It was not edited after the run.

Result: 99 passed, 1 failed.

H93, isolation, input "I sit on the bench." after the bench's campaign was no longer active. Expected category E, "not established". Actual category F, "Which seat do you mean? Nothing has been attempted." The other campaign's bench was not named and was not mutated. The miss is that zero visible seats are clarified instead of declined. The original result is preserved in `artifacts/pr_play_76/holdout_results.json`. The code was not tuned against this case.
"""

reports["19_REAL_HTTP_GAMEPLAY.md"] = """# Real HTTP Gameplay

Both campaigns used `POST /api/new_campaign`, `POST /api/start_campaign`, typed `/api/chat`, and the authored survey or report actions. They were not seeded through a developer-only state API. Provider calls were disabled. The opening used the existing offline fixture.

## Campaign A — survey

- Asked whether a small loose stone could be shifted. The engine established an ordinary light stone beside the stonework.
- "I push the loose stone aside." Position became aside from the stonework.
- "Is the loose stone still beside the stonework?" Answered from the new position.
- "I push it farther." Position became farther aside from the stonework. World flags did not change.
- Snapshot, new campaign, load snapshot.
- "Where is the loose stone?" still answered farther aside.
- A sit question then "I sit on the stone seat." Posture became sitting.

Result: PASS. Snapshot `2026-11-07T17-09-47_5ef9adf6`.

## Campaign B — report

- "I approach the notice board." Position became beside the Notice board.
- The climb line did not establish stonework and did not change scene state.
- "Am I beside the notice board?" answered from the ledger.
- Snapshot, new campaign, load snapshot. The beside position remained.
- "I step back from the notice board." Position became back.

Result: PASS. Snapshot `2026-11-07T17-09-53_b1e2a90e`.

No response contained a hidden sentinel. Full turn records are in `artifacts/pr_play_76/http/http_campaigns.json`.
"""

reports["20_BROWSER_GAMEPLAY.md"] = """# Browser Gameplay

Host: `artifacts/pr_play_76/runtime.py` on `http://127.0.0.1:8078/`, isolated storage `artifacts/pr_play_76/browser_data`. Player mode. Chat was entered in `#chatInput` and sent with the Send button. Branch choices used the on-screen affordance buttons. Snapshots used Create Snapshot and Load. Two controls that sat below the viewport were activated through the page's own button click after the browser click tool could not scroll them into view.

## Campaign A

New Campaign, Start, typed notice-board examination, typed patrol follow, typed milestone examination, Survey the uncertain trail yourself, Record the limits of your survey, typed loose-stone question, typed push, typed follow-up. The visible answer was "The ordinary loose stone is aside from the stonework." Snapshot `survey-stone` (`2026-11-07T17-12-22_cf8cc1f4`), reload, Load, typed "Where is the loose stone?" The same aside position was published. Screenshot: `browser_A_survey_push.png`.

Result: PASS.

## Campaign B

New Campaign, Start, typed investigation, Return to report the uncertain trail to the watch, typed return to the gate, Give the watch your patrol report, typed approach, typed climb, typed "Am I beside the notice board?" The climb was refused and the beside position remained. Snapshot `report-approach` (`2026-11-07T17-14-59_3b3dd5fd`), reload, Load of that snapshot, typed step back. The visible answer was "You step back from the Notice board." Screenshot: `browser_B_report_climb.png`.

Result: PASS.

Browser success is not inferred from the HTTP runs. The two hosts were separate.
"""

reports["21_REGRESSION_RESULTS.md"] = """# Regression Results

PR-PLAY-75 focused baseline: 1,065 passed, 20 failed. This cycle's focused run failed the same 20 test identities and no others. New focused failures: 0.

Isolated lifecycle (`test_pr_play_71_lifecycle.py`, `test_pr_play_71_persistence_recovery.py`, `test_pr_play_71v_verification.py`): 39 passed, 0 failed. The same files fail inside the combined focused run, which matches the historical combined-versus-isolated split.

Boundary plus broader, run together: the 6 historical opening failures and the 9 historical authority-assurance failures. No additional failure identity appeared. Those 15 tests are the previous boundary and broader failure lists.

This cycle's physical and matrix suites: 121 passed. They are new tests, not a regression of an older passing set.
"""

reports["22_LATENCY_AND_PROVIDER_USAGE.md"] = """# Latency and Provider Usage

HTTP chat turns in the two recorded campaigns: 12.

- Mean: 493.0 ms
- Median of the two central values: 562.9 ms
- Maximum: 1008.8 ms

Browser `/api/chat` completions on the play host: 15 typed submissions.

- Mean: 508.1 ms
- Median: 495.3 ms
- Maximum: 1082.6 ms

The maximum browser server time was "I step back from the notice board." These figures are server completion times, not a separate paint stopwatch.

Live provider requests: 0. Live provider tokens: 0. Retries: 0. Interpretation acceptance and rejection on the live hosts: not applicable, because routine wording never called the provider. Deterministic adjudication, mechanical refusal, ledger mutation, and player-facing text stayed separate in the traces.
"""

reports["23_LIMITATIONS_AND_OPEN_RISKS.md"] = """# Limitations and Open Risks

- Take and drop remain deferred. Ordinary carrying is not granted.
- Place works only after a lift to "raised in place".
- The live campaign has no authored door or crate with affordances. Movement there uses the validated loose-stone fitting, not a promoted clue mention of crates.
- Climbing the broken stonework stays unsupported until an authored check exists.
- A named sit with zero visible seats asks which seat instead of saying the seat is not established. H93 records that miss. It does not mutate state.
- Compounds are limited to two clauses.
- Live provider interpretation was not spent. Novel wording that the deterministic parser cannot classify is covered by the stub tests, not by a live call in this cycle.
- The dirty working tree still contains earlier uncommitted files. They were not part of this verdict.
"""

reports["24_NEXT_SESSION.md"] = """# Next Session

Proceed to PR-PLAY-77: multi-step player intent and consequence-aware planning.

General adjudication is safe. More than two operations work. Physical consequences persist across save and resume. Authority boundaries held: no invented DC, roll, success, room, treasure, quest, or hidden fact was published.

Do not open with another stabilization cycle only because climbing is unsupported, inventory is deferred, some objects lack affordances, or the historical regression failures remain.

The first useful repair inside later work, not a reason to block planning, is the zero-seat clarification in H93. A named seat that is not visible should be declined as not established.

Do not commit or push this cycle unless separately authorized.
"""

for name, text in reports.items():
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")

comparison = {
    "focused_failed": 20,
    "focused_new": 0,
    "lifecycle_isolated": "39/39",
    "boundary_historical": 6,
    "broader_historical": 9,
    "boundary_broader_run_matches_historical_identities": True,
    "development": "121/121",
    "holdout": "99/100",
    "http": "2/2",
    "browser": "2/2",
    "protected": "150/150",
    "live_provider_requests": 0,
    "live_provider_tokens": 0,
}
(ART / "regression_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
handoff = ROOT / "handoff"
handoff.mkdir(exist_ok=True)
archive = handoff / f"CURRENT_REVIEW({stamp})"
if archive.exists():
    shutil.rmtree(archive)
archive.mkdir()
for path in OUT.glob("*.md"):
    shutil.copy2(path, archive / path.name)
for name in (
    "protected_before.json", "frozen_holdout.json", "holdout_results.json",
    "regression_comparison.json", "browser_A_survey_push.png", "browser_B_report_climb.png",
):
    source = ART / name
    if source.exists():
        shutil.copy2(source, archive / name)
http = ART / "http" / "http_campaigns.json"
if http.exists():
    shutil.copy2(http, archive / "http_campaigns.json")
extract = []
network = ART / "browser_network.jsonl"
if network.exists():
    for line in network.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("path") == "/api/chat":
            extract.append({
                "server_ms": row.get("server_ms"),
                "request": row.get("request"),
                "player_facing": row.get("player_facing"),
            })
(archive / "browser_chat_extract.json").write_text(json.dumps(extract, indent=2), encoding="utf-8")
zip_path = handoff / f"CURRENT_REVIEW({stamp}).zip"
if zip_path.exists():
    zip_path.unlink()
shutil.make_archive(str(zip_path.with_suffix("")), "zip", archive)
print(zip_path)
print("reports", len(list(OUT.glob('*.md'))))
