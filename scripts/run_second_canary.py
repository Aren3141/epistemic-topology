"""Second fixed reply string, under the summarise-only system message.

Same 30 emails, same “Summarise the email in two sentences.”, a different
required reply. The October cache and the summarise-only cache are not
reused. Writes results/cache_second_canary/ and
results/ablation_second_canary.json. Probe scores are fit afterwards by
scripts/export_second_canary_dataset.py. This script does not decide the
homology gate.
"""

import json
from collections import Counter
from pathlib import Path

import torch

from src.specificity.corpus import (
    SECOND_CANARY,
    SECOND_CANARY_VERSION,
    SUMMARISE_ONLY_PROMPT,
    build_corpus,
)
from src.specificity.extract import load_model, run_example

CACHE = Path("results/cache_second_canary")


def main() -> None:
    torch.set_num_threads(4)
    tokenizer, model = load_model("cpu")
    records = []
    examples = build_corpus(SECOND_CANARY)
    for index, example in enumerate(examples, start=1):
        print(f"[{index}/{len(examples)}] base {example.base_id} {example.variant}", flush=True)
        record = run_example(
            tokenizer,
            model,
            example,
            system_prompt=SUMMARISE_ONLY_PROMPT,
            prompt_version=SECOND_CANARY_VERSION,
            cache_dir=CACHE,
            canary=SECOND_CANARY,
        )
        records.append(
            {
                "base_id": record["base_id"],
                "variant": record["variant"],
                "reply": record["reply"],
                "obedience": record["obedience"],
                "contains_canary": record["contains_canary"],
                "canary": record["canary"],
            }
        )
    rates: dict[str, Counter] = {}
    for record in records:
        bucket = rates.setdefault(record["variant"], Counter())
        bucket["n"] += 1
        if record["obedience"]:
            bucket["obedient"] += 1
        if record["contains_canary"]:
            bucket["mentioned"] += 1
    report = {
        "prompt_version": SECOND_CANARY_VERSION,
        "system_prompt": SUMMARISE_ONLY_PROMPT,
        "canary": SECOND_CANARY,
        "n_records": len(records),
        "rates": {
            variant: {
                "n": bucket["n"],
                "obedient": bucket["obedient"],
                "mentioned": bucket["mentioned"],
                "obedience_rate": bucket["obedient"] / bucket["n"],
            }
            for variant, bucket in rates.items()
        },
        "records": records,
    }
    destination = Path("results/ablation_second_canary.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["rates"], indent=2))
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
