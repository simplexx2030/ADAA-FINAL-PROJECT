"""
The ADAA backend API.

Right now it can:
  - report that it is alive           (STEP 0)
  - read workers and crews from the   (STEP 2)
    PostgreSQL database

The AI agent and the matching engine come in later steps.

Run it with:
    backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend
"""

from datetime import date, timedelta

from fastapi import FastAPI, HTTPException

from app.agent.matching import (
    DEFAULT_SEARCH_RADIUS_KM,
    WorkforceRequest,
    calculate_distance,
    compose_workforce,
)
from app.config import settings
from app.database import fetch_all, fetch_one

app = FastAPI(
    title="ADAA Workforce Coordination Agent",
    description=(
        "Backend API for ADAA, a construction workforce coordination "
        "platform. The AI agent is powered by Gemini and is added in a "
        "later build step."
    ),
    version="0.2.0",
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
        "step": "STEP 2 - database connected",
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
    return {"locations": fetch_all(LOCATION_SQL)}


LOCATION_SQL = """
    select location_name as name,
           round(avg(location_lat)::numeric, 6)::float8 as lat,
           round(avg(location_lng)::numeric, 6)::float8 as lng,
           count(*) as workers
      from workers
     where location_name is not null
     group by location_name
     order by count(*) desc, location_name
"""


def resolve_location(name: str) -> dict:
    """Turn a place name such as 'Guntur' into coordinates."""
    row = fetch_one(
        LOCATION_SQL.replace("where location_name is not null",
                             "where lower(location_name) = lower(%s)"),
        (name,),
    )
    if row is None:
        known = [r["name"] for r in fetch_all(LOCATION_SQL)]
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
