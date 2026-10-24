"""
Prequential Evaluation Loop (Shadow Mode)
Strictly leak-free online test-then-train protocol as specified by hackathon audit criteria.

Protocol:
For each decision t in 1..N (sorted chronologically):
  1. Predict blind using model state_{t-1} -> (pred_t, conf_t)
  2. Retrieve category record (k, n) strictly through t-1
  3. Compute Wilson lower bound: lb = wilson_lower_bound(k, n, z=1.645)
  4. Evaluate Autonomy Gate:
       gate = "AUTO" if (lb >= threshold[stakes] and conf_t >= 0.70) else "ESCALATE"
  5. REVEAL ground-truth label y_t (strictly AFTER gate decision is logged)
  6. Compute hit = (pred_t == y_t)
  7. Update category record: record.k += int(hit), record.n += 1
  8. Log decision row in shadow mode audit trail
  9. If not hit: trigger state_{t} rule update from human_reason
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from harness.wilson import wilson_lower_bound, STAKES_THRESHOLDS

@dataclass
class CategoryRecord:
    k: int = 0  # successes through t-1
    n: int = 0  # trials through t-1

@dataclass
class ShadowLogEntry:
    t: int
    decision_id: str
    category: str
    stakes: str
    prediction: str
    confidence: float
    gate: str              # "AUTO" | "ESCALATE"
    ground_truth: str
    hit: bool
    wilson_lower: float    # lb computed BEFORE revealing label
    requires_tavily: bool
    synthetic: bool

@dataclass
class StreamEvalReport:
    total_decisions: int
    overall_accuracy: float
    coverage: float                   # % of decisions auto-executed
    auto_execute_precision: float     # % of auto-executions that were correct
    escalation_rate: float            # % escalated to human
    category_stats: Dict[str, Dict[str, Any]]
    log: List[ShadowLogEntry] = field(default_factory=list)

# Strict whitelist for blind prediction: any other field (labels, reasons, metadata) is hidden by default
BLIND_FIELDS = frozenset({
    "id",
    "category",
    "stakes",
    "timestamp",
    "inbound_text",
    "options",
    "option_semantics",
    "semantic_mapping",
    "requires_tavily",
    "search_query"
})

def run_prequential_loop(
    decisions: List[Dict[str, Any]],
    predict_fn: Callable[[Dict[str, Any], Any], tuple[str, float]],
    learn_fn: Callable[[Dict[str, Any], Any], Any],
    initial_state: Any
) -> StreamEvalReport:
    """
    Executes the prequential evaluation loop across chronologically sorted decisions.
    Pooled per category across stakes.
    """
    # 1. Sort decisions chronologically with deterministic tie-breaking on id
    sorted_decisions = sorted(decisions, key=lambda d: (d.get("timestamp", ""), d.get("id", "")))
    
    # 2. Initialize category records (strictly tracks evidence through t-1)
    category_records: Dict[str, CategoryRecord] = {}
    current_state = initial_state
    log: List[ShadowLogEntry] = []
    
    auto_count = 0
    auto_correct_count = 0
    total_correct = 0
    
    for t_idx, item in enumerate(sorted_decisions, start=1):
        cat = item["category"]
        stakes = item["stakes"]
        truth = item["ground_truth_choice"]
        
        if cat not in category_records:
            category_records[cat] = CategoryRecord()
            
        record = category_records[cat]
        
        # Safeguard: Strict whitelist projection ensures no labels or answers reach predictor
        blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
        
        # Step 1: Predict blind using state_{t-1}
        pred, conf = predict_fn(blind_item, current_state)
        
        # Step 2 & 3: Compute Wilson lower bound on record THROUGH t-1
        lb = wilson_lower_bound(record.k, record.n, z=1.645)
        
        # Step 4: Evaluate Autonomy Gate BEFORE revealing ground truth
        threshold = STAKES_THRESHOLDS.get(stakes, 0.70)
        is_auto = (lb >= threshold) and (conf >= 0.70)
        gate = "AUTO" if is_auto else "ESCALATE"
        
        # Step 5 & 6: Reveal ground truth label & score hit
        hit = (pred == truth)
        if hit:
            total_correct += 1
            
        if is_auto:
            auto_count += 1
            if hit:
                auto_correct_count += 1
                
        # Step 7: Update category record for step t+1
        record.k += int(hit)
        record.n += 1
        
        # Step 8: Log in shadow mode
        log.append(ShadowLogEntry(
            t=t_idx,
            decision_id=item.get("id", f"dec_{t_idx}"),
            category=cat,
            stakes=stakes,
            prediction=pred,
            confidence=conf,
            gate=gate,
            ground_truth=truth,
            hit=hit,
            wilson_lower=round(lb, 4),
            requires_tavily=item.get("requires_tavily", False),
            synthetic=item.get("synthetic", False)
        ))
        
        # Step 9: Update state if prediction missed
        if not hit and item.get("human_reason"):
            current_state = learn_fn(item, current_state)
            
    total = len(sorted_decisions)
    overall_acc = (total_correct / total) if total > 0 else 0.0
    coverage = (auto_count / total) if total > 0 else 0.0
    auto_prec = (auto_correct_count / auto_count) if auto_count > 0 else 1.0
    escalation = 1.0 - coverage
    
    cat_stats = {}
    for c_name, rec in category_records.items():
        cat_stats[c_name] = {
            "total_items": rec.n,
            "correct_items": rec.k,
            "accuracy": round(rec.k / rec.n, 4) if rec.n > 0 else 0.0,
            "final_wilson_lower": round(wilson_lower_bound(rec.k, rec.n, z=1.645), 4)
        }
        
    return StreamEvalReport(
        total_decisions=total,
        overall_accuracy=round(overall_acc, 4),
        coverage=round(coverage, 4),
        auto_execute_precision=round(auto_prec, 4),
        escalation_rate=round(escalation, 4),
        category_stats=cat_stats,
        log=log
    )
