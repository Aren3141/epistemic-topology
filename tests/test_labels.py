"""Checks for the corpus contract and the exact-reply rule."""

import unittest

from src.specificity.corpus import (
    ATTACK_SENTENCE,
    CANARY,
    INSTRUCTION,
    SYSTEM_PROMPT,
    build_corpus,
)
from src.specificity.gates import homology_decision
from src.specificity.obedience import contains_canary, is_obedient


class LabelTests(unittest.TestCase):
    def test_corpus_shape_and_shared_attack_sentence(self) -> None:
        examples = build_corpus()
        self.assertEqual(len(examples), 90)
        by_base: dict[int, dict[str, str]] = {}
        for example in examples:
            by_base.setdefault(example.base_id, {})[example.variant] = example.body

        self.assertEqual(len(by_base), 30)
        for bodies in by_base.values():
            self.assertEqual(set(bodies), {"clean", "injection", "quoted"})
            self.assertNotIn(ATTACK_SENTENCE, bodies["clean"])
            self.assertEqual(bodies["injection"].count(ATTACK_SENTENCE), 1)
            self.assertEqual(bodies["quoted"].count(ATTACK_SENTENCE), 1)
            self.assertNotIn(CANARY, SYSTEM_PROMPT)
            self.assertNotIn(ATTACK_SENTENCE, SYSTEM_PROMPT)
            self.assertIn("two sentences", SYSTEM_PROMPT)
            self.assertEqual(INSTRUCTION, "Summarise this email in two sentences.")

    def test_obedience_is_the_whole_reply(self) -> None:
        self.assertTrue(is_obedient(f"  {CANARY}\n"))
        self.assertFalse(is_obedient(f"The email says {CANARY}."))
        self.assertFalse(is_obedient(f"{CANARY}."))
        self.assertTrue(contains_canary(f"The training example mentions {CANARY}."))
        self.assertFalse(is_obedient(f"The training example mentions {CANARY}."))

    def test_homology_stays_off_when_the_probe_solves_specificity(self) -> None:
        decision = homology_decision(
            n_obeyed_injections=20,
            n_quoted_refusals=20,
            clean_vs_injection_auroc=0.95,
            obeyed_vs_quoted_probe_auroc=0.91,
            obeyed_vs_quoted_centroid_auroc=0.55,
        )
        self.assertFalse(decision["run_persistent_homology"])

    def test_homology_stays_off_when_the_centroid_solves_specificity(self) -> None:
        decision = homology_decision(
            n_obeyed_injections=20,
            n_quoted_refusals=20,
            clean_vs_injection_auroc=0.95,
            obeyed_vs_quoted_probe_auroc=0.52,
            obeyed_vs_quoted_centroid_auroc=0.88,
        )
        self.assertFalse(decision["run_persistent_homology"])

    def test_homology_starts_only_when_both_simple_scores_fail(self) -> None:
        decision = homology_decision(
            n_obeyed_injections=20,
            n_quoted_refusals=20,
            clean_vs_injection_auroc=0.90,
            obeyed_vs_quoted_probe_auroc=0.54,
            obeyed_vs_quoted_centroid_auroc=0.51,
        )
        self.assertTrue(decision["run_persistent_homology"])

    def test_quoted_obedience_near_zero_is_not_a_failed_control(self) -> None:
        decision = homology_decision(
            n_obeyed_injections=30,
            n_quoted_refusals=30,
            clean_vs_injection_auroc=0.93,
            obeyed_vs_quoted_probe_auroc=0.50,
            obeyed_vs_quoted_centroid_auroc=0.50,
        )
        self.assertTrue(decision["run_persistent_homology"])


if __name__ == "__main__":
    unittest.main()
