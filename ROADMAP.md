# ROADMAP.md — Build Steps

One step at a time. After each step: run the tests, verify manually, then continue.

---

- [x] **STEP 0 — Environment**
      Repository, documentation, Python virtual environment, FastAPI project, `.env.example`.
      *Success: `GET /health` returns `{"status": "ok"}`.* ✅ **Done**

- [x] **STEP 1 — Sample workforce data**
      Ten CSV files in `data/`, produced by `backend/scripts/generate_data.py` under a
      fixed random seed: 32 workers, 5 crews, 6 contractors, 14 jobs, 448 availability
      rows. Mixed skills, locations, ratings, verification and availability states — some
      workers in crews, some independent.
      *Success: the backend reads the sample data.* ✅ **Done**

- [x] **STEP 2 — Database**
      PostgreSQL on Supabase — project **`adaa-ai agent`** (`plqpwsnylgpecdlcftqs`),
      `ap-south-1` Mumbai, PostgreSQL 17.6. All 11 tables created from
      `backend/database/schema.sql` and seeded by `backend/scripts/seed_database.py`.
      API endpoints read live records.
      *Success: the application retrieves real workforce records from PostgreSQL.* ✅ **Done**

- [x] **STEP 3 — Deterministic matching engine**
      `backend/app/agent/matching.py`: haversine distance, the five eligibility filters,
      the six-part weighted score, and crew-plus-individual composition. No AI involved,
      so it is testable on its own.
      *Success: "8 masons, Guntur, tomorrow" returns Ravi Crew (6) + 2 individuals = 8.*
      ✅ **Done**

- [x] **STEP 4 — Gemini integration**
      Google GenAI SDK, cached Gemini client, the section-12 system prompt, a conversation
      endpoint and a request parser. Running on `gemini-3.5-flash` — the spec's
      `gemini-3.1-pro-preview` gets zero quota on the free tier; `GEMINI_MODEL` in `.env`
      switches to Pro with no code change.
      *Success: "I need 8 masons tomorrow at 8 AM near Guntur" → skill Mason, quantity 8,
      date 2026-08-14, time 08:00, location Guntur.* ✅ **Done**

- [x] **STEP 5 — Agent tools**
      Seven read-only tools in `backend/app/agent/tools.py`: `search_workers`,
      `search_crews`, `get_worker_profile`, `get_crew_profile`, `check_availability`,
      `distance_between`, plus `recommend_workforce`, which runs the whole composition.
      Every reply reports `tools_used`, and `grounded` is true only when a tool ran.
      *Success: Gemini retrieves actual database information.* ✅ **Done**

- [x] **STEP 6 — Workforce coordination agent**
      The full loop, end to end, with a session and an audit trail. Every tool call is
      written to `agent_actions` (spec §24) with its arguments, its result, how long it
      took and whether it worked. Replies are cached so the same question does not spend
      Gemini quota twice.
      *Success: the agent solves the 8-mason scenario using real data.* ✅ **Done**

- [x] **STEP 7 — Job coordination**
      The first actions that change records — and none of them can be done by the agent.
      It **proposes**; a person confirms through `/api/actions/{id}/confirm`; the
      application executes. There is deliberately no tool that confirms, and a test
      asserts it. Notifications are simulated, as the spec requires.
      Confirming books the workers, so a confirmed worker stops appearing as available.
      *Success: contractor → job → offer → response → confirmation.* ✅ **Done**

- [ ] **STEP 8 — Reputation** ⬅️ **Next**
      Ratings, completed jobs, attendance, reliability, worker history, crew history.
      *Success: a completed job updates the correct worker and crew records — separately.*

- [ ] **STEP 9 — Independence intelligence**
      `check_independence_readiness()` returning score, evidence and recommendation.
      Not presented as scientifically validated — it is decision support.

- [ ] **STEP 10 — Frontend**
      Contractor dashboard, AI workforce assistant, crew dashboard, worker profile.
      *Success: a professor can use the system without the terminal.*

- [ ] **STEP 11 — Multilingual layer**
      English, Telugu, Hindi. Translation must never alter wage, quantity, date, time or job
      ID — those come from the database, not the model.

- [ ] **STEP 12 — Professor demonstration**
      Controlled dataset covering the six demo scenarios. Target length 5–10 minutes.

---

## Definition of Done

The full 18-item checklist is in section 26 of the build specification. The headline: a
contractor can submit a request, the agent grounds every claim in real data, crews and
individuals can be combined, worker and crew reputations stay separate, worker history
survives leaving a crew, and a professor can run the whole demo without a terminal.
