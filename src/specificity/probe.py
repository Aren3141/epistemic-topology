"""Email-level linear probe and centroid score.

PCA and logistic regression are fit inside each training fold. Base emails
never appear on both sides of a fold. The centroid distance is not trained.

`mention_within_injection` is a follow-up on the summarise-only cache. It
holds the attack sentence fixed and is not an input to `homology_decision`.
"""

from typing import Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.specificity.gates import N_SPLITS, PCA_COMPONENTS, SEED

# The October pilot. `evaluate_layer` uses these unless a caller adds a task.
PRE_REGISTERED_TASKS = ("clean_vs_injection", "obeyed_vs_quoted")
# Stage 3. Positives and negatives are both injections, so the attack sentence
# is present in every row. This score cannot open the homology gate.
MENTION_WITHIN_INJECTION = "mention_within_injection"


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
    if task == MENTION_WITHIN_INJECTION:
        if record["variant"] != "injection":
            return None
        return 1 if record["contains_canary"] else 0
    raise ValueError(f"unknown task: {task}")


def task_label(record: dict, task: str) -> Optional[int]:
    return _kept(record, task)


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
    aligned = aligned_oof_probabilities(features, labels, groups)
    scored = np.isfinite(aligned)
    if not scored.any():
        return np.array([]), np.array([])
    return labels[scored], aligned[scored]


def aligned_oof_probabilities(
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
) -> np.ndarray:
    """Probability of the positive class for every row. NaN if that row was not scored."""
    aligned = np.full(len(labels), np.nan, dtype=np.float64)
    if len(labels) == 0 or len(np.unique(groups)) < N_SPLITS:
        return aligned
    splitter = GroupKFold(n_splits=N_SPLITS)
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
        aligned[test_index] = probabilities
    return aligned


def task_probabilities(
    records: list[dict], layer_name: str, task: str
) -> list[float | None]:
    """Out-of-fold positive-class probability for every record. None if excluded."""
    features = []
    labels = []
    groups = []
    indexes = []
    for index, record in enumerate(records):
        label = task_label(record, task)
        if label is None:
            continue
        features.append(record["layers"][layer_name]["last_document"])
        labels.append(label)
        groups.append(record["base_id"])
        indexes.append(index)
    scores: list[float | None] = [None] * len(records)
    if not indexes:
        return scores
    aligned = aligned_oof_probabilities(
        np.array(features, dtype=np.float64),
        np.array(labels, dtype=np.int64),
        np.array(groups, dtype=np.int64),
    )
    for local, index in enumerate(indexes):
        value = float(aligned[local])
        scores[index] = None if not np.isfinite(value) else value
    return scores


def evaluate_layer(
    records: list[dict],
    layer_name: str,
    tasks: tuple[str, ...] = PRE_REGISTERED_TASKS,
) -> dict:
    report = {}
    for task in tasks:
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
