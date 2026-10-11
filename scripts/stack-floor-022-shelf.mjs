#!/usr/bin/env node
/** STACK² 022 — receiver-only, read-only HOLD shelf.
 * Loads original pinned reLATTE LocalReceiver and cold replays its signed journal.
 * No admission, payload reading, signer export, or donor claim promotion.
 */
import {readFile, lstat} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [mode, relattePath, receiverPath, crossingId] = process.argv.slice(2);
const refuse=(ok,code)=>{if(!ok)throw Error(code);};
const crossingPattern=/^relatte-crossing-v0:[a-f0-9]{64}$/;
const exact=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
try{
  refuse((mode==='list'&&process.argv.length===5)||
         (mode==='detail'&&process.argv.length===6&&crossingPattern.test(crossingId)),
         'UNSUPPORTED_SHELF_OPERATION');
  const relatte=resolve(relattePath),root=resolve(receiverPath);
  const receiverDir=await lstat(root);
  refuse(receiverDir.isDirectory()&&!receiverDir.isSymbolicLink(),'UNSAFE_RECEIVER_ROOT');
  const native=await import(pathToFileURL(join(relatte,'src/index.ts')).href);
  // Original R14 verifies all journal event hashes, receipt signatures,
  // source crossing signatures and receiver sequence before returning.
  const receiver=await native.LocalReceiver.open(root);
  const snapshot=receiver.snapshot();
  refuse(snapshot.schema==='relatte.local-receiver-snapshot/v0',
         'INVALID_NATIVE_RECEIVER_SNAPSHOT');
  const journalFile=join(root,'journal.jsonl');
  const meta=await lstat(journalFile);
  refuse(meta.isFile()&&!meta.isSymbolicLink()&&meta.size<=4*1024*1024,
         'SHELF_JOURNAL_TOO_LARGE_OR_UNSAFE');
  const journalText=await readFile(journalFile,'utf8');
  const lines=journalText.split('\n').filter(line=>line.trim());
  refuse(lines.length===receiver.journalLength()&&lines.length<=1000,
         'SHELF_JOURNAL_COUNT_CHANGED');
  const receiveMap=new Map(), holdMap=new Map();
  for(const line of lines){
    const event=JSON.parse(line);
    if(event.event_type==='RECEIVE'){
      refuse(event.crossing&&event.crossing.crossing_id===event.crossing_id,
             'INVALID_SHELF_CROSSING_EVENT');
      refuse(!receiveMap.has(event.crossing_id),'DUPLICATE_SHELF_RECEIVE');
      receiveMap.set(event.crossing_id,event);
    }
    if(event.event_type==='DISPOSITION'&&event.receipt?.kind==='R3_HOLD'){
      refuse(!holdMap.has(event.crossing_id),'DUPLICATE_SHELF_HOLD');
      holdMap.set(event.crossing_id,event);
    }
  }
  const ids=[...snapshot.held].sort();
  refuse(ids.length<=100&&ids.every(id=>crossingPattern.test(id)),
         'SHELF_INVALID_HELD_ITEM_COUNT');
  const records=[];
  for(const id of ids){
    const received=receiveMap.get(id),held=holdMap.get(id);
    refuse(received&&held&&received.seq<held.seq,'SHELF_MISSING_HOLD_HISTORY');
    const crossing=received.crossing;
    const recv=receiver.getReceiveReceipt(id);
    const hold=receiver.getDispositionReceipt(id);
    refuse(recv&&hold&&recv.kind==='RECEIVED'&&hold.kind==='R3_HOLD'&&
      recv.semantic_effect==='none'&&hold.semantic_effect==='none'&&
      recv.receipt_id===received.receipt.receipt_id&&
      hold.receipt_id===held.receipt.receipt_id&&
      recv.crossing_id===id&&hold.crossing_id===id,
      'SHELF_RECEIPT_STATE_MISMATCH');
    refuse(await native.verifyOpaqueOrganCrossing(crossing)&&
      await native.verifyReceipt(recv)&&await native.verifyReceipt(hold),
      'SHELF_INVALID_SIGNED_HISTORY');
    const original=Array.isArray(crossing.payload_refs)?crossing.payload_refs:[];
    refuse(original.length>0&&original.length<=30&&
       original.every(ref=>typeof ref.address==='string'&&
         typeof ref.role==='string'&&typeof ref.media_type==='string'),
       'SHELF_INVALID_SOURCE_REFS');
    const record={
      crossing_id:id,status:'HOLD',declared_kind:crossing.declared_kind,
      received_at:recv.created_at,held_at:hold.created_at,
      source_world:crossing.source_world,
      source_particular:crossing.source_particular,
      source_history_head:crossing.source_history_head,
      receive_receipt_id:recv.receipt_id,hold_receipt_id:hold.receipt_id,
      source_payload_count:original.length,
      signature_status:'NATIVE_RELATTE_VALIDATED',
      donor_proof:'NOT_REVERIFIED_BY_SHELF',
      semantic_effect:'none',
      owner_admitted:false,
    };
    if(mode==='detail'&&id===crossingId){
      record.payload_refs=original.map(({role,address,media_type})=>
        ({role,address,media_type}));
      record.requested_effect=crossing.requested_effect;
      record.source_contract=crossing.extensions?.organ_adapter?.donor_contract_ref??null;
      record.source_family=crossing.extensions?.organ_adapter?.family_ref??null;
      record.crossing_sender_signer_particular=crossing.signing?.public_key
        ? crossing.source_particular:null;
      record.receiver_world=receiver.config.world_id;
      record.receiver_particular=receiver.config.receiver_particular;
      record.receiver_contract_ref=receiver.config.contract_ref;
      record.receive_pre_state_ref=recv.pre_state_ref;
      record.receive_post_state_ref=recv.post_state_ref;
      record.hold_pre_state_ref=hold.pre_state_ref;
      record.hold_post_state_ref=hold.post_state_ref;
      record.custody_receipt_present=!!receiver.getPayloadCustodyReceipt(id);
      record.disposition_note=hold.note;
    }
    records.push(record);
  }
  const output={
    schema:'workbench.stack-squared-022-shelf/v0',
    mode,world_id:receiver.config.world_id,
    receiver_particular:receiver.config.receiver_particular,
    state_ref:snapshot.state_ref,
    history_head:snapshot.history_head,
    journal_events:receiver.journalLength(),
    counts:{held:ids.length,admitted:snapshot.admitted.length,
      refused:snapshot.refused.length,returned:snapshot.returned.length},
    records:mode==='list'?records:records.filter(x=>x.crossing_id===crossingId),
    original_receiver_journal_replayed:true,
    original_relatte_signatures_verified:true,
    original_ghot_signature_reverified:false,
    receiver_admission_authorized:false,
    payload_bytes_read:false,
    private_keys_exported:false,
    mutations_performed:false,
  };
  if(mode==='detail')refuse(output.records.length===1,'SHELF_ITEM_NOT_HELD');
  console.log(JSON.stringify(output));
}catch(error){
  console.error('SHELF_HOLD: '+String(error?.message??error).slice(0,160));
  process.exitCode=2;
}
