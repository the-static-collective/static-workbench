import {CARDS,card,inspectFloor,addCard,removeCard,inspectSummary,inspectNativeOutput,runLocalTrial} from './stack-floor-core.mjs';

const $=id=>document.getElementById(id);
let slots=[null,null,null,null],active='cannon',summary=null,native=null,trial=null,revision=0;
const h=(tag,cls='',txt='')=>{const x=document.createElement(tag);if(cls)x.className=cls;if(txt)x.textContent=txt;return x;};
const stateMessage=(id,value)=>{$(id).textContent=value;};
function showCard(id){
  const item=card(id);if(!item)return;active=id;
  stateMessage('part-name',item.title+' · '+item.label);
  stateMessage('part-description',item.summary);
  const box=$('part-details');box.replaceChildren();
  for(const [k,v] of [['ORIGINAL REPOSITORY',item.repo],['EXACT GIT COMMIT',item.commit],
    ['SOURCE FILE',item.source],['INPUT SOCKET',item.input],['OUTPUT SOCKET',item.output],
    ['OPERATOR ROLE',item.role]]){
    const line=h('div');line.append(h('span','',k),h('strong','',v));box.append(line);
  }
  const line=h('div');line.appendChild(h('span','','GIT SOURCE ADDRESS'));
  const link=h('a','',item.repo+' @ '+item.commit.slice(0,10)+' ↗');
  link.href='https://github.com/'+item.repo+'/blob/'+item.commit+'/'+item.source;
  link.rel='noopener noreferrer';link.target='_blank';line.append(link);box.append(line);
}
function render(){
  const view=inspectFloor(slots);
  const tray=$('tray');tray.replaceChildren();
  for(const brick of CARDS){
    const used=slots.includes(brick.id);
    const b=h('button','brick');
    b.type='button';b.draggable=!used;b.dataset.tint=brick.tint;
    b.dataset.id=brick.id;b.setAttribute('aria-disabled',String(used));
    b.title='Inspect and place '+brick.title;
    b.append(h('span','name',brick.title),h('span','type',brick.role),
      h('span','mini',brick.input+' → '+brick.output));
    b.addEventListener('click',()=>{
      showCard(brick.id);
      if(used){stateMessage('fit-caption',brick.title+' already on the floor.');return;}
      const first=slots.indexOf(null);
      if(first<0){stateMessage('fit-caption','Floor full. Remove a brick to replace it.');return;}
      try{slots=addCard(slots,brick.id,first).slots;resetTrial();render();}
      catch(e){stateMessage('fit-caption','HOLD: '+e.message);}
    });
    b.addEventListener('dragstart',ev=>{
      if(used){ev.preventDefault();return;}
      ev.dataTransfer.setData('text/plain',brick.id);
      ev.dataTransfer.effectAllowed='copy';
      showCard(brick.id);
    });
    tray.append(b);
  }
  const sockets=$('sockets');sockets.replaceChildren();
  view.links.forEach((link,index)=>{
    const selected=card(slots[index]);
    const slot=h('div','socket');slot.dataset.slot=String(index);
    const label=h('span','number',String(index+1).padStart(2,'0'));
    const content=h('div','occupant');
    content.append(h('strong','',selected?selected.title+' / '+selected.label:'Empty socket'),
      h('small','',selected?selected.input+' → '+selected.output:'Drop a brick here, or tap one on the left.'));
    const state=h('span','socket-state '+(link.status==='FITS'?'fit':link.status==='HOLD'?'hold':'empty'),
      link.status);
    slot.append(label,content,state);
    if(selected){
      const remove=h('button','', '×');remove.type='button';
      remove.setAttribute('aria-label','Remove '+selected.title+' from socket '+(index+1));
      remove.addEventListener('click',()=>{slots=removeCard(slots,index).slots;resetTrial();render();});
      slot.append(remove);
      content.addEventListener('click',()=>showCard(selected.id));
    }
    slot.addEventListener('dragover',ev=>{
      if(!slots[index]){ev.preventDefault();slot.classList.add('dragover');}
    });
    slot.addEventListener('dragleave',()=>slot.classList.remove('dragover'));
    slot.addEventListener('drop',ev=>{
      ev.preventDefault();slot.classList.remove('dragover');
      const id=ev.dataTransfer.getData('text/plain');
      try{slots=addCard(slots,id,index).slots;showCard(id);resetTrial();render();}
      catch(e){stateMessage('fit-caption','HOLD: '+e.message);}
    });
    sockets.append(slot);
  });
  stateMessage('fit-caption',view.connected?
    'ALL FOUR SOCKETS FIT · source, execution and admission remain separate':
    view.links.some(x=>x.status==='HOLD')?'HOLD · a socket mismatch prevents a local trial':
    view.slots.filter(Boolean).length+'/4 pieces placed · complete the floor to connect');
  updateButtons();
  window.dispatchEvent(new CustomEvent('stack-floor:changed',{detail:{connected:view.connected}}));
}
function resetTrial(){
  trial=null;$('export').disabled=true;
  stateMessage('trial-status','New arrangement or evidence. No local trial is currently verified.');
}
function updateButtons(){
  let ready=false;
  try{ready=inspectFloor(slots).connected&&!!summary&&!!native&&$('consent').checked;}catch{}
  $('trial').disabled=!ready;
}
async function fileInput(id){
  const f=$(id).files?.[0];
  if(!f)throw Error('MISSING_'+id.toUpperCase()+'_FILE');
  const cap=id==='summary'?196608:2097152;
  if(f.size>cap)throw Error('FILE_SIZE_EXCEEDS_'+cap+'_BYTES');
  return JSON.parse(await f.text());
}
function clearImport(clearInputs=true){
  revision++;summary=null;native=null;trial=null;$('consent').checked=false;
  if(clearInputs){$('summary').value='';$('native').value='';}
  stateMessage('evidence-status','NO FILES INSPECTED');
  stateMessage('source-status','NO LOCAL SOURCE VERIFIED');
  $('export').disabled=true;
  stateMessage('trial-status','Awaiting arrangement, source files, and explicit authorization.');
  updateButtons();
}
$('reset').addEventListener('click',()=>{slots=[null,null,null,null];resetTrial();render();});
$('forget').addEventListener('click',()=>clearImport());
for(const name of ['summary','native'])$(name).addEventListener('change',()=>clearImport(false));
$('consent').addEventListener('change',()=>{resetTrial();updateButtons();});
$('inspect').addEventListener('click',async()=>{
  const current=++revision;summary=null;native=null;trial=null;$('export').disabled=true;
  stateMessage('evidence-status','CHECKING LOCAL FILES');
  try{
    const [s,n]=await Promise.all([fileInput('summary'),fileInput('native')]);
    inspectSummary(s);inspectNativeOutput(n,s);
    if(current!==revision)return;
    summary=s;native=n;
    stateMessage('evidence-status','STRUCTURAL CHECK PASSED · 2 SOURCE RECORDS');
    stateMessage('source-status','FOREIGN CLAIMS; GIT OBJECTS NOT VERIFIED HERE');
    stateMessage('trial-status','Files pass structural checks. Connect four sockets and approve one local hash comparison.');
    updateButtons();
  }catch(e){
    if(current!==revision)return;
    stateMessage('evidence-status','HOLD: '+e.message);
    stateMessage('source-status','NOT VERIFIED');updateButtons();
  }
});
$('trial').addEventListener('click',async()=>{
  if($('trial').disabled)return;
  const current=++revision;
  $('trial').disabled=true;
  stateMessage('trial-status','Locally recomputing the native result hash and reported GHoT digest…');
  try{
    const result=await runLocalTrial(slots,summary,native,{authorized:$('consent').checked});
    if(current!==revision)return;
    trial=result;
    stateMessage('trial-status','LOCAL HASH RELATION VERIFIED · '+result.native_planz_output_sha256.slice(0,16)+
      '… · source signature and receiver journal NOT reverified here.');
    $('export').disabled=false;
  }catch(e){
    if(current!==revision)return;
    trial=null;stateMessage('trial-status','HOLD / REFUSED: '+e.message);
  }finally{if(current===revision)updateButtons();}
});
$('export').addEventListener('click',()=>{
  if(!trial)return;
  const blob=new Blob([JSON.stringify(trial,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='stack-squared-019-local-trial-unsigned.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),800);
  stateMessage('trial-status','Unsigned browser-only trial packet exported. No new reLATTE receipt or local execution authority exists.');
});
showCard(active);
render();