"use strict";
let token = "";
let state = null;
const $ = (id) => document.getElementById(id);

function el(tag, text, className) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (className) n.className = className;
  return n;
}
async function api(path, payload) {
  const options = {headers:{Accept:"application/json"}};
  if (payload !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.headers["x-workbench-session"] = token;
    options.body = JSON.stringify(payload);
  }
  const res = await fetch(path, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "The House refused the crossing.");
  return data;
}
function say(text, bad=false){$("status").textContent=text;$("status").style.color=bad?"var(--danger)":"var(--muted)";}
function latestOpenLetter() {
  const newest = state.letters[0];
  return newest && newest.opened_at ? newest : null;
}
function renderLetters(){
  const root=$("letters"); root.replaceChildren();
  for(const letter of state.letters.slice(0,8)){
    const card=el("article",undefined,"letter-card"); card.dataset.open=String(Boolean(letter.opened_at));
    card.append(el("h3",letter.opened_at?letter.title:"✉ Sealed letter"));
    if(letter.opened_at){
      card.append(el("p",letter.body),el("small","SHA "+letter.sha256.slice(0,16)+"…"));
    } else {
      const b=el("button","Open letter"); b.type="button";
      b.addEventListener("click",()=>mutate("/api/doorhouse/letters/"+letter.id+"/open",{},"Letter opened."));
      card.append(el("p","Its contents have not entered the shared local world."),b);
    }
    root.append(card);
  }
}
function renderDoors(){
  const root=$("doors"); root.replaceChildren();
  const letter=latestOpenLetter();
  if(!letter){root.append(el("p","Open the newest sealed letter to reveal its proposed doors.","muted"));return;}
  const doors=state.doors.filter(d=>d.letter_id===letter.id);
  for(const door of doors){
    const card=el("article",undefined,"door-card");
    card.dataset.selected=String(Boolean(door.selected_at && !door.crossed_at));
    card.dataset.crossed=String(Boolean(door.crossed_at));
    card.append(el("h3",door.label),el("p",door.perturbation),el("div","possible adapter · "+door.adapter_hint,"adapter-line"));
    const actions=el("div",undefined,"door-actions");
    const select=el("button",door.selected_at?"Selected":"Select"); select.disabled=Boolean(door.crossed_at||door.selected_at);
    select.addEventListener("click",()=>mutate("/api/doorhouse/doors/"+door.id+"/select",{expected_world_version:state.world_version},"Door selected. Selection is not crossing."));
    const cross=el("button","Cross this door"); cross.disabled=!door.selected_at||Boolean(door.crossed_at);
    cross.addEventListener("click",()=>mutate("/api/doorhouse/doors/"+door.id+"/cross",{expected_world_version:state.world_version},"Crossing completed. The room changed."));
    actions.append(select,cross); card.append(actions); root.append(card);
  }
}
function renderReceipts(){
  const root=$("receipts"); root.replaceChildren();
  if(!state.receipts.length){root.append(el("p","No crossings yet. A selection alone leaves no occurrence receipt.","muted"));return;}
  for(const receipt of state.receipts){
    const relatte=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="relatte");
    const ghotExecution=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="ghot_execution");
    const autodiscoPacket=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="autodisco_packet");
    const autodiscoResponse=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="autodisco_first_response");
    const ghotOffers=state.external_witnesses
      .filter(w=>w.receipt_id===receipt.id&&w.kind.startsWith("ghot_offer:"))
      .sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
    const ghotOffer=ghotOffers[0]||null;
    const card=el("article",undefined,"receipt-card");
    card.append(el("strong","World "+receipt.world_before+" → "+receipt.world_after));
    card.append(el("div",receipt.snapshot.artifact.title));

    if(relatte){
      card.append(el("div","reLATTE · RECEIVED → HOLD · semantic effect: none","adapter-line"));
    } else {
      const send=el("button","Cross through reLATTE → HOLD");
      send.type="button";
      send.addEventListener("click",()=>mutate(
        "/api/doorhouse/receipts/"+receipt.id+"/relatte",
        {},
        "reLATTE verified the crossing, RECEIVED it, and returned a signed HOLD receipt."
      ));
      card.append(send);
    }

    if(relatte && !ghotExecution){
      if(!ghotOffer){
        const discover=el("button","Ask GHoT which bodies are awake");
        discover.type="button";
        discover.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/ghot/offers",
          {},
          "GHoT returned a body offer. No body has been assigned."
        ));
        card.append(discover);
      } else {
        const offer=ghotOffer.snapshot;
        const eligible=(offer.candidates||[]).filter(candidate=>candidate.eligible===true);
        const noun=eligible.length===1?"body":"bodies";
        card.append(el("div",eligible.length+" "+noun+" awake and able to run "+offer.capability+".","adapter-line"));
        const actions=el("div",undefined,"door-actions");
        for(const candidate of eligible){
          const label=candidate.hostname
            ? candidate.hostname+" · "+candidate.node_id.slice(0,18)
            : candidate.node_id;
          const choose=el("button","Assign "+label);
          choose.type="button";
          choose.addEventListener("click",()=>mutate(
            "/api/doorhouse/receipts/"+receipt.id+"/ghot/assign",
            {expected_offer_id:offer.offer_id,selected_node_id:candidate.node_id},
            "GHoT executed on the body you selected and returned its receipt."
          ));
          actions.append(choose);
        }
        const refresh=el("button","Refresh body offers");
        refresh.type="button";
        refresh.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/ghot/offers",
          {},
          "GHoT refreshed the body offer. No assignment was implied."
        ));
        actions.append(refresh);
        card.append(actions);
        if(!eligible.length){
          card.append(el("p","No currently observed body is eligible. Refresh after a body wakes or offers the capability.","muted"));
        }
      }
    }

    if(ghotExecution){
      const gw=ghotExecution.snapshot;
      card.append(el(
        "div",
        "GHoT · "+gw.executor_node_id+" · "+gw.capability+" · "+gw.status,
        "adapter-line"
      ));
      if(gw.creative_artifact){
        card.append(el(
          "div",
          "Haunted Toaster · "+gw.creative_artifact.instrument+" · SVG "+gw.creative_artifact.svg_sha256.slice(0,16)+"…",
          "adapter-line"
        ));
      }

      if(autodiscoResponse){
        const aw=autodiscoResponse.snapshot;
        card.append(el(
          "div",
          "Autodisco · fresh response sealed · "+aw.model_used,
          "adapter-line"
        ));
      } else {
        const listen=el(
          "button",
          autodiscoPacket ? "Try a real fresh listener again" : "Send returned artifact to a fresh listener"
        );
        listen.type="button";
        listen.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/autodisco/first-encounter",
          {},
          "Autodisco preserved the isolated packet and returned only what a real listener actually produced."
        ));
        card.append(listen);
        if(autodiscoPacket){
          card.append(el(
            "div",
            "Autodisco · packet sealed · no simulated response",
            "adapter-line"
          ));
        }
      }
    }

    const details=document.createElement("details");
    details.append(el("summary","Inspect receipt + adapter truth"));
    const evidence={
      execution:receipt.snapshot.execution,
      perturbation:receipt.snapshot.envelope.perturbation,
      adapters:receipt.snapshot.adapters,
      receipt_sha256:receipt.sha256
    };
    if(relatte) evidence.relatte_witness=relatte.snapshot;
    if(ghotOffer) evidence.ghot_offer=ghotOffer.snapshot;
    if(ghotExecution) evidence.ghot_execution=ghotExecution.snapshot;
    if(autodiscoPacket) evidence.autodisco_packet=autodiscoPacket.snapshot;
    if(autodiscoResponse) evidence.autodisco_first_response=autodiscoResponse.snapshot;
    details.append(el("code",JSON.stringify(evidence,null,2)));
    card.append(details); root.append(card);
  }
}
function render(){
  $("entry-panel").classList.toggle("doorhouse-hidden",state.entered);
  $("play-panel").classList.toggle("doorhouse-hidden",!state.entered);
  $("world-version").textContent=state.entered?String(state.world_version):"—";
  const laws=$("laws"); laws.replaceChildren(); for(const law of state.laws) laws.append(el("span",law,"law-chip"));
  if(state.entered){renderLetters();renderDoors();renderReceipts();}
}
async function mutate(path,payload,message){
  try{state=await api(path,payload);render();say(message);}
  catch(error){say(error.message,true); state=await api("/api/doorhouse/state"); render();}
}
async function start(){
  try{
    const boot=await api("/api/bootstrap"); token=boot.session_token;
    state=await api("/api/doorhouse/state"); render();
    $("enter-house").addEventListener("click",()=>mutate("/api/doorhouse/enter",{},"You entered. A sealed letter is waiting."));
    say(state.entered?"The House remembers. Nothing here chooses for you.":"The House has not been entered on this machine.");
  }catch(error){say(error.message,true);}
}
start();
