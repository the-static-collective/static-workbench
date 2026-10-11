import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const file=process.argv[2];
if(!file){ console.error('usage: npm run assemble -- stories/<story-card>.json'); process.exit(2); }
const card=JSON.parse(fs.readFileSync(file,'utf8'));
const clipDir=path.resolve('generated/clips',card.id);
const outDir=path.resolve('generated/assemblies');
fs.mkdirSync(outDir,{recursive:true});
const rows=[];
for(const s of card.shots||[]){
  const candidates=[`${s.id}.mp4`,`${s.id.toLowerCase()}.mp4`];
  const found=candidates.map(x=>path.join(clipDir,x)).find(fs.existsSync);
  if(found) rows.push(`file '${found.replaceAll("'","'\\''")}'`);
}
const manifest=path.join(outDir,`${card.id}--concat.txt`);
fs.writeFileSync(manifest,rows.join('\n')+'\n');
if(!rows.length){ console.log(`No named clips found. Put clips at ${clipDir}/S01.mp4 etc. Manifest created: ${manifest}`); process.exit(0); }
const ff=spawnSync('ffmpeg',['-version'],{stdio:'ignore'});
if(ff.error || ff.status!==0){ console.log(`ffmpeg not found. Manifest ready: ${manifest}\nUse Flow Scenebuilder tonight, or install ffmpeg later.`); process.exit(0); }
const out=path.join(outDir,`${card.id}.mp4`);
const r=spawnSync('ffmpeg',['-y','-f','concat','-safe','0','-i',manifest,'-c','copy',out],{stdio:'inherit'});
if(r.status!==0){ console.error('Fast concat failed; clips may have incompatible codecs. Use Flow Scenebuilder or re-encode before concat.'); process.exit(r.status||1); }
console.log(out);
