# NPC Conversation

Current model: isolated social actions plus active interaction context, topic lookup, deterministic reply planning, model narration, and final social-emission validation.

Evidence:

- Social parser supports `question` and `social_probe` (`game/social.py:62`, `game/social.py:72`).
- `resolve_social_action()` owns target binding and sets active social target (`game/social.py:3834`, `game/social.py:4189`).
- Interaction context stores active target and mode (`game/interaction_context.py:1000`, `game/interaction_context.py:1018`).
- Follow-up/relevance utilities exist (`game/social.py:960`, `game/social.py:1564`, `game/social.py:2712`).

Missing: a sustained dialogue object with topic stack, unresolved questions, commitments, and implied addressee routing before interpretation rejection.

Conclusion: sustained NPC conversation is possible for recognized social turns, but it is not robust for ordinary follow-up language unless the message binds to an explicit/implicit social target and survives bridge validation.
