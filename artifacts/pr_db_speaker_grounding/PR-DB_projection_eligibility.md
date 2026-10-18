# PR-DB Projection Eligibility

Projector: `game.gm._project_harmless_social_provider_context`.

The predicate `exactly_one_allowed_speaker` was not modified.

PR-DA follow-up before this repair: first failure `exactly_one_allowed_speaker` (required 1, actual 0). Projection absent.

After this repair, the same follow-up was rebuilt deterministically and passed into the projector with `provider_response_contract = narration_only`.

`exactly_one_allowed_speaker`: required 1, actual 1, pass. Authority source: `speaker_selection.allowed_speaker_ids`.

Speaker, contract, and active interlocutor agree on `guard_captain`. Resolver is `social`. Ordinary contract is established. Social target is resolved. Permitted state mutations are empty. Combat is not active.

First failing predicate now:

| Predicate | Required | Actual | Result | Authority source |
|---|---|---|---|---|
| `reply_plan_kind` | `harmless_subjective_response_permitted` | `genuine_uncertainty` | FAIL | `social.reply_plan_kind` |

The same reply plan also fails `incidental_subjective_allowed` (actual false) and `npc_speech_authority` (actual `none`). In the projector those checks are later in the same conjunction. The first failure in source order is `reply_plan_kind`.

`provider_context_projection`: absent.

Projection was not forced. Turn 1's preference question is classified `harmless_subjective_response_permitted`. Turns 2 and 3 are not. That difference is the existing social reply-plan classifier, not a new exception.
