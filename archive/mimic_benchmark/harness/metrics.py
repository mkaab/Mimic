"""
harness/metrics.py - Evaluation Metrics for Benchmark Arms

Statistical Rigor:
1. Headline Accuracy: Reported with two-sided 95% Wilson confidence interval (z=1.96).
2. Gate Confidence: Reported with one-sided 90% Wilson lower bound (z=1.645).
3. AUROC: Computed using average ranks for ties. Returns None if single class.
   Includes 1000-sample bootstrap 95% confidence interval.
4. Brier Score: Calibration metric = mean((conf - hit)^2).
5. Gate Coverage & Auto-Execute Precision.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics import roc_auc_score

def compute_wilson_interval(k: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    """Computes (lower, point_est, upper) Wilson score interval for given z."""
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

def bootstrap_auroc_ci(
    y_true: np.ndarray,
    y_conf: np.ndarray,
    n_bootstraps: int = 1000,
    seed: int = 42
) -> Tuple[Optional[float], Optional[float]]:
    """Computes 95% percentile bootstrap confidence interval for AUROC."""
    if len(np.unique(y_true)) < 2:
        return None, None

    rng = np.random.RandomState(seed)
    n = len(y_true)
    bootstrapped_scores = []

    for _ in range(n_bootstraps):
        indices = rng.randint(0, n, n)
        b_y = y_true[indices]
        b_conf = y_conf[indices]
        if len(np.unique(b_y)) < 2:
            continue
        try:
            score = roc_auc_score(b_y, b_conf)
            bootstrapped_scores.append(score)
        except Exception:
            continue

    if len(bootstrapped_scores) < 100:
        return None, None

    low_ci = np.percentile(bootstrapped_scores, 2.5)
    high_ci = np.percentile(bootstrapped_scores, 97.5)
    return round(float(low_ci), 4), round(float(high_ci), 4)

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
    # Headline accuracy: two-sided 95% Wilson interval (z=1.96)
    acc_lower_95, acc_point, acc_upper_95 = compute_wilson_interval(k, n, z=1.96)

    # Gate thresholding: one-sided 90% Wilson lower bound (z=1.645)
    gate_lower_90, _, _ = compute_wilson_interval(k, n, z=1.645)

    y_true = np.array([1.0 if h else 0.0 for h in hits])
    y_conf = np.array(confidences)

    # Brier score (lower is better calibrated)
    brier = float(np.mean((y_conf - y_true) ** 2))

    # AUROC of confidence predicting hit vs miss (undefined if all hits or all misses)
    if len(np.unique(y_true)) > 1:
        try:
            auroc = round(float(roc_auc_score(y_true, y_conf)), 4)
            auroc_ci_low, auroc_ci_high = bootstrap_auroc_ci(y_true, y_conf, n_bootstraps=1000)
        except Exception:
            auroc = None
            auroc_ci_low, auroc_ci_high = None, None
    else:
        auroc = None
        auroc_ci_low, auroc_ci_high = None, None

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
        "accuracy": acc_point,
        "accuracy_95_ci": (acc_lower_95, acc_upper_95),
        "gate_wilson_lower_90": gate_lower_90,
        "brier_score": round(brier, 4),
        "auroc": auroc,
        "auroc_95_ci": (auroc_ci_low, auroc_ci_high) if auroc is not None else None,
        "coverage": round(coverage, 4),
        "auto_precision": round(auto_precision, 4)
    }
