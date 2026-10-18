# PR-CB Helpfulness Investigation

MODE: BOUNDED DIAGNOSTIC / PROMPT AND CONTEXT AUDIT
LIVE CALLS: 0
PR-CA inherited decision: B - READY WITH NON-BLOCKING QUALITY LIMITATIONS
PR-CB decision: F - MULTIPLE COUPLED CAUSES

The strongest explanation is engine-derived refusal guidance coupled to an under-scoped incidental-dialogue recipe. This is more specific than attributing the result to model quality alone. The social resolver converts absence of an authored topic into refusal for ordinary questions; the provider receives that refusal repeatedly even though narration validation accepts ordinary answers as NPC claims. The recipe simultaneously permits transient dialogue and discourages durable preference, with examples focused on refusal/hesitation rather than affirmative subjective answers. No authority or prompt repair was implemented.

Confirmed mechanisms: T1-T3 mechanical_resolution.social.reply_kind is refusal; narration_obligations.active_npc_reply_kind and structural prompt instructions repeat it; the final instruction requests refusal, uncertainty, or inability. Deterministic _infer_reply_expectation reproduces refusal/refusal/refusal/reaction from the four inputs without conversation history. All 12 ordinary-answer probes pass decision-aware narration, empty declarations, and the immutable lifecycle on the first attempt. The typed authority lane also accepts opinion, food detail, and ordinary personal characterization while rejecting a consequential proposal.

Supported effects: this guidance strongly encourages evasion, and prior evasive snippets help reinforce T2-T4. The exact model response and its invented safety implication are not causally proved by static evidence. No ablation, provider comparison, or live retry was performed.

The architecture supports harmless NPC speech and typed low-consequence improvisation, but the current social resolver and provider projection do not reliably present that permission for an unauthored mundane question. Acceptance does not measure whether a refusal answers the player's practical request. PR-CA's structural pass remains valid; its attribution to model quality alone is incomplete.

Evidence: four complete preserved provider inputs, context_reconstruction_evidence.json, validation_probe_evidence.json, typed_authority_probe_evidence.json, source_excerpt_evidence.json, focused_tests.txt, and offline_probes.txt. Reports use historical provider inputs as primary evidence; source excerpts describe the current working tree, which was already dirty. They are not a historical commit snapshot.
