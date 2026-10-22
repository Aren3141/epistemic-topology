"""Email-level linear probe and centroid score.

PCA and logistic regression are fit inside each training fold. Base emails
never appear on both sides of a fold. The centroid distance is not trained.
"""

from typing import Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.specificity.gates import N_SPLITS, PCA_COMPONENTS, SEED


def _kept(record: dict, task: str) -> Optional[int]:
    if task == "clean_vs_injection":
        if record["variant"] == "clean":
            return 0
        if record["variant"] == "injection":
            return 1
        return None
    if task == "obeyed_vs_quoted":
        if record["variant"] == "injection" and record["obedience"]:
            return 1
        if record["variant"] == "quoted" and not record["obedience"]:
            return 0
        return None
    raise ValueError(f"unknown task: {task}")


def _auroc(labels: np.ndarray, scores: np.ndarray) -> Optional[float]:
    if len(labels) == 0 or len(np.unique(labels)) < 2:
        return None
    return float(roc_auc_score(labels, scores))


def _select(records: list[dict], layer_name: str, task: str) -> dict:
    features = []
    labels = []
    groups = []
    centroids = []
    for record in records:
        label = _kept(record, task)
        if label is None:
            continue
        features.append(record["layers"][layer_name]["last_document"])
        labels.append(label)
        groups.append(record["base_id"])
        centroids.append(record["layers"][layer_name]["centroid_distance"])
    return {
        "features": np.array(features, dtype=np.float64),
        "labels": np.array(labels, dtype=np.int64),
        "groups": np.array(groups, dtype=np.int64),
        "centroids": np.array(centroids, dtype=np.float64),
    }


def out_of_fold_probe(
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return scored labels and probabilities. Unscored rows are omitted."""
    splitter = GroupKFold(n_splits=N_SPLITS)
    scored_labels = []
    scored_probabilities = []
    for train_index, test_index in splitter.split(features, labels, groups):
        train_labels = labels[train_index]
        if len(np.unique(train_labels)) < 2:
            continue
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(features[train_index])
        test_scaled = scaler.transform(features[test_index])
        components = min(
            PCA_COMPONENTS,
            train_scaled.shape[0] - 1,
            train_scaled.shape[1],
        )
        if components < 1:
            continue
        pca = PCA(n_components=components, random_state=SEED)
        train_reduced = pca.fit_transform(train_scaled)
        test_reduced = pca.transform(test_scaled)
        classifier = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            random_state=SEED,
        )
        classifier.fit(train_reduced, train_labels)
        probabilities = classifier.predict_proba(test_reduced)[:, 1]
        scored_labels.append(labels[test_index])
        scored_probabilities.append(probabilities)
    if not scored_labels:
        return np.array([]), np.array([])
    return np.concatenate(scored_labels), np.concatenate(scored_probabilities)


def evaluate_layer(records: list[dict], layer_name: str) -> dict:
    report = {}
    for task in ("clean_vs_injection", "obeyed_vs_quoted"):
        rows = _select(records, layer_name, task)
        unique_groups = len(np.unique(rows["groups"])) if len(rows["groups"]) else 0
        if unique_groups < N_SPLITS or len(rows["labels"]) == 0:
            probe_labels = np.array([])
            probe_scores = np.array([])
        else:
            probe_labels, probe_scores = out_of_fold_probe(
                rows["features"], rows["labels"], rows["groups"]
            )
        report[task] = {
            "n": int(len(rows["labels"])),
            "n_positive": int(rows["labels"].sum()) if len(rows["labels"]) else 0,
            "n_groups": int(unique_groups),
            "probe_auroc": _auroc(probe_labels, probe_scores),
            "probe_scored": int(len(probe_labels)),
            "centroid_auroc": _auroc(rows["labels"], rows["centroids"]),
        }
    return report
