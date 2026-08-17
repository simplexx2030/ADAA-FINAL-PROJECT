# ADAA — Frontend

The four screens from section 19 of the build specification. Next.js, React and
Tailwind, deliberately plain.

## Running it

The frontend shows data from the backend, so **start the backend first**:

```bash
backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
```

Then, in a second terminal:

```bash
npm run dev
```

Open <http://localhost:3000>.

The indicator in the top right says whether the backend is reachable. If it is red,
the backend is not running, and every page will say so rather than showing an empty
screen.

## The screens

| Page | What it is for |
|---|---|
| `/` | **Dashboard** — the figures, and the two ways in |
| `/assistant` | **AI assistant** — ask for workforce in plain language |
| `/contractor` | **Contractor dashboard** — post a job, see the recommended workforce for each |
| `/workers`, `/workers/{id}` | **Workers** — card grid with search and trade filters; profile with reputation, skills, crew history, independence |
| `/crews`, `/crews/{id}` | **Crews** — card grid; crew page shows each member's *own* rating |
| `/jobs` | Every job, filterable by status |
| `/activity` | **AI activity** — what the assistant looked up, and when |
| `/sessions/{id}` | One conversation, tool call by tool call |

## Posting a job

`/contractor` → **Post Job** opens a form (trade, headcount, place, date, time, wage).
Submitting creates the job, and the card immediately shows the workforce the matching
engine recommends for it, with a shortfall if there is one.

The form creates the job directly, unlike the agent's route, which only proposes one.
The difference is who is acting: business rule 7 exists so the AI cannot commit a
contractor to something, and here the contractor is pressing the button themselves.
The agent still has no way to do this.

## Two things the interface is careful about

**Every agent reply shows its provenance.** Under each answer is a row saying whether
it came from the database and which tools ran. A chat bubble on its own is not evidence
— a language model can write a confident paragraph about eight masons who do not exist.
If no tool ran, the interface says so. `/activity` shows the same record across every
conversation.

**A crew's rating is never shown as a member's rating.** The crew page puts the crew
rating and each member's own rating in adjacent columns, because keeping those two
apart is the point of the product.

Beyond those, the screens stay quiet: labels rather than commentary. The product should
not explain its own design to the person using it.

## How it is put together

The Next.js application sits at the **repository root**, alongside `api/` and
`backend/`, because Vercel requires it there — see
[`vercel-deploy.md`](vercel-deploy.md).

```text
├── app/               one folder per screen
├── components/
│   ├── Nav.tsx        the top bar and the health indicator
│   └── ui.tsx         cards, tags, stats, buttons — no component library
└── lib/
    ├── api.ts         every call made to the backend, in one file
    └── useLoad.ts     loading and error handling, written once
```

There is no state management library and no design system. A card is a `div` with a
border. Nothing here calculates a rating, a distance or an availability — the backend
is the source of truth and the interface only asks.

## Configuration

The backend address defaults to `http://127.0.0.1:8000`. To change it, copy
`.env.local.example` to `.env.local` and edit `NEXT_PUBLIC_API_URL`.

## Checking it

```bash
npm run build
```

A clean build also runs the TypeScript check.
