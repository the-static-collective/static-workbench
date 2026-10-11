// STATIC WORKBENCH / RETURN ROOM 001 — browser-local lens over STATIC OS dockets.
// Cryptographically checks ONLY the local self-addressed JSON; native reLATTE
// signatures and source input bytes must be reverified by STATIC OS outside this UI.
const byte=v=>new TextEncoder().encode(v);
const hex=buf=>Array.from(new Uint8Array(buf),b=>b.toString(16).padStart(2,'0')).join('');
const digest=async v=>'sha256:'+hex(await crypto.subtle.digest('SHA-256',byte(v)));
const ordered=v=>v&&typeof v==='object'?
  Array.isArray(v)?v.map(ordered):Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
export const canonical=v=>JSON.stringify(ordered(v));
const EXACT=(v,fields,label)=>{
 if(!v||typeof v!=='object'||Array.isArray(v)||
   Object.keys(v).length!==fields.length||fields.some(k=>!Object.hasOwn(v,k)))
  throw Error(label+'_SHAPE');
};
const inspectKeys=[
 'schema','crossing_id','public_payload_sha256','receive_receipt_id','hold_receipt_id',
 'custody_receipt_id','understory_contact_ref','understory_association_ref',
 'question_aperture','question','question_receipt_digest','verifier',
 'receiver_signatures_verified','claimed_human_observer','original_source_ancestry',
 'admission','automatic_execution','next_turn','memento_canon_changed',
 'remote_delivery','boot_proof'
];
const inputs=['carrier','review','questionSeed','contact','association'];
const requiredHash=s=>typeof s==='string'&&/^sha256:[a-f0-9]{64}$/.test(s);
const receipt=s=>typeof s==='string'&&/^relatte-receipt-v0:[a-f0-9]{64}$/.test(s);
const crossing=s=>typeof s==='string'&&/^relatte-crossing-v0:[a-f0-9]{64}$/.test(s);
const date=s=>typeof s==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(s)&&!Number.isNaN(Date.parse(s));
const FINGERPRINTS=o=>{
 EXACT(o,inputs,'INPUT_FINGERPRINTS');
 for(const id of inputs)if(!requiredHash(o[id]))throw Error('INVALID_INPUT_FINGERPRINT');
};
export const LENSES=Object.freeze([
 {id:'source',label:'01 · SOURCE',title:'What arrived?',description:'The candidate is a source-bound, redacted artifact; original private objects remain outside this room.'},
 {id:'receipt',label:'02 · RECEIPT',title:'Who signed?',description:'Receiver receipt IDs are recorded; this browser does not verify reLATTE P-256 signatures.'},
 {id:'hold',label:'03 · HOLD',title:'What remained unresolved?',description:'Local R3_HOLD is not permission, acceptance or canonical history.'},
 {id:'witness',label:'04 · WITNESS',title:'Who encountered it?',description:'The observer was asserted upstream, not independently authenticated here.'},
 {id:'neighbor',label:'05 · NEIGHBOR',title:'What was placed beside what?',description:'An unresolved association is not ancestry or causation.'},
 {id:'question',label:'06 · QUESTION',title:'What do we ask?',description:'The earliest original source is still missing.'},
 {id:'gap',label:'07 · GAP',title:'What cannot be claimed?',description:'The handoff must preserve uncertainty.'},
 {id:'return',label:'08 · RETURN',title:'What can be revisited?',description:'An old question can be revisited without modifying its past.'},
 {id:'custody',label:'09 · CUSTODY',title:'What exact bytes are addressed?',description:'Payload hashes and local file fingerprints are addresses, not third-party authentication.'},
 {id:'future',label:'10 · FUTURE',title:'Who may come next?',description:'A future reader may investigate without inheriting our conclusions.'},
 {id:'door',label:'11 · DOOR',title:'Who decides?',description:'Only a new explicit human selection could open a different world.'}
]);
function inspectSession(s){
 EXACT(s,['schema','state','input_fingerprints','inspection','at','operator_selected','scope',
  'writes_to_source_worlds','unresolved_questions','session_id'],'SESSION');
 if(s.schema!=='static-os.return-room-session/v0'||s.state!=='HELD_QUESTION'||
   s.operator_selected!==true||s.scope!=='LOCAL_QUESTION_WORKBENCH_ONLY'||
   s.writes_to_source_worlds!==false||!date(s.at)||!requiredHash(s.session_id))
  throw Error('INVALID_STATIC_OS_SESSION');
 FINGERPRINTS(s.input_fingerprints);
 const i=s.inspection;
 EXACT(i,inspectKeys,'INSPECTION');
 if(i.schema!=='static-os.return-room-inspection/v0'||!crossing(i.crossing_id)||
   !requiredHash(i.public_payload_sha256)||!requiredHash(i.question_receipt_digest)||
   !receipt(i.receive_receipt_id)||!receipt(i.hold_receipt_id)||!receipt(i.custody_receipt_id)||
   typeof i.understory_contact_ref!=='string'||!i.understory_contact_ref.startsWith('contact-madd-hold-')||
   typeof i.understory_association_ref!=='string'||!i.understory_association_ref.startsWith('association-madd-hold-')||
   i.question_aperture!=='source-object'||typeof i.question!=='string'||
   !i.question.endsWith('?')||i.question.length>4096||
   i.verifier!=='NATIVE_RELATTE_AND_NATIONAL_TREASURE'||i.receiver_signatures_verified!==3||
   i.claimed_human_observer!=='NOT_INDEPENDENTLY_AUTHENTICATED'||
   i.original_source_ancestry!=='NOT_ESTABLISHED'||i.admission!=='none'||
   i.automatic_execution!==false||i.next_turn!=='NOT_AUTHORIZED'||
   i.memento_canon_changed!==false||i.remote_delivery!==false||i.boot_proof!==false)
  throw Error('INSPECTION_UNEARNED_AUTHORITY');
 if(!Array.isArray(s.unresolved_questions)||s.unresolved_questions.length!==1||
    s.unresolved_questions[0]!==i.question)throw Error('QUESTION_DRIFT');
}
function inspectCheckpoint(c,s){
 EXACT(c,['schema','state','input_fingerprints','at','operator_selected','automatic_retry','reviewer_claim'],'CHECKPOINT');
 if(c.schema!=='static-os.return-room-checkpoint/v0'||c.state!=='PREPARED'||
    !date(c.at)||c.at!==s.at||c.operator_selected!==true||
    c.automatic_retry!==false||c.reviewer_claim!=='local-operator-provided-not-authenticated')
   throw Error('CHECKPOINT_DRIFT');
 FINGERPRINTS(c.input_fingerprints);
 if(canonical(c.input_fingerprints)!==canonical(s.input_fingerprints))throw Error('CHECKPOINT_SOURCE_DRIFT');
}
function inspectReplay(r,s){
 EXACT(r,['schema','state','session_id','crossing_id','question','independently_reverified',
    'read_only','executed_again','next_turn','owner_authority'],'REPLAY');
 if(r.schema!=='static-os.return-room-replay/v0'||r.state!=='HELD_QUESTION'||
   r.session_id!==s.session_id||r.crossing_id!==s.inspection.crossing_id||
   r.question!==s.inspection.question||r.independently_reverified!==true||
   r.read_only!==true||r.executed_again!==false||r.next_turn!=='NOT_AUTHORIZED'||
   r.owner_authority!=='none')throw Error('REPLAY_DRIFT');
}
export async function inspectDocket(session,checkpoint=null,replay=null){
 inspectSession(session);
 const {session_id,...body}=session;
 if(session_id!==await digest(canonical(body)))throw Error('SESSION_ADDRESS_CHANGED');
 if(checkpoint!==null)inspectCheckpoint(checkpoint,session);
 if(replay!==null)inspectReplay(replay,session);
 return Object.freeze({
  schema:'static-workbench.return-room-view/v0',
  status:'LOCAL_SESSION_ADDRESS_CHECKED',
  native_signatures:'NOT_REVERIFIED_IN_BROWSER',
  source_files:'NOT_REOPENED_IN_BROWSER',
  checkpoint:checkpoint?'STRUCTURALLY_BOUND':'NOT_IMPORTED',
  native_replay:replay?'CLAIMED_BY_IMPORTED_REPLAY_FILE':'NOT_IMPORTED',
  operator_identity:'NOT_AUTHENTICATED',
  session_id,
  question:session.inspection.question,
  crossing_id:session.inspection.crossing_id,
  admission:'none',next_turn:'NOT_AUTHORIZED'
 });
}
export function lensDetails(s,id){
 inspectSession(s);
 if(!LENSES.some(l=>l.id===id))throw Error('UNKNOWN_DIAL');
 const i=s.inspection;
 switch(id){
  case 'source':return [i.crossing_id,i.public_payload_sha256,'Private source objects: not established here'];
  case 'receipt':return [i.receive_receipt_id,i.hold_receipt_id,'P-256: inspect with STATIC OS to verify'];
  case 'hold':return ['Disposition: HELD_QUESTION','Next turn: NOT_AUTHORIZED','No ADMIT or project write'];
  case 'witness':return [i.understory_contact_ref,'Observer: NOT_INDEPENDENTLY_AUTHENTICATED','Receipt != person saw it'];
  case 'neighbor':return [i.understory_association_ref,'Unresolved association only','Adjacency != ancestry'];
  case 'question':return [i.question,'Question class: source-object','No answer or historical proof'];
  case 'gap':return ['Source genealogy NOT_ESTABLISHED','Original sources NOT_REOPENED','No hardware or boot claim'];
  case 'return':return [s.session_id,'Local session: HELD_QUESTION','No automatic re-execution'];
  case 'custody':return [i.custody_receipt_id,'Payload: '+i.public_payload_sha256,'Exact input files must be rechecked by STATIC OS'];
  case 'future':return ['Next reader may ask again','No inherited right to source files','The question survives without requiring an answer'];
  default:return ['Permission: NONE','Door: HUMAN_SELECTION_REQUIRED','STATIC OS owns the session; source worlds own their history'];
 }
}
export function nextReaderPacket(s){
 inspectSession(s);
 return {
  schema:'static-workbench.return-room-handoff/v0',
  source_session_id:s.session_id,
  crossing_id:s.inspection.crossing_id,
  question:s.inspection.question,
  question_aperture:'source-object',
  support_confidence:'unsupported',
  source_owner_identity:'NOT_AUTHENTICATED',
  browser_verification:'LOCAL_SESSION_ADDRESS_ONLY',
  native_receipt_verification:'REQUIRED_AT_RECEIVING_WORLD',
  admission:'none',
  next_action:'NEW_HUMAN_SELECTION_REQUIRED'
 };
}
