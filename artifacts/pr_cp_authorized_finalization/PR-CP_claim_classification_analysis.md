# PR-CP claim classification analysis

## What extraction already did

Preference speech returned early as epistemic NPC speech. The gesture became an entity-existence row (`kind=entity`, `relation=exists`, value matching "guard" inside "guard captain"). The patrol sentence returned early as epistemic speech and also tripped `patrol_route_or_geography`. The certainty sentence tripped certainty and evidential relations. Notice sentences tripped `notice_roster_history` because the pattern keys off posted/listed/names, which the authored fact itself contains.

Those pattern matches are still computed. They are not, by themselves, the repair.

## What the comparison did

`_undeclared_consequential_violations` flagged every authorized world-truth claim absent from `declared_claims`. Narration-only sets that list to empty, so every world-truth restatement was undeclared. Existence rows took that path even when no action was present.

`audit_narrated_claims` treated any consequential pattern hit as unauthorized, including a hit whose proposition was exactly the authorized statement.

## Repair rule

A pattern code is licensed when some authorized statement produces the same code and the sentence's proposition (quoted text, without a leading "Word is,") has content tokens that are a subset of that statement. Drops are allowed. Added content words are not.

Existence-only rows skip the undeclared world-truth flag unless an action verb matches outside quotes (`opens`, `orders`, `kills`, and the same class). Restating an authorized world fact also skips that flag.

The selected social topic is attached to the audit copy as claim-only, with an empty semantic identity, source `social.topic_revealed.{id}`. It is not written back onto the resolver decision and it is not promoted to world truth.

## What stays rejected

"East beyond the trading crossroads" adds tokens, so `patrol_route_or_geography` stays unlicensed. "Have not returned" is a separate proposition. "That's all I can confirm" stays a certainty upgrade. "Opens the gate and orders the watch to depart" matches the action verb outside quotes. Invented roster names, yesterday, and east-road orders stay `notice_roster_history` because they are not the authorized sentence.

## Subjective speech

"The captain prefers the dry watch" is not a world fact. It does not authorize a biography, a discovery, or an action. The rain example in the low-stakes state check was left in place. The action-verb check is the backstop for a consequential verb in the same sentence. `_structured_consequential_reasons` was not reordered.
