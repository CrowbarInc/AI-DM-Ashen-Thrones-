"""PR-BR live-validation repair: decision attachment and sentence-safe fidelity.

Deterministic only. No gameplay or model calls.
"""
from __future__ import annotations

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    audit_narration_against_decision,
    narration_authority_fields,
)
from game.immutable_valid_response import run_preserve_if_valid
from game.live_resolution import attach_interaction_obligation
from game.ordinary_semantic_ownership import carry_authoritative_contract


GENERIC_NO_ANSWER = "No one here can answer that from what is settled here."


def _prebuilt(contract_id: str, operation: str, *, raw: str, **extra) -> dict:
    contract = {
        "contract_id": contract_id,
        "operation": operation,
        "raw_input": raw,
        "conversational_subject": raw,
        "expected_resolution": "answer",
        "dimensions": extra.pop("dimensions", []),
    }
    contract.update(extra)
    return {
        "kind": extra.get("kind") or operation,
        "metadata": {"resolution_contract": contract},
    }


def _attach(resolution: dict, *, player: str, scene: dict | None = None, world: dict | None = None) -> dict:
    attach_interaction_obligation(
        resolution,
        player_text=player,
        session={"active_scene_id": "yard", "turn_counter": 1},
        scene_id="yard",
        scene=scene,
        world=world,
    )
    return resolution


def _assert_pair(resolution: dict) -> None:
    contract = resolution["metadata"]["resolution_contract"]
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    assert contract["contract_id"]
    assert decision["contract_id"] == contract["contract_id"]
    fields = narration_authority_fields(resolution)
    assert fields["resolution_contract"]["contract_id"] == contract["contract_id"]
    assert fields["gm_resolution_decision"]["contract_id"] == decision["contract_id"]


def _scene(*facts: object, scene_id: str = "yard") -> dict:
    return {"scene": {"id": scene_id, "visible_facts": list(facts), "summary": "A work yard."}}


def _audit(text: str, resolution: dict, scene: dict) -> dict:
    corpus = "\n".join(
        item.get("text", "") if isinstance(item, dict) else str(item)
        for item in scene["scene"].get("visible_facts") or []
    )
    return audit_narration_against_decision(
        text,
        decision=resolution["metadata"][DECISION_METADATA_KEY],
        authored_corpus=corpus,
    )


def test_fresh_information_request_attaches_contract_and_decision():
    resolution = _attach({}, player="What does the pot smell like?")
    _assert_pair(resolution)
    assert resolution["metadata"]["resolution_contract"]["operation"]


def test_prebuilt_social_contract_attaches_decision():
    resolution = _prebuilt(
        "rc_social",
        "ask",
        raw="I ask Nessa whether she belongs to the Violet Compact.",
        interlocutor_id="nessa",
    )
    resolution["kind"] = "question"
    _attach(resolution, player="I ask Nessa whether she belongs to the Violet Compact.")
    _assert_pair(resolution)
    assert resolution["metadata"]["resolution_contract"]["retry_preserved"] is True


def test_prebuilt_movement_contract_attaches_decision():
    resolution = _prebuilt("rc_move", "follow", raw="I go to the reed drying loft.")
    resolution["kind"] = "scene_transition"
    resolution["target_scene_id"] = "reed_drying_loft"
    _attach(resolution, player="I go to the reed drying loft.")
    _assert_pair(resolution)
    mutations = resolution["metadata"][DECISION_METADATA_KEY]["permitted_state_mutations"]
    assert any(row.get("type") == "location" for row in mutations)


def test_prebuilt_perception_contract_attaches_decision():
    resolution = _prebuilt(
        "rc_perceive",
        "perceive",
        raw="What does the kiln look like?",
        dimensions=["appearance"],
    )
    _attach(resolution, player="What does the kiln look like?")
    _assert_pair(resolution)


def test_prebuilt_clarification_contract_attaches_decision():
    resolution = _prebuilt(
        "rc_clarify",
        "clarify",
        raw="Which one?",
        request_kind="clarification",
        ambiguous=True,
    )
    _attach(resolution, player="Which one?")
    _assert_pair(resolution)


def test_retry_preserved_contract_keeps_the_same_decision():
    resolution = _attach({}, player="What does the pot smell like?")
    first = resolution["metadata"][DECISION_METADATA_KEY]["contract_id"]
    _attach(resolution, player="What color is the sky?")
    assert resolution["metadata"]["resolution_contract"]["retry_preserved"] is True
    assert resolution["metadata"][DECISION_METADATA_KEY]["contract_id"] == first
    _assert_pair(resolution)


def test_carry_copies_decision_onto_replacement_resolution():
    source = _attach({}, player="I ask Nessa whether she belongs to the Violet Compact.")
    replacement = {"kind": "question", "social": {"npc_name": "Nessa"}, "metadata": {}}
    carried = carry_authoritative_contract(source, replacement)
    assert carried["metadata"]["resolution_contract"]["contract_id"] == source["metadata"]["resolution_contract"]["contract_id"]
    assert carried["metadata"][DECISION_METADATA_KEY]["contract_id"] == source["metadata"][DECISION_METADATA_KEY]["contract_id"]


def _kiln_scene() -> dict:
    return _scene(
        {
            "text": "The clay kiln is cold and its firing arch is cracked.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "clay_kiln",
                "subject_aliases": ["clay kiln", "kiln", "firing arch"],
                "relation": "condition",
                "value": "cracked",
                "value_aliases": ["cracked", "cold"],
                "polarity": "positive",
            },
        },
        scene_id="clay_kiln_yard",
    )


def _kiln_resolution() -> dict:
    scene = _kiln_scene()
    resolution = _prebuilt("rc_kiln", "ask", raw="Is the kiln still firing pots today?")
    _attach(resolution, player="Is the kiln still firing pots today?", scene=scene)
    return resolution


def test_turn1_kiln_not_firing_is_valid_and_positive_firing_is_not():
    scene = _kiln_scene()
    resolution = _kiln_resolution()
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    assert decision["answer_relations"]
    assert decision["answer_relations"][0]["kind"] == "derived_denial"
    assert decision["answer_relations"][0]["permitted_polarity"] == "negative"

    valid = _audit(
        "The clay kiln is cold and its firing arch is cracked. The kiln is not currently firing.",
        resolution,
        scene,
    )
    assert valid["hard_valid"] is True, valid

    denied_only = _audit("The kiln is not firing.", resolution, scene)
    assert denied_only["hard_valid"] is True, denied_only

    asserted = _audit("The kiln is firing pots today.", resolution, scene)
    assert asserted["hard_valid"] is False
    assert "unsupported_consequential_inference" in asserted["violations"][0]["reason_codes"]


def test_unrelated_negation_does_not_contradict_a_positive_fact():
    scene = _scene(
        {
            "text": "The cistern is split.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "cistern",
                "subject_aliases": ["cistern"],
                "relation": "condition",
                "value": "split",
                "value_aliases": ["split"],
                "polarity": "positive",
            },
        }
    )
    resolution = _prebuilt("rc_cistern", "ask", raw="Is the cistern still holding?")
    _attach(resolution, player="Is the cistern still holding?", scene=scene)
    audit = _audit("The cistern is split. It is not holding.", resolution, scene)
    assert audit["hard_valid"] is True, audit
    inverted = _audit("The cistern is not split.", resolution, scene)
    assert inverted["hard_valid"] is False


def test_turn2_social_decision_rejects_unauthored_meeting_place():
    scene = _scene("Nessa is splicing a rope at a low bench.", scene_id="net_loft")
    world = {"npcs": [{"id": "nessa", "name": "Nessa", "role": "net-mender"}]}
    resolution = _prebuilt(
        "rc_nessa",
        "ask",
        raw="I ask Nessa whether she belongs to the Violet Compact.",
        interlocutor_id="nessa",
    )
    _attach(
        resolution,
        player="I ask Nessa whether she belongs to the Violet Compact.",
        scene=scene,
        world=world,
    )
    _assert_pair(resolution)
    denial = _audit(
        '"I don\'t belong to the Violet Compact," Nessa says. "I keep to my nets."',
        resolution,
        scene,
    )
    assert denial["hard_valid"] is True, denial
    invented = _audit(
        '"If you are looking for them, they are known to gather at the docks or the market."',
        resolution,
        scene,
    )
    assert invented["hard_valid"] is False
    assert "unauthorized_social_world_fact" in invented["violations"][0]["reason_codes"]


def test_turn4_vat_realizes_across_sentences_and_rejects_cause_and_residue():
    scene = _scene(
        {
            "text": "A pale crust rings the lip of the copper dye vat, and the wool in it has gone stiff.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "dye_vat",
                "subject_aliases": ["copper dye vat", "dye vat", "vat", "wool"],
                "relation": "observation",
                "value": "stiff",
                "value_aliases": ["stiff", "pale crust", "crust", "gone stiff"],
                "polarity": "positive",
            },
        }
    )
    resolution = _prebuilt(
        "rc_vat",
        "ask",
        raw="I lean over the dye vat and try to tell what happened to the wool.",
    )
    _attach(resolution, player="I lean over the dye vat and try to tell what happened to the wool.", scene=scene)
    assert "cause" in resolution["metadata"][DECISION_METADATA_KEY]["unresolved_qualifiers"]
    valid = _audit(
        "You lean over the vat. A pale crust rings the lip of the vat. "
        "The wool inside has gone stiff. Nothing here establishes what caused it.",
        resolution,
        scene,
    )
    assert valid["hard_valid"] is True, valid
    unclear = _audit("What happened to the wool is unclear.", resolution, scene)
    assert unclear["hard_valid"] is True, unclear
    caused = _audit("The dyeing process halted prematurely and fouled the wool.", resolution, scene)
    assert caused["hard_valid"] is False
    residue = _audit("No obvious splashes or spills mar the area around the vat.", resolution, scene)
    assert residue["hard_valid"] is False
    assert "unauthorized_physical_residue" in residue["violations"][0]["reason_codes"]


def test_turn7_bell_unknown_actor_and_time_do_not_negate_the_crack():
    scene = _scene(
        {
            "text": "The chapel bell is cracked.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "chapel_bell",
                "subject_aliases": ["chapel bell", "bell"],
                "relation": "condition",
                "value": "cracked",
                "value_aliases": ["cracked"],
                "polarity": "positive",
            },
        }
    )
    player = "Who cracked the chapel bell, and when did it happen?"
    resolution = _prebuilt("rc_bell", "ask", raw=player)
    _attach(resolution, player=player, scene=scene)
    qualifiers = set(resolution["metadata"][DECISION_METADATA_KEY]["unresolved_qualifiers"])
    assert {"actor", "time"} <= qualifiers
    valid = _audit(
        "The bell is cracked, but no one here knows who damaged it or when it happened.",
        resolution,
        scene,
    )
    assert valid["hard_valid"] is True, valid
    named = _audit("Brother Hal cracked the bell yesterday.", resolution, scene)
    assert named["hard_valid"] is False
    codes = set(named["violations"][0]["reason_codes"])
    assert "unauthorized_qualifier:actor" in codes
    assert "unauthorized_qualifier:time" in codes


def test_novel_established_condition_unknown_cause_and_actor():
    scene = _scene(
        {
            "text": "The granary door is warped.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "granary_door",
                "subject_aliases": ["granary door", "door"],
                "relation": "condition",
                "value": "warped",
                "value_aliases": ["warped"],
                "polarity": "positive",
            },
        }
    )
    player = "Who warped the granary door, and what happened to it?"
    resolution = _prebuilt("rc_door", "ask", raw=player)
    _attach(resolution, player=player, scene=scene)
    valid = _audit(
        "The granary door is warped. Who did it is unknown, and the cause is not established.",
        resolution,
        scene,
    )
    assert valid["hard_valid"] is True, valid
    invalid = _audit("Marshal Odo broke the door because the hinge failed.", resolution, scene)
    assert invalid["hard_valid"] is False


def test_entity_mention_is_not_a_new_proposition():
    scene = _scene(
        {
            "text": "The loom is threaded.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "loom",
                "subject_aliases": ["loom"],
                "relation": "condition",
                "value": "threaded",
                "value_aliases": ["threaded"],
                "polarity": "positive",
            },
        }
    )
    resolution = _prebuilt("rc_loom", "perceive", raw="I look at the loom.", dimensions=["appearance"])
    _attach(resolution, player="I look at the loom.", scene=scene)
    audit = _audit("You lean over the loom.", resolution, scene)
    assert audit["hard_valid"] is True, audit


def test_turn3_uncertainty_remains_valid_with_decision():
    scene = _scene("Pell stands in the pan with a wooden rake.", scene_id="salt_pans")
    world = {"npcs": [{"id": "pell", "name": "Pell", "role": "salt-raker"}]}
    player = "I ask Pell whether the upstream tannery has been dumping lye into the brine."
    resolution = _prebuilt("rc_pell", "ask", raw=player, interlocutor_id="pell")
    _attach(resolution, player=player, scene=scene, world=world)
    _assert_pair(resolution)
    text = (
        '"I have no way to confirm that," Pell replies. '
        '"The upstream tannery\'s dealings are not something I keep watch over."'
    )
    assert _audit(text, resolution, scene)["hard_valid"] is True


def test_turn5_incidental_smell_and_clothing_remain_valid_with_decision():
    scene = _scene("Bram the baker is working behind the counter.", scene_id="bread_stall")
    world = {"npcs": [{"id": "bram", "name": "Bram", "role": "baker"}]}
    player = "What does the bread smell like, and what is the baker wearing?"
    resolution = _prebuilt("rc_bread", "ask", raw=player, interlocutor_id="bram")
    _attach(resolution, player=player, scene=scene, world=world)
    _assert_pair(resolution)
    text = (
        "The bread carries a warm yeasty aroma. "
        "Bram wears a worn linen shirt and a scuffed apron."
    )
    assert _audit(text, resolution, scene)["hard_valid"] is True


def test_turn6_movement_narration_agrees_with_destination_and_has_decision():
    scene = _scene("The ladder climbs to the reed drying loft.", scene_id="reed_landing")
    player = "I go to the reed drying loft."
    resolution = _prebuilt("rc_loft", "follow", raw=player)
    resolution["kind"] = "scene_transition"
    resolution["target_scene_id"] = "reed_drying_loft"
    _attach(resolution, player=player, scene=scene)
    _assert_pair(resolution)
    audit = _audit("You step into the reed drying loft, where cut reed hangs from the beams.", resolution, scene)
    assert audit["hard_valid"] is True, audit
    extra = _audit(
        "You arrive at the reed drying loft after discovering a hidden trail to the watchtower.",
        resolution,
        scene,
    )
    assert extra["hard_valid"] is False


def test_turn8_background_npc_answers_without_importance_marker():
    scene = _scene("The smokehouse down the lane has its shutters closed this morning.", scene_id="fish_stall")
    world = {"npcs": [{"id": "ila", "name": "Ila", "role": "fish-seller"}]}
    player = "I ask the fish-seller who she is and what she makes of the shuttered smokehouse."
    resolution = _prebuilt("rc_ila", "ask", raw=player, interlocutor_id="ila")
    _attach(resolution, player=player, scene=scene, world=world)
    _assert_pair(resolution)
    text = (
        'Ila says, "I am the fish seller. I cannot say why the smokehouse is closed today."'
    )
    audit = _audit(text, resolution, scene)
    assert audit["hard_valid"] is True, audit
    assert "[IMPORTANT]" not in text


def test_competent_answer_does_not_retry():
    scene = _kiln_scene()
    resolution = _kiln_resolution()
    calls = {"n": 0}

    def _retry(_note: str):
        calls["n"] += 1
        return {"player_facing_text": "unused", "metadata": {}}

    sealed = run_preserve_if_valid(
        {
            "player_facing_text": "The kiln is cold and cracked. It is not firing.",
            "metadata": {},
        },
        regenerate=_retry,
        resolution=resolution,
        player_text="Is the kiln still firing pots today?",
        scene=scene,
    )
    assert calls["n"] == 0
    assert sealed["metadata"]["accepted_response"]["provenance"] == "initial_generation"
    assert "not firing" in sealed["player_facing_text"]


def test_retry_receives_contract_decision_and_failure_then_accepts_correction():
    scene = _kiln_scene()
    resolution = _kiln_resolution()
    seen = {}

    def _retry(note: str):
        seen["note"] = note
        return {
            "player_facing_text": "The kiln is cold and cracked. It is not firing.",
            "metadata": {},
        }

    sealed = run_preserve_if_valid(
        {
            "player_facing_text": "The kiln is cold and cracked. The kiln is firing under a secret guild order.",
            "metadata": {},
        },
        regenerate=_retry,
        resolution=resolution,
        player_text="Is the kiln still firing pots today?",
        scene=scene,
    )
    note = seen["note"]
    assert "resolution_contract" in note
    assert "gm_resolution_decision" in note
    assert "rc_kiln" in note
    assert "unauthorized" in note or "validation_failure" in note
    assert sealed["metadata"]["accepted_response"]["provenance"] == "regeneration"
    assert "secret guild" not in sealed["player_facing_text"]
    review = sealed["metadata"]["decision_review"]
    assert review["governing_decision_contract_id"] == "rc_kiln"
    assert review["retry_context"]
    assert review["attempt_1"]["gm_resolution_decision_audit"]
    assert review["acceptance"]["why"] == "regeneration_hard_valid"


def test_established_answer_does_not_collapse_to_generic_nonresolution():
    scene = _scene(
        {
            "text": "The chapel bell is cracked.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "chapel_bell",
                "subject_aliases": ["chapel bell", "bell"],
                "relation": "condition",
                "value": "cracked",
                "value_aliases": ["cracked"],
                "polarity": "positive",
            },
        }
    )
    player = "Who cracked the chapel bell, and when did it happen?"
    resolution = _prebuilt("rc_bell_fallback", "ask", raw=player)
    _attach(resolution, player=player, scene=scene)

    def _retry(_note: str):
        return {
            "player_facing_text": "Brother Hal cracked the bell yesterday, and the frame fell because of a storm.",
            "metadata": {},
        }

    sealed = run_preserve_if_valid(
        {
            "player_facing_text": "Brother Hal cracked the bell yesterday.",
            "metadata": {},
        },
        regenerate=_retry,
        resolution=resolution,
        player_text=player,
        scene=scene,
    )
    text = sealed["player_facing_text"]
    assert text != GENERIC_NO_ANSWER
    assert "cracked" in text.lower()
    assert "Brother Hal" not in text
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] in {
        "authorized_observation",
        "bounded_sentence_preservation",
    }
    audit = sealed["metadata"]["accepted_response"]["hard_validation"].get("gm_resolution_decision_audit")
    assert audit is not None


def test_bounded_preservation_keeps_valid_sentences_after_failed_retry():
    scene = _kiln_scene()
    resolution = _kiln_resolution()

    def _retry(_note: str):
        return {
            "player_facing_text": "The kiln is firing because thieves ordered a new arch.",
            "metadata": {},
        }

    sealed = run_preserve_if_valid(
        {
            "player_facing_text": (
                "The clay kiln is cold and its firing arch is cracked. "
                "A hidden guild ordered the firing stopped yesterday."
            ),
            "metadata": {},
        },
        regenerate=_retry,
        resolution=resolution,
        player_text="Is the kiln still firing pots today?",
        scene=scene,
    )
    text = sealed["player_facing_text"]
    assert "cold" in text.lower() or "cracked" in text.lower()
    assert "hidden guild" not in text.lower()
    assert text != GENERIC_NO_ANSWER
    assert sealed["metadata"]["accepted_response"]["immutable"] is True
