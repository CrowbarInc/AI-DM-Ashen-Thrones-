import json
from pathlib import Path

turn = json.loads(Path("persona_b/turns/turn_09.json").read_text(encoding="utf-8"))
# print top-level keys and nested metadata-like fields without evaluation
skip = {"evaluation", "contract", "discourse_focus", "persistence", "authority_generated", "authority_emitted", "authority_retry", "interpretation_proposal", "entity_binding", "turn_interpretation_calls"}
summary = {}
for k, v in turn.items():
    if k in skip:
        continue
    if isinstance(v, (str, int, float, bool)) or v is None:
        summary[k] = v
    elif isinstance(v, list) and k not in {"turn_generation_calls"}:
        summary[k] = v
    elif isinstance(v, dict) and k in {"target_ref"}:
        summary[k] = v
Path("b09_flat.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)[:20000], encoding="utf-8")
print("keys", sorted(turn.keys()))
