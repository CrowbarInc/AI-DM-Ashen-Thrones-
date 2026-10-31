import json
from pathlib import Path

root = Path("artifacts/pr_br_full_gate/20261002T021950Z")
files = []

def add(path, role, why):
    files.append(
        {
            "path": path.replace("\\", "/"),
            "role": role,
            "why": why,
            "behavioral_evidence": True,
            "human_review_required": True,
        }
    )

add(
    "docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md",
    "audit",
    "Campaign report, including the full 4x10 gate section and the C18-C20 baseline.",
)
add(
    "artifacts/pr_br_full_gate/20261002T021950Z/audit.md",
    "audit",
    "Gate audit: contracts, manual review, authority, discourse, and the decision.",
)
add(
    "artifacts/pr_br_full_gate/20261002T021950Z/freeze.json",
    "provenance",
    "HEAD, worktree, model names, and file hashes frozen before Session A.",
)
for name in ("persona_a.md", "persona_b.md", "persona_c.md", "persona_d.md"):
    add(
        f"artifacts/pr_br_full_gate/personas/{name}",
        "persona",
        "Player persona. No contracts, validators, or prior-session findings.",
    )
for pid, label in (
    ("persona_a", "Persona A direct/practical"),
    ("persona_b", "Persona B social/curious"),
    ("persona_c", "Persona C exploratory"),
    ("persona_d", "Persona D action-oriented"),
):
    base = f"artifacts/pr_br_full_gate/20261002T021950Z/{pid}"
    add(f"{base}/visible.md", "transcript", f"{label} player-visible opening and ten turns.")
    add(f"{base}/isolation.json", "isolation", f"{label} session id and empty discourse before Turn 1.")
    add(f"{base}/opening.json", "opening", f"{label} product opening text.")
    add(f"{base}/review_index.json", "contracts", f"{label} contracts, routing, hard validation, and discourse slots.")
    add(f"{base}/preflight.json", "provenance", f"{label} HEAD and model configuration at session start.")
    add(f"{base}/summary.json", "accounting", f"{label} generation and interpretation counts.")
    add(f"{base}/generation_calls.json", "candidates", f"{label} opening and gameplay model texts.")
    add(f"{base}/interpretation_calls.json", "routing", f"{label} structured interpretation outputs.")
    add(f"{base}/inbox.jsonl", "transcript", f"{label} turn-by-turn player lines.")
    for n in range(1, 11):
        add(
            f"{base}/turns/turn_{n:02d}.json",
            "turn",
            f"{label} turn {n} candidate, contract, validation, and emission.",
        )

config = {
    "campaign_id": "pr-br-full-4x10-synthetic-gate",
    "campaign_name": "PR-BR — Full 4×10 Synthetic Playability Gate",
    "campaign_date": "2026-10-01",
    "purpose": "Release-candidate 4x10 synthetic playability gate after Continuation 20. No behavior changes. No repair. No rerun. PR-BR remains open.",
    "objective_status": "OPEN",
    "executive_summary": "Four isolated frontier-gate sessions, 40/40 gameplay turns, no product edits. Final manual PASS 32/40. Initial manual PASS 32/40. Contracts: 6 correct, 18 partial, 16 incorrect. Partial contracts all still played. Incorrect contracts failed play on 6 turns. Accepted text matched emitted text on all 40 turns. Post-seal mismatches: 0. Unsupported consequential entities: 0. Stale binding fallbacks: 0. Rejected-response commits: 0. Structured-output leaks: 0. Two recurrent gameplay mechanisms: ordinary inspections replaced by one wear sentence (C10, D3), and a sealed speaker who is not the person addressed (B2, B9, C8). Sentence fragments were bound as incidental people in every persona. One roster name, Eldrin Voss, was emitted as a posted fact. DECISION: PR-BR SYNTHETIC GATE FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN. HUMAN PLAYTEST: NOT AUTHORIZED. PR-BR: STILL OPEN. HEAD d31beb7d73dd4fda0f22184a6a69b947b5f470ff.",
    "primary_report": "docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md",
    "evidence_packets": [],
    "changes": {
        "production": [],
        "validation": [],
        "tooling": [
            "artifacts/pr_br_full_gate/run_gate_session.py is a validation harness only. It does not change gameplay behavior."
        ],
        "documentation": [
            "docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md gains the full 4x10 gate section."
        ],
        "generated_artifacts": [
            "artifacts/pr_br_full_gate/20261002T021950Z holds four isolated sessions, transcripts, contracts, and the audit."
        ],
    },
    "testing": {
        "focused": "Not a deterministic band. This cycle is the 4x10 synthetic gate.",
        "broader": "Not run.",
        "full_suite": "Not run.",
        "runtime_validation": "40/40 gameplay turns in four isolated sessions. Opening plus chat through the product API. No early stop. No rerun.",
        "model_runtime_boundary": "Opening generation 4. Gameplay initial 40. Gameplay retry 8. Interpretation 15. Product synthetic-player calls 0. Evaluator model calls 0. Operator player-selection calls outside the product: 40.",
        "new_regressions": "No product patch. Live manual failures: 8/40 final. Recurrent: wear-sentence safe fallback; wrong speaker including one catalog grimace.",
        "pre_existing_failures": "Not re-scored. The gate did not replay prior failure strings.",
    },
    "decisions_requiring_human_review": [
        "The manual pass count is 32/40, at the approximate strong-pass line, while two mechanisms recurred across personas. The decision is FAILED — MULTIPLE SYSTEMIC DEFECTS REMAIN rather than a pass.",
        "A reviewer may instead treat the wear-sentence pair as the only narrow defect and the wrong-speaker turns as isolated. That would be decision B, still not a pass.",
        "PR-BR remains open. Do not start PR-BS. Do not implement a repair from this cycle. Human playtest is not authorized.",
    ],
    "known_problems": {
        "campaign_specific": [
            "C10 and D3 emitted the same safe line about the wear after both inspection candidates were rejected as interaction-incomplete.",
            "B2 sealed a captain reply to a player who was still questioning the runner.",
            "B9 replaced the generated answer with a catalog grimace before the immutable seal.",
            "C8 turned a look into stranger speech.",
            "Every persona stored at least one sentence fragment as an incidental person.",
            "D1 stated Eldrin Voss as the roster name of the missing patrol leader.",
        ],
        "pre_existing": [
            "The local evaluator marked 16 manually acceptable turns as failures and passed 5 manual failures."
        ],
    },
    "missing_concepts": [],
    "does_not_prove": [
        "Does not prove the stack is ready for a human playtest.",
        "Does not prove contract correctness. Correct contracts were 6/40.",
        "Does not authorize a repair or Continuation 21.",
        "Does not prove the authority classifier catches every consequential sentence. It missed the Eldrin Voss roster line.",
    ],
    "recommended_next_step": "External review. Do not repair, rerun, or playtest with a human from this cycle. Do not close PR-BR. Do not start PR-BS.",
    "supporting_files": files,
}
Path("artifacts/pr_br_full_gate/20261002T021950Z/handoff_config.json").write_text(
    json.dumps(config, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print("files", len(files))
