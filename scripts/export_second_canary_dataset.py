"""Publish the second-canary scores from results/cache_second_canary/.

The vectors stay in that cache, which is not committed. The first run creates
data/second_canary_90.jsonl. A later run refuses to continue if a cached
reply disagrees with that file. This script does not load the model.

The homology decision uses exact obedience to BETA-SIGNAL-17 only. Mention
scores are reported beside it and are not passed into homology_decision.
The October thresholds are not edited here.
"""

import json
from pathlib import Path

from src.specificity.corpus import SECOND_CANARY, SECOND_CANARY_VERSION, build_corpus
from src.specificity.gates import homology_decision
from src.specificity.probe import (
    MENTION_WITHIN_INJECTION,
    PRE_REGISTERED_TASKS,
    evaluate_layer,
    task_probabilities,
)

CACHE_DIR = Path("results/cache_second_canary")
DATA_DIR = Path("data")
PUBLISHED = DATA_DIR / "second_canary_90.jsonl"
SUMMARY_PATH = DATA_DIR / "second_canary_summary.json"
TASKS = PRE_REGISTERED_TASKS + (MENTION_WITHIN_INJECTION,)


def _load_published() -> dict[tuple[int, str], dict]:
    rows = [json.loads(line) for line in PUBLISHED.read_text().splitlines() if line.strip()]
    return {(row["base_id"], row["variant"]): row for row in rows}


def load_cached_records() -> list[dict]:
    published = _load_published() if PUBLISHED.exists() else None
    records = []
    for example in build_corpus(SECOND_CANARY):
        path = CACHE_DIR / f"{example.base_id:02d}_{example.variant}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing cache for {path.name}")
        record = json.loads(path.read_text())
        if record.get("prompt_version") != SECOND_CANARY_VERSION:
            raise RuntimeError(f"{path.name} is not {SECOND_CANARY_VERSION}")
        if record.get("canary") != SECOND_CANARY:
            raise RuntimeError(f"{path.name} was scored against a different reply string")
        if not record.get("complete"):
            raise RuntimeError(f"{path.name} is incomplete")
        key = (example.base_id, example.variant)
        if published is not None:
            if key not in published:
                raise RuntimeError(f"published table has no row for {path.name}")
            previous = published[key]
            for field in ("reply", "obedience", "contains_canary"):
                if record[field] != previous[field]:
                    raise RuntimeError(
                        f"{path.name} {field} does not match the published table"
                    )
        record["sender"] = example.sender
        records.append(record)
    if published is not None and len(records) != len(published):
        raise RuntimeError("published table has rows that are not in the cache")
    return records


def public_row(record: dict, probes: dict[str, list[float | None]]) -> dict:
    row = {
        "base_id": record["base_id"],
        "variant": record["variant"],
        "sender": record["sender"],
        "reply": record["reply"],
        "obedience": record["obedience"],
        "contains_canary": record["contains_canary"],
        "canary": SECOND_CANARY,
        "body_characters": record["body_characters"],
        "prompt_tokens": record["prompt_tokens"],
        "n_instruction_tokens": record["n_instruction_tokens"],
        "n_document_tokens": record["n_document_tokens"],
        "last_document_index": record["last_document_index"],
        "n_layers": record["n_layers"],
        "prompt_version": record["prompt_version"],
        "model_name": record["model_name"],
    }
    index = record["_index"]
    for layer_name in ("early", "middle"):
        layer = record["layers"][layer_name]
        row[f"{layer_name}_layer_index"] = layer["layer_index"]
        row[f"{layer_name}_centroid_distance"] = layer["centroid_distance"]
        for task in TASKS:
            row[f"{layer_name}_probe_{task}"] = probes[f"{layer_name}:{task}"][index]
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
        layer_name: evaluate_layer(records, layer_name, tasks=TASKS)
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
        "prompt_version": SECOND_CANARY_VERSION,
        "canary": SECOND_CANARY,
        "model_name": records[0]["model_name"],
        "device": "cpu",
        "n_records": len(rows),
        "rates": rates,
        "layers": layers,
        "decision": decision,
        "mention_contrast": {
            "authorises_homology": False,
            "reason": (
                "this contrast holds the attack sentence fixed inside injection "
                "rows; it is not the October obedience label and cannot open "
                "the homology gate"
            ),
        },
    }


def main() -> None:
    records = load_cached_records()
    for index, record in enumerate(records):
        record["_index"] = index
    probes = {}
    for layer_name in ("early", "middle"):
        for task in TASKS:
            probes[f"{layer_name}:{task}"] = task_probabilities(records, layer_name, task)
    rows = [public_row(record, probes) for record in records]
    summary = summarise(records, rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED.write_text("".join(json.dumps(row) + "\n" for row in rows))
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    print(
        f"wrote {PUBLISHED.name} and {SUMMARY_PATH.name}; "
        f"homology={summary['decision']['run_persistent_homology']}"
    )
    print(
        json.dumps(
            {
                "rates": summary["rates"],
                "middle": summary["layers"]["middle"],
                "decision": summary["decision"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
