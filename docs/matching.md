# The Matching Engine

`backend/app/agent/matching.py`

There is no AI in this file, and that is deliberate. Specification section 10 says Gemini
must not do the mathematics or the geography itself. Gemini reads the request and explains
the outcome; this module decides who is eligible and who ranks highest, where it can be
tested.

## Eligibility filters

A worker is a candidate only if **all** of these hold:

| Filter | Where it comes from |
|---|---|
| Holds the requested skill, **verified** | `worker_skills.verification_status = 'verified'` |
| The worker themselves is verified | `workers.verification_status` |
| Free on the day | `availability` row with `status = 'available'` |
| Not already committed | no `job_assignments` row that day with status accepted/confirmed |
| Within travel distance | haversine distance ≤ search radius **and** ≤ the worker's own `travel_radius_km` |

Both distance limits are applied. A contractor searching 25 km does not override a worker
who will only travel 10.

A crew's **supply** is the number of its active members who personally hold the verified
skill and are free that day. It is never the crew's headcount, and never an inference from
the crew's rating — that would breach business rules 2 and 3.

## Ranking

```text
match_score = 0.30 × skill
            + 0.20 × availability
            + 0.20 × reliability
            + 0.15 × rating
            + 0.10 × proximity
            + 0.05 × experience
```

Weights are from specification section 10 and live in one dictionary, `WEIGHTS`, so they
are easy to change and easy to report. **They are prototype weights, not validated ones.**

Each part is normalised to 0–1:

| Part | How it is measured |
|---|---|
| `skill` | years of experience *in the requested skill*, full marks at 10 years |
| `availability` | how many of the 7 days from the job date the person is free |
| `reliability` | `reliability_score` ÷ 5 |
| `rating` | `average_rating` ÷ 5 |
| `proximity` | 1.0 at the site, falling linearly to 0.0 at the search radius |
| `experience` | total years, full marks at 15 |

Every candidate already passed the verified-skill filter, so `skill` measures *depth* in
that trade rather than whether they have it.

Ties break on supply, then on id, so the same request always produces the same order —
specification section 23 asks whether the agent is consistent on unchanged data, which is
unanswerable if ordering wobbles.

## Composition

Three passes, in order:

1. **Whole crews that fit.** Crews come first — a crew that already works together is
   easier to coordinate. But only crews whose members are *all* needed are taken.
2. **Individuals fill the remainder.** Specification section 15 fills the last positions
   with individual workers rather than breaking up a second crew.
3. **Partial crew, last resort.** Only if individuals ran out, so a request is filled when
   it possibly can be.

Everyone in a selected crew is marked as used, so **no one is ever counted twice**. Being
listed both as a crew member and again as an individual would overstate the workforce,
which business rule 1 forbids.

If the request cannot be filled, `shortfall` says by how much and `complete` is `false`.
The list is never padded.

## Trying it

```bash
curl "http://127.0.0.1:8000/api/match/workforce?skill=Mason&quantity=8&location=Guntur"
```

Current result against the seeded data:

```text
crew   Ravi Crew   +6   score 90.2   (6 of 6 available members)
worker Mahesh      +1   score 88.9   rating 4.6, 24 jobs
worker Ramesh      +1   score 85.6   rating 4.06, 17 jobs
filled 8/8, complete
```

Asking for 40 electricians instead returns `filled 1, shortfall 39, complete false`.

## Tests

- `backend/tests/test_matching_math.py` — distance, proximity, scoring bounds. No database
  needed.
- `backend/tests/test_matching_engine.py` — runs against real data: every returned worker
  is re-checked against the database for verification, skill and availability; nobody is
  counted twice; supplies add up to the reported total; an impossible request reports a
  shortfall; the same request twice gives an identical answer.
