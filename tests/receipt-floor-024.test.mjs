import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {GHOT_PIN,RELATTE_PIN,CI_RUN,SCHEMA,SOURCE,inspectPublicWitness,
        cardsFor,inspectParticular,traverse,makeUnsignedInspection}
        from '../static_workbench/web/receipt-floor-core.mjs';

globalThis.crypto ??= webcrypto;
const id=(prefix,c)=>prefix+':'+c.repeat(64);
function sample(n=1){
  const items={
    schema:SCHEMA,
    source_commit:GHOT_PIN,
    relatte_commit:RELATTE_PIN,
    ghot_report_id:id('ai-recomposition-report-v0','a'),
    ghot_report_sha256:'b'.repeat(64),
    cannon_witness_id:id('cannon-stack2-ai-witness-v0','c'),
    ghot_signed_execution_receipts:[id('relatte-receipt-v0','1')],
    ghot_portable_packet_ids:[id('portable-seed-v0','2')],
    relatte_crossing_id:id('relatte-crossing-v0','3'),
    relatte_received_receipt_id:id('relatte-receipt-v0','4'),
    relatte_hold_receipt_id:id('relatte-receipt-v0','5'),
    destination:'R3_HOLD',
    original_ghot_donor_reexecuted:false,
    original_relatte_receiver_used:true,
    cold_signatures_verified:true,
    source_human_identity_established:false,
    receiver_admitted:false,
    external_effects:0,
    production_deployed:false
  };
  if(n===2){
    items.ghot_signed_execution_receipts.push(id('relatte-receipt-v0','6'));
    items.ghot_portable_packet_ids.push(id('portable-seed-v0','7'));
  }
  return items;
}
function hostile(change,match,template=sample()){
  const altered=structuredClone(template);change(altered);
  assert.throws(()=>inspectPublicWitness(altered),match);
}
test('exact original source-addressed cards and honest verification level',()=>{
  const report=inspectPublicWitness(sample());
  assert.equal(SOURCE.length,3);
  assert.equal(SOURCE[0].commit,GHOT_PIN);
  assert.equal(SOURCE[2].commit,RELATTE_PIN);
  assert.match(CI_RUN,/actions\/runs\/38165140352/);
  assert.equal(report.structural,'MATCHED_KNOWN_CI_REPORT_SHAPE');
  assert.equal(report.signature_status,'FOREIGN_NATIVE_CI_CLAIM_NOT_BROWSER_VERIFIED');
  assert.equal(report.native_calls_by_browser,0);
});
test('one and two native processors create real distinct typed proposal cards',()=>{
  const a=cardsFor(sample()),b=cardsFor(sample(2));
  assert.equal(a.length,7);assert.equal(b.length,9);
  assert.deepEqual(a.map(x=>x.kind),[
    'processing','execution-receipt','packet','source-witness',
    'signed-crossing','received','hold'
  ]);
  assert.deepEqual(b.filter(x=>x.kind==='packet').length,2);
  assert.equal(a.at(-1).authority,'RECEIVER_LOCAL');
  assert.equal(a.at(-2).kind,'received');
  assert.notEqual(a.at(-2).id,a.at(-1).id);
  assert.equal(a.find(x=>x.kind==='source-witness').authority,'NONE');
});
test('aperture navigation never rewrites the historical chain',()=>{
  const s=sample();
  assert.equal(traverse(s).visible,7);
  assert.equal(traverse(s,'processing').visible,3);
  assert.equal(traverse(s,'crossing').visible,2);
  assert.equal(traverse(s,'receiver').visible,2);
  assert.deepEqual(traverse(s,'receiver').cards.map(x=>x.kind),['received','hold']);
  assert.equal(traverse(s,'receiver').cryptographic_verification,'NOT_PERFORMED');
  assert.throws(()=>traverse(s,'admit'),/INVALID_APERTURE/);
  assert.throws(()=>inspectParticular(s,'fake'),/UNKNOWN_RECEIPT/);
  const hold=inspectParticular(s,s.relatte_hold_receipt_id);
  assert.equal(hold.claimed_effect,'RECEIVER_LOCAL_HOLD');
  assert.equal(hold.verification,'IDENTIFIERS_AND_DECLARED_RELATIONS_ONLY');
  assert.equal(hold.browser_execution,false);
});
test('refuses cryptographic or authority overclaims in public witness',()=>{
  hostile(x=>{x.receiver_admitted=true},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.destination='R3_ADMIT'},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.original_ghot_donor_reexecuted=true},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.source_human_identity_established=true},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.external_effects=1},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.production_deployed=true},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.cold_signatures_verified=false},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.original_relatte_receiver_used=false},/AUTHORITY_OR_OUTCOME_OVERCLAIM/);
  hostile(x=>{x.source_commit='e'.repeat(40)},/SOURCE_PINS_DO_NOT_MATCH/);
  hostile(x=>{x.relatte_commit='f'.repeat(40)},/SOURCE_PINS_DO_NOT_MATCH/);
  hostile(x=>{x.signatures_in_browser_verified=true},/UNEXPECTED_OR_MISSING_PUBLIC_FIELDS/);
  hostile(x=>{delete x.ghot_report_sha256},/UNEXPECTED_OR_MISSING_PUBLIC_FIELDS/);
});
test('refuses broken IDs, mismatched packets and collapsed receipts',()=>{
  hostile(x=>{x.ghot_report_id='fake'},/INVALID_GHOT_REPORT_ID/);
  hostile(x=>{x.ghot_portable_packet_ids=[]},/INVALID_GHOT_PORTABLE_PACKET_IDS/);
  hostile(x=>{x.ghot_signed_execution_receipts.push(x.ghot_signed_execution_receipts[0])},
    /DUPLICATED_GHOT_SIGNED_EXECUTION_RECEIPTS/);
  hostile(x=>{x.ghot_signed_execution_receipts.push(id('relatte-receipt-v0','a'))},
    /PACKET_RECEIPT_CARDINALITY_MISMATCH/);
  hostile(x=>{x.relatte_received_receipt_id=x.relatte_hold_receipt_id},
    /RECEIVE_AND_HOLD_MUST_BE_DISTINCT/);
  hostile(x=>{x.relatte_crossing_id='relatte-crossing-v0:invented'},
    /INVALID_RELATTE_CROSSING_ID/);
});
test('human consent gates unsigned local packet with bounded relation claims',async()=>{
  const s=sample(2);
  await assert.rejects(makeUnsignedInspection(s),/EXPLICIT_LOCAL_INSPECTION_REQUIRED/);
  await assert.rejects(makeUnsignedInspection(s,{authorized:'yes'}),/EXPLICIT_LOCAL_INSPECTION_REQUIRED/);
  const packet=await makeUnsignedInspection(s,{authorized:true});
  assert.equal(packet.receipt_is_signed,false);
  assert.equal(packet.signature_verification,'NOT_PERFORMED');
  assert.equal(packet.git_source_verification,'NOT_PERFORMED');
  assert.equal(packet.receiver_journal_verification,'NOT_PERFORMED');
  assert.equal(packet.authority_granted,false);
  assert.equal(packet.browser_network,false);
  assert.equal(packet.browser_execution,false);
  assert.equal(packet.local_sha256.length,64);
  assert.deepEqual(packet.reported_portable_packets,s.ghot_portable_packet_ids);\n  assert.deepEqual(packet.reported_receiver_receipts,[s.relatte_received_receipt_id,s.relatte_hold_receipt_id]);
  assert.equal(packet.reported_crossing,s.relatte_crossing_id);
});
