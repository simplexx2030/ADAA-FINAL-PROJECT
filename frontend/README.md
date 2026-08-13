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
npm run dev --prefix frontend
```

Open <http://localhost:3000>.

The indicator in the top right says whether the backend is reachable. If it is red,
the backend is not running, and every page will say so rather than showing an empty
screen.

## The screens

| Page | What it is for |
|---|---|
| `/` | **Contractor dashboard** — who is available, which crews, recent jobs |
| `/assistant` | **AI assistant** — ask for workforce in plain language |
| `/crews`, `/crews/{id}` | **Crew dashboard** — members, and each member's *own* rating |
| `/workers`, `/workers/{id}` | **Worker profile** — reputation, skills, crew history, independence |
| `/sessions/{id}` | What the agent actually did, tool call by tool call |

## Two things the interface is careful about

**Every agent reply shows its provenance.** Under each answer is a row saying whether
it is *grounded in the database* and which tools ran. A chat bubble on its own is not
evidence — a language model can write a confident paragraph about eight masons who do
not exist. If no tool ran, the interface says so.

**A crew's rating is never shown as a member's rating.** The crew page puts the crew
rating and each member's own rating side by side, in adjacent columns, because keeping
those two apart is the point of the product.

## How it is put together

```text
frontend/
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
npm run build --prefix frontend
```

A clean build also runs the TypeScript check.
