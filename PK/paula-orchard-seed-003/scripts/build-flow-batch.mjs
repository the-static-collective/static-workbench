import fs from 'node:fs';
import path from 'node:path';
const file=process.argv[2];
if(!file){ console.error('usage: npm run flow -- stories/<story-card>.json'); process.exit(2); }
const card=JSON.parse(fs.readFileSync(file,'utf8'));
if(!Array.isArray(card.shots) || !card.shots.length){ console.error('story card has no shots'); process.exit(2); }
const lines=[];
lines.push(`# FLOW BATCH — ${card.title || card.id}`,'');
if(card.character_ingredients?.length){
  lines.push('## Character / object ingredient cards','');
  for(const c of card.character_ingredients) lines.push(`- **${c.id} — ${c.label}**: ${c.visual_card}`);
  lines.push('');
}
lines.push('## Shots','');
for(const s of card.shots){
  lines.push(`### ${s.id} — ${s.class} — ${s.duration_s}s — ${s.aspect_ratio || '9:16'}`);
  if(s.continuity_reference) lines.push(`Continuity: ${s.continuity_reference}`);
  if(s.dialogue) lines.push(`Dialogue: ${s.dialogue}`);
  if(s.voiceover) lines.push(`VO: ${s.voiceover}`);
  if(s.sound_note) lines.push(`Sound: ${s.sound_note}`);
  lines.push('',s.flow_prompt || '[MISSING flow_prompt]','');
}
const out=path.resolve('generated/boards',`${card.id || 'story'}--flow.md`);
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,lines.join('\n'));
console.log(out);
