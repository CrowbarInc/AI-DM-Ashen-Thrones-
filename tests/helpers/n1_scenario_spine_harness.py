"""N1 scenario-spine harness: build/load spines, run branches, emit session-health artifacts.

Wraps ``tests.helpers.synthetic_runner.run_synthetic_session`` without changing runtime behavior.
All fingerprints and run ids are derived from stable hashes (no wall-clock entropy).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from tests.helpers.n1_scenario_spine_contract import (
    N1BranchComparisonSummary,
    N1BranchDefinition,
    N1BranchPointDefinition,
    N1DeterministicRunConfig,
    N1PerTurnContinuityObservation,
    N1RevisitExpectation,
    N1ScenarioSpineDefinition,
    N1SessionHealthArtifactDict,
    N1SessionHealthSummary,
    N1_SESSION_HEALTH_ARTIFACT_KIND,
    N1_SESSION_HEALTH_ARTIFACT_VERSION,
    N1_REASON_CONTINUITY_OK,
    N1_REASON_CONTINUITY_SCENE_GAP,
    N1_REASON_DRIFT_GM_TEXT_EMPTY,
    N1_REASON_DRIFT_PLAYER_TEXT_EMPTY,
    N1_REASON_FORGOTTEN_ANCHOR,
    N1_REASON_PROGRESSION_CHAIN_BROKEN,
    N1_REASON_PROGRESSION_CHAIN_OK,
    N1_REASON_REVISIT_INCONSISTENT,
    N1_REASON_REVISIT_NOT_APPLICABLE,
    N1_REASON_REVISIT_OK,
    N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,
    N1FinalSessionVerdict,
)
from tests.helpers.synthetic_runner import run_synthetic_session
from tests.helpers.synthetic_types import SyntheticProfile, SyntheticRunResult


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_line(text: object) -> str:
    return " ".join(str(text or "").strip().split())


def _fingerprint_text(text: object) -> str:
    return _sha256_hex(_normalize_line(text))


def _turn_view_sequence(run_result: SyntheticRunResult) -> tuple[dict[str, Any], ...]:
    return tuple(run_result.turn_views or ())


def _gm_text_from_turn_view(view: Mapping[str, Any]) -> str:
    snap = view.get("raw_snapshot")
    if isinstance(snap, dict):
        if isinstance(snap.get("gm_text"), str):
            return snap["gm_text"]
        response = snap.get("response")
        if isinstance(response, dict) and isinstance(response.get("player_facing_text"), str):
            return str(response["player_facing_text"])
    raw = view.get("gm_text")
    return str(raw) if isinstance(raw, str) else ""


def _scene_id_from_turn_view(view: Mapping[str, Any]) -> str | None:
    snap = view.get("raw_snapshot")
    if isinstance(snap, dict):
        sid = snap.get("scene_id")
        if isinstance(sid, str) and sid.strip():
            return sid.strip()
        scene = snap.get("scene")
        if isinstance(scene, dict):
            inner = scene.get("scene")
            if isinstance(inner, dict):
                inner_id = inner.get("id")
                if isinstance(inner_id, str) and inner_id.strip():
                    return inner_id.strip()
    raw = view.get("scene_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def stable_n1_run_id(
    *,
    scenario_spine_id: str,
    branch_id: str,
    deterministic_config: N1DeterministicRunConfig,
    player_texts: tuple[str, ...],
) -> str:
    """Deterministic identifier for an N1 harness run (replay-stable)."""
    payload = json.dumps(
        {
            "scenario_spine_id": str(scenario_spine_id),
            "branch_id": str(branch_id),
            "deterministic_config": _deterministic_config_fingerprint_dict(deterministic_config),
            "player_texts": [_normalize_line(line) for line in player_texts],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_hex(payload)


def _deterministic_config_fingerprint_dict(cfg: N1DeterministicRunConfig) -> dict[str, Any]:
    base = cfg.to_dict()
    # Normalize tuple to list for JSON stability.
    out: dict[str, Any] = {}
    for key in sorted(base.keys()):
        value = base[key]
        if key == "extra_scene_ids" and isinstance(value, tuple):
            out[key] = sorted(str(x) for x in value)
        elif isinstance(value, tuple):
            out[key] = list(value)
        else:
            out[key] = value
    return out


def build_n1_scenario_spine_definition(
    *,
    scenario_spine_id: str,
    narrative_anchor_ids: Sequence[str] = (),
    progression_chain_step_ids: Sequence[str] = (),
    revisit_expectations: Sequence[N1RevisitExpectation] = (),
    metadata: Mapping[str, Any] | None = None,
) -> N1ScenarioSpineDefinition:
    """Construct a validated spine definition (canonical builder)."""
    sid = str(scenario_spine_id).strip()
    if not sid:
        raise ValueError("scenario_spine_id must be non-empty")

    anchors = tuple(str(a).strip() for a in narrative_anchor_ids if str(a).strip())
    steps = tuple(str(s).strip() for s in progression_chain_step_ids if str(s).strip())
    revisits = tuple(revisit_expectations)

    meta = dict(metadata or {})
    return N1ScenarioSpineDefinition(
        scenario_spine_id=sid,
        narrative_anchor_ids=anchors,
        progression_chain_step_ids=steps,
        revisit_expectations=revisits,
        metadata=meta,
)


def load_n1_scenario_spine_from_json(path: str | Path) -> N1ScenarioSpineDefinition:
    """Load a spine definition from JSON on disk."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("spine json root must be an object")

    revisit_raw = data.get("revisit_expectations") or []
    if not isinstance(revisit_raw, list):
        raise TypeError("revisit_expectations must be a list")
    revisits: list[N1RevisitExpectation] = []
    for item in revisit_raw:
        if not isinstance(item, dict):
            raise TypeError("each revisit_expectation must be an object")
        triggers = item.get("trigger_player_substrings") or ()
        if isinstance(triggers, str):
            trig_tuple = (triggers,)
        elif isinstance(triggers, list):
            trig_tuple = tuple(str(x) for x in triggers)
        else:
            raise TypeError("trigger_player_substrings must be a list or string")
        revisits.append(
            N1RevisitExpectation(
                revisit_node_id=str(item["revisit_node_id"]),
                consistency_token=str(item["consistency_token"]),
                trigger_player_substrings=tuple(str(t).strip() for t in trig_tuple if str(t).strip()),
            )
        )

    anchors = data.get("narrative_anchor_ids") or ()
    steps = data.get("progression_chain_step_ids") or ()
    if not isinstance(anchors, list):
        raise TypeError("narrative_anchor_ids must be a list")
    if not isinstance(steps, list):
        raise TypeError("progression_chain_step_ids must be a list")
    meta = data.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        raise TypeError("metadata must be an object when present")

    return build_n1_scenario_spine_definition(
        scenario_spine_id=str(data["scenario_spine_id"]),
        narrative_anchor_ids=[str(x) for x in anchors],
        progression_chain_step_ids=[str(x) for x in steps],
        revisit_expectations=revisits,
        metadata=meta if isinstance(meta, dict) else None,
    )


def dump_n1_scenario_spine_to_json(spine: N1ScenarioSpineDefinition, path: str | Path) -> None:
    """Write a spine definition to JSON (sorted keys, stable arrays)."""
    payload = n1_scenario_spine_to_jsonable(spine)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def n1_scenario_spine_to_jsonable(spine: N1ScenarioSpineDefinition) -> dict[str, Any]:
    revisit = [
        {
            "consistency_token": r.consistency_token,
            "revisit_node_id": r.revisit_node_id,
            "trigger_player_substrings": list(r.trigger_player_substrings),
        }
        for r in spine.revisit_expectations
    ]
    revisit.sort(key=lambda item: item["revisit_node_id"])
    return {
        "metadata": dict(sorted(spine.metadata.items(), key=lambda kv: kv[0])),
        "narrative_anchor_ids": list(spine.narrative_anchor_ids),
        "progression_chain_step_ids": list(spine.progression_chain_step_ids),
        "revisit_expectations": revisit,
        "scenario_spine_id": spine.scenario_spine_id,
    }


def collect_n1_per_turn_continuity_observations(
    *,
    spine: N1ScenarioSpineDefinition,
    run_result: SyntheticRunResult,
) -> tuple[N1PerTurnContinuityObservation, ...]:
    """Derive per-turn observations from ``SyntheticRunResult.turn_views`` only (read-only)."""
    views = _turn_view_sequence(run_result)
    step_index = {step: idx for idx, step in enumerate(spine.progression_chain_step_ids)}
    last_step_idx = -1
    out: list[N1PerTurnContinuityObservation] = []

    for view in views:
        turn_index = int(view.get("turn_index", len(out)))
        gm = _gm_text_from_turn_view(view)
        player = str(view.get("player_text") or "")
        scene_id = _scene_id_from_turn_view(view)
        gm_l = gm.casefold()
        player_l = player.casefold()

        anchor_hits = {aid: (aid.casefold() in gm_l) for aid in spine.narrative_anchor_ids}
        prog_hits = {sid: (sid.casefold() in gm_l) for sid in spine.progression_chain_step_ids}
        for sid, hit in prog_hits.items():
            if hit:
                idx = step_index[sid]
                last_step_idx = max(last_step_idx, idx)

        revisit_hits: dict[str, bool] = {}
        for rev in spine.revisit_expectations:
            triggered = any(t.casefold() in player_l for t in rev.trigger_player_substrings)
            revisit_hits[rev.revisit_node_id] = triggered

        out.append(
            N1PerTurnContinuityObservation(
                turn_index=turn_index,
                scene_id=scene_id,
                gm_text_fingerprint=_fingerprint_text(gm),
                player_text_fingerprint=_fingerprint_text(player),
                anchor_hits=dict(sorted(anchor_hits.items(), key=lambda kv: kv[0])),
                progression_hits=dict(sorted(prog_hits.items(), key=lambda kv: kv[0])),
                progression_chain_index_ceiling=last_step_idx,
                revisit_hits=dict(sorted(revisit_hits.items(), key=lambda kv: kv[0])),
            )
        )
    return tuple(out)


def _forgotten_anchor_flags(
    *,
    spine: N1ScenarioSpineDefinition,
    observations: tuple[N1PerTurnContinuityObservation, ...],
) -> dict[str, bool]:
    flags = {aid: False for aid in spine.narrative_anchor_ids}
    if not observations or not spine.narrative_anchor_ids:
        return flags

    n = len(observations)
    establish_cutoff = max(0, n // 2)
    tail_start = max(0, n - min(3, n))

    for aid in spine.narrative_anchor_ids:
        established = any(obs.anchor_hits.get(aid, False) for obs in observations[: establish_cutoff + 1])
        present_in_tail = any(obs.anchor_hits.get(aid, False) for obs in observations[tail_start:])
        if established and not present_in_tail:
            flags[aid] = True
    return dict(sorted(flags.items(), key=lambda kv: kv[0]))


def _progression_chain_integrity(
    *,
    spine: N1ScenarioSpineDefinition,
    observations: tuple[N1PerTurnContinuityObservation, ...],
) -> tuple[bool, dict[str, bool], list[str]]:
    flags = {f"step_seen:{step}": False for step in spine.progression_chain_step_ids}
    reasons: list[str] = []
    if not spine.progression_chain_step_ids:
        return True, flags, [N1_REASON_PROGRESSION_CHAIN_OK]

    step_index = {step: idx for idx, step in enumerate(spine.progression_chain_step_ids)}
    last_idx = -1
    broken = False
    for obs in observations:
        for step in spine.progression_chain_step_ids:
            if obs.progression_hits.get(step):
                idx = step_index[step]
                flags[f"step_seen:{step}"] = True
                if idx < last_idx:
                    broken = True
                last_idx = max(last_idx, idx)

    all_seen = all(flags[f"step_seen:{step}"] for step in spine.progression_chain_step_ids)
    if broken or not all_seen:
        reasons.append(N1_REASON_PROGRESSION_CHAIN_BROKEN)
    else:
        reasons.append(N1_REASON_PROGRESSION_CHAIN_OK)
    ok = not broken and all_seen
    return ok, dict(sorted(flags.items(), key=lambda kv: kv[0])), reasons


def _revisit_consistency(
    spine: N1ScenarioSpineDefinition,
    run_result: SyntheticRunResult,
) -> tuple[bool, dict[str, bool], list[str]]:
    flags = {rev.revisit_node_id: False for rev in spine.revisit_expectations}
    reasons: list[str] = []
    if not spine.revisit_expectations:
        return True, flags, [N1_REASON_REVISIT_NOT_APPLICABLE]

    views = _turn_view_sequence(run_result)
    ok_all = True
    for rev in spine.revisit_expectations:
        if not rev.trigger_player_substrings:
            reasons.append(N1_REASON_REVISIT_NOT_APPLICABLE)
            continue
        last_gm = ""
        triggered = False
        for view in views:
            player = str(view.get("player_text") or "")
            player_l = player.casefold()
            if any(t.casefold() in player_l for t in rev.trigger_player_substrings):
                triggered = True
                last_gm = _gm_text_from_turn_view(view)
        if not triggered:
            reasons.append(N1_REASON_REVISIT_NOT_APPLICABLE)
            continue
        token_ok = rev.consistency_token.casefold() in last_gm.casefold()
        flags[rev.revisit_node_id] = not token_ok
        if not token_ok:
            ok_all = False
            reasons.append(f"{N1_REASON_REVISIT_INCONSISTENT}:{rev.revisit_node_id}")
        else:
            reasons.append(f"{N1_REASON_REVISIT_OK}:{rev.revisit_node_id}")
    return ok_all, dict(sorted(flags.items(), key=lambda kv: kv[0])), reasons


def _scene_gap_reasons(observations: tuple[N1PerTurnContinuityObservation, ...]) -> tuple[bool, list[str]]:
    """Detect alternating non-None scene ids (lightweight continuity probe)."""
    scenes = [obs.scene_id for obs in observations]
    non_null = [s for s in scenes if s]
    if len(non_null) < 3:
        return True, []
    # A-B-A pattern with distinct A,B is suspicious for a single session spine check.
    reasons: list[str] = []
    for i in range(len(non_null) - 2):
        a, b, c = non_null[i], non_null[i + 1], non_null[i + 2]
        if a != b and b != c and a == c:
            reasons.append(f"{N1_REASON_CONTINUITY_SCENE_GAP}:{a}->{b}->{c}")
    ok = not reasons
    return ok, reasons


def compute_n1_session_health_summary(
    *,
    spine: N1ScenarioSpineDefinition,
    branch: N1BranchDefinition,
    run_result: SyntheticRunResult,
    deterministic_config: N1DeterministicRunConfig,
    observations: tuple[N1PerTurnContinuityObservation, ...] | None = None,
) -> N1SessionHealthSummary:
    """Aggregate observations into session-health fields and sorted reason codes."""
    obs = observations or collect_n1_per_turn_continuity_observations(spine=spine, run_result=run_result)
    views = _turn_view_sequence(run_result)
    gm_empty = sum(1 for v in views if not _normalize_line(_gm_text_from_turn_view(v)))
    player_empty = sum(1 for v in views if not _normalize_line(v.get("player_text")))

    drift_flags = {
        "gm_text_empty_turns": gm_empty > 0,
        "player_text_empty_turns": player_empty > 0,
    }
    forgotten = _forgotten_anchor_flags(spine=spine, observations=obs)
    prog_ok, prog_flags, prog_reasons = _progression_chain_integrity(spine=spine, observations=obs)
    revisit_ok, revisit_flags, revisit_reasons = _revisit_consistency(spine, run_result)
    scene_ok, scene_reasons = _scene_gap_reasons(obs)

    continuity_ok = (gm_empty == 0 and player_empty == 0) and scene_ok

    reason_parts: list[str] = []
    if gm_empty:
        reason_parts.append(N1_REASON_DRIFT_GM_TEXT_EMPTY)
    if player_empty:
        reason_parts.append(N1_REASON_DRIFT_PLAYER_TEXT_EMPTY)
    reason_parts.extend(scene_reasons)
    if continuity_ok and not scene_reasons and gm_empty == 0 and player_empty == 0:
        reason_parts.append(N1_REASON_CONTINUITY_OK)
    reason_parts.extend(prog_reasons)
    reason_parts.extend(revisit_reasons)
    for aid, flagged in forgotten.items():
        if flagged:
            reason_parts.append(f"{N1_REASON_FORGOTTEN_ANCHOR}:{aid}")

    reason_codes = tuple(sorted(set(reason_parts)))

    aggregate_issue_counts = {
        "drift_gm_empty_turns": gm_empty,
        "drift_player_empty_turns": player_empty,
        "forgotten_anchors": sum(1 for v in forgotten.values() if v),
        "progression_issues": 0 if prog_ok else 1,
        "revisit_issues": sum(1 for v in revisit_flags.values() if v),
        "scene_gap_issues": len(scene_reasons),
    }

    verdict: N1FinalSessionVerdict
    if len(obs) == 0:
        verdict = "not_evaluated"
    elif not prog_ok or any(forgotten.values()) or any(revisit_flags.values()) or not scene_ok:
        verdict = "fail"
    elif drift_flags["gm_text_empty_turns"] or drift_flags["player_text_empty_turns"]:
        verdict = "warn"
    else:
        verdict = "pass"

    player_texts = tuple(str(v.get("player_text") or "") for v in views)
    run_id = stable_n1_run_id(
        scenario_spine_id=spine.scenario_spine_id,
        branch_id=branch.branch_id,
        deterministic_config=deterministic_config,
        player_texts=player_texts,
    )

    return N1SessionHealthSummary(
        run_id=run_id,
        scenario_spine_id=spine.scenario_spine_id,
        branch_id=branch.branch_id,
        deterministic_config=deterministic_config,
        turn_count=len(obs),
        per_turn_observations=obs,
        continuity_verdict_ok=continuity_ok,
        continuity_verdict_notes=";".join(scene_reasons) if scene_reasons else "",
        drift_flags=dict(sorted(drift_flags.items(), key=lambda kv: kv[0])),
        forgotten_anchor_flags=forgotten,
        progression_chain_integrity_ok=prog_ok,
        progression_chain_integrity_flags=prog_flags,
        revisit_consistency_ok=revisit_ok,
        revisit_consistency_flags=revisit_flags,
        aggregate_issue_counts=dict(sorted(aggregate_issue_counts.items(), key=lambda kv: kv[0])),
        final_session_verdict=verdict,
        reason_codes=reason_codes,
    )


def emit_n1_session_health_artifact_dict(summary: N1SessionHealthSummary) -> N1SessionHealthArtifactDict:
    """Normalize a session-health summary into a JSON-ready dict (sorted keys, stable lists)."""
    body = n1_session_health_summary_to_jsonable(summary)
    out: dict[str, Any] = {
        "artifact_kind": N1_SESSION_HEALTH_ARTIFACT_KIND,
        "artifact_version": N1_SESSION_HEALTH_ARTIFACT_VERSION,
        **body,
    }
    return _sort_dict_recursive(out)  # type: ignore[return-value]


def n1_session_health_summary_to_jsonable(summary: N1SessionHealthSummary) -> dict[str, Any]:
    cfg = _deterministic_config_fingerprint_dict(summary.deterministic_config)
    turns: list[dict[str, Any]] = []
    for obs in summary.per_turn_observations:
        turns.append(
            {
                "anchor_hits": dict(sorted(obs.anchor_hits.items(), key=lambda kv: kv[0])),
                "gm_text_fingerprint": obs.gm_text_fingerprint,
                "player_text_fingerprint": obs.player_text_fingerprint,
                "progression_chain_index_ceiling": obs.progression_chain_index_ceiling,
                "progression_hits": dict(sorted(obs.progression_hits.items(), key=lambda kv: kv[0])),
                "revisit_hits": dict(sorted(obs.revisit_hits.items(), key=lambda kv: kv[0])),
                "scene_id": obs.scene_id,
                "turn_index": obs.turn_index,
            }
        )
    return {
        "aggregate_issue_counts": dict(sorted(summary.aggregate_issue_counts.items(), key=lambda kv: kv[0])),
        "branch_id": summary.branch_id,
        "continuity_verdict_notes": summary.continuity_verdict_notes,
        "continuity_verdict_ok": summary.continuity_verdict_ok,
        "deterministic_config": dict(sorted(cfg.items(), key=lambda kv: kv[0])),
        "drift_flags": dict(sorted(summary.drift_flags.items(), key=lambda kv: kv[0])),
        "final_session_verdict": summary.final_session_verdict,
        "forgotten_anchor_flags": dict(sorted(summary.forgotten_anchor_flags.items(), key=lambda kv: kv[0])),
        "per_turn_observations": turns,
        "progression_chain_integrity_flags": dict(
            sorted(summary.progression_chain_integrity_flags.items(), key=lambda kv: kv[0])
        ),
        "progression_chain_integrity_ok": summary.progression_chain_integrity_ok,
        "reason_codes": list(summary.reason_codes),
        "revisit_consistency_flags": dict(sorted(summary.revisit_consistency_flags.items(), key=lambda kv: kv[0])),
        "revisit_consistency_ok": summary.revisit_consistency_ok,
        "run_id": summary.run_id,
        "scenario_spine_id": summary.scenario_spine_id,
        "turn_count": summary.turn_count,
    }


def _sort_dict_recursive(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sort_dict_recursive(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_sort_dict_recursive(v) for v in value]
    return value


def deterministic_json_dumps(payload: Mapping[str, Any]) -> str:
    """Deterministic JSON string (sorted keys at every object level)."""
    normalized = _sort_dict_recursive(dict(payload))
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def execute_n1_spine_branch_with_shared_prefix(
    *,
    spine: N1ScenarioSpineDefinition,
    branch_point: N1BranchPointDefinition,
    branch: N1BranchDefinition,
    profile: SyntheticProfile,
    deterministic_config: N1DeterministicRunConfig,
    shared_prefix_player_texts: tuple[str, ...],
    synthetic_runner_kwargs: dict[str, Any] | None = None,
) -> SyntheticRunResult:
    """Run one branch: shared prefix lines + branch suffix; wraps ``run_synthetic_session``."""
    _ = spine.scenario_spine_id
    if branch.branch_point_id != branch_point.branch_point_id:
        raise ValueError("branch.branch_point_id must match branch_point.branch_point_id")
    prefix = tuple(str(x) for x in shared_prefix_player_texts)
    if len(prefix) != int(branch_point.shared_prefix_turn_count):
        raise ValueError(
            f"shared_prefix_turn_count={branch_point.shared_prefix_turn_count} "
            f"but shared_prefix_player_texts has length {len(prefix)}"
        )
    suffix = tuple(str(x) for x in branch.suffix_player_texts)
    full_texts = prefix + suffix
    extra = dict(synthetic_runner_kwargs or {})
    # Caller-supplied keys should not override the spine-controlled player line list.
    extra.pop("player_texts", None)
    extra.pop("max_turns", None)
    extra.pop("seed", None)
    extra.pop("use_fake_gm", None)
    extra.pop("profile", None)

    return run_synthetic_session(
        profile=profile,
        seed=int(deterministic_config.seed),
        max_turns=len(full_texts),
        player_texts=full_texts,
        use_fake_gm=bool(deterministic_config.use_fake_gm),
        starting_scene_id=deterministic_config.starting_scene_id,
        extra_scene_ids=deterministic_config.extra_scene_ids,
        stall_repeat_threshold=int(deterministic_config.stall_repeat_threshold),
        **extra,
    )


def compare_n1_branch_session_health_summaries(
    *,
    scenario_spine_id: str,
    branch_point: N1BranchPointDefinition,
    summaries: Sequence[N1SessionHealthSummary],
    branch_full_player_texts: Mapping[str, Sequence[str]],
) -> N1BranchComparisonSummary:
    """Compare multiple branches that share the same prefix length (caller-enforced).

    ``branch_full_player_texts`` maps ``branch_id`` -> full ordered player lines for that run
    (prefix + suffix). Prefix segments must be identical across branches for a valid comparison.
    """
    ids = tuple(sorted(s.branch_id for s in summaries))
    if len(set(ids)) != len(ids):
        raise ValueError("branch_id values must be unique in summaries")

    prefix_fp = _sha256_hex(
        json.dumps(
            {
                "branch_point_id": branch_point.branch_point_id,
                "shared_prefix_turn_count": int(branch_point.shared_prefix_turn_count),
                "scenario_spine_id": scenario_spine_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    prefix_segments: list[tuple[str, ...]] = []
    per_suffix: dict[str, str] = {}
    per_final_scene: dict[str, str | None] = {}
    for s in summaries:
        texts = tuple(_normalize_line(x) for x in (branch_full_player_texts.get(s.branch_id) or ()))
        if len(texts) != s.turn_count:
            raise ValueError(
                f"branch_full_player_texts[{s.branch_id!r}] length {len(texts)} "
                f"does not match summary.turn_count {s.turn_count}"
            )
        k = int(branch_point.shared_prefix_turn_count)
        prefix_segments.append(texts[:k])
        suffix = texts[k:]
        per_suffix[s.branch_id] = _sha256_hex(json.dumps(list(suffix), sort_keys=True, separators=(",", ":")))
        per_final_scene[s.branch_id] = s.per_turn_observations[-1].scene_id if s.per_turn_observations else None

    if len({seg for seg in prefix_segments}) > 1:
        raise ValueError("shared prefix player texts must match across branches for this comparison")

    scene_values = list(per_final_scene.values())
    divergence = len({v for v in scene_values}) > 1

    reason_codes: list[str] = []
    if divergence:
        reason_codes.append(N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID)
    reason_codes_sorted = tuple(sorted(reason_codes))

    return N1BranchComparisonSummary(
        scenario_spine_id=scenario_spine_id,
        branch_point_id=branch_point.branch_point_id,
        compared_branch_ids=ids,
        shared_prefix_turn_count=int(branch_point.shared_prefix_turn_count),
        shared_prefix_fingerprint=prefix_fp,
        per_branch_suffix_fingerprint=dict(sorted(per_suffix.items(), key=lambda kv: kv[0])),
        per_branch_final_scene_id=dict(sorted(per_final_scene.items(), key=lambda kv: kv[0])),
        divergence_detected=divergence,
        reason_codes=reason_codes_sorted,
    )

