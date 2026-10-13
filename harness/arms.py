"""
harness/arms.py - Evaluation Arms and Prompt Builders for Mimic Benchmark

Defines the 6 benchmark arms:
1. Always-First Option: Sanity check measuring raw position bias.
2. Prequential Majority Class: Predicts the majority label strictly in that category through t-1.
3. Zero-Shot Nemotron: Predicts blind item with no persona or history.
4. Few-Shot Nemotron: Predicts blind item given all prior items 1..t-1 (including choices and human reasons).
5. Mimic Core: Predicts using frozen persona profile + rules learned only on misses through t-1.
6. Mimic + Tavily: Mimic Core with cached web search lookup for requires_tavily items.

All prompt builders strictly consume blind_item (projected via BLIND_FIELDS) and historical state.
"""

from typing import Dict, Any, List, Tuple
import copy

def build_zero_shot_prompt(blind_item: Dict[str, Any]) -> List[Dict[str, str]]:
    """Builds prompt for Zero-Shot Plain Nemotron. Zero history."""
    system_msg = (
        "You are an AI decision engine assisting a busy software engineer and founder.\n"
        "Your task is to predict the correct action for an inbound work situation.\n"
        "Evaluate the situation carefully and choose the best option (A or B).\n"
        "Respond with ONLY the single letter 'A' or 'B'."
    )
    user_msg = (
        f"Category: {blind_item.get('category', '').upper()}\n"
        f"Stakes: {blind_item.get('stakes', '').upper()}\n\n"
        f"Inbound Context:\n\"{blind_item.get('inbound_text', '')}\"\n\n"
        f"Options:\n"
        f"A) {blind_item.get('options', {}).get('A', '')}\n"
        f"B) {blind_item.get('options', {}).get('B', '')}\n\n"
        f"Which option should be chosen? (A/B):"
    )
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]

def build_few_shot_prompt(blind_item: Dict[str, Any], history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Builds prompt for Few-Shot Nemotron.
    Contains preceding items strictly 1..t-1 with revealed choices and reasons.
    """
    system_msg = (
        "You are an AI decision engine assisting a busy software engineer and founder.\n"
        "You have observed previous decisions and the user's explicit reasoning.\n"
        "Study the historical decisions below, then predict the correct action (A or B) for the new item.\n"
        "Respond with ONLY the single letter 'A' or 'B'."
    )
    history_blocks = []
    for idx, prev in enumerate(history, start=1):
        prev_opts = prev.get("options", {})
        choice = prev.get("ground_truth_choice", "A")
        reason = prev.get("human_reason", "")
        chosen_action = prev_opts.get(choice, "")
        semantic_label = prev.get("semantic_choice", "")
        history_blocks.append(
            f"Example {idx} [{prev.get('category', '').upper()} - {prev.get('stakes', '').upper()}]:\n"
            f"Context: \"{prev.get('inbound_text', '')}\"\n"
            f"Options: A) {prev_opts.get('A', '')} | B) {prev_opts.get('B', '')}\n"
            f"User Action Taken: \"{chosen_action}\" (Semantic: {semantic_label})\n"
            f"User Reason: \"{reason}\""
        )
    
    history_text = "\n\n".join(history_blocks) if history_blocks else "No prior history."
    
    user_msg = (
        f"=== PREVIOUS DECISIONS (t-1 Context) ===\n"
        f"{history_text}\n\n"
        f"=== NEW DECISION TO PREDICT ===\n"
        f"Category: {blind_item.get('category', '').upper()}\n"
        f"Stakes: {blind_item.get('stakes', '').upper()}\n\n"
        f"Inbound Context:\n\"{blind_item.get('inbound_text', '')}\"\n\n"
        f"Options:\n"
        f"A) {blind_item.get('options', {}).get('A', '')}\n"
        f"B) {blind_item.get('options', {}).get('B', '')}\n\n"
        f"Which option should be chosen? (A/B):"
    )
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]

def build_mimic_prompt(
    blind_item: Dict[str, Any],
    profile_summary: str,
    rules: List[str],
    web_context: str = ""
) -> List[Dict[str, str]]:
    """
    Builds prompt for Mimic Core and Mimic + Tavily.
    Uses frozen user profile + rules learned only from prior misses 1..t-1.
    """
    system_msg = (
        "You are Mimic, an earned autonomy personal AI assistant.\n"
        "You represent the user's exact judgment architecture.\n"
        "Follow the user profile and active learned heuristics strictly.\n"
        "Respond with ONLY the single letter 'A' or 'B'."
    )
    rules_text = "\n".join([f"- {r}" for r in rules]) if rules else "No learned rules yet."
    
    user_content = [
        f"=== USER JUDGMENT ARCHITECTURE ===",
        f"Profile: {profile_summary}\n",
        f"Active Learned Heuristics:\n{rules_text}\n"
    ]
    
    if web_context:
        user_content.append(f"=== VERIFIED WEB RESEARCH (Tavily) ===\n{web_context}\n")
        
    user_content.append(
        f"=== NEW DECISION ===\n"
        f"Category: {blind_item.get('category', '').upper()}\n"
        f"Stakes: {blind_item.get('stakes', '').upper()}\n\n"
        f"Inbound Context:\n\"{blind_item.get('inbound_text', '')}\"\n\n"
        f"Options:\n"
        f"A) {blind_item.get('options', {}).get('A', '')}\n"
        f"B) {blind_item.get('options', {}).get('B', '')}\n\n"
        f"Which option represents the user's judgment? (A/B):"
    )
    
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "\n".join(user_content)}
    ]

# Learner functions
def learn_few_shot(revealed_item: Dict[str, Any], current_state: Any) -> Any:
    """Appends revealed item to Few-Shot history buffer."""
    new_state = copy.deepcopy(current_state) if isinstance(current_state, list) else []
    new_state.append(revealed_item)
    return new_state

def learn_mimic(revealed_item: Dict[str, Any], current_state: Any) -> Any:
    """
    Updates Mimic state on a miss:
    Appends the human_reason as an active rule for that category.
    """
    new_state = copy.deepcopy(current_state)
    reason = revealed_item.get("human_reason", "").strip()
    cat = revealed_item.get("category", "")
    if reason:
        rule_entry = f"[{cat.upper()}] {reason}"
        if rule_entry not in new_state.setdefault("rules", []):
            new_state["rules"].append(rule_entry)
    return new_state

def predict_prequential_majority(blind_item: Dict[str, Any], state: Any) -> Tuple[str, float]:
    """
    Prequential majority baseline using semantic action frequency within category.
    Counts accumulated strictly through t-1.
    Compares option A's semantic action count vs option B's semantic action count.
    Falls back to 'A' (with conf=0.50) if tied or unseen.
    """
    cat = blind_item.get("category", "")
    cat_counts = state.get("category_counts", {}).get(cat, {}) if isinstance(state, dict) else {}
    
    mapping = blind_item.get("semantic_mapping", {})
    action_a = mapping.get("A", "")
    action_b = mapping.get("B", "")
    
    count_a = cat_counts.get(action_a, 0)
    count_b = cat_counts.get(action_b, 0)
    
    total = count_a + count_b
    if total == 0 or count_a == count_b:
        return "A", 0.50
    elif count_a > count_b:
        conf = round(count_a / total, 2)
        return "A", conf
    else:
        conf = round(count_b / total, 2)
        return "B", conf

def learn_prequential_majority(revealed_item: Dict[str, Any], state: Any) -> Any:
    """Updates category semantic counts when label is revealed at t."""
    new_state = copy.deepcopy(state) if isinstance(state, dict) else {}
    cat = revealed_item.get("category", "")
    sem_choice = revealed_item.get("semantic_choice")
    if not sem_choice:
        choice = revealed_item.get("ground_truth_choice", "")
        sem_choice = revealed_item.get("semantic_mapping", {}).get(choice, "")
    
    if sem_choice:
        counts = new_state.setdefault("category_counts", {}).setdefault(cat, {})
        counts[sem_choice] = counts.get(sem_choice, 0) + 1
    return new_state
