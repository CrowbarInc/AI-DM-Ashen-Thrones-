# 08 — Performance and Live-Test Readiness

## Provider budget

Renderer mode uses the existing single `call_gpt` opening request. It does not add a semantic judge, a retry, a model change, or an output-cap change. `ASHEN_OPENING_MAX_OUTPUT_TOKENS` is still the opening cap, default 3000, bounded 1..4096. The rendered opening test observed that same cap on the stub request.

Invalid configuration and an empty catalog return before admission. A rejected plan consumes the one opening response that was already requested; it does not request another.

## Token estimate

These are structural estimates, not live measurements.

| Piece | Estimate |
| --- | --- |
| Added catalog index | Identifiers, required flags, variant ids, and sequence. About 100–250 tokens for 7–15 public facts. Fact prose is not repeated in the index |
| Removed legacy opening guidance | About 150 tokens of exact-sentence instructions, replaced rather than added |
| Plan output | About 20 tokens per selected entry. Six required entries are well under a typical opening narration of several hundred to roughly 1,800 tokens |
| Latency | One request, a smaller output, and local rendering. No measured live latency change |

The synthetic five-turn ledger uses fixture token counts. It does not show a live saving.

## Enablement

```text
$env:ASHEN_OPENING_RENDERER = '1'
```

Unset, `0`, `false`, `no`, and `off` keep the legacy opening. Any other value fails the opening with `opening_renderer_configuration_invalid` and does not call the provider. Ordinary turns ignore the flag. The playtest worker emits a required-entry plan only for the `success` fixture while the flag is enabled. Later turns keep their narration fixtures.

## Residual risk before a live test

The model can still see the existing prompt, including GM-only context that the current prompt already carries. The renderer does not publish that context. A live opening should be reviewed for narrative adequacy, not only for acceptance. The concise variant is deterministic and was not the selection used by the five-turn run.
