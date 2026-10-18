# 03 ORIGINAL FAILURE REPRODUCTION

The original preserved R6 transcript is `artifacts/pr_eg_r6/live_turns.jsonl`, labeled_adversarial turn 14. Its provider performed one interpretation call, no unified plan; speech adoption, API equality, history equality and final seal all passed while the secret leaked.

`reproduction.json` captures the pre-edit deterministic resolver, source world, before/after session, speech and discovery. `baseline_turns.jsonl` reproduces the same utterance through fresh-provider `/api/chat` using preserved pre-edit modules and the same synthetic ADVERSARIAL source fixture. It is an isolated reconstruction, not a claim that a turn-13 save was recovered: the retained R6 save is already post-failure.

First eligibility failure: `_next_topic_to_reveal` accepted the authored secret based on relevance/sufficiency and dropped its policy metadata. Routing excluded “grant me” from the migrated family, exposing this weaker selector. NPC ownership established that Nara knew the password; it did not authorize disclosure. `resolve_social_action` marked it revealed and populated discovery fields before final speech adoption. `apply_socially_revealed_leads` persisted a derived clue and event log without checking disclosure. Final adoption trusted the selected topic and sealed the unauthorized sentence faithfully.

Failure classes: routing exposed the defect; source eligibility, disclosure authorization, speech adoption and persistence were faulty. This was not evidence that Nara lacked the secret, nor a final-text mutation. Raw `world.event_log` changed with discovery while the existing canonical-view projection remained unchanged.
