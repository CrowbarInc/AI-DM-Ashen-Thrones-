# pr_play_live_probe_configuration_recovery

**Verdict: A/PASS — live probe complete.** This is evaluation completion, not gameplay quality. Gameplay execution successes are 0/5.

The configuration-ordering defect is repaired in the evaluation driver. After `discover_identity()` imported `experiments.pr_dp` and set `ASHEN_DISABLE_LIVE_INTERPRETATION=1`, the driver established the live configuration and read it back through `production_live_interpretation_enabled()`. That function stayed true after the contract import, after each fixture seed, and after every turn.

Five ordinary `/api/chat` turns were attempted once on isolated frontier-gate campaigns. A1, A2, and A3 each made one OpenAI `gpt-4.1-mini` interpretation call and returned HTTP 200. A4 and B1 returned HTTP 200 with live interpretation still enabled and zero provider calls; both stopped at the existing `uncertain_actionable_coverage` gate. No narration, expression, recovery, or other model call occurred.

Provider requests 3/40. Input tokens 6,739. Output tokens 547. Cached tokens 0. Estimated uncached cost $0.0035708 of $5.00. Actual account billing was not queried. Request latency median 2.844s / maximum 3.593s. Gameplay-turn latency median 2.422s / maximum 6.265s. Provider errors, timeouts, and retries: 0. Returned model on every call: `gpt-4.1-mini-2025-04-14`.

The live model did not bind the carried Spellbook. Its permitted entity list contained scene ids only. A1 interpreted a use of the carried volume and left `target_ref` null; the host then withheld with `communication_before_execution`. A2 and A3 asked which spellbook was meant. No sheet spell was published. State stayed at turn 4 in `frontier_gate`. Character, world, combat, and conditions did not change.

No production gameplay module was edited. No second pass, model substitution, retry, remaining-15 run, commit, or push. The paused milestone `pr_play_social_check_repeat_and_legacy_stance` was not resumed.

Deterministic regression, providers disabled: combined 455 passed / 17 failed; focused 470 passed / 1 failed. New failure identities: 0 in both. The inherited initiative failure and the 17 combined identities are unchanged. Provider records in those runs: 0.
