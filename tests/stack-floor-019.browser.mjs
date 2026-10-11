import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdirSync} from 'node:fs';
import {setTimeout as delay} from 'node:timers/promises';
import {chromium} from 'playwright';

const sha=s=>createHash('sha256').update(s).digest('hex');
const canonical=x=>{
 if(x===null||typeof x==='string'||typeof x==='boolean'||typeof x==='number')return JSON.stringify(x);
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
};
const assert=(v,s)=>{if(!v)throw Error(s);};
function fixture(){
 const ids=['PLZ-TRANCH-ROOM-001','PLZ-HUMAN-SUPABARDO-001'];
 const native={schema:'static-collective/planz-global-sense-run/v0',dedupedRecordCount:2,
   authority:'none',selection:'NONE',
   frames:ids.map(planId=>({planId,authority:'none',selection:'NONE',signals:{}})),
   unaryCandidates:ids.map((id,i)=>({candidateId:'mut-'+(i?'2222222222222222':'1111111111111111'),
     chamber:'REANIMATE',sourcePlanIds:[id],authority:'none',selection:'NONE'}))};
 const summary={schema:'cannon.stack-squared-native-summary/v0',source_records:ids,
   original_git_witnesses:5,native_planz_run:true,native_planz_frame_count:2,
   native_planz_proposals:native.unaryCandidates.map(x=>({
     id:x.candidateId,chamber:x.chamber,sourcePlanIds:x.sourcePlanIds,
     authority:'none',selection:'NONE'})),
   native_ghot_local_system_hash:true,ghot_result_sha256:sha(sha(canonical(native))),
   ghot_receipt_sha256:'f'.repeat(64),
   native_relatte_signed_crossing_id:'relatte-crossing:synthetic-not-signed',
   native_relatte_receive_receipt_id:'relatte-receive:synthetic-not-signed',
   native_relatte_hold_receipt_id:'relatte-hold:synthetic-not-signed',
   signed_objects_cold_verified:3,disposition:'HOLD',receiver_admitted:false,
   external_effects:0,production_deployed:false};
 return {summary,native};
}
const py=[
 'from pathlib import Path',
 'from static_workbench.app import create_app',
 'from static_workbench.config import RootConfig, WorkbenchConfig',
 'import uvicorn',
 'r = Path.cwd().resolve()',
 'cfg = WorkbenchConfig(bind_host="127.0.0.1",port=13877,state_dir=Path("/tmp/stack-floor-browser-ci-state"),roots=(RootConfig("static",r),))',
 'uvicorn.run(create_app(cfg),host="127.0.0.1",port=13877,log_level="warning")'
].join('\n');
const server=spawn('python3',['-c',py],{stdio:['ignore','pipe','pipe']});
let errorLog='';
server.stderr.on('data',chunk=>{errorLog+=chunk.toString().slice(0,800)});
let browser;
try{
 let ready=false;
 for(let i=0;i<80;i++){
   if(server.exitCode!==null)throw Error('SERVER_DIED '+errorLog.slice(0,500));
   try{const res=await fetch('http://127.0.0.1:13877/stack-floor',{signal:AbortSignal.timeout(1000)});
     if(res.ok){ready=true;break;}}catch{}
   await delay(150);
 }
 assert(ready,'FASTAPI_NOT_READY '+errorLog.slice(0,500));
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1320,height:900},acceptDownloads:true});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:13877/stack-floor');
 assert(await page.locator('button.brick').count()===5,'FIVE_CARDS_MISSING');
 assert(await page.locator('.socket').count()===4,'FOUR_SOCKETS_MISSING');
 await page.locator('.brick[data-id="fixture"]').dragTo(page.locator('.socket').nth(0));
 assert(await page.locator('.socket').first().locator('.socket-state').innerText()==='HOLD',
   'INCOMPATIBLE_BRICK_DID_NOT_HOLD');
 await page.locator('#reset').click();
 await page.locator('.brick[data-id="cannon"]').focus();
 await page.keyboard.press('Enter');
 for(const id of ['planz','ghot','relatte'])await page.locator('.brick[data-id="'+id+'"]').click();
 assert((await page.locator('#fit-caption').innerText()).includes('ALL FOUR SOCKETS FIT'),'NATIVE_STACK_FAILED');
 const {summary,native}=fixture();
 await page.locator('#summary').setInputFiles({
   name:'public-inspection.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(summary))});
 await page.locator('#native').setInputFiles({
   name:'native-planz-output.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(native))});
 await page.locator('#inspect').click();
 await page.waitForFunction(()=>document.getElementById('evidence-status').textContent.includes('STRUCTURAL CHECK PASSED'));
 assert(await page.locator('#trial').isDisabled(),'TRIAL_NOT_CONSENT_GATED');
 await page.locator('#consent').check();
 assert(await page.locator('#trial').isEnabled(),'CONSENT_TRIAL_NOT_ENABLED');
 await page.locator('#trial').click();
 await page.waitForFunction(()=>document.getElementById('trial-status').textContent.includes('LOCAL HASH RELATION VERIFIED'));
 assert(await page.locator('#export').isEnabled(),'EXPORT_NOT_ENABLED');
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export').click()]);
 assert(download.suggestedFilename()==='stack-squared-019-local-trial-unsigned.json','UNEXPECTED_DOWNLOAD');
 assert(errors.length===0,'BROWSER_ERROR '+errors.join(';'));
 const output=process.env.STACK2_BROWSER_OUTPUT||'/tmp/stack-floor-019-witness';
 mkdirSync(output,{recursive:true});
 await page.screenshot({path:output+'/desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:output+'/mobile.png',fullPage:true});
 assert(await page.locator('#reset').isVisible(),'MOBILE_FLOOR_INVISIBLE');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=400,'MOBILE_HORIZONTAL_OVERFLOW');
 console.log(JSON.stringify({status:'REAL_CHROMIUM_STACK_FLOOR_019_PASSED',cards:5,sockets:4,
   incompatible:'HOLD',keyboard:true,consent_gated:true,browser_sha256:true,
   unsigned_download:true,desktop_mobile:true,page_errors:0}));
 await context.close();
}finally{
 if(browser)await browser.close();
 server.kill('SIGTERM');
}
