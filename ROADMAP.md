# ROADMAP.md — Build Steps

One step at a time. After each step: run the tests, verify manually, then continue.

---

- [x] **STEP 0 — Environment**
      Repository, documentation, Python virtual environment, FastAPI project, `.env.example`.
      *Success: `GET /health` returns `{"status": "ok"}`.* ✅ **Done**

- [ ] **STEP 1 — Sample workforce data**
      CSV files: workers, crews, crew members, contractors, jobs, ratings, availability.
      At least 20 workers across several skills, locations, ratings, job histories and
      availability states — some in crews, some independent.
      *Success: the backend can read the sample data.* ⬅️ **Next**

- [ ] **STEP 2 — Database**
      Move from CSV to PostgreSQL. Target project is ready: **`adaa-ai agent`**
      (`plqpwsnylgpecdlcftqs`), `ap-south-1` Mumbai, PostgreSQL 17, active and empty.
      Tables, relationships, seed data, CRUD tested.
      *Success: the application retrieves real workforce records from PostgreSQL.*

- [ ] **STEP 3 — Deterministic matching engine**
      Skill, availability and location filtering; reliability, rating, ranking, crew
      composition. Built **before** Gemini so it can be tested on its own.
      *Success: given "8 masons, Guntur, tomorrow" it returns suitable candidates.*

- [ ] **STEP 4 — Gemini integration**
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
