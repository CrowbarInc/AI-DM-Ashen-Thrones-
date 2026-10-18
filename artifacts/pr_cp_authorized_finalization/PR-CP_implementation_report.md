# PR-CP implementation report

MODE: AUTHORIZED NARRATION FINALIZATION REPAIR
LIVE CALLS: 0

HEAD at start: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
Worktree was already dirty. It was not reset. Production saves were not written. Fixtures are in-memory or test-local.

## Shared boundary

Narration-only envelopes declare no claims. The undeclared-consequential layer then treated a restatement of an already-authorized statement, and a mere mention that an NPC exists, as an undeclared world fact. Hard validation discarded the whole reply. Authorized material was lost together with the extras.

The validator was not disabled. A consequential pattern is a violation only when the sentence adds content the authorized statement does not contain. Existence mentions stay non-consequential unless an action verb appears outside quotation. The resolver-selected social topic is copied onto the audit decision as claim-only epistemic material. When a mixed reply fails, finalization emits only the canonical authored line.

## Code

`game/gm_resolution_decision.py`

- A proposition restates an authorized statement when its quoted content tokens are a subset of that statement.
- Pattern codes licensed by that restatement are not unauthorized discoveries.
- Existence-only rows are not undeclared consequential claims unless an action verb matches outside quotes.
- `decision_with_selected_social_topic` appends the selected topic to a decision copy. The resolver decision is not mutated.

`game/immutable_valid_response.py`

- Validation audits the copy that includes the selected topic.
- An ignorance line does not seal when the player asked for a visible fact that the line does not contain.
- After fidelity failure, the selected authored answer is projected before the visible-observation fallback.

## What was not changed

Social resolver selection, exploration routing, NPC knowledge contents, and the one-extra-content-word paraphrase cover were left in place. Hard-invalid outcomes remain. No second narration authority was added. PR-CO strings are not hardcoded. Token budget was not changed.

## Test adjustments that follow the same rule

`tests/test_pr_br_authority_reconciliation.py`: the exact beam and brace facts now reach the player on an empty declaration. Invented causes stay forbidden. "Without clear signs" is an explicit non-assertion that rides with those facts.

`tests/test_pr_br_continuation19_hard_authority.py`: an unauthored third bell still does not seal. The grounded schedule still seals on retry. A rumor question emits the selected stew topic, "Hot stew and rumors for coin.", and does not emit an unauthored third-bell rumor.
