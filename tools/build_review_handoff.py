#!/usr/bin/env python3
"""Build a centralized Markdown review surface and portable provenance-preserving ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "review_handoff.v1"
TOOL_VERSION = "1"
DEFAULT_HANDOFF = ROOT / "handoff"
DEFAULT_MAX_FILE_BYTES = 5 * 1024 * 1024
DEFAULT_WARN_BUNDLE_BYTES = 20 * 1024 * 1024

REQUIRED_SUMMARY_SECTIONS = (
    "# Campaign",
    "# Executive Summary",
    "# Changes Made",
    "# What Was Tested",
    "# Behavioral Evidence",
    "# Decisions Requiring Human Review",
    "# Known Problems / Unresolved Findings",
    "# Missing Concepts / Future Capabilities",
    "# What This Campaign Does NOT Prove",
    "# Recommended Next Step",
    "# Review Bundle Contents",
)

_SENSITIVE_PART_PATTERNS = (
    re.compile(r"^\.env(?:\..*)?$", re.I),
    re.compile(r"credential", re.I),
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"auth(?:entication)?[_-]?cache", re.I),
    re.compile(r"private[_-]?key", re.I),
    re.compile(r"(?:^|[_-])tokens?(?:[_-]|$)", re.I),
    re.compile(r"(?:^|[_-])secrets?(?:[_-]|$)", re.I),
)
_SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
_EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_resolve(source: str | Path, *, root: Path) -> Path:
    path = Path(source)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"source outside repository root: {source}") from exc
    return resolved


def sensitive_path_reason(path: Path) -> str | None:
    for part in path.parts:
        if part.lower() in _EXCLUDED_PARTS:
            return f"excluded path component: {part}"
        if any(pattern.search(part) for pattern in _SENSITIVE_PART_PATTERNS):
            return f"sensitive filename pattern: {part}"
    if path.suffix.lower() in _SENSITIVE_SUFFIXES:
        return f"sensitive key/certificate suffix: {path.suffix}"
    return None


def _source_row(
    path: Path,
    *,
    root: Path,
    role: str,
    why: str,
    behavioral_evidence: bool,
    human_review_required: bool,
) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "role": role,
        "why": why,
        "behavioral_evidence": behavioral_evidence,
        "human_review_required": human_review_required,
    }


def collect_sources(config: Mapping[str, Any], *, root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requested: list[dict[str, Any]] = []
    primary = _safe_resolve(str(config["primary_report"]), root=root)
    requested.append(
        _source_row(
            primary,
            root=root,
            role="primary_campaign_report",
            why="Primary campaign standard/report used to orient the review.",
            behavioral_evidence=False,
            human_review_required=True,
        )
    )
    for packet_value in config.get("evidence_packets") or []:
        packet_dir = _safe_resolve(str(packet_value), root=root)
        for filename, role in (
            ("evidence_summary.md", "behavioral_evidence_summary"),
            ("evidence_manifest.json", "behavioral_evidence_manifest"),
        ):
            requested.append(
                _source_row(
                    packet_dir / filename,
                    root=root,
                    role=role,
                    why="Standardized behavioral evidence packet consumed by the handoff.",
                    behavioral_evidence=True,
                    human_review_required=True,
                )
            )
    for row in config.get("supporting_files") or []:
        path = _safe_resolve(str(row["path"]), root=root)
        requested.append(
            _source_row(
                path,
                root=root,
                role=str(row.get("role") or "supporting_evidence"),
                why=str(row.get("why") or "Explicit campaign support file."),
                behavioral_evidence=bool(row.get("behavioral_evidence")),
                human_review_required=bool(row.get("human_review_required")),
            )
        )

    included: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    seen_hashes: dict[str, str] = {}
    max_file_bytes = int(config.get("max_file_bytes") or DEFAULT_MAX_FILE_BYTES)
    for row in requested:
        relative = str(row["path"])
        path = _safe_resolve(relative, root=root)
        reason = sensitive_path_reason(Path(relative))
        if reason:
            omitted.append({**row, "reason": reason})
            continue
        if "handoff" in {part.lower() for part in Path(relative).parts} or path.suffix.lower() == ".zip":
            omitted.append({**row, "reason": "recursive handoff/ZIP inclusion prohibited"})
            continue
        if not path.is_file():
            omitted.append({**row, "reason": "source file missing"})
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            omitted.append(
                {
                    **row,
                    "reason": f"source exceeds max_file_bytes ({size} > {max_file_bytes}); canonical reference retained",
                    "size_bytes": size,
                }
            )
            continue
        data = path.read_bytes()
        digest = _sha256_bytes(data)
        if digest in seen_hashes:
            omitted.append(
                {
                    **row,
                    "reason": f"duplicate content of {seen_hashes[digest]}; canonical reference retained",
                    "size_bytes": size,
                    "sha256": digest,
                }
            )
            continue
        seen_hashes[digest] = relative
        included.append(
            {
                **row,
                "canonical_source_path": relative,
                "bundle_path": f"support/{relative}",
                "canonical": True,
                "generated": False,
                "size_bytes": size,
                "sha256": digest,
            }
        )
    return included, omitted


def _load_behavioral(config: Mapping[str, Any], *, root: Path) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for value in config.get("evidence_packets") or []:
        path = _safe_resolve(str(value), root=root) / "evidence_manifest.json"
        if path.is_file():
            packets.append(json.loads(path.read_text(encoding="utf-8")))
    return packets


def _selected_example(packet: Mapping[str, Any], category: str) -> Mapping[str, Any] | None:
    selection = (packet.get("selected_evidence") or {}).get(category) or {}
    example_id = selection.get("example_id")
    return next((row for row in packet.get("examples") or [] if row.get("example_id") == example_id), None)


def _render_behavioral(packets: Sequence[Mapping[str, Any]]) -> list[str]:
    if not packets:
        return ["No standardized behavioral evidence packet was supplied.", ""]
    lines: list[str] = []
    for packet in packets:
        campaign = packet.get("campaign") or {}
        lines.extend(
            [
                f"## Evidence Packet: {campaign.get('campaign_id')}",
                "",
                f"Runs / turns: `{campaign.get('run_count')}` / `{campaign.get('turn_count')}`",
                f"Runtime/model boundary: {campaign.get('gm_boundary')}",
                "",
            ]
        )
        for category, label in (
            ("representative_success", "Representative success"),
            ("representative_failure", "Representative failure"),
            ("evaluator_disagreement", "Evaluator disagreement"),
            ("unexpected_unclassified", "Ambiguous/unexpected"),
            ("stress_probe", "Stress probe"),
        ):
            example = _selected_example(packet, category)
            if example is None:
                lines.extend([f"### {label}", "", "No example observed in this campaign.", ""])
                continue
            lines.extend(
                [
                    f"### {label}",
                    "",
                    f"Example: `{example.get('example_id')}`",
                    f"Player classification: `{', '.join(example.get('player_input_classification') or [])}`",
                    f"Player: {example.get('player_input')}",
                    f"GM: {example.get('exact_gm_output')}",
                    f"Automated result: `{example.get('semantic_result') or example.get('historical_result') or 'UNAVAILABLE'}`",
                    f"Human review: `{(example.get('human_review') or {}).get('status')}` - {(example.get('human_review') or {}).get('rationale')}",
                    f"Source: `{example.get('source_artifact_path')}`",
                    "",
                ]
            )
        disagreements = [
            row for row in packet.get("examples") or [] if (row.get("evaluator_disagreement") or {}).get("present")
        ]
        lines.extend(["### All evaluator disagreements", ""])
        if not disagreements:
            lines.extend(["No example observed in this campaign.", ""])
        for example in disagreements:
            lines.extend(
                [
                    f"- `{example.get('example_id')}`: automated `{example.get('semantic_result') or example.get('historical_result')}`; "
                    f"human `{(example.get('human_review') or {}).get('status')}`; player: {example.get('player_input')}; "
                    f"GM: {example.get('exact_gm_output')}",
                ]
            )
        lines.append("")
    return lines


def render_review(
    config: Mapping[str, Any],
    *,
    included: Sequence[Mapping[str, Any]],
    omitted: Sequence[Mapping[str, Any]],
    behavioral_packets: Sequence[Mapping[str, Any]],
    generated_at: str,
    bundle_size_bytes: int,
    warning_threshold: int,
) -> str:
    changes = config.get("changes") or {}
    testing = config.get("testing") or {}
    decisions = list(config.get("decisions_requiring_human_review") or [])
    known = config.get("known_problems") or {}
    lines = [
        "# Campaign",
        "",
        f"Campaign: {config.get('campaign_name')}",
        f"Identifier: `{config.get('campaign_id')}`",
        f"Date: {config.get('campaign_date')}",
        f"Generated: {generated_at}",
        f"Purpose: {config.get('purpose')}",
        "",
        "# Executive Summary",
        "",
        str(config.get("executive_summary") or ""),
        "",
        f"Objective status: `{config.get('objective_status')}`.",
        "",
        "# Changes Made",
        "",
    ]
    for key, label in (
        ("production", "Production changes"),
        ("validation", "Validation changes"),
        ("tooling", "Tooling changes"),
        ("documentation", "Documentation changes"),
        ("generated_artifacts", "Generated artifacts"),
    ):
        values = list(changes.get(key) or [])
        lines.extend([f"## {label}", ""])
        lines.extend([f"- {value}" for value in values] or ["- No changes in this category."])
        lines.append("")
    lines.extend(["# What Was Tested", ""])
    for key, label in (
        ("focused", "Focused tests"),
        ("broader", "Broader relevant tests"),
        ("full_suite", "Full suite"),
        ("runtime_validation", "Runtime validation"),
        ("model_runtime_boundary", "Model/runtime boundary"),
        ("new_regressions", "New regressions"),
        ("pre_existing_failures", "Pre-existing failures"),
    ):
        lines.append(f"- **{label}:** {testing.get(key) or 'Not reported.'}")
    lines.append(f"- **Self-contained bundle review:** {config.get('self_contained_review_test') or 'Not performed.'}")
    lines.extend(["", "# Behavioral Evidence", ""])
    lines.extend(_render_behavioral(behavioral_packets))
    lines.extend(["# Decisions Requiring Human Review", ""])
    lines.extend([f"- {value}" for value in decisions] or ["No human decision is required before the next planned step."])
    lines.extend(["", "# Known Problems / Unresolved Findings", "", "## Campaign-specific", ""])
    lines.extend([f"- {value}" for value in known.get("campaign_specific") or []] or ["- None reported."])
    lines.extend(["", "## Pre-existing baseline", ""])
    lines.extend([f"- {value}" for value in known.get("pre_existing") or []] or ["- None reported."])
    lines.extend(["", "# Missing Concepts / Future Capabilities", ""])
    lines.extend([f"- {value}" for value in config.get("missing_concepts") or []] or ["- None recorded."])
    lines.extend(["", "# What This Campaign Does NOT Prove", ""])
    lines.extend([f"- {value}" for value in config.get("does_not_prove") or []] or ["- No limitations recorded."])
    lines.extend(["", "# Recommended Next Step", "", str(config.get("recommended_next_step") or "No next step recorded."), ""])
    lines.extend(["# Review Bundle Contents", ""])
    lines.append(f"Bundle file count: `{len(included) + 2}`")
    lines.append(f"Bundle ZIP size: `{bundle_size_bytes:012d}` bytes")
    lines.append(f"Size warning threshold: `{warning_threshold}` bytes")
    lines.append(
        f"Size status: `{'WARNING_THRESHOLD_EXCEEDED' if bundle_size_bytes > warning_threshold else 'WITHIN_THRESHOLD'}`"
    )
    lines.append("")
    lines.append("- `CURRENT_REVIEW.md`: generated orientation and decision surface.")
    lines.append("- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.")
    for row in included:
        lines.append(f"- `{row['bundle_path']}`: {row['why']} Canonical source: `{row['canonical_source_path']}`.")
    lines.extend(["", "## Explicit omissions", ""])
    lines.extend(
        [f"- `{row['path']}`: {row['reason']}" for row in omitted]
        or ["No explicitly requested file was omitted."]
    )
    lines.extend(
        [
            "",
            "The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.",
            "Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.",
            "",
        ]
    )
    return "\n".join(lines)


def _zip_bytes(files: Mapping[str, bytes]) -> bytes:
    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = (
                zipfile.ZIP_STORED if name in {"CURRENT_REVIEW.md", "REVIEW_MANIFEST.json"} else zipfile.ZIP_DEFLATED
            )
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return buffer.getvalue()


def build_handoff(
    config: Mapping[str, Any],
    *,
    root: Path = ROOT,
    output_dir: Path = DEFAULT_HANDOFF,
    generated_at: str | None = None,
    archive_history: bool = True,
) -> dict[str, Any]:
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    included, omitted = collect_sources(config, root=root)
    behavioral = _load_behavioral(config, root=root)
    warn_bytes = int(config.get("warn_bundle_bytes") or DEFAULT_WARN_BUNDLE_BYTES)
    support_bytes = {
        str(row["bundle_path"]): (root / str(row["canonical_source_path"])).read_bytes() for row in included
    }
    bundle_size = 0
    final_summary = ""
    final_manifest: dict[str, Any] = {}
    final_zip = b""
    for _ in range(8):
        summary = render_review(
            config,
            included=included,
            omitted=omitted,
            behavioral_packets=behavioral,
            generated_at=generated,
            bundle_size_bytes=bundle_size,
            warning_threshold=warn_bytes,
        )
        summary_bytes = summary.encode("utf-8")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "campaign_id": config.get("campaign_id"),
            "campaign_name": config.get("campaign_name"),
            "generated_at": generated,
            "summary_path": "CURRENT_REVIEW.md",
            "generation_tool": "tools/build_review_handoff.py",
            "generation_tool_version": TOOL_VERSION,
            "included_files": [
                {
                    "bundle_path": "CURRENT_REVIEW.md",
                    "canonical_source_path": None,
                    "role": "review_summary",
                    "canonical": False,
                    "generated": True,
                    "why": "Stable human-readable review surface.",
                    "behavioral_evidence": bool(behavioral),
                    "human_review_required": True,
                    "size_bytes": len(summary_bytes),
                    "sha256": _sha256_bytes(summary_bytes),
                },
                {
                    "bundle_path": "REVIEW_MANIFEST.json",
                    "canonical_source_path": None,
                    "role": "review_manifest",
                    "canonical": False,
                    "generated": True,
                    "why": "Portable provenance and bundle-policy record.",
                    "behavioral_evidence": False,
                    "human_review_required": False,
                    "size_bytes": None,
                    "sha256": None,
                },
                *included,
            ],
            "omitted_artifacts": omitted,
            "omitted_artifact_policy": (
                "Explicit sources only. Sensitive, recursive handoff/ZIP, missing, oversized, and duplicate files are omitted "
                "with a reason and canonical reference. Unrelated repository/artifact trees are not discovered."
            ),
            "sensitive_file_policy": (
                "Reject .env variants, credential/API-key/token/secret/private-key/auth-cache filename patterns, key/certificate "
                "suffixes, VCS, virtualenv, dependency, and cache paths without inspecting secret values."
            ),
            "bundle_metrics": {
                "file_count": len(included) + 2,
                "zip_size_bytes": f"{bundle_size:012d}",
                "uncompressed_payload_bytes": len(summary_bytes)
                + sum(int(row["size_bytes"]) for row in included),
                "warning_threshold_bytes": warn_bytes,
                "warning": bundle_size > warn_bytes,
            },
            "provenance": {
                "configuration_source": config.get("configuration_source"),
                "canonical_repository_root": ".",
            },
        }
        manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        files = {"CURRENT_REVIEW.md": summary_bytes, "REVIEW_MANIFEST.json": manifest_bytes, **support_bytes}
        zip_bytes = _zip_bytes(files)
        measured = len(zip_bytes)
        final_summary, final_manifest, final_zip = summary, manifest, zip_bytes
        if measured == bundle_size:
            break
        bundle_size = measured

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "CURRENT_REVIEW.md"
    manifest_path = output_dir / "REVIEW_MANIFEST.json"
    zip_path = output_dir / "CURRENT_REVIEW.zip"
    summary_path.write_text(final_summary, encoding="utf-8")
    manifest_path.write_text(json.dumps(final_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    zip_path.write_bytes(final_zip)
    if archive_history:
        history = output_dir / "history" / str(config["campaign_id"])
        history.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(summary_path, history / "REVIEW.md")
        shutil.copyfile(manifest_path, history / "REVIEW_MANIFEST.json")
        shutil.copyfile(zip_path, history / "REVIEW.zip")
    return {
        "summary_path": str(summary_path),
        "manifest_path": str(manifest_path),
        "zip_path": str(zip_path),
        "file_count": len(included) + 2,
        "zip_size_bytes": len(final_zip),
        "warning": len(final_zip) > warn_bytes,
        "included": included,
        "omitted": omitted,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Explicit campaign handoff configuration JSON.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--generated-at", help="Optional stable ISO timestamp for reproducible generation.")
    parser.add_argument("--no-history", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config_path = _safe_resolve(args.config, root=ROOT)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["configuration_source"] = config_path.relative_to(ROOT).as_posix()
    result = build_handoff(
        config,
        root=ROOT,
        output_dir=args.output_dir,
        generated_at=args.generated_at,
        archive_history=not args.no_history,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
