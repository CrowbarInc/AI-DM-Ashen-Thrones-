# PR-PLAY-29 scenario

Initialize one fresh isolated frontier-gate-v1 instance through POST /api/new_campaign?ui_mode=player followed by the one live POST /api/start_campaign?ui_mode=player. Use unchanged production FastAPI app in owned worker. Never reuse/reset after failure.

Exact ordinary API inputs, same campaign/session:
1. "I approach the tavern runner and ask what they're offering."
2. "What sort of rumors have you heard?"

Hard ceiling: five live-provider requests (one opening, up to two per ordinary turn); zero retries, fallback-model calls, judges, exploratory actions or third turn. Production admission and transport observer enforce this ceiling. Remaining budget must cover complete next turn.

Opening gate requires coherent accepted opening, valid state, accessible tavern_runner, public offering fact, authored patrol_rumor with rumor metadata, no protected publication. Turn 1 continuation requires correct interaction/target, public authority, useful grounded answer, integrity/confidentiality, and two remaining slots. Rejected expression may continue only with useful authorized engine fallback. Any decisive semantic, integrity, provider or budget failure stops the experiment without reset or retry.

Expected actual authority transition: PUBLIC_FACT -> AUTHORED_TOPIC. Topic selection alone does not prove disclosure or clue authority; compare recorded source grants/events/log-bound mutations with production evaluator. Assess dialogue quality separately from mechanical success. No repairs, commit or push. Stop after evidence package for external review.
