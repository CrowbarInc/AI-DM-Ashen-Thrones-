# PR-PLAY-72 — 08 AMBIGUITY HANDLING

Ambiguous pronouns, multiple public aliases, unknown targets, negated attempts, and qualified/multiple action requests produce concise clarification without invoking a resolver. No persistent PR72 clarification state is introduced. Existing clarification handling remains outside this opt-in leaf. Tests compare session, world, character and combat for exact equality on PR72 non-executing turns; transcript writes are expected. Unknown or hidden target names are not echoed as established entities.
