# ADAA Workforce Coordination Agent — Claude Code Build Specification

## 0. Purpose

This is the master build specification for **Claude Code**.

The goal is NOT to train a new large language model. The goal is to build a working AI-agent application for ADAA.

### Important separation

- **Claude Code** = development/coding assistant used to build the ADAA software.
- **Gemini 3.1 Pro Preview** = the LLM that powers the ADAA Workforce Coordination Agent.
- **ADAA Agent** = the software agent that uses Gemini, tools, business rules, and the database.

The first version is a university research prototype, not a production-scale marketplace.

---

# 1. Product Context

## Product

**ADAA**

## AI Component

**ADAA Workforce Coordination Agent**

## Mission

Connect construction workforce demand with suitable workers, crews, and subcontractors while helping every worker build an independent professional reputation.

## Core Idea

ADAA should not simply eliminate the existing mason-leader system.

Instead, ADAA should digitize useful parts of the existing construction workforce network.

A mason leader becomes a recognized:

> **Crew Leader / Subcontractor**

Workers remain members of a crew while also having their own ADAA identity and individual reputation.

Long-term progression:

```text
Crew Member
    ↓
Verified Worker
    ↓
Independent Worker
    ↓
Crew Leader
    ↓
Subcontractor
```

Historical worker reputation remains attached to the individual worker.

---

# 2. Fieldwork Context

Initial fieldwork identified that mason leaders may perform several functions:

- Matchmaker
- Paymaster
- Support/insurance bridge
- Translator
- Crew coordinator

These findings are preliminary and should not be presented as statistically representative.

ADAA should preserve useful coordination functions while digitizing:

- worker identity
- availability
- skills
- job history
- ratings
- crew membership
- crew reputation
- contractor relationships

---

# 3. Users

## 3.1 Contractor

Needs to:

- post workforce requirements
- specify skill
- specify quantity
- specify site
- specify date/time
- specify wage
- receive workforce recommendations
- confirm workers/crews
- rate completed work

## 3.2 Crew Leader / Mason Leader / Subcontractor

Needs to:

- create a crew
- add workers
- manage crew availability
- receive job requests
- accept/decline jobs
- coordinate crew members
- maintain crew reputation
- eventually receive larger subcontracting opportunities

## 3.3 Crew Member

Needs to:

- maintain individual profile
- belong to a crew
- receive job information
- accept work when appropriate
- build independent work history
- accumulate individual ratings
- eventually become eligible for independent work

## 3.4 Independent Worker

Needs to:

- accept jobs directly
- maintain personal reputation
- maintain availability
- build contractor relationships
- eventually create/manage a crew

## 3.5 Admin

Needs to:

- verify users
- manage skills
- monitor jobs
- monitor agent actions
- resolve disputes
- monitor system performance

---

# 4. AI Agent

## 4.1 Agent Mission

> Coordinate the right construction workforce for the right job while continuously building reliable worker, crew, and subcontractor profiles.

## 4.2 Agent Responsibilities

### A. Understand requests

Example:

> "I need 8 masons tomorrow at 8 AM near Guntur."

Convert this into structured information:

```json
{
  "skill": "mason",
  "quantity": 8,
  "date": "tomorrow",
  "time": "08:00",
  "location": "Guntur"
}
```

### B. Identify missing information

If essential information is missing, ask concise clarification questions.

### C. Search workforce

Search:

- individual workers
- crews
- subcontractors

### D. Apply eligibility rules

Check:

- skill
- availability
- location
- travel radius
- current assignments
- verification
- reliability

### E. Compose workforce

The agent may combine:

```text
Crew + Crew
Crew + Individuals
Individuals only
Subcontractor + Individuals
```

Example:

```text
Requirement = 8 masons

Ravi Crew = 6
Suresh = 1
Raju = 1

Total = 8
```

### F. Explain recommendations

The agent must explain:

- why candidates were selected
- what evidence supports the recommendation
- any important limitations

Never invent qualifications or availability.

### G. Coordinate communication

Eventually:

- send job offers
- contact crew leaders
- collect responses
- update availability
- confirm workforce

### H. Update reputation/history

After job completion:

- update job history
- update worker reputation
- update crew reputation
- record attendance/outcome
- preserve historical relationships

### I. Recommend worker progression

The agent may recommend:

```text
Crew Member
    ↓
Independent Worker
```

and eventually:

```text
Independent Worker
    ↓
Crew Leader
    ↓
Subcontractor
```

The AI recommends.

The user decides.

---

# 5. Critical Business Rules

These must be implemented as application logic, not left entirely to the LLM.

## Rule 1 — Never claim unavailable workers are available.

Availability must come from the database.

## Rule 2 — Never fabricate worker qualifications.

Only verified skills may be used.

## Rule 3 — Worker and crew reputation are separate.

A crew's rating must not automatically become every member's rating.

## Rule 4 — Worker reputation belongs to the worker.

If Suresh leaves Ravi's crew, Suresh retains:

- jobs
- ratings
- verified skills
- attendance history
- contractor history

## Rule 5 — AI cannot force independence.

It can recommend:

> "Suresh may be ready for independent work."

Suresh must choose.

## Rule 6 — AI cannot automatically remove workers from crews.

Crew membership changes require appropriate user action.

## Rule 7 — Consequential actions require confirmation.

Examples:

- final job confirmation
- wage changes
- financial actions
- removing a worker
- changing verified information

## Rule 8 — Database is the source of truth.

Gemini is not the authoritative database.

## Rule 9 — Never claim an action happened unless the relevant tool confirms it.

---

# 6. System Architecture

```text
                    CONTRACTOR
                        |
                        v
                 ADAA APPLICATION
                        |
                        v
                  FASTAPI BACKEND
                        |
                        v
             ADAA WORKFORCE AGENT
                        |
                        v
                GEMINI 3.1 PRO
             (LLM / Reasoning Layer)
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Worker Tools   Crew Tools    Job Tools
          |             |             |
          +-------------+-------------+
                        |
                        v
                 PostgreSQL
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
     Workers          Crews            Jobs
```

### Separation of responsibilities

**Gemini 3.1 Pro**
- understand natural language
- reason about requests
- decide which tools are needed
- interpret retrieved information
- explain recommendations
- support multilingual interaction

**Python/application logic**
- calculate distance
- check availability
- calculate match scores
- retrieve database records
- enforce business rules
- update records
- perform validated actions

Core principle:

> **Gemini reasons; the ADAA application verifies and executes.**

---

# 7. Technology Stack

## LLM

**Gemini 3.1 Pro Preview**

The model name must be configurable through an environment variable so it can be changed later without rebuilding the application.

Example:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-pro-preview
```

Do not hard-code the model name throughout the application.

## Development Assistant

**Claude Code**

Claude Code is used to:

- create project files
- write code
- modify code
- run tests
- debug
- inspect project structure
- generate documentation

Claude Code is NOT the LLM powering the ADAA agent.

## Backend

**Python + FastAPI**

## Database

**PostgreSQL**

For the first prototype, local PostgreSQL is acceptable.

Later:

**Supabase/PostgreSQL + PostGIS**

## Frontend

**Next.js + React**

For the first prototype, keep the UI simple.

## Styling

**Tailwind CSS**

## Agent framework

### Version 1

Do NOT introduce LangGraph unless necessary.

Start with:

```text
Gemini API
+
Python
+
Function/Tool Calling
+
FastAPI
```

Add LangGraph only if the workflow becomes complex enough to justify it.

## Version control

**Git + GitHub**

---

# 8. Project Architecture

Create this initial structure:

```text
adaa-ai-agent/
│
├── README.md
├── PRODUCT.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── CLAUDE.md
├── .env.example
├── .gitignore
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │
│   │   ├── api/
│   │
│   │   ├── models/
│   │
│   │   ├── schemas/
│   │
│   │   ├── services/
│   │
│   │   ├── database/
│   │
│   │   └── agent/
│   │       ├── agent.py
│   │       ├── prompts.py
│   │       ├── tools.py
│   │       └── matching.py
│   │
│   └── tests/
│
├── frontend/
│
├── data/
│   ├── workers.csv
│   ├── crews.csv
│   ├── crew_members.csv
│   ├── contractors.csv
│   ├── jobs.csv
│   └── ratings.csv
│
└── docs/
```

Claude Code should not create unnecessary folders.

---

# 9. Database Model

## 9.1 workers

```text
id
name
phone
photo_url
preferred_language
location_lat
location_lng
travel_radius_km
experience_years
verification_status
availability_status
reliability_score
average_rating
completed_jobs
created_at
updated_at
```

## 9.2 skills

```text
id
name
category
```

## 9.3 worker_skills

```text
worker_id
skill_id
verification_status
years_experience
```

## 9.4 contractors

```text
id
name
phone
company_name
location
verification_status
rating
completed_jobs
created_at
```

## 9.5 crews

```text
id
name
leader_worker_id
primary_trade
location_lat
location_lng
travel_radius_km
availability_status
rating
completed_jobs
reliability_score
verification_status
created_at
updated_at
```

## 9.6 crew_members

```text
id
crew_id
worker_id
role
status
joined_at
left_at
```

Important:

Crew membership is a relationship.

It must not replace the worker's identity.

## 9.7 jobs

```text
id
contractor_id
title
description
skill_required
workers_required
location_lat
location_lng
site_address
date
start_time
wage
status
created_at
updated_at
```

## 9.8 job_assignments

```text
id
job_id
worker_id
crew_id
assignment_type
status
confirmed_at
completed_at
```

Assignment types:

```text
individual
crew
subcontractor
```

## 9.9 ratings

```text
id
job_id
rater_id
worker_id
crew_id
rating
comment
created_at
```

A rating may target a worker OR crew depending on the rating context.

## 9.10 availability

```text
id
worker_id
date
start_time
end_time
status
```

## 9.11 independence_assessments

```text
id
worker_id
score
completed_jobs_factor
rating_factor
attendance_factor
reliability_factor
contractor_relationship_factor
recommendation
created_at
```

This is an AI recommendation record, not an automatic employment-status change.

---

# 10. Workforce Matching Engine

Do not allow Gemini to perform basic mathematical/geographic matching by itself.

Create deterministic matching logic.

Candidate filters:

```text
skill matches
AND verified
AND available
AND not already assigned
AND within travel radius
```

Initial configurable ranking:

```text
match_score =
    0.30 * skill_score
  + 0.20 * availability_score
  + 0.20 * reliability_score
  + 0.15 * rating_score
  + 0.10 * proximity_score
  + 0.05 * experience_score
```

These are prototype weights, not scientifically validated weights.

---

# 11. Gemini Agent Tools

The first agent should have these tools.

## Tool 1

```text
search_workers()
```

Purpose:

Find suitable individual workers.

Inputs:

```text
skill
location
date
quantity
radius
```

## Tool 2

```text
search_crews()
```

Purpose:

Find available crews.

Inputs:

```text
skill
location
date
required_workers
radius
```

## Tool 3

```text
get_worker_profile()
```

Purpose:

Retrieve complete verified worker history.

## Tool 4

```text
get_crew_profile()
```

Purpose:

Retrieve crew history and members.

## Tool 5

```text
check_availability()
```

Purpose:

Verify whether a worker or crew is actually available.

## Tool 6

```text
calculate_distance()
```

Purpose:

Calculate distance between site and workforce location.

## Tool 7

```text
create_job()
```

Purpose:

Create a job after contractor confirmation.

## Tool 8

```text
send_job_offer()
```

Purpose:

Send a job opportunity to a worker or crew leader.

Initially this can be simulated.

Do not integrate WhatsApp/SMS until the core agent works.

## Tool 9

```text
record_job_outcome()
```

Purpose:

Record completion and outcome.

## Tool 10

```text
record_rating()
```

Purpose:

Record worker/crew rating.

## Tool 11

```text
check_independence_readiness()
```

Purpose:

Evaluate whether a worker has enough verified history for an independent-work recommendation.

---

# 12. Gemini System Prompt

Create a dedicated system prompt.

Initial version:

```text
You are the ADAA Workforce Coordination Agent.

ADAA is a construction workforce platform connecting
contractors, subcontractors, crew leaders, crews and
individual workers.

Your mission is to coordinate suitable construction
workforce for construction jobs while helping workers
build independent professional reputation.

You must:

1. Understand contractor workforce requests.
2. Extract skill, quantity, location, date, time and wage
   when available.
3. Ask concise clarification questions when essential
   information is missing.
4. Use tools to retrieve actual workforce data.
5. Never invent worker availability, skills, ratings or
   job history.
6. Apply eligibility rules before recommending workers.
7. Consider both crews and individual workers.
8. Combine crews and individuals when necessary.
9. Explain why a workforce recommendation was made.
10. Keep worker reputation separate from crew reputation.
11. Preserve a worker's historical reputation when they
    leave a crew.
12. Never force a worker to become independent.
13. Independence recommendations must be based on verified
    data.
14. Never make irreversible consequential decisions without
    appropriate confirmation.
15. Prefer concise, practical communication.
16. Communicate in the user's preferred language when supported.
17. Clearly distinguish verified data from recommendations.
18. Treat the database as the source of truth.
19. Do not pretend that an action was completed unless the
    relevant tool confirms completion.
```

---

# 13. First Prototype Data

Before connecting PostgreSQL, create sample CSV data.

## workers.csv

Create at least:

- 20 workers
- several skills
- several locations
- different ratings
- different job histories
- different availability
- some crew members
- some independent workers

Example:

```csv
id,name,skill,location,rating,completed_jobs,availability,crew
W001,Suresh,Mason,Guntur,4.7,31,available,RAVI01
W002,Mahesh,Mason,Guntur,4.6,24,available,RAVI01
W003,Raju,Mason,Guntur,4.5,18,available,
W004,Kumar,Helper,Guntur,4.4,15,available,RAVI01
```

## crews.csv

```csv
id,name,leader,trade,location,available_workers,rating,completed_jobs
RAVI01,Ravi Crew,Ravi,Masonry,Guntur,6,4.8,32
M001,Mahesh Crew,Mahesh,Masonry,Guntur,3,4.6,21
```

---

# 14. First Demonstration Scenario

The first successful agent demo must support:

### Input

```text
I need 8 masons tomorrow at 8 AM near Guntur.
```

### Expected process

```text
Understand request
        ↓
Search crews
        ↓
Search workers
        ↓
Check availability
        ↓
Rank candidates
        ↓
Compose workforce
        ↓
Explain recommendation
```

### Example expected result

```text
Recommended workforce:

Ravi Crew — 6 workers
Suresh — 1 worker
Raju — 1 worker

Total = 8 workers.

Reason:
- All candidates match the masonry requirement.
- They are available for the requested period.
- They are within the configured search area.
- Ravi Crew can efficiently provide six workers as a unit.
- Suresh and Raju fill the remaining positions.
```

The exact result must come from the dataset.

---

# 15. Second Demonstration — Crew Coordination

Input:

```text
Can Ravi's crew handle the job?
```

Agent should:

1. Retrieve Ravi's crew.
2. Check current availability.
3. Check required skill.
4. Check available member count.
5. Return a clear answer.

Example:

```text
Yes.

Ravi's crew currently has 6 available verified masons.
The job requires 8 workers, so the crew can cover 6 of
the required positions.

Two additional individual workers are recommended.
```

---

# 16. Third Demonstration — Worker Independence

Create Suresh:

```text
Jobs completed: 31
Average rating: 4.7
Attendance: 96%
Reliability: high
Verified skill: Mason
Current crew: Ravi Crew
```

Input:

```text
Is Suresh ready to work independently?
```

The agent should use the independence tool.

Expected style:

```text
Suresh appears suitable for consideration for independent
work based on his verified work history.

Evidence:
- 31 completed jobs
- 4.7 average rating
- 96% attendance
- verified masonry skill

Recommendation:
Eligible for selected independent assignments.

This is a recommendation, not an automatic change of status.
```

---

# 17. Fourth Demonstration — Reputation Preservation

Input:

```text
Suresh leaves Ravi's crew. What happens to his reputation?
```

Expected:

```text
Suresh retains his individual work history, verified skills,
ratings and completed jobs.

His previous relationship with Ravi's crew remains part of
his historical record.

Ravi's crew maintains its own separate crew reputation.
```

---

# 18. Fifth Demonstration — New Subcontractor

Input:

```text
Suresh has built his own crew. How should ADAA represent him?
```

Expected:

```text
Suresh remains an individual worker with his historical
reputation.

A new crew profile is created with Suresh as crew leader.

The crew develops its own reputation independently.

Suresh's worker reputation and the new crew reputation
remain separate.
```

---

# 19. Frontend Prototype

Build a simple interface after the agent backend works.

## Screen 1 — Contractor Dashboard

Components:

```text
Post Job
Active Jobs
Recommended Workforce
Recent Jobs
```

## Screen 2 — AI Workforce Assistant

Chat/input area:

```text
What workforce do you need?
```

Example:

```text
"I need 8 masons tomorrow at 8 AM near Guntur."
```

Show:

- parsed requirement
- recommended workforce
- explanation
- confirmation button

## Screen 3 — Crew Dashboard

Show:

```text
Crew name
Leader
Members
Availability
Rating
Active jobs
Incoming workforce requests
```

## Screen 4 — Worker Profile

Show:

```text
Name
Skill
Rating
Completed jobs
Attendance
Current crew
Verified skills
Independent-work progress
```

---

# 20. API Endpoints

Initial backend endpoints:

```text
POST /api/jobs/parse
POST /api/jobs
GET  /api/jobs/{id}

GET  /api/workers
GET  /api/workers/{id}

GET  /api/crews
GET  /api/crews/{id}

GET  /api/match/workforce

POST /api/offers
POST /api/offers/{id}/respond

POST /api/jobs/{id}/complete
POST /api/ratings

GET  /api/workers/{id}/independence
```

The exact implementation may change.

Do not over-engineer.

---

# 21. Build Roadmap

## STEP 0 — Environment

Goal:

Get the development environment working.

Tasks:

- create repository
- create Python virtual environment
- create FastAPI project
- configure Gemini environment variables
- install dependencies
- create `.env.example`
- create README
- verify server runs

Success:

```text
GET /health

{
  "status": "ok"
}
```

Do not build database or AI agent yet.

---

# STEP 1 — Sample Workforce Data

Goal:

Create a small realistic ADAA workforce dataset.

Tasks:

- workers
- crews
- crew members
- contractors
- jobs
- ratings
- availability

Success:

The backend can retrieve the sample data.

---

# STEP 2 — Database

Goal:

Move from CSV to PostgreSQL.

Tasks:

- configure database
- create tables
- create relationships
- seed sample data
- test CRUD operations

Success:

The application retrieves real workforce records from PostgreSQL.

---

# STEP 3 — Deterministic Matching Engine

Goal:

Build matching before Gemini.

Tasks:

- skill filtering
- availability filtering
- location filtering
- reliability
- rating
- ranking
- crew composition

Success:

Given:

```text
8 masons
Guntur
tomorrow
```

the matching engine returns suitable candidates.

---

# STEP 4 — Gemini Integration

Goal:

Connect Gemini 3.1 Pro Preview.

Tasks:

- Google GenAI SDK
- Gemini client
- environment configuration
- system prompt
- basic conversation endpoint

Success:

User can send:

```text
I need 8 masons tomorrow.
```

and receive a meaningful response.

---

# STEP 5 — Agent Tools

Goal:

Allow Gemini to use ADAA data.

Implement:

```text
search_workers
search_crews
get_worker_profile
get_crew_profile
check_availability
calculate_distance
```

Success:

Gemini can retrieve actual database information.

---

# STEP 6 — Workforce Coordination Agent

Goal:

Create the actual agent.

Workflow:

```text
User request
 ↓
Gemini understands request
 ↓
Tool calls
 ↓
Deterministic matching
 ↓
Workforce composition
 ↓
Gemini explains recommendation
```

Success:

The agent can solve the 8-mason scenario using real data.

---

# STEP 7 — Job Coordination

Add:

```text
create_job
send_job_offer
collect_response
confirm_assignment
```

Initially, simulate notifications.

Success:

The system can demonstrate:

```text
Contractor
 ↓
Job
 ↓
Crew/Worker
 ↓
Response
 ↓
Confirmation
```

---

# STEP 8 — Reputation

Add:

- ratings
- completed jobs
- attendance
- reliability
- worker history
- crew history

Success:

A completed job changes the correct worker/crew records.

---

# STEP 9 — Independence Intelligence

Implement:

```text
check_independence_readiness()
```

Initial factors:

```text
completed jobs
rating
attendance
reliability
verified skills
contractor relationships
```

Return:

```text
score
evidence
recommendation
```

Do not present the score as scientifically validated.

It is a prototype decision-support mechanism.

---

# STEP 10 — Frontend

Build:

1. Contractor dashboard
2. AI workforce assistant
3. Crew dashboard
4. Worker profile

Success:

A professor can interact with the system without using the terminal.

---

# STEP 11 — Multilingual Layer

Add:

- English
- Telugu
- Hindi

The first implementation can use Gemini for natural-language translation.

Do not allow translation to alter critical numbers such as:

- wage
- quantity
- date
- time
- job ID

Critical structured values should come from the database/application logic.

---

# STEP 12 — Professor Demonstration

Create a controlled demonstration dataset.

Demonstration:

### Scenario 1

Contractor:

> I need 8 masons tomorrow at 8 AM near Guntur.

### Scenario 2

> Can Ravi's crew handle it?

### Scenario 3

> Find individual workers to fill the remaining positions.

### Scenario 4

> Is Suresh ready to work independently?

### Scenario 5

> What happens to Suresh's reputation if he leaves Ravi's crew?

### Scenario 6

> Suresh has created his own crew. How should ADAA represent him?

Target demonstration length:

**5–10 minutes**

---

# 22. Evaluation Plan

Compare:

## Baseline

```text
Phone calls
WhatsApp
Mason leader
Personal contacts
```

## Treatment

```text
ADAA Workforce Coordination Agent
```

Measure:

| Metric | Baseline | ADAA Agent |
|---|---:|---:|
| Time to first acceptance | | |
| Time to fill | | |
| Acceptance rate | | |
| No-show rate | | |
| Contractor satisfaction | | |
| Worker satisfaction | | |
| Communication failures | | |

The experiment should use an appropriate sample size and documented methodology.

Do not claim improvement until measured.

---

# 23. AI Evaluation

Evaluate the agent on:

## Accuracy

Does it recommend workers who actually satisfy the rules?

## Grounding

Does it use database information rather than inventing facts?

## Tool Use

Does it call the correct tool?

## Explanation

Can it explain its recommendation?

## Safety

Does it avoid unauthorized actions?

## Multilingual Performance

Does it preserve meaning across English/Telugu/Hindi?

## Agent Reliability

Does the same request produce consistent decisions when the underlying data is unchanged?

---

# 24. Logging

Every important agent action should eventually be logged.

Example:

```text
agent_action
- session_id
- user_id
- action_type
- tool_name
- input
- output
- timestamp
- success
```

This allows debugging and university evaluation.

Never log secrets.

---

# 25. Important Non-Goals

Do NOT build these in the first version:

- payments
- payroll
- insurance claims
- material procurement
- equipment rental
- full social network
- AI construction estimator
- automated wage negotiation
- autonomous financial decisions
- fully autonomous hiring
- complex voice agent
- advanced analytics

These are future modules.

The university-funded AI project should remain focused on:

> **Workforce Coordination**

---

# 26. Final Definition of Done

The first complete prototype is finished when:

- [ ] Contractor can submit a workforce request.
- [ ] Gemini understands the request.
- [ ] Agent retrieves real workforce data.
- [ ] Matching engine filters candidates.
- [ ] Agent can consider crews and individuals.
- [ ] Agent can combine crews and individuals.
- [ ] Agent explains its recommendation.
- [ ] Agent never invents availability.
- [ ] Agent can demonstrate crew coordination.
- [ ] Jobs can be simulated from creation to completion.
- [ ] Worker and crew ratings are separate.
- [ ] Worker history remains after leaving a crew.
- [ ] Agent can evaluate independence readiness.
- [ ] Agent can explain worker progression.
- [ ] Basic frontend exists.
- [ ] Tests exist for core matching logic.
- [ ] Gemini API key is secured.
- [ ] Professor can complete the demonstration without terminal commands.

---

# 27. Development Rules for Claude Code

Claude Code must follow these rules.

## Rule A — Work incrementally

Do not build the entire system in one step.

Complete one milestone at a time.

## Rule B — Gemini is the ADAA LLM

Do not substitute Claude for Gemini inside the ADAA application.

Claude Code is only the development assistant.

The production/prototype agent must call Gemini through the Google GenAI API.

## Rule C — Explain before major changes

Before making a major architectural change, briefly explain:

- what is changing
- why
- files affected
- risks

Then implement it.

## Rule D — Do not invent requirements

Use this document as the product source of truth.

If a requirement is unclear:

1. inspect existing code
2. inspect documentation
3. ask the user only if necessary

## Rule E — Keep code simple

The developer is a student and does not code extensively.

Prefer:

- readable code
- clear names
- small functions
- comments where useful
- simple architecture

Avoid unnecessary design patterns.

## Rule F — Test every milestone

Each milestone must have:

- implementation
- test
- manual verification
- short explanation

## Rule G — Do not add unnecessary dependencies

Every new dependency should have a reason.

## Rule H — Never expose API keys

Use `.env`.

Never commit:

```text
GEMINI_API_KEY
DATABASE_PASSWORD
```

---

# 28. How Claude Code Should Work With This Document

At the beginning of the project, Claude Code should:

1. Read this file completely.
2. Inspect the current repository.
3. Identify what already exists.
4. Create a short implementation plan.
5. Start only with STEP 0.
6. Do not jump ahead.
7. After completing each step:
   - run tests
   - explain what was built
   - show how to run it
   - identify the next step
8. Stop and wait for the developer/user to proceed.

When the user says:

> "Continue to the next step"

Claude Code should implement the next incomplete milestone.

If a milestone is already complete, verify it before skipping it.

---

# 29. First Claude Code Instruction

Paste this after placing this file in the project as `CLAUDE.md`:

```text
Read the ADAA build specification completely before changing anything.

You are the senior software engineer helping me build the ADAA Workforce Coordination Agent.

Important architecture:
- Claude Code is ONLY my development/coding assistant.
- Gemini 3.1 Pro Preview is the LLM that must power the ADAA AI agent.
- Do NOT use the Anthropic API as the ADAA agent's LLM.
- The ADAA agent must use the Google GenAI API/SDK to communicate with Gemini.
- Python/FastAPI will be the backend.
- PostgreSQL will be the database.

Important context:
- I am a civil engineering student.
- I do not code extensively.
- I need a working AI-agent prototype for a university project.
- I need the architecture to remain understandable to me.
- Do not over-engineer the system.
- Do not build the entire product at once.

Your first task is ONLY STEP 0: Environment Setup.

Before writing code:
1. Inspect the repository.
2. Explain the proposed project structure briefly.
3. Identify whether anything already exists that should be preserved.
4. Confirm the Gemini integration approach.
5. Then implement STEP 0.

Do not implement the database, AI agent, frontend, or matching logic yet.

After completing STEP 0:
1. Run the relevant tests/checks.
2. Tell me exactly what was created.
3. Tell me exactly how to run the project.
4. Tell me what I should verify manually.
5. Stop and wait for me to say "continue".

Use the ADAA build specification as the primary source of truth.
Do not invent product requirements.
```

---

# 30. Development Philosophy

The goal is not:

> "Build the biggest AI system."

The goal is:

> **Build a small, demonstrably intelligent workforce coordination system that solves a real construction problem and can be scientifically evaluated.**

The final core loop is:

```text
Contractor request
        ↓
Gemini understands
        ↓
ADAA tools retrieve real data
        ↓
Deterministic matching
        ↓
Crew + individual coordination
        ↓
Job outcome
        ↓
Worker/crew reputation
        ↓
Worker independence pathway
```

### Final architecture in one sentence

> **Claude Code builds ADAA; Gemini 3.1 Pro powers ADAA's AI agent; Python/FastAPI controls the application; PostgreSQL stores the workforce data; deterministic business logic verifies and executes decisions.**
