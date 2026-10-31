# 06 — Performance and Provider Usage

| Measurement | Current pass |
|---|---|
| Nonbillable readiness DNS lookup | 6.839 ms, failed errno 11001 |
| Live gameplay turns | 0 / maximum 6 |
| Provider admissions / dispatches / returned replies | 0 / 0 / 0 |
| SDK transport retries actually made | 0; no dispatch |
| Host provider retries actually made | 0 |
| New provider token usage | No inference requested; no provider usage object exists |
| Cost | No billable inference attempted; no priced estimate required |
| Per-turn end-to-end / provider / host / UI timing | Unavailable; no gameplay turn |
| App startup / opening elapsed | Unavailable; not launched |
| User-visible repeated inputs / retries | 0 observed; no interface session |
| Offline suite | 204 tests, 3.869 s reported by JUnit, not gameplay timing |

**Inspected only:** game.api traces latency_ms including total_turn and stage timing; live_chat_interpretation records provider latency and usage; provider_budget records durable admissions before dispatch, completion usage and latency. Input-token estimates are distinct from returned provider counts. Ledger application admissions do not independently measure SDK retry transports. No reliable existing price table was used and no external pricing lookup is necessary for zero inference.

Important launch limitation: ASHEN_DISABLE_PROVIDER_RETRIES suppresses host narration retry attempts in gm.py. Both production OpenAI client constructors (gm.py and live_chat_interpretation.py) omit explicit max_retries, while the historical controlled runner constructed zero-retry clients. The readiness-only client used max_retries=0 but was closed without requests; that is not a production launch guarantee. This is an inspected accounting/control limitation, not an observed retry/billing incident. Normal UI strict transport-attempt compliance needs an already reviewed zero-retry launch control before a later bounded live test. No retry repair or harness was implemented here.

Historical R1-05 6,475 measured tokens and its failed/returned trials remain historical; they are not added to this checkpoint or used to estimate post-repair latency/cost. Failed inference would count as an admission if attempted; none was.
