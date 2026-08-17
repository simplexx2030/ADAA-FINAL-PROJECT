# Deploying ADAA to Vercel

One Vercel project serves the whole application: the Next.js pages and the
FastAPI backend share a single domain. There is no second URL to configure and
no cross-origin request to permit.

---

## Before you start

**The repository is `simplexx2030/ADAA-FINAL-PROJECT`.** The earlier remote,
`victorsimba189-lab/Adaa-ai-agent`, is abandoned — that GitHub account is not
accessible, and Vercel refuses to deploy a personal-account repository unless the
connected GitHub login *owns* it. Collaborator access is not enough. The old
remote is still configured locally as `old-origin`, for reference only.

**Your Vercel account's GitHub connection must be `simplexx2030`.** Check it at
**Vercel → Settings → Authentication**. A Vercel account links to exactly one
GitHub login and there is no way to add a second, so if it shows a different
account the only fix is a new Vercel account signed in with `simplexx2030`.

Have these three values to hand:

| Variable | Where it comes from |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio — the same key as in your local `.env` |
| `GEMINI_MODEL` | `gemini-3.5-flash` (see the note at the end) |
| `DATABASE_URL` | Supabase — **transaction pooler**, port 6543, see step 3 |

---

## Step 1 — Connect the repository

Project → **Settings** → **Git** → **Connect Git Repository** → GitHub →
`simplexx2030/ADAA-FINAL-PROJECT`, production branch **`main`**.

Every push to `main` then redeploys on its own, and nothing is ever uploaded by
hand again.

## Step 2 — Check the build settings

**Settings** → **Build and Deployment**.

**Root Directory must be empty.** It must point at the repository root. There is
no longer a `frontend/` directory to point it at, and setting it to anything else
means the Python function is never built and every `/api/*` request returns 404 —
the pages would load with no data on them.

There are no build commands to configure. The Next.js application is at the
repository root, so Vercel's defaults are correct: `npm install` and `next build`.

`vercel.json` does pin `outputDirectory` to `.next`, even though that is the
default. This is deliberate. A project imported while the application still lived
in `frontend/` has `frontend/.next` **stored in its dashboard settings**, and a
dashboard setting applies whenever `vercel.json` is silent. The result is a build
that compiles perfectly and then fails with:

```
Error: The Next.js output directory "frontend/.next" was not found
```

Settings in `vercel.json` take precedence over the dashboard, so pinning the value
in the repository fixes it for every project, present and future, without anyone
having to find the right settings page.

### Why the Next.js application is at the repository root

It used to live in `frontend/`, and moving it back would break deployment.
Vercel decides whether a project is Next.js by resolving the **installed** `next`
package in the Root Directory. With the application in a subdirectory,
`npm install --prefix frontend` put Next.js in `frontend/node_modules`, so the
build failed here every time:

```
Error: No Next.js version detected.
```

Declaring `next` in a root `package.json` while leaving the application in
`frontend/` was tried and does **not** work — the builder wants the installed
package, not the declaration. Moving the application up is the fix, and it is
also the layout Vercel's own Next.js + Python template uses.

## Step 3 — Add the environment variables

**Settings** → **Environment Variables**. Add each to **Production** and
**Preview**.

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | your Google AI Studio key |
| `GEMINI_MODEL` | `gemini-3.5-flash` |
| `DATABASE_URL` | the Supabase transaction-pooler string — see below |

**Add nothing else.** Vercel will offer to create a row for every name it finds
in `.env.example`, including `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`,
`GEMINI_CACHE` and `APP_ENV`. Delete those rows.

### Never leave a variable blank

An empty value is *not* the same as an unset one — pydantic uses the empty
string instead of the default in `app/config.py`. The consequences differ:

- **`GEMINI_CACHE=`** — empty fails `bool` parsing. Because `settings =
  Settings()` runs at import, the whole application fails to load and **every
  route returns 500, including `/api/health`.** An empty text box takes down the
  entire backend.
- **`GEMINI_MODEL=`** — an empty model name, so every Gemini call fails.
- **`APP_ENV=`** — harmless, but pointless.

If you do not need a variable, remove the row rather than leaving it empty.

### `GEMINI_MODEL` is not optional

It has a default, so it looks safe to skip. The default is
`gemini-3.1-pro-preview`, which the free tier grants **zero** quota, so skipping
it means every agent reply fails with 429. Locally your `.env` hides this. Set it
explicitly.

### `DATABASE_URL` uses a different port here than in development

Use Supabase's **transaction pooler on port 6543**, not the session pooler on
5432 that development uses:

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
the connection limit under any real use — including during a demonstration.

## Step 4 — Deploy

**Deployments** → **Redeploy**, or push to `main`.

Vercel will not apply newly added environment variables to an existing
deployment, so after step 3 you must redeploy even if nothing in the code
changed.

The first build takes a few minutes: Node dependencies, then Next.js, then the
Python dependencies from the root `requirements.txt` for the function in
`api/index.py`.

## Step 5 — Verify, in this order

**Use the short production URL, not the long one from the deployment page.**
Deployment Protection is set to *Standard Protection*, which on the Hobby plan
leaves the production domain public but protects every **generated** deployment
URL — the `project-a1b2c3d4.vercel.app` kind. Those demand a Vercel login, so
`curl` against one returns an HTML sign-in page instead of JSON and looks exactly
like a broken API. Standard Protection is the right setting; just test the right
address.

Each check isolates a different layer, so a failure tells you where to look.

1. **`/api/health`** → `{"status": "ok"}`
   The Python function is deployed and routing works. A 404 means Root Directory
   is wrong (step 2). A 500 means the application failed to import — check for a
   blank `GEMINI_CACHE` first.

2. **`/api/health/database`** → a worker count
   Supabase is reachable. If this fails and the one above passed, `DATABASE_URL`
   is wrong or is still using the 5432 session pooler.

3. **`/`**
   The landing page shows real workers and, in the sidebar, the model name. Both
   come from the API, so if they render, the frontend is talking to the backend.

4. **The AI Assistant page** — ask one question.
   This is the only check that spends Gemini quota, so leave it until last. A 503
   here with the first three passing points at `GEMINI_API_KEY` or
   `GEMINI_MODEL`.

The deployment's **Runtime Logs** show the Python traceback when something fails.

---

## Things worth knowing

**Do not set `NEXT_PUBLIC_API_URL`.** `lib/api.ts` falls back to an empty string
in production, which makes the browser call `/api/...` on the same domain. That is the entire point of the single-project layout. Setting it sends
requests elsewhere and reintroduces CORS.

**The reply cache is weaker in production.** Locally it persists in
`backend/.cache`. On Vercel the filesystem is read-only apart from `/tmp`, which
belongs to one warm function and disappears with it, so the cache saves quota
within a burst of questions but not between sessions. `backend/app/agent/cache.py`
already detects Vercel and adapts; nothing to configure.

**Check which model you are deploying.** Free-tier quota is 20 requests per day
*per model*, so `gemini-3.5-flash` and `gemini-3.1-flash-lite` have separate
allowances. Decide which one production should use before a demonstration rather
than during one.

**Rolling back.** Every previous deployment stays in the project's
**Deployments** list. Promoting an older one back to production is a single click
and the domain follows it. Deploying does not delete anything.
