# ENDPOINT INVENTORY

endpoint_inventory.json enumerates registered routes, methods, handlers, boundary class, observed HTTP counts and statuses. Player state/session/scene refresh and resume share GET /api/state. Player history uses GET /api/log. Runtime routes include /api/chat, /api/action, /api/start_campaign, /api/new_campaign, /api/reset_session, /api/scene/activate, /api/character, /api/import_sheet, /api/response_mode, /api/reset_combat, /api/clear_log and /api/snapshots (GET/POST), /api/snapshots/load.

/api/campaign, /api/scene and /api/world writes require privileged mode and are denied to player HTTP; /api/debug_trace is denied. Requests for author/debug HTTP modes remain 403 under the existing policy; no new authentication framework was added. Root/static UI and generated docs/OpenAPI serve no runtime campaign state. No distinct campaign-load endpoint exists: snapshot load is the existing loading/continuation operation.

Every registered /api handler receives the shared PlayerHTTPRoute final allowlist boundary. Successful, rejection, initialization failure, validation failure, exception and fallback paths were inspected. Multipart import covers valid sheet and malformed JSON.
