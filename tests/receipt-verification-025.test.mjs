import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {GHOT_PIN,RELATTE_PIN} from '../static_workbench/web/receipt-floor-core.mjs';
import {CANNON_PIN,PORTER_SCHEMA,API_SCHEMA,sha256Bytes,
        validatePorterSummary,inspectApiResult,matchPublicFile}
        from '../static_workbench/web/receipt-verification-core.mjs';

globalThis.crypto ??= webcrypto;
const ident=(prefix,hex)=>prefix+':'+hex.repeat(64);
const canonical=x=>{
 if(x===null||typeof x==='string'||typeof x==='boolean'||typeof x==='number')return JSON.stringify(x);
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
};
const checks=['EXACT_CANNON_023_SOURCE_BYTES','GHOT_SIGNED_INSTRUMENT_PACKET',
 'ORIGINAL_RELATTE_R14_CROSSING','DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES',
 'ORIGINAL_RECEIVER_DURABLE_JOURNAL','PRIVATE_REPORT_EXACT_BINDING','NO_ADMIT_OR_OWNER_ACT'];
const publicReport=()=>({
 schema:'cannon.stack-squared-ai-relatte-public/v0',
 source_commit:GHOT_PIN,relatte_commit:RELATTE_PIN,
 ghot_report_id:ident('ai-recomposition-report-v0','a'),
 ghot_report_sha256:'1'.repeat(64),
 cannon_witness_id:ident('cannon-stack2-ai-witness-v0','b'),
 ghot_signed_execution_receipts:[ident('relatte-receipt-v0','2')],
 ghot_portable_packet_ids:[ident('portable-seed-v0','3')],
 relatte_crossing_id:ident('relatte-crossing-v0','4'),
 relatte_received_receipt_id:ident('relatte-receipt-v0','5'),
 relatte_hold_receipt_id:ident('relatte-receipt-v0','6'),
 destination:'R3_HOLD',original_ghot_donor_reexecuted:false,
 original_relatte_receiver_used:true,cold_signatures_verified:true,
 source_human_identity_established:false,receiver_admitted:false,
 external_effects:0,production_deployed:false
});
async function specimen(){
 const pub=publicReport(),bytes=new TextEncoder().encode(JSON.stringify(pub,null,2)+'\n');
 const body={
  schema:PORTER_SCHEMA,status:'LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED',
  verified_at:'2026-10-11T19:01:00Z',
  source_pins:{GHoT:GHOT_PIN,CANNON:CANNON_PIN,reLATTE:RELATTE_PIN},
  public_inspection_sha256:await sha256Bytes(bytes),
  public_canonical_sha256:await sha256Bytes(new TextEncoder().encode(canonical(pub))),
  ghot_report_id:pub.ghot_report_id,
  relatte_crossing_id:pub.relatte_crossing_id,
  relatte_received_receipt_id:pub.relatte_received_receipt_id,
  relatte_hold_receipt_id:pub.relatte_hold_receipt_id,
  checks,receiver_disposition:'R3_HOLD',
  receiver_admitted:false,human_identity_authenticated:false,
  operator_permission_inferred:false,browser_execution:false,
  signature_trust:'SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY'
 };
 const attestation_sha256=await sha256Bytes(new TextEncoder().encode(canonical(body)));
 return {pub,bytes,summary:{...body,attestation_sha256}};
}
test('fixed read-only API shape refuses nonlocal opaque fields',async()=>{
 const s=await specimen();
 assert.equal((await inspectApiResult({schema:API_SCHEMA,available:true,state:'AVAILABLE',summary:s.summary})).status,
  'LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED');
 assert.equal(await inspectApiResult({schema:API_SCHEMA,available:false,state:'NO_OPERATOR_VERIFICATION'}),null);
 assert.equal(await inspectApiResult({schema:API_SCHEMA,available:false,state:'INVALID_LOCAL_PORTER_ATTESTATION'}),null);
 await assert.rejects(inspectApiResult({schema:API_SCHEMA,available:false,state:'AVAILABLE'}));
 await assert.rejects(inspectApiResult({schema:API_SCHEMA,available:true,state:'AVAILABLE',summary:s.summary,
  private_text:'should never arrive'}));
});
test('original reported signatures are bound to exact public file bytes',async()=>{
 const s=await specimen();
 await validatePorterSummary(s.summary);
 const result=await matchPublicFile(s.summary,s.bytes);
 assert.equal(result.status,'PUBLIC_FILE_BOUND_TO_OPERATOR_NATIVE_VERIFICATION');
 assert.equal(result.original_signatures_checked_by_browser,false);
 assert.equal(result.owner_identity_established,false);
 assert.equal(result.receiver_admitted,false);
 assert.equal(result.browser_executed_native,false);
});
test('tampered public bytes, swapped receipt IDs, ADMITS all refuse',async()=>{
 const s=await specimen();
 const altered=new Uint8Array(s.bytes);altered[4]=altered[4]===32?10:32;
 await assert.rejects(matchPublicFile(s.summary,altered),/PUBLIC_FILE_BYTES_DIFFER/);
 const mod={...s.pub,relatte_hold_receipt_id:ident('relatte-receipt-v0','9')};
 await assert.rejects(matchPublicFile(s.summary,new TextEncoder().encode(JSON.stringify(mod))),
    /PUBLIC_FILE_BYTES_DIFFER/);
 await assert.rejects(matchPublicFile(s.summary,new Uint8Array()),/INVALID_PUBLIC_FILE_SIZE/);
 const wrong={...s.summary,receiver_admitted:true};
 await assert.rejects(validatePorterSummary(wrong),/AUTHORITY_OR_CHECK_PROMOTION/);
 await assert.rejects(validatePorterSummary({...s.summary,human_identity_authenticated:true}),
  /AUTHORITY_OR_CHECK_PROMOTION/);
 await assert.rejects(validatePorterSummary({...s.summary,source_pins:{...s.summary.source_pins,CANNON:'0'.repeat(40)}}),
  /BAD_SOURCE_PINS/);
 await assert.rejects(validatePorterSummary({...s.summary,attestation_sha256:'f'.repeat(64)}),
  /ALTERED_LOCAL_SUMMARY/);
 await assert.rejects(validatePorterSummary({...s.summary,private_report:mod}),
  /BAD_PORTER_FIELDS/);
});
