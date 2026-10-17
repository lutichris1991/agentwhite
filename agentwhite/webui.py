HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AgentWhite</title>
<style>
:root{--bg:#07100d;--panel:#0d1915;--panel2:#11231d;--line:#1e3a30;--text:#d9f8e8;--muted:#83a795;--green:#5dffa7;--amber:#ffcc66;--red:#ff6b6b;--blue:#79c9ff}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 20% 0,#10261e 0,var(--bg) 38%);color:var(--text);font:14px/1.45 ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;min-height:100vh}
button,input{font:inherit}.shell{max-width:1280px;margin:0 auto;padding:24px}.top{display:flex;gap:18px;align-items:center;justify-content:space-between;margin-bottom:18px}.brand h1{margin:0;font-size:28px;letter-spacing:2px}.brand h1 span{color:var(--green)}.brand p{margin:4px 0 0;color:var(--muted)}.status{display:flex;gap:8px;flex-wrap:wrap}.pill{border:1px solid var(--line);background:#0a1511;padding:7px 10px;border-radius:999px;color:var(--muted)}.pill.ok{color:var(--green);border-color:#276344}.toolbar{display:flex;flex-wrap:wrap;gap:8px;padding:14px;background:rgba(13,25,21,.88);border:1px solid var(--line);border-radius:14px;position:sticky;top:8px;z-index:5;backdrop-filter:blur(12px)}button,.btn{border:1px solid #2d624c;background:#10291f;color:var(--text);padding:9px 12px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block}button:hover,.btn:hover{border-color:var(--green);color:var(--green)}button.primary{background:#173c2b;color:var(--green);border-color:#347d58}button.danger{border-color:#6c3838;background:#281414;color:#ffaaaa}.spacer{flex:1}.grid{display:grid;grid-template-columns:1.35fr .9fr;gap:16px;margin-top:16px}@media(max-width:900px){.grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}}.panel{background:rgba(13,25,21,.92);border:1px solid var(--line);border-radius:14px;overflow:hidden}.panel-head{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}.panel-head h2{font-size:15px;margin:0;letter-spacing:.7px}.count{color:var(--muted)}.panel-body{padding:12px}.device{padding:13px;border:1px solid var(--line);border-radius:11px;background:var(--panel2);margin-bottom:10px}.device:last-child{margin-bottom:0}.device-top{display:flex;align-items:flex-start;gap:10px}.device-main{min-width:0;flex:1}.device-name{font-weight:700;font-size:15px;word-break:break-word}.device-sub{color:var(--muted);margin-top:3px;word-break:break-all}.badge{font-size:11px;text-transform:uppercase;padding:4px 7px;border-radius:999px;border:1px solid var(--line);color:var(--blue)}.badge.enrolled{color:var(--green);border-color:#347d58}.details{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.kv{background:#09140f;border:1px solid #183127;padding:4px 7px;border-radius:7px;color:var(--muted);max-width:100%;word-break:break-word}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:11px}.finding{border-left:3px solid var(--blue);padding:12px 12px 12px 13px;background:#0b1712;border-radius:8px;margin-bottom:9px}.finding.medium{border-left-color:var(--amber)}.finding.high,.finding.critical{border-left-color:var(--red)}.finding h3{font-size:13px;margin:0 0 6px}.finding p{margin:5px 0;color:var(--muted)}.proof{font-size:12px;white-space:pre-wrap;background:#050b08;border:1px solid #172a22;padding:8px;border-radius:7px;color:#abd5c0;max-height:180px;overflow:auto}.severity{font-size:10px;text-transform:uppercase;letter-spacing:.8px;margin-left:7px}.severity.medium{color:var(--amber)}.severity.high,.severity.critical{color:var(--red)}.agents{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.agent{border:1px solid var(--line);background:#0a1511;border-radius:9px;padding:9px}.agent strong{display:block;color:var(--green);font-size:12px}.agent span{color:var(--muted);font-size:11px}.empty{color:var(--muted);padding:20px;text-align:center}.toast{position:fixed;right:18px;bottom:18px;background:#10291f;border:1px solid #347d58;border-radius:10px;padding:12px 14px;max-width:380px;display:none;box-shadow:0 15px 50px #0008}.toast.error{background:#2a1515;border-color:#844}.filterbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.filterbar button.active{color:var(--green);border-color:var(--green)}
.modal{display:none;position:fixed;inset:0;background:#000a;z-index:20;padding:24px;align-items:center;justify-content:center}.modal.open{display:flex}.modal-card{width:min(960px,100%);max-height:92vh;overflow:auto;background:#09140f;border:1px solid #2e5946;border-radius:14px;box-shadow:0 30px 100px #000}.modal-head{display:flex;gap:12px;align-items:center;padding:14px;border-bottom:1px solid var(--line);position:sticky;top:0;background:#09140f;z-index:2}.modal-head strong{flex:1}.modal-body{padding:14px}.pathbar{display:flex;gap:8px;margin-bottom:12px}.pathbar input{flex:1;background:#050b08;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px}.viewer-meta{white-space:pre-wrap;color:var(--muted);background:#050b08;border:1px solid var(--line);padding:9px;border-radius:8px;margin-bottom:10px}.viewer-content{background:#020604;border:1px solid var(--line);border-radius:8px;padding:10px;overflow:auto;max-height:58vh}.viewer-content pre{white-space:pre-wrap;word-break:break-word;margin:0}.viewer-content img{display:block;max-width:100%;height:auto;margin:auto}.status-label{font-size:10px;text-transform:uppercase;color:var(--muted);margin-left:6px}.gatt-service{border:1px solid var(--line);border-radius:8px;margin-bottom:10px;background:#07100d}.gatt-title{padding:9px;color:var(--green);border-bottom:1px solid var(--line);word-break:break-all}.gatt-char{padding:9px;border-bottom:1px solid #14271f}.gatt-char:last-child{border-bottom:0}.gatt-value{margin-top:7px;white-space:pre-wrap;word-break:break-word;color:#abd5c0;background:#030806;border:1px solid #14271f;border-radius:6px;padding:7px}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div class="brand"><h1>AGENT<span>WHITE</span></h1><p>Local wireless + device security validation console</p></div>
    <div class="status"><span class="pill ok">LOCAL ONLY</span><span id="ai-pill" class="pill">AI: checking</span><span id="db-pill" class="pill">Evidence DB</span></div>
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
        <div class="panel-head"><h2>AGENT ARMY</h2><span class="count">v0.2</span></div>
        <div class="panel-body"><div id="agents" class="agents"></div></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>VERIFIED FINDINGS</h2><span id="finding-count" class="count">0</span></div>
        <div class="panel-body" id="findings"><div class="empty">No verified findings yet.</div></div>
      </div>
    </div>
  </div>
</div>

<div id="viewer" class="modal" onclick="if(event.target===this)closeViewer()">
  <div class="modal-card">
    <div class="modal-head"><strong id="viewer-title">VERIFIED ACCESS VIEWER</strong><button onclick="closeViewer()">Close</button></div>
    <div class="modal-body">
      <div id="viewer-pathbar" class="pathbar"><input id="viewer-path" value="/" aria-label="HTTP resource path" /><button class="primary" onclick="loadResource()">Fetch Path</button></div>
      <div id="viewer-meta" class="viewer-meta">No response loaded.</div>
      <div id="viewer-content" class="viewer-content"><div class="empty">Select a verified HTTP/HTTPS service or an enrolled BLE device.</div></div>
    </div>
  </div>
</div>

<div id="toast" class="toast"></div>
<script>
let state={devices:[],findings:[],agents:[],ai:{}}; let filter='all'; let viewerContext=null;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function toast(msg,error=false){const e=document.getElementById('toast');e.textContent=msg;e.className='toast'+(error?' error':'');e.style.display='block';setTimeout(()=>e.style.display='none',3400)}
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});let data={};try{data=await r.json()}catch{}if(!r.ok)throw new Error(data.error||('Request failed: '+r.status));return data}
async function refreshState(){try{state=await api('/api/state');render()}catch(e){toast(e.message,true)}}
async function discover(kind){toast('Recon Agent scanning '+kind+'...');try{const r=await api('/api/discover',{method:'POST',body:JSON.stringify({kind})});toast('Scan complete: '+r.discovered+' assets observed');await refreshState()}catch(e){toast(e.message,true)}}
async function enroll(id,value){try{await api('/api/enroll',{method:'POST',body:JSON.stringify({device_id:id,enrolled:value})});toast(value?'Target enrolled for authorized validation':'Target removed from active scope');await refreshState()}catch(e){toast(e.message,true)}}
async function verify(id){toast('Verification Agent testing enrolled target...');try{const r=await api('/api/verify',{method:'POST',body:JSON.stringify({device_id:id})});toast(r.message||('Verification complete: '+r.verified+' observations confirmed'));await refreshState()}catch(e){toast(e.message,true)}}
function setFilter(v){filter=v;document.querySelectorAll('.filterbar button').forEach(b=>b.classList.remove('active'));document.getElementById('f-'+v).classList.add('active');renderDevices()}
function render(){document.getElementById('device-count').textContent=state.devices.length+' assets';document.getElementById('finding-count').textContent=state.findings.length;const a=state.ai||{};const pill=document.getElementById('ai-pill');pill.textContent=a.available?'Local AI: '+a.model:'Local AI: rule engine';pill.className='pill '+(a.available?'ok':'');renderAgents();renderDevices();renderFindings()}
function renderAgents(){const el=document.getElementById('agents');el.innerHTML=(state.agents||[]).map(a=>`<div class="agent"><strong>${esc(a.name)}</strong><span>${esc(a.role)}</span></div>`).join('')}
function renderDevices(){const el=document.getElementById('devices');const rows=(state.devices||[]).filter(d=>filter==='all'||d.kind===filter);if(!rows.length){el.innerHTML='<div class="empty">No assets in this view yet.</div>';return}el.innerHTML=rows.map(d=>{const detail=Object.entries(d.details||{}).filter(([,v])=>v!==null&&v!=='').slice(0,8).map(([k,v])=>`<span class="kv">${esc(k)}: ${esc(Array.isArray(v)?v.join(', '):v)}</span>`).join('');const action=d.enrolled?`<button class="danger" onclick="enroll('${esc(d.id)}',false)">Remove Scope</button>`:`<button onclick="enroll('${esc(d.id)}',true)">Enroll Target</button>`;let test='';if(d.enrolled&&d.kind==='lan')test=`<button class="primary" onclick="verify('${esc(d.id)}')">Verify Services</button>`;else if(d.enrolled&&d.kind==='wifi')test=`<button class="primary" onclick="verify('${esc(d.id)}')">Audit Configuration</button>`;else if(d.enrolled&&d.kind==='bluetooth')test=`<button class="primary" onclick="inspectBluetooth('${esc(d.id)}')">Inspect Access</button>`;return `<div class="device"><div class="device-top"><div class="device-main"><div class="device-name">${esc(d.name)}</div><div class="device-sub">${esc(d.address||'No address exposed by OS')}</div></div><span class="badge ${d.enrolled?'enrolled':''}">${d.enrolled?'ENROLLED':esc(d.kind)}</span></div><div class="details">${detail||'<span class="kv">No extra metadata</span>'}</div><div class="actions">${action}${test}</div></div>`}).join('')}
function serviceUrl(p){if(!p||!p.address||!p.port)return null;if([80,8000,8080].includes(Number(p.port)))return `http://${p.address}:${p.port}/`;if([443,8443].includes(Number(p.port)))return `https://${p.address}:${p.port}/`;return null}
function renderFindings(){const el=document.getElementById('findings');if(!(state.findings||[]).length){el.innerHTML='<div class="empty">No verified findings yet.</div>';return}el.innerHTML=state.findings.map(f=>{const url=serviceUrl(f.proof);const open=url&&f.category==='service-exposure'?`<a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Open Service</a>`:'';const view=url&&f.category==='service-exposure'?`<button class="primary" onclick="openViewer('${esc(f.device_id)}',${Number(f.proof.port)})">View Returned Material</button>`:'';const status=f.status?`<span class="status-label">${esc(f.status)}</span>`:'';return `<div class="finding ${esc(f.severity)}"><h3>${esc(f.title)} <span class="severity ${esc(f.severity)}">${esc(f.severity)}</span>${status}</h3><p><strong>Proof</strong></p><div class="proof">${esc(JSON.stringify(f.proof,null,2))}</div><p><strong>Patch guidance:</strong> ${esc(f.remediation)}</p><div class="actions">${view}${open}</div></div>`}).join('')}
function openViewer(deviceId,port){viewerContext={device_id:deviceId,port:Number(port)};document.getElementById('viewer-title').textContent='VERIFIED HTTP ACCESS VIEWER';document.getElementById('viewer-pathbar').style.display='flex';document.getElementById('viewer-path').value='/';document.getElementById('viewer').classList.add('open');loadResource()}
function closeViewer(){document.getElementById('viewer').classList.remove('open');document.getElementById('viewer-pathbar').style.display='flex';viewerContext=null}
async function loadResource(){if(!viewerContext)return;const path=document.getElementById('viewer-path').value||'/';const meta=document.getElementById('viewer-meta');const content=document.getElementById('viewer-content');meta.textContent='Verification Agent retrieving '+path+'...';content.innerHTML='';try{const r=await api('/api/resource',{method:'POST',body:JSON.stringify({...viewerContext,path})});const x=r.resource||{};meta.textContent=`Status: ${x.status} ${x.reason||''}\nContent-Type: ${x.content_type||'unknown'}\nBytes captured: ${x.bytes_captured||0}${x.truncated?' (truncated)':''}\nSHA-256: ${x.sha256||'n/a'}\nEvidence: ${x.evidence_path||'none'}`;if(x.image_data_url){const img=document.createElement('img');img.src=x.image_data_url;img.alt='Verified returned image evidence';content.appendChild(img)}else{const pre=document.createElement('pre');pre.textContent=x.text_preview||x.hex_preview||'The endpoint returned no previewable body.';content.appendChild(pre)}toast(r.verified?'Returned material verified':'Endpoint responded but access was blocked/challenged');await refreshState()}catch(e){meta.textContent='Viewer error: '+e.message;const pre=document.createElement('pre');pre.textContent=e.message;content.replaceChildren(pre);toast(e.message,true)}}
async function inspectBluetooth(deviceId){viewerContext=null;const modal=document.getElementById('viewer');const meta=document.getElementById('viewer-meta');const content=document.getElementById('viewer-content');document.getElementById('viewer-title').textContent='BLUETOOTH PROOF-OF-ACCESS VIEWER';document.getElementById('viewer-pathbar').style.display='none';modal.classList.add('open');meta.textContent='AccessScope Agent establishing BLE session and enumerating exposed GATT resources...';content.innerHTML='';try{const r=await api('/api/inspect',{method:'POST',body:JSON.stringify({device_id:deviceId})});const x=r.inspection||{};meta.textContent=`Connected: ${x.connected?'yes':'no'}\nAddress: ${x.address||'unknown'}\nServices: ${x.service_count||0}\nCharacteristics: ${x.characteristic_count||0}\nReadable values returned: ${x.readable_count||0}`;for(const s of (x.services||[])){const box=document.createElement('div');box.className='gatt-service';const title=document.createElement('div');title.className='gatt-title';title.textContent=(s.description||'GATT service')+' — '+s.uuid;box.appendChild(title);for(const c of (s.characteristics||[])){const row=document.createElement('div');row.className='gatt-char';const head=document.createElement('div');head.textContent=(c.description||'Characteristic')+' — '+c.uuid;row.appendChild(head);const props=document.createElement('div');props.className='device-sub';props.textContent='Properties: '+(c.properties||[]).join(', ')+(c.read_status?' | Read: '+c.read_status:'');row.appendChild(props);if(c.read_result){const value=document.createElement('div');value.className='gatt-value';value.textContent=c.read_result.text||c.read_result.hex||'(empty value)';row.appendChild(value)}else if(c.read_error){const value=document.createElement('div');value.className='gatt-value';value.textContent='Read blocked: '+c.read_error;row.appendChild(value)}box.appendChild(row)}content.appendChild(box)}if(!(x.services||[]).length){const empty=document.createElement('div');empty.className='empty';empty.textContent='BLE session completed but no GATT services were exposed.';content.appendChild(empty)}toast('Bluetooth access inspection complete');await refreshState()}catch(e){meta.textContent='BLE inspection error: '+e.message;const pre=document.createElement('pre');pre.textContent=e.message;content.replaceChildren(pre);toast(e.message,true)}}
refreshState();
</script>
</body>
</html>'''
