# Mimic Pre-Registration Protocol & Benchmark Specification

**Date:** 2026-10-13  
**Status:** FROZEN PRE-LABELING  
**Git Tag:** `prereg-v1`

---

## 1. Pre-Registration Commitment
This document establishes the pre-registered specification for evaluating Mimic's Earned Autonomy Delegation Layer.
- **Zero Retrospective Scenario Tuning:** No scenario texts, option descriptions, search queries, or arm hyperparameters may be modified after human labeling begins or model outputs are observed.
- **Reporting Guarantee:** Generic zero-shot, classical baseline, and perspective ensemble results will be reported exactly as observed, including all negative or neutral findings.

---

## 2. Frozen Artifact Hashes (SHA-256)

Prior to human ground-truth annotation, the following artifacts are strictly frozen and hashed:

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Hyperparameters** | `config/arms.json` | `4c9c4332ff04163e96d6f6abcc234b33daf87b2f915cc65052ada854005ab99c` |
| **Candidate Scenarios** | `data/unlabeled_decisions.json` | `fafec5cf457909224ab5752a14f08c9ea37979722e6d8bb6a1ab8c93cfd658a9` |
| **User Baseline Profile** | `data/initial_state.json` | `2c3876323f4134fe9134a3e72544ccba205f40c06863df42609340a43303586d` |

*Note on `data/initial_state.json`: An earlier draft placeholder was replaced with the user's live responses to the 5 baseline quiz questions (A, B, B, A, B) in commit `b29d07e` prior to freezing.*

---

## 3. Autonomy Gate & Evaluation Protocol

- **Online Prequential Stream:** For each inbound item $t \in \{1..30\}$, the model predicts blind and the gate evaluates autonomy using evidence accumulated strictly through $t-1$.
- **Strict Whitelist Projection:** Only `BLIND_FIELDS` (`id`, `category`, `stakes`, `timestamp`, `inbound_text`, `options`, `option_semantics`, `semantic_mapping`, `requires_tavily`, `search_query`) reach predictors. Labels, choices, and reasons are hidden by default.
- **Wilson Autonomy Gate:** Evaluates single-sided 90% Wilson lower bound ($z=1.645$):
  - Low Stakes: `0.65` (unlocks at 6/6)
  - Medium Stakes: `0.70` (unlocks at 7/7)
  - High Stakes: `0.85` (unlocks at 16/16)
  - Confidence Floor: `conf >= 0.70` (requires $\ge 5/7$ sample agreement)
- **Reporting Metrics:**
  - Headline Accuracy: Two-sided 95% Wilson confidence interval ($z=1.96$)
  - Calibration: Brier Score ($\text{mean}((\text{conf} - \text{hit})^2)$)
  - Discrimination: AUROC of confidence predicting hit vs. miss (with 1000-sample bootstrap 95% CI; `None` if single class)
  - Practical Delegation: Coverage (% auto-executed) and Auto-Execute Precision (% auto-executed that were correct)

---

## 4. The 8 Evaluation Arms

Each arm maintains its own independent state without cross-arm contamination:

1. **Always-First Option:** Sanity check measuring position bias.
2. **Prequential Semantic Majority:** Majority semantic choice within category through $t-1$.
3. **Classical Logistic Regression:** Scikit-learn LogisticRegression (L2, C=1.0, seed=42) on TF-IDF (1-2 grams) + metadata fit strictly on items $1..t-1$. Restricted to `option_semantics`. Cold start fallback ($n < 5$).
4. **Zero-Shot Plain Nemotron:** NVIDIA Nemotron 120B on Nebius Token Factory with zero profile or history.
5. **Few-Shot Nemotron:** Nemotron 120B with full preceding history $1..t-1$ (actions and human reasons).
6. **Mimic Core:** Frozen user profile + active heuristics learned strictly on misses through $t-1$.
7. **Mimic + Tavily:** Mimic Core + cached web search lookup for `requires_tavily` items.
8. **Independent Perspective Ensemble:** 7 independent Nemotron 120B calls ($T=0.8$), each with 60% rule subset, 3 nearest TF-IDF past decisions (1 dropped), and randomized option presentation. Majority vote share = confidence. Logs pairwise agreement and vote entropy.

---

## 5. Verification Status
All 14 invariants and leak canaries pass in local test suite (`Ran 14 tests in 0.08s, OK`):
- Whitelist projection sanitization
- Label-flip canary (bit-for-bit invariance on step $t$)
- Classical fit-set isolation & determinism
- Real-arm prompt canaries (zero items $\ge t$, zero cross-member leakage)
- Wilson score mathematical boundaries
