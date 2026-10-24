# Mimic Pre-Registration Protocol & Benchmark Specification (v1.1)

**Date:** 2026-10-13  
**Status:** FROZEN PRE-LABELING  
**Git Tags:** `prereg-v1` (baseline), `prereg-v1.1` (verbatim Q&A & 9-arm isolation)

---

## 1. Pre-Registration Commitment
This document establishes the pre-registered specification for evaluating Mimic's Earned Autonomy Delegation Layer.
- **Zero Retrospective Scenario Tuning:** No scenario texts, option descriptions, search queries, or arm hyperparameters may be modified after human labeling begins or model outputs are observed.
- **Reporting Guarantee:** Generic zero-shot, classical baseline, profile-only, and perspective ensemble results will be reported exactly as observed, including all negative or neutral findings.

---

## 2. Frozen Artifact Hashes (SHA-256)

Prior to human ground-truth annotation, the following artifacts are strictly frozen and hashed:

| Artifact | Path | SHA-256 Hash |
|---|---|---|
| **Hyperparameters** | `config/arms.json` | `4c9c4332ff04163e96d6f6abcc234b33daf87b2f915cc65052ada854005ab99c` |
| **Candidate Scenarios** | `data/unlabeled_decisions.json` | `fafec5cf457909224ab5752a14f08c9ea37979722e6d8bb6a1ab8c93cfd658a9` |
| **User Baseline Profile** | `data/initial_state.json` | `723732c6752067e2b96556e7533e60a08a3479f67b7e7c55c73e3aed92792e64` |

---

## 3. Changes Since v1 (`prereg-v1` -> `prereg-v1.1`) and Rationale

1. **Purged `profile_summary` from `initial_state.json`:**
   - *Rationale:* The earlier draft summary contained agent-synthesized phrases ("analytical thoroughness before technical commitments", "protects deep focus over shallow networking") that could leak editorial bias into candidate decisions.
   - *Fix:* Deleted `profile_summary` entirely. `data/initial_state.json` now stores exclusively the 5 literal quiz question stems and the user's chosen answer text verbatim. Prompts format these mechanically without editorializing.
2. **Cold-Start Fairness (Few-Shot Parity):**
   - Few-Shot prompt now receives the same baseline quiz Q&A as Mimic Core, plus its history. Both arms start from identical cold-start information.
3. **Added Arm 9: Profile-Only:**
   - Evaluates predictions using baseline quiz Q&A only, with zero learned rules and zero updates. Directly isolates the value of the online learning loop from static profiling.
4. **Ensemble Baseline Inclusion:**
   - Confirmed that ensemble member prompts also receive the baseline quiz Q&A.
5. **Exact Whitelist Pinning:**
   - Whitelist canary test pinned to exact set equality `set(blind_item.keys()) == EXPECTED_PINNED_FIELDS`, eliminating loose subset checking.

---

## 4. Autonomy Gate & Evaluation Protocol

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

## 5. The 9 Evaluation Arms

Each arm maintains its own independent state without cross-arm contamination:

1. **Always-First Option:** Sanity check measuring position bias.
2. **Prequential Semantic Majority:** Majority semantic choice within category through $t-1$.
3. **Classical Logistic Regression:** Scikit-learn LogisticRegression (L2, C=1.0, seed=42) on TF-IDF (1-2 grams) + metadata fit strictly on items $1..t-1$. Restricted to `option_semantics`. Cold start fallback ($n < 5$).
4. **Zero-Shot Plain Nemotron:** NVIDIA Nemotron 120B on Nebius Token Factory with zero profile or history.
5. **Profile-Only Nemotron:** Nemotron 120B with baseline quiz Q&A only. Zero learned heuristics, zero updates.
6. **Few-Shot Nemotron:** Nemotron 120B with baseline quiz Q&A + full preceding history $1..t-1$ (actions and human reasons).
7. **Mimic Core:** Baseline quiz Q&A + active heuristics learned strictly on misses through $t-1$.
8. **Mimic + Tavily:** Mimic Core + cached web search lookup for `requires_tavily` items.
9. **Independent Perspective Ensemble:** 7 independent Nemotron 120B calls ($T=0.8$), each with baseline quiz Q&A, 60% rule subset, 3 nearest TF-IDF past decisions (1 dropped), and randomized option presentation. Majority vote share = confidence. Logs pairwise agreement and vote entropy.

---

## 6. Pre-Registered Hypotheses & Comparison Protocol

### A. Primary Comparisons (Capped at Two)

1. **Primary Comparison 1 (Mimic Core vs. Few-Shot — Distillation vs. Context Stuffing):**
   - **Hypothesis:** Structured, miss-driven heuristic rule extraction (Mimic Core) will match or exceed raw uncompressed context history (Few-Shot) in prequential accuracy and calibration (Brier score), while preventing prompt bloat and recency degradation.
2. **Primary Comparison 2 (Mimic Core vs. Profile-Only — Online Learning Value):**
   - **Hypothesis:** Mimic Core will achieve superior prequential accuracy, AUROC, and auto-execute precision compared to Profile-Only, demonstrating that the prequential miss-driven reflection loop adds measurable marginal value over a static user profile.

### B. Exploratory Comparisons & Analyses

- **Exploratory 1 (Earned Autonomy Calibration):** Mimic's Wilson lower-bound gate will maintain $\ge 90\%$ precision on auto-executed decisions across categories and stakes, ensuring safe autonomous delegation.
- **Exploratory 2 (Perspective Ensemble Uncertainty):** Independent Perspective Ensemble (7 diverse viewpoints) will yield superior uncertainty discrimination (higher AUROC) and well-calibrated confidence through empirical vote entropy and pairwise agreement compared to single-sample estimation.
- **Exploratory 3 (Tavily Grounding Lift):** Web search retrieval (Mimic + Tavily) will provide positive precision delta over ungrounded Mimic Core specifically on commitment items requiring live external verification (`requires_tavily == true`).
- **Exploratory 4 (Classical & Heuristic Baselines):** Performance of Classical Logistic Regression, Prequential Semantic Majority, Zero-Shot Plain Nemotron, and Always-First Option (position bias control) will be reported as observed to establish task floor and control metrics.

---

## 7. Verification Status
All 15 invariants and leak canaries pass in local test suite (`Ran 15 tests in 0.14s, OK`):
- Whitelist projection sanitization (pinned exact set)
- Label-flip canary (bit-for-bit invariance on step $t$)
- Classical fit-set isolation & determinism
- Real-arm prompt canaries (zero items $\ge t$, zero cross-member leakage)
- Wilson score mathematical boundaries
- AUROC edge case handling & bootstrap CI
