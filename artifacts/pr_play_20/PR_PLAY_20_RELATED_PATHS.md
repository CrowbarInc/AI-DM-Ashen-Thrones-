# PR-PLAY-20 directly related paths

| Path | Finding / validation |
| --- | --- |
| POST /api/start_campaign success | Confirmed raw-state disclosure; repaired at completed response boundary; synthetic serialized HTTP regression passes |
| POST /api/start_campaign already started | Existing public_state envelope was safe; 409 preserved, no sentinel; now additionally passed through shared boundary |
| POST /api/start_campaign invalid plan | 422, no publication/commit; no sentinel, error diagnostics preserved |
| POST /api/action success | Same raw shared turn helper; confirmed broader leak mechanism; now public projection at HTTP adapter; roll initiative regression passes |
| POST /api/action rejection | Existing unsupported-action error has no state; error text and status preserved |
| POST /api/chat | Success and early nonmutating returns now use final projection; direct raw-compose combat rejection branches also covered by boundary regression |
| GET /api/state | Existing recursive public projection; sentinel absent; no production change |
| GET /api/log, /api/debug_trace | Read only for lane analysis; player log exposes narration/input only; debug reads selected by ui_mode |

The ordinary raw-state rejection test deliberately isolates routing by stubbing `chat` to return the
same compose_state representation used by the inspected combat rejection branches. This tests the
actual HTTP adapter/serializer but does not claim end-to-end combat-routing coverage. Actual negative
opening and unsupported-action routes are also exercised without a response stub.

Additional disclosures: successful ordinary action responses share the campaign/world/scene/session
raw-state exposure. The two chat combat-rejection branches merge compose_state directly; source
inspection confirms the mechanism, while HTTP boundary regression establishes final exclusion.
Nonpublic GM emission metadata also traveled in player responses and is now excluded.

Authorization concern for external review: `resolve_requested_ui_mode` trusts query/body mode values;
`GET /api/state?ui_mode=author` returns author_state (including the synthetic secret), and debug reads
likewise rely on mode selection. UI mode is a capability selector, not an authenticated identity.
Runtime requests with author/debug mode are denied (403), including attempts to select a privileged
start response. No new privileged mode or bypass was introduced. Existing privileged read behavior
is preserved as required; authentication/network exposure must be reviewed before untrusted players
can access the server. This prevents an unconditional safe-for-player-deployment verdict.

Scope stayed at related response/lane boundaries. No unrelated admin/infrastructure audit was run.
Secondary malformed telemetry classification: no diagnostic correction was required at these boundaries;
provider parsing and opening validation were left unchanged. Its cause remains a follow-up, not a claim
of this repair.
