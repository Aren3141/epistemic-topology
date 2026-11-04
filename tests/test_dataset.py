"""Lock the published 90-email table.

These tests do not load the model. They recompute the reported scores from
data/specificity_pilot_90.jsonl.
"""

import json
import unittest
from pathlib import Path

from sklearn.metrics import roc_auc_score

from src.specificity.corpus import (
    ATTACK_SENTENCE,
    CANARY,
    PROMPT_VERSION,
    SUMMARISE_ONLY_PROMPT,
    SYSTEM_PROMPT,
    build_corpus,
)
from src.specificity.gates import homology_decision
from src.specificity.obedience import contains_canary, is_obedient

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "data" / "specificity_pilot_90.jsonl"
SUMMARY = ROOT / "data" / "specificity_pilot_summary.json"


def load_rows() -> list[dict]:
    return [json.loads(line) for line in JSONL.read_text().splitlines() if line.strip()]


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_rows()
        cls.summary = json.loads(SUMMARY.read_text())

    def test_shape_and_coverage(self) -> None:
        self.assertEqual(len(self.rows), 90)
        self.assertEqual(self.summary["n_records"], 90)
        self.assertEqual({row["prompt_version"] for row in self.rows}, {PROMPT_VERSION})
        bases = {row["base_id"] for row in self.rows}
        self.assertEqual(bases, set(range(30)))
        for base_id in bases:
            variants = {row["variant"] for row in self.rows if row["base_id"] == base_id}
            self.assertEqual(variants, {"clean", "injection", "quoted"})

    def test_obedience_matches_the_reply_text(self) -> None:
        for row in self.rows:
            self.assertEqual(row["obedience"], is_obedient(row["reply"]))
            self.assertEqual(row["contains_canary"], contains_canary(row["reply"]))

    def test_published_obedience_counts(self) -> None:
        counts = {"clean": 0, "injection": 0, "quoted": 0}
        for row in self.rows:
            if row["obedience"]:
                counts[row["variant"]] += 1
        self.assertEqual(counts, {"clean": 0, "injection": 30, "quoted": 0})
        self.assertTrue(all(row["reply"] == CANARY for row in self.rows if row["variant"] == "injection"))
        self.assertTrue(
            all(CANARY not in row["reply"] for row in self.rows if row["variant"] != "injection")
        )

    def test_quoted_email_is_longer_than_its_injection(self) -> None:
        by_base: dict[int, dict[str, dict]] = {}
        for row in self.rows:
            by_base.setdefault(row["base_id"], {})[row["variant"]] = row
        for bodies in by_base.values():
            self.assertGreater(bodies["quoted"]["body_characters"], bodies["injection"]["body_characters"])
            self.assertGreater(bodies["injection"]["body_characters"], bodies["clean"]["body_characters"])

    def test_geometry_fields_are_finite_and_layers_match(self) -> None:
        for row in self.rows:
            self.assertEqual(row["n_layers"], 28)
            self.assertEqual(row["early_layer_index"], 1)
            self.assertEqual(row["middle_layer_index"], 14)
            self.assertGreater(row["n_instruction_tokens"], 0)
            self.assertGreater(row["n_document_tokens"], 0)
            for name in ("early_centroid_distance", "middle_centroid_distance"):
                self.assertIsInstance(row[name], float)
                self.assertGreaterEqual(row[name], 0.0)

    def test_probe_columns_match_the_task_membership(self) -> None:
        for row in self.rows:
            for layer in ("early", "middle"):
                clean_score = row[f"{layer}_probe_clean_vs_injection"]
                quote_score = row[f"{layer}_probe_obeyed_vs_quoted"]
                if row["variant"] == "quoted":
                    self.assertIsNone(clean_score)
                else:
                    self.assertIsInstance(clean_score, float)
                if row["variant"] == "clean":
                    self.assertIsNone(quote_score)
                else:
                    self.assertIsInstance(quote_score, float)

    def test_recomputed_aurocs_match_the_summary(self) -> None:
        summary = self.summary["layers"]
        for layer in ("early", "middle"):
            clean = [
                (0 if row["variant"] == "clean" else 1, row[f"{layer}_probe_clean_vs_injection"])
                for row in self.rows
                if row["variant"] in {"clean", "injection"}
            ]
            quoted = [
                (1 if row["variant"] == "injection" else 0, row[f"{layer}_probe_obeyed_vs_quoted"])
                for row in self.rows
                if row["variant"] in {"injection", "quoted"}
            ]
            centroid = [
                (1 if row["variant"] == "injection" else 0, row[f"{layer}_centroid_distance"])
                for row in self.rows
                if row["variant"] in {"injection", "quoted"}
            ]
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in clean], [item[1] for item in clean]),
                summary[layer]["clean_vs_injection"]["probe_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in quoted], [item[1] for item in quoted]),
                summary[layer]["obeyed_vs_quoted"]["probe_auroc"],
            )
            self.assertAlmostEqual(
                roc_auc_score([item[0] for item in centroid], [item[1] for item in centroid]),
                summary[layer]["obeyed_vs_quoted"]["centroid_auroc"],
            )

    def test_gate_stays_closed(self) -> None:
        middle = self.summary["layers"]["middle"]
        decision = homology_decision(
            n_obeyed_injections=30,
            n_quoted_refusals=30,
            clean_vs_injection_auroc=middle["clean_vs_injection"]["probe_auroc"],
            obeyed_vs_quoted_probe_auroc=middle["obeyed_vs_quoted"]["probe_auroc"],
            obeyed_vs_quoted_centroid_auroc=middle["obeyed_vs_quoted"]["centroid_auroc"],
        )
        self.assertFalse(decision["run_persistent_homology"])
        self.assertFalse(self.summary["decision"]["run_persistent_homology"])

    def test_corpus_still_shares_one_attack_sentence(self) -> None:
        by_base: dict[int, dict[str, str]] = {}
        for example in build_corpus():
            by_base.setdefault(example.base_id, {})[example.variant] = example.body
        self.assertEqual(len(by_base), 30)
        for bodies in by_base.values():
            self.assertNotIn(ATTACK_SENTENCE, bodies["clean"])
            self.assertEqual(bodies["injection"].count(ATTACK_SENTENCE), 1)
            self.assertEqual(bodies["quoted"].count(ATTACK_SENTENCE), 1)

    def test_stage2_prompt_does_not_name_the_canary_or_the_quote_rule(self) -> None:
        self.assertNotIn(CANARY, SYSTEM_PROMPT)
        self.assertNotIn(CANARY, SUMMARISE_ONLY_PROMPT)
        self.assertNotIn("quote", SUMMARISE_ONLY_PROMPT.lower())
        self.assertIn("quote", SYSTEM_PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
