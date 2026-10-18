# System-prompt owner excerpt

Owner: `SYSTEM_PROMPT` in `game/gm.py`.

The template still contains the PR-BT sentence so the replacement has a single anchor. Import-time replacement removes that sentence before any provider request is built. Constructed P1/P2/P3 system prompts contain the 651-character protocol once and do not contain "strongest grounded partial answer".

```183:201:game/gm.py
# Linguistic protocol only. It does not grant authority. Canonical acts stay in
# gm_resolution_decision, the decision-facing answer recipe, and response_policy.
EPISTEMIC_REALIZATION_PROTOCOL = (
    "EPISTEMIC REALIZATION: On an interpretation, or when the player offers a hypothesis, "
    "state the authorized observations first. If the decision permits inference, add one "
    "possibility tied to those observations and say explicitly that cause, actor, time, and "
    "history stay unresolved. Do not add a mechanism, setting, maintenance history, or causal "
    "chain the observations do not contain. Do not use certainty wording for inferred or "
    "hypothetical material, and do not attach that wording to the observations in the same "
    "sentence. A player hypothesis stays hypothetical: the visible facts may be compatible "
    "with it, and observation alone does not settle it."
)
_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE = (
    "If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic."
)

SYSTEM_PROMPT = _SYSTEM_PROMPT_HEADER + """The application owns authoritative mechanics, state, and persistence. ...
Answer direct questions first. If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic. Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.
```

```286:288:game/gm.py
if SYSTEM_PROMPT.count(_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE) != 1:
    raise RuntimeError("PR-BT abstract epistemic sentence was not found exactly once")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace(_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE, EPISTEMIC_REALIZATION_PROTOCOL, 1)
```

The following sentence stays, because the protocol does not state the authorization exception:

`Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.`

That sentence was already in the optimized prompt. It adds no restored characters.
