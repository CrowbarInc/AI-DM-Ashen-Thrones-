"""AT-OPT-04 mixed-key turn-packet policy deduplication.

Provider-free. Equality is the existing JSON comparison in game.gm.
Python's True == 1 is not that comparison and must not collapse a key.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from game.gm import _json_value_equal, omit_duplicate_turn_packet_policy

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _apply(payload):
    original = copy.deepcopy(payload)
    nested = None
    packet = payload.get("turn_packet") if isinstance(payload, dict) else None
    if isinstance(packet, dict) and isinstance(packet.get("response_policy"), dict):
        nested = packet["response_policy"]
    first = omit_duplicate_turn_packet_policy(payload)
    assert payload == original
    if nested is not None:
        assert payload["turn_packet"]["response_policy"] is nested
    if isinstance(payload, dict) and isinstance(payload.get("response_policy"), dict) and isinstance(first, dict):
        assert first["response_policy"] is payload["response_policy"]
    second = omit_duplicate_turn_packet_policy(first)
    assert _serialized(first) == _serialized(second)
    return first


def test_all_nested_keys_identical_omits_nested_policy() -> None:
    policy = {"answer_completeness": {"must": True}, "tone": "firm"}
    payload = {
        "response_policy": policy,
        "turn_packet": {"version": 1, "response_policy": {"answer_completeness": {"must": True}, "tone": "firm"}},
    }
    projected = _apply(payload)
    assert "response_policy" not in projected["turn_packet"]
    assert projected["turn_packet"]["version"] == 1
    assert projected["response_policy"] == policy


def test_all_nested_keys_different_preserves_nested_policy() -> None:
    payload = {
        "response_policy": {"answer_completeness": {"must": True}, "tone": "firm"},
        "turn_packet": {"response_policy": {"answer_completeness": {"must": False}, "tone": "soft"}},
    }
    projected = _apply(payload)
    assert projected["turn_packet"]["response_policy"] == {
        "answer_completeness": {"must": False},
        "tone": "soft",
    }
    assert projected is payload


def test_mixed_keys_remove_only_identical_values() -> None:
    payload = {
        "response_policy": {
            "rule_priority_order": ["scene", "policy"],
            "must_answer": True,
            "answer_completeness": {"must": True, "answer_exposition_plan": {"steps": 1}},
        },
        "turn_packet": {
            "version": 4,
            "response_policy": {
                "rule_priority_order": ["scene", "policy"],
                "must_answer": True,
                "answer_completeness": {"must": True},
            },
        },
    }
    projected = _apply(payload)
    nested = projected["turn_packet"]["response_policy"]
    assert list(nested) == ["answer_completeness"]
    assert nested["answer_completeness"] == {"must": True}
    assert "answer_exposition_plan" not in nested["answer_completeness"]
    assert projected["response_policy"]["must_answer"] is True
    assert projected["turn_packet"]["version"] == 4


def test_root_absent_nested_key_is_preserved() -> None:
    payload = {
        "response_policy": {"must_answer": True},
        "turn_packet": {"response_policy": {"must_answer": True, "planner_seam_trace": {"extra": True}}},
    }
    projected = _apply(payload)
    assert projected["turn_packet"]["response_policy"] == {"planner_seam_trace": {"extra": True}}


def test_empty_root_policy_preserves_nested_policy() -> None:
    nested = {"must_answer": True, "uncertainty": {"open": True}}
    payload = {"response_policy": {}, "turn_packet": {"response_policy": dict(nested)}}
    projected = _apply(payload)
    assert projected["turn_packet"]["response_policy"] == nested
    assert projected is payload


def test_empty_nested_policy_is_preserved() -> None:
    payload = {"response_policy": {"must_answer": True}, "turn_packet": {"response_policy": {}, "version": 2}}
    projected = _apply(payload)
    assert projected is payload
    assert projected["turn_packet"]["response_policy"] == {}
    assert projected["turn_packet"]["version"] == 2


def test_missing_root_policy_is_unchanged() -> None:
    payload = {"turn_packet": {"response_policy": {"must_answer": True}}}
    assert omit_duplicate_turn_packet_policy(payload) is payload
    assert payload["turn_packet"]["response_policy"] == {"must_answer": True}


def test_missing_nested_policy_is_unchanged() -> None:
    payload = {"response_policy": {"must_answer": True}, "turn_packet": {"version": 1}}
    assert omit_duplicate_turn_packet_policy(payload) is payload


def test_nested_object_differing_by_one_child_stays_intact() -> None:
    payload = {
        "response_policy": {"authority": {"mode": "strict", "exceptions": []}, "must_answer": True},
        "turn_packet": {
            "response_policy": {
                "authority": {"mode": "strict", "exceptions": ["scene_override"]},
                "must_answer": True,
            }
        },
    }
    projected = _apply(payload)
    authority = projected["turn_packet"]["response_policy"]["authority"]
    assert authority == {"mode": "strict", "exceptions": ["scene_override"]}
    assert list(projected["turn_packet"]["response_policy"]) == ["authority"]


def test_identical_lists_and_dicts_are_removed() -> None:
    payload = {
        "response_policy": {
            "rule_priority_order": ["scene", "policy"],
            "uncertainty": {"open": False, "notes": ["none"]},
            "answer_completeness": {"must": False},
        },
        "turn_packet": {
            "response_policy": {
                "rule_priority_order": ["scene", "policy"],
                "uncertainty": {"notes": ["none"], "open": False},
                "answer_completeness": {"must": True},
            }
        },
    }
    projected = _apply(payload)
    assert projected["turn_packet"]["response_policy"] == {"answer_completeness": {"must": True}}


def test_boolean_and_numeric_values_are_not_collapsed() -> None:
    assert _json_value_equal(True, 1) is False
    assert _json_value_equal(False, 0) is False
    assert _json_value_equal(True, True) is True
    payload = {
        "response_policy": {"flag": 1, "count": 0, "same": True},
        "turn_packet": {"response_policy": {"flag": True, "count": False, "same": True}},
    }
    projected = _apply(payload)
    nested = projected["turn_packet"]["response_policy"]
    assert nested["flag"] is True
    assert nested["count"] is False
    assert "same" not in nested


def test_null_and_missing_key_stay_distinct() -> None:
    payload = {
        "response_policy": {"present": None, "kept": "yes"},
        "turn_packet": {
            "response_policy": {"present": None, "only_nested": None, "kept": "yes"},
        },
    }
    projected = _apply(payload)
    nested = projected["turn_packet"]["response_policy"]
    assert list(nested) == ["only_nested"]
    assert nested["only_nested"] is None
    assert "only_nested" not in projected["response_policy"]
    assert projected["response_policy"]["present"] is None


def test_unrelated_turn_packet_fields_stay() -> None:
    hint = {"speaker": "gate"}
    payload = {
        "response_policy": {"must_answer": True, "tone": "firm"},
        "turn_packet": {
            "version": 9,
            "narration_hint": hint,
            "response_policy": {"must_answer": True, "tone": "soft"},
            "contracts": {"must_answer": True, "route_only": {"id": "keep"}},
        },
    }
    projected = _apply(payload)
    packet = projected["turn_packet"]
    assert packet["version"] == 9
    assert packet["narration_hint"] is hint
    assert packet["response_policy"] == {"tone": "soft"}
    assert packet["contracts"] == {"route_only": {"id": "keep"}}


def test_input_objects_are_not_mutated() -> None:
    policy = {"must_answer": True, "authority": {"mode": "strict", "exceptions": []}}
    nested = {
        "must_answer": True,
        "authority": {"mode": "strict", "exceptions": ["scene_override"]},
    }
    packet = {"version": 1, "response_policy": nested}
    payload = {"response_policy": policy, "turn_packet": packet}
    snapshot = copy.deepcopy(payload)
    projected = omit_duplicate_turn_packet_policy(payload)
    assert payload == snapshot
    assert payload["turn_packet"] is packet
    assert payload["response_policy"] is policy
    assert payload["turn_packet"]["response_policy"] is nested
    assert projected["turn_packet"] is not packet
    assert projected["response_policy"] is policy
    assert projected["turn_packet"]["response_policy"] is not nested


def test_repeated_invocation_is_idempotent() -> None:
    payload = {
        "response_policy": {"must_answer": True, "tone": "firm", "flag": 1},
        "turn_packet": {"response_policy": {"must_answer": True, "tone": "soft", "flag": True, "extra": None}},
    }
    once = _apply(payload)
    twice = omit_duplicate_turn_packet_policy(once)
    thrice = omit_duplicate_turn_packet_policy(twice)
    assert twice is once or _serialized(twice) == _serialized(once)
    assert _serialized(thrice) == _serialized(once)
    assert list(once["turn_packet"]["response_policy"]) == ["tone", "flag", "extra"]


def test_malformed_policy_structures_are_preserved() -> None:
    not_a_dict = ["not-a-dict"]
    assert omit_duplicate_turn_packet_policy(not_a_dict) is not_a_dict

    listed = {"response_policy": {"a": 1}, "turn_packet": {"response_policy": ["not", "a", "map"], "version": 3}}
    assert omit_duplicate_turn_packet_policy(listed) is listed
    assert listed["turn_packet"]["response_policy"] == ["not", "a", "map"]

    root_listed = {"response_policy": ["nope"], "turn_packet": {"response_policy": {"a": 1}}}
    assert omit_duplicate_turn_packet_policy(root_listed) is root_listed

    packet_text = {"response_policy": {"a": 1}, "turn_packet": "packet"}
    assert omit_duplicate_turn_packet_policy(packet_text) is packet_text

    class Box:
        pass

    box = Box()
    odd = {"response_policy": {"a": box}, "turn_packet": {"response_policy": {"a": box}}}
    assert omit_duplicate_turn_packet_policy(odd) is odd
    assert odd["turn_packet"]["response_policy"]["a"] is box


def test_f3_primary_narration_assembly_drops_only_equal_nested_keys() -> None:
    script = ROOT / "artifacts" / "at_opt_04" / "measure_primary_narration.py"
    destination = ROOT / "artifacts" / "at_opt_04" / "optimized_measurement.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--out",
            str(destination),
            "--assert-optimized",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    report = json.loads(destination.read_text(encoding="utf-8"))
    assert report["provider_client_constructions"] == 0
    assert report["call_gpt_entries"] == 0
    assert report["disk_unchanged"] is True
    assert report["problems"] == []
    assert report["equal_keys_still_in_final_nested"] == []
    assert report["preserved_nested_keys"] == [
        "response_delta",
        "answer_completeness",
        "planner_seam_trace",
    ]
    assert report["final_nested_keys"] == report["preserved_nested_keys"]
    assert report["root_missing_equal_keys"] == []
    assert len(report["equal_nested_keys"]) == 12
    assert report["blob_bytes"] < 83040
    assert report["must_advance_scene"] is True
    assert report["instruction_count"] == 78
