"""Non-executing Flight Card handoff contract: boundary and refusal tests."""
import copy
import unittest
from uuid import uuid4

from static_workbench.flight_cards import (
    FlightCardError, SCHEMA, _digest, self_report, validate_candidate,
)


def specimen():
    proposal = {
        "job": "Inspect a synthetic note",
        "tools": ["ALEX (suggestion only)"],
        "effects": ["read one synthetic note"],
        "fence": "No filesystem, network, or repository writes",
        "unknowns": ["Whether the note has an actual source"],
        "verification": "Human checks the synthetic note text",
    }
    card = {
        "schema": SCHEMA,
        "flight_id": str(uuid4()),
        "raw": {
            "text": "Look at a synthetic note. Preserve it unchanged.",
            "source_type": "text",
            "locator": None,
            "captured_at": "2026-09-20T10:00:00-05:00",
            "observer": "sample human",
        },
        "witnesses": [{
            "id": str(uuid4()), "class": "derived",
            "text": "A reading candidate, not an observation",
            "observer": "sample human", "source_locator": None,
            "occurred_at": None, "recorded_at": "2026-09-20T10:01:00-05:00",
            "known_at": None, "nonclaims": ["Not source-authenticated"],
        }],
        "proposal": proposal,
        "approval": None,
    }
    return card


class FlightCardContractTests(unittest.TestCase):
    def test_unapproved_candidate_is_inert(self):
        result = validate_candidate(specimen())
        self.assertFalse(result["human_approval_claimed"])
        self.assertEqual(result["house_authorization"], "not_evaluated")
        self.assertEqual(result["execution"], "not_attempted")
        self.assertEqual(result["source_authenticity"], "not_verified")

    def test_matching_approval_is_still_not_house_authorization(self):
        card = specimen()
        card["approval"] = {
            "actor": "sample human", "approved_at": "2026-09-20T10:02:00-05:00",
            "proposal_sha256": _digest(card["proposal"]),
            "effects": list(card["proposal"]["effects"]),
        }
        inspected = validate_candidate(card)
        self.assertTrue(inspected["human_approval_claimed"])
        self.assertEqual(inspected["binding"], "not_evaluated")
        self.assertEqual(inspected["execution"], "not_attempted")

    def test_edit_after_approval_refused(self):
        card = specimen()
        card["approval"] = {
            "actor": "sample human", "approved_at": "2026-09-20T10:02:00-05:00",
            "proposal_sha256": _digest(card["proposal"]),
            "effects": list(card["proposal"]["effects"]),
        }
        card["proposal"]["job"] = "Something else"
        with self.assertRaisesRegex(FlightCardError, "stale"):
            validate_candidate(card)

    def test_effect_scope_swap_refused(self):
        card = specimen()
        card["approval"] = {
            "actor": "sample human", "approved_at": "2026-09-20T10:02:00-05:00",
            "proposal_sha256": _digest(card["proposal"]),
            "effects": ["delete all files"],
        }
        with self.assertRaisesRegex(FlightCardError, "approved effects"):
            validate_candidate(card)

    def test_unknown_authority_field_refused(self):
        card = specimen()
        card["auto_execute"] = True
        with self.assertRaisesRegex(FlightCardError, "unknown fields"):
            validate_candidate(card)

    def test_timestamp_requires_timezone(self):
        card = specimen()
        card["raw"]["captured_at"] = "2026-09-20T10:00:00"
        with self.assertRaisesRegex(FlightCardError, "timezone"):
            validate_candidate(card)

    def test_duplicate_witness_refused(self):
        card = specimen()
        card["witnesses"].append(copy.deepcopy(card["witnesses"][0]))
        with self.assertRaisesRegex(FlightCardError, "duplicate"):
            validate_candidate(card)

    def test_invalid_evidence_class_refused(self):
        card = specimen()
        card["witnesses"][0]["class"] = "verified"
        with self.assertRaisesRegex(FlightCardError, "evidence class"):
            validate_candidate(card)

    def test_report_does_not_promote_partial_to_complete(self):
        card = specimen()
        report = {
            "receipt_id": str(uuid4()), "reporter": "sample human",
            "recorded_at": "2026-09-20T10:03:00-05:00",
            "outcome": "partial", "details": "Inspected half of the synthetic note",
            "evidence_locators": [], "nonclaims": ["Other half not inspected"],
            "parent_receipt_sha256": None,
        }
        result = self_report(card, report)
        self.assertEqual(result["report"]["outcome"], "partial")
        self.assertEqual(result["evidence_class"], "self_reported")
        self.assertFalse(result["independently_verified"])
        self.assertEqual(result["house_execution"], "not_performed")

    def test_return_preserves_parent_receipt_reference(self):
        card = specimen()
        report = {
            "receipt_id": str(uuid4()), "reporter": "sample human",
            "recorded_at": "2026-09-20T10:04:00-05:00",
            "outcome": "unresolved", "details": "New information still missing",
            "evidence_locators": [], "nonclaims": [],
            "parent_receipt_sha256": "a" * 64,
        }
        result = self_report(card, report)
        self.assertEqual(result["report"]["parent_receipt_sha256"], "a" * 64)
        self.assertEqual(result["candidate_sha256"], validate_candidate(card)["candidate_sha256"])

    def test_large_payload_refused(self):
        card = specimen()
        card["raw"]["text"] = "x" * 132000
        with self.assertRaisesRegex(FlightCardError, "exceeds"):
            validate_candidate(card)


if __name__ == "__main__":
    unittest.main()
