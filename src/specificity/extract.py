"""CPU prefill of Qwen2.5-1.5B-Instruct.

Activations are taken from the prompt only, at the last document token and as
means of the instruction tokens and the document tokens. Generation is greedy
and is used only to score obedience. It does not enter the feature vectors.
"""

import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.specificity.corpus import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    EmailExample,
)
from src.specificity.gates import MODEL_NAME
from src.specificity.obedience import contains_canary, is_obedient

CACHE_DIR = Path("results/cache")


def _token_positions(offsets: list[tuple[int, int]], start: int, end: int) -> list[int]:
    positions = []
    for index, (token_start, token_end) in enumerate(offsets):
        if token_start == token_end:
            continue
        if token_start >= start and token_start < end:
            positions.append(index)
    return positions


def _mean_rows(hidden: torch.Tensor, positions: list[int]) -> np.ndarray:
    rows = hidden[0, positions, :].detach().to(torch.float32).cpu().numpy()
    return rows.mean(axis=0)


def _cosine_distance(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        raise ValueError("a zero residual mean cannot define a cosine distance")
    return float(1.0 - np.dot(left, right) / (left_norm * right_norm))


def load_model(device: str = "cpu"):
    if device != "cpu":
        raise ValueError("the specificity pilot runs on cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.to(device)
    model.eval()
    if not getattr(tokenizer, "is_fast", False):
        raise RuntimeError("offset mapping requires the fast tokenizer")
    return tokenizer, model


def cache_path(example: EmailExample, cache_dir: Path = CACHE_DIR) -> Path:
    return cache_dir / f"{example.base_id:02d}_{example.variant}.json"


def _vector_ok(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all())


def run_example(
    tokenizer,
    model,
    example: EmailExample,
    system_prompt: str = SYSTEM_PROMPT,
    prompt_version: str = PROMPT_VERSION,
    cache_dir: Path = CACHE_DIR,
) -> dict:
    """Forward one email. Reuse a cached record when the reply and vectors exist."""
    path = cache_path(example, cache_dir)
    if path.exists():
        record = json.loads(path.read_text())
        if record.get("complete") and record.get("prompt_version") == prompt_version:
            return record

    prompt = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": example.body},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        return_offsets_mapping=True,
        add_special_tokens=False,
    )
    offsets = [(int(start), int(end)) for start, end in encoded["offset_mapping"][0]]
    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]

    instruction_at = prompt.find(system_prompt)
    if instruction_at < 0:
        raise RuntimeError("the system prompt is missing from the rendered prompt")
    body_at = prompt.find(example.body)
    if body_at < 0:
        raise RuntimeError("the email body span is missing from the rendered prompt")

    instruction_positions = _token_positions(
        offsets, instruction_at, instruction_at + len(system_prompt)
    )
    document_positions = _token_positions(
        offsets, body_at, body_at + len(example.body)
    )
    if not instruction_positions or not document_positions:
        raise RuntimeError(
            f"empty token span for base {example.base_id} {example.variant}"
        )

    with torch.inference_mode():
        prefill = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
            use_cache=False,
        )
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=64,
            do_sample=False,
        )

    hidden_states = prefill.hidden_states
    n_layers = len(hidden_states) - 1
    early_index = 1
    middle_index = n_layers // 2
    if middle_index < 1 or middle_index > n_layers:
        raise RuntimeError(f"unexpected layer count: {n_layers}")

    reply_ids = generated[0, input_ids.shape[1] :]
    reply = tokenizer.decode(reply_ids, skip_special_tokens=True).strip()
    last_document = document_positions[-1]

    layer_scores = {}
    for name, layer_index in ("early", early_index), ("middle", middle_index):
        hidden = hidden_states[layer_index]
        last_vector = (
            hidden[0, last_document, :].detach().to(torch.float32).cpu().numpy()
        )
        instruction_mean = _mean_rows(hidden, instruction_positions)
        document_mean = _mean_rows(hidden, document_positions)
        if not (
            _vector_ok(last_vector)
            and _vector_ok(instruction_mean)
            and _vector_ok(document_mean)
        ):
            raise RuntimeError(f"non-finite activation at {name} layer {layer_index}")
        layer_scores[name] = {
            "layer_index": layer_index,
            "last_document": last_vector.tolist(),
            "centroid_distance": _cosine_distance(instruction_mean, document_mean),
        }

    record = {
        "complete": True,
        "prompt_version": prompt_version,
        "model_name": MODEL_NAME,
        "base_id": example.base_id,
        "variant": example.variant,
        "sender": example.sender,
        "reply": reply,
        "obedience": is_obedient(reply),
        "contains_canary": contains_canary(reply),
        "body_characters": len(example.body),
        "prompt_tokens": int(input_ids.shape[1]),
        "n_instruction_tokens": len(instruction_positions),
        "n_document_tokens": len(document_positions),
        "last_document_index": last_document,
        "n_layers": n_layers,
        "layers": layer_scores,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    return record
