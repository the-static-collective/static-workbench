"use strict";
// First-party Workbench browser-local trace. Never a secret vault or reLATTE receipt.
import {
  appendVoyageEvent, projectVoyage,
  parseVoyageExport, serializeVoyageExport,
} from './webz-voyage.mjs';

const KEY = 'webz.voyage-local.v0';
const SCHEMA = 'webz/voyage-local/v0';
const LAW = 'browser-local-observation';
const exact = (value, keys) => value !== null && typeof value === 'object' &&
  !Array.isArray(value) && Object.keys(value).length === keys.length &&
  keys.every((key) => Object.hasOwn(value, key));
const unavailable = {status:'unavailable',error:'Browser storage is unavailable. Navigation remains possible without recording.'};

function parseState(value) {
  const data=JSON.parse(value);
  if (!exact(data,['schema','initial_world_id','events','recording']) ||
      data.schema !== SCHEMA || typeof data.recording !== 'boolean') {
    throw new Error('The local voyage format is invalid');
  }
  // Use the same validation as portable, noncanonical voyage exports.
  parseVoyageExport(serializeVoyageExport(data.initial_world_id,data.events));
  return data;
}
export function readVoyage(storage) {
  let raw;
  try { raw=storage.getItem(KEY); }
  catch (_) { return {...unavailable}; }
  if (raw === null) return {status:'off',record:null,projection:null};
  try {
    const record=parseState(raw);
    return {
      status:record.recording?'recording':'paused',
      record,
      projection:projectVoyage(record.events,record.initial_world_id),
    };
  } catch (_) {
    return {status:'corrupt',error:'Saved voyage is corrupt. Export raw browser data before erasing; it was not overwritten.'};
  }
}
function save(storage,record) {
  try { storage.setItem(KEY,JSON.stringify(record)); }
  catch (_) { return {...unavailable}; }
  return readVoyage(storage);
}
export function beginRecording(storage,initial_world_id) {
  const prior=readVoyage(storage);
  if (prior.status!=='off') {
    return prior.status==='recording'||prior.status==='paused'
      ? {...prior,status:'conflict',error:'Erase or resume the existing voyage before beginning a new one.'}
      : prior;
  }
  try { projectVoyage([],initial_world_id); }
  catch (_) { return {status:'unresolved',error:'Unknown initial world.'}; }
  return save(storage,{schema:SCHEMA,initial_world_id,events:[],recording:true});
}
export function setRecording(storage,recording) {
  const prior=readVoyage(storage);
  if (!['recording','paused'].includes(prior.status)) return prior;
  if (typeof recording !== 'boolean') return {status:'unresolved',error:'Recording choice must be explicit.'};
  return save(storage,{...prior.record,recording});
}
export function recordDeparture(storage,from_world_id,to_world_id,door_id) {
  const prior=readVoyage(storage);
  if (prior.status!=='recording') return prior;
  const projection=prior.projection;
  if (projection.pending_departure_seq!==null) return {...prior,status:'pending'};
  if (projection.current_world_id!==from_world_id) {
    return {...prior,status:'unresolved',error:'Current world does not match the recorded voyage.'};
  }
  const events=prior.record.events;
  let updated;
  try {
    updated=appendVoyageEvent(events,{
      seq:events.length+1,kind:'departed',from_world_id,to_world_id,door_id,
      carry_mode:'none',authority:LAW,
    });
  } catch (_) { return {...prior,status:'unresolved',error:'Undeclared door; no departure recorded.'}; }
  return save(storage,{...prior.record,events:updated});
}
export function confirmArrival(storage,to_world_id) {
  const prior=readVoyage(storage);
  if (prior.status!=='recording') return prior;
  const seq=prior.projection.pending_departure_seq;
  if (seq===null) return prior; // idempotent on reload
  const source=prior.record.events.find((event)=>event.seq===seq);
  if (!source || source.to_world_id!==to_world_id) return {...prior,status:'pending'};
  let updated;
  try {
    updated=appendVoyageEvent(prior.record.events,{
      seq:prior.record.events.length+1,kind:'arrived',
      from_world_id:source.from_world_id,to_world_id:source.to_world_id,
      door_id:source.door_id,carry_mode:'none',authority:LAW,
      basis_departure_seq:source.seq,
    });
  } catch (_) {return {...prior,status:'corrupt',error:'Arrival was not appended; local history needs inspection.'};}
  return save(storage,{...prior.record,events:updated});
}
export function exportVoyage(storage) {
  const result=readVoyage(storage);
  if (!['recording','paused'].includes(result.status)) {
    throw new Error('No valid local voyage is available to export.');
  }
  return serializeVoyageExport(result.record.initial_world_id,result.record.events);
}
export function eraseVoyage(storage) {
  try { storage.removeItem(KEY); }
  catch (_) { return {...unavailable}; }
  return readVoyage(storage);
}
