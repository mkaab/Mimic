"""
harness/classical.py - Arm 7: Classical Prequential Logistic Regression Baseline

Features:
- One LogisticRegression model per category (L2 penalty, C=1.0, random_state=42)
- Feature extraction: TF-IDF (1-2 grams, max 500 features) fit strictly on items 1..t-1
  plus stakes, requires_tavily, weekday, and hour
- Restricted candidate prediction: outputs only among actions in option_semantics
- Confidence: predicted probability of the winning candidate action
- Cold start: falls back to prequential majority if n_train < 5 or single class seen
- Learner updates after every item (hits and misses)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

STAKES_MAP = {"low": 0.0, "medium": 1.0, "high": 2.0}

def parse_temporal_features(ts_str: str) -> Tuple[float, float]:
    """Extracts weekday (0-6) and hour (0-23) from ISO timestamp."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return float(dt.weekday()), float(dt.hour)
    except Exception:
        return 0.0, 12.0

class PrequentialClassicalModel:
    def __init__(
        self,
        C: float = 1.0,
        penalty: str = "l2",
        tfidf_max_features: int = 500,
        ngram_range: Tuple[int, int] = (1, 2),
        min_train_per_category: int = 5,
        seed: int = 42
    ):
        self.C = C
        self.penalty = penalty
        self.tfidf_max_features = tfidf_max_features
        self.ngram_range = ngram_range
        self.min_train_per_category = min_train_per_category
        self.seed = seed
        # Category history strictly through t-1
        self.history_by_category: Dict[str, List[Dict[str, Any]]] = {}

    def get_train_size(self, category: str) -> int:
        return len(self.history_by_category.get(category, []))

    def _extract_dense_features(self, item: Dict[str, Any]) -> List[float]:
        stakes_val = STAKES_MAP.get(item.get("stakes", "medium"), 1.0)
        tavily_val = 1.0 if item.get("requires_tavily", False) else 0.0
        weekday_val, hour_val = parse_temporal_features(item.get("timestamp", ""))
        return [stakes_val, tavily_val, weekday_val, hour_val]

    def predict(self, blind_item: Dict[str, Any]) -> Tuple[str, float, int]:
        """
        Predicts blind item using history strictly through t-1.
        Returns: (predicted_letter, confidence, n_train)
        """
        cat = blind_item.get("category", "")
        history = self.history_by_category.get(cat, [])
        n_train = len(history)

        candidate_semantics = set(blind_item.get("option_semantics", []))
        sem_map = blind_item.get("semantic_mapping", {}) # {"A": "accept", "B": "decline"}
        reverse_map = {v: k for k, v in sem_map.items()}

        unique_labels = set(h.get("semantic_choice") for h in history if h.get("semantic_choice"))

        # Cold-start check
        if n_train < self.min_train_per_category or len(unique_labels) < 2:
            # Fall back to prequential majority
            counts = {}
            for h in history:
                sc = h.get("semantic_choice")
                if sc in candidate_semantics:
                    counts[sc] = counts.get(sc, 0) + 1
            
            # Find candidate with highest count
            best_action = None
            best_count = -1
            total_candidate_counts = sum(counts.values())
            for cand in candidate_semantics:
                c = counts.get(cand, 0)
                if c > best_count:
                    best_count = c
                    best_action = cand

            conf = (best_count / total_candidate_counts) if total_candidate_counts > 0 else 0.50
            if not best_action or best_count == 0:
                best_letter = "A"
                conf = 0.50
            else:
                best_letter = reverse_map.get(best_action, "A")
            return best_letter, round(conf, 4), n_train

        # Vectorizer fit strictly on items 1..t-1 in this category
        texts = [h.get("inbound_text", "") for h in history]
        labels = [h.get("semantic_choice", "") for h in history]

        vectorizer = TfidfVectorizer(
            max_features=self.tfidf_max_features,
            ngram_range=self.ngram_range
        )
        X_tfidf = vectorizer.fit_transform(texts).toarray()
        
        # Dense metadata features
        dense_feats = np.array([self._extract_dense_features(h) for h in history])
        X_train = np.hstack([X_tfidf, dense_feats])
        y_train = np.array(labels)

        clf = LogisticRegression(
            C=self.C,
            random_state=self.seed,
            solver="lbfgs",
            max_iter=200
        )
        clf.fit(X_train, y_train)

        # Transform blind test item
        test_tfidf = vectorizer.transform([blind_item.get("inbound_text", "")]).toarray()
        test_dense = np.array([self._extract_dense_features(blind_item)])
        X_test = np.hstack([test_tfidf, test_dense])

        probs = clf.predict_proba(X_test)[0] # shape (n_classes,)
        classes = list(clf.classes_)

        # Restrict candidates to option_semantics
        candidate_probs = {}
        for cls_name, prob in zip(classes, probs):
            if cls_name in candidate_semantics:
                candidate_probs[cls_name] = prob

        # If candidates were never seen in training classes, pick first candidate
        if not candidate_probs:
            return "A", 0.50, n_train

        best_cand = max(candidate_probs.keys(), key=lambda k: candidate_probs[k])
        # Normalized confidence among valid candidates
        total_cand_p = sum(candidate_probs.values())
        norm_conf = candidate_probs[best_cand] / total_cand_p if total_cand_p > 0 else 0.50

        best_letter = reverse_map.get(best_cand, "A")
        return best_letter, round(float(norm_conf), 4), n_train

    def update(self, revealed_item: Dict[str, Any]) -> None:
        """Updates category history after ground truth label is revealed at t."""
        cat = revealed_item.get("category", "")
        self.history_by_category.setdefault(cat, []).append(revealed_item)
