import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import pairwise_distances
from ripser import ripser
from persim import plot_diagrams, wasserstein
from typing import Dict, Any, Tuple


def balance_and_subsample(
    features: np.ndarray,
    labels: np.ndarray,
    max_n: int = 200,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    enforces strict density limits to guarantee cpu completion.
    uses fixed random seed for reproducibility.
    """
    rng = np.random.default_rng(seed)

    balanced_features = []
    balanced_labels = []

    for label_val in np.unique(labels):
        idx = np.where(labels == label_val)[0]

        sample_size = min(len(idx), max_n)
        selected_idx = rng.choice(idx, size=sample_size, replace=False)

        balanced_features.append(features[selected_idx])
        balanced_labels.extend([label_val] * sample_size)

    return np.vstack(balanced_features), np.array(balanced_labels)


def compute_topology(features: np.ndarray) -> Dict[str, Any]:
    """
    computes vietoris-rips persistence using euclidean geometry
    on l2-normalised embeddings (stabilises metric structure).
    """
    # normalise to remove scale artefacts (critical for VR stability)
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    features = features / norms

    distance_matrix = pairwise_distances(features, metric='euclidean')

    topology_data = ripser(
        distance_matrix,
        distance_matrix=True,
        maxdim=1
    )

    return topology_data


def calculate_wasserstein(dgm_a: np.ndarray, dgm_b: np.ndarray) -> float:
    """
    computes wasserstein distance between persistence diagrams.
    no artificial fallback scaling.
    """
    if len(dgm_a) == 0 and len(dgm_b) == 0:
        return 0.0

    return float(wasserstein(dgm_a, dgm_b))


def generate_diagram(topology_data: Dict[str, Any], label: str) -> None:
    """
    outputs a single persistence diagram for the specified regime.
    """
    plt.figure(figsize=(6, 6))

    plot_diagrams(topology_data['dgms'], show=False)

    plt.title(f"persistence diagram: {label} regime")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"persistence_{label}.png", dpi=300)
    plt.close()