# The answer

Written 5 November 2026, after stage 7. This is the page the goal asked for. It adds no new measurement and no new test. Every number is in a file under `data/`, and the protocol next to it says how that number was allowed to be read.

## The question

Does the shape of this model’s internal states, measured with persistent homology, say anything about obedience to a hidden instruction that simpler measurements of position do not already say?

The model is `Qwen/Qwen2.5-1.5B-Instruct`, float32, on CPU. The emails are short synthetic ones written for this study. Obedience means the whole reply is exactly a made-up code, `ALPHA-OVERRIDE-41` or, in one repeat, `BETA-SIGNAL-17`.

## The answer

**Position already answers the detection question. Shape does not add a detector of obedience.**

A linear readout of one vector, the last token of the message, separates an obeyed order from the same sentence shown as a quotation when the system message states that rule. Persistent homology was therefore not adopted as the detector. The gate that would have adopted it stays closed.

Shape does change. Adding the attack sentence changes the loops in a cloud of 30 emails. Inside one email, the sentence sits slightly closer to the rest of the email when it is an order than when it is a quotation, and that closer-order result holds on 30 fresh emails. Those shape changes are either matched by a simpler geometric measurement, or they track the presence and the framing of the sentence rather than whether the model then obeyed it.

One narrow topological result survived a fresh-email test. The gap in the longest loop, order minus quotation, is larger when the system message only says “summarise” than when it states the quote rule. That is an interaction between system messages. On the fresh emails, the summarise-only loop difference on its own did not clear the threshold. A longer loop is not, by this study’s own rule, a sign that the model refused.

## Detection, which is position

Under the system message that says to follow an explicit reply order and to ignore one that is quoted as something not to follow: 30 of 30 injections replied with only the code, and 0 of 30 quotations did. The middle-layer probe AUROC is 1.0. Source: `data/specificity_pilot_summary.json`, `docs/pilot_protocol.md`.

With that message reduced to “Summarise the email in two sentences.”: 3 of 30 exact replies for `ALPHA-OVERRIDE-41`, and 2 of 30 for `BETA-SIGNAL-17`. The probe still separates a clean email from an injection at AUROC 1.0. The gate closes on the count, because fewer than 8 injections were obeyed. Sources: `data/summarise_only_summary.json`, `data/second_canary_summary.json`.

On 30 fresh emails the same split appears again. With the quote rule, 30 of 30 orders were exact and 0 of 30 training-note quotations were. With only “summarise”, 1 of 30 orders was exact. A neutral quotation, which does not say whether to follow the sentence, was exact on 0 of 30 in both runs. That neutral count was recorded. It was not one of the pre-registered tests. Source: `data/confirmation_summary.json`.

## Shape across emails

Stage 5 built one persistence diagram per set of 30 last-token vectors, after location and scale were removed. Clean emails against emails that contain the attack sentence: the loops (H1) differ at p = 0.001 in all three runs. Order against quotation: no loop difference in any run, including the pilot, where obedience was 30 of 30 against 0 of 30 and the probe separates those rows perfectly. A simpler spacing statistic sees most of the clean-against-injection difference. Source: `data/population_shape_summary.json`, `docs/stage5_protocol.md`.

So at this scale, shape tracks whether the sentence is in the email. It does not track whether the model obeyed it. The probe, which uses position, does track obedience in the pilot.

## Shape inside one email

Stage 6 made each email a cloud of its own word-pieces plus the word-pieces of the attack sentence. In all 30 emails of all three runs, the order sits closer to the rest of the email than the quotation does. The median gap is 4.8, 6.6, and 7.9 percent of that email’s quotation separation. The clusters (H0) also differ, and the plain distance already shows the move, so the pre-registered rule says topology adds nothing beyond geometry. Source: `data/token_shape_summary.json`, `docs/stage6_protocol.md`.

The quotation also puts different words immediately before the sentence. Stage 7 added a neutral quotation of similar length that takes no stance, on 30 emails the earlier analysis had not seen.

On those emails, in both system messages, and in every email:

- the order sits closest to the email,
- the neutral quotation sits in the middle,
- the training-note quotation sits furthest.

Both separation tests are confirmed at p = 0.001. The reading written before the forwards is that both the quoting lead-in and what that lead-in says move the sentence. The stage 6 closer-order result is not only an artefact of the words “must not be followed”, and it is not only an artefact of having any lead-in at all.

The cluster result does not replicate. H0 is confirmed in the fresh pilot (29 of 30, p = 0.001) and not in the fresh summarise-only run (16 of 30, p = 0.372). The rule required both.

The loop interaction is confirmed (25 of 30, p = 0.001). The fresh summarise-only loop comparison alone is not (22 of 30, p = 0.036, and the threshold is 0.005). Source: `data/confirmation_summary.json`, `docs/stage7_protocol.md`.

## What this does not say

- It does not say persistent homology is useless on language-model states. It says that, for obedience on this model and these emails, the shape measurements did not beat a simpler account.
- It does not reopen the October gate. Descriptive diagrams were never an input to `homology_decision`. The gate stays closed.
- It does not claim a security detector. Ninety emails, then thirty more, on one 1.5B model, are a pilot.
- A 3B float32 model was not run. Its weights are about 12 GB, and this machine has 16 GB. A 4-bit copy would change the vectors.

## Where each part lives

| Claim | File |
| --- | --- |
| Probe AUROC 1.0, 30/30 obeyed under the quote rule | `data/specificity_pilot_summary.json` |
| 3/30 and the mention score 0.58 | `data/summarise_only_summary.json` |
| 2/30 for the second code | `data/second_canary_summary.json` |
| Population diagrams and p-values | `data/population_shape_summary.json` |
| Per-email token clouds | `data/token_shape_summary.json` |
| Fresh-email confirmations | `data/confirmation_summary.json` |
| The rule that kept homology out of the detector | `src/specificity/gates.py`, ADR 0003 |
