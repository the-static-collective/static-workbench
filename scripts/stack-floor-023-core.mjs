/** STACK² 023 — pure, bounded, explainable relation *proposals*.
 * Input consists exclusively of fields from verified native reLATTE HOLD history.
 * Equality of declared evidence is not an asserted causal or semantic relation.
 */
import {createHash} from 'node:crypto';
export const LENSES=['origin','lineage','structure','content','arrival'];
const safe=(x)=>typeof x==='string'&&x.length>0;
const hex=values=>'proposal-023:'+createHash('sha256').update(
  'stack-squared-023-mycelium-proposal-v0|'+JSON.stringify(values)).digest('hex');
const match=(value,a,b)=>safe(a[value])&&a[value]===b[value];
const evidence=(lens,kind,value,meaning)=>({lens,kind,value,meaning});
const sharedAddresses=(a,b)=>{
  const left=new Set(a.declared_payload_addresses||[]);
  return [...new Set(b.declared_payload_addresses||[])].filter(x=>left.has(x)).sort();
};
export function proposeMycelium(records,{stateRef,maxNodes=60,maxEdges=360}={}){
  if(!Array.isArray(records)||records.length>100||
    !safe(stateRef)||!Number.isInteger(maxNodes)||maxNodes<1||maxNodes>100||
    !Number.isInteger(maxEdges)||maxEdges<0||maxEdges>1000)
    throw Error('INVALID_MY CELIUM_INPUT'.replace(' ',''));
  const ordered=[...records].sort((a,b)=>a.crossing_id.localeCompare(b.crossing_id));
  if(ordered.some((r,i)=>!/^relatte-crossing-v0:[a-f0-9]{64}$/.test(r.crossing_id)||
     (i>0&&r.crossing_id===ordered[i-1].crossing_id)||
     r.status!=='HOLD'||r.owner_admitted!==false||
     !Number.isInteger(r.receive_seq)||r.receive_seq<1||
     !Array.isArray(r.declared_payload_addresses)||
     r.declared_payload_addresses.length>30||
     r.declared_payload_addresses.some(x=>!safe(x))))
    throw Error('UNVERIFIED_HELD_MY CELIUM_RECORD'.replace(' ',''));
  // Cap the number of particulars rather than silently overpromising display.
  const nodes=ordered.slice(0,maxNodes);
  const edges=[];
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
    const a=nodes[i],b=nodes[j],facts=[];
    if(match('source_world',a,b))
      facts.push(evidence('origin','SAME_DECLARED_SOURCE_WORLD',a.source_world,
        'Both signed envelopes name the same source world; this does not prove common ownership.'));
    if(match('source_particular',a,b))
      facts.push(evidence('origin','SAME_DECLARED_SOURCE_PARTICULAR',a.source_particular,
        'The sender-declared particular matches; human identity is not authenticated.'));
    if(match('source_history_head',a,b))
      facts.push(evidence('lineage','SAME_DECLARED_HISTORY_HEAD',a.source_history_head,
        'The source-history reference matches; a shared reference does not prove parentage.'));
    if(match('source_family',a,b))
      facts.push(evidence('structure','SAME_DECLARED_ADAPTER_FAMILY',a.source_family,
        'Both verified envelopes declare this adapter family; donor semantics remain unverified.'));
    if(match('source_contract',a,b))
      facts.push(evidence('structure','SAME_DECLARED_DONOR_CONTRACT',a.source_contract,
        'Matching declared donor contracts are labels, not cross-world authority.'));
    for(const addr of sharedAddresses(a,b))
      facts.push(evidence('content','SAME_DECLARED_PAYLOAD_ADDRESS',addr,
        'Both signed wrappers point to this address; these source bytes were not fetched or compared.'));
    // Neighbor means adjacent RECEIVEs in the *verified receiver journal*,
    // not necessarily adjacent wall-clock arrival or related original projects.
    if(Math.abs(a.receive_seq-b.receive_seq)===1)
      facts.push(evidence('arrival','NEIGHBOR_RECEIVE_SEQUENCE',
        String(Math.min(a.receive_seq,b.receive_seq))+'→'+Math.max(a.receive_seq,b.receive_seq),
        'These crossings were consecutive RECEIVE entries in this receiver journal; no content relation is implied.'));
    if(!facts.length)continue;
    facts.sort((a,b)=>a.lens.localeCompare(b.lens)||a.kind.localeCompare(b.kind)||
      a.value.localeCompare(b.value));
    const left=a.crossing_id,right=b.crossing_id;
    edges.push({
      proposal_id:hex({stateRef,left,right,facts}),
      source_crossing_id:left,target_crossing_id:right,
      evidence:facts,evidence_count:facts.length,
      lenses:[...new Set(facts.map(x=>x.lens))].sort(),
      status:'UNSELECTED_PROPOSAL',
      relation_asserted:false,admission_authorized:false,
    });
  }
  edges.sort((a,b)=>b.evidence_count-a.evidence_count||
    a.source_crossing_id.localeCompare(b.source_crossing_id)||
    a.target_crossing_id.localeCompare(b.target_crossing_id));
  const limited=edges.slice(0,maxEdges);
  return {
    schema:'workbench.stack2-023-mycelium-proposals/v0',
    state_ref:stateRef,
    total_held:records.length,
    included_held:nodes.length,
    skipped_held:records.length-nodes.length,
    total_evidence_edges:edges.length,
    edges_truncated:edges.length>limited.length,
    lenses:[...LENSES],
    nodes:nodes.map(({declared_payload_addresses,receive_seq,...rest})=>({
      ...rest,declared_payload_count:declared_payload_addresses.length,
      receive_seq,
      relation_selected:false,owner_admitted:false
    })),
    edges:limited,
    all_connections_are_proposals:true,
    receiver_disposition_unchanged:true,
    source_claims_independently_verified:false,
    source_bytes_compared:false,
    relationships_persisted:false,
    source_authority_inferred:false,
    receiver_admission_authorized:false
  };
}
