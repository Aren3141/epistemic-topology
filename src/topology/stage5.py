"""Pre-registered constants and outcome rule for stage 5, population shape.

Fixed on 5 November 2026 before any diagram was computed. The prose copy is
docs/stage5_protocol.md. Nothing here feeds homology_decision.
"""

from src.specificity.gates import PCA_COMPONENTS, SEED

RUNS = {
    "pilot": "results/cache",
    "summarise_only": "results/cache_summarise_only",
    "second_canary": "results/cache_second_canary",
}
COMPARISONS = (("clean", "injection"), ("injection", "quoted"))
PRIMARY_LAYER = "middle"
LAYERS = ("middle", "early")
HOMOLOGY_DIMENSIONS = (0, 1)
N_COMPONENTS = PCA_COMPONENTS
N_PERMUTATIONS = 999
PERMUTATION_SEED = SEED
ALPHA = 0.05
N_TOPOLOGY_TESTS = len(RUNS) * len(COMPARISONS) * len(HOMOLOGY_DIMENSIONS)
N_BASELINE_TESTS = len(RUNS) * len(COMPARISONS)
TOPOLOGY_THRESHOLD = ALPHA / N_TOPOLOGY_TESTS
BASELINE_THRESHOLD = ALPHA / N_BASELINE_TESTS

BEYOND_SPACING = "shape differs, beyond spacing"
WITH_SPACING = "shape differs, spacing already shows it"
SPACING_ONLY = "spacing differs, topology does not"
NO_DIFFERENCE = "no shape difference detected"


def shape_outcome(topology_p_values: dict[int, float], baseline_p_value: float) -> str:
    """Apply the stage 5 rule to one comparison at the primary layer."""
    topology_passes = any(
        value <= TOPOLOGY_THRESHOLD for value in topology_p_values.values()
    )
    if topology_passes:
        if baseline_p_value >= ALPHA:
            return BEYOND_SPACING
        return WITH_SPACING
    if baseline_p_value <= BASELINE_THRESHOLD:
        return SPACING_ONLY
    return NO_DIFFERENCE
