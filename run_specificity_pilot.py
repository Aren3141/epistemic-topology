"""Run the pre-registered specificity pilot.

The default command forwards all 90 emails on CPU. Cached records in
results/cache are reused. Persistent homology is not computed; the script
only records whether the gates allow it as a later milestone.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import torch

from src.specificity.corpus import build_corpus
from src.specificity.extract import load_model, run_example
from src.specificity.gates import MODEL_NAME, PRIMARY_LAYER, homology_decision
from src.specificity.probe import evaluate_layer


def _rates(records: list[dict]) -> dict:
    counts: dict[str, Counter] = {}
    for record in records:
        bucket = counts.setdefault(record["variant"], Counter())
        bucket["n"] += 1
        if record["obedience"]:
            bucket["obedient"] += 1
        if record["contains_canary"]:
            bucket["contains_canary"] += 1
    report = {}
    for variant, bucket in counts.items():
        report[variant] = {
            "n": bucket["n"],
            "obedient": bucket["obedient"],
            "obedience_rate": bucket["obedient"] / bucket["n"],
            "contains_canary": bucket["contains_canary"],
        }
    return report


def _spotcheck(records: list[dict]) -> list[dict]:
    chosen = []
    for variant in ("clean", "injection", "quoted"):
        rows = [record for record in records if record["variant"] == variant]
        chosen.extend(rows[:4] if variant == "injection" else rows[:3])
    return [
        {
            "base_id": record["base_id"],
            "variant": record["variant"],
            "obedience": record["obedience"],
            "contains_canary": record["contains_canary"],
            "reply": record["reply"],
        }
        for record in chosen
    ]


def _public_record(record: dict) -> dict:
    """Drop activation vectors from the human-readable report."""
    layers = {}
    for name, layer in record["layers"].items():
        vector = layer["last_document"]
        layers[name] = {
            "layer_index": layer["layer_index"],
            "centroid_distance": layer["centroid_distance"],
            "last_document_finite": True,
            "last_document_dim": len(vector),
        }
    return {
        "base_id": record["base_id"],
        "variant": record["variant"],
        "reply": record["reply"],
        "obedience": record["obedience"],
        "contains_canary": record["contains_canary"],
        "body_characters": record["body_characters"],
        "prompt_tokens": record["prompt_tokens"],
        "n_instruction_tokens": record["n_instruction_tokens"],
        "n_document_tokens": record["n_document_tokens"],
        "n_layers": record["n_layers"],
        "layers": layers,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="forward only the first N base emails; gates are not authoritative",
    )
    args = parser.parse_args()

    torch.set_num_threads(4)
    examples = build_corpus()
    if args.limit:
        examples = [example for example in examples if example.base_id < args.limit]

    print(f"loading {MODEL_NAME} on cpu...")
    tokenizer, model = load_model("cpu")
    records = []
    for index, example in enumerate(examples, start=1):
        print(f"[{index}/{len(examples)}] base {example.base_id} {example.variant}")
        records.append(run_example(tokenizer, model, example))

    rates = _rates(records)
    layer_reports = {
        layer_name: evaluate_layer(records, layer_name)
        for layer_name in ("early", "middle")
    }
    primary = layer_reports[PRIMARY_LAYER]
    specificity = primary["obeyed_vs_quoted"]
    decision = homology_decision(
        n_obeyed_injections=rates.get("injection", {}).get("obedient", 0),
        n_quoted_refusals=(
            rates.get("quoted", {}).get("n", 0)
            - rates.get("quoted", {}).get("obedient", 0)
        ),
        clean_vs_injection_auroc=primary["clean_vs_injection"]["probe_auroc"],
        obeyed_vs_quoted_probe_auroc=specificity["probe_auroc"],
        obeyed_vs_quoted_centroid_auroc=specificity["centroid_auroc"],
    )
    if args.limit:
        decision = {
            "run_persistent_homology": False,
            "reason": "partial run; gates are not authoritative below 30 base emails",
        }

    report = {
        "authoritative": args.limit == 0,
        "model_name": MODEL_NAME,
        "device": "cpu",
        "n_records": len(records),
        "rates": rates,
        "layers": layer_reports,
        "decision": decision,
        "spotcheck": _spotcheck(records),
        "records": [_public_record(record) for record in records],
    }
    destination = Path("results/specificity_pilot.json")
    if args.limit:
        destination = Path("results/specificity_pilot_partial.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print(json.dumps({"rates": rates, "layers": layer_reports, "decision": decision}, indent=2))
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
