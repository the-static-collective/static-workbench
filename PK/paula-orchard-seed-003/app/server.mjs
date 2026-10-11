import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const __dirname=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(__dirname,'..');
const host='127.0.0.1', port=3333;
const read=(p)=>fs.readFileSync(path.join(root,p),'utf8');
const send=(res,status,body,type='application/json; charset=utf-8')=>{res.writeHead(status,{'content-type':type,'cache-control':'no-store'});res.end(body)};
const slug=s=>String(s||'story').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,50)||'story';
const stamp=()=>new Date().toISOString().replace(/[:.]/g,'-');
const body=async req=>{let x=''; for await(const c of req) x+=c; return x;};

http.createServer(async(req,res)=>{
  try{
    if(req.method==='GET' && req.url==='/'){ return send(res,200,read('app/index.html'),'text/html; charset=utf-8'); }
    if(req.method==='GET' && req.url==='/project-instructions'){ return send(res,200,read('CHATGPT_PROJECT_INSTRUCTIONS.md'),'text/plain; charset=utf-8'); }
    if(req.method==='POST' && req.url==='/api/storydrop'){
      const data=JSON.parse(await body(req));
      const trace=String(data.trace||'').trim(); if(!trace) return send(res,400,JSON.stringify({error:'empty storydrop'}));
      const title=String(data.title||trace.split(/\n/)[0]).slice(0,80);
      const id=`${new Date().toISOString().slice(0,10)}-${slug(title)}`;
      const rel=`inbox/${id}--${stamp().slice(11,19)}.md`;
      const content=`# STORYDROP — ${title}\n\n- id: ${id}\n- captured: ${new Date().toISOString()}\n- status: raw-trace\n\n## Raw trace\n\n${trace}\n`;
      fs.writeFileSync(path.join(root,rel),content);
      const prompt=read('prompts/storydrop-packet.md').replace('{{STORYDROP}}',trace)+`\n\nTRACE REF: ${rel}\nSUGGESTED STORY ID: ${id}\n`;
      return send(res,200,JSON.stringify({id,trace_ref:rel,prompt}));
    }
    if(req.method==='POST' && req.url==='/api/storycard'){
      const raw=await body(req); let card; try{card=JSON.parse(raw)}catch{return send(res,400,JSON.stringify({error:'invalid JSON'}));}
      if(!card.id || !card.schema) return send(res,400,JSON.stringify({error:'card needs id and schema'}));
      const rel=`stories/${slug(card.id)}.json`; fs.writeFileSync(path.join(root,rel),JSON.stringify(card,null,2)+'\n');
      return send(res,200,JSON.stringify({saved:rel}));
    }
    if(req.method==='POST' && req.url==='/api/flow'){
      const data=JSON.parse(await body(req));
      const rel=String(data.story_ref||''); const full=path.resolve(root,rel);
      if(!full.startsWith(root) || !fs.existsSync(full)) return send(res,404,JSON.stringify({error:'story card not found'}));
      const card=JSON.parse(fs.readFileSync(full,'utf8')); const lines=[`# FLOW BATCH — ${card.title||card.id}`,''];
      if(card.character_ingredients?.length){lines.push('## Ingredient cards',''); for(const c of card.character_ingredients) lines.push(`- **${c.id} — ${c.label}**: ${c.visual_card}`); lines.push('');}
      lines.push('## Shots','');
      for(const s of card.shots||[]){lines.push(`### ${s.id} — ${s.class} — ${s.duration_s}s — ${s.aspect_ratio||'9:16'}`,s.continuity_reference?`Continuity: ${s.continuity_reference}`:'',s.dialogue?`Dialogue: ${s.dialogue}`:'',s.voiceover?`VO: ${s.voiceover}`:'',s.sound_note?`Sound: ${s.sound_note}`:'','',s.flow_prompt||'[MISSING flow_prompt]','');}
      const out=`generated/boards/${slug(card.id)}--flow.md`; fs.writeFileSync(path.join(root,out),lines.filter(x=>x!==undefined).join('\n'));
      return send(res,200,JSON.stringify({saved:out,text:lines.join('\n')}));
    }
    return send(res,404,JSON.stringify({error:'not found'}));
  }catch(e){return send(res,500,JSON.stringify({error:e.message}));}
}).listen(port,host,()=>console.log(`Paula Story Desk: http://${host}:${port}`));
