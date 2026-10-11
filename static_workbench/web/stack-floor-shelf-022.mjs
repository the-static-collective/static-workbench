/** STACK² 022 — only a read-only view of original signed receiver HOLD history. */
const $=id=>document.getElementById(id);
const node=(tag,cls='',text='')=>{
  const v=document.createElement(tag);
  if(cls)v.className=cls;
  if(text)v.textContent=String(text);
  return v;
};
let enabled=false,token=null,current=null,selected=null,busy=false,seq=0;
const line=(dt,dd,mono=false)=>{
  const wrap=node('div'),term=node('dt','',dt),data=node('dd',mono?'mono':'');
  data.textContent=String(dd??'NOT DECLARED');
  wrap.append(term,data);
  return wrap;
};
const message=s=>{$('shelf-022-summary').textContent=s;};
function controls(){
  $('shelf-022-refresh').disabled=!enabled||busy;
  $('shelf-022-export').disabled=!selected;
}
async function load(path,body){
  if(!token){
    const boot=await fetch('/api/bootstrap',{credentials:'same-origin'});
    if(!boot.ok)throw Error('LOCAL_SESSION_UNAVAILABLE');
    token=(await boot.json()).session_token;
  }
  const r=await fetch(path,{
    method:'POST',credentials:'same-origin',
    headers:{'X-Workbench-Session':token,'Content-Type':'application/json','Accept':'application/json'},
    body:JSON.stringify(body)
  });
  const result=await r.json();
  if(!r.ok)throw Error(typeof result.detail==='string'?result.detail:'SHELF_INSPECTION_REFUSED');
  if(result.schema!=='workbench.stack-squared-022-shelf/v0'||
    result.receiver_admission_authorized!==false||
    result.mutations_performed!==false||
    result.original_receiver_journal_replayed!==true||
    result.original_relatte_signatures_verified!==true||
    !Array.isArray(result.records))throw Error('UNVERIFIED_RECEIVER_RESPONSE');
  return result;
}
function clearSelection(){
  selected=null;
  $('shelf-022-selected-title').textContent='Nothing selected';
  $('shelf-022-selected-help').textContent='Choose a held source to inspect its signed history.';
  $('shelf-022-details').replaceChildren();
  controls();
}
function render(){
  const shelf=$('shelf-022-slots');
  shelf.replaceChildren();
  if(!current){shelf.append(node('p','help','This shelf has not been read.'));return;}
  const n=current.records.length;
  if(n===0){
    shelf.append(node('p','help','No items currently in HOLD. This does not mean this world has no history.'));
    return;
  }
  current.records.forEach((record,index)=>{
    const button=node('button','shelf-slot');
    button.type='button';
    button.setAttribute('aria-pressed',String(selected?.records?.[0]?.crossing_id===record.crossing_id));
    const marker=node('span','shelf-slot-number',String(index+1).padStart(2,'0'));
    const body=node('span','shelf-slot-body');
    body.append(
      node('span','shelf-slot-tag','HOLD · ORIGINAL SIGNATURES VALID'),
      node('span','shelf-slot-title',record.source_world+' · '+record.declared_kind),
      node('span','shelf-slot-sub','RECEIVED '+record.received_at),
      node('span','shelf-slot-sub',record.crossing_id)
    );
    button.append(marker,body);
    button.addEventListener('click',()=>inspectOne(record.crossing_id));
    shelf.append(button);
  });
}
function selectedDetail(response){
  const record=response.records[0];
  if(!record||record.status!=='HOLD'||record.owner_admitted!==false||
     record.signature_status!=='NATIVE_RELATTE_VALIDATED'){
    throw Error('ITEM_NO_LONGER_HELD_OR_SIGNATURE_INVALID');
  }
  selected=response;
  $('shelf-022-selected-title').textContent=record.declared_kind+' / HOLD';
  $('shelf-022-selected-help').textContent=
    'Receiver-local signed crossing history. Source claims are not promoted into authority.';
  const dl=$('shelf-022-details');
  dl.replaceChildren();
  const labels=[
    ['CROSSING ID',record.crossing_id,true],
    ['SOURCE WORLD',record.source_world],
    ['SOURCE PARTICULAR',record.source_particular],
    ['SOURCE HISTORY HEAD',record.source_history_head,true],
    ['SOURCE FAMILY',record.source_family],
    ['SOURCE CONTRACT',record.source_contract],
    ['SOURCE DECLARED PAYLOAD COUNT',record.source_payload_count],
    ['RECEIVED AT',record.received_at],
    ['SIGNED RECEIVE RECEIPT',record.receive_receipt_id,true],
    ['HOLD AT',record.held_at],
    ['SIGNED HOLD RECEIPT',record.hold_receipt_id,true],
    ['RECEIVER WORLD',record.receiver_world],
    ['RECEIVER CONTRACT',record.receiver_contract_ref],
    ['RECEIVER HISTORY HEAD',response.history_head,true],
    ['RECEIVER STATE REF',response.state_ref,true],
    ['SIGNATURE STATUS',record.signature_status],
    ['DONOR VERIFICATION',record.donor_proof],
    ['ADMITTED?',String(record.owner_admitted)],
    ['PAYLOAD BYTES OPENED?',String(response.payload_bytes_read)]
  ];
  for(const [label,value,mono] of labels)dl.append(line(label,value,mono));
  const refs=Array.isArray(record.payload_refs)?record.payload_refs:[];
  if(refs.length){
    const box=node('div');box.append(node('dt','','DECLARED SOURCE POINTERS (NOT CONTENT)'));
    for(const x of refs){
      const ref=node('dd','mono payload-ref');
      ref.textContent=x.role+' · '+x.address+' · '+x.media_type;
      box.append(ref);
    }
    dl.append(box);
  }
  controls();
  render();
}
async function inspectOne(crossingId){
  if(!enabled||busy||!/^relatte-crossing-v0:[a-f0-9]{64}$/.test(crossingId))return;
  const my=++seq;busy=true;controls();
  message('Replaying receiver-owned signed history for this particular…');
  try{
    const result=await load('/api/stack-floor/shelf/detail',{crossing_id:crossingId});
    if(my!==seq)return;
    selectedDetail(result);
    message('Original crossing, RECEIVE and HOLD signatures checked. No source execution, bytes opened or admission.');
  }catch(e){
    if(my!==seq)return;
    clearSelection();
    message('HOLD / REFUSED: '+e.message);
  }finally{if(my===seq){busy=false;controls();}}
}
async function refresh(){
  if(!enabled||busy)return;
  const my=++seq;busy=true;controls();
  message('Cold-replaying the original receiver journal, without changing disposition…');
  try{
    const result=await load('/api/stack-floor/shelf/list',{});
    if(my!==seq)return;
    current=result;selected=null;render();
    clearSelection();
    $('shelf-022-status').textContent='ORIGINAL RECEIVER JOURNAL VALID';
    $('shelf-022-count').textContent=String(result.counts.held)+' HELD';
    $('shelf-022-state').textContent=result.state_ref.slice(0,27)+'…';
    message(result.counts.held+' held · '+result.journal_events+
      ' signed events · '+result.counts.admitted+' admitted elsewhere in the receiver. Only HOLD items are shown.');
  }catch(e){
    if(my!==seq)return;
    current=null;clearSelection();render();
    $('shelf-022-status').textContent='HOLD / INSPECTION REFUSED';
    $('shelf-022-count').textContent='—';
    $('shelf-022-state').textContent='NOT VERIFIED';
    message('HOLD / REFUSED: '+e.message);
  }finally{if(my===seq){busy=false;controls();}}
}
$('shelf-022-refresh').addEventListener('click',refresh);
$('shelf-022-export').addEventListener('click',()=>{
  if(!selected)return;
  const record=selected.records[0];
  const packet={
    schema:'workbench.stack2-022-unsigned-inspection-card/v0',
    source:'LOCAL_RECEIVER_READ_ONLY',
    crossing_id:record.crossing_id,
    inspection:selected, // Only the server-filtered public metadata; no private key or raw payload.
    signed_receipts_included:false,
    original_relatte_receipt_identifiers_verified:true,
    original_ghot_signature_reverified:false,
    receiver_admission_authorized:false
  };
  const blob=new Blob([JSON.stringify(packet,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='stack-squared-022-hold-inspection-unsigned.json';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),800);
});
window.addEventListener('stack-floor:crossing-held',()=>{
  if(enabled)refresh();
});
async function init(){
  try{
    const r=await fetch('/api/stack-floor/shelf/status',{credentials:'same-origin'});
    if(!r.ok)throw Error('UNAVAILABLE');
    const data=await r.json();enabled=data.enabled===true&&data.read_only===true;
    $('shelf-022-status').textContent=enabled?
      'RECEIVER PRESENT · INSPECTION OPTIONAL':'OFF · NO LOCAL RECEIVER CONFIGURED';
    message(enabled?'Inspect when ready. Nothing has been admitted by visiting this shelf.':
      'Requires a previously configured original reLATTE receiver.');
  }catch{
    enabled=false;$('shelf-022-status').textContent='SHELF UNAVAILABLE';
    message('Receiver inspection is unavailable.');
  }
  controls();
}
init();
