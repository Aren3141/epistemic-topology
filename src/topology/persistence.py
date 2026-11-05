"""Persistence diagrams for small clouds of residual-stream states.

A Vietoris–Rips diagram depends only on pairwise distances, so it ignores
translation and rotation of the cloud. That is why it measures shape and the
linear probe measures location. Clouds are capped at 150 points and 32
dimensions, as the study's hardware notes require.
"""

import numpy as np
from ripser import ripser
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

MAX_POINTS = 150
MAX_DIMENSIONS = 32


def prepare_clouds(
    vectors_by_label: dict[str, np.ndarray],
    n_components: int,
    seed: int,
) -> dict[str, np.ndarray]:
    """Centre each labelled cloud on its own mean, then project all of them.

    The scaler and PCA are fit once on the pooled centred vectors. Rows keep
    their order, so row i of every cloud is the same base email.
    """
    centred = {
        label: np.asarray(vectors, dtype=np.float64) - np.asarray(vectors, dtype=np.float64).mean(axis=0)
        for label, vectors in vectors_by_label.items()
    }
    pooled = np.vstack(list(centred.values()))
    components = min(n_components, pooled.shape[0] - 1, pooled.shape[1])
    if components > MAX_DIMENSIONS:
        raise ValueError(f"at most {MAX_DIMENSIONS} dimensions per cloud")
    scaler = StandardScaler().fit(pooled)
    pca = PCA(n_components=components, random_state=seed).fit(scaler.transform(pooled))
    return {
        label: pca.transform(scaler.transform(cloud))
        for label, cloud in centred.items()
    }


def normalise_scale(cloud: np.ndarray) -> np.ndarray:
    """Divide a cloud by its median pairwise distance."""
    median = float(np.median(pdist(cloud)))
    if median <= 0.0:
        raise ValueError("a cloud with zero median distance has no scale")
    return cloud / median


def persistence_diagrams(cloud: np.ndarray, max_dimension: int = 1) -> list[np.ndarray]:
    """Rips diagrams H0..H{max_dimension}, with infinite bars removed."""
    cloud = np.asarray(cloud, dtype=np.float64)
    if cloud.ndim != 2:
        raise ValueError("a cloud is a 2-D array of points")
    if cloud.shape[0] > MAX_POINTS:
        raise ValueError(f"at most {MAX_POINTS} points per cloud")
    if cloud.shape[1] > MAX_DIMENSIONS:
        raise ValueError(f"at most {MAX_DIMENSIONS} dimensions per cloud")
    diagrams = ripser(cloud, maxdim=max_dimension)["dgms"]
    return [diagram[np.isfinite(diagram[:, 1])] for diagram in diagrams]


def total_persistence(diagram: np.ndarray) -> float:
    if len(diagram) == 0:
        return 0.0
    return float((diagram[:, 1] - diagram[:, 0]).sum())


def max_persistence(diagram: np.ndarray) -> float:
    if len(diagram) == 0:
        return 0.0
    return float((diagram[:, 1] - diagram[:, 0]).max())
