"""Bayesian Knowledge Tracing (BKT) Algorithm Implementation.

BKT models student knowledge state as a latent binary variable (known / unknown)
and updates mastery belief after every assessment response.
"""

from typing import Tuple


def update_bkt(
    p_know: float,
    is_correct: bool,
    p_learn: float = 0.2,
    p_guess: float = 0.2,
    p_slip: float = 0.1,
) -> float:
    """Computes the updated posterior probability of knowing the concept.

    Args:
        p_know: Prior probability of mastery P(L_t) [0.0 - 1.0].
        is_correct: True if student answered correctly, False otherwise.
        p_learn: Transition probability P(T) of learning after an opportunity.
        p_guess: Probability P(G) of guessing correctly without knowing.
        p_slip: Probability P(S) of making an error despite knowing.

    Returns:
        Updated mastery probability P(L_{t+1}) clamped between [0.01, 0.99].
    """
    # Clamp prior to safe range
    p_l = max(0.001, min(0.999, float(p_know)))

    # Step 1: Compute posterior belief conditioned on the observation
    if is_correct:
        numerator = p_l * (1.0 - p_slip)
        denominator = numerator + ((1.0 - p_l) * p_guess)
    else:
        numerator = p_l * p_slip
        denominator = numerator + ((1.0 - p_l) * (1.0 - p_guess))

    if denominator <= 0.0:
        p_posterior = p_l
    else:
        p_posterior = numerator / denominator

    # Step 2: Account for knowledge acquisition transition
    p_next = p_posterior + ((1.0 - p_posterior) * p_learn)

    # Return clamped within realistic educational bounds
    return round(max(0.01, min(0.99, p_next)), 4)


def evaluate_mastery_level(p_know: float) -> str:
    """Categorizes mastery probability into educational proficiency bands."""
    if p_know >= 0.85:
        return "Mastered"
    elif p_know >= 0.70:
        return "Proficient"
    elif p_know >= 0.45:
        return "Developing"
    else:
        return "Needs Remediation"


def check_level_proposal_triggers(
    p_know: float, consecutive_low: int, consecutive_high: int
) -> Tuple[bool, str]:
    """Evaluates whether an automated proposal should be generated for teacher review."""
    if consecutive_low >= 3 and p_know < 0.40:
        return True, "remediation"
    elif consecutive_high >= 3 and p_know >= 0.85:
        return True, "acceleration"
    return False, ""
