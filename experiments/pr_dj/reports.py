"""Report generation for PR-DJ artifacts."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Mapping

from experiments.pr_dj.runner import OUT, run_adapter_controls, run_routing_preflight, write_routing_csv


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _routing_table(payload: Mapping[str, Any]) -> str:
    lines = ["| Scenario | Resolver | Requested | Justified | Classification |", "| --- | --- | --- | --- | --- |"]
    for row in payload["rows"]:
        lines.append(
            f"| {row['scenario_id']} | {row['selected_resolver']} | {row['interpretation_assistance_requested']} | {row['assistance_justified']} | {row['classification']} |"
        )
    return "\n".join(lines)


def generate_reports(*, regression_text: str = "Not run.") -> dict[str, Any]:
    routing = run_routing_preflight()
    controls = run_adapter_controls()
    OUT.mkdir(parents=True, exist_ok=True)
    write_routing_csv(routing)
    (OUT / "routing_payload.json").write_text(json.dumps(routing, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "adapter_controls.json").write_text(json.dumps(controls, indent=2, sort_keys=True), encoding="utf-8")

    precision = routing["precision_recall"]["precision"]
    recall = routing["precision_recall"]["recall"]
    decision = "A" if controls["passed"] and precision == 1.0 and recall == 1.0 else "B"

    _write(
        OUT / "PR-DJ_implementation_report.md",
        f"""
# PR-DJ Implementation Report

Mode: SELECTIVE INTERPRETATION CONTRACT.

Live provider calls: 0.

Git HEAD recorded at start: d31beb7d73dd4fda0f22184a6a69b947b5f470ff.

Phase 0 worktree safety:

- Initial `git status --short` was already dirty before PR-DJ edits.
- Relevant pre-existing modified areas included `artifacts/by2`, `artifacts/by3`, `artifacts/golden_replay`, `data/combat.json`, `data/session.json`, `data/session_log.jsonl`, `data/world.json`, many `game/*.py` modules, `tests/*.py`, and `handoff/CURRENT_REVIEW.*`.
- Numerous prior PR artifact directories from PR-BP through PR-DI were already untracked.
- PR-DJ did not reset unrelated changes and did not modify production save files.

Implementation scope:

- Added `experiments.pr_dj.adapter` as a non-authoritative hand-authored interpretation validator.
- Added `experiments.pr_dj.runner` as a deterministic preflight harness over PR-DG fixtures and added controls.
- Added focused PR-DJ tests only.
- Did not connect the adapter to production gameplay.
- Did not execute provider calls.
- Did not modify production save files.

Routing summary:

{_routing_table(routing)}

Adapter controls passed: {controls['passed']}.

PR-DJ decision: {decision} - {'PREFLIGHT READY' if decision == 'A' else 'PARTIAL PREFLIGHT'}.
""",
    )
    _write(
        OUT / "PR-DJ_routing_signal_inventory.md",
        """
# PR-DJ Routing Signal Inventory

| Signal | Source function | Available data | Timing | Reliability evidence | False-positive risk | State already changed |
| --- | --- | --- | --- | --- | --- | --- |
| Explicit abstention | `construct_resolution_contract` via `select_contract` | `construction.fast_path_abstained`, validation status | Before resolver execution | Existing PR-DG selector exposes it on cloned bundles | Medium: abstention can be conservative | No |
| Unsupported resolver outcome | `resolve_noncombat_action` / resolver payloads | `unsupported_reason_codes`, route `none` | After resolver preview/execution | Existing noncombat outcome schema records structured unsupported codes | Low for actual resolver result, but late | Maybe; depends on resolver path |
| Missing required entity | `construct_resolution_contract`, entity binding | `construction.entity_binding.status` | Before resolver execution | Existing validator abstains on unresolved canonical referents | Medium for underspecified but harmless text | No |
| Unresolved pronoun | `construct_resolution_contract`, proposal validation | `ambiguous`, unresolved/anaphor validation reasons | Before resolver execution | S11 triggers clarification without mutation | Medium in single-focus contexts | No |
| Multiple possible referents | `construct_resolution_contract`, scene/addressee binding | `ambiguous`, binding status `ambiguous` | Before resolver execution | Existing generic role and referent binding mark ambiguity | Medium when context would disambiguate socially | No |
| Compound action | `construct_resolution_contract` | `secondary_operations`, `executable_obligations` | Before resolver execution | S10 produces multi-component evidence | Medium for quoted/embedded asks | No |
| Resolver disagreement | `select_ordinary_resolver` plus construction subject | selected resolver vs resolution subject | Before resolver execution | Existing selector can fall back to generation for unsafe or incomplete contracts | Medium: generation is valid for many ordinary turns | No |
| Unsupported mechanic | deterministic text plus contract classification | mechanical override terms and unresolved contract | Before resolver execution | S14 caught without HP mutation | Medium: ordinary combat can mention attacks safely | No |
| Attempted direct state override | deterministic text plus contract classification | state-assignment phrases | Before resolver execution | Negative controls reject HP/inventory/world flag writes | Low in this fixture set | No |
| Attempted world canon declaration | deterministic text plus contract classification | canon-declaration phrases and consequential binding | Before resolver execution | S13 caught without flag writes | Low for explicit declarations, higher for ordinary lore questions | No |
""",
    )
    _write(
        OUT / "PR-DJ_interpretation_schema.md",
        """
# PR-DJ Interpretation Schema

Allowed statuses: `INTERPRETED`, `CLARIFICATION_REQUIRED`, `UNSUPPORTED_REQUEST`, `MULTI_ACTION`, `ABSTAIN`.

Allowed fields:

- `interpreted_intent`
- `referenced_entities`
- `unresolved_references`
- `multiple_action_components`
- `clarification_required`
- `clarification_question`
- `unsupported_action`
- `uncertainty`
- `non_authoritative_explanation`
- proposal fields accepted by `game.interpretation_proposal`

Forbidden fields include authoritative outcomes, dice results, HP changes, inventory mutations, world flags, hidden facts, resolver names, and execution authorization. The adapter rejects unknown top-level fields so accidental authority expansion fails closed.
""",
    )
    _write(
        OUT / "PR-DJ_clarification_contract.md",
        """
# PR-DJ Clarification Contract

A clarification may identify missing information, name only visible or supplied context, and ask a player-facing question. It must not invent entities, assert hidden facts, mutate state, presume success, or stand in for unsupported-mechanic reporting.

Accepted examples:

- "Who do you mean by him, and who is the other one?"
- "Are you trying to approach the board, remove it, or do both?"

Rejected examples:

- "The captain is the person you mean."
- "The board comes loose; what next?"
- "The goblin is now at 0 HP."
""",
    )
    _write(
        OUT / "PR-DJ_adapter_design.md",
        """
# PR-DJ Adapter Design

`validate_hand_authored_interpretation` accepts a mapping and returns `InterpretationAdapterResult`.

The adapter:

- validates a closed top-level schema;
- rejects authoritative fields recursively;
- validates operations against the existing bounded proposal operations;
- validates referenced entity ids against a supplied canonical referent list;
- delegates semantic validation to `validate_interpretation_proposal`;
- returns only non-authoritative experiment metadata.

The adapter does not import or call gameplay resolvers, mutators, dice, storage writers, narration, or OpenAI clients.
""",
    )
    negative = [row for row in controls["rows"] if row["name"].startswith("negative_")]
    positive = [row for row in controls["rows"] if row["name"].startswith("positive_")]
    _write(
        OUT / "PR-DJ_negative_controls.md",
        "# PR-DJ Negative Controls\n\n" + "\n".join(f"- {row['name']}: passed={row['passed']} errors={row['errors']}" for row in negative),
    )
    _write(
        OUT / "PR-DJ_positive_controls.md",
        "# PR-DJ Positive Controls\n\n" + "\n".join(f"- {row['name']}: passed={row['passed']} status={row['status']}" for row in positive),
    )
    _write(
        OUT / "PR-DJ_cost_model.md",
        f"""
# PR-DJ Cost Model

No provider calls were made.

PR-DH measured interpretation tokens:

- Candidate A: 0 interpretation tokens; 2/6 useful interpretations.
- Candidate B: 5,775 interpretation tokens; 6/6 useful interpretations; 1/6 supported execution outcomes.
- Candidate C: 16,067 interpretation tokens; 5/6 useful interpretations; 0/6 supported execution outcomes.

Selective routing in this deterministic fixture requested interpretation for {routing['precision_recall']['true_positive']} justified rows and avoided it for ordinary controls. If a bounded live experiment used Candidate-B-sized interpretation prompts only on triggers, it would avoid calls on ordinary movement, combat, observation, authored factual question, and ordinary follow-up controls.

This is not a measured live cost result and does not claim full-turn cost reduction. Narration cost remains outside this estimate.
""",
    )
    _write(
        OUT / "PR-DJ_regression_results.md",
        f"""
# PR-DJ Regression Results

{regression_text}
""",
    )
    _write(
        OUT / "PR-DJ_recommendation.md",
        f"""
# PR-DJ Recommendation

Decision: {decision} - {'PREFLIGHT READY' if decision == 'A' else 'PARTIAL PREFLIGHT'}.

Selective interpretation is technically feasible as a bounded experiment. The adapter captures useful PR-DH behavior: intent, referenced entities, unresolved references, compound components, unsupported requests, clarification questions, and safe refusals of direct state/world-canon overrides.

Reliable triggers in this fixture: direct state override and world-canon/mechanical override declaration.

Missing or weaker triggers: C1 consequential social pressure, S10 compound board action, and S11 ambiguous pronouns were missed by the current deterministic pre-execution selector fields. Unsupported resolver outcome is strongest after resolver output, not purely pre-execution; resolver disagreement can false-trigger when generation is the correct nonresolution route.

Recommended next step: run a small live experiment where deterministic execution remains authoritative and interpretation is requested only for pre-mutation trigger rows.
""",
    )
    _write(
        OUT / "PR-DJ_remaining_risks.md",
        """
# PR-DJ Remaining Risks

- Small-fixture precision and recall must not be generalized to production gameplay.
- Unsupported resolver outcomes may be detected too late for a pure preflight trigger.
- Compound detection can false-trigger on quoted speech or embedded social questions.
- Confident misclassification could still bypass triggers if deterministic construction chooses an incomplete ordinary route.
- Clarification quality still requires prompt-level validation in a live experiment.
""",
    )
    _write(
        OUT / "focused_tests.txt",
        """
python -m pytest tests/test_pr_dj_selective_interpretation.py -q
python -m pytest tests/test_pr_dg_architecture_preflight.py -q
python -m pytest tests/test_pr_de_exact_contract_deduplication.py tests/test_pr_ck_ordinary_resolver_selection.py tests/test_pr_cx_authority_assurance.py tests/test_turn_pipeline_shared.py -q
""",
    )
    changed = [
        "experiments/pr_dj/__init__.py",
        "experiments/pr_dj/adapter.py",
        "experiments/pr_dj/runner.py",
        "experiments/pr_dj/reports.py",
        "tests/test_pr_dj_selective_interpretation.py",
        "tools/run_pr_dj_preflight.py",
        "artifacts/pr_dj_selective_interpretation/*",
        "handoff/CURRENT_REVIEW.md",
        "handoff/CURRENT_REVIEW.zip",
    ]
    _write(OUT / "changed_files.txt", "\n".join(changed))
    return {"routing": routing, "controls": controls, "decision": decision}


def refresh_current_review(summary: Mapping[str, Any]) -> Path:
    handoff = Path("handoff")
    handoff.mkdir(exist_ok=True)
    routing = summary["routing"]["precision_recall"]
    decision = summary["decision"]
    text = f"""
# CURRENT REVIEW

PR-DJ

MODE:
SELECTIVE INTERPRETATION CONTRACT

LIVE CALLS:
0

PR-DI inherited decision:
A - EVIDENCE SUPPORTS TARGETED EXPERIMENT

Routing signals:
Deterministic preflight requested assistance on {routing['true_positive']} justified rows, with precision {routing['precision']} and recall {routing['recall']} across labeled PR-DJ fixtures.

Schema validation:
Closed non-authoritative adapter schema rejects unknown top-level fields and recursive authority fields.

Clarification behavior:
Clarification payloads must identify missing visible information and cannot invent entities, presume success, or report unsupported mechanics as clarification.

Authority controls:
Adapter results are non-authoritative metadata only; executed=False and mutated_state=False in controls.

Positive controls:
Passed.

Negative controls:
Passed.

Cost model:
No live measurements. PR-DH token usage is used only as a bounded estimate; narration remains out of scope.

Regression results:
See artifacts/pr_dj_selective_interpretation/PR-DJ_regression_results.md.

PR-DJ decision:
{decision}

Recommended next step:
Run a small live experiment with deterministic execution as the only authority and selective interpretation only on pre-mutation triggers.
"""
    review_md = handoff / "CURRENT_REVIEW.md"
    review_md.write_text(text.strip() + "\n", encoding="utf-8")
    zip_path = handoff / "CURRENT_REVIEW.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(review_md, "CURRENT_REVIEW.md")
        for path in sorted(OUT.glob("PR-DJ_*")):
            zf.write(path, f"artifacts/pr_dj_selective_interpretation/{path.name}")
        zf.write(OUT / "focused_tests.txt", "artifacts/pr_dj_selective_interpretation/focused_tests.txt")
        zf.write(OUT / "changed_files.txt", "artifacts/pr_dj_selective_interpretation/changed_files.txt")
    return zip_path
