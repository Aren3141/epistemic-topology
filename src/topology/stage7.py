"""Pre-registered confirmation tests for stage 7, fresh emails and a neutral quotation.

Fixed on 5 November 2026 before any stage 7 forward. The prose copy is
docs/stage7_protocol.md. The per-cloud statistics are the stage 6 ones.
Nothing here feeds homology_decision.
"""

from dataclasses import dataclass

import numpy as np

from src.specificity.corpus import (
    CANARY,
    PROMPT_VERSION,
    SUMMARISE_ONLY_PROMPT,
    SUMMARISE_ONLY_VERSION,
    SYSTEM_PROMPT,
)
from src.topology.stage6 import N_PERMUTATIONS, PERMUTATION_SEED

RUNS = {
    "pilot": {
        "system_prompt": SYSTEM_PROMPT,
        "prompt_version": PROMPT_VERSION + "-held-out",
        "canary": CANARY,
    },
    "summarise_only": {
        "system_prompt": SUMMARISE_ONLY_PROMPT,
        "prompt_version": SUMMARISE_ONLY_VERSION + "-held-out",
        "canary": CANARY,
    },
}
ALPHA = 0.05


@dataclass(frozen=True)
class Confirmation:
    """One pre-registered test on per-email differences.

    The difference for one email is statistic(left) minus statistic(right) in
    `run`. When `minus_run` is set, the same difference in that run is
    subtracted, which tests whether the effect differs between runs.
    """

    name: str
    statistic: str
    run: str
    left: str
    right: str
    alternative: str
    minus_run: str | None = None


CONFIRMATIONS = (
    Confirmation("separation_pilot", "separation", "pilot", "injection", "quoted", "less"),
    Confirmation("separation_summarise_only", "separation", "summarise_only", "injection", "quoted", "less"),
    Confirmation("h0_pilot", "h0_total", "pilot", "injection", "quoted", "greater"),
    Confirmation("h0_summarise_only", "h0_total", "summarise_only", "injection", "quoted", "greater"),
    Confirmation("loop_summarise_only", "h1_max", "summarise_only", "injection", "quoted", "greater"),
    Confirmation(
        "loop_interaction", "h1_max", "summarise_only", "injection", "quoted", "greater",
        minus_run="pilot",
    ),
    Confirmation("neutral_vs_quoted_pilot", "separation", "pilot", "neutral", "quoted", "two-sided"),
    Confirmation(
        "neutral_vs_quoted_summarise_only", "separation", "summarise_only", "neutral", "quoted", "two-sided"
    ),
    Confirmation("injection_vs_neutral_pilot", "separation", "pilot", "injection", "neutral", "two-sided"),
    Confirmation(
        "injection_vs_neutral_summarise_only", "separation", "summarise_only", "injection", "neutral", "two-sided"
    ),
)
THRESHOLD = ALPHA / len(CONFIRMATIONS)

CONFIRMED = "confirmed"
NOT_CONFIRMED = "not confirmed"

STANCE = "the training note's wording moves the sentence"
ADJACENCY = "any quoting lead-in moves the sentence"
BOTH = "both the lead-in and its wording move the sentence"
UNRESOLVED = "neither comparison is significant"


def sign_flip_test(
    differences: np.ndarray,
    alternative: str = "two-sided",
    n_permutations: int = N_PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> dict[str, float]:
    """Paired sign-flip test on the mean difference.

    "less" asks whether the mean is below zero, "greater" whether it is above.
    """
    differences = np.asarray(differences, dtype=np.float64)
    if differences.ndim != 1 or len(differences) == 0:
        raise ValueError("differences are one value per pair")
    observed = float(differences.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(n_permutations, len(differences)))
    null = (signs * differences).mean(axis=1)
    tolerance = 1e-12
    if alternative == "two-sided":
        count = int((np.abs(null) >= abs(observed) - tolerance).sum())
    elif alternative == "less":
        count = int((null <= observed + tolerance).sum())
    elif alternative == "greater":
        count = int((null >= observed - tolerance).sum())
    else:
        raise ValueError(f"unknown alternative: {alternative}")
    return {
        "observed": observed,
        "null_mean": float(null.mean()),
        "p_value": (1 + count) / (1 + n_permutations),
    }


def confirmation_differences(
    per_email: dict[str, dict[int, dict[str, dict[str, float]]]], test: Confirmation
) -> np.ndarray:
    """Per-email differences for one test. per_email[run][base_id][variant][statistic]."""

    def difference(run: str) -> np.ndarray:
        emails = sorted(per_email[run])
        return np.array(
            [
                per_email[run][b][test.left][test.statistic]
                - per_email[run][b][test.right][test.statistic]
                for b in emails
            ]
        )

    values = difference(test.run)
    if test.minus_run is not None:
        values = values - difference(test.minus_run)
    return values


def verdict(p_value: float) -> str:
    return CONFIRMED if p_value <= THRESHOLD else NOT_CONFIRMED


def lead_in_reading(neutral_vs_quoted_p: float, injection_vs_neutral_p: float) -> str:
    """What the two neutral comparisons in one run say about the stage 6 move."""
    stance = neutral_vs_quoted_p <= THRESHOLD
    adjacency = injection_vs_neutral_p <= THRESHOLD
    if stance and adjacency:
        return BOTH
    if stance:
        return STANCE
    if adjacency:
        return ADJACENCY
    return UNRESOLVED
