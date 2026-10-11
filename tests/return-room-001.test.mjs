import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {inspectDocket,lensDetails,nextReaderPacket,LENSES,canonical} from '../static_workbench/web/return-room-core.mjs';

const staticRoot=resolve(process.env.STATIC_OS_SRC||'.deps/static-os');
const relatte=resolve(process.env.RELATTE_SRC||'.deps/reLATTE');
const national=resolve(process.env.NATIONAL_TREASURE_SRC||'.deps/national-treasure');
const {makeSyntheticDonor}=await import(pathToFileURL(join(staticRoot,'return_room/synthetic-donor.mjs')).href);
const {startDocket,replayDocket,donorModules}=await import(pathToFileURL(join(staticRoot,'return_room/room.mjs')).href);
async function useRealDocket(fn){
 const temp=await mkdtemp(join(tmpdir(),'wb-return-room-'));
 try{
  const {paths,modules,input}=await makeSyntheticDonor(temp,relatte,national);
  const out=join(temp,'docket');
  const session=await startDocket({paths,outputDir:out,reviewer:'local-test-operator',
   selected:true,at:'2026-10-11T14:06:00.000Z',modules});
  const checkpoint=JSON.parse(await readFile(join(out,'checkpoint.json'),'utf8'));
  const replay=await replayDocket({paths,outputDir:out,modules});
  await fn({session,checkpoint,replay,paths,temp,input});
 }finally{await rm(temp,{recursive:true,force:true});}
}
test('actual Static OS signed reLATTE and Question Box session is digest-checkable by Workbench',()=>useRealDocket(async({session,checkpoint,replay})=>{
 const checked=await inspectDocket(session,checkpoint,replay);
 assert.equal(checked.status,'LOCAL_SESSION_ADDRESS_CHECKED');
 assert.equal(checked.native_signatures,'NOT_REVERIFIED_IN_BROWSER');
 assert.equal(checked.source_files,'NOT_REOPENED_IN_BROWSER');
 assert.equal(checked.native_replay,'CLAIMED_BY_IMPORTED_REPLAY_FILE');
 assert.equal(checked.checkpoint,'STRUCTURALLY_BOUND');
 assert.equal(checked.next_turn,'NOT_AUTHORIZED');
 assert.equal(LENSES.length,11);
 for(const lens of LENSES){const values=lensDetails(session,lens.id);assert.ok(values.length>=2);}
 const handoff=nextReaderPacket(session);
 assert.equal(handoff.next_action,'NEW_HUMAN_SELECTION_REQUIRED');
 assert.equal(handoff.native_receipt_verification,'REQUIRED_AT_RECEIVING_WORLD');
 assert.equal(handoff.support_confidence,'unsupported');
 assert.equal(handoff.admission,'none');
 assert.equal(handoff.question,session.inspection.question);
 assert.equal(Object.hasOwn(handoff,'source_file'),false);
 assert.ok(!JSON.stringify(handoff).includes('synthetic-reader'));
}));
test('locally rehashed but forged authority and extra fields are refused',()=>useRealDocket(async({session})=>{
 const tamper=async mutate=>{
  const copy=structuredClone(session);mutate(copy);
  const {session_id,...fields}=copy;
  const bytes=canonical(fields);
  const hex=Buffer.from(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(bytes))).toString('hex');
  copy.session_id='sha256:'+hex;
  await assert.rejects(inspectDocket(copy));
 };
 for(const change of [
  x=>x.inspection.admission='ADMIT',
  x=>x.inspection.receiver_signatures_verified=0,
  x=>x.inspection.question_aperture='answer',
  x=>x.inspection.original_source_ancestry='ESTABLISHED',
  x=>x.inspection.claimed_human_observer='VERIFIED',
  x=>x.inspection.automatic_execution=true,
  x=>x.inspection.next_turn='AUTHORIZED',
  x=>x.writes_to_source_worlds=true,
  x=>x.operator_selected=false,
  x=>x.inspection.publish_private_source=true,
  x=>x.unresolved_questions=['We already know.']
 ])await tamper(change);
}));
test('session digest, checkpoint binding and independent replay metadata cannot be silently altered',()=>useRealDocket(async({session,checkpoint,replay})=>{
 const bad=structuredClone(session);
 bad.inspection.question+=' and invented detail';
 await assert.rejects(inspectDocket(bad),/QUESTION_DRIFT|SESSION_ADDRESS_CHANGED/);
 const c=structuredClone(checkpoint);c.input_fingerprints.carrier='sha256:'+'a'.repeat(64);
 await assert.rejects(inspectDocket(session,c),/CHECKPOINT_SOURCE_DRIFT/);
 const r=structuredClone(replay);r.executed_again=true;
 await assert.rejects(inspectDocket(session,checkpoint,r),/REPLAY_DRIFT/);
 assert.equal((await inspectDocket(session)).checkpoint,'NOT_IMPORTED');
}));
test('unknown dials and false next-reader proofs do not gain authority',()=>useRealDocket(async({session})=>{
 assert.throws(()=>lensDetails(session,'execute'),/UNKNOWN_DIAL/);
 const next=nextReaderPacket(session);
 for(const key of ['signature','admitted','operator_approved','original_source','power_grant']){
  assert.equal(Object.hasOwn(next,key),false);
 }
}));
