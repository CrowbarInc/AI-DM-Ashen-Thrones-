"""Offline PR-CB evidence reconstruction and deterministic probes. No providers."""
from __future__ import annotations

import hashlib
from copy import deepcopy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "artifacts/pr_ca_dialogue_continuity/evidence"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main():
    from game.gm import _safe_json
    from game.immutable_valid_response import validate_generated_response, run_preserve_if_valid
    from game.gm_resolution_decision import DECISION_METADATA_KEY, validate_declared_claims_against_decision
    from game.social import _infer_reply_expectation
    from game.bounded_improvisation import validate_bounded_improvisation_proposal

    rows = []
    cost = []
    probes = []
    samples = [
        "I usually keep a rye loaf for myself.",
        "For someone new, I'd recommend the wheat loaf.",
        "I don't have a favorite, but the barley bread is popular.",
    ]
    for turn in ("T1", "T2", "T3", "T4"):
        path = SOURCE / turn / "provider_request_attempt_generation_1.json"
        request = read(path)
        messages = request["provider_input"]
        payload = json.loads(messages[1]["content"])
        digest = read(SOURCE / turn / "digest.json")
        # Preserved inputs contain game context, not credentials or HTTP headers.
        write(f"{turn}_effective_provider_input_redacted.json", request)
        rows.append({
            "turn": turn, "source": str(path.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "roles": [m["role"] for m in messages],
            "player": payload["player_input"], "output": digest["emitted"],
            "scene": payload["scene"], "world": payload["world"],
            "visibility": payload["narration_visibility"],
            "social_context": payload["social_context"],
            "dialogue_social_plan": payload["dialogue_social_plan"],
            "narration_obligations": payload["narration_obligations"],
            "mechanical_resolution": payload["mechanical_resolution"],
            "recent_log": payload["recent_log"],
            "selected_conversational_memory": payload["selected_conversational_memory"],
            "recipe": payload["decision_facing_answer_recipe"],
            "envelope": read(SOURCE / turn / "envelope_selection.json"),
            "validation": read(SOURCE / turn / "validation.json"),
            "offline_reply_expectation": _infer_reply_expectation(
                payload["mechanical_resolution"]["kind"],
                prompt=payload["player_input"], raw_player_text=payload["player_input"],
                topic_revealed=False, requires_check=False),
        })
        sizes = {k: len(json.dumps(v, ensure_ascii=True)) for k, v in payload.items()}
        system_chars = len(messages[0]["content"])
        total = system_chars + len(messages[1]["content"])
        cost.append({"turn": turn, "input_tokens_actual": digest["input_tokens"],
                     "system_chars": system_chars, "user_chars": len(messages[1]["content"]),
                     "fields": [{"field": k, "chars": n, "share_percent": round(100*n/total, 2),
                                 "token_estimate_char_proportional": round(digest["input_tokens"]*n/total)}
                                for k, n in sorted(sizes.items(), key=lambda item: -item[1])],
                     "method": "Character shares; tokens apportioned from actual usage. Not exact tokenizer counts; keys, framing and punctuation create residual."})
        for sample in samples:
            narration = 'The baker says, "' + sample + '"'
            parsed = _safe_json(json.dumps({"narration": narration}), require_structured_claims=True,
                                provider_response_contract="narration_only")
            def no_regeneration(_feedback):
                raise RuntimeError("Offline probe attempted regeneration; no provider callable exists")
            resolution = deepcopy(payload["mechanical_resolution"])
            resolution.setdefault("metadata", {}).update({
                "resolution_contract": payload["resolution_contract"],
                DECISION_METADATA_KEY: payload["gm_resolution_decision"],
            })
            result = run_preserve_if_valid(
                parsed, regenerate=no_regeneration, resolution=resolution,
                player_text=payload["player_input"], scene=payload["scene"])
            probes.append({"turn": turn, "sample": sample,
                "validator": validate_generated_response(
                    narration, contract=payload["resolution_contract"], decision=payload["gm_resolution_decision"],
                    declared_claims=[], player_text=payload["player_input"],
                    resolution=payload["mechanical_resolution"], present_addressee="baker",
                    authored_corpus="A baker stands beside loaves at a bread stall."),
                "declarations": validate_declared_claims_against_decision([], decision=payload["gm_resolution_decision"]),
                "lifecycle_review": result.get("metadata", {}).get("decision_review"),
                "preserved_text": result.get("player_facing_text"),
                "text_unchanged": result.get("player_facing_text") == narration})
    typed = []
    for kind, category, content in [
        ("npc_claim", "opinion", samples[0]),
        ("incidental_fact", "food_composition", "The darker loaf is popular with travelers."),
        ("incidental_fact", "ordinary_personal_detail", "The baker prefers rye bread."),
        ("consequential_proposal", "quest", "The baker knows the hidden vault."),
    ]:
        proposal = {"kind": kind, "category": category, "content": content, "scope": "scene",
                    "speaker_id": "baker", "epistemic_status": "grounded", "consequence_level": "low"}
        verdict = validate_bounded_improvisation_proposal(proposal, session={}, scene=rows[0]["scene"], world=rows[0]["world"])
        typed.append({"proposal": proposal, "accepted": verdict.accepted, "reasons": verdict.reason_codes,
                      "entry": verdict.entry})
    write("context_reconstruction_evidence.json", rows)
    write("context_cost_evidence.json", cost)
    write("validation_probe_evidence.json", probes)
    write("typed_authority_probe_evidence.json", typed)
    general = []
    for prompt in ["Which dish would you recommend?", "Which fabric do you prefer?", "Where is the hidden vault?"]:
        general.append({"player": prompt, "authored_topic_available": False,
                        "reply_expectation": _infer_reply_expectation(
                            "question", prompt=prompt, raw_player_text=prompt,
                            topic_revealed=False, requires_check=False)})
    write("generic_reply_derivation_controls.json", general)
    assert all(p["validator"]["hard_valid"] and p["declarations"]["hard_valid"] and p["text_unchanged"] for p in probes)
    assert [r["offline_reply_expectation"][1] for r in rows] == ["refusal", "refusal", "refusal", "reaction"]
    assert all(p["accepted"] for p in typed[:3]) and not typed[3]["accepted"]
    assert all(p["lifecycle_review"]["attempt_1"]["gm_resolution_decision_audit"]["hard_valid"] for p in probes)
    assert all(g["reply_expectation"][1] == "refusal" for g in general)
    print("PASS: 12 narration/declaration/lifecycle probes; 4 reply derivations; 4 typed-authority controls. LIVE CALLS: 0")


if __name__ == "__main__":
    main()
