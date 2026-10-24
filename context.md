# Strata — AI-Led Operational Discovery & Alignment Engine

> **Multi-Agent Discovery Platform for AI Agencies & Heads of AI** powered by **Nebius Token Factory** (`nvidia/nemotron-3-super-120b-a12b`) and **Tavily Search API**.  
> Built for the **Nebius x NVIDIA AI Hackathon** (Targeting: **Agentic Workflows / Enterprise AI**, **NVIDIA Nemotron on Nebius**, and **Best Use of Tavily** tracks).

---

## 1. Executive Summary & Core Thesis

Most enterprise AI projects fail for one fundamental reason:
> **Leadership automates the process they *think* they have, not the messy reality on the ground.**

In organizations from 5 to 500 people, the CEO assumes a linear, automated pipeline (e.g. DocuSign to CRM to Jira). But on the frontline:
- The **Sales Rep** promises custom SLAs on WhatsApp and logs them in private spreadsheets.
- The **CS Lead** ignores the CRM ticket and runs an internal interrogation call because data is incomplete.
- The **RevOps / IT Lead** manually backfills broken schemas every Friday afternoon.

**Strata** is the automated discovery engine used by AI Agencies and internal Heads of AI. Instead of spending 8 weeks and $150k on consultants for a static slide deck, Strata deploys autonomous agents to interview stakeholders in parallel, detect the **"Delusion Gap"**, map the actual **Shadow Process DAG**, and export an actionable **Autonomous Agent Blueprint & MCP Configuration**.

```
Stakeholders (CEO, Sales, CS, IT) 
               │
               ▼
   [Parallel Nemotron 120B Probes]
               │
               ▼
[Dual-DAG Synthesis & Alignment Gap Detection]
   - Presumed Process (Executive Fantasy)
   - Actual Shadow Process (Ground Truth + Friction Nodes)
   - Tribal Knowledge & Unwritten Rules
   - Delusion Index (0–100%)
               │
               ▼
   [Tavily Technical Feasibility Audit]
               │
               ▼
[1-Click Agent Blueprint & MCP Tool Deployment Package]
```

---

## 2. Alignment with Nebius x NVIDIA Hackathon Judging Criteria

| Judging Criterion | Judge Feedback from Webinar | How Strata Delivers |
| :--- | :--- | :--- |
| **1. Technological Implementation** | Use Nebius/Nemotron to full capability; agentic workflows; non-obvious use cases (Johnny & Jackie). | **Multi-Agent Discovery System**: Nemotron 120B conducts parallel unscripted stakeholder probing, cross-role discrepancy reconciliation, DAG synthesis, and MCP schema generation. |
| **2. Design & "Aha Moment"** | Clear "aha" in under 2 minutes; avoid look-alike "Claude-baked" apps (Jackie & Darlene). | **The Dual-DAG Visualizer**: Immediate visual contrast between the clean executive line and the messy looping shadow graph with glowing red friction nodes and clickable quote evidence. |
| **3. Potential Impact** | Real problem for a real audience; solve the "why" (Selena, Ricky, Sushmita). | Directly attacks the **80% failure rate of enterprise AI pilots**. Empowers AI agency founders and enterprise Heads of AI. |
| **4. Quality of Idea & Domain Expertise** | Domain expertise is a key differentiator (Aditya Sabu); publish failure cases & limits. | Grounded in 6+ months of real enterprise ERP/WhatsApp discovery experience. Explicitly flags **AI Landmines** (processes that will fail if automated today). |
| **Best Use of Tavily** | Must use live search meaningfully, not as an afterthought. | Tavily audits external API specs, schema limitations, and industry benchmarks before recommending an automation. |
| **The "Nemos MCP" Advantage** | Judges praised Nemos for turning memory into an MCP layer other agents can use. | Strata takes vetted quick wins and exports **production-ready MCP tool configurations & system prompts** for instant agent deployment. |

---

## 3. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **LLM Inference** | **Nebius Token Factory** | `nvidia/nemotron-3-super-120b-a12b` via OpenAI-compatible async client |
| **Search Intelligence**| **Tavily Search API** | `AsyncTavilyClient`, advanced search depth for live technical feasibility and API limits |
| **Backend API** | **FastAPI + Python 3.13** | Asynchronous REST API, Pydantic validation, concurrent task execution |
| **Database** | **aiosqlite** | `strata.db` tracking `discovery_sessions` and synthesized blueprints |
| **Frontend Framework**| **React 19 + Vite 8** | High-performance SPA with fast HMR |
| **UI Components** | **HeroUI v3** | Modern dark-mode interface with `@heroui/styles` |
| **Styling** | **Tailwind CSS v4** | Dark radial gradients, glassmorphism, responsive cards |
| **Animations & Graphs**| **Framer Motion + SVG / Canvas** | Animated probe terminals and interactive Dual-DAG node graph |

---

## 4. API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Health check & model/API connectivity status. |
| `GET /api/strata/presets` | `GET` | Returns horizontal enterprise presets (B2B SaaS Onboarding, Procurement Reconciliation). |
| `POST /api/strata/generate-intake` | `POST` | Dynamically generates tailored company profile, target workflow, and 4 stakeholder personas from company name, domain, and mandate. |
| `POST /api/strata/probe` | `POST` | Executes parallel multi-stakeholder unscripted discovery interviews with Nemotron 120B. |
| `POST /api/strata/synthesize` | `POST` | Generates Dual-DAG (Presumed vs Actual), Primary Verdict (Landmine flag), Discovered Adjacent Workflow, Delusion Metric, and Opportunity Matrix. |
| `POST /api/strata/ground` | `POST` | Queries Tavily for live technical feasibility benchmarks and integration limits. |
| `POST /api/strata/export-agent` | `POST` | Generates production-ready Agent Blueprint, System Prompt, Guardrails, and MCP Tool schema. |
| `POST /api/strata/interview-turn` | `POST` | Executes real-time conversational interview turns with employees using Nemotron 120B to extract ground truth workarounds and shadow tools. |

---

## 5. Repository Structure

```
Mimic/
├── archive/
│   └── mimic_benchmark/       # Archived personal prediction benchmark (PREREG.md, harness, label.py)
├── data/
│   └── strata_presets.json    # Horizontal enterprise discovery presets (roles, initial statements)
├── database.py                # aiosqlite discovery_sessions persistence
├── strata_engine.py           # Core discovery engine (Nemotron 120B multi-agent probes, DAG synthesis, Tavily grounding, MCP export)
├── main.py                    # FastAPI server exposing Strata discovery API
├── direct_test_engine.py      # Automated end-to-end backend verification test
├── frontend/                  # React 19 + Vite 8 + HeroUI interface
├── .env                       # API keys (NEBIUS_API_KEY, TAVILY_API_KEY)
└── requirements.txt           # Python dependencies
```

---

## 6. How to Run Locally

### 1. Backend (FastAPI)
```bash
# In c:\dev\Mimic
.venv\Scripts\uvicorn.exe main:app --reload --port 8000
```

### 2. Frontend (Vite + React)
```bash
# In c:\dev\Mimic\frontend
npm run dev
```

### 3. Verify Engine Directly
```bash
.venv\Scripts\python.exe direct_test_engine.py
```
