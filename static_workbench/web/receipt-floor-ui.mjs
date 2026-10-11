import {SOURCE,inspectPublicWitness,cardsFor,inspectParticular,traverse,
        makeUnsignedInspection,CI_RUN} from './receipt-floor-core.mjs';

const $=id=>document.getElementById(id);
const el=(tag,cls='',content='')=>{
  const item=document.createElement(tag);
  if(cls)item.className=cls;
  if(content)item.textContent=content;
  return item;
};
let witness=null,phase='all',selected=null,receipt=null,epoch=0;
function status(id,text){$(id).textContent=text;}
function erase({input=true}={}){
  epoch++;witness=null;selected=null;receipt=null;
  if(input)$('receipt-file').value='';
  $('consent').checked=false;$('consent').disabled=true;
  $('make-packet').disabled=true;$('export-packet').disabled=true;$('walk').disabled=true;
  status('import-status','NO WITNESS LOADED');
  status('shape-status','NOT INSPECTED');
  status('packet-status','Awaiting an explicitly reviewed public witness.');
  render();
}
function sources(){
  const parent=$('sources');parent.replaceChildren();
  for(const source of SOURCE){
    const group=el('div');
    const link=el('a','',source.project+' · '+source.commit.slice(0,12)+' ↗');
    link.href='https://github.com/the-static-collective/'+source.project+
       '/blob/'+source.commit+'/'+source.path;
    link.rel='noopener noreferrer';link.target='_blank';
    group.append(link,el('small','',source.label));
    parent.append(group);
  }
}
function viewPart(id){
  if(!witness)return;
  const part=inspectParticular(witness,id);
  selected=id;
  status('part-kind',part.kind.toUpperCase()+' · '+part.phase.toUpperCase());
  status('part-name',part.title);
  status('part-detail',part.detail);
  status('part-id',part.id);
  status('part-verification',part.verification);
  status('part-authority',part.authority==='RECEIVER_LOCAL'?'RECEIVER LOCAL, HISTORICALLY REPORTED':'NONE');
  $('copy-address').disabled=false;
  render();
}
function render(){
  const chain=$('chain');chain.replaceChildren();
  for(const button of document.querySelectorAll('.view')){
    const on=button.dataset.phase===phase;
    button.classList.toggle('active',on);
    button.setAttribute('aria-pressed',String(on));
  }
  if(!witness){
    chain.append(el('div','empty','Import the actual STACK² 023 redacted public witness to assemble the crossing. No synthetic receipt is substituted.'));
    $('walk').disabled=true;status('chain-summary','No public witness loaded. No native or browser signature proof.');
    return;
  }
  const {cards,total}=traverse(witness,phase);
  for(const [i,part] of cards.entries()){
    if(i>0)chain.append(el('div','connector'));
    const button=el('button','chain-item phase-'+part.phase);
    button.type='button';button.dataset.kind=part.kind;
    button.setAttribute('aria-pressed',String(selected===part.id));
    button.setAttribute('aria-label',part.title+'; '+part.kind+'; inspect exact address');
    const idx=el('span','step-number',String(part.index+1).padStart(2,'0'));
    const middle=el('span','step-main');
    middle.append(el('strong','',part.title),el('small','',part.id));
    button.append(idx,middle,el('span','type-tag',part.kind.replaceAll('-',' ')));
    button.addEventListener('click',()=>viewPart(part.id));
    chain.append(button);
  }
  $('walk').disabled=false;
  status('chain-summary',cards.length+'/'+total+' particular cards visible. Structural inspection only; independent CI signature claim not reverified here.');
}
async function importWitness(){
  const current=++epoch;receipt=null;selected=null;
  $('export-packet').disabled=true;$('make-packet').disabled=true;
  $('consent').disabled=true;$('consent').checked=false;
  const file=$('receipt-file').files?.[0];
  witness=null;
  if(!file){status('import-status','HOLD: MISSING_LOCAL_FILE');render();return;}
  if(file.size===0||file.size>12288){
    status('import-status','HOLD: PUBLIC_FILE_SIZE_INVALID');render();return;
  }
  status('import-status','READING LOCAL PUBLIC WITNESS');
  try{
    const raw=await file.text();
    if(current!==epoch)return;
    const parsed=JSON.parse(raw);
    inspectPublicWitness(parsed);
    if(current!==epoch)return;
    witness=parsed;
    status('import-status','PUBLIC WITNESS LOADED · '+cardsFor(parsed).length+' PARTICULARS');
    status('shape-status','KNOWN STACK² 023 STRUCTURE MATCHED');
    $('consent').disabled=false;
    $('walk').disabled=false;
    status('packet-status','Public report shape accepted. Native cryptographic evidence remains external.');
    render();
  }catch(e){
    if(current!==epoch)return;
    status('import-status','HOLD: '+String(e.message).slice(0,125));
    status('shape-status','REFUSED');
    render();
  }
}
function walk(){
  if(!witness)return;
  const available=traverse(witness,phase).cards;
  const index=available.findIndex(x=>x.id===selected);
  viewPart(available[(index+1)%available.length].id);
}
async function copySelected(){
  if(!selected)return;
  try{
    await navigator.clipboard.writeText(selected);
    status('chain-summary','Exact selected address copied. No signature verified.');
  }catch{
    status('chain-summary','Clipboard unavailable; exact address remains readable in the particular panel.');
  }
}
async function makePacket(){
  if(!witness||!$('consent').checked)return;
  try{
    receipt=await makeUnsignedInspection(witness,{authorized:true});
    $('export-packet').disabled=false;
    status('packet-status','Unsigned inspection packet composed: sha256:'+receipt.local_sha256+
      '. Browser checked structure, not signatures.');
  }catch(e){
    receipt=null;$('export-packet').disabled=true;
    status('packet-status','HOLD: '+String(e.message).slice(0,120));
  }
}
function exportPacket(){
  if(!receipt||!witness||!$('consent').checked)return;
  const data=new Blob([JSON.stringify(receipt,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(data);
  const a=el('a');a.href=url;a.download='stack2-024-unsigned-inspection.json';
  document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),0);
}
for(const button of document.querySelectorAll('.view'))button.addEventListener('click',()=>{
  phase=button.dataset.phase;selected=null;
  status('part-kind','NO SELECTION');status('part-name','Choose a particular');
  status('part-detail','Each card retains its own provenance and boundary.');
  status('part-id','—');status('part-verification','FOREIGN PUBLIC SUMMARY ONLY');
  status('part-authority','NONE');$('copy-address').disabled=true;
  render();
});
$('receipt-file').addEventListener('change',()=>erase({input:false}));
$('inspect').addEventListener('click',importWitness);
$('clear').addEventListener('click',()=>erase());
$('walk').addEventListener('click',walk);
$('copy-address').addEventListener('click',copySelected);
$('consent').addEventListener('change',()=>{
  receipt=null;$('export-packet').disabled=true;
  $('make-packet').disabled=!witness||!$('consent').checked;
  status('packet-status',$('consent').checked?
     'Explicit authorization for local unsigned inspection recorded in this page only.':
     'No local inspection receipt authorized.');
});
$('make-packet').addEventListener('click',makePacket);
$('export-packet').addEventListener('click',exportPacket);
sources();render();
