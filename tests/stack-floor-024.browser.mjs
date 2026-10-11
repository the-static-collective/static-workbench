/** STACK² 024 — real Chrome original GHoT ACT, reLATTE HOLD, Mycelium, original Toaster deal and paper keepsake. */
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
  ' stack_floor_receiver_root=base/"receiver",',
  ' stack_floor_toaster_enabled=True,',
  ' stack_floor_toaster_checkout=Path(os.environ["STACK2_024_TOASTER_CHECKOUT"]))',
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
  // Native CROSS emits the observational shelf-refresh event. It must not
  // itself grant any shelf action or change the receiver's disposition.
  await page.waitForFunction(()=>
    document.getElementById('shelf-022-status').textContent.includes('ORIGINAL RECEIVER JOURNAL VALID'),
    null,{timeout:60000});
  await page.waitForFunction(()=>
    document.getElementById('shelf-022-count').textContent.includes('1 HELD'));
  ok(await page.locator('.shelf-slot').count()===1,'SHELF_MUST_SHOW_ONE_HELD_PARTICULAR');
  await page.locator('.shelf-slot').first().click();
  await page.waitForFunction(()=>
    document.getElementById('shelf-022-summary').textContent.includes('signatures checked'),
    null,{timeout:25000});
  ok((await page.locator('#shelf-022-details').innerText()).includes(
    'NOT_REVERIFIED_BY_SHELF'),'SHELF_MUST_NOT_AUTHENTICATE_DONOR_CLAIMS');
  ok((await page.locator('#shelf-022-details').innerText()).includes(
    receiptBundle.native_relatte_hold_receipt_id),'HOLD_RECEIPT_MUST_MATCH_CROSSING');
  const [inspectionDownload]=await Promise.all([
    page.waitForEvent('download'),page.locator('#shelf-022-export').click()
  ]);
  ok(inspectionDownload.suggestedFilename()==='stack-squared-022-hold-inspection-unsigned.json',
    'SHELF_INSPECTION_MUST_REMAIN_UNSIGNED');
  const shelfPacket=JSON.parse((await (await import('node:fs/promises')).readFile(
    await inspectionDownload.path())).toString('utf8'));
  ok(shelfPacket.inspection?.records?.[0]?.crossing_id===receiptBundle.crossing_id&&
    shelfPacket.signed_receipts_included===false&&
    shelfPacket.receiver_admission_authorized===false,
    'SHELF_MUST_NOT_PROMOTE_EVIDENCE_TO_AUTHORITY');
  // The additional specimens are an explicit, independently executed CI fixture.
  // Mycelium itself never creates, receives or admits any record.
  const syntheticSource=[
    "import {pathToFileURL} from 'node:url';",
    "const lib=await import(pathToFileURL(process.argv[1]+'/src/index.ts').href);",
    "const receiver=await lib.LocalReceiver.open(process.argv[2]);",
    "const now=Date.now();",
    "for(const i of [0,1]){",
    " const iso=n=>new Date(now+n*1000).toISOString();",
    " const spec={schema:'relatte.opaque-organ-spec/v0',",
    "  family_ref:'family:mycelium-browser-samples',",
    "  donor_contract_ref:'contract:ci-samples',",
    "  artifact_kind:'independent-signed-ci-specimen',",
    "  source_world:'world:ci-mycelium-two',",
    "  source_particular:'particular:ci-'+i,",
    "  source_history_head:'sha256:'+'f'.repeat(64),",
    "  payload_refs:[{address:'sha256:'+'e'.repeat(64),",
    "    role:'declared-ci-source',media_type:'application/octet-stream'}],",
    "  donor_claims:{synthetic:true,real_owner_authorized:false},",
    "  requested_effect:{kind:'candidate-ingress',execution_authorized:false},",
    "  return_address:null,created_at:iso(i*3)};",
    " const crossing=await lib.sealOpaqueOrganCrossing(spec,await lib.generateP256KeyPair());",
    " await receiver.receive(crossing,iso(i*3+1));",
    " await receiver.dispose(crossing.crossing_id,'HOLD',iso(i*3+2));",
    "}",
    "console.log(JSON.stringify(receiver.snapshot()));"
  ].join('\n');
  execFileSync('node',['--experimental-strip-types','--input-type=module','-e',
    syntheticSource,relatte,receiver],{cwd:relatte,timeout:35000});
  await page.waitForFunction(()=>
    document.getElementById('mycelium-023-status').textContent.includes('READY'));
  await page.locator('#mycelium-023-inspect').click();
  await page.waitForFunction(()=>
    document.getElementById('mycelium-023-status').textContent.includes('NATIVE HISTORY VERIFIED'),
    null,{timeout:45000});
  ok((await page.locator('#mycelium-023-nodes').innerText()).includes('3 HELD'),
    'MYCELIUM_MUST_CONTAIN_THREE_SIGNED_HELD_PARTICULARS');
  ok(await page.locator('.mycelium-node').count()===3,'VISUAL_PARTICULARS_NOT_GROWN');
  await page.locator('.mycelium-lenses button[data-lens="content"]').click();
  ok(await page.locator('.mycelium-thread').count()===1,
    'SHARED_SIGNED_POINTER_MUST_YIELD_ONE_ADDRESS_PROPOSAL');
  await page.locator('.mycelium-thread').first().click();
  ok((await page.locator('#mycelium-023-evidence').innerText())
    .includes('SAME DECLARED PAYLOAD ADDRESS'.toLowerCase())||
     (await page.locator('#mycelium-023-evidence').innerText())
    .includes('same declared payload address'),
    'EVIDENCE_NOT_EXPLAINED');
  ok(await page.locator('#mycelium-023-export').isEnabled(),
    'VISIBLE_RELATIONSHIP_QUESTION_MUST_BE_EXPORTABLE');
  const [questionDownload]=await Promise.all([
    page.waitForEvent('download'),page.locator('#mycelium-023-export').click()
  ]);
  ok(questionDownload.suggestedFilename()==='stack-squared-023-mycelium-question-unsigned.json',
     'PROPOSAL_MUST_EXPORT_AS_UNSIGNED_QUESTION');
  const myceliumPacket=JSON.parse((await (await import('node:fs/promises')).readFile(
    await questionDownload.path())).toString('utf8'));
  ok(myceliumPacket.schema==='workbench.stack2-023-unsigned-question/v0'&&
    myceliumPacket.persistent_relation_created===false&&
    myceliumPacket.user_selected_relation===false&&
    myceliumPacket.receiver_admitted===false&&
    myceliumPacket.donor_claims_independently_verified===false&&
    myceliumPacket.proposal.evidence.some(e=>e.kind==='SAME_DECLARED_PAYLOAD_ADDRESS'),
    'MYCELIUM_PROPOSAL_DID_NOT_PRESERVE_ITS_BOUNDARIES');
  // This is an actual original Toaster pure move-deck invocation, NOT a
  // video render. One evidenced Mycelium thread is currently selected above.
  await page.waitForFunction(()=>
    document.getElementById('delight-024-state').textContent.includes('OPTED IN'));
  await page.waitForFunction(()=>!document.getElementById('delight-024-deal').disabled);
  await page.locator('#delight-024-deal').click();
  await page.waitForFunction(()=>
    document.getElementById('delight-024-state').textContent.includes('VERIFIED'),
    null,{timeout:45000});
  ok(await page.locator('.delight-024-card').count()===6,'ORIGINAL_TOASTER_SIX_MOVES_NOT_VISIBLE');
  ok(await page.locator('.delight-024-card:disabled').count()===1,
    'MISSING_SIGNED_CROSS_EVIDENCE_SHOULD_REFUSE_ONE_MOVE');
  await page.locator('.delight-024-card:not(:disabled)').first().click();
  ok(await page.locator('#delight-024-export').isEnabled(),
    'LOCAL_POSTCARD_NOT_RENDERED');
  ok(await page.locator('#delight-024-paper svg').count()===1,
    'UNSIGNED_PAPER_PROVENANCE_PREVIEW_MISSING');
  const [postcardDownload]=await Promise.all([
    page.waitForEvent('download'),page.locator('#delight-024-export').click()
  ]);
  ok(postcardDownload.suggestedFilename()==='stack-squared-024-useful-delight-unsigned-postcard.svg',
    'POSTCARD_MUST_NOT_MASQUERADE_AS_MEDIA_RENDER');
  const postcard=(await (await import('node:fs/promises')).readFile(
    await postcardDownload.path())).toString('utf8');
  ok(postcard.includes('data-schema="workbench.stack2-024-unsigned-postcard/v0"')&&
    postcard.includes('data-admission-authorized="false"')&&
    postcard.includes('UNSIGNED / PREVIEW ONLY')&&
    postcard.includes('TOASTER MOVE'),
    'POSTCARD_MUST_RETAIN_PROVENANCE_AND_NONA UTHORITY'.replace(' ',''));
  await page.locator('#delight-024-again').click();
  await page.waitForFunction(()=>
    document.getElementById('delight-024-message').textContent.includes('Six source-bounded ideas'),
    null,{timeout:30000});
  const out=process.env.STACK2_BROWSER_OUTPUT||'/tmp/stack-floor-024-chromium';
  mkdirSync(out,{recursive:true});
  await page.screenshot({path:join(out,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:join(out,'mobile.png'),fullPage:true});
  ok(await page.evaluate(()=>document.documentElement.scrollWidth)<=400,'MOBILE_HORIZONTAL_OVERFLOW');
  ok(errors.length===0,'BROWSER_RUNTIME_ERRORS: '+errors.join(';'));
  console.log(JSON.stringify({status:'STACK_SQUARED_024_REAL_CHROMIUM_TOASTER_USEFUL_DELIGHT_PASSED',
    original_ghot_signed_act:true,separate_one_use_cross:true,
    original_relatte_signed_crossing:true,receiver_signed_hold:true,
    signatures_cold_verified:3,receiver_admitted:false,
    receiver_shelf_read_only:true,donor_claim_not_reverified:true,inspection_unsigned:true,mycelium_proposals_explained:true,lens_filters_verified:true,relationships_persisted:false,original_toaster_move_deck:true,postcard_unsigned:true,toaster_renderer_executed:false,desktop_mobile:true,page_errors:0}));
  await ctx.close();
}finally{
  if(browser)await browser.close();
  server.kill('SIGTERM');
  rmSync(home,{recursive:true,force:true});
}
