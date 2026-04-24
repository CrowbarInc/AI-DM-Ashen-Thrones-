"""Deterministic offline health evaluation for Scenario-Spine sessions (no API calls)."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from game.scenario_spine import ScenarioSpine, scenario_spine_from_dict

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_scenario_spine_session(
    spine: Mapping[str, Any] | ScenarioSpine,
    branch_id: str,
    turns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate recorded turns against a spine; result is JSON-serializable."""
    model = _coerce_spine(spine)
    resolved_branch = _resolve_branch_id(model, branch_id)
    if resolved_branch is None:
        return _error_result(
            model.spine_id,
            branch_id,
            turns,
            f"unknown_branch_id:{branch_id}",
        )
    norm_turns = [_normalize_turn_row(i, t) for i, t in enumerate(turns)]
    ctx = _EvalContext(
        spine=model,
        branch_id=resolved_branch,
        turns=tuple(norm_turns),
    )
    return ctx.run()


# ---------------------------------------------------------------------------
# Spine / turn normalization
# ---------------------------------------------------------------------------


_BRANCH_ALIASES: dict[str, str] = {
    "social_investigation": "branch_social_inquiry",
    "direct_intrusion": "branch_direct_intrusion",
    "cautious_observation": "branch_cautious_observe",
}

def _coerce_spine(spine: Mapping[str, Any] | ScenarioSpine) -> ScenarioSpine:
    if isinstance(spine, ScenarioSpine):
        return spine
    if not isinstance(spine, Mapping):
        msg = "spine must be a Mapping or ScenarioSpine"
        raise TypeError(msg)
    return scenario_spine_from_dict(spine)


def _resolve_branch_id(spine: ScenarioSpine, branch_id: str) -> str | None:
    bid = str(branch_id).strip()
    ids = {b.branch_id for b in spine.branches}
    if bid in ids:
        return bid
    mapped = _BRANCH_ALIASES.get(bid)
    if mapped and mapped in ids:
        return mapped
    return None


def _normalize_turn_row(turn_index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    gm = row.get("gm_text")
    if gm is None or (isinstance(gm, str) and not gm.strip()):
        alt = row.get("gm_output")
        gm = alt if isinstance(alt, str) else ""
    gm_s = str(gm) if gm is not None else ""

    player = row.get("player_prompt")
    if player is None or (isinstance(player, str) and not player.strip()):
        pt = row.get("player_text")
        player = pt if isinstance(pt, str) else ""
    player_s = str(player) if player is not None else ""

    tid = row.get("turn_id")
    if tid is None:
        tid = row.get("turn_index")
    tid_s = str(tid) if tid is not None else f"idx_{turn_index}"

    api_ok = row.get("api_ok")
    if api_ok is None:
        api_ok = True
    elif not isinstance(api_ok, bool):
        api_ok = bool(api_ok)

    meta = row.get("meta")
    meta_out: dict[str, Any] | None
    if isinstance(meta, Mapping):
        meta_out = {str(k): meta[k] for k in sorted(meta, key=str)}
    else:
        meta_out = None

    return {
        "turn_index": int(turn_index),
        "turn_id": tid_s,
        "player_text": player_s,
        "gm_text": gm_s,
        "api_ok": api_ok,
        "meta": meta_out,
    }


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _concat_gm(turns: Sequence[Mapping[str, Any]], end_inclusive: int) -> str:
    parts: list[str] = []
    for t in turns:
        if t["turn_index"] <= end_inclusive:
            parts.append(str(t["gm_text"]))
    return "\n".join(parts)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def _error_result(
    scenario_id: str,
    branch_id: str,
    turns: Sequence[Mapping[str, Any]],
    detail: str,
) -> dict[str, Any]:
    axis_shell = {
        "passed": False,
        "failure_codes": ["eval_aborted"],
        "warning_codes": [],
    }
    return _jsonable(
        {
            "schema_version": 1,
            "scenario_id": scenario_id,
            "branch_id": branch_id,
            "turn_count": len(turns),
            "session_health": {
                "overall_passed": False,
                "score": 0,
                "classification": "failed",
            },
            "axes": {
                "state_continuity": axis_shell,
                "referent_persistence": axis_shell,
                "world_project_progression": axis_shell,
                "narrative_grounding": axis_shell,
                "branch_coherence": axis_shell,
            },
            "detected_failures": [
                {"axis": "session", "code": "unknown_branch_id", "detail": detail},
            ],
            "warnings": [],
            "checkpoint_results": [],
        },
    )


def _compute_score(
    failures: Sequence[Mapping[str, Any]],
    warnings: Sequence[Mapping[str, Any]],
    *,
    api_majority: bool,
) -> int:
    score = 100
    score -= 24 * len(failures)
    score -= 7 * len(warnings)
    if api_majority:
        score -= 30
    return max(0, min(100, score))


def _classify(
    *,
    failed_axes: int,
    failure_count: int,
    warning_count: int,
    score: int,
    api_majority: bool,
) -> str:
    if api_majority or failed_axes >= 2:
        return "failed"
    if failed_axes == 1:
        return "degraded"
    if failure_count > 0 and failed_axes == 0:
        return "failed"
    if score < 40:
        return "failed"
    if warning_count > 0:
        return "warning"
    return "clean"


# ---------------------------------------------------------------------------
# Heuristic banks (reason-coded, transparent)
# ---------------------------------------------------------------------------

_RESET_PHRASES: tuple[str, ...] = (
    "start fresh",
    "new campaign",
    "you arrive for the first time",
    "none of this has happened",
    "forget the previous scene",
)

_DEBUG_LEAK_MARKERS: tuple[str, ...] = (
    "system:",
    "developer instruction",
    "final_emission_gate",
    "trace_id",
    "validator failed",
)

def _looks_json_diagnostic_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 24:
        return False
    if s[0] != "{" or s[-1] != "}":
        return False
    if '"trace_id"' in s or '"schema_version"' in s or '"error"' in s:
        return True
    return s.count('"') >= 10

_REFERENT_UNKNOWN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwho\s+is\s+captain\s+thoran\b", re.I), "unknown_captain_thoran"),
    (re.compile(r"\bcaptain\s+thoran\b.*\b(who|what)\b", re.I), "captain_thoran_questioned_unknown"),
    (re.compile(r"\byou\s+have\s+not\s+seen\s+(the\s+)?notice\b", re.I), "notice_unknown_to_player"),
    (re.compile(r"\b(no|not\s+any)\s+such\s+clue\b", re.I), "clue_denied"),
    (re.compile(r"\bthere\s+is\s+no\s+notice\b", re.I), "notice_denied"),
    (re.compile(r"\bnever\s+heard\s+of\s+captain\s+thoran\b", re.I), "thoran_unknown_reputation"),
)

_PROGRESSION_CONTRADICTION: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno\s+missing\s+patrol\b", re.I),
    re.compile(r"\bpatrol\s+(returned|was\s+fine|never\s+left)\b", re.I),
    re.compile(r"\bfalse\s+alarm\b.*\bpatrol\b", re.I),
)

_GENERIC_FILLER_PHRASES: frozenset[str] = frozenset(
    {
        "the moment stretches.",
        "silence hangs heavy.",
        "you wait and watch.",
        "nothing obvious changes yet.",
        "the crowd shifts uneasily.",
    },
)


def _referent_keywords_for_anchor(anchor_id: str, label: str, description: str) -> frozenset[str]:
    keys: set[str] = set()
    for chunk in (anchor_id, label, description):
        for token in re.split(r"[^\w]+", chunk.lower()):
            if len(token) >= 4:
                keys.add(token)
    # Fixture-specific short stems still useful
    if "thor" in anchor_id.lower() or "thoran" in label.lower():
        keys.update({"thoran", "captain"})
    if "notice" in anchor_id.lower() or "notice" in label.lower():
        keys.update({"notice", "board", "posted"})
    if "muddy" in anchor_id.lower() or "foot" in description.lower():
        keys.update({"muddy", "footprint", "prints", "northwest"})
    if "ash" in anchor_id.lower() or "compact" in label.lower():
        keys.update({"ash", "compact", "census"})
    return frozenset(k for k in keys if len(k) >= 3)


def _text_has_any_keyword(norm: str, keywords: frozenset[str]) -> bool:
    return any(k in norm for k in keywords if len(k) >= 3)


def _continuity_match(norm: str, description: str) -> bool:
    d = _norm_text(description)
    # Pull substantive tokens from anchor description
    toks = [t for t in re.split(r"[^\w]+", d) if len(t) >= 4]
    hits = sum(1 for t in toks[:12] if t in norm)
    return hits >= 2 or (len(toks) == 1 and toks[0] in norm)


def _progression_keywords(anchor_id: str, description: str, summary: str) -> frozenset[str]:
    aid = anchor_id.lower()
    base = _norm_text(f"{description} {summary}")
    toks = {t for t in re.split(r"[^\w]+", base) if len(t) >= 4}
    if "prog_patrol_investigation_advances" in aid or "patrol" in aid:
        toks.update(
            {
                "patrol",
                "missing",
                "investigation",
                "route",
                "sighting",
                "clock",
                "rumor",
                "disappearance",
            },
        )
    if "prog_watch_tightens" in aid or "watch" in aid:
        toks.update(
            {
                "watch",
                "curfew",
                "gate",
                "security",
                "enforcement",
                "tighten",
                "escalat",
                "serjeant",
            },
        )
    return frozenset(toks)


# ---------------------------------------------------------------------------
# Evaluation context
# ---------------------------------------------------------------------------


class _EvalContext:
    def __init__(
        self,
        *,
        spine: ScenarioSpine,
        branch_id: str,
        turns: tuple[dict[str, Any], ...],
    ) -> None:
        self.spine = spine
        self.branch_id = branch_id
        self.turns = turns
        self.failures: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.checkpoint_results: list[dict[str, Any]] = []

    def add_failure(
        self,
        axis: str,
        code: str,
        detail: str,
        *,
        turn_index: int | None = None,
        anchor_id: str | None = None,
    ) -> None:
        item: dict[str, Any] = {"axis": axis, "code": code, "detail": detail}
        if turn_index is not None:
            item["turn_index"] = turn_index
        if anchor_id is not None:
            item["anchor_id"] = anchor_id
        self.failures.append(item)

    def add_warning(
        self,
        axis: str,
        code: str,
        detail: str,
        *,
        turn_index: int | None = None,
        anchor_id: str | None = None,
    ) -> None:
        item: dict[str, Any] = {"axis": axis, "code": code, "detail": detail}
        if turn_index is not None:
            item["turn_index"] = turn_index
        if anchor_id is not None:
            item["anchor_id"] = anchor_id
        self.warnings.append(item)

    def run(self) -> dict[str, Any]:
        n = len(self.turns)
        axes: dict[str, Any] = {
            "state_continuity": self._axis_state_continuity(),
            "referent_persistence": self._axis_referent_persistence(),
            "world_project_progression": self._axis_progression(),
            "narrative_grounding": self._axis_narrative_grounding(),
            "branch_coherence": self._axis_branch_coherence(),
        }
        self._build_checkpoint_results()

        api_failures = sum(1 for t in self.turns if not t["api_ok"])
        api_majority = n > 0 and api_failures > n // 2
        if api_majority:
            self.add_failure(
                "session",
                "api_failure_majority",
                f"{api_failures}/{n} turns report api_ok=false",
            )

        score = _compute_score(self.failures, self.warnings, api_majority=api_majority)
        failed_axes = sum(1 for a in axes.values() if not a["passed"])
        classification = _classify(
            failed_axes=failed_axes,
            failure_count=len(self.failures),
            warning_count=len(self.warnings),
            score=score,
            api_majority=api_majority,
        )
        overall_passed = classification in ("clean", "warning")

        session_health = {
            "overall_passed": overall_passed,
            "score": score,
            "classification": classification,
        }

        out: dict[str, Any] = {
            "schema_version": 1,
            "scenario_id": self.spine.spine_id,
            "branch_id": self.branch_id,
            "turn_count": n,
            "session_health": session_health,
            "axes": axes,
            "detected_failures": list(self.failures),
            "warnings": list(self.warnings),
            "checkpoint_results": list(self.checkpoint_results),
        }
        return _jsonable(out)


    def _axis_state_continuity(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        # Reset language after turn index >= 3 (1-based "after turn 3")
        for t in self.turns:
            if t["turn_index"] < 3:
                continue
            low = _norm_text(str(t["gm_text"]))
            for phrase in _RESET_PHRASES:
                if phrase in low:
                    self.add_failure(
                        "state_continuity",
                        "continuity_reset_language",
                        f"gm contains reset phrase {phrase!r}",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("continuity_reset_language")

        # Checkpoint windows: continuity anchors referenced should not vanish entirely in later windows
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = len(cps)
        if k and self.turns:
            for i, cp in enumerate(cps):
                end_i = max(0, (i + 1) * len(self.turns) // k - 1)
                text_i = _norm_text(_concat_gm(self.turns, end_i))
                weak_ids: list[str] = []
                for rid in cp.referenced_anchor_ids:
                    ca = next((a for a in self.spine.continuity_anchors if a.anchor_id == rid), None)
                    if ca is None:
                        continue
                    if not _continuity_match(text_i, ca.description):
                        weak_ids.append(ca.anchor_id)
                if weak_ids:
                    self.add_warning(
                        "state_continuity",
                        "continuity_anchor_weak_by_checkpoint",
                        f"checkpoint {cp.checkpoint_id}: weak continuity for {sorted(weak_ids)}",
                    )
                    codes_warn.append("continuity_anchor_weak_by_checkpoint")

            # Vanishing: established in early window but absent in all turns after mid-session
            mid = len(self.turns) // 2
            last_start = max(0, len(self.turns) * 2 // 3)
            late_window = _norm_text(
                "\n".join(str(t["gm_text"]) for t in self.turns if t["turn_index"] >= last_start),
            )
            early = _norm_text(_concat_gm(self.turns, max(0, mid)))
            for ca in self.spine.continuity_anchors:
                if _continuity_match(early, ca.description) and not _continuity_match(late_window, ca.description):
                    self.add_warning(
                        "state_continuity",
                        "continuity_anchor_absent_late_window",
                        f"continuity {ca.anchor_id} present early but not in final third window",
                        anchor_id=ca.anchor_id,
                    )
                    codes_warn.append("continuity_anchor_absent_late_window")

        passed = not any(f["axis"] == "state_continuity" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_referent_persistence(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        if not self.turns:
            return {"passed": True, "failure_codes": [], "warning_codes": []}

        mid = max(1, len(self.turns) // 2)
        early_text = _norm_text(_concat_gm(self.turns, mid - 1))

        ref_map: dict[str, frozenset[str]] = {}
        for r in self.spine.referent_anchors:
            ref_map[r.anchor_id] = _referent_keywords_for_anchor(r.anchor_id, r.label, r.description)

        established: dict[str, bool] = {
            rid: _text_has_any_keyword(early_text, kws) for rid, kws in ref_map.items()
        }

        # Unknown-denial phrases only after the referent was established in prior GM text
        for t in self.turns:
            low = _norm_text(str(t["gm_text"]))
            prior = _norm_text(_concat_gm(self.turns, t["turn_index"] - 1)) if t["turn_index"] > 0 else ""
            established_prior = {
                rid: _text_has_any_keyword(prior, kws) for rid, kws in ref_map.items()
            }
            muddy_established = established_prior.get("ref_muddy_prints", False)
            for rx, pcode in _REFERENT_UNKNOWN_PATTERNS:
                if not rx.search(low):
                    continue
                if "thoran" in pcode and established_prior.get("ref_captain_thoran"):
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm treats Captain Thoran as unknown after establishment",
                        turn_index=t["turn_index"],
                        anchor_id="ref_captain_thoran",
                    )
                    codes_fail.append(pcode)
                if "notice" in pcode and any(
                    established_prior.get(aid) for aid in ref_map if "notice" in aid.lower()
                ):
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm denies notice after it was established",
                        turn_index=t["turn_index"],
                        anchor_id="ref_notice_board",
                    )
                    codes_fail.append(pcode)
                if pcode == "clue_denied" and muddy_established:
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm denies a clue after muddy-prints referent was established",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append(pcode)

        # Required referents from checkpoints
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        last_start = max(0, len(self.turns) * 2 // 3)
        late_window = _norm_text(
            "\n".join(str(t["gm_text"]) for t in self.turns if t["turn_index"] >= last_start),
        )
        required_ids: set[str] = set()
        for cp in cps:
            for rid in cp.referenced_anchor_ids:
                if any(r.anchor_id == rid for r in self.spine.referent_anchors):
                    required_ids.add(rid)

        for rid in sorted(required_ids):
            kws = ref_map.get(rid, frozenset())
            if not kws:
                continue
            if _text_has_any_keyword(early_text, kws) and not _text_has_any_keyword(late_window, kws):
                self.add_warning(
                    "referent_persistence",
                    "referent_absent_late_window",
                    f"required referent {rid} not present in final third gm window",
                    anchor_id=rid,
                )
                codes_warn.append("referent_absent_late_window")

        passed = not any(f["axis"] == "referent_persistence" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_progression(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        n = len(self.turns)

        prog_by_id = {p.anchor_id: p for p in self.spine.progression_anchors}

        for i, cp in enumerate(cps):
            end_i = max(0, (i + 1) * n // k - 1) if n else 0
            chunk = _norm_text(_concat_gm(self.turns, end_i))
            for rid in cp.referenced_anchor_ids:
                prog = prog_by_id.get(rid)
                if prog is None:
                    continue
                kws = _progression_keywords(prog.anchor_id, prog.description, prog.expected_change_summary)
                if not _text_has_any_keyword(chunk, kws):
                    self.add_failure(
                        "world_project_progression",
                        "progression_missing_by_checkpoint",
                        f"{prog.anchor_id} not evidenced by checkpoint {cp.checkpoint_id} window",
                        anchor_id=prog.anchor_id,
                    )
                    codes_fail.append("progression_missing_by_checkpoint")

        # Contradiction after positive signal
        full = _norm_text(_concat_gm(self.turns, n - 1 if n else 0))
        for prog in self.spine.progression_anchors:
            kws = _progression_keywords(prog.anchor_id, prog.description, prog.expected_change_summary)
            if not _text_has_any_keyword(full, kws):
                continue
            for rx in _PROGRESSION_CONTRADICTION:
                if rx.search(full):
                    self.add_warning(
                        "world_project_progression",
                        "progression_contradicted",
                        f"progression for {prog.anchor_id} later contradicted",
                        anchor_id=prog.anchor_id,
                    )
                    codes_warn.append("progression_contradicted")
                    break

        passed = not any(f["axis"] == "world_project_progression" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_narrative_grounding(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        for t in self.turns:
            raw = str(t["gm_text"])
            low = raw.lower()
            for marker in _DEBUG_LEAK_MARKERS:
                if marker in low:
                    self.add_failure(
                        "narrative_grounding",
                        "debug_or_system_leak",
                        f"gm contains marker {marker!r}",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("debug_or_system_leak")
            for line in raw.splitlines():
                if _looks_json_diagnostic_line(line):
                    self.add_failure(
                        "narrative_grounding",
                        "json_diagnostic_dump",
                        "gm line resembles raw JSON diagnostic",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("json_diagnostic_dump")

        # Repeated generic filler across long tail
        if len(self.turns) >= 12:
            low_lines = [_norm_text(str(t["gm_text"])) for t in self.turns]
            filler_hits = sum(1 for ln in low_lines if ln in _GENERIC_FILLER_PHRASES)
            if filler_hits >= max(6, len(self.turns) // 3):
                self.add_warning(
                    "narrative_grounding",
                    "repeated_generic_filler",
                    "high count of generic filler lines across session",
                )
                codes_warn.append("repeated_generic_filler")

        passed = not any(f["axis"] == "narrative_grounding" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_branch_coherence(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        by_branch = {b.branch_id: b for b in self.spine.branches}
        selected = by_branch.get(self.branch_id)
        if selected is None:
            return {"passed": True, "failure_codes": [], "warning_codes": []}

        selected_prompts = {_norm_text(t.player_prompt) for t in selected.turns}
        signatures: list[str] = []
        for bid, br in by_branch.items():
            if bid == self.branch_id:
                continue
            for t in br.turns:
                p = _norm_text(t.player_prompt)
                if len(p) < 12:
                    continue
                if p not in selected_prompts:
                    signatures.append(p)

        combined = _norm_text(_concat_gm(self.turns, len(self.turns) - 1))
        for sig in signatures:
            if len(sig) < 24:
                continue
            # Long distinctive substring from another branch's scripted prompt
            if sig in combined or (len(sig) > 40 and sig[:40] in combined):
                self.add_failure(
                    "branch_coherence",
                    "foreign_branch_prompt_echo",
                    "gm echoes another branch's scripted player beat",
                )
                codes_fail.append("foreign_branch_prompt_echo")
                break

        passed = not any(f["axis"] == "branch_coherence" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _build_checkpoint_results(self) -> None:
        self.checkpoint_results.clear()
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        n = len(self.turns)
        ref_map = {
            r.anchor_id: _referent_keywords_for_anchor(r.anchor_id, r.label, r.description)
            for r in self.spine.referent_anchors
        }
        cont_map = {a.anchor_id: a for a in self.spine.continuity_anchors}
        prog_map = {p.anchor_id: p for p in self.spine.progression_anchors}
        for i, cp in enumerate(cps):
            end_i = max(0, (i + 1) * n // k - 1) if n else 0
            text = _norm_text(_concat_gm(self.turns, end_i))
            issues: list[dict[str, Any]] = []
            for rid in cp.referenced_anchor_ids:
                if rid in prog_map:
                    pr = prog_map[rid]
                    kws = _progression_keywords(pr.anchor_id, pr.description, pr.expected_change_summary)
                    if not _text_has_any_keyword(text, kws):
                        issues.append(
                            {"code": "progression_missing", "anchor_id": rid, "detail": "keywords not found in window"},
                        )
                elif rid in cont_map:
                    if not _continuity_match(text, cont_map[rid].description):
                        issues.append(
                            {"code": "continuity_weak", "anchor_id": rid, "detail": "description tokens sparse in window"},
                        )
                elif rid in ref_map:
                    if not _text_has_any_keyword(text, ref_map[rid]):
                        issues.append(
                            {"code": "referent_weak", "anchor_id": rid, "detail": "referent keywords not found in window"},
                        )
            self.checkpoint_results.append(
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "label": cp.label,
                    "passed": len(issues) == 0,
                    "window_end_turn_index": end_i,
                    "referenced_anchor_ids": list(cp.referenced_anchor_ids),
                    "issues": issues,
                },
            )
