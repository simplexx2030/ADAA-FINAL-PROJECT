# PRODUCT.md — What ADAA Is

Condensed from sections 1–3 of the build specification. The spec remains the source of truth.

---

## Mission

> Connect construction workforce demand with suitable workers, crews and subcontractors while
> helping every worker build an independent professional reputation.

## The core idea

ADAA should **not** simply eliminate the existing mason-leader system. It should **digitise
the useful parts** of the construction workforce network that already exists.

A mason leader becomes a recognised **Crew Leader / Subcontractor**. Workers remain members of
a crew *while also* having their own ADAA identity and individual reputation.

### The progression ladder

```text
Crew Member
    ↓
Verified Worker
    ↓
Independent Worker
    ↓
Crew Leader
    ↓
Subcontractor
```

Historical worker reputation stays attached to the **individual worker**, never absorbed by
the crew. This is the single most important product idea in ADAA.

---

## Fieldwork context

Initial fieldwork found that mason leaders may act as: matchmaker, paymaster, support and
insurance bridge, translator, and crew coordinator.

> These findings are preliminary and must not be presented as statistically representative.

ADAA preserves the useful coordination functions while digitising: worker identity,
availability, skills, job history, ratings, crew membership, crew reputation, and contractor
relationships.

---

## Users

### Contractor
Posts workforce requirements (skill, quantity, site, date/time, wage), receives workforce
recommendations, confirms workers and crews, rates completed work.

### Crew Leader / Mason Leader / Subcontractor
Creates a crew, adds workers, manages crew availability, receives and accepts or declines job
requests, coordinates members, maintains crew reputation, and eventually receives larger
subcontracting opportunities.

### Crew Member
Maintains an individual profile, belongs to a crew, receives job information, accepts work,
builds an independent work history, accumulates individual ratings, and becomes eligible for
independent work over time.

### Independent Worker
Accepts jobs directly, maintains personal reputation and availability, builds contractor
relationships, and may eventually create and manage a crew.

### Admin
Verifies users, manages skills, monitors jobs and agent actions, resolves disputes, monitors
system performance.

---

## What the agent does

1. **Understands requests** — turns *"I need 8 masons tomorrow at 8 AM near Guntur"* into
   structured data.
2. **Identifies missing information** — asks concise clarification questions.
3. **Searches workforce** — individuals, crews, subcontractors.
4. **Applies eligibility rules** — skill, availability, location, travel radius, current
   assignments, verification, reliability.
5. **Composes workforce** — may combine crew + crew, crew + individuals, individuals only, or
   subcontractor + individuals.
6. **Explains recommendations** — why each candidate, what evidence, what limitations.
   Never invents qualifications or availability.
7. **Coordinates communication** — job offers, responses, confirmation.
8. **Updates reputation and history** — after job completion.
9. **Recommends worker progression** — the AI recommends, **the user decides**.

---

## Explicit non-goals for version 1

Not being built: payments, payroll, insurance claims, material procurement, equipment rental,
a social network, an AI construction estimator, automated wage negotiation, autonomous
financial decisions, fully autonomous hiring, a complex voice agent, or advanced analytics.

These are future modules. The university project stays focused on **workforce coordination**.

---

## How success is judged

The prototype is done when a professor can run the full demonstration without touching a
terminal, covering six scenarios:

1. "I need 8 masons tomorrow at 8 AM near Guntur."
2. "Can Ravi's crew handle it?"
3. "Find individual workers to fill the remaining positions."
4. "Is Suresh ready to work independently?"
5. "What happens to Suresh's reputation if he leaves Ravi's crew?"
6. "Suresh has created his own crew. How should ADAA represent him?"

Target length: **5–10 minutes**.

The full Definition of Done checklist is in section 26 of the build specification.
