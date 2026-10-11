import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {init,propose,review,authorize,perform,compose} from '../orchard-kernel.mjs';
const temp=t=>{const root=fs.mkdtempSync(path.join(os.tmpdir(),'paula-orchard-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));fs.mkdirSync(path.join(root,'stories'));fs.writeFileSync(path.join(root,'stories','little-film.txt'),'Paula owns the story.');return root;};
const request=(r,overrides={})=>propose(r,{source:'stories/little-film.txt',effect:'keep_local',purpose:'Keep selected fictional film locally',...overrides});
const consent=(p,overrides={})=>({actor:'Paula (declared, not verified)',ack:`I APPROVE ${p.source_sha256.slice(0,12)} ${p.effect}`,rightsConfirmed:true,...overrides});

test('private by default: a local keep is proposed, explicitly approved, single-use, and receipted',t=>{
  const r=temp(t);const p=request(r);assert.equal(p.authority,'none');
  assert.throws(()=>perform(r,p.id),/ENOENT/);assert.equal(review(r,p.id).unchanged,true);
  assert.throws(()=>authorize(r,p.id,consent(p,{ack:'I approve anything'})),/exact content-bound/);
  authorize(r,p.id,consent(p));const out=perform(r,p.id);
  assert.equal(out.status,'KEPT_LOCAL');assert.equal(out.external_transfer,false);
  assert.equal(fs.readFileSync(path.join(r,out.relative_output),'utf8'),'Paula owns the story.');
  assert.throws(()=>perform(r,p.id),/consumed/);assert.throws(()=>authorize(r,p.id,consent(p)),/cannot be approved twice|consumed/);
});
test('content changes invalidate an earlier proposal and approval',t=>{
  const r=temp(t);const p=request(r);fs.writeFileSync(path.join(r,'stories','little-film.txt'),'Different film');
  assert.equal(review(r,p.id).unchanged,false);assert.throws(()=>authorize(r,p.id,consent(p)),/source changed/);
  fs.writeFileSync(path.join(r,'stories','little-film.txt'),'Paula owns the story.');authorize(r,p.id,consent(p));
  fs.writeFileSync(path.join(r,'stories','little-film.txt'),'Different film');assert.throws(()=>perform(r,p.id),/source or approval mismatch|source changed/);
});
test('privacy, permission, and effect fences refuse unapproved sharing',t=>{
  const r=temp(t);
  assert.throws(()=>request(r,{effect:'stage_public',destination:'social profile'}),/private material/);
  assert.throws(()=>request(r,{effect:'stage_public',visibility:'shareable'}),/destination/);
  assert.throws(()=>request(r,{effect:'send_email'}),/unsupported effect/);
  assert.throws(()=>request(r,{effect:'spend'}),/unsupported effect/);
  const p=request(r,{effect:'stage_public',visibility:'shareable',destination:'Paula social account'});
  assert.throws(()=>authorize(r,p.id,consent(p,{rightsConfirmed:false})),/rights and consent/);
  authorize(r,p.id,consent(p));const rec=perform(r,p.id);
  assert.equal(rec.status,'STAGED_LOCALLY_NOT_SENT');assert.equal(rec.external_transfer,false);
  assert.match(rec.relative_output,/exports\/public/);
});
test('raw inbox and unsafe filesystem paths cannot become export sources',t=>{
  const r=temp(t);fs.mkdirSync(path.join(r,'inbox'));fs.writeFileSync(path.join(r,'inbox','trace.md'),'customer secret');
  assert.throws(()=>request(r,{source:'inbox/trace.md',effect:'stage_handoff',visibility:'private',destination:'Paula chat'}),/raw storydrops/);
  assert.throws(()=>request(r,{source:'inbox/trace.md',effect:'stage_handoff',visibility:'shareable',destination:'Paula chat'}),/raw storydrops/);
  for(const source of ['../customer.txt','stories/../../customer.txt','/etc/passwd','stories\\little-film.txt'])assert.throws(()=>request(r,{source}),/source outside|unsafe source/);
  fs.symlinkSync(path.join(r,'stories','little-film.txt'),path.join(r,'stories','link.txt'));
  assert.throws(()=>request(r,{source:'stories/link.txt'}),/symlink/);
});
test('capability references cannot become executable permission by composition',t=>{
  const r=temp(t);fs.copyFileSync(path.resolve('ORCHARD_CAPABILITIES.json'),path.join(r,'ORCHARD_CAPABILITIES.json'));
  const c=compose(r,['blender-dream','memento','loadout']);assert.equal(c.executable,false);assert.equal(c.status,'PLAN_ONLY');
  assert.ok(c.selection.every(x=>x.authority==='none'));
  assert.throws(()=>compose(r,['invented-auto-payment-adapter']),/unknown capability/);
});
test('initialize again cannot erase an earlier local receipt',t=>{
  const r=temp(t);let p=request(r);authorize(r,p.id,consent(p));const old=perform(r,p.id);init(r);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(r,'.orchard-private','receipts',p.id+'.json'))),old);
});
