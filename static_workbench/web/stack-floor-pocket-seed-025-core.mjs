/** STACK² 025: pure Pocket Seed maker.
 * Composes only bounded metadata already exposed by a native, source-pinned
 * 024 Toaster proposal. Never fetches sources, infers licenses or writes state.
 */
export const MODES=Object.freeze(['field-note','open-door','composer-seed']);
const KINDS=new Set(['expand','mutate','converge','stomp','cross']);
const CROSS=/^relatte-crossing-v0:[a-f0-9]{64}$/;
const PROPOSAL=/^proposal-023:[a-f0-9]{64}$/;
const MOVE=/^candidate-move:sha256:[a-f0-9]{64}$/;
const bound=(v,n)=>typeof v==='string'&&v.length>0&&v.length<=n;
const requireTruth=(ok,why)=>{if(!ok)throw Error(why);};
const escape=(s)=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;');
const previewFlags=[
  ['original_toaster_renderer_executed',false],
  ['original_toaster_source_media_loaded',false],
  ['original_receiver_changed',false],
  ['creative_output_authorized',false],
  ['source_bytes_read',false],
  ['native_relatte_signatures_verified',true],
  ['source_claims_independently_verified',false],
  ['relations_persisted',false],
  ['admissions_performed',0],
  ['human_selection_inferred',false],
];
function validate(input,mode){
  const {preview,card}=input||{};
  requireTruth(MODES.includes(mode),'UNKNOWN_SEED_FORMAT');
  requireTruth(preview?.schema==='workbench.stack2-024-toaster-delight-preview/v0'&&
    preview.original_toaster_policy==='candidate-move-deck/v1'&&
    preview.original_toaster_commit==='74365daa3351555d17482662a9a13cc6a316f1e1'&&
    preview.selected_relation_proposal_id&&
    PROPOSAL.test(preview.selected_relation_proposal_id)&&
    bound(preview.receiver_state_ref,160)&&
    /^candidate-move-deal:sha256:[a-f0-9]{64}$/.test(preview.original_toaster_deal_address)&&
    Array.isArray(preview.cards)&&preview.cards.length===6,
    'NO_VERIFIED_ORIGINAL_TOASTER_PREVIEW');
  for(const [field,value] of previewFlags)
    requireTruth(preview[field]===value,'TOASTER_PERMISSION_BOUNDARY_INVALID');
  requireTruth(card&&Number.isInteger(card.slot)&&card.slot>=0&&card.slot<6&&
    card.available===true&&card.suggested_only===true&&
    KINDS.has(card.kind)&&MOVE.test(card.original_toaster_move_address)&&
    card.source_material_loaded===false&&card.receiver_admitted===false&&
    preview.cards[card.slot]===card, 'CARD_NOT_SELECTED_FROM_CURRENT_DEAL');
  requireTruth(Array.isArray(card.source_crossing_ids)&&
    card.source_crossing_ids.length>=1&&card.source_crossing_ids.length<=2&&
    card.source_crossing_ids.every(x=>typeof x==='string'&&CROSS.test(x))&&
    new Set(card.source_crossing_ids).size===card.source_crossing_ids.length,
    'INVALID_SOVEREIGN_SOURCE_POINTERS');
  requireTruth(bound(card.title,160)&&bound(card.prompt,240)&&
    bound(card.from_source_world,320)&&
    (card.to_source_world==null||bound(card.to_source_world,320))&&
    Array.isArray(card.declared_evidence)&&card.declared_evidence.length>=1&&
    card.declared_evidence.length<=8,'MISSING_EXPLAINABLE_EVIDENCE');
  requireTruth(card.declared_evidence.every(x=>x&&
    ['origin','lineage','structure','content','arrival'].includes(x.lens)&&
    bound(x.kind,128)&&bound(x.value,512)&&bound(x.meaning,512)),
    'UNBOUNDED_SOURCE_DECLARATION');
  requireTruth(card.source_crossing_ids.length===(card.to_source_world==null?1:2),
    'CARD_PAIR_NOT_BOUND_TO_NAMES');
  return {preview,card};
}
const modeWords={
  'field-note':{
    heading:'AN OBSERVATION WORTH KEEPING',
    verb:'Notice',
    intro:'Two source-addressed particulars sit on the receiver shelf. Their original histories stay separate.',
    nudge:'What observation could disprove or refine the apparent connection?'
  },
  'open-door':{
    heading:'A DOOR LEFT GENTLY OPEN',
    verb:'Invite',
    intro:'Here is one small question worth sharing, but no one is being asked to surrender their history.',
    nudge:'Would anyone like to explore this declared connection without opening either source?'
  },
  'composer-seed':{
    heading:'A TINY COMPOSITION BRIEF',
    verb:'Imagine',
    intro:'Compose an original response to this metadata-only clue, not a quotation or recreation of unseen material.',
    nudge:'What completely new, independently authored miniature might this clue inspire?'
  }
};
const specific={
  content:'Both signed envelopes declare a matching payload address; the bytes have not been fetched.',
  lineage:'Both envelopes declare the same source-history reference; their actual ancestry is not established.',
  origin:'Both signed envelopes share a declared source label; human identity and ownership remain unverified.',
  structure:'Both signed envelopes share a declared structural label; compatible execution is not implied.',
  arrival:'These entries arrived next to each other in the receiver journal; proximity does not establish a relation.'
};
const fold=(s,limit)=>{
  const words=String(s).trim().split(/\s+/),lines=[];let line='';
  for(const w of words){
    if(line&&(line+' '+w).length>limit){lines.push(line);line=w;}else line=(line+' '+w).trim();
  }if(line)lines.push(line);
  return lines;
};
const svgText=(text,x,y,size=25,color='#283e33',weight=400)=>'<text x="'+x+'" y="'+y+
  '" font-family="Georgia, serif" font-size="'+size+'" fill="'+color+
  '" font-weight="'+weight+'">'+escape(text)+'</text>';
const sha=async(source)=>{
  requireTruth(globalThis.crypto?.subtle,'WEBCRYPTO_NOT_AVAILABLE');
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(source));
  return [...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
};
function sigil(hex){
  const cells=[],coords=new Set();
  for(let y=0;y<9;y++)for(let x=0;x<5;x++){
    const k=(y*5+x)%64;const lit=(parseInt(hex[k],16)&2)!==0;
    if(lit){coords.add(x+','+y);coords.add((8-x)+','+y);}
  }
  for(const pair of coords){const [x,y]=pair.split(',').map(Number);
    cells.push('<rect x="'+(618+x*26)+'" y="'+(174+y*26)+
      '" width="20" height="20" rx="4" fill="#45634c"/>');
  }
  return cells.join('');
}
function svgFor(packet,hash){
  const {manifest}=packet;const prose=manifest.composition;
  const id=manifest.seed_id;
  const introLines=fold(prose.observation,59).slice(0,3);
  const questionLines=fold(prose.question,62).slice(0,3);
  let y=225;
  const intro=introLines.map(x=>{const l=svgText(x,56,y,20);y+=32;return l;}).join('');
  y=395;
  const question=questionLines.map(x=>{const l=svgText(x,56,y,19,'#6c4f32');y+=30;return l;}).join('');
  return '<?xml version="1.0" encoding="UTF-8"?>\n'+
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 970 610" width="970" height="610" '+
    'role="img" aria-labelledby="pocket-title pocket-desc" '+
    'data-schema="workbench.stack2-025-unsigned-pocket-seed/v0" '+
    'data-seed-id="'+id+'" data-source-bytes-read="false" data-receiver-admitted="false">'+
    '<title id="pocket-title">'+escape(prose.heading)+'</title>'+
    '<desc id="pocket-desc">'+escape(prose.observation)+' '+escape(prose.question)+'</desc>'+
    '<rect width="970" height="610" rx="22" fill="#ecedd8"/>'+
    '<rect x="22" y="22" width="926" height="566" rx="15" fill="#f7f2e2" stroke="#a8ae91" stroke-width="2"/>'+
    '<path d="M 52 150 Q 230 110 390 146 T 562 139" stroke="#93a48b" stroke-width="3" fill="none" stroke-dasharray="6 10"/>'+
    svgText('STATIC / POCKET SEED 025',56,84,23,'#45634c',700)+
    svgText(prose.heading,56,147,31,'#283e33',700)+
    svgText('OBSERVATION',56,192,15,'#61765c',700)+intro+
    svgText('OPEN QUESTION',56,361,15,'#977351',700)+question+
    '<rect x="607" y="152" width="272" height="275" rx="11" fill="#e0e6d4" stroke="#92a98a"/>'+
    sigil(hash)+svgText('NOT A QR CODE',630,456,13,'#70866f')+
    svgText('PROVENANCE · '+hash.slice(0,18),56,506,18,'#4f6756')+
    svgText('UNSIGNED · DECLARATIONS ONLY · NO ADMISSION',56,551,15,'#865f43',700)+
    '</svg>\n';
}
export async function makePocketSeed(input,{mode='field-note'}={}){
  const {preview,card}=validate(input,mode);
  const chosen=card.declared_evidence.find(e=>e.lens!=='arrival')||card.declared_evidence[0];
  const copy=modeWords[mode],obs=specific[chosen.lens];
  const evidence={
    lens:chosen.lens,kind:chosen.kind,
    declared_value:chosen.value,meaning:chosen.meaning,
  };
  const core={
    schema:'workbench.stack2-025-pocket-seed/v0',
    mode,
    receiver_state_ref:preview.receiver_state_ref,
    source_crossing_ids:[...card.source_crossing_ids],
    source_world_labels:[card.from_source_world,
      ...(card.to_source_world?[card.to_source_world]:[])],
    original_relation_proposal_id:preview.selected_relation_proposal_id,
    original_toaster_commit:preview.original_toaster_commit,
    original_toaster_move_address:card.original_toaster_move_address,
    original_toaster_deal_address:preview.original_toaster_deal_address,
    declared_evidence:evidence,
    composition:{
      heading:copy.heading,
      invitation:card.prompt,
      observation:obs,
      question:copy.nudge,
      creator_move:copy.verb,
    },
    boundaries:{
      artifact_signed:false,source_envelope_signatures_cold_verified_by_workbench:true,
      human_identity_verified:false,donor_claims_verified:false,
      source_bytes_read:false,payload_permission_granted:false,
      reproduction_rights_inferred:false,relationship_accepted:false,
      original_receiver_mutated:false,receiver_admitted:false,
      original_toaster_renderer_executed:false,
      composition_local_only:true,created_from_declared_metadata_only:true
    },
  };
  const hash=await sha('STACK-SQUARED-025|'+JSON.stringify(core));
  const manifest={...core,seed_id:'pocket-seed-025:'+hash};
  const display=[copy.heading,'',copy.intro,'',
    'OBSERVATION',obs,'',
    'DECLARED MATCH',chosen.kind+' · '+chosen.value,'',
    'THE QUESTION',copy.nudge,'',
    'PROVENANCE',manifest.seed_id,
    'Toaster move: '+card.original_toaster_move_address,
    'Receiver state: '+preview.receiver_state_ref,
    'Source particulars: '+card.source_crossing_ids.join(' | '),'',
    'BOUNDARY: UNSIGNED · DECLARED METADATA ONLY · NO PAYLOAD CONTENT',
    'HOLD ≠ ADMIT · INSPIRATION ≠ AUTHORITY'
  ].join('\n')+'\n';
  requireTruth(new TextEncoder().encode(display).length<=3800,
    'SEED_TEXT_BUDGET_EXCEEDED');
  const packet={manifest,text:display};
  return {...packet,svg:svgFor(packet,hash)};
}
export function seedJson(packet){
  requireTruth(packet?.manifest?.schema==='workbench.stack2-025-pocket-seed/v0',
    'NO_VALID_POCKET_SEED');
  return JSON.stringify(packet.manifest,null,2)+'\n';
}
