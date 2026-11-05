"""Pre-registered constants, statistics, and outcome rule for stage 6, token-cloud shape.

Fixed on 5 November 2026 before any token-level activation was extracted. The
prose copy is docs/stage6_protocol.md. Nothing here feeds homology_decision.
"""

import numpy as np
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.specificity.corpus import (
    CANARY,
    PROMPT_VERSION,
    SECOND_CANARY,
    SECOND_CANARY_VERSION,
    SUMMARISE_ONLY_PROMPT,
    SUMMARISE_ONLY_VERSION,
    SYSTEM_PROMPT,
)
from src.specificity.gates import PCA_COMPONENTS, SEED
from src.topology.persistence import (
    MAX_DIMENSIONS,
    max_persistence,
    normalise_scale,
    persistence_diagrams,
    total_persistence,
)

RUNS = {
    "pilot": {
        "system_prompt": SYSTEM_PROMPT,
        "prompt_version": PROMPT_VERSION,
        "canary": CANARY,
        "cache": "results/cache",
    },
    "summarise_only": {
        "system_prompt": SUMMARISE_ONLY_PROMPT,
        "prompt_version": SUMMARISE_ONLY_VERSION,
        "canary": CANARY,
        "cache": "results/cache_summarise_only",
    },
    "second_canary": {
        "system_prompt": SUMMARISE_ONLY_PROMPT,
        "prompt_version": SECOND_CANARY_VERSION,
        "canary": SECOND_CANARY,
        "cache": "results/cache_second_canary",
    },
}
VARIANTS = ("injection", "quoted")
PRIMARY_LAYER = "middle"
LAYERS = ("middle", "early")
N_COMPONENTS = PCA_COMPONENTS
N_PERMUTATIONS = 999
PERMUTATION_SEED = SEED
STATE_TOLERANCE = 1e-4

TOPOLOGY_STATISTICS = ("h0_total", "h1_total", "h1_max")
GEOMETRY_STATISTICS = ("separation", "attachment")
ALPHA = 0.05
TOPOLOGY_THRESHOLD = ALPHA / (len(RUNS) * len(TOPOLOGY_STATISTICS))
GEOMETRY_THRESHOLD = ALPHA / (len(RUNS) * len(GEOMETRY_STATISTICS))

BEYOND_GEOMETRY = "shape differs, beyond geometry"
WITH_GEOMETRY = "shape differs, geometry already shows it"
GEOMETRY_ONLY = "geometry differs, topology does not"
NO_DIFFERENCE = "no difference detected"


def token_positions(
    offsets: list[tuple[int, int]], start: int, end: int
) -> list[int]:
    """Tokens that start inside [start, end). Zero-width tokens are skipped."""
    return [
        index
        for index, (token_start, token_end) in enumerate(offsets)
        if token_start != token_end and start <= token_start < end
    ]


def fit_projection(
    pooled: np.ndarray, n_components: int = N_COMPONENTS, seed: int = PERMUTATION_SEED
):
    """Scaler and PCA fit once on every token of one run and layer."""
    pooled = np.asarray(pooled, dtype=np.float64)
    components = min(n_components, pooled.shape[0] - 1, pooled.shape[1])
    if components > MAX_DIMENSIONS:
        raise ValueError(f"at most {MAX_DIMENSIONS} dimensions per cloud")
    scaler = StandardScaler().fit(pooled)
    pca = PCA(n_components=components, random_state=seed).fit(scaler.transform(pooled))

    def project(rows: np.ndarray) -> np.ndarray:
        return pca.transform(scaler.transform(np.asarray(rows, dtype=np.float64)))

    return project


def cloud_statistics(
    email: np.ndarray, sentence: np.ndarray, normalise: bool = True
) -> dict[str, float]:
    """The five per-cloud statistics for one email's tokens plus its sentence."""
    email = np.asarray(email, dtype=np.float64)
    sentence = np.asarray(sentence, dtype=np.float64)
    cloud = np.vstack([email, sentence])
    if normalise:
        cloud = normalise_scale(cloud)
    email, sentence = cloud[: len(email)], cloud[len(email) :]
    diagrams = persistence_diagrams(cloud, max_dimension=1)
    return {
        "h0_total": total_persistence(diagrams[0]),
        "h1_total": total_persistence(diagrams[1]),
        "h1_max": max_persistence(diagrams[1]),
        "separation": float(np.linalg.norm(sentence.mean(axis=0) - email.mean(axis=0))),
        "attachment": float(np.median(cdist(sentence, email).min(axis=1))),
    }


def sign_flip_test(
    differences: np.ndarray,
    n_permutations: int = N_PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> dict[str, float]:
    """Two-sided paired test on the mean of per-email differences."""
    differences = np.asarray(differences, dtype=np.float64)
    if differences.ndim != 1 or len(differences) == 0:
        raise ValueError("differences are one value per pair")
    observed = float(differences.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(n_permutations, len(differences)))
    null = (signs * differences).mean(axis=1)
    count = int((np.abs(null) >= abs(observed) - 1e-12).sum())
    return {
        "observed": observed,
        "null_mean": float(null.mean()),
        "p_value": (1 + count) / (1 + n_permutations),
    }


def token_outcome(
    topology_p_values: dict[str, float], geometry_p_values: dict[str, float]
) -> str:
    """Apply the stage 6 rule to one run at the primary layer."""
    topology_passes = any(
        value <= TOPOLOGY_THRESHOLD for value in topology_p_values.values()
    )
    smallest_geometry = min(geometry_p_values.values())
    if topology_passes:
        if smallest_geometry >= ALPHA:
            return BEYOND_GEOMETRY
        return WITH_GEOMETRY
    if smallest_geometry <= GEOMETRY_THRESHOLD:
        return GEOMETRY_ONLY
    return NO_DIFFERENCE
