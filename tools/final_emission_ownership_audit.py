#!/usr/bin/env python3
"""Advisory drift scan for Objective C2 final-emission ownership (post-Block B/D1).

This is **not** static analysis or a proof of semantics. It applies a small set of
regex / substring heuristics to catch accidental reintroduction of **boundary-owned**
semantic synthesis (answer/action minting, diegetic sanitizer rewrites in strip-only,
bridge/reconstruct language in the wrong layer).

**False positives:** comments that quote legacy behavior, string literals in tests copied
into ``game/``, and legitimate uses of words like "reconstruct" in unrelated contexts
may appear. Treat every finding as "read the hunk and decide"; prefer FEM contract tests
in ``tests/test_final_emission_boundary_convergence.py`` for behavioral truth.

See ``docs/final_emission_ownership_convergence.md`` and ``tools/validation_layer_audit.py``
(parallel advisory tool for validation-layer drift).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable


ROOT = Path(__file__).resolve().parents[1]

BOUNDARY_FILES: Final[tuple[str, ...]] = (
    "game/final_emission_gate.py",
    "game/final_emission_repairs.py",
    "game/final_emission_validators.py",
    "game/output_sanitizer.py",
)

# Hard regressions: symbols that must not return to orchestration after C2 Block B.
GATE_FORBIDDEN_SUBSTRINGS: Final[tuple[str, ...]] = (
    "_minimal_answer_contract_repair",
    "_minimal_action_outcome_contract_repair",
    "build_minimal_answer_contract_repair_text",
    "build_minimal_action_outcome_contract_repair_text",
)

# Soft signals: worth human review if they appear in final-boundary modules (not auto-fail).
REVIEW_PATTERNS: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (re.compile(r"\bbridge\b.+\b(narrative|intent|missing)\b", re.I), "possible narrative-bridge language"),
    (re.compile(r"\b(reconstruct|re-write|rewrite).+\b(intent|meaning|semantics)\b", re.I), "possible semantic reconstruction phrasing"),
    (re.compile(r"\bcomplete\b.+\b(thought|partial)\b", re.I), "possible 'complete partial output' phrasing"),
    (re.compile(r"second_person.*template|template.*second_person", re.I), "possible second-person template construction comment"),
)


@dataclass(frozen=True)
class Finding:
    severity: str  # "signal" | "review"
    path: str
    detail: str


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace")


def _strip_only_body(source: str) -> str:
    """Slice between strip-only entry and the following public sanitizer (line-stable anchor)."""
    a = source.find("def _sanitize_player_facing_output_strip_only")
    b = source.find("def sanitize_player_facing_output", a)
    if a == -1 or b == -1:
        return ""
    return source[a:b]


def _scan_file(rel: str, source: str) -> list[Finding]:
    out: list[Finding] = []
    if rel.endswith("final_emission_gate.py"):
        for s in GATE_FORBIDDEN_SUBSTRINGS:
            if s in source:
                out.append(Finding("signal", rel, f"forbidden boundary synthesis hook {s!r} reappeared in gate orchestration"))
    if rel.endswith("output_sanitizer.py"):
        body = _strip_only_body(source)
        # Avoid substring false positives on identifiers like ``_sanitizer_must_rewrite_sentence``.
        if body and ("_rewrite_sentence_atomically" in body or " _rewrite_sentence(" in body):
            out.append(
                Finding(
                    "signal",
                    rel,
                    "strip-only sanitizer path appears to invoke sentence rewrite helpers (diegetic rewrite leak)",
                )
            )
        if body and "_diegetic_uncertainty_fallback" in body:
            out.append(Finding("signal", rel, "strip-only path references _diegetic_uncertainty_fallback"))
    for rx, label in REVIEW_PATTERNS:
        if rx.search(source):
            out.append(Finding("review", rel, label))
    return out


def run_audit(files: Iterable[str] | None = None) -> tuple[list[Finding], list[str]]:
    rels = list(files) if files else list(BOUNDARY_FILES)
    findings: list[Finding] = []
    scanned: list[str] = []
    for rel in rels:
        p = ROOT / rel
        if not p.is_file():
            continue
        scanned.append(rel)
        findings.extend(_scan_file(rel, _read(rel)))
    return findings, scanned


def _report(findings: list[Finding], scanned: list[str]) -> str:
    lines = [
        "# Final emission ownership audit (Objective C2)",
        "",
        f"Scanned {len(scanned)} file(s): {', '.join(scanned)}",
        "",
    ]
    sig = [f for f in findings if f.severity == "signal"]
    rev = [f for f in findings if f.severity == "review"]
    lines.append(f"## Signals (likely regression): **{len(sig)}**")
    if not sig:
        lines.append("- (none)")
    else:
        for f in sig:
            lines.append(f"- **{f.path}** - {f.detail}")
    lines.append("")
    lines.append(f"## Review hints (ambiguous): **{len(rev)}**")
    if not rev:
        lines.append("- (none)")
    else:
        for f in rev:
            lines.append(f"- **{f.path}** - {f.detail}")
    lines.append("")
    lines.append("Exit: default **0** (advisory). Use `--strict` for nonzero on signals only.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="C2 final-emission ownership drift audit (advisory).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 if any **signal** finding is present (default: always 0 unless parse error).",
    )
    args = parser.parse_args()
    findings, scanned = run_audit()
    sys.stdout.write(_report(findings, scanned))
    if args.strict and any(f.severity == "signal" for f in findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
