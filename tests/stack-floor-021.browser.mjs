/** STACK² 021 — actual Chrome buttons: original GHoT ACT → separate CROSS → reLATTE HOLD. */
import {execFileSync,spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {setTimeout as pause} from 'node:timers/promises';
import {chromium} from 'playwright';

const ok=(v,reason)=>{if(!v)throw Error(reason);};
const ghot=process.env.STACK2_020_GHOT_CHECKOUT;
const planz=process.env.STACK2_020_PLANZ_CHECKOUT;
const relatte=process.env.STACK2_021_RELATTE_CHECKOUT;
ok(ghot&&planz&&relatte,'PINNED_CI_GIT_CHECKOUTS_REQUIRED');
const sha='e8111fdb64c5587b33aece0fed639ed3d03375ac';
const source='002/bin/sense-global.mjs';
const bytes=execFileSync('git',['-C',planz,'show',sha+':'+source]);
const sourceDigest=createHash('sha256').update(bytes).digest('hex');
const home=mkdtempSync(join(tmpdir(),'stack2-020-chromium-'));
const owner=join(home,'owner-ghot'),state=join(home,'state'),sources=join(home,'sources');
const receiver=join(home,'receiver');
mkdirSync(join(owner,'branch-worker'),{recursive:true});
mkdirSync(sources);
const context={
  repository:'the-static-collective/planZ',
  commit:sha,path:source,sha256:sourceDigest,
  branchHint:'experiment/fatherhand-grant-chain-residue-001'
};
const policy={schema:'ghot.branch-worker-sources/v0',entries:[{
  context,checkout_root:planz,reviewed_for_local_read:true
}]};
writeFileSync(join(owner,'branch-worker','sources.json'),JSON.stringify(policy)+'\n');
// Independent CI-only receiver creation OUTSIDE Workbench, using original native R14.
const createReceiver=[
 "import {pathToFileURL} from 'node:url';",
 "const r=await import(pathToFileURL(process.argv[1]+'/src/index.ts').href);",
 "await r.LocalReceiver.create(process.argv[2],{world_id:'world:stack2-021-chromium',",
 "receiver_particular:'particular:independent-chromium-receiver',",
 "contract_ref:'contract:chromium-hold-only/v0'});"
].join('\n');
execFileSync('node',['--experimental-strip-types','--input-type=module','-e',
  createReceiver,relatte,receiver],{cwd:relatte,timeout:25000});
const py=[
  'import os',
  'from pathlib import Path',
  'import uvicorn',
  'from static_workbench.app import create_app',
  'from static_workbench.config import WorkbenchConfig,RootConfig',
  'base=Path(os.environ["STACK2_BROWSER_TMP"])',
  'cfg=WorkbenchConfig(bind_host="127.0.0.1",port=13879,',
  ' state_dir=base/"state",roots=(RootConfig("local",base/"sources"),),',
  ' stack_floor_native_enabled=True,',
  ' stack_floor_ghot_checkout=Path(os.environ["STACK2_020_GHOT_CHECKOUT"]),',
  ' stack_floor_planz_checkout=Path(os.environ["STACK2_020_PLANZ_CHECKOUT"]),',
  ' stack_floor_ghot_home=base/"owner-ghot",',
  ' stack_floor_postoffice_enabled=True,',
  ' stack_floor_relatte_checkout=Path(os.environ["STACK2_021_RELATTE_CHECKOUT"]),',
  ' stack_floor_receiver_root=base/"receiver")',
  'uvicorn.run(create_app(cfg),host="127.0.0.1",port=13879,log_level="warning")'
].join('\n');
let browser=null;
const server=spawn('python3',['-c',py],{
  env:{...process.env,STACK2_BROWSER_TMP:home},stdio:['ignore','pipe','pipe']
});
let stderr='';
server.stderr.on('data',b=>{stderr+=b.toString().slice(0,500)});
try{
  let ready=false;
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('WORKBENCH_SERVER_FAILED '+stderr.slice(0,700));
    try{let res=await fetch('http://127.0.0.1:13879/stack-floor',{signal:AbortSignal.timeout(1000)});
      if(res.ok){ready=true;break;}}catch{}
    await pause(160);
  }
  ok(ready,'WORKBENCH_NOT_READY '+stderr);
  browser=await chromium.launch({headless:true});
  const ctx=await browser.newContext({viewport:{width:1320,height:960},acceptDownloads:true});
  const page=await ctx.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:13879/stack-floor');
  await page.waitForFunction(()=>document.getElementById('native-020-state').textContent.includes('AVAILABLE'));
  for(const id of ['cannon','planz','ghot','relatte']){
    await page.locator('.brick[data-id="'+id+'"]').click();
  }
  await page.waitForFunction(()=>!document.getElementById('native-020-preview').disabled);
  await page.locator('#native-020-preview').click();
  await page.waitForFunction(()=>document.getElementById('native-020-result').textContent.includes('Preview READY'));
  ok(await page.locator('#native-020-act').isDisabled(),'ACT_SHOULD_BE_OFF_BEFORE_CONSENT');
  await page.locator('#native-020-ack').check();
  await page.locator('#native-020-phrase').fill('ACT');
  ok(await page.locator('#native-020-act').isEnabled(),'EXPLICIT_ACT_NOT_ARMED');
  await page.locator('#native-020-act').click();
  await page.waitForFunction(()=>document.getElementById('native-020-result').textContent.includes('NATIVE GHoT SIGNED RECEIPT VERIFIED'),{timeout:30000});
  ok(await page.locator('#native-020-act').isDisabled(),'ACT_TICKET_NOT_SPENT');
  ok(await page.locator('#native-020-export').isEnabled(),'SIGNED_WITNESS_DOWNLOAD_NOT_AVAILABLE');
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#native-020-export').click()]);
  ok(download.suggestedFilename()==='stack-squared-020-native-ghot-signed-act.json',
    'DOWNLOAD_NOT_NATIVE_020');
  const witness=JSON.parse((await (await import('node:fs/promises')).readFile(await download.path())).toString('utf8'));
  ok(witness.status==='EXECUTED_AND_LOCAL_RECEIPT_VERIFIED'&&
    witness.receipt?.ticket_spent===true&&
    witness.native_ghot_030_signature_verified===true&&
    witness.branch_program_executed===false&&witness.receiver_admitted===false,
    'NATIVE_RECEIPT_SEMANTICS_CHANGED');
  // The receiving-world allowlist is authored OUTSIDE Workbench, after
  // the native receipt exists; 020 ACT cannot create crossing permission.
  const recipientPolicy={
    schema:'workbench.stack2-021-receiver-policy/v0',
    reviewed_for_local_hold:true,disposition:'HOLD',
    allowed_ticket_id:witness.ticket_id,
    allowed_receipt_id:witness.receipt_id,
    allowed_ghot_signer:witness.body_signer_particular,
    receiver_world:'world:stack2-021-chromium',
    receiver_particular:'particular:independent-chromium-receiver',
    receiver_contract:'contract:chromium-hold-only/v0'
  };
  writeFileSync(join(receiver,'stack-floor-021-inbox-policy.json'),
    JSON.stringify(recipientPolicy,null,2)+'\n');
  await page.waitForFunction(()=>document.getElementById('postoffice-021-state').textContent.includes('CONFIGURED'));
  await page.locator('#postoffice-021-ticket').fill(witness.ticket_id);
  await page.waitForFunction(()=>!document.getElementById('postoffice-021-preview').disabled);
  await page.locator('#postoffice-021-preview').click();
  await page.waitForFunction(()=>document.getElementById('postoffice-021-result').textContent.includes('GHoT original signature verified'));
  ok(await page.locator('#postoffice-021-cross').isDisabled(),
    'CROSS_SHOULD_REQUIRE_SEPARATE_CONSENT');
  await page.locator('#postoffice-021-ack').check();
  await page.locator('#postoffice-021-phrase').fill('CROSS');
  ok(await page.locator('#postoffice-021-cross').isEnabled(),'EXPLICIT_CROSS_NOT_ARMED');
  await page.locator('#postoffice-021-cross').click();
  await page.waitForFunction(()=>document.getElementById('postoffice-021-result').textContent.includes('RECEIVED → HOLD'),null,{timeout:60000});
  ok(await page.locator('#postoffice-021-cross').isDisabled(),'CROSS_CONSENT_NOT_SPENT');
  ok(await page.locator('#postoffice-021-export').isEnabled(),'SIGNED_HOLD_WITNESS_NOT_AVAILABLE');
  const [crossDownload]=await Promise.all([
    page.waitForEvent('download'),page.locator('#postoffice-021-export').click()
  ]);
  ok(crossDownload.suggestedFilename()==='stack-squared-021-signed-received-hold.json',
    'WRONG_CROSSING_DOWNLOAD_NAME');
  const receiptBundle=JSON.parse((await (await import('node:fs/promises')).readFile(
    await crossDownload.path())).toString('utf8'));
  ok(receiptBundle.status==='RECEIVED_AND_HELD'&&
    receiptBundle.ghot_signature_verified===true&&
    receiptBundle.relatte_signatures_verified===3&&
    receiptBundle.native_signed_receive_receipt?.kind==='RECEIVED'&&
    receiptBundle.native_signed_hold_receipt?.kind==='R3_HOLD'&&
    receiptBundle.receiver_admitted===false&&
    receiptBundle.foreign_admission_authorized===false,
    'NATIVE_CROSSING_NOT_SOVEREIGN_HOLD');
  const out=process.env.STACK2_BROWSER_OUTPUT||'/tmp/stack-floor-021-chromium';
  mkdirSync(out,{recursive:true});
  await page.screenshot({path:join(out,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:join(out,'mobile.png'),fullPage:true});
  ok(await page.evaluate(()=>document.documentElement.scrollWidth)<=400,'MOBILE_HORIZONTAL_OVERFLOW');
  ok(errors.length===0,'BROWSER_RUNTIME_ERRORS: '+errors.join(';'));
  console.log(JSON.stringify({status:'STACK_SQUARED_021_REAL_CHROMIUM_CROSSING_HOLD_PASSED',
    original_ghot_signed_act:true,separate_one_use_cross:true,
    original_relatte_signed_crossing:true,receiver_signed_hold:true,
    signatures_cold_verified:3,receiver_admitted:false,
    desktop_mobile:true,page_errors:0}));
  await ctx.close();
}finally{
  if(browser)await browser.close();
  server.kill('SIGTERM');
  rmSync(home,{recursive:true,force:true});
}
