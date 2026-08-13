# ADAA — Workforce Coordination Agent

An AI agent that connects construction workforce demand with suitable workers, crews and
subcontractors, while helping every worker build an **independent professional reputation**.

University research prototype. Not a production marketplace.

**Current status: STEP 0 complete** — environment set up, API server runs, health check passes.
There is no database, no AI agent and no user interface yet. Those arrive in later steps.

---

## What this project is

A contractor says:

> "I need 8 masons tomorrow at 8 AM near Guntur."

ADAA understands the request, searches real workforce data, and proposes a workforce:

```text
Ravi Crew  — 6 workers
Suresh     — 1 worker
Raju       — 1 worker
Total      = 8 workers
```

...with an explanation of *why* each was chosen, grounded in verified database records.

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
GEMINI_MODEL=gemini-3.1-pro-preview
```

**Never commit the `.env` file.** It is already listed in `.gitignore`.

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
| <http://127.0.0.1:8000/> | Project name and current status |
| <http://127.0.0.1:8000/docs> | Interactive API documentation |

Press `Ctrl+C` in the terminal to stop the server.

### Run the tests

```bash
backend/.venv/Scripts/python -m pytest backend/tests -v
```

You should see **2 passed**.

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
│   │   ├── main.py      the API (currently just /health)
│   │   └── config.py    all settings, read from .env
│   ├── scripts/
│   │   └── check_gemini.py
│   └── tests/
│
├── data/                sample workforce data (added at STEP 1)
└── docs/                notes and diagrams
```

Folders are created when a build step actually needs them, to keep the project easy to read.

---

## Important

The AI agent inside ADAA is powered by **Google Gemini**, not by Claude. Claude Code is only
the coding assistant used to build this software. See [`CLAUDE.md`](CLAUDE.md).

The full specification is in
[`ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md`](ADAA_CLAUDE_CODE_BUILD_SPEC_GEMINI.md).
