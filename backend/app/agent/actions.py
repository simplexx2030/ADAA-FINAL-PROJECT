"""
Actions that change something, and the confirmation they require.

Business rule 7 says consequential actions need confirmation: confirming a
job, changing a wage, financial actions, removing a worker, changing
verified information. Rule 6 says the AI cannot remove workers from crews
on its own. Rule 9 says never claim an action happened unless a tool
confirms it.

All three come down to one design decision:

    The agent proposes. A person confirms. The application executes.

Nothing here is called by Gemini directly except ``propose`` and
``look_up``. Confirmation arrives through the API, from a human, carrying
the proposal's id. There is deliberately no tool that lets the model
confirm its own proposal -- if there were, rule 7 would be a suggestion
rather than a rule.

Proposals expire, so a stale one cannot be confirmed hours later against
data that has moved on. And every proposal is re-checked at the moment of
execution: a worker who was free when the proposal was written may not be
free when it is confirmed, and in that case the action fails rather than
booking somebody who is already busy (rule 1).
"""

import json
import uuid
from datetime import date, datetime, timedelta, timezone

from app.database import connect, fetch_all, fetch_one

# How long a proposal stays confirmable. Long enough for a conversation,
# short enough that the workforce data behind it is still current.
PROPOSAL_LIFETIME_MINUTES = 30


class ActionError(RuntimeError):
    """Something about the request itself is wrong."""


def _new_id() -> str:
    return "act_" + uuid.uuid4().hex[:12]


def _next_job_id() -> str:
    """The next J-number, continuing the existing sequence."""
    row = fetch_one(
        """
        select coalesce(max(substring(id from 2)::int), 0) as highest
          from jobs where id ~ '^J[0-9]+$'
        """
    )
    return f"J{(row['highest'] or 0) + 1:04d}"


# ---------------------------------------------------------------------------
# Proposing
# ---------------------------------------------------------------------------

def propose(action_type: str, payload: dict, summary: str,
            session_id: str | None = None) -> dict:
    """Write down what is being asked for, without doing it."""
    action_id = _new_id()
    expires = datetime.now(timezone.utc) + timedelta(minutes=PROPOSAL_LIFETIME_MINUTES)

    fetch_one(
        """
        insert into pending_actions
            (id, session_id, action_type, summary, payload, expires_at)
        values (%s, %s, %s, %s, %s::jsonb, %s)
        returning id
        """,
        (action_id, session_id, action_type, summary,
         json.dumps(payload, default=str), expires),
    )

    return {
        "action_id": action_id,
        "action_type": action_type,
        "status": "pending",
        "summary": summary,
        "expires_at": expires.isoformat(),
        "confirmed": False,
        "note": (
            "NOTHING HAS HAPPENED YET. This is a proposal. It takes effect "
            f"only when a person confirms it by calling "
            f"POST /api/actions/{action_id}/confirm. Do not tell the user "
            "the job is created, the offers are sent, or anyone is booked."
        ),
    }


def look_up(action_id: str) -> dict:
    """The current state of a proposal."""
    row = fetch_one(
        """
        select id, session_id, action_type, summary, payload, status,
               result, error, created_at, expires_at, decided_at
          from pending_actions where id = %s
        """,
        (action_id,),
    )
    if row is None:
        return {"found": False, "note": f"There is no action with id {action_id}."}

    if row["status"] == "pending" and row["expires_at"] < datetime.now(timezone.utc):
        row["status"] = "expired"

    return {"found": True, **row}


def list_for_session(session_id: str) -> list[dict]:
    return fetch_all(
        """
        select id, action_type, summary, status, created_at, decided_at
          from pending_actions where session_id = %s
         order by created_at desc
        """,
        (session_id,),
    )


# ---------------------------------------------------------------------------
# Confirming and cancelling
# ---------------------------------------------------------------------------

def cancel(action_id: str) -> dict:
    """Decline a proposal. Nothing is carried out."""
    current = look_up(action_id)
    if not current["found"]:
        raise ActionError(f"There is no action with id {action_id}.")
    if current["status"] != "pending":
        raise ActionError(
            f"That action is already {current['status']}; it cannot be cancelled.")

    fetch_one(
        "update pending_actions set status='cancelled', decided_at=now() "
        "where id=%s returning id",
        (action_id,),
    )
    return {"action_id": action_id, "status": "cancelled",
            "note": "Nothing was changed."}


def confirm(action_id: str) -> dict:
    """
    Carry out a proposal, after a person has approved it.

    The proposal is re-checked here, not trusted. Between proposing and
    confirming, somebody may have been booked onto another job, so the
    checks that made the proposal valid are run again.
    """
    current = look_up(action_id)

    if not current["found"]:
        raise ActionError(f"There is no action with id {action_id}.")
    if current["status"] == "confirmed":
        raise ActionError("That action has already been carried out.")
    if current["status"] == "expired":
        raise ActionError(
            "That proposal has expired. Ask for it again so it is checked "
            "against current data.")
    if current["status"] != "pending":
        raise ActionError(f"That action is {current['status']}; nothing to confirm.")

    handler = _HANDLERS.get(current["action_type"])
    if handler is None:
        raise ActionError(f"Unknown action type {current['action_type']}.")

    try:
        result = handler(current["payload"])
    except ActionError as error:
        fetch_one(
            "update pending_actions set status='failed', error=%s, "
            "decided_at=now() where id=%s returning id",
            (str(error), action_id),
        )
        raise

    fetch_one(
        """
        update pending_actions
           set status='confirmed', result=%s::jsonb, decided_at=now()
         where id=%s returning id
        """,
        (json.dumps(result, default=str), action_id),
    )

    return {"action_id": action_id, "status": "confirmed",
            "action_type": current["action_type"], "result": result}


# ---------------------------------------------------------------------------
# What each action actually does
# ---------------------------------------------------------------------------

def _execute_create_job(payload: dict) -> dict:
    """Create the job row."""
    contractor = fetch_one("select id, company_name from contractors where id=%s",
                           (payload["contractor_id"],))
    if contractor is None:
        raise ActionError(f"No contractor with id {payload['contractor_id']}.")

    job_id = _next_job_id()

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into jobs
                    (id, contractor_id, title, description, skill_required,
                     workers_required, location_name, location_lat,
                     location_lng, site_address, date, start_time, wage, status)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'open')
                """,
                (job_id, payload["contractor_id"], payload["title"],
                 payload.get("description"), payload["skill_required"],
                 payload["workers_required"], payload.get("location_name"),
                 payload.get("location_lat"), payload.get("location_lng"),
                 payload.get("site_address"), payload["date"],
                 payload.get("start_time", "08:00"), payload.get("wage")),
            )
        conn.commit()

    return {"job_id": job_id, "status": "open",
            "contractor": contractor["company_name"]}


def _execute_send_offers(payload: dict) -> dict:
    """
    Record job offers to workers and crews.

    Notifications are SIMULATED. The specification is explicit that
    WhatsApp and SMS wait until the core agent works, so what happens here
    is that an assignment row is created with status 'offered'. Nobody's
    phone rings. The response is collected through the API instead.
    """
    job = fetch_one("select id, title, date from jobs where id=%s",
                    (payload["job_id"],))
    if job is None:
        raise ActionError(f"No job with id {payload['job_id']}.")

    worker_ids = payload.get("worker_ids") or []
    crew_ids = payload.get("crew_ids") or []
    if not worker_ids and not crew_ids:
        raise ActionError("No workers or crews to send an offer to.")

    sent, skipped = [], []

    with connect() as conn:
        with conn.cursor() as cur:
            for worker_id in worker_ids:
                # Re-check availability at the moment of sending. Somebody
                # free when this was proposed may be booked by now.
                free = fetch_one(
                    "select 1 as ok from availability "
                    "where worker_id=%s and date=%s and status='available'",
                    (worker_id, job["date"]),
                )
                if free is None:
                    skipped.append({"worker_id": worker_id,
                                    "reason": "no longer available that day"})
                    continue

                cur.execute(
                    """
                    insert into job_assignments
                        (job_id, worker_id, assignment_type, status)
                    values (%s, %s, 'individual', 'offered')
                    returning id
                    """,
                    (payload["job_id"], worker_id),
                )
                sent.append({"assignment_id": cur.fetchone()[0],
                             "worker_id": worker_id})

            for crew_id in crew_ids:
                cur.execute(
                    """
                    insert into job_assignments
                        (job_id, crew_id, assignment_type, status)
                    values (%s, %s, 'crew', 'offered')
                    returning id
                    """,
                    (payload["job_id"], crew_id),
                )
                sent.append({"assignment_id": cur.fetchone()[0],
                             "crew_id": crew_id})
        conn.commit()

    if not sent:
        raise ActionError(
            "Nobody could be offered this job: " +
            "; ".join(f"{s.get('worker_id')} {s['reason']}" for s in skipped))

    return {
        "job_id": payload["job_id"],
        "offers_sent": len(sent),
        "offers": sent,
        "skipped": skipped,
        "delivery": "simulated - no message was actually sent to anyone",
    }


def _execute_confirm_assignment(payload: dict) -> dict:
    """
    Confirm workers onto a job, and mark them booked.

    Marking availability is what stops the same person being recommended
    for another job that day. Without it, business rule 1 would hold only
    until the second request.
    """
    assignment_ids = payload.get("assignment_ids") or []
    if not assignment_ids:
        raise ActionError("No assignments to confirm.")

    confirmed, refused = [], []

    with connect() as conn:
        with conn.cursor() as cur:
            for assignment_id in assignment_ids:
                row = fetch_one(
                    """
                    select ja.id, ja.status, ja.worker_id, ja.crew_id,
                           j.date, j.id as job_id
                      from job_assignments ja
                      join jobs j on j.id = ja.job_id
                     where ja.id = %s
                    """,
                    (assignment_id,),
                )
                if row is None:
                    refused.append({"assignment_id": assignment_id,
                                    "reason": "no such assignment"})
                    continue
                if row["status"] not in ("offered", "accepted"):
                    refused.append({"assignment_id": assignment_id,
                                    "reason": f"status is {row['status']}"})
                    continue

                cur.execute(
                    "update job_assignments set status='confirmed', "
                    "confirmed_at=now() where id=%s",
                    (assignment_id,),
                )

                # Book the worker, or every active member of the crew.
                if row["worker_id"]:
                    cur.execute(
                        "update availability set status='booked' "
                        "where worker_id=%s and date=%s",
                        (row["worker_id"], row["date"]),
                    )
                elif row["crew_id"]:
                    cur.execute(
                        """
                        update availability set status='booked'
                         where date=%s and worker_id in (
                               select worker_id from crew_members
                                where crew_id=%s and status='active')
                        """,
                        (row["date"], row["crew_id"]),
                    )

                cur.execute("update jobs set status='confirmed', updated_at=now() "
                            "where id=%s", (row["job_id"],))

                confirmed.append({"assignment_id": assignment_id,
                                  "worker_id": row["worker_id"],
                                  "crew_id": row["crew_id"]})
        conn.commit()

    if not confirmed:
        raise ActionError("None of those assignments could be confirmed: " +
                          "; ".join(f"{r['assignment_id']}: {r['reason']}"
                                    for r in refused))

    return {"confirmed": len(confirmed), "assignments": confirmed,
            "refused": refused,
            "note": "Confirmed workers are now marked booked for that day."}


def _execute_complete_job(payload: dict) -> dict:
    """
    Mark a job finished, record who turned up, and update reputation.

    ``outcomes`` says, for each confirmed assignment, how many days the
    person was booked for and how many they actually worked. Those two
    numbers are what attendance is calculated from, so this is the moment a
    worker's record genuinely changes.

    Somebody who attended none of their days is recorded as a no_show
    rather than a completed job. That is the honest reading, and it means a
    no-show cannot quietly count towards completed_jobs.
    """
    from app.agent import reputation

    job = fetch_one("select id, title, status from jobs where id=%s",
                    (payload["job_id"],))
    if job is None:
        raise ActionError(f"No job with id {payload['job_id']}.")
    if job["status"] == "completed":
        raise ActionError("That job is already marked completed.")

    outcomes = payload.get("outcomes") or []
    if not outcomes:
        raise ActionError("No outcomes given, so there is nothing to record.")

    recorded = []

    with connect() as conn:
        with conn.cursor() as cur:
            for outcome in outcomes:
                assignment_id = outcome["assignment_id"]
                scheduled = int(outcome.get("scheduled_days", 1))
                attended = int(outcome.get("attended_days", scheduled))

                if scheduled < 1:
                    raise ActionError("scheduled_days must be at least 1.")
                if not 0 <= attended <= scheduled:
                    raise ActionError(
                        f"attended_days ({attended}) must be between 0 and "
                        f"scheduled_days ({scheduled}).")

                row = fetch_one(
                    "select id, status, worker_id, crew_id from job_assignments "
                    "where id=%s and job_id=%s",
                    (assignment_id, payload["job_id"]),
                )
                if row is None:
                    raise ActionError(
                        f"Assignment {assignment_id} is not on job "
                        f"{payload['job_id']}.")
                if row["status"] not in ("confirmed", "accepted"):
                    raise ActionError(
                        f"Assignment {assignment_id} is {row['status']}; only "
                        "confirmed work can be completed.")

                status = "completed" if attended > 0 else "no_show"
                cur.execute(
                    """
                    update job_assignments
                       set status=%s, scheduled_days=%s, attended_days=%s,
                           completed_at=now()
                     where id=%s
                    """,
                    (status, scheduled, attended, assignment_id),
                )
                recorded.append({
                    "assignment_id": assignment_id, "status": status,
                    "worker_id": row["worker_id"], "crew_id": row["crew_id"],
                    "scheduled_days": scheduled, "attended_days": attended,
                })

            cur.execute("update jobs set status='completed', updated_at=now() "
                        "where id=%s", (payload["job_id"],))
        conn.commit()

    # Reputation is recounted from the records, not adjusted by hand.
    updated = reputation.recalculate_for_job(payload["job_id"])

    return {
        "job_id": payload["job_id"], "status": "completed",
        "outcomes": recorded,
        "reputation_updated": {
            "workers": [{"worker_id": w["worker_id"],
                         "completed_jobs": w["completed_jobs"],
                         "attendance_rate": w["attendance_rate"]}
                        for w in updated["workers"]],
            "crews": [{"crew_id": c["crew_id"],
                       "completed_jobs": c["completed_jobs"]}
                      for c in updated["crews"]],
        },
        "note": ("Reputation was recalculated from the job records. Ratings "
                 "are recorded separately, by the contractor."),
    }


def record_rating(job_id: str, rater_id: str, rating: float,
                  worker_id: str | None = None, crew_id: str | None = None,
                  comment: str = "") -> dict:
    """
    A contractor rates a worker or a crew for a completed job.

    Exactly one of worker_id or crew_id. A rating belongs to one or the
    other and never to both -- that separation is business rule 3, and it
    is enforced by a database constraint as well as here.

    There is no agent tool for this. Reputation is something people give
    each other; the AI does not get to award it.
    """
    from app.agent import reputation

    if bool(worker_id) == bool(crew_id):
        raise ActionError("Give exactly one of worker_id or crew_id.")
    if not 0 <= float(rating) <= 5:
        raise ActionError("A rating must be between 0 and 5.")

    job = fetch_one("select id, status from jobs where id=%s", (job_id,))
    if job is None:
        raise ActionError(f"No job with id {job_id}.")
    if job["status"] != "completed":
        raise ActionError(
            "Only completed work can be rated. Mark the job completed first.")

    if fetch_one("select id from contractors where id=%s", (rater_id,)) is None:
        raise ActionError(f"No contractor with id {rater_id}.")

    worked = fetch_one(
        """
        select id from job_assignments
         where job_id=%s and status='completed'
           and (worker_id = %s or crew_id = %s)
        """,
        (job_id, worker_id, crew_id),
    )
    if worked is None:
        raise ActionError(
            "That worker or crew did not complete this job, so they cannot "
            "be rated for it.")

    already = fetch_one(
        """
        select id from ratings
         where job_id=%s and coalesce(worker_id,'') = coalesce(%s,'')
           and coalesce(crew_id,'') = coalesce(%s,'')
        """,
        (job_id, worker_id, crew_id),
    )
    if already is not None:
        raise ActionError("They have already been rated for this job.")

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into ratings
                    (job_id, rater_id, worker_id, crew_id, rating, comment)
                values (%s,%s,%s,%s,%s,%s) returning id
                """,
                (job_id, rater_id, worker_id, crew_id, rating, comment or None),
            )
            rating_id = cur.fetchone()[0]
        conn.commit()

    if worker_id:
        figures = reputation.recalculate_worker(worker_id)
        who = {"worker_id": worker_id,
               "average_rating": figures["average_rating"],
               "ratings_count": figures["ratings_count"],
               "note": "This rating belongs to the worker, not to any crew."}
    else:
        figures = reputation.recalculate_crew(crew_id)
        who = {"crew_id": crew_id, "rating": figures["rating"],
               "ratings_count": figures["ratings_count"],
               "note": ("This rating belongs to the crew. No member's own "
                        "rating was changed by it.")}

    return {"rating_id": rating_id, "job_id": job_id, "rating": float(rating),
            **who}


_HANDLERS = {
    "create_job": _execute_create_job,
    "send_offers": _execute_send_offers,
    "confirm_assignment": _execute_confirm_assignment,
    "complete_job": _execute_complete_job,
}


# ---------------------------------------------------------------------------
# The other side: a worker or crew answering an offer
# ---------------------------------------------------------------------------

def respond_to_offer(assignment_id: int, accept: bool) -> dict:
    """
    Record a worker's or crew leader's answer to an offer.

    In the real product this arrives from their phone. Here it comes
    through the API, which is enough to demonstrate the loop:

        contractor -> job -> offer -> response -> confirmation
    """
    row = fetch_one(
        """
        select ja.id, ja.status, ja.worker_id, ja.crew_id,
               coalesce(w.name, c.name) as who, j.title
          from job_assignments ja
          join jobs j on j.id = ja.job_id
          left join workers w on w.id = ja.worker_id
          left join crews c on c.id = ja.crew_id
         where ja.id = %s
        """,
        (assignment_id,),
    )
    if row is None:
        raise ActionError(f"There is no offer with id {assignment_id}.")
    if row["status"] != "offered":
        raise ActionError(
            f"That offer has already been answered; its status is "
            f"{row['status']}.")

    new_status = "accepted" if accept else "declined"
    fetch_one(
        "update job_assignments set status=%s where id=%s returning id",
        (new_status, assignment_id),
    )

    return {"assignment_id": assignment_id, "who": row["who"],
            "job": row["title"], "status": new_status}


def job_offers(job_id: str) -> list[dict]:
    """Every offer made for a job, and where each one stands."""
    return fetch_all(
        """
        select ja.id as assignment_id, ja.assignment_type, ja.status,
               ja.worker_id, ja.crew_id,
               coalesce(w.name, c.name) as who,
               ja.confirmed_at
          from job_assignments ja
          left join workers w on w.id = ja.worker_id
          left join crews c on c.id = ja.crew_id
         where ja.job_id = %s
         order by ja.id
        """,
        (job_id,),
    )


def expire_old_proposals() -> int:
    """Mark proposals that were never answered. Returns how many."""
    rows = fetch_all(
        "update pending_actions set status='expired' "
        "where status='pending' and expires_at < now() returning id"
    )
    return len(rows)
