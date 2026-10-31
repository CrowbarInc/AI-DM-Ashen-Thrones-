"""Generate PR-CW evidence from deterministic local fixtures; no provider calls."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/pr_cw_social_context_projection"
sys.path.insert(0, str(ROOT))
DECISION = "G - INCONCLUSIVE"


def dump(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write(name, text):
    (OUT / name).write_text(text, encoding="utf-8")


def xml_results(path):
    counts, failures = {}, []
    for case in ET.parse(path).iter("testcase"):
        suite = case.get("classname")
        counts.setdefault(suite, Counter())["failed" if case.find("failure") is not None else "passed"] += 1
        if case.find("failure") is not None:
            failures.append(f"{suite}::{case.get('name')}")
    return counts, failures


def main():
    import game.gm as gm
    from game.immutable_valid_response import run_preserve_if_valid
    from tests.test_pr_cw_social_context_projection import ADVERSARIAL_OUTPUTS, NEGATIVE_CONTROLS, POSITIVE_CONTROLS, social_request

    projector = gm._project_harmless_social_provider_context
    fixtures, exact = [], {}

    def add(name, label, before, after):
        b_payload, a_payload = (json.loads(m[1]["content"]) for m in (before, after))
        b_chars, a_chars = (sum(len(m["content"]) for m in msgs) for msgs in (before, after))
        b_bytes, a_bytes = (sum(len(m["content"].encode("utf-8")) for m in msgs) for msgs in (before, after))
        projection = a_payload.get("provider_context_projection") or {}
        row = {
            "fixture": name, "label": label,
            "baseline_prompt_bytes": b_bytes, "reduced_prompt_bytes": a_bytes,
            "absolute_byte_reduction": b_bytes - a_bytes,
            "percentage_byte_reduction": round(100 * (b_bytes - a_bytes) / b_bytes, 2),
            "baseline_estimated_tokens_char_div_4": round(b_chars / 4),
            "reduced_estimated_tokens_char_div_4": round(a_chars / 4),
            "estimated_token_savings_char_div_4": round((b_chars - a_chars) / 4),
            "baseline_user_payload_bytes": len(before[1]["content"].encode("utf-8")),
            "reduced_user_payload_bytes": len(after[1]["content"].encode("utf-8")),
            "baseline_hash": sha(dump(before)), "after_hash": sha(dump(after)),
            "baseline_payload_hash": sha(before[1]["content"]), "after_payload_hash": sha(after[1]["content"]),
            "projection_selected": bool(projection.get("selected")),
            "eligibility_reason": projection.get("reason", "full context: missing or ineligible authority metadata"),
            "retained_sections": sorted(a_payload), "omitted_sections": sorted(set(b_payload) - set(a_payload)),
            "compacted_sections": projection.get("compacted_sections", []),
        }
        fixtures.append(row)
        exact[name] = {"baseline_messages": before, "reduced_messages": after}

    cq_path = ROOT / "artifacts/pr_cq_live_finalization/evidence/T1/provider_request_generation_1.json"
    before = json.loads(cq_path.read_text(encoding="utf-8"))["provider_input"]
    after = [before[0], {"role": "user", "content": dump(projector(json.loads(before[1]["content"]), provider_response_contract="narration_only"))}]
    add("PR-CQ-T1", "Saved Guard Captain preference", before, after)
    for label, npc_id, player, history in POSITIVE_CONTROLS:
        with patch.object(gm, "_project_harmless_social_provider_context", lambda payload, **kwargs: payload):
            before, *_ = social_request(player, npc_id=npc_id, history=history)
        after, *_ = social_request(player, npc_id=npc_id, history=history)
        add(label, player, before, after)
        assert fixtures[-1]["projection_selected"] and fixtures[-1]["absolute_byte_reduction"] > 0
    for probe in ("P1", "P2", "P3"):
        path = OUT / "generated_baseline/evidence" / probe / "provider_request_generation_1.json"
        before = json.loads(path.read_text(encoding="utf-8"))["provider_input"]
        payload = json.loads(before[1]["content"])
        assert projector(payload, provider_response_contract=gm._provider_response_contract_from_payload(payload)) is payload
        add(probe, "Historical full-context fallback", before, before)
        (OUT / "generated_after/evidence" / probe / "provider_request_generation_1.json").write_text(dump({"provider_input": before}), encoding="utf-8")
    for player in (
        "Captain, what do you know about the missing patrol?",
        "Guard Captain, which secret guard schedule do you prefer?",
        "Guard Captain, which suspect do you think committed the murder?",
        "Guard Captain, which restricted entrance would you choose?",
    ):
        with patch.object(gm, "_project_harmless_social_provider_context", lambda payload, **kwargs: payload):
            before, *_ = social_request(player)
        after, *_ = social_request(player)
        assert before == after
        add(f"negative_{len(fixtures)}", player, before, after)
    write("PR-CW_before_after_payloads.json", json.dumps({
        "decision": DECISION, "live_provider_calls": 0,
        "measurement": "UTF-8 bytes and char/4 estimates summed over all effective message content; no transport overhead",
        "tokenizer": "tiktoken unavailable; no dependencies installed",
        "hash_algorithm": "SHA-256; message hashes cover JSON serialization, payload hashes cover exact user content",
        "fixtures": fixtures, "exact_payloads": exact,
    }, indent=2, ensure_ascii=False))
    with (OUT / "PR-CW_prompt_measurements.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fixtures[0]))
        writer.writeheader()
        writer.writerows({k: ";".join(v) if isinstance(v, list) else v for k, v in row.items()} for row in fixtures)

    authority = []
    for label, text, expected_valid in ADVERSARIAL_OUTPUTS:
        audits, facing = [], []
        for enabled in (False, True):
            with patch.object(gm, "_project_harmless_social_provider_context", projector if enabled else lambda payload, **kwargs: payload):
                _, resolution, scene, world, session = social_request(POSITIVE_CONTROLS[0][2])
            candidate = gm._safe_json(dump({"narration": text}), require_structured_claims=True, provider_response_contract="narration_only")
            sealed = run_preserve_if_valid(candidate, regenerate=None, resolution=resolution, player_text=POSITIVE_CONTROLS[0][2], scene=scene, world=world, session=session)
            audits.append(sealed["metadata"]["hard_validation_attempt_1"])
            facing.append(sealed["player_facing_text"])
        assert audits[0] == audits[1] and audits[0]["hard_valid"] is expected_valid
        authority.append({"family": label, "candidate": text, "full_context_audit": audits[0], "reduced_context_audit": audits[1], "final_outputs": facing, "inherited_acceptance_gap": expected_valid})
    write("adversarial_results.json", json.dumps(authority, indent=2))

    counts, failures = xml_results(OUT / "final_regression.xml")
    disabled_counts, disabled_failures = xml_results(OUT / "full_context_regression.xml")
    independent, independent_failures = xml_results(OUT / "authored_independent.xml")
    assert set(failures) == set(disabled_failures)
    assert independent["tests.test_authored_knowledge_realization"] == {"passed": 14, "failed": 2}
    assert counts["tests.test_turn_pipeline_shared"] == {"passed": 41, "failed": 24}
    inherited_suites = {"tests.test_authored_knowledge_realization", "tests.test_turn_pipeline_shared"}
    focused = sum(v["passed"] for k, v in counts.items() if k not in inherited_suites)
    assert all(v["failed"] == 0 for k, v in counts.items() if k not in inherited_suites)
    results = "\n".join(f"- `{name}`: {row['passed']} passed / {row['failed']} failed" for name, row in sorted(counts.items()))
    regression = f"""# PR-CW Regression Results

Final focused regression: {focused} passed, no failures. The combined run has
303 passed / 27 failed. A projection-disabled comparison reproduces exactly the
same failure identities. Authored knowledge independently remains 14 passed / 2 failed;
in the combined ordering it is 13 passed / 3 failed. The additional order-sensitive
`test_retry_fallback_prefers_authored_topic_over_ignorance` failure also occurs with
projection disabled. Shared pipeline remains 41 passed / 24 failed, matching Phase 1.
No new reproducible projection regression observed.

{results}

Failure identities in the combined run (also present with projection disabled):

""" + "\n".join(f"- `{f}`" for f in failures) + "\n"
    write("PR-CW_regression_results.md", regression)
    write("PR-CW_regression_baseline.md", """# PR-CW Regression Baseline

HEAD at start: d31beb7d73dd4fda0f22184a6a69b947b5f470ff.
The initial worktree had 67 modified tracked files plus untracked evidence/tests.
HEAD, status, and relevant diff were inspected before implementation. The dirty worktree
was preserved without reset, unrelated removal, or production-save modification.
Bundled final status/diff are labeled final, not a pristine PR-CW-only diff.

Phase 1: PR-BT 8 passed after one Windows evidence-directory cleanup retry;
PR-CT 3 passed; PR-CP 9 passed; PR-CR recovery/C18/C19 54 passed.
Authored knowledge 14 passed / 2 failed. Shared pipeline 41 passed / 24 failed.
No authority or prompt-contract gate regression before implementation.
Live provider calls: 0.
""")
    eligibility = """Existing authoritative metadata must select `social` with an established ordinary
contract. The social result must explicitly permit harmless subjective dialogue, have
a resolved NPC target, claim-only speech, no objective fact authority, and no durable
mutation. The recipe must select narration-only incidental dialogue without declarations,
inference, unresolved qualifiers, authored answer topics, or permitted mutations.
One allowed speaker must match the primary speaker, active NPC, social NPC, and contract
interlocutor. Scene, response policy, and dialogue plan must be present. Checks, state/world
changes, discoveries, transitions, active combat, opening, and arrival exclude projection.
Missing or malformed required metadata uses full context. Existing resolver results are
consumed; no new keyword classifier is introduced. Historical P2 lacks explicit harmless
permission and therefore remains full context. Current Baker requests are eligible.
"""
    write("PR-CW_eligibility_contract.md", "# PR-CW Eligibility Contract\n\n" + eligibility)
    inventory, removals = {}, {}
    for pair in exact.values():
        b, a = (json.loads(pair[k][1]["content"]) for k in ("baseline_messages", "reduced_messages"))
        for key in b:
            if key not in a:
                classification, handling = "E - inactive/irrelevant", "Omitted after eligibility checks"
            elif b[key] != a[key]:
                classification, handling = "D - conditional/duplicate", "Compacted; authority retained separately"
                if isinstance(b[key], dict) and isinstance(a[key], dict):
                    removals.setdefault(key, set()).update(set(b[key]) - set(a[key]))
            else:
                classification, handling = "F - uncertain or required", "Retained exactly"
            inventory.setdefault(key, (classification, handling))
    for key in ("player_input", "recent_log", "selected_conversational_memory", "active_interlocutor"):
        inventory[key] = ("A - generation/continuity", "Retained exactly")
    for key in ("scene", "speaker_selection", "response_policy", "resolution_contract", "gm_resolution_decision", "decision_facing_answer_recipe", "narration_visibility", "dialogue_social_plan"):
        inventory[key] = ("C - generation and validation", "Retained exactly")
    matrix = "# PR-CW Context Dependency Matrix\n\n| Surface | Classification | Handling |\n|---|---|---|\n" + "\n".join(f"| `{k}` | {v[0]} | {v[1]} |" for k, v in sorted(inventory.items()))
    matrix += "\n\nRemoved nested fields inspected in controls:\n\n" + "\n".join(f"- `{k}`: {', '.join(sorted(v))}" for k, v in sorted(removals.items()))
    matrix += "\n\nFull engine state, CTIR, and deterministic validator inputs remain outside this projection. Duplicate public/resolution/debug packet branches remain in the engine; top-level scene, resolution, decision, speaker, memory, and policy retain generation constraints. Narrative-role derivation telemetry and empty outcome scaffolding are compacted. Nonempty lead, inventory, faction, NPC, and world records are retained conservatively.\n"
    write("PR-CW_context_dependency_matrix.md", matrix)
    table = "| Fixture | Before Bytes | After Bytes | Reduction |\n|---|---:|---:|---:|\n" + "\n".join(f"| {r['fixture']} | {r['baseline_prompt_bytes']} | {r['reduced_prompt_bytes']} | {r['percentage_byte_reduction']}% |" for r in fixtures)
    write("PR-CW_implementation_report.md", f"""# PR-CW Implementation Report

Decision: {DECISION}.
One projection in `game.gm.build_messages` reduces provider context after existing envelope
selection and instruction deduplication. Full state and validators remain unchanged.
Scene, NPC, history, policy, GM decision, recipe, and authority constraints are retained;
inactive opening/progression scaffolding and duplicate planner branches are compacted.

{table}

Bytes sum effective system/user content. Developer messages: none. Tokens use char/4
estimates because tiktoken is unavailable; no dependencies installed or live savings claimed.
Five adversarial families are already accepted by full-context validation and remain accepted
with reduced context. This inherited gap prevents the requested universal rejection proof.
No validator was altered. Implementation is reviewable but not certified for rollout here.
Live provider calls: 0. Production saves unchanged. Dirty worktree preserved.
""")
    write("PR-CW_prompt_contract_tests.md", f"""# PR-CW Prompt Contract Tests

39 PR-CW tests pass: five current-resolver positive controls; historical P1/P2/P3 fallback
hashes in one test; ambiguous synthetic control; {len(NEGATIVE_CONTROLS)} metadata controls;
four real factual/restricted requests; eight adversarial equivalence checks; smuggled declarations.
Guard Captain preference, Baker preference, subjective opinion, follow-up, and recent-history
dialogue all select projection, retain context, and accept deterministic harmless speech.
Metadata controls cover all fourteen requested negative categories plus opening, arrival,
active combat, speaker mismatch, and malformed inference. These are distinguished from
end-to-end resolver tests and do not imply exhaustive natural-language classification coverage.
""")
    write("PR-CW_adversarial_authority.md", "# PR-CW Adversarial Authority\n\nFull/reduced audits match for all eight candidates.\n\n| Family | Full Context | Reduced Context |\n|---|---|---|\n" + "\n".join(f"| {r['family']} | {'ACCEPTED: inherited gap' if r['inherited_acceptance_gap'] else 'Rejected'} | {'ACCEPTED: inherited gap' if r['inherited_acceptance_gap'] else 'Rejected'} |" for r in authority) + "\n\nSmuggled declarations reject as `unexpected_declared_claims`. Exact candidates, audits, and final outputs are in `adversarial_results.json`. Five inherited acceptance gaps prevent decision A despite regression equivalence. Existing validators were neither weakened nor repaired.\n")
    retained = json.loads(exact["baker_preference"]["reduced_messages"][1]["content"])
    sizes = sorted(((k, len(dump(v).encode("utf-8"))) for k, v in retained.items()), key=lambda row: -row[1])
    write("PR-CW_remaining_context_inventory.md", "# PR-CW Remaining Context Inventory\n\nRetained Baker sections by serialized bytes:\n\n" + "\n".join(f"- `{k}`: {n} bytes" for k, n in sizes) + "\n\nUnrelated NPC, inventory, faction, and full-state deletion was not attempted. Authority gaps require separate assurance work before claiming comprehensive safety.\n")
    files = [name.replace(".", "/") + ".py" for name in counts]
    write("focused_tests.txt", "Final command: .\\.venv\\Scripts\\python.exe -m pytest " + " ".join(files) + " -o addopts= -q --tb=short --basetemp=codex_pytest_tmp_pr_cw_review --junitxml=artifacts/pr_cw_social_context_projection/final_regression.xml\n" + f"Result: {focused} focused passed; combined 303 passed / 27 failed. Projection-disabled comparison preserves identical failure IDs. Independent authored 14 passed / 2 failed; shared 41 passed / 24 failed. XML evidence included.\n")
    write("final_worktree_status.txt", subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    write("final_gm_diff_includes_inherited_changes.patch", subprocess.run(["git", "diff", "--", "game/gm.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    write("changed_files.txt", "PR-CW: game/gm.py (projection helpers and boundary call); tests/test_pr_cw_social_context_projection.py; artifacts/pr_cw_social_context_projection/*; handoff/CURRENT_REVIEW.md; handoff/REVIEW_MANIFEST.json; handoff/CURRENT_REVIEW.zip.\nFull gm.py diff includes inherited edits and is not a PR-CW-only patch.\n")
    review = f"""# CURRENT_REVIEW

PR-CW
MODE: HARMLESS SOCIAL CONTEXT PROJECTION
LIVE CALLS: 0
PR-CV inherited decision: A - POLICY CONTRACT RECONCILED

Regression baseline: PR-BT 8 passed; PR-CT 3 passed; PR-CP 9 passed; PR-CR/C18/C19
54 passed; authored 14 passed / 2 failed; shared 41 passed / 24 failed.

Eligibility contract:
{eligibility}

Implemented projection: one build_messages helper compacts mechanical resolution, turn packet,
narrative plan, and inactive opening/progression fields. Full authoritative state, CTIR,
validators, retry, persistence, response envelope, and output schema remain unchanged.

Prompt measurements:

{table}

Byte counts include effective system/user content. Tokens are char/4 estimates, not live claims.
Authority integrity: matching full/reduced audits; five inherited acceptance gaps prevent full
safety proof. Objective tax rules, unsupported certainty, state changes, and declarations reject.
Ineligible path behavior: P1/P2/P3 and four real factual/restricted requests match exactly;
19 metadata controls verify conservative fallback.

Shared pipeline before: 41 passed / 24 failed
Shared pipeline after: 41 passed / 24 failed
Focused regression: {focused} passed, including 39 PR-CW tests.
Authored independently: 14 passed / 2 failed. Combined ordering: 13 passed / 3 failed,
also reproduced with projection disabled. No new reproducible projection failure observed.

PR-CW decision: {DECISION}
Recommended next step: independently review the projection and inherited validator gaps.
Resolve authority assurance separately before promoting to decision A.
"""
    handoff = ROOT / "handoff"
    (handoff / "CURRENT_REVIEW.md").write_text(review, encoding="utf-8")
    bundle = [ROOT / "game/gm.py", ROOT / "tests/test_pr_cw_social_context_projection.py"] + [p for p in OUT.iterdir() if p.is_file()]
    manifest = {"pr": "PR-CW", "decision": DECISION, "live_calls": 0, "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle)}}
    (handoff / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(handoff / "CURRENT_REVIEW.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(handoff / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        archive.write(handoff / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for path in sorted(bundle):
            archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
    print(json.dumps({"decision": DECISION, "focused_passed": focused, "measurements": [{k: row[k] for k in ("fixture", "baseline_prompt_bytes", "reduced_prompt_bytes", "percentage_byte_reduction")} for row in fixtures]}, indent=2))


if __name__ == "__main__":
    main()
