# PR-CE subjective classifier audit

Owner: `game.social._bounded_social_reply_plan_for_missing_topic`.

Order of checks, unchanged:

1. Restricted information, or a hostile attitude, becomes `genuine_refusal`.
2. Consequential information becomes `consequential_information_request`.
3. The existing harmless-subjective expression becomes `harmless_subjective_response_permitted`.
4. Other questions become `genuine_uncertainty`.

There is still one expression and no model call. `gm_resolution_decision` is not a second classifier and was not given this decision.

## Why the two loaf questions diverged

`_HARMLESS_SUBJECTIVE_REPLY_RE` already matched recommendation and preference words (`recommend`, `prefer`, `favorite`) and two `which` shapes:

- `which` immediately followed by `one`, `way`, `would`, or `do you`
- `which` plus a short span plus `would you`

"Which loaf would you recommend?" matches `recommend` and `which loaf would you`.

"Baker, which loaf do you usually keep for yourself?" does not. `loaf` sits between `which` and `do you`, so the immediate `which do you` alternative misses. The habit is `do you usually keep`, not `would you`. None of `recommend`, `prefer`, or `favorite` appears.

## Bounded extension

The same expression now also matches ordinary selection habits:

- `which <up to eight words> do you [usually|normally|typically|often|generally] <preference verb>`
- `do you usually|normally|typically|often|generally <preference verb>`
- `like|prefer|enjoy` plus `best|most`
- `keep|save|pick|choose|take|hold` plus an optional short span plus `for yourself`

Preference verbs in the new alternatives are `prefer`, `like`, `keep`, `pick`, `choose`, `want`, `enjoy`, `recommend`, `suggest`, `take`, `save`, plus `eat`, `drink`, `buy`, `order`, `use`, and `wear` on the habit form. This is not an exact-string list of NPC lines.

## Boundary kept in the same expression

`murdered` was already consequential. Bare `murder` was not. A line such as "which suspect would you say committed the murder" could therefore match the older `which ... would you` alternative and enter the harmless lane. The consequential alternative now includes `murder(?:ed)?`, so murder questions stay consequential before the subjective expression is considered.

Restricted and consequential checks still run first. A subjective shape does not override them.

## What the repair does not do

It does not choose the NPC's words, store a favorite, or mark the reply as an objective world fact. Permission remains `npc_speech_authority=claim_only`, `objective_world_fact_authority=none`, and `durable_state_mutation_allowed=false`.
