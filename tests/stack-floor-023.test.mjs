import test from 'node:test';
import assert from 'node:assert/strict';
import {proposeMycelium,LENSES} from '../scripts/stack-floor-023-core.mjs';
const id=c=>'relatte-crossing-v0:'+c.repeat(64);
const address=c=>'sha256:'+c.repeat(64);
const base=(c,i)=>({
  crossing_id:id(c),status:'HOLD',owner_admitted:false,
  source_world:'world:other-'+c,source_particular:'particular:'+c,
  source_history_head:'sha256:'+c.repeat(64),
  source_family:'family:'+c,source_contract:'contract:'+c,
  declared_kind:'OPAQUE_ORGAN_ARTIFACT',
  declared_payload_addresses:[address(c)],receive_seq:i,
  received_at:'2026-10-11T12:00:00.000Z',
  held_at:'2026-10-11T12:00:01.000Z'
});
const a=base('a',1),b=base('b',2),c=base('c',4);
b.source_world=a.source_world;
b.source_particular=a.source_particular;
b.source_history_head=a.source_history_head;
b.source_contract=a.source_contract;
b.source_family=a.source_family;
b.declared_payload_addresses=[address('a'),address('b')];
const state='relatte-local-state-v0:'+ 'd'.repeat(64);
test('verified declared references generate only bounded, deterministic attributed proposals',()=>{
  const original=structuredClone([a,b,c]);
  const x=proposeMycelium(original,{stateRef:state});
  assert.equal(x.nodes.length,3);
  assert.equal(x.total_evidence_edges,1);
  assert.equal(x.edges.length,1);
  assert.equal(x.edges[0].source_crossing_id,id('a'));
  assert.equal(x.edges[0].target_crossing_id,id('b'));
  assert.deepEqual(x.edges[0].evidence.map(e=>e.kind).sort(),[
    'NEIGHBOR_RECEIVE_SEQUENCE',
    'SAME_DECLARED_ADAPTER_FAMILY',
    'SAME_DECLARED_DONOR_CONTRACT',
    'SAME_DECLARED_HISTORY_HEAD',
    'SAME_DECLARED_PAYLOAD_ADDRESS',
    'SAME_DECLARED_SOURCE_PARTICULAR',
    'SAME_DECLARED_SOURCE_WORLD'
  ].sort());
  assert.equal(x.all_connections_are_proposals,true);
  assert.equal(x.source_claims_independently_verified,false);
  assert.equal(x.source_bytes_compared,false);
  assert.equal(x.relationships_persisted,false);
  assert.equal(x.receiver_admission_authorized,false);
  assert.equal(x.edges[0].relation_asserted,false);
  assert.equal(x.edges[0].admission_authorized,false);
  assert.equal('declared_payload_addresses' in x.nodes[0],false);
  assert.deepEqual(original,[a,b,c],'pure engine must not rewrite any input');
  assert.deepEqual(proposeMycelium([c,b,a],{stateRef:state}),x);
  assert.deepEqual(LENSES,['origin','lineage','structure','content','arrival']);
});
test('same source metadata is not interpreted as permission, and isolated held records remain islands',()=>{
  const x=proposeMycelium([base('e',7),base('f',40)],{stateRef:state});
  assert.equal(x.total_evidence_edges,0);
  assert.equal(x.nodes.length,2);
  assert.equal(x.edges.length,0);
  assert.equal(x.receiver_disposition_unchanged,true);
});
test('exact address is a declared pointer, not verified bytes or matching donor semantics',()=>{
  const x=proposeMycelium([{...a,receive_seq:5},
    {...c,receive_seq:90,declared_payload_addresses:[address('a')] }],
    {stateRef:state});
  assert.deepEqual(x.edges[0].evidence.map(e=>e.kind),['SAME_DECLARED_PAYLOAD_ADDRESS']);
  assert.match(x.edges[0].evidence[0].meaning,/not fetched or compared/);
});
test('fail closed on forged status, duplicate identifier, invalid count, invalid provenance',()=>{
  assert.throws(()=>proposeMycelium([{...a,status:'ADMIT'}],{stateRef:state}),
    /UNVERIFIED_HELD_/);
  assert.throws(()=>proposeMycelium([{...a,owner_admitted:true}],{stateRef:state}),
    /UNVERIFIED_HELD_/);
  assert.throws(()=>proposeMycelium([a,a],{stateRef:state}),
    /UNVERIFIED_HELD_/);
  assert.throws(()=>proposeMycelium([a],{stateRef:''}),/INVALID_MY/);
  assert.throws(()=>proposeMycelium([{...a,crossing_id:'arbitrary'}],
    {stateRef:state}),/UNVERIFIED_HELD_/);
  assert.throws(()=>proposeMycelium([a],{stateRef:state,maxNodes:1000}),/INVALID_MY/);
});
test('node and thread budgets state truncation explicitly',()=>{
  const f=Array.from({length:10},(_,i)=>{
    const x=base(i.toString(16),i+1);
    x.source_world=a.source_world;
    x.source_family=a.source_family;
    return x;
  });
  const x=proposeMycelium(f,{stateRef:state,maxNodes:4,maxEdges:2});
  assert.equal(x.included_held,4);
  assert.equal(x.skipped_held,6);
  assert.equal(x.edges.length,2);
  assert.equal(x.edges_truncated,true);
  assert.equal(x.total_evidence_edges,6);
});
