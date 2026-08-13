"""
Tests for the tools Gemini is allowed to call.

These run against the real database but never call Gemini, so they cost
nothing. What they check is that each tool tells the truth: that it only
returns people who genuinely qualify, that it admits when it found nothing,
and that it never quietly turns a shortfall into a full crew.

Skipped automatically if the database cannot be reached.
"""

from datetime import date, timedelta

import pytest

from app.agent import tools
from app.database import fetch_one


@pytest.fixture(scope="module", autouse=True)
def require_database():
    try:
        fetch_one("select 1 as ok")
    except Exception:
        pytest.skip("database not reachable")


def tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


# --- search_workers --------------------------------------------------------

def test_search_workers_finds_masons_in_guntur():
    result = tools.search_workers("Mason", "Guntur", tomorrow())

    assert result["found"] > 0
    assert len(result["results"]) == result["found"]


def test_every_worker_returned_is_verified_skilled_and_free():
    """
    The tool's promise. If it returns someone, the database must agree they
    are verified, hold the skill as a verified skill, and are free that day.
    """
    for worker in tools.search_workers("Mason", "Guntur", tomorrow())["results"]:
        row = fetch_one(
            """
            select w.verification_status,
                   (select count(*) from worker_skills ws
                      join skills s on s.id = ws.skill_id
                     where ws.worker_id = w.id and lower(s.name) = 'mason'
                       and ws.verification_status = 'verified') as verified_skill,
                   (select count(*) from availability a
                     where a.worker_id = w.id and a.date = %s
                       and a.status = 'available') as free
              from workers w where w.id = %s
            """,
            (tomorrow(), worker["worker_id"]),
        )
        assert row["verification_status"] == "verified"
        assert row["verified_skill"] == 1
        assert row["free"] == 1


def test_results_carry_the_evidence_behind_them():
    """The agent must explain with numbers, so the numbers have to be there."""
    first = tools.search_workers("Mason", "Guntur", tomorrow())["results"][0]

    for field in ["average_rating", "completed_jobs", "attendance_rate",
                  "distance_km", "match_score"]:
        assert field in first, field


def test_an_unknown_place_is_admitted_and_the_real_ones_listed():
    result = tools.search_workers("Mason", "Atlantis")

    assert result["found"] == 0
    assert result["results"] == []
    assert "Guntur" in result["note"]


def test_a_trade_nobody_has_returns_nothing_rather_than_a_guess():
    result = tools.search_workers("Astronaut", "Guntur", tomorrow())

    assert result["found"] == 0
    assert "No verified workers" in result["note"]


# --- search_crews ----------------------------------------------------------

def test_ravi_crew_reports_six_available_masons():
    """Specification section 15."""
    crews = {c["crew_id"]: c
             for c in tools.search_crews("Mason", "Guntur", tomorrow())["results"]}

    assert crews["RAVI01"]["available_workers"] == 6


def test_crew_available_workers_is_never_more_than_its_active_members():
    """
    A crew's supply must come from members who hold the skill, not from its
    size and never from its reputation (business rules 2 and 3).
    """
    for crew in tools.search_crews("Mason", "Guntur", tomorrow())["results"]:
        active = fetch_one(
            "select count(*) as n from crew_members "
            "where crew_id = %s and status = 'active'",
            (crew["crew_id"],),
        )["n"]
        assert crew["available_workers"] <= active


# --- profiles --------------------------------------------------------------

def test_worker_profile_reports_reputation_that_matches_the_records():
    """
    Suresh's headline numbers must equal what is actually in the job and
    rating tables. This is the claim a professor is most likely to check.
    """
    profile = tools.get_worker_profile("W001")

    assert profile["found"] is True
    assert profile["name"] == "Suresh"

    real = fetch_one(
        """
        select (select count(*) from job_assignments
                 where worker_id='W001' and status='completed') as jobs,
               (select round(avg(rating),2) from ratings
                 where worker_id='W001') as avg_rating
        """
    )
    assert profile["completed_jobs"] == real["jobs"]
    assert float(profile["average_rating"]) == float(real["avg_rating"])


def test_a_worker_who_left_a_crew_keeps_everything():
    """
    Business rule 4. Bhaskar left Ravi Crew. His jobs, ratings and skills
    are still his, and the membership record survives with an end date.
    """
    profile = tools.get_worker_profile("W014")

    assert profile["completed_jobs"] > 0
    assert profile["average_rating"] is not None
    assert profile["skills"]

    left = [c for c in profile["crew_history"] if c["status"] == "left"]
    assert left, "expected a membership that ended"
    assert left[0]["left_at"] is not None
    assert left[0]["crew_name"] == "Ravi Crew"


def test_crew_profile_keeps_crew_and_member_ratings_apart():
    """Business rule 3."""
    crew = tools.get_crew_profile("RAVI01")

    own_ratings = {m["this_workers_own_rating"] for m in crew["members"]
                   if m["this_workers_own_rating"] is not None}

    assert len(own_ratings) > 1
    assert own_ratings != {crew["crew_rating"]}


def test_unknown_ids_are_reported_not_invented():
    assert tools.get_worker_profile("W999")["found"] is False
    assert tools.get_crew_profile("NOPE")["found"] is False


# --- availability ----------------------------------------------------------

def test_check_availability_agrees_with_the_availability_table():
    """
    Business rule 1. This tool is the only thing that may decide whether
    somebody is free, so it has to match the table exactly.
    """
    result = tools.check_availability(worker_id="W001", on_date=tomorrow())
    row = fetch_one(
        "select status from availability where worker_id='W001' and date=%s",
        (tomorrow(),),
    )

    assert result["available"] == (row["status"] == "available")


def test_check_availability_for_a_crew_counts_free_members():
    result = tools.check_availability(crew_id="RAVI01", on_date=tomorrow())

    assert result["available_members"] <= result["active_members"]
    assert len(result["members"]) == result["active_members"]


def test_check_availability_needs_something_to_check():
    assert tools.check_availability()["found"] is False


# --- distance --------------------------------------------------------------

def test_distance_between_two_real_places():
    result = tools.distance_between("Guntur", "Vijayawada")

    assert result["found"] is True
    assert 25 < result["distance_km"] < 40


def test_distance_to_a_made_up_place_is_refused():
    result = tools.distance_between("Guntur", "Atlantis")

    assert result["found"] is False
    assert "Atlantis" in result["note"]


# --- recommend_workforce ---------------------------------------------------

def test_recommend_workforce_fills_the_eight_mason_request():
    result = tools.recommend_workforce("Mason", 8, "Guntur", tomorrow())

    assert result["filled"] == 8
    assert result["complete"] is True
    assert sum(entry["supply"] for entry in result["selection"]) == 8


def test_recommend_workforce_admits_a_shortfall():
    """
    The most important test in this file. Asking for 500 masons must come
    back short, and the selection must not have been padded to hide it.
    """
    result = tools.recommend_workforce("Mason", 500, "Guntur", tomorrow())

    assert result["complete"] is False
    assert result["shortfall"] > 0
    assert result["filled"] + result["shortfall"] == 500
    assert sum(entry["supply"] for entry in result["selection"]) == result["filled"]


def test_recommend_workforce_does_not_send_the_model_the_full_candidate_list():
    """Kept out deliberately: it is long, and it is not needed to explain."""
    assert "considered" not in tools.recommend_workforce(
        "Mason", 2, "Guntur", tomorrow())


# --- the tool list ---------------------------------------------------------

def test_every_tool_has_a_docstring_gemini_can_read():
    """
    The SDK builds each tool's description from its docstring. A tool
    without one is invisible to the model.
    """
    for tool in tools.ALL_TOOLS:
        assert tool.__doc__, tool.__name__
        assert len(tool.__doc__.strip()) > 40, tool.__name__


def test_no_tool_can_write_to_the_database():
    """
    Every tool at this step is read-only. Actions that change records need
    confirmation (business rule 7) and arrive at STEP 7.
    """
    import inspect

    for tool in tools.ALL_TOOLS:
        source = inspect.getsource(tool).lower()
        for forbidden in ["insert into", "update ", "delete from"]:
            assert forbidden not in source, f"{tool.__name__} looks like it writes"
