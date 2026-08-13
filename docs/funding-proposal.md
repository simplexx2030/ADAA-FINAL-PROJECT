# ADAA

**A workforce coordination agent for construction labour in Andhra Pradesh**

Proposal for institutional funding of one AI agent · submitted to the Management Team
through the Department of Civil Engineering

---

## 1. Guide

| | |
|---|---|
| Name of Guide | Dr. P. Rakesh |
| Designation | Assistant Professor |

## 2. Student Details

| | |
|---|---|
| Name of Student | Simbarashe V. Chateya |
| Roll Number | 231FA03012 |
| Programme / Branch | B.Tech — Civil Engineering |
| Year | Final Year |
| Email | 231FA03012 |

---

## 3. Background and Need

Construction labour in Andhra Pradesh is arranged through mason leaders. A contractor who
needs eight masons on Tuesday morning telephones a mason leader he knows, and the mason
leader assembles the gang. Nothing is written down. The arrangement works, and it has worked
for a long time, which is the first thing any proposal to change it has to take seriously.

It has two costs, and they fall on different people.

The contractor's cost is search. He can only call the leaders whose numbers he has. If they
are booked, he does not know who else is free that morning, what they can do, or whether they
have turned up reliably for anyone else. Filling a gang is a sequence of phone calls with no
visibility, and a gap on site is expensive in a way that is hard to recover.

The worker's cost is heavier and less visible. **A worker's reputation is not his own.** Ten
years of good work is known to his mason leader and to nobody else. It does not travel. If he
leaves the crew — because he moves, because he falls out with the leader, because he wants to
take work directly — he starts again at zero. There is no record he can show a new contractor,
because the record was never his. That, rather than the inefficiency, is what keeps a skilled
worker permanently dependent on one intermediary.

Preliminary fieldwork in Guntur district suggests the mason leader performs several distinct
functions at once: matchmaker, paymaster, translator, insurance bridge and crew coordinator.
*These findings are preliminary and are not presented as statistically representative.* They
matter because they explain why the obvious digital answer — a labour marketplace that removes
the middleman — is the wrong answer. Remove him and the functions do not disappear; they land
on people who cannot perform them. Existing gig-work platforms also tend to reduce a worker to
a rating inside the platform, which reproduces the same dependency in a new place.

ADAA takes the opposite approach. It **digitises the mason leader rather than replacing him**.
He becomes a recognised Crew Leader, and eventually a Subcontractor, with a crew reputation of
his own. At the same time every worker gets an ADAA identity that belongs to them, so that a
worker's history follows the worker and not the crew.

---

## 4. Objectives of the Model

ADAA takes a workforce request written in ordinary language and returns a specific, verified
workforce with the evidence behind every name. A request enters as a sentence and leaves as a
list of real people who are genuinely qualified and genuinely free.

- **Understand the request.** Read *"I need 8 masons tomorrow at 8 AM near Guntur"* and
  extract trade, quantity, date, time, location and wage. Ask a short question when something
  essential is missing rather than assuming it.

- **Find who is actually eligible.** Filter on verified skill, verified worker, availability
  on the day, no existing commitment, and travel distance — checking both the search radius
  and how far that particular worker is willing to travel.

- **Compose a workforce from crews and individuals.** Prefer a crew that already works
  together, then fill the remaining positions with individual workers. Nobody is counted
  twice, and a shortfall is reported rather than padded.

- **Explain the recommendation.** Give the rating, completed jobs, attendance and distance
  behind every name, so a contractor can judge for himself instead of trusting a score.

- **Coordinate the job.** Carry a job from request through offers, responses and confirmation.
  Consequential steps are proposed by the agent and carried out only when a person confirms.

- **Build reputation that belongs to the worker.** Count completed jobs, ratings, attendance
  and reliability from what actually happened. **Keep worker and crew reputation separate**,
  and preserve a worker's full history when they leave a crew. This is the central objective;
  everything else is coordination.

- **Support the progression to independence.** Assess whether a worker's verified history
  supports independent work, and say so as a recommendation. *The system recommends; the
  worker decides.* ADAA cannot change anybody's status.

- **Work in the language the user speaks.** English, Telugu and Hindi, with wages, quantities,
  dates and job numbers taken from the database rather than from the translation.

---

## 4.1 How the System Works

The clearest way to describe ADAA is to follow one request through it. What follows is the
actual behaviour of the built system against its test dataset, not an illustration.

**Stage 1 — the request arrives in ordinary language.**
A contractor types or speaks: *"I need 8 masons tomorrow at 8 AM near Guntur."* Gemini reads
it and returns the facts it can find: trade `Mason`, quantity `8`, location `Guntur`, and the
words `"tomorrow"` and `"8 AM"`.

**Stage 2 — the application fixes the values that matter.**
The model does **not** work out what date "tomorrow" is. It hands back the word, and Python
converts it to a calendar date, normalises `"8 AM"` to `08:00`, and reduces `"near Guntur"`
to the place name `Guntur`. A wrong date sends eight people to a site on the wrong morning,
so dates, times, quantities and wages are decided by code that can be tested. If a phrase
cannot be understood — *"sometime next week"* — it is reported as missing and the contractor
is asked, rather than guessed at.

**Stage 3 — eligibility, entirely without the model.**
The matching engine queries the database. A worker is a candidate only if *every* condition
holds: the trade is held as a **verified** skill, the worker himself is verified, the
availability table says he is free that day, he is not already committed to another job, and
the site is within both the search radius and his own stated travel distance. Anyone failing
any condition is not returned at all, so the model never sees an ineligible name and cannot
recommend one.

**Stage 4 — ranking, from a stated formula.**
Each candidate is scored on six factors — depth in the trade, availability, reliability,
rating, proximity and experience — combined with published weights. The weights are prototype
values, and the system says so wherever it reports a score.

**Stage 5 — composing the gang.**
Whole crews first, because a crew that already works together is easier to coordinate, then
individual workers for the remaining positions. Every member of a selected crew is marked as
used, so nobody is counted twice. The current result for this request is:

```text
Ravi Crew   6 workers    (6 of 6 available verified masons)
Bhaskar     1 worker     4.5 rating · 27 jobs · 91% attendance
Mahesh      1 worker     4.6 rating · 24 jobs · 93% attendance
                         8 of 8 positions filled
```

Ask instead for forty electricians and the answer is *"filled 1, shortfall 39"*. **The list is
never padded to reach the number requested.**

**Stage 6 — the explanation.**
Gemini receives the tool's result and writes the reasoning in the contractor's language,
using the ratings, job counts and attendance figures the tool supplied. Every reply records
which tools ran; a reply with no tool behind it is flagged as ungrounded, so an answer that
merely sounds confident can be told apart from one built on records.

**Stage 7 — coordination, with a person in control.**
The agent can *propose* creating the job and *propose* sending offers. It cannot do either.
Each proposal is written down and returns an identifier; the work happens only when a person
confirms it. Asked directly to *"go ahead and do it"*, the built system replies that nothing
has been created and gives the confirmation identifier. **There is deliberately no tool that
lets the model approve its own proposal** — if there were, the confirmation rule would be a
suggestion rather than a rule. Offers, responses and final confirmation follow the same
pattern, and a confirmed worker is marked booked so he stops being offered elsewhere that day.

**Stage 8 — reputation, counted from what happened.**
When the job is completed, attendance is recorded as days worked against days booked, and
every reputation figure is **recounted from the records**: completed jobs from assignment
rows, average rating from rating rows, attendance from day counts. Nothing is typed in. A
verification endpoint recomputes every figure for every worker and reports any disagreement;
it returns nothing, and a test enforces that.

Two rules are enforced in the database queries rather than in instructions to the model. A
worker's rating is computed only from ratings addressed to that worker, and a crew's only from
ratings addressed to that crew, so **a crew rated 4.8 does not make its members 4.8 workers**.
And neither query ever consults crew membership, which is precisely what allows a worker to
leave a crew and keep everything he has earned.

**Stage 9 — the independence pathway.**
On request, the system assesses whether a worker's verified history supports independent work,
using completed jobs, rating, attendance, reliability and the number of different contractors
he has worked for. It returns a score, the evidence, and a recommendation — and it changes
nothing. Asked to *"make him independent"*, the built system answers that it cannot: the
decision rests with the worker, and his crew membership is unaffected either way.

---

## 5. Tools Used for Developing the Model

The system is built from open and widely available components. The environment is fixed, and
the sample dataset is generated from a fixed random seed, so a result can be reproduced by
someone else.

| Function | Tool | Role in the system |
|---|---|---|
| Language and version control | Python 3.14, Git | Building the system and keeping a clean history |
| Application and API | FastAPI, Uvicorn | Serving the agent and the business logic |
| **Reasoning layer** | **Google Gemini, via the Google GenAI SDK** | **Understanding requests, choosing which tools to call, explaining recommendations, multilingual interaction** |
| Database | PostgreSQL 17 (Supabase, Mumbai region) | Workers, crews, jobs, availability, ratings, audit trail |
| Database driver | psycopg 3 | Application-to-database access |
| Matching and geography | Plain Python (haversine, weighted scoring) | Distance, eligibility and ranking — deliberately not the model's work |
| Testing | pytest | 222 automated tests, run on every change |
| Interface | Next.js, React, Tailwind CSS | Contractor dashboard, assistant, crew and worker screens |

### The AI model, and why it is separated from the rest

The reasoning layer is **Google Gemini**, reached through the official Google GenAI SDK. The
exact model is set by an environment variable (`GEMINI_MODEL`) and is never written into the
code, so the system is not locked to any one model. Development and testing have been carried
out on `gemini-3.5-flash`; `gemini-3.1-pro-preview` is the intended production model and
requires paid access.

The design principle throughout is:

> **Gemini reasons; the ADAA application verifies and executes.**

| The model does | The application does |
|---|---|
| Understand natural language | Calculate distance |
| Decide which tool is needed | Check availability |
| Interpret what a tool returned | Calculate match scores |
| Explain a recommendation | Enforce the business rules |
| Support Telugu, Hindi and English | Read and write the database |

This split is not stylistic. It is what makes the system safe enough to put in front of a
contractor and testable enough to evaluate. The parts that must be correct — who is eligible,
who is available, what a worker's record says — are ordinary Python with tests, and they give
the same answer whether or not the model is available at all. The model is never permitted to
assert a fact about a worker; it may only report what a tool returned. Every reply records
which tools actually ran, and a reply with no tool behind it is marked as ungrounded.

### Funding request

**Metered access to the Gemini API is the only recurring cost in this project, and it is the
item for which support is sought.** Every other tool listed above is free or open source.

The need is specific and has been measured during development. The free tier permits
**20 requests per day per model and 5 per minute**. A single question that uses a tool costs
two requests, so the free allowance is roughly **ten questions per day**. That is enough to
build the system. It is not enough to evaluate it: the evaluation in Section 6 requires the
same scenarios run repeatedly, across three languages, against a baseline, and a consistency
check that by definition means asking the same question many times. The project has reached
the point where the free tier is the binding constraint on measurement rather than on
construction.

The project also requires field access rather than money: contractors and mason leaders in
Guntur district willing to be interviewed and to trial the system, and permission to record
anonymised coordination outcomes for the baseline comparison.

---

## 6. Outcomes of the Model

The system is built as separate modules, each of which can be tested on its own. The backend
modules below are complete and covered by 222 automated tests.

| Module | Component | Outcome produced | Status | Risk |
|---|---|---|---|---|
| M-01 | Request Understanding | A structured workforce request from a plain sentence, with missing details queried rather than assumed | Built | Low; dates and quantities are resolved by the application, not the model |
| M-02 | Matching Engine | A ranked, filtered set of genuinely eligible workers and crews | Built | Low; deterministic and independently tested |
| M-03 | Workforce Composition | A complete workforce combining crews and individuals, or an honest shortfall | Built | Low |
| M-04 | Job Coordination | A job carried from request to confirmed workers, with confirmation required at each consequential step | Built | Medium; notifications are simulated pending a messaging channel |
| M-05 | Reputation | Worker and crew records updated from completed work, kept separate from each other | Built | Low |
| M-06 | Independence Readiness | A score, the evidence behind it, and a recommendation the worker is free to decline | Built | Medium; the weights are a first estimate and are not validated |
| M-07 | Multilingual Layer | English, Telugu and Hindi, with critical values protected from translation | Planned | Medium; Telugu construction vocabulary needs field checking |

The intended deliverables are:

- **A measurement of coordination performance against the current practice.** Time to first
  acceptance, time to fill a gang, acceptance rate, no-show rate and communication failures,
  compared against telephone-and-WhatsApp coordination. *No improvement is claimed until it
  is measured.*

- **A grounding and consistency measurement for the agent.** What proportion of the agent's
  statements about workers can be traced to a database record, and whether the same request
  returns the same decision when the underlying data has not changed. The system records
  every tool call it makes, with its arguments and result, specifically so that this can be
  measured rather than asserted.

- **A demonstrated mechanism for portable worker reputation.** A worker leaves a crew and
  retains every completed job, rating, verified skill and attendance record — shown on
  records rather than described as a policy. This is the contribution that distinguishes ADAA
  from a labour marketplace.

- **A working demonstration** in which a contractor's spoken request is turned into a
  verified workforce, a job is coordinated to confirmation, and a worker's independence
  readiness is assessed — end to end, without terminal commands.

- **A data schema and matching engine for construction workforce coordination** that the
  department can continue to use after the project ends.

### Limits

The scoring weights, for both matching and independence readiness, are prototype values and
are **not scientifically validated**; they are stated openly wherever they are reported.
Development uses a generated dataset of 32 workers and 5 crews in Guntur district — the
structure is real, the people are not, and field data replaces it before any measurement is
claimed. The system does not handle payments, payroll, insurance or materials. It advises and
coordinates; it never hires anyone, and it cannot change a worker's employment status. Quantity
surveying and rate estimation are outside its scope.

---

## 7. Conclusion

The mason leader system is not a problem to be solved. It is an arrangement that works, held
together by relationships and memory, and it fails only in the two places where memory cannot
reach: a contractor cannot see beyond the numbers in his phone, and a worker cannot take his
record with him when he leaves.

ADAA addresses both without dismantling what already functions. The mason leader becomes a
recognised crew leader with a reputation of his own. The worker gets an identity and a history
that belong to him, so that ten years of reliable work becomes something he can show to a
contractor who has never met him. The progression from crew member to independent worker to
crew leader stops depending on one person's goodwill.

The project is scoped so that each module is testable on its own, and the central claim rests
on a measurement rather than a demonstration: whether a worker's reputation genuinely survives
leaving a crew, and whether the agent's statements can be traced to records. The backend is
complete and tested. Metered access to the Gemini API is the one input the project cannot
supply for itself, and it is now the binding constraint on measuring the system rather than on
building it.

---

## 8. Photograph of the Model

The system architecture is shown below. A workforce request enters at the left as a sentence
in plain language and leaves at the right as a confirmed workforce with the evidence behind
every name. The shaded stage is the only one that uses a language model; every other stage is
a fixed calculation against the database. The seven modules and the data they draw on are
shown beneath.

*Figure 1 · ADAA system architecture — request-to-confirmation pipeline and seven-module
component specification*

---

| | |
|---|---|
| **Signature of Student** | Simbarashe V. Chateya |
| **Signature of Guide** | Dr. P. Rakesh |
| **Head of the Department** | Civil Engineering |
