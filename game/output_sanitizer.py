from __future__ import annotations

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

_FULL_TEXT_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    # Join artifact cleanup seen in gauntlet concatenation.
    (
        re.compile(r"\byou might start leaves by speaking\b", re.IGNORECASE),
        "you might start by speaking",
    ),
    # Remove leaked label fragments that get spliced into valid narration.
    (
        re.compile(r"\b(?:internal|validator|router|planner)\s+(?:state|hint|instruction)s?\b", re.IGNORECASE),
        "",
    ),
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

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


def _strip_internal_prefixes(line: str) -> str:
    out = line
    for pat in _INTERNAL_LABEL_PREFIXES:
        out = pat.sub("", out, count=1)
    return out.strip()


def _rewrite_line(line: str, context: Dict[str, Any]) -> str:
    clean = _strip_internal_prefixes(line)
    low = clean.lower()
    if not clean:
        return ""
    if re.search(r"\b(?:scaffold|planner|router|validator)\b", low):
        clean = re.sub(r"\b(?:scaffold|planner|router|validator)\b", "", clean, flags=re.IGNORECASE).strip(" -:;,.")
        low = clean.lower()
        if not clean:
            return ""

    if (
        "more concrete action" in low
        or "resolve that procedurally" in low
        or "cannot determine roll requirements yet" in low
        or "state the specific action and target first" in low
        or "need a concrete, in-scene target" in low
    ):
        return "The scene offers no clear answer yet."

    if "distance is not established in authoritative state yet" in low:
        return "The distance is unclear from where you stand."

    if "from established state" in low and clean.endswith("."):
        return clean.replace("from established state", "from what you can see here").strip()

    for hint in _DROP_LINE_HINTS:
        if hint in low:
            return ""

    return clean


def _log_sanitizer_event(context: Dict[str, Any], event: str, sentence: str) -> None:
    if not isinstance(context, dict):
        return
    debug_log = context.setdefault("sanitizer_debug", [])
    if isinstance(debug_log, list):
        debug_log.append({"event": event, "sentence": sentence[:240]})


def _split_sentences(text: str) -> list[str]:
    chunks = _SENTENCE_SPLIT_RE.split(text)
    return [re.sub(r"\s+", " ", c).strip() for c in chunks if c and c.strip()]


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


def _rewrite_instructional_sentence(sentence: str) -> str:
    s = sentence.strip().strip(" -:;")
    low = s.lower()

    if "state exactly what you do" in low:
        return ""
    if "more concrete action" in low or "resolve that procedurally" in low:
        return "The scene offers no clear answer yet."
    if "force the next name behind them into the open" in low:
        return "Another name seems to sit behind the story, still out of reach."
    if re.search(r"\bno name or badge anyone would trust has surfaced\b", low):
        return "No trustworthy name or badge has surfaced yet."

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
        return "The scene offers no clear answer yet."
    return s


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


def sanitize_player_facing_output(text: str, context: Dict[str, Any] | None = None) -> str:
    """Hard final sanitization pass for player-facing output.

    Applies both full-text and line-level cleanup to prevent internal scaffold,
    planner/router/validator/adjudication leakage from reaching players.
    """
    if not isinstance(text, str):
        return ""

    ctx = context if isinstance(context, dict) else {}
    out = str(text)

    # Full-text pass for splice artifacts and leaked internal labels.
    for pattern, replacement in _FULL_TEXT_REWRITES:
        out = pattern.sub(replacement, out)

    # PASS 1: Pattern and line-level cleanup.
    sanitized_lines: list[str] = []
    for raw_line in out.splitlines():
        line = raw_line.strip()
        if not line:
            if sanitized_lines and sanitized_lines[-1] != "":
                sanitized_lines.append("")
            continue

        rewritten = _rewrite_line(line, ctx).strip()
        if not rewritten:
            continue

        low = rewritten.lower()
        if any(phrase.lower() in low for phrase in DISALLOWED_EXACT_PHRASES):
            continue
        if any(pattern.search(rewritten) for pattern in DISALLOWED_HEURISTIC_PATTERNS):
            # Last-resort rewrite for procedural/internal phrasing that survived.
            rewritten = "The scene offers no clear answer yet."

        sanitized_lines.append(rewritten)

    rebuilt = "\n".join(sanitized_lines).strip()
    rebuilt = re.sub(r"[ \t]{2,}", " ", rebuilt)
    rebuilt = re.sub(r"\n{3,}", "\n\n", rebuilt)

    # PASS 2: Semantic and structural validation at sentence level.
    candidate_sentences = _split_sentences(rebuilt)
    validated: list[str] = []
    for sentence in candidate_sentences:
        original = sentence
        if not sentence:
            continue
        if any(p.search(sentence) for p in _IMPERATIVE_OR_META_PATTERNS) or _is_spliced_or_malformed(sentence):
            sentence = _rewrite_instructional_sentence(sentence).strip()
            if sentence != original:
                _log_sanitizer_event(ctx, "rewritten", original)
        if not sentence:
            _log_sanitizer_event(ctx, "dropped_empty", original)
            continue
        if not _is_diegetic_sentence(sentence):
            _log_sanitizer_event(ctx, "dropped_non_diegetic", original)
            continue
        validated.append(sentence)

    coherent = _cohere_sentences(validated)
    rebuilt = " ".join(coherent).strip()

    if not rebuilt:
        return "For a breath, the scene stays still."
    return rebuilt
