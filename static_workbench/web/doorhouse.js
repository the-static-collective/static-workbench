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
    const card=el("article",undefined,"receipt-card");
    card.append(el("strong","World "+receipt.world_before+" → "+receipt.world_after));
    card.append(el("div",receipt.snapshot.artifact.title));
    const details=document.createElement("details");
    details.append(el("summary","Inspect receipt + adapter truth"));
    details.append(el("code",JSON.stringify({
      execution:receipt.snapshot.execution,
      perturbation:receipt.snapshot.envelope.perturbation,
      adapters:receipt.snapshot.adapters,
      receipt_sha256:receipt.sha256
    },null,2)));
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
