import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiosqlite

from database import init_db, get_db
import strata_engine

app = FastAPI(
    title="Strata — Operational Discovery & Alignment Engine",
    description="Multi-agent operational discovery for AI agencies & Heads of AI powered by Nebius (NVIDIA Nemotron 120B) and Tavily."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
def health_check():
    return {
        "status": "online",
        "product": "Strata",
        "model": strata_engine.MODEL_NAME,
        "nebius_connected": bool(strata_engine.NEBIUS_API_KEY),
        "tavily_connected": bool(strata_engine.TAVILY_API_KEY)
    }

@app.get("/api/strata/presets")
def get_presets():
    """Returns curated horizontal enterprise presets for quick demonstration."""
    preset_path = os.path.join(os.path.dirname(__file__), "data", "strata_presets.json")
    if not os.path.exists(preset_path):
        raise HTTPException(status_code=404, detail="Presets file not found")
    with open(preset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

class IntakeGenerationRequest(BaseModel):
    company_name: str
    domain: Optional[str] = None
    mandate: str
    roles_hint: Optional[str] = None

@app.post("/api/strata/generate-intake")
async def generate_intake(req: IntakeGenerationRequest):
    """
    Onboards a live custom enterprise:
    Uses Tavily (for web enrichment) + Nemotron 120B to generate the full operational discovery profile.
    """
    try:
        scenario = await strata_engine.generate_custom_company_scenario(
            company_name=req.company_name,
            domain=req.domain,
            mandate=req.mandate,
            roles_hint=req.roles_hint
        )
        return {"status": "success", "scenario": scenario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProbeRequest(BaseModel):
    scenario: Dict[str, Any]

@app.post("/api/strata/probe")
async def probe_stakeholders(req: ProbeRequest):
    """
    Simulates or executes unscripted multi-agent discovery probes across all stakeholders in parallel.
    Uncovers shadow tools, friction points, and unwritten operational rules.
    """
    try:
        results = await strata_engine.run_parallel_probes(req.scenario)
        return {"status": "success", "probes": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SynthesizeRequest(BaseModel):
    scenario: Dict[str, Any]
    transcripts: List[Dict[str, Any]]

@app.post("/api/strata/synthesize")
async def synthesize_blueprint(req: SynthesizeRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Synthesizes the complete Dual-DAG, alignment gaps, tribal knowledge catalog,
    delusion metric, and AI opportunity matrix.
    """
    try:
        blueprint = await strata_engine.synthesize_blueprint(req.scenario, req.transcripts)
        
        # Save session to SQLite
        try:
            await db.execute(
                """
                INSERT INTO discovery_sessions (scenario_id, scenario_title, target_workflow, blueprint_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    req.scenario.get("id", "custom"),
                    req.scenario.get("title", "Custom Scenario"),
                    req.scenario.get("target_workflow", "Custom Workflow"),
                    json.dumps(blueprint)
                )
            )
            await db.commit()
        except Exception as db_err:
            print("DB save error (non-fatal):", db_err)

        return {"status": "success", "blueprint": blueprint}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GroundRequest(BaseModel):
    opportunity_title: str
    target_workflow: str

@app.post("/api/strata/ground")
async def ground_opportunity(req: GroundRequest):
    """
    Queries Tavily for live technical feasibility benchmarks, API capabilities,
    and reference implementations for a recommended AI automation.
    """
    try:
        grounding = await strata_engine.ground_opportunity_with_tavily(
            req.opportunity_title,
            req.target_workflow
        )
        return {"status": "success", "grounding": grounding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExportAgentRequest(BaseModel):
    opportunity: Dict[str, Any]
    scenario_title: str
    grounding: Dict[str, Any]

@app.post("/api/strata/export-agent")
async def export_agent_blueprint(req: ExportAgentRequest):
    """
    Generates a production-grade Agent Deployment Blueprint and MCP Tool Configuration
    derived directly from discovered ground truth.
    """
    try:
        package = await strata_engine.generate_agent_blueprint_and_mcp(
            req.opportunity,
            req.scenario_title,
            req.grounding
        )
        return {"status": "success", "package": package}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LiveInterviewTurnRequest(BaseModel):
    company_name: str
    target_workflow: str
    role_name: str
    role_title: str
    tactical_probe_strategy: str
    conversation_history: List[Dict[str, str]]
    user_message: str

@app.post("/api/strata/interview-turn")
async def live_interview_turn(req: LiveInterviewTurnRequest):
    """
    Executes a real-time conversational interview turn with an actual employee using Nemotron-3 120B.
    """
    try:
        result = await strata_engine.conduct_live_interview_turn(
            company_name=req.company_name,
            target_workflow=req.target_workflow,
            role_name=req.role_name,
            role_title=req.role_title,
            tactical_probe_strategy=req.tactical_probe_strategy,
            conversation_history=req.conversation_history,
            user_message=req.user_message
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

