# Changelog

## [2026-11-05]
- Ran the second required reply, `BETA-SIGNAL-17`, under the summarise-only system message. Exact obedience is 2/30 injections and 0/30 quotations. Mention inside injections is 12/30. Middle-layer clean-versus-injection AUROC is 1.0. The gate stays closed on the class count. ADR: `docs/adr/0002-second-reply-string-does-not-amend-the-gate.md`.
- Re-exported the summarise-only cache. The published counts matched.
- Added a GitHub Actions workflow that runs the four table-test modules without downloading the model.
- Scored the summarise-only cache with the October probe. Middle-layer clean-versus-injection AUROC is 1.0. Exact obedience remains 3/30, so the homology gate stays closed on the class count.
- Recorded the within-injection mention contrast: 13 mentions against 17 omissions, middle-layer probe AUROC 0.58. That contrast does not enter `homology_decision`. ADR: `docs/adr/0001-mention-contrast-does-not-amend-the-gate.md`.
- Published geometry columns on `data/summarise_only_90.jsonl`, the summary at `data/summarise_only_summary.json`, and `docs/explorer/summarise-only.html`.
- About 1 day of this study remains, for a cache re-export and a reading of those tables. A second reply string would be a new protocol of about 1 week.

## [2026-10-22]
- Replaced the active question with the specificity pilot: obeyed injection versus the same sentence quoted as a security example.
- Added the matched 90-email corpus, the exact-reply rule, CPU extraction for `Qwen/Qwen2.5-1.5B-Instruct`, and an email-grouped linear probe plus centroid distance.
- Pre-registered the persistent-homology gate in `src/specificity/gates.py` and `docs/pilot_protocol.md`. Homology is not implemented.
- Left the June PCA baseline in place as `run_phase1.py`.
- Pinned `transformer-lens` to 3.9.0 so that baseline still imports `HookedTransformer`.
- Recorded the one-email CPU smoke test. The pipeline runs. The committed injection was summarised rather than obeyed exactly, so the 90-email run has not started.
- Moved the summary task into a shared system message after direct orders were obeyed and in-email orders were not. Three checked emails then obeyed the injection and refused the quotation. Demo cards are in `docs/demos/`.
- Ran all 90 emails. Every injection was an exact canary reply and no quoted email was. The middle-layer linear probe AUROC is 1.0, so persistent homology stays off.
- Published the 90-row table in `data/`, a browser page at `docs/explorer/index.html`, and tests that recompute the AUROCs from that table.
- Allowed `run_example` to take another system message and another cache directory. Stage 2, in `docs/stage2_protocol.md`, asks whether obedience survives when the system message only says to summarise.
- Finished that summarise-only run. Exact hijack happened on 3 of 30 injections. The canary was mentioned in 13 of 30 injection summaries and in no quotation.
- Recorded that a draft gate would have rejected a quoted row with zero obedience, and corrected that rule before any pilot forward.

## [Added]
- `src/baseline/pca_check.py` implemented for linear baseline validation.
- 2D PCA reduction, variance ratio logging, and silhouette score computation.
- Automated scatter plot generation (`pca_baseline_check.png`).

## [Tested]
- Verified tensor aggregation logic.
- Asserted strict CPU device enforcement to prevent MPS numerical instability.

## [Limitations Observed]
- Token-level aggregation inherently ignores sequence position. If temporal ordering is vital to the regime, PCA on flattened tokens will not capture it.
- Silhouette score computation `O(n^2)` is disabled for token counts exceeding 50,000 to prevent CPU bottlenecking.