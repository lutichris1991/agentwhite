HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AgentWhite</title>
<style>
:root{--bg:#07100d;--panel:#0d1915;--panel2:#11231d;--line:#1e3a30;--text:#d9f8e8;--muted:#83a795;--green:#5dffa7;--amber:#ffcc66;--red:#ff6b6b;--blue:#79c9ff}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 20% 0,#10261e 0,var(--bg) 38%);color:var(--text);font:14px/1.45 ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;min-height:100vh}
button,input{font:inherit}.shell{max-width:1280px;margin:0 auto;padding:24px}.top{display:flex;gap:18px;align-items:center;justify-content:space-between;margin-bottom:18px}.brand h1{margin:0;font-size:28px;letter-spacing:2px}.brand h1 span{color:var(--green)}.brand p{margin:4px 0 0;color:var(--muted)}.status{display:flex;gap:8px;flex-wrap:wrap}.pill{border:1px solid var(--line);background:#0a1511;padding:7px 10px;border-radius:999px;color:var(--muted)}.pill.ok{color:var(--green);border-color:#276344}.toolbar{display:flex;flex-wrap:wrap;gap:8px;padding:14px;background:rgba(13,25,21,.88);border:1px solid var(--line);border-radius:14px;position:sticky;top:8px;z-index:5;backdrop-filter:blur(12px)}button,.btn{border:1px solid #2d624c;background:#10291f;color:var(--text);padding:9px 12px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block}button:hover,.btn:hover{border-color:var(--green);color:var(--green)}button.primary{background:#173c2b;color:var(--green);border-color:#347d58}button.danger{border-color:#6c3838;background:#281414;color:#ffaaaa}.spacer{flex:1}.grid{display:grid;grid-template-columns:1.35fr .9fr;gap:16px;margin-top:16px}@media(max-width:900px){.grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}}.panel{background:rgba(13,25,21,.92);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-head{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}.panel-head h2{font-size:15px;margin:0;letter-spacing:.7px}.count{color:var(--muted)}.panel-body{padding:12px}.device{padding:13px;border:1px solid var(--line);border-radius:11px;background:var(--panel2);margin-bottom:10px}.device:last-child{margin-bottom:0}.device-top{display:flex;align-items:flex-start;gap:10px}.device-main{min-width:0;flex:1}.device-name{font-weight:700;font-size:15px;word-break:break-word}.device-sub{color:var(--muted);margin-top:3px;word-break:break-all}.badge{font-size:11px;text-transform:uppercase;padding:4px 7px;border-radius:999px;border:1px solid var(--line);color:var(--blue)}.badge.enrolled{color:var(--green);border-color:#347d58}.details{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.kv{background:#09140f;border:1px solid #183127;padding:4px 7px;border-radius:7px;color:var(--muted);max-width:100%;word-break:break-word}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:11px}.finding{border-left:3px solid var(--blue);padding:12px 12px 12px 13px;background:#0b1712;border-radius:8px;margin-bottom:9px}.finding.medium{border-left-color:var(--amber)}.finding.high,.finding.critical{border-left-color:var(--red)}.finding h3{font-size:13px;margin:0 0 6px}.finding p{margin:5px 0;color:var(--muted)}.proof{font-size:12px;white-space:pre-wrap;background:#050b08;border:1px solid #172a22;padding:8px;border-radius:7px;color:#abd5c0;max-height:220px;overflow:auto}.severity{font-size:10px;text-transform:uppercase;letter-spacing:.8px;margin-left:7px}.severity.medium{color:var(--amber)}.severity.high,.severity.critical{color:var(--red)}.agents{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.agent{border:1px solid var(--line);background:#0a1511;border-radius:9px;padding:9px}.agent strong{display:block;color:var(--green);font-size:12px}.agent span{color:var(--muted);font-size:11px}.empty{color:var(--muted);padding:20px;text-align:center}.toast{position:fixed;right:18px;bottom:18px;background:#10291f;border:1px solid #347d58;border-radius:10px;padding:12px 14px;max-width:380px;display:none;box-shadow:0 15px 50px #0008;z-index:30}.toast.error{background:#2a1515;border-color:#844}.filterbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.filterbar button.active{color:var(--green);border-color:var(--green)}
.modal{position:fixed;inset:0;background:#000b;display:none;align-items:center;justify-content:center;padding:18px;z-index:20}.modal.open{display:flex}.modal-card{width:min(980px,100%);max-height:90vh;overflow:auto;background:#08120e;border:1px solid #2f6650;border-radius:14px;box-shadow:0 30px 100px #000}.modal-head{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:14px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:#08120e;z-index:2}.modal-head h2{font-size:15px;margin:0}.modal-body{padding:16px}.preview-image{display:block;max-width:100%;max-height:58vh;margin:12px auto;border:1px solid var(--line);border-radius:8px}.proof-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:12px}@media(max-width:700px){.proof-grid{grid-template-columns:1fr}}.gatt-service{border:1px solid var(--line);border-radius:9px;padding:10px;margin-bottom:10px;background:#0b1712}.gatt-service h3{margin:0 0 8px;font-size:12px;color:var(--green)}.gatt-char{padding:8px;border-top:1px solid #183127}.gatt-char:first-of-type{border-top:0}.success{color:var(--green)}.blocked{color:var(--amber)}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div class="brand"><h1>AGENT<span>WHITE</span></h1><p>Local wireless + device security validation console</p></div>
    <div class="status"><span class="pill ok">LOCAL ONLY</span><span id="version-pill" class="pill">v0.2</span><span id="ai-pill" class="pill">AI: checking</span><span id="db-pill" class="pill">Evidence DB</span></div>
  </div>

  <div class="toolbar">
    <button class="primary" onclick="discover('all')">Scan Everything</button>
    <button onclick="discover('wifi')">Wi-Fi</button>
    <button onclick="discover('lan')">LAN</button>
    <button onclick="discover('bluetooth')">Bluetooth</button>
    <span class="spacer"></span>
    <a class="btn" href="/api/export" target="_blank">Export Evidence JSON</a>
    <button onclick="refreshState()">Refresh</button>
  </div>

  <div class="grid">
    <div class="panel">
      <div class="panel-head"><h2>DISCOVERED ASSETS</h2><span id="device-count" class="count">0</span></div>
      <div class="panel-body">
        <div class="filterbar">
          <button id="f-all" class="active" onclick="setFilter('all')">All</button>
          <button id="f-wifi" onclick="setFilter('wifi')">Wi-Fi</button>
          <button id="f-lan" onclick="setFilter('lan')">LAN</button>
          <button id="f-bluetooth" onclick="setFilter('bluetooth')">Bluetooth</button>
        </div>
        <div id="devices"><div class="empty">Run a scan to populate the local asset map.</div></div>
      </div>
    </div>

    <div>
      <div class="panel" style="margin-bottom:16px">
        <div class="panel-head"><h2>AGENT ARMY</h2><span class="count">proof-first</span></div>
        <div class="panel-body"><div id="agents" class="agents"></div></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>VERIFIED FINDINGS</h2><span id="finding-count" class="count">0</span></div>
        <div class="panel-body" id="findings"><div class="empty">No verified findings yet.</div></div>
      </div>
    </div>
  </div>
</div>

<div id="proof-modal" class="modal" onclick="modalBackdrop(event)">
  <div class="modal-card">
    <div class="modal-head"><h2 id="proof-title">Proof Viewer</h2><button onclick="closeProof()">Close</button></div>
    <div id="proof-body" class="modal-body"></div>
  </div>
</div>
<div id="toast" class="toast"></div>
<script>
let state={devices:[],findings:[],agents:[],ai:{}}; let filter='all';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function toast(msg,error=false){const e=document.getElementById('toast');e.textContent=msg;e.className='toast'+(error?' error':'');e.style.display='block';setTimeout(()=>e.style.display='none',3600)}
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});let data={};try{data=await r.json()}catch{}if(!r.ok)throw new Error(data.error||('Request failed: '+r.status));return data}
async function refreshState(){try{state=await api('/api/state');render()}catch(e){toast(e.message,true)}}
async function discover(kind){toast('Recon Agent scanning '+kind+'...');try{const r=await api('/api/discover',{method:'POST',body:JSON.stringify({kind})});toast('Scan complete: '+r.discovered+' assets observed');await refreshState()}catch(e){toast(e.message,true)}}
async function enroll(id,value){try{await api('/api/enroll',{method:'POST',body:JSON.stringify({device_id:id,enrolled:value})});toast(value?'Target enrolled for authorized validation':'Target removed from active scope');await refreshState()}catch(e){toast(e.message,true)}}
async function verify(id){toast('Verification Agent testing enrolled target...');try{const r=await api('/api/verify',{method:'POST',body:JSON.stringify({device_id:id})});toast(r.message||('Verification complete: '+r.verified+' observations confirmed'));await refreshState()}catch(e){toast(e.message,true)}}
function setFilter(v){filter=v;document.querySelectorAll('.filterbar button').forEach(b=>b.classList.remove('active'));document.getElementById('f-'+v).classList.add('active');renderDevices()}
function showProof(title,html){document.getElementById('proof-title').textContent=title;document.getElementById('proof-body').innerHTML=html;document.getElementById('proof-modal').classList.add('open')}
function closeProof(){document.getElementById('proof-modal').classList.remove('open')}
function modalBackdrop(e){if(e.target.id==='proof-modal')closeProof()}
function proofKv(obj){return Object.entries(obj||{}).filter(([,v])=>v!==null&&v!==undefined&&v!=='').map(([k,v])=>`<div class="kv"><strong>${esc(k)}</strong>: ${esc(typeof v==='object'?JSON.stringify(v):v)}</div>`).join('')}
async function inspectBluetooth(id){toast('AccessScope Agent establishing BLE inspection session...');try{const r=await api('/api/inspect',{method:'POST',body:JSON.stringify({device_id:id})});const x=r.inspection||{};const services=(x.services||[]).map(s=>`<div class="gatt-service"><h3>${esc(s.description||'GATT service')} — ${esc(s.uuid)}</h3>${(s.characteristics||[]).map(c=>{const read=c.read_result;const readHtml=read?`<div class="proof">${read.text?esc(read.text):esc(read.hex||'')}</div>`:(c.read_status==='blocked'?`<div class="blocked">Read blocked: ${esc(c.read_error||'authorization required')}</div>`:'');return `<div class="gatt-char"><div><strong>${esc(c.description||'Characteristic')}</strong></div><div class="device-sub">${esc(c.uuid)}</div><div class="details"><span class="kv">properties: ${esc((c.properties||[]).join(', '))}</span><span class="kv">read: ${esc(c.read_status||'not readable')}</span></div>${readHtml}</div>`}).join('')}</div>`).join('');showProof('Bluetooth Proof-of-Access',`<div class="proof-grid">${proofKv({connected:x.connected,services:x.service_count,characteristics:x.characteristic_count,readable:x.readable_count,address:x.address})}</div>${services||'<div class="empty">Session established, but no GATT services were exposed.</div>'}`);toast('BLE inspection complete');await refreshState()}catch(e){toast(e.message,true)}}
async function viewHttpResource(id){const portRaw=prompt('HTTP/HTTPS port to verify (80, 443, 8000, 8080, or 8443):','80');if(portRaw===null)return;const port=Number(portRaw);if(!Number.isInteger(port)){toast('Port must be a number.',true);return}const path=prompt('Resource path to retrieve from the enrolled device:','/');if(path===null)return;toast('AccessScope Agent retrieving explicitly selected resource...');try{const r=await api('/api/resource',{method:'POST',body:JSON.stringify({device_id:id,port,path})});const x=r.resource||{};let preview='';if(x.image_data_url)preview=`<img class="preview-image" src="${esc(x.image_data_url)}" alt="Retrieved proof" />`;else if(x.text_preview!==undefined)preview=`<div class="proof">${esc(x.text_preview)}</div>`;else if(x.hex_preview)preview=`<div class="proof">${esc(x.hex_preview)}</div>`;showProof('HTTP Resource Proof',`<div class="proof-grid">${proofKv({verified:r.verified,status:x.status,reason:x.reason,content_type:x.content_type,bytes_captured:x.bytes_captured,sha256:x.sha256,evidence_path:x.evidence_path,address:x.address,port:x.port,path:x.path})}</div>${preview||'<div class="empty">The endpoint responded without previewable content.</div>'}`);toast(r.verified?'Resource access verified':'Resource was blocked or challenged');await refreshState()}catch(e){toast(e.message,true)}}
function render(){document.getElementById('version-pill').textContent='v'+(state.version||'0.2');document.getElementById('device-count').textContent=state.devices.length+' assets';document.getElementById('finding-count').textContent=state.findings.length;const a=state.ai||{};const pill=document.getElementById('ai-pill');pill.textContent=a.available?'Local AI: '+a.model:'Local AI: rule engine';pill.className='pill '+(a.available?'ok':'');renderAgents();renderDevices();renderFindings()}
function renderAgents(){const el=document.getElementById('agents');el.innerHTML=(state.agents||[]).map(a=>`<div class="agent"><strong>${esc(a.name)}</strong><span>${esc(a.role)}</span></div>`).join('')}
function renderDevices(){const el=document.getElementById('devices');const rows=(state.devices||[]).filter(d=>filter==='all'||d.kind===filter);if(!rows.length){el.innerHTML='<div class="empty">No assets in this view yet.</div>';return}el.innerHTML=rows.map(d=>{const detail=Object.entries(d.details||{}).filter(([,v])=>v!==null&&v!=='').slice(0,8).map(([k,v])=>`<span class="kv">${esc(k)}: ${esc(Array.isArray(v)?v.join(', '):v)}</span>`).join('');const action=d.enrolled?`<button class="danger" onclick="enroll('${esc(d.id)}',false)">Remove Scope</button>`:`<button onclick="enroll('${esc(d.id)}',true)">Enroll Target</button>`;let active='';if(d.enrolled){if(d.kind==='lan')active=`<button class="primary" onclick="verify('${esc(d.id)}')">Verify Services</button><button onclick="viewHttpResource('${esc(d.id)}')">View HTTP Proof</button>`;else if(d.kind==='wifi')active=`<button class="primary" onclick="verify('${esc(d.id)}')">Audit Configuration</button>`;else if(d.kind==='bluetooth')active=`<button class="primary" onclick="inspectBluetooth('${esc(d.id)}')">Inspect Access</button>`}return `<div class="device"><div class="device-top"><div class="device-main"><div class="device-name">${esc(d.name)}</div><div class="device-sub">${esc(d.address||'No address exposed by OS')}</div></div><span class="badge ${d.enrolled?'enrolled':''}">${d.enrolled?'ENROLLED':esc(d.kind)}</span></div><div class="details">${detail||'<span class="kv">No extra metadata</span>'}</div><div class="actions">${action}${active}</div></div>`}).join('')}
function serviceUrl(p){if(!p||!p.address||!p.port)return null;if([80,8000,8080].includes(Number(p.port)))return `http://${p.address}:${p.port}/`;if([443,8443].includes(Number(p.port)))return `https://${p.address}:${p.port}/`;return null}
function renderFindings(){const el=document.getElementById('findings');if(!(state.findings||[]).length){el.innerHTML='<div class="empty">No verified findings yet.</div>';return}el.innerHTML=state.findings.map(f=>{const url=serviceUrl(f.proof);const open=url?`<a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Open Verified Service</a>`:'';return `<div class="finding ${esc(f.severity)}"><h3>${esc(f.title)} <span class="severity ${esc(f.severity)}">${esc(f.severity)}</span></h3><p><strong>Proof</strong></p><div class="proof">${esc(JSON.stringify(f.proof,null,2))}</div><p><strong>Patch guidance:</strong> ${esc(f.remediation)}</p><div class="actions">${open}</div></div>`}).join('')}
refreshState();
</script>
</body>
</html>'''
