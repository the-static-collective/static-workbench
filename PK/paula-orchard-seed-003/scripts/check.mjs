import fs from 'node:fs';
import path from 'node:path';
const required=['README.md','CHATGPT_PROJECT_INSTRUCTIONS.md','prompts/storydrop-packet.md','templates/story-card.example.json'];
let ok=true;
for(const f of required){ if(!fs.existsSync(path.resolve(f))){ console.error('missing',f); ok=false; } }
for(const dir of ['inbox','stories','generated/boards','generated/clips']){ if(!fs.existsSync(path.resolve(dir))){ console.error('missing dir',dir); ok=false; } }
try{ JSON.parse(fs.readFileSync('templates/story-card.example.json','utf8')); }catch(e){ console.error('bad example json',e.message); ok=false; }
if(!ok) process.exit(1);
console.log('Paula Story Workbench check: OK');
