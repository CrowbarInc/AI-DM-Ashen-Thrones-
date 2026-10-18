# PR-DF Improvisation Contract

Ten cases. Each architecture must label every invented detail as one of:

- **Ephemeral narration** — sentence in the reply, not stored
- **NPC subjective claim** — ledger kind `npc_claim`, epistemic status in the allowed set, not world truth
- **Proposed world fact** — model or planner text that has not passed a resolver or the improvisation validator
- **Authoritative world fact** — authored scene, clue, flag, or resolver output
- **Committed state change** — mutator result (scene, HP, clock, known clue, accepted ledger entry)

Not every improvised detail is stored. A consequential detail is not stored because the model said it.

The current validator (`validate_bounded_improvisation_proposal`) accepts only low-consequence incidental categories and NPC claim categories. It appends `kind:consequential`, `content:mechanical_authority`, `content:hidden_information`, and grounded consequential NPC claims to the reject list. Accepted entries are runtime ledger state. The module docstring says they are not authored world truth.

## Case table

| # | Case | A | B | C | Shared struggle |
|---|---|---|---|---|---|
| 1 | Incidental NPC preference (S1 rain versus dry) | Social resolver plus narration. A preference sentence can stay ephemeral. A matching incidental proposal can be ledgered if the category is allowed (`ordinary_personal_detail`). | Planner proposes `ask` with `expects_mutation: none`. Executor runs the social resolver. Preference text is narration unless a proposal passes the validator. | `propose_action` / `request_action_execution` for the ask. No write tool for "he likes rain." | Treating a taste as a flag. |
| 2 | Ordinary NPC opinion | Same ledger path with epistemic `opinion`. Grounded wording plus a consequential term is rejected. | Plan may include the opinion only as narration guidance, which the executor strips. The opinion enters the ledger only through the validator. | `inspect_permitted_npc_context` may return existing opinion entries. It does not accept a new opinion payload. | Model asserts the opinion as the world's position. |
| 3 | Improvised description (gesture, weather feel, cadence) | Prompt already allows mundane texture as plain narration. It is ephemeral unless a proposal is submitted and accepted. | Planner must not put texture in `actions`. Narration call may still describe it. | No tool. Narration only. | Description smuggles a new exit, clue, or NPC. |
| 4 | Unimportant background character | Incidental category `background_npc_detail` can be accepted at scene scope. Enrollment of an emergent actor exists on the production path and is outside the harness. | A step that creates an NPC id is `unknown_id` unless the catalog already has that id. Description of a crowd member stays in narration. | `query_known_entities` returns no new id. Execution cannot mint one. | A named extra becomes addressable next turn without enrollment rules. |
| 5 | Unanticipated environmental interaction | If no resolver accepts it, A uses `generation` or `unsupported`. Narration must not create the outcome. | Step `act` is validated. Unsupported physical outcomes stop. Narration may say the attempt failed. | `request_rules_adjudication` returns `unsupported` when no preview exists. Execution is refused. | Helpful narration succeeds the stunt anyway. This is the unusual-action test. |
| 6 | Player attempts to establish a new fact ("the tunnel is open") | Contract can mark consequential protection. Improvisation of that content is rejected. The utterance does not write a flag by itself. | Planner `actions` that set a flag are dropped fields. No step type writes flags. | No tool accepts a fact string. | The reply repeats the player's fact as accomplished. |
| 7 | Consequential discovery | Only resolver clue and lead paths (`apply_socially_revealed_leads`, `_apply_authoritative_clues_from_resolution`) add player-known clues. | A discovery step runs those paths or it does not discover. | Execution output lists clue ids the resolver marked known. | Narration names a clue the resolver did not return. |
| 8 | Hidden information | H1-style questions stay on the full visibility rules. Improvisation rejects hidden-info terms. | World queries omit hidden fields. | `not_visible` / absent keys. Narration call still sees whatever A puts in the payload, so the narration leak risk remains. | Answering from GM knowledge because the sentence is fluent. |
| 9 | NPC promises and commitments | Player travel commitment is an engine object (`player_commitment.py`). An NPC promise is not that object. A promise sentence is a subjective claim or ephemeral talk unless a resolver records a social consequence. | Plan cannot set `commitment_status`. The contract builder owns that field. | No promise tool. | "The captain swears" becomes a quest flag. |
| 10 | Detail that later becomes consequential | Ledger entries are not auto-promoted by a later turn in this design. Promotion to a clue or flag requires a resolver on the later turn, using authored or already-known state. The earlier sentence can be quoted as what was said. | Replan on the later turn may reference the ledger id as a claim, not as a fact. | `inspect_permitted_npc_context` can show the claim. Execution still needs a resolver to make it consequential. | Retroactively treating the ledger row as authored truth. |

## Where each architecture is weak

**A.** The narration model sees a large decision object and can sound as if a proposal were already true. Validators and the improvisation reject list are the check. The observe-only gateway can still adopt some post-narration structure on the production path. The experiment turns that off so the weakness is measured in text, not silently written.

**B.** The planner can emit a confident `expects_mutation` that the executor then refuses. The player-facing recovery must say the step did not happen. If the narration call is still the full A payload, it can describe the refused step as done. Scoring treats that sentence as a failure even when state is clean.

**C.** Tool results can be correct while the model's connecting prose invents a result it did not receive. The same narration check as B applies. Extra weakness: a long tool transcript gives the model more of its own earlier guesses to treat as memory. The cap of four rounds limits that. It does not remove it.

## Scoring labels for the experiment

For each scenario the harness stores `state_label` from the tuple in the authority contract, and `text_label` from a checklist:

- State changed only in fields the scenario allows.
- Player-facing text does not assert a prohibited outcome.
- Ledger, if any, has an allowed kind.
- Hidden strings from the fixture's hidden list do not appear in tool results or in player-facing text.

Text checks on the deterministic preflight use fixture gold for engine-authored lines (check prompts, off-scene lines, fallbacks). Model prose is scored only on the optional live arm, with the checklist above. Length and dramatic tone are not inputs to the score.
