# PR-DM Remaining Risks

- The 21 stored rows are the PR-DK fixture matrix, not a measured player distribution.
- D's 18 fully handled scenarios are interpretation outcomes. None was executed. A later executor could still misread a retained proposal.
- `var_unsupported_mechanic` lost its partial credit on purpose. The player still has no supported resolution for advantage, a spy reveal, or marking a patrol found. That needs a product response other than a model clarification, and this experiment does not add that mechanic.
- `declared_canon` and `mechanical_dump` are safely rejected and still unresolved as player-facing turns.
- Bare `and` plus verbs outside the old lists remains undetected (holdout_and_novel_verbs). Extending that with a synonym list or by splitting every conjunction was out of scope.
- Inherited false positives remain: `var_social_control` and `var_hypothetical_control`. Some holdout sentences also trip the unchanged PR-DK checks.
- Free-text novel nouns that are not entity ids and do not match the state-change patterns are not exhaustively detected.
- Holdout routing used local contracts only. No claim is made that a live model would interpret those paraphrases correctly.
- Shared turn-pipeline failures, if still present, are inherited and were not repaired.
- No provider price is stated. Token totals are interpretation-only.
- Production integration was not performed and is not supported by this replay.
