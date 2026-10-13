"""
harness/ensemble.py - Arm 8: Independent Perspective Ensemble

Budget Parity: exactly 7 independent calls per decision (Nemotron 120B, T=0.8).
Each member j receives:
1. Seeded 60% random subset of active rules (seed = hash(item_id, j))
2. Top 3 nearest past decisions by TF-IDF cosine on history 1..t-1 (with 1 randomly dropped)
3. Candidate options presented in seeded random order
4. Zero inter-member communication or message passing

Outputs:
- Majority vote decision (mapped back to semantic action)
- Confidence = majority vote share
- Diversity diagnostics: mean pairwise agreement and vote entropy
"""

import math
import random
import hashlib
from collections import Counter
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def derive_member_seed(item_id: str, member_idx: int) -> int:
    """Deterministic integer seed for member j on decision item."""
    token = f"{item_id}_member_{member_idx}"
    h = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(h, 16) % 1_000_000

def retrieve_nearest_examples(
    blind_item: Dict[str, Any],
    history: List[Dict[str, Any]],
    k: int = 3,
    drop_one: bool = True,
    rng: random.Random = None
) -> List[Dict[str, Any]]:
    """Retrieves top k nearest historical examples by TF-IDF cosine similarity, optionally dropping 1."""
    if not history:
        return []
    
    if len(history) <= k:
        selected = list(history)
    else:
        corpus = [h.get("inbound_text", "") for h in history]
        vectorizer = TfidfVectorizer(max_features=300, ngram_range=(1, 2))
        X_hist = vectorizer.fit_transform(corpus)
        X_query = vectorizer.transform([blind_item.get("inbound_text", "")])
        sims = cosine_similarity(X_query, X_hist)[0]
        top_indices = sims.argsort()[::-1][:k]
        selected = [history[i] for i in top_indices]

    if drop_one and len(selected) >= 2 and rng:
        drop_idx = rng.randint(0, len(selected) - 1)
        selected.pop(drop_idx)

    return selected

def build_member_prompt(
    blind_item: Dict[str, Any],
    profile_summary: str,
    rules: List[str],
    history: List[Dict[str, Any]],
    member_idx: int,
    rule_subset_frac: float = 0.6,
    k_nearest: int = 3,
    drop_one: bool = True
) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """
    Builds the prompt for perspective ensemble member j.
    Returns: (messages, member_option_to_semantic_map)
    """
    seed = derive_member_seed(blind_item.get("id", "item"), member_idx)
    rng = random.Random(seed)

    # 1. 60% rule subset
    if rules:
        n_rules = max(1, math.ceil(len(rules) * rule_subset_frac))
        member_rules = rng.sample(rules, min(n_rules, len(rules)))
    else:
        member_rules = []

    # 2. Nearest past examples with 1 dropped
    member_examples = retrieve_nearest_examples(
        blind_item=blind_item,
        history=history,
        k=k_nearest,
        drop_one=drop_one,
        rng=rng
    )

    # 3. Seeded option shuffle
    raw_options = blind_item.get("options", {})
    raw_mapping = blind_item.get("semantic_mapping", {}) # {"A": "accept", "B": "decline"}
    
    items_list = [("A", raw_options.get("A", ""), raw_mapping.get("A", "")),
                  ("B", raw_options.get("B", ""), raw_mapping.get("B", ""))]
    
    if rng.random() > 0.5:
        items_list = [items_list[1], items_list[0]]

    member_options = {
        "A": items_list[0][1],
        "B": items_list[1][1]
    }
    member_to_sem = {
        "A": items_list[0][2],
        "B": items_list[1][2]
    }

    # Format prompt messages
    rules_block = "\n".join([f"- {r}" for r in member_rules]) if member_rules else "No heuristics active."
    
    example_blocks = []
    for ex_idx, ex in enumerate(member_examples, start=1):
        action_text = ex.get("options", {}).get(ex.get("ground_truth_choice", "A"), "")
        sem = ex.get("semantic_choice", "")
        example_blocks.append(
            f"Reference {ex_idx} [{ex.get('category', '').upper()}]:\n"
            f"Context: \"{ex.get('inbound_text', '')}\"\n"
            f"Action Taken: \"{action_text}\" ({sem})\n"
            f"Reason: \"{ex.get('human_reason', '')}\""
        )
    ex_text = "\n\n".join(example_blocks) if example_blocks else "No reference cases."

    system_msg = (
        "You are an expert delegation assistant on an autonomous decision committee.\n"
        "Evaluate the inbound situation based on the user profile, active heuristics, and precedent.\n"
        "Respond with ONLY the single letter 'A' or 'B'."
    )

    user_msg = (
        f"=== USER PROFILE ===\n{profile_summary}\n\n"
        f"=== RELEVANT HEURISTICS ===\n{rules_block}\n\n"
        f"=== PRECEDENT CASES ===\n{ex_text}\n\n"
        f"=== NEW INBOUND SITUATION ===\n"
        f"Category: {blind_item.get('category', '').upper()} | Stakes: {blind_item.get('stakes', '').upper()}\n"
        f"Context: \"{blind_item.get('inbound_text', '')}\"\n\n"
        f"Options:\n"
        f"A) {member_options['A']}\n"
        f"B) {member_options['B']}\n\n"
        f"Decision (A/B):"
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]
    return messages, member_to_sem

def aggregate_ensemble_votes(
    member_picks: List[str],
    member_maps: List[Dict[str, str]],
    blind_item: Dict[str, Any]
) -> Tuple[str, float, float, float]:
    """
    Aggregates member picks into majority decision.
    
    Returns:
    - predicted_letter: 'A' or 'B' (relative to blind_item original options)
    - confidence: majority vote share (e.g. 5/7 = 0.7143)
    - mean_pairwise_agreement: average agreement across all member pairs
    - vote_entropy: Shannon entropy of the vote distribution
    """
    semantic_votes = []
    for pick, m_map in zip(member_picks, member_maps):
        sem_action = m_map.get(pick, "")
        if sem_action:
            semantic_votes.append(sem_action)

    if not semantic_votes:
        return "A", 0.50, 1.0, 0.0

    k = len(semantic_votes)
    counts = Counter(semantic_votes)
    best_sem, best_count = counts.most_common(1)[0]
    conf = best_count / k

    # Reverse map best_sem to original item's A/B
    raw_mapping = blind_item.get("semantic_mapping", {})
    reverse_raw = {v: k for k, v in raw_mapping.items()}
    pred_letter = reverse_raw.get(best_sem, "A")

    # Pairwise agreement
    pairs = 0
    agreements = 0
    for i in range(k):
        for j in range(i + 1, k):
            pairs += 1
            if semantic_votes[i] == semantic_votes[j]:
                agreements += 1
    mean_agreement = (agreements / pairs) if pairs > 0 else 1.0

    # Vote entropy
    entropy = 0.0
    for c in counts.values():
        p = c / k
        if p > 0:
            entropy -= p * math.log2(p)

    return pred_letter, round(conf, 4), round(mean_agreement, 4), round(entropy, 4)
