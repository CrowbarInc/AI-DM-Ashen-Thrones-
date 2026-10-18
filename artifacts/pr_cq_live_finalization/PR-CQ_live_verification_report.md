# PR-CQ Live Verification Report

MODE: MINIMAL LIVE FINALIZATION VERIFICATION
IMPLEMENTATION: none

Decision: **B — PARTIAL LIVE IMPROVEMENT**

PR-CP improves the live player-facing result on both planned turns. The preference now seals on the first generation. The patrol fact now reaches the player, and the stored reveal matches that sentence. The patrol turn still rejects both provider drafts, including a milestone paraphrase, and spends a full retry before canonical projection supplies the line.

## Baseline

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: `PR-BN bounded DM improvisational authority`
- Worktree: already dirty. It was not reset. This cycle did not edit application code.
- PR-CP modules used by the process are the untracked worktree files `game/gm_resolution_decision.py` and `game/immutable_valid_response.py`, including `decision_with_selected_social_topic` and the authored-answer projection in `game/immutable_valid_response.py`.
- Production `data/` mtimes were unchanged (`production_mtime_drift.json` is `[]`).
- Session directory: `artifacts/pr_cq_live_finalization/evidence/isolated_session/`. Storage was retargeted before the app started.

## Provider, checked before gameplay calls

- Provider: OpenAI. Billing path: official Python SDK `client.responses.create`.
- No `OPENAI_BASE_URL` or `OPENAI_API_BASE`. Endpoint: `https://api.openai.com/v1/responses`.
- API key present in `.env` (prefix `sk-`, length 164). The key is not in the artifacts.
- `MODEL_NAME=gpt-4.1-mini`. Default, high-precision, and retry-escalation names all resolve to `gpt-4.1-mini`. Routing is on and still selects that name.
- Live response model on all four calls: `gpt-4.1-mini-2025-04-14`.
- Published standard rates, confirmed from the GPT-4.1 mini model page before the calls: input $0.40 / 1M, cached input $0.10 / 1M, output $1.60 / 1M.
- Ceiling at 120,000 tokens, 95% input and 5% output, no cache: about $0.055.

Startup preflight was request 1. It returned usage and `health_class=healthy`. Gameplay calls started only after that.

## Budget

Caps: 2 gameplay turns, 4 provider requests including preflight, 120,000 combined tokens.

Used: 2 completed HTTP turns, 4 requests, 108,690 tokens. The fourth request was turn 2's retry and it finished. No fifth call was sent. No turn was rerun. No parallel session.

## Scenario

Authored `default_scene("frontier_gate")` and `default_world()`, plus `market_quarter` and `old_milestone`, in the disposable directory. Production `data/scenes/frontier_gate.json` was not loaded.

Initial state after the fresh seed:

- Scene `frontier_gate`, location Cinderwatch Gate District, turn counter 1, mode social
- Character Galinor, wizard, HP 8/8, inventory spellbook
- Guard Captain at the gate, topic `patrol`: "A patrol went missing near the old milestone."
- Visible notice board: taxes, curfews, and a posted warning about a missing patrol
- Old milestone exists as its own authored scene and is named by the captain's topic

## Turn 1

Player: "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"

The social resolver selected `guard_captain` and allowed an incidental subjective answer. No topic was revealed. The single provider draft stated a preference for somewhere dry, with a shrug and a glance toward the crowd. Validation sealed it as `initial_hard_valid`. Retry count: 0.

That meets the turn 1 success test. The player received a relevant preference. The reply is not the banner narration PR-CO emitted. An ordinary gesture did not force a retry.

## Turn 2

Player: "Captain, what do you know about the missing patrol?"

The social resolver selected topic `patrol` and the authored sentence. The first draft added an assignment, the trading crossroads, a non-return, and "no sign / no messages." It was hard-invalid. The retry draft paraphrased a patrol missing near the milestone, then said the captain did not know the details. That draft was also hard-invalid: the paraphrase was still `patrol_route_or_geography`, and the ignorance line was `ignorance_not_authorized_answer`.

Projection then emitted:

`Guard Captain mutters, "Word is, a patrol went missing near the old milestone."`

`revealed_topics` is `["patrol"]`. Clue text is the authored sentence. The spoken line contains that sentence. The player was not told the captain cannot answer.

The crossroads, the non-return, and the ignorance denial are absent from the final line. "Word is" and "mutters" come from the existing social realization template, not from a third model draft.

## Why B, not A

Both final answers are relevant and authorized, and the rejected extras did not survive. That is the improvement.

A also requires that no unnecessary retry cycle occur. Turn 2 still spent a retry, and the second generation was discarded as well. The milestone paraphrase did not seal. The player hears the fact only after projection. That is a remaining finalization failure, so the result is partial.

It is not C. PR-CO's preference became banner text, and its patrol turn stored the reveal while saying the captain could not answer. Neither of those outcomes happened here.

It is not D. The unauthorized patrol claims were rejected and were not written as discovered facts.

It is not E or F. The provider ran, usage was present, both turns completed, and the token cap was not hit. The request cap was exactly consumed by the last needed call.

## Recommended next step

Independent review of this package. Do not raise the provider budget and do not start another live session from this result. The open live gap is that a provider paraphrase of the selected patrol sentence is still rejected as route geography, so delivery still depends on a retry plus canonical projection.
