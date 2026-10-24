"""
harness/test_advanced_arms.py - Verification Suite for Arms 7 and 8

Verifies:
1. Classical determinism: Same seed yields identical predictions.
2. Classical fit-set test: Vectorizer and classifier fit strictly on items 1..t-1 (train size == t-1).
3. Classical label-flip canary: Flipping label/reason on item t does not alter item t's prediction, conf, or gate.
4. Ensemble prompt canary: Every member prompt (j=0..6) contains zero items >= t, zero cross-member leakage.
5. Ensemble aggregation & diversity diagnostics: Correctly computes vote share, pairwise agreement, and entropy.
"""

import unittest
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.loop import run_prequential_loop, BLIND_FIELDS
from harness.classical import PrequentialClassicalModel
from harness.ensemble import build_member_prompt, aggregate_ensemble_votes

class AdvancedArmsTestSuite(unittest.TestCase):

    def setUp(self):
        self.stream = [
            {
                "id": f"dec_{i:03d}",
                "category": "calendar",
                "stakes": "low",
                "timestamp": f"2026-09-{i:02d}T10:00:00Z",
                "inbound_text": f"Meeting invite number {i} discussing project sync",
                "options": {"A": "Accept meeting", "B": "Decline meeting"},
                "option_semantics": ["accept", "decline"],
                "semantic_mapping": {"A": "accept", "B": "decline"},
                "ground_truth_choice": "A" if i % 2 == 1 else "B",
                "semantic_choice": "accept" if i % 2 == 1 else "decline",
                "human_reason": f"Reason heuristic for decision {i}",
                "requires_tavily": False,
                "search_query": "",
                "synthetic": True
            }
            for i in range(1, 10)
        ]

    def test_classical_determinism(self):
        """Prequential classical model must be 100% deterministic with fixed seed."""
        model1 = PrequentialClassicalModel(seed=42)
        model2 = PrequentialClassicalModel(seed=42)

        # Train on first 6 items
        for item in self.stream[:6]:
            model1.update(item)
            model2.update(item)

        blind_test = {k: self.stream[6][k] for k in BLIND_FIELDS if k in self.stream[6]}
        pred1, conf1, n1 = model1.predict(blind_test)
        pred2, conf2, n2 = model2.predict(blind_test)

        self.assertEqual(pred1, pred2)
        self.assertEqual(conf1, conf2)
        self.assertEqual(n1, n2)

    def test_classical_fit_set_isolation(self):
        """Vectorizer and classifier must be fit strictly on items 1..t-1."""
        model = PrequentialClassicalModel(seed=42)
        
        for t_idx, item in enumerate(self.stream, start=1):
            blind_item = {k: item[k] for k in BLIND_FIELDS if k in item}
            
            # Assert train size in model is strictly t-1
            self.assertEqual(model.get_train_size(item["category"]), t_idx - 1)
            
            # Predict blind
            pred, conf, n_train = model.predict(blind_item)
            self.assertEqual(n_train, t_idx - 1)
            
            # Update strictly AFTER prediction
            model.update(item)

    def test_classical_label_flip_canary(self):
        """
        CLASSICAL LABEL-FLIP CANARY:
        Run prequential loop twice. In Run 2, flip label and reason on item t=7.
        Assert that for items 1..7: pred, conf, gate, and lb are IDENTICAL across runs.
        """
        run1_items = copy.deepcopy(self.stream)
        run2_items = copy.deepcopy(self.stream)
        
        # Flip label and reason on item 7
        run2_items[6]["ground_truth_choice"] = "B" if self.stream[6]["ground_truth_choice"] == "A" else "A"
        run2_items[6]["semantic_choice"] = "decline" if self.stream[6]["semantic_choice"] == "accept" else "accept"
        run2_items[6]["human_reason"] = "Flipped reason heuristic"

        def make_classical_runner():
            model = PrequentialClassicalModel(seed=42)
            def predict_fn(blind_item, state):
                pred, conf, _ = model.predict(blind_item)
                return pred, conf
            def learn_fn(revealed_item, state):
                model.update(revealed_item)
                return state
            return predict_fn, learn_fn

        p_fn1, l_fn1 = make_classical_runner()
        report1 = run_prequential_loop(run1_items, p_fn1, l_fn1, initial_state={})

        p_fn2, l_fn2 = make_classical_runner()
        report2 = run_prequential_loop(run2_items, p_fn2, l_fn2, initial_state={})

        # Items 1..7 must be bit-for-bit identical
        for idx in range(7):
            e1 = report1.log[idx]
            e2 = report2.log[idx]
            self.assertEqual(e1.prediction, e2.prediction, f"Classical prediction differed at item {idx+1}")
            self.assertEqual(e1.confidence, e2.confidence, f"Classical confidence differed at item {idx+1}")
            self.assertEqual(e1.gate, e2.gate, f"Classical gate differed at item {idx+1}")
            self.assertEqual(e1.wilson_lower, e2.wilson_lower, f"Classical Wilson bound differed at item {idx+1}")

    def test_ensemble_prompt_canary(self):
        """
        ENSEMBLE PROMPT CANARY:
        All 7 member prompts (j=0..6) at step t must contain ZERO tokens/IDs from items >= t,
        and no cross-member output leakage.
        """
        rules = [
            "[CALENDAR] Protect deep work blocks",
            "[INBOX] Decline cold outreach without mutual contact",
            "[COMMITMENTS] Never accept unpaid keynote without attendee alignment"
        ]
        history = self.stream[:3]
        target_item = self.stream[3] # item 4 (t=4)
        blind_item = {k: target_item[k] for k in BLIND_FIELDS if k in target_item}

        member_prompts = []
        for j in range(7):
            messages, m_map = build_member_prompt(
                blind_item=blind_item,
                quiz_qa=[{"question": "Q1", "selected_choice": "A", "selected_text": "Answer 1"}],
                rules=rules,
                history=history,
                member_idx=j
            )
            prompt_str = " ".join([m["content"] for m in messages])
            member_prompts.append(prompt_str)

            # 1. Assert NO future items (t=4..N) appear in member prompt
            for future_item in self.stream[3:]:
                if future_item["id"] != target_item["id"]:
                    self.assertNotIn(future_item["id"], prompt_str)
                    self.assertNotIn(future_item["inbound_text"], prompt_str)
                self.assertNotIn(future_item["human_reason"], prompt_str)

            # 2. Assert current item's human reason is NOT present
            self.assertNotIn(target_item["human_reason"], prompt_str)

        # 3. Assert member prompts are distinct (diversity from seeded shuffling/subsets)
        unique_prompts = set(member_prompts)
        self.assertGreater(len(unique_prompts), 1, "Ensemble members must receive diverse prompt variations")

    def test_ensemble_aggregation_metrics(self):
        """Tests vote aggregation, pairwise agreement, and entropy calculation."""
        blind_item = {
            "options": {"A": "Accept", "B": "Decline"},
            "semantic_mapping": {"A": "accept", "B": "decline"}
        }
        # Unanimous case (7 accept)
        picks_unanimous = ["A"] * 7
        maps_unanimous = [{"A": "accept", "B": "decline"}] * 7
        pred, conf, agree, ent = aggregate_ensemble_votes(picks_unanimous, maps_unanimous, blind_item)
        self.assertEqual(pred, "A")
        self.assertEqual(conf, 1.0)
        self.assertEqual(agree, 1.0)
        self.assertEqual(ent, 0.0)

        # 4-3 split case (4 accept, 3 decline)
        picks_split = ["A", "A", "A", "A", "B", "B", "B"]
        maps_split = [{"A": "accept", "B": "decline"}] * 7
        pred_s, conf_s, agree_s, ent_s = aggregate_ensemble_votes(picks_split, maps_split, blind_item)
        self.assertEqual(pred_s, "A")
        self.assertEqual(conf_s, round(4 / 7, 4))
        self.assertLess(agree_s, 1.0)
        self.assertGreater(ent_s, 0.9)

if __name__ == "__main__":
    unittest.main(verbosity=2)
