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

- [ ] **STEP 4 — Gemini integration** ⬅️ **Next**
      Google GenAI SDK, Gemini client, system prompt, basic conversation endpoint.
      *Success: "I need 8 masons tomorrow" gets a meaningful response.*

- [ ] **STEP 5 — Agent tools**
      `search_workers`, `search_crews`, `get_worker_profile`, `get_crew_profile`,
      `check_availability`, `calculate_distance`.
      *Success: Gemini retrieves actual database information.*

- [ ] **STEP 6 — Workforce coordination agent**
      The full loop: understand → tool calls → deterministic matching → composition →
      explanation.
      *Success: the agent solves the 8-mason scenario using real data.*

- [ ] **STEP 7 — Job coordination**
      `create_job`, `send_job_offer`, `collect_response`, `confirm_assignment`.
      Notifications simulated at first.
      *Success: contractor → job → crew/worker → response → confirmation.*

- [ ] **STEP 8 — Reputation**
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
