"use strict";
// WEBZ-003: no material is transported on GET, world view, or no-carry portal.
// This is a separate, human-authorized material-byte arrival instrument.
const mode=document.body?.dataset?.webzWorld;
const KINDS=new Set(["fruit","spore"]);
const $=(id)=>document.getElementById(id);

async function json(path,options={}) {
  const response=await fetch(path,{
    credentials:"same-origin",
    headers:{Accept:"application/json",...(options.headers||{})},
    ...options,
  });
  let value=null;
  try {value=await response.json();} catch(_){}
  if(!response.ok)throw new Error(
    typeof value?.detail==="string"?value.detail:
    "The local receiver evidence is unavailable."
  );
  return value;
}
function paragraph(message,klass="") {
  const node=document.createElement("p");
  node.className=klass;
  node.textContent=String(message);
  return node;
}
function label(message) {
  const node=document.createElement("strong");
  node.textContent=String(message);
  return node;
}

function sanctuary() {
  const kind=$("webz-custody-kind");
  const inspect=$("webz-custody-inspect");
  const consent=$("webz-custody-confirm");
  const deliver=$("webz-custody-deliver");
  const detail=$("webz-custody-preview");
  const status=$("webz-custody-status");
  let choice=null;
  let generation=0;
  function reset() {
    generation+=1;
    choice=null;
    consent.checked=false;
    consent.disabled=true;
    deliver.disabled=true;
    detail.hidden=true;
    detail.textContent="";
    status.textContent="No actual bytes have been delivered by this instrument.";
  }
  kind.addEventListener("change",reset);
  consent.addEventListener("change",()=>{
    deliver.disabled=!choice||!consent.checked;
  });
  inspect.addEventListener("click",async()=>{
    reset();
    const mine=generation;
    const chosen=kind.value;
    if(!KINDS.has(chosen))return;
    inspect.disabled=true;
    status.textContent="Inspecting existing signed envelope without transporting bytes…";
    try {
      const preview=await json("/api/webz/custody/"+chosen+"/preview");
      if(mine!==generation)return;
      if(preview.schema!=="workbench.webz-custody-preview/v0" ||
         preview.kind!==chosen ||
         preview.destination_world_id!=="webz:the-static-collective/orchard-022100" ||
         !/^[a-f0-9]{64}$/.test(preview.artifact_sha256||"")) {
        throw new Error("Unrecognized material-custody proposal.");
      }
      if(!preview.ready) {
        status.textContent="NOT READY · First complete the separate signed WEBZ-002 offer above. No bytes were transferred.";
        return;
      }
      if(!/^relatte-crossing-v0:[a-f0-9]{64}$/.test(preview.crossing_id||"") ||
         preview.receiver_policy!==(chosen==="fruit"?"HOLD":"REFUSE")) {
        throw new Error("Signed envelope or fixed receiver policy mismatched.");
      }
      detail.hidden=false;
      detail.textContent=
        "SIGNED CROSSING · "+preview.crossing_id+"\n"+
        "ACTUAL BYTES · SHA-256 "+preview.artifact_sha256+"\n"+
        "RECEIVER · "+preview.destination_world_id+"\n"+
        "RECEIVER POLICY · "+preview.receiver_policy+"\n"+
        "OWNER PIN · "+preview.pinned_owner+"\n"+
        "MATERIAL DOES NOT BECOME AN ADMITTED WORLD OBJECT.";
      if(preview.status==="ALREADY_VERIFIED") {
        status.textContent="ALREADY VERIFIED · The Orchard has an existing signed custody receipt ("+
          preview.custody_receipt_id+"). No duplicate delivery needed.";
        return;
      }
      if(preview.status!=="READY") throw new Error("Receiver is not ready for this proposal.");
      choice=preview;
      consent.disabled=false;
      status.textContent="PREVIEW ONLY · No physical material has moved. Review the digest, explicitly consent, then choose Deliver.";
    }catch(error){
      if(mine===generation)status.textContent="CUSTODY UNRESOLVED · "+error.message;
    }finally{inspect.disabled=false;}
  });
  deliver.addEventListener("click",async()=>{
    if(!choice||!consent.checked||deliver.disabled||choice.kind!==kind.value)return;
    const selected=choice;
    choice=null;
    consent.disabled=true;
    deliver.disabled=true;
    inspect.disabled=true;
    status.textContent="Transmitting exactly selected bytes to the independent destination receiver…";
    try {
      const session=await json("/api/bootstrap");
      if(!session||typeof session.session_token!=="string")throw new Error("Workbench session unavailable.");
      const result=await json("/api/webz/custody/"+selected.kind+"/deliver",{
        method:"POST",
        headers:{"Content-Type":"application/json","x-workbench-session":session.session_token},
        body:JSON.stringify({
          expected_sha256:selected.artifact_sha256,
          expected_crossing_id:selected.crossing_id,
          confirmation:"DELIVER_VERIFIED_BYTES",
        }),
      });
      if(result.schema!=="workbench.webz-material-custody/v0" ||
         result.kind!==selected.kind ||
         result.artifact_sha256!==selected.artifact_sha256 ||
         result.crossing_id!==selected.crossing_id ||
         result.admitted!==false ||
         result.receiver_disposition!==selected.receiver_policy ||
         result.retained!==(selected.receiver_policy==="HOLD")) {
        throw new Error("The returned custody witness contradicted the selected material.");
      }
      status.textContent=
        "DESTINATION VERIFIED ACTUAL BYTES · "+result.status+"\n"+
        "CUSTODY SIGNED RECEIPT · "+result.custody_receipt_id+"\n"+
        "PARENT CROSSING · "+result.crossing_id+"\n"+
        "BYTES · "+result.received_byte_length+" / SHA-256 "+result.artifact_sha256+"\n"+
        "ADMITTED: NO. Orchard can independently display its signed custody evidence.";
    }catch(error){
      status.textContent="NO CONFIRMED BYTE CUSTODY · "+error.message+
        "\nUnknown delivery is not automatically retried. Inspect the Orchard's receiver state.";
    }finally{
      consent.checked=false;consent.disabled=true;deliver.disabled=true;inspect.disabled=false;
    }
  });
}

function orchard() {
  const container=$("webz-custody-inbox");
  const refresh=$("webz-custody-refresh");
  const proof=$("webz-custody-proof");
  async function show() {
    container.replaceChildren();
    proof.hidden=true;proof.textContent="";
    refresh.disabled=true;
    try {
      const data=await json("/api/webz/custody/inbox");
      if(!Array.isArray(data.parcels))throw new Error("Invalid receiver material view.");
      if(data.parcels.length===0) {
        container.appendChild(paragraph("NO BYTE-CUSTODY RECEIPTS · Opening this world cannot transfer material."));
      }
      for(const receipt of data.parcels) {
        if(!KINDS.has(receipt.kind))continue;
        const item=document.createElement("article");
        item.className="webz-custody-receipt";
        item.append(
          label(receipt.kind.toUpperCase()+" · "+receipt.status),
          paragraph("RETAINED IN QUARANTINE · "+(receipt.retained?"YES":"NO")+" / ADMITTED · NO"),
          paragraph("SHA-256 · "+receipt.artifact_sha256,"webz-mono"),
          paragraph("ORIGIN CROSSING · "+receipt.crossing_id,"webz-mono"),
          paragraph("RECEIVER SIGNED · "+receipt.custody_receipt_id,"webz-mono"),
        );
        const button=document.createElement("button");
        button.type="button";
        button.className="webz-button webz-quiet webz-small";
        button.textContent="Inspect actual-byte signature ↗";
        button.addEventListener("click",async()=>{
          proof.hidden=false;
          proof.textContent="Reading receiver-local public evidence…";
          try{
            const data=await json("/api/webz/custody/"+receipt.kind+"/proof");
            if(data.schema!=="workbench.webz-byte-custody-proof/v0")throw new Error("Unknown custody proof.");
            proof.textContent=JSON.stringify(data,null,2);
          }catch(error){
            proof.textContent="CUSTODY PROOF UNAVAILABLE · "+error.message;
          }
        });
        item.appendChild(button);
        container.appendChild(item);
      }
    }catch(error){
      container.replaceChildren(paragraph(
        "CUSTODY UNAVAILABLE · "+error.message+
        ". No receiver possession has been inferred.","webz-custody-error",
      ));
    }finally{refresh.disabled=false;}
  }
  refresh.addEventListener("click",show);
  // Pure local GET: world arrival never creates/sends material.
  show();
}
if(mode==="sanctuary"&&$("webz-custody-deliver"))sanctuary();
if(mode==="orchard"&&$("webz-custody-inbox"))orchard();
