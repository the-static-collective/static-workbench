/**
 * STACK² 024 — Living Receipt Floor (browser-local, read-only).
 * Exact typed addresses are evidence references, not signature verification.
 */
export const SCHEMA = 'cannon.stack-squared-ai-relatte-public/v0';
export const GHOT_PIN = '6194d91ba83bad63606f6f6741723007227518f2';
export const RELATTE_PIN = 'dcc8cdca84c440aa4294134f020fb7095bf87f24';
export const CI_RUN = 'https://github.com/the-static-collective/CANNON/actions/runs/38165140352';
export const SOURCE = Object.freeze([
  {project:'GHoT',commit:GHOT_PIN,path:'ghot/ai_recomposition.py',
   label:'Original source-owned processing organ'},
  {project:'CANNON',commit:'4f981da3d7ab2f72ba4654b104a0ad4de33dceb0',
   path:'scripts/stack-squared-023-ai.mjs',label:'Historical STACK² 023 crossing carrier'},
  {project:'reLATTE',commit:RELATTE_PIN,path:'src/roundtrip.ts',
   label:'Original R14 receiver and durable journal protocol'}
]);
const HEX64 = /^[a-f0-9]{64}$/;
const PATTERNS = Object.freeze({
  ghot_report_id:/^ai-recomposition-report-v0:[a-f0-9]{64}$/,
  cannon_witness_id:/^cannon-stack2-ai-witness-v0:[a-f0-9]{64}$/,
  relatte_crossing_id:/^relatte-crossing-v0:[a-f0-9]{64}$/,
  relatte_received_receipt_id:/^relatte-receipt-v0:[a-f0-9]{64}$/,
  relatte_hold_receipt_id:/^relatte-receipt-v0:[a-f0-9]{64}$/,
  ghot_signed_execution_receipts:/^relatte-receipt-v0:[a-f0-9]{64}$/,
  ghot_portable_packet_ids:/^portable-seed-v0:[a-f0-9]{64}$/
});
const FIELDS = Object.freeze([
  'schema','source_commit','relatte_commit','ghot_report_id','ghot_report_sha256',
  'cannon_witness_id','ghot_signed_execution_receipts','ghot_portable_packet_ids',
  'relatte_crossing_id','relatte_received_receipt_id','relatte_hold_receipt_id',
  'destination','original_ghot_donor_reexecuted','original_relatte_receiver_used',
  'cold_signatures_verified','source_human_identity_established','receiver_admitted',
  'external_effects','production_deployed'
]);
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const fail=(condition,code)=>{if(!condition)throw Error(code);};
const hex=x=>typeof x==='string'&&HEX64.test(x);
const validId=(key,x)=>typeof x==='string'&&PATTERNS[key].test(x);
export function inspectPublicWitness(value){
  fail(plain(value),'NOT_AN_OBJECT');
  fail(Object.keys(value).sort().join('|')===FIELDS.slice().sort().join('|'),'UNEXPECTED_OR_MISSING_PUBLIC_FIELDS');
  fail(value.schema===SCHEMA,'NOT_STACK2_023');
  fail(value.source_commit===GHOT_PIN && value.relatte_commit===RELATTE_PIN,'SOURCE_PINS_DO_NOT_MATCH');
  fail(validId('ghot_report_id',value.ghot_report_id),'INVALID_GHOT_REPORT_ID');
  fail(hex(value.ghot_report_sha256),'INVALID_PRIVATE_REPORT_DIGEST');
  fail(validId('cannon_witness_id',value.cannon_witness_id),'INVALID_CANNON_WITNESS_ID');
  for(const field of ['ghot_signed_execution_receipts','ghot_portable_packet_ids']){
    const arr=value[field];
    fail(Array.isArray(arr)&&arr.length>=1&&arr.length<=2&&arr.every(x=>validId(field,x)),
         'INVALID_'+field.toUpperCase());
    fail(new Set(arr).size===arr.length,'DUPLICATED_'+field.toUpperCase());
  }
  fail(value.ghot_signed_execution_receipts.length===value.ghot_portable_packet_ids.length,
       'PACKET_RECEIPT_CARDINALITY_MISMATCH');
  for(const field of ['relatte_crossing_id','relatte_received_receipt_id','relatte_hold_receipt_id']){
    fail(validId(field,value[field]),'INVALID_'+field.toUpperCase());
  }
  fail(value.relatte_received_receipt_id!==value.relatte_hold_receipt_id,
       'RECEIVE_AND_HOLD_MUST_BE_DISTINCT');
  fail(value.destination==='R3_HOLD'&&value.original_ghot_donor_reexecuted===false&&
       value.original_relatte_receiver_used===true&&value.cold_signatures_verified===true&&
       value.source_human_identity_established===false&&value.receiver_admitted===false&&
       value.external_effects===0&&value.production_deployed===false,
       'AUTHORITY_OR_OUTCOME_OVERCLAIM');
  // A local JSON file is a self-declared report. No digital signature is checked here.
  return {
    schema:SCHEMA,source_profile:'EXACT_DECLARED_SOURCE_PINS',
    structural:'MATCHED_KNOWN_CI_REPORT_SHAPE',
    signature_status:'FOREIGN_NATIVE_CI_CLAIM_NOT_BROWSER_VERIFIED',
    source_identity_status:'UNAUTHENTICATED_PUBLIC_JSON',
    disposition:'REPORTED_R3_HOLD_NOT_ADMITTED',
    native_calls_by_browser:0,
    credential_import:false
  };
}
export function cardsFor(value){
  inspectPublicWitness(value);
  const cards = [];
  const add=(id,kind,phase,title,detail,authority='NONE')=>{
    cards.push({id,kind,phase,title,detail,authority,index:cards.length});
  };
  add(value.ghot_report_id,'processing','processing','Original GHoT report',
      'Source-owned work report. Input text and model outputs are not exposed here.');
  for(let i=0;i<value.ghot_signed_execution_receipts.length;i++){
    add(value.ghot_signed_execution_receipts[i],'execution-receipt','processing',
      'GHoT signed execution '+(i+1),
      'Signed local Instrument Rack execution receipt. Not a receiver HOLD.');
    add(value.ghot_portable_packet_ids[i],'packet','processing',
      'Portable seed packet '+(i+1),
      'A signed-evidence-bearing packet. Its arrival never grants admission.');
  }
  add(value.cannon_witness_id,'source-witness','crossing','CANNON 022 witness',
      'Source-pinned historical inspection. CANNON witness is unsigned.');
  add(value.relatte_crossing_id,'signed-crossing','crossing','reLATTE R14 crossing',
      'Reported independently signed opaque crossing, carrying GHoT evidence.');
  add(value.relatte_received_receipt_id,'received','receiver','Receiver: RECEIVED',
      'Reported receiver-signed arrival. Receipt does not mean ADMIT.','RECEIVER_LOCAL');
  add(value.relatte_hold_receipt_id,'hold','receiver','Receiver: R3_HOLD',
      'Reported receiver-signed HOLD. The receiving world still owns disposition.','RECEIVER_LOCAL');
  return cards;
}
export function inspectParticular(value,id){
  const item=cardsFor(value).find(x=>x.id===id);
  fail(item,'UNKNOWN_RECEIPT');
  return {...item,source_commit:item.phase==='processing'?GHOT_PIN:
    item.phase==='receiver'?RELATTE_PIN:null,
    verification:'IDENTIFIERS_AND_DECLARED_RELATIONS_ONLY',
    claimed_effect:item.kind==='hold'?'RECEIVER_LOCAL_HOLD':'NONE',
    browser_execution:false};
}
export function traverse(value,phase='all'){
  fail(['all','processing','crossing','receiver'].includes(phase),'INVALID_APERTURE');
  const cards=cardsFor(value);
  const visible=cards.filter(x=>phase==='all'||x.phase===phase);
  return {phase,cards:visible,total:cards.length,visible:visible.length,
    provenance:'DECLARED_CANNON_023_PUBLIC_SUMMARY',
    cryptographic_verification:'NOT_PERFORMED',
    source_ownership:'NOT_ESTABLISHED',
    state_mutated:false};
}
function canonical(x){
  if(x===null||typeof x==='string'||typeof x==='boolean')return JSON.stringify(x);
  if(typeof x==='number'){fail(Number.isSafeInteger(x),'NON_INTEGER');return JSON.stringify(x);}
  if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
  fail(plain(x),'NON_CANONICAL');
  return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
}
const sha=async s=>{
  fail(!!globalThis.crypto?.subtle,'WEBCRYPTO_UNAVAILABLE');
  const result=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(s));
  return Array.from(new Uint8Array(result),x=>x.toString(16).padStart(2,'0')).join('');
};
export async function makeUnsignedInspection(value,{authorized=false}={}){
  fail(authorized===true,'EXPLICIT_LOCAL_INSPECTION_REQUIRED');
  inspectPublicWitness(value);
  const packet={
    schema:'workbench.stack-squared-receipt-inspection/v0',
    imported_source:SCHEMA,source_pin:GHOT_PIN,receiver_source_pin:RELATTE_PIN,
    reported_report_sha256:value.ghot_report_sha256,
    reported_ghot_receipts:[...value.ghot_signed_execution_receipts],
    reported_portable_packets:[...value.ghot_portable_packet_ids],
    reported_crossing:value.relatte_crossing_id,
    reported_receiver_receipts:[value.relatte_received_receipt_id,value.relatte_hold_receipt_id],
    structural_check:'PASSED',
    signature_verification:'NOT_PERFORMED',
    receiver_journal_verification:'NOT_PERFORMED',
    git_source_verification:'NOT_PERFORMED',
    foreign_ci_url:CI_RUN,
    recipient_admission:false,
    browser_execution:false,
    browser_network:false,
    receipt_is_signed:false,
    authority_granted:false
  };
  return {...packet,local_sha256:await sha(canonical(packet))};
}
