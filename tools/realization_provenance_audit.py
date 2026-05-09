#!/usr/bin/env python3
"""Advisory audit for realization fallback provenance coverage.

This scanner is intentionally heuristic and non-enforcing. It looks for likely
player-facing fallback, emergency, terminal, and repair prose paths that may need
``realization_fallback_family`` metadata.
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

DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "realization_provenance_audit"

TARGET_FILES: tuple[str, ...] = (
    "game/api.py",
    "game/gm.py",
    "game/gm_retry.py",
    "game/final_emission_gate.py",
    "game/final_emission_repairs.py",
    "game/social_exchange_emission.py",
    "game/upstream_response_repairs.py",
    "game/diegetic_fallback_narration.py",
)

SEVERITIES: tuple[str, ...] = ("INFO", "REVIEW", "HIGH")

INDICATOR_TERMS: tuple[str, ...] = (
    "fallback",
    "emergency",
    "terminal",
    "repair",
    "player_facing_text",
    "final_emitted_source",
    "upstream_prepared_emission",
    "prepared_answer_fallback_text",
    "prepared_action_fallback_text",
    "gm_output",
    "text replacement",
    "forced retry",
)

PROVENANCE_TERMS: tuple[str, ...] = (
    "realization_fallback_family",
    "REALIZATION_FALLBACK_FAMILY_FIELD",
    "attach_realization_fallback_family",
)

PLAYER_FACING_SIGNALS: tuple[str, ...] = (
    "player_facing_text",
    "final_emitted_source",
    "prepared_answer_fallback_text",
    "prepared_action_fallback_text",
    "upstream_prepared_emission",
    "gm_output",
    "narration",
    "prose",
    "emission",
    "text",
    "output",
)

HIGH_RISK_TERMS: tuple[str, ...] = (
    "fallback",
    "emergency",
    "terminal",
    "prepared_answer_fallback_text",
    "prepared_action_fallback_text",
)

REVIEW_TERMS: tuple[str, ...] = (
    "repair",
    "final_emitted_source",
    "upstream_prepared_emission",
    "gm_output",
    "text replacement",
    "forced retry",
)

INDICATOR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (term, re.compile(re.escape(term), re.IGNORECASE)) for term in INDICATOR_TERMS
)


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    severity: str
    matched_term: str
    message: str
    text_excerpt: str


def _rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _context_text(lines: list[str], index: int, radius: int = 6) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return "\n".join(lines[start:end])


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _is_info_context(line: str, *, in_triple_quoted_block: bool) -> bool:
    stripped = line.strip()
    if in_triple_quoted_block:
        return True
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith(('"""', "'''", "*", "-")):
        return True
    return False


def _triple_quote_count(line: str) -> int:
    return line.count('"""') + line.count("'''")


def _is_labeled(context: str) -> bool:
    return _contains_any(context, PROVENANCE_TERMS)


def _severity_for(
    *,
    term: str,
    line: str,
    context: str,
    in_triple_quoted_block: bool,
) -> str:
    if _is_labeled(context):
        return "INFO"
    if _is_info_context(line, in_triple_quoted_block=in_triple_quoted_block):
        return "INFO"

    term_l = term.lower()
    near_player_facing = _contains_any(context, PLAYER_FACING_SIGNALS)
    if term_l in HIGH_RISK_TERMS and near_player_facing:
        return "HIGH"
    if term_l in REVIEW_TERMS or near_player_facing:
        return "REVIEW"
    return "INFO"


def _message_for(severity: str, term: str, *, labeled: bool) -> str:
    if labeled:
        return (
            f"Indicator {term!r} appears near realization_fallback_family provenance metadata."
        )
    if severity == "HIGH":
        return (
            f"Likely player-facing fallback/emergency prose indicator {term!r} lacks "
            "nearby realization_fallback_family provenance metadata."
        )
    if severity == "REVIEW":
        return (
            f"Fallback or repair pathway indicator {term!r} has ambiguous player-facing "
            "status and lacks nearby realization_fallback_family provenance metadata."
        )
    return f"Informational fallback provenance coverage reference for {term!r}."


def scan_text(text: str, *, file: str) -> list[Finding]:
    """Scan source text and return advisory provenance coverage findings."""
    findings: list[Finding] = []
    lines = text.splitlines()
    in_triple_quoted_block = False
    for index, line in enumerate(lines):
        starts_in_triple_quoted_block = in_triple_quoted_block
        context = _context_text(lines, index)
        labeled = _is_labeled(context)
        for term, pattern in INDICATOR_PATTERNS:
            if not pattern.search(line):
                continue
            severity = _severity_for(
                term=term,
                line=line,
                context=context,
                in_triple_quoted_block=starts_in_triple_quoted_block,
            )
            findings.append(
                Finding(
                    file=file,
                    line=index + 1,
                    severity=severity,
                    matched_term=term,
                    message=_message_for(severity, term, labeled=labeled),
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


def scan_repo(
    *,
    root: Path = ROOT,
    target_files: Iterable[str] = TARGET_FILES,
) -> tuple[list[Finding], list[str]]:
    return scan_paths((root / rel for rel in target_files), root=root)


def _summary(findings: list[Finding]) -> dict[str, object]:
    by_severity = Counter(f.severity for f in findings)
    by_term = Counter(f.matched_term for f in findings)
    return {
        "total_findings": len(findings),
        "by_severity": {severity: by_severity.get(severity, 0) for severity in SEVERITIES},
        "by_matched_term": dict(sorted(by_term.items())),
    }


def build_report_payload(findings: list[Finding], scanned_files: list[str], *, root: Path) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "advisory_only": True,
        "ci_enforced": False,
        "target_files": list(TARGET_FILES),
        "provenance_terms": list(PROVENANCE_TERMS),
        "summary": _summary(findings),
        "scanned_files": scanned_files,
        "findings": [asdict(f) for f in findings],
    }


def render_markdown_report(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    by_severity = summary.get("by_severity", {})
    by_term = summary.get("by_matched_term", {})
    findings = payload.get("findings", [])
    scanned = payload.get("scanned_files", [])
    high_findings = [
        f for f in findings if isinstance(f, dict) and f.get("severity") == "HIGH"
    ][:30]
    review_findings = [
        f for f in findings if isinstance(f, dict) and f.get("severity") == "REVIEW"
    ][:30]

    lines = [
        "# Realization Provenance Coverage Audit",
        "",
        "Advisory only: this report is not CI-enforced and findings are not failures.",
        "",
        "## Summary by Severity",
    ]
    if isinstance(by_severity, dict):
        for severity in SEVERITIES:
            lines.append(f"- {severity}: {by_severity.get(severity, 0)}")

    lines.extend(["", "## Summary by Matched Term"])
    if isinstance(by_term, dict) and by_term:
        for term, count in sorted(by_term.items()):
            lines.append(f"- `{term}`: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## HIGH Findings"])
    if high_findings:
        for f in high_findings:
            lines.append(
                f"- `{f['file']}:{f['line']}` {f['matched_term']}: {f['text_excerpt']}"
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## REVIEW Findings"])
    if review_findings:
        for f in review_findings:
            lines.append(
                f"- `{f['file']}:{f['line']}` {f['matched_term']}: {f['text_excerpt']}"
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
            "- HIGH means likely player-facing fallback/emergency prose lacks nearby provenance metadata.",
            "- REVIEW means fallback or repair status is ambiguous and should be inspected.",
            "- INFO means the context is already labeled or appears to be comment/doc-only.",
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
    json_out = output_dir / "realization_provenance_audit.json"
    md_out = output_dir / "realization_provenance_audit.md"
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
        "Realization provenance coverage audit (advisory only)",
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
        description="Advisory realization fallback provenance coverage audit."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for realization_provenance_audit.json and realization_provenance_audit.md.",
    )
    args = parser.parse_args(argv)
    result = run_audit(output_dir=args.output_dir)
    sys.stdout.write(_console_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
