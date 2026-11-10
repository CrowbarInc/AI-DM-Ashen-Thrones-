"""PR-PLAY-54 consequential fabrication gate.

The new check is deterministic and quarantined to prelude validation. It does
not call a provider, and a non-PASS result is not a player-facing pass.
"""
from __future__ import annotations

import time
from dataclasses import asdict

import pytest

from game.anchored_investigation_narration import preview_anchored_investigation, validate_prelude
from game.consequential_narration_validation import (
    FAIL,
    PASS,
    REVIEW_REQUIRED,
    VALIDATION_ERROR,
    SemanticAuthority,
    apply_consequential_gate,
    authority_from_anchored,
    validate_consequential_narration,
)
from game.immutable_valid_response import validate_generated_response
from game.resolution_contract import contract_mapping_from_resolution
from tests.pr_play_54_corpus import CASES, authority_for, contract_for, resolution_for
from tests.test_pr_play_53_quarantined_live import NOTICE, _facing, _mechanical, _play, _resolution


def _previous(case) -> str:
    resolution = resolution_for(case["authority"])
    audit = validate_generated_response(
        case["text"],
        resolution=resolution,
        contract=contract_mapping_from_resolution(resolution),
    )
    return FAIL if not audit["hard_valid"] else PASS


def _actual(case) -> dict:
    return validate_consequential_narration(case["text"], authority_for(case["authority"]))


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_corpus_decision(case):
    actual = _actual(case)
    assert actual["provider_requests"] == 0
    assert actual["decision"] == case["expected"]
    if case["expected"] == PASS:
        assert actual["reasons"] == []
    else:
        assert case["reason"] in actual["reasons"]
        assert actual["decision"] != PASS
    if "historical" in case:
        assert _previous(case) == case["historical"]


def test_critical_misses_are_no_longer_accepted():
    critical = [case for case in CASES if case.get("historical") == PASS and case["expected"] == FAIL]
    assert len(critical) >= 6
    for case in critical:
        assert _previous(case) == PASS
        assert _actual(case)["decision"] == FAIL


def test_previously_detected_fabrications_stay_rejected():
    detected = [case for case in CASES if case.get("historical") == FAIL]
    assert detected
    for case in detected:
        assert _previous(case) == FAIL
        assert _actual(case)["decision"] == FAIL


def test_categories_cover_the_required_matrix():
    categories = {case["category"] for case in CASES if case["group"] == "negative"}
    required = {
        "unauthorized_item_discovery",
        "unauthorized_item_acquisition",
        "unauthorized_npc_identification",
        "unauthorized_npc_confession",
        "false_mechanical_success",
        "false_mechanical_failure",
        "unauthorized_hidden_location",
        "unauthorized_location_access",
        "unauthorized_quest_progression",
        "unauthorized_condition_change",
        "hidden_information_disclosure",
        "discovery_contradiction",
    }
    assert required <= categories
    for category in required:
        assert sum(1 for case in CASES if case["category"] == category) >= 3


def test_prelude_gate_rejects_fabrications_and_keeps_harmless_lines():
    for case in CASES:
        if case["authority"] not in {
            "notice_success", "notice_failed", "notice_observed", "footprint", "guard_route",
        }:
            continue
        contract = contract_for(case["authority"])
        before = asdict(contract)
        prelude, audit = validate_prelude(contract, case["text"])
        assert asdict(contract) == before
        decision = audit["consequential_validation"]["decision"]
        assert decision == case["expected"]
        if case["expected"] == PASS:
            consequential_reasons = [
                reason for reason in audit["reasons"] if str(reason).startswith("consequential_")
            ]
            assert consequential_reasons == []
            # S21 is the older possession false positive. P1 is the older
            # geography rule, which does not treat a synonym as the same place.
            if case["id"] not in {"S21", "P1"}:
                assert audit["hard_valid"] is True
                assert prelude == case["text"]
        else:
            assert audit["hard_valid"] is False
            assert prelude == case["text"]


def test_dust_remains_a_legacy_possession_false_positive():
    """The new gate does not treat dust as loot. The older possession frame still does."""
    case = next(row for row in CASES if row["id"] == "S21")
    assert _actual(case)["decision"] == PASS
    _, audit = validate_prelude(contract_for(case["authority"]), case["text"])
    assert audit["consequential_validation"]["decision"] == PASS
    assert audit["hard_valid"] is False
    assert "unsupported_mechanical_claim:items_added" in audit["reasons"]


def test_non_pass_cannot_become_a_prelude_pass():
    class Stub:
        def generate(self, request):
            return "The compartment yields."

    contract = contract_for("notice_success")
    preview = preview_anchored_investigation(contract, Stub(), enabled=True)
    audit = validate_consequential_narration(Stub().generate({}), authority_from_anchored(contract))
    assert audit["decision"] == REVIEW_REQUIRED
    assert preview.used_fallback is True
    assert preview.diagnostic == "semantic_rejection"
    assert "compartment yields" not in preview.preview_text.casefold()


def test_validation_error_is_not_a_pass(monkeypatch):
    def explode(text, authority):
        raise RuntimeError("classifier_failed")

    monkeypatch.setattr(
        "game.consequential_narration_validation.validate_consequential_narration",
        explode,
    )
    _, audit = validate_prelude(contract_for("notice_success"), "Rain beads on the crowded board.")
    assert audit["consequential_validation"]["decision"] == VALIDATION_ERROR
    assert audit["hard_valid"] is False
    assert "consequential_validation_error" in audit["reasons"]


def test_gate_never_turns_a_rejection_into_a_pass():
    blocked = apply_consequential_gate(
        {"hard_valid": False, "reasons": ["unsupported_mechanical_claim:items_added"], "contract_satisfying": False},
        {"decision": PASS, "reasons": []},
    )
    assert blocked["hard_valid"] is False
    rejected = apply_consequential_gate(
        {"hard_valid": True, "reasons": [], "contract_satisfying": True},
        {"decision": REVIEW_REQUIRED, "reasons": ["ambiguous_consequential"]},
    )
    assert rejected["hard_valid"] is False
    assert "consequential_review_required" in rejected["reasons"]
    failed = apply_consequential_gate(
        {"hard_valid": True, "reasons": [], "contract_satisfying": True},
        {"decision": FAIL, "reasons": ["unauthorized_discovery"]},
    )
    assert failed["hard_valid"] is False


def test_invalid_input_is_a_validation_error():
    result = validate_consequential_narration(None, SemanticAuthority())
    assert result["decision"] == VALIDATION_ERROR
    assert result["provider_requests"] == 0
    other = validate_consequential_narration("Rain falls.", {"success": True})
    assert other["decision"] == VALIDATION_ERROR


def test_authority_projection_does_not_copy_hidden_fixture_fields():
    contract = contract_for("notice_success")
    authority = authority_from_anchored(contract)
    blob = " ".join(authority.observable_scene + authority.authorized_discoveries + authority.authorized_outcomes)
    assert "UNSEEN" not in blob
    assert "gm_only" not in blob.casefold()
    assert authority.restricted == ()


def test_validation_does_not_mutate_authority_or_resolution():
    contract = contract_for("notice_success")
    before_contract = asdict(contract)
    resolution = resolution_for("notice_success")
    before_resolution = dict(resolution)
    validate_consequential_narration(
        "You find a silver key beneath the board.",
        authority_from_anchored(contract),
    )
    validate_prelude(contract, "You find a silver key beneath the board.")
    assert asdict(contract) == before_contract
    assert resolution == before_resolution


def test_player_modules_do_not_import_the_consequential_gate():
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    for relative in ("game/api.py", "game/gm.py", "game/exploration.py"):
        source = (root / relative).read_text(encoding="utf-8")
        assert "consequential_narration_validation" not in source


def test_corpus_validation_stays_fast_and_local():
    started = time.perf_counter()
    for _ in range(5):
        for case in CASES:
            result = _actual(case)
            assert result["provider_requests"] == 0
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0


def test_rejected_and_unreviewed_narration_stay_off_the_player_response(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, NOTICE, live=False)
    rejected = _play(
        tmp_path, monkeypatch, NOTICE, live=True,
        prelude="You find a silver key beneath the board.",
    )
    review = _play(tmp_path, monkeypatch, NOTICE, live=True, prelude="The compartment yields.")
    for run in (rejected, review):
        record = run["quarantine"][0]
        assert record["diagnostic"] == "semantic_rejection"
        assert record["used_fallback"] is True
        assert record["validation"]["consequential_validation"]["decision"] in {FAIL, REVIEW_REQUIRED}
        assert _facing(run) == _facing(baseline)
        assert _mechanical(_resolution(run)) == _mechanical(_resolution(baseline))
        assert run["final"]["character"] == baseline["final"]["character"]
        assert "silver key" not in _facing(run)
        assert "compartment yields" not in _facing(run).casefold()
    assert rejected["quarantine"][0]["validation"]["consequential_validation"]["decision"] == FAIL
    assert review["quarantine"][0]["validation"]["consequential_validation"]["decision"] == REVIEW_REQUIRED
