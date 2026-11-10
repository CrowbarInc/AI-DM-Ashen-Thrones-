"""PR-PLAY-51 geography grounding. Offline. No provider calls and no campaign writes."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from game.anchored_investigation_narration import (
    assemble,
    authorize_anchored_investigation,
    prelude_request,
    validate_prelude,
)
from game.gm import _scene_layers
from game.proposition_authority import classify_propositions
from tests.test_pr_play_49_anchored_narration import CORPUS, contract

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
B2 = (
    "The ground near the weathered milestone is soft and disturbed, bearing the faint "
    "impressions of footsteps that overlap and blur together. The muddied earth tells of "
    "recent passage, yet the details remain elusive beneath the shifting layers of soil and rain."
)

# Semantic labels for this pass. Harmless lines describe ground, weather, or movement.
# Unsafe lines assert an unsupported feature, opening, route, or relocation.
HARMLESS = [
    "The mud bears signs of recent passage.",
    "Rain gathers beneath the wagon.",
    "The footprints overlap along the roadside.",
    "The earth has been disturbed by passing travelers.",
    "The details remain hidden beneath layers of wet soil.",
    "A breeze passes through the courtyard.",
    "The path is slick beneath your boots.",
    "You study the ground beside the milestone.",
    "The marks suggest movement through the area.",
    "The tracks fade where rain has softened the earth.",
]
UNSAFE = [
    "The hidden passage opens before you.",
    "A secret tunnel opens beneath the milestone.",
    "You discover an underground passage leading north.",
    "The concealed doorway swings open.",
    "You find yourself inside the crypt.",
    "A newly revealed route leads into the mountains.",
    "The wall slides aside, exposing a hidden chamber.",
    "You uncover the entrance to an ancient vault.",
    "A concealed stairway descends beneath the road.",
    "The footprints reveal a hidden entrance beneath the road.",
]
BORDERLINE = [
    ("accept", "The passage of rain softens the mud beneath your boots."),
    ("accept", "Footprints record recent passage beneath a sheet of rain."),
    ("reject", "The passage beneath the milestone leads north."),
    ("reject", "The worn path runs beneath the road."),
    ("accept", "The path is worn beneath a sheet of rain."),
]


def footprint_row() -> dict:
    path = ROOT / "artifacts" / "pr_play_49" / "evidence_fixture_old_milestone.json"
    return json.loads(path.read_text(encoding="utf-8"))


def footprint_contract():
    row = footprint_row()
    public, _, _ = _scene_layers(row["scene"])
    payload = {
        "scene": {
            "public": public,
            "discovered_clues": [{"text": text} for text in row.get("known") or []],
            "discoverable_clues": row["scene"]["scene"].get("discoverable_clues", []),
        }
    }
    return authorize_anchored_investigation(row["resolution"], payload)


def saved_requests() -> list[dict]:
    path = ROOT / "artifacts" / "pr_play_50" / "requests.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _audit(text: str, bound=None) -> dict:
    _, audit = validate_prelude(bound or footprint_contract(), text)
    return audit


def test_b2_reproduction_accepts_saved_prelude_and_keeps_the_anchor():
    saved = next(row for row in saved_requests() if row["request_id"] == "B2")
    raw = saved["extracted_narration_text"]
    assert raw == B2
    bound = footprint_contract()
    before = copy.deepcopy(bound.outcome)
    prelude, audit = validate_prelude(bound, raw)
    assembled = assemble(bound, prelude)
    assert audit["hard_valid"] is True
    assert "ungrounded_authoritative_rule" not in audit["reasons"]
    assert prelude == raw
    assert raw in assembled
    assert assembled == raw + "\n\n" + ANCHOR
    assert assembled.count(ANCHOR) == 1
    assert saved["authoritative_discovery"] == ANCHOR
    assert bound.anchors[0].text == ANCHOR
    assert bound.outcome == before
    families = [row["family"] for row in audit["authority"]]
    assert "geography" not in families
    assert audit["mechanical_claim_audit"]["reasons"] == []


def test_hidden_passage_counterexample_stays_rejected():
    audit = _audit("The hidden passage opens before you.")
    assert audit["hard_valid"] is False
    assert "ungrounded_authoritative_rule" in audit["reasons"]
    assert any(row["family"] == "hidden_information" for row in audit["authority"])


@pytest.mark.parametrize("text", HARMLESS)
def test_harmless_geographic_description_is_accepted(text: str):
    prelude, audit = validate_prelude(footprint_contract(), text)
    assert audit["hard_valid"] is True, audit
    assert prelude == text
    assert "ungrounded_authoritative_rule" not in audit["reasons"]


@pytest.mark.parametrize("text", UNSAFE)
def test_unsupported_geographic_assertion_is_rejected(text: str):
    audit = _audit(text)
    assert audit["hard_valid"] is False, text
    assert "ungrounded_authoritative_rule" in audit["reasons"]


@pytest.mark.parametrize("expected,text", BORDERLINE)
def test_borderline_geography_follows_the_relation(expected: str, text: str):
    audit = _audit(text)
    if expected == "accept":
        assert audit["hard_valid"] is True, audit
    else:
        assert audit["hard_valid"] is False, audit
        assert "ungrounded_authoritative_rule" in audit["reasons"]


def test_established_geography_and_hidden_controls_keep_their_families():
    geography = classify_propositions("The old milestone lies east beyond the trading crossroads.")
    hidden = classify_propositions("A secret tunnel runs beneath the gate into the keep.")
    assert any(row["family"] == "geography" and row["kind"] == "consequential_proposal" for row in geography)
    assert any(row["family"] == "hidden_information" and row["kind"] == "consequential_proposal" for row in hidden)


def test_saved_provider_responses_replay_without_edits():
    results = []
    for record in saved_requests():
        row = json.loads(
            (ROOT / "artifacts" / "pr_play_49" / f"evidence_fixture_{record['fixture']}.json").read_text(encoding="utf-8")
        )
        public, _, _ = _scene_layers(row["scene"])
        bound = authorize_anchored_investigation(row["resolution"], {
            "scene": {
                "public": public,
                "discovered_clues": [{"text": text} for text in row.get("known") or []],
                "discoverable_clues": row["scene"]["scene"].get("discoverable_clues", []),
            }
        })
        raw = record["extracted_narration_text"]
        prelude, audit = validate_prelude(bound, raw)
        assembled = assemble(bound, prelude)
        anchor = " ".join(item.text for item in bound.anchors)
        assert prelude == raw
        assert assembled == raw + "\n\n" + anchor
        assert anchor == record["authoritative_discovery"]
        assert audit["hard_valid"] is True, (record["request_id"], audit)
        results.append(record["request_id"])
    assert results == ["A1", "A2", "B1", "B2"]


def test_adversarial_corpus_does_not_accept_more_unsafe_lines():
    from tests.test_pr_play_49_anchored_narration import fixtures

    saved = json.loads((ROOT / "artifacts" / "pr_play_49" / "adversarial_corpus.json").read_text(encoding="utf-8"))
    previous = {row["case"]: row for row in saved}
    rows = fixtures()
    notice = contract(rows[0])
    prints = contract(rows[1])
    footprint_cases = {"link", "count", "destination", "certainty"}
    accepted_unsafe = 0
    newly_accepted = []
    newly_rejected_safe = []
    for case, text, safe in CORPUS:
        bound = prints if case in footprint_cases else notice
        prelude, audit = validate_prelude(bound, text)
        accepted = bool(audit["hard_valid"]) and prelude == text
        if not safe and accepted:
            accepted_unsafe += 1
        prior = previous[case]
        if prior["expected_safe"] is False and prior["false_accept"] is False and accepted:
            newly_accepted.append(case)
        if prior["expected_safe"] is True and prior["false_reject"] is False and not accepted:
            newly_rejected_safe.append(case)
    assert accepted_unsafe <= 17, accepted_unsafe
    assert newly_accepted == []
    assert newly_rejected_safe == []


def test_narration_path_is_not_wired_into_gameplay_modules():
    for relative in ("game/api.py", "game/gm.py", "game/exploration.py"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "anchored_investigation_narration" not in source
        assert "preview_anchored_investigation" not in source


def test_prelude_projection_omits_withheld_fixture_fields():
    row = footprint_row()
    bound = footprint_contract()
    request = json.dumps(prelude_request(bound))
    scene = row["scene"]["scene"]
    for exit_row in scene.get("exits") or []:
        assert exit_row["target_scene_id"] not in request
    hint = str((row.get("resolution") or {}).get("hint") or "")
    if hint:
        assert hint not in request
    assert ANCHOR in request


def test_validator_source_still_emits_the_geography_reason():
    source = (ROOT / "game" / "immutable_valid_response.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "validate_generated_response" in names
    assert "ungrounded_authoritative_rule" in source
