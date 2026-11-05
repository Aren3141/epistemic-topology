"""Stage 6 prefill: save the token states of each email and its attack sentence.

Prefill only, no generation. For the injection and quoted variants of the 30
base emails in each of the three runs, saves the middle- and early-layer states
of the email tokens and the sentence tokens to results/token_clouds/<run>/.
Stops if any protocol check fails. Existing files are reused.

    PYTHONPATH=. python scripts/extract_token_clouds.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

from src.specificity.corpus import attack_sentence, build_corpus
from src.specificity.extract import load_model
from src.topology.stage6 import RUNS, STATE_TOLERANCE, VARIANTS, token_positions

OUTPUT = Path("results/token_clouds")


def _relative_difference(left: np.ndarray, right: np.ndarray) -> float:
    scale = max(float(np.abs(left).max()), float(np.abs(right).max()))
    return float(np.abs(left - right).max()) / scale


def _forward(tokenizer, model, system_prompt: str, body: str, email: str, sentence: str) -> dict:
    prompt = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": body},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(
        prompt, return_tensors="pt", return_offsets_mapping=True, add_special_tokens=False
    )
    offsets = [(int(start), int(end)) for start, end in encoded["offset_mapping"][0]]
    ids = encoded["input_ids"][0].tolist()

    body_at = prompt.find(body)
    sentence_at = prompt.find(sentence, body_at)
    if body_at < 0 or sentence_at < 0 or not body.startswith(email):
        raise RuntimeError("email or sentence span is missing from the rendered prompt")
    email_positions = token_positions(offsets, body_at, body_at + len(email))
    sentence_positions = token_positions(offsets, sentence_at, sentence_at + len(sentence))
    body_positions = token_positions(offsets, body_at, body_at + len(body))
    if offsets[sentence_positions[0]][0] != sentence_at:
        raise RuntimeError("the sentence does not start on a token boundary")
    if offsets[sentence_positions[-1]][1] != sentence_at + len(sentence):
        raise RuntimeError("the sentence does not end on a token boundary")
    if offsets[email_positions[-1]][1] > body_at + len(email):
        raise RuntimeError("the last email token runs past the email text")

    with torch.inference_mode():
        hidden_states = model(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"],
            output_hidden_states=True,
            use_cache=False,
        ).hidden_states
    n_layers = len(hidden_states) - 1
    layers = {"early": 1, "middle": n_layers // 2}

    arrays = {
        "email_ids": np.array([ids[i] for i in email_positions]),
        "sentence_ids": np.array([ids[i] for i in sentence_positions]),
        "prompt_tokens": np.array(len(ids)),
    }
    for name, index in layers.items():
        states = hidden_states[index][0].to(torch.float32).cpu().numpy()
        if not np.isfinite(states).all():
            raise RuntimeError(f"non-finite state at the {name} layer")
        arrays[f"email_{name}"] = states[email_positions]
        arrays[f"sentence_{name}"] = states[sentence_positions]
        arrays[f"last_{name}"] = states[body_positions[-1]]
    return arrays


def main() -> int:
    tokenizer, model = load_model()
    checks = {}
    started = time.time()
    for run_name, run in RUNS.items():
        directory = OUTPUT / run_name
        directory.mkdir(parents=True, exist_ok=True)
        sentence = attack_sentence(run["canary"])
        corpus = build_corpus(run["canary"])
        clean = {example.base_id: example.body for example in corpus if example.variant == "clean"}
        worst_email, worst_last = 0.0, 0.0
        for example in corpus:
            if example.variant not in VARIANTS:
                continue
            path = directory / f"{example.base_id:02d}_{example.variant}.npz"
            if not path.exists():
                arrays = _forward(
                    tokenizer, model, run["system_prompt"], example.body,
                    clean[example.base_id], sentence,
                )
                np.savez(path, **arrays)
            saved = np.load(path)
            cached = json.loads(
                (Path(run["cache"]) / f"{example.base_id:02d}_{example.variant}.json").read_text()
            )
            if cached["prompt_version"] != run["prompt_version"]:
                raise RuntimeError(f"{path}: cache prompt version differs")
            if int(saved["prompt_tokens"]) != cached["prompt_tokens"]:
                raise RuntimeError(f"{path}: prompt token count differs from the cache")
            for layer in ("middle", "early"):
                difference = _relative_difference(
                    saved[f"last_{layer}"], np.array(cached["layers"][layer]["last_document"])
                )
                worst_last = max(worst_last, difference)
        for base_id in sorted(clean):
            pair = [np.load(directory / f"{base_id:02d}_{variant}.npz") for variant in VARIANTS]
            for key in ("email_ids", "sentence_ids"):
                if not np.array_equal(pair[0][key], pair[1][key]):
                    raise RuntimeError(f"base {base_id}: {key} differ between variants")
            for layer in ("middle", "early"):
                worst_email = max(
                    worst_email,
                    _relative_difference(pair[0][f"email_{layer}"], pair[1][f"email_{layer}"]),
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
    (OUTPUT / "checks.json").write_text(json.dumps(checks, indent=2))
    print(f"done in {checks['elapsed_seconds']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
