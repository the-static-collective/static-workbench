#!/usr/bin/env node
/** STACK² 026 — portable owner-issued P-256 statement of a bounded native proof.
 * Issuing requires explicit operator action and an externally managed private key.
 * Verification REQUIRES an independently supplied trust fingerprint.
 * OpenManus/LOADOUT may read the public certificate, never mint or verify authority.
 */
import {createHash, createPrivateKey, createPublicKey, createVerify, createSign,
        sign as ecdsaSign, verify as ecdsaVerify} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';

const SCHEMA='static.stack2.portable-native-verification/v0';
const STATE='workbench.stack-squared-native-verification/v0';
const GHOT='6194d91ba83bad63606f6f6741723007227518f2';
const CANNON='2fab6e142f21f6213bbcf4e290030acfce756061';
const R14='dcc8cdca84c440aa4294134f020fb7095bf87f24';
const CHECKS=['EXACT_CANNON_023_SOURCE_BYTES','GHOT_SIGNED_INSTRUMENT_PACKET',
  'ORIGINAL_RELATTE_R14_CROSSING','DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES',
  'ORIGINAL_RECEIVER_DURABLE_JOURNAL','PRIVATE_REPORT_EXACT_BINDING',
  'NO_ADMIT_OR_OWNER_ACT'];
const fail=(x,msg)=>{if(!x)throw Error(msg)};
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const sha=b=>createHash('sha256').update(b).digest('hex');
const canonical=v=>{
  if(v===null||typeof v==='boolean'||typeof v==='string')return JSON.stringify(v);
  if(typeof v==='number'){fail(Number.isSafeInteger(v),'UNSAFE_NUMBER');return JSON.stringify(v);}
  if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
  fail(object(v),'NON_JSON');
  return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
};
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const exact=(x,allowed)=>object(x)&&Object.keys(x).sort().join('|')===allowed.slice().sort().join('|');
const HEX=/^[0-9a-f]{64}$/;
const REF=/^(relatte-crossing-v0|relatte-receipt-v0|ai-recomposition-report-v0):[a-f0-9]{64}$/;
const bodyKeys=['schema','status','verified_at','source_pins','public_inspection_sha256',
    'public_canonical_sha256','ghot_report_id','relatte_crossing_id','relatte_received_receipt_id',
    'relatte_hold_receipt_id','checks','receiver_disposition','receiver_admitted',
    'human_identity_authenticated','operator_permission_inferred','browser_execution','signature_trust'];
function validateState(s){
  fail(exact(s,[...bodyKeys,'attestation_sha256'])&&s.schema===STATE&&
       s.status==='LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED','INVALID_LOCAL_PORTER_ATTESTATION');
  fail(exact(s.source_pins,['GHoT','CANNON','reLATTE'])&&s.source_pins.GHoT===GHOT&&
       s.source_pins.CANNON===CANNON&&s.source_pins.reLATTE===R14,'SOURCE_PINS_MISMATCH');
  fail(JSON.stringify(s.checks)===JSON.stringify(CHECKS)&&
       s.receiver_disposition==='R3_HOLD'&&s.receiver_admitted===false&&
       s.human_identity_authenticated===false&&s.operator_permission_inferred===false&&
       s.browser_execution===false&&
       s.signature_trust==='SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY',
       'UNAUTHORIZED_SEMANTIC_PROMOTION');
  fail(typeof s.verified_at==='string'&&!Number.isNaN(Date.parse(s.verified_at)),
       'INVALID_VERIFIED_AT');
  fail([s.public_inspection_sha256,s.public_canonical_sha256,s.attestation_sha256].every(x=>
      typeof x==='string'&&HEX.test(x)),'BAD_ATTESTATION_DIGEST');
  fail([s.ghot_report_id,s.relatte_crossing_id,s.relatte_received_receipt_id,
        s.relatte_hold_receipt_id].every(x=>typeof x==='string'&&REF.test(x)),
       'BAD_RECEIPT_ID');
  fail(s.relatte_received_receipt_id!==s.relatte_hold_receipt_id,'COLLAPSED_RECEIPT');
  const body={...s};delete body.attestation_sha256;
  fail(sha(canonical(body))===s.attestation_sha256,'TAMPERED_LOCAL_SUMMARY');
  return s;
}
function checkedTime(t){
  fail(typeof t==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(t)&&
       Number.isFinite(Date.parse(t))&&new Date(t).toISOString()===t.slice(0,-1)+'.000Z',
       'INVALID_EXPIRATION');
  return Date.parse(t);
}
const bytesToSign=v=>Buffer.from('STATIC-STACK2-026-PORTABLE-V0|'+canonical(v));
const pemToSpki=(pem)=>createPublicKey(pem).export({type:'spki',format:'der'});
export function keyFingerprint(spki){return 'sha256:'+sha(spki);}
export function issue(state,privateKeyPem,expiresAt,now=new Date()){
  validateState(state);
  const end=checkedTime(expiresAt),start=now.getTime();
  fail(Number.isFinite(start)&&end>start&&end<=start+30*86400e3,'EXPIRATION_OUTSIDE_30_DAYS');
  const key=createPrivateKey(privateKeyPem);
  fail(key.asymmetricKeyType==='ec'&&key.asymmetricKeyDetails?.namedCurve==='prime256v1',
       'ISSUER_KEY_MUST_BE_P256');
  const pub=createPublicKey(key).export({type:'spki',format:'der'});
  const payload={
    schema:'static.stack2.portable-proof-body/v0',
    source_pins:state.source_pins,
    verified_at:state.verified_at,
    expires_at:expiresAt,
    public_inspection_sha256:state.public_inspection_sha256,
    public_canonical_sha256:state.public_canonical_sha256,
    native_summary_sha256:state.attestation_sha256,
    source_report_id:state.ghot_report_id,
    crossing_id:state.relatte_crossing_id,
    received_receipt_id:state.relatte_received_receipt_id,
    hold_receipt_id:state.relatte_hold_receipt_id,
    native_checks:CHECKS,
    disposition:'R3_HOLD',admitted:false,operator_act:false,
    owner_identity_authenticated:false,
    agent_testimony_authority:false,
  };
  const signature=ecdsaSign('sha256',bytesToSign(payload),key);
  return {schema:SCHEMA,payload,signing:{
    algorithm:'ECDSA-P256-SHA256',
    public_key_spki_der_b64:pub.toString('base64'),
    key_fingerprint:keyFingerprint(pub),
    signature_b64:signature.toString('base64')
  }};
}
function b64(s){
  fail(typeof s==='string'&&s.length<8192&&s.length>1&&
       /^[A-Za-z0-9+/]+={0,2}$/.test(s),'INVALID_BASE64');
  const b=Buffer.from(s,'base64');
  fail(b.toString('base64')===s,'NONCANONICAL_BASE64');
  return b;
}
export function verify(bundle,trustFingerprint,now=new Date()){
  fail(exact(bundle,['schema','payload','signing'])&&bundle.schema===SCHEMA,
       'INVALID_PORTABLE_BUNDLE');
  const p=bundle.payload,k=bundle.signing;
  const pk=['schema','source_pins','verified_at','expires_at','public_inspection_sha256',
    'public_canonical_sha256','native_summary_sha256','source_report_id','crossing_id',
    'received_receipt_id','hold_receipt_id','native_checks','disposition','admitted',
    'operator_act','owner_identity_authenticated','agent_testimony_authority'];
  fail(exact(p,pk)&&exact(k,['algorithm','public_key_spki_der_b64','key_fingerprint','signature_b64']),
       'UNEXPECTED_PORTABLE_FIELDS');
  fail(exact(p.source_pins,['GHoT','CANNON','reLATTE'])&&p.source_pins.GHoT===GHOT&&
       p.source_pins.CANNON===CANNON&&p.source_pins.reLATTE===R14,
       'UNTRUSTED_SOURCE_PINS');
  fail(p.schema==='static.stack2.portable-proof-body/v0'&&
       p.disposition==='R3_HOLD'&&p.admitted===false&&p.operator_act===false&&
       p.owner_identity_authenticated===false&&p.agent_testimony_authority===false&&
       JSON.stringify(p.native_checks)===JSON.stringify(CHECKS),'UNAUTHORIZED_PORTABLE_CLAIM');
  fail([p.public_inspection_sha256,p.public_canonical_sha256,p.native_summary_sha256].every(x=>
       typeof x==='string'&&HEX.test(x)),'INVALID_CONTENT_ADDRESS');
  fail([p.source_report_id,p.crossing_id,p.received_receipt_id,p.hold_receipt_id].every(x=>
       typeof x==='string'&&REF.test(x))&&p.received_receipt_id!==p.hold_receipt_id,
       'INVALID_RECEIPT_BRAID');
  fail(typeof p.verified_at==='string'&&Number.isFinite(Date.parse(p.verified_at)),
       'INVALID_PROOF_TIME');
  const expiry=checkedTime(p.expires_at),verified=Date.parse(p.verified_at);
  fail(expiry>verified&&expiry-verified<=31*86400e3&&now.getTime()<expiry,
       'PORTABLE_PROOF_EXPIRED');
  fail(k.algorithm==='ECDSA-P256-SHA256','UNSUPPORTED_PORTABLE_ALGORITHM');
  const spki=b64(k.public_key_spki_der_b64);
  fail(typeof trustFingerprint==='string'&&/^sha256:[a-f0-9]{64}$/.test(trustFingerprint),
       'INDEPENDENT_TRUST_ANCHOR_REQUIRED');
  fail(keyFingerprint(spki)===trustFingerprint&&k.key_fingerprint===trustFingerprint,
       'ISSUER_NOT_TRUSTED');
  const key=createPublicKey({key:spki,format:'der',type:'spki'});
  fail(key.asymmetricKeyType==='ec'&&key.asymmetricKeyDetails?.namedCurve==='prime256v1',
       'UNSUPPORTED_SIGNING_CURVE');
  fail(ecdsaVerify('sha256',bytesToSign(p),key,b64(k.signature_b64)),
       'INVALID_PORTABLE_SIGNATURE');
  return {status:'PORTABLE_SOURCE_BOUNDED_SIGNATURE_VERIFIED',
          issuer_key_fingerprint:trustFingerprint,
          crossing_id:p.crossing_id,hold_id:p.hold_receipt_id,
          expires_at:p.expires_at,admitted:false,agent_authority:false,
          source_human_identity_authenticated:false,
          independent_issuer_key_trust:'OUT_OF_BAND_FINGERPRINT_REQUIRED'};
}
function argmap(argv){
  const args={};for(let i=0;i<argv.length;i+=2){
    fail(argv[i]?.startsWith('--')&&i+1<argv.length&&!args[argv[i]],
         'INVALID_CLI_ARGS');args[argv[i]]=argv[i+1];
  }return args;
}
function cli(){
  const [mode,...rest]=process.argv.slice(2),a=argmap(rest);
  if(mode==='issue'){
    fail(a['--approve-issue']==='yes'&&a['--state']&&a['--private-key']&&
         a['--expires-at']&&a['--output'],'EXPLICIT_ISSUER_APPROVAL_REQUIRED');
    fail(!existsSync(a['--output']),'REFUSE_OVERWRITE');
    const source=read(a['--state']);
    const signed=issue(source,readFileSync(a['--private-key'],'utf8'),a['--expires-at']);
    writeFileSync(a['--output'],JSON.stringify(signed,null,2)+'\n',{flag:'wx',mode:0o600});
    console.log(JSON.stringify({status:'ISSUED_NOT_ADMITTED',
      issuer_fingerprint:signed.signing.key_fingerprint,
      private_key_exported:false,portable_bundle:a['--output']}));
  }else if(mode==='verify'){
    fail(a['--bundle']&&a['--trust-fingerprint'],'REQUIRED_VERIFICATION_ARGUMENTS');
    console.log(JSON.stringify(verify(read(a['--bundle']),a['--trust-fingerprint']),null,2));
  }else if(mode==='fingerprint'){
    fail(a['--public-key'],'PUBLIC_KEY_PATH_REQUIRED');
    console.log(keyFingerprint(pemToSpki(readFileSync(a['--public-key'],'utf8'))));
  }else throw Error('Usage: issue|verify|fingerprint with explicit named flags');
}
if(process.argv[1]?.endsWith('stack2-026-portable.mjs')){
  try{cli();}catch(e){console.error('HOLD:',String(e.message).slice(0,200));process.exitCode=1;}
}
