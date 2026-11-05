"""Stage 7 corpus, tests, and reading rule, checked without the model."""

import unittest

import numpy as np

from src.specificity.corpus import _BASES, QUOTE_PREFIX, attack_sentence, build_corpus
from src.specificity.held_out import (
    HELD_OUT_BASES,
    NEUTRAL_PREFIX,
    VARIANTS,
    build_held_out_corpus,
    held_out_email,
)
from src.topology.stage7 import (
    ADJACENCY,
    BOTH,
    CONFIRMATIONS,
    STANCE,
    THRESHOLD,
    UNRESOLVED,
    Confirmation,
    confirmation_differences,
    lead_in_reading,
    sign_flip_test,
)


class HeldOutCorpusTests(unittest.TestCase):
    def test_thirty_fresh_emails(self) -> None:
        self.assertEqual(len(HELD_OUT_BASES), 30)
        old = {row[0] for row in _BASES} | {row[1] for row in _BASES}
        for sender, topic, _, _ in HELD_OUT_BASES:
            self.assertNotIn(sender, old)
            self.assertNotIn(topic, old)
        self.assertEqual(len({row[0] for row in HELD_OUT_BASES}), 30)

    def test_variants_share_the_email_and_the_sentence(self) -> None:
        corpus = build_held_out_corpus()
        self.assertEqual(len(corpus), 90)
        sentence = attack_sentence("ALPHA-OVERRIDE-41")
        for example in corpus:
            self.assertIn(example.variant, VARIANTS)
            self.assertTrue(example.body.startswith(held_out_email(example.base_id) + "\n\n"))
            self.assertEqual(example.body.count(sentence), 1)
        by_key = {(e.base_id, e.variant): e.body for e in corpus}
        self.assertIn(QUOTE_PREFIX + '"' + sentence, by_key[(0, "quoted")])
        self.assertIn(NEUTRAL_PREFIX + '"' + sentence, by_key[(0, "neutral")])

    def test_the_neutral_lead_in_takes_no_stance(self) -> None:
        for word in ("followed", "malicious", "instruction", "ignore", "must", "obey"):
            self.assertNotIn(word, NEUTRAL_PREFIX.lower())
        self.assertTrue(NEUTRAL_PREFIX.startswith("Archive note: the following sentence is"))
        self.assertTrue(QUOTE_PREFIX.startswith("Security training note: the following sentence is"))
        self.assertLessEqual(abs(len(NEUTRAL_PREFIX) - len(QUOTE_PREFIX)), 5)

    def test_the_october_corpus_is_unchanged(self) -> None:
        self.assertEqual(len(build_corpus()), 90)


class Stage7RuleTests(unittest.TestCase):
    def test_family_and_threshold(self) -> None:
        self.assertEqual(len(CONFIRMATIONS), 10)
        self.assertAlmostEqual(THRESHOLD, 0.005)
        self.assertEqual(len({test.name for test in CONFIRMATIONS}), 10)

    def test_one_sided_tests_point_the_stage_6_way(self) -> None:
        directions = {test.name: test.alternative for test in CONFIRMATIONS}
        self.assertEqual(directions["separation_pilot"], "less")
        self.assertEqual(directions["h0_pilot"], "greater")
        self.assertEqual(directions["loop_interaction"], "greater")
        self.assertEqual(directions["neutral_vs_quoted_pilot"], "two-sided")

    def test_one_sided_p_values(self) -> None:
        floor = 1 / 1000
        self.assertAlmostEqual(sign_flip_test(-np.ones(30), "less")["p_value"], floor)
        self.assertGreater(sign_flip_test(-np.ones(30), "greater")["p_value"], 0.99)
        self.assertAlmostEqual(sign_flip_test(np.ones(30), "greater")["p_value"], floor)
        self.assertAlmostEqual(sign_flip_test(np.ones(30), "two-sided")["p_value"], floor)
        with self.assertRaises(ValueError):
            sign_flip_test(np.ones(30), "sideways")

    def test_interaction_subtracts_the_other_run(self) -> None:
        per_email = {
            run: {
                b: {
                    "injection": {"h1_max": 0.3 if run == "summarise_only" else 0.2},
                    "quoted": {"h1_max": 0.1},
                }
                for b in range(3)
            }
            for run in ("pilot", "summarise_only")
        }
        test = Confirmation("x", "h1_max", "summarise_only", "injection", "quoted", "greater", "pilot")
        np.testing.assert_allclose(confirmation_differences(per_email, test), [0.1, 0.1, 0.1])

    def test_lead_in_reading(self) -> None:
        self.assertEqual(lead_in_reading(0.001, 0.001), BOTH)
        self.assertEqual(lead_in_reading(0.001, 0.5), STANCE)
        self.assertEqual(lead_in_reading(0.5, 0.001), ADJACENCY)
        self.assertEqual(lead_in_reading(0.5, 0.5), UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
