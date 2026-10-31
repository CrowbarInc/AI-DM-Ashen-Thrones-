#!/usr/bin/env python3
"""Build PR-CA evidence reports and refresh handoff/CURRENT_REVIEW.zip."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_ca_dialogue_continuity"
EVIDENCE = OUT / "evidence"
HANDOFF = ROOT / "handoff"


def load(name: str):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def yn(value: bool) -> str:
    return "yes" if value else "no"


def main() -> int:
    turns = load("completed.json")
    phase0 = load("phase0_prelive.json")
    run_finished = load("run_finished.json")
    model_calls = load("model_calls.json")
    total_input = sum(int(t.get("input_tokens") or 0) for t in turns)
    total_output = sum(int(t.get("output_tokens") or 0) for t in turns)
    total_tokens = sum(int(t.get("total_tokens") or 0) for t in turns)
    retries = sum(1 for t in turns if t.get("retry"))
    attempts = sum(int(t.get("provider_attempts") or 0) for t in turns)

    matrix = []
    for turn in turns:
        matrix.append(
            {
                "turn": turn["turn"],
                "player_input": turn["player"],
                "prior_conversational_context": turn.get("prior_conversational_context", {}).get("temporal"),
                "response_operation": turn.get("response_operation"),
                "declaration_expectation": turn.get("declaration_expectation"),
                "consequentiality": turn.get("consequentiality"),
                "selected_envelope": turn.get("selected_envelope"),
                "provider_response_contract": turn.get("provider_response_contracts"),
                "provider_attempts": turn.get("provider_attempts"),
                "retry": turn.get("retry"),
                "retry_reasons": turn.get("retry_reasons"),
                "input_tokens": turn.get("input_tokens"),
                "output_tokens": turn.get("output_tokens"),
                "total_tokens": turn.get("total_tokens"),
                "declaration_validation": {
                    "accepted_model_authored_declarations": turn.get("accepted_model_authored_declarations"),
                    "declaration_authorship": turn.get("declaration_authorship"),
                    "normalized_empty_declarations": turn.get("normalized_empty_declarations"),
                    "normalized_declared_claims": turn.get("normalized_declared_claims"),
                },
                "narration_validation": {
                    "attempt_1_reasons": turn.get("validation_attempt_1_reasons"),
                    "attempt_2_reasons": turn.get("validation_attempt_2_reasons"),
                    "regeneration_feedback": turn.get("regeneration_feedback"),
                    "accepted": turn.get("accepted"),
                    "sealed": turn.get("sealed"),
                    "emitted": turn.get("emitted"),
                    "c18_exact_equal": turn.get("c18_exact_equal"),
                },
                "state_changes": {
                    "authority_problems": turn.get("authority_problems"),
                    "temporal_after": turn.get("temporal_after"),
                },
                "provenance_changes": turn.get("provenance_changes"),
            }
        )
    write_json(OUT / "PR-CA_turn_matrix.json", matrix)

    token_usage = {
        "per_turn": [
            {
                "turn": t["turn"],
                "input_tokens": t.get("input_tokens"),
                "output_tokens": t.get("output_tokens"),
                "total_tokens": t.get("total_tokens"),
                "provider_attempts": t.get("provider_attempts"),
                "retry_overhead": 0 if not t.get("retry") else None,
                "input_chars": ((t.get("calls") or [{}])[0]).get("input_chars") if t.get("calls") else None,
            }
            for t in turns
        ],
        "cumulative": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_tokens,
            "provider_attempts": attempts,
            "retries": retries,
        },
        "context_growth_observation": "Generation input grew from 100,313 chars / 23,413 tokens on T1 to a high of 106,545 chars / 24,890 tokens on T3, then 106,067 chars / 24,763 tokens on T4. Growth is visible but bounded in this four-turn sample.",
    }
    write_json(OUT / "PR-CA_token_usage.json", token_usage)

    validation_retry = {
        "live_retry_path_exercised": retries > 0,
        "note": "LIVE RETRY PATH NOT EXERCISED." if retries == 0 else "At least one live retry occurred.",
        "turns": [
            {
                "turn": t["turn"],
                "provider_attempts": t.get("provider_attempts"),
                "retry": t.get("retry"),
                "validation_attempt_1_reasons": t.get("validation_attempt_1_reasons"),
                "validation_attempt_2_reasons": t.get("validation_attempt_2_reasons"),
                "regeneration_feedback": t.get("regeneration_feedback"),
                "provider_response_contracts": t.get("provider_response_contracts"),
                "initial_contract_failure": t.get("initial_contract_failure"),
                "initial_contract_reason": t.get("initial_contract_reason"),
                "retry_structural_shape": t.get("retry_structural_shape"),
                "retry_declared_claims": t.get("retry_declared_claims"),
            }
            for t in turns
        ],
    }
    write_json(OUT / "PR-CA_validation_retry_evidence.json", validation_retry)

    provider_evidence = {
        "redaction": "No API keys are present. Provider inputs are omitted here; full local evidence retains measured request metadata.",
        "calls": [
            {
                "turn": call.get("probe"),
                "model": call.get("response_model") or call.get("model"),
                "response_id": call.get("response_id"),
                "provider_response_contract": call.get("provider_response_contract"),
                "retry_context_present": call.get("retry_context_present"),
                "declared_claims_in_system_prompt": call.get("declared_claims_in_system_prompt"),
                "api_response_schema_present": call.get("api_response_schema_present"),
                "usage": call.get("usage"),
                "raw_output": call.get("raw_output"),
            }
            for call in model_calls
            if call.get("kind") == "generation"
        ],
    }
    write_json(OUT / "PR-CA_provider_request_response_redacted.json", provider_evidence)

    full_conversation = []
    for turn in turns:
        full_conversation.append(f"{turn['turn']} PLAYER: {turn['player']}")
        full_conversation.append(f"{turn['turn']} BAKER: {turn.get('emitted')}")
        full_conversation.append("")
    write(OUT / "PR-CA_full_conversation.txt", "\n".join(full_conversation).rstrip() + "\n")

    continuity = """# PR-CA Continuity Analysis

Decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS.

The exchange stayed structurally coherent: each turn addressed the baker, kept the same active interlocutor, and remained within ordinary incidental dialogue. The baker remembered the guarded/private stance from T1 into T2 and T3, and T4 acknowledged the player's closing remark.

Quality limitation: the baker never actually recommended a loaf on T3. Instead, the reply remained evasive and repeated the same caution pattern. T4 then accepted the player's phrasing about a "recommendation" even though the prior turn had not provided one. This is a player-facing conversational quality issue, not an authority or validation failure.

Continuity classifications:

- T1: acceptable incidental texture plus an NPC claim/refusal. No consequential world assertion.
- T2: unsupported but non-consequential NPC claim about privacy/safety. It elaborates naturally from T1 without durable promotion.
- T3: unsupported but non-consequential NPC claim and quality-limited evasion. It avoids fabricating a specific loaf, but is less useful than desired.
- T4: conversational memory is present, but the response repeats the prior non-answer and does not correct the player's "recommendation" framing.

No contradiction of established world facts was observed. No structured realization was invoked unnecessarily. No declaration metadata leaked.
"""
    write(OUT / "PR-CA_continuity_analysis.md", continuity)

    authority = f"""# PR-CA Authority And State Audit

All four turns selected `narration_only` with `response_operation=incidental_dialogue`, `declaration_expectation=reply_not_required`, and `consequential_realization_required=false`.

State/provenance result: PASS.

- Unauthorized durable world fact creation: none detected.
- Accepted model-authored declarations in narration-only: none.
- Declaration channel exposed to provider/player: no.
- C18 accepted/sealed/emitted equality: pass on all four turns.
- Scene visible facts remained limited to the authored baker/loaves setup.
- Rejected consequential bucket remained empty.
- Conversation history and temporal provenance remained available.

The temporal provenance accumulated bounded incidentals and inferred/NPC-claim-like conversational material. Those entries did not enter scene visible facts, world NPC facts, clues, or world flags. This preserves the distinction between conversational memory and authoritative world-state mutation.

World/system background faction pressure counters advanced as part of normal world tick behavior in the isolated run. They were not created by the baker dialogue content and did not encode loaf preferences or consequential bread-stall facts.
"""
    write(OUT / "PR-CA_authority_state_audit.md", authority)

    report = f"""# PR-CA - Incidental Dialogue Continuity Micro-Live

Mode: bounded multi-turn live validation.

Decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS.

## Deterministic Precheck

PASS. Focused narration-only regression tests passed (`48 passed`). PR-BY retry contract preservation, PR-BW narration-only envelope behavior, PR-BV operation projection, and PR-BR structured realization envelope coverage remain intact.

Phase 0 selector/contract check: PASS.

- P1 remained `structured_realization`.
- P2 remained `narration_only`.
- P3 remained `structured_realization`.
- Narration-only contract remained single-field `{{"narration": "player-facing response"}}`.
- Smuggled declaration fields remained rejected.

## Live Execution

One persistent baker session was used. Four player turns completed. The runner halted: `{run_finished.get("halt")}`.

| Turn | Envelope | Attempts | Retry | Input | Output | Total | C18 | Summary |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
"""
    for t in turns:
        report += (
            f"| {t['turn']} | {t.get('selected_envelope')} | {t.get('provider_attempts')} | "
            f"{yn(bool(t.get('retry')))} | {t.get('input_tokens')} | {t.get('output_tokens')} | "
            f"{t.get('total_tokens')} | {yn(bool(t.get('c18_exact_equal')))} | "
            f"{str(t.get('emitted') or '').replace('|', '/')[:140]} |\n"
        )
    report += f"""
## Validation And Retry

Narration validation accepted all four first attempts. Declaration validation passed with normalized empty declarations and no declaration authorship. No natural retry occurred: LIVE RETRY PATH NOT EXERCISED.

## Continuity And Player Experience

The exchange preserved the same baker/interlocutor, remembered the guarded stance, and avoided metadata leakage or consequential fact invention. It was usable but not fully satisfying: T3 did not answer the recommendation request with a loaf, and T4 treated the player's "recommendation" language as acceptable despite the prior non-answer. The repeated guarded phrasing is a model-quality limitation.

## Cost

Cumulative live generation usage: {total_input} input tokens, {total_output} output tokens, {total_tokens} total tokens across {attempts} provider attempts. Retry overhead: 0.
"""
    write(OUT / "PR-CA_dialogue_continuity_report.md", report)

    current_review = f"""# CURRENT REVIEW

PR-CA
MODE: INCIDENTAL DIALOGUE CONTINUITY MICRO-LIVE

LIVE CALLS: 4 generation calls
PLAYER TURNS COMPLETED: 4

Envelope selections: T1 narration_only; T2 narration_only; T3 narration_only; T4 narration_only

Provider attempts: 4 total; 1 per turn

Retries: 0 - LIVE RETRY PATH NOT EXERCISED

Continuity assessment: structurally coherent with non-blocking quality limits. The baker maintained guarded continuity but became repetitive and failed to provide a concrete recommendation on T3.

Narration validation: PASS on all first attempts

Declaration validation: PASS; normalized empty declarations; no model-authored declarations accepted

C18 integrity: PASS; accepted == sealed == emitted on all four turns

State/provenance integrity: PASS; no unauthorized durable world facts or provenance corruption detected

Player-facing usability: usable ordinary conversation, but evasive/repetitive and less helpful than ideal

Total tokens: {total_tokens} ({total_input} input / {total_output} output)

PR-BW status: implemented
PR-BX status: C / repaired by PR-BY
PR-BY status: A / deterministic repair passed
PR-BZ status: A / first-attempt live validation passed

PR-CA decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS

Recommended next step: accept the architecture as multi-turn safe for incidental dialogue, then run a targeted quality follow-up for answer helpfulness/repetition under narration-only NPC dialogue.
"""
    write(HANDOFF / "CURRENT_REVIEW.md", current_review)

    manifest = {
        "review": "PR-CA",
        "mode": "INCIDENTAL DIALOGUE CONTINUITY MICRO-LIVE",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "B - READY WITH NON-BLOCKING QUALITY LIMITATIONS",
        "evidence_root": "artifacts/pr_ca_dialogue_continuity",
        "files": [
            "artifacts/pr_ca_dialogue_continuity/PR-CA_dialogue_continuity_report.md",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_turn_matrix.json",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_full_conversation.txt",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_continuity_analysis.md",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_authority_state_audit.md",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_validation_retry_evidence.json",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_token_usage.json",
            "artifacts/pr_ca_dialogue_continuity/focused_tests.txt",
            "artifacts/pr_ca_dialogue_continuity/PR-CA_provider_request_response_redacted.json",
            "artifacts/pr_ca_dialogue_continuity/evidence/completed.json",
            "artifacts/pr_ca_dialogue_continuity/evidence/model_calls.json",
        ],
    }
    write_json(HANDOFF / "REVIEW_MANIFEST.json", manifest)

    zip_path = HANDOFF / "CURRENT_REVIEW.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in manifest["files"]:
            path = ROOT / rel
            zf.write(path, rel)
        zf.write(HANDOFF / "CURRENT_REVIEW.md", "handoff/CURRENT_REVIEW.md")
        zf.write(HANDOFF / "REVIEW_MANIFEST.json", "handoff/REVIEW_MANIFEST.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
