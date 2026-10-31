"""Deterministic scenario-spine definitions for long-session validation (schema only).

No live model calls, no session harness — pure data structures, serialization, and
definition validation suitable for fixtures and offline contract tests.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioTurn:
    """One scripted player beat within a branch."""

    turn_id: str
    player_prompt: str
    notes: str | None = None


@dataclass(frozen=True)
class ScenarioBranch:
    """A branchable player decision path as an ordered list of turns."""

    branch_id: str
    label: str
    turns: tuple[ScenarioTurn, ...]
    notes: str | None = None


@dataclass(frozen=True)
class ContinuityAnchor:
    """Diegetic continuity the session is expected to preserve (location, cast, etc.)."""

    anchor_id: str
    anchor_kind: str
    description: str


@dataclass(frozen=True)
class ReferentAnchor:
    """Stable referents the narration should keep coherent (objects, people, clues)."""

    anchor_id: str
    label: str
    description: str


@dataclass(frozen=True)
class ProgressionAnchor:
    """Expected world or project progression along a path."""

    anchor_id: str
    description: str
    expected_change_summary: str = ""


@dataclass(frozen=True)
class ScenarioCheckpoint:
    """Validation checkpoint tying evaluation to known anchors."""

    checkpoint_id: str
    label: str
    referenced_anchor_ids: tuple[str, ...]
    notes: str | None = None


@dataclass(frozen=True)
class ScenarioSpine:
    """Full spine: fixed start, anchors, branches, and checkpoints."""

    spine_id: str
    fixed_start_state: dict[str, Any]
    branches: tuple[ScenarioBranch, ...]
    continuity_anchors: tuple[ContinuityAnchor, ...] = ()
    referent_anchors: tuple[ReferentAnchor, ...] = ()
    progression_anchors: tuple[ProgressionAnchor, ...] = ()
    checkpoints: tuple[ScenarioCheckpoint, ...] = ()
    title: str = ""
    smoke_only: bool = False
    notes: str | None = None


# ---------------------------------------------------------------------------
# Stable JSON-oriented dict helpers
# ---------------------------------------------------------------------------


def _sort_mapping_keys(value: Any) -> Any:
    """Recursively sort dict keys for deterministic serialization."""
    if isinstance(value, dict):
        return {k: _sort_mapping_keys(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_sort_mapping_keys(v) for v in value]
    return value


def _turn_to_dict(turn: ScenarioTurn) -> dict[str, Any]:
    d: dict[str, Any] = {
        "turn_id": turn.turn_id,
        "player_prompt": turn.player_prompt,
    }
    if turn.notes is not None:
        d["notes"] = turn.notes
    return dict(sorted(d.items()))


def _branch_to_dict(branch: ScenarioBranch) -> dict[str, Any]:
    d: dict[str, Any] = {
        "branch_id": branch.branch_id,
        "label": branch.label,
        "turns": [_turn_to_dict(t) for t in branch.turns],
    }
    if branch.notes is not None:
        d["notes"] = branch.notes
    return dict(sorted(d.items()))


def _continuity_to_dict(a: ContinuityAnchor) -> dict[str, Any]:
    return dict(
        sorted(
            {
                "anchor_id": a.anchor_id,
                "anchor_kind": a.anchor_kind,
                "description": a.description,
            }.items(),
        ),
    )


def _referent_to_dict(a: ReferentAnchor) -> dict[str, Any]:
    return dict(
        sorted(
            {
                "anchor_id": a.anchor_id,
                "label": a.label,
                "description": a.description,
            }.items(),
        ),
    )


def _progression_to_dict(a: ProgressionAnchor) -> dict[str, Any]:
    d: dict[str, Any] = {
        "anchor_id": a.anchor_id,
        "description": a.description,
    }
    if a.expected_change_summary:
        d["expected_change_summary"] = a.expected_change_summary
    return dict(sorted(d.items()))


def _checkpoint_to_dict(c: ScenarioCheckpoint) -> dict[str, Any]:
    d: dict[str, Any] = {
        "checkpoint_id": c.checkpoint_id,
        "label": c.label,
        "referenced_anchor_ids": list(c.referenced_anchor_ids),
    }
    if c.notes is not None:
        d["notes"] = c.notes
    return dict(sorted(d.items()))


def scenario_spine_to_dict(spine: ScenarioSpine) -> dict[str, Any]:
    """Serialize a spine to a JSON-friendly dict with stable key and collection order."""
    body: dict[str, Any] = {
        "spine_id": spine.spine_id,
        "title": spine.title,
        "smoke_only": spine.smoke_only,
        "fixed_start_state": _sort_mapping_keys(dict(spine.fixed_start_state)),
        "continuity_anchors": [_continuity_to_dict(a) for a in sorted(spine.continuity_anchors, key=lambda x: x.anchor_id)],
        "referent_anchors": [_referent_to_dict(a) for a in sorted(spine.referent_anchors, key=lambda x: x.anchor_id)],
        "progression_anchors": [_progression_to_dict(a) for a in sorted(spine.progression_anchors, key=lambda x: x.anchor_id)],
        "branches": [_branch_to_dict(b) for b in sorted(spine.branches, key=lambda x: x.branch_id)],
        "checkpoints": [_checkpoint_to_dict(c) for c in sorted(spine.checkpoints, key=lambda x: x.checkpoint_id)],
    }
    if spine.notes is not None:
        body["notes"] = spine.notes
    return dict(sorted(body.items()))


def _clean_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field} must be a non-empty string"
        raise ValueError(msg)
    return value.strip()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def scenario_turn_from_dict(raw: Mapping[str, Any]) -> ScenarioTurn:
    if not isinstance(raw, Mapping):
        msg = "turn must be an object"
        raise TypeError(msg)
    return ScenarioTurn(
        turn_id=_clean_str(raw.get("turn_id"), field="turn.turn_id"),
        player_prompt=_clean_str(raw.get("player_prompt"), field="turn.player_prompt"),
        notes=_optional_str(raw.get("notes")),
    )


def scenario_branch_from_dict(raw: Mapping[str, Any]) -> ScenarioBranch:
    if not isinstance(raw, Mapping):
        msg = "branch must be an object"
        raise TypeError(msg)
    turns_raw = raw.get("turns")
    if not isinstance(turns_raw, list):
        msg = "branch.turns must be a list"
        raise TypeError(msg)
    turns = tuple(scenario_turn_from_dict(t) for t in turns_raw)
    return ScenarioBranch(
        branch_id=_clean_str(raw.get("branch_id"), field="branch.branch_id"),
        label=_clean_str(raw.get("label"), field="branch.label"),
        turns=turns,
        notes=_optional_str(raw.get("notes")),
    )


def continuity_anchor_from_dict(raw: Mapping[str, Any]) -> ContinuityAnchor:
    if not isinstance(raw, Mapping):
        msg = "continuity anchor must be an object"
        raise TypeError(msg)
    return ContinuityAnchor(
        anchor_id=_clean_str(raw.get("anchor_id"), field="continuity.anchor_id"),
        anchor_kind=_clean_str(raw.get("anchor_kind"), field="continuity.anchor_kind"),
        description=_clean_str(raw.get("description"), field="continuity.description"),
    )


def referent_anchor_from_dict(raw: Mapping[str, Any]) -> ReferentAnchor:
    if not isinstance(raw, Mapping):
        msg = "referent anchor must be an object"
        raise TypeError(msg)
    return ReferentAnchor(
        anchor_id=_clean_str(raw.get("anchor_id"), field="referent.anchor_id"),
        label=_clean_str(raw.get("label"), field="referent.label"),
        description=_clean_str(raw.get("description"), field="referent.description"),
    )


def progression_anchor_from_dict(raw: Mapping[str, Any]) -> ProgressionAnchor:
    if not isinstance(raw, Mapping):
        msg = "progression anchor must be an object"
        raise TypeError(msg)
    ecs = raw.get("expected_change_summary")
    ecs_s = "" if ecs is None else str(ecs).strip()
    return ProgressionAnchor(
        anchor_id=_clean_str(raw.get("anchor_id"), field="progression.anchor_id"),
        description=_clean_str(raw.get("description"), field="progression.description"),
        expected_change_summary=ecs_s,
    )


def scenario_checkpoint_from_dict(raw: Mapping[str, Any]) -> ScenarioCheckpoint:
    if not isinstance(raw, Mapping):
        msg = "checkpoint must be an object"
        raise TypeError(msg)
    refs_raw = raw.get("referenced_anchor_ids")
    if not isinstance(refs_raw, list):
        msg = "checkpoint.referenced_anchor_ids must be a list"
        raise TypeError(msg)
    refs: list[str] = []
    for item in refs_raw:
        refs.append(_clean_str(item, field="checkpoint.referenced_anchor_ids[]"))
    return ScenarioCheckpoint(
        checkpoint_id=_clean_str(raw.get("checkpoint_id"), field="checkpoint.checkpoint_id"),
        label=_clean_str(raw.get("label"), field="checkpoint.label"),
        referenced_anchor_ids=tuple(refs),
        notes=_optional_str(raw.get("notes")),
    )


def scenario_spine_from_dict(raw: Mapping[str, Any]) -> ScenarioSpine:
    """Deserialize a spine from JSON-compatible mappings (unknown top-level keys ignored)."""
    if not isinstance(raw, Mapping):
        msg = "spine root must be an object"
        raise TypeError(msg)
    fss = raw.get("fixed_start_state")
    if not isinstance(fss, dict):
        msg = "fixed_start_state must be an object"
        raise TypeError(msg)

    branches_raw = raw.get("branches")
    if not isinstance(branches_raw, list):
        msg = "branches must be a list"
        raise TypeError(msg)
    branches = tuple(scenario_branch_from_dict(b) for b in branches_raw)

    def _list_of(name: str, key: str, factory: Any) -> tuple[Any, ...]:
        seq = raw.get(key)
        if seq is None:
            return ()
        if not isinstance(seq, list):
            msg = f"{name} must be a list or omitted"
            raise TypeError(msg)
        return tuple(factory(x) for x in seq)

    continuity = _list_of("continuity_anchors", "continuity_anchors", continuity_anchor_from_dict)
    referents = _list_of("referent_anchors", "referent_anchors", referent_anchor_from_dict)
    progression = _list_of("progression_anchors", "progression_anchors", progression_anchor_from_dict)
    checkpoints = _list_of("checkpoints", "checkpoints", scenario_checkpoint_from_dict)

    title = raw.get("title")
    title_s = "" if title is None else str(title).strip()

    smoke = raw.get("smoke_only", False)
    if not isinstance(smoke, bool):
        msg = "smoke_only must be a boolean"
        raise TypeError(msg)

    return ScenarioSpine(
        spine_id=_clean_str(raw.get("spine_id"), field="spine_id"),
        title=title_s,
        smoke_only=bool(smoke),
        fixed_start_state=deepcopy(fss),
        branches=branches,
        continuity_anchors=continuity,
        referent_anchors=referents,
        progression_anchors=progression,
        checkpoints=checkpoints,
        notes=_optional_str(raw.get("notes")),
    )


# ---------------------------------------------------------------------------
# Definition validation
# ---------------------------------------------------------------------------


def validate_scenario_spine_definition(spine: ScenarioSpine) -> list[str]:
    """Return a sorted list of human-readable errors; empty means the definition is valid."""
    errors: list[str] = []

    if not isinstance(spine.fixed_start_state, dict) or len(spine.fixed_start_state) == 0:
        errors.append("scenario_spine:fixed_start_state must be a non-empty object")

    if len(spine.branches) == 0:
        errors.append("scenario_spine:branches must be non-empty")

    seen_branch_ids: set[str] = set()
    for branch in spine.branches:
        if branch.branch_id in seen_branch_ids:
            errors.append(f"scenario_spine:duplicate branch_id {branch.branch_id!r}")
        seen_branch_ids.add(branch.branch_id)

        seen_turn: set[str] = set()
        for turn in branch.turns:
            if turn.turn_id in seen_turn:
                errors.append(
                    f"scenario_spine:duplicate turn_id {turn.turn_id!r} within branch {branch.branch_id!r}",
                )
            seen_turn.add(turn.turn_id)

    anchor_ids: set[str] = set()
    for a in (*spine.continuity_anchors, *spine.referent_anchors, *spine.progression_anchors):
        if a.anchor_id in anchor_ids:
            errors.append(f"scenario_spine:duplicate anchor_id {a.anchor_id!r}")
        anchor_ids.add(a.anchor_id)

    for cp in spine.checkpoints:
        for rid in cp.referenced_anchor_ids:
            if rid not in anchor_ids:
                errors.append(
                    f"scenario_spine:checkpoint {cp.checkpoint_id!r} references unknown anchor_id {rid!r}",
                )

    if not spine.smoke_only:
        longest = max((len(b.turns) for b in spine.branches), default=0)
        if longest < 20:
            errors.append(
                "scenario_spine:at least one branch must define >= 20 turns unless smoke_only is true",
            )

    return sorted(errors)
