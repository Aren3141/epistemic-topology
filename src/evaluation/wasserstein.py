"""Distances between persistence diagrams and between point-cloud spacings.

`diagram_distance` is the 1-Wasserstein distance with the L-infinity ground
metric. A point may be matched to the diagonal at cost (death - birth) / 2.
`spacing_distance` is the geometric baseline: the 1-Wasserstein distance
between two clouds' distributions of pairwise distances. It ignores
translation and rotation, like homology, but not connectivity or loops.
"""

from typing import Callable

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist
from scipy.stats import wasserstein_distance


def diagram_distance(
    left: np.ndarray, right: np.ndarray, ground: str = "linf"
) -> float:
    """1-Wasserstein distance between two diagrams.

    `ground="linf"` is the stage 5 statistic. `ground="euclidean"` is the
    convention persim uses, kept so the matching can be checked against it.
    """
    left = np.asarray(left, dtype=np.float64).reshape(-1, 2)
    right = np.asarray(right, dtype=np.float64).reshape(-1, 2)
    n_left, n_right = len(left), len(right)
    if n_left == 0 and n_right == 0:
        return 0.0
    if ground == "linf":
        diagonal_factor = 0.5
    elif ground == "euclidean":
        diagonal_factor = 1.0 / np.sqrt(2.0)
    else:
        raise ValueError(f"unknown ground metric: {ground}")
    to_diagonal_left = (left[:, 1] - left[:, 0]) * diagonal_factor
    to_diagonal_right = (right[:, 1] - right[:, 0]) * diagonal_factor
    size = n_left + n_right
    # A cost that no optimal matching would choose. Keeps the solver finite.
    blocked = 1.0 + 2.0 * (to_diagonal_left.sum() + to_diagonal_right.sum())
    cost = np.zeros((size, size), dtype=np.float64)
    if n_left and n_right:
        birth_gap = np.abs(left[:, None, 0] - right[None, :, 0])
        death_gap = np.abs(left[:, None, 1] - right[None, :, 1])
        if ground == "linf":
            cost[:n_left, :n_right] = np.maximum(birth_gap, death_gap)
        else:
            cost[:n_left, :n_right] = np.hypot(birth_gap, death_gap)
    cost[:n_left, n_right:] = blocked
    cost[:n_left, n_right:][np.arange(n_left), np.arange(n_left)] = to_diagonal_left
    cost[n_left:, :n_right] = blocked
    cost[n_left:, :n_right][np.arange(n_right), np.arange(n_right)] = to_diagonal_right
    rows, columns = linear_sum_assignment(cost)
    return float(cost[rows, columns].sum())


def spacing_distance(left: np.ndarray, right: np.ndarray) -> float:
    return float(wasserstein_distance(pdist(left), pdist(right)))


def paired_permutation_test(
    left: np.ndarray,
    right: np.ndarray,
    compare: Callable[[np.ndarray, np.ndarray], dict[str, float]],
    n_permutations: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    """Swap row i between the two clouds with probability one half.

    Row i of `left` and row i of `right` come from the same base email. The
    p-value counts permutations whose statistic is at least the observed one.
    """
    if left.shape != right.shape:
        raise ValueError("paired clouds must have the same shape")
    observed = compare(left, right)
    at_least = {name: 0 for name in observed}
    totals = {name: 0.0 for name in observed}
    rng = np.random.default_rng(seed)
    for _ in range(n_permutations):
        swap = rng.random(left.shape[0]) < 0.5
        permuted_left = np.where(swap[:, None], right, left)
        permuted_right = np.where(swap[:, None], left, right)
        values = compare(permuted_left, permuted_right)
        for name, value in values.items():
            totals[name] += value
            if value >= observed[name]:
                at_least[name] += 1
    return {
        name: {
            "observed": float(observed[name]),
            "null_mean": totals[name] / n_permutations,
            "p_value": (1 + at_least[name]) / (1 + n_permutations),
        }
        for name in observed
    }
