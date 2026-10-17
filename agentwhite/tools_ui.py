TOOLS_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>AgentWhite Tool Registry</title>
<style>
:root{--bg:#07100d;--panel:#0d1915;--panel2:#11231d;--line:#1e3a30;--text:#d9f8e8;--muted:#83a795;--green:#5dffa7;--amber:#ffcc66;--red:#ff6b6b;--blue:#79c9ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#10261e 0,var(--bg) 40%);color:var(--text);font:14px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;min-height:100vh}.shell{max-width:1300px;margin:auto;padding:22px}.top,.row,.filters{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.top{justify-content:space-between;margin-bottom:14px}.brand{font-size:24px;font-weight:800;letter-spacing:1px}.brand span{color:var(--green)}.btn,button{border:1px solid #2d624c;background:#10291f;color:var(--text);padding:8px 11px;border-radius:8px;cursor:pointer;text-decoration:none}.btn:hover,button:hover{border-color:var(--green);color:var(--green)}.panel{background:rgba(13,25,21,.94);border:1px solid var(--line);border-radius:12px;overflow:hidden}.head{padding:13px 15px;border-bottom:1px solid var(--line)}.body{padding:12px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}@media(max-width:850px){.grid{grid-template-columns:1fr}}.card{border:1px solid var(--line);background:var(--panel2);border-radius:10px;padding:12px}.title{font-weight:800;font-size:15px}.muted{color:var(--muted)}.badge{font-size:10px;padding:3px 6px;border:1px solid var(--line);border-radius:999px;text-transform:uppercase}.badge.ok{color:var(--green);border-color:#347d58}.badge.warn{color:var(--amber)}.badge.bad{color:var(--red)}.right{margin-left:auto}.meta{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.chip{font-size:11px;padding:4px 6px;background:#09140f;border:1px solid #183127;border-radius:6px;color:var(--muted)}.policy{margin-top:9px;padding:8px;background:#050b08;border:1px solid #172a22;border-radius:7px;color:#abd5c0}.empty{padding:24px;text-align:center;color:var(--muted)}input{background:#050b08;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:8px;min-width:240px}.summary{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
</style>
</head>
<body>
<div class="shell">
  <div class="top"><div><div class="brand">AGENT<span>WHITE</span> · TOOL REGISTRY</div><div class="muted">External engines stay behind AgentWhite scope, approval, evidence, and no-auto-chain rules.</div></div><a class="btn" href="/">Back to Dashboard</a></div>
  <div class="panel">
    <div class="head"><div class="row"><strong>CURATED TOOL PACK</strong><span class="right muted" id="count">Loading…</span></div></div>
    <div class="body">
      <div class="summary" id="summary"></div>
      <div class="filters"><input id="search" placeholder="Filter tools, protocols, hardware…" oninput="render()"/><button onclick="setMode('all')">All</button><button onclick="setMode('installed')">Installed</button><button onclick="setMode('missing')">Missing</button></div>
      <div id="tools" class="grid" style="margin-top:12px"><div class="empty">Loading registry…</div></div>
    </div>
  </div>
</div>
<script>
let rows=[];let mode='all';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function setMode(v){mode=v;render()}
async function load(){const r=await fetch('/api/tools',{cache:'no-store'});const d=await r.json();rows=d.tools||[];document.getElementById('count').textContent=rows.length+' registered tools';render()}
function render(){const q=(document.getElementById('search').value||'').toLowerCase();let view=rows.filter(x=>mode==='all'||(mode==='installed'&&x.installed)||(mode==='missing'&&!x.installed));view=view.filter(x=>JSON.stringify(x).toLowerCase().includes(q));const installed=rows.filter(x=>x.installed).length;document.getElementById('summary').innerHTML=`<span class="badge ok">${installed} detected</span><span class="badge">${rows.length-installed} available to integrate/install</span><span class="badge warn">AUTO-CHAIN DISABLED</span>`;document.getElementById('tools').innerHTML=view.length?view.map(x=>`<div class="card"><div class="row"><div><div class="title">${esc(x.name)}</div><div class="muted">${esc(x.category)} · ${esc(x.project)}</div></div><span class="right badge ${x.installed?'ok':'warn'}">${x.installed?'DETECTED':'NOT DETECTED'}</span></div><div class="meta"><span class="chip">${esc(x.effect)}</span><span class="chip">${esc(x.integration)}</span><span class="chip">${esc(x.bundle_policy)}</span>${(x.platforms||[]).map(p=>`<span class="chip">${esc(p)}</span>`).join('')}</div><div><strong>Capabilities</strong><div class="muted">${esc((x.capabilities||[]).join(' · '))}</div></div><div style="margin-top:7px"><strong>Hardware</strong><div class="muted">${esc((x.hardware||[]).join(' · ')||'No dedicated hardware requirement')}</div></div><div style="margin-top:7px"><strong>License note</strong><div class="muted">${esc(x.license_hint)}</div></div>${x.detected?.length?`<div style="margin-top:7px"><strong>Detected at</strong><div class="muted">${esc(x.detected.join(' · '))}</div></div>`:''}<div class="policy">Enrollment required: ${x.policy.requires_enrollment?'YES':'NO'} · Auto-chain: ${x.policy.auto_chain?'YES':'NO'} · Save evidence/results: ${x.policy.persist_results?'YES':'NO'}</div></div>`).join(''):'<div class="empty">No tools match this filter.</div>'}
load().catch(e=>document.getElementById('tools').innerHTML='<div class="empty">'+esc(e.message)+'</div>');
</script>
</body>
</html>'''
