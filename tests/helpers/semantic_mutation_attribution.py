"""BY1 — Semantic Mutation Trace Probe (tests only).

Ordered normalized before/after checkpoints across policy, sanitizer, fallback,
repair, final emission, and replay boundaries. Identifies the first semantic
text change without altering runtime behavior or emitted text.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal, Mapping, Sequence

import game.dialogue_social_plan as dialogue_social_plan
import game.final_emission_acceptance_quality as acceptance_quality
import game.final_emission_finalize as emission_finalize
import game.final_emission_gate as final_emission_gate
import game.final_emission_gate_context as final_emission_gate_context
import game.final_emission_generic_exit as generic_exit
import game.final_emission_repairs as emission_repairs
import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_terminal_pipeline as terminal_pipeline
import game.speaker_contract_enforcement as speaker_contract_enforcement
import game.final_emission_visibility_fallback as visibility_fallback
import game.interaction_continuity as interaction_continuity
import game.output_sanitizer as output_sanitizer
import game.response_policy_enforcement as response_policy_enforcement
from game.final_emission_text_formatting import _normalize_text

MutationBucket = Literal["policy", "sanitizer", "fallback", "repair", "final_emission", "unknown"]

CHECKPOINT_WRITER_RAW_CANDIDATE = "writer_raw_candidate"
CHECKPOINT_POLICY_OUTPUT = "policy_output"
CHECKPOINT_SANITIZER_OUTPUT = "sanitizer_output"
CHECKPOINT_FALLBACK_SELECTION_OUTPUT = "fallback_selection_output"
CHECKPOINT_FINAL_EMISSION_GATE_ENTRY = "final_emission_gate_entry"
CHECKPOINT_STRICT_SOCIAL_TRUNK_ENTRY = "strict_social_trunk_entry"
CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE = "normalized_social_candidate"
CHECKPOINT_SPEAKER_CONTRACT_ENFORCEMENT = "speaker_contract_enforcement"
CHECKPOINT_STRICT_SOCIAL_PRE_TERMINAL = "strict_social_pre_terminal_pipeline"
CHECKPOINT_FINAL_EMISSION_ENTRY = "final_emission_entry"
CHECKPOINT_FINAL_EMISSION_EXIT = "final_emission_exit"
CHECKPOINT_REPLAY_FINAL_TEXT = "replay_final_text"

STRICT_SOCIAL_COMPOSITION_CHECKPOINTS: tuple[str, ...] = (
    CHECKPOINT_FINAL_EMISSION_GATE_ENTRY,
    CHECKPOINT_STRICT_SOCIAL_TRUNK_ENTRY,
    CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE,
    CHECKPOINT_SPEAKER_CONTRACT_ENFORCEMENT,
    CHECKPOINT_STRICT_SOCIAL_PRE_TERMINAL,
)

_DETERMINISTIC_STRICT_SOCIAL_SOURCES: frozenset[str] = frozenset(
    {
        "normalized_social_candidate",
        "minimal_social_emergency_fallback",
        "strict_social_deterministic_fallback",
    }
)

PRE_SPEAKER_REPAIR_IDS: frozenset[str] = frozenset({"answer_exposition_plan_pre_speaker"})

REPAIR_LAYER_CHECKPOINTS: tuple[str, ...] = (
    "anti_railroading",
    "context_separation",
    "narration_purity",
    "answer_shape_primacy",
    "scene_state_anchor",
    "fast_fallback_neutral_composition",
    "dialogue_plan_subtractive_strip",
    "answer_exposition_plan_post_speaker",
    "visibility_enforcement",
    "interaction_continuity_step",
    "fallback_behavior",
    "referent_clarity_pre_finalize",
    "acceptance_quality_n4",
    "attach_interaction_continuity_validation",
    "finalize_emission_output",
)

_MAX_PRESERVED_PROBE_TEXT = 240


@dataclass(frozen=True)
class SemanticMutationTraceEntry:
    sequence: int
    checkpoint_id: str
    bucket: MutationBucket
    source: str
    owner: str | None = None
    mutation_kind: str | None = None
    input_field: str = "player_facing_text"
    output_field: str = "player_facing_text"
    before_normalized: str = ""
    after_normalized: str = ""
    before_hash: str = ""
    after_hash: str = ""
    normalized_changed: bool = False
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class SemanticMutationRisk:
    changed_count: int
    unknown_count: int
    cross_bucket_count: int
    risk_score: int
    risk_band: str
    first_source_unknown: bool = False
    later_unattributed_changes: int = 0


@dataclass
class _TraceCollector:
    entries: list[SemanticMutationTraceEntry] = field(default_factory=list)
    _sequence: int = 0

    def track(
        self,
        *,
        checkpoint_id: str,
        bucket: MutationBucket,
        source: str,
        before_raw: str,
        after_raw: str,
        owner: str | None = None,
        mutation_kind: str | None = None,
        input_field: str = "player_facing_text",
        output_field: str = "player_facing_text",
        evidence: dict[str, Any] | None = None,
    ) -> SemanticMutationTraceEntry:
        before_norm = normalize_mutation_text(before_raw)
        after_norm = normalize_mutation_text(after_raw)
        self._sequence += 1
        entry = SemanticMutationTraceEntry(
            sequence=self._sequence,
            checkpoint_id=checkpoint_id,
            bucket=bucket,
            source=source,
            owner=owner,
            mutation_kind=mutation_kind,
            input_field=input_field,
            output_field=output_field,
            before_normalized=before_norm,
            after_normalized=after_norm,
            before_hash=mutation_text_hash(before_norm),
            after_hash=mutation_text_hash(after_norm),
            normalized_changed=before_norm != after_norm,
            evidence=dict(evidence) if evidence else None,
        )
        self.entries.append(entry)
        return entry


def normalize_mutation_text(text: Any) -> str:
    """Normalize player-facing text for semantic mutation comparison."""
    return _normalize_text(str(text or ""))


def mutation_text_hash(text: Any) -> str:
    """Short deterministic hash for normalized mutation text."""
    normalized = normalize_mutation_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _maybe_preserve_probe_text(text: str) -> str | None:
    if len(text) <= _MAX_PRESERVED_PROBE_TEXT:
        return text
    return None


def append_semantic_mutation_entry(
    entries: list[SemanticMutationTraceEntry],
    *,
    checkpoint_id: str,
    bucket: MutationBucket,
    source: str,
    before_raw: str,
    after_raw: str,
    owner: str | None = None,
    mutation_kind: str | None = None,
    input_field: str = "player_facing_text",
    output_field: str = "player_facing_text",
    evidence: dict[str, Any] | None = None,
) -> SemanticMutationTraceEntry:
    """Append one ordered trace entry with the next sequence number."""
    collector = _TraceCollector(entries=list(entries))
    collector._sequence = len(entries)
    entry = collector.track(
        checkpoint_id=checkpoint_id,
        bucket=bucket,
        source=source,
        before_raw=before_raw,
        after_raw=after_raw,
        owner=owner,
        mutation_kind=mutation_kind,
        input_field=input_field,
        output_field=output_field,
        evidence=evidence,
    )
    entries.append(entry)
    return entry


def _previous_after_normalized(entries: Sequence[SemanticMutationTraceEntry]) -> str | None:
    if not entries:
        return None
    return entries[-1].after_normalized


def select_first_semantic_mutation(
    entries: Sequence[SemanticMutationTraceEntry],
) -> dict[str, Any]:
    """Select earliest normalized divergence with continuity rules."""
    prev_after: str | None = None
    trace_continuity = True

    for entry in entries:
        if prev_after is not None and entry.before_normalized != prev_after:
            trace_continuity = False
        if entry.normalized_changed:
            bucket: MutationBucket = entry.bucket
            source = entry.source
            owner = entry.owner
            mutation_kind = entry.mutation_kind
            if not trace_continuity:
                bucket = "unknown"
                source = "broken_checkpoint_continuity"
                owner = None
                mutation_kind = "continuity_break"
            elif bucket == "unknown" or not str(source or "").strip():
                bucket = "unknown"
            return {
                "first_semantic_mutation_sequence": entry.sequence,
                "first_semantic_mutation_checkpoint_id": entry.checkpoint_id,
                "first_semantic_mutation_bucket": bucket,
                "first_semantic_mutation_source": source,
                "first_semantic_mutation_owner": owner,
                "first_semantic_mutation_kind": mutation_kind,
                "first_semantic_mutation_before_hash": entry.before_hash,
                "first_semantic_mutation_after_hash": entry.after_hash,
                "trace_continuity": trace_continuity,
            }
        prev_after = entry.after_normalized

    return {
        "first_semantic_mutation_sequence": None,
        "first_semantic_mutation_checkpoint_id": None,
        "first_semantic_mutation_bucket": None,
        "first_semantic_mutation_source": None,
        "first_semantic_mutation_owner": None,
        "first_semantic_mutation_kind": None,
        "first_semantic_mutation_before_hash": None,
        "first_semantic_mutation_after_hash": None,
        "trace_continuity": trace_continuity,
    }


def compute_semantic_mutation_risk(
    entries: Sequence[SemanticMutationTraceEntry],
    *,
    first_mutation: Mapping[str, Any] | None = None,
) -> SemanticMutationRisk:
    """Transparent diagnostic score from discovery specification."""
    changed = [e for e in entries if e.normalized_changed]
    changed_count = len(changed)
    if changed_count == 0:
        return SemanticMutationRisk(
            changed_count=0,
            unknown_count=0,
            cross_bucket_count=0,
            risk_score=0,
            risk_band=_risk_band(0),
            first_source_unknown=False,
            later_unattributed_changes=0,
        )

    unknown_count = sum(1 for e in changed if e.bucket == "unknown" or not str(e.source or "").strip())

    buckets = {
        e.bucket
        for e in changed
        if e.bucket != "unknown" and str(e.source or "").strip()
    }
    cross_bucket_count = len(buckets)

    first = dict(first_mutation or select_first_semantic_mutation(entries))
    first_bucket = first.get("first_semantic_mutation_bucket")
    first_source = first.get("first_semantic_mutation_source")
    first_source_unknown = not (
        first_bucket
        and str(first_bucket) != "unknown"
        and str(first_source or "").strip()
    )

    first_seq = first.get("first_semantic_mutation_sequence")
    later_unattributed = 0
    if first_seq is not None:
        for entry in changed:
            if entry.sequence <= int(first_seq):
                continue
            if entry.bucket == "unknown" or not str(entry.source or "").strip():
                later_unattributed += 1

    risk_score = min(
        100,
        60 * int(first_source_unknown)
        + 10 * min(later_unattributed, 2)
        + 10 * min(max(cross_bucket_count - 1, 0), 2),
    )
    return SemanticMutationRisk(
        changed_count=changed_count,
        unknown_count=unknown_count,
        cross_bucket_count=cross_bucket_count,
        risk_score=risk_score,
        risk_band=_risk_band(risk_score),
        first_source_unknown=first_source_unknown,
        later_unattributed_changes=later_unattributed,
    )


def _risk_band(score: int) -> str:
    if score <= 19:
        return "low"
    if score <= 39:
        return "guarded"
    if score <= 69:
        return "elevated"
    return "high"


def build_semantic_mutation_trace_record(
    entries: Sequence[SemanticMutationTraceEntry],
    *,
    include_bounded_text: bool = False,
) -> dict[str, Any]:
    """Assemble full diagnostic record for replay projection and reports."""
    first = select_first_semantic_mutation(entries)
    risk = compute_semantic_mutation_risk(entries, first_mutation=first)
    trace_rows: list[dict[str, Any]] = []
    for entry in entries:
        row = asdict(entry)
        if not include_bounded_text:
            row.pop("before_normalized", None)
            row.pop("after_normalized", None)
        else:
            row["before_normalized"] = _maybe_preserve_probe_text(entry.before_normalized)
            row["after_normalized"] = _maybe_preserve_probe_text(entry.after_normalized)
        trace_rows.append(row)

    return {
        "semantic_mutation_trace": trace_rows,
        "semantic_mutation_trace_complete": bool(entries),
        **first,
        "semantic_mutation_changed_count": risk.changed_count,
        "semantic_mutation_cross_bucket_count": risk.cross_bucket_count,
        "semantic_mutation_unknown_count": risk.unknown_count,
        "semantic_mutation_risk_score": risk.risk_score,
        "semantic_mutation_risk_band": risk.risk_band,
    }


def record_replay_final_text_checkpoint(
    collector: _TraceCollector,
    *,
    replay_final_text: str,
    previous_text: str,
) -> SemanticMutationTraceEntry:
    """Record replay projection final text against prior emission output."""
    return collector.track(
        checkpoint_id=CHECKPOINT_REPLAY_FINAL_TEXT,
        bucket="final_emission",
        source="golden_replay_projection.final_text",
        before_raw=previous_text,
        after_raw=replay_final_text,
        owner="tests.helpers.golden_replay_projection",
        mutation_kind="replay_projection",
    )


def install_semantic_mutation_probes(
    monkeypatch: Any,
    collector: _TraceCollector,
    *,
    phase: Any | None = None,
) -> None:
    """Install ordered semantic mutation wrappers following post-speaker probe pattern."""

    def wrap_policy(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(gm: dict[str, Any], **kwargs: Any) -> Any:
            tin = str((gm or {}).get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_WRITER_RAW_CANDIDATE,
                bucket="unknown",
                source="game.api raw candidate selection",
                before_raw=tin,
                after_raw=tin,
                owner="game.api",
                mutation_kind="raw_candidate_snapshot",
            )
            result = orig(gm, **kwargs)
            out = result if isinstance(result, dict) else gm
            tout = str(out.get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_POLICY_OUTPUT,
                bucket="policy",
                source="game.response_policy_enforcement.apply_response_policy_enforcement",
                before_raw=tin,
                after_raw=tout,
                owner="game.response_policy_enforcement",
            )
            return result

        return w

    def wrap_sanitizer(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, context: dict[str, Any] | None = None) -> str:
            tin = str(text or "")
            result = orig(text, context)
            tout = str(result or "")
            evidence: dict[str, Any] | None = None
            ctx = context if isinstance(context, dict) else {}
            if ctx.get("sanitizer_empty_fallback_used"):
                evidence = {"fallback_subsource": "sanitizer_empty_fallback"}
            collector.track(
                checkpoint_id=CHECKPOINT_SANITIZER_OUTPUT,
                bucket="sanitizer",
                source="game.output_sanitizer.sanitize_player_facing_output",
                before_raw=tin,
                after_raw=tout,
                owner="game.output_sanitizer",
                evidence=evidence,
            )
            return result

        return w

    def wrap_generic_replace(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: dict[str, Any], **kwargs: Any) -> Any:
            tin = str(out.get("player_facing_text") or "")
            result = orig(out, **kwargs)
            base = result if isinstance(result, dict) else out
            tout = str(base.get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_FALLBACK_SELECTION_OUTPUT,
                bucket="fallback",
                source="game.final_emission_generic_exit.run_generic_replace_exit",
                before_raw=tin,
                after_raw=tout,
                owner="game.final_emission_generic_exit",
                mutation_kind="sealed_replace",
            )
            return result

        return w

    def wrap_visibility_fallback(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: dict[str, Any], **kwargs: Any) -> Any:
            tin = str(out.get("player_facing_text") or "")
            result = orig(out, **kwargs)
            base = result if isinstance(result, dict) else out
            tout = str(base.get("player_facing_text") or "")
            bucket: MutationBucket = "fallback" if normalize_mutation_text(tin) != normalize_mutation_text(tout) else "repair"
            collector.track(
                checkpoint_id=CHECKPOINT_FALLBACK_SELECTION_OUTPUT
                if bucket == "fallback"
                else "visibility_enforcement",
                bucket=bucket,
                source="game.final_emission_visibility_fallback.apply_visibility_enforcement",
                before_raw=tin,
                after_raw=tout,
                owner="game.final_emission_visibility_fallback",
            )
            return result

        return w

    def wrap_tuple_repair(layer_id: str, orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            tin = str(text or "")
            out = orig(text, *args, **kwargs)
            if isinstance(out, tuple) and out:
                tout = str(out[0] or "")
            else:
                tout = tin
            collector.track(
                checkpoint_id=layer_id,
                bucket="repair",
                source=f"game.final_emission_repairs.{layer_id}",
                before_raw=tin,
                after_raw=tout,
                owner=_repair_owner_for_layer(layer_id),
            )
            return out

        return w

    def wrap_answer_exposition(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            if phase is None:
                lid = "answer_exposition_plan"
            elif not getattr(phase, "after_enforce", False):
                lid = "answer_exposition_plan_pre_speaker"
            else:
                lid = "answer_exposition_plan_post_speaker"
            tin = str(text or "")
            out = orig(text, *args, **kwargs)
            if isinstance(out, tuple) and out:
                tout = str(out[0] or "")
            else:
                tout = tin
            bucket: MutationBucket = "repair"
            if lid in PRE_SPEAKER_REPAIR_IDS:
                bucket = "repair"
            collector.track(
                checkpoint_id=lid,
                bucket=bucket,
                source="game.final_emission_repairs._apply_answer_exposition_plan_layer",
                before_raw=tin,
                after_raw=tout,
                owner="game.final_emission_repairs",
            )
            return out

        return w

    def wrap_out_mutate_repair(layer_id: str, orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(*args: Any, **kwargs: Any) -> Any:
            out = args[0] if args else kwargs.get("out")
            if not isinstance(out, dict):
                return orig(*args, **kwargs)
            tin = str(out.get("player_facing_text") or "")
            res = orig(*args, **kwargs)
            tout = str(out.get("player_facing_text") or "")
            bucket: MutationBucket = "repair"
            mutation_kind: str | None = None
            if layer_id == "acceptance_quality_n4":
                meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
                if meta.get("acceptance_quality_n4_fallback_used"):
                    bucket = "fallback"
                    mutation_kind = "n4_fallback"
            collector.track(
                checkpoint_id=layer_id,
                bucket=bucket,
                source=f"game.final_emission.{layer_id}",
                before_raw=tin,
                after_raw=tout,
                owner=_repair_owner_for_layer(layer_id),
                mutation_kind=mutation_kind,
            )
            return res

        return w

    def wrap_ic_step(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: Any, *, text: str, **kwargs: Any) -> Any:
            tin = str(text or "")
            result = orig(out, text=text, **kwargs)
            if isinstance(result, tuple) and result:
                tout = str(result[0] or "")
            else:
                tout = tin
            collector.track(
                checkpoint_id="interaction_continuity_step",
                bucket="repair",
                source="game.interaction_continuity.apply_interaction_continuity_emission_step",
                before_raw=tin,
                after_raw=tout,
                owner="game.interaction_continuity",
            )
            return result

        return w

    def wrap_finalize(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: dict[str, Any], **kwargs: Any) -> Any:
            if not isinstance(out, dict):
                return orig(out, **kwargs)
            tin = str(out.get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_FINAL_EMISSION_ENTRY,
                bucket="final_emission",
                source="game.final_emission_finalize.finalize_emission_output.entry",
                before_raw=tin,
                after_raw=tin,
                owner="game.final_emission_finalize",
                mutation_kind="entry",
            )
            res = orig(out, **kwargs)
            base = res if isinstance(res, dict) else out
            tout = str(base.get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_FINAL_EMISSION_EXIT,
                bucket="final_emission",
                source="game.final_emission_finalize.finalize_emission_output",
                before_raw=tin,
                after_raw=tout,
                owner="game.final_emission_finalize",
                mutation_kind="exit",
            )
            return res

        return w

    def wrap_gate_execution_context(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(gm_output: dict[str, Any], **kwargs: Any) -> Any:
            ctx = orig(gm_output, **kwargs)
            pre_gate = str(getattr(ctx, "pre_gate_text", "") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_FINAL_EMISSION_GATE_ENTRY,
                bucket="final_emission",
                source="game.final_emission_gate_context.initialize_gate_execution_context",
                before_raw=pre_gate,
                after_raw=pre_gate,
                owner="game.final_emission_gate",
                mutation_kind="gate_entry",
            )
            return ctx

        return w

    def wrap_strict_social_trunk(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(*args: Any, **kwargs: Any) -> Any:
            return orig(*args, **kwargs)

        return w

    def wrap_dialogue_plan_strict(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            tin = str(text or "")
            result = orig(text, *args, **kwargs)
            if isinstance(result, tuple) and result:
                tout = str(result[0] or "")
            else:
                tout = tin
            collector.track(
                checkpoint_id=CHECKPOINT_STRICT_SOCIAL_TRUNK_ENTRY,
                bucket="final_emission",
                source="game.dialogue_social_plan.enforce_dialogue_plan_invariant_on_strict_social",
                before_raw=tin,
                after_raw=tout,
                owner="game.dialogue_social_plan",
                mutation_kind="trunk_entry",
            )
            return result

        return w

    def wrap_build_strict_social(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(candidate_text: str, *args: Any, **kwargs: Any) -> Any:
            tin = str(candidate_text or "")
            result = orig(candidate_text, *args, **kwargs)
            details: dict[str, Any] = {}
            if isinstance(result, tuple) and result:
                tout = str(result[0] or "")
                if len(result) > 1 and isinstance(result[1], dict):
                    details = dict(result[1])
            else:
                tout = tin
            bucket: MutationBucket = "unknown"
            mutation_kind: str | None = None
            if normalize_mutation_text(tin) != normalize_mutation_text(tout):
                fe = str(details.get("final_emitted_source") or "")
                if details.get("used_internal_fallback") or fe in _DETERMINISTIC_STRICT_SOCIAL_SOURCES:
                    bucket = "fallback"
                    mutation_kind = fe or "deterministic_strict_social_replacement"
                else:
                    bucket = "repair"
                    mutation_kind = fe or "strict_social_composition"
            collector.track(
                checkpoint_id=CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE,
                bucket=bucket,
                source="game.social_exchange_emission.build_final_strict_social_response",
                before_raw=tin,
                after_raw=tout,
                owner="game.social_exchange_emission",
                mutation_kind=mutation_kind,
                evidence={"final_emitted_source": details.get("final_emitted_source")},
            )
            return result

        return w

    def wrap_speaker_contract(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            tin = str(text or "")
            result = orig(text, *args, **kwargs)
            if isinstance(result, tuple) and result:
                tout = str(result[0] or "")
                payload = result[1] if len(result) > 1 and isinstance(result[1], dict) else {}
            else:
                tout = tin
                payload = {}
            collector.track(
                checkpoint_id=CHECKPOINT_SPEAKER_CONTRACT_ENFORCEMENT,
                bucket="repair",
                source="game.speaker_contract_enforcement.enforce_emitted_speaker_with_contract",
                before_raw=tin,
                after_raw=tout,
                owner="game.speaker_contract_enforcement",
                mutation_kind=str(payload.get("final_reason_code") or "speaker_contract_enforcement"),
                evidence={"final_reason_code": payload.get("final_reason_code")},
            )
            return result

        return w

    def wrap_terminal_pipeline(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: dict[str, Any], **kwargs: Any) -> Any:
            tin = str(out.get("player_facing_text") or "")
            collector.track(
                checkpoint_id=CHECKPOINT_STRICT_SOCIAL_PRE_TERMINAL,
                bucket="final_emission",
                source="game.final_emission_terminal_pipeline.run_gate_terminal_enforcement_pipeline.entry",
                before_raw=tin,
                after_raw=tin,
                owner="game.final_emission_terminal_pipeline",
                mutation_kind="terminal_pipeline_entry",
            )
            return orig(out, **kwargs)

        return w

    if phase is not None:

        def wrap_strip(orig: Callable[..., Any]) -> Callable[..., Any]:
            def w(t: str) -> str:
                tin = str(t or "")
                r = orig(t)
                tout = str(r or "")
                if getattr(phase, "after_enforce", False):
                    collector.track(
                        checkpoint_id="dialogue_plan_subtractive_strip",
                        bucket="repair",
                        source="game.dialogue_social_plan.strip_dialogue_from_text",
                        before_raw=tin,
                        after_raw=tout,
                        owner="game.dialogue_social_plan",
                    )
                return r

            return w

        monkeypatch.setattr(
            dialogue_social_plan,
            "strip_dialogue_from_text",
            wrap_strip(dialogue_social_plan.strip_dialogue_from_text),
        )

    monkeypatch.setattr(
        response_policy_enforcement,
        "apply_response_policy_enforcement",
        wrap_policy(response_policy_enforcement.apply_response_policy_enforcement),
    )
    monkeypatch.setattr(
        output_sanitizer,
        "sanitize_player_facing_output",
        wrap_sanitizer(output_sanitizer.sanitize_player_facing_output),
    )
    monkeypatch.setattr(
        generic_exit,
        "run_generic_replace_exit",
        wrap_generic_replace(generic_exit.run_generic_replace_exit),
    )
    monkeypatch.setattr(
        visibility_fallback,
        "apply_visibility_enforcement",
        wrap_visibility_fallback(visibility_fallback.apply_visibility_enforcement),
    )

    monkeypatch.setattr(
        strict_social_stack,
        "apply_anti_railroading_layer",
        wrap_tuple_repair("anti_railroading", strict_social_stack.apply_anti_railroading_layer),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_context_separation_layer",
        wrap_tuple_repair("context_separation", strict_social_stack.apply_context_separation_layer),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_player_facing_narration_purity_layer",
        wrap_tuple_repair("narration_purity", strict_social_stack.apply_player_facing_narration_purity_layer),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_answer_shape_primacy_layer",
        wrap_tuple_repair("answer_shape_primacy", strict_social_stack.apply_answer_shape_primacy_layer),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_scene_state_anchor_layer",
        wrap_tuple_repair("scene_state_anchor", strict_social_stack.apply_scene_state_anchor_layer),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "apply_fast_fallback_neutral_composition_layer",
        wrap_tuple_repair(
            "fast_fallback_neutral_composition",
            strict_social_stack.apply_fast_fallback_neutral_composition_layer,
        ),
    )
    monkeypatch.setattr(
        emission_repairs,
        "_apply_answer_exposition_plan_layer",
        wrap_answer_exposition(emission_repairs._apply_answer_exposition_plan_layer),
    )
    monkeypatch.setattr(
        interaction_continuity,
        "apply_interaction_continuity_emission_step",
        wrap_ic_step(interaction_continuity.apply_interaction_continuity_emission_step),
    )
    monkeypatch.setattr(
        emission_repairs,
        "_apply_fallback_behavior_layer",
        wrap_tuple_repair("fallback_behavior", emission_repairs._apply_fallback_behavior_layer),
    )
    monkeypatch.setattr(
        terminal_pipeline,
        "_apply_referent_clarity_pre_finalize",
        wrap_out_mutate_repair(
            "referent_clarity_pre_finalize",
            terminal_pipeline._apply_referent_clarity_pre_finalize,
        ),
    )
    monkeypatch.setattr(
        acceptance_quality,
        "apply_acceptance_quality_n4_floor_seam",
        wrap_out_mutate_repair(
            "acceptance_quality_n4",
            acceptance_quality.apply_acceptance_quality_n4_floor_seam,
        ),
    )
    monkeypatch.setattr(
        interaction_continuity,
        "attach_interaction_continuity_validation",
        wrap_out_mutate_repair(
            "attach_interaction_continuity_validation",
            interaction_continuity.attach_interaction_continuity_validation,
        ),
    )
    monkeypatch.setattr(
        emission_finalize,
        "finalize_emission_output",
        wrap_finalize(emission_finalize.finalize_emission_output),
    )
    monkeypatch.setattr(
        final_emission_gate_context,
        "initialize_gate_execution_context",
        wrap_gate_execution_context(final_emission_gate_context.initialize_gate_execution_context),
    )
    monkeypatch.setattr(
        final_emission_gate,
        "initialize_gate_execution_context",
        wrap_gate_execution_context(final_emission_gate.initialize_gate_execution_context),
    )
    monkeypatch.setattr(
        dialogue_social_plan,
        "enforce_dialogue_plan_invariant_on_strict_social",
        wrap_dialogue_plan_strict(dialogue_social_plan.enforce_dialogue_plan_invariant_on_strict_social),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "enforce_dialogue_plan_invariant_on_strict_social",
        wrap_dialogue_plan_strict(strict_social_stack.enforce_dialogue_plan_invariant_on_strict_social),
    )
    monkeypatch.setattr(
        final_emission_gate,
        "run_strict_social_composition_trunk",
        wrap_strict_social_trunk(final_emission_gate.run_strict_social_composition_trunk),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "run_strict_social_composition_trunk",
        wrap_strict_social_trunk(strict_social_stack.run_strict_social_composition_trunk),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "build_final_strict_social_response",
        wrap_build_strict_social(strict_social_stack.build_final_strict_social_response),
    )
    monkeypatch.setattr(
        strict_social_stack,
        "enforce_emitted_speaker_with_contract",
        wrap_speaker_contract(strict_social_stack.enforce_emitted_speaker_with_contract),
    )
    monkeypatch.setattr(
        speaker_contract_enforcement,
        "enforce_emitted_speaker_with_contract",
        wrap_speaker_contract(speaker_contract_enforcement.enforce_emitted_speaker_with_contract),
    )
    monkeypatch.setattr(
        terminal_pipeline,
        "run_gate_terminal_enforcement_pipeline",
        wrap_terminal_pipeline(terminal_pipeline.run_gate_terminal_enforcement_pipeline),
    )

    # Replay/API paths bind callables at import time; patch consumer modules too.
    import game.api as api_module
    import game.api_turn_support as api_turn_support
    import game.gm as gm_module

    monkeypatch.setattr(
        api_module,
        "apply_response_policy_enforcement",
        wrap_policy(api_module.apply_response_policy_enforcement),
    )
    monkeypatch.setattr(
        gm_module,
        "apply_response_policy_enforcement",
        wrap_policy(gm_module.apply_response_policy_enforcement),
    )
    monkeypatch.setattr(
        api_turn_support,
        "sanitize_player_facing_output",
        wrap_sanitizer(api_turn_support.sanitize_player_facing_output),
    )


def _repair_owner_for_layer(layer_id: str) -> str:
    owners = {
        "anti_railroading": "game.final_emission_strict_social_stack",
        "context_separation": "game.final_emission_strict_social_stack",
        "narration_purity": "game.final_emission_strict_social_stack",
        "answer_shape_primacy": "game.final_emission_strict_social_stack",
        "scene_state_anchor": "game.final_emission_strict_social_stack",
        "fast_fallback_neutral_composition": "game.final_emission_strict_social_stack",
        "dialogue_plan_subtractive_strip": "game.dialogue_social_plan",
        "answer_exposition_plan_post_speaker": "game.final_emission_repairs",
        "visibility_enforcement": "game.final_emission_visibility_fallback",
        "interaction_continuity_step": "game.interaction_continuity",
        "fallback_behavior": "game.final_emission_repairs",
        "referent_clarity_pre_finalize": "game.final_emission_terminal_pipeline",
        "acceptance_quality_n4": "game.final_emission_acceptance_quality",
        "attach_interaction_continuity_validation": "game.interaction_continuity",
        "finalize_emission_output": "game.final_emission_finalize",
    }
    return owners.get(layer_id, "game.final_emission_repairs")


def new_trace_collector() -> _TraceCollector:
    return _TraceCollector()


def reset_trace_collector(collector: _TraceCollector) -> None:
    """Clear per-turn probe rows while keeping installed wrappers."""
    collector.entries.clear()
    collector._sequence = 0


def emission_text_before_replay_checkpoint(
    entries: Sequence[SemanticMutationTraceEntry],
) -> str:
    """Best-effort emission text immediately before replay projection."""
    for entry in reversed(entries):
        if entry.checkpoint_id == CHECKPOINT_FINAL_EMISSION_EXIT:
            return entry.after_normalized
    for entry in reversed(entries):
        if entry.normalized_changed:
            return entry.after_normalized
    if entries:
        return entries[-1].after_normalized
    return ""


def finalize_semantic_mutation_trace_for_turn(
    collector: _TraceCollector,
    *,
    replay_final_text: str,
) -> dict[str, Any]:
    """Append replay checkpoint and build the BY1 diagnostic record."""
    previous_text = emission_text_before_replay_checkpoint(collector.entries)
    record_replay_final_text_checkpoint(
        collector,
        replay_final_text=replay_final_text,
        previous_text=previous_text,
    )
    return build_semantic_mutation_trace_record(collector.entries)


def compute_first_source_attribution_rate(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate first-source coverage across turn trace records."""
    total = len(records)
    mutated = 0
    attributable = 0
    bucket_counts: dict[str, int] = {}
    for record in records:
        if int(record.get("semantic_mutation_changed_count") or 0) <= 0:
            continue
        mutated += 1
        bucket = record.get("first_semantic_mutation_bucket")
        source = record.get("first_semantic_mutation_source")
        if bucket and str(bucket) != "unknown" and str(source or "").strip():
            attributable += 1
            bucket_counts[str(bucket)] = bucket_counts.get(str(bucket), 0) + 1
    rate = (attributable / mutated) if mutated else 1.0
    return {
        "total_turns": total,
        "mutated_turns": mutated,
        "attributable_first_mutations": attributable,
        "first_source_coverage_rate": round(rate, 4),
        "bucket_frequencies": dict(sorted(bucket_counts.items())),
    }


def render_semantic_mutation_trace_sample(record: Mapping[str, Any]) -> str:
    """JSON sample for BY1 trace deliverable (summary-only, bounded text)."""
    payload = {
        "first_semantic_mutation_bucket": record.get("first_semantic_mutation_bucket"),
        "first_semantic_mutation_source": record.get("first_semantic_mutation_source"),
        "first_semantic_mutation_sequence": record.get("first_semantic_mutation_sequence"),
        "semantic_mutation_changed_count": record.get("semantic_mutation_changed_count"),
        "trace": record.get("semantic_mutation_trace"),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_semantic_mutation_risk_report(records: Sequence[Mapping[str, Any]]) -> str:
    """Markdown risk report sample for BY1 deliverable."""
    agg = compute_first_source_attribution_rate(records)
    lines = [
        "# Semantic Mutation Risk Report (BY1 sample)",
        "",
        f"- total turns: {agg['total_turns']}",
        f"- mutated turns: {agg['mutated_turns']}",
        f"- attributable first mutations: {agg['attributable_first_mutations']}",
        f"- first-source coverage rate: {agg['first_source_coverage_rate']:.2%}",
        "",
        "## Per-turn risk",
        "",
        "| sequence | bucket | source | changed | risk | band |",
        "|---|---|---|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            "| {seq} | {bucket} | {source} | {changed} | {risk} | {band} |".format(
                seq=record.get("first_semantic_mutation_sequence") or "-",
                bucket=record.get("first_semantic_mutation_bucket") or "-",
                source=record.get("first_semantic_mutation_source") or "-",
                changed=record.get("semantic_mutation_changed_count") or 0,
                risk=record.get("semantic_mutation_risk_score") or 0,
                band=record.get("semantic_mutation_risk_band") or "-",
            )
        )
    if agg["bucket_frequencies"]:
        lines.extend(["", "## Bucket frequencies", ""])
        for bucket, count in agg["bucket_frequencies"].items():
            lines.append(f"- {bucket}: {count}")
    return "\n".join(lines) + "\n"
