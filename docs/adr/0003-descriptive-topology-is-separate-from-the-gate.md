# ADR 0003: Descriptive topology runs beside the homology gate, not through it

- Status: accepted
- Date: 2026-11-05

## Context

The project is named for topological data analysis, and its goal is a statement about the shape of the model’s internal states. By 5 November 2026 no persistence diagram had been computed. The reason is the October gate in `src/specificity/gates.py`. It answers one question, whether persistent homology is needed to **detect** an obeyed injection against the same sentence quoted. It said no twice. Under `system-policy-v1` the probe already separated those emails with AUROC 1.0. Under the summarise-only prompts there were only 3 and then 2 obeyed emails, below the minimum of 8.

That gate does not answer a second question. A linear probe and a centroid distance measure where the points sit. Persistent homology of a Vietoris–Rips filtration depends only on pairwise distances, so it ignores translation and rotation. It measures shape. The probe result says injected emails sit elsewhere. It does not say whether their cloud has a different shape.

## Decision

Add descriptive topology stages that ask about shape, and keep them out of the detection gate.

1. Stage 5, population shape, uses the last-token vectors already cached for stages 1, 2, and 4. Each variant of each run is a 30-point cloud. The protocol, statistic, permutation test, and correction are written in `docs/stage5_protocol.md` and committed before the diagrams are computed.
2. Stage 6, token-cloud shape, follows the October protocol’s own description of “what homology would be”: diagrams of the email-token states for each email. It needs one new forward that saves those states, and its own protocol.
3. Neither stage passes anything into `homology_decision`. Neither stage edits the thresholds in `gates.py`. A topological difference found here is reported as a description of shape, not as an obedience detector.
4. Each stage compares its topological statistic with a simpler geometric statistic of the same clouds under the same permutation test. A topological result is called new only when the simpler statistic does not also detect it.
5. Pull request 2, the June homology script for three `gpt2-small` sentences, stays unmerged. It conflicts with main, commits bytecode, and runs on a sample that cannot support a claim. The topology code is written fresh in `src/topology/persistence.py` and `src/evaluation/wasserstein.py`.

## Consequences

`src/topology/persistence.py` and `src/evaluation/wasserstein.py` stop being placeholders. Ripser and persim, already in `requirements.txt`, become runtime dependencies of stage 5. They are not needed by the earlier table tests.

The `docs-keeper` and `external-qa` instructions stop treating “any persistence diagram” as a violation. They now check that no stage 5 or stage 6 result is passed into `homology_decision`.

With 30 points per cloud, loops (H1) may be few and short-lived. A null result is a valid outcome and is reported as such. If stage 5 finds no shape difference beyond the geometric baseline, stage 6 still runs, because it asks about a different cloud.
