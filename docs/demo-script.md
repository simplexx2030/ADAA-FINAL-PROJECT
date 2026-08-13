# Demonstration Script

The six scenarios from section 21 of the build specification. Target length **5–10 minutes**.

---

## ⚠️ Read this first: the free-tier limit

The Gemini free tier is **much tighter than it looks**, and it is the most likely thing to
go wrong in front of an audience.

| Limit | Value (free tier) |
|---|---|
| Requests per **minute** | 5 |
| Requests per **day**, per model | **20** |

And one question is not one request. When the agent uses a tool, it costs **two** requests:
one where Gemini asks for the tool, one where it answers using the result. So:

> **Six demo scenarios ≈ 12–15 requests. The daily allowance is 20.**

You get roughly **one full rehearsal and one live run per day, per model.**

### How to protect the demo

1. **Do not rehearse on the model you will present with.** Each model has its **own separate
   daily allowance**. Rehearse on one, present on another.
   Confirmed working on this key: `gemini-3.5-flash`, `gemini-3.1-flash-lite`,
   `gemini-3.5-flash-lite`, `gemini-flash-latest`, `gemini-3.6-flash`.
2. **Switch models by editing one line** in `.env` — no code change, no restart of anything
   but the server:
   ```env
   GEMINI_MODEL=gemini-3.6-flash
   ```
3. **Have a fallback.** Scenarios 1, 2 and 3 can be shown through
   `/api/match/workforce` and `/api/crews/RAVI01`, which use **no Gemini at all** and have
   no limit. If the quota dies mid-demo, switch to those and explain that the matching
   engine is deliberately independent of the LLM — which is true, and is one of the
   stronger points of the design.
4. The allowance resets after **midnight Pacific time**.

If it does run out, the agent says so in plain language rather than crashing.

---

## Before you start

```bash
backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
```

Check `/health` and `/health/database` both respond. Open `/docs` — that is where you will
run the agent from, using `POST /api/agent/chat`.

Have these open in browser tabs so you never have to type during the demo:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/crews/RAVI01`
- `http://127.0.0.1:8000/api/workers/W001`
- `http://127.0.0.1:8000/api/match/workforce?skill=Mason&quantity=8&location=Guntur`

---

## Scenario 1 — Understanding a request and composing a workforce

> **"I need 8 masons tomorrow at 8 AM near Guntur."**

**What to point out:** the agent called `recommend_workforce`. Check `tools_used` in the
response — it names every tool that actually ran. `grounded: true` means at least one claim
traces to a database row.

Expected shape of the answer:

```text
Ravi Crew    6 workers   (6 of 6 available verified masons)
+ 2 individual workers
Total 8, complete
```

**The line worth saying out loud:** *Gemini did not choose these people. It called a
deterministic Python function that applied the eligibility rules, and then explained the
result.*

---

## Scenario 2 — Crew coordination

> **"Can Ravi's crew handle it?"**

Send this with the previous exchange in `history`, or it will ask what "it" refers to —
which is itself correct behaviour worth showing if it happens.

The agent calls `get_crew_profile` or `check_availability`. Expected: Ravi Crew has **6
available verified masons**, so it covers 6 of the 8 positions and two individuals are
needed.

**Point out:** the crew's rating (4.8) is reported separately from each member's own rating.
A crew rated 4.8 does not make every member a 4.8 worker — that is business rule 3.

---

## Scenario 3 — Filling the remaining positions

> **"Find individual workers to fill the remaining positions."**

The agent calls `search_workers`. Every worker returned is verified, holds masonry as a
**verified** skill, and is free tomorrow according to the availability table.

**Good moment for the honesty demo.** Ask instead:

> **"I need 40 electricians in Guntur tomorrow."**

The agent reports the shortfall and suggests widening the radius or changing the date. It
does not invent 40 electricians. That is business rules 1 and 9 working.

---

## Scenario 4 — Independence readiness

> **"Is Suresh ready to work independently?"**

The agent calls `get_worker_profile("W001")`. Evidence in the database:

| | |
|---|---|
| Completed jobs | **31** |
| Average rating | **4.70** |
| Attendance | **96%** |
| Verified skill | Mason |
| Current crew | Ravi Crew |
| Contractors worked for | 5 different firms, with repeat work |

**The important sentence:** this is a **recommendation, not a status change**. The AI
recommends; Suresh decides. That is business rule 5.

**If challenged on where the numbers come from** — this is the question to hope for. Open:

```
http://127.0.0.1:8000/api/workers/W001
```

The 31 jobs and the 4.70 rating are **not typed into the worker record**. They are counted
from 31 rows in `job_assignments` and averaged from 31 rows in `ratings`. Every number is
traceable. (The full scoring tool, `check_independence_readiness`, is STEP 9 — not built
yet. Say so; do not imply otherwise.)

---

## Scenario 5 — Reputation preservation

> **"What happens to Suresh's reputation if he leaves Ravi's crew?"**

The best answer here is not hypothetical — **it has already happened to someone in the
data.** Show Bhaskar (`W014`), who left Ravi Crew six months ago:

```
http://127.0.0.1:8000/api/workers/W014
```

- `crew_history` still shows Ravi Crew, with `status: left` and a `left_at` date
- his 27 completed jobs and 4.50 rating are **still his**
- his verified masonry skill is untouched
- he now appears in searches as an independent worker

**The design point:** `crew_members` is a *relationship*, not an identity. Leaving sets an
end date. Nothing is deleted. That is business rule 4, and it is the heart of the whole
product idea.

---

## Scenario 6 — A worker becomes a subcontractor

> **"Suresh has created his own crew. How should ADAA represent him?"**

Expected answer: Suresh keeps his individual record and reputation. A **new crew** is
created with him as leader. The crew builds its **own** reputation from its own jobs. The
two never merge.

**Be honest here:** creating a crew is a write action, and no write tools exist yet
(STEP 7). The agent should explain the model rather than claim it did it. If it claims it
did it, that is a bug worth reporting — business rule 9.

---

## Scenario 7 (optional) — Actually booking the crew

Only if you have time, and only after scenario 1. This shows the full loop and the
confirmation rule, which is one of the more defensible parts of the design.

> **"Create that job for contractor CON001 and go ahead."**

The agent calls `propose_job` and answers with something like:

```text
I have prepared the proposal... **Nothing has been created yet.**
To proceed, please confirm this action using the following ID: act_ca85d67f2116
```

**Say this out loud:** it was told "go ahead" and it still did not do it. The agent has
**no tool that can confirm its own proposal** — that is enforced in code, not asked for in
the prompt. Business rule 7.

Then confirm it yourself, in `/docs`:

```
POST /api/actions/{action_id}/confirm
```

Now the job exists. Offers, responses and confirmation follow the same pattern:

| Step | Endpoint |
|---|---|
| Offer the job | agent proposes → you confirm |
| Worker answers | `POST /api/offers/{assignment_id}/respond` |
| Confirm workers | `POST /api/jobs/{job_id}/confirm` → confirm the action |

**The detail worth pointing at:** once workers are confirmed, they are marked `booked`, so
`/api/match/workforce` stops offering them for anything else that day. Business rule 1 holds
after the booking, not just before it.

> ⚠️ **This changes the data.** Confirming Ravi Crew books all seven members and the
> 8-mason scenario will stop working. Run `seed_database.py` afterwards to reset.

---

## The strongest thing you can show

After running the scenarios, open the audit trail for the session:

```
http://127.0.0.1:8000/api/agent/sessions/{session_id}
```

Pass a `session_id` in your first chat request (or copy the one the reply returns) and every
question stays in one trail. You get a row per tool call:

```text
tool_call   recommend_workforce   938ms  ok   {"skill":"Mason","location":"Guntur","quantity":8}
chat                             4689ms  ok   {"message":"I need 8 masons tomorrow..."}
tool_call   get_crew_profile      616ms  ok   {"crew_id":"RAVI01"}
chat                             3178ms  ok   {"message":"Can Ravi's crew handle it?"}
```

This is the difference between saying the agent uses real data and **showing** it. It is also
what specification section 24 asks for, and it is the evidence base for the evaluation
chapter.

`GET /api/agent/tool-usage` summarises the same thing across all sessions: which tools get
called, how often, and how often they fail.

---

## Saving quota while you rehearse

Replies are cached. Asking the same question twice costs Gemini nothing the second time —
the reply comes back with `"cached": true` and in about 0.3 seconds instead of 5.

The cache invalidates itself if the workforce data changes or the day rolls over, so it can
never hand back a stale answer about who is available. To force fresh answers:

```
DELETE /api/agent/cache
```

**This roughly halves what a rehearsal costs.** Run through the scenarios once to fill the
cache, and a second pass is free.

---

## If a professor asks the hard questions

**"How do you know it isn't making the workers up?"**
Every reply carries `tools_used`. If it is empty, `grounded` is false and nothing came from
the database. Then open the session trail and show the actual tool calls. Also:
`/api/match/workforce` returns the same composition with no LLM in the loop at all.

**"What stops it from saying an unavailable worker is free?"**
Availability is a database table, and the only thing that reads it is a Python function
with tests. The model never decides availability. Show `backend/app/agent/matching.py`.

**"Are the weights in the match score justified?"**
No — and the code says so in a comment. They are prototype weights from the specification,
kept in one dictionary so they can be changed and reported. Validating them is future work.

**"Where did the data come from?"**
It is generated dummy data for the prototype, from `backend/scripts/generate_data.py`, with
a fixed random seed so it is reproducible. Real fieldwork data replaces it later. The
*structure* is real; the people are not.

**"Why Gemini and not ChatGPT/Claude?"**
The specification fixes Gemini as the ADAA LLM. The model name is an environment variable,
so the system is not locked to any one model — that was a deliberate design decision, not
an accident.
