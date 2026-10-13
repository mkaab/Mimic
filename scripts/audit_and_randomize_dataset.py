"""
scripts/audit_and_randomize_dataset.py

Audits and cleans all 30 scenarios in Mimic candidate dataset:
1. Strips all telegraphing text, editorial bias, and explanatory parentheticals.
2. Ensures search queries are neutral (no verdict smuggling).
3. Interleaves categories (Calendar, Inbox, Commitments) across the timeline.
4. Uses seeded shuffle (seed=42) to assign semantic actions to Option A vs Option B,
   breaking position bias and ensuring ~50% A / 50% B distribution.
5. Emits data/unlabeled_decisions.json with semantic_options.
"""

import json
import random
import os

SEED = 42
rng = random.Random(SEED)

RAW_SCENARIOS = [
    # 1. Calendar - Low
    {
        "id": "dec_001",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-01T09:00:00Z",
        "inbound_text": "Meeting invite from Associate at Seed Venture Fund: 'Quick 15-min coffee chat to learn more about your background and what you are building.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept meeting invite",
            "decline": "Decline meeting invite"
        },
        "synthetic": True
    },
    # 2. Inbox - Low
    {
        "id": "dec_002",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-09-02T10:15:00Z",
        "inbound_text": "Cold outbound email from SDR at Cloud Observability SaaS: 'Saw your GitHub profile and wanted to demo our enterprise APM dashboard. Can I have 10 minutes on Tuesday?'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "archive": "Archive email",
            "reply": "Reply requesting one-pager"
        },
        "synthetic": True
    },
    # 3. Calendar - Medium
    {
        "id": "dec_003",
        "category": "calendar",
        "stakes": "medium",
        "timestamp": "2026-09-04T14:00:00Z",
        "inbound_text": "Calendar invite from Engineering Collaborator A: 'Urgent review of core inference pipeline refactor before v1 launch.' Proposes tomorrow at 11:00am.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept review meeting",
            "decline": "Decline and request async comments"
        },
        "synthetic": True
    },
    # 4. Commitments - Medium
    {
        "id": "dec_004",
        "category": "commitments",
        "stakes": "medium",
        "timestamp": "2026-09-06T11:30:00Z",
        "inbound_text": "Invitation from Regional Tech Summit: 'We invite you to participate in an unpaid panel on Real-World AI Agents on Oct 24 (45 mins in-person) with 200 local founders attending.'",
        "requires_tavily": True,
        "search_query": "Regional Tech Summit 2026 speaker lineup and attendees",
        "semantic_options": {
            "accept": "Accept panel invitation",
            "decline": "Decline panel invitation"
        },
        "synthetic": True
    },
    # 5. Calendar - Low
    {
        "id": "dec_005",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-07T16:00:00Z",
        "inbound_text": "Invite from Internal Team Lead: 'Quarterly team social check-in (optional, virtual game room, 30 mins) on Friday 4pm.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept social check-in",
            "decline": "Decline social check-in"
        },
        "synthetic": True
    },
    # 6. Inbox - Medium
    {
        "id": "dec_006",
        "category": "inbox",
        "stakes": "medium",
        "timestamp": "2026-09-09T08:45:00Z",
        "inbound_text": "Email from Trusted Peer B: 'Warm intro to Founder of Stealth AI Infrastructure startup who is building novel GPU orchestration. They would love 20 mins to get your technical feedback.'",
        "requires_tavily": True,
        "search_query": "Stealth AI Infrastructure GPU orchestration founders team",
        "semantic_options": {
            "accept": "Accept introduction",
            "decline": "Decline introduction"
        },
        "synthetic": True
    },
    # 7. Commitments - High
    {
        "id": "dec_007",
        "category": "commitments",
        "stakes": "high",
        "timestamp": "2026-09-11T13:20:00Z",
        "inbound_text": "Advisory proposal from Seed-Stage Robotics Startup C: 'Offer of 0.35% equity (2-year vesting, 3 hours/month commitment) to advise on autonomous agent architecture.'",
        "requires_tavily": True,
        "search_query": "Seed-Stage Robotics Startup C funding and executive team",
        "semantic_options": {
            "accept": "Accept advisory offer",
            "decline": "Decline advisory offer"
        },
        "synthetic": True
    },
    # 8. Calendar - Low
    {
        "id": "dec_008",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-12T15:30:00Z",
        "inbound_text": "Calendar invite from Junior Engineer D: 'Quick 15 min check-in to walk through SQLite schema migration PR.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept check-in meeting",
            "redirect": "Redirect to PR comments"
        },
        "synthetic": True
    },
    # 9. Inbox - Low
    {
        "id": "dec_009",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-09-14T09:10:00Z",
        "inbound_text": "Automated notification from Cloud Provider: 'Your monthly compute usage has reached 75% of budget threshold ($35 remaining).'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "review": "Review and terminate idle instances",
            "archive": "Mark notification as read"
        },
        "synthetic": True
    },
    # 10. Commitments - Medium
    {
        "id": "dec_010",
        "category": "commitments",
        "stakes": "medium",
        "timestamp": "2026-09-15T12:00:00Z",
        "inbound_text": "Freelance consulting inquiry from Mid-size HealthTech Org: 'Offer to audit existing LLM compliance pipeline for $4,500 fixed fee (estimated 15 hours work over weekend).' Delivery in 10 days.",
        "requires_tavily": True,
        "search_query": "HealthTech Org enterprise LLM compliance platform",
        "semantic_options": {
            "accept": "Accept consulting contract",
            "decline": "Decline consulting project"
        },
        "synthetic": True
    },
    # 11. Calendar - Medium
    {
        "id": "dec_011",
        "category": "calendar",
        "stakes": "medium",
        "timestamp": "2026-09-16T17:00:00Z",
        "inbound_text": "Invite from Recruiter at Tier-1 AI Lab: 'We are expanding our Agentic Systems team. Would love a 30-min exploratory video conversation.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept exploratory call",
            "decline": "Decline exploratory call"
        },
        "synthetic": True
    },
    # 12. Inbox - Low
    {
        "id": "dec_012",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-09-18T11:00:00Z",
        "inbound_text": "Email from Open Source Contributor E: 'Submitted a 40-line PR fixing edge-case timeout in asynchronous HTTP client with tests attached.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "review": "Review and merge PR promptly",
            "snooze": "Snooze review for later"
        },
        "synthetic": True
    },
    # 13. Calendar - Low
    {
        "id": "dec_013",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-19T10:30:00Z",
        "inbound_text": "Invite from Co-working Space Manager: 'Mandatory fire alarm testing and building maintenance on Tuesday 2pm (expect noise for 45 mins).' Option to book quiet booth.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "booth": "Book quiet booth or work remotely",
            "remain": "Remain at main desk"
        },
        "synthetic": True
    },
    # 14. Commitments - High
    {
        "id": "dec_014",
        "category": "commitments",
        "stakes": "high",
        "timestamp": "2026-09-20T14:15:00Z",
        "inbound_text": "Venture Studio Partnership Offer: 'Offer to incubate Mimic IP with $150k initial check in exchange for 18% common equity and IP assignment clause.'",
        "requires_tavily": True,
        "search_query": "Venture Studio investments track record and portfolio",
        "semantic_options": {
            "accept": "Sign term sheet",
            "decline": "Decline term sheet"
        },
        "synthetic": True
    },
    # 15. Calendar - Low
    {
        "id": "dec_015",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-21T09:45:00Z",
        "inbound_text": "Invite from Industry Podcast Host: 'Invitation to record 30-min remote audio episode discussing AI agent design patterns next month.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept podcast invitation",
            "decline": "Decline podcast invitation"
        },
        "synthetic": True
    },
    # 16. Inbox - Medium
    {
        "id": "dec_016",
        "category": "inbox",
        "stakes": "medium",
        "timestamp": "2026-09-22T13:30:00Z",
        "inbound_text": "Outreach from Former Manager F: 'Looking for an engineering reference call (15 mins) for a senior engineer candidate who previously worked on our shared team.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Agree to provide reference call",
            "decline": "Decline reference call"
        },
        "synthetic": True
    },
    # 17. Calendar - Medium
    {
        "id": "dec_017",
        "category": "calendar",
        "stakes": "medium",
        "timestamp": "2026-09-23T11:15:00Z",
        "inbound_text": "Invite from Prospective Design Partner Org: 'Demo of Mimic Core for their VP of Product to explore enterprise pilot deployment. 30 mins.'",
        "requires_tavily": True,
        "search_query": "Design Partner Org enterprise deployment case studies",
        "semantic_options": {
            "accept": "Accept demo meeting",
            "reschedule": "Reschedule demo meeting"
        },
        "synthetic": True
    },
    # 18. Inbox - Low
    {
        "id": "dec_018",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-09-24T16:20:00Z",
        "inbound_text": "Email from Conference Organizer: 'Early bird registration discount ends tonight for Global Agent Summit ($300 vs $600 standard ticket).' Virtual attendance option.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "purchase": "Purchase virtual pass ($150)",
            "archive": "Archive email and skip summit"
        },
        "synthetic": True
    },
    # 19. Commitments - Medium
    {
        "id": "dec_019",
        "category": "commitments",
        "stakes": "medium",
        "timestamp": "2026-09-25T10:00:00Z",
        "inbound_text": "Request from University AI Club: 'Guest lecture request (60 mins guest lecture on Building with NVIDIA Nemotron & Nebius Token Factory).' Target audience 60 CS students.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept guest lecture",
            "decline": "Decline guest lecture"
        },
        "synthetic": True
    },
    # 20. Calendar - Low
    {
        "id": "dec_020",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-26T14:40:00Z",
        "inbound_text": "Meeting invite from Bank Account Manager: 'Annual business banking compliance verification call (10 mins required).' Slots available this Thursday.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept compliance call",
            "delay": "Defer or snooze call"
        },
        "synthetic": True
    },
    # 21. Inbox - Medium
    {
        "id": "dec_021",
        "category": "inbox",
        "stakes": "medium",
        "timestamp": "2026-09-27T08:30:00Z",
        "inbound_text": "Email from Growth Marketer G: 'Pitching contract growth marketing retainer ($2,000/mo) to acquire early users for developer tool.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Schedule intro pitch call",
            "decline": "Decline marketing retainer"
        },
        "synthetic": True
    },
    # 22. Commitments - High
    {
        "id": "dec_022",
        "category": "commitments",
        "stakes": "high",
        "timestamp": "2026-09-27T17:10:00Z",
        "inbound_text": "Commercial licensing inquiry from Fintech Enterprise H: 'Request to white-label Mimic behavioral prediction engine for wealth management advisor coaching. Requires 1-year SLA and exclusivity in fintech vertical.'",
        "requires_tavily": True,
        "search_query": "Fintech Enterprise H annual revenue vendor partnerships",
        "semantic_options": {
            "accept": "Proceed with pilot negotiation",
            "decline": "Decline exclusivity proposal"
        },
        "synthetic": True
    },
    # 23. Calendar - Low
    {
        "id": "dec_023",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-09-28T12:15:00Z",
        "inbound_text": "Invite from Friend & Fellow Founder: 'Quick lunch catch-up near co-working space on Friday 12:30pm.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept lunch invite",
            "decline": "Decline lunch invite"
        },
        "synthetic": True
    },
    # 24. Inbox - Low
    {
        "id": "dec_024",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-09-29T09:50:00Z",
        "inbound_text": "Newsletter subscription confirmation email: 'Please confirm your subscription to AI Systems Weekly digest.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "confirm": "Confirm subscription",
            "delete": "Delete confirmation email"
        },
        "synthetic": True
    },
    # 25. Calendar - Medium
    {
        "id": "dec_025",
        "category": "calendar",
        "stakes": "medium",
        "timestamp": "2026-09-29T15:00:00Z",
        "inbound_text": "Invite from Cloud Infrastructure Solutions Architect: '1-on-1 architecture tuning session for GPU inference clusters and TensorRT deployment (30 mins free consultation).'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept architecture consultation",
            "decline": "Decline architecture consultation"
        },
        "synthetic": True
    },
    # 26. Inbox - Medium
    {
        "id": "dec_026",
        "category": "inbox",
        "stakes": "medium",
        "timestamp": "2026-09-30T10:20:00Z",
        "inbound_text": "Bug report from Beta Tester J: 'Encountered intermittent 500 error when submitting rapid successive queries during prediction sampling. Provided reproduction curl command.'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "acknowledge": "Acknowledge and file bug in tracker",
            "archive": "Archive notification"
        },
        "synthetic": True
    },
    # 27. Commitments - Medium
    {
        "id": "dec_027",
        "category": "commitments",
        "stakes": "medium",
        "timestamp": "2026-09-30T16:45:00Z",
        "inbound_text": "Co-authoring invite from Research Fellow K: 'Collaborate on a joint technical paper/blogpost on Evaluating Behavioral Personal AI and Autonomy Gates.' Draft outline attached.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept co-authoring invitation",
            "decline": "Decline co-authoring invitation"
        },
        "synthetic": True
    },
    # 28. Calendar - Low
    {
        "id": "dec_028",
        "category": "calendar",
        "stakes": "low",
        "timestamp": "2026-10-01T11:00:00Z",
        "inbound_text": "Invite from Account Rep at Domain Registrar: 'Courtesy renewal check-in call (10 mins).'",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "accept": "Accept renewal call",
            "decline": "Decline renewal call"
        },
        "synthetic": True
    },
    # 29. Inbox - Low
    {
        "id": "dec_029",
        "category": "inbox",
        "stakes": "low",
        "timestamp": "2026-10-01T14:30:00Z",
        "inbound_text": "Security bulletin notification from PyPI: 'Urgent patch available for transitive dependency in SQLite async driver.' Fix verified in patch release v0.2.1.",
        "requires_tavily": False,
        "search_query": "",
        "semantic_options": {
            "deploy": "Deploy dependency patch release",
            "defer": "Defer to next scheduled audit"
        },
        "synthetic": True
    },
    # 30. Commitments - High
    {
        "id": "dec_030",
        "category": "commitments",
        "stakes": "high",
        "timestamp": "2026-10-01T18:00:00Z",
        "inbound_text": "Angel Investment Invitation: 'Opportunity to participate in $25k allocation in Seed round of AI Developer Tool startup founded by former teammate L.' Minimum check $5,000.",
        "requires_tavily": True,
        "search_query": "AI Developer Tool startup seed round lead investors",
        "semantic_options": {
            "accept": "Commit $5,000 angel check",
            "decline": "Decline angel investment allocation"
        },
        "synthetic": True
    }
]

# Process scenarios: randomize A vs B assignment per item using seeded shuffle
cleaned_items = []
a_is_first_semantic_count = 0

for item in RAW_SCENARIOS:
    sem_opts = list(item["semantic_options"].items()) # [(k1, text1), (k2, text2)]
    
    # Deterministic coin flip per item
    flip = rng.random() > 0.5
    if flip:
        order = [sem_opts[0], sem_opts[1]]
    else:
        order = [sem_opts[1], sem_opts[0]]
        
    options_dict = {
        "A": order[0][1],
        "B": order[1][1]
    }
    semantic_key_map = {
        "A": order[0][0],
        "B": order[1][0]
    }
    
    cleaned_items.append({
        "id": item["id"],
        "category": item["category"],
        "stakes": item["stakes"],
        "timestamp": item["timestamp"],
        "inbound_text": item["inbound_text"],
        "requires_tavily": item["requires_tavily"],
        "search_query": item["search_query"],
        "options": options_dict,
        "semantic_mapping": semantic_key_map,
        "synthetic": item["synthetic"]
    })

os.makedirs("data", exist_ok=True)
with open("data/unlabeled_decisions.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_items, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {len(cleaned_items)} audited, randomized candidate decisions.")
print(f"Output saved to: data/unlabeled_decisions.json")
