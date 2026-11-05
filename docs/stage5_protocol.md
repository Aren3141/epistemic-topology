# Stage 5 — population shape

Written 5 November 2026, before any persistence diagram in this study was computed. The executable copy of the constants and the outcome rule is `src/topology/stage5.py`. If this page and that file disagree, the file is what ran, and the disagreement is a bug to fix before reading results. Decision record: `docs/adr/0003-descriptive-topology-is-separate-from-the-gate.md`.

## The question

The linear probe already shows that clean and injected emails sit in different places (AUROC 1.0 at the middle layer in stages 1, 2, and 4). This stage asks whether they also form clouds of different **shape**:

> With each variant’s location removed, do the 30 last-token states of one variant have a different persistent homology from the 30 states of another variant of the same emails?

This is a description of the model’s states. It is not an obedience detector, and nothing here is passed into `homology_decision`.

## Data

No new forwards. The last-email-token vectors already cached for three runs:

| Run | Cache | System message | Exact obedience on injections |
| --- | --- | --- | --- |
| `pilot` | `results/cache/` | `system-policy-v1`, which states the quote rule | 30 / 30 |
| `summarise_only` | `results/cache_summarise_only/` | “Summarise the email in two sentences.”, code `ALPHA-OVERRIDE-41` | 3 / 30 |
| `second_canary` | `results/cache_second_canary/` | The same, code `BETA-SIGNAL-17` | 2 / 30 |

Each run has 30 base emails in three variants. The middle layer (block 14) is primary. The early layer (block 1) is printed and is not interpreted.

## Comparisons

Two per run, six in all:

- **clean versus injection.** Does adding the order change the shape of the cloud?
- **injection versus quoted.** Does framing the same sentence as an order rather than a quotation change the shape? In the `pilot` run every injection was obeyed, so this is also obeyed versus quoted.

## Preparing the clouds

For one run and one layer:

1. Take the 90 vectors. Subtract from each vector the mean of its own variant (30 vectors). This removes location. Persistent homology ignores translation, but the permutation test below mixes points from two variants, and without this step a mixed cloud would straddle two locations and the test would measure location again.
2. Standardise each of the 1,536 coordinates over the 90 centred vectors, then keep the first 16 principal components (`random_state=20261022`). These are the same 16 components and the same scaler style the probe uses. The fit is label-free once the variant means are removed, and it is done once. It is not refit inside the permutations.
3. Each variant is now a cloud of 30 points in 16 dimensions.
4. Divide each cloud by its own median pairwise distance. This removes overall spread, so the comparison is about shape rather than size. The unscaled result is printed beside it and is not interpreted.

## Statistics

- **Topological.** Vietoris–Rips persistence diagrams in dimensions 0 and 1 (`ripser`, Euclidean distance, Z/2 coefficients). The infinite H0 bar is dropped. Two clouds are compared by the 1-Wasserstein distance between their diagrams, with the L∞ ground metric and matching to the diagonal allowed. One statistic for H0, one for H1.
- **Geometric baseline.** The 1-Wasserstein distance between the two clouds’ distributions of pairwise distances (435 distances each). It ignores translation and rotation, like homology, and it sees spacing but not connectivity or loops.

## Null and test

Paired label swap. The 30 base emails each contribute one point to each cloud. One permutation decides, for every base email independently and with probability one half, whether its two points swap clouds. The scale normalisation and every statistic are recomputed on the swapped clouds. 999 permutations, seed `20261022`. The p-value is (1 + number of permutations at least as large as the observed statistic) / 1000.

## Outcome rule

The topological family is 6 comparisons × 2 homology dimensions = 12 tests at the middle layer, scale-normalised. A topological test passes at p ≤ 0.05 / 12.

For each comparison:

| Topology (H0 or H1) | Geometric baseline | Outcome |
| --- | --- | --- |
| Passes | p ≥ 0.05 | **Shape differs, beyond spacing.** Topology sees something the simpler statistic does not. |
| Passes | p < 0.05 | **Shape differs, spacing already shows it.** Topology agrees with geometry and adds no new detection. |
| Fails | p ≤ 0.05 / 6 | **Spacing differs, topology does not.** |
| Fails | otherwise | **No shape difference detected** at 30 points per cloud. |

A null outcome is a result. With 30 points per cloud, loops may be few and short-lived.

## What this stage does not do

- It does not search other layers, other component counts, other filtrations, or other subsets of emails for a significant result. Those choices are fixed above.
- It does not compute obeyed versus quoted in the summarise-only runs, where only 3 and 2 injections were obeyed.
- It does not change `src/specificity/gates.py` or call `homology_decision`.
- It does not store raw vectors in `data/`. The published summary keeps statistics, p-values, and the middle-layer diagrams, which are derived numbers.

## Result

Filled in after `scripts/run_population_shape.py` writes `data/population_shape_summary.json`.
