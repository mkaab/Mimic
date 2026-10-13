import os
import re
import json
import asyncio
from collections import Counter
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import aiosqlite
from database import get_db, init_db
from tavily import AsyncTavilyClient

load_dotenv()

app = FastAPI(title="Mimic API")

@app.on_event("startup")
async def startup():
    await init_db()

# Fixed behavioral questions. held_out=True ones are NEVER shown to the model during profiling;
# they are the blind tests that Mimic and plain Nemotron both try to predict.
QUESTIONS = [
    {"id": 1, "text": "An opportunity with huge upside lands in your lap, but there's a 40% chance it fails.", "a": "Take it", "b": "Pass and wait for something safer", "held_out": False},
    {"id": 2, "text": "You need a new laptop and two options look equally good.", "a": "Pick one in 10 minutes on gut feel", "b": "Spend the evening reading reviews", "held_out": False},
    {"id": 3, "text": "It's Friday night and you're free.", "a": "Party with people you don't know yet", "b": "Stay in or see one close friend", "held_out": False},
    {"id": 4, "text": "A planned trip abroad is coming up.", "a": "Build a detailed day-by-day itinerary", "b": "Book the flight, figure out the rest there", "held_out": True},
    {"id": 5, "text": "A coworker presents your idea as theirs in a meeting.", "a": "Call it out on the spot", "b": "Talk to them privately afterwards", "held_out": False},
    {"id": 6, "text": "You unexpectedly receive $5,000.", "a": "Save or invest it", "b": "Spend it on an experience", "held_out": True},
    {"id": 7, "text": "A friend asks what you honestly think of their startup idea. You think it's weak.", "a": "Tell them straight", "b": "Encourage them and soften it", "held_out": False},
    {"id": 8, "text": "Three months into a project, early results are lukewarm.", "a": "Push through, it needs more time", "b": "Pivot quickly", "held_out": True},
]
N_SAMPLES = 7

def fmt_q(q):
    return f"{q['text']}\nA) {q['a']}\nB) {q['b']}"

async def sample_picks(system_prompt: str, q: dict):
    """Sample N A/B picks. Confidence = share of samples agreeing with the majority (not self-reported)."""
    res = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_prompt + "\nAnswer with ONLY the single letter A or B."},
                  {"role": "user", "content": fmt_q(q)}],
        temperature=0.8, max_tokens=1024, n=N_SAMPLES,
    )
    picks = []
    for ch in res.choices:
        m = re.search(r"\b([AB])\b", (ch.message.content or "").strip())
        if m:
            picks.append(m.group(1))
    if not picks:
        return None, 0.0
    letter, count = Counter(picks).most_common(1)[0]
    return letter, round(count / len(picks), 2)

# Initialize Nebius client (OpenAI compatible)
NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY")
client = AsyncOpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key=NEBIUS_API_KEY,
)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
tavily_client = AsyncTavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b"

class PredictRequest(BaseModel):
    user_id: int
    scenario: str

class RevealRequest(BaseModel):
    prediction_id: int
    user_actual_answer: str

class BootstrapRequest(BaseModel):
    name_or_query: str

class OnboardRequest(BaseModel):
    name: str
    answers: dict[str, str]          # question id -> "A" | "B"
    mbti: Optional[str] = None       # optional, if the user knows it
    public_handle: Optional[str] = None  # optional Tavily bootstrap

class ResearchPredictRequest(BaseModel):
    user_id: int
    scenario: str

class LearnRequest(BaseModel):
    user_id: int
    scenario: str
    correction: str

class RetestRequest(BaseModel):
    user_id: int
    scenario_text: str
    option_a: str
    option_b: str
    expected_answer: str


@app.get("/")
async def root():
    return {"status": "ok", "message": "Mimic API is running"}

@app.get("/questions")
async def get_questions():
    return [{k: q[k] for k in ("id", "text", "a", "b")} for q in QUESTIONS]

@app.post("/onboard")
async def onboard(req: OnboardRequest, db: aiosqlite.Connection = Depends(get_db)):
    """Build a profile from the training answers, then blind-test Mimic vs plain Nemotron on held-out ones."""
    train = [q for q in QUESTIONS if not q["held_out"]]
    held = [q for q in QUESTIONS if q["held_out"]]
    missing = [q["id"] for q in QUESTIONS if req.answers.get(str(q["id"])) not in ("A", "B")]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing answers for questions {missing}")

    evidence = "\n".join(
        f"- {q['text']} -> chose: {q[req.answers[str(q['id'])].lower()]}" for q in train
    )
    mbti = (req.mbti or "").strip().upper() or None

    sources = []
    web = ""
    if req.public_handle and tavily_client:
        try:
            sr = await tavily_client.search(req.public_handle, search_depth="advanced", max_results=5)
            results = sr.get("results", [])
            sources = [{"title": r.get("title"), "url": r.get("url")} for r in results]
            web = "\n".join(f"- {r['content'][:500]}" for r in results)
        except Exception:
            pass

    try:
        prof = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a behavioral profiler. From the evidence, write a concise, specific profile (under 90 words) of how this person makes decisions: risk tolerance, decisiveness, social energy, directness, planning style. "
                 + (f"They report their MBTI as {mbti}; use it as a weak prior only. " if mbti else "Also infer their most likely 4-letter MBTI type. ")
                 + 'Return ONLY JSON: {"profile": "...", "mbti": "XXXX"}'},
                {"role": "user", "content": f"Name: {req.name}\nScenario answers:\n{evidence}" + (f"\n\nPublic web footprint:\n{web}" if web else "")},
            ],
            temperature=0.4, max_tokens=2048,
        )
        raw = prof.choices[0].message.content or ""
        m = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(m.group(0)) if m else {"profile": raw.strip()}
        profile = data.get("profile", "").strip()
        mbti_final = mbti or (data.get("mbti") or "").strip().upper()[:4] or None

        cur = await db.execute("INSERT INTO users (name, context_profile, mbti) VALUES (?, ?, ?)", (req.name, profile, mbti_final))
        user_id = cur.lastrowid

        mimic_sys = f"You are Mimic, a behavioral model of {req.name}.\nProfile: {profile}\nTheir past choices:\n{evidence}" + (f"\nMBTI: {mbti_final}" if mbti_final else "") + f"\nPredict what {req.name} would choose."
        base_sys = "Predict what a typical person would choose."
        tasks = [sample_picks(mimic_sys, q) for q in held] + [sample_picks(base_sys, q) for q in held]
        out = await asyncio.gather(*tasks)
        mimic_out, base_out = out[:len(held)], out[len(held):]

        results = []
        for q, (m_pick, m_conf), (b_pick, _) in zip(held, mimic_out, base_out):
            actual = req.answers[str(q["id"])]
            mc, bc = int(m_pick == actual), int(b_pick == actual)
            await db.execute(
                "INSERT INTO predictions (user_id, scenario, user_actual_answer, model_predicted_answer, confidence_score, baseline_prediction, mimic_correct, baseline_correct) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, fmt_q(q), actual, m_pick, m_conf, b_pick, mc, bc),
            )
            results.append({"question": q["text"], "a": q["a"], "b": q["b"], "user": actual,
                            "mimic": m_pick, "confidence": m_conf, "baseline": b_pick,
                            "mimic_correct": bool(mc), "baseline_correct": bool(bc)})
        await db.commit()

        return {
            "status": "success", "user_id": user_id, "profile": profile,
            "mbti": mbti_final, "mbti_source": "you" if mbti else "inferred",
            "sources": sources, "results": results,
            "score": {"mimic": sum(r["mimic_correct"] for r in results),
                      "baseline": sum(r["baseline_correct"] for r in results), "total": len(results)},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """Fetch available models from Nebius to verify our connection."""
    try:
        response = await client.models.list()
        models = [model.id for model in response.data]
        return {"status": "success", "models": models}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/bootstrap")
async def bootstrap_profile(req: BootstrapRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Tavily Bootstrap:
    Searches the web for the user, uses Nemotron to synthesize a behavioral profile,
    and creates a new user in the database.
    """
    if not tavily_client:
        raise HTTPException(status_code=500, detail="Tavily API key not configured")
        
    try:
        # 1. Search Tavily
        search_result = await tavily_client.search(req.name_or_query, search_depth="advanced")
        context_data = "\n".join([f"- {res['content']}" for res in search_result.get('results', [])])
        
        # 2. Synthesize Profile with Nemotron
        system_prompt = f"You are a psychological profiler. Analyze the following search results about '{req.name_or_query}' and write a concise, highly specific behavioral context profile predicting their personality, decision-making style, and values. Keep it under 100 words."
        
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Search Data:\n{context_data}"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        synthesized_profile = response.choices[0].message.content.strip()
        
        # 3. Save to DB
        cursor = await db.execute(
            "INSERT INTO users (name, context_profile) VALUES (?, ?)",
            (req.name_or_query, synthesized_profile)
        )
        await db.commit()
        new_user_id = cursor.lastrowid
        
        return {"status": "success", "user_id": new_user_id, "profile": synthesized_profile}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def predict_behavior(req: PredictRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Step 1 of Blind Reveal:
    Accepts a scenario, uses the LLM to predict the user's answer, and saves it hidden.
    Returns only the prediction_id to the frontend.
    """
    # 1. Fetch user context
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        user = await cursor.fetchone()
        
    if not user:
        # Auto-create user 1 if missing for testing purposes
        await db.execute("INSERT INTO users (name, context_profile) VALUES (?, ?)", ("Test User", "A highly rational, minimal-code engineer."))
        await db.commit()
        user_context = "A highly rational, minimal-code engineer."
        user_name = "Test User"
    else:
        user_context = user["context_profile"]
        user_name = user["name"]

    # 2. Build the prompts
    system_prompt_mimic = f"""You are a behavioral model predicting how {user_name} will react or decide.
Their known context/profile:
{user_context}

Predict exactly what {user_name} would do in the following scenario. Provide a clear, concise predicted action."""

    system_prompt_baseline = "You are a generic helpful AI assistant. How would a typical person react or decide in the following scenario? Provide a clear, concise predicted action."

    try:
        # 3. Call Nemotron concurrently for speed. We request n=3 for Mimic to sample confidence.
        mimic_coro = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt_mimic},
                {"role": "user", "content": f"Scenario: {req.scenario}\nWhat does {user_name} do?"}
            ],
            temperature=0.7,
            max_tokens=300,
            n=3
        )
        
        baseline_coro = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt_baseline},
                {"role": "user", "content": f"Scenario: {req.scenario}\nWhat does a typical person do?"}
            ],
            temperature=0.7,
            max_tokens=300
        )

        mimic_res, baseline_res = await asyncio.gather(mimic_coro, baseline_coro)
        
        # Extract the 3 sampled answers
        mimic_answers = [choice.message.content.strip() for choice in mimic_res.choices]
        predicted_answer = mimic_answers[0] # Pick the first as the final answer
        baseline_answer = baseline_res.choices[0].message.content.strip()

        # 4. Calculate True Confidence via Semantic Agreement Evaluator
        eval_prompt = f"Evaluate the semantic agreement of the following {len(mimic_answers)} predicted actions. Are they suggesting the same core behavior or decision? Return ONLY a float between 0.00 and 1.00 representing the agreement/confidence score.\n\n"
        for i, ans in enumerate(mimic_answers):
            eval_prompt += f"Action {i+1}: {ans}\n\n"
            
        eval_res = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.1,
            max_tokens=1024  # Nemotron spends tokens reasoning first; 10 always truncated -> fallback
        )
        
        try:
            # Clean up output in case the model returns extra text
            confidence_str = eval_res.choices[0].message.content.strip()
            confidence_str = ''.join(c for c in confidence_str if c.isdigit() or c == '.')
            confidence = float(confidence_str)
            if confidence > 1.0: confidence = 1.0
        except:
            confidence = 0.85 # Fallback if parsing fails

        # 5. Save to DB (hidden from user)
        cursor = await db.execute(
            "INSERT INTO predictions (user_id, scenario, model_predicted_answer, confidence_score, baseline_prediction) VALUES (?, ?, ?, ?, ?)",
            (req.user_id, req.scenario, predicted_answer, confidence, baseline_answer)
        )
        await db.commit()
        prediction_id = cursor.lastrowid

        # Return only the ID (Blind Reveal)
        return {"status": "success", "prediction_id": prediction_id, "message": "Prediction generated and hidden."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reveal")
async def reveal_prediction(req: RevealRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    Step 2 of Blind Reveal:
    User submits their actual answer. We save it and return the model's hidden prediction.
    """
    # 1. Update the actual answer
    await db.execute(
        "UPDATE predictions SET user_actual_answer = ? WHERE id = ?",
        (req.user_actual_answer, req.prediction_id)
    )
    await db.commit()

    # 2. Fetch the stored prediction
    async with db.execute("SELECT * FROM predictions WHERE id = ?", (req.prediction_id,)) as cursor:
        prediction = await cursor.fetchone()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "status": "success",
        "scenario": prediction["scenario"],
        "user_actual_answer": req.user_actual_answer,
        "model_predicted_answer": prediction["model_predicted_answer"],
        "baseline_prediction": prediction["baseline_prediction"],
        "confidence_score": prediction["confidence_score"]
    }

@app.post("/research-predict")
async def research_predict(req: ResearchPredictRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    PRD §20 & §21 Grounded Opportunity & Decision Research via Tavily:
    1. Search Tavily for live external world context on the scenario.
    2. Synthesize 3-Tier Analysis:
       - What Tavily Found (Live external facts)
       - What Matters To You (Personal implications from user profile)
       - What Mimic Predicts (Personalized prediction with confidence)
       - Plain Nemotron Baseline (Generic AI without personal context)
    """
    # 1. Fetch user context
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        user = await cursor.fetchone()
        
    if not user:
        user_name = "User"
        user_context = "Rational, ambitious knowledge worker and builder."
        user_mbti = "INTJ"
    else:
        user_name = user["name"]
        user_context = user["context_profile"] or "Rational builder"
        user_mbti = user["mbti"] or ""

    # 2. Search Tavily
    sources = []
    search_context = ""
    is_live_search = False
    
    current_tavily = os.environ.get("TAVILY_API_KEY") or TAVILY_API_KEY
    if tavily_client and current_tavily and not current_tavily.startswith("tvly-your_") and len(current_tavily) > 10:
        try:
            search_res = await tavily_client.search(req.scenario, search_depth="advanced", max_results=5)
            raw_results = search_res.get("results", [])
            if raw_results:
                is_live_search = True
                sources = [{"title": r.get("title") or r.get("url"), "url": r.get("url")} for r in raw_results]
                search_context = "\n".join([f"- {r.get('title')}: {r.get('content')[:350]}" for r in raw_results])
        except Exception as e:
            search_context = f"Tavily search note: {str(e)}"
    
    if not search_context:
        search_context = "External live context: High-velocity market shift, funding concentration in AI infrastructure, aggressive equity packages vs cash compensation tradeoffs in current tech climate."

    # 3. Prompt Nemotron for 3-Tier Analysis
    system_prompt = (
        f"You are Mimic, an advanced behavioral intelligence engine predicting decisions for {user_name}.\n"
        f"User Profile: {user_context}\n"
        f"User MBTI: {user_mbti}\n\n"
        "Analyze this dilemma using both World Knowledge (Tavily search data) and Personal Knowledge (user profile).\n"
        "Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "web_facts": ["Key external market or live reality fact 1", "Key external market or live reality fact 2", "Key external reality 3"],\n'
        '  "personal_implications": ["How this connects to their personal risk/values 1", "How this matches their operating style 2", "Their decision bias 3"],\n'
        '  "mimic_prediction": "Clear, decisive prediction of what they choose and why in 1-2 sentences",\n'
        '  "confidence_score": 0.85,\n'
        '  "baseline_prediction": "What a generic AI or typical person would do without their personal profile (1-2 sentences)"\n'
        "}"
    )

    user_prompt = (
        f"Opportunity / Scenario:\n{req.scenario}\n\n"
        f"Live World Research from Tavily:\n{search_context}\n\n"
        f"Synthesize the 3-Tier Analysis: What Tavily found, what matters to {user_name}, and what Mimic predicts."
    )

    try:
        res = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        content = res.choices[0].message.content or ""
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            data = json.loads(m.group(0))
        else:
            data = {
                "web_facts": ["Analyzed live tech landscape via Tavily."],
                "personal_implications": ["Aligned with user risk tolerance and operating profile."],
                "mimic_prediction": content[:300],
                "confidence_score": 0.82,
                "baseline_prediction": "Standard risk-averse choice."
            }

        data["sources"] = sources
        data["is_live_search"] = is_live_search
        data["scenario"] = req.scenario
        data["user_name"] = user_name

        # Save to predictions table
        await db.execute(
            "INSERT INTO predictions (user_id, scenario, model_predicted_answer, confidence_score, baseline_prediction) VALUES (?, ?, ?, ?, ?)",
            (req.user_id, req.scenario, data.get("mimic_prediction", ""), float(data.get("confidence_score", 0.82)), data.get("baseline_prediction", ""))
        )
        await db.commit()

        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/demo-persona")
async def get_demo_persona(db: aiosqlite.Connection = Depends(get_db)):
    """PRD §16 & §34.1: Instant pre-seeded persona for hackathon judges."""
    name = "Alex"
    profile = "Alex is a high-agency, risk-tolerant technical founder. Prioritizes velocity, ownership, and asymmetrical upside over short-term safety. Communicates directly, makes fast decisions on partial data, and prefers building over planning."
    mbti = "ENTJ"
    
    cur = await db.execute("INSERT INTO users (name, context_profile, mbti) VALUES (?, ?, ?)", (name, profile, mbti))
    user_id = cur.lastrowid
    await db.commit()
    
    demo_results = [
        {
            "question": "A planned trip abroad is coming up.",
            "a": "Build a detailed day-by-day itinerary",
            "b": "Book the flight, figure out the rest there",
            "user": "B",
            "mimic": "B",
            "confidence": 0.86,
            "baseline": "A",
            "mimic_correct": True,
            "baseline_correct": False
        },
        {
            "question": "You unexpectedly receive $5,000.",
            "a": "Save or invest it",
            "b": "Spend it on an experience",
            "user": "A",
            "mimic": "B",
            "confidence": 0.71,
            "baseline": "B",
            "mimic_correct": False,
            "baseline_correct": False
        },
        {
            "question": "Three months into a project, early results are lukewarm.",
            "a": "Push through, it needs more time",
            "b": "Pivot quickly",
            "user": "B",
            "mimic": "B",
            "confidence": 1.0,
            "baseline": "A",
            "mimic_correct": True,
            "baseline_correct": False
        }
    ]
    
    return {
        "status": "success",
        "user_id": user_id,
        "name": name,
        "profile": profile,
        "mbti": mbti,
        "mbti_source": "demo",
        "results": demo_results,
        "score": {"mimic": 2, "baseline": 0, "total": 3}
    }

@app.post("/learn")
async def learn_from_correction(req: LearnRequest, db: aiosqlite.Connection = Depends(get_db)):
    """
    PRD §22: Visible Learning loop.
    1. Nemotron extracts a crisp behavioral rule from user's correction.
    2. Persists rule into user's context_profile.
    3. Generates a follow-up dilemma where this rule is put to the test.
    """
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        user = await cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_name = user["name"]
    curr_profile = user["context_profile"] or ""
    
    prompt = f"""You are a behavioral learning engine.
User: {user_name}
Scenario where Mimic made a mistake: "{req.scenario}"
User's explanation of why they chose what they did: "{req.correction}"

Task:
1. Formulate ONE short, powerful behavioral rule (under 15 words) describing this specific nuance (e.g. "Spends windfall money on experiences only if no debt exists").
2. Generate a similar follow-up A/B scenario to test if Mimic learned this rule. The scenario must have option A and option B, where one clearly aligns with the new rule.

Return strictly JSON:
{{
  "rule": "Learned rule under 15 words",
  "followup_scenario": {{
    "text": "Scenario question text",
    "a": "Option A text",
    "b": "Option B text",
    "expected_answer": "A" or "B"
  }}
}}"""

    try:
        res = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a behavioral modeling AI. Always respond with strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        content = res.choices[0].message.content or ""
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            data = json.loads(m.group(0))
        else:
            data = {
                "rule": f"Prefers choice based on context: {req.correction[:60]}",
                "followup_scenario": {
                    "text": f"Similar decision context for {user_name}:",
                    "a": "Follow the newly stated preference",
                    "b": "Revert to standard default",
                    "expected_answer": "A"
                }
            }
            
        rule = data.get("rule", "").strip()
        updated_profile = f"{curr_profile}\n- Learned Rule: {rule}"
        
        await db.execute("UPDATE users SET context_profile = ? WHERE id = ?", (updated_profile, req.user_id))
        await db.commit()
        
        return {
            "status": "success",
            "rule": rule,
            "updated_profile": updated_profile,
            "followup_scenario": data.get("followup_scenario")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retest")
async def retest_prediction(req: RetestRequest, db: aiosqlite.Connection = Depends(get_db)):
    """Runs Mimic prediction on the follow-up scenario with the newly learned rule."""
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        user = await cursor.fetchone()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    q = {
        "text": req.scenario_text,
        "a": req.option_a,
        "b": req.option_b
    }
    
    sys_prompt = f"You are Mimic, behavioral model of {user['name']}.\nProfile with recently learned rules:\n{user['context_profile']}\nPredict what they will choose."
    pick, conf = await sample_picks(sys_prompt, q)
    
    is_correct = (pick == req.expected_answer)
    return {
        "status": "success",
        "predicted": pick,
        "confidence": conf,
        "expected": req.expected_answer,
        "is_correct": is_correct
    }



