"""Local summary of saved probe artifacts. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "20261003T181221Z"


def main() -> None:
    for probe_dir in sorted(p for p in ROOT.glob("turn_*") if p.is_dir()):
        record = json.loads((probe_dir / "turn_record.json").read_text(encoding="utf-8"))
        generations = json.loads((probe_dir / "generations.json").read_text(encoding="utf-8"))
        resolution = json.loads((probe_dir / "resolution.json").read_text(encoding="utf-8"))
        meta = resolution.get("metadata") or {}
        contract = meta.get("resolution_contract") or {}
        decision = meta.get("gm_resolution_decision") or {}
        accepted = record.get("accepted_response") or {}
        hard = accepted.get("hard_validation") or {}
        print("=" * 80)
        print(probe_dir.name)
        print("PLAYER:", record.get("player_text"))
        print(
            "KIND:",
            resolution.get("kind"),
            "OP:",
            contract.get("operation"),
            "DIM:",
            contract.get("dimension"),
            "DIMS:",
            contract.get("dimensions"),
        )
        print("EXPECTED:", contract.get("expected_resolution"))
        print("INTERLOCUTOR:", contract.get("interlocutor_id"), "TARGET:", contract.get("target_ref"))
        print("CONTRACT_KEYS:", sorted(contract.keys()))
        print(
            "DECISION:",
            bool(decision),
            decision.get("outcome_classification"),
            decision.get("resolution_method"),
            decision.get("persistence_policy"),
        )
        print("MUTATIONS:", json.dumps(decision.get("permitted_state_mutations"), default=str)[:500])
        print("UNRESOLVED:", decision.get("unresolved_consequential_questions"))
        facts = decision.get("proposed_facts") or []
        print("FACTS", len(facts))
        for fact in facts:
            identity = fact.get("semantic_identity") or {}
            print(
                " -",
                fact.get("provenance"),
                fact.get("authority"),
                fact.get("persistence"),
                "|",
                str(fact.get("text") or "")[:160],
            )
            if identity:
                print(
                    "   ",
                    identity.get("kind"),
                    identity.get("subject"),
                    identity.get("relation"),
                    identity.get("value"),
                    identity.get("polarity"),
                    identity.get("target_scene_id"),
                )
        for constraint in decision.get("narration_constraints") or []:
            print("  C:", constraint)
        obligation = meta.get("interaction_obligation") or {}
        print("OBLIGATION:", {k: obligation.get(k) for k in ("kind", "target", "interlocutor_id", "subject", "requested_outcome", "resolution_mode")})
        print("SOCIAL:", json.dumps(resolution.get("social"), default=str)[:400] if resolution.get("social") else None)
        for index, generation in enumerate(generations, start=1):
            print(
                f"--- GEN {index} purpose={generation.get('purpose')} retry={generation.get('retry_attempt')} reason={generation.get('retry_reason')}"
            )
            print(generation.get("player_facing_text") or "")
            prompt = generation.get("prompt") or {}
            print(
                "PROMPT decision",
                prompt.get("contains_gm_resolution_decision"),
                "contract",
                prompt.get("contains_resolution_contract"),
                "chars",
                prompt.get("user_chars"),
            )
        audit = hard.get("gm_resolution_decision_audit") or {}
        print("ACCEPTED", accepted.get("provenance"), "hard", hard.get("hard_valid"), "reasons", hard.get("reasons"))
        print("AUDIT keys", list(audit)[:20] if isinstance(audit, dict) else None)
        if isinstance(audit, dict):
            print("AUDIT hard", audit.get("hard_valid"), "reasons", json.dumps(audit.get("reasons") or audit.get("failures") or audit, default=str)[:1500])
        print("EMITTED:", record.get("emitted_narration"))
        print(
            "SCENE",
            record.get("committed_active_scene_id"),
            "resolved",
            resolution.get("resolved_transition"),
            "target",
            resolution.get("target_scene_id"),
        )
        ledger = record.get("committed_bounded_improvisation") or {}
        print("LEDGER", len(ledger.get("entries") or []), "REJECTED", len(ledger.get("rejected") or []))
        for entry in (ledger.get("entries") or [])[:6]:
            print("  entry", json.dumps(entry, default=str)[:300])
        focus = record.get("committed_discourse_focus") or {}
        print("FOCUS", json.dumps(focus, default=str)[:800])


if __name__ == "__main__":
    main()
