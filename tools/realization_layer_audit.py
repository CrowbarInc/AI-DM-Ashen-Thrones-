#!/usr/bin/env python3
"""Advisory static audit for realization-layer semantic reconstruction risk.

This tool is intentionally heuristic and non-enforcing. It scans likely prompt,
GPT, gate, retry, and fallback files for language that may indicate a layer is
reconstructing semantic truth instead of realizing or validating Planner-backed
obligations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.realization_authority import (  # noqa: E402
    AUTHORITY_PROFILES,
    BOUNDED,
    FALLBACK_FAMILIES,
    LEGACY,
    SAFE,
    SUSPICIOUS,
    UNKNOWN,
)

DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "realization_layer_audit"
DEFAULT_JSON_OUT = DEFAULT_OUTPUT_DIR / "realization_layer_audit.json"
DEFAULT_MD_OUT = DEFAULT_OUTPUT_DIR / "realization_layer_audit.md"

TARGET_FILES: tuple[str, ...] = (
    "game/prompt_context.py",
    "game/gm.py",
    "game/gm_retry.py",
    "game/final_emission_gate.py",
    "game/final_emission_repairs.py",
    "game/social_exchange_emission.py",
    "game/diegetic_fallback_narration.py",
    "game/upstream_response_repairs.py",
    "game/narrative_authenticity.py",
    "game/fallback_behavior.py",
    "game/api.py",
    "game/opening_scene_realization.py",
)

SEVERITIES: tuple[str, ...] = ("INFO", "REVIEW", "HIGH")

TERM_CATEGORIES: dict[str, tuple[str, ...]] = {
    "semantic_reconstruction": (
        "infer",
        "derive",
        "decide",
        "resolve",
        "reconstruct",
        "synthesize",
        "invent",
        "repair",
    ),
    "fallback_authorship": (
        "fallback",
        "emergency",
        "generic",
        "stock",
        "terminal",
        "prepared_emission",
    ),
    "raw_state_semantic_risk": (
        "world",
        "session",
        "scene",
        "resolution",
        "visible_fact",
        "hidden",
        "clue",
        "motive",
        "consequence",
        "transition",
    ),
    "prompt_gpt_realization_risk": (
        "prompt",
        "messages",
        "call_gpt",
        "retry",
        "model output",
        "gm_output",
    ),
}

PLAYER_FACING_PROSE_TERMS: tuple[str, ...] = (
    "player_facing",
    "player-facing",
    "narration",
    "prose",
    "emission",
    "final_emission",
    "text",
    "output",
    "message",
    "messages",
    "gm_output",
    "model output",
    "call_gpt",
    "retry fallback",
)

HIGH_RISK_TERMS: tuple[str, ...] = (
    "fallback",
    "emergency",
    "repair",
    "invent",
    "reconstruct",
    "synthesize",
)

RAW_STATE_TERMS: tuple[str, ...] = TERM_CATEGORIES["raw_state_semantic_risk"]
PROMPT_GATE_FILES: tuple[str, ...] = (
    "prompt_context.py",
    "gm.py",
    "gm_retry.py",
    "final_emission_gate.py",
    "final_emission_repairs.py",
)

TERM_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    category: [
        (term, re.compile(re.escape(term), re.IGNORECASE))
        for term in terms
    ]
    for category, terms in TERM_CATEGORIES.items()
}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    severity: str
    matched_term: str
    category: str
    message: str
    text_excerpt: str


def _rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_info_context(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith(('"""', "'''", "*", "-")):
        return True
    if re.match(r"^[A-Z][A-Z0-9_]+\s*[:=]", stripped):
        return True
    return False


def _triple_quote_count(line: str) -> int:
    return line.count('"""') + line.count("'''")


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _context_text(lines: list[str], index: int, radius: int = 2) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return "\n".join(lines[start:end]).lower()


def _severity_for(
    *,
    rel_file: str,
    category: str,
    term: str,
    line: str,
    context: str,
    force_info_context: bool = False,
) -> str:
    if force_info_context or _is_info_context(line):
        return "INFO"

    term_l = term.lower()
    high_term = term_l in HIGH_RISK_TERMS
    near_player_facing = _contains_any(context, PLAYER_FACING_PROSE_TERMS)
    near_raw_state = _contains_any(context, RAW_STATE_TERMS)
    near_retry_or_gate = any(
        needle in context
        for needle in ("retry", "final_emission", "gm_output", "model output", "call_gpt")
    )
    if high_term and (near_player_facing or near_raw_state or near_retry_or_gate):
        return "HIGH"

    if (
        category == "semantic_reconstruction"
        and rel_file.endswith(PROMPT_GATE_FILES)
    ):
        return "REVIEW"

    if category == "fallback_authorship" and (near_player_facing or near_raw_state):
        return "REVIEW"

    return "INFO"


def _message_for(severity: str, category: str, term: str) -> str:
    if severity == "HIGH":
        return (
            f"High-risk {category} term {term!r} appears near player-facing prose, "
            "final emission, GPT output, retry fallback, or raw-state language."
        )
    if severity == "REVIEW":
        return (
            f"Review {category} term {term!r}; this may be benign, but it sits in a "
            "realization-layer file where semantic ownership matters."
        )
    return f"Informational {category} reference for {term!r}."


def scan_text(text: str, *, file: str) -> list[Finding]:
    """Scan source text and return structured advisory findings."""
    findings: list[Finding] = []
    lines = text.splitlines()
    in_triple_quoted_block = False
    for index, line in enumerate(lines):
        starts_in_triple_quoted_block = in_triple_quoted_block
        context = _context_text(lines, index)
        for category, patterns in TERM_PATTERNS.items():
            for term, pattern in patterns:
                if not pattern.search(line):
                    continue
                severity = _severity_for(
                    rel_file=file,
                    category=category,
                    term=term,
                    line=line,
                    context=context,
                    force_info_context=starts_in_triple_quoted_block,
                )
                findings.append(
                    Finding(
                        file=file,
                        line=index + 1,
                        severity=severity,
                        matched_term=term,
                        category=category,
                        message=_message_for(severity, category, term),
                        text_excerpt=line.strip()[:240],
                    )
                )
        if _triple_quote_count(line) % 2 == 1:
            in_triple_quoted_block = not in_triple_quoted_block
    return findings


def scan_paths(paths: Iterable[Path], *, root: Path) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    scanned: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = _rel_path(path, root)
        scanned.append(rel)
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text(text, file=rel))
    return findings, scanned


def scan_repo(*, root: Path = ROOT, target_files: Iterable[str] = TARGET_FILES) -> tuple[list[Finding], list[str]]:
    paths = [root / rel for rel in target_files]
    return scan_paths(paths, root=root)


def _summary(findings: list[Finding]) -> dict[str, object]:
    by_severity = Counter(f.severity for f in findings)
    by_category = Counter(f.category for f in findings)
    return {
        "total_findings": len(findings),
        "by_severity": {severity: by_severity.get(severity, 0) for severity in SEVERITIES},
        "by_category": dict(sorted(by_category.items())),
    }


def _ledger_summary() -> dict[str, object]:
    classifications = Counter(f.classification for f in FALLBACK_FAMILIES.values())
    return {
        "authority_profiles": sorted(AUTHORITY_PROFILES),
        "fallback_families": sorted(FALLBACK_FAMILIES),
        "fallback_classifications": {
            classification: classifications.get(classification, 0)
            for classification in (SAFE, BOUNDED, SUSPICIOUS, LEGACY, UNKNOWN)
        },
    }


def build_report_payload(findings: list[Finding], scanned_files: list[str], *, root: Path) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "advisory_only": True,
        "ci_enforced": False,
        "ledger": _ledger_summary(),
        "summary": _summary(findings),
        "scanned_files": scanned_files,
        "findings": [asdict(f) for f in findings],
    }


def render_markdown_report(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    by_severity = summary.get("by_severity", {})
    by_category = summary.get("by_category", {})
    findings = payload.get("findings", [])
    scanned = payload.get("scanned_files", [])
    high_findings = [
        f for f in findings if isinstance(f, dict) and f.get("severity") == "HIGH"
    ][:20]

    lines = [
        "# Realization Layer Audit",
        "",
        "Advisory only: this report is not CI-enforced and findings are not failures yet.",
        "Interpret classifications alongside `game.realization_authority`.",
        "",
        "## Summary by Severity",
    ]
    if isinstance(by_severity, dict):
        for severity in SEVERITIES:
            lines.append(f"- {severity}: {by_severity.get(severity, 0)}")
    lines.extend(["", "## Summary by Category"])
    if isinstance(by_category, dict) and by_category:
        for category, count in sorted(by_category.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Top HIGH Findings"])
    if high_findings:
        for f in high_findings:
            lines.append(
                f"- `{f['file']}:{f['line']}` {f['category']} / {f['matched_term']}: "
                f"{f['text_excerpt']}"
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Scanned Files"])
    if isinstance(scanned, list) and scanned:
        for rel in scanned:
            lines.append(f"- `{rel}`")
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Notes",
            "- The scanner is heuristic and intentionally advisory.",
            "- HIGH means read the hunk first; it does not prove a runtime behavior bug.",
            "- REVIEW means semantic ownership language appears in a sensitive layer.",
            "- INFO usually covers comments, docs, constants, or benign references.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_reports(
    findings: list[Finding],
    scanned_files: list[str],
    *,
    root: Path = ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_out = output_dir / "realization_layer_audit.json"
    md_out = output_dir / "realization_layer_audit.md"
    payload = build_report_payload(findings, scanned_files, root=root)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown_report(payload), encoding="utf-8")
    return {"json": json_out, "markdown": md_out}


def run_audit(
    *,
    root: Path = ROOT,
    target_files: Iterable[str] = TARGET_FILES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, object]:
    findings, scanned = scan_repo(root=root, target_files=target_files)
    outputs = write_reports(findings, scanned, root=root, output_dir=output_dir)
    return {
        "findings": findings,
        "scanned_files": scanned,
        "outputs": outputs,
        "summary": _summary(findings),
    }


def _console_summary(result: dict[str, object]) -> str:
    summary = result.get("summary", {})
    outputs = result.get("outputs", {})
    scanned = result.get("scanned_files", [])
    by_severity = summary.get("by_severity", {}) if isinstance(summary, dict) else {}
    lines = [
        "Realization layer audit (advisory only)",
        f"Scanned files: {len(scanned) if isinstance(scanned, list) else 0}",
    ]
    if isinstance(by_severity, dict):
        lines.append(
            "Findings: "
            + ", ".join(f"{severity}={by_severity.get(severity, 0)}" for severity in SEVERITIES)
        )
    if isinstance(outputs, dict):
        lines.append(f"JSON: {outputs.get('json')}")
        lines.append(f"Markdown: {outputs.get('markdown')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Advisory realization-layer semantic reconstruction audit."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for realization_layer_audit.json and realization_layer_audit.md.",
    )
    args = parser.parse_args(argv)
    result = run_audit(output_dir=args.output_dir)
    sys.stdout.write(_console_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
