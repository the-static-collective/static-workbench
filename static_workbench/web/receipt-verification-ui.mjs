import {inspectApiResult,matchPublicFile} from './receipt-verification-core.mjs';

const $=id=>document.getElementById(id);
const status=(id,text)=>{$(id).textContent=text;};
let porter=null,epoch=0;
function clear({file=true}={}){
 epoch++;porter=null;
 if(file)$('public-file').value='';
 $('match').disabled=true;
 for(const id of ['report-address','crossing-address','received-address','hold-address'])
  status(id,'—');
 status('porter-status','NOT REQUESTED');
 status('porter-time','NOT VERIFIED');
 status('porter-scope','SELF-DESCRIBING TEST KEYS, NOT HUMAN IDENTITY');
 status('attestation-id','—');
 status('match-status','No local native verification or public artifact has been bound.');
 $('checks').replaceChildren(document.createTextNode('No locally verified report loaded.'));
}
function render(p){
 status('porter-status','OPERATOR-RUN LOCAL NATIVE VERIFICATION REPORTED');
 status('porter-time',p.verified_at+' · historical snapshot');
 status('porter-scope','SIGNED CONTENT CHECKED ON HOST · IDENTITY NOT AUTHENTICATED');
 status('attestation-id',p.attestation_sha256);
 for(const [target,key] of [
  ['report-address','ghot_report_id'],['crossing-address','relatte_crossing_id'],
  ['received-address','relatte_received_receipt_id'],['hold-address','relatte_hold_receipt_id']])
  status(target,p[key]);
 const box=$('checks');box.replaceChildren();
 for(const s of p.checks){
  const row=document.createElement('div');row.textContent='✓ '+s.replaceAll('_',' ');
  box.append(row);
 }
}
$('read-local').addEventListener('click',async()=>{
 const current=++epoch;porter=null;$('match').disabled=true;
 status('porter-status','READING LOCAL SUMMARY ONLY');
 try {
  // Hard-coded, read-only, same-origin endpoint. No user paths and no POST.
  const response=await fetch('/api/receipt-verification/latest',{
   method:'GET',credentials:'same-origin',cache:'no-store',
   headers:{'Accept':'application/json'}
  });
  if(!response.ok)throw Error('LOCAL_READ_REFUSED');
  const data=await response.json();
  if(current!==epoch)return;
  const result=await inspectApiResult(data);
  if(current!==epoch)return;
  if(!result){
   status('porter-status','HOLD: '+data.state);
   status('porter-time','NOT VERIFIED');
   status('match-status','Operator must first run the source-pinned local verification CLI.');
   return;
  }
  porter=result;render(porter);
  $('match').disabled=!$('public-file').files?.length;
  status('match-status','Host verification loaded. Select the exact redacted public witness to bind its bytes.');
 }catch(e){
  if(current!==epoch)return;
  status('porter-status','HOLD: '+String(e.message).slice(0,115));
  status('match-status','No trusted local host verification available.');
 }
});
$('public-file').addEventListener('change',()=>{
 status('match-status','A new public file was selected. It has not been compared.');
 $('match').disabled=!porter||!$('public-file').files?.length;
});
$('match').addEventListener('click',async()=>{
 const current=++epoch;
 const file=$('public-file').files?.[0];
 if(!porter||!file)return;
 if(file.size===0||file.size>12288){
  status('match-status','HOLD: PUBLIC_FILE_SIZE_INVALID');return;
 }
 status('match-status','BINDING LOCAL FILE BY EXACT SHA-256');
 try{
  const bytes=new Uint8Array(await file.arrayBuffer());
  if(current!==epoch)return;
  const result=await matchPublicFile(porter,bytes);
  if(current!==epoch)return;
  status('match-status',result.status+' · host verification '+result.verified_at+
   '. No new signature or admission is created.');
 }catch(e){
  if(current!==epoch)return;
  status('match-status','HOLD: '+String(e.message).slice(0,120));
 }
});
$('clear-local').addEventListener('click',()=>clear());
