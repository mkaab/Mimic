# Mimic — Project Context & Hackathon Architecture

> **Personal AI Intelligence Core** powered by **Nebius Token Factory** (`nvidia/nemotron-3-super-120b-a12b`) and **Tavily Search API**.  
> Built for the **Nebius x NVIDIA AI Hackathon** (Targeting: **Personal AI** & **Best Use of Tavily** tracks).

---

## 1. Executive Summary & Thesis (PRD v0.6)

Most AI assistants are designed around **memory** (retrieving facts you previously told them).  
**Mimic** asks a fundamentally different question:

> **"What if AI could learn to predict what you would choose, say, or do?"**

Before an autonomous AI agent can be trusted to act on your behalf, it needs a testable model of your judgment. Predicting your own decisions back to you in blind tests is how Mimic proves it understands you.

```
Capture → Remember → Understand → Predict → Reveal → Learn
```

---

## 2. Core Features & What We Built

### 1. Calibrated Behavioral Onboarding & True Sampling (§16, §18)
- **8 Calibrated A/B Questions**: 5 train scenarios calibrate decision traits (risk tolerance, decisiveness, operating style, directness); **3 held-out scenarios** are reserved for blind testing.
- **Optional MBTI Badges**: 16 selectable types or automated inference by Nemotron.
- **Mathematical Confidence Sampling**: Instead of relying on hallucinated self-reported confidence numbers, Mimic samples $N=7$ generations at $T=0.8$. The confidence score equals the empirical majority agreement share (e.g. 6/7 = 86%).

### 2. Live Scoreboard & Baseline Comparison (§7, §23)
- Concurrently tests **Mimic (Personalized Model)** vs. **Plain Nemotron (Generic AI without Persona)** on the held-out scenarios.
- Renders an animated scoreboard showing a definitive head-to-head verdict (e.g. **Mimic 2/3 vs. Plain Nemotron 0/3**), proving personalization value over generic LLM outputs.

### 3. Visible Learning Loop (§22, §34.6)
- When Mimic misses a prediction, the user clicks **"🧠 Teach Mimic"** and explains their reasoning.
- Nemotron 120B synthesizes a **concise, persistent behavioral rule** (e.g. *"Uses unexpected windfall money for travel unless saving for home purchase"*), persists it to SQLite, and generates a verification scenario.
- Retesting runs against the updated profile: Mimic's prediction **flips to match the user** (`✓ Verified`), visually proving continuous behavioral adaptation.

### 4. Grounded Decision Engine via Tavily (§20, §21 — Best Use of Tavily Track)
- For real-world dilemmas, Mimic executes live advanced search via Tavily and feeds real-time market data + personal model into Nemotron 120B.
- Displays the PRD's **3-Tier Analysis Grid**:
  1. 🌐 **What Tavily Found**: Live external facts + clickable citations (`↗ source`).
  2. 👤 **What Matters To You**: Tailored implications filtered through the user's risk tolerance, goals, and MBTI.
  3. 🎯 **What Mimic Predicts**: Personalized verdict & confidence % contrasted against a generic AI baseline.
- Includes **3 one-click trending dilemmas**:
  - *⚡ Join early-stage AI agent lab vs stay at Big Tech with liquid stock*
  - *⚡ Pivot product architecture to open-source Nemotron models vs proprietary APIs*
  - *⚡ Raise venture capital in 2026 AI market vs bootstrap profitably*

### 5. Fast-Track Judge Demo Mode (§16, §34.1)
- Single-click **"⚡ Fast-Track Demo for Judges"** loads a pre-seeded persona (*Alex, ENTJ Founder*) and benchmark scoreboard in under 1 second, allowing rapid judging without typing 8 questions.

---

## 3. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **LLM Inference** | **Nebius Token Factory** | `nvidia/nemotron-3-super-120b-a12b` via OpenAI-compatible async client |
| **Search Intelligence**| **Tavily Search API** | `AsyncTavilyClient`, advanced search depth for live grounded decision analysis |
| **Backend API** | **FastAPI + Python 3.13** | Asynchronous REST API, Pydantic validation, concurrent task execution |
| **Database** | **SQLite + aiosqlite** | `mimic.db` with auto-migration on server startup (`users`, `predictions` tables) |
| **Frontend Framework**| **React 19 + Vite 8** | High-performance SPA with fast HMR |
| **UI Components** | **HeroUI v3** | Modern dark-mode interface with `@heroui/styles` |
| **Styling** | **Tailwind CSS v4** | Dark radial gradients, glassmorphism, responsive cards |
| **Animations** | **Framer Motion 14** | Smooth transitions between quiz, scoreboard, and research states |

---

## 4. API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Health check endpoint. |
| `GET /questions` | `GET` | Returns the 8 calibrated behavioral A/B questions. |
| `POST /onboard` | `POST` | Builds persona from training questions + runs $N=7$ sampled predictions on held-out questions vs. baseline. |
| `POST /demo-persona` | `POST` | Instantly seeds and returns the demo persona (*Alex, ENTJ*) for 1-click judging. |
| `POST /predict` | `POST` | Blind reveal step 1: Generates and hides prediction in DB. |
| `POST /reveal` | `POST` | Blind reveal step 2: User commits actual answer, reveals hidden model prediction. |
| `POST /research-predict` | `POST` | Grounded Decision Engine: Tavily live web search + Nemotron 3-tier synthesis. |
| `POST /learn` | `POST` | Visible learning: Extracts rule from user correction + generates follow-up dilemma. |
| `POST /retest` | `POST` | Retests the learned rule on the follow-up dilemma to verify prediction flip. |
| `GET /models` | `GET` | Nebius connectivity verification: lists available Token Factory models. |

---

## 5. How to Run Locally

### Prerequisites
1. Ensure `.env` is configured with:
   ```bash
   NEBIUS_API_KEY=your_nebius_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

### Running the Services
Open two separate terminal tabs at the root of `c:\dev\Mimic`:

**Terminal 1 (Backend — FastAPI):**
```bash
.\.venv\Scripts\uvicorn main:app --port 8000 --reload
```
*(Runs on http://127.0.0.1:8000)*

**Terminal 2 (Frontend — Vite/React):**
```bash
cd frontend
npm run dev
```
*(Runs on http://localhost:5173)*

---

## 6. Hackathon Demo Walkthrough (2 Minutes)

1. **Cold Open (0:00 - 0:20)**: Open http://localhost:5173/. Click `⚡ Fast-Track Demo for Judges` (or type your name and tap 8 quick answers).
2. **The Benchmark (0:20 - 0:45)**: Show the **Scoreboard**: *"Mimic scored 2/3 (or 3/3) vs Plain Nemotron 0/3. Notice confidence is derived from mathematical sample agreement, not hallucinated numbers."*
3. **Visible Learning (0:45 - 1:15)**: On the missed card, click **"🧠 Teach Mimic"**, type a reason, and click **"Test If Mimic Flips Choice"**. Show the new rule card and the flipped verdict (`✓ Verified`).
4. **Tavily Grounded Engine (1:15 - 1:45)**: Click *"Test on live opportunities with Tavily →"*, select *⚡ Join AI agent lab vs Big Tech*. Point out the 3 panels: Live Web Facts (Tavily), Personal Implications (Mimic Persona), and Personalized Prediction vs Generic AI.
5. **Closing (1:45 - 2:00)**: *"Before agents act on our behalf, they need a model of us. That model is Mimic."*
