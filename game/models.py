"""Request/response models and standardized engine result schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def make_check_request(
    *,
    requires_check: bool,
    check_type: Optional[str] = None,
    skill: Optional[str] = None,
    difficulty: Optional[int] = None,
    reason: Optional[str] = None,
    player_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a normalized engine-owned check request payload."""
    return {
        "requires_check": bool(requires_check),
        "check_type": str(check_type or skill or "").strip() or None,
        "skill": str(skill or check_type or "").strip() or None,
        "difficulty": int(difficulty) if isinstance(difficulty, (int, float)) else None,
        "reason": str(reason or "").strip() or None,
        "player_prompt": str(player_prompt or "").strip() or None,
    }


# -----------------------------------------------------------------------------
# Exploration Engine Result (standardized resolution schema)
# -----------------------------------------------------------------------------
# Canonical shape returned by resolve_exploration_action. All exploration action
# types (observe, investigate, interact, discover_clue, scene_transition, custom)
# use this schema so downstream code can rely on consistent keys.
#
# Backward compatibility: the dict form is used everywhere; existing callers
# using resolution.get("kind"), resolution.get("action_id"), etc. continue to work.
# -----------------------------------------------------------------------------


@dataclass
class ExplorationEngineResult:
    """Standardized engine result for exploration resolution. All resolve_exploration_action
    outcomes use this schema. Use to_dict() for JSON/log compatibility."""

    kind: str  # scene_transition | observe | investigate | interact | discover_clue | custom
    action_id: str
    label: str
    prompt: str
    success: Optional[bool]  # True/False when applicable; None for N/A
    resolved_transition: bool
    target_scene_id: Optional[str]
    clue_id: Optional[str]
    discovered_clues: List[str] = field(default_factory=list)  # clue texts; discover_clue populates
    world_updates: Optional[Dict[str, Any]] = None
    state_changes: Dict[str, Any] = field(default_factory=dict)  # e.g. scene_changed, clue_revealed
    hint: str = ""
    originating_scene_id: Optional[str] = None
    interactable_id: Optional[str] = None  # for discover_clue
    clue_text: Optional[str] = None  # for discover_clue (player-facing text)
    metadata: Dict[str, Any] = field(default_factory=dict)  # extensible debug metadata
    skill_check: Optional[Dict[str, Any]] = None  # engine-resolved roll result when applicable

    def to_dict(self) -> Dict[str, Any]:
        """Return dict suitable for API/log consumers. Preserves backward-compat keys."""
        d: Dict[str, Any] = {
            "kind": self.kind,
            "action_id": self.action_id,
            "label": self.label,
            "prompt": self.prompt,
            "success": self.success,
            "resolved_transition": self.resolved_transition,
            "target_scene_id": self.target_scene_id,
            "clue_id": self.clue_id,
            "discovered_clues": list(self.discovered_clues) if self.discovered_clues else [],
            "world_updates": dict(self.world_updates) if self.world_updates else None,
            "state_changes": dict(self.state_changes) if self.state_changes else {},
            "hint": self.hint,
        }
        if self.originating_scene_id is not None:
            d["originating_scene_id"] = self.originating_scene_id
        if self.interactable_id is not None:
            d["interactable_id"] = self.interactable_id
        if self.clue_text is not None:
            d["clue_text"] = self.clue_text
        if self.skill_check is not None:
            d["skill_check"] = dict(self.skill_check)
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d


def exploration_result_to_dict(r: ExplorationEngineResult) -> Dict[str, Any]:
    """Convert ExplorationEngineResult to canonical dict."""
    return r.to_dict()


# -----------------------------------------------------------------------------
# Combat Engine Result (standardized resolution schema, aligned with exploration)
# -----------------------------------------------------------------------------
# Canonical shape returned by combat resolvers. Same top-level contract as
# exploration (kind, action_id, label, prompt, success, hint, etc.) with
# combat-specific data in the "combat" sub-payload.
#
# Combat kinds: initiative | attack | spell | skill_check | enemy_attack |
#               enemy_turn_skipped | end_turn
# -----------------------------------------------------------------------------


@dataclass
class CombatEngineResult:
    """Standardized engine result for combat resolution. Same top-level shape as
    exploration; combat-specific data lives in the combat sub-payload."""

    kind: str  # initiative | attack | spell | skill_check | enemy_attack | enemy_turn_skipped | end_turn
    action_id: str  # attack_id, spell_id, skill_id, or "initiative", "end_turn", "enemy_attack"
    label: str
    prompt: str
    success: Optional[bool]  # hit/miss, save made/failed; None for initiative/end_turn
    hint: str = ""
    combat: Dict[str, Any] = field(default_factory=dict)  # combat-specific structured payload
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return dict with canonical engine-result contract. Includes backward-compat top-level keys."""
        d: Dict[str, Any] = {
            "kind": self.kind,
            "action_id": self.action_id,
            "label": self.label,
            "prompt": self.prompt,
            "success": self.success,
            "resolved_transition": False,
            "target_scene_id": None,
            "clue_id": None,
            "discovered_clues": [],
            "world_updates": None,
            "state_changes": {},
            "hint": self.hint,
            "combat": dict(self.combat),
        }
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        # Backward compat: surface common combat keys at top-level for legacy callers
        c = self.combat
        if c.get("hit") is not None:
            d["hit"] = c["hit"]
        if c.get("damage_dealt") is not None:
            d["damage"] = c["damage_dealt"]
        if c.get("round") is not None:
            d["round"] = c["round"]
        if c.get("active_actor_id") is not None:
            d["active_actor_id"] = c["active_actor_id"]
        if c.get("order") is not None:
            d["order"] = c["order"]
        return d


def combat_result_to_dict(r: CombatEngineResult) -> Dict[str, Any]:
    """Convert CombatEngineResult to canonical dict."""
    return r.to_dict()


# -----------------------------------------------------------------------------
# Social Engine Result (standardized resolution schema, aligned with exploration/combat)
# -----------------------------------------------------------------------------
# Canonical shape returned by resolve_social_action. Same top-level contract as
# exploration/combat (kind, action_id, label, prompt, success, hint, etc.) with
# social-specific data in the "social" sub-payload.
#
# Social kinds: question | persuade | intimidate | deceive | barter | recruit | social_probe
# -----------------------------------------------------------------------------


@dataclass
class SocialEngineResult:
    """Standardized engine result for social resolution. Same top-level shape as
    exploration/combat; social-specific data lives in the social sub-payload."""

    kind: str  # question | persuade | intimidate | deceive | barter | recruit | social_probe
    action_id: str
    label: str
    prompt: str
    success: Optional[bool]  # True/False when skill check ran; None for question/social_probe
    resolved_transition: bool = False
    target_scene_id: Optional[str] = None
    clue_id: Optional[str] = None
    discovered_clues: List[str] = field(default_factory=list)
    world_updates: Optional[Dict[str, Any]] = None
    state_changes: Dict[str, Any] = field(default_factory=dict)
    hint: str = ""
    social: Dict[str, Any] = field(default_factory=dict)  # social-specific structured payload
    metadata: Dict[str, Any] = field(default_factory=dict)
    skill_check: Optional[Dict[str, Any]] = None  # engine-resolved roll result when applicable
    requires_check: bool = False
    check_request: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return dict with canonical engine-result contract."""
        d: Dict[str, Any] = {
            "kind": self.kind,
            "action_id": self.action_id,
            "label": self.label,
            "prompt": self.prompt,
            "success": self.success,
            "resolved_transition": self.resolved_transition,
            "target_scene_id": self.target_scene_id,
            "clue_id": self.clue_id,
            "discovered_clues": list(self.discovered_clues) if self.discovered_clues else [],
            "world_updates": dict(self.world_updates) if self.world_updates else None,
            "state_changes": dict(self.state_changes) if self.state_changes else {},
            "hint": self.hint,
            "social": dict(self.social),
            "requires_check": bool(self.requires_check),
        }
        if self.skill_check is not None:
            d["skill_check"] = dict(self.skill_check)
        if self.check_request is not None:
            d["check_request"] = dict(self.check_request)
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d


def social_result_to_dict(r: SocialEngineResult) -> Dict[str, Any]:
    """Convert SocialEngineResult to canonical dict."""
    return r.to_dict()


class ActionRequest(BaseModel):
    action_type: str
    actor_id: Optional[str] = None
    target_id: Optional[str] = None
    attack_id: Optional[str] = None
    skill_id: Optional[str] = None
    spell_id: Optional[str] = None
    intent: Optional[str] = None
    modifiers: List[str] = Field(default_factory=list)
    exploration_action: Optional[Dict[str, Any]] = None
    social_action: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    text: str


class CampaignUpdate(BaseModel):
    title: str
    premise: str
    tone: str
    player_character: str
    character_role: str = ''
    starting_context: str
    gm_guidance: List[str] = Field(default_factory=list)
    world_pressures: List[str] = Field(default_factory=list)
    environmental_threats: List[str] = Field(default_factory=list)
    magic_style: str = ''
    campaign_structure: str = ''
    long_term_goals: List[str] = Field(default_factory=list)


class SceneEnvelope(BaseModel):
    """Scene dict may include visible_facts, journal_seed_facts, discoverable_clues (default []), hidden_facts, and other keys."""
    scene: Dict[str, Any]


class ResponseModeUpdate(BaseModel):
    mode: str


class SnapshotCreateRequest(BaseModel):
    """Optional label for a new snapshot."""
    label: Optional[str] = None


# --- Objective 4 — runtime boundary helpers (schema_contracts adoption) ---

_ENGINE_RESOLUTION_WORLD_UPDATE_KEYS = frozenset({"set_flags", "increment_counters", "advance_clocks"})


def normalize_runtime_engine_result(raw: Any) -> Dict[str, Any]:
    """Normalize an engine resolution dict at API/GM boundaries (legacy spellings, unknown top-level keys)."""
    from game.schema_contracts import adapt_legacy_engine_result

    return adapt_legacy_engine_result(raw if isinstance(raw, dict) else {})


def normalize_runtime_world_updates(raw: Any) -> Dict[str, Any]:
    """Normalize inbound GM / mixed ``world_updates`` through ``adapt_legacy_world_update``."""
    from game.schema_contracts import adapt_legacy_world_update, normalize_world_update

    if not isinstance(raw, dict):
        return normalize_world_update(adapt_legacy_world_update({}))
    work = dict(raw)
    ae = work.get("append_events")
    if isinstance(ae, list):
        clipped: List[Any] = []
        for item in ae[:32]:
            if isinstance(item, str):
                s = item.strip()
                if not s:
                    continue
                clipped.append(s[:500])
            elif isinstance(item, dict):
                clipped.append(item)
        work["append_events"] = clipped
    return normalize_world_update(adapt_legacy_world_update(work))


def resolution_world_updates_use_engine_apply_only(wu: Any) -> bool:
    """True when ``world_updates`` is only ``set_flags`` / ``increment_counters`` / ``advance_clocks`` (engine fragment)."""
    if not isinstance(wu, dict) or not wu:
        return False
    return frozenset(wu.keys()) <= _ENGINE_RESOLUTION_WORLD_UPDATE_KEYS


def canonical_world_update_is_effectively_empty(normalized: Dict[str, Any]) -> bool:
    """True when a normalized world-update dict carries no apply-able or inspectable payload."""
    if not isinstance(normalized, dict):
        return True
    if normalized.get("append_events"):
        return False
    for k in ("flags_patch", "counters_patch", "clocks_patch", "clues_patch"):
        if normalized.get(k):
            return False
    if normalized.get("projects_patch") or normalized.get("npcs_patch") or normalized.get("leads_patch"):
        return False
    md = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
    if md.get("legacy_increment_counters") or md.get("legacy_advance_clocks"):
        return False
    if md.get("unknown_legacy_keys"):
        return False
    if md.get("legacy_rejected_counters"):
        return False
    if isinstance(md, dict) and md:
        return False
    return True


def apply_normalized_world_updates(
    world: Dict[str, Any],
    normalized: Dict[str, Any],
    *,
    session: Optional[Dict[str, Any]] = None,
    scene_id: Optional[str] = None,
) -> None:
    """Delegate to :func:`game.world.apply_normalized_world_updates` (canonical bundle application)."""
    from game.world import apply_normalized_world_updates as _apply_normalized_world_updates_world

    _apply_normalized_world_updates_world(world, normalized, session=session, scene_id=scene_id)
