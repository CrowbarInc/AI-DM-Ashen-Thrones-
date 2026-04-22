#!/usr/bin/env python3
"""Heuristic audit for Objective #11 validation-layer ownership drift.

Uses ``game/validation_layer_contracts.py`` as the executable registry and
``docs/validation_layer_separation.md`` as the prose contract pointer.

This is a maintainer aid: low-noise pattern matching, not a proof of semantics.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final


ROOT = Path(__file__).resolve().parents[1]

# Import contract module from repo root (tooling entrypoint).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game import validation_layer_contracts as vlc  # noqa: E402


BLOCK_B_RESIDUE_PATH: Final[Path] = ROOT / "docs" / "validation_layer_separation_block_b_residue.md"
CANONICAL_CONTRACT_DOC: Final[Path] = ROOT / "docs" / "validation_layer_separation.md"
REGISTRY_MODULE: Final[str] = "game.validation_layer_contracts"


@dataclass(frozen=True)
class Finding:
    category: str
    severity: str  # "likely_drift" | "review" | "info"
    path: str
    detail: str


def _game_submodules_imported(source: str) -> set[str]:
    """First segment under ``game.*`` for each imported submodule (e.g. ``final_emission_gate``)."""
    out: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("game."):
            rest = node.module[len("game.") :].split(".", 1)[0]
            if rest:
                out.add(rest)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("game."):
                    seg = name[len("game.") :].split(".", 1)[0]
                    if seg:
                        out.add(seg)
    return out


def _classify_bucket(rel_posix: str) -> str | None:
    """Rough module bucket for heuristics (not a full runtime classifier)."""
    lower = rel_posix.lower()
    name = Path(rel_posix).name
    if name == "narrative_authenticity_eval.py":
        return "evaluator"
    if name in ("final_emission_gate.py", "final_emission_repairs.py", "final_emission_validators.py", "final_emission_meta.py"):
        return "gate"
    if name == "narrative_authenticity.py":
        return "na"
    if name in ("prompt_context.py", "response_policy_contracts.py", "prompt_context_leads.py"):
        return "planner"
    return "other"


def _parse_block_b_themes(text: str) -> list[str]:
    """Extract bullet themes from Block B residue (structure-based, not line-fixed)."""
    themes: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("- **"):
            inner = line[2:].strip()
            inner = re.sub(r"^\*\*([^*]+)\*\*:\s*", r"\1: ", inner)
            themes.append(inner)
    return themes


def _gate_split_modules_present(game_files: list[Path]) -> list[str]:
    names = {p.name for p in game_files}
    expected = ("final_emission_gate.py", "final_emission_repairs.py", "final_emission_validators.py")
    return [n for n in expected if n in names]


def _scan_evaluator_imports(rel: str, bucket: str | None, subs: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    if bucket != "evaluator":
        return findings
    allowed = {"final_emission_meta", "validation_layer_contracts", "telemetry_vocab"}
    bad = sorted(subs - allowed)
    for mod in bad:
        sev = "likely_drift"
        detail = f"Evaluator-class module imports ``game.{mod}`` (allowed game imports: {sorted(allowed)})."
        findings.append(Finding("evaluator_drift", sev, rel, detail))
    return findings


def _scan_gate_evaluator_import(rel: str, bucket: str | None, subs: set[str]) -> list[Finding]:
    if bucket != "gate":
        return []
    if "narrative_authenticity_eval" in subs:
        return [
            Finding(
                "gate_scoring_drift",
                "likely_drift",
                rel,
                "Gate-class module imports offline ``narrative_authenticity_eval``; evaluator must stay read-only and off live paths.",
            )
        ]
    return []


def _scan_na_imports(rel: str, bucket: str | None, subs: set[str]) -> list[Finding]:
    if bucket != "na":
        return []
    findings: list[Finding] = []
    forbidden = {"final_emission_gate", "final_emission_repairs", "narrative_authenticity_eval"}
    for mod in sorted(subs & forbidden):
        findings.append(
            Finding(
                "na_response_delta_drift",
                "likely_drift",
                rel,
                f"NA imports ``game.{mod}``; delta repair / gate orchestration should stay gate-owned (see contract + Block B residue).",
            )
        )
    return findings


def _scan_planner_imports(rel: str, bucket: str | None, subs: set[str]) -> list[Finding]:
    if bucket != "planner":
        return []
    findings: list[Finding] = []
    forbidden = {"final_emission_gate", "final_emission_repairs", "narrative_authenticity_eval"}
    for mod in sorted(subs & forbidden):
        findings.append(
            Finding(
                "planner_truth_drift",
                "likely_drift",
                rel,
                f"Planner-class module imports ``game.{mod}``; structure builders must not pull live gate/repair/evaluator surfaces.",
            )
        )
    return findings


_RE_EVAL_WRITE = re.compile(
    r"(?is)\b(?:write[- ]?back|mutate\s+(?:live|pipeline)|retry\s+repair|repair\s+retry)\b"
)
_RE_GATE_QUALITY = re.compile(
    r"(?is)\b(?:quality\s+rank|rank\s+candidates|grade\s+(?:the\s+)?output|subjective\s+quality\s+enforcement)\b"
)
_RE_PLANNER_OWNERSHIP = re.compile(
    r"(?is)\b(?:primary\s+ownership|canonical\s+repair\s+owner)\b.*\bresponse_delta\b"
)
_RE_NA_SHADOW = re.compile(r"NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON|follow_up_missing_signal_shadow_response_delta")
_RE_NA_RD_LEGAL = re.compile(r"['\"]response_delta_[a-z0-9_]+['\"]\s*(?:\]|=)")


def _text_heuristics(rel: str, bucket: str | None, source: str) -> list[Finding]:
    findings: list[Finding] = []
    if bucket == "evaluator" and _RE_EVAL_WRITE.search(source):
        findings.append(
            Finding(
                "evaluator_drift",
                "review",
                rel,
                "Evaluator-class text mentions write-back / live repair / retry-repair language - verify offline/read-only posture.",
            )
        )
    if bucket == "gate" and _RE_GATE_QUALITY.search(source):
        findings.append(
            Finding(
                "gate_scoring_drift",
                "review",
                rel,
                "Possible score/rank/grade phrasing - confirm it is not live legality enforcement (gate seals codes; scoring is evaluator).",
            )
        )
    if bucket == "planner" and _RE_PLANNER_OWNERSHIP.search(source):
        findings.append(
            Finding(
                "planner_truth_drift",
                "review",
                rel,
                "Strong ownership phrasing near ``response_delta`` - confirm this remains structure-only vs gate legality.",
            )
        )
    if bucket == "na":
        if "validate_response_delta" in source and not _RE_NA_SHADOW.search(source):
            findings.append(
                Finding(
                    "na_response_delta_drift",
                    "review",
                    rel,
                    "Uses ``validate_response_delta`` without the stable NA shadow reason token import/name - verify shadow path still aligns with ``NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON``.",
                )
            )
        for m in _RE_NA_RD_LEGAL.finditer(source):
            span = source[max(0, m.start() - 80) : m.end() + 40]
            if "shadow" in span.lower() or "diagnostic" in span.lower():
                continue
            findings.append(
                Finding(
                    "na_response_delta_drift",
                    "review",
                    rel,
                    "Possible ``response_delta_*``-shaped key assignment - confirm it stays diagnostic/shadow, not canonical legality metadata.",
                )
            )
    return findings


def _duplicate_ownership_phrase(source: str, rel: str) -> list[Finding]:
    """Soft signal: multiple modules claiming exclusive canonical repair for delta (text only)."""
    findings: list[Finding] = []
    if re.search(r"(?is)exclusive(?:ly)?\s+own.*response_delta", source) and re.search(
        r"(?is)\brepair\b", source
    ):
        findings.append(
            Finding(
                "duplicate_ownership_wording",
                "review",
                rel,
                "Exclusive ``response_delta`` / repair ownership language - confirm against contract (gate-owned legality; NA non-owning).",
            )
        )
    return findings


def collect_py_files(scan_roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in scan_roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    return files


def run_audit(
    *,
    scan_roots: list[Path],
    repo_root: Path,
) -> tuple[list[Finding], list[str], list[str]]:
    split_note = _gate_split_modules_present(collect_py_files(scan_roots))
    residue_text = ""
    if BLOCK_B_RESIDUE_PATH.is_file():
        residue_text = BLOCK_B_RESIDUE_PATH.read_text(encoding="utf-8")
    residue_themes = _parse_block_b_themes(residue_text)

    findings: list[Finding] = []
    scanned: list[str] = []

    for path in collect_py_files(scan_roots):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        scanned.append(rel)
        bucket = _classify_bucket(rel)
        subs = _game_submodules_imported(source)

        findings.extend(_scan_evaluator_imports(rel, bucket, subs))
        findings.extend(_scan_gate_evaluator_import(rel, bucket, subs))
        findings.extend(_scan_na_imports(rel, bucket, subs))
        findings.extend(_scan_planner_imports(rel, bucket, subs))
        findings.extend(_text_heuristics(rel, bucket, source))
        findings.extend(_duplicate_ownership_phrase(source, rel))

    benign: list[str] = []
    if len(split_note) == 3:
        benign.append(
            "Gate layer split across "
            + ", ".join(split_note)
            + " - single canonical **gate** legality layer (Block B residue: multiple files, one layer)."
        )
    benign.append(
        f"Stable NA shadow token: ``{vlc.NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON}`` (registry: ``{REGISTRY_MODULE}``)."
    )
    if residue_themes:
        benign.append("Block B residue themes loaded for tolerated-pattern context (see report section).")

    return findings, scanned, benign


def _format_report(
    findings: list[Finding],
    scanned: list[str],
    benign_lines: list[str],
    residue_themes: list[str],
) -> str:
    lines: list[str] = []
    lines.append("Validation layer ownership audit (heuristic)")
    lines.append("")
    lines.append("## Canonical contract source")
    lines.append(f"- Prose: ``{CANONICAL_CONTRACT_DOC.relative_to(ROOT).as_posix()}``")
    lines.append(f"- Executable registry: ``{REGISTRY_MODULE}``")
    lines.append(f"- Block B residue guide: ``{BLOCK_B_RESIDUE_PATH.relative_to(ROOT).as_posix()}``")
    lines.append("")
    lines.append("## Files/modules scanned")
    lines.append(f"- Count: {len(scanned)} Python files under scan root(s).")
    if len(scanned) <= 24:
        for s in scanned:
            lines.append(f"  - ``{s}``")
    else:
        lines.append("  (List omitted; use JSON mode for full list.)")
    lines.append("")

    likely = [f for f in findings if f.severity == "likely_drift"]
    review = [f for f in findings if f.severity == "review"]
    info = [f for f in findings if f.severity == "info"]

    lines.append("## Likely ownership drift")
    if not likely:
        lines.append("- (none)")
    else:
        for f in likely:
            lines.append(f"- **{f.category}** - ``{f.path}``: {f.detail}")
    lines.append("")

    lines.append("## Wording ambiguity / review-needed items")
    if not review:
        lines.append("- (none)")
    else:
        for f in review:
            lines.append(f"- **{f.category}** - ``{f.path}``: {f.detail}")
    lines.append("")

    lines.append("## Benign within-layer splits")
    for b in benign_lines:
        lines.append(f"- {b}")
    lines.append("")

    lines.append("## Residue-aligned tolerated patterns (Block B)")
    if not residue_themes:
        lines.append("- (Block B residue file missing or empty - add ``docs/validation_layer_separation_block_b_residue.md``.)")
    else:
        for t in residue_themes:
            lines.append(f"- {t}")
    lines.append("")

    lines.append("## Info / notes")
    if not info:
        lines.append("- (none)")
    else:
        for f in info:
            lines.append(f"- **{f.category}** - ``{f.path}``: {f.detail}")
    lines.append("")

    lines.append("## Exit summary")
    lines.append(
        f"- Likely drift findings: **{len(likely)}**; review items: **{len(review)}**; info: **{len(info)}**."
    )
    lines.append(
        "- Interpretation: **likely_drift** means an import or strong phrase tripped a seam guard; confirm in review."
        " **review** is ambiguous wording worth reading; it is not an automatic regression."
        " Multiple modules under one canonical layer are normal (see Block B + benign splits)."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validation layer ownership drift audit (Objective #11).")
    parser.add_argument(
        "--scan-root",
        action="append",
        dest="scan_roots",
        type=Path,
        help="Directory to scan (repeatable). Default: ./game",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON to stdout instead of the text report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 if any likely_drift finding is present (default: 0 unless tool error).",
    )
    args = parser.parse_args()
    roots = [Path(p).resolve() for p in (args.scan_roots or [])]
    if not roots:
        roots = [ROOT / "game"]

    findings, scanned, benign = run_audit(scan_roots=roots, repo_root=ROOT)
    residue_themes = _parse_block_b_themes(BLOCK_B_RESIDUE_PATH.read_text(encoding="utf-8")) if BLOCK_B_RESIDUE_PATH.is_file() else []

    likely_n = sum(1 for f in findings if f.severity == "likely_drift")

    def _rel_or_abs(p: Path) -> str:
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()

    if args.json:
        payload: dict[str, Any] = {
            "canonical_contract_doc": CANONICAL_CONTRACT_DOC.relative_to(ROOT).as_posix(),
            "executable_registry": REGISTRY_MODULE,
            "block_b_residue_doc": BLOCK_B_RESIDUE_PATH.relative_to(ROOT).as_posix(),
            "scan_roots": [_rel_or_abs(r) for r in roots],
            "files_scanned": scanned,
            "findings": [asdict(f) for f in findings],
            "benign_within_layer": benign,
            "block_b_residue_themes": residue_themes,
            "summary": {
                "likely_drift": likely_n,
                "review": sum(1 for f in findings if f.severity == "review"),
                "info": sum(1 for f in findings if f.severity == "info"),
            },
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_report(findings, scanned, benign, residue_themes))

    if args.strict and likely_n > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
