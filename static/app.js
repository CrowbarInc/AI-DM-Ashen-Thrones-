const API = '/api';
let state = null; // Legacy local cache for public lane only (player mode helpers).
let startCampaignBusy = false;

/** Developer-facing copy for blocked new campaign (infra/billing/preflight — not narrative). */
function formatBlockedNewCampaignMessage(data){
  const err = (data && data.error) ? String(data.error) : 'Could not start a new campaign.';
  const op = data && data.upstream_dependent_run_gate_operator;
  const lines = [err, '', 'This is an infrastructure, billing, or upstream preflight issue — not a narrative failure.'];
  if(op){
    if(op.compact_banner) lines.push(String(op.compact_banner));
    lines.push('upstream_gate_disposition: ' + String(op.upstream_gate_disposition || ''));
    lines.push('gameplay_conclusions_valid: ' + String(!!op.gameplay_conclusions_valid));
    if(op.block_reason != null && op.block_reason !== '') lines.push('block_reason: ' + String(op.block_reason));
    if(op.preflight_health_class != null && op.preflight_health_class !== '') lines.push('preflight_health_class: ' + String(op.preflight_health_class));
    if(op.action_hint) lines.push('action_hint: ' + String(op.action_hint));
  }
  return lines.join('\n');
}

function newCampaignBlockedDetails(data){
  const out = {};
  if(data && data.upstream_dependent_run_gate_operator) out.upstream_dependent_run_gate_operator = data.upstream_dependent_run_gate_operator;
  if(data && data.upstream_dependent_run_gate) out.upstream_dependent_run_gate = data.upstream_dependent_run_gate;
  return Object.keys(out).length ? out : null;
}

function $(id){ return document.getElementById(id); }
function esc(s){ return String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }

// --- UI mode (single source of truth) ---

const UI_MODES = /** @type {const} */ (["player", "author", "debug"]);
const DEFAULT_UI_MODE = "player";
const UI_MODE_STORAGE_KEY = "ashen_thrones_ui_mode";

/** @type {"player"|"author"|"debug"} */
let currentUIMode = loadPersistedUIMode();

function isKnownUIMode(mode){
  return UI_MODES.includes(String(mode));
}

function loadPersistedUIMode(){
  try {
    const raw = localStorage.getItem(UI_MODE_STORAGE_KEY);
    return isKnownUIMode(raw) ? raw : DEFAULT_UI_MODE;
  } catch {
    return DEFAULT_UI_MODE;
  }
}

function persistUIMode(mode){
  try { localStorage.setItem(UI_MODE_STORAGE_KEY, mode); } catch {}
}

function apiUrl(path, params={}){
  const url = new URL(API + path, window.location.origin);
  for(const [k,v] of Object.entries(params)){
    if(v === undefined || v === null) continue;
    url.searchParams.set(k, String(v));
  }
  return url.toString();
}

function addMessage(role, title, text, details=null){
  const log = $('chatLog');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `<div class="meta">${esc(title)}</div><div>${esc(text).replace(/\n/g,'<br>')}</div>`;
  if(details){
    const d = document.createElement('details');
    d.innerHTML = `<summary>Show details</summary><pre>${esc(JSON.stringify(details,null,2))}</pre>`;
    div.appendChild(d);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function replaceMessage(node, role, title, text, details=null){
  node.className = `msg ${role}`;
  node.innerHTML = `<div class="meta">${esc(title)}</div><div>${esc(text).replace(/\n/g,'<br>')}</div>`;
  if(details){
    const d = document.createElement('details');
    d.innerHTML = `<summary>Show details</summary><pre>${esc(JSON.stringify(details,null,2))}</pre>`;
    node.appendChild(d);
  }
}

function showTab(name, btn){
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  btn.classList.add('active');
  $('tab-'+name).classList.add('active');
}

document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', ()=>showTab(btn.dataset.tab, btn)));

function applyVisibleTabsForMode(mode){
  const visible = new Set(
    mode === "player" ? ["play", "character", "world"]
    : mode === "author" ? ["scene", "campaign", "world"]
    : ["debug"]
  );

  // Tab buttons
  document.querySelectorAll('.tab').forEach(btn => {
    const id = btn.dataset.tab;
    btn.style.display = visible.has(id) ? '' : 'none';
  });

  // Panels (hard separation: non-visible panels are hidden, and we clear mode-forbidden content elsewhere)
  document.querySelectorAll('.tab-panel').forEach(panel => {
    const id = panel.id?.replace(/^tab-/, '');
    panel.style.display = visible.has(id) ? '' : 'none';
  });

  // Default active tab within the mode
  const activeBtn = document.querySelector('.tab.active');
  const activeTab = activeBtn ? activeBtn.dataset.tab : null;
  if(!activeTab || !visible.has(activeTab)){
    const nextId = [...visible][0];
    const nextBtn = document.querySelector(`.tab[data-tab="${nextId}"]`);
    if(nextBtn) showTab(nextId, nextBtn);
  }
}

function clearForbiddenDomContentForMode(mode){
  // Clear (don't just hide) known historical cross-mode leak sites immediately on mode switch.
  if(mode !== "author" && $('sceneHiddenFacts')) $('sceneHiddenFacts').value = '';

  if(mode !== "debug"){
    if($('debugBox')) $('debugBox').textContent = 'No debug data in this mode.';
    if($('actionPipelineDebugContent')) $('actionPipelineDebugContent').innerHTML = '';
    if($('actionTraceContent')) $('actionTraceContent').innerHTML = '';
    if($('engineDebugContent')) $('engineDebugContent').innerHTML = '';
    if($('worldDebugBox')) $('worldDebugBox').textContent = '';
  }
}

function updateWorldModeHint(mode){
  const el = $('worldModeHint');
  if(!el) return;
  el.textContent =
    mode === "player" ? 'Gameplay view — consequences and discoveries as the player sees them.'
    : mode === "author" ? 'Author view — shared world summary (spoilers stripped). Use Scene/Campaign to edit.'
    : '';
}

function enforceDomBoundariesForMode(mode){
  // Player surfaces: chat + action helper are gameplay-only.
  const chatInput = $('chatInput');
  const sendBtn = $('sendChatBtn');
  const chatPanel = document.querySelector('.chat-input-panel');
  const affordanceBar = $('affordanceBar');
  const composerCard = $('composerBody')?.closest?.('.card');
  const controlsCard = $('clearLogBtn')?.closest?.('.card');
  const saveSlotsCard = $('createSnapshotBtn')?.closest?.('details.card');

  const allowRuntime = (mode === "player");
  if(chatPanel) chatPanel.style.display = allowRuntime ? '' : 'none';
  if(affordanceBar) affordanceBar.style.display = allowRuntime ? '' : 'none';
  if(composerCard) composerCard.style.display = allowRuntime ? '' : 'none';
  if(controlsCard) controlsCard.style.display = allowRuntime ? '' : 'none';
  if(saveSlotsCard) saveSlotsCard.style.display = allowRuntime ? '' : 'none';
  if(chatInput) chatInput.disabled = !allowRuntime;
  if(sendBtn) sendBtn.disabled = !allowRuntime;

  // Engine debug panel: debug-only.
  const engineDebugPanel = $('engineDebugPanel');
  if(engineDebugPanel) engineDebugPanel.style.display = (mode === "debug") ? '' : 'none';

  // World "Advanced World Debug": debug-only. Also clear any lingering text when forbidden.
  const worldDebugDetails = $('worldDebugBox')?.closest?.('details.card');
  if(worldDebugDetails) worldDebugDetails.style.display = (mode === "debug") ? '' : 'none';
  if(mode !== "debug" && $('worldDebugBox')) $('worldDebugBox').textContent = '';

  // Debug tab cards: debug-only (tab already hidden in other modes, but avoid accidental render leaks).
  const debugBox = $('debugBox');
  if(mode !== "debug" && debugBox) debugBox.textContent = 'No debug data in this mode.';
}

function renderPublicState(s){
  // Cache for player-mode helpers (composer, labels). Never treat this as a mixed state object.
  state = s;

  const char = s.character || {};
  if($('charSummary') && char && char.hp && char.ac){
    $('charSummary').innerHTML = `
      <strong>${esc(char.name || '')}</strong> — Level ${esc(char.level ?? '')} ${esc(char.class || '')}<br>
      HP: ${esc(char.hp.current ?? '')}/${esc(char.hp.max ?? '')}<br>
      AC: ${esc(char.ac.normal ?? '')} | Touch ${esc(char.ac.touch ?? '')} | Flat-Footed ${esc(char.ac.flat_footed ?? '')}<br>
      Conditions: ${(char.conditions||[]).map(c=>c.name).join(', ') || 'none'}`;
  }

  const combat = s.combat || {};
  if($('combatStatus')){
    $('combatStatus').textContent = combat.in_combat
      ? `Round ${combat.round} | Active: ${combat.active_actor_id || 'none'} | Action spent: ${combat.player_turn_used}`
      : 'Combat inactive.';
  }

  const ui = s.ui || {};
  if($('enemyStatus')){
    $('enemyStatus').innerHTML = (ui.living_enemies||[]).map(e=>`${esc(e.name)}: ${esc(e.hp)}/${esc(e.max_hp)}`).join('<br>') || 'No living enemies.';
  }

  const scene = (s.scene && s.scene.scene) ? s.scene.scene : {};
  if($('sceneHeader')) $('sceneHeader').textContent = scene.location || 'Ashen Thrones';
  if($('sceneSubheader')) $('sceneSubheader').textContent = scene.summary || '';
  if($('sceneNameDisplay')) $('sceneNameDisplay').textContent = scene.location || scene.id || '';
  if($('sceneModeDisplay')) $('sceneModeDisplay').textContent = scene.mode || '';

  // Save summary: player mode only (public lane). If absent, keep minimal.
  const saveCard = $('saveSummaryCard');
  const saveCont = $('saveSummaryContent');
  if(saveCard && saveCont){
    const sm = s.save_summary || {};
    const savedAt = sm.saved_at ? new Date(sm.saved_at).toLocaleString() : 'Never';
    const hasData = sm.save_data_exists ? 'Yes' : 'No';
    const activeScene = (s.session && s.session.active_scene_id) ? s.session.active_scene_id : null;
    saveCont.innerHTML = `
      <div><strong>Last saved:</strong> ${esc(savedAt)}</div>
      <div><strong>Active scene at save:</strong> ${esc(sm.active_scene_id || activeScene || '—')}</div>
      <div><strong>Save data exists:</strong> ${hasData}</div>
      <div class="muted" style="margin-top:4px">Auto-saves on each action/chat. ${sm.discovered_clues ?? 0} clues, ${sm.chat_messages ?? 0} log entries.</div>
    `;
  }

  if(s.session && s.session.response_mode && $('responseModeSelect')){
    $('responseModeSelect').value = s.session.response_mode;
  }

  if($('characterBox')) $('characterBox').textContent = JSON.stringify(s.character || {}, null, 2);

  const world = s.world || {};
  if($('worldFactions')) $('worldFactions').textContent = JSON.stringify(world.factions || {}, null, 2);

  const projects = world.projects || [];
  if($('worldProjectsList')){
    $('worldProjectsList').innerHTML = projects.map(p=>`<li><strong>${esc(p.name)}</strong> — ${esc(p.status)} (${esc(p.progress)}/${esc(p.target)})</li>`).join('') || '<li class="muted">No active projects.</li>';
  }

  const events = (world.event_log||[]).slice(-10);
  if($('worldEventsList')){
    $('worldEventsList').innerHTML = events.map(ev=>`<li>${esc(ev.text || JSON.stringify(ev))}</li>`).join('') || '<li class="muted">No recent events.</li>';
  }

  const journal = s.journal || {};
  const knownFacts = journal.known_facts || [];
  const clues = (journal.discovered_clues || []).concat(journal.unresolved_leads || []);
  if($('journalKnownFacts')) $('journalKnownFacts').innerHTML = knownFacts.map(f=>`<li>${esc(f)}</li>`).join('') || '<li class="muted">No facts recorded yet.</li>';
  if($('journalClues')) $('journalClues').innerHTML = clues.map(c=>`<li>${esc(c)}</li>`).join('') || '<li class="muted">No clues discovered yet.</li>';

  // Player/world must never render debug panels.
  if($('worldDebugBox')) $('worldDebugBox').textContent = '';

  // Player UI affordances/composer only in player mode.
  if(currentUIMode === "player"){
    if($('scenePicker')){
      $('scenePicker').innerHTML = (ui.scene_ids || []).map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join('');
      if(s.session && s.session.active_scene_id) $('scenePicker').value = s.session.active_scene_id;
    }
    if($('targetSelect')){
      $('targetSelect').innerHTML = (ui.living_enemies || []).map(e=>`<option value="${esc(e.id)}">${esc(e.name)} (${esc(e.hp)}/${esc(e.max_hp)})</option>`).join('');
    }
    renderAffordances(ui.affordances || []);
    renderComposer();
    updateCampaignBootstrapUI(s);
    renderSnapshots(s);
  } else {
    renderAffordances([]);
  }
}

function renderAuthorState(s){
  // Author surface: campaign + scene editors, plus author-only world tooling (if any).
  // Must not show debug telemetry by default.
  if(!s) return;

  const campaign = s.campaign || {};
  if($('campaignTitle')) $('campaignTitle').value = campaign.title || '';
  if($('campaignPremise')) $('campaignPremise').value = campaign.premise || '';
  if($('campaignTone')) $('campaignTone').value = campaign.tone || '';
  if($('campaignContext')) $('campaignContext').value = campaign.starting_context || '';
  if($('campaignGuidance')) $('campaignGuidance').value = (campaign.gm_guidance || []).join('\n');

  const scene = (s.scene && s.scene.scene) ? s.scene.scene : {};
  if($('sceneId')) $('sceneId').value = scene.id || '';
  if($('sceneLocation')) $('sceneLocation').value = scene.location || '';
  if($('sceneSummary')) $('sceneSummary').value = scene.summary || '';
  if($('sceneMode')) $('sceneMode').value = scene.mode || '';
  if($('sceneVisibleFacts')) $('sceneVisibleFacts').value = (scene.visible_facts || []).join('\n');
  if($('sceneDiscoverableClues')) $('sceneDiscoverableClues').value = (scene.discoverable_clues || []).join('\n');
  // Author-only field: hidden facts should only be populated in author mode.
  if($('sceneHiddenFacts')) $('sceneHiddenFacts').value = (scene.hidden_facts || []).join('\n');
}

function renderDebugState(s){
  if(!s) return;
  if($('debugBox')) $('debugBox').textContent = JSON.stringify(s, null, 2);

  // Action Pipeline Debug (debug lane only).
  const adb = $('actionPipelineDebugContent');
  const adbCard = $('actionPipelineDebugCard');
  if(adb && adbCard){
    const d = s.debug || {};
    adbCard.style.display = 'block';
    if(Object.keys(d).length){
      adb.innerHTML = `
        <div class="debug-row"><strong>Player input</strong><div class="debug-val">${esc(d.player_input || '(none)')}</div></div>
        <div class="debug-row"><strong>Action type</strong><div class="debug-val">${esc(d.last_action_type || '')}</div></div>
        <div class="debug-row"><strong>Parsed action</strong><pre class="debug-pre">${esc(d.normalized_action ? JSON.stringify(d.normalized_action,null,2) : '(not exploration)')}</pre></div>
        <div class="debug-row"><strong>Resolver result</strong><pre class="debug-pre">${esc(d.resolver_result ? JSON.stringify(d.resolver_result,null,2) : '(none)')}</pre></div>
        <div class="debug-row"><strong>Resolution kind</strong><div class="debug-val">${esc(d.resolution_kind || '')}</div></div>
        <div class="debug-row"><strong>Scene transition</strong><div class="debug-val">${d.scene_transition ? esc(`${d.scene_transition.from} → ${d.scene_transition.to}`) : '(none)'}</div></div>
      `;
    } else {
      adb.innerHTML = '<p class="muted">No action pipeline debug yet.</p>';
    }
  }

  // Action Trace (debug lane only).
  const atc = $('actionTraceCard');
  const atCont = $('actionTraceContent');
  if(atc && atCont){
    const traces = s.debug_traces || [];
    const latest = traces[traces.length - 1];
    atc.style.display = 'block';
    if(latest){
      atCont.innerHTML = `<pre class="debug-pre">${esc(JSON.stringify(latest,null,2))}</pre>`;
      if(typeof console !== 'undefined' && console.log) console.log('[Action Trace]', latest);
    } else {
      atCont.innerHTML = '<p class="muted">No trace yet.</p>';
    }
  }

  // Engine debug panel is debug-only; render it from debug lane.
  renderEngineDebug(s);

  // World debug details (migrated out of player/author world).
  if($('worldDebugBox')){
    const world = s.world || {};
    $('worldDebugBox').textContent = JSON.stringify(
      {factions: world.factions, projects: world.projects, events: world.event_log},
      null,
      2
    );
  }
}

function renderSnapshots(s){
  const listEl = $('snapshotsList');
  if (!listEl) return;
  const snaps = s.snapshots || [];
  if (!snaps.length) {
    listEl.innerHTML = '<li class="muted">No snapshots yet. Create one to save a restore point.</li>';
  } else {
    listEl.innerHTML = snaps.map(snap => {
      const label = snap.label ? esc(snap.label) : '';
      const time = snap.created_at ? new Date(snap.created_at).toLocaleString() : '';
      return `<li><button type="button" class="load-snapshot-btn" data-id="${esc(snap.id)}">Load</button> ${label || snap.id} ${time ? `(${time})` : ''}</li>`;
    }).join('');
  }
}

function renderStateEnvelope(envelope){
  const publicState = envelope && envelope.public_state ? envelope.public_state : null;
  const authorState = envelope && envelope.author_state ? envelope.author_state : null;
  const debugState = envelope && envelope.debug_state ? envelope.debug_state : null;

  // Always clear any author-only widgets when not in author mode.
  if(currentUIMode !== "author" && $('sceneHiddenFacts')) $('sceneHiddenFacts').value = '';

  // Always clear debug surfaces when not in debug mode.
  if(currentUIMode !== "debug"){
    if($('debugBox')) $('debugBox').textContent = 'No debug data in this mode.';
    if($('actionPipelineDebugContent')) $('actionPipelineDebugContent').innerHTML = '';
    if($('actionTraceContent')) $('actionTraceContent').innerHTML = '';
  }

  if(publicState) renderPublicState(publicState);
  if(currentUIMode === "author" && authorState) renderAuthorState(authorState);
  if(currentUIMode === "debug" && debugState) renderDebugState(debugState);
}

function renderEngineDebug(s) {
  const panel = $('engineDebugPanel');
  const content = $('engineDebugContent');
  const toggle = $('engineDebugToggle');
  if (!panel || !content || !toggle) return;

  const d = s.debug || {};
  const traces = s.debug_traces || [];
  const latestTrace = traces[traces.length - 1];
  const res = d.resolver_result || {};

  const rollSkillParts = [];
  if (res.roll != null) rollSkillParts.push(`Roll: ${res.roll}`);
  if (res.total != null) rollSkillParts.push(`Total: ${res.total}`);
  if (res.hit != null) rollSkillParts.push(`Hit: ${res.hit}`);
  if (res.skill_id) rollSkillParts.push(`Skill: ${res.skill_id}`);
  if (res.skill_check != null) rollSkillParts.push(`Check: ${JSON.stringify(res.skill_check)}`);
  if (res.success != null) rollSkillParts.push(`Success: ${res.success}`);
  const rollSkillSummary = rollSkillParts.length ? rollSkillParts.join(' | ') : null;

  const worldUpdates = (latestTrace && latestTrace.world_flag_updates && latestTrace.world_flag_updates.length)
    ? latestTrace.world_flag_updates.join(', ')
    : null;

  const recentTraces = traces.slice(-5).reverse();

  let html = '<div class="engine-debug-inner action-pipeline-debug">';
  html += `<div class="debug-row"><strong>Last player input</strong><div class="debug-val">${esc(d.player_input || '(none)')}</div></div>`;
  html += `<div class="debug-row"><strong>Action type</strong><div class="debug-val">${esc(d.last_action_type || '')}</div></div>`;
  html += `<div class="debug-row"><strong>Normalized action</strong><pre class="debug-pre">${esc(d.normalized_action ? JSON.stringify(d.normalized_action, null, 2) : '(not exploration)')}</pre></div>`;
  html += `<div class="debug-row"><strong>Resolution kind</strong><div class="debug-val">${esc(d.resolution_kind || '')}</div></div>`;
  html += `<div class="debug-row"><strong>Target scene</strong><div class="debug-val">${esc(d.target_scene || '(none)')}</div></div>`;
  html += `<div class="debug-row"><strong>Resolved transition</strong><div class="debug-val">${d.scene_transition ? esc(`${d.scene_transition.from} → ${d.scene_transition.to}`) : 'No'}</div></div>`;
  if (rollSkillSummary) {
    html += `<div class="debug-row"><strong>Roll/skill summary</strong><div class="debug-val">${esc(rollSkillSummary)}</div></div>`;
  }
  if (worldUpdates) {
    html += `<div class="debug-row"><strong>World updates</strong><div class="debug-val">${esc(worldUpdates)}</div></div>`;
  }
  if (recentTraces.length) {
    html += '<div class="debug-row"><strong>Recent traces</strong><div class="engine-debug-traces">';
    for (const t of recentTraces) {
      const time = t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '—';
      const src = t.source || t.action_type || 'action';
      const kind = t.resolution?.kind || '';
      const err = t.error ? ` [${esc(t.error)}]` : '';
      html += `<div class="trace-item">${esc(time)} ${esc(src)} ${esc(kind)}${err}</div>`;
    }
    html += '</div></div>';
  }
  html += '</div>';

  if (traces.length === 0 && !d.last_action_type && !d.player_input) {
    content.innerHTML = '<p class="muted">No engine debug yet. Perform an action or send a chat message.</p>';
  } else {
    content.innerHTML = html;
  }
}

function setupEngineDebugToggle() {
  const panel = $('engineDebugPanel');
  const toggle = $('engineDebugToggle');
  const content = $('engineDebugContent');
  if (!panel || !toggle || !content) return;
  toggle.addEventListener('click', () => {
    const expanded = panel.classList.toggle('collapsed');
    toggle.setAttribute('aria-expanded', !expanded);
    toggle.innerHTML = expanded ? 'Engine Debug &#9654;' : 'Engine Debug &#9660;';
  });
}

function renderComposer(){
  const type = $('actionType').value;
  const body = $('composerBody');
  if(!state){ body.innerHTML=''; return; }
  if(type==='attack'){
    body.innerHTML = `
      <label>Attack</label>
      <select id="attackSelect">${(state.character.attacks||[]).map(a=>`<option value="${esc(a.id)}">${esc(a.name)} (+${a.attack_bonus})</option>`).join('')}</select>
      <label><input type="checkbox" id="modRisky"> Risky Strike</label>
      <label><input type="checkbox" id="modDefensive"> Defensive Stance</label>
      <button id="submitActionBtn">Submit Attack</button>`;
  } else if(type==='spell') {
    body.innerHTML = `
      <label>Spell</label>
      <select id="spellSelect">${(state.character.spells?.prepared||[]).map(sp=>`<option value="${esc(sp.id)}">${esc(sp.name)}${sp.cast ? ' (cast)' : ''}</option>`).join('')}</select>
      <button id="submitActionBtn">Cast Spell</button>`;
  } else if(type==='skill') {
    body.innerHTML = `
      <label>Skill</label>
      <select id="skillSelect">${Object.keys(state.character.skills||{}).sort().map(sk=>`<option value="${esc(sk)}">${esc(sk)}</option>`).join('')}</select>
      <label>Intent</label><textarea id="skillIntent"></textarea>
      <button id="submitActionBtn">Use Skill</button>`;
  } else {
    body.innerHTML = `<label>Freeform Intent</label><textarea id="freeIntent"></textarea><button id="submitActionBtn">Submit Freeform</button>`;
  }
  $('submitActionBtn').addEventListener('click', submitAction);
}

async function fetchJSON(url, options={}){
  const res = await fetch(url, options);
  return await res.json();
}

async function loadState(){
  const s = await fetchJSON(apiUrl('/state', {ui_mode: currentUIMode}));
  renderStateEnvelope(s);
}

function updateCampaignBootstrapUI(s){
  const panel = $('campaignBootstrapPanel');
  const btn = $('startCampaignBtn');
  const can = !!(s && s.ui && s.ui.campaign_can_start);
  if(panel){
    if(can){
      panel.style.display = 'block';
      panel.textContent = 'Fresh campaign loaded. Click Start Campaign to receive the opening scene.';
    } else {
      panel.style.display = 'none';
      panel.textContent = '';
    }
  }
  if(btn){
    btn.style.display = can ? '' : 'none';
    btn.disabled = !can || startCampaignBusy;
  }
}

async function loadLog(){
  const data = await fetchJSON(apiUrl('/log', {ui_mode: currentUIMode}));
  const entries = data && data.entries ? data.entries : [];
  $('chatLog').innerHTML = '';
  // Empty transcript after New Campaign / clear: no synthetic GM or system narration here (NC2).
  for(const entry of entries){
    const playerText = String(entry.player_input || entry.player_text || entry.request?.text || entry.request?.chat || entry.resolution?.metadata?.player_input || entry.resolution?.prompt || '').trim();
    if(playerText){
      const playerName = state?.player_name || state?.character?.name || 'You';
      addMessage('player', playerName, playerText);
    }
    addMessage('gm','GM',entry.gm_output?.player_facing_text || '(no narration)', entry.resolution);
  }
  if(state && currentUIMode === "player") updateCampaignBootstrapUI(state);
}

async function reloadAll(){ await loadState(); await loadLog(); }

async function sendChat(){
  if(currentUIMode !== "player") return;
  const text = $('chatInput').value.trim();
  if(!text) return;
  $('chatInput').value = '';
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, text);
  const thinking = addMessage('system','System','GM is thinking...');
  const data = await fetchJSON(apiUrl('/chat', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text, ui_mode: currentUIMode})});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)');
  await reloadAll();
}

async function submitAction(){
  if(currentUIMode !== "player") return;
  const type = $('actionType').value;
  let payload = {action_type:type};
  let label = '';
  if(type==='attack'){
    const modifiers=[];
    if($('modRisky')?.checked) modifiers.push('risky_strike');
    if($('modDefensive')?.checked) modifiers.push('defensive_stance');
    payload = {action_type:'attack', attack_id:$('attackSelect').value, target_id:$('targetSelect').value || null, modifiers};
    label = `Attack with ${payload.attack_id}`;
  } else if(type==='spell') {
    payload = {action_type:'cast_spell', spell_id:$('spellSelect').value, target_id:$('targetSelect').value || null};
    label = `Cast ${payload.spell_id}`;
  } else if(type==='skill') {
    payload = {action_type:'skill_check', skill_id:$('skillSelect').value, intent:$('skillIntent').value.trim()};
    label = payload.intent || `Use ${payload.skill_id}`;
  } else {
    payload = {action_type:'freeform', intent:$('freeIntent').value.trim()};
    label = payload.intent;
  }
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, label);
  const thinking = addMessage('system','System','Resolving action...');
  payload.ui_mode = currentUIMode;
  const data = await fetchJSON(apiUrl('/action', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  await reloadAll();
}

$('sendChatBtn').addEventListener('click', sendChat);
$('chatInput').addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendChat(); } });
$('actionType').addEventListener('change', renderComposer);
$('rollInitBtn').addEventListener('click', ()=>submitDirect({action_type:'roll_initiative'}, 'I roll initiative.'));
$('endTurnBtn').addEventListener('click', ()=>submitDirect({action_type:'end_turn'}, 'I end my turn.'));
$('clearLogBtn').addEventListener('click', async ()=>{
  if(currentUIMode !== "player") return;
  await fetchJSON(apiUrl('/clear_log', {ui_mode: currentUIMode}), {method:'POST'});
  await loadLog();
});
$('resetCombatBtn').addEventListener('click', async ()=>{
  if(currentUIMode !== "player") return;
  await fetchJSON(apiUrl('/reset_combat', {ui_mode: currentUIMode}), {method:'POST'});
  await loadState();
});
$('newCampaignBtn').addEventListener('click', async ()=>{
  const data = await fetchJSON(apiUrl('/new_campaign', {ui_mode: currentUIMode}), {method:'POST'});
  if (!data || data.ok === false || data.status === 'blocked' || data.status !== 'ok'){
    const msg = formatBlockedNewCampaignMessage(data);
    addMessage('error', 'System', msg, newCampaignBlockedDetails(data));
    return;
  }
  console.log('Campaign reset complete', data.campaign_run_id || '');
  state = null;
  location.reload();
});

const startCampaignBtn = $('startCampaignBtn');
if(startCampaignBtn){
  startCampaignBtn.addEventListener('click', async ()=>{
    if(currentUIMode !== "player") return;
    if(startCampaignBusy) return;
    if(!state?.ui?.campaign_can_start) return;
    startCampaignBusy = true;
    startCampaignBtn.disabled = true;
    const thinking = addMessage('system','System','Preparing opening…');
    try {
      const res = await fetch(apiUrl('/start_campaign', {ui_mode: currentUIMode}), {method:'POST'});
      const data = await res.json();
      if(res.status === 503 || data.status === 'blocked'){
        replaceMessage(thinking,'error','System', formatBlockedNewCampaignMessage(data), newCampaignBlockedDetails(data));
        return;
      }
      if(res.status === 409 || data.ok === false){
        replaceMessage(thinking,'error','System', data.error || 'Could not start campaign.');
        await reloadAll();
        return;
      }
      if(!data.ok){
        replaceMessage(thinking,'error','System', data.error || 'Unknown error');
        return;
      }
      replaceMessage(thinking,'gm','GM', data.gm_output?.player_facing_text || '(no narration)', data.resolution);
      await reloadAll();
    } finally {
      startCampaignBusy = false;
      if(state) updateCampaignBootstrapUI(state);
    }
  });
}
$('saveCampaignBtn').addEventListener('click', saveCampaign);
$('saveSceneBtn').addEventListener('click', saveScene);
$('activateSceneBtn').addEventListener('click', activateScene);
$('importSheetBtn').addEventListener('click', importSheet);

const createSnapshotBtn = $('createSnapshotBtn');
if (createSnapshotBtn) {
  createSnapshotBtn.addEventListener('click', async () => {
    if(currentUIMode !== "player") return;
    const label = ($('snapshotLabel') && $('snapshotLabel').value) ? $('snapshotLabel').value.trim() : null;
    const data = await fetchJSON(apiUrl('/snapshots', {ui_mode: currentUIMode}), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label: label || null, ui_mode: currentUIMode }) });
    if (data.ok) { addMessage('system', 'System', 'Snapshot created.'); await loadState(); }
    else addMessage('error', 'Error', data.error || 'Failed to create snapshot.');
  });
}
const snapListEl = $('snapshotsList');
if (snapListEl) {
  snapListEl.addEventListener('click', async (e) => {
    if(currentUIMode !== "player") return;
    const btn = e.target.closest('.load-snapshot-btn');
    if (!btn || !btn.dataset.id) return;
    const data = await fetchJSON(apiUrl('/snapshots/load', {ui_mode: currentUIMode}), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ snapshot_id: btn.dataset.id, ui_mode: currentUIMode }) });
    if (data.ok) { addMessage('system', 'System', 'Snapshot restored.'); await loadState(); }
    else addMessage('error', 'Error', data.error || 'Failed to load snapshot.');
  });
}

async function submitDirect(payload, label){
  if(currentUIMode !== "player") return;
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, label);
  const thinking = addMessage('system','System','Resolving action...');
  payload.ui_mode = currentUIMode;
  const data = await fetchJSON(apiUrl('/action', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error||'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  await reloadAll();
}

/** Submit a structured exploration action (affordance) to /api/action. Uses same log/error pattern as submitDirect. */
async function submitExplorationAction(affordance){
  if(currentUIMode !== "player") return;
  const label = affordance.label || (affordance.metadata && affordance.metadata.prompt) || 'Action';
  const prompt = (affordance.metadata && affordance.metadata.prompt) || affordance.prompt || label;
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, label);
  const thinking = addMessage('system','System','Resolving action...');
  const actionType = String(affordance.type || 'custom').toLowerCase();
  const isSocialAffordance = ['question', 'social_probe', 'persuade', 'intimidate', 'deceive', 'barter', 'recruit'].includes(actionType);
  const structuredAction = {
    id: affordance.id,
    label: affordance.label,
    type: actionType || 'custom',
    targetSceneId: affordance.targetSceneId || affordance.target_scene_id || null,
    targetEntityId: affordance.targetEntityId || affordance.target_id || null,
    targetLocationId: affordance.targetLocationId || affordance.target_location_id || null,
    prompt: prompt,
    metadata: affordance.metadata || {}
  };
  const payload = isSocialAffordance
    ? {
        action_type: 'social',
        intent: prompt,
        social_action: structuredAction
      }
    : {
        action_type: 'exploration',
        intent: prompt,
        exploration_action: structuredAction
      };
  payload.ui_mode = currentUIMode;
  const data = await fetchJSON(apiUrl('/action', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  await reloadAll();
}

async function saveCampaign(){
  if(currentUIMode !== "author") return;
  const payload = {
    ui_mode: currentUIMode,
    title: $('campaignTitle').value.trim(),
    premise: $('campaignPremise').value.trim(),
    tone: $('campaignTone').value.trim(),
    player_character: state?.character?.name || '',
    character_role: state?.campaign?.character_role || '',
    starting_context: $('campaignContext').value.trim(),
    gm_guidance: $('campaignGuidance').value.split('\n').map(x=>x.trim()).filter(Boolean)
  };
  const data = await fetchJSON(apiUrl('/campaign', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(data.ok) addMessage('system','System','Campaign saved.');
  await loadState();
}

async function saveScene(){
  if(currentUIMode !== "author") return;
  const base = state?.scene?.scene || {};
  const payload = {
    ui_mode: currentUIMode,
    scene: {
      ...base,
      id: $('sceneId').value.trim(),
      location: $('sceneLocation').value.trim(),
      summary: $('sceneSummary').value.trim(),
      mode: $('sceneMode').value.trim(),
      visible_facts: $('sceneVisibleFacts').value.split('\n').map(x=>x.trim()).filter(Boolean),
      discoverable_clues: $('sceneDiscoverableClues').value.split('\n').map(x=>x.trim()).filter(Boolean),
      hidden_facts: $('sceneHiddenFacts').value.split('\n').map(x=>x.trim()).filter(Boolean),
      exits: base.exits || [],
      enemies: base.enemies || []
    }
  };
  const data = await fetchJSON(apiUrl('/scene', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(data.ok) addMessage('system','System','Scene saved.');
  await loadState();
}

async function activateScene(){
  if(currentUIMode !== "player") return;
  const scene_id = $('scenePicker').value;
  const data = await fetchJSON(apiUrl('/scene/activate', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({scene_id, ui_mode: currentUIMode})});
  if(data.ok) addMessage('system','System',`Activated scene: ${scene_id}`);
  await reloadAll();
}

async function importSheet(){
  if(currentUIMode !== "player") return;
  const file = $('sheetFile').files[0];
  if(!file) return;
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(apiUrl('/import_sheet', {ui_mode: currentUIMode}), {method:'POST', body:form});
  const data = await res.json();
  if(data.ok){ addMessage('system','System','Character sheet imported.'); await loadState(); }
  else addMessage('error','Error',data.error || 'Import failed.');
}

function renderAffordances(affs){
  const bar = $('affordanceBar');
  const container = $('affordanceButtons');
  if(!bar || !container) return;
  container.innerHTML = '';
  if(!Array.isArray(affs) || !affs.length){
    bar.style.display = 'none';
    return;
  }
  bar.style.display = 'flex';
  for(const a of affs){
    if(!a || typeof a !== 'object') continue;
    const label = String(a.label ?? '').trim();
    if(!label) continue;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'affordance-pill';
    btn.textContent = label;
    const title = String((a.metadata && (a.metadata.hint || a.metadata.prompt)) || a.prompt || '').trim();
    if(title && title !== label){
      btn.title = title;
    }
    btn.addEventListener('click', ()=>{ submitExplorationAction(a); });
    container.appendChild(btn);
  }
  if(!container.children.length){
    bar.style.display = 'none';
  }
}

async function setResponseMode(){
  if(currentUIMode !== "player") return;
  const select = $('responseModeSelect');
  if(!select) return;
  const mode = select.value;
  await fetchJSON(apiUrl('/response_mode', {ui_mode: currentUIMode}), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode, ui_mode: currentUIMode})});
  await loadState();
}

if($('responseModeSelect')){
  $('responseModeSelect').addEventListener('change', setResponseMode);
}
setupEngineDebugToggle();

function mountUIModeSelector(){
  const tabs = document.querySelector('.tabs');
  if(!tabs) return;
  if(document.getElementById('uiModeSelect')) return;
  const wrap = document.createElement('div');
  wrap.className = 'ui-mode-selector';
  wrap.innerHTML = `
    <label for="uiModeSelect">UI Mode</label>
    <select id="uiModeSelect">
      <option value="player">Player</option>
      <option value="author">Author</option>
      <option value="debug">Debug</option>
    </select>
  `;
  tabs.parentElement.insertBefore(wrap, tabs);
  const select = $('uiModeSelect');
  select.value = currentUIMode;
  select.addEventListener('change', ()=>setUIMode(select.value));
  wrap.dataset.mode = currentUIMode;
}

function updateUIModeSelectorUI(){
  const select = $('uiModeSelect');
  if(select) select.value = currentUIMode;
  const wrap = select ? select.closest('.ui-mode-selector') : null;
  if(wrap) wrap.dataset.mode = currentUIMode;
}

async function setUIMode(mode){
  if(!isKnownUIMode(mode)) mode = DEFAULT_UI_MODE;
  currentUIMode = mode;
  persistUIMode(mode);
  updateUIModeSelectorUI();
  updateWorldModeHint(mode);
  clearForbiddenDomContentForMode(mode);
  applyVisibleTabsForMode(mode);
  enforceDomBoundariesForMode(mode);
  await reloadAll();
}

mountUIModeSelector();
updateWorldModeHint(currentUIMode);
applyVisibleTabsForMode(currentUIMode);
enforceDomBoundariesForMode(currentUIMode);
reloadAll();
