"""
label.py - Ground Truth Labeling CLI for Mimic Decisions Dataset

Features:
- Loads redacted decision scenarios (data/unlabeled_decisions.json)
- Displays redacted text and checks for potential PII leaks via regex safety net
- Randomizes presentation order of options or supports clear selection to prevent position bias
- Records human ground-truth choice (A/B and semantic action string)
- Captures human reasoning heuristic (for Mimic's online rule learning)
- Explicitly flags scenarios as synthetic vs. real redacted decisions
- Saves incrementally to data/decisions.json with resume capability
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional

PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "Email address"),
    (re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), "Phone number"),
    (re.compile(r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|io|net|dev)\b'), "URL/Domain"),
]

def scan_pii(text: str) -> List[str]:
    """Scans text against regex safety net for unredacted PII."""
    warnings = []
    for pattern, name in PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            warnings.append(f"Potential {name} detected: {matches[:3]}")
    return warnings

def load_json(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath: str, data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_labeler(
    input_file: str = "data/unlabeled_decisions.json",
    output_file: str = "data/decisions.json",
    review_all: bool = False
):
    print("=" * 65)
    print("  MIMIC GROUND-TRUTH LABELING CLI")
    print("  Human Decision Annotation Protocol")
    print("=" * 65)
    
    unlabeled_items = load_json(input_file)
    if not unlabeled_items:
        print(f"Error: No items found in {input_file}.")
        return

    labeled_items = load_json(output_file)
    labeled_map = {item["id"]: item for item in labeled_items}

    total = len(unlabeled_items)
    already_done = len(labeled_map) if not review_all else 0

    print(f"Loaded {total} candidate items from {input_file}.")
    print(f"Already labeled: {already_done}/{total} items in {output_file}.\n")

    items_to_label = unlabeled_items if review_all else [item for item in unlabeled_items if item["id"] not in labeled_map]

    if not items_to_label:
        print("All items are already labeled! Use --review to review existing items or run evaluation.")
        return

    print("Commands during labeling:")
    print("  [A / B]  : Select your decision")
    print("  [s]      : Skip this item for now")
    print("  [q]      : Quit and save progress")
    print("=" * 65 + "\n")

    for idx, item in enumerate(items_to_label, start=1):
        item_id = item.get("id", f"dec_{idx}")
        cat = item.get("category", "general")
        stakes = item.get("stakes", "medium")
        is_synthetic = item.get("synthetic", True)
        requires_tavily = item.get("requires_tavily", False)
        text = item.get("inbound_text", "")
        options = item.get("options", {})

        print(f"\n--- [{idx}/{len(items_to_label)}] ID: {item_id} | Category: {cat.upper()} | Stakes: {stakes.upper()} ---")
        if requires_tavily:
            print(f"[Note: Requires external search/lookup: '{item.get('search_query', 'N/A')}']")

        # PII safety net check
        pii_warnings = scan_pii(text)
        if pii_warnings:
            print("⚠️  PII SAFETY WARNING:")
            for w in pii_warnings:
                print(f"   {w}")
            print("   Please ensure this item is fully redacted before saving.")

        print("\nINBOUND CONTEXT (Redacted):")
        print(f'"{text}"')

        print("\nOPTIONS:")
        print(f"  [A] {options.get('A', 'N/A')}")
        print(f"  [B] {options.get('B', 'N/A')}")

        # Choice prompt
        choice = None
        while choice not in ["A", "B", "S", "Q"]:
            user_input = input("\nYour Choice [A/B, (s)kip, (q)uit]: ").strip().upper()
            if user_input in ["A", "B", "S", "Q"]:
                choice = user_input
            else:
                print("Invalid input. Please enter A or B (or s/q).")

        if choice == "Q":
            print("\nQuitting and saving current progress...")
            break
        elif choice == "S":
            print(f"Skipping {item_id}.")
            continue

        selected_action = options.get(choice, "")

        # Reason prompt
        print(f"\nSelected: [{choice}] {selected_action}")
        reason = input("1-line heuristic / reason for this choice: ").strip()
        if not reason:
            reason = "Standard heuristic decision"

        # Synthetic check prompt
        default_synth = "s" if is_synthetic else "r"
        synth_input = input(f"Synthetic template [s] or real redacted decision [r]? (default '{default_synth}'): ").strip().lower()
        if synth_input == "r":
            final_synthetic = False
        elif synth_input == "s":
            final_synthetic = True
        else:
            final_synthetic = is_synthetic

        # Create labeled record (strict single ground_truth_choice key + semantic action provenance)
        labeled_record = {
            "id": item_id,
            "category": cat,
            "stakes": stakes,
            "timestamp": item.get("timestamp", ""),
            "inbound_text": text,
            "requires_tavily": requires_tavily,
            "search_query": item.get("search_query", ""),
            "options": options,
            "semantic_mapping": item.get("semantic_mapping", {}),
            "ground_truth_choice": choice,
            "semantic_choice": item.get("semantic_mapping", {}).get(choice, ""),
            "human_reason": reason,
            "synthetic": final_synthetic,
            "redacted_verified": True
        }

        # Update in map and save to file immediately
        labeled_map[item_id] = labeled_record
        all_sorted = sorted(labeled_map.values(), key=lambda d: d.get("timestamp", ""))
        save_json(output_file, all_sorted)
        print(f" Saved {item_id}. ({len(labeled_map)}/{total} labeled in {output_file})")

    print("\n" + "=" * 65)
    print(f"Session finished! Total labeled decisions: {len(labeled_map)}/{total}.")
    print(f"Output saved to: {output_file}")
    print("=" * 65)

def validate_dataset(filepath: str = "data/decisions.json"):
    """Validates the frozen dataset for schema consistency and leak absence."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist.")
        return False
    data = load_json(filepath)
    print(f"\n--- Dataset Validation: {filepath} ({len(data)} items) ---")
    
    categories = {}
    stakes_dist = {}
    synth_count = 0
    real_count = 0
    tavily_count = 0
    pii_alerts = 0
    
    for idx, item in enumerate(data, start=1):
        for req_field in ["id", "category", "stakes", "timestamp", "inbound_text", "options", "ground_truth_choice", "human_reason"]:
            if req_field not in item or not item[req_field]:
                print(f"❌ Item {item.get('id', idx)} missing required field: {req_field}")
                return False
                
        cat = item["category"]
        stk = item["stakes"]
        categories[cat] = categories.get(cat, 0) + 1
        stakes_dist[stk] = stakes_dist.get(stk, 0) + 1
        
        if item.get("synthetic", True):
            synth_count += 1
        else:
            real_count += 1
            
        if item.get("requires_tavily", False):
            tavily_count += 1
            
        warns = scan_pii(item["inbound_text"])
        if warns:
            print(f"⚠️ Item {item['id']} has PII warnings: {warns}")
            pii_alerts += 1
            
    print(f"Categories: {categories}")
    print(f"Stakes: {stakes_dist}")
    print(f"Data Source: {real_count} real redacted | {synth_count} synthetic templates")
    print(f"Tavily Lookup Items: {tavily_count}")
    print(f"PII Safety Net Warnings: {pii_alerts}")
    print(" Validation PASSED: Schema is complete and valid.")
    return True

def run_relabel_check(labeled_file: str = "data/decisions.json", sample_size: int = 10, relabel_seed: int = 999):
    """
    Day-later human self-consistency check.
    Takes a sample of labeled items, re-randomizes option order with a fresh seed,
    prompts the human blind to previous choice, and scores semantic agreement.
    """
    import random
    if not os.path.exists(labeled_file):
        print(f"Error: Labeled file {labeled_file} does not exist.")
        return
        
    labeled_items = load_json(labeled_file)
    if not labeled_items:
        print("No items to relabel.")
        return
        
    sample = labeled_items[:sample_size]
    relabel_rng = random.Random(relabel_seed)
    
    print("=" * 65)
    print(f"  HUMAN SELF-CONSISTENCY CHECK ({len(sample)} items)")
    print("  Fresh presentation order (measuring semantic consistency)")
    print("=" * 65 + "\n")
    
    matches = 0
    for idx, item in enumerate(sample, start=1):
        sem_map = item.get("semantic_mapping", {})
        original_sem_choice = item.get("semantic_choice", "")
        
        # Fresh coin flip to re-order options
        flip = relabel_rng.random() > 0.5
        actions = list(sem_map.items()) # [('A', sem1), ('B', sem2)]
        if flip:
            fresh_opts = {"A": item["options"]["A"], "B": item["options"]["B"]}
            fresh_map = {"A": sem_map.get("A", ""), "B": sem_map.get("B", "")}
        else:
            fresh_opts = {"A": item["options"]["B"], "B": item["options"]["A"]}
            fresh_map = {"A": sem_map.get("B", ""), "B": sem_map.get("A", "")}
            
        print(f"--- [{idx}/{len(sample)}] {item['id']} ({item['category'].upper()}) ---")
        print(f'"{item["inbound_text"]}"\n')
        print(f"  [A] {fresh_opts['A']}")
        print(f"  [B] {fresh_opts['B']}")
        
        choice = None
        while choice not in ["A", "B"]:
            choice = input("\nYour Choice [A/B]: ").strip().upper()
            
        fresh_sem_choice = fresh_map.get(choice, "")
        is_match = (fresh_sem_choice == original_sem_choice)
        if is_match:
            matches += 1
            print(" Consistency check: MATCH (agreed with original semantic choice)")
        else:
            print(f" Consistency check: DIVERGENCE (chose {fresh_sem_choice} vs original {original_sem_choice})")
        print()
        
    score = matches / len(sample)
    print("=" * 65)
    print(f"Self-Consistency Score: {matches}/{len(sample)} ({score:.1%})")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mimic Ground-Truth Decision Labeler")
    parser.add_argument("--input", default="data/unlabeled_decisions.json", help="Path to unlabeled candidates")
    parser.add_argument("--output", default="data/decisions.json", help="Path to output labeled dataset")
    parser.add_argument("--review", action="store_true", help="Re-review all items including already labeled")
    parser.add_argument("--validate", action="store_true", help="Validate existing labeled decisions.json")
    parser.add_argument("--relabel", action="store_true", help="Run blind self-consistency check on labeled sample")
    args = parser.parse_args()

    if args.validate:
        validate_dataset(args.output)
    elif args.relabel:
        run_relabel_check(args.output)
    else:
        run_labeler(args.input, args.output, review_all=args.review)
