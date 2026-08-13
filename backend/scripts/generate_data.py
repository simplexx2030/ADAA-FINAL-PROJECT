"""
STEP 1 - Generate the sample ADAA workforce dataset as CSV files.

Run it with:
    backend/.venv/Scripts/python backend/scripts/generate_data.py

Most of the data is random, so the dataset looks realistic and varied.
But a few records are FIXED on purpose, because the demonstration
scenarios in the build specification depend on them:

    Ravi Crew (RAVI01)  6 available verified masons, rating 4.8
    Suresh    (W001)    31 completed jobs, 4.7 rating, 96% attendance,
                        member of Ravi Crew
    Raju      (W003)    independent mason, 18 jobs, 4.5 rating
    Mahesh    (W002)    leader of his own crew (M001)

The random seed is fixed, so running this script twice produces exactly the
same data. That matters because the specification asks whether the agent
gives consistent answers when the data has not changed (section 23).
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Fixed seed => the same "random" dataset every time.
random.seed(42)

# How many days of availability to generate, starting today.
AVAILABILITY_DAYS = 14

# Places in and around Guntur district, Andhra Pradesh.
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
SKILL_ID_BY_NAME = {name: skill_id for skill_id, name, _ in SKILLS}

FIRST_NAMES = [
    "Suresh", "Mahesh", "Raju", "Kumar", "Ravi", "Venkat", "Srinivas", "Naresh",
    "Prakash", "Ramesh", "Ganesh", "Anil", "Sunil", "Kiran", "Murali", "Sekhar",
    "Bhaskar", "Nagaraju", "Chandra", "Prasad", "Vijay", "Satish", "Rajesh",
    "Krishna", "Balu", "Yesu", "Sambaiah", "Koteswara", "Lakshmana", "Veeraiah",
]

LANGUAGES = ["Telugu", "Telugu", "Telugu", "Hindi", "English"]


def write_csv(filename: str, header: list[str], rows: list[list]) -> None:
    """Write one CSV file into the data/ folder."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  {filename:<22} {len(rows):>4} rows")


def phone_number(index: int) -> str:
    """A fake but realistic-looking Indian mobile number."""
    return f"+919{random.randint(100000000, 999999999)}"


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

def build_workers():
    """
    Return (worker_rows, worker_skill_rows).

    The first five workers are fixed for the demonstration scenarios.
    The rest are random.
    """
    workers = []
    worker_skills = []

    def add(worker_id, name, skill, location, rating, jobs, availability,
            attendance, experience, verification="verified", reliability=None,
            radius=15, language="Telugu"):
        loc_name, lat, lng = location
        # Small random scatter so people are not all at the exact same point.
        lat += random.uniform(-0.02, 0.02)
        lng += random.uniform(-0.02, 0.02)
        if reliability is None:
            reliability = round(min(5.0, rating * 0.9 + jobs / 60), 2)
        workers.append([
            worker_id, name, phone_number(len(workers)), "", language,
            loc_name, round(lat, 6), round(lng, 6), radius, experience,
            verification, availability, reliability, rating, jobs, attendance,
        ])
        worker_skills.append([worker_id, SKILL_ID_BY_NAME[skill], "verified",
                              experience])
        return worker_id

    # --- Fixed demo workers (build spec sections 13, 15, 16) ---
    add("W001", "Suresh", "Mason", LOCATIONS[0], 4.70, 31, "available",
        96.0, 9, reliability=4.60)
    add("W002", "Mahesh", "Mason", LOCATIONS[0], 4.60, 24, "available",
        93.0, 11, reliability=4.45)
    add("W003", "Raju",   "Mason", LOCATIONS[0], 4.50, 18, "available",
        91.0, 7, reliability=4.30)
    add("W004", "Kumar",  "Helper", LOCATIONS[0], 4.40, 15, "available",
        89.0, 4, reliability=4.10)
    add("W005", "Ravi",   "Mason", LOCATIONS[0], 4.80, 47, "available",
        97.0, 15, reliability=4.75)

    # Ravi Crew needs six available masons in total, so W006-W009 join
    # Ravi and Suresh.
    for i, name in enumerate(["Venkat", "Srinivas", "Naresh", "Prakash"], start=6):
        add(f"W{i:03d}", name, "Mason", LOCATIONS[0],
            round(random.uniform(4.1, 4.8), 2), random.randint(12, 40),
            "available", round(random.uniform(88, 97), 1), random.randint(4, 14))

    # Mahesh Crew needs two more members besides Mahesh.
    for i, name in enumerate(["Ramesh", "Ganesh"], start=10):
        add(f"W{i:03d}", name, "Mason", LOCATIONS[0],
            round(random.uniform(4.0, 4.7), 2), random.randint(8, 30),
            "available", round(random.uniform(85, 95), 1), random.randint(3, 12))

    # Independent masons who belong to no crew. The 8-mason demonstration
    # needs Ravi Crew's six PLUS two individuals, so these must exist and
    # must not be left to chance.
    for i, name in enumerate(["Murali", "Sekhar", "Bhaskar"], start=12):
        add(f"W{i:03d}", name, "Mason", LOCATIONS[0],
            round(random.uniform(4.2, 4.7), 2), random.randint(10, 26),
            "available", round(random.uniform(86, 96), 1), random.randint(3, 11))

    # --- Random workers ---
    used_names = {w[1] for w in workers}
    available_names = [n for n in FIRST_NAMES if n not in used_names]
    random.shuffle(available_names)

    skill_pool = [name for _, name, _ in SKILLS]

    for i in range(15, 15 + 18):
        worker_id = f"W{i:03d}"
        name = available_names.pop() if available_names else f"Worker{i}"
        skill = random.choice(skill_pool)
        location = random.choice(LOCATIONS)
        jobs = random.randint(0, 55)
        rating = round(random.uniform(3.4, 4.9), 2) if jobs else 0.0

        # Verification and availability are deliberately mixed, so the
        # matching engine has something real to filter out.
        verification = random.choices(
            ["verified", "pending", "unverified"], weights=[70, 20, 10])[0]
        availability = random.choices(
            ["available", "busy", "unavailable"], weights=[65, 25, 10])[0]

        add(worker_id, name, skill, location, rating, jobs, availability,
            round(random.uniform(72, 99), 1), random.randint(0, 20),
            verification=verification,
            radius=random.choice([10, 15, 20, 25, 30]),
            language=random.choice(LANGUAGES))

        # Some workers have a verified second skill.
        if random.random() < 0.35:
            second = random.choice([s for s in skill_pool if s != skill])
            worker_skills.append([
                worker_id, SKILL_ID_BY_NAME[second],
                random.choice(["verified", "pending"]),
                random.randint(1, 6),
            ])

    return workers, worker_skills


# ---------------------------------------------------------------------------
# Crews
# ---------------------------------------------------------------------------

def build_crews():
    """Return (crew_rows, crew_member_rows)."""
    today = date.today()

    crews = [
        # id, name, leader, trade, location, radius, availability,
        # rating, jobs, reliability, verification
        ["RAVI01", "Ravi Crew",   "W005", "Masonry", "Guntur", 16.3067, 80.4365,
         30, "available", 4.80, 32, 4.75, "verified"],
        ["M001",   "Mahesh Crew", "W002", "Masonry", "Guntur", 16.3067, 80.4365,
         25, "available", 4.60, 21, 4.40, "verified"],
    ]

    crew_members = []

    def join(crew_id, worker_id, role, months_ago, status="active"):
        joined = today - timedelta(days=months_ago * 30)
        crew_members.append([crew_id, worker_id, role, status,
                             joined.isoformat(), ""])

    # Ravi Crew: leader plus six members. Six of the seven people are
    # masons, which is what the demo relies on.
    join("RAVI01", "W005", "leader", 40)
    join("RAVI01", "W001", "member", 26)   # Suresh
    join("RAVI01", "W006", "member", 18)
    join("RAVI01", "W007", "member", 14)
    join("RAVI01", "W008", "member", 11)
    join("RAVI01", "W009", "member", 8)
    join("RAVI01", "W004", "member", 20)   # Kumar, helper

    # Mahesh Crew: leader plus two members.
    join("M001", "W002", "leader", 22)
    join("M001", "W010", "member", 12)
    join("M001", "W011", "member", 9)

    # Three more crews built from random workers, so the dataset is not
    # only about Ravi and Mahesh.
    extra_crews = [
        ("C003", "Venkat Crew",   "Carpentry"),
        ("C004", "Srinivas Crew", "Finishing"),
        ("C005", "Nagaraju Crew", "Steel"),
    ]
    # W012-W014 are deliberately left out: they stay independent.
    pool = [f"W{i:03d}" for i in range(15, 33)]
    random.shuffle(pool)

    for crew_id, crew_name, trade in extra_crews:
        loc_name, lat, lng = random.choice(LOCATIONS)
        members = [pool.pop() for _ in range(random.randint(3, 5)) if pool]
        if not members:
            continue
        leader = members[0]
        crews.append([
            crew_id, crew_name, leader, trade, loc_name,
            round(lat, 6), round(lng, 6), random.choice([15, 20, 25, 30]),
            random.choices(["available", "busy"], weights=[70, 30])[0],
            round(random.uniform(3.8, 4.8), 2), random.randint(4, 28),
            round(random.uniform(3.6, 4.7), 2),
            random.choices(["verified", "pending"], weights=[75, 25])[0],
        ])
        join(crew_id, leader, "leader", random.randint(12, 36))
        for member in members[1:]:
            join(crew_id, member, "member", random.randint(2, 20))

    # One historical record: somebody who already left a crew. This proves
    # that leaving is recorded, not deleted (Rule 4).
    if pool:
        former = pool.pop()
        left_on = today - timedelta(days=60)
        crew_members.append(["C003", former, "member", "left",
                             (left_on - timedelta(days=300)).isoformat(),
                             left_on.isoformat()])

    return crews, crew_members


# ---------------------------------------------------------------------------
# Contractors, jobs, ratings, availability
# ---------------------------------------------------------------------------

def build_contractors():
    companies = [
        ("CON001", "Rajesh Kumar",   "Sri Venkateswara Constructions", "Guntur"),
        ("CON002", "Anitha Reddy",   "Reddy Builders",                 "Vijayawada"),
        ("CON003", "Mohan Rao",      "Amaravati Infra Projects",       "Amaravati"),
        ("CON004", "Sudhakar Naidu", "Naidu Civil Works",              "Tenali"),
        ("CON005", "Prasad Varma",   "Varma Housing",                  "Mangalagiri"),
        ("CON006", "Lakshmi Devi",   "Sai Ram Constructions",          "Guntur"),
    ]
    rows = []
    for contractor_id, name, company, location in companies:
        rows.append([
            contractor_id, name, phone_number(0), company, location,
            random.choices(["verified", "pending"], weights=[80, 20])[0],
            round(random.uniform(3.9, 4.9), 2), random.randint(3, 40),
        ])
    return rows


def build_jobs(contractors):
    """A mix of finished jobs (history) and open jobs (current work)."""
    today = date.today()
    titles = [
        ("Brickwork for first floor slab",  "Mason",       "Masonry"),
        ("Column shuttering",               "Shuttering Carpenter", "Carpentry"),
        ("Steel binding for footings",      "Bar Bender",  "Steel"),
        ("Internal wall plastering",        "Plasterer",   "Finishing"),
        ("Floor tiling, two apartments",    "Tile Layer",  "Finishing"),
        ("Site clearing and material shifting", "Helper",  "General"),
        ("Concrete pour, ground floor",     "Concrete Worker", "General"),
        ("Exterior painting",               "Painter",     "Finishing"),
        ("Compound wall masonry",           "Mason",       "Masonry"),
        ("Electrical conduit laying",       "Electrician", "Services"),
    ]

    rows = []
    job_number = 1

    # Past, completed jobs -> this is where reputation comes from.
    for _ in range(10):
        title, skill, _ = random.choice(titles)
        contractor = random.choice(contractors)
        loc_name, lat, lng = random.choice(LOCATIONS)
        job_date = today - timedelta(days=random.randint(7, 120))
        rows.append([
            f"J{job_number:03d}", contractor[0], title,
            f"{title} at {loc_name}.", skill, random.randint(2, 10),
            loc_name, round(lat + random.uniform(-0.02, 0.02), 6),
            round(lng + random.uniform(-0.02, 0.02), 6),
            f"Site {random.randint(1, 60)}, {loc_name}",
            job_date.isoformat(), "08:00",
            random.choice([650, 700, 750, 800, 850, 900, 1000]),
            "completed",
        ])
        job_number += 1

    # Current, open jobs.
    for _ in range(4):
        title, skill, _ = random.choice(titles)
        contractor = random.choice(contractors)
        loc_name, lat, lng = random.choice(LOCATIONS)
        job_date = today + timedelta(days=random.randint(1, 10))
        rows.append([
            f"J{job_number:03d}", contractor[0], title,
            f"{title} at {loc_name}.", skill, random.randint(2, 8),
            loc_name, round(lat + random.uniform(-0.02, 0.02), 6),
            round(lng + random.uniform(-0.02, 0.02), 6),
            f"Site {random.randint(1, 60)}, {loc_name}",
            job_date.isoformat(), random.choice(["08:00", "09:00"]),
            random.choice([700, 800, 850, 900, 1000]),
            "open",
        ])
        job_number += 1

    return rows


def build_assignments_and_ratings(jobs, workers, crews):
    """
    For every completed job, assign somebody and record a rating.

    Note that a rating targets EITHER a worker OR a crew, never both. That
    is what keeps the two reputations separate (Rule 3).
    """
    worker_ids = [w[0] for w in workers]
    crew_ids = [c[0] for c in crews]

    assignments = []
    ratings = []
    comments = [
        "Good work, finished on time.",
        "Reliable and punctual.",
        "Quality was acceptable.",
        "Very neat finishing.",
        "Arrived late on the first day.",
        "Would hire again.",
        "Strong team, well coordinated.",
        "Work completed as agreed.",
    ]

    for job in jobs:
        job_id, contractor_id, status = job[0], job[1], job[13]
        if status != "completed":
            continue

        if random.random() < 0.5:
            # A crew did this job -> the CREW gets the rating.
            crew_id = random.choice(crew_ids)
            assignments.append([job_id, "", crew_id, "crew", "completed"])
            ratings.append([job_id, contractor_id, "", crew_id,
                            round(random.uniform(3.7, 5.0), 2),
                            random.choice(comments)])
        else:
            # Individuals did this job -> each WORKER gets their own rating.
            for worker_id in random.sample(worker_ids, random.randint(1, 3)):
                assignments.append([job_id, worker_id, "", "individual",
                                    "completed"])
                ratings.append([job_id, contractor_id, worker_id, "",
                                round(random.uniform(3.4, 5.0), 2),
                                random.choice(comments)])

    return assignments, ratings


def build_availability(workers):
    """
    Day-by-day availability for the next two weeks.

    This table is the ONLY place the agent may look to decide whether
    somebody can work (Rule 1).
    """
    today = date.today()
    rows = []

    for worker in workers:
        worker_id = worker[0]
        overall = worker[11]  # availability_status

        for offset in range(AVAILABILITY_DAYS):
            day = today + timedelta(days=offset)

            # Sunday is usually a rest day.
            if day.weekday() == 6 and random.random() < 0.8:
                status = "unavailable"
            elif overall == "unavailable":
                status = "unavailable"
            elif overall == "busy":
                status = random.choices(["booked", "available"],
                                        weights=[75, 25])[0]
            else:
                status = random.choices(["available", "booked", "unavailable"],
                                        weights=[80, 15, 5])[0]

            rows.append([worker_id, day.isoformat(), "08:00", "18:00", status])

    # The demo asks about "tomorrow". Make sure the Ravi Crew masons and the
    # independent masons really are free then, so the answer is not an
    # accident of the random numbers.
    tomorrow = (today + timedelta(days=1)).isoformat()
    must_be_free = ["W001", "W002", "W003", "W004", "W005", "W006", "W007",
                    "W008", "W009", "W010", "W011",   # Ravi Crew + Mahesh Crew
                    "W012", "W013", "W014"]           # independent masons
    for row in rows:
        if row[0] in must_be_free and row[1] == tomorrow:
            row[4] = "available"

    return rows


# ---------------------------------------------------------------------------

def main():
    print("Generating ADAA sample workforce data")
    print("-" * 44)

    workers, worker_skills = build_workers()
    crews, crew_members = build_crews()
    contractors = build_contractors()
    jobs = build_jobs(contractors)
    assignments, ratings = build_assignments_and_ratings(jobs, workers, crews)
    availability = build_availability(workers)

    write_csv("skills.csv", ["id", "name", "category"],
              [list(s) for s in SKILLS])

    write_csv("workers.csv", [
        "id", "name", "phone", "photo_url", "preferred_language",
        "location_name", "location_lat", "location_lng", "travel_radius_km",
        "experience_years", "verification_status", "availability_status",
        "reliability_score", "average_rating", "completed_jobs",
        "attendance_rate",
    ], workers)

    write_csv("worker_skills.csv",
              ["worker_id", "skill_id", "verification_status", "years_experience"],
              worker_skills)

    write_csv("contractors.csv", [
        "id", "name", "phone", "company_name", "location",
        "verification_status", "rating", "completed_jobs",
    ], contractors)

    write_csv("crews.csv", [
        "id", "name", "leader_worker_id", "primary_trade", "location_name",
        "location_lat", "location_lng", "travel_radius_km",
        "availability_status", "rating", "completed_jobs", "reliability_score",
        "verification_status",
    ], crews)

    write_csv("crew_members.csv",
              ["crew_id", "worker_id", "role", "status", "joined_at", "left_at"],
              crew_members)

    write_csv("jobs.csv", [
        "id", "contractor_id", "title", "description", "skill_required",
        "workers_required", "location_name", "location_lat", "location_lng",
        "site_address", "date", "start_time", "wage", "status",
    ], jobs)

    write_csv("job_assignments.csv",
              ["job_id", "worker_id", "crew_id", "assignment_type", "status"],
              assignments)

    write_csv("ratings.csv",
              ["job_id", "rater_id", "worker_id", "crew_id", "rating", "comment"],
              ratings)

    write_csv("availability.csv",
              ["worker_id", "date", "start_time", "end_time", "status"],
              availability)

    print("-" * 44)
    print(f"Done. Files are in: {DATA_DIR}")


if __name__ == "__main__":
    main()
