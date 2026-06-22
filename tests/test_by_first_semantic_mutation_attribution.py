"""BY1 — first semantic mutation attribution tests."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import game.output_sanitizer as output_sanitizer_module
from game.final_emission_gate import apply_final_emission_gate
from game.response_policy_enforcement import apply_response_policy_enforcement
from tests.helpers.golden_replay_fixtures import minimal_turn_payload, observed_turn_from_gate_output
from tests.helpers.golden_replay_projection import (
    golden_text_hash,
    project_semantic_mutation_summary,
    project_turn_observation,
    protected_observation_field_paths,
)
from tests.helpers.post_speaker_finalize_probe import (
    chain_enforce_phase_marker,
    install_post_speaker_text_probes,
)
from tests.helpers.semantic_mutation_attribution import (
    CHECKPOINT_POLICY_OUTPUT,
    CHECKPOINT_REPLAY_FINAL_TEXT,
    CHECKPOINT_SANITIZER_OUTPUT,
    SemanticMutationTraceEntry,
    append_semantic_mutation_entry,
    build_semantic_mutation_trace_record,
    compute_first_source_attribution_rate,
    compute_semantic_mutation_risk,
    install_semantic_mutation_probes,
    new_trace_collector,
    normalize_mutation_text,
    mutation_text_hash,
    record_replay_final_text_checkpoint,
    render_semantic_mutation_risk_report,
    render_semantic_mutation_trace_sample,
    select_first_semantic_mutation,
)
from tests.helpers.speaker_relocation_shadow_harness import (
    ShadowEnforceCapture,
    build_finalize_stack_fixture,
    install_dual_run_enforce,
)
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details

pytestmark = pytest.mark.unit


def _entry(
    sequence: int,
    checkpoint_id: str,
    bucket: str,
    source: str,
    before: str,
    after: str,
    *,
    owner: str | None = None,
    mutation_kind: str | None = None,
) -> SemanticMutationTraceEntry:
    before_norm = normalize_mutation_text(before)
    after_norm = normalize_mutation_text(after)
    return SemanticMutationTraceEntry(
        sequence=sequence,
        checkpoint_id=checkpoint_id,
        bucket=bucket,  # type: ignore[arg-type]
        source=source,
        owner=owner,
        mutation_kind=mutation_kind,
        before_normalized=before_norm,
        after_normalized=after_norm,
        before_hash=mutation_text_hash(before_norm),
        after_hash=mutation_text_hash(after_norm),
        normalized_changed=before_norm != after_norm,
    )


def test_by_trace_selects_policy_as_first_normalized_change():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "alpha", "beta"),
        _entry(2, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "beta", "beta"),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["first_semantic_mutation_sequence"] == 1
    assert first["first_semantic_mutation_bucket"] == "policy"
    assert first["first_semantic_mutation_source"] == "policy.enforce"
    assert first["trace_continuity"] is True


def test_by_trace_ignores_formatting_only_change_for_first_semantic_mutation():
    raw_before = "Rain   falls.\n\nOn the road."
    raw_after = "Rain falls. On the road."
    entries = [
        _entry(
            1,
            CHECKPOINT_SANITIZER_OUTPUT,
            "sanitizer",
            "sanitizer.format",
            raw_before,
            raw_after,
        ),
        _entry(2, "narration_purity", "repair", "repair.purity", raw_after, "Rain falls on the road."),
    ]
    first = select_first_semantic_mutation(entries)
    assert entries[0].normalized_changed is False
    assert first["first_semantic_mutation_sequence"] == 2
    assert first["first_semantic_mutation_bucket"] == "repair"


def test_by_trace_selects_sanitizer_strip_before_gate_repair():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "hello", "hello"),
        _entry(
            2,
            CHECKPOINT_SANITIZER_OUTPUT,
            "sanitizer",
            "sanitizer.strip",
            "hello",
            "Rain on the gate road.",
        ),
        _entry(
            3,
            "fallback_behavior",
            "repair",
            "repair.fallback_behavior",
            "Rain on the gate road.",
            "Rain on the gate road.",
        ),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["first_semantic_mutation_bucket"] == "sanitizer"
    assert first["first_semantic_mutation_checkpoint_id"] == CHECKPOINT_SANITIZER_OUTPUT


def test_by_trace_selects_repair_before_later_final_emission_strip():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "seed with dialogue", "seed with dialogue"),
        _entry(
            2,
            "dialogue_plan_subtractive_strip",
            "repair",
            "repair.dialogue_strip",
            "seed with dialogue",
            "stripped seed",
        ),
        _entry(
            3,
            "final_emission_exit",
            "final_emission",
            "finalize.exit",
            "stripped seed",
            "stripped seed.",
        ),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["first_semantic_mutation_bucket"] == "repair"
    assert first["first_semantic_mutation_checkpoint_id"] == "dialogue_plan_subtractive_strip"


def test_by_trace_selects_fallback_for_visibility_hard_replacement():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "candidate", "candidate"),
        _entry(
            2,
            "fallback_selection_output",
            "fallback",
            "visibility.hard_replace",
            "candidate",
            "Safe narrative fallback line.",
        ),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["first_semantic_mutation_bucket"] == "fallback"


def test_by_trace_selects_final_emission_when_finalize_changes_text():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "Line one.", "Line one."),
        _entry(
            2,
            "final_emission_exit",
            "final_emission",
            "finalize.exit",
            "Line one.",
            "Line one. No appended stock.",
        ),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["first_semantic_mutation_bucket"] == "final_emission"
    assert first["first_semantic_mutation_checkpoint_id"] == "final_emission_exit"


def test_by_trace_marks_broken_checkpoint_continuity_unknown():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "alpha", "alpha"),
        _entry(
            2,
            CHECKPOINT_SANITIZER_OUTPUT,
            "sanitizer",
            "sanitizer.strip",
            "gamma",
            "delta",
        ),
    ]
    first = select_first_semantic_mutation(entries)
    assert first["trace_continuity"] is False
    assert first["first_semantic_mutation_bucket"] == "unknown"
    assert first["first_semantic_mutation_source"] == "broken_checkpoint_continuity"


def test_by_risk_scores_missing_first_source_and_later_unknown_changes():
    entries = [
        _entry(1, CHECKPOINT_POLICY_OUTPUT, "unknown", "", "a", "b"),
        _entry(2, "repair_layer", "unknown", "", "b", "c"),
        _entry(3, "repair_layer_2", "repair", "repair.x", "c", "d"),
    ]
    risk = compute_semantic_mutation_risk(entries)
    assert risk.changed_count == 3
    assert risk.unknown_count == 2
    assert risk.first_source_unknown is True
    assert risk.later_unattributed_changes == 1
    assert risk.risk_score == 70
    assert risk.risk_band == "high"


def test_by_risk_scores_attributed_first_source_low_risk():
    entries = [
        _entry(1, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "a", "b"),
        _entry(2, "repair_layer", "repair", "repair.x", "b", "c"),
    ]
    risk = compute_semantic_mutation_risk(entries)
    assert risk.first_source_unknown is False
    assert risk.cross_bucket_count == 2
    assert risk.risk_score == 10
    assert risk.risk_band == "low"


def test_by_projected_summary_round_trips_through_golden_observation():
    record = build_semantic_mutation_trace_record(
        [
            _entry(1, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "a", "b"),
        ]
    )
    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="by_projection_round_trip",
            gm_text="b",
            semantic_mutation_trace=record,
        )
    )
    assert turn["first_semantic_mutation_bucket"] == "sanitizer"
    assert turn["first_semantic_mutation_source"] == "sanitizer.strip"
    assert turn["semantic_mutation_changed_count"] == 1
    assert turn["semantic_mutation_risk_score"] == 0
    assert "first_semantic_mutation_bucket" not in protected_observation_field_paths()
    summary = project_semantic_mutation_summary(record)
    assert summary["semantic_mutation_changed_count"] == 1


def test_by_projection_defaults_when_trace_absent():
    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="by_projection_absent",
            gm_text="unchanged.",
        )
    )
    assert "first_semantic_mutation_bucket" not in turn
    assert "semantic_mutation_risk_score" not in turn


def test_by_build_record_preserves_ordering_and_counts():
    entries: list[SemanticMutationTraceEntry] = []
    append_semantic_mutation_entry(
        entries,
        checkpoint_id=CHECKPOINT_POLICY_OUTPUT,
        bucket="policy",
        source="policy.enforce",
        before_raw="one",
        after_raw="two",
    )
    append_semantic_mutation_entry(
        entries,
        checkpoint_id=CHECKPOINT_SANITIZER_OUTPUT,
        bucket="sanitizer",
        source="sanitizer.noop",
        before_raw="two",
        after_raw="two",
    )
    record = build_semantic_mutation_trace_record(entries)
    assert record["semantic_mutation_changed_count"] == 1
    assert record["semantic_mutation_trace_complete"] is True
    assert [row["sequence"] for row in record["semantic_mutation_trace"]] == [1, 2]


def test_by_sanitizer_integration_first_mutation(monkeypatch):
    collector = new_trace_collector()
    install_semantic_mutation_probes(monkeypatch, collector)
    raw = "I need a more concrete action or target to resolve that procedurally."
    output_sanitizer_module.sanitize_player_facing_output(
        raw,
        {"sanitizer_boundary_mode": "strip_only"},
    )
    changed = [e for e in collector.entries if e.normalized_changed]
    assert changed
    assert changed[0].bucket == "sanitizer"
    assert changed[0].checkpoint_id == CHECKPOINT_SANITIZER_OUTPUT


def test_by_policy_integration_first_mutation(monkeypatch):
    collector = new_trace_collector()
    install_semantic_mutation_probes(monkeypatch, collector)
    gm = {
        "player_facing_text": "Validator: unresolved question about the east gate.",
        "tags": [],
    }
    apply_response_policy_enforcement(
        gm,
        response_policy={"must_answer": True, "forbid_secret_leak": False, "diegetic_only": True},
        player_text="What happened at the east gate?",
        scene_envelope={"scene_id": "s1"},
        session={},
        world={},
        resolution={"kind": "question"},
    )
    changed = [e for e in collector.entries if e.normalized_changed]
    if changed:
        assert changed[0].bucket == "policy"


def test_by_probe_preserves_final_text_and_final_text_hash(local_rebind_strict_bundle, monkeypatch):
    session, world, sid, resolution, line = local_rebind_strict_bundle
    phase = SimpleNamespace(after_enforce=False)

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)

    out_baseline = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    baseline_text = str(out_baseline.get("player_facing_text") or "")
    baseline_hash = golden_text_hash(baseline_text)

    collector = new_trace_collector()
    cap2 = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap2)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_semantic_mutation_probes(monkeypatch, collector, phase=phase)

    out_probed = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    probed_text = str(out_probed.get("player_facing_text") or "")
    assert probed_text == baseline_text
    assert golden_text_hash(probed_text) == baseline_hash


@pytest.fixture
def local_rebind_strict_bundle(monkeypatch):
    return build_finalize_stack_fixture(
        monkeypatch,
        contract=locked_runner_contract(),
        strict_social_details=stub_strict_social_details,
    )


def test_by_repair_first_mutation_via_dialogue_strip(local_rebind_strict_bundle, monkeypatch):
    session, world, sid, resolution, line = local_rebind_strict_bundle
    phase = SimpleNamespace(after_enforce=False)
    collector = new_trace_collector()

    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_semantic_mutation_probes(monkeypatch, collector, phase=phase)

    apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    record = build_semantic_mutation_trace_record(collector.entries)
    changed = [e for e in collector.entries if e.normalized_changed]
    if not changed:
        pytest.skip("fixture produced no normalized mutation at probe granularity")
    first = select_first_semantic_mutation(collector.entries)
    assert first["first_semantic_mutation_bucket"] in {"repair", "fallback", "final_emission"}
    assert record["semantic_mutation_changed_count"] == len(changed)


def test_by_post_speaker_probe_and_semantic_probe_coexist(local_rebind_strict_bundle, monkeypatch):
    """Semantic probe must not alter text relative to post-speaker probe baseline."""
    session, world, sid, resolution, line = local_rebind_strict_bundle
    phase = SimpleNamespace(after_enforce=False)

    post_events = []
    cap = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_post_speaker_text_probes(monkeypatch, post_events, phase=phase)
    out_post = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    collector = new_trace_collector()
    cap2 = ShadowEnforceCapture()
    install_dual_run_enforce(monkeypatch, cap2)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_semantic_mutation_probes(monkeypatch, collector, phase=phase)
    out_sem = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert str(out_post.get("player_facing_text") or "") == str(out_sem.get("player_facing_text") or "")


def test_by_replay_final_text_checkpoint_continuity():
    collector = new_trace_collector()
    collector.track(
        checkpoint_id="final_emission_exit",
        bucket="final_emission",
        source="finalize.exit",
        before_raw="final line",
        after_raw="final line",
    )
    record_replay_final_text_checkpoint(
        collector,
        replay_final_text="final line",
        previous_text="final line",
    )
    record = build_semantic_mutation_trace_record(collector.entries)
    assert record["first_semantic_mutation_sequence"] is None
    replay_rows = [e for e in collector.entries if e.checkpoint_id == CHECKPOINT_REPLAY_FINAL_TEXT]
    assert len(replay_rows) == 1
    assert replay_rows[0].normalized_changed is False


def test_by_golden_observation_hash_preserved_with_trace(local_rebind_strict_bundle):
    session, world, sid, resolution, line = local_rebind_strict_bundle
    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    observed = observed_turn_from_gate_output(
        scenario_id="by_hash_preserve",
        gm_output=out,
        resolution=resolution,
    )
    record = build_semantic_mutation_trace_record(
        [
            _entry(
                1,
                "dialogue_plan_subtractive_strip",
                "repair",
                "repair.strip",
                line,
                str(out.get("player_facing_text") or ""),
            )
        ]
    )
    with_trace = project_turn_observation(
        minimal_turn_payload(
            scenario_id="by_hash_preserve",
            gm_text=str(out.get("player_facing_text") or ""),
            payload={"gm_output": out, "resolution": resolution},
            semantic_mutation_trace=record,
        )
    )
    assert with_trace["final_text"] == observed["final_text"]
    assert with_trace["final_text_hash"] == observed["final_text_hash"]


def test_by_sample_trace_and_risk_report_outputs():
    records = [
        build_semantic_mutation_trace_record(
            [
                _entry(1, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "a", "b"),
                _entry(2, "repair_layer", "repair", "repair.x", "b", "c"),
            ]
        ),
        build_semantic_mutation_trace_record(
            [
                _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "x", "y"),
            ]
        ),
        build_semantic_mutation_trace_record(
            [
                _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.noop", "same", "same"),
            ]
        ),
    ]
    sample = render_semantic_mutation_trace_sample(records[0])
    assert "first_semantic_mutation_bucket" in sample
    assert "sanitizer" in sample

    report = render_semantic_mutation_risk_report(records)
    assert "first-source coverage rate" in report
    agg = compute_first_source_attribution_rate(records)
    assert agg["mutated_turns"] == 2
    assert agg["attributable_first_mutations"] == 2
    assert agg["first_source_coverage_rate"] == 1.0


def test_by_attribution_rate_on_fixture_corpus():
    """Measure first-source coverage on representative synthetic BY1 fixtures."""
    corpus = [
        build_semantic_mutation_trace_record(
            [_entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [_entry(1, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [_entry(1, "fallback_selection_output", "fallback", "visibility.replace", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [_entry(1, "dialogue_plan_subtractive_strip", "repair", "repair.strip", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [_entry(1, "final_emission_exit", "final_emission", "finalize.exit", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [
                _entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "a", "b"),
                _entry(2, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.noop", "b", "b"),
            ]
        ),
        build_semantic_mutation_trace_record([]),
    ]
    agg = compute_first_source_attribution_rate(corpus)
    assert agg["total_turns"] == 7
    assert agg["mutated_turns"] == 6
    assert agg["first_source_coverage_rate"] == 1.0
    assert set(agg["bucket_frequencies"]) == {
        "policy",
        "sanitizer",
        "fallback",
        "repair",
        "final_emission",
    }
