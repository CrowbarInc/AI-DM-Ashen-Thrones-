import json
from pathlib import Path

turn = json.loads(Path("persona_b/turns/turn_09.json").read_text(encoding="utf-8"))
keys = [
    "accepted_provenance",
    "accepted_response_text",
    "accepted_immutable",
    "final_emitted_response",
    "accepted_emitted_exact_match",
    "accepted_emitted_semantic_match",
    "generation_attempt_1",
    "generation_attempt_count",
    "regeneration_invoked",
    "best_safe_candidate",
    "final_selected_candidate",
    "best_safe_invalidation",
    "candidate_transitions",
    "gm_tags",
]
out = {k: turn.get(k) for k in keys}
out["gen_calls"] = turn.get("turn_generation_calls")
Path("b09_meta.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", Path("b09_meta.json").stat().st_size)
