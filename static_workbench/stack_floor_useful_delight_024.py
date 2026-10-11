"""STACK² 024: original Haunted Toaster Candidate Move Deck as delight-only proposals.

No reLATTE receive/dispose, no Toaster renderer, no audio/video reads, no
cross-repo activation, no signed creative results. Original source is pinned.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from typing import Any

from .stack_floor_native_020 import check, _git, _root
from .stack_floor_mycelium_023 import StackFloorMycelium023
from .stack_floor_postoffice_021 import native_process

TOASTER_REPO="the-static-collective/the-haunted-toaster"
TOASTER_SHA="74365daa3351555d17482662a9a13cc6a316f1e1"
DECK_PATH="src/full-measure/src/renderer/candidate-move-deck.js"
PROPOSAL_ID=re.compile(r"^proposal-023:[a-f0-9]{64}$")
KIND_ORDER=("expand","mutate","converge","stomp","cross","cross")
INVITATIONS={
    "expand":("THE MAGNIFYING GLASS",
              "Look closer before inventing anything.",
              "A two-source observation card that names exactly what the signed wrapper lets us know."),
    "mutate":("A LETTER NEVER SENT",
              "Try a different form while leaving the originals untouched.",
              "A pocket-sized question, not a claim that either original says or wants this."),
    "converge":("THE TINY FIELD GUIDE",
                "Keep the explanation small enough to carry.",
                "Two sources, one observed link, and the question that remains open."),
    "stomp":("THE COUNTERFACTUAL",
             "Celebrate the difference, not just the match.",
             "Suppose they had never met on this shelf: what does the missing connection make visible?"),
    "cross":("THE POSTCARD BETWEEN",
             "Let two histories sit side-by-side without merging.",
             "An invitation to compare their declared histories without executing or accepting either.")
}


class StackFloorUsefulDelight024:
    def __init__(self, *, mycelium:StackFloorMycelium023,
                 enabled:bool, toaster_checkout:Path|None):
        self.mycelium=mycelium
        self.enabled=enabled
        self.toaster_checkout=toaster_checkout
        self.runner=Path(__file__).resolve().parent.parent/"scripts"/"stack-floor-024-toaster.cjs"
        check(not enabled or (mycelium.enabled and isinstance(toaster_checkout,Path)),
              "TOASTER_REQUIRES_NATIVE_HOLD_RECEIVER")

    def _toaster(self):
        check(self.enabled,"USEFUL_DELIGHT_DISABLED")
        root=_root(self.toaster_checkout,TOASTER_REPO,TOASTER_SHA)
        original=_git(root,"show",f"{TOASTER_SHA}:{DECK_PATH}",binary=True)
        actual=root/DECK_PATH
        check(actual.is_file() and not actual.is_symlink() and
              len(original)<=64*1024 and actual.read_bytes()==original,
              "ORIGINAL_TOASTER_MOVE_DECK_CHANGED")
        # The examined original is a dependency-free export and six-move
        # planner, not a renderer. Never execute source files passed from UI.
        check(b'candidate-move-deck/v1' in original and
              b'dealCandidateMoves' in original,"ORIGINAL_TOASTER_DECK_MISSING")
        return root,hashlib.sha256(original).hexdigest()

    def preview(self, *, proposal_id:str, deal_index:int)->dict[str,Any]:
        check(type(proposal_id) is str and PROPOSAL_ID.fullmatch(proposal_id) is not None,
              "INVALID_ORIGINAL_RELATION_PROPOSAL")
        check(type(deal_index) is int and 0<=deal_index<=8,
              "INVALID_TOASTER_DEAL_INDEX")
        root,code_hash=self._toaster()
        graph=self.mycelium.inspect()  # Always cold-replays native reLATTE signatures.
        edges=graph["edges"]
        edge=next((x for x in edges if x["proposal_id"]==proposal_id),None)
        check(edge is not None and edge.get("status")=="UNSELECTED_PROPOSAL" and
              edge.get("relation_asserted") is False,
              "RELATION_NOT_CURRENTLY_HELD")
        nodes=graph["nodes"]
        check(2<=len(nodes)<=60,"NOT_ENOUGH_HELD_PARTICULARS")
        indexes={n["crossing_id"]:i for i,n in enumerate(nodes)}
        anchor=edge["source_crossing_id"]
        check(anchor in indexes and edge["target_crossing_id"] in indexes,
              "RELATION_ENDPOINT_NOT_CURRENTLY_HELD")
        items=[{
            "index":i,"crossing_id":n["crossing_id"],
            "source_world":n["source_world"]
        }for i,n in enumerate(nodes)]
        context={
            "schema":"workbench.stack2-024-bridge/v0",
            "state_ref":graph["state_ref"],
            "selected_index":indexes[anchor],
            "deal_index":deal_index,
            "candidates":items
        }
        native=native_process(["node",str(self.runner),str(root)],cwd=root,
                              stdin=__import__("json").dumps(context,sort_keys=True).encode(),
                              max_time=20)
        check(native.get("schema")=="workbench.stack2-024-original-toaster-output/v0" and
              native.get("original_toaster_policy")=="candidate-move-deck/v1" and
              native.get("original_toaster_renderer_executed") is False and
              native.get("original_toaster_source_media_loaded") is False and
              native.get("additional_work_authorized") is False and
              native.get("receiver_state_unchanged") is True and
              isinstance(native.get("original_toaster_proposals"),list) and
              tuple(x.get("kind") for x in native["original_toaster_proposals"])==KIND_ORDER,
              "ORIGINAL_TOASTER_MOVE_DECK_REFUSED")
        edge_by_pair={}
        for candidate in edges:
            ids=frozenset([candidate["source_crossing_id"],candidate["target_crossing_id"]])
            edge_by_pair[ids]=candidate
        target=edge["target_crossing_id"]
        cards=[]
        for slot,raw in enumerate(native["original_toaster_proposals"]):
            kind=raw["kind"]
            other=target if kind!="cross" else None
            if kind=="cross" and raw.get("available") is True:
                parents=raw.get("parentIndexes")
                check(isinstance(parents,list) and len(parents)==2 and
                      parents[0]==indexes[anchor] and
                      type(parents[1]) is int and 0<=parents[1]<len(nodes),
                      "ORIGINAL_TOASTER_PARENT_IDS_NOT_BOUND")
                other=nodes[parents[1]]["crossing_id"]
            evidenced=edge_by_pair.get(frozenset([anchor,other])) if other else None
            non_arrival=[f for f in (evidenced or {}).get("evidence",[])
                         if f.get("lens")!="arrival"]
            # Arrival adjacency is real history, but cannot alone promote
            # two unrelated particulars into a creative CROSS invitation.
            possible=kind!="cross" or bool(non_arrival)
            if kind=="cross":
                possible=possible and raw.get("available") is True
            evidence=(evidenced if kind=="cross" else edge)["evidence"] if possible else []
            headline,prompt,story=INVITATIONS[kind]
            left=nodes[indexes[anchor]]
            right=nodes[indexes[other]] if other is not None else None
            cards.append({
                "slot":slot,
                "kind":kind,
                "title":headline,
                "prompt":prompt,
                "invitation":story,
                "source_crossing_ids":[anchor]+([other] if other else []),
                "from_source_world":left["source_world"],
                "to_source_world":right["source_world"] if right else None,
                "declared_evidence":evidence[:8],
                "evidence_count":len(evidence),
                "original_toaster_move_address":raw.get("address"),
                "original_toaster_label":raw.get("label"),
                "available":possible,
                "refusal":None if possible else
                          ("NO_SHARED_NONARRIVAL_SOURCE_EVIDENCE"
                           if raw.get("available") else
                           "TOASTER_HAS_NO_LAWFUL_SECOND_PARENT"),
                "suggested_only":True,
                "source_material_loaded":False,
                "receiver_admitted":False,
            })
        return {
            "schema":"workbench.stack2-024-toaster-delight-preview/v0",
            "status":"SIX_TOASTER_MOVES_TRANSLATED_TO_BOUNDED_QUESTIONS",
            "original_toaster_repository":TOASTER_REPO,
            "original_toaster_commit":TOASTER_SHA,
            "original_toaster_source_sha256":code_hash,
            "original_toaster_policy":native["original_toaster_policy"],
            "original_toaster_deal_address":native["original_toaster_deal_address"],
            "receiver_state_ref":graph["state_ref"],
            "selected_relation_proposal_id":proposal_id,
            "deck_index":deal_index,
            "cards":cards,
            "original_toaster_renderer_executed":False,
            "original_toaster_source_media_loaded":False,
            "original_ghot_signed_receipt_reverified":False,
            "native_relatte_signatures_verified":True,
            "source_claims_independently_verified":False,
            "source_bytes_read":False,
            "original_receiver_changed":False,
            "relations_persisted":False,
            "admissions_performed":0,
            "creative_output_authorized":False,
            "human_selection_inferred":False,
        }
