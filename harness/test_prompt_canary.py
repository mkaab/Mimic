"""
harness/test_prompt_canary.py - Real Arm Prompt Leak Canary

Verifies that for real evaluation arms (Zero-Shot, Few-Shot, Mimic Core):
1. The prompt at step t contains NO ground-truth labels, choices, or human reasons for items >= t.
2. Zero-Shot prompt contains ZERO history at all steps.
3. Few-Shot prompt at step t contains strictly history 1..t-1 and 0% future items.
4. Mimic Core prompt at step t contains only rules learned from misses strictly prior to t.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.arms import build_zero_shot_prompt, build_few_shot_prompt, build_mimic_prompt, learn_few_shot, learn_mimic
from harness.loop import BLIND_FIELDS

class PromptCanaryTestSuite(unittest.TestCase):

    def setUp(self):
        self.stream = [
            {
                "id": f"dec_{i:03d}",
                "category": "calendar" if i % 2 == 1 else "inbox",
                "stakes": "low",
                "timestamp": f"2026-09-{i:02d}T10:00:00Z",
                "inbound_text": f"Inbound inquiry {i}",
                "options": {"A": f"Action A for {i}", "B": f"Action B for {i}"},
                "ground_truth_choice": "A" if i % 2 == 1 else "B",
                "human_reason": f"Explicit human reasoning for item {i}",
                "synthetic": True
            }
            for i in range(1, 6)
        ]

    def test_zero_shot_prompt_has_no_history(self):
        """Zero-shot prompt must never contain previous history or reasons."""
        for item in self.stream:
            blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
            messages = build_zero_shot_prompt(blind_item)
            prompt_str = " ".join([m["content"] for m in messages])
            
            # Must contain no reasoning from any item
            for s in self.stream:
                self.assertNotIn(s["human_reason"], prompt_str)
                self.assertNotIn("PREVIOUS DECISIONS", prompt_str)

    def test_few_shot_prompt_never_leaks_current_or_future_items(self):
        """
        CRITICAL REAL-ARM CANARY:
        At step t, Few-Shot prompt must contain history 1..t-1,
        and MUST NOT contain choices or reasons from items t..N.
        """
        history_buffer = []
        
        for t_idx, item in enumerate(self.stream, start=1):
            blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
            
            # Build prompt at step t using history strictly through t-1
            messages = build_few_shot_prompt(blind_item, history_buffer)
            prompt_str = " ".join([m["content"] for m in messages])
            
            # 1. Assert current item's reason or choice never appear in prompt
            self.assertNotIn(
                item["human_reason"],
                prompt_str,
                f"Current item {item['id']} reason leaked at step t={t_idx}"
            )
            
            # 2. Assert strictly FUTURE items (t+1..N) never appear by ID, inbound_text, or reason
            for future_idx in range(t_idx, len(self.stream)):
                future_item = self.stream[future_idx]
                self.assertNotIn(
                    future_item["id"],
                    prompt_str,
                    f"Future item ID {future_item['id']} leaked at step t={t_idx}"
                )
                self.assertNotIn(
                    future_item["inbound_text"],
                    prompt_str,
                    f"Future item text {future_item['id']} leaked at step t={t_idx}"
                )
                self.assertNotIn(
                    future_item["human_reason"],
                    prompt_str,
                    f"Future item reason {future_item['id']} leaked at step t={t_idx}"
                )
                
            # 3. Assert prior items (1..t-1) DO appear in history context
            for prev_idx in range(0, t_idx - 1):
                prev_item = self.stream[prev_idx]
                self.assertIn(prev_item["human_reason"], prompt_str)
                self.assertIn(prev_item["options"][prev_item["ground_truth_choice"]], prompt_str)
                
            # Reveal label and append to history buffer AFTER prediction
            history_buffer = learn_few_shot(item, history_buffer)

    def test_mimic_prompt_never_leaks_current_or_future_rules(self):
        """
        Mimic Core prompt at step t must contain only rules learned from misses through t-1.
        Items t..N reasons must NOT exist in the prompt.
        """
        quiz_qa = [
            {"question": "Baseline risk question", "selected_choice": "A", "selected_text": "Take risk"},
            {"question": "Baseline focus question", "selected_choice": "B", "selected_text": "Protect focus"}
        ]
        mimic_state = {
            "quiz_qa": quiz_qa,
            "rules": []
        }
        
        for t_idx, item in enumerate(self.stream, start=1):
            blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
            
            messages = build_mimic_prompt(
                blind_item=blind_item,
                quiz_qa=mimic_state["quiz_qa"],
                rules=mimic_state["rules"]
            )
            prompt_str = " ".join([m["content"] for m in messages])
            
            # Assert NO current or future reasons exist in prompt
            for future_idx in range(t_idx - 1, len(self.stream)):
                future_item = self.stream[future_idx]
                self.assertNotIn(
                    future_item["human_reason"],
                    prompt_str,
                    f"Mimic prompt leak at step t={t_idx}: item {future_item['id']} reason in prompt."
                )
                
            # Simulate miss and update state AFTER step t
            mimic_state = learn_mimic(item, mimic_state)

    def test_profile_only_prompt_has_no_rules_or_updates(self):
        """Profile-Only arm prompt contains baseline quiz Q&A only, zero rules, zero history."""
        quiz_qa = [
            {"question": "Q1", "selected_choice": "A", "selected_text": "Answer 1"}
        ]
        for item in self.stream:
            blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
            from harness.arms import build_profile_only_prompt
            messages = build_profile_only_prompt(blind_item, quiz_qa)
            prompt_str = " ".join([m["content"] for m in messages])
            self.assertIn("Answer 1", prompt_str)
            self.assertNotIn("ACTIVE LEARNED HEURISTICS", prompt_str)
            self.assertNotIn("PREVIOUS DECISIONS", prompt_str)

if __name__ == "__main__":
    unittest.main(verbosity=2)
