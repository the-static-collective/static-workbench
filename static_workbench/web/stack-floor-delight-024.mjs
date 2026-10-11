/** STACK² 024 — original Haunted Toaster deck → metadata-only local postcard.
 * Browser makes a static unsigned SVG without reading donor bytes.
 */
const $=id=>document.getElementById(id);
const ns='http://www.w3.org/2000/svg';
const sx=(name,attrs={},body=null)=>{
  const e=document.createElementNS(ns,name);
  for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));
  if(body!==null)e.textContent=String(body);
  return e;
};
const node=(tag,cls='',text='')=>{
  const e=document.createElement(tag);if(cls)e.className=cls;
  if(text)e.textContent=String(text);return e;
};
const hex=/^proposal-023:[a-f0-9]{64}$/;
let enabled=false,session=null,proposal=null,receiverState=null,
    preview=null,chosen=null,dealIndex=0,working=false;
function msg(s){$('delight-024-message').textContent=s;}
function clear(){
  preview=null;chosen=null;
  window.dispatchEvent(new CustomEvent('stack-floor:toaster-delight-choice',{detail:null}));
  $('delight-024-deck').replaceChildren(node('p','help','No current, verified source-specific deal.'));
  $('delight-024-paper').replaceChildren(node('span','micro','NO KEEPSAKE SELECTED'));
  $('delight-024-preview-title').textContent='A preview needs a question.';
  $('delight-024-export').disabled=true;
  controls();
}
function controls(){
  $('delight-024-deal').disabled=!enabled||!proposal||working;
  $('delight-024-again').disabled=!enabled||!proposal||working||!preview||dealIndex>=8;
}
async function request(){
  if(!session){
    const r=await fetch('/api/bootstrap',{credentials:'same-origin'});
    if(!r.ok)throw Error('NO_LOCAL_WORKBENCH_SESSION');
    session=(await r.json()).session_token;
  }
  const response=await fetch('/api/stack-floor/delight/preview',{
    method:'POST',credentials:'same-origin',
    headers:{'X-Workbench-Session':session,'Content-Type':'application/json','Accept':'application/json'},
    body:JSON.stringify({proposal_id:proposal,deal_index:dealIndex})
  });
  const data=await response.json();
  if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'TOASTER_HOLD');
  if(data.schema!=='workbench.stack2-024-toaster-delight-preview/v0'||
    data.original_toaster_policy!=='candidate-move-deck/v1'||
    data.original_toaster_renderer_executed!==false||
    data.original_toaster_source_media_loaded!==false||
    data.original_receiver_changed!==false||
    data.creative_output_authorized!==false||
    data.admissions_performed!==0||
    data.relations_persisted!==false||
    !Array.isArray(data.cards)||data.cards.length!==6){
    throw Error('NATIVE_TOASTER_BRAIN_WITNESS_INVALID');
  }
  return data;
}
function excerpt(v,limit=65){
  const value=String(v??'UNDECLARED');
  return value.length>limit?value.slice(0,limit-1)+'…':value;
}
function wrap(v,limit=38){
  const parts=[];let line='';
  for(const word of String(v).split(/\s+/)){
    if((line+' '+word).trim().length>limit&&line){parts.push(line);line='';}
    line=(line+' '+word).trim();
  }
  if(line)parts.push(line);
  return parts.slice(0,2);
}
function typography(x,y,value,size=19,fill='#24342b',weight=400){
  return sx('text',{x,y,fill,'font-family':'Georgia,serif','font-size':size,
    'font-weight':weight},value);
}
function drawCard(card){
  const original=card.declared_evidence[0];
  const paper=sx('svg',{xmlns:ns,viewBox:'0 0 900 560',width:900,height:560,
    role:'img','aria-label':'Unsigned, local provenance postcard suggested by the original Toaster move deck'});
  paper.append(sx('rect',{x:4,y:4,width:892,height:552,rx:19,fill:'#f3ebd7',stroke:'#967d5f','stroke-width':3}));
  paper.append(sx('rect',{x:34,y:37,width:832,height:480,rx:5,fill:'#eee4cc',stroke:'#c2b59b'}));
  // Tape is visual form only; not a claim of historical photographic media.
  paper.append(sx('rect',{x:330,y:8,width:225,height:33,fill:'#d1b987',opacity:'.58',transform:'rotate(-2 442 24)'}));
  paper.append(sx('path',{d:'M 62 125 Q 168 94 268 132 T 464 149 T 846 94',stroke:'#76937d',
    'stroke-width':3,'stroke-dasharray':'4 12',fill:'none'}));
  paper.append(typography(64,86,'THE STATIC COLLECTIVE  /  USEFUL DELIGHT',18,'#4d6454',650));
  paper.append(typography(65,200,card.title,40,'#26382c',700));
  let y=258;
  for(const line of wrap(card.prompt,44)){paper.append(typography(67,y,line,23));y+=35;}
  const underline=original?excerpt(original.kind.replaceAll('_',' '),50):'TWO PARTICULARS';
  paper.append(typography(67,355,underline,17,'#87654a',700));
  paper.append(typography(67,392,'A QUESTION, NOT A CLAIM.',22,'#87654a'));
  paper.append(sx('rect',{x:640,y:78,width:152,height:156,fill:'none',stroke:'#87654a','stroke-width':3}));
  paper.append(sx('circle',{cx:717,cy:153,r:51,fill:'none',stroke:'#87654a','stroke-width':2,'stroke-dasharray':'6 7'}));
  paper.append(typography(680,145,'HOLD',25,'#87654a',700));
  paper.append(typography(674,175,'NO ADMIT',14,'#87654a',700));
  paper.append(sx('line',{x1:62,y1:427,x2:838,y2:427,stroke:'#b1a287','stroke-width':2}));
  paper.append(typography(65,458,excerpt(card.from_source_world,60),18,'#405b4b'));
  paper.append(typography(65,483,excerpt(card.to_source_world||'AN UNSENT SOLO QUESTION',70),18,'#405b4b'));
  paper.append(typography(65,506,'TOASTER MOVE '+(card.slot+1)+
    '  ·  '+excerpt(card.original_toaster_move_address,27),12,'#87654a'));
  paper.append(typography(625,508,'UNSIGNED / PREVIEW ONLY',13,'#87654a',700));
  return paper;
}
function chooseCard(card){
  if(!preview||!card.available)return;
  chosen=card;
  $('delight-024-preview-title').textContent=card.title;
  $('delight-024-preview-note').textContent=card.invitation+
    ' Original Toaster move, translated into a metadata-only creative question.';
  $('delight-024-paper').replaceChildren(drawCard(card));
  $('delight-024-export').disabled=false;
  renderDeck();
  window.dispatchEvent(new CustomEvent('stack-floor:toaster-delight-choice', {detail:{preview,card}}));
}
function renderDeck(){
  const deck=$('delight-024-deck');deck.replaceChildren();
  if(!preview)return;
  preview.cards.forEach(card=>{
    const b=node('button','delight-024-card');
    b.type='button';b.disabled=!card.available;
    b.setAttribute('aria-pressed',String(chosen?.slot===card.slot));
    b.append(node('span','delight-024-card-num','0'+(card.slot+1)),
      node('strong','',card.title),
      node('span','',card.prompt),
      node('span','delight-024-card-origin',excerpt(card.original_toaster_label,58)),
      node('span','delight-024-card-foot',card.available?
         card.evidence_count+' DECLARED FACTS · NOT EXECUTED':
         'REFUSED · NO SIGNED CURRENT RELATION'));
    b.addEventListener('click',()=>chooseCard(card));deck.append(b);
  });
}
async function deal(){
  if(working||!enabled||!proposal)return;
  const current=proposal;
  working=true;clear();controls();
  msg('Cold replaying receiver HOLD and dealing six moves using pinned original Toaster code…');
  try{
    const x=await request();
    if(current!==proposal||receiverState!==x.receiver_state_ref)
      throw Error('RECEIVER_STATE_CHANGED_SINCE_MY CELIUM_SELECTION'.replace(' ',''));
    preview=x;renderDeck();
    $('delight-024-state').textContent='ORIGINAL CANDIDATE MOVE DECK / V1 · VERIFIED';
    msg('Six source-bounded ideas from real Toaster policy. Nothing was executed, copied or admitted.');
  }catch(e){clear();msg('HOLD: '+e.message);}
  finally{working=false;controls();}
}
window.addEventListener('stack-floor:mycelium-proposal-selected',e=>{
  const id=e.detail?.proposal_id,state=e.detail?.receiver_state_ref;
  const changed=id!==proposal||state!==receiverState;
  if(!changed)return;
  proposal=hex.test(id||'')?id:null;
  receiverState=state||null;dealIndex=0;
  clear();
  $('delight-024-relation').textContent=proposal?
    excerpt(proposal,32)+'…':'NO CURRENTLY FOCUSED THREAD';
  msg(proposal?'A signed-wrapper relationship is ready for optional Toaster questions.':
    'Select an evidenced Mycelium thread first.');
  controls();
});
window.addEventListener('stack-floor:crossing-held',()=>{
  proposal=null;receiverState=null;dealIndex=0;clear();
  msg('The receiving world changed. Select a newly verified Mycelium thread again.');
});
$('delight-024-deal').addEventListener('click',()=>{dealIndex=0;deal();});
$('delight-024-again').addEventListener('click',()=>{if(dealIndex<8){dealIndex++;deal();}});
$('delight-024-export').addEventListener('click',()=>{
  if(!chosen||!preview)return;
  const svg=drawCard(chosen);
  svg.setAttribute('data-schema','workbench.stack2-024-unsigned-postcard/v0');
  svg.setAttribute('data-receiver-state-ref',preview.receiver_state_ref);
  svg.setAttribute('data-toaster-move',chosen.original_toaster_move_address);
  svg.setAttribute('data-proposal-id',preview.selected_relation_proposal_id);
  svg.setAttribute('data-original-source-signature-reverified','false');
  svg.setAttribute('data-admission-authorized','false');
  const xml=new XMLSerializer().serializeToString(svg);
  const blob=new Blob([xml],{type:'image/svg+xml'});
  const u=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=u;a.download='stack-squared-024-useful-delight-unsigned-postcard.svg';
  a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
});
async function init(){
  try{
    const r=await fetch('/api/stack-floor/delight/status',{credentials:'same-origin'});
    if(!r.ok)throw Error('NO_TOASTER_SOURCE');
    const s=await r.json();
    enabled=s.enabled===true&&s.proposals_only===true&&
      s.media_execution_available===false&&s.receiver_admission_available===false;
    $('delight-024-state').textContent=enabled?
      'ORIGINAL SOURCE OPTED IN · NO MEDIA PROCESSING':
      'DISABLED · PINNED ORIGINAL TOASTER CHECKOUT REQUIRED';
  }catch{enabled=false;$('delight-024-state').textContent='SOURCE UNAVAILABLE';}
  controls();
}
init();
