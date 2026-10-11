import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {CARDS,REQUIRED,inspectFloor,addCard,removeCard,inspectSummary,inspectNativeOutput,runLocalTrial} from '../static_workbench/web/stack-floor-core.mjs';

globalThis.crypto ??= webcrypto;
const h=s=>createHash('sha256').update(s).digest('hex');
const canonical=x=>{
  if(x===null||typeof x==='string'||typeof x==='boolean'||typeof x==='number')return JSON.stringify(x);
  if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
  return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
};
function specimen(){
  const ids=['PLZ-TRANCH-ROOM-001','PLZ-HUMAN-SUPABARDO-001'];
  const native={
    schema:'static-collective/planz-global-sense-run/v0',
    inputs:{seedPath:'/tmp/stack2/native-planz-seed.jsonl',provisionalPath:'/tmp/stack2/native-planz-provisional.jsonl',
      seedRecords:1,provisionalRecords:1},dedupedRecordCount:2,
    signalCounts:{gap:2,stranding:1,lineage:0,ambiguity:1,recoverability:2,compositionPressure:0},
    chamberCounts:{REANIMATE:2},repositoryCounts:{},
    frames:ids.map(planId=>({schema:'static-collective/planz-sense-frame/v0',planId,
      signals:{},basisRefs:[],authority:'none',selection:'NONE'})),
    unaryCandidates:ids.map((planId,i)=>({
      schema:'static-collective/planz-mutation-candidate/v0',
      candidateId:'mut-'+(i?'2222222222222222':'1111111111111111'),
      chamber:'REANIMATE',sourcePlanIds:[planId],hinge:null,proposal:'Synthetic only',
      residuals:['candidate-not-selected'],authority:'none',selection:'NONE'})),
    authority:'none',selection:'NONE',semanticSha256:'0'.repeat(64)};
  const commit=h(canonical(native));
  const summary={
    schema:'cannon.stack-squared-native-summary/v0',
    source_records:ids,source_count:2,original_git_witnesses:5,
    native_planz_run:true,native_planz_frame_count:2,
    native_planz_proposals:native.unaryCandidates.map(x=>({
      id:x.candidateId,chamber:x.chamber,sourcePlanIds:x.sourcePlanIds,
      authority:'none',selection:'NONE'})),
    native_ghot_local_system_hash:true,ghot_result_sha256:h(commit),
    ghot_receipt_sha256:'a'.repeat(64),
    native_relatte_signed_crossing_id:'relatte-crossing-v0:synthetic-long-id',
    native_relatte_receive_receipt_id:'relatte-receipt-v0:synthetic-receive',
    native_relatte_hold_receipt_id:'relatte-receipt-v0:synthetic-hold',
    signed_objects_cold_verified:3,disposition:'HOLD',receiver_admitted:false,
    external_effects:0,donor_mutations:0,git_merges:0,production_deployed:false};
  return {native,summary};
}
test('source-pinned five actual catalog cards, one explicitly incompatible fixture',()=>{
  assert.equal(CARDS.length,5);
  assert.deepEqual(CARDS.slice(0,4).map(x=>x.id),REQUIRED);
  assert(CARDS.every(x=>/^[a-f0-9]{40}$/.test(x.commit)));
  assert.equal(CARDS[4].id,'fixture');
  assert.equal(CARDS[4].input,'cannon.stack2.synthetic/v0');
});
test('tap-to-place, remove, typed sockets, no duplicate or inferred authority',()=>{
  let a=[null,null,null,null];
  for(let i=0;i<4;i++)a=addCard(a,REQUIRED[i],i).slots;
  const ready=inspectFloor(a);
  assert(ready.connected);
  assert.equal(ready.operational_authority,'NONE');
  assert.equal(ready.native_execution,false);
  assert(ready.links.every(x=>x.status==='FITS'));
  assert.throws(()=>addCard(a,'cannon',0),/DUPLICATE_BRICK/);
  assert.throws(()=>addCard(a,'bad-id',1),/UNKNOWN_BRICK/);
  assert.throws(()=>inspectFloor(['cannon','cannon',null,null]),/DUPLICATE_BRICK/);
  const emptied=removeCard(a,2);assert(!emptied.connected);
  const occupied=addCard(emptied.slots,'fixture',2);
  assert.equal(occupied.connected,false);
  assert.equal(occupied.links[2].status,'HOLD');
});
test('public CI claims are untrusted: refuse implicit ADMIT, change of plan IDs and signature exaggeration',()=>{
  const {summary}=specimen();
  assert.equal(inspectSummary(summary).signature_verification,'NOT_REVERIFIED_IN_BROWSER');
  const mutate=fn=>{
    const s=structuredClone(summary);fn(s);
    assert.throws(()=>inspectSummary(s));
  };
  mutate(s=>s.receiver_admitted=true);
  mutate(s=>s.disposition='ADMIT');
  mutate(s=>s.external_effects=1);
  mutate(s=>s.source_records.reverse());
  mutate(s=>s.native_planz_proposals[0].selection='SELECTED');
  mutate(s=>s.ghot_result_sha256='invalid');
});
test('human gate + WebCrypto replay of native planZ to reported GHoT hash',async()=>{
  const {summary,native}=specimen();
  inspectNativeOutput(native,summary);
  await assert.rejects(runLocalTrial(REQUIRED,summary,native),/EXPLICIT_AUTHORIZATION/);
  await assert.rejects(runLocalTrial(['fixture','planz','ghot','relatte'],summary,native,{authorized:true}),
    /STACK_SOCKETS_NOT_CONNECTED/);
  const result=await runLocalTrial(REQUIRED,summary,native,{authorized:true});
  assert.equal(result.browser_result,'HASH_RELATION_VERIFIED_FOREIGN_SIGNATURES_NOT_REVERIFIED');
  assert.equal(result.local_execution,'WEBCRYPTO_SHA256_ONLY');
  assert.equal(result.receipt_is_signed,false);
  assert.equal(result.native_donor_executions,0);
  assert.equal(result.authority_granted,false);
  assert.equal(result.packet_sha256.length,64);
  assert.deepEqual(result.recipe_cards.map(x=>x.id),REQUIRED);
  assert.equal(result.observed_ghot_output_sha256,summary.ghot_result_sha256);
});
test('reject changed native contents, forged selection and corrupted public result hash',async()=>{
  const {summary,native}=specimen();
  const altered=structuredClone(native);altered.signalCounts.gap=99;
  await assert.rejects(runLocalTrial(REQUIRED,summary,altered,{authorized:true}),/NATIVE_OUTPUT_GHOT_HASH_MISMATCH/);
  const promoted=structuredClone(native);promoted.frames[0].authority='owner';
  assert.throws(()=>inspectNativeOutput(promoted,summary),/SENSE_AUTHORITY/);
  const broken=structuredClone(summary);broken.ghot_result_sha256='f'.repeat(64);
  await assert.rejects(runLocalTrial(REQUIRED,broken,native,{authorized:true}),/NATIVE_OUTPUT_GHOT_HASH_MISMATCH/);
  const forged=structuredClone(native);forged.unaryCandidates[0].candidateId='mut-other';
  assert.throws(()=>inspectNativeOutput(forged,summary),/MUTATION_CANDIDATE_MISMATCH/);
});
