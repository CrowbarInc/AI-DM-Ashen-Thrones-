# PR-PLAY-25 repair report

Root cause: the social resolver received the public offering sentence, but topic-only authority selection never promoted it into answer material. Expression was correctly confined to uncertainty; downstream publication worked.

Production files changed:

* `game/public_fact_dialogue.py` (new): bounded question/relation grammar, exact unique registered-subject attribution, explicit visibility/source reference, single-source selection, authored/restricted precedence and diagnostic reasons. No provider import or state writes.
* `game/dialogue_authority.py`: use the selection only after existing topic/disclosure/semantic-plan checks; reuse existing world-source provenance, proposition identity and host sentence. Reconcile social reply fields to source-bound answer with durable mutation disabled. Select the public host source through the existing host-speech lane.
* `game/expressive_dialogue.py`: feed the authority proposition through the existing contract, select faithful paraphrase for this source, identify the offering relation in existing permitted meaning, explain scoped verb equivalences in the prompt, and apply those equivalences before existing closed-content validation. Explicitly reject negated offerings. All other source validation remains unchanged.

Regression file: `tests/test_pr_play_25_public_fact_dialogue.py`. Evidence scripts and reports live under `artifacts/pr_play_25`; before-files enable exact offline comparison. `source_diff.patch` compares only this pass's changes, and source snapshots preserve the reviewable result.

Generalization uses registered NPC identity and the offering relation. Runner, merchant, innkeeper, potter and cook use the same implementation with different names, items and accepted question variants. Neither the runner's name nor hot stew appears in production selection code.

Safeguards: no all-scene context injection, no provider-selected sources, no hidden-fact scan, no disclosed secret payload, no topic/clue mutation, no merging of conflicting facts, no pricing/reward authority. Authoritative character, campaign, combat, conditions, scene and world assertions pass; world change equals only the existing ordinary-turn tick. NPC attitude/trust/fear/suspicion and revealed topics remain unchanged. Session clock, interaction binding, delivered-speech memory, log and last-interaction bookkeeping remain permitted engine behavior.

Supported mock expression “I've got hot stew and rumors.” is adopted and published. “...for three copper” is rejected with `unsupported_number` and `unsupported_addition`; the authorized offering host fallback is published instead. Provider generation disabled also publishes the host offering without an expression request. Hidden and irrelevant questions preserve refusal/uncertainty.

Remaining limits: grammar is deliberately narrow, not a parser of arbitrary prose; item descriptions must remain intact in paraphrases (omitting an adjective is not newly licensed). Ambiguous or multiple public facts produce fallback. Existing locked semantic plans and authored-topic behavior are unchanged. Known broad historical failures remain and are not repaired here. No opening/data/model/provider-contract redesign, live gameplay, live-provider request, commit or push was performed.
