#!/usr/bin/env node
/** STACK² 024. Invoke the ORIGINAL pinned Haunted Toaster Candidate Move Deck.
 * The inputs are analogical, NOT Toaster media candidates or permissions.
 */
const fs=require('node:fs');
const path=require('node:path');
const [checkout]=process.argv.slice(2);
const fail=(ok,code)=>{if(!ok)throw Error(code)};
try{
  fail(process.argv.length===3&&path.isAbsolute(checkout),'FIXED_PINNED_TOASTER_ONLY');
  const input=JSON.parse(fs.readFileSync(0,'utf8'));
  fail(input?.schema==='workbench.stack2-024-bridge/v0'&&
       typeof input.state_ref==='string'&&input.state_ref.length<160&&
       Number.isInteger(input.selected_index)&&input.selected_index>=0&&
       Number.isInteger(input.deal_index)&&input.deal_index>=0&&input.deal_index<=8&&
       Array.isArray(input.candidates)&&
       input.candidates.length>=2&&input.candidates.length<=60,
       'INVALID_NATIVE_TOASTER_INPUT');
  const ids=new Set();
  const candidates=input.candidates.map((x,index)=>{
    fail(typeof x.crossing_id==='string'&&
      /^relatte-crossing-v0:[a-f0-9]{64}$/.test(x.crossing_id)&&
      x.index===index&&!ids.has(x.crossing_id)&&
      typeof x.source_world==='string'&&x.source_world.length<=300,
      'UNBOUND_SOURCE_PARTICULAR');
    ids.add(x.crossing_id);
    return {
      index,scoreAddress:'shelf-particular:'+x.crossing_id,
      signature:x.source_world,
      // These are only non-creative provenance metadata, not actual Toaster scores.
      toastmoodLane:null,crossLockProjection:null
    };
  });
  const deck=require(path.join(checkout,
    'src/full-measure/src/renderer/candidate-move-deck.js'));
  fail(deck.MOVE_DECK_POLICY==='candidate-move-deck/v1'&&
    typeof deck.dealCandidateMoves==='function','NOT_ORIGINAL_TOASTER_MOVE_DECK');
  const dealt=deck.dealCandidateMoves({
    familyHash:'held-receiver-state:'+input.state_ref,
    candidates,selectedIndex:input.selected_index,
    dealIndex:input.deal_index,locks:[]
  });
  fail(dealt.policy==='candidate-move-deck/v1'&&
    dealt.proposals.length===6&&
    dealt.proposals.map(x=>x.kind).join('|')===
      'expand|mutate|converge|stomp|cross|cross',
    'TOASTER_NATIVE_DECK_NOT_SIX_MOVES');
  const allowed=new Set(candidates.map(x=>x.index));
  for(const p of dealt.proposals){
    fail(['mutate','stomp','cross'].includes(p.action)&&
      ['expand','mutate','converge','stomp','cross'].includes(p.kind)&&
      typeof p.address==='string'&&
      p.address.startsWith('candidate-move:sha256:')&&
      (p.parentIndex==null||p.parentIndex===input.selected_index)&&
      (p.parentIndexes==null||
       (Array.isArray(p.parentIndexes)&&p.parentIndexes.length===2&&
         p.parentIndexes[0]===input.selected_index&&
         allowed.has(p.parentIndexes[1]))),
      'TOASTER_NATIVE_PROPOSAL_OUTSIDE_RECEIVER_SET');
  }
  console.log(JSON.stringify({
    schema:'workbench.stack2-024-original-toaster-output/v0',
    original_toaster_policy:dealt.policy,
    original_toaster_deal_address:dealt.dealAddress,
    original_toaster_deal_index:dealt.dealIndex,
    original_toaster_proposals:dealt.proposals,
    original_toaster_source_media_loaded:false,
    original_toaster_renderer_executed:false,
    receiver_state_unchanged:true,
    additional_work_authorized:false
  }));
}catch(err){console.error('TOASTER_HOLD: '+String(err?.message??err).slice(0,160));process.exitCode=2;}
