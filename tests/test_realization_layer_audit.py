"""Tests for the advisory realization-layer audit tool."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "realization_layer_audit.py"


@pytest.fixture(scope="module")
def audit_mod():
    name = "_realization_layer_audit_tool_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def scratch_dir() -> Path:
    path = ROOT / "artifacts" / "test_realization_layer_audit_tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        if path.exists() and ROOT in path.parents:
            shutil.rmtree(path, ignore_errors=True)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_tool_imports_successfully(audit_mod) -> None:
    assert audit_mod.AUTHORITY_PROFILES
    assert audit_mod.FALLBACK_FAMILIES
    assert audit_mod.SEVERITIES == ("INFO", "REVIEW", "HIGH")


def test_scanner_works_on_small_temporary_fixture(audit_mod, scratch_dir: Path) -> None:
    fixture = scratch_dir / "game" / "final_emission_gate.py"
    _write(
        fixture,
        "# Comment mentions fallback and repair only as documentation.\n"
        "def apply_gate(gm_output, resolution, session):\n"
        "    player_facing_text = repair_fallback_from_resolution(gm_output, resolution, session)\n"
        "    return player_facing_text\n",
    )
    findings, scanned = audit_mod.scan_paths([fixture], root=scratch_dir)
    assert scanned == ["game/final_emission_gate.py"]
    assert findings
    assert any(f.severity == "HIGH" for f in findings)
    assert any(f.severity == "INFO" for f in findings)


def test_structured_findings_include_required_fields(audit_mod) -> None:
    findings = audit_mod.scan_text(
        "def build_prompt(messages):\n"
        "    return reconstruct_missing_scene_semantics(messages)\n",
        file="game/prompt_context.py",
    )
    required = {
        "file",
        "line",
        "severity",
        "matched_term",
        "category",
        "message",
        "text_excerpt",
    }
    assert findings
    for finding in findings:
        assert set(audit_mod.asdict(finding)) == required


def test_severity_values_are_only_expected_values(audit_mod) -> None:
    findings = audit_mod.scan_text(
        "# fallback comment\n"
        "def call_gpt(messages):\n"
        "    return synthesize_fallback_scene_from_resolution(messages)\n",
        file="game/gm.py",
    )
    assert findings
    assert {f.severity for f in findings} <= set(audit_mod.SEVERITIES)


def test_report_generation_writes_json_and_markdown(audit_mod, scratch_dir: Path) -> None:
    fixture = scratch_dir / "game" / "gm_retry.py"
    _write(
        fixture,
        "def retry_terminal(gm_output, resolution):\n"
        "    return invent_fallback_prose_from_resolution(gm_output, resolution)\n",
    )
    findings, scanned = audit_mod.scan_paths([fixture], root=scratch_dir)
    out_dir = scratch_dir / "artifacts"
    outputs = audit_mod.write_reports(findings, scanned, root=scratch_dir, output_dir=out_dir)
    assert outputs["json"].is_file()
    assert outputs["markdown"].is_file()

    payload = json.loads(outputs["json"].read_text(encoding="utf-8"))
    assert payload["advisory_only"] is True
    assert payload["ci_enforced"] is False
    assert payload["findings"]
    assert "authority_profiles" in payload["ledger"]
    md = outputs["markdown"].read_text(encoding="utf-8")
    assert "Summary by Severity" in md
    assert "not CI-enforced" in md
    assert "game.realization_authority" in md


def test_audit_references_ledger_without_heavy_runtime_imports() -> None:
    source = TOOL_PATH.read_text(encoding="utf-8")
    assert "from game.realization_authority import" in source
    assert "FALLBACK_FAMILIES" in source
    assert "AUTHORITY_PROFILES" in source
    forbidden_imports = (
        "import game.gm",
        "import game.prompt_context",
        "import game.final_emission_gate",
        "from game.gm",
        "from game.prompt_context",
        "from game.final_emission_gate",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source


def test_real_repo_scan_does_not_require_zero_findings(audit_mod) -> None:
    findings, scanned = audit_mod.scan_repo(root=ROOT)
    assert scanned
    assert isinstance(findings, list)
