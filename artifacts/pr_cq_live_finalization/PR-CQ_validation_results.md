# PR-CQ Validation Results

Model on every completed response: `gpt-4.1-mini-2025-04-14`. Usage was present on every response. No call was rerun by the probe.

## Turn 1

| Check | Result |
| --- | --- |
| Resolver | `social`, action `question_guard_captain`, intent `social_exchange`, reply kind `answer` |
| Harmless preference | `incidental_subjective_allowed=true`. `topic_revealed=null` |
| Provider candidates | 1 generation |
| Attempt 1 | `hard_valid=true`, reasons `[]` |
| Retry | none. `regeneration_invoked` was not set |
| Immutable result | sealed, provenance `initial_generation`, attempt 1, authority `accepted` |
| Acceptance | `initial_hard_valid` |
| Final text | the provider preference answer |

The preference mentions the captain, a shrug, a gaze, and the muddy crowd. None of those caused a retry. The reply is about dry watch versus rain. It is not the unrelated banner fallback PR-CO emitted.

## Turn 2

| Check | Result |
| --- | --- |
| Resolver | `social`, action `question_guard_captain`, intent `social_exchange`, reply kind `answer` |
| Selected topic | `patrol` / "A patrol went missing near the old milestone." |
| Provider candidates | 2 generations |
| Attempt 1 | `hard_valid=false`, reason `unauthorized_resolution_decision_fact` |
| Retry | one, reason `hard_invalid` |
| Attempt 2 | `hard_valid=false`, reason `unauthorized_resolution_decision_fact` |
| Immutable result | sealed after projection, provenance label `safe_nonresolution`, acceptance why `authored_answer_projection` |
| Final text | canonical authored sentence inside the social template |

### Attempt 1 violation codes

The whole reply was discarded. Recorded codes on the rejected sentences:

- `official_orders_or_procedures` and `patrol_route_or_geography` on the "assigned near the old milestone" sentence
- `notice_roster_history` on "didn't return" plus the notice-board warning
- `unauthorized_negative_evidence` and `undeclared_negative_evidence` on "no sign of them, no messages"
- `undeclared_consequential_claim` on the captain-existence sentence that carried the assignment claim

The crossroads order and the non-return claim did not seal.

### Attempt 2 violation codes

- `patrol_route_or_geography` on "There's talk of a patrol missing near the old milestone."
- `unsupported_narrator_lead` on the ignorance-plus-notice sentence
- `ignorance_not_authorized_answer` and `undeclared_consequential_claim` on "I don't know the details myself"

The paraphrase was not treated as a restatement of the selected sentence. The ignorance line was not sealed over a topic the resolver had already selected.

### What sealed

`authored_answer_projection` replaced both drafts with:

`Guard Captain mutters, "Word is, a patrol went missing near the old milestone."`

That string is `format_structured_fact_social_line` around the authored topic text. It is not a third provider draft.
