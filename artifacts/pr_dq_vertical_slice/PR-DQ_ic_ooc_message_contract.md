# PR-DQ IC/OOC Message Contract

One conversation. Each player utterance is one envelope. IC and OOC are properties of that envelope, not separate histories.

The experimental boundary is `ingest_player_message`. It does not execute gameplay and it does not call a provider.

## Envelope

| Field | Role |
| --- | --- |
| message_id | Stable id supplied by the caller. History rejects a duplicate id. |
| text | Original player input, including any IC: or OOC: prefix. |
| mode | IC, OOC, MIXED, or UNRESOLVED. |
| mode_source | AUTO, USER_OVERRIDE, or SYSTEM_DEFAULT. |
| requested_override | AUTO, IC, or OOC. The caller's selection. AUTO is the default. |
| intent | ACTION, DIALOGUE, QUESTION, CORRECTION, RULES_QUERY, CLARIFICATION, or OTHER. |
| status | PENDING, CLASSIFIED, AWAITING_CLARIFICATION, PROCESSED, or REJECTED. |
| destination | Logical route. Empty only before routing. |
| correction_subject | NONE, REFERENT, INTENTION, or COMMITTED_ACTION. |
| classification_basis | Why the mode was chosen. |
| processing_result | What the boundary did. Includes executed, resolver_invoked, and the deterministic response. |
| committed | True only after an accepted IC resolver result is kept. |
| adjudication_required | True when a committed turn would have to change and this cycle will not change it. |

Ingest classifies and routes before it returns, so a returned message is not left PENDING. PENDING remains a legal status for a message that has been received and not yet classified. SYSTEM_DEFAULT remains a legal mode source. This cycle never assigns it, and it is not a silent IC default.

Intent is caller-supplied. When the caller omits it, the intent is OTHER. The boundary does not infer intent from keywords.

## Mode selection

1. An explicit IC or OOC override becomes the mode. Source is USER_OVERRIDE. Automatic markers do not replace it.
2. AUTO with both an IC marker and an OOC marker, or with a marker that is not at the start of the text, becomes MIXED.
3. AUTO with a leading `OOC:` or `Out of character:` becomes OOC.
4. AUTO with a leading `IC:` or `In character:` becomes IC.
5. AUTO with none of those markers becomes UNRESOLVED.

Unrecognized text is not treated as IC.

## What this contract does not decide

Communication mode does not decide mechanical legality, dice, NPC decisions, world facts, inventory, HP, or time. An unsupported in-world request stays IC. The gameplay adapter rejects operation classes in the PR-DO unsupported set, including `UNSUPPORTED_MECHANIC`, and leaves the mode IC.
