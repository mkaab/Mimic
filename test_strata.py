import asyncio
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_full_flow():
    print("=== Testing Strata Discovery Engine Endpoints ===")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Health check
        res = await client.get("/")
        print("1. Health Check:", res.status_code, res.json())
        assert res.status_code == 200

        # 2. Get Presets
        res = await client.get("/api/strata/presets")
        print("2. Presets:", res.status_code)
        assert res.status_code == 200
        presets = res.json()["presets"]
        print(f"   Found {len(presets)} presets. Testing with: {presets[0]['title']}")
        test_scenario = presets[0]

        # 3. Probe Stakeholders (Parallel Nemotron 120B probe)
        print("3. Probing stakeholders in parallel with Nemotron 120B...")
        res = await client.post("/api/strata/probe", json={"scenario": test_scenario})
        assert res.status_code == 200
        probes = res.json()["probes"]
        print(f"   Probed {len(probes)} stakeholders successfully.")
        for p in probes:
            print(f"   - [{p['name']}]: Probe -> \"{p['probing_question'][:70]}...\"")
            print(f"     Friction revealed -> {p['revealed_friction']}")
            print(f"     Shadow tools -> {p['shadow_tools_used']}")

        # 4. Synthesize Operational Blueprint
        print("\n4. Synthesizing Dual-DAG & Operational Blueprint...")
        res = await client.post("/api/strata/synthesize", json={
            "scenario": test_scenario,
            "transcripts": probes
        })
        assert res.status_code == 200
        bp = res.json()["blueprint"]
        print(f"   Delusion Metric: {bp.get('delusion_metric')}")
        print(f"   Presumed nodes: {len(bp.get('presumed_workflow', {}).get('nodes', []))}")
        print(f"   Actual nodes: {len(bp.get('actual_workflow', {}).get('nodes', []))}")
        print(f"   Alignment Gaps detected: {len(bp.get('alignment_gaps', []))}")
        print(f"   Tribal Knowledge rules: {len(bp.get('tribal_knowledge', []))}")
        qw = bp.get("ai_opportunity_matrix", {}).get("quick_wins", [])
        print(f"   Quick Wins count: {len(qw)}")
        if qw:
            print(f"   Top Quick Win: {qw[0].get('title')} (ROI: {qw[0].get('roi_hours_saved_weekly')} hrs/wk)")

        # 5. Tavily Grounding
        if qw:
            top_win = qw[0]
            print(f"\n5. Grounding Quick Win '{top_win['title']}' with Tavily...")
            res = await client.post("/api/strata/ground", json={
                "opportunity_title": top_win["title"],
                "target_workflow": test_scenario["target_workflow"]
            })
            assert res.status_code == 200
            grounding = res.json()["grounding"]
            print(f"   Tavily Verdict: {grounding.get('verdict')}")
            print(f"   Citations found: {len(grounding.get('citations', []))}")

            # 6. Export Agent Blueprint & MCP
            print(f"\n6. Generating Agent Blueprint & MCP Configuration...")
            res = await client.post("/api/strata/export-agent", json={
                "opportunity": top_win,
                "scenario_title": test_scenario["title"],
                "grounding": grounding
            })
            assert res.status_code == 200
            pkg = res.json()["package"]
            print(f"   Agent Name: {pkg.get('agent_name')}")
            print(f"   Guardrails: {len(pkg.get('guardrails', []))}")
            print(f"   MCP Tools: {[t['name'] for t in pkg.get('mcp_tools', [])]}")
            print(f"   Human Escalation Trigger: {pkg.get('human_in_the_loop_trigger')}")

    print("\n✅ All Strata Backend Foundation tests PASSED!")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
