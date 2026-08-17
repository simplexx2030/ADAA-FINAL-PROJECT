# CLAUDE.md — Working Rules for the ADAA Project

**Full product requirements live in [`ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md`](ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md).**
That file is the single source of truth. Read it before any significant change.
This file holds the rules that apply to *every* session.

---

## The one-sentence architecture

> Claude Code builds ADAA; Gemini powers ADAA's AI agent; Python/FastAPI controls the
> application; PostgreSQL stores the workforce data; deterministic business logic verifies
> and executes decisions.

## The core principle

> **Gemini reasons; the ADAA application verifies and executes.**

| Gemini does | Python does |
|---|---|
| Understand natural language | Calculate distance |
| Decide which tools are needed | Check availability |
| Interpret retrieved data | Calculate match scores |
| Explain recommendations | Enforce business rules |
| Support multilingual interaction | Read/write the database |

## Role separation — do not confuse these

- **Claude Code** = the development/coding assistant. Builds the software.
- **Gemini** = the LLM *inside* the product, called via the Google GenAI SDK.
- **ADAA Agent** = the software agent using Gemini + tools + business rules + database.

**The Anthropic API must never appear in the ADAA runtime.** Claude does not power the agent.

---

## The 9 business rules (spec §5)

These are **application logic**, not prompt instructions. The LLM must not be the only thing
enforcing them.

1. Never claim unavailable workers are available. Availability comes from the database.
2. Never fabricate worker qualifications. Only verified skills may be used.
3. Worker and crew reputation are **separate**. A crew's rating is not every member's rating.
4. Worker reputation belongs to the worker. Leaving a crew preserves jobs, ratings, verified
   skills, attendance, and contractor history.
5. AI cannot force independence. It recommends; the worker decides.
6. AI cannot automatically remove workers from crews.
7. Consequential actions require confirmation (job confirmation, wage changes, financial
   actions, removing a worker, changing verified information).
8. The database is the source of truth. Gemini is not.
9. Never claim an action happened unless the relevant tool confirms it.

---

## Development rules (spec §27)

- **A — Work incrementally.** One milestone at a time. Never build the whole system at once.
- **B — Gemini is the ADAA LLM.** Never substitute Claude inside the product.
- **C — Explain before major changes.** State what changes, why, files affected, risks.
- **D — Do not invent requirements.** The spec is the source of truth. Inspect code and docs
  first; ask the user only if genuinely necessary.
- **E — Keep code simple.** The developer is a civil engineering student who does not code
  extensively. Prefer readable code, clear names, small functions, useful comments, simple
  architecture. Avoid unnecessary design patterns.
- **F — Test every milestone.** Implementation + test + manual verification + short explanation.
- **G — No unnecessary dependencies.** Every dependency needs a reason.
- **H — Never expose API keys.** Use `.env`. Never commit `GEMINI_API_KEY` or database passwords.

## Session workflow

After completing each step:

1. Run the tests.
2. Explain what was built.
3. Show how to run it.
4. State what to verify manually.
5. Name the next step.
6. **Stop and wait** for the user to say "continue".

If a milestone appears already complete, verify it before skipping it.

---

## Project decisions made so far

- **Git**: this repo was initialised fresh for ADAA. The unrelated previous project
  (BidReady) history is kept locally in `.git-bidready-backup/` and is git-ignored.
  Remote (`origin`): `https://github.com/simplexx2030/ADAA-FINAL-PROJECT.git`
  The first remote, `victorsimba189-lab/Adaa-ai-agent`, was **abandoned on 2026-08-17**:
  that GitHub account is not accessible, and Vercel cannot deploy a personal-account
  repository unless the connected GitHub login *owns* it — collaborator access is not
  enough. It is still configured locally as `old-origin`, for reference only. Push to
  `origin`, which the machine's stored credential (`simplexx2030`) owns.
- **Database**: Supabase hosted PostgreSQL — project **`adaa-ai agent`**
  (ref `plqpwsnylgpecdlcftqs`), organisation `5pillars`, region `ap-south-1` (Mumbai),
  PostgreSQL 17, status ACTIVE_HEALTHY. API URL `https://plqpwsnylgpecdlcftqs.supabase.co`.
  All 11 tables exist and are seeded. Connect through `app.database`, never with a
  hand-built URL — `normalize_database_url` repairs the connection string.
- **Python**: 3.14 works; all dependencies install cleanly.
- **Model name**: never hard-coded. It comes from `GEMINI_MODEL` in `.env`. Verify the
  current one with `backend/scripts/check_gemini.py`. See "Gemini model" below.

## Known environment facts

- **Gemini model.** Running on **`gemini-3.5-flash`** (user decision, 2026-08-13).
  `gemini-3.1-pro-preview` exists and the key is valid, but the **free tier grants it zero
  quota** (429, `limit: 0`) — that is not exhaustion, Pro is simply never free. Confirmed
  working on this key: `gemini-3.5-flash`, `gemini-3.1-flash-lite`, `gemini-flash-latest`.
  Moving to Pro is one line in `.env` once billing is enabled.
- **Free-tier limits are tight: 5 requests/minute and 20/day PER MODEL.** A tool-using turn
  costs two requests. Each model has its own separate allowance, so changing `GEMINI_MODEL`
  buys a fresh one. Per-minute limits are retried automatically; per-day ones are not,
  because waiting cannot fix them. This is the main risk to a live demonstration — see
  [`docs/demo-script.md`](docs/demo-script.md).
- **Never swap Gemini for Claude.** This was raised and declined once already. Spec Rule B
  and §29 forbid it, the Claude Code subscription is not API access, and the Gemini free
  tier works.
- **The Gemini client must be cached.** A throwaway `genai.Client()` is garbage collected
  mid-request and the call dies with "client has been closed". See `agent._cached_client`.
- **Supabase connection.** Use the **session pooler** host
  (`aws-0-ap-south-1.pooler.supabase.com:5432`). The direct host `db.<ref>.supabase.co` is
  IPv6-only and does not resolve on this network. `aws-1-...` is the wrong pooler for this
  project.
- **RLS.** Supabase's platform event trigger `ensure_rls` auto-enables row level security on
  every new table in `public`. Our tables therefore have RLS on with no policies, which
  correctly blocks the public REST API. The backend connects as the `postgres` role and
  bypasses RLS. Policies are only needed if the frontend ever talks to Supabase directly —
  it should not; it goes through FastAPI.

## Current position

**STEP 0 through 10 complete.** Next: STEP 11 — the multilingual layer.

**Frontend** (Next.js 16 + React 19 + Tailwind 4, at the **repository root**): all calls go
through `lib/api.ts` — nothing else calls `fetch`. Pages are client components using
`useLoad`. Dynamic route params are a **Promise** in Next 16; unwrap with `use(params)`.
Read `AGENTS.md` and `node_modules/next/dist/docs/` before changing page conventions —
this Next version differs from older patterns.

**Why the frontend is at the root** (moved 2026-08-17, do not move it back into
`frontend/`): Vercel decides a project is Next.js by resolving the **installed** `next` in
the Root Directory. With the application in `frontend/`, `npm install --prefix frontend`
put it in `frontend/node_modules`, so every Git build died with *"No Next.js version
detected"* before it ever reached the Python function. Declaring `next` in a root
`package.json` was tried and is **not** sufficient — the builder wants the installed
package, not the declaration. So `app/`, `components/`, `lib/`, `public/` and the Node
config files all live at the root now, `api/index.py` and `backend/` are unchanged, and
`vercel.json` needs no build commands at all. See [`docs/vercel-deploy.md`](docs/vercel-deploy.md).

CORS in `backend/app/main.py` allows `localhost:3000` only, and exists purely because the
two run on different ports in development.

The agent reaches data **only** through `backend/app/agent/tools.py`. The read tools never
write; the `propose_*` tools write a proposal and nothing else. A person confirms via the
API — the agent has no tool that confirms, and no tool that awards a rating.

`grounded` on a chat reply is true only when a tool actually ran. Keep it that way — it is
the mechanical check behind rule 9.

**Audit log** (`app/agent/audit.py`, table `agent_actions`): every tool call is recorded with
arguments, result, duration and success. `agent_actions` is deliberately **not** dropped by
`schema.sql`, so re-seeding does not erase the evaluation evidence. Logging swallows its own
errors — a lost row must never cost a user their answer. Never log secrets.

**Reply cache** (`app/agent/cache.py`): the key includes the model, today's date and a
fingerprint of the workforce data, so a cached answer can never outlive the availability it
was based on. Tests run with the cache **off** (see `tests/conftest.py`) — without that,
tests sharing placeholder input read each other's answers.

**Write actions** (`app/agent/actions.py`, table `pending_actions`): the agent proposes,
a person confirms via `POST /api/actions/{id}/confirm`, the application executes.
**Never give the agent a tool that confirms, cancels or executes** — two tests guard this,
and without it rule 7 is only a suggestion. Proposals expire after 30 minutes and are
re-checked at execution, because a worker free at propose time may be booked by confirm time.

**Tests that write must clean up.** Confirming an assignment marks workers `booked`, which
silently breaks the 8-mason demo for everyone afterwards. See the `sandbox` fixture in
`tests/test_agent_actions.py`. If the demo ever looks wrong, re-run `seed_database.py`.

**Reputation** (`app/agent/reputation.py`): every figure is **counted**, never written by
hand — `completed_jobs`, `average_rating`, `attendance_rate` (days attended ÷ days booked)
and `reliability_score`. The same module is used by `generate_data.py` and at runtime, so
demo data and live updates cannot drift apart. `check_all()` must always return `[]`.

Two rules live in the SQL, not the prompt: `worker_figures` reads only ratings whose
`worker_id` matches and `crew_figures` only those whose `crew_id` matches (rule 3), and
**neither ever joins `crew_members`** — that is what makes a worker keep their history after
leaving a crew (rule 4). A test asserts both.

**Independence** (`app/agent/independence.py`): rule 5 means the assessment must change
nothing. It writes only to `independence_assessments`, which records *advice given* — never
to `workers` or `crew_members`. A test greps the source for `update workers` and friends.
The `important` disclaimer is inside the returned payload, not only in the prompt, because
the prompt is the part a model drifts away from. Gates (verified skill, verified worker,
minimum jobs, minimum contractors) are deliberately separate from the score, so a strong
average on a thin record is refused rather than rewarded. The weights are **not validated**
and every surface says so.

The matching engine (`backend/app/agent/matching.py`) is deterministic and fully tested
without an LLM. Gemini must call it, never replace it. See [`docs/matching.md`](docs/matching.md).
See [`ROADMAP.md`](ROADMAP.md) for the full checklist.
