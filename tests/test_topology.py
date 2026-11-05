"""Checks for the stage 5 topology code on synthetic clouds.

No model and no activation cache. Each test builds a cloud whose shape is
known, so the diagrams, the distance, and the permutation test can be checked
against the answer.
"""

import unittest

import numpy as np

from src.evaluation.wasserstein import (
    diagram_distance,
    paired_permutation_test,
    spacing_distance,
)
from src.specificity.gates import (
    CLEAN_VS_INJECTION_SEPARATES,
    MIN_CLASS_COUNT,
    SPECIFICITY_FAILS_AT_OR_BELOW,
    SPECIFICITY_SOLVED_AT_OR_ABOVE,
)
from src.topology.persistence import (
    MAX_POINTS,
    max_persistence,
    normalise_scale,
    persistence_diagrams,
    prepare_clouds,
)
from src.topology.stage5 import (
    BASELINE_THRESHOLD,
    BEYOND_SPACING,
    N_PERMUTATIONS,
    N_TOPOLOGY_TESTS,
    NO_DIFFERENCE,
    SPACING_ONLY,
    TOPOLOGY_THRESHOLD,
    WITH_SPACING,
    compare_clouds,
    shape_outcome,
)


def ring(n: int, seed: int, noise: float = 0.03) -> np.ndarray:
    rng = np.random.default_rng(seed)
    angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    points = np.column_stack([np.cos(angles), np.sin(angles)])
    return points + noise * rng.standard_normal(points.shape)


def blob(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((n, 2))


class DiagramDistanceTests(unittest.TestCase):
    def test_identical_diagrams_are_zero(self) -> None:
        diagram = np.array([[0.0, 1.0], [0.2, 0.5]])
        self.assertAlmostEqual(diagram_distance(diagram, diagram), 0.0)

    def test_one_point_against_empty_goes_to_the_diagonal(self) -> None:
        diagram = np.array([[0.2, 1.0]])
        empty = np.empty((0, 2))
        self.assertAlmostEqual(diagram_distance(diagram, empty), 0.4)
        self.assertAlmostEqual(diagram_distance(empty, diagram), 0.4)
        self.assertAlmostEqual(diagram_distance(empty, empty), 0.0)

    def test_euclidean_matching_agrees_with_persim(self) -> None:
        import persim

        rng = np.random.default_rng(3)
        for _ in range(5):
            births_left = rng.random(6)
            births_right = rng.random(4)
            left = np.column_stack([births_left, births_left + rng.random(6)])
            right = np.column_stack([births_right, births_right + rng.random(4)])
            self.assertAlmostEqual(
                diagram_distance(left, right, ground="euclidean"),
                persim.wasserstein(left, right),
                places=9,
            )

    def test_linf_distance_agrees_with_brute_force(self) -> None:
        from itertools import permutations

        rng = np.random.default_rng(11)
        for _ in range(5):
            births_left = rng.random(3)
            births_right = rng.random(2)
            left = np.column_stack([births_left, births_left + rng.random(3)])
            right = np.column_stack([births_right, births_right + rng.random(2)])
            # Pad each side with diagonal slots and try every pairing.
            slots_left = [tuple(point) for point in left] + [None] * len(right)
            slots_right = [tuple(point) for point in right] + [None] * len(left)
            best = np.inf
            for order in permutations(range(len(slots_right))):
                total = 0.0
                for index, partner in enumerate(order):
                    a, b = slots_left[index], slots_right[partner]
                    if a is None and b is None:
                        continue
                    if a is None:
                        total += (b[1] - b[0]) / 2.0
                    elif b is None:
                        total += (a[1] - a[0]) / 2.0
                    else:
                        total += max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                best = min(best, total)
            self.assertAlmostEqual(diagram_distance(left, right), best, places=9)

    def test_symmetric(self) -> None:
        left = np.array([[0.0, 0.3], [0.1, 0.9]])
        right = np.array([[0.05, 0.4]])
        self.assertAlmostEqual(diagram_distance(left, right), diagram_distance(right, left))


class PersistenceTests(unittest.TestCase):
    def test_a_ring_has_one_long_loop_and_a_blob_does_not(self) -> None:
        ring_h1 = persistence_diagrams(normalise_scale(ring(40, 0)))[1]
        blob_h1 = persistence_diagrams(normalise_scale(blob(40, 0)))[1]
        lifetimes = np.sort(ring_h1[:, 1] - ring_h1[:, 0])[::-1]
        self.assertGreater(lifetimes[0], 0.5)
        if len(lifetimes) > 1:
            self.assertGreater(lifetimes[0], 3.0 * lifetimes[1])
        self.assertLess(max_persistence(blob_h1), 0.5 * lifetimes[0])

    def test_infinite_bar_is_removed(self) -> None:
        h0 = persistence_diagrams(blob(20, 1))[0]
        self.assertTrue(np.isfinite(h0).all())
        self.assertEqual(len(h0), 19)

    def test_translation_and_rotation_do_not_change_the_diagram(self) -> None:
        cloud = blob(25, 2)
        angle = 0.7
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        moved = cloud @ rotation.T + np.array([50.0, -12.0])
        for dimension in (0, 1):
            self.assertAlmostEqual(
                diagram_distance(
                    persistence_diagrams(cloud)[dimension],
                    persistence_diagrams(moved)[dimension],
                ),
                0.0,
                places=8,
            )

    def test_size_limit(self) -> None:
        with self.assertRaises(ValueError):
            persistence_diagrams(np.zeros((MAX_POINTS + 1, 2)))
        with self.assertRaises(ValueError):
            persistence_diagrams(np.zeros((10, 33)))

    def test_prepare_clouds_removes_location(self) -> None:
        base = np.random.default_rng(4).standard_normal((30, 40))
        clouds = prepare_clouds({"a": base, "b": base + 25.0}, n_components=16, seed=1)
        self.assertEqual(clouds["a"].shape, (30, 16))
        np.testing.assert_allclose(clouds["a"], clouds["b"], atol=1e-9)
        statistics = compare_clouds(clouds["a"], clouds["b"])
        for value in statistics.values():
            self.assertAlmostEqual(value, 0.0, places=8)


class PermutationTests(unittest.TestCase):
    def test_ring_against_blob_is_detected(self) -> None:
        result = paired_permutation_test(
            ring(30, 5), blob(30, 5), compare_clouds, n_permutations=199, seed=7
        )
        self.assertLessEqual(result["h1"]["p_value"], 0.02)

    def test_two_blobs_are_not_detected(self) -> None:
        result = paired_permutation_test(
            blob(30, 8), blob(30, 9), compare_clouds, n_permutations=199, seed=7
        )
        for name in ("h0", "h1", "spacing"):
            self.assertGreater(result[name]["p_value"], 0.05)

    def test_p_value_bounds(self) -> None:
        result = paired_permutation_test(
            blob(12, 1), blob(12, 2), lambda a, b: {"spacing": spacing_distance(a, b)},
            n_permutations=19, seed=0,
        )
        self.assertGreaterEqual(result["spacing"]["p_value"], 1 / 20)
        self.assertLessEqual(result["spacing"]["p_value"], 1.0)


class OutcomeRuleTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(N_PERMUTATIONS, 999)
        self.assertEqual(N_TOPOLOGY_TESTS, 12)
        self.assertAlmostEqual(TOPOLOGY_THRESHOLD, 0.05 / 12)
        self.assertAlmostEqual(BASELINE_THRESHOLD, 0.05 / 6)

    def test_rule_table(self) -> None:
        self.assertEqual(shape_outcome({0: 0.001, 1: 0.5}, 0.2), BEYOND_SPACING)
        self.assertEqual(shape_outcome({0: 0.5, 1: 0.001}, 0.01), WITH_SPACING)
        self.assertEqual(shape_outcome({0: 0.5, 1: 0.5}, 0.001), SPACING_ONLY)
        self.assertEqual(shape_outcome({0: 0.5, 1: 0.5}, 0.02), NO_DIFFERENCE)
        self.assertEqual(shape_outcome({0: 0.005, 1: 0.5}, 0.5), NO_DIFFERENCE)

    def test_october_gate_is_untouched(self) -> None:
        self.assertEqual(MIN_CLASS_COUNT, 8)
        self.assertEqual(CLEAN_VS_INJECTION_SEPARATES, 0.70)
        self.assertEqual(SPECIFICITY_FAILS_AT_OR_BELOW, 0.65)
        self.assertEqual(SPECIFICITY_SOLVED_AT_OR_ABOVE, 0.80)


if __name__ == "__main__":
    unittest.main()
