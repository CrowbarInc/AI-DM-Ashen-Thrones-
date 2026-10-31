# PR-BR representative semantic traces

HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

## Level 2 — utterance treated as the target

`artifacts/pr_br_level2/20260928T002628Z` (7 turns, 9 model calls).

Smell follow-up "This close, what does it smell like?" built target `explicit_player` equal to the whole sentence. Discourse ref was null. The same pattern hit wear, "Where did you hear that?", and "How sure are you?". "I follow that lead" stayed `follow` / unresolved because no lead was stored.

## Level 2 remainder — pronoun repair held

`artifacts/pr_br_level2/20260928T002857Z` (3 turns, 3 model calls).

"What does it smell like?" after inspecting the cloth: provenance `inherited_discourse`, target "cloth itself", dimension smell. The prompt constraint named the cloth. The visible line was an inability about smell, not a description. Budget exhausted at 10.

## Smoke 2 — contract right, emission wrong

`artifacts/pr_br_smoke/20260928T003623Z` (14 turns).

- Wear question: contract `perceive` / `use` / inherited. Visible text pasted the question into "No reliable source here can verify …". Evaluator PASS.
- Smell question: contract smell / inherited. Visible text addressed ink, damp, and smoke. Held.
- "Take me as far as the gate allows toward that place.": contract `act`. Visible text repeated the Thoran rumor.
- "What can I see from here…": contract `perceive` / appearance. Visible text was a blocked crossing.
- Confidence question: contract `confidence`. Visible text pasted the question. Evaluator PASS.

Clusters: echoed question scored as coverage; action contracts emitted as rumor or stock social lines; source follow-ups with no stored claim.
