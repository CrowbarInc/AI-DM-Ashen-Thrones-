# Bounded Prompt Repair Inventory

This gate changed only prompt guidance in game/gm.py and game/prompt_context.py.
The worktree already contained broader PR-BR/PR-BS/PR-BT changes. No full git diff
is represented as the gate repair. A clean pre-gate source snapshot is unavailable.

## game/gm.py

The action-declaration instruction now explicitly contains:
`resolved_exploration_action`, `scene_transition_already_occurred`, third person,
quoted in-character speech, and the prohibition on restating player input.
The validator-voice instruction now explicitly contains `Spoiler safeguard` and
`hidden_facts`. The question/momentum line now includes direct answer (first
sentence), `scene_momentum:<kind>`, and `consequence_or_opportunity`.

## game/prompt_context.py

Added compact policy anchors for answer completeness/response delta, typed
uncertainty inputs, anti-railroading distinctions and commitment exception,
context-separation priority, narration purity, and scene anchoring. The scoped
addition-only diff is repair_policy_anchors.diff. It is an excerpt, not a complete
apply-ready patch for the whole repair.

The active-NPC obligation line now reads:
`If narration_obligations.should_answer_active_npc, answer/refuse in active NPC voice rather than empty stalling.`

No runtime validator, accepted-response mechanism, authority object, policy
object, test, or turn packet was changed during the gate. Full current prompt
sources are included so reviewers can inspect the surrounding implementation.
The restored guidance passes all 212 prompt cases but increases payload sizes;
the existing size test remains red and is explicitly reported.
