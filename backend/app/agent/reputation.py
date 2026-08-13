"""
Reputation, calculated from what actually happened.

The one rule this file exists to enforce
----------------------------------------
No reputation number is ever typed in. Every one of them is counted from
the job and rating tables:

    completed_jobs    = completed assignment rows
    average_rating    = mean of that worker's rating rows
    attendance_rate   = days turned up / days booked
    reliability_score = a stated formula over the three above

That means anybody -- a professor, an examiner, you in six months -- can
recompute a headline figure from the tables and get the same answer. It is
what business rule 8 (the database is the source of truth) means when
applied to reputation rather than to availability.

The two rules that shape the queries
------------------------------------
**Rule 3: worker and crew reputation are separate.** A rating targets a
worker OR a crew, never both, and the two are counted separately. A crew
rated 4.8 does not make its members 4.8 workers, and this file never lets
that happen: ``recalculate_worker`` only ever reads ratings where
``worker_id`` matches.

**Rule 4: reputation belongs to the worker.** Nothing here filters by crew
membership. A worker who leaves a crew keeps every completed job and every
rating, because those rows are attached to them, not to the crew. Leaving
changes ``crew_members.status``; it does not touch anything counted here.

This module is used both by the data generator and at runtime, so the
demonstration data and live updates cannot drift apart.
"""

from app.database import connect, fetch_all, fetch_one


def worker_figures(worker_id: str) -> dict:
    """
    Count one worker's history. Reads only; changes nothing.

    Returned so it can be checked without writing, which is what the tests
    do when they verify that a stored figure matches the records.
    """
    row = fetch_one(
        """
        select
            (select count(*) from job_assignments
              where worker_id = %(id)s and status = 'completed') as completed_jobs,
            (select count(*) from job_assignments
              where worker_id = %(id)s and status = 'no_show')   as no_shows,
            (select round(avg(rating), 2) from ratings
              where worker_id = %(id)s)                          as average_rating,
            (select count(*) from ratings
              where worker_id = %(id)s)                          as ratings_count,
            (select sum(scheduled_days) from job_assignments
              where worker_id = %(id)s
                and status in ('completed', 'no_show'))          as days_booked,
            (select sum(attended_days) from job_assignments
              where worker_id = %(id)s
                and status in ('completed', 'no_show'))          as days_attended
        """,
        {"id": worker_id},
    )

    days_booked = row["days_booked"] or 0
    days_attended = row["days_attended"] or 0

    attendance = (round(days_attended / days_booked * 100, 2)
                  if days_booked else None)

    return {
        "worker_id": worker_id,
        "completed_jobs": row["completed_jobs"],
        "no_shows": row["no_shows"],
        "average_rating": (float(row["average_rating"])
                           if row["average_rating"] is not None else None),
        "ratings_count": row["ratings_count"],
        "days_booked": days_booked,
        "days_attended": days_attended,
        "attendance_rate": attendance,
        "reliability_score": reliability(attendance, row["average_rating"],
                                         row["no_shows"]),
    }


def reliability(attendance_rate, average_rating, no_shows: int):
    """
    How dependable somebody has proved to be, out of 5.

    A prototype formula, stated openly rather than hidden: the average of
    their attendance (rescaled to 5) and their rating, less a small penalty
    for each time they did not turn up. It is not validated, and the
    specification does not define one -- what matters is that it is
    written down and reproducible.
    """
    if average_rating is None or attendance_rate is None:
        return None

    attendance_part = float(attendance_rate) / 100 * 5
    score = (attendance_part + float(average_rating)) / 2 - (no_shows * 0.15)
    return round(max(0.0, min(5.0, score)), 2)


def crew_figures(crew_id: str) -> dict:
    """
    Count one crew's history.

    Only ratings aimed at the crew are counted. Its members' individual
    ratings are deliberately not averaged in: they belong to the members
    (business rule 3).
    """
    row = fetch_one(
        """
        select
            (select count(*) from job_assignments
              where crew_id = %(id)s and status = 'completed') as completed_jobs,
            (select round(avg(rating), 2) from ratings
              where crew_id = %(id)s)                          as rating,
            (select count(*) from ratings
              where crew_id = %(id)s)                          as ratings_count
        """,
        {"id": crew_id},
    )

    rating = float(row["rating"]) if row["rating"] is not None else None

    return {
        "crew_id": crew_id,
        "completed_jobs": row["completed_jobs"],
        "rating": rating,
        "ratings_count": row["ratings_count"],
        "reliability_score": rating,
    }


def recalculate_worker(worker_id: str) -> dict:
    """Count the history, then store the result on the worker."""
    figures = worker_figures(worker_id)

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update workers
                   set completed_jobs   = %s,
                       average_rating   = %s,
                       attendance_rate  = %s,
                       reliability_score = %s,
                       updated_at = now()
                 where id = %s
                """,
                (figures["completed_jobs"], figures["average_rating"],
                 figures["attendance_rate"], figures["reliability_score"],
                 worker_id),
            )
        conn.commit()

    return figures


def recalculate_crew(crew_id: str) -> dict:
    """Count the crew's history, then store it on the crew."""
    figures = crew_figures(crew_id)

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update crews
                   set completed_jobs = %s,
                       rating = %s,
                       reliability_score = %s,
                       updated_at = now()
                 where id = %s
                """,
                (figures["completed_jobs"], figures["rating"],
                 figures["reliability_score"], crew_id),
            )
        conn.commit()

    return figures


def recalculate_for_job(job_id: str) -> dict:
    """
    Update everyone affected by one job.

    Called after a job is completed or a rating is recorded. Only the
    people on that job are touched -- there is no reason to recompute the
    whole workforce, and doing so would hide a bug in which rows a change
    actually reaches.
    """
    workers = [row["worker_id"] for row in fetch_all(
        "select distinct worker_id from job_assignments "
        "where job_id = %s and worker_id is not null", (job_id,))]
    crews = [row["crew_id"] for row in fetch_all(
        "select distinct crew_id from job_assignments "
        "where job_id = %s and crew_id is not null", (job_id,))]

    return {
        "workers": [recalculate_worker(worker_id) for worker_id in workers],
        "crews": [recalculate_crew(crew_id) for crew_id in crews],
    }


def check_all() -> list[dict]:
    """
    Find any stored figure that disagrees with the records.

    Nothing should ever show up here. It exists so the claim "every
    reputation number is derived" can be checked rather than trusted, and
    a test runs it across the whole workforce.
    """
    problems = []

    for row in fetch_all("select id, completed_jobs, average_rating, "
                         "attendance_rate from workers order by id"):
        actual = worker_figures(row["id"])

        if row["completed_jobs"] != actual["completed_jobs"]:
            problems.append({
                "id": row["id"], "field": "completed_jobs",
                "stored": row["completed_jobs"],
                "actual": actual["completed_jobs"]})

        stored_rating = (float(row["average_rating"])
                         if row["average_rating"] is not None else None)
        if stored_rating != actual["average_rating"]:
            problems.append({
                "id": row["id"], "field": "average_rating",
                "stored": stored_rating, "actual": actual["average_rating"]})

        stored_attendance = (float(row["attendance_rate"])
                             if row["attendance_rate"] is not None else None)
        if stored_attendance != actual["attendance_rate"]:
            problems.append({
                "id": row["id"], "field": "attendance_rate",
                "stored": stored_attendance,
                "actual": actual["attendance_rate"]})

    for row in fetch_all("select id, completed_jobs, rating from crews order by id"):
        actual = crew_figures(row["id"])

        if row["completed_jobs"] != actual["completed_jobs"]:
            problems.append({
                "id": row["id"], "field": "crew completed_jobs",
                "stored": row["completed_jobs"],
                "actual": actual["completed_jobs"]})

        stored_rating = float(row["rating"]) if row["rating"] is not None else None
        if stored_rating != actual["rating"]:
            problems.append({
                "id": row["id"], "field": "crew rating",
                "stored": stored_rating, "actual": actual["rating"]})

    return problems
