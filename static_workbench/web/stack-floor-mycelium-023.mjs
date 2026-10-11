/** STACK² 023 Mycelium Shelf.
 * All user interactions filter/read ephemeral relation proposals only.
 * No write endpoint, donor execution, receiver disposition or data persistence.
 */
const $=id=>document.getElementById(id);
const el=(tag,cls='',value='')=>{
  const x=document.createElement(tag);
  if(cls)x.className=cls;
  if(value)x.textContent=String(value);
  return x;
};
const NS='http://www.w3.org/2000/svg';
const svg=(tag,attrs={})=>{
  const x=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs))x.setAttribute(k,String(v));
  return x;
};
let enabled=false,session=null,field=null,waiting=false,sequence=0,
    lens='all',minimum=1,focusNode=null,selected=null;
const short=id=>id.slice(-9);
const say=s=>{$('mycelium-023-message').textContent=s;};
const position=(i,total)=>{
  // Deterministic phyllotaxis. No randomness, physics, or moving source items.
  const phi=i*2.399963229728653;
  const radius=total===1?0:Math.sqrt((i+.45)/total)*206;
  return {x:470+Math.cos(phi)*radius*1.65,y:240+Math.sin(phi)*radius*.95};
};
const titles={
  origin:'Origin',lineage:'Declared trace',structure:'Structure',
  content:'Shared address',arrival:'Arrival neighbor'
};
async function getField(){
  if(!session){
    const b=await fetch('/api/bootstrap',{credentials:'same-origin'});
    if(!b.ok)throw Error('LOCAL_WORKBENCH_SESSION_UNAVAILABLE');
    session=(await b.json()).session_token;
  }
  const res=await fetch('/api/stack-floor/mycelium/inspect',{
    method:'POST',credentials:'same-origin',
    headers:{'X-Workbench-Session':session,'Content-Type':'application/json',
      'Accept':'application/json'},
    body:'{}'
  });
  const x=await res.json();
  if(!res.ok)throw Error(typeof x.detail==='string'?x.detail:'RECEIVER_REFUSED_FIELD');
  if(x.schema!=='workbench.stack2-023-mycelium-proposals/v0'||
    x.native_relatte_signatures_cold_verified!==true||
    x.all_connections_are_proposals!==true||
    x.receiver_disposition_unchanged!==true||
    x.relationships_persisted!==false||
    x.receiver_admission_authorized!==false||
    x.source_claims_independently_verified!==false||
    x.write_operations!==0||!Array.isArray(x.nodes)||!Array.isArray(x.edges))
    throw Error('UNVERIFIED_RECEIVER_FIELD');
  return x;
}
function filtered(){
  if(!field)return [];
  return field.edges.filter(e=>{
    if(focusNode&&e.source_crossing_id!==focusNode&&
      e.target_crossing_id!==focusNode)return false;
    return e.evidence.filter(x=>lens==='all'||x.lens===lens).length>=minimum;
  });
}
function activeEvidence(e){
  return e.evidence.filter(x=>lens==='all'||x.lens===lens);
}
function layoutGraph(edges){
  const root=$('mycelium-023-graph');
  root.replaceChildren();
  if(!field)return;
  const positions=new Map(field.nodes.map((n,i)=>[n.crossing_id,position(i,field.nodes.length)]));
  const ring=svg('ellipse',{cx:470,cy:240,rx:344,ry:214,class:'mycelium-root'});
  root.append(ring);
  const drawing=edges.slice(0,180);
  const brightest=selected?.proposal_id;
  for(const e of drawing){
    const a=positions.get(e.source_crossing_id),b=positions.get(e.target_crossing_id);
    if(!a||!b)continue;
    const path=svg('path',{
      d:'M '+a.x+' '+a.y+' Q 470 240 '+b.x+' '+b.y,
      class:'mycelium-stem'+(brightest===e.proposal_id?' focused':'')
    });
    const label=svg('title');
    label.textContent=e.evidence_count+' matching declared facts. Proposal only.';
    path.append(label);
    root.append(path);
  }
  field.nodes.forEach((n,i)=>{
    const p=positions.get(n.crossing_id);
    const group=svg('g',{
      class:'mycelium-node'+(focusNode===n.crossing_id?' focused':''),
      role:'button',tabindex:'0',
      'aria-label':'Focus held particular '+(i+1)+': '+n.source_world
    });
    group.append(svg('circle',{cx:p.x,cy:p.y,r:field.nodes.length>27?14:18}));
    const t=svg('text',{x:p.x,y:p.y+5});
    t.textContent=String(i+1);
    group.append(t);
    const title=svg('title');
    title.textContent=n.crossing_id+' · '+n.source_world+' · HOLD';
    group.append(title);
    const choose=()=>{
      focusNode=focusNode===n.crossing_id?null:n.crossing_id;
      selected=null;
      render();
    };
    group.addEventListener('click',choose);
    group.addEventListener('keydown',e=>{
      if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}
    });
    root.append(group);
  });
  $('mycelium-023-graph-caption').textContent=
    'Only receiver-held particulars. '+edges.length+
    ' visible proposals ('+drawing.length+' threads drawn). '+
    (focusNode?'One particular focused; tap it again to see the whole field. ':
      'Tap a numbered island to focus its threads. ')+
    'Connections and distances are visual proposals, not measured certainty.';
}
function evidenceCard(item){
  const div=el('div','mycelium-evidence-item');
  div.append(el('strong','',titles[item.lens]+' · '+item.kind.replaceAll('_',' ').toLowerCase()));
  const value=el('code','',item.value);
  div.append(value,el('p','',item.meaning));
  return div;
}
function showSelection(edge){
  selected=edge;
  const name=$('mycelium-023-selected');
  const help=$('mycelium-023-context');
  const box=$('mycelium-023-evidence');
  box.replaceChildren();
  if(!edge){
    name.textContent='No thread selected';
    help.textContent='Choose a visible proposal. No relationship will be added to either history.';
    $('mycelium-023-export').disabled=true;
    return;
  }
  const nodes=field.nodes;
  const left=nodes.find(n=>n.crossing_id===edge.source_crossing_id);
  const right=nodes.find(n=>n.crossing_id===edge.target_crossing_id);
  const a=nodes.indexOf(left)+1,b=nodes.indexOf(right)+1;
  name.textContent='Particular '+a+' ↔ Particular '+b;
  help.textContent='A question supported by '+activeEvidence(edge).length+
    ' exact recorded match(es), not a selected or admitted relationship. '+short(edge.proposal_id);
  for(const item of activeEvidence(edge))box.append(evidenceCard(item));
  $('mycelium-023-export').disabled=false;
}
function renderList(edges){
  const list=$('mycelium-023-list');
  list.replaceChildren();
  $('mycelium-023-thread-count').textContent=edges.length+' MATCHING · '+
    Math.min(edges.length,40)+' LISTED';
  if(!edges.length){
    list.append(el('p','help','No recorded evidence under these lens settings. Empty space is a valid result.'));
    return;
  }
  const idToNumber=new Map(field.nodes.map((n,i)=>[n.crossing_id,i+1]));
  for(const edge of edges.slice(0,40)){
    const b=el('button','mycelium-thread');
    b.type='button';
    b.setAttribute('aria-pressed',String(selected?.proposal_id===edge.proposal_id));
    b.append(el('span','small','PROPOSAL · '+activeEvidence(edge).length+' DECLARED FACTS'),
      el('strong','','Particular '+idToNumber.get(edge.source_crossing_id)+
        ' ↔ '+idToNumber.get(edge.target_crossing_id)),
      el('span','small',activeEvidence(edge).map(x=>titles[x.lens]).filter(
        (x,i,a)=>a.indexOf(x)===i).join(' · ')),
      el('code','',short(edge.proposal_id)));
    b.addEventListener('click',()=>{selected=edge;render();});
    list.append(b);
  }
}
function render(){
  if(!field)return;
  const edges=filtered();
  if(selected&&!edges.some(e=>e.proposal_id===selected.proposal_id))selected=null;
  for(const b of $('mycelium-023-lenses').querySelectorAll('button[data-lens]')){
    b.setAttribute('aria-pressed',String(b.dataset.lens===lens));
  }
  $('mycelium-023-min-display').textContent=String(minimum);
  layoutGraph(edges);
  showSelection(selected);
  renderList(edges);
}
async function inspect(){
  if(waiting||!enabled)return;
  const seq=++sequence;waiting=true;selected=null;focusNode=null;
  $('mycelium-023-inspect').disabled=true;
  say('Cold replaying original receiver signatures, then comparing declared references…');
  try{
    const response=await getField();
    if(seq!==sequence)return;
    field=response;
    $('mycelium-023-status').textContent='PROPOSAL FIELD · NATIVE HISTORY VERIFIED';
    $('mycelium-023-nodes').textContent=response.included_held+
      (response.skipped_held?' / '+response.total_held:'')+' HELD';
    $('mycelium-023-edges').textContent=response.total_evidence_edges+
      ' POSSIBLE THREADS';
    render();
    say(response.edges.length+' bounded proposals read. '+
      (response.skipped_held||response.edges_truncated?
        'Field capped for inspection; not all nodes or edges displayed. ':'')+
      'Nothing was saved, selected for admission, or changed.');
  }catch(e){
    if(seq!==sequence)return;
    field=null;selected=null;
    $('mycelium-023-graph').replaceChildren();
    $('mycelium-023-list').replaceChildren(el('p','help','No verified field to display.'));
    $('mycelium-023-status').textContent='HOLD / RELATION INSPECTION REFUSED';
    $('mycelium-023-nodes').textContent='—';
    $('mycelium-023-edges').textContent='—';
    showSelection(null);
    say('HOLD: '+e.message);
  }finally{
    if(seq===sequence){waiting=false;$('mycelium-023-inspect').disabled=!enabled;}
  }
}
for(const b of $('mycelium-023-lenses').querySelectorAll('button[data-lens]')){
  b.addEventListener('click',()=>{lens=b.dataset.lens;selected=null;render();});
}
$('mycelium-023-min').addEventListener('input',e=>{
  minimum=Number(e.target.value);selected=null;render();
});
$('mycelium-023-inspect').addEventListener('click',inspect);
$('mycelium-023-export').addEventListener('click',()=>{
  if(!selected||!field||!filtered().some(x=>x.proposal_id===selected.proposal_id))return;
  const packet={
    schema:'workbench.stack2-023-unsigned-question/v0',
    state_ref:field.state_ref,
    proposal:selected,
    evidence_lens:lens,
    source_world:field.receiver_world,
    signed_artifacts_included:false,
    persistent_relation_created:false,
    user_selected_relation:false,
    receiver_admitted:false,
    donor_claims_independently_verified:false
  };
  const blob=new Blob([JSON.stringify(packet,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='stack-squared-023-mycelium-question-unsigned.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),800);
});
window.addEventListener('stack-floor:crossing-held',()=>{if(enabled&&field)inspect();});
async function init(){
  try{
    const response=await fetch('/api/stack-floor/mycelium/status',{credentials:'same-origin'});
    if(!response.ok)throw Error('STATUS_UNAVAILABLE');
    const value=await response.json();
    enabled=value.enabled===true&&value.proposals_only===true&&
      value.admission_api===false&&value.stored_relationships===false;
    $('mycelium-023-status').textContent=enabled?
      'READ-ONLY FIELD READY':'RECEIVER NOT CONFIGURED';
    say(enabled?'Inspect when ready. A relationship proposal can never move an item out of HOLD.':
      'Needs a locally configured receiving-world HOLD shelf.');
  }catch{enabled=false;$('mycelium-023-status').textContent='FIELD UNAVAILABLE';}
  $('mycelium-023-inspect').disabled=!enabled;
}
init();
