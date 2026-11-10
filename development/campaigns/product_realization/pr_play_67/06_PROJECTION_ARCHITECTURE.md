# PROJECTION ARCHITECTURE

Authoritative storage → compose_state / existing publication owners → explicit player-state DTO → response composition → player-response DTO → final PlayerHTTPRoute JSON allowlist → client. Existing action/chat/start helpers project before ordinary serialization; the route also decodes the locally staged JSON response and reprojects before any body reaches the network. This last defense covers other existing endpoints and explicit JSONResponse failures. It incurs local reencoding; measured total HTTP times include this.

The pure projector allocates fresh containers, performs no I/O, resolves no actions, calls no provider and owns no persistence. Raw authoritative state remains available to server resolvers, future scenes and snapshots. Legacy internal compose_state and local Python author/debug projections retain their separate tooling contracts; HTTP privileged modes remain blocked.

The API router class is the existing response-adapter seam: a narrow shared boundary avoids independent per-endpoint blacklists. FastAPI request-validation exceptions and ordinary exceptions get safe status/error objects; detailed diagnostics remain server-side.
