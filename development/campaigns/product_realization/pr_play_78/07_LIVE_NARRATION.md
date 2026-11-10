# Live narration

Gate: `ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION=1`. The host sends committed sentences to the expression transport. `validate_narration` requires outcome tokens such as aside, open, or closed when those tokens are in the facts, and rejects quest, treasure, secret, sentinel, gold, "you find", "hidden passage", "northwest", and invented "you open / climb / find".

`artifacts/pr_play_78/live_gate.json` is the post-fix session. Narration flags on the session are sticky, so a later `narration_adopted: true` is not an independent accept. Counts below use a provider-latency turn whose narration reasons are empty.

Published accepts (4):

1. "I stand up." → "You are upright, with your feet on the ground." (2438.6 ms)
2. "Approach the guard and greet him." → restyle beginning "You walk up next to the Gate Guard." (3588.0 ms)
3. "Ask the guard about the warning." → restyle of the uncertainty reply (2977.3 ms)
4. "Thank the guard." → restyle including "Stay safe out there." (3576.9 ms)

Rejected (1): "I look around." reason `not_a_variation` (3242.7 ms). The deterministic look-around was published instead.

Not counted: "Who are you?" at 35.6 ms.

The extended-play script left this gate off. Its narration is deterministic. Browser play left the provider disabled, so none of the browser text is live narration.

The provider does not commit state. `committed_by_provider` is false on the presentation log.
