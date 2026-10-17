from __future__ import annotations

from . import server

MODE_CSS = r'''
<style>
.aw-mode-strip{display:flex;gap:10px;align-items:center;justify-content:space-between;margin:0 0 10px;padding:10px 12px;border:1px solid rgba(0,245,154,.18);border-radius:8px;background:rgba(0,8,6,.76);box-shadow:inset 0 0 20px rgba(0,245,154,.025)}
.aw-mode-copy{min-width:0}.aw-mode-copy strong{color:var(--aw-green);letter-spacing:.08em}.aw-mode-copy div{margin-top:2px;color:var(--aw-muted);font-size:10px}.aw-mode-buttons{display:flex;gap:6px;flex-wrap:wrap}.aw-mode-btn.active{border-color:var(--aw-green);color:var(--aw-green);box-shadow:0 0 18px rgba(0,245,154,.12);background:rgba(0,245,154,.05)}
.aw-manual-shell{display:none;grid-template-columns:minmax(0,1.05fr) minmax(340px,.95fr);gap:10px;margin-bottom:10px}.aw-manual-shell.active{display:grid}.aw-manual-card{padding:11px;border:1px solid rgba(0,245,154,.14);border-radius:8px;background:rgba(0,8,6,.67)}.aw-manual-card h3{margin:0 0 8px;color:var(--aw-cyan);font-size:12px;letter-spacing:.08em}.aw-manual-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.aw-manual-field{display:grid;gap:4px}.aw-manual-field.full{grid-column:1/-1}.aw-manual-field label{font-size:9px;color:var(--aw-muted);letter-spacing:.08em;text-transform:uppercase}.aw-manual-field input,.aw-manual-field select{width:100%;box-sizing:border-box;background:#010605;color:#eafff6;border:1px solid rgba(0,245,154,.2);border-radius:7px;padding:9px;font:inherit}.aw-manual-field input:focus,.aw-manual-field select:focus{outline:none;border-color:var(--aw-green);box-shadow:0 0 0 2px rgba(0,245,154,.07)}.aw-manual-note{padding:8px;border:1px solid rgba(37,223,255,.18);border-radius:7px;background:rgba(0,20,22,.4);color:#a9eaf2;font-size:10px;line-height:1.45}.aw-request-preview,.aw-manual-output{min-height:120px;max-height:340px;overflow:auto;white-space:pre-wrap;word-break:break-word;background:#000403;border:1px solid rgba(0,245,154,.14);border-radius:7px;padding:9px;color:#bfffe3;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}.aw-manual-output{min-height:250px}.aw-catalog{max-height:215px;overflow:auto;display:grid;gap:5px}.aw-catalog-row{padding:7px;border:1px solid rgba(0,245,154,.1);border-radius:6px;background:rgba(0,9,7,.55);cursor:pointer}.aw-catalog-row:hover{border-color:rgba(0,245,154,.28)}.aw-catalog-row b{display:block;color:#d8fff0;font-size:10px}.aw-catalog-row span{color:var(--aw-muted);font-size:9px}.aw-mode-simple-hidden{display:none!important}.aw-dangerless{color:var(--aw-amber);font-size:9px}.aw-manual-actions{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-top:9px}@media(max-width:980px){.aw-manual-shell.active{grid-template-columns:1fr}.aw-mode-strip{align-items:flex-start;flex-direction:column}}@media(max-width:620px){.aw-manual-grid{grid-template-columns:1fr}.aw-manual-field.full{grid-column:auto}.aw-mode-buttons{width:100%}.aw-mode-buttons button{flex:1}}
</style>
'''

MODE_HTML = r'''
<div id="aw-mode-strip" class="aw-mode-strip">
  <div class="aw-mode-copy"><strong>OPERATOR MODE</strong><div>Choose the guided button interface or the advanced manual-input console. Both use the same policy, scope, logging, and stop-after-result controls.</div></div>
  <div class="aw-mode-buttons">
    <button id="aw-mode-simple-btn" class="aw-btn aw-mode-btn" onclick="awSetOperatorMode('simple')">▦ Simple Button Mode</button>
    <button id="aw-mode-advanced-btn" class="aw-btn aw-mode-btn" onclick="awSetOperatorMode('advanced')">⌘ Advanced Manual Mode</button>
  </div>
</div>
<section id="aw-advanced-mode" class="aw-manual-shell">
  <div class="aw-panel">
    <div class="aw-panel-head"><h2>⌘ ADVANCED MANUAL INPUT</h2><span class="aw-right aw-muted">Operator-entered IDs · same enforcement layer</span></div>
    <div class="aw-panel-body">
      <div class="aw-manual-note">Manual mode does not bypass AgentWhite controls. It lets an experienced operator enter registered action IDs and enrolled target IDs directly, while the server still rejects unknown actions, out-of-scope targets, arbitrary external-tool arguments, and automatic chaining.</div>
      <div class="aw-manual-grid" style="margin-top:9px">
        <div class="aw-manual-field full"><label>Operation family</label><select id="aw-manual-kind" onchange="awUpdateManualForm()"><option value="tool">Registered local tool action</option><option value="target">Enrolled target action</option></select></div>
        <div id="aw-tool-fields" class="aw-manual-field full"><label>Tool action ID</label><input id="aw-tool-action" list="aw-tool-actions" placeholder="Example: nmap.version" autocomplete="off" oninput="awRenderRequestPreview()"><datalist id="aw-tool-actions"></datalist></div>
        <div id="aw-target-device-wrap" class="aw-manual-field" style="display:none"><label>Enrolled target</label><select id="aw-target-device" onchange="awTargetChanged()"><option value="">Select enrolled target…</option></select></div>
        <div id="aw-target-action-wrap" class="aw-manual-field" style="display:none"><label>Target action ID</label><input id="aw-target-action" list="aw-target-actions" placeholder="Select or type an available action ID" autocomplete="off" oninput="awRenderRequestPreview()"><datalist id="aw-target-actions"></datalist></div>
        <div class="aw-manual-field full"><label>Request preview</label><pre id="aw-request-preview" class="aw-request-preview">{}</pre></div>
      </div>
      <div class="aw-manual-actions"><button id="aw-manual-run" class="aw-btn primary" onclick="awRunManualAction()">Run Manual Action</button><button class="aw-btn" onclick="awClearManualOutput()">Clear Output</button><span class="aw-dangerless">AUTO-CHAIN OFF · one action per submit</span></div>
    </div>
  </div>
  <div class="aw-panel">
    <div class="aw-panel-head"><h2>RAW RESULT / CATALOG</h2><span id="aw-manual-status" class="aw-right aw-muted">Ready</span></div>
    <div class="aw-panel-body">
      <pre id="aw-manual-output" class="aw-manual-output">Advanced manual mode ready. Choose an operation family and enter an approved action ID.</pre>
      <h3 style="margin-top:10px">AVAILABLE REGISTERED TOOL ACTIONS</h3>
      <div id="aw-manual-catalog" class="aw-catalog"><div class="aw-empty">Loading action catalog…</div></div>
    </div>
  </div>
</section>
'''

MODE_JS = r'''
<script>
const AW_MODE_KEY='agentwhite.operator.mode';
let awManualTools=[];let awManualDevices=[];let awManualWorkspace=null;
function awEsc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
async function awFetchJson(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},cache:'no-store',...opts});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.error||('Request failed: '+r.status));return d;}
function awSetOperatorMode(mode){mode=mode==='advanced'?'advanced':'simple';localStorage.setItem(AW_MODE_KEY,mode);const simple=document.getElementById('aw-simple-mode');const advanced=document.getElementById('aw-advanced-mode');document.getElementById('aw-mode-simple-btn')?.classList.toggle('active',mode==='simple');document.getElementById('aw-mode-advanced-btn')?.classList.toggle('active',mode==='advanced');if(simple)simple.classList.toggle('aw-mode-simple-hidden',mode==='advanced');if(advanced)advanced.classList.toggle('active',mode==='advanced');if(mode==='advanced')awRefreshManualCatalog();}
function awUpdateManualForm(){const kind=document.getElementById('aw-manual-kind').value;const isTarget=kind==='target';document.getElementById('aw-tool-fields').style.display=isTarget?'none':'grid';document.getElementById('aw-target-device-wrap').style.display=isTarget?'grid':'none';document.getElementById('aw-target-action-wrap').style.display=isTarget?'grid':'none';awRenderRequestPreview();}
function awManualRequest(){const kind=document.getElementById('aw-manual-kind').value;if(kind==='target')return{endpoint:'/api/action',body:{device_id:(document.getElementById('aw-target-device').value||'').trim(),action_id:(document.getElementById('aw-target-action').value||'').trim()}};return{endpoint:'/api/tool-action',body:{action_id:(document.getElementById('aw-tool-action').value||'').trim()}};}
function awRenderRequestPreview(){const req=awManualRequest();document.getElementById('aw-request-preview').textContent=JSON.stringify({method:'POST',endpoint:req.endpoint,body:req.body},null,2);}
function awRenderManualCatalog(actions){const el=document.getElementById('aw-manual-catalog');if(!actions.length){el.innerHTML='<div class="aw-empty">No approved registered actions are currently available.</div>';return;}el.innerHTML=actions.map(a=>`<div class="aw-catalog-row" onclick="awPickToolAction('${awEsc(a.id)}')"><b>${awEsc(a.id)} — ${awEsc(a.label)}</b><span>${awEsc(a.tool_id)} · ${awEsc(a.effect)} · ${awEsc(a.scope)} · ${a.available?'READY':'WAITING FOR TOOL'}</span></div>`).join('');}
function awPickToolAction(id){document.getElementById('aw-manual-kind').value='tool';awUpdateManualForm();document.getElementById('aw-tool-action').value=id;awRenderRequestPreview();}
async function awRefreshManualCatalog(){try{const [tools,stateData]=await Promise.all([awFetchJson('/api/tools'),awFetchJson('/api/state')]);awManualTools=tools.actions||[];awManualDevices=(stateData.devices||[]).filter(d=>d.enrolled);const dl=document.getElementById('aw-tool-actions');dl.innerHTML=awManualTools.map(a=>`<option value="${awEsc(a.id)}">${awEsc(a.label)}</option>`).join('');awRenderManualCatalog(awManualTools);const sel=document.getElementById('aw-target-device');const current=sel.value;sel.innerHTML='<option value="">Select enrolled target…</option>'+awManualDevices.map(d=>`<option value="${awEsc(d.id)}">${awEsc(d.name||d.address||d.id)} · ${awEsc(d.kind||'target')} · ${awEsc(d.address||'')}</option>`).join('');if(awManualDevices.some(d=>String(d.id)===String(current)))sel.value=current;document.getElementById('aw-manual-status').textContent=`${awManualTools.filter(a=>a.available).length} tool actions ready · ${awManualDevices.length} targets enrolled`;awRenderRequestPreview();}catch(e){document.getElementById('aw-manual-status').textContent='Catalog error';document.getElementById('aw-manual-output').textContent=e.message;}}
async function awTargetChanged(){const id=(document.getElementById('aw-target-device').value||'').trim();awManualWorkspace=null;document.getElementById('aw-target-actions').innerHTML='';document.getElementById('aw-target-action').value='';if(!id){awRenderRequestPreview();return;}try{awManualWorkspace=await awFetchJson('/api/workspace?device_id='+encodeURIComponent(id));const acts=awManualWorkspace.available_actions||[];document.getElementById('aw-target-actions').innerHTML=acts.map(a=>`<option value="${awEsc(a.id)}">${awEsc(a.label||a.id)}</option>`).join('');if(acts.length===1)document.getElementById('aw-target-action').value=acts[0].id;awRenderRequestPreview();}catch(e){document.getElementById('aw-manual-output').textContent=e.message;}}
async function awRunManualAction(){const req=awManualRequest();const body=req.body||{};if(!body.action_id){document.getElementById('aw-manual-output').textContent='Enter an action ID first.';return;}if(req.endpoint==='/api/action'&&!body.device_id){document.getElementById('aw-manual-output').textContent='Choose an enrolled target first.';return;}const btn=document.getElementById('aw-manual-run');btn.disabled=true;document.getElementById('aw-manual-status').textContent='Running one action…';document.getElementById('aw-manual-output').textContent='Submitting '+req.endpoint+'\n'+JSON.stringify(body,null,2);try{const result=await awFetchJson(req.endpoint,{method:'POST',body:JSON.stringify(body)});document.getElementById('aw-manual-output').textContent=JSON.stringify(result,null,2);document.getElementById('aw-manual-status').textContent='Completed · stopped after result';await awRefreshManualCatalog();if(typeof load==='function')await load();}catch(e){document.getElementById('aw-manual-output').textContent='ERROR\n'+e.message;document.getElementById('aw-manual-status').textContent='Rejected / failed';}finally{btn.disabled=false;}}
function awClearManualOutput(){document.getElementById('aw-manual-output').textContent='Output cleared. Ready for the next manual action.';}
window.addEventListener('DOMContentLoaded',()=>{awUpdateManualForm();awSetOperatorMode(localStorage.getItem(AW_MODE_KEY)||'simple');awRefreshManualCatalog();});
</script>
'''


def enable_mode_switch() -> None:
    """Layer the Simple/Advanced operator selector onto the existing Tool Center."""
    if 'id="aw-mode-strip"' in server.TOOLS_HTML:
        return
    html = server.TOOLS_HTML
    html = html.replace("</head>", MODE_CSS + "</head>", 1)
    html = html.replace('<div class="tool-layout">', MODE_HTML + '<div id="aw-simple-mode" class="tool-layout">', 1)
    html = html.replace("</body>", MODE_JS + "</body>", 1)
    server.TOOLS_HTML = html
