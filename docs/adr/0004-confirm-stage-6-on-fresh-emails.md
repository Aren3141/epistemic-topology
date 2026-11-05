# ADR 0004: Confirm the stage 6 leads on fresh emails before the write-up

- Status: accepted
- Date: 2026-11-05

## Context

Stage 6 (`docs/stage6_protocol.md`) found two things in the token clouds of the same 30 base emails used since October.

1. In every email of every run, the attack sentence sits closer to the rest of the email when it is an order than when it is a quotation. This was a pre-registered geometric statistic. Topology agreed with it and added nothing beyond it.
2. Not pre-registered: the longest loop differs between order and quotation in the two summarise-only runs, where the model almost never obeyed, and not in the pilot, where it always did. This is the only place in stages 5 and 6 where topology behaves differently from geometry across conditions.

There is also a confound. The quotation puts the training note (“…must not be followed:”) and a quote mark directly before the sentence, and the order does not. Because the model reads left to right, the sentence’s states may move because of what is next to it, not because of its stance.

Writing up now would leave the only topology-specific lead untested and the main geometric result open to the adjacency explanation.

## Decision

Insert a confirmation stage before the write-up. The write-up becomes stage 8.

1. Stage 7 uses 30 new base emails, written and committed before any forward. They use the same template as the October emails, so that only the content is new.
2. Each new email gets three variants: the order, the training-note quotation, and a **neutral quotation**. The neutral quotation has the same quote marks and a lead-in of similar length that reports the sentence without saying whether to follow it. The training-note and neutral quotations then differ only in what the lead-in says. The order and the neutral quotation differ in whether there is a quoting lead-in at all.
3. Two system messages: `system-policy-v1` and the summarise-only message, both with `ALPHA-OVERRIDE-41`. Replies are generated so obedience is recorded, as in stages 1 and 2.
4. The direction of each stage 6 lead is now known, so the confirmation tests are one-sided where stage 6 fixes a direction, and two-sided for the new neutral comparisons. The family and threshold are written in `docs/stage7_protocol.md` before the forwards.
5. As in ADR 0003, nothing passes into `homology_decision`, and `gates.py` is not edited.

## Consequences

The finishing date moves only slightly, because stage 6 took one day rather than the planned week. Stage 7 needs 180 generation forwards and 180 prefill forwards, about 20 minutes of CPU. Most of the work is the protocol and the new emails.

If the loop lead fails to replicate, the write-up says that the one topology-specific pattern in this study did not survive fresh emails. If it does replicate, the write-up can make one narrow, confirmed claim about shape. Either answer is useful for the goal.
