# QA log

Short notes from a newcomer pass. Append a dated section. Do not start a second log.

## 2026-11-05

**Questions a newcomer still has after the README.** What the canary string is, comes from the later sections. Why persistent homology is installed (`ripser`, `persim`) while the modules are empty, is answered by the gate. The remaining day versus the unapproved one-week experiment is stated in the status. Pull request 2 is not named in the README. It is named in the 5 November research-log entry.

**Conventions.** `src/specificity/extract.py` refuses a device other than CPU. Obedience is an exact string match in `src/specificity/obedience.py`. Thresholds live in `src/specificity/gates.py` and were not edited. `requirements.txt` pins `transformer-lens==3.9.0`. `results/` is gitignored. `src/topology/persistence.py` and `src/evaluation/wasserstein.py` still only reserve the later milestone.

**Docs versus the tables.** `data/summarise_only_summary.json` has `run_persistent_homology: false` with the class-count reason, and `mention_contrast.authorises_homology: false`. The tests recompute the AUROCs from the jsonl. The October page links to `summarise-only.html`.

**Git.** No `.env`, key, token, or `results/cache` file is tracked. This pass did not rewrite history. Pull request 2 (June homology script, `feature/phase-2-tda`) was still open. It stays unmerged while the gate is closed. Pull request 4 (`feature/summarise-only-result`) was the parent of this work and was still open.

**Tests.** From the repo root, Python 3.13 in `.venv`:

| Module | Result | Unittest time | Wall clock, including import |
| --- | --- | --- | --- |
| `tests/test_labels.py` | 9 passed, 0 failed | 0.000s | 1.342s |
| `tests/test_dataset.py` | 10 passed, 0 failed | 0.014s | 0.875s |
| `tests/test_summarise_only.py` | 8 passed, 0 failed | 0.010s | 0.858s |

Total 27 passed, 0 failed. There is no configured linter or typechecker, so none was run. `python tests/test_labels.py` without `PYTHONPATH=.` fails with `ModuleNotFoundError: No module named 'src'`. The README now gives the working command.

**Hygiene.** No `subprocess`, `os.system`, `shell=True`, `pickle`, or Python `eval` / `exec` in the Python sources. `model.eval()` is the PyTorch switch. The stage 2 page puts reply text in `textContent`. The October page still builds the card chrome with `innerHTML` and then sets the reply with `textContent`. The fields that pass through `innerHTML` are the project’s own sender, variant, and base id. No server and no authentication surface.

**Browser.** `docs/explorer/summarise-only.html` was opened at `http://127.0.0.1:8765/`. The mention filter showed 13 cards. The injection filter showed 30 cards, of which 3 carried the exact-reply badge and 10 carried the mention badge. At a 390px width the stats grid is one column (`grid-template-columns: 350px`). The click from that page back to the October page was not completed in the browser. The link is present in `docs/explorer/index.html`.

**Performance.** Scoring the 90 cached vectors took about two seconds. A fresh 90-email forward is the expensive step, on the order of the October run (about seven minutes on CPU once the weights are cached). The unit tests do not load the model.

**Not run.** No new model forward. No homology. No second canary. Pull request 2 was not merged and was not closed.

## 2026-11-05 — second-canary pass

Reviewed `feature/second-canary` at `5f53be5`, one docs commit after `b3b0c52`. The working tree was clean. This pass did not edit source, gates, protocols, or the canary string, and did not commit, push, or rewrite history.

**Questions a newcomer still has after the README.** The page gives the counts, the closed gate, and the three explorer pages. It does not give the full gate numbers (0.70, 0.65, 0.80, and the band between them), the verbatim attack sentence, the layer indexes, the probe recipe, the stage 2 email ids, the centroid AUROCs, or the file that holds the `BETA-SIGNAL-17` rows. The sentence about “the same rows” names `data/specificity_pilot_90.jsonl` and `data/summarise_only_90.jsonl` only.

**What the other docs answer.** `docs/pilot_protocol.md` states the gate numbers, the attack sentence, blocks 1 and `n_layers // 2`, the five-fold grouped probe with 16 components, greedy decoding, and 64 new tokens. `docs/stage2_protocol.md` records 3 of 30 exact replies, on emails 10, 20, and 27, and the scores fit on 5 November. `docs/stage3_protocol.md` and ADR 0001 keep the mention contrast out of `homology_decision`. `docs/stage4_protocol.md` and ADR 0002 name `BETA-SIGNAL-17`, `results/cache_second_canary/`, `data/second_canary_90.jsonl`, exact obedience 2 of 30 on emails 10 and 23, mention AUROC 0.60, and the class-count refusal. `data/README.md`, which the README links, lists the columns and that second table.

**Still open after those pages.** The verbatim October system prompt and the verbatim security-training prefix are in `src/specificity/corpus.py`. The protocols paraphrase them. The protocols do not say that the 30 emails are synthetic templates. The fold seed `20261022` is only in `src/specificity/gates.py`. How the email span is recovered inside the chat template is only in `src/specificity/extract.py`.

**Conventions.** `src/specificity/extract.py` refuses a device other than CPU. Obedience is `reply.strip()` equal to the required string in `src/specificity/obedience.py`. The numeric thresholds are defined only in `src/specificity/gates.py`, introduced in `26ce897` and not rewritten later. `requirements.txt` pins `transformer-lens==3.9.0`. `.gitignore` ignores `results/`. `src/topology/persistence.py` and `src/evaluation/wasserstein.py` still compute nothing. `.github/workflows/tests.yml` exists. It installs NumPy and scikit-learn only. There is no configured linter or typechecker. None was added.

**Docs versus the tables.** The October middle-layer figures in `data/specificity_pilot_summary.json` are probe AUROC 1.0 on both tasks, centroid 0.0 for clean versus injection, and centroid 0.8244 for obeyed versus quoted. `tests/test_dataset.py` recomputes those AUROCs from `data/specificity_pilot_90.jsonl` and passed. With 30 of 30 exact injections, that decision is the 0.80 probe refusal. `data/summarise_only_summary.json` and `data/second_canary_summary.json` both set `run_persistent_homology` to false with the class-count reason, and both set `mention_contrast.authorises_homology` to false. The second-canary rates are 2 exact injections and 12 mentions. No page now says the probe is unfitted, or that stage 2 is only a future run. The research-log “Open gap” paragraph still contains the earlier “not started” wording. The next sentence, added in `5f53be5`, says that proposal was run later the same day.

**Mismatch.** `tests/test_second_canary.py` defines nine tests and has no `unittest.main()` guard. The command in the README and in `.github/workflows/tests.yml` exits 0 and runs none of them. The same command does run the other three modules. Loading the file with `python -m unittest` runs the nine tests, and they pass. The gate file and the canary string were not changed.

**Git.** No `.env`, key, token, or `results/cache` path is tracked. Nothing in the repository instructs a force-push, `reset --hard`, or skipping hooks. `gh` is not authenticated, because the keyring token is invalid, so live pull-request state was not listed. The log shows merges of pull requests 1, 3, and 6. No merge of pull request 2 is in that history. It was not merged here.

**Tests.** From the repo root, Python 3.13.14 in `.venv`. Wall clock is `time -p` real time.

| Module | Invocation | Result | Unittest time | Wall clock |
| --- | --- | --- | --- | --- |
| `tests/test_labels.py` | `PYTHONPATH=. .venv/bin/python tests/test_labels.py` | 9 passed, 0 failed | 0.000s | 1.01s |
| `tests/test_dataset.py` | the same form | 10 passed, 0 failed | 0.008s | 0.85s |
| `tests/test_summarise_only.py` | the same form | 8 passed, 0 failed | 0.010s | 0.85s |
| `tests/test_second_canary.py` | the same form | no tests executed, exit 0 | none | 0.87s |
| `tests.test_second_canary` | `PYTHONPATH=. .venv/bin/python -m unittest tests.test_second_canary` | 9 passed, 0 failed | 0.005s | 0.85s |

The three script runs that execute tests are 27 passed and 0 failed. The nine second-canary assertions pass only through the unittest loader. `.venv/bin/python tests/test_labels.py` without `PYTHONPATH=.` exits 1 with `ModuleNotFoundError: No module named 'src'`.

**Hygiene.** No `subprocess`, `os.system`, `shell=True`, `pickle`, or Python `eval` / `exec` in the Python sources. `model.eval()` in `src/specificity/extract.py` and `scripts/obedience_prototype.py` is the PyTorch switch. In `docs/explorer/second-canary.html` the reply is assigned with `reply.textContent`. That page does not build the reply through `innerHTML`. The October page still builds the card chrome with `innerHTML` and then sets the reply with `textContent`. There is no server and no authentication surface.

**Performance.** The scored tables are 90 rows. The unit tests read those tables. They do not import the extractor or call `from_pretrained`. A fresh 90-email forward is the expensive step: about seven minutes in the October log, and about eight minutes for the second reply string, once the 1.5B float32 weights are cached.

**Not run.** No model forward. No homology. No linter. The second-canary page was read as a file, not in a browser. Pull request 2 was not merged. Git history was not rewritten.

## 2026-11-05 — second-canary command

The direct command `PYTHONPATH=. python tests/test_second_canary.py` did not run the nine tests, because the file had no `unittest.main()` guard. That guard is now the same as the other three modules. The README command and the GitHub Actions workflow both call the file that way.

## 2026-11-05 — stage 5 pass

Reviewed `feature/population-shape` at `56e728b` (pull request 9, stacked on pull request 8, `docs/project-overview`). The working tree was clean at the start. This pass edited only this file. It did not switch branches, commit, push, or rewrite history.

**Newcomer read of `README.md` and `docs/overview.md`.** Each of the four questions can be answered in one sentence from those two pages:

- What it is: topological data analysis of the internal states of `Qwen/Qwen2.5-1.5B-Instruct`, applied to whether a hidden email instruction is treated as an order or as a quotation.
- The goal: find out whether persistent homology says anything about obedience that a linear probe and a centroid distance do not already say, written up with every number traceable to `data/`.
- Where it is: stages 1 to 5 are done, and stage 5 produced the first persistence diagrams. The attack sentence changes the loops of the email cloud, but order against quotation does not. Stage 6 is next.
- Time remaining: about 1.5 weeks, to around 16 November 2026.

Why this is a topology project, and why topology arrived only at stage 5, is clear from `README.md` line 26 and the overview section "Why the project measured location first".

**Still confusing, contradictory, or jargon-heavy on those two pages.**

1. `README.md:36` says "the loop-counting stage stays off", and `README.md:65` says "persistent homology does not start". Both sit below a stage 5 row that reports persistence diagrams. Line 26 resolves this (the gate concerns homology as a detector), but a reader meets the contradiction first.
2. "Gate closed" (`docs/overview.md:45`, `:46`, `:48`) and "the October gate closes" (`README.md:181`) are never defined. A newcomer could read "closed" as "passed". The glossary defines "Gate" but not closed or open.
3. "Exact hijack" (`README.md:36`) is used once and is not defined. Elsewhere the term is "obedience".
4. The centroid distance is "instruction tokens" against "email tokens" in `README.md:55`, and "the average system-message state" in `docs/overview.md:77`. `docs/pilot_protocol.md:41` shows that these are the same span. The README alone does not.
5. In `docs/overview.md:70`, "the middle layer is the one that decides" means the pre-registered primary layer. "Decides" is ambiguous.
6. Both stage 5 rows say there is no loop difference for order against quotation. That is true for H1. They do not say that the pre-registered rule labels summarise-only injection against quoted as "shape differs, spacing already shows it", through H0 at p = 0.003. That label is in `docs/stage5_protocol.md` and `data/population_shape_summary.json`.
7. "Spacing statistics" (`docs/overview.md:49`) are not explained on either page.
8. Re-running stage 5 needs all three caches. Neither page says how `results/cache_summarise_only/` is produced. `scripts/run_summarise_only.py` exists, but no page in `docs/`, `README.md`, or `docs/overview.md` names it.
9. Stage 7 will "answer the goal", but neither page says what stage 6 result would count as "shape adds something beyond position". Stage 6 has no protocol yet, so this is expected.

**What the rest of the docs answer.** Item 1 is answered by ADR 0003. Item 2 is answered in substance by the gate section of `docs/pilot_protocol.md`, which defines when homology "is the next milestone". Item 4 is answered by `docs/pilot_protocol.md:41`, item 5 by `docs/pilot_protocol.md:66`, item 6 by the `docs/stage5_protocol.md` table and `docs/research_log.md:169`, and item 7 by `docs/stage5_protocol.md:43`. Item 8 is not answered anywhere in the docs. Item 9 is open.

**Stage tables.** The `README.md` and `docs/overview.md` stage tables agree on every count and score: 30/30 and AUROC 1.0; 3/30 and 1.0; 0.58; 2/30 on `BETA-SIGNAL-17`; H1 p = 0.001 in all three runs; stage 6 next; stage 7 planned. The overview row adds that spacing also sees most of the stage 5 result. The README row does not.

**`docs/stage5_protocol.md` against `data/population_shape_summary.json`.** All 18 middle-layer p-values match to 3 decimals. All six outcomes match `outcomes` and follow from `shape_outcome`. The thresholds 0.0042 and 0.0083, base email 28 as the most isolated quoted state in all three runs, early-layer H1 p = 0.002, and the longest loop of 0.24 all match. Two cloud descriptors are rounded wrongly:

- `docs/stage5_protocol.md:93`, pilot clean, H0 total persistence: the table says 19.6. The JSON value is 19.54997, which rounds to 19.5.
- `docs/stage5_protocol.md:101`, second canary quoted, longest loop: the table says 0.05. The JSON value is 0.044755, which rounds to 0.04.

No outcome depends on either value.

**Pre-registration order.** `d8557cf` (21:15:50, protocol and `src/topology/stage5.py`) comes before `b510ccd` (21:20:58), which adds `data/population_shape_summary.json` and the figure. The local reflog for `origin/feature/population-shape` records a push of `d8557cf` at 21:15:52. The in-between commit `add7483` changed `src/topology/stage5.py` only by adding imports and the `compare_clouds` helper. The constants and the outcome rule are identical between `d8557cf` and `b510ccd`. `docs/stage5_protocol.md` changed after the run only by gaining the "Result" section in `56e728b`.

**Conventions.** `src/specificity/extract.py:51` refuses a device other than CPU. `src/specificity/obedience.py` compares `reply.strip()` with the canary. No gate threshold appears outside `src/specificity/gates.py`, which has one commit (`26ce897`). `git diff main -- src/specificity/gates.py` is empty, and local `main` equals `origin/main` (`5973f9c`). The stage 5 alpha and Bonferroni thresholds live in `src/topology/stage5.py`, and they are stage 5's own. `requirements.txt` pins `transformer-lens==3.9.0`. `.gitignore` ignores `results/`. `homology_decision` is called only by `run_specificity_pilot.py`, `scripts/export_pilot_dataset.py`, `scripts/export_summarise_only_dataset.py`, `scripts/export_second_canary_dataset.py`, and the tests. None of those imports `src.topology`. `scripts/run_population_shape.py` neither imports nor calls it and writes `passes_into_homology_decision: false`. `tests/test_population_shape.py` checks only that one script, and only bare-name calls. `src/topology/persistence.py` enforces 150 points and 32 dimensions, and stage 5 clouds are 30 by 16.

**Doc drift.**

- `docs/pilot_protocol.md:82` still says "No diagram is computed while this protocol's gate is closed." The gate is still closed and stage 5 computed diagrams. ADR 0003 supersedes the sentence, but the page does not point to ADR 0003.
- `docs/explorer/index.html:42`, generated from `scripts/build_explorer.py:60`, still says "So that maths has not been run."
- `CHANGELOG.md:6` says the overview gives "about 2 weeks remaining". The overview now says 1.5 weeks. `docs/research_log.md:161` keeps the 2-week figure and points to the next entry, so it is not drift.
- No page says the probe is unfitted, or that stage 2 is only a future run.

**Git.** No `.env`, key, token, `results/` path, or bytecode is among the 70 tracked files. Nothing in the repository instructs a force-push, `reset --hard`, `clean -fd`, or `--no-verify`. `gh` is authenticated as `Aren3141`. The open pull requests are 9 (base `docs/project-overview`), 8 (base `main`), and 2 (June `feature/phase-2-tda`, base `main`). Pull request 2 was not merged.

**Tests.** From the repo root, Python 3.13.14 in `.venv`, each run as `MPLCONFIGDIR=/tmp/mpl PYTHONPATH=. .venv/bin/python tests/<file>`. Wall clock is `time -p` real time.

| Module | Result | Unittest time | Wall clock |
| --- | --- | --- | --- |
| `tests/test_dataset.py` | 10 passed, 0 failed | 0.017s | 1.40s |
| `tests/test_labels.py` | 9 passed, 0 failed | 0.000s | 0.97s |
| `tests/test_population_shape.py` | 7 passed, 0 failed | 0.002s | 0.97s |
| `tests/test_second_canary.py` | 9 passed, 0 failed | 0.006s | 0.91s |
| `tests/test_summarise_only.py` | 8 passed, 0 failed | 0.010s | 0.92s |
| `tests/test_topology.py` | 16 passed, 0 failed | 0.491s | 1.49s |

Total 59 passed, 0 failed. Every module reported "Ran N tests" with N above 0. The six files match the six commands in `.github/workflows/tests.yml`. Without `PYTHONPATH=.`, `tests/test_labels.py` fails with `ModuleNotFoundError: No module named 'src'`. There is no configured linter or typechecker, so none was run.

**Stage 5 script.** `MPLCONFIGDIR=/tmp/mpl PYTHONPATH=. .venv/bin/python scripts/run_population_shape.py` took 15.51 s real time, and the script reported 14.0 s. It regenerated identical outcomes. Afterwards `git status` and `git diff --stat` showed one modified file, `data/population_shape_summary.json`, with one line changed: `elapsed_seconds` went from 14.7 to 14.0. `docs/demos/stage5-population-shape/diagrams.png` was byte-identical. This pass restored nothing, and that one-line change was left in the working tree.

**Hygiene.** There is no `subprocess`, `os.system`, `shell=True`, `pickle`, or Python `eval` / `exec` in the Python sources. `model.eval()` in `src/specificity/extract.py:60` and `scripts/obedience_prototype.py:115` is the PyTorch switch. `docs/explorer/summarise-only.html` and `docs/explorer/second-canary.html` set reply text with `textContent`. `docs/explorer/index.html:61` still builds the card chrome with an `innerHTML` template, which interpolates the project's own base id, sender, variant, and scores. It then sets the reply with `textContent` at line 68. There is no server and no authentication surface.

**Performance.** Stage 5 reads 270 cached vectors and runs 999 paired permutations for 6 comparisons, 2 layers, and 2 scalings in about 15 seconds. No test imports the extractor, `torch`, or `transformers`, and none calls `from_pretrained`. The expensive step is still a fresh 90-email 1.5B float32 CPU forward, about seven to eight minutes, and stage 6 needs one.

**Not run.** No model forward. No linter or typechecker. The explorer pages were read as files, not opened in a browser. `scripts/build_explorer.py` was not re-run. Pull requests 2, 8, and 9 were not merged or modified. The `elapsed_seconds` change was not reverted or committed.

## 2026-11-05 — stage 6 pass (pull request 10, `feature/token-shape` at `7056e58`)

Midway through this pass the working tree moved to `feature/confirmation` (`7056e58` plus `904482e`, stage 7 pre-registration). The pull request 10 files were read before that move, or compared with `git diff feature/token-shape feature/confirmation`, which touches only `README.md` and the workflow. The tests below were re-run on a `git archive feature/token-shape` export in a temporary directory.

**Questions a newcomer still has after `README.md` and `docs/overview.md`.**

1. "Typical distance" (`docs/overview.md:46`, `README.md:205`) is not defined. In stage 5 it meant the median pairwise distance. Here it does not (see doc drift).
2. "Prefill forwards" (`docs/overview.md:66`, `README.md:100`) is not defined.
3. "Longest loop" (`docs/overview.md:48`) is not defined. The protocol calls it "H1 longest loop", the most persistent H1 bar.
4. The glossary's "Last email token" (`docs/overview.md:80`) is the last token of the whole user message, attack sentence included. Stage 6's "email tokens" exclude the sentence. The two uses of "email" collide.
5. Neither page says what stage 7 counts as confirmed, or what the write-up says if it fails. ADR 0004 (Consequences) and `docs/stage7_protocol.md` do.
6. The glossary's "Permutation test" says "shuffle the labels". Stage 6 flips the sign of paired differences. That is close enough, but it is not said.

The project, the goal, where it stands (stages 1 to 6 done, 7 next), and the time remaining (about 1 week, to around 12 November 2026) can each be said in one sentence from those two pages.

**Pre-registration order.** Commits are `6095554` (protocol, `src/topology/stage6.py`, tests) → `3fe4ba2` (scripts) → `0d2aa7b` (summary, figures, summary tests) → `7056e58` (status pages, ADR 0004). The local reflog for `origin/feature/token-shape` records pushes at 21:34:23, 21:37:56, and 21:41:09. `git diff 6095554 HEAD -- docs/stage6_protocol.md` only adds `## Result`. `src/topology/stage6.py` and `src/specificity/gates.py` are unchanged since `6095554` and against `main`. File times in `results/token_clouds/` show the extraction ran from 21:35:08 to 21:37:05. That is after the protocol push, but before the scripts commit, using the uncommitted script, last modified at 21:34:55 and unchanged since. `data/token_shape_summary.json` was last written at 21:37:58, after the scripts push. File times cannot rule out an earlier, overwritten analysis run.

**Docs versus data.** All 15 middle-layer, normalised rows of the Result table (medians, order-larger counts, p-values) match `data/token_shape_summary.json`. All three outcomes are "shape differs, geometry already shows it" and follow from `token_outcome`. The checks are 0.0 in every run. The extraction took 118.3 s, the analysis 1.3 s, and the clouds have 48 to 66 email tokens plus 15 or 16 sentence tokens. Separation is smaller for the order in 30 of 30 emails in every run, with no ties. Recomputing each sign-flip test from `per_email` reproduces 59 of 60 p-values. The exception is early, summarise-only, H1 total: 0.037 against the published 0.036. That comes from the six-decimal rounding of `per_email`, and that layer is not interpreted.

**Doc drift and claims.**

- "5 to 8 percent of the typical distance" (`docs/stage6_protocol.md:128`, `docs/overview.md:46`, `README.md:205`) is wrong as worded. The per-email gap is 4.8, 6.6, and 7.9 percent of the quotation's separation. As a share of the cloud's median pairwise distance, which is 1 after normalisation, it is 2.8, 3.9, and 4.6 percent.
- `docs/stage6_protocol.md:129` explains the larger H0 for the order as "a sentence that sits slightly apart from the rest". Reading 1 says the order sits closer. Without normalisation, summarise-only H0 does not differ (p = 0.50, printed only).
- "The only place in stages 5 and 6 where topology behaves differently from geometry across conditions" (`docs/stage6_protocol.md:130`, `docs/adr/0004-confirm-stage-6-on-fresh-emails.md:11`, `docs/overview.md:48`, also `docs/stage7_protocol.md:11` on the next branch) is not supported by the table. Attachment, a geometric statistic, is larger for the order in the pilot (22 of 30, p = 0.001), and smaller in summarise-only (10 of 30, p = 0.038) and second canary (13 of 30, p = 0.099).
- H1 total differs in opposite directions in the two runs that share the summarise-only system message: summarise-only 6 of 30 order larger (p = 0.003), second canary 23 of 30 (p = 0.005). No page mentions it.
- "Topology adds nothing beyond geometry" (`docs/stage6_protocol.md:129`, ADR 0004 line 10) is stronger than the rule. The label means the run's geometry p was below 0.05. It does not test whether the topological difference is explained by the geometric one.
- "Where the model did not obey" (`README.md:21`, `docs/overview.md:60`, `CHANGELOG.md:4`) is also "where the system message lacks the quote rule". Those runs had 3 and 2 obeyed injections, not 0.
- The adjacency caveat is stated (`docs/stage6_protocol.md:131`, `README.md:205`, ADR 0004). It does not mention that the training note also puts the quoted sentence more tokens away from the email.
- `docs/stage6_protocol.md:40` says "last-email-token". The code compares the last token of the whole body (`scripts/extract_token_clouds.py:81`), which is what the cache stores as `last_document`. The code is right; the wording is loose.
- `docs/stage6_protocol.md:100` gives the threshold as "p ≤ 0.0056". The rule is p ≤ 0.05/9 = 0.00556.
- Stage tables in `README.md` and `docs/overview.md` agree (6 done, 7 next, 8 planned). The timeframe of about 1 week, to around 12 November 2026, is the same in README, overview, research log, CHANGELOG, and ADR 0004. "1.5 weeks" and "Stage 6 … is next" remain only in dated earlier entries (`CHANGELOG.md:8`, `docs/research_log.md:173`).

**Code versus protocol.** These match `docs/stage6_protocol.md`: token spans found by character offset, with boundary and id checks; pooled scaler and PCA fit on the injection's email tokens plus all 60 sentence spans; 16 components (`PCA_COMPONENTS`, read from `gates.py`); per-cloud median-distance normalisation; ripser H0 and H1 with the infinite bar dropped; separation and attachment as defined; a two-sided sign flip with p = (1 + count)/1000; thresholds 0.05/9 and 0.05/6; and the four-row outcome rule. Clouds are at most 82 points by 16 dimensions. One gap: the boundary checks run only when an `.npz` is freshly written, not on reuse. This run wrote all of them fresh.

**Git.** The working tree was clean at the start. No `.env`, key, token, `results/` path, or `.npz` is tracked. The two new figures are 104 KB and 233 KB. `.gitignore` ignores `results/`, and `requirements.txt` pins `transformer-lens==3.9.0`. Neither `scripts/run_token_shape.py` nor `scripts/extract_token_clouds.py` imports or calls `homology_decision`, and the summary sets `passes_into_homology_decision: false`. `gh auth status` failed (keyring login invalid), so open pull requests were not listed. Pull request 2 was not touched.

**Tests.** Run on the `feature/token-shape` export, with `PYTHONPATH=. <repo>/.venv/bin/python tests/<file>`. Wall time is from a shell timer.

| Module | Result | Unittest time | Wall clock |
| --- | --- | --- | --- |
| `tests/test_dataset.py` | 10 passed | 0.017s | 2.6s |
| `tests/test_labels.py` | 9 passed | 0.000s | 2.0s |
| `tests/test_population_shape.py` | 7 passed | 0.004s | 2.8s |
| `tests/test_second_canary.py` | 9 passed | 0.011s | 1.9s |
| `tests/test_summarise_only.py` | 8 passed | 0.014s | 1.9s |
| `tests/test_token_shape.py` | 20 passed | 0.025s | 2.0s |
| `tests/test_topology.py` | 16 passed | 18.110s | 20.1s |

Total 79 passed, 0 failed. Every module reported "Ran N tests" with N above 0. The seven files match the seven commands in `.github/workflows/tests.yml` on that branch. On `feature/confirmation`, `tests/test_confirmation.py` also ran 9 tests and passed. Without `PYTHONPATH=.`, `tests/test_labels.py` fails with `ModuleNotFoundError: No module named 'src'`. There is no configured linter or typechecker, so none was run. `tests/test_topology.py` took 14 to 18 s, against 0.49 s in the stage 5 pass. Pull request 10 does not change it or the persistence code, and the sandbox did not allow `ps`. CPU contention from parallel stage 7 work is likely but unconfirmed.

**Hygiene.** No `subprocess`, `os.system`, `shell=True`, `pickle`, `allow_pickle`, or Python `eval`/`exec` in the Python sources. The explorer is unchanged by this pull request. It still builds card chrome with `innerHTML` and sets the reply with `textContent` (`scripts/build_explorer.py:79`, `:86`). There is no server and no authentication surface.

**Performance.** No test imports `torch`, `transformers`, or the extractor. `tests/test_token_shape.py` only parses the two scripts with `ast`. The stage 6 analysis took 1.3 s (`elapsed_seconds`), and the extraction 118.3 s (`results/token_clouds/checks.json`).

**Not run.** No model forward. `scripts/extract_token_clouds.py` and `scripts/run_token_shape.py` were not run, because the second would rewrite the summary and figures; numbers were recomputed read-only. No linter or typechecker. Figures were not inspected visually. No git command that changes state.
