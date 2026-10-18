# 11 — Source Change Inventory

```json
{
  "game/conversational_continuity.py": {
    "before_sha256": "0ccaf9fc09b8a29639a225226325bdadae58cc01995a648ee070d81a77bf9e6c",
    "after_sha256": "3f5041949f82164d0b687c7452b804a5de4c579c6070307585f394e5651c5aec"
  },
  "game/dialogue_authority.py": {
    "before_sha256": "cdde0d09e1c7d586e95c5c6897dd5c5b3fef008a2ff11bb10992d422f8958427",
    "after_sha256": "7c6b34f212911a6d38a793298bb7bfa4ef42454924a688640b70b5e8e33f3387"
  },
  "game/social.py": {
    "before_sha256": "adfd9e2a021b52a803778efa7a5c229d23c89332626c59676961aa7164be6a9c",
    "after_sha256": "15c8478b663c650d34a56a20f2b08a3d83d43389997a127c1552e29c3eed0173"
  }
}
```

conversational_continuity: reference_subject_tokens, _best_exchange, record_delivered_exchange, _npc_quote, _gm_quote, supplied_clarification, continuity_directive. dialogue_authority: requested_information, topic_supports_requested_information, build_dialogue_authority, select_host_speech. social: _next_topic_to_reveal, resolve_social_action.

Tests extend the existing R2C owner file; historical expected outcomes remain unchanged. tools/validate_pr_eg_r2c_r1.py is a cycle-specific derivative of the preserved R2C live runner. before_sources, sources and diffs separate these edits from the pre-existing dirty worktree.
