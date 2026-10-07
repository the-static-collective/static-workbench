import test from 'node:test';
import assert from 'node:assert/strict';
import {
  readVoyage, beginRecording, recordDeparture, confirmArrival,
  setRecording, exportVoyage, eraseVoyage,
} from '../static_workbench/web/webz-storage.mjs';

const A='webz:the-static-collective/sanctuary';
const B='webz:the-static-collective/orchard-022100';
const KEY='webz.voyage-local.v0';
class MemoryStorage {
  data = new Map();
  getItem(key) { return this.data.get(key) ?? null; }
  setItem(key, value) { this.data.set(key,String(value)); }
  removeItem(key) { this.data.delete(key); }
}

const outbound=(storage)=>recordDeparture(storage,A,B,'sanctuary-to-orchard');
const inbound=(storage)=>recordDeparture(storage,B,A,'orchard-to-sanctuary');

test('recording is off by default and nothing is persisted by reading', () => {
  const storage=new MemoryStorage();
  assert.equal(readVoyage(storage).status,'off');
  assert.equal(storage.data.size,0);
  assert.equal(outbound(storage).status,'off');
  assert.equal(storage.data.size,0);
});

test('only an explicit begin enables local recording', () => {
  const storage=new MemoryStorage();
  assert.equal(beginRecording(storage,A).status,'recording');
  assert.equal(JSON.parse(storage.getItem(KEY)).initial_world_id,A);
  assert.equal(beginRecording(storage,A).status,'conflict');
  assert.equal(readVoyage(storage).projection.visits.length,1);
});

test('crossing and browser reload remain one departure and arrival', () => {
  const storage=new MemoryStorage();
  beginRecording(storage,A);
  assert.equal(outbound(storage).projection.pending_departure_seq,1);
  assert.equal(outbound(storage).status,'pending');
  assert.equal(readVoyage(storage).record.events.length,1);
  assert.equal(confirmArrival(storage,B).projection.visits.length,2);
  assert.equal(confirmArrival(storage,B).record.events.length,2);
  assert.equal(inbound(storage).projection.pending_departure_seq,3);
  assert.deepEqual(confirmArrival(storage,A).projection.visits,[A,B,A]);
  assert.equal(readVoyage(storage).record.events.length,4);
});

test('a mismatched destination never fabricates an arrival', () => {
  const storage=new MemoryStorage();
  beginRecording(storage,A);
  outbound(storage);
  assert.equal(confirmArrival(storage,A).status,'pending');
  assert.equal(readVoyage(storage).record.events.length,1);
});

test('pausing recording refuses to append and can resume without erasing', () => {
  const storage=new MemoryStorage();
  beginRecording(storage,A);
  assert.equal(setRecording(storage,false).status,'paused');
  assert.equal(outbound(storage).status,'paused');
  assert.equal(setRecording(storage,true).status,'recording');
  assert.equal(outbound(storage).record.events.length,1);
});

test('export is deterministic, excludes recording preferences, and erase is explicit', () => {
  const storage=new MemoryStorage();
  beginRecording(storage,A);
  outbound(storage);
  confirmArrival(storage,B);
  const a=exportVoyage(storage);
  assert.equal(a,exportVoyage(storage));
  assert.deepEqual(Object.keys(JSON.parse(a)),['schema','initial_world_id','events']);
  assert.ok(!a.includes('human_name'));
  assert.equal(eraseVoyage(storage).status,'off');
  assert.equal(storage.getItem(KEY),null);
});

test('corrupt storage never resets silently', () => {
  const storage=new MemoryStorage();
  storage.setItem(KEY,'{broken');
  assert.equal(readVoyage(storage).status,'corrupt');
  assert.equal(beginRecording(storage,A).status,'corrupt');
  assert.equal(storage.getItem(KEY),'{broken');
  assert.throws(() => exportVoyage(storage));
});

test('blocked localStorage yields visible unavailable status, not a crash', () => {
  const blocked={getItem(){throw new Error('denied');},setItem(){throw new Error('denied');},removeItem(){throw new Error('denied');}};
  assert.equal(readVoyage(blocked).status,'unavailable');
  assert.equal(beginRecording(blocked,A).status,'unavailable');
  assert.equal(outbound(blocked).status,'unavailable');
  assert.equal(eraseVoyage(blocked).status,'unavailable');
});
