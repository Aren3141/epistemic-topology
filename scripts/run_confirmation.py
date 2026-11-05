"""Stage 7 forwards: replies and token states for the 30 fresh emails.

For each run in src/topology/stage7.py and each of the 90 fresh emails, one
generation forward (as in stages 1 and 2, cached under results/cache_stage7/)
and one prefill forward that saves the email and sentence token states (as in
stage 6, under results/token_clouds_stage7/). Stops if any protocol check
fails. Existing files are reused.

    PYTHONPATH=. python scripts/run_confirmation.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

from scripts.extract_token_clouds import _forward, _relative_difference
from src.specificity.corpus import attack_sentence
from src.specificity.extract import load_model, run_example
from src.specificity.held_out import VARIANTS, build_held_out_corpus, held_out_email
from src.topology.stage6 import STATE_TOLERANCE
from src.topology.stage7 import RUNS

REPLIES = Path("results/cache_stage7")
STATES = Path("results/token_clouds_stage7")


def main() -> int:
    tokenizer, model = load_model()
    checks = {}
    started = time.time()
    for run_name, run in RUNS.items():
        sentence = attack_sentence(run["canary"])
        corpus = build_held_out_corpus(run["canary"])
        state_dir = STATES / run_name
        state_dir.mkdir(parents=True, exist_ok=True)
        worst_last = 0.0
        for index, example in enumerate(corpus, start=1):
            record = run_example(
                tokenizer,
                model,
                example,
                system_prompt=run["system_prompt"],
                prompt_version=run["prompt_version"],
                cache_dir=REPLIES / run_name,
                canary=run["canary"],
            )
            path = state_dir / f"{example.base_id:02d}_{example.variant}.npz"
            if not path.exists():
                arrays = _forward(
                    tokenizer, model, run["system_prompt"], example.body,
                    held_out_email(example.base_id), sentence,
                )
                np.savez(path, **arrays)
            saved = np.load(path)
            if int(saved["prompt_tokens"]) != record["prompt_tokens"]:
                raise RuntimeError(f"{path}: prompt token count differs from the reply cache")
            for layer in ("middle", "early"):
                worst_last = max(
                    worst_last,
                    _relative_difference(
                        saved[f"last_{layer}"],
                        np.array(record["layers"][layer]["last_document"]),
                    ),
                )
            print(
                f"{run_name} {index:2d}/90 base {example.base_id:02d} {example.variant:9s} "
                f"obedient={record['obedience']} mention={record['contains_canary']}",
                flush=True,
            )
        worst_email = 0.0
        for base_id in range(len(corpus) // len(VARIANTS)):
            files = [np.load(state_dir / f"{base_id:02d}_{variant}.npz") for variant in VARIANTS]
            for other in files[1:]:
                for key in ("email_ids", "sentence_ids"):
                    if not np.array_equal(files[0][key], other[key]):
                        raise RuntimeError(f"base {base_id}: {key} differ between variants")
                for layer in ("middle", "early"):
                    worst_email = max(
                        worst_email,
                        _relative_difference(files[0][f"email_{layer}"], other[f"email_{layer}"]),
                    )
        checks[run_name] = {
            "email_state_difference": worst_email,
            "last_token_difference": worst_last,
        }
        print(f"{run_name}: email states {worst_email:.2e}, last token {worst_last:.2e}")
        if worst_email > STATE_TOLERANCE or worst_last > STATE_TOLERANCE:
            print("a protocol check failed", file=sys.stderr)
            return 1
    checks["elapsed_seconds"] = round(time.time() - started, 1)
    (STATES / "checks.json").write_text(json.dumps(checks, indent=2))
    print(f"done in {checks['elapsed_seconds']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
