"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let token = "";
  let selected = null;
  const note = (text, error=false) => { $("message").textContent=text; $("message").classList.toggle("error",error); };
  async function api(path, opts={}) {
    const headers = {Accept:"application/json", ...(opts.body ? {"Content-Type":"application/json","x-workbench-session":token} : {})};
    const response = await fetch(path, {...opts,headers,credentials:"same-origin"});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.error || "Request refused");
    return data;
  }
  const momentUrl = id => "/api/lifestream/moments/" + encodeURIComponent(id);
  function line(parent, label, value) {
    const p=document.createElement("p");const strong=document.createElement("strong");
    strong.textContent=label+" ";p.append(strong, document.createTextNode(String(value)));parent.append(p);
  }
  async function loadMoments() {
    const result=await api("/api/lifestream/moments");
    $("moments").replaceChildren();
    if (!result.moments.length) { $("moments").textContent="No imported moments.";return; }
    for(const moment of result.moments){
      const b=document.createElement("button");
      b.type="button";b.className="entry";
      b.textContent=moment.eventId+" · "+moment.span.startMs+"–"+moment.span.endMs+" ms · "+moment.momentId.slice(0,18);
      b.addEventListener("click",()=>selectMoment(moment.momentId).catch(e=>note(e.message,true)));
      $("moments").append(b);
    }
  }
  async function selectMoment(id) {
    // Selection is never permission to mutate or to trust a previously saved digest.
    const moment=await api(momentUrl(id));
    selected=id;
    $("detail").replaceChildren();
    const title=document.createElement("h2");title.textContent="Verified moment";$("detail").append(title);
    line($("detail"),"Event:",moment.eventId);
    line($("detail"),"Moment:",moment.momentId);
    line($("detail"),"Source SHA-256:",moment.sourceSha256);
    line($("detail"),"Media offsets (declared):",moment.span.startMs+"–"+moment.span.endMs+" ms");
    line($("detail"),"Recording start (declared):",moment.time.recordingStartedAtUtc);
    line($("detail"),"Observed at:",moment.time.observedAtUtc);
    const h=document.createElement("h3");h.textContent="Independent clock witnesses";$("detail").append(h);
    if(!moment.clockWitnesses.length){
      line($("detail"),"Clocks:","None supplied; no clock correlation inferred.");
    } else {
      for (const w of moment.clockWitnesses) {
        const card=document.createElement("div");card.style.borderTop="1px solid #555";
        line(card,w.clockId+":",w.reading);
        line(card,"Basis:",w.basis);
        line(card,"Observed:",w.observedAtUtc);
        line(card,"Evidence:",w.evidenceRef);
        $("detail").append(card);
      }
    }
    $("compose").hidden=false;
    await loadReturns();
    note("Source verified. No artifact has been performed or broadcast.");
  }
  async function loadReturns(){
    if(!selected)return;
    const result=await api(momentUrl(selected)+"/returns");
    $("returns").replaceChildren();
    if(!result.returns.length){$("returns").textContent="No saved returns.";return;}
    for(const item of result.returns){
      const button=document.createElement("button");
      button.type="button";button.className="entry";
      button.textContent="Export "+item.kind+" · "+item.createdAt+" · "+item.returnId.slice(0,18);
      button.addEventListener("click",async()=>{
        try {
          const returned=await api(momentUrl(selected)+"/returns/"+encodeURIComponent(item.returnId));
          const blob=new Blob([JSON.stringify(returned,null,2)+"\n"],{type:"application/json"});
          const href=URL.createObjectURL(blob);
          const a=document.createElement("a");a.href=href;a.download="lifestream-"+item.returnId.slice(7,19)+".json";
          document.body.append(a);a.click();a.remove();
          setTimeout(()=>URL.revokeObjectURL(href),3000);
          note("Private JSON return exported. STATIC LIVE must verify it separately; no broadcast or stage action occurred.");
        } catch(e){note(e.message,true);}
      });
      $("returns").append(button);
    }
  }
  $("import-form").addEventListener("submit",async e=>{
    e.preventDefault();
    try {
      const result=await api("/api/lifestream/moments/import",{
        method:"POST",body:JSON.stringify({
          root_id:$("root").value,manifest_path:$("manifest").value,source_path:$("source").value
        })
      });
      await loadMoments(); await selectMoment(result.momentId);
      note("Moment imported after source verification. No automatic publication.");
    }catch(error){note(error.message,true);}
  });
  $("draft-form").addEventListener("submit",async e=>{
    e.preventDefault();
    if(!selected||!$("reviewed").checked){note("Select a verified moment and explicitly review the text.",true);return;}
    try{
      const result=await api(momentUrl(selected)+"/returns",{
        method:"POST",body:JSON.stringify({
          kind:$("kind").value,text:$("draft").value,admitted_by:$("admitted-by").value,reviewed:true
        })
      });
      $("reviewed").checked=false;
      await loadReturns();
      note("Reviewed local candidate saved: "+result.returnId+". No broadcast, stage or publish effect.");
    }catch(error){note(error.message,true);}
  });
  async function start(){
    try{
      const bootstrap=await api("/api/bootstrap");
      token=bootstrap.session_token;
      $("root").replaceChildren();
      for(const root of bootstrap.roots){
        const option=document.createElement("option");option.value=root.id;
        option.textContent=root.id+" · "+root.path;$("root").append(option);
      }
      await loadMoments();note("Local inbox ready. Import an explicitly selected finished moment.");
    }catch(e){note(e.message,true);}
  }
  start();
})();