"""Deterministic longitudinal continuity analysis for N1 (test tooling only).

Builds on ``N1PerTurnContinuityObservation``, ``N1SessionHealthSummary``, and branch
comparison outputs without changing harness collection or playability contracts.
All logic is snapshot-derived (fingerprints, booleans, scene ids); no prose scoring.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

from tests.helpers.n1_scenario_spine_harness import deterministic_json_dumps
from tests.helpers.n1_scenario_spine_contract import (
    N1BranchComparisonSummary,
    N1BranchPointDefinition,
    N1PerTurnContinuityObservation,
    N1ScenarioSpineDefinition,
    N1SessionHealthSummary,
    N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,
    N1_REASON_BRANCH_SHARED_FACT_VIOLATION,
    N1_REASON_CONTINUITY_SCENE_GAP,
    N1_REASON_DRIFT_GM_TEXT_EMPTY,
    N1_REASON_DRIFT_PLAYER_TEXT_EMPTY,
    N1_REASON_FORGOTTEN_ANCHOR,
    N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
    N1_REASON_PROGRESSION_CHAIN_BROKEN,
    N1_REASON_REFERENT_INCONSISTENT,
    N1_REASON_REVISIT_INCONSISTENT,
    N1_REASON_REVISIT_SCENE_UNSTABLE,
)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_line(text: object) -> str:
    return " ".join(str(text or "").strip().split())


def _fingerprint_text(text: object) -> str:
    return _sha256_hex(_normalize_line(text))


def _empty_text_fingerprint() -> str:
    return _fingerprint_text("")


N1ContinuityIssueSeverity = Literal["hard", "soft", "info"]
N1ContinuityIssueCategory = Literal[
    "state_drift",
    "anchor_persistence",
    "progression_chain",
    "referent_consistency",
    "revisit_stability",
    "narrative_grounding",
    "branch_divergence",
]


@dataclass(frozen=True)
class N1ContinuityIssue:
    """Single longitudinal issue with stable machine reason and turn span metadata."""

    severity: N1ContinuityIssueSeverity
    category: N1ContinuityIssueCategory
    reason_code: str
    first_seen_turn: int | None
    last_seen_turn: int | None
    detail: str


@dataclass(frozen=True)
class N1LongitudinalContinuityReport:
    """Enriched, deterministic continuity rollup for one session-health summary."""

    run_id: str
    scenario_spine_id: str
    branch_id: str
    base_reason_codes: tuple[str, ...]
    analyzer_reason_codes: tuple[str, ...]
    merged_reason_codes: tuple[str, ...]
    issues: tuple[N1ContinuityIssue, ...]
    aggregate_issue_counters: dict[str, int]
    severity_counters: dict[str, int]


def _sorted_unique_strs(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(items)))


def _anchor_first_last_hits(
    observations: tuple[N1PerTurnContinuityObservation, ...], anchor_id: str
) -> tuple[int | None, int | None]:
    first: int | None = None
    last: int | None = None
    for obs in observations:
        if obs.anchor_hits.get(anchor_id):
            ti = int(obs.turn_index)
            if first is None:
                first = ti
            last = ti
    return first, last


def _progression_step_turns(
    observations: tuple[N1PerTurnContinuityObservation, ...], step_id: str
) -> tuple[int, ...]:
    turns: list[int] = []
    for obs in observations:
        if obs.progression_hits.get(step_id):
            turns.append(int(obs.turn_index))
    return tuple(sorted(set(turns)))


def _referent_inconsistency_issues(
    observations: tuple[N1PerTurnContinuityObservation, ...], anchor_id: str
) -> list[N1ContinuityIssue]:
    """Heuristic: anchor disappears then returns while scene_id stays stable (structured only)."""
    if len(observations) < 4:
        return []
    hits = [bool(o.anchor_hits.get(anchor_id)) for o in observations]
    scenes = [o.scene_id for o in observations]
    issues: list[N1ContinuityIssue] = []
    n = len(observations)
    for i in range(n - 3):
        if not (hits[i] and not hits[i + 1] and not hits[i + 2] and hits[i + 3]):
            continue
        s0, s1, s2, s3 = scenes[i], scenes[i + 1], scenes[i + 2], scenes[i + 3]
        if s0 is None or s0 != s1 or s1 != s2 or s2 != s3:
            continue
        code = f"{N1_REASON_REFERENT_INCONSISTENT}:{anchor_id}"
        issues.append(
            N1ContinuityIssue(
                severity="soft",
                category="referent_consistency",
                reason_code=code,
                first_seen_turn=int(observations[i].turn_index),
                last_seen_turn=int(observations[i + 3].turn_index),
                detail=f"anchor_gap_same_scene:{s0}",
            )
        )
    return issues


def _revisit_scene_stability_issues(
    spine: N1ScenarioSpineDefinition,
    observations: tuple[N1PerTurnContinuityObservation, ...],
    player_texts_by_turn: dict[int, str] | None,
) -> list[N1ContinuityIssue]:
    """If revisit triggers on multiple turns, distinct non-null scene_ids imply instability."""
    if not spine.revisit_expectations or player_texts_by_turn is None:
        return []
    issues: list[N1ContinuityIssue] = []
    by_turn = {int(o.turn_index): o for o in observations}
    for rev in sorted(spine.revisit_expectations, key=lambda r: r.revisit_node_id):
        if not rev.trigger_player_substrings:
            continue
        trigger_turns: list[int] = []
        for obs in observations:
            pl = str(player_texts_by_turn.get(int(obs.turn_index), "")).casefold()
            if any(t.casefold() in pl for t in rev.trigger_player_substrings):
                trigger_turns.append(int(obs.turn_index))
        if len(trigger_turns) < 2:
            continue
        scenes: list[str] = []
        for ti in sorted(set(trigger_turns)):
            o = by_turn.get(ti)
            if o and isinstance(o.scene_id, str) and o.scene_id.strip():
                scenes.append(o.scene_id.strip())
        distinct = sorted(set(scenes))
        if len(distinct) > 1:
            code = f"{N1_REASON_REVISIT_SCENE_UNSTABLE}:{rev.revisit_node_id}"
            issues.append(
                N1ContinuityIssue(
                    severity="soft",
                    category="revisit_stability",
                    reason_code=code,
                    first_seen_turn=min(trigger_turns),
                    last_seen_turn=max(trigger_turns),
                    detail="scenes:" + "->".join(distinct),
                )
            )
    return issues


def _narrative_grounding_degradation_issue(
    spine: N1ScenarioSpineDefinition,
    observations: tuple[N1PerTurnContinuityObservation, ...],
) -> list[N1ContinuityIssue]:
    """Structured-only: drop in any-anchor hit rate between session halves (heuristic)."""
    if len(observations) < 6 or not spine.narrative_anchor_ids:
        return []
    n = len(observations)
    mid = n // 2
    first = observations[:mid]
    second = observations[mid:]

    def _rate(chunk: tuple[N1PerTurnContinuityObservation, ...]) -> float:
        if not chunk:
            return 0.0
        hits = 0
        for o in chunk:
            if any(o.anchor_hits.get(a) for a in spine.narrative_anchor_ids):
                hits += 1
        return hits / float(len(chunk))

    r1, r2 = _rate(first), _rate(second)
    if r1 >= 0.34 and r2 < r1 * 0.5:
        return [
            N1ContinuityIssue(
                severity="soft",
                category="narrative_grounding",
                reason_code=N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
                first_seen_turn=int(first[0].turn_index),
                last_seen_turn=int(second[-1].turn_index),
                detail=f"anchor_hit_rate_first={r1:.4f};second={r2:.4f}",
            )
        ]
    return []


def _issues_from_session_summary(summary: N1SessionHealthSummary) -> list[N1ContinuityIssue]:
    """Classify harness-derived signals into severity buckets (no new string matching)."""
    issues: list[N1ContinuityIssue] = []
    obs = summary.per_turn_observations
    empty_fp = _empty_text_fingerprint()
    if summary.drift_flags.get("gm_text_empty_turns"):
        turns = [int(o.turn_index) for o in obs if o.gm_text_fingerprint == empty_fp]
        issues.append(
            N1ContinuityIssue(
                severity="soft",
                category="state_drift",
                reason_code=N1_REASON_DRIFT_GM_TEXT_EMPTY,
                first_seen_turn=min(turns) if turns else None,
                last_seen_turn=max(turns) if turns else None,
                detail="gm_text_empty_turns",
            )
        )
    if summary.drift_flags.get("player_text_empty_turns"):
        turns = [int(o.turn_index) for o in obs if o.player_text_fingerprint == empty_fp]
        issues.append(
            N1ContinuityIssue(
                severity="soft",
                category="state_drift",
                reason_code=N1_REASON_DRIFT_PLAYER_TEXT_EMPTY,
                first_seen_turn=min(turns) if turns else None,
                last_seen_turn=max(turns) if turns else None,
                detail="player_text_empty_turns",
            )
        )
    for note in (x for x in summary.continuity_verdict_notes.split(";") if x.strip()):
        if note.startswith(f"{N1_REASON_CONTINUITY_SCENE_GAP}:"):
            issues.append(
                N1ContinuityIssue(
                    severity="soft",
                    category="state_drift",
                    reason_code=note,
                    first_seen_turn=None,
                    last_seen_turn=None,
                    detail=note,
                )
            )
    if not summary.progression_chain_integrity_ok:
        turns_all = [int(o.turn_index) for o in obs]
        first_break = min(turns_all) if turns_all else None
        last_break = max(turns_all) if turns_all else None
        steps = sorted(
            k.removeprefix("step_seen:")
            for k in summary.progression_chain_integrity_flags
            if k.startswith("step_seen:")
        )
        seen_parts = [f"{sid}@{','.join(str(t) for t in _progression_step_turns(obs, sid))}" for sid in steps]
        issues.append(
            N1ContinuityIssue(
                severity="hard",
                category="progression_chain",
                reason_code=N1_REASON_PROGRESSION_CHAIN_BROKEN,
                first_seen_turn=first_break,
                last_seen_turn=last_break,
                detail=";".join(seen_parts),
            )
        )
    for aid, flagged in sorted(summary.forgotten_anchor_flags.items(), key=lambda kv: kv[0]):
        if not flagged:
            continue
        first, last_hit = _anchor_first_last_hits(obs, aid)
        issues.append(
            N1ContinuityIssue(
                severity="hard",
                category="anchor_persistence",
                reason_code=f"{N1_REASON_FORGOTTEN_ANCHOR}:{aid}",
                first_seen_turn=first,
                last_seen_turn=last_hit,
                detail="forgotten_in_session_tail",
            )
        )
    for nid, bad in sorted(summary.revisit_consistency_flags.items(), key=lambda kv: kv[0]):
        if not bad:
            continue
        issues.append(
            N1ContinuityIssue(
                severity="hard",
                category="revisit_stability",
                reason_code=f"{N1_REASON_REVISIT_INCONSISTENT}:{nid}",
                first_seen_turn=None,
                last_seen_turn=None,
                detail="token_mismatch_last_trigger",
            )
        )
    return issues


def _analyzer_only_issues(
    spine: N1ScenarioSpineDefinition,
    summary: N1SessionHealthSummary,
    player_texts_by_turn: dict[int, str] | None,
) -> list[N1ContinuityIssue]:
    obs = summary.per_turn_observations
    out: list[N1ContinuityIssue] = []
    for aid in sorted(spine.narrative_anchor_ids):
        out.extend(_referent_inconsistency_issues(obs, aid))
    out.extend(_revisit_scene_stability_issues(spine, obs, player_texts_by_turn))
    out.extend(_narrative_grounding_degradation_issue(spine, obs))
    return out


def _merge_reason_codes(
    base: tuple[str, ...], issues: tuple[N1ContinuityIssue, ...]
) -> tuple[str, ...]:
    extra = tuple(i.reason_code for i in issues)
    return _sorted_unique_strs(base + extra)


def _aggregate_counters(issues: tuple[N1ContinuityIssue, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        key = issue.reason_code.split(":", 1)[0]
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[0]))


def _severity_counters(issues: tuple[N1ContinuityIssue, ...]) -> dict[str, int]:
    out: dict[str, int] = {"hard": 0, "info": 0, "soft": 0}
    for i in issues:
        out[i.severity] = out.get(i.severity, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def _issue_sort_key(issue: N1ContinuityIssue) -> tuple[str, str, str, int, int]:
    fs = issue.first_seen_turn if issue.first_seen_turn is not None else -1
    ls = issue.last_seen_turn if issue.last_seen_turn is not None else -1
    return (issue.severity, issue.category, issue.reason_code, fs, ls)


def analyze_n1_longitudinal_continuity(
    *,
    spine: N1ScenarioSpineDefinition,
    summary: N1SessionHealthSummary,
    player_texts_by_turn: dict[int, str] | None = None,
) -> N1LongitudinalContinuityReport:
    """Deterministic longitudinal analysis for a single branch run (consumes session health only)."""
    harness_issues = tuple(sorted(_issues_from_session_summary(summary), key=_issue_sort_key))
    analyzer_only = tuple(sorted(_analyzer_only_issues(spine, summary, player_texts_by_turn), key=_issue_sort_key))
    merged_issues = tuple(sorted(harness_issues + analyzer_only, key=_issue_sort_key))
    analyzer_codes = tuple(sorted({i.reason_code for i in analyzer_only}))
    merged_codes = _merge_reason_codes(summary.reason_codes, merged_issues)
    return N1LongitudinalContinuityReport(
        run_id=summary.run_id,
        scenario_spine_id=summary.scenario_spine_id,
        branch_id=summary.branch_id,
        base_reason_codes=summary.reason_codes,
        analyzer_reason_codes=analyzer_codes,
        merged_reason_codes=merged_codes,
        issues=merged_issues,
        aggregate_issue_counters=_aggregate_counters(merged_issues),
        severity_counters=_severity_counters(merged_issues),
    )


def analyze_n1_branch_longitudinal_continuity(
    *,
    spine: N1ScenarioSpineDefinition,
    branch_point: N1BranchPointDefinition,
    summaries: tuple[N1SessionHealthSummary, ...],
    comparison: N1BranchComparisonSummary | None = None,
) -> tuple[N1ContinuityIssue, ...]:
    """Cross-branch checks only: shared-fact preservation vs ``forgotten_anchor_flags``; divergence note.

    Distinct final scenes are informational (``N1_BRANCH_DIVERGENT_FINAL_SCENE_ID``). Contradictions
    against anchors that appear in every branch's shared-prefix observations are hard failures.
    """
    issues: list[N1ContinuityIssue] = []
    k = int(branch_point.shared_prefix_turn_count)
    anchors = tuple(sorted(spine.narrative_anchor_ids))

    def _prefix_established(anchor_id: str) -> bool:
        for s in summaries:
            obs = s.per_turn_observations
            if not obs:
                return False
            upto = min(k, len(obs))
            if not any(obs[t].anchor_hits.get(anchor_id) for t in range(upto)):
                return False
        return True

    shared_facts = tuple(a for a in anchors if _prefix_established(a))
    for s in sorted(summaries, key=lambda x: x.branch_id):
        for aid in shared_facts:
            if s.forgotten_anchor_flags.get(aid):
                code = f"{N1_REASON_BRANCH_SHARED_FACT_VIOLATION}:{aid}"
                issues.append(
                    N1ContinuityIssue(
                        severity="hard",
                        category="branch_divergence",
                        reason_code=code,
                        first_seen_turn=None,
                        last_seen_turn=None,
                        detail=f"branch={s.branch_id}",
                    )
                )

    if comparison is not None and comparison.divergence_detected:
        issues.append(
            N1ContinuityIssue(
                severity="info",
                category="branch_divergence",
                reason_code=N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,
                first_seen_turn=None,
                last_seen_turn=None,
                detail="distinct_final_scene_ids_allowed",
            )
        )

    return tuple(sorted(issues, key=_issue_sort_key))


def continuity_report_to_jsonable(report: N1LongitudinalContinuityReport) -> dict[str, Any]:
    """Stable JSON-shaped dict for tests and logs (separate from session-health artifact)."""
    issues = [
        {
            "category": i.category,
            "detail": i.detail,
            "first_seen_turn": i.first_seen_turn,
            "last_seen_turn": i.last_seen_turn,
            "reason_code": i.reason_code,
            "severity": i.severity,
        }
        for i in report.issues
    ]
    payload = {
        "aggregate_issue_counters": dict(sorted(report.aggregate_issue_counters.items(), key=lambda kv: kv[0])),
        "analyzer_reason_codes": list(report.analyzer_reason_codes),
        "base_reason_codes": list(report.base_reason_codes),
        "branch_id": report.branch_id,
        "issues": issues,
        "merged_reason_codes": list(report.merged_reason_codes),
        "run_id": report.run_id,
        "scenario_spine_id": report.scenario_spine_id,
        "severity_counters": dict(sorted(report.severity_counters.items(), key=lambda kv: kv[0])),
    }
    return dict(sorted(payload.items(), key=lambda kv: kv[0]))


def deterministic_continuity_report_json(report: N1LongitudinalContinuityReport) -> str:
    """Compact JSON matching other N1 CLI artifacts (recursive key sort)."""
    return deterministic_json_dumps(continuity_report_to_jsonable(report))
