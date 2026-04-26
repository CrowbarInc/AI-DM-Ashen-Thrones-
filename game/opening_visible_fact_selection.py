"""Curate visible facts for opening-scene narration prompts only.

Full scene state keeps all visible_facts; this layer shrinks the prompt slice so
the model is not fed dozens of overlapping strings. Post-turn validation still
uses :func:`game.narration_visibility.build_narration_visibility_contract` from
authoritative scene data (full fact list).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from game.narration_visibility import _normalize_visibility_text

# Responsible for: scoring + selecting canonical facts
# Must NOT:
#   - access runtime overlays
#   - perform narrative shaping

OPENING_NARRATION_VISIBLE_FACT_MAX = 7

_STOPWORDS = frozenset({
    "that", "this", "with", "from", "into", "onto", "over", "under", "near",
    "there", "here", "they", "them", "their", "than", "then", "some", "many",
    "much", "very", "just", "only", "also", "still", "even", "been", "have",
    "has", "had", "were", "was", "are", "is", "and", "but", "for", "not",
    "you", "your", "the", "a", "an",
})

# Near-duplicate suppression: first match wins (deterministic order).
_TOPIC_CLUSTERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("patrol", ("missing patrol", "last patrol", "night patrol", "day patrol", "patrol", "sentry", "watchpost")),
    ("runner", ("tavern runner", "drink runner", "runner")),
    ("guard", ("spear-butt", "checkpoint", "guards", "guard")),
    ("crowd", ("onlooker", "onlookers", "watcher", "watchers", "murmur", "murmurs", "whisper", "whispers")),
    ("crate_alley", ("loading dock", "alleyway", "alley", "crates", "crate")),
    ("tension", ("agitation", "unrest", "uneasy", "tension")),
)

# Primary bucket (one per fact). Check specific hooks before broad environment.
_D_KEYWORDS = (
    "posted", "parchment", "notice", "notices", "sign", "signs", "bulletin",
    "board", "placard", "trail", "path",
    "east-road", "west-road", "road east", "road west", "speak with", "talk to",
)
_C_KEYWORDS = (
    "barkeep", "innkeeper", "merchant", "vendor", "steward", "clerk", "patron",
    "runner", "captain", "sergeant", "officer",     "beckon", "beckons", "gesture",
    "gestures", "approach", "approaches", "hail", "hails", "waves",
    " watching you", "watch you", "stares at", "stare at", "calls out",
)
_B_KEYWORDS = (
    "crowd", "crowds", "queue", "press", "pressing", "jostle", "jostling",
    "shout", "shouts", "panic", "urgent", "urgency", "hurry", "hurries",
)
_E_KEYWORDS = (
    "smell", "scent", "reek", "sound", "song", "din", "light", "shadow",
    "glow", "glimmer", "dusk", "dawn", "chill", "warmth", "breeze", "wind",
)
_A_KEYWORDS = (
    "gate", "wall", "walls", "square", "yard", "courtyard", "checkpoint",
    "district", "tavern", "inn ", " inn", "chamber", "hall", "bazaar", "market",
    "stall", "banner", "banners", "stone", "mud", "muddy", "rain", "snow",
    "fog", "mist", "ash", "smoke", "brazier", "torch", "lantern", "floor",
    "ceiling", "roof", "building", "architecture", "road", "street", "bridge",
)

_ACTOR_KEYWORDS = (
    "actor", "npc", "guard", "guards", "captain", "sergeant", "officer", "runner",
    "barkeep", "innkeeper", "merchant", "vendor", "steward", "clerk", "patron",
    "refugee", "refugees", "crowd", "crowds", "onlooker", "onlookers",
)
_ACTION_VERB_KEYWORDS = (
    "waves", "wave", "calls", "call", "scans", "scan", "argues", "argue",
    "shouts", "shout", "gestures", "gesture", "beckons", "beckon", "watches",
    "watch", "presses", "press", "jostles", "jostle", "haggles", "haggle",
    "holds", "hold", "moves", "move", "waits", "wait", "lingers", "linger",
)
_TENSION_KEYWORDS = (
    "crowd", "pressure", "guards", "guard", "curfew", "missing", "warning",
    "warns", "posted", "tax", "taxes", "press", "urgent", "panic", "unrest",
    "uneasy", "suspicious", "wary", "choke",
)
_AFFORDANCE_KEYWORDS = (
    "notice", "vendor", "gate", "guard", "guards", "interaction", "runner",
    "merchant", "barkeep", "board", "sign", "posted", "door", "path", "road",
    "trail", "stall", "checkpoint",
)
_BACKSTAGE_SELECTION_MARKERS = (
    "backstage",
    "gm hint",
    "gm note",
    "hidden fact",
    "who controls",
    "vital information",
    "manages patrol",
    "patrol assignments",
    "controls patrol",
)

_CATEGORY_RANK = {"A": 0, "E": 0, "B": 1, "C": 2, "D": 3}

_NON_OPENING_LIFECYCLES = frozenset({
    "runtime_observation",
    "discovered_clue",
    "investigation_result",
    "pc_specific",
    "gm_generated",
    "post_start_state",
})
_FORM_REJECTION_MARKERS = (
    "upon closer inspection",
    "examining ",
    "examining the ",
    "reveals ",
    " reveal ",
    "revealed ",
    "suggesting ",
    " suggests ",
    "appears to have",
    "appear to have",
    "has recently",
    "have recently",
    "recently posted",
    "after you ",
    "after the player ",
    "as you ",
)
_HIDDEN_VISIBILITY_VALUES = frozenset({"hidden", "gm_only", "backstage", "secret", "undiscovered"})


def _norm_hits(norm: str, needles: Tuple[str, ...]) -> bool:
    return any(n in norm for n in needles)


def _string_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(x).strip() for x in value if isinstance(x, str) and str(x).strip()]
    return []


def _fact_text_and_metadata(raw: Any) -> Tuple[str, Dict[str, Any]] | None:
    if isinstance(raw, str):
        text = " ".join(raw.split()).strip()
        return (text, {}) if text else None
    if not isinstance(raw, Mapping):
        return None
    text = ""
    for key in ("text", "fact", "line", "value", "description"):
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            text = " ".join(val.split()).strip()
            break
    if not text:
        return None
    metadata: Dict[str, Any] = {}
    nested = raw.get("metadata")
    if isinstance(nested, Mapping):
        metadata.update(dict(nested))
    for key in ("source", "lifecycle", "tags", "tag", "visibility", "immediately_observable", "pc_specific"):
        if key in raw and key not in metadata:
            metadata[key] = raw.get(key)
    return text, metadata


def _fact_rows(raw: Any, *, source: str) -> List[Tuple[str, Dict[str, Any]]]:
    if not isinstance(raw, list):
        return []
    rows: List[Tuple[str, Dict[str, Any]]] = []
    for item in raw:
        parsed = _fact_text_and_metadata(item)
        if not parsed:
            continue
        text, metadata = parsed
        md = dict(metadata)
        md.setdefault("source", source)
        rows.append((text, md))
    return rows


def _campaign_spine_opening_rows(public_scene: Mapping[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Return explicit opening facts supplied by a campaign/scenario spine."""
    sources: List[Any] = [
        public_scene.get("campaign_spine_opening_facts"),
        public_scene.get("spine_opening_facts"),
    ]
    for container_key in ("campaign_spine", "scenario_spine", "spine"):
        container = public_scene.get(container_key)
        if isinstance(container, Mapping):
            sources.extend(
                [
                    container.get("opening_seed_facts"),
                    container.get("opening_facts"),
                    container.get("scene_opening_facts"),
                ]
            )
    rows: List[Tuple[str, Dict[str, Any]]] = []
    for raw in sources:
        rows.extend(_fact_rows(raw, source="campaign_spine_opening_facts"))
    return rows


def _metadata_lifecycle_values(metadata: Mapping[str, Any] | None) -> Set[str]:
    md = metadata if isinstance(metadata, Mapping) else {}
    values: Set[str] = set()
    for key in ("lifecycle", "source"):
        raw = md.get(key)
        if isinstance(raw, str) and raw.strip():
            values.add(raw.strip().lower())
    for key in ("tag", "tags", "lifecycle_tags"):
        for item in _string_list(md.get(key)):
            values.add(item.strip().lower())
    return values


def _metadata_hidden_or_pc_specific(metadata: Mapping[str, Any] | None) -> bool:
    md = metadata if isinstance(metadata, Mapping) else {}
    if md.get("pc_specific") is True:
        return True
    if md.get("immediately_observable") is False:
        return True
    visibility = str(md.get("visibility") or "").strip().lower()
    return bool(visibility and visibility in _HIDDEN_VISIBILITY_VALUES)


def _player_specific_markers(metadata: Mapping[str, Any] | None) -> Set[str]:
    md = metadata if isinstance(metadata, Mapping) else {}
    out: Set[str] = set()

    def _add_name(raw: Any) -> None:
        if isinstance(raw, str):
            n = _normalize_visibility_text(raw)
            if n:
                out.add(n)
        elif isinstance(raw, Mapping):
            for key in ("name", "display_name", "pc_name", "character_name", "player_name"):
                val = raw.get(key)
                if isinstance(val, str):
                    n = _normalize_visibility_text(val)
                    if n:
                        out.add(n)
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
            for item in raw:
                _add_name(item)

    for key in (
        "player_name",
        "pc_name",
        "character_name",
        "player_names",
        "pc_names",
        "character_names",
        "player_context",
        "character",
        "session_player_context",
    ):
        _add_name(md.get(key))
    return {m for m in out if len(m) >= 3}


def _opening_fact_rejection_reason(fact: str, metadata: Mapping[str, Any] | None = None) -> str | None:
    text = " ".join(str(fact or "").split()).strip()
    if not text:
        return "form"
    norm = _normalize_visibility_text(text)
    if not norm:
        return "form"

    lifecycle_values = _metadata_lifecycle_values(metadata)
    if lifecycle_values & _NON_OPENING_LIFECYCLES:
        return "lifecycle"
    if _metadata_hidden_or_pc_specific(metadata):
        return "lifecycle"

    if _norm_hits(norm, _BACKSTAGE_SELECTION_MARKERS):
        return "form"
    if _norm_hits(norm, _FORM_REJECTION_MARKERS):
        return "form"
    for marker in _player_specific_markers(metadata):
        if marker and marker in norm:
            return "form"
    return None


def is_opening_eligible_fact(fact: str, metadata: Mapping[str, Any] | None = None) -> bool:
    """Return whether a fact is safe to use as opening narration basis.

    Eligibility is based on provenance/lifecycle metadata and sentence form, not
    on hardcoded entity or role-name blacklists.
    """
    return _opening_fact_rejection_reason(fact, metadata) is None


def opening_fact_primary_category(norm: str) -> str:
    """Single-letter category for ordering and slot filling (deterministic).

    Social/person hooks (C) before generic actionable phrasing (D) so lines like
    "runner … toward the side door" classify as social, not as a door affordance.
    """
    if _norm_hits(norm, _C_KEYWORDS):
        return "C"
    if _norm_hits(norm, _D_KEYWORDS):
        return "D"
    if _norm_hits(norm, _B_KEYWORDS):
        return "B"
    if _norm_hits(norm, _E_KEYWORDS):
        return "E"
    if _norm_hits(norm, _A_KEYWORDS):
        return "A"
    return "A"


def opening_fact_has_actor(norm: str) -> bool:
    return _norm_hits(norm, _ACTOR_KEYWORDS)


def opening_fact_has_activity(norm: str) -> bool:
    return _norm_hits(norm, _ACTION_VERB_KEYWORDS)


def opening_fact_has_tension(norm: str) -> bool:
    return _norm_hits(norm, _TENSION_KEYWORDS)


def opening_fact_has_affordance(norm: str) -> bool:
    return _norm_hits(norm, _AFFORDANCE_KEYWORDS)


def opening_fact_score(norm: str) -> int:
    score = 0
    if opening_fact_has_actor(norm):
        score += 2
    if opening_fact_has_activity(norm):
        score += 2
    if opening_fact_has_tension(norm):
        score += 1
    if opening_fact_has_affordance(norm):
        score += 1
    return score


def _dominant_cluster(norm: str) -> str:
    for cid, phrases in _TOPIC_CLUSTERS:
        for p in phrases:
            if p in norm:
                return cid
    return ""


def _content_tokens(norm: str) -> Set[str]:
    raw = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in norm.lower())
    out: Set[str] = set()
    for w in raw.split():
        if len(w) >= 4 and w not in _STOPWORDS:
            out.add(w)
    return out


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union or 1)


def _candidate_rows_from_public_scene(
    public_scene: Mapping[str, Any],
    *,
    eligibility_metadata: Mapping[str, Any] | None = None,
) -> Tuple[List[Tuple[str, str]], Dict[str, Any]]:
    ps = public_scene if isinstance(public_scene, Mapping) else {}
    opening_rows = _fact_rows(ps.get("opening_seed_facts"), source="opening_seed_facts")
    spine_rows = _campaign_spine_opening_rows(ps)

    source_used = "none"
    eligibility_mode = "none"
    rows: List[Tuple[str, Dict[str, Any]]] = []
    if opening_rows:
        rows = opening_rows
        source_used = "opening_seed_facts"
        eligibility_mode = "explicit_source"
    elif spine_rows:
        rows = spine_rows
        source_used = "campaign_spine_opening_facts"
        eligibility_mode = "explicit_source"

    base_md = dict(eligibility_metadata or {})
    seen_norm: Set[str] = set()
    pairs: List[Tuple[str, str]] = []
    rejected_by_lifecycle = 0
    rejected_by_form = 0
    for original, metadata in rows:
        md = {**base_md, **metadata}
        reason = _opening_fact_rejection_reason(original, md)
        if reason == "lifecycle":
            rejected_by_lifecycle += 1
            continue
        if reason == "form":
            rejected_by_form += 1
            continue
        n = _normalize_visibility_text(original)
        if not n or n in seen_norm:
            continue
        seen_norm.add(n)
        pairs.append((original, n))
    telemetry = {
        "opening_fact_source_used": source_used,
        "opening_fact_eligibility_mode": eligibility_mode,
        "opening_fact_rejected_by_lifecycle_count": rejected_by_lifecycle,
        "opening_fact_rejected_by_form_count": rejected_by_form,
    }
    return pairs, telemetry


_DEDUPE_ANCHOR_SUBSTRINGS: Tuple[str, ...] = (
    "patrol",
    "runner",
    "checkpoint",
    "refugee",
    "refugees",
)


def _would_collide(
    norm: str,
    tokens: Set[str],
    cluster: str,
    *,
    chosen_norms: List[str],
    chosen_tokens: List[Set[str]],
    used_clusters: Set[str],
    jaccard_threshold: float = 0.48,
) -> bool:
    if cluster and cluster in used_clusters:
        return True
    for anchor in _DEDUPE_ANCHOR_SUBSTRINGS:
        if anchor in norm and any(anchor in prev for prev in chosen_norms):
            return True
    for prev_norm, prev_toks in zip(chosen_norms, chosen_tokens):
        if norm == prev_norm:
            return True
        if _jaccard(tokens, prev_toks) >= jaccard_threshold:
            return True
        # Substantial substring containment (catch "patrol missing" vs "missing patrol")
        shorter, longer = (norm, prev_norm) if len(norm) <= len(prev_norm) else (prev_norm, norm)
        if len(shorter) >= 24 and shorter in longer:
            return True
    return False


def _try_take(
    rec: Dict[str, Any],
    selected: List[Dict[str, Any]],
    used_clusters: Set[str],
) -> bool:
    if _would_collide(
        rec["norm"],
        rec["tokens"],
        rec["cluster"],
        chosen_norms=[r["norm"] for r in selected],
        chosen_tokens=[r["tokens"] for r in selected],
        used_clusters=used_clusters,
    ):
        return False
    selected.append(rec)
    if rec["cluster"]:
        used_clusters.add(rec["cluster"])
    return True


def select_opening_narration_visible_facts(
    public_scene: Mapping[str, Any] | None,
    *,
    max_facts: int = OPENING_NARRATION_VISIBLE_FACT_MAX,
    eligibility_metadata: Mapping[str, Any] | None = None,
) -> List[str]:
    """Return up to *max_facts* curated visible fact strings for opening prompts."""
    selected, _telemetry = select_opening_narration_visible_facts_with_telemetry(
        public_scene,
        max_facts=max_facts,
        eligibility_metadata=eligibility_metadata,
    )
    return selected


def select_opening_narration_visible_facts_with_telemetry(
    public_scene: Mapping[str, Any] | None,
    *,
    max_facts: int = OPENING_NARRATION_VISIBLE_FACT_MAX,
    eligibility_metadata: Mapping[str, Any] | None = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """Return curated opening facts plus provenance/eligibility telemetry."""
    cap = int(max_facts)
    empty_meta = {
        "opening_fact_source_used": "none",
        "opening_fact_eligibility_mode": "none",
        "opening_fact_rejected_by_lifecycle_count": 0,
        "opening_fact_rejected_by_form_count": 0,
    }
    if cap < 1:
        return [], empty_meta
    ps = public_scene if isinstance(public_scene, Mapping) else {}
    pairs, telemetry = _candidate_rows_from_public_scene(ps, eligibility_metadata=eligibility_metadata)
    if not pairs:
        return [], telemetry
    if len(pairs) == 1:
        return [pairs[0][0]], telemetry

    records: List[Dict[str, Any]] = []
    for idx, (original, norm) in enumerate(pairs):
        records.append(
            {
                "original": original,
                "norm": norm,
                "tokens": _content_tokens(norm),
                "category": opening_fact_primary_category(norm),
                "score": opening_fact_score(norm),
                "has_actor": opening_fact_has_actor(norm),
                "has_activity": opening_fact_has_activity(norm),
                "has_tension": opening_fact_has_tension(norm),
                "has_affordance": opening_fact_has_affordance(norm),
                "cluster": _dominant_cluster(norm),
                "index": idx,
            }
        )

    by_cat: Dict[str, List[Dict[str, Any]]] = {"A": [], "B": [], "C": [], "D": [], "E": []}
    for rec in records:
        by_cat[rec["category"]].append(rec)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda r: (-int(r["score"]), int(r["index"])))

    selected: List[Dict[str, Any]] = []
    used_clusters: Set[str] = set()

    def _take_from_cat(cat: str, limit: int) -> None:
        nonlocal selected, used_clusters
        if len(selected) >= cap:
            return
        for rec in by_cat.get(cat, []):
            if len(selected) >= cap:
                break
            if limit <= 0:
                break
            if _try_take(rec, selected, used_clusters):
                limit -= 1

    # Slot template: A, B, up to 2×C, D, optional E — then back-fill.
    _take_from_cat("A", 1)
    _take_from_cat("B", 1)
    _take_from_cat("C", 2)
    _take_from_cat("D", 1)
    _take_from_cat("E", 1)

    has_c = any(r["category"] == "C" for r in selected)
    has_d = any(r["category"] == "D" for r in selected)
    if not has_c:
        for rec in by_cat["C"]:
            if len(selected) >= cap:
                break
            _try_take(rec, selected, used_clusters)
    if not has_d:
        for rec in by_cat["D"]:
            if len(selected) >= cap:
                break
            _try_take(rec, selected, used_clusters)

    # Back-fill in priority order A→E, original index order within category.
    if len(selected) < cap:
        for cat in ("A", "E", "B", "C", "D"):
            if len(selected) >= cap:
                break
            for rec in by_cat[cat]:
                if len(selected) >= cap:
                    break
                if rec in selected:
                    continue
                _try_take(rec, selected, used_clusters)

    def _has_sensory_spatial(rows: List[Dict[str, Any]]) -> bool:
        return any(r["category"] in {"A", "E"} for r in rows)

    def _has_social_actor(rows: List[Dict[str, Any]]) -> bool:
        return any(r["category"] in {"B", "C"} or bool(r.get("has_actor")) for r in rows)

    def _has_tension_or_affordance(rows: List[Dict[str, Any]]) -> bool:
        return any(bool(r.get("has_tension")) or bool(r.get("has_affordance")) for r in rows)

    def _add_required(predicate) -> None:
        nonlocal selected, used_clusters
        if predicate(selected):
            return
        candidates = [r for r in records if r not in selected and predicate([r])]
        candidates.sort(key=lambda r: (_CATEGORY_RANK.get(r["category"], 9), -int(r["score"]), int(r["index"])))
        for rec in candidates:
            if len(selected) < cap:
                if _try_take(rec, selected, used_clusters):
                    return
                continue
            replaceable = sorted(
                selected,
                key=lambda r: (-_CATEGORY_RANK.get(r["category"], 9), int(r["score"]), -int(r["index"])),
            )
            for old in replaceable:
                trial = [r for r in selected if r is not old] + [rec]
                if _has_sensory_spatial(trial) and _has_social_actor(trial) and _has_tension_or_affordance(trial):
                    selected = trial
                    used_clusters = {str(r["cluster"]) for r in selected if r.get("cluster")}
                    return

    _add_required(_has_sensory_spatial)
    _add_required(_has_social_actor)
    _add_required(_has_tension_or_affordance)

    selected.sort(key=lambda r: (_CATEGORY_RANK.get(r["category"], 9), -int(r["score"]), int(r["index"])))
    out = [str(r["original"]) for r in selected[:cap]]
    return out, telemetry
