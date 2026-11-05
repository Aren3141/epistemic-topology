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
