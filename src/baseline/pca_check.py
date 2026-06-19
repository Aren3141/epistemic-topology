import numpy as np
import torch
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from typing import List, Tuple, Optional

def process_tensors(tensors: List[torch.Tensor], labels: List[int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    aggregates token-level tensors into a unified dataset.
    results generated here are strictly exploratory.
    """
    assert len(tensors) == len(labels), "tensor and label counts must match"

    all_points = []
    all_labels = []

    for i, tensor in enumerate(tensors):
        # enforce hardware constraint strictly
        assert tensor.device.type == 'cpu', "fatal: tensor not on cpu. mps causes numerical drift."
        
        numpy_tensor = tensor.detach().numpy()
        num_tokens = numpy_tensor.shape[0]
        
        all_points.append(numpy_tensor)
        all_labels.extend([labels[i]] * num_tokens)

    unified_points = np.vstack(all_points)
    unified_labels = np.array(all_labels)

    return unified_points, unified_labels

def run_pca_analysis(features: np.ndarray, labels: np.ndarray) -> Tuple[PCA, Optional[float]]:
    """
    applies 2d pca and computes silhouette score.
    any separation observed only suggests linear structure.
    """
    pca_model = PCA(n_components=2)
    reduced_features = pca_model.fit_transform(features)
    
    variance_ratio = pca_model.explained_variance_ratio_
    print(f"explained variance ratio (pc1, pc2): {variance_ratio}")

    sil_score = None
    # restrict silhouette computation to prevent out-of-memory errors on cpu
    if features.shape[0] <= 50000:
        sil_score = float(silhouette_score(reduced_features, labels))
        print(f"silhouette score indicates cluster separation: {sil_score:.4f}")
    else:
        print("dataset exceeds 50k points; skipping silhouette score to maintain performance")

    _plot_pca(reduced_features, labels)

    return pca_model, sil_score

def _plot_pca(reduced_features: np.ndarray, labels: np.ndarray) -> None:
    """
    generates a strictly formatted scatter plot of the principal components.
    """
    plt.figure(figsize=(8, 6))

    colour_map = {0: 'blue', 1: 'red', 2: 'green'}
    label_names = {0: 'factual', 1: 'inconsistent', 2: 'neutral'}

    for label_val in np.unique(labels):
        idx = labels == label_val
        plt.scatter(
            reduced_features[idx, 0],
            reduced_features[idx, 1],
            c=colour_map[label_val],
            label=label_names[label_val],
            alpha=0.5,
            s=10
        )

    plt.title("exploratory pca of generation regimes")
    plt.xlabel("principal component 1")
    plt.ylabel("principal component 2")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("pca_baseline_check.png", dpi=300)
    plt.close()