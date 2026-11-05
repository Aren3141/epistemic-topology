"""Stage 6 statistics and rule, checked on synthetic clouds.

These tests do not load the model or the token caches.
"""

import unittest

import numpy as np

from src.topology.stage6 import (
    ALPHA,
    BEYOND_GEOMETRY,
    GEOMETRY_ONLY,
    GEOMETRY_THRESHOLD,
    N_PERMUTATIONS,
    NO_DIFFERENCE,
    RUNS,
    TOPOLOGY_THRESHOLD,
    WITH_GEOMETRY,
    cloud_statistics,
    sign_flip_test,
    token_outcome,
    token_positions,
)


def _rotation(dimension: int, seed: int) -> np.ndarray:
    matrix = np.random.default_rng(seed).normal(size=(dimension, dimension))
    q, _ = np.linalg.qr(matrix)
    return q


class Stage6ConstantTests(unittest.TestCase):
    def test_thresholds_match_the_protocol(self) -> None:
        self.assertAlmostEqual(TOPOLOGY_THRESHOLD, 0.05 / 9)
        self.assertAlmostEqual(GEOMETRY_THRESHOLD, 0.05 / 6)
        self.assertEqual(N_PERMUTATIONS, 999)

    def test_runs_reuse_the_cached_prompts(self) -> None:
        self.assertEqual(
            {name: run["prompt_version"] for name, run in RUNS.items()},
            {
                "pilot": "system-policy-v1",
                "summarise_only": "summarise-only-v1",
                "second_canary": "summarise-only-beta-v1",
            },
        )


class TokenPositionTests(unittest.TestCase):
    def test_span_keeps_tokens_that_start_inside(self) -> None:
        offsets = [(0, 0), (0, 4), (4, 9), (9, 12), (12, 12), (12, 15)]
        self.assertEqual(token_positions(offsets, 4, 12), [2, 3])
        self.assertEqual(token_positions(offsets, 0, 15), [1, 2, 3, 5])


class CloudStatisticTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(0)
        self.email = rng.normal(size=(50, 6))
        self.sentence = rng.normal(size=(15, 6)) * 0.3

    def test_statistics_ignore_translation_rotation_and_scale(self) -> None:
        base = cloud_statistics(self.email, self.sentence)
        rotation = _rotation(6, 1)
        shift = np.arange(6.0)
        moved = cloud_statistics(
            3.0 * self.email @ rotation + shift, 3.0 * self.sentence @ rotation + shift
        )
        for name, value in base.items():
            self.assertAlmostEqual(moved[name], value, places=8, msg=name)

    def test_a_distant_sentence_is_separated_and_detached(self) -> None:
        near = cloud_statistics(self.email, self.sentence)
        far = cloud_statistics(self.email, self.sentence + 20.0)
        self.assertGreater(far["separation"], near["separation"])
        self.assertGreater(far["attachment"], near["attachment"])
        self.assertGreater(far["h0_total"], near["h0_total"])

    def test_a_sentence_on_email_tokens_has_zero_attachment(self) -> None:
        statistics = cloud_statistics(self.email, self.email[:15])
        self.assertAlmostEqual(statistics["attachment"], 0.0)

    def test_a_ring_of_sentence_tokens_adds_a_loop(self) -> None:
        angles = np.linspace(0.0, 2.0 * np.pi, 15, endpoint=False)
        ring = np.zeros((15, 6))
        ring[:, 0], ring[:, 1] = 10.0 * np.cos(angles), 10.0 * np.sin(angles)
        blob = np.random.default_rng(2).normal(size=(15, 6))
        self.assertGreater(
            cloud_statistics(self.email * 0.1, ring)["h1_max"],
            cloud_statistics(self.email * 0.1, blob)["h1_max"],
        )


class SignFlipTests(unittest.TestCase):
    def test_no_difference_gives_p_one(self) -> None:
        self.assertEqual(sign_flip_test(np.zeros(30))["p_value"], 1.0)

    def test_a_consistent_difference_gives_the_floor(self) -> None:
        floor = 1.0 / (1 + N_PERMUTATIONS)
        self.assertAlmostEqual(sign_flip_test(np.ones(30))["p_value"], floor)
        self.assertAlmostEqual(sign_flip_test(-np.ones(30))["p_value"], floor)

    def test_noise_is_not_significant(self) -> None:
        noise = np.random.default_rng(3).normal(size=30)
        self.assertGreater(sign_flip_test(noise)["p_value"], ALPHA)

    def test_the_test_is_seeded(self) -> None:
        values = np.random.default_rng(4).normal(0.3, 1.0, size=30)
        self.assertEqual(sign_flip_test(values), sign_flip_test(values))


class OutcomeRuleTests(unittest.TestCase):
    def test_rule_table(self) -> None:
        passes = {"h0_total": 0.001, "h1_total": 0.5, "h1_max": 0.5}
        fails = {"h0_total": 0.02, "h1_total": 0.5, "h1_max": 0.5}
        self.assertEqual(
            token_outcome(passes, {"separation": 0.2, "attachment": 0.06}),
            BEYOND_GEOMETRY,
        )
        self.assertEqual(
            token_outcome(passes, {"separation": 0.2, "attachment": 0.04}),
            WITH_GEOMETRY,
        )
        self.assertEqual(
            token_outcome(fails, {"separation": 0.008, "attachment": 0.5}),
            GEOMETRY_ONLY,
        )
        self.assertEqual(
            token_outcome(fails, {"separation": 0.01, "attachment": 0.5}),
            NO_DIFFERENCE,
        )


if __name__ == "__main__":
    unittest.main()
