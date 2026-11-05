# ADR 0002: A second reply string does not amend the homology gate

- Status: accepted
- Date: 2026-11-05

## Context

Stage 2 left exact obedience at 3 of 30 for `ALPHA-OVERRIDE-41` under a system message that only says to summarise. The October gate needs 8 exact injection replies. The open measurement was whether that count is a property of this one string. A 3B float32 rerun was also left as a possible later ceiling. On a 16 GB machine the 3B float32 weights are about 12 GB before activations, and a 4-bit load would change the vectors under study.

## Decision

Run the same 30 emails and the same summarise-only system message with the required reply fixed, before any of those forwards, as `BETA-SIGNAL-17`. Store the run in `results/cache_second_canary/` under prompt version `summarise-only-beta-v1`. Score it with the October probe. Pass only the exact-reply counts and the two October AUROCs into `homology_decision`. Leave the numeric thresholds in `src/specificity/gates.py` as they were on 22 October 2026.

Do not start a 3B model in this stage. Do not merge the June homology pull request while the gate is closed.

## Consequences

The October table and the summarise-only table keep `ALPHA-OVERRIDE-41`. `build_corpus()` with no argument still builds that corpus. Mention-within-injection for the new string is reported and flagged `authorises_homology: false`. Opening homology still requires the existing function to return true on exact replies. A later model-size check needs its own decision, because it is a different vector.
