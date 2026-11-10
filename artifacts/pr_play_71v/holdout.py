"""Execute the frozen PR-PLAY-71V holdout once. Do not edit cases to chase a result."""
import errno
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pytest
from tests.test_pr_play_71v_verification import (
    SENTINELS,
    act,
    assert_no_sentinels,
    byid,
    chat,
    choose,
    create,
    denied,
    flags,
    patch_replace,
    prepared,
    reach,
    runtime_bytes,
    start,
)
from game import storage

OUT = Path(__file__).resolve().parent


def _atomic(case, tmp):
    kind = case["kind"]
    target = tmp / "session.json"
    if kind == "unavailable_destination":
        blocker = tmp / "blocked"
        blocker.write_text("kept", encoding="utf-8")
        try:
            storage._atomic_write_bytes(blocker / "session.json", b"next")
        except OSError:
            assert blocker.read_text(encoding="utf-8") == "kept"
            assert not list(tmp.glob("*.tmp.*"))
            return {"propagated": True}
        raise AssertionError("destination failure was swallowed")
    if kind == "create_missing":
        storage._atomic_write_bytes(target, b"created")
        assert target.read_bytes() == b"created"
        assert not list(tmp.glob("*.tmp.*"))
        return {"created": True}
    if kind != "missing_source":
        target.write_bytes(b"prior-valid")
    content = case.get("content", "next").encode()
    if kind == "missing_source":
        target.write_bytes(b"prior-valid")
        original = os.replace

        def replace(src, dst):
            Path(src).unlink(missing_ok=True)
            return original(src, dst)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(storage.os, "replace", replace)
            try:
                storage._atomic_write_bytes(target, b"next")
            except FileNotFoundError:
                assert target.read_bytes() == b"prior-valid"
                assert not list(tmp.glob("*.tmp.*"))
                return {"propagated": "FileNotFoundError"}
        raise AssertionError("missing source was swallowed")
    if kind == "real_windows_lock":
        import ctypes
        from ctypes import wintypes
        create_file = ctypes.windll.kernel32.CreateFileW
        create_file.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create_file.restype = wintypes.HANDLE
        handle = create_file(str(target), 0x80000000, 0, None, 3, 0x80, None)
        close = ctypes.windll.kernel32.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        if handle in (None, wintypes.HANDLE(-1).value):
            raise RuntimeError("exclusive Windows handle was not obtained")
        try:
            started = time.perf_counter()
            try:
                storage._atomic_write_bytes(target, b"blocked")
            except PermissionError as exc:
                elapsed = time.perf_counter() - started
                assert getattr(exc, "winerror", None) == 5
                assert 0.12 <= elapsed < 2.0
            else:
                raise AssertionError("real lock did not deny replacement")
        finally:
            assert close(handle)
        assert target.read_bytes() == b"prior-valid"
        assert not list(tmp.glob("*.tmp.*"))
        storage._atomic_write_bytes(target, b"recovered")
        assert target.read_bytes() == b"recovered"
        return {"real_lock": True, "winerror": 5, "recovered": True}
    with pytest.MonkeyPatch.context() as mp:
        if kind == "oserror":
            calls, _delays, _restore = patch_replace(mp, 9, error=OSError(errno.EIO, "disk unavailable"))
            try:
                storage._atomic_write_bytes(target, content)
            except OSError as exc:
                assert exc.errno == errno.EIO == case["expect_errno"]
                assert not isinstance(exc, PermissionError)
                assert len(calls) == 1 and target.read_bytes() == b"prior-valid"
                assert not list(tmp.glob("*.tmp.*"))
                return {"calls": len(calls)}
            raise AssertionError("os error was swallowed")
        if kind == "permission":
            calls, delays, _restore = patch_replace(mp, 9, code=case["code"])
            try:
                storage._atomic_write_bytes(target, content)
            except PermissionError:
                assert len(calls) == case["expect_calls"] and delays == []
                assert target.read_bytes() == b"prior-valid"
                assert not list(tmp.glob("*.tmp.*"))
                return {"calls": len(calls)}
            raise AssertionError("permission error was swallowed")
        if kind == "exhaust":
            calls, delays, _restore = patch_replace(mp, 9)
            started = time.perf_counter()
            try:
                storage._atomic_write_bytes(target, content)
            except PermissionError as exc:
                elapsed = time.perf_counter() - started
                assert exc.winerror == case["expect_winerror"]
                assert len(calls) == case["expect_calls"] and delays == case["expect_delays"]
                assert 0.12 <= elapsed < 1.0
                assert target.read_bytes() == b"prior-valid"
                assert not list(tmp.glob("*.tmp.*"))
                return {"calls": len(calls), "elapsed_s": round(elapsed, 3)}
            raise AssertionError("retry budget did not exhaust")
        calls, delays, _restore = patch_replace(mp, case["failures"])
        outer = {"count": 0}

        def once():
            outer["count"] += 1
            storage._atomic_write_bytes(target, content)

        once()
        assert target.read_bytes() == content
        assert len(calls) == case["expect_calls"]
        assert delays == case["expect_delays"]
        assert len({src for src, _dst in calls}) == 1
        assert not list(tmp.glob("*.tmp.*"))
        if kind == "single_outer":
            assert outer["count"] == case["expect_outer"]
        return {"calls": len(calls), "outer": outer["count"]}


def _client_case(case):
    kind = case["kind"]
    group = case["group"]
    with pytest.MonkeyPatch.context() as mp:
        client = prepared(OUT / "holdout_data" / case["id"], mp)
        with client:
            if group == "rollback":
                return _rollback(case, client, mp)
            if group == "chat":
                return _chat(case, client, mp)
            if group == "lifecycle":
                return _lifecycle(case, client)
            if group == "transcript":
                return _transcript(case, client)
            if group == "disclosure":
                return _disclosure(case, client, mp)
            if group == "projection":
                return _projection(case, client)
    raise AssertionError(group)


def _rollback(case, client, mp):
    identity = create(client)
    if case["kind"] != "opening":
        start(client)
        chat(client, "I examine the notice board.")
    before = runtime_bytes()
    before_id = storage.load_session()["campaign_run_id"]
    other = OUT / "holdout_data" / case["id"] / "unrelated.txt"
    other.write_text("keep", encoding="utf-8")
    kind = case["kind"]
    if kind == "normal_create":
        assert create(client) != identity
        return {"recovered": True}
    if kind == "identifier":
        def boom(_session):
            raise RuntimeError("CANARY_IDENTIFIER_PRIVATE")
        mp.setattr("game.campaign_reset.reset_session_state", boom)
    elif kind == "world_write" or kind == "recover_after_world":
        real = storage.save_world
        def fail_world(data, original=real):
            original(data)
            raise denied()
        mp.setattr("game.campaign_reset.save_world", fail_world)
    elif kind == "opening":
        original = storage._atomic_write_bytes
        def fail_session(path, data, original=original):
            if Path(path) == storage.SESSION_PATH:
                raise denied()
            return original(path, data)
        mp.setattr(storage, "_atomic_write_bytes", fail_session)
        response = client.post("/api/start_campaign")
        assert response.status_code >= 400 and response.json().get("ok") is not True
        assert response.json().get("campaign_started") is not True
        assert storage.load_session().get("campaign_started") is not True
        assert runtime_bytes()[storage.SESSION_PATH] == before[storage.SESSION_PATH]
        assert "CANARY_" not in response.text and "injected temporary" not in response.text
        return {"opening_rejected": True, "not_started": True}
    else:
        target_name = case.get("target", "session")
        target = {"session": storage.SESSION_PATH, "combat": storage.COMBAT_PATH, "log": storage.SESSION_LOG_PATH}[target_name]
        original = storage._atomic_write_bytes
        def fail(path, data, blocked=target, original=original):
            if Path(path) == blocked:
                raise denied()
            return original(path, data)
        mp.setattr(storage, "_atomic_write_bytes", fail)
    if kind != "opening":
        response = client.post("/api/new_campaign")
        assert response.status_code >= 400 and response.json().get("ok") is not True
        for sentinel in SENTINELS:
            assert sentinel not in response.text
        assert "injected temporary" not in response.text and "CANARY_" not in response.text
        assert runtime_bytes() == before
        assert storage.load_session()["campaign_run_id"] == before_id
        assert other.read_text(encoding="utf-8") == "keep"
    if kind == "recover_after_world":
        mp.setattr("game.campaign_reset.save_world", storage.save_world)
        recovered = create(client)
        assert recovered != before_id
        return {"rolled_back": True, "recovered": recovered}
    return {"rolled_back": True, "identity_preserved": before_id}


def _prepare_choice(client):
    create(client)
    start(client)
    reach(client)


def _chat(case, client, mp):
    from game import authored_consequences as consequences
    calls = {"resolve": 0}
    original = consequences.resolve
    def resolve(*args, **kwargs):
        calls["resolve"] += 1
        return original(*args, **kwargs)
    mp.setattr(consequences, "resolve", resolve)
    _prepare_choice(client)
    before_flags = dict(flags())
    before_log = storage.load_log()
    before_resolve = calls["resolve"]
    kind = case["kind"]
    if kind in {"transient_1", "transient_3"}:
        patch_replace(mp, 1 if kind == "transient_1" else 3)
        response = act(client, "patrol_survey")
        assert response["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
        assert flags().get("patrol_survey") is True and not flags().get("patrol_report")
        assert len(storage.load_log()) == len(before_log) + 1
        assert calls["resolve"] == before_resolve + 1
        return {"committed_once": True}
    if kind.startswith("permanent") or kind == "recover_after_permanent":
        _calls, _delays, restore = patch_replace(mp, 9)
        response = client.post("/api/action", json={
            "action_type": "exploration", "intent": byid("patrol_survey")["label"],
            "exploration_action": {"id": "patrol_survey", "type": "custom", "label": byid("patrol_survey")["label"]},
        })
        assert response.status_code >= 400 and response.json().get("ok") is not True
        assert flags() == before_flags and storage.load_log() == before_log
        assert calls["resolve"] == before_resolve + 1
        assert_no_sentinels(response.text)
        if kind == "recover_after_permanent":
            restore()
            recovered = act(client, "patrol_survey")
            assert flags().get("patrol_survey") is True
            assert recovered["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
            return {"failed_closed": True, "recovered": True}
        return {"failed_closed": True, "checks": kind}
    choose(client, "survey")
    committed = dict(flags())
    if kind == "duplicate_followup":
        act(client, "patrol_record_survey")
        assert flags().get("patrol_survey_recorded") is True
        texts = [entry["gm_output"]["player_facing_text"] for entry in storage.load_log()]
        assert texts.count(byid("patrol_record_survey")["consequence"]["text"]) == 1
        return {"duplicate_ignored": True}
    if kind == "opposite_branch":
        act(client, "patrol_report")
        assert not flags().get("patrol_report") and flags().get("patrol_survey") is True
        return {"exclusive": True}
    if kind == "reload_log":
        first = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        again = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert first == again and byid("patrol_survey")["consequence"]["text"] in first
        return {"stable_transcript": True}
    raise AssertionError(kind)


def _lifecycle(case, client):
    kind = case["kind"]
    if kind == "create":
        first = create(client)
        second = create(client)
        assert first != second and storage.load_session()["campaign_run_id"] == second
        return {"distinct": True}
    identity = create(client)
    if kind == "start":
        body = start(client)
        assert body["session"]["campaign_started"] is True
        return {"started": True}
    body = start(client)
    if kind == "opening_scene":
        assert body["session"]["active_scene_id"] == "frontier_gate"
        assert body["gm_output"]["player_facing_text"]
        return {"scene": "frontier_gate"}
    reach(client)
    if kind == "first_discovery":
        from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE, PRINT_CLUE
        text = "\n".join(entry["gm_output"]["player_facing_text"] for entry in storage.load_log())
        assert NOTICE_CLUE in text and PRINT_CLUE in text
        assert storage.load_session()["active_scene_id"] == "old_milestone"
        return {"discoveries": 2}
    branch = case["branch"]
    follow = choose(client, branch)
    committed = dict(flags())
    if kind == "branch":
        assert committed.get("patrol_" + branch) is True
        other = "report" if branch == "survey" else "survey"
        assert not committed.get("patrol_" + other)
        return {"branch": branch, "follow": follow}
    if kind == "exclusive":
        other = "patrol_report" if branch == "survey" else "patrol_survey"
        act(client, other)
        act(client, "patrol_" + branch)
        assert flags() == committed
        return {"exclusive": True}
    saved = client.post("/api/snapshots", json={"label": branch}).json()["snapshot"]["id"]
    other_id = create(client)
    assert other_id != identity
    client.post("/api/snapshots/load", json={"snapshot_id": saved})
    assert storage.load_session()["campaign_run_id"] == identity
    assert flags() == committed
    chat(client, "I examine the mud prints." if branch == "survey" else "I examine the notice board.")
    assert flags() == committed
    return {"resumed": True, "continued": True}


def _two_campaigns(client):
    survey_id = create(client)
    start(client)
    reach(client)
    choose(client, "survey")
    survey_snap = client.post("/api/snapshots", json={"label": "survey"}).json()["snapshot"]["id"]
    survey_log = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
    report_id = create(client)
    start(client)
    reach(client)
    choose(client, "report")
    report_snap = client.post("/api/snapshots", json={"label": "report"}).json()["snapshot"]["id"]
    report_log = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
    return survey_id, survey_snap, survey_log, report_id, report_snap, report_log


def _transcript(case, client):
    survey_id, survey_snap, survey_log, report_id, report_snap, report_log = _two_campaigns(client)
    survey_only = byid("patrol_record_survey")["consequence"]["text"]
    report_only = byid("patrol_warn_watch")["consequence"]["text"]
    kind = case["kind"]
    if kind == "survey_text":
        assert survey_only in survey_log and report_only not in survey_log
        return {"survey_only": True}
    if kind == "report_text":
        assert report_only in report_log and survey_only not in report_log
        return {"report_only": True}
    if kind == "restore_survey":
        client.post("/api/snapshots/load", json={"snapshot_id": report_snap})
        client.post("/api/snapshots/load", json={"snapshot_id": survey_snap})
        restored = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert restored == survey_log and storage.load_session()["campaign_run_id"] == survey_id
        assert report_only not in restored
        return {"restored": "survey"}
    if kind == "restore_report":
        client.post("/api/snapshots/load", json={"snapshot_id": survey_snap})
        client.post("/api/snapshots/load", json={"snapshot_id": report_snap})
        restored = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
        assert restored == report_log and storage.load_session()["campaign_run_id"] == report_id
        assert survey_only not in restored
        return {"restored": "report"}
    client.post("/api/snapshots/load", json={"snapshot_id": survey_snap})
    continued = chat(client, "I examine the mud prints.")
    survey_after = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
    assert survey_after[:-1] == survey_log
    client.post("/api/snapshots/load", json={"snapshot_id": report_snap})
    report_again = [entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"]]
    assert report_again == report_log
    assert storage.load_session()["campaign_run_id"] == report_id
    assert continued["gm_output"]["player_facing_text"] == survey_after[-1]
    return {"isolated": True}


def _disclosure(case, client, mp):
    from tests.test_pr_play_52_quarantined_integration import PRINT_CLUE
    kind = case["kind"]
    if kind == "rejected_narration":
        from game import integrated_investigation_narration as integrated
        from game import quarantined_investigation_narration as quarantine
        hook = integrated.run_integrated_hook
        mp.setattr(integrated, "run_integrated_hook", lambda handle, **kwargs: hook(handle, generator=quarantine._Replay("The gate is permanently open.", "")))
        create(client)
        start(client)
        chat(client, "I examine the notice board.")
        chat(client, "I follow the missing patrol rumor.")
        response = chat(client, "I examine the weathered milestone.")
        assert PRINT_CLUE in response["gm_output"]["player_facing_text"]
        assert "permanently open" not in response["gm_output"]["player_facing_text"]
        return {"mandatory_kept": True}
    create(client)
    start(client)
    if kind == "discovery":
        response = chat(client, "I examine the notice board.")
        from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE
        assert NOTICE_CLUE in response["gm_output"]["player_facing_text"]
        return {"disclosed": True}
    reach(client)
    if kind == "consequence":
        response = act(client, "patrol_survey")
        assert response["gm_output"]["player_facing_text"] == byid("patrol_survey")["consequence"]["text"]
        return {"published": True}
    if kind == "failed_persist_hidden":
        patch_replace(mp, 9)
        response = client.post("/api/action", json={
            "action_type": "exploration", "intent": byid("patrol_survey")["label"],
            "exploration_action": {"id": "patrol_survey", "type": "custom", "label": byid("patrol_survey")["label"]},
        })
        assert response.json().get("ok") is not True
        assert byid("patrol_survey")["consequence"]["text"] not in response.text
        assert not flags().get("patrol_survey")
        return {"not_published": True}
    response = act(client, "patrol_survey")
    saved = client.post("/api/snapshots", json={"label": "disclosure"}).json()["snapshot"]["id"]
    create(client)
    client.post("/api/snapshots/load", json={"snapshot_id": saved})
    text = "\n".join(entry["gm_output"]["player_facing_text"] for entry in client.get("/api/log").json()["entries"])
    assert response["gm_output"]["player_facing_text"] in text
    assert PRINT_CLUE in text
    return {"reloaded": True}


def _projection(case, client):
    kind = case["kind"]
    if kind == "new":
        response = client.post("/api/new_campaign")
        assert_no_sentinels(response.text)
        assert response.status_code == 200
        return {"clean": True}
    create(client)
    if kind == "start":
        response = client.post("/api/start_campaign")
        assert_no_sentinels(response.text)
        return {"clean": True}
    start(client)
    if kind == "gameplay":
        for text in ("I examine the notice board.", "I follow the missing patrol rumor.", "I examine the weathered milestone."):
            response = client.post("/api/chat", json={"text": text})
            assert response.status_code == 200
            assert_no_sentinels(response.text)
        assert_no_sentinels(json.dumps(act(client, "patrol_survey")))
        invalid = client.post("/api/action", json={
            "action_type": "exploration", "intent": "missing",
            "exploration_action": {"id": "missing", "type": "custom", "label": "missing"},
        })
        assert_no_sentinels(invalid.text)
        return {"clean": True}
    reach(client)
    act(client, "patrol_survey")
    if kind == "save_resume":
        saved = client.post("/api/snapshots", json={"label": "safe"})
        loaded = client.post("/api/snapshots/load", json={"snapshot_id": saved.json()["snapshot"]["id"]})
        assert_no_sentinels(saved.text)
        assert_no_sentinels(loaded.text)
        return {"clean": True}
    assert_no_sentinels(client.get("/api/state").text)
    assert_no_sentinels(client.get("/api/log").text)
    assert "CANARY_" not in client.get("/api/state").text
    return {"clean": True}


def run_case(case):
    tmp = OUT / "holdout_data" / case["id"]
    tmp.mkdir(parents=True, exist_ok=True)
    if case["group"] == "atomic":
        return _atomic(case, tmp)
    return _client_case(case)


def main():
    raw = (OUT / "frozen_holdout.json").read_bytes()
    manifest = json.loads((OUT / "frozen_holdout_manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == manifest["sha256"]
    started = OUT / "holdout_started.json"
    with started.open("x", encoding="utf-8") as handle:
        json.dump({"started": time.time(), "sha256": digest}, handle)
    rows = []
    for case in json.loads(raw):
        begin = time.perf_counter()
        try:
            result = run_case(case)
            row = {"id": case["id"], "group": case["group"], "passed": True, "result": result}
        except Exception:
            row = {"id": case["id"], "group": case["group"], "passed": False, "traceback": traceback.format_exc()}
        row["elapsed_ms"] = round((time.perf_counter() - begin) * 1000, 1)
        rows.append(row)
        (OUT / "holdout_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(case["id"], row["passed"], flush=True)
    summary = {
        "passed": sum(row["passed"] for row in rows),
        "failed": sum(not row["passed"] for row in rows),
        "cases": len(rows),
        "sha256": digest,
        "developer_authored": True,
        "executions": 1,
    }
    (OUT / "holdout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
