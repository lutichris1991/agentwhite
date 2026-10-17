"""First-run/update-tools prompt injected into the local AgentWhite dashboard."""

SETUP_PROMPT_HTML = r'''
<style>
#aw-setup-launch{position:fixed;right:18px;top:18px;z-index:140;display:none}
#aw-setup-overlay{display:none;position:fixed;inset:0;z-index:150;background:rgba(0,3,2,.84);backdrop-filter:blur(6px);align-items:center;justify-content:center;padding:18px}
#aw-setup-overlay.open{display:flex}
#aw-setup-card{width:min(720px,100%);max-height:90vh;overflow:auto;background:linear-gradient(180deg,rgba(5,25,19,.98),rgba(2,12,10,.98));border:1px solid rgba(0,245,154,.5);border-radius:12px;box-shadow:0 30px 100px #000;padding:0;color:#eafff5}
#aw-setup-head{display:flex;gap:12px;align-items:center;padding:15px 16px;border-bottom:1px solid rgba(0,245,154,.22)}
#aw-setup-head strong{font-size:15px;letter-spacing:1px}
#aw-setup-body{padding:16px}
.aw-setup-stat{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.aw-setup-stat>div{border:1px solid rgba(0,245,154,.18);border-radius:8px;padding:10px;background:rgba(1,9,7,.65)}
.aw-setup-num{font-size:23px;font-weight:900;color:#00f59a}.aw-setup-muted{color:#82aa9a;font-size:11px}.aw-setup-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.aw-setup-btn{border:1px solid rgba(0,245,154,.42);border-radius:7px;padding:9px 12px;background:#0b2a20;color:#eafff5;cursor:pointer;font:inherit}.aw-setup-btn.primary{color:#00f59a;border-color:#00f59a}.aw-setup-btn:hover{box-shadow:0 0 18px rgba(0,245,154,.12)}
#aw-setup-results{margin-top:12px;white-space:pre-wrap;word-break:break-word;background:#010605;border:1px solid rgba(0,245,154,.15);border-radius:7px;padding:9px;color:#9ce9c7;max-height:260px;overflow:auto;display:none}
@media(max-width:600px){.aw-setup-stat{grid-template-columns:1fr}}
</style>
<button id="aw-setup-launch" class="aw-setup-btn primary" onclick="awOpenSetup()">Update Tools</button>
<div id="aw-setup-overlay" onclick="if(event.target===this)awCloseSetup()">
  <div id="aw-setup-card">
    <div id="aw-setup-head"><strong>AGENT WHITE · TOOL SETUP</strong><span id="aw-setup-status" class="aw-setup-muted">Checking this PC…</span></div>
    <div id="aw-setup-body">
      <div style="font-size:17px;font-weight:800">Keep AgentWhite ready with one button.</div>
      <div class="aw-setup-muted" style="margin-top:5px">AgentWhite can install approved Windows tool packages for you, then recheck what is available. Hardware-specific and other-OS tools stay separate and are never installed silently.</div>
      <div class="aw-setup-stat">
        <div><div id="aw-ready" class="aw-setup-num">0</div><div class="aw-setup-muted">READY NOW</div></div>
        <div><div id="aw-installable" class="aw-setup-num">0</div><div class="aw-setup-muted">CAN UPDATE</div></div>
        <div><div id="aw-manual" class="aw-setup-num">0</div><div class="aw-setup-muted">HARDWARE / MANUAL / OTHER OS</div></div>
      </div>
      <div id="aw-setup-message" class="aw-setup-muted"></div>
      <div class="aw-setup-actions">
        <button id="aw-update-all" class="aw-setup-btn primary" onclick="awUpdateAllTools()">Update Tools</button>
        <a class="aw-setup-btn" href="/tools" style="text-decoration:none">Open Tool Center</a>
        <button class="aw-setup-btn" onclick="awDismissSetup()">Not now</button>
      </div>
      <div id="aw-setup-results"></div>
    </div>
  </div>
</div>
<script>
let awSetupState=null;
async function awSetupApi(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},cache:'no-store',...opts});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.error||('Request failed: '+r.status));return d}
function awOpenSetup(){document.getElementById('aw-setup-overlay').classList.add('open')}
function awCloseSetup(){document.getElementById('aw-setup-overlay').classList.remove('open')}
function awDismissSetup(){if(awSetupState?.version)localStorage.setItem('agentwhiteSetupDismissedVersion',awSetupState.version);awCloseSetup()}
function awRenderSetup(d){awSetupState=d;const s=d.setup_summary||{};const ready=Number(s.ready||0),installable=Number(s.installable||0),manual=Number(s.external_setup||0)+Number(s.unsupported_platform||0)+Number(s.winget_missing||0)+Number(s.bundled_engine_missing||0);document.getElementById('aw-ready').textContent=ready;document.getElementById('aw-installable').textContent=installable;document.getElementById('aw-manual').textContent=manual;document.getElementById('aw-setup-status').textContent=installable?installable+' approved update(s) available':'Tool setup checked';document.getElementById('aw-update-all').disabled=!installable;document.getElementById('aw-update-all').textContent=installable?'Update Tools ('+installable+')':'Tools Up To Date';document.getElementById('aw-setup-message').textContent=installable?'Press Update Tools once. AgentWhite will install only its fixed approved Windows packages and then stop.':'No approved automatic tool installs are pending. Hardware/manual items can be reviewed in Tool Center.';const launch=document.getElementById('aw-setup-launch');launch.style.display='block';launch.textContent=installable?'Update Tools · '+installable:'Tools';const dismissed=localStorage.getItem('agentwhiteSetupDismissedVersion');if((installable>0||Number(s.bundled_engine_missing||0)>0)&&dismissed!==d.version)awOpenSetup()}
async function awCheckSetup(){try{const d=await awSetupApi('/api/tool-setup-status');awRenderSetup(d)}catch(e){document.getElementById('aw-setup-status').textContent='Setup check unavailable'}}
async function awUpdateAllTools(){const btn=document.getElementById('aw-update-all'),out=document.getElementById('aw-setup-results');btn.disabled=true;btn.textContent='Updating…';out.style.display='block';out.textContent='Installing approved tool packages. Windows may request permission for drivers or packages.\n';try{const d=await awSetupApi('/api/tool-setup-all',{method:'POST',body:'{}'});out.textContent=JSON.stringify(d.results||[],null,2);awRenderSetup(d);if((d.setup_summary||{}).installable===0)out.textContent+='\n\nAutomatic tool setup is complete. Restart AgentWhite if a newly installed executable is not detected immediately.'}catch(e){out.textContent+='\nERROR: '+e.message;btn.disabled=false;btn.textContent='Try Update Again'}}
document.addEventListener('DOMContentLoaded',awCheckSetup);
</script>
'''