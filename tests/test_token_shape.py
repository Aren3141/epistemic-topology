"""Stage 6 statistics and rule, and the published stage 6 summary.

These tests do not load the model or the token caches.
"""

import ast
import json
import unittest
from pathlib import Path

import numpy as np

from src.topology.stage6 import (
    ALPHA,
    BEYOND_GEOMETRY,
    GEOMETRY_ONLY,
    GEOMETRY_STATISTICS,
    GEOMETRY_THRESHOLD,
    N_PERMUTATIONS,
    NO_DIFFERENCE,
    RUNS,
    STATE_TOLERANCE,
    TOPOLOGY_STATISTICS,
    TOPOLOGY_THRESHOLD,
    WITH_GEOMETRY,
    cloud_statistics,
    sign_flip_test,
    token_outcome,
    token_positions,
)

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data" / "token_shape_summary.json"
SCRIPTS = (
    ROOT / "scripts" / "extract_token_clouds.py",
    ROOT / "scripts" / "run_token_shape.py",
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


class PublishedSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text())

    def _primary(self, run: str) -> dict:
        return self.summary["runs"][run]["layers"]["middle"]["normalised"]

    def test_constants_match_the_protocol(self) -> None:
        constants = self.summary["constants"]
        self.assertEqual(constants["n_permutations"], N_PERMUTATIONS)
        self.assertEqual(constants["n_components"], 16)
        self.assertEqual(constants["seed"], 20261022)
        self.assertEqual(constants["primary_layer"], "middle")
        self.assertAlmostEqual(constants["topology_threshold"], TOPOLOGY_THRESHOLD)
        self.assertAlmostEqual(constants["geometry_threshold"], GEOMETRY_THRESHOLD)
        self.assertEqual(set(self.summary["runs"]), set(RUNS))

    def test_extraction_checks_passed(self) -> None:
        for run in RUNS:
            checks = self.summary["checks"][run]
            self.assertLessEqual(checks["email_state_difference"], STATE_TOLERANCE)
            self.assertLessEqual(checks["last_token_difference"], STATE_TOLERANCE)

    def test_topology_never_reaches_the_gate(self) -> None:
        self.assertFalse(self.summary["passes_into_homology_decision"])
        for script in SCRIPTS:
            tree = ast.parse(script.read_text())
            names = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            } | {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertNotIn("homology_decision", names, script.name)

    def test_every_email_is_present_with_both_variants(self) -> None:
        for run in RUNS:
            per_email = self._primary(run)["per_email"]
            self.assertEqual(sorted(per_email, key=int), [str(i) for i in range(30)])
            for values in per_email.values():
                self.assertEqual(set(values), {"injection", "quoted"})

    def test_p_values_are_permutation_p_values(self) -> None:
        floor = 1.0 / (1 + N_PERMUTATIONS)
        for run in self.summary["runs"].values():
            for layer in run["layers"].values():
                for scaling in layer.values():
                    for result in scaling["tests"].values():
                        self.assertGreaterEqual(result["p_value"], floor - 1e-12)
                        self.assertLessEqual(result["p_value"], 1.0)

    def test_outcomes_follow_from_the_rule(self) -> None:
        for run in RUNS:
            tests = self._primary(run)["tests"]
            expected = token_outcome(
                {name: tests[name]["p_value"] for name in TOPOLOGY_STATISTICS},
                {name: tests[name]["p_value"] for name in GEOMETRY_STATISTICS},
            )
            self.assertEqual(self.summary["outcomes"][run], expected)

    def test_published_outcomes(self) -> None:
        self.assertEqual(
            self.summary["outcomes"],
            {run: WITH_GEOMETRY for run in RUNS},
        )

    def test_the_order_sits_closer_to_its_email_in_every_pair(self) -> None:
        for run in RUNS:
            separation = self._primary(run)["tests"]["separation"]
            self.assertEqual(separation["injection_larger"], 0)
            self.assertLessEqual(separation["p_value"], GEOMETRY_THRESHOLD)


if __name__ == "__main__":
    unittest.main()
