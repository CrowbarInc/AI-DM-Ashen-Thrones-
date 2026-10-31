"""Production /api/chat baseline and isolated gold interventions.

Gold inputs exist only in this process. They are marked on each trace and are
not stored as player-facing features.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_eg_r6_r5"


def _dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _done(path: Path) -> set[tuple[str, str]]:
    found = set()
    if not path.exists():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        found.add((str(row.get("arm") or ""), str(row.get("turn_id") or "")))
    return found


def _git() -> dict:
    def run(*args: str) -> str:
        completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
        return (completed.stdout or completed.stderr).strip()

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "upstream": run("status", "-sb").splitlines()[:1],
        "dirty_entries": len([line for line in status.splitlines() if line.strip()]),
        "protected_replay_workflow": (ROOT / ".github/workflows/convergence-checks.yml").exists(),
    }


def _prepare_environment(target: Path) -> None:
    # The provider ledger refuses to reopen an existing file. Each process gets its own.
    stamp = f"{os.getpid()}"
    os.environ.update(
        ASHEN_DATA_DIR=str(target / "import-seed"),
        ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT="1",
        ASHEN_UNIFIED_SEMANTIC_PLANNING="1",
        ASHEN_HOST_CONSTRAINED_CANDIDATES="0",
        ASHEN_DISABLE_PROVIDER_CALLS="0",
        ASHEN_DISABLE_LIVE_INTERPRETATION="0",
        ASHEN_DISABLE_EXPRESSION_GENERATION="0",
        ASHEN_DISABLE_PROVIDER_RETRIES="1",
        ASHEN_PROVIDER_REQUEST_LIMIT="8000",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="12000000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="4000000",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="16000000",
        ASHEN_PROVIDER_TIMEOUT_SECONDS="60",
        ASHEN_PROVIDER_USAGE_PATH=str(target / f"provider_usage_{stamp}.jsonl"),
        ASHEN_SEMANTIC_TRACE_PATH=str(target / f"semantic_traces_{stamp}.jsonl"),
    )


def _snapshot(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def _restore(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def _canonical(world: dict) -> list:
    rows = []
    for person in (world or {}).get("npcs") or []:
        rows.append({
            "id": person.get("id"),
            "topics": [(topic.get("id"), topic.get("text"), topic.get("disclosure") or "public", bool(topic.get("secret"))) for topic in person.get("topics") or []],
        })
    return rows


def _secret_hits(family: dict, turn: dict, text: str) -> list[str]:
    blob = "\n".join(topic["text"] for npc in family["npcs"] for topic in npc["topics"] if topic.get("secret"))
    hits = []
    lowered = text.casefold()
    for phrase in turn.get("forbidden") or []:
        if phrase and phrase.casefold() in blob.casefold() and phrase.casefold() in lowered:
            hits.append(phrase)
    for npc in family["npcs"]:
        for topic in npc["topics"]:
            if topic.get("secret") and topic["text"].casefold() in lowered:
                hits.append(str(topic["id"]))
    return hits


def _plan_from(data: dict, session: dict) -> dict:
    resolution = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    decision = (resolution.get("metadata") or {}).get("conversational_decision") if isinstance(resolution.get("metadata"), dict) else {}
    authorization = decision.get("authorization") if isinstance(decision, dict) and isinstance(decision.get("authorization"), dict) else {}
    history = ((session.get("conversational_context") or {}).get("delivered_exchanges") or [])
    plan = social.get("unified_semantic_plan") or authorization.get("unified_semantic_plan") or {}
    if not plan and history and isinstance(history[-1], dict):
        plan = history[-1].get("unified_semantic_plan") or {}
    return plan if isinstance(plan, dict) else {}


def _trace_delta(path: Path, cursor: int) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[cursor:]
    rows = []
    for line in lines:
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"unparsed": line[:500]})
    return rows


def _raw_plan(traces: list[dict]) -> dict | None:
    for row in reversed(traces):
        raw = row.get("raw_output")
        if not isinstance(raw, str):
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _usage(records: list[dict]) -> list[dict]:
    kept = []
    for record in records:
        if not isinstance(record, dict):
            continue
        kept.append({
            "purpose": record.get("purpose"),
            "model": record.get("model"),
            "configured_model": record.get("configured_model"),
            "request_id": record.get("request_id"),
            "input_tokens": record.get("input_tokens"),
            "output_tokens": record.get("output_tokens"),
            "latency_ms": record.get("latency_ms"),
            "sent": record.get("sent"),
            "refusal": record.get("refusal"),
        })
    return kept


def _install(family: dict, storage) -> str:
    world = storage.load_world()
    scene = storage.load_active_scene()
    scene_id = scene["scene"]["id"]
    cast = []
    for npc in family["npcs"]:
        row = dict(npc)
        row["location"] = scene_id
        cast.append(row)
    world["npcs"] = cast
    world["factions"] = []
    storage.save_world(world)
    scene["scene"].update(
        summary=family["summary"],
        visible_facts=[],
        discoverable_clues=[],
        addressables=[{"id": npc["id"], "name": npc["name"], "kind": "npc", "aliases": []} for npc in family["npcs"]],
    )
    storage.save_scene(scene)
    session = storage.load_session()
    session["campaign_started"] = True
    session["conversational_context"] = {}
    interaction = session.get("interaction_context")
    if isinstance(interaction, dict):
        interaction["active_interaction_target_id"] = None
    storage.save_session(session)
    if storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return str(storage.DATA_DIR)


def _execute_turn(client, storage, family, turn, arm: str, trace_path: Path) -> dict:
    from experiments.pr_eg_r6_r5.gold import (
        authorized_fact,
        correspondence_for_text,
        features,
        filter_topic_rows,
        install_authorized_plan,
        patch_plan,
        relabel_sufficiency,
    )
    from experiments.pr_eg_r6_r5.score import score_reply
    from game.immutable_valid_response import verify_delivery_record
    from game.provider_budget import snapshot
    from game.semantic_correspondence import coverage as original_coverage
    from game.unified_semantic_planning import (
        authorize_information_turn as original_authorize,
        plan_proposer,
        _topic_rows as original_topics,
    )
    import game.semantic_correspondence as correspondence_module
    import game.unified_semantic_planning as planning_module

    flags = features(arm) if arm != "baseline" else {}
    baseline_raw = turn.get("_baseline_raw")
    notes = {"arm": arm}
    before_world = storage.load_world()
    before_canon = _canonical(before_world)
    trace_cursor = len(trace_path.read_text(encoding="utf-8").splitlines()) if trace_path.exists() else 0
    usage_cursor = len(snapshot()["records"])
    started = time.perf_counter()
    expression_previous = os.environ.get("ASHEN_DISABLE_EXPRESSION_GENERATION")

    def proposer(context):
        del context
        proposal, patch_notes = patch_plan(baseline_raw, turn, storage.load_session(), arm)
        notes.update(patch_notes)
        return {"status": "proposed", "plan": proposal, "api_calls": 0, "usage": {}, "gold_intervention": arm}

    def topic_rows(npc):
        rows = original_topics(npc)
        if not flags.get("retrieval"):
            return rows
        return filter_topic_rows(rows, turn, str((npc or {}).get("id") or ""))

    def coverage(request, source, *, question, source_text, participants=(), prior_text=""):
        if flags.get("correspondence"):
            label = correspondence_for_text(source_text, turn, family["npcs"])
            if label:
                return label
        return original_coverage(request, source, question=question, source_text=source_text, participants=participants, prior_text=prior_text)

    def authorize(*args, **kwargs):
        result = original_authorize(*args, **kwargs)
        if flags.get("plan"):
            result = install_authorized_plan(result, turn, family["npcs"])
        elif flags.get("sufficiency"):
            result = relabel_sufficiency(result, turn, family["npcs"])
        return result

    if flags.get("expression_off"):
        os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
    try:
        if arm != "baseline":
            planning_module._topic_rows = topic_rows
            correspondence_module.coverage = coverage
            planning_module.authorize_information_turn = authorize
        context = plan_proposer(proposer if arm != "baseline" else None)
        with context:
            response = client.post("/api/chat?ui_mode=player", json={"text": turn["player"], "ui_mode": "player"})
    finally:
        planning_module._topic_rows = original_topics
        correspondence_module.coverage = original_coverage
        planning_module.authorize_information_turn = original_authorize
        if expression_previous is None:
            os.environ.pop("ASHEN_DISABLE_EXPRESSION_GENERATION", None)
        else:
            os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = expression_previous
    elapsed = (time.perf_counter() - started) * 1000
    data = response.json()
    session = storage.load_session()
    world = storage.load_world()
    gm = data.get("gm_output") if isinstance(data.get("gm_output"), dict) else {}
    text = str(gm.get("player_facing_text") or "")
    accepted = (gm.get("metadata") or {}).get("accepted_response") if isinstance(gm.get("metadata"), dict) else {}
    accepted = accepted if isinstance(accepted, dict) else {}
    history = ((session.get("conversational_context") or {}).get("delivered_exchanges") or [])
    plan = _plan_from(data, session)
    traces = _trace_delta(trace_path, trace_cursor)
    calls = _usage(snapshot()["records"][usage_cursor:])
    leaks = _secret_hits(family, turn, text)
    checks = {
        "http": response.status_code == 200,
        "exact": bool(accepted) and accepted.get("text") == text,
        "sealed": bool(accepted) and verify_delivery_record(accepted),
        "history_exact": bool(history) and history[-1].get("delivered_text") == text,
        "topics_unchanged": _canonical(world) == before_canon,
        "no_restricted_disclosure": not leaks,
        "gold_fact_permitted": authorized_fact(turn, family["npcs"]) is None or not leaks,
    }
    score = score_reply(turn, text)
    expression = (gm.get("metadata") or {}).get("expression_generation") if isinstance(gm.get("metadata"), dict) else None
    return {
        "arm": arm,
        "turn_id": turn["id"],
        "conversation": family["id"],
        "partition": family["partition"],
        "index": turn["index"],
        "player": turn["player"],
        "answer_class": turn["answer_class"],
        "tags": turn["tags"],
        "text": text,
        "plan": plan,
        "expression": expression,
        "sealed_text": accepted.get("text"),
        "checks": checks,
        "restricted_hits": leaks,
        "score": score,
        "latency_ms": round(elapsed, 3),
        "provider_calls": calls,
        "semantic_trace_count": len(traces),
        "raw_plan": _raw_plan(traces) if arm == "baseline" else None,
        "intervention": notes,
        "reason": plan.get("reason"),
        "response_kind": plan.get("response_kind"),
        "addressee_id": plan.get("addressee_id"),
        "selected_source_ids": plan.get("selected_source_ids"),
        "host_line": plan.get("host_line"),
    }


def _families(selected: set[str] | None, partitions: set[str] | None):
    from experiments.pr_eg_r6_r5.corpus import build_corpus

    for family in build_corpus():
        if partitions and family["partition"] not in partitions:
            continue
        if selected and family["id"] not in selected:
            continue
        yield family


def _freeze() -> str:
    from experiments.pr_eg_r6_r5.corpus import corpus_document, corpus_hash, quota_report

    digest = corpus_hash()
    path = OUT / "freeze.json"
    if path.exists():
        recorded = json.loads(path.read_text(encoding="utf-8"))
        if recorded.get("corpus_sha256") != digest:
            raise SystemExit("Frozen corpus hash changed after the freeze. Refusing to run.")
        return digest
    _dump(path, {"corpus_sha256": digest, "quotas": quota_report(), "document_turn_count": corpus_document()["turn_count"]})
    _dump(OUT / "frozen_corpus.json", corpus_document())
    return digest


def run_baseline(families, limit: int | None) -> None:
    import pytest
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_pr_ef_gm_authority import seed_scene

    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "0"
    os.environ["ASHEN_UNIFIED_SEMANTIC_PLANNING"] = "1"
    os.environ["ASHEN_HOST_CONSTRAINED_CANDIDATES"] = "0"
    target = OUT / "baseline_run"
    target.mkdir(parents=True, exist_ok=True)
    rows_path = OUT / "baseline.jsonl"
    done = _done(rows_path)
    trace_path = Path(os.environ["ASHEN_SEMANTIC_TRACE_PATH"])
    for family in families:
        with pytest.MonkeyPatch.context() as monkeypatch:
            seed_scene(target / "state" / family["id"], monkeypatch)
            data_dir = Path(_install(family, storage))
            client = TestClient(api.app)
            count = 0
            for turn in family["turns"]:
                if limit is not None and count >= limit:
                    break
                count += 1
                snap = OUT / "snapshots" / family["id"] / f"{turn['index']:02d}"
                after = OUT / "snapshots" / family["id"] / f"{turn['index']:02d}_after"
                if ("baseline", turn["id"]) in done and after.exists():
                    _restore(after, data_dir)
                    continue
                _snapshot(data_dir, snap)
                try:
                    row = _execute_turn(client, storage, family, turn, "baseline", trace_path)
                except Exception as exc:  # noqa: BLE001 - preserve the rest of the diagnostic run
                    row = {"arm": "baseline", "turn_id": turn["id"], "conversation": family["id"], "partition": family["partition"], "player": turn["player"], "error": type(exc).__name__ + ": " + str(exc)[:500], "score": {"player_facing_success": False}, "checks": {}, "text": ""}
                _append(rows_path, row)
                _snapshot(data_dir, after)
                print(family["id"], turn["index"], "baseline", row.get("response_kind"), row.get("score", {}).get("player_facing_success"), "leak" if row.get("restricted_hits") else "sealed", (row.get("text") or row.get("error") or "")[:120], flush=True)


def run_interventions(arms: list[str], partitions: set[str] | None, conversations: set[str] | None, limit: int | None) -> None:
    import pytest
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_pr_ef_gm_authority import seed_scene

    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "0"
    os.environ["ASHEN_UNIFIED_SEMANTIC_PLANNING"] = "1"
    os.environ["ASHEN_HOST_CONSTRAINED_CANDIDATES"] = "0"
    baseline_rows = {}
    baseline_path = OUT / "baseline.jsonl"
    if not baseline_path.exists():
        raise SystemExit("Baseline jsonl is missing. Run the baseline phase first.")
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            baseline_rows[row["turn_id"]] = row
    target = OUT / "intervention_run"
    target.mkdir(parents=True, exist_ok=True)
    rows_path = OUT / "interventions.jsonl"
    done = _done(rows_path)
    trace_path = Path(os.environ["ASHEN_SEMANTIC_TRACE_PATH"])
    for family in _families(conversations, partitions):
        with pytest.MonkeyPatch.context() as monkeypatch:
            seed_scene(target / "state" / family["id"], monkeypatch)
            data_dir = Path(_install(family, storage))
            client = TestClient(api.app)
            count = 0
            for turn in family["turns"]:
                if limit is not None and count >= limit:
                    break
                count += 1
                snap = OUT / "snapshots" / family["id"] / f"{turn['index']:02d}"
                if not snap.exists():
                    print("missing snapshot", turn["id"], flush=True)
                    continue
                captured = baseline_rows.get(turn["id"]) or {}
                turn = dict(turn)
                turn["_baseline_raw"] = captured.get("raw_plan")
                purposes = {str(call.get("purpose") or "") for call in (captured.get("provider_calls") or []) if isinstance(call, dict)}
                planner_entered = bool(captured.get("raw_plan")) or "semantic_plan" in purposes
                for arm in arms:
                    if (arm, turn["id"]) in done:
                        continue
                    if not planner_entered:
                        row = {
                            "arm": arm,
                            "turn_id": turn["id"],
                            "conversation": family["id"],
                            "partition": family["partition"],
                            "index": turn["index"],
                            "player": turn["player"],
                            "answer_class": turn.get("answer_class"),
                            "tags": turn.get("tags"),
                            "text": captured.get("text") or "",
                            "plan": captured.get("plan"),
                            "checks": captured.get("checks") or {},
                            "restricted_hits": captured.get("restricted_hits") or [],
                            "score": captured.get("score") or {"player_facing_success": False},
                            "latency_ms": 0,
                            "provider_calls": [],
                            "intervention": {"arm": arm, "planner_not_entered": True},
                            "reason": captured.get("reason"),
                            "response_kind": captured.get("response_kind"),
                            "not_intercepted": True,
                        }
                        row["baseline_success"] = (captured.get("score") or {}).get("player_facing_success")
                        row["baseline_text"] = captured.get("text")
                        _append(rows_path, row)
                        print(family["id"], turn["index"], arm, "not-intercepted", row["score"].get("player_facing_success"), flush=True)
                        continue
                    _restore(snap, data_dir)
                    try:
                        row = _execute_turn(client, storage, family, turn, arm, trace_path)
                    except Exception as exc:  # noqa: BLE001
                        row = {"arm": arm, "turn_id": turn["id"], "conversation": family["id"], "partition": family["partition"], "player": turn["player"], "error": type(exc).__name__ + ": " + str(exc)[:500], "score": {"player_facing_success": False}, "checks": {}, "text": ""}
                    row["baseline_success"] = (captured.get("score") or {}).get("player_facing_success")
                    row["baseline_text"] = captured.get("text")
                    _append(rows_path, row)
                    print(family["id"], turn["index"], arm, row.get("response_kind"), row.get("score", {}).get("player_facing_success"), (row.get("text") or row.get("error") or "")[:100], flush=True)
                    if row.get("restricted_hits"):
                        _dump(OUT / "stop.json", {"reason": "intervention_restricted_disclosure", "arm": arm, "turn_id": turn["id"], "hits": row["restricted_hits"]})
                        raise SystemExit("A gold intervention disclosed restricted information. Stopping.")


def run_expression_control(partitions: set[str] | None, conversations: set[str] | None, limit: int | None) -> None:
    """Isolated provider wording of the same authorized sentence. Not a production path."""
    from openai import OpenAI

    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.gm import provider_timeout_seconds
    from game.provider_budget import admit_request
    from experiments.pr_eg_r6_r5.gold import _line_for
    from experiments.pr_eg_r6_r5.score import score_reply

    path = OUT / "expression_control.jsonl"
    done = _done(path)
    count_families = 0
    for family in _families(conversations, partitions):
        count_families += 1
        count = 0
        for turn in family["turns"]:
            if limit is not None and count >= limit:
                break
            count += 1
            if ("I10C", turn["id"]) in done:
                continue
            _kind, line, _authorized = _line_for(turn, family["npcs"])
            system = (
                "Speak one NPC reply. Use only the authorized sentence. "
                "Do not add facts, names, places, numbers, times, or reasons that are not in that sentence. "
                "If the sentence withholds or asks for clarification, do the same."
            )
            user = "Player asked: " + turn["player"] + "\nAuthorized sentence: " + line
            started = time.perf_counter()
            attempt = admit_request(
                owner="pr_eg_r6_r5.expression_control",
                model=DEFAULT_MODEL_NAME,
                purpose="expression_control",
                estimated_input=max(1, (len(system) + len(user)) // 4),
                max_output=180,
            )
            if attempt.refusal:
                usage = attempt.finish({"purpose": "expression_control", "sent": False, "refusal": attempt.refusal, "model": DEFAULT_MODEL_NAME})
                text = ""
                calls = [usage]
            else:
                client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
                response = attempt.dispatch(
                    client.responses.create,
                    model=DEFAULT_MODEL_NAME,
                    input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=0,
                    max_output_tokens=180,
                )
                text = str(getattr(response, "output_text", "") or "")
                usage_obj = getattr(response, "usage", None)
                calls = [attempt.finish({
                    "purpose": "expression_control",
                    "sent": True,
                    "model": str(getattr(response, "model", "") or ""),
                    "request_id": getattr(response, "id", None),
                    "input_tokens": getattr(usage_obj, "input_tokens", None),
                    "output_tokens": getattr(usage_obj, "output_tokens", None),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                })]
            leaks = _secret_hits(family, turn, text)
            row = {
                "arm": "I10C",
                "turn_id": turn["id"],
                "conversation": family["id"],
                "partition": family["partition"],
                "player": turn["player"],
                "authorized_sentence": line,
                "text": text,
                "score": score_reply(turn, text),
                "restricted_hits": leaks,
                "provider_calls": calls,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "checks": {"no_restricted_disclosure": not leaks},
                "intervention": "direct provider expression constrained to the authorized sentence",
            }
            _append(path, row)
            print(family["id"], turn["index"], "I10C", row["score"]["player_facing_success"], text[:100], flush=True)
            if leaks:
                _dump(OUT / "stop.json", {"reason": "expression_control_restricted_disclosure", "turn_id": turn["id"], "hits": leaks})
                raise SystemExit("Expression control disclosed restricted information. Stopping.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PR-EG-R6-R5 conversational pipeline diagnostic")
    parser.add_argument("--phase", choices=("baseline", "interventions", "expression"), required=True)
    parser.add_argument("--partitions", default="")
    parser.add_argument("--conversations", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--arms", default=",".join((
        "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9",
        "intent_referent", "question_source", "retrieval_correspondence", "correspondence_sufficiency", "I10B",
    )))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    _prepare_environment(OUT / "env")
    digest = _freeze()
    if not (OUT / "repository_baseline.json").exists():
        from game.config import DEFAULT_MODEL_NAME, ENABLE_MODEL_ROUTING, MODEL_NAME
        from game.host_constrained_candidates import candidate_selection_enabled
        from game.unified_semantic_planning import unified_semantic_planning_enabled

        _dump(OUT / "repository_baseline.json", {
            "git": _git(),
            "corpus_sha256": digest,
            "model_name_configured": bool(MODEL_NAME),
            "default_model": DEFAULT_MODEL_NAME,
            "model_routing_default": ENABLE_MODEL_ROUTING,
            "unified_semantic_planning_default_off": True,
            "unified_semantic_planning_enabled_for_this_run": unified_semantic_planning_enabled(),
            "host_constrained_candidates_enabled_for_this_run": candidate_selection_enabled(),
            "expression_enabled": os.environ.get("ASHEN_DISABLE_EXPRESSION_GENERATION", "0") in {"0", ""},
            "provider_retries_disabled_for_measurement": True,
            "api_key_recorded": False,
        })
    partitions = {item for item in args.partitions.split(",") if item} or None
    conversations = {item for item in args.conversations.split(",") if item} or None
    limit = args.limit or None
    if args.phase == "baseline":
        run_baseline(_families(conversations, partitions), limit)
    elif args.phase == "interventions":
        run_interventions([item for item in args.arms.split(",") if item], partitions, conversations, limit)
    else:
        run_expression_control(partitions, conversations, limit)


if __name__ == "__main__":
    main()
