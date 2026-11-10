# PR-PLAY-21 trust model

`game/ui_mode_policy.py` defines deterministic player, author, and debug
capabilities. Player may operate runtime; author may see/edit authored data;
debug may see diagnostic data. These are policies for an already chosen mode,
not proofs of requester authority. The gameplay `session.json` stores campaign
progress, clocks, dialogue context and telemetry; it is not an authenticated web
session. No authenticated session middleware, HTTP identity dependency, role
lookup, bearer/capability verifier, or privileged request context was found in
the inspected application entry, mode helpers, or immediately related routes.
Narrative/domain uses of the word authorization are not HTTP authorization.

`run.py:46` binds Uvicorn to 127.0.0.1:8000 with reload enabled by default. This
supports a solo local-operator deployment. It does not authorize every local
process or browser origin. `game/api.py:306` allows all origins, methods and
headers with credentials disabled. Both same-origin and foreign-origin requests
receive 403 for privileged modes after repair; the CORS response still says `*`.
CORS remains unchanged and is not used as authorization.

The browser in `static/app.js:33-54` chooses/persists UI mode in localStorage and
sends it in query/body fields (`:536`, `:560`, `:615`). Scene/campaign/world
editors and debug widgets demonstrate intended local author/developer workflows.
Their HTTP access had no independent trusted identity. No genuinely authorized
HTTP author workflow exists to preserve. Those browser workflows now fail
closed, even for the local operator. Re-enabling them requires a separately
designed trust boundary; no server-wide opt-in, predictable token, role header,
or network-address exception was added.

Existing internal workflows with Python/process/filesystem access remain:
`compose_state`, recursive projections, canonical policy functions, and storage
authoring functions. They are not exposed by a new endpoint. In-process code
and tests may explicitly invoke them; ability to execute repository Python is
the existing local execution trust assumption, not a newly authenticated user.
The focused test validates internal author and debug projection, exact hidden
fact retention and unchanged persisted data. TestClient and manually constructed
Request objects receive no extra HTTP privilege. Passing Request=None cannot
grant author mode through the resolver.

Gap: there is no trusted server-side HTTP author authorization mechanism. This
pass follows the specified fail-closed fallback and leaves that design gap
visible. It does not certify the application for arbitrary untrusted clients;
runtime write permissions and other non-read APIs were not broadly audited.
Evidence covers ASGI serialization/lifespan and source configuration, not a
deployed network service or real provider session.
