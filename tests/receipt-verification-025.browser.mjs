import {spawn} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {setTimeout as delay} from 'node:timers/promises';
import {chromium} from 'playwright';
import {GHOT_PIN,RELATTE_PIN} from '../static_workbench/web/receipt-floor-core.mjs';
import {CANNON_PIN,PORTER_SCHEMA,sha256Bytes}
  from '../static_workbench/web/receipt-verification-core.mjs';

const fail=(ok,why)=>{if(!ok)throw Error(why);};
const id=(prefix,c)=>prefix+':'+c.repeat(64);
const canonical=x=>{
 if(x===null||typeof x==='string'||typeof x==='boolean'||typeof x==='number')return JSON.stringify(x);
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
};
const stateDir='/tmp/stack2-025-browser-state';
const publicWitness={
 schema:'cannon.stack-squared-ai-relatte-public/v0',
 source_commit:GHOT_PIN,relatte_commit:RELATTE_PIN,
 ghot_report_id:id('ai-recomposition-report-v0','a'),
 ghot_report_sha256:'b'.repeat(64),
 cannon_witness_id:id('cannon-stack2-ai-witness-v0','c'),
 ghot_signed_execution_receipts:[id('relatte-receipt-v0','1')],
 ghot_portable_packet_ids:[id('portable-seed-v0','2')],
 relatte_crossing_id:id('relatte-crossing-v0','3'),
 relatte_received_receipt_id:id('relatte-receipt-v0','4'),
 relatte_hold_receipt_id:id('relatte-receipt-v0','5'),
 destination:'R3_HOLD',original_ghot_donor_reexecuted:false,
 original_relatte_receiver_used:true,cold_signatures_verified:true,
 source_human_identity_established:false,receiver_admitted:false,
 external_effects:0,production_deployed:false
};
const publicBytes=Buffer.from(JSON.stringify(publicWitness,null,2)+'\n');
const body={
 schema:PORTER_SCHEMA,status:'LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED',
 verified_at:'2026-10-11T19:10:00Z',
 source_pins:{GHoT:GHOT_PIN,CANNON:CANNON_PIN,reLATTE:RELATTE_PIN},
 public_inspection_sha256:await sha256Bytes(publicBytes),
 public_canonical_sha256:await sha256Bytes(new TextEncoder().encode(canonical(publicWitness))),
 ghot_report_id:publicWitness.ghot_report_id,
 relatte_crossing_id:publicWitness.relatte_crossing_id,
 relatte_received_receipt_id:publicWitness.relatte_received_receipt_id,
 relatte_hold_receipt_id:publicWitness.relatte_hold_receipt_id,
 checks:['EXACT_CANNON_023_SOURCE_BYTES','GHOT_SIGNED_INSTRUMENT_PACKET',
 'ORIGINAL_RELATTE_R14_CROSSING','DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES',
 'ORIGINAL_RECEIVER_DURABLE_JOURNAL','PRIVATE_REPORT_EXACT_BINDING','NO_ADMIT_OR_OWNER_ACT'],
 receiver_disposition:'R3_HOLD',receiver_admitted:false,
 human_identity_authenticated:false,operator_permission_inferred:false,
 browser_execution:false,signature_trust:'SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY'
};
const summary={...body,attestation_sha256:
 await sha256Bytes(new TextEncoder().encode(canonical(body)))};
mkdirSync(stateDir+'/receipt-porter',{recursive:true,mode:0o700});
writeFileSync(stateDir+'/receipt-porter/latest.json',JSON.stringify(summary,null,2)+'\n',{mode:0o600});
const script=[
 'from pathlib import Path',
 'from static_workbench.app import create_app',
 'from static_workbench.config import RootConfig, WorkbenchConfig',
 'import uvicorn',
 'p=Path.cwd().resolve()',
 'cfg=WorkbenchConfig(bind_host="127.0.0.1",port=13925,state_dir=Path("'+stateDir+'"),roots=(RootConfig("source",p),))',
 'uvicorn.run(create_app(cfg),host="127.0.0.1",port=13925,log_level="warning")'
].join('\n');
const server=spawn('python3',['-c',script],{stdio:['ignore','ignore','pipe']});
let errors=[],log='';server.stderr.on('data',b=>{log+=b.toString().slice(0,500)});
let browser;
try{
 let ready=false;
 for(let i=0;i<75;i++){
  if(server.exitCode!==null)throw Error('SERVER_FAILED '+log);
  try{const x=await fetch('http://127.0.0.1:13925/receipt-verification',
    {signal:AbortSignal.timeout(1000)});if(x.ok){ready=true;break;}}catch{}
  await delay(150);
 }
 fail(ready,'SERVER_NOT_READY');
 browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:1320,height:900}});
 const page=await ctx.newPage();
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:13925/receipt-verification');
 fail(await page.locator('#match').isDisabled(),'MATCH_NOT_GATED');
 await page.locator('#read-local').click();
 await page.waitForFunction(()=>document.getElementById('porter-status').textContent.includes('OPERATOR-RUN LOCAL'));
 fail((await page.locator('#porter-time').innerText()).includes('2026-10-11T19:10:00Z'),'TIMESTAMP_NOT_VISIBLE');
 await page.locator('#public-file').setInputFiles({
  name:'public-inspection.json',mimeType:'application/json',buffer:publicBytes});
 await page.locator('#match').click();
 await page.waitForFunction(()=>document.getElementById('match-status').textContent.includes('PUBLIC_FILE_BOUND'));
 fail((await page.locator('#hold-address').innerText())===publicWitness.relatte_hold_receipt_id,
      'RECEIPT_ADDRESS_LOST');
 await page.locator('#public-file').setInputFiles({
  name:'public-inspection.json',mimeType:'application/json',
  buffer:Buffer.from(JSON.stringify({...publicWitness,receiver_admitted:true}))});
 await page.locator('#match').click();
 await page.waitForFunction(()=>document.getElementById('match-status').textContent.includes('HOLD:'));
 fail((await page.locator('#match-status').innerText()).includes('PUBLIC_FILE_BYTES_DIFFER'),
   'TAMPERED_WITNESS_NOT_REFUSED');
 const output=process.env.STACK25_BROWSER_OUTPUT||'/tmp/stack2-025-browser-output';
 mkdirSync(output,{recursive:true});
 await page.screenshot({path:output+'/verify-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:output+'/verify-mobile.png',fullPage:true});
 fail(await page.evaluate(()=>document.documentElement.scrollWidth)<=400,'MOBILE_OVERFLOW');
 await page.locator('#clear-local').click();
 fail((await page.locator('#porter-status').innerText())==='NOT REQUESTED','CLEAR_NOT_RESPECTED');
 fail(errors.length===0,'BROWSER_RUNTIME_ERROR: '+errors.join(';'));
 console.log(JSON.stringify({status:'STACK2_025_BROWSER_PASS',
   fixture:'SYNTHETIC_HOST_SUMMARY_NOT_AUTHENTICATED_PROOF',
   local_get:true,public_bytes_bound:true,tampered_public_held:true,mobile:true,errors:0}));
 await ctx.close();
}finally{if(browser)await browser.close();server.kill('SIGTERM');}
