// WORLDBODY-001: local genealogy and receipt projection, NOT a network census or authority service.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

export const VERSION='worldbody.local/v0.1';
const TYPES=new Set(['inspired_by','collaborated_with','capability_from','seed_offered_to','seed_reportedly_received_from']);
const fail=s=>{throw new Error(s);};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const iso=()=>new Date().toISOString();
const exactString=(s,n=160)=>typeof s==='string'&&s.trim().length>0&&s.length<=n&& !/[\x00-\x1f\x7f]/.test(s);
const uuid=()=>crypto.randomUUID();
const privateRoot=r=>path.join(r,'.orchard-private','worldbody');
const eventDir=r=>path.join(privateRoot(r),'events');
export function initWorldbody(root){fs.mkdirSync(eventDir(root),{recursive:true,mode:0o700});return {schema:VERSION,state:'LOCAL_ONLY',authority:'none',directory:'.orchard-private/worldbody'};}
function safeFile(root,rel){
  if(!exactString(rel,240)||path.isAbsolute(rel)||rel.includes('\\')||rel.split('/').some(c=>c===''||c==='.'||c==='..')||rel.startsWith('.orchard-private/'))fail('unsafe source path');
  let p=path.resolve(root);for(const part of rel.split('/')){p=path.join(p,part);const st=fs.lstatSync(p);if(st.isSymbolicLink())fail('source symlink refused');}
  if(!fs.statSync(p).isFile())fail('source must be file');return fs.readFileSync(p);
}
function canonicalWithoutHash(e){const {event_sha256,...rest}=e;return rest;}
function ledger(root){
  const dir=eventDir(root);if(!fs.existsSync(dir))return [];
  const names=fs.readdirSync(dir).sort();let prior='GENESIS',known=new Set(),events=[];
  for(let i=0;i<names.length;i++){
    const name=names[i];if(!/^\d{6}\.json$/.test(name)||name!==String(i+1).padStart(6,'0')+'.json')fail('ledger sequence invalid');
    let e;try{e=JSON.parse(fs.readFileSync(path.join(dir,name),'utf8'));}catch{fail('ledger event corrupted');}
    if(e.schema!==VERSION||e.seq!==i+1||e.prev_sha256!==prior||e.event_sha256!==sha(JSON.stringify(canonicalWithoutHash(e))))fail('ledger history verification failed at '+name);
    if(e.type==='WORLD_DECLARED'){
      if(!exactString(e.world_id,80)||known.has(e.world_id)||!Array.isArray(e.parent_world_ids)||new Set(e.parent_world_ids).size!==e.parent_world_ids.length||e.parent_world_ids.some(id=>!known.has(id)))fail('invalid birth ancestry');
      if(!/^[a-f0-9]{64}$/.test(e.seed_sha256)||!exactString(e.label)||!exactString(e.operator_label)||e.membership!=='not_established'||e.authority!=='none')fail('invalid birth fields');
      known.add(e.world_id);
    } else if(e.type==='RELATION_ASSERTED'){
      if(!known.has(e.from_world)||!known.has(e.to_world)||e.from_world===e.to_world||!TYPES.has(e.relation)||!exactString(e.evidence_ref,240)||e.authority!=='none')fail('invalid world relation');
    }else if(e.type==='LOCAL_RECEIPT_REFERENCED'){
      if(!known.has(e.world_id)||!exactString(e.receipt_id,100)||!/^[a-f0-9]{64}$/.test(e.receipt_sha256)||!['KEPT_LOCAL','STAGED_LOCALLY_NOT_SENT'].includes(e.observed_status)||e.authority!=='none')fail('invalid receipt reference');
    }else fail('unknown event type');
    events.push(e);prior=e.event_sha256;
  }
  return events;
}
function append(root,type,fields){
  initWorldbody(root);const old=ledger(root),seq=old.length+1;if(seq>999999)fail('ledger limit');
  const event={schema:VERSION,seq,id:uuid(),type,occurred_at:iso(),prev_sha256:old.at(-1)?.event_sha256||'GENESIS',...fields};
  event.event_sha256=sha(JSON.stringify(canonicalWithoutHash(event)));
  const file=path.join(eventDir(root),String(seq).padStart(6,'0')+'.json');
  const fd=fs.openSync(file,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(event,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  return event;
}
const worldsFrom=events=>events.filter(e=>e.type==='WORLD_DECLARED');
export function declareWorld(root,{label,operator_label,seed_source,parent_world_ids=[],unresolved_external_origin=null}={}){
  if(!exactString(label)||!exactString(operator_label)||!Array.isArray(parent_world_ids)||parent_world_ids.length>12||new Set(parent_world_ids).size!==parent_world_ids.length)fail('invalid world declaration');
  if(unresolved_external_origin!==null&&!exactString(unresolved_external_origin,240))fail('invalid unresolved external origin');
  const previous=ledger(root),worlds=new Set(worldsFrom(previous).map(x=>x.world_id));
  if(parent_world_ids.some(id=>!worlds.has(id)))fail('parent world not registered here: keep external origin unresolved');
  const seed_sha256=sha(safeFile(root,seed_source));
  return append(root,'WORLD_DECLARED',{world_id:'worldbody://local/'+uuid(),label:label.trim(),operator_label:operator_label.trim(),seed_sha256,parent_world_ids,unresolved_external_origin,origin_status:unresolved_external_origin?'EXTERNAL_ORIGIN_UNVERIFIED':'LOCAL_SOURCE_DIGEST_ONLY',membership:'not_established',identity_verified:false,authority:'none'});
}
export function assertRelation(root,{from_world,to_world,relation,evidence_ref}={}){
  if(!TYPES.has(relation)||!exactString(evidence_ref,240))fail('invalid relation or evidence');
  const worlds=new Set(worldsFrom(ledger(root)).map(x=>x.world_id));
  if(!worlds.has(from_world)||!worlds.has(to_world)||from_world===to_world)fail('relation endpoints must be distinct registered local worlds');
  return append(root,'RELATION_ASSERTED',{from_world,to_world,relation,evidence_ref,attestation:'LOCAL_CLAIM_UNVERIFIED',consent_verified:false,authority:'none'});
}
export function referenceOrchardReceipt(root,{world_id,receipt_id}={}){
  const worlds=new Set(worldsFrom(ledger(root)).map(x=>x.world_id));
  if(!worlds.has(world_id)||typeof receipt_id!=='string'||!/^[a-f0-9]{32}$/.test(receipt_id))fail('world or receipt ID invalid');
  const p=path.join(root,'.orchard-private','receipts',receipt_id+'.json');
  let r,bytes;try{bytes=fs.readFileSync(p);r=JSON.parse(bytes.toString('utf8'));}catch{fail('missing or invalid local orchard receipt');}
  if(r.id!==receipt_id||r.external_transfer!==false||!['KEPT_LOCAL','STAGED_LOCALLY_NOT_SENT'].includes(r.status)||!exactString(r.relative_output,240)||!/^[a-f0-9]{64}$/.test(r.output_sha256))fail('not a supported local orchard receipt');
  const target=path.resolve(root,r.relative_output);const privateDir=path.resolve(root,'.orchard-private')+path.sep;
  if(!target.startsWith(privateDir)||!fs.existsSync(target)||fs.lstatSync(target).isSymbolicLink()||sha(fs.readFileSync(target))!==r.output_sha256)fail('receipt output missing, unsafe, or changed');
  const old=ledger(root);if(old.some(e=>e.type==='LOCAL_RECEIPT_REFERENCED'&&e.world_id===world_id&&e.receipt_id===receipt_id))fail('duplicate receipt reference for world');
  return append(root,'LOCAL_RECEIPT_REFERENCED',{world_id,receipt_id,receipt_sha256:sha(bytes),observed_status:r.status,reported_effect:r.effect,external_transfer:false,identity_verified:false,authority:'none'});
}
export function verifyWorldbody(root){const events=ledger(root);return {schema:VERSION,status:'LOCAL_CHAIN_VALID',event_count:events.length,head_sha256:events.at(-1)?.event_sha256||null,scope:'only this local ledger; not external identity, consent, membership, legal liability, or global integrity'};}
export function mapWorldbody(root){
  const events=ledger(root),worlds=worldsFrom(events),relations=events.filter(e=>e.type==='RELATION_ASSERTED'),receipts=events.filter(e=>e.type==='LOCAL_RECEIPT_REFERENCED');
  return {schema:VERSION,scope:'LOCAL_DECLARATIONS_ONLY',global_world_count:null,local_world_count:worlds.length,local_root_count:worlds.filter(x=>!x.parent_world_ids.length).length,local_descendant_count:worlds.filter(x=>x.parent_world_ids.length).length,unverified_external_origin_count:worlds.filter(x=>x.unresolved_external_origin).length,asserted_relation_count:relations.length,local_receipt_reference_count:receipts.length,worlds:worlds.map(x=>({world_id:x.world_id,label:x.label,seed_sha256:x.seed_sha256,parent_world_ids:x.parent_world_ids,unresolved_external_origin:x.unresolved_external_origin,identity_verified:false,membership:'not_established',authority:'none'})),relations:relations.map(x=>({from_world:x.from_world,to_world:x.to_world,type:x.relation,evidence_ref:x.evidence_ref,consent_verified:false,authority:'none'})),receipts:receipts.map(x=>({world_id:x.world_id,receipt_id:x.receipt_id,status:x.observed_status,external_transfer:false})),verification:verifyWorldbody(root)};
}
function parse(args){const [command,...tokens]=args,p={};for(let i=0;i<tokens.length;i++){let v=tokens[i];if(!v.startsWith('--')||!tokens[i+1]||tokens[i+1].startsWith('--'))fail('expected --key value');p[v.slice(2)]=tokens[++i];}return {command,p};}
export function cli(args,root=path.dirname(fileURLToPath(import.meta.url))){
  const {command,p}=parse(args);
  if(command==='init')return initWorldbody(root);
  if(command==='verify')return verifyWorldbody(root);
  if(command==='map')return mapWorldbody(root);
  if(command==='birth')return declareWorld(root,{label:p.label,operator_label:p.operator,seed_source:p.seed,parent_world_ids:(p.parents||'').split(',').filter(Boolean),unresolved_external_origin:p['external-origin']||null});
  if(command==='relation')return assertRelation(root,{from_world:p.from,to_world:p.to,relation:p.type,evidence_ref:p.evidence});
  if(command==='receipt')return referenceOrchardReceipt(root,{world_id:p.world,receipt_id:p.id});
  fail('commands: init | birth --label NAME --operator DECLARED_LABEL --seed RELATIVE_PATH [--parents WORLD_ID,...] [--external-origin SOURCE_REF] | relation --from WORLD_ID --to WORLD_ID --type TYPE --evidence REF | receipt --world WORLD_ID --id ORCHARD_RECEIPT_ID | map | verify');
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{console.log(JSON.stringify(cli(process.argv.slice(2)),null,2));}catch(e){console.error('REFUSED:',e.message);process.exitCode=2;}
}
