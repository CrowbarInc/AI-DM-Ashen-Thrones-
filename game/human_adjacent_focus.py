"""Implicit focus resolution for human-adjacent non-social actions (listen, approach+listen, crowd watch).

Maps player intent to nearby audible/social scene focus before unrelated environmental detail.
Does not replace social routing or provenance systems — only exploration hints + fact ordering.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Tuple

from game.interaction_context import assert_valid_speaker, find_addressed_npc_id_for_turn, inspect as inspect_interaction_context

# Block J / K: canonical continuity bundles (resolution or scene_runtime snapshot).
_HA_CONTINUITY_INTENT_FAMILIES = frozenset({"listen", "approach_listen", "observe_group"})
_HA_CONTINUITY_FOCUS_TIERS = frozenset({"active_npc", "speaking_group", "crowd_cluster"})

# Short follow-ups that continue overhear / nearby-group threads (Block K).
_HA_CONTINUITY_FOLLOWUP_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhat\s+are\s+they\s+(?:saying|talking\s+about)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:were|was)\s+they\s+saying\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:do|does|can)\s+(?:i|we)\s+hear\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+can\s+(?:i|we)\s+(?:make\s+out|discern)\b", re.IGNORECASE),
    re.compile(r"\b(?:i|we)\s+listen\s+in\b", re.IGNORECASE),
    re.compile(r"\blisten\s+in\b", re.IGNORECASE),
    re.compile(r"\b(?:i|we)\s+move\s+closer\b", re.IGNORECASE),
    re.compile(r"\b(?:step|edge|draw)\s+closer\b", re.IGNORECASE),
    re.compile(r"\band\s+the\s+(?:refugees?|patrol|crowd|guards?|group|patrons?|people)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+about\s+the\s+(?:refugees?|patrol|crowd|guards?|group|patrons?)\b", re.IGNORECASE),
    re.compile(r"\bstrain\s+to\s+hear\b", re.IGNORECASE),
    re.compile(r"\b(?:try|tries|trying)\s+to\s+hear\b", re.IGNORECASE),
)

_HUMAN_FOCUS_KEYWORDS: Tuple[str, ...] = (
    "refugee",
    "refugees",
    "patron",
    "patrons",
    "guard",
    "guards",
    "crowd",
    "group",
    "huddle",
    "cluster",
    "whisper",
    "whispers",
    "murmur",
    "murmurs",
    "mutter",
    "gossip",
    "conversation",
    "shout",
    "shouts",
    "runner",
    "voices",
    "voice",
    "rumor",
    "rumour",
    "merchant",
    "merchants",
    "talking",
    "murmuring",
    "urgent whispers",
)

_PHYSICAL_OBJECT_KEYWORDS: Tuple[str, ...] = (
    "footprint",
    "footprints",
    "track",
    "tracks",
    "trail",
    "crate",
    "crates",
    "mud",
    "stain",
    "door",
    "hinge",
    "lock",
    "mark",
    "marks",
    "scrape",
    "scrapes",
    "blood",
    "ash",
    "dead drop",
    "ajar",
    "spill",
)

_PHYSICAL_INSPECTION_RE = re.compile(
    r"\b(?:inspect|examine|study|investigate|search|check)\b[^.?!]{0,140}?"
    r"\b(?:footprint|footprints|tracks?|trail|crate|crates|mud|stain|door|hinge|lock|marks?|scrapes?|blood|ash|dead\s+drop)\b",
    re.IGNORECASE,
)
_FOOTPRINT_NEAR_CRATES_RE = re.compile(
    r"\b(?:footprint|footprints|tracks?)\b.*\b(?:crate|crates|mud)\b|\b(?:crate|crates|mud)\b.*\b(?:footprint|footprints|tracks?)\b",
    re.IGNORECASE,
)


def is_physical_clue_inspection_intent(text: str | None) -> bool:
    """True when the player is clearly inspecting physical evidence, not overhearing people."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if _FOOTPRINT_NEAR_CRATES_RE.search(low):
        return True
    if _PHYSICAL_INSPECTION_RE.search(low):
        return True
    if re.search(r"\b(?:inspect|examine|study)\s+(?:the\s+)?[^.]{0,40}?(?:footprint|footprints|tracks?|trail|crates?)\b", low):
        return True
    return False


def qualifying_canonical_ha_continuity_bundle(md: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    """Return a compact Block-J-shaped dict when *md* carries a defensible nearby-human continuity basis."""
    if not isinstance(md, Mapping):
        return None
    fam = str(md.get("human_adjacent_intent_family") or "").strip().lower()
    tier = str(md.get("implicit_focus_resolution") or "").strip().lower()
    if fam not in _HA_CONTINUITY_INTENT_FAMILIES or tier not in _HA_CONTINUITY_FOCUS_TIERS:
        return None
    lane = str(md.get("parser_lane") or "human_adjacent_observe").strip() or "human_adjacent_observe"
    out: Dict[str, Any] = {
        "human_adjacent_intent_family": fam,
        "implicit_focus_resolution": tier,
        "parser_lane": lane,
    }
    anchor = md.get("implicit_focus_anchor_fact")
    if isinstance(anchor, str) and anchor.strip():
        out["implicit_focus_anchor_fact"] = anchor.strip()[:220]
    if tier == "active_npc":
        tid = str(md.get("implicit_focus_target_id") or "").strip()
        if tid:
            out["implicit_focus_target_id"] = tid
    return out


def looks_like_human_adjacent_continuity_followup_text(text: str | None) -> bool:
    """True for short elliptical lines that continue listen / nearby-group threads."""
    raw = str(text or "").strip()
    if not raw or len(raw) > 140:
        return False
    low = raw.lower()
    return any(rx.search(low) for rx in _HA_CONTINUITY_FOLLOWUP_RES)


def classify_human_adjacent_intent_family(text: str | None) -> str:
    """Narrow intent family for implicit focus; ``none`` when not human-adjacent or when physical inspection."""
    low = str(text or "").strip().lower()
    if not low or is_physical_clue_inspection_intent(low):
        return "none"
    if re.search(r"\blisten\s+to\s+the\s+(?:rain|wind|storm|waves|thunder)\b", low):
        return "none"
    if re.search(r"\b(?:move|step|edge|draw)\s+closer\b", low) and re.search(
        r"\b(?:listen|eavesdrop|overhear|hear|gossip)\b", low
    ):
        return "approach_listen"
    if re.search(r"\bapproach\b", low) and re.search(r"\b(?:gossiping|group)\b", low) and re.search(
        r"\b(?:listen|hear|eavesdrop|overhear)\b", low
    ):
        return "approach_listen"
    if re.search(
        r"\b(?:eavesdrop|eavesdropping|overhear|overhearing|listen\s+in|listen\s+for|strain\s+to\s+hear|"
        r"try\s+to\s+hear|catch\s+(?:their|the)\s+(?:words|conversation)|hear\s+what\s+(?:they|the)\s+(?:say|are\s+saying))\b",
        low,
    ):
        return "listen"
    if re.search(r"\b(?:i|we)\s+listen\b", low) and not re.search(r"\bto\s+the\s+(?:rain|wind|storm)\b", low):
        return "listen"
    if re.search(
        r"\b(?:watch|observe)\s+(?:the\s+)?(?:crowd|patrons?|refugees?|guards?|people|group|gathering)\b", low
    ):
        return "observe_group"
    if re.search(r"\b(?:watch|observe)\s+(?:the\s+)?nearby\s+(?:patrons?|refugees?|guards?|people)\b", low):
        return "observe_group"
    return "none"


def _inner_scene(scene_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_envelope, Mapping):
        return {}
    raw = scene_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_envelope)  # type: ignore[arg-type]


def _fact_human_score(fact: str, *, player_text: str) -> int:
    fl = str(fact or "").lower()
    pt = str(player_text or "").lower()
    score = sum(2 for kw in _HUMAN_FOCUS_KEYWORDS if kw in fl)
    for raw in re.findall(r"[a-z]{4,}", pt):
        if len(raw) >= 5 and raw in fl:
            score += 5
    return int(score)


def _fact_physical_score(fact: str) -> int:
    fl = str(fact or "").lower()
    return sum(2 for kw in _PHYSICAL_OBJECT_KEYWORDS if kw in fl)


def _visible_fact_strings_raw(scene: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(scene, Mapping):
        return []
    vf = scene.get("visible_facts")
    if not isinstance(vf, list):
        return []
    out: List[str] = []
    for item in vf:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def resolve_implicit_human_adjacent_focus(
    *,
    player_text: str,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_envelope: Mapping[str, Any] | None,
    intent_family: str,
) -> Dict[str, Any]:
    """Return compact focus bundle: resolution tier, optional npc id, optional anchor phrase."""
    out: Dict[str, Any] = {
        "implicit_focus_resolution": "none",
        "human_adjacent_intent_family": intent_family if intent_family in {"listen", "approach_listen", "observe_group"} else "none",
        "implicit_focus_target_id": None,
        "implicit_focus_anchor_fact": None,
    }
    if intent_family == "none":
        out["human_adjacent_intent_family"] = "none"
        return out

    scene = _inner_scene(scene_envelope)
    text = str(player_text or "").strip()
    w = world if isinstance(world, dict) else {}
    sess = session if isinstance(session, dict) else None

    if sess is not None and scene:
        ic = inspect_interaction_context(sess)
        active_id = str(ic.get("active_interaction_target_id") or "").strip()
        mode = str(ic.get("interaction_mode") or "").strip().lower()
        if active_id and mode == "social":
            env = scene_envelope if isinstance(scene_envelope, Mapping) else {"scene": scene}
            if assert_valid_speaker(active_id, sess, scene_envelope=env if isinstance(env, dict) else None, world=w):
                out["implicit_focus_resolution"] = "active_npc"
                out["implicit_focus_target_id"] = active_id
                return out

    if sess is not None and scene:
        env = scene_envelope if isinstance(scene_envelope, Mapping) else {"scene": scene}
        addressed = find_addressed_npc_id_for_turn(text, sess, w, scene if isinstance(scene, dict) else None)
        if addressed:
            out["implicit_focus_resolution"] = "active_npc"
            out["implicit_focus_target_id"] = addressed
            return out

    facts = _visible_fact_strings_raw(scene)
    if not facts:
        return out

    ranked: List[Tuple[int, int, str]] = []
    for f in facts:
        h = _fact_human_score(f, player_text=text)
        p = _fact_physical_score(f)
        ranked.append((h, -p, f))
    ranked.sort(key=lambda t: (-t[0], t[1], t[2]))

    best_h, neg_p, best_fact = ranked[0]
    phys_penalty = -neg_p
    if best_h >= 6 or (best_h >= 4 and best_h > phys_penalty + 2):
        out["implicit_focus_resolution"] = "speaking_group"
        out["implicit_focus_anchor_fact"] = best_fact[:220]
        return out
    if best_h >= 2:
        out["implicit_focus_resolution"] = "crowd_cluster"
        out["implicit_focus_anchor_fact"] = best_fact[:220]
        return out

    return out


def _hint_for_focus_bundle(bundle: Dict[str, Any], *, player_text: str) -> str | None:
    fam = str(bundle.get("human_adjacent_intent_family") or "none")
    tier = str(bundle.get("implicit_focus_resolution") or "none")
    anchor = bundle.get("implicit_focus_anchor_fact")
    anchor_s = str(anchor).strip() if anchor else ""

    if tier == "active_npc":
        tid = str(bundle.get("implicit_focus_target_id") or "").strip()
        return (
            "Player is listening / observing near an active in-scene interlocutor. "
            f"Prioritize audible content and reactions tied to that exchange (target id: {tid}). "
            "Do not substitute unrelated environmental props unless the fiction already ties them in."
        )
    if tier in {"speaking_group", "crowd_cluster"} and anchor_s:
        scope = "a nearby speaking cluster or audible crowd detail" if tier == "speaking_group" else "crowd-level noise and motion"
        return (
            f"Human-adjacent intent ({fam}): anchor narration on {scope}. "
            f"Primary visible cue: {anchor_s} "
            "Prefer voices, groups, patrons, refugees, or guards already implied there; avoid random crate or footprint detail unless it directly supports that focus."
        )
    if fam in {"listen", "approach_listen", "observe_group"} and tier == "none":
        return (
            f"Human-adjacent intent ({fam}) but no strong nearby speech focus in established visible facts. "
            "Narrate a clean diegetic limitation: overlapping crowd noise, distance, indistinct voices, or no clear words carrying—"
            "do NOT invent unrelated environmental clues (footprints, crates, stains) as a substitute for overheard content."
        )
    return None


def enrich_exploration_resolution_for_human_adjacent_focus(
    *,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    normalized_action: Dict[str, Any],
    raw_player_text: str | None,
    prompt: str,
    action_type: str,
    hint: str,
    res_metadata: Dict[str, Any],
    transition_candidate: bool,
) -> Tuple[str, Dict[str, Any]]:
    """Attach implicit focus metadata and optional GM hint override for observe/investigate/custom."""
    if transition_candidate:
        return hint, res_metadata
    if action_type not in {"observe", "investigate", "custom"}:
        return hint, res_metadata
    if res_metadata.get("passive_interruption_wait") is True:
        return hint, res_metadata

    text = str(raw_player_text or prompt or "").strip()
    if is_physical_clue_inspection_intent(text):
        md = dict(res_metadata)
        md["human_adjacent_intent_family"] = "none"
        md["implicit_focus_resolution"] = "none"
        return hint, md

    am = normalized_action.get("metadata")
    if isinstance(am, dict) and am.get("nearby_group_continuity_carryover") is True:
        tier = str((am or {}).get("implicit_focus_resolution") or "").strip().lower()
        fam = str((am or {}).get("human_adjacent_intent_family") or "").strip().lower()
        if tier in _HA_CONTINUITY_FOCUS_TIERS and fam in _HA_CONTINUITY_INTENT_FAMILIES:
            md = dict(res_metadata)
            for key in (
                "parser_lane",
                "human_adjacent_intent_family",
                "implicit_focus_resolution",
                "implicit_focus_target_id",
                "implicit_focus_anchor_fact",
                "nearby_group_continuity_carryover",
            ):
                if key in am:
                    md[key] = am[key]
            bundle = {
                "implicit_focus_resolution": tier,
                "human_adjacent_intent_family": fam,
                "implicit_focus_target_id": md.get("implicit_focus_target_id"),
                "implicit_focus_anchor_fact": md.get("implicit_focus_anchor_fact"),
            }
            extra = _hint_for_focus_bundle({**bundle, "human_adjacent_intent_family": fam}, player_text=text)
            new_hint = hint
            if extra:
                new_hint = f"{hint}\n\nENGINE FOCUS: {extra}" if hint else f"ENGINE FOCUS: {extra}"
            return new_hint, md

    fam = str((am or {}).get("human_adjacent_intent_family") or "").strip() if isinstance(am, dict) else ""
    if fam not in {"listen", "approach_listen", "observe_group"}:
        fam = classify_human_adjacent_intent_family(text)
    if fam == "none":
        return hint, res_metadata

    bundle = resolve_implicit_human_adjacent_focus(
        player_text=text,
        session=session,
        world=world,
        scene_envelope=scene_envelope,
        intent_family=fam,
    )
    md = dict(res_metadata)
    md.update(
        {
            "human_adjacent_intent_family": bundle.get("human_adjacent_intent_family", fam),
            "implicit_focus_resolution": bundle.get("implicit_focus_resolution", "none"),
        }
    )
    if bundle.get("implicit_focus_target_id"):
        md["implicit_focus_target_id"] = bundle["implicit_focus_target_id"]
    if bundle.get("implicit_focus_anchor_fact"):
        md["implicit_focus_anchor_fact"] = bundle["implicit_focus_anchor_fact"]
    if bundle.get("implicit_focus_resolution") == "none" and fam in {"listen", "approach_listen", "observe_group"}:
        md["human_adjacent_diegetic_null"] = True

    extra = _hint_for_focus_bundle({**bundle, "human_adjacent_intent_family": fam}, player_text=text)
    new_hint = hint
    if extra:
        new_hint = f"{hint}\n\nENGINE FOCUS: {extra}" if hint else f"ENGINE FOCUS: {extra}"
    return new_hint, md


def prioritize_visible_facts_for_human_adjacent(
    facts: List[str],
    *,
    player_text: str,
    implicit_focus_resolution: str | None,
    human_adjacent_intent_family: str | None,
) -> List[str]:
    """Move human-relevant facts ahead for prompt export when listen/observe-group intent is active."""
    fam = str(human_adjacent_intent_family or "none")
    tier = str(implicit_focus_resolution or "").strip() or "none"
    if fam == "none" or is_physical_clue_inspection_intent(player_text):
        return list(facts)
    if tier == "none":
        return list(facts)
    scored: List[Tuple[int, int, int, str]] = []
    for idx, f in enumerate(facts):
        if not isinstance(f, str) or not f.strip():
            continue
        h = _fact_human_score(f, player_text=player_text)
        p = _fact_physical_score(f)
        scored.append((h, -p, idx, f))
    if not scored:
        return list(facts)
    scored.sort(key=lambda t: (-t[0], t[1], t[2]))
    if scored[0][0] < 2:
        return list(facts)
    head = [t[3] for t in scored]
    tail = [f for f in facts if f not in head]
    out = head + tail
    seen: set[str] = set()
    deduped: List[str] = []
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        deduped.append(x)
    return deduped


def _stable_u32_local(seed: str) -> int:
    acc = 2166136261
    for ch in str(seed or ""):
        acc = (acc ^ ord(ch)) * 16777619
        acc &= 0xFFFFFFFF
    return int(acc)


def diegetic_listen_null_line(*, seed_key: str) -> str:
    """Short diegetic line when listen intent has no distinct focus (stable variety)."""
    opts = (
        "Too much crowd noise washes together; no clear words carry to you.",
        "You catch tone and urgency, but overlapping voices never resolve into distinct speech.",
        "Distance and clamor swallow the syllables—nothing lands as a clean line you could repeat.",
        "A dozen half-conversations brush past your ears; none sharpens enough to follow.",
    )
    i = _stable_u32_local(f"ha-null|{seed_key}") % len(opts)
    return opts[i]
