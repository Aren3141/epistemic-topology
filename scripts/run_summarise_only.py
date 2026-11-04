"""Stage 2: the same 90 emails with a system message that only says to summarise.

The pilot cache is not reused. Writes results/cache_summarise_only/ and
results/ablation_summarise_only.json.
"""

import json
from collections import Counter
from pathlib import Path

import torch

from src.specificity.corpus import SUMMARISE_ONLY_PROMPT, SUMMARISE_ONLY_VERSION, build_corpus
from src.specificity.extract import load_model, run_example

CACHE = Path("results/cache_summarise_only")


def main() -> None:
    torch.set_num_threads(4)
    tokenizer, model = load_model("cpu")
    records = []
    examples = build_corpus()
    for index, example in enumerate(examples, start=1):
        print(f"[{index}/{len(examples)}] base {example.base_id} {example.variant}", flush=True)
        record = run_example(
            tokenizer,
            model,
            example,
            system_prompt=SUMMARISE_ONLY_PROMPT,
            prompt_version=SUMMARISE_ONLY_VERSION,
            cache_dir=CACHE,
        )
        records.append(
            {
                "base_id": record["base_id"],
                "variant": record["variant"],
                "reply": record["reply"],
                "obedience": record["obedience"],
                "contains_canary": record["contains_canary"],
            }
        )
    rates: dict[str, Counter] = {}
    for record in records:
        bucket = rates.setdefault(record["variant"], Counter())
        bucket["n"] += 1
        if record["obedience"]:
            bucket["obedient"] += 1
    report = {
        "prompt_version": SUMMARISE_ONLY_VERSION,
        "system_prompt": SUMMARISE_ONLY_PROMPT,
        "n_records": len(records),
        "rates": {
            variant: {
                "n": bucket["n"],
                "obedient": bucket["obedient"],
                "obedience_rate": bucket["obedient"] / bucket["n"],
            }
            for variant, bucket in rates.items()
        },
        "records": records,
    }
    destination = Path("results/ablation_summarise_only.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["rates"], indent=2))
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
