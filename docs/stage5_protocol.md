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

Run on 5 November 2026, after this protocol and `src/topology/stage5.py` were pushed (commit `d8557cf`). `scripts/run_population_shape.py` took about 15 seconds on CPU. Summary: `data/population_shape_summary.json`. Figure: `docs/demos/stage5-population-shape/diagrams.png`.

![Stage 5 persistence diagrams](demos/stage5-population-shape/diagrams.png)

Middle layer, scale-normalised, 999 paired permutations. A topology test passes at p ≤ 0.0042. The baseline threshold for “spacing differs” is p ≤ 0.0083.

| Run | Comparison | H0 p | H1 p | Spacing p | Outcome |
| --- | --- | --- | --- | --- | --- |
| pilot | clean vs injection | 0.027 | **0.001** | 0.035 | shape differs, spacing already shows it |
| pilot | injection vs quoted | 0.258 | 0.563 | 0.008 | spacing differs, topology does not |
| summarise-only | clean vs injection | 0.047 | **0.001** | 0.117 | shape differs, beyond spacing |
| summarise-only | injection vs quoted | **0.003** | 0.093 | 0.001 | shape differs, spacing already shows it |
| second canary | clean vs injection | 0.040 | **0.001** | 0.010 | shape differs, spacing already shows it |
| second canary | injection vs quoted | 0.049 | 0.323 | 0.006 | spacing differs, topology does not |

What the clouds look like, in units of each cloud’s median pairwise distance:

| Run | Variant | Median nearest neighbour | H0 total persistence | H1 loops | Longest loop |
| --- | --- | --- | --- | --- | --- |
| pilot | clean | 0.64 | 19.5 | 13 | 0.10 |
| pilot | injection | 0.30 | 10.1 | 4 | 0.14 |
| pilot | quoted | 0.31 | 13.4 | 5 | 0.02 |
| summarise-only | clean | 0.62 | 19.3 | 8 | 0.09 |
| summarise-only | injection | 0.34 | 11.3 | 4 | 0.24 |
| summarise-only | quoted | 0.27 | 9.3 | 4 | 0.10 |
| second canary | clean | 0.61 | 18.8 | 10 | 0.07 |
| second canary | injection | 0.33 | 11.4 | 4 | 0.12 |
| second canary | quoted | 0.23 | 9.5 | 3 | 0.04 |

**Reading.**

1. **The attack sentence changes the shape of the cloud.** With location and size removed, clean emails are spread evenly: each one’s nearest neighbour sits at about 0.6 of the typical distance, which leaves many small, short-lived loops. Once the sentence is appended, nearest neighbours are about half as far away. The cloud is clumpier, most small loops fill in, and the one that survives is larger. The loop statistic detects this at p = 0.001, the smallest value 999 permutations can give, in all three runs.
2. **Mostly, simpler geometry sees it too.** In the pilot and second-canary runs the pairwise-distance statistic also differs at p < 0.05, so topology agrees with geometry there rather than finding something new. In the summarise-only run only topology clears its threshold, and the rule labels that comparison “beyond spacing”. Across the three runs the loop statistic is the strongest and most consistent signal for clean against injection. It is not evidence that topology sees something geometry cannot.
3. **Order against quotation: no loop difference.** H1 p-values are 0.56, 0.09, and 0.32. In the pilot every injection was obeyed and no quotation was, and the linear probe separates them perfectly by position. Shape does not. At the population level, the shape tracks whether the sentence is present, not how it is framed or whether it is obeyed. That matches stage 3, where the state barely predicted whether a reply would mention the code.
4. **One isolated quoted email.** In all three runs the most isolated quoted state is base email 28, the “translation pass” email, which asks the reader to mark sentences that changed meaning. It is the off-scale H0 bar in the figure. This is a description, not a test.

Printed only, not interpreted: the early layer gives H1 p = 0.002 for clean against injection in each run. The unscaled clouds differ on almost every statistic, as expected when size is left in.

**What this means for the goal.** At the level of 30-email clouds, persistent homology adds no information about obedience beyond position. It confirms, with a different instrument, that the attack sentence reshapes the states. Stage 6 asks the same question inside a single email, where the cloud is the email’s own word-pieces.

**Limits.** Thirty points per cloud. The loops are small, at most 0.24 of the median distance, so the test is on whole diagrams rather than on any single loop. One model, one layer that decides, one set of synthetic emails. A difference in shape is a description of the states. It is not a detector, and it does not enter `homology_decision`.
