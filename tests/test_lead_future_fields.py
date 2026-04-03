"""Schema normalization, create_lead, and upsert behavior for extended lead fields."""

from __future__ import annotations

import pytest

from game.leads import (
    add_lead_tag,
    create_lead,
    get_lead,
    get_lead_tags,
    normalize_lead,
    upsert_lead,
)

pytestmark = pytest.mark.unit


def test_normalize_lead_backfills_new_list_fields_and_metadata():
    raw: dict = {"id": "x", "title": "X"}
    normalize_lead(raw)

    assert raw["related_faction_ids"] == []
    assert raw["related_scene_ids"] == []
    assert raw["tags"] == []
    assert raw["evidence_clue_ids"] == []
    assert raw["consequence_ids"] == []
    assert raw["metadata"] == {}
    assert raw.get("commitment_source") is None
    assert raw.get("commitment_strength") is None


def test_normalize_lead_new_lists_are_fresh_objects_each_call():
    a: dict = {"id": "a", "title": "A"}
    b: dict = {"id": "b", "title": "B"}
    normalize_lead(a)
    normalize_lead(b)

    assert a["related_faction_ids"] is not b["related_faction_ids"]
    assert a["tags"] is not b["tags"]
    assert a["metadata"] is not b["metadata"]


def test_normalize_lead_id_lists_dedupe_drop_blanks_deterministic_order():
    raw = {
        "id": "z",
        "title": "Z",
        "related_faction_ids": [" f1 ", "f2", "f1", "", None],
        "tags": ["b", "a", "b"],
        "evidence_clue_ids": ("c1", "c1", "c2"),
        "consequence_ids": [" z ", "z", "w"],
    }
    normalize_lead(raw)

    assert raw["related_faction_ids"] == ["f1", "f2"]
    assert raw["tags"] == ["b", "a"]
    assert raw["evidence_clue_ids"] == ["c1", "c2"]
    assert raw["consequence_ids"] == ["z", "w"]


def test_normalize_lead_metadata_fresh_dict_non_mapping_to_empty():
    raw = {
        "id": "m",
        "title": "M",
        "metadata": {"keep": 1, "nested": {"x": 2}},
    }
    normalize_lead(raw)
    assert raw["metadata"] == {"keep": 1, "nested": {"x": 2}}
    raw["metadata"]["keep"] = 99
    assert raw["metadata"]["keep"] == 99

    raw2 = {"id": "m2", "title": "M2", "metadata": "not-a-mapping"}
    normalize_lead(raw2)
    assert raw2["metadata"] == {}


def test_create_lead_accepts_extended_fields():
    lead = create_lead(
        title="T",
        summary="S",
        id="lead-1",
        related_faction_ids=["fa", "fa", "fb"],
        related_scene_ids=["sc1"],
        tags=["alpha", "beta", "alpha"],
        evidence_clue_ids=["clue-a", "clue-b"],
        metadata={"source": "test", "n": 2},
    )

    assert lead["related_faction_ids"] == ["fa", "fb"]
    assert lead["related_scene_ids"] == ["sc1"]
    assert lead["tags"] == ["alpha", "beta"]
    assert lead["evidence_clue_ids"] == ["clue-a", "clue-b"]
    assert lead["metadata"] == {"source": "test", "n": 2}


def test_create_lead_accepts_commitment_metadata_fields():
    lead = create_lead(
        title="C",
        summary="",
        id="commit-lead",
        commitment_source="player_choice",
        commitment_strength=3,
    )
    assert lead["commitment_source"] == "player_choice"
    assert lead["commitment_strength"] == 3


def test_upsert_preserves_metadata_and_extended_lists_when_absent_from_payload():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="A",
            summary="",
            id="a",
            metadata={"k": "v"},
            tags=["t1"],
            evidence_clue_ids=["e1"],
        ),
    )
    stored = get_lead(session, "a")
    assert stored is not None
    meta_id = id(stored["metadata"])

    upsert_lead(session, {"id": "a", "title": "A2"})

    after = get_lead(session, "a")
    assert after is not None
    assert after["metadata"] == {"k": "v"}
    assert after["metadata"] is stored["metadata"]
    assert id(after["metadata"]) == meta_id
    assert after["tags"] == ["t1"]
    assert after["evidence_clue_ids"] == ["e1"]


def test_upsert_explicit_overwrite_extended_fields_matches_scalar_overwrite():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="B",
            summary="",
            id="b",
            metadata={"old": True},
            tags=["x"],
            related_faction_ids=["f1"],
        ),
    )

    upsert_lead(
        session,
        {
            "id": "b",
            "title": "B",
            "metadata": {"new": 1},
            "tags": ["y", "y"],
            "related_faction_ids": ["f2", "f1"],
        },
    )

    row = get_lead(session, "b")
    assert row is not None
    assert row["metadata"] == {"new": 1}
    assert row["tags"] == ["y"]
    assert row["related_faction_ids"] == ["f2", "f1"]


def test_upsert_explicit_empty_metadata_replaces():
    session: dict = {}
    upsert_lead(session, create_lead(title="C", summary="", id="c", metadata={"x": 1}))
    upsert_lead(session, {"id": "c", "title": "C", "metadata": {}})
    assert get_lead(session, "c")["metadata"] == {}


def test_add_lead_tag_and_get_lead_tags():
    session: dict = {}
    upsert_lead(session, create_lead(title="D", summary="", id="d", tags=["a"]))

    add_lead_tag(session, "d", "b", turn=1)
    assert get_lead_tags(session, "d") == ["a", "b"]

    add_lead_tag(session, "d", "b", turn=2)
    assert get_lead_tags(session, "d") == ["a", "b"]


def test_get_lead_tags_returns_fresh_list():
    session: dict = {}
    upsert_lead(session, create_lead(title="E", summary="", id="e", tags=["z"]))
    a = get_lead_tags(session, "e")
    b = get_lead_tags(session, "e")
    assert a == ["z"]
    assert a is not b


@pytest.mark.parametrize("bad_meta", [None, "x", 3, []])
def test_create_lead_normalizes_bad_metadata_to_empty(bad_meta):
    lead = create_lead(title="F", summary="", id="f", metadata=bad_meta)  # type: ignore[arg-type]
    assert lead["metadata"] == {}
