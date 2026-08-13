# ARCHITECTURE.md — How ADAA Is Built

---

## The system

```text
                    CONTRACTOR
                        |
                        v
                 ADAA APPLICATION          (Next.js + React + Tailwind)
                        |
                        v
                  FASTAPI BACKEND          (Python)
                        |
                        v
             ADAA WORKFORCE AGENT
                        |
                        v
                GEMINI 3.1 PRO
             (LLM / Reasoning Layer)       (Google GenAI SDK)
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Worker Tools   Crew Tools    Job Tools
          |             |             |
          +-------------+-------------+
                        |
                        v
                 PostgreSQL               (Supabase, ap-south-1)
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
     Workers          Crews            Jobs
```

---

## The core principle

> **Gemini reasons; the ADAA application verifies and executes.**

This split is the heart of the design. It is what makes the system trustworthy and
scientifically evaluable, because the parts that must be correct are deterministic and
testable without an LLM.

| Gemini 3.1 Pro is responsible for | Python / application logic is responsible for |
|---|---|
| Understanding natural language | Calculating distance |
| Reasoning about requests | Checking availability |
| Deciding which tools are needed | Calculating match scores |
| Interpreting retrieved information | Retrieving database records |
| Explaining recommendations | Enforcing business rules |
| Supporting multilingual interaction | Updating records, executing validated actions |

Gemini never invents a fact. Every claim it makes about a worker, a crew or an action must
come from a tool result. If no tool confirms an action, the agent must not say it happened.

---

## Role separation

- **Claude Code** — the development assistant. Writes and edits this codebase. Not part of
  the running product.
- **Gemini 3.1 Pro Preview** — the LLM that powers the ADAA agent at runtime, reached through
  the Google GenAI SDK.
- **ADAA Agent** — the software agent combining Gemini, tools, business rules and the database.

The Anthropic API appears nowhere in the ADAA runtime.

---

## Technology choices

| Layer | Choice | Why |
|---|---|---|
| LLM | Gemini 3.1 Pro Preview | Required by the specification. Model name lives in `GEMINI_MODEL` so it can be swapped without code changes. |
| Backend | Python + FastAPI | Simple, readable, automatic API documentation. |
| Database | PostgreSQL via Supabase | Hosted, no local install, matches the spec's long-term target. PostGIS available later for geography. |
| Frontend | Next.js + React + Tailwind | Specified. Kept deliberately simple for the prototype. |
| Agent framework | Plain Gemini function calling | **No LangGraph in version 1.** Added only if the workflow genuinely becomes complex enough to justify it. |
| Version control | Git + GitHub | Standard. |

---

## The matching engine

Gemini is **not** allowed to perform the basic mathematical and geographic matching itself.
That logic is deterministic Python.

**Candidate filter** — a worker or crew is eligible only if *all* hold:

```text
skill matches
AND verified
AND available
AND not already assigned
AND within travel radius
```

**Ranking** (prototype weights, configurable, *not* scientifically validated):

```text
match_score =
    0.30 * skill_score
  + 0.20 * availability_score
  + 0.20 * reliability_score
  + 0.15 * rating_score
  + 0.10 * proximity_score
  + 0.05 * experience_score
```

Built at STEP 3, before Gemini is connected to it, so it can be tested on its own.

---

## Agent tools

The agent reaches data only through these functions. Each returns real database records.

| Tool | Purpose |
|---|---|
| `search_workers()` | Find suitable individual workers |
| `search_crews()` | Find available crews |
| `get_worker_profile()` | Retrieve a worker's verified history |
| `get_crew_profile()` | Retrieve crew history and members |
| `check_availability()` | Verify a worker or crew really is available |
| `calculate_distance()` | Distance between site and workforce |
| `create_job()` | Create a job after contractor confirmation |
| `send_job_offer()` | Send an opportunity (simulated at first — no WhatsApp/SMS until the core agent works) |
| `record_job_outcome()` | Record completion and outcome |
| `record_rating()` | Record a worker or crew rating |
| `check_independence_readiness()` | Evaluate readiness for an independent-work recommendation |

---

## Data model

Eleven tables: `workers`, `skills`, `worker_skills`, `contractors`, `crews`, `crew_members`,
`jobs`, `job_assignments`, `ratings`, `availability`, `independence_assessments`.

Two design points that carry the product idea:

- **`crew_members` is a relationship, not an identity.** It links a worker to a crew for a
  period of time. It never replaces the worker's own record. This is what lets a worker leave
  a crew and keep everything they earned.
- **`independence_assessments` records an AI recommendation**, not an automatic change of
  employment status. The worker decides.

Full column lists are in section 9 of the build specification.

---

## Logging

Every important agent action is logged: `session_id`, `user_id`, `action_type`, `tool_name`,
`input`, `output`, `timestamp`, `success`.

This enables debugging and university evaluation. **Secrets are never logged.**

---

## Current state

STEP 0. Only the FastAPI skeleton and its health check exist. Everything above this line
describes the target design, built one step at a time — see [`ROADMAP.md`](ROADMAP.md).
