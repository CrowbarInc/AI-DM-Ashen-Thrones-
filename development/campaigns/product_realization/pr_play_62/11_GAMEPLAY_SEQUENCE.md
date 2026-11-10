# Five-action sequence

Disposable governed frontier_gate campaign; state loaded over HTTP first.

| Turn | Input | Authoritative category | Narration result | Requests |
|---|---|---|---|---:|
| 1 | I examine the notice board. | discovered | PASS | 1 |
| 2 | I examine the rain barrel. | observed | REVIEW_REQUIRED | 1 |
| 3 | I examine the notice board again. | known | deterministic_fast_path | 0 |
| 4 | I look around the gate. | observed | REVIEW_REQUIRED | 1 |
| 5 | I examine the rain barrel. | known | deterministic_fast_path | 0 |

All five actions returned HTTP 200 in one campaign/scene. One discovery, first
barrel non-discovery, original-target repeat, gate follow-up and barrel follow-up
were exercised. No artificial discovery or additional mechanic was introduced.
No branching-choice or broad RPG playability claim.

Machine evidence: browser_actions.json is a historical filename for **HTTP/API**
capture, not browser evidence. It contains responses and per-turn before/after
authoritative projections. http_client_actions.json records client timing.
final_session.json contains full terminal conversation/action history. Separate
complete raw-session snapshots after every turn were not captured.
