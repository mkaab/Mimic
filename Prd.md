# Mimic
### Product Requirements Document — v0.6

> **v0.6 changes (hackathon review):** blind reveal (user commits before seeing the prediction) · baseline comparison vs plain Nemotron · confidence from sampling agreement instead of self-reported numbers · Tavily bootstraps the model from the user's public footprint (opt-in) · sharper impact framing (agents need a model of you to act for you) · demo reordered to open with the prediction moment · SQLite instead of Postgres for the hackathon.

> **An AI that learns how you think, what you care about, and what you would do — then predicts you and helps you act.**

---

## 1. Product Thesis

Most AI assistants are becoming better at **remembering users**.

Mimic asks a different question:

> **What if AI could learn to predict you?**

Mimic builds a continuously improving model of an individual from their conversations, decisions, preferences, goals, writing, and feedback.

It then uses that model to answer questions such as:

- “What would I choose?”
- “Would I take this opportunity?”
- “How would I respond to this?”
- “What would I prioritize?”
- “Would I actually do this?”
- “What should I consider before deciding?”

The core loop is:

**Capture → Remember → Understand → Predict → Reveal → Learn**

The product should make the user feel:

> **“Holy shit. It actually predicted me.”**

That moment is the central product experience.

---

# 2. Problem

Current AI assistants can know a lot about a user without truly understanding them.

They can remember:

- where someone works
- what projects they are building
- previous conversations
- preferences
- people they know
- information they have shared

But remembering information is not the same as understanding the person behind it.

Two people can have exactly the same information available to them and make completely different decisions.

The difference comes from:

- personality
- values
- goals
- risk tolerance
- decision style
- priorities
- communication style
- relationships
- past behavior
- current context

Mimic attempts to model these factors and use them to predict the user's behavior.

### Why this matters now

AI agents are starting to act on users' behalf: triaging email, booking, buying, replying, filtering opportunities.

An agent that has your data but no model of *you* has to either:

- ask you about everything (no time saved), or
- guess (wrong in ways you'll find out about later).

The missing layer is a **testable model of the user's judgment**: something an agent can ask *"what would they want here?"* before acting, plus a track record showing how often that answer is right.

Mimic is that layer. Predicting your own decisions back to you is how Mimic **proves** it understands you before anyone trusts it to act for you.

---

# 3. The Core Insight

### Memory is not the moat.

Memory tells an AI:

> **What happened.**

Mimic tries to learn:

> **What that means about you.**

And ultimately:

> **What you would do next.**

The architecture therefore progresses from:

**Memory → Context → Personal Model → Prediction → Feedback**

rather than stopping at:

**Memory → Retrieval → Answer**

---

# 4. Product Differentiation

| Generic AI | Memory AI | Mimic |
|---|---|---|
| Answers questions | Remembers information | Models the person |
| Performs tasks | Retrieves context | Predicts behavior |
| Knows facts | Knows history | Learns patterns |
| Responds to requests | Personalizes responses | Anticipates decisions |
| Static interaction | Better context | Continuous behavioral learning |

The key differentiator is not:

> “Mimic remembers more.”

It is:

> **“Mimic gets better at predicting you.”**

---

# 5. Target User

The initial target user is a knowledge worker, founder, builder, researcher, or ambitious individual who:

- makes frequent decisions
- researches opportunities
- communicates with many people
- has multiple goals/projects
- values personalized advice
- wants an AI that increasingly understands them

The initial product should optimize for users who are comfortable giving Mimic enough information to build a useful model.

---

# 6. MVP Goal

The MVP does **not** attempt to build a complete autonomous personal assistant.

Its single most important job is to prove:

> **Given enough information about a person, Mimic can make increasingly accurate predictions about what that person would think, choose, say, or do.**

### MVP success criteria

A new user should be able to:

1. Tell Mimic what they are trying to accomplish.
2. Answer a small number of behavioral questions.
3. Generate an initial personal model.
4. Ask Mimic a real question.
5. Have Mimic research the relevant external information.
6. Receive a personalized recommendation.
7. Test Mimic on a prediction scenario.
8. Reveal what they actually would do.
9. See whether Mimic was correct.
10. Correct Mimic when it is wrong.
11. Test it again.
12. See evidence that Mimic is learning.

---

# 7. The Killer Feature: Test Your Mimic

The primary demonstration should be a prediction game.

### User sees:

> ## What would you do?

**You receive two opportunities:**

**A.** Spend the next 3 months building a product around an emerging market.

**B.** Take a stable consulting opportunity that pays immediately.

### User locks in their answer first (hidden)

The user picks their answer **before** seeing Mimic's prediction. The answer is stored and hidden.

This matters: if the user sees the prediction first, the prediction anchors the answer and the result means nothing. Blind commit makes every "Correct" honest.

### Mimic predicts:

> **I think you'd choose A.**
>
> **78% confidence**

### Why?

- You tend to prioritize long-term upside over immediate certainty.
- You have previously chosen projects with higher uncertainty.
- Your current goal is building rather than maximizing short-term income.
- You usually research opportunities before committing.

### Both revealed side by side:

> **A**

### Result:

> **Correct.**

**Mimic accuracy: 8 / 10** · *Plain Nemotron (no personal model): 5 / 10*

The user can then provide additional context:

> “I would choose A, but only if I could validate the market first.”

Mimic records the correction.

The next prediction incorporates that information.

---

# 8. Why Prediction Matters

A personality dashboard is interesting.

A prediction is useful.

A correct prediction is emotionally powerful.

Therefore:

### Personality should be the foundation.

### Prediction should be the product.

### Learning should be the moat.

The personality profile exists primarily to improve Mimic's predictions.

---

# 9. Personal Model

Mimic maintains a structured representation of the user.

```text
Mimic
│
├── Personality
│   ├── Curiosity
│   ├── Drive
│   ├── Social
│   ├── Cooperation
│   ├── Sensitivity
│   └── Principles
│
├── Operating Style
│   ├── Initiative
│   ├── Decisiveness
│   └── Adaptability
│
├── Goals
│
├── Values
│
├── Preferences
│
├── Decision History
│
├── Communication Style
│
├── Relationships
│
├── Projects
│
└── Behavioral Observations
```

This model should evolve over time.

---

# 10. Personality Model

Mimic's personality framework is **informed by HEXACO**, a well-established six-dimensional personality framework.

The product should not claim to produce clinically or scientifically validated personality scores.

Instead:

> **Mimic creates a HEXACO-informed behavioral model based on observed and reported evidence.**

The six user-facing dimensions are:

### 1. Curiosity
**HEXACO: Openness to Experience**

Represents tendencies toward:

- exploration
- novelty
- intellectual curiosity
- creativity
- abstract thinking

### 2. Drive
**HEXACO: Conscientiousness**

Represents tendencies toward:

- organization
- diligence
- planning
- persistence
- goal pursuit
- prudence

### 3. Social
**HEXACO: Extraversion**

Represents tendencies toward:

- sociability
- confidence
- social energy
- assertiveness
- engagement with others

### 4. Cooperation
**HEXACO: Agreeableness**

Represents tendencies toward:

- patience
- flexibility
- forgiveness
- conflict management
- interpersonal cooperation

### 5. Sensitivity
**HEXACO: Emotionality**

Represents tendencies related to:

- emotional sensitivity
- anxiety
- fearfulness
- dependence
- sentimentality

This should **not** be framed as “emotionally strong vs weak.”

### 6. Principles
**HEXACO: Honesty–Humility**

Represents tendencies toward:

- sincerity
- fairness
- modesty
- avoiding exploitation
- resistance to status seeking
- greed avoidance

---

# 11. Operating Style

These are product-level behavioral constructs, not HEXACO dimensions.

### Initiative
**Reactive ↔ Proactive**

Does the user tend to wait for circumstances or create the next step?

### Decisiveness
**Deliberate ↔ Decisive**

Does the user prefer extensive analysis or move quickly once enough information is available?

### Adaptability
**Persistent ↔ Adaptive**

Does the user tend to stay committed to an initial path or change course when new information appears?

These dimensions are particularly important because they connect personality to action.

---

# 12. Agency

Agency is a key bridge between:

**Personality → Behavior → Action**

For example:

### High-agency behavior

> Research → identify opportunity → contact someone → create next step.

### Lower-agency behavior

> Research → save information → wait → gather more certainty.

Neither is inherently better.

The goal is to model what the individual is likely to do.

Agency should therefore influence prediction rather than exist merely as a profile statistic.

---

# 13. Personality Is Not Prediction

Mimic should never make a prediction using personality alone.

The prediction engine combines:

```text
Personality
+
Operating Style
+
Current Goals
+
Values
+
Past Decisions
+
Relationships
+
Communication Patterns
+
Current Context
+
External Information
+
Current Situation
↓
Predicted Behavior
```

For example:

> “You score high on Drive, therefore you will choose A”

is weak.

Instead:

> “You're currently trying to launch a product, you've previously prioritized long-term ownership over short-term income, and you tend to act once you've reached moderate certainty. Given this opportunity, I think you'd choose A.”

That is the Mimic experience.

---

# 14. Evidence Hierarchy

Not all information should influence the model equally.

Mimic should prioritize evidence approximately as follows:

1. **Repeated observed behavior**
2. **Repeated decisions**
3. **User corrections**
4. **Consistent patterns across multiple narratives**
5. **Single narrative**
6. **Self-reported preference**
7. **Single inferred observation**

This prevents one unusual conversation from radically changing the user's model.

---

# 15. Model Stability

Personality should change slowly.

Context and goals can change quickly.

For example:

```text
Personality
slow-moving

Operating style
medium-moving

Goals
fast-moving

Context
fast-moving

Prediction
changes immediately
```

A single event should not suddenly change someone's personality.

However, a new goal can immediately change what Mimic predicts they will do.

---

# 16. Onboarding

Target duration:

### 2–3 minutes with Tavily bootstrap

5–8 minutes without it.

Maximum:

### 10 minutes

A **pre-seeded demo persona** must also exist so judges and first-time visitors can try the prediction loop instantly without onboarding.

The onboarding should feel like a conversation rather than a personality test.

---

## Step 0 — Bootstrap from public footprint (optional, opt-in)

The user can paste links or a name + context (personal site, blog, GitHub, talks, LinkedIn summary).

Mimic uses **Tavily** to search and extract public content, then infers:

- current projects and goals
- stated values and interests
- past decisions visible in public (job moves, projects started/abandoned)
- communication style from their writing

Every inferred item is shown to the user with its source and must be **confirmed, edited or rejected** before it enters the model. Bootstrapped evidence starts at low confidence (level 7 in the Evidence Hierarchy) until confirmed.

This solves the cold-start problem and lets onboarding skip questions Mimic can already answer.

---

## Step 1 — Aspiration

Ask:

> **What are you trying to make happen right now?**

Examples:

- Build a company
- Change careers
- Find investors
- Get healthier
- Learn something difficult
- Make more money
- Build a creative project

This establishes the user's current objective.

---

## Step 2 — Behavioral Scenarios

Ask 6–8 scenario-based questions (fewer if Step 0 already covered them).

**2–3 of these are held out:** the user answers them, but they are not used to build the model. They become the first blind tests and the basis for the baseline comparison (Section 23).

Avoid:

> “Are you organized?”

Prefer:

> “You have three important things to finish today and only enough time for two. What do you do?”

Avoid:

> “Are you adventurous?”

Prefer:

> “You have an opportunity with a large upside but a meaningful chance of failure. What would make you take it?”

Scenario questions provide behavioral evidence rather than simple self-labels.

---

## Step 3 — Narrative Questions

Ask 2–3 open-ended questions:

> “Tell me about a decision you're proud of.”

> “Tell me about a decision you got wrong.”

> “When you're stuck, what do you usually do?”

Narrative answers provide richer behavioral signals.

---

## Step 4 — Generate Initial Mimic

Mimic generates:

- six personality estimates
- three operating-style estimates
- goals
- values
- decision tendencies
- communication tendencies
- initial confidence
- supporting evidence

The profile should explicitly say:

> **This is Mimic's current estimate — not a fixed description of you.**

---

# 17. Profile Experience

## YOUR MIMIC

### How you tend to be

**Curiosity** 82  
**Drive** 74  
**Social** 41  
**Cooperation** 68  
**Sensitivity** 61  
**Principles** 89

### How you tend to operate

**Initiative** 71  
**Decisiveness** 64  
**Adaptability** 78

### Model confidence

**Medium**

Based on:

- 8 behavioral answers
- 3 narratives
- 5 inferred patterns

The profile should be visually simple.

One radar chart can represent the six personality dimensions.

Three compact bars can represent operating style.

The profile is supporting infrastructure for prediction — not the primary experience.

---

# 18. Prediction Engine

Every prediction should produce:

### Prediction

> **I think you'd choose B.**

### Confidence

> **78%**

Confidence is **not** a number the model writes down; models are bad at stating their own confidence. Instead:

- run the prediction N times (e.g. 7–10) on Nebius Token Factory with temperature > 0
- confidence = share of runs that agree with the majority answer
- (optional, if Token Factory exposes logprobs for the chosen model) use token probability of the option label instead

This makes confidence measurable, and therefore calibratable (Section 24).

### Evidence

2–4 concise reasons.

### Relevant context

Why the current situation changes the prediction.

### Alternative

What could cause Mimic to be wrong.

Example:

> **I think you'd decline the meeting.**
>
> **74% confidence**
>
> Why:
> - You usually avoid meetings without a clear objective.
> - You're currently prioritizing deep work.
> - You prefer getting context asynchronously first.
>
> I could be wrong if:
> - The person has unusually high strategic value to you.

This is far more useful than exposing hidden reasoning or chain-of-thought.

---

# 19. Prediction Categories

MVP should focus primarily on **decision prediction**.

Future prediction types:

### Decision
> Which option would you choose?

### Preference
> Which product would you prefer?

### Priority
> Which task would you do first?

### Communication
> How would you respond?

### Opportunity
> Would you pursue this?

### Action
> Would you actually do this?

The product can eventually predict increasingly complex behavior.

---

# 20. Research + Tavily

Mimic should not only predict in a vacuum.

When a user asks:

> “Should I pursue this opportunity?”

Mimic can research the external world using Tavily.

The experience should separate:

### What I found

External facts and research.

### What matters to you

Personalized interpretation based on the user's model.

### What I think

Mimic's recommendation or prediction.

This creates a powerful combination:

> **World knowledge + personal knowledge**

rather than generic search.

---

# 21. Example Research Experience

User:

> “Should I pursue this startup idea?”

Mimic:

### What I found

- Market growing rapidly.
- Competition increasing.
- Several major players entering.
- Customer acquisition appears difficult.

### What matters to you

- You value ownership.
- You tolerate moderate uncertainty.
- You prefer markets where you can move quickly.
- You're currently optimizing for building rather than employment.

### What I think

> **I think you'd pursue it — but only after validating demand with 10–20 customers.**
>
> **81% confidence**

This demonstrates personalization rather than simple retrieval.

---

# 22. Feedback Loop

Every prediction creates training data.

```text
Mimic predicts
↓
User reveals actual answer
↓
Correct / incorrect
↓
User explains why
↓
Evidence stored
↓
Personal model updated
↓
Future prediction improves
```

Feedback options:

### Correct

> “Yep.”

### Partially correct

> “Mostly, but…”

### Wrong

> “No, because…”

The user should be able to correct Mimic naturally.

### Learning must be visible

When the user corrects Mimic, the UI shows exactly what changed:

> **New rule learned:** *"Takes high-upside opportunities — but only after validating demand first."*
> Source: your correction on "Build vs Consulting" · confidence: medium

Mimic then offers a **similar scenario** where the new rule should change the outcome. If the prediction flips and matches the user, that is the proof of learning.

Implementation note: in the MVP, "learning" means extracted rules and evidence are stored and pulled into future prediction prompts. That is fine, but it must be shown, not just claimed.

---

# 23. Accuracy

Mimic should track:

### Prediction Accuracy

```text
Correct predictions
-------------------
Total predictions
```

Example:

> **Mimic accuracy: 8 / 10**

It should also track improvement over time:

```text
Initial accuracy: 60%

After 10 predictions: 72%

After 25 predictions: 81%
```

This turns learning into a visible product experience.

### Baseline comparison (required)

Accuracy alone means nothing without a reference point. Mimic always reports accuracy against a baseline:

| Predictor | Accuracy on held-out scenarios |
|---|---|
| Plain Nemotron (scenario only, no personal model) | e.g. 51% |
| Mimic (personal model + memory) | e.g. 76% |
| Mimic after corrections | e.g. 82% |

The baseline uses the same model, same scenarios, same prompt structure, just without personal context. The gap between rows is the value of the personal model.

The team should also run this internally across several real testers before submission so the Devpost write-up can quote real numbers, not illustrative ones.

---

# 24. Confidence Calibration

Accuracy alone is insufficient.

Mimic should eventually measure whether its confidence corresponds to reality.

Example:

If Mimic says:

> 80% confidence

it should be correct roughly 80% of the time over enough predictions.

This makes confidence meaningful rather than decorative.

MVP implements simple calibration:

- confidence comes from sampling agreement (Section 18)
- predictions are grouped into confidence buckets (e.g. 50–65%, 65–80%, 80–100%)
- a small chart shows stated confidence vs actual hit rate per bucket

Even with few data points, showing this chart signals that confidence means something.

---

# 25. Memory Architecture

Mimic's memory should be structured rather than being a giant conversation history.

```text
Memory
├── Facts
├── People
├── Relationships
├── Goals
├── Projects
├── Decisions
├── Preferences
├── Communication Patterns
├── Behavioral Observations
└── Predictions
```

Each memory should include:

- content
- type
- source
- context
- confidence
- observed_at
- last_confirmed
- related entities

The system should preserve temporal context.

For example:

> “I'm raising money”

is different from:

> “I was raising money six months ago.”

---

# 26. Memory vs Personal Model

These should remain conceptually separate.

### Memory

> “I declined an investor meeting because there wasn't enough context.”

### Personal model

> “I tend to avoid high-cost meetings unless I understand their expected value.”

### Prediction

> “I think you'd decline this meeting.”

This distinction is fundamental to Mimic.

---

# 27. Technical Architecture

```text
                    USER
                      │
                      ▼
             Experience Layer
       ┌──────────────┼──────────────┐
       │              │              │
    Answers        Decisions      Conversations
       │              │              │
       └──────────────┼──────────────┘
                      ▼
               Memory Layer
                      │
                      ▼
              Personal Model
       ┌──────────────┼──────────────┐
       │              │              │
   Personality     Operating       Goals/
     Model           Style          Values
       │              │              │
       └──────────────┼──────────────┘
                      ▼
               Context Retrieval
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
   External Research         Personal Context
       (Tavily)                   │
          │                       │
          └───────────┬───────────┘
                      ▼
              Nebius Token Factory
                      │
                NVIDIA Model
                      │
                      ▼
                 Prediction
                      │
                      ▼
               User Feedback
                      │
                      └──────────► Model Update
```

---

# 28. Technology Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS

### Backend

- Next.js API routes / server actions

### Database

- SQLite for the hackathon (single file, zero ops)
- Postgres + pgvector later, only if scale requires it

### AI Infrastructure

- **Nebius Token Factory**

### Model

- **NVIDIA Nemotron models via Nebius Token Factory**, assigned by role (check which models Token Factory offers before building):
  - **Reasoning model:** predictions and personalized recommendations (sampled N times for confidence)
  - **Small/fast model:** extracting memories, evidence and rules from answers, corrections and Tavily results
  - **Embedding model:** memory retrieval (Nemotron embedding if available on Token Factory, otherwise any Token Factory embedding model)
- Structured (JSON) outputs for predictions so option, evidence, alternatives and rules are machine-readable.
- The same model also runs the **baseline** (no personal context) for the accuracy comparison.

### Research

- **Tavily**

### Development

- Cursor

The development environment and AI infrastructure are separate concerns:

> **Cursor builds Mimic. Nebius runs its intelligence.**

---

# 29. Hackathon Architecture Requirement

Mimic must actually use Nebius at runtime.

The application should send relevant inference requests through:

**Nebius Token Factory**

and use at least one qualifying:

**NVIDIA open-source model**

This should be demonstrated clearly in the technical architecture and submission.

---

# 30. Why Tavily Matters

Tavily should not be included simply because it is a hackathon integration.

It strengthens the core product thesis.

Generic AI:

> “Here is what the internet says.”

Mimic:

> “Here is what the internet says, and here is what I think **you** would do about it.”

This makes Tavily part of the personalization loop.

Tavily is used in three places:

1. **Bootstrap:** search and extract the user's public footprint to seed the personal model (Onboarding Step 0).
2. **Grounded scenarios:** test scenarios and "Should I…?" questions about real opportunities (companies, roles, markets, events) are researched live, so predictions react to real facts.
3. **Research → prediction:** results are filtered through the personal model: *what I found → what matters to you → what you'd do.*

---

# 31. Privacy and Trust

Mimic deals with highly personal information.

Core principles:

### User ownership

The user owns their personal data.

### Explicit consent

Connected sources require explicit permission.

### Data minimization

Only collect information necessary to improve the experience.

### Transparency

Explain why information influences a prediction.

### Corrections

Users can correct Mimic's assumptions.

### Confidence

Mimic should express uncertainty.

### Human approval

External actions require user approval in the MVP.

### No diagnosis

Personality estimates are not medical, psychological, or clinical diagnoses.

---

# 32. Action Layer

Actions are the long-term direction, not the MVP centerpiece.

Eventually Mimic could:

- draft emails
- triage inboxes
- prepare meetings
- recommend opportunities
- schedule tasks
- communicate with others
- make purchases
- manage projects
- act autonomously with permission

The progression is:

**Understand me → Predict me → Recommend for me → Act for me**

The hackathon MVP should primarily prove the first two.

---

# 33. What We Are NOT Building

For the hackathon, explicitly avoid:

- a general-purpose autonomous agent
- dozens of integrations
- a giant personality test
- a complex email assistant
- a fully autonomous personal operating system
- hundreds of personality dimensions
- elaborate memory-management UI
- claims of scientifically diagnosing personality

These dilute the core demonstration.

---

# 34. Hackathon Demo Flow

The ideal demo should take approximately 2–3 minutes. **Open with the prediction moment, not onboarding.**

### 1. Cold open: blind prediction (~20s)

A pre-seeded persona (a real team member). A scenario appears. They lock in an answer secretly. Mimic reveals its prediction and confidence. Both shown side by side.

> **Correct.**

### 2. The pitch (~15s)

> “Agents are about to act on your behalf. They can't do that without a model of you. Mimic learns how you decide, and proves it by predicting you.”

### 3. Bootstrap (~30s, time-compressed)

Paste a few links → Tavily pulls the public footprint → inferred goals/values appear with sources → user confirms → 3 scenario questions.

### 4. Personal model (~10s)

Radar chart + operating style. Do not explain every score.

### 5. Real question with Tavily (~30s)

> “Should I pursue this opportunity?”

**What I found → What matters to you → What I think**

### 6. Correct it → it learns (~30s)

Mimic gets one wrong. User explains why. **New rule learned** appears. A similar scenario runs, the prediction flips, and it matches.

### 7. Proof (~15s)

> **Mimic 76% vs plain Nemotron 51%** on held-out scenarios, plus the calibration chart.

### 8. Close

> “Before your agent acts, it should ask Mimic.”

That is the demo.

---

# 35. The Emotional Arc

The demo should create this sequence:

### Curiosity

> “It wants to learn me?”

↓

### Recognition

> “Those observations actually sound like me.”

↓

### Suspense

> “What does it think I'd choose?”

↓

### Surprise

> “It got it right.”

↓

### Trust

> “It understands why.”

↓

### Learning

> “And it got better after I corrected it.”

This emotional progression is more important than showing a large number of features.

---

# 36. Success Metrics

### Primary metric

**Mimic Prediction Accuracy**

Correct predictions / total predictions.

### Secondary metrics

**Confidence calibration**

How closely confidence matches actual outcomes.

**Learning rate**

How much prediction accuracy improves with additional evidence.

**Correction acceptance**

How often users confirm or correct inferred patterns.

**Prediction engagement**

How frequently users voluntarily test Mimic.

**Personalization quality**

User rating:

> “How much did this feel like you?”

---

# 37. MVP Definition of Done

Mimic is successful for the hackathon when:

- [ ] User can complete onboarding in under 10 minutes.
- [ ] Behavioral answers generate a personal model.
- [ ] Six HEXACO-informed dimensions are displayed.
- [ ] Three operating-style dimensions are displayed.
- [ ] Goals and preferences are stored.
- [ ] Memories are persisted.
- [ ] Relevant context can be retrieved.
- [ ] Nebius Token Factory is used at runtime.
- [ ] NVIDIA open-source model is used.
- [ ] Tavily provides external research.
- [ ] Research is personalized using the user's model.
- [ ] Mimic can make explicit predictions.
- [ ] Predictions include confidence.
- [ ] Predictions include concise evidence.
- [ ] User can reveal the actual answer.
- [ ] Accuracy is tracked.
- [ ] User can correct Mimic.
- [ ] Corrections influence future predictions.
- [ ] Demo visibly shows learning.
- [ ] User commits their answer **before** the prediction is revealed (blind test).
- [ ] Confidence is derived from sampling agreement, not self-reported by the model.
- [ ] Baseline (plain Nemotron, no personal context) is run on the same held-out scenarios and its accuracy shown next to Mimic's.
- [ ] Corrections produce a visible "new rule learned" with source.
- [ ] Tavily bootstrap from public footprint works, with user confirmation of each inferred item.
- [ ] Pre-seeded demo persona lets anyone try the loop without onboarding.
- [ ] Real accuracy numbers from internal testers are included in the Devpost write-up.

---

# 38. Stretch Features

Only build these if the core prediction loop is already excellent.

### More data sources

- Gmail
- Calendar
- documents
- browser history
- Slack
- notes

### Richer prediction

- email response prediction
- purchase prediction
- meeting behavior
- task prioritization
- opportunity selection

### Longitudinal model

Show:

> “Mimic has known you for 90 days.”

### Counterfactual prediction

> “If you had no financial pressure, I think you'd choose A.”

### Relationship modeling

> “You trust Sarah's judgment more than most people in this category.”

### Autonomous action

> “I know what you would probably do. Want me to do it?”

---

# 39. Long-Term Vision

Mimic should evolve from:

### AI assistant

to:

### AI model of the individual

and eventually:

### AI representative of the individual

The long-term product loop becomes:

```text
Learn me
   ↓
Understand me
   ↓
Predict me
   ↓
Recommend for me
   ↓
Act for me
   ↓
Learn from the outcome
   ↺
```

The ultimate vision:

> **An AI that doesn't just know your history — it understands your patterns well enough to represent you.**

---

# 40. Positioning

### Primary positioning

> **Mimic learns how you think, what you care about, and what you would do — then predicts you and helps you act.**

### Short version

> **An AI clone that learns how you think and predicts what you would do.**

### Hackathon pitch

> **Agents are about to act on our behalf, but memory alone doesn't tell them what we'd want. Mimic builds a personal model of how you decide from your public footprint, goals, decisions and corrections. Then it proves that model: it predicts your choices blind, beats a plain Nemotron baseline, and gets measurably better every time you correct it.**

---

# 41. Competitive Moat

Mimic's moat is not the underlying model.

It is not the vector database.

It is not generic memory.

It is not search.

The potential moat is:

### Longitudinal personal behavioral data

Over time, Mimic accumulates:

- decisions
- corrections
- outcomes
- preferences
- behavioral patterns
- contextual exceptions
- prediction accuracy

This creates an increasingly personalized model.

The longer the relationship:

> **the better Mimic can predict the individual.**

---

# 42. Core Product Principle

One principle should guide every feature decision:

> **Does this help Mimic understand the user well enough to make a better prediction?**

If yes:

Build it.

If not:

Defer it.

---

# 43. Final Product Thesis

Mimic is not trying to be another chatbot with memory.

It is building a model of the person behind the conversation.

**Memory tells Mimic what happened.**

**Personality helps explain patterns.**

**Context tells Mimic what matters now.**

**Prediction tests whether it actually understands.**

**Feedback makes it better.**

The product succeeds when the user stops thinking:

> “This AI knows things about me.”

and starts thinking:

> **“This AI knows what I would do.”**