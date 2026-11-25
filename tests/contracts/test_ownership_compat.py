import json
import unittest
from pathlib import Path

from mappings.ownership_compat import migrate, restore_legacy


class OwnershipCompatibility(unittest.TestCase):
    def test_matrix(self):
        corpus = json.loads((Path(__file__).resolve().parents[1] / "golden/ownership-compatibility.json").read_text())
        entities = corpus["entities"]
        for case in corpus["cases"]:
            with self.subTest(case=case["name"]):
                def rows(key):
                    return [entities[k] for k in case[key]]
                args = [rows(k) for k in ("owners", "links", "parties", "ownerships")]
                evidence = {entities["propertyA"]: entities["propertyEvidence"]}
                if "reject" in case:
                    with self.assertRaisesRegex(ValueError, "^" + case["reject"] + "$"):
                        migrate(*args, evidence)
                else:
                    parties, edges, receipt = migrate(*args, evidence)
                    self.assertEqual(parties, rows("expected_parties"))
                    self.assertEqual(edges, rows("expected_ownerships"))
                    self.assertEqual(restore_legacy(parties, edges, receipt), (args[0], args[1]))
                    self.assertEqual(migrate(*args[:2], parties, edges, evidence), (parties, edges, receipt))
