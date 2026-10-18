"""Write the PR-DG artifact set from results.json. No provider calls."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dg_architecture_preflight"


def _load() -> dict:
    return json.loads((OUT / "results.json").read_text(encoding="utf-8"))


def _ceil(value) -> str:
    if not isinstance(value, int):
        return ""
    return str((value + 3) // 4)


def _row(scenario: dict, label: str, row: dict, path: str) -> dict:
    narration = row.get("narration") or {}
    context = row.get("planner_context_bytes") if label == "B" else row.get("tool_context_bytes") if label == "C" else 0
    narration_bytes = narration.get("narration_bytes")
    rounds = 0
    if label == "A" and isinstance(narration_bytes, int):
        rounds = 1
    elif label == "B":
        rounds = 1 + (1 if isinstance(narration_bytes, int) else 0)
    elif label == "C":
        rounds = int(row.get("rounds") or 0) + (1 if isinstance(narration_bytes, int) else 0)
    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_number": scenario["number"],
        "path": path,
        "candidate": label,
        "initial_state_hash": row["initial_state_hash"],
        "resulting_state_hash": row["resulting_state_hash"],
        "resolver": row.get("resolver") or "",
        "status": row.get("status") or "",
        "transaction": row.get("transaction") or "",
        "scene_id": (row.get("after") or {}).get("scene_id"),
        "time_pressure": (row.get("after") or {}).get("time_pressure"),
        "tick_events": "|".join((row.get("after") or {}).get("tick_event_types") or []),
        "enemy_hp": json.dumps((row.get("after") or {}).get("enemy_hp") or {}, sort_keys=True),
        "interlocutor_id": (row.get("after") or {}).get("interlocutor_id") or "",
        "clue_ids": "|".join((row.get("after") or {}).get("known_clue_ids") or []),
        "authority_violations": "|".join(row.get("authority_violations") or []),
        "prohibited_diffs": "|".join(row.get("prohibited_diffs") or []),
        "unsupported": row.get("unsupported"),
        "narration_bytes": narration_bytes if narration_bytes is not None else "",
        "narration_tokens_ceil_bytes_div_4": _ceil(narration_bytes),
        "scripted_context_bytes": context if context else 0,
        "scripted_context_tokens_ceil_bytes_div_4": _ceil(context if isinstance(context, int) else None),
        "hypothetical_provider_rounds": rounds,
        "provider_calls_executed": 0,
    }


def _csv(payload: dict) -> None:
    rows = []
    for scenario in payload["scenarios"]:
        for label in ("A", "B", "C"):
            rows.append(_row(scenario, label, scenario["gold"][label], "gold"))
        for label, row in (scenario.get("illegal") or {}).items():
            rows.append(_row(scenario, label, row, "illegal"))
    path = OUT / "PR-DG_scenario_comparison.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _scenario_lines(payload: dict) -> str:
    lines = [
        "| # | Id | A status | A resolver | B status | B transaction | C status | C rounds | Match 1–9 | Sheet |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for scenario in payload["scenarios"]:
        gold = scenario["gold"]
        match = "" if not scenario.get("mechanical_match") else str(scenario["mechanical_match"]["match"])
        sheet = ",".join(f"{label}:{scenario['sheet']['pass'].get(label)}" for label in ("A", "B", "C"))
        lines.append(
            f"| {scenario['number']} | {scenario['scenario_id']} | {gold['A']['status']} | {gold['A'].get('resolver')} | "
            f"{gold['B']['status']} | {gold['B'].get('transaction')} | {gold['C']['status']} | {gold['C'].get('rounds')} | {match} | {sheet} |"
        )
    return "\n".join(lines)


def write_reports() -> None:
    payload = _load()
    _csv(payload)
    decision = payload["decision"]
    model = payload["model_configuration"]
    (OUT / "PR-DG_implementation_report.md").write_text(_implementation(payload, decision, model), encoding="utf-8")
    (OUT / "PR-DG_runner_design.md").write_text(_runner_design(), encoding="utf-8")
    (OUT / "PR-DG_candidate_A_results.md").write_text(_candidate_a(payload), encoding="utf-8")
    (OUT / "PR-DG_candidate_B_results.md").write_text(_candidate_b(payload), encoding="utf-8")
    (OUT / "PR-DG_candidate_C_results.md").write_text(_candidate_c(payload), encoding="utf-8")
    (OUT / "PR-DG_transaction_safety.md").write_text(_transactions(payload), encoding="utf-8")
    (OUT / "PR-DG_authority_controls.md").write_text(_authority(payload), encoding="utf-8")
    (OUT / "PR-DG_interpretation_limitations.md").write_text(_interpretation(payload), encoding="utf-8")
    (OUT / "PR-DG_cost_instrumentation.md").write_text(_cost(payload, model), encoding="utf-8")
    (OUT / "PR-DG_remaining_risks.md").write_text(_risks(decision), encoding="utf-8")
    print("wrote reports", decision["code"])


def _implementation(payload: dict, decision: dict, model: dict) -> str:
    return f"""# PR-DG Implementation Report

MODE: ARCHITECTURAL EXPERIMENT PREFLIGHT

LIVE PROVIDER CALLS: 0

PR-DF inherited decision: A — COMPARISON READY

PR-DG decision: {decision['code']} — {"PREFLIGHT READY" if decision["code"] == "A" else decision["code"]}

{decision["reason"]}

Scripted plans and scripted tool transcripts are not evidence that a live planner or a live tool-using model would choose those steps.

## Phase 0 — worktree

| Item | Value |
|---|---|
| HEAD | `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` |
| HEAD subject | PR-BN bounded DM improvisational authority |
| Worktree | Dirty before this cycle. Left dirty. Production saves were already modified and were not reset. |
| Production saves | `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`, plus character, campaign, and conditions, were fingerprinted. The write guard intercepted a probe to session, world, and the session log, then the scenario run recorded {payload["isolation"]["blocked_writes_after_probe"]} further blocked writes. The fingerprint matched at exit. |
| Provider calls | 0. `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` raise if invoked. `ASHEN_DISABLE_LIVE_INTERPRETATION=1`. |

## What was implemented

An isolated package, `experiments/pr_dg/`, plus `tests/test_pr_dg_architecture_preflight.py`. It is not imported by `chat`.

- Copied fixture bundles from the PR-DE constructors (`_gate_session_scene`, the K1 synthetic scene, `_scene_with_goblin`).
- One shared tick per turn: `advance_world_tick` then `advance_clock(session, "time_pressure", 1)`, then the turn counter increments. A second call returns `already_applied`.
- Candidate A runs `select_ordinary_resolver` on a discarded copy with interpretation pinned off, then the existing social, noncombat, exploration, or combat resolver.
- Candidate B validates a hand-authored plan and executes permitted steps through that same dispatch.
- Candidate C dispatches the eight PR-DF tools. Read-only tools are hash-checked. Writes go through the same dispatch or the same tick.
- State tuples and sha256 hashes are stored in `results.json` and `PR-DG_scenario_comparison.csv`.

## Contradictions in the PR-DF packet

These were not resolved by widening the experiment.

1. `PR-DF_experiment_design.md` says to call the PR-DE builders and the resolvers, not `chat`. `PR-DF_current_architecture_map.md` says the production path is `chat`, which loads and saves the production documents. The harness follows the experiment design. It does not call `chat`.
2. PR-DE's `_social` / `_explore` attach the contract after resolution. The architecture map builds the contract first. The harness selects the contract on a discarded copy, then calls the existing resolver. On scenarios 1–9 the selector and the executed resolver agreed.
3. Candidate B's operation enum includes `advance_time`. `semantic_interpreter._ALLOWED_OPERATIONS` includes `unresolved` and does not include `advance_time`. The harness uses the B enum for plans. It does not treat `advance_time` as a second clock.
4. `call_gpt` invokes `responses.create(model=route.selected_model, input=messages)` with no temperature and no max-token keyword. Interpretation uses temperature 0 and `max_output_tokens` 400. Those are the code values. Narration temperature was not invented. Recorded model name: `{model["default_model_name"]}`.
5. `build_canonical_referent_catalog` does not list scene enemies. `resolve_attack` addresses enemies on the scene document. The validator accepts an id that is already an enemy on that scene and records the gap. It does not mint enemies.
6. `_apply_authoritative_resolution_state_mutation` raises if the scene is marked `_is_canon`. `load_scene` sets that flag. The harness uses `build_effective_scene`, the existing gameplay copy, and does not write canon files.

## Scenario outcome

{_scenario_lines(payload)}

Scenarios 1–9 match on scene id, clue ids, enemy HP, interlocutor, time pressure, and tick event types. Illegal plans and illegal tool transcripts on scenarios 10, 13, and 14 do not commit HP, flags, or hidden strings.

Scenario 12 moved `df_mobile_courier` to `market_quarter` with one `npc_moved` event for A, B, and C. That is the current tick, not an engine gap.

## Decision

**{decision["code"]} — PREFLIGHT READY.**

The three scripted interfaces run through the existing resolvers under one authority contract. The adversarial controls do not commit unauthorized changes. A bounded live comparison can use the PR-DF minimum set. It still has to pin interpretation off for A, inject the combat die, keep isolated copies, and treat planner or tool quality as unmeasured.

Recommended next step: a bounded live arm on S1, the compound pry, the ambiguous ask, the declared-canon line, C1, and B1. No production saves. No claim that this preflight measured narrative quality.
"""


def _runner_design() -> str:
    return """# PR-DG Runner Design

The runner lives in `experiments/pr_dg/`. Production `chat` does not import it.

## Isolation

`ProductionSaveGuard` replaces `game.storage._atomic_write_bytes`, `_save_json`, and `append_log`. A path under `data/` is stored in memory and not written. Before any scenario, the guard writes a probe session, a probe world, and a probe log line, then asserts the on-disk fingerprint is unchanged. If that probe touches disk, the run stops.

`forbid_provider_calls` patches `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` to raise. `ASHEN_DISABLE_LIVE_INTERPRETATION` is set.

## Shared state

Each scenario factory returns one bundle. A, B, and C each receive a deep copy. The initial hash is taken before the tick, so the three candidates share it.

The tick is idempotent via a harness flag on the session copy. That flag is not a world flag and is not part of the state hash. The hash covers the authoritative tuple: scene id, clue ids and texts, combat HP, time pressure, tick event types, interlocutor, improvisation ledger, world flags, NPC locations, entity ids, and turn counter.

## Dispatch

`select_contract` builds the ordinary contract with `enable_model_interpretation` left off and the environment pin set. It runs on a discarded copy so the selector's telemetry does not become the candidate's state.

`execute_authorized` then calls one existing function:

| Selector | Call |
|---|---|
| social | `play_turn` (the PR-DE social entry, which calls `resolve_social_action`) |
| exploration, travel, world_action | `resolve_noncombat_action` |
| exploration on the K1 scene with utterance `Search.` | `resolve_exploration_action` with the PR-DE synthetic investigate action |
| combat, and the utterance is the quarterstaff attack | `resolve_attack` with `roll_die` patched to 10 |
| generation | no resolver |

`_apply_authoritative_resolution_state_mutation` runs after a domain resolution. If it raises, the bundle returns to the post-resolver copy and the exception is recorded. That is not an engine undo log.

## What the runner does not do

It does not call a provider, write `data/`, add a combat rule, add an inventory spend, or wire downtime. A preview that would have to roll returns `unsupported` for `social_check`. Attack and configured skill previews read `player_can_act` and `_get_skill_check_config` and do not call `resolve_attack` or `resolve_skill`.
"""


def _candidate_a(payload: dict) -> str:
    lines = ["# PR-DG Candidate A Results", "", "Interpretation was pinned off. No narration provider call was made. Failures were not repaired.", "", "| # | Resolver | Kind | Unsupported | Fast-path abstained | Narration bytes | HP | Interlocutor |", "|---|---|---|---|---|---:|---|---|"]
    for scenario in payload["scenarios"]:
        row = scenario["gold"]["A"]
        selector = row.get("selector") or {}
        lines.append(
            f"| {scenario['number']} {scenario['scenario_id']} | {row.get('resolver')} | {(row.get('resolution') or {}).get('kind')} | {row.get('unsupported')} | {selector.get('fast_path_abstained')} | {((row.get('narration') or {}).get('narration_bytes'))} | {row['after'].get('enemy_hp')} | {row['after'].get('interlocutor_id')} |"
        )
    lines.append("")
    lines.append("Ordinary social lines (S1, S2, F1, H1, C1) selected `social` / `ask` and the social resolver ran. The interlocutor stayed `guard_captain`. No clue ids were added on F1. That is the resolver's result on this fixture, not a harness repair.")
    lines.append("")
    lines.append("M1 selected `travel`. The scene id stayed `frontier_gate`. O1 selected `exploration` / `perceive`. Entity ids did not change.")
    lines.append("")
    lines.append("K1 selected `exploration` / `inspect`. `resolve_exploration_action` returned a perception check: modifier 2, DC 8, roll 10, total 12, success true. The roll is `game.skill_checks._deterministic_d20`, not the combat `roll_die` patch. The observed roll happened to be 10.")
    lines.append("")
    lines.append("B1 selected `combat`. `resolve_attack` with `roll_die` patched to 10 wrote goblin HP from 6 to 0. The same HP appears for B and C.")
    lines.append("")
    lines.append("The compound sentence selected `travel` even though `fast_path_abstained` and `model_interpretation_appropriate` were both true. The pin skipped the interpreter. The scene did not change and the board facts stayed. The pry was not a second resolved step.")
    lines.append("")
    lines.append("The ambiguous line selected `social`, and the social entry did not route (`social_entry_did_not_route`). The parsed kind was `interact`. No interlocutor was stored.")
    lines.append("")
    lines.append("The declared-canon line selected `world_action` and resolved as `custom`. World flags and clue ids did not change.")
    lines.append("")
    lines.append("The HP-dump line selected `social`. The parsed kind was `attack`, and `resolve_attack` was not called. Goblin HP stayed 6.")
    lines.append("")
    lines.append("The courier tick appended one `npc_moved` and the courier location became `market_quarter` before the social resolver ran.")
    return "\n".join(lines) + "\n"


def _candidate_b(payload: dict) -> str:
    return f"""# PR-DG Candidate B Results

Hand-authored plans. No planner call. A plan is not an outcome.

The validator requires `authority` = `non_authoritative_proposal`, the closed operation and resolver enums, at most four steps, and an acyclic `depends_on`. Forbidden fields (`hit_points`, `roll`, `hidden_facts`, `world_flags`, `narration_prose`, `commitment_status`, and the rest of the drop list) reject the step that carries them. A cleared catalog id marks the plan ambiguous and stops before steps. The contract selector outranks `proposed_resolver`.

On scenarios 1–9 the gold plan is one step that names the same utterance A used. The mechanical tuple matches A.

| # | Status | Transaction | Steps |
|---|---|---|---|
""" + "\n".join(
        f"| {scenario['number']} {scenario['scenario_id']} | {scenario['gold']['B']['status']} | {scenario['gold']['B'].get('transaction')} | "
        + "; ".join(f"{step.get('step_id')}:{step.get('status')}" for step in (scenario['gold']['B'].get('steps') or []))
        + " |"
        for scenario in payload["scenarios"]
    ) + """

The compound plan commits the approach and returns `unsupported` for the pry, because the pry sentence selects `generation`. The board stays. Transaction: `partially_committed`.

The ambiguous, declared-canon, and HP-dump gold plans set `uncertainty.ambiguous` and have no actions. No step runs. The shared tick still happens, matching chat's order.

Illegal plans on scenarios 10, 13, and 14 carry hit points, hidden facts, and world flags. Those steps are rejected. HP, flags, and clue ids do not change.

This does not show that a live model would emit these plans.
"""


def _candidate_c(payload: dict) -> str:
    return f"""# PR-DG Candidate C Results

Hand-authored tool transcripts. No tool-using model. Cap: four tool rounds. A fifth call would return `budget` and would not mutate.

Read-only tools: `inspect_visible_scene`, `query_known_entities`, `inspect_permitted_npc_context`, `request_rules_adjudication`, `propose_action`, `inspect_resulting_state`.

State-changing tools: `request_action_execution` and `advance_authorized_time`. Execution re-validates. It calls the same dispatch as B. The time tool is the shared tick; a second call is `already_applied`.

`request_rules_adjudication` for `attack` calls `player_can_act` and checks the enemy id. It does not call `resolve_attack`. For `skill` it reads `_get_skill_check_config` and does not report a guessed DC. `social_check` returns `unsupported` because a pure preview is not separated from the social resolver.

Hidden fields are not a tool output. `inspect_resulting_state` rejects `hidden_facts` with `permission`. A result that contains a fixture hidden string is replaced with an empty refusal.

| # | Status | Transaction | Rounds | Resolver recorded from execution |
|---|---|---|---|---|
""" + "\n".join(
        f"| {scenario['number']} {scenario['scenario_id']} | {scenario['gold']['C']['status']} | {scenario['gold']['C'].get('transaction')} | {scenario['gold']['C'].get('rounds')} | {scenario['gold']['C'].get('resolver')} |"
        for scenario in payload["scenarios"]
    ) + """

Where the gold transcript executes one legal step, the resulting state hash matches A and B. The compound transcript commits the approach and returns `unsupported` for the pry inside the four-round cap. Illegal transcripts that pass `hit_points` and `hidden_facts` into `request_action_execution` are refused. Goblin HP stays at the setup value on scenario 14.

This does not show that a live model would choose these tool calls.
"""


def _transactions(payload: dict) -> str:
    lines = ["# PR-DG Transaction Safety", "", "There is no engine undo. One successful resolver call commits on the harness copy. A later rejected step does not roll the earlier step back. Discarding a deep copy is not rollback, and these rows do not claim that it is.", ""]
    for case in payload["transactions"]:
        lines.append(f"## {case['name']}")
        lines.append("")
        shown = {key: value for key, value in case.items() if key != "name"}
        lines.append("```json")
        lines.append(json.dumps(shown, indent=2, default=str))
        lines.append("```")
        lines.append("")
    lines.append("## How to read the ten rows")
    lines.append("")
    lines.append("1. Successful single action: one social resolver call commits. The transaction is one resolver call, not a multi-step transaction.")
    lines.append("2. Invalid action: unknown id `duke_of_nowhere` is cleared, the plan stops before a resolver, scene and clues stay put. The shared tick still advances `time_pressure` by 1, which is chat's order.")
    lines.append("3. Partially valid compound: the approach commits and the pry is `unsupported`. Partially committed.")
    lines.append("4. Invalid second step: the ask commits and the step that carries `hit_points` is rejected. Partially committed. The forbidden step does not run.")
    lines.append("5. Repeated action: the second `request_action_execution` for the same step id returns `already_applied`.")
    lines.append("6. Read-only query: `inspect_visible_scene` leaves the state hash unchanged.")
    lines.append("7. Read-only combat preview: HP is unchanged and `roll_die` is not called.")
    lines.append("8. World clock: the first time tool commits `time_pressure` 1. The second returns `already_applied`.")
    lines.append("9. Hidden-information request: `hidden_facts` is `permission`. The fixture hidden string is not in the tool result.")
    lines.append("10. Unauthorized HP write: `permission`, mutation `refused`, HP unchanged.")
    lines.append("")
    lines.append("Compound execution is not atomic. A well-formed unsupported second step is partially committed. A forbidden field on a later step is also partially committed when an earlier step was valid. An unknown entity id stops the plan before any step.")
    return "\n".join(lines) + "\n"


def _authority(payload: dict) -> str:
    lines = ["# PR-DG Authority Controls", "", "A committed unauthorized change is a failure, not a warning. None of these attempts committed one.", ""]
    lines.append("| Attempt | Code | Mutation | Committed unauthorized |")
    lines.append("|---|---|---|---|")
    for row in payload["adversarial"]:
        lines.append(f"| {row['name']} | {row.get('code')} | {row.get('mutation')} | {row.get('committed_unauthorized')} |")
    lines.append("")
    lines.append("Duplicate execution codes: " + json.dumps(next(row.get("codes") for row in payload["adversarial"] if row["name"] == "duplicate_steps")))
    lines.append("")
    lines.append("Illegal scenario rows for 10, 13, and 14 are in the CSV with path `illegal`. Their authority-violation lists are empty and scenario 14's goblin HP stays 6.")
    lines.append("")
    lines.append("Read-only tools that change the state hash are restored and recorded as `read_only_mutation`. That restoration is containment after a failed control. It is not a successful read, and it did not trigger on these rows.")
    lines.append("")
    lines.append("The production post-GM gateway is not on this path. Narration text was not sent to a provider, so this preflight does not score a narration leak. Hidden strings were checked in tool results and in engine-visible control output.")
    lines.append("")
    lines.append("`fabricate_outcome` calls the read-only `propose_action` tool with `narration_prose` on the step. The plan validator strips that forbidden field and does not store it. The tool then accepts the remaining proposal shape, which is why the code is `ok` and the mutation is `none`. The sentence is not an outcome. `request_action_execution` refuses a step that still carries a forbidden field.")
    return "\n".join(lines) + "\n"


def _interpretation(payload: dict) -> str:
    return """# PR-DG Interpretation Limitations

Live interpretation was pinned off. Nothing here is a claim about a live model's plan.

## A. Ordinary correctly classified actions

S1, S2, F1, H1, and C1 select `ask` / `social` with interlocutor `guard_captain`. O1 selects `perceive` / `exploration`. K1 selects `inspect` / `exploration` and the synthetic check runs. B1 selects `act` / `combat` and `resolve_attack` runs. M1 selects `act` / `travel` and the scene does not change. A, B, and C match on the mechanical tuple for these nine.

## B. Deterministic abstentions

Scenarios 10 and 13 set `fast_path_abstained` and `model_interpretation_appropriate`. The pin made the interpreter return skipped, and the provider tripwire stayed at zero calls. The contract that remained was still executable: travel for the compound sentence, world_action for the declared-canon sentence. An abstention-only fallback that stopped whenever `fast_path_abstained` is true would have refused both. The selector did not stop. Abstention-only fallback would miss these, because they are abstentions that still carry a selected resolver.

## C. Confident deterministic misclassifications

Scenario 14's contract selects `social` / `ask` with no interlocutor. Inside the social entry, the parser's kind is `attack`. `resolve_attack` is not called, and HP stays 6. The mislabel is confident in the parser output and contained by the combat gate, which only attacks when the selector says combat and the utterance is the quarterstaff line.

Scenario 11's contract selects `social` / `ask` with no interlocutor. The social entry does not route. The parsed kind is `interact`. No interlocutor is stored. The selector was confident. The entry abstained. B's gold plan expresses the ambiguity directly and runs no step. The existing social resolver, given that the entry does not route, also does not pick an NPC. What remains unsupported is a clarification line that names the two candidate referents. The harness does not invent that line as canon.

## D. Compound actions

A resolves the whole pry sentence as one travel action and does not remove the board. B and C can express two steps. The approach runs under the M1 rule. The pry selects `generation` and returns `unsupported`. No new pry mechanic was added. The first step stays committed.

## E. Ambiguous player requests

The fresh-state line has two addressable people and no discourse focus. A's selector does not set `ambiguous`. B's hand-authored plan does, and stops. Both leave the interlocutor empty. A live planner is not shown to do what the hand-authored plan does.

## F. Unsupported mechanics

Pry, a direct HP assignment, a hidden dump, downtime (`delta` other than 1, or a rest activity), a social-check preview, and an item spend are unsupported. The skill preview can see a configured check without rolling. Attack preview can see `player_can_act` without rolling.

## What a hand-authored plan can express, and what the resolvers can execute

A plan can name the approach and the pry, the ambiguity, and the refusal. The resolvers can execute the approach, the social ask, the synthetic check, and the patched attack. They cannot execute the pry, the fiat HP write, or a hidden reveal. Those stay unsupported. A live model is not inferred to produce the hand-authored plan.
"""


def _cost(payload: dict, model: dict) -> str:
    lines = ["# PR-DG Cost Instrumentation", "", "No live provider call. No latency for a provider. No output-token assumption. No price.", "", f"Narration call shape from code: {model['narration_call']}", f"Default model name from code: `{model['default_model_name']}`.", "Narration temperature and max tokens: not passed. Interpretation, if it were enabled, uses temperature 0 and max_output_tokens 400. It was not enabled.", "Token estimate method: `ceil(utf-8 bytes / 4)`. This is not a provider bill. `tiktoken` was not required for this label.", "", "Scripted planner and tool bytes are the serialized gold plan or transcript plus the tool results. They are not measured live prompt usage.", "", "| # | A narration bytes | A est. | B narration | B scripted context | C narration | C scripted context | C rounds |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for scenario in payload["scenarios"]:
        a = scenario["gold"]["A"]["narration"]
        b = scenario["gold"]["B"]
        c = scenario["gold"]["C"]
        lines.append(
            f"| {scenario['number']} {scenario['scenario_id']} | {a.get('narration_bytes')} | {_ceil(a.get('narration_bytes'))} | "
            f"{b['narration'].get('narration_bytes')} | {b.get('planner_context_bytes')} | {c['narration'].get('narration_bytes')} | "
            f"{c.get('tool_context_bytes')} | {c.get('rounds')} |"
        )
    lines.append("")
    lines.append("Hypothetical provider rounds, if these scripts were later sent to a model, and if narration retries stay unknown rather than zero:")
    lines.append("")
    lines.append("- A: `I = 0` because interpretation is pinned off. `N = 1` when a narration payload was built, else the turn did not reach narration. `R` is not measured.")
    lines.append("- B: `P = 1` scripted plan input, `Q = 0` replans in this preflight, plus `N` as above when the plan executed.")
    lines.append("- C: the transcript round count (at most 4), plus `N` when execution committed.")
    lines.append("")
    lines.append("Where B or C executed, their narration byte count matched A. The payloads are not smaller. PR-DE's published S1 figure is 87,583 bytes. This run's S1 narration payload is the `build_messages` size for the harness resolution, and it is a different number. It is not used as a cost win against PR-DE or against another candidate.")
    lines.append("")
    lines.append("Local resolver timers were recorded in milliseconds on the result rows (`elapsed_ms`). Those are process timers around existing resolver calls. They are not provider latency and they are not a table baseline.")
    return "\n".join(lines) + "\n"


def _risks(decision: dict) -> str:
    return f"""# PR-DG Remaining Risks

PR-DG decision: {decision["code"]} — PREFLIGHT READY.

## What this cycle measured

Scripted A, B, and C can be compared on one copied world. Scenarios 1–9 match. Adversarial controls do not commit. Production saves do not change. Provider calls are zero.

## What it does not measure

- Whether a live planner emits a legal plan.
- Whether a live tool-using model stays inside the tools.
- Narrative quality. No provider narration was generated.
- Provider latency, output tokens, or price.
- Retry rate `R`. It stays unknown.

## Engine limits that remain

- No engine undo. Compound plans are partially committed.
- The post-GM gateway is still observe-only on production `chat`. This harness does not call it. A later integration that calls `chat` brings the seam back.
- The referent catalog omits enemies. The harness allows existing scene enemy ids and records that gap.
- F1 did not add a clue. That is the current resolver on this fixture.
- Downtime is still unwired. The time tool rejects a delta other than 1.
- Social-check preview is `unsupported` so it cannot roll by accident.
- Scenarios 10 and 13 abstain and still select a resolver. Turning live interpretation on for A would add a provider call the preflight did not make.
- The shared pipeline's inherited failures were not repaired.

## What would move the decision

A live arm that writes production saves, leaks a hidden string into a tool result, or needs a new mutator stops. A live arm that only shows scripted-plan behavior again would not answer the planner question.
"""


if __name__ == "__main__":
    write_reports()
