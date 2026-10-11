/** STACK² 025 — human-only local composition of one bounded Pocket Seed.
 * No new API, no source fetch, no persistence, no signing or receiver effects.
 */
import {makePocketSeed,seedJson,MODES} from './stack-floor-pocket-seed-025-core.mjs';
const $=id=>document.getElementById(id);
let current=null,seed=null,mode='field-note',version=0,busy=false;
const notice=s=>{$('seed-025-message').textContent=s;};
function resetGate(){
  $('seed-025-consent').checked=false;
  $('seed-025-phrase').value='';
}
function clearSeed(){
  seed=null;
  $('seed-025-paper').replaceChildren();
  const label=document.createElement('span');label.className='micro';
  label.textContent='ONE LITTLE THING CAN GROW HERE';
  $('seed-025-paper').append(label);
  $('seed-025-text').textContent='No seed has been made.';
  $('seed-025-id').textContent='NOT YET CREATED';
  $('seed-025-status').textContent='NO SEED MADE';
  for(const id of ['seed-025-save-txt','seed-025-save-svg','seed-025-save-json'])
    $(id).disabled=true;
}
function controls(){
  const ready=!!current&&!busy;
  $('seed-025-consent').disabled=!ready;
  $('seed-025-phrase').disabled=!ready;
  $('seed-025-make').disabled=!(
    ready&&$('seed-025-consent').checked&&$('seed-025-phrase').value==='MAKE');
}
function clear(){
  version++;current=null;
  resetGate();clearSeed();
  $('seed-025-source').textContent='NO TOASTER MOVE CHOSEN';
  notice('Select an available Toaster card. Source media will never be loaded.');
  controls();
}
window.addEventListener('stack-floor:toaster-delight-choice',event=>{
  const input=event.detail;
  if(!input?.preview||!input?.card||input.card.available!==true){
    clear();return;
  }
  version++;current=input;
  resetGate();clearSeed();
  $('seed-025-source').textContent=
    input.card.kind.toUpperCase()+' · '+input.card.title+
    ' · '+String(input.card.source_crossing_ids?.length||0)+' held source(s)';
  notice('Review the declared-metadata-only permission. MAKE is separate from Toaster preview.');
  controls();
});
for(const b of document.querySelectorAll('.seed-025-lanes button[data-mode]')){
  b.addEventListener('click',()=>{
    if(!MODES.includes(b.dataset.mode))return;
    mode=b.dataset.mode;
    for(const v of document.querySelectorAll('.seed-025-lanes button[data-mode]'))
      v.setAttribute('aria-pressed',String(v.dataset.mode===mode));
    version++;resetGate();clearSeed();controls();
    notice('Format changed. Explicit MAKE authorization is required again.');
  });
}
$('seed-025-consent').addEventListener('change',controls);
$('seed-025-phrase').addEventListener('input',controls);
function output(){
  const xml=new DOMParser().parseFromString(seed.svg,'image/svg+xml');
  if(xml.getElementsByTagName('parsererror').length||xml.documentElement.localName!=='svg')
    throw Error('POCKET_SEED_SVG_REFUSED');
  $('seed-025-paper').replaceChildren(document.importNode(xml.documentElement,true));
  $('seed-025-text').textContent=seed.text;
  $('seed-025-id').textContent=seed.manifest.seed_id;
  $('seed-025-status').textContent='MADE LOCALLY · UNSIGNED';
  for(const id of ['seed-025-save-txt','seed-025-save-svg','seed-025-save-json'])
    $(id).disabled=false;
}
$('seed-025-make').addEventListener('click',async()=>{
  if(!current||busy||!$('seed-025-consent').checked||
    $('seed-025-phrase').value!=='MAKE')return;
  const selected=current,epoch=version,selectedMode=mode;
  busy=true;controls();
  resetGate();notice('Composing a deterministic pocket seed locally from the already witnessed metadata…');
  try{
    const packet=await makePocketSeed(selected,{mode:selectedMode});
    if(epoch!==version||selected!==current||selectedMode!==mode)return;
    seed=packet;
    output();
    notice('One source-bound, unsigned micro-artifact made. No payload bytes, network write, receiver action or renderer.');
  }catch(e){
    if(epoch!==version)return;
    clearSeed();notice('MAKE REFUSED: '+e.message);
  }finally{busy=false;controls();}
});
function save(value,mime,filename){
  if(!seed||typeof value!=='string')return;
  const url=URL.createObjectURL(new Blob([value],{type:mime}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download=filename;
  anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('seed-025-save-txt').addEventListener('click',()=>save(seed?.text,
  'text/plain;charset=utf-8','stack-squared-025-pocket-seed.txt'));
$('seed-025-save-svg').addEventListener('click',()=>save(seed?.svg,
  'image/svg+xml','stack-squared-025-pocket-seed.svg'));
$('seed-025-save-json').addEventListener('click',()=>save(seed?seedJson(seed):null,
  'application/json','stack-squared-025-pocket-seed-evidence.json'));
controls();
