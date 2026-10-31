"""Deterministic session continuity diagnostics (no LLM, advisory only).

Detects *obvious* goldfish-memory failures across a short recent window: abrupt
scene resets, role/name slot drift, and rewards explicit callbacks. Intended
for gauntlets, simulations, and optional debug — never for altering narration.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any, Mapping, Sequence

_MAX_CHARS_PER_TURN = 24_000
_MAX_TURNS = 32

# --- env --------------------------------------------------------------------

def _truthy_env(name: str) -> bool:
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


# --- extraction (tolerant record shapes) ------------------------------------

_DEBUG_KEYS = frozenset(
    k.lower()
    for k in (
        "debug",
        "debug_notes",
        "trace",
        "turn_trace",
        "last_action_debug",
        "tool_calls",
        "raw_response",
    )
)


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def extract_player_input(turn: Mapping[str, Any] | None) -> str:
    """Best-effort player text from a loose turn packet."""
    if not isinstance(turn, Mapping):
        return ""
    t = turn
    return _as_str(t.get("player_input") or t.get("player_text") or t.get("intent"))


def extract_player_facing_text(turn: Mapping[str, Any] | None) -> str:
    """Best-effort GM / narration text from a loose turn packet."""
    if not isinstance(turn, Mapping):
        return ""
    t = turn
    s = _as_str(
        t.get("final_output")
        or t.get("player_facing_text")
        or t.get("narration")
        or t.get("gm_text")
    )
    if s:
        return s
    gm = t.get("gm")
    if isinstance(gm, Mapping):
        return _as_str(gm.get("player_facing_text") or gm.get("text"))
    return ""


def extract_scene_hint(turn: Mapping[str, Any] | None) -> str:
    """Scene / location-ish metadata if present (bounded)."""
    if not isinstance(turn, Mapping):
        return ""
    t = turn
    for key in ("scene_id", "sceneId", "active_scene", "location", "scene_label"):
        v = t.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()[:200]
    scene = t.get("scene")
    if isinstance(scene, Mapping):
        sid = scene.get("id") or scene.get("scene_id")
        if isinstance(sid, str) and sid.strip():
            return sid.strip()[:200]
    return ""


def _strip_debug_blobs(text: str) -> str:
    """Remove obvious JSON/debug dumps from scanning (bounded)."""
    if not text or len(text) > _MAX_CHARS_PER_TURN:
        text = text[:_MAX_CHARS_PER_TURN]
    # Lines that look like debug headers
    lines_out: list[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if any(low.startswith(k + ":") or low.startswith(k + " ") for k in ("dm:", "gm:", "debug:", "trace:")):
            continue
        lines_out.append(line)
    return "\n".join(lines_out)


def _meaningful_turn(narr: str, scene_hint: str) -> bool:
    return len(narr.strip()) >= 28 or len(scene_hint.strip()) >= 2


# --- bounded lexical extraction ---------------------------------------------

_TITLE_BLOCK = frozenset(
    """
    The This That These Those They There Then Than When What With From Into Onto
    Upon After Before While Where Which Within Without Because Though Although
    However Another Other Each Every Some Many Most Such Being Been Being Your
    You Their His Her Its Our Theirs Into Onto In At To By On Of As If We She Her
    """.split()
)

_TITLE_NAME = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

# Bounded to two title-case tokens (avoids swallowing trailing "Captain …" on same line).
_PREP_LOCATION = re.compile(
    r"\b(?:at|in|to|from|inside|outside|within|near|toward|towards)\s+"
    r"(?:the\s+)?([A-Z][\w']*(?:\s+[A-Z][\w']*){0,1})\b",
    re.I,
)

_ROLE_NAME = re.compile(
    r"\b(?:Captain|Sergeant|Lieutenant|Guard|Lord|Lady|Magistrate|Innkeeper|Merchant|"
    r"Bishop|Abbot|Scribe|Herald|Warden|Smith)\s+([A-Z][a-z]+)\b"
)

_OBJECT_PHRASE = re.compile(
    r"\b(?:the|your|his|her|their)\s+([a-z]{3,12})\s+(?:key|blade|sword|letter|seal|map|ring|coin|coins|lock|box|crate)\b",
    re.I,
)

_CALLBACK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bagain\b", re.I),
    re.compile(r"\bstill\b", re.I),
    re.compile(r"\bearlier\b", re.I),
    re.compile(r"\bpreviously\b", re.I),
    re.compile(r"\bas before\b", re.I),
    re.compile(r"\bback at\b", re.I),
    re.compile(r"\bthe same\s+\w+\b", re.I),
    re.compile(r"\breturning to\b", re.I),
    re.compile(r"\byou recall\b", re.I),
    re.compile(r"\breminds you\b", re.I),
)

_TRANSITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:later|eventually|meanwhile)\b", re.I),
    re.compile(r"\bafter a (?:while|moment|time)\b", re.I),
    re.compile(r"\bonce you (?:arrive|reach|enter|leave|step)\b", re.I),
    re.compile(r"\bback at\b", re.I),
    re.compile(r"\breturning to\b", re.I),
    re.compile(r"\bthe next (?:morning|day|evening|night|dawn)\b", re.I),
    re.compile(r"\bby the time\b", re.I),
    re.compile(r"\bafter leaving\b", re.I),
    re.compile(r"\bwhen you reach\b", re.I),
    re.compile(r"\bafter you (?:leave|arrive|step|enter)\b", re.I),
    re.compile(r"\bthe road carries you\b", re.I),
    re.compile(r"\bhours later\b", re.I),
    re.compile(r"\bthe journey\b", re.I),
)

_STARK_RESET = re.compile(
    r"\b(?:all at once|suddenly),?\s+you\s+(?:are|find yourself|stand)\b|\b"
    r"you\s+snap awake\b|\bwithout warning,?\s+you\b",
    re.I,
)


def _title_case_names(text: str) -> set[str]:
    found: set[str] = set()
    for m in _TITLE_NAME.finditer(text):
        phrase = m.group(1).strip()
        parts = phrase.split()
        if parts and parts[0] in _TITLE_BLOCK:
            continue
        if 2 <= len(parts) <= 4:
            found.add(phrase)
    return found


def _prep_locations(text: str) -> set[str]:
    out: set[str] = set()
    for m in _PREP_LOCATION.finditer(text):
        loc = m.group(1).strip()
        parts = loc.split()
        if parts and parts[0] in _TITLE_BLOCK:
            continue
        if len(loc) >= 3:
            out.add(loc)
    return out


def _role_names(text: str) -> dict[str, str]:
    """role_keyword -> given name (last wins)."""
    d: dict[str, str] = {}
    for m in _ROLE_NAME.finditer(text):
        role = m.group(0).rsplit(" ", 1)[0]
        given = m.group(1)
        d[role.lower()] = given
    return d


def _object_tokens(text: str) -> set[str]:
    s: set[str] = set()
    for m in _OBJECT_PHRASE.finditer(text):
        s.add(m.group(0).lower())
    return s


def _count_callbacks(text: str) -> int:
    n = 0
    for pat in _CALLBACK_PATTERNS:
        n += len(pat.findall(text))
    return n


def _has_transition(text: str) -> bool:
    return any(p.search(text) for p in _TRANSITION_PATTERNS)


def _normalize_turn_history(turn_history: Any) -> list[Mapping[str, Any]]:
    if turn_history is None:
        return []
    if not isinstance(turn_history, Sequence) or isinstance(turn_history, (str, bytes)):
        return []
    out: list[Mapping[str, Any]] = []
    for item in turn_history:
        if len(out) >= _MAX_TURNS:
            break
        if not isinstance(item, Mapping):
            continue
        # Drop obvious debug-only dicts
        if item and all(isinstance(k, str) and k.lower() in _DEBUG_KEYS for k in item):
            continue
        out.append(item)
    return out


def evaluate_session_cohesion(turn_history: Any) -> dict[str, Any]:
    """Score obvious continuity across a short recent window (deterministic).

    *turn_history*: 5–20 turns typical; accepts sparse / partial dict-like rows.

    Returns ``cohesive`` (True if score >= 0.75), ``memory_failures``,
    ``callback_hits``, ``notes``, ``tracked_entities``, and ``score`` in
    ``{0.0, 0.5, 1.0}`` (weak evidence stays partial, not hard failure).
    """
    notes: list[str] = ["ruleset:session_cohesion_v1"]
    notes.append(
        "anti_fp:transition_phrase_suppression;sparse_history_suppression;"
        "no_penalty_one_turn_entity_absence;bounded_extraction;no_coref_nlp"
    )

    turns = _normalize_turn_history(turn_history)
    narr_rows: list[str] = []
    scene_hints: list[str] = []
    for t in turns:
        narr = _strip_debug_blobs(extract_player_facing_text(t))
        if len(narr) > _MAX_CHARS_PER_TURN:
            narr = narr[:_MAX_CHARS_PER_TURN]
        narr_rows.append(narr)
        scene_hints.append(extract_scene_hint(t))

    usable = sum(1 for n, s in zip(narr_rows, scene_hints) if _meaningful_turn(n, s))
    joined_narr = "\n".join(narr_rows)
    callback_hits = _count_callbacks(joined_narr)
    if usable == 0:
        notes.append("sparse:no_meaningful_turns")
        return {
            "cohesive": False,
            "memory_failures": 0,
            "callback_hits": callback_hits,
            "notes": notes,
            "tracked_entities": {"npcs": [], "locations": [], "objects": []},
            "score": 0.5,
        }

    if usable < 3:
        notes.append(f"sparse:usable_turns={usable}")

    # Per-turn entity bags
    per_locs: list[set[str]] = []
    per_names: list[set[str]] = []
    per_roles: list[dict[str, str]] = []
    per_objs: list[set[str]] = []
    for narr, hint in zip(narr_rows, scene_hints):
        blob = narr
        if hint:
            blob = f"{hint}\n{narr}"
        per_locs.append(_prep_locations(blob) | ({hint} if hint else set()))
        per_names.append(_title_case_names(narr))
        per_roles.append(_role_names(narr))
        per_objs.append(_object_tokens(narr))

    # Establish locations: appear in >= 2 turn indices (anti_fp: one-turn absence OK)
    loc_turn_index: dict[str, set[int]] = {}
    for i, ls in enumerate(per_locs):
        for loc in ls:
            if not loc:
                continue
            loc_turn_index.setdefault(loc, set()).add(i)
    established_locs = {loc for loc, idxs in loc_turn_index.items() if len(idxs) >= 2}

    name_turn_index: dict[str, set[int]] = {}
    for i, ns in enumerate(per_names):
        for nm in ns:
            name_turn_index.setdefault(nm, set()).add(i)
    established_names = {nm for nm, idxs in name_turn_index.items() if len(idxs) >= 2}

    obj_turn_index: dict[str, set[int]] = {}
    for i, os_ in enumerate(per_objs):
        for o in os_:
            obj_turn_index.setdefault(o, set()).add(i)
    established_objs = {o for o, idxs in obj_turn_index.items() if len(idxs) >= 2}

    def _object_tail_map(phrases: set[str]) -> dict[str, str]:
        """Map object lemma (last token) -> full phrase."""
        m: dict[str, str] = {}
        for p in phrases:
            parts = p.split()
            if not parts:
                continue
            m[parts[-1]] = p
        return m

    memory_failures = 0
    transition_edges = 0
    # Adjacent continuity
    for i in range(1, len(narr_rows)):
        prev_n, cur_n = narr_rows[i - 1], narr_rows[i]
        if not _meaningful_turn(prev_n, scene_hints[i - 1]) or not _meaningful_turn(cur_n, scene_hints[i]):
            continue
        bridge = (prev_n[-180:] if len(prev_n) > 180 else prev_n) + " " + (cur_n[:180] if len(cur_n) > 180 else cur_n)
        if _has_transition(bridge):
            transition_edges += 1
            continue

        edge_failed = False
        edge_issues = 0

        L_prev, L_cur = per_locs[i - 1], per_locs[i]
        # Location: both sides have cues, disjoint, and previous had an established anchor
        if L_prev and L_cur and L_prev.isdisjoint(L_cur):
            prev_est = L_prev & established_locs
            if prev_est:
                edge_issues += 1
                edge_failed = True
                notes.append(f"failure:disjoint_locations:{i - 1}->{i}")

        # Stark reset cue + disjoint locations (one failure per edge)
        if (
            not edge_failed
            and _STARK_RESET.search(bridge)
            and L_prev
            and L_cur
            and L_prev.isdisjoint(L_cur)
        ):
            edge_issues += 1
            notes.append(f"failure:stark_reset_location:{i - 1}->{i}")

        # Role / name slot drift (same role keyword, different given name)
        if edge_issues == 0:
            R_prev, R_cur = per_roles[i - 1], per_roles[i]
            for role_key, name_prev in R_prev.items():
                if role_key in R_cur and R_cur[role_key] != name_prev:
                    edge_issues += 1
                    notes.append(f"failure:role_name_drift:{role_key}:{i - 1}->{i}")
                    break

        # Object phrase drift: same object lemma (key, blade, …), different full phrase, adjacent
        if edge_issues == 0:
            O_prev, O_cur = per_objs[i - 1], per_objs[i]
            if O_prev and O_cur:
                tm_p, tm_c = _object_tail_map(O_prev), _object_tail_map(O_cur)
                est_tails = {p.split()[-1] for p in established_objs}
                for tail, phrase_p in tm_p.items():
                    if tail in tm_c and tm_c[tail] != phrase_p:
                        if tail in est_tails:
                            edge_issues += 1
                            notes.append(f"failure:object_lemma_drift:{tail}:{i - 1}->{i}")
                            break
        if edge_issues:
            memory_failures += 1
    if transition_edges:
        notes.append(f"anti_fp:transition_suppressed_edges:{transition_edges}")

    # Continuity-positive: repeated mentions across turns (same string in 2+ indices)
    entity_reuse = len(established_locs) + len(established_names) + len(established_objs)
    positive_signal = entity_reuse > 0 or callback_hits > 0

    # Score
    if memory_failures >= 2:
        score = 0.0
        notes.append("score_rule:multiple_failures->0.0")
    elif memory_failures == 1:
        score = 0.5
        notes.append("score_rule:single_failure->0.5")
    elif usable < 3:
        if memory_failures == 0 and (callback_hits >= 2 or entity_reuse > 0):
            score = 1.0
            notes.append("score_rule:sparse_but_strong_continuity_signals->1.0")
        else:
            score = 0.5
            notes.append("score_rule:sparse_usable->0.5")
    elif positive_signal:
        score = 1.0
        notes.append("score_rule:zero_failures_positive_signal->1.0")
    else:
        # Enough turns but no strong reuse/callback — partial, not failure
        score = 0.5
        notes.append("score_rule:mixed_no_strong_signal->0.5")

    cohesive = score >= 0.75

    # Tracked entities (human-readable, capped)
    def _top(counter: Counter[str], cap: int = 12) -> list[str]:
        return [k for k, _ in counter.most_common(cap)]

    npc_c: Counter[str] = Counter()
    for ns in per_names:
        npc_c.update(ns)
    for d in per_roles:
        for role, given in d.items():
            npc_c[f"{role.title()} {given}"] += 1

    loc_c: Counter[str] = Counter()
    for ls in per_locs:
        loc_c.update(ls)

    obj_c: Counter[str] = Counter()
    for os_ in per_objs:
        obj_c.update(os_)

    tracked = {
        "npcs": _top(npc_c),
        "locations": _top(loc_c),
        "objects": _top(obj_c),
    }

    return {
        "cohesive": cohesive,
        "memory_failures": memory_failures,
        "callback_hits": callback_hits,
        "notes": notes[:48] + (["notes:truncated"] if len(notes) > 48 else []),
        "tracked_entities": tracked,
        "score": float(score),
    }


def _resolve_turn_history_arg(
    session: Mapping[str, Any] | None,
    turn_history: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]] | None:
    """Use explicit *turn_history* or optional session hook (no API wiring)."""
    if turn_history is not None:
        if isinstance(turn_history, Sequence) and not isinstance(turn_history, (str, bytes)):
            return list(turn_history)  # type: ignore[arg-type]
        return None
    if not isinstance(session, dict):
        return None
    hook = session.get("session_cohesion_turn_history")
    if isinstance(hook, list) and hook:
        return hook  # type: ignore[return-value]
    return None


def maybe_attach_session_cohesion_eval(
    session: Mapping[str, Any] | None,
    *,
    turn_history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """If ``ASGM_RECORD_SESSION_COHESION_EVAL`` is set, attach eval to ``session['last_action_debug']``.

    *turn_history* may be passed explicitly (gauntlets / tests). If omitted, a
    non-invasive optional hook reads ``session['session_cohesion_turn_history']``
    when present (list of turn dicts). Otherwise no-op. Does not change
    player-facing text.
    """
    if not _truthy_env("ASGM_RECORD_SESSION_COHESION_EVAL"):
        return None
    resolved = _resolve_turn_history_arg(session, turn_history)
    if not resolved:
        return None
    if not isinstance(session, dict):
        return None
    lad = session.get("last_action_debug")
    if not isinstance(lad, dict):
        return None
    payload = evaluate_session_cohesion(resolved)
    lad["session_cohesion_eval"] = payload
    return payload
