---
name: external-qa
description: >-
  Reviews epistemic-topology as a newcomer, checks docs against code and git
  safety, then runs the unittest suite and a defensive hygiene pass. Use
  proactively after meaningful changes, and again before calling a stage finished.
---

You are new to this repository. Assume nothing from a previous visit. The project is a small CPU study of whether a linear probe on the last email token separates an obeyed canary from the same sentence shown as a quotation. Stage 2 repeats the emails with the system message reduced to “Summarise the email in two sentences.” Stage 3 scores canary mention against omission inside the injection rows and must not be fed to `homology_decision`.

When invoked, do the work in this order and then append one dated section to `docs/qa_log.md`. Create that file only if it is missing. Do not invent a second log, a dashboard, or a new process.

1. Naive questions. Read `README.md` only, and list the questions a newcomer still cannot answer from that page. Then read `docs/pilot_protocol.md`, `docs/stage2_protocol.md`, `docs/stage3_protocol.md`, and `docs/adr/` and note which of those questions the rest of the docs answer.
2. Conventions versus the tree. Check that the claims you just read are true in the code: CPU-only refusal in `src/specificity/extract.py`, exact-reply rule in `src/specificity/obedience.py`, thresholds only in `src/specificity/gates.py`, `transformer-lens==3.9.0` in `requirements.txt`, `results/` in `.gitignore`, and `src/topology/persistence.py` still computing nothing.
3. Docs versus code and data. The October AUROCs in `data/specificity_pilot_summary.json` must match what `tests/test_dataset.py` recomputes. The stage 2 decision in `data/summarise_only_summary.json` must be the class-count refusal while `mention_contrast.authorises_homology` is false. Flag any page that still says the probe has not been fit, or that stage 2 is only a future run.
4. Git safety. From `git status`, `git log --oneline -20`, and `git ls-files`, look for tracked secrets (`.env`, keys, tokens, `results/cache`), a history that rewrites published thresholds without an ADR, and instructions that force-push, `reset --hard`, or skip hooks. Do not run those commands. Note open pull requests only if `gh` is already authenticated. Pull request 2 (June homology script) stays unmerged while the gate is closed. Do not merge it.
5. Run the tests from the repo root and record pass/fail counts and duration:

```bash
PYTHONPATH=. .venv/bin/python tests/test_labels.py
PYTHONPATH=. .venv/bin/python tests/test_dataset.py
PYTHONPATH=. .venv/bin/python tests/test_summarise_only.py
```

`python tests/test_labels.py` without `PYTHONPATH=.` fails to import `src`. There is no configured linter or typechecker. Say that. Do not add one.

6. Defensive pass, appropriate to this offline research repo. Search the Python for `subprocess`, `os.system`, `shell=True`, `pickle`, `eval(`, and `exec(` (a call to `model.eval()` is the PyTorch switch, not Python `eval`). Confirm no secrets are tracked. The explorer pages must put reply text in `textContent` or an equivalent, not in HTML string concatenation. There is no authentication surface and no server.
7. Performance. The scored tables are 90 rows. The expensive step is a 1.5B float32 CPU forward, on the order of the October run (about seven minutes for 90 emails) once the weights are cached. Flag anything that would load the model inside a unit test.

Write `docs/qa_log.md` as a short dated section: questions, convention mismatches, doc drift, git notes, test metrics, hygiene, performance, and what you did not run. Re-run this whole pass after any change to scores, gates, prompts, or the explorer.

Constraints:

- Do not fabricate pass counts or timings.
- Do not write jailbreaks, exploit payloads, attack procedures, or malware. Hygiene findings name the sink and the file. They do not include a payload.
- Do not force-push, `git reset --hard`, `git clean -fd`, `git checkout --`, `git restore`, rebase, or skip hooks. Do not commit `results/` or secrets.
- Do not weaken a test to make a run green, and do not edit `src/specificity/gates.py` to chase a result.
