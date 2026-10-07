import test from 'node:test';
import assert from 'node:assert/strict';
import {
  appendVoyageEvent, projectVoyage, canonicalVoyageProjection,
  parseVoyageExport, serializeVoyageExport,
} from '../static_workbench/web/webz-voyage.mjs';

const A = 'webz:the-static-collective/sanctuary';
const B = 'webz:the-static-collective/orchard-022100';
const LAW = 'browser-local-observation';
const base = (seq, kind, from_world_id, to_world_id, door_id) => ({
  seq, kind, from_world_id, to_world_id, door_id,
  carry_mode:'none', authority:LAW,
});
const depart = (seq, from, to, door) => base(seq, 'departed', from, to, door);
const arrive = (seq, from, to, door, parent) => ({
  ...base(seq,'arrived',from,to,door), basis_departure_seq:parent,
});
const d1 = depart(1,A,B,'sanctuary-to-orchard');
const a2 = arrive(2,A,B,'sanctuary-to-orchard',1);
const d3 = depart(3,B,A,'orchard-to-sanctuary');
const a4 = arrive(4,B,A,'orchard-to-sanctuary',3);

// A test created before the module must be RED: Module not found.
test('four crossing events reconstruct Sanctuary Orchard Sanctuary', () => {
  const events = [d1,a2,d3,a4];
  const p = projectVoyage(events,A);
  assert.deepEqual(p.visits, [A,B,A]);
  assert.equal(p.current_world_id,A);
  assert.equal(p.pending_departure_seq,null);
  const one = canonicalVoyageProjection(events,A);
  assert.equal(one,canonicalVoyageProjection(structuredClone(events),A));
  assert.equal(one, JSON.stringify(p));
});

test('append preserves ancestry without mutating input', () => {
  const original=[d1];
  const result=appendVoyageEvent(original,a2);
  assert.deepEqual(original,[d1]);
  assert.deepEqual(result,[d1,a2]);
  result[0].door_id='changed';
  assert.equal(original[0].door_id,'sanctuary-to-orchard');
});

test('duplicate arrival or wrong door refuses', () => {
  assert.throws(() => projectVoyage([d1,a2,arrive(3,A,B,'sanctuary-to-orchard',1)],A));
  assert.throws(() => projectVoyage([d1,arrive(2,A,B,'wrong-door',1)],A));
  assert.throws(() => projectVoyage([d1,arrive(2,A,A,'sanctuary-to-orchard',1)],A));
});

test('out-of-order arrival and invented departure refuse', () => {
  assert.throws(() => projectVoyage([a2],A));
  assert.throws(() => projectVoyage([depart(2,A,B,'sanctuary-to-orchard')],A));
  assert.throws(() => projectVoyage([depart(1,B,A,'orchard-to-sanctuary')],A));
  assert.throws(() => projectVoyage([d1,depart(2,A,B,'sanctuary-to-orchard')],A));
});

test('unmatched departure remains pending rather than fabricated arrival', () => {
  const p=projectVoyage([d1],A);
  assert.deepEqual(p.visits,[A]);
  assert.equal(p.current_world_id,A);
  assert.equal(p.pending_departure_seq,1);
});

test('exact local voyage JSON export cold replays and retains scope', () => {
  const events=[d1,a2,d3,a4];
  const serialized=serializeVoyageExport(A,events);
  assert.deepEqual(parseVoyageExport(serialized),{initial_world_id:A,events});
  assert.equal(serialized,serializeVoyageExport(A,parseVoyageExport(serialized).events));
  assert.equal(canonicalVoyageProjection(events,A),
    canonicalVoyageProjection(parseVoyageExport(serialized).events,A));
  assert.equal(JSON.parse(serialized).schema,'webz/voyage-local/v0');
});

test('truncated malformed export, unknown schema, and extra metadata refuse', () => {
  for(const text of ['{', 'null', '[]', '{}', '"hi"',
    JSON.stringify({schema:'webz/voyage-local/v99',initial_world_id:A,events:[]}),
    JSON.stringify({schema:'webz/voyage-local/v0',initial_world_id:A,events:[],private_note:'secret'}),
  ]) assert.throws(() => parseVoyageExport(text));
});

test('sensitive notes and foreign event fields never enter the local log', () => {
  assert.throws(() => appendVoyageEvent([], {...d1,private_note:'secret'}));
  assert.throws(() => appendVoyageEvent([], {...d1,carry_mode:'all'}));
  assert.throws(() => appendVoyageEvent([], {...d1,authority:'relatte-signed'}));
  assert.throws(() => appendVoyageEvent([],{...a2}));
  assert.throws(() => projectVoyage([], 'not-a-world'));
});
