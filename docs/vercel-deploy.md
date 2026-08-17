# Deploying ADAA to Vercel

One Vercel project serves the whole application: the Next.js pages and the
FastAPI backend share a single domain. There is no second URL to configure and
no cross-origin request to permit.

This document is the checklist for deploying into the **existing `adaa-three`
project**, so the address `https://adaa-three.vercel.app` stays exactly as it is.

---

## Before you start

You need to be signed in to Vercel as **chateya@mowtechnologies.co.zw**. That is
the account that owns `adaa-three`. Signing in as any other account will not show
the project, and creating a new one would produce a different address.

Have these three values to hand:

| Variable | Where it comes from |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio — the same key as in your local `.env` |
| `GEMINI_MODEL` | `gemini-3.5-flash` (see the note at the end) |
| `DATABASE_URL` | Supabase — **transaction pooler**, see step 3 |

---

## Step 1 — Connect the repository

`adaa-three` was created by uploading files, so it has no Git connection yet.
Connecting one means every future `git push` redeploys automatically, and you
never upload files by hand again.

1. Open the project → **Settings** → **Git**
2. **Connect Git Repository** → GitHub → `victorsimba189-lab/Adaa-ai-agent`
3. Production branch: **`main`**

## Step 2 — Check the build settings

Still in **Settings** → **Build and Deployment**.

**Root Directory must be empty.** This is the setting most likely to be wrong,
because the first MVP was a flat upload. It must point at the repository root,
not at `frontend/`. If it is set to `frontend/`, the Python function is never
built and every `/api/*` request returns 404 — the pages will load and nothing
on them will have any data.

Leave the build commands alone. `vercel.json` at the repository root already
specifies them, and it overrides whatever the dashboard shows:

```
installCommand    npm install --prefix frontend
buildCommand      npm run build --prefix frontend
outputDirectory   frontend/.next
```

## Step 3 — Add the environment variables

**Settings** → **Environment Variables**. Add all three to **Production**
(and to Preview as well, if you want preview deployments to work).

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | your Google AI Studio key |
| `GEMINI_MODEL` | `gemini-3.5-flash` |
| `DATABASE_URL` | the Supabase connection string — see below |

For `DATABASE_URL`, use Supabase's **transaction pooler on port 6543**, not the
session pooler on 5432 that development uses:

```
postgresql://postgres.plqpwsnylgpecdlcftqs:YOUR-PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

Copy it from **Supabase → Project Settings → Database → Connection string →
Transaction pooler** rather than typing it, and put your real password in place
of the placeholder. Paste it exactly as Supabase gives it: square brackets and
awkward characters in the password are repaired automatically by
`normalize_database_url` in `backend/app/database.py`.

Why the transaction pooler: each request runs in a short-lived serverless
function that opens a connection and closes it again. The session pooler holds
one connection per client, which is the wrong shape for that and will exhaust
the connection limit under any real use.

## Step 4 — Deploy

**Deployments** → **Redeploy**, or simply push to `main` once the Git connection
from step 1 is in place.

The first build takes a few minutes: Vercel installs the Node dependencies,
builds Next.js, then installs the Python dependencies from the root
`requirements.txt` for the function in `api/index.py`.

## Step 5 — Verify, in this order

Each check isolates a different layer, so a failure tells you where to look.

1. **`https://adaa-three.vercel.app/api/health`** → `{"status": "ok"}`
   The Python function is deployed and routing works. If this 404s, Root
   Directory is wrong (step 2).

2. **`https://adaa-three.vercel.app/api/health/database`** → a worker count
   Supabase is reachable. If this fails and the one above passed, `DATABASE_URL`
   is wrong or is using the 5432 session pooler.

3. **`https://adaa-three.vercel.app/`**
   The landing page shows real workers and, in the sidebar, the model name. Both
   come from the API, so if they render, the frontend is talking to the backend.

4. **The AI Assistant page** — ask one question.
   This is the only check that spends Gemini quota, so leave it until last.

If something is wrong, the deployment's **Runtime Logs** in the Vercel dashboard
show the Python traceback.

---

## Two things worth knowing

**The reply cache is weaker in production.** Locally it persists in
`backend/.cache`. On Vercel the filesystem is read-only apart from `/tmp`, which
belongs to one warm function and disappears with it. So the cache still saves
quota within a burst of questions but not between sessions. See
`backend/app/agent/cache.py`.

**Check which model you are deploying.** `CLAUDE.md` records `gemini-3.5-flash`
as the decision, but the local `.env` has been running `gemini-3.1-flash-lite`.
Free-tier quota is 20 requests per day *per model*, so these are separate
allowances — decide which one production should use before a demonstration
rather than during one.

**Rolling back.** Every previous deployment, including the original MVP, stays in
the project's **Deployments** list. Promoting an older one back to production is
a single click, and the domain follows it. Deploying does not delete anything.
