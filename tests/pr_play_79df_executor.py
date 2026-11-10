"""Deterministic PR-PLAY-79D-F checks. No live provider and no application edits."""
from __future__ import annotations

import copy
import json
import os

from game.expressive_dialogue import set_expression_transport
from game.publication_contract import narration_skip


ACCEPTED = "You move beside the notice board and stop there."
IRRELEVANT = "Rain keeps falling on the distant hills."
HIDDEN = "You discover a secret tunnel beside the notice board."
DIRECTION = "You move beside the notice board and look northwest."


def _prepare(monkeypatch, *, narrate: bool):
    from tests.test_pr_play_76_physical import enable
    from tests.test_pr_play_79a_continuity import gate

    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    if narrate:
        monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    else:
        monkeypatch.delenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", raising=False)
    session, scene, world = gate()
    scene["scene"]["interactables"] = [{
        "id": "notice_board",
        "label": "Notice board",
        "type": "investigate",
        "reveals_clue": "route",
    }]
    return session, scene, world


def physical(monkeypatch, transport_text, *, narrate=True, second_skip=False):
    """Adjudicate one approach and count bounded expression attempts."""
    from game import bounded_improvisation as bounded

    session, scene, world = _prepare(monkeypatch, narrate=narrate)
    calls = []

    def transport(contract):
        calls.append(contract)
        return {
            "ok": True, "sent": True, "text": transport_text, "latency_ms": 1,
            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
        }

    before = copy.deepcopy(session)
    # The deterministic suite replaces request_expression. Restore a controlled
    # candidate so validation and settlement still run, with no network client.
    monkeypatch.setattr("game.expressive_dialogue.request_expression", transport)
    monkeypatch.delenv("ASHEN_DISABLE_EXPRESSION_GENERATION", raising=False)
    set_expression_transport(lambda _contract: transport_text)
    try:
        text = "I approach the notice board."
        plan = bounded.controlled_request(text, session=session, scene=scene, world=world)
        result = None
        if plan and plan.get("physical"):
            result = bounded.resolve_controlled_fact(
                scene, session, world,
                {"id": plan["id"], "target_id": plan["id"]},
                prompt=text, action_id=plan["id"], label="approach",
            )
        owned = narration_skip(result, scene=scene, session=session) if result else None
        if second_skip and result:
            narration_skip(result, scene=scene, session=session)
    finally:
        set_expression_transport(None)
    meta = (result or {}).get("metadata") or {}
    position = ((session.get("bounded_improvisation") or {}).get("position") or {})
    narration = session.get("last_narration") or {}
    published = (owned[0] if owned else meta.get("engine_publication") or "")
    return {
        "plan_physical": bool(plan and plan.get("physical")),
        "calls": len(calls),
        "facts_seen": [
            str((call.get("prompt") or {}).get("user") or "") for call in calls
        ],
        "published": published,
        "live": bool(meta.get("live_expression_published")),
        "attempted": bool(meta.get("bounded_expression_attempted")),
        "contract": meta.get("publication_contract"),
        "reasons": list(narration.get("reasons") or []),
        "position": position.get("kind"),
        "target": position.get("target_id"),
        "session_before_mutated": before != session,
        "facts_committed": (not calls) or all(
            "COMMITTED FACTS" in item and "beside" in item.casefold() for item in [
                str((call.get("prompt") or {}).get("user") or "") for call in calls
            ]
        ),
        "resolution": result,
    }


def retreat_like_decline(monkeypatch):
    """A climb without a configured check must not become a success."""
    from game.physical_adjudication import plan_physical, commit_physical
    from tests.test_pr_play_76_physical import add

    session, scene, world = _prepare(monkeypatch, narrate=True)
    add(session, ident="wall", label="Wall", scene_id="frontier_gate")
    calls = []

    def transport(_contract):
        calls.append(_contract)
        return "You climb the wall and reach a hidden camp."

    set_expression_transport(transport)
    try:
        text = "I climb the wall."
        plan = plan_physical(text, session=session, scene=scene, world=world)
        result = None
        if plan and plan.get("mode") == "interact":
            result = commit_physical(
                scene, session, world, plan, prompt=text, action_id=plan.get("id"), label="climb",
            )
        published = ""
        if result:
            published = narration_skip(result, scene=scene, session=session)[0]
        elif plan:
            published = plan.get("message") or ""
    finally:
        set_expression_transport(None)
    position = (session.get("bounded_improvisation") or {}).get("position") or {}
    return {
        "calls": len(calls),
        "published": published,
        "elevated": position.get("kind") == "elevated",
        "plan_mode": None if plan is None else plan.get("mode"),
    }


def dialogue(monkeypatch, text, *, establish=False):
    from tests.test_pr_play_78_integrated import play

    session, scene, world = _prepare(monkeypatch, narrate=False)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    calls = []
    set_expression_transport(lambda _contract: calls.append(_contract) or "CANARY_HIDDEN extra speech")
    try:
        if establish:
            play("Hello, Gate Guard.", session, scene, world)
        _plan, result, said, _changed = play(text, session, scene, world)
    finally:
        set_expression_transport(None)
    publication = session.get("last_publication") or {}
    return {
        "said": said,
        "calls": len(calls),
        "owner": publication.get("owner"),
        "dialogue_published": publication.get("dialogue_published"),
        "narration_published": publication.get("narration_published"),
        "visible": publication.get("visible"),
        "contract": (result or {}).get("metadata", {}).get("publication_contract") if result else None,
    }


def recall(source, fact, condition):
    from tests.test_pr_play_79d_closeout import exercise_recall

    return {"recalled": list(exercise_recall(source, fact, condition))}


def renderer(monkeypatch):
    scene, session = None, None
    from tests.test_pr_play_79d_closeout import recall_fixture
    from game.storage import mark_interactable_resolved
    from game.defaults import default_world, default_character
    from game.exploration import resolve_exploration_action

    scene, session = recall_fixture("chart", "The chart records four moons.", "known")
    mark_interactable_resolved(session, "observatory", "chart")
    result = resolve_exploration_action(
        {"scene": scene}, session, default_world(),
        {"id": "chart", "target_id": "chart", "type": "investigate", "prompt": "I examine the chart again."},
        raw_player_text="I examine the chart again.", character=default_character(),
    )
    before = copy.deepcopy(result)
    owned = narration_skip(result)
    return {
        "unchanged": result == before,
        "published": owned[0],
        "same_text": owned[0] == result["metadata"]["engine_publication"],
    }


def cross_campaign(monkeypatch):
    from game.physical_adjudication import plan_physical
    from tests.test_pr_play_76_physical import add

    session, scene, world = _prepare(monkeypatch, narrate=False)
    add(session, ident="alpha_post", label="Alpha post", scene_id="frontier_gate")
    beta = copy.deepcopy(session)
    beta["campaign_run_id"] = "beta"
    before = copy.deepcopy(beta)
    plan = plan_physical("I approach the alpha post.", session=beta, scene=scene, world=world)
    return {
        "targets_alpha": bool(plan and plan.get("id") == "alpha_post"),
        "beta_unchanged": beta == before,
        "plan_is_none": plan is None,
    }


def save_roundtrip(monkeypatch):
    acted = physical(monkeypatch, ACCEPTED, narrate=True)
    encoded = json.loads(json.dumps(acted["resolution"]))
    session_position = acted["position"]
    restored = json.loads(json.dumps({"position": session_position, "published": acted["published"]}))
    return {
        "position": session_position,
        "restored_position": restored["position"],
        "published_survives": restored["published"] == acted["published"],
        "contract_survives": encoded.get("metadata", {}).get("publication_contract") == "FINAL_ENGINE_RESPONSE",
    }


def provider_accounting():
    from game.publication_contract import summarize_provider_rows

    rows = [
        {"event": "admitted", "attempt_id": "a", "sent": True},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 10, "output_tokens": 4, "total_tokens": 14, "retry_attempt": 0, "accepted": True},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 10, "output_tokens": 4, "total_tokens": 14},
        {"event": "completed", "attempt_id": "b", "sent": False, "total_tokens": 9},
        {"event": "completed", "attempt_id": "c", "sent": True, "input_tokens": 3, "output_tokens": 1, "total_tokens": 4, "retry_attempt": 1, "accepted": False},
    ]
    return summarize_provider_rows(rows)


def provider_admission(monkeypatch):
    import tempfile
    from pathlib import Path
    import game.provider_budget as budget

    saved = (
        budget._REQUESTS, budget._STOPPED, budget._STOP_REASON, budget._INITIALIZED,
        budget._INPUT, budget._OUTPUT, budget._RESERVED_INPUT, budget._RESERVED_OUTPUT,
        budget._LEDGER_PATH,
    )
    events = list(budget._EVENTS)
    attempts = dict(budget._ATTEMPTS)
    if not budget._INITIALIZED:
        monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(Path(tempfile.mkdtemp()) / "usage.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.setenv("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "10")
    monkeypatch.setenv("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", "10")
    monkeypatch.setenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "10")
    try:
        attempt = budget.admit_request(
            purpose="expression", owner="pr_play_79df", estimated_input=1, max_output=1, attempt_id="79df-ceiling",
        )
        return {"refusal": attempt.refusal, "sent": bool(attempt.dispatched)}
    finally:
        (
            budget._REQUESTS, budget._STOPPED, budget._STOP_REASON, budget._INITIALIZED,
            budget._INPUT, budget._OUTPUT, budget._RESERVED_INPUT, budget._RESERVED_OUTPUT,
            budget._LEDGER_PATH,
        ) = saved
        budget._EVENTS[:] = events
        budget._ATTEMPTS.clear()
        budget._ATTEMPTS.update(attempts)


def snapshot_recall(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session
    from fastapi.testclient import TestClient
    from game import api, storage

    setup_session(tmp_path, monkeypatch)
    monkeypatch.setattr(storage, "SNAPSHOTS_DIR", tmp_path / "snapshots")
    trace = tmp_path / "publication.jsonl"
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(trace))
    with TestClient(api.app) as client:
        first = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board."})
        known = copy.deepcopy(storage.load_session()["payload"]["clue_knowledge"] if "payload" in storage.load_session() else storage.load_session()["clue_knowledge"])
        snapshot = storage.create_snapshot("79df recall")
        loaded = storage.load_session()
        body = loaded["payload"] if isinstance(loaded, dict) and "payload" in loaded else loaded
        body["clue_knowledge"] = {}
        storage.save_session(loaded)
        storage.load_snapshot(snapshot["id"])
        resumed = storage.load_session()
        resumed_body = resumed["payload"] if isinstance(resumed, dict) and "payload" in resumed else resumed
        repeated = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board again."})
    return {
        "first_status": first.status_code,
        "repeat_status": repeated.status_code,
        "repeat_text": repeated.json()["gm_output"]["player_facing_text"],
        "knowledge_restored": resumed_body["clue_knowledge"] == known,
        "publication_lines": len(trace.read_text(encoding="utf-8").splitlines()) if trace.exists() else 0,
    }


def stale_owner_not_applied(tmp_path, monkeypatch):
    from game.publication_contract import record_completed_publication

    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "publication.jsonl"))
    text = "You move beside the notice board and stop there."
    stale = {
        "owner": "bounded_improvisation.conversation",
        "visible": "Gate Guard says, \"Hello.\"",
        "dialogue_accepted": True,
        "dialogue_published": True,
    }
    row = record_completed_publication(
        {"gm_output": {"player_facing_text": text}},
        source_handler="api_chat",
        publication_context=stale,
        presentation_rows=[{"kind": "narration", "decision": "accepted", "text": text}],
        provider_rows=[{"sent": True, "attempt_id": "expr-1"}],
    )
    return {
        "owner": row["publication_owner"],
        "category": row["response_category"],
        "validation": row["validation_outcome"],
        "attempts": row["provider_attempt_references"],
        "stale_dialogue_owner": row["publication_owner"] == "bounded_improvisation.conversation",
    }


def protected_write_blocked():
    from tests.helpers.storage_isolation import PROTECTED

    target = PROTECTED / "campaign.json"
    try:
        with open(target, "a", encoding="utf-8"):
            return {"blocked": False, "path": str(target)}
    except PermissionError as exc:
        return {"blocked": True, "message": str(exc)}


def matches(actual, expect):
    if "calls" in expect and actual.get("calls") != expect["calls"]:
        return False
    if "live" in expect and actual.get("live") is not expect["live"]:
        return False
    if "contract" in expect and actual.get("contract") != expect["contract"]:
        return False
    if "position" in expect and actual.get("position") != expect["position"]:
        return False
    text = str(actual.get("published") or actual.get("said") or actual.get("repeat_text") or "")
    for piece in expect.get("contains") or []:
        if piece.casefold() not in text.casefold():
            return False
    for piece in expect.get("excludes") or []:
        if piece.casefold() in text.casefold():
            return False
    for key, value in (expect.get("equals") or {}).items():
        if actual.get(key) != value:
            return False
    if "reason" in expect and expect["reason"] not in (actual.get("reasons") or []):
        return False
    if expect.get("nonempty"):
        text = actual.get("published") or actual.get("said") or actual.get("repeat_text") or ""
        if not str(text).strip():
            return False
    return True


def run_case(row, monkeypatch, tmp_path):
    kind = row["kind"]
    if kind == "narration":
        actual = physical(
            monkeypatch, row.get("transport") or ACCEPTED,
            narrate=row.get("gate", True), second_skip=row.get("second_skip", False),
        )
        actual.pop("resolution", None)
    elif kind == "climb":
        actual = retreat_like_decline(monkeypatch)
    elif kind == "dialogue":
        actual = dialogue(monkeypatch, row["input"], establish=not str(row["input"]).lower().startswith("hello"))
    elif kind == "recall":
        actual = recall(row["source"], row["fact"], row["condition"])
    elif kind == "renderer":
        actual = renderer(monkeypatch)
    elif kind == "cross":
        actual = cross_campaign(monkeypatch)
    elif kind == "roundtrip":
        actual = save_roundtrip(monkeypatch)
    elif kind == "accounting":
        actual = provider_accounting()
    elif kind == "admission":
        actual = provider_admission(monkeypatch)
    elif kind == "snapshot":
        actual = snapshot_recall(tmp_path, monkeypatch)
    elif kind == "owner":
        actual = stale_owner_not_applied(tmp_path, monkeypatch)
    elif kind == "protected":
        actual = protected_write_blocked()
    else:
        raise AssertionError("unknown holdout kind")
    actual["pass"] = matches(actual, row["expect"])
    return actual
