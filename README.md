# ADAA — Workforce Coordination Agent

An AI agent that connects construction workforce demand with suitable workers, crews and
subcontractors, while helping every worker build an **independent professional reputation**.

University research prototype. Not a production marketplace.

**Current status: STEPS 0–5 complete** — the agent understands a request in plain language,
searches the real database through its tools, and composes a workforce it can explain.
It cannot yet create jobs or send offers, and there is no user interface. Those come next.

**Presenting this?** Read [`docs/demo-script.md`](docs/demo-script.md) first. The Gemini
free tier allows only 20 requests a day, which is about one rehearsal and one live run.

---

## What this project is

A contractor says:

> "I need 8 masons tomorrow at 8 AM near Guntur."

ADAA understands the request, searches real workforce data, and proposes a workforce.
This is the actual output of the matching engine against the seeded database:

```text
Ravi Crew  — 6 workers    score 90.2   (6 of 6 available members)
Mahesh     — 1 worker     score 88.9   rating 4.6,  24 jobs
Ramesh     — 1 worker     score 85.6   rating 4.06, 17 jobs
Total      = 8 workers
```

...with an explanation of *why* each was chosen, grounded in verified database records.
Nobody appears who is not verified, skilled and genuinely free that day, and if the
request cannot be filled ADAA says so rather than padding the list.

The key idea: ADAA does not remove the traditional mason-leader system, it **digitises** it.
A mason leader becomes a recognised Crew Leader / Subcontractor, and workers keep their own
identity and reputation as they progress:

```text
Crew Member -> Verified Worker -> Independent Worker -> Crew Leader -> Subcontractor
```

See [`PRODUCT.md`](PRODUCT.md) for the full product picture and
[`ARCHITECTURE.md`](ARCHITECTURE.md) for how it is built.

---

## Setup

You need **Python 3.12 or newer**. (Tested on Python 3.14.)

### 1. Install the dependencies

From the project folder:

```bash
py -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
```

> On macOS or Linux the path is `backend/.venv/bin/python` instead of
> `backend/.venv/Scripts/python`.

### 2. Create your environment file

Copy `.env.example` to a new file named `.env`, then fill in your Gemini API key.
Get a key from <https://aistudio.google.com/apikey>.

```env
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.5-flash
```

**Never commit the `.env` file.** It is already listed in `.gitignore`.

---

### 3. Create the sample data and load the database

```bash
backend/.venv/Scripts/python backend/scripts/generate_data.py
backend/.venv/Scripts/python backend/scripts/seed_database.py
```

The first command writes ten CSV files into `data/`. The second creates all the database
tables and loads those files into PostgreSQL.

Both are safe to run again at any time. The data generator uses a fixed random seed, so it
always produces exactly the same dataset, and the seeder rebuilds the tables from scratch.

---

## Running it

### Start the server

```bash
backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
```

Then open in your browser:

| Address | What you should see |
|---|---|
| <http://127.0.0.1:8000/health> | `{"status":"ok"}` |
| <http://127.0.0.1:8000/health/database> | `{"status":"ok","workers":32}` |
| <http://127.0.0.1:8000/> | Project name and current status |
| <http://127.0.0.1:8000/docs> | Interactive API documentation |

Things worth trying in the browser:

| Address | What it shows |
|---|---|
| `/api/workers` | every worker, best rated first |
| `/api/workers?skill=Mason` | only workers with a **verified** masonry skill |
| `/api/workers/W001` | Suresh: profile, skills, crew history, ratings |
| `/api/crews` | all crews with their member counts |
| `/api/crews/RAVI01` | Ravi Crew, and each member's **own** rating |
| `/api/skills` | the twelve skills ADAA knows about |
| `/api/locations` | the places ADAA has workforce in |
| `/api/match/workforce?skill=Mason&quantity=8&location=Guntur` | **the 8-mason scenario** |

And two that use Gemini (POST, so use `/docs` to try them):

| Endpoint | What it does |
|---|---|
| `POST /api/jobs/parse` | reads a sentence into structured job details |
| `POST /api/agent/chat` | talks to the agent, which searches the database |

The agent's reply includes `tools_used` and `grounded`. If `grounded` is false, no tool ran,
so nothing in that reply came from the database.

Press `Ctrl+C` in the terminal to stop the server.

### Run the tests

```bash
backend/.venv/Scripts/python -m pytest backend/tests -v
```

You should see **134 passed** and 1 skipped. Tests that need the database are skipped automatically if it
cannot be reached, so the suite still runs without a `.env` file.

### Check that Gemini works

Only after you have put a real key in `.env`:

```bash
backend/.venv/Scripts/python backend/scripts/check_gemini.py
```

This tells you in plain language whether your key works and whether the model name in
`GEMINI_MODEL` is valid. If the model name is rejected, just change that one line in `.env` —
no code changes needed.

---

## Project layout

```text
ADAA-AI-AGENT/
├── README.md            this file
├── PRODUCT.md           what ADAA is, who uses it
├── ARCHITECTURE.md      how the system is put together
├── ROADMAP.md           the build steps, and where we are
├── CLAUDE.md            working rules for the AI coding assistant
├── .env.example         template for your .env file
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py      the API endpoints
│   │   ├── config.py    all settings, read from .env
│   │   ├── database.py  the PostgreSQL connection
│   │   └── agent/
│   │       ├── matching.py   who is eligible, and who ranks highest
│   │       ├── tools.py      what Gemini is allowed to look up
│   │       ├── agent.py      the Gemini connection
│   │       └── prompts.py    what Gemini is told
│   ├── database/
│   │   └── schema.sql   the eleven tables
│   ├── scripts/
│   │   ├── check_gemini.py
│   │   ├── generate_data.py    writes the CSV files
│   │   └── seed_database.py    loads them into PostgreSQL
│   └── tests/
│
├── data/                the sample workforce data (CSV)
└── docs/                notes and diagrams
```

Folders are created when a build step actually needs them, to keep the project easy to read.

---

## Important

The AI agent inside ADAA is powered by **Google Gemini**, not by Claude. Claude Code is only
the coding assistant used to build this software. See [`CLAUDE.md`](CLAUDE.md).

The full specification is in
[`ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md`](ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md).
