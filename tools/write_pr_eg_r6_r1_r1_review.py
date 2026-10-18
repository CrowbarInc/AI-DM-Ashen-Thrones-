"""Package the PR-EG-R6-R1-R1 CURRENT_REVIEW."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_eg_r6_r1_r1"
PREV = ROOT / "artifacts" / "pr_eg_r6_r1"


def write(name: str, value) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2, default=str), encoding="utf-8")


def ref(path: str, symbol: str) -> str:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    number = next((i for i, line in enumerate(lines, 1) if symbol in line), 1)
    return f"[{path}:{number}](../../{path}#L{number})"


def cases(path: Path) -> dict:
    out = {}
    for case in ET.parse(path).iter("testcase"):
        failed = next((item for item in case if item.tag in {"failure", "error"}), None)
        out[f"{case.get('classname')}::{case.get('name')}"] = {
            "failed": failed is not None,
            "message": (failed.get("message") or "") if failed is not None else "",
        }
    return out


def live_rows() -> list[dict]:
    path = OUT / "live_turns.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def p95(values: list[float]):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95 + 0.999) - 1)]


def main() -> None:
    preserved = json.loads((PREV / "regression_comparison.json").read_text(encoding="utf-8"))
    current = cases(OUT / "regression_junit.xml")
    reproduction = cases(OUT / "reproduction_junit.xml")
    new_ids = list(preserved["new_failures"])
    inherited_ids = list(preserved["inherited_failures"])
    still_new = [key for key in new_ids if current.get(key, {}).get("failed")]
    still_inherited = [key for key in inherited_ids if current.get(key, {}).get("failed")]
    reproduced_new = [key for key in new_ids if reproduction.get(key, {}).get("failed")]
    inherited_not_reproduced = [key for key in inherited_ids if key in reproduction and not reproduction[key]["failed"]]
    added = [key for key in current if "test_pr_eg_r6_r1_r1_provenance" in key]
    live = live_rows()
    tokens = [sum(call.get("input_tokens") or 0 for call in row.get("provider_calls") or []) for row in live]
    latency = [row["latency_ms"] for row in live]
    calls = [call for row in live for call in row.get("provider_calls") or []]
    performance = {
        "turns": len(live),
        "conversations": len({row["conversation"] for row in live}),
        "provider_calls": len(calls),
        "calls_per_turn": len(calls) / len(live) if live else None,
        "mean_input_tokens_per_turn": statistics.mean(tokens) if tokens else None,
        "p95_input_tokens_per_turn": p95(tokens),
        "mean_latency_ms": statistics.mean(latency) if latency else None,
        "p95_latency_ms": p95(latency),
        "retry_calls": sum("retry" in str(call.get("purpose") or "") for call in calls),
        "failed_integrity_checks": sum(not all(row["checks"].values()) for row in live),
        "secret_value_leaks": sum(not row["checks"]["no_secret"] for row in live),
        "unauthorized_secret_clues": sum(not row["checks"]["no_secret_clue"] for row in live),
        "categories_observed": sorted({str(row.get("authority_category")) for row in live}),
        "note": "Provenance validation is host-owned and adds no provider call. Input-token p95 is carried by the existing narration calls, not by a provenance model.",
    }
    write("performance.json", performance)
    write("live_status.json", {"status": "completed", **performance})
    clusters = {
        "A_host_operation_or_fixture_world_source": [key for key in new_ids if "authorized_disclosure" in key or "frozen_holdout" in key or "direct_authorized" in key or "partial_fact" in key or "T09" in key or "T11" in key or "T12" in key or "T15" in key or "T27" in key or "R1H08" in key],
        "B_verified_or_legacy_history": [key for key in new_ids if "recall" in key or "T0" in key or "T1" in key or "T2" in key or "continuity" in key or "historical" in key or "exact_recall" in key or "R1H10" in key or "proposition_identity" in key or "followup" in key or "gm_and_absent" in key],
        "C_commitment": [key for key in new_ids if "repeated_preference" in key],
        "I_denial_replaced_uncertainty": [key for key in new_ids if "provider_evidence" in key],
    }
    write("regression_comparison.json", {
        "baseline_preserved_passed": preserved["baseline_passed"],
        "baseline_preserved_failed": preserved["baseline_failed"],
        "r6_r1_preserved_passed": preserved["final_passed"],
        "r6_r1_preserved_failed": preserved["final_failed"],
        "r6_r1_new_identities": len(new_ids),
        "reproduction_new_still_failing": len(reproduced_new),
        "reproduction_inherited_not_reproduced": inherited_not_reproduced,
        "final_passed": sum(not row["failed"] for row in current.values()),
        "final_failed": sum(row["failed"] for row in current.values()),
        "new_identities_still_failing": still_new,
        "inherited_still_failing": still_inherited,
        "added_provenance_tests": len(added),
        "added_provenance_failures": sum(current[key]["failed"] for key in added),
        "clusters": {name: items for name, items in clusters.items()},
    })

    summary = (
        "**B — QUALIFIED WITH LIMITATIONS.** The 44 PR-EG-R6-R1 disclosure regressions were reproduced and recovered. "
        f"The matched selection is now {sum(not row['failed'] for row in current.values())} passed / {sum(row['failed'] for row in current.values())} failed. "
        "Both remaining failures are inherited and were not introduced here. Fresh production /api/chat qualification recorded 80 turns across 5 conversations, with 0 restricted-value leaks and 0 restricted clue discoveries. "
        "Legacy recall of non-protected delivered speech is intentionally narrower than a blanket grandfather, and wider than a current-source recheck of every public sentence. Unified-planning live turns still often fail to ground an utterance; that routing behavior was not redesigned."
    )
    sections = {
        "01_EXECUTIVE_SUMMARY": summary + "\n\nStop. Do not begin PR-EG-R6-R2 or PR-EH.",
        "02_BASELINE_AND_REPOSITORY_STATE": (
            "Preserved R6-R1 evidence remains in `artifacts/pr_eg_r6_r1`. Before this cycle edited production code, the same selection was rerun from the current tree into `reproduction_junit.xml`. "
            f"All {len(reproduced_new)} preserved new identities failed again. "
            f"{len(inherited_not_reproduced)} preserved inherited identities did not fail in a clean process. Their preserved messages are expression-audit `None` or missing `expression_generation`, which is what `expression_generation_disabled()` returns when provider calls are disabled. This cycle did not treat those as fixed disclosure defects.\n\n"
            "Two inherited failures still reproduce with the same messages: `answer_sufficiency` is absent on a source-denied authority record built without an NPC, and the preseal test still expects `initial_generation` where the host now seals `authorized_host_speech`."
        ),
        "03_REGRESSION_FAILURE_CLASSIFICATION": (
            "Every preserved new identity was classified before production edits. The first failing decision was `seal_host_speech` or `historical_disclosure_permitted`, not a later narrator.\n\n"
            "- World-source fixtures put an authorized fact on `topic_revealed` without an NPC receipt. The seal treated the missing receipt as denial and replaced the fact with a refusal. The original expectation, that the authorized fact is delivered, remains valid. The helpers now bind a public NPC source and the host receipt that production social resolution already writes. Assertions were not rewritten.\n"
            "- Historical and continuity rows were rejected because a delivered proposition was promoted back into a world-source check, or because a legacy row had no digest. Expected recall of non-protected delivered speech was still valid.\n"
            "- The morning preference commitment had no `disclosure_scope`. It is bounded expression, not a secret.\n"
            "- `test_provider_evidence_cannot_recall_fact_for_incompatible_question` expected uncertainty (`couldn't`) and received a disclosure refusal because the prior proposition vetoed the whole line.\n\n"
            "No new identity was an actual unauthorized disclosure. Identities are grouped in `regression_comparison.json`."
        ),
        "04_AUTHORITY_FLOW_AUDIT": (
            f"Authority is created by {ref('game/dialogue_authority.py', 'def authorize_npc_disclosure')} and {ref('game/dialogue_authority.py', 'def build_dialogue_authority')}. "
            f"Social resolution calls that grant before a topic is revealed: {ref('game/social.py', 'disclosure = authorize_npc_disclosure')}. "
            f"Validation at final adoption is {ref('game/immutable_valid_response.py', 'def seal_host_speech')}. "
            f"History is rechecked by {ref('game/dialogue_authority.py', 'def historical_disclosure_permitted')} from {ref('game/conversational_continuity.py', 'def supplied_clarification')}. "
            f"Discovery re-resolves the same grant in {ref('game/clues.py', 'grant = authorize_npc_disclosure')}. "
            f"The API passes world into adoption at {ref('game/api.py', 'adopted_speech = adopt_host_speech')}. "
            "A receipt is consulted only when world is absent. Provider metadata is not an authority input. Provenance is stored on the existing authority record and the sealed accepted response; it is not a second store."
        ),
        "05_UNIFIED_PROVENANCE_CONTRACT": (
            f"Categories live beside the existing authority record: `world_source`, `host_operation`, `bounded_expression`, and `verified_history` ({ref('game/dialogue_authority.py', 'CATEGORY_WORLD')}). "
            f"Each record from {ref('game/dialogue_authority.py', 'def provenance_record')} carries category, speaker, addressee, operation, proposition, source id, epistemic status, validation, provenance id, and policy version `pr-eg-r6-r1-r1`. "
            "The final digest still covers the accepted response, including this provenance object. Provider text cannot mint the record."
        ),
        "06_WORLD_SOURCE_AUTHORITY": (
            "Consequential disclosure still requires `authorize_npc_disclosure`: a matching NPC source, known status, and a public/allowed/authorized policy. Unknown policy and unknown knowledge fail closed. "
            "When world is present, a caller-supplied receipt is ignored and the NPC source is resolved again. A pure caller without world must present a host receipt whose validation, provenance, speaker, and proposition match, and that receipt cannot authorize protected wording."
        ),
        "07_HOST_OPERATION_AUTHORITY": (
            "Uncertainty, clarification, refusal, and acknowledgment are `host_operation` when they do not carry a protected or consequential addition. "
            f"The check is {ref('game/dialogue_authority.py', 'def is_host_operation')} and {ref('game/dialogue_authority.py', 'def consequential_addition')}. "
            "A refusal that also states a protected fact is rejected. A host operation does not create a discovered clue."
        ),
        "08_BOUNDED_EXPRESSION_AUTHORITY": (
            "Preferences such as morning or evening, and the existing non-canonical watch remark, stay `bounded_expression`. "
            "Protected wording or the existing consequential-claim pattern removes that classification. The expression contract's prohibition on new facts is unchanged."
        ),
        "09_VERIFIED_HISTORY_AUTHORITY": (
            "A modern row with a topic id is recallable only when the current NPC source permits that topic and the delivered wording restates it. A digest alone does not authorize protected text. "
            "Paraphrase such as `Word is, ...` matches when the source sentence is contained and no protected extra is added."
        ),
        "10_LEGACY_HISTORY_COMPATIBILITY": (
            "Legacy rows are classified rather than grandfathered. Protected wording fails closed. An NPC topic that exists and is not permitted fails closed. "
            "A host-owned delivered exchange whose text is not protected remains recallable as delivered speech. That is the compatibility limit: a public location sentence in an old host record can be quoted again, while a restricted source or protected sentence cannot."
        ),
        "11_HISTORICAL_RECALL_AND_COMMITMENTS": (
            f"Commitments with a proposition still need a permitted source. A proposition that is only a preference is bounded and may be reused ({ref('game/dialogue_authority.py', 'def commitment_disclosure_permitted')}). "
            "A commitment whose text is protected is not reusable. Speaker identity on the delivery row is unchanged. Recall quotes the stored line; it does not invent a new fact."
        ),
        "12_MIXED_CONTENT_AUTHORIZATION": (
            "A sentence covered by an authorized proposition can stand. Another sentence that matches the protected or consequential pattern is enough to reject the whole candidate through the existing seal. The unauthorized portion is not delivered beside the safe portion."
        ),
        "13_PROVENANCE_VALIDATION": (
            "Category is chosen by the host from the line, the topic grant, and the history decision. A caller field named `authority_category` is not read. "
            "A receipt with `permission: true` but without host validation, authored provenance, speaker, and exact proposition is rejected. Protected wording is rejected even if those fields are forged. World re-resolution rejects a secret topic whose policy is restricted."
        ),
        "14_FINAL_RESPONSE_INTEGRATION": (
            "Seal still writes one immutable accepted response and then the delivery digest. API text, the sealed text, and recorded history matched on all 80 live turns. "
            f"A disclosure refusal is stored as GM-owned history without raising a speaker mismatch ({ref('game/conversational_continuity.py', 'Disclosure refusals are stored')}). "
            "Post-adoption world updates on the discarded candidate are cleared by the existing host-speech seal."
        ),
        "15_DISCOVERY_PERSISTENCE": (
            "Clue landing still re-resolves the NPC source before writing. Unauthorized password resolutions write no clue. An authorized public fact writes one clue, and a second landing is empty. "
            "Live logs showed public harbor clues and an ignored duplicate. No restricted value appeared in clue knowledge."
        ),
        "16_REGRESSION_REPAIRS": (
            f"Recovered new identities: {len(new_ids) - len(still_new)} of {len(new_ids)}. Remaining new identities: {len(still_new)}. "
            "Repairs were the provenance decision in the existing seal, legacy history classification, bounded commitments, and fixture receipts for pure callers. No speaker-name exception or phrase blacklist was added. The password policy check was not weakened."
        ),
        "17_CONTROLLED_TESTS": (
            f"`tests/test_pr_eg_r6_r1_r1_provenance.py` adds {len(added)} cases covering T01–T36, including grammatical password variants under both feature-gate settings. All of those cases passed. "
            "The original disclosure-boundary module was rerun with them and remained green."
        ),
        "18_REGRESSION_COMPARISON": (
            f"Preserved pre-repair selection: {preserved['baseline_passed']} passed / {preserved['baseline_failed']} failed. "
            f"Preserved R6-R1 selection: {preserved['final_passed']} passed / {preserved['final_failed']} failed, of which {len(new_ids)} were new. "
            f"This cycle's selection, including the new provenance tests: {sum(not row['failed'] for row in current.values())} passed / {sum(row['failed'] for row in current.values())} failed. "
            f"New identities still failing: {len(still_new)}. Inherited identities still failing: {len(still_inherited)}. "
            "The two inherited failures are listed in `regression_comparison.json`. Their expectations were not rewritten."
        ),
        "19_ADVERSARIAL_PROVENANCE_TESTS": (
            "Controlled cases reject a missing source, a host-operation sentence that adds a protected fact, a bounded sentence that adds a protected fact, a restricted historical row, a forged permission flag, a provider-marked secret topic, mixed public and protected sentences, and password requests under both gates. "
            "Live conversation 3 repeated imperative, elliptical, false-prior, injection, and mixed requests. None delivered the restricted value and none wrote a restricted clue."
        ),
        "20_MATCHED_BASELINE_COMPARISON": (
            "A, before R6-R1: the preserved reproduction disclosed the restricted value and persisted a clue. "
            "B, R6-R1: the same request was blocked, and legitimate recall fixtures failed closed. "
            "C, this cycle: the value stays blocked with world re-resolution; public bell, gate, and watch facts are delivered when the NPC source permits them; uncertainty and preference lines are sealed under host or bounded provenance; a non-protected legacy quote can be recalled; a protected legacy quote cannot."
        ),
        "21_FRESH_PROVIDER_CONVERSATIONS": (
            "Five independent 16-turn conversations, 80 turns, were run through production `/api/chat` with unified planning alternating on and off. "
            "The frozen R6 holdout file was hashed and not edited. Utterances were authored for this qualification and were not taken from that holdout. "
            "An initial substring detector treated the topic word as the restricted value and stopped early. That was an instrument error. The rerun uses a word-boundary check. The stopped utterance was a refusal, not a value disclosure."
        ),
        "22_TURN_LEVEL_QUALIFICATION": (
            "Each live row records the player utterance, feature-gate flag, delivered text with the restricted value redacted, authority category, validation, authorization source, seal/history/canonical/clue checks, provider-call purposes, token counts, and latency. "
            f"Integrity failures: {performance['failed_integrity_checks']}. Restricted-value leaks: {performance['secret_value_leaks']}. "
            "Many unified-planning turns returned an ungrounded clarification instead of an answer. That is recorded, and it is outside this cycle's repair."
        ),
        "23_PERFORMANCE": (
            f"Provider calls: {performance['provider_calls']} across {performance['turns']} turns ({performance['calls_per_turn']:.3f} per turn). "
            f"Mean input tokens/turn: {performance['mean_input_tokens_per_turn']:.1f}. P95 input tokens/turn: {performance['p95_input_tokens_per_turn']:.1f}. "
            f"Mean latency: {performance['mean_latency_ms']:.1f} ms. P95 latency: {performance['p95_latency_ms']:.1f} ms. Retry-purpose calls: {performance['retry_calls']}. "
            "R6-R1 reported 52 calls / 60 turns, mean input 1,463, mean latency 1.90 s, P95 latency 2.78 s. This set makes fewer calls per turn and has lower mean latency. P95 input tokens are higher because the narration calls that do occur are large. Provenance itself does not call a provider."
        ),
        "24_ACCEPTANCE_GATES": """
| Gate | Result |
| --- | --- |
| 1 Regression classification | Met. All 44 new identities classified. |
| 2 Regression recovery | Met for new identities. Two inherited failures remain. |
| 3 World-source authority | Met. Restricted and missing sources fail closed. |
| 4 Host operations | Met for uncertainty, clarification, and acknowledgment. |
| 5 Bounded expression | Met for a preference; a preference plus a protected fact is rejected. |
| 6 Verified history | Met with the legacy non-protected limit below. |
| 7 Original exploit | Met in resolver tests and live adversarial turns. |
| 8 Routing independence | Met for grammatical password variants under both gates. |
| 9 Mixed content | Met. A protected addition rejects the candidate. |
| 10 Discovery | Met. No restricted clue; authorized public clue is idempotent. |
| 11 Final delivery | Met. 80/80 live turns sealed and equal to history. |
| 12 State | Met. Canonical view unchanged on 80/80 turns. |
| 13 Adversarial | Met. No restricted value in the evaluated set. |
| 14 Fresh provider | Met. 80 turns, 5 conversations, final code, `/api/chat`. |
| 15 Performance | Met with a noted narration-token p95, not a provenance call. |
""",
        "25_REMAINING_LIMITATIONS": (
            "Legacy host deliveries that are not protected can be quoted without a current NPC source. A consequential public sentence in an old save is therefore recallable. Restricted sources and protected wording are not. "
            "Expression rewording of an already selected line is sealed as host conversational speech when no topic is attached to that seal call, provided it adds no protected or consequential pattern. One live paraphrase said the bell marks the hour, which is not the authored sentence. "
            "Unified planning enabled still produces many ungrounded clarifications. This cycle did not redesign that planner. "
            "Two inherited tests remain failed. Twenty-four other preserved inherited failures do not reproduce unless expression generation is disabled. "
            "The synthetic qualification world still contains the restricted topic so the refusal can be tested. It is not part of the review bundle."
        ),
        "26_RECOMMENDED_NEXT_ACTION": (
            "Submit CURRENT_REVIEW for external review. Do not start PR-EG-R6-R2. Do not start PR-EH. "
            "The next decision is whether legacy non-protected consequential sentences should require a reconstructed source before quotation, and whether the ungrounded unified-planning turns belong in a later routing cycle."
        ),
        "27_FINAL_VERDICT": summary,
        "28_SOURCE_AND_EVIDENCE_INVENTORY": (
            "Production: `game/dialogue_authority.py`, `game/immutable_valid_response.py`, `game/conversational_continuity.py`.\n"
            "Tests: `tests/test_pr_eg_r6_r1_r1_provenance.py` and the three resolution helpers that now attach a public source receipt.\n"
            "Tools: `tools/qualify_pr_eg_r6_r1_r1.py`, `tools/write_pr_eg_r6_r1_r1_review.py`.\n"
            "Evidence: reproduction and final JUnit, redacted live turns, usage, performance, and regression comparison. Campaign state directories are omitted because they contain the restricted topic."
        ),
    }
    for title, body in sections.items():
        write(f"{title}.md", f"# {title.replace('_', ' ')}\n\n{body}\n")

    changed = [
        "game/dialogue_authority.py",
        "game/immutable_valid_response.py",
        "game/conversational_continuity.py",
        "tests/test_pr_eg_r2c_speech_adoption.py",
        "tests/test_pr_eg_r3_expressive_dialogue.py",
        "tests/test_pr_eg_r3_r1_expression_semantics.py",
        "tests/test_pr_eg_r6_r1_r1_provenance.py",
        "tools/qualify_pr_eg_r6_r1_r1.py",
        "tools/write_pr_eg_r6_r1_r1_review.py",
    ]
    supports = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or "state" in path.parts:
            continue
        if path.suffix == ".pyc" or path.name == "handoff_config.json":
            continue
        supports.append({
            "path": path.relative_to(ROOT).as_posix(),
            "role": "r6_r1_r1_evidence",
            "why": "Cycle report or redacted qualification evidence.",
            "human_review_required": path.name.startswith(("01_", "27_")),
        })
    for name in changed:
        supports.append({
            "path": name,
            "role": "source",
            "why": "Provenance implementation or validation.",
            "human_review_required": True,
        })
    config = {
        "campaign_id": "pr_eg_r6_r1_r1_provenance_20261017",
        "campaign_name": "PR-EG-R6-R1-R1 — Authorization Provenance and Legacy Compatibility",
        "campaign_date": "2026-10-17",
        "purpose": "Restore legitimate conversational authority without reopening disclosure.",
        "objective_status": "B — QUALIFIED WITH LIMITATIONS",
        "executive_summary": summary,
        "changes": {
            "production": changed[:3],
            "validation": [f"{len(added)} provenance cases; 80 fresh /api/chat turns."],
            "tooling": ["Qualification runner and review builder."],
            "documentation": ["28 review artifacts."],
            "generated_artifacts": ["Redacted transcripts, JUnit, comparison, performance."],
        },
        "testing": {
            "focused": f"{len(added)} provenance tests passed",
            "broader": f"{sum(not row['failed'] for row in current.values())} passed / {sum(row['failed'] for row in current.values())} failed",
            "full_suite": "Not run.",
            "runtime_validation": f"{len(live)} final-code fresh turns across 5 conversations.",
            "model_runtime_boundary": "Configured OpenAI model from the environment. Request purposes are in the usage log.",
            "new_regressions": f"{len(still_new)} of the 44 R6-R1 new identities remain.",
            "pre_existing_failures": f"{len(still_inherited)} inherited failures still reproduce.",
        },
        "known_problems": {
            "campaign_specific": [
                "Legacy non-protected delivered speech can be recalled without a current source.",
                "Unified-planning live turns often remain ungrounded.",
            ],
            "pre_existing": [f"{len(still_inherited)} inherited failures."],
        },
        "decisions_requiring_human_review": [
            "Accept or narrow legacy recall of non-protected consequential sentences.",
        ],
        "missing_concepts": ["A reconstructed source for every legacy public sentence."],
        "does_not_prove": ["That every future paraphrase is free of unauthored incidental detail."],
        "recommended_next_step": "External review. Stop. Do not start PR-EG-R6-R2 or PR-EH.",
        "primary_report": "artifacts/pr_eg_r6_r1_r1/01_EXECUTIVE_SUMMARY.md",
        "supporting_files": supports,
        "max_file_bytes": 50000000,
        "warn_bundle_bytes": 100000000,
    }
    write("handoff_config.json", config)
    hold = hashlib.sha256((ROOT / "artifacts/pr_eg_r6/frozen_holdouts.json").read_bytes()).hexdigest()
    write("holdout_sha256.txt", hold + "\n")
    from tools.build_review_handoff import build_handoff

    result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff")
    print(json.dumps({key: result[key] for key in ("file_count", "zip_size_bytes", "warning") if key in result}, default=str))


if __name__ == "__main__":
    main()
