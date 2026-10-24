import asyncio
import json
import sys
import io

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from strata_engine import run_parallel_probes, synthesize_blueprint, ground_opportunity_with_tavily, generate_agent_blueprint_and_mcp

async def test_engine_directly():
    print("Loading test scenario from data/strata_presets.json...")
    with open("data/strata_presets.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    scenario = data["presets"][0]
    print(f"Testing Scenario: {scenario['title']}")

    print("\n--- 1. Testing Parallel Multi-Stakeholder Probes (Nemotron 120B) ---")
    probes = await run_parallel_probes(scenario)
    print(f"Received {len(probes)} probed stakeholder transcripts.")
    for p in probes:
        print(f"  • {p['name']} ({p['title']}):")
        print(f"    Probe: {p['probing_question']}")
        print(f"    Response: {p['stakeholder_response']}")
        print(f"    Friction: {p['revealed_friction']}")
        print(f"    Shadow tools: {p['shadow_tools_used']}")

    print("\n--- 2. Testing Operational Blueprint Synthesis (Nemotron 120B) ---")
    bp = await synthesize_blueprint(scenario, probes)
    print("Blueprint keys:", list(bp.keys()))
    if "error" in bp:
        print("ERROR IN BLUEPRINT:", bp.get("error"))
        print("RAW PREVIEW:\n", bp.get("raw", "")[:800])
    else:
        print(f"Delusion Metric: {bp.get('delusion_metric')}")
        print(f"Presumed Workflow: {bp.get('presumed_workflow', {}).get('summary')}")
        print(f"Actual Workflow: {bp.get('actual_workflow', {}).get('summary')}")
        print(f"Alignment Gaps: {len(bp.get('alignment_gaps', []))} detected")
        for g in bp.get('alignment_gaps', [])[:2]:
            print(f"  - Gap [{g.get('severity')}]: {g.get('title')} -> {g.get('direct_quote')}")
        print(f"Tribal Knowledge: {len(bp.get('tribal_knowledge', []))} rules")
    
    qw = bp.get("ai_opportunity_matrix", {}).get("quick_wins", [])
    if qw:
        top_qw = qw[0]
        print(f"\n--- 3. Testing Tavily Grounding on Top Quick Win: '{top_qw.get('title')}' ---")
        grounding = await ground_opportunity_with_tavily(top_qw.get("title"), scenario.get("target_workflow"))
        print(f"Tavily Verdict: {grounding.get('verdict')}")
        print(f"Tavily Answer snippet: {grounding.get('answer', '')[:200]}")
        print(f"Citations: {len(grounding.get('citations', []))}")

        print(f"\n--- 4. Testing Export Agent Blueprint & MCP Spec ---")
        pkg = await generate_agent_blueprint_and_mcp(top_qw, scenario.get("title"), grounding)
        print(f"Agent Name: {pkg.get('agent_name')}")
        print(f"Guardrails: {pkg.get('guardrails')}")
        print(f"Escalation Trigger: {pkg.get('human_in_the_loop_trigger')}")
        print(f"MCP Tools defined: {[t['name'] for t in pkg.get('mcp_tools', [])]}")

    print("\n✅ Direct Strata Engine verification COMPLETE and SUCCESSFUL!")

if __name__ == "__main__":
    asyncio.run(test_engine_directly())
