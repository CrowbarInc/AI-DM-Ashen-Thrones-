"""Objective #15 hardening: frontend ui_mode rendering contract regression checks.

These are lightweight string/structure assertions that lock the shipped architecture:
- authoritative render source is GET /api/state?ui_mode=...
- tab visibility matches canonical contract exactly
- mode switches clear forbidden DOM content (no stale leak persistence)
- /api/chat and /api/action are not treated as authoritative render state sources
"""

from __future__ import annotations

from pathlib import Path


def _read_static(name: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / "static" / name).read_text(encoding="utf-8")


def test_apply_visible_tabs_matches_canonical_contract() -> None:
    js = _read_static("app.js")
    assert "function applyVisibleTabsForMode(mode){" in js
    # Canonical tab sets
    assert 'mode === "player" ? ["play", "character", "world"]' in js
    assert ': mode === "author" ? ["scene", "campaign", "world"]' in js
    assert ': ["debug"]' in js


def test_current_ui_mode_drives_state_request() -> None:
    js = _read_static("app.js")
    # Authoritative render state load must always request ui_mode explicitly.
    assert "fetchJSON(apiUrl('/state', {ui_mode: currentUIMode}))" in js
    assert "renderStateEnvelope(s);" in js


def test_render_functions_are_lane_specific_and_not_mixed() -> None:
    js = _read_static("app.js")
    # Envelope split is explicit and uses canonical lane names.
    assert "function renderStateEnvelope(envelope){" in js
    assert "const publicState = envelope && envelope.public_state" in js
    assert "const authorState = envelope && envelope.author_state" in js
    assert "const debugState = envelope && envelope.debug_state" in js

    # Lane-gated rendering: author/debug renderers only run in their mode.
    assert 'if(currentUIMode === "author" && authorState) renderAuthorState(authorState);' in js
    assert 'if(currentUIMode === "debug" && debugState) renderDebugState(debugState);' in js


def test_mode_switch_clears_known_historical_leak_sites() -> None:
    js = _read_static("app.js")

    # Hidden facts must be cleared outside author mode (author -> player/debug).
    assert 'if(currentUIMode !== "author" && $(\'sceneHiddenFacts\')) $(\'sceneHiddenFacts\').value = \'\';' in js

    # Debug JSON / trace boxes must be cleared outside debug mode (debug -> player/author).
    assert 'if(currentUIMode !== "debug"){' in js
    assert "if($('debugBox')) $('debugBox').textContent = 'No debug data in this mode.';" in js
    assert "if($('actionPipelineDebugContent')) $('actionPipelineDebugContent').innerHTML = '';" in js
    assert "if($('actionTraceContent')) $('actionTraceContent').innerHTML = '';" in js

    # Advanced World Debug must be debug-only and cleared when forbidden.
    assert "const worldDebugDetails = $('worldDebugBox')?.closest?.('details.card');" in js
    assert "worldDebugDetails.style.display = (mode === \"debug\") ? '' : 'none';" in js
    assert "if(mode !== \"debug\" && $('worldDebugBox')) $('worldDebugBox').textContent = '';" in js


def test_authoritative_render_flow_not_mixed_with_chat_or_action_payloads() -> None:
    js = _read_static("app.js")

    # Chat and action must end by reloading from /api/state and /api/log, not by rendering directly from response.
    assert "async function reloadAll(){ await loadState(); await loadLog(); }" in js

    # chat success path ends in reloadAll()
    assert "const data = await fetchJSON(apiUrl('/chat', {ui_mode: currentUIMode})" in js
    assert "replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text" in js
    assert "await reloadAll();" in js

    # action success path ends in reloadAll()
    assert "const data = await fetchJSON(apiUrl('/action', {ui_mode: currentUIMode})" in js
    assert "replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text" in js
    assert "await reloadAll();" in js

    # Guardrail: no renderStateEnvelope(data) on /chat or /action payloads.
    assert "renderStateEnvelope(data)" not in js

