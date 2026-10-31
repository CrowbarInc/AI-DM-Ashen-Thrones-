"""Deterministic player-agency diagnostics (no LLM, advisory only).

Scans *final_output* for narration that presumes the PC's decisions, reflexes, or
involuntary commitments. Intended for tests and optional session debug — never for
altering player-facing text.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

_MAX_SCAN_CHARS = 200_000

_SEVERITY_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
_SCORE_FOR_SEVERITY = {"none": 1.0, "low": 0.75, "medium": 0.5, "high": 0.0}


def _truthy_env(name: str) -> bool:
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


def _mask_double_quoted_regions(text: str) -> str:
    """Replace ASCII double-quoted spans with spaces (same length) for scanning.

    Keeps indices aligned with *text* so matches can be sliced from the original.
    Does not treat escaped quotes; TTRPG snippets rarely need `\"` inside speech.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 1
            if j < n:
                out.append(" " * (j - i + 1))
                i = j + 1
            else:
                out.append(" " * (n - i))
                i = n
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _mask_curly_quoted_regions(text: str) -> str:
    """Also mask “…” style quotes (common in prose)."""
    s = text
    for open_ch, close_ch in ("\u201c", "\u201d"), ("\u2018", "\u2019"):
        parts: list[str] = []
        idx = 0
        while idx < len(s):
            start = s.find(open_ch, idx)
            if start == -1:
                parts.append(s[idx:])
                break
            parts.append(s[idx:start])
            end = s.find(close_ch, start + 1)
            if end == -1:
                parts.append(" " * (len(s) - start))
                break
            span = end - start + 1
            parts.append(" " * span)
            idx = end + 1
        s = "".join(parts)
    return s


def _scan_surface(text: str) -> str:
    """Unquoted narration surface: quotes masked, length preserved."""
    t = text if len(text) <= _MAX_SCAN_CHARS else text[:_MAX_SCAN_CHARS]
    t = _mask_double_quoted_regions(t)
    t = _mask_curly_quoted_regions(t)
    return t


@dataclass(frozen=True)
class _Rule:
    name: str
    severity: str  # "high" | "medium" | "low"
    pattern: re.Pattern[str]


# --- High: explicit player decision / action / involuntary commitment ---------

_HIGH_RULES: tuple[_Rule, ...] = (
    _Rule("forced_decide", "high", re.compile(r"\byou decide to\b", re.I)),
    _Rule("forced_choose", "high", re.compile(r"\byou choose to\b", re.I)),
    _Rule("forced_proceed", "high", re.compile(r"\byou proceed to\b", re.I)),
    # Cognitive-only "can't help but wonder/…" is medium (see _MEDIUM_RULES).
    _Rule(
        "cant_help_but",
        "high",
        re.compile(
            r"\byou can'?t help but(?!\s+(?:wonder|worry|think|notice|realize)\b)",
            re.I,
        ),
    ),
    _Rule(
        "cannot_help_but",
        "high",
        re.compile(
            r"\byou cannot help but(?!\s+(?:wonder|worry|think|notice|realize)\b)",
            re.I,
        ),
    ),
    _Rule("feel_compelled", "high", re.compile(r"\byou feel compelled to\b", re.I)),
    _Rule("automatically", "high", re.compile(r"\byou automatically\b", re.I)),
    _Rule(
        "before_react",
        "high",
        re.compile(r"\bbefore you can react,?\s+you\b", re.I),
    ),
)


_MEDIUM_RULES: tuple[_Rule, ...] = (
    _Rule(
        "cant_help_cognitive",
        "medium",
        re.compile(
            r"\byou can'?t help but\s+(?:wonder|worry|think|notice|realize)\b",
            re.I,
        ),
    ),
    _Rule(
        "cannot_help_cognitive",
        "medium",
        re.compile(
            r"\byou cannot help but\s+(?:wonder|worry|think|notice|realize)\b",
            re.I,
        ),
    ),
    _Rule("find_yourself", "medium", re.compile(r"\byou find yourself\b", re.I)),
    _Rule(
        "instinctive_action",
        "medium",
        re.compile(r"\byou instinctively\s+[a-z]{3,20}\b", re.I),
    ),
    # Forced affect leading to PC action (bounded clause).
    _Rule(
        "feel_and_act",
        "medium",
        re.compile(
            r"\byou feel [^.!?\n]{2,100}?\s+and\s+(?:therefore\s+)?you\s+"
            r"(?:run|flee|retreat|leave|attack|draw|strike|move|go|step|turn|reach|"
            r"grab|take|drop|open|close|speak|say|nod|shake)\b",
            re.I,
        ),
    ),
)


# --- Low: soft presumption (very narrow; prefer false negatives) ---------------

_LOW_RULES: tuple[_Rule, ...] = (
    _Rule("seem_inclined", "low", re.compile(r"\byou seem inclined to\b", re.I)),
)


def _hypothetical_prefix_before(text: str, pos: int, window: int = 80) -> bool:
    """True if the narration right before *pos* reads as conditional / offered possibility."""
    prefix = text[max(0, pos - window) : pos]
    if not prefix:
        return False
    # "If you decide …" — the "you" is inside the match; only a subordinator + whitespace
    # may appear before *pos*.
    # Narrow subordinators only — avoid narrative "… as you …" / "… when you …".
    if re.search(r"\b(?:if|whether|unless)\s+$", prefix, re.I):
        return True
    if re.search(r"\b(?:suppose|imagine|perhaps|maybe)\s+$", prefix, re.I):
        return True
    if re.search(r"\b(?:you|one) (?:might|could|may)\s+$", prefix, re.I):
        return True
    if re.search(
        r"(?:^|[\n\r])\s*(?:note|optional|suggestion)\s*:\s*$",
        prefix,
        re.I,
    ):
        return True
    pl = prefix.lower()
    for s in (
        "feel free to ",
        "you're welcome to ",
        "you are welcome to ",
    ):
        if pl.endswith(s):
            return True
    return False


def _instructional_line(line: str) -> bool:
    """Heuristic: OOC / rules lines (not in quotes — quotes already masked in surface)."""
    s = line.strip().lower()
    if not s:
        return False
    if s.startswith(("dm:", "gm:", "ooc:", "note:", "rules:", "mechanics:")):
        return True
    if s.startswith("```") or s.startswith("#"):
        return True
    return False


def evaluate_player_agency(final_output: str) -> dict[str, Any]:
    """Scan *final_output* for deterministic player-agency risk signals.

    Returns ``violation``, ``severity`` (``none``/``low``/``medium``/``high``),
    ``instances`` (matched substrings), ``notes`` (rule diagnostics), and ``score``
    (1.0 / 0.75 / 0.5 / 0.0 by worst severity).
    """
    notes: list[str] = ["ruleset:player_agency_v1", "anti_fp:mask_double_and_curly_quotes"]
    if not isinstance(final_output, str) or not final_output.strip():
        return {
            "violation": False,
            "severity": "none",
            "instances": [],
            "notes": notes + ["empty_or_non_string_input"],
            "score": 1.0,
        }

    surface = _scan_surface(final_output)
    lines_skipped = 0
    # Line-level: drop obvious non-narration lines from *surface* by blanking them
    # (preserve length by replacing with spaces).
    line_buf: list[str] = []
    line_start = 0
    for i, ch in enumerate(surface):
        if ch == "\n":
            seg = surface[line_start:i]
            if _instructional_line(seg):
                line_buf.append(" " * len(seg))
                lines_skipped += 1
            else:
                line_buf.append(seg)
            line_buf.append("\n")
            line_start = i + 1
    if line_start < len(surface):
        seg = surface[line_start:]
        if _instructional_line(seg):
            line_buf.append(" " * len(seg))
            lines_skipped += 1
        else:
            line_buf.append(seg)
    surface_lines = "".join(line_buf)
    if lines_skipped:
        notes.append(f"anti_fp:skipped_instructional_lines:{lines_skipped}")

    instances: list[str] = []
    matched_rules: list[str] = []
    worst = "none"

    def consider(rule: _Rule, m: re.Match[str]) -> None:
        nonlocal worst
        if _hypothetical_prefix_before(surface_lines, m.start()):
            return
        sev = rule.severity
        if _SEVERITY_RANK[sev] > _SEVERITY_RANK[worst]:
            worst = sev
        matched_rules.append(rule.name)
        raw = final_output[m.start() : m.end()]
        if raw not in instances:
            instances.append(raw)

    for rule in _HIGH_RULES:
        for m in rule.pattern.finditer(surface_lines):
            consider(rule, m)

    for rule in _MEDIUM_RULES:
        for m in rule.pattern.finditer(surface_lines):
            consider(rule, m)

    for rule in _LOW_RULES:
        for m in rule.pattern.finditer(surface_lines):
            consider(rule, m)

    # De-duplicate overlapping notes for skipped hypothetical (can be verbose); cap notes
    if len(notes) > 40:
        notes = notes[:40] + ["notes:truncated"]

    if matched_rules:
        notes.append("matched:" + ",".join(sorted(set(matched_rules))))

    violation = worst != "none"
    score = _SCORE_FOR_SEVERITY[worst]

    return {
        "violation": violation,
        "severity": worst,
        "instances": instances,
        "notes": notes,
        "score": score,
    }


def maybe_attach_player_agency_eval(session: Mapping[str, Any] | None, *, final_output: str) -> None:
    """If ``ASGM_RECORD_PLAYER_AGENCY_EVAL`` is set, attach eval to ``session['last_action_debug']``.

    No-op when disabled or *session* lacks a mutable ``last_action_debug`` dict.
    Does not change player-facing text.
    """
    if not _truthy_env("ASGM_RECORD_PLAYER_AGENCY_EVAL"):
        return
    if not isinstance(session, dict):
        return
    lad = session.get("last_action_debug")
    if not isinstance(lad, dict):
        return
    lad["player_agency_eval"] = evaluate_player_agency(final_output)
