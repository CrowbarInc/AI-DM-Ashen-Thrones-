"""Objective #14 regression suite: runtime persistence + session integrity.

This file is the *single* high-signal place to understand and protect the
post-Objective-14 runtime persistence guarantees.

Coverage buckets (explicit):
- envelope/version acceptance and rejection
- integrity mismatch behavior
- atomic runtime write safety
- validate-first restore behavior
- rollback-on-commit-failure behavior (all-or-nothing)
- concurrency guard behavior (no overlapping operations within process)
- post-restore coherency enforcement (restore success implies coherent runtime)
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import pytest

import game.storage as st
from game.defaults import default_scene
from game.persistence_contract import (
    PERSISTENCE_FORMAT_VERSION,
    PersistenceAcceptance,
    PersistenceContractError,
    PersistenceFailureCategory,
    unwrap_and_validate,
    wrap_runtime_payload,
)
from game.campaign_reset import apply_new_campaign_hard_reset


pytestmark = pytest.mark.integration


def _setup_isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(st, "BASE_DIR", tmp_path)
    monkeypatch.setattr(st, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    monkeypatch.setattr(st, "SNAPSHOTS_DIR", st.DATA_DIR / "snapshots")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for sid in ("frontier_gate", "market_quarter"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def _read_runtime_payload_from_disk(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    payload, _ = unwrap_and_validate(raw, expected_kind=path.stem, allow_legacy_missing_envelope=True)
    return payload


# -----------------------------------------------------------------------------
# envelope/version acceptance and rejection
# -----------------------------------------------------------------------------


def test_obj14_envelope_round_trip_with_integrity() -> None:
    payload = {"a": 1, "b": {"c": 2}}
    env = wrap_runtime_payload(
        kind="session",
        payload=payload,
        saved_at="2026-01-01T00:00:00Z",
        include_integrity=True,
    )
    assert env["persistence_version"] == PERSISTENCE_FORMAT_VERSION
    assert env["kind"] == "session"
    assert env["saved_at"] == "2026-01-01T00:00:00Z"
    assert env["payload"] == payload
    assert "integrity" in env

    out, decision = unwrap_and_validate(env, expected_kind="session")
    assert out == payload
    assert decision.acceptance == PersistenceAcceptance.ACCEPTED_AS_IS


def test_obj14_accepts_legacy_missing_envelope_when_allowed() -> None:
    legacy = {"x": 1}
    out, decision = unwrap_and_validate(legacy, expected_kind="combat", allow_legacy_missing_envelope=True)
    assert out == legacy
    assert decision.acceptance == PersistenceAcceptance.NORMALIZED_FORWARD
    assert decision.category == PersistenceFailureCategory.MISSING_ENVELOPE


def test_obj14_rejects_missing_envelope_when_not_allowed() -> None:
    with pytest.raises(PersistenceContractError) as e:
        unwrap_and_validate({"x": 1}, expected_kind="session", allow_legacy_missing_envelope=False)
    assert e.value.category == PersistenceFailureCategory.MISSING_ENVELOPE


def test_obj14_rejects_wrong_document_kind() -> None:
    env = wrap_runtime_payload(kind="combat", payload={"x": 1}, saved_at="t", include_integrity=False)
    with pytest.raises(PersistenceContractError) as e:
        unwrap_and_validate(env, expected_kind="session")
    assert e.value.category == PersistenceFailureCategory.WRONG_DOCUMENT_KIND


def test_obj14_rejects_unsupported_version() -> None:
    env = wrap_runtime_payload(kind="session", payload={"x": 1}, saved_at="t", include_integrity=False)
    env["persistence_version"] = 999
    with pytest.raises(PersistenceContractError) as e:
        unwrap_and_validate(env, expected_kind="session")
    assert e.value.category == PersistenceFailureCategory.UNSUPPORTED_VERSION


# -----------------------------------------------------------------------------
# integrity mismatch behavior
# -----------------------------------------------------------------------------


def test_obj14_rejects_integrity_mismatch() -> None:
    env = wrap_runtime_payload(kind="session", payload={"x": 1}, saved_at="t", include_integrity=True)
    env["payload"]["x"] = 2  # mutate payload without updating integrity
    with pytest.raises(PersistenceContractError) as e:
        unwrap_and_validate(env, expected_kind="session")
    assert e.value.category == PersistenceFailureCategory.INTEGRITY_MISMATCH


# -----------------------------------------------------------------------------
# atomic runtime write safety
# -----------------------------------------------------------------------------


def test_obj14_atomic_save_session_writes_valid_envelope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    session = st.load_session()
    session["turn_counter"] = 7
    st.save_session(session)

    raw = json.loads(st.SESSION_PATH.read_text(encoding="utf-8"))
    payload, _ = unwrap_and_validate(raw, expected_kind="session", allow_legacy_missing_envelope=False)
    assert payload["turn_counter"] == 7
    assert payload.get("last_saved_at")


def test_obj14_atomic_save_failure_does_not_corrupt_live_session_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    session = st.load_session()
    session["turn_counter"] = 1
    st.save_session(session)
    before = st.SESSION_PATH.read_bytes()

    def boom(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(st.os, "replace", boom)
    session2 = dict(session)
    session2["turn_counter"] = 2
    with pytest.raises(OSError):
        st.save_session(session2)

    after = st.SESSION_PATH.read_bytes()
    assert after == before
    leftovers = list(st.SESSION_PATH.parent.glob(st.SESSION_PATH.name + ".tmp.*"))
    assert leftovers == []


# -----------------------------------------------------------------------------
# validate-first restore behavior
# -----------------------------------------------------------------------------


def test_obj14_snapshot_restore_validates_before_any_live_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    st.save_session(st.load_session())
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()

    before = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }

    st.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    bad = {"version": st.SNAPSHOT_VERSION, "created_at": "t", "label": "bad", "session": {}}
    (st.SNAPSHOTS_DIR / "bad.json").write_text(json.dumps(bad, indent=2), encoding="utf-8")

    assert st.load_snapshot("bad") is None

    after = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }
    assert after == before


# -----------------------------------------------------------------------------
# rollback-on-commit-failure behavior (all-or-nothing)
# -----------------------------------------------------------------------------


def test_obj14_snapshot_restore_is_all_or_nothing_with_rollback_on_commit_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    session = st.load_session()
    session["active_scene_id"] = "frontier_gate"
    st.save_session(session)
    combat = st.load_combat()
    combat["active"] = False
    st.save_combat(combat)
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    meta = st.create_snapshot(label="baseline")

    session2 = st.load_session()
    session2["active_scene_id"] = "market_quarter"
    st.save_session(session2)

    before = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }

    calls = {"n": 0}
    real_replace = st.os.replace

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("simulated mid-commit failure")
        return real_replace(src, dst)

    monkeypatch.setattr(st.os, "replace", flaky_replace)

    with pytest.raises(RuntimeError):
        st.load_snapshot(meta["id"])

    after = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }
    assert after == before


# -----------------------------------------------------------------------------
# concurrency guard behavior
# -----------------------------------------------------------------------------


def test_obj14_overlapping_persistence_operations_are_serialized_deterministically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)

    entered = threading.Event()
    release = threading.Event()
    second_acquired = threading.Event()

    def hook(op: str, phase: str) -> None:
        if op == "save_session" and phase == "acquired":
            if not entered.is_set():
                entered.set()
                release.wait(timeout=5)
            else:
                second_acquired.set()

    monkeypatch.setattr(st, "_RUNTIME_PERSISTENCE_TEST_HOOK", hook)

    exc: list[BaseException] = []

    def t1() -> None:
        try:
            s = st.load_session()
            s["turn_counter"] = 1
            st.save_session(s)
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    thread1 = threading.Thread(target=t1)
    thread1.start()
    assert entered.wait(timeout=5)

    def t2() -> None:
        try:
            s2 = st.load_session()
            s2["turn_counter"] = 2
            st.save_session(s2)
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    thread2 = threading.Thread(target=t2)
    thread2.start()

    assert not second_acquired.is_set()

    release.set()
    thread1.join(timeout=5)
    thread2.join(timeout=5)
    assert not exc
    assert second_acquired.is_set()
    assert st.load_session().get("turn_counter") == 2


def test_obj14_snapshot_restore_cannot_race_a_save_into_mixed_visible_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    s = st.load_session()
    s["active_scene_id"] = "frontier_gate"
    st.save_session(s)
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    meta = st.create_snapshot(label="baseline")

    entered = threading.Event()
    release = threading.Event()
    restore_completed = threading.Event()

    def hook(op: str, phase: str) -> None:
        if op == "save_session" and phase == "acquired":
            entered.set()
            release.wait(timeout=5)

    monkeypatch.setattr(st, "_RUNTIME_PERSISTENCE_TEST_HOOK", hook)

    exc: list[BaseException] = []

    def hold_save_session() -> None:
        try:
            s2 = st.load_session()
            s2["active_scene_id"] = "market_quarter"
            st.save_session(s2)
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    t = threading.Thread(target=hold_save_session)
    t.start()
    assert entered.wait(timeout=5)

    exc2: list[BaseException] = []

    def run_restore() -> None:
        try:
            st.load_snapshot(meta["id"])
            restore_completed.set()
        except BaseException as e:  # pragma: no cover
            exc2.append(e)

    r = threading.Thread(target=run_restore)
    r.start()
    assert not restore_completed.is_set()

    release.set()
    t.join(timeout=5)
    r.join(timeout=5)
    assert not exc
    assert not exc2
    assert restore_completed.is_set()
    assert st.load_session().get("active_scene_id") in ("market_quarter", "frontier_gate")
    assert isinstance(st.load_combat(), dict)
    assert isinstance(st.load_world(), dict)
    assert isinstance(st.load_character(), dict)


def test_obj14_append_log_is_serialized_against_snapshot_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    st.save_session(st.load_session())
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    meta = st.create_snapshot(label="baseline")

    restore_entered = threading.Event()
    allow_restore_to_finish = threading.Event()
    append_acquired = threading.Event()

    def hook(op: str, phase: str) -> None:
        if op == "snapshot_restore" and phase == "acquired":
            restore_entered.set()
            allow_restore_to_finish.wait(timeout=5)
        if op == "append_log" and phase == "acquired":
            append_acquired.set()

    monkeypatch.setattr(st, "_RUNTIME_PERSISTENCE_TEST_HOOK", hook)

    exc: list[BaseException] = []

    def run_restore() -> None:
        try:
            st.load_snapshot(meta["id"])
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    r = threading.Thread(target=run_restore)
    r.start()
    assert restore_entered.wait(timeout=5)

    def run_append() -> None:
        try:
            st.append_log({"kind": "chat", "text": "hi"})
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    a = threading.Thread(target=run_append)
    a.start()
    # append_log must not acquire while restore holds the guard
    assert not append_acquired.is_set()

    allow_restore_to_finish.set()
    r.join(timeout=5)
    a.join(timeout=5)
    assert not exc
    assert append_acquired.is_set()


def test_obj14_new_campaign_reset_cannot_overlap_restore_or_save_silently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    st.save_session(st.load_session())
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    meta = st.create_snapshot(label="baseline")

    entered = threading.Event()
    release = threading.Event()
    restore_completed = threading.Event()

    def hook(op: str, phase: str) -> None:
        if op == "new_campaign_hard_reset" and phase == "acquired":
            entered.set()
            release.wait(timeout=5)

    monkeypatch.setattr(st, "_RUNTIME_PERSISTENCE_TEST_HOOK", hook)

    exc: list[BaseException] = []

    def run_reset() -> None:
        try:
            apply_new_campaign_hard_reset()
        except BaseException as e:  # pragma: no cover
            exc.append(e)

    t = threading.Thread(target=run_reset)
    t.start()
    assert entered.wait(timeout=5)

    exc2: list[BaseException] = []

    def run_restore() -> None:
        try:
            st.load_snapshot(meta["id"])
            restore_completed.set()
        except BaseException as e:  # pragma: no cover
            exc2.append(e)

    r = threading.Thread(target=run_restore)
    r.start()
    assert not restore_completed.is_set()

    release.set()
    t.join(timeout=5)
    r.join(timeout=5)
    assert not exc
    assert not exc2
    assert restore_completed.is_set()


# -----------------------------------------------------------------------------
# post-restore coherency enforcement (restore success implies coherent runtime)
# -----------------------------------------------------------------------------


def test_obj14_restore_rejected_when_post_restore_runtime_is_structurally_incoherent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    s = st.load_session()
    s["active_scene_id"] = "frontier_gate"
    st.save_session(s)
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    ok_snapshot = st.create_snapshot(label="ok")

    before = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }

    st.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    bad_bundle = json.loads((st.SNAPSHOTS_DIR / f"{ok_snapshot['id']}.json").read_text(encoding="utf-8"))
    bad_bundle["session"]["active_scene_id"] = "not_a_scene"
    (st.SNAPSHOTS_DIR / "bad_coherency.json").write_text(
        json.dumps(bad_bundle, indent=2), encoding="utf-8"
    )

    with pytest.raises(RuntimeError):
        st.load_snapshot("bad_coherency")

    after = {
        "session": st.SESSION_PATH.read_bytes(),
        "combat": st.COMBAT_PATH.read_bytes(),
        "world": st.WORLD_PATH.read_bytes(),
        "character": st.CHARACTER_PATH.read_bytes(),
        "log": st.SESSION_LOG_PATH.read_bytes(),
    }
    assert after == before


def test_obj14_successful_restore_yields_coherent_loadable_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_isolated_storage(tmp_path, monkeypatch)
    s = st.load_session()
    s["active_scene_id"] = "market_quarter"
    st.save_session(s)
    st.save_combat(st.load_combat())
    st.save_world(st.load_world())
    st.save_character(st.load_character())
    st.clear_log()
    meta = st.create_snapshot(label="checkpoint")

    s2 = st.load_session()
    s2["active_scene_id"] = "frontier_gate"
    st.save_session(s2)

    out = st.load_snapshot(meta["id"])
    assert out is not None

    s3 = st.load_session()
    assert s3["active_scene_id"] == "market_quarter"
    assert st.is_known_scene_id(s3["active_scene_id"])
    assert isinstance(st.load_combat(), dict)
    assert isinstance(st.load_world(), dict)
    assert isinstance(st.load_character(), dict)

