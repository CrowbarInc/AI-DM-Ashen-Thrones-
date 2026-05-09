"""Tests for the advisory realization provenance coverage audit."""
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
TOOL_PATH = ROOT / "tools" / "realization_provenance_audit.py"


@pytest.fixture(scope="module")
def audit_mod():
    name = "_realization_provenance_audit_tool_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def scratch_dir() -> Path:
    path = ROOT / "artifacts" / "test_realization_provenance_audit_tmp" / uuid.uuid4().hex
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
    assert audit_mod.TARGET_FILES
    assert audit_mod.SEVERITIES == ("INFO", "REVIEW", "HIGH")
    assert "realization_fallback_family" in audit_mod.PROVENANCE_TERMS


def test_scanner_detects_unlabeled_fallback_prose_in_temp_fixture(audit_mod, scratch_dir: Path) -> None:
    fixture = scratch_dir / "game" / "gm.py"
    _write(
        fixture,
        "def provider_failure():\n"
        "    gm_output = {\n"
        "        'player_facing_text': 'The game master is temporarily unavailable. Please try again.',\n"
        "    }\n"
        "    return fallback_gm_output(gm_output)\n",
    )

    findings, scanned = audit_mod.scan_paths([fixture], root=scratch_dir)
    assert scanned == ["game/gm.py"]
    assert findings
    assert any(f.severity == "HIGH" for f in findings)


def test_scanner_treats_nearby_realization_fallback_family_as_labeled(audit_mod) -> None:
    findings = audit_mod.scan_text(
        "def provider_failure():\n"
        "    gm_output = {'metadata': {}}\n"
        "    attach_realization_fallback_family(gm_output['metadata'], GPT_BUDGET_OR_PROVIDER_FAILURE)\n"
        "    gm_output['player_facing_text'] = 'The game master is temporarily unavailable. Please try again.'\n"
        "    return fallback_gm_output(gm_output)\n",
        file="game/gm.py",
    )
    assert findings
    assert {f.severity for f in findings} == {"INFO"}
    assert any("near realization_fallback_family" in f.message for f in findings)


def test_report_generation_writes_json_and_markdown(audit_mod, scratch_dir: Path) -> None:
    fixture = scratch_dir / "game" / "gm_retry.py"
    _write(
        fixture,
        "def retry_terminal():\n"
        "    player_facing_text = 'The game master is temporarily unavailable. Please try again.'\n"
        "    return {'player_facing_text': player_facing_text, 'source': 'terminal fallback'}\n",
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
    assert payload["summary"]["by_severity"]

    md = outputs["markdown"].read_text(encoding="utf-8")
    assert "Realization Provenance Coverage Audit" in md
    assert "not CI-enforced" in md
    assert "Summary by Severity" in md


def test_severity_values_are_only_expected_values(audit_mod) -> None:
    findings = audit_mod.scan_text(
        "# fallback appears in a comment\n"
        "def apply_repair(gm_output):\n"
        "    return force_text_replacement(gm_output)\n",
        file="game/final_emission_repairs.py",
    )
    assert findings
    assert {f.severity for f in findings} <= set(audit_mod.SEVERITIES)


def test_real_repo_scan_does_not_require_zero_findings(audit_mod) -> None:
    findings, scanned = audit_mod.scan_repo(root=ROOT)
    assert scanned
    assert isinstance(findings, list)
