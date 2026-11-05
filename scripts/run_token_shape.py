"""Stage 6: persistence of each email's token cloud, order against quotation.

Reads results/token_clouds/ (written by scripts/extract_token_clouds.py),
applies docs/stage6_protocol.md, and writes data/token_shape_summary.json and
two figures. The model is not loaded. Nothing here calls homology_decision.
"""

import json
import time
from pathlib import Path

import numpy as np

from src.topology.persistence import normalise_scale, persistence_diagrams
from src.topology.stage6 import (
    ALPHA,
    GEOMETRY_STATISTICS,
    GEOMETRY_THRESHOLD,
    LAYERS,
    N_COMPONENTS,
    N_PERMUTATIONS,
    PERMUTATION_SEED,
    PRIMARY_LAYER,
    RUNS,
    TOPOLOGY_STATISTICS,
    TOPOLOGY_THRESHOLD,
    VARIANTS,
    cloud_statistics,
    fit_projection,
    sign_flip_test,
    token_outcome,
)

N_BASES = 30
CLOUDS = Path("results/token_clouds")
SUMMARY_PATH = Path("data/token_shape_summary.json")
FIGURE_DIR = Path("docs/demos/stage6-token-shape")
STATISTICS = TOPOLOGY_STATISTICS + GEOMETRY_STATISTICS
LABELS = {
    "h0_total": "H0 total persistence",
    "h1_total": "H1 total persistence",
    "h1_max": "H1 longest loop",
    "separation": "separation",
    "attachment": "attachment",
}
RUN_LABELS = {"pilot": "pilot", "summarise_only": "summarise-only", "second_canary": "second canary"}
EXAMPLE_BASE = 0


def load_run(run: str) -> dict[int, dict[str, np.lib.npyio.NpzFile]]:
    return {
        base_id: {
            variant: np.load(CLOUDS / run / f"{base_id:02d}_{variant}.npz")
            for variant in VARIANTS
        }
        for base_id in range(N_BASES)
    }


def project_run(files, layer: str) -> dict[int, dict[str, tuple[np.ndarray, np.ndarray]]]:
    pooled = [files[base_id]["injection"][f"email_{layer}"] for base_id in files]
    pooled += [
        files[base_id][variant][f"sentence_{layer}"] for base_id in files for variant in VARIANTS
    ]
    project = fit_projection(np.vstack(pooled), N_COMPONENTS, PERMUTATION_SEED)
    return {
        base_id: {
            variant: (
                project(files[base_id][variant][f"email_{layer}"]),
                project(files[base_id][variant][f"sentence_{layer}"]),
            )
            for variant in VARIANTS
        }
        for base_id in files
    }


def test_layer(clouds) -> dict:
    report = {}
    for scaling, normalise in (("normalised", True), ("unscaled", False)):
        per_email = {
            base_id: {
                variant: cloud_statistics(*clouds[base_id][variant], normalise=normalise)
                for variant in VARIANTS
            }
            for base_id in clouds
        }
        tests = {}
        for name in STATISTICS:
            injection = np.array([per_email[b]["injection"][name] for b in sorted(per_email)])
            quoted = np.array([per_email[b]["quoted"][name] for b in sorted(per_email)])
            result = sign_flip_test(injection - quoted, N_PERMUTATIONS, PERMUTATION_SEED)
            result["injection_median"] = float(np.median(injection))
            result["quoted_median"] = float(np.median(quoted))
            result["injection_larger"] = int((injection > quoted).sum())
            tests[name] = result
        report[scaling] = {
            "tests": tests,
            "per_email": {
                str(base_id): {
                    variant: {name: round(value, 6) for name, value in values.items()}
                    for variant, values in by_variant.items()
                }
                for base_id, by_variant in per_email.items()
            },
        }
    return report


def plot(summary: dict, example) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(len(RUNS), len(STATISTICS), figsize=(17, 10))
    for row, run in enumerate(RUNS):
        layer = summary["runs"][run]["layers"][PRIMARY_LAYER]["normalised"]
        for column, name in enumerate(STATISTICS):
            axis = axes[row, column]
            injection = [layer["per_email"][b]["injection"][name] for b in layer["per_email"]]
            quoted = [layer["per_email"][b]["quoted"][name] for b in layer["per_email"]]
            low = min(injection + quoted)
            high = max(injection + quoted)
            pad = 0.05 * (high - low or 1.0)
            axis.plot([low - pad, high + pad], [low - pad, high + pad], color="0.7", lw=1)
            axis.scatter(quoted, injection, s=14, color="#c0392b")
            axis.set_xlim(low - pad, high + pad)
            axis.set_ylim(low - pad, high + pad)
            p_value = layer["tests"][name]["p_value"]
            threshold = TOPOLOGY_THRESHOLD if name in TOPOLOGY_STATISTICS else GEOMETRY_THRESHOLD
            marker = " (passes)" if p_value <= threshold else ""
            axis.set_title(f"{RUN_LABELS[run]}: {LABELS[name]}\np = {p_value:.3f}{marker}", fontsize=9)
            if column == 0:
                axis.set_ylabel("injection (order)")
            if row == len(RUNS) - 1:
                axis.set_xlabel("quoted")
            axis.tick_params(labelsize=7)
    figure.suptitle(
        "Stage 6: one dot per email. Above the grey line, the order's cloud has the larger value.",
        fontsize=11,
    )
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "paired_statistics.png", dpi=110)
    plt.close(figure)

    figure, axes = plt.subplots(2, 2, figsize=(10, 9))
    for column, variant in enumerate(VARIANTS):
        email, sentence = example[variant]
        cloud = normalise_scale(np.vstack([email, sentence]))
        email, sentence = cloud[: len(email)], cloud[len(email) :]
        axis = axes[0, column]
        axis.scatter(email[:, 0], email[:, 1], s=14, color="0.6", label="email tokens")
        axis.scatter(sentence[:, 0], sentence[:, 1], s=22, color="#c0392b", label="sentence tokens")
        axis.plot(sentence[:, 0], sentence[:, 1], color="#c0392b", lw=0.6, alpha=0.6)
        axis.set_title(f"pilot, email {EXAMPLE_BASE}, {variant}: first two of 16 components", fontsize=9)
        axis.legend(fontsize=8)
        diagrams = persistence_diagrams(cloud, max_dimension=1)
        axis = axes[1, column]
        limit = max(float(diagrams[0][:, 1].max()), 1e-6) * 1.05
        axis.plot([0, limit], [0, limit], color="0.7", lw=1)
        axis.scatter(diagrams[0][:, 0], diagrams[0][:, 1], s=12, color="#2c3e50", label="H0 (clusters)")
        if len(diagrams[1]):
            axis.scatter(diagrams[1][:, 0], diagrams[1][:, 1], s=18, color="#e67e22", label="H1 (loops)")
        axis.set_xlim(0, limit)
        axis.set_ylim(0, limit)
        axis.set_xlabel("birth")
        axis.set_ylabel("death")
        axis.set_title(f"{variant}: persistence diagram", fontsize=9)
        axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "example_email.png", dpi=110)
    plt.close(figure)


def main() -> None:
    started = time.time()
    checks = json.loads((CLOUDS / "checks.json").read_text())
    summary = {
        "stage": 6,
        "protocol": "docs/stage6_protocol.md",
        "passes_into_homology_decision": False,
        "constants": {
            "n_components": N_COMPONENTS,
            "n_permutations": N_PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "alpha": ALPHA,
            "topology_threshold": TOPOLOGY_THRESHOLD,
            "geometry_threshold": GEOMETRY_THRESHOLD,
            "primary_layer": PRIMARY_LAYER,
            "topology_statistics": list(TOPOLOGY_STATISTICS),
            "geometry_statistics": list(GEOMETRY_STATISTICS),
            "difference": "injection minus quoted, paired by base email",
        },
        "checks": {run: checks[run] for run in RUNS},
        "runs": {},
        "outcomes": {},
    }
    example = None
    for run in RUNS:
        files = load_run(run)
        first = files[0]["injection"]
        run_report = {
            "prompt_version": RUNS[run]["prompt_version"],
            "canary": RUNS[run]["canary"],
            "n_email_tokens": [len(files[b]["injection"]["email_ids"]) for b in files],
            "n_sentence_tokens": len(first["sentence_ids"]),
            "layers": {},
        }
        for layer in LAYERS:
            clouds = project_run(files, layer)
            if run == "pilot" and layer == PRIMARY_LAYER:
                example = clouds[EXAMPLE_BASE]
            run_report["layers"][layer] = test_layer(clouds)
            tests = run_report["layers"][layer]["normalised"]["tests"]
            print(
                f"{run:15s} {layer:6s} "
                + "  ".join(
                    f"{name}: {values['injection_median']:.3f}/{values['quoted_median']:.3f} p={values['p_value']:.3f}"
                    for name, values in tests.items()
                ),
                flush=True,
            )
        primary = run_report["layers"][PRIMARY_LAYER]["normalised"]["tests"]
        summary["outcomes"][run] = token_outcome(
            {name: primary[name]["p_value"] for name in TOPOLOGY_STATISTICS},
            {name: primary[name]["p_value"] for name in GEOMETRY_STATISTICS},
        )
        summary["runs"][run] = run_report
    summary["elapsed_seconds"] = round(time.time() - started, 1)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    plot(summary, example)
    print(json.dumps(summary["outcomes"], indent=2))
    print(f"wrote {SUMMARY_PATH} and {FIGURE_DIR} in {summary['elapsed_seconds']} s")


if __name__ == "__main__":
    main()
