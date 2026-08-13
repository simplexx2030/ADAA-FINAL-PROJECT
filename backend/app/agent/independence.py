"""
Is this worker ready to take work on their own?

What this is
------------
A decision-support score. It reads a worker's verified history and returns
a number, the evidence behind it, and a recommendation in words.

What this is NOT
----------------
**It is not validated.** The weights below are a first guess, chosen
because they seem reasonable, not because they were tested against
outcomes. The specification is explicit about this (section 9.11, step 9):
do not present the score as scientific. Anyone reporting it should say so.

**It does not change anyone's status.** Business rule 5: the AI
recommends, the worker decides. Nothing in this file writes to the
``workers`` table. It saves a row to ``independence_assessments``, which is
a record of advice given -- not a promotion, not a change of employment,
not a removal from a crew. A worker can be assessed as ready and simply
carry on as a crew member, and ADAA must be equally happy with that.

Why "independent" is not the same as "good"
-------------------------------------------
A worker can be excellent and still not be ready to work alone: taking
direct contracts means dealing with contractors yourself, turning up
without a crew leader organising it, and being trusted by more than one
employer. So the score is not just an average of their ratings. It weighs
breadth of contractor relationships and consistency of attendance, because
those are what change when the crew leader stops arranging the work.
"""

from app.database import fetch_all, fetch_one

# --- The weights -----------------------------------------------------------
# Prototype values. They are in one place, and they are meant to be argued
# with. Section 9.11 names the five factors; these decide how much each
# counts.
WEIGHTS = {
    "completed_jobs": 0.25,
    "rating": 0.20,
    "attendance": 0.20,
    "reliability": 0.20,
    "contractor_relationships": 0.15,
}

# What counts as "enough" for full marks on each factor.
JOBS_FOR_FULL_SCORE = 25
CONTRACTORS_FOR_FULL_SCORE = 4

# Below these, a recommendation is not offered at all, whatever the score
# says. They are floors, not weights: a worker with two jobs and one
# contractor has not yet shown enough for anybody to judge.
MINIMUM_JOBS = 10
MINIMUM_CONTRACTORS = 2

# Where the wording changes.
READY_SCORE = 70
DEVELOPING_SCORE = 50


def _capped(value, maximum) -> float:
    if value is None or maximum == 0:
        return 0.0
    return max(0.0, min(float(value) / maximum, 1.0))


def gather_evidence(worker_id: str) -> dict | None:
    """
    Everything the assessment is based on, straight from the records.

    Returns None if there is no such worker. Every number here is counted,
    not read from a summary column, so the evidence and the score cannot
    disagree with the underlying history.
    """
    worker = fetch_one(
        "select id, name, verification_status, experience_years "
        "from workers where id = %s",
        (worker_id,),
    )
    if worker is None:
        return None

    from app.agent import reputation

    figures = reputation.worker_figures(worker_id)

    verified_skills = fetch_all(
        """
        select s.name, ws.years_experience
          from worker_skills ws join skills s on s.id = ws.skill_id
         where ws.worker_id = %s and ws.verification_status = 'verified'
         order by s.name
        """,
        (worker_id,),
    )

    contractors = fetch_all(
        """
        select c.company_name, count(*) as jobs
          from job_assignments ja
          join jobs j on j.id = ja.job_id
          join contractors c on c.id = j.contractor_id
         where ja.worker_id = %s and ja.status = 'completed'
         group by c.company_name
         order by count(*) desc
        """,
        (worker_id,),
    )

    crews = fetch_all(
        """
        select c.name, cm.role, cm.status
          from crew_members cm join crews c on c.id = cm.crew_id
         where cm.worker_id = %s
         order by cm.joined_at desc
        """,
        (worker_id,),
    )

    return {
        "worker_id": worker_id,
        "name": worker["name"],
        "verification_status": worker["verification_status"],
        "experience_years": worker["experience_years"],
        "completed_jobs": figures["completed_jobs"],
        "no_shows": figures["no_shows"],
        "average_rating": figures["average_rating"],
        "ratings_count": figures["ratings_count"],
        "attendance_rate": figures["attendance_rate"],
        "days_attended": figures["days_attended"],
        "days_booked": figures["days_booked"],
        "reliability_score": figures["reliability_score"],
        "verified_skills": [s["name"] for s in verified_skills],
        "contractors": [{"company": c["company_name"], "jobs": c["jobs"]}
                        for c in contractors],
        "distinct_contractors": len(contractors),
        "crew_membership": crews,
    }


def assess(worker_id: str, save: bool = False) -> dict:
    """
    Score a worker's readiness for independent work.

    Set ``save=True`` to keep the assessment in
    ``independence_assessments``. That table records advice that was given;
    it does not change the worker's status, and nothing here ever will.
    """
    evidence = gather_evidence(worker_id)
    if evidence is None:
        return {"found": False,
                "note": f"There is no worker with id {worker_id}."}

    factors = {
        "completed_jobs": _capped(evidence["completed_jobs"], JOBS_FOR_FULL_SCORE),
        "rating": _capped(evidence["average_rating"], 5.0),
        "attendance": _capped(evidence["attendance_rate"], 100.0),
        "reliability": _capped(evidence["reliability_score"], 5.0),
        "contractor_relationships": _capped(evidence["distinct_contractors"],
                                            CONTRACTORS_FOR_FULL_SCORE),
    }

    score = round(sum(WEIGHTS[name] * value
                      for name, value in factors.items()) * 100, 1)

    # --- the gates ---
    # These are separate from the score on purpose. A worker can score well
    # on averages and still not have shown enough for anyone to judge, and
    # an unverified skill may never be used to recommend anything (rule 2).
    blockers = []
    if not evidence["verified_skills"]:
        blockers.append("no verified skill on record")
    if evidence["verification_status"] != "verified":
        blockers.append(f"worker is {evidence['verification_status']}, not verified")
    if evidence["completed_jobs"] < MINIMUM_JOBS:
        blockers.append(
            f"{evidence['completed_jobs']} completed jobs, fewer than the "
            f"{MINIMUM_JOBS} this assessment needs to say anything useful")
    if evidence["distinct_contractors"] < MINIMUM_CONTRACTORS:
        blockers.append(
            f"has worked for {evidence['distinct_contractors']} contractor(s); "
            f"independent work usually means dealing with several")

    if blockers:
        readiness = "not_enough_history"
        recommendation = (
            f"{evidence['name']} does not yet have enough verified history "
            "for this assessment to be meaningful: "
            + "; ".join(blockers) + "."
        )
    elif score >= READY_SCORE:
        readiness = "ready_for_consideration"
        recommendation = (
            f"{evidence['name']} appears suitable for consideration for "
            "selected independent assignments, based on their verified work "
            "history."
        )
    elif score >= DEVELOPING_SCORE:
        readiness = "developing"
        recommendation = (
            f"{evidence['name']} is building a solid record but is not yet a "
            "clear candidate for independent work. More completed jobs and a "
            "wider range of contractors would strengthen the case."
        )
    else:
        readiness = "not_yet"
        recommendation = (
            f"{evidence['name']}'s record does not currently support a "
            "recommendation for independent work."
        )

    result = {
        "found": True,
        "worker_id": worker_id,
        "name": evidence["name"],
        "score": score,
        "readiness": readiness,
        "recommendation": recommendation,
        "blockers": blockers,
        "factors": {name: round(value, 3) for name, value in factors.items()},
        "weights_used": WEIGHTS,
        "evidence": evidence,
        # Repeated in the payload itself, because this is the sentence that
        # most needs to survive being summarised by a language model.
        "important": (
            "This is a RECOMMENDATION, not a change of status. ADAA cannot "
            "make anyone independent. The worker decides, and their crew "
            "membership is unaffected either way. The score is a prototype "
            "decision-support figure and has not been scientifically "
            "validated."
        ),
    }

    if save:
        saved = fetch_one(
            """
            insert into independence_assessments
                (worker_id, score, completed_jobs_factor, rating_factor,
                 attendance_factor, reliability_factor,
                 contractor_relationship_factor, recommendation)
            values (%s,%s,%s,%s,%s,%s,%s,%s)
            returning id, created_at
            """,
            (worker_id, score, factors["completed_jobs"], factors["rating"],
             factors["attendance"], factors["reliability"],
             factors["contractor_relationships"], recommendation),
        )
        result["assessment_id"] = saved["id"]
        result["saved_at"] = saved["created_at"]

    return result


def history(worker_id: str) -> list[dict]:
    """
    Past assessments for a worker, newest first.

    Kept so a recommendation can be shown to have been made at a point in
    time, on the evidence available then.
    """
    return fetch_all(
        """
        select id, score, recommendation, created_at,
               completed_jobs_factor, rating_factor, attendance_factor,
               reliability_factor, contractor_relationship_factor
          from independence_assessments
         where worker_id = %s
         order by created_at desc
        """,
        (worker_id,),
    )
