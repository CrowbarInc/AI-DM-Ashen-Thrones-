"""Deterministic opening-scene **renderer helpers** from published (player-visible) scene slices.

Structural opening obligations (C1-A) are owned by :attr:`game.narrative_planning.build_narrative_plan`
as ``scene_opening`` on the Narrative Plan. This module curates **diegetic basis lines** and
instruction expansion for prompt assembly only — not a parallel opener authority alongside the plan.

Builds a small, inspectable opening payload for first-turn / opening narration prompts.
Does not read hidden facts, GM notes, or undiscoverable layers — callers must pass only
public scene fields and an existing narration_visibility snapshot for name grounding.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Set, Tuple

from game.narration_visibility import _normalize_visibility_text
from game.opening_visible_fact_selection import opening_fact_primary_category

# Title-cased role labels often mistaken for proper names — replace longer phrases first.
_ROLE_LABEL_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    ("The Tavern Runner", "A tavern runner"),
    ("A Tavern Runner", "A tavern runner"),
    ("The Drink Runner", "A drink runner"),
    ("The Guard Captain", "The guard captain"),
    ("The Captain Of The Guard", "The captain of the guard"),
    ("The Gate Sergeant", "The gate sergeant"),
    ("The Patrol Captain", "The patrol captain"),
    ("The Town Crier", "The town crier"),
    ("The Innkeeper", "The innkeeper"),
    ("The Barkeep", "The barkeep"),
    ("Tavern Runner", "a tavern runner"),
    ("Drink Runner", "a drink runner"),
    ("Guard Captain", "the guard captain"),
    ("Captain Of The Guard", "the captain of the guard"),
    ("Gate Sergeant", "the gate sergeant"),
    ("Patrol Captain", "the patrol captain"),
    ("Town Crier", "the town crier"),
    ("Innkeeper", "the innkeeper"),
    ("Bar Keep", "the barkeep"),
    ("Barkeep", "the barkeep"),
)
_ROLE_LABEL_REPLACEMENTS = tuple(
    sorted(_ROLE_LABEL_REPLACEMENTS, key=lambda kv: len(kv[0]), reverse=True)
)

# Premature backstage / system-summary flavor in visible_fact prose (normalized substring match).
_BACKSTAGE_DUMP_MARKERS: Tuple[str, ...] = (
    "who controls",
    "who knows what",
    "what faction",
    "vital information",
    "manages patrol",
    "patrol assignments",
    # Transcript-honest opening regressions (pseudo-briefing from role labels).
    "guard captain indicates",
    "tavern runner shouts",
    "backstage",
    "system summary",
    "engine state",
    "plot thread",
    "main quest",
)

_HONORIFIC_NAME_RE = re.compile(
    r"\b(?:Lord|Lady|Sir|Dame|Captain|Sergeant|Baron|Baroness|Count|Countess|Duke|Duchess)\s+([A-Z][a-z]+)\b"
)
_APPOSITIVE_NAME_RE = re.compile(r"\b([A-Z][a-z]{2,}),\s*the\s+(?:town\s+crier|merchant|guard|captain|sergeant)\b")

_UNCERTAINTY_MARKERS: Tuple[str, ...] = (
    "seems ",
    "seems to",
    "appears ",
    "might ",
    "perhaps ",
    "unclear",
    "uncertain",
    "subtle",
    "furtive",
)


def _mapping_str_list(m: Mapping[str, Any] | None, key: str) -> List[str]:
    raw = (m or {}).get(key)
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if isinstance(x, str) and str(x).strip()]


def allowed_grounded_proper_name_norms(visibility_contract: Mapping[str, Any] | None) -> Set[str]:
    """Lowercase normalized display tokens/phrases that may appear as proper names in openings."""
    out: Set[str] = set()
    vc = visibility_contract if isinstance(visibility_contract, Mapping) else {}
    for item in _mapping_str_list(vc, "visible_entity_names"):
        n = _normalize_visibility_text(item)
        if n:
            out.add(n)
    alias_map = vc.get("visible_entity_aliases")
    if isinstance(alias_map, dict):
        for k, vals in alias_map.items():
            if isinstance(k, str):
                nk = _normalize_visibility_text(k)
                if nk:
                    out.add(nk)
            if isinstance(vals, str):
                nv = _normalize_visibility_text(vals)
                if nv:
                    out.add(nv)
            elif isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str):
                        nv = _normalize_visibility_text(v)
                        if nv:
                            out.add(nv)
    return out


def _phrase_grounded(norm_phrase: str, allowed: Set[str]) -> bool:
    if not norm_phrase:
        return False
    if norm_phrase in allowed:
        return True
    for a in allowed:
        if not a:
            continue
        if norm_phrase in a or a in norm_phrase:
            return True
    tail = norm_phrase.rsplit(" ", 1)[-1]
    if len(tail) >= 4 and any(a.endswith(tail) or tail in a for a in allowed):
        return True
    return False


def _honorific_matches(text: str) -> List[str]:
    out: List[str] = []
    for m in _HONORIFIC_NAME_RE.finditer(text):
        full = m.group(0).strip()
        out.append(_normalize_visibility_text(full))
    m2 = _APPOSITIVE_NAME_RE.search(text)
    if m2:
        out.append(_normalize_visibility_text(m2.group(1)))
    return out


def _has_ungrounded_honorific_name(text: str, allowed: Set[str]) -> bool:
    for phrase in _honorific_matches(text):
        if phrase and not _phrase_grounded(phrase, allowed):
            return True
    return False


def _backstage_dump(norm: str) -> bool:
    return any(marker in norm for marker in _BACKSTAGE_DUMP_MARKERS)


def suppress_role_label_proper_name_leakage(line: str) -> str:
    """Replace title-cased role bigrams with natural lowercase phrasing (deterministic)."""
    s = " ".join(str(line or "").split())
    if not s:
        return s
    for title, spoken in _ROLE_LABEL_REPLACEMENTS:
        pattern = re.compile(rf"\b{re.escape(title)}\b", flags=re.IGNORECASE)
        s = pattern.sub(spoken, s)
    s = re.sub(r"\bThe the\b", "The", s, flags=re.IGNORECASE)
    s = re.sub(r"\bA a\b", "A", s, flags=re.IGNORECASE)
    s = re.sub(r"\bThe a\b", "A", s, flags=re.IGNORECASE)
    return s


def partition_opening_fact_categories(lines: Sequence[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Split lines into sensory/spatial (A+E), ambient/crowd (B), social motion (C), other (D)."""
    sensory: List[str] = []
    ambient: List[str] = []
    social: List[str] = []
    other: List[str] = []
    for raw in lines:
        if not isinstance(raw, str) or not raw.strip():
            continue
        norm = _normalize_visibility_text(raw)
        cat = opening_fact_primary_category(norm)
        if cat in ("A", "E"):
            sensory.append(raw.strip())
        elif cat == "B":
            ambient.append(raw.strip())
        elif cat == "C":
            social.append(raw.strip())
        else:
            other.append(raw.strip())
    return sensory, ambient, social, other


def build_opening_narration_obligations_payload(*, opening_mode: bool) -> Dict[str, Any]:
    """Machine-readable opening narration obligations for prompt assembly."""
    if not opening_mode:
        return {
            "opening_mode": False,
            "opener_style": None,
            "required_first_move": None,
            "preferred_diction": None,
        }
    return {
        "opening_mode": True,
        "opener_style": "scene_establishing",
        "required_first_move": {
            "sensory_or_spatial_details": {"min": 2, "max": 4},
            "ambient_social_signal_max": 1,
            "named_backstage_explanations": 0,
            "hidden_fact_assertions": 0,
        },
        "preferred_diction": {
            "unknown_people": "refer_by_visible_role_or_appearance_in_natural_language",
            "role_labels": "avoid_title_casing_role_labels_unless_actual_names",
            "first_paragraph": "externally_observable_only",
        },
    }


# Machine codes aligned with ``game.narrative_planning.DEFAULT_SCENE_OPENING_PROHIBITED_CONTENT_CODES``.
_PROHIBITED_OPENER_CODE_ORDER: Tuple[str, ...] = (
    "no_engine_role_label_as_proper_name",
    "no_unintroduced_offscene_npc_names",
    "no_backstage_plot_briefings",
    "no_hidden_gm_facts_as_immediate_perception",
    "no_unfounded_faction_control_claims",
)

_PROHIBITED_OPENER_LINE_BY_CODE: Dict[str, str] = {
    "no_engine_role_label_as_proper_name": (
        "Do not treat engine role labels as proper names (for example title-cased 'Tavern Runner', 'Guard Captain')."
    ),
    "no_unintroduced_offscene_npc_names": (
        "Do not name unseen or off-scene NPCs the player has not been introduced to through direct presence or clear address."
    ),
    "no_backstage_plot_briefings": (
        "Do not open with backstage plot summaries, faction strategy briefings, or omniscient knowledge claims."
    ),
    "no_hidden_gm_facts_as_immediate_perception": (
        "Do not narrate hidden GM notes, scene seeds, or privileged facts as immediate player perception."
    ),
    "no_unfounded_faction_control_claims": (
        "Do not assert who controls patrols, who secretly knows what, or what factions are doing unless that is directly visible or audible here and now."
    ),
}


def default_prohibited_opener_content() -> List[str]:
    """Static prohibitions shipped with every opening contract."""
    return prohibited_opener_lines_from_codes(list(_PROHIBITED_OPENER_CODE_ORDER))


def prohibited_opener_lines_from_codes(codes: Sequence[str]) -> List[str]:
    """Expand plan ``prohibited_content_codes`` into the legacy instruction strings (renderer-only)."""
    out: List[str] = []
    seen: Set[str] = set()
    for raw in codes:
        if not isinstance(raw, str):
            continue
        c = raw.strip()
        if not c or c in seen:
            continue
        seen.add(c)
        line = _PROHIBITED_OPENER_LINE_BY_CODE.get(c)
        if line:
            out.append(line)
    return out


def patch_opening_export_with_plan_scene_opening(
    opening_scene_export: MutableMapping[str, Any],
    *,
    scene_opening: Mapping[str, Any] | None,
) -> None:
    """When a bundled plan carries ``scene_opening``, align export prohibitions with plan codes (in-place)."""
    if not isinstance(opening_scene_export, MutableMapping):
        return
    if not opening_scene_export.get("opening_mode"):
        return
    if not isinstance(scene_opening, Mapping):
        return
    codes = scene_opening.get("prohibited_content_codes")
    if not isinstance(codes, list) or not codes:
        return
    contract = opening_scene_export.get("contract")
    if not isinstance(contract, MutableMapping):
        return
    contract["prohibited_opener_content"] = prohibited_opener_lines_from_codes(codes)


def _diegetic_uncertainty_hooks(lines: Sequence[str], *, cap: int = 2) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for raw in lines:
        if not isinstance(raw, str):
            continue
        norm = _normalize_visibility_text(raw)
        if not norm or norm in seen:
            continue
        if any(marker in norm for marker in _UNCERTAINTY_MARKERS):
            out.append(raw.strip())
            seen.add(norm)
        if len(out) >= cap:
            break
    return out


def validate_opening_scene_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Narrow deterministic pre-check for opening contract shape (not a full NIL layer)."""
    issues: List[str] = []
    basis = contract.get("narration_basis_visible_facts")
    if not isinstance(basis, list):
        issues.append("missing_narration_basis_visible_facts")
    else:
        for line in basis:
            if not isinstance(line, str):
                issues.append("non_string_basis_line")
                break
            n = _normalize_visibility_text(line)
            if _backstage_dump(n):
                issues.append("basis_contains_backstage_marker")
    anchors = contract.get("sensory_anchors")
    if isinstance(anchors, list) and len(anchors) < 1 and isinstance(basis, list) and len(basis) > 0:
        issues.append("sparse_sensory_anchors")
    return {"ok": not issues, "issues": issues}


def build_opening_scene_realization(
    *,
    public_scene: Mapping[str, Any] | None,
    curated_visible_fact_strings: Sequence[str],
    visibility_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Assemble opening contract + narration basis from published scene data only."""
    ps = public_scene if isinstance(public_scene, Mapping) else {}
    allowed = allowed_grounded_proper_name_norms(visibility_contract)

    ordered_input = [str(s).strip() for s in curated_visible_fact_strings if isinstance(s, str) and str(s).strip()]
    relaxed_no_backstage: List[str] = []
    strict_basis: List[str] = []
    for line in ordered_input:
        cleaned = suppress_role_label_proper_name_leakage(line)
        norm = _normalize_visibility_text(cleaned)
        if not norm or _backstage_dump(norm):
            continue
        relaxed_no_backstage.append(cleaned)
        if _has_ungrounded_honorific_name(cleaned, allowed):
            continue
        strict_basis.append(cleaned)

    if strict_basis:
        narration_basis = strict_basis
    elif any(_has_ungrounded_honorific_name(x, allowed) for x in relaxed_no_backstage):
        # Prefer omitting ungrounded proper-name lines over reverting to unfiltered curated facts.
        narration_basis = []
    else:
        narration_basis = list(relaxed_no_backstage)

    if not narration_basis and ordered_input and not relaxed_no_backstage:
        narration_basis = [
            suppress_role_label_proper_name_leakage(x)
            for x in ordered_input
            if _normalize_visibility_text(suppress_role_label_proper_name_leakage(x))
        ]

    sensory, ambient, social, other = partition_opening_fact_categories(narration_basis)
    # Prefer sensory establishment over notice-board affordances in the exported anchors list.
    sensory_anchors = list(sensory)
    if len(sensory_anchors) < 2:
        for bucket in (other, ambient, social):
            for item in bucket:
                if item not in sensory_anchors:
                    sensory_anchors.append(item)
                if len(sensory_anchors) >= 4:
                    break
            if len(sensory_anchors) >= 4:
                break

    ambient_motion = list(ambient)
    for item in social[:1]:
        if item not in ambient_motion:
            ambient_motion.append(item)

    uncertainty_hooks = _diegetic_uncertainty_hooks(narration_basis, cap=2)

    location = str(ps.get("location") or "").strip()
    scene_id = str(ps.get("id") or "").strip()

    contract: Dict[str, Any] = {
        "scene_id": scene_id or None,
        "location": location or None,
        "sensory_anchors": sensory_anchors[:6],
        "ambient_motion": ambient_motion[:4],
        "diegetic_uncertainty_hooks": uncertainty_hooks,
        "prohibited_opener_content": default_prohibited_opener_content(),
        "narration_basis_visible_facts": narration_basis,
        "source": {
            "visible_facts": "public_scene.visible_facts via select_opening_narration_visible_facts",
            "name_grounding": "narration_visibility.visible_entity_names + visible_entity_aliases",
        },
    }
    contract["validator"] = validate_opening_scene_contract(contract)
    return {
        "opening_mode": True,
        "contract": contract,
        "opening_narration_obligations": build_opening_narration_obligations_payload(opening_mode=True),
    }


def merge_opening_instructions(existing: MutableSequence[str], *, contract: Mapping[str, Any]) -> None:
    """Append compact opening-scene instructions (caller owns the list)."""
    c = contract if isinstance(contract, Mapping) else {}
    prohib = c.get("prohibited_opener_content")
    lines = [str(x).strip() for x in prohib if isinstance(x, str) and str(x).strip()] if isinstance(prohib, list) else []
    existing.append(
        "OPENING SCENE (HARD SHAPE): First paragraph grounds the moment in externally observable sensory "
        "and spatial detail only; no omniscient briefing, no title-cased role labels as names, no hidden-fact assertions."
    )
    if lines:
        existing.append("OPENING SCENE PROHIBITED CONTENT: " + " | ".join(lines[:5]))


def opening_realization_none() -> Dict[str, Any]:
    return {
        "opening_mode": False,
        "contract": None,
        "opening_narration_obligations": build_opening_narration_obligations_payload(opening_mode=False),
    }
