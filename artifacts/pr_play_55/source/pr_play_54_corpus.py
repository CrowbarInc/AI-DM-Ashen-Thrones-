"""PR-PLAY-54 consequential-claim corpus.

Cases are linguistic variations of claim types. They are not sentence-specific
exceptions in the validator. `historical` is the previous validator's pass/fail
label and is rechecked against `validate_generated_response` when present.
"""
from __future__ import annotations

import json
from pathlib import Path

from game.anchored_investigation_narration import authorize_anchored_investigation
from game.consequential_narration_validation import SemanticAuthority, authority_from_anchored
from game.gm import _scene_layers

ROOT = Path(__file__).resolve().parents[1]
NOTICE_CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
GUARD_CLUE = "The guard patrols the western road at dusk."

_NOTICE_PUBLIC = {
    "location": "Cinderwatch Gate District",
    "summary": "Rain and a notice board.",
    "visible_facts": [
        "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
    ],
}


def _notice_resolution(kind: str) -> dict:
    if kind == "failed":
        return {
            "kind": "investigate", "success": False, "action_id": "notice_board",
            "interactable_id": "notice_board", "discovered_clues": [], "clue_text": "",
            "state_changes": {},
        }
    if kind == "observed":
        return {
            "kind": "investigate", "success": True, "action_id": "rain_barrel",
            "interactable_id": None, "discovered_clues": [], "clue_text": "",
            "state_changes": {},
        }
    return {
        "kind": "discover_clue", "success": True, "action_id": "notice_board",
        "interactable_id": "notice_board", "discovered_clues": [NOTICE_CLUE],
        "clue_text": NOTICE_CLUE, "state_changes": {},
    }


def _notice_contract(kind: str):
    payload = {"scene": {"public": dict(_NOTICE_PUBLIC), "discovered_clues": []}}
    return authorize_anchored_investigation(_notice_resolution(kind), payload)


def _footprint_contract():
    row = json.loads((ROOT / "artifacts" / "pr_play_49" / "evidence_fixture_old_milestone.json").read_text(encoding="utf-8"))
    public, _, _ = _scene_layers(row["scene"])
    payload = {
        "scene": {
            "public": public,
            "discovered_clues": [{"text": text} for text in row.get("known") or []],
            "discoverable_clues": row["scene"]["scene"].get("discoverable_clues", []),
        }
    }
    return authorize_anchored_investigation(row["resolution"], payload)


def _guard_contract():
    resolution = {
        "kind": "discover_clue", "success": True, "action_id": "guard_post",
        "interactable_id": "guard_post", "discovered_clues": [GUARD_CLUE],
        "clue_text": GUARD_CLUE, "state_changes": {},
    }
    payload = {
        "scene": {
            "public": {
                "visible_facts": [
                    "A guard is visible nearby.",
                    "Rain falls across the square.",
                    "A notice board stands beside the street.",
                ],
            },
            "discovered_clues": [],
        }
    }
    return authorize_anchored_investigation(resolution, payload)


def authority_for(name: str) -> SemanticAuthority:
    if name == "notice_success":
        return authority_from_anchored(_notice_contract("success"))
    if name == "notice_failed":
        return authority_from_anchored(_notice_contract("failed"))
    if name == "notice_observed":
        return authority_from_anchored(_notice_contract("observed"))
    if name == "footprint":
        return authority_from_anchored(_footprint_contract())
    if name == "guard_route":
        return authority_from_anchored(_guard_contract())
    if name == "compass_granted":
        return SemanticAuthority(
            observable_scene=("A table stands in the room.",),
            authorized_outcomes=("You receive a brass compass.",),
            items_added=("brass compass",),
            success=True,
        )
    if name == "admission_granted":
        return SemanticAuthority(
            observable_scene=("A guard stands by the board.",),
            authorized_discoveries=("The guard admits the patrol was delayed.",),
            dialogue=("The guard admits the patrol was delayed.",),
            success=True,
        )
    if name == "opening_granted":
        return SemanticAuthority(
            observable_scene=("A stone wall stands ahead.",),
            authorized_discoveries=("The hidden passage opens onto the lower cellar.",),
            routes_unlocked=("hidden passage",),
            success=True,
        )
    if name == "restricted_ferryman":
        return SemanticAuthority(
            observable_scene=("A ferryman waits at the quay.",),
            authorized_outcomes=("The investigation establishes nothing new.",),
            restricted=("The ferryman secretly serves the Queen of Cinders.",),
            success=False,
        )
    raise KeyError(name)


def contract_for(name: str):
    if name == "notice_success":
        return _notice_contract("success")
    if name == "notice_failed":
        return _notice_contract("failed")
    if name == "notice_observed":
        return _notice_contract("observed")
    if name == "footprint":
        return _footprint_contract()
    if name == "guard_route":
        return _guard_contract()
    raise KeyError(name)


def resolution_for(name: str) -> dict:
    if name == "notice_failed":
        return _notice_resolution("failed")
    if name == "notice_observed":
        return _notice_resolution("observed")
    if name == "notice_success":
        return _notice_resolution("success")
    if name == "guard_route":
        return {
            "kind": "discover_clue", "success": True, "discovered_clues": [GUARD_CLUE],
            "clue_text": GUARD_CLUE, "state_changes": {},
        }
    if name == "compass_granted":
        return {
            "kind": "investigate", "success": True, "discovered_clues": [],
            "state_changes": {"items_added": ["brass compass"]},
        }
    if name == "opening_granted":
        return {
            "kind": "investigate", "success": True, "discovered_clues": [
                "The hidden passage opens onto the lower cellar.",
            ],
            "state_changes": {"routes_unlocked": ["hidden passage"]},
        }
    if name == "admission_granted":
        return {
            "kind": "discover_clue", "success": True,
            "discovered_clues": ["The guard admits the patrol was delayed."],
            "clue_text": "The guard admits the patrol was delayed.",
            "state_changes": {},
        }
    if name == "restricted_ferryman":
        return {
            "kind": "investigate", "success": False, "discovered_clues": [],
            "state_changes": {},
        }
    if name == "footprint":
        row = json.loads((ROOT / "artifacts" / "pr_play_49" / "evidence_fixture_old_milestone.json").read_text(encoding="utf-8"))
        return row["resolution"]
    raise KeyError(name)


def _case(case_id, category, group, authority, text, expected, reason=None, historical=None):
    row = {
        "id": case_id,
        "category": category,
        "group": group,
        "authority": authority,
        "text": text,
        "expected": expected,
    }
    if reason is not None:
        row["reason"] = reason
    if historical is not None:
        row["historical"] = historical
    return row


# Negative claims. `historical` is set only where this cycle compares the
# previous gate directly; the evidence run records the rest.
CASES = [
    # A. Unauthorized item discovery
    _case("A1", "unauthorized_item_discovery", "negative", "notice_success",
          "You find a silver key beneath the board.", "FAIL", "unauthorized_discovery", "PASS"),
    _case("A2", "unauthorized_item_discovery", "negative", "notice_success",
          "Something metallic glints in your hand: a silver key.", "FAIL", "unauthorized_acquisition"),
    _case("A3", "unauthorized_item_discovery", "negative", "notice_success",
          "The key you recovered should open the nearby door.", "FAIL", "unauthorized_discovery"),
    _case("A4", "unauthorized_item_discovery", "negative", "notice_success",
          "With the newly discovered key secured, you continue.", "FAIL", "unauthorized_discovery"),
    _case("A5", "unauthorized_item_discovery", "negative", "notice_success",
          "A glint beneath the notice resolves into a small silver key.", "FAIL", "unauthorized_discovery"),
    # B. Unauthorized acquisition
    _case("B1", "unauthorized_item_acquisition", "negative", "notice_success",
          "You acquire a brass compass.", "FAIL", "unauthorized_acquisition", "FAIL"),
    _case("B2", "unauthorized_item_acquisition", "negative", "notice_success",
          "A silver key now rests among your possessions.", "FAIL", "unauthorized_acquisition", "FAIL"),
    _case("B3", "unauthorized_item_acquisition", "negative", "notice_success",
          "The silver key is now yours.", "FAIL", "unauthorized_acquisition", "PASS"),
    _case("B4", "unauthorized_item_acquisition", "negative", "notice_success",
          "A small silver key now rests among your belongings.", "FAIL", "unauthorized_acquisition"),
    _case("B5", "unauthorized_item_acquisition", "negative", "notice_success",
          "You pocket the brass compass without a word.", "FAIL", "unauthorized_acquisition"),
    # C. Unauthorized NPC identification
    _case("C1", "unauthorized_npc_identification", "negative", "notice_success",
          "You recognize the culprit immediately.", "FAIL", "unauthorized_identity", "PASS"),
    _case("C2", "unauthorized_npc_identification", "negative", "notice_success",
          "The culprit is the tavern runner.", "FAIL", "unauthorized_identity"),
    _case("C3", "unauthorized_npc_identification", "negative", "notice_success",
          "You identify the tavern runner as the murderer.", "FAIL", "unauthorized_identity"),
    _case("C4", "unauthorized_npc_identification", "negative", "notice_success",
          "The tavern runner is the one who killed the merchant.", "FAIL", "unauthorized_identity"),
    # D. Unauthorized confession
    _case("D1", "unauthorized_npc_confession", "negative", "notice_success",
          "The tavern runner confesses that he sold the patrol route.", "FAIL", "unauthorized_confession", "PASS"),
    _case("D2", "unauthorized_npc_confession", "negative", "notice_success",
          "The guard admits he murdered the merchant.", "FAIL", "unauthorized_confession"),
    _case("D3", "unauthorized_npc_confession", "negative", "notice_success",
          "He admits the killing and looks away.", "FAIL", "unauthorized_confession"),
    _case("D4", "unauthorized_npc_confession", "negative", "notice_success",
          "The runner gives a whispered admission: he sold the route.", "FAIL", "unauthorized_confession"),
    # E. False mechanical success
    _case("E1", "false_mechanical_success", "negative", "notice_failed",
          "You succeed in uncovering the patrol route.", "FAIL", "false_mechanical_success", "PASS"),
    _case("E2", "false_mechanical_success", "negative", "notice_failed",
          "The search succeeds.", "FAIL", "false_mechanical_success"),
    _case("E3", "false_mechanical_success", "negative", "notice_failed",
          "You successfully uncover the hidden route.", "FAIL", "false_mechanical_success"),
    _case("E4", "false_mechanical_success", "negative", "notice_failed",
          "Your investigation succeeds in naming the track.", "FAIL", "false_mechanical_success"),
    # F. False mechanical failure
    _case("F1", "false_mechanical_failure", "negative", "notice_success",
          "You fail to learn anything from the board.", "FAIL", "false_mechanical_failure"),
    _case("F2", "false_mechanical_failure", "negative", "notice_success",
          "The investigation fails.", "FAIL", "false_mechanical_failure"),
    _case("F3", "false_mechanical_failure", "negative", "notice_success",
          "You learn nothing of the patrol.", "FAIL", "false_mechanical_failure"),
    # G. Unauthorized hidden location
    _case("G1", "unauthorized_hidden_location", "negative", "notice_success",
          "You discover a hidden compartment behind the board.", "FAIL", "unauthorized_hidden_location"),
    _case("G2", "unauthorized_hidden_location", "negative", "notice_success",
          "A concealed cache comes into view beneath the crates.", "FAIL", "unauthorized_hidden_location"),
    _case("G3", "unauthorized_hidden_location", "negative", "footprint",
          "The footprints reveal a hidden entrance beneath the road.", "FAIL", "unauthorized_hidden_location"),
    _case("G4", "unauthorized_hidden_location", "negative", "notice_success",
          "The patrol is hiding in the buried salt fortress.", "FAIL", "unauthorized_hidden_location"),
    # H. Unauthorized location access
    _case("H1", "unauthorized_location_access", "negative", "notice_success",
          "The hidden passage opens before you.", "FAIL", "unauthorized_access", "FAIL"),
    _case("H2", "unauthorized_location_access", "negative", "notice_success",
          "The lock clicks open.", "FAIL", "unauthorized_access"),
    _case("H3", "unauthorized_location_access", "negative", "notice_success",
          "A concealed door swings open at your touch.", "FAIL", "unauthorized_access"),
    _case("H4", "unauthorized_location_access", "negative", "notice_success",
          "You step into a hidden cellar.", "FAIL", "unauthorized_access"),
    _case("H5", "unauthorized_location_access", "negative", "notice_success",
          "You arrive at the glass tower.", "FAIL", "unauthorized_access"),
    # I. Unauthorized quest progression
    _case("I1", "unauthorized_quest_progression", "negative", "notice_success",
          "The investigation completes your quest.", "FAIL", "unauthorized_quest"),
    _case("I2", "unauthorized_quest_progression", "negative", "notice_success",
          "You complete the missing patrol quest.", "FAIL", "unauthorized_quest"),
    _case("I3", "unauthorized_quest_progression", "negative", "notice_success",
          "This finding advances the patrol objective.", "FAIL", "unauthorized_quest"),
    # J. Unauthorized condition changes
    _case("J1", "unauthorized_condition_change", "negative", "notice_success",
          "The poison has worn off.", "FAIL", "unauthorized_condition"),
    _case("J2", "unauthorized_condition_change", "negative", "notice_success",
          "Your wounds knit shut as you read.", "FAIL", "unauthorized_condition"),
    _case("J3", "unauthorized_condition_change", "negative", "notice_success",
          "You are no longer poisoned.", "FAIL", "unauthorized_condition"),
    # K. Hidden-information disclosure
    _case("K1", "hidden_information_disclosure", "negative", "restricted_ferryman",
          "The ferryman secretly serves the Queen of Cinders.", "FAIL", "hidden_disclosure"),
    _case("K2", "hidden_information_disclosure", "negative", "notice_success",
          "The ferryman hopes to betray you to his patron.", "FAIL", "hidden_disclosure"),
    _case("K3", "hidden_information_disclosure", "negative", "notice_success",
          "GM_ONLY: the board is a coded signal.", "FAIL", "hidden_disclosure"),
    _case("K4", "hidden_information_disclosure", "negative", "notice_success",
          "The secret is that the chamber conceals a release.", "FAIL", "hidden_disclosure"),
    # L. Contradiction of authorized discoveries
    _case("L1", "discovery_contradiction", "negative", "notice_success",
          "The missing patrol was last seen heading southeast.", "FAIL", "discovery_contradiction"),
    _case("L2", "discovery_contradiction", "negative", "guard_route",
          "The guard leaves the western gate completely unprotected at dusk.", "FAIL", "consequential_expansion"),
    _case("L3", "discovery_contradiction", "negative", "footprint",
          "The prints lead straight to the salt fortress.", "FAIL", "unauthorized_discovery"),
    _case("L4", "discovery_contradiction", "negative", "footprint",
          "The prints definitely prove that the patrol went north.", "FAIL", "discovery_contradiction"),
    _case("L5", "discovery_contradiction", "negative", "notice_observed",
          "You read that the patrol took the northwest mud track past the crates.", "FAIL", "unauthorized_discovery", "PASS"),
    # Paraphrases that remain inside the authorized fact.
    _case("P1", "authorized_paraphrase", "paraphrase", "guard_route",
          "At sundown, the guard makes his rounds along the west road.", "PASS"),
    _case("P2", "authorized_paraphrase", "paraphrase", "guard_route",
          "Along the western road, dusk is when the guard patrols.", "PASS"),
    _case("P3", "authorized_paraphrase", "paraphrase", "notice_success",
          "You read that the patrol took the northwest mud track past the crates.", "PASS"),
    _case("P4", "authorized_paraphrase", "paraphrase", "notice_success",
          "You succeed in uncovering the patrol route.", "PASS"),
    _case("P5", "authorized_paraphrase", "paraphrase", "compass_granted",
          "You acquire a brass compass.", "PASS"),
    _case("P6", "authorized_paraphrase", "paraphrase", "admission_granted",
          "The guard admits the patrol was delayed.", "PASS"),
    _case("P7", "authorized_paraphrase", "paraphrase", "opening_granted",
          "The hidden passage opens before you.", "PASS"),
    # Harmless controls. Speculation, metaphor, and negation are not facts.
    _case("S1", "sensory_description", "positive", "notice_success",
          "Rain beads on the crowded board as you lean in for a closer look.", "PASS"),
    _case("S2", "sensory_description", "positive", "notice_success",
          "A cracked wax seal holds one corner of the top notice.", "PASS"),
    _case("S3", "metaphor", "positive", "notice_success",
          "The rain sounds like keys rattling against glass.", "PASS"),
    _case("S4", "incidental_gesture", "positive", "notice_success",
          "The guard's expression suggests exhaustion.", "PASS"),
    _case("S5", "atmospheric_observation", "positive", "notice_success",
          "The passage smells of old stone.", "PASS"),
    _case("S6", "speculation", "positive", "notice_success",
          "You wonder whether someone concealed a key nearby.", "PASS"),
    _case("S7", "speculation", "positive", "notice_success",
          "The merchant looks as though he has something to confess.", "PASS"),
    _case("S8", "negation", "positive", "notice_success",
          "You do not find a silver key.", "PASS"),
    _case("S9", "speculation", "positive", "notice_success",
          "You might find a silver key beneath the board.", "PASS"),
    _case("S10", "conditional", "positive", "notice_success",
          "If you found a key, the door would open.", "PASS"),
    _case("S11", "failed_investigation", "positive", "notice_failed",
          "The lock resists your efforts.", "PASS"),
    _case("S12", "failed_investigation", "positive", "notice_observed",
          "You look around the barrel and learn nothing new.", "PASS"),
    _case("S13", "sensory_description", "positive", "footprint",
          "The mud bears signs of recent passage.", "PASS"),
    _case("S14", "atmospheric_observation", "positive", "footprint",
          "The details remain hidden beneath layers of wet soil.", "PASS"),
    _case("S15", "atmospheric_observation", "positive", "footprint",
          "The passage of rain softens the mud beneath your boots.", "PASS"),
    _case("S16", "atmospheric_observation", "positive", "footprint",
          "Footprints record recent passage beneath a sheet of rain.", "PASS"),
    _case("S17", "speculation", "positive", "footprint",
          "The marks suggest movement through the area.", "PASS"),
    _case("S18", "incidental_gesture", "positive", "notice_success",
          "You fold your arms and study the board.", "PASS"),
    _case("S19", "atmospheric_observation", "positive", "notice_success",
          "A chipped ceramic cup sits beside the innkeeper.", "PASS"),
    _case("S20", "sensory_description", "positive", "notice_success",
          "You gain a sense of the surface texture.", "PASS"),
    _case("S21", "incidental_debris", "positive", "notice_success",
          "A little dust lies in your pack.", "PASS"),
    _case("S22", "emotional_tone", "positive", "notice_success",
          "You take your time before drawing conclusions.", "PASS"),
    _case("S23", "background_activity", "positive", "footprint",
          "A breeze passes through the courtyard.", "PASS"),
    _case("S24", "weather", "positive", "footprint",
          "Rain gathers beneath the wagon.", "PASS"),
    # Ambiguous consequential claims fail closed, without being called certain.
    _case("R1", "ambiguous_consequential", "ambiguous", "notice_success",
          "The compartment yields.", "REVIEW_REQUIRED", "ambiguous_consequential"),
    _case("R2", "ambiguous_consequential", "ambiguous", "notice_success",
          "The lock resists your efforts.", "REVIEW_REQUIRED", "ambiguous_consequential"),
    _case("R3", "ambiguous_consequential", "ambiguous", "notice_failed",
          "You have what you came for.", "FAIL", "unauthorized_acquisition"),
]
