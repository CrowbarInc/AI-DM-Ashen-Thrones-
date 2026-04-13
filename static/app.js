const API = '/api';
let state = null;

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

function renderState(s){
  state = s;
  $('charSummary').innerHTML = `
    <strong>${esc(s.character.name)}</strong> — Level ${esc(s.character.level)} ${esc(s.character.class)}<br>
    HP: ${s.character.hp.current}/${s.character.hp.max}<br>
    AC: ${s.character.ac.normal} | Touch ${s.character.ac.touch} | Flat-Footed ${s.character.ac.flat_footed}<br>
    Conditions: ${(s.character.conditions||[]).map(c=>c.name).join(', ') || 'none'}`;
  $('combatStatus').textContent = s.combat.in_combat ? `Round ${s.combat.round} | Active: ${s.combat.active_actor_id || 'none'} | Action spent: ${s.combat.player_turn_used}` : 'Combat inactive.';
  $('enemyStatus').innerHTML = (s.ui.living_enemies||[]).map(e=>`${e.name}: ${e.hp}/${e.max_hp}`).join('<br>') || 'No living enemies.';
  $('sceneHeader').textContent = s.scene.scene.location;
  $('sceneSubheader').textContent = s.scene.scene.summary;
  $('sceneNameDisplay').textContent = s.scene.scene.location || s.scene.scene.id || '';
  $('sceneModeDisplay').textContent = s.scene.scene.mode || '';
  // Save summary: last saved, active scene at save, whether save data exists
  const saveCard = $('saveSummaryCard');
  const saveCont = $('saveSummaryContent');
  if(saveCard && saveCont){
    const sm = s.save_summary || {};
    const savedAt = sm.saved_at ? new Date(sm.saved_at).toLocaleString() : 'Never';
    const hasData = sm.save_data_exists ? 'Yes' : 'No';
    saveCont.innerHTML = `
      <div><strong>Last saved:</strong> ${esc(savedAt)}</div>
      <div><strong>Active scene at save:</strong> ${esc(sm.active_scene_id || s.session?.active_scene_id || '—')}</div>
      <div><strong>Save data exists:</strong> ${hasData}</div>
      <div class="muted" style="margin-top:4px">Auto-saves on each action/chat. ${sm.discovered_clues ?? 0} clues, ${sm.chat_messages ?? 0} log entries.</div>
    `;
  }
  // Response mode selector reflects current session state.
  if(s.session && s.session.response_mode && $('responseModeSelect')){
    $('responseModeSelect').value = s.session.response_mode;
  }
  $('characterBox').textContent = JSON.stringify(s.character,null,2);
  $('worldFactions').textContent = JSON.stringify(s.world.factions,null,2);
  // Projects list
  const projects = s.world.projects || [];
  $('worldProjectsList').innerHTML = projects.map(p=>`<li><strong>${esc(p.name)}</strong> — ${esc(p.status)} (${p.progress}/${p.target})</li>`).join('') || '<li class="muted">No active projects.</li>';
  // Events list
  const events = (s.world.event_log||[]).slice(-10);
  $('worldEventsList').innerHTML = events.map(ev=>`<li>${esc(ev.text || JSON.stringify(ev))}</li>`).join('') || '<li class="muted">No recent events.</li>';
  // Journal
  const journal = s.journal || {};
  const knownFacts = journal.known_facts || [];
  const clues = (journal.discovered_clues || []).concat(journal.unresolved_leads || []);
  $('journalKnownFacts').innerHTML = knownFacts.map(f=>`<li>${esc(f)}</li>`).join('') || '<li class="muted">No facts recorded yet.</li>';
  $('journalClues').innerHTML = clues.map(c=>`<li>${esc(c)}</li>`).join('') || '<li class="muted">No clues discovered yet.</li>';
  $('worldDebugBox').textContent = JSON.stringify({factions:s.world.factions, projects:s.world.projects, events:s.world.event_log}, null, 2);
  $('debugBox').textContent = JSON.stringify(s,null,2);

  // Action Pipeline Debug: Player input, Parsed action, Resolver result, Scene transition
  const adb = $('actionPipelineDebugContent');
  const adbCard = $('actionPipelineDebugCard');
  if(adb && adbCard){
    const d = s.debug;
    if(d){
      adbCard.style.display = 'block';
      adb.innerHTML = `
        <div class="debug-row"><strong>Player input</strong><div class="debug-val">${esc(d.player_input || '(none)')}</div></div>
        <div class="debug-row"><strong>Action type</strong><div class="debug-val">${esc(d.last_action_type || '')}</div></div>
        <div class="debug-row"><strong>Parsed action</strong><pre class="debug-pre">${esc(d.normalized_action ? JSON.stringify(d.normalized_action,null,2) : '(not exploration)')}</pre></div>
        <div class="debug-row"><strong>Resolver result</strong><pre class="debug-pre">${esc(d.resolver_result ? JSON.stringify(d.resolver_result,null,2) : '(none)')}</pre></div>
        <div class="debug-row"><strong>Resolution kind</strong><div class="debug-val">${esc(d.resolution_kind || '')}</div></div>
        <div class="debug-row"><strong>Scene transition</strong><div class="debug-val">${d.scene_transition ? esc(`${d.scene_transition.from} → ${d.scene_transition.to}`) : '(none)'}</div></div>
      `;
    } else {
      adbCard.style.display = 'block';
      adb.innerHTML = '<p class="muted">No action pipeline debug yet. Perform an action or send a chat message.</p>';
    }
  }

  // Action Trace: most recent debug trace
  const atc = $('actionTraceCard');
  const atCont = $('actionTraceContent');
  if(atc && atCont){
    const traces = s.debug_traces || [];
    const latest = traces[traces.length - 1];
    if(latest){
      atc.style.display = 'block';
      atCont.innerHTML = `<pre class="debug-pre">${esc(JSON.stringify(latest,null,2))}</pre>`;
      if(typeof console !== 'undefined' && console.log) console.log('[Action Trace]', latest);
    } else {
      atc.style.display = 'block';
      atCont.innerHTML = '<p class="muted">No trace yet. Perform an action or send a chat message.</p>';
    }
  }

  $('campaignTitle').value = s.campaign.title || '';
  $('campaignPremise').value = s.campaign.premise || '';
  $('campaignTone').value = s.campaign.tone || '';
  $('campaignContext').value = s.campaign.starting_context || '';
  $('campaignGuidance').value = (s.campaign.gm_guidance || []).join('\n');

  $('sceneId').value = s.scene.scene.id || '';
  $('sceneLocation').value = s.scene.scene.location || '';
  $('sceneSummary').value = s.scene.scene.summary || '';
  $('sceneMode').value = s.scene.scene.mode || '';
  $('sceneVisibleFacts').value = (s.scene.scene.visible_facts || []).join('\n');
  $('sceneDiscoverableClues').value = (s.scene.scene.discoverable_clues || []).join('\n');
  $('sceneHiddenFacts').value = (s.scene.scene.hidden_facts || []).join('\n');

  $('scenePicker').innerHTML = (s.ui.scene_ids || []).map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join('');
  $('scenePicker').value = s.session.active_scene_id;
  $('targetSelect').innerHTML = (s.ui.living_enemies || []).map(e=>`<option value="${esc(e.id)}">${esc(e.name)} (${e.hp}/${e.max_hp})</option>`).join('');
  renderAffordances(s.ui.affordances || []);
  renderComposer();
  renderEngineDebug(s);

  // Save Slots: list snapshots with Load buttons
  const listEl = $('snapshotsList');
  if (listEl) {
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
  const s = await fetchJSON(API+'/state');
  renderState(s);
}

async function loadLog(){
  const {entries} = await fetchJSON(API+'/log');
  $('chatLog').innerHTML = '';
  if(!entries.length) addMessage('system','System','GM ready.');
  for(const entry of entries){
    addMessage('gm','GM',entry.gm_output?.player_facing_text || '(no narration)', entry.resolution);
  }
}

async function reloadAll(){ await loadState(); await loadLog(); }

async function sendChat(){
  const text = $('chatInput').value.trim();
  if(!text) return;
  $('chatInput').value = '';
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, text);
  const thinking = addMessage('system','System','GM is thinking...');
  const data = await fetchJSON(API+'/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)');
  renderState(data);
}

async function submitAction(){
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
  const data = await fetchJSON(API+'/action', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  renderState(data);
}

$('sendChatBtn').addEventListener('click', sendChat);
$('chatInput').addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendChat(); } });
$('actionType').addEventListener('change', renderComposer);
$('rollInitBtn').addEventListener('click', ()=>submitDirect({action_type:'roll_initiative'}, 'I roll initiative.'));
$('endTurnBtn').addEventListener('click', ()=>submitDirect({action_type:'end_turn'}, 'I end my turn.'));
$('clearLogBtn').addEventListener('click', async ()=>{ await fetchJSON(API+'/clear_log',{method:'POST'}); await loadLog(); });
$('resetCombatBtn').addEventListener('click', async ()=>{ await fetchJSON(API+'/reset_combat',{method:'POST'}); await loadState(); });
$('newCampaignBtn').addEventListener('click', async ()=>{
  const data = await fetchJSON(API+'/new_campaign', {method:'POST'});
  if (!data || data.ok === false || data.status === 'blocked' || data.status !== 'ok'){
    const msg = formatBlockedNewCampaignMessage(data);
    addMessage('error', 'System', msg, newCampaignBlockedDetails(data));
    return;
  }
  console.log('Campaign reset complete', data.campaign_run_id || '');
  state = null;
  location.reload();
});
$('saveCampaignBtn').addEventListener('click', saveCampaign);
$('saveSceneBtn').addEventListener('click', saveScene);
$('activateSceneBtn').addEventListener('click', activateScene);
$('importSheetBtn').addEventListener('click', importSheet);

const createSnapshotBtn = $('createSnapshotBtn');
if (createSnapshotBtn) {
  createSnapshotBtn.addEventListener('click', async () => {
    const label = ($('snapshotLabel') && $('snapshotLabel').value) ? $('snapshotLabel').value.trim() : null;
    const data = await fetchJSON(API + '/snapshots', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label: label || null }) });
    if (data.ok) { addMessage('system', 'System', 'Snapshot created.'); await loadState(); }
    else addMessage('error', 'Error', data.error || 'Failed to create snapshot.');
  });
}
const snapListEl = $('snapshotsList');
if (snapListEl) {
  snapListEl.addEventListener('click', async (e) => {
    const btn = e.target.closest('.load-snapshot-btn');
    if (!btn || !btn.dataset.id) return;
    const data = await fetchJSON(API + '/snapshots/load', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ snapshot_id: btn.dataset.id }) });
    if (data.ok) { addMessage('system', 'System', 'Snapshot restored.'); await loadState(); }
    else addMessage('error', 'Error', data.error || 'Failed to load snapshot.');
  });
}

async function submitDirect(payload, label){
  const playerName = state?.player_name || state?.character?.name || 'You';
  addMessage('player', playerName, label);
  const thinking = addMessage('system','System','Resolving action...');
  const data = await fetchJSON(API+'/action',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error||'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  renderState(data);
}

/** Submit a structured exploration action (affordance) to /api/action. Uses same log/error pattern as submitDirect. */
async function submitExplorationAction(affordance){
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
    targetSceneId: affordance.targetSceneId || null,
    targetEntityId: affordance.targetEntityId || affordance.target_id || null,
    targetLocationId: affordance.targetLocationId || null,
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
  const data = await fetchJSON(API+'/action', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  if(!data.ok){ replaceMessage(thinking,'error','Error',data.error || 'Unknown error'); return; }
  replaceMessage(thinking,'gm','GM',data.gm_output?.player_facing_text || '(no narration)', data.resolution);
  renderState(data);
}

async function saveCampaign(){
  const payload = {
    title: $('campaignTitle').value.trim(),
    premise: $('campaignPremise').value.trim(),
    tone: $('campaignTone').value.trim(),
    player_character: state?.character?.name || '',
    character_role: state?.campaign?.character_role || '',
    starting_context: $('campaignContext').value.trim(),
    gm_guidance: $('campaignGuidance').value.split('\n').map(x=>x.trim()).filter(Boolean)
  };
  const data = await fetchJSON(API+'/campaign',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(data.ok) addMessage('system','System','Campaign saved.');
  await loadState();
}

async function saveScene(){
  const base = state?.scene?.scene || {};
  const payload = {
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
  const data = await fetchJSON(API+'/scene',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if(data.ok) addMessage('system','System','Scene saved.');
  await loadState();
}

async function activateScene(){
  const scene_id = $('scenePicker').value;
  const data = await fetchJSON(API+'/scene/activate',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({scene_id})});
  if(data.ok) addMessage('system','System',`Activated scene: ${scene_id}`);
  await reloadAll();
}

async function importSheet(){
  const file = $('sheetFile').files[0];
  if(!file) return;
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(API+'/import_sheet',{method:'POST', body:form});
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
  const select = $('responseModeSelect');
  if(!select) return;
  const mode = select.value;
  await fetchJSON(API+'/response_mode', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode})});
  await loadState();
}

if($('responseModeSelect')){
  $('responseModeSelect').addEventListener('change', setResponseMode);
}
setupEngineDebugToggle();

reloadAll();
