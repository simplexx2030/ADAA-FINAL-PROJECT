"""
Generate the ADAA demonstration dataset.

Run it with:
    backend/.venv/Scripts/python backend/scripts/generate_data.py

This is dummy data built for the professor demonstration. Real fieldwork
data replaces it later.

The important design decision
----------------------------
Reputation is NOT typed in. It is calculated from job history.

An earlier version of this script simply wrote "Suresh: 31 jobs, 4.70
rating" into the workers table. It looked fine until you opened his
profile and found no jobs and no ratings behind those numbers. A professor
asking "where does 4.7 come from?" would have had no answer.

So the order is now:

    1. create contractors, workers, crews
    2. create ~18 months of real jobs
    3. assign people to those jobs, and rate the work
    4. COUNT the results to get completed_jobs, average_rating and
       reliability

Every headline number a demonstration shows can be traced to rows in
job_assignments and ratings. That is what business rule 8 -- the database
is the source of truth -- actually means in practice.

The random seed is fixed, so this produces the same dataset every time.
"""

import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

random.seed(42)

AVAILABILITY_DAYS = 14
HISTORY_MONTHS = 18

LOCATIONS = [
    ("Guntur",          16.3067, 80.4365),
    ("Vijayawada",      16.5062, 80.6480),
    ("Tenali",          16.2430, 80.6400),
    ("Mangalagiri",     16.4307, 80.5680),
    ("Narasaraopet",    16.2350, 80.0500),
    ("Sattenapalle",    16.3937, 80.1500),
    ("Ponnur",          16.0667, 80.5667),
    ("Chilakaluripet",  16.0892, 80.1672),
    ("Bapatla",         15.9044, 80.4671),
    ("Amaravati",       16.5735, 80.3585),
]

SKILLS = [
    (1,  "Mason",                "Masonry"),
    (2,  "Helper",               "General"),
    (3,  "Carpenter",            "Carpentry"),
    (4,  "Shuttering Carpenter", "Carpentry"),
    (5,  "Bar Bender",           "Steel"),
    (6,  "Welder",               "Steel"),
    (7,  "Painter",              "Finishing"),
    (8,  "Plasterer",            "Finishing"),
    (9,  "Tile Layer",           "Finishing"),
    (10, "Electrician",          "Services"),
    (11, "Plumber",              "Services"),
    (12, "Concrete Worker",      "General"),
]
SKILL_ID = {name: skill_id for skill_id, name, _ in SKILLS}
SKILL_NAMES = [name for _, name, _ in SKILLS]

JOB_TITLES = {
    "Mason":                ["Brickwork for first floor slab", "Compound wall masonry",
                             "Block work for partition walls"],
    "Helper":               ["Site clearing and material shifting", "Assisting concrete pour"],
    "Carpenter":            ["Door and window frame fitting", "Roof truss carpentry"],
    "Shuttering Carpenter": ["Column shuttering", "Slab shuttering and props"],
    "Bar Bender":           ["Steel binding for footings", "Column reinforcement cage"],
    "Welder":               ["Grill and railing welding", "Structural steel welding"],
    "Painter":              ["Exterior painting", "Interior emulsion painting"],
    "Plasterer":            ["Internal wall plastering", "Ceiling plastering"],
    "Tile Layer":           ["Floor tiling, two apartments", "Bathroom wall tiling"],
    "Electrician":          ["Electrical conduit laying", "Wiring and switchboard fitting"],
    "Plumber":              ["Sanitary line installation", "Overhead tank plumbing"],
    "Concrete Worker":      ["Concrete pour, ground floor", "Foundation concreting"],
}

RATING_COMMENTS = [
    "Good work, finished on time.", "Reliable and punctual.",
    "Quality was acceptable.", "Very neat finishing.",
    "Would hire again.", "Strong team, well coordinated.",
    "Work completed as agreed.", "Careful with materials.",
]


# ---------------------------------------------------------------------------
# The demonstration cast
# ---------------------------------------------------------------------------
#
# These people are fixed, because the six demonstration scenarios in the
# build specification depend on them. Everyone else is random.
#
#  id     name       skill    jobs  rating  attend  exp  crew
DEMO_CAST = [
    ("W001", "Suresh", "Mason",  31, 4.70, 96.0,  9, "RAVI01"),
    ("W002", "Mahesh", "Mason",  24, 4.60, 93.0, 11, "M001"),
    ("W003", "Raju",   "Mason",  18, 4.50, 91.0,  7, None),
    ("W004", "Kumar",  "Helper", 15, 4.40, 89.0,  4, "RAVI01"),
    ("W005", "Ravi",   "Mason",  47, 4.80, 97.0, 15, "RAVI01"),
    # Ravi Crew's other masons
    ("W006", "Venkat",   "Mason", 29, 4.55, 94.0, 10, "RAVI01"),
    ("W007", "Srinivas", "Mason", 22, 4.35, 90.0,  8, "RAVI01"),
    ("W008", "Naresh",   "Mason", 17, 4.25, 88.0,  6, "RAVI01"),
    ("W009", "Prakash",  "Mason", 26, 4.45, 92.0,  9, "RAVI01"),
    # Mahesh Crew
    ("W010", "Ramesh", "Mason", 19, 4.30, 89.0,  7, "M001"),
    ("W011", "Ganesh", "Mason", 14, 4.20, 87.0,  5, "M001"),
    # Independent masons. The 8-mason demonstration needs individuals to
    # fill the last two positions, so these must exist by design.
    ("W012", "Murali",  "Mason", 21, 4.40, 90.0,  8, None),
    ("W013", "Sekhar",  "Mason", 16, 4.25, 88.0,  6, None),
    # W014 LEFT Ravi Crew six months ago. He exists so that scenario 5 --
    # "what happens to a worker's reputation if they leave a crew?" -- can
    # be shown on real records instead of described in words.
    ("W014", "Bhaskar", "Mason", 27, 4.50, 92.0, 11, "LEFT_RAVI01"),
]

RANDOM_NAMES = [
    "Nagaraju", "Chandra", "Prasad", "Vijay", "Satish", "Rajesh", "Krishna",
    "Balu", "Yesu", "Sambaiah", "Koteswara", "Lakshmana", "Veeraiah", "Anil",
    "Sunil", "Kiran", "Durga", "Mohan",
]

LANGUAGES = ["Telugu", "Telugu", "Telugu", "Hindi", "English"]

CONTRACTORS = [
    ("CON001", "Rajesh Kumar",   "Sri Venkateswara Constructions", "Guntur"),
    ("CON002", "Anitha Reddy",   "Reddy Builders",                 "Vijayawada"),
    ("CON003", "Mohan Rao",      "Amaravati Infra Projects",       "Amaravati"),
    ("CON004", "Sudhakar Naidu", "Naidu Civil Works",              "Tenali"),
    ("CON005", "Prasad Varma",   "Varma Housing",                  "Mangalagiri"),
    ("CON006", "Lakshmi Devi",   "Sai Ram Constructions",          "Guntur"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_csv(filename: str, header: list[str], rows: list[list]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with (DATA_DIR / filename).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  {filename:<22} {len(rows):>5} rows")


def phone() -> str:
    return f"+919{random.randint(100000000, 999999999)}"


def ratings_with_exact_mean(count: int, target: float) -> list[float]:
    """
    Produce ``count`` individual ratings whose mean is exactly ``target``.

    Ratings are built in balanced pairs: for every rating that is 0.2 above
    the target there is one 0.2 below it. That way the average is exact by
    construction, so a worker's stored average_rating is genuinely the mean
    of their rating rows and can be recomputed by anyone checking.
    """
    if count <= 0:
        return []

    headroom = min(target - 3.0, 5.0 - target, 0.45)
    ratings = []

    if count % 2 == 1:
        ratings.append(round(target, 2))

    for _ in range(count // 2):
        spread = round(random.uniform(0.05, max(0.06, headroom)), 2)
        ratings.append(round(target + spread, 2))
        ratings.append(round(target - spread, 2))

    random.shuffle(ratings)
    return ratings


def reliability_formula(attendance_rate, average_rating, no_shows):
    """
    The same formula the application uses at runtime.

    Kept identical to app.agent.reputation.reliability on purpose: if the
    generator and the runtime disagreed, a worker's score would jump the
    first time they finished a job.
    """
    if average_rating is None or attendance_rate is None:
        return None
    attendance_part = float(attendance_rate) / 100 * 5
    score = (attendance_part + float(average_rating)) / 2 - (no_shows * 0.15)
    return round(max(0.0, min(5.0, score)), 2)


def scatter(lat: float, lng: float) -> tuple[float, float]:
    return (round(lat + random.uniform(-0.02, 0.02), 6),
            round(lng + random.uniform(-0.02, 0.02), 6))


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------

def build_people():
    """
    Create workers and their verified skills.

    Reputation columns are left blank here. They are filled in later, from
    the job history.
    """
    workers = {}
    worker_skills = []
    plan = {}          # worker_id -> what history we owe them

    def add(worker_id, name, skill, location, experience, attendance,
            target_jobs, target_rating, verification="verified",
            availability="available", radius=15, language="Telugu"):
        loc_name, lat, lng = location
        lat, lng = scatter(lat, lng)
        workers[worker_id] = {
            "id": worker_id, "name": name, "phone": phone(), "photo_url": "",
            "preferred_language": language, "location_name": loc_name,
            "location_lat": lat, "location_lng": lng,
            "travel_radius_km": radius, "experience_years": experience,
            "verification_status": verification,
            "availability_status": availability,
            "attendance_rate": attendance,
            # filled in from history:
            "reliability_score": None, "average_rating": None,
            "completed_jobs": 0,
        }
        worker_skills.append([worker_id, SKILL_ID[skill], "verified", experience])
        plan[worker_id] = {"skill": skill, "jobs": target_jobs,
                           "rating": target_rating}

    # --- the fixed demonstration cast ---
    for worker_id, name, skill, jobs, rating, attendance, experience, _crew in DEMO_CAST:
        add(worker_id, name, skill, LOCATIONS[0], experience, attendance,
            jobs, rating, radius=random.choice([15, 20, 25]))

    # --- everybody else ---
    names = RANDOM_NAMES[:]
    random.shuffle(names)

    for index in range(15, 15 + 18):
        worker_id = f"W{index:03d}"
        name = names.pop() if names else f"Worker{index}"
        skill = random.choice(SKILL_NAMES)
        experience = random.randint(0, 20)

        # Newer workers genuinely have little history. That is realistic,
        # and it gives the matching engine weak candidates to rank down.
        target_jobs = min(random.randint(0, 40), experience * 4 + 2)
        target_rating = round(random.uniform(3.6, 4.9), 2) if target_jobs else 0.0

        add(worker_id, name, skill, random.choice(LOCATIONS), experience,
            round(random.uniform(72, 99), 1), target_jobs, target_rating,
            verification=random.choices(["verified", "pending", "unverified"],
                                        weights=[70, 20, 10])[0],
            availability=random.choices(["available", "busy", "unavailable"],
                                        weights=[65, 25, 10])[0],
            radius=random.choice([10, 15, 20, 25, 30]),
            language=random.choice(LANGUAGES))

        # Some workers have a verified second trade.
        if random.random() < 0.35:
            second = random.choice([s for s in SKILL_NAMES if s != skill])
            worker_skills.append([worker_id, SKILL_ID[second],
                                  random.choice(["verified", "pending"]),
                                  random.randint(1, 6)])

    return workers, worker_skills, plan


def build_crews(workers):
    """Crews, and who belongs to them. Crew reputation is filled in later."""
    today = date.today()
    crews = {}
    memberships = []

    def crew(crew_id, name, leader, trade, location, jobs_target, rating_target,
             radius=30):
        loc_name, lat, lng = location
        crews[crew_id] = {
            "id": crew_id, "name": name, "leader_worker_id": leader,
            "primary_trade": trade, "location_name": loc_name,
            "location_lat": round(lat, 6), "location_lng": round(lng, 6),
            "travel_radius_km": radius, "availability_status": "available",
            "verification_status": "verified",
            "rating": None, "completed_jobs": 0, "reliability_score": None,
            "_target_jobs": jobs_target, "_target_rating": rating_target,
        }

    def join(crew_id, worker_id, role, months_ago, status="active",
             left_months_ago=None):
        joined = today - timedelta(days=months_ago * 30)
        left = (today - timedelta(days=left_months_ago * 30)).isoformat() \
            if left_months_ago else ""
        memberships.append([crew_id, worker_id, role, status,
                            joined.isoformat(), left])

    crew("RAVI01", "Ravi Crew",   "W005", "Masonry", LOCATIONS[0], 32, 4.80)
    crew("M001",   "Mahesh Crew", "W002", "Masonry", LOCATIONS[0], 21, 4.60, 25)

    join("RAVI01", "W005", "leader", 40)
    join("RAVI01", "W001", "member", 26)
    join("RAVI01", "W006", "member", 18)
    join("RAVI01", "W007", "member", 14)
    join("RAVI01", "W008", "member", 11)
    join("RAVI01", "W009", "member", 8)
    join("RAVI01", "W004", "member", 20)          # Kumar, the helper

    # Bhaskar left Ravi Crew six months ago and now works independently.
    # His record stays: the membership row is kept with an end date, and
    # every job and rating he earned remains his (business rule 4).
    join("RAVI01", "W014", "member", 30, status="left", left_months_ago=6)

    join("M001", "W002", "leader", 22)
    join("M001", "W010", "member", 12)
    join("M001", "W011", "member", 9)

    # Three more crews from the random workers.
    pool = [w for w in workers if w >= "W015"]
    random.shuffle(pool)

    for crew_id, name, trade in [("C003", "Nagaraju Crew", "Carpentry"),
                                 ("C004", "Prasad Crew",   "Finishing"),
                                 ("C005", "Vijay Crew",    "Steel")]:
        members = [pool.pop() for _ in range(random.randint(3, 4)) if pool]
        if not members:
            continue
        location = random.choice(LOCATIONS)
        crew(crew_id, name, members[0], trade, location,
             random.randint(4, 26), round(random.uniform(3.9, 4.8), 2),
             radius=random.choice([15, 20, 25, 30]))
        crews[crew_id]["availability_status"] = random.choices(
            ["available", "busy"], weights=[70, 30])[0]
        crews[crew_id]["verification_status"] = random.choices(
            ["verified", "pending"], weights=[75, 25])[0]

        join(crew_id, members[0], "leader", random.randint(12, 36))
        for member in members[1:]:
            join(crew_id, member, "member", random.randint(2, 20))

    return crews, memberships


# ---------------------------------------------------------------------------
# History: the jobs people actually did
# ---------------------------------------------------------------------------

def build_history(workers, crews, plan):
    """
    Create past jobs, put people on them, and rate the work.

    Each worker is given a small set of "regular" contractors, and most of
    their work comes from those. That is how construction hiring actually
    behaves, and it gives the independence assessment (STEP 9) something
    real to measure when it looks at contractor relationships.
    """
    today = date.today()
    jobs = []
    assignments = []
    ratings = []

    regulars = {
        worker_id: random.sample(CONTRACTORS, random.randint(2, 3))
        for worker_id in workers
    }

    job_number = 0
    job_rows = {}                       # job_id -> the row, so we can edit it
    pool = defaultdict(list)            # skill -> jobs that still have room

    def new_job(skill, when, contractor, status="completed", crew_job=False):
        """Create a job with room for several people."""
        nonlocal job_number
        job_number += 1
        job_id = f"J{job_number:04d}"
        loc_name, lat, lng = random.choice(LOCATIONS)
        lat, lng = scatter(lat, lng)
        title = random.choice(JOB_TITLES.get(skill, [f"{skill} work"]))

        row = [
            job_id, contractor[0], title, f"{title} at {loc_name}.", skill,
            0,  # workers_required, corrected at the end to the real number
            loc_name, lat, lng, f"Site {random.randint(1, 60)}, {loc_name}",
            when.isoformat(), random.choice(["08:00", "08:30", "09:00"]),
            random.choice([650, 700, 750, 800, 850, 900, 1000]), status,
        ]
        jobs.append(row)
        job_rows[job_id] = row

        if not crew_job:
            pool[skill].append({
                "job_id": job_id, "contractor": contractor,
                "room": random.randint(1, 7), "date": when,
            })
        return job_id

    def job_for(worker_id, skill):
        """
        Find a job for this worker: usually an existing one, so that several
        people work the same site, which is how construction actually runs
        and makes workers_required mean something.
        """
        candidates = [j for j in pool[skill] if j["room"] > 0]

        # Prefer a site run by one of this worker's regular contractors.
        preferred = [j for j in candidates
                     if j["contractor"] in regulars[worker_id]]

        if preferred and random.random() < 0.7:
            chosen = random.choice(preferred)
        elif candidates and random.random() < 0.5:
            chosen = random.choice(candidates)
        else:
            contractor = (random.choice(regulars[worker_id])
                          if random.random() < 0.7 else random.choice(CONTRACTORS))
            when = today - timedelta(days=random.randint(10, HISTORY_MONTHS * 30))
            new_job(skill, when, contractor)
            chosen = pool[skill][-1]

        chosen["room"] -= 1
        return chosen["job_id"], chosen["contractor"]

    # --- individual work history ---
    for worker_id, wanted in plan.items():
        count = wanted["jobs"]
        if count <= 0:
            continue

        for rating_value in ratings_with_exact_mean(count, wanted["rating"]):
            job_id, contractor = job_for(worker_id, wanted["skill"])

            # A job runs for a few days. Attendance is worked out from
            # these two numbers, so it is derived like everything else
            # rather than typed in.
            days = random.randint(2, 5)
            assignments.append([job_id, worker_id, "", "individual",
                                "completed", days, days])
            ratings.append([job_id, contractor[0], worker_id, "",
                            rating_value, random.choice(RATING_COMMENTS)])

        # A few no-shows, so reliability is not simply a copy of the rating.
        # These are recorded but are NOT completed jobs and earn no rating.
        for _ in range(random.randint(0, 2)):
            job_id, _contractor = job_for(worker_id, wanted["skill"])
            days = random.randint(2, 4)
            assignments.append([job_id, worker_id, "", "individual",
                                "no_show", days, 0])

    # --- crew work history ---
    for crew_id, crew in crews.items():
        count = crew["_target_jobs"]
        if count <= 0:
            continue

        crew_ratings = ratings_with_exact_mean(count, crew["_target_rating"])
        trade_skill = {"Masonry": "Mason", "Carpentry": "Carpenter",
                       "Finishing": "Painter", "Steel": "Bar Bender"}.get(
                           crew["primary_trade"], "Mason")

        for rating_value in crew_ratings:
            contractor = random.choice(CONTRACTORS)
            when = today - timedelta(days=random.randint(10, HISTORY_MONTHS * 30))
            # A crew job is the crew's own site, not shared with individuals.
            job_id = new_job(trade_skill, when, contractor, crew_job=True)
            # The crew brought a team, so the job needed several people.
            job_rows[job_id][5] = random.randint(3, 8)

            assignments.append([job_id, "", crew_id, "crew", "completed",
                                random.randint(3, 6), random.randint(3, 6)])
            ratings.append([job_id, contractor[0], "", crew_id,
                            rating_value, random.choice(RATING_COMMENTS)])

    # --- a few jobs that are still open ---
    for _ in range(4):
        skill = random.choice(SKILL_NAMES)
        contractor = random.choice(CONTRACTORS)
        when = today + timedelta(days=random.randint(1, 10))
        job_id = new_job(skill, when, contractor, status="open", crew_job=True)
        job_rows[job_id][5] = random.randint(2, 8)

    # Make workers_required truthful: for the historical jobs it is exactly
    # the number of people who were actually put on them. A job claiming it
    # needed eight workers while showing one assignment would be the first
    # thing a careful reader noticed.
    people_on_job = defaultdict(int)
    for row in assignments:
        job_id, _worker_id, _crew_id, kind = row[0], row[1], row[2], row[3]
        if kind == "individual":
            people_on_job[job_id] += 1

    for job_id, count in people_on_job.items():
        job_rows[job_id][5] = count

    # Any job nobody was assigned to keeps a sensible minimum.
    for row in jobs:
        if row[5] == 0:
            row[5] = 1

    return jobs, assignments, ratings


def tune_attendance(assignments, plan):
    """
    Adjust the day counts so each worker's attendance comes out at their
    target.

    Attendance is now days-attended over days-booked, so the target cannot
    simply be written onto the worker -- it has to be produced. This nudges
    the attended_days on completed assignments until the ratio matches.

    A completed assignment never drops below one attended day, because a
    completed job where nobody turned up is a contradiction.
    """
    by_worker = defaultdict(list)
    for row in assignments:
        _job, worker_id, _crew, kind, _status = row[:5]
        if kind == "individual":
            by_worker[worker_id].append(row)

    for worker_id, target in plan.items():
        rows = by_worker.get(worker_id)
        if not rows or target is None:
            continue

        booked = sum(row[5] for row in rows)
        desired = round(booked * target / 100)
        current = sum(row[6] for row in rows)

        # Too many days attended: take some back off completed rows.
        surplus = current - desired
        for row in rows:
            if surplus <= 0:
                break
            if row[4] != "completed":
                continue
            can_remove = min(surplus, row[6] - 1)
            if can_remove > 0:
                row[6] -= can_remove
                surplus -= can_remove

        # Too few: shorten the no-show bookings instead, which raises the
        # ratio without inventing attendance.
        shortfall = desired - sum(row[6] for row in rows)
        for row in rows:
            if shortfall <= 0:
                break
            if row[4] != "no_show":
                continue
            can_shorten = min(shortfall, row[5] - 1)
            if can_shorten > 0:
                row[5] -= can_shorten
                shortfall -= can_shorten


def derive_reputation(workers, crews, assignments, ratings):
    """
    Count the history and write the results onto the workers and crews.

    This is the step that makes every headline number checkable. After it
    runs, workers.completed_jobs is literally the number of completed
    assignment rows, and workers.average_rating is literally the mean of
    their rating rows.
    """
    completed = defaultdict(int)
    no_shows = defaultdict(int)
    crew_completed = defaultdict(int)

    booked_days = defaultdict(int)
    attended_days = defaultdict(int)

    for row in assignments:
        _job_id, worker_id, crew_id, kind, status = row[:5]
        scheduled, attended = row[5], row[6]

        if kind == "crew":
            if status == "completed":
                crew_completed[crew_id] += 1
            continue

        booked_days[worker_id] += scheduled
        attended_days[worker_id] += attended

        if status == "completed":
            completed[worker_id] += 1
        elif status == "no_show":
            no_shows[worker_id] += 1

    worker_ratings = defaultdict(list)
    crew_ratings = defaultdict(list)
    for _job_id, _rater, worker_id, crew_id, value, _comment in ratings:
        if worker_id:
            worker_ratings[worker_id].append(float(value))
        elif crew_id:
            crew_ratings[crew_id].append(float(value))

    for worker_id, worker in workers.items():
        values = worker_ratings[worker_id]
        worker["completed_jobs"] = completed[worker_id]
        worker["average_rating"] = (
            round(sum(values) / len(values), 2) if values else None
        )

        # Attendance is days turned up over days booked -- the same
        # calculation the running application uses, so the demonstration
        # data and live updates cannot drift apart.
        booked = booked_days[worker_id]
        worker["attendance_rate"] = (
            round(attended_days[worker_id] / booked * 100, 2) if booked else None
        )
        worker["reliability_score"] = reliability_formula(
            worker["attendance_rate"], worker["average_rating"],
            no_shows[worker_id])

    for crew_id, crew in crews.items():
        values = crew_ratings[crew_id]
        crew["completed_jobs"] = crew_completed[crew_id]
        crew["rating"] = round(sum(values) / len(values), 2) if values else None
        if values:
            members_reliability = crew["rating"]
            crew["reliability_score"] = round(min(5.0, members_reliability), 2)
        else:
            crew["reliability_score"] = None


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def build_availability(workers):
    """
    Day by day availability for the next two weeks.

    This table is the only thing that decides whether somebody can work
    (business rule 1).
    """
    today = date.today()
    rows = []

    for worker_id, worker in workers.items():
        overall = worker["availability_status"]

        for offset in range(AVAILABILITY_DAYS):
            day = today + timedelta(days=offset)

            if day.weekday() == 6 and random.random() < 0.8:
                status = "unavailable"                 # Sunday
            elif overall == "unavailable":
                status = "unavailable"
            elif overall == "busy":
                status = random.choices(["booked", "available"],
                                        weights=[75, 25])[0]
            else:
                status = random.choices(["available", "booked", "unavailable"],
                                        weights=[80, 15, 5])[0]

            rows.append([worker_id, day.isoformat(), "08:00", "18:00", status])

    # The demonstration asks about tomorrow. The cast must genuinely be
    # free then, so the answer is not an accident of the random numbers.
    tomorrow = (today + timedelta(days=1)).isoformat()
    cast = {entry[0] for entry in DEMO_CAST}
    for row in rows:
        if row[0] in cast and row[1] == tomorrow:
            row[4] = "available"

    return rows


# ---------------------------------------------------------------------------

def main():
    print("Generating the ADAA demonstration dataset")
    print("-" * 46)

    workers, worker_skills, plan = build_people()
    crews, memberships = build_crews(workers)
    jobs, assignments, ratings = build_history(workers, crews, plan)

    # Attendance is derived from day counts, so the demonstration figures
    # have to be produced rather than asserted.
    tune_attendance(assignments,
                    {worker_id: worker["attendance_rate"]
                     for worker_id, worker in workers.items()})

    derive_reputation(workers, crews, assignments, ratings)
    availability = build_availability(workers)

    write_csv("skills.csv", ["id", "name", "category"], [list(s) for s in SKILLS])

    write_csv("workers.csv", [
        "id", "name", "phone", "photo_url", "preferred_language",
        "location_name", "location_lat", "location_lng", "travel_radius_km",
        "experience_years", "verification_status", "availability_status",
        "reliability_score", "average_rating", "completed_jobs",
        "attendance_rate",
    ], [[w["id"], w["name"], w["phone"], w["photo_url"],
         w["preferred_language"], w["location_name"], w["location_lat"],
         w["location_lng"], w["travel_radius_km"], w["experience_years"],
         w["verification_status"], w["availability_status"],
         w["reliability_score"], w["average_rating"], w["completed_jobs"],
         w["attendance_rate"]] for w in workers.values()])

    write_csv("worker_skills.csv",
              ["worker_id", "skill_id", "verification_status", "years_experience"],
              worker_skills)

    write_csv("contractors.csv", [
        "id", "name", "phone", "company_name", "location",
        "verification_status", "rating", "completed_jobs",
    ], [[c[0], c[1], phone(), c[2], c[3], "verified",
         round(random.uniform(3.9, 4.9), 2), random.randint(8, 60)]
        for c in CONTRACTORS])

    write_csv("crews.csv", [
        "id", "name", "leader_worker_id", "primary_trade", "location_name",
        "location_lat", "location_lng", "travel_radius_km",
        "availability_status", "rating", "completed_jobs", "reliability_score",
        "verification_status",
    ], [[c["id"], c["name"], c["leader_worker_id"], c["primary_trade"],
         c["location_name"], c["location_lat"], c["location_lng"],
         c["travel_radius_km"], c["availability_status"], c["rating"],
         c["completed_jobs"], c["reliability_score"], c["verification_status"]]
        for c in crews.values()])

    write_csv("crew_members.csv",
              ["crew_id", "worker_id", "role", "status", "joined_at", "left_at"],
              memberships)

    write_csv("jobs.csv", [
        "id", "contractor_id", "title", "description", "skill_required",
        "workers_required", "location_name", "location_lat", "location_lng",
        "site_address", "date", "start_time", "wage", "status",
    ], jobs)

    write_csv("job_assignments.csv",
              ["job_id", "worker_id", "crew_id", "assignment_type", "status",
               "scheduled_days", "attended_days"],
              assignments)

    write_csv("ratings.csv",
              ["job_id", "rater_id", "worker_id", "crew_id", "rating", "comment"],
              ratings)

    write_csv("availability.csv",
              ["worker_id", "date", "start_time", "end_time", "status"],
              availability)

    print("-" * 46)
    print("Reputation was calculated from the history above, not typed in.")
    print("Check for yourself:")
    print("  Suresh  jobs:", workers["W001"]["completed_jobs"],
          " rating:", workers["W001"]["average_rating"])
    print("  Ravi Crew jobs:", crews["RAVI01"]["completed_jobs"],
          " rating:", crews["RAVI01"]["rating"])
    print(f"Files are in: {DATA_DIR}")


if __name__ == "__main__":
    main()
