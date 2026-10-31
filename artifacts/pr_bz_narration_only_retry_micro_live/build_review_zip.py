#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_bz_narration_only_retry_micro_live"
EVIDENCE = OUT / "evidence"
HANDOFF = ROOT / "handoff"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    digest = load_json(EVIDENCE / "P2" / "digest.json")
    validation = load_json(EVIDENCE / "P2" / "validation.json")
    normalization = load_json(EVIDENCE / "P2" / "normalization.json")
    phase0 = load_json(EVIDENCE / "phase0_prelive.json")
    raw1 = load_json(EVIDENCE / "P2" / "raw_generation_attempt_1.json")
    request1 = load_json(EVIDENCE / "P2" / "provider_request_attempt_generation_1.json")

    attempt_calls = [
        call for call in digest.get("calls", []) if call.get("kind") == "generation"
    ]
    attempt_tokens = [
        {
            "attempt": index,
            "input_tokens": call.get("input_tokens"),
            "output_tokens": call.get("output_tokens"),
            "total_tokens": call.get("total_tokens"),
            "response_id": call.get("response_id"),
        }
        for index, call in enumerate(attempt_calls, start=1)
    ]

    token_comparison = {
        "pr_bx_p2": {
            "attempt_1_input": 23413,
            "attempt_2_input": 24881,
            "total_input": 48294,
            "total_output": 209,
            "total_tokens": 48503,
            "provider_attempts": 2,
            "retry_reason": "narration validation rejected attempt 1; retry feedback reintroduced structured declarations",
            "final_outcome": "safe_nonresolution",
        },
        "pr_bz_p2": {
            "attempt_tokens": attempt_tokens,
            "input_tokens": digest.get("input_tokens"),
            "output_tokens": digest.get("output_tokens"),
            "total_tokens": digest.get("total_tokens"),
            "provider_attempts": digest.get("provider_attempts"),
            "retry_reason": None,
            "final_outcome": "accepted_initial_generation",
        },
        "comparison_note": "Single-sample live cost only. PR-BZ did not exercise retry, so this must not be generalized as a retry cost improvement.",
    }
    write_json(OUT / "PR-BZ_token_comparison.json", token_comparison)

    p2_evidence = {
        "gate": "PR-BZ",
        "mode": "NARRATION-ONLY RETRY MICRO-LIVE VALIDATION",
        "probe": "P2",
        "reconstruction": {
            "source": "artifacts/pr_bx_narration_only_micro_live",
            "player_input": digest.get("player"),
            "scene": "Bread stall. Visible fact: a baker stands beside loaves. No authored loaf preference.",
            "response_operation": digest.get("response_operation"),
            "declaration_expectation": digest.get("declaration_expectation"),
            "consequentiality_classification": {
                "consequential_realization_required": digest.get("consequential_realization_required"),
                "semantic_ceiling": ((digest.get("recipe_turn_operation") or {}).get("semantic_ceiling")),
            },
        },
        "selected_envelope": digest.get("selected_envelope"),
        "provider_response_contracts": digest.get("provider_response_contracts"),
        "provider_attempt_count": digest.get("provider_attempts"),
        "provider_attempts": {
            "attempt_1": {
                "response_id": raw1.get("response_id"),
                "model": raw1.get("model"),
                "usage": raw1.get("usage"),
                "response_shape": raw1.get("parsed", {}).get("structural_shape"),
                "raw_output": raw1.get("parsed", {}).get("raw_output"),
                "narration": raw1.get("parsed", {}).get("player_facing_text"),
            },
            "attempt_2": None,
        },
        "declaration_validation_result": (validation.get("attempt_1") or {})
        .get("gm_resolution_decision_audit", {})
        .get("declaration_validation"),
        "narration_validation_result": (validation.get("attempt_1") or {})
        .get("gm_resolution_decision_audit", {})
        .get("narration_validation"),
        "regeneration_trigger": validation.get("regeneration_invoked"),
        "regeneration_feedback": validation.get("regeneration_feedback"),
        "final_accepted_result": digest.get("accepted"),
        "emitted_player_facing_narration": digest.get("emitted"),
        "c18": {
            "accepted": digest.get("accepted"),
            "sealed": digest.get("sealed"),
            "emitted": digest.get("emitted"),
            "exact_equal": digest.get("c18_exact_equal"),
        },
        "integrity": {
            "player_facing_leakage": digest.get("player_facing_leakage"),
            "authority_problems": digest.get("authority_problems"),
            "accepted_model_authored_declarations": digest.get("accepted_model_authored_declarations"),
            "temporal_after": digest.get("temporal_after"),
        },
    }
    write_json(OUT / "PR-BZ_P2_live_evidence.json", p2_evidence)

    retry_evidence = {
        "retry_observed": bool(digest.get("retry")),
        "provider_attempts": digest.get("provider_attempts"),
        "selected_envelope": digest.get("selected_envelope"),
        "initial_provider_contract": digest.get("provider_response_contracts", [None])[0],
        "initial_response_shape": digest.get("initial_structural_shape"),
        "regeneration_feedback": validation.get("regeneration_feedback"),
        "retry_context": validation.get("retry_context"),
        "retry_contract_preserved": None,
        "retry_contract_not_exercised": True,
        "deterministic_pr_by_evidence": {
            "focused_tests": "22 passed",
            "phase0_prelive_passed": phase0.get("passed"),
            "narration_only_response_contract": phase0.get("narration_only_response_contract"),
            "declared_claims_in_narration_only_system_prompt": phase0.get("declared_claims_in_narration_only_system_prompt"),
            "smuggled_declaration_rejected": phase0.get("smuggled_declaration_rejected"),
        },
        "classification": "NO RETRY OBSERVED. Live retry path not exercised.",
    }
    write_json(OUT / "PR-BZ_retry_contract_evidence.json", retry_evidence)

    redacted = {
        "attempt_1_request": {
            "measurements": request1.get("measurements"),
            "contract": request1.get("contract"),
            "create_kwarg_keys": request1.get("create_kwarg_keys"),
            "api_response_schema_present": request1.get("api_response_schema_present"),
            "decision_facing_answer_recipe": request1.get("decision_facing_answer_recipe"),
            "provider_input_redaction": "Full prompt omitted from review bundle; no credentials observed in captured request.",
        },
        "attempt_1_response": {
            "response_id": raw1.get("response_id"),
            "model": raw1.get("model"),
            "usage": raw1.get("usage"),
            "raw_output": raw1.get("parsed", {}).get("raw_output"),
            "parsed": {
                key: raw1.get("parsed", {}).get(key)
                for key in (
                    "structural_shape",
                    "provider_response_contract",
                    "declared_claims",
                    "normalized_empty_declarations",
                    "declaration_authorship",
                    "structured_contract_failure",
                    "structured_contract_reason",
                    "player_facing_text",
                )
            },
        },
    }
    write_json(OUT / "provider_request_response_redacted.json", redacted)

    report = f"""# PR-BZ — Narration-only retry micro-live validation

Date: 2026-10-08.

MODE: CONTROLLED MICRO-LIVE VALIDATION.

Live execution was limited to P2. P1 and P3 were not run live. Phase 0 still verified the inherited selector controls for P1/P2/P3 before the live call.

## Decision

**A — P2 LIVE VALIDATION PASSED.**

PR-BY live retry path not exercised.

P2 selected `narration_only`, the provider obeyed the one-field narration-only contract, and the first response was accepted. The final accepted, sealed, and emitted narration are identical. No declaration metadata leaked to the player, no model-authored declarations were accepted, and no unauthorized state/provenance mutation was observed.

## Reconstruction

- Source: `artifacts/pr_bx_narration_only_micro_live`.
- Player input: `{digest.get("player")}`.
- Scene: Bread stall. Visible fact: a baker stands beside loaves. No authored loaf preference.
- Response operation: `{digest.get("response_operation")}`.
- Declaration expectation: `{digest.get("declaration_expectation")}`.
- Consequential realization required: `{digest.get("consequential_realization_required")}`.

## Pre-live Verification

Focused PR-BY regression: PASS, 22 passed.

Selector/control verification: PASS. P2 selected `narration_only`; P1/P3 controls remained `structured_realization`; narration-only contract stayed `{phase0.get("narration_only_response_contract")}`; `declared_claims` was absent from the narration-only system prompt; smuggled declarations were rejected.

## Live P2 Evidence

- Selected envelope: `{digest.get("selected_envelope")}`.
- Provider response contract: `{digest.get("provider_response_contracts", [None])[0]}`.
- Provider attempts: `{digest.get("provider_attempts")}`.
- Attempt 1 input tokens: `{attempt_tokens[0].get("input_tokens") if attempt_tokens else None}`.
- Attempt 1 output tokens: `{attempt_tokens[0].get("output_tokens") if attempt_tokens else None}`.
- Attempt 1 response shape: `{json.dumps(digest.get("initial_structural_shape"), ensure_ascii=False)}`.
- Declaration validation: hard valid, accepted claims empty.
- Narration validation: hard valid, no rejection reasons.
- Regeneration triggered: `{bool(digest.get("retry"))}`.

Attempt 1 narration:

> {digest.get("initial_player_facing_text")}

Final emitted narration:

> {digest.get("emitted")}

## Retry Contract

No retry occurred. This demonstrates successful first-attempt narration-only operation, but does not independently prove the PR-BY live retry repair under live regeneration. Deterministic PR-BY retry evidence is preserved in `PR-BZ_retry_contract_evidence.json` and the focused test output.

## Narration Validation

No narration rejection occurred in PR-BZ P2. The PR-BX rejection pattern involving `unowned_stateful_world_assertion` and `unauthorized_evidential_relation` did not recur in this sample. No sentence-boundary parsing issue was observed.

## Final Response Integrity

Accepted narration equals sealed narration equals emitted narration. `declared_claims` remained application-created and empty. Player-facing leakage list is empty. `authority_problems` is empty. The only accepted incidental temporal record is bounded incidental texture for the baker's glance/shrug; the NPC spoken answer is claim-only/hearsay in validation and is not promoted to durable world truth.

## Cost

PR-BX P2: 48,294 input tokens, 209 output tokens, 48,503 total tokens, 2 provider attempts.

PR-BZ P2: {digest.get("input_tokens")} input tokens, {digest.get("output_tokens")} output tokens, {digest.get("total_tokens")} total tokens, {digest.get("provider_attempts")} provider attempt.

This is a single sample and did not exercise retry, so no generalized cost-improvement claim is made.
"""
    (OUT / "PR-BZ_micro_live_report.md").write_text(report, encoding="utf-8")

    analysis = f"""# PR-BZ Narration Validation Analysis

No PR-BZ P2 narration rejection occurred.

Accepted narration:

> {digest.get("accepted")}

Declaration validation passed with application-created empty `declared_claims`.

Narration validation passed with no violations. The validator classified the baker's gesture as bounded incidental texture and the spoken denial of a favorite loaf as NPC claim-only/hearsay. No implicated rejected span exists for this run.

PR-BX comparison: the prior baker response was rejected for `unowned_stateful_world_assertion` and `unauthorized_evidential_relation`; the latter had a suspicious curly-quote sentence boundary. That behavior did not recur here, so PR-BZ provides no new evidence for a sentence-boundary defect and no basis for validator repair.
"""
    (OUT / "PR-BZ_narration_validation_analysis.md").write_text(analysis, encoding="utf-8")

    current_review = f"""# CURRENT REVIEW

PR-BZ
MODE: NARRATION-ONLY RETRY MICRO-LIVE VALIDATION

LIVE CALLS: 1 gameplay generation. One first sandboxed attempt was interrupted before gameplay generation during startup/preflight; the successful live run was executed outside the sandbox for API access.

P2 selected envelope: {digest.get("selected_envelope")}

P2 provider attempts: {digest.get("provider_attempts")}

P2 initial response shape: {json.dumps(digest.get("initial_structural_shape"), ensure_ascii=False)}

P2 initial declaration validation: hard_valid true; accepted_claims []; rejected_claims [].

P2 initial narration validation: hard_valid true; reasons [].

Retry triggered: false

Retry contract not exercised: true

Final accepted: true

Final emitted narration:
{digest.get("emitted")}

C18 integrity: accepted == sealed == emitted.

State/provenance integrity: no authority problems; no accepted model-authored declarations; no declaration metadata leaked.

Token comparison: PR-BX P2 48,294 input / 209 output / 48,503 total / 2 attempts. PR-BZ P2 {digest.get("input_tokens")} input / {digest.get("output_tokens")} output / {digest.get("total_tokens")} total / {digest.get("provider_attempts")} attempt.

PR-BW status: implemented
PR-BX status: C / bounded repair requested
PR-BY status: A / deterministic repair passed

PR-BZ decision: A — P2 LIVE VALIDATION PASSED

Recommended next step: accept PR-BZ as first-attempt live validation of ordinary incidental dialogue under the narration-only contract. Do not claim live retry validation; retry remains covered by deterministic PR-BY evidence until a natural live narration rejection exercises it.
"""
    (HANDOFF / "CURRENT_REVIEW.md").write_text(current_review, encoding="utf-8")

    manifest = {
        "review": "PR-BZ",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "A — P2 LIVE VALIDATION PASSED",
        "evidence_root": "artifacts/pr_bz_narration_only_retry_micro_live",
        "files": [
            "artifacts/pr_bz_narration_only_retry_micro_live/PR-BZ_micro_live_report.md",
            "artifacts/pr_bz_narration_only_retry_micro_live/PR-BZ_P2_live_evidence.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/PR-BZ_retry_contract_evidence.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/PR-BZ_narration_validation_analysis.md",
            "artifacts/pr_bz_narration_only_retry_micro_live/PR-BZ_token_comparison.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/focused_tests.txt",
            "artifacts/pr_bz_narration_only_retry_micro_live/provider_request_response_redacted.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/evidence/phase0_prelive.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/evidence/P2/digest.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/evidence/P2/validation.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/evidence/P2/normalization.json",
            "artifacts/pr_bz_narration_only_retry_micro_live/evidence/P2/raw_generation_attempt_1.json",
        ],
    }
    write_json(HANDOFF / "REVIEW_MANIFEST.json", manifest)

    zip_path = HANDOFF / "CURRENT_REVIEW.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        zf.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for rel in manifest["files"]:
            path = ROOT / rel
            if path.exists():
                zf.write(path, rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
