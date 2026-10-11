#!/usr/bin/env node
/** STACK² 021: original pinned reLATTE cryptography + receiver replay checker.
 * This verifies original native signatures. It cannot authenticate a human.
 */
import {readFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
const [mode,relattePath,receiverPath,requestPath,resultPath]=process.argv.slice(2);
const fail=(condition,code)=>{if(!condition)throw Error(code)};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
try{
  fail((mode==='receiver'&&process.argv.length===5)||
       (mode==='verify'&&process.argv.length===7),'INVALID_FIXED_VERIFICATION_ARGUMENTS');
  const root=resolve(relattePath),receiver=resolve(receiverPath);
  const r=await import(pathToFileURL(join(root,'src/index.ts')).href);
  const world=await r.LocalReceiver.open(receiver);
  const snap=world.snapshot();
  fail(snap.schema==='relatte.local-receiver-snapshot/v0','NOT_NATIVE_RECEIVER');
  if(mode==='receiver'){
    console.log(JSON.stringify({schema:'workbench.stack2-native-receiver-inspection/v0',
      world_id:world.config.world_id,receiver_particular:world.config.receiver_particular,
      contract_ref:world.config.contract_ref,state_ref:snap.state_ref,
      held_count:snap.held.length,admitted_count:snap.admitted.length}));
  }else{
    const req=JSON.parse(readFileSync(resolve(requestPath),'utf8'));
    const result=JSON.parse(readFileSync(resolve(resultPath),'utf8'));
    fail(req.schema==='relatte.opaque-roundtrip-request/v0'&&req.disposition==='HOLD',
      'NOT_NATIVE_HOLD_REQUEST');
    fail(result.schema==='relatte.opaque-roundtrip-result/v0'&&
      result.request_id===r.computeOpaqueRoundTripRequestId(req),'ROUNDTRIP_REQUEST_CHANGED');
    fail(await r.verifyOpaqueOrganCrossing(result.crossing),'INVALID_NATIVE_CROSSING_SIGNATURE');
    fail(await r.verifyReceipt(result.receive_receipt),'INVALID_NATIVE_RECEIVE_SIGNATURE');
    fail(await r.verifyReceipt(result.disposition_receipt),'INVALID_NATIVE_HOLD_SIGNATURE');
    fail(result.receive_receipt.kind==='RECEIVED'&&
      result.receive_receipt.semantic_effect==='none'&&
      result.disposition_receipt.kind==='R3_HOLD'&&
      result.disposition_receipt.semantic_effect==='none',
      'RECEIVER_DISPOSITION_NOT_HOLD');
    const id=result.crossing.crossing_id;
    fail(result.receive_receipt.crossing_id===id&&
      result.disposition_receipt.crossing_id===id&&
      snap.held.includes(id)&&!snap.admitted.includes(id),
      'SIGNED_RECEIPT_OR_RECEIVER_HOLD_NOT_BOUND');
    fail(same(result.crossing.extensions?.organ_adapter?.donor_claims,req.spec.donor_claims),
      'SIGNED_GHOT_DONOR_CLAIMS_MISMATCH');
    fail(result.crossing.source_history_head===req.spec.source_history_head&&
      same(result.crossing.payload_refs,req.spec.payload_refs)&&
      result.crossing.requested_effect?.kind==='candidate-ingress'&&
      result.crossing.requested_effect?.execution_authorized===false,
      'CROSSING_PROVENANCE_OR_AUTHORITY_CHANGED');
    fail(world.config.world_id===req.receiver.world_id&&
      world.config.receiver_particular===req.receiver.receiver_particular&&
      world.config.contract_ref===req.receiver.contract_ref,
      'RECEIVER_IDENTITY_MISMATCH');
    const transport=await r.readFileBundle(req.bundle_path);
    fail(transport.crossing.crossing_id===id,'TRANSPORT_FILE_CHANGED');
    console.log(JSON.stringify({schema:'workbench.stack2-021-native-cold-verification/v0',
      status:'CROSSING_RECEIVED_AND_HELD',crossing_id:id,
      receive_receipt_id:result.receive_receipt.receipt_id,
      hold_receipt_id:result.disposition_receipt.receipt_id,
      receiver_state_ref:snap.state_ref,receiver_world:world.config.world_id,
      signatures_cold_verified:3,receiver_admitted:false,
      owner_identity_authenticated:false}));
  }
}catch(e){
  process.stderr.write('HOLD: '+String(e.message).slice(0,230)+'\n');
  process.exitCode=1;
}
