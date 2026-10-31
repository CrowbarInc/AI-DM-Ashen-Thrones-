from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from tools.build_review_handoff import (
    REQUIRED_SUMMARY_SECTIONS,
    build_handoff,
    collect_sources,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG = ROOT / "data/validation/review_handoffs/validation_evidence_standard.json"
GENERATED_AT = "2026-09-18T03:00:00+00:00"


def _config() -> dict:
    config = json.loads(DEMO_CONFIG.read_text(encoding="utf-8"))
    config["configuration_source"] = DEMO_CONFIG.relative_to(ROOT).as_posix()
    return config


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generates_stable_summary_zip_manifest_and_required_sections(tmp_path: Path) -> None:
    result = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path / "handoff", generated_at=GENERATED_AT, archive_history=False
    )
    summary = Path(result["summary_path"])
    bundle = Path(result["zip_path"])
    manifest = Path(result["manifest_path"])

    assert summary.is_file()
    assert bundle.is_file()
    assert manifest.is_file()
    text = summary.read_text(encoding="utf-8")
    assert all(section in text for section in REQUIRED_SUMMARY_SECTIONS)
    with zipfile.ZipFile(bundle) as archive:
        assert "CURRENT_REVIEW.md" in archive.namelist()
        assert "REVIEW_MANIFEST.json" in archive.namelist()


def test_manifest_has_provenance_and_exact_archive_metrics(tmp_path: Path) -> None:
    result = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False
    )
    manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
    canonical = [row for row in manifest["included_files"] if row["canonical"]]

    assert canonical
    assert all(row["canonical_source_path"] and row["sha256"] for row in canonical)
    assert int(manifest["bundle_metrics"]["zip_size_bytes"]) == Path(result["zip_path"]).stat().st_size
    assert manifest["bundle_metrics"]["file_count"] == len(manifest["included_files"])


def test_behavioral_disagreements_and_review_decisions_are_on_front_page(tmp_path: Path) -> None:
    result = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False
    )
    text = Path(result["summary_path"]).read_text(encoding="utf-8")

    assert 'GM: Tavern Runner grimaces. "Not something I can say here."' in text
    assert 'GM: The guard says, "I do not know enough to answer that."' in text
    assert "HUMAN_ACCEPTED" in text and "HUMAN_REJECTED" in text and "HUMAN_AMBIGUOUS" in text
    assert "Decide in a later calibration campaign" in text
    assert "stress_probe" in text


def test_empty_decision_state_is_explicit(tmp_path: Path) -> None:
    config = _config()
    config["decisions_requiring_human_review"] = []
    result = build_handoff(config, root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False)
    text = Path(result["summary_path"]).read_text(encoding="utf-8")
    assert "No human decision is required before the next planned step." in text


def test_new_and_preexisting_failures_are_distinguished(tmp_path: Path) -> None:
    result = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False
    )
    text = Path(result["summary_path"]).read_text(encoding="utf-8")
    assert "## Campaign-specific" in text
    assert "## Pre-existing baseline" in text
    assert "49 failures" in text


def test_sensitive_recursive_and_oversized_sources_are_explicitly_omitted(tmp_path: Path) -> None:
    (tmp_path / "report.md").write_text("report", encoding="utf-8")
    (tmp_path / ".env").write_text("DO_NOT_PACKAGE", encoding="utf-8")
    (tmp_path / "previous.zip").write_bytes(b"old bundle")
    (tmp_path / "large.json").write_bytes(b"x" * 64)
    config = {
        "primary_report": "report.md",
        "max_file_bytes": 16,
        "supporting_files": [
            {"path": ".env"},
            {"path": "previous.zip"},
            {"path": "large.json"},
        ],
    }
    included, omitted = collect_sources(config, root=tmp_path)
    assert [row["path"] for row in included] == ["report.md"]
    reasons = {row["path"]: row["reason"] for row in omitted}
    assert "sensitive filename pattern" in reasons[".env"]
    assert "ZIP inclusion prohibited" in reasons["previous.zip"]
    assert "exceeds max_file_bytes" in reasons["large.json"]


def test_missing_optional_source_is_reported_without_corrupting_bundle(tmp_path: Path) -> None:
    config = _config()
    config["supporting_files"].append({"path": "docs/does_not_exist.md", "role": "optional"})
    result = build_handoff(config, root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False)
    assert Path(result["zip_path"]).is_file()
    assert any(row["path"] == "docs/does_not_exist.md" and row["reason"] == "source file missing" for row in result["omitted"])


def test_structural_only_campaign_has_lightweight_handoff_without_behavioral_claims(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "report.md").write_text("# Structural report\nSchema contract passed.\n", encoding="utf-8")
    config = {
        "campaign_id": "structural_schema",
        "campaign_name": "Structural schema check",
        "campaign_date": "2026-09-18",
        "purpose": "Check schema shape.",
        "objective_status": "ACHIEVED",
        "executive_summary": "A structural contract was checked.",
        "changes": {},
        "testing": {"focused": "Schema tests passed."},
        "decisions_requiring_human_review": [],
        "known_problems": {},
        "missing_concepts": [],
        "does_not_prove": ["Semantic gameplay quality."],
        "recommended_next_step": "No behavioral conclusion.",
        "primary_report": "report.md",
        "evidence_packets": [],
        "supporting_files": [],
    }
    result = build_handoff(config, root=root, output_dir=root / "handoff", generated_at=GENERATED_AT, archive_history=False)
    text = Path(result["summary_path"]).read_text(encoding="utf-8")
    assert "No standardized behavioral evidence packet was supplied." in text
    assert "Semantic gameplay quality" in text


def test_generation_does_not_modify_canonical_sources(tmp_path: Path) -> None:
    sources = (
        ROOT / "docs/validation_evidence_standard.md",
        ROOT / "artifacts/validation_evidence/reactive_adversarial/evidence_manifest.json",
    )
    before = {path: _digest(path) for path in sources}
    build_handoff(_config(), root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False)
    assert {path: _digest(path) for path in sources} == before


def test_repeated_generation_is_byte_stable_for_fixed_inputs_and_timestamp(tmp_path: Path) -> None:
    first = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path / "one", generated_at=GENERATED_AT, archive_history=False
    )
    second = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path / "two", generated_at=GENERATED_AT, archive_history=False
    )
    assert _digest(Path(first["zip_path"])) == _digest(Path(second["zip_path"]))
    assert Path(first["summary_path"]).read_bytes() == Path(second["summary_path"]).read_bytes()


def test_bundle_only_self_contained_review_answers_required_questions(tmp_path: Path) -> None:
    result = build_handoff(
        _config(), root=ROOT, output_dir=tmp_path, generated_at=GENERATED_AT, archive_history=False
    )
    extract = tmp_path / "extracted"
    with zipfile.ZipFile(result["zip_path"]) as archive:
        archive.extractall(extract)
    summary = (extract / "CURRENT_REVIEW.md").read_text(encoding="utf-8")
    manifest = json.loads((extract / "REVIEW_MANIFEST.json").read_text(encoding="utf-8"))

    required_answers = (
        "Review Handoff Automation",
        "# Changes Made",
        "No changes in this category.",
        "# What Was Tested",
        "49 failures",
        "# Behavioral Evidence",
        "Player:",
        "GM:",
        "All evaluator disagreements",
        "HUMAN_AMBIGUOUS",
        "# Decisions Requiring Human Review",
        "# What This Campaign Does NOT Prove",
        "# Recommended Next Step",
    )
    assert all(answer in summary for answer in required_answers)
    assert all(row.get("canonical_source_path") for row in manifest["included_files"] if row["canonical"])
