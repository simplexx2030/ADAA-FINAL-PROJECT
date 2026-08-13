"""
The ADAA backend API.

What it can do:
  - report that it is alive and that the database is reachable
  - read workers, crews, skills and locations from PostgreSQL
  - compose a workforce with the deterministic matching engine
  - talk to the Gemini agent, which searches the database through its tools

  - carry a job from request to confirmed workers, and record how it went
  - recount reputation from the job records

Anything consequential is PROPOSED, then confirmed by a person through
/api/actions/{id}/confirm. The agent cannot confirm its own proposal.

Run it with:
    backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
"""

from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import (actions as agent_actions, audit,
                       cache as reply_cache, independence, reputation)
from app.agent.actions import ActionError
from app.agent.agent import GeminiUnavailable, Turn, chat, parse_request
from app.agent.matching import (
    DEFAULT_SEARCH_RADIUS_KM,
    WorkforceRequest,
    calculate_distance,
    compose_workforce,
)
from app.config import settings
from app.database import all_locations, fetch_all, fetch_one, find_location

app = FastAPI(
    title="ADAA Workforce Coordination Agent",
    description=(
        "Backend API for ADAA, a construction workforce coordination "
        "platform. The AI agent is powered by Gemini, which reaches the "
        "workforce data only through tools. Read 'tools_used' on any agent "
        "reply to see exactly what was looked up."
    ),
    version="0.8.0",
)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """
    Confirm the server is running.

    This is the success criterion for STEP 0 of the build spec.
    """
    return {"status": "ok"}


@app.get("/")
def root():
    """
    A friendly landing response.

    Note that we report *whether* a Gemini key is configured, never the key
    itself. Secrets must never be exposed through the API or the logs.
    """
    return {
        "name": "ADAA Workforce Coordination Agent",
        "step": "STEP 8 - reputation from job history",
        "environment": settings.app_env,
        "gemini_model": settings.gemini_model,
        "gemini_key_configured": bool(settings.gemini_api_key),
        "database_configured": bool(settings.database_url),
        "docs": "/docs",
    }


@app.get("/health/database")
def health_database():
    """Confirm the application can actually reach PostgreSQL."""
    try:
        row = fetch_one("select count(*) as workers from workers")
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {type(error).__name__}",
        )
    return {"status": "ok", "workers": row["workers"]}


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

WORKER_COLUMNS = """
    w.id, w.name, w.location_name, w.location_lat, w.location_lng,
    w.travel_radius_km, w.experience_years, w.preferred_language,
    w.verification_status, w.availability_status, w.reliability_score,
    w.average_rating, w.completed_jobs, w.attendance_rate
"""


@app.get("/api/workers")
def list_workers(skill: str | None = None, location: str | None = None):
    """
    List workers, optionally filtered by verified skill and by location.

    Only VERIFIED skills are matched, because ADAA must never present an
    unverified qualification as if it were confirmed (business rule 2).
    """
    sql = f"""
        select {WORKER_COLUMNS},
               (select string_agg(s.name, ', ' order by s.name)
                  from worker_skills ws
                  join skills s on s.id = ws.skill_id
                 where ws.worker_id = w.id
                   and ws.verification_status = 'verified') as verified_skills
          from workers w
         where 1 = 1
    """
    params: list = []

    if skill:
        sql += """
           and exists (select 1
                         from worker_skills ws
                         join skills s on s.id = ws.skill_id
                        where ws.worker_id = w.id
                          and ws.verification_status = 'verified'
                          and lower(s.name) = lower(%s))
        """
        params.append(skill)

    if location:
        sql += " and lower(w.location_name) = lower(%s)"
        params.append(location)

    sql += " order by w.average_rating desc nulls last, w.completed_jobs desc"

    return {"workers": fetch_all(sql, tuple(params))}


@app.get("/api/workers/{worker_id}")
def get_worker(worker_id: str):
    """
    One worker's full profile, including their verified skills and their
    crew membership history.

    The membership history is included on purpose: it shows that a worker
    keeps their record even after leaving a crew (business rule 4).
    """
    worker = fetch_one(
        f"select {WORKER_COLUMNS} from workers w where w.id = %s",
        (worker_id,),
    )
    if worker is None:
        raise HTTPException(status_code=404, detail=f"No worker with id {worker_id}")

    worker["skills"] = fetch_all(
        """
        select s.name, s.category, ws.verification_status, ws.years_experience
          from worker_skills ws
          join skills s on s.id = ws.skill_id
         where ws.worker_id = %s
         order by s.name
        """,
        (worker_id,),
    )

    worker["crew_history"] = fetch_all(
        """
        select c.id as crew_id, c.name as crew_name, cm.role, cm.status,
               cm.joined_at, cm.left_at
          from crew_members cm
          join crews c on c.id = cm.crew_id
         where cm.worker_id = %s
         order by cm.joined_at desc
        """,
        (worker_id,),
    )

    worker["ratings_received"] = fetch_all(
        """
        select r.job_id, r.rating, r.comment, r.created_at
          from ratings r
         where r.worker_id = %s
         order by r.created_at desc
        """,
        (worker_id,),
    )

    return worker


# ---------------------------------------------------------------------------
# Crews
# ---------------------------------------------------------------------------

@app.get("/api/crews")
def list_crews(trade: str | None = None):
    """List crews, optionally filtered by trade, with their member count."""
    sql = """
        select c.id, c.name, c.primary_trade, c.location_name,
               c.location_lat, c.location_lng, c.travel_radius_km,
               c.availability_status, c.rating, c.completed_jobs,
               c.reliability_score, c.verification_status,
               leader.name as leader_name,
               (select count(*) from crew_members cm
                 where cm.crew_id = c.id and cm.status = 'active') as active_members
          from crews c
          left join workers leader on leader.id = c.leader_worker_id
         where 1 = 1
    """
    params: list = []

    if trade:
        sql += " and lower(c.primary_trade) = lower(%s)"
        params.append(trade)

    sql += " order by c.rating desc nulls last"

    return {"crews": fetch_all(sql, tuple(params))}


@app.get("/api/crews/{crew_id}")
def get_crew(crew_id: str):
    """
    One crew's profile and its current members.

    The crew's own rating is reported separately from each member's rating,
    because the two reputations are not the same thing (business rule 3).
    """
    crew = fetch_one(
        """
        select c.id, c.name, c.primary_trade, c.location_name,
               c.location_lat, c.location_lng, c.travel_radius_km,
               c.availability_status, c.rating, c.completed_jobs,
               c.reliability_score, c.verification_status,
               c.leader_worker_id, leader.name as leader_name
          from crews c
          left join workers leader on leader.id = c.leader_worker_id
         where c.id = %s
        """,
        (crew_id,),
    )
    if crew is None:
        raise HTTPException(status_code=404, detail=f"No crew with id {crew_id}")

    crew["members"] = fetch_all(
        """
        select w.id, w.name, cm.role, cm.status, cm.joined_at, cm.left_at,
               w.average_rating as worker_own_rating,
               w.completed_jobs as worker_own_completed_jobs,
               w.availability_status
          from crew_members cm
          join workers w on w.id = cm.worker_id
         where cm.crew_id = %s
         order by (cm.role = 'leader') desc, w.name
        """,
        (crew_id,),
    )

    return crew


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@app.get("/api/skills")
def list_skills():
    """The list of skills ADAA knows about."""
    return {"skills": fetch_all("select id, name, category from skills order by name")}


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

@app.get("/api/locations")
def list_locations():
    """
    The places ADAA has workforce in.

    Coordinates are averaged from the workers recorded at each place, so
    this list comes from the data rather than from a hard-coded table.
    """
    return {"locations": all_locations()}


def resolve_location(name: str) -> dict:
    """Turn a place name such as 'Guntur' into coordinates."""
    row = find_location(name)
    if row is None:
        known = [r["name"] for r in all_locations()]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown location '{name}'. Known locations: {', '.join(known)}",
        )
    return row


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

@app.get("/api/match/workforce")
def match_workforce(
    skill: str,
    quantity: int,
    location: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    on_date: str | None = None,
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
):
    """
    Find and compose a workforce for a job.

    This endpoint contains no AI. It is the deterministic matching engine
    described in section 10 of the build specification, and it is what the
    Gemini agent will call in a later step.

    Example:
        /api/match/workforce?skill=Mason&quantity=8&location=Guntur

    Give either a known ``location`` name, or explicit ``lat`` and ``lng``.
    ``on_date`` defaults to tomorrow, which is what the demonstration asks
    for.
    """
    if quantity < 1:
        raise HTTPException(status_code=400, detail="quantity must be at least 1")

    if lat is None or lng is None:
        if not location:
            raise HTTPException(
                status_code=400,
                detail="Give either a location name, or both lat and lng.",
            )
        place = resolve_location(location)
        lat, lng, location_name = place["lat"], place["lng"], place["name"]
    else:
        location_name = location or f"{lat}, {lng}"

    if on_date:
        try:
            wanted = date.fromisoformat(on_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="on_date must look like 2026-08-14",
            )
    else:
        wanted = date.today() + timedelta(days=1)

    request = WorkforceRequest(
        skill=skill,
        quantity=quantity,
        on_date=wanted,
        location_lat=lat,
        location_lng=lng,
        location_name=location_name,
        max_distance_km=radius_km,
    )

    return compose_workforce(request)


@app.get("/api/distance")
def distance(lat1: float, lng1: float, lat2: float, lng2: float):
    """Distance in kilometres between two points (agent tool 6)."""
    return {"distance_km": calculate_distance(lat1, lng1, lat2, lng2)}


# ---------------------------------------------------------------------------
# The AI agent (Gemini)
# ---------------------------------------------------------------------------

class ChatTurn(BaseModel):
    """One earlier message in the conversation."""

    role: str = Field(description="'user' or 'model'")
    text: str


class ChatRequest(BaseModel):
    message: str = Field(description="What the contractor said")
    history: list[ChatTurn] = Field(default_factory=list)
    session_id: str | None = Field(
        default=None,
        description=("Pass the session_id from a previous reply to keep the "
                     "whole conversation in one audit trail. One is created "
                     "if you leave this out."),
    )
    user_id: str | None = Field(
        default=None,
        description="Who is asking, if known. Recorded in the action log.",
    )


@app.post("/api/agent/chat")
def agent_chat(request: ChatRequest):
    """
    Talk to the ADAA agent.

    The agent is powered by Gemini and can search the ADAA database through
    its tools: workers, crews, profiles, availability, distances, and a
    full workforce recommendation.

    Read "tools_used" in the response. It lists every tool that actually
    ran, with its arguments. "grounded" is true only when at least one tool
    ran -- if it is false, nothing in the reply came from the database,
    however confident the wording sounds.
    """
    try:
        return chat(
            request.message,
            history=[Turn(role=t.role, text=t.text) for t in request.history],
            session_id=request.session_id,
            user_id=request.user_id,
        )
    except GeminiUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))


# ---------------------------------------------------------------------------
# The agent action log (specification section 24)
# ---------------------------------------------------------------------------

@app.get("/api/agent/sessions")
def list_sessions(limit: int = 20):
    """
    Recent conversations, newest first.

    Each row summarises one conversation: how many actions, which tools
    were used, and whether anything failed.
    """
    return {"sessions": audit.recent_sessions(limit)}


@app.get("/api/agent/sessions/{session_id}")
def session_trail(session_id: str):
    """
    Everything the agent did in one conversation, in order.

    This is the answer to "how do you know it did not make that up?".
    Each tool call is recorded with the arguments the agent chose and the
    records that came back.
    """
    actions = audit.session_actions(session_id)
    if not actions:
        raise HTTPException(status_code=404,
                            detail=f"No actions recorded for session {session_id}")
    return {"session_id": session_id, "actions": actions}


# ---------------------------------------------------------------------------
# Actions that change something (business rule 7)
# ---------------------------------------------------------------------------
#
# The agent proposes. A person confirms. These endpoints are the "person"
# half. There is no way for the agent to reach them.

@app.get("/api/actions/{action_id}")
def get_action(action_id: str):
    """What a proposed action would do, and whether it has been confirmed."""
    found = agent_actions.look_up(action_id)
    if not found.get("found"):
        raise HTTPException(status_code=404,
                            detail=f"No action with id {action_id}")
    return found


@app.post("/api/actions/{action_id}/confirm")
def confirm_action(action_id: str):
    """
    Approve a proposed action and carry it out.

    This is the only way a job gets created, an offer gets sent, or a
    worker gets confirmed. The agent cannot call it.

    The proposal is re-checked here rather than trusted: somebody free when
    it was proposed may have been booked since, and in that case the action
    fails rather than double-booking them.
    """
    try:
        return agent_actions.confirm(action_id)
    except ActionError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.post("/api/actions/{action_id}/cancel")
def cancel_action(action_id: str):
    """Decline a proposed action. Nothing is changed."""
    try:
        return agent_actions.cancel(action_id)
    except ActionError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.get("/api/jobs/{job_id}/offers")
def list_offers(job_id: str):
    """Who has been offered this job, and how they answered."""
    return {"job_id": job_id, "offers": agent_actions.job_offers(job_id)}


class OfferResponse(BaseModel):
    accept: bool = Field(description="True to accept the job, false to decline")


@app.post("/api/offers/{assignment_id}/respond")
def respond_to_offer(assignment_id: int, response: OfferResponse):
    """
    A worker or crew leader answers an offer.

    In the real product this comes from their phone. Here it comes through
    the API, which is enough to demonstrate the loop:
    contractor to job to offer to response to confirmation.
    """
    try:
        return agent_actions.respond_to_offer(assignment_id, response.accept)
    except ActionError as error:
        raise HTTPException(status_code=409, detail=str(error))


class ConfirmAssignments(BaseModel):
    assignment_ids: list[int] = Field(
        description="Which offers to confirm, by assignment id")


@app.post("/api/jobs/{job_id}/confirm")
def confirm_assignments(job_id: str, request: ConfirmAssignments):
    """
    Propose confirming workers onto a job.

    Confirming is consequential -- it books people for the day -- so this
    creates a proposal that must itself be confirmed. Post the returned
    action_id to /api/actions/{id}/confirm to carry it out.
    """
    job = fetch_one("select id, title, date from jobs where id = %s", (job_id,))
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {job_id}")

    summary = (f"Confirm {len(request.assignment_ids)} worker(s) onto job "
               f"{job_id} ({job['title']}) on {job['date']}. They will be "
               "marked booked for that day.")

    return agent_actions.propose(
        "confirm_assignment",
        {"assignment_ids": request.assignment_ids, "job_id": job_id},
        summary,
    )


# ---------------------------------------------------------------------------
# Reputation (business rules 3 and 4)
# ---------------------------------------------------------------------------

class JobOutcome(BaseModel):
    assignment_id: int
    scheduled_days: int = Field(default=1, description="Days they were booked for")
    attended_days: int = Field(default=1, description="Days they actually worked")


class CompleteJob(BaseModel):
    outcomes: list[JobOutcome] = Field(
        description="One entry per confirmed assignment on this job")


@app.post("/api/jobs/{job_id}/complete")
def complete_job(job_id: str, request: CompleteJob):
    """
    Propose marking a job finished and recording who turned up.

    Completing a job changes people's permanent records, so it is a
    proposal like any other consequential action: post the returned
    action_id to /api/actions/{id}/confirm to carry it out.

    Somebody who attended none of their booked days is recorded as a
    no-show rather than a completed job.
    """
    job = fetch_one("select id, title from jobs where id = %s", (job_id,))
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {job_id}")

    summary = (f"Mark job {job_id} ({job['title']}) completed, recording "
               f"attendance for {len(request.outcomes)} assignment(s). This "
               "updates completed jobs, attendance and reliability.")

    return agent_actions.propose(
        "complete_job",
        {"job_id": job_id,
         "outcomes": [o.model_dump() for o in request.outcomes]},
        summary,
    )


class NewRating(BaseModel):
    job_id: str
    rater_id: str = Field(description="The contractor giving the rating")
    rating: float = Field(description="0 to 5")
    worker_id: str | None = Field(default=None, description="Rate a worker")
    crew_id: str | None = Field(default=None, description="Or rate a crew")
    comment: str = ""


@app.post("/api/ratings")
def add_rating(request: NewRating):
    """
    A contractor rates a worker or a crew for completed work.

    Exactly one of worker_id or crew_id. A rating belongs to one or the
    other, never both -- that is business rule 3, and it is enforced by a
    database constraint as well as here.

    There is no agent tool for this. Reputation is something people give
    each other; the AI does not award it.
    """
    try:
        return agent_actions.record_rating(
            request.job_id, request.rater_id, request.rating,
            worker_id=request.worker_id, crew_id=request.crew_id,
            comment=request.comment)
    except ActionError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.get("/api/workers/{worker_id}/reputation")
def worker_reputation(worker_id: str):
    """
    A worker's reputation, recounted from the records right now.

    Nothing here is read from the workers table. It is all counted from
    job_assignments and ratings, so you can compare it with the stored
    figures and see that they agree. That is what "the database is the
    source of truth" means for reputation.
    """
    if fetch_one("select id from workers where id=%s", (worker_id,)) is None:
        raise HTTPException(status_code=404, detail=f"No worker with id {worker_id}")
    return reputation.worker_figures(worker_id)


@app.get("/api/crews/{crew_id}/reputation")
def crew_reputation(crew_id: str):
    """
    A crew's reputation, recounted from the records.

    Only ratings aimed at the crew are counted. Its members' own ratings
    are deliberately excluded: they belong to the members (rule 3).
    """
    if fetch_one("select id from crews where id=%s", (crew_id,)) is None:
        raise HTTPException(status_code=404, detail=f"No crew with id {crew_id}")
    return reputation.crew_figures(crew_id)


@app.get("/api/workers/{worker_id}/independence")
def worker_independence(worker_id: str, save: bool = False):
    """
    Whether a worker has enough verified history to be considered for
    independent work.

    Returns a score, the five factors behind it, the evidence, and a
    recommendation in words.

    **This is a recommendation, not a change of status.** ADAA cannot make
    anyone independent -- the worker decides, and their crew membership is
    unaffected either way (business rule 5). The score is a prototype
    decision-support figure and has not been validated.

    Pass save=true to keep the assessment in the record of advice given.
    """
    result = independence.assess(worker_id, save=save)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"No worker with id {worker_id}")
    return result


@app.get("/api/workers/{worker_id}/independence/history")
def worker_independence_history(worker_id: str):
    """Past assessments for this worker, newest first."""
    if fetch_one("select id from workers where id=%s", (worker_id,)) is None:
        raise HTTPException(status_code=404, detail=f"No worker with id {worker_id}")
    return {"worker_id": worker_id,
            "assessments": independence.history(worker_id)}


@app.get("/api/reputation/check")
def reputation_check():
    """
    Compare every stored reputation figure with the records.

    Should always return an empty list. It exists so the claim that every
    number is derived can be checked rather than trusted.
    """
    problems = reputation.check_all()
    return {"consistent": not problems, "disagreements": problems}


@app.get("/api/agent/tool-usage")
def tool_usage():
    """
    How often each tool has been called, and how reliable it is.

    Specification section 23 asks whether the agent calls the correct tool.
    This is where that is measured rather than assumed.
    """
    return {"tools": audit.tool_usage()}


@app.get("/api/agent/cache")
def cache_status():
    """
    What the reply cache currently holds.

    Asking the agent the same question twice only costs Gemini quota once.
    Every agent reply says whether it was "cached", so during a
    demonstration you always know if you are seeing a fresh answer.
    """
    return reply_cache.stats()


@app.delete("/api/agent/cache")
def clear_cache():
    """
    Forget every cached reply.

    The cache already invalidates itself when the workforce data changes or
    the day rolls over, so this is rarely needed. Use it if you want to be
    certain the next answer comes fresh from Gemini.
    """
    return {"cleared": reply_cache.clear()}


class ParseRequest(BaseModel):
    text: str = Field(
        description="A workforce request in plain language",
        examples=["I need 8 masons tomorrow at 8 AM near Guntur"],
    )


@app.post("/api/jobs/parse")
def parse_job_request(request: ParseRequest):
    """
    Turn a sentence into structured job details.

    Gemini reads the language. The calendar date is worked out by the
    application, not by the model, because a wrong date sends people to a
    site on the wrong morning.

    Anything the contractor did not say comes back as null and is listed in
    "missing", together with one question that would fill the gaps.
    """
    try:
        return parse_request(request.text)
    except GeminiUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error))
