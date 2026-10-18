# PR-CP authority contract matrix

Existing owners are unchanged. The social resolver owns topic selection. Scene and journal text own visible facts. The decision audit owns whether narration may state them. Finalization may project an already-authorized line. It may not invent one.

| Category | Authority source | Permitted narration | Provenance required | Validator | State mutation | Rejection |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Authored objective world facts | Scene, journal, and decision world-truth rows | Restate the fact. Drop-only wording whose content tokens stay inside the fact | The fact text on the decision | Unlicensed consequential patterns; undeclared world-truth rows | None from narration | Added geography, names, dates, orders, causes |
| 2. Authored NPC knowledge | NPC topic corpus | The selected topic sentence, or its canonical "Word is" line | Resolver topic id | Selected topic is claim-only on the audit copy | Resolver already records the reveal | Topics the resolver did not select |
| 3. Resolver-selected social topics | `resolve_social_action` topic id and text | That text only | `social.topic_revealed.{id}` | Same as row 2, then authored-answer projection if the reply mixes extras | Topic revealed and clue knowledge, as the resolver already commits | Certainty upgrades and extra propositions in the same reply |
| 4. Harmless NPC opinions | Narration contract: ordinary dialogue is not a world fact | Preference and characterization with no new objective fact | None beyond the speaking NPC existing | Existence mention is not consequential; action verbs still are | None | Biography, discoveries, or world facts phrased as opinion |
| 5. Grounded observations | Decision observation rows and visible facts | Describe what the decision already lists | Row text | Authorized observation line when the model text fails | None | Hidden content and unsupported mechanism |
| 6. Paraphrases of visible facts | Same rows as 5 | Exact fact, or a cover of at most one extra content word (`_empty_identity_covers`) | The visible fact string | Pattern license only when no content word is added | None | Edicts, urgent, freshly posted, and any invented inscription |
| 7. Unsupported objective assertions | None | Not permitted | None | Consequential patterns and undeclared claims | None | Always rejected |
| 8. Unsupported consequential actions | None | Not permitted | None | Existence-action verb outside quotes; stateful assertions | None | Opens, orders, departs, kills, and similar verbs |
| 9. Unauthorized discoveries | Clue and discovery owners, not narration | Not permitted unless already on the decision | Discovery id | Evidential and discovery patterns | None | New clues, roster entries, hidden board text |
| 10. Unsupported certainty upgrades | Epistemic outcome on NPC claims | Hedged or exact authored wording | Authored fact, not a new certainty | `unauthorized_certainty_upgrade`, `unauthorized_evidential_relation` | None | "That's all I can confirm", "definitely has not returned" when unauthored |

No new authority owner was created.
