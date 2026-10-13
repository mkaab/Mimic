"""
harness/test_canary.py - Leak Canary & Invariant Test Suite for Mimic Autonomy Gate

Verifies:
1. Whitelist projection: predictor receives strictly BLIND_FIELDS, nothing else.
2. Label-flip canary: flipping label/reason on item t does NOT alter pred_t, conf_t, gate_t, or lb_t.
3. Miss path: 7/8 record gives Wilson ~0.59 and immediately drops below low/med thresholds.
4. High stakes: never AUTO below 16/16.
5. Edge cases: n=0 returns 0.0, low confidence veto, and deterministic (timestamp, id) sorting.
"""

import unittest
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.wilson import wilson_lower_bound, evaluate_autonomy_gate, STAKES_THRESHOLDS
from harness.loop import run_prequential_loop, BLIND_FIELDS, StreamEvalReport

class CanaryTestSuite(unittest.TestCase):

    def test_wilson_lower_bound_math(self):
        """Validates exact Wilson lower bounds at one-sided 90% (z=1.645)."""
        # n = 0 edge case
        self.assertEqual(wilson_lower_bound(0, 0), 0.0)
        
        # 5/5: 0.6488 < 0.65 (Low needs 6/6)
        lb_5_5 = wilson_lower_bound(5, 5, z=1.645)
        self.assertEqual(round(lb_5_5, 4), 0.6488)
        self.assertLess(lb_5_5, STAKES_THRESHOLDS["low"])
        
        # 6/6: 0.6892 >= 0.65 (Low unlocks at 6/6)
        lb_6_6 = wilson_lower_bound(6, 6, z=1.645)
        self.assertEqual(round(lb_6_6, 4), 0.6892)
        self.assertGreaterEqual(lb_6_6, STAKES_THRESHOLDS["low"])
        
        # 7/7: 0.7212 >= 0.70 (Medium unlocks at 7/7)
        lb_7_7 = wilson_lower_bound(7, 7, z=1.645)
        self.assertEqual(round(lb_7_7, 4), 0.7212)
        self.assertGreaterEqual(lb_7_7, STAKES_THRESHOLDS["medium"])
        
        # 7/8 (one miss): 0.5888 (~0.59, drops below even Low threshold of 0.65)
        lb_7_8 = wilson_lower_bound(7, 8, z=1.645)
        self.assertEqual(round(lb_7_8, 4), 0.5888)
        self.assertEqual(round(lb_7_8, 2), 0.59)
        self.assertLess(lb_7_8, STAKES_THRESHOLDS["low"])
        self.assertLess(lb_7_8, STAKES_THRESHOLDS["medium"])

    def test_high_stakes_never_auto_below_16(self):
        """High stakes requires 16/16 perfect record (0.8553 >= 0.85). 15/15 must escalate."""
        lb_15_15 = wilson_lower_bound(15, 15, z=1.645)
        self.assertEqual(round(lb_15_15, 4), 0.8472)
        is_auto_15, _ = evaluate_autonomy_gate(15, 15, "high", item_confidence=0.95)
        self.assertFalse(is_auto_15, "15/15 must NOT trigger high-stakes auto execution")
        
        lb_16_16 = wilson_lower_bound(16, 16, z=1.645)
        self.assertEqual(round(lb_16_16, 4), 0.8553)
        is_auto_16, _ = evaluate_autonomy_gate(16, 16, "high", item_confidence=0.95)
        self.assertTrue(is_auto_16, "16/16 must trigger high-stakes auto execution")

    def test_confidence_veto(self):
        """Item confidence < 0.70 must veto auto-execution even with a perfect Wilson bound."""
        # 10/10 has lb = 0.7870 (clears low & medium thresholds)
        is_auto_high_conf, _ = evaluate_autonomy_gate(10, 10, "medium", item_confidence=0.85)
        self.assertTrue(is_auto_high_conf)
        
        is_auto_low_conf, _ = evaluate_autonomy_gate(10, 10, "medium", item_confidence=0.69)
        self.assertFalse(is_auto_low_conf, "Confidence < 0.70 must veto auto-execution")

    def test_whitelist_projection_sanitizes_inputs(self):
        """Ensures predict_fn strictly receives the exact pinned BLIND_FIELDS set and zero leaked fields."""
        EXPECTED_PINNED_FIELDS = frozenset({
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
        self.assertEqual(BLIND_FIELDS, EXPECTED_PINNED_FIELDS, "BLIND_FIELDS definition has drifted from pinned spec")

        leaky_item = {
            "id": "dec_001",
            "category": "calendar",
            "stakes": "low",
            "timestamp": "2026-09-01T10:00:00Z",
            "inbound_text": "Meeting invite",
            "options": {"A": "Decline", "B": "Accept"},
            "option_semantics": ["accept", "decline"],
            "semantic_mapping": {"A": "decline", "B": "accept"},
            "requires_tavily": False,
            "search_query": "",
            # Leak vectors that must be stripped:
            "ground_truth_choice": "A",
            "ground_truth_action": "Decline",
            "relabel_choice": "B",
            "human_reason": "Never take introductory chats",
            "synthetic": True,
            "private_token": "secret_123"
        }
        
        received_keys = []
        
        def inspecting_predict(blind_item, state):
            nonlocal received_keys
            received_keys = list(blind_item.keys())
            self.assertEqual(set(blind_item.keys()), EXPECTED_PINNED_FIELDS)
            self.assertNotIn("ground_truth_choice", blind_item)
            self.assertNotIn("ground_truth_action", blind_item)
            self.assertNotIn("relabel_choice", blind_item)
            self.assertNotIn("human_reason", blind_item)
            self.assertNotIn("synthetic", blind_item)
            self.assertNotIn("private_token", blind_item)
            return ("A", 0.90)

        report = run_prequential_loop([leaky_item], inspecting_predict, lambda item, s: s, {})
        self.assertEqual(len(report.log), 1)
        self.assertEqual(set(received_keys), EXPECTED_PINNED_FIELDS)

    def test_label_flip_canary(self):
        """
        CRITICAL CANARY:
        Runs the loop twice. In Run 2, flip ground_truth_choice and human_reason on item t=3.
        Assert that for item t=3: pred, conf, gate, and lb are 100% IDENTICAL across runs.
        """
        base_items = [
            {
                "id": f"dec_{i:03d}",
                "category": "inbox",
                "stakes": "low",
                "timestamp": f"2026-09-{i:02d}T10:00:00Z",
                "inbound_text": f"Inbound inquiry {i}",
                "options": {"A": "Archive", "B": "Reply"},
                "requires_tavily": False,
                "search_query": "",
                "ground_truth_choice": "A",
                "human_reason": "Archive unsolicited cold outreach",
                "synthetic": True
            }
            for i in range(1, 6)
        ]
        
        # Run 1: Original labels
        run1_items = copy.deepcopy(base_items)
        
        # Run 2: Flipped label and reason on item 3
        run2_items = copy.deepcopy(base_items)
        run2_items[2]["ground_truth_choice"] = "B"
        run2_items[2]["human_reason"] = "Reply immediately because this is an exception"
        
        def heuristic_predict(blind_item, state):
            rules = state.get("rules", [])
            if rules:
                return ("B", 0.85)
            return ("A", 0.85)
            
        def rule_learn(item, state):
            new_state = copy.deepcopy(state)
            new_state.setdefault("rules", []).append(item.get("human_reason", ""))
            return new_state

        report1 = run_prequential_loop(run1_items, heuristic_predict, rule_learn, initial_state={})
        report2 = run_prequential_loop(run2_items, heuristic_predict, rule_learn, initial_state={})

        # Items 1, 2, 3 must have IDENTICAL prediction, confidence, gate decision, and Wilson bound!
        for idx in range(3):
            entry1 = report1.log[idx]
            entry2 = report2.log[idx]
            
            self.assertEqual(entry1.prediction, entry2.prediction, f"Item {idx+1} prediction differed")
            self.assertEqual(entry1.confidence, entry2.confidence, f"Item {idx+1} confidence differed")
            self.assertEqual(entry1.gate, entry2.gate, f"Item {idx+1} gate differed")
            self.assertEqual(entry1.wilson_lower, entry2.wilson_lower, f"Item {idx+1} Wilson lower bound differed")
        
        # For item 3 itself, hit status should differ (one hit, one miss)
        self.assertTrue(report1.log[2].hit)
        self.assertFalse(report2.log[2].hit)

        # After item 3, item 4's record and state CAN differ because item 3 was learned in step 3
        # In run 2, a rule was learned after item 3, so item 4 prediction is B
        self.assertEqual(report1.log[3].prediction, "A")
        self.assertEqual(report2.log[3].prediction, "B")

    def test_deterministic_tie_breaking(self):
        """Equal timestamps must sort deterministically by (timestamp, id)."""
        items = [
            {"id": "dec_z", "timestamp": "2026-09-01T10:00:00Z", "category": "calendar", "stakes": "low", "options": {"A": "1", "B": "2"}, "ground_truth_choice": "A", "human_reason": ""},
            {"id": "dec_a", "timestamp": "2026-09-01T10:00:00Z", "category": "calendar", "stakes": "low", "options": {"A": "1", "B": "2"}, "ground_truth_choice": "A", "human_reason": ""},
            {"id": "dec_m", "timestamp": "2026-09-01T10:00:00Z", "category": "calendar", "stakes": "low", "options": {"A": "1", "B": "2"}, "ground_truth_choice": "A", "human_reason": ""},
        ]
        report = run_prequential_loop(items, lambda item, s: ("A", 0.9), lambda item, s: s, {})
        processed_order = [entry.decision_id for entry in report.log]
        self.assertEqual(processed_order, ["dec_a", "dec_m", "dec_z"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
