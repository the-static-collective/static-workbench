"use strict";
let token = "";
let state = null;
let fieldState = null;
let fieldReturns = [];
let roots = [];
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

async function copyJson(value){
  const text=JSON.stringify(value,null,2);
  await navigator.clipboard.writeText(text);
  say("Copied exact JSON to the clipboard.");
}

function downloadJson(value, filename){
  const blob=new Blob([JSON.stringify(value,null,2)+"\n"],{type:"application/json"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url;
  a.download=filename;
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function returnFieldDoor(door, disposition, noteInput){
  try{
    const result=await api("/api/doorhouse/field-station/returns",{
      expected_field_state_id:fieldState.field_state_id,
      door_id:door.door_id,
      disposition,
      note:noteInput.value
    });
    const noun=result.reseed?"Return saved; exact reseed is ready.":"Return saved.";
    say(noun);
    await refreshFieldStation();
  }catch(error){
    say(error.message,true);
    await refreshFieldStation();
  }
}

function fieldReturnById(receiptId){
  return fieldReturns.find(item=>item.receipt_id===receiptId)||null;
}

async function crossFieldReseed(receipt){
  try{
    await api(
      "/api/doorhouse/field-station/returns/"+receipt.receipt_id+"/ghot/receive",
      {}
    );
    say("reLATTE delivered the exact reseed. GHoT is holding it; admission is still pending.");
    await refreshFieldStation();
  }catch(error){
    say(error.message,true);
    await refreshFieldStation();
  }
}

async function admitFieldReseed(receipt){
  try{
    await api(
      "/api/doorhouse/field-station/returns/"+receipt.receipt_id+"/ghot/admit",
      {}
    );
    say("GHoT admitted the carried intent locally. No body, capability, or execution was assigned.");
    await refreshFieldStation();
  }catch(error){
    say(error.message,true);
    await refreshFieldStation();
  }
}

async function offerFieldIntentAssignment(receipt){
  try{
    await api(
      "/api/doorhouse/field-station/returns/"+receipt.receipt_id+"/ghot/assignment-offer",
      {}
    );
    say("GHoT exposed its current body/capability field. Nothing was selected.");
    await refreshFieldStation();
  }catch(error){
    say(error.message,true);
    await refreshFieldStation();
  }
}

async function assignFieldIntent(receipt, selectedNodeId, capability, offerId){
  try{
    await api(
      "/api/doorhouse/field-station/returns/"+receipt.receipt_id+"/ghot/assign",
      {
        expected_offer_id:offerId,
        selected_node_id:selectedNodeId,
        capability
      }
    );
    say("GHoT assigned the carried intent to the exact chosen pair. No task or execution was created.");
    await refreshFieldStation();
  }catch(error){
    say(error.message,true);
    await refreshFieldStation();
  }
}

function latestOpenLetter() {
  const newest = state.letters[0];
  return newest && newest.opened_at ? newest : null;
}
function renderFieldStation(){
  const root=$("field-station");
  if(!root) return;
  root.replaceChildren();
  if(!fieldState){
    root.append(el("p","Reading the field…","muted"));
    return;
  }

  const head=el("div",undefined,"field-station-head");
  const summary=el("div");
  if(fieldState.present?.kind==="static-live"){
    const event=fieldState.present.event?.title||"local event";
    summary.append(
      el("div","PRESENT · STATIC LIVE · "+event,"field-station-present"),
      el(
        "small",
        String(fieldState.present.state||"unknown")
          +" · recording "+String(Boolean(fieldState.present.recording))
          +" · stream "+String(Boolean(fieldState.present.stream)),
        "muted"
      )
    );
  } else if(fieldState.present?.kind==="lifestream-moment"){
    summary.append(
      el("div","PRESENT · LIFESTREAM MOMENT","field-station-present"),
      el("small",String(fieldState.present.moment_id||""),"muted")
    );
  } else {
    summary.append(
      el("div","PRESENT · QUIET","field-station-present"),
      el("small","No reachable live broadcast occurrence is being claimed.","muted")
    );
  }
  head.append(summary);
  if(fieldState.current_episode){
    const current=el("div",undefined,"field-station-current");
    current.append(
      el("small","PLAYABLE ARTIFACT"),
      el("strong",fieldState.current_episode.title||fieldState.current_episode.episode_id)
    );
    head.append(current);
  }
  root.append(head);

  const pressures=el("div",undefined,"field-pressure-strip");
  for(const pressure of fieldState.memory_pressures||[]){
    pressures.append(el(
      "span",
      pressure.kind+" · "+pressure.value,
      "field-pressure"
    ));
  }
  if(!pressures.childElementCount){
    pressures.append(el("span","no explicit memory pressure","field-pressure"));
  }
  root.append(pressures);

  const doors=el("div",undefined,"field-door-grid");
  for(const door of fieldState.nearby_doors||[]){
    const card=el("article",undefined,"field-door-card");
    card.dataset.lane=door.lane;
    card.append(
      el("small",String(door.lane||"field").toUpperCase()+" · "+door.adapter,"field-door-lane"),
      el("h3",door.label),
      el("p",door.why)
    );
    const details=document.createElement("details");
    details.append(el("summary","Why this door is here"));
    details.append(el("code",JSON.stringify({
      door_id:door.door_id,
      evidence:door.evidence,
      target:door.target,
      effect:door.effect,
      laws:door.laws
    },null,2)));
    card.append(details);

    const note=document.createElement("textarea");
    note.className="field-return-note";
    note.maxLength=1200;
    note.rows=2;
    note.placeholder="Optional human note carried with this exact door…";
    note.setAttribute("aria-label","Optional note for "+door.label);

    const actions=el("div",undefined,"field-return-actions");
    const receiverControl=door.target?.control;
    if(receiverControl==="ghot-field-reseed-admit"){
      const source=fieldReturnById(door.target.field_return_id);
      const admit=el("button","ADMIT TO GHOT");
      admit.type="button";
      admit.dataset.disposition="admit";
      admit.disabled=!source;
      admit.addEventListener("click",()=>source&&admitFieldReseed(source));
      actions.append(admit);
      for(const disposition of ["hold","pass"]){
        const button=el("button",disposition.toUpperCase());
        button.type="button";
        button.dataset.disposition=disposition;
        button.addEventListener("click",()=>returnFieldDoor(door,disposition,note));
        actions.append(button);
      }
    } else if(receiverControl==="ghot-field-intent-offer"){
      const source=fieldReturnById(door.target.field_return_id);
      const openOffer=el("button","OPEN BODY + CAPABILITY FIELD");
      openOffer.type="button";
      openOffer.dataset.disposition="offer";
      openOffer.disabled=!source;
      openOffer.addEventListener("click",()=>source&&offerFieldIntentAssignment(source));
      actions.append(openOffer);
      for(const disposition of ["hold","pass"]){
        const button=el("button",disposition.toUpperCase());
        button.type="button";
        button.dataset.disposition=disposition;
        button.addEventListener("click",()=>returnFieldDoor(door,disposition,note));
        actions.append(button);
      }
    } else if(receiverControl==="ghot-field-intent-assign"){
      const choose=el("button","CHOOSE BODY + CAPABILITY ↓");
      choose.type="button";
      choose.dataset.disposition="assign";
      choose.addEventListener("click",()=>{
        const target=document.getElementById(
          "field-return-"+String(door.target.field_return_id||"").replaceAll(":","-")
        );
        target?.scrollIntoView({behavior:"smooth",block:"center"});
      });
      actions.append(choose);
      for(const disposition of ["hold","pass"]){
        const button=el("button",disposition.toUpperCase());
        button.type="button";
        button.dataset.disposition=disposition;
        button.addEventListener("click",()=>returnFieldDoor(door,disposition,note));
        actions.append(button);
      }
    } else {
      for(const disposition of ["take","hold","pass"]){
        const button=el("button",disposition.toUpperCase());
        button.type="button";
        button.dataset.disposition=disposition;
        button.addEventListener("click",()=>returnFieldDoor(door,disposition,note));
        actions.append(button);
      }
    }
    card.append(note,actions);
    doors.append(card);
  }
  root.append(doors);

  const shelf=el("section",undefined,"field-return-shelf");
  shelf.append(el("div","FIELD RETURNS · HUMAN DISPOSITION","field-return-heading"));
  if(!fieldReturns.length){
    shelf.append(el("p","No Field returns yet. TAKE, HOLD, or PASS binds your choice to the exact field you saw.","muted"));
  }
  for(const receipt of fieldReturns.slice(0,12)){
    const card=el("article",undefined,"field-return-card");
    card.id="field-return-"+String(receipt.receipt_id||"").replaceAll(":","-");
    const lane=receipt.selected_door?.lane||"field";
    card.dataset.disposition=receipt.disposition;
    card.append(
      el("small",receipt.disposition.toUpperCase()+" · "+String(lane).toUpperCase(),"field-door-lane"),
      el("strong",receipt.selected_door?.label||receipt.door_id),
      el("div",receipt.stored_at||"","field-return-time")
    );
    if(receipt.human_note){
      card.append(el("p",receipt.human_note,"field-return-human-note"));
    }

    const exact=document.createElement("details");
    exact.append(el("summary","Inspect exact return receipt"));
    exact.append(el("code",JSON.stringify(receipt,null,2)));
    card.append(exact);

    const actions=el("div",undefined,"field-return-actions");
    const copyReceipt=el("button","Copy receipt");
    copyReceipt.type="button";
    copyReceipt.addEventListener("click",()=>copyJson(receipt).catch(error=>say(error.message,true)));
    actions.append(copyReceipt);

    if(receipt.reseed){
      const copySeed=el("button","Copy reseed");
      copySeed.type="button";
      copySeed.addEventListener("click",()=>copyJson(receipt.reseed).catch(error=>say(error.message,true)));
      const downloadSeed=el("button","Download reseed");
      downloadSeed.type="button";
      downloadSeed.addEventListener("click",()=>downloadJson(
        receipt.reseed,
        String(receipt.reseed.reseed_id||"field-reseed").replaceAll(":","-")+".json"
      ));
      actions.append(copySeed,downloadSeed);

      const seed=document.createElement("details");
      seed.append(el("summary","Inspect proposal-only reseed"));
      seed.append(el("code",JSON.stringify(receipt.reseed,null,2)));
      card.append(seed);

      const receiver=receipt.receiver;
      if(!receiver){
        const cross=el("button","Cross to GHoT → HOLD");
        cross.type="button";
        cross.addEventListener("click",()=>crossFieldReseed(receipt));
        actions.append(cross);
      } else if(receiver.status==="RECEIVED_THEN_HELD"){
        card.append(el(
          "div",
          "reLATTE · RECEIVED → HOLD · GHoT · HOLD · semantic effect: none",
          "field-receiver-status"
        ));
        const admit=el("button","Admit to GHoT inbox");
        admit.type="button";
        admit.dataset.disposition="admit";
        admit.addEventListener("click",()=>admitFieldReseed(receipt));
        actions.append(admit);
      } else if(receiver.status==="ADMITTED_NOT_ASSIGNED"){
        const intent=receiver.admission?.ghot_admission?.intent;
        card.append(el(
          "div",
          "GHoT · ADMITTED · NOT ASSIGNED · local inbox only",
          "field-receiver-status"
        ));
        if(intent){
          const carried=document.createElement("details");
          carried.append(el("summary","Inspect receiver-owned carried intent"));
          carried.append(el("code",JSON.stringify(intent,null,2)));
          card.append(carried);
        }
        const offer=el("button","Open body + capability field");
        offer.type="button";
        offer.dataset.disposition="offer";
        offer.addEventListener("click",()=>offerFieldIntentAssignment(receipt));
        actions.append(offer);
      } else if(receiver.status==="OFFER_READY"){
        const offered=receiver.assignment_offer?.ghot_offer;
        card.append(el(
          "div",
          "GHoT · OFFER READY · NO SELECTION · NO SCORE",
          "field-receiver-status"
        ));
        const options=[];
        for(const body of offered?.bodies||[]){
          for(const item of body.offers||[]){
            if(item.eligible===true){
              options.push({
                node_id:body.node_id,
                location:body.location,
                hostname:body.hostname,
                capability:item.capability
              });
            }
          }
        }
        if(options.length){
          const chooser=document.createElement("select");
          chooser.className="field-assignment-select";
          chooser.setAttribute("aria-label","Choose one GHoT body and capability");
          for(const option of options){
            const elOption=document.createElement("option");
            elOption.value=JSON.stringify({
              node_id:option.node_id,
              capability:option.capability
            });
            elOption.textContent=
              String(option.capability)
              +" · "+String(option.location||"body")
              +" · "+String(option.hostname||option.node_id);
            chooser.append(elOption);
          }
          const assign=el("button","Assign exact pair");
          assign.type="button";
          assign.dataset.disposition="assign";
          assign.addEventListener("click",()=>{
            const chosen=JSON.parse(chooser.value);
            assignFieldIntent(
              receipt,
              chosen.node_id,
              chosen.capability,
              offered.offer_id
            );
          });
          const refresh=el("button","Refresh offer");
          refresh.type="button";
          refresh.dataset.disposition="offer";
          refresh.addEventListener("click",()=>offerFieldIntentAssignment(receipt));
          const chooserWrap=el("div",undefined,"field-assignment-picker");
          chooserWrap.append(chooser,assign,refresh);
          card.append(chooserWrap);
        } else {
          card.append(el(
            "p",
            "No currently eligible body/capability pair is present in this exact offer.",
            "muted"
          ));
        }
        const exactOffer=document.createElement("details");
        exactOffer.append(el("summary","Inspect exact unranked GHoT offer"));
        exactOffer.append(el("code",JSON.stringify(offered,null,2)));
        card.append(exactOffer);
      } else if(receiver.status==="ASSIGNED_NOT_EXECUTED"){
        const assigned=receiver.assignment?.ghot_assignment;
        card.append(el(
          "div",
          "GHoT · ASSIGNED · NOT EXECUTED · assignment only",
          "field-receiver-status"
        ));
        if(assigned){
          card.append(el(
            "p",
            String(assigned.capability)
              +" → "+String(assigned.selected_node_id),
            "field-return-human-note"
          ));
          const exactAssignment=document.createElement("details");
          exactAssignment.append(el("summary","Inspect assignment-only receipt"));
          exactAssignment.append(el("code",JSON.stringify(assigned,null,2)));
          card.append(exactAssignment);
        }
      }

      if(receiver){
        const receiverDetails=document.createElement("details");
        receiverDetails.append(el("summary","Inspect receiver continuity"));
        receiverDetails.append(el("code",JSON.stringify(receiver,null,2)));
        card.append(receiverDetails);
      }
    }
    card.append(actions);
    shelf.append(card);
  }
  root.append(shelf);

  root.append(el(
    "p",
    "The Field proposes. TAKE, crossing, admission, assignment, and execution remain separate acts. An assignment-only receipt creates no task and authorizes no dispatch.",
    "field-station-law"
  ));
}

async function refreshFieldStation(){
  try{
    const [nextField,returnPayload]=await Promise.all([
      api("/api/doorhouse/field-station"),
      api("/api/doorhouse/field-station/returns")
    ]);
    fieldState=nextField;
    fieldReturns=returnPayload.returns||[];
    renderFieldStation();
    if(state?.entered) renderReceipts();
  }catch(error){
    fieldState=null;
    fieldReturns=[];
    const root=$("field-station");
    if(root){
      root.replaceChildren(el("p","Field unavailable · "+error.message,"muted"));
    }
  }
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
function renderAudioWindowForm(receipt,currentWindow){
  const wrap=el("div",undefined,"audio-window-form");
  const heading=el("div",currentWindow?"Cut another bounded audio window":"AUDIO WINDOW 001 · choose a bounded local specimen","audio-window-heading");
  wrap.append(heading);
  if(!roots.length){
    wrap.append(el("p","No configured Workbench roots are available.","muted"));
    return wrap;
  }
  const rootSelect=document.createElement("select");
  rootSelect.setAttribute("aria-label","Workbench root");
  for(const root of roots){
    const option=document.createElement("option");
    option.value=root.id;
    option.textContent=root.id+" · "+root.path;
    rootSelect.append(option);
  }
  const pathInput=document.createElement("input");
  pathInput.type="text";
  pathInput.placeholder="relative/path/to/song.mp3";
  pathInput.setAttribute("aria-label","Root-relative audio path");

  const currentBounds=currentWindow?.snapshot?.window?.requested_bounds||null;
  const startInput=document.createElement("input");
  startInput.type="number";
  startInput.min="0";
  startInput.step="1";
  startInput.value=String(currentBounds?currentBounds.end_ms:0);
  startInput.setAttribute("aria-label","Start milliseconds");

  const endInput=document.createElement("input");
  endInput.type="number";
  endInput.min="1";
  endInput.step="1";
  endInput.value=String((currentBounds?currentBounds.end_ms:0)+30000);
  endInput.setAttribute("aria-label","End milliseconds");

  const labelInput=document.createElement("input");
  labelInput.type="text";
  labelInput.maxLength=120;
  labelInput.value=currentWindow
    ? String(currentWindow.snapshot.window.declared_metadata?.window_label||"window")+"-next"
    : "window-001";
  labelInput.setAttribute("aria-label","Opaque window label");

  const cut=el("button",currentWindow?"Cut next window":"Cut bounded audio window");
  cut.type="button";
  cut.addEventListener("click",()=>{
    const start=Number(startInput.value);
    const end=Number(endInput.value);
    const relativePath=pathInput.value.trim();
    const label=labelInput.value.trim();
    if(!relativePath){say("Choose a root-relative audio file path.",true);return;}
    if(!Number.isInteger(start)||!Number.isInteger(end)||end<=start){
      say("Audio bounds must be integer milliseconds with end > start.",true);return;
    }
    mutate(
      "/api/doorhouse/receipts/"+receipt.id+"/autodisco/audio-window",
      {
        root_id:rootSelect.value,
        relative_path:relativePath,
        start_ms:start,
        end_ms:end,
        window_label:label
      },
      "The House materialized one canonical bounded audio window. No listener has heard it yet."
    );
  });

  const fields=el("div",undefined,"audio-window-fields");
  fields.append(rootSelect,pathInput,startInput,endInput,labelInput,cut);
  wrap.append(fields);
  wrap.append(el("small","root · file · start ms · end ms · opaque label","muted"));
  return wrap;
}

function renderReceipts(){
  const root=$("receipts"); root.replaceChildren();
  if(!state.receipts.length){root.append(el("p","No crossings yet. A selection alone leaves no occurrence receipt.","muted"));return;}
  for(const receipt of state.receipts){
    const relatte=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="relatte");
    const ghotExecution=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="ghot_execution");
    const autodiscoPacket=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="autodisco_packet");
    const autodiscoResponse=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="autodisco_first_response");
    const lookTwicePair=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="look_twice_pair");
    const lookTwiceFirsts=state.external_witnesses.filter(w=>w.receipt_id===receipt.id&&w.kind.startsWith("look_twice_first:"));
    const lookTwiceDialoguePacket=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="look_twice_dialogue_packet");
    const lookTwiceDialogue=state.external_witnesses.find(w=>w.receipt_id===receipt.id&&w.kind==="look_twice_dialogue");
    const audioWindows=state.external_witnesses
      .filter(w=>w.receipt_id===receipt.id&&w.kind.startsWith("audio_window:"))
      .sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
    const audioWindow=audioWindows[0]||null;
    const phonographAnswer=audioWindow
      ? state.external_witnesses.find(
          w=>w.receipt_id===receipt.id
            && w.kind==="phonograph_field_answer:"+audioWindow.snapshot.window_id
        )
      : null;
    const phonographReentry=audioWindow
      ? state.external_witnesses.find(
          w=>w.receipt_id===receipt.id
            && w.kind==="phonograph_reentry:"+audioWindow.snapshot.window_id
        )
      : null;
    const dogramGeneration=audioWindow
      ? state.external_witnesses.find(
          w=>w.receipt_id===receipt.id
            && w.kind==="dogram_generation_delta:"+audioWindow.snapshot.window_id
        )
      : null;
    const dogramListener=audioWindow
      ? state.external_witnesses.find(
          w=>w.receipt_id===receipt.id
            && w.kind==="dogram_listener_delta:"+audioWindow.snapshot.window_id
        )
      : null;
    const dogramDoor=audioWindow
      ? (fieldState?.nearby_doors||[]).find(
          d=>d.kind==="measure-generation-delta"
            && d.target?.receipt_id===receipt.id
            && d.target?.child_window_id===audioWindow.snapshot.window_id
        )
      : null;
    const listenerDogramDoor=audioWindow
      ? (fieldState?.nearby_doors||[]).find(
          d=>d.kind==="measure-listener-delta"
            && d.target?.receipt_id===receipt.id
            && d.target?.child_window_id===audioWindow.snapshot.window_id
        )
      : null;
    const phonographDoor=audioWindow
      ? (fieldState?.nearby_doors||[]).find(
          d=>d.kind==="ask-phonograph-answer"
            && d.target?.receipt_id===receipt.id
            && d.target?.window_id===audioWindow.snapshot.window_id
        )
      : null;
    const audioPairs=state.external_witnesses
      .filter(w=>w.receipt_id===receipt.id&&w.kind.startsWith("audio_look_twice_pair:"))
      .filter(w=>!audioWindow||w.snapshot.window_id===audioWindow.snapshot.window_id)
      .sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
    const audioPair=audioPairs[0]||null;
    const audioPairId=audioPair?.snapshot?.pair_id||null;
    const audioFirsts=state.external_witnesses.filter(
      w=>w.receipt_id===receipt.id
        && w.kind.startsWith("audio_look_twice_first:")
        && w.snapshot.pair_id===audioPairId
    );
    const audioDialoguePacket=state.external_witnesses.find(
      w=>w.receipt_id===receipt.id
        && w.kind.startsWith("audio_look_twice_dialogue_packet:")
        && w.snapshot.pair_id===audioPairId
    );
    const audioDialogue=state.external_witnesses.find(
      w=>w.receipt_id===receipt.id
        && w.kind.startsWith("audio_look_twice_dialogue:")
        && w.snapshot.pair_id===audioPairId
    );
    const broadcastEpisodes=state.external_witnesses
      .filter(w=>w.receipt_id===receipt.id&&w.kind.startsWith("broadcast_episode:"))
      .filter(w=>!audioPairId||w.snapshot.pair_id===audioPairId)
      .sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
    const broadcastEpisode=broadcastEpisodes[0]||null;
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

      if(!lookTwicePair){
        const prepareTwice=el("button","LOOK TWICE · prepare two isolated booths");
        prepareTwice.type="button";
        prepareTwice.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/autodisco/look-twice/prepare",
          {},
          "Static Sam and Juniper received separate sealed packets. Neither has seen the other's response."
        ));
        card.append(prepareTwice);
      } else {
        card.append(el(
          "div",
          "LOOK TWICE · pair sealed · "+lookTwiceFirsts.length+"/2 first responses",
          "adapter-line"
        ));
        if(lookTwiceFirsts.length<2){
          const encounter=el("button","Invite both fresh listeners independently");
          encounter.type="button";
          encounter.addEventListener("click",()=>mutate(
            "/api/doorhouse/receipts/"+receipt.id+"/autodisco/look-twice/encounters",
            {},
            "LOOK TWICE returned only first responses that actually occurred. Cross-read remains locked until both are sealed."
          ));
          card.append(encounter);
        } else if(!lookTwiceDialogue){
          const crossRead=el("button","Unlock cross-read · let them look twice");
          crossRead.type="button";
          crossRead.addEventListener("click",()=>mutate(
            "/api/doorhouse/receipts/"+receipt.id+"/autodisco/look-twice/dialogue",
            {},
            "The two immutable first responses were allowed to see each other only after sealing."
          ));
          card.append(crossRead);
          if(lookTwiceDialoguePacket){
            card.append(el(
              "div",
              "LOOK TWICE · dialogue packet sealed · no simulated exchange",
              "adapter-line"
            ));
          }
        } else {
          const dw=lookTwiceDialogue.snapshot;
          const dialogue=dw.dialogue||{};
          card.append(el(
            "div",
            "LOOK TWICE · dialogue sealed · lingering intrigue: "+String(Boolean(dialogue.lingering_intrigue)),
            "adapter-line"
          ));
          if(dialogue.door_seed){
            card.append(el("div","door seed · "+dialogue.door_seed,"adapter-line"));
          }
        }
      }
    }

    card.append(renderAudioWindowForm(receipt,audioWindow));
    if(audioWindow){
      const aw=audioWindow.snapshot;
      const bounds=aw.window.requested_bounds;
      const duration=Math.round(aw.window.canonical_audio.duration_ms);
      card.append(el(
        "div",
        "AUDIO WINDOW · "+bounds.start_ms+"–"+bounds.end_ms+" ms · "+duration+" ms canonical · "+aw.audio_sha256.slice(0,16)+"…",
        "adapter-line"
      ));

      if(phonographReentry){
        const rw=phonographReentry.snapshot;
        card.append(el(
          "div",
          "PHONOGRAPH RE-ENTRY · descendant of "+rw.parent_window_id.slice(0,30)+"… · fresh radio witness required",
          "adapter-line"
        ));
      }

      if(dogramGeneration){
        const dg=dogramGeneration.snapshot;
        card.append(el(
          "div",
          "DOGRAM SIGNAL · "+dg.classification+" · changed axes: "
            +(dg.changed_axes||[]).join(", "),
          "adapter-line"
        ));
        const dActions=el("div",undefined,"door-actions");
        const receiptLink=document.createElement("a");
        receiptLink.href="/api/doorhouse/receipts/"+receipt.id+"/dogram/"
          +encodeURIComponent(audioWindow.snapshot.window_id)+"/generation-delta.json";
        receiptLink.target="_blank";
        receiptLink.rel="noopener";
        receiptLink.textContent="Generation delta receipt";
        receiptLink.className="radio-link";
        dActions.append(receiptLink);
        card.append(dActions);
      } else if(dogramDoor){
        const measure=el("button","MEASURE PARENT → DESCENDANT");
        measure.type="button";
        measure.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/dogram/"
            +encodeURIComponent(audioWindow.snapshot.window_id)+"/generation-delta",
          {},
          "Dogram measured the admitted parent-to-descendant signal transform and kept listener effects residual."
        ));
        card.append(measure);
        card.append(el(
          "div",
          "GENERATION-DELTA-001 · both generations witnessed · measurement != verdict",
          "adapter-line"
        ));
      }

      if(dogramListener){
        const dl=dogramListener.snapshot;
        card.append(el(
          "div",
          "DOGRAM LISTENERS · "+dl.classification+" · "
            +String(dl.changed_listener_count)+"/"+String(dl.listener_count)
            +" listeners changed on declared response axes",
          "adapter-line"
        ));
        if((dl.shared_changed_axes||[]).length){
          card.append(el(
            "div",
            "shared changed axes · "+dl.shared_changed_axes.join(", "),
            "adapter-line"
          ));
        }
        const lActions=el("div",undefined,"door-actions");
        const listenerReceipt=document.createElement("a");
        listenerReceipt.href="/api/doorhouse/receipts/"+receipt.id+"/dogram/"
          +encodeURIComponent(audioWindow.snapshot.window_id)+"/listener-delta.json";
        listenerReceipt.target="_blank";
        listenerReceipt.rel="noopener";
        listenerReceipt.textContent="Listener delta receipt";
        listenerReceipt.className="radio-link";
        lActions.append(listenerReceipt);
        card.append(lActions);
        card.append(el(
          "div",
          "response delta != person delta · response delta != causal effect · lexical overlap != semantic agreement",
          "adapter-line"
        ));
      } else if(listenerDogramDoor){
        const measureListeners=el("button","MEASURE LISTENER RESPONSE DELTA");
        measureListeners.type="button";
        measureListeners.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/dogram/"
            +encodeURIComponent(audioWindow.snapshot.window_id)+"/listener-delta",
          {},
          "Dogram measured the sealed first-response transform without scoring listeners or claiming the audio change caused it."
        ));
        card.append(measureListeners);
        card.append(el(
          "div",
          "LISTENER-DELTA-001 · exact sealed responses · response delta != person delta",
          "adapter-line"
        ));
      }

      if(dogramGeneration || dogramListener){
        card.append(el(
          "div",
          "Dogram measures declared transforms · delta != value · residual != failure",
          "adapter-line"
        ));
      }

      if(phonographAnswer){
        const pw=phonographAnswer.snapshot;
        card.append(el(
          "div",
          "HAUNTED PHONOGRAPH · proposal ready · "+pw.proposal_receipt_hash.slice(0,23)+"…",
          "adapter-line"
        ));
        const player=document.createElement("audio");
        player.controls=true;
        player.preload="metadata";
        player.src="/api/doorhouse/receipts/"+receipt.id+"/phonograph/"
          +encodeURIComponent(audioWindow.snapshot.window_id)+"/audition.wav";
        player.className="phono-audition";
        card.append(player);

        const phonoActions=el("div",undefined,"door-actions");
        const midi=document.createElement("a");
        midi.href="/api/doorhouse/receipts/"+receipt.id+"/phonograph/"
          +encodeURIComponent(audioWindow.snapshot.window_id)+"/answer.mid";
        midi.target="_blank";
        midi.rel="noopener";
        midi.textContent="answer.mid";
        midi.className="radio-link";
        const phonoReceipt=document.createElement("a");
        phonoReceipt.href="/api/doorhouse/receipts/"+receipt.id+"/phonograph/"
          +encodeURIComponent(audioWindow.snapshot.window_id)+"/receipt.json";
        phonoReceipt.target="_blank";
        phonoReceipt.rel="noopener";
        phonoReceipt.textContent="Phonograph receipt";
        phonoReceipt.className="radio-link";
        const admit=el("button","ADMIT AS NEW RADIO SPECIMEN");
        admit.type="button";
        admit.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/phonograph/"
            +encodeURIComponent(audioWindow.snapshot.window_id)+"/admit-radio",
          {},
          "You admitted the Phonograph proposal as a descendant radio specimen. Fresh first-listen evidence is required before Phonograph may answer the descendant."
        ));
        phonoActions.append(midi,phonoReceipt,admit);
        card.append(phonoActions);
        card.append(el(
          "div",
          "signal facts → musical proposal · audition != admission · descendant != parent",
          "adapter-line"
        ));
      } else if(phonographDoor){
        const askPhono=el("button","Ask Haunted Phonograph to answer this window");
        askPhono.type="button";
        askPhono.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/phonograph/field-answer",
          {},
          "Haunted Phonograph returned one receipted musical proposal from bounded PCM facts."
        ));
        card.append(askPhono);
        card.append(el(
          "div",
          "FIELD ANSWER 001 · signal fact != musical meaning · musical possibility != recommendation",
          "adapter-line"
        ));
      }

      if(!audioPair){
        const prepareAudio=el("button","FIRST-LISTEN RADIO · prepare two audio booths");
        prepareAudio.type="button";
        prepareAudio.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/autodisco/audio-look-twice/prepare",
          {},
          "Static Sam and Juniper now reference the same exact audio digest from separate first-listen booths."
        ));
        card.append(prepareAudio);
      } else if(audioFirsts.length<2){
        const listenTwice=el("button","Play window independently to both listeners");
        listenTwice.type="button";
        listenTwice.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/autodisco/audio-look-twice/encounters",
          {},
          "The station kept only first listens that actually occurred. Cross-read remains locked until both are sealed."
        ));
        card.append(listenTwice);
        card.append(el(
          "div",
          "FIRST-LISTEN RADIO · "+audioFirsts.length+"/2 sealed first listens",
          "adapter-line"
        ));
      } else if(!audioDialogue){
        const crossAudio=el(
          "button",
          audioDialoguePacket
            ? "Try real audio cross-read again"
            : "Unlock audio cross-read · window stays closed"
        );
        crossAudio.type="button";
        crossAudio.addEventListener("click",()=>mutate(
          "/api/doorhouse/receipts/"+receipt.id+"/autodisco/audio-look-twice/dialogue",
          {},
          "The audio window stayed closed. Only the two sealed first listens entered the cross-read."
        ));
        card.append(crossAudio);
        card.append(el(
          "div",
          audioDialoguePacket
            ? "FIRST-LISTEN RADIO · dialogue packet sealed · no simulated exchange"
            : "FIRST-LISTEN RADIO · 2/2 first listens sealed · cross-read unlocked",
          "adapter-line"
        ));
      } else {
        const dialogue=audioDialogue.snapshot.dialogue||{};
        card.append(el(
          "div",
          "FIRST-LISTEN RADIO · cross-read sealed · lingering intrigue: "+String(Boolean(dialogue.lingering_intrigue)),
          "adapter-line"
        ));
        if(dialogue.door_seed){
          card.append(el("div","radio door seed · "+dialogue.door_seed,"adapter-line"));
        }

        if(!broadcastEpisode){
          const assemble=el("button","ASSEMBLE FIRST RADIO EPISODE");
          assemble.type="button";
          assemble.addEventListener("click",()=>mutate(
            "/api/doorhouse/receipts/"+receipt.id+"/radio/assemble",
            {},
            "The station assembled one portable episode from the exact sealed radio evidence."
          ));
          card.append(assemble);
        } else {
          const ep=broadcastEpisode.snapshot;
          card.append(el(
            "div",
            "BROADCAST ASSEMBLY · "+ep.title+" · "+ep.episode_digest.slice(0,16)+"…",
            "adapter-line"
          ));
          const actions=el("div",undefined,"door-actions");
          const play=document.createElement("a");
          play.href="/api/doorhouse/receipts/"+receipt.id+"/radio/"+encodeURIComponent(ep.episode_id)+"/";
          play.target="_blank";
          play.rel="noopener";
          play.textContent="PLAY EPISODE";
          play.className="radio-link";
          const manifest=document.createElement("a");
          manifest.href="/api/doorhouse/receipts/"+receipt.id+"/radio/"+encodeURIComponent(ep.episode_id)+"/episode.json";
          manifest.target="_blank";
          manifest.rel="noopener";
          manifest.textContent="episode.json";
          manifest.className="radio-link";
          const wav=document.createElement("a");
          wav.href="/api/doorhouse/receipts/"+receipt.id+"/radio/"+encodeURIComponent(ep.episode_id)+"/window.wav";
          wav.target="_blank";
          wav.rel="noopener";
          wav.textContent="window.wav";
          wav.className="radio-link";
          actions.append(play,manifest,wav);
          card.append(actions);
          card.append(el(
            "div",
            "browser voice is a playback projection · episode != broadcast occurrence",
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
    if(lookTwicePair) evidence.look_twice_pair=lookTwicePair.snapshot;
    if(lookTwiceFirsts.length) evidence.look_twice_first_responses=lookTwiceFirsts.map(w=>w.snapshot);
    if(lookTwiceDialoguePacket) evidence.look_twice_dialogue_packet=lookTwiceDialoguePacket.snapshot;
    if(lookTwiceDialogue) evidence.look_twice_dialogue=lookTwiceDialogue.snapshot;
    if(audioWindow) evidence.audio_window=audioWindow.snapshot;
    if(audioPair) evidence.audio_look_twice_pair=audioPair.snapshot;
    if(audioFirsts.length) evidence.audio_first_listens=audioFirsts.map(w=>w.snapshot);
    if(audioDialoguePacket) evidence.audio_dialogue_packet=audioDialoguePacket.snapshot;
    if(audioDialogue) evidence.audio_dialogue=audioDialogue.snapshot;
    if(phonographAnswer) evidence.phonograph_field_answer=phonographAnswer.snapshot;
    if(phonographReentry) evidence.phonograph_reentry=phonographReentry.snapshot;
    if(dogramGeneration) evidence.dogram_generation_delta=dogramGeneration.snapshot;
    if(dogramListener) evidence.dogram_listener_delta=dogramListener.snapshot;
    if(broadcastEpisode) evidence.broadcast_episode=broadcastEpisode.snapshot;
    details.append(el("code",JSON.stringify(evidence,null,2)));
    card.append(details); root.append(card);
  }
}
function render(){
  $("entry-panel").classList.toggle("doorhouse-hidden",state.entered);
  $("play-panel").classList.toggle("doorhouse-hidden",!state.entered);
  $("world-version").textContent=state.entered?String(state.world_version):"—";
  const laws=$("laws"); laws.replaceChildren(); for(const law of state.laws) laws.append(el("span",law,"law-chip"));
  if(state.entered){renderFieldStation();renderLetters();renderDoors();renderReceipts();}
}
async function mutate(path,payload,message){
  try{
    state=await api(path,payload);
    render();
    await refreshFieldStation();
    say(message);
  }catch(error){
    say(error.message,true);
    state=await api("/api/doorhouse/state");
    render();
    await refreshFieldStation();
  }
}
async function start(){
  try{
    const boot=await api("/api/bootstrap"); token=boot.session_token; roots=boot.roots||[];
    state=await api("/api/doorhouse/state");
    render();
    if(state.entered) await refreshFieldStation();
    $("enter-house").addEventListener("click",()=>mutate("/api/doorhouse/enter",{},"You entered. A sealed letter is waiting."));
    say(state.entered?"The House remembers. Nothing here chooses for you.":"The House has not been entered on this machine.");
  }catch(error){say(error.message,true);}
}
start();
