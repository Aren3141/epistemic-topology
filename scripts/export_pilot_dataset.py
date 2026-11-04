"""Publish the 90-email pilot as a table, without the raw activation vectors.

The vectors stay in results/cache/, which is not committed. This script reads
that cache, recomputes the email-grouped probe scores, and writes data/.
"""

import json
from pathlib import Path

import numpy as np

from src.specificity.corpus import PROMPT_VERSION, build_corpus
from src.specificity.extract import CACHE_DIR
from src.specificity.gates import homology_decision
from src.specificity.probe import aligned_oof_probabilities, evaluate_layer, task_label

DATA_DIR = Path("data")


def load_cached_records() -> list[dict]:
    records = []
    for example in build_corpus():
        path = CACHE_DIR / f"{example.base_id:02d}_{example.variant}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing cache for {path.name}")
        record = json.loads(path.read_text())
        if record.get("prompt_version") != PROMPT_VERSION:
            raise RuntimeError(f"{path.name} is not {PROMPT_VERSION}")
        record["sender"] = example.sender
        records.append(record)
    return records


def _task_probability(records: list[dict], layer_name: str, task: str) -> list[float | None]:
    features = []
    labels = []
    groups = []
    indexes = []
    for index, record in enumerate(records):
        label = task_label(record, task)
        if label is None:
            continue
        features.append(record["layers"][layer_name]["last_document"])
        labels.append(label)
        groups.append(record["base_id"])
        indexes.append(index)
    scores = [None] * len(records)
    if not indexes:
        return scores
    aligned = aligned_oof_probabilities(
        np.array(features, dtype=np.float64),
        np.array(labels, dtype=np.int64),
        np.array(groups, dtype=np.int64),
    )
    for local, index in enumerate(indexes):
        value = float(aligned[local])
        scores[index] = None if not np.isfinite(value) else value
    return scores


def public_row(record: dict, probes: dict[str, list[float | None]]) -> dict:
    row = {
        "base_id": record["base_id"],
        "variant": record["variant"],
        "sender": record["sender"],
        "reply": record["reply"],
        "obedience": record["obedience"],
        "contains_canary": record["contains_canary"],
        "body_characters": record["body_characters"],
        "prompt_tokens": record["prompt_tokens"],
        "n_instruction_tokens": record["n_instruction_tokens"],
        "n_document_tokens": record["n_document_tokens"],
        "last_document_index": record["last_document_index"],
        "n_layers": record["n_layers"],
        "prompt_version": record["prompt_version"],
        "model_name": record["model_name"],
    }
    for layer_name in ("early", "middle"):
        layer = record["layers"][layer_name]
        row[f"{layer_name}_layer_index"] = layer["layer_index"]
        row[f"{layer_name}_centroid_distance"] = layer["centroid_distance"]
        row[f"{layer_name}_probe_clean_vs_injection"] = probes[f"{layer_name}:clean_vs_injection"][
            record["_index"]
        ]
        row[f"{layer_name}_probe_obeyed_vs_quoted"] = probes[f"{layer_name}:obeyed_vs_quoted"][
            record["_index"]
        ]
    return row


def summarise(records: list[dict], rows: list[dict]) -> dict:
    rates = {}
    for variant in ("clean", "injection", "quoted"):
        subset = [row for row in rows if row["variant"] == variant]
        obedient = sum(row["obedience"] for row in subset)
        mentioned = sum(row["contains_canary"] for row in subset)
        rates[variant] = {
            "n": len(subset),
            "obedient": obedient,
            "obedience_rate": obedient / len(subset),
            "contains_canary": mentioned,
        }
    layers = {
        layer_name: evaluate_layer(records, layer_name)
        for layer_name in ("early", "middle")
    }
    primary = layers["middle"]
    decision = homology_decision(
        n_obeyed_injections=rates["injection"]["obedient"],
        n_quoted_refusals=rates["quoted"]["n"] - rates["quoted"]["obedient"],
        clean_vs_injection_auroc=primary["clean_vs_injection"]["probe_auroc"],
        obeyed_vs_quoted_probe_auroc=primary["obeyed_vs_quoted"]["probe_auroc"],
        obeyed_vs_quoted_centroid_auroc=primary["obeyed_vs_quoted"]["centroid_auroc"],
    )
    return {
        "prompt_version": PROMPT_VERSION,
        "model_name": records[0]["model_name"],
        "device": "cpu",
        "n_records": len(rows),
        "rates": rates,
        "layers": layers,
        "decision": decision,
    }


def main() -> None:
    records = load_cached_records()
    for index, record in enumerate(records):
        record["_index"] = index
    probes = {}
    for layer_name in ("early", "middle"):
        for task in ("clean_vs_injection", "obeyed_vs_quoted"):
            probes[f"{layer_name}:{task}"] = _task_probability(records, layer_name, task)
    rows = [public_row(record, probes) for record in records]
    summary = summarise(records, rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    jsonl = DATA_DIR / "specificity_pilot_90.jsonl"
    jsonl.write_text("".join(json.dumps(row) + "\n" for row in rows))
    (DATA_DIR / "specificity_pilot_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {jsonl} and summary; homology={summary['decision']['run_persistent_homology']}")


if __name__ == "__main__":
    main()
