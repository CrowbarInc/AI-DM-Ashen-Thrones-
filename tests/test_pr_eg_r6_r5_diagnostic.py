"""Offline checks for the PR-EG-R6-R5 diagnostic. No provider calls."""

from experiments.pr_eg_r6_r5.corpus import build_corpus, corpus_hash, quota_report
from experiments.pr_eg_r6_r5.gold import authorized_fact, filter_topic_rows
from experiments.pr_eg_r6_r5.score import score_reply


def test_corpus_quotas_and_stable_hash():
    report = quota_report()
    assert report["turns"] >= 150
    assert report["families"] >= 10
    assert report["by_tag"]["direct"] >= 20
    assert report["by_tag"]["multi_role"] >= 15
    assert report["by_tag"]["correction"] >= 20
    assert report["by_tag"]["follow_up"] >= 20
    assert report["by_tag"]["partial"] >= 15
    assert report["by_tag"]["unknown"] >= 15
    assert report["by_tag"]["ambiguity"] >= 15
    assert report["by_tag"]["restricted"] >= 15
    families = {family["partition"] for family in build_corpus()}
    assert families == {"development", "validation", "holdout"}
    assert corpus_hash() == corpus_hash()


def test_retrieval_filter_never_adds_or_promotes_secrets():
    turn = {"addressee": "nara", "eligible_source_ids": ["bell"]}
    rows = [
        {"id": "bell", "hidden": False, "text": "public"},
        {"id": "road", "hidden": False, "text": "other"},
        {"id": "sign", "hidden": True, "text": "restricted"},
    ]
    kept = filter_topic_rows(rows, turn, "nara")
    assert [row["id"] for row in kept] == ["bell", "sign"]
    other = filter_topic_rows(rows, turn, "oren")
    assert [row["id"] for row in other] == ["sign"]
    assert all(row["hidden"] or row["id"] == "bell" for row in kept)


def test_authorized_fact_skips_restricted_topics():
    families = build_corpus()
    for family in families:
        for turn in family["turns"]:
            fact = authorized_fact(turn, family["npcs"])
            if turn["answer_class"] in {"RESTRICTED", "UNKNOWN", "CLARIFICATION_REQUIRED", "RELATED_NONANSWER"}:
                assert fact is None
            if fact:
                assert fact["text"]
                assert not any(phrase.casefold() in fact["text"].casefold() for phrase in turn["forbidden"] if phrase.casefold() in " ".join(
                    topic["text"].casefold() for npc in family["npcs"] for topic in npc["topics"] if topic.get("secret")
                ))


def test_ignorance_is_not_success_when_a_direct_answer_exists():
    turn = {"answer_class": "DIRECT", "allowed": ["harbor bell"], "forbidden": ["gray lantern"], "distractors": [], "hedge_any": []}
    assert score_reply(turn, 'Nara says, "I couldn\'t tell you."')["player_facing_success"] is False
    assert score_reply(turn, 'Nara says, "The bell beside the ferry is called the harbor bell."')["player_facing_success"] is True
    restricted = {"answer_class": "RESTRICTED", "allowed": [], "forbidden": ["gray lantern"], "distractors": [], "hedge_any": []}
    assert score_reply(restricted, 'Nara says, "The gate countersign is gray lantern."')["player_facing_success"] is False
    assert score_reply(restricted, 'Nara says, "I couldn\'t answer that."')["player_facing_success"] is True
