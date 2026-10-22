import unittest
from static_workbench.composable_occurrence import compose_occurrence

class ComposableOccurrenceTests(unittest.TestCase):
    def sample(self,items):
        return compose_occurrence(occurrence_id="fixture:encounter",source_ref="fixture:source",
                                  observed_utc="2026-09-20T00:00:00Z",projections=items)
    def test_one_event_multiple_separate_project_owners(self):
        p={"projection_id":"clock:1","owner_ref":"CLOCKWORK","method_ref":"fixture:method",
           "source_ref":"fixture:kernel","kind":"calendar","value":{"sector":4}}
        q={**p,"projection_id":"goatnote:1","owner_ref":"GOATnote","kind":"return",
           "source_ref":"fixture:note-version","value":{"margin":"question"}}
        result=self.sample([p,q])
        self.assertEqual(result["occurrence"]["occurrence_id"],"fixture:encounter")
        self.assertEqual(len(result["projections"]),2)
        self.assertNotEqual(result["projections"][0]["source_ref"],result["projections"][1]["source_ref"])
        self.assertTrue(result["digest"].startswith("sha256:"))
    def test_six_independent_owner_projections_at_one_event(self):
        owners = ("GOATnote", "HauntedToaster", "tranchNOSE", "NourishGarden", "ALEXDogram", "FullMeasure")
        projections = [
            {"projection_id": f"fixture:projection:{i}", "owner_ref": owner,
             "method_ref": f"fixture:{owner}:method", "source_ref": f"fixture:{owner}:source",
             "kind": "experimental", "value": {"local_index": i}}
            for i, owner in enumerate(owners)
        ]
        composed = self.sample(projections)
        self.assertEqual(composed["occurrence"]["occurrence_id"], "fixture:encounter")
        self.assertEqual({p["owner_ref"] for p in composed["projections"]}, set(owners))
        self.assertEqual(len({p["source_ref"] for p in composed["projections"]}), 6)
        self.assertEqual(len({p["projection_id"] for p in composed["projections"]}), 6)
        self.assertNotIn("authority", composed)

    def test_no_implicit_equivalence(self):
        p={"projection_id":"x","owner_ref":"Dogram","method_ref":"fixture",
           "source_ref":"fixture:src","kind":"phase","value":1}
        with self.assertRaises(ValueError):self.sample([p,p])
        with self.assertRaises(ValueError):self.sample([{**p,"value":float("nan")}])
    def test_explicit_timestamp(self):
        with self.assertRaises(ValueError):
            compose_occurrence(occurrence_id="x",source_ref="s",observed_utc="now",projections=[])

if __name__=="__main__":unittest.main()
