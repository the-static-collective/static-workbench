import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {issue,verify,keyFingerprint} from '../scripts/stack2-026-portable.mjs';

const keys=generateKeyPairSync('ec',{namedCurve:'prime256v1'});
const priv=keys.privateKey.export({type:'pkcs8',format:'pem'});
const spki=keys.publicKey.export({type:'spki',format:'der'});
const anchor=keyFingerprint(spki);
const now=new Date('2026-10-11T19:30:00Z');
const expiry='2026-10-12T19:30:00Z';
const codeId=(p,c)=>p+':'+c.repeat(64);
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
function canonical(x){
  if(x===null||typeof x==='boolean'||typeof x==='number'||typeof x==='string')return JSON.stringify(x);
  if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
  return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
}
function state(){
  const b={
    schema:'workbench.stack-squared-native-verification/v0',
    status:'LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED',
    verified_at:'2026-10-11T19:00:00Z',
    source_pins:{
      GHoT:'6194d91ba83bad63606f6f6741723007227518f2',
      CANNON:'2fab6e142f21f6213bbcf4e290030acfce756061',
      reLATTE:'dcc8cdca84c440aa4294134f020fb7095bf87f24'
    },
    public_inspection_sha256:'a'.repeat(64),
    public_canonical_sha256:'b'.repeat(64),
    ghot_report_id:codeId('ai-recomposition-report-v0','c'),
    relatte_crossing_id:codeId('relatte-crossing-v0','d'),
    relatte_received_receipt_id:codeId('relatte-receipt-v0','e'),
    relatte_hold_receipt_id:codeId('relatte-receipt-v0','f'),
    checks:['EXACT_CANNON_023_SOURCE_BYTES','GHOT_SIGNED_INSTRUMENT_PACKET',
     'ORIGINAL_RELATTE_R14_CROSSING','DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES',
     'ORIGINAL_RECEIVER_DURABLE_JOURNAL','PRIVATE_REPORT_EXACT_BINDING',
     'NO_ADMIT_OR_OWNER_ACT'],
    receiver_disposition:'R3_HOLD',
    receiver_admitted:false,
    human_identity_authenticated:false,
    operator_permission_inferred:false,
    browser_execution:false,
    signature_trust:'SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY'
  };
  return {...b,attestation_sha256:createHash('sha256').update(canonical(b)).digest('hex')};
}
test('P256 issues portable public-only certificate that independently verifies with out-of-band anchor',()=>{
  const s=state(),bundle=issue(s,priv,expiry,now);
  assert.equal(bundle.signing.key_fingerprint,anchor);
  assert.equal(bundle.payload.admitted,false);
  assert.equal(bundle.payload.operator_act,false);
  assert.equal(bundle.payload.agent_testimony_authority,false);
  assert.equal(bundle.payload.owner_identity_authenticated,false);
  assert(!JSON.stringify(bundle).includes('PRIVATE MODEL PROMPT'));
  const result=verify(bundle,anchor,now);
  assert.equal(result.status,'PORTABLE_SOURCE_BOUNDED_SIGNATURE_VERIFIED');
  assert.equal(result.admitted,false);
  assert.equal(result.agent_authority,false);
  assert.equal(result.source_human_identity_authenticated,false);
});
test('refuse self-asserted issuer trust, altered signing key, payload tamper and fabricated admission',()=>{
  const signed=issue(state(),priv,expiry,now);
  const alter=f=>{const x=structuredClone(signed);f(x);return x;};
  assert.throws(()=>verify(signed,undefined,now),/INDEPENDENT_TRUST_ANCHOR_REQUIRED/);
  assert.throws(()=>verify(signed,'sha256:'+'1'.repeat(64),now),/ISSUER_NOT_TRUSTED/);
  assert.throws(()=>verify(alter(x=>x.payload.admitted=true),anchor,now),/UNAUTHORIZED_PORTABLE_CLAIM/);
  assert.throws(()=>verify(alter(x=>x.payload.agent_testimony_authority=true),anchor,now),
    /UNAUTHORIZED_PORTABLE_CLAIM/);
  assert.throws(()=>verify(alter(x=>x.payload.public_inspection_sha256='1'.repeat(64)),anchor,now),
    /INVALID_PORTABLE_SIGNATURE/);
  assert.throws(()=>verify(alter(x=>x.signing.signature_b64='QUJDRA=='),anchor,now),
    /INVALID_PORTABLE_SIGNATURE/);
  assert.throws(()=>verify(alter(x=>x.payload.injected_provider_approval=true),anchor,now),
    /UNEXPECTED_PORTABLE_FIELDS/);
});
test('refuse expiry, changed original 025 attestation and wrong issuer key curve',()=>{
  const s=state();
  const bundle=issue(s,priv,expiry,now);
  assert.throws(()=>verify(bundle,anchor,new Date('2026-10-12T19:30:00Z')),/EXPIRED/);
  assert.throws(()=>issue({...s,receiver_admitted:true},priv,expiry,now),
    /UNAUTHORIZED_SEMANTIC_PROMOTION/);
  assert.throws(()=>issue({...s,attestation_sha256:'f'.repeat(64)},priv,expiry,now),
    /TAMPERED_LOCAL_SUMMARY/);
  assert.throws(()=>issue(s,priv,'2027-11-12T19:30:00Z',now),/EXPIRATION_OUTSIDE_30_DAYS/);
  const other=generateKeyPairSync('ed25519');
  assert.throws(()=>issue(s,other.privateKey.export({type:'pkcs8',format:'pem'}),expiry,now),
    /ISSUER_KEY_MUST_BE_P256/);
});
