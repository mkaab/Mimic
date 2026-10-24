import math

def wilson_lower_bound(k: int, n: int, z: float = 1.645) -> float:
    """
    Computes the lower bound of the Wilson score confidence interval.
    Default z=1.645 corresponds to a 90% one-sided confidence bound (alpha=0.10),
    which is standard for one-sided autonomy-activation gates.

    Args:
        k: Number of correct decisions (successes)
        n: Total number of decisions (trials)
        z: Normal distribution quantile (1.645 for 90% one-sided)

    Returns:
        float: Lower bound between 0.0 and 1.0. Returns 0.0 if n == 0.
    """
    if n == 0:
        return 0.0
    
    p_hat = k / n
    z2 = z * z
    
    # Exact Wilson interval lower bound formula
    numerator = p_hat + (z2 / (2 * n)) - z * math.sqrt((p_hat * (1 - p_hat) / n) + (z2 / (4 * (n * n))))
    denominator = 1 + (z2 / n)
    
    lower = numerator / denominator
    return max(0.0, min(1.0, lower))

# Stakes thresholds (one-sided 90% confidence with z=1.645, pooled per category)
STAKES_THRESHOLDS = {
    "low": 0.65,    # Fires at 6/6 perfect (6/8.706 ≈ 0.689)
    "medium": 0.70, # Fires at 7/7 perfect (7/9.706 ≈ 0.721)
    "high": 0.85    # Fires at 16/16 perfect (16/18.706 ≈ 0.855); policy-bound escalation for small N
}

def evaluate_autonomy_gate(k: int, n: int, stakes: str, item_confidence: float) -> tuple[bool, float]:
    """
    Evaluates whether an inbound decision earns auto-execution.
    Gate rule:
        1. Wilson lower bound >= stakes threshold
        2. Model item confidence >= 0.70 (prevents auto-executing ambiguous items on historical laurels)
    
    Returns:
        (is_auto_executed: bool, wilson_lower: float)
    """
    threshold = STAKES_THRESHOLDS.get(stakes, 0.70)
    lb = wilson_lower_bound(k, n, z=1.645)
    is_auto = (lb >= threshold) and (item_confidence >= 0.70)
    return is_auto, lb
