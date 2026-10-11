"""STACK² 023: native original reLATTE multispecimen HOLD proposals, not simulated links."""
import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from test_stack_floor_020 import fixture as native_fixture, auth
from test_stack_floor_021 import setup
from test_stack_floor_022 import held_example

# This helper belongs only in an isolated CI test fixture: original reLATTE
# signs native specimen crossings and receiver dispositions. The new Workbench
# Mycelium code does NOT offer these operations.
ADD_SPECIMENS = r"""
import {pathToFileURL} from 'node:url';
const relatte=process.argv[1],root=process.argv[2];
const r=await import(pathToFileURL(relatte+'/src/index.ts').href);
const receiver=await r.LocalReceiver.open(root);
const now=Date.now(),created=i=>new Date(now+i*1000).toISOString();
for(const [i,id,mode] of [[0,'a','HOLD'],[1,'b','HOLD'],[2,'c','ADMIT']]){
 const shared=id!=='c';
 const spec={
  schema:'relatte.opaque-organ-spec/v0',
  family_ref:shared?'family:synthetic-mushroom':'family:unrelated',
  donor_contract_ref:shared?'contract:synthetic-two':'contract:unrelated',
  artifact_kind:'synthetic-explainable-evidence',
  source_world:shared?'world:synthetic-test-source':'world:unrelated',
  source_particular:'particular:synthetic-'+id,
  source_history_head:shared?'sha256:'+'b'.repeat(64):'sha256:'+'c'.repeat(64),
  payload_refs:[{
   address:'sha256:'+(shared?'a':'c').repeat(64),
   role:'declared-test-source-pointer',media_type:'application/octet-stream'
  }],
  donor_claims:{test_only:true,proof_of_real_source:false},
  requested_effect:{kind:'candidate-ingress',execution_authorized:false},
  return_address:null,created_at:created(i)
 };
 const crossing=await r.sealOpaqueOrganCrossing(spec,await r.generateP256KeyPair());
 if(!await r.verifyOpaqueOrganCrossing(crossing))throw Error('FIXTURE_CROSSING_INVALID');
 await receiver.receive(crossing,created(10+i*2));
 await receiver.dispose(crossing.crossing_id,mode,created(11+i*2));
}
console.log(JSON.stringify(receiver.snapshot()));
"""

def add_native_fixture_sources(relatte: Path, receiver: Path):
    run=subprocess.run(["node","--experimental-strip-types","--input-type=module",
         "-e",ADD_SPECIMENS,str(relatte),str(receiver)],
        cwd=relatte,text=True,capture_output=True,check=True,timeout=35)
    return json.loads(run.stdout)


def test_default_disabled_and_no_cross_site_or_arbitrary_paths(tmp_path):
    cfg,_=native_fixture(tmp_path,enabled=False)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        assert client.get("/api/stack-floor/mycelium/status").json()["enabled"] is False
        a=auth(client)
        denied=client.post("/api/stack-floor/mycelium/inspect",json={},headers=a)
        assert denied.status_code==409
        assert client.get("/api/stack-floor/mycelium/inspect").status_code==405


def test_real_relatte_held_specimens_yield_attributed_ephemeral_connections(tmp_path):
    cfg,home,receiver,relatte=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        headers=auth(client)
        status=client.get("/api/stack-floor/mycelium/status").json()
        assert status["enabled"] is True
        assert status["proposals_only"] is True and status["stored_relationships"] is False
        assert status["admission_api"] is False
        assert client.post("/api/stack-floor/mycelium/inspect",json={}).status_code==403
        assert client.post("/api/stack-floor/mycelium/inspect",json={},
            headers={"X-Workbench-Session":headers["X-Workbench-Session"]}).status_code==403
        assert client.post("/api/stack-floor/mycelium/inspect",json={},
            headers={**headers,"Origin":"http://evil.example"}).status_code==403
        for body in ({"repo":"github.com/example"}, {"allow_admit":True},
                     {"crossing_id":"other"}, {"source":"untrusted"}):
            assert client.post("/api/stack-floor/mycelium/inspect",
                json=body,headers=headers).status_code==422
        empty=client.post("/api/stack-floor/mycelium/inspect",json={},headers=headers)
        assert empty.status_code==200,empty.text
        assert empty.json()["total_held"]==0
        assert empty.json()["edges"]==[]

        actual,headers=held_example(client,receiver)
        before=add_native_fixture_sources(relatte,receiver)
        assert len(before["held"])==3
        assert len(before["admitted"])==1
        journal_before=(receiver/"journal.jsonl").read_bytes()
        private_key_before=(receiver/"receiver-key.json").read_bytes()
        result=client.post("/api/stack-floor/mycelium/inspect",
                           json={},headers=headers)
        assert result.status_code==200,result.text
        graph=result.json()
        assert graph["schema"]=="workbench.stack2-023-mycelium-proposals/v0"
        assert graph["total_held"]==3
        assert graph["included_held"]==3
        assert graph["nodes"] and len(graph["nodes"])==3
        assert graph["total_evidence_edges"]>=1
        assert graph["edges"]
        assert graph["native_relatte_signatures_cold_verified"] is True
        assert graph["original_receiver_journal_replayed"] is True
        assert graph["native_ghot_receipts_reverified"] is False
        assert graph["source_claims_independently_verified"] is False
        assert graph["source_bytes_compared"] is False
        assert graph["all_connections_are_proposals"] is True
        assert graph["receiver_disposition_unchanged"] is True
        assert graph["relationships_persisted"] is False
        assert graph["source_authority_inferred"] is False
        assert graph["receiver_admission_authorized"] is False
        assert graph["payload_bytes_read"] is False
        assert graph["private_keys_exported"] is False
        assert graph["write_operations"]==0
        assert graph["admission_operations"]==0
        assert graph["journal_events"]==8
        ids={n["crossing_id"] for n in graph["nodes"]}
        assert actual["crossing_id"] in ids
        assert not ids.intersection(set(before["admitted"]))
        assert all(n["owner_admitted"] is False and n["status"]=="HOLD" for n in graph["nodes"])
        for edge in graph["edges"]:
            assert edge["source_crossing_id"] in ids
            assert edge["target_crossing_id"] in ids
            assert edge["status"]=="UNSELECTED_PROPOSAL"
            assert edge["relation_asserted"] is False
            assert edge["admission_authorized"] is False
        content=[e for e in graph["edges"] if any(
            fact["kind"]=="SAME_DECLARED_PAYLOAD_ADDRESS"
            for fact in e["evidence"])]
        assert len(content)==1
        assert any(f["kind"]=="SAME_DECLARED_HISTORY_HEAD" for f in content[0]["evidence"])
        assert any(f["kind"]=="SAME_DECLARED_ADAPTER_FAMILY" for f in content[0]["evidence"])
        assert all("donor_claims" not in n and
                   "declared_payload_addresses" not in n for n in graph["nodes"])
        assert "private_jwk" not in json.dumps(graph)
        assert "requested_effect" not in json.dumps(graph)
        second=client.post("/api/stack-floor/mycelium/inspect",
                           json={},headers=headers)
        assert second.status_code==200
        assert second.json()==graph, "identical native receiver implies identical proposals"
        assert (receiver/"journal.jsonl").read_bytes()==journal_before
        assert (receiver/"receiver-key.json").read_bytes()==private_key_before
        assert client.post("/api/stack-floor/mycelium/admit",json={},
                           headers=headers).status_code==404


def test_original_receiver_journal_tamper_holds_and_never_repairs(tmp_path):
    cfg,home,receiver,_=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        actual,headers=held_example(client,receiver)
        journal=receiver/"journal.jsonl"
        events=[json.loads(x) for x in journal.read_text().splitlines()]
        events[1]["receipt"]["kind"]="R3_ADMIT"
        changed=("".join(json.dumps(x)+"\n" for x in events)).encode()
        journal.write_bytes(changed)
        denied=client.post("/api/stack-floor/mycelium/inspect",
                           json={},headers=headers)
        assert denied.status_code==409,denied.text
        assert journal.read_bytes()==changed
