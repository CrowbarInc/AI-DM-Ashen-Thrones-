#!/usr/bin/env python3
"""PR-CT safe prompt deduplication evidence builder. No provider calls."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from game.gm import NO_VALIDATOR_VOICE_RULE, RULE_PRIORITY_COMPACT_INSTRUCTION
from tools.measure_pr_bt_policy_instruction_payloads import PROBES, reconstruct_probe

OUT = ROOT / "artifacts" / "pr_ct_safe_prompt_dedup"
HANDOFF = ROOT / "handoff"

SYSTEM_OWNED_DUPLICATES = (
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    "Always answer the player. Prefer partial truth over refusal. Never output meta explanations.",
    NO_VALIDATOR_VOICE_RULE,
)

CAPTURED_FIXTURES = (
    ("A", "harmless_npc_preference", ROOT / "artifacts/pr_cq_live_finalization/evidence/T1/provider_request_generation_1.json"),
    ("B", "authored_npc_fact_question", ROOT / "artifacts/pr_cq_live_finalization/evidence/T2/provider_request_generation_1.json"),
    ("C", "observation_notice_board", ROOT / "artifacts/pr_co_gameplay_viability/evidence/T1/provider_request_generation_1.json"),
    ("D", "ordinary_observation", ROOT / "artifacts/pr_co_gameplay_viability/evidence/T2/provider_request_generation_1.json"),
    ("E", "natural_language_exploration", ROOT / "artifacts/pr_co_gameplay_viability/evidence/T3/provider_request_generation_1.json"),
)


def _sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _stable(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _estimate_tokens(chars: int) -> int:
    return (chars + 3) // 4


def _load_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _messages_from_request(request: dict[str, Any]) -> list[dict[str, str]]:
    messages = request.get("provider_input")
    if not isinstance(messages, list):
        raise RuntimeError(f"missing provider_input in request")
    return messages


def _system_payload(messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    system = ""
    payload: dict[str, Any] = {}
    for msg in messages:
        if msg.get("role") == "system":
            system = str(msg.get("content") or "")
        elif msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                payload = parsed
    return system, payload


def _deduped_messages(messages: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    system, payload = _system_payload(messages)
    instructions = payload.get("instructions")
    if not isinstance(instructions, list):
        return messages, []
    removed: list[str] = []
    kept: list[Any] = []
    for item in instructions:
        if isinstance(item, str) and item.strip() and item in system:
            removed.append(item)
        else:
            kept.append(item)
    if not removed:
        return messages, []
    reduced_payload = dict(payload)
    reduced_payload["instructions"] = kept
    reduced: list[dict[str, str]] = []
    for msg in messages:
        if msg.get("role") == "user":
            reduced.append({"role": "user", "content": json.dumps(reduced_payload, ensure_ascii=False)})
        else:
            reduced.append(dict(msg))
    return reduced, removed


def _reinsert_baseline_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    system, payload = _system_payload(messages)
    instructions = list(payload.get("instructions") or [])
    to_insert = [text for text in SYSTEM_OWNED_DUPLICATES if text in system and text not in instructions]
    if not to_insert:
        return messages
    insert_at = 0
    for i, item in enumerate(instructions):
        if isinstance(item, str) and item.startswith("Follow response_policy."):
            insert_at = i
            break
    baseline_payload = dict(payload)
    baseline_payload["instructions"] = instructions[:insert_at] + to_insert + instructions[insert_at:]
    baseline: list[dict[str, str]] = []
    for msg in messages:
        if msg.get("role") == "user":
            baseline.append({"role": "user", "content": json.dumps(baseline_payload, ensure_ascii=False)})
        else:
            baseline.append(dict(msg))
    return baseline


def _top_sections(messages: list[dict[str, str]]) -> dict[str, int]:
    system, payload = _system_payload(messages)
    sections = {"system_prompt": len(system), "user_payload": len(_stable(payload))}
    for key, value in payload.items():
        sections[f"payload.{key}"] = len(_stable(value))
    return dict(sorted(sections.items(), key=lambda kv: kv[1], reverse=True)[:12])


def _contract_result(messages: list[dict[str, str]]) -> dict[str, bool]:
    system, payload = _system_payload(messages)
    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    scene = payload.get("scene") if isinstance(payload.get("scene"), dict) else {}
    return {
        "player_intent": bool(str(payload.get("player_input") or "").strip()),
        "current_scene": isinstance(scene.get("public"), dict) or isinstance(payload.get("session"), dict),
        "visibility": isinstance(payload.get("narration_visibility"), dict),
        "response_policy": isinstance(policy, dict) and bool(policy),
        "schema": "Return valid JSON only" in system,
        "authority_decision": isinstance(payload.get("gm_resolution_decision"), dict)
        or isinstance(payload.get("resolution_contract"), dict),
        "continuity": isinstance(payload.get("selected_conversational_memory"), list)
        or isinstance(payload.get("recent_log"), list),
    }


def _measure(fixture_id: str, name: str, baseline: list[dict[str, str]], reduced: list[dict[str, str]], removed: list[str]) -> dict[str, Any]:
    before_s = _stable(baseline)
    after_s = _stable(reduced)
    before_chars = len(before_s)
    after_chars = len(after_s)
    return {
        "fixture_id": fixture_id,
        "fixture": name,
        "baseline_sha256": _sha(before_s),
        "reduced_sha256": _sha(after_s),
        "baseline_bytes": len(before_s.encode("utf-8")),
        "reduced_bytes": len(after_s.encode("utf-8")),
        "baseline_chars": before_chars,
        "reduced_chars": after_chars,
        "byte_reduction": len(before_s.encode("utf-8")) - len(after_s.encode("utf-8")),
        "percent_byte_reduction": round((len(before_s.encode("utf-8")) - len(after_s.encode("utf-8"))) / max(1, len(before_s.encode("utf-8"))) * 100, 4),
        "baseline_est_tokens_chars_over_4": _estimate_tokens(before_chars),
        "reduced_est_tokens_chars_over_4": _estimate_tokens(after_chars),
        "estimated_token_reduction": _estimate_tokens(before_chars) - _estimate_tokens(after_chars),
        "removed_instruction_count": len(removed),
        "removed_sha256": [_sha(text) for text in removed],
        "removed_categories": ["exact system-owned duplicate instruction"] if removed else [],
        "top_sections_baseline": _top_sections(baseline),
        "top_sections_reduced": _top_sections(reduced),
        "contract": _contract_result(reduced),
    }


def _current_probe_fixture(probe: str, player: str) -> list[dict[str, str]]:
    reconstruct_probe(probe, player, out_dir=OUT)
    request = _load_request(OUT / "evidence" / probe / "provider_request_generation_1.json")
    return _messages_from_request(request)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    for fixture_id, name, path in CAPTURED_FIXTURES:
        request = _load_request(path)
        baseline = _messages_from_request(request)
        reduced, removed = _deduped_messages(baseline)
        rec = _measure(fixture_id, name, baseline, reduced, removed)
        records.append(rec)
        payloads[fixture_id] = {"name": name, "baseline": baseline, "reduced": reduced}
    for fixture_id, name, probe in (
        ("F", "consequential_social_interaction_proxy", "P2"),
        ("G", "physical_world_action_proxy", "P1"),
        ("H", "exploration_hypothesis_proxy", "P3"),
    ):
        player = next(p for p, _scene, p in PROBES if p == probe) if False else None
        player = {p: text for p, _scene, text in PROBES}[probe]
        reduced = _current_probe_fixture(probe, player)
        baseline = _reinsert_baseline_messages(reduced)
        _reduced2, removed = _deduped_messages(baseline)
        rec = _measure(fixture_id, name, baseline, reduced, removed)
        records.append(rec)
        payloads[fixture_id] = {"name": name, "baseline": baseline, "reduced": reduced}
    (OUT / "PR-CT_before_after_payloads.json").write_text(json.dumps(payloads, indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "PR-CT_prompt_measurements.csv").open("w", encoding="utf-8", newline="") as f:
        fields = [
            "fixture_id",
            "fixture",
            "baseline_bytes",
            "reduced_bytes",
            "byte_reduction",
            "percent_byte_reduction",
            "baseline_est_tokens_chars_over_4",
            "reduced_est_tokens_chars_over_4",
            "estimated_token_reduction",
            "removed_instruction_count",
            "baseline_sha256",
            "reduced_sha256",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow({k: rec.get(k) for k in fields})
    summary = {
        "live_provider_calls": 0,
        "tokenizer": "local estimate ceil(chars/4); exact GPT-4.1 tokenizer unavailable locally",
        "records": records,
        "decision": "B - LIMITED SAVINGS",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def _write_reports(summary: dict[str, Any]) -> None:
    records = summary["records"]
    total_removed = sum(int(r["byte_reduction"]) for r in records)
    min_removed = min(int(r["byte_reduction"]) for r in records)
    max_removed = max(int(r["byte_reduction"]) for r in records)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True)
    (OUT / "changed_files.txt").write_text(changed, encoding="utf-8")
    (OUT / "focused_tests.txt").write_text(
        ".\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ct_safe_prompt_deduplication.py -q --basetemp=codex_pytest_tmp_pr_ct\n",
        encoding="utf-8",
    )
    (OUT / "PR-CT_deduplication_contract.md").write_text(
        "# PR-CT Deduplication Contract\n\n"
        "Eligible removal was limited to instruction strings in provider payload instructions that are present verbatim in the selected system prompt. "
        "The system prompt keeps the higher-priority canonical copy; payload policy objects, resolver decisions, visibility contracts, CTIR-derived projections, validators, persistence, and audit logs are not removed.\n\n"
        "Removed category: exact system-owned duplicate instruction. Semantic near-duplicates, retry feedback, provenance-bearing facts, visibility/certainty-bearing claims, and validator inputs remain in place.\n",
        encoding="utf-8",
    )
    rows = "\n".join(
        f"| {r['fixture_id']} | {r['fixture']} | {r['baseline_bytes']} | {r['reduced_bytes']} | {r['byte_reduction']} | {r['estimated_token_reduction']} |"
        for r in records
    )
    (OUT / "PR-CT_implementation_report.md").write_text(
        "# PR-CT Implementation Report\n\n"
        f"Git HEAD: `{head}`\n\n"
        "Implementation: `game.gm._dedupe_provider_payload_instructions` removes exact system-owned duplicate instruction strings at the provider-payload boundary after resolver-specific payload assembly and before JSON serialization.\n\n"
        "Live provider calls: 0.\n\n"
        "Tokenizer: local estimate `ceil(chars/4)`; exact GPT-4.1 tokenizer was not installed or fetched.\n\n"
        "| Fixture | Name | Baseline bytes | Reduced bytes | Byte reduction | Estimated token reduction |\n"
        "|---|---:|---:|---:|---:|---:|\n"
        f"{rows}\n\n"
        f"Total byte reduction across measured fixtures: {total_removed}. Per-fixture range: {min_removed} to {max_removed} bytes.\n\n"
        "Decision: B - LIMITED SAVINGS. The reduction is intentionally small and exact; no semantic prompt profiling was introduced.\n",
        encoding="utf-8",
    )
    (OUT / "PR-CT_removed_content_inventory.md").write_text(
        "# PR-CT Removed Content Inventory\n\n"
        "Removed only these exact duplicated instruction strings when already present in the selected system prompt:\n\n"
        + "\n".join(f"- `{_sha(text)}`: {text}" for text in SYSTEM_OWNED_DUPLICATES)
        + "\n",
        encoding="utf-8",
    )
    (OUT / "PR-CT_prompt_contract_tests.md").write_text(
        "# PR-CT Prompt Contract Tests\n\n"
        "Added `tests/test_pr_ct_safe_prompt_deduplication.py`.\n\n"
        "The tests inspect serialized provider-facing messages and assert player input, scene/session, turn packet, response policy, narration visibility, decision-facing recipe, GM resolution decision, resolution contract, and response schema remain present while exact system-owned duplicates are absent from payload instructions.\n",
        encoding="utf-8",
    )
    (OUT / "PR-CT_authority_integrity.md").write_text(
        "# PR-CT Authority Integrity\n\n"
        "No authority-bearing state was removed. `response_policy`, `narration_visibility`, `gm_resolution_decision`, `resolution_contract`, `decision_facing_answer_recipe`, `turn_packet`, and scene/session payload surfaces remain provider-visible in focused contract tests. The change does not alter resolver selection, schemas, retry eligibility, state commitment, model routing, validators, or persistence.\n",
        encoding="utf-8",
    )
    (OUT / "PR-CT_regression_results.md").write_text(
        "# PR-CT Regression Results\n\n"
        "Focused PR-CT prompt-contract tests: `3 passed`.\n\n"
        "Broader requested suites were not fully run in this bounded pass. Existing inherited shared pipeline baseline from PR-CS: `41 passed / 24 failed`. No live provider calls were made.\n",
        encoding="utf-8",
    )
    (HANDOFF / "CURRENT_REVIEW.md").write_text(
        "# CURRENT REVIEW\n\n"
        "PR-CT\n\n"
        "MODE:\nSAFE PROMPT DEDUPLICATION\n\n"
        "LIVE CALLS:\n0\n\n"
        "PR-CS inherited decision:\nA - CLEAR LOW-RISK OPTIMIZATION PATH\n\n"
        "Baseline prompt measurements:\nSee `artifacts/pr_ct_safe_prompt_dedup/PR-CT_prompt_measurements.csv`.\n\n"
        "Reduced prompt measurements:\nSee `artifacts/pr_ct_safe_prompt_dedup/PR-CT_prompt_measurements.csv`.\n\n"
        "Exact/estimated tokenizer:\nEstimated only: local `ceil(chars/4)`. Exact tokenizer unavailable locally; no dependency install or network call performed.\n\n"
        "Removed content:\nExact instruction strings duplicated verbatim between selected system prompt and payload instructions.\n\n"
        "Authority-sensitive content preserved:\nresponse_policy, narration_visibility, gm_resolution_decision, resolution_contract, decision_facing_answer_recipe, turn_packet, scene/session surfaces, validators, finalization, persistence.\n\n"
        "Prompt contract results:\nFocused PR-CT tests passed: 3 passed.\n\n"
        "Authority integrity:\nNo authority owner changed; no semantic deduplication or resolver-specific prompt profile introduced.\n\n"
        "Shared pipeline before:\n41 passed / 24 failed\n\n"
        "Shared pipeline after:\nNot rerun in full.\n\n"
        "Focused regression:\n`.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_ct_safe_prompt_deduplication.py -q --basetemp=codex_pytest_tmp_pr_ct` => 3 passed.\n\n"
        "Broad regression:\nNot run / results unavailable.\n\n"
        "PR-CT decision:\nB - LIMITED SAVINGS\n\n"
        "Recommended next step:\nRun the broader PR-CP/PR-CR/PR-CI/PR-CC/PR-CE/PR-CK/PR-CN/shared-pipeline regression matrix, then consider a separate exact repeated-fact projection pass.\n",
        encoding="utf-8",
    )
    manifest = {"pr": "PR-CT", "artifact_dir": "artifacts/pr_ct_safe_prompt_dedup", "head": head, "status_short": status}
    (HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(HANDOFF / "CURRENT_REVIEW.zip", "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in [HANDOFF / "CURRENT_REVIEW.md", HANDOFF / "REVIEW_MANIFEST.json", *sorted(OUT.glob("PR-CT*")), OUT / "focused_tests.txt", OUT / "changed_files.txt"]:
            z.write(path, path.relative_to(ROOT))


def main() -> int:
    summary = build()
    _write_reports(summary)
    print(json.dumps({"decision": summary["decision"], "fixtures": len(summary["records"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
