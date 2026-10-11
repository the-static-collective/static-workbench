/** STACK² 019 — offline inspection of a proven native CANNON 018 stack.
 * Does not execute donor programs, authenticate Git origins or verify ECDSA signatures.
 */
export const CARDS=Object.freeze([
  {id:'cannon',title:'CANNON',label:'Source witness',repo:'the-static-collective/CANNON',
    commit:'53a1b439161210c03168bb0bb3f6f178ee1da315',
    source:'src/stack-squared-018.mjs',input:'stack19.declared-sources/v0',
    output:'stack19.verified-sources/v0',role:'Verifier',tint:'copper',
    summary:'Original-Git-object checks and explicit local source report'},
  {id:'planz',title:'planZ',label:'Sense engine',repo:'the-static-collective/planZ',
    commit:'e8111fdb64c5587b33aece0fed639ed3d03375ac',
    source:'002/bin/sense-global.mjs',input:'stack19.verified-sources/v0',
    output:'stack19.planz-sense/v0',role:'Native SENSE',tint:'moss',
    summary:'Two actual PlanRecords become non-authoritative Sense Frames'},
  {id:'ghot',title:'GHoT',label:'Local body',repo:'the-static-collective/GHoT',
    commit:'e35dd470384d864b7b0b629a68dad570875a7df0',
    source:'ghot/reference_node.py',input:'stack19.planz-sense/v0',
    output:'stack19.local-hash/v0',role:'Bounded system.hash',tint:'amber',
    summary:'Hashes the PlanZ output digest; does not execute mutation candidates'},
  {id:'relatte',title:'reLATTE',label:'Crossing carrier',repo:'the-static-collective/reLATTE',
    commit:'dcc8cdca84c440aa4294134f020fb7095bf87f24',
    source:'scripts/opaque-roundtrip.ts',input:'stack19.local-hash/v0',
    output:'stack19.held-crossing/v0',role:'Signed RECEIVE → HOLD',tint:'blue',
    summary:'Native signed transport and receiver-owned HOLD, never automatic ADMIT'},
  {id:'fixture',title:'STACK² 017',label:'Loose brick',repo:'the-static-collective/CANNON',
    commit:'3aa5b0d0e9403e90affe05ec4056825e8d166fe4',
    source:'src/stack-squared-017.mjs',input:'cannon.stack2.synthetic/v0',
    output:'cannon.stack2.wrapped/v0',role:'Fixture-only adapter',tint:'ash',
    summary:'A different, tested *fixture* family: not native SENSE-compatible'}
]);
export const REQUIRED=Object.freeze(['cannon','planz','ghot','relatte']);
const ID=/^[a-z][a-z0-9-]{1,31}$/;
const fail=(okay,code)=>{if(!okay)throw new Error(code);};
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
  (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
export function card(id){return CARDS.find(x=>x.id===id)||null;}
export function inspectFloor(slots){
  fail(Array.isArray(slots)&&slots.length===4,'FOUR_SOCKETS_REQUIRED');
  fail(slots.every(id=>id===null||(typeof id==='string'&&ID.test(id)&&card(id))),
    'UNKNOWN_BRICK');
  const used=slots.filter(Boolean);
  fail(new Set(used).size===used.length,'DUPLICATE_BRICK');
  const links=[];
  for(let i=0;i<slots.length;i++){
    const source=card(slots[i]);
    if(!source){links.push({slot:i,status:'EMPTY',reason:'Select a card'});continue;}
    if(i===0){
      links.push({slot:i,status:source.input==='stack19.declared-sources/v0'?'FITS':'HOLD',
        reason:source.input==='stack19.declared-sources/v0'?'Declared source inspection':'Wrong first input type'});
      continue;
    }
    const previous=card(slots[i-1]);
    const fits=previous&&previous.output===source.input&&links[i-1].status==='FITS';
    links.push({slot:i,status:fits?'FITS':'HOLD',
      reason:fits?'Typed Workbench socket matches':'Mismatched or absent predecessor port'});
  }
  return {schema:'workbench.stack-squared-floor/v0',slots:[...slots],links,
    connected:slots.every(Boolean)&&links.every(link=>link.status==='FITS')&&
      REQUIRED.every((id,i)=>id===slots[i]),
    operational_authority:'NONE',native_execution:false,
    port_meaning:'Workbench recipe descriptors, NOT independently executed donor API contracts'};
}
export function addCard(slots,id,where){
  const current=inspectFloor(slots);
  fail(card(id)!==null,'UNKNOWN_BRICK');
  fail(Number.isSafeInteger(where)&&where>=0&&where<4,'INVALID_SOCKET');
  fail(!current.slots.includes(id),'DUPLICATE_BRICK');
  fail(current.slots[where]===null,'SOCKET_OCCUPIED');
  const next=[...slots];next[where]=id;
  return inspectFloor(next);
}
export function removeCard(slots,where){
  inspectFloor(slots);
  fail(Number.isSafeInteger(where)&&where>=0&&where<4,'INVALID_SOCKET');
  const next=[...slots];next[where]=null;
  return inspectFloor(next);
}
function canonical(x){
  if(x===null||typeof x==='string'||typeof x==='boolean')return JSON.stringify(x);
  if(typeof x==='number'){fail(Number.isSafeInteger(x),'UNSAFE_INTEGER');return JSON.stringify(x);}
  if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
  fail(plain(x),'NOT_CANONICAL_JSON');
  return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
}
async function sha(value){
  // WebCrypto is the only runtime operation, with no server call or third-party code.
  fail(typeof crypto!=='undefined'&&crypto.subtle,'WEBCRYPTO_REQUIRED');
  const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
  return [...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');
}
export function inspectSummary(value){
  fail(plain(value)&&value.schema==='cannon.stack-squared-native-summary/v0','NOT_STACK2_018_SUMMARY');
  fail(Array.isArray(value.source_records)&&value.source_records.length===2&&
    value.source_records[0]==='PLZ-TRANCH-ROOM-001'&&
    value.source_records[1]==='PLZ-HUMAN-SUPABARDO-001','UNEXPECTED_SOURCE_RECORDS');
  fail(value.native_planz_run===true&&value.native_planz_frame_count===2&&
    value.native_ghot_local_system_hash===true&&value.original_git_witnesses===5&&
    value.signed_objects_cold_verified===3,'MISSING_CI_PROOF_CLAIMS');
  fail(value.disposition==='HOLD'&&value.receiver_admitted===false&&
    value.external_effects===0&&value.production_deployed===false,
    'FORGED_AUTHORITY_CLAIM');
  fail(Array.isArray(value.native_planz_proposals)&&value.native_planz_proposals.length===2&&
    value.native_planz_proposals.every(x=>plain(x)&&typeof x.id==='string'&&
      x.authority==='none'&&x.selection==='NONE'),'FORGED_PLANZ_PROPOSAL');
  for(const key of ['ghot_result_sha256','ghot_receipt_sha256']){
    fail(typeof value[key]==='string'&&/^[a-f0-9]{64}$/.test(value[key]),'MALFORMED_HASH');
  }
  for(const key of ['native_relatte_signed_crossing_id','native_relatte_receive_receipt_id','native_relatte_hold_receipt_id']){
    fail(typeof value[key]==='string'&&value[key].length>10&&value[key].length<500,'MISSING_RECEIPT_IDENTIFIER');
  }
  // These fields are untrusted input claims, NOT a signature verification.
  return {schema:value.schema,review:'FOREIGN_CI_CLAIMS_ONLY',
    source_records:value.source_records,disposition:'HOLD',
    signature_verification:'NOT_REVERIFIED_IN_BROWSER'};
}
export function inspectNativeOutput(native,summary){
  inspectSummary(summary);
  fail(plain(native)&&native.schema==='static-collective/planz-global-sense-run/v0'&&
    native.authority==='none'&&native.selection==='NONE'&&native.dedupedRecordCount===2,
    'NOT_NATIVE_PLANZ_SENSE');
  fail(Array.isArray(native.frames)&&native.frames.length===2&&
    Array.isArray(native.unaryCandidates)&&native.unaryCandidates.length===2,
    'NATIVE_FRAME_COUNT_MISMATCH');
  fail(native.frames.every((v,i)=>plain(v)&&v.planId===summary.source_records[i]&&
    v.authority==='none'&&v.selection==='NONE'),'SENSE_AUTHORITY_OR_SOURCE_MISMATCH');
  fail(native.unaryCandidates.every((v,i)=>plain(v)&&
    v.authority==='none'&&v.selection==='NONE'&&
    summary.native_planz_proposals[i].id===v.candidateId&&
    summary.native_planz_proposals[i].chamber===v.chamber&&
    canonical(summary.native_planz_proposals[i].sourcePlanIds)===canonical(v.sourcePlanIds)),
    'MUTATION_CANDIDATE_MISMATCH');
  return {source_count:2,candidates:2,execution_authority:'NONE'};
}
export async function runLocalTrial(slots,summary,native,{authorized=false}={}){
  const floor=inspectFloor(slots);
  fail(floor.connected,'STACK_SOCKETS_NOT_CONNECTED');
  fail(authorized===true,'LOCAL_TRIAL_REQUIRES_EXPLICIT_AUTHORIZATION');
  inspectNativeOutput(native,summary);
  const nativeDigest=await sha(canonical(native));
  const expectedGhotHash=await sha(nativeDigest);
  fail(expectedGhotHash===summary.ghot_result_sha256,'NATIVE_OUTPUT_GHOT_HASH_MISMATCH');
  const packet={
    schema:'workbench.stack-squared-local-trial/v0',
    relation:'READ_ONLY_HASH_COMPARISON',
    recipe_cards:floor.slots.map(id=>{
      const c=card(id);return {id:c.id,repository:c.repo,source_commit:c.commit,source_path:c.source};
    }),
    native_planz_output_sha256:nativeDigest,
    observed_ghot_output_sha256:summary.ghot_result_sha256,
    native_planz_record_ids:[...summary.source_records],
    source_ci_reported_disposition:'HOLD',
    source_ci_reported_crossing_id:summary.native_relatte_signed_crossing_id,
    source_ci_reported_receive_receipt_id:summary.native_relatte_receive_receipt_id,
    source_ci_reported_hold_receipt_id:summary.native_relatte_hold_receipt_id,
    checked:['type alignment','planZ source IDs and non-authority','native PlanZ output digest','reported GHoT hashed digest'],
    not_checked:['original Git objects in this browser','GHoT local task receipt contents','reLATTE P-256 signatures','receiver durable journal','operator identity','owner permission'],
    browser_result:'HASH_RELATION_VERIFIED_FOREIGN_SIGNATURES_NOT_REVERIFIED',
    local_execution:'WEBCRYPTO_SHA256_ONLY',native_donor_executions:0,
    network_requests:0,real_world_effects:0,receipt_is_signed:false,
    authority_granted:false,receiver_admitted:false
  };
  return {...packet,packet_sha256:await sha(canonical(packet))};
}
