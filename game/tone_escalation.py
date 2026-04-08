"""Tone / escalation contract + validator (read-only, deterministic).

This layer answers what *intensity* of interpersonal hostility the narrator may portray,
given **published** engine/session/world inputs only. It does not invent scene facts or
drive narrative; downstream callers may consult it before emission.

Policy is **conservative**: when uncertain, caps escalation rather than allowing it.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# Ordered from calm → severe (inclusive ceiling semantics).
_TONE_LEVELS: Tuple[str, ...] = ("neutral", "guarded", "tense", "threatening", "violent")
_TONE_RANK: Dict[str, int] = {name: index for index, name in enumerate(_TONE_LEVELS)}

_AUTHORITY_ROLE_TOKENS: frozenset[str] = frozenset(
    {
        "guard",
        "guards",
        "captain",
        "watch",
        "watchman",
        "watchmen",
        "sentry",
        "guardsman",
        "soldier",
        "soldiers",
        "marshal",
        "bailiff",
        "tax",
        "inspector",
        "official",
    }
)

_TENSION_FACT_PHRASES: Tuple[str, ...] = (
    "curfew",
    "patrol",
    "missing patrol",
    "warning",
    "tax",
    "checkpoint",
    "discipline",
    "choke",
    "pressed",
    "crowd",
    "nerves",
    "tension",
    "watch",
    "armed",
)

_STRONG_TENSION_FACT_PHRASES: Tuple[str, ...] = (
    "riot",
    "blood",
    "drawn steel",
    "weapons",
    "brandish",
    "mob",
    "shouting match",
    "standoff",
)

_COERCIVE_RESOLUTION_KINDS: frozenset[str] = frozenset({"intimidate", "deceive"})
_AGGRESSIVE_RESOLUTION_KINDS: frozenset[str] = frozenset({"attack", "combat"})
_RISKY_RESOLUTION_KINDS: frozenset[str] = frozenset(
    {
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
        "social_probe",
        "attack",
        "combat",
        "initiative",
        "enemy_attack",
        "spell",
        "roll_initiative",
        "cast_spell",
        "interact",
        "investigate",
        "discover_clue",
    }
)

_JUSTIFICATION_FLAG_KEYS: Tuple[str, ...] = (
    "player_used_aggressive_action",
    "player_used_coercive_social_action",
    "player_persisted_after_refusal",
    "scene_has_active_tension",
    "scene_has_authority_pressure",
    "scene_has_visible_hostile_actor",
    "combat_active",
    "resolution_is_risky",
    "npc_already_hostile_in_state",
)

_DIALOGUE_SPAN_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"‘[^’\n]*’"),
    re.compile(r"(?<!\w)'[^'\n]*'(?!\w)"),
)

# Verbal hardening / scrutiny (not yet "or else").
_VERBAL_PRESSURE_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:enough|stop)\s+(?:asking|pushing|talking)\b", re.IGNORECASE),
    re.compile(r"\b(?:back\s+off|lay\s+off|drop\s+it|leave\s+it)\b", re.IGNORECASE),
    re.compile(r"\b(?:not\s+here|wrong\s+place|wrong\s+time)\b", re.IGNORECASE),
    re.compile(r"\b(?:you('?re| are)\s+out\s+of\s+line|overstep)\w*\b", re.IGNORECASE),
    re.compile(r"\b(?:watch\s+your(?:self)?|careful\s+how)\b", re.IGNORECASE),
    re.compile(r"\b(?:cold|hard|flat)\s+(?:stare|look|smile)\b", re.IGNORECASE),
    re.compile(r"\b(?:hand|fingers)\s+(?:rest|drift|hover)\w*\s+(?:on|near|by)\s+(?:the\s+)?(?:hilt|pommel|haft|belt)\b", re.IGNORECASE),
)

# Explicit conditional / capability threats.
_EXPLICIT_THREAT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:or\s+else|or\s+you(?:'ll| will))\b", re.IGNORECASE),
    re.compile(r"\b(?:you(?:'ll| will)\s+regret|you(?:'ll| will)\s+be\s+sorry)\b", re.IGNORECASE),
    re.compile(r"\b(?:last\s+chance|one\s+more\s+word|try\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(?:i(?:'ll| will)\s+(?:hurt|kill|ruin|break)\s+you)\b", re.IGNORECASE),
    re.compile(r"\b(?:make\s+you\s+(?:hurt|bleed|pay))\b", re.IGNORECASE),
)

_PHYSICAL_HOSTILITY_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:lunge|lunges|lunging|grab|grabs|grabbing|shove|shoves|shoving|"
        r"slam|slams|slamming|strike|strikes|striking|punch|punches|kick|kicks|"
        r"stab|stabs|cut|cuts|slash|slashes|shoot|shoots|fire|fires)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:throws?\s+a\s+punch|connects?\s+with|knocks?\s+(?:you|them|him|her)\s+(?:down|back|aside))\b",
        re.IGNORECASE,
    ),
)

_WEAPON_DRAW_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:draw|draws|drawing|unsheathe|unsheathes|clear|clears)\s+"
        r"(?:a\s+|the\s+|his\s+|her\s+|their\s+)?(?:blade|sword|knife|dagger|axe|mace|weapon|steel|bow)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:weapon\s+comes\s+free|steel\s+(?:clears|whispers|hisses))\b", re.IGNORECASE),
)

_COMBAT_INITIATION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:initiative|rolls?\s+initiative|first\s+strike|combat\s+begins)\b", re.IGNORECASE),
    re.compile(r"\b(?:attack\s+of\s+opportunity|readied\s+action|surprise\s+round)\b", re.IGNORECASE),
)

_FORCED_DRAMA_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:out\s+of\s+nowhere|without\s+warning|suddenly,?\s+everything)\b", re.IGNORECASE),
    re.compile(r"\b(?:chaos\s+erupts|all\s+hell\s+breaks\s+loose)\b", re.IGNORECASE),
    re.compile(r"\b(?:a\s+shadowy\s+figure|the\s+stranger\s+attacks)\b", re.IGNORECASE),
)

_GUARDED_SOFT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:tense|tension|uneasy|wary|guarded|careful|hesitat\w*)\b", re.IGNORECASE),
    re.compile(r"\b(?:refuse|refuses|refusing|won'?t\s+(?:say|tell|help))\b", re.IGNORECASE),
    re.compile(r"\b(?:not\s+(?:your\s+business|for\s+you))\b", re.IGNORECASE),
)


def _clean_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _tone_name(rank: int) -> str:
    rank = max(0, min(rank, len(_TONE_LEVELS) - 1))
    return _TONE_LEVELS[rank]


def _tone_rank(name: str) -> int:
    key = _clean_str(name).lower()
    return _TONE_RANK.get(key, 0)


def _normalize_scan_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split()).strip().lower()
    if not text:
        return ""
    punct = string.punctuation
    while text and text[0] in punct:
        text = text[1:].lstrip().lower()
        text = " ".join(text.split()).strip()
    while text and text[-1] in punct:
        text = text[:-1].rstrip().lower()
        text = " ".join(text.split()).strip()
    return text


def _mask_dialogue_spans(text: str) -> str:
    if not text:
        return ""
    masked = list(text)
    for pattern in _DIALOGUE_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                masked[index] = " "
    return "".join(masked)


def _visible_roles(nv: Mapping[str, Any]) -> List[str]:
    roles_map = nv.get("visible_entity_roles")
    if not isinstance(roles_map, Mapping):
        return []
    out: List[str] = []
    for value in roles_map.values():
        if isinstance(value, str) and value.strip():
            out.append(value.strip().lower())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip().lower())
    return out


def _facts_blob(nv: Mapping[str, Any]) -> str:
    facts = nv.get("visible_fact_strings")
    if not isinstance(facts, list):
        return ""
    parts: List[str] = []
    for item in facts:
        if isinstance(item, str) and item.strip():
            parts.append(item.strip().lower())
    return " ".join(parts)


def _npcs_for_scene(world: Mapping[str, Any], scene_id: str) -> List[Mapping[str, Any]]:
    npcs = world.get("npcs")
    if not isinstance(npcs, list):
        return []
    sid = _clean_str(scene_id)
    out: List[Mapping[str, Any]] = []
    for row in npcs:
        if isinstance(row, dict):
            loc = _clean_str(row.get("location") or row.get("scene_id") or row.get("origin_scene_id"))
            if loc == sid:
                out.append(row)
    return out


def _stance_hostile(npc: Mapping[str, Any]) -> bool:
    stance = _clean_str(npc.get("stance_toward_player")).lower()
    if stance == "hostile":
        return True
    disp = _clean_str(npc.get("disposition")).lower()
    if disp == "hostile":
        return True
    tags = npc.get("tags")
    if isinstance(tags, list):
        lowered = {str(t).strip().lower() for t in tags if isinstance(t, str)}
        if lowered & {"hostile", "enemy", "aggressive"}:
            return True
    return False


def _log_player_text(entry: Mapping[str, Any]) -> str:
    lm = entry.get("log_meta")
    if isinstance(lm, dict):
        pi = lm.get("player_input")
        if isinstance(pi, str) and pi.strip():
            return pi.strip()
    req = entry.get("request")
    if isinstance(req, dict):
        t = req.get("text")
        if isinstance(t, str) and t.strip():
            return t.strip()
    return ""


def _resolution_kind(res: Mapping[str, Any]) -> str:
    return _clean_str(res.get("kind")).lower()


def _normalized_action_type(res: Mapping[str, Any]) -> str:
    meta = res.get("metadata")
    if isinstance(meta, dict):
        na = meta.get("normalized_action")
        if isinstance(na, dict):
            return _clean_str(na.get("type")).lower()
    return ""


def _combat_payload_active(res: Mapping[str, Any]) -> bool:
    combat = res.get("combat")
    if not isinstance(combat, dict) or not combat:
        return False
    phase = _clean_str(combat.get("combat_phase")).lower()
    if phase in {"", "idle", "none"}:
        return False
    return True


def _resolution_shows_refusal(res: Mapping[str, Any]) -> bool:
    soc = res.get("social")
    if isinstance(soc, dict):
        rk = _clean_str(soc.get("reply_kind")).lower()
        if rk == "refusal":
            return True
        tags = soc.get("tags")
        if isinstance(tags, list) and any(
            isinstance(t, str) and t.strip().lower() in {"refusal_evasion", "refusal", "pressure_refusal"} for t in tags
        ):
            return True
    return False


def _player_text_aggressive(text: str) -> bool:
    low = _normalize_scan_text(text)
    if not low:
        return False
    return bool(
        re.search(
            r"\b(?:attack|strike|stab|shoot|kill|murder|grab|shove|punch|kick|draw|unsheathe|"
            r"threaten|intimidate|cut\s+down|run\s+through)\b",
            low,
        )
    )


def _player_text_coercive(text: str) -> bool:
    low = _normalize_scan_text(text)
    if not low:
        return False
    return bool(
        re.search(
            r"\b(?:intimidate|threaten|blackmail|coerce|force|or\s+else|make\s+you\s+talk)\b",
            low,
        )
    )


def _scan_recent_player_voice(recent_log: Sequence[Mapping[str, Any]], max_entries: int = 4) -> Tuple[str, str]:
    """Return (latest_player_text, concatenated_recent) from log tail."""
    if not recent_log:
        return "", ""
    tail = list(recent_log[-max_entries:]) if len(recent_log) > max_entries else list(recent_log)
    chunks: List[str] = []
    latest = ""
    for entry in tail:
        if not isinstance(entry, Mapping):
            continue
        t = _log_player_text(entry)
        if t:
            chunks.append(t)
            latest = t
    return latest, " ".join(chunks)


def _topic_pressure_value(session: Mapping[str, Any], scene_id: str) -> int:
    root = session.get("scene_runtime")
    if not isinstance(root, dict):
        return 0
    per_scene = root.get(scene_id)
    if not isinstance(per_scene, dict):
        return 0
    raw = per_scene.get("topic_pressure")
    try:
        return int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        return 0


def _collect_justification(
    *,
    session: Mapping[str, Any],
    world: Mapping[str, Any],
    scene_id: str,
    resolution: Mapping[str, Any] | None,
    narration_visibility: Mapping[str, Any],
    scene_state_anchor_contract: Mapping[str, Any],
    recent_log: Sequence[Mapping[str, Any]] | None,
) -> Tuple[Dict[str, bool], List[str], Dict[str, Any]]:
    flags: Dict[str, bool] = {key: False for key in _JUSTIFICATION_FLAG_KEYS}
    reasons: List[str] = []
    dbg: Dict[str, Any] = {}

    res = resolution if isinstance(resolution, Mapping) else None
    kind = _resolution_kind(res) if res else ""
    nat = _normalized_action_type(res) if res else ""

    latest_pt, combined_pt = _scan_recent_player_voice(recent_log or ())
    dbg["recent_player_text_latest_len"] = len(latest_pt)
    dbg["resolution_kind"] = kind or None
    dbg["normalized_action_type"] = nat or None

    if res and (kind in _AGGRESSIVE_RESOLUTION_KINDS or nat in {"attack", "combat"}):
        flags["player_used_aggressive_action"] = True
        reasons.append("resolution_kind_or_normalized_action_is_attackish")
    elif _player_text_aggressive(latest_pt) or _player_text_aggressive(combined_pt):
        flags["player_used_aggressive_action"] = True
        reasons.append("recent_player_text_matches_aggressive_tokens")

    if res and kind in _COERCIVE_RESOLUTION_KINDS:
        flags["player_used_coercive_social_action"] = True
        reasons.append("resolution_kind_coercive_social")
    elif _player_text_coercive(latest_pt) or _player_text_coercive(combined_pt):
        flags["player_used_coercive_social_action"] = True
        reasons.append("recent_player_text_matches_coercive_tokens")

    prev_refusal = False
    if recent_log:
        for entry in reversed(recent_log):
            if not isinstance(entry, Mapping):
                continue
            prev_res = entry.get("resolution")
            if isinstance(prev_res, dict) and _resolution_shows_refusal(prev_res):
                prev_refusal = True
                break
    dbg["prior_refusal_seen_in_log"] = prev_refusal

    if prev_refusal and res and isinstance(res.get("social"), dict):
        soc = res["social"]
        if isinstance(soc, dict):
            prev_npc = None
            if recent_log:
                for entry in reversed(recent_log):
                    if not isinstance(entry, Mapping):
                        continue
                    pr = entry.get("resolution")
                    if isinstance(pr, dict) and isinstance(pr.get("social"), dict):
                        prev_npc = _clean_str(pr["social"].get("npc_id"))
                        if prev_npc:
                            break
            cur_npc = _clean_str(soc.get("npc_id"))
            if prev_npc and cur_npc and prev_npc == cur_npc and kind in {
                "persuade",
                "intimidate",
                "deceive",
                "question",
                "social_probe",
                "barter",
            }:
                flags["player_persisted_after_refusal"] = True
                reasons.append("continued_social_push_after_logged_refusal_same_npc")

    blob = _facts_blob(narration_visibility)
    strong_hit = any(p in blob for p in _STRONG_TENSION_FACT_PHRASES)
    soft_hit = any(p in blob for p in _TENSION_FACT_PHRASES)
    roles = _visible_roles(narration_visibility)
    role_blob = " ".join(roles)
    authority_hit = any(token in role_blob.split() for token in _AUTHORITY_ROLE_TOKENS) or any(
        any(tok in r for tok in _AUTHORITY_ROLE_TOKENS) for r in roles
    )

    ic = session.get("interaction_context")
    engagement = _clean_str(ic.get("engagement_level")).lower() if isinstance(ic, dict) else ""

    pressure = _topic_pressure_value(session, scene_id)
    dbg["topic_pressure"] = pressure

    if strong_hit or pressure >= 4:
        flags["scene_has_active_tension"] = True
        reasons.append("visible_facts_or_runtime_topic_pressure_indicate_elevated_tension")
    elif soft_hit or pressure >= 2 or engagement in {"engaged", "focused"}:
        flags["scene_has_active_tension"] = True
        reasons.append("visible_facts_engagement_or_moderate_topic_pressure")

    if authority_hit:
        flags["scene_has_authority_pressure"] = True
        reasons.append("visible_entity_roles_include_authority_guardship")

    nv_kinds = narration_visibility.get("visible_entity_kinds")
    hostile_visible = False
    if isinstance(nv_kinds, Mapping):
        for value in nv_kinds.values():
            if isinstance(value, str) and value.strip().lower() in {"enemy", "creature", "hostile"}:
                hostile_visible = True
                break
    npcs_here = _npcs_for_scene(world, scene_id)
    hostile_npc_here = any(_stance_hostile(n) for n in npcs_here)
    if hostile_visible:
        flags["scene_has_visible_hostile_actor"] = True
        reasons.append("visibility_marks_hostile_kind")
    if hostile_npc_here:
        flags["scene_has_visible_hostile_actor"] = True
        flags["npc_already_hostile_in_state"] = True
        reasons.append("world_npc_in_scene_with_hostile_stance_or_disposition")

    factions = world.get("factions")
    if isinstance(factions, list) and npcs_here:
        aff_ids = {
            _clean_str(n.get("affiliation")).lower()
            for n in npcs_here
            if _clean_str(n.get("affiliation"))
        }
        for fac in factions:
            if not isinstance(fac, dict):
                continue
            fid = _clean_str(fac.get("id")).lower()
            if not fid or fid not in aff_ids:
                continue
            att = _clean_str(fac.get("attitude")).lower()
            try:
                fpress = int(fac.get("pressure") or 0)
            except (TypeError, ValueError):
                fpress = 0
            if fpress >= 2 and att in {"suspicious", "wary", "opportunistic", "hostile"}:
                flags["scene_has_active_tension"] = True
                reasons.append("affiliated_faction_attitude_and_pressure_in_world_state")

    combat_active = False
    if res:
        if _combat_payload_active(res):
            combat_active = True
            reasons.append("resolution_carries_active_combat_payload")
        elif kind in {"initiative", "enemy_attack", "end_turn", "combat"}:
            combat_active = True
            reasons.append("resolution_kind_mid_combat_timeline")
    dbg["combat_active_inferred"] = combat_active
    flags["combat_active"] = combat_active

    risky = False
    if res:
        if kind in _RISKY_RESOLUTION_KINDS:
            risky = True
        if bool(res.get("requires_check")):
            risky = True
        sc = res.get("skill_check")
        if isinstance(sc, dict) and sc:
            risky = True
        if _combat_payload_active(res):
            risky = True
    if risky:
        flags["resolution_is_risky"] = True
        reasons.append("resolution_kind_or_mechanical_payload_is_risky")

    anchor = scene_state_anchor_contract.get("player_action_tokens") if scene_state_anchor_contract else None
    if isinstance(anchor, list):
        joined = " ".join(str(x).lower() for x in anchor if isinstance(x, str))
        if re.search(r"\b(?:attack|strike|grab|shove|threat|draw)\b", joined):
            if not flags["player_used_aggressive_action"]:
                flags["player_used_aggressive_action"] = True
                reasons.append("scene_state_anchor_player_action_tokens_imply_physical_or_threat_move")

    return flags, reasons, dbg


def _compute_base_rank(
    flags: Mapping[str, bool],
    narration_visibility: Mapping[str, Any],
    session: Mapping[str, Any],
) -> int:
    rank = 0
    blob = _facts_blob(narration_visibility)
    if any(p in blob for p in _TENSION_FACT_PHRASES):
        rank = max(rank, 1)
    if any(p in blob for p in _STRONG_TENSION_FACT_PHRASES):
        rank = max(rank, 2)

    roles = _visible_roles(narration_visibility)
    role_blob = " ".join(roles)
    if any(token in role_blob for token in _AUTHORITY_ROLE_TOKENS):
        rank = max(rank, 1)

    ic = session.get("interaction_context")
    if isinstance(ic, dict):
        eng = _clean_str(ic.get("engagement_level")).lower()
        imode = _clean_str(ic.get("interaction_mode")).lower()
        if eng in {"engaged", "focused"}:
            rank = max(rank, 1)
        if imode not in {"", "none"}:
            rank = max(rank, 1)

    if flags.get("scene_has_active_tension"):
        rank = max(rank, 1)
    if flags.get("scene_has_authority_pressure"):
        rank = max(rank, 1)
    if flags.get("npc_already_hostile_in_state"):
        rank = max(rank, 2)
    if flags.get("scene_has_visible_hostile_actor") and flags.get("npc_already_hostile_in_state"):
        rank = max(rank, 2)
    return rank


def _compute_max_rank(flags: Mapping[str, bool], base_rank: int, resolution_kind: str) -> int:
    m = base_rank
    kind = _clean_str(resolution_kind).lower()

    if flags.get("resolution_is_risky"):
        m = max(m, 1)

    if flags.get("scene_has_active_tension"):
        m = max(m, 2)

    if flags.get("player_used_coercive_social_action"):
        m = max(m, 2)

    if flags.get("player_persisted_after_refusal"):
        m = max(m, 2)

    threat_gate = (
        flags.get("player_used_aggressive_action")
        or flags.get("combat_active")
        or flags.get("npc_already_hostile_in_state")
        or (flags.get("scene_has_authority_pressure") and flags.get("player_used_coercive_social_action"))
        or (flags.get("scene_has_visible_hostile_actor") and flags.get("player_used_coercive_social_action"))
    )
    if threat_gate:
        m = max(m, 3)

    # Violence in narration: only when combat is active or the engine resolved an attack/combat beat.
    violent_gate = bool(flags.get("combat_active")) or kind in _AGGRESSIVE_RESOLUTION_KINDS
    if violent_gate:
        m = max(m, 4)

    # Topic pressure / risky resolution alone cannot justify threats.
    if m >= 3 and not threat_gate:
        m = 2

    if m >= 4 and not violent_gate:
        m = 3

    return max(0, min(m, 4))


def _allow_flags(max_rank: int, flags: Mapping[str, bool], resolution_kind: str) -> Dict[str, bool]:
    allow_guarded = max_rank >= 1
    allow_verbal = max_rank >= 2
    allow_threat = max_rank >= 3
    combat = bool(flags.get("combat_active"))
    kind = _clean_str(resolution_kind).lower()
    allow_physical = max_rank >= 4 or (combat and max_rank >= 3)
    allow_combat_init = combat or kind in {"initiative", "enemy_attack", "combat", "roll_initiative"}
    return {
        "allow_guarded_refusal": allow_guarded,
        "allow_verbal_pressure": allow_verbal,
        "allow_explicit_threat": allow_threat,
        "allow_physical_hostility": allow_physical,
        "allow_combat_initiation": allow_combat_init,
    }


def _preferred_deescalations(max_rank: int) -> List[str]:
    if max_rank >= 4:
        return [
            "Keep violence implied or off-screen unless combat state is active.",
            "Prefer a visible threat or standoff beat over a landed strike.",
            "Use environmental friction (crowd, orders, noise) instead of injury.",
        ]
    if max_rank >= 3:
        return [
            "Swap ultimatums for clipped scrutiny and procedural pressure.",
            "Offer a hard boundary or refusal without capability threats.",
            "Shift to time pressure or witness risk instead of bodily harm.",
        ]
    if max_rank >= 2:
        return [
            "Tighten diction and body language without 'or else' phrasing.",
            "Use deadlines, policy, or reputation risk as leverage.",
        ]
    return [
        "Default to observational tone; keep interpersonal heat optional.",
        "Prefer curiosity and clarification over suspicion-as-accusation.",
    ]


def build_tone_escalation_contract(
    *,
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    scene_id: str,
    resolution: Mapping[str, Any] | None,
    speaker_selection_contract: Mapping[str, Any] | None = None,
    scene_state_anchor_contract: Mapping[str, Any] | None = None,
    narration_visibility: Mapping[str, Any] | None = None,
    recent_log: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Assemble a conservative tone / escalation ceiling from published inputs only."""
    sid = _clean_str(scene_id)
    sess = _mapping(session)
    w = _mapping(world)
    nv = _mapping(narration_visibility)
    ssc = _mapping(speaker_selection_contract)
    sac = _mapping(scene_state_anchor_contract)

    active_speaker = _clean_str(ssc.get("primary_speaker_id")) or None
    if not active_speaker:
        active_speaker = _clean_str(nv.get("active_interlocutor_id")) or None

    if not sid:
        return {
            "enabled": False,
            "scene_id": sid or "",
            "active_speaker_id": active_speaker,
            "base_tone": "neutral",
            "max_allowed_tone": "neutral",
            "allow_guarded_refusal": False,
            "allow_verbal_pressure": False,
            "allow_explicit_threat": False,
            "allow_physical_hostility": False,
            "allow_combat_initiation": False,
            "justification_flags": {k: False for k in _JUSTIFICATION_FLAG_KEYS},
            "justification_reasons": [],
            "preferred_deescalations": _preferred_deescalations(0),
            "debug_reason": "aborted_empty_scene_id",
            "debug_inputs": {"scene_id": sid},
            "debug_flags": {},
        }

    flags, reasons, jdbg = _collect_justification(
        session=sess,
        world=w,
        scene_id=sid,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        narration_visibility=nv,
        scene_state_anchor_contract=sac,
        recent_log=recent_log,
    )

    res_kind = _resolution_kind(resolution) if isinstance(resolution, Mapping) else ""

    base_rank = _compute_base_rank(flags, nv, sess)
    max_rank = _compute_max_rank(flags, base_rank, res_kind)
    allows = _allow_flags(max_rank, flags, res_kind)

    debug_inputs: Dict[str, Any] = {
        "scene_id": sid,
        "has_session": bool(session),
        "has_world": bool(world),
        "has_resolution": isinstance(resolution, Mapping),
        "has_narration_visibility": bool(nv),
        "has_scene_state_anchor_contract": bool(sac),
        "has_speaker_selection_contract": bool(ssc),
        "recent_log_len": len(recent_log) if isinstance(recent_log, Sequence) and not isinstance(recent_log, (str, bytes)) else 0,
    }
    debug_flags: Dict[str, Any] = {
        "base_rank": base_rank,
        "max_rank": max_rank,
        **jdbg,
    }
    debug_reason = (
        f"tone_escalation: base_rank={base_rank} max_rank={max_rank} "
        f"combat_active={bool(flags.get('combat_active'))} hostile_npc={bool(flags.get('npc_already_hostile_in_state'))}"
    )

    return {
        "enabled": True,
        "scene_id": sid,
        "active_speaker_id": active_speaker,
        "base_tone": _tone_name(base_rank),
        "max_allowed_tone": _tone_name(max_rank),
        "allow_guarded_refusal": allows["allow_guarded_refusal"],
        "allow_verbal_pressure": allows["allow_verbal_pressure"],
        "allow_explicit_threat": allows["allow_explicit_threat"],
        "allow_physical_hostility": allows["allow_physical_hostility"],
        "allow_combat_initiation": allows["allow_combat_initiation"],
        "justification_flags": dict(flags),
        "justification_reasons": list(dict.fromkeys(reasons)),
        "preferred_deescalations": _preferred_deescalations(max_rank),
        "debug_reason": debug_reason,
        "debug_inputs": debug_inputs,
        "debug_flags": debug_flags,
    }


def _detect_levels(masked_text: str) -> Dict[str, bool]:
    low = _normalize_scan_text(masked_text)
    out = {
        "guarded": False,
        "verbal_pressure": False,
        "explicit_threat": False,
        "physical_hostility": False,
        "combat_initiation": False,
    }
    if not low:
        return out

    if any(p.search(low) for p in _GUARDED_SOFT_RES):
        out["guarded"] = True
    if any(p.search(low) for p in _VERBAL_PRESSURE_RES):
        out["verbal_pressure"] = True
    if any(p.search(low) for p in _EXPLICIT_THREAT_RES):
        out["explicit_threat"] = True
    if any(p.search(low) for p in _FORCED_DRAMA_RES):
        out["explicit_threat"] = True
        out["verbal_pressure"] = True
    if any(p.search(low) for p in _WEAPON_DRAW_RES):
        out["explicit_threat"] = True
    if any(p.search(low) for p in _PHYSICAL_HOSTILITY_RES):
        out["physical_hostility"] = True
    if any(p.search(low) for p in _COMBAT_INITIATION_RES):
        out["combat_initiation"] = True

    return out


def _matched_tone_level(assertions: Mapping[str, bool]) -> Optional[str]:
    if assertions.get("physical_hostility") or assertions.get("combat_initiation"):
        return "violent"
    if assertions.get("explicit_threat"):
        return "threatening"
    if assertions.get("verbal_pressure"):
        return "tense"
    if assertions.get("guarded"):
        return "guarded"
    return None


def validate_tone_escalation(
    text: str,
    *,
    contract: Mapping[str, Any] | None,
    player_text: str | None = None,
) -> Dict[str, Any]:
    """Check *text* against a pre-built tone escalation contract (conservative)."""
    ctr = _mapping(contract) if contract is not None else {}
    if not ctr.get("enabled"):
        return {
            "checked": False,
            "ok": True,
            "failure_reasons": [],
            "matched_tone_level": None,
            "detected_assertion_flags": {
                "guarded": False,
                "verbal_pressure": False,
                "explicit_threat": False,
                "physical_hostility": False,
                "combat_initiation": False,
            },
            "suggested_deflection_modes": [],
        }

    raw = str(text or "")
    masked = _mask_dialogue_spans(raw)
    assertions = _detect_levels(masked)
    matched = _matched_tone_level(assertions)
    matched_rank = _tone_rank(matched) if matched else 0
    max_rank = _tone_rank(str(ctr.get("max_allowed_tone") or "neutral"))

    failure_reasons: List[str] = []

    if matched_rank >= 1 and not ctr.get("allow_guarded_refusal"):
        failure_reasons.append("guarded_tone_not_allowed")
    if assertions.get("verbal_pressure") and not ctr.get("allow_verbal_pressure"):
        failure_reasons.append("verbal_pressure_not_allowed")
    if assertions.get("explicit_threat") and not ctr.get("allow_explicit_threat"):
        failure_reasons.append("explicit_threat_not_allowed")
    if assertions.get("physical_hostility") and not ctr.get("allow_physical_hostility"):
        failure_reasons.append("physical_hostility_not_allowed")
    if assertions.get("combat_initiation") and not ctr.get("allow_combat_initiation"):
        failure_reasons.append("combat_initiation_not_allowed")

    # Unsupported weapon/drama path: drawing steel or forced drama needs threat allowance at minimum.
    low = _normalize_scan_text(masked)
    if low:
        if any(p.search(low) for p in _WEAPON_DRAW_RES) and not ctr.get("allow_explicit_threat"):
            failure_reasons.append("weapon_draw_requires_explicit_threat_allowance")
        if any(p.search(low) for p in _FORCED_DRAMA_RES) and not ctr.get("allow_verbal_pressure"):
            failure_reasons.append("forced_drama_cue_requires_verbal_pressure_allowance")

    # Optional player echo: if narration only mirrors player's violent phrasing in quoted dialogue,
    # we already masked quotes; if player_text is extreme but contract disallows violence, do not
    # automatically fail unless narration also asserts physical hostility outside quotes.

    ok = not failure_reasons
    deflections: List[str] = []
    if not ok:
        deflections = ["bounded_uncertainty", "scrutiny_without_threat", "procedural_deadline"]

    return {
        "checked": True,
        "ok": ok,
        "failure_reasons": list(dict.fromkeys(failure_reasons)),
        "matched_tone_level": matched,
        "detected_assertion_flags": dict(assertions),
        "suggested_deflection_modes": deflections,
    }


def tone_escalation_repair_hints(
    *,
    contract: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None,
) -> List[str]:
    """Return deterministic repair nudges when validation fails."""
    ctr = _mapping(contract) if contract is not None else {}
    val = _mapping(validation) if validation is not None else {}
    if not val.get("checked") or val.get("ok"):
        return []

    hints: List[str] = []
    fails = [str(x) for x in (val.get("failure_reasons") or []) if isinstance(x, str)]

    if "physical_hostility_not_allowed" in fails:
        hints.append("Replace landed blows or grabs with a failed reach, a checked motion, or an interrupted swing.")
        hints.append("If combat is not authorized, keep harm off-screen or use a standoff beat instead.")
    if "combat_initiation_not_allowed" in fails:
        hints.append("Defer system combat initiation; describe posturing or a break in the crowd instead.")
    if "explicit_threat_not_allowed" in fails:
        hints.append("Swap ultimatums for clipped refusal, scrutiny, or a procedural boundary (policy, orders, time).")
    if "verbal_pressure_not_allowed" in fails:
        hints.append("Soften hardening: cool professionalism, short answers, or changing the subject without warnings.")
    if "guarded_tone_not_allowed" in fails:
        hints.append("Reduce interpersonal edge to neutral observation unless the contract permits guarded refusal.")
    if "weapon_draw_requires_explicit_threat_allowance" in fails:
        hints.append("Keep steel sheathed; imply readiness with posture, spacing, or hands resting away from steel.")
    if "forced_drama_cue_requires_verbal_pressure_allowance" in fails:
        hints.append("Remove 'sudden chaos' beats; anchor friction in visible scene facts or social procedure.")

    for line in ctr.get("preferred_deescalations") or []:
        if isinstance(line, str) and line.strip():
            hints.append(line.strip())

    out: List[str] = []
    seen: set[str] = set()
    for h in hints:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out
