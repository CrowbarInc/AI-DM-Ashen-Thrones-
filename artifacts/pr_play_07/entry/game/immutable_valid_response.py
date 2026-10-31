"""Preserve a hard-valid model response. Regenerate once. Then stop.

Deterministic authority still owns canonical state, mechanics, permissions,
PR-BN classes, consequential inventions, and what may be committed. It does
not author a replacement sentence after a generated response has passed the
hard-validation boundary.

Presentation-only differences (whitespace and simple markup) may remain.
Meaning, speaker, target, operation, and state implication may not.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Callable, Mapping

MAX_GENERATION_ATTEMPTS = 2

PROVENANCE_INITIAL = "initial_generation"
PROVENANCE_REGENERATION = "regeneration"
PROVENANCE_AUTHORED_PROJECTION = "authored_answer_projection"
PROVENANCE_SAFE = "safe_nonresolution"
PROVENANCE_REJECTED = "rejected"

ACCEPTED_KEY = "accepted_response"
TERMINAL_FALLBACK = "I cannot provide a validated response to that request."


def seal_delivery_contract(gm: dict[str, Any]) -> None:
    """Pin the existing adoption record; only authorization code calls this.

    The immutable JSON value is a response seal, not another history or world
    store. Mutable diagnostic dictionaries cannot change the adopted identity.
    """
    record = gm.get("metadata", {}).get(ACCEPTED_KEY)
    if not isinstance(record, dict) or record.get("immutable") is not True:
        return
    record.setdefault("subject", record.get("target", ""))
    record.setdefault("authorization_source", record.get("provenance", ""))
    record.setdefault("adoption_status", "safe_fallback_selected" if record.get("provenance") == PROVENANCE_SAFE else "candidate_accepted")
    payload = {k: v for k, v in record.items() if k not in {"integrity_digest", "skipped_mutators"}}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    record["integrity_digest"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    gm["_final_delivery_seal"] = raw


def verify_delivery_record(record: Mapping[str, Any]) -> bool:
    payload = {k: v for k, v in record.items() if k not in {"integrity_digest", "skipped_mutators"}}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return record.get("integrity_digest") == hashlib.sha256(raw.encode("utf-8")).hexdigest()

_STOP = frozenset(
    {
        "the", "a", "an", "of", "on", "to", "and", "or", "at", "for", "with",
        "from", "into", "over", "that", "this", "nearest", "holding", "line",
        "them", "they", "you", "your", "his", "her", "their",
    }
)
_LOCATE_RE = re.compile(
    r"\b(?:find|locate|look for|go find|need to find|have to find)\b",
    re.IGNORECASE,
)
_CLOCK_RE = re.compile(
    r"\bless than\s+\w+\s+hours?\b|\bdusk sharp\b|\b\d{1,2}:\d{2}\b",
    re.IGNORECASE,
)
_QUOTE_RE = re.compile(r'["“][^"”]*["”]')
_SUCCESS_NARRATION_RE = re.compile(
    r"\b(?:you hit|the blow lands|the attack hits|you succeed|the strike lands)\b",
    re.IGNORECASE,
)
_FAILURE_NARRATION_RE = re.compile(
    r"\b(?:you miss|the attack misses|you fail to hit|the blow misses)\b",
    re.IGNORECASE,
)
_NEGATION_RE = re.compile(r"\b(?:miss|fail|not|n't|never)\b", re.IGNORECASE)
_LEAK_RE = re.compile(
    r"\b(?:the secret is|hidden fact:|do not reveal|gm_only)\b",
    re.IGNORECASE,
)
_ADDRESS_RE = re.compile(
    r"\b(?:ask|asking|face|facing|approach(?:ing)?|address(?:ing)?|"
    r"speak to|talk to|turn to|step up to|walk over to)\s+"
    r"(?:the\s+|a\s+|an\s+|nearest\s+)?(?P<nominal>[a-z][^?.!]{0,48})",
    re.IGNORECASE,
)
_QUESTION_NOMINAL_RE = re.compile(
    r"^(?:what|whether|how|who|where|when|why|if|calmly|quietly|directly)\b",
    re.IGNORECASE,
)
_ROLE_RE = re.compile(
    r"\b(?:guard|captain|runner|watcher|serjeant|sergeant|merchant|clerk|figure|sentry)\b",
    re.IGNORECASE,
)
_SPEECH_ATTRIB_RE = re.compile(
    r"\b(?:says|said|replies|replied|answers|answered|asks|asked|mutters|whispers)\b",
    re.IGNORECASE,
)
_SPLICE_TEMPLATE_RE = re.compile(
    r"\b(?:couldn'?t|could not)\s+tell you\b",
    re.IGNORECASE,
)
_DIMENSION_LEXICON = {
    "smell": ("smell", "scent", "odor", "odour", "aroma", "stink"),
    "wear": ("wear", "worn", "fray", "frayed", "scuff", "threadbare"),
    "sound": ("sound", "hear", "noise", "listen", "call", "shout", "voice", "ring", "bell"),
    "taste": ("taste", "flavor", "flavour"),
}
_INABILITY_RE = re.compile(
    r"\b(?:can't|cannot|can not|don't know|do not know|not sure|unable to|will not say|won't say)\b",
    re.IGNORECASE,
)
_HARD_META_VOICE_RE = re.compile(
    r"\bbased on what(?:'s| is)\s+established\b|\bwe can determine\b|\bas an ai\b|"
    r"\bas (?:a )?(?:language )?model\b|\bmy (?:system|training data|tools?)\b",
    re.IGNORECASE,
)
_INTERNAL_STAGE_LABEL_RE = re.compile(
    r"(?:^|[.!?\n])\s*(?:planner|router|validator|adjudication|scaffold)\s*:",
    re.IGNORECASE,
)
_YOU_RE = re.compile(r"\byou\b", re.IGNORECASE)
_NO_ONE_RE = re.compile(r"\bno one\b", re.IGNORECASE)
_HTML_RE = re.compile(r"</?(?:b|i|em|strong|br|p)\s*/?>", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")

INSPECT_SAFE_LINE = (
    "The inspection establishes no further reliable detail from the current scene."
)
CLARIFICATION_LINE = "Which person are you speaking to?"
ACTION_INCOMPLETE_LINE = "The action cannot currently be completed."
ACTION_FAILED_LINE = "The action does not succeed."

# C17 mutator inventory. Every entry has one implementation status.
MUTATOR_MIGRATION: dict[str, str] = {
    "guard_gm_output": "RETAINED AS HARD VALIDATOR",
    "apply_stay_leave_narration_agreement_to_gm": "RETAINED AS LAST-RESORT SAFE NONRESOLUTION",
    "apply_visibility_enforcement": "RETAINED AS HARD VALIDATOR",
    "hard_reject_social_exchange_text": "REMOVED FROM CRITICAL PATH",
    "apply_narrative_authority_layer": "RETAINED AS HARD VALIDATOR",
    "enforce_emitted_speaker_with_contract": "REMOVED FROM CRITICAL PATH",
    "retain_resolved_contract_text": "REMOVED FROM CRITICAL PATH",
    "response_policy_answer_shaping": "REMOVED FROM CRITICAL PATH",
    "sanitize_player_facing_output": "RETAINED AS PRESENTATION-ONLY",
    "select_preserved_answer": "RETAINED AS OBSERVABILITY",
    "enforce_emitted_contract_monotonicity": "RETAINED AS OBSERVABILITY",
    "apply_social_response_structure_repair": "REMOVED FROM CRITICAL PATH",
    "apply_spoken_state_refinement_cash_out": "REMOVED FROM CRITICAL PATH",
    "apply_answer_shape_primacy_layer": "REMOVED FROM CRITICAL PATH",
    "apply_deterministic_retry_fallback": "REMOVED FROM CRITICAL PATH",
    "ensure_minimal_social_resolution": "REMOVED FROM CRITICAL PATH",
    "scene_pressure_appenders": "REMOVED FROM CRITICAL PATH",
    "apply_authored_knowledge_realization_to_gm": "REMOVED FROM CRITICAL PATH",
    "apply_perception_non_invention_to_gm": "REMOVED FROM CRITICAL PATH",
    "strict_social_rebuild_and_emergency_pool": "REMOVED FROM CRITICAL PATH",
    "obligation_preserving_fallback_line": "REMOVED FROM CRITICAL PATH",
    "run_generic_replace_exit": "REMOVED FROM CRITICAL PATH",
    "apply_first_mention_enforcement": "REMOVED FROM CRITICAL PATH",
    "apply_referential_clarity_enforcement": "REMOVED FROM CRITICAL PATH",
    "generic_ask_completion": "RETAINED AS LAST-RESORT SAFE NONRESOLUTION",
    "apply_destination_arrival_realization_to_gm": "REMOVED FROM CRITICAL PATH",
    "apply_repeated_description_guard": "REMOVED FROM CRITICAL PATH",
    "serialized_payload_extract": "RETAINED AS PRESENTATION-ONLY",
    "context_separation_and_narration_purity": "RETAINED AS PRESENTATION-ONLY",
    "finalize_emission_output": "RETAINED AS PRESENTATION-ONLY",
    "remember_satisfied_candidate": "RETAINED AS OBSERVABILITY",
    "detect_semantic_degradation": "RETAINED AS OBSERVABILITY",
    "second_grounding_pass": "REMOVED FROM CRITICAL PATH",
    "best_safe_tournament": "RETAINED AS OBSERVABILITY",
    "satisfaction_rank_chooser": "RETAINED AS OBSERVABILITY",
    "authoritative_resolution_state_mutation": "STILL REQUIRED FOR STATE/MECHANICS",
    "promote_accepted_bounded_improvisation": "STILL REQUIRED FOR STATE/MECHANICS",
    "note_emitted_npc_claim": "STILL REQUIRED FOR STATE/MECHANICS",
    "commit_discourse_focus": "STILL REQUIRED FOR STATE/MECHANICS",
    "evaluate_playability": "RETAINED AS OBSERVABILITY",
}

_ALLOWED_STATUSES = frozenset(
    {
        "REMOVED FROM CRITICAL PATH",
        "RETAINED AS HARD VALIDATOR",
        "RETAINED AS PRESENTATION-ONLY",
        "RETAINED AS OBSERVABILITY",
        "RETAINED AS LAST-RESORT SAFE NONRESOLUTION",
        "STILL REQUIRED FOR STATE/MECHANICS",
    }
)

# Post-acceptance operations that may touch the string and must not change meaning.
PRESENTATION_TRANSFORMS = (
    "json_serialization",
    "transport_escaping",
    "whitespace_normalization",
    "simple_html_strip",
)


def mutator_statuses_are_complete() -> bool:
    return bool(MUTATOR_MIGRATION) and all(status in _ALLOWED_STATUSES for status in MUTATOR_MIGRATION.values())


def normalize_presentation(text: str | None) -> str:
    """Whitespace and simple markup only. Words stay in order."""
    raw = _HTML_RE.sub(" ", str(text or ""))
    return _WS_RE.sub(" ", raw).strip()


def semantic_equal(left: str | None, right: str | None) -> bool:
    return normalize_presentation(left) == normalize_presentation(right)


def accepted_record(gm: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(gm, Mapping):
        return None
    seal = gm.get("_final_delivery_seal")
    if isinstance(seal, str):
        record = json.loads(seal)
        record["integrity_digest"] = hashlib.sha256(seal.encode("utf-8")).hexdigest()
        return record
    metadata = gm.get("metadata")
    if not isinstance(metadata, Mapping):
        return None
    record = metadata.get(ACCEPTED_KEY)
    return dict(record) if isinstance(record, Mapping) else None


def response_is_immutable(gm: Mapping[str, Any] | None) -> bool:
    record = accepted_record(gm)
    return bool(record and record.get("immutable") is True and str(record.get("text") or "").strip())


def leave_text_unchanged(gm: Any, mutator_name: str) -> bool:
    """True when this mutator must not replace an accepted response."""
    if not isinstance(gm, dict) or not response_is_immutable(gm):
        return False
    note_mutator_skipped(gm, mutator_name)
    return True


def note_mutator_skipped(gm: dict[str, Any], mutator_name: str) -> None:
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        return
    skipped = metadata.setdefault("skipped_semantic_mutators", [])
    if isinstance(skipped, list) and mutator_name not in skipped:
        skipped.append(mutator_name)
    record = metadata.get(ACCEPTED_KEY)
    if isinstance(record, dict):
        names = record.setdefault("skipped_mutators", [])
        if isinstance(names, list) and mutator_name not in names:
            names.append(mutator_name)


def effects_allowed(gm: Mapping[str, Any] | None) -> bool:
    """World, claim, and discourse commits follow the accepted response only.

    A gm dict with no acceptance record stays on the legacy path so older
    callers keep their current commit behavior.
    """
    record = accepted_record(gm)
    if record is None:
        return True
    if str(record.get("provenance") or "") == PROVENANCE_REJECTED:
        return False
    if record.get("authorization_source") == "host_terminal_safety":
        return False
    if record.get("immutable") is not True:
        return False
    return semantic_equal(record.get("text"), (gm or {}).get("player_facing_text") if isinstance(gm, Mapping) else "")


def mark_candidate_rejected(gm: dict[str, Any], text: str, reasons: list[str] | None = None) -> dict[str, Any]:
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        gm["metadata"] = metadata
    metadata[ACCEPTED_KEY] = {
        "provenance": PROVENANCE_REJECTED,
        "immutable": False,
        "text": str(text or ""),
        "hard_invalid_reasons": list(reasons or []),
    }
    gm.pop("_final_delivery_seal", None)
    return gm


def _words(text: str | None) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9']+", str(text or "").lower())
        if len(word) > 3 and word not in _STOP
    }


def _catalog_ids(label: str, referents: list[Mapping[str, Any]] | None) -> set[str]:
    words = _words(label)
    if not words or not referents:
        return set()
    found: set[str] = set()
    for row in referents:
        if not isinstance(row, Mapping):
            continue
        names = [str(row.get("label") or ""), str(row.get("id") or "").replace("_", " ")]
        aliases = row.get("aliases") or ()
        if isinstance(aliases, str):
            aliases = (aliases,)
        names.extend(str(alias) for alias in aliases)
        for name in names:
            name_words = _words(name)
            if name_words and (name_words <= words or words <= name_words):
                ident = str(row.get("id") or "").strip()
                if ident:
                    found.add(ident)
    return found


_GENERIC_ROLE_WORDS = frozenset(
    {"guard", "guards", "soldier", "soldiers", "watchman", "sentry", "guardsman"}
)


def _unresolved_explicit_addressee(contract: Mapping[str, Any] | None) -> str:
    """Explicit requested person whose binding did not succeed. Not 'no addressee'."""
    if not isinstance(contract, Mapping):
        return ""
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    if not binding.get("explicit_new_interlocutor"):
        return ""
    if binding.get("status") not in {"unresolved", "ambiguous", "rejected_consequential"}:
        return ""
    return " ".join(
        str(
            binding.get("proposed_interlocutor")
            or binding.get("proposed_span")
            or binding.get("label")
            or ""
        ).split()
    )


def _unresolved_addressee_conflict(speaker: str, requested: str) -> bool:
    """A different NPC must not answer an explicit person who was not bound.

    A shared generic role word such as guard is not identity. Serjeant and
    captain stay different even when both are guards.
    """
    left = _words(speaker) - _GENERIC_ROLE_WORDS
    right = _words(requested) - _GENERIC_ROLE_WORDS
    if left and right:
        return left.isdisjoint(right)
    extra = _words(speaker) - _words(requested) - _GENERIC_ROLE_WORDS
    return bool(extra)


def _speaker_conflicts(
    speaker: str,
    addressee: str,
    referents: list[Mapping[str, Any]] | None = None,
) -> bool:
    speaker_ids = _catalog_ids(speaker, referents)
    addressee_ids = _catalog_ids(addressee, referents)
    if speaker_ids and addressee_ids:
        if speaker_ids & addressee_ids:
            return False
        if len(speaker_ids) == 1 and len(addressee_ids) == 1:
            return True
    left = _words(speaker)
    right = _words(addressee)
    if not left or not right:
        return False
    return left.isdisjoint(right)


def _outside_quotes(text: str) -> str:
    return _QUOTE_RE.sub(" ", str(text or ""))


def same_clause_locates(text: str | None, labels: list[str]) -> bool:
    """Locate-verb and addressee words must sit in the same clause, after the verb."""
    for clause in re.split(r"[.!?]+|\n+", str(text or "")):
        match = _LOCATE_RE.search(clause)
        if not match:
            continue
        after = clause[match.end() :].lower()
        for label in labels:
            words = _words(label)
            if words and all(word in after for word in words):
                return True
    return False


def _explicit_addressee(player_text: str, referents: list[Mapping[str, Any]] | None) -> str:
    try:
        from game.interaction_completion import explicit_discourse_binding

        binding = explicit_discourse_binding(player_text, referents or (), None)
    except Exception:
        binding = {}
    label = str(binding.get("selected_interlocutor_label") or "").strip()
    if label:
        return label
    player = str(player_text or "")
    chosen = ""
    for match in _ADDRESS_RE.finditer(player):
        nominal = " ".join(str(match.group("nominal") or "").split())
        if not nominal or _QUESTION_NOMINAL_RE.match(nominal):
            continue
        if not _ROLE_RE.search(nominal):
            continue
        prefix = player[max(0, match.start() - 24) : match.start()].lower()
        if re.search(r"\bnot\b", prefix):
            continue
        chosen = nominal
    return chosen


def _speech_shell(text: str) -> bool:
    """A speech-attribution line with no proposition. 'Rain continues' is not one."""
    raw = " ".join(str(text or "").split())
    if not raw or '"' in raw or "“" in raw:
        return False
    if not _SPEECH_ATTRIB_RE.search(raw):
        return False
    if re.search(
        r"\b(?:is|are|was|were|can't|cannot|won't|will|means|because|costs|need|needs)\b",
        raw,
        re.IGNORECASE,
    ):
        return False
    return len(raw) < 220


def _speaker_constraint_label(contract: Mapping[str, Any] | None) -> str:
    """Only an interlocutor slot constrains the speaker. A claim or object does not."""
    if not isinstance(contract, Mapping):
        return ""
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    if binding.get("status") == "bound_incidental" and binding.get("label"):
        return str(binding.get("label"))
    # An ask keeps its bound person even when the discourse pointer was cleared.
    if str(contract.get("operation") or "") == "ask" and binding.get("status") == "bound_canonical":
        label = " ".join(str(binding.get("label") or "").split())
        if label:
            return label
        ident = " ".join(str(binding.get("bound_interlocutor_id") or contract.get("interlocutor_id") or "").replace("_", " ").split())
        if ident:
            return ident
    if binding.get("explicit_new_interlocutor") and binding.get("status") in {
        "unresolved",
        "ambiguous",
        "rejected_consequential",
    }:
        proposed = " ".join(str(binding.get("proposed_interlocutor") or binding.get("label") or "").split())
        if proposed:
            return proposed
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    dtype = str(discourse.get("type") or "")
    if dtype and dtype != "interlocutor":
        return ""
    label = " ".join(str(discourse.get("label") or "").split())
    if label:
        return label
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    if str(target.get("type") or "") in {"", "interlocutor"}:
        text = " ".join(str(target.get("id_or_text") or "").replace("_", " ").split())
        if text and _ROLE_RE.search(text):
            return text
    return ""


def _player_sensory_dimensions(player_text: str) -> list[str]:
    """Sensory dimensions the utterance itself asks for. A stale contract tag is not one."""
    from game.resolution_contract import DIM_SMELL, DIM_SOUND, DIM_USE, DIM_WEAR, _dimensions

    sensory = {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, "taste"}
    found: list[str] = []
    for name in _dimensions(player_text or ""):
        if name in sensory and name not in found:
            found.append(name)
    return found


def _dimension_satisfied(text: str, name: str) -> bool:
    """Perceptible evidence, a legitimate absence, or an inability. Not one canned verb."""
    if _INABILITY_RE.search(text):
        return True
    from game.resolution_contract import _RESPONSE_CUES

    cue = _RESPONSE_CUES.get(name)
    if cue is not None and cue.search(text or ""):
        return True
    # Inflected forms of the same evidence: "rustles" satisfies a sound request.
    stems = {
        "sound": r"\b(?:rustl\w*|snapp?\w*|creak\w*|murmur\w*|thud\w*|footstep\w*|whisper\w*)\b",
        "wear": r"\b(?:fray\w*|scuff\w*|scratch\w*|newer|older|worn|weathered)\b",
        "smell": r"\b(?:smell\w*|scent\w*|reek\w*|stink\w*)\b",
        "use": r"\b(?:used|useful|purpose|function|meant|lets?|opens?|lifts?)\b",
    }
    extra = stems.get(name)
    if extra and re.search(extra, text or "", re.IGNORECASE):
        return True
    absence = {
        "sound": r"\b(?:nothing (?:to hear|audible|stirs)|no sound|silence|silent|can't hear|cannot hear|quiet)\b",
        "smell": r"\b(?:no smell|nothing to smell|odorless|no scent)\b",
        "wear": r"\b(?:no (?:sign of )?wear|unworn|untouched|no scuff|intact|newer|scratches?)\b",
        "use": r"\b(?:no (?:obvious|visible) use|cannot tell what it is for|no sign of use)\b",
        "taste": r"\b(?:no taste|tasteless)\b",
    }
    pattern = absence.get(name)
    return bool(pattern and re.search(pattern, text or "", re.IGNORECASE))


def _perception_dimension_miss(
    text: str,
    contract: Mapping[str, Any] | None,
    player_text: str | None = None,
) -> bool:
    """Miss only when the player asked for a sense the response does not address.

    A dimensionless inspection is complete when it carries an observation.
    Wear words do not satisfy a sound request, and a sound request is not
    incomplete for lacking the word wear.
    """
    if not isinstance(contract, Mapping) or str(contract.get("operation") or "") not in {"inspect", "perceive"}:
        return False
    if _INABILITY_RE.search(text):
        return False
    player = str(player_text or contract.get("raw_input") or "")
    requested = _player_sensory_dimensions(player)
    stall = re.search(
        r"no further reliable detail about the (sound|smell|wear|use|taste)\b",
        text,
        re.IGNORECASE,
    )
    if stall and stall.group(1).lower() not in requested:
        return True
    if not requested:
        return False
    for name in requested:
        if not _dimension_satisfied(text, name):
            return True
    return False


def _contract_label(contract: Mapping[str, Any] | None) -> str:
    if not isinstance(contract, Mapping):
        return ""
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    for value in (
        discourse.get("label"),
        target.get("id_or_text"),
        contract.get("interlocutor_id"),
    ):
        text = " ".join(str(value or "").replace("_", " ").split())
        if text:
            return text
    return ""


def _unresolved_travel_arrival(text: str, resolution: Mapping[str, Any] | None) -> bool:
    """A travel attempt that did not resolve must not be narrated as an arrival."""
    if not isinstance(resolution, Mapping):
        return False
    if resolution.get("resolved_transition") is True:
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in {"travel", "scene_transition"}:
        return False
    from game.narration_state_consistency import (
        _FALSE_ARRIVAL_RE,
        _PLAYER_DEPARTED_RE,
        text_asserts_unowned_spatial_transition,
    )

    return bool(
        _FALSE_ARRIVAL_RE.search(text)
        or _PLAYER_DEPARTED_RE.search(text)
        or text_asserts_unowned_spatial_transition(text)
    )


def _mechanical_success(resolution: Mapping[str, Any] | None) -> bool | None:
    if not isinstance(resolution, Mapping):
        return None
    adjudication = resolution.get("adjudication")
    if isinstance(adjudication, Mapping) and "success" in adjudication:
        return bool(adjudication.get("success"))
    combat = resolution.get("combat")
    if isinstance(combat, Mapping) and "hit" in combat:
        return bool(combat.get("hit"))
    if "mechanical_success" in resolution:
        return bool(resolution.get("mechanical_success"))
    return None


def _malformed(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return True
    from game.gm_resolution_decision import preservation_structure_valid

    if not preservation_structure_valid(raw):
        return True
    lowered = raw.lower()
    if lowered.endswith("adding,") or lowered.endswith("adding"):
        return True
    if raw.endswith(":") and len(raw) < 80:
        return True
    if raw.endswith("…") and len(raw) < 40:
        return True
    return False


def _operation(contract: Mapping[str, Any] | None) -> str:
    return str((contract or {}).get("operation") or "").strip().lower()


def validate_generated_response(
    text: str | None,
    *,
    contract: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    declared_claims: list[Mapping[str, Any]] | None = None,
    player_text: str | None = None,
    resolution: Mapping[str, Any] | None = None,
    referents: list[Mapping[str, Any]] | None = None,
    authored_corpus: str = "",
    present_addressee: str = "",
    dead_actor_labels: list[str] | None = None,
) -> dict[str, Any]:
    """High-confidence hard invalidity only.

    Low-confidence lexical suspicions are soft flags. They do not reject.
    """
    from game.interaction_completion import (
        attribution_shell,
        attributed_speaker_label,
        passive_observation,
        player_utterance_embedded,
        recommends_locating_interlocutor,
        response_attributes_npc_speech,
    )

    raw = str(text or "")
    reasons: list[str] = []
    soft: list[str] = []
    operation = _operation(contract)
    player = str(player_text or (contract or {}).get("raw_input") or "")

    from game.structured_player_output import text_contains_response_envelope

    if text_contains_response_envelope(raw):
        reasons.append("structured_envelope")
    if _malformed(raw):
        reasons.append("malformed_or_truncated")
    if _LEAK_RE.search(raw):
        reasons.append("hidden_information")
    if player_utterance_embedded(raw, player) and _SPLICE_TEMPLATE_RE.search(raw):
        reasons.append("player_text_splice")
    elif player_utterance_embedded(raw, player):
        soft.append("player_echo")
    if operation == "ask" and (_speech_shell(raw) or attribution_shell(raw) and _SPEECH_ATTRIB_RE.search(raw)):
        reasons.append("interaction_incomplete")
    if operation == "ask" and passive_observation(raw):
        reasons.append("interaction_incomplete")
    if _perception_dimension_miss(raw, contract, player_text=player):
        reasons.append("interaction_incomplete")
    if operation in {"inspect", "perceive", "act", "follow"} and response_attributes_npc_speech(raw):
        reasons.append("unsolicited_npc_speech")
    # Reject explicit internal stage headings before sealing. A later sanitizer
    # cannot strip them without violating accepted-response integrity.
    if _HARD_META_VOICE_RE.search(raw) or _INTERNAL_STAGE_LABEL_RE.search(_outside_quotes(raw)):
        reasons.append("malformed_or_truncated")

    explicit = _explicit_addressee(player, referents)
    contract_label = _speaker_constraint_label(contract)
    addressee = explicit or present_addressee or contract_label
    speaker = attributed_speaker_label(raw)
    unresolved_addressee = _unresolved_explicit_addressee(contract)
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    known_social = (isinstance(social, Mapping) and social.get("target_resolved") is True
                    and social.get("npc_id") == (contract or {}).get("interlocutor_id"))
    if known_social:
        addressee = str(social.get("npc_name") or social.get("npc_id"))
        authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else None
        speaker_name = str(social.get("npc_name") or "").strip().lower()
        incidental_reaction = bool(
            isinstance(authority, Mapping)
            and authority.get("improvisation_permitted")
            and speaker_name
            and speaker_name in raw.lower()
        )
        if operation == "ask" and not response_attributes_npc_speech(raw) and not incidental_reaction:
            reasons.append("interaction_incomplete")
        if re.search(r"\b(?:no one here|nobody here|person you addressed cannot be identified)\b", raw, re.I):
            reasons.append("authoritative_target_contradiction")
        if isinstance(authority, Mapping):
            from game.dialogue_authority import dialogue_rejection_reasons

            for reason in dialogue_rejection_reasons(raw, authority=authority):
                reasons.append(reason)
    if ((contract or {}).get("construction") or {}).get("authority_conflict"):
        reasons.append("conflicting_target_authorities")
    if speaker and unresolved_addressee and _unresolved_addressee_conflict(speaker, unresolved_addressee):
        reasons.append("wrong_interlocutor")
    elif speaker and addressee and _speaker_conflicts(speaker, addressee, referents):
        reasons.append("wrong_interlocutor")

    locate_labels = [label for label in (explicit, present_addressee, contract_label) if label]
    if same_clause_locates(raw, locate_labels):
        reasons.append("locate_present_interlocutor")
    elif (
        _YOU_RE.search(player)
        and _NO_ONE_RE.search(raw)
        and same_clause_locates(raw, ["guard captain", "the captain"])
    ):
        reasons.append("locate_present_interlocutor")
    elif isinstance(contract, Mapping) and recommends_locating_interlocutor(raw, contract):
        soft.append("low_confidence_locate")

    narrator = _outside_quotes(raw)
    clock = _CLOCK_RE.search(narrator)
    if clock and clock.group(0).lower() not in str(authored_corpus or "").lower():
        reasons.append("consequential_invention")

    from game.interpretation_proposal import referential_action_shape
    from game.resolution_contract import _LITERAL_STEP_RE

    if referential_action_shape(player) and _LITERAL_STEP_RE.search(raw):
        reasons.append("consequential_invention")

    from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules

    authority = classify_propositions(raw, authored_corpus=authored_corpus)
    if unauthorized_authoritative_rules(raw, authored_corpus):
        reasons.append("ungrounded_authoritative_rule")
    if decision is not None:
        from game.gm_resolution_decision import decision_with_selected_social_topic

        decision = decision_with_selected_social_topic(decision, resolution)
        if declared_claims is not None:
            from game.gm_resolution_decision import audit_realization_envelope_against_decision

            decision_audit = audit_realization_envelope_against_decision(
                narration=raw,
                declared_claims=declared_claims,
                decision=decision,
                authored_corpus=authored_corpus,
            )
        else:
            from game.gm_resolution_decision import audit_narration_against_decision

            decision_audit = audit_narration_against_decision(
                raw,
                decision=decision,
                authored_corpus=authored_corpus,
            )
        if not decision_audit.get("hard_valid"):
            reasons.append("unauthorized_resolution_decision_fact")
        from game.gm_resolution_decision import _IGNORANCE_SEAL_RE, authorized_observation_line

        # Ignorance must not seal over an authorized observation the player asked for.
        if _IGNORANCE_SEAL_RE.search(raw or ""):
            observed = authorized_observation_line(decision, player)
            observed_norm = " ".join(str(observed or "").lower().split())
            raw_norm = " ".join(str(raw or "").lower().split())
            if observed_norm and observed_norm not in raw_norm:
                if "unauthorized_resolution_decision_fact" not in reasons:
                    reasons.append("unauthorized_resolution_decision_fact")
    else:
        decision_audit = None

    if _unresolved_travel_arrival(raw, resolution):
        reasons.append("consequential_invention")

    success = _mechanical_success(resolution)
    if success is False and _SUCCESS_NARRATION_RE.search(raw) and not _NEGATION_RE.search(raw):
        reasons.append("mechanical_contradiction")
    if success is True and _FAILURE_NARRATION_RE.search(raw):
        reasons.append("mechanical_contradiction")

    for label in dead_actor_labels or []:
        if not str(label).strip():
            continue
        if re.search(
            rf"\b{re.escape(str(label))}\b.{{0,48}}\b(?:says|said|replies|replied|answers)\b",
            raw,
            re.IGNORECASE,
        ):
            reasons.append("impossible_entity_state")
            break

    # De-duplicate while keeping order.
    ordered: list[str] = []
    for reason in reasons:
        if reason not in ordered:
            ordered.append(reason)
    hard_valid = not ordered
    return {
        "hard_valid": hard_valid,
        "reasons": ordered,
        "soft_flags": soft,
        "speaker": speaker,
        "addressee": addressee,
        "operation": operation,
        "interaction_complete": "interaction_incomplete" not in ordered and "malformed_or_truncated" not in ordered,
        "contract_satisfying": hard_valid,
        "authority": authority,
        "gm_resolution_decision_audit": decision_audit,
    }


_NARRATION_ONLY_RETRY_SHAPE = (
    'Return valid JSON only as {"narration": "player-facing response"}. '
    "Do not include any other fields."
)


def _with_retry_authority(
    text: str,
    *,
    reasons: list[str],
    resolution: Mapping[str, Any] | None,
    audit: Mapping[str, Any] | None,
    provider_response_contract: str = "structured_realization",
) -> str:
    if not isinstance(resolution, Mapping):
        return text
    from game.gm_resolution_decision import retry_authority_context

    extra = retry_authority_context(
        resolution=resolution,
        reasons=reasons,
        audit=audit,
        provider_response_contract=provider_response_contract,
    )
    if not extra:
        return text
    return f"{text} {extra}"


def regeneration_feedback(
    reasons: list[str] | None,
    *,
    resolution: Mapping[str, Any] | None = None,
    audit: Mapping[str, Any] | None = None,
    provider_response_contract: str = "structured_realization",
) -> str:
    """Name the violation. Do not supply a replacement sentence.

    ``provider_response_contract`` is the envelope already selected for this
    resolution. Retry wording follows that selection and does not reclassify
    the turn.
    """
    from game.gm_resolution_decision import (
        PROVIDER_ENVELOPE_NARRATION_ONLY,
        PROVIDER_ENVELOPE_STRUCTURED,
    )

    selected = (
        PROVIDER_ENVELOPE_NARRATION_ONLY
        if str(provider_response_contract or "") == PROVIDER_ENVELOPE_NARRATION_ONLY
        else PROVIDER_ENVELOPE_STRUCTURED
    )
    narration_only = selected == PROVIDER_ENVELOPE_NARRATION_ONLY
    named = [str(reason) for reason in (reasons or []) if str(reason).strip()]

    def _finish(text: str) -> str:
        if narration_only and '{"narration": "player-facing response"}' not in text:
            text = f"{text.rstrip()} {_NARRATION_ONLY_RETRY_SHAPE}"
        return _with_retry_authority(
            text,
            reasons=named,
            resolution=resolution,
            audit=audit,
            provider_response_contract=selected,
        )

    if "structured_contract_failure" in named:
        if narration_only:
            text = (
                "The previous attempt was rejected for: structured_contract_failure. "
                "The model output was not a valid narration-only response envelope. "
                f"{_NARRATION_ONLY_RETRY_SHAPE} "
                "Plain prose is not a valid model response. "
                "Do not invent a replacement fact."
            )
            return _finish(text)
        text = (
            "The previous attempt was rejected for: structured_contract_failure. "
            "The model output was not a valid structured realization envelope. "
            "Return valid JSON only with declared_claims and narration. "
            'Required envelope: {"declared_claims": [{"declaration_mode": "realize|propose", "text": "short claim"}], "narration": "player-facing sentence"}. '
            "Plain prose is not a valid model response. "
            "Do not speak the envelope keys to the player. "
            "Do not invent a replacement fact."
        )
        return _finish(text)
    if "ungrounded_authoritative_rule" in named:
        text = (
            "The previous attempt was rejected for: ungrounded_authoritative_rule. "
            "It asserted an ungrounded authoritative world rule. "
            "Answer again without establishing unsupported authoritative facts. "
            "Do not invent a replacement fact. "
            "Keep the same resolution contract, canonical state, mechanical result, "
            "operation, and interlocutor."
        )
        return _finish(text)
    if "unauthorized_resolution_decision_fact" in named:
        if narration_only:
            text = (
                "The previous attempt was rejected for: unauthorized_resolution_decision_fact. "
                "It narrated consequential world facts that were not authorized by the pre-narration GM resolution decision. "
                "The prior narration was rejected. "
                f"{_NARRATION_ONLY_RETRY_SHAPE} "
                "Avoid unsupported world assertions. "
                "Restrict the answer to authorized material. "
                "Produce revised player-facing narration. "
                "Answer again using only established facts, bounded incidental detail, or explicitly qualified NPC belief/hearsay. "
                "Do not invent routes, orders, command authorities, physical evidence, rosters, notice history, or movement as world truth. "
                "Keep every sentence that already matches the GM resolution decision. Repair only the rejected sentence."
            )
            return _finish(text)
        text = (
            "The previous attempt was rejected for: unauthorized_resolution_decision_fact. "
            "It narrated consequential world facts that were not authorized by the pre-narration GM resolution decision. "
            "Answer again as the same structured envelope with declared_claims plus narration. "
            "Do not repeat rejected declarations or their prose realization. "
            "Answer again using only established facts, bounded incidental detail, or explicitly qualified NPC belief/hearsay. "
            "Do not invent routes, orders, command authorities, physical evidence, rosters, notice history, or movement as world truth. "
            "Keep every sentence that already matches the GM resolution decision. Repair only the rejected sentence."
        )
        return _finish(text)
    if "wrong_interlocutor" in named or "unsolicited_npc_speech" in named:
        codes = ", ".join(named)
        text = (
            f"The previous attempt was rejected for: {codes}. "
            "The response assigns the answer to the wrong speaker. "
            "Preserve the bound interlocutor. Do not answer as a different person, and do not turn an "
            "observation into unrelated NPC speech. "
            "Keep the same resolution contract, operation, target, and dimension. "
            "Answer again. Do not rewrite a name into the previous sentence."
        )
        return _finish(text)
    codes = ", ".join(named) or "hard_invalid"
    if narration_only:
        text = (
            "Regenerate this turn under the same resolution contract, canonical state, "
            "authority boundaries, mechanical result, operation, and interlocutor. "
            f"The previous attempt was rejected for: {codes}. "
            f"{_NARRATION_ONLY_RETRY_SHAPE} "
            "Do not switch speaker, do not switch the inspected target or dimension, "
            "do not invent a posted fact, and do not quote the player. "
            "Produce a complete in-world response."
        )
        return _finish(text)
    text = (
        "Regenerate this turn under the same resolution contract, canonical state, "
        "authority boundaries, mechanical result, operation, and interlocutor. "
        f"The previous attempt was rejected for: {codes}. "
        "Return the same structured envelope shape: declared_claims plus narration. "
        "Do not switch speaker, do not switch the inspected target or dimension, "
        "do not invent a posted fact, and do not quote the player. "
        "Produce a complete in-world response."
    )
    return _finish(text)


def safe_nonresolution(
    contract: Mapping[str, Any] | None,
    *,
    resolution: Mapping[str, Any] | None = None,
    visible_facts: list[str] | None = None,
    player_text: str | None = None,
) -> str:
    """Last resort. No new topic, no player-text splice, no switched speaker."""
    from game.interaction_completion import generic_ask_completion

    operation = _operation(contract)
    construction = (contract or {}).get("construction") if isinstance(contract, Mapping) else {}
    authorization = construction.get("conversational_authorization") if isinstance(construction, Mapping) else {}
    if isinstance(authorization, Mapping) and authorization.get("mutation_eligibility") is False and (
        authorization.get("operation_eligibility") == "requires_clarification"
        or authorization.get("target_resolution") in {"ambiguous", "unresolved"}
    ):
        clarification = str(authorization.get("clarification") or "").strip()
        return clarification or "Which person do you mean? Nothing has been attempted."
    player = str(player_text or (contract or {}).get("raw_input") or "")
    requested = [name for name in _player_sensory_dimensions(player) if name in _DIMENSION_LEXICON]
    success = _mechanical_success(resolution)
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    if (operation == "ask" and isinstance(social, Mapping) and social.get("target_resolved") is True
            and social.get("npc_id") == (contract or {}).get("interlocutor_id")):
        authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else {}
        authored_line = str(authority.get("player_line") or "").strip()
        label = str(social.get("npc_name") or "").strip()
        if authored_line:
            return authored_line
        if authority and label:
            from game.dialogue_authority import _player_line

            return _player_line(label, str(authority.get("knowledge_posture") or "unknown"), "")
        if label:
            return f'{label} says, "I cannot answer that from what is settled here."'
    if operation in {"inspect", "perceive"} and len(requested) == 1:
        token = str(requested[0] or "").strip().lower()
        if re.fullmatch(r"[a-z][a-z ]{2,40}", token):
            return f"The inspection establishes no further reliable detail about the {token}."
        return INSPECT_SAFE_LINE
    if operation in {"inspect", "perceive"}:
        return INSPECT_SAFE_LINE
    if success is False:
        line = ACTION_FAILED_LINE
    elif operation in {"inspect", "perceive"}:
        fact = next((str(item).strip() for item in (visible_facts or []) if str(item).strip()), "")
        line = fact or INSPECT_SAFE_LINE
    elif operation in {"act", "follow", "confirm"}:
        line = ACTION_INCOMPLETE_LINE
    elif _unresolved_explicit_addressee(contract):
        line = "The person you addressed cannot be identified clearly enough to answer."
    elif isinstance(contract, Mapping) and contract.get("ambiguous") and not _contract_label(contract):
        line = CLARIFICATION_LINE
    else:
        line = generic_ask_completion(contract)
    if player_utterance_in_line(line, player_text) or _label_repeats_player(line, player_text):
        line = "No one here can answer that from what is settled here."
    return line


def _label_repeats_player(line: str | None, player_text: str | None) -> bool:
    from game.interaction_completion import subject_repeats_player_opening

    player = " ".join(str(player_text or "").split())
    body = " ".join(str(line or "").split())
    if player and player.lower() in body.lower():
        return True
    return subject_repeats_player_opening(body, player)


def player_utterance_in_line(line: str | None, player_text: str | None) -> bool:
    from game.interaction_completion import player_utterance_embedded

    return player_utterance_embedded(line, player_text)


def _contract_from_resolution(resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    from game.resolution_contract import contract_mapping_from_resolution

    return contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)


def lifecycle_applies(resolution: Mapping[str, Any] | None) -> bool:
    if not isinstance(resolution, Mapping):
        return False
    if str(resolution.get("kind") or "").strip().lower() == "scene_opening":
        return False
    contract = _contract_from_resolution(resolution)
    operation = str(contract.get("operation") or "").strip()
    # Ordinary unmatched narration is not an owed answer or action. Sealing it
    # before the existing question and scene-stall retry loop would hide those
    # failures. Social, inspection, and world-action contracts still seal.
    if operation == "unresolved" and not str(contract.get("interlocutor_id") or "").strip():
        return False
    return bool(operation)


def _referents_for(
    resolution: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    contract = _contract_from_resolution(resolution)
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    candidates = construction.get("canonical_candidates") if isinstance(construction, Mapping) else None
    if isinstance(candidates, list) and candidates:
        return [row for row in candidates if isinstance(row, Mapping)]
    try:
        from game.scene_referent_catalog import build_canonical_referent_catalog

        catalog = build_canonical_referent_catalog(
            scene=scene,
            world=world,
            session=session,
            scene_id=str((session or {}).get("active_scene_id") or "") if isinstance(session, Mapping) else "",
        )
    except Exception:
        catalog = None
    if isinstance(catalog, list):
        return [row for row in catalog if isinstance(row, Mapping)]
    return []


def _authored_corpus(scene: Mapping[str, Any] | None, extra: str = "") -> str:
    parts: list[str] = [str(extra or "")]
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        for key in ("visible_facts", "opening_seed_facts", "summary"):
            value = inner.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value)
            elif isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def _scene_id_for_social_projection(
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
) -> str:
    if isinstance(scene, Mapping):
        inner = scene.get("scene") if isinstance(scene.get("scene"), Mapping) else scene
        if isinstance(inner, Mapping) and str(inner.get("id") or "").strip():
            return str(inner.get("id") or "").strip()
    if isinstance(session, Mapping) and str(session.get("active_scene_id") or "").strip():
        return str(session.get("active_scene_id") or "").strip()
    if isinstance(resolution, Mapping) and str(resolution.get("scene_id") or "").strip():
        return str(resolution.get("scene_id") or "").strip()
    return ""


def _project_authorized_social_answer_before_seal(
    gm: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    player_text: str,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(resolution, Mapping) or not isinstance(resolution.get("social"), Mapping):
        return gm
    social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else None
    topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
    if topic_text:
        from game.dialogue_authority import npc_source_permitted
        person = next((n for n in (world or {}).get("npcs") or [] if isinstance(n, Mapping)
                       and n.get("id") == social.get("npc_id")), None)
        if not npc_source_permitted(person, topic):
            return {**gm, "player_facing_text": f'{social.get("npc_name") or "They"} says, "I cannot share that information."'}
        try:
            from game.social import (
                _text_communicates_authored_fact,
                format_authored_knowledge_realization_line,
            )

            current = str(gm.get("player_facing_text") or "")
            speaker_id = str(social.get("npc_id") or "").strip() or None
            speaker_name = str(social.get("npc_name") or "").strip() or None
            if _text_communicates_authored_fact(
                current,
                topic_text,
                speaker_id=speaker_id,
                speaker_name=speaker_name,
            ):
                return gm
            projected = dict(gm)
            projected["player_facing_text"] = format_authored_knowledge_realization_line(
                dict(resolution),
                topic_text,
            )
            tags = [str(t) for t in (projected.get("tags") or []) if isinstance(t, str)]
            if "authored_knowledge_preseal_projection" not in tags:
                tags.append("authored_knowledge_preseal_projection")
            projected["tags"] = tags
            metadata = projected.setdefault("metadata", {})
            if isinstance(metadata, dict):
                metadata.pop("content_leak_reasons", None)
                metadata.pop("structured_output_rejected", None)
                metadata.pop("structured_contract_failure", None)
                debug = metadata.setdefault("emission_debug", {})
                if isinstance(debug, dict):
                    debug["authored_answer_preseal_projection"] = {
                        "applied": True,
                        "topic_id": str((topic or {}).get("id") or ""),
                        "speaker_id": speaker_id,
                        "replaced_preview": current[:180],
                    }
            return projected
        except Exception:
            return gm
    try:
        from game.social import player_facing_invents_unauthored_social_fact
        from game.social_exchange_fallback_catalog import strict_social_ownership_terminal_fallback

        current = str(gm.get("player_facing_text") or "")
        speaker_id = str(social.get("npc_id") or "").strip() or None
        speaker_name = str(social.get("npc_name") or "").strip() or None
        if player_facing_invents_unauthored_social_fact(
            current,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
        ):
            replacement = str(strict_social_ownership_terminal_fallback(dict(resolution)) or "").strip()
            if replacement:
                projected = dict(gm)
                projected["player_facing_text"] = replacement
                tags = [str(t) for t in (projected.get("tags") or []) if isinstance(t, str)]
                if "grounded_social_absence_preseal_projection" not in tags:
                    tags.append("grounded_social_absence_preseal_projection")
                projected["tags"] = tags
                metadata = projected.setdefault("metadata", {})
                if isinstance(metadata, dict):
                    metadata.pop("content_leak_reasons", None)
                    metadata.pop("structured_output_rejected", None)
                    metadata.pop("structured_contract_failure", None)
                    debug = metadata.setdefault("emission_debug", {})
                    if isinstance(debug, dict):
                        debug["grounded_social_absence_preseal_projection"] = {
                            "applied": True,
                            "speaker_id": speaker_id,
                            "replaced_preview": current[:180],
                        }
                return projected
    except Exception:
        return gm
    try:
        from game.social import apply_authored_knowledge_realization_to_gm

        projected = apply_authored_knowledge_realization_to_gm(
            gm,
            player_text=player_text,
            resolution=dict(resolution),
            session=dict(session) if isinstance(session, Mapping) else None,
            world=dict(world) if isinstance(world, Mapping) else None,
            scene=dict(scene) if isinstance(scene, Mapping) else None,
            scene_id=_scene_id_for_social_projection(scene, session, resolution),
        )
    except Exception:
        return gm
    return projected if isinstance(projected, dict) else gm


def _unsupported_perception(
    text: str,
    *,
    resolution: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> bool:
    """Scene-backed perception invention is hard-invalid. Social turns are not checked."""
    if not str(text or "").strip() or not isinstance(resolution, Mapping):
        return False
    try:
        from game.perception_grounding import (
            PERCEPTION_KINDS,
            build_perception_evidence_surface,
            classify_perception_invention,
        )
    except Exception:
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind not in PERCEPTION_KINDS:
        return False
    contract = _contract_from_resolution(resolution)
    if _operation(contract) == "ask":
        return False
    evidence = build_perception_evidence_surface(
        scene=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    verdict = classify_perception_invention(text, evidence, resolution=resolution)
    return bool(verdict.get("unsupported"))


def _visible_facts(scene: Mapping[str, Any] | None) -> list[str]:
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if not isinstance(inner, Mapping):
        return []
    facts = inner.get("visible_facts")
    if not isinstance(facts, list):
        return []
    return [str(item).strip() for item in facts if str(item).strip()]


def seal_accepted_response(
    gm: dict[str, Any],
    *,
    text: str,
    provenance: str,
    attempt: int,
    validation: Mapping[str, Any],
    contract: Mapping[str, Any] | None,
    player_text: str,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gm["player_facing_text"] = text
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        gm["metadata"] = metadata
    if provenance == PROVENANCE_SAFE:
        gm.pop("improvisation_proposals", None)
        gm.pop("bounded_improvisation_authority", None)
    metadata[ACCEPTED_KEY] = {
        "immutable": True,
        "text": text,
        "provenance": provenance,
        "attempt": int(attempt),
        "player_input": str(player_text or ""),
        "turn_identity": str((contract or {}).get("contract_id") or (contract or {}).get("turn_index") or ""),
        "speaker": str(validation.get("speaker") or ""),
        "addressee": str(validation.get("addressee") or ""),
        "target": _contract_label(contract),
        "operation": str(validation.get("operation") or _operation(contract)),
        "authority_result": "accepted" if validation.get("hard_valid") else "safe_nonresolution",
        "grounding_result": "not_a_replacement_trigger",
        "hard_validation": {
            "hard_valid": bool(validation.get("hard_valid")),
            "reasons": list(validation.get("reasons") or []),
            "soft_flags": list(validation.get("soft_flags") or []),
            "authority": list(validation.get("authority") or []),
            "gm_resolution_decision_audit": validation.get("gm_resolution_decision_audit"),
        },
        "interaction_completion": bool(validation.get("interaction_complete")),
        "contract_satisfying": bool(validation.get("contract_satisfying")),
        "contract": {
            "contract_id": str((contract or {}).get("contract_id") or ""),
            "operation": _operation(contract),
            "interlocutor_id": str((contract or {}).get("interlocutor_id") or ""),
            "expected_resolution": str((contract or {}).get("expected_resolution") or ""),
        },
        "resolution_kind": str((resolution or {}).get("kind") or "") if isinstance(resolution, Mapping) else "",
        "generation_attempts": int(attempt),
        "skipped_mutators": [],
    }
    debug = metadata.setdefault("emission_debug", {})
    if isinstance(debug, dict):
        debug["accepted_response_provenance"] = provenance
        debug["generation_attempts"] = int(attempt)
        debug["legacy_emission_authority"] = False
        debug["semantic_degradation"] = False
        debug["semantic_degradation_reasons"] = []
        debug["resolution_contract_semantic"] = {
            "status": "legitimate_nonresolution" if provenance == PROVENANCE_SAFE else "satisfied",
            "reasons": list(validation.get("reasons") or []),
            "preserved": provenance != PROVENANCE_SAFE,
        }
    seal_delivery_contract(gm)
    return gm


def restore_accepted_text(gm: dict[str, Any] | None) -> dict[str, Any]:
    """Put the accepted sentence back if a later stage changed it.

    Exact equality is preferred. A whitespace or markup difference is recorded
    as presentation-only and normalized. Any other difference is a blocked
    semantic mutation.
    """
    report = {
        "immutable": False,
        "exact_match": False,
        "semantic_match": False,
        "presentation_only": False,
        "mutation_blocked": False,
    }
    if not isinstance(gm, dict) or not response_is_immutable(gm):
        return report
    record = accepted_record(gm) or {}
    accepted = str(record.get("text") or "")
    emitted = str(gm.get("player_facing_text") or "")
    if record.get("integrity_digest") and not verify_delivery_record(record):
        raise ValueError("Final response integrity check failed")
    # Restore attribution/provenance as well as text from the pinned record.
    if gm.get("_final_delivery_seal"):
        current = gm.setdefault("metadata", {}).get(ACCEPTED_KEY)
        gm["metadata"][ACCEPTED_KEY] = copy.deepcopy(record)
        if isinstance(current, dict) and current != record:
            report["metadata_mutation_blocked"] = True
    report["immutable"] = True
    report["accepted_response_text"] = accepted
    report["emitted_response_text"] = emitted
    if emitted == accepted:
        report["exact_match"] = True
        report["semantic_match"] = True
    elif semantic_equal(emitted, accepted):
        report["semantic_match"] = True
        report["presentation_only"] = True
        gm["player_facing_text"] = accepted
        report["exact_match"] = True
        report["emitted_response_text"] = gm["player_facing_text"]
    else:
        report["mutation_blocked"] = True
        gm["player_facing_text"] = accepted
        report["exact_match"] = True
        report["semantic_match"] = True
        report["emitted_response_text"] = accepted
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        debug = metadata.setdefault("emission_debug", {})
        if isinstance(debug, dict):
            debug["accepted_emitted_equality"] = {
                "exact_match": emitted == accepted or report["mutation_blocked"],
                "semantic_match": True,
                "presentation_only": report["presentation_only"],
                "mutation_blocked": report["mutation_blocked"],
                "attempted_text": emitted[:500],
            }
    return report


def _structured_contract_failed(candidate: Mapping[str, Any] | None) -> bool:
    if not isinstance(candidate, Mapping):
        return False
    metadata = candidate.get("metadata")
    return bool(isinstance(metadata, Mapping) and metadata.get("structured_contract_failure"))


def candidate_entered_structured_envelope_path(candidate: Mapping[str, Any] | None) -> bool:
    """True once a candidate is on the one-call structured claim path.

    Prose-only ``_bounded_keep`` must not run after that. Legacy JSON that never
    carried declared claims stays on the older preservation path.
    """
    if not isinstance(candidate, Mapping):
        return False
    metadata = candidate.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    if metadata.get("structured_contract_failure"):
        return True
    envelope = metadata.get("realization_envelope")
    if not isinstance(envelope, Mapping) or envelope.get("legacy_fallback"):
        return False
    declared = envelope.get("declared_claims")
    return isinstance(declared, list) or bool(envelope.get("structured_contract_present"))


def adopt_host_speech(
    gm: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    player_text: str,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Bind host-owned speech to the existing immutable final-response record."""
    from game.dialogue_authority import select_host_speech

    selection = select_host_speech(resolution, player_text=player_text, session=session)
    if selection is None:
        return None
    line, source = selection
    social = resolution["social"]
    from game.expressive_dialogue import apply_expression, attach_expression_audit

    expressed = apply_expression(
        player_text=player_text,
        speaker_name=str(social.get("npc_name") or ""),
        speaker_id=str(social.get("npc_id") or ""),
        fallback_line=line,
        fallback_source=source,
        resolution=resolution,
    )
    audit = None
    if expressed is not None:
        line, source, audit = expressed
    sealed = seal_host_speech(gm, text=line, source=source, speaker_id=social["npc_id"],
                              speaker_name=social["npc_name"], resolution=resolution, player_text=player_text, world=world)
    if sealed["metadata"][ACCEPTED_KEY].get("authorization_source") != "dialogue_authority.disclosure_denied":
        attach_expression_audit(sealed, audit)
    return sealed


def seal_host_speech(
    gm: dict[str, Any], *, text: str, source: str, speaker_id: str,
    speaker_name: str, resolution: Mapping[str, Any] | None, player_text: str,
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Use one final-response representation for resolver and continuity speech."""
    from game.dialogue_authority import (
        CATEGORY_BOUNDED,
        CATEGORY_HISTORY,
        CATEGORY_HOST,
        CATEGORY_WORLD,
        authorize_npc_disclosure,
        consequential_addition,
        contains_protected_disclosure,
        is_bounded_expression,
        is_host_operation,
        provenance_record,
    )

    line = text
    social = (resolution or {}).get("social") or {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else None
    plan = social.get("unified_semantic_plan") or {}
    if not topic and plan.get("authorized_text"):
        topic = {"id": next(iter(plan.get("selected_source_ids") or []), ""),
                 "text": str(plan["authorized_text"])}
    authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else {}
    reuse = bool(authority.get("reuse_prior_speech") or str(source).startswith("dialogue_authority.reuse_prior_speech"))
    category = CATEGORY_HOST
    validation = "host_operation"
    proposition = ""
    source_identity = ""
    epistemic = "none"

    def _deny() -> None:
        nonlocal line, source, category, validation, proposition
        line = f'{speaker_name or "They"} says, "I cannot share that information."'
        source = "dialogue_authority.disclosure_denied"
        category = CATEGORY_WORLD
        validation = "source_or_policy_denied"
        proposition = ""

    if reuse:
        category = CATEGORY_HISTORY
        proposition = str(authority.get("authorized_proposition") or "")
        validation = "verified_history"
        if contains_protected_disclosure(line) or consequential_addition(line, proposition):
            _deny()
    else:
        topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "")
        states_topic = bool(topic_text) and topic_text.lower().rstrip(".") in line.lower()
        hostish = is_host_operation(line) or is_bounded_expression(line)
        if isinstance(topic, Mapping) and topic_text and (states_topic or not hostish):
            person = next((n for n in (world or {}).get("npcs") or []
                           if isinstance(n, Mapping) and n.get("id") == speaker_id), None)
            grant = authorize_npc_disclosure(person, topic)
            if world is None:
                # Production always passes world and re-resolves above. A pure
                # caller must carry the host receipt, and that receipt cannot
                # authorize protected wording.
                receipt = topic.get("disclosure_authorization") if isinstance(topic.get("disclosure_authorization"), Mapping) else {}
                receipt_ok = bool(
                    receipt.get("permission")
                    and receipt.get("validation") == "authorized"
                    and receipt.get("provenance") == "authored_npc_source"
                    and receipt.get("speaker_id") == speaker_id
                    and receipt.get("authorized_proposition") == topic_text
                    and not contains_protected_disclosure(topic_text)
                    and not contains_protected_disclosure(line)
                )
                grant = {
                    "permission": receipt_ok,
                    "source_id": receipt.get("source_id") or "",
                    "epistemic_status": receipt.get("epistemic_status") or "npc_knowledge",
                }
            if not grant["permission"] or consequential_addition(line, topic_text):
                _deny()
            else:
                category = CATEGORY_WORLD
                validation = "authorized"
                proposition = topic_text
                source_identity = str(grant.get("source_id") or "")
                epistemic = str(grant.get("epistemic_status") or "npc_knowledge")
        elif is_bounded_expression(line):
            category = CATEGORY_BOUNDED
            validation = "bounded_expression"
            proposition = line
            if consequential_addition(line):
                _deny()
        elif is_host_operation(line):
            category = CATEGORY_HOST
            validation = "host_operation"
            if contains_protected_disclosure(line) or consequential_addition(line):
                _deny()
        elif contains_protected_disclosure(line) or consequential_addition(line):
            _deny()
        else:
            # Expression may reword an already selected host sentence. Protected
            # and consequential additions are rejected above; this is not a
            # source-less grant for a new topic.
            category = CATEGORY_HOST
            validation = "host_operation"
    candidate = str(gm.get("player_facing_text") or "")
    # A discarded draft cannot supply state effects alongside the host answer.
    for key in ("scene_update", "world_updates", "activate_scene_id", "new_scene_draft", "suggested_action"):
        gm[key] = None
    gm.pop("improvisation_proposals", None)
    gm.pop("bounded_improvisation_authority", None)
    sealed = seal_accepted_response(
        gm, text=line, provenance="authorized_host_speech", attempt=0,
        validation={"hard_valid": True, "reasons": [], "soft_flags": [],
                    "speaker": speaker_name, "addressee": "player",
                    "operation": "ask", "interaction_complete": True,
                    "contract_satisfying": True, "authority": [source]},
        contract=_contract_from_resolution(resolution), player_text=player_text,
        resolution=resolution,
    )
    record = sealed["metadata"][ACCEPTED_KEY]
    record.update(speech_adoption="AUTHORIZED_HOST_SPEECH", authorization_source=source,
                  speaker_id=speaker_id, canonical=False,
                  candidate_disposition="UNAUTHORIZED_GENERATED_CANDIDATE" if candidate and not semantic_equal(candidate, line) else "host_selected",
                  authorization_provenance=provenance_record(
                      category=category,
                      speaker_id=speaker_id,
                      operation=str(record.get("operation") or "ask"),
                      proposition=proposition,
                      source_id=source_identity,
                      epistemic_status=epistemic,
                      validation=validation,
                  ))
    seal_delivery_contract(sealed)
    return sealed


def run_preserve_if_valid(
    gm: dict[str, Any],
    *,
    regenerate: Callable[[str], dict[str, Any] | None] | None,
    resolution: Mapping[str, Any] | None,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    referents: list[Mapping[str, Any]] | None = None,
    authored_corpus: str = "",
    present_addressee: str = "",
    dead_actor_labels: list[str] | None = None,
    visible_facts: list[str] | None = None,
) -> dict[str, Any]:
    """Generate is already done. Validate, preserve, or retry once."""
    if not isinstance(gm, dict):
        return gm
    adopted = adopt_host_speech(gm, resolution=resolution, player_text=player_text, session=session, world=world)
    if adopted is not None:
        return adopted
    contract = _contract_from_resolution(resolution)
    try:
        from game.gm_resolution_decision import decision_from_resolution

        gm_decision = decision_from_resolution(resolution)
    except Exception:
        gm_decision = {}
    catalog = referents if referents is not None else _referents_for(resolution, scene, world, session)
    corpus = authored_corpus or _authored_corpus(scene)
    facts = visible_facts if visible_facts is not None else _visible_facts(scene)
    player = str(player_text or contract.get("raw_input") or "")
    gm = _project_authorized_social_answer_before_seal(
        gm,
        resolution=resolution,
        player_text=player,
        scene=scene,
        world=world,
        session=session,
    )
    if isinstance(resolution, Mapping) and not isinstance(resolution.get("social"), Mapping):
        # Preserve resolver observations before validation, never by overwriting
        # an already adopted generic sentence downstream.
        from game.api_turn_support import _authoritative_resolution_fact_text, _looks_like_generic_resolution_fallback

        fact, _source = _authoritative_resolution_fact_text(resolution=resolution, scene=scene, world=world)
        if fact:
            # This is the selected public resolver result, not a provider fact
            # or the complete (possibly hidden) clue catalog.
            corpus = corpus + "\n" + fact
            if _source.get("source") == "clue_text" and gm_decision:
                selected = str(resolution.get("clue_text") or "").strip()
                if not selected:
                    selected = " ".join(str(item) for item in resolution.get("discovered_clues") or [])
                if selected:
                    gm_decision = copy.deepcopy(gm_decision)
                    gm_decision.setdefault("proposed_facts", []).append({
                        "text": selected, "provenance": "authored_world_fact", "consequence": "consequential",
                        "authorized": True, "authority": "world_truth", "persistence": "do_not_persist",
                        "source_ref": "resolution.clue_text", "outcome_classification": "established_or_retrieved",
                        "reason_codes": ["resolver_selected_public_clue"], "semantic_identity": {}})
        if _looks_like_generic_resolution_fallback(str(gm.get("player_facing_text") or "")):
            if fact:
                gm = {**gm, "player_facing_text": fact}

    def _check(candidate: dict[str, Any]) -> dict[str, Any]:
        candidate_meta = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
        realization_envelope = (
            candidate_meta.get("realization_envelope")
            if isinstance(candidate_meta.get("realization_envelope"), Mapping)
            else {}
        )
        declared = (
            realization_envelope.get("declared_claims")
            if isinstance(realization_envelope.get("declared_claims"), list)
            else None
        )
        verdict = validate_generated_response(
            str(candidate.get("player_facing_text") or ""),
            contract=contract,
            decision=gm_decision or None,
            declared_claims=declared,
            player_text=player,
            resolution=resolution,
            referents=catalog,
            authored_corpus=corpus,
            present_addressee=present_addressee,
            dead_actor_labels=dead_actor_labels,
        )
        leak_reasons = []
        if isinstance(candidate_meta, Mapping):
            leak_reasons = list(candidate_meta.get("content_leak_reasons") or [])
        if _unsupported_perception(
            str(candidate.get("player_facing_text") or ""),
            resolution=resolution,
            scene=scene,
            world=world,
            session=session,
        ):
            reasons = list(verdict.get("reasons") or [])
            if "consequential_invention" not in reasons:
                reasons.append("consequential_invention")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        if leak_reasons:
            reasons = list(verdict.get("reasons") or [])
            if "hidden_information" not in reasons:
                reasons.append("hidden_information")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        if isinstance(candidate_meta, Mapping) and candidate_meta.get("structured_contract_failure"):
            reasons = list(verdict.get("reasons") or [])
            if "structured_contract_failure" not in reasons:
                reasons.append("structured_contract_failure")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        return verdict

    first = _check(gm)
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["hard_validation_attempt_1"] = {
            "hard_valid": first["hard_valid"],
            "reasons": list(first["reasons"]),
            "soft_flags": list(first["soft_flags"]),
            "text": str(gm.get("player_facing_text") or "")[:2000],
        }
    review: dict[str, Any] = {
        "governing_decision_contract_id": str((gm_decision or {}).get("contract_id") or ""),
        "outcome_classification": str((gm_decision or {}).get("outcome_classification") or ""),
        "attempt_1": {
            "text": str(gm.get("player_facing_text") or "")[:2000],
            "reasons": list(first.get("reasons") or []),
            "gm_resolution_decision_audit": first.get("gm_resolution_decision_audit"),
        },
        "retry_context": "",
        "attempt_2": None,
        "acceptance": {"why": "initial_hard_valid"},
    }

    def _finish(sealed: dict[str, Any], *, why: str) -> dict[str, Any]:
        terminal = (sealed.get("metadata") or {}).get(ACCEPTED_KEY) or {}
        if terminal.get("provenance") == PROVENANCE_REJECTED:
            # Conflicting NPC authority can invalidate even a generic line in
            # the NPC validator. The host may only select this fixed GM safety
            # response, with no NPC attribution or state effects.
            rejected = copy.deepcopy(terminal)
            seal_accepted_response(sealed, text=TERMINAL_FALLBACK, provenance=PROVENANCE_SAFE,
                attempt=int((sealed.get("metadata") or {}).get("generation_attempt_count") or 1),
                validation={"hard_valid": True, "speaker": "GM", "addressee": "player",
                            "authority": ["host_terminal_safety"], "reasons": [],
                            "interaction_complete": False, "contract_satisfying": False},
                contract=contract, player_text=player, resolution=resolution)
            record = sealed["metadata"][ACCEPTED_KEY]
            record.update(speaker_id="", subject="", authority_result="safe_nonresolution", authorization_source="host_terminal_safety",
                          candidate_disposition="rejected", rejected_candidate=rejected)
            for key in ("scene_update", "world_updates", "activate_scene_id", "new_scene_draft", "suggested_action"):
                sealed[key] = None
        review["acceptance"] = {"why": why, "text": str(sealed.get("player_facing_text") or "")[:2000]}
        sealed_meta = sealed.setdefault("metadata", {})
        if isinstance(sealed_meta, dict):
            sealed_meta["decision_review"] = review
            record = sealed_meta.get(ACCEPTED_KEY)
            if isinstance(record, dict):
                hard = record.setdefault("hard_validation", {})
                if isinstance(hard, dict):
                    if hard.get("gm_resolution_decision_audit") is None:
                        hard["gm_resolution_decision_audit"] = {
                            "decision_id": review["governing_decision_contract_id"],
                            "source": "decision_review",
                            "attempt_1": review["attempt_1"],
                            "attempt_2": review["attempt_2"],
                            "retry_context_present": bool(review.get("retry_context")),
                            "acceptance_why": why,
                        }
                    hard["decision_acceptance_why"] = why
        seal_delivery_contract(sealed)
        return sealed

    if first["hard_valid"]:
        social = resolution.get("social") if isinstance(resolution, Mapping) else None
        authority = social.get("dialogue_authority") if isinstance(social, Mapping) else None
        from game.conversational_continuity import bounded_personal_line, is_unhelpful_personal_ignorance

        if is_unhelpful_personal_ignorance(str(gm.get("player_facing_text") or ""), authority if isinstance(authority, Mapping) else None):
            kind = str((authority or {}).get("requested_information") or "opinion")
            name = str(social.get("npc_name") or "They") if isinstance(social, Mapping) else "They"
            npc_id = str(social.get("npc_id") or "") if isinstance(social, Mapping) else ""
            recovered_line = bounded_personal_line(name, npc_id, kind)
            checked = _check({"player_facing_text": recovered_line, "metadata": {}})
            if checked.get("hard_valid"):
                sealed = seal_accepted_response(
                    gm,
                    text=recovered_line,
                    provenance=PROVENANCE_INITIAL,
                    attempt=1,
                    validation=checked,
                    contract=contract,
                    player_text=player,
                    resolution=resolution,
                )
                return _finish(sealed, why="incidental_personal_recovery")
        sealed = seal_accepted_response(
            gm,
            text=str(gm.get("player_facing_text") or ""),
            provenance=PROVENANCE_INITIAL,
            attempt=1,
            validation=first,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="initial_hard_valid")

    mark_candidate_rejected(gm, str(gm.get("player_facing_text") or ""), first["reasons"])
    feedback = regeneration_feedback(
        first["reasons"],
        resolution=resolution,
        audit=first.get("gm_resolution_decision_audit") if isinstance(first.get("gm_resolution_decision_audit"), Mapping) else None,
        provider_response_contract=str(metadata.get("provider_response_contract") or ""),
    )
    review["retry_context"] = feedback
    if isinstance(metadata, dict):
        metadata["regeneration_feedback"] = feedback
        metadata["regeneration_invoked"] = regenerate is not None
        metadata["hard_validation_attempt_1"]["gm_resolution_decision_audit"] = first.get("gm_resolution_decision_audit")

    def _early_authored_projection() -> tuple[dict[str, Any], dict[str, Any], str] | None:
        if not isinstance(resolution, Mapping) or _operation(contract) != "ask":
            return None
        social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else None
        if not isinstance(social, Mapping):
            return None
        topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else None
        topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
        if not topic_text:
            return None
        if _unresolved_explicit_addressee(contract):
            return None
        if isinstance(gm_decision, Mapping):
            if gm_decision.get("unresolved_qualifiers"):
                return None
            obligations = gm_decision.get("executable_obligations")
            if isinstance(obligations, Mapping) and obligations.get("primary"):
                return None
            mutations = gm_decision.get("permitted_state_mutations")
            allowed_mutations = {
                ("state_change", "topic_revealed"),
                ("state_change", "npc_id"),
            }
            if isinstance(mutations, list) and any(
                (
                    str(item.get("type") or ""),
                    str(item.get("key") or ""),
                )
                not in allowed_mutations
                for item in mutations
                if isinstance(item, Mapping)
            ):
                return None
        try:
            from game.social import format_authored_knowledge_realization_line

            line = format_authored_knowledge_realization_line(dict(resolution), topic_text)
        except Exception:
            return None
        if not str(line or "").strip():
            return None
        projected = copy.deepcopy(gm)
        projected["player_facing_text"] = str(line).strip()
        tags = [str(t) for t in (projected.get("tags") or []) if isinstance(t, str)]
        if "early_authored_answer_projection" not in tags:
            tags.append("early_authored_answer_projection")
        projected["tags"] = tags
        projected_meta = projected.setdefault("metadata", {})
        if isinstance(projected_meta, dict):
            projected_meta.pop("content_leak_reasons", None)
            projected_meta.pop("structured_output_rejected", None)
            projected_meta.pop("structured_contract_failure", None)
            projected_meta["regeneration_invoked"] = False
            projected_meta["generation_attempt_count"] = 1
            projected_meta["deterministic_recovery_method"] = "authored_answer_projection"
            projected_meta["rejected_attempt_1_reasons"] = list(first.get("reasons") or [])
            projected_meta["rejected_attempt_1_text"] = str(gm.get("player_facing_text") or "")[:2000]
            debug = projected_meta.setdefault("emission_debug", {})
            if isinstance(debug, dict):
                debug["early_authored_answer_projection"] = {
                    "applied": True,
                    "topic_id": str((topic or {}).get("id") or ""),
                    "rejected_reasons": list(first.get("reasons") or []),
                    "rejected_preview": str(gm.get("player_facing_text") or "")[:180],
                }
        checked = _check({"player_facing_text": str(line).strip(), "metadata": {}})
        if not checked.get("hard_valid"):
            if isinstance(projected_meta, dict):
                projected_meta["early_authored_projection_rejected"] = {
                    "reasons": list(checked.get("reasons") or []),
                    "text": str(line)[:2000],
                }
            return None
        return projected, checked, str(line).strip()

    def _incidental_quote_recovery(candidate_text: str) -> tuple[str, dict[str, Any]] | None:
        """Keep a harmless quoted remark and drop a consequential sentence beside it."""
        if not isinstance(resolution, Mapping) or _operation(contract) != "ask":
            return None
        social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else None
        if not isinstance(social, Mapping):
            return None
        authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else None
        if not isinstance(authority, Mapping) or authority.get("improvisation_permitted") is not True:
            return None
        name = str(social.get("npc_name") or "").strip() or "They"
        from game.dialogue_authority import dialogue_rejection_reasons
        from game.proposition_authority import CONSEQUENTIAL_KIND, classify_propositions

        spans = re.findall(r'["“]([^"”]{1,220})["”]', str(candidate_text or ""))
        for span in spans:
            for piece in re.split(r"(?<=[.!?])\s+", span.strip()):
                remark = piece.strip(" \"")
                if len(remark) < 3:
                    continue
                rows = classify_propositions(remark, authored_corpus=corpus)
                if any(row.get("kind") == CONSEQUENTIAL_KIND for row in rows):
                    continue
                if dialogue_rejection_reasons(remark, authority=authority):
                    continue
                spoken = remark[0].upper() + remark[1:] if remark[:1].islower() else remark
                spoken = spoken.rstrip(" ,;:")
                if not spoken:
                    continue
                if spoken[-1] not in ".?!":
                    spoken = spoken + "."
                line = f'{name} says, "{spoken}"'
                checked = _check({"player_facing_text": line, "metadata": {}})
                if checked.get("hard_valid"):
                    return line, checked
        return None

    early_projection = _early_authored_projection()
    if early_projection is not None:
        projected, checked, line = early_projection
        sealed = seal_accepted_response(
            projected,
            text=line,
            provenance=PROVENANCE_AUTHORED_PROJECTION,
            attempt=1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="authored_answer_projection")

    def _bounded_keep(candidate_text: str) -> tuple[str, dict[str, Any]] | None:
        from game.gm_resolution_decision import preservation_structure_valid, structural_narration_units

        source_verdict = _check({"player_facing_text": candidate_text})
        source_audit = source_verdict.get("gm_resolution_decision_audit")
        if not isinstance(source_audit, Mapping) or not source_audit.get("violations"):
            return None
        safe_units: list[str] = []
        for unit in structural_narration_units(candidate_text):
            unit_verdict = _check({"player_facing_text": unit})
            if unit_verdict.get("hard_valid"):
                safe_units.append(unit)
        kept = " ".join(safe_units).strip()
        if not kept or kept == str(candidate_text or "").strip() or not preservation_structure_valid(kept):
            return None
        # C18: this exact post-deletion string, not the source audit, governs sealing.
        checked = _check({"player_facing_text": kept})
        if not checked.get("hard_valid"):
            return None
        return kept, checked

    def _terminal_after_fidelity(reasons: list[str]) -> tuple[str, str]:
        from game.gm_resolution_decision import authorized_observation_line
        from game.social import format_authored_knowledge_realization_line

        social = resolution.get("social") if isinstance(resolution, Mapping) else None
        topic = social.get("topic_revealed") if isinstance(social, Mapping) else None
        topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
        if topic_text:
            projected = format_authored_knowledge_realization_line(
                dict(resolution) if isinstance(resolution, Mapping) else {},
                topic_text,
            )
            if projected.strip():
                checked = _check({"player_facing_text": projected})
                if checked.get("hard_valid"):
                    return projected, "authored_answer_projection"

        if "unauthorized_resolution_decision_fact" in reasons:
            realized = authorized_observation_line(gm_decision, player)
            generic = "No one here can answer that from what is settled here."
            if realized and realized.strip() != generic:
                checked = _check({"player_facing_text": realized})
                if checked.get("hard_valid"):
                    return realized, "authorized_observation"
        return (
            safe_nonresolution(contract, resolution=resolution, visible_facts=facts, player_text=player),
            "safe_nonresolution",
        )

    recovered = _incidental_quote_recovery(str(gm.get("player_facing_text") or ""))
    if recovered is not None:
        line, checked = recovered
        sealed = seal_accepted_response(
            gm,
            text=line,
            provenance=PROVENANCE_INITIAL,
            attempt=1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="incidental_quote_recovery")

    if regenerate is None:
        bounded = (
            None
            if candidate_entered_structured_envelope_path(gm)
            else _bounded_keep(str(gm.get("player_facing_text") or ""))
        )
        if bounded is not None:
            kept, checked = bounded
            sealed = seal_accepted_response(
                gm,
                text=kept,
                provenance=PROVENANCE_INITIAL,
                attempt=1,
                validation=checked,
                contract=contract,
                player_text=player,
                resolution=resolution,
            )
            return _finish(sealed, why="bounded_sentence_preservation")
        line, why = _terminal_after_fidelity(list(first.get("reasons") or []))
        safe_validation = _check({"player_facing_text": line})
        if not safe_validation.get("hard_valid"):
            gm["player_facing_text"] = "I cannot provide a validated response to that request."
            return _finish(mark_candidate_rejected(gm, gm["player_facing_text"],
                                                   list(safe_validation.get("reasons") or [])),
                           why="controlled_validation_failure")
        sealed = seal_accepted_response(
            gm,
            text=line,
            provenance=PROVENANCE_SAFE,
            attempt=1,
            validation=safe_validation,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why=why)

    regenerated = regenerate(feedback)
    if not isinstance(regenerated, dict):
        regenerated = {"player_facing_text": "", "metadata": {}}
    second = _check(regenerated)
    review["attempt_2"] = {
        "text": str(regenerated.get("player_facing_text") or "")[:2000],
        "reasons": list(second.get("reasons") or []),
        "gm_resolution_decision_audit": second.get("gm_resolution_decision_audit"),
    }
    second_meta = regenerated.setdefault("metadata", {})
    if isinstance(second_meta, dict):
        second_meta["hard_validation_attempt_1"] = metadata.get("hard_validation_attempt_1") if isinstance(metadata, dict) else {}
        second_meta["hard_validation_attempt_2"] = {
            "hard_valid": second["hard_valid"],
            "reasons": list(second["reasons"]),
            "soft_flags": list(second["soft_flags"]),
            "text": str(regenerated.get("player_facing_text") or "")[:2000],
            "gm_resolution_decision_audit": second.get("gm_resolution_decision_audit"),
        }
        second_meta["regeneration_feedback"] = feedback
        second_meta["regeneration_invoked"] = True
        second_meta["generation_attempt_count"] = 2
    if second["hard_valid"]:
        sealed = seal_accepted_response(
            regenerated,
            text=str(regenerated.get("player_facing_text") or ""),
            provenance=PROVENANCE_REGENERATION,
            attempt=2,
            validation=second,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="regeneration_hard_valid")
    mark_candidate_rejected(regenerated, str(regenerated.get("player_facing_text") or ""), second["reasons"])
    structured_turn = candidate_entered_structured_envelope_path(gm) or candidate_entered_structured_envelope_path(
        regenerated
    )
    bounded = None
    bounded_from_retry = False
    if not structured_turn:
        bounded = _bounded_keep(str(gm.get("player_facing_text") or ""))
        if bounded is None:
            bounded = _bounded_keep(str(regenerated.get("player_facing_text") or ""))
            bounded_from_retry = bounded is not None
    if bounded is not None:
        kept, checked = bounded
        host = regenerated if bounded_from_retry else gm
        sealed = seal_accepted_response(
            host,
            text=kept,
            provenance=PROVENANCE_REGENERATION if bounded_from_retry else PROVENANCE_INITIAL,
            attempt=2 if bounded_from_retry else 1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="bounded_sentence_preservation")
    line, why = _terminal_after_fidelity(list(first.get("reasons") or []) + list(second.get("reasons") or []))
    checked_line = _check({"player_facing_text": line})
    if not checked_line.get("hard_valid"):
        regenerated["player_facing_text"] = "I cannot provide a validated response to that request."
        return _finish(mark_candidate_rejected(regenerated, regenerated["player_facing_text"],
                                               list(checked_line.get("reasons") or [])),
                       why="controlled_validation_failure")
    safe_validation = checked_line
    # Keep the rejected attempt record beside the safe seal.
    sealed = seal_accepted_response(
        regenerated,
        text=line,
        provenance=PROVENANCE_SAFE,
        attempt=2,
        validation=safe_validation,
        contract=contract,
        player_text=player,
        resolution=resolution,
    )
    sealed_meta = sealed.setdefault("metadata", {})
    if isinstance(sealed_meta, dict):
        sealed_meta["rejected_attempt_2_reasons"] = list(second["reasons"])
        sealed_meta["generation_attempt_count"] = 2
    if provenance_is_safe(sealed):
        sealed["retry_exhausted"] = True
        sealed["targeted_retry_terminal"] = True
    return _finish(sealed, why=why)


def provenance_is_safe(gm: Mapping[str, Any] | None) -> bool:
    record = accepted_record(gm)
    return bool(record and record.get("provenance") == PROVENANCE_SAFE)


def commit_text(gm: Mapping[str, Any] | None) -> str:
    """Text that discourse and claim notes are allowed to describe."""
    if isinstance(gm, Mapping) and response_is_immutable(gm):
        record = accepted_record(gm) or {}
        return str(record.get("text") or "")
    if isinstance(gm, Mapping) and not effects_allowed(gm):
        return ""
    if isinstance(gm, Mapping):
        return str(gm.get("player_facing_text") or "")
    return ""
