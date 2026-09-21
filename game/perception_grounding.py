"""Perception non-invention: observation may reveal the world, not author it.

This is a realization/validation helper. It does not own scene, clue, NPC, or
lead persistence. It consumes existing scene/visibility/clue/NPC surfaces and
fails closed through existing diegetic observe fallback.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from game.clues import get_known_clues_with_presentation
from game.diegetic_fallback_narration import render_observe_perception_fallback_line
from game.referenced_surface import (
    AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
    AUTHORITY_AUTHORED_HIDDEN,
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    AUTHORITY_UNSUPPORTED,
    AUTHORITY_UNTARGETED,
    classification_from_resolution,
    classify_referenced_surface,
    render_referenced_surface_inspection_line,
)
from game.interaction_context import inspect as inspect_interaction_context
from game.storage import get_scene_runtime

PERCEPTION_KINDS = frozenset({"observe", "investigate", "discover_clue", "interact"})
_SOCIAL_OR_EVENT_KINDS = frozenset(
    {
        "question",
        "social_probe",
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
        "dialogue",
        "attack",
        "initiative",
        "spell",
        "enemy_attack",
    }
)

# Player-targeted social/event invention. Category detectors, not scene nouns.
_QUOTED_PLAYER_ADDRESS_RE = re.compile(
    r'["“][^"”]{0,220}\b(?:you(?:\'re|r)?|tell me|ask me|walk with me|get moving|'
    r"get (?:on|clear)|pick one|state your)\b",
    re.IGNORECASE,
)
_PLAYER_TARGETED_APPROACH_RE = re.compile(
    r"\b(?:squares?\s+up\s+to\s+you|stops?\s+at\s+your|comes?\s+(?:straight\s+)?"
    r"(?:to\s+you|over(?:\s+at\s+once)?)|approaches?\s+you|"
    r"peels?\s+away[^.!?]{0,48}\byou\b|closes?\s+the\s+(?:distance|gap)|"
    r"waiting\s+for\s+you\s+to\s+choose|crosses?\s+the\s+space\s+between\s+you|"
    r"cuts?\s+through[^.!?]{0,40}stops?)\b",
    re.IGNORECASE,
)

_PHYSICAL_CATEGORIES: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "inscription",
        re.compile(
            r"\b(?:inscriptions?|inscribed|engraved|etched|"
            r"carved\s+(?:letters?|writing|runes?|words?|names?)|lettering)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "blood",
        re.compile(r"\b(?:blood(?:y|stain|trail)?|gore)\b", re.IGNORECASE),
    ),
    (
        "body",
        re.compile(r"\b(?:corpse|dead\s+body|body\s+lies|remains\s+of)\b", re.IGNORECASE),
    ),
    (
        "secret_passage",
        re.compile(r"\b(?:secret\s+door|hidden\s+door|concealed\s+passage)\b", re.IGNORECASE),
    ),
    (
        "symbol",
        re.compile(r"\b(?:hidden\s+symbol|secret\s+sigil|occult\s+rune)\b", re.IGNORECASE),
    ),
    (
        "dropped_item",
        re.compile(r"\b(?:dropped\s+(?:sword|weapon|blade|letter)|discarded\s+weapon)\b", re.IGNORECASE),
    ),
    (
        "tracks",
        re.compile(r"\b(?:footprints?|boot\s*prints?|tracks\s+in\s+the\s+(?:mud|snow|dust))\b", re.IGNORECASE),
    ),
    (
        "smoke",
        re.compile(r"\b(?:woodsmoke|smoke(?:s|y)?|soot-cloud|burning\s+(?:wood|oil|pitch))\b", re.IGNORECASE),
    ),
    (
        "moving_figure",
        re.compile(
            r"\b(?:a (?:dark |lone |hooded )?(?:figure|silhouette) "
            r"(?:moves|slips|appears|approaches|crosses|emerges)|"
            r"someone (?:approaches|appears|slips|steps out) "
            r"(?:from|out of|in) the)\b",
            re.IGNORECASE,
        ),
    ),
)

# Category detectors for perceptible events. Authorization is presence of the
# same category on the evidence surface, not a banned-word list.
_PERCEPTIBLE_EVENT_CATEGORIES: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "whisper",
        re.compile(r"\bwhispers?\b", re.IGNORECASE),
    ),
    (
        "complaint",
        re.compile(r"\bcomplaints?\b", re.IGNORECASE),
    ),
    (
        "mutter",
        re.compile(r"\bmutters?\b", re.IGNORECASE),
    ),
    (
        "spoken_content",
        re.compile(
            r"\b(?:talk(?:s|ing)? (?:of|about)|whisper(?:s|ing)? (?:about|that|of)|"
            r"complain(?:s|ing|ed|ts?) about|says? that|"
            r"mutter(?:s|ing)? (?:about|that)|murmur(?:s|ing)? (?:about|that|of)|"
            r"shout(?:s|ing)? about)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "footsteps",
        re.compile(
            r"\b(?:footsteps?|boots?\s+(?:scrape|scuff|approach|echo)|"
            r"tread of (?:boots?|feet))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "bell",
        re.compile(r"\b(?:bells?(?:\s+(?:ring|rings|rang|toll|tolls|clang|peal))?|tolling)\b", re.IGNORECASE),
    ),
    (
        "scrape",
        re.compile(
            r"\b(?:something scrapes|scrap(?:e|es|ing) (?:behind|against|along|across))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "shouted_warning",
        re.compile(
            r"\b(?:shout(?:s|ed|ing)? (?:a |the )?warning|warning (?:shout|cry|call)|"
            r"cries? (?:a |the )?warning)\b",
            re.IGNORECASE,
        ),
    ),
)

_NEGATION_WINDOW_RE = re.compile(
    r"\b(?:no|not|none|without|unmarked|blank|bare|lacks?|missing|find\s+no|never|nothing)\b",
    re.IGNORECASE,
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _inner_scene(scene_or_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_or_envelope, Mapping):
        return {}
    raw = scene_or_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_or_envelope)


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = _clean(item)
        if text:
            out.append(text)
    return out


def _resolution_kind(resolution: Mapping[str, Any] | None) -> str:
    if not isinstance(resolution, Mapping):
        return ""
    return _clean(resolution.get("kind")).lower()


def _bound_interlocutor_id(session: Mapping[str, Any] | None) -> str:
    if not isinstance(session, Mapping):
        return ""
    ctx = inspect_interaction_context(dict(session))
    return _clean(ctx.get("active_interaction_target_id"))


def _fact_texts(scene_inner: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts"):
        out.extend(_string_list(scene_inner.get(key)))
    summary = _clean(scene_inner.get("summary"))
    if summary:
        out.append(summary)
    location = _clean(scene_inner.get("location"))
    if location:
        out.append(location)
    return out


def _interactable_texts(scene_inner: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    raw = scene_inner.get("interactables")
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        for key in ("label", "name", "description", "text"):
            text = _clean(item.get(key))
            if text:
                out.append(text)
        out.extend(_string_list(item.get("aliases")))
        props = item.get("properties")
        if isinstance(props, list):
            out.extend(_string_list(props))
        elif isinstance(props, str) and props.strip():
            out.append(props.strip())
    return out


def _exit_texts(scene_inner: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    raw = scene_inner.get("exits")
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        label = _clean(item.get("label"))
        if label:
            out.append(label)
        dest = _clean(item.get("target_scene_id") or item.get("targetSceneId"))
        if dest:
            out.append(dest.replace("_", " "))
    return out


def _present_npc_texts(
    scene_inner: Mapping[str, Any],
    world: Mapping[str, Any] | None,
) -> List[str]:
    out: List[str] = []
    scene_id = _clean(scene_inner.get("id"))
    addressables = scene_inner.get("addressables")
    if isinstance(addressables, list):
        for item in addressables:
            if not isinstance(item, Mapping):
                continue
            name = _clean(item.get("name") or item.get("id"))
            if name:
                out.append(name)
            out.extend(_string_list(item.get("aliases")))
            out.extend(_string_list(item.get("address_roles")))
    if not isinstance(world, Mapping):
        return out
    npcs = world.get("npcs")
    if isinstance(npcs, list):
        rows: Sequence[Any] = npcs
    elif isinstance(npcs, Mapping):
        rows = list(npcs.values())
    else:
        rows = []
    for npc in rows:
        if not isinstance(npc, Mapping):
            continue
        loc = _clean(npc.get("location") or npc.get("scene_id"))
        if scene_id and loc and loc != scene_id:
            continue
        name = _clean(npc.get("name") or npc.get("id"))
        if name:
            out.append(name)
    return out


def _discovered_clue_texts(
    session: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    scene_inner: Mapping[str, Any],
) -> List[str]:
    out: List[str] = []
    known_ids: set[str] = set()
    if isinstance(session, Mapping):
        for row in get_known_clues_with_presentation(dict(session)):
            if not isinstance(row, Mapping):
                continue
            cid = _clean(row.get("id"))
            if cid:
                known_ids.add(cid)
            text = _clean(row.get("text"))
            if text:
                out.append(text)
    if isinstance(resolution, Mapping):
        cid = _clean(resolution.get("clue_id"))
        if cid:
            known_ids.add(cid)
        extra = resolution.get("discovered_clues")
        if isinstance(extra, list):
            for item in extra:
                if isinstance(item, str) and item.strip():
                    known_ids.add(item.strip())
                elif isinstance(item, Mapping):
                    extra_id = _clean(item.get("id"))
                    extra_text = _clean(item.get("text"))
                    if extra_id:
                        known_ids.add(extra_id)
                    if extra_text:
                        out.append(extra_text)
    clues = scene_inner.get("discoverable_clues")
    if isinstance(clues, list):
        for clue in clues:
            if not isinstance(clue, Mapping):
                continue
            if _clean(clue.get("id")) in known_ids:
                text = _clean(clue.get("text"))
                if text:
                    out.append(text)
    return out


def _undiscovered_clue_texts(
    scene_inner: Mapping[str, Any],
    discovered: Sequence[str],
) -> List[str]:
    discovered_low = {item.lower() for item in discovered}
    out: List[str] = []
    clues = scene_inner.get("discoverable_clues")
    if not isinstance(clues, list):
        return out
    for clue in clues:
        if not isinstance(clue, Mapping):
            continue
        text = _clean(clue.get("text"))
        if text and text.lower() not in discovered_low:
            out.append(text)
    return out


def _hidden_fact_texts(
    scene_inner: Mapping[str, Any],
    session: Mapping[str, Any] | None,
) -> List[str]:
    hidden = _string_list(scene_inner.get("hidden_facts"))
    revealed: set[str] = set()
    if isinstance(session, Mapping):
        sid = _clean(scene_inner.get("id"))
        runtime = get_scene_runtime(dict(session), sid) if sid else {}
        if isinstance(runtime, Mapping):
            revealed = {item.lower() for item in _string_list(runtime.get("revealed_hidden_facts"))}
    return [item for item in hidden if item.lower() not in revealed]


def build_perception_evidence_surface(
    *,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Read-only evidence the current perception action may realize."""
    inner = _inner_scene(scene)
    visible = _fact_texts(inner)
    interactables = _interactable_texts(inner)
    exits = _exit_texts(inner)
    npcs = _present_npc_texts(inner, world)
    discovered = _discovered_clue_texts(session, resolution, inner)
    hidden = _hidden_fact_texts(inner, session)
    undiscovered = _undiscovered_clue_texts(inner, discovered)
    authorized_blob = " ".join([*visible, *interactables, *exits, *npcs, *discovered]).lower()
    return {
        "scene_id": _clean(inner.get("id")),
        "visible_facts": visible,
        "interactable_texts": interactables,
        "exit_texts": exits,
        "present_npc_texts": npcs,
        "discovered_clue_texts": discovered,
        "hidden_fact_texts": hidden,
        "undiscovered_clue_texts": undiscovered,
        "authorized_blob": authorized_blob,
        "kind": _resolution_kind(resolution),
        "interlocutor_id": _bound_interlocutor_id(session),
    }


def _distinctive_spans(texts: Sequence[str], *, min_words: int = 6) -> List[str]:
    spans: List[str] = []
    for text in texts:
        words = [part for part in re.findall(r"[a-z0-9']+", text.lower()) if part]
        if len(words) < min_words:
            continue
        spans.append(" ".join(words[:min_words]))
    return spans


def _category_asserted(text: str, pattern: re.Pattern[str]) -> bool:
    for match in pattern.finditer(text):
        window = text[max(0, match.start() - 36) : match.start()]
        if _NEGATION_WINDOW_RE.search(window):
            continue
        return True
    return False


def classify_perception_invention(
    text: str,
    evidence: Mapping[str, Any] | None,
    *,
    resolution: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return unsupported world-significant perception claims, if any."""
    raw = _clean(text)
    kind = _resolution_kind(resolution) or _clean((evidence or {}).get("kind")).lower()
    flags: List[str] = []
    if not raw or kind not in PERCEPTION_KINDS or kind in _SOCIAL_OR_EVENT_KINDS:
        return {"unsupported": False, "flags": flags, "checked": bool(raw)}
    ev = evidence if isinstance(evidence, Mapping) else {}
    interlocutor = _clean(ev.get("interlocutor_id"))
    if not interlocutor and (
        _QUOTED_PLAYER_ADDRESS_RE.search(raw) or _PLAYER_TARGETED_APPROACH_RE.search(raw)
    ):
        flags.append("npc_confrontation")
    blob = _clean(ev.get("authorized_blob")).lower()
    for name, pattern in _PHYSICAL_CATEGORIES:
        if _category_asserted(raw, pattern) and not pattern.search(blob):
            flags.append(f"physical_evidence:{name}")
    for name, pattern in _PERCEPTIBLE_EVENT_CATEGORIES:
        if _category_asserted(raw, pattern) and not pattern.search(blob):
            flags.append(f"perceptible_event:{name}")
    low = raw.lower()
    for span in _distinctive_spans(list(ev.get("hidden_fact_texts") or [])):
        if span and span in low:
            flags.append("hidden_fact")
            break
    for span in _distinctive_spans(list(ev.get("undiscovered_clue_texts") or [])):
        if span and span in low:
            flags.append("clue_invention")
            break
    return {"unsupported": bool(flags), "flags": flags, "checked": True}


def render_grounded_perception_line(
    scene: Mapping[str, Any] | None,
    *,
    player_text: str = "",
    resolution: Mapping[str, Any] | None = None,
    seed_key: str = "perception",
    evidence: Mapping[str, Any] | None = None,
) -> str:
    """Useful fail-closed realization from existing scene/clue surfaces."""
    ev = evidence if isinstance(evidence, Mapping) else {}
    kind = _resolution_kind(resolution) or _clean(ev.get("kind")).lower()
    discovered = [item for item in list(ev.get("discovered_clue_texts") or []) if _clean(item)]
    if kind in {"investigate", "discover_clue"} and discovered:
        line = discovered[-1].strip()
        if line and line[-1] not in ".!?":
            line += "."
        return line
    classified = classification_from_resolution(resolution)
    if not classified.get("authority"):
        classified = classify_referenced_surface(player_text, scene)
    if kind == "investigate" and classified.get("authority") in {
        AUTHORITY_AUTHORED_INTERACTABLE,
        AUTHORITY_AUTHORED_VISIBLE_FEATURE,
        AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
        AUTHORITY_AUTHORED_HIDDEN,
        AUTHORITY_UNSUPPORTED,
    }:
        surface_line = render_referenced_surface_inspection_line(classified, scene)
        if surface_line:
            return surface_line
    line = render_observe_perception_fallback_line(
        scene,
        seed_key=seed_key or "perception",
        player_text=player_text,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    if line and line.strip():
        return line.strip()
    visible = list(ev.get("visible_facts") or [])
    if visible:
        lead = str(visible[0]).strip()
        return lead if lead.endswith((".", "!", "?")) else f"{lead}."
    inner = _inner_scene(scene)
    summary = _clean(inner.get("summary"))
    if summary:
        return summary if summary.endswith((".", "!", "?")) else f"{summary}."
    location = _clean(inner.get("location"))
    if location:
        return f"You take in {location}."
    return "You take in what is actually present here."


def apply_perception_non_invention_to_gm(
    gm_output: dict | None,
    *,
    resolution: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    player_text: str = "",
) -> dict | None:
    """Replace unsupported perception invention with grounded scene realization."""
    if not isinstance(gm_output, dict) or not isinstance(resolution, Mapping):
        return gm_output
    kind = _resolution_kind(resolution)
    if kind not in PERCEPTION_KINDS:
        return gm_output
    text = _clean(gm_output.get("player_facing_text"))
    evidence = build_perception_evidence_surface(
        scene=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    verdict = classify_perception_invention(text, evidence, resolution=resolution)
    classified = classification_from_resolution(resolution)
    if not classified.get("authority"):
        classified = classify_referenced_surface(player_text, scene, world=world)
    force_surface = kind == "investigate" and (
        classified.get("authority")
        in {
            AUTHORITY_AUTHORED_VISIBLE_FEATURE,
            AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
            AUTHORITY_AUTHORED_HIDDEN,
            AUTHORITY_UNSUPPORTED,
            AUTHORITY_UNTARGETED,
        }
        or (
            classified.get("authority") == AUTHORITY_AUTHORED_INTERACTABLE
            and not classified.get("inspectable_text")
        )
    )
    if not verdict.get("unsupported") and not force_surface:
        return gm_output
    sid = _clean(evidence.get("scene_id")) or "perception"
    if force_surface:
        replacement = render_referenced_surface_inspection_line(classified, scene)
    else:
        replacement = render_grounded_perception_line(
            scene,
            player_text=player_text,
            resolution=resolution,
            seed_key=f"prah|{sid}|{kind}|{player_text}",
            evidence=evidence,
        )
    if not replacement:
        return gm_output
    gm_output["player_facing_text"] = replacement
    tags = list(gm_output.get("tags") or []) if isinstance(gm_output.get("tags"), list) else []
    if force_surface:
        if "referenced_surface_realization" not in tags:
            tags.append("referenced_surface_realization")
    elif "perception_non_invention" not in tags:
        tags.append("perception_non_invention")
    gm_output["tags"] = tags
    meta = gm_output.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
        gm_output["metadata"] = meta
    if force_surface:
        meta["referenced_surface_realization"] = {
            "applied": True,
            "authority": classified.get("authority"),
            "target": classified.get("target"),
        }
    else:
        meta["perception_non_invention"] = {
            "applied": True,
            "flags": list(verdict.get("flags") or []),
        }
    if isinstance(session, dict) and sid:
        _resync_contextual_leads_from_grounded_text(session, sid, replacement)
    return gm_output


def _resync_contextual_leads_from_grounded_text(
    session: Dict[str, Any],
    scene_id: str,
    text: str,
) -> None:
    """Prevent rejected prose from remaining as later contextual authority."""
    from game.gm import remember_recent_contextual_leads

    runtime = get_scene_runtime(session, scene_id)
    if isinstance(runtime, dict):
        runtime["recent_contextual_leads"] = []
    remember_recent_contextual_leads(session, scene_id, text)
