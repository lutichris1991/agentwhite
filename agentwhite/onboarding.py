from __future__ import annotations

from . import server

FIRST_RUN_MODE_HTML = r'''
<style>
#aw-mode-first-run{display:none;position:fixed;inset:0;z-index:220;background:rgba(0,3,2,.9);backdrop-filter:blur(8px);align-items:center;justify-content:center;padding:18px}
#aw-mode-first-run.open{display:flex}
#aw-mode-first-card{width:min(900px,100%);max-height:92vh;overflow:auto;background:linear-gradient(180deg,rgba(5,25,19,.99),rgba(2,12,10,.99));border:1px solid rgba(0,245,154,.5);border-radius:13px;box-shadow:0 30px 100px #000;color:#eafff5}
#aw-mode-first-head{padding:17px 18px;border-bottom:1px solid rgba(0,245,154,.22)}
#aw-mode-first-head strong{font-size:16px;letter-spacing:1.1px;color:#00f59a}
#aw-mode-first-body{padding:18px}.aw-first-muted{color:#8eb3a4;font-size:11px;line-height:1.5}.aw-mode-choice-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:15px}.aw-mode-choice{padding:16px;border:1px solid rgba(0,245,154,.2);border-radius:10px;background:rgba(0,9,7,.68)}.aw-mode-choice.advanced{border-color:rgba(37,223,255,.25)}.aw-mode-choice h3{margin:0 0 7px;font-size:15px;color:#dffff2}.aw-mode-choice ul{margin:10px 0 0;padding-left:18px;color:#a8cdbf;font-size:11px;line-height:1.55}.aw-mode-choice button{margin-top:14px;width:100%;border:1px solid #00f59a;border-radius:8px;padding:10px 12px;background:#0a2b20;color:#00f59a;cursor:pointer;font:inherit;font-weight:700}.aw-mode-choice.advanced button{border-color:#25dfff;color:#bcefff;background:#062229}.aw-mode-warning{margin-top:14px;padding:10px;border:1px solid rgba(255,212,91,.24);border-radius:8px;background:rgba(49,38,0,.22);color:#e6cf87;font-size:10px;line-height:1.5}@media(max-width:720px){.aw-mode-choice-grid{grid-template-columns:1fr}}
</style>
<div id="aw-mode-first-run">
  <div id="aw-mode-first-card">
    <div id="aw-mode-first-head"><strong>AGENT WHITE · CHOOSE YOUR OPERATOR MODE</strong></div>
    <div id="aw-mode-first-body">
      <div style="font-size:19px;font-weight:850">How do you want to run AgentWhite?</div>
      <div class="aw-first-muted" style="margin-top:5px">This is a local preference and can be changed later in Tool Center. Both modes are intended only for systems you own or are explicitly authorized to assess.</div>
      <div class="aw-mode-choice-grid">
        <div class="aw-mode-choice">
          <h3>▦ Simple Button Mode</h3>
          <div class="aw-first-muted">The current guided experience. AgentWhite presents only the actions available for the selected target or detected tool.</div>
          <ul><li>Button-driven workflow</li><li>Clear next-step choices</li><li>Target workspaces and saved evidence</li><li>Best for fast, repeatable validation</li></ul>
          <button onclick="awChooseFirstMode('simple')">Use Simple Mode</button>
        </div>
        <div class="aw-mode-choice advanced">
          <h3>⌘ Advanced Manual Mode</h3>
          <div class="aw-first-muted">An expert interface for directly entering registered action IDs, enrolled target IDs, and viewing raw request/result data.</div>
          <ul><li>Manual action selection and direct IDs</li><li>Raw JSON request previews and results</li><li>Same persistent history and evidence model</li><li>Designed for experienced operators</li></ul>
          <button onclick="awChooseFirstMode('advanced')">Use Advanced Mode</button>
        </div>
      </div>
      <div class="aw-mode-warning"><strong>Advanced does not mean unrestricted shell access.</strong> AgentWhite still enforces target enrollment, registered actions, one-action-per-submit behavior, logging, and policy checks. It does not accept arbitrary external-tool command lines through this interface.</div>
    </div>
  </div>
</div>
<script>
(function(){
  const key='agentwhite.operator.mode';
  window.awChooseFirstMode=function(mode){
    mode=mode==='advanced'?'advanced':'simple';
    localStorage.setItem(key,mode);
    localStorage.setItem('agentwhite.operator.mode.chosen','1');
    document.getElementById('aw-mode-first-run')?.classList.remove('open');
    if(mode==='advanced') window.location.href='/tools';
  };
  document.addEventListener('DOMContentLoaded',()=>{
    const chosen=localStorage.getItem('agentwhite.operator.mode.chosen');
    if(!chosen) document.getElementById('aw-mode-first-run')?.classList.add('open');
  });
})();
</script>
'''


def enable_first_run_mode_prompt() -> None:
    if 'id="aw-mode-first-run"' in server.HTML:
        return
    server.HTML = server.HTML.replace("</body>", FIRST_RUN_MODE_HTML + "</body>", 1)
