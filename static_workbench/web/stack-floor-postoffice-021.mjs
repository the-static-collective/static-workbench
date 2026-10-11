/** STACK² 021: distinct human CROSS consent, native reLATTE HOLD only. */
const $=id=>document.getElementById(id);
let enabled=false,connected=false,session=null,preview=null,result=null,busy=false;
const msg=s=>{$('postoffice-021-result').textContent=s;};
function ui(){
  $('postoffice-021-preview').disabled=!enabled||!connected||busy||
    !/^ghot-activation-ticket-v0:[a-f0-9]{64}$/.test($('postoffice-021-ticket').value.trim());
  const active=!!preview&&!busy;
  $('postoffice-021-ack').disabled=!active;
  $('postoffice-021-phrase').disabled=!active;
  $('postoffice-021-cross').disabled=!(active&&connected&&
    $('postoffice-021-ack').checked&&$('postoffice-021-phrase').value==='CROSS');
  $('postoffice-021-export').disabled=!result;
}
function revoke(message){
  preview=null;
  $('postoffice-021-ack').checked=false;
  $('postoffice-021-phrase').value='';
  $('postoffice-021-proposal').textContent='No active receiver-authorized preview.';
  if(message)msg(message);
  ui();
}
async function request(path,body=null){
  const opts={headers:{Accept:'application/json'}};
  if(body!==null){
    if(!session){
      const res=await fetch('/api/bootstrap');
      if(!res.ok)throw Error('LOCAL_WORKBENCH_SESSION_UNAVAILABLE');
      session=(await res.json()).session_token;
    }
    opts.method='POST';opts.headers['X-Workbench-Session']=session;
    opts.headers['Content-Type']='application/json';
    opts.body=JSON.stringify(body);
  }
  const res=await fetch(path,opts);
  const json=await res.json();
  if(!res.ok)throw Error(typeof json.detail==='string'?json.detail:'POST_OFFICE_REFUSED');
  return json;
}
async function status(){
  try{
    const x=await request('/api/stack-floor/postoffice/status');
    enabled=x.enabled===true;
    $('postoffice-021-state').textContent=enabled?
      'RECEIVER ROOT CONFIGURED · OWNER POLICY STILL REQUIRED':
      'DISABLED · SEPARATE RECEIVER CONFIGURATION REQUIRED';
  }catch{
    enabled=false;
    $('postoffice-021-state').textContent='LOCAL POST OFFICE UNAVAILABLE';
  }
  ui();
}
window.addEventListener('stack-floor:changed',e=>{
  connected=e.detail?.connected===true;
  if(!connected&&preview)revoke('HOLD: floor changed; crossing proposal discarded.');
  ui();
});
window.addEventListener('stack-floor:native-act',e=>{
  const id=e.detail?.ticket_id;
  if(typeof id==='string'&&/^ghot-activation-ticket-v0:[a-f0-9]{64}$/.test(id)){
    $('postoffice-021-ticket').value=id;
    revoke('Native 020 ACT signed. A separate receiver policy and explicit CROSS are still necessary.');
  }
});
$('postoffice-021-ticket').addEventListener('input',()=>{
  if(preview)revoke('HOLD: source ticket changed; old receiver preview discarded.');
  ui();
});
$('postoffice-021-ack').addEventListener('change',ui);
$('postoffice-021-phrase').addEventListener('input',ui);
$('postoffice-021-preview').addEventListener('click',async()=>{
  if(!enabled||!connected||busy)return;
  revoke();busy=true;ui();
  result=null;
  msg('Reading the existing signed GHoT receipt and pre-existing receiver policy. No crossing yet.');
  try{
    const t=$('postoffice-021-ticket').value.trim();
    const response=await request('/api/stack-floor/postoffice/preview',{
      card_ids:['cannon','planz','ghot','relatte'],ticket_id:t
    });
    if(!connected||$('postoffice-021-ticket').value.trim()!==t)
      throw Error('STACK_OR_TICKET_CHANGED_DURING_PREVIEW');
    if(response.status!=='READY_TO_REQUEST_HOLD'||
       response.crossing_performed!==false||response.disposition!=='HOLD')
      throw Error('UNEXPECTED_CROSSING_PREVIEW');
    preview=response;
    $('postoffice-021-proposal').textContent=
      'RECEIVER '+response.receiver_world+' · HOLD only · '+response.ttl_seconds+'s';
    msg('GHoT original signature verified and receiver-owned policy permits this precise receipt for HOLD. Tick consent, type CROSS, and explicitly request the crossing.');
  }catch(e){msg('HOLD: '+e.message);}
  finally{busy=false;ui();}
});
$('postoffice-021-cross').addEventListener('click',async()=>{
  if(!preview||!connected||busy||!$('postoffice-021-ack').checked||
      $('postoffice-021-phrase').value!=='CROSS')return;
  const p=preview;
  revoke();busy=true;ui();
  msg('One sender CROSS approval spent. Native reLATTE signs the crossing and receiver-owned RECEIVED/HOLD receipts.');
  try{
    const x=await request('/api/stack-floor/postoffice/cross',{
      card_ids:['cannon','planz','ghot','relatte'],
      ticket_id:p.ticket_id,consent_nonce:p.consent_nonce,
      expected_receipt_id:p.receipt_id,
      confirm_phrase:'CROSS',acknowledge_receiver_hold:true
    });
    if(x.status!=='RECEIVED_AND_HELD'||x.disposition!=='HOLD'||
      x.receiver_admitted!==false||x.relatte_signatures_verified!==3)
      throw Error('UNEXPECTED_NATIVE_CROSSING_OUTCOME');
    result=x;
    msg('RECEIVED → HOLD: '+x.crossing_id+' · THREE reLATTE signatures verified · GHoT native receipt checked. No ADMIT.');
  }catch(e){
    result=null;
    msg('HOLD / REFUSED: '+e.message+' · CROSS approval was spent; no automatic retry.');
  }finally{busy=false;ui();}
});
$('postoffice-021-export').addEventListener('click',()=>{
  if(!result)return;
  const blob=new Blob([JSON.stringify(result,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='stack-squared-021-signed-received-hold.json';
  link.click();setTimeout(()=>URL.revokeObjectURL(url),800);
});
status();
