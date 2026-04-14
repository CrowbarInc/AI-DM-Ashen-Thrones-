"""Unit tests for the static architecture audit CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "architecture_audit.py"


@pytest.fixture(scope="module")
def audit_mod():
    name = "_architecture_audit_tool_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _mini_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "mini_repo"
    _write(
        repo / "game" / "prompt_context.py",
        '"""Prompt layer contract assembly for emitted response policy hints."""\n\n'
        "def build_prompt_contract():\n"
        "    return {'prompt': True}\n",
    )
    _write(
        repo / "game" / "response_policy_contracts.py",
        '"""Canonical owner for response policy contracts."""\n'
        "from game.final_emission_validators import validate_answer\n\n"
        "def build_contract():\n"
        "    return {'enabled': True}\n",
    )
    _write(
        repo / "game" / "final_emission_validators.py",
        '"""Pure validator helpers."""\n\n'
        "def validate_answer():\n"
        "    return True\n",
    )
    _write(
        repo / "game" / "final_emission_repairs.py",
        '"""Repair and layer wiring extracted from the gate for compatibility."""\n'
        "from game.final_emission_validators import validate_answer\n\n"
        "def repair_answer():\n"
        "    return validate_answer()\n\n"
        "def apply_answer_layer():\n"
        "    return repair_answer()\n",
    )
    _write(
        repo / "game" / "final_emission_gate.py",
        '"""The orchestration owner for final emission ordering."""\n\n'
        "from game.final_emission_validators import validate_answer\n\n"
        "def apply_final_emission_gate():\n"
        "    return validate_answer()\n",
    )
    _write(
        repo / "game" / "social_exchange_emission.py",
        '"""Strict social exchange emission; not the ownership home for repairs."""\n\n'
        "def build_social_exchange_emission():\n"
        "    return {'social': True}\n",
    )
    _write(
        repo / "game" / "final_emission_text.py",
        '"""Shared text utilities only; no policy orchestration."""\n\n'
        "def _normalize_text(text=None):\n"
        "    return str(text or '').strip()\n",
    )
    _write(
        repo / "game" / "narrative_authenticity.py",
        '"""Historical compatibility note retained for historical tests."""\n\n'
        "def validate_narrative_authenticity():\n"
        "    return {'passed': True}\n",
    )
    _write(
        repo / "game" / "stage_diff_telemetry.py",
        '"""Telemetry helpers only."""\n\n'
        "def record_stage_snapshot():\n"
        "    return None\n",
    )
    _write(
        repo / "game" / "turn_packet.py",
        '"""Turn packet single source of truth."""\n\n'
        "def get_turn_packet():\n"
        "    return {}\n",
    )
    _write(
        repo / "game" / "prompt_context_leads.py",
        '"""Prompt-context lead helpers only."""\n\n'
        "def build_authoritative_lead_prompt_context():\n"
        "    return {'leads': []}\n",
    )
    _write(
        repo / "tools" / "test_audit.py",
        '"""Inventory tooling."""\n\n'
        "def main():\n"
        "    return 0\n",
    )
    _write(
        repo / "tests" / "test_final_emission_gate.py",
        "import pytest\n\n"
        "pytestmark = pytest.mark.integration\n\n"
        "def test_gate_smoke():\n"
        "    assert True\n",
    )
    _write(
        repo / "tests" / "test_response_policy_contracts.py",
        "import pytest\n"
        "from game.response_policy_contracts import build_contract\n\n"
        "pytestmark = pytest.mark.unit\n\n"
        "def test_build_contract_is_stable():\n"
        "    assert build_contract()['enabled'] is True\n",
    )
    _write(
        repo / "tests" / "test_turn_packet_accessors.py",
        "from game.turn_packet import get_turn_packet\n\n"
        "def test_turn_packet_contract_accessors_are_stable():\n"
        "    assert get_turn_packet() == {}\n",
    )
    _write(
        repo / "tests" / "test_transcript_regression.py",
        "import pytest\n\n"
        "pytestmark = [pytest.mark.transcript, pytest.mark.slow]\n\n"
        "def test_transcript_turn_order_stays_stable(tmp_path, monkeypatch):\n"
        "    transcript = '''Turn 1: Player asks.\\nTurn 2: NPC answers.\\n\"Keep moving,\" the guard says.'''\n"
        "    assert 'Turn 2' in transcript\n",
    )
    _write(
        repo / "tests" / "test_narrative_authenticity.py",
        "def test_narrative_authenticity_smoke():\n"
        "    assert True\n",
    )
    _write(
        repo / "tests" / "README_TESTS.md",
        "# Tests\n\n"
        "Canonical owner notes live here.\n"
        "Smoke overlap is allowed when layers differ.\n",
    )
    _write(
        repo / "tests" / "TEST_AUDIT.md",
        "# Test Audit\n\n"
        "Canonical owner map.\n"
        "Canonical owner for response policy contracts is `tests/test_response_policy_contracts.py`.\n"
        "Canonical owner for turn packet accessors is `tests/test_turn_packet_accessors.py`.\n"
        "Transcript overlap belongs in `tests/test_transcript_regression.py`.\n",
    )
    _write(
        repo / "tests" / "TEST_CONSOLIDATION_PLAN.md",
        "# Consolidation\n\n"
        "Deferred extraction notes.\n"
        "Inventory docs remain canonical only when practical owner tests agree.\n",
    )
    _write(
        repo / "docs" / "narrative_integrity_architecture.md",
        "# Narrative Integrity\n\n"
        "The orchestration owner is `game/final_emission_gate.py`.\n"
        "The canonical owner for response policy contracts is `game/response_policy_contracts.py`.\n"
        "See `tests/TEST_AUDIT.md` and `docs/missing_doc.md`.\n",
    )
    _write(
        repo / "docs" / "current_focus.md",
        "# Current Focus\n\n"
        "Deferred work remains documented here.\n",
    )
    _write(
        repo / "docs" / "ai_gm_contract.md",
        "# Contract\n\n"
        "Prompt contract notes.\n",
    )
    _write(
        repo / "docs" / "system_overview.md",
        "# System Overview\n\n"
        "Single source of truth notes.\n",
    )
    _write(
        repo / "docs" / "README.md",
        "# Docs\n\n"
        "Telemetry and architecture live here.\n",
    )
    _write(
        repo / "docs" / "testing.md",
        "# Testing\n\n"
        "Canonical owner test notes.\n",
    )
    _write(
        repo / "docs" / "narrative_authenticity_anti_echo_rumor_realism.md",
        "# Narrative Authenticity\n\n"
        "AER notes.\n",
    )
    return repo


def _synthetic_subsystem(
    audit_mod,
    *,
    subsystem_name: str,
    inferred_owner: str = "game/example.py",
    ownership_confidence: str = "high",
    ownership_score: str = "green",
    archaeology_score: str = "green",
    verdict: str = "green",
    role_labels: list[str] | None = None,
    alignment_status: str = "aligned",
    mismatch_type: str = "healthy_overlap",
    severity: str = "low",
    coverage_spread: int = 1,
    overlap_findings: list[dict[str, object]] | None = None,
    archaeology_markers: list[dict[str, str]] | None = None,
    coupling_indicators: dict[str, object] | None = None,
) -> dict[str, object]:
    audit_scores = {
        dimension: {"score": "green", "reason": "synthetic"}
        for dimension in audit_mod.DIMENSIONS
    }
    audit_scores["ownership clarity"]["score"] = ownership_score
    audit_scores["historical residue / archaeology risk"]["score"] = archaeology_score
    return {
        "subsystem_name": subsystem_name,
        "primary_files": [inferred_owner] if inferred_owner != "unknown" else [],
        "declared_owner": inferred_owner,
        "inferred_owner": inferred_owner,
        "ownership_confidence": ownership_confidence,
        "owner_evidence": ["synthetic owner evidence"],
        "role_labels": role_labels or ["contract_owner"],
        "inferred_role": "synthetic role",
        "related_tests": [],
        "related_docs": [],
        "likely_dependencies": [],
        "likely_overlap_points": [],
        "ownership_findings": [],
        "overlap_findings": overlap_findings or [],
        "coupling_indicators": coupling_indicators
        or {
            "max_fan_in": 2,
            "max_fan_out": 1,
            "possible_centrality_hotspots": [],
        },
        "archaeology_markers": archaeology_markers or [],
        "test_ownership_alignment": {
            "concern_name": subsystem_name,
            "runtime_owner": inferred_owner,
            "declared_runtime_owner": inferred_owner,
            "doc_canonical_owners": [],
            "practical_test_owner": "tests/test_example.py" if alignment_status != "unclear" else "unknown",
            "primary_test_homes": [],
            "secondary_test_homes": [],
            "direct_runtime_owner_test_homes": ["tests/test_example.py"] if alignment_status == "aligned" else [],
            "alignment_status": alignment_status,
            "mismatch_type": mismatch_type,
            "severity": severity,
            "healthy_overlap": alignment_status == "aligned",
            "coverage_spread": coverage_spread,
            "category_counts": {},
            "evidence": ["synthetic test alignment evidence"],
        },
        "audit_scores": audit_scores,
        "evidence": {
            "file_metrics": [],
            "ownership_language_hits": [],
            "historical_residue_hits": [],
            "related_doc_reference_issues": [],
        },
        "warnings": [],
        "verdict": verdict,
    }


def test_architecture_audit_cli_generates_json_and_markdown(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    json_out = repo / "artifacts" / "architecture_audit" / "architecture_audit.json"
    md_out = repo / "artifacts" / "architecture_audit" / "architecture_audit.md"

    exit_code = audit_mod.main(
        [
            "--repo-root",
            str(repo),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )

    assert exit_code == 0
    assert json_out.is_file()
    assert md_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert list(payload) == list(audit_mod.TOP_LEVEL_KEYS)
    markdown = md_out.read_text(encoding="utf-8")
    assert "## Executive verdict" in markdown
    assert "## Repo-level scorecard" in markdown
    assert "## Subsystem verdicts" in markdown
    assert "## Strongest evidence that the architecture is real" in markdown
    assert "## Strongest evidence that the architecture may be patch-accumulating" in markdown
    assert "## Known ambiguity hotspots" in markdown
    assert "## Runtime/test/doc mismatch review" in markdown
    assert "## Transcript-lock vs contract-lock risk summary" in markdown
    assert "## Manual spot-check list" in markdown
    assert "## Cleanup-only opportunities" in markdown
    assert "## Stop-before-feature warnings" in markdown


def test_architecture_audit_report_shape_is_stable(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    report = audit_mod.analyze_repo(repo)

    assert set(report) == set(audit_mod.TOP_LEVEL_KEYS)
    assert report["modules_analyzed"]["count"] >= 1
    assert report["docs_analyzed"]["count"] >= 1
    assert report["tests_analyzed"]["count"] >= 1
    assert len(report["subsystem_reports"]) == len(audit_mod.SUBSYSTEM_SEEDS)

    first = report["subsystem_reports"][0]
    assert set(first) == {
        "subsystem_name",
        "primary_files",
        "declared_owner",
        "inferred_owner",
        "ownership_confidence",
        "owner_evidence",
        "role_labels",
        "inferred_role",
        "related_tests",
        "related_docs",
        "likely_dependencies",
        "likely_overlap_points",
        "ownership_findings",
        "overlap_findings",
        "coupling_indicators",
        "archaeology_markers",
        "test_ownership_alignment",
        "audit_scores",
        "evidence",
        "warnings",
        "verdict",
    }
    assert set(first["audit_scores"]) == set(audit_mod.DIMENSIONS)
    assert report["summary"]["broken_doc_reference_count"] == 1
    assert "top_ownership_ambiguities" in report["summary"]
    assert "top_overlap_findings" in report["summary"]
    assert "top_coupling_hotspots" in report["summary"]
    assert "test_category_counts" in report["summary"]
    assert "test_alignment_overview" in report["summary"]
    assert "top_test_runtime_doc_mismatches" in report["summary"]
    assert "likely_transcript_lock_seams" in report["summary"]
    assert "likely_contract_owned_seams_with_weak_direct_tests" in report["summary"]
    assert "inventory_docs_authority_status" in report["summary"]
    assert "manual_review_shortlist" in report["summary"]
    assert "repo_level_verdict" in report["summary"]
    assert "repo_level_confidence" in report["summary"]
    assert "recommended_action_mode" in report["summary"]
    assert "repo_level_scorecard" in report["summary"]
    assert "hotspot_classifications" in report["summary"]
    assert "strongest_evidence_architecture_real" in report["summary"]
    assert "strongest_evidence_patch_accumulating" in report["summary"]
    assert "runtime_test_doc_mismatch_review" in report["summary"]
    assert "transcript_contract_lock_risk_summary" in report["summary"]
    assert "cleanup_only_opportunities" in report["summary"]
    assert "stop_before_feature_warnings" in report["summary"]
    assert "manual_spot_check_list" in report["summary"]
    assert "schema_notes" in report["summary"]
    assert "category_counts" in report["tests_analyzed"]
    assert "file_category_counts" in report["tests_analyzed"]


def test_architecture_audit_infers_runtime_ownership_and_overlap(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    report = audit_mod.analyze_repo(repo)
    by_name = {item["subsystem_name"]: item for item in report["subsystem_reports"]}

    validators = by_name["final emission validators"]
    assert validators["inferred_owner"] == "game/final_emission_validators.py"
    assert "validator_owner" in validators["role_labels"]
    assert validators["ownership_confidence"] in {"medium", "high", "low"}

    gate = by_name["final emission gate orchestration"]
    assert gate["inferred_owner"] == "game/final_emission_gate.py"
    assert "orchestration_owner" in gate["role_labels"]

    prompt_contracts = by_name["prompt contracts"]
    assert prompt_contracts["ownership_findings"]
    assert prompt_contracts["overlap_findings"]


def test_architecture_audit_reconciles_runtime_docs_and_test_ownership(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    report = audit_mod.analyze_repo(repo)
    by_name = {item["subsystem_name"]: item for item in report["subsystem_reports"]}

    response_policy = by_name["response policy contracts"]["test_ownership_alignment"]
    assert response_policy["practical_test_owner"] == "tests/test_response_policy_contracts.py"
    assert response_policy["runtime_owner"] in {
        "game/response_policy_contracts.py",
        "game/final_emission_repairs.py",
    }
    assert response_policy["alignment_status"] in {"aligned", "partial", "conflict"}
    if response_policy["runtime_owner"] != "game/response_policy_contracts.py":
        assert response_policy["alignment_status"] in {"partial", "conflict"}

    test_docs = by_name["test ownership / inventory docs"]["test_ownership_alignment"]
    assert test_docs["mismatch_type"] in {
        "inventory_docs_authority_unclear",
        "inventory_docs_vs_actual_usage",
        "ownership_spread_wide",
        "no_practical_test_owner",
    }
    assert report["summary"]["inventory_docs_authority_status"]["status"] in {"partially clearer", "remains unclear"}


def test_architecture_audit_classifies_test_categories_stably(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    report = audit_mod.analyze_repo(repo)
    test_files = {item["path"]: item for item in report["tests_analyzed"]["files"]}

    assert test_files["tests/test_response_policy_contracts.py"]["inferred_category"] == "unit / pure-rule"
    assert test_files["tests/test_final_emission_gate.py"]["inferred_category"] == "smoke / overlap"
    assert test_files["tests/test_transcript_regression.py"]["inferred_category"] == "transcript / scenario lock"
    assert report["tests_analyzed"]["category_counts"]["transcript / scenario lock"] >= 1


def test_architecture_audit_never_imports_game_modules(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    before = {name for name in sys.modules if name == "game" or name.startswith("game.")}
    audit_mod.analyze_repo(repo)
    after = {name for name in sys.modules if name == "game" or name.startswith("game.")}
    assert after == before


def test_architecture_audit_handles_missing_directories_gracefully(audit_mod, tmp_path):
    repo = tmp_path / "missing_dirs_repo"
    _write(
        repo / "game" / "final_emission_gate.py",
        '"""Orchestration owner."""\n\n'
        "def apply_final_emission_gate():\n"
        "    return None\n",
    )

    json_out = repo / "out.json"
    md_out = repo / "out.md"
    exit_code = audit_mod.main(
        [
            "--repo-root",
            str(repo),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ]
    )

    assert exit_code == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert any("Missing directory handled gracefully" in warning for warning in payload["warnings"])
    assert payload["summary"]["inventory_docs_authority_status"]["status"] in {"missing", "remains unclear"}
    assert md_out.is_file()


def test_architecture_audit_focus_subsystem_rendering(audit_mod, tmp_path):
    repo = _mini_repo(tmp_path)
    report = audit_mod.analyze_repo(repo)

    text = audit_mod._focus_subsystem_text(report, "response policy contracts")

    assert "Focus subsystem: response policy contracts" in text
    assert "Declared owner:" in text
    assert "Inferred owner:" in text
    assert "Overlap:" in text
    assert "Coupling:" in text
    assert "Archaeology:" in text
    assert "Test ownership alignment:" in text
    assert "Key evidence lines:" in text


def test_architecture_audit_rubric_distinguishes_localized_vs_systemwide(audit_mod):
    localized_reports = [
        _synthetic_subsystem(audit_mod, subsystem_name="prompt contracts", alignment_status="partial", mismatch_type="docs_runtime_owner_drift", severity="medium", coverage_spread=3, verdict="yellow"),
        _synthetic_subsystem(audit_mod, subsystem_name="response policy contracts"),
        _synthetic_subsystem(audit_mod, subsystem_name="final emission gate orchestration", archaeology_markers=[{"path": "game/final_emission_gate.py", "kind": "compatibility", "excerpt": "compatibility"}], archaeology_score="yellow", verdict="yellow"),
        _synthetic_subsystem(audit_mod, subsystem_name="stage diff telemetry"),
        _synthetic_subsystem(audit_mod, subsystem_name="test ownership / inventory docs", inferred_owner="tools/test_audit.py", alignment_status="partial", mismatch_type="inventory_docs_vs_actual_usage", severity="medium", coverage_spread=3, verdict="yellow"),
    ]
    localized = audit_mod._synthesize_repo_verdict(
        localized_reports,
        broken_doc_reference_count=1,
        top_overlap_findings=[{"concern_name": "final emission gate", "severity": "medium"}],
        top_coupling_hotspots=[{"path": "game/final_emission_gate.py", "reasons": ["fan-in 7", "fan-out 4"]}],
        top_archaeology_flags=[{"path": "game/final_emission_gate.py", "markers": ["compatibility"]}],
        test_alignment_overview={"aligned": 3, "partial": 2},
        top_test_runtime_doc_mismatches=[{"concern_name": "prompt contracts", "alignment_status": "partial", "severity": "medium", "runtime_owner": "game/example.py", "practical_test_owner": "tests/test_example.py", "coverage_spread": 3, "evidence": ["docs drift"]}],
        concerns_with_widest_test_ownership_spread=[{"concern_name": "prompt contracts", "coverage_spread": 3}],
        likely_transcript_lock_seams=[],
        likely_contract_owned_seams_with_weak_direct_tests=[],
        inventory_docs_authority_status={"status": "partially clearer", "summary": "partial", "evidence": []},
        manual_review_shortlist=[],
    )

    smear_reports = [
        _synthetic_subsystem(audit_mod, subsystem_name="prompt contracts", ownership_score="red", alignment_status="conflict", mismatch_type="transcript_primary_for_contract_owner", severity="high", coverage_spread=8, verdict="red", overlap_findings=[{"overlap_type": "shared_concern_language", "severity": "high", "evidence": ["shared owner language"]}]),
        _synthetic_subsystem(audit_mod, subsystem_name="response policy contracts", ownership_score="red", alignment_status="partial", mismatch_type="docs_claim_owner_tests_target_other_home", severity="high", coverage_spread=7, verdict="red", overlap_findings=[{"overlap_type": "shared_concern_language", "severity": "high", "evidence": ["shared owner language"]}], coupling_indicators={"max_fan_in": 24, "max_fan_out": 8, "possible_centrality_hotspots": [{"path": "game/response_policy_contracts.py"}]}),
        _synthetic_subsystem(audit_mod, subsystem_name="final emission gate orchestration", ownership_score="yellow", alignment_status="partial", mismatch_type="docs_claim_owner_tests_target_other_home", severity="high", coverage_spread=7, verdict="red", archaeology_markers=[{"path": "game/final_emission_gate.py", "kind": "compatibility", "excerpt": "compatibility"}], coupling_indicators={"max_fan_in": 30, "max_fan_out": 12, "possible_centrality_hotspots": [{"path": "game/final_emission_gate.py"}]}),
        _synthetic_subsystem(audit_mod, subsystem_name="stage diff telemetry", ownership_score="yellow", alignment_status="partial", mismatch_type="ownership_spread_wide", severity="high", coverage_spread=7, verdict="yellow", coupling_indicators={"max_fan_in": 22, "max_fan_out": 11, "possible_centrality_hotspots": [{"path": "game/turn_packet.py"}]}),
        _synthetic_subsystem(audit_mod, subsystem_name="test ownership / inventory docs", inferred_owner="unknown", ownership_confidence="unclear", ownership_score="red", alignment_status="unclear", mismatch_type="inventory_docs_authority_unclear", severity="high", coverage_spread=7, verdict="red"),
    ]
    smear = audit_mod._synthesize_repo_verdict(
        smear_reports,
        broken_doc_reference_count=12,
        top_overlap_findings=[
            {"concern_name": "prompt contracts", "severity": "high"},
            {"concern_name": "response policy contracts", "severity": "high"},
            {"concern_name": "stage diff telemetry", "severity": "high"},
            {"concern_name": "social exchange emission", "severity": "high"},
        ],
        top_coupling_hotspots=[
            {"path": "game/final_emission_gate.py", "reasons": ["fan-in 30", "fan-out 12"]},
            {"path": "game/turn_packet.py", "reasons": ["fan-in 22", "fan-out 11"]},
        ],
        top_archaeology_flags=[
            {"path": "game/final_emission_gate.py", "markers": ["compatibility"]},
            {"path": "game/final_emission_repairs.py", "markers": ["compatibility"]},
            {"path": "game/prompt_context_leads.py", "markers": ["extracted_from"]},
        ],
        test_alignment_overview={"partial": 3, "conflict": 1, "unclear": 1},
        top_test_runtime_doc_mismatches=[{"concern_name": "prompt contracts", "alignment_status": "conflict", "severity": "high", "runtime_owner": "game/example.py", "practical_test_owner": "mixed: tests/a.py, tests/b.py", "coverage_spread": 8, "evidence": ["conflict"]}],
        concerns_with_widest_test_ownership_spread=[
            {"concern_name": "prompt contracts", "coverage_spread": 8},
            {"concern_name": "response policy contracts", "coverage_spread": 7},
            {"concern_name": "stage diff telemetry", "coverage_spread": 7},
        ],
        likely_transcript_lock_seams=[{"concern_name": "prompt contracts", "evidence": ["transcript-heavy"]}],
        likely_contract_owned_seams_with_weak_direct_tests=[{"concern_name": "prompt contracts", "evidence": ["weak direct tests"]}, {"concern_name": "response policy contracts", "evidence": ["weak direct tests"]}],
        inventory_docs_authority_status={"status": "remains unclear", "summary": "unclear", "evidence": []},
        manual_review_shortlist=[],
    )

    assert localized["repo_level_verdict"] in {"structurally real, under-consolidated", "transitional but coherent"}
    assert localized["recommended_action_mode"] != "high ambiguity / stop and stabilize before growth"
    assert smear["repo_level_verdict"] == "high ambiguity / architecture risk"
    assert smear["recommended_action_mode"] == "high ambiguity / stop and stabilize before growth"


def test_architecture_audit_hotspot_classification_is_stable(audit_mod):
    smear_report = _synthetic_subsystem(
        audit_mod,
        subsystem_name="prompt contracts",
        alignment_status="conflict",
        mismatch_type="transcript_primary_for_contract_owner",
        severity="high",
        coverage_spread=8,
        overlap_findings=[{"overlap_type": "shared_concern_language", "severity": "high", "evidence": ["shared owner language"]}],
    )
    residue_report = _synthetic_subsystem(
        audit_mod,
        subsystem_name="prompt contracts",
        alignment_status="partial",
        mismatch_type="docs_runtime_owner_drift",
        severity="medium",
        archaeology_markers=[{"path": "game/prompt_context_leads.py", "kind": "extracted_from", "excerpt": "extracted"}],
    )
    unclear_report = _synthetic_subsystem(
        audit_mod,
        subsystem_name="test ownership / inventory docs",
        inferred_owner="unknown",
        ownership_confidence="unclear",
        alignment_status="unclear",
        mismatch_type="inventory_docs_authority_unclear",
        severity="high",
    )
    local_report = _synthetic_subsystem(
        audit_mod,
        subsystem_name="stage diff telemetry",
        alignment_status="partial",
        mismatch_type="docs_runtime_owner_drift",
        severity="medium",
        coverage_spread=3,
    )

    assert audit_mod._classify_hotspot(smear_report, label="prompt contracts conflict")["classification"] == "possible ownership smear"
    assert audit_mod._classify_hotspot(residue_report, label="prompt_context_leads residue", module_path="game/prompt_context_leads.py")["classification"] == "transitional residue"
    assert audit_mod._classify_hotspot(unclear_report, label="test ownership / inventory docs still unclear")["classification"] == "unclear / needs human review"
    assert audit_mod._classify_hotspot(local_report, label="stage diff telemetry partial mismatch")["classification"] == "localized under-consolidation"


def test_architecture_audit_handles_sparse_unknown_synthesis(audit_mod):
    sparse_report = _synthetic_subsystem(
        audit_mod,
        subsystem_name="test ownership / inventory docs",
        inferred_owner="unknown",
        ownership_confidence="unclear",
        ownership_score="unknown",
        archaeology_score="unknown",
        alignment_status="unclear",
        mismatch_type="no_practical_test_owner",
        severity="high",
        verdict="red",
        role_labels=["unclear_owner"],
    )

    summary = audit_mod._synthesize_repo_verdict(
        [sparse_report],
        broken_doc_reference_count=0,
        top_overlap_findings=[],
        top_coupling_hotspots=[],
        top_archaeology_flags=[],
        test_alignment_overview={"unclear": 1},
        top_test_runtime_doc_mismatches=[],
        concerns_with_widest_test_ownership_spread=[],
        likely_transcript_lock_seams=[],
        likely_contract_owned_seams_with_weak_direct_tests=[],
        inventory_docs_authority_status={"status": "missing", "summary": "missing", "evidence": []},
        manual_review_shortlist=[],
    )

    assert summary["repo_level_verdict"] in {"mixed / caution", "high ambiguity / architecture risk"}
    assert len(summary["repo_level_scorecard"]) == 6
    assert summary["repo_level_confidence"] in {"medium", "low"}
