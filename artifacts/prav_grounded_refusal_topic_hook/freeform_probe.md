# PR-AV freeform / generalization probe

Deterministic isolation after the hook repair. Vocabulary is kiln-yard / cedar-wharf, not Frontier Gate stew / patrol / board calibration examples.

The malformed hook is selected by the integrity catalog, not authored by the live model. Live GPT was not required to prove the token decision.

| Case | Player | Hook before | Hook after | Refusal after |
| --- | --- | --- | --- | --- |
| known night | I ask the night porter when the kiln crew actually left. | `night` | `kiln` | about kiln — not about night |
| known step | I step back to the tavern runner and ask who last checked that board. | `step` | `board` | about board — not about step |
| novel movement | I amble past the lamp clerk and ask how many barrels remain. | `amble` | `barrels` | about barrels |
| novel temporal | I ask the lamp clerk this morning how many barrels remain. | `lamp` | `barrels` | about barrels — not about morning/lamp |
| legitimate subject | I ask the lamp clerk about the tarred coils. | (would have been speaker/movement) | `coils` | about coils |
| no trustworthy topic | I ask the lamp clerk. | `lamp` | empty | I won't answer that—not here. |

Engine state on the known refusals stayed `topic_revealed=None`, `reply_kind=refusal`. No invented time, price, count, identity, or redirect was added to make the sentence sound natural.

Sources: `artifacts/prav_grounded_refusal_topic_hook/isolation_before.json`, `isolation_after.json`, `tests/test_grounded_refusal_topic_hook_integrity.py`.
