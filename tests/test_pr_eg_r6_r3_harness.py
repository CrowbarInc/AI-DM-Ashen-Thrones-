"""Harness checks that do not call a provider."""
from experiments.pr_eg_r6_r3.architecture_b import compile_description
from experiments.pr_eg_r6_r3.architecture_c import candidates_for, compile_selection
from experiments.pr_eg_r6_r3.common import restricted_leak, score_case
from experiments.pr_eg_r6_r3.corpus import cases


def test_corpus_meets_contract_minimums():
    loaded = cases()
    assert len(loaded) >= 120
    assert sum("correction" in case["tags"] for case in loaded) >= 25
    assert sum("follow_up" in case["tags"] for case in loaded) >= 25
    assert sum("multi_role" in case["tags"] for case in loaded) >= 15
    assert sum("ambiguity" in case["tags"] for case in loaded) >= 15
    assert {case["partition"] for case in loaded} == {"development", "validation", "holdout"}


def test_b_compiler_ignores_meaning_and_utterance_keywords():
    case = next(item for item in cases() if item["id"] == "D17")
    ir = {
        "move": "ask_about_previous", "anchor": "current", "anchor_marks": [],
        "predicate": "", "predicate_evidence": "", "predicate_changed": False,
        "role_updates": [], "gap": "who_supplied_the_information", "gap_detail": "",
        "temporal": "", "spatial": "", "negated": False, "qualifier_changed": False,
        "meaning": "The player is correcting the object to something else entirely.",
    }
    compiled = compile_description(ir, case)
    assert compiled["operation"] == "follow_up"
    assert compiled["follow_up"] == "source_attribution"
    assert compiled["roles"]["item"] == "cedar casks"


def test_b_does_not_keyword_classify_a_correction_phrase():
    case = next(item for item in cases() if item["id"] == "D09")
    ir = {
        "move": "fresh_question", "anchor": "none", "anchor_marks": [],
        "predicate": "seal", "predicate_evidence": "oak", "predicate_changed": True,
        "role_updates": [{"role": "item", "value": "oak butts", "evidence": "oak butts"}],
        "gap": "", "gap_detail": "sealer", "temporal": "", "spatial": "", "negated": False,
        "qualifier_changed": False, "meaning": "correction",
    }
    compiled = compile_description(ir, case)
    assert compiled["operation"] == "information_question"


def test_c_candidates_ignore_utterance_wording():
    sample = next(item for item in cases() if item["id"] == "D13")
    other = dict(sample)
    other["utterance"] = "completely different wording with no shared verbs"
    assert [row["id"] for row in candidates_for(sample)] == [row["id"] for row in candidates_for(other)]


def test_c_rejects_unknown_candidate_without_repair():
    sample = next(item for item in cases() if item["id"] == "D09")
    rows = candidates_for(sample)
    compiled = compile_selection({"candidate_id": "not-a-real-candidate", "value": "oak butts", "value_evidence": "oak butts",
                                  "predicate": "", "predicate_evidence": "", "requested_role": "", "temporal": "",
                                  "spatial": "", "negated": False, "new_roles": []}, sample, rows)
    assert compiled["validation"] == "rejected"
    assert compiled["operation"] == "other"


def test_score_uses_labels_not_self_reported_success():
    sample = next(item for item in cases() if item["id"] == "D09")
    normalized = {
        "operation": "information_question", "referent_target": "", "relationship": "seal",
        "roles": {"item": "oak butts"}, "requested_role": "sealer", "temporal": "", "spatial": "",
        "negated": False, "follow_up": "", "validation": "accepted", "ambiguity": False,
        "response_class": "answer", "malformed": False, "disclosure_granted": False,
        "authorized_text": "", "selected_source_ids": [], "success": True,
    }
    scores = score_case(sample, normalized)
    assert scores["correction_success"] is False
    assert scores["operation_correct"] is False


def test_restricted_text_in_sources_is_a_leak_and_player_text_is_not():
    case = next(item for item in cases() if item["id"] == "D08")
    assert restricted_leak({"candidates": [{"text": "The tide-room cipher is gray-lantern."}]}, case)
    assert restricted_leak({"utterance": "what is gray-lantern?", "candidates": []}, case) == []
