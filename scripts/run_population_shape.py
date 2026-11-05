"""Stage 5: persistence diagrams of the cached last-token states.

Reads the three local caches, applies docs/stage5_protocol.md, and writes
data/population_shape_summary.json and a figure of the middle-layer diagrams.
The model is not loaded. Nothing here calls homology_decision.
"""

import json
import time
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform

from src.specificity.corpus import (
    PROMPT_VERSION,
    SECOND_CANARY_VERSION,
    SUMMARISE_ONLY_VERSION,
)
from src.evaluation.wasserstein import paired_permutation_test
from src.topology.persistence import (
    max_persistence,
    normalise_scale,
    persistence_diagrams,
    prepare_clouds,
    total_persistence,
)
from src.topology.stage5 import (
    ALPHA,
    BASELINE_THRESHOLD,
    COMPARISONS,
    HOMOLOGY_DIMENSIONS,
    LAYERS,
    N_COMPONENTS,
    N_PERMUTATIONS,
    PERMUTATION_SEED,
    PRIMARY_LAYER,
    RUNS,
    TOPOLOGY_THRESHOLD,
    compare_clouds,
    shape_outcome,
)

VERSIONS = {
    "pilot": PROMPT_VERSION,
    "summarise_only": SUMMARISE_ONLY_VERSION,
    "second_canary": SECOND_CANARY_VERSION,
}
VARIANTS = ("clean", "injection", "quoted")
N_BASES = 30
SUMMARY_PATH = Path("data/population_shape_summary.json")
FIGURE_PATH = Path("docs/demos/stage5-population-shape/diagrams.png")


def load_vectors(run: str) -> dict[str, dict[str, np.ndarray]]:
    cache = Path(RUNS[run])
    vectors = {layer: {variant: [] for variant in VARIANTS} for layer in LAYERS}
    for base_id in range(N_BASES):
        for variant in VARIANTS:
            path = cache / f"{base_id:02d}_{variant}.json"
            if not path.exists():
                raise FileNotFoundError(f"missing {path}")
            record = json.loads(path.read_text())
            if record.get("prompt_version") != VERSIONS[run] or not record.get("complete"):
                raise RuntimeError(f"{path} is not a complete {VERSIONS[run]} record")
            if record["base_id"] != base_id or record["variant"] != variant:
                raise RuntimeError(f"{path} holds the wrong email")
            for layer in LAYERS:
                vectors[layer][variant].append(record["layers"][layer]["last_document"])
    return {
        layer: {variant: np.array(rows, dtype=np.float64) for variant, rows in by_variant.items()}
        for layer, by_variant in vectors.items()
    }


def describe(cloud: np.ndarray) -> dict:
    scaled = normalise_scale(cloud)
    diagrams = persistence_diagrams(scaled)
    distances = squareform(pdist(scaled))
    np.fill_diagonal(distances, np.inf)
    nearest = distances.min(axis=1)
    loneliest = int(nearest.argmax())
    return {
        "n_points": int(cloud.shape[0]),
        "n_dimensions": int(cloud.shape[1]),
        "h0_total_persistence": total_persistence(diagrams[0]),
        "h1_count": int(len(diagrams[1])),
        "h1_total_persistence": total_persistence(diagrams[1]),
        "h1_max_persistence": max_persistence(diagrams[1]),
        "median_nearest_neighbour": float(np.median(nearest)),
        "most_isolated_base_id": loneliest,
        "most_isolated_nearest_neighbour": float(nearest[loneliest]),
    }


def plot(diagrams: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    titles = {
        "pilot": "pilot (rule in system message)",
        "summarise_only": "summarise-only, ALPHA",
        "second_canary": "summarise-only, BETA",
    }
    figure, axes = plt.subplots(3, 3, figsize=(10.5, 10), sharex=True, sharey=True)
    limit = 1.15
    for row, run in enumerate(RUNS):
        for column, variant in enumerate(VARIANTS):
            axis = axes[row][column]
            axis.plot([0, limit], [0, limit], color="#999999", linewidth=0.8)
            h0 = np.array(diagrams[run][variant]["h0"]).reshape(-1, 2)
            h1 = np.array(diagrams[run][variant]["h1"]).reshape(-1, 2)
            off_scale = h0[h0[:, 1] > limit]
            h0 = h0[h0[:, 1] <= limit]
            axis.scatter(h0[:, 0], h0[:, 1], s=14, color="#2b6cb0", label="H0 clusters")
            axis.scatter(h1[:, 0], h1[:, 1], s=22, color="#dd6b20", marker="^", label="H1 loops")
            for _, death in off_scale:
                axis.annotate(
                    f"one isolated email,\nmerges at {death:.2f}",
                    xy=(0.0, limit * 0.98),
                    xytext=(0.12, limit * 0.84),
                    fontsize=8,
                    arrowprops={"arrowstyle": "->", "color": "#2b6cb0"},
                )
            axis.set_xlim(0, limit)
            axis.set_ylim(0, limit)
            if row == 0:
                axis.set_title(variant, fontsize=12)
            if column == 0:
                axis.set_ylabel(f"{titles[run]}\ndeath", fontsize=10)
            if row == 2:
                axis.set_xlabel("birth")
    axes[0][0].legend(loc="lower right", fontsize=8)
    figure.suptitle(
        "Stage 5: persistence diagrams of 30 last-email-token states per cloud\n"
        "middle layer, location removed, scaled to median distance 1",
        fontsize=12,
    )
    figure.tight_layout()
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=130)
    plt.close(figure)


def main() -> None:
    started = time.time()
    summary = {
        "stage": 5,
        "protocol": "docs/stage5_protocol.md",
        "passes_into_homology_decision": False,
        "constants": {
            "n_components": N_COMPONENTS,
            "n_permutations": N_PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "alpha": ALPHA,
            "topology_threshold": TOPOLOGY_THRESHOLD,
            "baseline_threshold": BASELINE_THRESHOLD,
            "primary_layer": PRIMARY_LAYER,
            "homology_dimensions": list(HOMOLOGY_DIMENSIONS),
            "diagram_distance": "1-Wasserstein, L-infinity ground metric",
            "baseline": "1-Wasserstein between pairwise-distance distributions",
        },
        "runs": {},
        "outcomes": {},
        "diagrams": {},
    }
    for run in RUNS:
        vectors = load_vectors(run)
        run_report = {"prompt_version": VERSIONS[run], "cache": RUNS[run], "layers": {}}
        for layer in LAYERS:
            clouds = prepare_clouds(vectors[layer], N_COMPONENTS, PERMUTATION_SEED)
            layer_report = {
                "clouds": {variant: describe(clouds[variant]) for variant in VARIANTS},
                "comparisons": {},
            }
            for left, right in COMPARISONS:
                name = f"{left}_vs_{right}"
                normalised = paired_permutation_test(
                    clouds[left], clouds[right], compare_clouds, N_PERMUTATIONS, PERMUTATION_SEED
                )
                unscaled = paired_permutation_test(
                    clouds[left],
                    clouds[right],
                    lambda a, b: compare_clouds(a, b, normalise=False),
                    N_PERMUTATIONS,
                    PERMUTATION_SEED,
                )
                layer_report["comparisons"][name] = {
                    "normalised": normalised,
                    "unscaled": unscaled,
                }
                print(
                    f"{run:15s} {layer:6s} {name:20s} "
                    + "  ".join(
                        f"{stat}: {values['observed']:.3f} p={values['p_value']:.3f}"
                        for stat, values in normalised.items()
                    ),
                    flush=True,
                )
            run_report["layers"][layer] = layer_report
            if layer == PRIMARY_LAYER:
                summary["diagrams"][run] = {}
                for variant in VARIANTS:
                    diagrams = persistence_diagrams(normalise_scale(clouds[variant]))
                    summary["diagrams"][run][variant] = {
                        f"h{dimension}": [
                            [round(float(birth), 6), round(float(death), 6)]
                            for birth, death in diagrams[dimension]
                        ]
                        for dimension in HOMOLOGY_DIMENSIONS
                    }
        primary = run_report["layers"][PRIMARY_LAYER]["comparisons"]
        summary["outcomes"][run] = {
            name: shape_outcome(
                {
                    dimension: result["normalised"][f"h{dimension}"]["p_value"]
                    for dimension in HOMOLOGY_DIMENSIONS
                },
                result["normalised"]["spacing"]["p_value"],
            )
            for name, result in primary.items()
        }
        summary["runs"][run] = run_report
    summary["elapsed_seconds"] = round(time.time() - started, 1)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    plot(summary["diagrams"])
    print(json.dumps(summary["outcomes"], indent=2))
    print(f"wrote {SUMMARY_PATH} and {FIGURE_PATH} in {summary['elapsed_seconds']} s")


if __name__ == "__main__":
    main()
