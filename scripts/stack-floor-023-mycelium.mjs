#!/usr/bin/env node
/** STACK² 023 — native sovereign HOLD-only metadata graph read.
 * Not a generic graph scanner. Loads original pinned reLATTE R14 receiver;
 * repeats original signature checks; never invokes a disposition method.
 */
import {readFile,lstat} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {proposeMycelium} from './stack-floor-023-core.mjs';

const [relattePath,receiverPath]=process.argv.slice(2);
const insist=(condition,code)=>{if(!condition)throw Error(code)};
const crossingId=/^relatte-crossing-v0:[a-f0-9]{64}$/;
try{
  insist(process.argv.length===4,'FIXED_RECEIVER_ONLY_ARGUMENTS');
  const relatte=resolve(relattePath),root=resolve(receiverPath);
  const dir=await lstat(root),file=await lstat(join(root,'journal.jsonl'));
  insist(dir.isDirectory()&&!dir.isSymbolicLink()&&file.isFile()&&
    !file.isSymbolicLink()&&file.size<=4*1024*1024,'UNSAFE_MY CELIUM_RECEIVER'.replace(' ',''));
  const before=await readFile(join(root,'journal.jsonl'));
  const native=await import(pathToFileURL(join(relatte,'src/index.ts')).href);
  const receiver=await native.LocalReceiver.open(root);
  const snap=receiver.snapshot();
  insist(snap.schema==='relatte.local-receiver-snapshot/v0','RECEIVER_SNAPSHOT_INVALID');
  const after=await readFile(join(root,'journal.jsonl'));
  insist(before.equals(after),'RECEIVER_JOURNAL_CHANGED_DURING_READ');
  const events=before.toString('utf8').split('\n').filter(x=>x.trim()).map(x=>JSON.parse(x));
  insist(events.length===receiver.journalLength()&&events.length<=1000,
    'JOURNAL_EVENT_BOUNDS_CHANGED');
  insist(Array.isArray(snap.held)&&snap.held.length<=100,'HELD_SET_EXCEEDS_SAFE_BOUND');
  const receiveEvents=new Map();
  const holdEvents=new Map();
  let arrival=0;
  for(const ev of events){
    if(ev.event_type==='RECEIVE'){
      arrival++;
      insist(!receiveEvents.has(ev.crossing_id)&&ev.crossing?.crossing_id===ev.crossing_id,
        'DUPLICATE_OR_INVALID_RECEIVE');
      receiveEvents.set(ev.crossing_id,{event:ev,arrival});
    }else if(ev.event_type==='DISPOSITION'&&ev.receipt?.kind==='R3_HOLD'){
      insist(!holdEvents.has(ev.crossing_id),'DUPLICATE_HELD_EVENT');
      holdEvents.set(ev.crossing_id,ev);
    }
  }
  const records=[];
  for(const id of [...snap.held].sort()){
    insist(crossingId.test(id),'INVALID_HELD_CROSSING_ID');
    const receive=receiveEvents.get(id),held=holdEvents.get(id);
    insist(receive&&held&&receive.event.seq<held.seq,
      'HELD_CROSSING_WITHOUT_SIGNED_RECEIVE_AND_HOLD');
    const crossing=receive.event.crossing;
    const recvReceipt=receiver.getReceiveReceipt(id);
    const holdReceipt=receiver.getDispositionReceipt(id);
    insist(recvReceipt?.receipt_id===receive.event.receipt?.receipt_id&&
      holdReceipt?.receipt_id===held.receipt?.receipt_id&&
      recvReceipt?.kind==='RECEIVED'&&holdReceipt?.kind==='R3_HOLD'&&
      recvReceipt?.crossing_id===id&&holdReceipt?.crossing_id===id&&
      recvReceipt?.semantic_effect==='none'&&holdReceipt?.semantic_effect==='none',
      'RECEIVER_SIGNED_DISPOSITION_MISMATCH');
    insist(await native.verifyOpaqueOrganCrossing(crossing)&&
      await native.verifyReceipt(recvReceipt)&&await native.verifyReceipt(holdReceipt),
      'SIGNATURE_OR_OPAQUE_CROSSING_MISMATCH');
    const refs=crossing.payload_refs;
    insist(Array.isArray(refs)&&refs.length>0&&refs.length<=30&&
      refs.every(r=>typeof r.address==='string'&&r.address.length<512&&
        typeof r.role==='string'&&typeof r.media_type==='string'),
      'SOURCE_REF_BOUNDS_INVALID');
    const string=(v)=>typeof v==='string'&&v.length>0&&v.length<512?v:null;
    const family=string(crossing.extensions?.organ_adapter?.family_ref);
    const contract=string(crossing.extensions?.organ_adapter?.donor_contract_ref);
    const original={
      crossing_id:id,status:'HOLD',owner_admitted:false,
      source_world:string(crossing.source_world),
      source_particular:string(crossing.source_particular),
      source_history_head:string(crossing.source_history_head),
      source_family:family,source_contract:contract,
      declared_kind:string(crossing.declared_kind),
      declared_payload_addresses:[...new Set(refs.map(x=>x.address))].sort(),
      receive_seq:receive.arrival,
      received_at:recvReceipt.created_at,
      held_at:holdReceipt.created_at,
      receive_receipt_id:recvReceipt.receipt_id,
      hold_receipt_id:holdReceipt.receipt_id,
    };
    insist(original.source_world&&original.source_particular&&
      original.declared_kind,'MISSING_SOURCE_LABEL');
    records.push(original);
  }
  const proposals=proposeMycelium(records,{stateRef:snap.state_ref,maxNodes:60,maxEdges:360});
  console.log(JSON.stringify({
    ...proposals,
    receiver_world:snap.world_id,
    receiver_particular:snap.receiver_particular,
    receiver_journal_head:snap.history_head,
    journal_events:receiver.journalLength(),
    original_receiver_journal_replayed:true,
    native_relatte_signatures_cold_verified:true,
    native_ghot_receipts_reverified:false,
    payload_bytes_read:false,
    private_keys_exported:false,
    write_operations:0,
    admission_operations:0
  }));
}catch(error){
  console.error('MYCELIUM_HOLD: '+String(error?.message??error).slice(0,200));
  process.exitCode=2;
}
