/** STACK² 020 native door. This file alone may contact same-origin Workbench.
 * Native execution is opt-in, preview-bound, explicit one-use ACT.
 */
const $=id=>document.getElementById(id);
let enabled=false,connected=false,preview=null,session=null,receipt=null,busy=false;
const state=text=>{$('native-020-result').textContent=text;};
function controls(){
  $('native-020-preview').disabled=!enabled||!connected||busy;
  const pending=!!preview&&!busy;
  $('native-020-ack').disabled=!pending;
  $('native-020-phrase').disabled=!pending;
  $('native-020-act').disabled=!(pending&&$('native-020-ack').checked&&
    $('native-020-phrase').value==='ACT'&&connected);
  $('native-020-export').disabled=!receipt;
}
function revoke(reason){
  preview=null;$('native-020-ack').checked=false;$('native-020-phrase').value='';
  $('native-020-proposal').textContent='No exact proposal issued.';
  if(reason)state(reason);
  controls();
}
async function jsonResponse(url,method='GET',body=null){
  const opts={method,headers:{Accept:'application/json'}};
  if(body!==null){
    opts.headers['Content-Type']='application/json';
    opts.headers['X-Workbench-Session']=session;
    opts.body=JSON.stringify(body);
  }
  const res=await fetch(url,opts);
  const data=await res.json();
  if(!res.ok)throw Error(typeof data.detail==='string'?data.detail:'WORKBENCH_NATIVE_REQUEST_REFUSED');
  return data;
}
async function status(){
  try{
    const response=await jsonResponse('/api/stack-floor/native/status');
    enabled=response.enabled===true;
    $('native-020-state').textContent=enabled?
      'OPERATOR CONFIGURED · REAL NATIVE ACT AVAILABLE':'OFF BY DEFAULT · OWNER CONFIGURATION REQUIRED';
  }catch(e){enabled=false;$('native-020-state').textContent='LOCAL NATIVE STATUS UNAVAILABLE';}
  controls();
}
window.addEventListener('stack-floor:changed',event=>{
  connected=event.detail?.connected===true;
  if(preview&&!connected)revoke('HOLD: stack changed; previous exact-source preview discarded.');
  controls();
});
$('native-020-ack').addEventListener('change',controls);
$('native-020-phrase').addEventListener('input',controls);
$('native-020-preview').addEventListener('click',async()=>{
  if(!enabled||!connected||busy)return;
  busy=true;receipt=null;revoke();
  state('Requesting a fresh native GHoT 030 preflight; no operation is executing.');
  try{
    if(!session){
      const bootstrap=await jsonResponse('/api/bootstrap');
      session=bootstrap.session_token;
    }
    const result=await jsonResponse('/api/stack-floor/native/preview','POST',{
      card_ids:['cannon','planz','ghot','relatte'],operation:'hash-exact-source'});
    if(!connected)throw Error('STACK_CHANGED_DURING_PREVIEW');
    if(result.status!=='READY'||result.executed!==false)throw Error('NATIVE_PREVIEW_NOT_READY');
    preview=result;
    $('native-020-proposal').textContent=
      'READY '+result.proposal_address.slice(0,22)+'… · '+result.expires_in_seconds+'s';
    state('Preview READY for one source-hash only. Check consent, type ACT, and use the one-use ticket.');
  }catch(e){state('HOLD: '+e.message);}
  finally{busy=false;controls();}
});
$('native-020-act').addEventListener('click',async()=>{
  if(!preview||busy||!connected||!$('native-020-ack').checked||
    $('native-020-phrase').value!=='ACT')return;
  busy=true;const p=preview;preview=null;receipt=null;
  controls();state('Consuming a single-use preview; GHoT performs a fresh source inspection and signs its own result.');
  try{
    const result=await jsonResponse('/api/stack-floor/native/act','POST',{
      card_ids:['cannon','planz','ghot','relatte'],
      consent_nonce:p.consent_nonce,proposal_address:p.proposal_address,
      confirm_phrase:'ACT',acknowledge_single_use:true
    });
    if(result.status!=='EXECUTED_AND_LOCAL_RECEIPT_VERIFIED'||
      result.ticket_spent!==true||result.receiver_admitted!==false){
      throw Error('UNEXPECTED_NATIVE_RECEIPT');
    }
    receipt=result;
    state('NATIVE GHoT SIGNED RECEIPT VERIFIED · '+result.receipt_id+
      ' · ticket spent · original planZ program NOT executed · no reLATTE ADMIT.');
  }catch(e){state('HOLD: '+e.message+' · preview was spent; request a new preview before any retry.');}
  finally{busy=false;revoke();controls();}
});
$('native-020-export').addEventListener('click',()=>{
  if(!receipt)return;
  const blob=new Blob([JSON.stringify(receipt,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='stack-squared-020-native-ghot-signed-act.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),800);
});
status();
