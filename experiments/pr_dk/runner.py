"""Deterministic PR-DK escalation routing comparison.

This is an experiment-only harness. It does not integrate with gameplay and
disables live interpretation before constructing contracts.
"""
from __future__ import annotations

import csv
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Mapping

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

from experiments.pr_dg.scenarios import (  # noqa: E402
    AMBIGUOUS,
    C1,
    COMPOUND,
    DUMP,
    FACT,
    F1,
    O1,
    S1,
    scenario_table,
)
from experiments.pr_dg.state import combat_bundle, exploration_bundle, followup_bundle, frontier_bundle, state_hash  # noqa: E402
from experiments.pr_dj.runner import _classify, _request_assistance, _signals  # noqa: E402
from game.ordinary_semantic_ownership import establish_ordinary_gameplay_contract, select_ordinary_resolver  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dk_escalation_routing"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _contract(bundle: Any, text: str) -> dict[str, Any]:
    scratch = bundle.clone()
    shell: dict[str, Any] = {"prompt": text, "metadata": {}}
    scene_id = str((scratch.scene.get("scene") or {}).get("id") or scratch.session.get("active_scene_id") or "")
    contract = establish_ordinary_gameplay_contract(
        shell,
        player_text=text,
        session=scratch.session,
        scene_id=scene_id,
        scene=scratch.scene,
        world=scratch.world,
    )
    resolver, family = select_ordinary_resolver(contract, in_combat=bool(scratch.combat.get("in_combat")))
    construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
    return {
        "resolver": resolver,
        "family": family,
        "operation": contract.get("operation"),
        "interlocutor_id": contract.get("interlocutor_id"),
        "dimension": contract.get("dimension"),
        "dimensions": list(contract.get("dimensions") or []),
        "expected_resolution": contract.get("expected_resolution"),
        "referent_provenance": contract.get("referent_provenance"),
        "ambiguous": bool(contract.get("ambiguous")),
        "construction": construction,
    }


def _outside_quotes(text: str) -> str:
    return re.sub(r'"[^"]*"|“[^”]*”', " ", text)


def _independent_checks(text: str, selector: Mapping[str, Any]) -> dict[str, bool]:
    construction = selector.get("construction") if isinstance(selector.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    validation = construction.get("validation_result") if isinstance(construction.get("validation_result"), Mapping) else {}
    raw = _outside_quotes(text)
    low = raw.lower()
    clauses = [part.strip() for part in re.split(r"\b(?:and then|then|and)\b", low) if part.strip()]
    action_families = []
    for clause in clauses:
        families = set()
        if re.search(r"\b(?:walk|go|head|approach|move|step)\b", clause):
            families.add("movement")
        if re.search(r"\b(?:pry|pull|remove|tear|break|force|open|take)\b", clause):
            families.add("object_action")
        if re.search(r"\b(?:ask|tell|say|speak|inquire)\b", clause):
            families.add("social")
        if re.search(r"\b(?:attack|strike|stab|slash|smite)\b", clause):
            families.add("combat")
        action_families.extend(sorted(families))
    distinct_action_families = set(action_families)
    has_compound_action = (
        len(clauses) > 1
        and "movement" in distinct_action_families
        and bool(distinct_action_families & {"object_action", "combat", "social"})
    )
    person_pronouns = re.findall(r"\b(?:him|her|them|the other one|other one)\b", low)
    unresolved_person_reference = bool(person_pronouns) and (
        not selector.get("interlocutor_id")
        or binding.get("status") in {"unresolved", "ambiguous"}
        or selector.get("referent_provenance") in {"unresolved", "ambiguous"}
    )
    candidate_people = [
        row
        for row in construction.get("canonical_candidates") or []
        if isinstance(row, Mapping) and row.get("type") == "interlocutor"
    ]
    multiple_plausible_people = unresolved_person_reference and len({row.get("id") for row in candidate_people}) > 1
    consequential_question = bool(
        selector.get("operation") == "ask"
        and re.search(r"\b(?:assassinate|murder|kill|betray|secret|hidden|poison|steal|ambush)\b", low)
        and re.search(r"\b(?:easier|possible|can|could|would|whether|how)\b", low)
    )
    contract_mismatch = bool(
        selector.get("resolver") in {"travel", "social"}
        and re.search(r"\b(?:pry|pull|remove|break|force|set|give me|update the world)\b", low)
        and selector.get("operation") in {"ask", "act"}
    )
    missing_required_participant = bool(
        selector.get("operation") == "ask"
        and not selector.get("interlocutor_id")
        and (unresolved_person_reference or binding.get("status") in {"unresolved", "ambiguous"})
    )
    unsupported_secondary_action = bool(
        has_compound_action
        and (
            validation.get("status") == "abstained"
            or not construction.get("secondary_operations")
            or not (construction.get("executable_obligations") or {}).get("sequence")
        )
    )
    return {
        "multiple_independent_action_clauses": has_compound_action,
        "unresolved_personal_pronoun": unresolved_person_reference,
        "multiple_plausible_referents": multiple_plausible_people,
        "input_action_contract_mismatch": contract_mismatch,
        "omitted_action_components": has_compound_action and not bool(construction.get("secondary_operations")),
        "missing_required_participants": missing_required_participant,
        "unsupported_secondary_actions": unsupported_secondary_action,
        "consequential_social_interpretation": consequential_question,
    }


def _scenario_specs() -> list[dict[str, Any]]:
    selected = {
        row["scenario_id"]: row
        for row in scenario_table()
        if row["scenario_id"] in {"S1", "C1", "compound", "ambiguous", "declared_canon", "mechanical_dump"}
    }
    specs = [
        {"scenario_id": "S1", "utterance": S1, "factory": selected["S1"]["factory"], "justified": False},
        {"scenario_id": "C1", "utterance": C1, "factory": selected["C1"]["factory"], "justified": True},
        {"scenario_id": "compound", "utterance": COMPOUND, "factory": selected["compound"]["factory"], "justified": True},
        {"scenario_id": "ambiguous", "utterance": AMBIGUOUS, "factory": selected["ambiguous"]["factory"], "justified": True},
        {"scenario_id": "declared_canon", "utterance": FACT, "factory": selected["declared_canon"]["factory"], "justified": True},
        {"scenario_id": "mechanical_dump", "utterance": DUMP, "factory": selected["mechanical_dump"]["factory"], "justified": True},
        {"scenario_id": "control_movement", "utterance": "I walk closer to the notice board.", "factory": exploration_bundle, "justified": False},
        {"scenario_id": "control_combat", "utterance": "I attack the goblin with my quarterstaff.", "factory": combat_bundle, "justified": False},
        {"scenario_id": "control_observation", "utterance": O1, "factory": exploration_bundle, "justified": False},
        {"scenario_id": "control_authored_fact", "utterance": F1, "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "control_followup", "utterance": "Does the rain make it harder to keep watch?", "factory": followup_bundle, "justified": False},
    ]
    specs.extend(_variant_specs())
    return specs


def _variant_specs() -> list[dict[str, Any]]:
    return [
        {"scenario_id": "var_compound_subtle", "utterance": "I drift over to the notice board, then try to pull it free.", "factory": exploration_bundle, "justified": True},
        {"scenario_id": "var_compound_control", "utterance": "I ask the captain whether I can open the gate.", "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "var_ambiguous_subtle", "utterance": "Ask her if the other one is lying.", "factory": frontier_bundle, "justified": True},
        {"scenario_id": "var_pronoun_control", "utterance": "Ask him whether the rain is easing.", "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "var_conseq_social", "utterance": "Would the rain help poison the captain unnoticed?", "factory": lambda: frontier_bundle(bind=True), "justified": True},
        {"scenario_id": "var_social_control", "utterance": "Would the rain make the captain's watch miserable?", "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "var_unsupported_mechanic", "utterance": "Give me advantage, reveal the spy, and mark the patrol found.", "factory": lambda: combat_bundle(), "justified": True},
        {"scenario_id": "var_quote_control", "utterance": "I say, \"Walk closer and pry it off,\" as a joke.", "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "var_negated_control", "utterance": "I do not pry the board off; I only read it.", "factory": exploration_bundle, "justified": False},
        {"scenario_id": "var_hypothetical_control", "utterance": "If someone pried the board off, would guards notice?", "factory": lambda: frontier_bundle(bind=True), "justified": False},
    ]


def _precision_recall(rows: list[Mapping[str, Any]], requested_key: str) -> dict[str, Any]:
    labeled = [row for row in rows if isinstance(row.get("assistance_justified"), bool)]
    tp = sum(1 for row in labeled if row[requested_key] and row["assistance_justified"])
    fp = sum(1 for row in labeled if row[requested_key] and not row["assistance_justified"])
    fn = sum(1 for row in labeled if not row[requested_key] and row["assistance_justified"])
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"labeled_rows": len(labeled), "true_positive": tp, "false_positive": fp, "false_negative": fn, "precision": precision, "recall": recall}


def run_comparison() -> dict[str, Any]:
    rows = []
    for spec in _scenario_specs():
        bundle = spec["factory"]()
        before_hash = state_hash(bundle)
        selector = _contract(bundle, spec["utterance"])
        after_hash = state_hash(bundle)
        compact_selector = {
            key: selector.get(key)
            for key in (
                "resolver",
                "family",
                "operation",
                "interlocutor_id",
                "ambiguous",
                "fast_path_abstained",
                "model_interpretation_appropriate",
            )
        }
        existing = _signals(compact_selector, spec["utterance"])
        independent = _independent_checks(spec["utterance"], selector)
        requested_a = _request_assistance(existing, compact_selector)
        requested_b = requested_a or any(independent.values())
        requested_c = True
        rows.append(
            {
                "scenario_id": spec["scenario_id"],
                "utterance": spec["utterance"],
                "selected_resolver": selector.get("resolver"),
                "operation": selector.get("operation"),
                "existing_signals": existing,
                "independent_checks": independent,
                "assistance_justified": bool(spec["justified"]),
                "pre_mutation_signal": before_hash == after_hash,
                "state_changed": before_hash != after_hash,
                "A_requested": requested_a,
                "B_requested": requested_b,
                "C_requested": requested_c,
                "A_classification": _classify(requested=requested_a, justified=bool(spec["justified"])),
                "B_classification": _classify(requested=requested_b, justified=bool(spec["justified"])),
                "C_classification": _classify(requested=requested_c, justified=bool(spec["justified"])),
                "contract_trace": _trace(selector),
            }
        )
    return {
        "live_provider_calls": 0,
        "rows": rows,
        "metrics": {
            "A": _precision_recall(rows, "A_requested"),
            "B": _precision_recall(rows, "B_requested"),
            "C": _precision_recall(rows, "C_requested"),
        },
    }


def _trace(selector: Mapping[str, Any]) -> dict[str, Any]:
    construction = selector.get("construction") if isinstance(selector.get("construction"), Mapping) else {}
    return {
        "operation": selector.get("operation"),
        "resolver": selector.get("resolver"),
        "interlocutor_id": selector.get("interlocutor_id"),
        "dimension": selector.get("dimension"),
        "dimensions": selector.get("dimensions"),
        "expected_resolution": selector.get("expected_resolution"),
        "referent_provenance": selector.get("referent_provenance"),
        "ambiguous": selector.get("ambiguous"),
        "proposal_source": construction.get("proposal_source"),
        "fast_path_abstained": construction.get("fast_path_abstained"),
        "fast_path_abstention_reason": construction.get("fast_path_abstention_reason"),
        "model_interpretation_appropriate": construction.get("model_interpretation_appropriate"),
        "model_interpreter_invoked": construction.get("model_interpreter_invoked"),
        "interpretation_api_calls": construction.get("interpretation_api_calls"),
        "validation_status": construction.get("validation_status"),
        "validation_result": construction.get("validation_result"),
        "entity_binding": construction.get("entity_binding"),
        "referent_reason": construction.get("referent_reason"),
        "resolution_subject": construction.get("resolution_subject"),
        "secondary_operations": construction.get("secondary_operations"),
        "executable_obligations": construction.get("executable_obligations"),
        "cues": construction.get("cues"),
    }


def generate_reports(*, regression_text: str = "Not run.") -> dict[str, Any]:
    payload = run_comparison()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "routing_payload.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _write_comparison_csv(payload)
    _write_reports(payload, regression_text=regression_text)
    return payload


def _write_comparison_csv(payload: Mapping[str, Any]) -> None:
    cols = [
        "scenario_id",
        "selected_resolver",
        "assistance_justified",
        "A_requested",
        "A_classification",
        "B_requested",
        "B_classification",
        "C_requested",
        "C_classification",
        "existing_signals",
        "independent_checks",
    ]
    with (OUT / "PR-DK_comparison.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({key: json.dumps(row[key], sort_keys=True) if key.endswith("signals") or key.endswith("checks") else row[key] for key in cols})


def _metric_line(metrics: Mapping[str, Any], key: str) -> str:
    item = metrics[key]
    return f"{key}: TP={item['true_positive']} FP={item['false_positive']} FN={item['false_negative']} precision={item['precision']} recall={item['recall']}"


def _write_reports(payload: Mapping[str, Any], *, regression_text: str) -> None:
    metrics = payload["metrics"]
    rows = payload["rows"]
    _write(
        OUT / "PR-DK_investigation_report.md",
        f"""
# PR-DK Investigation Report

Mode: ESCALATION ROUTING INVESTIGATION.

Live provider calls: 0 in the PR-DK harness. `ASHEN_DISABLE_LIVE_INTERPRETATION=1` is set before contract construction.

Git HEAD at start: d31beb7d73dd4fda0f22184a6a69b947b5f470ff.

Initial worktree: dirty before PR-DK. Existing modified areas included prior artifacts, `data/*.json`, many `game/*.py` modules, tests, and `handoff/CURRENT_REVIEW.*`. PR-DK preserves that worktree and only adds experiment/report artifacts plus the requested handoff refresh.

Three-way result over {len(rows)} deterministic rows:

- {_metric_line(metrics, 'A')}
- {_metric_line(metrics, 'B')}
- {_metric_line(metrics, 'C')}

Decision: C - BOTH REQUIRE LIVE COMPARISON.

Rationale: independent deterministic checks materially improve fixture recall versus existing signals, but they add false-positive exposure in ordinary hypotheticals, negations, quotes, and single-focus pronoun follow-ups. Universal interpretation has predictable coverage and large call volume, but PR-DH already showed that interpretation quality and authority validity are not automatic. Deterministic fixture performance alone is therefore insufficient to pick a production strategy.
""",
    )
    missed = [row for row in rows if row["scenario_id"] in {"C1", "compound", "ambiguous"}]
    _write(
        OUT / "PR-DK_failure_reconstruction.md",
        "# PR-DK Failure Reconstruction\n\n"
        + "\n\n".join(_failure_section(row) for row in missed),
    )
    _write(
        OUT / "PR-DK_existing_signal_audit.md",
        """
# PR-DK Existing Signal Audit

Existing signals were populated as boolean fields for every row, but most are derived from the selected contract construction. The fields that fired in PR-DJ were text-backed override/canon signals; the fields intended to catch pronouns, compound action, and referent ambiguity were either false or unavailable in the compact selector.

- `explicit_abstention`: available only if the router reads `construction.fast_path_abstained`; PR-DJ's compact selector placed `fast_path_abstained` at top level, while `_signals` looked under `construction`, so it was effectively ignored.
- `missing_required_entity`: depends on `construction.entity_binding.status`; missed in PR-DJ because the compact selector discarded construction.
- `unresolved_pronoun`: depends on `selector.ambiguous`, so unresolved but non-ambiguous pronoun cases such as S11 are missed.
- `multiple_possible_referents`: depends on `selector.ambiguous` or an explicit ambiguous binding; unresolved addressee/claim states do not count.
- `compound_action`: depends on `secondary_operations` or executable obligations after construction; S10's secondary pry was never represented there.
- `resolver_disagreement`: only catches generation fallback disagreement, not an incomplete specialized resolver choice.
- `unsupported_mechanic`, `attempted_direct_state_override`, `attempted_world_canon_declaration`: populated from raw text and caught the two PR-DJ positives.

Existing data could detect S10's abstention and unresolved entity if construction were passed through, but it could not detect C1's consequential social content or S11's two unresolved personal references without additional checks.
""",
    )
    _write(
        OUT / "PR-DK_independent_checks.md",
        """
# PR-DK Independent Completeness Checks

The minimal checks tested here are independent of the selected resolver label:

- multiple independent action clauses outside quotes;
- unresolved personal pronouns when no addressee is bound;
- multiple plausible interlocutor referents for unresolved personal pronouns;
- mismatch between raw action content and the selected action contract;
- omitted secondary components when the raw text names approach plus manipulation;
- missing required participants for social asks;
- unsupported secondary actions when construction abstained or recorded no executable sequence;
- consequential social interpretation for feasibility questions about serious harm, betrayal, theft, ambush, or hidden consequential content.

These are completeness checks, not execution rules. They can request interpretation or clarification, but they do not authorize state mutation.
""",
    )
    _write(
        OUT / "PR-DK_false_positive_controls.md",
        """
# PR-DK False-Positive Controls

Controls included quoted dialogue, hypothetical actions, negated actions, ordinary compound sentences, single-focus pronouns, combat declarations, movement, harmless social questions, authored factual questions, and conversational follow-ups.

Observed B-policy false-positive pressure:

- Quoted "Walk closer and pry it off" can look like a compound action unless quote spans are removed first.
- Hypothetical "If someone pried..." can look like unsupported object manipulation unless modal/hypothetical framing is honored.
- Negated "I do not pry..." can look like object manipulation unless negation is handled.
- Single-focus "Ask him..." should stay ordinary when discourse has a unique active interlocutor.

The harness removes quoted spans and requires movement plus a second concrete action family for compound detection, but negation and hypothetical framing remain residual risks for production.
""",
    )
    _write(
        OUT / "PR-DK_adversarial_variants.md",
        "# PR-DK Adversarial Variants\n\n"
        + "\n".join(
            f"- {row['scenario_id']}: justified={row['assistance_justified']} A={row['A_classification']} B={row['B_classification']} C={row['C_classification']} :: {row['utterance']}"
            for row in rows
            if row["scenario_id"].startswith("var_")
        ),
    )
    _write(
        OUT / "PR-DK_cost_model.md",
        """
# PR-DK Cost Model

PR-DH provider baseline:

- Candidate B: 6 interpretation calls, 4,414 input tokens, 1,361 output tokens, 5,775 total tokens.
- Candidate C: 16 interpretation calls, 18,983 input tokens, 2,859 output tokens, 21,842 total tokens.
- PR-DH total live interpretation requests: 22 / 24 rows.

Average per interpretation call from PR-DH:

- Candidate B: about 962.5 total tokens per call.
- Candidate C: about 1,365.1 total tokens per call.
- Overall PR-DH: about 992.8 total tokens per call.

Hypothetical calls per 100 player turns:

| Complication rate | Selective calls / 100 | Universal calls / 100 | Selective token overhead at B avg | Universal token overhead at B avg |
| --- | ---: | ---: | ---: | ---: |
| 5% | 5 | 100 | ~4,813 | ~96,250 |
| 15% | 15 | 100 | ~14,438 | ~96,250 |
| 30% | 30 | 100 | ~28,875 | ~96,250 |
| 50% | 50 | 100 | ~48,125 | ~96,250 |

This does not invent provider prices and does not claim full-turn savings. Narration cost remains. Clarification overhead and repeated-call overhead are additional risks; PR-DH Candidate C demonstrated repeated interpretation calls on difficult cases.
""",
    )
    _write(
        OUT / "PR-DK_safety_analysis.md",
        """
# PR-DK Safety Analysis

All compared approaches must preserve:

- authoritative engine execution;
- existing dice and mechanics;
- world-state validation;
- hidden-information boundaries;
- no direct model mutation;
- no model-authored outcomes;
- no interpretation execution without authoritative validation.

Selective routing and universal interpretation differ only in when non-authoritative interpretation metadata is requested. Neither may write saves, mutate state, choose dice, reveal hidden information, or replace resolver validation.
""",
    )
    _write(OUT / "PR-DK_regression_results.md", "# PR-DK Regression Results\n\n" + regression_text)
    _write(
        OUT / "PR-DK_recommendation.md",
        """
# PR-DK Recommendation

1. The router missed the three cases because PR-DJ's compact selector discarded construction data, relied on final ambiguity labels, and lacked independent completeness checks for consequential social content and secondary actions.
2. Existing signals can be repaired partially by passing construction through and reading abstention/entity-binding fields consistently. That does not solve C1.
3. Independent checks materially improve detection by catching C1, S10, and S11 before execution in the deterministic harness.
4. They create false-positive costs around quotes, hypotheticals, negation, and ordinary pronoun follow-ups.
5. Selective routing remains attractive on cost because it can avoid most interpretation calls if complication rates are low or moderate.
6. Universal lightweight interpretation is worth live comparison because selective routing still depends on brittle preflight completeness detection.
7. The smallest next experiment is a no-mutation live comparison over the same PR-DK matrix: selective B-policy calls only when deterministic checks fire, universal calls on every row, both passed through the same adapter and authority validator.

Decision: C - BOTH REQUIRE LIVE COMPARISON.
""",
    )
    _write(
        OUT / "PR-DK_remaining_risks.md",
        """
# PR-DK Remaining Risks

- PR-DK variants are deterministic fixtures, not measured production distributions.
- The independent checks are intentionally small and may under-detect subtle social consequence requests.
- Negation and hypothetical framing need stronger syntax-aware handling before production.
- Universal interpretation may still produce invalid or over-authoritative structures.
- Cost depends on real player-turn complication rates, which are not measured here.
- A manual trace during investigation showed why live interpretation must be disabled explicitly when reconstructing contract construction; the PR-DK harness does this.
""",
    )
    _write(
        OUT / "focused_tests.txt",
        """
python -m pytest tests/test_pr_dk_escalation_routing.py -q
python -m pytest tests/test_pr_dj_selective_interpretation.py -q
python -m pytest tests/test_pr_dg_architecture_preflight.py -q
python -m pytest tests/test_model_routing_escalation.py tests/test_model_routing_runtime.py -q
python -m pytest tests/test_pr_cx_authority_assurance.py tests/test_turn_pipeline_shared.py -q
""",
    )
    _write(
        OUT / "changed_files.txt",
        """
experiments/pr_dk/__init__.py
experiments/pr_dk/runner.py
tests/test_pr_dk_escalation_routing.py
tools/run_pr_dk_investigation.py
artifacts/pr_dk_escalation_routing/*
handoff/CURRENT_REVIEW.md
handoff/CURRENT_REVIEW.zip
""",
    )


def _failure_section(row: Mapping[str, Any]) -> str:
    trace = row["contract_trace"]
    return f"""## {row['scenario_id']}

Raw input: {row['utterance']}

Parsed components:

- operation: {trace.get('operation')}
- resolver: {trace.get('resolver')}
- dimension(s): {trace.get('dimension') or trace.get('dimensions')}
- entity binding: {trace.get('entity_binding')}
- secondary operations: {trace.get('secondary_operations')}
- executable obligations: {trace.get('executable_obligations')}

Construction output:

- proposal source: {trace.get('proposal_source')}
- validation: {trace.get('validation_status')} / {trace.get('validation_result')}
- referent reason: {trace.get('referent_reason')}
- resolution subject: {trace.get('resolution_subject')}

Escalation signals:

- existing: {row['existing_signals']}
- independent: {row['independent_checks']}

Information loss:

{_loss(row)}
"""


def _loss(row: Mapping[str, Any]) -> str:
    sid = row["scenario_id"]
    if sid == "C1":
        return "The ask is resolved as ordinary social dialogue against the inherited guard captain. The consequential feasibility content, assassinating the captain in the rain, is not represented as a protected consequence or unsupported request."
    if sid == "compound":
        return "The raw text contains approach plus pry, but construction records no secondary operation or executable sequence. The selected resolver is travel, so the pry component is discarded before existing routing sees it."
    if sid == "ambiguous":
        return "The fast path validates an ask with confidence dimension while leaving `him` and `the other one` unresolved. Because `ambiguous` remains false, pronoun and multiple-referent signals do not fire."
    return "No loss recorded."


def refresh_current_review(payload: Mapping[str, Any]) -> Path:
    metrics = payload["metrics"]
    text = f"""
# CURRENT REVIEW

PR-DK

MODE:
ESCALATION ROUTING INVESTIGATION

LIVE CALLS:
0 in the PR-DK harness.

PR-DJ inherited decision:
B - PARTIAL PREFLIGHT

Missed-trigger root causes:
Construction was compacted away for existing signals; final resolver labels hid incomplete interpretations; C1 lacked a consequential-social completeness signal; S10 lost the secondary pry component; S11 validated an unresolved pronoun ask without setting ambiguity.

Existing-signal findings:
{_metric_line(metrics, 'A')}

Independent-check findings:
{_metric_line(metrics, 'B')}

False-positive findings:
Quotes, hypotheticals, negation, and single-focus pronouns need explicit controls before production.

Selective-routing performance:
Improved fixture recall, still dependent on brittle deterministic completeness checks.

Universal-interpretation cost model:
Universal policy implies 100 interpretation calls per 100 turns. PR-DH Candidate B averaged about 962.5 total tokens per interpretation call; Candidate C averaged about 1,365.1.

Regression results:
See artifacts/pr_dk_escalation_routing/PR-DK_regression_results.md.

PR-DK decision:
C

Recommended next step:
Run a no-mutation live comparison of B-policy selective calls versus universal calls across the PR-DK matrix, with both outputs validated by the same non-authoritative adapter and authority controls.
"""
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    review_md = handoff / "CURRENT_REVIEW.md"
    review_md.write_text(text.strip() + "\n", encoding="utf-8")
    zip_path = handoff / "CURRENT_REVIEW.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(review_md, "CURRENT_REVIEW.md")
        for path in sorted(OUT.glob("PR-DK_*")):
            zf.write(path, f"artifacts/pr_dk_escalation_routing/{path.name}")
        for name in ("focused_tests.txt", "changed_files.txt", "routing_payload.json"):
            zf.write(OUT / name, f"artifacts/pr_dk_escalation_routing/{name}")
    return zip_path
