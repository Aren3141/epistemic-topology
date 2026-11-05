# ADR 0001: The mention contrast does not amend the homology gate

- Status: accepted
- Date: 2026-11-05

## Context

The October pilot pre-registered `homology_decision` in `src/specificity/gates.py`. Persistent homology starts only when at least 8 injections are exact canary replies, at least 8 quoted replies refuse, the clean-versus-injection probe reaches AUROC 0.70, and both specificity scores fall to 0.65 or below.

Stage 2, summarise-only, produced 3 exact injection replies and 30 quoted refusals. The canary also appears inside 13 of 30 injection summaries and in no quotation. The stage 2 protocol had left the probe unfitted. Fitting it raises a choice: whether “contains the canary” may replace “the whole reply is the canary” as the label that can open homology.

## Decision

Score the two October tasks on the summarise-only cache, and also score `mention_within_injection`: injection rows whose reply contains the canary against injection rows whose reply omits it. Pass only the exact-reply counts and the two October AUROCs into `homology_decision`. The mention AUROC is stored in `data/summarise_only_summary.json` under the layer reports and flagged with `mention_contrast.authorises_homology: false`.

The numeric thresholds in `gates.py` stay as they were on 22 October 2026.

## Consequences

With 3 exact replies the gate returns “contrast insufficient”, and persistent homology stays off. Both middle-layer mention scores are at or below 0.65 (probe 0.58, centroid 0.63). Substituting those scores and the 13-versus-17 counts for the obedience arguments would make `homology_decision` return true. The export script does not do that, and `tests/test_summarise_only.py` locks both the published decision and that counterfactual. Opening homology, or swapping the obedience label, requires a new ADR. The June pull request that adds a homology script for the three-sentence baseline is outside this decision and stays unmerged.
