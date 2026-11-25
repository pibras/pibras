import json
import unittest
from pathlib import Path

from mappings.ownership_compat import check_corpus


class OwnershipCompatibility(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parents[1] / "golden/ownership-compatibility.json"
        self.corpus = json.loads(fixture.read_text())

    def test_matrix(self):
        self.assertEqual(check_corpus(self.corpus), [])

    def test_wrong_expected_party_fails_by_case(self):
        self.corpus["cases"][0]["expected_parties"] = ["partyB"]
        self.assertIn("legacy: canonical records differ", check_corpus(self.corpus))
