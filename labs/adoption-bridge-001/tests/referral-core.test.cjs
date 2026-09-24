"use strict";
const {readFileSync}=require("node:fs");
const {join}=require("node:path");
const {runInNewContext}=require("node:vm");
const {test}=require("node:test");
const assert=require("node:assert/strict");

const html=readFileSync(join(__dirname,"../index.html"),"utf8");
const begin=html.indexOf("function advanceCase(");
const end=html.indexOf("const initial=",begin);
assert.ok(begin>=0 && end>begin,"Shipped HTML must contain an identifiable core function");
const advanceCase=runInNewContext(html.slice(begin,end)+"\nadvanceCase;");
const start=()=>({id:"SYN-001",subjectDigest:"synthetic-referral-v1",scope:"service-topic-only",status:"draft",history:[]});
const sequence=(...steps)=>steps.reduce((c,step)=>advanceCase(c,step),start());

test("full simulated chain: only confirmed after authorization → sent → accepted → reported",()=>{
  const result=sequence("authorize","send","accept","report","confirm");
  assert.equal(result.status,"confirmed");
  assert.equal(result.history.length,5);
  assert.equal(result.history[3].kind,"report");
  assert.equal(result.history[4].actor,"Fictional adult");
});
test("no sending before authorization",()=>assert.throws(()=>sequence("send"),/Refused/));
test("sending only after exact subject and narrow scope",()=>{
 assert.throws(()=>advanceCase({...start(),subjectDigest:"different"},"authorize"),/Refused/);
 assert.throws(()=>advanceCase({...start(),scope:"full-case-file"},"authorize"),/Refused/);
});
test("no report without receiving desk acceptance",()=>assert.throws(()=>sequence("authorize","send","report"),/Refused/));
test("no confirmation until report",()=>assert.throws(()=>sequence("authorize","send","accept","confirm"),/Refused/));
test("duplicate sends cannot create second handoff",()=>assert.throws(()=>sequence("authorize","send","send"),/Refused/));
test("withdrawal blocks future send and confirm, without erasing historical events",()=>{
 const withdrawn=sequence("authorize","send","accept","report","revoke");
 assert.equal(withdrawn.status,"revoked");
 assert.equal(withdrawn.history.length,5);
 assert.equal(withdrawn.history[4].kind,"revoke");
 assert.throws(()=>advanceCase(withdrawn,"confirm"),/Refused/);
 assert.throws(()=>advanceCase(withdrawn,"send"),/Refused/);
});
test("receiving desk may decline; decline is not fulfillment",()=>{
 const declined=sequence("authorize","send","decline");
 assert.equal(declined.status,"declined");
 assert.throws(()=>advanceCase(declined,"confirm"),/Refused/);
});
test("event evidence is explicitly synthetic",()=>{
 const c=sequence("authorize");
 assert.match(c.history[0].evidence,/SIMULATED ACTION/);
 assert.ok(!Object.keys(c).some(k=>["legalValidity","authenticatedIdentity","childPlacement"].includes(k)));
});
test("public directory does not submit requests and displays no fields for private cases",()=>{
 assert.ok(html.includes("NO LIVE REFERRALS"));
 assert.equal((html.match(/fetch\s*\(/g)||[]).length,0);
 assert.equal((html.match(/localStorage|sessionStorage/g)||[]).length,0);
});
