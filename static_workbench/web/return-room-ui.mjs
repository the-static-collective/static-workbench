import {LENSES,inspectDocket,lensDetails,nextReaderPacket} from './return-room-core.mjs';
const $=id=>document.getElementById(id);
let active='source',session=null,inspection=null,generation=0;
function show(id){const lens=LENSES.find(d=>d.id===id);active=id;
 for(const btn of $('dials').querySelectorAll('button'))btn.setAttribute('aria-pressed',String(btn.dataset.id===id));
 $('dial-caption').textContent='LENS '+String(LENSES.indexOf(lens)+1).padStart(2,'0')+'/11';
 $('view-eyebrow').textContent=lens.label;$('view-title').textContent=lens.title;
 $('view-description').textContent=lens.description;
 const lines=session?lensDetails(session,id):['No inspected session. Select a local file and inspect first.'];
 const list=$('view-details');list.replaceChildren();
 for(const value of lines){const li=document.createElement('li');li.textContent=value;list.appendChild(li);}
}
for(const lens of LENSES){
 const b=document.createElement('button');
 b.type='button';b.dataset.id=lens.id;b.textContent=lens.label;b.setAttribute('aria-pressed','false');
 b.addEventListener('click',()=>show(lens.id));$('dials').appendChild(b);
}
show('source');
async function load(id,required=false){
 const f=$(id).files?.[0];
 if(!f){if(required)throw Error('REQUIRED_'+id.toUpperCase());return null;}
 if(f.size>131072)throw Error('MAXIMUM_FILE_SIZE_128KB_'+id.toUpperCase());
 return JSON.parse(await f.text());
}
$('inspect').addEventListener('click',async()=>{
 const g=++generation;session=null;inspection=null;$('carry').disabled=true;
 $('status').textContent='Checking the local self-addressed session. No native signing keys or source artifacts are opened.';
 try{
  const s=await load('session',true);
  const c=await load('checkpoint');
  const r=await load('replay');
  const result=await inspectDocket(s,c,r);
  if(g!==generation)return;
  inspection=result;session=s;
  $('status').textContent='LOCAL ADDRESS CHECK PASSED · '+result.session_id+
    ' · native reLATTE signatures NOT reverified in browser · no next turn authorized.';
  $('carry').disabled=false;
  show(active);
 }catch(e){if(g!==generation)return;$('status').textContent='HOLD / REFUSED: '+(e.message||String(e));show(active);}
});
$('clear').addEventListener('click',()=>{
 generation++;session=null;inspection=null;
 for(const id of ['session','checkpoint','replay'])$(id).value='';
 $('carry').disabled=true;
 $('status').textContent='Cleared from this page. Source files, receipts and STATIC-OS sessions were not altered.';
 show(active);
});
$('carry').addEventListener('click',()=>{
 if(!session||!inspection)return;
 const payload=nextReaderPacket(session);
 const blob=new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob);
 const link=document.createElement('a');link.href=url;link.download='return-room-next-reader.json';
 link.click();setTimeout(()=>URL.revokeObjectURL(url),1200);
 $('status').textContent='Downloaded an unsigned, non-authoritative question handoff. A receiving world must independently check source evidence and make its own decision.';
});
