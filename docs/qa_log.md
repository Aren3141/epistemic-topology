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
