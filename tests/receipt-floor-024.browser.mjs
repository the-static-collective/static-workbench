import {spawn} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {setTimeout as delay} from 'node:timers/promises';
import {chromium} from 'playwright';
import {GHOT_PIN,RELATTE_PIN,SCHEMA} from '../static_workbench/web/receipt-floor-core.mjs';

const expect=(condition,reason)=>{if(!condition)throw Error(reason);};
const mk=(prefix,d)=>prefix+':'+d.repeat(64);
const fixture={
  schema:SCHEMA,source_commit:GHOT_PIN,relatte_commit:RELATTE_PIN,
  ghot_report_id:mk('ai-recomposition-report-v0','a'),
  ghot_report_sha256:'b'.repeat(64),
  cannon_witness_id:mk('cannon-stack2-ai-witness-v0','c'),
  ghot_signed_execution_receipts:[mk('relatte-receipt-v0','1')],
  ghot_portable_packet_ids:[mk('portable-seed-v0','2')],
  relatte_crossing_id:mk('relatte-crossing-v0','3'),
  relatte_received_receipt_id:mk('relatte-receipt-v0','4'),
  relatte_hold_receipt_id:mk('relatte-receipt-v0','5'),
  destination:'R3_HOLD',original_ghot_donor_reexecuted:false,
  original_relatte_receiver_used:true,cold_signatures_verified:true,
  source_human_identity_established:false,receiver_admitted:false,
  external_effects:0,production_deployed:false
};
const python=[
 'from pathlib import Path',
 'from static_workbench.app import create_app',
 'from static_workbench.config import RootConfig, WorkbenchConfig',
 'import uvicorn',
 'root=Path.cwd().resolve()',
 'config=WorkbenchConfig(bind_host="127.0.0.1",port=13924,state_dir=Path("/tmp/stack2-receipt-browser-state"),roots=(RootConfig("home",root),))',
 'uvicorn.run(create_app(config),host="127.0.0.1",port=13924,log_level="warning")'
].join('\n');
const server=spawn('python3',['-c',python],{stdio:['ignore','ignore','pipe']});
let stderr='';server.stderr.on('data',v=>{stderr+=v.toString().slice(0,400);});
let browser;
try{
 let started=false;
 for(let n=0;n<80;n++){
   if(server.exitCode!==null)throw Error('SERVER_DIED:'+stderr);
   try{const res=await fetch('http://127.0.0.1:13924/receipt-floor',
     {signal:AbortSignal.timeout(900)});if(res.ok){started=true;break;}}catch{}
   await delay(140);
 }
 expect(started,'SERVER_NOT_READY:'+stderr);
 browser=await chromium.launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:1330,height:900},acceptDownloads:true});
 const page=await ctx.newPage();const errors=[];
 page.on('pageerror',error=>errors.push(String(error.message)));
 await page.goto('http://127.0.0.1:13924/receipt-floor');
 expect(await page.locator('#make-packet').isDisabled(),'NO CONSENT GATE');
 expect(await page.locator('.chain-item').count()===0,'INVENTED RECEIPTS BEFORE FILE IMPORT');
 // Import explicit, clearly synthetic *test* data. This is UI mechanics, not crypto evidence.
 await page.locator('#receipt-file').setInputFiles({
  name:'public-inspection.json',mimeType:'application/json',
  buffer:Buffer.from(JSON.stringify(fixture))});
 await page.locator('#inspect').click();
 await page.waitForFunction(()=>document.getElementById('import-status').textContent.includes('PUBLIC WITNESS LOADED'));
 expect(await page.locator('.chain-item').count()===7,'SEVEN_RECEIPT_CARDS_MISSING');
 await page.locator('.chain-item').last().focus();
 await page.keyboard.press('Enter');
 expect((await page.locator('#part-name').innerText()).includes('R3_HOLD'),'KEYBOARD_HOLD_SELECTION');
 expect((await page.locator('#part-authority').innerText()).includes('RECEIVER LOCAL'),'LOCAL_AUTHORITY_LABEL');
 await page.locator('[data-phase="receiver"]').click();
 expect(await page.locator('.chain-item').count()===2,'RECEIVER_APERTURE_COUNT');
 await page.locator('#walk').click();
 expect(await page.locator('#part-name').innerText()==='Receiver: RECEIVED','WALK_START');
 await page.locator('#walk').click();
 expect(await page.locator('#part-name').innerText()==='Receiver: R3_HOLD','WALK_HOLD');
 expect(await page.locator('#make-packet').isDisabled(),'NO_INSPECTION_CONSENT');
 await page.locator('#consent').check();
 await page.locator('#make-packet').click();
 await page.waitForFunction(()=>document.getElementById('packet-status').textContent.includes('Unsigned inspection packet composed'));
 expect(await page.locator('#export-packet').isEnabled(),'EXPORT_SHOULD_BE_READY');
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-packet').click()]);
 expect(download.suggestedFilename()==='stack2-024-unsigned-inspection.json','WRONG_EXPORT_FILE');
 const output=process.env.STACK24_BROWSER_OUTPUT||'/tmp/stack2-receipt-floor-images';
 mkdirSync(output,{recursive:true});
 await page.locator('[data-phase="all"]').click();
 await page.screenshot({path:output+'/receipt-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:output+'/receipt-mobile.png',fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)<=400,'MOBILE_HORIZONTAL_OVERFLOW');
 await page.locator('#clear').click();
 expect(await page.locator('.chain-item').count()===0,'WITNESS_WAS_NOT_CLEARED');
 expect(await page.locator('#export-packet').isDisabled(),'STALE_PACKET_AFTER_CLEAR');
 expect(errors.length===0,'BROWSER_RUNTIME_ERRORS:'+errors.join(';'));
 console.log(JSON.stringify({status:'RECEIPT_FLOOR_024_CHROMIUM_PASSED',
   fixture:'SYNTHETIC_UI_ONLY',cards:7,aperture:true,keyboard:true,
   local_unsigned_export:true,clearing:true,mobile:true,page_errors:0}));
 await ctx.close();
}finally{if(browser)await browser.close();server.kill('SIGTERM');}
