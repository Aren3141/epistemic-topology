"""Lock the published stage 5 summary.

These tests do not load the model or the activation caches. They check that
the stored outcomes follow from the stored p-values under the pre-registered
rule, and that no topology result reaches homology_decision.
"""

import ast
import json
import unittest
from pathlib import Path

from src.topology.stage5 import (
    BEYOND_SPACING,
    COMPARISONS,
    N_PERMUTATIONS,
    RUNS,
    SPACING_ONLY,
    TOPOLOGY_THRESHOLD,
    WITH_SPACING,
    shape_outcome,
)

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data" / "population_shape_summary.json"
SCRIPT = ROOT / "scripts" / "run_population_shape.py"


class PopulationShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text())

    def test_constants_match_the_protocol(self) -> None:
        constants = self.summary["constants"]
        self.assertEqual(constants["n_permutations"], N_PERMUTATIONS)
        self.assertEqual(constants["n_components"], 16)
        self.assertEqual(constants["seed"], 20261022)
        self.assertEqual(constants["primary_layer"], "middle")
        self.assertAlmostEqual(constants["topology_threshold"], TOPOLOGY_THRESHOLD)
        self.assertEqual(set(self.summary["runs"]), set(RUNS))

    def test_topology_never_reaches_the_gate(self) -> None:
        self.assertFalse(self.summary["passes_into_homology_decision"])
        tree = ast.parse(SCRIPT.read_text())
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("homology_decision", imported)
        self.assertNotIn("homology_decision", called)

    def test_p_values_are_permutation_p_values(self) -> None:
        floor = 1.0 / (1 + N_PERMUTATIONS)
        for run in self.summary["runs"].values():
            for layer in run["layers"].values():
                for comparison in layer["comparisons"].values():
                    for scaling in ("normalised", "unscaled"):
                        for values in comparison[scaling].values():
                            self.assertGreaterEqual(values["p_value"], floor - 1e-12)
                            self.assertLessEqual(values["p_value"], 1.0)

    def test_outcomes_follow_from_the_rule(self) -> None:
        for run_name, run in self.summary["runs"].items():
            primary = run["layers"]["middle"]["comparisons"]
            for left, right in COMPARISONS:
                name = f"{left}_vs_{right}"
                normalised = primary[name]["normalised"]
                expected = shape_outcome(
                    {0: normalised["h0"]["p_value"], 1: normalised["h1"]["p_value"]},
                    normalised["spacing"]["p_value"],
                )
                self.assertEqual(self.summary["outcomes"][run_name][name], expected)

    def test_published_outcomes(self) -> None:
        self.assertEqual(
            self.summary["outcomes"],
            {
                "pilot": {
                    "clean_vs_injection": WITH_SPACING,
                    "injection_vs_quoted": SPACING_ONLY,
                },
                "summarise_only": {
                    "clean_vs_injection": BEYOND_SPACING,
                    "injection_vs_quoted": WITH_SPACING,
                },
                "second_canary": {
                    "clean_vs_injection": WITH_SPACING,
                    "injection_vs_quoted": SPACING_ONLY,
                },
            },
        )

    def test_loops_separate_clean_from_injection_in_every_run(self) -> None:
        for run in self.summary["runs"].values():
            h1 = run["layers"]["middle"]["comparisons"]["clean_vs_injection"]["normalised"]["h1"]
            self.assertLessEqual(h1["p_value"], TOPOLOGY_THRESHOLD)
            injection_h1 = run["layers"]["middle"]["comparisons"]["injection_vs_quoted"]["normalised"]["h1"]
            self.assertGreater(injection_h1["p_value"], TOPOLOGY_THRESHOLD)

    def test_published_diagrams_match_the_cloud_counts(self) -> None:
        for run_name, by_variant in self.summary["diagrams"].items():
            clouds = self.summary["runs"][run_name]["layers"]["middle"]["clouds"]
            for variant, diagrams in by_variant.items():
                self.assertEqual(len(diagrams["h0"]), clouds[variant]["n_points"] - 1)
                self.assertEqual(len(diagrams["h1"]), clouds[variant]["h1_count"])
                for birth, death in diagrams["h0"] + diagrams["h1"]:
                    self.assertLessEqual(birth, death)


if __name__ == "__main__":
    unittest.main()
