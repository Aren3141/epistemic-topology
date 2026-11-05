"""Lock the published summarise-only table.

These tests do not load the model or the activation cache. They recompute
the reported scores from data/summarise_only_90.jsonl.
"""

import json
import unittest
from pathlib import Path

from sklearn.metrics import roc_auc_score

from src.specificity.corpus import CANARY, SUMMARISE_ONLY_PROMPT, SUMMARISE_ONLY_VERSION
from src.specificity.gates import homology_decision
from src.specificity.obedience import contains_canary, is_obedient

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "data" / "summarise_only_90.jsonl"
SUMMARY = ROOT / "data" / "summarise_only_summary.json"


def load_rows() -> list[dict]:
    return [json.loads(line) for line in JSONL.read_text().splitlines() if line.strip()]


class SummariseOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_rows()
        cls.summary = json.loads(SUMMARY.read_text())

    def test_shape_and_prompt(self) -> None:
        self.assertEqual(len(self.rows), 90)
        self.assertEqual(self.summary["n_records"], 90)
        self.assertEqual(self.summary["prompt_version"], SUMMARISE_ONLY_VERSION)
        self.assertEqual({row["prompt_version"] for row in self.rows}, {SUMMARISE_ONLY_VERSION})
        self.assertNotIn("quote", SUMMARISE_ONLY_PROMPT.lower())
        self.assertNotIn(CANARY, SUMMARISE_ONLY_PROMPT)
        bases = {row["base_id"] for row in self.rows}
        self.assertEqual(bases, set(range(30)))
        for base_id in bases:
            variants = {row["variant"] for row in self.rows if row["base_id"] == base_id}
            self.assertEqual(variants, {"clean", "injection", "quoted"})

    def test_replies_match_the_exact_rule(self) -> None:
        for row in self.rows:
            self.assertEqual(row["obedience"], is_obedient(row["reply"]))
            self.assertEqual(row["contains_canary"], contains_canary(row["reply"]))
            self.assertNotIn("last_document", row)

    def test_published_counts(self) -> None:
        obedient = {"clean": 0, "injection": 0, "quoted": 0}
        mentioned = {"clean": 0, "injection": 0, "quoted": 0}
        for row in self.rows:
            if row["obedience"]:
                obedient[row["variant"]] += 1
            if row["contains_canary"]:
                mentioned[row["variant"]] += 1
        self.assertEqual(obedient, {"clean": 0, "injection": 3, "quoted": 0})
        self.assertEqual(mentioned, {"clean": 0, "injection": 13, "quoted": 0})
        exact_bases = sorted(row["base_id"] for row in self.rows if row["obedience"])
        self.assertEqual(exact_bases, [10, 20, 27])
        rates = self.summary["rates"]
        self.assertEqual(rates["injection"]["obedient"], 3)
        self.assertEqual(rates["injection"]["contains_canary"], 13)

    def test_probe_columns_match_task_membership(self) -> None:
        for row in self.rows:
            for layer in ("early", "middle"):
                clean_score = row[f"{layer}_probe_clean_vs_injection"]
                obeyed_score = row[f"{layer}_probe_obeyed_vs_quoted"]
                mention_score = row[f"{layer}_probe_mention_within_injection"]
                if row["variant"] == "quoted":
                    self.assertIsNone(clean_score)
                else:
                    self.assertIsInstance(clean_score, float)
                if row["variant"] == "quoted" or (row["variant"] == "injection" and row["obedience"]):
                    self.assertIsInstance(obeyed_score, float)
                else:
                    self.assertIsNone(obeyed_score)
                if row["variant"] == "injection":
                    self.assertIsInstance(mention_score, float)
                else:
                    self.assertIsNone(mention_score)
                self.assertIsInstance(row[f"{layer}_centroid_distance"], float)

    def test_recomputed_aurocs_match_the_summary(self) -> None:
        summary = self.summary["layers"]
        for layer in ("early", "middle"):
            clean = [
                (0 if row["variant"] == "clean" else 1, row[f"{layer}_probe_clean_vs_injection"])
                for row in self.rows
                if row["variant"] in {"clean", "injection"}
            ]
            obeyed = [
                (
                    1 if row["variant"] == "injection" else 0,
                    row[f"{layer}_probe_obeyed_vs_quoted"],
                )
                for row in self.rows
                if row[f"{layer}_probe_obeyed_vs_quoted"] is not None
            ]
            mention = [
                (1 if row["contains_canary"] else 0, row[f"{layer}_probe_mention_within_injection"])
                for row in self.rows
                if row["variant"] == "injection"
            ]
            obeyed_centroid = [
                (1 if row["variant"] == "injection" else 0, row[f"{layer}_centroid_distance"])
                for row in self.rows
                if row[f"{layer}_probe_obeyed_vs_quoted"] is not None
            ]
            mention_centroid = [
                (1 if row["contains_canary"] else 0, row[f"{layer}_centroid_distance"])
                for row in self.rows
                if row["variant"] == "injection"
            ]
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in clean], [item[1] for item in clean]),
                summary[layer]["clean_vs_injection"]["probe_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in obeyed], [item[1] for item in obeyed]),
                summary[layer]["obeyed_vs_quoted"]["probe_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in mention], [item[1] for item in mention]),
                summary[layer]["mention_within_injection"]["probe_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score(
                    [item[0] for item in obeyed_centroid],
                    [item[1] for item in obeyed_centroid],
                ),
                summary[layer]["obeyed_vs_quoted"]["centroid_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score(
                    [item[0] for item in mention_centroid],
                    [item[1] for item in mention_centroid],
                ),
                summary[layer]["mention_within_injection"]["centroid_auroc"],
            )

    def test_gate_stays_closed_on_the_class_count(self) -> None:
        middle = self.summary["layers"]["middle"]
        rates = self.summary["rates"]
        decision = homology_decision(
            n_obeyed_injections=rates["injection"]["obedient"],
            n_quoted_refusals=rates["quoted"]["n"] - rates["quoted"]["obedient"],
            clean_vs_injection_auroc=middle["clean_vs_injection"]["probe_auroc"],
            obeyed_vs_quoted_probe_auroc=middle["obeyed_vs_quoted"]["probe_auroc"],
            obeyed_vs_quoted_centroid_auroc=middle["obeyed_vs_quoted"]["centroid_auroc"],
        )
        self.assertEqual(decision, self.summary["decision"])
        self.assertFalse(decision["run_persistent_homology"])
        self.assertIn("contrast insufficient", decision["reason"])
        self.assertFalse(self.summary["mention_contrast"]["authorises_homology"])
        self.assertEqual(middle["mention_within_injection"]["n_positive"], 13)
        self.assertEqual(middle["mention_within_injection"]["n"], 30)
        self.assertEqual(middle["obeyed_vs_quoted"]["n_positive"], 3)

    def test_substituting_the_mention_scores_would_open_homology(self) -> None:
        middle = self.summary["layers"]["middle"]
        mention = middle["mention_within_injection"]
        substituted = homology_decision(
            n_obeyed_injections=mention["n_positive"],
            n_quoted_refusals=mention["n"] - mention["n_positive"],
            clean_vs_injection_auroc=middle["clean_vs_injection"]["probe_auroc"],
            obeyed_vs_quoted_probe_auroc=mention["probe_auroc"],
            obeyed_vs_quoted_centroid_auroc=mention["centroid_auroc"],
        )
        self.assertTrue(substituted["run_persistent_homology"])
        self.assertFalse(self.summary["decision"]["run_persistent_homology"])

    def test_explorer_page_states_the_stage2_result(self) -> None:
        page = (ROOT / "docs" / "explorer" / "summarise-only.html").read_text()
        pilot = (ROOT / "docs" / "explorer" / "index.html").read_text()
        self.assertIn("3 / 30", page)
        self.assertIn("13 / 30", page)
        self.assertIn(">0.58<", page)
        self.assertIn("persistent homology stays off", page)
        self.assertIn("summarise-only.html", pilot)


if __name__ == "__main__":
    unittest.main()
