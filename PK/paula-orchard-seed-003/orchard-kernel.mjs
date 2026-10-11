// ORCHARD SEED 001 — local, deliberately non-networked authority membrane.
// No dependency, autonomous execution, identity verification, or external transfer.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

export const VERSION='orchard.seed-001/v0.1';
const EFFECTS=new Set(['keep_local','stage_public','stage_handoff']);
const ALLOW_SOURCE=new Set(['stories','inbox','generated','artifacts']);
const idPattern=/^[a-f0-9]{32}$/;
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const iso=()=>new Date().toISOString();
const fail=m=>{throw new Error(m)};
const makeDir=p=>fs.mkdirSync(p,{recursive:true,mode:0o700});
const privateDir=root=>path.join(root,'.orchard-private');
const repoRoot=()=>path.dirname(fileURLToPath(import.meta.url));
function secureRead(root,relative){
  if(typeof relative!=='string'||relative.length>300||path.isAbsolute(relative)||relative.includes('\\')||relative.includes('\0')) fail('unsafe source path');
  const parts=relative.split('/');
  if(!parts.length||!ALLOW_SOURCE.has(parts[0])||parts.some(x=>!x||x==='.'||x==='..')) fail('source outside admitted local areas');
  let at=root;
  for(const part of parts){at=path.join(at,part);const st=fs.lstatSync(at);if(st.isSymbolicLink()) fail('symlink source refused');}
  const st=fs.statSync(at);
  if(!st.isFile()||st.size>5*1024*1024) fail('source must be a regular file <=5 MiB');
  return fs.readFileSync(at);
}
function writeNew(root,category,id,obj){const folder=path.join(privateDir(root),category);makeDir(folder);const p=path.join(folder,id+'.json');fs.writeFileSync(p,JSON.stringify(obj,null,2)+'\n',{flag:'wx',mode:0o600});return obj;}
function load(root,category,id){if(!idPattern.test(id))fail('invalid proposal id');return JSON.parse(fs.readFileSync(path.join(privateDir(root),category,id+'.json'),'utf8'));}
export function init(root=repoRoot()){
  for(const d of ['proposals','approvals','used','receipts','kept','exports/public','exports/handoff'])makeDir(path.join(privateDir(root),d));
  const marker=path.join(privateDir(root),'README.txt');
  if(!fs.existsSync(marker))fs.writeFileSync(marker,'Local only. Private material and approvals: do not sync this directory. This is not verified identity, legal consent, or a publishing service.\n',{mode:0o600});
  return {status:'INITIALIZED',private_directory:'.orchard-private',version:VERSION};
}
export function propose(root,{source,effect,purpose,visibility='private',destination='local-only',capabilities=[]}){
  init(root);
  if(!EFFECTS.has(effect))fail('unsupported effect: no network, spending, or plugin execution adapter');
  if(!['private','shareable'].includes(visibility))fail('visibility must be private or shareable');
  if(effect!=='keep_local'&&source.startsWith('inbox/'))fail('raw storydrops cannot be staged for export; first create and review a separate derived artifact');
  if(effect!=='keep_local'&&visibility!=='shareable')fail('private material cannot be staged for export');
  if(effect==='keep_local'&&destination!=='local-only')fail('local keep requires local-only destination');
  if(effect!=='keep_local'&&(!destination||destination==='local-only'||destination.length>160))fail('exact human-readable destination required');
  if(typeof purpose!=='string'||!purpose.trim()||purpose.length>240)fail('bounded purpose required');
  if(!Array.isArray(capabilities)||capabilities.length>15||capabilities.some(x=>typeof x!=='string'||x.length>150))fail('capability references must be a bounded list');
  const bytes=secureRead(root,source),id=crypto.randomBytes(16).toString('hex');
  return writeNew(root,'proposals',id,{schema:VERSION,id,created_at:iso(),source,effect,purpose:purpose.trim(),visibility,destination,capabilities,source_sha256:digest(bytes),status:'PROPOSED',authority:'none'});
}
export function review(root,id){
  const p=load(root,'proposals',id),data=secureRead(root,p.source);
  return {...p,current_sha256:digest(data),unchanged:digest(data)===p.source_sha256,already_approved:fs.existsSync(path.join(privateDir(root),'approvals',id+'.json')),consumed:fs.existsSync(path.join(privateDir(root),'used',id+'.json'))};
}
export function authorize(root,id,{actor,ack,rightsConfirmed=false}={}){
  const p=review(root,id);
  if(!p.unchanged)fail('source changed; re-propose and review exact new bytes');
  if(p.consumed||p.already_approved)fail('one proposal cannot be approved twice');
  if(typeof actor!=='string'||!actor.trim()||actor.length>100)fail('declared actor required');
  if(ack!==`I APPROVE ${p.source_sha256.slice(0,12)} ${p.effect}`)fail('exact content-bound approval phrase required');
  if(p.effect!=='keep_local'&&rightsConfirmed!==true)fail('affirm rights and consent for this exact export');
  return writeNew(root,'approvals',id,{schema:VERSION,id,proposal_sha256:digest(Buffer.from(JSON.stringify(load(root,'proposals',id)))),source_sha256:p.source_sha256,effect:p.effect,destination:p.destination,declared_actor:actor.trim(),rights_attested:p.effect==='keep_local'?null:true,approved_at:iso(),human_identity_verified:false,authority:'one local staging operation only'});
}
export function perform(root,id){
  const p=review(root,id),a=load(root,'approvals',id);
  if(p.consumed)fail('approval already consumed');
  if(!p.unchanged||p.source_sha256!==a.source_sha256||p.effect!==a.effect||p.destination!==a.destination)fail('source or approval mismatch');
  if(digest(Buffer.from(JSON.stringify(load(root,'proposals',id))))!==a.proposal_sha256)fail('proposal changed after approval');
  const bytes=secureRead(root,p.source);
  if(digest(bytes)!==a.source_sha256)fail('source changed during execution');
  writeNew(root,'used',id,{id,consumed_at:iso(),approval_ref:id}); // fail-closed on partial output, prevents replay
  const kind=p.effect==='keep_local'?'kept':p.effect==='stage_public'?'exports/public':'exports/handoff';
  const out=path.join(privateDir(root),kind,id+'.'+(path.extname(p.source).slice(1).replace(/[^a-z0-9]/gi,'').slice(0,12)||'bin'));
  fs.writeFileSync(out,bytes,{flag:'wx',mode:0o600});
  const receipt={schema:VERSION,id,effect:p.effect,status:p.effect==='keep_local'?'KEPT_LOCAL':'STAGED_LOCALLY_NOT_SENT',source_sha256:p.source_sha256,output_sha256:digest(fs.readFileSync(out)),relative_output:path.relative(root,out),destination_intent:p.destination,approval_ref:id,performed_at:iso(),external_transfer:false,verified_identity:false,source_ref:p.source};
  writeNew(root,'receipts',id,receipt);
  return receipt;
}
export function listCapabilities(root=repoRoot()){
  return JSON.parse(fs.readFileSync(path.join(root,'ORCHARD_CAPABILITIES.json'),'utf8'));
}
export function compose(root,ids){
  const inventory=listCapabilities(root),chosen=ids.map(id=>inventory.capabilities.find(x=>x.id===id)||fail('unknown capability '+id));
  return {status:'PLAN_ONLY',selection:chosen.map(x=>({id:x.id,source:x.source,status:x.status,adapter:x.adapter,authority:'none'})),executable:false,reason:'References and source metadata do not grant execution, private access, or effects; independently validate and authorize an exact adapter before binding.'};
}
export function cli(args,root=repoRoot()){
  const [cmd,...rest]=args;const values={};for(let i=0;i<rest.length;i++){const x=rest[i];if(!x.startsWith('--'))fail('unknown argument '+x);const v=rest[++i];if(!v||v.startsWith('--'))fail('missing value for '+x);values[x.slice(2)]=v;}
  if(cmd==='init')return init(root);
  if(cmd==='capabilities')return listCapabilities(root);
  if(cmd==='compose')return compose(root,(values.ids||'').split(',').filter(Boolean));
  if(cmd==='propose')return propose(root,{source:values.source,effect:values.effect,purpose:values.purpose,visibility:values.visibility||'private',destination:values.destination||'local-only',capabilities:(values.capabilities||'').split(',').filter(Boolean)});
  if(cmd==='review')return review(root,values.id);
  if(cmd==='perform')return perform(root,values.id);
  if(cmd==='approve'){
    if(!process.stdin.isTTY||!process.stdout.isTTY)fail('approval requires a local interactive terminal; never pass an approval phrase as a CLI argument');
    const p=review(root,values.id);process.stdout.write(JSON.stringify(p,null,2)+'\n');
    process.stdout.write('Open the displayed source path and inspect its exact contents before approving. Type the displayed phrase, or press Enter to refuse:\n');
    const phrase=`I APPROVE ${p.source_sha256.slice(0,12)} ${p.effect}`;
    process.stdout.write(phrase+'\n> ');
    const buf=Buffer.alloc(256);const n=fs.readSync(process.stdin.fd,buf,0,256,null);const ack=buf.subarray(0,n).toString().trim();
    let rightsConfirmed=false;
    if(p.effect!=='keep_local'){
      process.stdout.write('Do you affirm you have the necessary rights AND third-party permissions for this exact material and destination? Type YES, otherwise refused: ');
      const b=Buffer.alloc(32),k=fs.readSync(process.stdin.fd,b,0,32,null);rightsConfirmed=b.subarray(0,k).toString().trim()==='YES';
    }
    return authorize(root,values.id,{actor:values.actor,ack,rightsConfirmed});
  }
  fail('commands: init | capabilities | compose --ids ID,ID | propose --source REL --effect keep_local|stage_public|stage_handoff --purpose TEXT [--visibility shareable --destination EXACT] | review --id ID | approve --id ID --actor NAME (local terminal) | perform --id ID');
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{console.log(JSON.stringify(cli(process.argv.slice(2)),null,2));}catch(e){console.error('REFUSED:',e.message);process.exitCode=2;}
}
