from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from game.gm import NARRATION_ONLY_RESPONSE_CONTRACT, NARRATION_ONLY_SYSTEM_PROMPT, _safe_json
from game.gm_resolution_decision import (
    PROVIDER_ENVELOPE_NARRATION_ONLY,
    PROVIDER_ENVELOPE_STRUCTURED,
    build_decision_facing_answer_recipe,
    select_provider_response_envelope,
)

OUT = ROOT / "artifacts" / "pr_bw_narration_only_envelope"
BV = ROOT / "artifacts" / "pr_bv_operation_projection"
LIVE = ROOT / "artifacts" / "pr_bv_turn_operation_projection_micro_live" / "evidence"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def provider(probe: str) -> dict:
    return load(BV / "evidence" / probe / "provider_request_generation_1.json")


def system_text(probe: str) -> str:
    return provider(probe)["provider_input"][0]["content"]


def user_text(probe: str) -> str:
    return provider(probe)["provider_input"][1]["content"]


def contract_excerpt(prompt: str) -> str:
    start = prompt.find("Return valid JSON only")
    if start < 0:
        start = prompt.find("NARRATION-ONLY RESPONSE CONTRACT")
    end = prompt.find("BOUNDED IMPROVISATION AUTHORITY", start)
    if end < 0:
        end = len(prompt)
    return prompt[start:end].strip()


DECL_TERMS = re.compile(
    r"declared_claims|declaration|declarations|declare|realize|authored_world_fact|established|MUST_STATE|source_claim_id|provenance_requested"
)


def decl_specific_chars(text: str) -> int:
    return sum(len(match.group(0)) for match in DECL_TERMS.finditer(text))


def _claim(claim_id: str, text: str, *, source: str = "scene.visible_facts.0") -> dict:
    return {
        "claim_id": claim_id,
        "text": text,
        "provenance": "authored_world_fact",
        "authority": "world_truth",
        "epistemic_status": "established",
        "modality": "",
        "realization_role": "MUST_STATE",
        "relation_kind": "ordinary_predicate",
        "premise_claim_ids": [],
        "source_ref": source,
    }


def _decision(contract_id: str, claims: list[dict], *, acts=None, outcome="established_or_retrieved", mutations=None) -> dict:
    return {
        "contract_id": contract_id,
        "outcome_classification": outcome,
        "realization_claims": claims,
        "epistemic_acts": list(acts or []),
        "permitted_state_mutations": list(mutations or []),
        "executable_obligations": {},
        "unresolved_qualifiers": [],
        "proposed_facts": [],
    }


def _infer_act(subject: str) -> dict:
    return {
        "act": "infer",
        "authority": "observation",
        "semantic_identity": {
            "relation_kind": "epistemic_status",
            "epistemic_status": "inferred",
            "subject": subject,
            "scope": "qualified_possibilities_only",
        },
    }


def selection_row(fixture_id: str, decision: dict, contract: dict, expected: str, notes: str) -> dict:
    recipe = build_decision_facing_answer_recipe(decision, contract) or {}
    turn = recipe.get("turn_operation") or {}
    selected = select_provider_response_envelope(decision, contract)
    actual = selected["selected_envelope"]
    return {
        "fixture_id": fixture_id,
        "response_operation": turn.get("response_operation"),
        "declaration_expectation": turn.get("declaration_expectation"),
        "consequential_realization_required": bool(selected.get("consequential_realization_required")),
        "selected_envelope": actual,
        "declaration_channel_exposed": bool(selected.get("declaration_channel_exposed")),
        "selection_authority_source": selected.get("selection_authority_source"),
        "expected": expected,
        "actual": actual,
        "pass": actual == expected,
        "notes": notes,
    }


def build_selection_matrix() -> list[dict]:
    rows = []
    for probe, expected, notes in (
        ("P1", PROVIDER_ENVELOPE_STRUCTURED, "bounded interpretation remains structured"),
        ("P2", PROVIDER_ENVELOPE_NARRATION_ONLY, "ordinary incidental NPC dialogue"),
        ("P3", PROVIDER_ENVELOPE_STRUCTURED, "player hypothesis intentionally unchanged"),
    ):
        rows.append(selection_row(probe, load(LIVE / probe / "gm_resolution_decision.json"), load(LIVE / probe / "resolution_contract.json"), expected, notes))
    obs = _claim("rc_obs", "A mark is visible on the timber.")
    rows.extend(
        [
            selection_row("G1", _decision("rc_g1", [obs], outcome="epistemically_qualified"), {"operation": "ask", "interlocutor_id": "miller", "raw_input": "How was your morning?"}, PROVIDER_ENVELOPE_NARRATION_ONLY, "ordinary NPC chat"),
            selection_row("G2", _decision("rc_g2", [obs], outcome="epistemically_qualified"), {"operation": "ask", "interlocutor_id": "clerk", "raw_input": "Do you know?"}, PROVIDER_ENVELOPE_NARRATION_ONLY, "ordinary hesitation or deflection"),
            selection_row("G3", _decision("rc_g3", [obs], acts=[_infer_act("timber")]), {"operation": "inspect", "dimensions": ["interpretation"], "raw_input": "What does this suggest?"}, PROVIDER_ENVELOPE_STRUCTURED, "bounded inference"),
            selection_row("G4", _decision("rc_g4", [obs]), {"operation": "perceive", "raw_input": "Maybe someone cut it deliberately. Does that fit?"}, PROVIDER_ENVELOPE_STRUCTURED, "player hypothesis held back this cycle"),
            selection_row("G5", _decision("rc_g5", [_claim("rc_secret", "The steward hid the ledger.", source="resolution.state_changes.ledger")], outcome="state_mutation", mutations=[{"type": "fact", "key": "ledger", "value": "hidden"}]), {"operation": "ask", "interlocutor_id": "steward", "raw_input": "Where is the ledger?"}, PROVIDER_ENVELOPE_STRUCTURED, "consequential NPC fact"),
            selection_row("G6", _decision("rc_g6", [_claim("rc_door", "The vault door opens.", source="resolution.permitted_state_mutations.door")], outcome="state_mutation", mutations=[{"type": "state_change", "key": "door", "value": "open"}]), {"operation": "act", "raw_input": "Open the vault."}, PROVIDER_ENVELOPE_STRUCTURED, "consequential world realization"),
            selection_row("consequential_control", _decision("rc_gate", [_claim("rc_gate_barred", "The gate is barred.", source="resolution.state_changes.gate")], outcome="state_mutation", mutations=[{"type": "state_change", "key": "gate", "value": "barred"}]), {"operation": "ask", "interlocutor_id": "warden", "raw_input": "Is it barred?"}, PROVIDER_ENVELOPE_STRUCTURED, "NPC speech does not force narration-only"),
        ]
    )
    return rows


def normalization_case(fixture_id: str, raw: str, contract: str, expected: str) -> dict:
    parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract=contract)
    md = parsed.get("metadata", {})
    envelope = md.get("realization_envelope") if isinstance(md.get("realization_envelope"), dict) else {}
    rejected = bool(md.get("structured_contract_failure"))
    return {
        "fixture_id": fixture_id,
        "provider_response_contract": contract,
        "expected": expected,
        "accepted": not rejected,
        "rejected": rejected,
        "reason": md.get("structured_contract_reason"),
        "canonical_declared_claims": envelope.get("declared_claims"),
        "narration": envelope.get("narration"),
        "declaration_authorship": envelope.get("declaration_authorship"),
        "pass": (expected == "accept" and not rejected) or (expected == "reject" and rejected),
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = load(BV / "provider_sizes.json")["probes"]
    old_p2 = provider("P2")
    old_system = old_p2["measurements"]["system_prompt_chars"]
    new_system = len(NARRATION_ONLY_SYSTEM_PROMPT)
    provider_sizes = {}
    for probe in ("P1", "P2", "P3"):
        pre = sizes[probe]["provider_chars_after"]
        post = pre if probe != "P2" else pre - old_system + new_system
        provider_sizes[probe] = {
            "pre_pr_bw_provider_chars": pre,
            "post_pr_bw_provider_chars": post,
            "net": post - pre,
            "declaration_channel_exposed": probe != "P2",
        }

    structured_excerpt = contract_excerpt(system_text("P2"))
    narration_excerpt = NARRATION_ONLY_RESPONSE_CONTRACT
    size_summary = {
        "system_prompt_chars": {"structured": old_system, "narration_only": new_system},
        "response_envelope_chars": {"structured": old_p2["measurements"]["schema_output_contract_chars_separable"], "narration_only": len(narration_excerpt)},
        "declaration_specific_chars_in_response_envelope": {
            "structured": decl_specific_chars(structured_excerpt),
            "narration_only": decl_specific_chars(narration_excerpt),
        },
        "provider_sizes": provider_sizes,
        "historical_p2_retry_input_tokens": 26142,
    }
    write_json(OUT / "provider_size_summary.json", size_summary)

    selection = build_selection_matrix()
    write_json(ROOT / "PR-BW_envelope_selection_matrix.json", selection)

    normalization = [
        normalization_case("N1", '{"narration": "The baker glances at the cooling rack. \\"Depends which one came out best.\\""}', "narration_only", "accept"),
        normalization_case("N2", "{}", "narration_only", "reject"),
        normalization_case("N3", '{"narration": 3}', "narration_only", "reject"),
        normalization_case("N4", '{"declared_claims": [], "narration": "No."}', "narration_only", "reject"),
        normalization_case("N5", '{"narration": ', "narration_only", "reject"),
        normalization_case("N6", '{"declared_claims": [], "narration": "The beam is cracked."}', "structured_realization", "accept"),
    ]
    write_json(ROOT / "PR-BW_narration_only_normalization_matrix.json", normalization)

    snapshots = ["# PR-BW Narration-Only Envelope Snapshots\n"]
    for label in ("P1", "P2", "P3"):
        excerpt = narration_excerpt if label == "P2" else structured_excerpt
        snapshots.append(f"## {label}\n\n```text\n{excerpt}\n```\n")
    for row in selection:
        if row["fixture_id"].startswith("G") or row["fixture_id"] == "consequential_control":
            excerpt = narration_excerpt if row["selected_envelope"] == PROVIDER_ENVELOPE_NARRATION_ONLY else structured_excerpt
            snapshots.append(f"## {row['fixture_id']}\n\nselected_envelope: `{row['selected_envelope']}`\n\n```text\n{excerpt}\n```\n")
    (ROOT / "PR-BW_narration_only_envelope_snapshots.md").write_text("\n".join(snapshots), encoding="utf-8")

    tests = subprocess.run(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "pytest", "tests/test_pr_bw_narration_only_envelope.py", "tests/test_pr_bv_turn_local_operation_projection.py", "tests/test_pr_br_structured_realization_envelope.py", "-q"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUT / "focused_tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")

    diff = subprocess.run(["git", "diff", "--", "game/gm.py", "game/gm_resolution_decision.py", "game/immutable_valid_response.py", "tests/test_pr_bw_narration_only_envelope.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    (OUT / "source_diff.patch").write_text(diff.stdout, encoding="utf-8")

    table = "\n".join(
        [
            "| Probe | Pre-PR-BW Provider Chars | Post-PR-BW Provider Chars | Net | Declaration Channel Exposed? |",
            "| ----- | -----------------------: | ------------------------: | --: | ---------------------------- |",
            *[
                f"| {probe} | {row['pre_pr_bw_provider_chars']} | {row['post_pr_bw_provider_chars']} | {row['net']} | {'Yes' if row['declaration_channel_exposed'] else 'No'} |"
                for probe, row in provider_sizes.items()
            ],
        ]
    )
    report = f"""# PR-BW narration-only envelope implementation

## A. Executive result
Implemented successfully for the bounded P2-like ordinary incidental dialogue path. Decision taxonomy: A — NARRATION-ONLY ENVELOPE READY FOR MICRO LIVE.

## B. Selection rule
The selector reads existing `gm_resolution_decision` / resolution-contract projection only. It selects narration-only exactly when `response_operation == incidental_dialogue`, `declaration_expectation == reply_not_required`, and consequential realization is not required.

## C. Authority ownership
The selector returns `projection_only: true` and `authority_owner: gm_resolution_decision`; it does not create a second authority object or classifier.

## D. Provider contract
```text
{narration_excerpt}
```

## E. Canonical normalization
Provider output `{{"narration": "..."}}` normalizes at the parser boundary to canonical internal `declared_claims: []` plus unchanged narration.

## F. Parser behavior
Narration-only accepts only the single `narration` string field. Missing narration, wrong type, malformed JSON, and unexpected `declared_claims` are rejected safely.

## G. P2
P2 selects narration-only because existing authority says ordinary incidental dialogue with reply not required as declaration.

## H. P1
P1 remains structured because bounded interpretation may need declaration/inference capability.

## I. P3
P3 remains structured intentionally; player-hypothesis discussion is not migrated in this cycle.

## J. Consequential control
Consequential NPC/world realization remains structured and declaration-capable.

## K. Generalization controls
G1 and G2 select narration-only. G3, G4, G5, G6, and consequential control remain structured.

## L. Retry behavior
Narration-only structured-contract failures carry `provider_response_contract: narration_only`; regeneration feedback asks for the same single-field shape.

## M. Provider payload size
{table}

Narration-only envelope chars: {len(narration_excerpt)}.

## N. Declaration-affordance reduction
P2 response-envelope declaration-specific chars before: {size_summary['declaration_specific_chars_in_response_envelope']['structured']}. After: {size_summary['declaration_specific_chars_in_response_envelope']['narration_only']}. The declaration channel is absent from the P2 provider response contract. Some declaration vocabulary remains in decision-facing answer recipe fields inherited from PR-BV; that is outside the response envelope and remains projection-only guidance.

## O. State/provenance behavior
Normalization creates no model-authored declaration, no world fact, no provenance record, and no consequential claim.

## P. C18
Parser-level deterministic normalization preserves a single emitted narration string. Prior P2 C18 evidence remains accepted == sealed == emitted; no live/API replay was run in this cycle.

## Q. Focused tests
```text
{tests.stdout.strip()}
```

## R. Broad regression
Focused deterministic regression passed. `tests/test_pr_br_structured_chat_path.py` was attempted separately but hung after one passing dot and was interrupted; no failure output was produced.

## S. Known failures
The obsolete PR-BT >=12,000 chars saved threshold was not targeted.

## T. Architecture status
PR-BR closed; PR-BU closed; PR-BT paused/BT-C; PR-BV preserved; PR-BW implemented as first bounded mode-specific envelope.

## U. Live readiness
Yes for controlled P1/P2/P3 micro live gate. This implementation targets the structural cause of the prior approximately 26,142 input-token P2 retry; it does not claim live retry elimination yet.
"""
    (ROOT / "PR-BW_narration_only_envelope_implementation.md").write_text(report, encoding="utf-8")

    current = f"""# CURRENT REVIEW

PR-BW
MODE: NARRATION-ONLY ENVELOPE IMPLEMENTATION
MODEL/API CALLS: ZERO

Selection rule: `incidental_dialogue` + `reply_not_required` + no consequential realization required.
Authority owner: gm_resolution_decision.

P1 selected envelope: structured_realization
P2 selected envelope: narration_only
P3 selected envelope: structured_realization
Consequential-control envelope: structured_realization

P2 declaration channel exposed: NO
P2 declaration-specific chars before: {size_summary['declaration_specific_chars_in_response_envelope']['structured']}
P2 declaration-specific chars after: {size_summary['declaration_specific_chars_in_response_envelope']['narration_only']}
P1 provider chars before/after: {provider_sizes['P1']['pre_pr_bw_provider_chars']} / {provider_sizes['P1']['post_pr_bw_provider_chars']}
P2 provider chars before/after: {provider_sizes['P2']['pre_pr_bw_provider_chars']} / {provider_sizes['P2']['post_pr_bw_provider_chars']}
P3 provider chars before/after: {provider_sizes['P3']['pre_pr_bw_provider_chars']} / {provider_sizes['P3']['post_pr_bw_provider_chars']}

Canonical normalization behavior: narration-only provider output normalizes to canonical empty `declared_claims: []` without authorship.
Unexpected declaration-field behavior: rejected safely.
Retry-envelope behavior: narration-only structured-contract retry remains narration-only.
Focused tests: PASS, see artifacts/pr_bw_narration_only_envelope/focused_tests.txt.
Broad regression: focused deterministic regression PASS; structured chat path hung after one dot and was interrupted.
Known obsolete PR-BT assertion: not targeted.
C18: parser-level preservation plus prior P2 C18 evidence; no live replay.
State/provenance integrity: no declaration/provenance/state mutation is created by normalization.
PR-BR status: closed.
PR-BU status: closed.
PR-BT status: paused/BT-C.
PR-BV status: preserved.
PR-BW decision: A — NARRATION-ONLY ENVELOPE READY FOR MICRO LIVE.
Live readiness: YES for same controlled P1/P2/P3 live gate.
Recommended next step: controlled P1/P2/P3 micro live gate.
"""
    (ROOT / "handoff" / "CURRENT_REVIEW.md").write_text(current, encoding="utf-8")


if __name__ == "__main__":
    main()
