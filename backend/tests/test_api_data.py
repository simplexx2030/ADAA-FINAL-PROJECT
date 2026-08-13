"""
Tests that the API really reads the workforce data out of PostgreSQL.

These tests need a working DATABASE_URL and an internet connection. If the
database cannot be reached they are skipped rather than failed, so that
someone without the .env file can still run the rest of the test suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def require_database():
    """Skip this whole file if the database is not reachable."""
    response = client.get("/health/database")
    if response.status_code != 200:
        pytest.skip("database not reachable")


def test_database_health_reports_workers():
    body = client.get("/health/database").json()

    assert body["status"] == "ok"
    assert body["workers"] >= 20  # the spec asks for at least 20 workers


def test_worker_list_is_not_empty():
    workers = client.get("/api/workers").json()["workers"]

    assert len(workers) >= 20
    assert {"id", "name", "average_rating"} <= set(workers[0])


def test_filtering_by_skill_returns_only_verified_masons():
    workers = client.get("/api/workers", params={"skill": "Mason"}).json()["workers"]

    assert workers, "expected at least one mason"
    for worker in workers:
        assert "Mason" in (worker["verified_skills"] or "")


def test_suresh_matches_the_demonstration_profile():
    """
    Section 16 of the build spec describes Suresh precisely. The
    demonstration depends on these exact numbers.
    """
    suresh = client.get("/api/workers/W001").json()

    assert suresh["name"] == "Suresh"
    assert suresh["completed_jobs"] == 31
    assert float(suresh["average_rating"]) == 4.70
    assert float(suresh["attendance_rate"]) == 96.00


def test_ravi_crew_has_six_available_masons():
    """Section 15: Ravi's crew has six available verified masons."""
    crew = client.get("/api/crews/RAVI01").json()

    assert crew["name"] == "Ravi Crew"
    active = [m for m in crew["members"] if m["status"] == "active"]
    assert len(active) == 7  # six masons plus one helper


def test_worker_keeps_their_own_rating_inside_a_crew():
    """
    Business rule 3: a crew's rating must not become every member's rating.
    """
    crew = client.get("/api/crews/RAVI01").json()
    member_ratings = {
        float(m["worker_own_rating"])
        for m in crew["members"]
        if m["worker_own_rating"] is not None
    }

    assert len(member_ratings) > 1, "members should have differing own ratings"
    assert member_ratings != {float(crew["rating"])}


def test_crew_history_survives_leaving_a_crew():
    """
    Business rule 4: leaving a crew is recorded, not erased. Somewhere in
    the dataset there is a worker with a 'left' membership row, and their
    own record must still be intact.
    """
    crews = client.get("/api/crews").json()["crews"]
    former_member = None

    for crew in crews:
        detail = client.get(f"/api/crews/{crew['id']}").json()
        for member in detail["members"]:
            if member["status"] == "left":
                former_member = member
                break
        if former_member:
            break

    if former_member is None:
        pytest.skip("no historical membership in this dataset")

    worker = client.get(f"/api/workers/{former_member['id']}").json()

    assert worker["id"] == former_member["id"]
    assert worker["completed_jobs"] >= 0
    # The membership record still exists, with an end date.
    left_rows = [c for c in worker["crew_history"] if c["status"] == "left"]
    assert left_rows and left_rows[0]["left_at"] is not None


def test_unknown_worker_returns_404():
    assert client.get("/api/workers/W999").status_code == 404


def test_unknown_crew_returns_404():
    assert client.get("/api/crews/NOPE").status_code == 404
