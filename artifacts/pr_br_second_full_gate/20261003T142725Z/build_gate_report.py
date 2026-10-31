from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ROWS = {
    "persona_a": [
        ("FAIL", "MEDIUM", "CONTRACT_CONSTRUCTION", "INCORRECT", "Clear compound inspection lost its targets; generic nonresolution did not inspect."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented posting date, official seal, handwriting match, and notice chronology."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented departure timing, altered route, absent signals, and captain updates."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Misbound roster as notice board; invented roster, time, orders, and annotations without names."),
        ("PASS", None, None, "INCORRECT", "Contract was unresolved, but the bounded negative physical search was playable."),
        ("PASS", None, None, "PARTIAL BUT SUFFICIENT", "Missing target binding, but the close crate inspection was reasonably resolved."),
        ("FAIL", "HIGH", "RESOLUTION_EXECUTION", "INCORRECT", "Explicit request to the serjeant became an unaddressed act and dead-end fallback."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented access restrictions and a patrol member bringing news."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented a trouble report and returns through other gates."),
        ("FAIL", "MEDIUM", "DISCOURSE_CONTINUITY", "FULLY CORRECT", "Correct speaker binding, but generic refusal did not reconcile the engine-created contradiction."),
    ],
    "persona_b": [
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Ignored shelter/work and invented footprints as the patrol's last-seen point."),
        ("FAIL", "MEDIUM", "DISCOURSE_CONTINUITY", "INCORRECT", "Lost the unambiguous tavern-runner follow-up and emitted identification fallback."),
        ("PASS", None, None, "FULLY CORRECT", "Watcher gave a bounded answer about personal observation."),
        ("FAIL", "MEDIUM", "ADDRESSEE_BINDING", "INCORRECT", "Lost the active watcher in a direct follow-up."),
        ("PASS", None, None, "FULLY CORRECT", "Reasonable epistemically bounded answer."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "FULLY CORRECT", "Invented Captain Thoran and consequential command and hiring authority."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Persisted invented captain and invented official requirements; malformed quotation."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Invented official assignment, orders, reporting, and deferred payment."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented return timeline and reserved captain details; self-referral."),
        ("FAIL", "HIGH", "ADDRESSEE_BINDING", "INCORRECT", "Captain was explicitly addressed, but serjeant answered and redirected to captain."),
    ],
    "persona_c": [
        ("PASS", None, None, "PARTIAL BUT SUFFICIENT", "Authored northwest-track clue was revealed; no names or additions were reported."),
        ("FAIL", "MEDIUM", "RESOLUTION_EXECUTION", "INCORRECT", "Clear track inspection received generic nonresolution."),
        ("FAIL", "MEDIUM", "CONSEQUENTIAL_AUTHORITY", "FULLY CORRECT", "Reasonable refusal was coupled to unsupported patrol orders."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented physical orders, report point, and dusk-yesterday deadline."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Invented patrol bootprints, hurried movement, broken twigs, and traceable woods route."),
        ("FAIL", "MEDIUM", "RESOLUTION_EXECUTION", "INCORRECT", "Generic fallback ignored marking, movement, blood, and pursuit checks."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Invented fork, split patrol, marker, watchtower, and route evidence."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Invented evidence that the patrol hurried northwest or split."),
        ("FAIL", "MEDIUM", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Repeated unsupported thinning prints and patrol-split evidence."),
        ("FAIL", "HIGH", "MOVEMENT / LOCATION", "INCORRECT", "Reset the character to the already-passed fork after proceeding around a later bend."),
    ],
    "persona_d": [
        ("PASS", None, None, "PARTIAL BUT SUFFICIENT", "Tavern runner reasonably admitted ignorance and redirected to the roster holder."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "PARTIAL BUT SUFFICIENT", "Invented changed route, redirection, causal rationale, and captain procedure."),
        ("PASS", None, None, "INCORRECT", "Response answered as the watcher despite the contract binding the wrong NPC."),
        ("FAIL", "HIGH", "ADDRESSEE_BINDING", "INCORRECT", "Clearly addressed watcher was lost and treated as unidentified."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "FULLY CORRECT", "Invented historical notices, route changes, timing, and census causation."),
        ("FAIL", "HIGH", "CONSEQUENTIAL_AUTHORITY", "INCORRECT", "Invented driver's route report, milestone conditions, and negative eyewitness evidence."),
        ("FAIL", "HIGH", "REFERENT_BINDING", "INCORRECT", "Lost the prior driver and contradicted immediate wagon continuity."),
        ("FAIL", "HIGH", "RESOLUTION_EXECUTION", "PARTIAL BUT SUFFICIENT", "Contract bound the driver, but generation said no driver responded."),
        ("PASS", None, None, "INCORRECT", "No answer at the townhouse was a reasonable bounded outcome despite wrong contract target."),
        ("FAIL", "MEDIUM", "RESOLUTION_EXECUTION", "INCORRECT", "Stale notice target produced generic nonresolution for townhouse-track inspection."),
    ],
}

POST_CONTRACT_RAW = {("persona_a", 5), ("persona_d", 3), ("persona_d", 9)}
TOPIC_OVER_STRUCTURE = {("persona_c", 5), ("persona_c", 7), ("persona_c", 9)}
GENERIC_FALLBACKS = {
    ("persona_a", 1), ("persona_a", 7), ("persona_a", 10),
    ("persona_b", 2), ("persona_b", 4),
    ("persona_c", 2), ("persona_c", 6),
    ("persona_d", 4), ("persona_d", 7), ("persona_d", 8), ("persona_d", 9), ("persona_d", 10),
}
WRONG_ADDRESSEE_ACCEPTS = {("persona_b", 10)}
STALE_INTERLOCUTOR = {("persona_b", 2), ("persona_b", 4), ("persona_d", 4), ("persona_d", 7)}
UNSUPPORTED_IDENTITY = {("persona_b", 6)}
UNSUPPORTED_FACT = {
    ("persona_a", 2), ("persona_a", 3), ("persona_a", 4), ("persona_a", 8), ("persona_a", 9),
    ("persona_b", 1), ("persona_b", 7), ("persona_b", 8), ("persona_b", 9), ("persona_b", 10),
    ("persona_c", 3), ("persona_c", 4), ("persona_c", 5), ("persona_c", 7), ("persona_c", 8), ("persona_c", 9),
    ("persona_d", 2), ("persona_d", 5), ("persona_d", 6),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def event_map(persona: str) -> dict[str, dict]:
    result = {}
    log = ROOT / persona / "isolated_data" / "data" / "session_log.jsonl"
    for line in log.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        text = row.get("player_input")
        if text:
            result[text] = row
    return result


def questions(grade: str, family: str | None) -> dict[str, bool]:
    if grade == "PASS":
        return {str(i): True for i in range(1, 11)}
    failed = {
        "CONTRACT_CONSTRUCTION": {1, 2, 10},
        "CONSEQUENTIAL_AUTHORITY": {6, 10},
        "DISCOURSE_CONTINUITY": {2, 3, 10},
        "ADDRESSEE_BINDING": {1, 3, 4, 10},
        "REFERENT_BINDING": {1, 3, 4, 10},
        "RESOLUTION_EXECUTION": {2, 10},
        "MOVEMENT / LOCATION": {3, 10},
    }.get(family or "", {10})
    return {str(i): i not in failed for i in range(1, 11)}


manual = []
telemetry = []
for persona, reviews in ROWS.items():
    turns = read_json(ROOT / persona / "turns.json")
    events = event_map(persona)
    for turn, review in zip(turns, reviews, strict=True):
        grade, severity, family, contract_quality, note = review
        n = int(turn["turn_number"])
        key = (persona, n)
        contract = turn.get("contract") or {}
        construction = contract.get("construction") or {}
        event = events.get(turn["player_text"], {})
        resolution = event.get("resolution") or {}
        event_meta = resolution.get("metadata") or {}
        manual.append({
            "persona": persona,
            "turn": n,
            "grade": grade,
            "severity": severity,
            "primary_family": family,
            "secondary_families": [],
            "contract_quality": contract_quality,
            "evaluation_questions": questions(grade, family),
            "reviewer_note": note,
        })
        telemetry.append({
            "persona": persona,
            "turn_number": n,
            "player_input": turn.get("player_text"),
            "player_input_length": len(turn.get("player_text") or ""),
            "structural_segmentation": event_meta.get("turn_segmentation") or event_meta.get("segmented_turn"),
            "operative_clauses": construction.get("secondary_operations") or [],
            "contract_construction_source": event_meta.get("contract_construction_source") or construction.get("proposal_source"),
            "interpretation_proposal": turn.get("interpretation_proposal"),
            "structural_frame": construction.get("primary_operation"),
            "coherence_validation_result": construction.get("resolution_subject_coherence"),
            "authoritative_resolution_contract": contract,
            "operation": turn.get("operation"),
            "target": turn.get("canonical_target"),
            "dimension": turn.get("dimension"),
            "requested_addressee": construction.get("requested_addressee"),
            "bound_interlocutor": turn.get("bound_interlocutor"),
            "commitment": construction.get("commitment_status"),
            "topic_content": contract.get("conversational_subject"),
            "resolution_subject": construction.get("resolution_subject"),
            "semantic_owner": event_meta.get("semantic_owner"),
            "selected_resolver": event_meta.get("selected_resolver"),
            "resolver_selection_inputs": {
                "operation": contract.get("operation"),
                "resolution_subject": construction.get("resolution_subject"),
                "interlocutor_id": contract.get("interlocutor_id"),
            },
            "post_contract_raw_text_semantic_influence": key in POST_CONTRACT_RAW,
            "initial_candidate": turn.get("generation_attempt_1"),
            "c19_result": {
                "hard_valid": turn.get("attempt_1_hard_valid"),
                "reasons": turn.get("attempt_1_reasons"),
            },
            "c18_result": {
                "accepted_immutable": turn.get("accepted_immutable"),
                "accepted_emitted_exact_match": turn.get("accepted_emitted_exact_match"),
            },
            "retry_reason": (turn.get("turn_generation_calls") or [{}])[-1].get("retry_reason") if turn.get("regeneration_invoked") else None,
            "retry_output": turn.get("generation_attempt_2"),
            "accepted_response": turn.get("accepted_response_text"),
            "emitted_response": turn.get("final_emitted_response"),
            "accepted_emitted_equality": turn.get("accepted_emitted_exact_match"),
            "state_mutation": resolution.get("state_changes"),
            "discourse_mutation": turn.get("discourse_focus"),
            "incidental_entities_created_or_bound": turn.get("entity_binding"),
            "authoritative_facts_created": resolution.get("discovered_clues") or [],
            "npc_claims_created": [x for x in turn.get("authority_emitted") or [] if x.get("authority_class") == "npc_claim"],
            "location_before_after": ["frontier_gate", (turn.get("persistence") or {}).get("active_scene_id")],
            "manual_grade": grade,
            "evaluator_grade": turn.get("semantic_result"),
            "failure_family": family,
            "reviewer_notes": note,
        })

counts = Counter(row["grade"] for row in manual)
severity = Counter(row["severity"] for row in manual if row["severity"])
contracts = Counter(row["contract_quality"] for row in manual)
evaluator_pass = sum(1 for row in telemetry if row["evaluator_grade"] == "PASS")
agreement = sum(1 for m, t in zip(manual, telemetry, strict=True) if m["grade"] == t["evaluator_grade"])
false_positive = sum(1 for m, t in zip(manual, telemetry, strict=True) if m["grade"] == "FAIL" and t["evaluator_grade"] == "PASS")
false_negative = sum(1 for m, t in zip(manual, telemetry, strict=True) if m["grade"] == "PASS" and t["evaluator_grade"] == "FAIL")
incorrect_visible = sum(1 for row in manual if row["contract_quality"] == "INCORRECT" and row["grade"] == "FAIL")
summaries = [read_json(ROOT / p / "summary.json") for p in ROWS]

summary = {
    "personas_completed": 4,
    "turns_completed": 40,
    "manual_pass_by_persona": {
        p: sum(1 for row in manual if row["persona"] == p and row["grade"] == "PASS") for p in ROWS
    },
    "manual_pass": counts["PASS"],
    "manual_fail": counts["FAIL"],
    "manual_pass_rate": counts["PASS"] / 40,
    "numeric_threshold_met": counts["PASS"] >= 34,
    "evaluator_pass": evaluator_pass,
    "evaluator_manual_agreement": agreement,
    "evaluator_false_positives": false_positive,
    "evaluator_false_negatives": false_negative,
    "contracts": dict(contracts),
    "incorrect_contracts_causing_visible_failure": incorrect_visible,
    "ordinary_gameplay_without_contract": sum(1 for row in telemetry if not row["authoritative_resolution_contract"]),
    "semantic_owner_not_resolution_contract": sum(1 for row in telemetry if row["semantic_owner"] != "resolution_contract"),
    "resolver_before_contract": 0,
    "post_contract_semantic_reinterpretations": len(POST_CONTRACT_RAW),
    "topic_over_structure_errors": len(TOPIC_OVER_STRUCTURE),
    "operative_clauses_lost_through_truncation": 0,
    "contract_resolution_subject_incoherence": 0,
    "accepted_emitted_mismatches": sum(1 for row in telemetry if not row["accepted_emitted_equality"]),
    "post_seal_mutations": 0,
    "structured_envelope_leaks": 0,
    "rejected_response_state_commits": 0,
    "wrong_speaker_addressee_accepts": len(WRONG_ADDRESSEE_ACCEPTS),
    "stale_interlocutor_fallbacks": len(STALE_INTERLOCUTOR),
    "uncommitted_actions_executed": 0,
    "malformed_incidental_person_persistence": 0,
    "unsupported_consequential_identities_accepted": len(UNSUPPORTED_IDENTITY),
    "other_unsupported_consequential_facts_accepted": len(UNSUPPORTED_FACT),
    "npc_claim_promoted_incorrectly_to_truth": 1,
    "player_authored_assertions_encountered": 0,
    "player_authored_assertions_improperly_accepted": 0,
    "generic_fallback_nonresolution_count": len(GENERIC_FALLBACKS),
    "repeated_fallback_count": 8,
    "bounded_incidental_improvisations_observed": 8,
    "bounded_incidental_improvisation_continuity_failures": 2,
    "severity": dict(severity),
    "recurring_failure_mechanisms": 5,
    "recurring_high_severity_mechanisms": 4,
    "all_personas_playable_through_turn_10": True,
    "simulation_location_continuity_acceptable": False,
    "npc_discourse_continuity_acceptable": False,
    "authority_behavior_acceptable": False,
    "human_dm_quality_acceptable": False,
    "gameplay_initial_generation_model_calls": 40,
    "gameplay_retry_generation_model_calls": sum(x["gameplay_retry_calls"] for x in summaries),
    "structured_interpretation_model_calls": sum(x["interpretation_calls"] for x in summaries),
    "synthetic_player_model_calls": 40,
    "evaluator_model_calls": 0,
    "manual_operator_reruns": 0,
    "production_code_modified_during_gate": False,
    "decision": "SECOND FULL 4×10 GATE FAILED — ARCHITECTURAL INVARIANT REGRESSION",
    "human_playtest_readiness": "NOT READY",
    "c28_created": False,
    "pr_br_status": "OPEN — GATE FAILED / PENDING EXTERNAL REVIEW",
}

(ROOT / "manual_review.json").write_text(json.dumps(manual, indent=2, ensure_ascii=False), encoding="utf-8")
(ROOT / "per_turn_telemetry.json").write_text(json.dumps(telemetry, indent=2, ensure_ascii=False), encoding="utf-8")
(ROOT / "scorecard.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

score_lines = ["# 40-turn scorecard", "", "| Turn | Grade | Severity | Family | Contract | Note |", "|---|---|---|---|---|---|"]
for row in manual:
    score_lines.append(
        f"| {row['persona'][-1].upper()}{row['turn']} | {row['grade']} | {row['severity'] or '—'} | "
        f"{row['primary_family'] or '—'} | {row['contract_quality']} | {row['reviewer_note']} |"
    )
(ROOT / "scorecard.md").write_text("\n".join(score_lines) + "\n", encoding="utf-8")

rel_root = ROOT.relative_to(ROOT.parents[2]).as_posix()
supporting = [
    {
        "path": f"{rel_root}/{name}",
        "role": role,
        "why": why,
        "behavioral_evidence": True,
        "human_review_required": review,
    }
    for name, role, why, review in [
        ("freeze.json", "provenance", "Frozen HEAD, worktree, model configuration, personas, and product hashes.", True),
        ("manual_review.json", "manual_review", "Authoritative per-turn human-DM grading and failure classification.", True),
        ("per_turn_telemetry.json", "telemetry", "Normalized C18-C27 and gameplay telemetry for all 40 turns.", True),
        ("scorecard.json", "scorecard", "Machine-readable aggregate gate counts and decision.", True),
        ("scorecard.md", "scorecard", "Human-readable 40-turn scorecard.", True),
    ]
]
for persona in ROWS:
    for name, role, why, review in [
        ("visible.md", "transcript", "Complete player-visible opening and ten-turn transcript.", True),
        ("isolation.json", "isolation", "Clean-session and unique-storage proof.", True),
        ("opening.json", "opening", "Generated opening and opening-call provenance.", True),
        ("review_index.json", "contracts", "Compact contract, routing, validation, and discourse index.", True),
        ("preflight.json", "provenance", "Per-session upstream and environment preflight.", True),
        ("summary.json", "accounting", "Per-session model-call and completion accounting.", True),
        ("generation_calls.json", "candidates", "Initial and bounded-retry generation evidence.", True),
        ("interpretation_calls.json", "interpretation", "Structured-interpretation call evidence.", True),
        ("inbox.jsonl", "player_actions", "Exact synthetic-player inputs, motivations, and intended meanings.", True),
    ]:
        supporting.append({
            "path": f"{rel_root}/{persona}/{name}",
            "role": role,
            "why": f"{persona}: {why}",
            "behavioral_evidence": True,
            "human_review_required": review,
        })
    for n in range(1, 11):
        supporting.append({
            "path": f"{rel_root}/{persona}/turns/turn_{n:02d}.json",
            "role": "turn",
            "why": f"{persona} turn {n}: contract, candidates, validation, emission, state, and authority evidence.",
            "behavioral_evidence": True,
            "human_review_required": True,
        })
for name in ("persona_a.md", "persona_b.md", "persona_c.md", "persona_d.md"):
    supporting.append({
        "path": f"artifacts/pr_br_full_gate/personas/{name}",
        "role": "persona",
        "why": "Frozen synthetic-player behavior description; contains no regression internals.",
        "behavioral_evidence": True,
        "human_review_required": True,
    })

handoff = {
    "campaign_id": "pr-br-second-full-4x10-synthetic-gate",
    "campaign_name": "PR-BR — Second Full 4×10 Synthetic Playability Gate",
    "campaign_date": "2026-10-03",
    "purpose": "Second product-level 4x10 synthetic playability gate after C23-C27. One run; no repair, rerun, human playtest, commit, or push.",
    "objective_status": "OPEN",
    "executive_summary": (
        "Four isolated personas completed 40/40 turns. Manual PASS 8/40 (20%); threshold missed. "
        "Contracts: 6 fully correct, 11 partial-but-sufficient, 23 incorrect. "
        "Accepted/emitted integrity held, but three confirmed post-contract raw-semantic resolutions, "
        "one unsupported consequential identity, 19 other consequential-fact accepts, recurring "
        "addressee loss, generic nonresolution, and location-state failure require Decision D: "
        "SECOND FULL 4×10 GATE FAILED — ARCHITECTURAL INVARIANT REGRESSION. Human playtest not ready."
    ),
    "primary_report": f"{rel_root}/audit.md",
    "evidence_packets": [],
    "changes": {
        "production": [],
        "validation": ["Four updated persona descriptions were frozen before the gate."],
        "tooling": ["Existing validation-only full-gate harness reused without product-behavior changes."],
        "documentation": [f"{rel_root}/audit.md"],
        "generated_artifacts": [f"{rel_root} contains complete second-gate evidence."],
    },
    "testing": {
        "focused": "Not a targeted regression run.",
        "broader": "Not run; this cycle is the authorized fresh 4x10 product gate.",
        "full_suite": "Not run.",
        "runtime_validation": "4 isolated sessions and exactly 10 completed gameplay turns each.",
        "model_runtime_boundary": "4 opening, 40 gameplay initial, 11 retry, 18 interpretation, 40 synthetic-player, 0 evaluator-model calls.",
        "new_regressions": "Post-contract semantic closure, consequential authority, addressee continuity, fallback competence, and movement persistence failed.",
        "pre_existing_failures": "No historical transcript or targeted phrase was replayed.",
    },
    "decisions_requiring_human_review": [
        "Whether the population justifies one final repair, broader redesign, or a different strategy.",
        "Whether declared resolution-contract ownership can be trusted while downstream raw semantics still control output.",
        "PR-BR remains open; human playtest is not authorized.",
    ],
    "known_problems": {
        "campaign_specific": [
            "Manual playability 8/40.",
            "Three confirmed post-contract raw-semantic resolutions.",
            "One unsupported consequential identity and 19 other consequential-fact accept events.",
            "Twenty-three incorrect contracts; twenty caused visible failure.",
            "C10 location reset after unsupported prose-only exploration.",
        ],
        "pre_existing": ["Working tree was already dirty and is fully frozen in freeze.json."],
    },
    "missing_concepts": [],
    "does_not_prove": [
        "Does not authorize human playtest.",
        "Does not authorize C28 or another repair continuation.",
        "Does not prove semantic ownership from telemetry labels alone.",
    ],
    "recommended_next_step": "External failure-population review. Do not repair, rerun, create C28, start PR-BS, commit, or push from this gate.",
    "supporting_files": supporting,
}
(ROOT / "handoff_config.json").write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
