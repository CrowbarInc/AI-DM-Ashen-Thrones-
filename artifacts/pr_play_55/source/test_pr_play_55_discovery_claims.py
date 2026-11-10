"""PR-PLAY-55 development gate. The frozen holdout is a separate file."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from game.anchored_investigation_narration import validate_prelude
from game.consequential_narration_validation import (
    FAIL,
    PASS,
    REVIEW_REQUIRED,
    SemanticAuthority,
    apply_consequential_gate,
    validate_consequential_narration,
)
from game.mechanical_claims import audit_mechanical_claims
from tests.pr_play_54_corpus import CASES as PREVIOUS, authority_for, contract_for
from tests.pr_play_55_development import CASES

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT = ROOT / "tests" / "pr_play_55_holdout.json"
MANIFEST = ROOT / "tests" / "pr_play_55_holdout_manifest.json"


def _actual(case):
    return validate_consequential_narration(case["text"], authority_for(case["authority"]))


def test_development_cases_match_the_discovery_boundary():
    assert len(CASES) >= 36
    groups = {case["group"] for case in CASES}
    assert {"negative", "positive", "paraphrase", "ambiguous"} <= groups
    required = {
        "unknown_object_discovery",
        "unknown_object_acquisition",
        "indirect_object_discovery",
        "presupposed_acquisition",
        "implied_npc_identification",
        "implied_npc_confession",
        "false_success_without_success_word",
        "false_failure_without_failure_word",
        "unauthorized_location_access",
        "unauthorized_environment",
        "unauthorized_quest_progression",
        "authorized_discovery_paraphrase",
        "harmless_unfamiliar_object",
        "surface_observation",
        "speculation",
        "metaphor",
        "ambiguous_marking",
    }
    assert required <= {case["category"] for case in CASES}
    for case in CASES:
        actual = _actual(case)
        assert actual["provider_requests"] == 0
        assert actual["decision"] == case["expected"], (case["id"], actual)
        if case["expected"] == PASS:
            assert actual["reasons"] == []
        else:
            assert case["reason"] in actual["reasons"]


def test_find_and_discover_share_a_claim_relation():
    found = _actual(next(case for case in CASES if case["id"] == "D01"))
    discovered = _actual(next(case for case in CASES if case["id"] == "D02"))
    assert found["decision"] == discovered["decision"] == FAIL
    for result in (found, discovered):
        claim = result["claims"][0]
        assert claim["relation"] == "establishes_discovery"
        assert "ribbon" in claim["subject"]
        assert claim.get("authority_reference", None) in {None, ""}


def test_unfamiliar_marking_is_review_not_a_pass():
    result = _actual(next(case for case in CASES if case["id"] == "D17"))
    assert result["decision"] == REVIEW_REQUIRED
    assert result["claims"][0]["reason_code"] == "AMBIGUOUS_CONSEQUENCE"


def test_previous_fabrication_corpus_still_fails():
    negatives = [case for case in PREVIOUS if case["group"] == "negative"]
    assert len(negatives) == 49
    for case in negatives:
        actual = validate_consequential_narration(case["text"], authority_for(case["authority"]))
        assert actual["decision"] == FAIL
        assert actual["decision"] != PASS


def test_combined_gate_accepts_synonym_route_and_satchel_grit():
    _, route = validate_prelude(
        contract_for("guard_route"),
        "At sunset, the sentry makes his rounds along the west road.",
    )
    assert route["hard_valid"] is True, route["reasons"]
    _, grit = validate_prelude(contract_for("notice_success"), "A little grit lies in your satchel.")
    assert grit["hard_valid"] is True, grit["reasons"]
    audit = audit_mechanical_claims(
        "A silver key lies in your satchel.",
        {"kind": "investigate", "success": True, "state_changes": {}},
    )
    assert "unsupported_mechanical_claim:items_added" in audit["reasons"]


def test_gate_cannot_promote_a_failure_or_a_review():
    blocked = apply_consequential_gate(
        {"hard_valid": False, "reasons": ["ungrounded_authoritative_rule"], "contract_satisfying": False},
        {"decision": PASS, "reasons": []},
    )
    assert blocked["hard_valid"] is False
    reviewed = apply_consequential_gate(
        {"hard_valid": True, "reasons": [], "contract_satisfying": True},
        {"decision": REVIEW_REQUIRED, "reasons": ["ambiguous_consequential"]},
    )
    assert reviewed["hard_valid"] is False
    assert "consequential_review_required" in reviewed["reasons"]
    errored = apply_consequential_gate(
        {"hard_valid": True, "reasons": [], "contract_satisfying": True},
        {"decision": "VALIDATION_ERROR", "reasons": ["validator_exception"]},
    )
    assert errored["hard_valid"] is False
    assert errored["contract_satisfying"] is False


def test_validation_does_not_mutate_resolution_or_authority_fields():
    resolution = {"kind": "investigate", "success": True, "state_changes": {}, "discovered_clues": ["A public note."]}
    before = json.dumps(resolution)
    authority = authority_for("notice_success")
    snapshot = asdict(authority)
    validate_consequential_narration("You find a ribbon beneath the board.", authority)
    audit_mechanical_claims("A little dust lies in your pack.", resolution)
    assert json.dumps(resolution) == before
    assert asdict(authority) == snapshot
    assert "ribbon" not in json.dumps(asdict(SemanticAuthority()))


def test_player_modules_still_do_not_import_the_gate():
    for relative in ("game/api.py", "game/gm.py", "game/exploration.py"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "consequential_narration_validation" not in source
        assert "preview_anchored_investigation" not in source


def test_holdout_manifest_is_frozen_without_classifying_it():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(HOLDOUT.read_bytes()).hexdigest()
    assert digest == manifest["sha256"]
    payload = json.loads(HOLDOUT.read_text(encoding="utf-8"))
    assert len(payload["cases"]) == 70
    assert manifest["labeled_before_implementation"] is True
    groups = {}
    for case in payload["cases"]:
        groups[case["group"]] = groups.get(case["group"], 0) + 1
    assert groups == {"fabrication": 30, "harmless": 20, "paraphrase": 10, "ambiguous": 10}
