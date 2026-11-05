# Stage 3 — mention versus omission, inside the injections

Decided 5 November 2026, from the counts already published on 4 November, and scored the same day from the existing cache.

## Why this is the next measurement

Stage 2 left exact obedience at 3 of 30 injections. The October gate needs 8, so that contrast cannot decide anything further. The canary still appears in 13 injection replies and in no quotation. Those 13 and the 17 injections that omit it all contain the same attack sentence. The measurement that still has both classes above 8 is whether the last email token separates those two injection rows.

Comparing a mentioning injection with a quoted email would mostly restate “the attack sentence is present”, which clean versus injection already measures. Stage 3 keeps the sentence fixed and changes only the label.

## What is unchanged

| Choice | Stage 3 | Why |
| --- | --- | --- |
| Emails, model, cache | The stage 2 cache | No new forwards. |
| Probe | The October email-grouped probe, 16 components, five folds | Same instrument. |
| Positive | Injection whose reply contains `ALPHA-OVERRIDE-41` | Includes the 3 exact replies, because they contain the code. |
| Negative | Injection whose reply omits the code | The attack sentence is still in the email. |
| Quoted and clean rows | Left out of this contrast | They answer different questions. |
| Homology | Stays on `homology_decision` and the exact-reply counts | This AUROC is not passed in. See `docs/adr/0001-mention-contrast-does-not-amend-the-gate.md`. |

## Result

Middle layer: probe AUROC 0.58, centroid AUROC 0.63, 13 positives and 17 negatives, all 30 rows scored.

Early layer, printed only: probe AUROC 0.28, centroid AUROC 0.48.

The vector that separates clean emails from injections at AUROC 1.0 scores mention against omission at 0.58. The centroid on that split is 0.63. Both are at or below the October line of 0.65. Substituting them for the obedience scores would make the gate start homology. The published decision leaves them out, so homology stays off. Ten of the thirteen mentions are summaries that repeat the code as part of the email’s request. Three replies are the code alone.

## What remains

About 1 day of this study remains: re-run `scripts/export_summarise_only_dataset.py` against the local cache and read these tables. No further forwards are scheduled.

The study still measures one canary on one model. A proposed next experiment, not started, would repeat this summarise-only setup with a different fixed reply string, chosen and written into the protocol before the forwards. It would measure the exact-reply count, the clean-versus-injection AUROC, and this mention AUROC. The October gate would stay the gate. If that experiment is approved it is about 1 week, and it is not part of the remaining day.
