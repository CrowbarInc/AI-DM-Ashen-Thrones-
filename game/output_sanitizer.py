from __future__ import annotations

import json
import re
from typing import Any, Dict

# Centralized exact phrases that must never leak as-is.
DISALLOWED_EXACT_PHRASES: tuple[str, ...] = (
    "I need a more concrete action or target to resolve that procedurally.",
)

# Centralized heuristic patterns for scaffold/procedural leakage.
DISALLOWED_HEURISTIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi need a more concrete action\b", re.IGNORECASE),
    re.compile(r"\bresolve that procedurally\b", re.IGNORECASE),
    re.compile(r"\bcannot determine roll requirements yet\b", re.IGNORECASE),
    re.compile(r"\bstate the specific action and target first\b", re.IGNORECASE),
    re.compile(r"\bneed a concrete, in-scene target\b", re.IGNORECASE),
    re.compile(r"\bdistance is not established in authoritative state yet\b", re.IGNORECASE),
    re.compile(r"\bfrom established state\b", re.IGNORECASE),
)

# Internal labels that should never appear in player-facing prose.
_INTERNAL_LABEL_PREFIXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*adjudication\s*[:\-–—]\s*", re.IGNORECASE),
    re.compile(r"^\s*validator\s*[:\-–—]\s*", re.IGNORECASE),
    re.compile(r"^\s*router\s*[:\-–—]\s*", re.IGNORECASE),
    re.compile(r"^\s*planner\s*[:\-–—]\s*", re.IGNORECASE),
)

# Hard-drop indicators when no plausible diegetic rewrite can be inferred.
_DROP_LINE_HINTS: tuple[str, ...] = (
    "from established state",
    "authoritative state",
    "resolve that procedurally",
)

_FULL_TEXT_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = ()

_SENTENCE_TERMINATORS = ".!?"
_CLOSING_PUNCT_OR_QUOTES = "\"')]}»”’"

_VISUAL_GROUNDED_HINTS: tuple[str, ...] = (
    "see",
    "seen",
    "saw",
    "look",
    "looks",
    "looked",
    "watch",
    "watched",
    "glance",
    "glances",
    "glanced",
    "hear",
    "heard",
    "sound",
    "sounds",
    "smell",
    "smells",
    "felt",
    "feel",
    "visible",
    "appears in",
    "flicker",
    "flickers",
    "shadow",
    "shadows",
    "silhouette",
)

_ANALYTICAL_PHRASE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("you can trace", re.compile(r"\byou\s+can\s+trace\b", re.IGNORECASE)),
    ("you can narrow it", re.compile(r"\byou\s+can\s+narrow\s+it\b", re.IGNORECASE)),
    ("you might want to", re.compile(r"\byou\s+might\s+want\s+to\b", re.IGNORECASE)),
    ("you can", re.compile(r"\byou\s+can\b", re.IGNORECASE)),
    ("only fragments of", re.compile(r"\bonly\s+fragments\s+of\b", re.IGNORECASE)),
    ("no clear answer", re.compile(r"\bno\s+clear\s+answer\b", re.IGNORECASE)),
    ("another name seems to", re.compile(r"\banother\s+name\s+seems\s+to\b", re.IGNORECASE)),
    ("the scene suggests", re.compile(r"\bthe\s+scene\s+suggests\b", re.IGNORECASE)),
    ("it can be inferred", re.compile(r"\bit\s+can\s+be\s+inferred\b", re.IGNORECASE)),
    ("it appears that", re.compile(r"\bit\s+appears\s+that\b", re.IGNORECASE)),
)

_DIRECTIVE_PHRASE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou\s+should\b", re.IGNORECASE),
    re.compile(r"\byou\s+might\b", re.IGNORECASE),
    re.compile(r"\byou\s+could\b", re.IGNORECASE),
    re.compile(r"\byou\s+want\s+to\b", re.IGNORECASE),
    re.compile(r"\bperhaps\s+you\s+could\b", re.IGNORECASE),
    re.compile(r"\bif\s+you\s+want\b", re.IGNORECASE),
    re.compile(r"\bconsider\s+asking\b", re.IGNORECASE),
)

_IMPLICIT_IMPERATIVE_START_RE = re.compile(
    r"^\s*(?P<lemma>investigate|observe|follow|approach|examine|check|track|ask|head\s+toward|go\s+to)\b(?:\s+(?P<object>.+))?$",
    re.IGNORECASE,
)

_ADVISORY_PHRASE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bit\s+is\s+advisable(?:\s+to)?\b", re.IGNORECASE),
    re.compile(r"\bit\s+would\s+be\s+wise(?:\s+to)?\b", re.IGNORECASE),
    re.compile(r"\bbest\s+to\b", re.IGNORECASE),
    re.compile(r"\bworth\s+investigating\b", re.IGNORECASE),
    re.compile(r"\bcould\s+be\s+worth\b", re.IGNORECASE),
    re.compile(r"\bmight\s+be\s+useful\s+to\b", re.IGNORECASE),
)

_IDENTITY_SYSTEM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*you\s+recognize\s+them\s+as\b", re.IGNORECASE),
    re.compile(r"^\s*that\s+person\s+is\b", re.IGNORECASE),
    re.compile(r"^\s*this\s+is\b", re.IGNORECASE),
)

_IMPERATIVE_OR_META_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*start with\b", re.IGNORECASE),
    re.compile(r"^\s*(?:you might\s+)?start by\b", re.IGNORECASE),
    re.compile(r"^\s*follow\b", re.IGNORECASE),
    re.compile(r"^\s*state exactly\b", re.IGNORECASE),
    re.compile(r"^\s*force\b", re.IGNORECASE),
    re.compile(r"\bstate exactly what you do\b", re.IGNORECASE),
    re.compile(r"\bresolve that procedurally\b", re.IGNORECASE),
    re.compile(r"\bmore concrete action\b", re.IGNORECASE),
    re.compile(r"\bstate the specific action and target first\b", re.IGNORECASE),
    re.compile(r"\bauthoritative state\b", re.IGNORECASE),
    re.compile(r"\bestablished state\b", re.IGNORECASE),
    re.compile(r"\bscaffold\b", re.IGNORECASE),
    re.compile(r"\b(?:planner|router|validator|adjudication)\b", re.IGNORECASE),
)

_KNOWN_SPLICE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bstart leaves by\b", re.IGNORECASE),
    re.compile(r"\bstay with many want it\b", re.IGNORECASE),
    re.compile(r"\bforce the next name behind them into the open\b", re.IGNORECASE),
)

_TEMPLATE_FRAGMENT_PHRASES: tuple[str, ...] = (
    "remains within reach",
    "framed by the noise",
    "another name",
    "the next name",
    "surrounding the tavern or",
    "details that do not quite fit",
)

_CONJUNCTION_COLLISION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bor\s+(?:approach|investigate|observe|follow|examine|check|track|ask)\b", re.IGNORECASE),
    re.compile(r"\band\s+remains\s+within\s+reach\b", re.IGNORECASE),
    re.compile(r"\bor\s+[a-z]+ing\b", re.IGNORECASE),
)

_FINAL_INTERNAL_STYLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:planner|router|validator|adjudication|scaffold)\b", re.IGNORECASE),
    re.compile(r"\b(?:the scene suggests|it can be inferred|no clear answer)\b", re.IGNORECASE),
)

_RESPONSE_SCHEMA_KEYS: tuple[str, ...] = (
    "player_facing_text",
    "tags",
    "scene_update",
    "activate_scene_id",
    "new_scene_draft",
    "world_updates",
    "suggested_action",
    "debug_notes",
)
_SCHEMA_KEY_ALT = "|".join(re.escape(k) for k in _RESPONSE_SCHEMA_KEYS)
_QUOTED_RESPONSE_KEY_RE = re.compile(rf"""["'](?:{_SCHEMA_KEY_ALT})["']\s*:""", re.IGNORECASE)
_PLAYER_TEXT_KEY_RE = re.compile(r"""["']player_facing_text["']\s*:""", re.IGNORECASE)

_SCENE_AMBIGUITY_FALLBACKS: tuple[str, ...] = (
    "Nothing in the scene points to a clear answer yet.",
    "From here, no certain answer presents itself.",
    "The truth is still buried beneath rumor and rain.",
)

_NPC_IGNORANCE_FALLBACKS: tuple[str, ...] = (
    'He glances away. "I do not know that part for certain."',
    'She lowers her voice. "I have heard the talk, but not the names."',
    'They trade a quick look. "No one here can swear to it."',
)

_PROCEDURAL_INSUFFICIENCY_FALLBACKS: tuple[str, ...] = (
    "No answer presents itself from here; the only lead is the east lane.",
    "The truth stays locked until someone pushes a concrete move through the scene.",
    "The answer has not formed yet; one visible lead still stands open at the checkpoint.",
)


def resembles_serialized_response_payload(text: str) -> bool:
    """Heuristic detector for leaked serialized response schema text."""
    if not isinstance(text, str):
        return False
    s = text.strip()
    if not s:
        return False

    key_matches = list(_QUOTED_RESPONSE_KEY_RE.finditer(s))
    if not key_matches:
        return False

    key_count = len(key_matches)
    objectish = any(tok in s for tok in ("{", "}", "[", "]", ",", ":"))
    has_player_key = bool(_PLAYER_TEXT_KEY_RE.search(s))

    # Two+ schema keys or any explicit player_facing_text key is enough.
    if key_count >= 2 or has_player_key:
        return True
    # Single schema key plus object-like punctuation catches truncated fragments.
    return objectish and key_count >= 1


def _extract_object_candidate(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    if start != -1:
        return text[start:]
    return text


def _decode_jsonish_string(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except Exception:
        # Minimal safe unescape fallback for malformed quoted segments.
        return (
            raw.replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\r", "\r")
            .replace("\\\\", "\\")
        )


def extract_player_text_from_serialized_payload(text: str) -> str | None:
    """Extract only player_facing_text from leaked serialized payload text."""
    if not isinstance(text, str) or not text.strip():
        return None
    if not resembles_serialized_response_payload(text):
        return None

    candidate = _extract_object_candidate(text)
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            value = parsed.get("player_facing_text")
            if isinstance(value, str) and value.strip():
                return value.strip()
    except Exception:
        pass

    key_match = _PLAYER_TEXT_KEY_RE.search(text)
    if not key_match:
        return None

    i = key_match.end()
    n = len(text)
    while i < n and text[i].isspace():
        i += 1
    if i >= n:
        return None

    if text[i] in ('"', "'"):
        quote = text[i]
        i += 1
        escaped = False
        buff: list[str] = []
        while i < n:
            ch = text[i]
            if escaped:
                buff.append(ch)
                escaped = False
            elif ch == "\\":
                buff.append(ch)
                escaped = True
            elif ch == quote:
                value = _decode_jsonish_string("".join(buff)).strip()
                return value or None
            else:
                buff.append(ch)
            i += 1
        # Malformed/truncated quote: keep what we captured.
        value = _decode_jsonish_string("".join(buff)).strip()
        return value or None

    # Non-quoted malformed value fallback.
    tail = text[i:]
    value = re.split(r"[,}\n\r]", tail, maxsplit=1)[0].strip()
    return value or None


def strip_serialized_payload_fragments(text: str) -> str:
    """Best-effort removal for leaked schema fragments when extraction fails."""
    if not isinstance(text, str):
        return ""
    if not resembles_serialized_response_payload(text):
        return text

    first_key = _QUOTED_RESPONSE_KEY_RE.search(text)
    if first_key:
        prefix = text[: first_key.start()].rstrip(" \t\r\n,;:-{[")
        # Keep narrative lead-in if it looks like real prose/dialogue.
        if len(re.findall(r"[A-Za-z']+", prefix)) >= 3:
            return prefix

    cleaned_lines = [ln for ln in text.splitlines() if not _QUOTED_RESPONSE_KEY_RE.search(ln)]
    return "\n".join(cleaned_lines).strip(" \t\r\n,;:-{}[]")


def _strip_internal_prefixes(line: str) -> str:
    out = line
    for pat in _INTERNAL_LABEL_PREFIXES:
        out = pat.sub("", out, count=1)
    return out.strip()


def _has_unrecoverable_fragment_shape(text: str) -> bool:
    if not isinstance(text, str):
        return True
    s = text.strip()
    if not s:
        return True
    if len(re.findall(r"[A-Za-z']+", s)) < 3:
        return True
    if re.fullmatch(r"[^\w]+", s):
        return True
    if s.count("{") > s.count("}") + 1:
        return True
    if s.count("[") > s.count("]") + 1:
        return True
    return False


def _context_prefers_npc_uncertainty(context: Dict[str, Any] | None) -> bool:
    if not isinstance(context, dict):
        return False
    resolution = context.get("resolution")
    if not isinstance(resolution, dict):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind in {"question", "social", "social_exchange", "persuade", "deceive", "intimidate", "barter", "ask"}:
        return True
    if isinstance(resolution.get("social"), dict):
        return True
    social_intent = str((resolution.get("metadata") or {}).get("social_intent_class") or "").strip().lower()
    return social_intent in {"social_exchange", "interrogation", "negotiation"}


def _looks_like_npc_exchange(text: str, context: Dict[str, Any] | None) -> bool:
    s = (text or "").strip()
    low = s.lower()
    if '"' in s and re.search(r"\b(says|asks|replies|murmurs|whispers)\b", low):
        return True
    if re.search(r"\b(?:he|she|they)\s+(?:glances|lowers|shrugs|leans)\b", low):
        return True
    if re.search(r"\b(?:i|we)\s+(?:don't|do not|can't|cannot)\s+(?:know|say|swear|name)\b", low):
        return True
    return _context_prefers_npc_uncertainty(context) and _looks_like_dialogue(s)


def _context_prefers_procedural_insufficiency(context: Dict[str, Any] | None) -> bool:
    if not isinstance(context, dict):
        return False
    resolution = context.get("resolution")
    if not isinstance(resolution, dict):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind == "adjudication_query":
        return True
    if bool(resolution.get("requires_check")):
        return True
    check_request = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    if bool(check_request.get("requires_check")):
        return True
    adjudication = resolution.get("adjudication") if isinstance(resolution.get("adjudication"), dict) else {}
    return str(adjudication.get("answer_type") or "").strip().lower() in {"needs_concrete_action", "check_required"}


def _infer_uncertainty_source_mode(
    context: Dict[str, Any] | None,
    source_text: str,
    explicit_mode: str | None = None,
) -> str:
    if explicit_mode in {"npc", "narration"}:
        return "npc_ignorance" if explicit_mode == "npc" else "scene_ambiguity"
    if _context_prefers_procedural_insufficiency(context):
        return "procedural_insufficiency"
    if _looks_like_npc_exchange(source_text, context):
        return "npc_ignorance"
    if re.search(
        r"\b(resolve that procedurally|more concrete action|cannot determine roll requirements yet|state the specific action and target first|need a concrete, in-scene target)\b",
        source_text or "",
        re.IGNORECASE,
    ):
        return "procedural_insufficiency"
    return "scene_ambiguity"


def _diegetic_uncertainty_fallback(
    context: Dict[str, Any] | None,
    *,
    mode: str | None = None,
    source_text: str = "",
) -> str:
    source_mode = _infer_uncertainty_source_mode(context, source_text, explicit_mode=mode)
    templates = {
        "npc_ignorance": _NPC_IGNORANCE_FALLBACKS,
        "scene_ambiguity": _SCENE_AMBIGUITY_FALLBACKS,
        "procedural_insufficiency": _PROCEDURAL_INSUFFICIENCY_FALLBACKS,
    }.get(source_mode, _SCENE_AMBIGUITY_FALLBACKS)
    seed = source_text.strip() or source_mode
    idx = sum(ord(ch) for ch in seed) % len(templates)
    return templates[idx]


def _rewrite_line(line: str, context: Dict[str, Any]) -> str:
    clean = _strip_internal_prefixes(line)
    low = clean.lower()
    if not clean:
        return ""
    if re.search(r"\b(?:scaffold|planner|router|validator)\b", low):
        return _diegetic_uncertainty_fallback(context, source_text=clean)

    if (
        "more concrete action" in low
        or "resolve that procedurally" in low
        or "cannot determine roll requirements yet" in low
        or "state the specific action and target first" in low
        or "need a concrete, in-scene target" in low
    ):
        return _diegetic_uncertainty_fallback(context, source_text=clean)

    if "distance is not established in authoritative state yet" in low:
        return "The distance is unclear from where you stand."

    if "from established state" in low:
        return _diegetic_uncertainty_fallback(context, source_text=clean)

    for hint in _DROP_LINE_HINTS:
        if hint in low:
            if _has_unrecoverable_fragment_shape(clean):
                return ""
            return _diegetic_uncertainty_fallback(context, source_text=clean)

    return clean


def _log_sanitizer_event(context: Dict[str, Any], event: str, sentence: str) -> None:
    if not isinstance(context, dict):
        return
    debug_log = context.setdefault("sanitizer_debug", [])
    if isinstance(debug_log, list):
        debug_log.append({"event": event, "sentence": sentence[:240]})


def _contains_template_fragment(sentence: str) -> bool:
    low = (sentence or "").lower()
    return any(fragment in low for fragment in _TEMPLATE_FRAGMENT_PHRASES)


def _simple_diegetic_fallback(sentence: str, context: Dict[str, Any] | None = None) -> str:
    low = (sentence or "").lower()
    if "man in tattered clothes" in low:
        return "The man in tattered clothes lingers nearby, watching the crowd."
    if "runner" in low:
        return "The runner lingers at the edge of the crowd, listening."
    if "notice board" in low:
        return "The notice board stands nearby, crowded with damp postings."
    if "guard" in low:
        return "A guard watches the lane with one hand on the spear."
    return _diegetic_uncertainty_fallback(context, mode="narration", source_text=sentence)


def _fails_final_validation_heuristics(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    if _contains_template_fragment(s):
        return True
    if any(p.search(s) for p in _CONJUNCTION_COLLISION_PATTERNS):
        return True
    if any(p.search(s) for p in _FINAL_INTERNAL_STYLE_PATTERNS):
        return True
    if _is_spliced_or_malformed(s) or _looks_like_sentence_fragment(s):
        return True
    # Heuristic abrupt shift: unresolved conjunction between two scene anchors.
    if re.search(r"\b(?:tavern|gate|crowd)\b.+\bor\s+(?:approach|follow|ask)\b", s, flags=re.IGNORECASE):
        return True
    return False


def _collapse_inline_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _split_sentences(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    src = text.replace("\r\n", "\n").replace("\r", "\n")
    if not src.strip():
        return []

    sentences: list[str] = []
    buff: list[str] = []
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]

        # Preserve paragraph boundaries as sentence boundaries while avoiding
        # accidental fragment merges across dropped lines.
        if ch == "\n":
            if i + 1 < n and src[i + 1] == "\n":
                flushed = _collapse_inline_whitespace("".join(buff))
                if flushed:
                    sentences.append(flushed)
                buff = []
                while i + 1 < n and src[i + 1] == "\n":
                    i += 1
                i += 1
                continue
            buff.append(" ")
            i += 1
            continue

        buff.append(ch)
        if ch in _SENTENCE_TERMINATORS:
            j = i + 1
            while j < n and src[j] in _CLOSING_PUNCT_OR_QUOTES:
                buff.append(src[j])
                j += 1
            flushed = _collapse_inline_whitespace("".join(buff))
            if flushed:
                sentences.append(flushed)
            buff = []
            while j < n and src[j].isspace():
                j += 1
            i = j
            continue
        i += 1

    tail = _collapse_inline_whitespace("".join(buff))
    if tail:
        sentences.append(tail)
    # Keep quoted speech + attribution together.
    merged: list[str] = []
    idx = 0
    while idx < len(sentences):
        current = sentences[idx]
        if idx + 1 < len(sentences):
            nxt = sentences[idx + 1]
            if re.search(r'["\']\s*$', current) and re.match(
                r"^(the|a|an|he|she|they|i|we|you|[A-Z][a-z]+)\b",
                nxt,
                flags=re.IGNORECASE,
            ) and re.search(
                r"\b(says|asks|asked|replies|reply|adds|added|murmurs|whispers|shouts|calls)\b",
                nxt,
                flags=re.IGNORECASE,
            ):
                merged.append(f"{current} {nxt}".strip())
                idx += 2
                continue
        merged.append(current)
        idx += 1
    return merged


def _looks_like_dialogue(sentence: str) -> bool:
    s = sentence.strip()
    if '"' in s:
        return True
    lower = s.lower()
    return lower.startswith(("i say", "you say", "he says", "she says", "they say", "someone says"))


def _looks_like_internal_thought(sentence: str) -> bool:
    lower = sentence.strip().lower()
    return lower.startswith(("i think", "you wonder", "he wonders", "she wonders", "they wonder"))


def _is_spliced_or_malformed(sentence: str) -> bool:
    low = sentence.strip().lower()
    if any(p.search(sentence) for p in _KNOWN_SPLICE_PATTERNS):
        return True
    if re.match(r"^(and|but|or|with|into|behind|then)\b", low):
        return True
    if "..." in sentence and not re.search(r"\.\.\.\s*[A-Z\"]", sentence):
        return True
    if "start with" in low or "follow " in low or "force " in low:
        return True
    return False


def _rewrite_instructional_sentence(sentence: str, context: Dict[str, Any] | None = None) -> str:
    s = sentence.strip().strip(" -:;")
    low = s.lower()

    if "state exactly what you do" in low:
        return ""
    if "more concrete action" in low or "resolve that procedurally" in low:
        return _diegetic_uncertainty_fallback(context, source_text=s)
    if "force the next name behind them into the open" in low:
        return "Another name seems to sit behind the story, still out of reach."
    if re.search(r"\bno name or badge anyone would trust has surfaced\b", low):
        return "No trustworthy name or badge has surfaced yet."

    if "start leaves by speaking to" in low:
        subject = _extract_subject_after_phrase(s, r"\bstart\s+leaves\s+by\s+speaking\s+to\s+([^.,;!?]+)")
        if subject:
            return f"{_subject_with_article(subject)} lingers nearby, watching the crowd."
        return _simple_diegetic_fallback(s, context)

    start_match = re.search(r"\bstart with\s+([^.,;]+)", s, flags=re.IGNORECASE)
    if start_match:
        subject = start_match.group(1).strip()
        if re.match(r"^(a|an|the)\s+", subject, flags=re.IGNORECASE):
            return f"{subject[0].upper()}{subject[1:]} lingers nearby, watching the crowd."
        return f"A {subject} lingers nearby, watching the crowd."

    start_by_match = re.search(r"\bstart by speaking to\s+([^.,;]+)", s, flags=re.IGNORECASE)
    if start_by_match:
        subject = start_by_match.group(1).strip()
        if re.match(r"^(the|a|an)\s+", subject, flags=re.IGNORECASE):
            return f"{subject[0].upper()}{subject[1:]} watches from the edge of the crowd."
        return f"{subject[0].upper()}{subject[1:]} watches from the edge of the crowd."

    follow_match = re.search(r"\bfollow\s+([^.,;]+)", s, flags=re.IGNORECASE)
    if follow_match:
        subject = follow_match.group(1).strip()
        if subject:
            if re.match(r"^(the|a|an)\s+", subject, flags=re.IGNORECASE):
                return f"{subject[0].upper()}{subject[1:]} moves ahead through the scene."
            return f"{subject[0].upper()}{subject[1:]} moves ahead through the scene."

    if any(p.search(s) for p in _IMPERATIVE_OR_META_PATTERNS):
        if _has_unrecoverable_fragment_shape(s):
            return ""
        return _diegetic_uncertainty_fallback(context, source_text=s)
    return s


def _detect_analytical_phrases(sentence: str) -> list[str]:
    low = (sentence or "").lower()
    if not low.strip():
        return []
    detected: list[str] = []
    for label, pattern in _ANALYTICAL_PHRASE_PATTERNS:
        if label == "it appears that":
            if not pattern.search(sentence):
                continue
            # Keep sensory "it appears that..." constructions when they are grounded.
            if any(hint in low for hint in _VISUAL_GROUNDED_HINTS):
                continue
            detected.append(label)
            continue
        if pattern.search(sentence):
            detected.append(label)
    return detected


def _infer_analytical_strategy(markers: list[str], context: Dict[str, Any] | None) -> str:
    marker_set = set(markers)
    if {"you can", "you can trace", "you can narrow it", "you might want to"} & marker_set:
        return "diegetic_observation"
    if _context_prefers_npc_uncertainty(context) and {"no clear answer", "it can be inferred", "the scene suggests"} & marker_set:
        return "npc_bounded_uncertainty"
    if "another name seems to" in marker_set:
        return "environmental_implication"
    if {"only fragments of", "it appears that", "it can be inferred", "the scene suggests"} & marker_set:
        return "environmental_implication"
    if "no clear answer" in marker_set:
        return "npc_bounded_uncertainty" if _context_prefers_npc_uncertainty(context) else "environmental_implication"
    return "diegetic_observation"


def rewrite_analytical_sentence(sentence: str, context: Dict[str, Any] | None = None) -> str:
    s = (sentence or "").strip()
    if not s:
        return ""

    markers = _detect_analytical_phrases(s)
    if not markers:
        return s

    low = s.lower()
    strategy = _infer_analytical_strategy(markers, context)

    if strategy == "diegetic_observation":
        if "you might want to" in low and "runner" in low:
            return "The runner watches the crowd, clearly listening for more than he says."
        if "notice board" in low:
            return "The notice board is crowded with fresh postings, edges torn and re-pinned by too many hurried hands."
        if "trace what happened" in low:
            return "Scuffed mud, broken chalk, and damp paper scraps mark where the crowd surged and split."
        if "narrow it" in low:
            return "Two details stand out: fresh boot tracks toward the east lane and a clerk who will not meet your eyes."
        if "only fragments of" in low or "method" in low:
            return "Scattered signs-broken seals, hushed arguments, and half-torn notices-hint at a plan no one admits aloud."
        return "Around you, small details sharpen into clues: wet footprints, lowered voices, and doors closing a moment too fast."

    if strategy == "npc_bounded_uncertainty":
        return _diegetic_uncertainty_fallback(context, mode="npc", source_text=s)

    # environmental_implication
    if "another name seems to" in low:
        return "Another name rides the edge of each whisper, but every voice drops before it is spoken."
    if "no clear answer" in low:
        return "Rain beads on stone while rumors cross and recross the square without settling on one truth."
    if "only fragments of" in low:
        return "Scattered signs-broken seals, hushed arguments, and half-torn notices-hint at something organized, never complete."
    if "the scene suggests" in low or "it can be inferred" in low or "it appears that" in low:
        return "Taken together, the marks in the mud and the clipped exchanges point toward someone still moving behind the crowd."
    return "The scene holds together in fragments, enough to raise suspicion but not enough to name a culprit."


def _contains_directive_phrase(sentence: str) -> bool:
    return any(p.search(sentence or "") for p in _DIRECTIVE_PHRASE_PATTERNS)


def _extract_subject_after_phrase(sentence: str, phrase_re: str) -> str | None:
    match = re.search(phrase_re, sentence, flags=re.IGNORECASE)
    if not match:
        return None
    subject = match.group(1).strip(" .,:;!?-")
    if not subject:
        return None
    # Remove trailing infinitive helper if present.
    subject = re.sub(r"^(?:to\s+)?", "", subject, flags=re.IGNORECASE)
    return subject.strip() or None


def _rewrite_directive_sentence(sentence: str, context: Dict[str, Any] | None = None) -> str:
    s = (sentence or "").strip().strip(" -:;")
    if not s:
        return ""
    low = s.lower()

    if "notice board" in low:
        return "The notice board stands nearby, its fresh postings drawing uneasy glances."
    if "runner" in low and re.search(r"\b(ask|question|speak|talk|consider asking)\b", low):
        return "The runner watches the crowd, clearly listening for more than he says."

    target = (
        _extract_subject_after_phrase(s, r"\b(?:you\s+should|you\s+could|perhaps\s+you\s+could)\s+([^.,;!?]+)")
        or _extract_subject_after_phrase(s, r"\byou\s+might(?:\s+want\s+to)?\s+([^.,;!?]+)")
        or _extract_subject_after_phrase(s, r"\bif\s+you\s+want(?:\s+to)?\s+([^.,;!?]+)")
        or _extract_subject_after_phrase(s, r"\bconsider\s+asking\s+([^.,;!?]+)")
        or _extract_subject_after_phrase(s, r"\byou\s+want\s+to\s+([^.,;!?]+)")
    )
    if target:
        if re.match(r"^(the|a|an)\s+", target, flags=re.IGNORECASE):
            return f"{target[0].upper()}{target[1:]} lingers nearby, half-hidden in the crowd."
        return f"{target[0].upper()}{target[1:]} lingers nearby, half-hidden in the crowd."

    # Last-resort diegetic fallback with no direct instruction language.
    return _diegetic_uncertainty_fallback(context, mode="narration", source_text=s)


def _rewrite_identity_system_sentence(sentence: str) -> str:
    s = (sentence or "").strip()
    if not s:
        return ""
    if not any(p.search(s) for p in _IDENTITY_SYSTEM_PATTERNS):
        return s
    low = s.lower()
    if "runner" in low:
        return "The runner shifts under your gaze."
    if "guard" in low:
        return "A guard tightens their grip on the spear and watches for your next move."
    # Prefer dropping synthetic identity framing when no natural rewrite is obvious.
    return ""


def _normalize_subject_phrase(subject: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", (subject or "")).strip(" .,:;!?-")
    if not cleaned:
        return None
    cleaned = re.sub(r"^(?:to\s+)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:discreetly|quietly|carefully|immediately|now)\b$", "", cleaned, flags=re.IGNORECASE).strip(
        " .,:;!?-"
    )
    if not cleaned:
        return None
    return cleaned


def _subject_with_article(subject: str) -> str:
    if re.match(r"^(?:the|a|an|this|that|these|those)\s+", subject, flags=re.IGNORECASE):
        return f"{subject[0].upper()}{subject[1:]}"
    return f"The {subject}"


def _extract_advisory_target(sentence: str) -> str | None:
    s = sentence.strip()
    action_match = re.search(
        r"\b(?:it\s+is\s+advisable(?:\s+to)?|it\s+would\s+be\s+wise(?:\s+to)?|best\s+to|might\s+be\s+useful\s+to)\s+([^.?!,;]+)",
        s,
        flags=re.IGNORECASE,
    )
    if action_match:
        phrase = action_match.group(1).strip()
        lead = re.match(
            r"^(?:investigate|observe|follow|approach|examine|check|track|ask|head\s+toward|go\s+to)\s+(.+)$",
            phrase,
            flags=re.IGNORECASE,
        )
        if lead:
            return _normalize_subject_phrase(lead.group(1))
    worth_match = re.search(r"\b(?:worth\s+investigating|could\s+be\s+worth)\s+([^.?!,;]+)", s, flags=re.IGNORECASE)
    if worth_match:
        return _normalize_subject_phrase(worth_match.group(1))
    return None


def _contains_implicit_instruction(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return False
    if _IMPLICIT_IMPERATIVE_START_RE.search(s):
        return True
    return any(p.search(s) for p in _ADVISORY_PHRASE_PATTERNS)


def _rewrite_implicit_instruction_sentence(sentence: str) -> str:
    s = (sentence or "").strip().strip(" -:;")
    if not s:
        return ""

    imperative_match = _IMPLICIT_IMPERATIVE_START_RE.search(s)
    if imperative_match:
        lemma = re.sub(r"\s+", " ", (imperative_match.group("lemma") or "").strip().lower())
        subject = _normalize_subject_phrase(imperative_match.group("object") or "")
        if subject:
            framed = _subject_with_article(subject)
            if lemma in {"investigate", "examine", "check", "track"}:
                return f"{framed} bears subtle signs of recent movement: scuffed edges and damp marks."
            if lemma == "observe":
                return f"{framed} keeps drawing stray glances, never still for long."
            if lemma in {"follow", "approach", "head toward", "go to"}:
                return f"{framed} stays near the edge of the scene, close enough to watch without speaking."
            if lemma == "ask":
                return f"{framed} listens in silence, weighing each word before answering."
        return "A quiet opening hangs in the scene, carried by glances and half-finished whispers."

    advisory_target = _extract_advisory_target(s)
    if advisory_target:
        framed = _subject_with_article(advisory_target)
        return f"{framed} keeps to the margins of the crowd, as if waiting to be noticed."
    return "The scene offers an opening, but every voice keeps it wrapped in implication."


def _is_diegetic_sentence(sentence: str) -> bool:
    if re.fullmatch(r"\[[^\]]+\]", sentence.strip()):
        return True
    if _looks_like_dialogue(sentence) or _looks_like_internal_thought(sentence):
        return True
    if any(p.search(sentence) for p in _IMPERATIVE_OR_META_PATTERNS):
        return False
    if _is_spliced_or_malformed(sentence):
        return False
    word_count = len(re.findall(r"[A-Za-z']+", sentence))
    return word_count >= 3


def _cohere_sentences(sentences: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        clean = re.sub(r"\s+", " ", sentence).strip()
        if not clean:
            continue
        clean = re.sub(r"[ ]+([,.;!?])", r"\1", clean)
        clean = re.sub(r"([!?.,])\1{1,}", r"\1", clean)
        if re.fullmatch(r"\[[^\]]+\]", clean):
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(clean)
            continue
        if clean.endswith("..."):
            clean = clean[:-3].rstrip() + "."
        if not re.search(r"[.!?]$", clean):
            clean += "."
        key = re.sub(r"\s+", " ", clean.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _looks_like_sentence_fragment(sentence: str) -> bool:
    s = sentence.strip()
    if not s:
        return True
    if re.fullmatch(r"\[[^\]]+\]", s):
        return False
    if _looks_like_dialogue(s) or _looks_like_internal_thought(s):
        return False
    words = re.findall(r"[A-Za-z']+", s)
    if len(words) < 3:
        return True
    if s[-1] in ",:;-":
        return True
    if s.count('"') % 2 != 0:
        return True
    if s.count("(") != s.count(")"):
        return True
    if re.match(r"^(and|but|or|with|into|behind|then|because)\b", s.lower()):
        return True
    # Drop terse clause-like fragments that rarely stand on their own.
    if len(words) <= 5:
        has_subject = bool(re.search(r"^(?:the|a|an|i|you|he|she|they|we|it|[A-Z][a-z]+)\b", s))
        has_verb = bool(
            re.search(
                r"\b(is|are|was|were|be|been|do|does|did|has|have|had|[a-z]+(?:s|ed|ing))\b",
                s.lower(),
            )
        )
        if not (has_subject and has_verb):
            return True
    return False


def _dedupe_repeated_fragment(sentence: str) -> str:
    s = re.sub(r"\s+", " ", sentence).strip()
    m = re.match(r"^(.{8,}?)\s+\1([.!?])?$", s, flags=re.IGNORECASE)
    if m:
        return (m.group(1).strip() + (m.group(2) or ".")).strip()
    return s


def _has_orphan_pronoun_lead(sentence: str, *, has_previous: bool) -> bool:
    if has_previous:
        return False
    s = (sentence or "").strip()
    if not s:
        return True
    if _looks_like_dialogue(s):
        return False
    return bool(re.match(r"^(he|she|they|it|this|that|these|those)\b", s, flags=re.IGNORECASE))


def _has_orphan_quote_shape(sentence: str) -> bool:
    s = (sentence or "").strip()
    return bool(s) and s.count('"') % 2 != 0


def _rewrite_sentence_atomically(sentence: str, context: Dict[str, Any] | None = None) -> str:
    s = _strip_internal_prefixes(sentence).strip()
    if not s:
        return ""

    # Start from explicit procedural/internal leakage to avoid carrying remnants.
    if any(p.search(s) for p in _IMPERATIVE_OR_META_PATTERNS):
        s = _rewrite_instructional_sentence(s, context).strip()
    if not s:
        return ""

    if any(pattern.search(s) for pattern in DISALLOWED_HEURISTIC_PATTERNS):
        s = _diegetic_uncertainty_fallback(context, source_text=s)

    rewritten_identity = _rewrite_identity_system_sentence(s).strip()
    if not rewritten_identity:
        return ""
    s = rewritten_identity

    if _detect_analytical_phrases(s):
        s = rewrite_analytical_sentence(s, context).strip()
    if not s:
        return ""

    if _contains_directive_phrase(s):
        s = _rewrite_directive_sentence(s, context).strip()
    if not s:
        return ""

    if _contains_implicit_instruction(s):
        s = _rewrite_implicit_instruction_sentence(s).strip()
    if not s:
        return ""

    if _contains_template_fragment(s) or any(p.search(s) for p in _CONJUNCTION_COLLISION_PATTERNS):
        s = _simple_diegetic_fallback(s, context).strip()
    if not s:
        return ""

    if _has_orphan_quote_shape(s):
        s = _diegetic_uncertainty_fallback(context, source_text=s)

    if _fails_final_validation_heuristics(s):
        fallback = _simple_diegetic_fallback(s, context).strip()
        if not fallback or _fails_final_validation_heuristics(fallback):
            return ""
        s = fallback
    return s.strip()


def _classify_sentence_action(
    sentence: str,
    *,
    context: Dict[str, Any] | None = None,
    has_previous_kept_sentence: bool = False,
) -> tuple[str, str]:
    s = _strip_internal_prefixes(sentence).strip()
    if not s:
        return ("drop", "")
    if re.fullmatch(r"\[[^\]]+\]", s):
        return ("keep", s)

    # Hard-drop tiny debris and malformed remnants.
    if _has_unrecoverable_fragment_shape(s) and not _looks_like_dialogue(s):
        return ("drop", "")

    must_rewrite = False
    if any(phrase.lower() in s.lower() for phrase in DISALLOWED_EXACT_PHRASES):
        must_rewrite = True
    if any(pattern.search(s) for pattern in DISALLOWED_HEURISTIC_PATTERNS):
        must_rewrite = True
    if any(p.search(s) for p in _IMPERATIVE_OR_META_PATTERNS):
        must_rewrite = True
    if _detect_analytical_phrases(s):
        must_rewrite = True
    if _contains_directive_phrase(s) or _contains_implicit_instruction(s):
        must_rewrite = True
    if any(p.search(s) for p in _IDENTITY_SYSTEM_PATTERNS):
        must_rewrite = True
    if _contains_template_fragment(s) or any(p.search(s) for p in _CONJUNCTION_COLLISION_PATTERNS):
        must_rewrite = True
    if _is_spliced_or_malformed(s) or _has_orphan_quote_shape(s):
        must_rewrite = True
    if _has_orphan_pronoun_lead(s, has_previous=has_previous_kept_sentence):
        must_rewrite = True

    if must_rewrite:
        rewritten = _rewrite_sentence_atomically(s, context).strip()
        if not rewritten:
            return ("drop", "")
        return ("rewrite", rewritten)

    if not _is_diegetic_sentence(s) or _looks_like_sentence_fragment(s):
        return ("drop", "")
    return ("keep", s)


def final_coherence_pass(text: str) -> str:
    if not isinstance(text, str):
        return ""
    candidate_sentences = _split_sentences(text)
    cleaned: list[str] = []
    for sentence in candidate_sentences:
        s = _dedupe_repeated_fragment(sentence)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        if re.fullmatch(r"\[[^\]]+\]", s):
            cleaned.append(s)
            continue
        s = re.sub(r"[ ]+([,.;!?])", r"\1", s)
        if s and s[0].islower():
            # Repair simple lowercase starts; drop obvious malformed starts.
            if re.match(r"^[a-z][a-z'\-]+(?:\s+[a-z'\-]+){0,2}$", s):
                continue
            s = s[0].upper() + s[1:]
        if _looks_like_sentence_fragment(s):
            continue
        if not re.search(r"[.!?]$", s):
            s += "."
        cleaned.append(s)
    coherent = _cohere_sentences(cleaned)
    return " ".join(coherent).strip()


def atomic_rewrite_enforcement_pass(sentences: list[str], context: Dict[str, Any] | None = None) -> list[str]:
    out: list[str] = []
    for sentence in sentences:
        s = (sentence or "").strip()
        if not s:
            continue
        if _contains_template_fragment(s) or any(p.search(s) for p in _CONJUNCTION_COLLISION_PATTERNS):
            rewritten = _simple_diegetic_fallback(s, context).strip()
            if rewritten:
                out.append(rewritten)
            continue
        out.append(s)
    return out


def final_validation_pass(text: str, context: Dict[str, Any] | None = None) -> str:
    if not isinstance(text, str):
        return ""
    validated: list[str] = []
    for sentence in _split_sentences(text):
        s = (sentence or "").strip()
        if not s:
            continue
        if not _fails_final_validation_heuristics(s):
            validated.append(s)
            continue
        rewritten = _simple_diegetic_fallback(s, context).strip()
        if rewritten and not _fails_final_validation_heuristics(rewritten):
            validated.append(rewritten)
    return " ".join(_cohere_sentences(validated)).strip()


def sanitize_player_facing_output(text: str, context: Dict[str, Any] | None = None) -> str:
    """Hard final sanitization pass for player-facing output.

    Applies both full-text and line-level cleanup to prevent internal scaffold,
    planner/router/validator/adjudication leakage from reaching players.
    """
    if not isinstance(text, str):
        return ""

    ctx = context if isinstance(context, dict) else {}
    out = str(text)

    # STEP 1: structured firewall.
    if resembles_serialized_response_payload(out):
        extracted = extract_player_text_from_serialized_payload(out)
        out = extracted if isinstance(extracted, str) and extracted.strip() else strip_serialized_payload_fragments(out)

    # STEP 2: global pattern sanitizer.
    for pattern, replacement in _FULL_TEXT_REWRITES:
        out = pattern.sub(replacement, out)

    # STEP 3: sentence-atomic sanitizer.
    processed: list[str] = []
    for sentence in _split_sentences(out):
        action, resolved = _classify_sentence_action(
            sentence,
            context=ctx,
            has_previous_kept_sentence=bool(processed),
        )
        if action == "drop":
            _log_sanitizer_event(ctx, "dropped_sentence", sentence)
            continue
        if action == "rewrite" and resolved != sentence.strip():
            _log_sanitizer_event(ctx, "rewritten_sentence", sentence)
        processed.append(resolved)

    rebuilt = " ".join(_cohere_sentences(processed)).strip()

    # STEP 4: final validation and coherence.
    rebuilt = final_validation_pass(rebuilt, ctx)
    rebuilt = final_coherence_pass(rebuilt)

    # Final boundary guard to avoid any surviving schema leakage.
    if resembles_serialized_response_payload(rebuilt):
        extracted = extract_player_text_from_serialized_payload(rebuilt)
        rebuilt = extracted if isinstance(extracted, str) and extracted.strip() else strip_serialized_payload_fragments(rebuilt)
        rebuilt = re.sub(r"\s+", " ", rebuilt).strip()

    if not rebuilt:
        return "For a breath, the scene stays still."
    return rebuilt
