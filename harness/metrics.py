"""
harness/metrics.py - Evaluation Metrics for Benchmark Arms

Computes:
1. Accuracy with Wilson score confidence interval
2. Brier Score: Calibration metric = mean((conf - hit)^2)
3. AUROC of confidence for predicting hit vs miss
4. Coverage: % of decisions auto-executed by the Wilson gate
5. Auto-Execute Precision: % of auto-executions that were correct
"""

import math
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics import roc_auc_score
from harness.wilson import wilson_lower_bound

def wilson_interval(k: int, n: int, z: float = 1.645) -> Tuple[float, float, float]:
    """Computes (lower, point_est, upper) Wilson interval."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) / n) + (z2 / (4 * n * n)))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(lower, 4), round(p, 4), round(upper, 4)

def compute_arm_metrics(
    hits: List[bool],
    confidences: List[float],
    gates: List[str]
) -> Dict[str, Any]:
    """
    Computes complete benchmark metrics for an arm's shadow mode evaluation.
    """
    n = len(hits)
    if n == 0:
        return {}

    k = sum(hits)
    lower, acc, upper = wilson_interval(k, n, z=1.645)

    y_true = np.array([1.0 if h else 0.0 for h in hits])
    y_conf = np.array(confidences)

    # Brier score (lower is better calibrated)
    brier = float(np.mean((y_conf - y_true) ** 2))

    # AUROC of confidence predicting hit vs miss
    # Requires both hits and misses to compute ROC
    if len(np.unique(y_true)) > 1:
        try:
            auroc = float(roc_auc_score(y_true, y_conf))
        except Exception:
            auroc = 0.50
    else:
        auroc = 1.0 if k == n else 0.0

    # Gate metrics
    auto_indices = [i for i, g in enumerate(gates) if g == "AUTO"]
    coverage = len(auto_indices) / n
    if auto_indices:
        auto_hits = sum(hits[i] for i in auto_indices)
        auto_precision = auto_hits / len(auto_indices)
    else:
        auto_precision = 1.0  # vacuously perfect when 0 auto-executions

    return {
        "n": n,
        "correct": k,
        "accuracy": acc,
        "wilson_lower": lower,
        "wilson_upper": upper,
        "brier_score": round(brier, 4),
        "auroc": round(auroc, 4),
        "coverage": round(coverage, 4),
        "auto_precision": round(auto_precision, 4)
    }
