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

- [x] **STEP 8 — Reputation**
      `backend/app/agent/reputation.py`. Nothing is typed in: completed jobs, average
      rating, attendance and reliability are all **counted** from `job_assignments` and
      `ratings`. Attendance became days-attended over days-booked, which needed two new
      columns — it was the last hand-written number.
      `/api/reputation/check` recomputes every figure and reports any disagreement; it
      returns an empty list, and a test asserts that.
      *Success: a completed job updates the correct worker and crew records — separately.*
      ✅ **Done**

- [x] **STEP 9 — Independence intelligence**
      `backend/app/agent/independence.py`. Returns a score, the five factors from §9.11,
      the evidence, and a recommendation in words. Nothing in it writes to `workers` or
      `crew_members` — a test reads the source and asserts that, because rule 5 says the
      AI recommends and the worker decides.
      Gates are kept separate from the score, so a good average on three jobs is refused
      rather than rewarded. Presented openly as an unvalidated prototype figure.
      ✅ **Done**

- [x] **STEP 10 — Frontend**
      Next.js, React and Tailwind. All four screens from §19, plus a fifth showing the
      agent's action trail. Every agent reply displays whether it is grounded and which
      tools ran; the crew page puts the crew's rating and each member's own rating in
      adjacent columns.
      *Success: a professor can use the system without the terminal.* ✅ **Done**

- [ ] **STEP 11 — Multilingual layer** ⬅️ **Next**
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
