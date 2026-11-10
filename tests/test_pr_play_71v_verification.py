"""PR-PLAY-71V persistence, rollback, idempotency, disclosure, and projection checks.

Replacement faults are injected at os.replace. A separate test holds a real
Windows exclusive file handle. Gameplay and provider calls are counted outside
the rename loop so a retry cannot hide a repeated turn.
"""
import copy
import errno
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game import authored_consequences as consequences
from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE, PRINT_CLUE
from tests.test_pr_play_71_lifecycle import act, byid, chat, choose, configure, create, flags, reach, start

SENTINELS = (
    "CANARY_GM_NOTE",
    "CANARY_HIDDEN_BRANCH",
    "CANARY_UNDISCOVERED",
    "CANARY_NPC_MOTIVE",
    "CANARY_FUTURE",
    "CANARY_RESOLVER",
    "CANARY_PROVIDER_PROMPT",
    "CANARY_VALIDATION",
    "CANARY_RAW_STATE",
)


def denied(code=5, message="injected temporary Windows file lock"):
    exc = PermissionError(errno.EACCES, message)
    if code is not None:
        exc.winerror = code
    return exc


def patch_replace(monkeypatch, failures, code=5, error=None):
    original = os.replace
    calls = []
    delays = []
    real_sleep = time.sleep

    def sleep(seconds):
        delays.append(seconds)
        return real_sleep(seconds)

    def replace(src, dst):
        calls.append((str(src), str(dst)))
        if len(calls) <= failures:
            raise error if error is not None else denied(code)
        return original(src, dst)

    monkeypatch.setattr(storage.os, "replace", replace)
    monkeypatch.setattr(storage.time, "sleep", sleep)

    def restore():
        monkeypatch.setattr(storage.os, "replace", original)
        monkeypatch.setattr(storage.time, "sleep", real_sleep)

    return calls, delays, restore


def runtime_bytes():
    paths = [
        storage.SESSION_PATH,
        storage.WORLD_PATH,
        storage.COMBAT_PATH,
        storage.CHARACTER_PATH,
        storage.SESSION_LOG_PATH,
    ]
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def plant_sentinels():
    world = storage.load_world()
    world["gm_notes"] = "CANARY_GM_NOTE"
    world["hidden_branch_conditions"] = "CANARY_HIDDEN_BRANCH"
    world["undiscovered_clue"] = "CANARY_UNDISCOVERED"
    world["npc_private_motivation"] = "CANARY_NPC_MOTIVE"
    world["secret_future_outcome"] = "CANARY_FUTURE"
    world["resolver_metadata"] = "CANARY_RESOLVER"
    world["provider_prompt"] = "CANARY_PROVIDER_PROMPT"
    world["validation_trace"] = "CANARY_VALIDATION"
    world["raw_authoritative_state"] = "CANARY_RAW_STATE"
    storage.save_world(world)


def assert_no_sentinels(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    for sentinel in SENTINELS:
        assert sentinel not in text


def prepared(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    plant_sentinels()
    return TestClient(api.app, raise_server_exceptions=False)


@pytest.mark.parametrize("failures", [0, 1, 2, 3])
def test_atomic_replace_succeeds_within_budget(tmp_path, monkeypatch, failures):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior")
    calls, delays, _restore = patch_replace(monkeypatch, failures)
    started = time.perf_counter()
    storage._atomic_write_bytes(target, b"next")
    elapsed = time.perf_counter() - started
    assert target.read_bytes() == b"next"
    assert len(calls) == failures + 1
    assert len({src for src, _dst in calls}) == 1
    assert delays == [0.01, 0.03, 0.09][:failures]
    assert elapsed < 1.0
    assert not list(tmp_path.glob("*.tmp.*"))


def test_atomic_replace_exhaustion_preserves_target(tmp_path, monkeypatch):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior-valid")
    calls, delays, _restore = patch_replace(monkeypatch, 9)
    started = time.perf_counter()
    with pytest.raises(PermissionError) as caught:
        storage._atomic_write_bytes(target, b"next")
    elapsed = time.perf_counter() - started
    assert caught.value.winerror == 5
    assert target.read_bytes() == b"prior-valid"
    assert len(calls) == 4
    assert delays == [0.01, 0.03, 0.09]
    assert 0.12 <= elapsed < 1.0
    assert not list(tmp_path.glob("*.tmp.*"))


@pytest.mark.parametrize("code", [32, 13, None])
def test_unrelated_permission_error_is_not_retried(tmp_path, monkeypatch, code):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior")
    calls, delays, _restore = patch_replace(monkeypatch, 9, code=code)
    with pytest.raises(PermissionError):
        storage._atomic_write_bytes(target, b"next")
    assert len(calls) == 1 and delays == []
    assert target.read_bytes() == b"prior"
    assert not list(tmp_path.glob("*.tmp.*"))


def test_other_os_error_is_not_retried(tmp_path, monkeypatch):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior")
    calls, _delays, _restore = patch_replace(monkeypatch, 9, error=OSError(errno.EIO, "disk unavailable"))
    with pytest.raises(OSError) as caught:
        storage._atomic_write_bytes(target, b"next")
    assert caught.value.errno == errno.EIO
    assert not isinstance(caught.value, PermissionError)
    assert len(calls) == 1
    assert target.read_bytes() == b"prior"
    assert not list(tmp_path.glob("*.tmp.*"))


def test_missing_temp_source_propagates(tmp_path, monkeypatch):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior")
    original = os.replace

    def replace(src, dst):
        Path(src).unlink(missing_ok=True)
        return original(src, dst)

    monkeypatch.setattr(storage.os, "replace", replace)
    with pytest.raises(FileNotFoundError):
        storage._atomic_write_bytes(target, b"next")
    assert target.read_bytes() == b"prior"
    assert not list(tmp_path.glob("*.tmp.*"))


def test_unavailable_destination_propagates(tmp_path):
    blocker = tmp_path / "blocked"
    blocker.write_text("kept", encoding="utf-8")
    with pytest.raises(OSError):
        storage._atomic_write_bytes(blocker / "session.json", b"next")
    assert blocker.read_text(encoding="utf-8") == "kept"
    assert not list(tmp_path.glob("*.tmp.*"))


def test_rename_retry_does_not_repeat_outer_operation(tmp_path, monkeypatch):
    target = tmp_path / "session.json"
    target.write_bytes(b"prior")
    calls, _delays, _restore = patch_replace(monkeypatch, 3)
    resolutions = {"count": 0}

    def resolve_once():
        resolutions["count"] += 1
        storage._atomic_write_bytes(target, b"next")

    resolve_once()
    assert resolutions["count"] == 1
    assert len(calls) == 4
    assert target.read_bytes() == b"next"


@pytest.mark.skipif(os.name != "nt", reason="real Windows exclusive-handle reproduction")
def test_real_windows_exclusive_lock_then_recovery(tmp_path):
    import ctypes
    from ctypes import wintypes

    target = tmp_path / "locked.json"
    target.write_bytes(b"prior-real")
    generic_read = 0x80000000
    open_existing = 3
    normal = 0x80
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    handle = create(str(target), generic_read, 0, None, open_existing, normal, None)
    invalid = wintypes.HANDLE(-1).value
    close = ctypes.windll.kernel32.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    if handle == invalid or handle is None:
        pytest.skip("exclusive handle was not obtained")
    try:
        started = time.perf_counter()
        with pytest.raises(PermissionError) as caught:
            storage._atomic_write_bytes(target, b"blocked")
        elapsed = time.perf_counter() - started
        assert getattr(caught.value, "winerror", None) == 5
        assert 0.12 <= elapsed < 2.0
    finally:
        assert close(handle)
    assert target.read_bytes() == b"prior-real"
    assert not list(tmp_path.glob("*.tmp.*"))
    storage._atomic_write_bytes(target, b"recovered")
    assert target.read_bytes() == b"recovered"


def test_new_campaign_rollback_on_each_runtime_file(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        identity = create(client)
        start(client)
        chat(client, "I examine the notice board.")
        before = runtime_bytes()
        before_id = storage.load_session()["campaign_run_id"]
        other_note = tmp_path / "unrelated-campaign.txt"
        other_note.write_text("keep", encoding="utf-8")
        original = storage._atomic_write_bytes
        atomic_targets = [
            storage.SESSION_PATH,
            storage.COMBAT_PATH,
            storage.SESSION_LOG_PATH,
        ]
        for target in atomic_targets:
            def fail(path, data, blocked=target):
                if Path(path) == blocked:
                    raise denied()
                return original(path, data)

            monkeypatch.setattr(storage, "_atomic_write_bytes", fail)
            response = client.post("/api/new_campaign")
            assert response.status_code >= 400
            assert response.json().get("ok") is not True
            assert "injected temporary" not in response.text
            assert_no_sentinels(response.text)
            assert runtime_bytes() == before
            assert storage.load_session()["campaign_run_id"] == before_id
            assert other_note.read_text(encoding="utf-8") == "keep"
        real_world = storage.save_world

        def fail_world(data):
            real_world(data)
            raise denied()

        monkeypatch.setattr("game.campaign_reset.save_world", fail_world)
        response = client.post("/api/new_campaign")
        assert response.status_code >= 400
        assert response.json().get("ok") is not True
        assert "injected temporary" not in response.text
        assert_no_sentinels(response.text)
        assert runtime_bytes() == before
        assert storage.load_session()["campaign_run_id"] == before_id
        assert other_note.read_text(encoding="utf-8") == "keep"
        monkeypatch.setattr(storage, "_atomic_write_bytes", original)
        monkeypatch.setattr("game.campaign_reset.save_world", real_world)
        recovered = create(client)
        assert recovered != identity
        started = start(client)
        assert started["session"]["campaign_started"] is True
        assert started["session"]["active_scene_id"] == "frontier_gate"


def test_new_campaign_identifier_failure_changes_nothing(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        create(client)
        start(client)
        before = runtime_bytes()
        identity = storage.load_session()["campaign_run_id"]

        def boom(session):
            raise RuntimeError("CANARY_IDENTIFIER_PRIVATE")

        monkeypatch.setattr("game.campaign_reset.reset_session_state", boom)
        response = client.post("/api/new_campaign")
        assert response.status_code >= 400
        assert "CANARY_" not in response.text
        assert runtime_bytes() == before
        assert storage.load_session()["campaign_run_id"] == identity
        monkeypatch.undo()
        assert create(client) != identity


def test_opening_persistence_failure_does_not_publish_start(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        create(client)
        before = runtime_bytes()
        original = storage._atomic_write_bytes

        def fail_session(path, data):
            if Path(path) == storage.SESSION_PATH:
                raise denied()
            return original(path, data)

        monkeypatch.setattr(storage, "_atomic_write_bytes", fail_session)
        response = client.post("/api/start_campaign")
        assert response.status_code >= 400
        body = response.json()
        assert body.get("ok") is not True
        assert body.get("campaign_started") is not True
        assert "injected temporary" not in response.text
        assert_no_sentinels(response.text)
        assert storage.load_session().get("campaign_started") is not True
        assert runtime_bytes()[storage.SESSION_PATH] == before[storage.SESSION_PATH]
        assert runtime_bytes()[storage.SESSION_LOG_PATH] == before[storage.SESSION_LOG_PATH]
        monkeypatch.setattr(storage, "_atomic_write_bytes", original)
        started = start(client)
        assert started["session"]["campaign_started"] is True


@pytest.mark.parametrize("failures", [1, 3])
def test_chat_transient_rename_commits_one_turn(tmp_path, monkeypatch, failures):
    client = prepared(tmp_path, monkeypatch)
    calls = {"gpt": 0, "resolve": 0}
    original_gpt = api.call_gpt
    original_resolve = consequences.resolve

    def gpt(*args, **kwargs):
        calls["gpt"] += 1
        return original_gpt(*args, **kwargs)

    def resolve(*args, **kwargs):
        calls["resolve"] += 1
        return original_resolve(*args, **kwargs)

    monkeypatch.setattr(api, "call_gpt", gpt)
    monkeypatch.setattr(consequences, "resolve", resolve)
    with client:
        create(client)
        start(client)
        reach(client)
        before_turn = storage.load_session()["turn_counter"]
        before_log = len(storage.load_log())
        before_flags = copy.deepcopy(flags())
        before_resolve = calls["resolve"]
        before_gpt = calls["gpt"]
        _calls, _delays, _restore = patch_replace(monkeypatch, failures)
        response = act(client, "patrol_survey")
        assert response["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
        assert flags()["patrol_survey"] is True
        assert not flags().get("patrol_report")
        assert storage.load_session()["turn_counter"] == before_turn
        assert len(storage.load_log()) == before_log + 1
        assert calls["resolve"] == before_resolve + 1
        assert calls["gpt"] == before_gpt
        assert before_flags != flags()
        texts = [entry["gm_output"]["player_facing_text"] for entry in storage.load_log()]
        assert texts.count(byid("patrol_survey")["consequence"]["text"]) == 1


def test_chat_permanent_rename_does_not_publish_success(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    calls = {"resolve": 0}
    original_resolve = consequences.resolve

    def resolve(*args, **kwargs):
        calls["resolve"] += 1
        return original_resolve(*args, **kwargs)

    monkeypatch.setattr(consequences, "resolve", resolve)
    with client:
        create(client)
        start(client)
        reach(client)
        before = runtime_bytes()
        before_flags = copy.deepcopy(flags())
        before_turn = storage.load_session()["turn_counter"]
        before_log = storage.load_log()
        before_resolve = calls["resolve"]
        _calls, _delays, restore = patch_replace(monkeypatch, 9)
        response = client.post("/api/action", json={
            "action_type": "exploration",
            "intent": byid("patrol_survey")["label"],
            "exploration_action": {"id": "patrol_survey", "type": "custom", "label": byid("patrol_survey")["label"]},
        })
        assert response.status_code >= 400
        assert response.json().get("ok") is not True
        assert "injected temporary" not in response.text
        assert_no_sentinels(response.text)
        assert storage.load_session()["turn_counter"] == before_turn
        assert storage.load_log() == before_log
        assert flags() == before_flags
        assert runtime_bytes()[storage.SESSION_PATH] == before[storage.SESSION_PATH]
        assert runtime_bytes()[storage.SESSION_LOG_PATH] == before[storage.SESSION_LOG_PATH]
        assert not flags().get("patrol_survey")
        assert calls["resolve"] == before_resolve + 1
        restore()
        recovered = act(client, "patrol_survey")
        assert recovered["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
        assert flags()["patrol_survey"] is True
        assert flags().get("patrol_report") is not True
        assert len(storage.load_log()) == len(before_log) + 1


def test_transcript_and_authoritative_isolation(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        survey_id = create(client)
        start(client)
        reach(client)
        choose(client, "survey")
        survey_snap = client.post("/api/snapshots", json={"label": "survey"}).json()["snapshot"]["id"]
        survey_flags = copy.deepcopy(flags())
        survey_log = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        report_id = create(client)
        assert report_id != survey_id
        start(client)
        reach(client)
        choose(client, "report")
        report_snap = client.post("/api/snapshots", json={"label": "report"}).json()["snapshot"]["id"]
        report_flags = copy.deepcopy(flags())
        report_log = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        survey_only = byid("patrol_record_survey")["consequence"]["text"]
        report_only = byid("patrol_warn_watch")["consequence"]["text"]
        assert survey_only in survey_log and report_only not in survey_log
        assert report_only in report_log and survey_only not in report_log

        loaded = client.post("/api/snapshots/load", json={"snapshot_id": survey_snap})
        assert loaded.status_code == 200 and loaded.json()["ok"] is True
        restored = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert restored == survey_log
        assert report_only not in json.dumps(restored)
        assert storage.load_session()["campaign_run_id"] == survey_id
        assert flags() == survey_flags

        loaded = client.post("/api/snapshots/load", json={"snapshot_id": report_snap})
        restored = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert restored == report_log
        assert survey_only not in json.dumps(restored)
        assert storage.load_session()["campaign_run_id"] == report_id
        assert flags() == report_flags
        assert not flags().get("patrol_survey")

        loaded = client.post("/api/snapshots/load", json={"snapshot_id": survey_snap})
        continued = chat(client, "I examine the mud prints.")
        assert flags() == survey_flags
        assert storage.load_session()["campaign_run_id"] == survey_id
        survey_after = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert survey_after[:-1] == survey_log
        assert continued["gm_output"]["player_facing_text"] == survey_after[-1]
        reloaded = client.post("/api/snapshots/load", json={"snapshot_id": report_snap})
        assert reloaded.json()["ok"] is True
        report_again = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert report_again == report_log
        assert survey_after[-1] not in report_again or survey_after[-1] in report_log
        assert_no_sentinels(client.get("/api/state").text)
        assert_no_sentinels(client.get("/api/log").text)


def test_player_safe_projection_across_lifecycle(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        created = client.post("/api/new_campaign")
        assert_no_sentinels(created.text)
        assert consequences.ENROLLMENT not in created.text
        started = client.post("/api/start_campaign")
        assert_no_sentinels(started.text)
        for text in (
            "I examine the notice board.",
            "I follow the missing patrol rumor.",
            "I examine the weathered milestone.",
        ):
            response = client.post("/api/chat", json={"text": text})
            assert response.status_code == 200
            assert_no_sentinels(response.text)
        choice = act(client, "patrol_survey")
        follow = act(client, "patrol_record_survey")
        assert NOTICE_CLUE
        assert PRINT_CLUE in client.get("/api/log").text
        assert choice["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
        assert follow["gm_output"]["player_facing_text"] == byid("patrol_record_survey")["consequence"]["text"]
        saved = client.post("/api/snapshots", json={"label": "safe"})
        resumed = client.post("/api/snapshots/load", json={"snapshot_id": saved.json()["snapshot"]["id"]})
        invalid = client.post("/api/action", json={"action_type": "exploration", "intent": "nope", "exploration_action": {"id": "missing", "type": "custom", "label": "nope"}})
        for response in (saved, resumed, invalid, client.get("/api/state")):
            assert_no_sentinels(response.text)
        assert "CANARY_" not in client.get("/api/state").text


def test_mandatory_disclosure_survives_rejected_narration(tmp_path, monkeypatch):
    from game import integrated_investigation_narration as integrated
    from game import quarantined_investigation_narration as quarantine

    client = prepared(tmp_path, monkeypatch)
    hook = integrated.run_integrated_hook
    monkeypatch.setattr(
        integrated,
        "run_integrated_hook",
        lambda handle, **kwargs: hook(handle, generator=quarantine._Replay("The gate is permanently open.", "")),
    )
    with client:
        create(client)
        start(client)
        chat(client, "I examine the notice board.")
        chat(client, "I follow the missing patrol rumor.")
        response = chat(client, "I examine the weathered milestone.")
        assert PRINT_CLUE in response["gm_output"]["player_facing_text"]
        assert "permanently open" not in response["gm_output"]["player_facing_text"]
        assert PRINT_CLUE in client.get("/api/log").text


def test_duplicate_request_does_not_duplicate_branch(tmp_path, monkeypatch):
    client = prepared(tmp_path, monkeypatch)
    with client:
        create(client)
        start(client)
        reach(client)
        choose(client, "survey")
        committed = copy.deepcopy(flags())
        log_len = len(storage.load_log())
        act(client, "patrol_record_survey")
        act(client, "patrol_report")
        assert flags() == committed
        chat(client, "I examine the mud prints.")
        assert flags() == committed
        assert len([entry for entry in storage.load_log() if entry["gm_output"]["player_facing_text"] == byid("patrol_record_survey")["consequence"]["text"]]) == 1
        assert log_len < len(storage.load_log())
