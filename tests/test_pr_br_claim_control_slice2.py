"""PR-BR claim-control slice 2 adversarial paraphrases.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

from game.gm_resolution_decision import (
    AUTH_CLAIM,
    AUTH_OBSERVATION,
    AUTH_WORLD,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_NPC_CLAIM,
    PROVENANCE_PLAYER_HYPOTHESIS,
    REL_EPISTEMIC_STATUS,
    REL_OBSERVATION,
    STATUS_HYPOTHESIS,
    STATUS_INFERRED,
    audit_narration_against_decision,
    remember_temporal_claims,
)
from game.immutable_valid_response import run_preserve_if_valid
from tests.test_pr_br_claim_control_slice1 import _audit, _decision, _fact


def _assert_rejected(decision: dict, texts: list[str], expected: set[str]) -> None:
    for text in texts:
        audit = _audit(text, decision)
        reasons = {reason for row in audit["claim_results"] for reason in row["reason_codes"]}
        assert audit["hard_valid"] is False, (text, audit)
        assert reasons & expected, (text, reasons)


def _relation_fact(text: str, subject: str, value: str, relation: str, aliases: list[str]) -> dict:
    row = _fact(text, subject, value, relation_kind=relation)
    row["semantic_identity"]["relation"] = relation
    row["semantic_identity"]["value_aliases"].extend(aliases)
    return row


def test_actor_attribution_paraphrases_do_not_launder_authorized_condition():
    decision = _decision(_fact("The gate hinge is broken.", "gate hinge", "broken"), unresolved=("actor",))
    _assert_rejected(
        decision,
        [
            "Someone from the guild broke the hinge.",
            "Guild hands did this.",
            "This was the guild's work.",
            "The damage belongs to the guild.",
            "You can tell guild workers were responsible.",
        ],
        {"unauthorized_actor_attribution", "unowned_stateful_world_assertion"},
    )


def test_cause_attribution_paraphrases_do_not_launder_authorized_condition():
    decision = _decision(_fact("The orchard trees are dead.", "orchard trees", "dead"), unresolved=("cause",))
    _assert_rejected(
        decision,
        [
            "The trees died from tainted runoff.",
            "Tainted runoff killed them.",
            "Their death came from poisoned drainage.",
            "Bad water is what finished the orchard.",
            "The drainage explains the dead trees.",
        ],
        {"unauthorized_cause_attribution", "unauthorized_causal_relation", "unowned_stateful_world_assertion"},
    )


def test_time_and_history_paraphrases_do_not_launder_authorized_condition():
    door = _decision(_fact("The warehouse door is forced open.", "warehouse door", "forced open"), unresolved=("time",))
    _assert_rejected(
        door,
        [
            "It was forced sometime before dawn.",
            "The break-in happened overnight.",
            "This was done last night.",
            "The damage is only a few hours old.",
            "Whoever did it came through before sunrise.",
        ],
        {"unauthorized_time_attribution", "unauthorized_history_assertion", "unauthorized_qualifier:time"},
    )

    statue = _decision(_fact("The shrine statue is missing.", "shrine statue", "missing"), unresolved=("actor", "time"))
    _assert_rejected(
        statue,
        [
            "It was removed during yesterday's procession.",
            "Someone took it after the priests left.",
            "The statue used to stand here until last night.",
            "This is where it stood before thieves carried it off.",
        ],
        {"unauthorized_actor_attribution", "unauthorized_time_attribution", "unauthorized_history_assertion"},
    )


def test_relationship_and_cueless_residuals_without_classic_relation_words_are_rejected():
    relation = _decision(
        _fact("The window is open.", "window", "open"),
        _fact("The desk is disturbed.", "desk", "disturbed"),
        unresolved=("actor", "cause"),
    )
    _assert_rejected(
        relation,
        [
            "The open window explains the disturbed desk.",
            "Whoever came through the window searched the desk.",
            "The desk was disturbed because someone entered there.",
            "Taken together, the window and desk point to an intruder.",
            "Those two details tell the same story: someone climbed inside.",
        ],
        {"unauthorized_actor_attribution", "unauthorized_cause_attribution", "unauthorized_evidential_relation"},
    )

    cases = [
        (_decision(_fact("The rope is cut.", "rope", "cut"), unresolved=("actor",)), "A smuggler's knife did that."),
        (_decision(_fact("The grain sacks are wet.", "grain sacks", "wet"), unresolved=("cause", "time")), "River water got into the storehouse overnight."),
        (_decision(_fact("The lock is damaged.", "lock", "damaged"), unresolved=("actor",)), "Two people worked on it from opposite sides."),
        (_decision(_fact("The cart is abandoned.", "cart", "abandoned"), unresolved=("actor", "time")), "The driver fled toward the southern farms."),
        (_decision(_fact("The altar cloth is burned.", "altar cloth", "burned"), unresolved=("actor",)), "The priest destroyed it himself."),
    ]
    for decision, text in cases:
        audit = _audit(text, decision)
        assert audit["hard_valid"] is False, (text, audit)


def test_false_positive_controls_remain_speakable():
    controls = [
        (_decision(_fact("The rope is cut.", "rope", "cut"), unresolved=("actor",)), "The cut rope hangs loosely."),
        (_decision(_fact("The grain sacks are wet.", "grain sacks", "wet"), unresolved=("cause", "time")), "The wet sacks smell musty."),
        (_decision(_fact("The lock is damaged.", "lock", "damaged"), unresolved=("actor",)), "The damaged lock is cold under your fingers."),
        (_decision(_fact("The cart is abandoned.", "cart", "abandoned"), unresolved=("actor", "time")), "Dust has settled on the abandoned cart."),
        (_decision(_fact("The altar cloth is burned.", "altar cloth", "burned"), unresolved=("actor",)), "The burned cloth leaves soot on the stone."),
    ]
    for decision, text in controls:
        assert _audit(text, decision)["hard_valid"] is True, text

    unresolved_lines = [
        (_decision(_fact("The rope is cut.", "rope", "cut"), unresolved=("actor",)), "You don't know who cut it."),
        (_decision(_fact("The grain sacks are wet.", "grain sacks", "wet"), unresolved=("time",)), "Nothing here tells you when the sacks got wet."),
        (_decision(_fact("The lock is damaged.", "lock", "damaged"), unresolved=("actor",)), "The damage alone doesn't identify who worked on the lock."),
        (_decision(_fact("The cart is abandoned.", "cart", "abandoned"), unresolved=("cause",)), "Why the driver left is still unclear."),
        (_decision(_fact("The altar cloth is burned.", "altar cloth", "burned"), unresolved=("actor",)), "The cloth is burned; who did it remains unknown."),
    ]
    for decision, text in unresolved_lines:
        assert _audit(text, decision)["hard_valid"] is True, text


def test_epistemic_certainty_and_player_presupposition_do_not_promote_inference():
    decision = _decision(
        _fact("The gate hinge is broken.", "gate hinge", "broken"),
        _relation_fact("Sabotage is possible.", "sabotage", "possible", REL_EPISTEMIC_STATUS, ["deliberate damage"]),
        unresolved=("actor", "cause"),
    )
    permitted = [
        "One possibility is sabotage.",
        "Sabotage could explain it.",
        "It might have been deliberate.",
        "You can't rule out deliberate damage.",
        "If it was sabotage, the actor is still unknown.",
    ]
    for text in permitted:
        assert _audit(text, decision)["hard_valid"] is True, text

    established = [
        "It was sabotage.",
        "Clearly, someone sabotaged it.",
        "There is no doubt this was deliberate.",
        "That confirms sabotage.",
        "So that's what happened.",
        "Now we know someone did this deliberately.",
    ]
    _assert_rejected(
        decision,
        established,
        {
            "unauthorized_actor_attribution",
            "unauthorized_certainty_upgrade",
            "unauthorized_consequential_residual",
            "unauthorized_causal_relation",
        },
    )

    session = {"active_scene_id": "gate", "turn_counter": 3}
    remember_temporal_claims(
        session,
        claims=[
            {
                "text": "Sabotage is possible.",
                "semantic_identity": {"subject": "sabotage", "relation": "possibility"},
                "provenance": PROVENANCE_GM_INFERENCE,
                "authority": AUTH_OBSERVATION,
                "epistemic_status": STATUS_INFERRED,
                "relation_kind": REL_EPISTEMIC_STATUS,
                "authorized": True,
            }
        ],
        scene_id="gate",
        source_turn=3,
    )
    player_claims = [
        "If it was sabotage, who had access?",
        "Assuming someone sabotaged it, who could get in?",
        "So the saboteur would've needed access, right?",
        "Whoever sabotaged it must have come through here?",
        "Let's say you're right and it was sabotage - who benefits?",
        "Since it was sabotage, who did it?",
    ]
    for text in player_claims:
        remember_temporal_claims(
            session,
            claims=[
                {
                    "text": text,
                    "semantic_identity": {"subject": "sabotage", "relation": "hypothesis"},
                    "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
                    "authority": AUTH_OBSERVATION,
                    "epistemic_status": STATUS_HYPOTHESIS,
                    "relation_kind": REL_EPISTEMIC_STATUS,
                    "authorized": True,
                }
            ],
            scene_id="gate",
            source_turn=4,
        )
    record = session["narration_temporal_provenance"]
    assert record["gm_inferences"][0]["authority"] != AUTH_WORLD
    assert all(row["authority"] != AUTH_WORLD for row in record["player_hypotheses"])


def test_npc_repetition_remains_claim_only_while_explicit_authority_still_works():
    decision = _decision(_fact("The gate hinge is broken.", "gate hinge", "broken"), unresolved=("actor",))
    claim = audit_narration_against_decision(
        'Mira says, "Guild hands did this, or so I heard."',
        decision=decision,
        authored_corpus="",
    )
    assert claim["hard_valid"] is True
    assert claim["proposed_facts"][0]["authority"] == AUTH_CLAIM
    assert claim["proposed_facts"][0]["provenance"] == PROVENANCE_NPC_CLAIM

    established = _decision(
        _fact("The gate hinge is broken.", "gate hinge", "broken"),
        _relation_fact(
            "A guild worker broke the hinge.",
            "gate hinge",
            "guild worker broke",
            "actor_attribution",
            ["guild hands did this", "guild workers were responsible"],
        ),
    )
    established["proposed_facts"][1]["semantic_identity"]["subject_aliases"].append("this")
    assert _audit("Guild hands did this.", established)["hard_valid"] is True


def test_mixed_and_multisentence_preservation_drop_only_unsafe_residuals():
    decision = _decision(_fact("The rope is cut.", "rope", "cut"), unresolved=("actor",))
    valid_lines = [
        "The rope is cut and the rope hangs loosely.",
        "The cut rope hangs loosely.",
        "The rope is cut, and someone might have done it.",
        "The rope is cut; who did it remains unknown.",
    ]
    for text in valid_lines:
        assert _audit(text, decision)["hard_valid"] is True, text

    invalid_lines = [
        "The rope is cut, and a smuggler's knife did that.",
        "The cut rope hangs loosely, and a smuggler's knife did that.",
        "Someone might have cut it, so now we know the smuggler did it.",
        'Mira says, "Maybe it was a smuggler," so the smuggler cut it.',
    ]
    for text in invalid_lines:
        assert _audit(text, decision)["hard_valid"] is False, text

    resolution = {"metadata": {"gm_resolution_decision": decision}}
    mixed = "The rope is cut. A smuggler's knife did that. Who did it remains unknown."
    sealed = run_preserve_if_valid(
        {"player_facing_text": mixed, "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="What happened to the rope?",
    )
    assert "rope is cut" in sealed["player_facing_text"].lower()
    assert "smuggler" not in sealed["player_facing_text"].lower()
    assert "unknown" in sealed["player_facing_text"].lower()


def test_temporal_provenance_caps_scope_and_explicit_promotion_is_precise():
    session = {"active_scene_id": "bridge", "turn_counter": 1}
    for index in range(30):
        remember_temporal_claims(
            session,
            claims=[
                {
                    "text": f"Rejected claim {index}",
                    "semantic_identity": {"subject": f"claim_{index}", "relation": "event"},
                    "provenance": "generated_proposal",
                    "authority": "unauthorized",
                    "epistemic_status": "unresolved",
                    "relation_kind": "actor_attribution",
                    "authorized": False,
                    "reason_codes": ["unauthorized_actor_attribution"],
                }
            ],
            scene_id="bridge",
            source_turn=index,
            cap=24,
        )
    record = session["narration_temporal_provenance"]
    assert len(record["rejected_consequential"]) == 24
    assert record["rejected_consequential"][0]["text"] == "Rejected claim 6"

    established = _decision(
        _fact("The bridge cable is severed.", "bridge cable", "severed"),
        _relation_fact(
            "A mason cut the bridge cable.",
            "bridge cable",
            "mason cut",
            "actor_attribution",
            ["mason cut the bridge cable"],
        ),
        _fact("The bridge railing is damaged.", "bridge railing", "damaged"),
    )
    assert _audit("A mason cut the bridge cable.", established)["hard_valid"] is True
    assert _audit("A mason cut the bridge railing.", established)["hard_valid"] is False


def test_claim_identity_collisions_do_not_cross_authorize_nearby_propositions():
    collision_cases = [
        (
            _decision(_fact("The bridge cable is severed.", "bridge cable", "severed")),
            "The bridge railing is damaged.",
        ),
        (_decision(_fact("The sheep is ill.", "sheep", "ill")), "The shepherd is ill."),
        (_decision(_fact("The warehouse shelf is empty.", "warehouse shelf", "empty")), "The warehouse is locked."),
        (_decision(_fact("The ledger is burned.", "ledger", "burned")), "The ledger is missing."),
    ]
    for decision, text in collision_cases:
        assert _audit(text, decision)["hard_valid"] is False, text
