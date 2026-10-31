"""PR-BU zero-call narration-validator diagnostic.

Imports production helpers and runs them. Does not modify production behavior
and does not call a model or gameplay API.
"""
from __future__ import annotations

import json
from pathlib import Path

from game import gm_resolution_decision as g
from game.proposition_authority import epistemic_frame

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "artifacts" / "pr_bt_selective_epistemic_restoration_final_micro_live" / "evidence"
OUT = Path(__file__).resolve().parent / "diagnostic_output.json"

P1_NARRATION = (
    "The bell's wooden yoke is visibly split, and its leather hanger is torn. "
    "This damage might suggest the bell has been subjected to significant stress or prolonged neglect, "
    "perhaps due to heavy use or an external force acting upon it."
)
P1_SENTENCE = (
    "This damage might suggest the bell has been subjected to significant stress or prolonged neglect, "
    "perhaps due to heavy use or an external force acting upon it."
)
P1_DECLARATION = (
    "The split wooden yoke and torn leather hanger might indicate the bell has been under significant stress "
    "or neglect, possibly from heavy use or an external force."
)
P3_NARRATION = (
    "The bell's wooden yoke is indeed split, and its leather hanger is torn. "
    "These visible damages could be consistent with being deliberately cut, but without additional evidence, "
    "that motive remains uncertain."
)
P3_SENTENCE = (
    "These visible damages could be consistent with being deliberately cut, but without additional evidence, "
    "that motive remains uncertain."
)
P3_RETRY = (
    "The bell's wooden yoke is split, and its leather hanger is torn. "
    "These damages are clear, but whether they were made deliberately cannot be determined from what is visible here."
)
CORPUS = "The bell's wooden yoke is split.\nThe bell's leather hanger is torn.\nA bronze bell hangs from a timber frame.\nChapel belfry"


def _load(rel: str):
    return json.loads((EVIDENCE / rel).read_text(encoding="utf-8"))


def _match(pattern, text: str) -> str:
    found = pattern.search(text or "")
    return found.group(0) if found else ""


def _summarize(claims) -> dict:
    return {
        "hard_reject": any(not claim.authorized for claim in claims),
        "reason_codes": sorted({code for claim in claims for code in claim.reason_codes}),
        "authorized_flags": [claim.authorized for claim in claims],
        "claims": [
            {
                "authorized": claim.authorized,
                "reason_codes": list(claim.reason_codes),
                "relation_kind": claim.relation_kind,
                "provenance": claim.provenance,
                "epistemic_status": claim.epistemic_status,
            }
            for claim in claims
        ],
    }


def _classify(sentence: str, decision, corpus: str = CORPUS, response: str = "") -> dict:
    claims = g.audit_narrated_claims(
        sentence,
        decision=decision,
        authored_corpus=corpus,
        response_text=response or sentence,
    )
    fact = g.classify_narrated_fact(
        sentence,
        decision=decision,
        authored_corpus=corpus,
        response_text=response or sentence,
    )
    summary = _summarize(claims)
    if fact is None:
        actual = "no_claim"
    elif fact.authorized:
        actual = "accept"
    else:
        actual = "reject"
    summary["actual"] = actual
    summary["fact_reasons"] = list(fact.reason_codes) if fact is not None else []
    summary["fact_authorized"] = None if fact is None else bool(fact.authorized)
    return summary


def _recognizers(sentence: str, decision, corpus: str = CORPUS) -> dict:
    ground = g._decision_ground(corpus, decision)
    definites = []
    for match in g._DEFINITE_PHRASE_RE.finditer(sentence or ""):
        tokens = []
        for raw in __import__("re").findall(r"[a-z']+", match.group(1).lower()):
            token = raw.replace("'s", "").replace("'", "")
            if len(token) < 5 or token in g._DEFINITE_STOP:
                continue
            tokens.append({"token": token, "in_ground": token in ground})
        definites.append({"span": match.group(0)[:80], "tokens": tokens})
    return {
        "epistemic_frame": epistemic_frame(sentence),
        "is_claim_or_uncertain": g._is_claim_or_uncertain(sentence),
        "attributed_source": g._attributed_epistemic_source(sentence, sentence),
        "decision_allows_inference": g._decision_allows_inference(decision),
        "decision_allows_epistemic_limit": g._decision_allows_epistemic_limit(decision),
        "authorized_epistemic_limit": g._authorized_epistemic_limit(sentence, decision),
        "qualified_inference": _match(g._QUALIFIED_INFERENCE_RE, sentence),
        "generated_lead": _match(g._GENERATED_LEAD_RE, sentence),
        "specific_lead": _match(g._SPECIFIC_LEAD_RE, sentence),
        "unknown_slot": _match(g._UNKNOWN_SLOT_RE, sentence),
        "epistemic_limit": _match(g._EPISTEMIC_LIMIT_RE, sentence),
        "epistemic_parent": _match(g._EPISTEMIC_PARENT_REALIZATION_RE, sentence),
        "uncertain_frame": _match(g._UNCERTAIN_FRAME_RE, sentence),
        "narrator_modal": _match(g._NARRATOR_MODAL_RE, sentence),
        "nonassertion": _match(g._NONASSERTION_FRAME_RE, sentence),
        "cause_fill": _match(g._CAUSE_FILL_RE, sentence),
        "causal_relation": _match(g._CAUSAL_RELATION_RE, sentence),
        "event_cause": _match(g._EVENT_CAUSE_ATTRIBUTION_RE, sentence),
        "event_history": _match(g._EVENT_HISTORY_ASSERTION_RE, sentence),
        "definite_history": _match(g._DEFINITE_HISTORY_RE, sentence),
        "actor": _match(g._ACTOR_ATTRIBUTION_RE, sentence),
        "agent_fill": _match(g._AGENT_FILL_RE, sentence),
        "time_fill": _match(g._TIME_FILL_RE, sentence),
        "certainty_upgrade": _match(g._CERTAINTY_UPGRADE_RE, sentence),
        "evidential": _match(g._EVIDENTIAL_RELATION_RE, sentence),
        "stateful": _match(g._STATEFUL_ASSERTION_RE, sentence),
        "ungrounded_definite": g._has_ungrounded_definite(sentence, ground),
        "unsupported_narrator_lead": g._unsupported_narrator_lead(sentence, corpus, decision, sentence),
        "slot_fill_reasons": g._slot_fill_reasons(sentence, decision),
        "relationship_residuals": [c.reason_codes for c in g._relationship_residual_claims(sentence, decision)],
        "ordinary_residuals": g._ordinary_residual_reasons(sentence, decision),
        "structured_consequential": g._structured_consequential_reasons(sentence),
        "covered_rows": [row.get("text") for row in g._authorized_rows_for_sentence(sentence, decision)],
        "definites": definites,
        "unresolved_qualifiers": list((decision or {}).get("unresolved_qualifiers") or []),
    }


def _flow(sentence: str, decision, corpus: str = CORPUS) -> list[dict]:
    """Mirror audit_narrated_claims branch order. Records the first terminal return."""
    text = sentence
    steps: list[dict] = []

    def add(name: str, taken: bool, terminal: bool, detail: str = "") -> bool:
        steps.append(
            {
                "function": name,
                "taken": taken,
                "terminal": taken and terminal,
                "continues": not (taken and terminal),
                "detail": detail,
            }
        )
        return taken and terminal

    if add(
        "attributed_uncertain_claim_return",
        g._is_claim_or_uncertain(text) and g._attributed_epistemic_source(text, text),
        True,
        "epistemically_qualified",
    ):
        return steps
    if add(
        "authorized_epistemic_limit_return",
        g._authorized_epistemic_limit(text, decision),
        True,
        "authorized_epistemic_limit",
    ):
        return steps
    lead = g._unsupported_narrator_lead(text, corpus, decision, text)
    add("unsupported_narrator_lead_append", lead, False, "appends unauthorized claim; does not return")
    inference = (
        g._decision_allows_inference(decision)
        and bool(g._QUALIFIED_INFERENCE_RE.search(text))
        and not g._GENERATED_LEAD_RE.search(text)
        and not g._SPECIFIC_LEAD_RE.search(text)
    )
    if add("authorized_qualified_inference_return", bool(inference), True, "returns before cause/history residuals"):
        return steps
    if add("explicit_nonassertion_return", bool(g._NONASSERTION_FRAME_RE.search(text)), True, "explicit_nonassertion"):
        return steps
    early_slots = g._slot_fill_reasons(text, decision)
    if add(
        "interrogative_return",
        g._is_interrogative(text) and "unauthorized_qualifier:location" not in early_slots,
        True,
        "interrogative_not_assertion",
    ):
        return steps
    add("unknown_slot_append", bool(g._UNKNOWN_SLOT_RE.search(text)), False, "unknown_cause_actor_or_time")
    add("relationship_residuals", bool(g._relationship_residual_claims(text, decision)), False, "causal/evidential/certainty")
    add("slot_fill", bool(early_slots), False, ",".join(early_slots))
    add("structured_semantic_rejection", bool(g._structured_semantic_rejection(text, decision)), False, "")
    add("consequential_or_history_tail", True, False, "falls through to residual/legacy classification")
    return steps


def _with_slots(decision: dict, slots: list[str]) -> dict:
    out = dict(decision)
    out["unresolved_qualifiers"] = list(slots)
    return out


def _case(case_id, category, text, authority, expected, notes, decision, corpus=CORPUS):
    got = _classify(text, decision, corpus, text)
    rec = _recognizers(text, decision, corpus)
    raw_actual = got["actual"]
    actual = "accept_by_omission" if raw_actual == "no_claim" else raw_actual
    reasons = got["fact_reasons"] or got["reason_codes"]
    passed = actual in {"accept", "accept_by_omission"}
    false_accept = expected == "reject" and passed
    false_reject = expected == "accept" and actual == "reject"
    ambiguous = expected == "ambiguous"
    if ambiguous:
        false_accept = False
        false_reject = False
    if raw_actual == "no_claim":
        notes = notes + " No claim was emitted, so the narration audit does not reject the sentence."
    path = "none"
    for step in _flow(text, decision, corpus):
        if step["terminal"]:
            path = step["function"]
            break
        if step["taken"]:
            path = step["function"]
    causes = []
    if false_accept and path == "authorized_qualified_inference_return":
        causes.append("C")
        causes.append("D")
    if rec["unknown_slot"] and rec["ungrounded_definite"] is False and "uncertain" not in rec["unknown_slot"] and "unclear" in rec["unknown_slot"]:
        causes.append("B")
    if (not rec["unknown_slot"]) and rec["epistemic_parent"] and actual == "reject":
        causes.append("B")
    if rec["certainty_upgrade"] and any(word in text.lower() for word in ("not ", "cannot", "can't", "no ")):
        causes.append("E")
    if false_accept or false_reject:
        if "C" not in causes and path.endswith("_return"):
            causes.append("C")
        if "D" not in causes:
            causes.append("D")
    return {
        "case_id": case_id,
        "semantic_category": category,
        "text": text,
        "authority_setup": authority,
        "expected_classification": expected,
        "actual_classification": actual,
        "rejection_acceptance_path": path,
        "reason_codes": reasons,
        "relevant_recognizers": {
            "qualified_inference": rec["qualified_inference"],
            "uncertainty_frame": rec["uncertain_frame"],
            "unknown_slot": rec["unknown_slot"],
            "epistemic_limit": rec["epistemic_limit"],
            "epistemic_parent": rec["epistemic_parent"],
            "certainty_upgrade": rec["certainty_upgrade"],
            "lead": rec["unsupported_narrator_lead"],
            "ungrounded_definite": rec["ungrounded_definite"],
            "cause_fill": rec["cause_fill"],
            "causal_relation": rec["causal_relation"],
            "hypothesis_frame": "could" in rec["uncertain_frame"] or "might" in rec["uncertain_frame"] or "perhaps" in rec["uncertain_frame"],
            "narrator_modal": rec["narrator_modal"],
        },
        "false_accept": false_accept,
        "false_reject": false_reject,
        "ambiguous": ambiguous,
        "root_cause_category": causes,
        "notes": notes,
        "skipped_if_early_return": {
            "slot_fill_reasons": rec["slot_fill_reasons"],
            "relationship_residuals": rec["relationship_residuals"],
            "ordinary_residuals": rec["ordinary_residuals"],
        },
    }


def main() -> None:
    p1 = _load("P1/gm_resolution_decision.json")
    p3 = _load("P3/gm_resolution_decision.json")
    p1_declared = [
        {
            "declaration_id": "inf_1",
            "declaration_mode": "propose",
            "source_claim_id": None,
            "premise_claim_ids": ["rc_db5ec0aa65c3", "rc_b31ecb1fd1c7"],
            "semantic_identity": {},
            "provenance_requested": "gm_inference",
            "epistemic_status": "inferred",
            "modality": "possible",
            "realization_role": "MAY_STATE",
            "relation_kind": "epistemic_status",
            "text": P1_DECLARATION,
        }
    ]
    declaration = g.validate_declared_claims_against_decision(p1_declared, decision=p1)
    effective = g._decision_with_accepted_declarations(p1, declaration.get("accepted_claims"))
    p1_envelope = g.audit_realization_envelope_against_decision(
        narration=P1_NARRATION,
        declared_claims=p1_declared,
        decision=p1,
        authored_corpus=CORPUS,
    )
    p3_envelope = g.audit_realization_envelope_against_decision(
        narration=P3_NARRATION,
        declared_claims=[],
        decision=p3,
        authored_corpus=CORPUS,
    )
    p3_retry = g.audit_narration_against_decision(P3_RETRY, decision=p3, authored_corpus=CORPUS)
    slotted = _with_slots(p1, ["cause", "actor", "time", "history"])

    traces = {
        "p1_sentence_on_saved_decision": {
            "recognizers": _recognizers(P1_SENTENCE, p1),
            "flow": _flow(P1_SENTENCE, p1),
            "audit": _classify(P1_SENTENCE, p1, response=P1_NARRATION),
        },
        "p1_sentence_on_effective_decision": {
            "recognizers": _recognizers(P1_SENTENCE, effective),
            "flow": _flow(P1_SENTENCE, effective),
            "audit": _classify(P1_SENTENCE, effective, response=P1_NARRATION),
        },
        "p1_declaration_validation": {
            "hard_valid": declaration.get("hard_valid"),
            "accepted": [row.get("reason_codes") for row in declaration.get("accepted_claims") or []],
            "rejected": declaration.get("rejected_claims"),
            "recognizers": _recognizers(P1_DECLARATION, p1),
        },
        "p1_full_envelope_hard_valid": p1_envelope.get("hard_valid"),
        "p1_full_narration_sentences": [
            {
                "sentence": sentence,
                "audit": _classify(sentence, effective, response=P1_NARRATION),
                "flow": _flow(sentence, effective),
            }
            for sentence in g._sentences(P1_NARRATION)
        ],
        "p3_sentence": {
            "recognizers": _recognizers(P3_SENTENCE, p3),
            "flow": _flow(P3_SENTENCE, p3),
            "audit": _classify(P3_SENTENCE, p3, response=P3_NARRATION),
        },
        "p3_envelope_hard_valid": p3_envelope.get("hard_valid"),
        "p3_envelope_reasons": [
            row.get("reason_codes") for row in (p3_envelope.get("violations") or [])
        ],
        "p3_retry": {
            "hard_valid": p3_retry.get("hard_valid"),
            "sentences": [
                {
                    "sentence": sentence,
                    "recognizers": _recognizers(sentence, p3),
                    "flow": _flow(sentence, p3),
                    "audit": _classify(sentence, p3, response=P3_RETRY),
                }
                for sentence in g._sentences(P3_RETRY)
            ],
        },
        "p1_if_unresolved_qualifiers_populated": {
            "recognizers": _recognizers(P1_SENTENCE, slotted),
            "flow": _flow(P1_SENTENCE, slotted),
            "audit": _classify(P1_SENTENCE, slotted),
            "note": "Recipe lists cause/actor/time/history. Saved decision unresolved_qualifiers is empty. This copy only shows that populating the slot list still loses to the inference return.",
        },
    }

    base = "The split wooden yoke and the torn leather hanger"
    p3_stem = "The split wooden yoke and the torn leather hanger could be consistent with deliberate cutting, but"
    cases = []

    def add(*args, decision=p1, **kwargs):
        cases.append(_case(*args, decision=decision, **kwargs))

    add("A01", "pure_observation", "The bell's wooden yoke is split.", "p1_interpret", "accept", "Authorized observation restated exactly.")
    add("A02", "pure_observation", "The bell's leather hanger is torn.", "p1_interpret", "accept", "Authorized observation restated exactly.")
    add(
        "A03",
        "valid_qualified_inference",
        "The split wooden yoke and the torn leather hanger could be consistent with significant stress or force.",
        "p1_interpret",
        "accept",
        "Existing PR-BS useful-A1 sentence. Qualified possibility, no cause connective.",
    )
    add(
        "A04",
        "valid_qualified_inference",
        "The split yoke might suggest the wood gave under a load.",
        "p1_interpret",
        "accept",
        "Control A. Hedge tied to the observation. No because/due-to and no history noun.",
    )
    add(
        "B01",
        "unsupported_cause",
        "The split is due to prolonged neglect.",
        "p1_interpret",
        "reject",
        "Control B. Unqualified cause. No inference hedge.",
    )
    add(
        "B02",
        "unsupported_history",
        "The hanger was torn last night.",
        "p1_interpret",
        "reject",
        "Unqualified history and time. Existing PR-BS overreach wording.",
    )
    add(
        "B03",
        "unsupported_cause",
        "A sudden pull caused the split yoke.",
        "p1_interpret",
        "reject",
        "Unqualified cause. Existing PR-BS overreach wording.",
    )
    add(
        "B04",
        "unsupported_actor",
        "Someone cracked the wooden yoke.",
        "p1_interpret",
        "reject",
        "Unqualified actor.",
    )
    add(
        "C01",
        "mixed_inference_plus_cause",
        P1_SENTENCE,
        "p1_interpret_after_accepted_declaration",
        "reject",
        "Live production path. The accepted declaration is merged into proposed facts before narration audit. That merge puts the hedge word into the definite-phrase ground.",
        decision=effective,
    )
    add(
        "C01b",
        "mixed_inference_plus_cause",
        P1_SENTENCE,
        "p1_interpret_before_declaration_merge",
        "reject",
        "Same live sentence on the saved decision, before the declaration is copied into the ground. The lead check fires, and the inference return still skips the cause residual.",
    )
    add(
        "C02",
        "mixed_inference_plus_cause",
        f"{base} might suggest significant stress, perhaps due to prolonged neglect.",
        "p1_interpret",
        "reject",
        "Mixed E shape. Authorized hedge first, unauthorized due-to second.",
    )
    add(
        "C03",
        "mixed_cause_then_inference",
        "Prolonged neglect is the cause, though the split yoke might also suggest stress.",
        "p1_interpret",
        "reject",
        "Mixed D shape. Unauthorized cause before the hedge.",
    )
    add(
        "C04",
        "mixed_inference_plus_history_noun",
        "The split wooden yoke might point to neglect.",
        "p1_interpret",
        "reject",
        "Grounded subject plus the neglect noun the recipe forbids. No due-to.",
    )
    add(
        "C05",
        "mixed_inference_plus_history_noun",
        "The damage might point to neglect.",
        "p1_interpret",
        "reject",
        "Existing PR-BS overreach sentence. Ungrounded 'damage' may reject for a different reason than neglect.",
    )
    add(
        "C06",
        "declaration_bounded_inference",
        P1_DECLARATION,
        "p1_interpret",
        "reject",
        "Live P1 declaration. Neglect, heavy use, and external force without due-to.",
    )
    add(
        "D01",
        "player_hypothesis_conditional",
        P3_SENTENCE,
        "p3_perceive",
        "reject",
        "Live P3 sentence. Conditional fit plus ungrounded motive. Whole sentence should not pass.",
        decision=p3,
    )
    add(
        "D02",
        "player_hypothesis_conditional",
        f"{p3_stem} the explanation remains uncertain.",
        "p3_perceive",
        "accept",
        "Same conditional proposition, no new motive noun, remains uncertain.",
        decision=p3,
    )
    add(
        "D03",
        "uncertainty_variant",
        f"{p3_stem} the explanation remains unclear.",
        "p3_perceive",
        "accept",
        "Same proposition. remains unclear.",
        decision=p3,
    )
    add(
        "D04",
        "uncertainty_variant",
        f"{p3_stem} the explanation is unclear.",
        "p3_perceive",
        "accept",
        "Same proposition. is unclear.",
        decision=p3,
    )
    add(
        "D05",
        "uncertainty_variant",
        f"{p3_stem} the explanation is uncertain.",
        "p3_perceive",
        "accept",
        "Same proposition. is uncertain.",
        decision=p3,
    )
    add(
        "D06",
        "uncertainty_variant",
        f"{p3_stem} deliberate cutting cannot be determined.",
        "p3_perceive",
        "accept",
        "Same proposition. cannot be determined.",
        decision=p3,
    )
    add(
        "D07",
        "uncertainty_variant",
        f"{p3_stem} deliberate cutting cannot be established.",
        "p3_perceive",
        "accept",
        "Same proposition. cannot be established. Contains the stem established.",
        decision=p3,
    )
    add(
        "D08",
        "uncertainty_variant",
        "The split wooden yoke might be consistent with deliberate cutting.",
        "p3_perceive",
        "accept",
        "might be consistent with. No uncertainty coda.",
        decision=p3,
    )
    add(
        "D09",
        "uncertainty_variant",
        "The split wooden yoke may fit deliberate cutting.",
        "p3_perceive",
        "accept",
        "may fit. No uncertainty coda.",
        decision=p3,
    )
    add(
        "D10",
        "uncertainty_variant",
        "Deliberate cutting is possible, and the split yoke does not rule it out.",
        "p3_perceive",
        "accept",
        "is possible / not ruled out.",
        decision=p3,
    )
    add(
        "E01",
        "certainty_upgrade",
        "The split yoke clearly comes from deliberate cutting.",
        "p3_perceive",
        "reject",
        "Certainty strengthening of the hypothesis.",
        decision=p3,
    )
    add(
        "E02",
        "certainty_upgrade",
        "The split yoke was definitely cut on purpose.",
        "p3_perceive",
        "reject",
        "definitely. May or may not be in the certainty recognizer.",
        decision=p3,
    )
    add(
        "E03",
        "certainty_upgrade",
        "The split yoke was certainly cut.",
        "p3_perceive",
        "reject",
        "certainly.",
        decision=p3,
    )
    add(
        "E04",
        "certainty_upgrade",
        "The split yoke was obviously cut.",
        "p3_perceive",
        "reject",
        "obviously.",
        decision=p3,
    )
    add(
        "F01",
        "negated_certainty",
        "The cause is not clear.",
        "p1_interpret",
        "accept",
        "Negated clarity. Should not become a certainty upgrade.",
    )
    add(
        "F02",
        "negated_certainty",
        "The cause is clear.",
        "p1_interpret",
        "reject",
        "Positive clarity about cause.",
    )
    add(
        "F03",
        "negated_certainty",
        "It is not clearly neglect.",
        "p1_interpret",
        "accept",
        "not clearly. Scope should block the certainty keyword.",
    )
    add(
        "F04",
        "negated_certainty",
        "It clearly could be neglect.",
        "p1_interpret",
        "reject",
        "clearly attached to a forbidden history noun, even with could.",
    )
    add(
        "F05",
        "negated_certainty",
        "There is no clear evidence of deliberate cutting.",
        "p3_perceive",
        "accept",
        "no clear evidence. Negative evidential wording.",
        decision=p3,
    )
    add(
        "F06",
        "negated_certainty",
        "Deliberate cutting cannot be established.",
        "p3_perceive",
        "accept",
        "cannot be established. Negation over establish.",
        decision=p3,
    )
    add(
        "F07",
        "negated_certainty",
        "Deliberate cutting remains possible but unproven.",
        "p3_perceive",
        "accept",
        "possible but unproven.",
        decision=p3,
    )
    add(
        "G01",
        "order_reversed_mixed",
        "Perhaps due to prolonged neglect, the split wooden yoke might suggest significant stress.",
        "p1_interpret",
        "reject",
        "Unauthorized cause first, qualified inference second. Same sentence.",
    )
    add(
        "G02",
        "order_forward_mixed",
        "The split wooden yoke might suggest significant stress, perhaps due to prolonged neglect.",
        "p1_interpret",
        "reject",
        "Qualified inference first, unauthorized cause second.",
    )
    add(
        "H01",
        "live_p3_unclear_swap",
        P3_SENTENCE.replace("remains uncertain", "remains unclear"),
        "p3_perceive",
        "reject",
        "Live P3 with only uncertain changed to unclear. Motive is still ungrounded. Exemption must not immunize it.",
        decision=p3,
    )
    add(
        "H02",
        "live_p1_without_due_to",
        "This damage might suggest the bell has been subjected to significant stress or prolonged neglect.",
        "p1_interpret",
        "reject",
        "Live P1 cause clause removed. Neglect noun remains.",
    )
    add(
        "H03",
        "slotted_decision_still_returns",
        P1_SENTENCE,
        "p1_interpret_with_unresolved_qualifiers",
        "reject",
        "Same live sentence after copying cause/actor/time/history onto unresolved_qualifiers.",
        decision=slotted,
    )

    counts = {
        "cases": len(cases),
        "correct_accepts": sum(
            1
            for row in cases
            if row["expected_classification"] == "accept" and row["actual_classification"] in {"accept", "accept_by_omission"}
        ),
        "correct_rejects": sum(1 for row in cases if row["expected_classification"] == "reject" and row["actual_classification"] == "reject"),
        "false_accepts": sum(1 for row in cases if row["false_accept"]),
        "false_rejects": sum(1 for row in cases if row["false_reject"]),
        "ambiguous": sum(1 for row in cases if row["ambiguous"]),
        "accept_by_omission": sum(1 for row in cases if row["actual_classification"] == "accept_by_omission"),
    }
    payload = {
        "model_calls": 0,
        "corpus": CORPUS,
        "traces": traces,
        "counts": counts,
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "counts": counts}, indent=2))
    for row in cases:
        flag = "OK"
        if row["false_accept"]:
            flag = "FALSE_ACCEPT"
        elif row["false_reject"]:
            flag = "FALSE_REJECT"
        elif row["expected_classification"] != row["actual_classification"]:
            flag = "MISMATCH"
        print(f"{row['case_id']} {flag} exp={row['expected_classification']} act={row['actual_classification']} path={row['rejection_acceptance_path']} reasons={row['reason_codes']}")


if __name__ == "__main__":
    main()
