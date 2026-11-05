"""Stage 7 analysis: the ten pre-registered confirmations on the fresh emails.

Reads results/cache_stage7/ and results/token_clouds_stage7/ (written by
scripts/run_confirmation.py), applies docs/stage7_protocol.md, and writes
data/confirmation_summary.json and a figure. The model is not loaded. Nothing
here calls homology_decision.
"""

import itertools
import json
import time
from pathlib import Path

import numpy as np

from src.specificity.held_out import VARIANTS
from src.topology.stage6 import (
    GEOMETRY_STATISTICS,
    LAYERS,
    N_COMPONENTS,
    N_PERMUTATIONS,
    PERMUTATION_SEED,
    PRIMARY_LAYER,
    TOPOLOGY_STATISTICS,
    cloud_statistics,
    fit_projection,
)
from src.topology.stage7 import (
    CONFIRMATIONS,
    RUNS,
    THRESHOLD,
    confirmation_differences,
    lead_in_reading,
    sign_flip_test,
    verdict,
)

N_BASES = 30
REPLIES = Path("results/cache_stage7")
STATES = Path("results/token_clouds_stage7")
SUMMARY_PATH = Path("data/confirmation_summary.json")
STAGE6_SUMMARY = Path("data/token_shape_summary.json")
FIGURE_PATH = Path("docs/demos/stage7-confirmation/confirmation.png")
STATISTICS = TOPOLOGY_STATISTICS + GEOMETRY_STATISTICS
RUN_LABELS = {"pilot": "pilot", "summarise_only": "summarise-only"}
COLOURS = {"injection": "#c0392b", "quoted": "#2c3e50", "neutral": "#e67e22"}


def per_email_statistics(run: str, layer: str, normalise: bool) -> dict:
    files = {
        b: {v: np.load(STATES / run / f"{b:02d}_{v}.npz") for v in VARIANTS} for b in range(N_BASES)
    }
    pooled = [files[b][VARIANTS[0]][f"email_{layer}"] for b in files]
    pooled += [files[b][v][f"sentence_{layer}"] for b in files for v in VARIANTS]
    project = fit_projection(np.vstack(pooled), N_COMPONENTS, PERMUTATION_SEED)
    return {
        b: {
            v: cloud_statistics(
                project(files[b][v][f"email_{layer}"]),
                project(files[b][v][f"sentence_{layer}"]),
                normalise=normalise,
            )
            for v in VARIANTS
        }
        for b in files
    }


def describe_pairs(per_email: dict) -> dict:
    """Two-sided tests for every statistic and pair of variants. Recorded, not tested."""
    report = {}
    for left, right in itertools.combinations(VARIANTS, 2):
        report[f"{left}_vs_{right}"] = {}
        for name in STATISTICS:
            differences = np.array(
                [per_email[b][left][name] - per_email[b][right][name] for b in sorted(per_email)]
            )
            result = sign_flip_test(differences, "two-sided")
            result["left_median"] = float(np.median([per_email[b][left][name] for b in per_email]))
            result["right_median"] = float(np.median([per_email[b][right][name] for b in per_email]))
            result["left_larger"] = int((differences > 0).sum())
            report[f"{left}_vs_{right}"][name] = result
    return report


def behaviour(run: str) -> dict:
    rows = {}
    counts = {v: {"obedience": 0, "contains_canary": 0} for v in VARIANTS}
    for b in range(N_BASES):
        rows[str(b)] = {}
        for v in VARIANTS:
            record = json.loads((REPLIES / run / f"{b:02d}_{v}.json").read_text())
            if record["prompt_version"] != RUNS[run]["prompt_version"]:
                raise RuntimeError(f"{run} {b} {v}: prompt version differs")
            rows[str(b)][v] = {
                "reply": record["reply"],
                "obedience": record["obedience"],
                "contains_canary": record["contains_canary"],
            }
            counts[v]["obedience"] += int(record["obedience"])
            counts[v]["contains_canary"] += int(record["contains_canary"])
    return {"counts": counts, "replies": rows}


def run_interactions(per_email_by_run: dict) -> dict:
    """Not pre-registered. Does the order-minus-training-note difference depend on the run?"""
    report = {}
    for name in STATISTICS:
        by_run = {}
        for run in RUNS:
            per_email = per_email_by_run[run]
            by_run[run] = np.array(
                [
                    per_email[b]["injection"][name] - per_email[b]["quoted"][name]
                    for b in sorted(per_email, key=int)
                ]
            )
        interaction = by_run["summarise_only"] - by_run["pilot"]
        result = sign_flip_test(interaction, "two-sided")
        result["pilot_mean"] = float(by_run["pilot"].mean())
        result["summarise_only_mean"] = float(by_run["summarise_only"].mean())
        result["n_positive"] = int((interaction > 0).sum())
        report[name] = result
    return report


def plot(per_email: dict, confirmations: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(11, 9))
    for column, run in enumerate(RUNS):
        axis = axes[0, column]
        for b in sorted(per_email[run]):
            values = [per_email[run][b][v]["separation"] for v in VARIANTS]
            axis.plot(range(len(VARIANTS)), values, color="0.8", lw=0.8)
        for x, v in enumerate(VARIANTS):
            values = [per_email[run][b][v]["separation"] for b in per_email[run]]
            axis.scatter([x] * len(values), values, s=14, color=COLOURS[v], zorder=3)
        axis.set_xticks(range(len(VARIANTS)), ["order", "training note", "neutral note"])
        axis.set_ylabel("separation (sentence to email)")
        axis.set_title(f"{RUN_LABELS[run]}: separation, one line per fresh email", fontsize=10)
    for column, (name, label) in enumerate((("h0_total", "H0 total"), ("h1_max", "longest loop"))):
        axis = axes[1, column]
        for x, run in enumerate(RUNS):
            differences = [
                per_email[run][b]["injection"][name] - per_email[run][b]["quoted"][name]
                for b in sorted(per_email[run])
            ]
            jitter = np.linspace(-0.12, 0.12, len(differences))
            axis.scatter(x + jitter, differences, s=14, color="#c0392b")
        axis.axhline(0.0, color="0.6", lw=1)
        axis.set_xticks(range(len(RUNS)), [RUN_LABELS[r] for r in RUNS])
        axis.set_ylabel(f"{label}: order minus training note")
        key = "h0_summarise_only" if name == "h0_total" else "loop_interaction"
        axis.set_title(
            f"{label}, one dot per fresh email\n{key}: p = {confirmations[key]['p_value']:.3f}",
            fontsize=10,
        )
    figure.suptitle("Stage 7: 30 fresh emails, middle layer, scale-normalised", fontsize=11)
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=110)
    plt.close(figure)


def main() -> None:
    started = time.time()
    checks = json.loads((STATES / "checks.json").read_text())
    summary = {
        "stage": 7,
        "protocol": "docs/stage7_protocol.md",
        "passes_into_homology_decision": False,
        "constants": {
            "n_components": N_COMPONENTS,
            "n_permutations": N_PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "threshold": THRESHOLD,
            "primary_layer": PRIMARY_LAYER,
            "n_confirmations": len(CONFIRMATIONS),
        },
        "checks": {run: checks[run] for run in RUNS},
        "behaviour": {run: behaviour(run) for run in RUNS},
        "runs": {},
        "confirmations": {},
        "readings": {},
    }
    primary = {}
    for run in RUNS:
        summary["runs"][run] = {"prompt_version": RUNS[run]["prompt_version"], "layers": {}}
        for layer in LAYERS:
            summary["runs"][run]["layers"][layer] = {}
            for scaling, normalise in (("normalised", True), ("unscaled", False)):
                per_email = per_email_statistics(run, layer, normalise)
                if layer == PRIMARY_LAYER and normalise:
                    primary[run] = per_email
                summary["runs"][run]["layers"][layer][scaling] = {
                    "pairs": describe_pairs(per_email),
                    "per_email": {
                        str(b): {
                            v: {name: round(value, 6) for name, value in stats.items()}
                            for v, stats in by_variant.items()
                        }
                        for b, by_variant in per_email.items()
                    },
                }
        counts = summary["behaviour"][run]["counts"]
        print(f"{run}: obedience " + ", ".join(f"{v} {counts[v]['obedience']}/30" for v in VARIANTS))
    for test in CONFIRMATIONS:
        differences = confirmation_differences(primary, test)
        result = sign_flip_test(differences, test.alternative)
        result.update(
            {
                "statistic": test.statistic,
                "run": test.run,
                "left": test.left,
                "right": test.right,
                "minus_run": test.minus_run,
                "alternative": test.alternative,
                "n_positive": int((differences > 0).sum()),
                "verdict": verdict(result["p_value"]),
            }
        )
        summary["confirmations"][test.name] = result
        print(f"{test.name:38s} mean {result['observed']:+.4f} p={result['p_value']:.3f} {result['verdict']}")
    for run in RUNS:
        summary["readings"][run] = lead_in_reading(
            summary["confirmations"][f"neutral_vs_quoted_{run}"]["p_value"],
            summary["confirmations"][f"injection_vs_neutral_{run}"]["p_value"],
        )
    stage6 = json.loads(STAGE6_SUMMARY.read_text())
    summary["exploratory"] = {
        "note": "Added after the stage 7 results were seen. Not pre-registered. Two-sided.",
        "run_interactions": {
            "fresh_emails": run_interactions(primary),
            "october_emails": run_interactions(
                {
                    run: stage6["runs"][run]["layers"][PRIMARY_LAYER]["normalised"]["per_email"]
                    for run in RUNS
                }
            ),
        },
    }
    for emails, report in summary["exploratory"]["run_interactions"].items():
        for name, result in report.items():
            print(
                f"exploratory {emails:14s} {name:11s} pilot {result['pilot_mean']:+.4f} "
                f"summarise-only {result['summarise_only_mean']:+.4f} p={result['p_value']:.3f}"
            )
    summary["elapsed_seconds"] = round(time.time() - started, 1)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    plot(primary, summary["confirmations"])
    print(json.dumps(summary["readings"], indent=2))
    print(f"wrote {SUMMARY_PATH} and {FIGURE_PATH} in {summary['elapsed_seconds']} s")


if __name__ == "__main__":
    main()
