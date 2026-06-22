"""Registry authority and golden_replay marker discoverability for protected replay (BW1)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.helpers.protected_replay_registry import (
    BX_SPEAKER_PARITY_MODULE,
    DIRECT_SEAM_MODULE,
    LONG_SESSION_MODULE,
    ProtectionStatus,
    SCENARIO_SPINE_MODULE,
    STRUCTURAL_INVARIANTS_MODULE,
    bx_speaker_parity_corpus,
    bx_speaker_parity_corpus_test_node_ids,
    protected_replay_corpus,
    protected_replay_corpus_test_node_ids,
    protected_replay_registry,
    protected_replay_registry_validation_errors,
)

ROOT = Path(__file__).resolve().parents[1]


def test_protected_replay_registry_contains_six_short_structural_scenarios() -> None:
    corpus = protected_replay_corpus()

    assert len(corpus) == 6
    assert {entry.test_module for entry in corpus} == {STRUCTURAL_INVARIANTS_MODULE}
    assert {entry.scenario_id for entry in corpus} == {
        "directed_npc_question",
        "vocative_override_after_prior_continuity",
        "wrong_speaker_strict_social_emission",
        "thin_answer_action_outcome_final_emission",
        "sanitizer_scaffold_leakage",
        "lead_followup_with_dialogue_lock",
    }


def test_protected_replay_registry_scenario_ids_are_unique() -> None:
    assert protected_replay_registry_validation_errors() == []
    scenario_ids = [entry.scenario_id for entry in protected_replay_registry()]
    assert len(scenario_ids) == len(set(scenario_ids))


def test_protected_replay_registry_order_is_stable() -> None:
    first = protected_replay_registry()
    second = protected_replay_registry()

    assert first == second
    assert [entry.sort_key for entry in first] == sorted(entry.sort_key for entry in first)


def test_diagnostic_replay_scenarios_are_not_promoted_to_protected_corpus() -> None:
    corpus_node_ids = set(protected_replay_corpus_test_node_ids())
    supporting = [
        entry
        for entry in protected_replay_registry()
        if entry.protection_status is not ProtectionStatus.PROTECTED
    ]

    assert supporting
    for entry in supporting:
        assert entry.test_node_id not in corpus_node_ids
        assert entry.protection_status is ProtectionStatus.SUPPORTING

    supporting_modules = {entry.test_module for entry in supporting}
    assert LONG_SESSION_MODULE in supporting_modules
    assert DIRECT_SEAM_MODULE in supporting_modules
    assert SCENARIO_SPINE_MODULE in supporting_modules


def test_bx_speaker_parity_corpus_contains_four_guard_matrix_scenarios() -> None:
    corpus = bx_speaker_parity_corpus()

    assert len(corpus) == 4
    assert {entry.test_module for entry in corpus} == {BX_SPEAKER_PARITY_MODULE}
    assert {entry.scenario_id for entry in corpus} == {
        "bx5_guard_role_alias_guard_captain",
        "bx5_guard_canonical_guard_captain",
        "bx5_guard_gate_guard_distinct",
        "bx5_guard_ambiguous_multi_guard",
    }


def test_bx_speaker_parity_marker_collects_registered_corpus_tests() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "bx_speaker_parity", "--collect-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 0, output
    collected_node_ids = {
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().startswith("tests/") and "::" in line
    }
    assert collected_node_ids >= set(bx_speaker_parity_corpus_test_node_ids()), (
        f"collected={sorted(collected_node_ids)!r} "
        f"expected_at_least={sorted(bx_speaker_parity_corpus_test_node_ids())!r}"
    )


def test_golden_replay_marker_collects_protected_corpus_tests() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "golden_replay", "--collect-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 0, output
    assert "6/" in output and "tests collected" in output, output

    collected_node_ids = {
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().startswith("tests/") and "::" in line
    }
    assert collected_node_ids == set(protected_replay_corpus_test_node_ids()), (
        f"collected={sorted(collected_node_ids)!r} "
        f"expected={sorted(protected_replay_corpus_test_node_ids())!r}"
    )


def test_golden_replay_marker_does_not_collect_diagnostic_modules() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            LONG_SESSION_MODULE,
            DIRECT_SEAM_MODULE,
            SCENARIO_SPINE_MODULE,
            "-m",
            "golden_replay",
            "--collect-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 5, output
    assert "no tests collected" in output.lower(), output
