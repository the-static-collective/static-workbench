/** Read-only browser comparison against one operator-initiated host-native proof. */
import {GHOT_PIN,RELATTE_PIN,inspectPublicWitness} from './receipt-floor-core.mjs';

export const CANNON_PIN='2fab6e142f21f6213bbcf4e290030acfce756061';
export const PORTER_SCHEMA='workbench.stack-squared-native-verification/v0';
export const API_SCHEMA='workbench.stack-squared-native-verification-state/v0';
const safe=(ok,code)=>{if(!ok)throw Error(code);};
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.getPrototypeOf(x)===Object.prototype;
const digestId=/^[a-f0-9]{64}$/;
const fields=['schema','status','verified_at','source_pins','public_inspection_sha256',
 'public_canonical_sha256','ghot_report_id','relatte_crossing_id',
 'relatte_received_receipt_id','relatte_hold_receipt_id','checks',
 'receiver_disposition','receiver_admitted','human_identity_authenticated',
 'operator_permission_inferred','browser_execution','signature_trust','attestation_sha256'];
const checks=['EXACT_CANNON_023_SOURCE_BYTES','GHOT_SIGNED_INSTRUMENT_PACKET',
 'ORIGINAL_RELATTE_R14_CROSSING','DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES',
 'ORIGINAL_RECEIVER_DURABLE_JOURNAL','PRIVATE_REPORT_EXACT_BINDING',
 'NO_ADMIT_OR_OWNER_ACT'];
function canonical(x){
 if(x===null||typeof x==='string'||typeof x==='boolean')return JSON.stringify(x);
 if(typeof x==='number'){safe(Number.isSafeInteger(x),'NON_INTEGER');return JSON.stringify(x);}
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 safe(plain(x),'NON_CANONICAL');
 return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
}
export async function sha256Bytes(buf){
 safe(globalThis.crypto?.subtle,'LOCAL_WEBCRYPTO_UNAVAILABLE');
 const result=await crypto.subtle.digest('SHA-256',buf);
 return Array.from(new Uint8Array(result),x=>x.toString(16).padStart(2,'0')).join('');
}
export async function validatePorterSummary(value){
 safe(plain(value)&&Object.keys(value).sort().join('|')===fields.slice().sort().join('|'),'BAD_PORTER_FIELDS');
 safe(value.schema===PORTER_SCHEMA&&value.status==='LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED','BAD_PORTER_SCHEMA');
 safe(plain(value.source_pins)&&Object.keys(value.source_pins).sort().join('|')==='CANNON|GHoT|reLATTE'&&
  value.source_pins.GHoT===GHOT_PIN&&value.source_pins.CANNON===CANNON_PIN&&
  value.source_pins.reLATTE===RELATTE_PIN,'BAD_SOURCE_PINS');
 safe(typeof value.verified_at==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(value.verified_at),
  'BAD_VERIFICATION_TIME');
 safe(value.receiver_disposition==='R3_HOLD'&&value.receiver_admitted===false&&
  value.human_identity_authenticated===false&&value.operator_permission_inferred===false&&
  value.browser_execution===false&&
  value.signature_trust==='SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY'&&
  JSON.stringify(value.checks)===JSON.stringify(checks),'AUTHORITY_OR_CHECK_PROMOTION');
 for(const k of ['public_inspection_sha256','public_canonical_sha256','attestation_sha256'])
  safe(typeof value[k]==='string'&&digestId.test(value[k]),'BAD_DIGEST');
 for(const k of ['ghot_report_id','relatte_crossing_id','relatte_received_receipt_id',
                  'relatte_hold_receipt_id'])safe(typeof value[k]==='string'&&value[k].length<160,'BAD_RECEIPT_ID');
 const body={...value};delete body.attestation_sha256;
 safe(value.attestation_sha256===await sha256Bytes(new TextEncoder().encode(canonical(body))),'ALTERED_LOCAL_SUMMARY');
 return value;
}
export async function inspectApiResult(data){
 safe(plain(data)&&data.schema===API_SCHEMA&&typeof data.available==='boolean'&&
      typeof data.state==='string','INVALID_LOCAL_API_RESPONSE');
 if(!data.available){
   safe(Object.keys(data).sort().join('|')==='available|schema|state'&&
        ['NO_OPERATOR_VERIFICATION','INVALID_LOCAL_PORTER_ATTESTATION'].includes(data.state),
        'INVALID_UNAVAILABLE_RESPONSE');
   return null;
 }
 safe(data.state==='AVAILABLE'&&Object.keys(data).sort().join('|')==='available|schema|state|summary',
     'INVALID_AVAILABLE_RESPONSE');
 return validatePorterSummary(data.summary);
}
export async function matchPublicFile(porter,originalBytes){
 await validatePorterSummary(porter);
 safe(originalBytes instanceof Uint8Array&&originalBytes.byteLength>=1&&
      originalBytes.byteLength<=12288,'INVALID_PUBLIC_FILE_SIZE');
 const bytesDigest=await sha256Bytes(originalBytes);
 safe(bytesDigest===porter.public_inspection_sha256,'PUBLIC_FILE_BYTES_DIFFER_FROM_NATIVE_PROOF');
 const parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(originalBytes));
 inspectPublicWitness(parsed);
 safe(await sha256Bytes(new TextEncoder().encode(canonical(parsed)))===porter.public_canonical_sha256,
      'PUBLIC_CANONICAL_CONTENT_CHANGED');
 safe(parsed.ghot_report_id===porter.ghot_report_id&&
      parsed.relatte_crossing_id===porter.relatte_crossing_id&&
      parsed.relatte_received_receipt_id===porter.relatte_received_receipt_id&&
      parsed.relatte_hold_receipt_id===porter.relatte_hold_receipt_id,'RECEIPT_IDENTITIES_DIFFER');
 return {status:'PUBLIC_FILE_BOUND_TO_OPERATOR_NATIVE_VERIFICATION',
         verified_at:porter.verified_at,attestation_sha256:porter.attestation_sha256,
         original_signatures_checked_by_browser:false,
         verification_performed_by_host:true,
         owner_identity_established:false,receiver_admitted:false,browser_executed_native:false};
}
