# INITIALIZATION CONTRACT

Observable contract: identifiers exist; authoritative session/world exist; frontier_gate selected; player-safe opening text returned; frontend renders that text with Galinor and supported buttons; first notice-board action succeeds; the resulting discovery is persisted. This was observed through real UI and separately TCP.

Server, HTTP and browser measures are separate. TCP timings include network/client wait; browser_network server_ms measures middleware body capture/processing, not only initialization. Refreshed browser console ASHEN_UI_READY uses performance.now through state/log reload and next animation frame; it is a readiness proxy, not a physical paint ACK. Initial A startup timing and full backend/network/render decomposition were not recovered. Tool-call durations for cached-context operations are only upper bounds and are not substituted for exact browser timings.
