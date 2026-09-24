"""PR-BK: remembered dialogue is not automatically a reusable structured fact."""
from __future__ import annotations

from game.response_policy_enforcement import apply_response_policy_enforcement
from game.social import (
    GENERATIVE_LAST_ANSWER_PROVENANCE,
    select_best_social_answer_candidate,
)
from game.storage import get_npc_runtime, get_scene_runtime

KILN_FACT = "The ash sluice was barred after the night firing failed."
DOCK_FACT = "The cedar wharf tally names three unpaid cooperage lots."
UNSUPPORTED = (
    "The harbor warden will see anyone who asks, and the roster board lists open watches "
    "if you introduce yourself first."
)
REFUSAL = "I do not know that. Ask someone who keeps the books."
PARAPHRASE = "Word is, the ash sluice stayed shut once the night firing went wrong."
CUTOFF = "The porter begins to respond before a cart bell pulls their attention away."


def _session(scene_id: str, npc_id: str, topic_key: str, last_answer: str = "") -> dict:
    session = {
        "active_scene_id": scene_id,
        "turn_counter": 4,
        "npc_runtime": {},
        "scene_runtime": {
            scene_id: {
                "topic_pressure_current": {
                    "topic_key": topic_key,
                    "speaker_key": npc_id,
                    "interaction_kind": "social",
                    "interaction_mode": "social",
                    "social_intent_class": "social_exchange",
                    "npc_name": npc_id,
                },
                "topic_pressure": {
                    topic_key: {
                        "last_answer": last_answer,
                        "repeat_count": 2,
                        "speaker_targets": {npc_id: {"repeat_count": 2}},
                    }
                },
            }
        },
    }
    return session


def _resolution(npc_id: str, reply_kind: str = "explanation") -> dict:
    return {
        "kind": "social_probe",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": npc_id.replace("_", " ").title(),
            "reply_kind": reply_kind,
            "topic_revealed": None,
        },
    }


def _world(npc_id: str, topic_id: str, fact: str) -> dict:
    return {
        "npcs": [
            {
                "id": npc_id,
                "name": npc_id.replace("_", " ").title(),
                "location": "kiln_yard" if "porter" in npc_id else "cedar_wharf",
                "topics": [{"id": topic_id, "text": fact}],
            }
        ]
    }


def _select(session, scene_id, npc_id, player, resolution, world=None):
    return select_best_social_answer_candidate(
        session=session,
        scene_id=scene_id,
        npc_id=npc_id,
        topic_key=None,
        player_text=player,
        resolution=resolution,
        world=world,
    )


def _commit(session, scene_id, npc_id, reply, resolution, world=None):
    apply_response_policy_enforcement(
        {"player_facing_text": reply, "tags": [], "metadata": {}, "debug_notes": ""},
        response_policy={
            "must_answer": False,
            "forbid_state_invention": False,
            "forbid_secret_leak": False,
            "diegetic_only": False,
            "prefer_scene_momentum": False,
            "prefer_specificity": False,
        },
        player_text="What do you know about the sluice?",
        scene_envelope={"scene": {"id": scene_id}},
        session=session,
        world=world or {"npcs": []},
        resolution=resolution,
        discovered_clues=[],
    )


def test_probe_a_unsupported_prose_is_not_selected() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", UNSUPPORTED)
    entry = get_scene_runtime(session, "kiln_yard")["topic_pressure"]["topic:sluice"]
    entry["last_answer_provenance"] = GENERATIVE_LAST_ANSWER_PROVENANCE
    cand = _select(
        session,
        "kiln_yard",
        "night_porter",
        "Where can I find the harbor warden?",
        _resolution("night_porter"),
        _world("night_porter", "sluice_barred", KILN_FACT),
    )
    assert cand.get("source") != "topic_pressure:last_answer"
    assert "harbor warden" not in str(cand.get("text") or "").lower()
    assert entry["last_answer"] == UNSUPPORTED


def test_probe_b_authored_prior_answer_remains_reusable() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", KILN_FACT)
    get_npc_runtime(session, "night_porter")["revealed_topics"] = ["sluice_barred"]
    world = _world("night_porter", "sluice_barred", KILN_FACT)
    cand = _select(
        session,
        "kiln_yard",
        "night_porter",
        "Why is that?",
        _resolution("night_porter"),
        world,
    )
    assert cand.get("source") == "topic_pressure:last_answer"
    assert "night firing" in str(cand.get("text") or "").lower()


def test_probe_c_cutoff_stays_ineligible() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", CUTOFF)
    cand = _select(
        session,
        "kiln_yard",
        "night_porter",
        "Tell me about the sluice.",
        _resolution("night_porter"),
    )
    assert cand.get("source") != "topic_pressure:last_answer"
    assert "begins to respond" not in str(cand.get("text") or "").lower()


def test_probe_d_refusal_commit_does_not_become_fact() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", "")
    resolution = _resolution("night_porter", "refusal")
    _commit(session, "kiln_yard", "night_porter", REFUSAL, resolution)
    entry = get_scene_runtime(session, "kiln_yard")["topic_pressure"]["topic:sluice"]
    assert entry["last_answer"] == REFUSAL
    assert entry["last_answer_provenance"] == GENERATIVE_LAST_ANSWER_PROVENANCE
    cand = _select(
        session,
        "kiln_yard",
        "night_porter",
        "Why is that?",
        resolution,
    )
    assert cand.get("source") != "topic_pressure:last_answer"
    assert "books" not in str(cand.get("text") or "").lower()


def test_probe_e_paraphrase_keeps_payload_not_prose() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", "")
    get_npc_runtime(session, "night_porter")["revealed_topics"] = ["sluice_barred"]
    world = _world("night_porter", "sluice_barred", KILN_FACT)
    resolution = _resolution("night_porter")
    _commit(session, "kiln_yard", "night_porter", PARAPHRASE, resolution, world)
    entry = get_scene_runtime(session, "kiln_yard")["topic_pressure"]["topic:sluice"]
    assert entry["last_answer"] == PARAPHRASE
    assert entry["last_answer_provenance"] == "authored_topic"
    assert entry["last_answer_authoritative_text"] == KILN_FACT
    cand = _select(
        session,
        "kiln_yard",
        "night_porter",
        "Why is that?",
        resolution,
        world,
    )
    assert cand.get("source") == "topic_pressure:last_answer"
    assert "night firing failed" in str(cand.get("text") or "").lower()
    assert "went wrong" not in str(cand.get("text") or "").lower()


def test_probe_f_same_turn_prose_cannot_promote_itself() -> None:
    session = _session("cedar_wharf", "tally_clerk", "topic:lots", "")
    resolution = _resolution("tally_clerk")
    _commit(session, "cedar_wharf", "tally_clerk", UNSUPPORTED, resolution)
    cand = _select(
        session,
        "cedar_wharf",
        "tally_clerk",
        "Will the harbor warden see me?",
        resolution,
    )
    assert cand.get("source") != "topic_pressure:last_answer"
    assert cand.get("answer_kind") == "refusal"


def test_probe_g_cross_turn_prose_stays_continuity() -> None:
    session = _session("cedar_wharf", "tally_clerk", "topic:lots", UNSUPPORTED)
    entry = get_scene_runtime(session, "cedar_wharf")["topic_pressure"]["topic:lots"]
    entry["last_answer_provenance"] = GENERATIVE_LAST_ANSWER_PROVENANCE
    cand = _select(
        session,
        "cedar_wharf",
        "tally_clerk",
        "How do I get an introduction?",
        _resolution("tally_clerk"),
    )
    assert cand.get("source") not in {
        "topic_pressure:last_answer",
        "structured_fact_candidate_emission",
    }
    assert "introduction" not in str(cand.get("text") or "").lower()
    assert entry["last_answer"] == UNSUPPORTED


def test_probe_h_different_npc_topic_family() -> None:
    session = _session("cedar_wharf", "tally_clerk", "topic:lots", DOCK_FACT)
    get_npc_runtime(session, "tally_clerk")["revealed_topics"] = ["unpaid_lots"]
    world = _world("tally_clerk", "unpaid_lots", DOCK_FACT)
    cand = _select(
        session,
        "cedar_wharf",
        "tally_clerk",
        "Why is that?",
        _resolution("tally_clerk"),
        world,
    )
    assert cand.get("source") == "topic_pressure:last_answer"
    assert "cooperage" in str(cand.get("text") or "").lower()


def test_human_shape_unsupported_access_claim_fails_closed() -> None:
    session = _session("kiln_yard", "night_porter", "topic:sluice", "")
    resolution = _resolution("night_porter", "refusal")
    resolution["social"]["topic_revealed"] = None
    invented = (
        "The yard captain keeps open hours and will speak if you have already been introduced."
    )
    _commit(session, "kiln_yard", "night_porter", invented, resolution)
    entry = get_scene_runtime(session, "kiln_yard")["topic_pressure"]["topic:sluice"]
    follow = _select(
        session,
        "kiln_yard",
        "night_porter",
        "So the captain will see me if I introduce myself?",
        resolution,
    )
    assert entry["last_answer_provenance"] == GENERATIVE_LAST_ANSWER_PROVENANCE
    assert follow.get("source") != "topic_pressure:last_answer"
    assert follow.get("answer_kind") == "refusal"
    assert resolution["social"].get("topic_revealed") in (None, {})
