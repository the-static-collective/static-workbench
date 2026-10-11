import test from 'node:test';
import assert from 'node:assert/strict';
import {makePocketSeed,seedJson,MODES} from '../static_workbench/web/stack-floor-pocket-seed-025-core.mjs';
const crossing=x=>'relatte-crossing-v0:'+x.repeat(64);
const move=x=>'candidate-move:sha256:'+x.repeat(64);
function originalFixture(){
  const card={
    slot:0,kind:'expand',available:true,suggested_only:true,
    original_toaster_move_address:move('a'),
    source_crossing_ids:[crossing('b'),crossing('c')],
    title:'THE MAGNIFYING GLASS',prompt:'Look closer before inventing anything.',
    from_source_world:'world:ci-one',to_source_world:'world:ci-two',
    declared_evidence:[{
      lens:'content',kind:'SAME_DECLARED_PAYLOAD_ADDRESS',
      value:'sha256:'+'d'.repeat(64),
      meaning:'Declared in two signed wrappers, bytes not retrieved.'
    }],source_material_loaded:false,receiver_admitted:false
  };
  const cards=[card,...Array.from({length:5},(_,i)=>({slot:i+1,available:false}))];
  const preview={
    schema:'workbench.stack2-024-toaster-delight-preview/v0',
    original_toaster_policy:'candidate-move-deck/v1',
    original_toaster_commit:'74365daa3351555d17482662a9a13cc6a316f1e1',
    selected_relation_proposal_id:'proposal-023:'+'e'.repeat(64),
    receiver_state_ref:'relatte-local-state-v0:'+'f'.repeat(64),
    original_toaster_deal_address:'candidate-move-deal:sha256:'+'2'.repeat(64),
    original_toaster_renderer_executed:false,
    original_toaster_source_media_loaded:false,
    original_receiver_changed:false,creative_output_authorized:false,
    source_bytes_read:false,native_relatte_signatures_verified:true,
    source_claims_independently_verified:false,
    relations_persisted:false,admissions_performed:0,
    human_selection_inferred:false,cards
  };
  return {preview,card};
}
test('one selected source-bound Toaster proposal creates a useful, bounded, deterministic pocket seed',async()=>{
  const input=originalFixture();
  const x=await makePocketSeed(input);
  const y=await makePocketSeed(input);
  assert.deepEqual(x,y);
  assert.match(x.manifest.seed_id,/^pocket-seed-025:[a-f0-9]{64}$/);
  assert.equal(x.manifest.original_toaster_move_address,input.card.original_toaster_move_address);
  assert.equal(x.manifest.receiver_state_ref,input.preview.receiver_state_ref);
  assert.deepEqual(x.manifest.source_crossing_ids,input.card.source_crossing_ids);
  assert.equal(x.manifest.boundaries.payload_permission_granted,false);
  assert.equal(x.manifest.boundaries.reproduction_rights_inferred,false);
  assert.equal(x.manifest.boundaries.receiver_admitted,false);
  assert.equal(x.manifest.boundaries.artifact_signed,false);
  assert.equal(x.manifest.boundaries.source_bytes_read,false);
  assert.equal(x.manifest.boundaries.original_toaster_renderer_executed,false);
  assert.match(x.text,/AN OBSERVATION WORTH KEEPING/);
  assert.match(x.text,/The bytes have not been fetched/i);
  assert.match(x.text,/HOLD ≠ ADMIT/);
  assert.ok(new TextEncoder().encode(x.text).length<3800);
  assert.match(x.svg,/data-schema="workbench.stack2-025-unsigned-pocket-seed\/v0"/);
  assert.match(x.svg,/NOT A QR CODE/);
  assert.match(x.svg,/UNSIGNED/);
  assert.match(seedJson(x),/source_world_labels/);
});
test('three purpose modes yield different reproducible words and distinct seed IDs, not source facts',async()=>{
  const input=originalFixture(),out=[];
  for(const mode of MODES){
    const v=await makePocketSeed(input,{mode});
    assert.equal(v.manifest.mode,mode);
    assert.equal(v.manifest.declared_evidence.declared_value,input.card.declared_evidence[0].value);
    assert.equal(v.manifest.boundaries.source_bytes_read,false);
    out.push(v);
  }
  assert.equal(new Set(out.map(x=>x.manifest.seed_id)).size,3);
  assert.deepEqual(MODES,['field-note','open-door','composer-seed']);
  assert.match(out[1].text,/A DOOR LEFT GENTLY OPEN/);
  assert.match(out[2].text,/A TINY COMPOSITION BRIEF/);
});
test('a single changed receipt state or original Toaster move changes identity; no false source history merge',async()=>{
  const a=originalFixture(),b=originalFixture();
  b.preview.receiver_state_ref='relatte-local-state-v0:'+'1'.repeat(64);
  assert.notEqual((await makePocketSeed(a)).manifest.seed_id,
    (await makePocketSeed(b)).manifest.seed_id);
  const c=originalFixture();
  c.card.original_toaster_move_address=move('8');
  assert.notEqual((await makePocketSeed(a)).manifest.seed_id,
    (await makePocketSeed(c)).manifest.seed_id);
});
test('refuse forged authority, stale choice, absent evidence, unsupported input',async()=>{
  for(const mutate of [
    x=>{x.preview.native_relatte_signatures_verified=false;},
    x=>{x.preview.original_toaster_renderer_executed=true;},
    x=>{x.preview.source_bytes_read=true;},
    x=>{x.preview.original_receiver_changed=true;},
    x=>{x.preview.creative_output_authorized=true;},
    x=>{x.preview.cards[0]={...x.card};},
    x=>{x.card.available=false;},
    x=>{x.card.declared_evidence=[];},
    x=>{x.card.source_crossing_ids=[crossing('b'),'notsigned'];},
    x=>{x.card.to_source_world=null;},
    x=>{x.preview.original_toaster_commit='main';},
  ]){
    const input=originalFixture();mutate(input);
    await assert.rejects(makePocketSeed(input),/BOUNDARY|NO_VERIFIED|CARD_|EVIDENCE|POINTERS|PAIR_/);
  }
  await assert.rejects(makePocketSeed(originalFixture(),{mode:'auto-publish'}),/UNKNOWN_SEED_FORMAT/);
});
test('untrusted source labels are escaped by pure SVG composition, never treated as HTML instructions',async()=>{
  const input=originalFixture();
  input.card.prompt='Please <script>alert("hello")</script> & publish';
  input.card.declared_evidence[0].value='</svg><script>alert("evil")</script>';
  const packet=await makePocketSeed(input);
  assert.equal(packet.svg.includes('<script'),false);
  assert.equal(packet.svg.includes('</svg><script>'),false);
  assert.equal(packet.manifest.boundaries.composition_local_only,true);
  assert.equal(packet.manifest.boundaries.human_identity_verified,false);
});
