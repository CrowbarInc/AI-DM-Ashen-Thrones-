"""Static audit for Planner Convergence (Block D): ``tools/planner_convergence_audit``."""

from __future__ import annotations

from pathlib import Path

from tools.planner_convergence_audit import (
    APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS,
    audit_build_narrative_plan_call_sites,
    audit_emergency_player_facing_functions,
    audit_file,
    audit_narration_plan_bundle_projection_keys,
    audit_prompt_context_raw_semantic_shortcuts,
    run_planner_convergence_audit,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Canonical command strings documented in docs/planner_convergence.md (discoverability guard).
_DOC_AUDIT_CMD = "python tools/planner_convergence_audit.py"
_DOC_FOCUSED_PYTEST = (
    "py -3 -m pytest tests/test_planner_convergence_contract.py "
    "tests/test_planner_convergence_live_pipeline.py "
    "tests/test_prompt_context_plan_only_convergence.py "
    "tests/test_planner_convergence_static_audit.py"
)


def test_planner_convergence_doc_lists_audit_and_focused_pytest_commands() -> None:
    doc = (REPO_ROOT / "docs" / "planner_convergence.md").read_text(encoding="utf-8")
    assert _DOC_AUDIT_CMD in doc
    assert _DOC_FOCUSED_PYTEST in doc
    makefile = REPO_ROOT / "Makefile"
    assert makefile.is_file()
    mk = makefile.read_text(encoding="utf-8")
    assert "planner-convergence-audit:" in mk
    assert "planner-convergence-check:" in mk
    assert "planner_convergence_audit.py" in mk


def test_audit_passes_current_architecture_after_block_c() -> None:
    ok, issues = run_planner_convergence_audit(repo_root=REPO_ROOT)
    assert ok, issues


def test_injected_prompt_context_build_narrative_plan_call_flagged() -> None:
    base = (REPO_ROOT / "game" / "prompt_context.py").read_text(encoding="utf-8")
    injected = base + "\n# static_audit_injection: forbidden second planner\nbuild_narrative_plan(ctir=None)\n"
    issues = audit_build_narrative_plan_call_sites("game/prompt_context.py", injected)
    assert issues, "expected build_narrative_plan outside approved owners to fail"
    assert any("build_narrative_plan" in msg for msg in issues)


def test_injected_prompt_context_raw_semantic_shortcut_flagged() -> None:
    bad = '''
def build_narration_context():
    _ = world.get("semantic_shortcut_for_narrative_plan") + str(narrative_plan)
    return {}
'''
    issues = audit_prompt_context_raw_semantic_shortcuts("game/prompt_context.py", bad)
    assert issues
    assert any("raw-state" in msg or "shortcut" in msg for msg in issues)


def test_injected_raw_semantic_shortcut_allowed_with_presentation_marker() -> None:
    ok_line = (
        '    x = world.get("presentation")  # planner_convergence_presentation_only\n'
        "    _ = str(narrative_plan)\n"
    )
    src = "def build_narration_context():\n" + ok_line + "    return {}\n"
    issues = audit_prompt_context_raw_semantic_shortcuts("game/prompt_context.py", src)
    assert not issues


def test_injected_full_plan_top_level_narrative_plan_shipment_flagged() -> None:
    bad = """
from typing import Any, Dict

def build_narration_context():
    narrative_plan = {"version": 1, "narrative_mode": "continuation"}
    payload: Dict[str, Any] = {
        "narrative_plan": narrative_plan,
    }
    return payload
"""
    issues = audit_file("game/prompt_context.py", source=bad)
    assert any("payload['narrative_plan']" in msg or "narrative_plan" in msg for msg in issues), issues


def test_injected_player_facing_fallback_without_emergency_registration_flagged() -> None:
    bad = '''
def rogue_emergency_fallback(gm, session):
    gm["player_facing_text"] = "Unregistered nonplan line."
    return gm
'''
    issues = audit_emergency_player_facing_functions(bad, rel_path="synthetic_emergency.py")
    assert issues


def test_registered_emergency_fallback_sample_passes() -> None:
    good = '''
def emergency_fallback_sample(session):
    gm = {"player_facing_text": "Registered nonplan line."}
    record_emergency_nonplan_output(session, reason="audit_fixture", owner_module=__name__)
    return gm
'''
    assert not audit_emergency_player_facing_functions(good, rel_path="synthetic_emergency.py")


def test_approved_public_projection_keys_match_bundle_implementation() -> None:
    rel = "game/narration_plan_bundle.py"
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert not audit_narration_plan_bundle_projection_keys(rel, text)
    # Contract doc + audit constant stay aligned (update both if projection grows).
    assert APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS == frozenset(
        {
            "version",
            "narrative_mode",
            "role_allocation",
            "scene_anchors",
            "active_pressures",
            "required_new_information",
            "allowable_entity_references",
            "narrative_roles",
            "narrative_mode_contract",
        }
    )


def test_prompt_context_payload_uses_projection_only_on_real_file() -> None:
    text = (REPO_ROOT / "game" / "prompt_context.py").read_text(encoding="utf-8")
    issues = audit_file("game/prompt_context.py", source=text)
    payload_issues = [m for m in issues if "payload['narrative_plan']" in m]
    assert not payload_issues, payload_issues
